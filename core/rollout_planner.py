"""
LOVE Rollout Planner — Look-ahead planning via world model rollouts.

Instead of responding immediately, LOVE simulates what happens to its
predicted state under different response strategies, then picks the one
that minimises predicted free energy (surprise) over a 4-step horizon.

Architecture:
  1. Get current world model state (last embedding in history)
  2. Generate K candidate "response direction" embeddings
     (each represents a different style/content direction)
  3. For each candidate: roll out MLP for ROLLOUT_STEPS steps
  4. Compute cumulative predicted free energy across all steps
  5. Return the candidate with lowest total predicted error

This is Model Predictive Control (MPC) applied to language.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from core.world_model_latent import (
    LatentWorldModel,
    get_world_model_latent,
    embed,
    _mlp_forward,
)

# ── Constants ────────────────────────────────────────────────────────────────

ROLLOUT_STEPS = 4          # default horizon (matches world_model_latent.ROLLOUT_STEPS)
BLEND_ALPHA = 0.7          # weight on current state vs candidate direction
DISCOUNT = 0.9             # recency discount per step
MAX_PLANNING_MS = 200      # timeout for get_planning_context()

DEFAULT_STYLES: List[str] = [
    "direct factual answer",
    "empathetic supportive response",
    "analytical deep-dive",
    "concise one-liner",
    "proactive with follow-up question",
    "creative lateral thinking",
]


# ── Core engine ──────────────────────────────────────────────────────────────

class RolloutPlanner:
    """
    Model Predictive Control planner over the latent world model.

    Uses the world model's residual MLP to simulate K candidate response
    directions forward for `horizon` steps and ranks them by accumulated
    predicted free energy (transition surprise).  Lower FE == less
    surprising transition trajectory == preferred response strategy.
    """

    _instance: Optional["RolloutPlanner"] = None
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

        # Stats
        self._total_plans: int = 0
        self._sum_winner_fe: float = 0.0
        self._last_winner: str = ""
        self._last_plan_ts: Optional[str] = None

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _get_world_model(self) -> LatentWorldModel:
        return get_world_model_latent()

    def _current_state(self, query_embedding: np.ndarray) -> np.ndarray:
        """Return the last known world-model embedding, or fall back to query."""
        m = self._get_world_model()
        with m._mu:
            if len(m._history) > 0:
                return np.array(m._history[-1], dtype=np.float32)
        return np.array(query_embedding, dtype=np.float32)

    def _blend_and_norm(
        self,
        current: np.ndarray,
        candidate: np.ndarray,
    ) -> np.ndarray:
        """Blend current state with candidate direction, then L2-normalise."""
        blended = BLEND_ALPHA * current + (1.0 - BLEND_ALPHA) * candidate
        norm = float(np.linalg.norm(blended))
        return blended / norm if norm > 1e-8 else blended

    def _rollout_fe(
        self,
        x0: np.ndarray,
        horizon: int,
        W1: np.ndarray,
        b1: np.ndarray,
        W2: np.ndarray,
        b2: np.ndarray,
    ) -> float:
        """
        Simulate world model MLP forward for `horizon` steps from x0.

        Returns discounted cumulative free energy:
            FE = sum_t  ||pred_t - x_t|| * discount^t
        """
        x = x0.copy()
        total_fe = 0.0
        for step in range(horizon):
            pred, h, pre_h = _mlp_forward(x, W1, b1, W2, b2)
            step_surprise = float(np.linalg.norm(pred - x))
            total_fe += step_surprise * (DISCOUNT ** step)
            # Advance: the prediction becomes the next state
            # (normalise to stay on unit sphere, consistent with embed())
            pred_norm = float(np.linalg.norm(pred))
            x = pred / pred_norm if pred_norm > 1e-8 else pred
        return total_fe

    # ── Public API ───────────────────────────────────────────────────────────

    def plan(
        self,
        query_embedding: np.ndarray,
        candidates: List[str],
        horizon: int = ROLLOUT_STEPS,
    ) -> Dict[str, Any]:
        """
        Rank candidate response strategies by predicted free energy.

        Parameters
        ----------
        query_embedding : np.ndarray
            384-d embedding of the user's query (pre-normalised).
        candidates : List[str]
            2-8 candidate response strategy descriptions.
        horizon : int
            Number of MLP rollout steps (default 4).

        Returns
        -------
        dict with winner_idx, winner_candidate, winner_fe, all_scores, horizon,
        current_state_norm.
        """
        if not candidates:
            candidates = DEFAULT_STYLES[:]

        # Snapshot MLP weights once (thread-safe read)
        m = self._get_world_model()
        with m._mu:
            W1 = m._W1.copy()
            b1 = m._b1.copy()
            W2 = m._W2.copy()
            b2 = m._b2.copy()

        current_state = self._current_state(query_embedding)
        current_state_norm = float(np.linalg.norm(current_state))

        scores: List[Dict[str, Any]] = []

        for cand_text in candidates:
            # Embed candidate strategy string
            cand_emb = embed(cand_text)
            if cand_emb is None:
                # Fallback: use a tiny random perturbation of query so we
                # still produce a valid (if weak) ranking.
                rng = np.random.default_rng(abs(hash(cand_text)) & 0xFFFFFFFF)
                noise = rng.standard_normal(384).astype(np.float32) * 0.05
                cand_emb = query_embedding + noise
                n = float(np.linalg.norm(cand_emb))
                if n > 1e-8:
                    cand_emb = cand_emb / n

            x0 = self._blend_and_norm(current_state, cand_emb)
            fe = self._rollout_fe(x0, horizon, W1, b1, W2, b2)
            scores.append({"candidate": cand_text, "fe": fe})

        # Sort ascending — lower free energy is better
        scores_sorted = sorted(scores, key=lambda s: s["fe"])

        # Assign ranks (1 = best)
        for rank, entry in enumerate(scores_sorted, start=1):
            entry["rank"] = rank

        # Restore original candidate order in all_scores
        rank_by_name = {e["candidate"]: e["rank"] for e in scores_sorted}
        all_scores = [
            {
                "candidate": e["candidate"],
                "fe": e["fe"],
                "rank": rank_by_name[e["candidate"]],
            }
            for e in scores
        ]

        winner = scores_sorted[0]
        winner_idx = next(
            i for i, e in enumerate(candidates) if e == winner["candidate"]
        )

        # Update stats
        with self._mu:
            self._total_plans += 1
            self._sum_winner_fe += winner["fe"]
            self._last_winner = winner["candidate"]
            self._last_plan_ts = datetime.utcnow().isoformat()

        return {
            "winner_idx": winner_idx,
            "winner_candidate": winner["candidate"],
            "winner_fe": winner["fe"],
            "all_scores": all_scores,
            "horizon": horizon,
            "current_state_norm": current_state_norm,
        }

    def plan_response_style(
        self,
        query: str,
        styles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        High-level wrapper: embed query → plan over style candidates.

        Falls back to DEFAULT_STYLES when no styles are supplied.
        """
        style_list = styles if styles else DEFAULT_STYLES[:]

        q_emb = embed(query)
        if q_emb is None:
            # Last-ditch fallback: uniform random unit vector
            v = np.random.randn(384).astype(np.float32)
            v /= max(float(np.linalg.norm(v)), 1e-8)
            q_emb = v

        return self.plan(q_emb, style_list)

    def get_planning_context(self, query: str) -> str:
        """
        Convenience method for agent.py prompt injection.

        Returns a 1-line hint string if planning completes within 200 ms,
        otherwise returns an empty string.
        """
        t0 = time.monotonic()
        try:
            result = self.plan_response_style(query)
            elapsed_ms = (time.monotonic() - t0) * 1000.0
            if elapsed_ms > MAX_PLANNING_MS:
                return ""
            w = result["winner_candidate"]
            fe = result["winner_fe"]
            return f"[planner: {w} predicted lowest surprise over 4 steps (FE={fe:.3f})]"
        except Exception:
            return ""

    def snapshot(self) -> Dict[str, Any]:
        """Return planner telemetry."""
        with self._mu:
            total = self._total_plans
            avg_fe = (
                self._sum_winner_fe / total if total > 0 else 0.0
            )
            return {
                "total_plans": total,
                "avg_winner_fe": round(avg_fe, 5),
                "last_plan_winner": self._last_winner,
                "last_plan_timestamp": self._last_plan_ts,
            }


# ── Singleton accessor ───────────────────────────────────────────────────────

def get_rollout_planner() -> RolloutPlanner:
    """Return the process-global RolloutPlanner singleton."""
    return RolloutPlanner()
