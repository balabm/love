"""
LOVE Risk Intelligence Trainer — Calculated Risk Intelligence (Modern AI Pattern)

Most risk is either avoided blindly or taken recklessly. This trainer:

1. RISK TRACKING
   - Record risk assessments and their characteristics
   - Track risk types (career, relational, financial, health, creative)
   - Log risk outcomes and their quality

2. PATTERN ANALYSIS
   - Identify the user's risk profile (cautious, impulsive, calculated, avoidant)
   - Find risk assessment strategies that yield good outcomes
   - Detect risk biases (loss aversion, overconfidence, availability)

3. RISK TRAINING
   - Suggest risk calibration exercises
   - Provide expected value calculations
   - Recommendation regret-minimization frameworks

4. INTELLIGENCE CULTIVATION
   - Track the correlation between risk quality and life satisfaction
   - Alert when risk posture is becoming maladaptive
   - Celebrate well-calculated risks

Architecture:
- record_risk(decision, risk_level, assessment, outcome): Log risk
- get_risk_stats(): Get risk pattern analysis
- get_risk_suggestion(bias, domain): Get suggestion
- get_risk_score(): Calculate overall risk health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "risk_intelligence_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RISK_LOG = DATA_DIR / "risks.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RiskEntry:
    """A tracked risk entry."""
    entry_id: str = ""
    decision: str = ""
    risk_type: str = ""  # career, relational, financial, health, creative, reputational
    risk_level: float = 0.5  # 0-1
    assessment_quality: float = 0.5  # 0-1, how well they assessed
    expected_value: float = 0.0
    actual_value: float = 0.0
    outcome: str = ""
    outcome_quality: float = 0.5  # 0-1
    regret: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RiskIntelligenceTrainer:
    """
    Intelligent risk trainer with bias detection and calibration exercises.
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
            "avg_assessment": 0.0,
            "avg_regret": 0.0,
            "dominant_type": "",
            "bias_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_risk(self, decision: str = "", risk_type: str = "", risk_level: float = 0.5, assessment_quality: float = 0.5, expected_value: float = 0.0, actual_value: float = 0.0, outcome: str = "", outcome_quality: float = 0.5, regret: float = 0.5, notes: str = "") -> RiskEntry:
        """Record a risk entry."""
        entry_id = f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RiskEntry(
            entry_id=entry_id,
            decision=decision or "unspecified",
            risk_type=risk_type or "career",
            risk_level=risk_level,
            assessment_quality=assessment_quality,
            expected_value=expected_value,
            actual_value=actual_value,
            outcome=outcome,
            outcome_quality=outcome_quality,
            regret=regret,
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

    def get_risk_stats(self) -> Dict[str, Any]:
        """Get risk pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "risk_sum": 0.0, "assessment_sum": 0.0, "outcome_sum": 0.0, "regret_sum": 0.0})
        for e in self._entries:
            by_type[e.risk_type]["count"] += 1
            by_type[e.risk_type]["risk_sum"] += e.risk_level
            by_type[e.risk_type]["assessment_sum"] += e.assessment_quality
            by_type[e.risk_type]["outcome_sum"] += e.outcome_quality
            by_type[e.risk_type]["regret_sum"] += e.regret

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_risk": round(data["risk_sum"] / count, 2),
                "avg_assessment": round(data["assessment_sum"] / count, 2),
                "avg_outcome": round(data["outcome_sum"] / count, 2),
                "avg_regret": round(data["regret_sum"] / count, 2),
            }

        dominant_type = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Assessment accuracy
        if self._entries:
            ev_errors = [abs(e.expected_value - e.actual_value) for e in self._entries]
            avg_ev_error = sum(ev_errors) / len(ev_errors)
        else:
            avg_ev_error = 0

        # Bias detection
        losses = [e for e in self._entries if e.outcome_quality < 0.4]
        wins = [e for e in self._entries if e.outcome_quality > 0.7]
        
        if losses and wins:
            loss_risk = sum(e.risk_level for e in losses) / len(losses)
            win_risk = sum(e.risk_level for e in wins) / len(wins)
            loss_aversion_bias = loss_risk < win_risk * 0.7
            overconfidence_bias = win_risk > 0.8 and len(wins) < len(losses)
        else:
            loss_aversion_bias = False
            overconfidence_bias = False

        # Regret analysis
        high_regret = [e for e in self._entries if e.regret > 0.7]
        if high_regret:
            high_regret_risk = sum(e.risk_level for e in high_regret) / len(high_regret)
            missed_opportunity = sum(1 for e in high_regret if e.actual_value < 0) / len(high_regret)
        else:
            high_regret_risk = 0
            missed_opportunity = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_assessment = sum(e.assessment_quality for e in recent) / len(recent)
            recent_regret = sum(e.regret for e in recent) / len(recent)
            recent_outcome = sum(e.outcome_quality for e in recent) / len(recent)
        else:
            recent_assessment = 0
            recent_regret = 0
            recent_outcome = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_assessment = sum(e.assessment_quality for e in older) / len(older)
            older_regret = sum(e.regret for e in older) / len(older)
            assessment_trend = recent_assessment - older_assessment
            regret_trend = recent_regret - older_regret
        else:
            assessment_trend = 0
            regret_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "dominant_type": dominant_type[0],
            "avg_ev_error": round(avg_ev_error, 2),
            "bias_analysis": {
                "loss_aversion": loss_aversion_bias,
                "overconfidence": overconfidence_bias,
            },
            "regret_analysis": {
                "high_regret_risk": round(high_regret_risk, 2),
                "missed_opportunity_rate": round(missed_opportunity, 2),
            },
            "avg_assessment": round(sum(e.assessment_quality for e in self._entries) / len(self._entries), 2),
            "avg_regret": round(sum(e.regret for e in self._entries) / len(self._entries), 2),
            "avg_outcome": round(sum(e.outcome_quality for e in self._entries) / len(self._entries), 2),
            "assessment_trend": round(assessment_trend, 2),
            "regret_trend": round(regret_trend, 2),
            "recent_outcome": round(recent_outcome, 2),
        }

    def get_risk_suggestion(self, bias: str = "", domain: str = "") -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "loss_aversion": [
                "Flip the frame. Instead of 'what do I lose?', ask 'what do I gain?'",
                "Set a loss budget. Decide in advance what you can afford to lose. Then act.",
                "Most losses are reversible. Most missed opportunities are not.",
            ],
            "overconfidence": [
                "Find the smartest person who disagrees with you. Understand their argument fully.",
                "Ask: 'What would make me wrong?' If nothing, you're overconfident.",
                "Cut your probability estimates in half. Still worth it? Then proceed.",
            ],
            "availability": [
                "Seek base rates. What's the statistical reality, not the memorable story?",
                "The recent past is not the future. Recency bias distorts risk assessment.",
                "Ask: 'Has this happened to people I know?' Personal anecdotes are not data.",
            ],
            "status_quo": [
                "Inaction is also a choice. And it has consequences. Evaluate it explicitly.",
                "The default is not safe. It's just familiar. Familiarity is not safety.",
                "Ask: 'If I were starting fresh, would I choose my current path?'",
            ],
            "general": [
                "Expected value: Probability of success x Value of success - Probability of failure x Cost of failure. Do the math.",
                "Regret minimization: Project yourself to age 80. Which decision would you regret less?",
                "The only bad risks are the unexamined ones. Examine. Then choose.",
            ],
        }

        selected = suggestions.get(bias, suggestions["general"])

        if bias == "loss_aversion":
            bias_note = "You're overweighting losses. This is automatic. Override it by explicitly valuing gains."
        elif bias == "overconfidence":
            bias_note = "You're underweighting failure. This is dangerous. Find the person who sees what you don't."
        elif bias == "availability":
            bias_note = "You're using vivid examples instead of base rates. Look up the statistics."
        elif bias == "status_quo":
            bias_note = "You're privileging the current state. Inaction is not neutral. It has costs."
        else:
            bias_note = "Good risk intelligence requires both analysis and intuition. Use both."

        return {
            "bias": bias or "none",
            "domain": domain or "general",
            "suggestion": random.choice(selected),
            "bias_note": bias_note,
            "principle": "Risk is not the enemy. Uncalibrated risk is. The goal is not to eliminate risk. It's to take risks that are worth taking, with eyes open, and to learn from every outcome. That's risk intelligence.",
        }

    def get_risk_score(self) -> int:
        """Calculate overall risk health (0-100)."""
        if not self._entries:
            return 35

        # Assessment quality
        avg_assessment = sum(e.assessment_quality for e in self._entries) / len(self._entries)

        # Low regret
        avg_regret = sum(e.regret for e in self._entries) / len(self._entries)

        # Outcome quality
        avg_outcome = sum(e.outcome_quality for e in self._entries) / len(self._entries)

        # Expected value accuracy
        if self._entries:
            ev_errors = [abs(e.expected_value - e.actual_value) for e in self._entries]
            avg_ev_error = sum(ev_errors) / len(ev_errors)
            ev_accuracy = max(0, 1 - avg_ev_error)
        else:
            ev_accuracy = 0

        # Type variety
        unique_types = len(set(e.risk_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_assessment = sum(e.assessment_quality for e in recent) / len(recent)
            recent_regret = sum(e.regret for e in recent) / len(recent)
            recent_outcome = sum(e.outcome_quality for e in recent) / len(recent)
        else:
            recent_assessment = 0
            recent_regret = 0
            recent_outcome = 0

        # Bias penalties
        losses = [e for e in self._entries if e.outcome_quality < 0.4]
        wins = [e for e in self._entries if e.outcome_quality > 0.7]
        bias_penalty = 0
        if losses and wins:
            loss_risk = sum(e.risk_level for e in losses) / len(losses)
            win_risk = sum(e.risk_level for e in wins) / len(wins)
            if loss_risk < win_risk * 0.7:
                bias_penalty += 5
            if win_risk > 0.8 and len(wins) < len(losses):
                bias_penalty += 5

        score = (avg_assessment * 25) + ((1 - avg_regret) * 20) + (avg_outcome * 20) + (ev_accuracy * 10) + (unique_types * 2) + (recent_assessment * 10) + ((1 - recent_regret) * 10) + (recent_outcome * 5) - bias_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_assessment"] = round(sum(e.assessment_quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_regret"] = round(sum(e.regret for e in self._entries) / len(self._entries), 2)

            by_type = defaultdict(int)
            for e in self._entries:
                by_type[e.risk_type] += 1
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1])
                self._stats["dominant_type"] = dominant[0]

            losses = [e for e in self._entries if e.outcome_quality < 0.4]
            wins = [e for e in self._entries if e.outcome_quality > 0.7]
            if losses and wins:
                loss_risk = sum(e.risk_level for e in losses) / len(losses)
                win_risk = sum(e.risk_level for e in wins) / len(wins)
                self._stats["bias_risk"] = loss_risk < win_risk * 0.7 or (win_risk > 0.8 and len(wins) < len(losses))

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.risk_intelligence_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.risk_intelligence_trainer")

    def _log_entry(self, entry: RiskEntry):
        try:
            with open(RISK_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "decision": entry.decision,
                    "risk_type": entry.risk_type,
                    "risk_level": entry.risk_level,
                    "assessment_quality": entry.assessment_quality,
                    "expected_value": entry.expected_value,
                    "actual_value": entry.actual_value,
                    "outcome": entry.outcome,
                    "outcome_quality": entry.outcome_quality,
                    "regret": entry.regret,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.risk_intelligence_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rit_instance: Optional[RiskIntelligenceTrainer] = None
_rit_lock = threading.Lock()


def get_risk_intelligence_trainer() -> RiskIntelligenceTrainer:
    global _rit_instance
    with _rit_lock:
        if _rit_instance is None:
            _rit_instance = RiskIntelligenceTrainer()
        return _rit_instance
