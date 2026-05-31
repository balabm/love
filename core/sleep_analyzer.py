"""
LOVE Sleep Quality Analyzer — Sleep Pattern Intelligence (Modern AI Pattern)

Sleep is the foundation of everything. This analyzer:

1. SLEEP METRICS
   - Track sleep duration, quality, latency, and interruptions
   - Detect sleep phases (deep, light, REM) from available data
   - Calculate sleep efficiency (time asleep / time in bed)

2. PATTERN DETECTION
   - Identify optimal bedtime and wake time
   - Detect sleep debt accumulation
   - Find correlations between sleep and next-day performance

3. QUALITY SCORING
   - Calculate overall sleep quality score (0-100)
   - Identify factors hurting sleep (late meals, screen time, stress)
   - Track sleep consistency (regular vs irregular schedule)

4. PROACTIVE RECOMMENDATIONS
   - Suggest bedtime based on tomorrow's schedule
   - Warn about sleep debt before it impacts performance
   - Recommend sleep hygiene improvements

Architecture:
- record_sleep(start, end, quality): Log a sleep session
- get_sleep_insights(days): Get sleep analysis
- get_sleep_score(): Get overall sleep quality score
- get_recommendations(): Get personalized sleep tips
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "sleep_analyzer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SLEEP_LOG = DATA_DIR / "sleep_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SleepSession:
    """A recorded sleep session."""
    start_time: str = ""
    end_time: str = ""
    duration_hours: float = 0.0
    quality: float = 0.5  # self-reported 0-1
    latency_minutes: float = 15.0  # time to fall asleep
    interruptions: int = 0
    factors: Dict[str, float] = field(default_factory=dict)  # caffeine, screen_time, stress
    deep_sleep_pct: float = 0.0
    rem_sleep_pct: float = 0.0


class SleepAnalyzer:
    """
    Analyze sleep patterns and provide recommendations.
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
        self._history: deque = deque(maxlen=200)
        self._stats = {
            "avg_duration": 7.5,
            "avg_quality": 0.7,
            "avg_score": 75,
            "best_bedtime": "22:30",
            "sleep_debt_hours": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_sleep(self, start: str, end: str, quality: float = 0.5, **kwargs) -> SleepSession:
        """Record a sleep session."""
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            duration = (end_dt - start_dt).total_seconds() / 3600
            if duration < 0:
                duration += 24  # Crossed midnight
        except Exception:
            duration = 7.5

        session = SleepSession(
            start_time=start,
            end_time=end,
            duration_hours=round(duration, 1),
            quality=quality,
            latency_minutes=kwargs.get("latency_minutes", 15),
            interruptions=kwargs.get("interruptions", 0),
            factors=kwargs.get("factors", {}),
            deep_sleep_pct=kwargs.get("deep_sleep_pct", 0.2),
            rem_sleep_pct=kwargs.get("rem_sleep_pct", 0.25),
        )

        with self._lock:
            self._history.append(session)
            self._update_stats(session)

        self._save_stats()
        self._log_sleep(session)

        return session

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_sleep_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get sleep analysis for recent days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in self._history if s.start_time > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        durations = [s.duration_hours for s in recent]
        qualities = [s.quality for s in recent]

        # Calculate sleep debt (difference from 8 hours)
        total_debt = sum(max(0, 8 - d) for d in durations)

        # Detect patterns
        bedtimes = []
        for s in recent:
            try:
                bt = datetime.fromisoformat(s.start_time)
                bedtimes.append(bt.hour + bt.minute / 60)
            except Exception:
                pass

        avg_bedtime = sum(bedtimes) / max(1, len(bedtimes)) if bedtimes else 22.5

        # Find worst factors
        factor_scores = defaultdict(float)
        factor_counts = defaultdict(int)
        for s in recent:
            for factor, value in s.factors.items():
                factor_scores[factor] += value
                factor_counts[factor] += 1

        avg_factors = {k: round(factor_scores[k] / max(1, factor_counts[k]), 2) for k in factor_scores}
        worst_factors = sorted(avg_factors.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "days_analyzed": len(recent),
            "avg_duration": round(sum(durations) / len(durations), 1),
            "avg_quality": round(sum(qualities) / len(qualities), 2),
            "sleep_debt_hours": round(total_debt, 1),
            "avg_bedtime": f"{int(avg_bedtime)}:{int((avg_bedtime % 1) * 60):02d}",
            "consistency": round(1 - (max(durations) - min(durations)) / max(1, sum(durations) / len(durations)), 2),
            "worst_factors": worst_factors,
            "interruption_avg": round(sum(s.interruptions for s in recent) / len(recent), 1),
        }

    def get_sleep_score(self) -> int:
        """Calculate overall sleep quality score (0-100)."""
        if not self._history:
            return 50

        recent = list(self._history)[-7:]
        durations = [s.duration_hours for s in recent]
        qualities = [s.quality for s in recent]

        # Duration score (ideal: 7-9 hours)
        avg_duration = sum(durations) / len(durations)
        duration_score = max(0, min(100, 100 - abs(avg_duration - 8) * 20))

        # Quality score
        avg_quality = sum(qualities) / len(qualities)
        quality_score = avg_quality * 100

        # Consistency score
        if len(durations) > 1:
            variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
            consistency_score = max(0, 100 - variance * 50)
        else:
            consistency_score = 70

        overall = round(duration_score * 0.4 + quality_score * 0.4 + consistency_score * 0.2)
        self._stats["avg_score"] = overall
        return overall

    def get_recommendations(self) -> List[str]:
        """Get personalized sleep recommendations."""
        recs = []
        insights = self.get_sleep_insights(7)

        if insights.get("avg_duration", 8) < 6.5:
            recs.append("Your sleep is too short. Aim for 7-9 hours.")
        if insights.get("avg_quality", 0.7) < 0.6:
            recs.append("Sleep quality is low. Review pre-sleep routine.")
        if insights.get("sleep_debt_hours", 0) > 3:
            recs.append(f"You have {insights['sleep_debt_hours']:.1f} hours of sleep debt. Catch up this weekend.")

        for factor, score in insights.get("worst_factors", []):
            if factor == "caffeine" and score > 0.5:
                recs.append("Reduce afternoon caffeine for better sleep.")
            elif factor == "screen_time" and score > 0.5:
                recs.append("Less screen time before bed. Try reading instead.")
            elif factor == "stress" and score > 0.5:
                recs.append("Evening relaxation ritual would help. Try meditation or warm bath.")

        if not recs:
            recs.append("Sleep looks good! Keep your current routine.")

        return recs[:5]

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, session: SleepSession):
        """Update running statistics."""
        n = len(self._history)
        prev_avg = self._stats.get("avg_duration", 7.5)
        self._stats["avg_duration"] = round((prev_avg * (n - 1) + session.duration_hours) / max(1, n), 1)

        prev_quality = self._stats.get("avg_quality", 0.7)
        self._stats["avg_quality"] = round((prev_quality * (n - 1) + session.quality) / max(1, n), 2)

        # Calculate sleep debt
        debt = max(0, 8 - session.duration_hours)
        self._stats["sleep_debt_hours"] = round(self._stats.get("sleep_debt_hours", 0) + debt, 1)

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

    def _log_sleep(self, session: SleepSession):
        try:
            with open(SLEEP_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.start_time,
                    "duration": session.duration_hours,
                    "quality": session.quality,
                    "interruptions": session.interruptions,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sa_instance: Optional[SleepAnalyzer] = None
_sa_lock = threading.Lock()


def get_sleep_analyzer() -> SleepAnalyzer:
    global _sa_instance
    with _sa_lock:
        if _sa_instance is None:
            _sa_instance = SleepAnalyzer()
        return _sa_instance
