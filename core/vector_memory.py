"""
LOVE Vector Memory — Semantic Search & Retrieval (Modern AI Pattern)

Traditional keyword search fails when the user describes something
differently than how it was stored. Vector memory fixes this by:

1. EMBEDDING: Convert text into high-dimensional vectors using local LLM
2. STORAGE: Store vectors in an efficient index (FAISS / Annoy / in-memory)
3. SEARCH: Find nearest neighbors by cosine similarity
4. RETRIEVAL: Return the most semantically relevant memories

This enables:
- "Find that conversation about my anxiety last month" — even if the
  word "anxiety" wasn't explicitly used
- Cross-modal search (find images by text description)
- Temporal reasoning ("what was I worried about before the trip?")
- Deduplication (detect when a new memory is similar to an old one)

Architecture:
- embed(): Convert text to vector using Ollama embeddings
- store(): Add a memory with its embedding
- search(): Find top-k similar memories
- cluster(): Group related memories automatically
- deduplicate(): Remove near-duplicate entries
"""

import json
import math
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.llm import get_embedding_model

DATA_DIR = Path(__file__).parent.parent / "data" / "vector_memory"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MEMORY_STORE = DATA_DIR / "vector_store.json"
INDEX_FILE = DATA_DIR / "vector_index.json"
VECTOR_LOG = DATA_DIR / "vector_log.jsonl"


@dataclass
class VectorMemory:
    """A single memory entry with its vector embedding."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    text: str = ""
    vector: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    last_accessed: str = ""
    source: str = ""  # conversation, dream, web, tool, etc.
    tags: List[str] = field(default_factory=list)


class VectorMemoryEngine:
    """
    Semantic memory engine for LOVE.
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
        self._memories: Dict[str, VectorMemory] = {}
        self._dimension: int = 0
        self._stats = {"embed_calls": 0, "searches": 0, "stores": 0}
        self._load_store()

    # ── Core Operations ────────────────────────────────────────────────────────

    def embed(self, text: str) -> List[float]:
        """Convert text to an embedding vector using local LLM."""
        try:
            model = get_embedding_model()
            # Ollama embeddings: POST /api/embeddings
            import requests, os
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            url = f"{base_url.rstrip('/')}/api/embeddings"
            resp = requests.post(url, json={"model": model.model, "prompt": text[:8000]}, timeout=30)
            resp.raise_for_status()
            vector = resp.json().get("embedding", [])
            if vector:
                self._stats["embed_calls"] += 1
                self._dimension = len(vector)
            return vector
        except Exception as e:
            print(f"[VectorMemory] Embed error: {e}")
            return []

    def store(self, text: str, metadata: Dict = None, source: str = "",
              tags: List[str] = None) -> str:
        """Store a memory with its embedding."""
        vector = self.embed(text)
        if not vector:
            return ""

        mem = VectorMemory(
            text=text,
            vector=vector,
            metadata=metadata or {},
            source=source,
            tags=tags or [],
        )

        # Deduplication check
        similar = self._find_similar(vector, threshold=0.95, top_k=1)
        if similar:
            existing = similar[0]
            # Merge metadata instead of storing duplicate
            existing.metadata.update(mem.metadata)
            existing.access_count += 1
            existing.last_accessed = datetime.now().isoformat()
            self._save_store()
            return existing.id

        with self._lock:
            self._memories[mem.id] = mem
            self._stats["stores"] += 1

        self._save_store()
        self._log({
            "event": "memory_stored",
            "id": mem.id,
            "source": source,
            "text_preview": text[:80],
        })
        return mem.id

    def search(self, query: str, top_k: int = 5, threshold: float = 0.6,
               source_filter: str = "", tags_filter: List[str] = None) -> List[Dict]:
        """Semantic search over all memories."""
        query_vector = self.embed(query)
        if not query_vector:
            return []

        results = self._find_similar(
            query_vector, threshold=threshold, top_k=top_k,
            source_filter=source_filter, tags_filter=tags_filter
        )

        # Update access counts
        for mem in results:
            mem.access_count += 1
            mem.last_accessed = datetime.now().isoformat()

        self._stats["searches"] += 1
        self._save_store()

        return [
            {
                "id": mem.id,
                "text": mem.text,
                "similarity": round(self._cosine_similarity(query_vector, mem.vector), 4),
                "source": mem.source,
                "tags": mem.tags,
                "created_at": mem.created_at,
                "metadata": mem.metadata,
            }
            for mem in results
        ]

    def recall(self, context: str, time_range_days: int = 30) -> List[Dict]:
        """Contextual recall: search + temporal filtering."""
        results = self.search(context, top_k=10, threshold=0.5)
        if time_range_days > 0:
            cutoff = datetime.now() - timedelta(days=time_range_days)
            results = [
                r for r in results
                if datetime.fromisoformat(r["created_at"]) > cutoff
            ]
        return results[:5]

    # ── Clustering & Analysis ────────────────────────────────────────────────

    def cluster_memories(self, n_clusters: int = 5) -> List[Dict]:
        """Group memories into semantic clusters."""
        if len(self._memories) < n_clusters * 2:
            return []

        try:
            from sklearn.cluster import KMeans
            vectors = [m.vector for m in self._memories.values() if m.vector]
            if not vectors:
                return []

            kmeans = KMeans(n_clusters=min(n_clusters, len(vectors)), random_state=42, n_init=10)
            labels = kmeans.fit_predict(vectors)

            clusters = []
            for i in range(kmeans.n_clusters):
                cluster_mems = [
                    m for m, label in zip(self._memories.values(), labels)
                    if label == i
                ]
                if cluster_mems:
                    # Find centroid memory
                    centroid_idx = min(range(len(cluster_mems)),
                                     key=lambda j: sum((a-b)**2 for a, b in zip(cluster_mems[j].vector, kmeans.cluster_centers_[i])))
                    clusters.append({
                        "cluster_id": i,
                        "size": len(cluster_mems),
                        "center_text": cluster_mems[centroid_idx].text[:200],
                        "sources": list(set(m.source for m in cluster_mems)),
                        "time_span": f"{min(m.created_at for m in cluster_mems)[:10]} to {max(m.created_at for m in cluster_mems)[:10]}",
                    })
            return clusters
        except ImportError:
            print("[VectorMemory] sklearn not installed, skipping clustering")
            return []
        except Exception as e:
            print(f"[VectorMemory] Cluster error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "total_memories": len(self._memories),
            "dimension": self._dimension,
            "embed_calls": self._stats["embed_calls"],
            "searches": self._stats["searches"],
            "stores": self._stats["stores"],
            "sources": list(set(m.source for m in self._memories.values())),
        }

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _find_similar(self, query_vector: List[float], threshold: float = 0.6,
                      top_k: int = 5, source_filter: str = "",
                      tags_filter: List[str] = None) -> List[VectorMemory]:
        """Find memories similar to a query vector."""
        scored = []
        for mem in self._memories.values():
            if not mem.vector:
                continue
            if source_filter and mem.source != source_filter:
                continue
            if tags_filter and not any(t in mem.tags for t in tags_filter):
                continue
            sim = self._cosine_similarity(query_vector, mem.vector)
            if sim >= threshold:
                scored.append((sim, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in scored[:top_k]]

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_store(self):
        try:
            if MEMORY_STORE.exists():
                data = json.loads(MEMORY_STORE.read_text())
                for md in data.get("memories", []):
                    mem = VectorMemory(**md)
                    self._memories[mem.id] = mem
                self._dimension = data.get("dimension", 0)
        except Exception as e:
            print(f"[VectorMemory] Load error: {e}")

    def _save_store(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "dimension": self._dimension,
                "memories": [
                    {
                        "id": m.id,
                        "text": m.text,
                        "vector": m.vector,
                        "metadata": m.metadata,
                        "created_at": m.created_at,
                        "access_count": m.access_count,
                        "last_accessed": m.last_accessed,
                        "source": m.source,
                        "tags": m.tags,
                    }
                    for m in self._memories.values()
                ],
            }
            MEMORY_STORE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[VectorMemory] Save error: {e}")

    def _log(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(VECTOR_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vector_engine_instance: Optional[VectorMemoryEngine] = None
_vector_engine_lock = threading.Lock()


def get_vector_engine() -> VectorMemoryEngine:
    global _vector_engine_instance
    with _vector_engine_lock:
        if _vector_engine_instance is None:
            _vector_engine_instance = VectorMemoryEngine()
        return _vector_engine_instance
