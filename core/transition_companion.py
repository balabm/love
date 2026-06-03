"""
LOVE Transition Companion — Change Intelligence (Modern AI Pattern)

Most people struggle with change because they resist it. This companion:

1. TRANSITION TRACKING
   - Record transitions and their characteristics
   - Track transition types (career, relationship, location, identity, loss, growth)
   - Log readiness, support, and integration of transitions

2. PATTERN ANALYSIS
   - Identify the user's transition profile (adaptive, resistant, rushing, grieving)
   - Find transition patterns that lead to growth vs stagnation
   - Detect transition avoidance and its costs

3. TRANSITION SUPPORT
   - Suggest practices for navigating change matched to transition type
   - Provide frameworks for letting go and embracing new beginnings
   - Recommend support structures during transitions

4. GROWTH CULTIVATION
   - Track the correlation between transition handling and resilience
   - Alert when change is being resisted beyond its utility
   - Celebrate moments of graceful transition

Architecture:
- record_transition(transition, type, readiness, support, integration): Log transition
- get_transition_stats(): Get transition pattern analysis
- get_transition_suggestion(capacity, context): Get suggestion
- get_transition_score(): Calculate overall transition health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "transition_companion"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRANSITION_LOG = DATA_DIR / "transitions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TransitionEntry:
    """A tracked transition."""
    entry_id: str = ""
    transition: str = ""  # what changed
    transition_type: str = ""  # career, relationship, location, identity, loss, growth
    readiness: float = 0.0  # 0-1
    support: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1
    grief: float = 0.0  # 0-1
    growth: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class TransitionCompanion:
    """
    Intelligent transition companion with readiness detection and growth cultivation.
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
            "avg_readiness": 0.0,
            "avg_integration": 0.0,
            "resistance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_transition(self, transition: str = "", transition_type: str = "", readiness: float = 0.0, support: float = 0.0, integration: float = 0.0, grief: float = 0.0, growth: float = 0.0, notes: str = "") -> TransitionEntry:
        """Record a transition."""
        entry_id = f"trn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = TransitionEntry(
            entry_id=entry_id,
            transition=transition or "unspecified",
            transition_type=transition_type or "general",
            readiness=readiness,
            support=support,
            integration=integration,
            grief=grief,
            growth=growth,
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

    def get_transition_stats(self) -> Dict[str, Any]:
        """Get transition pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "readiness_sum": 0.0, "integration_sum": 0.0, "growth_sum": 0.0})
        for e in self._entries:
            by_type[e.transition_type]["count"] += 1
            by_type[e.transition_type]["readiness_sum"] += e.readiness
            by_type[e.transition_type]["integration_sum"] += e.integration
            by_type[e.transition_type]["growth_sum"] += e.growth

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_readiness": round(data["readiness_sum"] / count, 2),
                "avg_integration": round(data["integration_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
            }

        # Readiness analysis
        high_ready = [e for e in self._entries if e.readiness > 0.7]
        low_ready = [e for e in self._entries if e.readiness < 0.4]
        if high_ready and low_ready:
            high_ready_int = sum(e.integration for e in high_ready) / len(high_ready)
            low_ready_int = sum(e.integration for e in low_ready) / len(low_ready)
            high_ready_growth = sum(e.growth for e in high_ready) / len(high_ready)
            low_ready_growth = sum(e.growth for e in low_ready) / len(low_ready)
        else:
            high_ready_int = 0
            low_ready_int = 0
            high_ready_growth = 0
            low_ready_growth = 0

        # Support analysis
        high_support = [e for e in self._entries if e.support > 0.7]
        low_support = [e for e in self._entries if e.support < 0.4]
        if high_support and low_support:
            high_sup_int = sum(e.integration for e in high_support) / len(high_support)
            low_sup_int = sum(e.integration for e in low_support) / len(low_support)
        else:
            high_sup_int = 0
            low_sup_int = 0

        # Resistance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_ready = sum(e.readiness for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            resistance_risk = recent_ready < 0.3 and recent_int < 0.3
        else:
            resistance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "readiness_impact": {
                "high_readiness_integration": round(high_ready_int, 2),
                "low_readiness_integration": round(low_ready_int, 2),
                "high_readiness_growth": round(high_ready_growth, 2),
                "low_readiness_growth": round(low_ready_growth, 2),
            },
            "support_effect": {
                "high_support_integration": round(high_sup_int, 2),
                "low_support_integration": round(low_sup_int, 2),
            },
            "resistance_risk": resistance_risk,
            "avg_readiness": round(sum(e.readiness for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
        }

    def get_transition_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get transition suggestion."""
        suggestions = [
            "Change is not loss. It's transformation. The caterpillar doesn't die. It becomes a butterfly. Let yourself transform.",
            "Grieve what you're leaving. Even good changes involve loss. The old apartment. The old routine. The old identity. Grief is not weakness. It's honesty.",
            "Create a ritual of goodbye. Write a letter to the past. Visit the old place. Say thank you. Closure is a gift you give yourself.",
            "Don't rush the transition. Transitions have their own timeline. The liminal space between what was and what will be is uncomfortable. And necessary.",
            "Find someone who's been through this. Their experience is a map. Not your map. But a map. Ask them. Listen. Learn.",
            "Keep one thing constant. In change, stability matters. One friend. One routine. One hobby. An anchor in the storm.",
            "Reframe the transition. Not as disruption. As opportunity. As adventure. As the next chapter. The frame changes the experience.",
            "Be patient with yourself. You'll make mistakes in the new situation. You'll feel lost. That's normal. That's transition. It passes.",
            "Transitions reveal who you are. When everything changes, what remains? That's your core. That's what matters. That's what survives.",
            "The only constant is change. The person who resists all change resists life itself. Learn to flow. Learn to adapt. Learn to find the gift in the change."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One breath. One acceptance. One small step into the new. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A ritual of transition. A support conversation. A planned step. Medium adaptation."
        else:
            capacity_note = "Good capacity. Full embrace of change. A new chapter. A bold move. You have the strength to transform."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Transitions are the thread that sews the patches of life into a quilt. Without transitions, life is just a series of disconnected moments. The transition is where growth happens. Where resilience is built. Where the old self is shed and the new self emerges. The person who handles transitions well is not the person who avoids discomfort. They're the person who knows that discomfort is temporary and growth is permanent. They grieve what they leave. They embrace what they find. They know that every ending is a beginning. And they trust themselves to navigate the space between."
        }

    def get_transition_score(self) -> int:
        """Calculate overall transition health (0-100)."""
        if not self._entries:
            return 25

        avg_ready = sum(e.readiness for e in self._entries) / len(self._entries)
        avg_support = sum(e.support for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_grief = sum(e.grief for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_ready = sum(e.readiness for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
        else:
            recent_ready = 0
            recent_int = 0

        # Resistance penalty
        resist_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if last_90:
            recent_ready_90 = sum(e.readiness for e in last_90) / len(last_90)
            recent_int_90 = sum(e.integration for e in last_90) / len(last_90)
            if recent_ready_90 < 0.3 and recent_int_90 < 0.3:
                resist_penalty = 15

        # Type variety
        unique_types = len(set(e.transition_type for e in self._entries))

        score = (avg_ready * 20) + (avg_support * 15) + (avg_int * 25) + (avg_grief * 5) + (avg_growth * 20) + (recent_ready * 5) + (recent_int * 5) + (unique_types * 2) - resist_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_readiness"] = round(sum(e.readiness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integration"] = round(sum(e.integration for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_ready = sum(e.readiness for e in recent) / len(recent)
                recent_int = sum(e.integration for e in recent) / len(recent)
                self._stats["resistance_risk"] = recent_ready < 0.3 and recent_int < 0.3
            else:
                self._stats["resistance_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.transition_companion")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.transition_companion")

    def _log_entry(self, entry: TransitionEntry):
        try:
            with open(TRANSITION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "transition": entry.transition,
                    "transition_type": entry.transition_type,
                    "readiness": entry.readiness,
                    "integration": entry.integration,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.transition_companion")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_tc_instance: Optional[TransitionCompanion] = None
_tc_lock = threading.Lock()


def get_transition_companion() -> TransitionCompanion:
    global _tc_instance
    with _tc_lock:
        if _tc_instance is None:
            _tc_instance = TransitionCompanion()
        return _tc_instance
