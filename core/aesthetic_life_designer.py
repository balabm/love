"""
LOVE Aesthetic Life Designer — Beauty Intelligence (Modern AI Pattern)

Most people neglect beauty in daily life. This designer:

1. AESTHETIC TRACKING
   - Record aesthetic experiences and their characteristics
   - Track experience types (visual, auditory, tactile, culinary, natural, artistic)
   - Log beauty, meaning, and inspiration from aesthetic encounters

2. PATTERN ANALYSIS
   - Identify the user's aesthetic profile (sensitive, numb, selective, abundant)
   - Find aesthetic patterns that create vitality and meaning
   - Detect aesthetic deprivation and its consequences

3. AESTHETIC BUILDING
   - Suggest beauty experiences matched to current capacity and preferences
   - Provide frameworks for cultivating aesthetic awareness
   - Recommend creative and natural beauty sources

4. BEAUTY CULTIVATION
   - Track the correlation between aesthetic experience and wellbeing
   - Alert when life has become purely functional
   - Celebrate moments of genuine aesthetic awe

Architecture:
- record_experience(experience, type, beauty, meaning, inspiration): Log experience
- get_aesthetic_stats(): Get aesthetic pattern analysis
- get_aesthetic_suggestion(capacity, context): Get suggestion
- get_aesthetic_score(): Calculate overall aesthetic health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "aesthetic_life_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

AESTHETIC_LOG = DATA_DIR / "experiences.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AestheticEntry:
    """A tracked aesthetic experience."""
    entry_id: str = ""
    experience: str = ""  # what was experienced
    aesthetic_type: str = ""  # visual, auditory, tactile, culinary, natural, artistic
    beauty: float = 0.5  # 0-1
    meaning: float = 0.0  # 0-1
    inspiration: float = 0.0  # 0-1
    awe: float = 0.0  # 0-1
    novelty: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AestheticLifeDesigner:
    """
    Intelligent aesthetic life designer with beauty detection and awe cultivation.
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
            "avg_beauty": 0.0,
            "avg_inspiration": 0.0,
            "aesthetic_deprivation": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_experience(self, experience: str = "", aesthetic_type: str = "", beauty: float = 0.5, meaning: float = 0.0, inspiration: float = 0.0, awe: float = 0.0, novelty: float = 0.0, notes: str = "") -> AestheticEntry:
        """Record an aesthetic experience."""
        entry_id = f"aes_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = AestheticEntry(
            entry_id=entry_id,
            experience=experience or "unspecified",
            aesthetic_type=aesthetic_type or "visual",
            beauty=beauty,
            meaning=meaning,
            inspiration=inspiration,
            awe=awe,
            novelty=novelty,
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

    def get_aesthetic_stats(self) -> Dict[str, Any]:
        """Get aesthetic pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "beauty_sum": 0.0, "meaning_sum": 0.0, "inspiration_sum": 0.0})
        for e in self._entries:
            by_type[e.aesthetic_type]["count"] += 1
            by_type[e.aesthetic_type]["beauty_sum"] += e.beauty
            by_type[e.aesthetic_type]["meaning_sum"] += e.meaning
            by_type[e.aesthetic_type]["inspiration_sum"] += e.inspiration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_beauty": round(data["beauty_sum"] / count, 2),
                "avg_meaning": round(data["meaning_sum"] / count, 2),
                "avg_inspiration": round(data["inspiration_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_beauty"]) if type_stats else ("", {})

        # Beauty analysis
        high_beauty = [e for e in self._entries if e.beauty > 0.7]
        low_beauty = [e for e in self._entries if e.beauty < 0.4]
        if high_beauty and low_beauty:
            high_beauty_inspiration = sum(e.inspiration for e in high_beauty) / len(high_beauty)
            low_beauty_inspiration = sum(e.inspiration for e in low_beauty) / len(low_beauty)
            high_beauty_meaning = sum(e.meaning for e in high_beauty) / len(high_beauty)
            low_beauty_meaning = sum(e.meaning for e in low_beauty) / len(low_beauty)
        else:
            high_beauty_inspiration = 0
            low_beauty_inspiration = 0
            high_beauty_meaning = 0
            low_beauty_meaning = 0

        # Awe analysis
        high_awe = [e for e in self._entries if e.awe > 0.7]
        low_awe = [e for e in self._entries if e.awe < 0.4]
        if high_awe and low_awe:
            high_awe_inspiration = sum(e.inspiration for e in high_awe) / len(high_awe)
            low_awe_inspiration = sum(e.inspiration for e in low_awe) / len(low_awe)
        else:
            high_awe_inspiration = 0
            low_awe_inspiration = 0

        # Aesthetic deprivation detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_beauty = sum(e.beauty for e in recent) / len(recent)
            recent_inspiration = sum(e.inspiration for e in recent) / len(recent)
            aesthetic_deprivation = recent_beauty < 0.3 and recent_inspiration < 0.3
        else:
            aesthetic_deprivation = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "beauty_impact": {
                "high_beauty_inspiration": round(high_beauty_inspiration, 2),
                "low_beauty_inspiration": round(low_beauty_inspiration, 2),
                "high_beauty_meaning": round(high_beauty_meaning, 2),
                "low_beauty_meaning": round(low_beauty_meaning, 2),
            },
            "awe_effect": {
                "high_awe_inspiration": round(high_awe_inspiration, 2),
                "low_awe_inspiration": round(low_awe_inspiration, 2),
            },
            "aesthetic_deprivation": aesthetic_deprivation,
            "avg_beauty": round(sum(e.beauty for e in self._entries) / len(self._entries), 2),
            "avg_inspiration": round(sum(e.inspiration for e in self._entries) / len(self._entries), 2),
        }

    def get_aesthetic_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get aesthetic suggestion."""
        suggestions = [
            "Look up. The sky. The architecture. The trees. Most people walk through life looking at their feet or their phones. Beauty is above you. Around you. Everywhere. Look.",
            "Listen to music that moves you. Not background noise. Real listening. Close your eyes. Let it in. Music is beauty you can feel.",
            "Cook something beautiful. Not just functional. Arrange the plate. Use colors. Food is the most accessible art form. Make it beautiful.",
            "Go outside. Nature is the original aesthetic experience. A sunset. A flower. A stream. Nature doesn't try to be beautiful. It just is. And it's free.",
            "Visit a museum. A gallery. A garden. Art is humanity's attempt to capture beauty. Go be in its presence. You don't need to understand it. You need to feel it.",
            "Dress beautifully. Not expensively. Beautifully. Color. Texture. Fit. Your body is the frame for your presence in the world. Frame it well.",
            "Create something. Draw. Write. Build. Arrange flowers. The act of creation is an aesthetic experience. And you don't need to be good at it. You just need to do it.",
            "Notice one beautiful thing every day. Train your eye. The pattern of rain on a window. The way light hits a wall. The smile of a stranger. Beauty is a practice.",
            "Aesthetic deprivation is real. People who live without beauty become functional but hollow. Don't let that be you. Seek beauty deliberately."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One beautiful thing. One sunset. One song. One flower. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A creative activity. A nature walk. A visit to something beautiful. Medium investment in aesthetics."
        else:
            capacity_note = "Good capacity. A major aesthetic project. A creative work. A transformation of your environment. You have the energy for real beauty creation."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Beauty is not optional. It's not luxury. It's not decoration. Beauty is essential to human wellbeing. People who live without aesthetic experience suffer in ways they often can't name. They become functional. Efficient. Productive. And empty. Beauty awakens the soul. It reminds us that life is not just a series of problems to solve. It's a gift to receive. The sunset doesn't care about your to-do list. The symphony doesn't care about your productivity. They exist for their own sake. And in their existence, they teach us that not everything needs to be useful. Some things just need to be beautiful. Seek beauty. Create beauty. Be beauty. It's not extra. It's the point.",
        }

    def get_aesthetic_score(self) -> int:
        """Calculate overall aesthetic health (0-100)."""
        if not self._entries:
            return 25

        avg_beauty = sum(e.beauty for e in self._entries) / len(self._entries)
        avg_meaning = sum(e.meaning for e in self._entries) / len(self._entries)
        avg_inspiration = sum(e.inspiration for e in self._entries) / len(self._entries)
        avg_awe = sum(e.awe for e in self._entries) / len(self._entries)
        avg_novelty = sum(e.novelty for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_beauty = sum(e.beauty for e in recent) / len(recent)
            recent_inspiration = sum(e.inspiration for e in recent) / len(recent)
        else:
            recent_beauty = 0
            recent_inspiration = 0

        # Aesthetic deprivation penalty
        dep_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 3:
            dep_penalty = 15

        # Type variety
        unique_types = len(set(e.aesthetic_type for e in self._entries))

        score = (avg_beauty * 30) + (avg_meaning * 15) + (avg_inspiration * 20) + (avg_awe * 15) + (avg_novelty * 10) + (recent_beauty * 5) + (recent_inspiration * 5) + (unique_types * 2) - dep_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_beauty"] = round(sum(e.beauty for e in self._entries) / len(self._entries), 2)
            self._stats["avg_inspiration"] = round(sum(e.inspiration for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_beauty = sum(e.beauty for e in recent) / len(recent)
                recent_inspiration = sum(e.inspiration for e in recent) / len(recent)
                self._stats["aesthetic_deprivation"] = recent_beauty < 0.3 and recent_inspiration < 0.3
            else:
                self._stats["aesthetic_deprivation"] = True

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

    def _log_entry(self, entry: AestheticEntry):
        try:
            with open(AESTHETIC_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "experience": entry.experience,
                    "aesthetic_type": entry.aesthetic_type,
                    "beauty": entry.beauty,
                    "inspiration": entry.inspiration,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ald_instance: Optional[AestheticLifeDesigner] = None
_ald_lock = threading.Lock()


def get_aesthetic_life_designer() -> AestheticLifeDesigner:
    global _ald_instance
    with _ald_lock:
        if _ald_instance is None:
            _ald_instance = AestheticLifeDesigner()
        return _ald_instance
