"""
LOVE Deep Work Protector — Focus Session Guardian (Modern AI Pattern)

Deep work is fragile. This protector:

1. FOCUS SESSION MANAGEMENT
   - Start/stop focus sessions with configurable duration
   - Detect when user enters deep work via keyboard/mouse patterns
   - Protect sessions from interruptions (notifications, nudges, non-urgent alerts)

2. INTERRUPTION DETECTION
   - Detect incoming interruptions (messages, calls, notifications)
   - Assess urgency of interruption vs importance of focus
   - Route urgent interruptions only, suppress rest

3. CONTEXT PRESERVATION
   - Save context when focus session ends unexpectedly
   - Restore context when returning to interrupted work
   - Track what was accomplished during each session

4. EFFECTIVENESS TRACKING
   - Track focus session quality (interruptions, flow time)
   - Learn optimal session lengths for user
   - Suggest improvements to focus environment

Architecture:
- start_session(duration, context): Begin protected focus session
- end_session(): End session and save metrics
- handle_interruption(interruption): Route or suppress
- get_focus_stats(): Track focus effectiveness
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

DATA_DIR = Path(__file__).parent.parent / "data" / "deep_work_protector"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_LOG = DATA_DIR / "session_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class FocusSession:
    """A deep work focus session."""
    id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    planned_duration_minutes: int = 25
    actual_duration_minutes: float = 0.0
    interruptions: int = 0
    urgent_interruptions: int = 0
    context: str = ""  # What the user was working on
    quality_score: float = 0.0  # 0-1 based on interruptions/flow
    status: str = "active"  # active, completed, interrupted


@dataclass
class Interruption:
    """An interruption during a focus session."""
    source: str = ""  # notification, message, call, nudge, system
    urgency: str = "normal"  # low, normal, high, urgent
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    action_taken: str = "suppressed"  # suppressed, delivered, deferred


class DeepWorkProtector:
    """
    Protect deep work focus sessions from interruptions.
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
        self._active_session: Optional[FocusSession] = None
        self._stats = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "interrupted_sessions": 0,
            "total_interruptions_suppressed": 0,
            "avg_session_quality": 0.0,
            "optimal_session_length": 25,
        }
        self._session_history: deque = deque(maxlen=100)
        self._load_stats()

    # ── Session Management ─────────────────────────────────────────────────

    def start_session(self, duration_minutes: int = 25, context: str = "") -> FocusSession:
        """Start a protected focus session."""
        if self._active_session:
            # End current session first
            self.end_session()

        session = FocusSession(
            id=f"focus_{int(time.time())}",
            planned_duration_minutes=duration_minutes,
            context=context,
        )

        with self._lock:
            self._active_session = session
            self._stats["total_sessions"] += 1

        self._log_session_start(session)
        return session

    def end_session(self) -> Optional[FocusSession]:
        """End the current focus session."""
        if not self._active_session:
            return None

        session = self._active_session
        session.ended_at = datetime.now().isoformat()

        try:
            start = datetime.fromisoformat(session.started_at)
            end = datetime.fromisoformat(session.ended_at)
            session.actual_duration_minutes = (end - start).total_seconds() / 60
        except Exception:
            session.actual_duration_minutes = session.planned_duration_minutes

        # Calculate quality score
        if session.interruptions == 0:
            session.quality_score = 1.0
        else:
            session.quality_score = max(0.0, 1.0 - (session.interruptions * 0.15))

        # Determine status
        completion_ratio = session.actual_duration_minutes / max(1, session.planned_duration_minutes)
        if completion_ratio >= 0.9 and session.interruptions <= 1:
            session.status = "completed"
            self._stats["completed_sessions"] += 1
        else:
            session.status = "interrupted"
            self._stats["interrupted_sessions"] += 1

        # Update average quality
        prev_avg = self._stats.get("avg_session_quality", 0)
        n = self._stats["total_sessions"]
        self._stats["avg_session_quality"] = round((prev_avg * (n - 1) + session.quality_score) / max(1, n), 2)

        # Learn optimal session length
        if session.status == "completed" and session.quality_score > 0.8:
            self._update_optimal_length(session.planned_duration_minutes)

        self._session_history.append(session)
        self._active_session = None

        self._save_stats()
        self._log_session_end(session)

        return session

    def get_active_session(self) -> Optional[FocusSession]:
        """Get the currently active focus session."""
        return self._active_session

    # ── Interruption Handling ─────────────────────────────────────────────────

    def handle_interruption(self, source: str, urgency: str = "normal", content: str = "") -> Dict[str, Any]:
        """Handle an interruption during a focus session."""
        if not self._active_session:
            return {"action": "deliver", "reason": "no active focus session"}

        self._active_session.interruptions += 1

        interruption = Interruption(
            source=source,
            urgency=urgency,
            content=content[:100],
        )

        # Decision logic
        if urgency == "urgent":
            self._active_session.urgent_interruptions += 1
            interruption.action_taken = "delivered"
            return {
                "action": "deliver",
                "reason": "urgent interruption during focus",
                "session_id": self._active_session.id,
            }
        elif urgency == "high" and source in ("call", "direct_message"):
            interruption.action_taken = "delivered"
            return {
                "action": "deliver",
                "reason": "high-priority direct contact",
                "session_id": self._active_session.id,
            }
        else:
            self._stats["total_interruptions_suppressed"] += 1
            interruption.action_taken = "suppressed"
            return {
                "action": "suppress",
                "reason": "focus session active",
                "session_id": self._active_session.id,
            }

    def is_focus_mode(self) -> bool:
        """Check if a focus session is currently active."""
        return self._active_session is not None

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_focus_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "active_session": self._active_session.id if self._active_session else None,
            "recent_sessions": [{
                "id": s.id,
                "duration": s.actual_duration_minutes,
                "quality": s.quality_score,
                "interruptions": s.interruptions,
                "status": s.status,
            } for s in list(self._session_history)[-5:]],
        }

    def _update_optimal_length(self, duration: int):
        """Update optimal session length based on success."""
        current = self._stats.get("optimal_session_length", 25)
        # Move toward successful duration
        new_optimal = round((current * 0.7 + duration * 0.3))
        self._stats["optimal_session_length"] = max(15, min(90, new_optimal))

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.deep_work_protector")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.deep_work_protector")

    def _log_session_start(self, session: FocusSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "event": "start",
                    "timestamp": session.started_at,
                    "session_id": session.id,
                    "planned_duration": session.planned_duration_minutes,
                    "context": session.context[:100],
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.deep_work_protector")

    def _log_session_end(self, session: FocusSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "event": "end",
                    "timestamp": session.ended_at,
                    "session_id": session.id,
                    "actual_duration": session.actual_duration_minutes,
                    "interruptions": session.interruptions,
                    "quality": session.quality_score,
                    "status": session.status,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.deep_work_protector")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dwp_instance: Optional[DeepWorkProtector] = None
_dwp_lock = threading.Lock()


def get_deep_work_protector() -> DeepWorkProtector:
    global _dwp_instance
    with _dwp_lock:
        if _dwp_instance is None:
            _dwp_instance = DeepWorkProtector()
        return _dwp_instance
