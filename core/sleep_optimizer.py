"""
LOVE Sleep Optimizer — Rest Intelligence (Modern AI Pattern)

Most people neglect sleep, the foundation of everything. This optimizer:

1. SLEEP TRACKING
   - Record sleep sessions and their quality metrics
   - Track sleep hygiene factors and their effects
   - Log sleep disruptions and their causes

2. PATTERN ANALYSIS
   - Identify the user's sleep chronotype and optimal schedule
   - Find sleep inhibitors (caffeine, screens, stress, food)
   - Detect sleep debt accumulation

3. SLEEP OPTIMIZATION
   - Suggest bedtime routines matched to chronotype
   - Provide environment optimization recommendations
   - Recommend nap strategies and caffeine timing

4. SLEEP DEBT MANAGEMENT
   - Track sleep debt and suggest recovery
   - Alert when sleep is compromising performance
   - Celebrate consistent sleep wins

Architecture:
- record_sleep_session(duration, quality, factors, disruptions): Log session
- get_sleep_stats(): Get sleep pattern analysis
- get_sleep_recommendation(current_debt, chronotype): Get recommendation
- get_sleep_score(): Calculate overall sleep health
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
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "sleep_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SLEEP_LOG = DATA_DIR / "sleep.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SleepSession:
    """A tracked sleep session."""
    session_id: str = ""
    duration_hours: float = 0.0
    quality: float = 0.5  # 0-1
    latency_minutes: float = 0.0  # time to fall asleep
    awakenings: int = 0
    deep_sleep_pct: float = 0.0
    rem_sleep_pct: float = 0.0
    bedtime: str = ""
    wake_time: str = ""
    caffeine_after_2pm: bool = False
    screen_time_before_bed: float = 0.0  # minutes
    alcohol: bool = False
    exercise_within_3h: bool = False
    stress_level: float = 0.5
    room_temp: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SleepOptimizer:
    """
    Intelligent sleep optimizer with chronotype analysis and debt tracking.
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
        self._sessions: deque = deque(maxlen=200)
        self._stats = {
            "total_sessions": 0,
            "avg_quality": 0.0,
            "avg_duration": 0.0,
            "sleep_debt_hours": 0.0,
            "chronotype_estimate": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_sleep_session(self, duration: float = 0.0, quality: float = 0.5, latency: float = 0.0, awakenings: int = 0, deep_pct: float = 0.0, rem_pct: float = 0.0, bedtime: str = "", wake_time: str = "", caffeine_after_2pm: bool = False, screen_time: float = 0.0, alcohol: bool = False, exercise_within_3h: bool = False, stress: float = 0.5, room_temp: float = 0.0, notes: str = "") -> SleepSession:
        """Record a sleep session."""
        session_id = f"sleep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = SleepSession(
            session_id=session_id,
            duration_hours=duration,
            quality=quality,
            latency_minutes=latency,
            awakenings=awakenings,
            deep_sleep_pct=deep_pct,
            rem_sleep_pct=rem_pct,
            bedtime=bedtime,
            wake_time=wake_time,
            caffeine_after_2pm=caffeine_after_2pm,
            screen_time_before_bed=screen_time,
            alcohol=alcohol,
            exercise_within_3h=exercise_within_3h,
            stress_level=stress,
            room_temp=room_temp,
            notes=notes,
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_session(session)

        return session

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_sleep_stats(self) -> Dict[str, Any]:
        """Get sleep pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Factor analysis
        caffeine_sessions = [s for s in self._sessions if s.caffeine_after_2pm]
        no_caffeine = [s for s in self._sessions if not s.caffeine_after_2pm]
        caffeine_effect = (sum(s.quality for s in caffeine_sessions) / max(1, len(caffeine_sessions))) - (sum(s.quality for s in no_caffeine) / max(1, len(no_caffeine))) if caffeine_sessions and no_caffeine else 0

        screen_sessions = [s for s in self._sessions if s.screen_time_before_bed > 30]
        no_screen = [s for s in self._sessions if s.screen_time_before_bed <= 30]
        screen_effect = (sum(s.quality for s in screen_sessions) / max(1, len(screen_sessions))) - (sum(s.quality for s in no_screen) / max(1, len(no_screen))) if screen_sessions and no_screen else 0

        alcohol_sessions = [s for s in self._sessions if s.alcohol]
        no_alcohol = [s for s in self._sessions if not s.alcohol]
        alcohol_effect = (sum(s.quality for s in alcohol_sessions) / max(1, len(alcohol_sessions))) - (sum(s.quality for s in no_alcohol) / max(1, len(no_alcohol))) if alcohol_sessions and no_alcohol else 0

        # Bedtime analysis
        bedtimes = []
        for s in self._sessions:
            if s.bedtime:
                try:
                    hour = int(s.bedtime.split(":")[0])
                    bedtimes.append(hour)
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.sleep_optimizer")

        if bedtimes:
            avg_bedtime = sum(bedtimes) / len(bedtimes)
            chronotype = "night_owl" if avg_bedtime >= 23 else "morning_lark" if avg_bedtime <= 22 else "intermediate"
        else:
            chronotype = "unknown"

        # Duration analysis
        short = [s for s in self._sessions if s.duration_hours < 6]
        optimal = [s for s in self._sessions if 7 <= s.duration_hours <= 9]
        long_sleep = [s for s in self._sessions if s.duration_hours > 9]

        duration_stats = {}
        if short:
            duration_stats["short"] = {"count": len(short), "avg_quality": round(sum(s.quality for s in short) / len(short), 2)}
        if optimal:
            duration_stats["optimal"] = {"count": len(optimal), "avg_quality": round(sum(s.quality for s in optimal) / len(optimal), 2)}
        if long_sleep:
            duration_stats["long"] = {"count": len(long_sleep), "avg_quality": round(sum(s.quality for s in long_sleep) / len(long_sleep), 2)}

        # Sleep debt (7.5 hours as baseline)
        total_debt = sum(max(0, 7.5 - s.duration_hours) for s in self._sessions)

        # Recent trend
        recent = list(self._sessions)[-7:]
        if recent:
            recent_quality = sum(s.quality for s in recent) / len(recent)
            recent_duration = sum(s.duration_hours for s in recent) / len(recent)
        else:
            recent_quality = 0
            recent_duration = 0

        older = list(self._sessions)[:-7] if len(self._sessions) > 7 else []
        if older:
            older_quality = sum(s.quality for s in older) / len(older)
            quality_trend = recent_quality - older_quality
        else:
            quality_trend = 0

        return {
            "total_sessions": len(self._sessions),
            "avg_duration": round(sum(s.duration_hours for s in self._sessions) / len(self._sessions), 1),
            "avg_quality": round(sum(s.quality for s in self._sessions) / len(self._sessions), 2),
            "avg_latency": round(sum(s.latency_minutes for s in self._sessions) / len(self._sessions), 1),
            "avg_awakenings": round(sum(s.awakenings for s in self._sessions) / len(self._sessions), 1),
            "chronotype_estimate": chronotype,
            "caffeine_effect": round(caffeine_effect, 2),
            "screen_effect": round(screen_effect, 2),
            "alcohol_effect": round(alcohol_effect, 2),
            "duration_stats": duration_stats,
            "sleep_debt_hours": round(total_debt, 1),
            "quality_trend": round(quality_trend, 2),
            "recent_avg_duration": round(recent_duration, 1),
        }

    def get_sleep_recommendation(self, current_debt: float = 0.0, chronotype: str = "") -> Dict[str, Any]:
        """Get recommendation."""
        if current_debt > 5:
            urgency = "critical"
            message = "Severe sleep debt. Prioritize sleep above all else. Cancel non-essentials. Sleep 9+ hours tonight."
        elif current_debt > 2:
            urgency = "high"
            message = "Moderate sleep debt. Add 30-60 minutes to tonight's sleep. Take a 20-minute nap if possible."
        elif current_debt > 0:
            urgency = "moderate"
            message = "Small sleep debt. Maintain 7.5-8 hours tonight. You'll recover in a day or two."
        else:
            urgency = "low"
            message = "No sleep debt. Maintain your schedule. Consistency is more important than perfection."

        bedtime_routines = {
            "night_owl": [
                "Gradually shift bedtime earlier by 15 minutes every 2 days",
                "Use dim red lights after 9pm. Avoid blue light completely.",
                "Do gentle stretching or reading (paper book) before bed",
                "Keep room cool (65-68F) and dark",
            ],
            "morning_lark": [
                "Maintain consistent early bedtime. Don't stay up late on weekends.",
                "Use blackout curtains to maintain early sleep schedule",
                "Avoid caffeine after noon",
                "Exercise in morning, not evening",
            ],
            "intermediate": [
                "Choose a consistent bedtime and stick to it",
                "Create a 30-minute wind-down routine",
                "Limit screens 1 hour before bed",
                "Keep room dark, cool, and quiet",
            ],
        }

        routine = bedtime_routines.get(chronotype, bedtime_routines["intermediate"])

        return {
            "current_debt": current_debt,
            "chronotype": chronotype or "unknown",
            "urgency": urgency,
            "message": message,
            "routine": random.sample(routine, min(2, len(routine))),
            "caffeine_rule": "No caffeine after 2pm. It has a half-life of 5-6 hours.",
            "screen_rule": "No screens 1 hour before bed. The blue light suppresses melatonin.",
            "principle": "Sleep is not a luxury. It's the foundation of cognition, emotion, and health. Protect it like your life depends on it. Because it does.",
        }

    def get_sleep_score(self) -> int:
        """Calculate overall sleep health (0-100)."""
        if not self._sessions:
            return 30

        # Duration (optimal 7-9 hours)
        avg_duration = sum(s.duration_hours for s in self._sessions) / len(self._sessions)
        duration_score = max(0, 1 - abs(avg_duration - 7.5) / 3)

        # Quality
        avg_quality = sum(s.quality for s in self._sessions) / len(self._sessions)

        # Low latency
        avg_latency = sum(s.latency_minutes for s in self._sessions) / len(self._sessions)
        latency_score = max(0, 1 - avg_latency / 60)

        # Low awakenings
        avg_awakenings = sum(s.awakenings for s in self._sessions) / len(self._sessions)
        awakening_score = max(0, 1 - avg_awakenings / 5)

        # Recent trend
        recent = list(self._sessions)[-7:]
        if recent:
            recent_quality = sum(s.quality for s in recent) / len(recent)
        else:
            recent_quality = 0

        # Sleep debt
        total_debt = sum(max(0, 7.5 - s.duration_hours) for s in self._sessions)
        debt_penalty = min(20, total_debt * 2)

        score = (duration_score * 20) + (avg_quality * 25) + (latency_score * 10) + (awakening_score * 10) + (recent_quality * 15) - debt_penalty + 20
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_quality"] = round(sum(s.quality for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_duration"] = round(sum(s.duration_hours for s in self._sessions) / len(self._sessions), 1)
            self._stats["sleep_debt_hours"] = round(sum(max(0, 7.5 - s.duration_hours) for s in self._sessions), 1)

            bedtimes = []
            for s in self._sessions:
                if s.bedtime:
                    try:
                        hour = int(s.bedtime.split(":")[0])
                        bedtimes.append(hour)
                    except Exception as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.sleep_optimizer")
            if bedtimes:
                avg_bedtime = sum(bedtimes) / len(bedtimes)
                if avg_bedtime >= 23:
                    self._stats["chronotype_estimate"] = "night_owl"
                elif avg_bedtime <= 22:
                    self._stats["chronotype_estimate"] = "morning_lark"
                else:
                    self._stats["chronotype_estimate"] = "intermediate"

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sleep_optimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sleep_optimizer")

    def _log_session(self, session: SleepSession):
        try:
            with open(SLEEP_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "duration": session.duration_hours,
                    "quality": session.quality,
                    "latency": session.latency_minutes,
                    "awakenings": session.awakenings,
                    "bedtime": session.bedtime,
                    "caffeine": session.caffeine_after_2pm,
                    "screen_time": session.screen_time_before_bed,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sleep_optimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_so_instance: Optional[SleepOptimizer] = None
_so_lock = threading.Lock()


def get_sleep_optimizer() -> SleepOptimizer:
    global _so_instance
    with _so_lock:
        if _so_instance is None:
            _so_instance = SleepOptimizer()
        return _so_instance
