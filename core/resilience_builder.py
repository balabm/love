"""
LOVE Resilience Builder — Bounce-Back Intelligence (Modern AI Pattern)

Most resilience advice is generic. This builder:

1. RESILIENCE TRACKING
   - Record setbacks and the user's response
   - Track recovery time, learning extraction, and growth from adversity
   - Log support systems used and their effectiveness

2. PATTERN ANALYSIS
   - Identify the user's resilience style (fighter, adapter, meaning-maker, connector)
   - Find which setbacks are hardest to recover from and why
   - Detect resilience depleters (chronic stress, isolation, sleep debt)

3. RESILIENCE BUILDING
   - Suggest micro-recovery practices for current setbacks
   - Provide resilience-strengthening exercises
   - Recommend support activation strategies

4. GROWTH INTEGRATION
   - Track post-traumatic/ post-adversity growth
   - Celebrate resilience milestones
   - Alert when resilience reserves are low

Architecture:
- record_setback(event, impact, response, recovery_time): Log setback
- get_resilience_stats(): Get resilience pattern analysis
- get_recovery_suggestion(setback_type, current_state): Get recovery plan
- get_resilience_score(): Calculate overall resilience health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "resilience_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SETBACK_LOG = DATA_DIR / "setbacks.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Setback:
    """A tracked setback and response."""
    setback_id: str = ""
    event: str = ""
    category: str = ""  # health, work, relationship, finance, identity, loss, failure, betrayal
    impact: float = 0.5  # 0-1
    initial_response: str = ""  # shock, denial, anger, despair, action, numbness
    recovery_actions: List[str] = field(default_factory=list)
    support_used: List[str] = field(default_factory=list)
    recovery_time_days: float = 0.0
    lessons_learned: List[str] = field(default_factory=list)
    growth_achieved: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ResilienceBuilder:
    """
    Intelligent resilience builder with setback pattern analysis and recovery optimization.
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
        self._setbacks: deque = deque(maxlen=200)
        self._stats = {
            "total_setbacks": 0,
            "avg_recovery_time": 0.0,
            "avg_growth": 0.0,
            "hardest_category": "",
            "resilience_trend": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_setback(self, event: str = "", category: str = "", impact: float = 0.5, initial_response: str = "", recovery_actions: Optional[List[str]] = None, support_used: Optional[List[str]] = None, recovery_time: float = 0, lessons: Optional[List[str]] = None, growth: float = 0.0, notes: str = "") -> Setback:
        """Record a setback and response."""
        setback_id = f"setback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._setbacks)}"
        sb = Setback(
            setback_id=setback_id,
            event=event or "unspecified",
            category=category or "general",
            impact=impact,
            initial_response=initial_response or "shock",
            recovery_actions=recovery_actions or [],
            support_used=support_used or [],
            recovery_time_days=recovery_time,
            lessons_learned=lessons or [],
            growth_achieved=growth,
            notes=notes,
        )

        with self._lock:
            self._setbacks.append(sb)
            self._stats["total_setbacks"] += 1
            self._update_stats()

        self._save_stats()
        self._log_setback(sb)

        return sb

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_resilience_stats(self) -> Dict[str, Any]:
        """Get resilience pattern analysis."""
        if not self._setbacks:
            return {"status": "insufficient_data"}

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "impact_sum": 0.0, "recovery_sum": 0.0, "growth_sum": 0.0})
        for s in self._setbacks:
            by_category[s.category]["count"] += 1
            by_category[s.category]["impact_sum"] += s.impact
            by_category[s.category]["recovery_sum"] += s.recovery_time_days
            by_category[s.category]["growth_sum"] += s.growth_achieved

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            category_stats[c] = {
                "count": count,
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_recovery": round(data["recovery_sum"] / count, 1),
                "avg_growth": round(data["growth_sum"] / count, 2),
            }

        hardest = max(category_stats.items(), key=lambda x: x[1]["avg_recovery"]) if category_stats else ("", {})

        # Response analysis
        by_response = defaultdict(lambda: {"count": 0, "recovery_sum": 0.0, "growth_sum": 0.0})
        for s in self._setbacks:
            by_response[s.initial_response]["count"] += 1
            by_response[s.initial_response]["recovery_sum"] += s.recovery_time_days
            by_response[s.initial_response]["growth_sum"] += s.growth_achieved

        response_stats = {}
        for r, data in by_response.items():
            count = data["count"]
            response_stats[r] = {
                "count": count,
                "avg_recovery": round(data["recovery_sum"] / count, 1),
                "avg_growth": round(data["growth_sum"] / count, 2),
            }

        # Support effectiveness
        by_support = defaultdict(lambda: {"count": 0, "recovery_sum": 0.0})
        for s in self._setbacks:
            for support in s.support_used:
                by_support[support]["count"] += 1
                by_support[support]["recovery_sum"] += s.recovery_time_days

        support_stats = {}
        for sup, data in by_support.items():
            count = data["count"]
            support_stats[sup] = {
                "count": count,
                "avg_recovery": round(data["recovery_sum"] / count, 1),
            }

        # Trend
        recent = list(self._setbacks)[-10:]
        older = list(self._setbacks)[:-10] if len(self._setbacks) > 10 else []
        if recent and older:
            recent_recovery = sum(s.recovery_time_days for s in recent) / len(recent)
            older_recovery = sum(s.recovery_time_days for s in older) / len(older)
            trend = "improving" if recent_recovery < older_recovery * 0.8 else "stable" if recent_recovery < older_recovery * 1.2 else "declining"
        else:
            trend = "stable"

        return {
            "total_setbacks": len(self._setbacks),
            "category_stats": category_stats,
            "hardest_category": hardest[0],
            "response_stats": response_stats,
            "support_effectiveness": support_stats,
            "avg_recovery_time": round(sum(s.recovery_time_days for s in self._setbacks) / len(self._setbacks), 1),
            "avg_growth": round(sum(s.growth_achieved for s in self._setbacks) / len(self._setbacks), 2),
            "resilience_trend": trend,
        }

    def get_recovery_suggestion(self, setback_type: str = "", current_state: str = "", impact: float = 0.5) -> Dict[str, Any]:
        """Get recovery plan."""
        immediate = {
            "shock": "Breathe. You're in shock. Don't make any decisions for 24 hours.",
            "denial": "It's okay to not be ready. But notice what you're avoiding feeling.",
            "anger": "Your anger is valid. Use it to fuel action, not destruction.",
            "despair": "This is the bottom. The only way from here is up. You don't have to see it yet.",
            "numbness": "Numbness is protection. When you're ready, the feelings will come. Be gentle.",
            "action": "Good. Action helps. But don't outrun your need to feel this.",
        }

        strategies = {
            "health": [
                "Prioritize sleep above everything else",
                "Move your body gently—walk, stretch, breathe",
                "Eat nourishing food even if you don't feel like it",
                "See a doctor if symptoms persist beyond 2 weeks",
            ],
            "work": [
                "Take one day to just organize your thoughts",
                "Ask for help. Vulnerability at work is strength",
                "Focus on what you can control, accept what you can't",
                "Document lessons before the pain fades and you forget",
            ],
            "relationship": [
                "Feel the grief. Don't rush to fix or replace",
                "Talk to someone who won't try to solve it",
                "Write an unsent letter to process what you can't say",
                "Give yourself permission to be messy for a while",
            ],
            "finance": [
                "Face the numbers. Fear grows in the dark",
                "Make one small financial decision today",
                "Seek professional advice if needed—pride is expensive",
                "Remember: your worth is not your net worth",
            ],
            "identity": [
                "You're in transition. The old you is dying. This is growth",
                "Write about who you're becoming, not who you were",
                "Try something that the old you never would have",
                "Talk to someone who sees the new you clearly",
            ],
            "loss": [
                "Grief has no timeline. Don't let anyone rush you",
                "Create a ritual to honor what you lost",
                "Let yourself miss them without trying to 'move on'",
                "Seek grief support if you're drowning",
            ],
            "failure": [
                "Separate the event from your identity. You failed. You're not a failure",
                "Extract one lesson. Just one. That's enough for now",
                "Share the failure with someone safe. Shame dies in sunlight",
                "Ask: What would I advise a friend in this situation?",
            ],
            "betrayal": [
                "Your trust was broken. Your ability to trust isn't",
                "Feel the rage, then decide what justice looks like for you",
                "Don't let their choices become your prison",
                "Rebuild trust slowly. Very slowly. With yourself first",
            ],
        }

        base = strategies.get(setback_type, strategies["failure"])
        response_message = immediate.get(current_state, "Whatever you're feeling is valid. Start from there.")

        if impact > 0.7:
            urgency = "This is heavy. Consider professional support. You don't have to carry this alone."
        elif impact > 0.4:
            urgency = "This matters. Take it seriously, but don't catastrophize."
        else:
            urgency = "This is manageable. Use it as practice for bigger storms."

        return {
            "setback_type": setback_type or "general",
            "current_state": current_state or "unknown",
            "impact": impact,
            "immediate_response": response_message,
            "strategies": base,
            "urgency": urgency,
            "reminder": "Recovery isn't linear. Some days will be harder than others. That's the process.",
        }

    def get_resilience_score(self) -> int:
        """Calculate overall resilience health (0-100)."""
        if not self._setbacks:
            return 50

        # Recovery speed (faster is better)
        avg_recovery = sum(s.recovery_time_days for s in self._setbacks) / len(self._setbacks)
        recovery_score = max(0, 30 - avg_recovery)

        # Growth from setbacks
        avg_growth = sum(s.growth_achieved for s in self._setbacks) / len(self._setbacks)

        # Support usage (using support is strength)
        support_rate = sum(1 for s in self._setbacks if s.support_used) / len(self._setbacks)

        # Action orientation
        action_rate = sum(1 for s in self._setbacks if s.recovery_actions) / len(self._setbacks)

        # Learning extraction
        learning_rate = sum(1 for s in self._setbacks if s.lessons_learned) / len(self._setbacks)

        # Recent trend
        recent = self._setbacks[-5:] if len(self._setbacks) >= 5 else self._setbacks
        recent_recovery = sum(s.recovery_time_days for s in recent) / len(recent)
        trend_bonus = 10 if recent_recovery < avg_recovery else 0

        score = recovery_score + (avg_growth * 25) + (support_rate * 15) + (action_rate * 10) + (learning_rate * 10) + trend_bonus
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._setbacks:
            self._stats["avg_recovery_time"] = round(sum(s.recovery_time_days for s in self._setbacks) / len(self._setbacks), 1)
            self._stats["avg_growth"] = round(sum(s.growth_achieved for s in self._setbacks) / len(self._setbacks), 2)

            by_category = defaultdict(lambda: {"recovery": 0.0, "count": 0})
            for s in self._setbacks:
                by_category[s.category]["recovery"] += s.recovery_time_days
                by_category[s.category]["count"] += 1
            
            if by_category:
                hardest = max(by_category.items(), key=lambda x: x[1]["recovery"] / max(1, x[1]["count"]))
                self._stats["hardest_category"] = hardest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.resilience_builder")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.resilience_builder")

    def _log_setback(self, setback: Setback):
        try:
            with open(SETBACK_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": setback.timestamp,
                    "event": setback.event,
                    "category": setback.category,
                    "impact": setback.impact,
                    "recovery_time": setback.recovery_time_days,
                    "growth": setback.growth_achieved,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.resilience_builder")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rb_instance: Optional[ResilienceBuilder] = None
_rb_lock = threading.Lock()


def get_resilience_builder() -> ResilienceBuilder:
    global _rb_instance
    with _rb_lock:
        if _rb_instance is None:
            _rb_instance = ResilienceBuilder()
        return _rb_instance
