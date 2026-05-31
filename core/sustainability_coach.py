"""
LOVE Sustainability Coach — Stewardship Intelligence (Modern AI Pattern)

Most environmental harm is invisible and gradual. This coach:

1. SUSTAINABILITY TRACKING
   - Record sustainable actions and their characteristics
   - Track sustainability domains (energy, water, waste, food, transport, consumption)
   - Log impact and their effects on ecological footprint

2. PATTERN ANALYSIS
   - Identify the user's sustainability profile (unaware, starter, practitioner, steward)
   - Find sustainable behaviors that create lasting habits
   - Detect greenwashing and performative actions

3. SUSTAINABILITY BUILDING
   - Suggest sustainable actions matched to current lifestyle
   - Provide reduction and replacement frameworks
   - Recommendation circular economy practices

4. STEWARDSHIP CULTIVATION
   - Track the correlation between awareness and behavior change
   - Alert when habits are regressing
   - Celebrate genuine impact reduction

Architecture:
- record_action(action, domain, impact, effort): Log action
- get_sustainability_stats(): Get sustainability pattern analysis
- get_sustainability_action(domain, capacity): Get action
- get_sustainability_score(): Calculate overall sustainability health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "sustainability_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SUSTAINABILITY_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SustainabilityEntry:
    """A tracked sustainability entry."""
    entry_id: str = ""
    action: str = ""  # what was done
    domain: str = ""  # energy, water, waste, food, transport, consumption
    impact: float = 0.0  # estimated impact reduction (kg CO2, liters, etc.)
    effort: float = 0.5  # 0-1, how much effort required
    consistency: float = 0.5  # 0-1, how consistent
    genuine: bool = True  # was it genuine or performative
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SustainabilityCoach:
    """
    Intelligent sustainability coach with impact tracking and greenwashing detection.
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
            "total_impact": 0.0,
            "avg_effort": 0.0,
            "regression_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", domain: str = "", impact: float = 0.0, effort: float = 0.5, consistency: float = 0.5, genuine: bool = True, notes: str = "") -> SustainabilityEntry:
        """Record a sustainability entry."""
        entry_id = f"sus_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SustainabilityEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            domain=domain or "energy",
            impact=impact,
            effort=effort,
            consistency=consistency,
            genuine=genuine,
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

    def get_sustainability_stats(self) -> Dict[str, Any]:
        """Get sustainability pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "impact_sum": 0.0, "effort_sum": 0.0, "consistency_sum": 0.0, "genuine_count": 0})
        for e in self._entries:
            by_domain[e.domain]["count"] += 1
            by_domain[e.domain]["impact_sum"] += e.impact
            by_domain[e.domain]["effort_sum"] += e.effort
            by_domain[e.domain]["consistency_sum"] += e.consistency
            if e.genuine:
                by_domain[e.domain]["genuine_count"] += 1

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "total_impact": round(data["impact_sum"], 1),
                "avg_effort": round(data["effort_sum"] / count, 2),
                "avg_consistency": round(data["consistency_sum"] / count, 2),
                "genuine_rate": round(data["genuine_count"] / count, 2),
            }

        best_domain = max(domain_stats.items(), key=lambda x: x[1]["total_impact"]) if domain_stats else ("", {})

        # Effort vs impact
        low_effort = [e for e in self._entries if e.effort < 0.4]
        high_effort = [e for e in self._entries if e.effort > 0.7]
        if low_effort and high_effort:
            low_effort_impact = sum(e.impact for e in low_effort) / len(low_effort)
            high_effort_impact = sum(e.impact for e in high_effort) / len(high_effort)
        else:
            low_effort_impact = 0
            high_effort_impact = 0

        # Consistency analysis
        high_cons = [e for e in self._entries if e.consistency > 0.7]
        low_cons = [e for e in self._entries if e.consistency < 0.4]
        if high_cons and low_cons:
            high_cons_impact = sum(e.impact for e in high_cons) / len(high_cons)
            low_cons_impact = sum(e.impact for e in low_cons) / len(low_cons)
        else:
            high_cons_impact = 0
            low_cons_impact = 0

        # Genuine vs performative
        genuine = [e for e in self._entries if e.genuine]
        performative = [e for e in self._entries if not e.genuine]
        if genuine and performative:
            genuine_impact = sum(e.impact for e in genuine) / len(genuine)
            performative_impact = sum(e.impact for e in performative) / len(performative)
        else:
            genuine_impact = 0
            performative_impact = 0

        # Regression detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_impact = sum(e.impact for e in recent) / len(recent)
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            regression_risk = recent_impact < 0.5 or recent_cons < 0.4
        else:
            regression_risk = False

        # Recent trend
        if recent:
            recent_effort = sum(e.effort for e in recent) / len(recent)
            recent_genuine = sum(1 for e in recent if e.genuine) / len(recent)
        else:
            recent_effort = 0
            recent_genuine = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_impact = sum(e.impact for e in older) / len(older)
            older_cons = sum(e.consistency for e in older) / len(older)
            impact_trend = recent_impact - older_impact if recent else 0
            cons_trend = recent_cons - older_cons if recent else 0
        else:
            impact_trend = 0
            cons_trend = 0

        return {
            "total_entries": len(self._entries),
            "total_impact": round(sum(e.impact for e in self._entries), 1),
            "domain_stats": domain_stats,
            "best_domain": best_domain[0],
            "effort_efficiency": {
                "low_effort_impact": round(low_effort_impact, 1),
                "high_effort_impact": round(high_effort_impact, 1),
            },
            "consistency_impact": {
                "high_consistency_impact": round(high_cons_impact, 1),
                "low_consistency_impact": round(low_cons_impact, 1),
            },
            "genuine_vs_performative": {
                "genuine_impact": round(genuine_impact, 1),
                "performative_impact": round(performative_impact, 1),
            },
            "regression_risk": regression_risk,
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 1),
            "avg_effort": round(sum(e.effort for e in self._entries) / len(self._entries), 2),
            "impact_trend": round(impact_trend, 1),
            "consistency_trend": round(cons_trend, 2),
            "recent_effort": round(recent_effort, 2),
            "recent_genuine_rate": round(recent_genuine, 2),
        }

    def get_sustainability_action(self, domain: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get action."""
        actions = {
            "energy": [
                "Switch to LED bulbs. Small change. Real impact. Every watt saved is a watt not generated.",
                "Adjust thermostat 2 degrees. Down in winter. Up in summer. You won't notice. The planet will.",
                "Unplug phantom loads. Chargers. TVs. They draw power when off. Kill the vampires.",
            ],
            "water": [
                "Fix the drip. One drip per second = 3,000 gallons per year. That's not trivial.",
                "Shorter showers. 5 minutes. Set a timer. Water is not infinite. Even where it seems abundant.",
                "Capture rainwater. For plants. For washing. Free water from the sky. Use it.",
            ],
            "waste": [
                "Refuse first. Reduce second. Reuse third. Recycle fourth. In that order.",
                "Buy bulk. Less packaging. Less waste. Often cheaper. Triple win.",
                "Compost. Food scraps become soil. Soil grows food. The circle closes.",
            ],
            "food": [
                "Eat less meat. Not none. Less. The most impactful dietary change you can make.",
                "Buy local. Food miles matter. Local is fresher. Local supports community.",
                "Reduce food waste. Plan meals. Use leftovers. 40% of food is wasted. Don't contribute.",
            ],
            "transport": [
                "Walk for trips under 1 mile. Bike for trips under 5. Drive for the rest. In that order.",
                "Combine trips. Errand batching. One efficient trip beats five scattered ones.",
                "If you must drive, carpool. One car. Four people. 75% reduction. Simple math.",
            ],
            "consumption": [
                "Buy durable. Cheap is expensive. A $50 item that lasts 10 years beats a $10 item that lasts 1.",
                "Repair before replace. Most things can be fixed. YouTube will show you how.",
                "Borrow before buy. Library. Tool library. Friends. Ownership is overrated.",
            ],
            "general": [
                "You don't need to be perfect. You need to be better. One sustainable choice. Then another.",
                "The most sustainable product is the one you already own. Use it. Maintain it. Keep it.",
                "Your individual impact is small. But your influence is large. Live sustainably. Others will notice.",
            ],
        }

        selected = actions.get(domain, actions["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. Start with one tiny change. One lightbulb. One shorter shower. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. You can handle a few domains. Pick two. Master them. Then add."
        else:
            capacity_note = "Good capacity. This is when you systematize. Audit your home. Your commute. Your diet. Optimize."

        return {
            "domain": domain or "general",
            "capacity": capacity,
            "action": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most people think sustainability is about sacrifice. It's not. It's about intelligence. The most sustainable choices are often the cheapest, healthiest, and most satisfying. A bike commute is cheaper than driving, healthier than sitting, and more pleasant than traffic. Local food is fresher than shipped. Durable goods cost less over time. Sustainability is not about giving things up. It's about choosing better things.",
        }

    def get_sustainability_score(self) -> int:
        """Calculate overall sustainability health (0-100)."""
        if not self._entries:
            return 25

        # Impact and low effort
        total_impact = sum(e.impact for e in self._entries)
        avg_impact = total_impact / len(self._entries)
        avg_effort = sum(e.effort for e in self._entries) / len(self._entries)

        # Consistency and genuineness
        avg_cons = sum(e.consistency for e in self._entries) / len(self._entries)
        genuine_rate = sum(1 for e in self._entries if e.genuine) / len(self._entries)

        # Domain variety
        unique_domains = len(set(e.domain for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_impact = sum(e.impact for e in recent) / len(recent)
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            recent_genuine = sum(1 for e in recent if e.genuine) / len(recent)
        else:
            recent_impact = 0
            recent_cons = 0
            recent_genuine = 0

        # Regression penalty
        regression_penalty = 0
        if recent:
            recent_impact_val = sum(e.impact for e in recent) / len(recent)
            recent_cons_val = sum(e.consistency for e in recent) / len(recent)
            if recent_impact_val < 0.5 or recent_cons_val < 0.4:
                regression_penalty = 10

        score = (avg_impact * 2) + ((1 - avg_effort) * 15) + (avg_cons * 20) + (genuine_rate * 15) + (unique_domains * 3) + (recent_impact * 2) + (recent_cons * 15) + (recent_genuine * 10) - regression_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["total_impact"] = round(sum(e.impact for e in self._entries), 1)
            self._stats["avg_effort"] = round(sum(e.effort for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_impact = sum(e.impact for e in recent) / len(recent)
                recent_cons = sum(e.consistency for e in recent) / len(recent)
                self._stats["regression_risk"] = recent_impact < 0.5 or recent_cons < 0.4

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

    def _log_entry(self, entry: SustainabilityEntry):
        try:
            with open(SUSTAINABILITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "domain": entry.domain,
                    "impact": entry.impact,
                    "effort": entry.effort,
                    "consistency": entry.consistency,
                    "genuine": entry.genuine,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sc_instance: Optional[SustainabilityCoach] = None
_sc_lock = threading.Lock()


def get_sustainability_coach() -> SustainabilityCoach:
    global _sc_instance
    with _sc_lock:
        if _sc_instance is None:
            _sc_instance = SustainabilityCoach()
        return _sc_instance
