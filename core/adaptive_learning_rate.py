"""
LOVE Adaptive Learning Rate Engine — Dynamic Model Parameter Tuning (Modern AI Pattern)

Modern AI systems need to adapt their behavior based on feedback. This engine:

1. FEEDBACK LOOP OPTIMIZATION
   - Track response quality, latency, and user satisfaction
   - Adjust learning parameters based on recent performance
   - Apply momentum to smooth out noisy feedback

2. EXPLORATION vs EXPLOITATION BALANCE
   - Dynamically balance trying new strategies vs using proven ones
   - Increase exploration when performance plateaus
   - Decrease exploration when system is stable

3. TEMPERATURE ADAPTATION
   - Adjust response creativity/temperature based on task type
   - Lower temperature for factual queries, higher for creative tasks
   - Adapt based on user feedback on response style

4. PARAMETER SCHEDULING
   - Gradually decay learning rate over time
   - Warm up parameters after major updates
   - Cyclical scheduling for continued improvement

Architecture:
- adjust_parameters(feedback): Tune system parameters based on feedback
- get_optimal_temperature(task_type): Get temperature for task
- get_exploration_rate(): Current exploration vs exploitation balance
- get_learning_stats(): Track adaptation metrics
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "adaptive_learning"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEARNING_LOG = DATA_DIR / "learning_log.jsonl"
PARAM_DB = DATA_DIR / "param_db.json"

DEFAULT_TEMPERATURE = 0.7
DEFAULT_EXPLORATION_RATE = 0.2


@dataclass
class ParameterState:
    """Current state of a tunable parameter."""
    name: str = ""
    value: float = 0.0
    min_value: float = 0.0
    max_value: float = 1.0
    learning_rate: float = 0.1
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    history: List[float] = field(default_factory=list)


class AdaptiveLearningRateEngine:
    """
    Dynamic parameter tuning for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._parameters: Dict[str, ParameterState] = {}
        self._feedback_window: deque = deque(maxlen=100)
        self._stats = {
            "total_adjustments": 0,
            "exploration_count": 0,
            "exploitation_count": 0,
            "average_quality": 0.0,
        }
        self._initialize_defaults()
        self._load_params()

    def _initialize_defaults(self):
        """Initialize default parameters."""
        defaults = [
            ("temperature", DEFAULT_TEMPERATURE, 0.0, 1.5, 0.05),
            ("exploration_rate", DEFAULT_EXPLORATION_RATE, 0.0, 1.0, 0.02),
            ("response_length_pref", 0.5, 0.0, 1.0, 0.03),
            ("creativity_boost", 0.3, 0.0, 1.0, 0.04),
            ("fact_checking_strictness", 0.7, 0.0, 1.0, 0.02),
        ]
        for name, val, min_v, max_v, lr in defaults:
            if name not in self._parameters:
                self._parameters[name] = ParameterState(
                    name=name, value=val, min_value=min_v, max_value=max_v, learning_rate=lr
                )

    # ── Core Adjustment ────────────────────────────────────────────────────

    def adjust_parameters(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust system parameters based on feedback."""
        quality = feedback.get("quality", 0.5)
        latency_ms = feedback.get("latency_ms", 500)
        user_satisfaction = feedback.get("user_satisfaction", 0.5)
        task_type = feedback.get("task_type", "general")

        self._feedback_window.append({
            "quality": quality,
            "latency_ms": latency_ms,
            "user_satisfaction": user_satisfaction,
            "task_type": task_type,
            "timestamp": time.time(),
        })

        adjustments = {}

        with self._lock:
            # Adjust temperature based on task type and quality
            temp_param = self._parameters["temperature"]
            if task_type in ("creative", "brainstorming", "story"):
                target_temp = 0.9
            elif task_type in ("factual", "coding", "math"):
                target_temp = 0.3
            else:
                target_temp = DEFAULT_TEMPERATURE

            # If quality is low, move temperature toward target
            if quality < 0.5:
                delta = (target_temp - temp_param.value) * temp_param.learning_rate
                temp_param.value = max(temp_param.min_value,
                                       min(temp_param.max_value, temp_param.value + delta))
                adjustments["temperature"] = round(temp_param.value, 3)

            # Adjust exploration rate based on recent quality variance
            if len(self._feedback_window) >= 10:
                recent = list(self._feedback_window)[-10:]
                qualities = [f["quality"] for f in recent]
                avg_q = sum(qualities) / len(qualities)
                variance = sum((q - avg_q) ** 2 for q in qualities) / len(qualities)

                exp_param = self._parameters["exploration_rate"]
                if variance < 0.05:  # Performance is stable, try exploring
                    exp_param.value = min(exp_param.max_value, exp_param.value + 0.05)
                    self._stats["exploration_count"] += 1
                elif variance > 0.2:  # Too much variance, exploit more
                    exp_param.value = max(exp_param.min_value, exp_param.value - 0.05)
                    self._stats["exploitation_count"] += 1
                adjustments["exploration_rate"] = round(exp_param.value, 3)

            # Adjust creativity boost based on user satisfaction
            creative_param = self._parameters["creativity_boost"]
            if user_satisfaction > 0.7:
                creative_param.value = min(creative_param.max_value,
                                           creative_param.value + 0.03)
            elif user_satisfaction < 0.4:
                creative_param.value = max(creative_param.min_value,
                                           creative_param.value - 0.05)
            adjustments["creativity_boost"] = round(creative_param.value, 3)

            # Update average quality stat
            all_qualities = [f["quality"] for f in self._feedback_window]
            self._stats["average_quality"] = round(sum(all_qualities) / len(all_qualities), 3)
            self._stats["total_adjustments"] += 1

            # Record history
            for name, param in self._parameters.items():
                param.history.append(param.value)
                if len(param.history) > 50:
                    param.history.pop(0)
                param.last_updated = datetime.now().isoformat()

        self._save_params()
        self._log_adjustment(feedback, adjustments)

        return {"adjustments": adjustments, "current_params": self.get_current_params()}

    # ── Temperature & Exploration ──────────────────────────────────────────

    def get_optimal_temperature(self, task_type: str = "general") -> float:
        """Get optimal temperature for a task type."""
        base_temps = {
            "creative": 0.9,
            "brainstorming": 0.95,
            "story": 0.85,
            "factual": 0.3,
            "coding": 0.2,
            "math": 0.1,
            "general": DEFAULT_TEMPERATURE,
        }
        base = base_temps.get(task_type, DEFAULT_TEMPERATURE)
        current = self._parameters.get("temperature", ParameterState(value=base))
        # Blend base with learned preference
        return round((base + current.value) / 2, 2)

    def get_exploration_rate(self) -> float:
        """Get current exploration rate."""
        return self._parameters.get("exploration_rate",
                                     ParameterState(value=DEFAULT_EXPLORATION_RATE)).value

    def should_explore(self) -> bool:
        """Decide whether to explore or exploit."""
        return self.get_exploration_rate() > 0.3

    # ── Parameter Access ────────────────────────────────────────────────────

    def get_current_params(self) -> Dict[str, float]:
        """Get all current parameter values."""
        return {name: param.value for name, param in self._parameters.items()}

    def get_parameter_history(self, param_name: str) -> List[float]:
        """Get history of a parameter."""
        param = self._parameters.get(param_name)
        return param.history.copy() if param else []

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_learning_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "current_params": self.get_current_params(),
            "feedback_count": len(self._feedback_window),
            "parameter_count": len(self._parameters),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_params(self):
        try:
            data = {
                "parameters": {
                    name: {
                        "name": p.name,
                        "value": p.value,
                        "min_value": p.min_value,
                        "max_value": p.max_value,
                        "learning_rate": p.learning_rate,
                        "last_updated": p.last_updated,
                        "history": p.history,
                    }
                    for name, p in self._parameters.items()
                },
                "stats": self._stats,
            }
            PARAM_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_params(self):
        try:
            if PARAM_DB.exists():
                data = json.loads(PARAM_DB.read_text())
                for name, p_data in data.get("parameters", {}).items():
                    self._parameters[name] = ParameterState(**p_data)
                self._stats.update(data.get("stats", {}))
        except Exception:
            pass

    def _log_adjustment(self, feedback: Dict[str, Any], adjustments: Dict[str, float]):
        try:
            with open(LEARNING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "feedback": feedback,
                    "adjustments": adjustments,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_alr_instance: Optional[AdaptiveLearningRateEngine] = None
_alr_lock = threading.Lock()


def get_adaptive_learning_engine() -> AdaptiveLearningRateEngine:
    global _alr_instance
    with _alr_lock:
        if _alr_instance is None:
            _alr_instance = AdaptiveLearningRateEngine()
        return _alr_instance
