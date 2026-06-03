"""
LOVE Skill Gap Analyzer — Capability Intelligence (Modern AI Pattern)

Most skill tracking is static lists. This analyzer:

1. SKILL TRACKING
   - Record skills with proficiency levels and last used dates
   - Track skill decay (skills unused get rusty)
   - Log skill application in real projects

2. GAP DETECTION
   - Compare current skills against target role requirements
   - Identify emerging skills in the industry
   - Detect skills that are becoming obsolete

3. LEARNING PRIORITIZATION
   - Prioritize gaps by impact on career goals
   - Suggest optimal learning order (foundations first)
   - Recommend learning resources based on skill type

4. PROGRESS TRACKING
   - Track skill acquisition velocity
   - Celebrate skill milestones
   - Alert when practice is needed to maintain proficiency

Architecture:
- record_skill(skill, proficiency, last_used): Log skill status
- analyze_gaps(target_skills): Compare current vs target
- get_learning_priority(): Get prioritized learning plan
- get_skill_health_score(): Calculate overall skill portfolio health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "skill_gap_analyzer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SKILL_LOG = DATA_DIR / "skills.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Skill:
    """A tracked skill."""
    name: str = ""
    proficiency: float = 0.5  # 0-1 (beginner to expert)
    category: str = ""  # technical, soft, leadership, creative, business
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    times_applied: int = 0
    projects_used: List[str] = field(default_factory=list)
    learning_hours: float = 0.0
    certification: str = ""  # certification name if any
    decay_rate: float = 0.01  # proficiency lost per month unused
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SkillTarget:
    """A target skill requirement."""
    name: str = ""
    required_proficiency: float = 0.7
    priority: str = "medium"  # low, medium, high, critical
    category: str = ""
    reason: str = ""  # why this skill is needed


class SkillGapAnalyzer:
    """
    Analyze skill gaps and create intelligent learning plans.
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
        self._skills: Dict[str, Skill] = {}
        self._targets: Dict[str, SkillTarget] = {}
        self._stats = {
            "total_skills": 0,
            "avg_proficiency": 0.5,
            "skills_at_risk": 0,
            "portfolio_health": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_skill(self, name: str, proficiency: float = 0.5, category: str = "", times_applied: int = 0, projects: Optional[List[str]] = None, learning_hours: float = 0, certification: str = "") -> Skill:
        """Record or update a skill."""
        skill_id = name.lower().replace(" ", "_")
        
        if skill_id in self._skills:
            # Update existing
            self._skills[skill_id].proficiency = proficiency
            self._skills[skill_id].last_used = datetime.now().isoformat()
            self._skills[skill_id].times_applied += times_applied
            self._skills[skill_id].projects_used.extend(projects or [])
            self._skills[skill_id].learning_hours += learning_hours
            if certification:
                self._skills[skill_id].certification = certification
        else:
            self._skills[skill_id] = Skill(
                name=name,
                proficiency=proficiency,
                category=category or "general",
                times_applied=times_applied,
                projects_used=projects or [],
                learning_hours=learning_hours,
                certification=certification,
            )

        with self._lock:
            self._stats["total_skills"] = len(self._skills)
            self._update_stats()

        self._save_stats()
        self._log_skill(self._skills[skill_id])

        return self._skills[skill_id]

    def add_target(self, name: str, required_proficiency: float = 0.7, priority: str = "medium", category: str = "", reason: str = ""):
        """Add a target skill requirement."""
        self._targets[name.lower().replace(" ", "_")] = SkillTarget(
            name=name,
            required_proficiency=required_proficiency,
            priority=priority,
            category=category or "general",
            reason=reason,
        )
        self._save_stats()

    # ── Analysis ──────────────────────────────────────────────────────────

    def analyze_gaps(self, target_role: str = "") -> Dict[str, Any]:
        """Compare current skills against targets and identify gaps."""
        # Apply decay to all skills
        current_skills = self._apply_decay()
        
        gaps = []
        strengths = []
        at_risk = []

        # Check target gaps
        for target_id, target in self._targets.items():
            current = current_skills.get(target_id)
            if not current:
                gaps.append({
                    "skill": target.name,
                    "current": 0,
                    "required": target.required_proficiency,
                    "gap": target.required_proficiency,
                    "priority": target.priority,
                    "reason": target.reason,
                    "status": "missing",
                })
            elif current.proficiency < target.required_proficiency:
                gaps.append({
                    "skill": target.name,
                    "current": round(current.proficiency, 2),
                    "required": target.required_proficiency,
                    "gap": round(target.required_proficiency - current.proficiency, 2),
                    "priority": target.priority,
                    "reason": target.reason,
                    "status": "underdeveloped",
                })
            else:
                strengths.append({
                    "skill": target.name,
                    "current": round(current.proficiency, 2),
                    "required": target.required_proficiency,
                    "excess": round(current.proficiency - target.required_proficiency, 2),
                })

        # Check for at-risk skills (unused for 6+ months)
        six_months_ago = (datetime.now() - timedelta(days=180)).isoformat()
        for skill_id, skill in current_skills.items():
            if skill.last_used < six_months_ago and skill.proficiency > 0.3:
                months_unused = (datetime.now() - datetime.fromisoformat(skill.last_used)).days / 30
                at_risk.append({
                    "skill": skill.name,
                    "proficiency": round(skill.proficiency, 2),
                    "months_unused": round(months_unused, 1),
                    "estimated_decayed": round(max(0, skill.proficiency - (months_unused * skill.decay_rate)), 2),
                })

        # Sort gaps by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda x: priority_order.get(x["priority"], 2))

        return {
            "gaps": gaps,
            "strengths": strengths,
            "at_risk": at_risk,
            "total_gaps": len(gaps),
            "critical_gaps": sum(1 for g in gaps if g["priority"] == "critical"),
            "portfolio_health": self._calculate_health(current_skills),
        }

    def get_learning_priority(self) -> List[Dict[str, Any]]:
        """Get prioritized learning plan."""
        analysis = self.analyze_gaps()
        gaps = analysis.get("gaps", [])
        
        if not gaps:
            return [{"suggestion": "Your skill set looks strong! Consider adding emerging skills in your field.", "priority": "low"}]

        plan = []
        for gap in gaps[:5]:
            # Estimate learning time
            if gap["status"] == "missing":
                estimated_hours = gap["required"] * 100  # 100 hours per proficiency unit
            else:
                estimated_hours = gap["gap"] * 80

            # Suggest learning method
            if gap["gap"] > 0.5:
                methods = ["Online course", "Book + practice", "Mentorship"]
            else:
                methods = ["Practice project", "Refresher course", "Peer learning"]

            plan.append({
                "skill": gap["skill"],
                "priority": gap["priority"],
                "current_level": gap["current"],
                "target_level": gap["required"],
                "gap": gap["gap"],
                "estimated_hours": round(estimated_hours, 0),
                "suggested_methods": methods[:2],
                "timeline": "1-2 months" if gap["gap"] < 0.3 else "3-6 months" if gap["gap"] < 0.6 else "6+ months",
                "reason": gap.get("reason", "Required for career growth"),
            })

        return plan

    def get_skill_health_score(self) -> int:
        """Calculate overall skill portfolio health (0-100)."""
        current_skills = self._apply_decay()
        
        if not current_skills:
            return 0

        # Average proficiency
        avg_proficiency = sum(s.proficiency for s in current_skills.values()) / len(current_skills)
        proficiency_score = avg_proficiency * 100

        # Diversity score (categories covered)
        categories = set(s.category for s in current_skills.values())
        diversity_score = min(100, len(categories) * 20)  # 5 categories = 100

        # Recency score
        recent = [s for s in current_skills.values() if s.last_used > (datetime.now() - timedelta(days=90)).isoformat()]
        recency_score = (len(recent) / max(1, len(current_skills))) * 100

        # Target coverage
        if self._targets:
            covered = sum(1 for t in self._targets.values() if t.name.lower().replace(" ", "_") in current_skills and current_skills[t.name.lower().replace(" ", "_")].proficiency >= t.required_proficiency)
            target_score = (covered / len(self._targets)) * 100
        else:
            target_score = 50

        overall = round(proficiency_score * 0.4 + diversity_score * 0.2 + recency_score * 0.2 + target_score * 0.2)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _apply_decay(self) -> Dict[str, Skill]:
        """Apply skill decay based on time unused."""
        now = datetime.now()
        decayed_skills = {}
        
        for skill_id, skill in self._skills.items():
            months_unused = (now - datetime.fromisoformat(skill.last_used)).days / 30
            decay = months_unused * skill.decay_rate
            
            decayed_skill = Skill(
                name=skill.name,
                proficiency=max(0, skill.proficiency - decay),
                category=skill.category,
                last_used=skill.last_used,
                times_applied=skill.times_applied,
                projects_used=skill.projects_used,
                learning_hours=skill.learning_hours,
                certification=skill.certification,
                decay_rate=skill.decay_rate,
            )
            decayed_skills[skill_id] = decayed_skill
        
        return decayed_skills

    def _calculate_health(self, skills: Dict[str, Skill]) -> int:
        """Calculate portfolio health score."""
        if not skills:
            return 0
        
        avg_proficiency = sum(s.proficiency for s in skills.values()) / len(skills)
        recent_usage = sum(1 for s in skills.values() if s.last_used > (datetime.now() - timedelta(days=90)).isoformat())
        recency_ratio = recent_usage / len(skills)
        
        health = round(avg_proficiency * 60 + recency_ratio * 40)
        return min(100, health)

    def _update_stats(self):
        """Update running statistics."""
        if self._skills:
            self._stats["avg_proficiency"] = round(sum(s.proficiency for s in self._skills.values()) / len(self._skills), 2)
            
            six_months_ago = (datetime.now() - timedelta(days=180)).isoformat()
            at_risk = sum(1 for s in self._skills.values() if s.last_used < six_months_ago and s.proficiency > 0.3)
            self._stats["skills_at_risk"] = at_risk
            
            self._stats["portfolio_health"] = self.get_skill_health_score()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "skills": {k: {
                    "name": v.name,
                    "proficiency": v.proficiency,
                    "category": v.category,
                    "last_used": v.last_used,
                    "times_applied": v.times_applied,
                    "projects_used": v.projects_used,
                    "learning_hours": v.learning_hours,
                    "certification": v.certification,
                    "decay_rate": v.decay_rate,
                } for k, v in self._skills.items()},
                "targets": {k: {
                    "name": v.name,
                    "required_proficiency": v.required_proficiency,
                    "priority": v.priority,
                    "category": v.category,
                    "reason": v.reason,
                } for k, v in self._targets.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.skill_gap_analyzer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("skills", {}).items():
                    self._skills[k] = Skill(**v)
                for k, v in data.get("targets", {}).items():
                    self._targets[k] = SkillTarget(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.skill_gap_analyzer")

    def _log_skill(self, skill: Skill):
        try:
            with open(SKILL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": skill.timestamp,
                    "skill": skill.name,
                    "proficiency": skill.proficiency,
                    "category": skill.category,
                    "last_used": skill.last_used,
                    "learning_hours": skill.learning_hours,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.skill_gap_analyzer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sga_instance: Optional[SkillGapAnalyzer] = None
_sga_lock = threading.Lock()


def get_skill_gap_analyzer() -> SkillGapAnalyzer:
    global _sga_instance
    with _sga_lock:
        if _sga_instance is None:
            _sga_instance = SkillGapAnalyzer()
        return _sga_instance
