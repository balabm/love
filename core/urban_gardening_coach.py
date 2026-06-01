"""
LOVE Urban Gardening Coach — City Horticulture Intelligence (Modern AI Pattern)

Most city dwellers think they can't garden. This coach:

1. URBAN TRACKING
   - Record urban gardening moments and their characteristics
   - Track urban types (balcony, windowsill, rooftop, community, indoor, vertical)
   - Log creativity, resourcefulness, yield, and satisfaction of urban growing

2. PATTERN ANALYSIS
   - Identify the user's urban profile (aspiring, struggling, developing, thriving)
    - Find urban patterns that create abundance vs limitation
   - Detect chronic space-defeatism and its costs

3. URBAN BUILDING
   - Suggest practices for growing in small spaces
   - Provide frameworks for vertical, container, and indoor gardening
   - Recommend practices for urban resourcefulness

4. CITY ABUNDANCE CULTIVATION
   - Track the correlation between urban gardening and city life quality
   - Alert when 'no space' is becoming an unquestioned belief
   - Celebrate moments of genuine urban harvest

Architecture:
- record_urban(garden, type, creativity, resourcefulness, yield, satisfaction): Log urban
- get_urban_stats(): Get urban pattern analysis
- get_urban_suggestion(capacity, context): Get suggestion
- get_urban_score(): Calculate overall urban health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "urban_gardening_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

URBAN_LOG = DATA_DIR / "urbans.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class UrbanEntry:
    """A tracked urban gardening moment."""
    entry_id: str = ""
    garden: str = ""  # what was grown
    urban_type: str = ""  # balcony, windowsill, rooftop, community, indoor, vertical
    creativity: float = 0.0  # 0-1
    resourcefulness: float = 0.0  # 0-1
    yield_val: float = 0.0  # 0-1
    satisfaction: float = 0.0  # 0-1
    community: float = 0.0  # 0-1 connected with other urban growers?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class UrbanGardeningCoach:
    """
    Intelligent urban gardening coach with space-defeatism detection and city abundance cultivation.
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
            "avg_creativity": 0.0,
            "avg_satisfaction": 0.0,
            "defeatism_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_urban(self, garden: str = "", urban_type: str = "", creativity: float = 0.0, resourcefulness: float = 0.0, yield_val: float = 0.0, satisfaction: float = 0.0, community: float = 0.0, notes: str = "") -> UrbanEntry:
        """Record an urban gardening moment."""
        entry_id = f"urb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = UrbanEntry(
            entry_id=entry_id,
            garden=garden or "unspecified",
            urban_type=urban_type or "balcony",
            creativity=creativity,
            resourcefulness=resourcefulness,
            yield_val=yield_val,
            satisfaction=satisfaction,
            community=community,
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

    def get_urban_stats(self) -> Dict[str, Any]:
        """Get urban pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "creativity_sum": 0.0, "yield_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.urban_type]["count"] += 1
            by_type[e.urban_type]["creativity_sum"] += e.creativity
            by_type[e.urban_type]["yield_sum"] += e.yield_val
            by_type[e.urban_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_creativity": round(data["creativity_sum"] / count, 2),
                "avg_yield": round(data["yield_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Creativity analysis
        high_cre = [e for e in self._entries if e.creativity > 0.7]
        low_cre = [e for e in self._entries if e.creativity < 0.4]
        if high_cre and low_cre:
            high_cre_sat = sum(e.satisfaction for e in high_cre) / len(high_cre)
            low_cre_sat = sum(e.satisfaction for e in low_cre) / len(low_cre)
            high_cre_yield = sum(e.yield_val for e in high_cre) / len(high_cre)
            low_cre_yield = sum(e.yield_val for e in low_cre) / len(low_cre)
        else:
            high_cre_sat = 0
            low_cre_sat = 0
            high_cre_yield = 0
            low_cre_yield = 0

        # Community analysis
        high_com = [e for e in self._entries if e.community > 0.7]
        low_com = [e for e in self._entries if e.community < 0.4]
        if high_com and low_com:
            high_com_sat = sum(e.satisfaction for e in high_com) / len(high_com)
            low_com_sat = sum(e.satisfaction for e in low_com) / len(low_com)
        else:
            high_com_sat = 0
            low_com_sat = 0

        # Defeatism risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cre = sum(e.creativity for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            defeatism_risk = recent_cre < 0.3 and recent_sat < 0.3
        else:
            defeatism_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "creativity_impact": {
                "high_creativity_satisfaction": round(high_cre_sat, 2),
                "low_creativity_satisfaction": round(low_cre_sat, 2),
                "high_creativity_yield": round(high_cre_yield, 2),
                "low_creativity_yield": round(low_cre_yield, 2),
            },
            "community_effect": {
                "high_community_satisfaction": round(high_com_sat, 2),
                "low_community_satisfaction": round(low_com_sat, 2),
            },
            "defeatism_risk": defeatism_risk,
            "avg_creativity": round(sum(e.creativity for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
        }

    def get_urban_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get urban suggestion."""
        suggestions = [
            "You don't need land. You need imagination. A windowsill is a garden. A balcony is a farm. A rooftop is an orchard. The city is full of growing spaces. You just have to see them.",
            "Grow up. Literally. Vertical gardening multiplies your space. Trellises. Hanging planters. Wall-mounted pots. Stackable containers. The city grows up. So should your garden.",
            "Containers are freedom. You can move them. You can control the soil. You can adjust the sun exposure. A container garden is a garden you curate. Not one you inherit.",
            "Choose city-hardy plants. Herbs. Salad greens. Cherry tomatoes. Peppers. Strawberries. These produce in small spaces. They're forgiving. And they reward you quickly.",
            "Use your microclimates. The sunny windowsill. The sheltered balcony corner. The warm wall. The breezy spot. Every urban space has microclimates. Match plants to them.",
            "Compost in the city. Worm bins. Bokashi. Small tumblers. Your food scraps become garden gold. The city generates waste. Your garden turns it into life. That's alchemy.",
            "Join a community garden. Or start one. Shared spaces. Shared knowledge. Shared harvests. Community gardens are not just about growing food. They're about growing community.",
            "Harvest rainwater. Even a small barrel on a balcony collects enough for container plants. Every drop saved is independence gained. The city has water. Capture it.",
            "Grow food you actually eat. Not what's impressive. Not what's exotic. What you cook with. What you enjoy. What makes your meals better. A few fresh herbs transform cooking.",
            "The person who gardens in the city is not making do. They're pioneering. They're creating green in a gray world. They're growing life in the heart of concrete. That's not limitation. That's courage."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One herb on a windowsill. One container planted. One urban growing space noticed. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A balcony garden started. A vertical planter built. A community garden visited. Medium urban abundance."
        else:
            capacity_note = "Good capacity. Deep urban gardening. A systematic practice of growing food, beauty, and life in the heart of the city. You have the strength to be an urban pioneer."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Urban gardening is not a compromise. It's an innovation. Most people believe you need land to garden. Acres. Soil. Sun. Space. And if you live in a city, they tell you gardening is impossible. But that's wrong. Cities are full of growing spaces. Balconies. Windowsills. Rooftops. Walls. Alleys. Community plots. Vertical spaces. Container gardens. Indoor gardens. The urban gardener is not a gardener making do. They're a gardener inventing new ways to grow. The work of urban gardening coaching is about helping you see the possibilities in your urban environment. About teaching you the techniques of container gardening, vertical growing, and indoor cultivation. About connecting you with urban growing communities. And about helping you understand that growing your own food in the city is not just possible. It's revolutionary. Because every plant grown in the city is a statement. That life can thrive anywhere. That green can grow in gray. And that the person who gardens in the city is not limited by their environment. They're inspired by it."
        }

    def get_urban_score(self) -> int:
        """Calculate overall urban health (0-100)."""
        if not self._entries:
            return 25

        avg_cre = sum(e.creativity for e in self._entries) / len(self._entries)
        avg_res = sum(e.resourcefulness for e in self._entries) / len(self._entries)
        avg_yield = sum(e.yield_val for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_com = sum(e.community for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cre = sum(e.creativity for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_cre = 0
            recent_sat = 0

        # Defeatism penalty
        def_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cre_30 = sum(e.creativity for e in last_30) / len(last_30)
            recent_sat_30 = sum(e.satisfaction for e in last_30) / len(last_30)
            if recent_cre_30 < 0.3 and recent_sat_30 < 0.3:
                def_penalty = 15

        # Type variety
        unique_types = len(set(e.urban_type for e in self._entries))

        score = (avg_cre * 20) + (avg_res * 15) + (avg_yield * 15) + (avg_sat * 20) + (avg_com * 10) + (recent_cre * 5) + (recent_sat * 5) + (unique_types * 2) - def_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_creativity"] = round(sum(e.creativity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cre = sum(e.creativity for e in recent) / len(recent)
                recent_sat = sum(e.satisfaction for e in recent) / len(recent)
                self._stats["defeatism_risk"] = recent_cre < 0.3 and recent_sat < 0.3
            else:
                self._stats["defeatism_risk"] = False

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

    def _log_entry(self, entry: UrbanEntry):
        try:
            with open(URBAN_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "garden": entry.garden,
                    "urban_type": entry.urban_type,
                    "creativity": entry.creativity,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ugc_instance: Optional[UrbanGardeningCoach] = None
_ugc_lock = threading.Lock()


def get_urban_gardening_coach() -> UrbanGardeningCoach:
    global _ugc_instance
    with _ugc_lock:
        if _ugc_instance is None:
            _ugc_instance = UrbanGardeningCoach()
        return _ugc_instance
