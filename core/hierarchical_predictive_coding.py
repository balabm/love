"""
LOVE Hierarchical Predictive Coding (HPC)

Friston's free-energy principle says brains *minimize prediction error* at every
level of a hierarchy. Lower levels predict raw sensory dynamics (LOVE: body +
world model). Higher levels predict abstract regularities (intent, plans).

Three-level hierarchy:

  Level 3 (slow):  PLAN / NARRATIVE
    Predicts what the user is doing this hour/day. Updates ~10 min.
    Error here triggers re-planning.

  Level 2 (mid):   CONTEXT / ACTIVITY
    Predicts what topic/activity is active. Updates ~1 min.
    Error here triggers context-switch awareness.

  Level 1 (fast):  SENSORY
    The latent world model itself. Updates every observation.
    Error here is per-step surprise.

Each level:
  - Holds a predicted state (embedding for L1/L2, label distribution for L3)
  - Receives the lower level's *prediction error* as input
  - Sends its prediction *downward* to constrain the lower level

Attention allocation = softmax over per-level prediction errors. The level
with highest unresolved error gets compute priority.

This is the closest classical-ML analog to a thalamus + cortex loop.
"""
from __future__ import annotations

import json
import math
import threading
import time
from collections import deque, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "hpc"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "hpc_state.json"
LEVELS_FILE = DATA_DIR / "levels.npz"
ERROR_LOG = DATA_DIR / "errors.jsonl"

EMBED_DIM = 384


@dataclass
class LevelState:
    name: str
    timescale_seconds: float
    last_update: float = 0.0
    error: float = 0.0          # unresolved prediction error at this level
    confidence: float = 0.5     # 1 - mean(error) over recent history


# ── L3: Plan / Narrative (label-distribution predictor) ──────────────────────

class PlanLevel:
    """Predicts a coarse activity label (work / rest / social / learn / health / unknown)."""
    LABELS = ["work", "rest", "social", "learn", "health", "creative", "transit", "unknown"]

    def __init__(self):
        # Prior distribution over labels (Dirichlet-ish via counts)
        self._counts: Dict[str, float] = {l: 1.0 for l in self.LABELS}
        # Predicted next label
        self._predicted_label: str = "unknown"
        # Hour-of-day prior — counts per (label, hour)
        self._hour_counts: Dict[Tuple[str, int], float] = {}

    def predict(self) -> Dict[str, float]:
        hour = datetime.now().hour
        # combine global prior with hour-conditional
        scores = {}
        total_global = sum(self._counts.values())
        for l in self.LABELS:
            global_p = self._counts[l] / total_global
            hour_count = self._hour_counts.get((l, hour), 0.5)
            scores[l] = global_p * (1.0 + math.log(1.0 + hour_count))
        # normalize
        z = sum(scores.values())
        dist = {k: v / z for k, v in scores.items()}
        self._predicted_label = max(dist, key=dist.get)
        return dist

    def observe(self, label: str):
        if label not in self._counts:
            label = "unknown"
        hour = datetime.now().hour
        self._counts[label] += 1.0
        self._hour_counts[(label, hour)] = self._hour_counts.get((label, hour), 0.0) + 1.0

    def error(self, observed_label: str) -> float:
        dist = self.predict()
        # cross-entropy with one-hot observed (capped)
        p = max(1e-3, dist.get(observed_label, 1e-3))
        return -math.log(p) / math.log(len(self.LABELS))   # normalized to [0, 1+]

    def serialize(self) -> Dict:
        return {
            "counts": self._counts,
            "hour_counts": {f"{k[0]}_{k[1]}": v for k, v in self._hour_counts.items()},
            "predicted_label": self._predicted_label,
        }

    def load(self, d: Dict):
        self._counts = d.get("counts", self._counts)
        hc = d.get("hour_counts", {})
        self._hour_counts = {}
        for k, v in hc.items():
            try:
                label, hour = k.rsplit("_", 1)
                self._hour_counts[(label, int(hour))] = v
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.hierarchical_predictive_coding")


# ── L2: Context / Activity (embedding centroid predictor) ────────────────────

class ContextLevel:
    """Tracks current activity centroid. Predicts: next obs is near this centroid."""

    def __init__(self):
        self._centroid: Optional[np.ndarray] = None
        self._inertia = 0.92   # exponential smoothing
        self._stability = 0.0   # 0..1; higher = stable context

    def predict(self) -> Optional[np.ndarray]:
        return self._centroid

    def observe_and_error(self, obs_embedding: np.ndarray) -> float:
        if obs_embedding is None:
            return 0.0
        if self._centroid is None:
            self._centroid = obs_embedding.copy()
            return 0.0
        # error = 1 - cosine_similarity
        sim = float(np.dot(obs_embedding, self._centroid))
        err = max(0.0, 1.0 - sim)
        # update centroid (EMA), renormalize
        self._centroid = self._inertia * self._centroid + (1 - self._inertia) * obs_embedding
        n = np.linalg.norm(self._centroid)
        if n > 0:
            self._centroid /= n
        # stability is 1 - rolling error
        self._stability = 0.9 * self._stability + 0.1 * (1.0 - err)
        return err

    def serialize(self) -> Dict:
        return {
            "centroid": self._centroid.tolist() if self._centroid is not None else None,
            "stability": self._stability,
        }

    def load(self, d: Dict):
        c = d.get("centroid")
        if c:
            self._centroid = np.asarray(c, dtype=np.float32)
        self._stability = d.get("stability", 0.0)


# ── HPC Engine ───────────────────────────────────────────────────────────────

class HierarchicalPredictiveCoding:
    _instance: Optional["HierarchicalPredictiveCoding"] = None
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
        self._level_states = {
            "L1_sensory":  LevelState(name="L1_sensory",  timescale_seconds=1.0),
            "L2_context":  LevelState(name="L2_context",  timescale_seconds=60.0),
            "L3_plan":     LevelState(name="L3_plan",     timescale_seconds=600.0),
        }
        self._L2 = ContextLevel()
        self._L3 = PlanLevel()
        self._context_switch_log: Deque[Tuple[float, float]] = deque(maxlen=128)   # (time, error)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load()

    # ── public API for observations ──────────────────────────────────────────

    def feed(self, text: str, source: str, hint_label: Optional[str] = None) -> Dict[str, float]:
        """One unified entry point. Returns per-level prediction errors."""
        from core.world_model_latent import get_world_model_latent, embed

        # L1: world model already computes per-obs surprise
        wm = get_world_model_latent()
        obs = wm.observe(text, source=source)
        l1_err = obs.pred_error
        emb = obs.state

        # L2: context-centroid drift
        l2_err = self._L2.observe_and_error(emb)

        # L3: plan/label prediction
        if hint_label is None:
            hint_label = self._infer_label(text, source)
        l3_err = self._L3.error(hint_label)
        self._L3.observe(hint_label)

        with self._mu:
            self._level_states["L1_sensory"].error = l1_err
            self._level_states["L2_context"].error = l2_err
            self._level_states["L3_plan"].error = l3_err
            for lv in self._level_states.values():
                lv.last_update = time.time()
                lv.confidence = 0.9 * lv.confidence + 0.1 * (1.0 - min(1.0, lv.error))

            # detect context switch
            if l2_err > 0.4:
                self._context_switch_log.append((time.time(), l2_err))

            self._log_errors(l1_err, l2_err, l3_err, hint_label)

        return {"L1_sensory": l1_err, "L2_context": l2_err, "L3_plan": l3_err}

    def _infer_label(self, text: str, source: str) -> str:
        """Cheap heuristic label inference. Caller can override with explicit hint."""
        t = text.lower()
        if source == "user":
            if any(w in t for w in ["meeting", "deadline", "code", "build", "task", "work"]):
                return "work"
            if any(w in t for w in ["tired", "sleep", "break", "rest"]):
                return "rest"
            if any(w in t for w in ["learn", "study", "read", "doc"]):
                return "learn"
            if any(w in t for w in ["workout", "run", "gym", "fitness"]):
                return "health"
            if any(w in t for w in ["friend", "family", "call", "chat"]):
                return "social"
        if source == "body":
            return "health"
        if source == "github" or "code" in t:
            return "work"
        return "unknown"

    # ── attention allocation (the actuator side) ─────────────────────────────

    def attention(self) -> Dict[str, float]:
        """Softmax over level errors. Caller schedules compute proportionally."""
        with self._mu:
            errs = np.array([self._level_states[k].error for k in ["L1_sensory", "L2_context", "L3_plan"]],
                            dtype=np.float32)
        # high error = high attention
        e = np.exp((errs - errs.max()) / 0.3)
        e = e / e.sum()
        return {
            "L1_sensory": float(e[0]),
            "L2_context": float(e[1]),
            "L3_plan":    float(e[2]),
        }

    def context_switch_rate(self, window_sec: float = 1800.0) -> float:
        """Switches per minute over the last `window_sec` — how scattered is attention?"""
        now = time.time()
        recent = [x for x in self._context_switch_log if now - x[0] < window_sec]
        if not recent:
            return 0.0
        return len(recent) / (window_sec / 60.0)

    def current_inferred_activity(self) -> str:
        return self._L3._predicted_label

    def context_stability(self) -> float:
        return self._L2._stability

    # ── loop ─────────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="LOVE-HPC")
        self._thread.start()
        print("[HPC] online — hierarchical predictive coding active")

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(45)
        while self._running:
            try:
                self._idle_predict()
            except Exception as e:
                print(f"[HPC] idle predict error: {e}")
            time.sleep(120)

    def _idle_predict(self):
        """In the absence of new observations, run pure-prediction step (dreaming)."""
        # L3 freshens its label distribution against current hour
        self._L3.predict()
        # persist occasionally
        if int(time.time()) % 600 < 120:
            self._save()

    # ── persistence ──────────────────────────────────────────────────────────

    def _log_errors(self, l1: float, l2: float, l3: float, label: str):
        try:
            with open(ERROR_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "t": datetime.now().isoformat(),
                    "L1": round(l1, 4), "L2": round(l2, 4), "L3": round(l3, 4),
                    "label": label,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.hierarchical_predictive_coding")

    def _save(self):
        try:
            with self._mu:
                STATE_FILE.write_text(json.dumps({
                    "levels": {k: asdict(v) for k, v in self._level_states.items()},
                    "L3": self._L3.serialize(),
                    "L2": self._L2.serialize(),
                }, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.hierarchical_predictive_coding")

    def _load(self):
        if not STATE_FILE.exists():
            return
        try:
            d = json.loads(STATE_FILE.read_text())
            for k, v in d.get("levels", {}).items():
                if k in self._level_states:
                    ls = self._level_states[k]
                    for kk, vv in v.items():
                        setattr(ls, kk, vv)
            self._L3.load(d.get("L3", {}))
            self._L2.load(d.get("L2", {}))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.hierarchical_predictive_coding")

    def snapshot(self) -> Dict[str, Any]:
        with self._mu:
            return {
                "levels": {
                    k: {"error": round(v.error, 4), "confidence": round(v.confidence, 3)}
                    for k, v in self._level_states.items()
                },
                "attention": {k: round(v, 3) for k, v in self.attention().items()},
                "inferred_activity": self.current_inferred_activity(),
                "context_stability": round(self.context_stability(), 3),
                "switches_per_min_30m": round(self.context_switch_rate(), 2),
            }


_hpc_instance: Optional[HierarchicalPredictiveCoding] = None


def get_hpc() -> HierarchicalPredictiveCoding:
    global _hpc_instance
    if _hpc_instance is None:
        _hpc_instance = HierarchicalPredictiveCoding()
    return _hpc_instance
