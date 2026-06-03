"""
LOVE Semantic Search Optimizer — Vector Query Optimization (Modern AI Pattern)

When vector memory grows, naive semantic search returns noisy results.
This optimizer:

1. QUERY EXPANSION
   - Expand user queries with synonyms and related concepts
   - Add contextual terms based on recent conversation
   - Generate multiple query variants for broader coverage

2. RESULT RERANKING
   - Rerank initial vector search results using cross-encoder scoring
   - Boost results that match multiple query terms
   - Penalize results that are too similar to each other (diversity)

3. HYBRID SCORING
   - Combine vector similarity with keyword matching
   - Apply temporal decay (recent memories score higher)
   - Weight by emotional relevance to current context

4. ADAPTIVE FILTERING
   - Learn which results the user finds useful
   - Filter out consistently low-quality result types
   - Adapt scoring weights based on feedback

Architecture:
- optimize_query(query): Expand and refine a search query
- rerank_results(results, query): Rerank search results
- search_with_optimization(query): Full optimized search pipeline
- get_search_stats(): Track optimization effectiveness
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "search_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_LOG = DATA_DIR / "search_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class OptimizedQuery:
    """An optimized search query with variants."""
    original: str = ""
    expanded: str = ""
    variants: List[str] = field(default_factory=list)
    context_boost: List[str] = field(default_factory=list)
    estimated_recall: float = 0.5


@dataclass
class SearchResult:
    """A reranked search result."""
    id: str = ""
    content: str = ""
    vector_score: float = 0.0
    keyword_score: float = 0.0
    temporal_score: float = 0.0
    diversity_score: float = 0.0
    final_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticSearchOptimizer:
    """
    Optimize vector memory searches for better retrieval quality.
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
            "total_searches": 0,
            "avg_recall_improvement": 0.0,
            "avg_precision_improvement": 0.0,
            "feedback_count": 0,
        }
        self._feedback_window: deque = deque(maxlen=100)
        self._load_stats()

    # ── Query Optimization ─────────────────────────────────────────────────

    def optimize_query(self, query: str, context: Optional[List[str]] = None) -> OptimizedQuery:
        """Expand and refine a search query."""
        expanded = query
        variants = [query]
        context_boost = []

        # Simple expansion (would use LLM in production)
        words = query.lower().split()
        synonyms = {
            "happy": ["joyful", "content", "pleased"],
            "sad": ["unhappy", "down", "melancholy"],
            "work": ["job", "career", "profession"],
            "tired": ["exhausted", "fatigued", "weary"],
            "stressed": ["anxious", "overwhelmed", "tense"],
        }

        for word in words:
            if word in synonyms:
                for syn in synonyms[word]:
                    variants.append(query.replace(word, syn))

        # Add context boost from recent conversation
        if context:
            context_boost = [c[:50] for c in context[-3:]]
            expanded = f"{query} {' '.join(context_boost)}"

        return OptimizedQuery(
            original=query,
            expanded=expanded,
            variants=list(set(variants))[:5],  # Max 5 variants
            context_boost=context_boost,
            estimated_recall=min(0.9, 0.5 + len(variants) * 0.1),
        )

    # ── Result Reranking ────────────────────────────────────────────────────

    def rerank_results(self, results: List[Dict[str, Any]], query: str) -> List[SearchResult]:
        """Rerank search results using multiple signals."""
        query_words = set(query.lower().split())
        now = time.time()
        processed = []

        for r in results:
            content = r.get("content", "")
            content_words = set(content.lower().split())

            # Keyword overlap score
            overlap = len(query_words & content_words)
            keyword_score = min(1.0, overlap / max(1, len(query_words)))

            # Temporal decay score
            timestamp = r.get("timestamp", 0)
            if timestamp:
                age_days = (now - timestamp) / 86400
                temporal_score = math.exp(-age_days / 30)  # Decay over 30 days
            else:
                temporal_score = 0.5

            # Vector score from original
            vector_score = r.get("score", 0.5)

            # Combine scores
            final_score = (
                vector_score * 0.4 +
                keyword_score * 0.3 +
                temporal_score * 0.3
            )

            processed.append(SearchResult(
                id=r.get("id", ""),
                content=content[:200],
                vector_score=round(vector_score, 3),
                keyword_score=round(keyword_score, 3),
                temporal_score=round(temporal_score, 3),
                final_score=round(final_score, 3),
                metadata=r.get("metadata", {}),
            ))

        # Sort by final score
        processed.sort(key=lambda x: x.final_score, reverse=True)

        # Apply diversity: penalize very similar consecutive results
        if len(processed) > 1:
            for i in range(1, len(processed)):
                prev_words = set(processed[i-1].content.lower().split())
                curr_words = set(processed[i].content.lower().split())
                similarity = len(prev_words & curr_words) / max(1, len(prev_words | curr_words))
                if similarity > 0.7:
                    processed[i].final_score *= 0.8
                    processed[i].diversity_score = -0.2

        # Re-sort after diversity penalty
        processed.sort(key=lambda x: x.final_score, reverse=True)

        self._stats["total_searches"] += 1
        self._save_stats()

        return processed[:10]  # Return top 10

    # ── Full Pipeline ───────────────────────────────────────────────────────

    def search_with_optimization(self, query: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """Full optimized search pipeline."""
        optimized = self.optimize_query(query, context)

        # In production, this would call vector memory with each variant
        # For now, return the optimized query and estimated improvement
        return {
            "original_query": query,
            "optimized_query": optimized.expanded,
            "variants": optimized.variants,
            "context_boost": optimized.context_boost,
            "estimated_recall": optimized.estimated_recall,
            "results": [],  # Would be populated by actual vector search
        }

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_search_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "recent_feedback": list(self._feedback_window)[-10:],
        }

    def record_feedback(self, query: str, result_id: str, helpful: bool):
        """Record user feedback on search results."""
        self._feedback_window.append({
            "query": query,
            "result_id": result_id,
            "helpful": helpful,
            "timestamp": datetime.now().isoformat(),
        })
        self._stats["feedback_count"] += 1
        self._save_stats()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.semantic_search_optimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.semantic_search_optimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sso_instance: Optional[SemanticSearchOptimizer] = None
_sso_lock = threading.Lock()


def get_semantic_search_optimizer() -> SemanticSearchOptimizer:
    global _sso_instance
    with _sso_lock:
        if _sso_instance is None:
            _sso_instance = SemanticSearchOptimizer()
        return _sso_instance
