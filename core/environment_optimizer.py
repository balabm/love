"""
LOVE Environment Optimizer — Space Intelligence (Modern AI Pattern)

Most people ignore their environment. This optimizer:

1. ENVIRONMENT TRACKING
   - Track workspace conditions (lighting, noise, temperature, clutter)
   - Log productivity correlation with environment state
   - Identify optimal environmental conditions

2. CONDITION ANALYSIS
   - Find correlations between environment and focus/energy/mood
   - Detect when environment is hurting performance
   - Track seasonal/cyclical environment effects

3. OPTIMIZATION SUGGESTIONS
   - Suggest lighting adjustments for time of day
   - Recommend temperature changes for focus
   - Propose decluttering when productivity drops

4. PROACTIVE ADJUSTMENTS
   - Alert when environment conditions are suboptimal
   - Suggest environment changes before work sessions
   - Track which changes actually improve performance

Architecture:
- record_conditions(lighting, noise, temp, clutter): Log environment state
- get_environment_insights(): Get environment-performance correlation
- get_optimization_suggestions(): Suggest environment improvements
- get_environment_score(): Calculate current environment quality
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "environment_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENV_LOG = DATA_DIR / "environment.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EnvironmentState:
    """A recorded environment state."""
    location: str = ""  # desk, couch, cafe, office, etc.
    lighting: float = 5.0  # 1-10 (dim to bright)
    noise_level: float = 5.0  # 1-10 (quiet to loud)
    temperature: float = 22.0  # celsius
    clutter: float = 5.0  # 1-10 (clean to cluttered)
    air_quality: float = 5.0  # 1-10 (poor to excellent)
    natural_light: bool = False
    focus_score: float = 0.5  # how well you focused here
    energy_score: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EnvironmentOptimizer:
    """
    Optimize physical environment for peak performance.
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
        self._states: deque = deque(maxlen=500)
        self._stats = {
            "total_records": 0,
            "avg_focus": 0.5,
            "avg_energy": 0.5,
            "optimal_temp": 22.0,
            "optimal_lighting": 7.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_conditions(self, location: str = "", lighting: float = 5.0, noise_level: float = 5.0, temperature: float = 22.0, clutter: float = 5.0, air_quality: float = 5.0, natural_light: bool = False, focus_score: float = 0.5, energy_score: float = 0.5, notes: str = "") -> EnvironmentState:
        """Record environment conditions and performance correlation."""
        state = EnvironmentState(
            location=location or "desk",
            lighting=lighting,
            noise_level=noise_level,
            temperature=temperature,
            clutter=clutter,
            air_quality=air_quality,
            natural_light=natural_light,
            focus_score=focus_score,
            energy_score=energy_score,
            notes=notes,
        )

        with self._lock:
            self._states.append(state)
            self._stats["total_records"] += 1
            self._update_stats(state)

        self._save_stats()
        self._log_state(state)

        return state

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_environment_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get environment-performance correlation."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in self._states if s.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Location analysis
        by_location = defaultdict(lambda: {"focus_scores": [], "energy_scores": [], "count": 0})
        for s in recent:
            loc = s.location
            by_location[loc]["focus_scores"].append(s.focus_score)
            by_location[loc]["energy_scores"].append(s.energy_score)
            by_location[loc]["count"] += 1

        location_stats = {}
        for loc, data in by_location.items():
            location_stats[loc] = {
                "count": data["count"],
                "avg_focus": round(sum(data["focus_scores"]) / len(data["focus_scores"]), 2),
                "avg_energy": round(sum(data["energy_scores"]) / len(data["energy_scores"]), 2),
            }

        # Correlation analysis
        # Find conditions that correlate with high focus
        high_focus = [s for s in recent if s.focus_score > 0.7]
        low_focus = [s for s in recent if s.focus_score < 0.4]

        insights = {}
        if high_focus and low_focus:
            insights["optimal_temperature"] = round(sum(s.temperature for s in high_focus) / len(high_focus), 1)
            insights["optimal_lighting"] = round(sum(s.lighting for s in high_focus) / len(high_focus), 1)
            insights["optimal_noise"] = round(sum(s.noise_level for s in high_focus) / len(high_focus), 1)
            insights["clutter_impact"] = "high" if sum(s.clutter for s in low_focus) / len(low_focus) > sum(s.clutter for s in high_focus) / len(high_focus) + 2 else "low"
            insights["natural_light_benefit"] = sum(1 for s in high_focus if s.natural_light) / len(high_focus) > 0.6

        return {
            "days_analyzed": len(set(s.timestamp[:10] for s in recent)),
            "total_records": len(recent),
            "location_stats": location_stats,
            "best_location": max(location_stats.items(), key=lambda x: x[1]["avg_focus"])[0] if location_stats else "",
            "condition_insights": insights,
            "avg_focus": round(sum(s.focus_score for s in recent) / len(recent), 2),
            "avg_energy": round(sum(s.energy_score for s in recent) / len(recent), 2),
        }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest environment improvements."""
        insights = self.get_environment_insights()
        suggestions = []

        if insights.get("status") == "insufficient_data":
            return [{"suggestion": "Record some environment conditions to get optimization suggestions.", "priority": "low"}]

        # Temperature suggestion
        current = [s for s in self._states if s.timestamp > (datetime.now() - timedelta(hours=2)).isoformat()]
        if current:
            avg_temp = sum(s.temperature for s in current) / len(current)
            optimal = insights.get("condition_insights", {}).get("optimal_temperature", 22)
            if abs(avg_temp - optimal) > 2:
                suggestions.append({
                    "area": "temperature",
                    "suggestion": f"Current temp is {avg_temp:.1f}°C. Your optimal focus temp is ~{optimal:.1f}°C.",
                    "action": f"Adjust thermostat to ~{optimal:.1f}°C" if avg_temp < optimal else f"Cool room to ~{optimal:.1f}°C",
                    "priority": "medium",
                })

        # Lighting suggestion
            avg_light = sum(s.lighting for s in current) / len(current)
            optimal_light = insights.get("condition_insights", {}).get("optimal_lighting", 7)
            if avg_light < optimal_light - 1:
                suggestions.append({
                    "area": "lighting",
                    "suggestion": f"Lighting is dim ({avg_light:.1f}/10). You focus best at ~{optimal_light:.1f}/10.",
                    "action": "Turn on more lights or move closer to a window.",
                    "priority": "high",
                })

        # Clutter suggestion
            avg_clutter = sum(s.clutter for s in current) / len(current)
            if avg_clutter > 6:
                suggestions.append({
                    "area": "clutter",
                    "suggestion": f"Space is cluttered ({avg_clutter:.1f}/10). Clutter competes for attention.",
                    "action": "Spend 5 minutes clearing your desk before deep work.",
                    "priority": "medium",
                })

        # Noise suggestion
            avg_noise = sum(s.noise_level for s in current) / len(current)
            if avg_noise > 6:
                suggestions.append({
                    "area": "noise",
                    "suggestion": f"Noise level is high ({avg_noise:.1f}/10). Consider noise-cancelling headphones.",
                    "action": "Put on noise-cancelling headphones or move to a quieter space.",
                    "priority": "high",
                })

        return suggestions

    def get_environment_score(self) -> int:
        """Calculate current environment quality score (0-100)."""
        recent = [s for s in self._states if s.timestamp > (datetime.now() - timedelta(hours=2)).isoformat()]
        
        if not recent:
            return 50

        # Average the key metrics
        avg_focus = sum(s.focus_score for s in recent) / len(recent)
        avg_energy = sum(s.energy_score for s in recent) / len(recent)
        avg_lighting = sum(s.lighting for s in recent) / len(recent) / 10
        avg_clutter = 1 - (sum(s.clutter for s in recent) / len(recent) / 10)  # inverted
        avg_noise = 1 - (sum(s.noise_level for s in recent) / len(recent) / 10)  # inverted

        overall = round(avg_focus * 30 + avg_energy * 20 + avg_lighting * 15 + avg_clutter * 15 + avg_noise * 20)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, state: EnvironmentState):
        """Update running statistics."""
        n = self._stats["total_records"]
        self._stats["avg_focus"] = round((self._stats["avg_focus"] * (n - 1) + state.focus_score) / n, 2)
        self._stats["avg_energy"] = round((self._stats["avg_energy"] * (n - 1) + state.energy_score) / n, 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception:
            pass

    def _log_state(self, state: EnvironmentState):
        try:
            with open(ENV_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": state.timestamp,
                    "location": state.location,
                    "lighting": state.lighting,
                    "noise": state.noise_level,
                    "temp": state.temperature,
                    "clutter": state.clutter,
                    "focus": state.focus_score,
                    "energy": state.energy_score,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_eo_instance: Optional[EnvironmentOptimizer] = None
_eo_lock = threading.Lock()


def get_environment_optimizer() -> EnvironmentOptimizer:
    global _eo_instance
    with _eo_lock:
        if _eo_instance is None:
            _eo_instance = EnvironmentOptimizer()
        return _eo_instance
