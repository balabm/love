"""
LOVE Maker Mindset Trainer — Creative Craft Intelligence (Modern AI Pattern)

Most people consume instead of create. This trainer:

1. MAKING TRACKING
   - Record making moments and their characteristics
   - Track make types (build, craft, code, write, cook, grow, fix, design)
   - Log curiosity, resourcefulness, persistence, learning, and joy of making

2. PATTERN ANALYSIS
   - Identify the user's maker profile (consumer, dabbler, developing, prolific)
   - Find making patterns that create flow vs frustration
   - Detect chronic consumption without creation and its costs

3. MINDSET BUILDING
   - Suggest practices for cultivating a maker mentality
   - Provide frameworks for learning by doing
   - Recommend practices for embracing the creative struggle

4. MAKER MASTERY CULTIVATION
   - Track the correlation between making practice and creative confidence
   - Alert when watching is replacing doing
   - Celebrate moments of genuine maker flow

Architecture:
- record_make(creation, type, curiosity, resourcefulness, persistence, learning, joy): Log make
- get_make_stats(): Get make pattern analysis
- get_make_suggestion(capacity, context): Get suggestion
- get_make_score(): Calculate overall make health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "maker_mindset_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAKE_LOG = DATA_DIR / "makes.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MakeEntry:
    """A tracked making moment."""
    entry_id: str = ""
    creation: str = ""  # what was made
    make_type: str = ""  # build, craft, code, write, cook, grow, fix, design
    curiosity: float = 0.0  # 0-1
    resourcefulness: float = 0.0  # 0-1
    persistence: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    flow: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MakerMindsetTrainer:
    """
    Intelligent maker mindset trainer with consumption detection and maker mastery cultivation.
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
            "avg_joy": 0.0,
            "consumption_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_make(self, creation: str = "", make_type: str = "", curiosity: float = 0.0, resourcefulness: float = 0.0, persistence: float = 0.0, learning: float = 0.0, joy: float = 0.0, flow: float = 0.0, notes: str = "") -> MakeEntry:
        """Record a making moment."""
        entry_id = f"mkr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = MakeEntry(
            entry_id=entry_id,
            creation=creation or "unspecified",
            make_type=make_type or "craft",
            curiosity=curiosity,
            resourcefulness=resourcefulness,
            persistence=persistence,
            learning=learning,
            joy=joy,
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

    def get_make_stats(self) -> Dict[str, Any]:
        """Get make pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "curiosity_sum": 0.0, "persistence_sum": 0.0, "joy_sum": 0.0})
        for e in self._entries:
            by_type[e.make_type]["count"] += 1
            by_type[e.make_type]["curiosity_sum"] += e.curiosity
            by_type[e.make_type]["persistence_sum"] += e.persistence
            by_type[e.make_type]["joy_sum"] += e.joy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_curiosity": round(data["curiosity_sum"] / count, 2),
                "avg_persistence": round(data["persistence_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Curiosity analysis
        high_cur = [e for e in self._entries if e.curiosity > 0.7]
        low_cur = [e for e in self._entries if e.curiosity < 0.4]
        if high_cur and low_cur:
            high_cur_learn = sum(e.learning for e in high_cur) / len(high_cur)
            low_cur_learn = sum(e.learning for e in low_cur) / len(low_cur)
            high_cur_joy = sum(e.joy for e in high_cur) / len(high_cur)
            low_cur_joy = sum(e.joy for e in low_cur) / len(low_cur)
        else:
            high_cur_learn = 0
            low_cur_learn = 0
            high_cur_joy = 0
            low_cur_joy = 0

        # Flow analysis
        high_flow = [e for e in self._entries if e.flow > 0.7]
        low_flow = [e for e in self._entries if e.flow < 0.4]
        if high_flow and low_flow:
            high_flow_pers = sum(e.persistence for e in high_flow) / len(high_flow)
            low_flow_pers = sum(e.persistence for e in low_flow) / len(low_flow)
        else:
            high_flow_pers = 0
            low_flow_pers = 0

        # Consumption risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cur = sum(e.curiosity for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
            consumption_risk = recent_cur < 0.3 and recent_joy < 0.3
        else:
            consumption_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "curiosity_impact": {
                "high_curiosity_learning": round(high_cur_learn, 2),
                "low_curiosity_learning": round(low_cur_learn, 2),
                "high_curiosity_joy": round(high_cur_joy, 2),
                "low_curiosity_joy": round(low_cur_joy, 2),
            },
            "flow_effect": {
                "high_flow_persistence": round(high_flow_pers, 2),
                "low_flow_persistence": round(low_flow_pers, 2),
            },
            "consumption_risk": consumption_risk,
            "avg_curiosity": round(sum(e.curiosity for e in self._entries) / len(self._entries), 2),
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
        }

    def get_make_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get make suggestion."""
        suggestions = [
            "Most people are consumers. They watch. They buy. They scroll. They consume other people's creations. And they wonder why they feel empty. Why they feel powerless. Why they feel like spectators in their own lives. The answer is simple: they're not making anything.",
            "Make something today. Not something big. Something small. A meal. A doodle. A note. A fix. A garden bed. Code. Words. Anything. The act of making is the antidote to consumption. It reminds you that you have agency. That you can create. That you're not just a receiver.",
            "Embrace the ugly first draft. Everything you make will be imperfect. That's the point. Perfection is the enemy of making. The person who waits for perfection makes nothing. The person who embraces imperfection makes everything.",
            "Learn by doing. Not by watching. Not by reading. By doing. The person who watches twenty tutorials and makes nothing learns less than the person who makes one thing and fails. Doing is learning. Making is understanding.",
            "Use what you have. Not what you wish you had. The right tool. The better material. The bigger space. These are excuses. The maker makes with what they have. A pen. A knife. A computer. A garden. A kitchen. Start there.",
            "Share your work. Even when it's not perfect. Especially when it's not perfect. Sharing is not about validation. It's about courage. It's about saying 'I made this.' And that statement is powerful. Even if nobody responds. Even if nobody cares. You said it. You made it. You shared it.",
            "Make time for making. Schedule it. Protect it. Not when you have time. When you make time. The person who waits for free time never makes anything. The person who carves out time makes everything.",
            "Connect making to meaning. Don't make for the sake of making. Make because it matters. Because it expresses something. Because it solves something. Because it brings joy. Meaningful making is sustainable making.",
            "Teach what you make. The best way to learn is to teach. The best way to solidify is to share. The best way to grow is to help others grow. The maker who teaches is the maker who masters.",
            "The person who cultivates a maker mindset is not just creative. They're powerful. They understand that the world is not fixed. That it can be changed. That they can change it. One creation at a time. One fix at a time. One meal at a time. One word at a time. That is the maker's power. And it is available to everyone."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small creation. One ugly first draft. One thing made with what you have. One moment of making instead of consuming. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A regular making practice. A failure embraced. A skill learned by doing. A creation shared. Medium maker mindset."
        else:
            capacity_note = "Good capacity. Deep maker work. A systematic practice of creating, learning, failing, and sharing. You have the strength to change the world one creation at a time."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Maker mindset training is not about being artistic. It's about being active. Most people live their lives as consumers. They watch other people create. They buy other people's products. They scroll through other people's lives. And they feel empty. They feel powerless. They feel like spectators. The work of maker mindset training is about understanding that the human default is to make. That we are creators by nature. That the act of making is not a special talent. It's a fundamental capability. And that the person who rediscovers their maker mindset is not just more creative. They're more alive. They're more engaged. They're more powerful. Because they understand that they don't have to accept the world as it is. They can make it different. One creation at a time."
        }

    def get_make_score(self) -> int:
        """Calculate overall make health (0-100)."""
        if not self._entries:
            return 25

        avg_cur = sum(e.curiosity for e in self._entries) / len(self._entries)
        avg_res = sum(e.resourcefulness for e in self._entries) / len(self._entries)
        avg_pers = sum(e.persistence for e in self._entries) / len(self._entries)
        avg_learn = sum(e.learning for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_flow = sum(e.flow for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cur = sum(e.curiosity for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
        else:
            recent_cur = 0
            recent_joy = 0

        # Consumption penalty
        cons_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cur_30 = sum(e.curiosity for e in last_30) / len(last_30)
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            if recent_cur_30 < 0.3 and recent_joy_30 < 0.3:
                cons_penalty = 15

        # Type variety
        unique_types = len(set(e.make_type for e in self._entries))

        score = (avg_cur * 25) + (avg_res * 10) + (avg_pers * 15) + (avg_learn * 10) + (avg_joy * 15) + (avg_flow * 15) + (recent_cur * 5) + (recent_joy * 5) + (unique_types * 2) - cons_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_curiosity"] = round(sum(e.curiosity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cur = sum(e.curiosity for e in recent) / len(recent)
                recent_joy = sum(e.joy for e in recent) / len(recent)
                self._stats["consumption_risk"] = recent_cur < 0.3 and recent_joy < 0.3
            else:
                self._stats["consumption_risk"] = False

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

    def _log_entry(self, entry: MakeEntry):
        try:
            with open(MAKE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "creation": entry.creation,
                    "make_type": entry.make_type,
                    "curiosity": entry.curiosity,
                    "joy": entry.joy,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mmt_instance: Optional[MakerMindsetTrainer] = None
_mmt_lock = threading.Lock()


def get_maker_mindset_trainer() -> MakerMindsetTrainer:
    global _mmt_instance
    with _mmt_lock:
        if _mmt_instance is None:
            _mmt_instance = MakerMindsetTrainer()
        return _mmt_instance
