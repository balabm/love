"""
LOVE Difficult Conversation Navigator — Conflict Intelligence (Modern AI Pattern)

Most people avoid difficult conversations. This navigator:

1. CONVERSATION TRACKING
   - Record difficult conversations and their characteristics
   - Track conversation types (feedback, boundary, conflict, breakup, apology, confrontation)
   - Log preparation, delivery, reception, and outcome of conversations

2. PATTERN ANALYSIS
   - Identify the user's conversation profile (avoidant, reactive, prepared, masterful)
   - Find conversation patterns that resolve vs escalate conflict
   - Detect chronic avoidance and its costs

3. NAVIGATION BUILDING
   - Suggest practices for preparing and delivering difficult messages
   - Provide frameworks for non-violent communication and active listening
   - Recommend practices for managing emotions during conflict

4. COURAGEOUS DIALOGUE CULTIVATION
   - Track the correlation between conversation quality and relationship health
   - Alert when avoidance is becoming the default
   - Celebrate moments of genuine, skillful confrontation

Architecture:
- record_conversation(topic, type, preparation, delivery, reception, outcome): Log conversation
- get_conversation_stats(): Get conversation pattern analysis
- get_conversation_suggestion(capacity, context): Get suggestion
- get_conversation_score(): Calculate overall conversation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "difficult_conversation_navigator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONVERSATION_LOG = DATA_DIR / "conversations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ConversationEntry:
    """A tracked difficult conversation."""
    entry_id: str = ""
    topic: str = ""  # what was discussed
    conversation_type: str = ""  # feedback, boundary, conflict, breakup, apology, confrontation
    preparation: float = 0.0  # 0-1
    delivery: float = 0.0  # 0-1
    reception: float = 0.0  # 0-1
    outcome: float = 0.0  # 0-1
    emotion_management: float = 0.0  # 0-1
    follow_up: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DifficultConversationNavigator:
    """
    Intelligent difficult conversation navigator with avoidance detection and courageous dialogue cultivation.
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
        self._entries: deque = deque(maxlen=300)
        self._stats = {
            "total_entries": 0,
            "avg_preparation": 0.0,
            "avg_outcome": 0.0,
            "avoidance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_conversation(self, topic: str = "", conversation_type: str = "", preparation: float = 0.0, delivery: float = 0.0, reception: float = 0.0, outcome: float = 0.0, emotion_management: float = 0.0, follow_up: float = 0.0, notes: str = "") -> ConversationEntry:
        """Record a difficult conversation."""
        entry_id = f"cnv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ConversationEntry(
            entry_id=entry_id,
            topic=topic or "unspecified",
            conversation_type=conversation_type or "feedback",
            preparation=preparation,
            delivery=delivery,
            reception=reception,
            outcome=outcome,
            emotion_management=emotion_management,
            follow_up=follow_up,
            notes=notes,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_stats()

        self._save_stats()
        self._log_entry(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "prep_sum": 0.0, "delivery_sum": 0.0, "outcome_sum": 0.0})
        for e in self._entries:
            by_type[e.conversation_type]["count"] += 1
            by_type[e.conversation_type]["prep_sum"] += e.preparation
            by_type[e.conversation_type]["delivery_sum"] += e.delivery
            by_type[e.conversation_type]["outcome_sum"] += e.outcome

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_preparation": round(data["prep_sum"] / count, 2),
                "avg_delivery": round(data["delivery_sum"] / count, 2),
                "avg_outcome": round(data["outcome_sum"] / count, 2),
            }

        # Preparation analysis
        high_prep = [e for e in self._entries if e.preparation > 0.7]
        low_prep = [e for e in self._entries if e.preparation < 0.4]
        if high_prep and low_prep:
            high_prep_out = sum(e.outcome for e in high_prep) / len(high_prep)
            low_prep_out = sum(e.outcome for e in low_prep) / len(low_prep)
            high_prep_del = sum(e.delivery for e in high_prep) / len(high_prep)
            low_prep_del = sum(e.delivery for e in low_prep) / len(low_prep)
        else:
            high_prep_out = 0
            low_prep_out = 0
            high_prep_del = 0
            low_prep_del = 0

        # Emotion management analysis
        high_emo = [e for e in self._entries if e.emotion_management > 0.7]
        low_emo = [e for e in self._entries if e.emotion_management < 0.4]
        if high_emo and low_emo:
            high_emo_out = sum(e.outcome for e in high_emo) / len(high_emo)
            low_emo_out = sum(e.outcome for e in low_emo) / len(low_emo)
        else:
            high_emo_out = 0
            low_emo_out = 0

        # Avoidance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_prep = sum(e.preparation for e in recent) / len(recent)
            recent_out = sum(e.outcome for e in recent) / len(recent)
            avoidance_risk = recent_prep < 0.3 and recent_out < 0.3
        else:
            avoidance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "preparation_impact": {
                "high_preparation_outcome": round(high_prep_out, 2),
                "low_preparation_outcome": round(low_prep_out, 2),
                "high_preparation_delivery": round(high_prep_del, 2),
                "low_preparation_delivery": round(low_prep_del, 2),
            },
            "emotion_effect": {
                "high_emotion_management_outcome": round(high_emo_out, 2),
                "low_emotion_management_outcome": round(low_emo_out, 2),
            },
            "avoidance_risk": avoidance_risk,
            "avg_preparation": round(sum(e.preparation for e in self._entries) / len(self._entries), 2),
            "avg_outcome": round(sum(e.outcome for e in self._entries) / len(self._entries), 2),
        }

    def get_conversation_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get conversation suggestion."""
        suggestions = [
            "Difficult conversations are not about winning. They're about understanding. About being understood. About finding a way forward. If you're trying to win, you've already lost.",
            "Prepare. Not to script. To clarify. What do you want? What do they want? What's the gap? What's your request? Clarity before the conversation prevents confusion during it.",
            "Use 'I' statements. 'I feel hurt when...' not 'You always...' Own your experience. Don't accuse. The moment you accuse, they defend. And the conversation ends.",
            "Listen more than you speak. Difficult conversations are not speeches. They're dialogues. Ask questions. Seek understanding. You might learn something that changes everything.",
            "Manage your emotions. Not by suppressing them. By noticing them. 'I'm getting angry. I'll pause.' Emotion is information. But it's terrible at driving. Let it inform. Then decide.",
            "Start with curiosity, not conclusion. 'Help me understand...' not 'You need to stop...' Curiosity opens doors. Conclusions close them. Be a door opener.",
            "Pick the right time. Not when you're exhausted. Not when they're stressed. Not in public. Not over text. Difficult conversations deserve difficult preparation. Including timing.",
            "Follow up. The conversation doesn't end when you stop talking. Check in. 'How are you feeling about our conversation?' Relationships are built in the follow-up, not the confrontation.",
            "Be willing to be wrong. You might have misunderstood. You might have contributed. You might be the problem. Hold your position lightly. Be ready to adjust. That's strength.",
            "The conversation you're avoiding is the conversation you need to have. It doesn't get easier with time. It gets harder. And more damaging. Have it now. Prepare. Then have it."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small conversation. One honest sentence. One moment of courage. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A prepared conversation. An 'I' statement practiced. A follow-up planned. Medium navigation."
        else:
            capacity_note = "Good capacity. Deep conversation skill. A systematic approach to difficult dialogue. You have the strength to navigate any conversation."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Difficult conversations are the price of meaningful relationships. You cannot have depth without them. You cannot have growth without them. You cannot have honesty without them. And yet most people avoid them. They tolerate the intolerable. They accept the unacceptable. They silence their truth. And they wonder why their relationships feel shallow. Why they feel resentful. Why they feel invisible. The work of difficult conversation navigation is about building the skill to have these conversations well. About preparing. About delivering with kindness. About listening with curiosity. About managing emotions. And about following up. It's not about winning. It's about understanding. It's not about being right. It's about being connected. And it's about recognizing that the conversation you're avoiding is costing you more than the conversation you're fearing."
        }

    def get_conversation_score(self) -> int:
        """Calculate overall conversation health (0-100)."""
        if not self._entries:
            return 25

        avg_prep = sum(e.preparation for e in self._entries) / len(self._entries)
        avg_del = sum(e.delivery for e in self._entries) / len(self._entries)
        avg_out = sum(e.outcome for e in self._entries) / len(self._entries)
        avg_emo = sum(e.emotion_management for e in self._entries) / len(self._entries)
        avg_follow = sum(e.follow_up for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_prep = sum(e.preparation for e in recent) / len(recent)
            recent_out = sum(e.outcome for e in recent) / len(recent)
        else:
            recent_prep = 0
            recent_out = 0

        # Avoidance penalty
        avoid_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_prep_30 = sum(e.preparation for e in last_30) / len(last_30)
            recent_out_30 = sum(e.outcome for e in last_30) / len(last_30)
            if recent_prep_30 < 0.3 and recent_out_30 < 0.3:
                avoid_penalty = 15

        # Type variety
        unique_types = len(set(e.conversation_type for e in self._entries))

        score = (avg_prep * 20) + (avg_del * 20) + (avg_out * 20) + (avg_emo * 15) + (avg_follow * 10) + (recent_prep * 5) + (recent_out * 5) + (unique_types * 2) - avoid_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_preparation"] = round(sum(e.preparation for e in self._entries) / len(self._entries), 2)
            self._stats["avg_outcome"] = round(sum(e.outcome for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_prep = sum(e.preparation for e in recent) / len(recent)
                recent_out = sum(e.outcome for e in recent) / len(recent)
                self._stats["avoidance_risk"] = recent_prep < 0.3 and recent_out < 0.3
            else:
                self._stats["avoidance_risk"] = False

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

    def _log_entry(self, entry: ConversationEntry):
        try:
            with open(CONVERSATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "topic": entry.topic,
                    "conversation_type": entry.conversation_type,
                    "preparation": entry.preparation,
                    "outcome": entry.outcome,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dcn_instance: Optional[DifficultConversationNavigator] = None
_dcn_lock = threading.Lock()


def get_difficult_conversation_navigator() -> DifficultConversationNavigator:
    global _dcn_instance
    with _dcn_lock:
        if _dcn_instance is None:
            _dcn_instance = DifficultConversationNavigator()
        return _dcn_instance
