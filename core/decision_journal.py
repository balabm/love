"""
LOVE Decision Journal — Decision Quality Tracker (Modern AI Pattern)

Most decisions are forgotten. This journal:

1. DECISION LOGGING
   - Record decisions with context, options considered, and expected outcomes
   - Track decision quality (how well it turned out)
   - Categorize decisions (strategic, tactical, emotional, financial)

2. PATTERN ANALYSIS
   - Identify recurring decision traps (analysis paralysis, impulsive choices)
   - Detect decision fatigue patterns
   - Find optimal decision-making conditions (time of day, energy level)

3. OUTCOME TRACKING
   - Compare expected vs actual outcomes
   - Calculate decision accuracy over time
   - Identify domains where the user makes better/worse decisions

4. PROACTIVE IMPROVEMENT
   - Suggest decision-making frameworks for complex choices
   - Warn when similar bad decisions repeat
   - Celebrate good decision streaks

Architecture:
- log_decision(context, options, choice, expected): Record a decision
- review_decision(decision_id, actual_outcome): Review outcome
- get_decision_stats(): Get decision analytics
- get_framework_suggestion(): Suggest decision framework
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

DATA_DIR = Path(__file__).parent.parent / "data" / "decision_journal"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DECISION_LOG = DATA_DIR / "decisions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Decision:
    """A recorded decision."""
    decision_id: str = ""
    context: str = ""
    options: List[str] = field(default_factory=list)
    choice: str = ""
    expected_outcome: str = ""
    category: str = ""  # strategic, tactical, emotional, financial
    confidence: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    energy_level: float = 0.5
    time_of_day: str = ""  # morning, afternoon, evening, night
    actual_outcome: Optional[str] = None
    outcome_quality: Optional[float] = None  # 0-1


class DecisionJournal:
    """
    Track decisions and improve decision-making quality.
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
        self._decisions: Dict[str, Decision] = {}
        self._stats = {
            "total_decisions": 0,
            "reviewed_decisions": 0,
            "avg_confidence": 0.5,
            "avg_accuracy": 0.5,
            "best_category": "",
            "worst_category": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def log_decision(self, context: str, options: List[str], choice: str, expected_outcome: str, category: str = "", confidence: float = 0.5, energy_level: float = 0.5) -> Decision:
        """Record a new decision."""
        decision_id = f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        decision = Decision(
            decision_id=decision_id,
            context=context,
            options=options,
            choice=choice,
            expected_outcome=expected_outcome,
            category=category or "tactical",
            confidence=confidence,
            energy_level=energy_level,
            time_of_day=time_of_day,
        )

        with self._lock:
            self._decisions[decision_id] = decision
            self._stats["total_decisions"] += 1

        self._save_stats()
        self._log_decision(decision)

        return decision

    def review_decision(self, decision_id: str, actual_outcome: str, outcome_quality: float):
        """Review a decision's actual outcome."""
        if decision_id not in self._decisions:
            return

        decision = self._decisions[decision_id]
        decision.actual_outcome = actual_outcome
        decision.outcome_quality = outcome_quality

        self._stats["reviewed_decisions"] += 1
        self._update_accuracy()
        self._save_stats()

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_decision_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get decision analytics."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [d for d in self._decisions.values() if d.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "total_quality": 0.0, "confidence_sum": 0.0})
        for d in recent:
            cat = d.category
            by_category[cat]["count"] += 1
            if d.outcome_quality is not None:
                by_category[cat]["total_quality"] += d.outcome_quality
            by_category[cat]["confidence_sum"] += d.confidence

        category_stats = {}
        for cat, stats in by_category.items():
            category_stats[cat] = {
                "count": stats["count"],
                "avg_quality": round(stats["total_quality"] / max(1, stats["count"]), 2),
                "avg_confidence": round(stats["confidence_sum"] / stats["count"], 2),
            }

        # Find best/worst categories
        rated = {k: v for k, v in category_stats.items() if v["avg_quality"] > 0}
        best_cat = max(rated.items(), key=lambda x: x[1]["avg_quality"])[0] if rated else ""
        worst_cat = min(rated.items(), key=lambda x: x[1]["avg_quality"])[0] if rated else ""

        # Time of day analysis
        by_time = defaultdict(list)
        for d in recent:
            if d.outcome_quality is not None:
                by_time[d.time_of_day].append(d.outcome_quality)

        best_time = max(by_time.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if by_time else ""

        # Decision fatigue detection
        daily_counts = defaultdict(int)
        for d in recent:
            daily_counts[d.timestamp[:10]] += 1
        avg_daily = sum(daily_counts.values()) / max(1, len(daily_counts))
        fatigue_risk = avg_daily > 5

        return {
            "total_decisions": len(recent),
            "reviewed": sum(1 for d in recent if d.outcome_quality is not None),
            "avg_confidence": round(sum(d.confidence for d in recent) / len(recent), 2),
            "avg_accuracy": self._stats.get("avg_accuracy", 0.5),
            "category_stats": category_stats,
            "best_category": best_cat,
            "worst_category": worst_cat,
            "best_time_of_day": best_time,
            "fatigue_risk": fatigue_risk,
            "avg_daily_decisions": round(avg_daily, 1),
        }

    def get_framework_suggestion(self, context: str = "", complexity: str = "medium") -> Dict[str, Any]:
        """Suggest a decision-making framework."""
        frameworks = {
            "simple": {
                "name": "10-10-10 Rule",
                "description": "How will this matter in 10 minutes, 10 months, 10 years?",
                "best_for": "quick decisions with long-term impact",
            },
            "medium": {
                "name": "Pros/Cons + Second-Order Thinking",
                "description": "List pros/cons, then ask 'and then what?' for each",
                "best_for": "strategic choices with cascading effects",
            },
            "complex": {
                "name": "Decision Matrix + Pre-Mortem",
                "description": "Score options across criteria, then imagine each failed and why",
                "best_for": "high-stakes decisions with multiple options",
            },
            "emotional": {
                "name": "Sleep-On-It + Values Check",
                "description": "Wait 24 hours, check if choice aligns with core values",
                "best_for": "emotionally charged decisions",
            },
        }

        if "emotional" in context.lower() or "feel" in context.lower():
            return frameworks["emotional"]
        elif complexity == "high":
            return frameworks["complex"]
        elif complexity == "low":
            return frameworks["simple"]
        else:
            return frameworks["medium"]

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_accuracy(self):
        """Update decision accuracy."""
        reviewed = [d for d in self._decisions.values() if d.outcome_quality is not None]
        if reviewed:
            self._stats["avg_accuracy"] = round(sum(d.outcome_quality for d in reviewed) / len(reviewed), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "decisions": {k: {
                    "decision_id": v.decision_id,
                    "context": v.context,
                    "options": v.options,
                    "choice": v.choice,
                    "expected_outcome": v.expected_outcome,
                    "category": v.category,
                    "confidence": v.confidence,
                    "timestamp": v.timestamp,
                    "energy_level": v.energy_level,
                    "time_of_day": v.time_of_day,
                    "actual_outcome": v.actual_outcome,
                    "outcome_quality": v.outcome_quality,
                } for k, v in self._decisions.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.decision_journal")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("decisions", {}).items():
                    self._decisions[k] = Decision(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.decision_journal")

    def _log_decision(self, decision: Decision):
        try:
            with open(DECISION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": decision.timestamp,
                    "decision_id": decision.decision_id,
                    "context": decision.context,
                    "choice": decision.choice,
                    "category": decision.category,
                    "confidence": decision.confidence,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.decision_journal")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dj_instance: Optional[DecisionJournal] = None
_dj_lock = threading.Lock()


def get_decision_journal() -> DecisionJournal:
    global _dj_instance
    with _dj_lock:
        if _dj_instance is None:
            _dj_instance = DecisionJournal()
        return _dj_instance
