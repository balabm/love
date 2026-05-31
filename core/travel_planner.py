"""
LOVE Travel Planner — Travel Intelligence (Modern AI Pattern)

Most travel planning is spreadsheet chaos. This planner:

1. TRIP TRACKING
   - Record trips with purpose, duration, and satisfaction
   - Track packing efficiency (forgot items, overpacked)
   - Log travel stressors and highlights

2. PATTERN ANALYSIS
   - Identify optimal trip length for this user
   - Find preferred travel styles (adventure, relaxation, cultural)
   - Detect pre-trip stress patterns

3. SMART PREPARATION
   - Generate packing lists based on destination and season
   - Suggest optimal booking windows
   - Recommend trip timing based on work/finance cycles

4. PROACTIVE SUGGESTIONS
   - Suggest trips during low-stress periods
   - Recommend destinations based on current mood/energy
   - Alert about upcoming trip preparation needs

Architecture:
- record_trip(destination, purpose, duration, satisfaction): Log trip
- get_travel_stats(): Get travel pattern analysis
- get_packing_list(destination, season): Get smart packing list
- get_trip_suggestion(): Suggest next trip
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "travel_planner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRIP_LOG = DATA_DIR / "trips.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Trip:
    """A recorded trip."""
    destination: str = ""
    purpose: str = ""  # leisure, business, family, adventure, relaxation
    duration_days: float = 0.0
    satisfaction: float = 0.5  # 0-1
    stress_level: float = 0.3  # 0-1
    highlights: List[str] = field(default_factory=list)
    stressors: List[str] = field(default_factory=list)
    packing_score: float = 0.5  # how well packing worked
    forgot_items: List[str] = field(default_factory=list)
    overpacked: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class TravelPreference:
    """Travel preferences learned over time."""
    preferred_purpose: str = ""
    optimal_duration: float = 5.0
    preferred_season: str = ""
    avg_satisfaction: float = 0.5
    trip_count: int = 0


class TravelPlanner:
    """
    Personal travel planner with pattern intelligence.
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
        self._trips: deque = deque(maxlen=200)
        self._preferences: Dict[str, TravelPreference] = {}
        self._stats = {
            "total_trips": 0,
            "avg_satisfaction": 0.5,
            "avg_stress": 0.3,
            "avg_duration": 5.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_trip(self, destination: str = "", purpose: str = "", duration: float = 0, satisfaction: float = 0.5, stress_level: float = 0.3, highlights: Optional[List[str]] = None, stressors: Optional[List[str]] = None, packing_score: float = 0.5, forgot_items: Optional[List[str]] = None, overpacked: bool = False, notes: str = "") -> Trip:
        """Record a trip."""
        trip = Trip(
            destination=destination or "unspecified",
            purpose=purpose or "leisure",
            duration_days=duration,
            satisfaction=satisfaction,
            stress_level=stress_level,
            highlights=highlights or [],
            stressors=stressors or [],
            packing_score=packing_score,
            forgot_items=forgot_items or [],
            overpacked=overpacked,
            notes=notes,
        )

        with self._lock:
            self._trips.append(trip)
            self._stats["total_trips"] += 1
            self._update_preferences(trip)
            self._update_stats(trip)

        self._save_stats()
        self._log_trip(trip)

        return trip

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_travel_stats(self, months: int = 12) -> Dict[str, Any]:
        """Get travel pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=months * 30)).isoformat()
        recent = [t for t in self._trips if t.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Purpose breakdown
        by_purpose = defaultdict(lambda: {"count": 0, "satisfaction_sum": 0.0, "duration_sum": 0.0})
        for t in recent:
            p = t.purpose
            by_purpose[p]["count"] += 1
            by_purpose[p]["satisfaction_sum"] += t.satisfaction
            by_purpose[p]["duration_sum"] += t.duration_days

        purpose_stats = {}
        for p, data in by_purpose.items():
            purpose_stats[p] = {
                "count": data["count"],
                "avg_satisfaction": round(data["satisfaction_sum"] / data["count"], 2),
                "avg_duration": round(data["duration_sum"] / data["count"], 1),
            }

        # Destination analysis
        by_destination = defaultdict(lambda: {"count": 0, "satisfaction": 0.0})
        for t in recent:
            by_destination[t.destination]["count"] += 1
            by_destination[t.destination]["satisfaction"] += t.satisfaction

        top_destinations = sorted(
            [(d, s["count"], round(s["satisfaction"]/s["count"], 2)) for d, s in by_destination.items()],
            key=lambda x: x[2],
            reverse=True,
        )[:5]

        # Packing analysis
        forgot_counts = defaultdict(int)
        for t in recent:
            for item in t.forgot_items:
                forgot_counts[item] += 1

        overpacked_pct = sum(1 for t in recent if t.overpacked) / len(recent) * 100

        return {
            "months_analyzed": months,
            "total_trips": len(recent),
            "avg_satisfaction": round(sum(t.satisfaction for t in recent) / len(recent), 2),
            "avg_stress": round(sum(t.stress_level for t in recent) / len(recent), 2),
            "avg_duration": round(sum(t.duration_days for t in recent) / len(recent), 1),
            "purpose_breakdown": purpose_stats,
            "top_destinations": top_destinations,
            "commonly_forgotten": sorted(forgot_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "overpacked_pct": round(overpacked_pct, 1),
        }

    def get_packing_list(self, destination: str = "", season: str = "", duration: float = 3, activities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate smart packing list based on past trips."""
        # Base packing list
        base_items = ["Passport/ID", "Phone charger", "Toiletries", "Underwear", "Socks", "Sleepwear"]

        # Season-specific
        season_items = {
            "summer": ["Sunscreen", "Sunglasses", "Hat", "Light clothing", "Swimwear"],
            "winter": ["Coat", "Gloves", "Scarf", "Warm socks", "Layers"],
            "spring": ["Light jacket", "Umbrella", "Layered clothing"],
            "fall": ["Warm jacket", "Boots", "Layers"],
        }

        # Activity-specific
        activity_items = {
            "hiking": ["Hiking boots", "Backpack", "Water bottle", "Trail snacks"],
            "beach": ["Beach towel", "Flip flops", "Beach bag", "Waterproof phone case"],
            "business": ["Laptop", "Business cards", "Formal shoes", "Iron/steamer"],
            "city": ["Comfortable walking shoes", "Day bag", "Map/guidebook"],
            "camping": ["Tent", "Sleeping bag", "Flashlight", "Multi-tool"],
        }

        # Check commonly forgotten items from past trips
        stats = self.get_travel_stats()
        commonly_forgotten = [item[0] for item in stats.get("commonly_forgotten", [])]

        # Build list
        packing = {
            "essential": base_items,
            "season_specific": season_items.get(season, []),
            "activity_specific": [],
            "dont_forget": commonly_forgotten[:3],
            "duration_based": [],
        }

        for activity in (activities or []):
            packing["activity_specific"].extend(activity_items.get(activity, []))

        # Duration-based suggestions
        if duration > 7:
            packing["duration_based"].append("Laundry bag")
            packing["duration_based"].append("Extra medication if needed")
        if duration > 3:
            packing["duration_based"].append("Extra outfits")

        return {
            "destination": destination,
            "duration": duration,
            "season": season,
            "packing_list": packing,
            "packing_tip": "Roll clothes instead of folding to save space and reduce wrinkles." if "business" not in (activities or []) else "Use packing cubes to keep formal wear crisp.",
        }

    def get_trip_suggestion(self) -> Dict[str, Any]:
        """Suggest next trip based on patterns."""
        stats = self.get_travel_stats()
        if stats.get("status") == "insufficient_data":
            return {
                "suggestion": "Record some trips to get personalized travel suggestions.",
                "type": "general",
            }

        # Find most satisfying purpose
        purposes = stats.get("purpose_breakdown", {})
        if purposes:
            best_purpose = max(purposes.items(), key=lambda x: x[1]["avg_satisfaction"])
            suggested_purpose = best_purpose[0]
            suggested_duration = best_purpose[1]["avg_duration"]
        else:
            suggested_purpose = "leisure"
            suggested_duration = 3

        # Check stress levels
        recent_stress = stats.get("avg_stress", 0)
        if recent_stress > 0.5:
            suggestion = f"You've been stressed on recent trips. Consider a {suggested_duration}-day {suggested_purpose} trip for recovery."
        else:
            suggestion = f"Based on your history, a {suggested_duration}-day {suggested_purpose} trip would be ideal."

        return {
            "suggestion": suggestion,
            "suggested_purpose": suggested_purpose,
            "suggested_duration": suggested_duration,
            "best_destination_type": "familiar" if recent_stress > 0.4 else "new",
            "type": "personalized",
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_preferences(self, trip: Trip):
        """Update travel preferences based on trip."""
        purpose = trip.purpose
        if purpose not in self._preferences:
            self._preferences[purpose] = TravelPreference(preferred_purpose=purpose)

        pref = self._preferences[purpose]
        pref.trip_count += 1
        pref.avg_satisfaction = (pref.avg_satisfaction * (pref.trip_count - 1) + trip.satisfaction) / pref.trip_count
        pref.optimal_duration = (pref.optimal_duration * (pref.trip_count - 1) + trip.duration_days) / pref.trip_count

    def _update_stats(self, trip: Trip):
        """Update running statistics."""
        n = self._stats["total_trips"]
        self._stats["avg_satisfaction"] = round((self._stats["avg_satisfaction"] * (n - 1) + trip.satisfaction) / n, 2)
        self._stats["avg_stress"] = round((self._stats["avg_stress"] * (n - 1) + trip.stress_level) / n, 2)
        self._stats["avg_duration"] = round((self._stats["avg_duration"] * (n - 1) + trip.duration_days) / n, 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "preferences": {k: {
                    "preferred_purpose": v.preferred_purpose,
                    "optimal_duration": v.optimal_duration,
                    "avg_satisfaction": v.avg_satisfaction,
                    "trip_count": v.trip_count,
                } for k, v in self._preferences.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("preferences", {}).items():
                    self._preferences[k] = TravelPreference(**v)
        except Exception:
            pass

    def _log_trip(self, trip: Trip):
        try:
            with open(TRIP_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": trip.timestamp,
                    "destination": trip.destination,
                    "purpose": trip.purpose,
                    "duration": trip.duration_days,
                    "satisfaction": trip.satisfaction,
                    "stress": trip.stress_level,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_tp_instance: Optional[TravelPlanner] = None
_tp_lock = threading.Lock()


def get_travel_planner() -> TravelPlanner:
    global _tp_instance
    with _tp_lock:
        if _tp_instance is None:
            _tp_instance = TravelPlanner()
        return _tp_instance
