"""
LOVE Finance Pattern Detector — Financial Intelligence (Modern AI Pattern)

Most finance tracking is reactive. This detector:

1. SPENDING PATTERN ANALYSIS
   - Categorize transactions automatically
   - Detect recurring vs one-time expenses
   - Identify spending velocity changes (accelerating/decelerating)

2. ANOMALY DETECTION
   - Flag unusual transactions (amount, merchant, timing)
   - Detect subscription creep (small recurring charges adding up)
   - Identify duplicate or erroneous charges

3. BUDGET INTELLIGENCE
   - Track spending vs budget by category
   - Predict month-end spending based on current trajectory
   - Suggest budget adjustments based on patterns

4. PROACTIVE ALERTS
   - Warn before overspending in any category
   - Alert about unusual account activity
   - Suggest savings opportunities (recurring charges you forgot about)

Architecture:
- record_transaction(amount, merchant, category): Log transaction
- get_spending_insights(days): Get spending pattern analysis
- detect_anomalies(): Find unusual financial activity
- get_budget_status(): Get budget tracking
- get_savings_opportunities(): Find money-saving opportunities
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "finance_pattern_detector"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRANSACTION_LOG = DATA_DIR / "transactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Transaction:
    """A financial transaction."""
    amount: float = 0.0
    merchant: str = ""
    category: str = ""  # food, transport, entertainment, utilities, subscription, etc.
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    transaction_type: str = "expense"  # expense, income, transfer
    recurring: bool = False
    notes: str = ""


@dataclass
class BudgetCategory:
    """Budget tracking for a category."""
    category: str = ""
    budget_limit: float = 0.0
    spent_this_month: float = 0.0
    projected_month_end: float = 0.0
    status: str = "on_track"  # on_track, at_risk, over


class FinancePatternDetector:
    """
    Detect financial patterns and provide proactive insights.
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
        self._transactions: deque = deque(maxlen=500)
        self._budgets: Dict[str, BudgetCategory] = {}
        self._stats = {
            "total_transactions": 0,
            "total_spent": 0.0,
            "total_income": 0.0,
            "avg_transaction": 0.0,
            "subscription_total": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_transaction(self, amount: float, merchant: str = "", category: str = "", transaction_type: str = "expense", recurring: bool = False, notes: str = "") -> Transaction:
        """Record a financial transaction."""
        txn = Transaction(
            amount=amount,
            merchant=merchant,
            category=category or "uncategorized",
            transaction_type=transaction_type,
            recurring=recurring,
            notes=notes,
        )

        with self._lock:
            self._transactions.append(txn)
            self._stats["total_transactions"] += 1
            if transaction_type == "expense":
                self._stats["total_spent"] += amount
                if recurring:
                    self._stats["subscription_total"] += amount
            elif transaction_type == "income":
                self._stats["total_income"] += amount

            self._update_budget(category, amount, transaction_type)
            self._update_stats()

        self._save_stats()
        self._log_transaction(txn)

        return txn

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_spending_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get spending pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [t for t in self._transactions if t.timestamp > cutoff and t.transaction_type == "expense"]

        if not recent:
            return {"status": "insufficient_data"}

        # Category breakdown
        by_category = defaultdict(lambda: {"count": 0, "total": 0.0, "avg": 0.0})
        for t in recent:
            cat = t.category
            by_category[cat]["count"] += 1
            by_category[cat]["total"] += t.amount

        for cat in by_category:
            by_category[cat]["avg"] = round(by_category[cat]["total"] / by_category[cat]["count"], 2)

        # Time trend
        daily_spending = defaultdict(float)
        for t in recent:
            day = t.timestamp[:10]
            daily_spending[day] += t.amount

        avg_daily = sum(daily_spending.values()) / max(1, len(daily_spending))
        max_day = max(daily_spending.items(), key=lambda x: x[1]) if daily_spending else ("", 0)

        # Recurring vs discretionary
        recurring_total = sum(t.amount for t in recent if t.recurring)
        discretionary_total = sum(t.amount for t in recent if not t.recurring)

        return {
            "days_analyzed": len(set(t.timestamp[:10] for t in recent)),
            "total_spent": round(sum(t.amount for t in recent), 2),
            "transaction_count": len(recent),
            "avg_transaction": round(sum(t.amount for t in recent) / len(recent), 2),
            "avg_daily": round(avg_daily, 2),
            "max_day": {"date": max_day[0], "amount": round(max_day[1], 2)} if max_day[0] else None,
            "category_breakdown": {k: dict(v) for k, v in by_category.items()},
            "recurring_pct": round(recurring_total / max(1, sum(t.amount for t in recent)) * 100, 1),
            "discretionary_pct": round(discretionary_total / max(1, sum(t.amount for t in recent)) * 100, 1),
        }

    def detect_anomalies(self, days: int = 7) -> List[Dict[str, Any]]:
        """Find unusual financial activity."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [t for t in self._transactions if t.timestamp > cutoff and t.transaction_type == "expense"]

        if len(recent) < 5:
            return []

        anomalies = []

        # Statistical anomalies (amount > 3 std dev from mean)
        amounts = [t.amount for t in recent]
        mean = sum(amounts) / len(amounts)
        variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
        std_dev = math.sqrt(variance)

        for t in recent:
            if t.amount > mean + 3 * std_dev:
                anomalies.append({
                    "type": "unusual_amount",
                    "transaction": f"{t.merchant}: ${t.amount:.2f}",
                    "severity": "high",
                    "reason": f"Amount is {((t.amount - mean) / max(1, std_dev)):.1f} standard deviations above average",
                })

        # Duplicate detection
        seen = defaultdict(int)
        for t in recent:
            key = (t.merchant, t.amount, t.timestamp[:10])
            seen[key] += 1
            if seen[key] > 1:
                anomalies.append({
                    "type": "duplicate",
                    "transaction": f"{t.merchant}: ${t.amount:.2f}",
                    "severity": "medium",
                    "reason": f"Duplicate charge detected on {t.timestamp[:10]}",
                })

        # Velocity anomaly (spending much faster than usual)
        if len(recent) >= 3:
            recent_daily = sum(t.amount for t in recent[-3:]) / 3
            older = [t for t in recent[:-3]]
            if older:
                older_daily = sum(t.amount for t in older) / max(1, len(older))
                if recent_daily > older_daily * 2:
                    anomalies.append({
                        "type": "spending_spike",
                        "severity": "medium",
                        "reason": f"Recent spending is {recent_daily/older_daily:.1f}x higher than previous pattern",
                    })

        return anomalies

    def get_budget_status(self) -> List[Dict[str, Any]]:
        """Get budget tracking status."""
        now = datetime.now()
        month_start = now.replace(day=1).isoformat()[:10]

        # Calculate current month spending by category
        month_txns = [t for t in self._transactions if t.timestamp[:10] >= month_start and t.transaction_type == "expense"]
        month_spending = defaultdict(float)
        for t in month_txns:
            month_spending[t.category] += t.amount

        # Days remaining in month
        days_in_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        days_remaining = max(1, (days_in_month - now).days)
        days_elapsed = max(1, now.day)

        status = []
        for cat, budget in self._budgets.items():
            spent = month_spending.get(cat, 0)
            projected = spent / days_elapsed * 30  # Project to full month
            pct_used = spent / max(1, budget.budget_limit) * 100
            projected_pct = projected / max(1, budget.budget_limit) * 100

            if projected_pct > 100:
                cat_status = "over"
            elif projected_pct > 80:
                cat_status = "at_risk"
            else:
                cat_status = "on_track"

            status.append({
                "category": cat,
                "budget": budget.budget_limit,
                "spent": round(spent, 2),
                "projected": round(projected, 2),
                "pct_used": round(pct_used, 1),
                "projected_pct": round(projected_pct, 1),
                "status": cat_status,
                "days_remaining": days_remaining,
            })

        return sorted(status, key=lambda x: x["projected_pct"], reverse=True)

    def get_savings_opportunities(self) -> List[Dict[str, Any]]:
        """Find money-saving opportunities."""
        opportunities = []

        # Subscription audit
        recurring = [t for t in self._transactions if t.recurring and t.transaction_type == "expense"]
        if recurring:
            monthly_sub_total = sum(t.amount for t in recurring[-30:])  # Last 30 days
            if monthly_sub_total > 50:
                opportunities.append({
                    "type": "subscription_audit",
                    "potential_savings": round(monthly_sub_total * 0.2, 2),
                    "suggestion": f"You're spending ${monthly_sub_total:.2f}/month on subscriptions. Review which ones you actually use.",
                    "impact": "high",
                })

        # Category overspend
        budget_status = self.get_budget_status()
        for cat in budget_status:
            if cat["status"] == "at_risk":
                opportunities.append({
                    "type": "category_overspend",
                    "potential_savings": round(cat["projected"] - cat["budget"], 2),
                    "suggestion": f"{cat['category'].title()} is projected to exceed budget by ${round(cat['projected'] - cat['budget'], 2)}. Consider cutting back.",
                    "impact": "medium",
                })

        # Duplicate subscriptions (same merchant, multiple charges)
        merchant_counts = defaultdict(int)
        for t in recurring:
            merchant_counts[t.merchant] += 1
        for merchant, count in merchant_counts.items():
            if count > 1:
                opportunities.append({
                    "type": "duplicate_subscription",
                    "potential_savings": "unknown",
                    "suggestion": f"Multiple charges from {merchant} detected. Check if you have duplicate subscriptions.",
                    "impact": "medium",
                })

        return opportunities

    # ── Budget Management ──────────────────────────────────────────────────

    def set_budget(self, category: str, limit: float):
        """Set a budget limit for a category."""
        self._budgets[category] = BudgetCategory(
            category=category,
            budget_limit=limit,
        )
        self._save_stats()

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_budget(self, category: str, amount: float, transaction_type: str):
        """Update budget tracking."""
        if category in self._budgets and transaction_type == "expense":
            self._budgets[category].spent_this_month += amount

    def _update_stats(self):
        """Update running statistics."""
        if self._transactions:
            amounts = [t.amount for t in self._transactions if t.transaction_type == "expense"]
            if amounts:
                self._stats["avg_transaction"] = round(sum(amounts) / len(amounts), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "budgets": {k: {
                    "category": v.category,
                    "budget_limit": v.budget_limit,
                    "spent_this_month": v.spent_this_month,
                } for k, v in self._budgets.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.finance_pattern_detector")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("budgets", {}).items():
                    self._budgets[k] = BudgetCategory(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.finance_pattern_detector")

    def _log_transaction(self, txn: Transaction):
        try:
            with open(TRANSACTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": txn.timestamp,
                    "amount": txn.amount,
                    "merchant": txn.merchant,
                    "category": txn.category,
                    "type": txn.transaction_type,
                    "recurring": txn.recurring,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.finance_pattern_detector")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_fpd_instance: Optional[FinancePatternDetector] = None
_fpd_lock = threading.Lock()


def get_finance_pattern_detector() -> FinancePatternDetector:
    global _fpd_instance
    with _fpd_lock:
        if _fpd_instance is None:
            _fpd_instance = FinancePatternDetector()
        return _fpd_instance
