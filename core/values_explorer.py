"""
LOVE Values Explorer — Axiology Intelligence (Modern AI Pattern)

Most people inherit values without examining them. This explorer:

1. VALUES TRACKING
   - Record values and their importance ratings
   - Track value-expression in daily decisions
   - Log value conflicts and their resolution

2. PATTERN ANALYSIS
   - Identify the user's value hierarchy (what matters most)
   - Find value-expression gaps (where stated values don't match actions)
   - Detect value drift over time

3. VALUES CLARIFICATION
   - Suggest values-clarification exercises
   - Provide conflict-resolution frameworks for competing values
   - Recommend value-aligned goal-setting

4. ALIGNMENT TRACKING
   - Track the correlation between value alignment and wellbeing
   - Alert when actions contradict core values
   - Celebrate values-based decisions

Architecture:
- record_value(value, importance, expression): Log value
- get_values_stats(): Get values pattern analysis
- get_clarification_exercise(conflict_type): Get exercise
- get_values_score(): Calculate overall values health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "values_explorer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VALUES_LOG = DATA_DIR / "values.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ValueEntry:
    """A tracked value entry."""
    entry_id: str = ""
    value: str = ""
    importance: float = 0.5  # 0-1
    expression: float = 0.5  # 0-1, how much it's expressed
    category: str = ""  # personal, professional, relational, societal, spiritual
    conflicts_with: List[str] = field(default_factory=list)
    recent_example: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ValuesExplorer:
    """
    Intelligent values explorer with hierarchy analysis and expression tracking.
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
        self._entries: deque = deque(maxlen=200)
        self._stats = {
            "total_entries": 0,
            "avg_importance": 0.0,
            "avg_expression": 0.0,
            "biggest_gap": "",
            "top_value": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_value(self, value: str = "", importance: float = 0.5, expression: float = 0.5, category: str = "", conflicts: Optional[List[str]] = None, example: str = "", notes: str = "") -> ValueEntry:
        """Record a value entry."""
        entry_id = f"val_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ValueEntry(
            entry_id=entry_id,
            value=value or "unspecified",
            importance=importance,
            expression=expression,
            category=category or "personal",
            conflicts_with=conflicts or [],
            recent_example=example,
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

    def get_values_stats(self) -> Dict[str, Any]:
        """Get values pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Value analysis
        by_value = defaultdict(lambda: {"count": 0, "importance_sum": 0.0, "expression_sum": 0.0, "conflicts": []})
        for e in self._entries:
            by_value[e.value]["count"] += 1
            by_value[e.value]["importance_sum"] += e.importance
            by_value[e.value]["expression_sum"] += e.expression
            by_value[e.value]["conflicts"].extend(e.conflicts_with)

        value_stats = {}
        for v, data in by_value.items():
            count = data["count"]
            avg_importance = data["importance_sum"] / count
            avg_expression = data["expression_sum"] / count
            value_stats[v] = {
                "count": count,
                "avg_importance": round(avg_importance, 2),
                "avg_expression": round(avg_expression, 2),
                "gap": round(avg_importance - avg_expression, 2),
                "conflicts": list(set(data["conflicts"])),
            }

        # Top value
        top = max(value_stats.items(), key=lambda x: x[1]["avg_importance"]) if value_stats else ("", {})

        # Biggest gap
        gaps = {v: d["gap"] for v, d in value_stats.items() if d["gap"] > 0.3}
        biggest_gap = max(gaps.items(), key=lambda x: x[1]) if gaps else ("", 0)

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "importance_sum": 0.0, "expression_sum": 0.0})
        for e in self._entries:
            by_category[e.category]["count"] += 1
            by_category[e.category]["importance_sum"] += e.importance
            by_category[e.category]["expression_sum"] += e.expression

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            category_stats[c] = {
                "count": count,
                "avg_importance": round(data["importance_sum"] / count, 2),
                "avg_expression": round(data["expression_sum"] / count, 2),
                "gap": round((data["importance_sum"] - data["expression_sum"]) / count, 2),
            }

        # Conflict analysis
        all_conflicts = []
        for e in self._entries:
            for c in e.conflicts_with:
                all_conflicts.append({"value": e.value, "conflicts_with": c})

        # Expression trend
        recent = list(self._entries)[-10:]
        if recent:
            recent_expression = sum(e.expression for e in recent) / len(recent)
        else:
            recent_expression = 0

        older = list(self._entries)[:-10] if len(self._entries) > 10 else []
        if older:
            older_expression = sum(e.expression for e in older) / len(older)
            trend = recent_expression - older_expression
        else:
            trend = 0

        return {
            "total_entries": len(self._entries),
            "value_stats": value_stats,
            "top_value": top[0],
            "biggest_gap": biggest_gap[0],
            "gap_size": biggest_gap[1],
            "category_stats": category_stats,
            "conflicts": all_conflicts,
            "avg_importance": round(sum(e.importance for e in self._entries) / len(self._entries), 2),
            "avg_expression": round(sum(e.expression for e in self._entries) / len(self._entries), 2),
            "expression_trend": round(trend, 2),
        }

    def get_clarification_exercise(self, conflict_type: str = "", focus_value: str = "") -> Dict[str, Any]:
        """Get exercise."""
        exercises = {
            "time": {
                "prompt": "You say you value [X], but you spend your time on [Y]. One of these is your real value.",
                "exercise": "Track your time for 3 days. Compare it to your stated values. The mismatch is data, not shame.",
                "question": "If an alien observed your calendar, what would they say you value most?",
            },
            "money": {
                "prompt": "You say you value [X], but you spend your money on [Y]. Your wallet knows your real values.",
                "exercise": "Review last month's spending. Each category is a vote for what matters.",
                "question": "If you had to cut spending by 50%, what would you keep? That's your real value hierarchy.",
            },
            "energy": {
                "prompt": "You say you value [X], but you give your best energy to [Y]. Energy is truth.",
                "exercise": "For one week, rate your energy by activity. High energy = aligned values.",
                "question": "What do you do even when you're exhausted? That's a core value.",
            },
            "relationships": {
                "prompt": "You say you value [X], but your closest relationships reflect [Y]. We become our company.",
                "exercise": "List your 5 closest relationships. What values do they embody? Do they match yours?",
                "question": "Who do you admire most? What do they value? That's a mirror.",
            },
            "decisions": {
                "prompt": "You say you value [X], but under pressure you choose [Y]. Pressure reveals truth.",
                "exercise": "Review 3 hard decisions from last year. What did you actually choose? What does that reveal?",
                "question": "When you have to choose between two good things, what breaks the tie?",
            },
        }

        base = exercises.get(conflict_type, exercises["time"])

        return {
            "conflict_type": conflict_type or "general",
            "focus_value": focus_value or "unspecified",
            **base,
            "reminder": "Values aren't what you say. Values are what you do when you have to choose. Clarify, don't judge.",
        }

    def get_values_score(self) -> int:
        """Calculate overall values health (0-100)."""
        if not self._entries:
            return 35

        # Expression alignment
        gaps = []
        for e in self._entries:
            gaps.append(e.importance - e.expression)
        avg_gap = sum(gaps) / len(gaps)

        # Low conflict
        conflict_count = sum(len(e.conflicts_with) for e in self._entries)
        conflict_penalty = min(15, conflict_count * 2)

        # Recent trend
        recent = list(self._entries)[-10:]
        if recent:
            recent_expression = sum(e.expression for e in recent) / len(recent)
        else:
            recent_expression = 0
        older = list(self._entries)[:-10] if len(self._entries) > 10 else []
        if older:
            older_expression = sum(e.expression for e in older) / len(older)
            trend = recent_expression - older_expression
        else:
            trend = 0

        # Category balance
        categories = set(e.category for e in self._entries)
        category_bonus = len(categories) * 2

        # Importance clarity
        high_importance = [e for e in self._entries if e.importance > 0.7]
        if high_importance:
            high_expression = sum(e.expression for e in high_importance) / len(high_importance)
        else:
            high_expression = 0

        score = 50 + ((1 - avg_gap) * 25) + (trend * 15) + (high_expression * 15) + category_bonus - conflict_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_importance"] = round(sum(e.importance for e in self._entries) / len(self._entries), 2)
            self._stats["avg_expression"] = round(sum(e.expression for e in self._entries) / len(self._entries), 2)

            by_value = defaultdict(lambda: {"importance": 0.0, "expression": 0.0, "count": 0})
            for e in self._entries:
                by_value[e.value]["importance"] += e.importance
                by_value[e.value]["expression"] += e.expression
                by_value[e.value]["count"] += 1
            
            if by_value:
                top = max(by_value.items(), key=lambda x: x[1]["importance"] / max(1, x[1]["count"]))
                self._stats["top_value"] = top[0]
                
                gaps = {v: (d["importance"] - d["expression"]) / max(1, d["count"]) for v, d in by_value.items()}
                biggest = max(gaps.items(), key=lambda x: x[1])
                self._stats["biggest_gap"] = biggest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.values_explorer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.values_explorer")

    def _log_entry(self, entry: ValueEntry):
        try:
            with open(VALUES_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "value": entry.value,
                    "importance": entry.importance,
                    "expression": entry.expression,
                    "category": entry.category,
                    "conflicts": entry.conflicts_with,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.values_explorer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ve_instance: Optional[ValuesExplorer] = None
_ve_lock = threading.Lock()


def get_values_explorer() -> ValuesExplorer:
    global _ve_instance
    with _ve_lock:
        if _ve_instance is None:
            _ve_instance = ValuesExplorer()
        return _ve_instance
