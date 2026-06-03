"""
LOVE Memory Curation Coach — Curatorial Intelligence (Modern AI Pattern)

Most people accumulate without curating. This coach:

1. CURATION TRACKING
   - Record memory curation moments and their characteristics
   - Track curation types (review, select, delete, organize, archive, share)
   - Log intention, selectivity, care, meaning, and preservation of curation

2. PATTERN ANALYSIS
   - Identify the user's curation profile (hoarding, indifferent, developing, curatorial)
   - Find curation patterns that create meaning vs clutter
   - Detect chronic accumulation without review and its costs

3. CURATION BUILDING
   - Suggest practices for reviewing and curating memories
   - Provide frameworks for keeping, deleting, and organizing
   - Recommend practices for meaningful preservation

4. CURATORIAL MASTERY CULTIVATION
   - Track the correlation between curation and memory quality
   - Alert when hoarding is replacing meaning-making
   - Celebrate moments of genuine curatorial wisdom

Architecture:
- record_curation(moment, type, intention, selectivity, care, meaning, preservation): Log curation
- get_curation_stats(): Get curation pattern analysis
- get_curation_suggestion(capacity, context): Get suggestion
- get_curation_score(): Calculate overall curation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "memory_curation_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CURATION_LOG = DATA_DIR / "curations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CurationEntry:
    """A tracked memory curation moment."""
    entry_id: str = ""
    moment: str = ""  # what was curated
    curation_type: str = ""  # review, select, delete, organize, archive, share
    intention: float = 0.0  # 0-1
    selectivity: float = 0.0  # 0-1
    care: float = 0.0  # 0-1
    meaning: float = 0.0  # 0-1
    preservation: float = 0.0  # 0-1
    ritual: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MemoryCurationCoach:
    """
    Intelligent memory curation coach with hoarding detection and curatorial mastery cultivation.
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
            "avg_selectivity": 0.0,
            "hoarding_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_curation(self, moment: str = "", curation_type: str = "", intention: float = 0.0, selectivity: float = 0.0, care: float = 0.0, meaning: float = 0.0, preservation: float = 0.0, ritual: float = 0.0, notes: str = "") -> CurationEntry:
        """Record a memory curation moment."""
        entry_id = f"cur_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CurationEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            curation_type=curation_type or "review",
            intention=intention,
            selectivity=selectivity,
            care=care,
            meaning=meaning,
            preservation=preservation,
            ritual=ritual,
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

    def get_curation_stats(self) -> Dict[str, Any]:
        """Get curation pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intention_sum": 0.0, "selectivity_sum": 0.0, "care_sum": 0.0})
        for e in self._entries:
            by_type[e.curation_type]["count"] += 1
            by_type[e.curation_type]["intention_sum"] += e.intention
            by_type[e.curation_type]["selectivity_sum"] += e.selectivity
            by_type[e.curation_type]["care_sum"] += e.care

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intention": round(data["intention_sum"] / count, 2),
                "avg_selectivity": round(data["selectivity_sum"] / count, 2),
                "avg_care": round(data["care_sum"] / count, 2),
            }

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_mean = sum(e.meaning for e in high_int) / len(high_int)
            low_int_mean = sum(e.meaning for e in low_int) / len(low_int)
            high_int_pres = sum(e.preservation for e in high_int) / len(high_int)
            low_int_pres = sum(e.preservation for e in low_int) / len(low_int)
        else:
            high_int_mean = 0
            low_int_mean = 0
            high_int_pres = 0
            low_int_pres = 0

        # Selectivity analysis
        high_sel = [e for e in self._entries if e.selectivity > 0.7]
        low_sel = [e for e in self._entries if e.selectivity < 0.4]
        if high_sel and low_sel:
            high_sel_mean = sum(e.meaning for e in high_sel) / len(high_sel)
            low_sel_mean = sum(e.meaning for e in low_sel) / len(low_sel)
        else:
            high_sel_mean = 0
            low_sel_mean = 0

        # Hoarding risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_sel = sum(e.selectivity for e in recent) / len(recent)
            recent_mean = sum(e.meaning for e in recent) / len(recent)
            hoarding_risk = recent_sel < 0.3 and recent_mean < 0.3
        else:
            hoarding_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "intention_impact": {
                "high_intention_meaning": round(high_int_mean, 2),
                "low_intention_meaning": round(low_int_mean, 2),
                "high_intention_preservation": round(high_int_pres, 2),
                "low_intention_preservation": round(low_int_pres, 2),
            },
            "selectivity_effect": {
                "high_selectivity_meaning": round(high_sel_mean, 2),
                "low_selectivity_meaning": round(low_sel_mean, 2),
            },
            "hoarding_risk": hoarding_risk,
            "avg_intention": round(sum(e.intention for e in self._entries) / len(self._entries), 2),
            "avg_selectivity": round(sum(e.selectivity for e in self._entries) / len(self._entries), 2),
        }

    def get_curation_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get curation suggestion."""
        suggestions = [
            "Most people hoard memories. They keep everything. Every photo. Every message. Every document. Every note. And they end up with a life that is full of stuff and empty of meaning. Curation is not deletion. It's love.",
            "Review regularly. Not just when you're out of storage. Every month. Every season. Look at what you've accumulated. What still matters? What has faded? What was important then but isn't now? Be honest.",
            "Delete without regret. The photo of a meal you don't remember. The document you'll never read. The message from someone who's gone. They served their purpose. Let them go. Gratitude and goodbye.",
            "Organize by meaning. Not by date. Not by type. By meaning. The people you love. The places that matter. The moments that changed you. The experiences that formed you. Meaning is the only organizing principle that lasts.",
            "Archive with care. The things you keep deserve respect. Proper folders. Proper names. Proper backup. They're not data. They're your life. Treat them like the treasures they are.",
            "Share the living. Not everything is private. Some memories want to be shared. The people who were there. The people who care. The people who would love to see. Sharing is not broadcasting. It's community.",
            "Make rituals of review. A Sunday evening. A birthday. A new year. Sit with your memories. Let them wash over you. Laugh. Cry. Remember who you were. Remember who you've become. This is the practice.",
            "Keep less. Remember more. The paradox of memory is that the more you keep, the less you remember. Because you never look. Because you never sit with it. Because it's buried under accumulation. Keep less. Sit with it. Remember more.",
            "Create artifacts. Not just files. A printed photo album. A written journal. A recorded voice memo. Physical and intentional. The artifact is a commitment. It says 'this mattered enough to make real.'",
            "The person who curates their memories is not nostalgic. They're grateful. They're intentional. They understand that life is a river and that the curation is the act of cupping water. You can't keep the river. But you can keep enough to remember it was beautiful."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One folder reviewed. One deletion made. One memory truly seen. One artifact created. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A batch curated. An album organized. A ritual established. A sharing made with care. Medium curation."
        else:
            capacity_note = "Good capacity. Deep curatorial work. A systematic practice of review, selection, organization, and meaningful preservation. You have the strength to hold what matters."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Memory curation is not about keeping everything. It's about keeping what matters. Most people confuse storage with preservation. They keep thousands of photos, hundreds of documents, decades of messages. And they never look at any of it. The work of memory curation coaching is about understanding that memory is not a function of quantity. It's a function of quality. Of attention. Of meaning. Of care. It's about reviewing regularly. Deleting without regret. Organizing by meaning. Archiving with care. Sharing with community. And understanding that the person who curates their memories well is not just organized. They're grateful. They're intentional. They're someone who understands that life is fleeting. And that the curation is the act of saying 'this mattered.'"
        }

    def get_curation_score(self) -> int:
        """Calculate overall curation health (0-100)."""
        if not self._entries:
            return 25

        avg_int = sum(e.intention for e in self._entries) / len(self._entries)
        avg_sel = sum(e.selectivity for e in self._entries) / len(self._entries)
        avg_care = sum(e.care for e in self._entries) / len(self._entries)
        avg_mean = sum(e.meaning for e in self._entries) / len(self._entries)
        avg_pres = sum(e.preservation for e in self._entries) / len(self._entries)
        avg_rit = sum(e.ritual for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_sel = sum(e.selectivity for e in recent) / len(recent)
            recent_mean = sum(e.meaning for e in recent) / len(recent)
        else:
            recent_sel = 0
            recent_mean = 0

        # Hoarding penalty
        hoard_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_sel_30 = sum(e.selectivity for e in last_30) / len(last_30)
            recent_mean_30 = sum(e.meaning for e in last_30) / len(last_30)
            if recent_sel_30 < 0.3 and recent_mean_30 < 0.3:
                hoard_penalty = 15

        # Type variety
        unique_types = len(set(e.curation_type for e in self._entries))

        score = (avg_int * 20) + (avg_sel * 20) + (avg_care * 10) + (avg_mean * 20) + (avg_pres * 10) + (avg_rit * 10) + (recent_sel * 5) + (recent_mean * 5) + (unique_types * 2) - hoard_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intention"] = round(sum(e.intention for e in self._entries) / len(self._entries), 2)
            self._stats["avg_selectivity"] = round(sum(e.selectivity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_sel = sum(e.selectivity for e in recent) / len(recent)
                recent_mean = sum(e.meaning for e in recent) / len(recent)
                self._stats["hoarding_risk"] = recent_sel < 0.3 and recent_mean < 0.3
            else:
                self._stats["hoarding_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.memory_curation_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.memory_curation_coach")

    def _log_entry(self, entry: CurationEntry):
        try:
            with open(CURATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "curation_type": entry.curation_type,
                    "intention": entry.intention,
                    "selectivity": entry.selectivity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.memory_curation_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mcc_instance: Optional[MemoryCurationCoach] = None
_mcc_lock = threading.Lock()


def get_memory_curation_coach() -> MemoryCurationCoach:
    global _mcc_instance
    with _mcc_lock:
        if _mcc_instance is None:
            _mcc_instance = MemoryCurationCoach()
        return _mcc_instance
