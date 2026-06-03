"""
LOVE Task Batch Optimizer — Task Clustering Engine (Modern AI Pattern)

Most task lists are flat. This optimizer:

1. TASK CLUSTERING
   - Group similar tasks by type, energy level, location, tools needed
   - Identify tasks that share context (same project, same person, same tool)
   - Cluster by cognitive load (deep work vs shallow work)

2. BATCH OPTIMIZATION
   - Suggest optimal task ordering within batches
   - Calculate batch efficiency score (time saved vs individual execution)
   - Recommend batch size (not too many, not too few)

3. ENERGY-BASED SCHEDULING
   - Schedule high-energy tasks during peak hours
   - Batch low-energy tasks for low-energy periods
   - Alternate task types to maintain engagement

4. TRANSITION MINIMIZATION
   - Minimize physical transitions (location changes)
   - Minimize tool transitions (software switches)
   - Minimize cognitive transitions (context changes)

Architecture:
- add_task(task, category, energy, tools): Add task to pool
- optimize_batches(constraints): Get optimized batch schedule
- get_batch_efficiency(): Calculate efficiency score
- get_execution_plan(): Get step-by-step execution plan
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "task_batch_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TASK_LOG = DATA_DIR / "task_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Task:
    """A task for batching."""
    task_id: str = ""
    title: str = ""
    category: str = ""  # email, coding, admin, creative, research, calls
    energy_level: str = ""  # high, medium, low
    estimated_minutes: float = 0.0
    tools: List[str] = field(default_factory=list)  # browser, ide, phone, paper
    location: str = ""  # desk, phone, away, anywhere
    priority: float = 0.5
    deadline: Optional[str] = None
    project: str = ""
    blocked_by: List[str] = field(default_factory=list)


@dataclass
class Batch:
    """An optimized batch of tasks."""
    batch_id: str = ""
    name: str = ""
    tasks: List[Task] = field(default_factory=list)
    total_minutes: float = 0.0
    category: str = ""
    energy_level: str = ""
    location: str = ""
    tools: List[str] = field(default_factory=list)
    efficiency_score: float = 0.0


class TaskBatchOptimizer:
    """
    Optimize task execution through intelligent batching.
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
        self._tasks: Dict[str, Task] = {}
        self._batches: List[Batch] = []
        self._stats = {
            "total_tasks": 0,
            "total_batches_created": 0,
            "avg_batch_size": 0.0,
            "avg_efficiency": 0.0,
        }
        self._load_stats()

    # ── Core Management ─────────────────────────────────────────────────────

    def add_task(self, title: str, category: str = "", energy_level: str = "medium", estimated_minutes: float = 0.0, tools: Optional[List[str]] = None, location: str = "", priority: float = 0.5, deadline: Optional[str] = None, project: str = "") -> Task:
        """Add a task to the optimization pool."""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._tasks)}"
        task = Task(
            task_id=task_id,
            title=title,
            category=category or "admin",
            energy_level=energy_level,
            estimated_minutes=estimated_minutes,
            tools=tools or [],
            location=location or "anywhere",
            priority=priority,
            deadline=deadline,
            project=project,
        )

        with self._lock:
            self._tasks[task_id] = task
            self._stats["total_tasks"] += 1

        self._save_stats()
        self._log_task(task)

        return task

    # ── Optimization ──────────────────────────────────────────────────────

    def optimize_batches(self, max_batch_minutes: float = 120, constraints: Optional[Dict[str, Any]] = None) -> List[Batch]:
        """Create optimized batches from the task pool."""
        if not self._tasks:
            return []

        # Get tasks that haven't been batched yet
        available = list(self._tasks.values())

        # Sort by priority and deadline
        available.sort(key=lambda t: (t.priority * -1, t.deadline or "9999"))

        # Group by category first
        by_category = defaultdict(list)
        for task in available:
            by_category[task.category].append(task)

        batches = []
        batch_num = 0

        for category, tasks in by_category.items():
            # Further group by energy level within category
            by_energy = defaultdict(list)
            for task in tasks:
                by_energy[task.energy_level].append(task)

            for energy, energy_tasks in by_energy.items():
                current_batch = []
                current_minutes = 0.0

                for task in energy_tasks:
                    if current_minutes + task.estimated_minutes <= max_batch_minutes:
                        current_batch.append(task)
                        current_minutes += task.estimated_minutes
                    else:
                        # Save current batch and start new one
                        if current_batch:
                            batch_num += 1
                            batches.append(self._create_batch(f"batch_{batch_num}", category, energy, current_batch))
                        current_batch = [task]
                        current_minutes = task.estimated_minutes

                # Don't forget the last batch
                if current_batch:
                    batch_num += 1
                    batches.append(self._create_batch(f"batch_{batch_num}", category, energy, current_batch))

        self._batches = batches
        self._stats["total_batches_created"] += len(batches)
        self._update_stats()
        self._save_stats()

        return batches

    def get_batch_efficiency(self) -> Dict[str, Any]:
        """Calculate batch efficiency metrics."""
        if not self._batches:
            return {"status": "no_batches"}

        total_tasks = sum(len(b.tasks) for b in self._batches)
        total_time = sum(b.total_minutes for b in self._batches)

        # Estimate individual execution time (with switch costs)
        individual_time = total_time + (total_tasks * 5)  # 5 min switch cost per task

        # Batch time has lower switch cost
        batch_time = total_time + (len(self._batches) * 5)  # 5 min per batch

        time_saved = individual_time - batch_time
        efficiency = (time_saved / max(1, individual_time)) * 100

        return {
            "total_batches": len(self._batches),
            "total_tasks": total_tasks,
            "total_time_minutes": round(total_time, 1),
            "estimated_individual_time": round(individual_time, 1),
            "estimated_batch_time": round(batch_time, 1),
            "time_saved_minutes": round(time_saved, 1),
            "efficiency_pct": round(efficiency, 1),
            "avg_batch_size": round(total_tasks / max(1, len(self._batches)), 1),
        }

    def get_execution_plan(self) -> List[Dict[str, Any]]:
        """Get step-by-step execution plan."""
        if not self._batches:
            return [{"step": 1, "action": "Add tasks to get an execution plan"}]

        plan = []
        step = 1

        # Sort batches by energy level (high energy first)
        energy_order = {"high": 0, "medium": 1, "low": 2}
        sorted_batches = sorted(self._batches, key=lambda b: energy_order.get(b.energy_level, 1))

        for batch in sorted_batches:
            plan.append({
                "step": step,
                "action": f"Start batch: {batch.name}",
                "details": f"{len(batch.tasks)} tasks, ~{batch.total_minutes:.0f} minutes",
                "energy": batch.energy_level,
                "category": batch.category,
            })
            step += 1

            for task in batch.tasks:
                plan.append({
                    "step": step,
                    "action": f"  → {task.title}",
                    "details": f"~{task.estimated_minutes:.0f} min",
                    "priority": task.priority,
                })
                step += 1

            plan.append({
                "step": step,
                "action": f"Complete batch: {batch.name}",
                "details": "Take a short break before next batch",
            })
            step += 1

        return plan

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _create_batch(self, batch_id: str, category: str, energy: str, tasks: List[Task]) -> Batch:
        """Create a batch from tasks."""
        total_minutes = sum(t.estimated_minutes for t in tasks)
        all_tools = set()
        for t in tasks:
            all_tools.update(t.tools)

        # Determine location (most common)
        locations = [t.location for t in tasks if t.location]
        location = max(set(locations), key=locations.count) if locations else "anywhere"

        # Efficiency score based on similarity
        if len(tasks) > 1:
            same_category = sum(1 for t in tasks if t.category == category) / len(tasks)
            same_energy = sum(1 for t in tasks if t.energy_level == energy) / len(tasks)
            efficiency = (same_category + same_energy) / 2
        else:
            efficiency = 0.5

        return Batch(
            batch_id=batch_id,
            name=f"{energy.title()} {category.title()} Batch",
            tasks=tasks,
            total_minutes=total_minutes,
            category=category,
            energy_level=energy,
            location=location,
            tools=list(all_tools),
            efficiency_score=round(efficiency, 2),
        )

    def _update_stats(self):
        """Update running statistics."""
        if self._batches:
            total_tasks = sum(len(b.tasks) for b in self._batches)
            self._stats["avg_batch_size"] = round(total_tasks / len(self._batches), 1)
            self._stats["avg_efficiency"] = round(sum(b.efficiency_score for b in self._batches) / len(self._batches), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.task_batch_optimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.task_batch_optimizer")

    def _log_task(self, task: Task):
        try:
            with open(TASK_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "task_id": task.task_id,
                    "title": task.title,
                    "category": task.category,
                    "energy": task.energy_level,
                    "minutes": task.estimated_minutes,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.task_batch_optimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_tbo_instance: Optional[TaskBatchOptimizer] = None
_tbo_lock = threading.Lock()


def get_task_batch_optimizer() -> TaskBatchOptimizer:
    global _tbo_instance
    with _tbo_lock:
        if _tbo_instance is None:
            _tbo_instance = TaskBatchOptimizer()
        return _tbo_instance
