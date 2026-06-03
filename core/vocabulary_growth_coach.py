"""
LOVE Vocabulary Growth Coach — Word Mastery Intelligence (Modern AI Pattern)

Most people memorize words without owning them. This coach:

1. VOCABULARY TRACKING
   - Record vocabulary moments and their characteristics
   - Track vocabulary types (learn, use, review, connect, teach, discover)
   - Log retention, usage, context, depth, and joy of words

2. PATTERN ANALYSIS
   - Identify the user's vocabulary profile (passive, memorizing, developing, masterful)
   - Find vocabulary patterns that create ownership vs forgetfulness
   - Detect chronic passive accumulation and its costs

3. MASTERY BUILDING
   - Suggest practices for truly owning new words
   - Provide frameworks for contextual, active vocabulary learning
   - Recommend practices for memorable, meaningful word acquisition

4. VOCABULARY MASTERY CULTIVATION
   - Track the correlation between active usage and word retention
   - Alert when collecting is replacing connecting
   - Celebrate moments of genuine lexical power

Architecture:
- record_vocabulary(word, type, retention, usage, context, depth, joy): Log vocabulary
- get_vocabulary_stats(): Get vocabulary pattern analysis
- get_vocabulary_suggestion(capacity, context): Get suggestion
- get_vocabulary_score(): Calculate overall vocabulary health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "vocabulary_growth_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VOCABULARY_LOG = DATA_DIR / "vocabularies.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class VocabularyEntry:
    """A tracked vocabulary moment."""
    entry_id: str = ""
    word: str = ""  # what was the word
    vocabulary_type: str = ""  # learn, use, review, connect, teach, discover
    retention: float = 0.0  # 0-1
    usage: float = 0.0  # 0-1
    context: float = 0.0  # 0-1
    depth: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VocabularyGrowthCoach:
    """
    Intelligent vocabulary growth coach with passivity detection and vocabulary mastery cultivation.
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
            "avg_retention": 0.0,
            "avg_usage": 0.0,
            "accumulation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_vocabulary(self, word: str = "", vocabulary_type: str = "", retention: float = 0.0, usage: float = 0.0, context: float = 0.0, depth: float = 0.0, joy: float = 0.0, connection: float = 0.0, notes: str = "") -> VocabularyEntry:
        """Record a vocabulary moment."""
        entry_id = f"voc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = VocabularyEntry(
            entry_id=entry_id,
            word=word or "unspecified",
            vocabulary_type=vocabulary_type or "learn",
            retention=retention,
            usage=usage,
            context=context,
            depth=depth,
            joy=joy,
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

    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """Get vocabulary pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "retention_sum": 0.0, "usage_sum": 0.0, "joy_sum": 0.0})
        for e in self._entries:
            by_type[e.vocabulary_type]["count"] += 1
            by_type[e.vocabulary_type]["retention_sum"] += e.retention
            by_type[e.vocabulary_type]["usage_sum"] += e.usage
            by_type[e.vocabulary_type]["joy_sum"] += e.joy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_retention": round(data["retention_sum"] / count, 2),
                "avg_usage": round(data["usage_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Retention analysis
        high_ret = [e for e in self._entries if e.retention > 0.7]
        low_ret = [e for e in self._entries if e.retention < 0.4]
        if high_ret and low_ret:
            high_ret_use = sum(e.usage for e in high_ret) / len(high_ret)
            low_ret_use = sum(e.usage for e in low_ret) / len(low_ret)
            high_ret_depth = sum(e.depth for e in high_ret) / len(high_ret)
            low_ret_depth = sum(e.depth for e in low_ret) / len(low_ret)
        else:
            high_ret_use = 0
            low_ret_use = 0
            high_ret_depth = 0
            low_ret_depth = 0

        # Connection analysis
        high_conn = [e for e in self._entries if e.connection > 0.7]
        low_conn = [e for e in self._entries if e.connection < 0.4]
        if high_conn and low_conn:
            high_conn_ret = sum(e.retention for e in high_conn) / len(high_conn)
            low_conn_ret = sum(e.retention for e in low_conn) / len(low_conn)
        else:
            high_conn_ret = 0
            low_conn_ret = 0

        # Accumulation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_ret = sum(e.retention for e in recent) / len(recent)
            recent_use = sum(e.usage for e in recent) / len(recent)
            accumulation_risk = recent_ret < 0.3 and recent_use < 0.3
        else:
            accumulation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "retention_impact": {
                "high_retention_usage": round(high_ret_use, 2),
                "low_retention_usage": round(low_ret_use, 2),
                "high_retention_depth": round(high_ret_depth, 2),
                "low_retention_depth": round(low_ret_depth, 2),
            },
            "connection_effect": {
                "high_connection_retention": round(high_conn_ret, 2),
                "low_connection_retention": round(low_conn_ret, 2),
            },
            "accumulation_risk": accumulation_risk,
            "avg_retention": round(sum(e.retention for e in self._entries) / len(self._entries), 2),
            "avg_usage": round(sum(e.usage for e in self._entries) / len(self._entries), 2),
        }

    def get_vocabulary_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get vocabulary suggestion."""
        suggestions = [
            "Most people collect words like stamps. They have thousands. And they use none. They know what the words mean. But they don't own them. Because ownership comes from use. From context. From connection. Not from memorization.",
            "Learn words in sentences. Not in lists. Not in isolation. In context. 'The ephemeral beauty of cherry blossoms.' Not 'ephemeral: lasting for a short time.' Context creates memory. Sentences create meaning. Stories create ownership.",
            "Use new words immediately. In a sentence. In a conversation. In a text. In a journal. The word you don't use is the word you don't know. Use it three times in the first day. Five times in the first week. Until it feels natural. Until you own it.",
            "Connect words to your life. Not to definitions. To experiences. To feelings. To memories. The word 'solitude' is not 'being alone.' It's that Sunday morning when the house is quiet and you have the whole day. Connect words to what you know. And you'll never forget them.",
            "Review with spaced repetition. Not cramming. Not once. Not twice. At intervals. One day. Three days. One week. One month. The brain forgets on a curve. Fight the curve with timing. The right review at the right time creates permanent memory.",
            "Teach words to someone. The best way to learn is to teach. Explain the word. Use it in a sentence. Create a story with it. The person who teaches a word owns it. Because teaching forces understanding. And understanding forces memory.",
            "Read widely. Not just one genre. Not just one topic. Fiction. Non-fiction. Poetry. Science. History. Philosophy. Each domain has its own vocabulary. Its own rhythms. Its own expressions. The wide reader has a wide vocabulary. And a wide mind.",
            "Play with words. Puns. Word games. Crosswords. Anagrams. Rhymes. Etymology. The person who plays with words loves words. And the person who loves words learns words. Play is not frivolous. Play is practice in disguise.",
            "Notice words you love. Not just words you need. The sound. The feel. The meaning. The history. Collect beautiful words. Words that make you pause. Words that make you think. Words that make you feel. A vocabulary of beauty is a vocabulary of power.",
            "The person who grows their vocabulary is not just learning words. They're learning precision. They're learning nuance. They're learning to say exactly what they mean. And the person who can say exactly what they mean can think exactly what they mean. And that is the foundation of all mastery."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One word in a sentence. One word used. One word connected to memory. One word taught. One beautiful word noticed. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A daily word practice. A spaced review. A contextual learning session. A teaching moment. A wide reading habit. Medium mastery."
        else:
            capacity_note = "Good capacity. Deep vocabulary growth work. A systematic practice of contextual learning, active usage, meaningful connection, and spaced review. You have the strength to own any word."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Vocabulary growth coaching is not about memorizing more words. It's about owning the words you learn. Most people treat vocabulary as a collection. They accumulate words. They test themselves. They forget. And they accumulate more. The work of vocabulary growth coaching is about understanding that a word is not truly learned until it is used. Until it is connected. Until it is owned. It's about learning words in context. Using them immediately. Connecting them to experience. Reviewing them strategically. And understanding that vocabulary is not just a measure of knowledge. It's a measure of precision. Of nuance. Of the ability to say exactly what you mean. And the person who grows their vocabulary with intention is the person who grows their mind."
        }

    def get_vocabulary_score(self) -> int:
        """Calculate overall vocabulary health (0-100)."""
        if not self._entries:
            return 25

        avg_ret = sum(e.retention for e in self._entries) / len(self._entries)
        avg_use = sum(e.usage for e in self._entries) / len(self._entries)
        avg_ctx = sum(e.context for e in self._entries) / len(self._entries)
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_conn = sum(e.connection for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_ret = sum(e.retention for e in recent) / len(recent)
            recent_use = sum(e.usage for e in recent) / len(recent)
        else:
            recent_ret = 0
            recent_use = 0

        # Accumulation penalty
        accum_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_ret_30 = sum(e.retention for e in last_30) / len(last_30)
            recent_use_30 = sum(e.usage for e in last_30) / len(last_30)
            if recent_ret_30 < 0.3 and recent_use_30 < 0.3:
                accum_penalty = 15

        # Type variety
        unique_types = len(set(e.vocabulary_type for e in self._entries))

        score = (avg_ret * 25) + (avg_use * 20) + (avg_ctx * 10) + (avg_depth * 15) + (avg_joy * 10) + (avg_conn * 15) + (recent_ret * 5) + (recent_use * 5) + (unique_types * 2) - accum_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_retention"] = round(sum(e.retention for e in self._entries) / len(self._entries), 2)
            self._stats["avg_usage"] = round(sum(e.usage for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_ret = sum(e.retention for e in recent) / len(recent)
                recent_use = sum(e.usage for e in recent) / len(recent)
                self._stats["accumulation_risk"] = recent_ret < 0.3 and recent_use < 0.3
            else:
                self._stats["accumulation_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.vocabulary_growth_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.vocabulary_growth_coach")

    def _log_entry(self, entry: VocabularyEntry):
        try:
            with open(VOCABULARY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "word": entry.word,
                    "vocabulary_type": entry.vocabulary_type,
                    "retention": entry.retention,
                    "usage": entry.usage,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.vocabulary_growth_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vgc_instance: Optional[VocabularyGrowthCoach] = None
_vgc_lock = threading.Lock()


def get_vocabulary_growth_coach() -> VocabularyGrowthCoach:
    global _vgc_instance
    with _vgc_lock:
        if _vgc_instance is None:
            _vgc_instance = VocabularyGrowthCoach()
        return _vgc_instance
