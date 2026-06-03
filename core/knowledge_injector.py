"""
LOVE Proactive Knowledge Injector — Contextual Knowledge Delivery (Modern AI Pattern)

When users converse, relevant knowledge from memory, knowledge graph, and
external sources can enrich the conversation. This injector:

1. CONTEXTUAL KNOWLEDGE MATCHING
   - Match conversation topics with stored knowledge
   - Identify knowledge gaps in the current conversation
   - Suggest relevant facts, memories, or documents

2. PROACTIVE INJECTION
   - Inject knowledge before user explicitly asks
   - Surface related past conversations on similar topics
   - Suggest relevant external resources

3. RELEVANCE SCORING
   - Score knowledge items by topical relevance
   - Weight by recency and user engagement
   - Filter out redundant or obvious information

4. CONVERSATION ENRICHMENT
   - Enrich user messages with context from knowledge base
   - Provide background information for complex topics
   - Connect current conversation to related past discussions

Architecture:
- inject_knowledge(text, context): Propose knowledge to inject
- score_relevance(knowledge, context): Score knowledge relevance
- get_injection_stats(): Track injection effectiveness
"""

import json
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "knowledge_injector"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INJECTION_LOG = DATA_DIR / "injection_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class KnowledgeItem:
    """A piece of knowledge ready for injection."""
    id: str = ""
    source: str = ""  # memory, graph, document, external
    content: str = ""
    relevance_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InjectionProposal:
    """A proposed knowledge injection."""
    trigger_text: str = ""
    knowledge_items: List[KnowledgeItem] = field(default_factory=list)
    insertion_point: str = "before_response"  # or "after_response"
    confidence: float = 0.5


class KnowledgeInjector:
    """
    Proactively inject relevant knowledge into conversations.
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
            "total_injections": 0,
            "accepted": 0,
            "rejected": 0,
            "avg_relevance": 0.0,
        }
        self._feedback_window: deque = deque(maxlen=100)
        self._load_stats()

    # ── Core Injection ────────────────────────────────────────────────────

    def inject_knowledge(self, text: str, context: Optional[List[str]] = None) -> InjectionProposal:
        """Propose knowledge to inject into the conversation."""
        if context is None:
            context = []

        # Extract topics from text
        topics = self._extract_topics(text)

        # Search for relevant knowledge (simplified — would query vector memory + graph)
        knowledge_items = []

        # Simulate knowledge retrieval from different sources
        for topic in topics:
            # From memory
            knowledge_items.append(KnowledgeItem(
                id=f"mem_{topic}_{int(time.time())}",
                source="memory",
                content=f"Previous discussion about {topic}: ...",
                relevance_score=0.7,
                metadata={"topic": topic, "source_type": "conversation_memory"},
            ))

            # From knowledge graph
            knowledge_items.append(KnowledgeItem(
                id=f"kg_{topic}_{int(time.time())}",
                source="graph",
                content=f"Knowledge graph entry for {topic}: ...",
                relevance_score=0.6,
                metadata={"topic": topic, "source_type": "knowledge_graph"},
            ))

        # Score and filter
        scored_items = []
        for item in knowledge_items:
            item.relevance_score = self._score_relevance(item, text, context)
            if item.relevance_score > 0.5:
                scored_items.append(item)

        scored_items.sort(key=lambda x: x.relevance_score, reverse=True)

        proposal = InjectionProposal(
            trigger_text=text[:100],
            knowledge_items=scored_items[:3],  # Top 3 items
            confidence=round(sum(i.relevance_score for i in scored_items[:3]) / max(1, len(scored_items[:3])), 2),
        )

        with self._lock:
            self._stats["total_injections"] += 1

        self._save_stats()
        self._log_injection(proposal)

        return proposal

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        # Simple extraction — would use NLP in production
        words = text.lower().split()
        # Filter for potential topics (nouns, longer words)
        topics = [w.strip(".,!?;:") for w in words if len(w) > 4 and w[0].islower()]
        return list(set(topics))[:5]  # Max 5 topics

    def _score_relevance(self, item: KnowledgeItem, text: str, context: List[str]) -> float:
        """Score relevance of a knowledge item."""
        text_words = set(text.lower().split())
        item_words = set(item.content.lower().split())

        # Jaccard similarity
        intersection = len(text_words & item_words)
        union = len(text_words | item_words)
        base_score = intersection / max(1, union)

        # Boost for recent items
        try:
            item_time = datetime.fromisoformat(item.timestamp)
            age_hours = (datetime.now() - item_time).total_seconds() / 3600
            recency_boost = math.exp(-age_hours / 168)  # Decay over 1 week
        except Exception:
            recency_boost = 0.5

        # Boost for memory sources
        source_boost = 1.2 if item.source == "memory" else 1.0

        return min(1.0, base_score * 0.6 + recency_boost * 0.3 + (source_boost - 1) * 0.1)

    # ── Feedback ──────────────────────────────────────────────────────────

    def record_injection_feedback(self, injection_id: str, accepted: bool):
        """Record whether user found the injection helpful."""
        if accepted:
            self._stats["accepted"] += 1
        else:
            self._stats["rejected"] += 1

        self._feedback_window.append({
            "injection_id": injection_id,
            "accepted": accepted,
            "timestamp": datetime.now().isoformat(),
        })

        self._save_stats()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_injection_stats(self) -> Dict[str, Any]:
        total = self._stats["total_injections"]
        accepted = self._stats["accepted"]
        return {
            **self._stats,
            "acceptance_rate": round(accepted / max(1, total), 2),
            "recent_feedback": list(self._feedback_window)[-10:],
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.knowledge_injector")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.knowledge_injector")

    def _log_injection(self, proposal: InjectionProposal):
        try:
            with open(INJECTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "trigger": proposal.trigger_text[:100],
                    "items_count": len(proposal.knowledge_items),
                    "confidence": proposal.confidence,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.knowledge_injector")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ki_instance: Optional[KnowledgeInjector] = None
_ki_lock = threading.Lock()


def get_knowledge_injector() -> KnowledgeInjector:
    global _ki_instance
    with _ki_lock:
        if _ki_instance is None:
            _ki_instance = KnowledgeInjector()
        return _ki_instance
