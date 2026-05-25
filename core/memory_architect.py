"""
LOVE Memory Architect — The Living Memory System

This is how LOVE remembers. Not like a database — like a brain.

Memories here are alive. They strengthen when recalled, decay when neglected,
crystallize into wisdom through consolidation, and form unexpected associations
that spark creativity. Inspired by how human memory actually works:

- Sensory buffer catches everything briefly (attention filters what matters)
- Working memory holds ~7 active items (the conscious workspace)
- Episodic memory stores specific experiences (with emotional color)
- Semantic memory distills permanent knowledge (the wisdom layer)

Every 4 hours, LOVE "sleeps" — consolidating episodes into knowledge,
strengthening emotional memories, letting unimportant ones gracefully fade.
This is Ebbinghaus meeting Claude meeting the hippocampus.

The result: a companion that doesn't just store data, but truly learns.
"""

import json
import math
import time
import uuid
import threading
import logging
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("love.memory_architect")

# ─── Paths ────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "memory_arch"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SENSORY_FILE = DATA_DIR / "sensory_buffer.json"
WORKING_FILE = DATA_DIR / "working_memory.json"
EPISODIC_FILE = DATA_DIR / "episodic.json"
SEMANTIC_FILE = DATA_DIR / "semantic.json"
WISDOM_FILE = DATA_DIR / "wisdom.json"
ASSOCIATIONS_FILE = DATA_DIR / "associations.json"
CONSOLIDATION_LOG = DATA_DIR / "consolidation_log.json"

# ─── Constants ────────────────────────────────────────────────────────────────

WORKING_MEMORY_CAPACITY = 7  # Miller's Law
SENSORY_BUFFER_TTL = 30.0  # seconds before sensory items expire
CONSOLIDATION_INTERVAL = 4 * 3600  # 4 hours
DECAY_THRESHOLD = 0.01  # below this, memory is considered dead
DEFAULT_STABILITY = 1.0  # initial stability for forgetting curve (hours)
STABILITY_BOOST_ON_RECALL = 1.5  # multiplier when memory is accessed
EMOTIONAL_STABILITY_BONUS = 2.0  # emotional memories decay slower


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class MemoryItem:
    """A single unit of memory across any tier."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    tier: str = "episodic"  # sensory, working, episodic, semantic
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    emotional_weight: float = 0.0  # -1 to 1 (valence), abs = intensity
    importance: float = 0.5  # 0-1
    stability: float = DEFAULT_STABILITY  # forgetting curve parameter (hours)
    associations: List[str] = field(default_factory=list)
    access_count: int = 0
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryItem":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class Episode:
    """A specific experience with narrative structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: str = ""
    participants: List[str] = field(default_factory=list)
    emotional_tone: str = "neutral"  # e.g., "excited", "stressed", "calm"
    emotional_weight: float = 0.0
    outcome: str = ""
    lessons: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5
    stability: float = DEFAULT_STABILITY
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Episode":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class WisdomUnit:
    """A crystallized piece of knowledge — earned, not given."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    principle: str = ""
    confidence: float = 0.5  # 0-1
    evidence_count: int = 0
    first_learned: float = field(default_factory=time.time)
    last_confirmed: float = field(default_factory=time.time)
    exceptions: List[str] = field(default_factory=list)
    topic: str = ""
    source_episodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "WisdomUnit":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class MemoryStats:
    """Health snapshot of the memory system."""
    total: int = 0
    per_tier: Dict[str, int] = field(default_factory=dict)
    oldest: Optional[float] = None
    newest: Optional[float] = None
    avg_stability: float = 0.0
    consolidation_health: float = 1.0  # 0-1, 1 = healthy
    last_consolidation: Optional[float] = None
    wisdom_count: int = 0
    dying_memories: int = 0


@dataclass
class MemoryResult:
    """A search result from the unified memory search."""
    item: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0
    source_tier: str = ""
    age: float = 0.0  # hours since creation

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MemoryIssue:
    """A detected problem in the memory system."""
    issue_type: str = ""  # contradiction, gap, stale, neglected
    description: str = ""
    severity: float = 0.5  # 0-1
    affected_memories: List[str] = field(default_factory=list)
    suggested_action: str = ""


# ─── The Architect ────────────────────────────────────────────────────────────

class MemoryArchitect:
    """
    The living memory system of LOVE.
    
    Orchestrates sensory buffer, working memory, episodic memory, and semantic
    memory into a coherent whole. Memories aren't stored — they're grown,
    consolidated, and sometimes gracefully released.
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

        # Memory tiers
        self._sensory_buffer: deque = deque(maxlen=100)
        self._working_memory: List[MemoryItem] = []
        self._episodic_memory: List[Episode] = []
        self._semantic_memory: List[MemoryItem] = []
        self._wisdom: List[WisdomUnit] = []

        # Associative network
        self._associations: Dict[str, List[Dict[str, str]]] = {}  # id -> [{target, relationship}]

        # Consolidation state
        self._last_consolidation: float = 0.0
        self._consolidation_log: List[Dict] = []
        self._consolidation_thread: Optional[threading.Thread] = None
        self._running = True

        # Thread safety
        self._tier_lock = threading.RLock()

        # Load persisted state
        self._load_all()

        # Start background consolidation
        self._start_consolidation_daemon()

        logger.info("[MemoryArch] Memory Architect initialized — %d episodic, %d semantic, %d wisdom units",
                    len(self._episodic_memory), len(self._semantic_memory), len(self._wisdom))

    # ─── Tier 1: Sensory Buffer ───────────────────────────────────────────────

    def buffer_input(self, raw_input: str, source: str = "user") -> str:
        """
        Catch raw input in the sensory buffer. Transient — auto-expires.
        Everything flows through here first. Attention decides what persists.
        """
        item = MemoryItem(
            content=raw_input,
            tier="sensory",
            source=source,
            importance=self._estimate_importance(raw_input),
            emotional_weight=self._estimate_emotion(raw_input),
        )
        with self._tier_lock:
            self._sensory_buffer.append(item)
        logger.debug("[MemoryArch] Buffered sensory input from %s (importance: %.2f)",
                     source, item.importance)
        return item.id

    def get_attention_focus(self) -> Optional[MemoryItem]:
        """What's most salient right now? Highest importance in the sensory buffer."""
        with self._tier_lock:
            self._expire_sensory()
            if not self._sensory_buffer:
                return None
            return max(self._sensory_buffer, key=lambda m: m.importance * (1 + abs(m.emotional_weight)))

    def _expire_sensory(self):
        """Remove expired sensory items."""
        now = time.time()
        while self._sensory_buffer and (now - self._sensory_buffer[0].created_at) > SENSORY_BUFFER_TTL:
            self._sensory_buffer.popleft()

    # ─── Tier 2: Working Memory ───────────────────────────────────────────────

    def hold_in_working_memory(self, item: str, priority: float = 0.5, metadata: Dict = None) -> str:
        """
        Add to the conscious workspace. Limited to 7 items — 
        lowest priority gets evicted when full. This is what LOVE is
        actively thinking about right now.
        """
        memory = MemoryItem(
            content=item,
            tier="working",
            importance=priority,
            metadata=metadata or {},
        )
        with self._tier_lock:
            self._working_memory.append(memory)
            # Enforce capacity — evict lowest priority if over limit
            if len(self._working_memory) > WORKING_MEMORY_CAPACITY:
                self._working_memory.sort(key=lambda m: m.importance, reverse=True)
                evicted = self._working_memory.pop()
                logger.debug("[MemoryArch] Evicted from working memory: %s", evicted.content[:50])
                # Evicted items may get promoted to episodic if important enough
                if evicted.importance > 0.3:
                    self._promote_to_episodic(evicted)
            self._save_working()
        return memory.id

    def get_working_context(self) -> List[Dict[str, Any]]:
        """Current active items in working memory — the conscious workspace."""
        with self._tier_lock:
            return [
                {"content": m.content, "priority": m.importance, "id": m.id, "metadata": m.metadata}
                for m in sorted(self._working_memory, key=lambda m: m.importance, reverse=True)
            ]

    def clear_working_memory(self):
        """Flush working memory — useful after task completion."""
        with self._tier_lock:
            # Promote anything important before clearing
            for item in self._working_memory:
                if item.importance > 0.4:
                    self._promote_to_episodic(item)
            self._working_memory.clear()
            self._save_working()
        logger.info("[MemoryArch] Working memory cleared")

    # ─── Tier 3: Episodic Memory ──────────────────────────────────────────────

    def store_episode(self, event: str, emotional_weight: float = 0.0,
                      importance: float = 0.5, participants: List[str] = None,
                      emotional_tone: str = "neutral", outcome: str = "",
                      lessons: List[str] = None, context: Dict = None) -> str:
        """
        Store a specific experience. Episodic memories are stories —
        they have characters, emotions, outcomes. They fade unless reinforced.
        """
        episode = Episode(
            event=event,
            emotional_weight=emotional_weight,
            importance=importance,
            participants=participants or [],
            emotional_tone=emotional_tone,
            outcome=outcome,
            lessons=lessons or [],
            context=context or {},
            stability=DEFAULT_STABILITY + (abs(emotional_weight) * EMOTIONAL_STABILITY_BONUS),
        )
        with self._tier_lock:
            self._episodic_memory.append(episode)
            self._save_episodic()

        logger.info("[MemoryArch] Stored episode: %s (emotion: %.2f, importance: %.2f)",
                    event[:60], emotional_weight, importance)

        # Publish to neural bus if available
        self._publish_event("memory.episode_stored", {
            "episode_id": episode.id,
            "event": event[:100],
            "importance": importance,
        })

        return episode.id

    def recall_similar(self, query: str, limit: int = 5) -> List[Episode]:
        """
        Recall episodes most relevant to the query.
        Relevance = content similarity × recency × emotional weight × importance.
        Accessing a memory strengthens it (spacing effect).
        """
        with self._tier_lock:
            if not self._episodic_memory:
                return []

            scored = []
            query_lower = query.lower()
            query_words = set(query_lower.split())
            now = time.time()

            for ep in self._episodic_memory:
                # Content relevance (simple keyword overlap — upgrade to embeddings later)
                ep_words = set(ep.event.lower().split())
                if ep.outcome:
                    ep_words.update(ep.outcome.lower().split())
                for lesson in ep.lessons:
                    ep_words.update(lesson.lower().split())

                overlap = len(query_words & ep_words)
                if overlap == 0:
                    continue

                relevance = overlap / max(len(query_words), 1)
                # Recency boost (newer = better, exponential decay)
                age_hours = (now - ep.timestamp) / 3600
                recency = math.exp(-age_hours / 720)  # half-life ~30 days
                # Retention from forgetting curve
                retention = self._calculate_retention_raw(ep.stability, ep.last_accessed, now)
                # Emotional salience
                emotion_boost = 1 + abs(ep.emotional_weight)
                # Composite score
                score = relevance * recency * retention * emotion_boost * ep.importance

                scored.append((score, ep))

            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for score, ep in scored[:limit]:
                # Strengthen on recall (spacing effect)
                ep.last_accessed = now
                ep.access_count += 1
                ep.stability *= STABILITY_BOOST_ON_RECALL
                results.append(ep)

            self._save_episodic()
            return results

    def _promote_to_episodic(self, item: MemoryItem):
        """Promote a working memory item to episodic storage."""
        episode = Episode(
            event=item.content,
            emotional_weight=item.emotional_weight,
            importance=item.importance,
            context=item.metadata,
        )
        self._episodic_memory.append(episode)

    # ─── Tier 4: Semantic Memory ──────────────────────────────────────────────

    def crystallize_knowledge(self, episodes: List[Episode] = None, topic: str = None) -> List[MemoryItem]:
        """
        Extract general principles from specific experiences.
        This is the episodic → semantic transformation: stories become facts.
        Uses LLM to find patterns if available, falls back to heuristic extraction.
        """
        if episodes is None:
            episodes = self._get_consolidation_candidates()

        if not episodes:
            return []

        crystallized = []
        # Group episodes by emotional tone and context
        theme_groups = self._group_by_theme(episodes)

        for theme, group in theme_groups.items():
            if len(group) < 2:
                continue  # Need multiple episodes to crystallize

            # Extract common lessons
            all_lessons = []
            for ep in group:
                all_lessons.extend(ep.lessons)

            # Try LLM extraction
            knowledge = self._llm_extract_knowledge(group, theme)
            if knowledge:
                for principle in knowledge:
                    item = MemoryItem(
                        content=principle,
                        tier="semantic",
                        importance=0.7,
                        emotional_weight=sum(ep.emotional_weight for ep in group) / len(group),
                        stability=DEFAULT_STABILITY * 3,  # Semantic memories are more stable
                        metadata={"theme": theme, "source_count": len(group), "topic": topic or theme},
                    )
                    crystallized.append(item)
            elif all_lessons:
                # Heuristic: most repeated lessons become semantic knowledge
                from collections import Counter
                lesson_counts = Counter(all_lessons)
                for lesson, count in lesson_counts.most_common(3):
                    if count >= 2:
                        item = MemoryItem(
                            content=lesson,
                            tier="semantic",
                            importance=min(0.9, 0.5 + count * 0.1),
                            stability=DEFAULT_STABILITY * 3,
                            metadata={"theme": theme, "evidence_count": count, "topic": topic or theme},
                        )
                        crystallized.append(item)

        with self._tier_lock:
            self._semantic_memory.extend(crystallized)
            self._save_semantic()

        if crystallized:
            logger.info("[MemoryArch] Crystallized %d semantic memories from %d episodes",
                        len(crystallized), len(episodes))
            self._publish_event("memory.knowledge_crystallized", {
                "count": len(crystallized),
                "topics": list(theme_groups.keys()),
            })

        return crystallized

    def get_wisdom(self, topic: str) -> List[WisdomUnit]:
        """Retrieve distilled wisdom about a topic."""
        with self._tier_lock:
            topic_lower = topic.lower()
            results = []
            for w in self._wisdom:
                if (topic_lower in w.principle.lower() or
                        topic_lower in w.topic.lower()):
                    results.append(w)
            # Sort by confidence
            results.sort(key=lambda w: w.confidence, reverse=True)
            return results

    # ─── Memory Consolidation (Sleep-like) ────────────────────────────────────

    def consolidate(self, force: bool = False) -> Dict[str, Any]:
        """
        Run a consolidation cycle — LOVE's version of sleep.
        
        Process:
        1. Review recent episodic memories
        2. Identify patterns across episodes
        3. Extract generalizable knowledge → promote to semantic
        4. Strengthen emotionally significant memories
        5. Decay old, unreinforced memories
        6. Detect contradictions
        7. Resolve conflicts
        """
        now = time.time()
        if not force and (now - self._last_consolidation) < CONSOLIDATION_INTERVAL:
            return {"status": "skipped", "reason": "too soon"}

        logger.info("[MemoryArch] Beginning consolidation cycle...")
        report = {
            "timestamp": now,
            "started_at": datetime.now().isoformat(),
            "strengthened": 0,
            "decayed": 0,
            "archived": 0,
            "crystallized": 0,
            "contradictions": 0,
            "wisdom_extracted": 0,
        }

        with self._tier_lock:
            # Step 1-3: Crystallize knowledge from recent episodes
            recent = self._get_consolidation_candidates()
            if recent:
                new_knowledge = self.crystallize_knowledge(recent)
                report["crystallized"] = len(new_knowledge)

            # Step 4: Strengthen emotionally significant memories
            for ep in self._episodic_memory:
                if abs(ep.emotional_weight) > 0.6:
                    ep.stability *= 1.2
                    report["strengthened"] += 1

            # Step 5: Decay old, unreinforced memories
            to_archive = []
            for i, ep in enumerate(self._episodic_memory):
                retention = self._calculate_retention_raw(ep.stability, ep.last_accessed, now)
                if retention < DECAY_THRESHOLD:
                    to_archive.append(i)
                elif retention < 0.3:
                    # Memory is fading but not dead — reduce importance
                    ep.importance *= 0.9

            # Archive dead memories (remove from active, keep in log)
            for idx in reversed(to_archive):
                archived_ep = self._episodic_memory.pop(idx)
                self._log_archived(archived_ep)
                report["archived"] += 1

            report["decayed"] = len([ep for ep in self._episodic_memory
                                     if self._calculate_retention_raw(ep.stability, ep.last_accessed, now) < 0.5])

            # Step 6: Detect contradictions
            contradictions = self._detect_contradictions()
            report["contradictions"] = len(contradictions)

            # Step 7: Extract wisdom
            new_wisdom = self._extract_wisdom_from_semantic()
            report["wisdom_extracted"] = len(new_wisdom)

            # Update state
            self._last_consolidation = now
            self._consolidation_log.append(report)
            if len(self._consolidation_log) > 100:
                self._consolidation_log = self._consolidation_log[-100:]

            # Save everything
            self._save_all()

        logger.info("[MemoryArch] Consolidation complete — crystallized: %d, archived: %d, wisdom: %d",
                    report["crystallized"], report["archived"], report["wisdom_extracted"])

        self._publish_event("memory.consolidated", report)
        return report

    def _get_consolidation_candidates(self) -> List[Episode]:
        """Get episodes from last consolidation window that haven't been processed."""
        cutoff = self._last_consolidation
        return [ep for ep in self._episodic_memory if ep.timestamp > cutoff]

    # ─── Forgetting Curves ────────────────────────────────────────────────────

    def calculate_retention(self, memory_id: str) -> float:
        """
        Calculate current retention of a memory using Ebbinghaus curve.
        R = e^(-t/S) where t = time since last access, S = stability.
        """
        now = time.time()
        with self._tier_lock:
            # Search across tiers
            for ep in self._episodic_memory:
                if ep.id == memory_id:
                    return self._calculate_retention_raw(ep.stability, ep.last_accessed, now)
            for item in self._semantic_memory:
                if item.id == memory_id:
                    return self._calculate_retention_raw(item.stability, item.last_accessed, now)
        return 0.0

    def _calculate_retention_raw(self, stability: float, last_accessed: float, now: float) -> float:
        """
        Ebbinghaus forgetting curve: R = e^(-t/S)
        t = hours since last access
        S = stability (higher = slower decay)
        """
        t_hours = (now - last_accessed) / 3600
        if t_hours <= 0:
            return 1.0
        retention = math.exp(-t_hours / max(stability, 0.01))
        return max(0.0, min(1.0, retention))

    def get_dying_memories(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Memories about to be lost — spaced repetition opportunity.
        These are worth reviewing if they matter.
        """
        now = time.time()
        dying = []
        with self._tier_lock:
            for ep in self._episodic_memory:
                retention = self._calculate_retention_raw(ep.stability, ep.last_accessed, now)
                if retention < threshold and retention > DECAY_THRESHOLD:
                    dying.append({
                        "id": ep.id,
                        "event": ep.event,
                        "retention": round(retention, 4),
                        "importance": ep.importance,
                        "last_accessed_hours_ago": round((now - ep.last_accessed) / 3600, 1),
                    })
        dying.sort(key=lambda d: d["importance"], reverse=True)
        return dying

    # ─── Wisdom Extraction ────────────────────────────────────────────────────

    def extract_wisdom(self, topic: str = None) -> List[WisdomUnit]:
        """
        Analyze semantic memory for high-confidence generalizations.
        Wisdom is knowledge that has been confirmed multiple times.
        """
        with self._tier_lock:
            candidates = self._semantic_memory
            if topic:
                topic_lower = topic.lower()
                candidates = [m for m in candidates
                              if topic_lower in m.content.lower() or
                              topic_lower in m.metadata.get("topic", "").lower()]

            wisdom_units = []
            # Group by similar content
            processed = set()
            for i, mem in enumerate(candidates):
                if i in processed:
                    continue
                similar = [mem]
                for j, other in enumerate(candidates):
                    if j != i and j not in processed:
                        if self._content_similarity(mem.content, other.content) > 0.5:
                            similar.append(other)
                            processed.add(j)
                processed.add(i)

                if len(similar) >= 1:
                    # More evidence = higher confidence
                    evidence_count = sum(m.metadata.get("evidence_count", 1) for m in similar)
                    confidence = min(0.99, 0.3 + (evidence_count * 0.05) + (len(similar) * 0.1))

                    unit = WisdomUnit(
                        principle=mem.content,
                        confidence=confidence,
                        evidence_count=evidence_count,
                        first_learned=min(m.created_at for m in similar),
                        last_confirmed=max(m.last_accessed for m in similar),
                        topic=topic or mem.metadata.get("topic", "general"),
                        source_episodes=[m.id for m in similar],
                    )
                    wisdom_units.append(unit)

            # Update stored wisdom
            for unit in wisdom_units:
                existing = self._find_existing_wisdom(unit.principle)
                if existing:
                    existing.confidence = max(existing.confidence, unit.confidence)
                    existing.evidence_count = max(existing.evidence_count, unit.evidence_count)
                    existing.last_confirmed = unit.last_confirmed
                else:
                    self._wisdom.append(unit)

            self._save_wisdom()

        if wisdom_units:
            self._publish_event("memory.wisdom_extracted", {
                "count": len(wisdom_units),
                "topic": topic,
            })

        return wisdom_units

    def apply_wisdom(self, query: str, context: Dict = None) -> List[WisdomUnit]:
        """Retrieve wisdom relevant to the current situation.
        Falls back to synthesising proto-wisdom from episodic memory when the
        wisdom store is still empty (before consolidation has run).
        """
        with self._tier_lock:
            query_lower = query.lower()
            query_words = set(query_lower.split())
            scored: List[tuple] = []

            for w in self._wisdom:
                principle_words = set(w.principle.lower().split())
                topic_words = set(w.topic.lower().split())
                all_words = principle_words | topic_words
                overlap = len(query_words & all_words)
                if overlap > 0:
                    score = (overlap / max(len(query_words), 1)) * w.confidence
                    scored.append((score, w))

            scored.sort(key=lambda x: x[0], reverse=True)
            results = [w for _, w in scored[:5]]

            # Fallback: synthesise proto-wisdom units from episodic memory
            # so the method is immediately useful even before consolidation
            if len(results) < 2 and self._episodic_memory:
                ep_results = []
                for ep in self._episodic_memory:
                    content = f"{ep.event} {getattr(ep, 'outcome', '')} {' '.join(getattr(ep, 'lessons', []))}"
                    ep_words = set(content.lower().split())
                    overlap = len(query_words & ep_words)
                    if overlap > 0:
                        score = (overlap / max(len(query_words), 1)) * ep.importance
                        ep_results.append((score, ep))
                ep_results.sort(key=lambda x: x[0], reverse=True)
                for score, ep in ep_results[:3]:
                    if ep.lessons:
                        for lesson in ep.lessons[:2]:
                            proto = WisdomUnit(
                                id=f"proto_{ep.id}",
                                topic=query[:50],
                                principle=lesson[:200],
                                confidence=min(0.6, score),
                                source_episodes=[ep.id],
                            )
                            results.append(proto)
                    elif ep.outcome:
                        proto = WisdomUnit(
                            id=f"proto_{ep.id}",
                            topic=query[:50],
                            principle=ep.outcome[:200],
                            confidence=min(0.5, score),
                            source_episodes=[ep.id],
                        )
                        results.append(proto)

            return results[:5]

    # ─── Unified Memory Search ────────────────────────────────────────────────

    def search(self, query: str, memory_tiers: List[str] = None, limit: int = 10) -> List[MemoryResult]:
        """
        Search across all memory tiers simultaneously.
        Results ranked by: relevance × recency × emotional_weight × importance.
        """
        if memory_tiers is None or "all" in (memory_tiers or ["all"]):
            memory_tiers = ["sensory", "working", "episodic", "semantic"]

        results = []
        now = time.time()
        query_lower = query.lower()
        query_words = set(query_lower.split())

        with self._tier_lock:
            # Search working memory
            if "working" in memory_tiers:
                for item in self._working_memory:
                    score = self._score_item(item.content, query_words, item.importance,
                                            item.emotional_weight, item.created_at, now)
                    if score > 0:
                        results.append(MemoryResult(
                            item=item.to_dict(),
                            relevance_score=score,
                            source_tier="working",
                            age=(now - item.created_at) / 3600,
                        ))

            # Search episodic memory
            if "episodic" in memory_tiers:
                for ep in self._episodic_memory:
                    content = f"{ep.event} {ep.outcome} {' '.join(ep.lessons)}"
                    retention = self._calculate_retention_raw(ep.stability, ep.last_accessed, now)
                    score = self._score_item(content, query_words, ep.importance,
                                            ep.emotional_weight, ep.timestamp, now) * retention
                    if score > 0:
                        results.append(MemoryResult(
                            item=ep.to_dict(),
                            relevance_score=score,
                            source_tier="episodic",
                            age=(now - ep.timestamp) / 3600,
                        ))

            # Search semantic memory
            if "semantic" in memory_tiers:
                for item in self._semantic_memory:
                    score = self._score_item(item.content, query_words, item.importance,
                                            item.emotional_weight, item.created_at, now)
                    if score > 0:
                        # Semantic memories get a relevance boost (they're distilled truth)
                        results.append(MemoryResult(
                            item=item.to_dict(),
                            relevance_score=score * 1.3,
                            source_tier="semantic",
                            age=(now - item.created_at) / 3600,
                        ))

            # Search sensory buffer
            if "sensory" in memory_tiers:
                self._expire_sensory()
                for item in self._sensory_buffer:
                    score = self._score_item(item.content, query_words, item.importance,
                                            item.emotional_weight, item.created_at, now)
                    if score > 0:
                        results.append(MemoryResult(
                            item=item.to_dict(),
                            relevance_score=score,
                            source_tier="sensory",
                            age=(now - item.created_at) / 3600,
                        ))

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:limit]

    def get_context_for_prompt(self, query: str, token_budget: int = 500) -> str:
        """
        Build optimal memory context for the current query within token budget.
        Returns a formatted string ready to inject into a prompt.
        """
        results = self.search(query, limit=15)
        if not results:
            return ""

        context_parts = []
        estimated_tokens = 0

        # Always include working memory context
        working = self.get_working_context()
        if working:
            wm_str = "Active context: " + "; ".join(w["content"][:80] for w in working[:3])
            context_parts.append(wm_str)
            estimated_tokens += len(wm_str.split()) * 1.3

        # Add relevant wisdom first (highest signal-to-noise)
        wisdom = self.apply_wisdom(query)
        for w in wisdom[:2]:
            if estimated_tokens >= token_budget:
                break
            w_str = f"Known: {w.principle} (confidence: {w.confidence:.0%})"
            context_parts.append(w_str)
            estimated_tokens += len(w_str.split()) * 1.3

        # Add search results
        for result in results:
            if estimated_tokens >= token_budget:
                break
            content = result.item.get("content") or result.item.get("event", "")
            if not content:
                continue
            snippet = content[:150]
            tier_label = result.source_tier.capitalize()
            r_str = f"[{tier_label}] {snippet}"
            context_parts.append(r_str)
            estimated_tokens += len(r_str.split()) * 1.3

        return "\n".join(context_parts)

    # ─── Associative Memory Graph ─────────────────────────────────────────────

    def link_memories(self, memory_a: str, memory_b: str, relationship: str = "related"):
        """Create an association between two memories — spreading activation."""
        with self._tier_lock:
            if memory_a not in self._associations:
                self._associations[memory_a] = []
            if memory_b not in self._associations:
                self._associations[memory_b] = []

            # Bidirectional link
            self._associations[memory_a].append({"target": memory_b, "relationship": relationship})
            self._associations[memory_b].append({"target": memory_a, "relationship": relationship})
            self._save_associations()

        logger.debug("[MemoryArch] Linked %s <-> %s (%s)", memory_a[:8], memory_b[:8], relationship)

    def get_associations(self, memory_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """
        Get connected memories via spreading activation.
        Depth controls how far to traverse the association graph.
        """
        visited = set()
        results = []

        def _traverse(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return
            visited.add(current_id)
            links = self._associations.get(current_id, [])
            for link in links:
                target_id = link["target"]
                if target_id not in visited:
                    results.append({
                        "id": target_id,
                        "relationship": link["relationship"],
                        "depth": current_depth,
                    })
                    _traverse(target_id, current_depth + 1)

        with self._tier_lock:
            _traverse(memory_id, 1)
        return results

    def find_unexpected_connections(self, topic: str) -> List[Dict[str, Any]]:
        """
        Find surprising links across disparate topics — creativity aid.
        Looks for memories that are connected but seem unrelated on the surface.
        """
        # Find memories about this topic
        topic_results = self.search(topic, limit=10)
        unexpected = []

        for result in topic_results:
            item_id = result.item.get("id", "")
            associations = self.get_associations(item_id, depth=3)
            for assoc in associations:
                # Check if the associated memory is about a different topic
                connected = self._find_memory_by_id(assoc["id"])
                if connected:
                    content = connected.get("content") or connected.get("event", "")
                    # If the content doesn't share words with the topic, it's unexpected
                    if topic.lower() not in content.lower():
                        unexpected.append({
                            "source_topic": topic,
                            "connected_content": content[:100],
                            "relationship": assoc["relationship"],
                            "connection_depth": assoc["depth"],
                        })

        return unexpected[:5]

    # ─── Memory Health ────────────────────────────────────────────────────────

    def get_memory_stats(self) -> MemoryStats:
        """Health snapshot of the entire memory system."""
        now = time.time()
        with self._tier_lock:
            all_stabilities = [ep.stability for ep in self._episodic_memory]
            all_stabilities.extend(m.stability for m in self._semantic_memory)

            dying = len([ep for ep in self._episodic_memory
                        if self._calculate_retention_raw(ep.stability, ep.last_accessed, now) < 0.1])

            all_timestamps = [ep.timestamp for ep in self._episodic_memory]
            all_timestamps.extend(m.created_at for m in self._semantic_memory)

            # Consolidation health: how recently we consolidated and how much is pending
            time_since_consolidation = now - self._last_consolidation if self._last_consolidation else float('inf')
            consolidation_health = max(0.0, 1.0 - (time_since_consolidation / (CONSOLIDATION_INTERVAL * 2)))

            return MemoryStats(
                total=len(self._episodic_memory) + len(self._semantic_memory) + len(self._wisdom),
                per_tier={
                    "sensory": len(self._sensory_buffer),
                    "working": len(self._working_memory),
                    "episodic": len(self._episodic_memory),
                    "semantic": len(self._semantic_memory),
                    "wisdom": len(self._wisdom),
                },
                oldest=min(all_timestamps) if all_timestamps else None,
                newest=max(all_timestamps) if all_timestamps else None,
                avg_stability=sum(all_stabilities) / len(all_stabilities) if all_stabilities else 0.0,
                consolidation_health=consolidation_health,
                last_consolidation=self._last_consolidation or None,
                wisdom_count=len(self._wisdom),
                dying_memories=dying,
            )

    def detect_memory_issues(self) -> List[MemoryIssue]:
        """Detect problems in the memory system — contradictions, gaps, staleness."""
        issues = []
        now = time.time()

        with self._tier_lock:
            # Check for contradictions
            contradictions = self._detect_contradictions()
            for c in contradictions:
                issues.append(MemoryIssue(
                    issue_type="contradiction",
                    description=c["description"],
                    severity=0.7,
                    affected_memories=c["memory_ids"],
                    suggested_action="Review and resolve conflicting memories",
                ))

            # Check for stale memories dominating
            stale_count = sum(1 for ep in self._episodic_memory
                            if (now - ep.last_accessed) > 30 * 24 * 3600)  # 30 days
            if stale_count > len(self._episodic_memory) * 0.7:
                issues.append(MemoryIssue(
                    issue_type="stale",
                    description=f"{stale_count} memories haven't been accessed in 30+ days",
                    severity=0.4,
                    suggested_action="Run consolidation to archive or strengthen",
                ))

            # Check for over-consolidation (too long since last cycle)
            if self._last_consolidation and (now - self._last_consolidation) > CONSOLIDATION_INTERVAL * 3:
                issues.append(MemoryIssue(
                    issue_type="consolidation_overdue",
                    description="Memory consolidation is overdue — knowledge may not be crystallizing",
                    severity=0.6,
                    suggested_action="Force consolidation cycle",
                ))

            # Check for neglected topics
            if len(self._episodic_memory) > 20:
                topics = {}
                for ep in self._episodic_memory:
                    tone = ep.emotional_tone
                    topics[tone] = topics.get(tone, 0) + 1
                dominant = max(topics.values()) if topics else 0
                if dominant > len(self._episodic_memory) * 0.6:
                    dominant_topic = max(topics, key=topics.get)
                    issues.append(MemoryIssue(
                        issue_type="imbalanced",
                        description=f"Memory is heavily skewed toward '{dominant_topic}' episodes",
                        severity=0.3,
                        suggested_action="Actively seek diverse experiences",
                    ))

        return issues

    def repair_memory(self, issue: MemoryIssue) -> str:
        """Attempt to fix a detected memory issue."""
        if issue.issue_type == "consolidation_overdue":
            self.consolidate(force=True)
            return "Forced consolidation cycle completed"
        elif issue.issue_type == "stale":
            # Archive memories with very low retention
            archived = 0
            with self._tier_lock:
                now = time.time()
                to_remove = []
                for i, ep in enumerate(self._episodic_memory):
                    retention = self._calculate_retention_raw(ep.stability, ep.last_accessed, now)
                    if retention < 0.05 and ep.importance < 0.3:
                        to_remove.append(i)
                for idx in reversed(to_remove):
                    self._log_archived(self._episodic_memory.pop(idx))
                    archived += 1
                self._save_episodic()
            return f"Archived {archived} effectively dead memories"
        elif issue.issue_type == "contradiction":
            return "Contradictions flagged for manual review — newer evidence preferred"
        return "No automatic repair available for this issue type"

    # ─── Internal Helpers ─────────────────────────────────────────────────────

    def _score_item(self, content: str, query_words: Set[str], importance: float,
                    emotional_weight: float, created_at: float, now: float) -> float:
        """Unified scoring: relevance × recency × emotional × importance."""
        content_words = set(content.lower().split())
        overlap = len(query_words & content_words)
        if overlap == 0:
            return 0.0

        relevance = overlap / max(len(query_words), 1)
        age_hours = max((now - created_at) / 3600, 0.01)
        recency = 1.0 / (1.0 + math.log1p(age_hours / 24))  # logarithmic decay
        emotion_boost = 1 + abs(emotional_weight) * 0.5
        return relevance * recency * emotion_boost * importance

    def _estimate_importance(self, text: str) -> float:
        """Quick heuristic importance estimation for sensory input."""
        importance = 0.3
        # Questions are more important
        if "?" in text:
            importance += 0.2
        # Longer inputs tend to be more substantive
        if len(text) > 200:
            importance += 0.1
        # Emotional language
        emotional_words = {"love", "hate", "worried", "excited", "stressed", "happy",
                          "angry", "scared", "proud", "frustrated", "grateful"}
        if any(w in text.lower() for w in emotional_words):
            importance += 0.2
        # Direct requests
        if any(w in text.lower() for w in ["please", "need", "help", "urgent", "important"]):
            importance += 0.15
        return min(1.0, importance)

    def _estimate_emotion(self, text: str) -> float:
        """Quick emotional valence estimation (-1 to 1)."""
        positive = {"happy", "excited", "great", "love", "amazing", "proud", "grateful", "good"}
        negative = {"stressed", "worried", "angry", "hate", "frustrated", "sad", "overwhelmed", "bad"}

        text_lower = text.lower()
        pos_count = sum(1 for w in positive if w in text_lower)
        neg_count = sum(1 for w in negative if w in text_lower)

        if pos_count + neg_count == 0:
            return 0.0
        return (pos_count - neg_count) / (pos_count + neg_count)

    def _content_similarity(self, a: str, b: str) -> float:
        """Simple word-overlap similarity (Jaccard)."""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0

    def _group_by_theme(self, episodes: List[Episode]) -> Dict[str, List[Episode]]:
        """Group episodes by emotional tone and context keywords."""
        groups: Dict[str, List[Episode]] = {}
        for ep in episodes:
            key = ep.emotional_tone or "neutral"
            if key not in groups:
                groups[key] = []
            groups[key].append(ep)
        return groups

    def _detect_contradictions(self) -> List[Dict[str, Any]]:
        """Find memories that contradict each other."""
        contradictions = []
        # Simple heuristic: look for opposing emotional tones on same topic
        # Real implementation would use LLM
        seen_topics: Dict[str, List[Episode]] = {}
        for ep in self._episodic_memory:
            # Use first 3 words as rough topic key
            topic_key = " ".join(ep.event.lower().split()[:3])
            if topic_key not in seen_topics:
                seen_topics[topic_key] = []
            seen_topics[topic_key].append(ep)

        for topic_key, episodes in seen_topics.items():
            if len(episodes) < 2:
                continue
            # Check for opposing outcomes or emotional tones
            tones = set(ep.emotional_tone for ep in episodes)
            if "excited" in tones and "stressed" in tones:
                contradictions.append({
                    "description": f"Mixed signals about '{topic_key}' — both positive and negative experiences",
                    "memory_ids": [ep.id for ep in episodes[:2]],
                })

        return contradictions[:5]  # Limit to top 5

    def _extract_wisdom_from_semantic(self) -> List[WisdomUnit]:
        """Promote high-confidence semantic memories to wisdom."""
        new_wisdom = []
        for mem in self._semantic_memory:
            evidence = mem.metadata.get("evidence_count", 1)
            if evidence >= 3 and mem.importance > 0.6:
                # Check if already exists as wisdom
                if not self._find_existing_wisdom(mem.content):
                    unit = WisdomUnit(
                        principle=mem.content,
                        confidence=min(0.95, 0.4 + evidence * 0.08),
                        evidence_count=evidence,
                        first_learned=mem.created_at,
                        last_confirmed=mem.last_accessed,
                        topic=mem.metadata.get("topic", "general"),
                    )
                    self._wisdom.append(unit)
                    new_wisdom.append(unit)
        return new_wisdom

    def _find_existing_wisdom(self, principle: str) -> Optional[WisdomUnit]:
        """Check if similar wisdom already exists."""
        for w in self._wisdom:
            if self._content_similarity(w.principle, principle) > 0.6:
                return w
        return None

    def _find_memory_by_id(self, memory_id: str) -> Optional[Dict]:
        """Find any memory by ID across all tiers."""
        for ep in self._episodic_memory:
            if ep.id == memory_id:
                return ep.to_dict()
        for item in self._semantic_memory:
            if item.id == memory_id:
                return item.to_dict()
        for item in self._working_memory:
            if item.id == memory_id:
                return item.to_dict()
        return None

    def _log_archived(self, episode: Episode):
        """Log an archived (dead) memory for potential resurrection."""
        archive_file = DATA_DIR / "archived_memories.jsonl"
        try:
            with open(archive_file, "a") as f:
                data = episode.to_dict()
                data["archived_at"] = time.time()
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            logger.warning("[MemoryArch] Failed to archive memory: %s", e)

    def _llm_extract_knowledge(self, episodes: List[Episode], theme: str) -> List[str]:
        """Use LLM to extract generalizable knowledge from episodes."""
        try:
            from core.llm import get_reasoning_llm
            llm = get_reasoning_llm(temperature=0.3)

            episodes_text = "\n".join([
                f"- {ep.event} (tone: {ep.emotional_tone}, outcome: {ep.outcome})"
                for ep in episodes[:10]
            ])

            prompt = (
                f"Given these {len(episodes)} experiences about '{theme}':\n\n"
                f"{episodes_text}\n\n"
                "Extract 1-3 general principles or patterns. "
                "Be specific and actionable. One principle per line, no numbering."
            )

            response = llm.invoke(prompt)
            if response:
                principles = [line.strip() for line in response.strip().split("\n")
                            if line.strip() and len(line.strip()) > 10]
                return principles[:3]
        except Exception as e:
            logger.debug("[MemoryArch] LLM extraction unavailable: %s", e)
        return []

    # ─── Neural Bus Integration ───────────────────────────────────────────────

    def _publish_event(self, event_type: str, payload: Dict[str, Any]):
        """Publish memory events to the neural bus (if available)."""
        try:
            from core.neural_bus import NeuralBus
            bus = NeuralBus()
            bus.publish(
                domain="memory",
                event_type=event_type,
                payload=payload,
                source_module="memory_architect",
            )
        except Exception:
            pass  # Neural bus not available — degrade gracefully

    # ─── Background Consolidation Daemon ──────────────────────────────────────

    def _start_consolidation_daemon(self):
        """Background thread that runs consolidation on schedule."""
        def _daemon():
            while self._running:
                try:
                    time.sleep(60)  # Check every minute
                    now = time.time()
                    if (now - self._last_consolidation) >= CONSOLIDATION_INTERVAL:
                        logger.info("[MemoryArch] Auto-consolidation triggered")
                        self.consolidate()
                except Exception as e:
                    logger.error("[MemoryArch] Consolidation daemon error: %s", e)
                    time.sleep(300)  # Back off on error

        self._consolidation_thread = threading.Thread(target=_daemon, daemon=True, name="MemoryConsolidation")
        self._consolidation_thread.start()

    def shutdown(self):
        """Graceful shutdown — save everything and stop background threads."""
        self._running = False
        self._save_all()
        logger.info("[MemoryArch] Memory Architect shut down — all memories persisted")

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _save_all(self):
        """Persist all memory tiers to disk."""
        self._save_working()
        self._save_episodic()
        self._save_semantic()
        self._save_wisdom()
        self._save_associations()
        self._save_consolidation_log()

    def _save_working(self):
        self._safe_write(WORKING_FILE, [m.to_dict() for m in self._working_memory])

    def _save_episodic(self):
        self._safe_write(EPISODIC_FILE, [ep.to_dict() for ep in self._episodic_memory])

    def _save_semantic(self):
        self._safe_write(SEMANTIC_FILE, [m.to_dict() for m in self._semantic_memory])

    def _save_wisdom(self):
        self._safe_write(WISDOM_FILE, [w.to_dict() for w in self._wisdom])

    def _save_associations(self):
        self._safe_write(ASSOCIATIONS_FILE, self._associations)

    def _save_consolidation_log(self):
        self._safe_write(CONSOLIDATION_LOG, self._consolidation_log)

    def _safe_write(self, path: Path, data: Any):
        """Atomic-ish write with error handling."""
        try:
            tmp = path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            tmp.replace(path)
        except Exception as e:
            logger.error("[MemoryArch] Failed to write %s: %s", path.name, e)

    def _load_all(self):
        """Load all persisted memory tiers."""
        # Working memory
        working_data = self._safe_read(WORKING_FILE, [])
        self._working_memory = [MemoryItem.from_dict(d) for d in working_data]

        # Episodic memory
        episodic_data = self._safe_read(EPISODIC_FILE, [])
        self._episodic_memory = [Episode.from_dict(d) for d in episodic_data]

        # Semantic memory
        semantic_data = self._safe_read(SEMANTIC_FILE, [])
        self._semantic_memory = [MemoryItem.from_dict(d) for d in semantic_data]

        # Wisdom
        wisdom_data = self._safe_read(WISDOM_FILE, [])
        self._wisdom = [WisdomUnit.from_dict(d) for d in wisdom_data]

        # Associations
        self._associations = self._safe_read(ASSOCIATIONS_FILE, {})

        # Consolidation log
        self._consolidation_log = self._safe_read(CONSOLIDATION_LOG, [])
        if self._consolidation_log:
            self._last_consolidation = self._consolidation_log[-1].get("timestamp", 0)

    def _safe_read(self, path: Path, default: Any) -> Any:
        """Safe file read with graceful fallback."""
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("[MemoryArch] Failed to read %s: %s — using default", path.name, e)
            return default


# ─── Singleton Access ─────────────────────────────────────────────────────────

_architect_instance: Optional[MemoryArchitect] = None
_architect_lock = threading.Lock()


def get_memory_architect() -> MemoryArchitect:
    """
    Get the singleton MemoryArchitect instance.
    Thread-safe, lazy initialization.
    """
    global _architect_instance
    if _architect_instance is None:
        with _architect_lock:
            if _architect_instance is None:
                _architect_instance = MemoryArchitect()
    return _architect_instance
