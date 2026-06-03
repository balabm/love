"""
LOVE Perfectionism Healer — Completion Intelligence (Modern AI Pattern)

Most people are paralyzed by perfectionism. This healer:

1. PERFECTIONISM TRACKING
   - Record perfectionism moments and their characteristics
   - Track perfectionism types (self, others, task, appearance, performance)
   - Log cost, completion, and satisfaction from perfectionist patterns

2. PATTERN ANALYSIS
   - Identify the user's perfectionism profile (paralyzed, driven, balanced, recovering)
   - Find perfectionism patterns that create quality vs paralysis
   - Detect chronic perfectionism and its costs

3. PERFECTIONISM HEALING
   - Suggest practices for releasing perfectionist demands
   - Provide frameworks for "good enough" and completion
   - Recommend practices for self-acceptance despite imperfection

4. COMPLETION CULTIVATION
   - Track the correlation between perfectionism and actual completion
   - Alert when perfectionism is preventing progress
   - Celebrate moments of genuine "good enough"

Architecture:
- record_perfectionism(situation, type, cost, completion, satisfaction): Log perfectionism
- get_perfectionism_stats(): Get perfectionism pattern analysis
- get_perfectionism_suggestion(capacity, context): Get suggestion
- get_perfectionism_score(): Calculate overall perfectionism health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "perfectionism_healer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PERFECTIONISM_LOG = DATA_DIR / "perfectionism.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PerfectionismEntry:
    """A tracked perfectionism moment."""
    entry_id: str = ""
    situation: str = ""  # what happened
    perfectionism_type: str = ""  # self, others, task, appearance, performance
    cost: float = 0.0  # 0-1 cost of perfectionism
    completion: float = 0.0  # 0-1
    satisfaction: float = 0.0  # 0-1
    self_acceptance: float = 0.0  # 0-1
    good_enough: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PerfectionismHealer:
    """
    Intelligent perfectionism healer with cost detection and completion cultivation.
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
            "avg_cost": 0.0,
            "avg_completion": 0.0,
            "paralysis_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_perfectionism(self, situation: str = "", perfectionism_type: str = "", cost: float = 0.0, completion: float = 0.0, satisfaction: float = 0.0, self_acceptance: float = 0.0, good_enough: float = 0.0, notes: str = "") -> PerfectionismEntry:
        """Record a perfectionism moment."""
        entry_id = f"prf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PerfectionismEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            perfectionism_type=perfectionism_type or "task",
            cost=cost,
            completion=completion,
            satisfaction=satisfaction,
            self_acceptance=self_acceptance,
            good_enough=good_enough,
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

    def get_perfectionism_stats(self) -> Dict[str, Any]:
        """Get perfectionism pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "cost_sum": 0.0, "completion_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.perfectionism_type]["count"] += 1
            by_type[e.perfectionism_type]["cost_sum"] += e.cost
            by_type[e.perfectionism_type]["completion_sum"] += e.completion
            by_type[e.perfectionism_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_cost": round(data["cost_sum"] / count, 2),
                "avg_completion": round(data["completion_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Cost analysis
        high_cost = [e for e in self._entries if e.cost > 0.7]
        low_cost = [e for e in self._entries if e.cost < 0.4]
        if high_cost and low_cost:
            high_cost_comp = sum(e.completion for e in high_cost) / len(high_cost)
            low_cost_comp = sum(e.completion for e in low_cost) / len(low_cost)
            high_cost_sat = sum(e.satisfaction for e in high_cost) / len(high_cost)
            low_cost_sat = sum(e.satisfaction for e in low_cost) / len(low_cost)
        else:
            high_cost_comp = 0
            low_cost_comp = 0
            high_cost_sat = 0
            low_cost_sat = 0

        # Good enough analysis
        high_ge = [e for e in self._entries if e.good_enough > 0.7]
        low_ge = [e for e in self._entries if e.good_enough < 0.4]
        if high_ge and low_ge:
            high_ge_comp = sum(e.completion for e in high_ge) / len(high_ge)
            low_ge_comp = sum(e.completion for e in low_ge) / len(low_ge)
        else:
            high_ge_comp = 0
            low_ge_comp = 0

        # Paralysis risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cost = sum(e.cost for e in recent) / len(recent)
            recent_comp = sum(e.completion for e in recent) / len(recent)
            paralysis_risk = recent_cost > 0.7 and recent_comp < 0.3
        else:
            paralysis_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "cost_impact": {
                "high_cost_completion": round(high_cost_comp, 2),
                "low_cost_completion": round(low_cost_comp, 2),
                "high_cost_satisfaction": round(high_cost_sat, 2),
                "low_cost_satisfaction": round(low_cost_sat, 2),
            },
            "good_enough_effect": {
                "high_good_enough_completion": round(high_ge_comp, 2),
                "low_good_enough_completion": round(low_ge_comp, 2),
            },
            "paralysis_risk": paralysis_risk,
            "avg_cost": round(sum(e.cost for e in self._entries) / len(self._entries), 2),
            "avg_completion": round(sum(e.completion for e in self._entries) / len(self._entries), 2),
        }

    def get_perfectionism_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get perfectionism suggestion."""
        suggestions = [
            "Done is better than perfect. The perfect thing that never ships is worthless. The good enough thing that ships changes the world. Ship it.",
            "Set a deadline. Not a quality standard. The deadline creates the standard. 'This is what I can do in two hours.' That's your standard. Move on.",
            "Perfectionism is not a virtue. It's a defense mechanism. Against criticism. Against failure. Against shame. But the defense becomes the prison.",
            "Ask: who am I trying to impress? And do they matter? Most perfectionism is performance for an audience that isn't watching. Or doesn't care.",
            "Embrace the first draft. Everything good started as something bad. The first draft is supposed to be terrible. That's why it's called a draft.",
            "Perfect is the enemy of good. And good is the enemy of done. Stop at good enough. Good enough is good enough.",
            "Notice the cost. Hours spent. Opportunities missed. Stress accumulated. Is the marginal improvement worth the cost? Usually, it's not.",
            "Imperfect action beats perfect inaction. The person who does things imperfectly accomplishes infinitely more than the person who does nothing perfectly.",
            "Your worth is not your output. You are not a machine to be optimized. You are a human to be lived. Perfectionism treats you like a machine. Reject that.",
            "The person who demands perfection is the person who never finishes. And the person who never finishes never learns. Because learning comes from completion. From feedback. From the next iteration. Finish. Then improve."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small completion. One 'good enough.' One release of perfection. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A task finished at 80%. A deadline met. A deliberate 'good enough.' Medium healing."
        else:
            capacity_note = "Good capacity. A major release of perfectionism. A completed project. A systematic shift to completion. You have the strength to let go."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Perfectionism is not the pursuit of excellence. It's the fear of criticism. The person who says 'I just want to do it right' is often the person who is terrified of doing it wrong. And that terror prevents them from doing it at all. Real excellence comes from iteration. From shipping. From getting feedback. From improving. The perfect painting in the studio is not art. The imperfect painting in the gallery is. Perfectionism is the voice that says: keep working. It's not ready. And it never will be. Because readiness is not a state. It's a decision. Decide to be done. Decide to ship. Decide that good enough is good enough. And then do the next thing. That's how anything meaningful gets made."
        }

    def get_perfectionism_score(self) -> int:
        """Calculate overall perfectionism health (0-100)."""
        if not self._entries:
            return 25

        avg_cost = sum(e.cost for e in self._entries) / len(self._entries)
        avg_comp = sum(e.completion for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_sc = sum(e.self_acceptance for e in self._entries) / len(self._entries)
        avg_ge = sum(e.good_enough for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cost = sum(e.cost for e in recent) / len(recent)
            recent_comp = sum(e.completion for e in recent) / len(recent)
        else:
            recent_cost = 0
            recent_comp = 0

        # Paralysis penalty
        par_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cost_30 = sum(e.cost for e in last_30) / len(last_30)
            recent_comp_30 = sum(e.completion for e in last_30) / len(last_30)
            if recent_cost_30 > 0.7 and recent_comp_30 < 0.3:
                par_penalty = 15

        # Type variety
        unique_types = len(set(e.perfectionism_type for e in self._entries))

        score = (avg_comp * 25) + (avg_sat * 15) + (avg_sc * 20) + (avg_ge * 20) + (recent_comp * 10) + (recent_comp * 5) + (unique_types * 2) - (avg_cost * 10) - par_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_cost"] = round(sum(e.cost for e in self._entries) / len(self._entries), 2)
            self._stats["avg_completion"] = round(sum(e.completion for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cost = sum(e.cost for e in recent) / len(recent)
                recent_comp = sum(e.completion for e in recent) / len(recent)
                self._stats["paralysis_risk"] = recent_cost > 0.7 and recent_comp < 0.3
            else:
                self._stats["paralysis_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.perfectionism_healer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.perfectionism_healer")

    def _log_entry(self, entry: PerfectionismEntry):
        try:
            with open(PERFECTIONISM_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "perfectionism_type": entry.perfectionism_type,
                    "cost": entry.cost,
                    "completion": entry.completion,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.perfectionism_healer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ph_instance: Optional[PerfectionismHealer] = None
_ph_lock = threading.Lock()


def get_perfectionism_healer() -> PerfectionismHealer:
    global _ph_instance
    with _ph_lock:
        if _ph_instance is None:
            _ph_instance = PerfectionismHealer()
        return _ph_instance
