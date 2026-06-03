"""
LOVE Uncertainty Embracer — Ambiguity Intelligence (Modern AI Pattern)

Most people suffer because they demand certainty in an uncertain world. This embracer:

1. UNCERTAINTY TRACKING
   - Record uncertainty experiences and their characteristics
   - Track uncertainty types (career, relationship, health, existential, creative)
   - Log tolerance, growth, and insight from uncertainty

2. PATTERN ANALYSIS
   - Identify the user's uncertainty profile (embracing, anxious, avoiding, transforming)
   - Find uncertainty patterns that create growth vs paralysis
   - Detect intolerance of ambiguity and its costs

3. UNCERTAINTY BUILDING
   - Suggest practices for tolerating and leveraging ambiguity
   - Provide frameworks for decision-making under uncertainty
   - Recommend practices for finding peace in not knowing

4. FLEXIBILITY CULTIVATION
   - Track the correlation between uncertainty tolerance and resilience
   - Alert when demand for certainty is limiting life options
   - Celebrate moments of genuine comfort with the unknown

Architecture:
- record_uncertainty(uncertainty, type, tolerance, growth, insight): Log uncertainty
- get_uncertainty_stats(): Get uncertainty pattern analysis
- get_uncertainty_suggestion(capacity, context): Get suggestion
- get_uncertainty_score(): Calculate overall uncertainty health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "uncertainty_embracer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UNCERTAINTY_LOG = DATA_DIR / "uncertainties.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class UncertaintyEntry:
    """A tracked uncertainty experience."""
    entry_id: str = ""
    uncertainty: str = ""  # what was uncertain
    uncertainty_type: str = ""  # career, relationship, health, existential, creative
    tolerance: float = 0.0  # 0-1
    growth: float = 0.0  # 0-1
    insight: float = 0.0  # 0-1
    anxiety: float = 0.0  # 0-1
    action: float = 0.0  # 0-1 action despite uncertainty
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class UncertaintyEmbracer:
    """
    Intelligent uncertainty embracer with tolerance detection and flexibility cultivation.
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
            "avg_tolerance": 0.0,
            "avg_growth": 0.0,
            "intolerance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_uncertainty(self, uncertainty: str = "", uncertainty_type: str = "", tolerance: float = 0.0, growth: float = 0.0, insight: float = 0.0, anxiety: float = 0.0, action: float = 0.0, notes: str = "") -> UncertaintyEntry:
        """Record an uncertainty experience."""
        entry_id = f"unc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = UncertaintyEntry(
            entry_id=entry_id,
            uncertainty=uncertainty or "unspecified",
            uncertainty_type=uncertainty_type or "general",
            tolerance=tolerance,
            growth=growth,
            insight=insight,
            anxiety=anxiety,
            action=action,
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

    def get_uncertainty_stats(self) -> Dict[str, Any]:
        """Get uncertainty pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "tolerance_sum": 0.0, "growth_sum": 0.0, "insight_sum": 0.0})
        for e in self._entries:
            by_type[e.uncertainty_type]["count"] += 1
            by_type[e.uncertainty_type]["tolerance_sum"] += e.tolerance
            by_type[e.uncertainty_type]["growth_sum"] += e.growth
            by_type[e.uncertainty_type]["insight_sum"] += e.insight

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_tolerance": round(data["tolerance_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_insight": round(data["insight_sum"] / count, 2),
            }

        # Tolerance analysis
        high_tol = [e for e in self._entries if e.tolerance > 0.7]
        low_tol = [e for e in self._entries if e.tolerance < 0.4]
        if high_tol and low_tol:
            high_tol_growth = sum(e.growth for e in high_tol) / len(high_tol)
            low_tol_growth = sum(e.growth for e in low_tol) / len(low_tol)
            high_tol_insight = sum(e.insight for e in high_tol) / len(high_tol)
            low_tol_insight = sum(e.insight for e in low_tol) / len(low_tol)
        else:
            high_tol_growth = 0
            low_tol_growth = 0
            high_tol_insight = 0
            low_tol_insight = 0

        # Action analysis
        high_act = [e for e in self._entries if e.action > 0.7]
        low_act = [e for e in self._entries if e.action < 0.4]
        if high_act and low_act:
            high_act_growth = sum(e.growth for e in high_act) / len(high_act)
            low_act_growth = sum(e.growth for e in low_act) / len(low_act)
        else:
            high_act_growth = 0
            low_act_growth = 0

        # Intolerance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_tol = sum(e.tolerance for e in recent) / len(recent)
            recent_anxiety = sum(e.anxiety for e in recent) / len(recent)
            intolerance_risk = recent_tol < 0.3 and recent_anxiety > 0.7
        else:
            intolerance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "tolerance_impact": {
                "high_tolerance_growth": round(high_tol_growth, 2),
                "low_tolerance_growth": round(low_tol_growth, 2),
                "high_tolerance_insight": round(high_tol_insight, 2),
                "low_tolerance_insight": round(low_tol_insight, 2),
            },
            "action_effect": {
                "high_action_growth": round(high_act_growth, 2),
                "low_action_growth": round(low_act_growth, 2),
            },
            "intolerance_risk": intolerance_risk,
            "avg_tolerance": round(sum(e.tolerance for e in self._entries) / len(self._entries), 2),
            "avg_growth": round(sum(e.growth for e in self._entries) / len(self._entries), 2),
        }

    def get_uncertainty_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get uncertainty suggestion."""
        suggestions = [
            "You don't need to know the outcome to take the first step. Most of life's best decisions are made with incomplete information. Act anyway.",
            "Uncertainty is not the enemy. It's the container for possibility. The certain path is the closed path. The uncertain path is where adventure lives.",
            "Name your fear of the unknown. What exactly are you afraid of? Usually it's not the uncertainty itself. It's a specific bad outcome. Name it. Then plan for it.",
            "Make peace with 'I don't know.' It's a complete answer. It's an honest answer. The person who admits they don't know is wiser than the person who pretends they do.",
            "Act as if. Not as if you know. As if you can handle whatever comes. Because you can. You've handled uncertainty before. You'll handle it again.",
            "The plan that requires certainty is the plan that never starts. Start with what you know. Adjust as you learn. That's how everything gets built.",
            "Uncertainty reveals character. The person who panics. The person who freezes. The person who adapts. Pay attention to your response. That's data about who you are.",
            "Focus on what you can control. Not the outcome. The effort. Not the result. The process. Not the future. The present moment. Control what's controllable.",
            "Every expert was once a beginner. Every master once knew nothing. Uncertainty is the beginning of all learning. Embrace it as the gateway to growth.",
            "Life is inherently uncertain. The person who demands certainty is demanding something that doesn't exist. And that demand creates endless suffering. Learn to live with not knowing. It's the only way to live at all."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One breath in uncertainty. One acceptance of not knowing. One small step anyway. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A decision despite doubt. An action despite fear. Medium embrace of ambiguity."
        else:
            capacity_note = "Good capacity. Full engagement with the unknown. A bold move into uncertainty. You have the strength to thrive in ambiguity."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Uncertainty is the water we swim in. We pretend it's not there. We build elaborate structures of prediction and planning to deny it. But it's always there. The job you might lose. The relationship that might end. The health that might fail. The future that might not match your plans. And the tragedy is not the uncertainty itself. It's the energy we spend fighting it. The person who embraces uncertainty is not reckless. They're realistic. They know that control is an illusion. That the attempt to eliminate uncertainty is the attempt to eliminate life itself. Because life is uncertain. Always. Every moment. The embrace of uncertainty is not resignation. It's liberation. It's the freedom to act without guarantees. To love without assurances. To live without a script. And that freedom is the only real freedom there is."
        }

    def get_uncertainty_score(self) -> int:
        """Calculate overall uncertainty health (0-100)."""
        if not self._entries:
            return 25

        avg_tol = sum(e.tolerance for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)
        avg_insight = sum(e.insight for e in self._entries) / len(self._entries)
        avg_action = sum(e.action for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_tol = sum(e.tolerance for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
        else:
            recent_tol = 0
            recent_growth = 0

        # Intolerance penalty
        intol_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_tol_30 = sum(e.tolerance for e in last_30) / len(last_30)
            recent_anxiety_30 = sum(e.anxiety for e in last_30) / len(last_30)
            if recent_tol_30 < 0.3 and recent_anxiety_30 > 0.7:
                intol_penalty = 15

        # Type variety
        unique_types = len(set(e.uncertainty_type for e in self._entries))

        # Normalize anxiety
        avg_anxiety = sum(e.anxiety for e in self._entries) / len(self._entries)

        score = (avg_tol * 30) + (avg_growth * 20) + (avg_insight * 15) + (avg_action * 20) + (recent_tol * 10) + (recent_growth * 5) + (unique_types * 2) - intol_penalty - (avg_anxiety * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_tolerance"] = round(sum(e.tolerance for e in self._entries) / len(self._entries), 2)
            self._stats["avg_growth"] = round(sum(e.growth for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_tol = sum(e.tolerance for e in recent) / len(recent)
                recent_anxiety = sum(e.anxiety for e in recent) / len(recent)
                self._stats["intolerance_risk"] = recent_tol < 0.3 and recent_anxiety > 0.7
            else:
                self._stats["intolerance_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.uncertainty_embracer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.uncertainty_embracer")

    def _log_entry(self, entry: UncertaintyEntry):
        try:
            with open(UNCERTAINTY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "uncertainty": entry.uncertainty,
                    "uncertainty_type": entry.uncertainty_type,
                    "tolerance": entry.tolerance,
                    "growth": entry.growth,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.uncertainty_embracer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ue_instance: Optional[UncertaintyEmbracer] = None
_ue_lock = threading.Lock()


def get_uncertainty_embracer() -> UncertaintyEmbracer:
    global _ue_instance
    with _ue_lock:
        if _ue_instance is None:
            _ue_instance = UncertaintyEmbracer()
        return _ue_instance
