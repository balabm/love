"""
LOVE Morning Routine Designer — Morning Intelligence (Modern AI Pattern)

Most morning routines are static lists. This designer:

1. ROUTINE TRACKING
   - Record morning routine components and their effectiveness
   - Track wake-up time, energy levels, and mood after routine
   - Log which routine elements actually improve the day

2. PATTERN ANALYSIS
   - Identify the optimal routine length and composition
   - Find which activities boost energy vs drain it
   - Detect wake-up time patterns and their impact

3. PERSONALIZED DESIGN
   - Generate custom morning routines based on goals and constraints
   - Adjust routines based on upcoming day demands
   - Suggest routine swaps when energy patterns change

4. PROACTIVE ADAPTATION
   - Alert when morning routine becomes stale
   - Suggest seasonal adjustments (winter vs summer mornings)
   - Recommend routine elements based on current life phase

Architecture:
- record_routine_element(element, duration, energy_impact): Log routine part
- get_morning_stats(): Get morning effectiveness analysis
- get_routine_suggestion(goals, time_available): Get custom routine
- get_wake_up_optimization(): Get wake-up time recommendations
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "morning_routine_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ROUTINE_LOG = DATA_DIR / "routines.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RoutineElement:
    """A morning routine element."""
    element_id: str = ""
    name: str = ""
    category: str = ""  # movement, mindfulness, nutrition, hygiene, planning, creative, social
    duration_minutes: float = 0.0
    energy_impact: float = 0.0  # -5 to +5
    mood_impact: float = 0.0  # -5 to +5
    focus_impact: float = 0.0  # -5 to +5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class MorningRecord:
    """A complete morning record."""
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    wake_up_time: str = ""
    total_routine_time: float = 0.0
    elements: List[str] = field(default_factory=list)
    energy_before: float = 3.0  # 1-10
    energy_after: float = 5.0
    mood_after: float = 5.0
    focus_after: float = 5.0
    day_rating: float = 0.5  # how good the day was
    notes: str = ""


class MorningRoutineDesigner:
    """
    Intelligent morning routine designer with personalization.
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
        self._elements: deque = deque(maxlen=300)
        self._mornings: deque = deque(maxlen=100)
        self._stats = {
            "total_elements": 0,
            "total_mornings": 0,
            "avg_routine_time": 0.0,
            "avg_energy_boost": 0.0,
            "best_element": "",
            "optimal_wake_time": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_routine_element(self, name: str = "", category: str = "", duration: float = 0, energy_impact: float = 0, mood_impact: float = 0, focus_impact: float = 0, notes: str = "") -> RoutineElement:
        """Record a routine element."""
        element_id = f"elem_{name.replace(' ', '_').lower()}_{len(self._elements)}"
        element = RoutineElement(
            element_id=element_id,
            name=name or "untitled",
            category=category or "general",
            duration_minutes=duration,
            energy_impact=energy_impact,
            mood_impact=mood_impact,
            focus_impact=focus_impact,
            notes=notes,
        )

        with self._lock:
            self._elements.append(element)
            self._stats["total_elements"] += 1
            self._update_element_stats()

        self._save_stats()
        self._log_element(element)

        return element

    def record_morning(self, wake_up_time: str = "", elements: Optional[List[str]] = None, energy_before: float = 3.0, energy_after: float = 5.0, mood_after: float = 5.0, focus_after: float = 5.0, day_rating: float = 0.5, notes: str = "") -> MorningRecord:
        """Record a complete morning."""
        morning = MorningRecord(
            wake_up_time=wake_up_time,
            elements=elements or [],
            energy_before=energy_before,
            energy_after=energy_after,
            mood_after=mood_after,
            focus_after=focus_after,
            day_rating=day_rating,
            notes=notes,
        )

        with self._lock:
            self._mornings.append(morning)
            self._stats["total_mornings"] += 1
            self._update_morning_stats()

        self._save_stats()
        self._log_morning(morning)

        return morning

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_morning_stats(self) -> Dict[str, Any]:
        """Get morning effectiveness analysis."""
        if not self._mornings:
            return {"status": "insufficient_data"}

        # Element effectiveness
        by_element = defaultdict(lambda: {"count": 0, "energy_sum": 0.0, "mood_sum": 0.0, "focus_sum": 0.0, "day_rating_sum": 0.0})
        
        for morning in self._mornings:
            for elem_name in morning.elements:
                # Find the element record
                elem = next((e for e in self._elements if e.name == elem_name), None)
                if elem:
                    by_element[elem_name]["count"] += 1
                    by_element[elem_name]["energy_sum"] += morning.energy_after - morning.energy_before
                    by_element[elem_name]["mood_sum"] += morning.mood_after
                    by_element[elem_name]["focus_sum"] += morning.focus_after
                    by_element[elem_name]["day_rating_sum"] += morning.day_rating

        element_stats = {}
        for name, data in by_element.items():
            count = data["count"]
            element_stats[name] = {
                "count": count,
                "avg_energy_boost": round(data["energy_sum"] / count, 2),
                "avg_mood": round(data["mood_sum"] / count, 2),
                "avg_focus": round(data["focus_sum"] / count, 2),
                "avg_day_rating": round(data["day_rating_sum"] / count, 2),
            }

        # Wake-up time analysis
        wake_times = {}
        for morning in self._mornings:
            if morning.wake_up_time:
                hour = morning.wake_up_time[:2]
                if hour not in wake_times:
                    wake_times[hour] = {"count": 0, "day_rating_sum": 0.0, "energy_sum": 0.0}
                wake_times[hour]["count"] += 1
                wake_times[hour]["day_rating_sum"] += morning.day_rating
                wake_times[hour]["energy_sum"] += morning.energy_after

        wake_stats = {h: {"avg_day_rating": round(v["day_rating_sum"]/v["count"], 2), "avg_energy": round(v["energy_sum"]/v["count"], 2)} for h, v in wake_times.items() if v["count"] >= 3}

        # Best wake time
        best_wake = max(wake_stats.items(), key=lambda x: x[1]["avg_day_rating"])[0] if wake_stats else ""

        # Routine length analysis
        if self._mornings:
            short = [m for m in self._mornings if m.total_routine_time < 30]
            medium = [m for m in self._mornings if 30 <= m.total_routine_time <= 60]
            long_r = [m for m in self._mornings if m.total_routine_time > 60]

            length_stats = {
                "short": {"count": len(short), "avg_day_rating": round(sum(m.day_rating for m in short)/max(1, len(short)), 2)} if short else None,
                "medium": {"count": len(medium), "avg_day_rating": round(sum(m.day_rating for m in medium)/max(1, len(medium)), 2)} if medium else None,
                "long": {"count": len(long_r), "avg_day_rating": round(sum(m.day_rating for m in long_r)/max(1, len(long_r)), 2)} if long_r else None,
            }
        else:
            length_stats = {}

        return {
            "total_mornings": len(self._mornings),
            "avg_energy_boost": round(sum(m.energy_after - m.energy_before for m in self._mornings) / len(self._mornings), 2),
            "avg_mood": round(sum(m.mood_after for m in self._mornings) / len(self._mornings), 2),
            "avg_focus": round(sum(m.focus_after for m in self._mornings) / len(self._mornings), 2),
            "element_stats": element_stats,
            "wake_time_stats": wake_stats,
            "best_wake_time": best_wake,
            "routine_length_stats": {k: v for k, v in length_stats.items() if v},
        }

    def get_routine_suggestion(self, goals: Optional[List[str]] = None, time_available: float = 30, energy_level: str = "medium") -> List[Dict[str, Any]]:
        """Get custom morning routine."""
        goals = goals or ["energy", "focus"]
        
        # Base elements by category
        element_pool = {
            "movement": [
                {"name": "Stretch", "duration": 5, "energy": 2, "mood": 1, "focus": 0},
                {"name": "Quick walk", "duration": 15, "energy": 4, "mood": 3, "focus": 1},
                {"name": "Jumping jacks + pushups", "duration": 10, "energy": 5, "mood": 2, "focus": 1},
                {"name": "Yoga flow", "duration": 20, "energy": 3, "mood": 4, "focus": 2},
            ],
            "mindfulness": [
                {"name": "Meditation", "duration": 10, "energy": 0, "mood": 3, "focus": 4},
                {"name": "Breathing exercise", "duration": 5, "energy": 1, "mood": 2, "focus": 3},
                {"name": "Gratitude journaling", "duration": 5, "energy": 1, "mood": 4, "focus": 1},
            ],
            "nutrition": [
                {"name": "Healthy breakfast", "duration": 15, "energy": 3, "mood": 2, "focus": 2},
                {"name": "Green tea/coffee", "duration": 5, "energy": 2, "mood": 1, "focus": 2},
                {"name": "Water + vitamins", "duration": 3, "energy": 1, "mood": 1, "focus": 0},
            ],
            "planning": [
                {"name": "Review calendar", "duration": 5, "energy": 0, "mood": 1, "focus": 3},
                {"name": "Set top 3 priorities", "duration": 5, "energy": 0, "mood": 2, "focus": 4},
                {"name": "Time block schedule", "duration": 10, "energy": 0, "mood": 1, "focus": 4},
            ],
            "creative": [
                {"name": "Read 10 pages", "duration": 15, "energy": 1, "mood": 3, "focus": 2},
                {"name": "Free writing", "duration": 10, "energy": 1, "mood": 3, "focus": 2},
                {"name": "Sketch/doodle", "duration": 10, "energy": 1, "mood": 4, "focus": 1},
            ],
        }

        # Select based on goals
        selected = []
        remaining_time = time_available

        # Always include basics
        basics = ["Water + vitamins", "Stretch", "Set top 3 priorities"]
        for basic in basics:
            for cat, elems in element_pool.items():
                for elem in elems:
                    if elem["name"] == basic and remaining_time >= elem["duration"]:
                        selected.append({**elem, "category": cat})
                        remaining_time -= elem["duration"]
                        break

        # Add goal-specific elements
        goal_elements = {
            "energy": ["Quick walk", "Jumping jacks + pushups", "Healthy breakfast"],
            "focus": ["Meditation", "Time block schedule", "Breathing exercise"],
            "mood": ["Gratitude journaling", "Sketch/doodle", "Yoga flow"],
            "creative": ["Free writing", "Read 10 pages", "Sketch/doodle"],
        }

        for goal in goals:
            for elem_name in goal_elements.get(goal, []):
                for cat, elems in element_pool.items():
                    for elem in elems:
                        if elem["name"] == elem_name and remaining_time >= elem["duration"] and not any(s["name"] == elem_name for s in selected):
                            selected.append({**elem, "category": cat})
                            remaining_time -= elem["duration"]
                            break

        # Sort by natural morning flow
        flow_order = {"movement": 0, "nutrition": 1, "mindfulness": 2, "creative": 3, "planning": 4}
        selected.sort(key=lambda x: flow_order.get(x["category"], 5))

        return selected

    def get_wake_up_optimization(self) -> Dict[str, Any]:
        """Get wake-up time recommendations."""
        stats = self.get_morning_stats()
        if stats.get("status") == "insufficient_data":
            return {"suggestion": "Record some mornings to get wake-up optimization."}

        best_wake = stats.get("best_wake_time", "")
        wake_stats = stats.get("wake_time_stats", {})

        if best_wake and wake_stats:
            best_data = wake_stats.get(best_wake, {})
            return {
                "best_wake_time": f"{best_wake}:00",
                "reason": f"Waking at {best_wake}:00 correlates with {best_data.get('avg_day_rating', 0):.1f}/1.0 day rating and {best_data.get('avg_energy', 0):.1f}/10 energy.",
                "suggestion": f"Try consistently waking at {best_wake}:00 for the next 2 weeks.",
            }

        return {"suggestion": "No clear wake-up pattern yet. Try different times and record results."}

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_element_stats(self):
        """Update element statistics."""
        if self._elements:
            by_name = defaultdict(list)
            for e in self._elements:
                by_name[e.name].append(e)

            best = max(by_name.items(), key=lambda x: sum(e.energy_impact for e in x[1])/len(x[1]))
            self._stats["best_element"] = best[0]

    def _update_morning_stats(self):
        """Update morning statistics."""
        if self._mornings:
            self._stats["avg_routine_time"] = round(sum(m.total_routine_time for m in self._mornings) / len(self._mornings), 1)
            self._stats["avg_energy_boost"] = round(sum(m.energy_after - m.energy_before for m in self._mornings) / len(self._mornings), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "mornings": [{
                    "date": m.date,
                    "wake_up_time": m.wake_up_time,
                    "total_routine_time": m.total_routine_time,
                    "elements": m.elements,
                    "energy_before": m.energy_before,
                    "energy_after": m.energy_after,
                    "mood_after": m.mood_after,
                    "focus_after": m.focus_after,
                    "day_rating": m.day_rating,
                    "notes": m.notes,
                } for m in list(self._mornings)[-50:]],
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
        except Exception:
            pass

    def _log_element(self, element: RoutineElement):
        try:
            with open(ROUTINE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": element.timestamp,
                    "name": element.name,
                    "category": element.category,
                    "duration": element.duration_minutes,
                    "energy_impact": element.energy_impact,
                }) + "\n")
        except Exception:
            pass

    def _log_morning(self, morning: MorningRecord):
        try:
            with open(ROUTINE_LOG, "a") as f:
                f.write(json.dumps({
                    "date": morning.date,
                    "wake_up": morning.wake_up_time,
                    "energy_before": morning.energy_before,
                    "energy_after": morning.energy_after,
                    "day_rating": morning.day_rating,
                    "elements": morning.elements,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mrd_instance: Optional[MorningRoutineDesigner] = None
_mrd_lock = threading.Lock()


def get_morning_routine_designer() -> MorningRoutineDesigner:
    global _mrd_instance
    with _mrd_lock:
        if _mrd_instance is None:
            _mrd_instance = MorningRoutineDesigner()
        return _mrd_instance
