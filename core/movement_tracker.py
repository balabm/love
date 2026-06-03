"""
LOVE Movement Tracker — Body Intelligence (Modern AI Pattern)

Most movement is mindless or neglected. This tracker:

1. MOVEMENT TRACKING
   - Record movement sessions and their characteristics
   - Track movement types (walk, run, strength, flexibility, play)
   - Log energy, mood, and body feedback from movement

2. PATTERN ANALYSIS
   - Identify the user's movement style (consistency, intensity, variety)
   - Find movement types that boost energy and wellbeing
   - Detect movement gaps and sedentary patterns

3. PERSONALIZED GUIDANCE
   - Suggest movement matched to energy and mood
   - Provide micro-movement options for busy days
   - Recommend recovery movement after intense sessions

4. SUSTAINABILITY
   - Track adherence to movement intentions
   - Alert when sedentary time is excessive
   - Celebrate movement wins

Architecture:
- record_session(activity, type, duration, intensity): Log session
- get_movement_stats(): Get movement pattern analysis
- get_movement_suggestion(energy, mood, time): Get suggestion
- get_movement_score(): Calculate overall movement health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "movement_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MOVEMENT_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MovementSession:
    """A tracked movement session."""
    session_id: str = ""
    activity: str = ""
    movement_type: str = ""  # walk, run, strength, flexibility, play, sport, dance
    duration_minutes: float = 0.0
    intensity: float = 0.5  # 0-1
    energy_before: float = 0.5  # 0-1
    energy_after: float = 0.5  # 0-1
    mood_after: float = 0.5  # 0-1
    body_feedback: str = ""  # good, sore, tired, energized, pain
    social: bool = False  # done with others?
    outdoors: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MovementTracker:
    """
    Intelligent movement tracker with personalized guidance and sedentary detection.
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
            "avg_duration": 0.0,
            "avg_energy_change": 0.0,
            "dominant_type": "",
            "sedentary_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, activity: str = "", movement_type: str = "", duration: float = 0, intensity: float = 0.5, energy_before: float = 0.5, energy_after: float = 0.5, mood_after: float = 0.5, body_feedback: str = "", social: bool = False, outdoors: bool = False, notes: str = "") -> MovementSession:
        """Record a movement session."""
        session_id = f"move_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = MovementSession(
            session_id=session_id,
            activity=activity or "unspecified",
            movement_type=movement_type or "walk",
            duration_minutes=duration,
            intensity=intensity,
            energy_before=energy_before,
            energy_after=energy_after,
            mood_after=mood_after,
            body_feedback=body_feedback,
            social=social,
            outdoors=outdoors,
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

    def get_movement_stats(self) -> Dict[str, Any]:
        """Get movement pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "duration_sum": 0.0, "energy_change_sum": 0.0, "mood_sum": 0.0})
        for s in self._sessions:
            by_type[s.movement_type]["count"] += 1
            by_type[s.movement_type]["duration_sum"] += s.duration_minutes
            by_type[s.movement_type]["energy_change_sum"] += (s.energy_after - s.energy_before)
            by_type[s.movement_type]["mood_sum"] += s.mood_after

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_duration": round(data["duration_sum"] / count, 1),
                "avg_energy_change": round(data["energy_change_sum"] / count, 2),
                "avg_mood": round(data["mood_sum"] / count, 2),
            }

        dominant = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Intensity analysis
        low = [s for s in self._sessions if s.intensity <= 0.3]
        moderate = [s for s in self._sessions if 0.3 < s.intensity <= 0.7]
        high = [s for s in self._sessions if s.intensity > 0.7]

        intensity_stats = {}
        if low:
            intensity_stats["low"] = {"count": len(low), "avg_energy_change": round(sum(s.energy_after - s.energy_before for s in low) / len(low), 2)}
        if moderate:
            intensity_stats["moderate"] = {"count": len(moderate), "avg_energy_change": round(sum(s.energy_after - s.energy_before for s in moderate) / len(moderate), 2)}
        if high:
            intensity_stats["high"] = {"count": len(high), "avg_energy_change": round(sum(s.energy_after - s.energy_before for s in high) / len(high), 2)}

        # Social vs solo
        social = [s for s in self._sessions if s.social]
        solo = [s for s in self._sessions if not s.social]
        if social and solo:
            social_mood = sum(s.mood_after for s in social) / len(social)
            solo_mood = sum(s.mood_after for s in solo) / len(solo)
        else:
            social_mood = 0
            solo_mood = 0

        # Outdoors vs indoors
        outdoor = [s for s in self._sessions if s.outdoors]
        indoor = [s for s in self._sessions if not s.outdoors]
        if outdoor and indoor:
            outdoor_energy = sum(s.energy_after - s.energy_before for s in outdoor) / len(outdoor)
            indoor_energy = sum(s.energy_after - s.energy_before for s in indoor) / len(indoor)
        else:
            outdoor_energy = 0
            indoor_energy = 0

        # Sedentary detection
        recent_days = defaultdict(list)
        for s in self._sessions:
            day = s.timestamp[:10]
            recent_days[day].append(s)
        
        if recent_days:
            avg_daily_movement = sum(sum(s.duration_minutes for s in sessions) for sessions in recent_days.values()) / len(recent_days)
            sedentary_risk = avg_daily_movement < 20
        else:
            sedentary_risk = False

        # Body feedback analysis
        by_feedback = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for s in self._sessions:
            if s.body_feedback:
                by_feedback[s.body_feedback]["count"] += 1
                by_feedback[s.body_feedback]["intensity_sum"] += s.intensity

        feedback_stats = {}
        for fb, data in by_feedback.items():
            count = data["count"]
            if count >= 2:
                feedback_stats[fb] = {
                    "count": count,
                    "avg_intensity": round(data["intensity_sum"] / count, 2),
                }

        return {
            "total_sessions": len(self._sessions),
            "type_stats": type_stats,
            "dominant_type": dominant[0],
            "intensity_stats": intensity_stats,
            "social_vs_solo": {"social_mood": round(social_mood, 2), "solo_mood": round(solo_mood, 2)},
            "outdoor_vs_indoor": {"outdoor_energy_change": round(outdoor_energy, 2), "indoor_energy_change": round(indoor_energy, 2)},
            "sedentary_risk": sedentary_risk,
            "avg_daily_duration": round(sum(s.duration_minutes for s in self._sessions) / max(1, len(recent_days)), 1) if recent_days else 0,
            "feedback_stats": feedback_stats,
            "avg_energy_change": round(sum(s.energy_after - s.energy_before for s in self._sessions) / len(self._sessions), 2),
            "avg_mood": round(sum(s.mood_after for s in self._sessions) / len(self._sessions), 2),
        }

    def get_movement_suggestion(self, energy_level: float = 0.5, mood: float = 0.5, time_available: float = 15, preference: str = "") -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "low_energy": [
                "5-minute walk outside. Fresh air is more energizing than caffeine.",
                "Gentle stretching at your desk. Neck rolls, shoulder shrugs, spine twists.",
                "Dance to one song. Let the music move you.",
            ],
            "high_energy": [
                "Interval training: 30 seconds hard, 30 seconds rest. 10 rounds.",
                "Bodyweight circuit: squats, push-ups, lunges, planks. 3 rounds.",
                "Run or bike hard. Push your heart rate. You'll feel alive after.",
            ],
            "stressed": [
                "Yoga or tai chi. Move slowly and breathe deeply.",
                "Walk in nature. Let the environment lower your cortisol.",
                "Swim. The water will hold you while you move.",
            ],
            "tired": [
                "Gentle restorative yoga. Props, blankets, long holds.",
                "Slow walk with a friend. Talk while you move gently.",
                "Foam rolling or self-massage. Release tension.",
            ],
            "social": [
                "Join a class: dance, martial arts, group fitness.",
                "Play a sport with friends. Competition + connection.",
                "Walk and talk meeting. Movement + productivity + social.",
            ],
            "focus_needed": [
                "10 minutes of walking before deep work. It primes the brain.",
                "Balance exercises. They require presence.",
                "Rock climbing or bouldering. Full focus required.",
            ],
        }

        if energy_level < 0.3:
            key = "tired"
        elif energy_level < 0.6:
            key = "low_energy"
        elif mood < 0.4:
            key = "stressed"
        elif preference == "social":
            key = "social"
        else:
            key = "high_energy"

        selected = suggestions.get(key, suggestions["low_energy"])

        if time_available < 10:
            time_note = "Even 5 minutes counts. Movement begets movement."
        elif time_available < 30:
            time_note = "Short and effective. Intensity over duration."
        else:
            time_note = "Good time available. Warm up, work out, cool down."

        return {
            "energy_level": energy_level,
            "mood": mood,
            "time_available": time_available,
            "suggestion": random.choice(selected),
            "time_note": time_note,
            "reminder": "Your body is not a machine to be maintained. It's a partner to be listened to. Move it, rest it, nourish it.",
        }

    def get_movement_score(self) -> int:
        """Calculate overall movement health (0-100)."""
        if not self._sessions:
            return 25

        # Duration (150 minutes/week target = ~21 min/day)
        recent_days = defaultdict(list)
        for s in self._sessions:
            day = s.timestamp[:10]
            recent_days[day].append(s)
        if recent_days:
            avg_daily = sum(sum(s.duration_minutes for s in sessions) for sessions in recent_days.values()) / len(recent_days)
            duration_score = min(1, avg_daily / 30)
        else:
            duration_score = 0

        # Energy response
        avg_energy_change = sum(s.energy_after - s.energy_before for s in self._sessions) / len(self._sessions)

        # Mood
        avg_mood = sum(s.mood_after for s in self._sessions) / len(self._sessions)

        # Variety
        unique_types = len(set(s.movement_type for s in self._sessions))

        # Low pain
        pain_sessions = sum(1 for s in self._sessions if s.body_feedback == "pain")
        pain_rate = pain_sessions / len(self._sessions)

        # Recent trend
        recent = list(self._sessions)[-14:]
        if recent:
            recent_duration = sum(s.duration_minutes for s in recent) / len(recent)
            recent_mood = sum(s.mood_after for s in recent) / len(recent)
        else:
            recent_duration = 0
            recent_mood = 0

        # Consistency
        if recent_days:
            active_days = sum(1 for sessions in recent_days.values() if sum(s.duration_minutes for s in sessions) > 15)
            consistency = active_days / len(recent_days)
        else:
            consistency = 0

        score = (duration_score * 20) + (avg_energy_change * 15) + (avg_mood * 15) + (unique_types * 3) + ((1 - pain_rate) * 15) + (recent_duration / 60 * 10) + (recent_mood * 10) + (consistency * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_duration"] = round(sum(s.duration_minutes for s in self._sessions) / len(self._sessions), 1)
            self._stats["avg_energy_change"] = round(sum(s.energy_after - s.energy_before for s in self._sessions) / len(self._sessions), 2)

            by_type = defaultdict(lambda: {"count": 0, "duration": 0.0})
            for s in self._sessions:
                by_type[s.movement_type]["count"] += 1
                by_type[s.movement_type]["duration"] += s.duration_minutes
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1]["duration"])
                self._stats["dominant_type"] = dominant[0]

            recent_days = defaultdict(list)
            for s in self._sessions:
                day = s.timestamp[:10]
                recent_days[day].append(s)
            if recent_days:
                avg_daily = sum(sum(s.duration_minutes for s in sessions) for sessions in recent_days.values()) / len(recent_days)
                self._stats["sedentary_risk"] = avg_daily < 20

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.movement_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.movement_tracker")

    def _log_session(self, session: MovementSession):
        try:
            with open(MOVEMENT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "activity": session.activity,
                    "movement_type": session.movement_type,
                    "duration": session.duration_minutes,
                    "intensity": session.intensity,
                    "energy_before": session.energy_before,
                    "energy_after": session.energy_after,
                    "mood_after": session.mood_after,
                    "outdoors": session.outdoors,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.movement_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mt_instance: Optional[MovementTracker] = None
_mt_lock = threading.Lock()


def get_movement_tracker() -> MovementTracker:
    global _mt_instance
    with _mt_lock:
        if _mt_instance is None:
            _mt_instance = MovementTracker()
        return _mt_instance
