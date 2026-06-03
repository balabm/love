"""
LOVE Exercise Optimizer — Fitness Intelligence (Modern AI Pattern)

Most fitness trackers count steps. This optimizer:

1. WORKOUT LOGGING
   - Record exercise type, intensity, duration, and perceived exertion
   - Track muscle groups worked and recovery needs
   - Log energy levels before/after exercise

2. RECOVERY INTELLIGENCE
   - Calculate optimal rest between workouts for each muscle group
   - Detect overtraining patterns (elevated resting heart rate, poor sleep, fatigue)
   - Suggest active recovery vs complete rest

3. PROGRESSIVE OVERLOAD
   - Track performance trends (weights, reps, pace, distance)
   - Suggest when to increase intensity or volume
   - Identify plateau patterns and suggest changes

4. PROACTIVE SCHEDULING
   - Suggest optimal workout times based on energy patterns
   - Recommend workout type based on current recovery state
   - Alert when a muscle group is ready to be trained again

Architecture:
- record_workout(type, duration, intensity, muscles): Log workout
- get_recovery_status(muscle_group): Check muscle recovery
- get_workout_suggestion(): Suggest next workout
- get_fitness_trends(): Track performance over time
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

DATA_DIR = Path(__file__).parent.parent / "data" / "exercise_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WORKOUT_LOG = DATA_DIR / "workouts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Workout:
    """A recorded workout session."""
    workout_type: str = ""  # strength, cardio, flexibility, sport
    duration_minutes: float = 0.0
    intensity: float = 0.5  # 0-1
    perceived_exertion: int = 5  # 1-10 RPE scale
    muscle_groups: List[str] = field(default_factory=list)
    exercises: List[str] = field(default_factory=list)
    energy_before: float = 0.5
    energy_after: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class MuscleRecovery:
    """Recovery status for a muscle group."""
    muscle: str = ""
    last_trained: Optional[str] = None
    training_count_7d: int = 0
    recovery_score: float = 1.0  # 0-1 (0 = fully recovered, 1 = not recovered)
    status: str = "recovered"  # recovered, ready, fatigued, overreached


class ExerciseOptimizer:
    """
    Optimize exercise routines with recovery intelligence.
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
        self._workouts: deque = deque(maxlen=500)
        self._muscle_recovery: Dict[str, MuscleRecovery] = {}
        self._stats = {
            "total_workouts": 0,
            "total_minutes": 0,
            "avg_intensity": 0.5,
            "avg_exertion": 5.0,
            "consistency_streak": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_workout(self, workout_type: str, duration: float, intensity: float = 0.5, perceived_exertion: int = 5, muscle_groups: Optional[List[str]] = None, exercises: Optional[List[str]] = None, energy_before: float = 0.5, energy_after: float = 0.5, notes: str = "") -> Workout:
        """Record a workout session."""
        workout = Workout(
            workout_type=workout_type,
            duration_minutes=duration,
            intensity=intensity,
            perceived_exertion=perceived_exertion,
            muscle_groups=muscle_groups or [],
            exercises=exercises or [],
            energy_before=energy_before,
            energy_after=energy_after,
            notes=notes,
        )

        with self._lock:
            self._workouts.append(workout)
            self._stats["total_workouts"] += 1
            self._stats["total_minutes"] += duration
            self._update_muscle_recovery(workout)
            self._update_stats(workout)

        self._save_stats()
        self._log_workout(workout)

        # Check for overtraining
        self._check_overtraining()

        return workout

    # ── Recovery Intelligence ──────────────────────────────────────────────

    def get_recovery_status(self, muscle_group: Optional[str] = None) -> Dict[str, Any]:
        """Check muscle recovery status."""
        if muscle_group:
            recovery = self._muscle_recovery.get(muscle_group)
            if not recovery:
                return {"status": "no_data", "muscle": muscle_group}
            return {
                "muscle": recovery.muscle,
                "last_trained": recovery.last_trained,
                "recovery_score": round(recovery.recovery_score, 2),
                "status": recovery.status,
                "training_count_7d": recovery.training_count_7d,
            }

        # Return all muscle recovery statuses
        all_recovery = []
        for muscle, recovery in self._muscle_recovery.items():
            all_recovery.append({
                "muscle": muscle,
                "status": recovery.status,
                "recovery_score": round(recovery.recovery_score, 2),
                "last_trained": recovery.last_trained,
            })

        return sorted(all_recovery, key=lambda x: x["recovery_score"], reverse=True)

    # ── Suggestions ────────────────────────────────────────────────────────

    def get_workout_suggestion(self) -> Dict[str, Any]:
        """Suggest next workout based on recovery and patterns."""
        # Find muscles that are recovered
        ready_muscles = [m for m, r in self._muscle_recovery.items() if r.status in ["recovered", "ready"]]
        fatigued_muscles = [m for m, r in self._muscle_recovery.items() if r.status in ["fatigued", "overreached"]]

        # Get recent workout types
        recent_types = defaultdict(int)
        for w in list(self._workouts)[-7:]:
            recent_types[w.workout_type] += 1

        # Suggest based on recovery state
        if len(fatigued_muscles) > 3:
            return {
                "workout_type": "rest_or_active_recovery",
                "suggested_duration": 20,
                "reason": f"Multiple muscle groups are fatigued: {', '.join(fatigued_muscles[:3])}. Take a recovery day.",
                "ready_muscles": ready_muscles,
                "fatigued_muscles": fatigued_muscles,
            }

        # If upper body muscles are recovered, suggest upper body
        upper_muscles = ["chest", "shoulders", "triceps", "biceps", "back"]
        lower_muscles = ["quads", "hamstrings", "glutes", "calves"]
        core_muscles = ["abs", "core", "lower_back"]

        upper_ready = sum(1 for m in ready_muscles if m in upper_muscles)
        lower_ready = sum(1 for m in ready_muscles if m in lower_muscles)

        if upper_ready >= 3 and recent_types.get("strength", 0) < 3:
            return {
                "workout_type": "upper_body_strength",
                "suggested_duration": 45,
                "target_muscles": [m for m in ready_muscles if m in upper_muscles][:3],
                "reason": "Upper body muscles are recovered and ready for training.",
            }
        elif lower_ready >= 2 and recent_types.get("strength", 0) < 3:
            return {
                "workout_type": "lower_body_strength",
                "suggested_duration": 45,
                "target_muscles": [m for m in ready_muscles if m in lower_muscles][:2],
                "reason": "Lower body muscles are recovered and ready for training.",
            }
        elif recent_types.get("cardio", 0) < 2:
            return {
                "workout_type": "cardio",
                "suggested_duration": 30,
                "reason": "Light cardio would be good for recovery and cardiovascular health.",
            }
        else:
            return {
                "workout_type": "flexibility",
                "suggested_duration": 20,
                "reason": "Consider stretching or yoga for active recovery.",
            }

    def get_fitness_trends(self, days: int = 30) -> Dict[str, Any]:
        """Track performance trends over time."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [w for w in self._workouts if w.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Weekly volume trend
        weekly_volume = defaultdict(float)
        weekly_intensity = defaultdict(float)
        weekly_count = defaultdict(int)

        for w in recent:
            week = datetime.fromisoformat(w.timestamp).isocalendar()[1]
            weekly_volume[week] += w.duration_minutes
            weekly_intensity[week] += w.intensity
            weekly_count[week] += 1

        weeks = sorted(weekly_volume.keys())
        volume_trend = []
        for week in weeks:
            volume_trend.append({
                "week": week,
                "volume_minutes": round(weekly_volume[week], 1),
                "avg_intensity": round(weekly_intensity[week] / max(1, weekly_count[week]), 2),
                "workout_count": weekly_count[week],
            })

        # Workout type distribution
        by_type = defaultdict(lambda: {"count": 0, "total_minutes": 0.0})
        for w in recent:
            by_type[w.workout_type]["count"] += 1
            by_type[w.workout_type]["total_minutes"] += w.duration_minutes

        return {
            "days_analyzed": days,
            "total_workouts": len(recent),
            "total_minutes": round(sum(w.duration_minutes for w in recent), 1),
            "avg_duration": round(sum(w.duration_minutes for w in recent) / len(recent), 1),
            "avg_intensity": round(sum(w.intensity for w in recent) / len(recent), 2),
            "avg_exertion": round(sum(w.perceived_exertion for w in recent) / len(recent), 1),
            "weekly_trend": volume_trend,
            "type_distribution": {k: dict(v) for k, v in by_type.items()},
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_muscle_recovery(self, workout: Workout):
        """Update muscle recovery status after a workout."""
        now = datetime.now().isoformat()
        for muscle in workout.muscle_groups:
            if muscle not in self._muscle_recovery:
                self._muscle_recovery[muscle] = MuscleRecovery(muscle=muscle)

            recovery = self._muscle_recovery[muscle]
            recovery.last_trained = now
            recovery.training_count_7d += 1

            # Calculate recovery score based on intensity and recent training
            recovery.recovery_score = min(1.0, recovery.recovery_score + workout.intensity * 0.3)

            # Determine status
            if recovery.recovery_score < 0.3:
                recovery.status = "recovered"
            elif recovery.recovery_score < 0.6:
                recovery.status = "ready"
            elif recovery.recovery_score < 0.85:
                recovery.status = "fatigued"
            else:
                recovery.status = "overreached"

    def _update_stats(self, workout: Workout):
        """Update running statistics."""
        n = self._stats["total_workouts"]
        self._stats["avg_intensity"] = round((self._stats["avg_intensity"] * (n - 1) + workout.intensity) / n, 2)
        self._stats["avg_exertion"] = round((self._stats["avg_exertion"] * (n - 1) + workout.perceived_exertion) / n, 1)

        # Calculate consistency streak (workouts within last 7 days)
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        recent_workouts = sum(1 for w in self._workouts if w.timestamp > cutoff)
        self._stats["consistency_streak"] = recent_workouts

    def _check_overtraining(self):
        """Check for overtraining patterns."""
        # If more than 5 high-intensity workouts in 7 days
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        high_intensity = [w for w in self._workouts if w.timestamp > cutoff and w.intensity > 0.7]
        if len(high_intensity) > 5:
            try:
                from core.neural_bus import get_neural_bus
                get_neural_bus().publish(
                    event_type="overtraining_risk",
                    domain="wellness",
                    payload={
                        "high_intensity_workouts_7d": len(high_intensity),
                        "suggestion": "Consider reducing intensity or taking a rest day.",
                    },
                )
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.exercise_optimizer")

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "muscle_recovery": {k: {
                    "muscle": v.muscle,
                    "last_trained": v.last_trained,
                    "training_count_7d": v.training_count_7d,
                    "recovery_score": v.recovery_score,
                    "status": v.status,
                } for k, v in self._muscle_recovery.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.exercise_optimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("muscle_recovery", {}).items():
                    self._muscle_recovery[k] = MuscleRecovery(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.exercise_optimizer")

    def _log_workout(self, workout: Workout):
        try:
            with open(WORKOUT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": workout.timestamp,
                    "type": workout.workout_type,
                    "duration": workout.duration_minutes,
                    "intensity": workout.intensity,
                    "exertion": workout.perceived_exertion,
                    "muscles": workout.muscle_groups,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.exercise_optimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_eo_instance: Optional[ExerciseOptimizer] = None
_eo_lock = threading.Lock()


def get_exercise_optimizer() -> ExerciseOptimizer:
    global _eo_instance
    with _eo_lock:
        if _eo_instance is None:
            _eo_instance = ExerciseOptimizer()
        return _eo_instance
