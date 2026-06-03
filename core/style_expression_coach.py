"""
LOVE Style Expression Coach — Personal Aesthetic Intelligence (Modern AI Pattern)

Most people dress to conform. This coach:

1. STYLE TRACKING
   - Record style moments and their characteristics
   - Track style types (professional, casual, creative, social, comfort, statement)
   - Log authenticity, confidence, comfort, appropriateness, and expression of style

2. PATTERN ANALYSIS
   - Identify the user's style profile (invisible, safe, developing, expressive)
   - Find style patterns that create confidence vs self-erasure
   - Detect chronic conformity and its costs

3. EXPRESSION BUILDING
   - Suggest practices for authentic personal style
   - Provide frameworks for dressing as self-expression
   - Recommend practices for style experimentation

4. AESTHETIC AUTHENTICITY CULTIVATION
   - Track the correlation between style authenticity and confidence
   - Alert when camouflage is replacing expression
   - Celebrate moments of genuine style courage

Architecture:
- record_style(choice, type, authenticity, confidence, comfort, appropriateness, expression): Log style
- get_style_stats(): Get style pattern analysis
- get_style_suggestion(capacity, context): Get suggestion
- get_style_score(): Calculate overall style health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "style_expression_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STYLE_LOG = DATA_DIR / "styles.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class StyleEntry:
    """A tracked style moment."""
    entry_id: str = ""
    choice: str = ""  # what was the choice
    style_type: str = ""  # professional, casual, creative, social, comfort, statement
    authenticity: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    comfort: float = 0.0  # 0-1
    appropriateness: float = 0.0  # 0-1
    expression: float = 0.0  # 0-1
    experimentation: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class StyleExpressionCoach:
    """
    Intelligent style expression coach with conformity detection and aesthetic authenticity cultivation.
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
            "avg_confidence": 0.0,
            "conformity_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_style(self, choice: str = "", style_type: str = "", authenticity: float = 0.0, confidence: float = 0.0, comfort: float = 0.0, appropriateness: float = 0.0, expression: float = 0.0, experimentation: float = 0.0, notes: str = "") -> StyleEntry:
        """Record a style moment."""
        entry_id = f"stl_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = StyleEntry(
            entry_id=entry_id,
            choice=choice or "unspecified",
            style_type=style_type or "casual",
            authenticity=authenticity,
            confidence=confidence,
            comfort=comfort,
            appropriateness=appropriateness,
            expression=expression,
            experimentation=experimentation,
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

    def get_style_stats(self) -> Dict[str, Any]:
        """Get style pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "authenticity_sum": 0.0, "confidence_sum": 0.0, "expression_sum": 0.0})
        for e in self._entries:
            by_type[e.style_type]["count"] += 1
            by_type[e.style_type]["authenticity_sum"] += e.authenticity
            by_type[e.style_type]["confidence_sum"] += e.confidence
            by_type[e.style_type]["expression_sum"] += e.expression

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_authenticity": round(data["authenticity_sum"] / count, 2),
                "avg_confidence": round(data["confidence_sum"] / count, 2),
                "avg_expression": round(data["expression_sum"] / count, 2),
            }

        # Authenticity analysis
        high_auth = [e for e in self._entries if e.authenticity > 0.7]
        low_auth = [e for e in self._entries if e.authenticity < 0.4]
        if high_auth and low_auth:
            high_auth_conf = sum(e.confidence for e in high_auth) / len(high_auth)
            low_auth_conf = sum(e.confidence for e in low_auth) / len(low_auth)
            high_auth_expr = sum(e.expression for e in high_auth) / len(high_auth)
            low_auth_expr = sum(e.expression for e in low_auth) / len(low_auth)
        else:
            high_auth_conf = 0
            low_auth_conf = 0
            high_auth_expr = 0
            low_auth_expr = 0

        # Experimentation analysis
        high_exp = [e for e in self._entries if e.experimentation > 0.7]
        low_exp = [e for e in self._entries if e.experimentation < 0.4]
        if high_exp and low_exp:
            high_exp_conf = sum(e.confidence for e in high_exp) / len(high_exp)
            low_exp_conf = sum(e.confidence for e in low_exp) / len(low_exp)
        else:
            high_exp_conf = 0
            low_exp_conf = 0

        # Conformity risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            recent_expr = sum(e.expression for e in recent) / len(recent)
            conformity_risk = recent_auth < 0.3 and recent_expr < 0.3
        else:
            conformity_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "authenticity_impact": {
                "high_authenticity_confidence": round(high_auth_conf, 2),
                "low_authenticity_confidence": round(low_auth_conf, 2),
                "high_authenticity_expression": round(high_auth_expr, 2),
                "low_authenticity_expression": round(low_auth_expr, 2),
            },
            "experimentation_effect": {
                "high_experimentation_confidence": round(high_exp_conf, 2),
                "low_experimentation_confidence": round(low_exp_conf, 2),
            },
            "conformity_risk": conformity_risk,
            "avg_authenticity": round(sum(e.authenticity for e in self._entries) / len(self._entries), 2),
            "avg_confidence": round(sum(e.confidence for e in self._entries) / len(self._entries), 2),
        }

    def get_style_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get style suggestion."""
        suggestions = [
            "Most people dress to disappear. To blend in. To not be noticed. To not offend. To not stand out. And they wonder why they feel invisible. Why they feel like ghosts in their own lives. The answer is in their closet. They're wearing camouflage.",
            "Your clothes are a language. They say things about you before you open your mouth. What do yours say? 'I'm safe.' 'I'm invisible.' 'I don't care.' Or 'This is who I am.' Choose what they say. Intentionally. Deliberately. Authentically.",
            "Wear what feels like you. Not what feels like the you you think you should be. Not the you that impresses. Not the you that conforms. The actual you. The you that feels alive. The you that feels free. That might be jeans. That might be color. That might be simplicity. That might be boldness. It doesn't matter what it is. It matters that it's you.",
            "Experiment. Try something new. A color you've never worn. A fit you've never tried. A combination you've never considered. Not to become someone else. To discover more of yourself. Style is exploration. Not destination.",
            "Comfort and expression are not enemies. The person who thinks style must be uncomfortable has confused fashion with self-expression. The person who thinks comfort must be sloppy has confused ease with carelessness. Find the intersection. Where you feel good and look like yourself.",
            "Notice what you wear when no one is watching. On weekends. At home. When you're alone. That's your true style. That's your authentic expression. Bring more of that into your public life. Not all of it. But more.",
            "Dress for the person you want to be. Not the person you think others want you to be. The clothes you wear influence how you feel. How you act. How you think. Dress like the person you want to become. And watch yourself become them.",
            "Quality over quantity. Not more clothes. Better clothes. Fewer pieces that feel like you. That fit well. That last. That you reach for again and again. A small, intentional wardrobe is more powerful than a large, chaotic one.",
            "The person who dresses authentically is not seeking attention. They're refusing to hide. They're saying 'I am here. This is me. Take it or leave it.' And that is the most powerful statement anyone can make. With words or without.",
            "Style is not shallow. It's not vanity. It's not frivolous. It's self-expression. It's self-respect. It's communication. It's courage. The person who understands this uses their clothes as a tool for authenticity. And that is one of the most profound things you can do."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One authentic choice. One color tried. One outfit that feels like you. One moment of not hiding. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A wardrobe edit. An experiment made. A comfort-expression balance found. A personal style emerging. Medium expression."
        else:
            capacity_note = "Good capacity. Deep style work. A systematic practice of authentic self-expression through dress. You have the strength to wear who you are."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Style expression coaching is not about fashion. It's about authenticity. Most people dress to conform. To blend. To disappear. They wear what they think they should wear. What others expect. What feels safe. And they wonder why they feel invisible. Why they feel like they're playing a role. The work of style expression coaching is about understanding that your clothes are a language. They communicate before you speak. They affect how you feel. How you act. How others perceive you. And most importantly, they affect how you perceive yourself. The person who dresses authentically is not seeking attention. They're refusing to hide. They're saying 'this is who I am' without saying a word. And that is one of the most powerful forms of self-expression available."
        }

    def get_style_score(self) -> int:
        """Calculate overall style health (0-100)."""
        if not self._entries:
            return 25

        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_conf = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_comf = sum(e.comfort for e in self._entries) / len(self._entries)
        avg_app = sum(e.appropriateness for e in self._entries) / len(self._entries)
        avg_expr = sum(e.expression for e in self._entries) / len(self._entries)
        avg_exp = sum(e.experimentation for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            recent_expr = sum(e.expression for e in recent) / len(recent)
        else:
            recent_auth = 0
            recent_expr = 0

        # Conformity penalty
        conf_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_auth_30 = sum(e.authenticity for e in last_30) / len(last_30)
            recent_expr_30 = sum(e.expression for e in last_30) / len(last_30)
            if recent_auth_30 < 0.3 and recent_expr_30 < 0.3:
                conf_penalty = 15

        # Type variety
        unique_types = len(set(e.style_type for e in self._entries))

        score = (avg_auth * 25) + (avg_conf * 15) + (avg_comf * 10) + (avg_app * 10) + (avg_expr * 20) + (avg_exp * 10) + (recent_auth * 5) + (recent_expr * 5) + (unique_types * 2) - conf_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_authenticity"] = round(sum(e.authenticity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_confidence"] = round(sum(e.confidence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_auth = sum(e.authenticity for e in recent) / len(recent)
                recent_expr = sum(e.expression for e in recent) / len(recent)
                self._stats["conformity_risk"] = recent_auth < 0.3 and recent_expr < 0.3
            else:
                self._stats["conformity_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.style_expression_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.style_expression_coach")

    def _log_entry(self, entry: StyleEntry):
        try:
            with open(STYLE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "choice": entry.choice,
                    "style_type": entry.style_type,
                    "authenticity": entry.authenticity,
                    "confidence": entry.confidence,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.style_expression_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sec_instance: Optional[StyleExpressionCoach] = None
_sec_lock = threading.Lock()


def get_style_expression_coach() -> StyleExpressionCoach:
    global _sec_instance
    with _sec_lock:
        if _sec_instance is None:
            _sec_instance = StyleExpressionCoach()
        return _sec_instance
