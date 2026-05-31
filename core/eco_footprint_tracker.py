"""
LOVE Eco Footprint Tracker — Impact Intelligence (Modern AI Pattern)

Most people don't know their footprint. This tracker:

1. FOOTPRINT TRACKING
   - Record carbon and ecological footprint measurements
   - Track footprint categories (transport, home, food, goods, services)
   - Log changes and their effects on overall impact

2. PATTERN ANALYSIS
   - Identify the user's footprint profile (heavy, moderate, light, regenerative)
   - Find reduction patterns that create lasting change
   - Detect hidden sources of high impact

3. FOOTPRINT BUILDING
   - Suggest reduction strategies matched to current footprint profile
   - Provide measurement and comparison frameworks
   - Recommendation offset and removal practices

4. IMPACT CULTIVATION
   - Track the correlation between awareness and reduction
   - Alert when footprint is creeping upward
   - Celebrate milestone reductions

Architecture:
- record_measurement(category, amount, unit, reduction): Log measurement
- get_footprint_stats(): Get footprint pattern analysis
- get_reduction_strategy(category, current, target): Get strategy
- get_footprint_score(): Calculate overall footprint health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "eco_footprint_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FOOTPRINT_LOG = DATA_DIR / "measurements.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class FootprintEntry:
    """A tracked footprint entry."""
    entry_id: str = ""
    category: str = ""  # transport, home, food, goods, services
    amount: float = 0.0  # footprint amount
    unit: str = ""  # kg CO2, hectares, etc.
    reduction: float = 0.0  # amount reduced from previous
    reduction_action: str = ""  # what caused the reduction
    global_average: float = 0.0  # for comparison
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EcoFootprintTracker:
    """
    Intelligent eco footprint tracker with reduction optimization and impact visualization.
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
            "total_reduction": 0.0,
            "avg_footprint": 0.0,
            "creep_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_measurement(self, category: str = "", amount: float = 0.0, unit: str = "", reduction: float = 0.0, reduction_action: str = "", global_average: float = 0.0, notes: str = "") -> FootprintEntry:
        """Record a footprint entry."""
        entry_id = f"eco_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = FootprintEntry(
            entry_id=entry_id,
            category=category or "transport",
            amount=amount,
            unit=unit or "kg CO2",
            reduction=reduction,
            reduction_action=reduction_action,
            global_average=global_average,
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

    def get_footprint_stats(self) -> Dict[str, Any]:
        """Get footprint pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Category analysis
        by_cat = defaultdict(lambda: {"count": 0, "amount_sum": 0.0, "reduction_sum": 0.0, "global_sum": 0.0})
        for e in self._entries:
            by_cat[e.category]["count"] += 1
            by_cat[e.category]["amount_sum"] += e.amount
            by_cat[e.category]["reduction_sum"] += e.reduction
            by_cat[e.category]["global_sum"] += e.global_average

        cat_stats = {}
        for c, data in by_cat.items():
            count = data["count"]
            cat_stats[c] = {
                "count": count,
                "avg_amount": round(data["amount_sum"] / count, 1),
                "avg_reduction": round(data["reduction_sum"] / count, 1),
                "vs_global_avg": round((data["amount_sum"] / count) / max(1, data["global_sum"] / count), 2),
            }

        highest_cat = max(cat_stats.items(), key=lambda x: x[1]["avg_amount"]) if cat_stats else ("", {})

        # Reduction analysis
        with_reduction = [e for e in self._entries if e.reduction > 0]
        without_reduction = [e for e in self._entries if e.reduction <= 0]
        if with_reduction and without_reduction:
            with_red_amount = sum(e.amount for e in with_reduction) / len(with_reduction)
            without_red_amount = sum(e.amount for e in without_reduction) / len(without_reduction)
        else:
            with_red_amount = 0
            without_red_amount = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_amount = sum(e.amount for e in recent) / len(recent)
            recent_reduction = sum(e.reduction for e in recent) / len(recent)
        else:
            recent_amount = 0
            recent_reduction = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_amount = sum(e.amount for e in older) / len(older)
            older_reduction = sum(e.reduction for e in older) / len(older)
            amount_trend = recent_amount - older_amount
            reduction_trend = recent_reduction - older_reduction
        else:
            amount_trend = 0
            reduction_trend = 0

        # Creep detection
        creep_risk = amount_trend > 0 and reduction_trend < 0

        return {
            "total_entries": len(self._entries),
            "total_reduction": round(sum(e.reduction for e in self._entries), 1),
            "category_stats": cat_stats,
            "highest_category": highest_cat[0],
            "reduction_effectiveness": {
                "with_reduction_avg": round(with_red_amount, 1),
                "without_reduction_avg": round(without_red_amount, 1),
            },
            "creep_risk": creep_risk,
            "avg_footprint": round(sum(e.amount for e in self._entries) / len(self._entries), 1),
            "amount_trend": round(amount_trend, 1),
            "reduction_trend": round(reduction_trend, 1),
            "recent_footprint": round(recent_amount, 1),
        }

    def get_reduction_strategy(self, category: str = "", current: float = 0.0, target: float = 0.0) -> Dict[str, Any]:
        """Get strategy."""
        strategies = {
            "transport": [
                "Cut one flight per year. A single round-trip transatlantic flight = 1.6 tons CO2. That's significant.",
                "Bike to work one day a week. Start there. Build up. Every mile not driven matters.",
                "When you replace your car, go electric. Or hybrid. Or smaller. In that order.",
            ],
            "home": [
                "Insulate. The biggest bang for buck. Attic. Walls. Windows. Keep heat in. Keep cool in.",
                "Heat pump instead of furnace. 3-4x more efficient. The future of home heating.",
                "Solar panels. If you own your roof. The payback is 6-10 years. Then free electricity for decades.",
            ],
            "food": [
                "Reduce beef. One burger = 2 kg CO2. A chicken sandwich = 0.5 kg. Choose wisely.",
                "Waste less. 40% of food is wasted. Plan meals. Use leftovers. Compost scraps.",
                "Buy local and seasonal. Food miles matter. Fresh tastes better. Two wins.",
            ],
            "goods": [
                "Buy less. The most sustainable product is the one you don't buy. Question every purchase.",
                "Buy used. Thrift. Consignment. Facebook Marketplace. Used is the new new.",
                "Buy durable. One $100 item that lasts 10 years beats ten $15 items that last 1 year.",
            ],
            "services": [
                "Choose green providers. Green energy. Carbon-neutral shipping. Your money votes.",
                "Bank responsibly. Some banks fund fossil fuels. Others fund renewables. Know where your money sleeps.",
                "Offset what you can't reduce. But offset genuinely. Not as license to pollute. As last resort.",
            ],
            "general": [
                "Measure first. You can't manage what you don't measure. Use a carbon calculator. Know your number.",
                "Focus on the big items. Transport. Home. Food. These are 80% of most footprints. Ignore the small stuff initially.",
                "Progress, not perfection. A 20% reduction is heroic. A 50% reduction is legendary. Start with 10%.",
            ],
        }

        selected = strategies.get(category, strategies["general"])

        gap = current - target
        if gap > current * 0.5:
            gap_note = "Large gap. This will take time. Focus on one category. One change. Consistency wins."
        elif gap > 0:
            gap_note = "Moderate gap. You're making progress. Keep going. Small reductions compound."
        else:
            gap_note = "At or below target. You're doing well. Now maintain. Or help others."

        return {
            "category": category or "general",
            "current": current,
            "target": target,
            "strategy": random.choice(selected),
            "gap_note": gap_note,
            "principle": "Most people feel powerless about climate change. They're not. Individual choices aggregate. Your footprint is not trivial. A typical American produces 16 tons of CO2 per year. Cutting that to 8 tons is equivalent to taking a car off the road. You are not powerless. You are the power. Every choice is a vote for the world you want.",
        }

    def get_footprint_score(self) -> int:
        """Calculate overall footprint health (0-100)."""
        if not self._entries:
            return 30

        # Low footprint and high reduction
        avg_amount = sum(e.amount for e in self._entries) / len(self._entries)
        total_reduction = sum(e.reduction for e in self._entries)

        # Comparison to global average
        global_avgs = [e.global_average for e in self._entries if e.global_average > 0]
        if global_avgs:
            avg_global = sum(global_avgs) / len(global_avgs)
            comparison = max(0, 1 - avg_amount / max(1, avg_global))
        else:
            comparison = 0.5

        # Category variety
        unique_cats = len(set(e.category for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_amount = sum(e.amount for e in recent) / len(recent)
            recent_reduction = sum(e.reduction for e in recent) / len(recent)
        else:
            recent_amount = 0
            recent_reduction = 0

        # Creep penalty
        creep_penalty = 0
        if len(self._entries) > 14:
            older = list(self._entries)[:-14]
            older_amount = sum(e.amount for e in older) / len(older)
            if recent_amount > older_amount:
                creep_penalty = 10

        score = (comparison * 30) + (total_reduction * 2) + (unique_cats * 3) + ((1 - recent_amount / max(1, avg_amount)) * 15) + (recent_reduction * 5) - creep_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["total_reduction"] = round(sum(e.reduction for e in self._entries), 1)
            self._stats["avg_footprint"] = round(sum(e.amount for e in self._entries) / len(self._entries), 1)

            if len(self._entries) > 14:
                recent = list(self._entries)[-14:]
                older = list(self._entries)[:-14]
                recent_amount = sum(e.amount for e in recent) / len(recent)
                older_amount = sum(e.amount for e in older) / len(older)
                self._stats["creep_risk"] = recent_amount > older_amount

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

    def _log_entry(self, entry: FootprintEntry):
        try:
            with open(FOOTPRINT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "category": entry.category,
                    "amount": entry.amount,
                    "unit": entry.unit,
                    "reduction": entry.reduction,
                    "reduction_action": entry.reduction_action,
                    "global_average": entry.global_average,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_eft_instance: Optional[EcoFootprintTracker] = None
_eft_lock = threading.Lock()


def get_eco_footprint_tracker() -> EcoFootprintTracker:
    global _eft_instance
    with _eft_lock:
        if _eft_instance is None:
            _eft_instance = EcoFootprintTracker()
        return _eft_instance
