"""
LOVE Digital Minimalism Coach — Intentional Tech Intelligence (Modern AI Pattern)

Most digital use is compulsive, not intentional. This coach:

1. DIGITAL USE TRACKING
   - Record digital sessions and their characteristics
   - Track app/website categories and time spent
   - Log mood and energy before and after digital use

2. PATTERN ANALYSIS
   - Identify the user's digital use profile (consumer, creator, connector, escapist)
   - Find high-value vs low-value digital activities
   - Detect compulsive patterns (doomscrolling, notification checking, context switching)

3. INTENTIONAL DESIGN
   - Suggest digital minimalism practices
   - Provide app/website blocking strategies
   - Recommend digital Sabbath and offline rituals

4. RECLAIMING ATTENTION
   - Track attention quality over time
   - Alert when digital use is compromising focus
   - Celebrate intentional digital choices

Architecture:
- record_session(app, category, duration, value): Log session
- get_digital_stats(): Get digital use pattern analysis
- get_minimalism_practice(profile, goal): Get practice
- get_digital_score(): Calculate overall digital health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "digital_minimalism_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DIGITAL_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class DigitalSession:
    """A tracked digital session."""
    session_id: str = ""
    app_or_site: str = ""
    category: str = ""  # social_media, news, entertainment, work, communication, learning, shopping
    duration_minutes: float = 0.0
    value_score: float = 0.5  # 0-1, how valuable was this
    intentionality: float = 0.5  # 0-1, how intentional was this
    energy_before: float = 0.5  # 0-1
    energy_after: float = 0.5  # 0-1
    mood_after: float = 0.5  # 0-1
    compulsive: bool = False  # did you open it without thinking?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DigitalMinimalismCoach:
    """
    Intelligent digital minimalism coach with intentionality tracking and compulsive pattern detection.
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
        self._sessions: deque = deque(maxlen=300)
        self._stats = {
            "total_sessions": 0,
            "avg_value": 0.0,
            "avg_intentionality": 0.0,
            "compulsive_rate": 0.0,
            "problematic_app": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, app_or_site: str = "", category: str = "", duration: float = 0, value_score: float = 0.5, intentionality: float = 0.5, energy_before: float = 0.5, energy_after: float = 0.5, mood_after: float = 0.5, compulsive: bool = False, notes: str = "") -> DigitalSession:
        """Record a digital session."""
        session_id = f"dig_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = DigitalSession(
            session_id=session_id,
            app_or_site=app_or_site or "unspecified",
            category=category or "general",
            duration_minutes=duration,
            value_score=value_score,
            intentionality=intentionality,
            energy_before=energy_before,
            energy_after=energy_after,
            mood_after=mood_after,
            compulsive=compulsive,
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

    def get_digital_stats(self) -> Dict[str, Any]:
        """Get digital use pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "duration_sum": 0.0, "value_sum": 0.0, "intentionality_sum": 0.0, "compulsive_count": 0})
        for s in self._sessions:
            by_category[s.category]["count"] += 1
            by_category[s.category]["duration_sum"] += s.duration_minutes
            by_category[s.category]["value_sum"] += s.value_score
            by_category[s.category]["intentionality_sum"] += s.intentionality
            if s.compulsive:
                by_category[s.category]["compulsive_count"] += 1

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            category_stats[c] = {
                "count": count,
                "total_duration": round(data["duration_sum"], 1),
                "avg_value": round(data["value_sum"] / count, 2),
                "avg_intentionality": round(data["intentionality_sum"] / count, 2),
                "compulsive_rate": round(data["compulsive_count"] / count, 2),
            }

        # App/site analysis
        by_app = defaultdict(lambda: {"count": 0, "duration_sum": 0.0, "value_sum": 0.0, "compulsive_count": 0})
        for s in self._sessions:
            by_app[s.app_or_site]["count"] += 1
            by_app[s.app_or_site]["duration_sum"] += s.duration_minutes
            by_app[s.app_or_site]["value_sum"] += s.value_score
            if s.compulsive:
                by_app[s.app_or_site]["compulsive_count"] += 1

        app_stats = {}
        for a, data in by_app.items():
            count = data["count"]
            if count >= 2:
                app_stats[a] = {
                    "count": count,
                    "total_duration": round(data["duration_sum"], 1),
                    "avg_value": round(data["value_sum"] / count, 2),
                    "compulsive_rate": round(data["compulsive_count"] / count, 2),
                }

        problematic_app = min(app_stats.items(), key=lambda x: x[1]["avg_value"]) if app_stats else ("", {})

        # Time of day analysis
        by_hour = defaultdict(lambda: {"count": 0, "duration_sum": 0.0, "value_sum": 0.0})
        for s in self._sessions:
            hour = s.timestamp[11:13] if len(s.timestamp) > 13 else "00"
            by_hour[hour]["count"] += 1
            by_hour[hour]["duration_sum"] += s.duration_minutes
            by_hour[hour]["value_sum"] += s.value_score

        hour_stats = {}
        for h, data in by_hour.items():
            count = data["count"]
            if count >= 2:
                hour_stats[h] = {
                    "count": count,
                    "total_duration": round(data["duration_sum"], 1),
                    "avg_value": round(data["value_sum"] / count, 2),
                }

        # Energy/mood impact
        avg_energy_change = sum(s.energy_after - s.energy_before for s in self._sessions) / len(self._sessions)
        avg_mood_after = sum(s.mood_after for s in self._sessions) / len(self._sessions)

        # Compulsive rate
        compulsive_count = sum(1 for s in self._sessions if s.compulsive)
        compulsive_rate = compulsive_count / len(self._sessions)

        # Total daily duration
        daily_durations = defaultdict(float)
        for s in self._sessions:
            day = s.timestamp[:10]
            daily_durations[day] += s.duration_minutes
        avg_daily_duration = sum(daily_durations.values()) / len(daily_durations) if daily_durations else 0

        return {
            "total_sessions": len(self._sessions),
            "category_stats": category_stats,
            "app_stats": app_stats,
            "problematic_app": problematic_app[0],
            "hour_stats": hour_stats,
            "avg_value": round(sum(s.value_score for s in self._sessions) / len(self._sessions), 2),
            "avg_intentionality": round(sum(s.intentionality for s in self._sessions) / len(self._sessions), 2),
            "avg_energy_change": round(avg_energy_change, 2),
            "avg_mood_after": round(avg_mood_after, 2),
            "compulsive_rate": round(compulsive_rate, 2),
            "avg_daily_duration": round(avg_daily_duration, 1),
        }

    def get_minimalism_practice(self, profile: str = "", goal: str = "") -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "reduce_compulsive": [
                "Remove all apps from your phone's home screen. Make opening them a deliberate choice.",
                "Turn off all non-essential notifications. You check your phone enough without prompts.",
                "Use grayscale mode. Color is designed to grab attention. Remove the bait.",
            ],
            "increase_intentional": [
                "Before opening any app, ask: 'What am I here for?' Set a timer for 10 minutes.",
                "Batch your digital tasks. Check email 3x/day, not 30x.",
                "Use one screen at a time. No split-screen multitasking.",
            ],
            "digital_sabbath": [
                "Take one full day off from all non-essential digital tools. Read, walk, cook, talk.",
                "No phones at meals. Not face-down. In another room.",
                "Create a 'no phone zone' in your home. A room where screens don't exist.",
            ],
            "reclaim_attention": [
                "Practice the 20-second rule: Make bad habits 20 seconds harder to start.",
                "Use website blockers during focus hours. Freedom or Cold Turkey.",
                "Set a 'digital sunset' 1 hour before bed. No screens. Period.",
            ],
            "deepen_value": [
                "For every hour of consumption, spend 30 minutes creating.",
                "Curate your feeds ruthlessly. Unfollow anything that doesn't educate or inspire.",
                "Use social media only to connect with specific people, not to browse.",
            ],
        }

        selected = practices.get(goal, practices["reduce_compulsive"])

        if profile == "consumer":
            profile_note = "You consume more than you create. Shift the ratio. Create first, consume second."
        elif profile == "escapist":
            profile_note = "You use digital tools to avoid discomfort. The discomfort won't go away. Face it directly."
        elif profile == "connector":
            profile_note = "You use digital tools for connection. Deepen the quality, not the quantity."
        elif profile == "creator":
            profile_note = "You create digitally. Protect your creative time. Don't let consumption steal it."
        else:
            profile_note = "Your digital use is mixed. Start with awareness. Track every session for one day."

        return {
            "profile": profile or "mixed",
            "goal": goal or "general",
            "practice": random.choice(selected),
            "profile_note": profile_note,
            "principle": "Technology is a tool. It should serve your goals, not hijack your attention. Use it intentionally, or it will use you.",
        }

    def get_digital_score(self) -> int:
        """Calculate overall digital health (0-100)."""
        if not self._sessions:
            return 35

        # Value and intentionality
        avg_value = sum(s.value_score for s in self._sessions) / len(self._sessions)
        avg_intentionality = sum(s.intentionality for s in self._sessions) / len(self._sessions)

        # Low compulsive rate
        compulsive_count = sum(1 for s in self._sessions if s.compulsive)
        compulsive_rate = compulsive_count / len(self._sessions)

        # Energy/mood impact
        avg_energy_change = sum(s.energy_after - s.energy_before for s in self._sessions) / len(self._sessions)
        avg_mood = sum(s.mood_after for s in self._sessions) / len(self._sessions)

        # Recent trend
        recent = list(self._sessions)[-14:]
        if recent:
            recent_value = sum(s.value_score for s in recent) / len(recent)
            recent_intentionality = sum(s.intentionality for s in recent) / len(recent)
        else:
            recent_value = 0
            recent_intentionality = 0

        # Duration control
        daily_durations = defaultdict(float)
        for s in self._sessions:
            day = s.timestamp[:10]
            daily_durations[day] += s.duration_minutes
        if daily_durations:
            avg_daily = sum(daily_durations.values()) / len(daily_durations)
            duration_penalty = min(15, max(0, (avg_daily - 120) / 60 * 5))
        else:
            duration_penalty = 0

        score = (avg_value * 25) + (avg_intentionality * 20) + ((1 - compulsive_rate) * 15) + (avg_energy_change * 10) + (avg_mood * 10) + (recent_value * 10) + (recent_intentionality * 5) - duration_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_value"] = round(sum(s.value_score for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_intentionality"] = round(sum(s.intentionality for s in self._sessions) / len(self._sessions), 2)

            compulsive_count = sum(1 for s in self._sessions if s.compulsive)
            self._stats["compulsive_rate"] = round(compulsive_count / len(self._sessions), 2)

            by_app = defaultdict(lambda: {"value": 0.0, "count": 0, "compulsive": 0})
            for s in self._sessions:
                by_app[s.app_or_site]["value"] += s.value_score
                by_app[s.app_or_site]["count"] += 1
                if s.compulsive:
                    by_app[s.app_or_site]["compulsive"] += 1
            if by_app:
                problematic = min(by_app.items(), key=lambda x: x[1]["value"] / max(1, x[1]["count"]))
                self._stats["problematic_app"] = problematic[0]

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

    def _log_session(self, session: DigitalSession):
        try:
            with open(DIGITAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "app": session.app_or_site,
                    "category": session.category,
                    "duration": session.duration_minutes,
                    "value": session.value_score,
                    "intentionality": session.intentionality,
                    "compulsive": session.compulsive,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dmc_instance: Optional[DigitalMinimalismCoach] = None
_dmc_lock = threading.Lock()


def get_digital_minimalism_coach() -> DigitalMinimalismCoach:
    global _dmc_instance
    with _dmc_lock:
        if _dmc_instance is None:
            _dmc_instance = DigitalMinimalismCoach()
        return _dmc_instance
