"""
LOVE Graph RAG — Knowledge-Graph-Enhanced Retrieval (Modern AI Pattern)

Traditional RAG retrieves documents by semantic similarity. Graph RAG goes
further by:

1. STRUCTURED RETRIEVAL
   - Query the knowledge graph for entities and relationships
   - Find connected concepts that simple vector search would miss
   - Traverse multi-hop relationships (friend-of-friend, cause-effect)

2. SEMANTIC + GRAPH HYBRID
   - Use vector memory for semantic similarity
   - Use knowledge graph for relational reasoning
   - Combine both for richer, more contextual answers

3. EXPLAINABLE PATHS
   - Show the reasoning path: "User mentioned X → X relates to Y → Y connects to Z"
   - Each answer includes the evidence chain
   - Users can verify and correct the reasoning

4. PROACTIVE DISCOVERY
   - Detect when the user is asking about a topic with unexplored connections
   - Suggest related entities the user hasn't mentioned
   - Surface "did you mean?" clarifications based on graph structure

Architecture:
- query_graph(): Query knowledge graph for entities/relations
- semantic_graph_search(): Vector similarity + graph traversal
- explain_path(): Show reasoning chain from query to answer
- suggest_connections(): Proactive related concept suggestions
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "graph_rag"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GRAPH_RAG_LOG = DATA_DIR / "graph_rag_log.jsonl"
QUERY_CACHE = DATA_DIR / "query_cache.json"


@dataclass
class GraphPath:
    """A reasoning path through the knowledge graph."""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    source: str = ""


@dataclass
class GraphRAGResult:
    """Result of a Graph RAG query."""
    answer: str = ""
    entities: List[str] = field(default_factory=list)
    paths: List[GraphPath] = field(default_factory=list)
    semantic_matches: List[Dict] = field(default_factory=list)
    suggested_questions: List[str] = field(default_factory=list)
    confidence: float = 0.0


class GraphRAGEngine:
    """
    Knowledge-graph-enhanced retrieval for LOVE.
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
        self._stats = {"queries": 0, "cache_hits": 0, "graph_lookups": 0, "vector_lookups": 0}
        self._query_cache: Dict[str, Dict] = {}
        self._load_cache()

    # ── Core Query ──────────────────────────────────────────────────────────

    def query(self, question: str, top_k: int = 5) -> GraphRAGResult:
        """
        Answer a question using both knowledge graph and vector memory.
        """
        result = GraphRAGResult()

        # Check cache
        cache_key = question.lower().strip()
        if cache_key in self._query_cache:
            cached = self._query_cache[cache_key]
            if time.time() - cached["timestamp"] < 3600:  # 1 hour cache
                self._stats["cache_hits"] += 1
                return GraphRAGResult(**cached["result"])

        # Step 1: Extract entities from the question
        entities = self._extract_entities(question)
        result.entities = entities

        # Step 2: Query knowledge graph for these entities
        graph_results = []
        for entity in entities:
            graph_results.extend(self._query_knowledge_graph(entity))
        self._stats["graph_lookups"] += len(entities)

        # Step 3: Semantic search in vector memory
        vector_results = self._semantic_search(question, top_k=top_k)
        result.semantic_matches = vector_results
        self._stats["vector_lookups"] += 1

        # Step 4: Build reasoning paths
        paths = self._build_reasoning_paths(entities, graph_results, vector_results)
        result.paths = paths

        # Step 5: Synthesize answer
        if paths:
            result.answer = self._synthesize_answer(question, paths, vector_results)
            result.confidence = max(p.confidence for p in paths)
        elif vector_results:
            result.answer = self._synthesize_from_vectors(question, vector_results)
            result.confidence = 0.6
        else:
            result.answer = "I don't have enough information to answer that confidently."
            result.confidence = 0.0

        # Step 6: Suggest follow-up questions
        result.suggested_questions = self._suggest_questions(entities, graph_results)

        # Cache result
        self._query_cache[cache_key] = {
            "timestamp": time.time(),
            "result": {
                "answer": result.answer,
                "entities": result.entities,
                "paths": [{"steps": p.steps, "confidence": p.confidence, "source": p.source} for p in result.paths],
                "semantic_matches": result.semantic_matches,
                "suggested_questions": result.suggested_questions,
                "confidence": result.confidence,
            }
        }
        self._save_cache()

        self._stats["queries"] += 1
        self._log({
            "event": "query",
            "question": question,
            "entities": entities,
            "confidence": result.confidence,
        })

        return result

    # ── Entity Extraction ───────────────────────────────────────────────────

    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential entities from text using simple heuristics."""
        entities = []
        try:
            from core.knowledge_graph import extract_entities
            entities = extract_entities(text)
        except Exception:
            # Fallback: simple noun extraction
            import re
            # Find capitalized phrases (potential proper nouns)
            entities = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
            # Also find quoted phrases
            quoted = re.findall(r'"([^"]+)"', text)
            entities.extend(quoted)

        # Deduplicate and filter short ones
        seen = set()
        result = []
        for e in entities:
            key = e.lower().strip()
            if key not in seen and len(key) > 2:
                seen.add(key)
                result.append(e)
        return result[:5]  # Limit to top 5

    # ── Knowledge Graph Query ───────────────────────────────────────────────

    def _query_knowledge_graph(self, entity: str) -> List[Dict]:
        """Query the knowledge graph for an entity."""
        results = []
        try:
            from core.knowledge_graph import find_entities, get_relations

            # Find the entity
            matches = find_entities(entity)
            for match in matches:
                # Get relations
                relations = get_relations(match.get("id", match.get("name", "")))
                results.append({
                    "entity": match,
                    "relations": relations,
                })
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.graph_rag")
        return results

    # ── Semantic Search ─────────────────────────────────────────────────────

    def _semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search vector memory for semantically similar content."""
        try:
            from core.vector_memory import get_vector_engine
            engine = get_vector_engine()
            results = engine.search(query, top_k=top_k, threshold=0.5)
            return results
        except Exception:
            return []

    # ── Reasoning Path Builder ──────────────────────────────────────────────

    def _build_reasoning_paths(self, entities: List[str],
                               graph_results: List[Dict],
                               vector_results: List[Dict]) -> List[GraphPath]:
        """Build reasoning paths from query to answers."""
        paths = []

        # Path type 1: Entity -> Relation -> Related Entity
        for gr in graph_results:
            entity = gr.get("entity", {})
            relations = gr.get("relations", [])
            for rel in relations[:3]:  # Top 3 relations
                path = GraphPath(
                    steps=[
                        {"type": "entity", "value": entity.get("name", "")},
                        {"type": "relation", "value": rel.get("type", ""), "target": rel.get("target", "")},
                    ],
                    confidence=rel.get("strength", 0.5),
                    source="knowledge_graph",
                )
                paths.append(path)

        # Path type 2: Query -> Vector Match -> Relevant Memory
        for vr in vector_results[:2]:
            path = GraphPath(
                steps=[
                    {"type": "query", "value": "semantic search"},
                    {"type": "memory", "value": vr.get("text", "")[:100], "source": vr.get("source", "")},
                ],
                confidence=vr.get("similarity", 0.5),
                source="vector_memory",
            )
            paths.append(path)

        # Sort by confidence
        paths.sort(key=lambda p: p.confidence, reverse=True)
        return paths[:5]

    # ── Answer Synthesis ────────────────────────────────────────────────────

    def _synthesize_answer(self, question: str, paths: List[GraphPath],
                           vector_results: List[Dict]) -> str:
        """Synthesize a natural language answer from reasoning paths."""
        parts = []

        # Include knowledge graph paths
        kg_paths = [p for p in paths if p.source == "knowledge_graph"]
        if kg_paths:
            parts.append("Based on what I know:")
            for path in kg_paths[:3]:
                entity = path.steps[0]["value"] if path.steps else ""
                relation = path.steps[1] if len(path.steps) > 1 else {}
                rel_type = relation.get("value", "")
                target = relation.get("target", "")
                if entity and rel_type and target:
                    parts.append(f"  - {entity} {rel_type} {target}")

        # Include vector memory context
        if vector_results:
            parts.append("\nFrom our conversations:")
            for vr in vector_results[:2]:
                text = vr.get("text", "")
                if text:
                    parts.append(f"  - {text[:150]}...")

        return "\n".join(parts)

    def _synthesize_from_vectors(self, question: str,
                                 vector_results: List[Dict]) -> str:
        """Synthesize answer from vector results only."""
        if not vector_results:
            return ""
        parts = ["Based on similar past conversations:"]
        for vr in vector_results[:3]:
            text = vr.get("text", "")
            if text:
                parts.append(f"  - {text[:200]}")
        return "\n".join(parts)

    # ── Proactive Suggestions ───────────────────────────────────────────────

    def _suggest_questions(self, entities: List[str],
                           graph_results: List[Dict]) -> List[str]:
        """Suggest follow-up questions based on graph connections."""
        suggestions = []

        # Find related entities not mentioned
        mentioned = set(e.lower() for e in entities)
        for gr in graph_results:
            relations = gr.get("relations", [])
            for rel in relations:
                target = rel.get("target", "")
                if target and target.lower() not in mentioned:
                    suggestions.append(f"Tell me more about {target}")
                    break
            if suggestions:
                break

        # Suggest exploring relations
        if graph_results:
            suggestions.append("How do these relate to each other?")

        return suggestions[:3]

    # ── Statistics ───────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "cache_size": len(self._query_cache),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(GRAPH_RAG_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.graph_rag")

    def _save_cache(self):
        try:
            data = {k: v for k, v in self._query_cache.items()}
            QUERY_CACHE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.graph_rag")

    def _load_cache(self):
        try:
            if QUERY_CACHE.exists():
                data = json.loads(QUERY_CACHE.read_text())
                self._query_cache = data
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.graph_rag")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_graph_rag_instance: Optional[GraphRAGEngine] = None
_graph_rag_lock = threading.Lock()


def get_graph_rag_engine() -> GraphRAGEngine:
    global _graph_rag_instance
    with _graph_rag_lock:
        if _graph_rag_instance is None:
            _graph_rag_instance = GraphRAGEngine()
        return _graph_rag_instance
