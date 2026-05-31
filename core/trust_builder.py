"""
LOVE Trust Builder — Relational Intelligence (Modern AI Pattern)

Most trust is built slowly and broken suddenly. This builder:

1. TRUST TRACKING
   - Record trust-building moments and trust-breaking incidents
   - Track consistency, reliability, and honesty in relationships
   - Log repairs after trust violations

2. PATTERN ANALYSIS
   - Identify who consistently builds trust vs erodes it
   - Detect the user's own trust-building and trust-breaking patterns
   - Find which trust dimensions are strongest/weakest (competence, integrity, benevolence)

3. REPAIR GUIDANCE
   - Suggest trust repair steps after violations
   - Provide scripts for apologizing and making amends
   - Track the timeline of trust rebuilding

4. PROACTIVE MANAGEMENT
   - Alert when trust is accumulating in one-sided relationships
   - Suggest trust-building actions for important relationships
   - Track relationship trust scores over time

Architecture:
- record_trust_event(person, type, dimension, impact): Log event
- get_trust_stats(): Get trust pattern analysis
- get_repair_guide(violation_type): Get repair strategy
- get_trust_score(person): Calculate relationship trust level
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "trust_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRUST_LOG = DATA_DIR / "trust.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TrustEvent:
    """A tracked trust event."""
    event_id: str = ""
    person: str = ""
    event_type: str = ""  # built, broken, repaired, maintained
    dimension: str = ""  # competence, integrity, benevolence, consistency
    impact: float = 0.0  # -1 to 1
    description: str = ""
    repair_attempted: bool = False
    repair_successful: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class TrustBuilder:
    """
    Intelligent trust builder with violation tracking and repair guidance.
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
            "trust_built": 0,
            "trust_broken": 0,
            "repair_rate": 0.0,
            "strongest_dimension": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_trust_event(self, person: str = "", event_type: str = "", dimension: str = "", impact: float = 0.0, description: str = "", repair_attempted: bool = False, repair_successful: bool = False, notes: str = "") -> TrustEvent:
        """Record a trust event."""
        event_id = f"trust_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._events)}"
        event = TrustEvent(
            event_id=event_id,
            person=person or "unspecified",
            event_type=event_type or "maintained",
            dimension=dimension or "consistency",
            impact=impact,
            description=description,
            repair_attempted=repair_attempted,
            repair_successful=repair_successful,
            notes=notes,
        )

        with self._lock:
            self._events.append(event)
            self._stats["total_events"] += 1
            if event_type == "built":
                self._stats["trust_built"] += 1
            elif event_type == "broken":
                self._stats["trust_broken"] += 1
            self._update_stats()

        self._save_stats()
        self._log_event(event)

        return event

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_trust_stats(self) -> Dict[str, Any]:
        """Get trust pattern analysis."""
        if not self._events:
            return {"status": "insufficient_data"}

        # Person analysis
        by_person = defaultdict(lambda: {"events": 0, "built": 0, "broken": 0, "impact_sum": 0.0, "repair_attempts": 0, "repair_success": 0})
        for e in self._events:
            by_person[e.person]["events"] += 1
            if e.event_type == "built":
                by_person[e.person]["built"] += 1
            elif e.event_type == "broken":
                by_person[e.person]["broken"] += 1
            by_person[e.person]["impact_sum"] += e.impact
            if e.repair_attempted:
                by_person[e.person]["repair_attempts"] += 1
            if e.repair_successful:
                by_person[e.person]["repair_success"] += 1

        person_stats = {}
        for p, data in by_person.items():
            events = data["events"]
            person_stats[p] = {
                "events": events,
                "built": data["built"],
                "broken": data["broken"],
                "net_trust": round(data["impact_sum"], 2),
                "repair_rate": round(data["repair_success"] / max(1, data["repair_attempts"]), 2) if data["repair_attempts"] else 0,
                "status": "strong" if data["impact_sum"] > 2 else "developing" if data["impact_sum"] > 0 else "fragile" if data["impact_sum"] > -2 else "broken",
            }

        # Dimension analysis
        by_dimension = defaultdict(lambda: {"count": 0, "impact_sum": 0.0})
        for e in self._events:
            by_dimension[e.dimension]["count"] += 1
            by_dimension[e.dimension]["impact_sum"] += e.impact

        dimension_stats = {}
        for d, data in by_dimension.items():
            count = data["count"]
            dimension_stats[d] = {
                "count": count,
                "avg_impact": round(data["impact_sum"] / count, 2),
                "strength": "strong" if data["impact_sum"] / count > 0.3 else "moderate" if data["impact_sum"] / count > 0 else "weak",
            }

        strongest = max(dimension_stats.items(), key=lambda x: x[1]["avg_impact"]) if dimension_stats else ("", {})

        # Recent trend
        recent = [e for e in self._events if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_impact = sum(e.impact for e in recent)
            trend = "building" if recent_impact > 1 else "eroding" if recent_impact < -1 else "stable"
        else:
            trend = "stable"

        return {
            "total_events": len(self._events),
            "person_stats": person_stats,
            "dimension_stats": dimension_stats,
            "strongest_dimension": strongest[0],
            "trend": trend,
            "trust_built": self._stats["trust_built"],
            "trust_broken": self._stats["trust_broken"],
            "net_trust": round(sum(e.impact for e in self._events), 2),
        }

    def get_repair_guide(self, violation_type: str = "", severity: str = "medium") -> Dict[str, Any]:
        """Get trust repair strategy."""
        guides = {
            "broken_promise": {
                "steps": [
                    "Acknowledge the broken promise specifically (not vaguely)",
                    "Explain why it happened without making excuses",
                    "Make a new, smaller promise you can definitely keep",
                    "Follow through immediately on the new promise",
                ],
                "timeline": "Immediate acknowledgment, then consistent action for 2-4 weeks",
            },
            "dishonesty": {
                "steps": [
                    "Come clean completely—partial truth extends the damage",
                    "Explain why you lied (fear, shame, protection)",
                    "Accept their anger without defending yourself",
                    "Give them space to process without demanding forgiveness",
                ],
                "timeline": "Immediate confession, then patience for weeks to months",
            },
            "incompetence": {
                "steps": [
                    "Acknowledge the failure without self-deprecation",
                    "Explain what you'll do differently next time",
                    "Ask for their input on how to improve",
                    "Deliver a small win in the same area soon",
                ],
                "timeline": "Immediate plan, then demonstrate competence within 1-2 weeks",
            },
            "neglect": {
                "steps": [
                    "Acknowledge that you weren't there when they needed you",
                    "Ask what they needed that they didn't get",
                    "Commit to specific, regular check-ins",
                    "Follow through even when it's inconvenient",
                ],
                "timeline": "Immediate commitment, then sustained presence for 1-2 months",
            },
            "betrayal": {
                "steps": [
                    "Acknowledge the depth of the betrayal without minimizing",
                    "Accept that they may never fully trust you again",
                    "Offer complete transparency going forward",
                    "Be patient with their need to verify your words",
                ],
                "timeline": "Months to years. Focus on consistency, not speed.",
            },
        }

        base = guides.get(violation_type, guides["broken_promise"])

        if severity == "high":
            base["note"] = "This is a serious violation. Professional support (couples therapy, etc.) is recommended."
        elif severity == "low":
            base["note"] = "This is repairable with prompt, sincere action."

        return base

    def get_trust_score(self, person: str = "") -> int:
        """Calculate relationship trust level (0-100)."""
        if not self._events:
            return 50

        # Filter by person if specified
        events = [e for e in self._events if not person or e.person == person]
        if not events:
            return 50

        # Net impact
        net_impact = sum(e.impact for e in events)
        
        # Recent weighting
        recent = [e for e in events if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        recent_impact = sum(e.impact for e in recent) if recent else 0

        # Repair success
        repairs = [e for e in events if e.repair_attempted]
        if repairs:
            successful = sum(1 for e in repairs if e.repair_successful)
            repair_score = successful / len(repairs)
        else:
            repair_score = 1.0

        # Calculate score
        base = 50
        impact_bonus = net_impact * 10
        recent_bonus = recent_impact * 15
        repair_bonus = (repair_score - 0.5) * 20

        score = base + impact_bonus + recent_bonus + repair_bonus
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        repairs = [e for e in self._events if e.repair_attempted]
        if repairs:
            successful = sum(1 for e in repairs if e.repair_successful)
            self._stats["repair_rate"] = round(successful / len(repairs), 2)

        by_dimension = defaultdict(lambda: {"impact": 0.0, "count": 0})
        for e in self._events:
            by_dimension[e.dimension]["impact"] += e.impact
            by_dimension[e.dimension]["count"] += 1
        
        if by_dimension:
            strongest = max(by_dimension.items(), key=lambda x: x[1]["impact"] / max(1, x[1]["count"]))
            self._stats["strongest_dimension"] = strongest[0]

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

    def _log_event(self, event: TrustEvent):
        try:
            with open(TRUST_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": event.timestamp,
                    "person": event.person,
                    "type": event.event_type,
                    "dimension": event.dimension,
                    "impact": event.impact,
                    "repair": event.repair_attempted,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_tb_instance: Optional[TrustBuilder] = None
_tb_lock = threading.Lock()


def get_trust_builder() -> TrustBuilder:
    global _tb_instance
    with _tb_lock:
        if _tb_instance is None:
            _tb_instance = TrustBuilder()
        return _tb_instance
