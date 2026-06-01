"""
LOVE Garden Therapy Coach — Horticultural Intelligence (Modern AI Pattern)

Most people garden for aesthetics. This coach:

1. GARDEN TRACKING
   - Record garden therapy moments and their characteristics
   - Track therapy types (planting, weeding, watering, harvesting, observing, resting)
   - Log presence, growth, patience, and healing of gardening

2. PATTERN ANALYSIS
   - Identify the user's garden profile (neglectful, chore, developing, therapeutic)
   - Find garden patterns that create healing vs stress
   - Detect chronic garden neglect and its costs

3. THERAPY BUILDING
   - Suggest practices for using gardening as therapy
   - Provide frameworks for mindful garden engagement
   - Recommend practices for growing as healing

4. HORTICULTURAL WELLNESS CULTIVATION
   - Track the correlation between gardening and mental health
   - Alert when the garden is becoming a source of pressure
   - Celebrate moments of genuine garden peace

Architecture:
- record_garden(activity, type, presence, growth, patience, healing): Log garden
- get_garden_stats(): Get garden pattern analysis
- get_garden_suggestion(capacity, context): Get suggestion
- get_garden_score(): Calculate overall garden health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "garden_therapy_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GARDEN_LOG = DATA_DIR / "gardens.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class GardenEntry:
    """A tracked garden therapy moment."""
    entry_id: str = ""
    activity: str = ""  # what was done
    garden_type: str = ""  # planting, weeding, watering, harvesting, observing, resting
    presence: float = 0.0  # 0-1
    growth: float = 0.0  # 0-1
    patience: float = 0.0  # 0-1
    healing: float = 0.0  # 0-1
    sensory: float = 0.0  # 0-1 sensory engagement?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class GardenTherapyCoach:
    """
    Intelligent garden therapy coach with neglect detection and horticultural wellness cultivation.
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
            "avg_presence": 0.0,
            "avg_healing": 0.0,
            "neglect_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_garden(self, activity: str = "", garden_type: str = "", presence: float = 0.0, growth: float = 0.0, patience: float = 0.0, healing: float = 0.0, sensory: float = 0.0, notes: str = "") -> GardenEntry:
        """Record a garden therapy moment."""
        entry_id = f"grd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = GardenEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            garden_type=garden_type or "observing",
            presence=presence,
            growth=growth,
            patience=patience,
            healing=healing,
            sensory=sensory,
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

    def get_garden_stats(self) -> Dict[str, Any]:
        """Get garden pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "presence_sum": 0.0, "growth_sum": 0.0, "healing_sum": 0.0})
        for e in self._entries:
            by_type[e.garden_type]["count"] += 1
            by_type[e.garden_type]["presence_sum"] += e.presence
            by_type[e.garden_type]["growth_sum"] += e.growth
            by_type[e.garden_type]["healing_sum"] += e.healing

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_presence": round(data["presence_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_healing": round(data["healing_sum"] / count, 2),
            }

        # Presence analysis
        high_pres = [e for e in self._entries if e.presence > 0.7]
        low_pres = [e for e in self._entries if e.presence < 0.4]
        if high_pres and low_pres:
            high_pres_heal = sum(e.healing for e in high_pres) / len(high_pres)
            low_pres_heal = sum(e.healing for e in low_pres) / len(low_pres)
            high_pres_grow = sum(e.growth for e in high_pres) / len(high_pres)
            low_pres_grow = sum(e.growth for e in low_pres) / len(low_pres)
        else:
            high_pres_heal = 0
            low_pres_heal = 0
            high_pres_grow = 0
            low_pres_grow = 0

        # Patience analysis
        high_pat = [e for e in self._entries if e.patience > 0.7]
        low_pat = [e for e in self._entries if e.patience < 0.4]
        if high_pat and low_pat:
            high_pat_heal = sum(e.healing for e in high_pat) / len(high_pat)
            low_pat_heal = sum(e.healing for e in low_pat) / len(low_pat)
        else:
            high_pat_heal = 0
            low_pat_heal = 0

        # Neglect risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_pres = sum(e.presence for e in recent) / len(recent)
            recent_heal = sum(e.healing for e in recent) / len(recent)
            neglect_risk = recent_pres < 0.3 and recent_heal < 0.3
        else:
            neglect_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "presence_impact": {
                "high_presence_healing": round(high_pres_heal, 2),
                "low_presence_healing": round(low_pres_heal, 2),
                "high_presence_growth": round(high_pres_grow, 2),
                "low_presence_growth": round(low_pres_grow, 2),
            },
            "patience_effect": {
                "high_patience_healing": round(high_pat_heal, 2),
                "low_patience_healing": round(low_pat_heal, 2),
            },
            "neglect_risk": neglect_risk,
            "avg_presence": round(sum(e.presence for e in self._entries) / len(self._entries), 2),
            "avg_healing": round(sum(e.healing for e in self._entries) / len(self._entries), 2),
        }

    def get_garden_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get garden suggestion."""
        suggestions = [
            "The garden doesn't care about your schedule. It grows at its own pace. And that's the therapy. The garden teaches patience. It teaches that some things cannot be rushed. That growth takes time. That presence is the fertilizer.",
            "Touch the soil. Feel it. Smell it. The earth is alive. And touching it connects you to life itself. Studies show soil bacteria reduce anxiety. The garden is not decoration. It's medicine.",
            "Plant something from seed. Watch the whole journey. From nothing to something. From potential to reality. This is hope made visible. And hope is the antidote to despair.",
            "Weed mindfully. Not as a chore. As meditation. Each weed removed is a thought clarified. Each space cleared is a mind cleared. The garden is a mirror. Clean the mirror.",
            "Water with attention. Notice how the soil drinks. How the leaves respond. How the color changes. Water is life. And giving it is an act of care. For them. For you.",
            "Harvest with gratitude. Even one leaf. One herb. One flower. Thank the plant. Thank the soil. Thank the sun. Thank the rain. Gratitude is the harvest of the soul.",
            "Sit in the garden. Don't do anything. Just be. Let the birds come. Let the insects buzz. Let the wind move the leaves. You're not in charge here. And that's the relief.",
            "Notice the seasons. The garden changes. It dies back. It returns. It flowers. It fruits. It rests. These are not failures. They're cycles. And you have cycles too. Learn from them.",
            "Start small. A pot. A windowsill. A balcony. You don't need acres. You need engagement. One plant cared for is better than a garden neglected. Scale to your capacity.",
            "The person who gardens is not escaping reality. They're engaging with it more deeply. Dirt under nails. Sun on skin. Wind in hair. These are not luxuries. They're necessities. And the garden provides them."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One plant watered. One weed pulled. One minute in the garden. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A planting session. A mindful harvest. A rest in the garden. Medium therapy."
        else:
            capacity_note = "Good capacity. Deep horticultural therapy. A systematic practice of growing, tending, and being with plants. You have the strength to cultivate peace."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Garden therapy is not about having a beautiful garden. It's about having a relationship with the living world. Most people see gardening as a chore. As maintenance. As something to outsource. But the garden is one of the oldest forms of therapy known to humanity. The simple acts of planting, tending, watering, and harvesting engage the body, calm the mind, and nourish the soul. The garden teaches patience. It teaches that growth takes time. It teaches that death is part of life. And it teaches that beauty emerges from care. The work of garden therapy coaching is about helping you use the garden as a therapeutic practice. About being present with plants. About finding peace in dirt. About understanding that the garden doesn't judge you. It just grows. And in that simple, wordless relationship, healing happens."
        }

    def get_garden_score(self) -> int:
        """Calculate overall garden health (0-100)."""
        if not self._entries:
            return 25

        avg_pres = sum(e.presence for e in self._entries) / len(self._entries)
        avg_grow = sum(e.growth for e in self._entries) / len(self._entries)
        avg_pat = sum(e.patience for e in self._entries) / len(self._entries)
        avg_heal = sum(e.healing for e in self._entries) / len(self._entries)
        avg_sens = sum(e.sensory for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_pres = sum(e.presence for e in recent) / len(recent)
            recent_heal = sum(e.healing for e in recent) / len(recent)
        else:
            recent_pres = 0
            recent_heal = 0

        # Neglect penalty
        neg_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_pres_30 = sum(e.presence for e in last_30) / len(last_30)
            recent_heal_30 = sum(e.healing for e in last_30) / len(last_30)
            if recent_pres_30 < 0.3 and recent_heal_30 < 0.3:
                neg_penalty = 15

        # Type variety
        unique_types = len(set(e.garden_type for e in self._entries))

        score = (avg_pres * 25) + (avg_grow * 15) + (avg_pat * 10) + (avg_heal * 20) + (avg_sens * 10) + (recent_pres * 5) + (recent_heal * 5) + (unique_types * 2) - neg_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_presence"] = round(sum(e.presence for e in self._entries) / len(self._entries), 2)
            self._stats["avg_healing"] = round(sum(e.healing for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_pres = sum(e.presence for e in recent) / len(recent)
                recent_heal = sum(e.healing for e in recent) / len(recent)
                self._stats["neglect_risk"] = recent_pres < 0.3 and recent_heal < 0.3
            else:
                self._stats["neglect_risk"] = False

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

    def _log_entry(self, entry: GardenEntry):
        try:
            with open(GARDEN_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "garden_type": entry.garden_type,
                    "presence": entry.presence,
                    "healing": entry.healing,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gtc_instance: Optional[GardenTherapyCoach] = None
_gtc_lock = threading.Lock()


def get_garden_therapy_coach() -> GardenTherapyCoach:
    global _gtc_instance
    with _gtc_lock:
        if _gtc_instance is None:
            _gtc_instance = GardenTherapyCoach()
        return _gtc_instance
