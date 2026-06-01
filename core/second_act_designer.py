"""
LOVE Second Act Designer — Reinvention Intelligence (Modern AI Pattern)

Most people think their best work is behind them. This designer:

1. REINVENTION TRACKING
   - Record reinvention moments and their characteristics
   - Track reinvention types (career, creative, personal, social, contribution, lifestyle)
   - Log vision, courage, skill, network, and momentum of reinvention

2. PATTERN ANALYSIS
   - Identify the user's reinvention profile (stuck, exploring, building, thriving)
   - Find reinvention patterns that create momentum vs stagnation
   - Detect chronic age-based limitation beliefs and their costs

3. DESIGN BUILDING
   - Suggest practices for designing a powerful second act
   - Provide frameworks for reinvention at any age
   - Recommend practices for building new skills and networks

4. SECOND ACT MASTERY CULTIVATION
   - Track the correlation between vision clarity and reinvention success
   - Alert when resignation is replacing ambition
   - Celebrate moments of genuine reinvention breakthrough

Architecture:
- record_reinvention(action, type, vision, courage, skill, network, momentum): Log reinvention
- get_reinvention_stats(): Get reinvention pattern analysis
- get_reinvention_suggestion(capacity, context): Get suggestion
- get_reinvention_score(): Calculate overall reinvention health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "second_act_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REINVENTION_LOG = DATA_DIR / "reinventions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ReinventionEntry:
    """A tracked reinvention moment."""
    entry_id: str = ""
    action: str = ""  # what was the action
    reinvention_type: str = ""  # career, creative, personal, social, contribution, lifestyle
    vision: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    skill: float = 0.0  # 0-1
    network: float = 0.0  # 0-1
    momentum: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SecondActDesigner:
    """
    Intelligent second act designer with resignation detection and second act mastery cultivation.
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
            "avg_vision": 0.0,
            "avg_momentum": 0.0,
            "resignation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_reinvention(self, action: str = "", reinvention_type: str = "", vision: float = 0.0, courage: float = 0.0, skill: float = 0.0, network: float = 0.0, momentum: float = 0.0, joy: float = 0.0, notes: str = "") -> ReinventionEntry:
        """Record a reinvention moment."""
        entry_id = f"act_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ReinventionEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            reinvention_type=reinvention_type or "career",
            vision=vision,
            courage=courage,
            skill=skill,
            network=network,
            momentum=momentum,
            joy=joy,
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

    def get_reinvention_stats(self) -> Dict[str, Any]:
        """Get reinvention pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "vision_sum": 0.0, "momentum_sum": 0.0, "joy_sum": 0.0})
        for e in self._entries:
            by_type[e.reinvention_type]["count"] += 1
            by_type[e.reinvention_type]["vision_sum"] += e.vision
            by_type[e.reinvention_type]["momentum_sum"] += e.momentum
            by_type[e.reinvention_type]["joy_sum"] += e.joy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_vision": round(data["vision_sum"] / count, 2),
                "avg_momentum": round(data["momentum_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Vision analysis
        high_vis = [e for e in self._entries if e.vision > 0.7]
        low_vis = [e for e in self._entries if e.vision < 0.4]
        if high_vis and low_vis:
            high_vis_mom = sum(e.momentum for e in high_vis) / len(high_vis)
            low_vis_mom = sum(e.momentum for e in low_vis) / len(low_vis)
            high_vis_cour = sum(e.courage for e in high_vis) / len(high_vis)
            low_vis_cour = sum(e.courage for e in low_vis) / len(low_vis)
        else:
            high_vis_mom = 0
            low_vis_mom = 0
            high_vis_cour = 0
            low_vis_cour = 0

        # Courage analysis
        high_cour = [e for e in self._entries if e.courage > 0.7]
        low_cour = [e for e in self._entries if e.courage < 0.4]
        if high_cour and low_cour:
            high_cour_mom = sum(e.momentum for e in high_cour) / len(high_cour)
            low_cour_mom = sum(e.momentum for e in low_cour) / len(low_cour)
        else:
            high_cour_mom = 0
            low_cour_mom = 0

        # Resignation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_vis = sum(e.vision for e in recent) / len(recent)
            recent_mom = sum(e.momentum for e in recent) / len(recent)
            resignation_risk = recent_vis < 0.3 and recent_mom < 0.3
        else:
            resignation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "vision_impact": {
                "high_vision_momentum": round(high_vis_mom, 2),
                "low_vision_momentum": round(low_vis_mom, 2),
                "high_vision_courage": round(high_vis_cour, 2),
                "low_vision_courage": round(low_vis_cour, 2),
            },
            "courage_effect": {
                "high_courage_momentum": round(high_cour_mom, 2),
                "low_courage_momentum": round(low_cour_mom, 2),
            },
            "resignation_risk": resignation_risk,
            "avg_vision": round(sum(e.vision for e in self._entries) / len(self._entries), 2),
            "avg_momentum": round(sum(e.momentum for e in self._entries) / len(self._entries), 2),
        }

    def get_reinvention_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get reinvention suggestion."""
        suggestions = [
            "Most people believe their best work is behind them. That their prime is past. That it's too late. That they're too old. That the world has moved on. And they settle. They resign. They coast. And they die with their music still in them. This is the tragedy of the unlived second act.",
            "Your second act is not a consolation prize. It's not what you do when you fail at the first. It's not less important. It's different. More mature. More intentional. More you. The first act was for others. The second act is for yourself. And that makes it more valuable.",
            "Design it. Don't drift into it. What do you want? Not what you should want. Not what others expect. What do YOU want? For the next ten years. The next twenty. The rest of your life. Design it like an architect. Not like a passenger.",
            "Learn new skills. Not to compete with twenty-year-olds. To express yourself. To create what you want to create. To do what you want to do. Skills are tools. And you can acquire tools at any age. The person who stops learning stops living.",
            "Build a new network. Not by replacing the old. By expanding. Find people who are doing what you want to do. At your stage. At your level. With your values. Networks are not just for jobs. They're for inspiration. For collaboration. For community.",
            "Start before you're ready. You will never feel ready. You will never feel qualified. You will never feel the right age. Start anyway. The person who waits to feel ready never starts. The person who starts becomes ready.",
            "Embrace the beginner's mind. In your new domain. You're a beginner. That's not embarrassing. That's brave. Most people won't start because they don't want to be beginners. The person who embraces being a beginner has access to every field. Every skill. Every possibility.",
            "Use your experience. Don't reject it. Everything you've done. Every job. Every relationship. Every failure. Every success. It all informs your second act. Your experience is not baggage. It's fuel.",
            "Be patient. Second acts take time. The first act took decades. The second won't happen in a month. Or a year. But it will happen. If you persist. If you iterate. If you keep moving forward. One step at a time. One day at a time.",
            "The person who designs their second act is not running from their first. They're building on it. They're saying 'I've done that. Now I want to do this.' And that is the most powerful statement anyone can make at any age. The statement of continued creation. Of refusing to be finished. Of choosing to begin again."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One new skill. One new connection. One small step. One vision written. One act begun. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A direction chosen. A skill building. A network growing. A momentum starting. A design emerging. Medium reinvention."
        else:
            capacity_note = "Good capacity. Deep second act design. A systematic practice of vision, courage, skill building, network expansion, and momentum creation. You have the strength to reinvent anything."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Second act design is not about retirement. It's about reinvention. Most people believe their best work is behind them. That their prime is past. That it's too late to start something new. And they settle. They resign. They coast. The work of second act design coaching is about understanding that your second act can be your best act. That it can be more intentional. More authentic. More meaningful. That you can bring everything you've learned to something new. That age is not a limitation but an advantage. And that the person who refuses to be finished - who chooses to begin again - is the person who lives the fullest life."
        }

    def get_reinvention_score(self) -> int:
        """Calculate overall reinvention health (0-100)."""
        if not self._entries:
            return 25

        avg_vis = sum(e.vision for e in self._entries) / len(self._entries)
        avg_cour = sum(e.courage for e in self._entries) / len(self._entries)
        avg_skill = sum(e.skill for e in self._entries) / len(self._entries)
        avg_net = sum(e.network for e in self._entries) / len(self._entries)
        avg_mom = sum(e.momentum for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_vis = sum(e.vision for e in recent) / len(recent)
            recent_mom = sum(e.momentum for e in recent) / len(recent)
        else:
            recent_vis = 0
            recent_mom = 0

        # Resignation penalty
        res_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_vis_30 = sum(e.vision for e in last_30) / len(last_30)
            recent_mom_30 = sum(e.momentum for e in last_30) / len(last_30)
            if recent_vis_30 < 0.3 and recent_mom_30 < 0.3:
                res_penalty = 15

        # Type variety
        unique_types = len(set(e.reinvention_type for e in self._entries))

        score = (avg_vis * 25) + (avg_cour * 15) + (avg_skill * 10) + (avg_net * 10) + (avg_mom * 20) + (avg_joy * 10) + (recent_vis * 5) + (recent_mom * 5) + (unique_types * 2) - res_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_vision"] = round(sum(e.vision for e in self._entries) / len(self._entries), 2)
            self._stats["avg_momentum"] = round(sum(e.momentum for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_vis = sum(e.vision for e in recent) / len(recent)
                recent_mom = sum(e.momentum for e in recent) / len(recent)
                self._stats["resignation_risk"] = recent_vis < 0.3 and recent_mom < 0.3
            else:
                self._stats["resignation_risk"] = False

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

    def _log_entry(self, entry: ReinventionEntry):
        try:
            with open(REINVENTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "reinvention_type": entry.reinvention_type,
                    "vision": entry.vision,
                    "momentum": entry.momentum,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sad_instance: Optional[SecondActDesigner] = None
_sad_lock = threading.Lock()


def get_second_act_designer() -> SecondActDesigner:
    global _sad_instance
    with _sad_lock:
        if _sad_instance is None:
            _sad_instance = SecondActDesigner()
        return _sad_instance
