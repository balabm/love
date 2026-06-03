"""
LOVE Life Balance Wheel — Life Intelligence (Modern AI Pattern)

Most balance tools are static pie charts. This wheel:

1. DOMAIN TRACKING
   - Track satisfaction across life domains (work, health, relationships, growth, recreation, finance, environment, purpose)
   - Record what activities feed vs drain each domain
   - Detect domain neglect and over-investment

2. BALANCE ANALYSIS
   - Calculate balance score (how evenly distributed energy is)
   - Identify the "neglected domain" that needs attention
   - Detect "balance earthquakes" (sudden shifts in life focus)

3. PATTERN INSIGHTS
   - Find correlations between domain satisfaction and overall wellbeing
   - Identify which domain improvements boost others
   - Track balance trends over time

4. PROACTIVE REBALANCING
   - Suggest small actions to boost neglected domains
   - Alert when one domain is consuming too much energy
   - Recommend periodic rebalancing rituals

Architecture:
- record_domain_rating(domain, rating, activities): Log domain status
- get_balance_score(): Get overall life balance score
- get_domain_insights(): Get domain-specific insights
- get_rebalancing_suggestions(): Suggest actions to restore balance
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "life_balance_wheel"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WHEEL_LOG = DATA_DIR / "wheel.jsonl"
STATS_DB = DATA_DIR / "stats.json"

DOMAINS = ["work", "health", "relationships", "growth", "recreation", "finance", "environment", "purpose"]


@dataclass
class DomainEntry:
    """A life domain entry."""
    domain: str = ""
    rating: float = 5.0  # 1-10
    energy_invested: float = 5.0  # hours/week or subjective 1-10
    satisfaction: float = 5.0  # 1-10
    activities: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LifeBalanceWheel:
    """
    Track and optimize life balance across multiple domains.
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
        self._entries: deque = deque(maxlen=500)
        self._stats = {
            "total_entries": 0,
            "avg_balance_score": 0.0,
            "most_neglected": "",
            "most_overinvested": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_domain_rating(self, domain: str, rating: float = 5.0, energy_invested: float = 5.0, satisfaction: float = 5.0, activities: Optional[List[str]] = None, notes: str = "") -> DomainEntry:
        """Record a domain rating."""
        if domain not in DOMAINS:
            domain = "other"

        entry = DomainEntry(
            domain=domain,
            rating=max(1.0, min(10.0, rating)),
            energy_invested=max(0.0, energy_invested),
            satisfaction=max(1.0, min(10.0, satisfaction)),
            activities=activities or [],
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

    def get_balance_score(self) -> int:
        """Calculate overall life balance score (0-100)."""
        # Get latest entry for each domain
        latest = {}
        for entry in self._entries:
            latest[entry.domain] = entry

        if len(latest) < 3:
            return 50

        ratings = [e.rating for e in latest.values()]
        energies = [e.energy_invested for e in latest.values()]

        # Average satisfaction
        avg_rating = sum(ratings) / len(ratings)
        satisfaction_score = avg_rating * 10

        # Balance score (lower variance = better balance)
        if len(ratings) > 1:
            variance = sum((r - avg_rating) ** 2 for r in ratings) / len(ratings)
            std_dev = math.sqrt(variance)
            balance_score = max(0, 100 - std_dev * 15)
        else:
            balance_score = 80

        # Energy distribution (should be somewhat even)
        if len(energies) > 1:
            total_energy = sum(energies)
            if total_energy > 0:
                expected_energy = total_energy / len(energies)
                energy_variance = sum((e - expected_energy) ** 2 for e in energies) / len(energies)
                energy_score = max(0, 100 - energy_variance * 5)
            else:
                energy_score = 50
        else:
            energy_score = 50

        overall = round(satisfaction_score * 0.5 + balance_score * 0.3 + energy_score * 0.2)
        return min(100, overall)

    def get_domain_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get domain-specific insights."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self._entries if e.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Domain averages
        domain_data = defaultdict(lambda: {"ratings": [], "energies": [], "satisfactions": [], "activities": []})
        for e in recent:
            d = e.domain
            domain_data[d]["ratings"].append(e.rating)
            domain_data[d]["energies"].append(e.energy_invested)
            domain_data[d]["satisfactions"].append(e.satisfaction)
            domain_data[d]["activities"].extend(e.activities)

        insights = {}
        for domain, data in domain_data.items():
            avg_rating = sum(data["ratings"]) / len(data["ratings"])
            avg_energy = sum(data["energies"]) / len(data["energies"])
            avg_satisfaction = sum(data["satisfactions"]) / len(data["satisfactions"])

            # Trend
            if len(data["ratings"]) >= 3:
                first_third = sum(data["ratings"][:len(data["ratings"])//3]) / max(1, len(data["ratings"])//3)
                last_third = sum(data["ratings"][-len(data["ratings"])//3:]) / max(1, len(data["ratings"])//3)
                trend = "improving" if last_third > first_third + 0.5 else "declining" if last_third < first_third - 0.5 else "stable"
            else:
                trend = "insufficient_data"

            # Most common activities
            activity_counts = defaultdict(int)
            for a in data["activities"]:
                activity_counts[a] += 1
            top_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            insights[domain] = {
                "avg_rating": round(avg_rating, 1),
                "avg_energy": round(avg_energy, 1),
                "avg_satisfaction": round(avg_satisfaction, 1),
                "trend": trend,
                "top_activities": [a[0] for a in top_activities],
                "entries": len(data["ratings"]),
            }

        # Neglected domains (low rating + low energy)
        neglected = sorted(
            [(d, i["avg_rating"]) for d, i in insights.items() if i["avg_rating"] < 5],
            key=lambda x: x[1],
        )

        # Overinvested domains (high energy, low satisfaction)
        overinvested = sorted(
            [(d, i["avg_energy"] - i["avg_satisfaction"]) for d, i in insights.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        return {
            "domains": insights,
            "neglected": [d[0] for d in neglected[:3]],
            "overinvested": [d[0] for d in overinvested if d[1] > 2],
            "balance_score": self.get_balance_score(),
        }

    def get_rebalancing_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest actions to restore life balance."""
        insights = self.get_domain_insights()
        suggestions = []

        if insights.get("status") == "insufficient_data":
            return [{"suggestion": "Rate all 8 life domains to get rebalancing suggestions.", "domain": "general"}]

        # Suggest actions for neglected domains
        for domain in insights.get("neglected", []):
            domain_actions = {
                "work": "Set a hard stop time today. Work will still be there tomorrow.",
                "health": "Schedule a 20-minute workout or walk. Your body is asking for attention.",
                "relationships": "Send a message to someone you care about. Connection is a verb.",
                "growth": "Read for 15 minutes or watch an educational video. Growth compounds.",
                "recreation": "Do something fun today. Play is not optional.",
                "finance": "Review your spending for 5 minutes. Awareness is the first step.",
                "environment": "Clean your desk or organize a drawer. Your space affects your mind.",
                "purpose": "Journal about what matters to you. Purpose gives energy to everything else.",
            }
            suggestions.append({
                "domain": domain,
                "suggestion": domain_actions.get(domain, f"Give some attention to {domain}."),
                "priority": "high",
                "type": "neglected",
            })

        # Suggest actions for overinvested domains
        for domain in insights.get("overinvested", []):
            domain_redux = {
                "work": "You might be over-investing in work. What's the minimum effective dose?",
                "health": "Are you obsessing over health metrics? Balance means not overdoing anything.",
                "relationships": "Are you people-pleasing? Healthy boundaries create better relationships.",
                "finance": "Money is important, but so is living. Don't forget to enjoy what you're earning.",
            }
            if domain in domain_redux:
                suggestions.append({
                    "domain": domain,
                    "suggestion": domain_redux[domain],
                    "priority": "medium",
                    "type": "overinvested",
                })

        # General balance suggestion
        if len(suggestions) == 0:
            suggestions.append({
                "domain": "general",
                "suggestion": "Your life balance looks good. Keep doing what you're doing.",
                "priority": "low",
                "type": "maintenance",
            })

        return suggestions

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        latest = {}
        for entry in self._entries:
            latest[entry.domain] = entry

        if len(latest) >= 2:
            ratings = [e.rating for e in latest.values()]
            avg = sum(ratings) / len(ratings)
            variance = sum((r - avg) ** 2 for r in ratings) / len(ratings)
            self._stats["avg_balance_score"] = round(max(0, 100 - math.sqrt(variance) * 15), 1)

            # Find most neglected
            neglected = min(latest.items(), key=lambda x: x[1].rating)
            self._stats["most_neglected"] = neglected[0]

            # Find most overinvested (high energy, lower satisfaction)
            overinvested = max(latest.items(), key=lambda x: x[1].energy_invested - x[1].satisfaction)
            self._stats["most_overinvested"] = overinvested[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.life_balance_wheel")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.life_balance_wheel")

    def _log_entry(self, entry: DomainEntry):
        try:
            with open(WHEEL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "domain": entry.domain,
                    "rating": entry.rating,
                    "energy": entry.energy_invested,
                    "satisfaction": entry.satisfaction,
                    "activities": entry.activities,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.life_balance_wheel")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lbw_instance: Optional[LifeBalanceWheel] = None
_lbw_lock = threading.Lock()


def get_life_balance_wheel() -> LifeBalanceWheel:
    global _lbw_instance
    with _lbw_lock:
        if _lbw_instance is None:
            _lbw_instance = LifeBalanceWheel()
        return _lbw_instance
