"""
LOVE Authentic Expression Coach — Voice Intelligence (Modern AI Pattern)

Most people hide their truth. This coach:

1. EXPRESSION TRACKING
   - Record expression moments and their characteristics
   - Track expression types (truth, need, boundary, desire, opinion, feeling)
   - Log authenticity, fear, reception, and satisfaction of expression

2. PATTERN ANALYSIS
   - Identify the user's expression profile (suppressed, guarded, developing, free)
   - Find expression patterns that create connection vs isolation
   - Detect chronic suppression and its costs

3. EXPRESSION BUILDING
   - Suggest practices for speaking your truth more freely
   - Provide frameworks for authentic, kind communication
   - Recommend practices for expressing without attacking

4. AUTHENTICITY CULTIVATION
   - Track the correlation between authenticity and relationship quality
   - Alert when suppression is becoming the default
   - Celebrate moments of genuine, brave expression

Architecture:
- record_expression(expression, type, authenticity, fear, reception, satisfaction): Log expression
- get_expression_stats(): Get expression pattern analysis
- get_expression_suggestion(capacity, context): Get suggestion
- get_expression_score(): Calculate overall expression health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "authentic_expression_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPRESSION_LOG = DATA_DIR / "expressions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ExpressionEntry:
    """A tracked expression moment."""
    entry_id: str = ""
    expression: str = ""  # what was expressed
    expression_type: str = ""  # truth, need, boundary, desire, opinion, feeling
    authenticity: float = 0.0  # 0-1
    fear: float = 0.0  # 0-1
    reception: float = 0.0  # 0-1 how it was received
    satisfaction: float = 0.0  # 0-1
    kindness: float = 0.0  # 0-1 was it kind?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AuthenticExpressionCoach:
    """
    Intelligent authentic expression coach with suppression detection and authenticity cultivation.
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
            "avg_authenticity": 0.0,
            "avg_satisfaction": 0.0,
            "suppression_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_expression(self, expression: str = "", expression_type: str = "", authenticity: float = 0.0, fear: float = 0.0, reception: float = 0.0, satisfaction: float = 0.0, kindness: float = 0.0, notes: str = "") -> ExpressionEntry:
        """Record an expression moment."""
        entry_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ExpressionEntry(
            entry_id=entry_id,
            expression=expression or "unspecified",
            expression_type=expression_type or "truth",
            authenticity=authenticity,
            fear=fear,
            reception=reception,
            satisfaction=satisfaction,
            kindness=kindness,
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

    def get_expression_stats(self) -> Dict[str, Any]:
        """Get expression pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "auth_sum": 0.0, "fear_sum": 0.0, "sat_sum": 0.0})
        for e in self._entries:
            by_type[e.expression_type]["count"] += 1
            by_type[e.expression_type]["auth_sum"] += e.authenticity
            by_type[e.expression_type]["fear_sum"] += e.fear
            by_type[e.expression_type]["sat_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_authenticity": round(data["auth_sum"] / count, 2),
                "avg_fear": round(data["fear_sum"] / count, 2),
                "avg_satisfaction": round(data["sat_sum"] / count, 2),
            }

        # Authenticity analysis
        high_auth = [e for e in self._entries if e.authenticity > 0.7]
        low_auth = [e for e in self._entries if e.authenticity < 0.4]
        if high_auth and low_auth:
            high_auth_sat = sum(e.satisfaction for e in high_auth) / len(high_auth)
            low_auth_sat = sum(e.satisfaction for e in low_auth) / len(low_auth)
            high_auth_rec = sum(e.reception for e in high_auth) / len(high_auth)
            low_auth_rec = sum(e.reception for e in low_auth) / len(low_auth)
        else:
            high_auth_sat = 0
            low_auth_sat = 0
            high_auth_rec = 0
            low_auth_rec = 0

        # Fear analysis
        high_fear = [e for e in self._entries if e.fear > 0.7]
        low_fear = [e for e in self._entries if e.fear < 0.4]
        if high_fear and low_fear:
            high_fear_auth = sum(e.authenticity for e in high_fear) / len(high_fear)
            low_fear_auth = sum(e.authenticity for e in low_fear) / len(low_fear)
        else:
            high_fear_auth = 0
            low_fear_auth = 0

        # Suppression risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            recent_fear = sum(e.fear for e in recent) / len(recent)
            suppression_risk = recent_auth < 0.3 and recent_fear > 0.7
        else:
            suppression_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "authenticity_impact": {
                "high_authenticity_satisfaction": round(high_auth_sat, 2),
                "low_authenticity_satisfaction": round(low_auth_sat, 2),
                "high_authenticity_reception": round(high_auth_rec, 2),
                "low_authenticity_reception": round(low_auth_rec, 2),
            },
            "fear_effect": {
                "high_fear_authenticity": round(high_fear_auth, 2),
                "low_fear_authenticity": round(low_fear_auth, 2),
            },
            "suppression_risk": suppression_risk,
            "avg_authenticity": round(sum(e.authenticity for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
        }

    def get_expression_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get expression suggestion."""
        suggestions = [
            "Your truth is not an attack. It's information. 'I feel hurt when you do that' is not an attack. It's a fact about your internal state. Share it. The right people will receive it.",
            "Authenticity is not blurting. It's expressing your truth with care for the listener. The person who says 'I'm just being honest' while being cruel is not authentic. They're just cruel.",
            "Start small. You don't have to share your deepest secrets on day one. One honest preference. One real opinion. One genuine feeling. Authenticity is a muscle. Build it gradually.",
            "The cost of suppression is higher than the cost of expression. Suppressed truth becomes resentment. Suppressed needs become deprivation. Suppressed feelings become illness. Express. Even imperfectly.",
            "You are not responsible for how people receive your truth. You're responsible for speaking it kindly. If they can't handle it, that's their work. Not yours. Keep speaking kindly.",
            "Authentic expression creates intimacy. When you share your real self, you give permission for others to share theirs. Vulnerability begets vulnerability. It's the path to real connection.",
            "Notice when you say 'I'm fine' and you're not. That's the moment. The split between what you feel and what you express. Close that gap. One moment at a time.",
            "Your needs are not too much. Your desires are not shameful. Your boundaries are not selfish. Express them. The people who matter will respect them. The people who don't, don't matter.",
            "Kind honesty is possible. 'I don't want to do that' is kind. 'I need something different' is kind. You don't have to lie to be nice. You can be both honest and kind. That's authenticity.",
            "The person who never expresses their truth is invisible. Even to themselves. Because they don't know who they are. They're just a collection of reactions to other people's expectations. Express. Become visible."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small truth. One honest preference. One real feeling. One small step toward visibility. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A boundary expressed. A need shared. A feeling named. Medium expression work."
        else:
            capacity_note = "Good capacity. Deep authentic expression. A systematic practice of speaking your truth with kindness and courage. You have the strength to be truly seen."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Authentic expression is the bridge between who you are and who others see. Most people build walls instead of bridges. They hide their truth. They suppress their needs. They fake their feelings. And they wonder why they feel invisible. Why their relationships feel hollow. Why they don't feel known. The work of authentic expression is about dismantling those walls. About speaking your truth. About naming your needs. About sharing your feelings. And about doing it with kindness. Because authenticity without kindness is just cruelty. And kindness without authenticity is just manipulation. The goal is both. To be real and to be kind. To be seen and to see others. That's the work of authentic expression. And it's the foundation of all genuine connection."
        }

    def get_expression_score(self) -> int:
        """Calculate overall expression health (0-100)."""
        if not self._entries:
            return 25

        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_rec = sum(e.reception for e in self._entries) / len(self._entries)
        avg_kind = sum(e.kindness for e in self._entries) / len(self._entries)
        avg_fear = sum(e.fear for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_auth = 0
            recent_sat = 0

        # Suppression penalty
        supp_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_auth_30 = sum(e.authenticity for e in last_30) / len(last_30)
            recent_fear_30 = sum(e.fear for e in last_30) / len(last_30)
            if recent_auth_30 < 0.3 and recent_fear_30 > 0.7:
                supp_penalty = 15

        # Type variety
        unique_types = len(set(e.expression_type for e in self._entries))

        score = (avg_auth * 25) + (avg_sat * 20) + (avg_rec * 15) + (avg_kind * 15) + (recent_auth * 10) + (recent_sat * 5) + (unique_types * 2) - (avg_fear * 10) - supp_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_authenticity"] = round(sum(e.authenticity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_auth = sum(e.authenticity for e in recent) / len(recent)
                recent_fear = sum(e.fear for e in recent) / len(recent)
                self._stats["suppression_risk"] = recent_auth < 0.3 and recent_fear > 0.7
            else:
                self._stats["suppression_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.authentic_expression_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.authentic_expression_coach")

    def _log_entry(self, entry: ExpressionEntry):
        try:
            with open(EXPRESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "expression": entry.expression,
                    "expression_type": entry.expression_type,
                    "authenticity": entry.authenticity,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.authentic_expression_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_aec_instance: Optional[AuthenticExpressionCoach] = None
_aec_lock = threading.Lock()


def get_authentic_expression_coach() -> AuthenticExpressionCoach:
    global _aec_instance
    with _aec_lock:
        if _aec_instance is None:
            _aec_instance = AuthenticExpressionCoach()
        return _aec_instance
