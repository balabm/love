"""
LOVE Pet Loss Support — Grief Intelligence (Modern AI Pattern)

Most people dismiss pet grief. This support:

1. GRIEF TRACKING
   - Record pet loss moments and their characteristics
   - Track grief types (anticipatory, acute, anniversary, regret, guilt, relief)
   - Log intensity, processing, support, and integration of grief

2. PATTERN ANALYSIS
   - Identify the user's grief profile (dismissed, suppressed, developing, integrated)
   - Find grief patterns that heal vs prolong suffering
   - Detect chronic disenfranchisement and its costs

3. GRIEF SUPPORT
   - Suggest practices for processing pet loss
   - Provide frameworks for honoring the bond
   - Recommend practices for memorial and meaning-making

4. HEALING CULTIVATION
   - Track the correlation between grief processing and recovery
   - Alert when dismissal is preventing healing
   - Celebrate moments of genuine, loving remembrance

Architecture:
- record_grief(moment, type, intensity, processing, support, integration): Log grief
- get_grief_stats(): Get grief pattern analysis
- get_grief_suggestion(capacity, context): Get suggestion
- get_grief_score(): Calculate overall grief health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "pet_loss_support"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GRIEF_LOG = DATA_DIR / "griefs.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class GriefEntry:
    """A tracked pet grief moment."""
    entry_id: str = ""
    moment: str = ""  # what happened
    grief_type: str = ""  # anticipatory, acute, anniversary, regret, guilt, relief
    intensity: float = 0.0  # 0-1
    processing: float = 0.0  # 0-1
    support: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1
    memorial: float = 0.0  # 0-1 did you honor them?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PetLossSupport:
    """
    Intelligent pet loss support with dismissal detection and healing cultivation.
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
            "avg_processing": 0.0,
            "avg_integration": 0.0,
            "dismissal_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_grief(self, moment: str = "", grief_type: str = "", intensity: float = 0.0, processing: float = 0.0, support: float = 0.0, integration: float = 0.0, memorial: float = 0.0, notes: str = "") -> GriefEntry:
        """Record a pet grief moment."""
        entry_id = f"gft_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = GriefEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            grief_type=grief_type or "acute",
            intensity=intensity,
            processing=processing,
            support=support,
            integration=integration,
            memorial=memorial,
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

    def get_grief_stats(self) -> Dict[str, Any]:
        """Get grief pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "processing_sum": 0.0, "integration_sum": 0.0})
        for e in self._entries:
            by_type[e.grief_type]["count"] += 1
            by_type[e.grief_type]["intensity_sum"] += e.intensity
            by_type[e.grief_type]["processing_sum"] += e.processing
            by_type[e.grief_type]["integration_sum"] += e.integration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_processing": round(data["processing_sum"] / count, 2),
                "avg_integration": round(data["integration_sum"] / count, 2),
            }

        # Processing analysis
        high_proc = [e for e in self._entries if e.processing > 0.7]
        low_proc = [e for e in self._entries if e.processing < 0.4]
        if high_proc and low_proc:
            high_proc_int = sum(e.integration for e in high_proc) / len(high_proc)
            low_proc_int = sum(e.integration for e in low_proc) / len(low_proc)
            high_proc_sup = sum(e.support for e in high_proc) / len(high_proc)
            low_proc_sup = sum(e.support for e in low_proc) / len(low_proc)
        else:
            high_proc_int = 0
            low_proc_int = 0
            high_proc_sup = 0
            low_proc_sup = 0

        # Memorial analysis
        high_mem = [e for e in self._entries if e.memorial > 0.7]
        low_mem = [e for e in self._entries if e.memorial < 0.4]
        if high_mem and low_mem:
            high_mem_int = sum(e.integration for e in high_mem) / len(high_mem)
            low_mem_int = sum(e.integration for e in low_mem) / len(low_mem)
        else:
            high_mem_int = 0
            low_mem_int = 0

        # Dismissal risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_proc = sum(e.processing for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            dismissal_risk = recent_proc < 0.3 and recent_int < 0.3
        else:
            dismissal_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "processing_impact": {
                "high_processing_integration": round(high_proc_int, 2),
                "low_processing_integration": round(low_proc_int, 2),
                "high_processing_support": round(high_proc_sup, 2),
                "low_processing_support": round(low_proc_sup, 2),
            },
            "memorial_effect": {
                "high_memorial_integration": round(high_mem_int, 2),
                "low_memorial_integration": round(low_mem_int, 2),
            },
            "dismissal_risk": dismissal_risk,
            "avg_processing": round(sum(e.processing for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
        }

    def get_grief_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get grief suggestion."""
        suggestions = [
            "Your grief is real. Your pet was not 'just an animal.' They were a family member. A companion. A source of unconditional love. The world may not understand. But your heart does. Honor it.",
            "Cry. Loudly. Quietly. Alone. With someone. However you need to. The person who says 'it was just a pet' has never known the love of an animal. Their opinion is irrelevant. Your grief is valid.",
            "Create a memorial. A photo album. A planted tree. A donation in their name. A ritual of remembrance. The dead are not gone when they're remembered. They're gone when they're forgotten. Remember them.",
            "Talk about them. Say their name. Tell their stories. Share what you loved. What you miss. What they taught you. Grief that is spoken heals. Grief that is silenced festers. Speak.",
            "Don't rush to replace them. A new pet is not a replacement. They're a new chapter. Grieve the old one first. Fully. Then, when you're ready, open to a new one. Not as replacement. As continuation.",
            "Notice the guilt. 'I should have...' 'If only I had...' This is normal. And it's not true. You loved them. You did your best. They knew it. Forgive yourself. They already did.",
            "Feel the emptiness. The silence where there was sound. The stillness where there was movement. This is the shape of their absence. It hurts because they mattered. That's not a flaw. That's love.",
            "Write a letter to them. Tell them what you wish you'd said. What you're grateful for. What you miss. What you learned. Letters to the dead are letters to the living. They heal the writer.",
            "Find your people. Others who understand. Pet loss groups. Online communities. Friends who get it. Grief is heavy. Don't carry it alone. Share the weight. Share the love. Share the memory.",
            "The love doesn't end. It changes form. From daily presence to cherished memory. From physical touch to emotional imprint. They're in you now. Forever. That's not less. That's different. And it's enough."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One tear shed. One memory spoken. One moment of acknowledging the loss. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A memorial created. A letter written. A story shared. A ritual of remembrance. Medium healing."
        else:
            capacity_note = "Good capacity. Deep grief work. A systematic practice of processing, honoring, and integrating the loss of a beloved companion. You have the strength to carry their memory with love."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Pet loss is real grief. And it's often disenfranchised grief. The world tells you to get over it. To replace the pet. To move on. But the bond between human and animal is profound. It's ancient. It's biological. And when it's broken, the pain is real. The work of pet loss support is about validating that grief. About giving it space. About helping you process the loss of a being who loved you unconditionally. Who was always there. Who never judged. Who accepted you completely. And about understanding that grieving this loss is not weakness. It's the natural response to losing a source of pure love. The healing comes not from forgetting. But from remembering. From honoring. From integrating the love into who you are. And from understanding that the best way to honor a pet who loved you is to become someone who loves as freely as they did."
        }

    def get_grief_score(self) -> int:
        """Calculate overall grief health (0-100)."""
        if not self._entries:
            return 25

        avg_proc = sum(e.processing for e in self._entries) / len(self._entries)
        avg_sup = sum(e.support for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_mem = sum(e.memorial for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_proc = sum(e.processing for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
        else:
            recent_proc = 0
            recent_int = 0

        # Dismissal penalty
        dis_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_proc_30 = sum(e.processing for e in last_30) / len(last_30)
            recent_int_30 = sum(e.integration for e in last_30) / len(last_30)
            if recent_proc_30 < 0.3 and recent_int_30 < 0.3:
                dis_penalty = 15

        # Type variety
        unique_types = len(set(e.grief_type for e in self._entries))

        score = (avg_proc * 25) + (avg_sup * 15) + (avg_int * 25) + (avg_mem * 10) + (recent_proc * 5) + (recent_int * 5) + (unique_types * 2) - dis_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_processing"] = round(sum(e.processing for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integration"] = round(sum(e.integration for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_proc = sum(e.processing for e in recent) / len(recent)
                recent_int = sum(e.integration for e in recent) / len(recent)
                self._stats["dismissal_risk"] = recent_proc < 0.3 and recent_int < 0.3
            else:
                self._stats["dismissal_risk"] = False

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

    def _log_entry(self, entry: GriefEntry):
        try:
            with open(GRIEF_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "grief_type": entry.grief_type,
                    "processing": entry.processing,
                    "integration": entry.integration,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pls_instance: Optional[PetLossSupport] = None
_pls_lock = threading.Lock()


def get_pet_loss_support() -> PetLossSupport:
    global _pls_instance
    with _pls_lock:
        if _pls_instance is None:
            _pls_instance = PetLossSupport()
        return _pls_instance
