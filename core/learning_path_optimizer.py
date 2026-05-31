"""
LOVE Learning Path Optimizer — Adaptive Learning Sequences (Modern AI Pattern)

Learning is most effective with spaced repetition and optimal difficulty.
This optimizer:

1. SKILL MAPPING
   - Map user skills and knowledge gaps
   - Identify prerequisites for target skills
   - Track mastery level for each skill

2. SPACED REPETITION
   - Schedule review based on forgetting curve
   - Prioritize weak areas for reinforcement
   - Adapt intervals based on performance

3. DIFFICULTY CALIBRATION
   - Match learning material to current skill level
   - Suggest challenging but achievable material
   - Detect and avoid plateaus

4. PROGRESS OPTIMIZATION
   - Suggest optimal learning order
   - Minimize context switching
   - Maximize retention per study session

Architecture:
- add_skill(name, level, prerequisites): Add skill to map
- suggest_next_topic(goal): Suggest optimal next topic
- record_review(skill, performance): Log review performance
- get_learning_stats(): Track progress and effectiveness
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "learning_path_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REVIEW_LOG = DATA_DIR / "review_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Skill:
    """A skill with mastery tracking."""
    name: str = ""
    level: float = 0.0  # 0-1 mastery
    prerequisites: List[str] = field(default_factory=list)
    last_reviewed: Optional[str] = None
    review_count: int = 0
    avg_performance: float = 0.5
    difficulty: float = 0.5  # perceived difficulty
    next_review: Optional[str] = None
    status: str = "learning"  # learning, reviewing, mastered


@dataclass
class ReviewSession:
    """A review/practice session record."""
    skill_name: str = ""
    performance: float = 0.5  # 0-1
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    difficulty_rating: float = 0.5


class LearningPathOptimizer:
    """
    Optimize learning sequences using spaced repetition and difficulty calibration.
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
        self._reviews: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self._stats = {
            "total_skills": 0,
            "mastered_skills": 0,
            "total_reviews": 0,
            "avg_retention": 0.0,
        }
        self._load_stats()

    # ── Core Management ─────────────────────────────────────────────────────

    def add_skill(self, name: str, level: float = 0.0, prerequisites: Optional[List[str]] = None, difficulty: float = 0.5):
        """Add or update a skill."""
        if name not in self._skills:
            self._skills[name] = Skill(
                name=name,
                level=level,
                prerequisites=prerequisites or [],
                difficulty=difficulty,
            )
            with self._lock:
                self._stats["total_skills"] += 1
            self._save_stats()
        else:
            self._skills[name].level = max(self._skills[name].level, level)
            if prerequisites:
                self._skills[name].prerequisites = prerequisites

    def record_review(self, skill_name: str, performance: float, duration: float = 0.0, difficulty_rating: float = 0.5):
        """Record a review/practice session."""
        if skill_name not in self._skills:
            self.add_skill(skill_name)

        session = ReviewSession(
            skill_name=skill_name,
            performance=performance,
            duration_minutes=duration,
            difficulty_rating=difficulty_rating,
        )

        skill = self._skills[skill_name]
        skill.last_reviewed = session.timestamp
        skill.review_count += 1

        # Update average performance
        prev_avg = skill.avg_performance
        n = skill.review_count
        skill.avg_performance = round((prev_avg * (n - 1) + performance) / n, 2)

        # Update level based on performance
        skill.level = min(1.0, skill.level + performance * 0.1)

        # Update status
        if skill.level >= 0.9 and skill.avg_performance >= 0.8:
            skill.status = "mastered"
            self._stats["mastered_skills"] += 1
        elif skill.level >= 0.6:
            skill.status = "reviewing"
        else:
            skill.status = "learning"

        # Calculate next review using spaced repetition
        skill.next_review = self._calculate_next_review(skill)

        self._reviews[skill_name].append(session)

        with self._lock:
            self._stats["total_reviews"] += 1

        self._save_stats()
        self._log_review(session)

    # ── Suggestions ────────────────────────────────────────────────────────

    def suggest_next_topic(self, goal: Optional[str] = None) -> List[Dict[str, Any]]:
        """Suggest optimal next learning topics."""
        candidates = []
        now = datetime.now()

        for skill in self._skills.values():
            # Check prerequisites
            prereqs_met = all(self._skills.get(p, Skill()).level >= 0.5 for p in skill.prerequisites)
            if not prereqs_met:
                continue

            # Calculate priority
            priority = 0.0
            reason = ""

            # Due for review
            if skill.next_review:
                try:
                    next_review = datetime.fromisoformat(skill.next_review)
                    if now >= next_review:
                        priority += 0.5
                        reason = "Review due"
                except Exception:
                    pass

            # Weak skill
            if skill.level < 0.4:
                priority += 0.3
                reason = reason or "Weak skill needs practice"

            # Recently learned, needs reinforcement
            if skill.review_count < 3 and skill.level > 0:
                priority += 0.2
                reason = reason or "New skill needs reinforcement"

            # Goal alignment
            if goal and (goal.lower() in skill.name.lower() or any(goal.lower() in p.lower() for p in skill.prerequisites)):
                priority += 0.4
                reason = reason or f"Aligned with goal: {goal}"

            if priority > 0:
                candidates.append({
                    "skill": skill.name,
                    "priority": round(priority, 2),
                    "current_level": round(skill.level, 2),
                    "reason": reason,
                    "estimated_time": self._estimate_time(skill),
                })

        candidates.sort(key=lambda x: x["priority"], reverse=True)
        return candidates[:5]

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning progress statistics."""
        skills_by_status = defaultdict(list)
        for skill in self._skills.values():
            skills_by_status[skill.status].append(skill.name)

        # Calculate retention estimate
        recent_reviews = []
        for reviews in self._reviews.values():
            recent_reviews.extend(list(reviews)[-3:])

        if recent_reviews:
            avg_recent_perf = sum(r.performance for r in recent_reviews) / len(recent_reviews)
            self._stats["avg_retention"] = round(avg_recent_perf, 2)

        return {
            **self._stats,
            "skills_by_status": {k: len(v) for k, v in skills_by_status.items()},
            "total_skills": len(self._skills),
            "skills": [
                {
                    "name": s.name,
                    "level": round(s.level, 2),
                    "status": s.status,
                    "reviews": s.review_count,
                    "next_review": s.next_review,
                }
                for s in sorted(self._skills.values(), key=lambda x: x.level, reverse=True)[:10]
            ],
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _calculate_next_review(self, skill: Skill) -> str:
        """Calculate next review date using spaced repetition."""
        base_intervals = [1, 3, 7, 14, 30, 60, 120]  # days

        if skill.review_count == 0:
            return (datetime.now() + timedelta(days=1)).isoformat()

        # Use performance to adjust interval
        idx = min(skill.review_count - 1, len(base_intervals) - 1)
        base = base_intervals[idx]

        # Performance multiplier (0.5-1.5)
        multiplier = 0.5 + skill.avg_performance
        days = int(base * multiplier)

        return (datetime.now() + timedelta(days=days)).isoformat()

    def _estimate_time(self, skill: Skill) -> str:
        """Estimate time needed for skill."""
        if skill.level < 0.3:
            return "30-60 min"
        elif skill.level < 0.6:
            return "20-30 min"
        elif skill.level < 0.9:
            return "15-20 min"
        else:
            return "10-15 min"

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "skills": {k: {
                    "name": v.name,
                    "level": v.level,
                    "prerequisites": v.prerequisites,
                    "last_reviewed": v.last_reviewed,
                    "review_count": v.review_count,
                    "avg_performance": v.avg_performance,
                    "difficulty": v.difficulty,
                    "next_review": v.next_review,
                    "status": v.status,
                } for k, v in self._skills.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("skills", {}).items():
                    self._skills[k] = Skill(**v)
        except Exception:
            pass

    def _log_review(self, session: ReviewSession):
        try:
            with open(REVIEW_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "skill": session.skill_name,
                    "performance": session.performance,
                    "duration": session.duration_minutes,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lpo_instance: Optional[LearningPathOptimizer] = None
_lpo_lock = threading.Lock()


def get_learning_path_optimizer() -> LearningPathOptimizer:
    global _lpo_instance
    with _lpo_lock:
        if _lpo_instance is None:
            _lpo_instance = LearningPathOptimizer()
        return _lpo_instance
