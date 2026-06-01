"""
LOVE Life Transition Navigator — Transition Intelligence (Modern AI Pattern)

Most people navigate transitions without a map. This navigator:

1. TRANSITION TRACKING
   - Record transition moments and their characteristics
   - Track transition types (career, relationship, location, health, identity, loss)
   - Log awareness, acceptance, planning, support, and growth of transitions

2. PATTERN ANALYSIS
   - Identify the user's transition profile (resistant, reactive, developing, graceful)
   - Find transition patterns that create growth vs stagnation
   - Detect chronic resistance and its costs

3. NAVIGATION BUILDING
   - Suggest practices for navigating life transitions with grace
   - Provide frameworks for acceptance and planning
   - Recommend practices for finding support and meaning

4. GRACEFUL TRANSITION CULTIVATION
   - Track the correlation between acceptance and transition outcome
   - Alert when resistance is replacing flow
   - Celebrate moments of genuine transition mastery

Architecture:
- record_transition(change, type, awareness, acceptance, planning, support, growth): Log transition
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

DATA_DIR = Path(__file__).parent.parent / "data" / "life_transition_navigator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRANSITION_LOG = DATA_DIR / "transitions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TransitionEntry:
    """A tracked transition moment."""
    entry_id: str = ""
    change: str = ""  # what was the change
    transition_type: str = ""  # career, relationship, location, health, identity, loss
    awareness: float = 0.0  # 0-1
    acceptance: float = 0.0  # 0-1
    planning: float = 0.0  # 0-1
    support: float = 0.0  # 0-1
    growth: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LifeTransitionNavigator:
    """
    Intelligent life transition navigator with resistance detection and graceful transition cultivation.
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
            "avg_acceptance": 0.0,
            "avg_growth": 0.0,
            "resistance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_transition(self, change: str = "", transition_type: str = "", awareness: float = 0.0, acceptance: float = 0.0, planning: float = 0.0, support: float = 0.0, growth: float = 0.0, courage: float = 0.0, notes: str = "") -> TransitionEntry:
        """Record a transition moment."""
        entry_id = f"trn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = TransitionEntry(
            entry_id=entry_id,
            change=change or "unspecified",
            transition_type=transition_type or "career",
            awareness=awareness,
            acceptance=acceptance,
            planning=planning,
            support=support,
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

    def get_transition_stats(self) -> Dict[str, Any]:
        """Get transition pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "acceptance_sum": 0.0, "planning_sum": 0.0, "growth_sum": 0.0})
        for e in self._entries:
            by_type[e.transition_type]["count"] += 1
            by_type[e.transition_type]["acceptance_sum"] += e.acceptance
            by_type[e.transition_type]["planning_sum"] += e.planning
            by_type[e.transition_type]["growth_sum"] += e.growth

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_acceptance": round(data["acceptance_sum"] / count, 2),
                "avg_planning": round(data["planning_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
            }

        # Acceptance analysis
        high_acc = [e for e in self._entries if e.acceptance > 0.7]
        low_acc = [e for e in self._entries if e.acceptance < 0.4]
        if high_acc and low_acc:
            high_acc_growth = sum(e.growth for e in high_acc) / len(high_acc)
            low_acc_growth = sum(e.growth for e in low_acc) / len(low_acc)
            high_acc_plan = sum(e.planning for e in high_acc) / len(high_acc)
            low_acc_plan = sum(e.planning for e in low_acc) / len(low_acc)
        else:
            high_acc_growth = 0
            low_acc_growth = 0
            high_acc_plan = 0
            low_acc_plan = 0

        # Support analysis
        high_sup = [e for e in self._entries if e.support > 0.7]
        low_sup = [e for e in self._entries if e.support < 0.4]
        if high_sup and low_sup:
            high_sup_growth = sum(e.growth for e in high_sup) / len(high_sup)
            low_sup_growth = sum(e.growth for e in low_sup) / len(low_sup)
        else:
            high_sup_growth = 0
            low_sup_growth = 0

        # Resistance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_acc = sum(e.acceptance for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
            resistance_risk = recent_acc < 0.3 and recent_growth < 0.3
        else:
            resistance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "acceptance_impact": {
                "high_acceptance_growth": round(high_acc_growth, 2),
                "low_acceptance_growth": round(low_acc_growth, 2),
                "high_acceptance_planning": round(high_acc_plan, 2),
                "low_acceptance_planning": round(low_acc_plan, 2),
            },
            "support_effect": {
                "high_support_growth": round(high_sup_growth, 2),
                "low_support_growth": round(low_sup_growth, 2),
            },
            "resistance_risk": resistance_risk,
            "avg_acceptance": round(sum(e.acceptance for e in self._entries) / len(self._entries), 2),
            "avg_growth": round(sum(e.growth for e in self._entries) / len(self._entries), 2),
        }

    def get_transition_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get transition suggestion."""
        suggestions = [
            "Most people resist transitions. They cling to what was. They fear what will be. They ignore what is. And they wonder why they feel stuck. Why they feel lost. Why they feel like they're drowning in change. The answer is simple: they're fighting the current. And the current always wins.",
            "Acceptance is not surrender. It's acknowledgment. It's saying 'this is happening.' Not 'I like it.' Not 'I chose it.' Just 'this is real.' And that acknowledgment is the foundation of every successful transition. You cannot navigate what you refuse to see.",
            "Grieve what you leave. Even good changes involve loss. A new job means leaving colleagues. A new city means leaving places. A new relationship means leaving solitude. Grief is not weakness. It's honesty. Honor what was. Then move forward.",
            "Plan what you can. Accept what you can't. Some transitions are chosen. Some are forced. Some you can prepare for. Some you can't. Plan the parts you control. Release the parts you don't. Control is an illusion anyway. But planning gives you ground to stand on.",
            "Find your people. Transitions are not solo journeys. Even if you're physically alone. Reach out. Talk. Share. Ask for help. The person who navigates alone takes longer. Suffers more. And learns less. Community is not a luxury. It's a necessity.",
            "Notice the growth. Not immediately. Eventually. Look back at who you were before the transition. Look at who you are now. What did you learn? What did you discover? What did you gain? Growth is invisible in the moment. Obvious in retrospect.",
            "Be patient with yourself. Transitions have their own timeline. Not yours. Some are quick. Some take years. Some never really end. They just become the new normal. Don't rush. Don't compare. Don't judge your progress. You're not late. You're not slow. You're human.",
            "Create rituals of transition. A goodbye dinner. A welcome breakfast. A letter to your past self. A vision for your future self. Rituals mark boundaries. They create meaning. They honor the significance of what is happening. And they help you move through it.",
            "Trust the uncertainty. Not because it's comfortable. Because it's inevitable. You don't know what's on the other side. Nobody does. And that's okay. The person who trusts uncertainty is the person who discovers possibility. The person who fears it discovers only fear.",
            "The person who navigates transitions well is not someone who avoids them. They're someone who understands that life IS transition. That stability is an illusion. That change is constant. And that the skill of navigating change gracefully is perhaps the most valuable skill there is."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One acknowledgment. One small plan. One reached-out hand. One moment of grief. One ritual created. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. An acceptance practiced. A support system built. A plan made. A ritual honored. A growth noticed. Medium grace."
        else:
            capacity_note = "Good capacity. Deep transition navigation. A systematic practice of awareness, acceptance, planning, support, and growth. You have the strength to navigate any change."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Life transition navigation is not about avoiding change. It's about moving through it. Most people resist transitions. They cling to what was. They fear what will be. They ignore what is. And they get stuck. The work of life transition navigation coaching is about understanding that transitions are not interruptions to life. They ARE life. That acceptance is not surrender. That grief is necessary. That planning gives ground. That support is essential. And that every transition - however painful - carries the seed of growth. The person who understands this doesn't just survive transitions. They use them. They grow through them. They become more themselves because of them."
        }

    def get_transition_score(self) -> int:
        """Calculate overall transition health (0-100)."""
        if not self._entries:
            return 25

        avg_aware = sum(e.awareness for e in self._entries) / len(self._entries)
        avg_acc = sum(e.acceptance for e in self._entries) / len(self._entries)
        avg_plan = sum(e.planning for e in self._entries) / len(self._entries)
        avg_sup = sum(e.support for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)
        avg_cour = sum(e.courage for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_acc = sum(e.acceptance for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
        else:
            recent_acc = 0
            recent_growth = 0

        # Resistance penalty
        res_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_acc_30 = sum(e.acceptance for e in last_30) / len(last_30)
            recent_growth_30 = sum(e.growth for e in last_30) / len(last_30)
            if recent_acc_30 < 0.3 and recent_growth_30 < 0.3:
                res_penalty = 15

        # Type variety
        unique_types = len(set(e.transition_type for e in self._entries))

        score = (avg_aware * 10) + (avg_acc * 25) + (avg_plan * 15) + (avg_sup * 15) + (avg_growth * 20) + (avg_cour * 10) + (recent_acc * 5) + (recent_growth * 5) + (unique_types * 2) - res_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_acceptance"] = round(sum(e.acceptance for e in self._entries) / len(self._entries), 2)
            self._stats["avg_growth"] = round(sum(e.growth for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_acc = sum(e.acceptance for e in recent) / len(recent)
                recent_growth = sum(e.growth for e in recent) / len(recent)
                self._stats["resistance_risk"] = recent_acc < 0.3 and recent_growth < 0.3
            else:
                self._stats["resistance_risk"] = False

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

    def _log_entry(self, entry: TransitionEntry):
        try:
            with open(TRANSITION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "change": entry.change,
                    "transition_type": entry.transition_type,
                    "acceptance": entry.acceptance,
                    "growth": entry.growth,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ltn_instance: Optional[LifeTransitionNavigator] = None
_ltn_lock = threading.Lock()


def get_life_transition_navigator() -> LifeTransitionNavigator:
    global _ltn_instance
    with _ltn_lock:
        if _ltn_instance is None:
            _ltn_instance = LifeTransitionNavigator()
        return _ltn_instance
