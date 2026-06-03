"""
LOVE Intergenerational Bridge Builder — Cross-Age Intelligence (Modern AI Pattern)

Most people live in age-segregated silos. This builder:

1. BRIDGE TRACKING
   - Record cross-generational interactions and their quality
   - Track interaction types (learning, teaching, support, celebration, sharing)
   - Log mutual benefit, respect, and understanding

2. PATTERN ANALYSIS
   - Identify the user's intergenerational profile (connected, distant, one-directional, rich)
   - Find patterns that create mutual enrichment across ages
   - Detect age-based isolation and its costs

3. BRIDGE BUILDING
   - Suggest intergenerational activities matched to current relationships
   - Provide frameworks for respecting wisdom while embracing change
   - Recommend practices for cross-age communication

4. LEGACY CULTIVATION
   - Track the correlation between intergenerational connection and life meaning
   - Alert when generational distance is growing
   - Celebrate moments of genuine cross-age understanding

Architecture:
- record_interaction(generation, type, mutual_benefit, respect, understanding): Log interaction
- get_bridge_stats(): Get bridge pattern analysis
- get_bridge_suggestion(capacity, context): Get suggestion
- get_bridge_score(): Calculate overall bridge health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "intergenerational_bridge_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BridgeEntry:
    """A tracked intergenerational interaction."""
    entry_id: str = ""
    generation: str = ""  # older, younger, peer_elder, peer_youth
    person: str = ""  # who
    interaction_type: str = ""  # learning, teaching, support, celebration, sharing
    mutual_benefit: float = 0.0  # 0-1
    respect: float = 0.5  # 0-1
    understanding: float = 0.0  # 0-1
    wisdom_shared: float = 0.0  # 0-1
    energy_received: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class IntergenerationalBridgeBuilder:
    """
    Intelligent intergenerational bridge builder with cross-age detection and legacy cultivation.
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
            "avg_mutual_benefit": 0.0,
            "avg_respect": 0.0,
            "isolation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, generation: str = "", person: str = "", interaction_type: str = "", mutual_benefit: float = 0.0, respect: float = 0.5, understanding: float = 0.0, wisdom_shared: float = 0.0, energy_received: float = 0.0, notes: str = "") -> BridgeEntry:
        """Record an intergenerational interaction."""
        entry_id = f"brg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BridgeEntry(
            entry_id=entry_id,
            generation=generation or "unspecified",
            person=person or "unspecified",
            interaction_type=interaction_type or "sharing",
            mutual_benefit=mutual_benefit,
            respect=respect,
            understanding=understanding,
            wisdom_shared=wisdom_shared,
            energy_received=energy_received,
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

    def get_bridge_stats(self) -> Dict[str, Any]:
        """Get bridge pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Generation analysis
        by_gen = defaultdict(lambda: {"count": 0, "mutual_sum": 0.0, "respect_sum": 0.0, "understanding_sum": 0.0})
        for e in self._entries:
            by_gen[e.generation]["count"] += 1
            by_gen[e.generation]["mutual_sum"] += e.mutual_benefit
            by_gen[e.generation]["respect_sum"] += e.respect
            by_gen[e.generation]["understanding_sum"] += e.understanding

        gen_stats = {}
        for g, data in by_gen.items():
            count = data["count"]
            gen_stats[g] = {
                "count": count,
                "avg_mutual_benefit": round(data["mutual_sum"] / count, 2),
                "avg_respect": round(data["respect_sum"] / count, 2),
                "avg_understanding": round(data["understanding_sum"] / count, 2),
            }

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "mutual_sum": 0.0, "wisdom_sum": 0.0})
        for e in self._entries:
            by_type[e.interaction_type]["count"] += 1
            by_type[e.interaction_type]["mutual_sum"] += e.mutual_benefit
            by_type[e.interaction_type]["wisdom_sum"] += e.wisdom_shared

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_mutual_benefit": round(data["mutual_sum"] / count, 2),
                "avg_wisdom_shared": round(data["wisdom_sum"] / count, 2),
            }

        # Mutual benefit analysis
        high_mutual = [e for e in self._entries if e.mutual_benefit > 0.7]
        low_mutual = [e for e in self._entries if e.mutual_benefit < 0.4]
        if high_mutual and low_mutual:
            high_mutual_under = sum(e.understanding for e in high_mutual) / len(high_mutual)
            low_mutual_under = sum(e.understanding for e in low_mutual) / len(low_mutual)
            high_mutual_energy = sum(e.energy_received for e in high_mutual) / len(high_mutual)
            low_mutual_energy = sum(e.energy_received for e in low_mutual) / len(low_mutual)
        else:
            high_mutual_under = 0
            low_mutual_under = 0
            high_mutual_energy = 0
            low_mutual_energy = 0

        # Respect analysis
        high_respect = [e for e in self._entries if e.respect > 0.7]
        low_respect = [e for e in self._entries if e.respect < 0.4]
        if high_respect and low_respect:
            high_respect_wisdom = sum(e.wisdom_shared for e in high_respect) / len(high_respect)
            low_respect_wisdom = sum(e.wisdom_shared for e in low_respect) / len(low_respect)
        else:
            high_respect_wisdom = 0
            low_respect_wisdom = 0

        # Isolation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_mutual = sum(e.mutual_benefit for e in recent) / len(recent)
            recent_under = sum(e.understanding for e in recent) / len(recent)
            isolation_risk = recent_mutual < 0.3 and recent_under < 0.3
        else:
            isolation_risk = True

        return {
            "total_entries": len(self._entries),
            "generation_stats": gen_stats,
            "type_stats": type_stats,
            "mutual_benefit_impact": {
                "high_mutual_understanding": round(high_mutual_under, 2),
                "low_mutual_understanding": round(low_mutual_under, 2),
                "high_mutual_energy": round(high_mutual_energy, 2),
                "low_mutual_energy": round(low_mutual_energy, 2),
            },
            "respect_effect": {
                "high_respect_wisdom": round(high_respect_wisdom, 2),
                "low_respect_wisdom": round(low_respect_wisdom, 2),
            },
            "isolation_risk": isolation_risk,
            "avg_mutual_benefit": round(sum(e.mutual_benefit for e in self._entries) / len(self._entries), 2),
            "avg_respect": round(sum(e.respect for e in self._entries) / len(self._entries), 2),
        }

    def get_bridge_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get bridge suggestion."""
        suggestions = [
            "Ask an older person about their life. Not for advice. For the story. The stories of previous generations are the inheritance we often ignore. Ask. Listen. Receive.",
            "Teach a younger person something you know. Not to be impressive. To pass it on. Every skill you have is a potential bridge. Share it.",
            "Cook a family recipe with someone from another generation. The kitchen is the original intergenerational classroom. Food is memory. Cooking together is connection.",
            "Play across generations. Chess with a grandparent. Video games with a child. Sports with a teenager. Play dissolves age barriers faster than anything.",
            "Listen to music from another generation. Ask what it meant to them. Music carries memory. And sharing music is sharing a piece of your history.",
            "Visit someone older regularly. Not just holidays. Weekly. Monthly. Consistency says: you matter to me. And isolation is the enemy of older people.",
            "Ask a younger person to teach you something. Technology. Slang. A game. Humility creates connection. The person who can't learn from the young is already old in the worst way.",
            "Share your failures across generations. Not just successes. The young need to know that struggle is normal. The old need to know their struggles mattered.",
            "Create something together. A garden. A quilt. A business. A tradition. Collaboration across generations creates bonds that outlast any single interaction.",
            "Every generation thinks the next one is ruining everything. And every generation is wrong. The young are not broken. The old are not obsolete. We're all just humans at different points in the same journey. Meet each other there.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One question. One story. One moment across generations. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A regular visit. A shared activity. A teaching moment. Medium investment in bridges."
        else:
            capacity_note = "Good capacity. A major cross-generational project. A mentorship. A tradition. You have the energy to build real intergenerational culture."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "We live in the most age-segregated society in human history. Children go to school. Adults go to work. Old people go to retirement communities. We have lost the natural intergenerational contact that was the norm for most of human existence. And we've lost something precious. The young need the wisdom of the old. The old need the energy of the young. Everyone needs the perspective of other generations to see their own time clearly. Intergenerational connection is not charity. It's mutual enrichment. It's how we maintain continuity. It's how we prevent each generation from having to relearn everything. Build bridges across ages. The benefits flow both ways.",
        }

    def get_bridge_score(self) -> int:
        """Calculate overall bridge health (0-100)."""
        if not self._entries:
            return 25

        avg_mutual = sum(e.mutual_benefit for e in self._entries) / len(self._entries)
        avg_respect = sum(e.respect for e in self._entries) / len(self._entries)
        avg_under = sum(e.understanding for e in self._entries) / len(self._entries)
        avg_wisdom = sum(e.wisdom_shared for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy_received for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_mutual = sum(e.mutual_benefit for e in recent) / len(recent)
            recent_under = sum(e.understanding for e in recent) / len(recent)
        else:
            recent_mutual = 0
            recent_under = 0

        # Isolation penalty
        isolation_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if len(last_90) < 3:
            isolation_penalty = 15

        # Generation variety
        unique_gens = len(set(e.generation for e in self._entries))

        score = (avg_mutual * 25) + (avg_respect * 20) + (avg_under * 15) + (avg_wisdom * 10) + (avg_energy * 10) + (recent_mutual * 10) + (recent_under * 5) + (unique_gens * 2) - isolation_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_mutual_benefit"] = round(sum(e.mutual_benefit for e in self._entries) / len(self._entries), 2)
            self._stats["avg_respect"] = round(sum(e.respect for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_mutual = sum(e.mutual_benefit for e in recent) / len(recent)
                recent_under = sum(e.understanding for e in recent) / len(recent)
                self._stats["isolation_risk"] = recent_mutual < 0.3 and recent_under < 0.3
            else:
                self._stats["isolation_risk"] = True

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intergenerational_bridge_builder")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intergenerational_bridge_builder")

    def _log_entry(self, entry: BridgeEntry):
        try:
            with open(BRIDGE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "generation": entry.generation,
                    "person": entry.person,
                    "interaction_type": entry.interaction_type,
                    "mutual_benefit": entry.mutual_benefit,
                    "respect": entry.respect,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intergenerational_bridge_builder")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ibb_instance: Optional[IntergenerationalBridgeBuilder] = None
_ibb_lock = threading.Lock()


def get_intergenerational_bridge_builder() -> IntergenerationalBridgeBuilder:
    global _ibb_instance
    with _ibb_lock:
        if _ibb_instance is None:
            _ibb_instance = IntergenerationalBridgeBuilder()
        return _ibb_instance
