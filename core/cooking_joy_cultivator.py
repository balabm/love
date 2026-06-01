"""
LOVE Cooking Joy Cultivator — Culinary Intelligence (Modern AI Pattern)

Most people cook out of obligation. This cultivator:

1. COOKING TRACKING
   - Record cooking moments and their characteristics
   - Track cooking types (simple, elaborate, experimental, traditional, social, solo)
   - Log joy, creativity, skill, and nourishment of cooking

2. PATTERN ANALYSIS
   - Identify the user's cooking profile (avoidant, reluctant, developing, joyful)
   - Find cooking patterns that create pleasure vs dread
   - Detect chronic cooking avoidance and its costs

3. JOY BUILDING
   - Suggest practices for finding pleasure in cooking
   - Provide frameworks for kitchen creativity
   - Recommend practices for cooking as self-expression

4. CULINARY FULFILLMENT CULTIVATION
   - Track the correlation between cooking joy and life satisfaction
   - Alert when avoidance is becoming the default
   - Celebrate moments of genuine kitchen delight

Architecture:
- record_cooking(dish, type, joy, creativity, skill, nourishment): Log cooking
- get_cooking_stats(): Get cooking pattern analysis
- get_cooking_suggestion(capacity, context): Get suggestion
- get_cooking_score(): Calculate overall cooking health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "cooking_joy_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COOKING_LOG = DATA_DIR / "cookings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CookingEntry:
    """A tracked cooking moment."""
    entry_id: str = ""
    dish: str = ""  # what was cooked
    cooking_type: str = ""  # simple, elaborate, experimental, traditional, social, solo
    joy: float = 0.0  # 0-1
    creativity: float = 0.0  # 0-1
    skill: float = 0.0  # 0-1
    nourishment: float = 0.0  # 0-1
    sharing: float = 0.0  # 0-1 did you share?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CookingJoyCultivator:
    """
    Intelligent cooking joy cultivator with avoidance detection and culinary fulfillment cultivation.
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
            "avg_nourishment": 0.0,
            "avoidance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_cooking(self, dish: str = "", cooking_type: str = "", joy: float = 0.0, creativity: float = 0.0, skill: float = 0.0, nourishment: float = 0.0, sharing: float = 0.0, notes: str = "") -> CookingEntry:
        """Record a cooking moment."""
        entry_id = f"cook_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CookingEntry(
            entry_id=entry_id,
            dish=dish or "unspecified",
            cooking_type=cooking_type or "simple",
            joy=joy,
            creativity=creativity,
            skill=skill,
            nourishment=nourishment,
            sharing=sharing,
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

    def get_cooking_stats(self) -> Dict[str, Any]:
        """Get cooking pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "joy_sum": 0.0, "creativity_sum": 0.0, "nourishment_sum": 0.0})
        for e in self._entries:
            by_type[e.cooking_type]["count"] += 1
            by_type[e.cooking_type]["joy_sum"] += e.joy
            by_type[e.cooking_type]["creativity_sum"] += e.creativity
            by_type[e.cooking_type]["nourishment_sum"] += e.nourishment

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_creativity": round(data["creativity_sum"] / count, 2),
                "avg_nourishment": round(data["nourishment_sum"] / count, 2),
            }

        # Joy analysis
        high_joy = [e for e in self._entries if e.joy > 0.7]
        low_joy = [e for e in self._entries if e.joy < 0.4]
        if high_joy and low_joy:
            high_joy_nour = sum(e.nourishment for e in high_joy) / len(high_joy)
            low_joy_nour = sum(e.nourishment for e in low_joy) / len(low_joy)
            high_joy_cre = sum(e.creativity for e in high_joy) / len(high_joy)
            low_joy_cre = sum(e.creativity for e in low_joy) / len(low_joy)
        else:
            high_joy_nour = 0
            low_joy_nour = 0
            high_joy_cre = 0
            low_joy_cre = 0

        # Sharing analysis
        high_share = [e for e in self._entries if e.sharing > 0.7]
        low_share = [e for e in self._entries if e.sharing < 0.4]
        if high_share and low_share:
            high_share_joy = sum(e.joy for e in high_share) / len(high_share)
            low_share_joy = sum(e.joy for e in low_share) / len(low_share)
        else:
            high_share_joy = 0
            low_share_joy = 0

        # Avoidance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_nour = sum(e.nourishment for e in recent) / len(recent)
            avoidance_risk = recent_joy < 0.3 and recent_nour < 0.3
        else:
            avoidance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "joy_impact": {
                "high_joy_nourishment": round(high_joy_nour, 2),
                "low_joy_nourishment": round(low_joy_nour, 2),
                "high_joy_creativity": round(high_joy_cre, 2),
                "low_joy_creativity": round(low_joy_cre, 2),
            },
            "sharing_effect": {
                "high_sharing_joy": round(high_share_joy, 2),
                "low_sharing_joy": round(low_share_joy, 2),
            },
            "avoidance_risk": avoidance_risk,
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
            "avg_nourishment": round(sum(e.nourishment for e in self._entries) / len(self._entries), 2),
        }

    def get_cooking_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get cooking suggestion."""
        suggestions = [
            "Cooking is not a chore. It's creation. You take raw ingredients and transform them into something nourishing. That's alchemy. That's art. That's love made visible.",
            "Start simple. One dish. Five ingredients. Fifteen minutes. You don't need to be a chef. You need to be willing. The person who cooks one simple meal is more alive than the person who orders every meal.",
            "Cook for someone. Even yourself. Cooking is an act of care. When you cook for someone, you're saying 'I want you to be nourished.' When you cook for yourself, you're saying 'I matter.' Both are true. Both matter.",
            "Experiment. Add something new. A spice you've never used. A technique you've never tried. Cooking is play. It's exploration. It's safe failure. The worst that happens is dinner is weird. The best is you discover something new.",
            "Notice the sensory pleasure. The sizzle of onions. The aroma of garlic. The color of fresh vegetables. The texture of dough. Cooking engages all the senses. Most people miss this. Don't be most people.",
            "Cook what you loved as a child. The foods of memory. Of comfort. Of belonging. They're not just nutrients. They're emotional anchors. They connect you to who you were. And who you are.",
            "Share the kitchen. Cook with someone. A partner. A child. A friend. Cooking together is connection. It's collaboration. It's creating something together. And eating it together. That's intimacy.",
            "Don't aim for perfect. Aim for present. The burnt toast. The oversalted soup. The lopsided cake. These are not failures. They're stories. They're evidence of life. Perfection is sterile. Presence is alive.",
            "Cooking is a form of self-care that feeds others too. When you cook, you nourish your body. When you share what you cook, you nourish relationships. It's efficient compassion. Practical love.",
            "The person who cooks regularly lives longer. Not because of the nutrients. Because of the intention. The creativity. The care. The engagement. Cooking is not just food preparation. It's life preparation."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One simple dish. One ingredient smelled. One moment in the kitchen. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A recipe tried. A meal shared. A technique learned. Medium culinary joy."
        else:
            capacity_note = "Good capacity. Deep cooking joy. A systematic practice of culinary creativity and nourishment. You have the strength to feed yourself and others with love."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Cooking is one of the most fundamental human activities. And one of the most neglected in modern life. Most people have outsourced their nourishment to corporations. They eat food that was designed in a lab, manufactured in a factory, and delivered in a box. And they wonder why they feel disconnected. Why they feel empty. Why their meals bring no joy. The work of cooking joy cultivation is about reclaiming the kitchen. About understanding that cooking is not a chore to be avoided but a practice to be cultivated. It's about creativity. About sensory pleasure. About nourishment. About care. And about understanding that the person who cooks is not just feeding their body. They're feeding their soul. They're connecting with tradition. They're expressing love. And they're creating moments of genuine joy in the most ordinary of activities."
        }

    def get_cooking_score(self) -> int:
        """Calculate overall cooking health (0-100)."""
        if not self._entries:
            return 25

        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_cre = sum(e.creativity for e in self._entries) / len(self._entries)
        avg_skill = sum(e.skill for e in self._entries) / len(self._entries)
        avg_nour = sum(e.nourishment for e in self._entries) / len(self._entries)
        avg_share = sum(e.sharing for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_nour = sum(e.nourishment for e in recent) / len(recent)
        else:
            recent_joy = 0
            recent_nour = 0

        # Avoidance penalty
        avoid_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            recent_nour_30 = sum(e.nourishment for e in last_30) / len(last_30)
            if recent_joy_30 < 0.3 and recent_nour_30 < 0.3:
                avoid_penalty = 15

        # Type variety
        unique_types = len(set(e.cooking_type for e in self._entries))

        score = (avg_joy * 25) + (avg_cre * 15) + (avg_skill * 15) + (avg_nour * 15) + (avg_share * 10) + (recent_joy * 5) + (recent_nour * 5) + (unique_types * 2) - avoid_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)
            self._stats["avg_nourishment"] = round(sum(e.nourishment for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_joy = sum(e.joy for e in recent) / len(recent)
                recent_nour = sum(e.nourishment for e in recent) / len(recent)
                self._stats["avoidance_risk"] = recent_joy < 0.3 and recent_nour < 0.3
            else:
                self._stats["avoidance_risk"] = False

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

    def _log_entry(self, entry: CookingEntry):
        try:
            with open(COOKING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "dish": entry.dish,
                    "cooking_type": entry.cooking_type,
                    "joy": entry.joy,
                    "nourishment": entry.nourishment,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cjc_instance: Optional[CookingJoyCultivator] = None
_cjc_lock = threading.Lock()


def get_cooking_joy_cultivator() -> CookingJoyCultivator:
    global _cjc_instance
    with _cjc_lock:
        if _cjc_instance is None:
            _cjc_instance = CookingJoyCultivator()
        return _cjc_instance
