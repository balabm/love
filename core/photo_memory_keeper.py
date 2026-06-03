"""
LOVE Photo Memory Keeper — Visual Memory Intelligence (Modern AI Pattern)

Most people take photos without meaning. This keeper:

1. PHOTO TRACKING
   - Record photo moments and their characteristics
   - Track photo types (event, portrait, landscape, detail, candid, intentional)
   - Log intention, quality, emotion, story, and preservation of photos

2. PATTERN ANALYSIS
   - Identify the user's photo profile (mindless, hoarding, developing, curatorial)
   - Find photo patterns that create memory vs clutter
   - Detect chronic mindless snapping and its costs

3. MEMORY BUILDING
   - Suggest practices for intentional photography
   - Provide frameworks for photo-as-memory
   - Recommend practices for quality over quantity

4. VISUAL LEGACY CULTIVATION
   - Track the correlation between photo intention and memory quality
   - Alert when accumulation is replacing curation
   - Celebrate moments of genuine visual storytelling

Architecture:
- record_photo(photo, type, intention, quality, emotion, story, preservation): Log photo
- get_photo_stats(): Get photo pattern analysis
- get_photo_suggestion(capacity, context): Get suggestion
- get_photo_score(): Calculate overall photo health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "photo_memory_keeper"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PHOTO_LOG = DATA_DIR / "photos.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PhotoEntry:
    """A tracked photo moment."""
    entry_id: str = ""
    photo: str = ""  # what was photographed
    photo_type: str = ""  # event, portrait, landscape, detail, candid, intentional
    intention: float = 0.0  # 0-1
    quality: float = 0.0  # 0-1
    emotion: float = 0.0  # 0-1
    story: float = 0.0  # 0-1
    preservation: float = 0.0  # 0-1
    curation: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PhotoMemoryKeeper:
    """
    Intelligent photo memory keeper with mindless-snapping detection and visual legacy cultivation.
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
            "avg_intention": 0.0,
            "avg_story": 0.0,
            "clutter_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_photo(self, photo: str = "", photo_type: str = "", intention: float = 0.0, quality: float = 0.0, emotion: float = 0.0, story: float = 0.0, preservation: float = 0.0, curation: float = 0.0, notes: str = "") -> PhotoEntry:
        """Record a photo moment."""
        entry_id = f"pho_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PhotoEntry(
            entry_id=entry_id,
            photo=photo or "unspecified",
            photo_type=photo_type or "intentional",
            intention=intention,
            quality=quality,
            emotion=emotion,
            story=story,
            preservation=preservation,
            curation=curation,
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

    def get_photo_stats(self) -> Dict[str, Any]:
        """Get photo pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intention_sum": 0.0, "quality_sum": 0.0, "story_sum": 0.0})
        for e in self._entries:
            by_type[e.photo_type]["count"] += 1
            by_type[e.photo_type]["intention_sum"] += e.intention
            by_type[e.photo_type]["quality_sum"] += e.quality
            by_type[e.photo_type]["story_sum"] += e.story

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intention": round(data["intention_sum"] / count, 2),
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_story": round(data["story_sum"] / count, 2),
            }

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_qual = sum(e.quality for e in high_int) / len(high_int)
            low_int_qual = sum(e.quality for e in low_int) / len(low_int)
            high_int_story = sum(e.story for e in high_int) / len(high_int)
            low_int_story = sum(e.story for e in low_int) / len(low_int)
        else:
            high_int_qual = 0
            low_int_qual = 0
            high_int_story = 0
            low_int_story = 0

        # Curation analysis
        high_cur = [e for e in self._entries if e.curation > 0.7]
        low_cur = [e for e in self._entries if e.curation < 0.4]
        if high_cur and low_cur:
            high_cur_pres = sum(e.preservation for e in high_cur) / len(high_cur)
            low_cur_pres = sum(e.preservation for e in low_cur) / len(low_cur)
        else:
            high_cur_pres = 0
            low_cur_pres = 0

        # Clutter risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_int = sum(e.intention for e in recent) / len(recent)
            recent_story = sum(e.story for e in recent) / len(recent)
            clutter_risk = recent_int < 0.3 and recent_story < 0.3
        else:
            clutter_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "intention_impact": {
                "high_intention_quality": round(high_int_qual, 2),
                "low_intention_quality": round(low_int_qual, 2),
                "high_intention_story": round(high_int_story, 2),
                "low_intention_story": round(low_int_story, 2),
            },
            "curation_effect": {
                "high_curation_preservation": round(high_cur_pres, 2),
                "low_curation_preservation": round(low_cur_pres, 2),
            },
            "clutter_risk": clutter_risk,
            "avg_intention": round(sum(e.intention for e in self._entries) / len(self._entries), 2),
            "avg_story": round(sum(e.story for e in self._entries) / len(self._entries), 2),
        }

    def get_photo_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get photo suggestion."""
        suggestions = [
            "Most people take photos to capture. But they end up hoarding. Thousands of images. None looked at. None remembered. The camera is not a memory device. It's a memory tool. And tools need intention.",
            "Before you take a photo, ask: why? What am I trying to remember? What story am I trying to tell? If you don't know, don't take it. The best photos come from questions, not reflexes.",
            "Delete ruthlessly. For every photo you keep, delete ten. Curation is the craft. The person who keeps everything remembers nothing. The person who keeps only what matters remembers everything.",
            "Print the important ones. A photo on a screen is data. A photo on a wall is memory. A photo in an album is legacy. The physical photo lives differently in your mind. Print it.",
            "Organize by story, not by date. The trip to the mountains. The first year of marriage. The garden's growth. Stories have meaning. Dates don't. Create albums that tell stories.",
            "Take fewer photos. Be present more. The person who photographs everything experiences nothing. Put the camera down. Look with your eyes. Feel with your body. Remember with your heart. Then, if it matters, take one photo.",
            "Notice light. The golden hour. The blue hour. The shadows. The reflections. Light is what makes a photo. Not the subject. Learn to see light. And you'll learn to see beauty.",
            "Capture the ordinary. Not just the extraordinary. Breakfast. The cat sleeping. Rain on the window. These are the photos you'll treasure. Because they're the ones that show what life actually was.",
            "Write captions. Not just dates. 'This was the day everything changed.' 'Her laugh at the surprise party.' 'The last time we were all together.' Words give photos meaning. And meaning gives photos life.",
            "The person who keeps photos with intention is not nostalgic. They're grateful. They understand that life is fleeting. That moments pass. And that the photo is a love letter to the past. Write it well."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One intentional photo. One deletion. One caption written. One moment truly seen. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A story album created. A batch curated. A print made. A memory preserved with care. Medium craft."
        else:
            capacity_note = "Good capacity. Deep visual legacy work. A systematic practice of intentional photography, curation, and preservation. You have the strength to hold time."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Photo memory keeping is not about taking pictures. It's about keeping memories. Most people confuse the two. They take thousands of photos. They store them in the cloud. They never look at them. And they wonder why they can't remember their life. The work of photo memory keeping is about intentionality. About taking fewer photos with more purpose. About curating rather than hoarding. About organizing by story rather than date. About printing the important ones. And about understanding that a photo is not just an image. It's a memory. A story. A moment of time held still. And the person who treats photos with care is not just preserving images. They're preserving their life."
        }

    def get_photo_score(self) -> int:
        """Calculate overall photo health (0-100)."""
        if not self._entries:
            return 25

        avg_int = sum(e.intention for e in self._entries) / len(self._entries)
        avg_qual = sum(e.quality for e in self._entries) / len(self._entries)
        avg_emo = sum(e.emotion for e in self._entries) / len(self._entries)
        avg_story = sum(e.story for e in self._entries) / len(self._entries)
        avg_pres = sum(e.preservation for e in self._entries) / len(self._entries)
        avg_cur = sum(e.curation for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_int = sum(e.intention for e in recent) / len(recent)
            recent_story = sum(e.story for e in recent) / len(recent)
        else:
            recent_int = 0
            recent_story = 0

        # Clutter penalty
        clut_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_int_30 = sum(e.intention for e in last_30) / len(last_30)
            recent_story_30 = sum(e.story for e in last_30) / len(last_30)
            if recent_int_30 < 0.3 and recent_story_30 < 0.3:
                clut_penalty = 15

        # Type variety
        unique_types = len(set(e.photo_type for e in self._entries))

        score = (avg_int * 25) + (avg_qual * 10) + (avg_emo * 10) + (avg_story * 20) + (avg_pres * 10) + (avg_cur * 15) + (recent_int * 5) + (recent_story * 5) + (unique_types * 2) - clut_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intention"] = round(sum(e.intention for e in self._entries) / len(self._entries), 2)
            self._stats["avg_story"] = round(sum(e.story for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_int = sum(e.intention for e in recent) / len(recent)
                recent_story = sum(e.story for e in recent) / len(recent)
                self._stats["clutter_risk"] = recent_int < 0.3 and recent_story < 0.3
            else:
                self._stats["clutter_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.photo_memory_keeper")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.photo_memory_keeper")

    def _log_entry(self, entry: PhotoEntry):
        try:
            with open(PHOTO_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "photo": entry.photo,
                    "photo_type": entry.photo_type,
                    "intention": entry.intention,
                    "story": entry.story,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.photo_memory_keeper")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pmk_instance: Optional[PhotoMemoryKeeper] = None
_pmk_lock = threading.Lock()


def get_photo_memory_keeper() -> PhotoMemoryKeeper:
    global _pmk_instance
    with _pmk_lock:
        if _pmk_instance is None:
            _pmk_instance = PhotoMemoryKeeper()
        return _pmk_instance
