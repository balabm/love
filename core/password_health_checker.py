"""
LOVE Password Health Checker — Security Intelligence (Modern AI Pattern)

Most password tools are breach checkers. This checker:

1. PASSWORD TRACKING
   - Track password age, strength, and reuse across accounts
   - Record password changes and their triggers
   - Monitor which accounts have 2FA enabled

2. HEALTH ANALYSIS
   - Calculate overall password health score
   - Identify weak, old, or reused passwords
   - Detect accounts without 2FA

3. RISK ASSESSMENT
   - Score each account's security posture
   - Identify high-value accounts that need extra protection
   - Track exposure to known breaches

4. PROACTIVE REMINDERS
   - Alert when passwords need rotation
   - Suggest stronger passwords for weak ones
   - Recommend 2FA for high-value accounts

Architecture:
- record_account(service, password_age, has_2fa, strength): Log account
- get_password_health(): Get overall security health
- get_risk_assessment(): Get account risk analysis
- get_security_recommendations(): Get improvement suggestions
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

DATA_DIR = Path(__file__).parent.parent / "data" / "password_health_checker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNT_LOG = DATA_DIR / "accounts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Account:
    """A tracked account."""
    service: str = ""
    username: str = ""
    password_age_days: int = 0
    password_strength: float = 0.5  # 0-1
    has_2fa: bool = False
    account_value: str = "medium"  # low, medium, high, critical
    last_changed: str = field(default_factory=lambda: datetime.now().isoformat())
    category: str = ""  # financial, social, work, shopping, entertainment
    breach_exposed: bool = False
    notes: str = ""


class PasswordHealthChecker:
    """
    Monitor password health and security posture.
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
        self._accounts: Dict[str, Account] = {}
        self._stats = {
            "total_accounts": 0,
            "avg_password_age": 0,
            "accounts_with_2fa": 0,
            "weak_passwords": 0,
            "overall_score": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_account(self, service: str = "", username: str = "", password_age_days: int = 0, password_strength: float = 0.5, has_2fa: bool = False, account_value: str = "medium", category: str = "", breach_exposed: bool = False, notes: str = "") -> Account:
        """Record or update an account."""
        account_id = f"{service}_{username}".lower().replace(" ", "_")
        account = Account(
            service=service or "unspecified",
            username=username or "",
            password_age_days=password_age_days,
            password_strength=password_strength,
            has_2fa=has_2fa,
            account_value=account_value,
            category=category or "general",
            breach_exposed=breach_exposed,
            notes=notes,
        )

        with self._lock:
            self._accounts[account_id] = account
            self._stats["total_accounts"] = len(self._accounts)
            self._update_stats()

        self._save_stats()
        self._log_account(account)

        return account

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_password_health(self) -> Dict[str, Any]:
        """Get overall password security health."""
        if not self._accounts:
            return {"status": "no_accounts"}

        # Age analysis
        ages = [a.password_age_days for a in self._accounts.values()]
        avg_age = sum(ages) / len(ages)
        old_passwords = sum(1 for a in ages if a > 180)

        # Strength analysis
        strengths = [a.password_strength for a in self._accounts.values()]
        avg_strength = sum(strengths) / len(strengths)
        weak = sum(1 for s in strengths if s < 0.4)

        # 2FA analysis
        with_2fa = sum(1 for a in self._accounts.values() if a.has_2fa)
        without_2fa = len(self._accounts) - with_2fa

        # Category breakdown
        by_category = defaultdict(lambda: {"count": 0, "with_2fa": 0, "avg_strength": 0.0})
        for a in self._accounts.values():
            cat = a.category
            by_category[cat]["count"] += 1
            by_category[cat]["with_2fa"] += 1 if a.has_2fa else 0
            by_category[cat]["avg_strength"] += a.password_strength

        for cat in by_category:
            by_category[cat]["avg_strength"] = round(by_category[cat]["avg_strength"] / by_category[cat]["count"], 2)

        # Calculate overall score
        age_score = max(0, 100 - (avg_age / 3))  # Penalty for old passwords
        strength_score = avg_strength * 100
        twofa_score = (with_2fa / max(1, len(self._accounts))) * 100
        overall = round(age_score * 0.3 + strength_score * 0.4 + twofa_score * 0.3)

        return {
            "overall_score": min(100, overall),
            "total_accounts": len(self._accounts),
            "avg_password_age_days": round(avg_age, 1),
            "old_passwords": old_passwords,
            "avg_strength": round(avg_strength, 2),
            "weak_passwords": weak,
            "accounts_with_2fa": with_2fa,
            "accounts_without_2fa": without_2fa,
            "breach_exposed": sum(1 for a in self._accounts.values() if a.breach_exposed),
            "by_category": dict(by_category),
        }

    def get_risk_assessment(self) -> List[Dict[str, Any]]:
        """Get account risk analysis."""
        risks = []
        
        for account_id, account in self._accounts.items():
            risk_score = 0
            risk_factors = []

            # Weak password
            if account.password_strength < 0.4:
                risk_score += 30
                risk_factors.append("weak_password")

            # Old password
            if account.password_age_days > 180:
                risk_score += 20
                risk_factors.append("old_password")

            # No 2FA on high-value account
            if not account.has_2fa and account.account_value in ["high", "critical"]:
                risk_score += 25
                risk_factors.append("no_2fa_high_value")

            # Breach exposure
            if account.breach_exposed:
                risk_score += 40
                risk_factors.append("breach_exposed")

            # Reused password (check if same strength/age pattern)
            similar = [a for a in self._accounts.values() if a != account and abs(a.password_strength - account.password_strength) < 0.05 and abs(a.password_age_days - account.password_age_days) < 7]
            if len(similar) > 0:
                risk_score += 15
                risk_factors.append("likely_reused")

            risk_level = "critical" if risk_score >= 60 else "high" if risk_score >= 40 else "medium" if risk_score >= 20 else "low"

            risks.append({
                "service": account.service,
                "username": account.username,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "account_value": account.account_value,
            })

        return sorted(risks, key=lambda x: x["risk_score"], reverse=True)

    def get_security_recommendations(self) -> List[Dict[str, Any]]:
        """Get security improvement suggestions."""
        recommendations = []
        health = self.get_password_health()
        risks = self.get_risk_assessment()

        # Critical risks first
        critical = [r for r in risks if r["risk_level"] == "critical"]
        for risk in critical[:3]:
            recommendations.append({
                "priority": "critical",
                "service": risk["service"],
                "action": f"Change password immediately for {risk['service']}. {', '.join(risk['risk_factors'])}",
                "impact": "High",
            })

        # 2FA recommendations for high-value accounts
        high_value_no_2fa = [r for r in risks if "no_2fa_high_value" in r["risk_factors"]]
        for risk in high_value_no_2fa[:3]:
            recommendations.append({
                "priority": "high",
                "service": risk["service"],
                "action": f"Enable 2FA on {risk['service']} ({risk['account_value']} value account).",
                "impact": "Medium",
            })

        # Old password rotation
        old_passwords = [r for r in risks if "old_password" in r["risk_factors"] and r["risk_level"] not in ["critical"]]
        if old_passwords:
            recommendations.append({
                "priority": "medium",
                "service": "multiple",
                "action": f"Rotate passwords for {len(old_passwords)} accounts older than 6 months.",
                "impact": "Low",
            })

        # General recommendation
        if health.get("accounts_without_2fa", 0) > health.get("accounts_with_2fa", 0):
            recommendations.append({
                "priority": "medium",
                "service": "general",
                "action": "Most accounts lack 2FA. Prioritize adding it to financial and email accounts.",
                "impact": "Medium",
            })

        if not recommendations:
            recommendations.append({
                "priority": "low",
                "service": "general",
                "action": "Your password health looks good! Continue rotating passwords every 6 months.",
                "impact": "None",
            })

        return recommendations

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._accounts:
            ages = [a.password_age_days for a in self._accounts.values()]
            self._stats["avg_password_age"] = round(sum(ages) / len(ages), 1)
            self._stats["accounts_with_2fa"] = sum(1 for a in self._accounts.values() if a.has_2fa)
            self._stats["weak_passwords"] = sum(1 for a in self._accounts.values() if a.password_strength < 0.4)
            self._stats["overall_score"] = self.get_password_health().get("overall_score", 0)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "accounts": {k: {
                    "service": v.service,
                    "username": v.username,
                    "password_age_days": v.password_age_days,
                    "password_strength": v.password_strength,
                    "has_2fa": v.has_2fa,
                    "account_value": v.account_value,
                    "last_changed": v.last_changed,
                    "category": v.category,
                    "breach_exposed": v.breach_exposed,
                    "notes": v.notes,
                } for k, v in self._accounts.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.password_health_checker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("accounts", {}).items():
                    self._accounts[k] = Account(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.password_health_checker")

    def _log_account(self, account: Account):
        try:
            with open(ACCOUNT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": account.last_changed,
                    "service": account.service,
                    "username": account.username,
                    "strength": account.password_strength,
                    "has_2fa": account.has_2fa,
                    "category": account.category,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.password_health_checker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_phc_instance: Optional[PasswordHealthChecker] = None
_phc_lock = threading.Lock()


def get_password_health_checker() -> PasswordHealthChecker:
    global _phc_instance
    with _phc_lock:
        if _phc_instance is None:
            _phc_instance = PasswordHealthChecker()
        return _phc_instance
