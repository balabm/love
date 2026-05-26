"""
LOVE Latent World Model — Predictive Coding on Real Embeddings

Implements Friston's free-energy principle on top of ChromaDB's sentence-transformer
embeddings. This is the substrate every higher-level system reads from.

Architecture:
  state_t   = embed(observation_text)          # 384-d vector from MiniLM
  pred_t+1  = MLP(state_t)                     # residual 2-layer MLP next-state predictor
  error_t   = ||obs_t - pred_t||               # prediction error (free energy proxy)
  attention = softmax(error per channel)       # surprise drives attention
  MLP      <- online SGD backprop (lr=0.01)   # gradient through residual net

MLP architecture (residual):
  h        = relu(W1 @ x + b1)                # W1: hidden x 384, b1: hidden
  pred     = x + W2 @ h + b2                  # W2: 384 x hidden, b2: 384
  hidden   = 256

What's real here (not scaffolding):
  - Actual 384-d embeddings via chromadb's default EF
  - Actual residual MLP transition model learned online via SGD
  - Actual KL-like surprise signal that other modules can consume
  - Actual free-energy bound tracked over time (drives sleep/consolidation)

What this enables for other modules:
  - Sentinel: high surprise -> wake up, investigate
  - Homeostasis: sustained high free-energy -> trigger consolidation
  - MoE router: surprise per channel decides which expert to route to
  - Evolution: regions of state space with chronic high error -> capability gap
"""
from __future__ import annotations

import json
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data" / "world_model"
DATA_DIR.mkdir(parents=True, exist_ok=True)
# Old linear-weight file — kept for backward-compat detection only (never written)
_OLD_WEIGHTS_FILE = DATA_DIR / "transition_W.npy"
# New MLP params file (np.savez)
MLP_PARAMS_FILE = DATA_DIR / "mlp_params.npz"
STATE_FILE = DATA_DIR / "state.json"
TRAJECTORY = DATA_DIR / "trajectory.jsonl"

EMBED_DIM = 384    # MiniLM-L6-v2 default
MLP_HIDDEN = 256   # residual MLP hidden dimension
HISTORY = 64       # rolling context window for transition learning
LR_INIT = 0.02
LR_MIN = 0.001
MLP_LR = 0.01      # SGD learning rate for MLP weights
GRAD_CLIP = 0.05   # gradient clip bound
WEIGHT_DECAY = 0.9999  # L2 weight decay factor per step

ROLLOUT_STEPS = 4        # multi-step prediction horizon
ROLLOUT_LR = 0.005       # slightly lower than single-step lr (MLP_LR = 0.01)
ROLLOUT_WINDOW = 16      # keep last 16 embeddings for rollout training


# ── Embedding access ─────────────────────────────────────────────────────────

_ef = None
_ef_lock = threading.Lock()


def _get_embedder():
    """Lazy-load chromadb's default embedding function (sentence-transformers MiniLM)."""
    global _ef
    with _ef_lock:
        if _ef is None:
            try:
                from chromadb.utils import embedding_functions
                _ef = embedding_functions.DefaultEmbeddingFunction()
            except Exception as e:
                print(f"[WorldModel] embedder unavailable: {e}")
                _ef = False
        return _ef


def embed(text: str) -> Optional[np.ndarray]:
    ef = _get_embedder()
    if not ef:
        return None
    try:
        v = ef([text])[0]
        v = np.asarray(v, dtype=np.float32)
        # L2-normalize so cosine == dot product
        n = np.linalg.norm(v)
        return v / n if n > 0 else v
    except Exception:
        return None


# ── Data ─────────────────────────────────────────────────────────────────────

@dataclass
class Observation:
    t: float
    source: str               # "user", "system", "sensor", "agent"
    text: str
    state: np.ndarray         # 384-d
    pred_error: float = 0.0   # ||state - pred|| (surprise / free energy)
    free_energy: float = 0.0  # running EMA of pred_error


@dataclass
class WorldModelState:
    total_observations: int = 0
    cumulative_free_energy: float = 0.0
    ema_free_energy: float = 0.0
    lr: float = LR_INIT
    last_consolidation: str = ""


# ── Residual MLP helpers (pure numpy) ────────────────────────────────────────

def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, x)


def _relu_prime(x: np.ndarray) -> np.ndarray:
    """Derivative of ReLU (1 where x > 0, else 0)."""
    return (x > 0).astype(np.float32)


def _mlp_forward(
    x: np.ndarray,
    W1: np.ndarray, b1: np.ndarray,
    W2: np.ndarray, b2: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Forward pass of residual MLP.

    Returns:
        pred  : x + W2 @ h + b2          (384,)
        h     : relu(W1 @ x + b1)        (hidden,)
        pre_h : W1 @ x + b1              (hidden,)  — needed for backprop
    """
    pre_h = W1 @ x + b1          # (hidden,)
    h = _relu(pre_h)              # (hidden,)
    pred = x + W2 @ h + b2       # (384,)  — residual skip
    return pred, h, pre_h


def _mlp_backward_and_update(
    x: np.ndarray,
    pred: np.ndarray,
    h: np.ndarray,
    pre_h: np.ndarray,
    target: np.ndarray,
    W1: np.ndarray, b1: np.ndarray,
    W2: np.ndarray, b2: np.ndarray,
    lr: float = MLP_LR,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Backprop through residual MLP and return updated (W1, b1, W2, b2).

    Loss  = 0.5 * ||target - pred||^2
    dL/dpred = -(target - pred) / max(||target - pred||, 1e-8)   [normalized]

    Gradient flow:
      dL/db2 = dL/dpred
      dL/dW2 = outer(dL/dpred, h)
      dL/dh  = W2^T @ dL/dpred
      dL/dpre_h = dL/dh * relu'(pre_h)
      dL/db1 = dL/dpre_h
      dL/dW1 = outer(dL/dpre_h, x)
    """
    diff = target - pred                                     # (384,)
    norm = float(np.linalg.norm(diff))
    d_pred = -diff / max(norm, 1e-8)                         # (384,)

    # --- W2, b2 gradients ---
    d_b2 = d_pred.copy()                                     # (384,)
    d_W2 = np.outer(d_pred, h)                              # (384, hidden)

    # --- backprop through residual into h ---
    d_h = W2.T @ d_pred                                      # (hidden,)
    d_pre_h = d_h * _relu_prime(pre_h)                       # (hidden,)

    # --- W1, b1 gradients ---
    d_b1 = d_pre_h.copy()                                    # (hidden,)
    d_W1 = np.outer(d_pre_h, x)                             # (hidden, 384)

    # --- clip gradients ---
    np.clip(d_W1, -GRAD_CLIP, GRAD_CLIP, out=d_W1)
    np.clip(d_b1, -GRAD_CLIP, GRAD_CLIP, out=d_b1)
    np.clip(d_W2, -GRAD_CLIP, GRAD_CLIP, out=d_W2)
    np.clip(d_b2, -GRAD_CLIP, GRAD_CLIP, out=d_b2)

    # --- SGD update with L2 weight decay ---
    W1_new = W1 * WEIGHT_DECAY - lr * d_W1
    b1_new = b1 - lr * d_b1
    W2_new = W2 * WEIGHT_DECAY - lr * d_W2
    b2_new = b2 - lr * d_b2

    return W1_new, b1_new, W2_new, b2_new


# ── Engine ───────────────────────────────────────────────────────────────────

class LatentWorldModel:
    _instance: Optional["LatentWorldModel"] = None
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
        self._history: Deque[np.ndarray] = deque(maxlen=HISTORY)
        self._recent_obs: Deque[Observation] = deque(maxlen=256)
        self._channel_surprise: Dict[str, float] = {}  # per-source EMA error
        self._W1, self._b1, self._W2, self._b2 = self._load_mlp_params()
        self._state = self._load_state()
        self._rollout_buffer: Deque[np.ndarray] = deque(maxlen=ROLLOUT_WINDOW)
        self._rollout_loss_ema: float = 0.0

    # ── persistence ──────────────────────────────────────────────────────────

    def _init_mlp_params(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Initialise MLP weights from scratch.

        W1: He-init (fan_in = EMBED_DIM)
        W2: small near-zero so the residual skip dominates at t=0
        biases: zero
        """
        scale1 = math.sqrt(2.0 / EMBED_DIM)
        W1 = np.random.randn(MLP_HIDDEN, EMBED_DIM).astype(np.float32) * scale1
        b1 = np.zeros(MLP_HIDDEN, dtype=np.float32)
        scale2 = 0.01
        W2 = np.random.randn(EMBED_DIM, MLP_HIDDEN).astype(np.float32) * scale2
        b2 = np.zeros(EMBED_DIM, dtype=np.float32)
        return W1, b1, W2, b2

    def _load_mlp_params(
        self,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Load MLP params from mlp_params.npz.
        If the new file is missing (fresh install or old deployment with only
        transition_W.npy), initialise from scratch — the model relearns quickly.
        """
        if MLP_PARAMS_FILE.exists():
            try:
                data = np.load(str(MLP_PARAMS_FILE))
                W1 = data["W1"].astype(np.float32)
                b1 = data["b1"].astype(np.float32)
                W2 = data["W2"].astype(np.float32)
                b2 = data["b2"].astype(np.float32)
                if (
                    W1.shape == (MLP_HIDDEN, EMBED_DIM)
                    and b1.shape == (MLP_HIDDEN,)
                    and W2.shape == (EMBED_DIM, MLP_HIDDEN)
                    and b2.shape == (EMBED_DIM,)
                ):
                    return W1, b1, W2, b2
            except Exception:
                pass
        # Backward-compat note: old transition_W.npy exists — ignore it, init fresh.
        return self._init_mlp_params()

    def _save_mlp_params(self):
        try:
            np.savez(
                str(MLP_PARAMS_FILE),
                W1=self._W1, b1=self._b1,
                W2=self._W2, b2=self._b2,
            )
        except Exception:
            pass

    def _load_state(self) -> WorldModelState:
        if STATE_FILE.exists():
            try:
                d = json.loads(STATE_FILE.read_text())
                return WorldModelState(**d)
            except Exception:
                pass
        return WorldModelState()

    def _save_state(self):
        try:
            from dataclasses import asdict
            STATE_FILE.write_text(json.dumps(asdict(self._state), indent=2))
        except Exception:
            pass

    # ── core predict / observe / learn loop ──────────────────────────────────

    def predict_next(self, current: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
        """Predicted next-state given current state (or last history if None)."""
        with self._mu:
            if current is None:
                if not self._history:
                    return None
                current = self._history[-1]
            pred, _h, _pre_h = _mlp_forward(
                current, self._W1, self._b1, self._W2, self._b2
            )
            # renormalize to unit sphere
            n = np.linalg.norm(pred)
            return pred / n if n > 0 else pred

    def observe(self, text: str, source: str = "system") -> Observation:
        """Embed an observation, compute surprise, update MLP via online SGD."""
        state = embed(text)
        if state is None:
            return Observation(
                t=time.time(), source=source, text=text,
                state=np.zeros(EMBED_DIM, dtype=np.float32),
            )

        with self._mu:
            # 1) compute prediction error against last-state MLP prediction
            err = 0.0
            if self._history:
                prev = self._history[-1]
                pred, h, pre_h = _mlp_forward(
                    prev, self._W1, self._b1, self._W2, self._b2
                )
                pn = np.linalg.norm(pred)
                pred_norm = pred / pn if pn > 0 else pred
                diff = state - pred_norm
                err = float(np.linalg.norm(diff))

                # 2) online SGD: backprop through residual MLP
                #    We train against the un-normalised pred so gradients are
                #    well-scaled; the normalisation is only for the error metric.
                self._W1, self._b1, self._W2, self._b2 = _mlp_backward_and_update(
                    x=prev,
                    pred=pred,
                    h=h,
                    pre_h=pre_h,
                    target=state,
                    W1=self._W1, b1=self._b1,
                    W2=self._W2, b2=self._b2,
                    lr=MLP_LR,
                )

            # 3) update channel surprise EMA
            prev_surprise = self._channel_surprise.get(source, err)
            self._channel_surprise[source] = 0.9 * prev_surprise + 0.1 * err

            # 4) update global free-energy EMA
            self._state.ema_free_energy = 0.95 * self._state.ema_free_energy + 0.05 * err
            self._state.cumulative_free_energy += err
            self._state.total_observations += 1

            # 5) anneal learning rate (kept for state tracking; MLP uses MLP_LR)
            self._state.lr = max(
                LR_MIN,
                LR_INIT * (1000.0 / (1000.0 + self._state.total_observations)),
            )

            # 6) push into history — also fire SSM train_step on the transition
            prev_state_for_ssm = self._history[-1].copy() if self._history else None
            self._history.append(state)
            self._rollout_buffer.append(state)
            if prev_state_for_ssm is not None:
                try:
                    from core.state_space_memory import get_ssm_memory
                    _ssm = get_ssm_memory()
                    _ssm.step(prev_state_for_ssm)          # advance SSM on prev
                    _ssm.train_step(prev_state_for_ssm, state)  # supervise: predict curr
                except Exception:
                    pass

            obs = Observation(
                t=time.time(), source=source, text=text, state=state,
                pred_error=err, free_energy=self._state.ema_free_energy,
            )
            self._recent_obs.append(obs)

            # 7) periodic persist
            if self._state.total_observations % 50 == 0:
                self._save_mlp_params()
                self._save_state()
                self._append_trajectory(obs)

            # Flag for rollout training (executed outside lock to avoid deadlock)
            _do_rollout = (
                self._state.total_observations % 8 == 0
                and len(self._rollout_buffer) >= ROLLOUT_STEPS + 1
            )

        # 8) multi-step rollout BPTT (every 8 observations, outside lock)
        if _do_rollout:
            self.train_rollout()

        return obs

    def _append_trajectory(self, obs: Observation):
        try:
            with open(TRAJECTORY, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "t": obs.t, "source": obs.source,
                    "text": obs.text[:200],
                    "err": round(obs.pred_error, 4),
                    "fe": round(obs.free_energy, 4),
                }) + "\n")
        except Exception:
            pass

    # ── multi-step rollout BPTT ──────────────────────────────────────────────

    def train_rollout(self) -> float:
        """
        Multi-step rollout BPTT through the MLP.

        For each anchor in the buffer (all except last 4):
          - Roll out MLP for ROLLOUT_STEPS steps autoregressively
          - Compare each predicted step to the actual next embedding
          - Accumulate gradients backward through all steps (chain rule through MLP)

        Returns average rollout loss.
        """
        with self._mu:
            buf = list(self._rollout_buffer)
            if len(buf) < ROLLOUT_STEPS + 1:
                return 0.0

            total_loss = 0.0
            n_anchors = 0

            # Accumulate gradients across all anchors
            dW1_acc = np.zeros_like(self._W1)
            db1_acc = np.zeros_like(self._b1)
            dW2_acc = np.zeros_like(self._W2)
            db2_acc = np.zeros_like(self._b2)

            for anchor_idx in range(len(buf) - ROLLOUT_STEPS):
                x0 = buf[anchor_idx]
                targets = buf[anchor_idx + 1 : anchor_idx + ROLLOUT_STEPS + 1]

                # Forward rollout: x0 -> x1_pred -> x2_pred -> ... xK_pred
                rollout_states = [x0]
                rollout_h = []       # hidden activations h = relu(W1@x + b1)
                rollout_pre_h = []   # pre-activation (for gradient)
                rollout_preds = []   # MLP output at each step

                x = x0
                for step in range(ROLLOUT_STEPS):
                    pred, h, pre_h = _mlp_forward(x, self._W1, self._b1, self._W2, self._b2)
                    # normalize prediction (as actual embeddings are L2-normalized)
                    pn = np.linalg.norm(pred)
                    pred_norm = pred / pn if pn > 0 else pred
                    rollout_preds.append(pred)        # unnormalized (for gradient)
                    rollout_h.append(h)
                    rollout_pre_h.append(pre_h)
                    rollout_states.append(pred_norm)  # use normalized as next input
                    x = pred_norm

                # Backward through rollout (BPTT)
                # Loss at each step: 0.5 * ||pred - target||^2, weighted by recency
                dx_next = np.zeros_like(x0)  # gradient flowing back from future steps

                for step in reversed(range(ROLLOUT_STEPS)):
                    # Error at this step
                    diff = rollout_preds[step] - targets[step]
                    step_loss = float(np.mean(diff ** 2))
                    # Weight later steps less (they're harder to predict)
                    weight = 0.9 ** (ROLLOUT_STEPS - 1 - step)
                    total_loss += step_loss * weight

                    # Gradient of loss w.r.t pred (+ incoming gradient from next step)
                    dL_dpred = diff * weight  # (EMBED_DIM,)
                    dL_dpred += dx_next

                    # Backprop through MLP: accumulate grads instead of applying
                    x_in = rollout_states[step]
                    h = rollout_h[step]
                    pre_h = rollout_pre_h[step]

                    # d/dW2: outer(dL_dpred, h)  (residual: pred = x + W2@h + b2)
                    dW2_acc += np.outer(dL_dpred, h)
                    db2_acc += dL_dpred

                    # d/dh: W2^T @ dL_dpred
                    dh = self._W2.T @ dL_dpred

                    # d/dpre_h: dh * relu'(pre_h)
                    dpre_h = dh * (pre_h > 0).astype(np.float32)

                    # d/dW1, d/db1
                    dW1_acc += np.outer(dpre_h, x_in)
                    db1_acc += dpre_h

                    # Gradient of x_in (to pass back for chain rule through rollout)
                    dx_next = self._W1.T @ dpre_h   # approximate: only direct path

                n_anchors += 1

            if n_anchors == 0:
                return 0.0

            # Average gradients and apply
            scale = 1.0 / n_anchors
            lr = ROLLOUT_LR
            clip = 0.05

            for d_arr in [dW1_acc, db1_acc, dW2_acc, db2_acc]:
                d_arr *= scale

            np.clip(dW1_acc, -clip, clip, out=dW1_acc)
            np.clip(db1_acc, -clip, clip, out=db1_acc)
            np.clip(dW2_acc, -clip, clip, out=dW2_acc)
            np.clip(db2_acc, -clip, clip, out=db2_acc)

            self._W1 = self._W1 * WEIGHT_DECAY - lr * dW1_acc
            self._b1 = self._b1 - lr * db1_acc
            self._W2 = self._W2 * WEIGHT_DECAY - lr * dW2_acc
            self._b2 = self._b2 - lr * db2_acc

            avg_loss = total_loss / (n_anchors * ROLLOUT_STEPS)
            self._rollout_loss_ema = 0.95 * self._rollout_loss_ema + 0.05 * avg_loss
            return avg_loss

    # ── consumer APIs for other modules ──────────────────────────────────────

    def surprise(self) -> float:
        """Current surprise (last prediction error). 0 = perfect prediction."""
        if not self._recent_obs:
            return 0.0
        return self._recent_obs[-1].pred_error

    def free_energy(self) -> float:
        """Running EMA of surprise — high = world is unpredictable, need to learn/sleep."""
        return self._state.ema_free_energy

    def channel_surprise(self) -> Dict[str, float]:
        """Per-source surprise — which channel is most informative right now."""
        return dict(self._channel_surprise)

    def attention_distribution(self) -> Dict[str, float]:
        """Softmax over channel surprise — where attention should go."""
        s = self._channel_surprise
        if not s:
            return {}
        keys = list(s.keys())
        vals = np.array([s[k] for k in keys], dtype=np.float32)
        # temperature 0.5 sharpens
        e = np.exp((vals - vals.max()) / 0.5)
        e = e / e.sum()
        return {k: float(v) for k, v in zip(keys, e)}

    # alias used by external callers
    channel_attention = attention_distribution

    def trajectory_similarity(self, text: str, k: int = 5) -> List[Tuple[float, Observation]]:
        """Cosine-similar recent observations — semantic 'where am I now'."""
        q = embed(text)
        if q is None or not self._recent_obs:
            return []
        scored = [(float(np.dot(q, o.state)), o) for o in self._recent_obs]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    def should_consolidate(self, threshold: float = 0.6) -> bool:
        """Free-energy above threshold => model is struggling, time to sleep/consolidate."""
        return self._state.ema_free_energy > threshold

    def consolidate(self):
        """Alias for reset_after_consolidation — called by external consolidation triggers."""
        self.reset_after_consolidation()

    def reset_after_consolidation(self):
        with self._mu:
            self._state.ema_free_energy *= 0.5
            self._state.last_consolidation = datetime.now().isoformat()
            self._save_state()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "total_observations": self._state.total_observations,
            "ema_free_energy": round(self._state.ema_free_energy, 4),
            "lr": round(self._state.lr, 5),
            "mlp_hidden_dim": MLP_HIDDEN,
            "channels": {k: round(v, 4) for k, v in self._channel_surprise.items()},
            "history_depth": len(self._history),
            "last_surprise": round(self.surprise(), 4),
            "last_consolidation": self._state.last_consolidation,
            "rollout_loss_ema": round(self._rollout_loss_ema, 6),
            "rollout_horizon": ROLLOUT_STEPS,
        }


_world_model_instance: Optional[LatentWorldModel] = None


def get_world_model_latent() -> LatentWorldModel:
    global _world_model_instance
    if _world_model_instance is None:
        _world_model_instance = LatentWorldModel()
    return _world_model_instance
