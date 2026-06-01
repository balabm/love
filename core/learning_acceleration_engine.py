"""
LOVE Learning Acceleration Engine — Rapid Acquisition Intelligence (Modern AI Pattern)

Most learning is slow and inefficient. This engine:

1. LEARNING TRACKING
   - Record learning sessions and their characteristics
   - Track learning techniques and their effectiveness
   - Log retention rates and forgetting curves

2. PATTERN ANALYSIS
   - Identify the user's learning style (visual, auditory, kinesthetic, conceptual)
   - Find high-yield learning techniques
   - Detect learning inefficiencies and wasted time

3. ACCELERATION
   - Suggest spaced repetition schedules
   - Provide active recall exercises
   - Recommend interleaving and elaboration practices

4. RETENTION
   - Track knowledge decay and optimal review timing
   - Alert when review is needed
   - Celebrate learning breakthroughs

Architecture:
- record_session(topic, technique, duration, retention): Log session
- get_learning_stats(): Get learning pattern analysis
- get_acceleration_plan(topic, deadline, current_level): Get plan
- get_learning_score(): Calculate overall learning health
"""

import json
import math
import random
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "learning_acceleration_engine"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEARNING_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class LearningSession:
    """A tracked learning session."""
    session_id: str = ""
    topic: str = ""
    technique: str = ""  # active_recall, spaced_repetition, interleaving, elaboration, teaching, practice
    duration_minutes: float = 0.0
    difficulty: float = 0.5  # 0-1
    retention_immediate: float = 0.5  # 0-1
    retention_delayed: float = 0.0  # 0-1, tested later
    engagement: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LearningAccelerationEngine:
    """
    Intelligent learning acceleration engine with spaced repetition optimization and technique matching.
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
        self._sessions: deque = deque(maxlen=300)
        self._stats = {
            "total_sessions": 0,
            "avg_retention": 0.0,
            "avg_engagement": 0.0,
            "best_technique": "",
            "review_needed": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, topic: str = "", technique: str = "", duration: float = 0, difficulty: float = 0.5, retention_immediate: float = 0.5, retention_delayed: float = 0.0, engagement: float = 0.5, notes: str = "") -> LearningSession:
        """Record a learning session."""
        session_id = f"learn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = LearningSession(
            session_id=session_id,
            topic=topic or "unspecified",
            technique=technique or "active_recall",
            duration_minutes=duration,
            difficulty=difficulty,
            retention_immediate=retention_immediate,
            retention_delayed=retention_delayed,
            engagement=engagement,
            notes=notes,
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_session(session)

        return session

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Technique analysis
        by_technique = defaultdict(lambda: {"count": 0, "retention_sum": 0.0, "engagement_sum": 0.0, "duration_sum": 0.0})
        for s in self._sessions:
            by_technique[s.technique]["count"] += 1
            by_technique[s.technique]["retention_sum"] += s.retention_immediate
            by_technique[s.technique]["engagement_sum"] += s.engagement
            by_technique[s.technique]["duration_sum"] += s.duration_minutes

        technique_stats = {}
        for t, data in by_technique.items():
            count = data["count"]
            technique_stats[t] = {
                "count": count,
                "avg_retention": round(data["retention_sum"] / count, 2),
                "avg_engagement": round(data["engagement_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
            }

        best_technique = max(technique_stats.items(), key=lambda x: x[1]["avg_retention"] * x[1]["avg_engagement"]) if technique_stats else ("", {})

        # Topic analysis
        by_topic = defaultdict(lambda: {"count": 0, "retention_sum": 0.0, "engagement_sum": 0.0})
        for s in self._sessions:
            by_topic[s.topic]["count"] += 1
            by_topic[s.topic]["retention_sum"] += s.retention_immediate
            by_topic[s.topic]["engagement_sum"] += s.engagement

        topic_stats = {}
        for top, data in by_topic.items():
            count = data["count"]
            topic_stats[top] = {
                "count": count,
                "avg_retention": round(data["retention_sum"] / count, 2),
                "avg_engagement": round(data["engagement_sum"] / count, 2),
            }

        # Difficulty analysis
        easy = [s for s in self._sessions if s.difficulty <= 0.3]
        medium = [s for s in self._sessions if 0.3 < s.difficulty <= 0.7]
        hard = [s for s in self._sessions if s.difficulty > 0.7]

        difficulty_stats = {}
        if easy:
            difficulty_stats["easy"] = {"count": len(easy), "avg_retention": round(sum(s.retention_immediate for s in easy) / len(easy), 2)}
        if medium:
            difficulty_stats["medium"] = {"count": len(medium), "avg_retention": round(sum(s.retention_immediate for s in medium) / len(medium), 2)}
        if hard:
            difficulty_stats["hard"] = {"count": len(hard), "avg_retention": round(sum(s.retention_immediate for s in hard) / len(hard), 2)}

        # Forgetting curve analysis
        with_delayed = [s for s in self._sessions if s.retention_delayed > 0]
        if with_delayed:
            avg_decay = sum(s.retention_immediate - s.retention_delayed for s in with_delayed) / len(with_delayed)
        else:
            avg_decay = 0

        # Review detection (sessions older than 7 days with no review)
        recent_sessions = [s for s in self._sessions if s.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        old_sessions = [s for s in self._sessions if s.timestamp <= (datetime.now() - timedelta(days=7)).isoformat()]
        review_needed = len(old_sessions) > len(recent_sessions) * 2

        # Recent trend
        recent = list(self._sessions)[-14:]
        if recent:
            recent_retention = sum(s.retention_immediate for s in recent) / len(recent)
            recent_engagement = sum(s.engagement for s in recent) / len(recent)
        else:
            recent_retention = 0
            recent_engagement = 0

        older = list(self._sessions)[:-14] if len(self._sessions) > 14 else []
        if older:
            older_retention = sum(s.retention_immediate for s in older) / len(older)
            older_engagement = sum(s.engagement for s in older) / len(older)
            retention_trend = recent_retention - older_retention
            engagement_trend = recent_engagement - older_engagement
        else:
            retention_trend = 0
            engagement_trend = 0

        return {
            "total_sessions": len(self._sessions),
            "technique_stats": technique_stats,
            "best_technique": best_technique[0],
            "topic_stats": topic_stats,
            "difficulty_stats": difficulty_stats,
            "avg_decay": round(avg_decay, 2),
            "review_needed": review_needed,
            "avg_retention": round(sum(s.retention_immediate for s in self._sessions) / len(self._sessions), 2),
            "avg_engagement": round(sum(s.engagement for s in self._sessions) / len(self._sessions), 2),
            "retention_trend": round(retention_trend, 2),
            "engagement_trend": round(engagement_trend, 2),
            "recent_retention": round(recent_retention, 2),
            "recent_engagement": round(recent_engagement, 2),
        }

    def get_acceleration_plan(self, topic: str = "", deadline: str = "", current_level: float = 0.3, target_level: float = 0.8) -> Dict[str, Any]:
        """Get plan."""
        gap = target_level - current_level
        
        if gap > 0.5:
            urgency = "High gap. Intensive learning needed. Prioritize active recall and spaced repetition."
            sessions_per_week = 5
        elif gap > 0.3:
            urgency = "Moderate gap. Steady learning. Mix techniques for depth."
            sessions_per_week = 3
        else:
            urgency = "Small gap. Maintenance mode. Focus on consolidation and application."
            sessions_per_week = 2

        techniques = [
            "Active recall: Close the book. Test yourself. What do you remember?",
            "Spaced repetition: Review at increasing intervals. 1 day, 3 days, 7 days, 14 days.",
            "Interleaving: Mix different topics in one session. Don't block practice.",
            "Elaboration: Explain the concept in your own words. Connect it to what you know.",
            "Teaching: Teach someone else. If you can't explain it simply, you don't understand it.",
            "Practice: Apply the knowledge immediately. Build something. Solve a problem.",
        ]

        plan = {
            "topic": topic or "general",
            "deadline": deadline or "none",
            "current_level": current_level,
            "target_level": target_level,
            "gap": round(gap, 2),
            "urgency": urgency,
            "sessions_per_week": sessions_per_week,
            "recommended_techniques": random.sample(techniques, min(3, len(techniques))),
            "review_schedule": [
                "Review after 1 day",
                "Review after 3 days",
                "Review after 7 days",
                "Review after 14 days",
                "Review after 30 days",
            ],
            "principle": "Learning is not reading. It's retrieving. Every time you pull knowledge from your memory, you strengthen it. Test yourself more than you read.",
        }

        return plan

    def get_learning_score(self) -> int:
        """Calculate overall learning health (0-100)."""
        if not self._sessions:
            return 30

        # Retention
        avg_retention = sum(s.retention_immediate for s in self._sessions) / len(self._sessions)

        # Engagement
        avg_engagement = sum(s.engagement for s in self._sessions) / len(self._sessions)

        # Low decay
        with_delayed = [s for s in self._sessions if s.retention_delayed > 0]
        if with_delayed:
            avg_decay = sum(s.retention_immediate - s.retention_delayed for s in with_delayed) / len(with_delayed)
            decay_score = max(0, 1 - avg_decay)
        else:
            decay_score = 0.5

        # Technique variety
        unique_techniques = len(set(s.technique for s in self._sessions))

        # Topic variety
        unique_topics = len(set(s.topic for s in self._sessions))

        # Recent trend
        recent = list(self._sessions)[-14:]
        if recent:
            recent_retention = sum(s.retention_immediate for s in recent) / len(recent)
            recent_engagement = sum(s.engagement for s in recent) / len(recent)
        else:
            recent_retention = 0
            recent_engagement = 0

        # Review compliance
        old_sessions = [s for s in self._sessions if s.timestamp <= (datetime.now() - timedelta(days=7)).isoformat()]
        recent_sessions = [s for s in self._sessions if s.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        review_compliance = min(1, len(recent_sessions) / max(1, len(old_sessions)))

        score = (avg_retention * 25) + (avg_engagement * 20) + (decay_score * 15) + (unique_techniques * 2) + (unique_topics * 2) + (recent_retention * 15) + (recent_engagement * 10) + (review_compliance * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_retention"] = round(sum(s.retention_immediate for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_engagement"] = round(sum(s.engagement for s in self._sessions) / len(self._sessions), 2)

            by_technique = defaultdict(lambda: {"retention": 0.0, "engagement": 0.0, "count": 0})
            for s in self._sessions:
                by_technique[s.technique]["retention"] += s.retention_immediate
                by_technique[s.technique]["engagement"] += s.engagement
                by_technique[s.technique]["count"] += 1
            if by_technique:
                best = max(by_technique.items(), key=lambda x: (x[1]["retention"] + x[1]["engagement"]) / max(1, x[1]["count"]))
                self._stats["best_technique"] = best[0]

            old_sessions = [s for s in self._sessions if s.timestamp <= (datetime.now() - timedelta(days=7)).isoformat()]
            recent_sessions = [s for s in self._sessions if s.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
            self._stats["review_needed"] = len(old_sessions) > len(recent_sessions) * 2

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception:
            pass

    def _log_session(self, session: LearningSession):
        try:
            with open(LEARNING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "topic": session.topic,
                    "technique": session.technique,
                    "duration": session.duration_minutes,
                    "difficulty": session.difficulty,
                    "retention": session.retention_immediate,
                    "engagement": session.engagement,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lae_instance: Optional[LearningAccelerationEngine] = None
_lae_lock = threading.Lock()


    
def get_learning_acceleration_engine() -> LearningAccelerationEngine:
    global _lae_instance
    with _lae_lock:
        if _lae_instance is None:
            _lae_instance = LearningAccelerationEngine()
        return _lae_instance
