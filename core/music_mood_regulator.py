"""
LOVE Music Mood Regulator — Sonic Intelligence (Modern AI Pattern)

Most people let music happen to them. This regulator:

1. MUSIC TRACKING
   - Record music listening moments and their characteristics
   - Track music types (energizing, calming, focusing, emotional, nostalgic, uplifting)
   - Log mood_before, mood_after, and regulation quality

2. PATTERN ANALYSIS
   - Identify the user's music regulation profile (passive, reactive, intentional, masterful)
   - Find music patterns that create desired states vs unwanted ones
   - Detect chronic mismatched listening and its costs

3. REGULATION BUILDING
   - Suggest practices for intentional music use
   - Provide frameworks for music as medicine
   - Recommend practices for curating sonic environments

4. SONIC WELLBEING CULTIVATION
   - Track the correlation between music and emotional regulation
   - Alert when music is reinforcing negative states
   - Celebrate moments of masterful sonic self-regulation

Architecture:
- record_music(song, type, mood_before, mood_after, regulation): Log music
- get_music_stats(): Get music pattern analysis
- get_music_suggestion(capacity, context): Get suggestion
- get_music_score(): Calculate overall music health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "music_mood_regulator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MUSIC_LOG = DATA_DIR / "musics.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MusicEntry:
    """A tracked music listening moment."""
    entry_id: str = ""
    song: str = ""  # what was listened to
    music_type: str = ""  # energizing, calming, focusing, emotional, nostalgic, uplifting
    mood_before: float = 0.0  # 0-1
    mood_after: float = 0.0  # 0-1
    regulation: float = 0.0  # 0-1 did it help?
    intention: float = 0.0  # 0-1 was it intentional?
    duration: float = 0.0  # minutes
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MusicMoodRegulator:
    """
    Intelligent music mood regulator with passive listening detection and sonic wellbeing cultivation.
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
            "avg_regulation": 0.0,
            "avg_intention": 0.0,
            "mismatch_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_music(self, song: str = "", music_type: str = "", mood_before: float = 0.0, mood_after: float = 0.0, regulation: float = 0.0, intention: float = 0.0, duration: float = 0.0, notes: str = "") -> MusicEntry:
        """Record a music listening moment."""
        entry_id = f"mus_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = MusicEntry(
            entry_id=entry_id,
            song=song or "unspecified",
            music_type=music_type or "calming",
            mood_before=mood_before,
            mood_after=mood_after,
            regulation=regulation,
            intention=intention,
            duration=duration,
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

    def get_music_stats(self) -> Dict[str, Any]:
        """Get music pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "reg_sum": 0.0, "intention_sum": 0.0, "mood_change_sum": 0.0})
        for e in self._entries:
            by_type[e.music_type]["count"] += 1
            by_type[e.music_type]["reg_sum"] += e.regulation
            by_type[e.music_type]["intention_sum"] += e.intention
            by_type[e.music_type]["mood_change_sum"] += (e.mood_after - e.mood_before)

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_regulation": round(data["reg_sum"] / count, 2),
                "avg_intention": round(data["intention_sum"] / count, 2),
                "avg_mood_change": round(data["mood_change_sum"] / count, 2),
            }

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_reg = sum(e.regulation for e in high_int) / len(high_int)
            low_int_reg = sum(e.regulation for e in low_int) / len(low_int)
            high_int_change = sum(e.mood_after - e.mood_before for e in high_int) / len(high_int)
            low_int_change = sum(e.mood_after - e.mood_before for e in low_int) / len(low_int)
        else:
            high_int_reg = 0
            low_int_reg = 0
            high_int_change = 0
            low_int_change = 0

        # Mood improvement analysis
        improved = [e for e in self._entries if e.mood_after > e.mood_before]
        worsened = [e for e in self._entries if e.mood_after < e.mood_before]
        if improved and worsened:
            improved_reg = sum(e.regulation for e in improved) / len(improved)
            worsened_reg = sum(e.regulation for e in worsened) / len(worsened)
        else:
            improved_reg = 0
            worsened_reg = 0

        # Mismatch risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_reg = sum(e.regulation for e in recent) / len(recent)
            recent_int = sum(e.intention for e in recent) / len(recent)
            mismatch_risk = recent_reg < 0.3 and recent_int < 0.3
        else:
            mismatch_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "intention_impact": {
                "high_intention_regulation": round(high_int_reg, 2),
                "low_intention_regulation": round(low_int_reg, 2),
                "high_intention_mood_change": round(high_int_change, 2),
                "low_intention_mood_change": round(low_int_change, 2),
            },
            "mood_effect": {
                "improved_regulation": round(improved_reg, 2),
                "worsened_regulation": round(worsened_reg, 2),
            },
            "mismatch_risk": mismatch_risk,
            "avg_regulation": round(sum(e.regulation for e in self._entries) / len(self._entries), 2),
            "avg_intention": round(sum(e.intention for e in self._entries) / len(self._entries), 2),
        }

    def get_music_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get music suggestion."""
        suggestions = [
            "Music is medicine. But only if you use it intentionally. The person who puts on sad music when they're sad is not healing. They're wallowing. Choose your medicine wisely.",
            "Match the music to the mood you want, not the mood you have. Anxious? Calming music. Tired? Energizing music. Down? Uplifting music. Don't reinforce. Redirect.",
            "Create playlists for states. One for focus. One for energy. One for calm. One for joy. When you need a state change, press play. Don't think. Just play.",
            "Notice how different music affects you. Some songs lift you. Others sink you. Pay attention. Curate your library like a pharmacy. Keep the medicine. Remove the poison.",
            "Silence is also music. Sometimes the best sonic environment is none at all. When you're overwhelmed, turn it off. Let your nervous system rest.",
            "Listen actively. Not as background noise. Put on headphones. Close your eyes. Let the music in. Passive listening is entertainment. Active listening is therapy.",
            "Your musical taste is not random. It reflects your psychology. The minor keys. The major keys. The tempo. The lyrics. Listen to what you choose. It tells you who you are.",
            "Music connects you to time. A song can transport you to a moment years ago. Use this. Create new memories with music. Attach songs to good times. Build a soundtrack for your life.",
            "Share music. Send a song to someone. Explain why. 'This made me think of you.' Music is a bridge. Use it to connect. It's one of the most human things you can do.",
            "The person who masters their sonic environment masters their emotional environment. Music is not trivial. It's a powerful tool for state management. Use it with intention."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One intentional song. One playlist. One moment of active listening. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A curated playlist. A sonic environment designed. A mood matched with music. Medium regulation."
        else:
            capacity_note = "Good capacity. Deep sonic mastery. A systematic use of music for emotional regulation and wellbeing. You have the strength to conduct your own symphony."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Music is one of the most powerful tools for emotional regulation that most people use unconsciously. They put on whatever is available. Whatever is familiar. Whatever matches their current mood. And they wonder why they stay stuck. The work of music mood regulation is about using music intentionally. About choosing the sonic environment that creates the state you want. About understanding that music is not just entertainment. It's medicine. It's therapy. It's a bridge to different emotional states. And it's available to anyone who remembers to use it with purpose. The person who masters their music masters their mood. And the person who masters their mood masters their life."
        }

    def get_music_score(self) -> int:
        """Calculate overall music health (0-100)."""
        if not self._entries:
            return 25

        avg_reg = sum(e.regulation for e in self._entries) / len(self._entries)
        avg_int = sum(e.intention for e in self._entries) / len(self._entries)
        avg_change = sum(e.mood_after - e.mood_before for e in self._entries) / len(self._entries)
        avg_dur = sum(e.duration for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_reg = sum(e.regulation for e in recent) / len(recent)
            recent_int = sum(e.intention for e in recent) / len(recent)
        else:
            recent_reg = 0
            recent_int = 0

        # Mismatch penalty
        mismatch_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_reg_30 = sum(e.regulation for e in last_30) / len(last_30)
            recent_int_30 = sum(e.intention for e in last_30) / len(last_30)
            if recent_reg_30 < 0.3 and recent_int_30 < 0.3:
                mismatch_penalty = 15

        # Type variety
        unique_types = len(set(e.music_type for e in self._entries))

        score = (avg_reg * 25) + (avg_int * 20) + (avg_change * 15) + (recent_reg * 10) + (recent_int * 10) + (unique_types * 2) + min(5, avg_dur / 10) - mismatch_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_regulation"] = round(sum(e.regulation for e in self._entries) / len(self._entries), 2)
            self._stats["avg_intention"] = round(sum(e.intention for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_reg = sum(e.regulation for e in recent) / len(recent)
                recent_int = sum(e.intention for e in recent) / len(recent)
                self._stats["mismatch_risk"] = recent_reg < 0.3 and recent_int < 0.3
            else:
                self._stats["mismatch_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.music_mood_regulator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.music_mood_regulator")

    def _log_entry(self, entry: MusicEntry):
        try:
            with open(MUSIC_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "song": entry.song,
                    "music_type": entry.music_type,
                    "regulation": entry.regulation,
                    "intention": entry.intention,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.music_mood_regulator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mmr_instance: Optional[MusicMoodRegulator] = None
_mmr_lock = threading.Lock()


def get_music_mood_regulator() -> MusicMoodRegulator:
    global _mmr_instance
    with _mmr_lock:
        if _mmr_instance is None:
            _mmr_instance = MusicMoodRegulator()
        return _mmr_instance
