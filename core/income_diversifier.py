"""
LOVE Income Diversifier — Stream Intelligence (Modern AI Pattern)

Most financial fragility comes from single-source dependence. This diversifier:

1. INCOME TRACKING
   - Record income sources and their characteristics
   - Track income types (salary, business, investment, royalty, gig, passive)
   - Log diversification outcomes and their effects on stability

2. PATTERN ANALYSIS
   - Identify the user's income profile (single, dual, diversified, portfolio)
   - Find diversification patterns that create resilience
   - Detect over-dependence on primary source

3. DIVERSIFICATION BUILDING
   - Suggest income streams matched to skills and capacity
   - Provide side income and passive income frameworks
   - Recommendation stream development practices

4. RESILIENCE CULTIVATION
   - Track the correlation between source count and stability
   - Alert when dependence is becoming dangerous
   - Celebrate moments of stream activation

Architecture:
- record_source(source, type, amount, stability, effort): Log source
- get_income_stats(): Get income pattern analysis
- get_diversification_suggestion(skill, capacity, risk): Get suggestion
- get_income_score(): Calculate overall income health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "income_diversifier"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INCOME_LOG = DATA_DIR / "sources.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class IncomeEntry:
    """A tracked income entry."""
    entry_id: str = ""
    source: str = ""  # what is the source
    income_type: str = ""  # salary, business, investment, royalty, gig, passive
    amount: float = 0.0  # monthly amount
    stability: float = 0.5  # 0-1, how reliable
    effort_required: float = 0.5  # 0-1, how much ongoing effort
    growth_potential: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class IncomeDiversifier:
    """
    Intelligent income diversifier with dependence detection and stream optimization.
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
            "source_count": 0,
            "avg_stability": 0.0,
            "dependence_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_source(self, source: str = "", income_type: str = "", amount: float = 0.0, stability: float = 0.5, effort_required: float = 0.5, growth_potential: float = 0.5, notes: str = "") -> IncomeEntry:
        """Record an income entry."""
        entry_id = f"inc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = IncomeEntry(
            entry_id=entry_id,
            source=source or "unspecified",
            income_type=income_type or "salary",
            amount=amount,
            stability=stability,
            effort_required=effort_required,
            growth_potential=growth_potential,
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

    def get_income_stats(self) -> Dict[str, Any]:
        """Get income pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "amount_sum": 0.0, "stability_sum": 0.0, "effort_sum": 0.0, "growth_sum": 0.0})
        for e in self._entries:
            by_type[e.income_type]["count"] += 1
            by_type[e.income_type]["amount_sum"] += e.amount
            by_type[e.income_type]["stability_sum"] += e.stability
            by_type[e.income_type]["effort_sum"] += e.effort_required
            by_type[e.income_type]["growth_sum"] += e.growth_potential

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_amount": round(data["amount_sum"] / count, 2),
                "avg_stability": round(data["stability_sum"] / count, 2),
                "avg_effort": round(data["effort_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
            }

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "amount_sum": 0.0, "stability_sum": 0.0})
        for e in self._entries:
            by_source[e.source]["count"] += 1
            by_source[e.source]["amount_sum"] += e.amount
            by_source[e.source]["stability_sum"] += e.stability

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_amount": round(data["amount_sum"] / count, 2),
                "avg_stability": round(data["stability_sum"] / count, 2),
            }

        # Primary source dependence
        total_amount = sum(e.amount for e in self._entries)
        if total_amount > 0:
            max_source = max(source_stats.items(), key=lambda x: x[1]["avg_amount"] * x[1]["count"])
            primary_amount = max_source[1]["avg_amount"] * max_source[1]["count"]
            primary_dependence = primary_amount / total_amount
        else:
            primary_dependence = 1.0

        dependence_risk = primary_dependence > 0.8

        # Stability vs effort analysis
        high_stability = [e for e in self._entries if e.stability > 0.7]
        low_stability = [e for e in self._entries if e.stability < 0.4]
        if high_stability and low_stability:
            high_stability_effort = sum(e.effort_required for e in high_stability) / len(high_stability)
            low_stability_effort = sum(e.effort_required for e in low_stability) / len(low_stability)
            high_stability_growth = sum(e.growth_potential for e in high_stability) / len(high_stability)
            low_stability_growth = sum(e.growth_potential for e in low_stability) / len(low_stability)
        else:
            high_stability_effort = 0
            low_stability_effort = 0
            high_stability_growth = 0
            low_stability_growth = 0

        # Growth potential analysis
        high_growth = [e for e in self._entries if e.growth_potential > 0.7]
        if high_growth:
            high_growth_effort = sum(e.effort_required for e in high_growth) / len(high_growth)
        else:
            high_growth_effort = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_sources = len(set(e.source for e in recent))
            recent_stability = sum(e.stability for e in recent) / len(recent)
            recent_growth = sum(e.growth_potential for e in recent) / len(recent)
        else:
            recent_sources = 0
            recent_stability = 0
            recent_growth = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_sources = len(set(e.source for e in older))
            older_stability = sum(e.stability for e in older) / len(older)
            source_trend = recent_sources - older_sources
            stability_trend = recent_stability - older_stability
        else:
            source_trend = 0
            stability_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "source_stats": source_stats,
            "source_count": len(source_stats),
            "primary_dependence": round(primary_dependence, 2),
            "dependence_risk": dependence_risk,
            "stability_effort": {
                "high_stability_effort": round(high_stability_effort, 2),
                "low_stability_effort": round(low_stability_effort, 2),
                "high_stability_growth": round(high_stability_growth, 2),
                "low_stability_growth": round(low_stability_growth, 2),
            },
            "growth_effort": round(high_growth_effort, 2),
            "avg_stability": round(sum(e.stability for e in self._entries) / len(self._entries), 2),
            "source_trend": round(source_trend, 0),
            "stability_trend": round(stability_trend, 2),
            "recent_growth_potential": round(recent_growth, 2),
        }

    def get_diversification_suggestion(self, skill: str = "", capacity: float = 0.5, risk_tolerance: float = 0.5) -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "skill_based": [
                "Monetize what you know. Consulting. Coaching. Courses. Your expertise has market value.",
                "Freelance your skills. One client. One project. Prove the model. Then scale.",
                "Create a product from your expertise. Ebook. Template. Tool. Build once. Sell forever.",
            ],
            "passive": [
                "Invest in dividend stocks. The 4% rule. $1M invested = $40k/year. Start now.",
                "Create digital assets. Apps. Plugins. Content. They work while you sleep.",
                "Rent what you own. Car. Room. Equipment. Idle assets are missed opportunities.",
            ],
            "active": [
                "Side business. Solve a problem you have. Others probably have it too.",
                "Gig work. Uber. DoorDash. TaskRabbit. Not glamorous. But immediate.",
                "Flipping. Buy low. Sell high. Thrift stores. Estate sales. Facebook Marketplace.",
            ],
            "creative": [
                "Content creation. YouTube. Newsletter. Podcast. Build an audience. Monetize later.",
                "Art. Music. Writing. The creator economy is real. Start small. Be consistent.",
                "Affiliate marketing. Recommend what you use. Earn when they buy. No inventory.",
            ],
            "general": [
                "Every stream you add reduces fragility. Aim for 3-5 sources. Diversify type, not just amount.",
                "Start before you need it. Building streams takes time. Crisis is the wrong moment to begin.",
                "One stream at a time. Master it. Automate it. Then add another. Parallel is expensive.",
            ],
        }

        selected = suggestions.get(skill, suggestions["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. Start tiny. 1 hour a week. Consistency beats intensity."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. You can handle one side stream. Choose wisely."
        else:
            capacity_note = "High capacity. You can build multiple streams. But start with one."

        return {
            "skill": skill or "general",
            "capacity": capacity,
            "risk_tolerance": risk_tolerance,
            "suggestion": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most people have one income source. Their job. When that fails, everything fails. Multiple income streams are not about getting rich. They're about not being fragile. Three streams means you can lose one and survive. Five means you can lose two and thrive. The goal is resilience, not greed.",
        }

    def get_income_score(self) -> int:
        """Calculate overall income health (0-100)."""
        if not self._entries:
            return 30

        # Source count and stability
        unique_sources = len(set(e.source for e in self._entries))
        unique_types = len(set(e.income_type for e in self._entries))
        avg_stability = sum(e.stability for e in self._entries) / len(self._entries)

        # Low effort, high growth potential
        avg_effort = sum(e.effort_required for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth_potential for e in self._entries) / len(self._entries)

        # Low primary dependence
        total_amount = sum(e.amount for e in self._entries)
        if total_amount > 0:
            by_source = defaultdict(float)
            for e in self._entries:
                by_source[e.source] += e.amount
            max_amount = max(by_source.values())
            primary_dependence = max_amount / total_amount
        else:
            primary_dependence = 1.0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_sources = len(set(e.source for e in recent))
            recent_stability = sum(e.stability for e in recent) / len(recent)
            recent_growth = sum(e.growth_potential for e in recent) / len(recent)
        else:
            recent_sources = 0
            recent_stability = 0
            recent_growth = 0

        # Dependence penalty
        dependence_penalty = 0
        if primary_dependence > 0.8:
            dependence_penalty = 15

        score = (unique_sources * 5) + (unique_types * 3) + (avg_stability * 15) + ((1 - avg_effort) * 10) + (avg_growth * 15) + ((1 - primary_dependence) * 15) + (recent_sources * 3) + (recent_stability * 10) + (recent_growth * 10) - dependence_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["source_count"] = len(set(e.source for e in self._entries))
            self._stats["avg_stability"] = round(sum(e.stability for e in self._entries) / len(self._entries), 2)

            total_amount = sum(e.amount for e in self._entries)
            if total_amount > 0:
                by_source = defaultdict(float)
                for e in self._entries:
                    by_source[e.source] += e.amount
                max_amount = max(by_source.values())
                primary_dependence = max_amount / total_amount
                self._stats["dependence_risk"] = primary_dependence > 0.8

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

    def _log_entry(self, entry: IncomeEntry):
        try:
            with open(INCOME_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "source": entry.source,
                    "income_type": entry.income_type,
                    "amount": entry.amount,
                    "stability": entry.stability,
                    "effort_required": entry.effort_required,
                    "growth_potential": entry.growth_potential,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_id_instance: Optional[IncomeDiversifier] = None
_id_lock = threading.Lock()


def get_income_diversifier() -> IncomeDiversifier:
    global _id_instance
    with _id_lock:
        if _id_instance is None:
            _id_instance = IncomeDiversifier()
        return _id_instance
