"""
LOVE Energy Audit Tool — Personal Energy Intelligence (Modern AI Pattern)

Most productivity tools track time. This tool tracks ENERGY:

1. ENERGY LOGGING
   - Record energy level before/after activities
   - Track energy drains and energy sources
   - Identify energy patterns across the day/week

2. ACTIVITY IMPACT ANALYSIS
   - Calculate net energy gain/loss per activity type
   - Identify which activities recharge vs deplete
   - Find optimal activity sequences

3. ENERGY FORECASTING
   - Predict energy levels for upcoming time blocks
   - Suggest when to schedule high-energy vs low-energy tasks
   - Warn about upcoming energy crashes

4. RECOVERY OPTIMIZATION
   - Identify fastest recovery activities
   - Suggest micro-recoveries (2-5 minute recharges)
   - Track recovery effectiveness over time

Architecture:
- record_energy(activity, before, after): Log energy before/after activity
- get_energy_profile(): Get personal energy pattern analysis
- get_activity_impact(): Get net energy impact by activity type
- get_energy_forecast(): Predict energy for upcoming hours
- get_recovery_suggestion(): Suggest fastest recovery action
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "energy_audit"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENERGY_LOG = DATA_DIR / "energy_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EnergyRecord:
    """An energy before/after measurement."""
    activity: str = ""
    activity_type: str = ""  # work, social, exercise, creative, admin, rest
    before_energy: float = 0.5  # 0-1
    after_energy: float = 0.5
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context: str = ""  # morning, afternoon, evening, night
    notes: str = ""


class EnergyAuditTool:
    """
    Track personal energy patterns and optimize activity scheduling.
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
        self._records: deque = deque(maxlen=500)
        self._stats = {
            "total_records": 0,
            "avg_before": 0.5,
            "avg_after": 0.5,
            "avg_delta": 0.0,
            "best_activity": "",
            "worst_activity": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_energy(self, activity: str, before_energy: float, after_energy: float, activity_type: str = "", duration: float = 0.0, context: str = "", notes: str = "") -> EnergyRecord:
        """Record energy before/after an activity."""
        record = EnergyRecord(
            activity=activity,
            activity_type=activity_type or "work",
            before_energy=before_energy,
            after_energy=after_energy,
            duration_minutes=duration,
            context=context or self._get_time_context(),
            notes=notes,
        )

        with self._lock:
            self._records.append(record)
            self._stats["total_records"] += 1
            self._update_stats(record)

        self._save_stats()
        self._log_record(record)

        return record

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_energy_profile(self, days: int = 7) -> Dict[str, Any]:
        """Get personal energy pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [r for r in self._records if r.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Time-of-day energy levels
        by_time = defaultdict(list)
        for r in recent:
            by_time[r.context].append(r.before_energy)

        time_avg = {t: round(sum(v)/len(v), 2) for t, v in by_time.items()}

        # Energy trend
        sorted_records = sorted(recent, key=lambda r: r.timestamp)
        if len(sorted_records) > 5:
            first_half = sorted_records[:len(sorted_records)//2]
            second_half = sorted_records[len(sorted_records)//2:]
            first_avg = sum(r.before_energy for r in first_half) / len(first_half)
            second_avg = sum(r.before_energy for r in second_half) / len(second_half)
            trend = "improving" if second_avg > first_avg + 0.1 else "declining" if second_avg < first_avg - 0.1 else "stable"
        else:
            trend = "insufficient_data"

        # Recovery detection
        recoveries = [r for r in recent if r.after_energy > r.before_energy]
        avg_recovery = sum(r.after_energy - r.before_energy for r in recoveries) / max(1, len(recoveries))

        # Drain detection
        drains = [r for r in recent if r.after_energy < r.before_energy - 0.2]

        return {
            "days_analyzed": len(set(r.timestamp[:10] for r in recent)),
            "total_records": len(recent),
            "time_of_day_energy": time_avg,
            "energy_trend": trend,
            "avg_recovery_boost": round(avg_recovery, 2),
            "drain_episodes": len(drains),
            "avg_before": round(sum(r.before_energy for r in recent) / len(recent), 2),
            "avg_after": round(sum(r.after_energy for r in recent) / len(recent), 2),
        }

    def get_activity_impact(self) -> List[Dict[str, Any]]:
        """Get net energy impact by activity type."""
        by_type = defaultdict(lambda: {"count": 0, "before_sum": 0.0, "after_sum": 0.0, "deltas": []})

        for r in self._records:
            t = r.activity_type
            by_type[t]["count"] += 1
            by_type[t]["before_sum"] += r.before_energy
            by_type[t]["after_sum"] += r.after_energy
            by_type[t]["deltas"].append(r.after_energy - r.before_energy)

        results = []
        for activity_type, stats in by_type.items():
            count = stats["count"]
            avg_before = stats["before_sum"] / count
            avg_after = stats["after_sum"] / count
            avg_delta = sum(stats["deltas"]) / count
            results.append({
                "activity_type": activity_type,
                "count": count,
                "avg_before": round(avg_before, 2),
                "avg_after": round(avg_after, 2),
                "net_impact": round(avg_delta, 2),
                "impact_label": "recharging" if avg_delta > 0.1 else "draining" if avg_delta < -0.1 else "neutral",
            })

        return sorted(results, key=lambda x: x["net_impact"], reverse=True)

    def get_energy_forecast(self, hours_ahead: int = 4) -> List[Dict[str, Any]]:
        """Predict energy levels for upcoming hours."""
        if not self._records:
            return [{"hour": i, "predicted": 0.5, "confidence": "low"} for i in range(hours_ahead)]

        now = datetime.now()
        recent = list(self._records)[-20:]

        # Calculate average energy by hour of day from recent data
        hour_avg = defaultdict(list)
        for r in recent:
            try:
                hour = datetime.fromisoformat(r.timestamp).hour
                hour_avg[hour].append(r.before_energy)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.energy_audit_tool")

        forecasts = []
        for i in range(hours_ahead):
            future_hour = (now.hour + i) % 24
            if future_hour in hour_avg and len(hour_avg[future_hour]) > 2:
                avg = sum(hour_avg[future_hour]) / len(hour_avg[future_hour])
                confidence = "medium"
            else:
                avg = 0.5
                confidence = "low"

            # Apply trend decay if recent records show decline
            if i > 0:
                recent_deltas = [r.after_energy - r.before_energy for r in recent[-5:]]
                if recent_deltas:
                    avg_trend = sum(recent_deltas) / len(recent_deltas)
                    avg = max(0.1, min(0.9, avg + avg_trend * (i * 0.1)))

            forecasts.append({
                "hour": future_hour,
                "predicted": round(avg, 2),
                "confidence": confidence,
            })

        return forecasts

    def get_recovery_suggestion(self) -> Dict[str, Any]:
        """Suggest fastest recovery action based on data."""
        impacts = self.get_activity_impact()
        recharging = [i for i in impacts if i["impact_label"] == "recharging"]

        if recharging:
            best = recharging[0]
            return {
                "activity": best["activity_type"],
                "expected_boost": round(best["net_impact"], 2),
                "duration": "10-15 minutes",
                "reason": f"{best['activity_type'].title()} has the best energy recovery based on your data",
            }

        # Default suggestions if no data
        defaults = [
            {"activity": "short walk", "expected_boost": 0.2, "duration": "10 minutes"},
            {"activity": "deep breathing", "expected_boost": 0.15, "duration": "5 minutes"},
            {"activity": "hydration + stretch", "expected_boost": 0.1, "duration": "5 minutes"},
        ]
        return {
            **defaults[0],
            "reason": "General recovery recommendation (build more data for personalized suggestions)",
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _get_time_context(self) -> str:
        """Get time-of-day context."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _update_stats(self, record: EnergyRecord):
        """Update running statistics."""
        n = self._stats["total_records"]
        self._stats["avg_before"] = round((self._stats["avg_before"] * (n - 1) + record.before_energy) / n, 2)
        self._stats["avg_after"] = round((self._stats["avg_after"] * (n - 1) + record.after_energy) / n, 2)
        self._stats["avg_delta"] = round(self._stats["avg_after"] - self._stats["avg_before"], 2)

        # Update best/worst activity
        impacts = self.get_activity_impact()
        if impacts:
            self._stats["best_activity"] = impacts[0]["activity_type"]
            self._stats["worst_activity"] = impacts[-1]["activity_type"]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.energy_audit_tool")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.energy_audit_tool")

    def _log_record(self, record: EnergyRecord):
        try:
            with open(ENERGY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": record.timestamp,
                    "activity": record.activity,
                    "activity_type": record.activity_type,
                    "before": record.before_energy,
                    "after": record.after_energy,
                    "duration": record.duration_minutes,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.energy_audit_tool")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_eat_instance: Optional[EnergyAuditTool] = None
_eat_lock = threading.Lock()


def get_energy_audit_tool() -> EnergyAuditTool:
    global _eat_instance
    with _eat_lock:
        if _eat_instance is None:
            _eat_instance = EnergyAuditTool()
        return _eat_instance
