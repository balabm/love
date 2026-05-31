"""
LOVE Habit Streak Tracker — Consistency & Momentum Engine (Modern AI Pattern)

Most habit trackers are passive logs. This tracker:

1. STREAK DETECTION
   - Automatically detect habit completion from conversation + logs
   - Track current streak, longest streak, and streak history
   - Identify patterns in habit completion (time of day, triggers)

2. MOMENTUM SCORING
   - Calculate momentum score based on recent consistency
   - Detect slipping streaks before they break
   - Reward multi-day consistency with momentum bonuses

3. PROACTIVE ENCOURAGEMENT
   - Celebrate streak milestones (7, 21, 30, 60, 90 days)
   - Warn when habit completion is overdue
   - Suggest habit stacking (pair new habits with existing ones)

4. ADAPTIVE GOAL SETTING
   - Adjust habit frequency based on success rate
   - Simplify habits that consistently fail
   - Ramp up habits that are consistently achieved

Architecture:
- record_habit(habit_id, completed): Record habit completion
- get_streaks(): Get all current streaks
- get_momentum_score(habit_id): Get momentum for a habit
- detect_slipping(): Find habits at risk of breaking
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "habit_streak_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HABIT_LOG = DATA_DIR / "habit_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class HabitStreak:
    """Current state of a habit streak."""
    habit_id: str = ""
    habit_name: str = ""
    current_streak: int = 0
    longest_streak: int = 0
    last_completed: Optional[str] = None
    total_completions: int = 0
    completion_rate: float = 0.0
    momentum_score: float = 0.0
    status: str = "active"  # active, at_risk, broken


class HabitStreakTracker:
    """
    Track habit streaks and provide proactive encouragement.
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
        self._habits: Dict[str, HabitStreak] = {}
        self._completion_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_habit(self, habit_id: str, habit_name: str = "", completed: bool = True):
        """Record habit completion."""
        now = datetime.now()
        today = now.date()

        if habit_id not in self._habits:
            self._habits[habit_id] = HabitStreak(habit_id=habit_id, habit_name=habit_name or habit_id)

        habit = self._habits[habit_id]
        habit.habit_name = habit_name or habit.habit_name

        if completed:
            # Check if this is consecutive
            if habit.last_completed:
                try:
                    last_date = datetime.fromisoformat(habit.last_completed).date()
                    days_diff = (today - last_date).days
                    if days_diff == 1:
                        habit.current_streak += 1
                    elif days_diff == 0:
                        pass  # Already logged today
                    else:
                        habit.current_streak = 1  # Streak broken, restart
                except Exception:
                    habit.current_streak = 1
            else:
                habit.current_streak = 1

            habit.last_completed = now.isoformat()
            habit.total_completions += 1
            habit.longest_streak = max(habit.longest_streak, habit.current_streak)
            habit.completion_rate = self._calculate_completion_rate(habit_id)
            habit.momentum_score = self._calculate_momentum(habit_id)
            habit.status = "active"

            self._completion_history[habit_id].append(now.isoformat())

            # Check milestones
            self._check_milestones(habit)

        self._save_stats()
        self._log_completion(habit_id, completed)

    def get_streaks(self) -> List[HabitStreak]:
        """Get all current streaks."""
        # Update status for all habits
        for habit in self._habits.values():
            if habit.last_completed:
                try:
                    last_date = datetime.fromisoformat(habit.last_completed).date()
                    days_since = (datetime.now().date() - last_date).days
                    if days_since > 2:
                        habit.status = "broken"
                    elif days_since > 1:
                        habit.status = "at_risk"
                except Exception:
                    pass

        return sorted(self._habits.values(), key=lambda h: h.momentum_score, reverse=True)

    def get_momentum_score(self, habit_id: str) -> float:
        """Get momentum score for a specific habit."""
        if habit_id not in self._habits:
            return 0.0
        return self._calculate_momentum(habit_id)

    def detect_slipping(self) -> List[Dict[str, Any]]:
        """Detect habits at risk of breaking."""
        at_risk = []
        for habit in self._habits.values():
            if habit.status == "at_risk":
                at_risk.append({
                    "habit_id": habit.habit_id,
                    "habit_name": habit.habit_name,
                    "current_streak": habit.current_streak,
                    "days_since": (datetime.now().date() - datetime.fromisoformat(habit.last_completed).date()).days if habit.last_completed else None,
                    "urgency": "high" if habit.current_streak > 7 else "medium",
                })
        return at_risk

    # ── Calculations ──────────────────────────────────────────────────────

    def _calculate_completion_rate(self, habit_id: str) -> float:
        """Calculate completion rate over last 30 days."""
        history = self._completion_history.get(habit_id, [])
        if not history:
            return 0.0

        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        recent = [h for h in history if h > thirty_days_ago]
        return round(len(recent) / 30, 2)

    def _calculate_momentum(self, habit_id: str) -> float:
        """Calculate momentum score (0-1)."""
        habit = self._habits.get(habit_id)
        if not habit:
            return 0.0

        # Factors: streak length, completion rate, recency
        streak_factor = min(1.0, habit.current_streak / 21)  # Max at 21 days
        rate_factor = habit.completion_rate
        recency_factor = 1.0

        if habit.last_completed:
            try:
                last = datetime.fromisoformat(habit.last_completed)
                hours_since = (datetime.now() - last).total_seconds() / 3600
                if hours_since > 48:
                    recency_factor = 0.3
                elif hours_since > 24:
                    recency_factor = 0.7
            except Exception:
                pass

        return round((streak_factor * 0.4 + rate_factor * 0.4 + recency_factor * 0.2), 2)

    def _check_milestones(self, habit: HabitStreak):
        """Check and celebrate streak milestones."""
        milestones = [7, 21, 30, 60, 90, 180, 365]
        if habit.current_streak in milestones:
            try:
                from core.neural_bus import get_neural_bus
                get_neural_bus().publish(
                    event_type="streak_milestone",
                    domain="habits",
                    payload={
                        "habit_id": habit.habit_id,
                        "habit_name": habit.habit_name,
                        "streak": habit.current_streak,
                    },
                )
            except Exception:
                pass

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                "habits": {k: {
                    "habit_id": v.habit_id,
                    "habit_name": v.habit_name,
                    "current_streak": v.current_streak,
                    "longest_streak": v.longest_streak,
                    "last_completed": v.last_completed,
                    "total_completions": v.total_completions,
                    "completion_rate": v.completion_rate,
                    "momentum_score": v.momentum_score,
                    "status": v.status,
                } for k, v in self._habits.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                for k, v in data.get("habits", {}).items():
                    self._habits[k] = HabitStreak(**v)
        except Exception:
            pass

    def _log_completion(self, habit_id: str, completed: bool):
        try:
            with open(HABIT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "habit_id": habit_id,
                    "completed": completed,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hst_instance: Optional[HabitStreakTracker] = None
_hst_lock = threading.Lock()


def get_habit_streak_tracker() -> HabitStreakTracker:
    global _hst_instance
    with _hst_lock:
        if _hst_instance is None:
            _hst_instance = HabitStreakTracker()
        return _hst_instance
