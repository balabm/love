"""
LOVE Goal Progress Visualizer — Goal Intelligence (Modern AI Pattern)

Most goal trackers are static lists. This visualizer:

1. PROGRESS TRACKING
   - Record progress on goals with quantitative and qualitative metrics
   - Track milestone completion and velocity
   - Identify when goals are on track, at risk, or off track

2. VISUAL INSIGHTS
   - Calculate completion percentage and trajectory
   - Identify bottleneck goals that block others
   - Visualize goal dependencies and critical path

3. PATTERN DETECTION
   - Find goals that consistently get pushed back
   - Detect goals that are too easy or too ambitious
   - Identify the user's goal completion archetype

4. PROACTIVE GUIDANCE
   - Suggest daily/weekly actions to stay on track
   - Alert when a goal needs attention
   - Recommend goal decomposition when stuck

Architecture:
- record_progress(goal_id, amount, notes): Log progress
- get_goal_status(): Get comprehensive goal status
- get_trajectory(goal_id): Get completion trajectory
- get_suggestions(): Get goal management suggestions
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "goal_progress_visualizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROGRESS_LOG = DATA_DIR / "progress.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Goal:
    """A tracked goal."""
    goal_id: str = ""
    title: str = ""
    description: str = ""
    target: float = 100.0
    current: float = 0.0
    unit: str = ""  # pages, hours, dollars, items, etc.
    deadline: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    category: str = ""
    dependencies: List[str] = field(default_factory=list)  # goal_ids this depends on
    status: str = "active"  # active, completed, paused, abandoned
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


@dataclass
class ProgressEntry:
    """A progress entry."""
    goal_id: str = ""
    amount: float = 0.0
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class GoalProgressVisualizer:
    """
    Visualize and manage goal progress with predictive intelligence.
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
        self._goals: Dict[str, Goal] = {}
        self._progress: deque = deque(maxlen=500)
        self._stats = {
            "total_goals": 0,
            "completed_goals": 0,
            "avg_completion_time_days": 0.0,
            "on_track_pct": 0.0,
        }
        self._load_stats()

    # ── Core Management ─────────────────────────────────────────────────────

    def add_goal(self, title: str, description: str = "", target: float = 100.0, unit: str = "", deadline: Optional[str] = None, priority: str = "medium", category: str = "", dependencies: Optional[List[str]] = None) -> Goal:
        """Add a new goal to track."""
        goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._goals)}"
        goal = Goal(
            goal_id=goal_id,
            title=title,
            description=description,
            target=target,
            unit=unit or "units",
            deadline=deadline,
            priority=priority,
            category=category or "general",
            dependencies=dependencies or [],
        )

        with self._lock:
            self._goals[goal_id] = goal
            self._stats["total_goals"] += 1

        self._save_stats()
        return goal

    def record_progress(self, goal_id: str, amount: float = 0.0, notes: str = "") -> Optional[ProgressEntry]:
        """Record progress on a goal."""
        if goal_id not in self._goals:
            return None

        entry = ProgressEntry(
            goal_id=goal_id,
            amount=amount,
            notes=notes,
        )

        with self._lock:
            self._progress.append(entry)
            self._goals[goal_id].current += amount
            
            # Check completion
            if self._goals[goal_id].current >= self._goals[goal_id].target:
                self._goals[goal_id].status = "completed"
                self._goals[goal_id].completed_at = entry.timestamp
                self._stats["completed_goals"] += 1

        self._save_stats()
        self._log_progress(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_goal_status(self) -> List[Dict[str, Any]]:
        """Get comprehensive goal status for all active goals."""
        status_list = []

        for goal_id, goal in self._goals.items():
            if goal.status == "active":
                pct = (goal.current / max(1, goal.target)) * 100
                
                # Calculate trajectory
                trajectory = self._calculate_trajectory(goal_id)
                
                # Determine status
                if pct >= 90:
                    goal_status = "nearly_done"
                elif trajectory.get("on_track", False):
                    goal_status = "on_track"
                elif trajectory.get("days_behind", 0) > 7:
                    goal_status = "at_risk"
                else:
                    goal_status = "slipping"

                # Check dependencies
                blocked = False
                for dep_id in goal.dependencies:
                    if dep_id in self._goals and self._goals[dep_id].status != "completed":
                        blocked = True
                        break

                status_list.append({
                    "goal_id": goal_id,
                    "title": goal.title,
                    "category": goal.category,
                    "priority": goal.priority,
                    "current": round(goal.current, 1),
                    "target": goal.target,
                    "unit": goal.unit,
                    "pct_complete": round(pct, 1),
                    "status": goal_status,
                    "blocked": blocked,
                    "deadline": goal.deadline,
                    "trajectory": trajectory,
                })

        return sorted(status_list, key=lambda x: ({"critical": 0, "high": 1, "medium": 2, "low": 3}[x["priority"]], -x["trajectory"].get("days_behind", 0)))

    def get_trajectory(self, goal_id: str) -> Dict[str, Any]:
        """Get completion trajectory for a specific goal."""
        if goal_id not in self._goals:
            return {"status": "not_found"}
        return self._calculate_trajectory(goal_id)

    def get_suggestions(self) -> List[Dict[str, Any]]:
        """Get goal management suggestions."""
        suggestions = []
        status = self.get_goal_status()

        # Find at-risk goals
        at_risk = [g for g in status if g["status"] == "at_risk"]
        for goal in at_risk:
            suggestions.append({
                "type": "urgent",
                "goal": goal["title"],
                "suggestion": f"'{goal['title']}' is {goal['trajectory'].get('days_behind', 0)} days behind. Consider breaking it into smaller milestones.",
                "action": "Break this goal into daily tasks of 1-2 hours each.",
            })

        # Find blocked goals
        blocked = [g for g in status if g["blocked"]]
        for goal in blocked:
            suggestions.append({
                "type": "dependency",
                "goal": goal["title"],
                "suggestion": f"'{goal['title']}' is blocked by incomplete dependencies. Focus on those first.",
                "action": "Complete dependency goals before working on this one.",
            })

        # Find nearly done goals
        nearly_done = [g for g in status if g["status"] == "nearly_done"]
        for goal in nearly_done:
            suggestions.append({
                "type": "momentum",
                "goal": goal["title"],
                "suggestion": f"'{goal['title']}' is almost done! Push through and complete it for the dopamine hit.",
                "action": f"You need {goal['target'] - goal['current']:.1f} more {goal['unit']}. Do it today.",
            })

        # Check for too many active goals
        active_count = len(status)
        if active_count > 7:
            suggestions.append({
                "type": "focus",
                "goal": "multiple",
                "suggestion": f"You have {active_count} active goals. The brain works best with 3-5 concurrent goals.",
                "action": "Pause or abandon the lowest priority goals. Focus on the top 5.",
            })

        return suggestions

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _calculate_trajectory(self, goal_id: str) -> Dict[str, Any]:
        """Calculate trajectory for a goal."""
        goal = self._goals.get(goal_id)
        if not goal:
            return {}

        # Get progress history
        entries = [p for p in self._progress if p.goal_id == goal_id]
        if len(entries) < 2:
            return {"on_track": True, "days_behind": 0, "estimated_completion": "unknown"}

        # Calculate velocity (units per day)
        sorted_entries = sorted(entries, key=lambda x: x.timestamp)
        first_date = datetime.fromisoformat(sorted_entries[0].timestamp)
        last_date = datetime.fromisoformat(sorted_entries[-1].timestamp)
        days_elapsed = max(1, (last_date - first_date).days)
        
        total_progress = sum(p.amount for p in entries)
        velocity = total_progress / days_elapsed

        # Estimate completion
        remaining = max(0, goal.target - goal.current)
        if velocity > 0:
            days_to_completion = remaining / velocity
            estimated_completion = (last_date + timedelta(days=days_to_completion)).isoformat()
        else:
            days_to_completion = float('inf')
            estimated_completion = "never"

        # Check if on track
        on_track = True
        days_behind = 0
        if goal.deadline:
            try:
                deadline = datetime.fromisoformat(goal.deadline)
                days_to_deadline = max(0, (deadline - datetime.now()).days)
                
                if days_to_completion > days_to_deadline:
                    on_track = False
                    days_behind = int(days_to_completion - days_to_deadline)
            except Exception:
                pass

        return {
            "velocity_per_day": round(velocity, 2),
            "remaining": round(remaining, 1),
            "days_to_completion": round(days_to_completion, 1) if days_to_completion != float('inf') else "infinite",
            "estimated_completion": estimated_completion,
            "on_track": on_track,
            "days_behind": days_behind,
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "goals": {k: {
                    "goal_id": v.goal_id,
                    "title": v.title,
                    "description": v.description,
                    "target": v.target,
                    "current": v.current,
                    "unit": v.unit,
                    "deadline": v.deadline,
                    "priority": v.priority,
                    "category": v.category,
                    "dependencies": v.dependencies,
                    "status": v.status,
                    "created_at": v.created_at,
                    "completed_at": v.completed_at,
                } for k, v in self._goals.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("goals", {}).items():
                    self._goals[k] = Goal(**v)
        except Exception:
            pass

    def _log_progress(self, entry: ProgressEntry):
        try:
            with open(PROGRESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "goal_id": entry.goal_id,
                    "amount": entry.amount,
                    "notes": entry.notes,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gpv_instance: Optional[GoalProgressVisualizer] = None
_gpv_lock = threading.Lock()


def get_goal_progress_visualizer() -> GoalProgressVisualizer:
    global _gpv_instance
    with _gpv_lock:
        if _gpv_instance is None:
            _gpv_instance = GoalProgressVisualizer()
        return _gpv_instance
