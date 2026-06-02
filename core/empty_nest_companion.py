"""
LOVE Empty Nest Companion — Life Stage Intelligence (Modern AI Pattern)

Most parents struggle when children leave. This companion:

1. NEST TRACKING
   - Record empty nest moments and their characteristics
   - Track nest types (grief, rediscovery, relationship, identity, purpose, joy)
   - Log grief, hope, rediscovery, relationship, identity, and growth

2. PATTERN ANALYSIS
   - Identify the user's nest profile (lost, grieving, developing, thriving)
   - Find nest patterns that create growth vs stagnation
   - Detect chronic loss-focus and its costs

3. COMPANIONSHIP BUILDING
   - Suggest practices for navigating the empty nest
   - Provide frameworks for rediscovery and reinvention
   - Recommend practices for relationship renewal

4. EMPTY NEST THRIVING CULTIVATION
   - Track the correlation between rediscovery and wellbeing
   - Alert when grief is replacing growth
   - Celebrate moments of genuine nest flourishing

Architecture:
- record_nest(moment, type, grief, hope, rediscovery, relationship, identity, growth): Log nest
- get_nest_stats(): Get nest pattern analysis
- get_nest_suggestion(capacity, context): Get suggestion
- get_nest_score(): Calculate overall nest health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "empty_nest_companion"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NEST_LOG = DATA_DIR / "nests.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class NestEntry:
    """A tracked empty nest moment."""
    entry_id: str = ""
    moment: str = ""  # what was the moment
    nest_type: str = ""  # grief, rediscovery, relationship, identity, purpose, joy
    grief: float = 0.0  # 0-1
    hope: float = 0.0  # 0-1
    rediscovery: float = 0.0  # 0-1
    relationship: float = 0.0  # 0-1
    identity: float = 0.0  # 0-1
    growth: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EmptyNestCompanion:
    """
    Intelligent empty nest companion with stagnation detection and empty nest thriving cultivation.
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
            "avg_grief": 0.0,
            "avg_growth": 0.0,
            "stagnation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_nest(self, moment: str = "", nest_type: str = "", grief: float = 0.0, hope: float = 0.0, rediscovery: float = 0.0, relationship: float = 0.0, identity: float = 0.0, growth: float = 0.0, courage: float = 0.0, notes: str = "") -> NestEntry:
        """Record an empty nest moment."""
        entry_id = f"nst_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = NestEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            nest_type=nest_type or "grief",
            grief=grief,
            hope=hope,
            rediscovery=rediscovery,
            relationship=relationship,
            identity=identity,
            growth=growth,
            courage=courage,
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

    def get_nest_stats(self) -> Dict[str, Any]:
        """Get nest pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "grief_sum": 0.0, "growth_sum": 0.0, "hope_sum": 0.0})
        for e in self._entries:
            by_type[e.nest_type]["count"] += 1
            by_type[e.nest_type]["grief_sum"] += e.grief
            by_type[e.nest_type]["growth_sum"] += e.growth
            by_type[e.nest_type]["hope_sum"] += e.hope

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_grief": round(data["grief_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_hope": round(data["hope_sum"] / count, 2),
            }

        # Grief analysis
        high_grief = [e for e in self._entries if e.grief > 0.7]
        low_grief = [e for e in self._entries if e.grief < 0.4]
        if high_grief and low_grief:
            high_grief_growth = sum(e.growth for e in high_grief) / len(high_grief)
            low_grief_growth = sum(e.growth for e in low_grief) / len(low_grief)
            high_grief_hope = sum(e.hope for e in high_grief) / len(high_grief)
            low_grief_hope = sum(e.hope for e in low_grief) / len(low_grief)
        else:
            high_grief_growth = 0
            low_grief_growth = 0
            high_grief_hope = 0
            low_grief_hope = 0

        # Rediscovery analysis
        high_red = [e for e in self._entries if e.rediscovery > 0.7]
        low_red = [e for e in self._entries if e.rediscovery < 0.4]
        if high_red and low_red:
            high_red_growth = sum(e.growth for e in high_red) / len(high_red)
            low_red_growth = sum(e.growth for e in low_red) / len(low_red)
        else:
            high_red_growth = 0
            low_red_growth = 0

        # Stagnation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_grief = sum(e.grief for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
            stagnation_risk = recent_grief > 0.7 and recent_growth < 0.3
        else:
            stagnation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "grief_impact": {
                "high_grief_growth": round(high_grief_growth, 2),
                "low_grief_growth": round(low_grief_growth, 2),
                "high_grief_hope": round(high_grief_hope, 2),
                "low_grief_hope": round(low_grief_hope, 2),
            },
            "rediscovery_effect": {
                "high_rediscovery_growth": round(high_red_growth, 2),
                "low_rediscovery_growth": round(low_red_growth, 2),
            },
            "stagnation_risk": stagnation_risk,
            "avg_grief": round(sum(e.grief for e in self._entries) / len(self._entries), 2),
            "avg_growth": round(sum(e.growth for e in self._entries) / len(self._entries), 2),
        }

    def get_nest_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get nest suggestion."""
        suggestions = [
            "Most parents struggle when their children leave. The house is quiet. Too quiet. The routines that structured decades are gone. The purpose that defined years has vanished. And they wonder who they are without the role that consumed them. This is the empty nest. And it is one of the most profound transitions a person can face.",
            "Grieve. Really grieve. Not quickly. Not quietly. Not stoically. Grieve the daily presence. The noise. The chaos. The mess. The hugs. The arguments. The meals together. The goodnights. Grieve what was. Because it was beautiful. And it is gone. And pretending it isn't hurts more than feeling it.",
            "Your children leaving is not a rejection. It's a success. You raised them to be independent. To be capable. To leave. That was the goal. The fact that they left means you did your job. Remember that. When the quiet hurts. Remember that the silence is proof of your success.",
            "Rediscover yourself. Not the parent. The person. The one who existed before children. Who had hobbies. Interests. Dreams. Friends. A life. That person is still there. Buried under years of selflessness. Dig them up. Gently. Patiently. They're waiting.",
            "Renew your relationship. With your partner. With yourself. With your friends. The relationship that was neglected because parenting consumed everything. Date your partner again. Call your friends. Spend time with yourself. The person who only gave for years now gets to receive.",
            "Reimagine your home. Not as a family house. As YOUR house. Paint the walls. Move the furniture. Create a space that's yours. The room that was a child's bedroom can be your studio. Your gym. Your sanctuary. Your home can finally reflect you. Not your role.",
            "Find new purpose. Not to replace parenting. To complement it. Volunteering. Mentoring. Creating. Learning. Traveling. Contributing. The world needs what you have. Your experience. Your wisdom. Your time. Your love. Find where it can flow now.",
            "Be patient. This transition takes years. Not weeks. Not months. Years. You don't become a new person overnight. You grieve. You wander. You experiment. You fail. You try again. And slowly, gradually, you become someone new. Someone who is not just a parent. But a whole person.",
            "Stay connected. But differently. Text instead of tuck in. Call instead of cook for. Visit instead of live with. Your relationship with your children evolves. It doesn't end. It becomes something new. Something adult. Something beautiful in its own way. But different.",
            "The person who thrives in the empty nest is not someone who ignores the grief. They're someone who honors it. Who grieves fully. And then who chooses to grow. To rediscover. To reinvent. To become more themselves than they ever were. The empty nest is not an ending. It's a beginning. And beginnings are beautiful. Even when they start with grief."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of grief felt. One small rediscovery. One call to a friend. One new hobby tried. One quiet moment accepted. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A grief ritual. A relationship renewed. A home reimagined. A purpose explored. A new routine found. Medium thriving."
        else:
            capacity_note = "Good capacity. Deep empty nest work. A systematic practice of grief, rediscovery, reinvention, and thriving. You have the strength to flourish in this new chapter."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Empty nest companionship is not about replacing children. It's about rediscovering yourself. Most parents struggle enormously when their children leave. They've spent decades defining themselves through parenting. And when that role diminishes, they feel lost. Grief is natural. Stagnation is dangerous. The work of empty nest companionship is about understanding that this transition is not an ending but a beginning. That grieving is necessary. That rediscovery is possible. That reinvention is available at any age. And that the person who embraces this chapter with courage and openness finds a life that is in many ways richer than the one they left behind."
        }

    def get_nest_score(self) -> int:
        """Calculate overall nest health (0-100)."""
        if not self._entries:
            return 25

        avg_grief = sum(e.grief for e in self._entries) / len(self._entries)
        avg_hope = sum(e.hope for e in self._entries) / len(self._entries)
        avg_red = sum(e.rediscovery for e in self._entries) / len(self._entries)
        avg_rel = sum(e.relationship for e in self._entries) / len(self._entries)
        avg_id = sum(e.identity for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)
        avg_cour = sum(e.courage for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_grief = sum(e.grief for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
        else:
            recent_grief = 0
            recent_growth = 0

        # Stagnation penalty
        stag_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_grief_30 = sum(e.grief for e in last_30) / len(last_30)
            recent_growth_30 = sum(e.growth for e in last_30) / len(last_30)
            if recent_grief_30 > 0.7 and recent_growth_30 < 0.3:
                stag_penalty = 15

        # Type variety
        unique_types = len(set(e.nest_type for e in self._entries))

        score = (avg_hope * 20) + (avg_red * 20) + (avg_rel * 10) + (avg_id * 10) + (avg_growth * 20) + (avg_cour * 15) + (recent_growth * 5) - (recent_grief * 5) + (unique_types * 2) - stag_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_grief"] = round(sum(e.grief for e in self._entries) / len(self._entries), 2)
            self._stats["avg_growth"] = round(sum(e.growth for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_grief = sum(e.grief for e in recent) / len(recent)
                recent_growth = sum(e.growth for e in recent) / len(recent)
                self._stats["stagnation_risk"] = recent_grief > 0.7 and recent_growth < 0.3
            else:
                self._stats["stagnation_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.empty_nest_companion")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.empty_nest_companion")

    def _log_entry(self, entry: NestEntry):
        try:
            with open(NEST_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "nest_type": entry.nest_type,
                    "grief": entry.grief,
                    "growth": entry.growth,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.empty_nest_companion")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_enc_instance: Optional[EmptyNestCompanion] = None
_enc_lock = threading.Lock()


def get_empty_nest_companion() -> EmptyNestCompanion:
    global _enc_instance
    with _enc_lock:
        if _enc_instance is None:
            _enc_instance = EmptyNestCompanion()
        return _enc_instance
