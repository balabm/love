"""
LOVE Expected Value Coach — Probabilistic Intelligence (Modern AI Pattern)

Most people ignore expected value. This coach:

1. EV TRACKING
   - Record expected value assessments and their characteristics
   - Track EV types (financial, career, relational, health, creative)
   - Log probability estimate, payoff estimate, and actual outcome

2. PATTERN ANALYSIS
   - Identify the user's EV profile (optimistic, pessimistic, calibrated, ignorant)
   - Find EV patterns that create good vs bad bets
   - Detect chronic miscalibration and its costs

3. EV COACHING
   - Suggest practices for improving probability estimation
   - Provide frameworks for expected value calculation
   - Recommend practices for separating emotion from EV

4. CALIBRATION CULTIVATION
   - Track the correlation between estimated and actual outcomes
   - Alert when estimates are chronically miscalibrated
   - Celebrate moments of genuine probabilistic wisdom

Architecture:
- record_ev(decision, type, probability, payoff, actual_outcome): Log EV
- get_ev_stats(): Get EV pattern analysis
- get_ev_suggestion(capacity, context): Get suggestion
- get_ev_score(): Calculate overall EV health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "expected_value_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EV_LOG = DATA_DIR / "evs.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EVEntry:
    """A tracked expected value assessment."""
    entry_id: str = ""
    decision: str = ""  # what was decided
    ev_type: str = ""  # financial, career, relational, health, creative
    probability: float = 0.0  # 0-1 estimated probability
    payoff: float = 0.0  # 0-1 estimated payoff
    actual_outcome: float = 0.0  # 0-1 actual outcome
    emotion_influence: float = 0.0  # 0-1 how much emotion influenced estimate
    calibration: float = 0.0  # 0-1 accuracy of estimate
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ExpectedValueCoach:
    """
    Intelligent expected value coach with calibration detection and probabilistic wisdom cultivation.
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
            "avg_calibration": 0.0,
            "avg_emotion_influence": 0.0,
            "miscalibration_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_ev(self, decision: str = "", ev_type: str = "", probability: float = 0.0, payoff: float = 0.0, actual_outcome: float = 0.0, emotion_influence: float = 0.0, calibration: float = 0.0, notes: str = "") -> EVEntry:
        """Record an expected value assessment."""
        entry_id = f"evc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EVEntry(
            entry_id=entry_id,
            decision=decision or "unspecified",
            ev_type=ev_type or "career",
            probability=probability,
            payoff=payoff,
            actual_outcome=actual_outcome,
            emotion_influence=emotion_influence,
            calibration=calibration,
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

    def get_ev_stats(self) -> Dict[str, Any]:
        """Get EV pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "prob_sum": 0.0, "outcome_sum": 0.0, "calibration_sum": 0.0})
        for e in self._entries:
            by_type[e.ev_type]["count"] += 1
            by_type[e.ev_type]["prob_sum"] += e.probability
            by_type[e.ev_type]["outcome_sum"] += e.actual_outcome
            by_type[e.ev_type]["calibration_sum"] += e.calibration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_probability": round(data["prob_sum"] / count, 2),
                "avg_outcome": round(data["outcome_sum"] / count, 2),
                "avg_calibration": round(data["calibration_sum"] / count, 2),
            }

        # Emotion influence analysis
        high_emo = [e for e in self._entries if e.emotion_influence > 0.7]
        low_emo = [e for e in self._entries if e.emotion_influence < 0.4]
        if high_emo and low_emo:
            high_emo_cal = sum(e.calibration for e in high_emo) / len(high_emo)
            low_emo_cal = sum(e.calibration for e in low_emo) / len(low_emo)
            high_emo_out = sum(e.actual_outcome for e in high_emo) / len(high_emo)
            low_emo_out = sum(e.actual_outcome for e in low_emo) / len(low_emo)
        else:
            high_emo_cal = 0
            low_emo_cal = 0
            high_emo_out = 0
            low_emo_out = 0

        # Calibration analysis
        high_cal = [e for e in self._entries if e.calibration > 0.7]
        low_cal = [e for e in self._entries if e.calibration < 0.4]
        if high_cal and low_cal:
            high_cal_out = sum(e.actual_outcome for e in high_cal) / len(high_cal)
            low_cal_out = sum(e.actual_outcome for e in low_cal) / len(low_cal)
        else:
            high_cal_out = 0
            low_cal_out = 0

        # Miscalibration risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cal = sum(e.calibration for e in recent) / len(recent)
            recent_emo = sum(e.emotion_influence for e in recent) / len(recent)
            miscalibration_risk = recent_cal < 0.4 and recent_emo > 0.6
        else:
            miscalibration_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "emotion_impact": {
                "high_emotion_calibration": round(high_emo_cal, 2),
                "low_emotion_calibration": round(low_emo_cal, 2),
                "high_emotion_outcome": round(high_emo_out, 2),
                "low_emotion_outcome": round(low_emo_out, 2),
            },
            "calibration_effect": {
                "high_calibration_outcome": round(high_cal_out, 2),
                "low_calibration_outcome": round(low_cal_out, 2),
            },
            "miscalibration_risk": miscalibration_risk,
            "avg_calibration": round(sum(e.calibration for e in self._entries) / len(self._entries), 2),
            "avg_emotion_influence": round(sum(e.emotion_influence for e in self._entries) / len(self._entries), 2),
        }

    def get_ev_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get EV suggestion."""
        suggestions = [
            "Expected value is probability times payoff. Most people overweight payoff and underweight probability. A 10% chance of $1000 is worth $100. Don't treat it like it's $1000. Don't treat it like it's $0. It's $100.",
            "Your gut feeling about probability is usually wrong. Humans are terrible at probability. We overestimate rare events. We underestimate common events. We confuse correlation with causation. Use data. Or at least be humble about your estimates.",
            "Separate the decision from the outcome. A good decision with a bad outcome is still a good decision. A bad decision with a good outcome is still a bad decision. Judge the process, not the result.",
            "The person who only considers the best case is delusional. The person who only considers the worst case is paralyzed. Consider both. Weight them by probability. That's expected value.",
            "Small probabilities of large payoffs are seductive. The lottery. The startup. The affair. They all look like good bets because the payoff is so big. But multiply by the probability. It's usually terrible.",
            "Don't throw good money after bad. Sunk costs are sunk. The fact that you invested time or money doesn't make a bad bet good. Evaluate from now. Not from the past.",
            "The base rate matters. If 90% of startups fail, your startup probably fails too. You're not special. Not in the ways that matter. Base rates are the best predictor of individual outcomes.",
            "Consider what you're giving up. Every bet has an opportunity cost. The money you spend on lottery tickets could be invested. The time you spend on a bad relationship could be spent on yourself. Account for the alternative.",
            "Track your predictions. Write them down. Compare them to reality. Most people think they're good at predicting. They're not. Data is the only way to calibrate. Be honest with yourself.",
            "Expected value is not everything. Some things are worth doing even if the EV is negative. Relationships. Art. Adventure. But know when you're making an EV-negative bet for non-EV reasons. Don't confuse it with good strategy."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One honest probability estimate. One moment separating emotion from math. One question: what's the actual chance? That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. An EV calculation for one decision. A prediction logged. A calibration check. Medium coaching."
        else:
            capacity_note = "Good capacity. Deep probabilistic work. A systematic calibration of your judgment. You have the strength to see the odds clearly."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Expected value is the most important concept in decision-making that most people ignore. It's simple: probability times payoff. But humans are terrible at both. We overestimate probabilities when we want something. We underestimate them when we fear something. We overweight payoffs that are emotionally salient. We underweight payoffs that are distant or abstract. And we ignore base rates. The result is chronic miscalibration. We make bad bets and think we're making good ones. We make good bets and abandon them because the first outcome was bad. The work of expected value coaching is about calibrating your judgment. About separating emotion from math. About recognizing that a good decision and a good outcome are not the same thing. And about building the humility to say: I don't know the probability. But here's my best guess. And here's what I'll do if I'm wrong."
        }

    def get_ev_score(self) -> int:
        """Calculate overall EV health (0-100)."""
        if not self._entries:
            return 25

        avg_cal = sum(e.calibration for e in self._entries) / len(self._entries)
        avg_emo = sum(e.emotion_influence for e in self._entries) / len(self._entries)
        avg_prob = sum(e.probability for e in self._entries) / len(self._entries)
        avg_payoff = sum(e.payoff for e in self._entries) / len(self._entries)
        avg_out = sum(e.actual_outcome for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cal = sum(e.calibration for e in recent) / len(recent)
            recent_emo = sum(e.emotion_influence for e in recent) / len(recent)
        else:
            recent_cal = 0
            recent_emo = 0

        # Miscalibration penalty
        misc_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cal_30 = sum(e.calibration for e in last_30) / len(last_30)
            recent_emo_30 = sum(e.emotion_influence for e in last_30) / len(last_30)
            if recent_cal_30 < 0.4 and recent_emo_30 > 0.6:
                misc_penalty = 15

        # Type variety
        unique_types = len(set(e.ev_type for e in self._entries))

        score = (avg_cal * 30) + (avg_prob * 10) + (avg_payoff * 10) + (avg_out * 15) + (recent_cal * 10) + (recent_cal * 5) + (unique_types * 2) - (avg_emo * 15) - misc_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_calibration"] = round(sum(e.calibration for e in self._entries) / len(self._entries), 2)
            self._stats["avg_emotion_influence"] = round(sum(e.emotion_influence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cal = sum(e.calibration for e in recent) / len(recent)
                recent_emo = sum(e.emotion_influence for e in recent) / len(recent)
                self._stats["miscalibration_risk"] = recent_cal < 0.4 and recent_emo > 0.6
            else:
                self._stats["miscalibration_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.expected_value_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.expected_value_coach")

    def _log_entry(self, entry: EVEntry):
        try:
            with open(EV_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "decision": entry.decision,
                    "ev_type": entry.ev_type,
                    "probability": entry.probability,
                    "actual_outcome": entry.actual_outcome,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.expected_value_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_evc_instance: Optional[ExpectedValueCoach] = None
_evc_lock = threading.Lock()


def get_expected_value_coach() -> ExpectedValueCoach:
    global _evc_instance
    with _evc_lock:
        if _evc_instance is None:
            _evc_instance = ExpectedValueCoach()
        return _evc_instance
