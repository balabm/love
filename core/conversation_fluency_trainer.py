"""
LOVE Conversation Fluency Trainer — Spoken Language Intelligence (Modern AI Pattern)

Most people can read a language but can't speak it. This trainer:

1. CONVERSATION TRACKING
   - Record conversation moments and their characteristics
   - Track conversation types (casual, formal, debate, story, instruction, emotional)
   - Log fluency, vocabulary, grammar, listening, and confidence of conversations

2. PATTERN ANALYSIS
   - Identify the user's conversation profile (silent, hesitant, developing, fluent)
   - Find conversation patterns that create flow vs blockage
   - Detect chronic passive learning and its costs

3. FLUENCY BUILDING
   - Suggest practices for building speaking confidence
   - Provide frameworks for conversation strategies
   - Recommend practices for overcoming speaking anxiety

4. SPEAKING MASTERY CULTIVATION
   - Track the correlation between speaking practice and fluency growth
   - Alert when listening is replacing speaking
   - Celebrate moments of genuine conversational breakthrough

Architecture:
- record_conversation(topic, type, fluency, vocabulary, grammar, listening, confidence): Log conversation
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

DATA_DIR = Path(__file__).parent.parent / "data" / "conversation_fluency_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONVERSATION_LOG = DATA_DIR / "conversations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ConversationEntry:
    """A tracked conversation moment."""
    entry_id: str = ""
    topic: str = ""  # what was the topic
    conversation_type: str = ""  # casual, formal, debate, story, instruction, emotional
    fluency: float = 0.0  # 0-1
    vocabulary: float = 0.0  # 0-1
    grammar: float = 0.0  # 0-1
    listening: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ConversationFluencyTrainer:
    """
    Intelligent conversation fluency trainer with passivity detection and speaking mastery cultivation.
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
            "avg_fluency": 0.0,
            "avg_confidence": 0.0,
            "passivity_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_conversation(self, topic: str = "", conversation_type: str = "", fluency: float = 0.0, vocabulary: float = 0.0, grammar: float = 0.0, listening: float = 0.0, confidence: float = 0.0, connection: float = 0.0, notes: str = "") -> ConversationEntry:
        """Record a conversation moment."""
        entry_id = f"con_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ConversationEntry(
            entry_id=entry_id,
            topic=topic or "unspecified",
            conversation_type=conversation_type or "casual",
            fluency=fluency,
            vocabulary=vocabulary,
            grammar=grammar,
            listening=listening,
            confidence=confidence,
            connection=connection,
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
        by_type = defaultdict(lambda: {"count": 0, "fluency_sum": 0.0, "confidence_sum": 0.0, "connection_sum": 0.0})
        for e in self._entries:
            by_type[e.conversation_type]["count"] += 1
            by_type[e.conversation_type]["fluency_sum"] += e.fluency
            by_type[e.conversation_type]["confidence_sum"] += e.confidence
            by_type[e.conversation_type]["connection_sum"] += e.connection

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_fluency": round(data["fluency_sum"] / count, 2),
                "avg_confidence": round(data["confidence_sum"] / count, 2),
                "avg_connection": round(data["connection_sum"] / count, 2),
            }

        # Fluency analysis
        high_flu = [e for e in self._entries if e.fluency > 0.7]
        low_flu = [e for e in self._entries if e.fluency < 0.4]
        if high_flu and low_flu:
            high_flu_conf = sum(e.confidence for e in high_flu) / len(high_flu)
            low_flu_conf = sum(e.confidence for e in low_flu) / len(low_flu)
            high_flu_conn = sum(e.connection for e in high_flu) / len(high_flu)
            low_flu_conn = sum(e.connection for e in low_flu) / len(low_flu)
        else:
            high_flu_conf = 0
            low_flu_conf = 0
            high_flu_conn = 0
            low_flu_conn = 0

        # Confidence analysis
        high_conf = [e for e in self._entries if e.confidence > 0.7]
        low_conf = [e for e in self._entries if e.confidence < 0.4]
        if high_conf and low_conf:
            high_conf_flu = sum(e.fluency for e in high_conf) / len(high_conf)
            low_conf_flu = sum(e.fluency for e in low_conf) / len(low_conf)
        else:
            high_conf_flu = 0
            low_conf_flu = 0

        # Passivity risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_flu = sum(e.fluency for e in recent) / len(recent)
            recent_conf = sum(e.confidence for e in recent) / len(recent)
            passivity_risk = recent_flu < 0.3 and recent_conf < 0.3
        else:
            passivity_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "fluency_impact": {
                "high_fluency_confidence": round(high_flu_conf, 2),
                "low_fluency_confidence": round(low_flu_conf, 2),
                "high_fluency_connection": round(high_flu_conn, 2),
                "low_fluency_connection": round(low_flu_conn, 2),
            },
            "confidence_effect": {
                "high_confidence_fluency": round(high_conf_flu, 2),
                "low_confidence_fluency": round(low_conf_flu, 2),
            },
            "passivity_risk": passivity_risk,
            "avg_fluency": round(sum(e.fluency for e in self._entries) / len(self._entries), 2),
            "avg_confidence": round(sum(e.confidence for e in self._entries) / len(self._entries), 2),
        }

    def get_conversation_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get conversation suggestion."""
        suggestions = [
            "Most people can understand a language but can't speak it. They can read novels. They can watch movies. They can follow podcasts. But when someone asks them a question, they freeze. They stumble. They reach for words that won't come. And they feel ashamed. The gap between passive and active knowledge is the gap between knowing and doing.",
            "Speak every day. Not perfectly. Not eloquently. Just speak. To yourself. To a partner. To a pet. To a recording. To a mirror. The mouth needs practice. The tongue needs exercise. The brain needs to connect thought to speech. Daily speaking is the only path to fluency.",
            "Shadow native speakers. Listen to a sentence. Pause. Repeat it exactly. The rhythm. The intonation. The pauses. The emphasis. Shadowing trains your mouth to make the sounds. Your ear to hear the music. Your brain to process the speed. It's the fastest way to sound natural.",
            "Prepare topics. Not scripts. Topics you care about. Your work. Your hobbies. Your opinions. Your stories. Prepare vocabulary. Prepare phrases. Prepare how to start. The person who prepares speaks with more confidence. And confidence creates fluency.",
            "Embrace the awkward pause. It's not failure. It's processing. Native speakers pause too. They search for words. They change direction. They say 'um' and 'uh.' The awkward pause is normal. Don't fear it. Use it. Breathe. Think. Continue.",
            "Talk about what you love. Not what you think you should talk about. Passion creates vocabulary. Enthusiasm creates fluency. When you care about the topic, you forget about the language. And that's when you speak best.",
            "Record yourself. Listen back. Cringe. Then learn. Where do you hesitate? What words do you reach for? What grammar do you misuse? Recording is a mirror. It shows you what you can't feel in the moment. And that awareness is the foundation of improvement.",
            "Ask questions. When you don't know what to say. When you don't understand. When you need time. Questions are conversation savers. 'What do you mean?' 'Can you say that again?' 'How do you say...?' These are not signs of weakness. They're tools of the learner.",
            "Celebrate small wins. The first full sentence. The first joke that landed. The first argument you held your own in. The first story you told that made someone laugh. These are milestones. Not the final destination. But steps on the path. And each one matters.",
            "The person who trains conversation fluency is not just learning to speak. They're learning to think in a new language. To feel in a new language. To be in a new language. And that is not just a skill. It's a transformation. It changes who you are. It multiplies who you can be."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One sentence spoken. One shadowing session. One topic prepared. One recording made. One question asked. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A daily speaking practice. A shadowing routine. A prepared topic used. A recording reviewed. A small win celebrated. Medium fluency."
        else:
            capacity_note = "Good capacity. Deep conversation fluency work. A systematic practice of speaking, shadowing, preparing, and connecting. You have the strength to hold a conversation in any language."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Conversation fluency training is not about knowing more words. It's about using the words you know. Most language learners accumulate passive knowledge. They can read. They can listen. They can understand. But they can't speak. Because speaking is a different skill. It requires practice. It requires courage. It requires failure. And it requires the willingness to sound bad before you sound good. The work of conversation fluency training is about understanding that fluency comes from use, not study. From speaking, not reading. From interaction, not isolation. And that the person who commits to daily speaking practice - however imperfect - is the person who will eventually speak with ease, confidence, and genuine connection."
        }

    def get_conversation_score(self) -> int:
        """Calculate overall conversation health (0-100)."""
        if not self._entries:
            return 25

        avg_flu = sum(e.fluency for e in self._entries) / len(self._entries)
        avg_voc = sum(e.vocabulary for e in self._entries) / len(self._entries)
        avg_gram = sum(e.grammar for e in self._entries) / len(self._entries)
        avg_listen = sum(e.listening for e in self._entries) / len(self._entries)
        avg_conf = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_conn = sum(e.connection for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_flu = sum(e.fluency for e in recent) / len(recent)
            recent_conf = sum(e.confidence for e in recent) / len(recent)
        else:
            recent_flu = 0
            recent_conf = 0

        # Passivity penalty
        pass_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_flu_30 = sum(e.fluency for e in last_30) / len(last_30)
            recent_conf_30 = sum(e.confidence for e in last_30) / len(last_30)
            if recent_flu_30 < 0.3 and recent_conf_30 < 0.3:
                pass_penalty = 15

        # Type variety
        unique_types = len(set(e.conversation_type for e in self._entries))

        score = (avg_flu * 25) + (avg_voc * 10) + (avg_gram * 10) + (avg_listen * 10) + (avg_conf * 20) + (avg_conn * 15) + (recent_flu * 5) + (recent_conf * 5) + (unique_types * 2) - pass_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_fluency"] = round(sum(e.fluency for e in self._entries) / len(self._entries), 2)
            self._stats["avg_confidence"] = round(sum(e.confidence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_flu = sum(e.fluency for e in recent) / len(recent)
                recent_conf = sum(e.confidence for e in recent) / len(recent)
                self._stats["passivity_risk"] = recent_flu < 0.3 and recent_conf < 0.3
            else:
                self._stats["passivity_risk"] = False

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
                    "fluency": entry.fluency,
                    "confidence": entry.confidence,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cft_instance: Optional[ConversationFluencyTrainer] = None
_cft_lock = threading.Lock()


def get_conversation_fluency_trainer() -> ConversationFluencyTrainer:
    global _cft_instance
    with _cft_lock:
        if _cft_instance is None:
            _cft_instance = ConversationFluencyTrainer()
        return _cft_instance
