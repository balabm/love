"""
LOVE Active Listening Coach — Connection Intelligence (Modern AI Pattern)

Most listening is waiting for your turn to speak. This coach:

1. LISTENING TRACKING
   - Record listening sessions with attention quality scores
   - Track interruptions, advice-giving, and mind-wandering
   - Log emotional attunement and validation attempts

2. PATTERN ANALYSIS
   - Identify when the user listens well vs performs poorly
   - Find which relationships get the best listening quality
   - Detect listening fatigue and emotional depletion

3. SKILL BUILDING
   - Generate reflection prompts and validation scripts
   - Suggest follow-up questions for deeper connection
   - Provide graded listening exercises

4. PROACTIVE GUIDANCE
   - Alert when listening quality drops in important relationships
   - Suggest repair conversations after poor listening
   - Track relationship depth improvements from better listening

Architecture:
- record_session(person, duration, attention, interruptions): Log session
- get_listening_stats(): Get listening quality analysis
- get_reflection_script(emotion): Get empathetic response
- get_listening_score(): Calculate overall listening ability
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

DATA_DIR = Path(__file__).parent.parent / "data" / "active_listening_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ListeningSession:
    """A tracked listening session."""
    session_id: str = ""
    person: str = ""  # who was talking
    relationship_type: str = ""  # romantic, family, friend, colleague, stranger
    duration_minutes: float = 0.0
    attention_score: float = 0.5  # 0-1, how present the user was
    interruptions: int = 0
    advice_given: int = 0
    questions_asked: int = 0
    reflections_made: int = 0  # paraphrasing, validating
    emotional_attunement: float = 0.5  # 0-1, how well emotions were picked up
    mind_wandering: bool = False
    user_fatigue: float = 0.3  # 0-1
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ActiveListeningCoach:
    """
    Intelligent listening coach with quality analysis and skill building.
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
        self._sessions: deque = deque(maxlen=200)
        self._stats = {
            "total_sessions": 0,
            "avg_attention": 0.0,
            "avg_interruptions": 0.0,
            "reflection_rate": 0.0,
            "best_listener_for": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, person: str = "", relationship: str = "", duration: float = 0, attention: float = 0.5, interruptions: int = 0, advice: int = 0, questions: int = 0, reflections: int = 0, attunement: float = 0.5, wandered: bool = False, fatigue: float = 0.3, notes: str = "") -> ListeningSession:
        """Record a listening session."""
        session_id = f"listen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = ListeningSession(
            session_id=session_id,
            person=person or "unspecified",
            relationship_type=relationship or "general",
            duration_minutes=duration,
            attention_score=attention,
            interruptions=interruptions,
            advice_given=advice,
            questions_asked=questions,
            reflections_made=reflections,
            emotional_attunement=attunement,
            mind_wandering=wandered,
            user_fatigue=fatigue,
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

    def get_listening_stats(self) -> Dict[str, Any]:
        """Get listening quality analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Person analysis
        by_person = defaultdict(lambda: {"count": 0, "attention_sum": 0.0, "interruptions": 0, "reflections": 0, "attunement_sum": 0.0})
        for s in self._sessions:
            by_person[s.person]["count"] += 1
            by_person[s.person]["attention_sum"] += s.attention_score
            by_person[s.person]["interruptions"] += s.interruptions
            by_person[s.person]["reflections"] += s.reflections_made
            by_person[s.person]["attunement_sum"] += s.emotional_attunement

        person_stats = {}
        for p, data in by_person.items():
            count = data["count"]
            person_stats[p] = {
                "count": count,
                "avg_attention": round(data["attention_sum"] / count, 2),
                "total_interruptions": data["interruptions"],
                "avg_reflections": round(data["reflections"] / count, 2),
                "avg_attunement": round(data["attunement_sum"] / count, 2),
                "quality": "excellent" if data["attention_sum"] / count > 0.8 and data["interruptions"] / count < 1 else "good" if data["attention_sum"] / count > 0.6 else "needs_work",
            }

        # Best listener target
        best = max(person_stats.items(), key=lambda x: x[1]["avg_attention"]) if person_stats else ("", {})

        # Relationship type analysis
        by_type = defaultdict(lambda: {"count": 0, "attention_sum": 0.0, "interruptions": 0})
        for s in self._sessions:
            by_type[s.relationship_type]["count"] += 1
            by_type[s.relationship_type]["attention_sum"] += s.attention_score
            by_type[s.relationship_type]["interruptions"] += s.interruptions

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_attention": round(data["attention_sum"] / count, 2),
                "avg_interruptions": round(data["interruptions"] / count, 1),
            }

        # Trend
        recent = [s for s in self._sessions if s.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_attention = sum(s.attention_score for s in recent) / len(recent)
            older = [s for s in self._sessions if s.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if older:
                older_attention = sum(s.attention_score for s in older) / len(older)
                trend = "improving" if recent_attention > older_attention + 0.05 else "declining" if recent_attention < older_attention - 0.05 else "stable"
            else:
                trend = "new"
        else:
            trend = "stable"

        return {
            "total_sessions": len(self._sessions),
            "person_stats": person_stats,
            "best_listener_for": best[0],
            "relationship_type_stats": type_stats,
            "avg_attention": round(sum(s.attention_score for s in self._sessions) / len(self._sessions), 2),
            "avg_interruptions": round(sum(s.interruptions for s in self._sessions) / len(self._sessions), 1),
            "reflection_rate": round(sum(s.reflections_made for s in self._sessions) / len(self._sessions), 2),
            "mind_wandering_rate": round(sum(1 for s in self._sessions if s.mind_wandering) / len(self._sessions), 2),
            "trend": trend,
        }

    def get_reflection_script(self, emotion: str = "", context: str = "") -> Dict[str, Any]:
        """Get empathetic response script."""
        scripts = {
            "sad": {
                "validation": "It sounds like you're going through something really hard right now.",
                "reflection": "You're feeling overwhelmed by everything that's piling up.",
                "question": "What would help you most right now—space, support, or a distraction?",
            },
            "angry": {
                "validation": "That sounds incredibly frustrating. I'd be angry too.",
                "reflection": "You feel disrespected and like your boundaries were ignored.",
                "question": "What do you need to feel heard on this?",
            },
            "anxious": {
                "validation": "I can hear how much this is weighing on you.",
                "reflection": "You're worried things might not work out the way you need them to.",
                "question": "What's the worst-case scenario you're imagining? Let's look at it together.",
            },
            "happy": {
                "validation": "That's wonderful! I can hear how much this means to you.",
                "reflection": "You're feeling seen and valued for what you've accomplished.",
                "question": "How can we celebrate this properly?",
            },
            "hurt": {
                "validation": "That really hurt. Your feelings make complete sense.",
                "reflection": "You expected better from them, and they let you down.",
                "question": "What would repair look like for you?",
            },
            "confused": {
                "validation": "This is really complex. It's okay to not have it figured out yet.",
                "reflection": "You're trying to make sense of something that doesn't add up.",
                "question": "What part feels most confusing right now?",
            },
        }

        base = scripts.get(emotion, scripts["sad"])

        return {
            "emotion": emotion,
            "validation": base["validation"],
            "reflection": base["reflection"],
            "follow_up_question": base["question"],
            "body_language": "Lean in slightly, nod, maintain soft eye contact",
            "what_to_avoid": "Don't fix, don't minimize, don't compare to your own experience",
            "context": context,
        }

    def get_listening_score(self) -> int:
        """Calculate overall listening ability (0-100)."""
        if not self._sessions:
            return 50

        # Attention
        avg_attention = sum(s.attention_score for s in self._sessions) / len(self._sessions)

        # Interruptions (lower is better)
        avg_interruptions = sum(s.interruptions for s in self._sessions) / len(self._sessions)
        interruption_penalty = min(30, avg_interruptions * 5)

        # Reflections (higher is better)
        avg_reflections = sum(s.reflections_made for s in self._sessions) / len(self._sessions)
        reflection_bonus = min(20, avg_reflections * 5)

        # Attunement
        avg_attunement = sum(s.emotional_attunement for s in self._sessions) / len(self._sessions)

        # Mind wandering (lower is better)
        wander_rate = sum(1 for s in self._sessions if s.mind_wandering) / len(self._sessions)
        wander_penalty = wander_rate * 20

        score = (avg_attention * 40) + reflection_bonus + (avg_attunement * 20) - interruption_penalty - wander_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_attention"] = round(sum(s.attention_score for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_interruptions"] = round(sum(s.interruptions for s in self._sessions) / len(self._sessions), 1)
            reflections = sum(s.reflections_made for s in self._sessions)
            self._stats["reflection_rate"] = round(reflections / len(self._sessions), 2)

            by_person = defaultdict(lambda: {"attention": 0.0, "count": 0})
            for s in self._sessions:
                by_person[s.person]["attention"] += s.attention_score
                by_person[s.person]["count"] += 1
            
            if by_person:
                best = max(by_person.items(), key=lambda x: x[1]["attention"] / max(1, x[1]["count"]))
                self._stats["best_listener_for"] = best[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.active_listening_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.active_listening_coach")

    def _log_session(self, session: ListeningSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "person": session.person,
                    "relationship": session.relationship_type,
                    "duration": session.duration_minutes,
                    "attention": session.attention_score,
                    "interruptions": session.interruptions,
                    "reflections": session.reflections_made,
                    "attunement": session.emotional_attunement,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.active_listening_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_alc_instance: Optional[ActiveListeningCoach] = None
_alc_lock = threading.Lock()


def get_active_listening_coach() -> ActiveListeningCoach:
    global _alc_instance
    with _alc_lock:
        if _alc_instance is None:
            _alc_instance = ActiveListeningCoach()
        return _alc_instance
