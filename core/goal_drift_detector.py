"""
LOVE Goal Drift Detector — Proactive Goal Alignment Monitor

Warns the user when their daily activities drift from stated goals.
Uses activity alignment scores and progress tracking to detect:
- Goal drift (low-alignment activities dominating recent history)
- Procrastination (no progress on high-priority goals for N days)

Design principles (per .cursorrules):
- Proactive by design: detects drift before the user asks
- Pattern-aware: stores structured data for future reasoning
- Warm, specific, opinionated language over generic assistant phrasing
"""

import json
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Data storage
_DATA_DIR = Path(__file__).parent.parent / "data" / "goal_drift"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_GOALS_FILE = _DATA_DIR / "goals.json"
_ACTIVITIES_FILE = _DATA_DIR / "activities.json"
_ALERTS_FILE = _DATA_DIR / "alerts.json"
_STATS_FILE = _DATA_DIR / "stats.json"

# Constants
_LOW_ALIGNMENT_THRESHOLD = 0.4
_DRIFT_LOOKBACK_DAYS = 7
_PROCRASTINATION_DAYS = 3
_HIGH_PRIORITY_THRESHOLD = 0.7


@dataclass
class Goal:
    goal_id: str
    description: str
    priority: float  # 0.0–1.0
    target_metrics: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_progress_at: Optional[str] = None
    current_value: float = 0.0


@dataclass
class Activity:
    activity_id: str
    activity_type: str
    description: str
    duration: float  # minutes
    goal_alignment_score: float  # 0.0–1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    linked_goal_ids: List[str] = field(default_factory=list)


@dataclass
class DriftAlert:
    alert_id: str
    alert_type: str  # "drift" | "procrastination"
    severity: str  # "low" | "medium" | "high"
    score: float  # 0.0–1.0
    message: str
    goal_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    acknowledged: bool = False


class GoalDriftDetector:
    """
    Singleton detector that monitors goal alignment and warns on drift.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._goals: Dict[str, Goal] = {}
        self._activities: List[Activity] = []
        self._alerts: List[DriftAlert] = []
        self._stats = {
            "total_goals_registered": 0,
            "total_activities_logged": 0,
            "total_alerts_raised": 0,
            "last_drift_scan": None,
        }
        self._load_data()

    # ── Persistence ──────────────────────────────────────────────────────

    def _load_data(self):
        if _GOALS_FILE.exists():
            try:
                raw = json.loads(_GOALS_FILE.read_text(encoding="utf-8"))
                for gid, g in raw.items():
                    self._goals[gid] = Goal(**g)
            except Exception:
                pass
        if _ACTIVITIES_FILE.exists():
            try:
                raw = json.loads(_ACTIVITIES_FILE.read_text(encoding="utf-8"))
                self._activities = [Activity(**a) for a in raw]
            except Exception:
                pass
        if _ALERTS_FILE.exists():
            try:
                raw = json.loads(_ALERTS_FILE.read_text(encoding="utf-8"))
                self._alerts = [DriftAlert(**a) for a in raw]
            except Exception:
                pass
        if _STATS_FILE.exists():
            try:
                self._stats = json.loads(_STATS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save_goals(self):
        try:
            _GOALS_FILE.write_text(
                json.dumps({gid: asdict(g) for gid, g in self._goals.items()}, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _save_activities(self):
        try:
            _ACTIVITIES_FILE.write_text(
                json.dumps([asdict(a) for a in self._activities], indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _save_alerts(self):
        try:
            _ALERTS_FILE.write_text(
                json.dumps([asdict(a) for a in self._alerts], indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _save_stats(self):
        try:
            _STATS_FILE.write_text(json.dumps(self._stats, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass

    # ── Public API ─────────────────────────────────────────────────────────

    def set_goal(self, goal_id: str, description: str, priority: float, target_metrics: Dict[str, Any]) -> Goal:
        """Register a user goal."""
        goal = Goal(
            goal_id=goal_id,
            description=description,
            priority=priority,
            target_metrics=target_metrics,
        )
        self._goals[goal_id] = goal
        self._stats["total_goals_registered"] = len(self._goals)
        self._save_goals()
        self._save_stats()
        return goal

    def record_activity(self, activity_type: str, description: str, duration: float, goal_alignment_score: float, linked_goal_ids: Optional[List[str]] = None) -> Activity:
        """Log a daily activity."""
        activity_id = f"act_{int(time.time() * 1000)}_{len(self._activities)}"
        activity = Activity(
            activity_id=activity_id,
            activity_type=activity_type,
            description=description,
            duration=duration,
            goal_alignment_score=goal_alignment_score,
            linked_goal_ids=linked_goal_ids or [],
        )
        self._activities.append(activity)
        self._stats["total_activities_logged"] = len(self._activities)
        self._save_activities()
        self._save_stats()

        # Auto-link to goals if alignment is high and goals exist
        if goal_alignment_score >= 0.6 and not activity.linked_goal_ids:
            for gid, goal in self._goals.items():
                # Simple keyword match for linkage
                if any(kw in description.lower() for kw in goal.description.lower().split()):
                    activity.linked_goal_ids.append(gid)
                    # Update goal progress
                    goal.current_value += duration
                    goal.last_progress_at = activity.timestamp
            if activity.linked_goal_ids:
                self._save_activities()
                self._save_goals()

        return activity

    def detect_drift(self) -> List[DriftAlert]:
        """Compare recent activities to stated goals and detect drift."""
        cutoff = datetime.now() - timedelta(days=_DRIFT_LOOKBACK_DAYS)
        recent = [
            a for a in self._activities
            if datetime.fromisoformat(a.timestamp) >= cutoff
        ]

        new_alerts: List[DriftAlert] = []

        # 1. Alignment drift: low-alignment activities dominate recent history
        if recent:
            low_alignment = [a for a in recent if a.goal_alignment_score < _LOW_ALIGNMENT_THRESHOLD]
            total_duration = sum(a.duration for a in recent)
            low_duration = sum(a.duration for a in low_alignment)

            if total_duration > 0:
                drift_ratio = low_duration / total_duration
                if drift_ratio >= 0.5:
                    severity = self._severity(drift_ratio)
                    alert = DriftAlert(
                        alert_id=f"drift_{int(time.time() * 1000)}",
                        alert_type="drift",
                        severity=severity,
                        score=round(drift_ratio, 3),
                        message=(
                            f"You've spent {int(drift_ratio * 100)}% of your recent time on "
                            f"activities that don't align with your goals. "
                            f"That's not accidental — it's a pattern. Want to recalibrate?"
                        ),
                    )
                    new_alerts.append(alert)

        # 2. Procrastination: no progress on high-priority goals for N days
        for gid, goal in self._goals.items():
            if goal.priority < _HIGH_PRIORITY_THRESHOLD:
                continue
            last_progress = goal.last_progress_at or goal.created_at
            try:
                last_dt = datetime.fromisoformat(last_progress)
            except Exception:
                last_dt = datetime.now()
            days_since = (datetime.now() - last_dt).days

            if days_since >= _PROCRASTINATION_DAYS:
                score = min(1.0, days_since / 7.0)
                severity = self._severity(score)
                alert = DriftAlert(
                    alert_id=f"proc_{gid}_{int(time.time() * 1000)}",
                    alert_type="procrastination",
                    severity=severity,
                    score=round(score, 3),
                    goal_id=gid,
                    message=(
                        f"Your goal '{goal.description}' has been untouched for {days_since} days. "
                        f"It's a high-priority commitment — even 10 minutes today moves the needle."
                    ),
                )
                new_alerts.append(alert)

        # Persist new alerts
        if new_alerts:
            self._alerts.extend(new_alerts)
            self._stats["total_alerts_raised"] = len(self._alerts)
            self._stats["last_drift_scan"] = datetime.now().isoformat()
            self._save_alerts()
            self._save_stats()
        else:
            self._stats["last_drift_scan"] = datetime.now().isoformat()
            self._save_stats()

        return new_alerts

    def get_drift_alerts(self, include_acknowledged: bool = False) -> List[Dict[str, Any]]:
        """Return active drift warnings with severity."""
        alerts = self._alerts if include_acknowledged else [a for a in self._alerts if not a.acknowledged]
        return [asdict(a) for a in sorted(alerts, key=lambda x: x.created_at, reverse=True)]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for a in self._alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                self._save_alerts()
                return True
        return False

    def get_goal_progress(self, goal_id: str) -> Dict[str, Any]:
        """Return progress toward a specific goal."""
        goal = self._goals.get(goal_id)
        if not goal:
            return {"error": f"Goal {goal_id} not found"}

        # Compute progress ratio against target if numeric target exists
        target = goal.target_metrics.get("target_value")
        progress_ratio = 0.0
        if target and isinstance(target, (int, float)) and target > 0:
            progress_ratio = min(1.0, goal.current_value / target)

        # Recent activities linked to this goal
        cutoff = datetime.now() - timedelta(days=_DRIFT_LOOKBACK_DAYS)
        recent = [
            a for a in self._activities
            if goal_id in a.linked_goal_ids and datetime.fromisoformat(a.timestamp) >= cutoff
        ]

        return {
            "goal_id": goal_id,
            "description": goal.description,
            "priority": goal.priority,
            "target_metrics": goal.target_metrics,
            "current_value": goal.current_value,
            "progress_ratio": round(progress_ratio, 3),
            "last_progress_at": goal.last_progress_at,
            "days_since_progress": (
                (datetime.now() - datetime.fromisoformat(goal.last_progress_at)).days
                if goal.last_progress_at else None
            ),
            "recent_activity_count": len(recent),
            "recent_duration_minutes": round(sum(a.duration for a in recent), 1),
        }

    def get_drift_stats(self) -> Dict[str, Any]:
        """Return detector statistics."""
        active_alerts = len([a for a in self._alerts if not a.acknowledged])
        high_severity = len([a for a in self._alerts if a.severity == "high" and not a.acknowledged])
        return {
            **self._stats,
            "active_alerts": active_alerts,
            "high_severity_alerts": high_severity,
            "goal_count": len(self._goals),
            "activity_count": len(self._activities),
        }

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _severity(score: float) -> str:
        """Map a 0–1 score to severity tier."""
        if score >= 0.7:
            return "high"
        elif score >= 0.5:
            return "medium"
        return "low"


# ═══════════════════════════════════════════════════════════════════════════════
# Global Access
# ═══════════════════════════════════════════════════════════════════════════════

_detector: Optional[GoalDriftDetector] = None
_detector_lock = threading.Lock()


def get_goal_drift_detector() -> GoalDriftDetector:
    global _detector
    with _detector_lock:
        if _detector is None:
            _detector = GoalDriftDetector()
        return _detector
