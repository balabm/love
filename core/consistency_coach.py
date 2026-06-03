"""
LOVE Consistency Coach — Steady-State Intelligence (Modern AI Pattern)

Most people start strong and fade. This coach:

1. CONSISTENCY TRACKING
   - Record daily actions and streaks for commitments
   - Track consistency across multiple domains simultaneously
   - Log what disrupts consistency and what restores it

2. PATTERN ANALYSIS
   - Identify consistency profiles (daily, weekly, flexible, rigid)
   - Find the user's consistency sweet spot (how many days/weeks before burnout)
   - Detect consistency crash patterns

3. SUSTAINABILITY DESIGN
   - Suggest the minimum viable dose for continued consistency
   - Provide recovery protocols after breaks
   - Recommend flexibility rules to prevent all-or-nothing thinking

4. MOMENTUM BUILDING
   - Track the compound effect of small consistent actions
   - Celebrate not just streaks, but the quality of the practice
   - Alert when consistency is becoming compulsion

Architecture:
- record_action(action, domain, done, quality): Log action
- get_consistency_stats(): Get consistency pattern analysis
- get_sustainability_suggestion(domain, current_streak): Get sustainability plan
- get_consistency_score(): Calculate overall consistency health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "consistency_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACTION_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class DailyAction:
    """A tracked daily action."""
    action_id: str = ""
    action: str = ""
    domain: str = ""  # fitness, learning, creativity, relationship, work, health, finance
    done: bool = False
    quality: float = 0.5  # 0-1
    duration_minutes: float = 0.0
    resistance_felt: float = 0.0  # 0-1
    enjoyment: float = 0.5  # 0-1
    recovery_needed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ConsistencyCoach:
    """
    Intelligent consistency coach with sustainability design and burnout prevention.
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
        self._actions: deque = deque(maxlen=500)
        self._stats = {
            "total_actions": 0,
            "completion_rate": 0.0,
            "avg_quality": 0.0,
            "burnout_risk": False,
            "strongest_domain": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", domain: str = "", done: bool = False, quality: float = 0.5, duration: float = 0, resistance: float = 0.0, enjoyment: float = 0.5, recovery_needed: bool = False, notes: str = "") -> DailyAction:
        """Record a daily action."""
        action_id = f"action_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._actions)}"
        da = DailyAction(
            action_id=action_id,
            action=action or "unspecified",
            domain=domain or "general",
            done=done,
            quality=quality,
            duration_minutes=duration,
            resistance_felt=resistance,
            enjoyment=enjoyment,
            recovery_needed=recovery_needed,
            notes=notes,
        )

        with self._lock:
            self._actions.append(da)
            self._stats["total_actions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_action(da)

        return da

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_consistency_stats(self) -> Dict[str, Any]:
        """Get consistency pattern analysis."""
        if not self._actions:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "done": 0, "quality_sum": 0.0, "resistance_sum": 0.0, "enjoyment_sum": 0.0})
        for a in self._actions:
            by_domain[a.domain]["count"] += 1
            if a.done:
                by_domain[a.domain]["done"] += 1
            by_domain[a.domain]["quality_sum"] += a.quality
            by_domain[a.domain]["resistance_sum"] += a.resistance_felt
            by_domain[a.domain]["enjoyment_sum"] += a.enjoyment

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "completion_rate": round(data["done"] / count, 2),
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_resistance": round(data["resistance_sum"] / count, 2),
                "avg_enjoyment": round(data["enjoyment_sum"] / count, 2),
            }

        strongest = max(domain_stats.items(), key=lambda x: x[1]["completion_rate"]) if domain_stats else ("", {})

        # Streak calculation (simplified - consecutive done days per domain)
        streaks = {}
        for d in by_domain.keys():
            domain_actions = [a for a in self._actions if a.domain == d]
            current_streak = 0
            max_streak = 0
            for a in reversed(domain_actions):
                if a.done:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            streaks[d] = {
                "current": current_streak,
                "max": max_streak,
            }

        # Burnout detection
        recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            high_resistance = sum(1 for a in recent if a.resistance_felt > 0.7)
            low_enjoyment = sum(1 for a in recent if a.enjoyment < 0.3)
            recovery_count = sum(1 for a in recent if a.recovery_needed)
            burnout_risk = (high_resistance / max(1, len(recent)) > 0.4) or (low_enjoyment / max(1, len(recent)) > 0.4) or (recovery_count > 3)
        else:
            burnout_risk = False

        # All-or-nothing detection
        missed = [a for a in self._actions if not a.done]
        if missed:
            post_miss_rate = sum(1 for a in missed if self._get_next_action_done(a) is False) / len(missed)
        else:
            post_miss_rate = 0

        return {
            "total_actions": len(self._actions),
            "domain_stats": domain_stats,
            "strongest_domain": strongest[0],
            "streaks": streaks,
            "burnout_risk": burnout_risk,
            "completion_rate": round(sum(1 for a in self._actions if a.done) / len(self._actions), 2),
            "avg_quality": round(sum(a.quality for a in self._actions) / len(self._actions), 2),
            "post_miss_cascade": round(post_miss_rate, 2),
        }

    def _get_next_action_done(self, action: DailyAction) -> Optional[bool]:
        """Check if the next action after this one was done."""
        found = False
        for a in self._actions:
            if found:
                return a.done
            if a.action_id == action.action_id:
                found = True
        return None

    def get_sustainability_suggestion(self, domain: str = "", current_streak: int = 0, feeling: str = "good") -> Dict[str, Any]:
        """Get sustainability plan."""
        if feeling == "exhausted":
            suggestion = {
                "message": "You're exhausted. Not lazy. Not weak. Exhausted. Rest is not quitting.",
                "action": "Reduce to the absolute minimum for 3 days. Then reassess.",
                "minimum": "Show up for 5 minutes. That's it. 5 minutes counts.",
            }
        elif feeling == "bored":
            suggestion = {
                "message": "Boredom is a signal. You've outgrown the current form.",
                "action": "Change one variable: time, place, music, companion, or format.",
                "minimum": "Do the same thing but differently. Novelty restores engagement.",
            }
        elif feeling == "overwhelmed":
            suggestion = {
                "message": "Overwhelm happens when everything feels equally urgent.",
                "action": "Pick ONE domain to protect. Let others float for now.",
                "minimum": "One commitment kept is infinitely better than five abandoned.",
            }
        elif feeling == "good":
            suggestion = {
                "message": "Good. This is your growth window. But don't expand too fast.",
                "action": "Add one small thing, or deepen one existing thing. Not both.",
                "minimum": "Maintain the current practice. Improvement is optional; maintenance is mandatory.",
            }
        else:
            suggestion = {
                "message": "Check in with yourself. What do you actually need right now?",
                "action": "Journal for 2 minutes. Then decide.",
                "minimum": "Do something, even if it's not the planned thing.",
            }

        # Streak-specific advice
        if current_streak > 30:
            streak_note = f"{current_streak}-day streak. Impressive. But streaks can become prisons. Missing one day doesn't erase {current_streak} days."
        elif current_streak > 7:
            streak_note = f"{current_streak}-day streak. You're building momentum. Protect it by not pushing too hard."
        else:
            streak_note = "Early days. The hardest part is starting. You're past that. Keep showing up."

        return {
            "domain": domain or "general",
            "feeling": feeling,
            **suggestion,
            "streak_note": streak_note,
            "recovery_rule": "If you miss a day, the next day you do the minimum. No catching up. No punishment. Just return.",
        }

    def get_consistency_score(self) -> int:
        """Calculate overall consistency health (0-100)."""
        if not self._actions:
            return 35

        # Completion rate
        completion = sum(1 for a in self._actions if a.done) / len(self._actions)

        # Quality
        avg_quality = sum(a.quality for a in self._actions) / len(self._actions)

        # Enjoyment (sustainable consistency requires some joy)
        avg_enjoyment = sum(a.enjoyment for a in self._actions) / len(self._actions)

        # Domain balance
        domains = defaultdict(int)
        for a in self._actions:
            if a.done:
                domains[a.domain] += 1
        domain_balance = len(domains)

        # Recent trend
        recent = list(self._actions)[-14:]
        recent_completion = sum(1 for a in recent if a.done) / len(recent)
        older = list(self._actions)[:-14] if len(self._actions) > 14 else []
        if older:
            older_completion = sum(1 for a in older if a.done) / len(older)
            trend = recent_completion - older_completion
        else:
            trend = 0

        # Burnout protection (low resistance = good)
        avg_resistance = sum(a.resistance_felt for a in self._actions) / len(self._actions)

        score = (completion * 30) + (avg_quality * 15) + (avg_enjoyment * 15) + (domain_balance * 3) + (trend * 10) + ((1 - avg_resistance) * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._actions:
            done = sum(1 for a in self._actions if a.done)
            self._stats["completion_rate"] = round(done / len(self._actions), 2)
            self._stats["avg_quality"] = round(sum(a.quality for a in self._actions) / len(self._actions), 2)

            recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if recent:
                high_resistance = sum(1 for a in recent if a.resistance_felt > 0.7)
                low_enjoyment = sum(1 for a in recent if a.enjoyment < 0.3)
                recovery_count = sum(1 for a in recent if a.recovery_needed)
                self._stats["burnout_risk"] = (high_resistance / max(1, len(recent)) > 0.4) or (low_enjoyment / max(1, len(recent)) > 0.4) or (recovery_count > 3)

            by_domain = defaultdict(lambda: {"done": 0, "total": 0})
            for a in self._actions:
                by_domain[a.domain]["total"] += 1
                if a.done:
                    by_domain[a.domain]["done"] += 1
            if by_domain:
                strongest = max(by_domain.items(), key=lambda x: x[1]["done"] / max(1, x[1]["total"]))
                self._stats["strongest_domain"] = strongest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.consistency_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.consistency_coach")

    def _log_action(self, action: DailyAction):
        try:
            with open(ACTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": action.timestamp,
                    "action": action.action,
                    "domain": action.domain,
                    "done": action.done,
                    "quality": action.quality,
                    "resistance": action.resistance_felt,
                    "enjoyment": action.enjoyment,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.consistency_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cc_instance: Optional[ConsistencyCoach] = None
_cc_lock = threading.Lock()


def get_consistency_coach() -> ConsistencyCoach:
    global _cc_instance
    with _cc_lock:
        if _cc_instance is None:
            _cc_instance = ConsistencyCoach()
        return _cc_instance
