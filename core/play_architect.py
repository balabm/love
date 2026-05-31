"""
LOVE Play Architect — Recreation Intelligence (Modern AI Pattern)

Most adults have forgotten how to play. This architect:

1. PLAY TRACKING
   - Record play experiences and their characteristics
   - Track play types (physical, creative, social, imaginative, exploratory, competitive)
   - Log joy, freedom, and presence during play

2. PATTERN ANALYSIS
   - Identify the user's play profile (playful, serious, nostalgic, hesitant)
   - Find play patterns that create vitality and connection
   - Detect play deficiency and its consequences

3. PLAY BUILDING
   - Suggest play activities matched to current mood, energy, and constraints
   - Provide frameworks for integrating play into daily life
   - Recommend solo and social play based on needs

4. VITALITY CULTIVATION
   - Track the correlation between play and overall wellbeing
   - Alert when life has become excessively work-focused
   - Celebrate moments of genuine joy and freedom

Architecture:
- record_play(activity, type, joy, freedom, presence): Log play
- get_play_stats(): Get play pattern analysis
- get_play_suggestion(capacity, context): Get suggestion
- get_play_score(): Calculate overall play health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "play_architect"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PLAY_LOG = DATA_DIR / "play.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PlayEntry:
    """A tracked play experience."""
    entry_id: str = ""
    activity: str = ""  # what was played
    play_type: str = ""  # physical, creative, social, imaginative, exploratory, competitive
    joy: float = 0.5  # 0-1
    freedom: float = 0.0  # 0-1
    presence: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    novelty: float = 0.0  # 0-1
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PlayArchitect:
    """
    Intelligent play architect with vitality detection and joy cultivation.
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
        self._entries: deque = deque(maxlen=300)
        self._stats = {
            "total_entries": 0,
            "avg_joy": 0.0,
            "avg_presence": 0.0,
            "play_deficit_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_play(self, activity: str = "", play_type: str = "", joy: float = 0.5, freedom: float = 0.0, presence: float = 0.0, connection: float = 0.0, novelty: float = 0.0, duration_minutes: float = 0.0, notes: str = "") -> PlayEntry:
        """Record a play experience."""
        entry_id = f"ply_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PlayEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            play_type=play_type or "exploratory",
            joy=joy,
            freedom=freedom,
            presence=presence,
            connection=connection,
            novelty=novelty,
            duration_minutes=duration_minutes,
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

    def get_play_stats(self) -> Dict[str, Any]:
        """Get play pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "joy_sum": 0.0, "freedom_sum": 0.0, "presence_sum": 0.0})
        for e in self._entries:
            by_type[e.play_type]["count"] += 1
            by_type[e.play_type]["joy_sum"] += e.joy
            by_type[e.play_type]["freedom_sum"] += e.freedom
            by_type[e.play_type]["presence_sum"] += e.presence

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_freedom": round(data["freedom_sum"] / count, 2),
                "avg_presence": round(data["presence_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_joy"]) if type_stats else ("", {})

        # Joy analysis
        high_joy = [e for e in self._entries if e.joy > 0.7]
        low_joy = [e for e in self._entries if e.joy < 0.4]
        if high_joy and low_joy:
            high_joy_presence = sum(e.presence for e in high_joy) / len(high_joy)
            low_joy_presence = sum(e.presence for e in low_joy) / len(low_joy)
            high_joy_conn = sum(e.connection for e in high_joy) / len(high_joy)
            low_joy_conn = sum(e.connection for e in low_joy) / len(low_joy)
        else:
            high_joy_presence = 0
            low_joy_presence = 0
            high_joy_conn = 0
            low_joy_conn = 0

        # Novelty analysis
        high_novelty = [e for e in self._entries if e.novelty > 0.7]
        low_novelty = [e for e in self._entries if e.novelty < 0.4]
        if high_novelty and low_novelty:
            high_nov_joy = sum(e.joy for e in high_novelty) / len(high_novelty)
            low_nov_joy = sum(e.joy for e in low_novelty) / len(low_novelty)
        else:
            high_nov_joy = 0
            low_nov_joy = 0

        # Play deficit detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_presence = sum(e.presence for e in recent) / len(recent)
            play_deficit_risk = recent_joy < 0.3 and recent_presence < 0.3
        else:
            play_deficit_risk = True

        return {
            "total_entries": len(self._entries),
            "total_hours": round(sum(e.duration_minutes for e in self._entries) / 60, 1),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "joy_impact": {
                "high_joy_presence": round(high_joy_presence, 2),
                "low_joy_presence": round(low_joy_presence, 2),
                "high_joy_connection": round(high_joy_conn, 2),
                "low_joy_connection": round(low_joy_conn, 2),
            },
            "novelty_effect": {
                "high_novelty_joy": round(high_nov_joy, 2),
                "low_novelty_joy": round(low_nov_joy, 2),
            },
            "play_deficit_risk": play_deficit_risk,
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
            "avg_presence": round(sum(e.presence for e in self._entries) / len(self._entries), 2),
        }

    def get_play_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get play suggestion."""
        suggestions = [
            "Do something pointless. Not everything has to be productive. Build a sandcastle. Fly a kite. Color. Play exists outside of purpose. That's the point.",
            "Play with a child. Or an animal. They know how. Follow their lead. Be ridiculous. Make funny faces. The permission to be silly is the permission to be free.",
            "Try something new. Not for mastery. For curiosity. A new game. A new sport. A new hobby. Novelty wakes up the brain. It breaks routine. It creates joy.",
            "Play a game. Board game. Video game. Sport. Games create a bounded world where failure is fun. Where competition is safe. Where you can be fully engaged without consequence.",
            "Be creative without judgment. Doodle. Write a silly poem. Dance badly. Sing loudly. Creativity without standards is play. And play is necessary.",
            "Get physical. Run. Jump. Climb. Throw. The body needs play as much as the mind. Physical play releases tension. It connects you to your animal nature.",
            "Make something with your hands. Build. Craft. Cook. The satisfaction of creation without pressure is deeply restorative. It's play that produces.",
            "Explore somewhere new. A neighborhood. A trail. A shop. Curiosity is play. Discovery is play. You don't need a destination. You need a direction.",
            "Play music. Not to perform. To enjoy. Sing. Drum. Strum. Music is one of the oldest forms of play. It's how humans have always expressed joy.",
            "Life without play is not life. It's labor. Schedule play the way you schedule work. Because play is not the opposite of work. It's the complement. The balance. The reason work is worth doing.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Five minutes of anything fun. A game on your phone. A silly song. One joke. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. An hour of play. A hobby. A game with friends. Medium investment in joy."
        else:
            capacity_note = "Good capacity. A full play session. A new activity. A creative project just for fun. You have the energy for real play."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Play is not optional. It's not childish. It's not a waste of time. Play is how mammals learn. How humans bond. How creativity happens. How stress is released. How joy is generated. The adult who has forgotten how to play has forgotten how to live. Play creates the psychological safety that makes everything else possible. The mind that plays is the mind that adapts. The heart that plays is the heart that heals. You don't need to earn play. You need it. Period. Find it. Protect it. Schedule it if you must. But never let go of play.",
        }

    def get_play_score(self) -> int:
        """Calculate overall play health (0-100)."""
        if not self._entries:
            return 25

        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_presence = sum(e.presence for e in self._entries) / len(self._entries)
        avg_freedom = sum(e.freedom for e in self._entries) / len(self._entries)
        avg_connection = sum(e.connection for e in self._entries) / len(self._entries)
        avg_novelty = sum(e.novelty for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_presence = sum(e.presence for e in recent) / len(recent)
        else:
            recent_joy = 0
            recent_presence = 0

        # Play deficit penalty
        deficit_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 3:
            deficit_penalty = 15

        # Type variety
        unique_types = len(set(e.play_type for e in self._entries))

        score = (avg_joy * 30) + (avg_presence * 20) + (avg_freedom * 15) + (avg_connection * 10) + (avg_novelty * 10) + (recent_joy * 10) + (recent_presence * 5) + (unique_types * 2) - deficit_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)
            self._stats["avg_presence"] = round(sum(e.presence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_joy = sum(e.joy for e in recent) / len(recent)
                recent_presence = sum(e.presence for e in recent) / len(recent)
                self._stats["play_deficit_risk"] = recent_joy < 0.3 and recent_presence < 0.3
            else:
                self._stats["play_deficit_risk"] = True

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

    def _log_entry(self, entry: PlayEntry):
        try:
            with open(PLAY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "play_type": entry.play_type,
                    "joy": entry.joy,
                    "presence": entry.presence,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pa_instance: Optional[PlayArchitect] = None
_pa_lock = threading.Lock()


def get_play_architect() -> PlayArchitect:
    global _pa_instance
    with _pa_lock:
        if _pa_instance is None:
            _pa_instance = PlayArchitect()
        return _pa_instance
