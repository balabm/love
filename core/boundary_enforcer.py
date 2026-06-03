"""
LOVE Boundary Enforcer — Limit Intelligence (Modern AI Pattern)

Most boundary violations are self-inflicted. This enforcer:

1. BOUNDARY TRACKING
   - Record boundary settings and violations (internal and external)
   - Track the cost of violated boundaries (energy, time, emotion)
   - Log boundary successes and what made them possible

2. PATTERN ANALYSIS
   - Identify the user's boundary style (rigid, porous, healthy, inconsistent)
   - Find which boundaries are hardest to maintain and why
   - Detect boundary violation triggers (guilt, FOMO, people-pleasing, urgency)

3. BOUNDARY BUILDING
   - Suggest scripts for saying no in specific situations
   - Provide boundary-setting exercises for weak areas
   - Recommend pre-commitment strategies for known triggers

4. PROACTIVE DEFENSE
   - Alert when boundary risk is high
   - Suggest boundary reviews for recurring violations
   - Celebrate maintained boundaries

Architecture:
- record_boundary(boundary, type, maintained, cost): Log boundary
- get_boundary_stats(): Get boundary pattern analysis
- get_boundary_script(situation, type): Get boundary language
- get_boundary_score(): Calculate overall boundary health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "boundary_enforcer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BOUNDARY_LOG = DATA_DIR / "boundaries.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BoundaryEvent:
    """A tracked boundary event."""
    event_id: str = ""
    boundary: str = ""  # what the boundary was
    boundary_type: str = ""  # time, emotional, physical, digital, social, work, energy
    maintained: bool = True
    violation_by: str = ""  # self, other, system
    trigger: str = ""  # what caused the violation
    cost: float = 0.0  # 0-1, cost of violation
    response_used: str = ""  # what they said or did
    satisfaction: float = 0.5  # 0-1, how they felt after
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BoundaryEnforcer:
    """
    Intelligent boundary enforcer with violation analysis and script generation.
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
        self._events: deque = deque(maxlen=200)
        self._stats = {
            "total_events": 0,
            "maintenance_rate": 0.0,
            "avg_cost": 0.0,
            "weakest_type": "",
            "strongest_type": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_boundary(self, boundary: str = "", boundary_type: str = "", maintained: bool = True, violation_by: str = "", trigger: str = "", cost: float = 0.0, response: str = "", satisfaction: float = 0.5, notes: str = "") -> BoundaryEvent:
        """Record a boundary event."""
        event_id = f"boundary_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._events)}"
        event = BoundaryEvent(
            event_id=event_id,
            boundary=boundary or "unspecified",
            boundary_type=boundary_type or "time",
            maintained=maintained,
            violation_by=violation_by or "self",
            trigger=trigger,
            cost=cost,
            response_used=response,
            satisfaction=satisfaction,
            notes=notes,
        )

        with self._lock:
            self._events.append(event)
            self._stats["total_events"] += 1
            self._update_stats()

        self._save_stats()
        self._log_event(event)

        return event

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_boundary_stats(self) -> Dict[str, Any]:
        """Get boundary pattern analysis."""
        if not self._events:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "maintained": 0, "cost_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._events:
            by_type[e.boundary_type]["count"] += 1
            if e.maintained:
                by_type[e.boundary_type]["maintained"] += 1
            by_type[e.boundary_type]["cost_sum"] += e.cost
            by_type[e.boundary_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "maintenance_rate": round(data["maintained"] / count, 2),
                "avg_cost": round(data["cost_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        weakest = min(type_stats.items(), key=lambda x: x[1]["maintenance_rate"]) if type_stats else ("", {})
        strongest = max(type_stats.items(), key=lambda x: x[1]["maintenance_rate"]) if type_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "maintained": 0})
        for e in self._events:
            if e.trigger:
                by_trigger[e.trigger]["count"] += 1
                if e.maintained:
                    by_trigger[e.trigger]["maintained"] += 1

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            trigger_stats[tr] = {
                "count": count,
                "maintenance_rate": round(data["maintained"] / count, 2),
            }

        # Violator analysis
        by_violator = defaultdict(lambda: {"count": 0, "cost_sum": 0.0})
        for e in self._events:
            if not e.maintained:
                by_violator[e.violation_by]["count"] += 1
                by_violator[e.violation_by]["cost_sum"] += e.cost

        violator_stats = {}
        for v, data in by_violator.items():
            count = data["count"]
            violator_stats[v] = {
                "count": count,
                "avg_cost": round(data["cost_sum"] / count, 2),
            }

        # Response effectiveness
        responses = [e for e in self._events if e.response_used]
        if responses:
            by_response = defaultdict(lambda: {"count": 0, "maintained": 0, "satisfaction_sum": 0.0})
            for e in responses:
                by_response[e.response_used]["count"] += 1
                if e.maintained:
                    by_response[e.response_used]["maintained"] += 1
                by_response[e.response_used]["satisfaction_sum"] += e.satisfaction
            
            response_stats = {}
            for r, data in by_response.items():
                count = data["count"]
                response_stats[r] = {
                    "count": count,
                    "success_rate": round(data["maintained"] / count, 2),
                    "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                }
        else:
            response_stats = {}

        return {
            "total_events": len(self._events),
            "type_stats": type_stats,
            "weakest_type": weakest[0],
            "strongest_type": strongest[0],
            "trigger_stats": trigger_stats,
            "violator_stats": violator_stats,
            "response_stats": response_stats,
            "maintenance_rate": round(sum(1 for e in self._events if e.maintained) / len(self._events), 2),
            "avg_cost": round(sum(e.cost for e in self._events if not e.maintained) / max(1, sum(1 for e in self._events if not e.maintained)), 2),
        }

    def get_boundary_script(self, situation: str = "", boundary_type: str = "", relationship: str = "") -> Dict[str, Any]:
        """Get boundary language."""
        scripts = {
            "time": {
                "work": [
                    "I work until 6pm. After that, I'm offline.",
                    "I can give this 30 minutes now, or we can schedule a proper block tomorrow.",
                    "My calendar is full today. What deadline are we working toward?",
                ],
                "friend": [
                    "I'd love to, but I need tonight to recharge. How about Saturday?",
                    "I can stay for an hour, then I need to head home.",
                    "I'm saying no to plans this week so I can say yes to us next week.",
                ],
                "family": [
                    "I need 30 minutes of quiet time when I get home. Then I'm all yours.",
                    "I can't take on that right now, but I can help you find someone who can.",
                    "This weekend I'm protecting family time. No exceptions.",
                ],
            },
            "emotional": {
                "work": [
                    "I'm not in a space to process this right now. Can we revisit tomorrow?",
                    "I hear you. I need some time before I respond to that.",
                    "I'm taking that feedback seriously. I'll need a day to sit with it.",
                ],
                "friend": [
                    "I care about you, and I'm not available to be your therapist tonight.",
                    "I'm emotionally full right now. Can we talk about something light?",
                    "I need to protect my peace today. Let's connect when I'm more resourced.",
                ],
                "family": [
                    "I love you, and I'm not going to discuss this when we're both activated.",
                    "I'm setting a boundary around how we talk about [topic]. It hurts me.",
                    "I need you to ask before giving advice. I just need to be heard.",
                ],
            },
            "digital": {
                "general": [
                    "I don't check email after 8pm. It'll wait.",
                    "I'm not available on weekends for non-urgent messages.",
                    "I use my phone for 30 minutes in the morning, then it stays in another room.",
                ],
            },
            "work": {
                "colleague": [
                    "I can take this on if we deprioritize something else. What should drop?",
                    "My plate is full. Let's look at who's better resourced for this.",
                    "I can review this Friday. I need focused time today for [current project].",
                ],
            },
        }

        type_scripts = scripts.get(boundary_type, scripts["time"])
        rel_scripts = type_scripts.get(relationship, type_scripts.get("general", type_scripts.get("work", ["I'm not available for that right now."])))
        script = random.choice(rel_scripts)

        if relationship == "close_friend":
            tone = "warm but firm"
        elif relationship == "boss":
            tone = "professional and solution-oriented"
        elif relationship == "family":
            tone = "loving but clear"
        else:
            tone = "direct and respectful"

        return {
            "boundary_type": boundary_type or "general",
            "situation": situation or "unspecified",
            "relationship": relationship or "general",
            "script": script,
            "tone": tone,
            "prep": "Before saying this, breathe. Ground yourself. You don't need to apologize for having limits.",
            "aftercare": "Afterward, don't over-explain. Don't negotiate with yourself. The boundary stands.",
        }

    def get_boundary_score(self) -> int:
        """Calculate overall boundary health (0-100)."""
        if not self._events:
            return 40

        # Maintenance rate
        maintained = sum(1 for e in self._events if e.maintained)
        maintenance_rate = maintained / len(self._events)

        # Low cost (when boundaries are violated, cost is managed)
        violated = [e for e in self._events if not e.maintained]
        if violated:
            avg_cost = sum(e.cost for e in violated) / len(violated)
        else:
            avg_cost = 0

        # Satisfaction after boundary events
        avg_satisfaction = sum(e.satisfaction for e in self._events) / len(self._events)

        # Self vs other violations (self-violations are more controllable)
        self_violations = sum(1 for e in self._events if not e.maintained and e.violation_by == "self")
        other_violations = sum(1 for e in self._events if not e.maintained and e.violation_by == "other")
        violation_balance = 1 - (self_violations / max(1, len(self._events))) * 0.5

        # Recent trend
        recent = list(self._events)[-10:]
        recent_maintained = sum(1 for e in recent if e.maintained) / len(recent)
        older = list(self._events)[:-10] if len(self._events) > 10 else []
        if older:
            older_maintained = sum(1 for e in older if e.maintained) / len(older)
            trend = recent_maintained - older_maintained
        else:
            trend = 0

        # Type coverage
        unique_types = len(set(e.boundary_type for e in self._events))

        score = (maintenance_rate * 30) + ((1 - avg_cost) * 15) + (avg_satisfaction * 15) + (violation_balance * 10) + (trend * 10) + (unique_types * 2)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._events:
            maintained = sum(1 for e in self._events if e.maintained)
            self._stats["maintenance_rate"] = round(maintained / len(self._events), 2)
            
            violated = [e for e in self._events if not e.maintained]
            if violated:
                self._stats["avg_cost"] = round(sum(e.cost for e in violated) / len(violated), 2)

            by_type = defaultdict(lambda: {"maintained": 0, "total": 0})
            for e in self._events:
                by_type[e.boundary_type]["total"] += 1
                if e.maintained:
                    by_type[e.boundary_type]["maintained"] += 1
            
            if by_type:
                weakest = min(by_type.items(), key=lambda x: x[1]["maintained"] / max(1, x[1]["total"]))
                strongest = max(by_type.items(), key=lambda x: x[1]["maintained"] / max(1, x[1]["total"]))
                self._stats["weakest_type"] = weakest[0]
                self._stats["strongest_type"] = strongest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.boundary_enforcer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.boundary_enforcer")

    def _log_event(self, event: BoundaryEvent):
        try:
            with open(BOUNDARY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": event.timestamp,
                    "boundary": event.boundary,
                    "type": event.boundary_type,
                    "maintained": event.maintained,
                    "violation_by": event.violation_by,
                    "cost": event.cost,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.boundary_enforcer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_be_instance: Optional[BoundaryEnforcer] = None
_be_lock = threading.Lock()


def get_boundary_enforcer() -> BoundaryEnforcer:
    global _be_instance
    with _be_lock:
        if _be_instance is None:
            _be_instance = BoundaryEnforcer()
        return _be_instance
