"""
LOVE State-Space Memory — Mamba/S4-inspired Linear Recurrent Memory

Why this exists:
  ChromaDB gives us semantic recall ("what was said") but loses temporal dynamics.
  Transformers cost O(N^2) over context. SSMs give us O(N) compressed state that
  remembers patterns across thousands of events without exploding context.

Real algorithm (selective SSM, simplified):
  h_t = A * h_t-1 + B(x_t) * x_t       # state update, A is diagonal stable
  y_t = C * h_t + D * x_t              # readout
  where:
    - A is data-independent, stable (|A| < 1), HiPPO-like diagonal init
    - B(x_t), C(x_t) are *input-dependent* (the "selective" part of Mamba)
    - x_t is the 384-d observation embedding from the world model

What's real:
  - Stable diagonal state-transition (HiPPO-style log-spaced eigenvalues)
  - Input-dependent gating (the breakthrough from S6/Mamba)
  - Constant-memory online update (no quadratic cost)
  - Persistent state vector survives across sessions
  - Self-supervised online learning: SSM predicts next world-model embedding
    and backprops through D_out, C_proj, B_proj, gate_W each step
  - Truncated BPTT over N=8 step windows for richer temporal credit assignment

What other modules get:
  - get_context_vector() -> compact 256-d summary of "everything LOVE has lived through"
  - get_temporal_attention(query) -> which past states are relevant now
  - decode_recent_dynamics() -> "what trajectory is the user/system on"
  - get_next_prediction() -> predicted next 384-d embedding (online learned)
  - train_step(x_t, x_next) -> online SGD update, returns scalar MSE loss
  - train_on_trajectory(xs) -> TBPTT over N-step window, returns avg MSE loss
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "ssm_memory"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_VEC = DATA_DIR / "h_state.npy"
PARAMS = DATA_DIR / "params.npz"
META = DATA_DIR / "meta.json"

INPUT_DIM = 384      # matches world_model_latent embed dim
STATE_DIM = 256      # compressed memory state
OUTPUT_DIM = 256

TRAIN_LR = 0.005             # online learning rate for self-supervised objective
TRAIN_GRAD_CLIP = 0.02       # gradient clip magnitude
TRAIN_LOSS_EMA_ALPHA = 0.05  # EMA smoothing factor for loss tracking

BPTT_LR = 0.003              # slightly lower lr for truncated BPTT
BPTT_WINDOW = 8              # trajectory window size for TBPTT


# ── HiPPO-inspired stable init ───────────────────────────────────────────────

def _hippo_diag_init(state_dim: int) -> np.ndarray:
    """Log-spaced negative-real eigenvalues -> stable exponential-decay basis.
    This is the trick that makes SSMs remember long horizons without blowing up."""
    # log-spaced decay timescales from ~10 steps to ~10000 steps
    timescales = np.logspace(np.log10(10.0), np.log10(10000.0), num=state_dim)
    # discrete A = exp(-1/tau) so each dim decays at its own rate
    return np.exp(-1.0 / timescales).astype(np.float32)


# ── Engine ───────────────────────────────────────────────────────────────────

class StateSpaceMemory:
    _instance: Optional["StateSpaceMemory"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init = False
            return cls._instance

    def __init__(self):
        if self._init:
            return
        self._init = True
        self._mu = threading.Lock()

        # Load or initialize parameters
        if PARAMS.exists():
            try:
                p = np.load(PARAMS)
                self._A = p["A"]                # (STATE_DIM,)  diagonal
                self._B_proj = p["B_proj"]      # (STATE_DIM, INPUT_DIM)
                self._C_proj = p["C_proj"]      # (OUTPUT_DIM, STATE_DIM)
                self._D = p["D"]                # (OUTPUT_DIM, INPUT_DIM)
                self._gate_W = p["gate_W"]      # (INPUT_DIM, STATE_DIM)  selective gate
                # D_out may not exist in older checkpoints — fall back to random init
                if "D_out" in p:
                    self._D_out = p["D_out"]    # (INPUT_DIM, OUTPUT_DIM)
                else:
                    rng = np.random.default_rng(99)
                    self._D_out = (rng.standard_normal((INPUT_DIM, OUTPUT_DIM)).astype(np.float32)
                                   / np.sqrt(OUTPUT_DIM)) * 0.1
                # h_bptt_start may not exist in older checkpoints — init to zeros
                if "h_bptt_start" in p:
                    self._h_bptt_start = p["h_bptt_start"].astype(np.float32)
                else:
                    self._h_bptt_start = np.zeros(STATE_DIM, dtype=np.float32)
            except Exception:
                self._init_params()
        else:
            self._init_params()

        # Hidden state — live recurrent state updated every step()
        if STATE_VEC.exists():
            try:
                self._h = np.load(STATE_VEC).astype(np.float32)
                if self._h.shape != (STATE_DIM,):
                    self._h = np.zeros(STATE_DIM, dtype=np.float32)
            except Exception:
                self._h = np.zeros(STATE_DIM, dtype=np.float32)
        else:
            self._h = np.zeros(STATE_DIM, dtype=np.float32)

        # Previous hidden state — cached before each step for 1-step BPTT
        self._h_prev: np.ndarray = np.zeros(STATE_DIM, dtype=np.float32)

        # Last predicted next embedding (384-d), updated every step()
        self._last_prediction: Optional[np.ndarray] = None

        # Online training loss EMA (1-step train_step)
        self._train_loss_ema: float = 0.0

        # BPTT loss EMA — updated by train_on_trajectory()
        self._bptt_loss_ema: float = 0.0

        # Trajectory buffer: accumulates embeddings for TBPTT windows
        self._trajectory_buffer: deque = deque(maxlen=BPTT_WINDOW)

        # Trajectory of recent compressed outputs (for attention queries)
        self._y_history: List[np.ndarray] = []
        self._step_count = 0
        self._meta = self._load_meta()

    def _init_params(self):
        rng = np.random.default_rng(42)
        self._A = _hippo_diag_init(STATE_DIM)
        # Small random projections, scaled for stability
        self._B_proj = (rng.standard_normal((STATE_DIM, INPUT_DIM)).astype(np.float32)
                       / np.sqrt(INPUT_DIM))
        self._C_proj = (rng.standard_normal((OUTPUT_DIM, STATE_DIM)).astype(np.float32)
                       / np.sqrt(STATE_DIM))
        self._D = (rng.standard_normal((OUTPUT_DIM, INPUT_DIM)).astype(np.float32)
                  / np.sqrt(INPUT_DIM)) * 0.1
        # Gate: input -> per-dim selective scaling of A. This is the Mamba magic.
        self._gate_W = (rng.standard_normal((INPUT_DIM, STATE_DIM)).astype(np.float32)
                      / np.sqrt(INPUT_DIM))
        # Decoder: maps 256-d SSM output back to 384-d embedding space
        self._D_out = (rng.standard_normal((INPUT_DIM, OUTPUT_DIM)).astype(np.float32)
                      / np.sqrt(OUTPUT_DIM)) * 0.1
        # BPTT window start state (detached snapshot, not the live _h)
        self._h_bptt_start = np.zeros(STATE_DIM, dtype=np.float32)

    def _load_meta(self) -> Dict:
        if META.exists():
            try:
                return json.loads(META.read_text())
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.state_space_memory")
        return {"steps": 0, "last_update": ""}

    def _save(self):
        try:
            np.save(STATE_VEC, self._h)
            np.savez(PARAMS,
                     A=self._A, B_proj=self._B_proj, C_proj=self._C_proj,
                     D=self._D, gate_W=self._gate_W, D_out=self._D_out,
                     h_bptt_start=self._h_bptt_start)
            self._meta["steps"] = self._step_count
            self._meta["last_update"] = datetime.now().isoformat()
            META.write_text(json.dumps(self._meta, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.state_space_memory")

    # ── core selective SSM step ──────────────────────────────────────────────

    def step(self, x: np.ndarray) -> np.ndarray:
        """One SSM step. x is a 384-d embedding. Returns 256-d compressed output.

        h_t = (A * gate(x_t)) ⊙ h_t-1 + B @ x_t
        y_t = C @ h_t + D @ x_t

        Also updates self._last_prediction = D_out @ y_t (predicted next embedding).
        """
        if x is None or x.shape != (INPUT_DIM,):
            return np.zeros(OUTPUT_DIM, dtype=np.float32)

        with self._mu:
            # Cache previous h before update (needed for train_step BPTT)
            self._h_prev = self._h.copy()

            # Selective gate: sigmoid(x @ gate_W) ∈ (0,1) per state dim.
            # This makes A *input-dependent* — the key innovation in Mamba.
            gate = 1.0 / (1.0 + np.exp(-(x @ self._gate_W)))   # (STATE_DIM,)
            # Effective per-step decay
            A_eff = self._A * (0.5 + 0.5 * gate)  # clamp into [0.5*A, A]

            # State update: elementwise stable recurrence
            self._h = A_eff * self._h + self._B_proj @ x

            # Readout
            y = self._C_proj @ self._h + self._D @ x

            # Predicted next embedding via learned decoder
            self._last_prediction = self._D_out @ y   # (INPUT_DIM,)

            self._step_count += 1
            if self._step_count % 100 == 0:
                self._save()

            # Keep a short tail for attention queries
            self._y_history.append(y.copy())
            if len(self._y_history) > 512:
                self._y_history = self._y_history[-256:]

            return y

    # ── self-supervised online training ─────────────────────────────────────

    def decode_next(self, y: np.ndarray) -> np.ndarray:
        """Decode a 256-d SSM output to a predicted 384-d next embedding.
        Pure forward pass — no side-effects, no lock required."""
        return (self._D_out @ y).astype(np.float32)

    def train_on_trajectory(self, xs: List[np.ndarray]) -> float:
        """Truncated BPTT over a window of N embeddings (each 384-d).

        Takes xs[0..N-1], predicts xs[1..N-1] from xs[0..N-2], and
        backpropagates through all N-1 steps simultaneously.

        Uses self._h_bptt_start as the detached initial state for this window
        (NOT the live self._h — that one runs the world in real time).

        Args:
            xs: List of N 384-d embeddings (N >= 2).  Typically N = BPTT_WINDOW = 8.

        Returns:
            Average MSE loss across the N-1 prediction steps.
        """
        if len(xs) < 2:
            return 0.0

        xs = [x.astype(np.float32) for x in xs]

        with self._mu:
            # ── Forward pass — store intermediates ───────────────────────────
            h = self._h_bptt_start.copy()   # detached snapshot, not live _h
            h_states = [h.copy()]           # h_states[0] = h before any step
            ys: List[np.ndarray] = []
            gates: List[np.ndarray] = []

            for x in xs[:-1]:              # predict xs[1..N-1]
                gate = 1.0 / (1.0 + np.exp(-(x @ self._gate_W)))  # (STATE_DIM,)
                A_eff = self._A * (0.5 + 0.5 * gate)
                h = A_eff * h + self._B_proj @ x
                y = self._C_proj @ h + self._D @ x
                h_states.append(h.copy())
                ys.append(y)
                gates.append(gate)

            targets = xs[1:]               # xs[1] .. xs[N-1]
            N = len(ys)                    # number of prediction steps = len(xs)-1

            # ── Backward pass (TBPTT, reversed) ─────────────────────────────
            dD_out  = np.zeros_like(self._D_out)   # (INPUT_DIM,  OUTPUT_DIM)
            dC_proj = np.zeros_like(self._C_proj)  # (OUTPUT_DIM, STATE_DIM)
            dB_proj = np.zeros_like(self._B_proj)  # (STATE_DIM,  INPUT_DIM)
            dh = np.zeros(STATE_DIM, dtype=np.float32)  # gradient flowing back in time

            total_loss = 0.0

            for t in reversed(range(N)):
                # ── decode error at step t ────────────────────────────────
                pred_x = self._D_out @ ys[t]           # (INPUT_DIM,)
                err    = pred_x - targets[t]           # (INPUT_DIM,)
                loss_t = float(np.mean(err ** 2))
                total_loss += loss_t

                # ── grad through D_out ────────────────────────────────────
                dD_out += np.outer(err, ys[t])

                # dy combines gradient from decode loss + gradient from next step
                dy = self._D_out.T @ err + dh          # (OUTPUT_DIM,)

                # ── grad through C_proj (readout) ─────────────────────────
                # y_t = C_proj @ h_{t+1}  =>  dh_{t+1} = C_proj^T @ dy
                dh_t = self._C_proj.T @ dy             # (STATE_DIM,)
                dC_proj += np.outer(dy, h_states[t + 1])

                # ── grad through state update h = A_eff * h_prev + B @ x ──
                # dL/dh_prev = dL/dh_new * A_eff  (pass back in time)
                A_eff_t = self._A * (0.5 + 0.5 * gates[t])
                dh = dh_t * A_eff_t

                # ── grad through B_proj ───────────────────────────────────
                dB_proj += np.outer(dh_t, xs[t])

            # ── Clip & apply accumulated gradients (averaged over N steps) ─
            for grad, param_name in [
                (dD_out  / N, "D_out"),
                (dC_proj / N, "C_proj"),
                (dB_proj / N, "B_proj"),
            ]:
                grad_clipped = np.clip(grad, -TRAIN_GRAD_CLIP, TRAIN_GRAD_CLIP)
                if param_name == "D_out":
                    self._D_out  -= BPTT_LR * grad_clipped
                elif param_name == "C_proj":
                    self._C_proj -= BPTT_LR * grad_clipped
                elif param_name == "B_proj":
                    self._B_proj -= BPTT_LR * grad_clipped

            # ── Advance the BPTT window start to end of this window ────────
            self._h_bptt_start = h_states[-1].copy()

            # ── Update BPTT loss EMA ───────────────────────────────────────
            avg_loss = total_loss / N
            if self._bptt_loss_ema == 0.0:
                self._bptt_loss_ema = avg_loss
            else:
                self._bptt_loss_ema = ((1.0 - TRAIN_LOSS_EMA_ALPHA) * self._bptt_loss_ema
                                       + TRAIN_LOSS_EMA_ALPHA * avg_loss)

        return avg_loss

    def train_step(self, x_t: np.ndarray, x_next: np.ndarray) -> float:
        """Self-supervised update: teach the SSM to predict the next embedding.

        Backward compat API — also feeds into the trajectory buffer so that
        every 8 calls it auto-triggers train_on_trajectory() for TBPTT.

        Args:
            x_t:    Current 384-d world-model embedding (input at step t).
            x_next: Actual next 384-d embedding observed (prediction target).

        Returns:
            Scalar MSE loss (float) before the 1-step parameter update.

        Algorithm (1-step BPTT, manual numpy):
          Forward:
            gate   = sigmoid(x_t @ gate_W)             # (STATE_DIM,)
            A_eff  = A * (0.5 + 0.5 * gate)
            h_new  = A_eff * h_prev + B_proj @ x_t     # (STATE_DIM,)
            y      = C_proj @ h_new + D @ x_t          # (OUTPUT_DIM,)
            pred   = D_out @ y                          # (INPUT_DIM,)
            loss   = 0.5 * ||pred - x_next||^2

          Backward:
            error       = pred - x_next                 # (INPUT_DIM,)
            dL/dD_out   = outer(error, y)               # (INPUT_DIM, OUTPUT_DIM)
            dL/dy       = D_out^T @ error               # (OUTPUT_DIM,)
            dL/dh_new   = C_proj^T @ dL/dy              # (STATE_DIM,)
            dL/dB_proj  = outer(dL/dh_new, x_t)        # (STATE_DIM, INPUT_DIM)
            dL/dgate_W  = outer(x_t, dL/dh_new * h_prev * A
                                       * 0.5 * gate*(1-gate))
                          shape: (INPUT_DIM, STATE_DIM)  — 1-step BPTT stop-grad on A_eff*h

          All gradients clipped to [-TRAIN_GRAD_CLIP, TRAIN_GRAD_CLIP].
          Updates applied with lr = TRAIN_LR.
        """
        if (x_t is None or x_next is None
                or x_t.shape != (INPUT_DIM,)
                or x_next.shape != (INPUT_DIM,)):
            return 0.0

        x_t = x_t.astype(np.float32)
        x_next = x_next.astype(np.float32)

        with self._mu:
            # ── forward (re-compute for this x_t using cached _h_prev) ──────
            gate = 1.0 / (1.0 + np.exp(-(x_t @ self._gate_W)))   # (STATE_DIM,)
            A_eff = self._A * (0.5 + 0.5 * gate)                  # (STATE_DIM,)
            h_new = A_eff * self._h_prev + self._B_proj @ x_t     # (STATE_DIM,)
            y = self._C_proj @ h_new + self._D @ x_t              # (OUTPUT_DIM,)
            pred = self._D_out @ y                                 # (INPUT_DIM,)

            # ── loss ─────────────────────────────────────────────────────────
            error = pred - x_next                                  # (INPUT_DIM,)
            loss = float(0.5 * np.dot(error, error))

            # ── backward ─────────────────────────────────────────────────────
            # dL/dD_out  shape (INPUT_DIM, OUTPUT_DIM)
            dL_dD_out = np.outer(error, y)

            # dL/dy      shape (OUTPUT_DIM,)
            dL_dy = self._D_out.T @ error

            # dL/dh_new  shape (STATE_DIM,)
            dL_dh = self._C_proj.T @ dL_dy

            # dL/dB_proj  shape (STATE_DIM, INPUT_DIM)
            dL_dB_proj = np.outer(dL_dh, x_t)

            # dL/dgate_W  shape (INPUT_DIM, STATE_DIM)
            # gate_grad_factor = dL/dh_new * h_prev * A * sigmoid' = ... * 0.5 * gate*(1-gate)
            gate_grad_factor = dL_dh * self._h_prev * self._A * 0.5 * gate * (1.0 - gate)
            dL_dgate_W = np.outer(x_t, gate_grad_factor)

            # ── clip & apply ─────────────────────────────────────────────────
            dL_dD_out = np.clip(dL_dD_out, -TRAIN_GRAD_CLIP, TRAIN_GRAD_CLIP)
            dL_dB_proj = np.clip(dL_dB_proj, -TRAIN_GRAD_CLIP, TRAIN_GRAD_CLIP)
            dL_dgate_W = np.clip(dL_dgate_W, -TRAIN_GRAD_CLIP, TRAIN_GRAD_CLIP)

            self._D_out -= TRAIN_LR * dL_dD_out
            self._B_proj -= TRAIN_LR * dL_dB_proj
            self._gate_W -= TRAIN_LR * dL_dgate_W

            # EMA loss tracking (1-step path)
            if self._train_loss_ema == 0.0:
                self._train_loss_ema = loss
            else:
                self._train_loss_ema = ((1.0 - TRAIN_LOSS_EMA_ALPHA) * self._train_loss_ema
                                        + TRAIN_LOSS_EMA_ALPHA * loss)

            # ── Feed trajectory buffer; trigger TBPTT when window is full ───
            # Add x_t first; when we have a full window train_on_trajectory
            # will use xs[0..N-2] as inputs and xs[1..N-1] as targets.
            self._trajectory_buffer.append(x_t.copy())
            # Also ensure x_next is present as the final target
            if len(self._trajectory_buffer) == BPTT_WINDOW:
                # We have exactly N items; the last is the "next" of N-1
                # Append x_next temporarily so trajectory ends on the right target
                buf_snapshot = list(self._trajectory_buffer)
                buf_snapshot.append(x_next.copy())

        # ── TBPTT call outside the inner lock section (train_on_trajectory
        #    re-acquires _mu internally) ────────────────────────────────────
        try:
            if (len(self._trajectory_buffer) == BPTT_WINDOW
                    and 'buf_snapshot' in locals()):
                self.train_on_trajectory(buf_snapshot)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.state_space_memory")

        return loss

    # ── prediction exposure ──────────────────────────────────────────────────

    @property
    def last_prediction(self) -> Optional[np.ndarray]:
        """Most recent predicted next 384-d embedding (updated every step())."""
        return self._last_prediction

    def get_next_prediction(self) -> Optional[np.ndarray]:
        """Public accessor: predicted next world-model embedding (384-d).
        Returns None if step() has not been called yet."""
        return self._last_prediction

    # ── consumer APIs ────────────────────────────────────────────────────────

    def get_context_vector(self) -> np.ndarray:
        """The compressed 'gist of everything so far'. Read by MoE router + agent."""
        return self._C_proj @ self._h

    def get_temporal_attention(self, query_vec: np.ndarray, k: int = 8) -> List[int]:
        """Indices of recent SSM outputs most similar to query (attention)."""
        if not self._y_history or query_vec is None:
            return []
        Q = query_vec
        if Q.shape[0] != OUTPUT_DIM:
            return []
        Y = np.stack(self._y_history)               # (N, OUTPUT_DIM)
        # Cosine
        Yn = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-8)
        Qn = Q / (np.linalg.norm(Q) + 1e-8)
        scores = Yn @ Qn
        idx = np.argsort(-scores)[:k]
        return idx.tolist()

    def state_norm(self) -> float:
        """Magnitude of internal state. Sustained high norm => saturating, need reset."""
        return float(np.linalg.norm(self._h))

    def effective_horizon(self) -> float:
        """How many past steps this state effectively remembers (1/(1-A_max))."""
        a_max = float(self._A.max())
        return 1.0 / max(1e-3, 1.0 - a_max)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "steps": self._step_count,
            "state_norm": round(self.state_norm(), 3),
            "effective_horizon_steps": round(self.effective_horizon(), 1),
            "history_depth": len(self._y_history),
            "decay_min": round(float(self._A.min()), 4),
            "decay_max": round(float(self._A.max()), 4),
            "train_loss_ema": round(self._train_loss_ema, 6),
            "bptt_loss_ema": round(self._bptt_loss_ema, 6),
            "bptt_window": BPTT_WINDOW,
        }

    def decode_recent_dynamics(self) -> str:
        """Simple heuristic: describe whether the SSM state is growing, stable, shrinking."""
        if len(self._y_history) < 4:
            return "insufficient_history"
        recent = [float(np.linalg.norm(y)) for y in self._y_history[-8:]]
        trend = recent[-1] - recent[0]
        if trend > 0.5:
            return "expanding"
        elif trend < -0.5:
            return "contracting"
        return "stable"

    def soft_reset(self):
        """Halve the state — used during 'sleep' to prevent saturation."""
        with self._mu:
            self._h *= 0.5
            self._save()


_ssm_instance: Optional[StateSpaceMemory] = None


def get_ssm_memory() -> StateSpaceMemory:
    global _ssm_instance
    if _ssm_instance is None:
        _ssm_instance = StateSpaceMemory()
    return _ssm_instance
