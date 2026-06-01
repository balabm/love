"""
LOVE Curiosity Cultivator — Wonder Intelligence (Modern AI Pattern)

Most curiosity is crushed by efficiency and certainty. This cultivator:

1. CURIOSITY TRACKING
   - Record curiosity moments and their characteristics
   - Track curiosity types (epistemic, perceptual, interpersonal, existential)
   - Log curiosity triggers and their frequency

2. PATTERN ANALYSIS
   - Identify the user's curiosity profile (broad, deep, social, solitary)
   - Find curiosity killers (fear, certainty, efficiency, judgment)
   - Detect curiosity atrophy and its signs

3. CURIOSITY CULTIVATION
   - Suggest curiosity practices matched to current state
   - Provide question-generating exercises
   - Recommend wonder-inducing experiences

4. LIFELONG LEARNING
   - Track the correlation between curiosity and learning velocity
   - Alert when curiosity is being sacrificed for productivity
   - Celebrate moments of genuine wonder

Architecture:
- record_curiosity(topic, type, depth, trigger): Log curiosity
- get_curiosity_stats(): Get curiosity pattern analysis
- get_curiosity_practice(block, domain): Get practice
- get_curiosity_score(): Calculate overall curiosity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "curiosity_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CURIOSITY_LOG = DATA_DIR / "curiosity.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CuriosityEntry:
    """A tracked curiosity entry."""
    entry_id: str = ""
    topic: str = ""
    curiosity_type: str = ""  # epistemic, perceptual, interpersonal, existential
    depth: float = 0.5  # 0-1
    trigger: str = ""  # what sparked it
    action_taken: str = ""  # what they did about it
    satisfaction: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CuriosityCultivator:
    """
    Intelligent curiosity cultivator with wonder tracking and atrophy detection.
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
            "avg_depth": 0.0,
            "avg_satisfaction": 0.0,
            "dominant_type": "",
            "atrophy_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_curiosity(self, topic: str = "", curiosity_type: str = "", depth: float = 0.5, trigger: str = "", action_taken: str = "", satisfaction: float = 0.5, notes: str = "") -> CuriosityEntry:
        """Record a curiosity entry."""
        entry_id = f"cur_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CuriosityEntry(
            entry_id=entry_id,
            topic=topic or "unspecified",
            curiosity_type=curiosity_type or "epistemic",
            depth=depth,
            trigger=trigger,
            action_taken=action_taken,
            satisfaction=satisfaction,
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

    def get_curiosity_stats(self) -> Dict[str, Any]:
        """Get curiosity pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.curiosity_type]["count"] += 1
            by_type[e.curiosity_type]["depth_sum"] += e.depth
            by_type[e.curiosity_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        dominant_type = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "depth_sum": 0.0})
        for e in self._entries:
            if e.trigger:
                by_trigger[e.trigger]["count"] += 1
                by_trigger[e.trigger]["depth_sum"] += e.depth

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            if count >= 2:
                trigger_stats[tr] = {
                    "count": count,
                    "avg_depth": round(data["depth_sum"] / count, 2),
                }

        best_trigger = max(trigger_stats.items(), key=lambda x: x[1]["avg_depth"]) if trigger_stats else ("", {})

        # Action analysis
        actions = [e for e in self._entries if e.action_taken]
        action_rate = len(actions) / len(self._entries)
        if actions:
            action_satisfaction = sum(e.satisfaction for e in actions) / len(actions)
        else:
            action_satisfaction = 0

        # Atrophy detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if len(self._entries) > 14:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if older:
                recent_depth = sum(e.depth for e in recent) / len(recent) if recent else 0
                older_depth = sum(e.depth for e in older) / len(older)
                atrophy_risk = recent_depth < older_depth * 0.7
            else:
                atrophy_risk = False
        else:
            atrophy_risk = False

        # Topic variety
        unique_topics = len(set(e.topic for e in self._entries))

        # Recent trend
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_satisfaction = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "dominant_type": dominant_type[0],
            "trigger_stats": trigger_stats,
            "best_trigger": best_trigger[0],
            "action_rate": round(action_rate, 2),
            "action_satisfaction": round(action_satisfaction, 2),
            "atrophy_risk": atrophy_risk,
            "unique_topics": unique_topics,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
            "recent_depth": round(recent_depth, 2),
            "recent_satisfaction": round(recent_satisfaction, 2),
        }

    def get_curiosity_practice(self, block: str = "", domain: str = "") -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "fear": [
                "Ask one question you're afraid to ask. The one that makes you feel small. Ask it anyway.",
                "Explore a topic where you might be wrong. What if your certainty is misplaced?",
                "Talk to someone with a radically different worldview. Listen to understand, not to argue.",
            ],
            "certainty": [
                "Find one thing you 'know' and question its source. How do you know? Who told you?",
                "Read a book that challenges your worldview. Not to disagree. To understand.",
                "Ask: 'What would change my mind on this?' If nothing, you're not curious. You're committed.",
            ],
            "efficiency": [
                "Spend 30 minutes learning something with no practical value. Purely for the joy of knowing.",
                "Take the long way home. Notice one new thing. Efficiency is the enemy of discovery.",
                "Wander in a bookstore or library. Pick up something random. Read 10 pages.",
            ],
            "judgment": [
                "Observe without evaluating for 5 minutes. Just notice. No good or bad.",
                "Ask: 'What's interesting about this?' instead of 'What's wrong with this?'",
                "Find something beautiful in a domain you usually dismiss. There is wonder everywhere.",
            ],
            "boredom": [
                "Look closer. The mundane is miraculous at the right scale.",
                "Ask 5 whys about something ordinary. Why is the sky blue? Why do we sleep? Keep digging.",
                "Teach something you know to someone else. Teaching reveals what you don't understand.",
            ],
            "general": [
                "Ask one beautiful question today. A question that has no obvious answer.",
                "Spend 10 minutes in childlike wonder. Ask 'why?' like a 5-year-old.",
                "Follow one thread of curiosity for 20 minutes. No agenda. Just follow.",
            ],
        }

        selected = practices.get(block, practices["general"])

        if block == "fear":
            block_note = "Fear and curiosity cannot coexist. Choose curiosity. It's the braver choice."
        elif block == "certainty":
            block_note = "Certainty is comfortable. Curiosity is brave. The most dangerous person is the one who is certain."
        elif block == "efficiency":
            block_note = "Efficiency optimizes the known. Curiosity discovers the unknown. You need both."
        elif block == "judgment":
            block_note = "Judgment closes doors. Curiosity opens them. You can always judge later."
        elif block == "boredom":
            block_note = "Boredom is not a lack of interesting things. It's a lack of attention. Look closer."
        else:
            block_note = "Curiosity is a muscle. Use it or lose it. Today's question is tomorrow's discovery."

        return {
            "block": block or "none",
            "domain": domain or "general",
            "practice": random.choice(selected),
            "block_note": block_note,
            "principle": "Curiosity is not about knowing more. It's about being comfortable with not knowing. It's the admission that the world is more complex and more interesting than your current model allows. That admission is the beginning of all growth.",
        }

    def get_curiosity_score(self) -> int:
        """Calculate overall curiosity health (0-100)."""
        if not self._entries:
            return 30

        # Depth and satisfaction
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_satisfaction = sum(e.satisfaction for e in self._entries) / len(self._entries)

        # Action rate (curiosity without action atrophies)
        actions = [e for e in self._entries if e.action_taken]
        action_rate = len(actions) / len(self._entries)

        # Topic variety
        unique_topics = len(set(e.topic for e in self._entries))

        # Type variety
        unique_types = len(set(e.curiosity_type for e in self._entries))

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_satisfaction = 0

        # Atrophy penalty
        if len(self._entries) > 14:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if older:
                older_depth = sum(e.depth for e in older) / len(older)
                atrophy_penalty = 10 if recent_depth < older_depth * 0.7 else 0
            else:
                atrophy_penalty = 0
        else:
            atrophy_penalty = 0

        score = (avg_depth * 25) + (avg_satisfaction * 20) + (action_rate * 15) + (unique_topics * 2) + (unique_types * 3) + (recent_depth * 15) + (recent_satisfaction * 10) - atrophy_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            by_type = defaultdict(int)
            for e in self._entries:
                by_type[e.curiosity_type] += 1
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1])
                self._stats["dominant_type"] = dominant[0]

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if len(self._entries) > 14:
                older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
                if older:
                    recent_depth = sum(e.depth for e in recent) / len(recent) if recent else 0
                    older_depth = sum(e.depth for e in older) / len(older)
                    self._stats["atrophy_risk"] = recent_depth < older_depth * 0.7

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

    def _log_entry(self, entry: CuriosityEntry):
        try:
            with open(CURIOSITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "topic": entry.topic,
                    "curiosity_type": entry.curiosity_type,
                    "depth": entry.depth,
                    "trigger": entry.trigger,
                    "action_taken": entry.action_taken,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cc_instance: Optional[CuriosityCultivator] = None
_cc_lock = threading.Lock()


    
def get_curiosity_cultivator() -> CuriosityCultivator:
    global _cc_instance
    with _cc_lock:
        if _cc_instance is None:
            _cc_instance = CuriosityCultivator()
        return _cc_instance
