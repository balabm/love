"""
LOVE Courage Coach — Brave Action Intelligence (Modern AI Pattern)

Most courage is not the absence of fear, but action despite it. This coach:

1. COURAGE TRACKING
   - Record courageous actions and their characteristics
   - Track fear levels and their correlation with action
   - Log courage types (moral, physical, social, creative, existential)

2. PATTERN ANALYSIS
   - Identify the user's courage profile (impulsive, calculated, reluctant, habitual)
   - Find courage triggers (values, relationships, deadlines, inspiration)
   - Detect courage gaps (areas where fear consistently wins)

3. COURAGE BUILDING
   - Suggest courage practices matched to current fear
   - Provide graduated exposure exercises
   - Recommendation moral clarity practices

4. BRAVERY CULTIVATION
   - Track the correlation between courage and growth
   - Alert when comfort zones are expanding unchecked
   - Celebrate courageous moments

Architecture:
- record_action(action, fear_level, courage_type, outcome): Log action
- get_courage_stats(): Get courage pattern analysis
- get_courage_practice(fear_type, current_courage): Get practice
- get_courage_score(): Calculate overall courage health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "courage_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COURAGE_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CourageAction:
    """A tracked courageous action."""
    action_id: str = ""
    action: str = ""
    fear_level: float = 0.5  # 0-1
    courage_type: str = ""  # moral, physical, social, creative, existential, emotional
    trigger: str = ""  # what prompted the action
    preparation: float = 0.5  # 0-1, how much preparation
    outcome: str = ""
    outcome_quality: float = 0.5  # 0-1
    growth: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CourageCoach:
    """
    Intelligent courage coach with fear analysis and graduated bravery building.
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
        self._actions: deque = deque(maxlen=300)
        self._stats = {
            "total_actions": 0,
            "avg_fear": 0.0,
            "avg_growth": 0.0,
            "dominant_type": "",
            "comfort_zone_expansion": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", fear_level: float = 0.5, courage_type: str = "", trigger: str = "", preparation: float = 0.5, outcome: str = "", outcome_quality: float = 0.5, growth: float = 0.5, notes: str = "") -> CourageAction:
        """Record a courageous action."""
        action_id = f"cour_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._actions)}"
        entry = CourageAction(
            action_id=action_id,
            action=action or "unspecified",
            fear_level=fear_level,
            courage_type=courage_type or "social",
            trigger=trigger,
            preparation=preparation,
            outcome=outcome,
            outcome_quality=outcome_quality,
            growth=growth,
            notes=notes,
        )

        with self._lock:
            self._actions.append(entry)
            self._stats["total_actions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_action(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_courage_stats(self) -> Dict[str, Any]:
        """Get courage pattern analysis."""
        if not self._actions:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "fear_sum": 0.0, "growth_sum": 0.0, "quality_sum": 0.0})
        for a in self._actions:
            by_type[a.courage_type]["count"] += 1
            by_type[a.courage_type]["fear_sum"] += a.fear_level
            by_type[a.courage_type]["growth_sum"] += a.growth
            by_type[a.courage_type]["quality_sum"] += a.outcome_quality

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_fear": round(data["fear_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_quality": round(data["quality_sum"] / count, 2),
            }

        dominant_type = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "fear_sum": 0.0, "growth_sum": 0.0})
        for a in self._actions:
            if a.trigger:
                by_trigger[a.trigger]["count"] += 1
                by_trigger[a.trigger]["fear_sum"] += a.fear_level
                by_trigger[a.trigger]["growth_sum"] += a.growth

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            if count >= 2:
                trigger_stats[tr] = {
                    "count": count,
                    "avg_fear": round(data["fear_sum"] / count, 2),
                    "avg_growth": round(data["growth_sum"] / count, 2),
                }

        best_trigger = max(trigger_stats.items(), key=lambda x: x[1]["avg_growth"]) if trigger_stats else ("", {})

        # Fear-outcome correlation
        high_fear = [a for a in self._actions if a.fear_level > 0.7]
        low_fear = [a for a in self._actions if a.fear_level <= 0.4]
        if high_fear and low_fear:
            high_fear_growth = sum(a.growth for a in high_fear) / len(high_fear)
            low_fear_growth = sum(a.growth for a in low_fear) / len(low_fear)
            fear_growth_correlation = high_fear_growth - low_fear_growth
        else:
            fear_growth_correlation = 0

        # Preparation analysis
        high_prep = [a for a in self._actions if a.preparation > 0.7]
        low_prep = [a for a in self._actions if a.preparation <= 0.4]
        if high_prep and low_prep:
            high_prep_quality = sum(a.outcome_quality for a in high_prep) / len(high_prep)
            low_prep_quality = sum(a.outcome_quality for a in low_prep) / len(low_prep)
        else:
            high_prep_quality = 0
            low_prep_quality = 0

        # Comfort zone expansion
        recent = list(self._actions)[-20:]
        if recent:
            recent_fear = sum(a.fear_level for a in recent) / len(recent)
            recent_growth = sum(a.growth for a in recent) / len(recent)
        else:
            recent_fear = 0
            recent_growth = 0

        older = list(self._actions)[:-20] if len(self._actions) > 20 else []
        if older:
            older_fear = sum(a.fear_level for a in older) / len(older)
            older_growth = sum(a.growth for a in older) / len(older)
            comfort_zone_expansion = recent_fear < older_fear and recent_growth < older_growth
        else:
            comfort_zone_expansion = False

        # Recent trend
        recent_10 = list(self._actions)[-10:]
        if recent_10:
            recent_fear_trend = sum(a.fear_level for a in recent_10) / len(recent_10)
            recent_growth_trend = sum(a.growth for a in recent_10) / len(recent_10)
        else:
            recent_fear_trend = 0
            recent_growth_trend = 0

        return {
            "total_actions": len(self._actions),
            "type_stats": type_stats,
            "dominant_type": dominant_type[0],
            "trigger_stats": trigger_stats,
            "best_trigger": best_trigger[0],
            "fear_growth_correlation": round(fear_growth_correlation, 2),
            "preparation_analysis": {
                "high_prep_quality": round(high_prep_quality, 2),
                "low_prep_quality": round(low_prep_quality, 2),
            },
            "comfort_zone_expansion": comfort_zone_expansion,
            "avg_fear": round(sum(a.fear_level for a in self._actions) / len(self._actions), 2),
            "avg_growth": round(sum(a.growth for a in self._actions) / len(self._actions), 2),
            "avg_quality": round(sum(a.outcome_quality for a in self._actions) / len(self._actions), 2),
            "recent_fear": round(recent_fear_trend, 2),
            "recent_growth": round(recent_growth_trend, 2),
        }

    def get_courage_practice(self, fear_type: str = "", current_courage: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "social": [
                "Say the thing you're afraid to say. To one person. Start there.",
                "Rejection is data, not destiny. Ask for what you want. The worst answer is no.",
                "Speak up in a meeting. Even if your voice shakes. Especially then.",
            ],
            "creative": [
                "Publish something imperfect. The world needs your voice, not your polish.",
                "Share your work before you feel ready. Ready is a myth.",
                "Create the thing that scares you. That's where your growth lives.",
            ],
            "moral": [
                "Stand up for someone who can't stand up for themselves. That's the highest courage.",
                "Tell the truth when a lie would be easier. Integrity is courage in action.",
                "Challenge the group when they're wrong. One dissenting voice is sometimes all it takes.",
            ],
            "existential": [
                "Face the big question you've been avoiding. The one that keeps you up at night.",
                "Make a decision that commits you to a path. Indecision is its own form of fear.",
                "Ask for help. Admitting need is existential courage. We are not meant to be alone.",
            ],
            "emotional": [
                "Feel the feeling you're running from. Set a timer. 5 minutes. Just feel it.",
                "Tell someone you love them. Risk the vulnerability of unrequited expression.",
                "Apologize sincerely. Own your part. That's emotional courage.",
            ],
            "general": [
                "Do one small brave thing today. Courage is a muscle. Small reps build strength.",
                "Fear and excitement share physiology. Reframe your fear as energy.",
                "The 5-second rule: When you feel fear, count down 5-4-3-2-1 and move. Don't let your brain talk you out.",
            ],
        }

        selected = practices.get(fear_type, practices["general"])

        if current_courage < 0.3:
            courage_note = "Courage is low. That's when you need it most. Start with the smallest brave thing."
        elif current_courage < 0.6:
            courage_note = "Building courage. You're in the sweet spot. Keep pushing the edge."
        else:
            courage_note = "Strong courage. Now use it wisely. The bravest thing might be restraint, not action."

        return {
            "fear_type": fear_type or "general",
            "current_courage": current_courage,
            "practice": random.choice(selected),
            "courage_note": courage_note,
            "principle": "Courage is not the absence of fear. It's the decision that something else is more important than fear. The person you become by facing fear is more valuable than the comfort you gain by avoiding it.",
        }

    def get_courage_score(self) -> int:
        """Calculate overall courage health (0-100)."""
        if not self._actions:
            return 30

        # Growth and quality
        avg_growth = sum(a.growth for a in self._actions) / len(self._actions)
        avg_quality = sum(a.outcome_quality for a in self._actions) / len(self._actions)

        # Fear management (not too high, not too low)
        avg_fear = sum(a.fear_level for a in self._actions) / len(self._actions)
        fear_score = 1 - abs(avg_fear - 0.5)  # optimal fear is moderate

        # Preparation
        avg_preparation = sum(a.preparation for a in self._actions) / len(self._actions)

        # Type variety
        unique_types = len(set(a.courage_type for a in self._actions))

        # Recent trend
        recent = list(self._actions)[-10:]
        if recent:
            recent_growth = sum(a.growth for a in recent) / len(recent)
            recent_quality = sum(a.outcome_quality for a in recent) / len(recent)
            recent_fear = sum(a.fear_level for a in recent) / len(recent)
        else:
            recent_growth = 0
            recent_quality = 0
            recent_fear = 0

        # Comfort zone penalty
        older = list(self._actions)[:-20] if len(self._actions) > 20 else []
        if older:
            older_fear = sum(a.fear_level for a in older) / len(older)
            older_growth = sum(a.growth for a in older) / len(older)
            comfort_penalty = 10 if recent_fear < older_fear and recent_growth < older_growth else 0
        else:
            comfort_penalty = 0

        score = (avg_growth * 30) + (avg_quality * 20) + (fear_score * 15) + (avg_preparation * 10) + (unique_types * 2) + (recent_growth * 15) + (recent_quality * 10) - comfort_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._actions:
            self._stats["avg_fear"] = round(sum(a.fear_level for a in self._actions) / len(self._actions), 2)
            self._stats["avg_growth"] = round(sum(a.growth for a in self._actions) / len(self._actions), 2)

            by_type = defaultdict(int)
            for a in self._actions:
                by_type[a.courage_type] += 1
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1])
                self._stats["dominant_type"] = dominant[0]

            recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            older = [a for a in self._actions if a.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
            if recent and older:
                recent_fear = sum(a.fear_level for a in recent) / len(recent)
                older_fear = sum(a.fear_level for a in older) / len(older)
                recent_growth = sum(a.growth for a in recent) / len(recent)
                older_growth = sum(a.growth for a in older) / len(older)
                self._stats["comfort_zone_expansion"] = recent_fear < older_fear and recent_growth < older_growth

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

    def _log_action(self, action: CourageAction):
        try:
            with open(COURAGE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": action.timestamp,
                    "action": action.action,
                    "fear_level": action.fear_level,
                    "courage_type": action.courage_type,
                    "trigger": action.trigger,
                    "preparation": action.preparation,
                    "outcome": action.outcome,
                    "outcome_quality": action.outcome_quality,
                    "growth": action.growth,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cc_instance: Optional[CourageCoach] = None
_cc_lock = threading.Lock()


def get_courage_coach() -> CourageCoach:
    global _cc_instance
    with _cc_lock:
        if _cc_instance is None:
            _cc_instance = CourageCoach()
        return _cc_instance
