"""
LOVE Knowledge Synthesizer — Integration Intelligence (Modern AI Pattern)

Most knowledge is fragmented and isolated. This synthesizer:

1. KNOWLEDGE TRACKING
   - Record knowledge pieces and their characteristics
   - Track connections between different knowledge domains
   - Log synthesis attempts and their outcomes

2. PATTERN ANALYSIS
   - Identify the user's knowledge architecture (hierarchical, networked, linear, spiral)
   - Find synthesis patterns that create insight
   - Detect knowledge silos and isolation

3. SYNTHESIS PRACTICES
   - Suggest connection-building exercises
   - Provide cross-domain integration techniques
   - Recommendation knowledge mapping practices

4. INSIGHT GENERATION
   - Track the correlation between synthesis and insight
   - Alert when knowledge is accumulating without integration
   - Celebrate synthesis breakthroughs

Architecture:
- record_knowledge(topic, source, connections, insight): Log knowledge
- get_synthesis_stats(): Get synthesis pattern analysis
- get_synthesis_exercise(silos, goal): Get exercise
- get_synthesis_score(): Calculate overall synthesis health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "knowledge_synthesizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_LOG = DATA_DIR / "knowledge.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class KnowledgeEntry:
    """A tracked knowledge entry."""
    entry_id: str = ""
    topic: str = ""
    source: str = ""  # book, conversation, experience, observation, course
    domain: str = ""  # where this knowledge lives
    connections: List[str] = field(default_factory=list)  # connected topics
    insight: str = ""  # synthesized insight
    insight_quality: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class KnowledgeSynthesizer:
    """
    Intelligent knowledge synthesizer with connection tracking and silo detection.
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
            "avg_insight_quality": 0.0,
            "avg_connections": 0.0,
            "dominant_domain": "",
            "silo_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_knowledge(self, topic: str = "", source: str = "", domain: str = "", connections: Optional[List[str]] = None, insight: str = "", insight_quality: float = 0.5, notes: str = "") -> KnowledgeEntry:
        """Record a knowledge entry."""
        entry_id = f"know_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = KnowledgeEntry(
            entry_id=entry_id,
            topic=topic or "unspecified",
            source=source or "observation",
            domain=domain or "general",
            connections=connections or [],
            insight=insight,
            insight_quality=insight_quality,
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

    def get_synthesis_stats(self) -> Dict[str, Any]:
        """Get synthesis pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "insight_sum": 0.0, "connection_sum": 0.0})
        for e in self._entries:
            by_domain[e.domain]["count"] += 1
            by_domain[e.domain]["insight_sum"] += e.insight_quality
            by_domain[e.domain]["connection_sum"] += len(e.connections)

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "avg_insight": round(data["insight_sum"] / count, 2),
                "avg_connections": round(data["connection_sum"] / count, 1),
            }

        dominant_domain = max(domain_stats.items(), key=lambda x: x[1]["count"]) if domain_stats else ("", {})

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "insight_sum": 0.0})
        for e in self._entries:
            by_source[e.source]["count"] += 1
            by_source[e.source]["insight_sum"] += e.insight_quality

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_insight": round(data["insight_sum"] / count, 2),
            }

        # Connection network
        all_connections = []
        for e in self._entries:
            all_connections.extend(e.connections)
        
        connection_counts = defaultdict(int)
        for conn in all_connections:
            connection_counts[conn] += 1

        top_connections = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Insight analysis
        with_insight = [e for e in self._entries if e.insight]
        insight_rate = len(with_insight) / len(self._entries)

        # Silo detection
        if len(self._entries) >= 20:
            recent = list(self._entries)[-20:]
            recent_domains = set(e.domain for e in recent)
            domain_concentration = max(len([e for e in recent if e.domain == d]) for d in recent_domains) / len(recent)
            silo_risk = domain_concentration > 0.6 and len(recent_domains) < 3
        else:
            silo_risk = False

        # Cross-domain connections
        cross_domain = [e for e in self._entries if e.connections and any(conn not in [e.domain, e.topic] for conn in e.connections)]
        cross_domain_rate = len(cross_domain) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_insight = sum(e.insight_quality for e in recent) / len(recent)
            recent_connections = sum(len(e.connections) for e in recent) / len(recent)
        else:
            recent_insight = 0
            recent_connections = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_insight = sum(e.insight_quality for e in older) / len(older)
            older_connections = sum(len(e.connections) for e in older) / len(older)
            insight_trend = recent_insight - older_insight
            connection_trend = recent_connections - older_connections
        else:
            insight_trend = 0
            connection_trend = 0

        return {
            "total_entries": len(self._entries),
            "domain_stats": domain_stats,
            "dominant_domain": dominant_domain[0],
            "source_stats": source_stats,
            "top_connections": top_connections,
            "insight_rate": round(insight_rate, 2),
            "silo_risk": silo_risk,
            "cross_domain_rate": round(cross_domain_rate, 2),
            "avg_insight": round(sum(e.insight_quality for e in self._entries) / len(self._entries), 2),
            "avg_connections": round(sum(len(e.connections) for e in self._entries) / len(self._entries), 1),
            "insight_trend": round(insight_trend, 2),
            "connection_trend": round(connection_trend, 2),
        }

    def get_synthesis_exercise(self, silos: Optional[List[str]] = None, goal: str = "") -> Dict[str, Any]:
        """Get exercise."""
        exercises = {
            "bridge_silos": [
                "Find one concept from each silo. Force a connection between them. What's the bridge?",
                "Write a paragraph that uses vocabulary from two different domains. Make it coherent.",
                "Draw a Venn diagram of two silos. What's in the overlap?",
            ],
            "deepen_connections": [
                "Pick one connection you made. Ask 'why?' 3 times. Go deeper.",
                "Find the root principle behind two connected ideas. What's the common thread?",
                "Explain one connection to a child. If you can't simplify it, you don't fully understand it.",
            ],
            "generate_insight": [
                "Synthesize 3 pieces of knowledge into one sentence. One powerful sentence.",
                "Write a 'however' statement. 'Most people think X, however...' What's the counter-intuitive insight?",
                "What if the opposite of what you believe is true? Explore that seriously for 10 minutes.",
            ],
            "map_knowledge": [
                "Create a mind map of everything you know about one topic. Then add 3 branches from other domains.",
                "List 10 concepts you understand well. Draw lines between the related ones. Notice the clusters and the gaps.",
                "Write a 'knowledge autobiography.' How did your understanding of this topic evolve?",
            ],
            "general": [
                "Read one article from a field you know nothing about. Find one connection to your expertise.",
                "Have a conversation with someone from a different discipline. Ask them about their mental models.",
                "Teach a concept you know well to someone from a completely different background. Notice what you assume.",
            ],
        }

        selected = exercises.get(goal, exercises["general"])

        if silos and len(silos) > 1:
            silo_note = f"You have knowledge silos: {', '.join(silos)}. The magic happens at the intersections. Force connections."
        elif silos:
            silo_note = f"Your knowledge is concentrated in {silos[0]}. Expand. Read outside this domain."
        else:
            silo_note = "Your knowledge is well-distributed. Now deepen the connections between domains."

        return {
            "silos": silos or [],
            "goal": goal or "general",
            "exercise": random.choice(selected),
            "silo_note": silo_note,
            "principle": "Knowledge is not power. Synthesized knowledge is power. A thousand isolated facts are less useful than one insight that connects them. The value is in the connections, not the collection.",
        }

    def get_synthesis_score(self) -> int:
        """Calculate overall synthesis health (0-100)."""
        if not self._entries:
            return 30

        # Insight quality
        avg_insight = sum(e.insight_quality for e in self._entries) / len(self._entries)

        # Connection richness
        avg_connections = sum(len(e.connections) for e in self._entries) / len(self._entries)

        # Insight rate
        with_insight = [e for e in self._entries if e.insight]
        insight_rate = len(with_insight) / len(self._entries)

        # Cross-domain
        cross_domain = [e for e in self._entries if e.connections and any(conn not in [e.domain, e.topic] for conn in e.connections)]
        cross_domain_rate = len(cross_domain) / len(self._entries)

        # Domain variety
        unique_domains = len(set(e.domain for e in self._entries))

        # Source variety
        unique_sources = len(set(e.source for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_insight = sum(e.insight_quality for e in recent) / len(recent)
            recent_connections = sum(len(e.connections) for e in recent) / len(recent)
        else:
            recent_insight = 0
            recent_connections = 0

        # Silo penalty
        if len(self._entries) >= 20:
            recent_entries = list(self._entries)[-20:]
            recent_domains = set(e.domain for e in recent_entries)
            domain_concentration = max(len([e for e in recent_entries if e.domain == d]) for d in recent_domains) / len(recent_entries)
            silo_penalty = min(15, domain_concentration * 15) if domain_concentration > 0.6 else 0
        else:
            silo_penalty = 0

        score = (avg_insight * 25) + (avg_connections * 10) + (insight_rate * 15) + (cross_domain_rate * 15) + (unique_domains * 2) + (unique_sources * 2) + (recent_insight * 15) + (recent_connections * 10) - silo_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_insight_quality"] = round(sum(e.insight_quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_connections"] = round(sum(len(e.connections) for e in self._entries) / len(self._entries), 1)

            by_domain = defaultdict(int)
            for e in self._entries:
                by_domain[e.domain] += 1
            if by_domain:
                dominant = max(by_domain.items(), key=lambda x: x[1])
                self._stats["dominant_domain"] = dominant[0]

            if len(self._entries) >= 20:
                recent = list(self._entries)[-20:]
                recent_domains = set(e.domain for e in recent)
                domain_concentration = max(len([e for e in recent if e.domain == d]) for d in recent_domains) / len(recent)
                self._stats["silo_risk"] = domain_concentration > 0.6 and len(recent_domains) < 3

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

    def _log_entry(self, entry: KnowledgeEntry):
        try:
            with open(KNOWLEDGE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "topic": entry.topic,
                    "source": entry.source,
                    "domain": entry.domain,
                    "connections": entry.connections,
                    "insight": entry.insight,
                    "insight_quality": entry.insight_quality,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ks_instance: Optional[KnowledgeSynthesizer] = None
_ks_lock = threading.Lock()


def get_knowledge_synthesizer() -> KnowledgeSynthesizer:
    global _ks_instance
    with _ks_lock:
        if _ks_instance is None:
            _ks_instance = KnowledgeSynthesizer()
        return _ks_instance
