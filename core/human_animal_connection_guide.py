"""
LOVE Human-Animal Connection Guide — Biophilia Intelligence (Modern AI Pattern)

Most people ignore animals. This guide:

1. CONNECTION TRACKING
   - Record human-animal connection moments and their characteristics
   - Track connection types (wildlife, domestic, farm, marine, bird, insect)
   - Log wonder, respect, reciprocity, and expansion of connection

2. PATTERN ANALYSIS
   - Identify the user's connection profile (alienated, occasional, developing, kinship)
   - Find connection patterns that create belonging vs separation
   - Detect chronic human-animal disconnection and its costs

3. CONNECTION BUILDING
   - Suggest practices for expanding relationship with animals
   - Provide frameworks for ethical wildlife interaction
   - Recommend practices for understanding human role in animal lives

4. BIOPHILIA CULTIVATION
   - Track the correlation between animal connection and wellbeing
   - Alert when nature disconnection is becoming the default
   - Celebrate moments of genuine interspecies kinship

Architecture:
- record_connection(animal, type, wonder, respect, reciprocity, expansion): Log connection
- get_connection_stats(): Get connection pattern analysis
- get_connection_suggestion(capacity, context): Get suggestion
- get_connection_score(): Calculate overall connection health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "human_animal_connection_guide"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONNECTION_LOG = DATA_DIR / "connections.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ConnectionEntry:
    """A tracked human-animal connection moment."""
    entry_id: str = ""
    animal: str = ""  # what animal was connected with
    connection_type: str = ""  # wildlife, domestic, farm, marine, bird, insect
    wonder: float = 0.0  # 0-1
    respect: float = 0.0  # 0-1
    reciprocity: float = 0.0  # 0-1
    expansion: float = 0.0  # 0-1
    ethical: float = 0.0  # 0-1 was interaction ethical?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HumanAnimalConnectionGuide:
    """
    Intelligent human-animal connection guide with disconnection detection and biophilia cultivation.
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
            "avg_wonder": 0.0,
            "avg_respect": 0.0,
            "disconnection_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_connection(self, animal: str = "", connection_type: str = "", wonder: float = 0.0, respect: float = 0.0, reciprocity: float = 0.0, expansion: float = 0.0, ethical: float = 0.0, notes: str = "") -> ConnectionEntry:
        """Record a human-animal connection moment."""
        entry_id = f"hac_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ConnectionEntry(
            entry_id=entry_id,
            animal=animal or "unspecified",
            connection_type=connection_type or "wildlife",
            wonder=wonder,
            respect=respect,
            reciprocity=reciprocity,
            expansion=expansion,
            ethical=ethical,
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

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "wonder_sum": 0.0, "respect_sum": 0.0, "expansion_sum": 0.0})
        for e in self._entries:
            by_type[e.connection_type]["count"] += 1
            by_type[e.connection_type]["wonder_sum"] += e.wonder
            by_type[e.connection_type]["respect_sum"] += e.respect
            by_type[e.connection_type]["expansion_sum"] += e.expansion

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_wonder": round(data["wonder_sum"] / count, 2),
                "avg_respect": round(data["respect_sum"] / count, 2),
                "avg_expansion": round(data["expansion_sum"] / count, 2),
            }

        # Wonder analysis
        high_won = [e for e in self._entries if e.wonder > 0.7]
        low_won = [e for e in self._entries if e.wonder < 0.4]
        if high_won and low_won:
            high_won_exp = sum(e.expansion for e in high_won) / len(high_won)
            low_won_exp = sum(e.expansion for e in low_won) / len(low_won)
            high_won_resp = sum(e.respect for e in high_won) / len(high_won)
            low_won_resp = sum(e.respect for e in low_won) / len(low_won)
        else:
            high_won_exp = 0
            low_won_exp = 0
            high_won_resp = 0
            low_won_resp = 0

        # Ethical analysis
        high_eth = [e for e in self._entries if e.ethical > 0.7]
        low_eth = [e for e in self._entries if e.ethical < 0.4]
        if high_eth and low_eth:
            high_eth_won = sum(e.wonder for e in high_eth) / len(high_eth)
            low_eth_won = sum(e.wonder for e in low_eth) / len(low_eth)
        else:
            high_eth_won = 0
            low_eth_won = 0

        # Disconnection risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_won = sum(e.wonder for e in recent) / len(recent)
            recent_resp = sum(e.respect for e in recent) / len(recent)
            disconnection_risk = recent_won < 0.3 and recent_resp < 0.3
        else:
            disconnection_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "wonder_impact": {
                "high_wonder_expansion": round(high_won_exp, 2),
                "low_wonder_expansion": round(low_won_exp, 2),
                "high_wonder_respect": round(high_won_resp, 2),
                "low_wonder_respect": round(low_won_resp, 2),
            },
            "ethical_effect": {
                "high_ethical_wonder": round(high_eth_won, 2),
                "low_ethical_wonder": round(low_eth_won, 2),
            },
            "disconnection_risk": disconnection_risk,
            "avg_wonder": round(sum(e.wonder for e in self._entries) / len(self._entries), 2),
            "avg_respect": round(sum(e.respect for e in self._entries) / len(self._entries), 2),
        }

    def get_connection_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get connection suggestion."""
        suggestions = [
            "You are not separate from nature. You are nature. The human-animal divide is a construct. A story we tell ourselves. But the truth is simpler: we are all alive. We are all related. We are all kin.",
            "Notice the animals around you. The birds in the trees. The squirrels on the fence. The insects in the grass. The stray cat on the street. They're not background. They're neighbors. Acknowledge them.",
            "Feed the birds. Put out water. Plant flowers for bees. Create a small habitat. You don't need a farm. A windowsill. A balcony. A yard corner. Small gestures create big connections.",
            "Visit a farm. Or a sanctuary. Or a zoo that cares for animals well. See them up close. Watch them be. Not performing. Not entertaining. Just being. That's the real animal. The one that exists when no one is watching.",
            "Watch wildlife documentaries. Not for entertainment. For education. For connection. For understanding the lives of beings you'll never meet but share a planet with. Knowledge creates compassion.",
            "Don't exploit animals for your pleasure. The circus. The rodeo. The poorly run petting zoo. The tourist elephant ride. If the animal is not free to leave, question whether your pleasure is worth their suffering.",
            "Eat less meat. Or no meat. Not because animals are equal to humans. But because they're alive. They feel. They suffer. And your choices have consequences. Every meal is a vote. Vote for less suffering.",
            "Rescue if you can. Adopt if you can. Foster if you can. Volunteer if you can. Donate if you can. There are animals who need you. And helping them connects you to something larger than yourself.",
            "Sit in nature and just be. Let animals come to you. Or not. It doesn't matter. What matters is that you're there. Available. Present. In their world. Not taking. Just being.",
            "The person who feels kinship with animals is not sentimental. They're awake. They see the web of life. They understand their place in it. And they act from that understanding. That's wisdom."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One bird noticed. One insect spared. One moment of seeing an animal as a being. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A wildlife observation. A habitat created. An ethical choice made. A donation given. Medium connection."
        else:
            capacity_note = "Good capacity. Deep biophilia work. A systematic practice of kinship, respect, and ethical relationship with animals. You have the strength to be a good ancestor."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Human-animal connection is the original relationship. Before cities. Before agriculture. Before language. We were animals among animals. And we still are. But most people have forgotten this. They live in concrete boxes. They eat food from factories. They see animals as resources or entertainment. And they wonder why they feel disconnected. Why they feel lonely. Why they feel like something is missing. The work of human-animal connection guidance is about rekindling the ancient bond between human and animal. About seeing animals as kin, not commodities. About understanding that our wellbeing is connected to theirs. About recognizing that the way we treat animals is a mirror of who we are. And about creating a life where human-animal connection is not an afterthought but a foundation. Because the person who lives in kinship with animals lives in kinship with life itself."
        }

    def get_connection_score(self) -> int:
        """Calculate overall connection health (0-100)."""
        if not self._entries:
            return 25

        avg_won = sum(e.wonder for e in self._entries) / len(self._entries)
        avg_resp = sum(e.respect for e in self._entries) / len(self._entries)
        avg_recip = sum(e.reciprocity for e in self._entries) / len(self._entries)
        avg_exp = sum(e.expansion for e in self._entries) / len(self._entries)
        avg_eth = sum(e.ethical for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_won = sum(e.wonder for e in recent) / len(recent)
            recent_resp = sum(e.respect for e in recent) / len(recent)
        else:
            recent_won = 0
            recent_resp = 0

        # Disconnection penalty
        dis_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_won_30 = sum(e.wonder for e in last_30) / len(last_30)
            recent_resp_30 = sum(e.respect for e in last_30) / len(last_30)
            if recent_won_30 < 0.3 and recent_resp_30 < 0.3:
                dis_penalty = 15

        # Type variety
        unique_types = len(set(e.connection_type for e in self._entries))

        score = (avg_won * 25) + (avg_resp * 20) + (avg_recip * 10) + (avg_exp * 10) + (avg_eth * 10) + (recent_won * 5) + (recent_resp * 5) + (unique_types * 2) - dis_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_wonder"] = round(sum(e.wonder for e in self._entries) / len(self._entries), 2)
            self._stats["avg_respect"] = round(sum(e.respect for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_won = sum(e.wonder for e in recent) / len(recent)
                recent_resp = sum(e.respect for e in recent) / len(recent)
                self._stats["disconnection_risk"] = recent_won < 0.3 and recent_resp < 0.3
            else:
                self._stats["disconnection_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.human_animal_connection_guide")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.human_animal_connection_guide")

    def _log_entry(self, entry: ConnectionEntry):
        try:
            with open(CONNECTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "animal": entry.animal,
                    "connection_type": entry.connection_type,
                    "wonder": entry.wonder,
                    "respect": entry.respect,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.human_animal_connection_guide")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hac_instance: Optional[HumanAnimalConnectionGuide] = None
_hac_lock = threading.Lock()


def get_human_animal_connection_guide() -> HumanAnimalConnectionGuide:
    global _hac_instance
    with _hac_lock:
        if _hac_instance is None:
            _hac_instance = HumanAnimalConnectionGuide()
        return _hac_instance
