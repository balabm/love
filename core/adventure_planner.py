"""
LOVE Adventure Planner — Experience Intelligence (Modern AI Pattern)

Most adventures are either too big (vacations) or too small (Netflix). This planner:

1. ADVENTURE TRACKING
   - Record adventures with thrill, novelty, and growth ratings
   - Track planned vs spontaneous adventures
   - Log who shared the adventure and relationship impact

2. PATTERN ANALYSIS
   - Identify the user's adventure style (thrill-seeker, cultural explorer, nature lover, urban explorer)
   - Find adventure gaps and predict adventure cravings
   - Detect comfort zone boundaries

3. ADVENTURE GENERATION
   - Suggest micro-adventures (1-4 hours) based on location and energy
   - Plan medium adventures (day trips) and epic adventures (multi-day)
   - Recommend solo vs group adventures

4. GROWTH SUPPORT
   - Track courage and confidence growth from adventures
   - Suggest adventures that stretch without breaking
   - Celebrate adventure milestones

Architecture:
- record_adventure(activity, thrill, novelty, growth): Log adventure
- get_adventure_stats(): Get adventure pattern analysis
- get_adventure_suggestion(budget, time, energy): Get adventure idea
- get_adventure_score(): Calculate overall adventure health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "adventure_planner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ADVENTURE_LOG = DATA_DIR / "adventures.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Adventure:
    """A tracked adventure."""
    adventure_id: str = ""
    activity: str = ""
    adventure_type: str = ""  # thrill, cultural, nature, urban, creative, social
    duration_hours: float = 0.0
    thrill_level: float = 0.5  # 0-1
    novelty_level: float = 0.5  # 0-1
    growth_level: float = 0.5  # 0-1
    planned: bool = True
    solo: bool = True
    companions: List[str] = field(default_factory=list)
    cost: float = 0.0
    location: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AdventurePlanner:
    """
    Intelligent adventure planner with style analysis and micro- to epic-adventure generation.
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
        self._adventures: deque = deque(maxlen=200)
        self._stats = {
            "total_adventures": 0,
            "avg_thrill": 0.0,
            "avg_novelty": 0.0,
            "avg_growth": 0.0,
            "adventure_style": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_adventure(self, activity: str = "", adventure_type: str = "", duration: float = 0, thrill: float = 0.5, novelty: float = 0.5, growth: float = 0.5, planned: bool = True, solo: bool = True, companions: Optional[List[str]] = None, cost: float = 0, location: str = "", notes: str = "") -> Adventure:
        """Record an adventure."""
        adventure_id = f"adv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._adventures)}"
        adv = Adventure(
            adventure_id=adventure_id,
            activity=activity or "unspecified",
            adventure_type=adventure_type or "urban",
            duration_hours=duration,
            thrill_level=thrill,
            novelty_level=novelty,
            growth_level=growth,
            planned=planned,
            solo=solo,
            companions=companions or [],
            cost=cost,
            location=location or "",
            notes=notes,
        )

        with self._lock:
            self._adventures.append(adv)
            self._stats["total_adventures"] += 1
            self._update_stats()

        self._save_stats()
        self._log_adventure(adv)

        return adv

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_adventure_stats(self) -> Dict[str, Any]:
        """Get adventure pattern analysis."""
        if not self._adventures:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "thrill": 0.0, "novelty": 0.0, "growth": 0.0})
        for a in self._adventures:
            by_type[a.adventure_type]["count"] += 1
            by_type[a.adventure_type]["thrill"] += a.thrill_level
            by_type[a.adventure_type]["novelty"] += a.novelty_level
            by_type[a.adventure_type]["growth"] += a.growth_level

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_thrill": round(data["thrill"] / count, 2),
                "avg_novelty": round(data["novelty"] / count, 2),
                "avg_growth": round(data["growth"] / count, 2),
            }

        # Adventure style
        avg_thrill = sum(a.thrill_level for a in self._adventures) / len(self._adventures)
        avg_novelty = sum(a.novelty_level for a in self._adventures) / len(self._adventures)
        avg_growth = sum(a.growth_level for a in self._adventures) / len(self._adventures)

        if avg_thrill > 0.7:
            style = "thrill-seeker"
        elif avg_novelty > 0.7:
            style = "cultural explorer"
        elif avg_growth > 0.7:
            style = "growth hunter"
        elif type_stats.get("nature", {}).get("count", 0) > len(self._adventures) * 0.3:
            style = "nature lover"
        else:
            style = "urban explorer"

        # Drought detection
        recent = [a for a in self._adventures if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        drought = len(recent) == 0

        # Comfort zone analysis
        avg_risk = avg_thrill + avg_novelty / 2
        comfort_zone = "expanding" if avg_risk > 0.6 else "stable" if avg_risk > 0.3 else "contracting"

        return {
            "total_adventures": len(self._adventures),
            "type_stats": type_stats,
            "adventure_style": style,
            "avg_thrill": round(avg_thrill, 2),
            "avg_novelty": round(avg_novelty, 2),
            "avg_growth": round(avg_growth, 2),
            "drought": drought,
            "comfort_zone": comfort_zone,
            "planned_vs_spontaneous": {
                "planned": sum(1 for a in self._adventures if a.planned),
                "spontaneous": sum(1 for a in self._adventures if not a.planned),
            },
        }

    def get_adventure_suggestion(self, budget: str = "low", time: str = "micro", energy: str = "medium", solo: bool = True) -> Dict[str, Any]:
        """Get adventure idea."""
        adventures = {
            "micro": {  # 1-4 hours
                "low": [
                    "Take a bus to a neighborhood you've never visited and explore",
                    "Find the highest point in your city and watch sunset",
                    "Go to a restaurant of a cuisine you've never tried",
                    "Visit a museum or gallery you've walked past 100 times",
                    "Take a walking tour of your own city like a tourist",
                ],
                "medium": [
                    "Try an escape room or axe throwing",
                    "Take a cooking class for an unfamiliar cuisine",
                    "Go to a comedy show or open mic night",
                    "Try indoor rock climbing or bouldering",
                    "Take a one-day workshop (pottery, painting, improv)",
                ],
                "high": [
                    "Book a helicopter or hot air balloon ride",
                    "Do a zero-gravity or skydiving experience",
                    "Private tour with a local expert",
                    "Rent a luxury car for a scenic drive",
                    "Michelin-star restaurant tasting menu",
                ],
            },
            "medium": {  # Day trip
                "low": [
                    "Hike a trail you've never done before",
                    "Visit a nearby small town and walk its main street",
                    "Go to a state park or national monument",
                    "Beach day at a new beach",
                    "Volunteer for a day at an animal shelter or farm",
                ],
                "medium": [
                    "Whitewater rafting or kayaking day trip",
                    "Wine tasting tour in a nearby region",
                    "Guided cave or canyon exploration",
                    "Hot springs visit",
                    "Zipline or canopy tour",
                ],
                "high": [
                    "Private guided day trip to a remote location",
                    "Helicopter tour of natural wonders",
                    "Luxury glamping experience",
                    "Private yacht or sailboat day charter",
                    "Exclusive behind-the-scenes access tour",
                ],
            },
            "epic": {  # Multi-day
                "low": [
                    "Backpacking trip with minimal gear",
                    "Road trip with no planned destination",
                    "Volunteer vacation (build houses, teach, conservation)",
                    "Pilgrimage walk or long-distance trail",
                    "House-swap in another city",
                ],
                "medium": [
                    "International trip to a country you've never visited",
                    "Multi-day rafting or sailing expedition",
                    "Music festival or cultural immersion trip",
                    "Wildlife safari or photography expedition",
                    "Learn to surf/scuba/ski intensive camp",
                ],
                "high": [
                    "Round-the-world ticket with 5+ countries",
                    "Expedition to remote location (Antarctica, Everest base camp)",
                    "Luxury cruise or train journey",
                    "Private island rental",
                    "Space tourism (when available) or zero-g flight",
                ],
            },
        }

        time_options = adventures.get(time, adventures["micro"])
        budget_options = time_options.get(budget, time_options["low"])
        activity = random.choice(budget_options)

        if not solo and "hike" in activity:
            activity = activity.replace("a trail", "a trail with a friend")

        return {
            "activity": activity,
            "time_category": time,
            "budget": budget,
            "energy": energy,
            "solo": solo,
            "why": "Novel experiences are the raw material of a memorable life.",
            "planning_tips": ["Tell someone your plan", "Leave room for spontaneity", "Document one moment"],
        }

    def get_adventure_score(self) -> int:
        """Calculate overall adventure health (0-100)."""
        if not self._adventures:
            return 30

        # Novelty and growth
        avg_novelty = sum(a.novelty_level for a in self._adventures) / len(self._adventures)
        avg_growth = sum(a.growth_level for a in self._adventures) / len(self._adventures)

        # Frequency
        recent = [a for a in self._adventures if a.timestamp > (datetime.now() - timedelta(days=60)).isoformat()]
        frequency = len(recent)

        # Variety
        unique_types = len(set(a.adventure_type for a in self._adventures))

        # Spontaneity
        spontaneous = sum(1 for a in self._adventures if not a.planned)
        spontaneity = spontaneous / len(self._adventures)

        score = (avg_novelty * 25) + (avg_growth * 25) + (min(frequency, 8) * 5) + (unique_types * 5) + (spontaneity * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._adventures:
            self._stats["avg_thrill"] = round(sum(a.thrill_level for a in self._adventures) / len(self._adventures), 2)
            self._stats["avg_novelty"] = round(sum(a.novelty_level for a in self._adventures) / len(self._adventures), 2)
            self._stats["avg_growth"] = round(sum(a.growth_level for a in self._adventures) / len(self._adventures), 2)

            by_type = defaultdict(int)
            for a in self._adventures:
                by_type[a.adventure_type] += 1
            if by_type:
                self._stats["adventure_style"] = max(by_type.items(), key=lambda x: x[1])[0]

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

    def _log_adventure(self, adventure: Adventure):
        try:
            with open(ADVENTURE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": adventure.timestamp,
                    "activity": adventure.activity,
                    "type": adventure.adventure_type,
                    "thrill": adventure.thrill_level,
                    "novelty": adventure.novelty_level,
                    "growth": adventure.growth_level,
                    "planned": adventure.planned,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ap_instance: Optional[AdventurePlanner] = None
_ap_lock = threading.Lock()


def get_adventure_planner() -> AdventurePlanner:
    global _ap_instance
    with _ap_lock:
        if _ap_instance is None:
            _ap_instance = AdventurePlanner()
        return _ap_instance
