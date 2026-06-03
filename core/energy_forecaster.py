"""
LOVE Energy Forecasting Engine — Predictive Energy Modeling (Modern AI Pattern)

Energy levels fluctuate predictably. This forecaster:

1. ENERGY PATTERN LEARNING
   - Learn user's energy patterns from history (sleep, meals, work, exercise)
   - Identify peak energy windows and crash times
   - Detect energy drains (meetings, difficult tasks, social events)

2. PREDICTIVE MODELING
   - Forecast energy for upcoming hours based on patterns
   - Predict energy crash before it happens
   - Suggest optimal task scheduling based on energy forecast

3. REAL-TIME ADJUSTMENT
   - Adjust forecast based on actual energy reports
   - Detect anomalies (unexpected energy dips or boosts)
   - Update model with new data continuously

4. PROACTIVE RECOMMENDATIONS
   - Suggest high-energy tasks during peak windows
   - Recommend rest before predicted crashes
   - Alert when energy forecast conflicts with scheduled tasks

Architecture:
- forecast_energy(hours_ahead): Predict energy levels
- report_actual_energy(level): Update model with actual data
- get_energy_insights(): Get pattern analysis
- get_recommendations(tasks): Suggest task timing
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "energy_forecaster"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENERGY_LOG = DATA_DIR / "energy_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EnergySnapshot:
    """A snapshot of user's energy level."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    level: float = 0.5  # 0 = exhausted, 1 = peak
    factors: Dict[str, float] = field(default_factory=dict)  # sleep, meals, caffeine, stress
    activity: str = ""


@dataclass
class EnergyForecast:
    """A forecast of energy levels."""
    timestamp: str = ""
    predicted_level: float = 0.5
    confidence: float = 0.5
    factors: Dict[str, float] = field(default_factory=dict)
    recommendation: str = ""


class EnergyForecaster:
    """
    Forecast user energy levels and suggest optimal task timing.
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
        self._history: deque = deque(maxlen=500)
        self._hourly_patterns: Dict[int, List[float]] = defaultdict(list)
        self._stats = {
            "total_reports": 0,
            "avg_energy": 0.5,
            "peak_hour": 10,
            "crash_hour": 15,
            "forecast_accuracy": 0.0,
        }
        self._load_stats()

    # ── Core Forecasting ──────────────────────────────────────────────────

    def forecast_energy(self, hours_ahead: int = 4) -> List[EnergyForecast]:
        """Forecast energy levels for upcoming hours."""
        forecasts = []
        now = datetime.now()

        for h in range(1, hours_ahead + 1):
            forecast_time = now + timedelta(hours=h)
            hour = forecast_time.hour

            # Base prediction from hourly pattern
            pattern_values = self._hourly_patterns.get(hour, [0.5])
            base_level = sum(pattern_values) / max(1, len(pattern_values))

            # Adjust for time of day
            time_adjustment = self._time_of_day_factor(hour)
            adjusted_level = base_level * time_adjustment

            # Adjust for recent trend
            recent = [e.level for e in list(self._history)[-5:]]
            if recent:
                trend = (recent[-1] - recent[0]) / max(1, len(recent))
                adjusted_level += trend * h * 0.1

            # Clamp to valid range
            predicted = min(1.0, max(0.0, adjusted_level))

            # Confidence based on data availability
            confidence = min(0.9, 0.3 + len(pattern_values) * 0.05)

            # Generate recommendation
            recommendation = self._generate_recommendation(predicted, hour)

            forecasts.append(EnergyForecast(
                timestamp=forecast_time.isoformat(),
                predicted_level=round(predicted, 2),
                confidence=round(confidence, 2),
                factors={"time_of_day": round(time_adjustment, 2), "recent_trend": round(trend if recent else 0, 2)},
                recommendation=recommendation,
            ))

        return forecasts

    def report_actual_energy(self, level: float, factors: Optional[Dict[str, float]] = None, activity: str = ""):
        """Report actual energy level to improve forecasts."""
        snapshot = EnergySnapshot(
            level=level,
            factors=factors or {},
            activity=activity,
        )

        with self._lock:
            self._history.append(snapshot)
            self._stats["total_reports"] += 1

            # Update hourly pattern
            hour = datetime.now().hour
            self._hourly_patterns[hour].append(level)
            # Keep only last 30 values per hour
            if len(self._hourly_patterns[hour]) > 30:
                self._hourly_patterns[hour] = self._hourly_patterns[hour][-30:]

            # Update average
            prev_avg = self._stats.get("avg_energy", 0.5)
            n = self._stats["total_reports"]
            self._stats["avg_energy"] = round((prev_avg * (n - 1) + level) / max(1, n), 3)

        self._save_stats()
        self._log_energy(snapshot)

    # ── Insights ──────────────────────────────────────────────────────────

    def get_energy_insights(self) -> Dict[str, Any]:
        """Get energy pattern insights."""
        if not self._history:
            return {"status": "insufficient_data"}

        # Calculate average energy by hour
        hourly_avg = {}
        for hour, values in self._hourly_patterns.items():
            if values:
                hourly_avg[hour] = round(sum(values) / len(values), 2)

        # Find peak and crash hours
        if hourly_avg:
            peak_hour = max(hourly_avg, key=hourly_avg.get)
            crash_hour = min(hourly_avg, key=hourly_avg.get)
            self._stats["peak_hour"] = peak_hour
            self._stats["crash_hour"] = crash_hour

        # Detect drains and boosts
        drains = defaultdict(float)
        boosts = defaultdict(float)
        for i in range(1, len(self._history)):
            prev = self._history[i - 1]
            curr = self._history[i]
            change = curr.level - prev.level
            activity = curr.activity or "unknown"
            if change < -0.2:
                drains[activity] += abs(change)
            elif change > 0.2:
                boosts[activity] += change

        return {
            "hourly_avg": hourly_avg,
            "peak_hour": self._stats.get("peak_hour"),
            "crash_hour": self._stats.get("crash_hour"),
            "top_drains": sorted(drains.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_boosts": sorted(boosts.items(), key=lambda x: x[1], reverse=True)[:5],
            "avg_energy": self._stats.get("avg_energy"),
        }

    def get_recommendations(self, tasks: List[Dict[str, Any]] = []) -> List[Dict[str, Any]]:
        """Get task timing recommendations based on energy forecast."""
        forecast = self.forecast_energy(hours_ahead=8)
        recommendations = []

        for task in tasks:
            cognitive_load = task.get("cognitive_load", 0.5)
            best_slot = None
            best_score = -1

            for f in forecast:
                # High cognitive load needs high energy
                if cognitive_load > 0.6 and f.predicted_level > 0.7:
                    score = f.predicted_level * f.confidence
                # Medium load tolerates medium energy
                elif cognitive_load > 0.3 and f.predicted_level > 0.4:
                    score = f.predicted_level * f.confidence
                # Low load works anytime
                else:
                    score = f.confidence

                if score > best_score:
                    best_score = score
                    best_slot = f

            if best_slot:
                recommendations.append({
                    "task": task.get("title", ""),
                    "suggested_time": best_slot.timestamp,
                    "predicted_energy": best_slot.predicted_level,
                    "reason": best_slot.recommendation,
                })

        return recommendations

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _time_of_day_factor(self, hour: int) -> float:
        """Calculate time-of-day energy factor."""
        # Typical circadian rhythm
        if 6 <= hour < 10:
            return 0.7 + (hour - 6) * 0.1  # Rising
        elif 10 <= hour < 14:
            return 1.0  # Peak
        elif 14 <= hour < 17:
            return 0.8 - (hour - 14) * 0.1  # Declining
        elif 17 <= hour < 20:
            return 0.5  # Low
        else:
            return 0.3  # Very low

    def _generate_recommendation(self, predicted_level: float, hour: int) -> str:
        """Generate recommendation based on predicted energy."""
        if predicted_level > 0.8:
            return "Peak energy — tackle complex tasks"
        elif predicted_level > 0.6:
            return "Good energy — productive work"
        elif predicted_level > 0.4:
            return "Moderate energy — routine tasks"
        elif predicted_level > 0.2:
            return "Low energy — rest or light tasks"
        else:
            return "Very low — consider a break or nap"

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "hourly_patterns": {str(k): v[-10:] for k, v in self._hourly_patterns.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.energy_forecaster")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                patterns = data.get("hourly_patterns", {})
                for k, v in patterns.items():
                    self._hourly_patterns[int(k)] = v
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.energy_forecaster")

    def _log_energy(self, snapshot: EnergySnapshot):
        try:
            with open(ENERGY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": snapshot.timestamp,
                    "level": snapshot.level,
                    "activity": snapshot.activity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.energy_forecaster")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ef_instance: Optional[EnergyForecaster] = None
_ef_lock = threading.Lock()


def get_energy_forecaster() -> EnergyForecaster:
    global _ef_instance
    with _ef_lock:
        if _ef_instance is None:
            _ef_instance = EnergyForecaster()
        return _ef_instance
