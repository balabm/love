"""
LOVE Values Navigator — Principles Intelligence (Modern AI Pattern)

Most people violate their values without realizing it. This navigator:

1. VALUES TRACKING
   - Record values-based decisions and their characteristics
   - Track value types (integrity, compassion, courage, justice, growth, love)
   - Log alignment, cost, and satisfaction from value-based choices

2. PATTERN ANALYSIS
   - Identify the user's values profile (aligned, compromised, unclear, aspirational)
   - Find values patterns that create integrity vs regret
   - Detect values drift and its causes

3. VALUES OPTIMIZATION
   - Suggest practices for values clarification and alignment
   - Provide frameworks for difficult values conflicts
   - Recommend values-based decision making

4. INTEGRITY CULTIVATION
   - Track the correlation between values alignment and self-respect
   - Alert when compromises are becoming habitual
   - Celebrate moments of genuine values-based action

Architecture:
- record_decision(decision, value, alignment, cost, satisfaction): Log decision
- get_values_stats(): Get values pattern analysis
- get_values_suggestion(capacity, context): Get suggestion
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

DATA_DIR = Path(__file__).parent.parent / "data" / "values_navigator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VALUES_LOG = DATA_DIR / "decisions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ValuesEntry:
    """A tracked values-based decision."""
    entry_id: str = ""
    decision: str = ""  # what was decided
    value: str = ""  # which value
    alignment: float = 0.0  # 0-1
    cost: float = 0.0  # 0-1 cost of alignment
    satisfaction: float = 0.0  # 0-1
    integrity: float = 0.0  # 0-1
    pride: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ValuesNavigator:
    """
    Intelligent values navigator with alignment detection and integrity cultivation.
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
            "avg_alignment": 0.0,
            "avg_integrity": 0.0,
            "compromise_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_decision(self, decision: str = "", value: str = "", alignment: float = 0.0, cost: float = 0.0, satisfaction: float = 0.0, integrity: float = 0.0, pride: float = 0.0, notes: str = "") -> ValuesEntry:
        """Record a values-based decision."""
        entry_id = f"val_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ValuesEntry(
            entry_id=entry_id,
            decision=decision or "unspecified",
            value=value or "general",
            alignment=alignment,
            cost=cost,
            satisfaction=satisfaction,
            integrity=integrity,
            pride=pride,
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
        by_value = defaultdict(lambda: {"count": 0, "alignment_sum": 0.0, "satisfaction_sum": 0.0, "integrity_sum": 0.0})
        for e in self._entries:
            by_value[e.value]["count"] += 1
            by_value[e.value]["alignment_sum"] += e.alignment
            by_value[e.value]["satisfaction_sum"] += e.satisfaction
            by_value[e.value]["integrity_sum"] += e.integrity

        value_stats = {}
        for v, data in by_value.items():
            count = data["count"]
            value_stats[v] = {
                "count": count,
                "avg_alignment": round(data["alignment_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                "avg_integrity": round(data["integrity_sum"] / count, 2),
            }

        # Alignment analysis
        high_align = [e for e in self._entries if e.alignment > 0.7]
        low_align = [e for e in self._entries if e.alignment < 0.4]
        if high_align and low_align:
            high_align_sat = sum(e.satisfaction for e in high_align) / len(high_align)
            low_align_sat = sum(e.satisfaction for e in low_align) / len(low_align)
            high_align_pride = sum(e.pride for e in high_align) / len(high_align)
            low_align_pride = sum(e.pride for e in low_align) / len(low_align)
        else:
            high_align_sat = 0
            low_align_sat = 0
            high_align_pride = 0
            low_align_pride = 0

        # Cost analysis
        high_cost = [e for e in self._entries if e.cost > 0.7]
        low_cost = [e for e in self._entries if e.cost < 0.4]
        if high_cost and low_cost:
            high_cost_int = sum(e.integrity for e in high_cost) / len(high_cost)
            low_cost_int = sum(e.integrity for e in low_cost) / len(low_cost)
        else:
            high_cost_int = 0
            low_cost_int = 0

        # Compromise risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_align = sum(e.alignment for e in recent) / len(recent)
            recent_integrity = sum(e.integrity for e in recent) / len(recent)
            compromise_risk = recent_align < 0.4 and recent_integrity < 0.4
        else:
            compromise_risk = False

        return {
            "total_entries": len(self._entries),
            "value_stats": value_stats,
            "alignment_impact": {
                "high_alignment_satisfaction": round(high_align_sat, 2),
                "low_alignment_satisfaction": round(low_align_sat, 2),
                "high_alignment_pride": round(high_align_pride, 2),
                "low_alignment_pride": round(low_align_pride, 2),
            },
            "cost_effect": {
                "high_cost_integrity": round(high_cost_int, 2),
                "low_cost_integrity": round(low_cost_int, 2),
            },
            "compromise_risk": compromise_risk,
            "avg_alignment": round(sum(e.alignment for e in self._entries) / len(self._entries), 2),
            "avg_integrity": round(sum(e.integrity for e in self._entries) / len(self._entries), 2),
        }

    def get_values_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get values suggestion."""
        suggestions = [
            "Name your top three values. Not what you think they should be. What they actually are. The ones you live by when no one is watching. Write them down. Look at them daily.",
            "When in doubt, choose the harder right over the easier wrong. The short-term cost of integrity is always less than the long-term cost of compromise.",
            "Your values are not abstract principles. They're decision filters. 'Does this align with what I believe?' Ask this before every significant decision.",
            "Values conflicts are inevitable. Courage vs safety. Honesty vs kindness. Growth vs comfort. The goal is not to eliminate conflict. It's to choose consciously.",
            "Notice when you feel resentment. Resentment is often the signal that a value has been violated. Usually by you. Usually through silence. Usually through compromise.",
            "Integrity is not about being perfect. It's about being whole. When your actions match your values, you feel whole. When they don't, you feel fragmented.",
            "The most expensive thing in the world is a compromised conscience. No amount of success, money, or approval is worth the cost of violating your own values.",
            "Values are like muscles. They strengthen through use. Every values-aligned decision, no matter how small, makes the next one easier.",
            "Ask: will I be proud of this decision in five years? Not tomorrow. Not next week. Five years. The long view reveals what really matters.",
            "You are your values. Not your job. Not your appearance. Not your achievements. Your values are the only thing that will be with you on your deathbed. Live accordingly."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One honest choice. One small alignment. One moment of integrity. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A values clarification. A difficult decision made well. A boundary drawn. Medium integrity work."
        else:
            capacity_note = "Good capacity. A major values realignment. A life audit. A systematic change in how you make decisions. You have the strength for real integrity."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Values are not decorations. They're the operating system of your life. Every decision you make either aligns with your values or violates them. And every violation, no matter how small, creates a tiny fracture in your sense of self. Over time, those fractures add up. The person who lives in constant conflict with their values becomes depressed, anxious, and disconnected. Not because of external circumstances. Because of internal misalignment. The good news is that alignment is always available. In the next conversation. The next decision. The next moment of choice. Choose integrity. Choose wholeness. Choose yourself."
        }

    def get_values_score(self) -> int:
        """Calculate overall values health (0-100)."""
        if not self._entries:
            return 25

        avg_align = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_int = sum(e.integrity for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_pride = sum(e.pride for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_align = sum(e.alignment for e in recent) / len(recent)
            recent_int = sum(e.integrity for e in recent) / len(recent)
        else:
            recent_align = 0
            recent_int = 0

        # Compromise penalty
        comp_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_align_30 = sum(e.alignment for e in last_30) / len(last_30)
            recent_int_30 = sum(e.integrity for e in last_30) / len(last_30)
            if recent_align_30 < 0.4 and recent_int_30 < 0.4:
                comp_penalty = 15

        # Value variety
        unique_values = len(set(e.value for e in self._entries))

        score = (avg_align * 30) + (avg_int * 25) + (avg_sat * 15) + (avg_pride * 15) + (recent_align * 10) + (recent_int * 5) + (unique_values * 2) - comp_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_alignment"] = round(sum(e.alignment for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integrity"] = round(sum(e.integrity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_align = sum(e.alignment for e in recent) / len(recent)
                recent_integrity = sum(e.integrity for e in recent) / len(recent)
                self._stats["compromise_risk"] = recent_align < 0.4 and recent_integrity < 0.4
            else:
                self._stats["compromise_risk"] = False

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

    def _log_entry(self, entry: ValuesEntry):
        try:
            with open(VALUES_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "decision": entry.decision,
                    "value": entry.value,
                    "alignment": entry.alignment,
                    "integrity": entry.integrity,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vn_instance: Optional[ValuesNavigator] = None
_vn_lock = threading.Lock()


def get_values_navigator() -> ValuesNavigator:
    global _vn_instance
    with _vn_lock:
        if _vn_instance is None:
            _vn_instance = ValuesNavigator()
        return _vn_instance
