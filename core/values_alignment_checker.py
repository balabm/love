"""
LOVE Values Alignment Checker — Integrity Monitor (Modern AI Pattern)

Most people have values but don't track whether daily actions align.
This checker:

1. VALUES DEFINITION
   - Track core values (health, family, growth, integrity, creativity, etc.)
   - Weight values by personal priority
   - Allow values to evolve over time

2. ALIGNMENT SCORING
   - Score how well recent actions align with each value
   - Calculate overall integrity score
   - Detect value neglect (values that haven't been acted on recently)

3. CONFLICT DETECTION
   - Identify when actions conflict with stated values
   - Detect situations where two values are in tension
   - Suggest resolution paths for value conflicts

4. PROACTIVE ALIGNMENT
   - Suggest daily actions that honor neglected values
   - Celebrate when alignment improves
   - Warn when alignment drifts significantly

Architecture:
- add_value(name, priority): Define a core value
- record_action(action, values_supported): Log an action
- get_alignment_score(): Get overall alignment score
- get_neglected_values(): Find values being ignored
- get_alignment_suggestions(): Suggest actions to restore balance
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

DATA_DIR = Path(__file__).parent.parent / "data" / "values_alignment"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACTION_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Value:
    """A core value with tracking."""
    name: str = ""
    priority: float = 0.5  # 0-1
    description: str = ""
    last_action: Optional[str] = None
    action_count: int = 0
    alignment_score: float = 0.5  # 0-1
    status: str = "active"  # active, neglected, honored


@dataclass
class Action:
    """An action that supports values."""
    action: str = ""
    values_supported: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    energy_invested: float = 0.5  # 0-1


class ValuesAlignmentChecker:
    """
    Monitor alignment between actions and stated values.
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
        self._values: Dict[str, Value] = {}
        self._actions: deque = deque(maxlen=500)
        self._stats = {
            "overall_alignment": 50,
            "values_defined": 0,
            "actions_logged": 0,
            "most_honored_value": "",
            "most_neglected_value": "",
        }
        self._load_stats()

    # ── Core Management ─────────────────────────────────────────────────────

    def add_value(self, name: str, priority: float = 0.5, description: str = ""):
        """Add or update a core value."""
        if name not in self._values:
            self._values[name] = Value(name=name, priority=priority, description=description)
            self._stats["values_defined"] = len(self._values)
            self._save_stats()
        else:
            self._values[name].priority = priority
            self._values[name].description = description or self._values[name].description

    def record_action(self, action: str, values_supported: List[str], energy_invested: float = 0.5):
        """Record an action that supports values."""
        entry = Action(
            action=action,
            values_supported=values_supported,
            energy_invested=energy_invested,
        )

        with self._lock:
            self._actions.append(entry)
            self._stats["actions_logged"] += 1

            # Update value tracking
            for value_name in values_supported:
                if value_name in self._values:
                    value = self._values[value_name]
                    value.last_action = entry.timestamp
                    value.action_count += 1

            self._update_alignment_scores()

        self._save_stats()
        self._log_action(entry)

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_alignment_score(self) -> int:
        """Calculate overall alignment score (0-100)."""
        if not self._values:
            return 50

        # Weighted average of value alignment scores
        total_weight = sum(v.priority for v in self._values.values())
        if total_weight == 0:
            return 50

        weighted_sum = sum(v.alignment_score * v.priority for v in self._values.values())
        overall = round((weighted_sum / total_weight) * 100)
        self._stats["overall_alignment"] = overall
        return overall

    def get_neglected_values(self, days: int = 7) -> List[Dict[str, Any]]:
        """Find values that haven't been acted on recently."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        neglected = []

        for value in self._values.values():
            if not value.last_action or value.last_action < cutoff:
                days_since = 999
                if value.last_action:
                    try:
                        last = datetime.fromisoformat(value.last_action)
                        days_since = (datetime.now() - last).days
                    except Exception as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.values_alignment_checker")

                neglected.append({
                    "name": value.name,
                    "priority": value.priority,
                    "days_since_action": days_since,
                    "description": value.description,
                    "urgency": "high" if value.priority > 0.7 else "medium",
                })

        return sorted(neglected, key=lambda x: x["priority"], reverse=True)

    def get_alignment_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest actions to improve alignment."""
        suggestions = []
        neglected = self.get_neglected_values(7)

        # Suggest actions for neglected high-priority values
        for value in neglected[:3]:
            if value["priority"] > 0.5:
                suggestions.append({
                    "value": value["name"],
                    "suggestion": self._suggest_action_for_value(value["name"]),
                    "priority": value["priority"],
                    "reason": f"{value['name']} is a high-priority value but hasn't been acted on in {value['days_since_action']} days",
                })

        # Check for overall alignment drift
        overall = self.get_alignment_score()
        if overall < 40:
            suggestions.append({
                "value": "overall",
                "suggestion": "Review your top 3 values and plan one action for each today",
                "priority": 1.0,
                "reason": "Overall alignment is low. Values need intentional attention.",
            })

        return suggestions

    def get_value_breakdown(self) -> List[Dict[str, Any]]:
        """Get detailed breakdown of each value."""
        result = []
        for value in sorted(self._values.values(), key=lambda v: v.priority, reverse=True):
            result.append({
                "name": value.name,
                "priority": value.priority,
                "alignment_score": round(value.alignment_score, 2),
                "action_count": value.action_count,
                "last_action": value.last_action,
                "status": value.status,
                "description": value.description,
            })
        return result

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_alignment_scores(self):
        """Update alignment scores for all values."""
        cutoff_7d = (datetime.now() - timedelta(days=7)).isoformat()
        cutoff_30d = (datetime.now() - timedelta(days=30)).isoformat()

        for value in self._values.values():
            # Count recent actions
            recent_7d = sum(1 for a in self._actions if value.name in a.values_supported and a.timestamp > cutoff_7d)
            recent_30d = sum(1 for a in self._actions if value.name in a.values_supported and a.timestamp > cutoff_30d)

            # Alignment score based on recency and frequency
            if recent_7d > 0:
                score = min(1.0, 0.5 + recent_7d * 0.1)
                value.status = "honored"
            elif recent_30d > 0:
                score = 0.4
                value.status = "active"
            else:
                score = 0.2
                value.status = "neglected"

            value.alignment_score = round(score, 2)

        # Update stats
        honored = [v for v in self._values.values() if v.status == "honored"]
        neglected = [v for v in self._values.values() if v.status == "neglected"]
        self._stats["most_honored_value"] = max(honored, key=lambda v: v.alignment_score).name if honored else ""
        self._stats["most_neglected_value"] = max(neglected, key=lambda v: v.priority).name if neglected else ""

    def _suggest_action_for_value(self, value_name: str) -> str:
        """Suggest a specific action for a value."""
        suggestions = {
            "health": "Exercise for 20 minutes or prepare a healthy meal",
            "family": "Call a family member or plan quality time",
            "growth": "Read for 15 minutes or work on a skill",
            "integrity": "Review a recent decision for honesty, or keep a commitment",
            "creativity": "Create something for 15 minutes (write, draw, code)",
            "peace": "Meditate for 10 minutes or spend time in nature",
            "connection": "Reach out to a friend or attend a social event",
            "impact": "Do one thing that helps someone else",
            "learning": "Study a new topic for 15 minutes",
            "balance": "Set a boundary or say no to something",
            "finance": "Review spending or make a financial plan",
            "fun": "Schedule something enjoyable today",
        }
        return suggestions.get(value_name.lower(), f"Do one small thing that honors {value_name}")

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "values": {k: {
                    "name": v.name,
                    "priority": v.priority,
                    "description": v.description,
                    "last_action": v.last_action,
                    "action_count": v.action_count,
                    "alignment_score": v.alignment_score,
                    "status": v.status,
                } for k, v in self._values.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.values_alignment_checker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("values", {}).items():
                    self._values[k] = Value(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.values_alignment_checker")

    def _log_action(self, action: Action):
        try:
            with open(ACTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": action.timestamp,
                    "action": action.action,
                    "values": action.values_supported,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.values_alignment_checker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vac_instance: Optional[ValuesAlignmentChecker] = None
_vac_lock = threading.Lock()


def get_values_alignment_checker() -> ValuesAlignmentChecker:
    global _vac_instance
    with _vac_lock:
        if _vac_instance is None:
            _vac_instance = ValuesAlignmentChecker()
        return _vac_instance
