"""
LOVE Repair Specialist — Restoration Intelligence (Modern AI Pattern)

Most damage is fixable if addressed promptly. This specialist:

1. REPAIR TRACKING
   - Record repair actions and their characteristics
   - Track repair domains (health, relationships, skills, systems, habits)
   - Log repair outcomes and their durability

2. PATTERN ANALYSIS
   - Identify the user's repair profile (proactive, reactive, neglectful, systematic)
   - Find repair strategies that create lasting fixes
   - Detect repair avoidance and its costs

3. REPAIR BUILDING
   - Suggest repair actions matched to current damage
   - Provide damage assessment frameworks
   - Recommendation proactive maintenance practices

4. RESTORATION CULTIVATION
   - Track the correlation between repair speed and outcome quality
   - Alert when damage is being ignored
   - Celebrate successful restoration

Architecture:
- record_repair(damage, domain, action, outcome): Log repair
- get_repair_stats(): Get repair pattern analysis
- get_repair_plan(damage, domain, urgency): Get plan
- get_repair_score(): Calculate overall repair health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "repair_specialist"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REPAIR_LOG = DATA_DIR / "repairs.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RepairEntry:
    """A tracked repair entry."""
    entry_id: str = ""
    damage: str = ""
    domain: str = ""  # health, relationships, skills, systems, habits, environment
    severity: float = 0.5  # 0-1
    repair_action: str = ""
    proactive: bool = False  # was this proactive or reactive
    time_to_repair: float = 0.0  # days
    outcome: str = ""  # fixed, improved, stable, worsened
    durability: float = 0.5  # 0-1
    cost: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RepairSpecialist:
    """
    Intelligent repair specialist with damage detection and proactive maintenance.
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
            "avg_durability": 0.0,
            "avg_time": 0.0,
            "neglect_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_repair(self, damage: str = "", domain: str = "", severity: float = 0.5, repair_action: str = "", proactive: bool = False, time_to_repair: float = 0, outcome: str = "", durability: float = 0.5, cost: float = 0.5, notes: str = "") -> RepairEntry:
        """Record a repair entry."""
        entry_id = f"rep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RepairEntry(
            entry_id=entry_id,
            damage=damage or "unspecified",
            domain=domain or "habits",
            severity=severity,
            repair_action=repair_action,
            proactive=proactive,
            time_to_repair=time_to_repair,
            outcome=outcome or "stable",
            durability=durability,
            cost=cost,
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

    def get_repair_stats(self) -> Dict[str, Any]:
        """Get repair pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "severity_sum": 0.0, "durability_sum": 0.0, "time_sum": 0.0, "cost_sum": 0.0, "proactive_count": 0})
        for e in self._entries:
            by_domain[e.domain]["count"] += 1
            by_domain[e.domain]["severity_sum"] += e.severity
            by_domain[e.domain]["durability_sum"] += e.durability
            by_domain[e.domain]["time_sum"] += e.time_to_repair
            by_domain[e.domain]["cost_sum"] += e.cost
            if e.proactive:
                by_domain[e.domain]["proactive_count"] += 1

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "avg_severity": round(data["severity_sum"] / count, 2),
                "avg_durability": round(data["durability_sum"] / count, 2),
                "avg_time": round(data["time_sum"] / count, 1),
                "avg_cost": round(data["cost_sum"] / count, 2),
                "proactive_rate": round(data["proactive_count"] / count, 2),
            }

        # Outcome analysis
        by_outcome = defaultdict(lambda: {"count": 0, "severity_sum": 0.0, "time_sum": 0.0})
        for e in self._entries:
            by_outcome[e.outcome]["count"] += 1
            by_outcome[e.outcome]["severity_sum"] += e.severity
            by_outcome[e.outcome]["time_sum"] += e.time_to_repair

        outcome_stats = {}
        for o, data in by_outcome.items():
            count = data["count"]
            outcome_stats[o] = {
                "count": count,
                "avg_severity": round(data["severity_sum"] / count, 2),
                "avg_time": round(data["time_sum"] / count, 1),
            }

        # Proactive vs reactive analysis
        proactive = [e for e in self._entries if e.proactive]
        reactive = [e for e in self._entries if not e.proactive]
        if proactive and reactive:
            proactive_durability = sum(e.durability for e in proactive) / len(proactive)
            reactive_durability = sum(e.durability for e in reactive) / len(reactive)
            proactive_cost = sum(e.cost for e in proactive) / len(proactive)
            reactive_cost = sum(e.cost for e in reactive) / len(reactive)
            proactive_time = sum(e.time_to_repair for e in proactive) / len(proactive)
            reactive_time = sum(e.time_to_repair for e in reactive) / len(reactive)
        else:
            proactive_durability = 0
            reactive_durability = 0
            proactive_cost = 0
            reactive_cost = 0
            proactive_time = 0
            reactive_time = 0

        # Neglect detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        high_severity = [e for e in self._entries if e.severity > 0.7]
        if high_severity:
            neglected = sum(1 for e in high_severity if e.time_to_repair > 7)
            neglect_risk = neglected / len(high_severity) > 0.3
        else:
            neglect_risk = False

        # Time-outcome correlation
        fast = [e for e in self._entries if e.time_to_repair <= 1]
        slow = [e for e in self._entries if e.time_to_repair > 7]
        if fast and slow:
            fast_durability = sum(e.durability for e in fast) / len(fast)
            slow_durability = sum(e.durability for e in slow) / len(slow)
        else:
            fast_durability = 0
            slow_durability = 0

        # Recent trend
        if recent:
            recent_durability = sum(e.durability for e in recent) / len(recent)
            recent_time = sum(e.time_to_repair for e in recent) / len(recent)
            recent_proactive = sum(1 for e in recent if e.proactive) / len(recent)
        else:
            recent_durability = 0
            recent_time = 0
            recent_proactive = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_durability = sum(e.durability for e in older) / len(older)
            older_time = sum(e.time_to_repair for e in older) / len(older)
            durability_trend = recent_durability - older_durability
            time_trend = recent_time - older_time
        else:
            durability_trend = 0
            time_trend = 0

        return {
            "total_entries": len(self._entries),
            "domain_stats": domain_stats,
            "outcome_stats": outcome_stats,
            "proactive_vs_reactive": {
                "proactive_durability": round(proactive_durability, 2),
                "reactive_durability": round(reactive_durability, 2),
                "proactive_cost": round(proactive_cost, 2),
                "reactive_cost": round(reactive_cost, 2),
                "proactive_time": round(proactive_time, 1),
                "reactive_time": round(reactive_time, 1),
            },
            "neglect_risk": neglect_risk,
            "time_outcome": {
                "fast_repair_durability": round(fast_durability, 2),
                "slow_repair_durability": round(slow_durability, 2),
            },
            "avg_durability": round(sum(e.durability for e in self._entries) / len(self._entries), 2),
            "avg_time": round(sum(e.time_to_repair for e in self._entries) / len(self._entries), 1),
            "avg_cost": round(sum(e.cost for e in self._entries) / len(self._entries), 2),
            "durability_trend": round(durability_trend, 2),
            "time_trend": round(time_trend, 2),
            "recent_durability": round(recent_durability, 2),
            "recent_time": round(recent_time, 1),
            "recent_proactive_rate": round(recent_proactive, 2),
        }

    def get_repair_plan(self, damage: str = "", domain: str = "", urgency: float = 0.5) -> Dict[str, Any]:
        """Get plan."""
        plans = {
            "health": [
                "Schedule the appointment. Today. Not tomorrow. The body doesn't wait.",
                "Sleep debt is real. Pay it back. 8 hours tonight. No exceptions.",
                "One healthy meal. Not a diet. Just one meal that nourishes you.",
            ],
            "relationships": [
                "Send one message. 'I was wrong. I'm sorry.' Send it now.",
                "Schedule time with someone you've neglected. Put it on the calendar.",
                "Listen without defending. Just listen. That's the repair.",
            ],
            "skills": [
                "Practice for 15 minutes. Consistency beats intensity. Start now.",
                "Find one tutorial. Watch it. Apply one thing from it today.",
                "Teach what you know to someone else. Teaching reveals gaps. Fill them.",
            ],
            "systems": [
                "Fix one broken process. What's the bottleneck? Address it.",
                "Automate one repetitive task. Future you will thank present you.",
                "Document one thing that only you know. Knowledge silos are risks.",
            ],
            "habits": [
                "Restart one habit. Day 1. Not 'when I'm ready.' Now.",
                "Break one bad habit for one day. 24 hours. Prove you can.",
                "Stack a new habit on an existing one. After coffee, meditate. After shower, journal.",
            ],
            "environment": [
                "Clean one space. Desk, car, closet. Order outside creates order inside.",
                "Fix one broken thing. The lightbulb. The squeaky door. Small wins.",
                "Remove one source of friction. What's annoying you daily? Fix it.",
            ],
        }

        selected = plans.get(domain, plans["habits"])

        if urgency > 0.7:
            urgency_note = "Urgent. Damage is compounding. Act today. Even a small action stops the spiral."
        elif urgency > 0.4:
            urgency_note = "Moderate urgency. You have a few days. But don't wait. Momentum matters."
        else:
            urgency_note = "Low urgency. Perfect time for proactive maintenance. Fix it before it breaks."

        return {
            "damage": damage or "general",
            "domain": domain or "habits",
            "urgency": urgency,
            "plan": random.choice(selected),
            "urgency_note": urgency_note,
            "principle": "Most problems don't get better on their own. They get worse. The cost of repair increases with time. Proactive maintenance is cheaper than reactive repair. But when damage happens, repair promptly. Delay is the enemy of restoration.",
        }

    def get_repair_score(self) -> int:
        """Calculate overall repair health (0-100)."""
        if not self._entries:
            return 35

        # Durability and low cost
        avg_durability = sum(e.durability for e in self._entries) / len(self._entries)
        avg_cost = sum(e.cost for e in self._entries) / len(self._entries)

        # Speed
        avg_time = sum(e.time_to_repair for e in self._entries) / len(self._entries)
        speed_score = max(0, 1 - avg_time / 14)

        # Proactive ratio
        proactive = [e for e in self._entries if e.proactive]
        proactive_rate = len(proactive) / len(self._entries)

        # Outcome quality
        fixed = sum(1 for e in self._entries if e.outcome in ["fixed", "improved"])
        outcome_rate = fixed / len(self._entries)

        # Domain variety
        unique_domains = len(set(e.domain for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_durability = sum(e.durability for e in recent) / len(recent)
            recent_time = sum(e.time_to_repair for e in recent) / len(recent)
            recent_proactive = sum(1 for e in recent if e.proactive) / len(recent)
        else:
            recent_durability = 0
            recent_time = 0
            recent_proactive = 0

        # Neglect penalty
        high_severity = [e for e in self._entries if e.severity > 0.7]
        if high_severity:
            neglected = sum(1 for e in high_severity if e.time_to_repair > 7)
            neglect_penalty = min(15, neglected / len(high_severity) * 15)
        else:
            neglect_penalty = 0

        score = (avg_durability * 25) + ((1 - avg_cost) * 15) + (speed_score * 15) + (proactive_rate * 15) + (outcome_rate * 15) + (unique_domains * 2) + (recent_durability * 10) + (recent_proactive * 10) - neglect_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_durability"] = round(sum(e.durability for e in self._entries) / len(self._entries), 2)
            self._stats["avg_time"] = round(sum(e.time_to_repair for e in self._entries) / len(self._entries), 1)

            high_severity = [e for e in self._entries if e.severity > 0.7]
            if high_severity:
                neglected = sum(1 for e in high_severity if e.time_to_repair > 7)
                self._stats["neglect_risk"] = neglected / len(high_severity) > 0.3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.repair_specialist")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.repair_specialist")

    def _log_entry(self, entry: RepairEntry):
        try:
            with open(REPAIR_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "damage": entry.damage,
                    "domain": entry.domain,
                    "severity": entry.severity,
                    "repair_action": entry.repair_action,
                    "proactive": entry.proactive,
                    "time_to_repair": entry.time_to_repair,
                    "outcome": entry.outcome,
                    "durability": entry.durability,
                    "cost": entry.cost,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.repair_specialist")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rs_instance: Optional[RepairSpecialist] = None
_rs_lock = threading.Lock()


def get_repair_specialist() -> RepairSpecialist:
    global _rs_instance
    with _rs_lock:
        if _rs_instance is None:
            _rs_instance = RepairSpecialist()
        return _rs_instance
