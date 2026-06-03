"""
LOVE Focus Recovery Tracker — Focus Session Intelligence (Modern AI Pattern)

After a focus session, most systems just say "done." This tracker:

1. RECOVERY METRICS
   - Track how long it takes to recover focus after interruption
   - Measure focus depth (shallow vs deep)
   - Calculate focus stamina (how many deep sessions before degradation)

2. PATTERN DETECTION
   - Identify what interrupts focus most (notifications, context switching, fatigue)
   - Find optimal recovery activities (walk, water, breath, music)
   - Detect focus "crash" patterns (overworking without recovery)

3. RECOVERY SUGGESTIONS
   - Suggest specific recovery actions based on session type
   - Recommend when to schedule next deep session
   - Warn if focus is degrading across sessions

4. STAMINA BUILDING
   - Track focus endurance over time
   - Suggest progressive focus training
   - Celebrate focus milestones

Architecture:
- record_session(duration, depth, interruptions): Log focus session
- record_recovery(duration, activity): Log recovery
- get_focus_stats(): Get focus analytics
- get_recovery_recommendation(): Suggest recovery action
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

DATA_DIR = Path(__file__).parent.parent / "data" / "focus_recovery_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_LOG = DATA_DIR / "session_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class FocusSession:
    """A focus session record."""
    duration_minutes: float = 0.0
    depth: float = 0.5  # 0-1 (shallow to deep)
    interruptions: int = 0
    recovery_minutes: float = 0.0
    recovery_activity: str = ""
    focus_quality: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    task_type: str = ""  # coding, writing, reading, meeting


class FocusRecoveryTracker:
    """
    Track focus sessions and recovery patterns.
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
        self._history: deque = deque(maxlen=200)
        self._stats = {
            "avg_session_duration": 25.0,
            "avg_depth": 0.5,
            "avg_recovery_time": 5.0,
            "focus_stamina": 3,  # sessions before degradation
            "total_sessions": 0,
            "best_streak": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, duration: float, depth: float, interruptions: int = 0, task_type: str = "") -> FocusSession:
        """Record a focus session."""
        session = FocusSession(
            duration_minutes=duration,
            depth=depth,
            interruptions=interruptions,
            task_type=task_type,
        )

        with self._lock:
            self._history.append(session)
            self._stats["total_sessions"] += 1
            self._update_stats(session)

        self._save_stats()
        self._log_session(session)

        return session

    def record_recovery(self, session_id: Optional[str] = None, duration: float = 0.0, activity: str = ""):
        """Record recovery time and activity."""
        # Associate with most recent session if no ID given
        if self._history and not session_id:
            session = self._history[-1]
            session.recovery_minutes = duration
            session.recovery_activity = activity

        self._save_stats()

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_focus_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get focus analytics."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in self._history if s.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        durations = [s.duration_minutes for s in recent]
        depths = [s.depth for s in recent]
        interruptions = [s.interruptions for s in recent]
        recoveries = [s.recovery_minutes for s in recent if s.recovery_minutes > 0]

        # Calculate stamina (sessions before depth drops below 0.6)
        stamina = 0
        for s in recent:
            if s.depth >= 0.6:
                stamina += 1
            else:
                break

        # Find best recovery activities
        activity_recovery = defaultdict(list)
        for s in recent:
            if s.recovery_activity:
                activity_recovery[s.recovery_activity].append(s.depth)

        best_recovery = sorted(
            [(act, sum(scores)/len(scores)) for act, scores in activity_recovery.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:3] if activity_recovery else []

        return {
            "days_analyzed": len(set(s.timestamp[:10] for s in recent)),
            "total_sessions": len(recent),
            "avg_duration": round(sum(durations) / len(durations), 1),
            "avg_depth": round(sum(depths) / len(depths), 2),
            "avg_interruptions": round(sum(interruptions) / len(interruptions), 1),
            "avg_recovery_time": round(sum(recoveries) / max(1, len(recoveries)), 1) if recoveries else 0,
            "focus_stamina": stamina,
            "best_recovery_activities": best_recovery,
            "interruption_rate": round(sum(interruptions) / max(1, len(recent)), 2),
        }

    def get_recovery_recommendation(self) -> Dict[str, Any]:
        """Suggest recovery action based on recent sessions."""
        if not self._history:
            return {"activity": "take a short walk", "duration": 5, "reason": "Default recovery"}

        recent = list(self._history)[-3:]
        avg_depth = sum(s.depth for s in recent) / len(recent)
        avg_duration = sum(s.duration_minutes for s in recent) / len(recent)

        if avg_depth > 0.8 and avg_duration > 45:
            return {
                "activity": "20-minute break: walk + hydration + stretch",
                "duration": 20,
                "reason": "Deep long session - full recovery needed",
            }
        elif avg_depth > 0.7:
            return {
                "activity": "10-minute break: eyes closed + deep breathing",
                "duration": 10,
                "reason": "Deep focus session - mental reset needed",
            }
        elif avg_duration > 60:
            return {
                "activity": "15-minute break: movement + snack",
                "duration": 15,
                "reason": "Long session - physical recovery needed",
            }
        else:
            return {
                "activity": "5-minute break: water + stretch",
                "duration": 5,
                "reason": "Standard recovery between sessions",
            }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, session: FocusSession):
        """Update running statistics."""
        n = self._stats["total_sessions"]
        self._stats["avg_session_duration"] = round(
            (self._stats["avg_session_duration"] * (n - 1) + session.duration_minutes) / n, 1
        )
        self._stats["avg_depth"] = round(
            (self._stats["avg_depth"] * (n - 1) + session.depth) / n, 2
        )

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.focus_recovery_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.focus_recovery_tracker")

    def _log_session(self, session: FocusSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "duration": session.duration_minutes,
                    "depth": session.depth,
                    "interruptions": session.interruptions,
                    "task_type": session.task_type,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.focus_recovery_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_frt_instance: Optional[FocusRecoveryTracker] = None
_frt_lock = threading.Lock()


def get_focus_recovery_tracker() -> FocusRecoveryTracker:
    global _frt_instance
    with _frt_lock:
        if _frt_instance is None:
            _frt_instance = FocusRecoveryTracker()
        return _frt_instance
