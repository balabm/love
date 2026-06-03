"""
LOVE Meditation Coach — Mindfulness Intelligence (Modern AI Pattern)

Most meditation apps are passive timers. This coach:

1. SESSION TRACKING
   - Record meditation duration, type, and quality
   - Track heart rate and breathing patterns if available
   - Log pre/post mood and stress levels

2. PROGRESS ANALYSIS
   - Calculate consistency streaks and total practice time
   - Identify most effective meditation types for the user
   - Detect patterns in meditation quality (time of day, duration, etc.)

3. PERSONALIZED GUIDANCE
   - Suggest meditation type based on current state (stressed, tired, anxious)
   - Recommend session length based on experience level
   - Adapt difficulty based on progress

4. PROACTIVE NUDGES
   - Suggest meditation when stress patterns are detected
   - Recommend recovery meditation after intense work
   - Celebrate milestones and consistency

Architecture:
- record_session(duration, type, quality): Log meditation session
- get_progress_stats(): Get practice statistics
- get_recommendation(context): Get personalized meditation suggestion
- get_mindfulness_score(): Get overall mindfulness score
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

DATA_DIR = Path(__file__).parent.parent / "data" / "meditation_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MeditationSession:
    """A recorded meditation session."""
    duration_minutes: float = 0.0
    meditation_type: str = ""  # mindfulness, breathing, body_scan, loving_kindness, focused_attention, open_monitoring
    quality: float = 0.5  # 0-1 (distracted to deeply focused)
    stress_before: float = 0.5  # 0-1
    stress_after: float = 0.5
    mood_before: str = ""
    mood_after: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""
    interruptions: int = 0


class MeditationCoach:
    """
    Personal meditation coach with adaptive guidance.
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
        self._sessions: deque = deque(maxlen=500)
        self._stats = {
            "total_sessions": 0,
            "total_minutes": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "avg_session_length": 0.0,
            "avg_quality": 0.5,
            "mindfulness_score": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, duration: float, meditation_type: str = "mindfulness", quality: float = 0.5, stress_before: float = 0.5, stress_after: float = 0.5, mood_before: str = "", mood_after: str = "", notes: str = "", interruptions: int = 0) -> MeditationSession:
        """Record a meditation session."""
        session = MeditationSession(
            duration_minutes=duration,
            meditation_type=meditation_type,
            quality=quality,
            stress_before=stress_before,
            stress_after=stress_after,
            mood_before=mood_before,
            mood_after=mood_after,
            notes=notes,
            interruptions=interruptions,
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._stats["total_minutes"] += duration
            self._update_streak(session)
            self._update_stats(session)

        self._save_stats()
        self._log_session(session)

        # Check milestones
        self._check_milestones()

        return session

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_progress_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get practice statistics."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in self._sessions if s.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Type effectiveness
        by_type = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "stress_reduction": 0.0})
        for s in recent:
            t = s.meditation_type
            by_type[t]["count"] += 1
            by_type[t]["quality_sum"] += s.quality
            by_type[t]["stress_reduction"] += max(0, s.stress_before - s.stress_after)

        type_stats = {}
        for t, stats in by_type.items():
            type_stats[t] = {
                "count": stats["count"],
                "avg_quality": round(stats["quality_sum"] / stats["count"], 2),
                "avg_stress_reduction": round(stats["stress_reduction"] / stats["count"], 2),
            }

        # Find best type for stress reduction
        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_stress_reduction"]) if type_stats else ("", {})

        # Time of day analysis
        by_hour = defaultdict(list)
        for s in recent:
            try:
                hour = datetime.fromisoformat(s.timestamp).hour
                by_hour[hour].append(s.quality)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.meditation_coach")

        best_hour = max(by_hour.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if by_hour else None

        return {
            "days_analyzed": len(set(s.timestamp[:10] for s in recent)),
            "total_sessions": len(recent),
            "total_minutes": round(sum(s.duration_minutes for s in recent), 1),
            "avg_duration": round(sum(s.duration_minutes for s in recent) / len(recent), 1),
            "avg_quality": round(sum(s.quality for s in recent) / len(recent), 2),
            "avg_stress_reduction": round(sum(max(0, s.stress_before - s.stress_after) for s in recent) / len(recent), 2),
            "current_streak": self._stats["current_streak"],
            "longest_streak": self._stats["longest_streak"],
            "type_effectiveness": type_stats,
            "best_type_for_stress": best_type[0] if best_type else "",
            "best_hour": f"{best_hour}:00" if best_hour is not None else "",
        }

    def get_recommendation(self, context: str = "", current_stress: float = 0.5) -> Dict[str, Any]:
        """Get personalized meditation suggestion."""
        # Determine session type based on context
        if current_stress > 0.7 or "stress" in context.lower() or "anxious" in context.lower():
            meditation_type = "breathing"
            duration = 5
            reason = "Breathing meditation is excellent for acute stress relief."
        elif current_stress > 0.4 or "tired" in context.lower() or "exhausted" in context.lower():
            meditation_type = "body_scan"
            duration = 10
            reason = "Body scan helps release physical tension when you're tired."
        elif "focus" in context.lower() or "distracted" in context.lower():
            meditation_type = "focused_attention"
            duration = 10
            reason = "Focused attention meditation trains concentration."
        elif "happy" in context.lower() or "grateful" in context.lower():
            meditation_type = "loving_kindness"
            duration = 10
            reason = "Loving-kindness amplifies positive emotions."
        else:
            meditation_type = "mindfulness"
            duration = 10
            reason = "General mindfulness practice for overall wellbeing."

        # Adjust duration based on experience
        if self._stats["total_sessions"] > 20:
            duration = min(30, duration + 5)
            reason += " You're experienced enough for a longer session."
        elif self._stats["total_sessions"] < 5:
            duration = 5
            reason = "Start with 5 minutes to build the habit." + reason

        return {
            "meditation_type": meditation_type,
            "duration_minutes": duration,
            "reason": reason,
            "guidance": self._get_guidance(meditation_type),
        }

    def get_mindfulness_score(self) -> int:
        """Calculate overall mindfulness score (0-100)."""
        if not self._sessions:
            return 0

        recent = list(self._sessions)[-30:]
        n = len(recent)

        # Consistency score (sessions per week)
        weeks = max(1, len(set(s.timestamp[:10] for s in recent)) / 7)
        sessions_per_week = n / weeks
        consistency_score = min(100, sessions_per_week * 25)  # 4+ sessions/week = 100

        # Quality score
        avg_quality = sum(s.quality for s in recent) / n
        quality_score = avg_quality * 100

        # Stress management score
        stress_improved = sum(1 for s in recent if s.stress_after < s.stress_before)
        stress_score = (stress_improved / n) * 100

        # Streak bonus
        streak_bonus = min(20, self._stats["current_streak"] * 2)

        overall = round(consistency_score * 0.3 + quality_score * 0.3 + stress_score * 0.2 + streak_bonus)
        self._stats["mindfulness_score"] = min(100, overall)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_streak(self, session: MeditationSession):
        """Update meditation streak."""
        today = datetime.now().date()
        try:
            session_date = datetime.fromisoformat(session.timestamp).date()
        except Exception:
            session_date = today

        if self._sessions and len(self._sessions) > 1:
            try:
                last_session = list(self._sessions)[-2]
                last_date = datetime.fromisoformat(last_session.timestamp).date()
                if (session_date - last_date).days == 1:
                    self._stats["current_streak"] += 1
                elif (session_date - last_date).days > 1:
                    self._stats["current_streak"] = 1
            except Exception:
                self._stats["current_streak"] = 1
        else:
            self._stats["current_streak"] = 1

        self._stats["longest_streak"] = max(self._stats["longest_streak"], self._stats["current_streak"])

    def _update_stats(self, session: MeditationSession):
        """Update running statistics."""
        n = self._stats["total_sessions"]
        self._stats["avg_session_length"] = round((self._stats["avg_session_length"] * (n - 1) + session.duration_minutes) / n, 1)
        self._stats["avg_quality"] = round((self._stats["avg_quality"] * (n - 1) + session.quality) / n, 2)

    def _get_guidance(self, meditation_type: str) -> str:
        """Get brief guidance for meditation type."""
        guidance = {
            "mindfulness": "Sit comfortably, close your eyes, and observe your breath. When your mind wanders, gently return to the breath.",
            "breathing": "Breathe in for 4 counts, hold for 4, exhale for 4, hold for 4. Repeat. Focus entirely on the breath.",
            "body_scan": "Starting from your toes, slowly move your attention up through each part of your body. Notice sensations without judgment.",
            "loving_kindness": "Silently repeat: 'May I be happy. May I be healthy. May I be at peace.' Then extend this to loved ones, then all beings.",
            "focused_attention": "Choose an object (breath, sound, candle). When attention wanders, notice it and return to the chosen object.",
            "open_monitoring": "Rest in open awareness. Notice whatever arises in experience without focusing on any particular object.",
        }
        return guidance.get(meditation_type, "Focus on your breath and return when the mind wanders.")

    def _check_milestones(self):
        """Check and celebrate meditation milestones."""
        milestones = {
            1: "First session! The journey of a thousand miles begins with a single step.",
            7: "One week! You're building a powerful habit.",
            30: "30 sessions! Mindfulness is becoming part of your life.",
            100: "100 sessions! You have cultivated serious mental fitness.",
        }

        if self._stats["total_sessions"] in milestones:
            try:
                from core.neural_bus import get_neural_bus
                get_neural_bus().publish(
                    event_type="meditation_milestone",
                    domain="wellness",
                    payload={
                        "sessions": self._stats["total_sessions"],
                        "message": milestones[self._stats["total_sessions"]],
                    },
                )
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.meditation_coach")

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meditation_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meditation_coach")

    def _log_session(self, session: MeditationSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "duration": session.duration_minutes,
                    "type": session.meditation_type,
                    "quality": session.quality,
                    "stress_before": session.stress_before,
                    "stress_after": session.stress_after,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meditation_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mc_instance: Optional[MeditationCoach] = None
_mc_lock = threading.Lock()


def get_meditation_coach() -> MeditationCoach:
    global _mc_instance
    with _mc_lock:
        if _mc_instance is None:
            _mc_instance = MeditationCoach()
        return _mc_instance
