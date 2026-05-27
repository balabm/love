"""
LOVE Rollout Planner — Active MPC planning via world model rollouts.

Wave 27 upgrade: Active Planning Loop.

Before:  Planner injected a passive hint into the prompt; LLM could ignore it.
After:   Planner selects the response style as a *directive*, the prompt
         enforces it, and post-response verification compares predicted vs
         actual free energy to improve future planning.

Architecture:
  1. Get current world model state (last embedding in history)
  2. Generate K candidate "response direction" embeddings
     (each represents a different style/content direction)
  3. For each candidate: roll out MLP for ROLLOUT_STEPS steps
  4. Compute cumulative predicted free energy across all steps
  5. Return the candidate with lowest total predicted error
  6. NEW: After response, embed it and compare actual FE vs predicted FE
  7. NEW: Feed prediction delta back to calibrate planning confidence

This is Model Predictive Control (MPC) applied to language.
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

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

# Outcome learning
DATA_DIR = Path(__file__).parent.parent / "data" / "planner"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"
CALIBRATION_FILE = DATA_DIR / "calibration.json"
OUTCOME_WINDOW = 50        # keep last N outcomes for calibration

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

        # Outcome learning (Wave 27)
        self._pending_plan: Optional[Dict[str, Any]] = None  # plan awaiting verification
        self._outcomes: Deque[Dict[str, Any]] = deque(maxlen=OUTCOME_WINDOW)
        self._calibration = self._load_calibration()
        self._style_accuracy: Dict[str, List[float]] = {}  # style -> recent prediction errors

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

    # ── Query category detection (Wave 28) ───────────────────────────────────

    _CATEGORY_KEYWORDS: Dict[str, List[str]] = {
        "casual": ["hey", "hi", "hello", "what's up", "yo", "sup", "morning",
                   "evening", "how are you", "how's it going", "good day",
                   "thanks", "thank you", "nice", "cool", "lol", "haha"],
        "emotional": ["feel", "feeling", "sad", "happy", "stressed", "anxious",
                      "worried", "angry", "upset", "lonely", "tired", "burned out",
                      "overwhelmed", "excited", "nervous", "scared", "depressed",
                      "frustrated", "disappointed", "grateful", "love", "miss"],
        "technical": ["code", "function", "bug", "error", "fix", "implement",
                      "architecture", "api", "database", "query", "deploy",
                      "build", "compile", "debug", "refactor", "algorithm",
                      "model", "train", "pipeline", "server", "client",
                      "frontend", "backend", "framework", "library"],
        "task": ["need to", "plan", "schedule", "remind me", "task", "todo",
                 "deadline", "meeting", "call", "email", "send", "prepare",
                 "review", "check", "follow up", "coordinate", "arrange",
                 "book", "reserve", "appointment"],
    }

    def detect_query_category(self, query: str) -> str:
        """Classify query into casual/emotional/technical/task."""
        q_lower = query.lower()
        scores: Dict[str, int] = {}
        for category, keywords in self._CATEGORY_KEYWORDS.items():
            scores[category] = sum(1 for kw in keywords if kw in q_lower)
        # If no keywords match, use embedding similarity to determine
        if max(scores.values(), default=0) == 0:
            return "casual"  # default
        # Tie-break: prefer emotional over technical, technical over task, task over casual
        order = ["emotional", "technical", "task", "casual"]
        best_score = max(scores.values())
        tied = [c for c, s in scores.items() if s == best_score]
        for c in order:
            if c in tied:
                return c
        return tied[0]

    def _get_category_calibration(self, category: str, style: str) -> float:
        """Get prediction accuracy for a style in a specific category."""
        key = f"{category}:{style}"
        history = self._style_accuracy.get(key, [])
        if not history:
            # Fall back to global style accuracy
            return self._get_style_accuracy(style)
        return sum(history) / len(history)

    # ── Active planning (Wave 27) ──────────────────────────────────────────

    def plan_active(self, query: str) -> Dict[str, Any]:
        """
        Active planning: select style, store pending plan for verification.

        Wave 28: Category-aware — detects query type (casual/emotional/technical/task)
        and uses per-category calibration for directive strength.

        Returns dict with:
          - winner_style: the selected response style string
          - directive: prompt directive enforcing the style
          - plan_id: unique ID for outcome tracking
          - all_scores: full ranking for transparency
          - category: detected query category
        """
        result = self.plan_response_style(query)
        winner = result["winner_candidate"]
        category = self.detect_query_category(query)
        plan_id = f"plan_{int(time.time() * 1000)}"

        # Store pending plan for post-response verification
        pending = {
            "plan_id": plan_id,
            "query": query[:200],
            "winner_style": winner,
            "category": category,
            "predicted_fe": result["winner_fe"],
            "all_scores": result["all_scores"],
            "timestamp": time.time(),
        }
        with self._mu:
            self._pending_plan = pending

        # Build directive — category-aware calibration (Wave 28)
        directive = self._build_directive(winner, result, category=category)

        return {
            "winner_style": winner,
            "directive": directive,
            "plan_id": plan_id,
            "all_scores": result["all_scores"],
            "predicted_fe": result["winner_fe"],
            "category": category,
        }

    def _build_directive(self, winner: str, result: Dict, category: str = "") -> str:
        """Build a prompt directive from the planning result (Wave 28: category-aware)."""
        # Get calibration confidence for this style (category-aware if available)
        confidence = self._calibration.get("confidence", 0.5)
        style_acc = self._get_style_accuracy(winner)
        cat_acc = self._get_category_calibration(category, winner) if category else style_acc

        # Use the more specific accuracy if category is available
        effective_acc = cat_acc if category else style_acc

        # Strong directive when confidence is high, softer when uncertain
        if confidence > 0.6 and effective_acc > 0.4:
            strength = "RESPOND IN THIS STYLE"
        elif confidence > 0.3:
            strength = "Prefer this response style"
        else:
            strength = "Consider this response style"

        fe = result["winner_fe"]
        runner_up = ""
        scores = result.get("all_scores", [])
        ranked = sorted(scores, key=lambda s: s.get("rank", 99))
        if len(ranked) >= 2:
            runner_up = f" (runner-up: {ranked[1]['candidate']})"

        cat_hint = f" [{category}]" if category else ""
        return (
            f"\n\n=== PLANNED RESPONSE STYLE (world model MPC, 4-step lookahead) ===\n"
            f"{strength}: **{winner}**{runner_up}{cat_hint}\n"
            f"Predicted surprise: {fe:.3f} | Planning confidence: {confidence:.0%}\n"
        )

    # ── Outcome verification (Wave 27C) ──────────────────────────────────

    def verify_outcome(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        After LLM responds, embed the response and compare predicted vs actual FE.
        Feeds the prediction delta back to calibrate future planning.

        Returns outcome record, or None if no pending plan.
        """
        with self._mu:
            pending = self._pending_plan
            self._pending_plan = None

        if pending is None:
            return None

        # Embed the actual response
        response_emb = embed(response_text)
        if response_emb is None:
            return None

        # Compute actual free energy of the response trajectory
        m = self._get_world_model()
        with m._mu:
            W1 = m._W1.copy()
            b1 = m._b1.copy()
            W2 = m._W2.copy()
            b2 = m._b2.copy()

        actual_fe = self._rollout_fe(response_emb, ROLLOUT_STEPS, W1, b1, W2, b2)
        predicted_fe = pending["predicted_fe"]

        # Prediction error: how far off were we?
        prediction_delta = actual_fe - predicted_fe
        abs_delta = abs(prediction_delta)

        # Was our prediction accurate? (within 20% is "good")
        prediction_accurate = abs_delta < max(0.1, predicted_fe * 0.2)

        outcome = {
            "plan_id": pending["plan_id"],
            "query": pending["query"],
            "winner_style": pending["winner_style"],
            "category": pending.get("category", ""),
            "predicted_fe": round(predicted_fe, 5),
            "actual_fe": round(actual_fe, 5),
            "prediction_delta": round(prediction_delta, 5),
            "prediction_accurate": prediction_accurate,
            "timestamp": time.time(),
        }

        # Update calibration (global + per-style + per-category)
        self._update_calibration(outcome)

        # Persist
        self._persist_outcome(outcome)

        with self._mu:
            self._outcomes.append(outcome)

        return outcome

    def _update_calibration(self, outcome: Dict[str, Any]) -> None:
        """Update planning confidence based on prediction accuracy (Wave 28: per-category)."""
        style = outcome["winner_style"]
        category = outcome.get("category", "")
        accurate = outcome["prediction_accurate"]
        delta = abs(outcome["prediction_delta"])

        # Update global confidence (EMA)
        current_conf = self._calibration.get("confidence", 0.5)
        signal = 1.0 if accurate else max(0.0, 1.0 - delta)
        new_conf = 0.9 * current_conf + 0.1 * signal
        self._calibration["confidence"] = round(new_conf, 4)

        # Update per-style accuracy
        if style not in self._style_accuracy:
            self._style_accuracy[style] = []
        self._style_accuracy[style].append(1.0 if accurate else 0.0)
        if len(self._style_accuracy[style]) > 20:
            self._style_accuracy[style] = self._style_accuracy[style][-20:]

        # Update per-category accuracy (Wave 28)
        if category:
            cat_key = f"{category}:{style}"
            if cat_key not in self._style_accuracy:
                self._style_accuracy[cat_key] = []
            self._style_accuracy[cat_key].append(1.0 if accurate else 0.0)
            if len(self._style_accuracy[cat_key]) > 20:
                self._style_accuracy[cat_key] = self._style_accuracy[cat_key][-20:]

            # Also update category-level aggregate
            cat_agg_key = f"category:{category}"
            if cat_agg_key not in self._style_accuracy:
                self._style_accuracy[cat_agg_key] = []
            self._style_accuracy[cat_agg_key].append(1.0 if accurate else 0.0)
            if len(self._style_accuracy[cat_agg_key]) > 20:
                self._style_accuracy[cat_agg_key] = self._style_accuracy[cat_agg_key][-20:]

        # Update total outcomes count
        self._calibration["total_outcomes"] = self._calibration.get("total_outcomes", 0) + 1
        self._calibration["last_outcome_ts"] = datetime.utcnow().isoformat()

        # Persist calibration
        self._save_calibration()

    def _get_style_accuracy(self, style: str) -> float:
        """Get recent prediction accuracy for a specific style."""
        history = self._style_accuracy.get(style, [])
        if not history:
            return 0.5  # default: uncertain
        return sum(history) / len(history)

    # ── Calibration persistence ──────────────────────────────────────────

    def _load_calibration(self) -> Dict[str, Any]:
        try:
            if CALIBRATION_FILE.exists():
                return json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"confidence": 0.5, "total_outcomes": 0}

    def _save_calibration(self) -> None:
        try:
            CALIBRATION_FILE.write_text(
                json.dumps(self._calibration, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def _persist_outcome(self, outcome: Dict[str, Any]) -> None:
        try:
            with OUTCOMES_FILE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(outcome) + "\n")
        except Exception:
            pass

    # ── Active planning context (replaces passive hint) ──────────────────

    def get_planning_context(self, query: str) -> str:
        """
        Active planning for agent.py prompt injection (Wave 27 upgrade).

        Instead of a passive hint, this returns a directive that instructs
        the LLM to adopt the planned response style. Also stores the pending
        plan for post-response verification via verify_outcome().
        """
        t0 = time.monotonic()
        try:
            result = self.plan_active(query)
            elapsed_ms = (time.monotonic() - t0) * 1000.0
            if elapsed_ms > MAX_PLANNING_MS:
                # Timed out — fall back to no directive
                with self._mu:
                    self._pending_plan = None
                return ""
            return result["directive"]
        except Exception:
            return ""

    def snapshot(self) -> Dict[str, Any]:
        """Return planner telemetry (expanded for Wave 27 + 28)."""
        with self._mu:
            total = self._total_plans
            avg_fe = (
                self._sum_winner_fe / total if total > 0 else 0.0
            )

            # Outcome learning stats
            outcomes = list(self._outcomes)
            n_outcomes = len(outcomes)
            accurate_count = sum(1 for o in outcomes if o.get("prediction_accurate"))
            avg_delta = (
                sum(abs(o.get("prediction_delta", 0)) for o in outcomes) / n_outcomes
                if n_outcomes > 0 else 0.0
            )

            # Per-category stats (Wave 28)
            cat_stats: Dict[str, Any] = {}
            for cat in ["casual", "emotional", "technical", "task"]:
                cat_key = f"category:{cat}"
                if cat_key in self._style_accuracy:
                    vals = self._style_accuracy[cat_key]
                    cat_stats[cat] = {
                        "accuracy": round(sum(vals) / len(vals), 3),
                        "samples": len(vals),
                    }

            # Per-style accuracy
            style_acc: Dict[str, float] = {}
            for style, vals in self._style_accuracy.items():
                if ":" not in style:  # global style accuracy, not category-specific
                    style_acc[style] = round(sum(vals) / len(vals), 3)

            return {
                "total_plans": total,
                "avg_winner_fe": round(avg_fe, 5),
                "last_plan_winner": self._last_winner,
                "last_plan_timestamp": self._last_plan_ts,
                "calibration_confidence": self._calibration.get("confidence", 0.5),
                "total_outcomes": n_outcomes,
                "outcome_accuracy": round(accurate_count / n_outcomes, 3) if n_outcomes else 0.0,
                "avg_prediction_delta": round(avg_delta, 5),
                "has_pending_plan": self._pending_plan is not None,
                "per_category_stats": cat_stats,
                "per_style_accuracy": style_acc,
            }


# ── Singleton accessor ───────────────────────────────────────────────────────

def get_rollout_planner() -> RolloutPlanner:
    """Return the process-global RolloutPlanner singleton."""
    return RolloutPlanner()
