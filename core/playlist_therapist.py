"""
LOVE Playlist Therapist — Curation Intelligence (Modern AI Pattern)

Most people shuffle randomly. This therapist:

1. PLAYLIST TRACKING
   - Record playlist moments and their characteristics
   - Track playlist types (energizing, calming, focusing, emotional, nostalgic, celebratory)
   - Log match, transition, arc, and therapeutic quality

2. PATTERN ANALYSIS
   - Identify the user's curation profile (random, reactive, intentional, therapeutic)
   - Find playlist patterns that create flow vs jarring shifts
   - Detect chronic mismatch and its costs

3. CURATION BUILDING
   - Suggest practices for intentional playlist design
   - Provide frameworks for sonic storytelling
   - Recommend practices for mood-appropriate sequencing

4. SONIC NARRATIVE CULTIVATION
   - Track the correlation between playlist quality and emotional journey
   - Alert when randomness is undermining intention
   - Celebrate moments of masterful sonic curation

Architecture:
- record_playlist(song, type, match, transition, arc, therapeutic): Log playlist
- get_playlist_stats(): Get playlist pattern analysis
- get_playlist_suggestion(capacity, context): Get suggestion
- get_playlist_score(): Calculate overall playlist health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "playlist_therapist"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PLAYLIST_LOG = DATA_DIR / "playlists.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PlaylistEntry:
    """A tracked playlist moment."""
    entry_id: str = ""
    song: str = ""  # what was played
    playlist_type: str = ""  # energizing, calming, focusing, emotional, nostalgic, celebratory
    match: float = 0.0  # 0-1 did it match the intended mood?
    transition: float = 0.0  # 0-1 smooth transition?
    arc: float = 0.0  # 0-1 overall journey quality
    therapeutic: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PlaylistTherapist:
    """
    Intelligent playlist therapist with randomness detection and sonic narrative cultivation.
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
            "avg_match": 0.0,
            "avg_therapeutic": 0.0,
            "randomness_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_playlist(self, song: str = "", playlist_type: str = "", match: float = 0.0, transition: float = 0.0, arc: float = 0.0, therapeutic: float = 0.0, notes: str = "") -> PlaylistEntry:
        """Record a playlist moment."""
        entry_id = f"plt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PlaylistEntry(
            entry_id=entry_id,
            song=song or "unspecified",
            playlist_type=playlist_type or "calming",
            match=match,
            transition=transition,
            arc=arc,
            therapeutic=therapeutic,
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

    def get_playlist_stats(self) -> Dict[str, Any]:
        """Get playlist pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "match_sum": 0.0, "trans_sum": 0.0, "arc_sum": 0.0})
        for e in self._entries:
            by_type[e.playlist_type]["count"] += 1
            by_type[e.playlist_type]["match_sum"] += e.match
            by_type[e.playlist_type]["trans_sum"] += e.transition
            by_type[e.playlist_type]["arc_sum"] += e.arc

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_match": round(data["match_sum"] / count, 2),
                "avg_transition": round(data["trans_sum"] / count, 2),
                "avg_arc": round(data["arc_sum"] / count, 2),
            }

        # Match analysis
        high_match = [e for e in self._entries if e.match > 0.7]
        low_match = [e for e in self._entries if e.match < 0.4]
        if high_match and low_match:
            high_match_th = sum(e.therapeutic for e in high_match) / len(high_match)
            low_match_th = sum(e.therapeutic for e in low_match) / len(low_match)
            high_match_arc = sum(e.arc for e in high_match) / len(high_match)
            low_match_arc = sum(e.arc for e in low_match) / len(low_match)
        else:
            high_match_th = 0
            low_match_th = 0
            high_match_arc = 0
            low_match_arc = 0

        # Transition analysis
        high_trans = [e for e in self._entries if e.transition > 0.7]
        low_trans = [e for e in self._entries if e.transition < 0.4]
        if high_trans and low_trans:
            high_trans_arc = sum(e.arc for e in high_trans) / len(high_trans)
            low_trans_arc = sum(e.arc for e in low_trans) / len(low_trans)
        else:
            high_trans_arc = 0
            low_trans_arc = 0

        # Randomness risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_match = sum(e.match for e in recent) / len(recent)
            recent_arc = sum(e.arc for e in recent) / len(recent)
            randomness_risk = recent_match < 0.3 and recent_arc < 0.3
        else:
            randomness_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "match_impact": {
                "high_match_therapeutic": round(high_match_th, 2),
                "low_match_therapeutic": round(low_match_th, 2),
                "high_match_arc": round(high_match_arc, 2),
                "low_match_arc": round(low_match_arc, 2),
            },
            "transition_effect": {
                "high_transition_arc": round(high_trans_arc, 2),
                "low_transition_arc": round(low_trans_arc, 2),
            },
            "randomness_risk": randomness_risk,
            "avg_match": round(sum(e.match for e in self._entries) / len(self._entries), 2),
            "avg_therapeutic": round(sum(e.therapeutic for e in self._entries) / len(self._entries), 2),
        }

    def get_playlist_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get playlist suggestion."""
        suggestions = [
            "A playlist is a journey. Not a random collection. Think about where you want to go. Up? Down? In? Out? Then choose songs that take you there. In order.",
            "Transitions matter. The song after this one should feel like a natural next step. Not a jump. Pay attention to the space between songs. That's where the magic is.",
            "Build arcs. Start here. Go there. Return. Or don't. But have a shape. A beginning. A middle. An end. Playlists with arcs are playlists that move you.",
            "Don't shuffle when you need medicine. Shuffling is for entertainment. Sequencing is for therapy. When you're working through something, curate. Don't gamble.",
            "Match the playlist to the moment. Morning commute? Energizing. Evening wind-down? Calming. Deep work? Focusing. The right playlist for the right moment is invisible power.",
            "Remove songs that don't fit. Even if you love them. A playlist is a container. It has a purpose. Songs that don't serve the purpose dilute the medicine. Be ruthless.",
            "Create playlists for emotional states. One for hope. One for grief. One for focus. One for joy. When you need a state, you have a prescription ready.",
            "Notice when a playlist fails. When you skip three songs in a row. That's data. The playlist is wrong. Or the moment is wrong. Adjust.",
            "Share playlists. They're gifts. 'This is what I'm listening to.' That's intimacy. That's connection. Music is a language. Share your vocabulary.",
            "The person who curates their sonic environment curates their emotional environment. A playlist is not trivial. It's a technology for state management. Use it well."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One intentional song choice. One playlist created. One moment of curation. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A three-song arc. A mood-matched playlist. A transition noticed. Medium therapy."
        else:
            capacity_note = "Good capacity. Deep sonic narrative work. A systematic practice of playlist curation for emotional journey. You have the strength to conduct your own symphony."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Playlist therapy is about understanding that the order of songs is as important as the songs themselves. Most people listen to music passively. They shuffle. They skip. They let algorithms decide. And they wonder why their emotional state feels random. The work of playlist therapy is about intentionality. About creating sonic journeys that take you where you want to go. About understanding transitions, arcs, and matches. About curating your audio environment the way an interior designer curates a room. Because the soundtrack of your life is not background noise. It's the emotional architecture of your days. And you can design it."
        }

    def get_playlist_score(self) -> int:
        """Calculate overall playlist health (0-100)."""
        if not self._entries:
            return 25

        avg_match = sum(e.match for e in self._entries) / len(self._entries)
        avg_trans = sum(e.transition for e in self._entries) / len(self._entries)
        avg_arc = sum(e.arc for e in self._entries) / len(self._entries)
        avg_th = sum(e.therapeutic for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_match = sum(e.match for e in recent) / len(recent)
            recent_arc = sum(e.arc for e in recent) / len(recent)
        else:
            recent_match = 0
            recent_arc = 0

        # Randomness penalty
        rand_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_match_30 = sum(e.match for e in last_30) / len(last_30)
            recent_arc_30 = sum(e.arc for e in last_30) / len(last_30)
            if recent_match_30 < 0.3 and recent_arc_30 < 0.3:
                rand_penalty = 15

        # Type variety
        unique_types = len(set(e.playlist_type for e in self._entries))

        score = (avg_match * 25) + (avg_trans * 20) + (avg_arc * 20) + (avg_th * 15) + (recent_match * 5) + (recent_arc * 5) + (unique_types * 2) - rand_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_match"] = round(sum(e.match for e in self._entries) / len(self._entries), 2)
            self._stats["avg_therapeutic"] = round(sum(e.therapeutic for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_match = sum(e.match for e in recent) / len(recent)
                recent_arc = sum(e.arc for e in recent) / len(recent)
                self._stats["randomness_risk"] = recent_match < 0.3 and recent_arc < 0.3
            else:
                self._stats["randomness_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.playlist_therapist")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.playlist_therapist")

    def _log_entry(self, entry: PlaylistEntry):
        try:
            with open(PLAYLIST_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "song": entry.song,
                    "playlist_type": entry.playlist_type,
                    "match": entry.match,
                    "therapeutic": entry.therapeutic,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.playlist_therapist")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pt_instance: Optional[PlaylistTherapist] = None
_pt_lock = threading.Lock()


def get_playlist_therapist() -> PlaylistTherapist:
    global _pt_instance
    with _pt_lock:
        if _pt_instance is None:
            _pt_instance = PlaylistTherapist()
        return _pt_instance
