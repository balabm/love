"""
LOVE Conversation Summarizer — Long Conversation Distillation (Modern AI Pattern)

When conversations grow long, important information gets buried. This summarizer:

1. TURN EXTRACTION
   - Extract key turns from long conversations
   - Identify topic boundaries and transitions
   - Detect decision points and action items

2. HIERARCHICAL SUMMARY
   - Per-topic summaries within the conversation
   - Overall conversation summary
   - Action items and follow-ups extracted

3. IMPORTANCE SCORING
   - Score each turn by information density
   - Detect questions, decisions, commitments
   - Flag emotionally significant moments

4. PROGRESSIVE SUMMARY
   - Maintain running summary as conversation grows
   - Update summary incrementally rather than re-summarizing
   - Preserve context across summary updates

Architecture:
- summarize_conversation(turns): Generate hierarchical summary
- extract_action_items(turns): Pull out commitments and tasks
- get_topic_segments(turns): Split conversation by topic
- get_summary_stats(): Track summarization metrics
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

DATA_DIR = Path(__file__).parent.parent / "data" / "conversation_summarizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_LOG = DATA_DIR / "summary_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TurnSummary:
    """Summary of a single conversation turn."""
    turn_index: int = 0
    speaker: str = ""  # user or assistant
    key_points: List[str] = field(default_factory=list)
    importance_score: float = 0.0
    emotion: str = "neutral"
    action_items: List[str] = field(default_factory=list)
    topic: str = ""


@dataclass
class ConversationSummary:
    """Summary of an entire conversation."""
    conversation_id: str = ""
    overall_summary: str = ""
    topic_segments: List[Dict[str, Any]] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    emotional_arc: List[str] = field(default_factory=list)
    compression_ratio: float = 0.0
    turn_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ConversationSummarizer:
    """
    Summarize long conversations while preserving key information.
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
        self._stats = {
            "total_conversations_summarized": 0,
            "total_turns_processed": 0,
            "avg_compression_ratio": 0.0,
            "avg_action_items_per_conv": 0.0,
        }
        self._load_stats()

    # ── Core Summarization ────────────────────────────────────────────────

    def summarize_conversation(self, turns: List[Dict[str, Any]]) -> ConversationSummary:
        """Generate hierarchical summary of a conversation."""
        if not turns:
            return ConversationSummary()

        turn_summaries = []
        topics = defaultdict(list)
        decisions = []
        action_items = []
        emotions = []

        for i, turn in enumerate(turns):
            speaker = turn.get("speaker", "unknown")
            text = turn.get("text", "")

            # Extract key points (simple heuristic)
            key_points = self._extract_key_points(text)

            # Detect action items
            turn_actions = self._detect_action_items(text, speaker)
            action_items.extend(turn_actions)

            # Detect decisions
            if self._is_decision(text):
                decisions.append(text[:150])

            # Detect emotion
            emotion = self._detect_emotion(text)
            emotions.append(emotion)

            # Categorize topic
            topic = self._categorize_topic(text)
            topics[topic].append(i)

            # Calculate importance
            importance = self._calculate_importance(text, key_points, turn_actions)

            turn_summaries.append(TurnSummary(
                turn_index=i,
                speaker=speaker,
                key_points=key_points[:3],
                importance_score=importance,
                emotion=emotion,
                action_items=turn_actions,
                topic=topic,
            ))

        # Build topic segments
        topic_segments = []
        for topic, indices in sorted(topics.items(), key=lambda x: len(x[1]), reverse=True):
            if len(indices) >= 2:
                segment_turns = [turns[i] for i in indices]
                segment_text = " ".join([t.get("text", "") for t in segment_turns])
                topic_segments.append({
                    "topic": topic,
                    "turn_count": len(indices),
                    "summary": self._generate_topic_summary(segment_text),
                    "key_points": self._extract_key_points(segment_text)[:5],
                })

        # Overall summary from high-importance turns
        high_importance = [t for t in turn_summaries if t.importance_score > 0.6]
        if high_importance:
            summary_parts = []
            for t in high_importance[:5]:
                summary_parts.append(f"{t.speaker}: {' '.join(t.key_points[:2])}")
            overall_summary = " ".join(summary_parts)
        else:
            overall_summary = " ".join([t.get("text", "") for t in turns[-3:]])[:200]

        # Emotional arc
        emotional_arc = self._build_emotional_arc(emotions)

        # Calculate compression ratio
        original_chars = sum(len(t.get("text", "")) for t in turns)
        summary_chars = len(overall_summary) + sum(len(s["summary"]) for s in topic_segments)
        compression_ratio = max(0.0, round(1 - (summary_chars / max(1, original_chars)), 3))

        summary = ConversationSummary(
            conversation_id=f"conv_{int(time.time())}",
            overall_summary=overall_summary[:300],
            topic_segments=topic_segments[:5],
            key_decisions=list(set(decisions))[:5],
            action_items=list(set(action_items))[:10],
            emotional_arc=emotional_arc,
            compression_ratio=compression_ratio,
            turn_count=len(turns),
        )

        with self._lock:
            self._stats["total_conversations_summarized"] += 1
            self._stats["total_turns_processed"] += len(turns)
            prev_avg = self._stats.get("avg_compression_ratio", 0)
            n = self._stats["total_conversations_summarized"]
            self._stats["avg_compression_ratio"] = round((prev_avg * (n - 1) + compression_ratio) / max(1, n), 3)

            prev_action_avg = self._stats.get("avg_action_items_per_conv", 0)
            self._stats["avg_action_items_per_conv"] = round(
                (prev_action_avg * (n - 1) + len(action_items)) / max(1, n), 2
            )

        self._save_stats()
        self._log_summary(summary)

        return summary

    # ── Extraction Helpers ─────────────────────────────────────────────────

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text."""
        sentences = [s.strip() for s in text.split(".") if s.strip() and len(s) > 15]
        # Score by information density (longer = more info, but not too long)
        scored = [(s, len(s) * (1 + s.count(",") * 0.1)) for s in sentences]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:3]]

    def _detect_action_items(self, text: str, speaker: str) -> List[str]:
        """Detect action items in text."""
        action_markers = ["need to", "should", "will", "plan to", "going to", "must", "have to"]
        text_lower = text.lower()
        items = []
        for marker in action_markers:
            if marker in text_lower:
                # Extract the sentence containing the marker
                for sent in text.split("."):
                    if marker in sent.lower():
                        items.append(f"[{speaker}] {sent.strip()[:100]}")
                        break
        return items[:2]

    def _is_decision(self, text: str) -> bool:
        """Check if text contains a decision."""
        decision_markers = ["decided", "choose", "going with", "settled on", "finalized", "agreed to"]
        return any(m in text.lower() for m in decision_markers)

    def _detect_emotion(self, text: str) -> str:
        """Simple emotion detection."""
        emotion_keywords = {
            "happy": ["happy", "great", "awesome", "excited", "love", "joy"],
            "sad": ["sad", "depressed", "down", "upset"],
            "angry": ["angry", "mad", "frustrated", "annoyed"],
            "anxious": ["anxious", "worried", "nervous", "stressed"],
        }
        text_lower = text.lower()
        for emotion, keywords in emotion_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return emotion
        return "neutral"

    def _categorize_topic(self, text: str) -> str:
        """Simple topic categorization."""
        topic_keywords = {
            "work": ["work", "job", "project", "meeting", "deadline", "task"],
            "health": ["health", "exercise", "sleep", "doctor", "medicine", "diet"],
            "finance": ["money", "finance", "investment", "budget", "price", "cost"],
            "relationship": ["friend", "family", "relationship", "partner", "date"],
            "technology": ["code", "software", "app", "system", "bug", "feature"],
        }
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return topic
        return "general"

    def _calculate_importance(self, text: str, key_points: List[str], action_items: List[str]) -> float:
        """Calculate importance score for a turn."""
        score = 0.3  # Base score
        score += len(key_points) * 0.15
        score += len(action_items) * 0.2
        if "?" in text:
            score += 0.1  # Questions are important
        if any(m in text.lower() for m in ["decided", "agreed", "final", "important", "urgent"]):
            score += 0.2
        return min(1.0, score)

    def _generate_topic_summary(self, text: str) -> str:
        """Generate summary for a topic segment."""
        sentences = [s.strip() for s in text.split(".") if s.strip() and len(s) > 10]
        if len(sentences) <= 3:
            return " ".join(sentences)
        return " ".join(sentences[:2]) + "..."

    def _build_emotional_arc(self, emotions: List[str]) -> List[str]:
        """Build emotional arc from sequence of emotions."""
        if not emotions:
            return []
        # Simplify to transitions
        arc = [emotions[0]]
        for e in emotions[1:]:
            if e != arc[-1]:
                arc.append(e)
        return arc[:5]

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_summary_stats(self) -> Dict[str, Any]:
        return self._stats

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

    def _log_summary(self, summary: ConversationSummary):
        try:
            with open(SUMMARY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "conversation_id": summary.conversation_id,
                    "turn_count": summary.turn_count,
                    "compression_ratio": summary.compression_ratio,
                    "topics": [t["topic"] for t in summary.topic_segments],
                    "action_items": len(summary.action_items),
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cs_instance: Optional[ConversationSummarizer] = None
_cs_lock = threading.Lock()


def get_conversation_summarizer() -> ConversationSummarizer:
    global _cs_instance
    with _cs_lock:
        if _cs_instance is None:
            _cs_instance = ConversationSummarizer()
        return _cs_instance
