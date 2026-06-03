"""
LOVE Conversation Quality Analyzer — Real-time Interaction Assessment

Modern AI systems need to understand not just WHAT users say, but HOW
the interaction is going. This analyzer provides:

1. REAL-TIME QUALITY SCORING
   - Engagement: Is the user actively participating?
   - Clarity: Are LOVE's responses clear and helpful?
   - Relevance: Is LOVE staying on topic?
   - Emotional tone: Is the conversation warm and supportive?

2. PROACTIVE ADJUSTMENT SUGGESTIONS
   - "User seems confused — try simpler explanation"
   - "User is frustrated — acknowledge their feeling first"
   - "Conversation is drifting — refocus on the main topic"
   - "User is delighted — this approach works, remember it"

3. PATTERN DETECTION
   - Identify conversation styles that work best for this user
   - Detect recurring friction points
   - Track quality trends over time

4. QUALITY METRICS DASHBOARD
   - Average conversation quality score
   - Quality trend (improving/declining)
   - Best and worst performing conversation patterns
   - Suggested improvements based on data

Architecture:
- analyze_turn(): Score a single conversation turn
- analyze_conversation(): Score a full conversation
- get_suggestions(): Proactive adjustment recommendations
- get_quality_trends(): Historical quality metrics
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
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "conversation_quality"
DATA_DIR.mkdir(parents=True, exist_ok=True)

QUALITY_DB = DATA_DIR / "quality_db.json"
TRENDS_LOG = DATA_DIR / "trends.jsonl"


@dataclass
class TurnAnalysis:
    """Analysis of a single conversation turn."""
    turn_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_message_length: int = 0
    love_response_length: int = 0
    engagement_score: float = 0.0  # 0-1
    clarity_score: float = 0.0
    relevance_score: float = 0.0
    emotional_tone: str = "neutral"  # positive, negative, neutral, confused, frustrated
    response_time_ms: float = 0.0
    overall_score: float = 0.0


@dataclass
class ConversationSummary:
    """Summary of a full conversation."""
    conversation_id: str = ""
    start_time: str = ""
    end_time: str = ""
    turn_count: int = 0
    avg_quality: float = 0.0
    best_turn: Optional[str] = None
    worst_turn: Optional[str] = None
    dominant_emotion: str = "neutral"
    suggestions: List[str] = field(default_factory=list)


class ConversationQualityAnalyzer:
    """
    Real-time conversation quality analysis for LOVE.
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
        self._lock = threading.Lock()
        self._turns: deque = deque(maxlen=1000)
        self._conversations: Dict[str, ConversationSummary] = {}
        self._stats = {"turns_analyzed": 0, "conversations_analyzed": 0}
        self._load_db()

    # ── Core Analysis ──────────────────────────────────────────────────────

    def analyze_turn(self, user_message: str, love_response: str,
                     response_time_ms: float = 0.0) -> TurnAnalysis:
        """Analyze a single conversation turn."""
        turn_id = f"turn_{int(time.time())}_{threading.current_thread().ident}"

        # Engagement: longer user messages = more engaged
        engagement = min(1.0, len(user_message) / 200)
        if len(user_message) < 10:
            engagement = max(0.1, engagement)  # Very short might be dismissive

        # Clarity: response should be structured and specific
        clarity = self._score_clarity(love_response)

        # Relevance: response should reference user's message
        relevance = self._score_relevance(user_message, love_response)

        # Emotional tone
        tone = self._detect_emotion(user_message)

        # Overall: weighted average
        overall = (engagement * 0.3 + clarity * 0.3 + relevance * 0.3 +
                   (1.0 if tone in ("positive", "neutral") else 0.5) * 0.1)

        analysis = TurnAnalysis(
            turn_id=turn_id,
            user_message_length=len(user_message),
            love_response_length=len(love_response),
            engagement_score=round(engagement, 3),
            clarity_score=round(clarity, 3),
            relevance_score=round(relevance, 3),
            emotional_tone=tone,
            response_time_ms=response_time_ms,
            overall_score=round(overall, 3),
        )

        with self._lock:
            self._turns.append(analysis)
        self._stats["turns_analyzed"] += 1

        return analysis

    def analyze_conversation(self, conversation_id: str = "") -> ConversationSummary:
        """Analyze a complete conversation."""
        if not conversation_id:
            conversation_id = f"conv_{int(time.time())}"

        recent_turns = list(self._turns)[-50:]
        if not recent_turns:
            return ConversationSummary(conversation_id=conversation_id)

        avg_quality = sum(t.overall_score for t in recent_turns) / len(recent_turns)
        best = max(recent_turns, key=lambda t: t.overall_score)
        worst = min(recent_turns, key=lambda t: t.overall_score)

        # Dominant emotion
        emotions = defaultdict(int)
        for t in recent_turns:
            emotions[t.emotional_tone] += 1
        dominant = max(emotions, key=emotions.get) if emotions else "neutral"

        # Generate suggestions
        suggestions = self._generate_suggestions(recent_turns)

        summary = ConversationSummary(
            conversation_id=conversation_id,
            start_time=recent_turns[0].timestamp,
            end_time=recent_turns[-1].timestamp,
            turn_count=len(recent_turns),
            avg_quality=round(avg_quality, 3),
            best_turn=best.turn_id,
            worst_turn=worst.turn_id,
            dominant_emotion=dominant,
            suggestions=suggestions,
        )

        with self._lock:
            self._conversations[conversation_id] = summary
        self._stats["conversations_analyzed"] += 1
        self._save_db()
        self._log_trend(summary)

        return summary

    # ── Scoring Methods ────────────────────────────────────────────────────

    def _score_clarity(self, response: str) -> float:
        """Score response clarity."""
        score = 0.5

        # Presence of structure markers
        if any(m in response for m in ["1.", "2.", "3.", "First", "Second", "Finally"]):
            score += 0.2

        # Presence of examples
        if "for example" in response.lower() or "like" in response.lower():
            score += 0.1

        # Presence of summaries
        if "summary" in response.lower() or "in short" in response.lower():
            score += 0.1

        # Conciseness bonus (not too short, not too long)
        word_count = len(response.split())
        if 20 <= word_count <= 200:
            score += 0.1

        return min(1.0, score)

    def _score_relevance(self, user_msg: str, response: str) -> float:
        """Score response relevance to user message."""
        user_words = set(user_msg.lower().split())
        response_words = set(response.lower().split())

        if not user_words:
            return 0.5

        overlap = len(user_words & response_words)
        relevance = overlap / max(len(user_words), 1)

        # Boost if response directly addresses a question
        if any(w in user_msg.lower() for w in ["?", "what", "how", "why", "when", "where"]):
            if any(w in response.lower() for w in ["because", "since", "as", "is", "are"]):
                relevance = min(1.0, relevance + 0.2)

        return min(1.0, max(0.1, relevance))

    def _detect_emotion(self, message: str) -> str:
        """Detect emotional tone from message."""
        msg = message.lower()

        positive = ["great", "awesome", "thanks", "love", "perfect", "excellent", "happy", "good"]
        negative = ["bad", "terrible", "hate", "awful", "worst", "disappointed", "angry", "upset"]
        confused = ["confused", "don't understand", "what do you mean", "not sure", "?"]
        frustrated = ["frustrated", "annoying", "useless", "stupid", "again", "already told you"]

        if any(w in msg for w in frustrated):
            return "frustrated"
        if any(w in msg for w in confused):
            return "confused"
        if any(w in msg for w in negative):
            return "negative"
        if any(w in msg for w in positive):
            return "positive"

        return "neutral"

    # ── Suggestion Generation ──────────────────────────────────────────────

    def _generate_suggestions(self, turns: List[TurnAnalysis]) -> List[str]:
        """Generate improvement suggestions based on turn analysis."""
        suggestions = []

        avg_clarity = sum(t.clarity_score for t in turns) / max(len(turns), 1)
        avg_relevance = sum(t.relevance_score for t in turns) / max(len(turns), 1)
        avg_engagement = sum(t.engagement_score for t in turns) / max(len(turns), 1)

        # Check for low clarity
        if avg_clarity < 0.6:
            suggestions.append("Responses could be more structured. Try using numbered lists or bullet points.")

        # Check for low relevance
        if avg_relevance < 0.5:
            suggestions.append("Responses sometimes drift from the user's topic. Try referencing their specific words more.")

        # Check for low engagement
        if avg_engagement < 0.4:
            suggestions.append("User engagement is low. Try asking follow-up questions or offering choices.")

        # Check for frustration
        frustrated_turns = [t for t in turns if t.emotional_tone == "frustrated"]
        if len(frustrated_turns) > 2:
            suggestions.append(f"User showed frustration {len(frustrated_turns)} times. Consider acknowledging their frustration directly.")

        # Check for confusion
        confused_turns = [t for t in turns if t.emotional_tone == "confused"]
        if len(confused_turns) > 2:
            suggestions.append(f"User seemed confused {len(confused_turns)} times. Try simpler explanations or ask clarifying questions.")

        return suggestions[:5]

    # ── Trend Analysis ─────────────────────────────────────────────────────

    def get_quality_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get quality trends over the last N days."""
        cutoff = time.time() - (days * 86400)
        recent_turns = [t for t in self._turns if datetime.fromisoformat(t.timestamp).timestamp() > cutoff]

        if not recent_turns:
            return {"message": "No recent conversation data"}

        daily_scores = defaultdict(list)
        for t in recent_turns:
            day = datetime.fromisoformat(t.timestamp).strftime("%Y-%m-%d")
            daily_scores[day].append(t.overall_score)

        trend = []
        for day in sorted(daily_scores.keys()):
            scores = daily_scores[day]
            trend.append({
                "date": day,
                "avg_quality": round(sum(scores) / len(scores), 3),
                "turns": len(scores),
            })

        return {
            "period_days": days,
            "total_turns": len(recent_turns),
            "avg_quality": round(sum(t.overall_score for t in recent_turns) / len(recent_turns), 3),
            "trend": trend,
            "trend_direction": "improving" if len(trend) > 1 and trend[-1]["avg_quality"] > trend[0]["avg_quality"] else "stable",
        }

    # ── Statistics ──────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "total_conversations": len(self._conversations),
            "recent_avg_quality": round(
                sum(t.overall_score for t in list(self._turns)[-20:]) / max(min(len(self._turns), 20), 1), 3
            ),
        }

    # ── Persistence ────────────────────────────────────────────────────────

    def _save_db(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "stats": self._stats,
                "conversations": [
                    {
                        "conversation_id": c.conversation_id,
                        "start_time": c.start_time,
                        "end_time": c.end_time,
                        "turn_count": c.turn_count,
                        "avg_quality": c.avg_quality,
                        "dominant_emotion": c.dominant_emotion,
                        "suggestions": c.suggestions,
                    }
                    for c in self._conversations.values()
                ],
            }
            QUALITY_DB.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.conversation_quality")

    def _load_db(self):
        try:
            if QUALITY_DB.exists():
                data = json.loads(QUALITY_DB.read_text())
                self._stats = data.get("stats", self._stats)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.conversation_quality")

    def _log_trend(self, summary: ConversationSummary):
        try:
            with open(TRENDS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": summary.end_time or datetime.now().isoformat(),
                    "conversation_id": summary.conversation_id,
                    "avg_quality": summary.avg_quality,
                    "turn_count": summary.turn_count,
                    "dominant_emotion": summary.dominant_emotion,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.conversation_quality")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_quality_analyzer_instance: Optional[ConversationQualityAnalyzer] = None
_quality_analyzer_lock = threading.Lock()


def get_conversation_quality_analyzer() -> ConversationQualityAnalyzer:
    global _quality_analyzer_instance
    with _quality_analyzer_lock:
        if _quality_analyzer_instance is None:
            _quality_analyzer_instance = ConversationQualityAnalyzer()
        return _quality_analyzer_instance
