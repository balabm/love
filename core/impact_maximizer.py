"""
LOVE Impact Maximizer — Leverage Intelligence (Modern AI Pattern)

Most effort yields linear results. This maximizer:

1. IMPACT TRACKING
   - Record impact events and their characteristics
   - Track impact types (direct, indirect, catalytic, systemic)
   - Log effort-to-impact ratios

2. PATTERN ANALYSIS
   - Identify the user's impact style (direct, multiplier, connector, amplifier)
   - Find high-leverage activities
   - Detect low-impact traps (busywork that feels productive)

3. LEVERAGE PRACTICES
   - Suggest leverage opportunities matched to current situation
   - Provide multipliers (automation, delegation, teaching, system-building)
   - Recommendation high-impact activity prioritization

4. EFFICIENCY CULTIVATION
   - Track the correlation between strategy and impact magnitude
   - Alert when effort is increasing without impact growth
   - Celebrate leverage breakthroughs

Architecture:
- record_impact(action, type, effort, recipients, outcome): Log impact
- get_impact_stats(): Get impact pattern analysis
- get_leverage_suggestion(trap, capacity): Get suggestion
- get_impact_score(): Calculate overall impact health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "impact_maximizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

IMPACT_LOG = DATA_DIR / "impacts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ImpactEntry:
    """A tracked impact entry."""
    entry_id: str = ""
    action: str = ""
    impact_type: str = ""  # direct, indirect, catalytic, systemic
    effort: float = 0.5  # 0-1
    recipients: int = 0
    outcome: str = ""
    outcome_quality: float = 0.5  # 0-1
    leverage: float = 0.5  # 0-1, how much this multiplies
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ImpactMaximizer:
    """
    Intelligent impact maximizer with leverage tracking and trap detection.
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
            "avg_leverage": 0.0,
            "avg_quality": 0.0,
            "effort_trap": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_impact(self, action: str = "", impact_type: str = "", effort: float = 0.5, recipients: int = 0, outcome: str = "", outcome_quality: float = 0.5, leverage: float = 0.5, notes: str = "") -> ImpactEntry:
        """Record an impact entry."""
        entry_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ImpactEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            impact_type=impact_type or "direct",
            effort=effort,
            recipients=recipients,
            outcome=outcome,
            outcome_quality=outcome_quality,
            leverage=leverage,
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

    def get_impact_stats(self) -> Dict[str, Any]:
        """Get impact pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Impact type analysis
        by_type = defaultdict(lambda: {"count": 0, "effort_sum": 0.0, "quality_sum": 0.0, "leverage_sum": 0.0, "recipients_sum": 0})
        for e in self._entries:
            by_type[e.impact_type]["count"] += 1
            by_type[e.impact_type]["effort_sum"] += e.effort
            by_type[e.impact_type]["quality_sum"] += e.outcome_quality
            by_type[e.impact_type]["leverage_sum"] += e.leverage
            by_type[e.impact_type]["recipients_sum"] += e.recipients

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_effort": round(data["effort_sum"] / count, 2),
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_leverage": round(data["leverage_sum"] / count, 2),
                "avg_recipients": round(data["recipients_sum"] / count, 1),
            }

        # Effort vs impact analysis
        high_effort = [e for e in self._entries if e.effort > 0.7]
        low_effort = [e for e in self._entries if e.effort <= 0.4]
        
        if high_effort:
            high_effort_quality = sum(e.outcome_quality for e in high_effort) / len(high_effort)
            high_effort_leverage = sum(e.leverage for e in high_effort) / len(high_effort)
        else:
            high_effort_quality = 0
            high_effort_leverage = 0

        if low_effort:
            low_effort_quality = sum(e.outcome_quality for e in low_effort) / len(low_effort)
            low_effort_leverage = sum(e.leverage for e in low_effort) / len(low_effort)
        else:
            low_effort_quality = 0
            low_effort_leverage = 0

        # Trap detection
        effort_trap = high_effort_quality < low_effort_quality and high_effort_leverage < low_effort_leverage

        # Recipient analysis
        total_recipients = sum(e.recipients for e in self._entries)
        if total_recipients > 0:
            avg_impact_per_recipient = sum(e.outcome_quality for e in self._entries) / total_recipients
        else:
            avg_impact_per_recipient = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_leverage = sum(e.leverage for e in recent) / len(recent)
            recent_quality = sum(e.outcome_quality for e in recent) / len(recent)
            recent_effort = sum(e.effort for e in recent) / len(recent)
        else:
            recent_leverage = 0
            recent_quality = 0
            recent_effort = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_leverage = sum(e.leverage for e in older) / len(older)
            older_quality = sum(e.outcome_quality for e in older) / len(older)
            leverage_trend = recent_leverage - older_leverage
            quality_trend = recent_quality - older_quality
        else:
            leverage_trend = 0
            quality_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "effort_analysis": {
                "high_effort_quality": round(high_effort_quality, 2),
                "low_effort_quality": round(low_effort_quality, 2),
                "high_effort_leverage": round(high_effort_leverage, 2),
                "low_effort_leverage": round(low_effort_leverage, 2),
            },
            "effort_trap": effort_trap,
            "total_recipients": total_recipients,
            "avg_impact_per_recipient": round(avg_impact_per_recipient, 2),
            "avg_leverage": round(sum(e.leverage for e in self._entries) / len(self._entries), 2),
            "avg_quality": round(sum(e.outcome_quality for e in self._entries) / len(self._entries), 2),
            "avg_effort": round(sum(e.effort for e in self._entries) / len(self._entries), 2),
            "leverage_trend": round(leverage_trend, 2),
            "quality_trend": round(quality_trend, 2),
            "recent_effort": round(recent_effort, 2),
        }

    def get_leverage_suggestion(self, trap: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "busywork": [
                "Automate it. If you do it more than twice, write a script, template, or process.",
                "Eliminate it. Is this necessary? What happens if you stop? Often, nothing.",
                "Delegate it. Someone else can do 80% as well as you. Let them.",
            ],
            "perfectionism": [
                "80% is the new 100%. Ship it. Perfect is the enemy of done.",
                "What would 'good enough' look like? Do that. Move on.",
                "The last 20% takes 80% of the time. Is it worth it? Usually not.",
            ],
            "reactivity": [
                "Batch process. Don't answer every email immediately. Check twice a day.",
                "Set boundaries. 'I respond to non-urgent requests within 24 hours.' Stick to it.",
                "Protect your morning. The first 2 hours are for creation, not reaction.",
            ],
            "isolation": [
                "Teach someone. The best way to multiply your impact is to clone your capability.",
                "Build a system. Document your process. Others can use it without you.",
                "Connect people. Introductions are the highest-leverage action you can take.",
            ],
            "scarcity": [
                "Say no to good opportunities so you can say yes to great ones. Default to no.",
                "What are you uniquely positioned to do? Do only that. Delegate or drop the rest.",
                "Focus on high-leverage activities. 1 hour of system-building > 4 hours of doing.",
            ],
            "general": [
                "The Pareto Principle: 80% of your impact comes from 20% of your actions. Find the 20%.",
                "Ask: 'What can only I do?' Do that. Everything else is negotiable.",
                "Impact is not about doing more. It's about doing what matters, then stopping.",
            ],
        }

        selected = suggestions.get(trap, suggestions["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. This is when leverage matters most. Do less, but do what multiplies."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Good time to build systems that will multiply future impact."
        else:
            capacity_note = "High capacity. This is when you can take on catalytic work. Create ripples."

        return {
            "trap": trap or "none",
            "capacity": capacity,
            "suggestion": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Effort is linear. Leverage is exponential. A lever lets you move more with less. The best levers are systems, teaching, and connections. Build levers. Then use them.",
        }

    def get_impact_score(self) -> int:
        """Calculate overall impact health (0-100)."""
        if not self._entries:
            return 30

        # Leverage and quality
        avg_leverage = sum(e.leverage for e in self._entries) / len(self._entries)
        avg_quality = sum(e.outcome_quality for e in self._entries) / len(self._entries)

        # Efficiency (low effort, high quality)
        avg_effort = sum(e.effort for e in self._entries) / len(self._entries)
        efficiency = avg_quality / max(0.1, avg_effort)

        # Recipient reach
        total_recipients = sum(e.recipients for e in self._entries)
        recipient_score = min(1, total_recipients / 100)

        # Impact type variety
        unique_types = len(set(e.impact_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_leverage = sum(e.leverage for e in recent) / len(recent)
            recent_quality = sum(e.outcome_quality for e in recent) / len(recent)
            recent_effort = sum(e.effort for e in recent) / len(recent)
        else:
            recent_leverage = 0
            recent_quality = 0
            recent_effort = 0

        # Effort trap penalty
        high_effort = [e for e in self._entries if e.effort > 0.7]
        low_effort = [e for e in self._entries if e.effort <= 0.4]
        if high_effort and low_effort:
            high_effort_quality = sum(e.outcome_quality for e in high_effort) / len(high_effort)
            low_effort_quality = sum(e.outcome_quality for e in low_effort) / len(low_effort)
            trap_penalty = 10 if high_effort_quality < low_effort_quality else 0
        else:
            trap_penalty = 0

        score = (avg_leverage * 25) + (avg_quality * 20) + (efficiency * 15) + (recipient_score * 10) + (unique_types * 3) + (recent_leverage * 15) + (recent_quality * 10) + (recent_effort * 5) - trap_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_leverage"] = round(sum(e.leverage for e in self._entries) / len(self._entries), 2)
            self._stats["avg_quality"] = round(sum(e.outcome_quality for e in self._entries) / len(self._entries), 2)

            high_effort = [e for e in self._entries if e.effort > 0.7]
            low_effort = [e for e in self._entries if e.effort <= 0.4]
            if high_effort and low_effort:
                high_effort_quality = sum(e.outcome_quality for e in high_effort) / len(high_effort)
                low_effort_quality = sum(e.outcome_quality for e in low_effort) / len(low_effort)
                self._stats["effort_trap"] = high_effort_quality < low_effort_quality

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.impact_maximizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.impact_maximizer")

    def _log_entry(self, entry: ImpactEntry):
        try:
            with open(IMPACT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "impact_type": entry.impact_type,
                    "effort": entry.effort,
                    "recipients": entry.recipients,
                    "outcome": entry.outcome,
                    "outcome_quality": entry.outcome_quality,
                    "leverage": entry.leverage,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.impact_maximizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_im_instance: Optional[ImpactMaximizer] = None
_im_lock = threading.Lock()


def get_impact_maximizer() -> ImpactMaximizer:
    global _im_instance
    with _im_lock:
        if _im_instance is None:
            _im_instance = ImpactMaximizer()
        return _im_instance
