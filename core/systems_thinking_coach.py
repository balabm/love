"""
LOVE Systems Thinking Coach — Interconnection Intelligence (Modern AI Pattern)

Most people see parts. This coach sees wholes.

1. SYSTEMS TRACKING
   - Record systems thinking moments and their characteristics
   - Track systems types (feedback_loops, leverage_points, emergent_properties, stock_and_flow, delays)
   - Log interconnection, perspective, and intervention quality

2. PATTERN ANALYSIS
   - Identify the user's systems profile (linear, component, relational, holistic)
   - Find systems patterns that create understanding vs confusion
   - Detect chronic linear thinking and its costs

3. SYSTEMS BUILDING
   - Suggest practices for seeing interconnections and feedback loops
   - Provide frameworks for mapping systems and finding leverage points
   - Recommend practices for understanding emergent properties

4. HOLISTIC UNDERSTANDING CULTIVATION
   - Track the correlation between systems thinking and effective intervention
   - Alert when thinking is becoming overly reductionist
   - Celebrate moments of genuine systems insight

Architecture:
- record_systems(situation, type, interconnection, perspective, intervention): Log systems
- get_systems_stats(): Get systems pattern analysis
- get_systems_suggestion(capacity, context): Get suggestion
- get_systems_score(): Calculate overall systems health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "systems_thinking_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SYSTEMS_LOG = DATA_DIR / "systems.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SystemsEntry:
    """A tracked systems thinking moment."""
    entry_id: str = ""
    situation: str = ""  # what was analyzed
    systems_type: str = ""  # feedback_loops, leverage_points, emergent_properties, stock_and_flow, delays
    interconnection: float = 0.0  # 0-1 did you see connections?
    perspective: float = 0.0  # 0-1 holistic vs reductionist
    intervention: float = 0.0  # 0-1 quality of intervention
    feedback_seen: float = 0.0  # 0-1
    leverage_found: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SystemsThinkingCoach:
    """
    Intelligent systems thinking coach with linear thinking detection and holistic understanding cultivation.
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
            "avg_interconnection": 0.0,
            "avg_intervention": 0.0,
            "linear_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_systems(self, situation: str = "", systems_type: str = "", interconnection: float = 0.0, perspective: float = 0.0, intervention: float = 0.0, feedback_seen: float = 0.0, leverage_found: float = 0.0, notes: str = "") -> SystemsEntry:
        """Record a systems thinking moment."""
        entry_id = f"sys_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SystemsEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            systems_type=systems_type or "feedback_loops",
            interconnection=interconnection,
            perspective=perspective,
            intervention=intervention,
            feedback_seen=feedback_seen,
            leverage_found=leverage_found,
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

    def get_systems_stats(self) -> Dict[str, Any]:
        """Get systems pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "interconnection_sum": 0.0, "perspective_sum": 0.0, "intervention_sum": 0.0})
        for e in self._entries:
            by_type[e.systems_type]["count"] += 1
            by_type[e.systems_type]["interconnection_sum"] += e.interconnection
            by_type[e.systems_type]["perspective_sum"] += e.perspective
            by_type[e.systems_type]["intervention_sum"] += e.intervention

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_interconnection": round(data["interconnection_sum"] / count, 2),
                "avg_perspective": round(data["perspective_sum"] / count, 2),
                "avg_intervention": round(data["intervention_sum"] / count, 2),
            }

        # Interconnection analysis
        high_int = [e for e in self._entries if e.interconnection > 0.7]
        low_int = [e for e in self._entries if e.interconnection < 0.4]
        if high_int and low_int:
            high_int_intv = sum(e.intervention for e in high_int) / len(high_int)
            low_int_intv = sum(e.intervention for e in low_int) / len(low_int)
            high_int_lev = sum(e.leverage_found for e in high_int) / len(high_int)
            low_int_lev = sum(e.leverage_found for e in low_int) / len(low_int)
        else:
            high_int_intv = 0
            low_int_intv = 0
            high_int_lev = 0
            low_int_lev = 0

        # Feedback analysis
        high_fb = [e for e in self._entries if e.feedback_seen > 0.7]
        low_fb = [e for e in self._entries if e.feedback_seen < 0.4]
        if high_fb and low_fb:
            high_fb_intv = sum(e.intervention for e in high_fb) / len(high_fb)
            low_fb_intv = sum(e.intervention for e in low_fb) / len(low_fb)
        else:
            high_fb_intv = 0
            low_fb_intv = 0

        # Linear risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_int = sum(e.interconnection for e in recent) / len(recent)
            recent_pers = sum(e.perspective for e in recent) / len(recent)
            linear_risk = recent_int < 0.3 and recent_pers < 0.3
        else:
            linear_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "interconnection_impact": {
                "high_interconnection_intervention": round(high_int_intv, 2),
                "low_interconnection_intervention": round(low_int_intv, 2),
                "high_interconnection_leverage": round(high_int_lev, 2),
                "low_interconnection_leverage": round(low_int_lev, 2),
            },
            "feedback_effect": {
                "high_feedback_intervention": round(high_fb_intv, 2),
                "low_feedback_intervention": round(low_fb_intv, 2),
            },
            "linear_risk": linear_risk,
            "avg_interconnection": round(sum(e.interconnection for e in self._entries) / len(self._entries), 2),
            "avg_intervention": round(sum(e.intervention for e in self._entries) / len(self._entries), 2),
        }

    def get_systems_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get systems suggestion."""
        suggestions = [
            "Every system is perfectly designed to get the results it gets. If you don't like the results, change the system. Not the people. Not the effort. The system. The structure. The incentives. The feedback loops.",
            "Feedback loops are invisible architects of behavior. They create virtuous cycles and vicious cycles. The person who exercises feels good, so they exercise more. The person who isolates feels bad, so they isolate more. Find the loops. Shape them.",
            "Small interventions at leverage points create large changes. But most people push where it's hard. They work harder. They try more. Instead, find where a small push creates a big effect. That's leverage.",
            "Emergent properties cannot be predicted from the parts. Water is wet. But hydrogen and oxygen are not. Trust is emergent. Culture is emergent. You can't build them directly. You create the conditions. Then they emerge.",
            "Stocks and flows: understand what accumulates and what flows. Money is a stock. Income is a flow. Knowledge is a stock. Learning is a flow. Health is a stock. Exercise is a flow. Manage both. Don't just focus on flows.",
            "Delays are dangerous. The effect of your action today may not show up for months. The diet you start today shows results in weeks. The relationship you neglect today breaks in years. Account for delays. Don't expect immediate feedback.",
            "The system fights back. When you push on a system, it pushes back. Lower prices, demand rises. Fire the bad employees, morale drops. Intervene with the system's response in mind. Or you'll be surprised.",
            "Boundaries are arbitrary. Where does your body end? At your skin? Or at the air you breathe? Where does your company end? At the building? Or at the customers it serves? The boundaries you draw create the problems you see.",
            "Cause and effect are not close in time and space. The flu outbreak in January was caused by holiday travel in December. The bankruptcy in 2025 was caused by decisions in 2022. Look upstream. Look far. Look wide.",
            "The person who understands systems doesn't blame individuals. They understand that behavior is shaped by structure. By incentives. By feedback. By culture. Change the structure. The behavior follows."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One feedback loop noticed. One connection seen. One system mapped. One small step into holistic thinking. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A system mapped. A leverage point found. A delay accounted for. Medium coaching."
        else:
            capacity_note = "Good capacity. Deep systems work. A systematic practice of seeing interconnections, feedback loops, and emergent properties. You have the strength to think in wholes."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Systems thinking is the antidote to the reductionist thinking that dominates modern life. Most people see parts. They see the employee who is underperforming. They see the student who is failing. They see the market that is crashing. And they think: fix the part. Fire the employee. Punish the student. Regulate the market. But systems thinking sees wholes. It sees that the underperforming employee is in a system with bad incentives. That the failing student is in a system with inadequate support. That the crashing market is in a system with misaligned incentives. And it understands that fixing the part without fixing the system is temporary at best. The work of systems thinking is about seeing interconnections. About understanding feedback loops. About recognizing that cause and effect are often separated by time and space. About understanding that the whole is greater than the sum of its parts. And about intervening at leverage points where small changes create large effects. That's the work of wisdom. And it's available to anyone who stops looking at parts and starts looking at wholes."
        }

    def get_systems_score(self) -> int:
        """Calculate overall systems health (0-100)."""
        if not self._entries:
            return 25

        avg_int = sum(e.interconnection for e in self._entries) / len(self._entries)
        avg_pers = sum(e.perspective for e in self._entries) / len(self._entries)
        avg_intv = sum(e.intervention for e in self._entries) / len(self._entries)
        avg_fb = sum(e.feedback_seen for e in self._entries) / len(self._entries)
        avg_lev = sum(e.leverage_found for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_int = sum(e.interconnection for e in recent) / len(recent)
            recent_pers = sum(e.perspective for e in recent) / len(recent)
        else:
            recent_int = 0
            recent_pers = 0

        # Linear penalty
        linear_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_int_30 = sum(e.interconnection for e in last_30) / len(last_30)
            recent_pers_30 = sum(e.perspective for e in last_30) / len(last_30)
            if recent_int_30 < 0.3 and recent_pers_30 < 0.3:
                linear_penalty = 15

        # Type variety
        unique_types = len(set(e.systems_type for e in self._entries))

        score = (avg_int * 25) + (avg_pers * 20) + (avg_intv * 15) + (avg_fb * 15) + (avg_lev * 10) + (recent_int * 5) + (recent_pers * 5) + (unique_types * 2) - linear_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_interconnection"] = round(sum(e.interconnection for e in self._entries) / len(self._entries), 2)
            self._stats["avg_intervention"] = round(sum(e.intervention for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_int = sum(e.interconnection for e in recent) / len(recent)
                recent_pers = sum(e.perspective for e in recent) / len(recent)
                self._stats["linear_risk"] = recent_int < 0.3 and recent_pers < 0.3
            else:
                self._stats["linear_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.systems_thinking_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.systems_thinking_coach")

    def _log_entry(self, entry: SystemsEntry):
        try:
            with open(SYSTEMS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "systems_type": entry.systems_type,
                    "interconnection": entry.interconnection,
                    "intervention": entry.intervention,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.systems_thinking_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_stc_instance: Optional[SystemsThinkingCoach] = None
_stc_lock = threading.Lock()


def get_systems_thinking_coach() -> SystemsThinkingCoach:
    global _stc_instance
    with _stc_lock:
        if _stc_instance is None:
            _stc_instance = SystemsThinkingCoach()
        return _stc_instance
