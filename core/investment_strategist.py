"""
LOVE Investment Strategist — Capital Intelligence (Modern AI Pattern)

Most investment failures come from emotion, not analysis. This strategist:

1. INVESTMENT TRACKING
   - Record investment decisions and their characteristics
   - Track investment types (equity, fixed income, real estate, alternatives, cash)
   - Log outcomes and their effects on portfolio performance

2. PATTERN ANALYSIS
   - Identify the user's investment profile (speculator, indexer, value, growth, passive)
   - Find decision patterns that create consistent returns
   - Detect emotional trading and its costs

3. STRATEGY BUILDING
   - Suggest portfolio adjustments matched to goals and risk tolerance
   - Provide rebalancing and tax-loss harvesting frameworks
   - Recommendation diversification practices

4. WEALTH CULTIVATION
   - Track the correlation between discipline and returns
   - Alert when behavior is diverging from strategy
   - Celebrate moments of patient capital deployment

Architecture:
- record_decision(asset, type, amount, rationale, outcome): Log decision
- get_investment_stats(): Get investment pattern analysis
- get_portfolio_suggestion(goal, horizon, risk): Get suggestion
- get_investment_score(): Calculate overall investment health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "investment_strategist"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INVESTMENT_LOG = DATA_DIR / "decisions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class InvestmentEntry:
    """A tracked investment entry."""
    entry_id: str = ""
    asset: str = ""  # what was invested in
    investment_type: str = ""  # equity, fixed_income, real_estate, alternatives, cash
    amount: float = 0.0
    rationale: str = ""  # why
    emotion_level: float = 0.0  # 0-1, how emotional was the decision
    expected_return: float = 0.0  # annual expected
    actual_return: float = 0.0  # actual return
    holding_period: float = 0.0  # days
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class InvestmentStrategist:
    """
    Intelligent investment strategist with emotional trading detection and discipline tracking.
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
            "avg_return": 0.0,
            "avg_emotion": 0.0,
            "emotional_trading_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_decision(self, asset: str = "", investment_type: str = "", amount: float = 0.0, rationale: str = "", emotion_level: float = 0.0, expected_return: float = 0.0, actual_return: float = 0.0, holding_period: float = 0.0, notes: str = "") -> InvestmentEntry:
        """Record an investment entry."""
        entry_id = f"inv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = InvestmentEntry(
            entry_id=entry_id,
            asset=asset or "unspecified",
            investment_type=investment_type or "equity",
            amount=amount,
            rationale=rationale,
            emotion_level=emotion_level,
            expected_return=expected_return,
            actual_return=actual_return,
            holding_period=holding_period,
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

    def get_investment_stats(self) -> Dict[str, Any]:
        """Get investment pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "return_sum": 0.0, "emotion_sum": 0.0, "hold_sum": 0.0})
        for e in self._entries:
            by_type[e.investment_type]["count"] += 1
            by_type[e.investment_type]["return_sum"] += e.actual_return
            by_type[e.investment_type]["emotion_sum"] += e.emotion_level
            by_type[e.investment_type]["hold_sum"] += e.holding_period

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_return": round(data["return_sum"] / count, 3),
                "avg_emotion": round(data["emotion_sum"] / count, 2),
                "avg_holding": round(data["hold_sum"] / count, 1),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_return"]) if type_stats else ("", {})

        # Emotion analysis
        high_emotion = [e for e in self._entries if e.emotion_level > 0.7]
        low_emotion = [e for e in self._entries if e.emotion_level < 0.3]
        if high_emotion and low_emotion:
            high_emotion_return = sum(e.actual_return for e in high_emotion) / len(high_emotion)
            low_emotion_return = sum(e.actual_return for e in low_emotion) / len(low_emotion)
            high_emotion_hold = sum(e.holding_period for e in high_emotion) / len(high_emotion)
            low_emotion_hold = sum(e.holding_period for e in low_emotion) / len(low_emotion)
        else:
            high_emotion_return = 0
            low_emotion_return = 0
            high_emotion_hold = 0
            low_emotion_hold = 0

        # Holding period analysis
        long_hold = [e for e in self._entries if e.holding_period > 365]
        short_hold = [e for e in self._entries if e.holding_period < 30]
        if long_hold and short_hold:
            long_return = sum(e.actual_return for e in long_hold) / len(long_hold)
            short_return = sum(e.actual_return for e in short_hold) / len(short_hold)
        else:
            long_return = 0
            short_return = 0

        # Expected vs actual
        expectations_met = sum(1 for e in self._entries if abs(e.actual_return - e.expected_return) < 0.05)
        expectation_accuracy = expectations_met / len(self._entries)

        # Emotional trading detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_emotion = sum(e.emotion_level for e in recent) / len(recent)
            recent_short_hold = sum(1 for e in recent if e.holding_period < 30)
            emotional_trading_risk = recent_emotion > 0.6 or recent_short_hold / len(recent) > 0.3
        else:
            emotional_trading_risk = False

        # Recent trend
        if recent:
            recent_return = sum(e.actual_return for e in recent) / len(recent)
            recent_hold = sum(e.holding_period for e in recent) / len(recent)
        else:
            recent_return = 0
            recent_hold = 0

        older = list(self._entries)[-30:] if len(self._entries) > 30 else []
        if older and recent:
            older_return = sum(e.actual_return for e in older) / len(older)
            return_trend = recent_return - older_return
        else:
            return_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "emotion_impact": {
                "high_emotion_return": round(high_emotion_return, 3),
                "low_emotion_return": round(low_emotion_return, 3),
                "high_emotion_holding": round(high_emotion_hold, 1),
                "low_emotion_holding": round(low_emotion_hold, 1),
            },
            "holding_impact": {
                "long_hold_return": round(long_return, 3),
                "short_hold_return": round(short_return, 3),
            },
            "expectation_accuracy": round(expectation_accuracy, 2),
            "emotional_trading_risk": emotional_trading_risk,
            "avg_return": round(sum(e.actual_return for e in self._entries) / len(self._entries), 3),
            "avg_emotion": round(sum(e.emotion_level for e in self._entries) / len(self._entries), 2),
            "return_trend": round(return_trend, 3),
            "recent_return": round(recent_return, 3),
            "recent_holding": round(recent_hold, 1),
        }

    def get_portfolio_suggestion(self, goal: str = "", horizon: float = 10, risk_tolerance: float = 0.5) -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "growth": [
                "Growth requires volatility tolerance. Index funds. Broad exposure. Rebalance annually. No stock picking.",
                "Time in market beats timing the market. Start now. Add monthly. Ignore the noise.",
                "Your greatest asset is time. At 7% return, money doubles every 10 years. Start the clock.",
            ],
            "preservation": [
                "Preservation means accepting lower returns. That's the deal. Safety has a cost.",
                "Ladder your bonds. Spread maturities. Protect against rate changes.",
                "Cash is not trash in volatile times. It's optionality. Hold some.",
            ],
            "income": [
                "Income investing is about yield sustainability, not yield maximization. Dividend aristocrats. Not junk bonds.",
                "Diversify income sources. REITs, bonds, dividend stocks, royalties. Multiple streams.",
                "Watch the payout ratio. If they're paying out more than they earn, the dividend will cut.",
            ],
            "speculation": [
                "Speculate with money you can lose entirely. Not your retirement. Not your emergency fund. Play money only.",
                "Set a stop loss before you buy. Emotion will prevent you from selling. Automate it.",
                "The best speculators are wrong 60% of the time. They win because their wins are 10x their losses.",
            ],
            "general": [
                "Diversify across asset classes, geographies, and time. Concentration builds wealth. Diversification preserves it.",
                "Costs matter. A 1% fee difference compounds to 26% less wealth over 30 years. Choose low-cost index funds.",
                "Rebalance annually. Sell high. Buy low. It's mechanical. Don't think. Just do.",
            ],
        }

        selected = suggestions.get(goal, suggestions["general"])

        if risk_tolerance < 0.3:
            risk_note = "Conservative. Protect capital first. Accept lower returns. Sleep well at night."
        elif risk_tolerance < 0.6:
            risk_note = "Moderate. Balanced portfolio. Some growth, some safety. The middle path."
        else:
            risk_note = "Aggressive. Volatility is your friend. Long horizon allows recovery. Stay the course."

        return {
            "goal": goal or "general",
            "horizon": horizon,
            "risk_tolerance": risk_tolerance,
            "suggestion": random.choice(selected),
            "risk_note": risk_note,
            "principle": "Most people lose money in markets because they do the opposite of what works. They buy when everyone is excited. They sell when everyone is terrified. They check prices daily. They trade on news. The winning strategy is boring: buy broadly, hold long, rebalance occasionally, ignore the noise. Boring is beautiful in investing.",
        }

    def get_investment_score(self) -> int:
        """Calculate overall investment health (0-100)."""
        if not self._entries:
            return 40

        # Returns and low emotion
        avg_return = sum(e.actual_return for e in self._entries) / len(self._entries)
        avg_emotion = sum(e.emotion_level for e in self._entries) / len(self._entries)

        # Holding period (longer is generally better for most investors)
        avg_hold = sum(e.holding_period for e in self._entries) / len(self._entries)
        hold_score = min(15, avg_hold / 30)

        # Expectation accuracy
        expectations_met = sum(1 for e in self._entries if abs(e.actual_return - e.expected_return) < 0.05)
        expectation_accuracy = expectations_met / len(self._entries)

        # Type variety (diversification)
        unique_types = len(set(e.investment_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_return = sum(e.actual_return for e in recent) / len(recent)
            recent_emotion = sum(e.emotion_level for e in recent) / len(recent)
            recent_hold = sum(e.holding_period for e in recent) / len(recent)
        else:
            recent_return = 0
            recent_emotion = 0
            recent_hold = 0

        # Emotional trading penalty
        emotional_penalty = 0
        if recent:
            if recent_emotion > 0.6:
                emotional_penalty = 10
            recent_short = sum(1 for e in recent if e.holding_period < 30)
            if recent_short / len(recent) > 0.3:
                emotional_penalty = max(emotional_penalty, 10)

        score = (avg_return * 200) + ((1 - avg_emotion) * 15) + hold_score + (expectation_accuracy * 10) + (unique_types * 2) + (recent_return * 100) + ((1 - recent_emotion) * 10) + (recent_hold / 30 * 5) - emotional_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_return"] = round(sum(e.actual_return for e in self._entries) / len(self._entries), 3)
            self._stats["avg_emotion"] = round(sum(e.emotion_level for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_emotion = sum(e.emotion_level for e in recent) / len(recent)
                recent_short = sum(1 for e in recent if e.holding_period < 30)
                self._stats["emotional_trading_risk"] = recent_emotion > 0.6 or recent_short / len(recent) > 0.3

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

    def _log_entry(self, entry: InvestmentEntry):
        try:
            with open(INVESTMENT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "asset": entry.asset,
                    "investment_type": entry.investment_type,
                    "amount": entry.amount,
                    "rationale": entry.rationale,
                    "emotion_level": entry.emotion_level,
                    "expected_return": entry.expected_return,
                    "actual_return": entry.actual_return,
                    "holding_period": entry.holding_period,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_is_instance: Optional[InvestmentStrategist] = None
_is_lock = threading.Lock()


def get_investment_strategist() -> InvestmentStrategist:
    global _is_instance
    with _is_lock:
        if _is_instance is None:
            _is_instance = InvestmentStrategist()
        return _is_instance
