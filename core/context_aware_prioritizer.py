"""
LOVE Context-Aware Task Prioritizer — Intelligent Task Ordering (Modern AI Pattern)

Traditional task lists are static. This prioritizer reorders tasks based on:

1. USER CONTEXT
   - Current energy level (high energy = hard tasks, low = easy tasks)
   - Time of day (morning person vs night owl)
   - Location (home, work, commute)
   - Emotional state (stressed = avoid complex tasks)

2. TASK CHARACTERISTICS
   - Urgency (deadlines, dependencies)
   - Importance (alignment with goals)
   - Cognitive load (easy vs complex)
   - Duration (quick wins vs long tasks)

3. DYNAMIC REORDERING
   - Re-prioritize when context changes
   - Suggest task switches based on energy shifts
   - Block time for deep work when focus is high

4. PROACTIVE SUGGESTIONS
   - Suggest next task based on current state
   - Warn about approaching deadlines
   - Recommend breaks before burnout

Architecture:
- prioritize_tasks(tasks, context): Reorder tasks by context
- suggest_next_task(tasks, context): Recommend single next task
- get_prioritization_stats(): Track effectiveness
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

DATA_DIR = Path(__file__).parent.parent / "data" / "context_aware_prioritizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRIORITIZATION_LOG = DATA_DIR / "prioritization_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class UserContext:
    """Current user context for prioritization."""
    energy_level: float = 0.5  # 0 = exhausted, 1 = peak
    time_of_day: str = "morning"  # morning, afternoon, evening, night
    location: str = "unknown"  # home, work, commute, outdoors
    emotional_state: str = "neutral"  # happy, stressed, anxious, tired, focused
    focus_depth: float = 0.5  # 0 = distracted, 1 = deep focus
    available_time_minutes: int = 60
    work_limit_hours: float = 8.0
    work_done_today_hours: float = 0.0


@dataclass
class Task:
    """A task with prioritization attributes."""
    id: str = ""
    title: str = ""
    urgency: float = 0.5  # 0 = low, 1 = critical
    importance: float = 0.5
    cognitive_load: float = 0.5  # 0 = easy, 1 = complex
    estimated_minutes: int = 30
    deadline: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    completed: bool = False


@dataclass
class PrioritizedTask:
    """A task with calculated priority score."""
    task: Task = field(default_factory=Task)
    priority_score: float = 0.0
    reason: str = ""
    suggested_time: str = ""


class ContextAwarePrioritizer:
    """
    Dynamically prioritize tasks based on user context.
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
            "total_prioritizations": 0,
            "tasks_completed": 0,
            "avg_satisfaction": 0.0,
        }
        self._feedback_window: deque = deque(maxlen=100)
        self._load_stats()

    # ── Core Prioritization ─────────────────────────────────────────────────

    def prioritize_tasks(self, tasks: List[Task], context: Optional[UserContext] = None) -> List[PrioritizedTask]:
        """Reorder tasks based on user context."""
        if context is None:
            context = self._gather_context()

        if not tasks:
            return []

        prioritized = []
        for task in tasks:
            if task.completed:
                continue

            score = self._calculate_priority(task, context)
            reason = self._generate_reason(task, context, score)
            suggested_time = self._suggest_time(task, context)

            prioritized.append(PrioritizedTask(
                task=task,
                priority_score=round(score, 3),
                reason=reason,
                suggested_time=suggested_time,
            ))

        # Sort by priority score descending
        prioritized.sort(key=lambda x: x.priority_score, reverse=True)

        with self._lock:
            self._stats["total_prioritizations"] += 1

        self._save_stats()
        self._log_prioritization(prioritized, context)

        return prioritized

    def suggest_next_task(self, tasks: List[Task], context: Optional[UserContext] = None) -> Optional[PrioritizedTask]:
        """Suggest the single best next task."""
        prioritized = self.prioritize_tasks(tasks, context)
        if not prioritized:
            return None
        return prioritized[0]

    # ── Priority Calculation ────────────────────────────────────────────────

    def _calculate_priority(self, task: Task, context: UserContext) -> float:
        """Calculate priority score for a task."""
        # Base scores
        urgency_score = task.urgency
        importance_score = task.importance

        # Context alignment
        energy_alignment = self._energy_alignment(task.cognitive_load, context.energy_level)
        time_alignment = self._time_alignment(task.estimated_minutes, context.available_time_minutes)
        emotional_alignment = self._emotional_alignment(task.cognitive_load, context.emotional_state)
        focus_alignment = self._focus_alignment(task.cognitive_load, context.focus_depth)

        # Deadline pressure
        deadline_score = self._deadline_score(task.deadline)

        # Work limit consideration
        work_limit_factor = 1.0
        if context.work_done_today_hours >= context.work_limit_hours:
            work_limit_factor = 0.3  # Strongly deprioritize work tasks
        elif context.work_done_today_hours >= context.work_limit_hours * 0.8:
            work_limit_factor = 0.7

        # Combine scores
        score = (
            urgency_score * 0.25 +
            importance_score * 0.20 +
            energy_alignment * 0.15 +
            time_alignment * 0.10 +
            emotional_alignment * 0.10 +
            focus_alignment * 0.10 +
            deadline_score * 0.10
        ) * work_limit_factor

        return min(1.0, max(0.0, score))

    def _energy_alignment(self, cognitive_load: float, energy: float) -> float:
        """Score how well task matches energy level."""
        # High energy = good for high cognitive load
        # Low energy = good for low cognitive load
        diff = abs(cognitive_load - energy)
        return 1.0 - diff

    def _time_alignment(self, estimated_minutes: int, available_minutes: int) -> float:
        """Score how well task fits available time."""
        if estimated_minutes <= available_minutes:
            return 1.0
        elif estimated_minutes <= available_minutes * 1.5:
            return 0.5
        else:
            return 0.0

    def _emotional_alignment(self, cognitive_load: float, emotional_state: str) -> float:
        """Score how well task matches emotional state."""
        if emotional_state in ("stressed", "anxious", "tired"):
            # Prefer low cognitive load when stressed
            return 1.0 - cognitive_load * 0.5
        elif emotional_state == "focused":
            # Good for any cognitive load
            return 1.0
        else:
            return 0.7

    def _focus_alignment(self, cognitive_load: float, focus_depth: float) -> float:
        """Score how well task matches focus depth."""
        # High focus + high cognitive load = great match
        # Low focus + high cognitive load = poor match
        return 1.0 - abs(cognitive_load - focus_depth) * 0.5

    def _deadline_score(self, deadline: Optional[str]) -> float:
        """Score urgency based on deadline."""
        if not deadline:
            return 0.5
        try:
            deadline_dt = datetime.fromisoformat(deadline)
            hours_until = (deadline_dt - datetime.now()).total_seconds() / 3600
            if hours_until < 0:
                return 1.0  # Overdue
            elif hours_until < 24:
                return 0.9
            elif hours_until < 72:
                return 0.7
            elif hours_until < 168:
                return 0.5
            else:
                return 0.3
        except Exception:
            return 0.5

    # ── Context Gathering ─────────────────────────────────────────────────

    def _gather_context(self) -> UserContext:
        """Gather current user context."""
        now = datetime.now()
        hour = now.hour

        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        # Try to get work hours from settings
        work_limit = 8.0
        work_done = 0.0
        try:
            from core.settings import get_settings
            settings = get_settings()
            work_limit = getattr(settings, 'WORK_LIMIT_HOURS', 8.0)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.context_aware_prioritizer")

        return UserContext(
            time_of_day=time_of_day,
            work_limit_hours=work_limit,
            work_done_today_hours=work_done,
        )

    # ── Reason Generation ─────────────────────────────────────────────────

    def _generate_reason(self, task: Task, context: UserContext, score: float) -> str:
        """Generate human-readable reason for priority."""
        reasons = []

        if task.urgency > 0.7:
            reasons.append("urgent")
        if task.importance > 0.7:
            reasons.append("important")
        if context.energy_level > 0.6 and task.cognitive_load > 0.6:
            reasons.append("matches your high energy")
        if context.energy_level < 0.4 and task.cognitive_load < 0.4:
            reasons.append("easy task for low energy")
        if task.deadline:
            try:
                deadline_dt = datetime.fromisoformat(task.deadline)
                hours_until = (deadline_dt - datetime.now()).total_seconds() / 3600
                if hours_until < 24:
                    reasons.append("due soon")
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.context_aware_prioritizer")

        if not reasons:
            reasons.append("aligned with current context")

        return ", ".join(reasons)

    def _suggest_time(self, task: Task, context: UserContext) -> str:
        """Suggest when to do the task."""
        if task.estimated_minutes <= 15:
            return "now (quick win)"
        elif context.energy_level > 0.7 and task.cognitive_load > 0.6:
            return "now (high energy + complex task)"
        elif context.time_of_day in ("morning", "afternoon"):
            return "this afternoon"
        else:
            return "tomorrow morning"

    # ── Feedback ──────────────────────────────────────────────────────────

    def record_task_completion(self, task_id: str, satisfaction: float):
        """Record task completion feedback."""
        self._feedback_window.append({
            "task_id": task_id,
            "satisfaction": satisfaction,
            "timestamp": datetime.now().isoformat(),
        })
        self._stats["tasks_completed"] += 1
        prev_avg = self._stats.get("avg_satisfaction", 0)
        n = self._stats["tasks_completed"]
        self._stats["avg_satisfaction"] = round((prev_avg * (n - 1) + satisfaction) / max(1, n), 2)
        self._save_stats()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_prioritization_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "recent_feedback": list(self._feedback_window)[-10:],
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.context_aware_prioritizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.context_aware_prioritizer")

    def _log_prioritization(self, prioritized: List[PrioritizedTask], context: UserContext):
        try:
            with open(PRIORITIZATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "task_count": len(prioritized),
                    "energy_level": context.energy_level,
                    "emotional_state": context.emotional_state,
                    "top_task": prioritized[0].task.title if prioritized else "",
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.context_aware_prioritizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cap_instance: Optional[ContextAwarePrioritizer] = None
_cap_lock = threading.Lock()


def get_context_aware_prioritizer() -> ContextAwarePrioritizer:
    global _cap_instance
    with _cap_lock:
        if _cap_instance is None:
            _cap_instance = ContextAwarePrioritizer()
        return _cap_instance
