"""
LOVE Habit Architect — Behavior Design Intelligence (Modern AI Pattern)

Most habits fail because they're designed against human psychology. This architect:

1. HABIT TRACKING
   - Record habit attempts, successes, and failures
   - Track habit stack position, cues, rewards, and friction
   - Log habit streaks and their psychological impact

2. PATTERN ANALYSIS
   - Identify the user's habit style (routine-based, trigger-based, identity-based, social)
   - Find which habit designs work (cue clarity, reward timing, friction level)
   - Detect habit collapse predictors

3. ARCHITECTURE DESIGN
   - Suggest habit stacks using existing behaviors as anchors
   - Provide friction reduction strategies
   - Recommend reward systems that actually work

4. FAILURE RECOVERY
   - Analyze why habits failed (wrong cue, too hard, no reward, identity mismatch)
   - Suggest redesigns based on failure analysis
   - Prevent all-or-nothing collapse after missed days

Architecture:
- record_habit_attempt(habit, success, cue, reward, friction): Log attempt
- get_habit_stats(): Get habit pattern analysis
- get_habit_design(goal, anchor_habit): Get architecture
- get_habit_score(): Calculate overall habit health
"""

import json
import math
import random
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "habit_architect"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HABIT_LOG = DATA_DIR / "habits.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class HabitAttempt:
    """A tracked habit attempt."""
    attempt_id: str = ""
    habit: str = ""
    category: str = ""  # health, learning, creativity, social, productivity, recovery
    success: bool = False
    cue: str = ""  # what triggered the habit
    reward: str = ""  # what reinforced it
    friction: float = 0.5  # 0-1, how hard it was
    motivation: float = 0.5  # 0-1, how motivated they felt
    identity_link: str = ""  # which identity this supports
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HabitArchitect:
    """
    Intelligent habit architect with behavioral design and failure recovery.
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
        self._attempts: deque = deque(maxlen=300)
        self._stats = {
            "total_attempts": 0,
            "success_rate": 0.0,
            "avg_friction": 0.0,
            "strongest_habit": "",
            "weakest_habit": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_habit_attempt(self, habit: str = "", category: str = "", success: bool = False, cue: str = "", reward: str = "", friction: float = 0.5, motivation: float = 0.5, identity_link: str = "", notes: str = "") -> HabitAttempt:
        """Record a habit attempt."""
        attempt_id = f"habit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._attempts)}"
        attempt = HabitAttempt(
            attempt_id=attempt_id,
            habit=habit or "unspecified",
            category=category or "general",
            success=success,
            cue=cue,
            reward=reward,
            friction=friction,
            motivation=motivation,
            identity_link=identity_link,
            notes=notes,
        )

        with self._lock:
            self._attempts.append(attempt)
            self._stats["total_attempts"] += 1
            self._update_stats()

        self._save_stats()
        self._log_attempt(attempt)

        return attempt

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_habit_stats(self) -> Dict[str, Any]:
        """Get habit pattern analysis."""
        if not self._attempts:
            return {"status": "insufficient_data"}

        # Habit analysis
        by_habit = defaultdict(lambda: {"count": 0, "success": 0, "friction_sum": 0.0, "motivation_sum": 0.0})
        for a in self._attempts:
            by_habit[a.habit]["count"] += 1
            if a.success:
                by_habit[a.habit]["success"] += 1
            by_habit[a.habit]["friction_sum"] += a.friction
            by_habit[a.habit]["motivation_sum"] += a.motivation

        habit_stats = {}
        for h, data in by_habit.items():
            count = data["count"]
            habit_stats[h] = {
                "count": count,
                "success_rate": round(data["success"] / count, 2),
                "avg_friction": round(data["friction_sum"] / count, 2),
                "avg_motivation": round(data["motivation_sum"] / count, 2),
            }

        strongest = max(habit_stats.items(), key=lambda x: x[1]["success_rate"]) if habit_stats else ("", {})
        weakest = min(habit_stats.items(), key=lambda x: x[1]["success_rate"]) if habit_stats else ("", {})

        # Cue analysis
        by_cue = defaultdict(lambda: {"count": 0, "success": 0})
        for a in self._attempts:
            if a.cue:
                by_cue[a.cue]["count"] += 1
                if a.success:
                    by_cue[a.cue]["success"] += 1

        cue_stats = {}
        for c, data in by_cue.items():
            count = data["count"]
            if count >= 2:
                cue_stats[c] = {
                    "count": count,
                    "success_rate": round(data["success"] / count, 2),
                }

        # Reward analysis
        by_reward = defaultdict(lambda: {"count": 0, "success": 0})
        for a in self._attempts:
            if a.reward:
                by_reward[a.reward]["count"] += 1
                if a.success:
                    by_reward[a.reward]["success"] += 1

        reward_stats = {}
        for r, data in by_reward.items():
            count = data["count"]
            if count >= 2:
                reward_stats[r] = {
                    "count": count,
                    "success_rate": round(data["success"] / count, 2),
                }

        # Identity link analysis
        by_identity = defaultdict(lambda: {"count": 0, "success": 0})
        for a in self._attempts:
            if a.identity_link:
                by_identity[a.identity_link]["count"] += 1
                if a.success:
                    by_identity[a.identity_link]["success"] += 1

        identity_stats = {}
        for i, data in by_identity.items():
            count = data["count"]
            identity_stats[i] = {
                "count": count,
                "success_rate": round(data["success"] / count, 2),
            }

        # Friction vs success
        successful = [a for a in self._attempts if a.success]
        failed = [a for a in self._attempts if not a.success]
        if successful and failed:
            avg_friction_success = sum(a.friction for a in successful) / len(successful)
            avg_friction_failed = sum(a.friction for a in failed) / len(failed)
            friction_insight = f"Successful habits had {avg_friction_success:.2f} avg friction vs {avg_friction_failed:.2f} for failed"
        else:
            friction_insight = "insufficient_data"

        return {
            "total_attempts": len(self._attempts),
            "habit_stats": habit_stats,
            "strongest_habit": strongest[0],
            "weakest_habit": weakest[0],
            "cue_stats": cue_stats,
            "reward_stats": reward_stats,
            "identity_stats": identity_stats,
            "success_rate": round(sum(1 for a in self._attempts if a.success) / len(self._attempts), 2),
            "avg_friction": round(sum(a.friction for a in self._attempts) / len(self._attempts), 2),
            "friction_insight": friction_insight,
        }

    def get_habit_design(self, goal: str = "", anchor_habit: str = "", current_friction: float = 0.5) -> Dict[str, Any]:
        """Get architecture."""
        stack_templates = [
            f"After I {anchor_habit}, I will [new habit]",
            f"Before I {anchor_habit}, I will [new habit]",
            f"While I {anchor_habit}, I will [new habit]",
            f"If I {anchor_habit}, then I will also [new habit]",
        ]

        friction_reducers = [
            "Reduce the habit to 2 minutes or less",
            "Prepare everything the night before",
            "Make the habit impossible to miss (leave shoes by bed)",
            "Pair with something you already enjoy",
            "Change your environment to make the habit the default",
            "Use a visual tracker (calendar, app, beads)",
        ]

        reward_systems = [
            "Immediate: Cross it off a list. The dopamine is real.",
            "Social: Tell someone you did it. Accountability = reward.",
            "Sensory: Special coffee, tea, or music only after the habit.",
            "Progress: Watch a streak grow. Numbers motivate.",
            "Identity: Remind yourself: 'This is who I am now.'",
        ]

        if current_friction > 0.7:
            approach = "This habit is too hard. Shrink it by 80%. Two minutes max. Make it stupidly easy."
        elif current_friction > 0.4:
            approach = "Moderate friction. Focus on environment design and cue clarity."
        else:
            approach = "Low friction. You're ready. Add a reward system to make it sticky."

        return {
            "goal": goal or "unspecified",
            "anchor_habit": anchor_habit or "wake up",
            "current_friction": current_friction,
            "stack_template": random.choice(stack_templates),
            "friction_reducers": random.sample(friction_reducers, min(2, len(friction_reducers))),
            "reward_systems": random.sample(reward_systems, min(2, len(reward_systems))),
            "approach": approach,
            "rule": "Never miss twice. One miss is data. Two misses is a pattern. Three is a new habit (the wrong one).",
        }

    def get_habit_score(self) -> int:
        """Calculate overall habit health (0-100)."""
        if not self._attempts:
            return 35

        # Success rate
        success_rate = sum(1 for a in self._attempts if a.success) / len(self._attempts)

        # Low friction
        avg_friction = sum(a.friction for a in self._attempts) / len(self._attempts)

        # Identity alignment
        identity_aligned = [a for a in self._attempts if a.identity_link]
        if identity_aligned:
            identity_success = sum(1 for a in identity_aligned if a.success) / len(identity_aligned)
        else:
            identity_success = 0

        # Recent trend
        recent = list(self._attempts)[-14:]
        recent_success = sum(1 for a in recent if a.success) / len(recent)
        older = list(self._attempts)[:-14] if len(self._attempts) > 14 else []
        if older:
            older_success = sum(1 for a in older if a.success) / len(older)
            trend = recent_success - older_success
        else:
            trend = 0

        # Cue clarity
        cued = [a for a in self._attempts if a.cue]
        if cued:
            cued_success = sum(1 for a in cued if a.success) / len(cued)
        else:
            cued_success = 0

        score = (success_rate * 30) + ((1 - avg_friction) * 15) + (identity_success * 15) + (trend * 15) + (cued_success * 10) + 15
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._attempts:
            success = sum(1 for a in self._attempts if a.success)
            self._stats["success_rate"] = round(success / len(self._attempts), 2)
            self._stats["avg_friction"] = round(sum(a.friction for a in self._attempts) / len(self._attempts), 2)

            by_habit = defaultdict(lambda: {"success": 0, "total": 0})
            for a in self._attempts:
                by_habit[a.habit]["total"] += 1
                if a.success:
                    by_habit[a.habit]["success"] += 1
            
            if by_habit:
                strongest = max(by_habit.items(), key=lambda x: x[1]["success"] / max(1, x[1]["total"]))
                weakest = min(by_habit.items(), key=lambda x: x[1]["success"] / max(1, x[1]["total"]))
                self._stats["strongest_habit"] = strongest[0]
                self._stats["weakest_habit"] = weakest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.habit_architect")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.habit_architect")

    def _log_attempt(self, attempt: HabitAttempt):
        try:
            with open(HABIT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": attempt.timestamp,
                    "habit": attempt.habit,
                    "category": attempt.category,
                    "success": attempt.success,
                    "friction": attempt.friction,
                    "motivation": attempt.motivation,
                    "cue": attempt.cue,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.habit_architect")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ha_instance: Optional[HabitArchitect] = None
_ha_lock = threading.Lock()


def get_habit_architect() -> HabitArchitect:
    global _ha_instance
    with _ha_lock:
        if _ha_instance is None:
            _ha_instance = HabitArchitect()
        return _ha_instance
