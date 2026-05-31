"""
LOVE Wealth Builder — Accumulation Intelligence (Modern AI Pattern)

Most people never build wealth because they confuse income with wealth. This builder:

1. WEALTH TRACKING
   - Record wealth-building actions and their characteristics
   - Track wealth types (savings, investments, business, real estate, intellectual)
   - Log accumulation outcomes and their effects on net worth

2. PATTERN ANALYSIS
   - Identify the user's wealth profile (spender, saver, investor, builder, creator)
   - Find accumulation patterns that create compounding growth
   - Detect lifestyle inflation and its costs

3. WEALTH BUILDING
   - Suggest wealth-building actions matched to current stage
   - Provide savings rate and compounding frameworks
   - Recommendation asset allocation practices

4. ABUNDANCE CULTIVATION
   - Track the correlation between savings rate and wealth growth
   - Alert when spending is outpacing income growth
   - Celebrate moments of compounding acceleration

Architecture:
- record_action(action, wealth_type, amount, outcome): Log action
- get_wealth_stats(): Get wealth pattern analysis
- get_wealth_action(stage, income, savings_rate): Get action
- get_wealth_score(): Calculate overall wealth health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "wealth_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WEALTH_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WealthEntry:
    """A tracked wealth entry."""
    entry_id: str = ""
    action: str = ""  # what was done
    wealth_type: str = ""  # savings, investments, business, real_estate, intellectual
    amount: float = 0.0  # dollar amount
    income_before: float = 0.0  # monthly income
    savings_rate: float = 0.0  # percentage saved
    net_worth_change: float = 0.0  # percentage change
    lifestyle_inflation: bool = False  # did spending increase with income
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class WealthBuilder:
    """
    Intelligent wealth builder with lifestyle inflation detection and compounding optimization.
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
            "avg_savings_rate": 0.0,
            "avg_net_worth_change": 0.0,
            "lifestyle_inflation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", wealth_type: str = "", amount: float = 0.0, income_before: float = 0.0, savings_rate: float = 0.0, net_worth_change: float = 0.0, lifestyle_inflation: bool = False, notes: str = "") -> WealthEntry:
        """Record a wealth entry."""
        entry_id = f"wealth_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = WealthEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            wealth_type=wealth_type or "savings",
            amount=amount,
            income_before=income_before,
            savings_rate=savings_rate,
            net_worth_change=net_worth_change,
            lifestyle_inflation=lifestyle_inflation,
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

    def get_wealth_stats(self) -> Dict[str, Any]:
        """Get wealth pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "amount_sum": 0.0, "savings_sum": 0.0, "nw_sum": 0.0, "inflation_count": 0})
        for e in self._entries:
            by_type[e.wealth_type]["count"] += 1
            by_type[e.wealth_type]["amount_sum"] += e.amount
            by_type[e.wealth_type]["savings_sum"] += e.savings_rate
            by_type[e.wealth_type]["nw_sum"] += e.net_worth_change
            if e.lifestyle_inflation:
                by_type[e.wealth_type]["inflation_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_amount": round(data["amount_sum"] / count, 2),
                "avg_savings_rate": round(data["savings_sum"] / count, 2),
                "avg_net_worth_change": round(data["nw_sum"] / count, 3),
                "inflation_rate": round(data["inflation_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_net_worth_change"]) if type_stats else ("", {})

        # Savings rate analysis
        high_savings = [e for e in self._entries if e.savings_rate > 0.3]
        low_savings = [e for e in self._entries if e.savings_rate < 0.1]
        if high_savings and low_savings:
            high_savings_nw = sum(e.net_worth_change for e in high_savings) / len(high_savings)
            low_savings_nw = sum(e.net_worth_change for e in low_savings) / len(low_savings)
        else:
            high_savings_nw = 0
            low_savings_nw = 0

        # Lifestyle inflation detection
        inflation_entries = [e for e in self._entries if e.lifestyle_inflation]
        if inflation_entries:
            inflation_nw = sum(e.net_worth_change for e in inflation_entries) / len(inflation_entries)
            inflation_rate = len(inflation_entries) / len(self._entries)
            lifestyle_inflation_risk = inflation_rate > 0.3 or inflation_nw < 0
        else:
            lifestyle_inflation_risk = False

        # Income vs savings correlation
        if len(self._entries) > 5:
            avg_income = sum(e.income_before for e in self._entries) / len(self._entries)
            avg_savings = sum(e.savings_rate for e in self._entries) / len(self._entries)
            # Check if higher income leads to lower savings rate
            high_income = [e for e in self._entries if e.income_before > avg_income * 1.2]
            low_income = [e for e in self._entries if e.income_before < avg_income * 0.8]
            if high_income and low_income:
                high_income_savings = sum(e.savings_rate for e in high_income) / len(high_income)
                low_income_savings = sum(e.savings_rate for e in low_income) / len(low_income)
                income_savings_divergence = high_income_savings < low_income_savings
            else:
                income_savings_divergence = False
        else:
            income_savings_divergence = False

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_savings = sum(e.savings_rate for e in recent) / len(recent)
            recent_nw = sum(e.net_worth_change for e in recent) / len(recent)
            recent_inflation = sum(1 for e in recent if e.lifestyle_inflation) / len(recent)
        else:
            recent_savings = 0
            recent_nw = 0
            recent_inflation = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_savings = sum(e.savings_rate for e in older) / len(older)
            older_nw = sum(e.net_worth_change for e in older) / len(older)
            savings_trend = recent_savings - older_savings
            nw_trend = recent_nw - older_nw
        else:
            savings_trend = 0
            nw_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_wealth_type": best_type[0],
            "savings_impact": {
                "high_savings_nw_change": round(high_savings_nw, 3),
                "low_savings_nw_change": round(low_savings_nw, 3),
            },
            "lifestyle_inflation_risk": lifestyle_inflation_risk,
            "income_savings_divergence": income_savings_divergence,
            "avg_savings_rate": round(sum(e.savings_rate for e in self._entries) / len(self._entries), 2),
            "avg_net_worth_change": round(sum(e.net_worth_change for e in self._entries) / len(self._entries), 3),
            "savings_trend": round(savings_trend, 2),
            "nw_trend": round(nw_trend, 3),
            "recent_savings_rate": round(recent_savings, 2),
            "recent_inflation_rate": round(recent_inflation, 2),
        }

    def get_wealth_action(self, stage: str = "", income: float = 0.0, savings_rate: float = 0.0) -> Dict[str, Any]:
        """Get action."""
        actions = {
            "survival": [
                "Survival stage: every dollar counts. Track spending. Cut waste. Build a $1000 emergency fund first.",
                "Income is your only wealth tool right now. Protect your job. Build skills. Increase earning power.",
                "No investments yet. Just savings. Liquidity is more important than return when you're one paycheck away.",
            ],
            "stability": [
                "Stability stage: 3-6 months expenses in cash. Then start investing. Index funds. Broad market.",
                "Automate your savings. Pay yourself first. Before bills, before fun. You won't miss what you don't see.",
                "Increase income or decrease spending. Both work. Doing both accelerates everything.",
            ],
            "growth": [
                "Growth stage: max out tax-advantaged accounts. 401k. IRA. HSA. These are wealth-building machines.",
                "Diversify. Not just stocks. Real estate. Bonds. International. Don't bet everything on one asset class.",
                "Increase savings rate to 30%+. At this stage, every percentage point compounds massively.",
            ],
            "acceleration": [
                "Acceleration stage: you're compounding. Don't interrupt it. Stay the course through volatility.",
                "Consider entrepreneurial income. A side business can accelerate wealth faster than a salary.",
                "Optimize taxes. Tax-loss harvesting. Asset location. These matter more when the numbers are bigger.",
            ],
            "freedom": [
                "Freedom stage: wealth preservation matters more than growth. Capital protection is the game now.",
                "Generational wealth. Trusts. Estate planning. You're not building for you anymore. You're building for them.",
                "Philanthropy. Giving is the final stage of wealth. It completes the circle.",
            ],
            "general": [
                "Wealth = income x savings rate x time x return. You control the first two. Time passes regardless. Return is mostly luck.",
                "The best time to start was 10 years ago. The second best time is today. Start now.",
                "Wealth is not about having more. It's about needing less. The smaller your needs, the wealthier you are.",
            ],
        }

        selected = actions.get(stage, actions["general"])

        if savings_rate < 0.1:
            savings_note = "Critical: savings rate below 10%. This is an emergency. Find 10% today. Anywhere."
        elif savings_rate < 0.2:
            savings_note = "Savings rate below 20%. You're saving, but not enough. Push for 20%. That's the minimum for wealth building."
        elif savings_rate < 0.3:
            savings_note = "Savings rate 20-30%. Good foundation. Now optimize. Where can you find another 5%?"
        else:
            savings_note = "Savings rate above 30%. You're in the acceleration zone. Keep going. Compounding is your friend."

        return {
            "stage": stage or "general",
            "income": income,
            "savings_rate": savings_rate,
            "action": random.choice(selected),
            "savings_note": savings_note,
            "principle": "Most people think wealth comes from high income. It doesn't. It comes from the gap between income and spending. A person making $50k who saves $15k is wealthier than a person making $200k who saves $10k. The math is simple. The behavior is hard. Wealth is a series of small, boring decisions repeated for decades.",
        }

    def get_wealth_score(self) -> int:
        """Calculate overall wealth health (0-100)."""
        if not self._entries:
            return 30

        # Savings rate and net worth growth
        avg_savings = sum(e.savings_rate for e in self._entries) / len(self._entries)
        avg_nw = sum(e.net_worth_change for e in self._entries) / len(self._entries)

        # Low lifestyle inflation
        inflation_rate = sum(1 for e in self._entries if e.lifestyle_inflation) / len(self._entries)

        # Type variety
        unique_types = len(set(e.wealth_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_savings = sum(e.savings_rate for e in recent) / len(recent)
            recent_nw = sum(e.net_worth_change for e in recent) / len(recent)
            recent_inflation = sum(1 for e in recent if e.lifestyle_inflation) / len(recent)
        else:
            recent_savings = 0
            recent_nw = 0
            recent_inflation = 0

        # Lifestyle inflation penalty
        inflation_penalty = 0
        if recent:
            if recent_inflation > 0.3:
                inflation_penalty = 15

        # Income-savings divergence penalty
        divergence_penalty = 0
        if len(self._entries) > 5:
            avg_income = sum(e.income_before for e in self._entries) / len(self._entries)
            high_income = [e for e in self._entries if e.income_before > avg_income * 1.2]
            low_income = [e for e in self._entries if e.income_before < avg_income * 0.8]
            if high_income and low_income:
                high_income_savings = sum(e.savings_rate for e in high_income) / len(high_income)
                low_income_savings = sum(e.savings_rate for e in low_income) / len(low_income)
                if high_income_savings < low_income_savings:
                    divergence_penalty = 10

        score = (avg_savings * 100) + (avg_nw * 200) + ((1 - inflation_rate) * 15) + (unique_types * 2) + (recent_savings * 50) + (recent_nw * 100) - inflation_penalty - divergence_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_savings_rate"] = round(sum(e.savings_rate for e in self._entries) / len(self._entries), 2)
            self._stats["avg_net_worth_change"] = round(sum(e.net_worth_change for e in self._entries) / len(self._entries), 3)

            inflation_entries = [e for e in self._entries if e.lifestyle_inflation]
            if inflation_entries:
                inflation_nw = sum(e.net_worth_change for e in inflation_entries) / len(inflation_entries)
                inflation_rate = len(inflation_entries) / len(self._entries)
                self._stats["lifestyle_inflation_risk"] = inflation_rate > 0.3 or inflation_nw < 0

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

    def _log_entry(self, entry: WealthEntry):
        try:
            with open(WEALTH_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "wealth_type": entry.wealth_type,
                    "amount": entry.amount,
                    "income_before": entry.income_before,
                    "savings_rate": entry.savings_rate,
                    "net_worth_change": entry.net_worth_change,
                    "lifestyle_inflation": entry.lifestyle_inflation,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wb_instance: Optional[WealthBuilder] = None
_wb_lock = threading.Lock()


def get_wealth_builder() -> WealthBuilder:
    global _wb_instance
    with _wb_lock:
        if _wb_instance is None:
            _wb_instance = WealthBuilder()
        return _wb_instance
