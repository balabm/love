"""
LOVE Cross-Cultural Bridge Builder — Intercultural Intelligence (Modern AI Pattern)

Most people interact across cultures without awareness. This builder:

1. INTERACTION TRACKING
   - Record cross-cultural moments and their characteristics
   - Track interaction types (observe, adapt, bridge, learn, share, reconcile)
   - Log curiosity, respect, empathy, adaptability, and openness of interactions

2. PATTERN ANALYSIS
   - Identify the user's cultural profile (ignorant, tolerant, developing, fluent)
   - Find interaction patterns that create connection vs misunderstanding
   - Detect chronic cultural blindness and its costs

3. BRIDGE BUILDING
   - Suggest practices for genuine cross-cultural understanding
   - Provide frameworks for cultural humility and adaptation
   - Recommend practices for meaningful cross-cultural connection

4. INTERCULTURAL FLUENCY CULTIVATION
   - Track the correlation between cultural openness and relationship quality
   - Alert when assumptions are replacing inquiry
   - Celebrate moments of genuine cultural bridge-building

Architecture:
- record_interaction(situation, type, curiosity, respect, empathy, adaptability, openness): Log interaction
- get_interaction_stats(): Get interaction pattern analysis
- get_interaction_suggestion(capacity, context): Get suggestion
- get_interaction_score(): Calculate overall interaction health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "cross_cultural_bridge_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTERACTION_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class InteractionEntry:
    """A tracked cross-cultural interaction moment."""
    entry_id: str = ""
    situation: str = ""  # what was the situation
    interaction_type: str = ""  # observe, adapt, bridge, learn, share, reconcile
    curiosity: float = 0.0  # 0-1
    respect: float = 0.0  # 0-1
    empathy: float = 0.0  # 0-1
    adaptability: float = 0.0  # 0-1
    openness: float = 0.0  # 0-1
    humility: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CrossCulturalBridgeBuilder:
    """
    Intelligent cross-cultural bridge builder with blindness detection and intercultural fluency cultivation.
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
            "avg_curiosity": 0.0,
            "avg_empathy": 0.0,
            "blindness_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, situation: str = "", interaction_type: str = "", curiosity: float = 0.0, respect: float = 0.0, empathy: float = 0.0, adaptability: float = 0.0, openness: float = 0.0, humility: float = 0.0, notes: str = "") -> InteractionEntry:
        """Record a cross-cultural interaction moment."""
        entry_id = f"ccb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = InteractionEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            interaction_type=interaction_type or "observe",
            curiosity=curiosity,
            respect=respect,
            empathy=empathy,
            adaptability=adaptability,
            openness=openness,
            humility=humility,
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

    def get_interaction_stats(self) -> Dict[str, Any]:
        """Get interaction pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "curiosity_sum": 0.0, "empathy_sum": 0.0, "openness_sum": 0.0})
        for e in self._entries:
            by_type[e.interaction_type]["count"] += 1
            by_type[e.interaction_type]["curiosity_sum"] += e.curiosity
            by_type[e.interaction_type]["empathy_sum"] += e.empathy
            by_type[e.interaction_type]["openness_sum"] += e.openness

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_curiosity": round(data["curiosity_sum"] / count, 2),
                "avg_empathy": round(data["empathy_sum"] / count, 2),
                "avg_openness": round(data["openness_sum"] / count, 2),
            }

        # Curiosity analysis
        high_cur = [e for e in self._entries if e.curiosity > 0.7]
        low_cur = [e for e in self._entries if e.curiosity < 0.4]
        if high_cur and low_cur:
            high_cur_emp = sum(e.empathy for e in high_cur) / len(high_cur)
            low_cur_emp = sum(e.empathy for e in low_cur) / len(low_cur)
            high_cur_adapt = sum(e.adaptability for e in high_cur) / len(high_cur)
            low_cur_adapt = sum(e.adaptability for e in low_cur) / len(low_cur)
        else:
            high_cur_emp = 0
            low_cur_emp = 0
            high_cur_adapt = 0
            low_cur_adapt = 0

        # Humility analysis
        high_hum = [e for e in self._entries if e.humility > 0.7]
        low_hum = [e for e in self._entries if e.humility < 0.4]
        if high_hum and low_hum:
            high_hum_res = sum(e.respect for e in high_hum) / len(high_hum)
            low_hum_res = sum(e.respect for e in low_hum) / len(low_hum)
        else:
            high_hum_res = 0
            low_hum_res = 0

        # Blindness risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cur = sum(e.curiosity for e in recent) / len(recent)
            recent_open = sum(e.openness for e in recent) / len(recent)
            blindness_risk = recent_cur < 0.3 and recent_open < 0.3
        else:
            blindness_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "curiosity_impact": {
                "high_curiosity_empathy": round(high_cur_emp, 2),
                "low_curiosity_empathy": round(low_cur_emp, 2),
                "high_curiosity_adaptability": round(high_cur_adapt, 2),
                "low_curiosity_adaptability": round(low_cur_adapt, 2),
            },
            "humility_effect": {
                "high_humility_respect": round(high_hum_res, 2),
                "low_humility_respect": round(low_hum_res, 2),
            },
            "blindness_risk": blindness_risk,
            "avg_curiosity": round(sum(e.curiosity for e in self._entries) / len(self._entries), 2),
            "avg_empathy": round(sum(e.empathy for e in self._entries) / len(self._entries), 2),
        }

    def get_interaction_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get interaction suggestion."""
        suggestions = [
            "Most people assume their way is the right way. Their culture is the normal one. Their customs are the default. And they wonder why they can't connect. Why they offend without meaning to. Why they misread signals. The answer is cultural blindness. And it is the default state of humanity.",
            "Assume nothing. Not politeness. Not rudeness. Not intention. Not meaning. Ask. Observe. Learn. The person who assumes is the person who misunderstands. The person who inquires is the person who bridges.",
            "Listen more than you speak. In every culture. But especially in ones you don't understand. The person who dominates the conversation dominates their own learning. The person who listens dominates their own growth.",
            "Learn the cultural rules. Not to judge them. To understand them. Why do they bow? Why do they not make eye contact? Why do they speak indirectly? Why do they value group over individual? Every custom has a reason. Every reason has a history. Every history has a humanity.",
            "Apologize when you don't know. Not defensively. Curiously. 'I don't know your customs. Please teach me.' That is not weakness. That is respect. And respect is the foundation of every bridge.",
            "Find common ground. Not by ignoring differences. By acknowledging them. 'We are different. And that is interesting. What do we share?' Shared humanity. Shared fears. Shared hopes. Shared loves. These exist across every culture. Find them.",
            "Adapt your behavior. Not your values. You don't have to agree with everything. But you do have to respect it. The person who adapts their behavior while holding their values is the person who can move between worlds.",
            "Celebrate differences. Not tolerate them. Tolerance is the minimum. Celebration is the maximum. The food. The music. The stories. The wisdom. The perspectives. These are gifts. Not threats. Receive them.",
            "Be patient with yourself. You will make mistakes. You will offend. You will misunderstand. This is normal. This is learning. The person who never makes cultural mistakes never takes cultural risks. And the person who never takes risks never builds bridges.",
            "The person who builds cross-cultural bridges is not just a good traveler. They're a good human. They understand that the world is bigger than their experience. That there are many ways to be right. Many ways to be good. Many ways to be human. And they choose to learn them all."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One question asked. One assumption questioned. One custom learned. One apology made. One difference celebrated. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A cultural rule learned. An adaptation made. A bridge built. A misunderstanding repaired. Medium intercultural fluency."
        else:
            capacity_note = "Good capacity. Deep cross-cultural work. A systematic practice of curiosity, humility, respect, and bridge-building. You have the strength to connect across any divide."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Cross-cultural bridge building is not about being politically correct. It's about being genuinely curious. Most people interact with other cultures from a position of ignorance. They don't know the customs. They don't understand the values. They don't recognize the signals. And they don't ask. They assume. They judge. They misread. And they wonder why they can't connect. The work of cross-cultural bridge building is about understanding that every culture is a complete, coherent, meaningful system of being human. That there is no single right way to be human. That diversity is not a problem to be solved but a richness to be explored. And that the person who approaches cultural differences with genuine curiosity, humility, and respect is the person who can build bridges that no wall can break."
        }

    def get_interaction_score(self) -> int:
        """Calculate overall interaction health (0-100)."""
        if not self._entries:
            return 25

        avg_cur = sum(e.curiosity for e in self._entries) / len(self._entries)
        avg_res = sum(e.respect for e in self._entries) / len(self._entries)
        avg_emp = sum(e.empathy for e in self._entries) / len(self._entries)
        avg_adapt = sum(e.adaptability for e in self._entries) / len(self._entries)
        avg_open = sum(e.openness for e in self._entries) / len(self._entries)
        avg_hum = sum(e.humility for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cur = sum(e.curiosity for e in recent) / len(recent)
            recent_open = sum(e.openness for e in recent) / len(recent)
        else:
            recent_cur = 0
            recent_open = 0

        # Blindness penalty
        blind_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cur_30 = sum(e.curiosity for e in last_30) / len(last_30)
            recent_open_30 = sum(e.openness for e in last_30) / len(last_30)
            if recent_cur_30 < 0.3 and recent_open_30 < 0.3:
                blind_penalty = 15

        # Type variety
        unique_types = len(set(e.interaction_type for e in self._entries))

        score = (avg_cur * 20) + (avg_res * 15) + (avg_emp * 15) + (avg_adapt * 15) + (avg_open * 15) + (avg_hum * 15) + (recent_cur * 5) + (recent_open * 5) + (unique_types * 2) - blind_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_curiosity"] = round(sum(e.curiosity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_empathy"] = round(sum(e.empathy for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cur = sum(e.curiosity for e in recent) / len(recent)
                recent_open = sum(e.openness for e in recent) / len(recent)
                self._stats["blindness_risk"] = recent_cur < 0.3 and recent_open < 0.3
            else:
                self._stats["blindness_risk"] = False

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

    def _log_entry(self, entry: InteractionEntry):
        try:
            with open(INTERACTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "interaction_type": entry.interaction_type,
                    "curiosity": entry.curiosity,
                    "empathy": entry.empathy,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ccb_instance: Optional[CrossCulturalBridgeBuilder] = None
_ccb_lock = threading.Lock()


def get_cross_cultural_bridge_builder() -> CrossCulturalBridgeBuilder:
    global _ccb_instance
    with _ccb_lock:
        if _ccb_instance is None:
            _ccb_instance = CrossCulturalBridgeBuilder()
        return _ccb_instance
