"""
LOVE Temporal Memory — Autobiographical Memory System

Unlike ChromaDB vector search (which retrieves by similarity),
Temporal Memory gives LOVE a sense of TIME and NARRATIVE.

Capabilities:
1. Episodic Timeline — "What happened last Tuesday at 3pm?"
2. Emotional Anchoring — Important memories are weighted by emotion
3. Memory Decay — Unimportant memories fade, significant ones strengthen
4. Narrative Threading — Connects related memories across time
5. Déjà Vu Detection — "This situation feels familiar..."
6. Memory Consolidation — During "sleep", compress and integrate memories
7. Forgetting Curve — Realistic memory fading with spaced reinforcement

This answers: "What do I remember about this moment in time?"
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import threading
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
TEMPORAL_FILE = DATA_DIR / "temporal_memory.json"
NARRATIVE_FILE = DATA_DIR / "narrative_threads.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TemporalMemory:
    """A single memory with temporal and emotional context."""
    id: str
    timestamp: str
    content: str                           # What happened
    category: str                          # conversation, event, insight, milestone
    emotional_valence: float = 0.0         # -1 to +1
    emotional_intensity: float = 0.0       # 0 to 1
    importance: float = 0.5                # 0 to 1, decays over time
    initial_importance: float = 0.5        # Original importance (never changes)
    access_count: int = 0                  # How many times recalled
    last_accessed: Optional[str] = None
    related_memories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)  # Time of day, user mood, etc.
    narrative_thread: Optional[str] = None  # Which ongoing story this belongs to


@dataclass
class NarrativeThread:
    """An ongoing story or theme in LOVE's experience."""
    id: str
    title: str                              # "Karthi's burnout recovery"
    description: str
    started_at: str
    last_updated: str
    memory_ids: List[str] = field(default_factory=list)
    status: str = "active"                  # active, resolved, dormant
    emotional_arc: List[float] = field(default_factory=list)  # Valence over time


class TemporalMemoryEngine:
    """
    Autobiographical memory system with realistic temporal dynamics.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.memories: Dict[str, TemporalMemory] = {}
        self.narratives: Dict[str, NarrativeThread] = {}
        self._load()

    # ── Core Operations ──────────────────────────────────────────────────────

    def remember(self, content: str, category: str = "conversation",
                 emotional_valence: float = 0.0, emotional_intensity: float = 0.0,
                 importance: float = 0.5, tags: List[str] = None,
                 context: Dict[str, Any] = None) -> str:
        """Store a new temporal memory."""
        mem_id = f"tmem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.memories)}"

        memory = TemporalMemory(
            id=mem_id,
            timestamp=datetime.now().isoformat(),
            content=content,
            category=category,
            emotional_valence=emotional_valence,
            emotional_intensity=emotional_intensity,
            importance=importance,
            initial_importance=importance,
            tags=tags or [],
            context=context or {"hour": datetime.now().hour, "day": datetime.now().strftime("%A")},
        )

        with self._lock:
            self.memories[mem_id] = memory
            self._save()

        # Try to attach to a narrative thread
        self._auto_thread(memory)

        return mem_id

    def recall_by_time(self, start: datetime, end: datetime = None,
                       limit: int = 20) -> List[TemporalMemory]:
        """Recall memories from a specific time range."""
        end = end or datetime.now()
        results = []

        for mem in self.memories.values():
            try:
                mem_time = datetime.fromisoformat(mem.timestamp)
                if start <= mem_time <= end:
                    # Apply forgetting curve
                    mem.importance = self._apply_decay(mem)
                    mem.access_count += 1
                    mem.last_accessed = datetime.now().isoformat()
                    results.append(mem)
            except Exception:
                pass

        # Sort by importance (most important first)
        results.sort(key=lambda m: m.importance, reverse=True)
        self._save()
        return results[:limit]

    def recall_by_emotion(self, valence_range: Tuple[float, float] = (-1, 1),
                          min_intensity: float = 0.3,
                          limit: int = 10) -> List[TemporalMemory]:
        """Recall emotionally significant memories."""
        results = []
        for mem in self.memories.values():
            if (valence_range[0] <= mem.emotional_valence <= valence_range[1] and
                    mem.emotional_intensity >= min_intensity):
                results.append(mem)

        results.sort(key=lambda m: m.emotional_intensity, reverse=True)
        return results[:limit]

    def deja_vu(self, current_context: str, threshold: float = 0.6) -> Optional[TemporalMemory]:
        """
        Check if the current situation feels familiar.
        Returns the most similar past memory if found.
        """
        current_words = set(current_context.lower().split())

        best_match = None
        best_score = 0

        for mem in self.memories.values():
            mem_words = set(mem.content.lower().split())
            if not mem_words:
                continue

            # Jaccard similarity
            intersection = current_words & mem_words
            union = current_words | mem_words
            similarity = len(intersection) / len(union) if union else 0

            # Boost by emotional intensity (emotional memories are stickier)
            boosted_score = similarity * (1 + mem.emotional_intensity * 0.3)

            if boosted_score > best_score and boosted_score >= threshold:
                best_score = boosted_score
                best_match = mem

        return best_match

    # ── Forgetting Curve ─────────────────────────────────────────────────────

    def _apply_decay(self, memory: TemporalMemory) -> float:
        """
        Apply Ebbinghaus forgetting curve with emotional anchoring.
        
        Emotionally intense memories decay MUCH slower.
        Frequently accessed memories decay slower (spaced repetition).
        """
        try:
            created = datetime.fromisoformat(memory.timestamp)
            hours_elapsed = (datetime.now() - created).total_seconds() / 3600

            # Base decay: importance = initial * e^(-decay_rate * time)
            base_decay_rate = 0.01  # Slow decay

            # Emotional anchoring — strong emotions resist decay
            emotional_anchor = 1 - (memory.emotional_intensity * 0.8)
            effective_decay = base_decay_rate * emotional_anchor

            # Spaced repetition — each access resets some decay
            repetition_bonus = math.log(1 + memory.access_count) * 0.1

            new_importance = memory.initial_importance * math.exp(
                -effective_decay * hours_elapsed
            ) + repetition_bonus

            return max(0.01, min(1.0, new_importance))

        except Exception:
            return memory.importance

    def consolidate(self):
        """
        Memory consolidation — "sleep" process.
        - Strengthen important/emotional memories
        - Let trivial memories decay
        - Merge related memories into narratives
        """
        consolidated = 0
        decayed = 0

        for mem_id, mem in list(self.memories.items()):
            new_importance = self._apply_decay(mem)
            mem.importance = new_importance

            if new_importance < 0.05 and mem.emotional_intensity < 0.2:
                # Memory has faded — archive it
                del self.memories[mem_id]
                decayed += 1
            elif new_importance > mem.initial_importance * 0.8:
                consolidated += 1

        self._save()
        return {"consolidated": consolidated, "decayed": decayed, "remaining": len(self.memories)}

    # ── Narrative Threading ──────────────────────────────────────────────────

    def _auto_thread(self, memory: TemporalMemory):
        """Automatically attach a memory to an ongoing narrative thread."""
        for thread in self.narratives.values():
            if thread.status != "active":
                continue

            # Check tag overlap
            if memory.tags and any(tag in thread.title.lower() for tag in memory.tags):
                thread.memory_ids.append(memory.id)
                thread.last_updated = datetime.now().isoformat()
                thread.emotional_arc.append(memory.emotional_valence)
                memory.narrative_thread = thread.id
                self._save()
                return

    def create_narrative(self, title: str, description: str,
                         initial_memory_id: str = None) -> str:
        """Create a new narrative thread."""
        thread_id = f"narrative_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        thread = NarrativeThread(
            id=thread_id,
            title=title,
            description=description,
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            memory_ids=[initial_memory_id] if initial_memory_id else [],
        )
        self.narratives[thread_id] = thread
        self._save()
        return thread_id

    def get_active_narratives(self) -> List[Dict]:
        """Get all active narrative threads with summaries."""
        return [
            {
                "id": n.id,
                "title": n.title,
                "description": n.description,
                "memory_count": len(n.memory_ids),
                "emotional_arc": n.emotional_arc[-10:],
                "started_at": n.started_at,
                "last_updated": n.last_updated,
            }
            for n in self.narratives.values()
            if n.status == "active"
        ]

    # ── Context for Prompt Injection ─────────────────────────────────────────

    def get_temporal_context(self, query: str = "", limit: int = 5) -> str:
        """Get temporal memory context for injection into LLM prompt."""
        parts = []

        # Recent memories (last 24 hours)
        recent = self.recall_by_time(
            start=datetime.now() - timedelta(hours=24),
            limit=3
        )
        if recent:
            parts.append("RECENT MEMORIES (last 24h):")
            for mem in recent:
                parts.append(f"  [{mem.timestamp[:16]}] {mem.content[:120]}")

        # Déjà vu check
        if query:
            similar = self.deja_vu(query, threshold=0.4)
            if similar:
                parts.append(f"\nDÉJÀ VU: This reminds me of [{similar.timestamp[:10]}]: {similar.content[:100]}")

        # Active narratives
        narratives = self.get_active_narratives()
        if narratives:
            parts.append(f"\nONGOING STORIES: {', '.join(n['title'] for n in narratives[:3])}")

        # Emotionally significant memories
        emotional = self.recall_by_emotion(min_intensity=0.7, limit=2)
        if emotional:
            parts.append("\nSTRONG MEMORIES:")
            for mem in emotional:
                parts.append(f"  [{mem.timestamp[:10]}] {mem.content[:100]} (intensity: {mem.emotional_intensity})")

        return "\n".join(parts) if parts else ""

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self):
        try:
            if TEMPORAL_FILE.exists():
                with open(TEMPORAL_FILE, 'r') as f:
                    data = json.load(f)
                for mid, mdata in data.get("memories", {}).items():
                    self.memories[mid] = TemporalMemory(**mdata)
            if NARRATIVE_FILE.exists():
                with open(NARRATIVE_FILE, 'r') as f:
                    data = json.load(f)
                for nid, ndata in data.get("narratives", {}).items():
                    self.narratives[nid] = NarrativeThread(**ndata)
        except Exception as e:
            print(f"[TemporalMemory] Load error: {e}")

    def _save(self):
        with self._lock:
            try:
                with open(TEMPORAL_FILE, 'w') as f:
                    json.dump({
                        "memories": {
                            mid: {
                                "id": m.id, "timestamp": m.timestamp, "content": m.content,
                                "category": m.category, "emotional_valence": m.emotional_valence,
                                "emotional_intensity": m.emotional_intensity,
                                "importance": m.importance, "initial_importance": m.initial_importance,
                                "access_count": m.access_count, "last_accessed": m.last_accessed,
                                "related_memories": m.related_memories, "tags": m.tags,
                                "context": m.context, "narrative_thread": m.narrative_thread,
                            }
                            for mid, m in self.memories.items()
                        }
                    }, f, indent=2)
                with open(NARRATIVE_FILE, 'w') as f:
                    json.dump({
                        "narratives": {
                            nid: {
                                "id": n.id, "title": n.title, "description": n.description,
                                "started_at": n.started_at, "last_updated": n.last_updated,
                                "memory_ids": n.memory_ids, "status": n.status,
                                "emotional_arc": n.emotional_arc,
                            }
                            for nid, n in self.narratives.items()
                        }
                    }, f, indent=2)
            except Exception as e:
                print(f"[TemporalMemory] Save error: {e}")


# Singleton
_engine: Optional[TemporalMemoryEngine] = None
_lock = threading.Lock()

def get_temporal_memory() -> TemporalMemoryEngine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = TemporalMemoryEngine()
    return _engine
