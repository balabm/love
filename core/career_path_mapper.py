"""
LOVE Career Path Mapper — Career Intelligence (Modern AI Pattern)

Most career tools are static resume builders. This mapper:

1. CAREER TRACKING
   - Record roles, projects, skills gained, and achievements
   - Track career trajectory and progression velocity
   - Log mentorship, networking, and learning activities

2. PATH ANALYSIS
   - Identify patterns in successful career moves
   - Map skills to potential next roles
   - Detect stagnation or acceleration trends

3. GROWTH OPPORTUNITIES
   - Suggest roles that match current skills + gap
   - Identify lateral moves that build diverse experience
   - Recommend stretch assignments and projects

4. PROACTIVE DEVELOPMENT
   - Alert when skills need updating for target role
   - Suggest networking targets based on career goals
   - Track progress toward long-term career vision

Architecture:
- record_role(title, company, skills, achievements): Log career step
- get_career_trajectory(): Get career progression analysis
- get_next_role_suggestions(): Suggest potential next moves
- get_development_plan(target_role): Get skill development roadmap
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "career_path_mapper"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ROLE_LOG = DATA_DIR / "roles.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CareerRole:
    """A career role or position."""
    title: str = ""
    company: str = ""
    department: str = ""
    start_date: str = ""
    end_date: Optional[str] = None
    skills_gained: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    satisfaction: float = 0.5
    learning_velocity: float = 0.5  # how much you learned
    impact_score: float = 0.5  # measurable impact
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class CareerGoal:
    """A career goal or target."""
    target_role: str = ""
    target_date: Optional[str] = None
    required_skills: List[str] = field(default_factory=list)
    current_skills: List[str] = field(default_factory=list)
    status: str = "active"  # active, achieved, abandoned


class CareerPathMapper:
    """
    Personal career path mapper with trajectory intelligence.
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
        self._roles: deque = deque(maxlen=100)
        self._goals: Dict[str, CareerGoal] = {}
        self._stats = {
            "total_roles": 0,
            "total_skills": 0,
            "avg_satisfaction": 0.5,
            "avg_learning_velocity": 0.5,
            "career_momentum": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_role(self, title: str = "", company: str = "", department: str = "", start_date: str = "", end_date: Optional[str] = None, skills_gained: Optional[List[str]] = None, achievements: Optional[List[str]] = None, satisfaction: float = 0.5, learning_velocity: float = 0.5, impact_score: float = 0.5, notes: str = "") -> CareerRole:
        """Record a career role."""
        role = CareerRole(
            title=title or "unspecified",
            company=company or "unspecified",
            department=department or "",
            start_date=start_date or datetime.now().isoformat(),
            end_date=end_date,
            skills_gained=skills_gained or [],
            achievements=achievements or [],
            satisfaction=satisfaction,
            learning_velocity=learning_velocity,
            impact_score=impact_score,
            notes=notes,
        )

        with self._lock:
            self._roles.append(role)
            self._stats["total_roles"] += 1
            self._stats["total_skills"] = len(set(skill for r in self._roles for skill in r.skills_gained))
            self._update_stats(role)

        self._save_stats()
        self._log_role(role)

        return role

    def add_goal(self, target_role: str, target_date: Optional[str] = None, required_skills: Optional[List[str]] = None, current_skills: Optional[List[str]] = None):
        """Add a career goal."""
        self._goals[target_role] = CareerGoal(
            target_role=target_role,
            target_date=target_date,
            required_skills=required_skills or [],
            current_skills=current_skills or [],
        )
        self._save_stats()

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_career_trajectory(self) -> Dict[str, Any]:
        """Get career progression analysis."""
        if not self._roles:
            return {"status": "insufficient_data"}

        sorted_roles = sorted(self._roles, key=lambda x: x.start_date)
        
        # Trajectory analysis
        satisfactions = [r.satisfaction for r in sorted_roles]
        learnings = [r.learning_velocity for r in sorted_roles]
        impacts = [r.impact_score for r in sorted_roles]

        # Trend analysis
        if len(satisfactions) >= 3:
            first_half = sum(satisfactions[:len(satisfactions)//2]) / max(1, len(satisfactions)//2)
            second_half = sum(satisfactions[len(satisfactions)//2:]) / max(1, len(satisfactions) - len(satisfactions)//2)
            satisfaction_trend = "improving" if second_half > first_half + 0.2 else "declining" if second_half < first_half - 0.2 else "stable"
        else:
            satisfaction_trend = "insufficient_data"

        # All skills collected
        all_skills = set()
        for r in sorted_roles:
            all_skills.update(r.skills_gained)

        # Role progression
        role_history = []
        for r in sorted_roles:
            role_history.append({
                "title": r.title,
                "company": r.company,
                "start": r.start_date,
                "end": r.end_date,
                "duration_months": self._calculate_duration(r.start_date, r.end_date),
                "skills": r.skills_gained[:5],
            })

        return {
            "total_roles": len(sorted_roles),
            "unique_skills": len(all_skills),
            "avg_satisfaction": round(sum(satisfactions) / len(satisfactions), 2),
            "avg_learning": round(sum(learnings) / len(learnings), 2),
            "avg_impact": round(sum(impacts) / len(impacts), 2),
            "satisfaction_trend": satisfaction_trend,
            "career_momentum": round(self._stats["career_momentum"], 2),
            "role_history": role_history,
            "top_skills": sorted(list(all_skills))[:20],
        }

    def get_next_role_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest potential next career moves."""
        trajectory = self.get_career_trajectory()
        if trajectory.get("status") == "insufficient_data":
            return [{"suggestion": "Record some career roles to get path suggestions.", "type": "general"}]

        current_skills = set(trajectory.get("top_skills", []))
        suggestions = []

        # Lateral moves (build breadth)
        suggestions.append({
            "type": "lateral",
            "suggestion": "Consider a lateral move to build cross-functional experience.",
            "reason": "You've built depth. Breadth will make you more versatile.",
            "example": "If you're an engineer, try product management or data science.",
        })

        # Vertical moves (build depth)
        if trajectory.get("avg_learning", 0) > 0.6:
            suggestions.append({
                "type": "vertical",
                "suggestion": "You're learning fast. Consider a senior or lead role.",
                "reason": f"Your learning velocity is {trajectory['avg_learning']:.1f}/1.0. You're ready for more scope.",
                "example": "Senior Engineer, Team Lead, or Principal role.",
            })

        # Skill gap moves
        for goal in self._goals.values():
            if goal.status == "active":
                gap = set(goal.required_skills) - current_skills
                if gap:
                    suggestions.append({
                        "type": "skill_build",
                        "suggestion": f"To reach '{goal.target_role}', focus on: {', '.join(list(gap)[:3])}",
                        "reason": f"You need {len(gap)} more skills for your target role.",
                        "target_date": goal.target_date,
                    })
                else:
                    suggestions.append({
                        "type": "ready",
                        "suggestion": f"You have all the skills for '{goal.target_role}'! Start applying.",
                        "reason": "Your skill set matches the target role requirements.",
                    })

        # If satisfaction is declining, suggest change
        if trajectory.get("satisfaction_trend") == "declining":
            suggestions.insert(0, {
                "type": "urgent",
                "suggestion": "Your satisfaction has been declining. It's time for a change.",
                "reason": "Career satisfaction is a leading indicator of burnout. Act before it gets worse.",
                "action": "Update your resume and start networking this week.",
            })

        return suggestions

    def get_development_plan(self, target_role: str = "") -> Dict[str, Any]:
        """Get skill development roadmap."""
        goal = self._goals.get(target_role)
        if not goal:
            return {"status": "goal_not_found"}

        current_skills = set()
        for r in self._roles:
            current_skills.update(r.skills_gained)

        gaps = list(set(goal.required_skills) - current_skills)
        strengths = list(set(goal.required_skills) & current_skills)

        # Learning path suggestions
        learning_paths = {
            "leadership": ["Take a management course", "Lead a cross-team project", "Find a mentor who is a manager"],
            "technical": ["Build a side project", "Contribute to open source", "Get a certification"],
            "communication": ["Join Toastmasters", "Start a blog", "Present at a conference"],
            "business": ["Read 5 business books", "Shadow a product manager", "Take an MBA course"],
        }

        actions = []
        for gap in gaps[:3]:
            # Determine category
            if any(word in gap.lower() for word in ["manage", "lead", "team"]):
                category = "leadership"
            elif any(word in gap.lower() for word in ["code", "engineer", "data", "cloud"]):
                category = "technical"
            elif any(word in gap.lower() for word in ["communicate", "present", "write"]):
                category = "communication"
            else:
                category = "business"

            actions.append({
                "skill": gap,
                "category": category,
                "suggested_actions": learning_paths.get(category, ["Research and practice this skill"])[:2],
                "timeline": "3-6 months",
            })

        return {
            "target_role": target_role,
            "target_date": goal.target_date,
            "strengths": strengths[:5],
            "gaps": gaps,
            "development_actions": actions,
            "progress_pct": round(len(strengths) / max(1, len(goal.required_skills)) * 100, 1),
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _calculate_duration(self, start: str, end: Optional[str]) -> int:
        """Calculate duration in months."""
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end) if end else datetime.now()
            return max(0, int((end_dt - start_dt).days / 30))
        except Exception:
            return 0

    def _update_stats(self, role: CareerRole):
        """Update running statistics."""
        n = self._stats["total_roles"]
        self._stats["avg_satisfaction"] = round((self._stats["avg_satisfaction"] * (n - 1) + role.satisfaction) / n, 2)
        self._stats["avg_learning_velocity"] = round((self._stats["avg_learning_velocity"] * (n - 1) + role.learning_velocity) / n, 2)

        # Calculate career momentum (combination of learning and impact)
        if n >= 2:
            recent = list(self._roles)[-3:]
            momentum = sum(r.learning_velocity + r.impact_score for r in recent) / max(1, len(recent) * 2)
            self._stats["career_momentum"] = round(momentum, 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "goals": {k: {
                    "target_role": v.target_role,
                    "target_date": v.target_date,
                    "required_skills": v.required_skills,
                    "current_skills": v.current_skills,
                    "status": v.status,
                } for k, v in self._goals.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("goals", {}).items():
                    self._goals[k] = CareerGoal(**v)
        except Exception:
            pass

    def _log_role(self, role: CareerRole):
        try:
            with open(ROLE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": role.timestamp,
                    "title": role.title,
                    "company": role.company,
                    "satisfaction": role.satisfaction,
                    "learning": role.learning_velocity,
                    "impact": role.impact_score,
                    "skills": role.skills_gained,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cpm_instance: Optional[CareerPathMapper] = None
_cpm_lock = threading.Lock()


def get_career_path_mapper() -> CareerPathMapper:
    global _cpm_instance
    with _cpm_lock:
        if _cpm_instance is None:
            _cpm_instance = CareerPathMapper()
        return _cpm_instance
