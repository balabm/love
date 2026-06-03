"""
LOVE Habit Builder — Habit Intelligence (Modern AI Pattern)

Most habit trackers check boxes. This builder:

1. HABIT DESIGN
   - Design habits using cue-routine-reward framework
   - Track habit difficulty and success rate
   - Log environment triggers that support or sabotage habits

2. PROGRESS ANALYSIS
   - Calculate habit consistency and momentum
   - Identify the best time/place for each habit
   - Detect habit plateaus and suggest changes

3. FAILURE ANALYSIS
   - Log habit misses with reasons (forgot, tired, busy, unmotivated)
   - Identify the biggest obstacle for each habit
   - Suggest recovery strategies after missed days

4. PROACTIVE SUPPORT
   - Suggest habit stacking (attach to existing habits)
   - Alert when habit consistency drops
   - Celebrate streaks and milestones meaningfully

Architecture:
- add_habit(name, cue, routine, reward, difficulty): Design habit
- record_habit(habit_id, completed, obstacle): Log attempt
- get_habit_stats(): Get habit performance analysis
- get_habit_recommendations(): Suggest habit improvements
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

DATA_DIR = Path(__file__).parent.parent / "data" / "habit_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HABIT_LOG = DATA_DIR / "habits.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Habit:
    """A designed habit."""
    habit_id: str = ""
    name: str = ""
    cue: str = ""  # trigger that starts the habit
    routine: str = ""  # what to do
    reward: str = ""  # what you get after
    difficulty: str = "medium"  # easy, medium, hard
    target_frequency: str = "daily"  # daily, weekly, 3x_week
    best_time: str = ""  # morning, afternoon, evening, anytime
    environment: str = ""  # where to do it
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    streak: int = 0
    best_streak: int = 0
    total_attempts: int = 0
    total_completions: int = 0
    status: str = "active"  # active, paused, archived


@dataclass
class HabitAttempt:
    """A single habit attempt."""
    habit_id: str = ""
    completed: bool = False
    obstacle: str = ""  # forgot, tired, busy, unmotivated, environment, other
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_minutes: float = 0.0


class HabitBuilder:
    """
    Intelligent habit builder with failure analysis and recovery.
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
        self._habits: Dict[str, Habit] = {}
        self._attempts: deque = deque(maxlen=500)
        self._stats = {
            "total_habits": 0,
            "total_attempts": 0,
            "overall_success_rate": 0.0,
            "avg_streak": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def add_habit(self, name: str = "", cue: str = "", routine: str = "", reward: str = "", difficulty: str = "medium", target_frequency: str = "daily", best_time: str = "", environment: str = "") -> Habit:
        """Design a new habit."""
        habit_id = f"habit_{name.replace(' ', '_').lower()}_{len(self._habits)}"
        habit = Habit(
            habit_id=habit_id,
            name=name or "untitled",
            cue=cue,
            routine=routine,
            reward=reward,
            difficulty=difficulty,
            target_frequency=target_frequency,
            best_time=best_time or "anytime",
            environment=environment,
        )

        with self._lock:
            self._habits[habit_id] = habit
            self._stats["total_habits"] = len(self._habits)

        self._save_stats()
        return habit

    def record_habit(self, habit_id: str, completed: bool = False, obstacle: str = "", notes: str = "", duration: float = 0) -> Optional[HabitAttempt]:
        """Record a habit attempt."""
        if habit_id not in self._habits:
            return None

        attempt = HabitAttempt(
            habit_id=habit_id,
            completed=completed,
            obstacle=obstacle or ("" if completed else "forgot"),
            notes=notes,
            duration_minutes=duration,
        )

        with self._lock:
            self._attempts.append(attempt)
            habit = self._habits[habit_id]
            habit.total_attempts += 1
            
            if completed:
                habit.total_completions += 1
                habit.streak += 1
                habit.best_streak = max(habit.best_streak, habit.streak)
            else:
                habit.streak = 0

            self._stats["total_attempts"] += 1
            self._update_stats()

        self._save_stats()
        self._log_attempt(attempt)

        return attempt

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_habit_stats(self) -> List[Dict[str, Any]]:
        """Get habit performance analysis."""
        stats = []

        for habit_id, habit in self._habits.items():
            if habit.status != "active":
                continue

            # Get recent attempts
            recent = [a for a in self._attempts if a.habit_id == habit_id and a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            
            if not recent:
                stats.append({
                    "habit_id": habit_id,
                    "name": habit.name,
                    "status": "no_recent_data",
                    "streak": habit.streak,
                    "success_rate": 0.0,
                })
                continue

            completions = sum(1 for a in recent if a.completed)
            success_rate = completions / len(recent)

            # Obstacle analysis
            obstacles = defaultdict(int)
            for a in recent:
                if not a.completed and a.obstacle:
                    obstacles[a.obstacle] += 1

            top_obstacle = max(obstacles.items(), key=lambda x: x[1])[0] if obstacles else ""

            # Time analysis
            morning = sum(1 for a in recent if a.completed and "06:00:00" <= a.timestamp[11:19] <= "12:00:00")
            afternoon = sum(1 for a in recent if a.completed and "12:00:00" < a.timestamp[11:19] <= "18:00:00")
            evening = sum(1 for a in recent if a.completed and "18:00:00" < a.timestamp[11:19] <= "23:59:59")
            
            best_time = "morning" if morning >= afternoon and morning >= evening else "afternoon" if afternoon >= evening else "evening"

            stats.append({
                "habit_id": habit_id,
                "name": habit.name,
                "cue": habit.cue,
                "routine": habit.routine,
                "difficulty": habit.difficulty,
                "streak": habit.streak,
                "best_streak": habit.best_streak,
                "total_completions": habit.total_completions,
                "success_rate": round(success_rate, 2),
                "recent_attempts": len(recent),
                "top_obstacle": top_obstacle,
                "best_time_of_day": best_time,
                "consistency_trend": "improving" if success_rate > 0.7 else "declining" if success_rate < 0.4 else "stable",
            })

        return sorted(stats, key=lambda x: x["success_rate"], reverse=True)

    def get_habit_recommendations(self) -> List[Dict[str, Any]]:
        """Suggest habit improvements."""
        recommendations = []
        stats = self.get_habit_stats()

        for habit_stat in stats:
            # Low success rate habits
            if habit_stat.get("success_rate", 1.0) < 0.4:
                top_obstacle = habit_stat.get("top_obstacle", "unknown")
                cue = habit_stat.get("cue", "current trigger")
                recommendations.append({
                    "habit": habit_stat["name"],
                    "type": "struggling",
                    "suggestion": f"'{habit_stat['name']}' has only {habit_stat['success_rate']:.0%} success. Make it easier.",
                    "action": f"Your top obstacle is '{top_obstacle}'. Address that first. Try: {cue} -> simpler routine.",
                    "priority": "high",
                })

            # Streak at risk
            if habit_stat.get("streak", 0) == 0 and habit_stat.get("best_streak", 0) > 3:
                recommendations.append({
                    "habit": habit_stat["name"],
                    "type": "streak_broken",
                    "suggestion": f"You broke a {habit_stat['best_streak']}-day streak on '{habit_stat['name']}'. Don't miss twice.",
                    "action": "Do it today, even if it's just the minimum version.",
                    "priority": "high",
                })

            # Habit stacking suggestion
            if habit_stat.get("consistency_trend") == "stable" and habit_stat.get("success_rate", 0) > 0.6:
                recommendations.append({
                    "habit": habit_stat["name"],
                    "type": "stack_opportunity",
                    "suggestion": f"'{habit_stat['name']}' is solid. Stack a new habit after it.",
                    "action": f"After {habit_stat['routine']}, try adding a 2-minute habit.",
                    "priority": "low",
                })

            # Time optimization
            best_time_of_day = habit_stat.get("best_time_of_day")
            best_time = habit_stat.get("best_time", "")
            if best_time_of_day and best_time_of_day != best_time:
                recommendations.append({
                    "habit": habit_stat["name"],
                    "type": "time_shift",
                    "suggestion": f"You succeed with '{habit_stat['name']}' more in the {best_time_of_day}.",
                    "action": f"Consider moving it to {best_time_of_day}.",
                    "priority": "medium",
                })

        # General recommendation if too many habits
        active_count = len(stats)
        if active_count > 5:
            recommendations.append({
                "habit": "general",
                "type": "focus",
                "suggestion": f"You have {active_count} active habits. The research says 3 is the sweet spot.",
                "action": "Pause the lowest priority habits. Master 3, then add more.",
                "priority": "medium",
            })

        return sorted(recommendations, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._attempts:
            completions = sum(1 for a in self._attempts if a.completed)
            self._stats["overall_success_rate"] = round(completions / len(self._attempts), 2)
            
            active_habits = [h for h in self._habits.values() if h.status == "active"]
            if active_habits:
                self._stats["avg_streak"] = round(sum(h.streak for h in active_habits) / len(active_habits), 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "habits": {k: {
                    "habit_id": v.habit_id,
                    "name": v.name,
                    "cue": v.cue,
                    "routine": v.routine,
                    "reward": v.reward,
                    "difficulty": v.difficulty,
                    "target_frequency": v.target_frequency,
                    "best_time": v.best_time,
                    "environment": v.environment,
                    "created_at": v.created_at,
                    "streak": v.streak,
                    "best_streak": v.best_streak,
                    "total_attempts": v.total_attempts,
                    "total_completions": v.total_completions,
                    "status": v.status,
                } for k, v in self._habits.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.habit_builder")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("habits", {}).items():
                    self._habits[k] = Habit(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.habit_builder")

    def _log_attempt(self, attempt: HabitAttempt):
        try:
            with open(HABIT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": attempt.timestamp,
                    "habit_id": attempt.habit_id,
                    "completed": attempt.completed,
                    "obstacle": attempt.obstacle,
                    "duration": attempt.duration_minutes,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.habit_builder")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hb_instance: Optional[HabitBuilder] = None
_hb_lock = threading.Lock()


def get_habit_builder() -> HabitBuilder:
    global _hb_instance
    with _hb_lock:
        if _hb_instance is None:
            _hb_instance = HabitBuilder()
        return _hb_instance
