"""
LOVE Boundary Architect — Protection Intelligence (Modern AI Pattern)

Most burnout comes from porous boundaries. This architect:

1. BOUNDARY TRACKING
   - Record boundary settings and their characteristics
   - Track boundary types (time, energy, emotional, physical, digital)
   - Log enforcement outcomes and their effects on wellbeing

2. PATTERN ANALYSIS
   - Identify the user's boundary profile (rigid, porous, flexible, absent)
   - Find boundary strategies that protect without isolating
   - Detect boundary erosion patterns

3. BOUNDARY BUILDING
   - Suggest boundary settings matched to current drains
   - Provide scripts for difficult boundary conversations
   - Recommendation maintenance practices

4. PROTECTION CULTIVATION
   - Track the correlation between boundary strength and energy
   - Alert when boundaries are being consistently violated
   - Celebrate boundary maintenance

Architecture:
- record_boundary(domain, boundary, enforcement, outcome): Log boundary
- get_boundary_stats(): Get boundary pattern analysis
- get_boundary_script(domain, situation): Get script
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

DATA_DIR = Path(__file__).parent.parent / "data" / "boundary_architect"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BOUNDARY_LOG = DATA_DIR / "boundaries.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BoundaryEntry:
    """A tracked boundary entry."""
    entry_id: str = ""
    domain: str = ""  # time, energy, emotional, physical, digital
    boundary: str = ""  # what was the boundary
    enforcement: float = 0.5  # 0-1, how well was it enforced
    violation: bool = False  # was it violated
    energy_before: float = 0.5  # 0-1
    energy_after: float = 0.5  # 0-1
    relationship_impact: float = 0.0  # -1 to 1
    outcome: str = ""  # protected, tested, violated, reinforced
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BoundaryArchitect:
    """
    Intelligent boundary architect with erosion detection and protection optimization.
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
            "avg_enforcement": 0.0,
            "violation_rate": 0.0,
            "erosion_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_boundary(self, domain: str = "", boundary: str = "", enforcement: float = 0.5, violation: bool = False, energy_before: float = 0.5, energy_after: float = 0.5, relationship_impact: float = 0.0, outcome: str = "", notes: str = "") -> BoundaryEntry:
        """Record a boundary entry."""
        entry_id = f"bound_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BoundaryEntry(
            entry_id=entry_id,
            domain=domain or "time",
            boundary=boundary or "unspecified",
            enforcement=enforcement,
            violation=violation,
            energy_before=energy_before,
            energy_after=energy_after,
            relationship_impact=relationship_impact,
            outcome=outcome or "tested",
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

    def get_boundary_stats(self) -> Dict[str, Any]:
        """Get boundary pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "enf_sum": 0.0, "energy_sum": 0.0, "rel_sum": 0.0, "violation_count": 0, "protected_count": 0})
        for e in self._entries:
            by_domain[e.domain]["count"] += 1
            by_domain[e.domain]["enf_sum"] += e.enforcement
            by_domain[e.domain]["energy_sum"] += e.energy_after - e.energy_before
            by_domain[e.domain]["rel_sum"] += e.relationship_impact
            if e.violation:
                by_domain[e.domain]["violation_count"] += 1
            if e.outcome == "protected":
                by_domain[e.domain]["protected_count"] += 1

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "avg_enforcement": round(data["enf_sum"] / count, 2),
                "avg_energy_change": round(data["energy_sum"] / count, 2),
                "avg_relationship_impact": round(data["rel_sum"] / count, 2),
                "violation_rate": round(data["violation_count"] / count, 2),
                "protection_rate": round(data["protected_count"] / count, 2),
            }

        weakest_domain = min(domain_stats.items(), key=lambda x: x[1]["avg_enforcement"]) if domain_stats else ("", {})

        # Outcome analysis
        by_outcome = defaultdict(lambda: {"count": 0, "energy_sum": 0.0, "rel_sum": 0.0})
        for e in self._entries:
            by_outcome[e.outcome]["count"] += 1
            by_outcome[e.outcome]["energy_sum"] += e.energy_after - e.energy_before
            by_outcome[e.outcome]["rel_sum"] += e.relationship_impact

        outcome_stats = {}
        for o, data in by_outcome.items():
            count = data["count"]
            outcome_stats[o] = {
                "count": count,
                "avg_energy_change": round(data["energy_sum"] / count, 2),
                "avg_relationship_impact": round(data["rel_sum"] / count, 2),
            }

        # Enforcement analysis
        high_enf = [e for e in self._entries if e.enforcement > 0.7]
        low_enf = [e for e in self._entries if e.enforcement < 0.4]
        if high_enf and low_enf:
            high_enf_energy = sum(e.energy_after - e.energy_before for e in high_enf) / len(high_enf)
            low_enf_energy = sum(e.energy_after - e.energy_before for e in low_enf) / len(low_enf)
            high_enf_rel = sum(e.relationship_impact for e in high_enf) / len(high_enf)
            low_enf_rel = sum(e.relationship_impact for e in low_enf) / len(low_enf)
        else:
            high_enf_energy = 0
            low_enf_energy = 0
            high_enf_rel = 0
            low_enf_rel = 0

        # Erosion detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_violations = sum(1 for e in recent if e.violation) / len(recent)
            recent_enf = sum(e.enforcement for e in recent) / len(recent)
            erosion_risk = recent_violations > 0.3 or recent_enf < 0.5
        else:
            erosion_risk = False

        # Recent trend
        if recent:
            recent_energy = sum(e.energy_after - e.energy_before for e in recent) / len(recent)
            recent_rel = sum(e.relationship_impact for e in recent) / len(recent)
        else:
            recent_energy = 0
            recent_rel = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_enf = sum(e.enforcement for e in older) / len(older)
            older_energy = sum(e.energy_after - e.energy_before for e in older) / len(older)
            enf_trend = recent_enf - older_enf if recent else 0
            energy_trend = recent_energy - older_energy
        else:
            enf_trend = 0
            energy_trend = 0

        return {
            "total_entries": len(self._entries),
            "domain_stats": domain_stats,
            "weakest_domain": weakest_domain[0],
            "outcome_stats": outcome_stats,
            "enforcement_impact": {
                "high_enforcement_energy": round(high_enf_energy, 2),
                "low_enforcement_energy": round(low_enf_energy, 2),
                "high_enforcement_relationship": round(high_enf_rel, 2),
                "low_enforcement_relationship": round(low_enf_rel, 2),
            },
            "erosion_risk": erosion_risk,
            "avg_enforcement": round(sum(e.enforcement for e in self._entries) / len(self._entries), 2),
            "violation_rate": round(sum(1 for e in self._entries if e.violation) / len(self._entries), 2),
            "avg_energy_change": round(sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries), 2),
            "enforcement_trend": round(enf_trend, 2),
            "energy_trend": round(energy_trend, 2),
            "recent_enforcement": round(sum(e.enforcement for e in recent) / len(recent), 2) if recent else 0,
        }

    def get_boundary_script(self, domain: str = "", situation: str = "") -> Dict[str, Any]:
        """Get script."""
        scripts = {
            "time": [
                "I'm not available after 7pm. That's my recovery time. I can help you tomorrow.",
                "I need 48 hours notice for meetings. Last-minute requests don't work for my schedule.",
                "I have 30 minutes for this. At 3:30, I need to leave. Let's make it count.",
            ],
            "energy": [
                "I don't have the energy for this right now. It's not about you. It's about my capacity.",
                "I can listen for 10 minutes. After that, I need to recharge. Can we set a timer?",
                "This drains me. I care about you, but I can't be the person for this. Let's find someone who can.",
            ],
            "emotional": [
                "I can't absorb your anger right now. I need you to calm down before we talk.",
                "I'm not responsible for your emotions. I can support you, but I can't fix them.",
                "That comment hurt me. I need an apology before we continue this conversation.",
            ],
            "physical": [
                "I need my space. Please don't touch me without asking.",
                "My home is my sanctuary. I'm not having guests this week.",
                "I need to leave now. I've reached my limit for social interaction.",
            ],
            "digital": [
                "I don't check messages after 9pm. If it's urgent, call. Otherwise, I'll see it tomorrow.",
                "I need you to stop sending me work messages on weekends. That's non-negotiable.",
                "I'm muting this group for 24 hours. I'll catch up when I'm ready.",
            ],
            "general": [
                "Boundaries are not rejection. They're protection. Anyone who respects you will respect them.",
                "You don't need to explain. 'No' or 'I can't' is enough. Over-explaining invites negotiation.",
                "The people who get angry at your boundaries are the ones who benefited from you not having them.",
            ],
        }

        selected = scripts.get(domain, scripts["general"])

        if domain == "time":
            domain_note = "Time boundaries protect your most finite resource. Guard them fiercely."
        elif domain == "energy":
            domain_note = "Energy boundaries are invisible but critical. You can't pour from an empty cup."
        elif domain == "emotional":
            domain_note = "Emotional boundaries prevent you from carrying what isn't yours."
        elif domain == "physical":
            domain_note = "Physical boundaries are fundamental. Your body, your space, your rules."
        elif domain == "digital":
            domain_note = "Digital boundaries prevent 24/7 availability. You are not an on-call service."
        else:
            domain_note = "Every boundary you set is a vote for the life you want to live."

        return {
            "domain": domain or "general",
            "situation": situation or "general",
            "script": random.choice(selected),
            "domain_note": domain_note,
            "principle": "Most people struggle with boundaries because they confuse them with walls. Boundaries are not about keeping people out. They're about keeping yourself in. They're the container that holds your energy, your time, your emotions. Without them, you leak. With them, you thrive. The people who matter will respect them. The people who don't, don't matter.",
        }

    def get_boundary_score(self) -> int:
        """Calculate overall boundary health (0-100)."""
        if not self._entries:
            return 35

        # Enforcement and energy protection
        avg_enf = sum(e.enforcement for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries)

        # Low violation rate
        violation_rate = sum(1 for e in self._entries if e.violation) / len(self._entries)

        # Protection rate
        protected = sum(1 for e in self._entries if e.outcome == "protected")
        protection_rate = protected / len(self._entries)

        # Relationship maintenance (boundaries shouldn't destroy relationships)
        avg_rel = sum(e.relationship_impact for e in self._entries) / len(self._entries)

        # Domain variety
        unique_domains = len(set(e.domain for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_enf = sum(e.enforcement for e in recent) / len(recent)
            recent_energy = sum(e.energy_after - e.energy_before for e in recent) / len(recent)
            recent_violations = sum(1 for e in recent if e.violation) / len(recent)
        else:
            recent_enf = 0
            recent_energy = 0
            recent_violations = 0

        # Erosion penalty
        erosion_penalty = 0
        if recent:
            if recent_violations > 0.3 or recent_enf < 0.5:
                erosion_penalty = 10

        score = (avg_enf * 25) + (avg_energy * 15) + ((1 - violation_rate) * 15) + (protection_rate * 15) + (avg_rel * 10) + (unique_domains * 2) + (recent_enf * 10) + (recent_energy * 10) - erosion_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_enforcement"] = round(sum(e.enforcement for e in self._entries) / len(self._entries), 2)
            self._stats["violation_rate"] = round(sum(1 for e in self._entries if e.violation) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_violations = sum(1 for e in recent if e.violation) / len(recent)
                recent_enf = sum(e.enforcement for e in recent) / len(recent)
                self._stats["erosion_risk"] = recent_violations > 0.3 or recent_enf < 0.5

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.boundary_architect")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.boundary_architect")

    def _log_entry(self, entry: BoundaryEntry):
        try:
            with open(BOUNDARY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "domain": entry.domain,
                    "boundary": entry.boundary,
                    "enforcement": entry.enforcement,
                    "violation": entry.violation,
                    "energy_before": entry.energy_before,
                    "energy_after": entry.energy_after,
                    "relationship_impact": entry.relationship_impact,
                    "outcome": entry.outcome,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.boundary_architect")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ba_instance: Optional[BoundaryArchitect] = None
_ba_lock = threading.Lock()


def get_boundary_architect() -> BoundaryArchitect:
    global _ba_instance
    with _ba_lock:
        if _ba_instance is None:
            _ba_instance = BoundaryArchitect()
        return _ba_instance
