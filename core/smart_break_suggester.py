"""
LOVE Smart Break Suggester — Optimal Break Timing (Modern AI Pattern)

Breaks taken at the right time boost productivity. This suggester:

1. BREAK TIMING OPTIMIZATION
   - Suggest breaks before energy crashes
   - Time breaks after natural task completion points
   - Adapt break frequency to cognitive load

2. BREAK TYPE RECOMMENDATION
   - Micro-break (2-5 min) for quick resets
   - Movement break (10-15 min) for physical recovery
   - Deep rest (20-30 min) for cognitive recovery
   - Social break for emotional recharging

3. PERSONALIZED SCHEDULING
   - Learn user's break preferences and effectiveness
   - Adjust for chronotype (morning/evening person)
   - Consider upcoming calendar events

4. PROACTIVE REMINDERS
   - Detect when user has been working too long without breaks
   - Warn before burnout rather than after
   - Suggest recovery activities based on current state

Architecture:
- suggest_break(context): Recommend break timing and type
- get_optimal_schedule(tasks): Build task+break schedule
- record_break_effectiveness(break_id, effect): Learn from feedback
- get_break_stats(): Track break effectiveness
"""

import json
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "smart_break_suggester"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BREAK_LOG = DATA_DIR / "break_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BreakSuggestion:
    """A suggested break."""
    id: str = ""
    suggested_at: str = field(default_factory=lambda: datetime.now().isoformat())
    break_type: str = "micro"  # micro, movement, deep_rest, social
    duration_minutes: int = 5
    reason: str = ""
    urgency: str = "suggested"  # suggested, recommended, required
    activities: List[str] = field(default_factory=list)
    expected_benefit: str = ""


@dataclass
class BreakRecord:
    """A recorded break."""
    break_id: str = ""
    break_type: str = ""
    planned_duration: int = 0
    actual_duration: float = 0.0
    taken_at: str = ""
    ended_at: Optional[str] = None
    effectiveness: float = 0.5  # 0-1, self-reported or inferred
    activities_done: List[str] = field(default_factory=list)


class SmartBreakSuggester:
    """
    Suggest optimal break timing and type.
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
        self._stats = {
            "total_breaks_suggested": 0,
            "total_breaks_taken": 0,
            "avg_effectiveness": 0.0,
            "optimal_break_interval": 60,  # minutes
        }
        self._break_history: deque = deque(maxlen=200)
        self._last_break_time: Optional[datetime] = None
        self._load_stats()

    # ── Core Suggestion ───────────────────────────────────────────────────

    def suggest_break(self, context: Optional[Dict[str, Any]] = None) -> Optional[BreakSuggestion]:
        """Suggest a break based on current context."""
        if context is None:
            context = {}

        # Check if break is warranted
        work_minutes = context.get("work_minutes_since_break", 0)
        cognitive_load = context.get("cognitive_load", 0.5)
        energy_level = context.get("energy_level", 0.5)
        stress_level = context.get("stress_level", 0.0)

        # Calculate break urgency
        urgency_score = 0.0
        reason_parts = []

        if work_minutes > 90:
            urgency_score += 0.3
            reason_parts.append(f"working for {work_minutes} minutes")

        if cognitive_load > 0.7:
            urgency_score += 0.25
            reason_parts.append("high cognitive load")

        if energy_level < 0.4:
            urgency_score += 0.3
            reason_parts.append("low energy")

        if stress_level > 0.6:
            urgency_score += 0.15
            reason_parts.append("elevated stress")

        if self._last_break_time:
            minutes_since = (datetime.now() - self._last_break_time).total_seconds() / 60
            optimal = self._stats.get("optimal_break_interval", 60)
            if minutes_since > optimal * 1.5:
                urgency_score += 0.2
                reason_parts.append("overdue for break")

        if urgency_score < 0.3:
            return None  # No break needed yet

        # Determine break type
        break_type, duration, activities, benefit = self._determine_break_type(
            cognitive_load, energy_level, stress_level, work_minutes
        )

        urgency = "required" if urgency_score > 0.8 else "recommended" if urgency_score > 0.5 else "suggested"

        suggestion = BreakSuggestion(
            id=f"break_{int(time.time())}",
            break_type=break_type,
            duration_minutes=duration,
            reason="; ".join(reason_parts),
            urgency=urgency,
            activities=activities,
            expected_benefit=benefit,
        )

        with self._lock:
            self._stats["total_breaks_suggested"] += 1

        self._save_stats()
        self._log_suggestion(suggestion)

        return suggestion

    def get_optimal_schedule(self, tasks: List[Dict[str, Any]], start_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Build an optimal task+break schedule."""
        if start_time is None:
            start_time = datetime.now()

        schedule = []
        current_time = start_time
        optimal_interval = self._stats.get("optimal_break_interval", 60)

        for i, task in enumerate(tasks):
            duration = task.get("estimated_minutes", 30)

            # Add task
            schedule.append({
                "type": "task",
                "title": task.get("title", "Task"),
                "start": current_time.isoformat(),
                "end": (current_time + timedelta(minutes=duration)).isoformat(),
                "duration": duration,
            })
            current_time += timedelta(minutes=duration)

            # Add break after task (except last, and if not too short)
            if i < len(tasks) - 1 and duration >= 15:
                break_duration = 5 if i % 2 == 0 else 15  # Micro then longer
                schedule.append({
                    "type": "break",
                    "break_type": "micro" if break_duration <= 5 else "movement",
                    "start": current_time.isoformat(),
                    "end": (current_time + timedelta(minutes=break_duration)).isoformat(),
                    "duration": break_duration,
                    "reason": "maintain productivity",
                })
                current_time += timedelta(minutes=break_duration)

        return schedule

    # ── Break Type Determination ──────────────────────────────────────────

    def _determine_break_type(self, cognitive_load: float, energy: float, stress: float, work_minutes: int) -> tuple:
        """Determine best break type based on context."""
        if energy < 0.2 or stress > 0.8:
            return "deep_rest", 20, ["close eyes", "breathe deeply", "no screens"], "Restore cognitive resources"
        elif work_minutes > 120 or cognitive_load > 0.8:
            return "movement", 15, ["walk", "stretch", "look at distant objects"], "Physical and mental recovery"
        elif stress > 0.5:
            return "social", 10, ["message a friend", "step outside", "people watch"], "Emotional recharging"
        else:
            return "micro", 5, ["stand up", "stretch shoulders", "drink water"], "Quick reset"

    # ── Effectiveness Tracking ────────────────────────────────────────────

    def record_break_taken(self, suggestion_id: str, break_type: str, planned_duration: int, actual_duration: float, activities: List[str]):
        """Record that a break was taken."""
        record = BreakRecord(
            break_id=suggestion_id,
            break_type=break_type,
            planned_duration=planned_duration,
            actual_duration=actual_duration,
            taken_at=datetime.now().isoformat(),
            activities_done=activities,
        )

        self._break_history.append(record)
        self._last_break_time = datetime.now()

        with self._lock:
            self._stats["total_breaks_taken"] += 1

        self._save_stats()
        self._log_break(record)

    def record_break_effectiveness(self, break_id: str, effectiveness: float, post_break_energy: float):
        """Record how effective the break was."""
        for record in self._break_history:
            if record.break_id == break_id:
                record.effectiveness = effectiveness
                record.ended_at = datetime.now().isoformat()
                break

        # Update optimal break interval based on effectiveness
        if effectiveness > 0.7:
            current = self._stats.get("optimal_break_interval", 60)
            # Slightly extend interval if breaks are very effective
            self._stats["optimal_break_interval"] = min(90, current + 1)
        elif effectiveness < 0.4:
            current = self._stats.get("optimal_break_interval", 60)
            # Shorten interval if breaks aren't helping
            self._stats["optimal_break_interval"] = max(30, current - 2)

        # Update average effectiveness
        prev_avg = self._stats.get("avg_effectiveness", 0)
        n = self._stats["total_breaks_taken"]
        self._stats["avg_effectiveness"] = round((prev_avg * (n - 1) + effectiveness) / max(1, n), 2)

        self._save_stats()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_break_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "last_break": self._last_break_time.isoformat() if self._last_break_time else None,
            "recent_breaks": [{
                "type": r.break_type,
                "effectiveness": r.effectiveness,
                "planned": r.planned_duration,
                "actual": r.actual_duration,
            } for r in list(self._break_history)[-10:]],
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.smart_break_suggester")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.smart_break_suggester")

    def _log_suggestion(self, suggestion: BreakSuggestion):
        try:
            with open(BREAK_LOG, "a") as f:
                f.write(json.dumps({
                    "event": "suggested",
                    "timestamp": suggestion.suggested_at,
                    "break_id": suggestion.id,
                    "type": suggestion.break_type,
                    "urgency": suggestion.urgency,
                    "reason": suggestion.reason[:100],
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.smart_break_suggester")

    def _log_break(self, record: BreakRecord):
        try:
            with open(BREAK_LOG, "a") as f:
                f.write(json.dumps({
                    "event": "taken",
                    "timestamp": record.taken_at,
                    "break_id": record.break_id,
                    "type": record.break_type,
                    "planned": record.planned_duration,
                    "actual": record.actual_duration,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.smart_break_suggester")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sbs_instance: Optional[SmartBreakSuggester] = None
_sbs_lock = threading.Lock()


def get_smart_break_suggester() -> SmartBreakSuggester:
    global _sbs_instance
    with _sbs_lock:
        if _sbs_instance is None:
            _sbs_instance = SmartBreakSuggester()
        return _sbs_instance
