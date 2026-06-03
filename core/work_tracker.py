"""
LOVE Real-Time Work Tracker — Wave 28

Guardian only sees Git commits. That means meetings, docs, debugging, design,
and deep focus sessions are invisible. This tracker fills the gap.

Signals tracked:
- Focus mode sessions (from FocusMode.jsx)
- Manual session start/stop via API
- Calendar events (future: Google Calendar)
- Heartbeat pings while app is open

Total hours today = Git commits + tracked sessions (whichever is higher, merged).
"""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
WORK_SESSION_LOG = DATA_DIR / "work_sessions.jsonl"
_lock = threading.Lock()


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


class RealtimeWorkTracker:
    """Track work sessions in real-time across multiple signals."""

    def __init__(self):
        self.current_session: Optional[Dict] = None
        self.session_start: Optional[datetime] = None
        DATA_DIR.mkdir(exist_ok=True)

    def start_session(self, activity: str = "general", context: str = "") -> Dict[str, Any]:
        """Start tracking a work session."""
        with _lock:
            if self.current_session:
                # Auto-close previous session
                self._close_session_internal()

            self.session_start = datetime.now()
            self.current_session = {
                "start": self.session_start.isoformat(),
                "activity": activity,
                "context": context,
                "signals": [],
                "date": _today_str(),
            }
        return {"status": "started", "start": self.session_start.isoformat(), "activity": activity}

    def end_session(self) -> Dict[str, Any]:
        """End current work session and persist."""
        with _lock:
            return self._close_session_internal()

    def _close_session_internal(self) -> Dict[str, Any]:
        """Internal: close and save session (must hold _lock)."""
        if not self.current_session or not self.session_start:
            return {"status": "no_session"}

        duration_h = (datetime.now() - self.session_start).total_seconds() / 3600
        self.current_session["end"] = datetime.now().isoformat()
        self.current_session["duration_hours"] = round(duration_h, 4)

        try:
            with open(WORK_SESSION_LOG, "a") as f:
                f.write(json.dumps(self.current_session) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.work_tracker")

        result = {
            "status": "saved",
            "activity": self.current_session["activity"],
            "duration_hours": self.current_session["duration_hours"],
            "context": self.current_session.get("context", ""),
        }
        self.current_session = None
        self.session_start = None
        return result

    def log_signal(self, signal_type: str, data: Dict) -> None:
        """Log a work signal into the current session (e.g. git commit, window change)."""
        with _lock:
            if self.current_session:
                self.current_session.setdefault("signals", []).append({
                    "type": signal_type,
                    "ts": datetime.now().isoformat(),
                    "data": data,
                })

    def log_focus_session(self, preset: str, duration_minutes: int, task: str = "") -> Dict[str, Any]:
        """
        Directly log a completed focus session.
        This is the primary integration point for FocusMode.jsx.
        """
        entry = {
            "start": (datetime.now() - timedelta(minutes=duration_minutes)).isoformat(),
            "end": datetime.now().isoformat(),
            "activity": "focus",
            "context": f"{preset}: {task}" if task else preset,
            "duration_hours": round(duration_minutes / 60, 4),
            "signals": [{"type": "focus_complete", "ts": datetime.now().isoformat(),
                         "data": {"preset": preset, "duration_min": duration_minutes, "task": task}}],
            "date": _today_str(),
        }
        try:
            with open(WORK_SESSION_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.work_tracker")
        return {"status": "logged", "duration_hours": entry["duration_hours"], "context": entry["context"]}

    def get_today_hours(self) -> float:
        """Get total tracked work hours today (excludes Git commits — add those separately)."""
        today = _today_str()
        total = 0.0
        try:
            if WORK_SESSION_LOG.exists():
                for line in WORK_SESSION_LOG.read_text(encoding="utf-8").strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        s = json.loads(line)
                        if s.get("date") == today:
                            total += s.get("duration_hours", 0)
                    except Exception as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.work_tracker")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.work_tracker")
        return round(total, 2)

    def get_today_sessions(self) -> List[Dict[str, Any]]:
        """Return all sessions logged today."""
        today = _today_str()
        sessions = []
        try:
            if WORK_SESSION_LOG.exists():
                for line in WORK_SESSION_LOG.read_text(encoding="utf-8").strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        s = json.loads(line)
                        if s.get("date") == today:
                            sessions.append(s)
                    except Exception as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.work_tracker")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.work_tracker")
        return sessions

    def get_status(self) -> Dict[str, Any]:
        """Return current tracking status."""
        with _lock:
            active = self.current_session is not None
            elapsed = 0.0
            if active and self.session_start:
                elapsed = (datetime.now() - self.session_start).total_seconds() / 3600

        return {
            "active": active,
            "activity": self.current_session.get("activity") if active else None,
            "elapsed_hours": round(elapsed, 4),
            "today_tracked_hours": self.get_today_hours(),
            "today_sessions": len(self.get_today_sessions()),
        }


# ── Singleton ──────────────────────────────────────────────────────────────────

_tracker: Optional[RealtimeWorkTracker] = None
_tracker_lock = threading.Lock()


def get_work_tracker() -> RealtimeWorkTracker:
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = RealtimeWorkTracker()
    return _tracker
