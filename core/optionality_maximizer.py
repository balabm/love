"""
LOVE Optionality Maximizer — Strategic Intelligence (Modern AI Pattern)

Most people close doors without realizing it. This maximizer:

1. OPTIONALITY TRACKING
   - Record optionality decisions and their characteristics
   - Track optionality types (career, financial, relational, geographic, skill)
   - Log doors opened, doors closed, and flexibility maintained

2. PATTERN ANALYSIS
   - Identify the user's optionality profile (constrained, balanced, flexible, maximized)
   - Find optionality patterns that create freedom vs stagnation
   - Detect chronic door-closing and its costs

3. OPTIONALITY BUILDING
   - Suggest practices for preserving and creating options
   - Provide frameworks for reversible vs irreversible decisions
   - Recommend practices for strategic flexibility

4. STRATEGIC FREEDOM CULTIVATION
   - Track the correlation between optionality and life satisfaction
   - Alert when doors are being closed unnecessarily
   - Celebrate moments of genuine optionality creation

Architecture:
- record_optionality(decision, type, doors_opened, doors_closed, reversibility): Log optionality
- get_optionality_stats(): Get optionality pattern analysis
- get_optionality_suggestion(capacity, context): Get suggestion
- get_optionality_score(): Calculate overall optionality health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "optionality_maximizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OPTIONALITY_LOG = DATA_DIR / "optionalities.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class OptionalityEntry:
    """A tracked optionality decision."""
    entry_id: str = ""
    decision: str = ""  # what was decided
    optionality_type: str = ""  # career, financial, relational, geographic, skill
    doors_opened: float = 0.0  # 0-1
    doors_closed: float = 0.0  # 0-1
    reversibility: float = 0.0  # 0-1
    flexibility: float = 0.0  # 0-1
    strategic_value: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class OptionalityMaximizer:
    """
    Intelligent optionality maximizer with door-closing detection and strategic freedom cultivation.
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
            "avg_doors_opened": 0.0,
            "avg_doors_closed": 0.0,
            "constraint_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_optionality(self, decision: str = "", optionality_type: str = "", doors_opened: float = 0.0, doors_closed: float = 0.0, reversibility: float = 0.0, flexibility: float = 0.0, strategic_value: float = 0.0, notes: str = "") -> OptionalityEntry:
        """Record an optionality decision."""
        entry_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = OptionalityEntry(
            entry_id=entry_id,
            decision=decision or "unspecified",
            optionality_type=optionality_type or "career",
            doors_opened=doors_opened,
            doors_closed=doors_closed,
            reversibility=reversibility,
            flexibility=flexibility,
            strategic_value=strategic_value,
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

    def get_optionality_stats(self) -> Dict[str, Any]:
        """Get optionality pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "opened_sum": 0.0, "closed_sum": 0.0, "flexibility_sum": 0.0})
        for e in self._entries:
            by_type[e.optionality_type]["count"] += 1
            by_type[e.optionality_type]["opened_sum"] += e.doors_opened
            by_type[e.optionality_type]["closed_sum"] += e.doors_closed
            by_type[e.optionality_type]["flexibility_sum"] += e.flexibility

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_doors_opened": round(data["opened_sum"] / count, 2),
                "avg_doors_closed": round(data["closed_sum"] / count, 2),
                "avg_flexibility": round(data["flexibility_sum"] / count, 2),
            }

        # Opened vs closed analysis
        high_open = [e for e in self._entries if e.doors_opened > 0.7]
        high_close = [e for e in self._entries if e.doors_closed > 0.7]
        if high_open and high_close:
            high_open_strat = sum(e.strategic_value for e in high_open) / len(high_open)
            high_close_strat = sum(e.strategic_value for e in high_close) / len(high_close)
            high_open_flex = sum(e.flexibility for e in high_open) / len(high_open)
            high_close_flex = sum(e.flexibility for e in high_close) / len(high_close)
        else:
            high_open_strat = 0
            high_close_strat = 0
            high_open_flex = 0
            high_close_flex = 0

        # Reversibility analysis
        high_rev = [e for e in self._entries if e.reversibility > 0.7]
        low_rev = [e for e in self._entries if e.reversibility < 0.4]
        if high_rev and low_rev:
            high_rev_flex = sum(e.flexibility for e in high_rev) / len(high_rev)
            low_rev_flex = sum(e.flexibility for e in low_rev) / len(low_rev)
        else:
            high_rev_flex = 0
            low_rev_flex = 0

        # Constraint risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_closed = sum(e.doors_closed for e in recent) / len(recent)
            recent_flex = sum(e.flexibility for e in recent) / len(recent)
            constraint_risk = recent_closed > 0.7 and recent_flex < 0.3
        else:
            constraint_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "open_vs_close": {
                "high_opened_strategic_value": round(high_open_strat, 2),
                "high_closed_strategic_value": round(high_close_strat, 2),
                "high_opened_flexibility": round(high_open_flex, 2),
                "high_closed_flexibility": round(high_close_flex, 2),
            },
            "reversibility_effect": {
                "high_reversibility_flexibility": round(high_rev_flex, 2),
                "low_reversibility_flexibility": round(low_rev_flex, 2),
            },
            "constraint_risk": constraint_risk,
            "avg_doors_opened": round(sum(e.doors_opened for e in self._entries) / len(self._entries), 2),
            "avg_doors_closed": round(sum(e.doors_closed for e in self._entries) / len(self._entries), 2),
        }

    def get_optionality_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get optionality suggestion."""
        suggestions = [
            "Before you close a door, ask: can this be reversed? If not, proceed with caution. Irreversible decisions deserve more thought than reversible ones. Don't treat them the same.",
            "Optionality is not about keeping every door open. It's about keeping the right doors open. The ones that matter to you. Close the ones that don't. But know which is which.",
            "Every commitment closes some doors. That's not bad. Commitment is necessary. But commit consciously. Know what you're giving up. And make sure what you're gaining is worth it.",
            "The person with the most options is not the person who never commits. It's the person who commits strategically. Who builds skills that transfer. Who maintains relationships. Who saves money. Who stays healthy. These are the real options.",
            "Don't confuse comfort with optionality. Staying in a job you hate because it's 'safe' is not optionality. It's a cage with soft walls. True optionality is the ability to leave. Even if you choose to stay.",
            "Skills are optionality. The more you can do, the more options you have. Learn widely. Learn deeply. The person who can code, write, speak, and lead has more options than the person who can only code.",
            "Money is optionality. Not because it buys happiness. Because it buys choices. The person with savings can say no to bad opportunities. Can wait for good ones. Can take risks. That's optionality.",
            "Relationships are optionality. The person with a strong network has more options than the person who is brilliant but isolated. Invest in people. Not for what you can get. For what you can give. And what emerges from that.",
            "Geographic flexibility is optionality. The person who can live anywhere has more options than the person tied to one city. This doesn't mean you should move. It means you could if you wanted to.",
            "The best time to create optionality is before you need it. When everything is fine. When you have energy. When you have resources. Because when you need it, you usually don't have the capacity to create it."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One door left open. One skill learned. One connection maintained. One small act of optionality preservation. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. An optionality audit. A skill investment. A financial buffer. A network expansion. Medium maximization."
        else:
            capacity_note = "Good capacity. Deep strategic work. A systematic creation of options across life domains. You have the strength to be truly free."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Optionality is the freedom to choose. And most people give it away without realizing it. They take on debt that constrains them. They commit to relationships that limit them. They build skills that only apply to one industry. They live in places they can't afford to leave. And then they wonder why they feel trapped. The work of optionality maximization is about preserving and creating choices. Not about refusing to choose. But about choosing consciously. About knowing what doors you're closing. About making sure the doors that matter to you stay open. About building the skills, savings, relationships, and health that create genuine freedom. Because optionality is not just a financial concept. It's a life concept. And it's the foundation of a life well-lived."
        }

    def get_optionality_score(self) -> int:
        """Calculate overall optionality health (0-100)."""
        if not self._entries:
            return 25

        avg_open = sum(e.doors_opened for e in self._entries) / len(self._entries)
        avg_close = sum(e.doors_closed for e in self._entries) / len(self._entries)
        avg_rev = sum(e.reversibility for e in self._entries) / len(self._entries)
        avg_flex = sum(e.flexibility for e in self._entries) / len(self._entries)
        avg_strat = sum(e.strategic_value for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_open = sum(e.doors_opened for e in recent) / len(recent)
            recent_flex = sum(e.flexibility for e in recent) / len(recent)
        else:
            recent_open = 0
            recent_flex = 0

        # Constraint penalty
        constr_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_closed_30 = sum(e.doors_closed for e in last_30) / len(last_30)
            recent_flex_30 = sum(e.flexibility for e in last_30) / len(last_30)
            if recent_closed_30 > 0.7 and recent_flex_30 < 0.3:
                constr_penalty = 15

        # Type variety
        unique_types = len(set(e.optionality_type for e in self._entries))

        score = (avg_open * 25) + (avg_rev * 15) + (avg_flex * 20) + (avg_strat * 15) + (recent_open * 10) + (recent_flex * 5) + (unique_types * 2) - (avg_close * 10) - constr_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_doors_opened"] = round(sum(e.doors_opened for e in self._entries) / len(self._entries), 2)
            self._stats["avg_doors_closed"] = round(sum(e.doors_closed for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_closed = sum(e.doors_closed for e in recent) / len(recent)
                recent_flex = sum(e.flexibility for e in recent) / len(recent)
                self._stats["constraint_risk"] = recent_closed > 0.7 and recent_flex < 0.3
            else:
                self._stats["constraint_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.optionality_maximizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.optionality_maximizer")

    def _log_entry(self, entry: OptionalityEntry):
        try:
            with open(OPTIONALITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "decision": entry.decision,
                    "optionality_type": entry.optionality_type,
                    "doors_opened": entry.doors_opened,
                    "doors_closed": entry.doors_closed,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.optionality_maximizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_om_instance: Optional[OptionalityMaximizer] = None
_om_lock = threading.Lock()


def get_optionality_maximizer() -> OptionalityMaximizer:
    global _om_instance
    with _om_lock:
        if _om_instance is None:
            _om_instance = OptionalityMaximizer()
        return _om_instance
