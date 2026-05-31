"""
LOVE Humor & Playfulness Trainer — Lightness Intelligence (Modern AI Pattern)

Most adults have forgotten how to play. This trainer:

1. PLAYFULNESS TRACKING
   - Record playful moments and their characteristics
   - Track humor types (wit, absurdity, wordplay, physical, situational)
   - Log playfulness outcomes and their effects on mood and connection

2. PATTERN ANALYSIS
   - Identify the user's playfulness profile (witty, silly, observational, physical)
   - Find contexts where humor thrives
   - Detect seriousness accumulation and its costs

3. PLAYFULNESS BUILDING
   - Suggest humor exercises matched to current mood
   - Provide playfulness practices for serious contexts
   - Recommendation laughter and play routines

4. LIGHTNESS CULTIVATION
   - Track the correlation between playfulness and resilience
   - Alert when seriousness is becoming chronic
   - Celebrate moments of genuine fun

Architecture:
- record_play(moment, humor_type, mood_effect, connection): Log play
- get_playfulness_stats(): Get playfulness pattern analysis
- get_playfulness_practice(seriousness, context): Get practice
- get_playfulness_score(): Calculate overall playfulness health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "humor_playfulness_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PLAY_LOG = DATA_DIR / "play.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PlayfulnessEntry:
    """A tracked playfulness entry."""
    entry_id: str = ""
    moment: str = ""
    humor_type: str = ""  # wit, absurdity, wordplay, physical, situational, self_deprecating
    mood_before: float = 0.5
    mood_after: float = 0.5
    connection_boost: float = 0.0  # 0-1
    context: str = ""  # work, social, alone, family, public
    spontaneity: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HumorPlayfulnessTrainer:
    """
    Intelligent humor and playfulness trainer with seriousness detection and lightness exercises.
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
            "avg_mood_boost": 0.0,
            "avg_connection": 0.0,
            "dominant_type": "",
            "seriousness_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_play(self, moment: str = "", humor_type: str = "", mood_before: float = 0.5, mood_after: float = 0.5, connection_boost: float = 0.0, context: str = "", spontaneity: float = 0.5, notes: str = "") -> PlayfulnessEntry:
        """Record a playfulness entry."""
        entry_id = f"play_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PlayfulnessEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            humor_type=humor_type or "situational",
            mood_before=mood_before,
            mood_after=mood_after,
            connection_boost=connection_boost,
            context=context or "general",
            spontaneity=spontaneity,
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

    def get_playfulness_stats(self) -> Dict[str, Any]:
        """Get playfulness pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "mood_sum": 0.0, "connection_sum": 0.0, "spontaneity_sum": 0.0})
        for e in self._entries:
            by_type[e.humor_type]["count"] += 1
            by_type[e.humor_type]["mood_sum"] += e.mood_after - e.mood_before
            by_type[e.humor_type]["connection_sum"] += e.connection_boost
            by_type[e.humor_type]["spontaneity_sum"] += e.spontaneity

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_mood_boost": round(data["mood_sum"] / count, 2),
                "avg_connection": round(data["connection_sum"] / count, 2),
                "avg_spontaneity": round(data["spontaneity_sum"] / count, 2),
            }

        dominant_type = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "mood_sum": 0.0, "connection_sum": 0.0})
        for e in self._entries:
            by_context[e.context]["count"] += 1
            by_context[e.context]["mood_sum"] += e.mood_after - e.mood_before
            by_context[e.context]["connection_sum"] += e.connection_boost

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_mood_boost": round(data["mood_sum"] / count, 2),
                "avg_connection": round(data["connection_sum"] / count, 2),
            }

        best_context = max(context_stats.items(), key=lambda x: x[1]["avg_mood_boost"] + x[1]["avg_connection"]) if context_stats else ("", {})

        # Seriousness detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if len(self._entries) > 14:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if recent and older:
                recent_play = len(recent) / max(1, len(older) / 2)
                seriousness_risk = recent_play < 0.5
            else:
                seriousness_risk = False
        else:
            seriousness_risk = False

        # Spontaneity analysis
        avg_spontaneity = sum(e.spontaneity for e in self._entries) / len(self._entries)
        planned = [e for e in self._entries if e.spontaneity < 0.4]
        spontaneous = [e for e in self._entries if e.spontaneity > 0.7]
        if planned and spontaneous:
            planned_mood = sum(e.mood_after - e.mood_before for e in planned) / len(planned)
            spontaneous_mood = sum(e.mood_after - e.mood_before for e in spontaneous) / len(spontaneous)
        else:
            planned_mood = 0
            spontaneous_mood = 0

        # Recent trend
        if recent:
            recent_mood = sum(e.mood_after - e.mood_before for e in recent) / len(recent)
            recent_connection = sum(e.connection_boost for e in recent) / len(recent)
        else:
            recent_mood = 0
            recent_connection = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_mood = sum(e.mood_after - e.mood_before for e in older) / len(older)
            older_connection = sum(e.connection_boost for e in older) / len(older)
            mood_trend = recent_mood - older_mood
            connection_trend = recent_connection - older_connection
        else:
            mood_trend = 0
            connection_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "dominant_type": dominant_type[0],
            "context_stats": context_stats,
            "best_context": best_context[0],
            "seriousness_risk": seriousness_risk,
            "avg_spontaneity": round(avg_spontaneity, 2),
            "spontaneity_comparison": {
                "planned_mood": round(planned_mood, 2),
                "spontaneous_mood": round(spontaneous_mood, 2),
            },
            "avg_mood_boost": round(sum(e.mood_after - e.mood_before for e in self._entries) / len(self._entries), 2),
            "avg_connection": round(sum(e.connection_boost for e in self._entries) / len(self._entries), 2),
            "mood_trend": round(mood_trend, 2),
            "connection_trend": round(connection_trend, 2),
        }

    def get_playfulness_practice(self, seriousness: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get practice."""
        practices = [
            "Make a silly face in the mirror. Just for you. No one else needs to know.",
            "Write a limerick about your current problem. Rhyme makes everything smaller.",
            "Do one thing 'wrong' on purpose. Wear mismatched socks. Order dessert first.",
            "Find the absurdity in your current situation. There's always something ridiculous if you look.",
            "Play a word association game with yourself. No judgment. Just flow.",
            "Dance to one song. Alone. Badly. The worse, the better.",
            "Tell a dad joke. To yourself. Out loud. Groan authentically.",
            "Imagine your problem as a cartoon. What would the characters look like?",
            "Speak in an accent for 5 minutes. With a pet or plant if no humans are available.",
            "Make up a ridiculous backstory for a stranger. The more elaborate, the better.",
            "Turn your to-do list into a rap. Perform it. You're welcome.",
            "Find something in your room and give it a personality. Have a conversation.",
            "Draw your current mood. Badly. Stick figures are encouraged.",
            "Make animal noises. Yes, really. Start with your favorite.",
            "Pretend you're a character in a movie. How would they handle this?",
        ]

        if seriousness > 0.8:
            seriousness_note = "Seriousness level: critical. You've forgotten how to play. This is not a character flaw. It's a habit. Break it."
        elif seriousness > 0.5:
            seriousness_note = "Moderate seriousness. You could use some lightness. One small silly thing."
        else:
            seriousness_note = "Good lightness. Keep the play alive. Don't let adulthood steal your joy."

        return {
            "seriousness": seriousness,
            "context": context or "general",
            "practice": random.choice(practices),
            "seriousness_note": seriousness_note,
            "principle": "Play is not frivolous. It's how mammals learn, bond, and recover. The most serious people are often the most brittle. Play keeps you flexible. It makes you harder to break. And it's the fastest way to remember that you're alive.",
        }

    def get_playfulness_score(self) -> int:
        """Calculate overall playfulness health (0-100)."""
        if not self._entries:
            return 30

        # Mood boost and connection
        avg_mood_boost = sum(e.mood_after - e.mood_before for e in self._entries) / len(self._entries)
        avg_connection = sum(e.connection_boost for e in self._entries) / len(self._entries)

        # Spontaneity
        avg_spontaneity = sum(e.spontaneity for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.humor_type for e in self._entries))

        # Context variety
        unique_contexts = len(set(e.context for e in self._entries))

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_mood = sum(e.mood_after - e.mood_before for e in recent) / len(recent)
            recent_connection = sum(e.connection_boost for e in recent) / len(recent)
            recent_spontaneity = sum(e.spontaneity for e in recent) / len(recent)
        else:
            recent_mood = 0
            recent_connection = 0
            recent_spontaneity = 0

        # Seriousness penalty
        if len(self._entries) > 14:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if recent and older:
                recent_play = len(recent) / max(1, len(older) / 2)
                seriousness_penalty = 10 if recent_play < 0.5 else 0
            else:
                seriousness_penalty = 0
        else:
            seriousness_penalty = 0

        score = (avg_mood_boost * 25) + (avg_connection * 20) + (avg_spontaneity * 15) + (unique_types * 2) + (unique_contexts * 2) + (recent_mood * 20) + (recent_connection * 10) + (recent_spontaneity * 10) - seriousness_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_mood_boost"] = round(sum(e.mood_after - e.mood_before for e in self._entries) / len(self._entries), 2)
            self._stats["avg_connection"] = round(sum(e.connection_boost for e in self._entries) / len(self._entries), 2)

            by_type = defaultdict(int)
            for e in self._entries:
                by_type[e.humor_type] += 1
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1])
                self._stats["dominant_type"] = dominant[0]

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if len(self._entries) > 14:
                older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
                if recent and older:
                    recent_play = len(recent) / max(1, len(older) / 2)
                    self._stats["seriousness_risk"] = recent_play < 0.5

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

    def _log_entry(self, entry: PlayfulnessEntry):
        try:
            with open(PLAY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "humor_type": entry.humor_type,
                    "mood_before": entry.mood_before,
                    "mood_after": entry.mood_after,
                    "connection_boost": entry.connection_boost,
                    "context": entry.context,
                    "spontaneity": entry.spontaneity,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hpt_instance: Optional[HumorPlayfulnessTrainer] = None
_hpt_lock = threading.Lock()


def get_humor_playfulness_trainer() -> HumorPlayfulnessTrainer:
    global _hpt_instance
    with _hpt_lock:
        if _hpt_instance is None:
            _hpt_instance = HumorPlayfulnessTrainer()
        return _hpt_instance
