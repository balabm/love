"""
LOVE Deep Listener — Presence Intelligence (Modern AI Pattern)

Most people listen to respond. This coach trains you to listen to understand.

1. LISTENING TRACKING
   - Record listening sessions and their characteristics
   - Track listening types (active, empathetic, critical, reflective)
   - Log comprehension and connection outcomes

2. PATTERN ANALYSIS
   - Identify the user's listening profile (distracted, selective, active, deep)
   - Find listening accelerators (what helps them truly hear)
   - Detect listening avoidance patterns

3. LISTENING BUILDING
   - Suggest listening practices matched to current conversation context
   - Provide reflection and paraphrasing exercises
   - Recommendation presence techniques

4. CONNECTION CULTIVATION
   - Track the correlation between listening depth and relationship quality
   - Alert when listening is becoming performative
   - Celebrate moments of genuine understanding

Architecture:
- record_session(speaker, topic, listening_type, comprehension, connection): Log session
- get_listening_stats(): Get listening pattern analysis
- get_listening_practice(context, capacity): Get practice
- get_listening_score(): Calculate overall listening health
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
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "deep_listener"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LISTENING_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ListeningSession:
    """A tracked listening session."""
    session_id: str = ""
    speaker: str = ""  # who was speaking
    topic: str = ""  # what was discussed
    listening_type: str = ""  # active, empathetic, critical, reflective
    comprehension: float = 0.5  # 0-1, how well did you understand
    connection: float = 0.5  # 0-1, how connected did they feel
    presence: float = 0.5  # 0-1, how present were you
    interruptions: int = 0  # how many times you interrupted
    questions_asked: int = 0  # clarifying questions
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DeepListener:
    """
    Intelligent listening coach with presence tracking and comprehension analysis.
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
            "avg_comprehension": 0.0,
            "avg_connection": 0.0,
            "avg_interruptions": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, speaker: str = "", topic: str = "", listening_type: str = "", comprehension: float = 0.5, connection: float = 0.5, presence: float = 0.5, interruptions: int = 0, questions_asked: int = 0, notes: str = "") -> ListeningSession:
        """Record a listening session."""
        session_id = f"listen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = ListeningSession(
            session_id=session_id,
            speaker=speaker or "unspecified",
            topic=topic or "general",
            listening_type=listening_type or "active",
            comprehension=comprehension,
            connection=connection,
            presence=presence,
            interruptions=interruptions,
            questions_asked=questions_asked,
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
        """Get listening pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "comp_sum": 0.0, "conn_sum": 0.0, "pres_sum": 0.0, "int_sum": 0, "q_sum": 0})
        for s in self._sessions:
            by_type[s.listening_type]["count"] += 1
            by_type[s.listening_type]["comp_sum"] += s.comprehension
            by_type[s.listening_type]["conn_sum"] += s.connection
            by_type[s.listening_type]["pres_sum"] += s.presence
            by_type[s.listening_type]["int_sum"] += s.interruptions
            by_type[s.listening_type]["q_sum"] += s.questions_asked

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_comprehension": round(data["comp_sum"] / count, 2),
                "avg_connection": round(data["conn_sum"] / count, 2),
                "avg_presence": round(data["pres_sum"] / count, 2),
                "avg_interruptions": round(data["int_sum"] / count, 1),
                "avg_questions": round(data["q_sum"] / count, 1),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_connection"] + x[1]["avg_comprehension"]) if type_stats else ("", {})

        # Speaker analysis
        by_speaker = defaultdict(lambda: {"count": 0, "comp_sum": 0.0, "conn_sum": 0.0})
        for s in self._sessions:
            by_speaker[s.speaker]["count"] += 1
            by_speaker[s.speaker]["comp_sum"] += s.comprehension
            by_speaker[s.speaker]["conn_sum"] += s.connection

        speaker_stats = {}
        for sp, data in by_speaker.items():
            count = data["count"]
            if count >= 2:
                speaker_stats[sp] = {
                    "count": count,
                    "avg_comprehension": round(data["comp_sum"] / count, 2),
                    "avg_connection": round(data["conn_sum"] / count, 2),
                }

        # Interruption analysis
        high_int = [s for s in self._sessions if s.interruptions > 2]
        low_int = [s for s in self._sessions if s.interruptions == 0]
        if high_int and low_int:
            high_int_conn = sum(s.connection for s in high_int) / len(high_int)
            low_int_conn = sum(s.connection for s in low_int) / len(low_int)
            high_int_comp = sum(s.comprehension for s in high_int) / len(high_int)
            low_int_comp = sum(s.comprehension for s in low_int) / len(low_int)
        else:
            high_int_conn = 0
            low_int_conn = 0
            high_int_comp = 0
            low_int_comp = 0

        # Question analysis
        high_q = [s for s in self._sessions if s.questions_asked > 2]
        low_q = [s for s in self._sessions if s.questions_asked == 0]
        if high_q and low_q:
            high_q_conn = sum(s.connection for s in high_q) / len(high_q)
            low_q_conn = sum(s.connection for s in low_q) / len(low_q)
        else:
            high_q_conn = 0
            low_q_conn = 0

        # Recent trend
        recent = list(self._sessions)[-14:]
        if recent:
            recent_comp = sum(s.comprehension for s in recent) / len(recent)
            recent_conn = sum(s.connection for s in recent) / len(recent)
            recent_pres = sum(s.presence for s in recent) / len(recent)
            recent_int = sum(s.interruptions for s in recent) / len(recent)
            recent_q = sum(s.questions_asked for s in recent) / len(recent)
        else:
            recent_comp = 0
            recent_conn = 0
            recent_pres = 0
            recent_int = 0
            recent_q = 0

        older = list(self._sessions)[:-14] if len(self._sessions) > 14 else []
        if older:
            older_comp = sum(s.comprehension for s in older) / len(older)
            older_conn = sum(s.connection for s in older) / len(older)
            comp_trend = recent_comp - older_comp
            conn_trend = recent_conn - older_conn
        else:
            comp_trend = 0
            conn_trend = 0

        return {
            "total_sessions": len(self._sessions),
            "type_stats": type_stats,
            "best_listening_type": best_type[0],
            "speaker_stats": speaker_stats,
            "interruption_impact": {
                "high_interruption_connection": round(high_int_conn, 2),
                "low_interruption_connection": round(low_int_conn, 2),
                "high_interruption_comprehension": round(high_int_comp, 2),
                "low_interruption_comprehension": round(low_int_comp, 2),
            },
            "question_impact": {
                "high_question_connection": round(high_q_conn, 2),
                "low_question_connection": round(low_q_conn, 2),
            },
            "avg_comprehension": round(sum(s.comprehension for s in self._sessions) / len(self._sessions), 2),
            "avg_connection": round(sum(s.connection for s in self._sessions) / len(self._sessions), 2),
            "avg_presence": round(sum(s.presence for s in self._sessions) / len(self._sessions), 2),
            "avg_interruptions": round(sum(s.interruptions for s in self._sessions) / len(self._sessions), 1),
            "comprehension_trend": round(comp_trend, 2),
            "connection_trend": round(conn_trend, 2),
            "recent_presence": round(recent_pres, 2),
            "recent_interruptions": round(recent_int, 1),
            "recent_questions": round(recent_q, 1),
        }

    def get_listening_practice(self, context: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "difficult": [
                "They're saying something you disagree with. Your job is not to agree. Your job is to understand. Listen as if you'll be tested.",
                "Set down your rebuttal. It will still be there when they're done. Right now, your only task is comprehension.",
                "Repeat back what you heard. Not your interpretation. Their actual words. Let them correct you.",
            ],
            "emotional": [
                "They're emotional. Don't fix. Don't advise. Just witness. 'That sounds really hard.' is often enough.",
                "Silence is not empty. It's where they process. Don't fill it.",
                "Name the emotion you hear. 'You sound frustrated.' Not 'You are frustrated.' Give them the chance to own or correct it.",
            ],
            "technical": [
                "Ask them to explain it like you're five. If you can't explain it simply, you don't understand it.",
                "Take notes. Writing forces attention. Your brain can't wander if your hand is moving.",
                "Ask for an example. Abstract concepts become concrete with one story.",
            ],
            "casual": [
                "Put the phone away. Face them. Eye contact. The simplest practices are the most powerful.",
                "Ask one follow-up question. Not about you. About them. 'What was that like?'",
                "Remember one detail from last time. Ask about it. 'How did that interview go?'",
            ],
            "general": [
                "Listening is not waiting for your turn to speak. It's active construction of their reality in your mind.",
                "The best listeners are the most loved people. Not the most entertaining. The most attentive.",
                "You already know what you think. The point of listening is to learn what they think.",
            ],
        }

        selected = practices.get(context, practices["general"])

        if capacity < 0.3:
            capacity_note = "Low listening capacity. That's okay. Start with one conversation. Just one. Put the phone away. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. You can handle medium-complexity conversations. Choose one relationship to deepen."
        else:
            capacity_note = "Good capacity. This is when you tackle the hard ones. The ones where you deeply disagree. Listen to understand."

        return {
            "context": context or "general",
            "capacity": capacity,
            "practice": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most people listen at 25% capacity. They're planning their response, checking their phone, or waiting for their turn. Deep listening is a superpower. It builds trust, deepens relationships, and surfaces information you would never get otherwise. The best leaders, partners, and friends are the best listeners.",
        }

    def get_listening_score(self) -> int:
        """Calculate overall listening health (0-100)."""
        if not self._sessions:
            return 35

        # Comprehension and connection
        avg_comp = sum(s.comprehension for s in self._sessions) / len(self._sessions)
        avg_conn = sum(s.connection for s in self._sessions) / len(self._sessions)

        # Presence
        avg_pres = sum(s.presence for s in self._sessions) / len(self._sessions)

        # Low interruptions
        avg_int = sum(s.interruptions for s in self._sessions) / len(self._sessions)
        int_penalty = min(15, avg_int * 5)

        # Questions asked
        avg_q = sum(s.questions_asked for s in self._sessions) / len(self._sessions)

        # Type variety
        unique_types = len(set(s.listening_type for s in self._sessions))

        # Recent trend
        recent = list(self._sessions)[-14:]
        if recent:
            recent_comp = sum(s.comprehension for s in recent) / len(recent)
            recent_conn = sum(s.connection for s in recent) / len(recent)
            recent_pres = sum(s.presence for s in recent) / len(recent)
            recent_int = sum(s.interruptions for s in recent) / len(recent)
            recent_q = sum(s.questions_asked for s in recent) / len(recent)
        else:
            recent_comp = 0
            recent_conn = 0
            recent_pres = 0
            recent_int = 0
            recent_q = 0

        score = (avg_comp * 25) + (avg_conn * 25) + (avg_pres * 15) + (avg_q * 10) + (unique_types * 2) + (recent_comp * 10) + (recent_conn * 10) + (recent_pres * 10) + (recent_q * 5) - int_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_comprehension"] = round(sum(s.comprehension for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_connection"] = round(sum(s.connection for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_interruptions"] = round(sum(s.interruptions for s in self._sessions) / len(self._sessions), 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.deep_listener")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.deep_listener")

    def _log_session(self, session: ListeningSession):
        try:
            with open(LISTENING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "speaker": session.speaker,
                    "topic": session.topic,
                    "listening_type": session.listening_type,
                    "comprehension": session.comprehension,
                    "connection": session.connection,
                    "presence": session.presence,
                    "interruptions": session.interruptions,
                    "questions_asked": session.questions_asked,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.deep_listener")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dl_instance: Optional[DeepListener] = None
_dl_lock = threading.Lock()


def get_deep_listener() -> DeepListener:
    global _dl_instance
    with _dl_lock:
        if _dl_instance is None:
            _dl_instance = DeepListener()
        return _dl_instance
