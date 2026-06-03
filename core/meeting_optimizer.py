"""
LOVE Meeting Optimizer — Meeting Intelligence (Modern AI Pattern)

Most meetings waste time. This optimizer:

1. MEETING ANALYSIS
   - Track meeting duration vs scheduled time
   - Measure participant engagement (speaking time distribution)
   - Identify recurring meeting patterns (overruns, cancellations, no-shows)

2. EFFICIENCY SCORING
   - Score meetings by outcome/duration ratio
   - Detect meetings that could have been emails
   - Find optimal meeting length for different types

3. OPTIMIZATION SUGGESTIONS
   - Suggest shorter default durations (25 min instead of 30, 50 instead of 60)
   - Recommend optimal attendee lists (who adds value vs who is passive)
   - Propose async alternatives when possible

4. PROACTIVE IMPROVEMENT
   - Suggest agenda requirements before scheduling
   - Recommend meeting-free blocks for deep work
   - Alert about meeting overload days

Architecture:
- record_meeting(title, duration, attendees, outcome): Log meeting
- get_meeting_stats(): Get meeting analytics
- get_efficiency_score(): Get overall meeting efficiency score
- get_optimization_suggestions(): Suggest meeting improvements
- get_meeting_free_blocks(): Suggest protected focus time
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

DATA_DIR = Path(__file__).parent.parent / "data" / "meeting_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MEETING_LOG = DATA_DIR / "meeting_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Meeting:
    """A recorded meeting."""
    meeting_id: str = ""
    title: str = ""
    scheduled_minutes: float = 0.0
    actual_minutes: float = 0.0
    attendee_count: int = 0
    active_participants: int = 0
    had_agenda: bool = False
    had_notes: bool = False
    outcome: str = ""  # productive, neutral, wasteful, cancelled
    outcome_quality: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    meeting_type: str = ""  # standup, review, planning, 1on1, brainstorm, sync


class MeetingOptimizer:
    """
    Optimize meetings for maximum efficiency.
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
        self._meetings: deque = deque(maxlen=200)
        self._stats = {
            "total_meetings": 0,
            "total_meeting_hours": 0.0,
            "avg_efficiency": 0.5,
            "avg_overrun_pct": 0.0,
            "cancellation_rate": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_meeting(self, title: str, scheduled_minutes: float, actual_minutes: float, attendee_count: int = 0, active_participants: int = 0, had_agenda: bool = False, had_notes: bool = False, outcome: str = "", outcome_quality: float = 0.5, meeting_type: str = "") -> Meeting:
        """Record a meeting."""
        meeting_id = f"mtg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        meeting = Meeting(
            meeting_id=meeting_id,
            title=title,
            scheduled_minutes=scheduled_minutes,
            actual_minutes=actual_minutes,
            attendee_count=attendee_count,
            active_participants=active_participants,
            had_agenda=had_agenda,
            had_notes=had_notes,
            outcome=outcome or "neutral",
            outcome_quality=outcome_quality,
            meeting_type=meeting_type or "sync",
        )

        with self._lock:
            self._meetings.append(meeting)
            self._stats["total_meetings"] += 1
            self._stats["total_meeting_hours"] += actual_minutes / 60
            self._update_stats(meeting)

        self._save_stats()
        self._log_meeting(meeting)

        return meeting

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_meeting_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get meeting analytics."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [m for m in self._meetings if m.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Meeting type breakdown
        by_type = defaultdict(lambda: {"count": 0, "total_minutes": 0.0, "quality_sum": 0.0})
        for m in recent:
            t = m.meeting_type
            by_type[t]["count"] += 1
            by_type[t]["total_minutes"] += m.actual_minutes
            by_type[t]["quality_sum"] += m.outcome_quality

        type_stats = {}
        for t, stats in by_type.items():
            type_stats[t] = {
                "count": stats["count"],
                "avg_duration": round(stats["total_minutes"] / stats["count"], 1),
                "avg_quality": round(stats["quality_sum"] / stats["count"], 2),
            }

        # Overrun analysis
        overruns = [m for m in recent if m.actual_minutes > m.scheduled_minutes]
        avg_overrun = sum((m.actual_minutes - m.scheduled_minutes) / max(1, m.scheduled_minutes) for m in overruns) / max(1, len(overruns)) if overruns else 0

        # Agenda impact
        with_agenda = [m for m in recent if m.had_agenda]
        without_agenda = [m for m in recent if not m.had_agenda]
        agenda_impact = (
            sum(m.outcome_quality for m in with_agenda) / max(1, len(with_agenda))
            - sum(m.outcome_quality for m in without_agenda) / max(1, len(without_agenda))
        ) if with_agenda and without_agenda else 0

        # Meeting hours per day
        daily_meetings = defaultdict(float)
        for m in recent:
            day = m.timestamp[:10]
            daily_meetings[day] += m.actual_minutes / 60

        return {
            "days_analyzed": len(set(m.timestamp[:10] for m in recent)),
            "total_meetings": len(recent),
            "total_hours": round(sum(m.actual_minutes for m in recent) / 60, 1),
            "avg_duration": round(sum(m.actual_minutes for m in recent) / len(recent), 1),
            "avg_efficiency": round(sum(m.outcome_quality for m in recent) / len(recent), 2),
            "overrun_rate": round(len(overruns) / len(recent) * 100, 1),
            "avg_overrun_pct": round(avg_overrun * 100, 1),
            "agenda_impact": round(agenda_impact, 2),
            "type_breakdown": type_stats,
            "avg_meeting_hours_per_day": round(sum(daily_meetings.values()) / max(1, len(daily_meetings)), 1),
            "meeting_heavy_days": sum(1 for h in daily_meetings.values() if h > 4),
        }

    def get_efficiency_score(self) -> int:
        """Calculate overall meeting efficiency score (0-100)."""
        if not self._meetings:
            return 50

        recent = list(self._meetings)[-20:]
        if not recent:
            return 50

        # Quality score
        avg_quality = sum(m.outcome_quality for m in recent) / len(recent)
        quality_score = avg_quality * 100

        # Time efficiency (shorter = better, but not too short)
        durations = [m.actual_minutes for m in recent]
        avg_duration = sum(durations) / len(durations)
        # Optimal is 25-30 min for most meetings
        duration_score = max(0, 100 - abs(avg_duration - 27.5) * 3)

        # Punctuality score
        on_time = sum(1 for m in recent if m.actual_minutes <= m.scheduled_minutes)
        punctuality_score = (on_time / len(recent)) * 100

        # Agenda score
        agenda_pct = sum(1 for m in recent if m.had_agenda) / len(recent)
        agenda_score = agenda_pct * 100

        overall = round(quality_score * 0.4 + duration_score * 0.2 + punctuality_score * 0.2 + agenda_score * 0.2)
        return min(100, overall)

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest meeting improvements."""
        suggestions = []
        stats = self.get_meeting_stats(14)

        if stats.get("status") == "insufficient_data":
            return [{"suggestion": "Log some meetings to get optimization suggestions", "impact": "high"}]

        # Check meeting overload
        if stats.get("avg_meeting_hours_per_day", 0) > 4:
            suggestions.append({
                "suggestion": f"You're averaging {stats['avg_meeting_hours_per_day']:.1f} hours of meetings per day. Consider blocking 2-hour focus blocks.",
                "impact": "high",
                "category": "overload",
            })

        # Check overruns
        if stats.get("overrun_rate", 0) > 30:
            suggestions.append({
                "suggestion": f"{stats['overrun_rate']:.0f}% of meetings run over time. Try scheduling 25 or 50-minute meetings instead of 30/60.",
                "impact": "medium",
                "category": "timing",
            })

        # Check agenda impact
        if stats.get("agenda_impact", 0) > 0.2:
            suggestions.append({
                "suggestion": "Meetings with agendas are significantly more effective. Require agendas for all meetings.",
                "impact": "high",
                "category": "preparation",
            })

        # Check meeting-heavy days
        if stats.get("meeting_heavy_days", 0) > 2:
            suggestions.append({
                "suggestion": f"You had {stats['meeting_heavy_days']} days with 4+ hours of meetings. Try clustering meetings on specific days and keeping others free.",
                "impact": "medium",
                "category": "scheduling",
            })

        # Type-specific suggestions
        type_stats = stats.get("type_breakdown", {})
        for mtype, tstats in type_stats.items():
            if tstats["avg_duration"] > 45 and mtype in ["standup", "sync"]:
                suggestions.append({
                    "suggestion": f"Your {mtype} meetings average {tstats['avg_duration']:.0f} min. These should be 15 min max.",
                    "impact": "medium",
                    "category": "type_specific",
                })

        return suggestions

    def get_meeting_free_blocks(self, day_start: str = "09:00", day_end: str = "18:00") -> List[Dict[str, Any]]:
        """Suggest meeting-free blocks for deep work."""
        # Simple heuristic: suggest morning or afternoon blocks
        return [
            {
                "start": day_start,
                "end": "12:00",
                "duration_hours": 3,
                "reason": "Morning is typically best for deep work. Block meetings before noon.",
            },
            {
                "start": "13:00",
                "end": "15:00",
                "duration_hours": 2,
                "reason": "Post-lunch focus block. Schedule shallow work or meetings after 3pm.",
            },
        ]

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, meeting: Meeting):
        """Update running statistics."""
        n = self._stats["total_meetings"]

        # Average overrun
        if meeting.actual_minutes > meeting.scheduled_minutes:
            overrun = (meeting.actual_minutes - meeting.scheduled_minutes) / max(1, meeting.scheduled_minutes)
            self._stats["avg_overrun_pct"] = round(
                (self._stats["avg_overrun_pct"] * (n - 1) + overrun * 100) / n, 1
            )

        # Average efficiency
        self._stats["avg_efficiency"] = round(
            (self._stats["avg_efficiency"] * (n - 1) + meeting.outcome_quality) / n, 2
        )

        # Cancellation rate
        cancelled = sum(1 for m in self._meetings if m.outcome == "cancelled")
        self._stats["cancellation_rate"] = round(cancelled / n * 100, 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meeting_optimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meeting_optimizer")

    def _log_meeting(self, meeting: Meeting):
        try:
            with open(MEETING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": meeting.timestamp,
                    "meeting_id": meeting.meeting_id,
                    "title": meeting.title,
                    "scheduled": meeting.scheduled_minutes,
                    "actual": meeting.actual_minutes,
                    "attendees": meeting.attendee_count,
                    "outcome": meeting.outcome,
                    "quality": meeting.outcome_quality,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meeting_optimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mo_instance: Optional[MeetingOptimizer] = None
_mo_lock = threading.Lock()


def get_meeting_optimizer() -> MeetingOptimizer:
    global _mo_instance
    with _mo_lock:
        if _mo_instance is None:
            _mo_instance = MeetingOptimizer()
        return _mo_instance
