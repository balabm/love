"""
LOVE Legacy Builder — Long-term Impact Intelligence (Modern AI Pattern)

Most people live day-to-day without building lasting impact. This builder:

1. LEGACY TRACKING
   - Record legacy contributions and their characteristics
   - Track legacy types (relationships, creations, teaching, service, values)
   - Log legacy recipients and their feedback

2. PATTERN ANALYSIS
   - Identify the user's legacy style (builder, planter, mentor, catalyst)
   - Find legacy-building activities that create lasting impact
   - Detect legacy gaps (areas where impact is temporary)

3. LEGACY DESIGN
   - Suggest legacy-building activities matched to current capacity
   - Provide long-term impact planning exercises
   - Recommend ripple-effect amplification practices

4. IMPACT PRESERVATION
   - Track the durability of contributions over time
   - Alert when short-term busyness is displacing legacy work
   - Celebrate legacy milestones

Architecture:
- record_contribution(contribution, type, recipients, durability): Log contribution
- get_legacy_stats(): Get legacy pattern analysis
- get_legacy_plan(style, timeframe): Get plan
- get_legacy_score(): Calculate overall legacy health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "legacy_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEGACY_LOG = DATA_DIR / "contributions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class LegacyContribution:
    """A tracked legacy contribution."""
    contribution_id: str = ""
    contribution: str = ""
    legacy_type: str = ""  # relationships, creations, teaching, service, values, mentorship
    recipients: List[str] = field(default_factory=list)
    durability: float = 0.5  # 0-1, how long-lasting
    impact_depth: float = 0.5  # 0-1
    personal_cost: float = 0.5  # 0-1
    satisfaction: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LegacyBuilder:
    """
    Intelligent legacy builder with durability tracking and ripple-effect analysis.
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
        self._contributions: deque = deque(maxlen=300)
        self._stats = {
            "total_contributions": 0,
            "avg_durability": 0.0,
            "avg_impact": 0.0,
            "dominant_type": "",
            "short_term_bias": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_contribution(self, contribution: str = "", legacy_type: str = "", recipients: Optional[List[str]] = None, durability: float = 0.5, impact_depth: float = 0.5, personal_cost: float = 0.5, satisfaction: float = 0.5, notes: str = "") -> LegacyContribution:
        """Record a legacy contribution."""
        contribution_id = f"leg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._contributions)}"
        entry = LegacyContribution(
            contribution_id=contribution_id,
            contribution=contribution or "unspecified",
            legacy_type=legacy_type or "service",
            recipients=recipients or [],
            durability=durability,
            impact_depth=impact_depth,
            personal_cost=personal_cost,
            satisfaction=satisfaction,
            notes=notes,
        )

        with self._lock:
            self._contributions.append(entry)
            self._stats["total_contributions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_contribution(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_legacy_stats(self) -> Dict[str, Any]:
        """Get legacy pattern analysis."""
        if not self._contributions:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "durability_sum": 0.0, "impact_sum": 0.0, "satisfaction_sum": 0.0})
        for c in self._contributions:
            by_type[c.legacy_type]["count"] += 1
            by_type[c.legacy_type]["durability_sum"] += c.durability
            by_type[c.legacy_type]["impact_sum"] += c.impact_depth
            by_type[c.legacy_type]["satisfaction_sum"] += c.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_durability": round(data["durability_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        dominant_type = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Recipient analysis
        all_recipients = []
        for c in self._contributions:
            all_recipients.extend(c.recipients)
        
        recipient_counts = defaultdict(int)
        for r in all_recipients:
            recipient_counts[r] += 1

        top_recipients = sorted(recipient_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Cost-benefit analysis
        high_cost = [c for c in self._contributions if c.personal_cost > 0.7]
        if high_cost:
            high_cost_satisfaction = sum(c.satisfaction for c in high_cost) / len(high_cost)
        else:
            high_cost_satisfaction = 0

        low_cost = [c for c in self._contributions if c.personal_cost <= 0.4]
        if low_cost:
            low_cost_satisfaction = sum(c.satisfaction for c in low_cost) / len(low_cost)
        else:
            low_cost_satisfaction = 0

        # Short-term bias detection
        recent = list(self._contributions)[-20:]
        if recent:
            short_term = sum(1 for c in recent if c.durability < 0.4) / len(recent)
            short_term_bias = short_term > 0.5
        else:
            short_term_bias = False

        # Durability trend
        if len(self._contributions) >= 20:
            first_half = list(self._contributions)[:len(self._contributions)//2]
            second_half = list(self._contributions)[len(self._contributions)//2:]
            first_durability = sum(c.durability for c in first_half) / len(first_half)
            second_durability = sum(c.durability for c in second_half) / len(second_half)
            durability_trend = second_durability - first_durability
        else:
            durability_trend = 0

        return {
            "total_contributions": len(self._contributions),
            "type_stats": type_stats,
            "dominant_type": dominant_type[0],
            "top_recipients": top_recipients,
            "cost_analysis": {
                "high_cost_satisfaction": round(high_cost_satisfaction, 2),
                "low_cost_satisfaction": round(low_cost_satisfaction, 2),
            },
            "short_term_bias": short_term_bias,
            "avg_durability": round(sum(c.durability for c in self._contributions) / len(self._contributions), 2),
            "avg_impact": round(sum(c.impact_depth for c in self._contributions) / len(self._contributions), 2),
            "avg_satisfaction": round(sum(c.satisfaction for c in self._contributions) / len(self._contributions), 2),
            "durability_trend": round(durability_trend, 2),
        }

    def get_legacy_plan(self, style: str = "", timeframe: str = "5_years") -> Dict[str, Any]:
        """Get plan."""
        plans = {
            "builder": [
                "Create something that outlasts you. A book, a system, a community, a piece of art.",
                "Document your knowledge. Write it down. Others will build on it.",
                "Build infrastructure that makes others' lives easier. The builder's legacy is the scaffold.",
            ],
            "planter": [
                "Invest in relationships with people who will outlive you. Young people, children, mentees.",
                "Plant trees. Literal and metaphorical. Shade you will never sit under.",
                "Start something that takes decades to mature. Long-term thinking is rare and powerful.",
            ],
            "mentor": [
                "Teach one person deeply. Transfer not just knowledge, but wisdom.",
                "Share your failures openly. They're more valuable than your successes.",
                "Create opportunities for others. Open doors you had to break through.",
            ],
            "catalyst": [
                "Spark movements, not just moments. Inspire others to take up the work.",
                "Connect people who should know each other. The network effect of generosity.",
                "Challenge the status quo. Ask the question no one else is asking.",
            ],
            "general": [
                "Write a letter to your future great-grandchild. What do you want them to know about you?",
                "What would you do differently if you knew you'd be remembered for it? Do that.",
                "Legacy is not about being remembered. It's about being worth remembering.",
            ],
        }

        selected = plans.get(style, plans["general"])

        if timeframe == "1_year":
            time_note = "One year is short. Focus on seeds, not forests. Plant relationships, habits, and ideas."
        elif timeframe == "5_years":
            time_note = "Five years is enough for saplings to grow. Build systems, teach people, create enduring work."
        elif timeframe == "20_years":
            time_note = "Twenty years is legacy time. What forest do you want to walk through? Plant those trees."
        else:
            time_note = "Legacy unfolds on its own timeline. Focus on direction, not destination."

        return {
            "style": style or "general",
            "timeframe": timeframe,
            "plan": random.choice(selected),
            "time_note": time_note,
            "principle": "Legacy is not what you accumulate. It's what you leave behind that continues to grow without you. It's the ripple effect of your best self, extended through time by the people and systems you touched.",
        }

    def get_legacy_score(self) -> int:
        """Calculate overall legacy health (0-100)."""
        if not self._contributions:
            return 30

        # Durability and impact
        avg_durability = sum(c.durability for c in self._contributions) / len(self._contributions)
        avg_impact = sum(c.impact_depth for c in self._contributions) / len(self._contributions)

        # Satisfaction
        avg_satisfaction = sum(c.satisfaction for c in self._contributions) / len(self._contributions)

        # Low short-term bias
        short_term = sum(1 for c in self._contributions if c.durability < 0.4) / len(self._contributions)

        # Recipient breadth
        all_recipients = []
        for c in self._contributions:
            all_recipients.extend(c.recipients)
        unique_recipients = len(set(all_recipients))

        # Type variety
        unique_types = len(set(c.legacy_type for c in self._contributions))

        # Recent trend
        recent = list(self._contributions)[-14:]
        if recent:
            recent_durability = sum(c.durability for c in recent) / len(recent)
            recent_impact = sum(c.impact_depth for c in recent) / len(recent)
        else:
            recent_durability = 0
            recent_impact = 0

        # Cost sustainability
        avg_cost = sum(c.personal_cost for c in self._contributions) / len(self._contributions)

        score = (avg_durability * 25) + (avg_impact * 20) + (avg_satisfaction * 15) + ((1 - short_term) * 10) + (unique_recipients * 1) + (unique_types * 2) + (recent_durability * 15) + (recent_impact * 10) + ((1 - avg_cost) * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._contributions:
            self._stats["avg_durability"] = round(sum(c.durability for c in self._contributions) / len(self._contributions), 2)
            self._stats["avg_impact"] = round(sum(c.impact_depth for c in self._contributions) / len(self._contributions), 2)

            by_type = defaultdict(int)
            for c in self._contributions:
                by_type[c.legacy_type] += 1
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1])
                self._stats["dominant_type"] = dominant[0]

            recent = [c for c in self._contributions if c.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                short_term = sum(1 for c in recent if c.durability < 0.4) / len(recent)
                self._stats["short_term_bias"] = short_term > 0.5

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.legacy_builder")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.legacy_builder")

    def _log_contribution(self, contribution: LegacyContribution):
        try:
            with open(LEGACY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": contribution.timestamp,
                    "contribution": contribution.contribution,
                    "legacy_type": contribution.legacy_type,
                    "recipients": contribution.recipients,
                    "durability": contribution.durability,
                    "impact_depth": contribution.impact_depth,
                    "personal_cost": contribution.personal_cost,
                    "satisfaction": contribution.satisfaction,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.legacy_builder")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lb_instance: Optional[LegacyBuilder] = None
_lb_lock = threading.Lock()


def get_legacy_builder() -> LegacyBuilder:
    global _lb_instance
    with _lb_lock:
        if _lb_instance is None:
            _lb_instance = LegacyBuilder()
        return _lb_instance
