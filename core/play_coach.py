"""
LOVE Play Coach — Joy Intelligence (Modern AI Pattern)

Most adults forget how to play. This coach:

1. PLAY TRACKING
   - Record play activities and their joy impact
   - Track spontaneous vs planned play
   - Log which types of play feel nourishing vs draining

2. PATTERN ANALYSIS
   - Identify the user's play style (competitive, creative, physical, social, imaginative)
   - Find play droughts and their causes
   - Detect the gap between desired and actual play time

3. PLAY GENERATION
   - Suggest play activities based on energy, time, and mood
   - Provide micro-play (2-minute joy injections)
   - Recommend play companions and solo play options

4. GROWTH SUPPORT
   - Track play as essential, not optional
   - Suggest play experiments outside comfort zone
   - Celebrate playfulness milestones

Architecture:
- record_play(activity, type, duration, joy_level): Log play
- get_play_stats(): Get play pattern analysis
- get_play_suggestion(energy, time, mood): Get play idea
- get_playfulness_score(): Calculate overall play health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "play_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PLAY_LOG = DATA_DIR / "play.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PlaySession:
    """A tracked play session."""
    session_id: str = ""
    activity: str = ""
    play_type: str = ""  # competitive, creative, physical, social, imaginative, exploratory
    duration_minutes: float = 0.0
    joy_level: float = 0.5  # 0-1
    energy_required: str = ""  # low, medium, high
    planned: bool = False
    solo: bool = True
    location: str = ""  # home, outdoors, venue, online
    companions: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PlayCoach:
    """
    Intelligent play coach with play style analysis and joy optimization.
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
            "avg_joy": 0.0,
            "planned_rate": 0.0,
            "solo_rate": 0.0,
            "dominant_type": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_play(self, activity: str = "", play_type: str = "", duration: float = 0, joy: float = 0.5, energy: str = "", planned: bool = False, solo: bool = True, location: str = "", companions: Optional[List[str]] = None, notes: str = "") -> PlaySession:
        """Record a play session."""
        session_id = f"play_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = PlaySession(
            session_id=session_id,
            activity=activity or "unspecified",
            play_type=play_type or "exploratory",
            duration_minutes=duration,
            joy_level=joy,
            energy_required=energy or "medium",
            planned=planned,
            solo=solo,
            location=location or "home",
            companions=companions or [],
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

    def get_play_stats(self) -> Dict[str, Any]:
        """Get play pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "joy_sum": 0.0, "duration_sum": 0.0})
        for s in self._sessions:
            by_type[s.play_type]["count"] += 1
            by_type[s.play_type]["joy_sum"] += s.joy_level
            by_type[s.play_type]["duration_sum"] += s.duration_minutes

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
            }

        dominant = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Energy analysis
        by_energy = defaultdict(lambda: {"count": 0, "joy_sum": 0.0})
        for s in self._sessions:
            by_energy[s.energy_required]["count"] += 1
            by_energy[s.energy_required]["joy_sum"] += s.joy_level

        energy_stats = {}
        for e, data in by_energy.items():
            count = data["count"]
            energy_stats[e] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Drought detection
        recent = [s for s in self._sessions if s.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        drought = len(recent) < 2

        # Planned vs spontaneous
        planned_count = sum(1 for s in self._sessions if s.planned)
        spontaneous_count = len(self._sessions) - planned_count

        return {
            "total_sessions": len(self._sessions),
            "type_stats": type_stats,
            "dominant_type": dominant[0],
            "energy_stats": energy_stats,
            "avg_joy": round(sum(s.joy_level for s in self._sessions) / len(self._sessions), 2),
            "avg_duration": round(sum(s.duration_minutes for s in self._sessions) / len(self._sessions), 1),
            "planned_vs_spontaneous": {"planned": planned_count, "spontaneous": spontaneous_count},
            "solo_vs_social": {"solo": sum(1 for s in self._sessions if s.solo), "social": sum(1 for s in self._sessions if not s.solo)},
            "drought": drought,
        }

    def get_play_suggestion(self, energy: str = "medium", time: float = 30, mood: str = "neutral", solo: bool = True) -> Dict[str, Any]:
        """Get play idea."""
        suggestions = {
            "competitive": {
                "low": ["Card game with yourself (solitaire)", "Online trivia", "Word puzzle race"],
                "medium": ["Board game with friend", "Video game match", "Pool/billiards"],
                "high": ["Team sport pickup game", "Escape room", "Tournament"],
            },
            "creative": {
                "low": ["Doodle for 5 minutes", "Hum a made-up song", "Rearrange something beautiful"],
                "medium": ["Write a silly poem", "Cook something new without a recipe", "Build with LEGO"],
                "high": ["Paint/draw for an hour", "Write a short story", "Pottery class"],
            },
            "physical": {
                "low": ["Stretch like a cat", "Dance to one song", "Walk barefoot on grass"],
                "medium": ["Bike ride", "Swim", "Frisbee in park"],
                "high": ["Rock climbing", "Dance class", "Surfing/rollerblading"],
            },
            "social": {
                "low": ["Send a funny meme to a friend", "Call someone just to laugh"],
                "medium": ["Game night", "Karaoke", "Improv class"],
                "high": ["Host a party", "Join a club", "Team sport"],
            },
            "imaginative": {
                "low": ["Daydream out the window", "Invent a character", "Rename everything you see"],
                "medium": ["Write a fictional diary entry", "Roleplay a scene", "Visit a place pretending you're a tourist"],
                "high": ["LARP", "Write a screenplay", "Design a fantasy world"],
            },
            "exploratory": {
                "low": ["Explore a new playlist", "Taste something you've never had", "Look up a random Wikipedia article"],
                "medium": ["Visit a new neighborhood", "Try a new hobby for an hour", "Go to a museum"],
                "high": ["Road trip to somewhere unknown", "Try an extreme sport", "Learn a language for a trip"],
            },
        }

        # Pick random type and energy-appropriate activity
        play_types = list(suggestions.keys())
        selected_type = random.choice(play_types)
        
        energy_options = suggestions[selected_type].get(energy, suggestions[selected_type]["medium"])
        activity = random.choice(energy_options)

        if solo and "friend" in activity.lower():
            activity = activity.replace("with friend", "solo").replace("game night", "solo puzzle night")

        return {
            "activity": activity,
            "type": selected_type,
            "energy": energy,
            "time": time,
            "mood": mood,
            "solo": solo,
            "why": f"{selected_type.capitalize()} play boosts creativity and reduces stress.",
            "commitment": "Optional. Stop whenever it stops being fun.",
        }

    def get_playfulness_score(self) -> int:
        """Calculate overall play health (0-100)."""
        if not self._sessions:
            return 35

        # Joy
        avg_joy = sum(s.joy_level for s in self._sessions) / len(self._sessions)

        # Frequency
        recent = [s for s in self._sessions if s.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        frequency = len(recent)

        # Variety
        unique_types = len(set(s.play_type for s in self._sessions))

        # Spontaneity
        spontaneous = sum(1 for s in self._sessions if not s.planned)
        spontaneity_rate = spontaneous / len(self._sessions)

        score = (avg_joy * 30) + (min(frequency, 10) * 4) + (unique_types * 5) + (spontaneity_rate * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_joy"] = round(sum(s.joy_level for s in self._sessions) / len(self._sessions), 2)
            self._stats["planned_rate"] = round(sum(1 for s in self._sessions if s.planned) / len(self._sessions), 2)
            self._stats["solo_rate"] = round(sum(1 for s in self._sessions if s.solo) / len(self._sessions), 2)

            by_type = defaultdict(int)
            for s in self._sessions:
                by_type[s.play_type] += 1
            if by_type:
                self._stats["dominant_type"] = max(by_type.items(), key=lambda x: x[1])[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.play_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.play_coach")

    def _log_session(self, session: PlaySession):
        try:
            with open(PLAY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "activity": session.activity,
                    "type": session.play_type,
                    "duration": session.duration_minutes,
                    "joy": session.joy_level,
                    "planned": session.planned,
                    "solo": session.solo,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.play_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pc_instance: Optional[PlayCoach] = None
_pc_lock = threading.Lock()


def get_play_coach() -> PlayCoach:
    global _pc_instance
    with _pc_lock:
        if _pc_instance is None:
            _pc_instance = PlayCoach()
        return _pc_instance
