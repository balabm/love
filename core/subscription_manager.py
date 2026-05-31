"""
LOVE Subscription Manager — Finance Intelligence (Modern AI Pattern)

Most subscription tools are just lists. This manager:

1. SUBSCRIPTION TRACKING
   - Record all subscriptions (streaming, SaaS, memberships, utilities)
   - Track cost, billing frequency, and next payment date
   - Log usage vs cost to find waste

2. VALUE ANALYSIS
   - Calculate cost-per-use for each subscription
   - Identify subscriptions that are overpriced for usage
   - Find overlapping services (multiple streaming services with same content)

3. OPTIMIZATION SUGGESTIONS
   - Suggest annual plans when they save money
   - Recommend cancellation of unused subscriptions
   - Propose family/team plans to reduce per-person cost

4. PROACTIVE ALERTS
   - Alert before trial periods end
   - Warn about price increases
   - Suggest cancellation timing (right after billing cycle)

Architecture:
- record_subscription(name, cost, frequency, category): Log subscription
- record_usage(name, date): Track when a subscription was used
- get_subscription_stats(): Get cost and value analysis
- get_optimization_suggestions(): Suggest money-saving actions
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "subscription_manager"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SUB_LOG = DATA_DIR / "subscriptions.jsonl"
USAGE_LOG = DATA_DIR / "usage.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Subscription:
    """A tracked subscription."""
    sub_id: str = ""
    name: str = ""
    cost: float = 0.0
    frequency: str = "monthly"  # daily, weekly, monthly, quarterly, yearly
    category: str = ""  # streaming, software, membership, utility, news, fitness
    provider: str = ""
    signup_date: str = field(default_factory=lambda: datetime.now().isoformat())
    next_billing_date: str = ""
    trial_end_date: Optional[str] = None
    is_active: bool = True
    cancellation_date: Optional[str] = None
    notes: str = ""


@dataclass
class UsageRecord:
    """A subscription usage record."""
    sub_id: str = ""
    usage_date: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_minutes: float = 0.0
    feature_used: str = ""


class SubscriptionManager:
    """
    Intelligent subscription manager with cost optimization.
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
        self._subscriptions: Dict[str, Subscription] = {}
        self._usage: deque = deque(maxlen=500)
        self._stats = {
            "total_subscriptions": 0,
            "active_subscriptions": 0,
            "monthly_cost": 0.0,
            "annual_cost": 0.0,
            "avg_cost_per_use": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_subscription(self, name: str = "", cost: float = 0, frequency: str = "monthly", category: str = "", provider: str = "", next_billing_date: str = "", trial_end_date: Optional[str] = None, notes: str = "") -> Subscription:
        """Record a subscription."""
        sub_id = f"sub_{name.replace(' ', '_').lower()}"
        sub = Subscription(
            sub_id=sub_id,
            name=name or "untitled",
            cost=cost,
            frequency=frequency or "monthly",
            category=category or "general",
            provider=provider or "",
            next_billing_date=next_billing_date,
            trial_end_date=trial_end_date,
            notes=notes,
        )

        with self._lock:
            self._subscriptions[sub_id] = sub
            self._stats["total_subscriptions"] = len(self._subscriptions)
            self._stats["active_subscriptions"] = sum(1 for s in self._subscriptions.values() if s.is_active)
            self._update_cost_stats()

        self._save_stats()
        self._log_subscription(sub)

        return sub

    def record_usage(self, sub_id: str = "", duration: float = 0, feature: str = "") -> Optional[UsageRecord]:
        """Record subscription usage."""
        if sub_id not in self._subscriptions:
            return None

        record = UsageRecord(
            sub_id=sub_id,
            duration_minutes=duration,
            feature_used=feature,
        )

        with self._lock:
            self._usage.append(record)
            self._update_stats()

        self._save_stats()
        self._log_usage(record)

        return record

    def cancel_subscription(self, sub_id: str = ""):
        """Mark a subscription as cancelled."""
        if sub_id in self._subscriptions:
            with self._lock:
                self._subscriptions[sub_id].is_active = False
                self._subscriptions[sub_id].cancellation_date = datetime.now().isoformat()
                self._stats["active_subscriptions"] -= 1
            self._save_stats()

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get cost and value analysis."""
        if not self._subscriptions:
            return {"status": "no_subscriptions"}

        # Category breakdown
        by_category = defaultdict(lambda: {"count": 0, "monthly_cost": 0.0, "usage_count": 0})
        for sub in self._subscriptions.values():
            if not sub.is_active:
                continue
            cat = sub.category
            by_category[cat]["count"] += 1
            by_category[cat]["monthly_cost"] += self._to_monthly_cost(sub.cost, sub.frequency)

        # Add usage data
        for usage in self._usage:
            if usage.sub_id in self._subscriptions and self._subscriptions[usage.sub_id].is_active:
                cat = self._subscriptions[usage.sub_id].category
                by_category[cat]["usage_count"] += 1

        # Per-subscription analysis
        sub_analysis = []
        for sub_id, sub in self._subscriptions.items():
            if not sub.is_active:
                continue
            usages = [u for u in self._usage if u.sub_id == sub_id]
            monthly_cost = self._to_monthly_cost(sub.cost, sub.frequency)
            
            if usages:
                cost_per_use = monthly_cost / max(1, len(usages))
                last_used = max(u.usage_date for u in usages)
                days_since = (datetime.now() - datetime.fromisoformat(last_used)).days
            else:
                cost_per_use = monthly_cost
                days_since = 999

            sub_analysis.append({
                "name": sub.name,
                "monthly_cost": round(monthly_cost, 2),
                "cost_per_use": round(cost_per_use, 2),
                "usage_count": len(usages),
                "days_since_last_use": days_since,
                "next_billing": sub.next_billing_date,
                "value_rating": "poor" if cost_per_use > 10 else "fair" if cost_per_use > 5 else "good" if cost_per_use > 2 else "excellent",
            })

        # Total costs
        total_monthly = sum(self._to_monthly_cost(s.cost, s.frequency) for s in self._subscriptions.values() if s.is_active)
        total_annual = total_monthly * 12

        return {
            "active_subscriptions": sum(1 for s in self._subscriptions.values() if s.is_active),
            "total_monthly_cost": round(total_monthly, 2),
            "total_annual_cost": round(total_annual, 2),
            "by_category": {k: {"count": v["count"], "monthly_cost": round(v["monthly_cost"], 2)} for k, v in by_category.items()},
            "subscription_analysis": sorted(sub_analysis, key=lambda x: x["cost_per_use"], reverse=True),
        }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest money-saving actions."""
        suggestions = []
        stats = self.get_subscription_stats()
        
        if stats.get("status") == "no_subscriptions":
            return [{"suggestion": "Record your subscriptions to get optimization suggestions.", "potential_savings": 0}]

        # Find unused subscriptions
        for sub in stats.get("subscription_analysis", []):
            if sub["days_since_last_use"] > 30:
                suggestions.append({
                    "type": "cancel_unused",
                    "subscription": sub["name"],
                    "suggestion": f"You haven't used {sub['name']} in {sub['days_since_last_use']} days.",
                    "action": "Cancel or pause this subscription.",
                    "potential_savings": round(sub["monthly_cost"] * 12, 2),
                })

        # Find poor value subscriptions
        for sub in stats.get("subscription_analysis", []):
            if sub["value_rating"] == "poor" and sub["days_since_last_use"] <= 30:
                suggestions.append({
                    "type": "reduce_usage",
                    "subscription": sub["name"],
                    "suggestion": f"{sub['name']} costs ${sub['cost_per_use']:.2f} per use. That's expensive.",
                    "action": "Use it more to get value, or find a cheaper alternative.",
                    "potential_savings": 0,
                })

        # Find trial endings
        for sub_id, sub in self._subscriptions.items():
            if sub.trial_end_date and sub.is_active:
                try:
                    trial_end = datetime.fromisoformat(sub.trial_end_date)
                    days_until = (trial_end - datetime.now()).days
                    if 0 <= days_until <= 3:
                        suggestions.append({
                            "type": "trial_ending",
                            "subscription": sub.name,
                            "suggestion": f"{sub.name} trial ends in {days_until} days. Decide now: keep or cancel?",
                            "action": "Set a reminder to cancel before billing if you don't want it.",
                            "potential_savings": round(self._to_monthly_cost(sub.cost, sub.frequency) * 12, 2),
                        })
                except Exception:
                    pass

        # Find duplicate categories
        category_counts = defaultdict(list)
        for sub in self._subscriptions.values():
            if sub.is_active:
                category_counts[sub.category].append(sub.name)
        
        for cat, subs in category_counts.items():
            if len(subs) > 2 and cat in ["streaming", "software", "news"]:
                suggestions.append({
                    "type": "consolidate",
                    "category": cat,
                    "suggestion": f"You have {len(subs)} {cat} subscriptions. Do you need all of them?",
                    "action": f"Consider rotating between {subs[0]} and {subs[1]} instead of paying for both.",
                    "potential_savings": "variable",
                })

        return sorted(suggestions, key=lambda x: x.get("potential_savings", 0), reverse=True)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _to_monthly_cost(self, cost: float, frequency: str) -> float:
        """Convert any frequency to monthly equivalent."""
        multipliers = {
            "daily": 30,
            "weekly": 4.33,
            "monthly": 1,
            "quarterly": 0.33,
            "yearly": 1/12,
        }
        return cost * multipliers.get(frequency, 1)

    def _update_cost_stats(self):
        """Update cost statistics."""
        active = [s for s in self._subscriptions.values() if s.is_active]
        monthly = sum(self._to_monthly_cost(s.cost, s.frequency) for s in active)
        self._stats["monthly_cost"] = round(monthly, 2)
        self._stats["annual_cost"] = round(monthly * 12, 2)

    def _update_stats(self):
        """Update usage statistics."""
        if self._usage:
            # Calculate average cost per use
            usage_by_sub = defaultdict(list)
            for u in self._usage:
                usage_by_sub[u.sub_id].append(u)
            
            total_cost_per_use = 0
            count = 0
            for sub_id, usages in usage_by_sub.items():
                if sub_id in self._subscriptions and self._subscriptions[sub_id].is_active:
                    monthly_cost = self._to_monthly_cost(self._subscriptions[sub_id].cost, self._subscriptions[sub_id].frequency)
                    cost_per_use = monthly_cost / max(1, len(usages))
                    total_cost_per_use += cost_per_use
                    count += 1
            
            if count > 0:
                self._stats["avg_cost_per_use"] = round(total_cost_per_use / count, 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "subscriptions": {k: {
                    "sub_id": v.sub_id,
                    "name": v.name,
                    "cost": v.cost,
                    "frequency": v.frequency,
                    "category": v.category,
                    "provider": v.provider,
                    "signup_date": v.signup_date,
                    "next_billing_date": v.next_billing_date,
                    "trial_end_date": v.trial_end_date,
                    "is_active": v.is_active,
                    "cancellation_date": v.cancellation_date,
                    "notes": v.notes,
                } for k, v in self._subscriptions.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("subscriptions", {}).items():
                    self._subscriptions[k] = Subscription(**v)
        except Exception:
            pass

    def _log_subscription(self, sub: Subscription):
        try:
            with open(SUB_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": sub.signup_date,
                    "sub_id": sub.sub_id,
                    "name": sub.name,
                    "cost": sub.cost,
                    "frequency": sub.frequency,
                    "category": sub.category,
                    "is_active": sub.is_active,
                }) + "\n")
        except Exception:
            pass

    def _log_usage(self, record: UsageRecord):
        try:
            with open(USAGE_LOG, "a") as f:
                f.write(json.dumps({
                    "sub_id": record.sub_id,
                    "date": record.usage_date,
                    "duration": record.duration_minutes,
                    "feature": record.feature_used,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sm_instance: Optional[SubscriptionManager] = None
_sm_lock = threading.Lock()


def get_subscription_manager() -> SubscriptionManager:
    global _sm_instance
    with _sm_lock:
        if _sm_instance is None:
            _sm_instance = SubscriptionManager()
        return _sm_instance
