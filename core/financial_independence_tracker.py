"""
LOVE Financial Independence Tracker — Freedom Intelligence (Modern AI Pattern)

Most people never reach freedom because they never track it. This tracker:

1. FI TRACKING
   - Record financial independence metrics and their characteristics
   - Track FI types (lean, regular, fat, coast, barista)
   - Log progress and their effects on life choices

2. PATTERN ANALYSIS
   - Identify the user's FI profile (dreamer, planner, executor, achiever)
   - Find behaviors that accelerate FI trajectory
   - Detect lifestyle sabotage patterns

3. FI BUILDING
   - Suggest actions matched to current FI stage and timeline
   - Provide withdrawal rate and safe spending frameworks
   - Recommendation milestone practices

4. FREEDOM CULTIVATION
   - Track the correlation between savings rate and FI date
   - Alert when spending is delaying freedom
   - Celebrate milestone achievements

Architecture:
- record_snapshot(net_worth, expenses, income, fi_number, stage): Log snapshot
- get_fi_stats(): Get FI pattern analysis
- get_fi_action(stage, timeline, gap): Get action
- get_fi_score(): Calculate overall FI health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "financial_independence_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FI_LOG = DATA_DIR / "snapshots.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class FIEntry:
    """A tracked FI entry."""
    entry_id: str = ""
    net_worth: float = 0.0
    monthly_expenses: float = 0.0
    monthly_income: float = 0.0
    fi_number: float = 0.0  # 25x annual expenses
    fi_progress: float = 0.0  # 0-1, % to FI
    fi_type: str = ""  # lean, regular, fat, coast, barista
    stage: str = ""  # discovery, accumulation, coasting, freedom
    years_to_fi: float = 0.0
    savings_rate: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class FinancialIndependenceTracker:
    """
    Intelligent FI tracker with milestone detection and trajectory optimization.
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
            "avg_progress": 0.0,
            "avg_years_to_fi": 0.0,
            "sabotage_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_snapshot(self, net_worth: float = 0.0, monthly_expenses: float = 0.0, monthly_income: float = 0.0, fi_number: float = 0.0, fi_progress: float = 0.0, fi_type: str = "", stage: str = "", years_to_fi: float = 0.0, savings_rate: float = 0.0, notes: str = "") -> FIEntry:
        """Record an FI entry."""
        entry_id = f"fi_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = FIEntry(
            entry_id=entry_id,
            net_worth=net_worth,
            monthly_expenses=monthly_expenses,
            monthly_income=monthly_income,
            fi_number=fi_number,
            fi_progress=fi_progress,
            fi_type=fi_type or "regular",
            stage=stage or "accumulation",
            years_to_fi=years_to_fi,
            savings_rate=savings_rate,
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

    def get_fi_stats(self) -> Dict[str, Any]:
        """Get FI pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Stage analysis
        by_stage = defaultdict(lambda: {"count": 0, "progress_sum": 0.0, "years_sum": 0.0, "savings_sum": 0.0})
        for e in self._entries:
            by_stage[e.stage]["count"] += 1
            by_stage[e.stage]["progress_sum"] += e.fi_progress
            by_stage[e.stage]["years_sum"] += e.years_to_fi
            by_stage[e.stage]["savings_sum"] += e.savings_rate

        stage_stats = {}
        for s, data in by_stage.items():
            count = data["count"]
            stage_stats[s] = {
                "count": count,
                "avg_progress": round(data["progress_sum"] / count, 2),
                "avg_years_to_fi": round(data["years_sum"] / count, 1),
                "avg_savings_rate": round(data["savings_sum"] / count, 2),
            }

        # FI type analysis
        by_type = defaultdict(lambda: {"count": 0, "progress_sum": 0.0, "nw_sum": 0.0})
        for e in self._entries:
            by_type[e.fi_type]["count"] += 1
            by_type[e.fi_type]["progress_sum"] += e.fi_progress
            by_type[e.fi_type]["nw_sum"] += e.net_worth

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_progress": round(data["progress_sum"] / count, 2),
                "avg_net_worth": round(data["nw_sum"] / count, 2),
            }

        # Savings rate impact
        high_savings = [e for e in self._entries if e.savings_rate > 0.4]
        low_savings = [e for e in self._entries if e.savings_rate < 0.2]
        if high_savings and low_savings:
            high_savings_years = sum(e.years_to_fi for e in high_savings) / len(high_savings)
            low_savings_years = sum(e.years_to_fi for e in low_savings) / len(low_savings)
            high_savings_progress = sum(e.fi_progress for e in high_savings) / len(high_savings)
            low_savings_progress = sum(e.fi_progress for e in low_savings) / len(low_savings)
        else:
            high_savings_years = 0
            low_savings_years = 0
            high_savings_progress = 0
            low_savings_progress = 0

        # Expense analysis
        high_expenses = [e for e in self._entries if e.monthly_expenses > e.monthly_income * 0.9]
        if high_expenses:
            expense_sabotage = True
        else:
            expense_sabotage = False

        # Progress velocity
        if len(self._entries) > 5:
            sorted_entries = sorted(self._entries, key=lambda e: e.timestamp)
            first_half = sorted_entries[:len(sorted_entries)//2]
            second_half = sorted_entries[len(sorted_entries)//2:]
            if first_half and second_half:
                first_progress = sum(e.fi_progress for e in first_half) / len(first_half)
                second_progress = sum(e.fi_progress for e in second_half) / len(second_half)
                progress_velocity = second_progress - first_progress
            else:
                progress_velocity = 0
        else:
            progress_velocity = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_progress = sum(e.fi_progress for e in recent) / len(recent)
            recent_years = sum(e.years_to_fi for e in recent) / len(recent)
            recent_savings = sum(e.savings_rate for e in recent) / len(recent)
            recent_expenses = sum(e.monthly_expenses for e in recent) / len(recent)
        else:
            recent_progress = 0
            recent_years = 0
            recent_savings = 0
            recent_expenses = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_progress = sum(e.fi_progress for e in older) / len(older)
            older_years = sum(e.years_to_fi for e in older) / len(older)
            progress_trend = recent_progress - older_progress
            years_trend = recent_years - older_years
        else:
            progress_trend = 0
            years_trend = 0

        return {
            "total_entries": len(self._entries),
            "stage_stats": stage_stats,
            "type_stats": type_stats,
            "savings_impact": {
                "high_savings_years_to_fi": round(high_savings_years, 1),
                "low_savings_years_to_fi": round(low_savings_years, 1),
                "high_savings_progress": round(high_savings_progress, 2),
                "low_savings_progress": round(low_savings_progress, 2),
            },
            "expense_sabotage": expense_sabotage,
            "progress_velocity": round(progress_velocity, 3),
            "avg_progress": round(sum(e.fi_progress for e in self._entries) / len(self._entries), 2),
            "avg_years_to_fi": round(sum(e.years_to_fi for e in self._entries) / len(self._entries), 1),
            "avg_savings_rate": round(sum(e.savings_rate for e in self._entries) / len(self._entries), 2),
            "progress_trend": round(progress_trend, 3),
            "years_trend": round(years_trend, 1),
            "recent_progress": round(recent_progress, 2),
            "recent_expenses": round(recent_expenses, 2),
        }

    def get_fi_action(self, stage: str = "", timeline: float = 10, gap: float = 0.5) -> Dict[str, Any]:
        """Get action."""
        actions = {
            "discovery": [
                "Calculate your FI number. 25x annual expenses. That's the target. Now you know what you're aiming for.",
                "Track spending for one month. Every dollar. You can't optimize what you don't measure.",
                "Read one book on FI. 'The Simple Path to Wealth.' 'Your Money or Your Life.' Knowledge is the first investment.",
            ],
            "accumulation": [
                "Maximize savings rate. Every 5% increase cuts years off your timeline. Find the waste. Cut it.",
                "Invest automatically. Before you see it. Before you spend it. Pay your future self first.",
                "Increase income. Negotiate salary. Side hustle. Skills. Income is the accelerator.",
            ],
            "coasting": [
                "You've built the base. Now you can relax a little. Coasting means your investments do the work.",
                "Don't quit yet. Coasting to FI is slower than sprinting. But it's sustainable.",
                "Use this phase to test your post-FI life. Sabbatical. Part-time. Trial run.",
            ],
            "freedom": [
                "You've arrived. Now what? Freedom without purpose is just unemployment. Find your next chapter.",
                "Withdraw conservatively. 3.5-4% annually. In bad years, spend less. In good years, spend more.",
                "Give back. Mentorship. Philanthropy. Teaching. You've earned the freedom. Now earn the meaning.",
            ],
            "general": [
                "FI is not about retiring early. It's about having options. The freedom to choose work you love.",
                "The math is simple. The behavior is hard. Most people fail at the behavior, not the math.",
                "Every dollar you don't spend is a dollar of freedom. Every dollar you invest is a soldier working for you.",
            ],
        }

        selected = actions.get(stage, actions["general"])

        if gap > 0.7:
            gap_note = "Large gap. This will take time. Don't despair. Small actions compound. Start today."
        elif gap > 0.3:
            gap_note = "Moderate gap. You're making progress. Keep the momentum. Don't let lifestyle inflation steal it."
        else:
            gap_note = "Small gap. You're close. Push through. The last miles are the hardest. Then the view changes."

        return {
            "stage": stage or "general",
            "timeline": timeline,
            "gap": gap,
            "action": random.choice(selected),
            "gap_note": gap_note,
            "principle": "Most people work until they're 65 because they never questioned the default. Financial independence is the recognition that the default is optional. You can choose a different path. It requires saving more, spending less, and investing wisely. But mostly, it requires wanting it badly enough to do the boring work for years. The boring work is the price of freedom. And it's worth every penny.",
        }

    def get_fi_score(self) -> int:
        """Calculate overall FI health (0-100)."""
        if not self._entries:
            return 25

        # Progress and low years to FI
        avg_progress = sum(e.fi_progress for e in self._entries) / len(self._entries)
        avg_years = sum(e.years_to_fi for e in self._entries) / len(self._entries)
        years_score = max(0, 20 - avg_years)

        # High savings rate
        avg_savings = sum(e.savings_rate for e in self._entries) / len(self._entries)

        # Low expenses relative to income
        expense_ratios = [e.monthly_expenses / max(1, e.monthly_income) for e in self._entries if e.monthly_income > 0]
        avg_expense_ratio = sum(expense_ratios) / len(expense_ratios) if expense_ratios else 1

        # Stage variety
        unique_stages = len(set(e.stage for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_progress = sum(e.fi_progress for e in recent) / len(recent)
            recent_years = sum(e.years_to_fi for e in recent) / len(recent)
            recent_savings = sum(e.savings_rate for e in recent) / len(recent)
        else:
            recent_progress = 0
            recent_years = 0
            recent_savings = 0

        # Expense sabotage penalty
        sabotage_penalty = 0
        high_expenses = [e for e in self._entries if e.monthly_expenses > e.monthly_income * 0.9]
        if high_expenses:
            sabotage_penalty = 15

        score = (avg_progress * 40) + (years_score) + (avg_savings * 30) + ((1 - avg_expense_ratio) * 15) + (unique_stages * 2) + (recent_progress * 20) + (recent_savings * 10) - sabotage_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_progress"] = round(sum(e.fi_progress for e in self._entries) / len(self._entries), 2)
            self._stats["avg_years_to_fi"] = round(sum(e.years_to_fi for e in self._entries) / len(self._entries), 1)

            high_expenses = [e for e in self._entries if e.monthly_expenses > e.monthly_income * 0.9]
            self._stats["sabotage_risk"] = len(high_expenses) > 0

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

    def _log_entry(self, entry: FIEntry):
        try:
            with open(FI_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "net_worth": entry.net_worth,
                    "monthly_expenses": entry.monthly_expenses,
                    "monthly_income": entry.monthly_income,
                    "fi_number": entry.fi_number,
                    "fi_progress": entry.fi_progress,
                    "fi_type": entry.fi_type,
                    "stage": entry.stage,
                    "years_to_fi": entry.years_to_fi,
                    "savings_rate": entry.savings_rate,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_fit_instance: Optional[FinancialIndependenceTracker] = None
_fit_lock = threading.Lock()


def get_financial_independence_tracker() -> FinancialIndependenceTracker:
    global _fit_instance
    with _fit_lock:
        if _fit_instance is None:
            _fit_instance = FinancialIndependenceTracker()
        return _fit_instance
