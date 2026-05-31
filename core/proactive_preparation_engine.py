"""
LOVE Proactive Preparation Engine — Anticipatory Intelligence (Modern AI Pattern)

Most systems react. This engine prepares:

1. CONTEXT GATHERING
   - Scan calendar, tasks, and messages for upcoming events
   - Identify what preparation is needed for each event
   - Gather relevant context (docs, contacts, previous notes)

2. PREPARATION SUGGESTIONS
   - Suggest prep work before meetings (review agenda, attendees)
   - Suggest packing lists before travel
   - Suggest prep time blocks before important events

3. TIMING OPTIMIZATION
   - Calculate optimal prep time (not too early, not too late)
   - Account for context switching cost between prep and event
   - Batch prep work for multiple events when possible

4. PROACTIVE REMINDERS
   - Nudge when prep hasn't started with enough lead time
   - Escalate urgency as event approaches
   - Suggest cancellation/postponement if prep is impossible

Architecture:
- scan_upcoming_events(hours_ahead): Find events needing prep
- suggest_preparation(event): Get prep checklist
- get_prep_timeline(): Get optimal prep schedule
- check_prep_status(): Verify prep completion
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "proactive_preparation"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PREP_LOG = DATA_DIR / "prep_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PrepTask:
    """A preparation task."""
    task: str = ""
    event_id: str = ""
    event_title: str = ""
    due_before: str = ""
    estimated_minutes: float = 0.0
    priority: str = "medium"  # low, medium, high, critical
    completed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UpcomingEvent:
    """An upcoming event requiring preparation."""
    event_id: str = ""
    title: str = ""
    start_time: str = ""
    event_type: str = ""  # meeting, travel, deadline, presentation
    prep_needed: List[str] = field(default_factory=list)
    urgency: str = "low"
    context_items: List[str] = field(default_factory=list)


class ProactivePreparationEngine:
    """
    Anticipate upcoming events and suggest proactive preparation.
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
        self._prep_tasks: deque = deque(maxlen=200)
        self._stats = {
            "total_prep_tasks": 0,
            "completed_prep_tasks": 0,
            "events_prepared": 0,
            "avg_prep_time": 0.0,
        }
        self._load_stats()

    # ── Core Scanning ─────────────────────────────────────────────────────

    def scan_upcoming_events(self, hours_ahead: int = 24) -> List[UpcomingEvent]:
        """Scan for upcoming events needing preparation."""
        events = []
        now = datetime.now()
        cutoff = (now + timedelta(hours=hours_ahead)).isoformat()

        # Scan calendar
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            if gs.is_connected():
                cal_events = gs.get_upcoming_events(hours_ahead)
                for evt in cal_events:
                    events.append(self._analyze_event(evt))
        except Exception:
            pass

        # Scan tasks
        try:
            from core.autonomous_goal_engine import get_goal_status
            goals = get_goal_status()
            for goal in goals.get("goals", []):
                if goal.get("deadline") and goal["deadline"] < cutoff:
                    events.append(UpcomingEvent(
                        event_id=f"goal_{goal['id']}",
                        title=goal.get("name", "Goal deadline"),
                        start_time=goal["deadline"],
                        event_type="deadline",
                        prep_needed=["review progress", "plan final push"],
                        urgency="high" if goal["deadline"] < (now + timedelta(hours=4)).isoformat() else "medium",
                    ))
        except Exception:
            pass

        return events

    def suggest_preparation(self, event: UpcomingEvent) -> List[PrepTask]:
        """Generate preparation tasks for an event."""
        tasks = []
        event_time = datetime.fromisoformat(event.start_time)
        now = datetime.now()
        hours_until = (event_time - now).total_seconds() / 3600

        # Determine urgency
        if hours_until < 2:
            urgency = "critical"
        elif hours_until < 8:
            urgency = "high"
        elif hours_until < 24:
            urgency = "medium"
        else:
            urgency = "low"

        # Event-specific prep
        if event.event_type == "meeting":
            tasks.append(PrepTask(
                task="Review agenda and attendee list",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(minutes=15)).isoformat(),
                estimated_minutes=5,
                priority=urgency,
            ))
            tasks.append(PrepTask(
                task="Prepare 2-3 talking points or questions",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(minutes=10)).isoformat(),
                estimated_minutes=10,
                priority=urgency,
            ))

        elif event.event_type == "presentation":
            tasks.append(PrepTask(
                task="Review slides and key messages",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(hours=1)).isoformat(),
                estimated_minutes=20,
                priority=urgency,
            ))
            tasks.append(PrepTask(
                task="Test tech setup (screen share, audio)",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(minutes=15)).isoformat(),
                estimated_minutes=5,
                priority=urgency,
            ))

        elif event.event_type == "travel":
            tasks.append(PrepTask(
                task="Check packing list and weather",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(hours=2)).isoformat(),
                estimated_minutes=15,
                priority=urgency,
            ))
            tasks.append(PrepTask(
                task="Confirm transport and accommodation",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(hours=4)).isoformat(),
                estimated_minutes=5,
                priority=urgency,
            ))

        elif event.event_type == "deadline":
            tasks.append(PrepTask(
                task="Review current progress vs target",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(hours=2)).isoformat(),
                estimated_minutes=10,
                priority=urgency,
            ))
            tasks.append(PrepTask(
                task="Identify blockers and contingency plan",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(hours=1)).isoformat(),
                estimated_minutes=15,
                priority=urgency,
            ))

        else:
            tasks.append(PrepTask(
                task=f"Prepare for {event.title}",
                event_id=event.event_id,
                event_title=event.title,
                due_before=(event_time - timedelta(minutes=15)).isoformat(),
                estimated_minutes=10,
                priority=urgency,
            ))

        # Store tasks
        for task in tasks:
            with self._lock:
                self._prep_tasks.append(task)
                self._stats["total_prep_tasks"] += 1
            self._log_task(task)

        self._save_stats()
        return tasks

    # ── Timeline & Status ────────────────────────────────────────────────

    def get_prep_timeline(self) -> List[Dict[str, Any]]:
        """Get optimal preparation schedule."""
        events = self.scan_upcoming_events(48)
        timeline = []

        for event in events:
            event_time = datetime.fromisoformat(event.start_time)
            now = datetime.now()
            hours_until = max(0, (event_time - now).total_seconds() / 3600)

            # Calculate optimal prep window
            if hours_until > 24:
                prep_window = "today or tomorrow"
            elif hours_until > 8:
                prep_window = "this evening"
            elif hours_until > 2:
                prep_window = "in the next few hours"
            else:
                prep_window = "RIGHT NOW"

            timeline.append({
                "event": event.title,
                "start_time": event.start_time,
                "hours_until": round(hours_until, 1),
                "prep_window": prep_window,
                "prep_tasks": len(self.suggest_preparation(event)),
                "urgency": event.urgency,
            })

        return sorted(timeline, key=lambda x: x["hours_until"])

    def check_prep_status(self, event_id: str) -> Dict[str, Any]:
        """Check preparation status for a specific event."""
        tasks = [t for t in self._prep_tasks if t.event_id == event_id]
        completed = sum(1 for t in tasks if t.completed)
        total = len(tasks)

        return {
            "event_id": event_id,
            "total_tasks": total,
            "completed": completed,
            "pending": total - completed,
            "ready": completed == total and total > 0,
            "completion_pct": round(completed / max(1, total) * 100, 1),
            "pending_tasks": [
                {"task": t.task, "due": t.due_before, "priority": t.priority}
                for t in tasks if not t.completed
            ],
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _analyze_event(self, evt: Dict[str, Any]) -> UpcomingEvent:
        """Analyze a calendar event to determine prep needs."""
        title = evt.get("summary", "").lower()
        event_type = "meeting"

        if any(word in title for word in ["flight", "travel", "trip", "hotel"]):
            event_type = "travel"
        elif any(word in title for word in ["present", "demo", "pitch", "talk"]):
            event_type = "presentation"
        elif any(word in title for word in ["deadline", "due", "submit", "deliver"]):
            event_type = "deadline"

        return UpcomingEvent(
            event_id=evt.get("id", ""),
            title=evt.get("summary", "Event"),
            start_time=evt.get("start", {}).get("dateTime", datetime.now().isoformat()),
            event_type=event_type,
            prep_needed=[],
            urgency="medium",
        )

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

    def _log_task(self, task: PrepTask):
        try:
            with open(PREP_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": task.timestamp,
                    "task": task.task,
                    "event": task.event_title,
                    "priority": task.priority,
                    "completed": task.completed,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ppe_instance: Optional[ProactivePreparationEngine] = None
_ppe_lock = threading.Lock()


def get_proactive_preparation_engine() -> ProactivePreparationEngine:
    global _ppe_instance
    with _ppe_lock:
        if _ppe_instance is None:
            _ppe_instance = ProactivePreparationEngine()
        return _ppe_instance
