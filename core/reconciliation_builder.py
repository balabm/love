"""
LOVE Reconciliation Builder — Repair Intelligence (Modern AI Pattern)

Most relationships end because repair was never attempted. This builder:

1. RECONCILIATION TRACKING
   - Record repair attempts and their characteristics
   - Track reconciliation types (apology, amends, dialogue, space, reset)
   - Log repair outcomes and their effects on relationship quality

2. PATTERN ANALYSIS
   - Identify the user's repair style (avoidant, eager, strategic, genuine)
   - Find repair approaches that restore connection
   - Detect repair avoidance and its consequences

3. RECONCILIATION BUILDING
   - Suggest repair strategies matched to relationship damage
   - Provide apology and amends frameworks
   - Recommendation repair timing and context

4. CONNECTION RESTORATION
   - Track the correlation between repair and trust
   - Alert when repair is being delayed past optimal window
   - Celebrate successful reconciliation

Architecture:
- record_repair(relationship, damage, repair, outcome): Log repair
- get_reconciliation_stats(): Get reconciliation pattern analysis
- get_repair_strategy(damage, relationship_type): Get strategy
- get_reconciliation_score(): Calculate overall reconciliation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "reconciliation_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REPAIR_LOG = DATA_DIR / "repairs.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RepairEntry:
    """A tracked repair entry."""
    entry_id: str = ""
    relationship: str = ""  # who
    damage_type: str = ""  # betrayal, neglect, misunderstanding, conflict, distance
    severity: float = 0.5  # 0-1
    repair_type: str = ""  # apology, amends, dialogue, space, reset
    repair_quality: float = 0.5  # 0-1
    timing: float = 0.5  # 0-1, how quickly after damage
    outcome: str = ""  # restored, improved, unchanged, worsened
    relationship_quality_after: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ReconciliationBuilder:
    """
    Intelligent reconciliation builder with repair timing optimization and strategy matching.
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
            "avg_repair_quality": 0.0,
            "avg_relationship_after": 0.0,
            "repair_avoidance": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_repair(self, relationship: str = "", damage_type: str = "", severity: float = 0.5, repair_type: str = "", repair_quality: float = 0.5, timing: float = 0.5, outcome: str = "", relationship_quality_after: float = 0.5, notes: str = "") -> RepairEntry:
        """Record a repair entry."""
        entry_id = f"rep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RepairEntry(
            entry_id=entry_id,
            relationship=relationship or "unspecified",
            damage_type=damage_type or "misunderstanding",
            severity=severity,
            repair_type=repair_type or "dialogue",
            repair_quality=repair_quality,
            timing=timing,
            outcome=outcome or "unchanged",
            relationship_quality_after=relationship_quality_after,
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

    def get_reconciliation_stats(self) -> Dict[str, Any]:
        """Get reconciliation pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Damage type analysis
        by_damage = defaultdict(lambda: {"count": 0, "severity_sum": 0.0, "repair_sum": 0.0, "after_sum": 0.0})
        for e in self._entries:
            by_damage[e.damage_type]["count"] += 1
            by_damage[e.damage_type]["severity_sum"] += e.severity
            by_damage[e.damage_type]["repair_sum"] += e.repair_quality
            by_damage[e.damage_type]["after_sum"] += e.relationship_quality_after

        damage_stats = {}
        for d, data in by_damage.items():
            count = data["count"]
            damage_stats[d] = {
                "count": count,
                "avg_severity": round(data["severity_sum"] / count, 2),
                "avg_repair": round(data["repair_sum"] / count, 2),
                "avg_after": round(data["after_sum"] / count, 2),
            }

        # Repair type analysis
        by_repair = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "after_sum": 0.0, "timing_sum": 0.0})
        for e in self._entries:
            by_repair[e.repair_type]["count"] += 1
            by_repair[e.repair_type]["quality_sum"] += e.repair_quality
            by_repair[e.repair_type]["after_sum"] += e.relationship_quality_after
            by_repair[e.repair_type]["timing_sum"] += e.timing

        repair_stats = {}
        for r, data in by_repair.items():
            count = data["count"]
            repair_stats[r] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_after": round(data["after_sum"] / count, 2),
                "avg_timing": round(data["timing_sum"] / count, 2),
            }

        best_repair = max(repair_stats.items(), key=lambda x: x[1]["avg_after"]) if repair_stats else ("", {})

        # Timing analysis
        fast = [e for e in self._entries if e.timing > 0.7]
        slow = [e for e in self._entries if e.timing <= 0.4]
        if fast and slow:
            fast_after = sum(e.relationship_quality_after for e in fast) / len(fast)
            slow_after = sum(e.relationship_quality_after for e in slow) / len(slow)
            fast_quality = sum(e.repair_quality for e in fast) / len(fast)
            slow_quality = sum(e.repair_quality for e in slow) / len(slow)
        else:
            fast_after = 0
            slow_after = 0
            fast_quality = 0
            slow_quality = 0

        # Outcome analysis
        by_outcome = defaultdict(lambda: {"count": 0, "severity_sum": 0.0})
        for e in self._entries:
            by_outcome[e.outcome]["count"] += 1
            by_outcome[e.outcome]["severity_sum"] += e.severity

        outcome_stats = {}
        for o, data in by_outcome.items():
            count = data["count"]
            outcome_stats[o] = {
                "count": count,
                "avg_severity": round(data["severity_sum"] / count, 2),
            }

        # Repair avoidance detection
        high_severity = [e for e in self._entries if e.severity > 0.7]
        if high_severity:
            high_severity_repair = sum(e.repair_quality for e in high_severity) / len(high_severity)
            repair_avoidance = high_severity_repair < 0.4
        else:
            repair_avoidance = False

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_repair = sum(e.repair_quality for e in recent) / len(recent)
            recent_after = sum(e.relationship_quality_after for e in recent) / len(recent)
            recent_timing = sum(e.timing for e in recent) / len(recent)
        else:
            recent_repair = 0
            recent_after = 0
            recent_timing = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_repair = sum(e.repair_quality for e in older) / len(older)
            older_after = sum(e.relationship_quality_after for e in older) / len(older)
            repair_trend = recent_repair - older_repair
            after_trend = recent_after - older_after
        else:
            repair_trend = 0
            after_trend = 0

        return {
            "total_entries": len(self._entries),
            "damage_stats": damage_stats,
            "repair_stats": repair_stats,
            "best_repair_type": best_repair[0],
            "timing_analysis": {
                "fast_repair_after": round(fast_after, 2),
                "slow_repair_after": round(slow_after, 2),
                "fast_repair_quality": round(fast_quality, 2),
                "slow_repair_quality": round(slow_quality, 2),
            },
            "outcome_stats": outcome_stats,
            "repair_avoidance": repair_avoidance,
            "avg_repair_quality": round(sum(e.repair_quality for e in self._entries) / len(self._entries), 2),
            "avg_relationship_after": round(sum(e.relationship_quality_after for e in self._entries) / len(self._entries), 2),
            "avg_timing": round(sum(e.timing for e in self._entries) / len(self._entries), 2),
            "repair_trend": round(repair_trend, 2),
            "after_trend": round(after_trend, 2),
            "recent_timing": round(recent_timing, 2),
        }

    def get_repair_strategy(self, damage: str = "", relationship_type: str = "") -> Dict[str, Any]:
        """Get strategy."""
        strategies = {
            "betrayal": [
                "Betrayal requires transparency. Full disclosure. No secrets. Then patience. They decide the timeline.",
                "Make amends through actions, not words. Consistent behavior over time. Words are cheap.",
                "Accept that trust may never fully return. That's their right. Your job is to be trustworthy anyway.",
            ],
            "neglect": [
                "Acknowledge the neglect specifically. 'I wasn't there when...' Name it.",
                "Ask what they need. Then provide it. Consistently. Not just once.",
                "Schedule regular connection. Neglect is often forgetfulness, not malice. Systematize care.",
            ],
            "misunderstanding": [
                "Clarify your intention. Then ask for theirs. Misunderstanding lives in the gap between intent and impact.",
                "Paraphrase their perspective until they say 'Yes, that's what I meant.' Only then respond.",
                "Apologize for the impact, not the intent. 'I'm sorry that landed that way.'",
            ],
            "conflict": [
                "Cool down first. 24 hours minimum. Conflict + heat = explosion.",
                "Find the shared goal beneath the disagreement. What do you both want?",
                "Use 'I' statements. 'I felt...' not 'You made me...' Ownership diffuses defensiveness.",
            ],
            "distance": [
                "Reach out with no agenda. 'Thinking of you.' Not 'We need to talk.'",
                "Share something personal. Distance grows in silence. Intimacy grows in disclosure.",
                "Propose a specific activity. Vague invitations get vague responses.",
            ],
            "general": [
                "Repair is not weakness. It's the highest form of strength. It requires humility, courage, and love.",
                "The sooner, the better. But late repair is better than none. Never too late if both are willing.",
                "Listen more than you speak. Repair is about their experience, not your explanation.",
            ],
        }

        selected = strategies.get(damage, strategies["general"])

        if relationship_type == "intimate":
            rel_note = "Intimate relationships require the deepest repair. Surface fixes don't work here. Go deep."
        elif relationship_type == "family":
            rel_note = "Family repair is complicated by history. Be patient. Be consistent. Time matters."
        elif relationship_type == "work":
            rel_note = "Work relationships need professionalism in repair. Clear boundaries. Specific actions."
        elif relationship_type == "friend":
            rel_note = "Friendship repair is about showing up. Presence is the best apology."
        else:
            rel_note = "Every relationship is worth repair if the other person is willing. Assess willingness first."

        return {
            "damage": damage or "general",
            "relationship_type": relationship_type or "general",
            "strategy": random.choice(selected),
            "relationship_note": rel_note,
            "principle": "Most relationships don't end because of the damage. They end because repair was never attempted. Or attempted poorly. Repair is a skill. Like any skill, it improves with practice. The first repair is the hardest. Each one gets easier.",
        }

    def get_reconciliation_score(self) -> int:
        """Calculate overall reconciliation health (0-100)."""
        if not self._entries:
            return 35

        # Repair quality and relationship improvement
        avg_repair = sum(e.repair_quality for e in self._entries) / len(self._entries)
        avg_after = sum(e.relationship_quality_after for e in self._entries) / len(self._entries)

        # Timing (faster is generally better)
        avg_timing = sum(e.timing for e in self._entries) / len(self._entries)

        # Low severity or well-repaired severity
        avg_severity = sum(e.severity for e in self._entries) / len(self._entries)
        severity_repair_ratio = avg_repair / max(0.1, avg_severity)

        # Outcome quality
        restored = sum(1 for e in self._entries if e.outcome == "restored")
        improved = sum(1 for e in self._entries if e.outcome == "improved")
        positive_outcome = (restored + improved) / len(self._entries)

        # Type variety
        unique_types = len(set(e.repair_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_repair = sum(e.repair_quality for e in recent) / len(recent)
            recent_after = sum(e.relationship_quality_after for e in recent) / len(recent)
            recent_timing = sum(e.timing for e in recent) / len(recent)
        else:
            recent_repair = 0
            recent_after = 0
            recent_timing = 0

        # Avoidance penalty
        high_severity = [e for e in self._entries if e.severity > 0.7]
        if high_severity:
            high_severity_repair = sum(e.repair_quality for e in high_severity) / len(high_severity)
            avoidance_penalty = 10 if high_severity_repair < 0.4 else 0
        else:
            avoidance_penalty = 0

        score = (avg_repair * 20) + (avg_after * 25) + (avg_timing * 10) + (severity_repair_ratio * 10) + (positive_outcome * 15) + (unique_types * 2) + (recent_repair * 10) + (recent_after * 10) + (recent_timing * 5) - avoidance_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_repair_quality"] = round(sum(e.repair_quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_relationship_after"] = round(sum(e.relationship_quality_after for e in self._entries) / len(self._entries), 2)

            high_severity = [e for e in self._entries if e.severity > 0.7]
            if high_severity:
                high_severity_repair = sum(e.repair_quality for e in high_severity) / len(high_severity)
                self._stats["repair_avoidance"] = high_severity_repair < 0.4

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

    def _log_entry(self, entry: RepairEntry):
        try:
            with open(REPAIR_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "relationship": entry.relationship,
                    "damage_type": entry.damage_type,
                    "severity": entry.severity,
                    "repair_type": entry.repair_type,
                    "repair_quality": entry.repair_quality,
                    "timing": entry.timing,
                    "outcome": entry.outcome,
                    "relationship_quality_after": entry.relationship_quality_after,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rb_instance: Optional[ReconciliationBuilder] = None
_rb_lock = threading.Lock()


def get_reconciliation_builder() -> ReconciliationBuilder:
    global _rb_instance
    with _rb_lock:
        if _rb_instance is None:
            _rb_instance = ReconciliationBuilder()
        return _rb_instance
