"""
LOVE Writing Coach — Writing Intelligence (Modern AI Pattern)

Most writing tools are grammar checkers. This coach:

1. WRITING SESSION TRACKING
   - Record writing sessions (type, duration, word count, quality)
   - Track writing velocity and consistency
   - Log flow state indicators (interruptions, focus depth)

2. PATTERN ANALYSIS
   - Identify peak writing times and conditions
   - Detect writer's block patterns
   - Track project progress and word count goals

3. QUALITY INSIGHTS
   - Track clarity, structure, and engagement metrics
   - Identify overused phrases or weak constructions
   - Suggest improvements based on writing goals

4. PROACTIVE COACHING
   - Suggest writing sprints when energy is high
   - Recommend breaks when quality drops
   - Celebrate milestones and consistency

Architecture:
- record_session(project, words, duration, quality): Log writing session
- get_writing_stats(): Get writing analytics
- get_suggestion(): Get personalized writing coaching
- get_flow_score(): Calculate writing flow state score
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "writing_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WritingSession:
    """A writing session."""
    project: str = ""
    session_type: str = ""  # drafting, editing, outlining, brainstorming, polishing
    word_count: int = 0
    duration_minutes: float = 0.0
    quality_score: float = 0.5  # 0-1
    flow_score: float = 0.5
    interruptions: int = 0
    clarity_rating: float = 0.5
    structure_rating: float = 0.5
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class WritingProject:
    """A writing project being tracked."""
    name: str = ""
    goal_words: int = 0
    current_words: int = 0
    project_type: str = ""  # blog, book, essay, documentation, creative
    deadline: Optional[str] = None
    status: str = "active"  # active, paused, completed, abandoned
    start_date: str = field(default_factory=lambda: datetime.now().isoformat())


class WritingCoach:
    """
    Personal writing coach with flow state intelligence.
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
        self._sessions: deque = deque(maxlen=500)
        self._projects: Dict[str, WritingProject] = {}
        self._stats = {
            "total_sessions": 0,
            "total_words": 0,
            "total_minutes": 0,
            "avg_words_per_session": 0,
            "avg_wpm": 0.0,
            "current_streak": 0,
            "projects_completed": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, project: str = "", session_type: str = "", word_count: int = 0, duration: float = 0, quality: float = 0.5, flow: float = 0.5, interruptions: int = 0, clarity: float = 0.5, structure: float = 0.5, notes: str = "") -> WritingSession:
        """Record a writing session."""
        session = WritingSession(
            project=project or "general",
            session_type=session_type or "drafting",
            word_count=word_count,
            duration_minutes=duration,
            quality_score=quality,
            flow_score=flow,
            interruptions=interruptions,
            clarity_rating=clarity,
            structure_rating=structure,
            notes=notes,
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._stats["total_words"] += word_count
            self._stats["total_minutes"] += duration
            self._update_streak(session)
            self._update_stats(session)

            # Update project progress
            if project and project in self._projects:
                self._projects[project].current_words += word_count
                if self._projects[project].current_words >= self._projects[project].goal_words:
                    self._projects[project].status = "completed"
                    self._stats["projects_completed"] += 1

        self._save_stats()
        self._log_session(session)

        return session

    def add_project(self, name: str, goal_words: int = 0, project_type: str = "", deadline: Optional[str] = None):
        """Add a writing project to track."""
        self._projects[name] = WritingProject(
            name=name,
            goal_words=goal_words,
            project_type=project_type or "general",
            deadline=deadline,
        )
        self._save_stats()

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_writing_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get writing analytics."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in self._sessions if s.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Velocity
        total_words = sum(s.word_count for s in recent)
        total_minutes = sum(s.duration_minutes for s in recent)
        avg_wpm = total_words / max(1, total_minutes)

        # Quality trends
        avg_quality = sum(s.quality_score for s in recent) / len(recent)
        avg_flow = sum(s.flow_score for s in recent) / len(recent)
        avg_clarity = sum(s.clarity_rating for s in recent) / len(recent)
        avg_structure = sum(s.structure_rating for s in recent) / len(recent)

        # Type breakdown
        by_type = defaultdict(lambda: {"count": 0, "words": 0, "minutes": 0})
        for s in recent:
            t = s.session_type
            by_type[t]["count"] += 1
            by_type[t]["words"] += s.word_count
            by_type[t]["minutes"] += s.duration_minutes

        # Daily word counts
        daily_words = defaultdict(int)
        for s in recent:
            day = s.timestamp[:10]
            daily_words[day] += s.word_count

        # Project progress
        project_status = []
        for name, proj in self._projects.items():
            pct = (proj.current_words / max(1, proj.goal_words)) * 100 if proj.goal_words > 0 else 0
            project_status.append({
                "name": name,
                "words": proj.current_words,
                "goal": proj.goal_words,
                "pct": round(pct, 1),
                "status": proj.status,
            })

        return {
            "days_analyzed": len(set(s.timestamp[:10] for s in recent)),
            "total_sessions": len(recent),
            "total_words": total_words,
            "total_minutes": round(total_minutes, 1),
            "avg_wpm": round(avg_wpm, 1),
            "avg_quality": round(avg_quality, 2),
            "avg_flow": round(avg_flow, 2),
            "avg_clarity": round(avg_clarity, 2),
            "avg_structure": round(avg_structure, 2),
            "current_streak": self._stats["current_streak"],
            "type_breakdown": {k: dict(v) for k, v in by_type.items()},
            "daily_word_counts": dict(daily_words),
            "projects": project_status,
        }

    def get_suggestion(self) -> Dict[str, Any]:
        """Get personalized writing coaching suggestion."""
        recent = list(self._sessions)[-10:]
        if not recent:
            return {
                "suggestion": "Start tracking your writing sessions to get personalized coaching.",
                "action": "Write for 25 minutes and log the session.",
            }

        avg_flow = sum(s.flow_score for s in recent) / len(recent)
        avg_quality = sum(s.quality_score for s in recent) / len(recent)
        avg_interruptions = sum(s.interruptions for s in recent) / len(recent)

        suggestions = []
        actions = []

        if avg_flow < 0.4:
            suggestions.append("Your flow state has been low. Try the Pomodoro technique: 25 min writing, 5 min break.")
            actions.append("Set a timer for 25 minutes. No interruptions allowed.")
        elif avg_flow > 0.8:
            suggestions.append("You're in a great flow state. Keep the momentum going!")
            actions.append("Extend your current session by 15 minutes while the flow lasts.")

        if avg_interruptions > 2:
            suggestions.append("You're getting interrupted a lot. Consider turning off notifications.")
            actions.append("Put your phone in another room. Close Slack. Deep work mode.")

        if avg_quality < 0.5:
            suggestions.append("Writing quality is dipping. You might be tired or distracted.")
            actions.append("Take a 10-minute walk, then come back fresh.")

        # Check project deadlines
        for name, proj in self._projects.items():
            if proj.status == "active" and proj.deadline:
                try:
                    days_to_deadline = (datetime.fromisoformat(proj.deadline) - datetime.now()).days
                    if days_to_deadline < 7 and days_to_deadline > 0:
                        words_needed = max(0, proj.goal_words - proj.current_words)
                        daily_needed = words_needed / days_to_deadline
                        suggestions.append(f"'{name}' deadline in {days_to_deadline} days. You need {int(daily_needed)} words/day.")
                except Exception:
                    pass

        return {
            "suggestions": suggestions[:3],
            "actions": actions[:2],
            "current_flow_state": "high" if avg_flow > 0.7 else "medium" if avg_flow > 0.4 else "low",
        }

    def get_flow_score(self) -> int:
        """Calculate current writing flow score (0-100)."""
        if not self._sessions:
            return 0

        recent = list(self._sessions)[-10:]
        n = len(recent)

        # Flow quality
        avg_flow = sum(s.flow_score for s in recent) / n
        flow_score = avg_flow * 100

        # Consistency
        daily_sessions = len(set(s.timestamp[:10] for s in recent))
        consistency_score = min(100, daily_sessions * 14)

        # Low interruption bonus
        avg_interruptions = sum(s.interruptions for s in recent) / n
        focus_score = max(0, 100 - avg_interruptions * 20)

        overall = round(flow_score * 0.5 + consistency_score * 0.2 + focus_score * 0.3)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_streak(self, session: WritingSession):
        """Update writing streak."""
        today = datetime.now().date()
        try:
            session_date = datetime.fromisoformat(session.timestamp).date()
        except Exception:
            session_date = today

        if self._sessions and len(self._sessions) > 1:
            try:
                last_session = list(self._sessions)[-2]
                last_date = datetime.fromisoformat(last_session.timestamp).date()
                if (session_date - last_date).days == 1:
                    self._stats["current_streak"] += 1
                elif (session_date - last_date).days > 1:
                    self._stats["current_streak"] = 1
            except Exception:
                self._stats["current_streak"] = 1
        else:
            self._stats["current_streak"] = 1

    def _update_stats(self, session: WritingSession):
        """Update running statistics."""
        n = self._stats["total_sessions"]
        self._stats["avg_words_per_session"] = round((self._stats["avg_words_per_session"] * (n - 1) + session.word_count) / n, 1)
        if session.duration_minutes > 0:
            wpm = session.word_count / session.duration_minutes
            self._stats["avg_wpm"] = round((self._stats["avg_wpm"] * (n - 1) + wpm) / n, 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "projects": {k: {
                    "name": v.name,
                    "goal_words": v.goal_words,
                    "current_words": v.current_words,
                    "status": v.status,
                    "deadline": v.deadline,
                } for k, v in self._projects.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("projects", {}).items():
                    self._projects[k] = WritingProject(**v)
        except Exception:
            pass

    def _log_session(self, session: WritingSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "project": session.project,
                    "type": session.session_type,
                    "words": session.word_count,
                    "minutes": session.duration_minutes,
                    "flow": session.flow_score,
                    "quality": session.quality_score,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wc_instance: Optional[WritingCoach] = None
_wc_lock = threading.Lock()


def get_writing_coach() -> WritingCoach:
    global _wc_instance
    with _wc_lock:
        if _wc_instance is None:
            _wc_instance = WritingCoach()
        return _wc_instance
