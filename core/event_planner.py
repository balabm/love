"""
LOVE Event Planner — Event Intelligence (Modern AI Pattern)

Most event planning is spreadsheet chaos. This planner:

1. EVENT TRACKING
   - Record events with purpose, attendees, and outcomes
   - Track preparation time and stress levels
   - Log post-event reflections and lessons learned

2. PATTERN ANALYSIS
   - Identify which types of events energize vs drain
   - Find optimal event frequency and duration
   - Detect over-commitment patterns

3. SMART PREPARATION
   - Generate preparation checklists based on event type
   - Suggest optimal timing between events
   - Recommend buffer time for recovery

4. PROACTIVE MANAGEMENT
   - Alert about upcoming events needing preparation
   - Suggest saying no to events that don't align with goals
   - Track social energy budget

Architecture:
- record_event(title, type, duration, attendees): Log event
- get_event_insights(): Get event pattern analysis
- get_preparation_checklist(event_type): Get smart checklist
- get_social_energy_score(): Calculate social energy status
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "event_planner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EVENT_LOG = DATA_DIR / "events.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Event:
    """A tracked event."""
    event_id: str = ""
    title: str = ""
    event_type: str = ""  # social, work, family, celebration, networking, volunteer, personal
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_hours: float = 0.0
    attendees: int = 0
    preparation_time: float = 0.0  # hours spent preparing
    energy_before: float = 5.0  # 1-10
    energy_after: float = 5.0
    satisfaction: float = 0.5
    stress_level: float = 0.3
    location: str = ""
    notes: str = ""
    lessons_learned: List[str] = field(default_factory=list)


@dataclass
class EventPreference:
    """Learned event preferences."""
    event_type: str = ""
    avg_satisfaction: float = 0.5
    avg_energy_change: float = 0.0
    optimal_duration: float = 2.0
    optimal_frequency_days: float = 7.0
    event_count: int = 0


class EventPlanner:
    """
    Intelligent event planner with social energy management.
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
        self._events: deque = deque(maxlen=200)
        self._preferences: Dict[str, EventPreference] = {}
        self._stats = {
            "total_events": 0,
            "avg_satisfaction": 0.5,
            "avg_stress": 0.3,
            "avg_energy_change": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_event(self, title: str = "", event_type: str = "", date: str = "", duration: float = 0, attendees: int = 0, preparation_time: float = 0, energy_before: float = 5.0, energy_after: float = 5.0, satisfaction: float = 0.5, stress_level: float = 0.3, location: str = "", notes: str = "", lessons: Optional[List[str]] = None) -> Event:
        """Record an event."""
        event_id = f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._events)}"
        event = Event(
            event_id=event_id,
            title=title or "untitled",
            event_type=event_type or "social",
            date=date or datetime.now().isoformat(),
            duration_hours=duration,
            attendees=attendees,
            preparation_time=preparation_time,
            energy_before=energy_before,
            energy_after=energy_after,
            satisfaction=satisfaction,
            stress_level=stress_level,
            location=location,
            notes=notes,
            lessons_learned=lessons or [],
        )

        with self._lock:
            self._events.append(event)
            self._stats["total_events"] += 1
            self._update_preferences(event)
            self._update_stats(event)

        self._save_stats()
        self._log_event(event)

        return event

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_event_insights(self, months: int = 6) -> Dict[str, Any]:
        """Get event pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=months * 30)).isoformat()
        recent = [e for e in self._events if e.date > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "satisfaction_sum": 0.0, "energy_change_sum": 0.0, "duration_sum": 0.0})
        for e in recent:
            t = e.event_type
            by_type[t]["count"] += 1
            by_type[t]["satisfaction_sum"] += e.satisfaction
            by_type[t]["energy_change_sum"] += (e.energy_after - e.energy_before)
            by_type[t]["duration_sum"] += e.duration_hours

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            avg_sat = data["satisfaction_sum"] / count
            avg_energy = data["energy_change_sum"] / count
            type_stats[t] = {
                "count": count,
                "avg_satisfaction": round(avg_sat, 2),
                "avg_energy_change": round(avg_energy, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
                "impact": "energizing" if avg_energy > 1 else "draining" if avg_energy < -1 else "neutral",
            }

        # Over-commitment detection
        weekly_events = defaultdict(int)
        for e in recent:
            week = e.date[:7]  # YYYY-MM (approximate week grouping)
            weekly_events[week] += 1

        avg_weekly = sum(weekly_events.values()) / max(1, len(weekly_events))

        # Best and worst event types
        if type_stats:
            best = max(type_stats.items(), key=lambda x: x[1]["avg_satisfaction"])
            worst = min(type_stats.items(), key=lambda x: x[1]["avg_satisfaction"])
        else:
            best = ("", {})
            worst = ("", {})

        return {
            "months_analyzed": months,
            "total_events": len(recent),
            "avg_satisfaction": round(sum(e.satisfaction for e in recent) / len(recent), 2),
            "avg_stress": round(sum(e.stress_level for e in recent) / len(recent), 2),
            "avg_energy_change": round(sum(e.energy_after - e.energy_before for e in recent) / len(recent), 2),
            "type_stats": type_stats,
            "best_type": best[0],
            "worst_type": worst[0],
            "avg_events_per_month": round(avg_weekly, 1),
            "overcommitted": avg_weekly > 8,
        }

    def get_preparation_checklist(self, event_type: str = "", attendees: int = 0, duration: float = 0) -> List[str]:
        """Get smart preparation checklist."""
        checklists = {
            "social": ["Check who's coming", "Plan conversation topics", "Set a time limit for yourself", "Have an exit strategy"],
            "work": ["Review agenda", "Prepare talking points", "Gather materials", "Block calendar after for notes"],
            "family": ["Confirm who's hosting", "Bring something to share", "Set boundaries for duration", "Plan recovery time"],
            "celebration": ["Get gift if needed", "Dress appropriately", "Prepare small talk", "Plan transportation"],
            "networking": ["Research attendees", "Prepare elevator pitch", "Bring business cards", "Set follow-up reminders"],
            "volunteer": ["Confirm location and time", "Dress appropriately", "Bring required items", "Set realistic time commitment"],
            "personal": ["Set intention", "Prepare materials", "Clear distractions", "Plan reflection time after"],
        }

        base = checklists.get(event_type, ["Confirm details", "Prepare mentally", "Plan logistics"])

        if attendees > 10:
            base.append("Arrive early to settle in before crowd")
        if duration > 4:
            base.append("Plan energy breaks or quiet moments")
        if duration > 6:
            base.append("Consider staying only for part of the event")

        return base

    def get_social_energy_score(self) -> int:
        """Calculate social energy status (0-100)."""
        # Recent event impact
        recent = [e for e in self._events if e.date > (datetime.now() - timedelta(days=7)).isoformat()]
        
        if not recent:
            return 70  # Neutral if no recent events

        # Energy depletion from recent events
        energy_changes = [e.energy_after - e.energy_before for e in recent]
        avg_change = sum(energy_changes) / len(energy_changes)
        
        # Stress accumulation
        avg_stress = sum(e.stress_level for e in recent) / len(recent)
        
        # Event density
        daily_count = len(recent) / 7

        # Calculate score (100 = fully energized, 0 = completely drained)
        base_score = 70
        energy_penalty = avg_change * -5  # Negative energy change reduces score
        stress_penalty = avg_stress * 20
        density_penalty = daily_count * 5

        score = base_score + energy_penalty - stress_penalty - density_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_preferences(self, event: Event):
        """Update event type preferences."""
        et = event.event_type
        if et not in self._preferences:
            self._preferences[et] = EventPreference(event_type=et)

        pref = self._preferences[et]
        pref.event_count += 1
        pref.avg_satisfaction = (pref.avg_satisfaction * (pref.event_count - 1) + event.satisfaction) / pref.event_count
        pref.avg_energy_change = (pref.avg_energy_change * (pref.event_count - 1) + (event.energy_after - event.energy_before)) / pref.event_count
        pref.optimal_duration = (pref.optimal_duration * (pref.event_count - 1) + event.duration_hours) / pref.event_count

    def _update_stats(self, event: Event):
        """Update running statistics."""
        n = self._stats["total_events"]
        self._stats["avg_satisfaction"] = round((self._stats["avg_satisfaction"] * (n - 1) + event.satisfaction) / n, 2)
        self._stats["avg_stress"] = round((self._stats["avg_stress"] * (n - 1) + event.stress_level) / n, 2)
        energy_changes = [e.energy_after - e.energy_before for e in self._events]
        if energy_changes:
            self._stats["avg_energy_change"] = round(sum(energy_changes) / len(energy_changes), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "preferences": {k: {
                    "event_type": v.event_type,
                    "avg_satisfaction": v.avg_satisfaction,
                    "avg_energy_change": v.avg_energy_change,
                    "optimal_duration": v.optimal_duration,
                    "optimal_frequency_days": v.optimal_frequency_days,
                    "event_count": v.event_count,
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
                    self._preferences[k] = EventPreference(**v)
        except Exception:
            pass

    def _log_event(self, event: Event):
        try:
            with open(EVENT_LOG, "a") as f:
                f.write(json.dumps({
                    "event_id": event.event_id,
                    "title": event.title,
                    "type": event.event_type,
                    "date": event.date,
                    "duration": event.duration_hours,
                    "attendees": event.attendees,
                    "satisfaction": event.satisfaction,
                    "stress": event.stress_level,
                    "energy_change": event.energy_after - event.energy_before,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ep_instance: Optional[EventPlanner] = None
_ep_lock = threading.Lock()


def get_event_planner() -> EventPlanner:
    global _ep_instance
    with _ep_lock:
        if _ep_instance is None:
            _ep_instance = EventPlanner()
        return _ep_instance
