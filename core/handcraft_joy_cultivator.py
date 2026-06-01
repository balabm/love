"""
LOVE Handcraft Joy Cultivator — Manual Creation Intelligence (Modern AI Pattern)

Most people buy instead of make. This cultivator:

1. HANDCRAFT TRACKING
   - Record handcraft moments and their characteristics
   - Track craft types (wood, fiber, clay, paper, metal, food, garden, mixed)
   - Log skill, patience, creativity, beauty, and satisfaction of handcraft

2. PATTERN ANALYSIS
   - Identify the user's craft profile (buyer, beginner, developing, artisan)
   - Find craft patterns that create joy vs frustration
   - Detect chronic buying-instead-of-making and its costs

3. JOY BUILDING
   - Suggest practices for finding joy in manual creation
   - Provide frameworks for skill development and creative expression
   - Recommend practices for slow, intentional making

4. ARTISAN MASTERY CULTIVATION
   - Track the correlation between handcraft practice and life satisfaction
   - Alert when convenience is replacing craft
   - Celebrate moments of genuine handcraft joy

Architecture:
- record_handcraft(item, type, skill, patience, creativity, beauty, satisfaction): Log handcraft
- get_handcraft_stats(): Get handcraft pattern analysis
- get_handcraft_suggestion(capacity, context): Get suggestion
- get_handcraft_score(): Calculate overall handcraft health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "handcraft_joy_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HANDCRAFT_LOG = DATA_DIR / "handcrafts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class HandcraftEntry:
    """A tracked handcraft moment."""
    entry_id: str = ""
    item: str = ""  # what was crafted
    craft_type: str = ""  # wood, fiber, clay, paper, metal, food, garden, mixed
    skill: float = 0.0  # 0-1
    patience: float = 0.0  # 0-1
    creativity: float = 0.0  # 0-1
    beauty: float = 0.0  # 0-1
    satisfaction: float = 0.0  # 0-1
    flow: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HandcraftJoyCultivator:
    """
    Intelligent handcraft joy cultivator with convenience-detection and artisan mastery cultivation.
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
            "avg_satisfaction": 0.0,
            "avg_beauty": 0.0,
            "convenience_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_handcraft(self, item: str = "", craft_type: str = "", skill: float = 0.0, patience: float = 0.0, creativity: float = 0.0, beauty: float = 0.0, satisfaction: float = 0.0, flow: float = 0.0, notes: str = "") -> HandcraftEntry:
        """Record a handcraft moment."""
        entry_id = f"hnd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = HandcraftEntry(
            entry_id=entry_id,
            item=item or "unspecified",
            craft_type=craft_type or "mixed",
            skill=skill,
            patience=patience,
            creativity=creativity,
            beauty=beauty,
            satisfaction=satisfaction,
            flow=flow,
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

    def get_handcraft_stats(self) -> Dict[str, Any]:
        """Get handcraft pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "skill_sum": 0.0, "beauty_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.craft_type]["count"] += 1
            by_type[e.craft_type]["skill_sum"] += e.skill
            by_type[e.craft_type]["beauty_sum"] += e.beauty
            by_type[e.craft_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_skill": round(data["skill_sum"] / count, 2),
                "avg_beauty": round(data["beauty_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Skill analysis
        high_skill = [e for e in self._entries if e.skill > 0.7]
        low_skill = [e for e in self._entries if e.skill < 0.4]
        if high_skill and low_skill:
            high_skill_sat = sum(e.satisfaction for e in high_skill) / len(high_skill)
            low_skill_sat = sum(e.satisfaction for e in low_skill) / len(low_skill)
            high_skill_beaut = sum(e.beauty for e in high_skill) / len(high_skill)
            low_skill_beaut = sum(e.beauty for e in low_skill) / len(low_skill)
        else:
            high_skill_sat = 0
            low_skill_sat = 0
            high_skill_beaut = 0
            low_skill_beaut = 0

        # Flow analysis
        high_flow = [e for e in self._entries if e.flow > 0.7]
        low_flow = [e for e in self._entries if e.flow < 0.4]
        if high_flow and low_flow:
            high_flow_sat = sum(e.satisfaction for e in high_flow) / len(high_flow)
            low_flow_sat = sum(e.satisfaction for e in low_flow) / len(low_flow)
        else:
            high_flow_sat = 0
            low_flow_sat = 0

        # Convenience risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            recent_flow = sum(e.flow for e in recent) / len(recent)
            convenience_risk = recent_sat < 0.3 and recent_flow < 0.3
        else:
            convenience_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "skill_impact": {
                "high_skill_satisfaction": round(high_skill_sat, 2),
                "low_skill_satisfaction": round(low_skill_sat, 2),
                "high_skill_beauty": round(high_skill_beaut, 2),
                "low_skill_beauty": round(low_skill_beaut, 2),
            },
            "flow_effect": {
                "high_flow_satisfaction": round(high_flow_sat, 2),
                "low_flow_satisfaction": round(low_flow_sat, 2),
            },
            "convenience_risk": convenience_risk,
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
            "avg_beauty": round(sum(e.beauty for e in self._entries) / len(self._entries), 2),
        }

    def get_handcraft_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get handcraft suggestion."""
        suggestions = [
            "Most people buy what they could make. They buy bread instead of baking. They buy furniture instead of building. They buy art instead of creating. And they wonder why they feel disconnected. Why they feel powerless. The answer is in their hands. Or rather, not in their hands.",
            "Make something with your hands today. Not with a machine. Not with a service. With your hands. Knead dough. Carve wood. Stitch fabric. Mold clay. Plant seeds. Cook a meal from scratch. The hand that makes is the hand that knows.",
            "Start with something simple. A loaf of bread. A scarf. A shelf. A pot. A drawing. Simple things teach complex truths. About material. About process. About patience. About yourself. Don't start with mastery. Start with making.",
            "Value the imperfect. The handmade is not flawed. It's alive. The machine makes identical. The hand makes unique. The wobble in the pottery. The unevenness in the stitch. The irregularity in the bread. These are signatures. Not mistakes. They say 'a human made this.' And that is beautiful.",
            "Learn from the material. Wood has grain. Clay has memory. Dough has temperament. Fabric has drape. The material teaches. You don't impose on it. You collaborate with it. The person who listens to the material makes better things. And learns more.",
            "Slow down. Handcraft is not fast. It's not efficient. It's not productive. It's slow. Deliberate. Intentional. The slowness is the point. The hand moves at the speed of attention. And attention is the source of joy.",
            "Use your mistakes. The cracked pot becomes a planter. The torn fabric becomes a patch. The burnt bread becomes croutons. The handcraft mistake is not waste. It's material for the next creation. The person who uses their mistakes is the person who never wastes.",
            "Make for someone. Not for sale. Not for show. For someone you love. A meal. A gift. A fix. A garden. The handcraft made with love is the handcraft that matters most. Because love is the best material.",
            "Keep your tools. Care for them. Sharpen them. Clean them. Store them well. Tools are extensions of your hands. And your hands are extensions of your heart. The person who cares for their tools cares for their craft.",
            "The person who cultivates handcraft joy is not just making things. They're making a life. They're saying 'I can create what I need.' They're saying 'I don't have to buy everything.' They're saying 'my hands are capable.' And that is a profound form of freedom."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One simple handcraft. One loaf kneaded. One stitch made. One seed planted. One meal cooked from scratch. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A regular handcraft practice. A skill developing. A mistake embraced. A gift made with hands. Medium artisan joy."
        else:
            capacity_note = "Good capacity. Deep handcraft mastery work. A systematic practice of making, learning, and finding joy in the slow, intentional creation of beautiful, useful things. You have the strength to make what you need."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Handcraft joy cultivation is not about being an artist. It's about being human. Most people have lost touch with their hands. They type. They scroll. They tap. They buy. But they don't make. They don't knead. They don't carve. They don't stitch. They don't plant. And they've lost something essential. The work of handcraft joy cultivation is about understanding that making things with your hands is not a hobby. It's a human need. It's about reconnecting with material. With process. With patience. With imperfection. And with the profound satisfaction of creating something useful and beautiful from raw material. The person who rediscovers handcraft joy is not just making things. They're making themselves whole."
        }

    def get_handcraft_score(self) -> int:
        """Calculate overall handcraft health (0-100)."""
        if not self._entries:
            return 25

        avg_skill = sum(e.skill for e in self._entries) / len(self._entries)
        avg_pat = sum(e.patience for e in self._entries) / len(self._entries)
        avg_creat = sum(e.creativity for e in self._entries) / len(self._entries)
        avg_beaut = sum(e.beauty for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_flow = sum(e.flow for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            recent_flow = sum(e.flow for e in recent) / len(recent)
        else:
            recent_sat = 0
            recent_flow = 0

        # Convenience penalty
        conv_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_sat_30 = sum(e.satisfaction for e in last_30) / len(last_30)
            recent_flow_30 = sum(e.flow for e in last_30) / len(last_30)
            if recent_sat_30 < 0.3 and recent_flow_30 < 0.3:
                conv_penalty = 15

        # Type variety
        unique_types = len(set(e.craft_type for e in self._entries))

        score = (avg_skill * 20) + (avg_pat * 15) + (avg_creat * 15) + (avg_beaut * 15) + (avg_sat * 15) + (avg_flow * 10) + (recent_sat * 5) + (recent_flow * 5) + (unique_types * 2) - conv_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)
            self._stats["avg_beauty"] = round(sum(e.beauty for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_sat = sum(e.satisfaction for e in recent) / len(recent)
                recent_flow = sum(e.flow for e in recent) / len(recent)
                self._stats["convenience_risk"] = recent_sat < 0.3 and recent_flow < 0.3
            else:
                self._stats["convenience_risk"] = False

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

    def _log_entry(self, entry: HandcraftEntry):
        try:
            with open(HANDCRAFT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "item": entry.item,
                    "craft_type": entry.craft_type,
                    "satisfaction": entry.satisfaction,
                    "beauty": entry.beauty,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hjc_instance: Optional[HandcraftJoyCultivator] = None
_hjc_lock = threading.Lock()


def get_handcraft_joy_cultivator() -> HandcraftJoyCultivator:
    global _hjc_instance
    with _hjc_lock:
        if _hjc_instance is None:
            _hjc_instance = HandcraftJoyCultivator()
        return _hjc_instance
