"""
LOVE Peak Performance Tracker — Excellence Intelligence (Modern AI Pattern)

Most performance tracking focuses on output, not conditions. This tracker:

1. PERFORMANCE TRACKING
   - Record peak performance episodes and their conditions
   - Track performance metrics (output, quality, flow, energy)
   - Log pre-performance routines and their effectiveness

2. PATTERN ANALYSIS
   - Identify the user's performance profile (morning, night, sprint, endurance)
   - Find performance predictors (sleep, nutrition, stress, preparation)
   - Detect performance inhibitors and their accumulation

3. CONDITION OPTIMIZATION
   - Suggest pre-performance routines based on past peaks
   - Provide environment and state recommendations
   - Recommend recovery-after-performance protocols

4. PROGRESSIVE OVERLOAD
   - Track performance trends over time
   - Alert when performance is plateauing or declining
   - Celebrate performance breakthroughs

Architecture:
- record_performance(task, metrics, conditions, routines): Log performance
- get_performance_stats(): Get performance pattern analysis
- get_peak_conditions(goal, timeframe): Get conditions
- get_performance_score(): Calculate overall performance health
"""

import json
import math
import random
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "peak_performance_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PERFORMANCE_LOG = DATA_DIR / "performances.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PerformanceEntry:
    """A tracked performance entry."""
    entry_id: str = ""
    task: str = ""
    output_score: float = 0.5  # 0-1
    quality_score: float = 0.5  # 0-1
    flow_score: float = 0.0  # 0-1
    energy_level: float = 0.5  # 0-1
    sleep_hours: float = 0.0
    stress_level: float = 0.5  # 0-1
    preparation_minutes: float = 0.0
    recovery_minutes: float = 0.0
    time_of_day: str = ""
    environment: str = ""  # office, home, cafe, outdoors, etc.
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PeakPerformanceTracker:
    """
    Intelligent peak performance tracker with condition analysis and progressive overload.
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
        self._entries: deque = deque(maxlen=200)
        self._stats = {
            "total_entries": 0,
            "avg_output": 0.0,
            "avg_quality": 0.0,
            "peak_time": "",
            "peak_environment": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_performance(self, task: str = "", output_score: float = 0.5, quality_score: float = 0.5, flow_score: float = 0.0, energy_level: float = 0.5, sleep_hours: float = 0.0, stress_level: float = 0.5, preparation: float = 0.0, recovery: float = 0.0, time_of_day: str = "", environment: str = "", notes: str = "") -> PerformanceEntry:
        """Record a performance entry."""
        entry_id = f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PerformanceEntry(
            entry_id=entry_id,
            task=task or "unspecified",
            output_score=output_score,
            quality_score=quality_score,
            flow_score=flow_score,
            energy_level=energy_level,
            sleep_hours=sleep_hours,
            stress_level=stress_level,
            preparation_minutes=preparation,
            recovery_minutes=recovery,
            time_of_day=time_of_day or datetime.now().strftime("%H:%M"),
            environment=environment or "general",
            notes=notes,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_stats()

        self._save_stats()
        self._log_entry(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Time of day analysis
        by_hour = defaultdict(lambda: {"count": 0, "output_sum": 0.0, "quality_sum": 0.0, "flow_sum": 0.0})
        for e in self._entries:
            hour = e.time_of_day[:2] if e.time_of_day else "00"
            by_hour[hour]["count"] += 1
            by_hour[hour]["output_sum"] += e.output_score
            by_hour[hour]["quality_sum"] += e.quality_score
            by_hour[hour]["flow_sum"] += e.flow_score

        hour_stats = {}
        for h, data in by_hour.items():
            count = data["count"]
            if count >= 2:
                hour_stats[h] = {
                    "count": count,
                    "avg_output": round(data["output_sum"] / count, 2),
                    "avg_quality": round(data["quality_sum"] / count, 2),
                    "avg_flow": round(data["flow_sum"] / count, 2),
                }

        peak_time = max(hour_stats.items(), key=lambda x: x[1]["avg_output"] + x[1]["avg_quality"]) if hour_stats else ("", {})

        # Environment analysis
        by_env = defaultdict(lambda: {"count": 0, "output_sum": 0.0, "quality_sum": 0.0})
        for e in self._entries:
            by_env[e.environment]["count"] += 1
            by_env[e.environment]["output_sum"] += e.output_score
            by_env[e.environment]["quality_sum"] += e.quality_score

        env_stats = {}
        for env, data in by_env.items():
            count = data["count"]
            if count >= 2:
                env_stats[env] = {
                    "count": count,
                    "avg_output": round(data["output_sum"] / count, 2),
                    "avg_quality": round(data["quality_sum"] / count, 2),
                }

        peak_env = max(env_stats.items(), key=lambda x: x[1]["avg_output"] + x[1]["avg_quality"]) if env_stats else ("", {})

        # Condition correlations
        high_performers = [e for e in self._entries if e.output_score > 0.7 and e.quality_score > 0.7]
        if high_performers:
            avg_sleep = sum(e.sleep_hours for e in high_performers) / len(high_performers)
            avg_stress = sum(e.stress_level for e in high_performers) / len(high_performers)
            avg_prep = sum(e.preparation_minutes for e in high_performers) / len(high_performers)
            avg_energy = sum(e.energy_level for e in high_performers) / len(high_performers)
        else:
            avg_sleep = 0
            avg_stress = 0
            avg_prep = 0
            avg_energy = 0

        # Trend analysis
        recent = list(self._entries)[-10:]
        if recent:
            recent_avg = sum(e.output_score + e.quality_score for e in recent) / (len(recent) * 2)
        else:
            recent_avg = 0
        older = list(self._entries)[:-10] if len(self._entries) > 10 else []
        if older:
            older_avg = sum(e.output_score + e.quality_score for e in older) / (len(older) * 2)
            trend = recent_avg - older_avg
        else:
            trend = 0

        # Plateau detection
        if len(self._entries) >= 20:
            first_half = list(self._entries)[:len(self._entries)//2]
            second_half = list(self._entries)[len(self._entries)//2:]
            first_avg = sum(e.output_score for e in first_half) / len(first_half)
            second_avg = sum(e.output_score for e in second_half) / len(second_half)
            plateau = abs(second_avg - first_avg) < 0.1
        else:
            plateau = False

        return {
            "total_entries": len(self._entries),
            "hour_stats": hour_stats,
            "peak_time": peak_time[0],
            "env_stats": env_stats,
            "peak_environment": peak_env[0],
            "peak_conditions": {
                "avg_sleep": round(avg_sleep, 1),
                "avg_stress": round(avg_stress, 2),
                "avg_prep": round(avg_prep, 1),
                "avg_energy": round(avg_energy, 2),
            },
            "avg_output": round(sum(e.output_score for e in self._entries) / len(self._entries), 2),
            "avg_quality": round(sum(e.quality_score for e in self._entries) / len(self._entries), 2),
            "avg_flow": round(sum(e.flow_score for e in self._entries) / len(self._entries), 2),
            "trend": round(trend, 2),
            "plateau": plateau,
        }

    def get_peak_conditions(self, goal: str = "", timeframe: str = "tomorrow") -> Dict[str, Any]:
        """Get conditions."""
        high_performers = [e for e in self._entries if e.output_score > 0.7 and e.quality_score > 0.7]
        
        if high_performers:
            peak_hour = max(set(e.time_of_day[:2] for e in high_performers), key=lambda h: sum(1 for e in high_performers if e.time_of_day[:2] == h))
            peak_env = max(set(e.environment for e in high_performers), key=lambda env: sum(1 for e in high_performers if e.environment == env))
            avg_sleep = sum(e.sleep_hours for e in high_performers) / len(high_performers)
            avg_prep = sum(e.preparation_minutes for e in high_performers) / len(high_performers)
        else:
            peak_hour = "09"
            peak_env = "office"
            avg_sleep = 7.5
            avg_prep = 15

        return {
            "goal": goal or "general",
            "timeframe": timeframe,
            "optimal_time": f"{peak_hour}:00" if peak_hour else "morning",
            "optimal_environment": peak_env,
            "target_sleep": round(avg_sleep, 1),
            "target_prep": round(avg_prep, 1),
            "routine": [
                f"Sleep {avg_sleep:.1f} hours the night before",
                f"Spend {avg_prep:.0f} minutes in preparation",
                "Minimize decisions before peak work",
                "Remove all distractions from environment",
                "Start exactly at your peak time. Don't wait for motivation.",
            ],
            "reminder": "Peak performance is not random. It's the result of optimized conditions. Create the conditions, performance follows.",
        }

    def get_performance_score(self) -> int:
        """Calculate overall performance health (0-100)."""
        if not self._entries:
            return 35

        # Output and quality
        avg_output = sum(e.output_score for e in self._entries) / len(self._entries)
        avg_quality = sum(e.quality_score for e in self._entries) / len(self._entries)

        # Flow
        avg_flow = sum(e.flow_score for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-10:]
        recent_avg = sum(e.output_score + e.quality_score for e in recent) / (len(recent) * 2)
        older = list(self._entries)[:-10] if len(self._entries) > 10 else []
        if older:
            older_avg = sum(e.output_score + e.quality_score for e in older) / (len(older) * 2)
            trend = recent_avg - older_avg
        else:
            trend = 0

        # Condition awareness
        high_perf = [e for e in self._entries if e.output_score > 0.7]
        if high_perf:
            condition_score = sum(e.energy_level + (1 - e.stress_level) for e in high_perf) / (len(high_perf) * 2)
        else:
            condition_score = 0

        # Variety (different environments, times)
        unique_envs = len(set(e.environment for e in self._entries))
        unique_hours = len(set(e.time_of_day[:2] for e in self._entries if e.time_of_day))

        score = (avg_output * 20) + (avg_quality * 20) + (avg_flow * 15) + (trend * 15) + (condition_score * 15) + (unique_envs * 2) + (unique_hours * 1)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_output"] = round(sum(e.output_score for e in self._entries) / len(self._entries), 2)
            self._stats["avg_quality"] = round(sum(e.quality_score for e in self._entries) / len(self._entries), 2)

            by_hour = defaultdict(lambda: {"output": 0.0, "quality": 0.0, "count": 0})
            for e in self._entries:
                hour = e.time_of_day[:2] if e.time_of_day else "00"
                by_hour[hour]["output"] += e.output_score
                by_hour[hour]["quality"] += e.quality_score
                by_hour[hour]["count"] += 1
            if by_hour:
                peak = max(by_hour.items(), key=lambda x: (x[1]["output"] + x[1]["quality"]) / max(1, x[1]["count"]))
                self._stats["peak_time"] = peak[0]

            by_env = defaultdict(lambda: {"output": 0.0, "quality": 0.0, "count": 0})
            for e in self._entries:
                by_env[e.environment]["output"] += e.output_score
                by_env[e.environment]["quality"] += e.quality_score
                by_env[e.environment]["count"] += 1
            if by_env:
                peak_env = max(by_env.items(), key=lambda x: (x[1]["output"] + x[1]["quality"]) / max(1, x[1]["count"]))
                self._stats["peak_environment"] = peak_env[0]

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

    def _log_entry(self, entry: PerformanceEntry):
        try:
            with open(PERFORMANCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "task": entry.task,
                    "output": entry.output_score,
                    "quality": entry.quality_score,
                    "flow": entry.flow_score,
                    "energy": entry.energy_level,
                    "sleep": entry.sleep_hours,
                    "stress": entry.stress_level,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ppt_instance: Optional[PeakPerformanceTracker] = None
_ppt_lock = threading.Lock()


def get_peak_performance_tracker() -> PeakPerformanceTracker:
    global _ppt_instance
    with _ppt_lock:
        if _ppt_instance is None:
            _ppt_instance = PeakPerformanceTracker()
        return _ppt_instance
