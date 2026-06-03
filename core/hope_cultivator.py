"""
LOVE Hope Cultivator — Future Intelligence (Modern AI Pattern)

Most people lose hope under pressure and don't notice. This cultivator:

1. HOPE TRACKING
   - Record hope experiences and their characteristics
   - Track hope types (agency, pathway, motivational, relational, spiritual)
   - Log strength, clarity, and action from hope

2. PATTERN ANALYSIS
   - Identify the user's hope profile (hopeful, despairing, realistic, fragile)
   - Find hope patterns that create resilience and action
   - Detect hopelessness and its warning signs

3. HOPE BUILDING
   - Suggest hope practices matched to current circumstances and capacity
   - Provide frameworks for realistic optimism
   - Recommend small wins that rebuild agency

4. POSSIBILITY CULTIVATION
   - Track the correlation between hope and wellbeing
   - Alert when despair is becoming normalized
   - Celebrate moments of genuine hope and possibility

Architecture:
- record_hope(hope, type, strength, clarity, action): Log hope
- get_hope_stats(): Get hope pattern analysis
- get_hope_suggestion(capacity, context): Get suggestion
- get_hope_score(): Calculate overall hope health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "hope_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HOPE_LOG = DATA_DIR / "hope.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class HopeEntry:
    """A tracked hope experience."""
    entry_id: str = ""
    hope: str = ""  # what was hoped for
    hope_type: str = ""  # agency, pathway, motivational, relational, spiritual
    strength: float = 0.5  # 0-1
    clarity: float = 0.0  # 0-1
    action: float = 0.0  # 0-1
    support: float = 0.0  # 0-1
    meaning: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HopeCultivator:
    """
    Intelligent hope cultivator with strength detection and possibility cultivation.
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
            "avg_strength": 0.0,
            "avg_action": 0.0,
            "hopelessness_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_hope(self, hope: str = "", hope_type: str = "", strength: float = 0.5, clarity: float = 0.0, action: float = 0.0, support: float = 0.0, meaning: float = 0.0, notes: str = "") -> HopeEntry:
        """Record a hope experience."""
        entry_id = f"hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = HopeEntry(
            entry_id=entry_id,
            hope=hope or "unspecified",
            hope_type=hope_type or "motivational",
            strength=strength,
            clarity=clarity,
            action=action,
            support=support,
            meaning=meaning,
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

    def get_hope_stats(self) -> Dict[str, Any]:
        """Get hope pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "strength_sum": 0.0, "action_sum": 0.0, "clarity_sum": 0.0})
        for e in self._entries:
            by_type[e.hope_type]["count"] += 1
            by_type[e.hope_type]["strength_sum"] += e.strength
            by_type[e.hope_type]["action_sum"] += e.action
            by_type[e.hope_type]["clarity_sum"] += e.clarity

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_strength": round(data["strength_sum"] / count, 2),
                "avg_action": round(data["action_sum"] / count, 2),
                "avg_clarity": round(data["clarity_sum"] / count, 2),
            }

        # Strength analysis
        high_strength = [e for e in self._entries if e.strength > 0.7]
        low_strength = [e for e in self._entries if e.strength < 0.4]
        if high_strength and low_strength:
            high_str_act = sum(e.action for e in high_strength) / len(high_strength)
            low_str_act = sum(e.action for e in low_strength) / len(low_strength)
            high_str_mean = sum(e.meaning for e in high_strength) / len(high_strength)
            low_str_mean = sum(e.meaning for e in low_strength) / len(low_strength)
        else:
            high_str_act = 0
            low_str_act = 0
            high_str_mean = 0
            low_str_mean = 0

        # Clarity analysis
        high_clarity = [e for e in self._entries if e.clarity > 0.7]
        low_clarity = [e for e in self._entries if e.clarity < 0.4]
        if high_clarity and low_clarity:
            high_clar_act = sum(e.action for e in high_clarity) / len(high_clarity)
            low_clar_act = sum(e.action for e in low_clarity) / len(low_clarity)
        else:
            high_clar_act = 0
            low_clar_act = 0

        # Hopelessness risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_strength = sum(e.strength for e in recent) / len(recent)
            recent_action = sum(e.action for e in recent) / len(recent)
            recent_meaning = sum(e.meaning for e in recent) / len(recent)
            hopelessness_risk = recent_strength < 0.3 and recent_action < 0.3 and recent_meaning < 0.3
        else:
            hopelessness_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "strength_impact": {
                "high_strength_action": round(high_str_act, 2),
                "low_strength_action": round(low_str_act, 2),
                "high_strength_meaning": round(high_str_mean, 2),
                "low_strength_meaning": round(low_str_mean, 2),
            },
            "clarity_effect": {
                "high_clarity_action": round(high_clar_act, 2),
                "low_clarity_action": round(low_clar_act, 2),
            },
            "hopelessness_risk": hopelessness_risk,
            "avg_strength": round(sum(e.strength for e in self._entries) / len(self._entries), 2),
            "avg_action": round(sum(e.action for e in self._entries) / len(self._entries), 2),
        }

    def get_hope_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get hope suggestion."""
        suggestions = [
            "Hope is not optimism. Optimism is the belief that things will get better. Hope is the belief that things can get better, and that your actions matter. Hope is harder. And more powerful.",
            "Find one thing you can control. Just one. A meal. A walk. A conversation. Agency is the antidote to despair. Control something. Even something small.",
            "Remember when you survived before. You've been through hard things. You've made it. That wasn't luck. That was you. You have evidence of resilience.",
            "Hope needs company. Despair isolates. Reach out. To a friend. A family member. A professional. Hope is easier to hold when someone else is holding it with you.",
            "Create a small win. Something achievable today. Send an email. Make a call. Clean a surface. Small wins rebuild the pathway to bigger wins.",
            "Visualize a possible future. Not a perfect one. A possible one. One where things are a little better. The brain needs a target. Give it one.",
            "Help someone else. Nothing restores hope faster than being useful to someone else. Your problems shrink when you're focused on someone else's.",
            "Read about people who made it through. Biographies. Stories. Documentaries. Other people's hope becomes your hope. You're not the first person to struggle.",
            "Hope is not a feeling. It's a practice. You don't wait to feel hopeful. You act as if things can get better. And then they often do.",
            "The darkest hour is not the end. It's the middle. The part where you're tired and can't see the exit. Keep walking. The exit is closer than it looks."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small hope. One small action. One small possibility. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A meaningful step. A plan. A conversation. Medium investment in possibility."
        else:
            capacity_note = "Good capacity. A major vision. A significant step. A bold move. You have the energy to build real hope."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Hope is the belief that the future contains possibilities worth working toward. It's not the same as optimism. Optimism is passive. Hope is active. Optimism says things will be fine. Hope says things can be better, and I can contribute to that. Hope is not a denial of reality. It's a refusal to accept that the current reality is the only possible reality. The most powerful thing about hope is that it's contagious. One person's hope can spark another's. And collective hope is the engine of all social change. Cultivate hope. Not as denial. As strategy. As practice. As resistance against despair."
        }

    def get_hope_score(self) -> int:
        """Calculate overall hope health (0-100)."""
        if not self._entries:
            return 25

        avg_strength = sum(e.strength for e in self._entries) / len(self._entries)
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_action = sum(e.action for e in self._entries) / len(self._entries)
        avg_support = sum(e.support for e in self._entries) / len(self._entries)
        avg_meaning = sum(e.meaning for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_strength = sum(e.strength for e in recent) / len(recent)
            recent_action = sum(e.action for e in recent) / len(recent)
        else:
            recent_strength = 0
            recent_action = 0

        # Hopelessness penalty
        hopeless_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_strength_30 = sum(e.strength for e in last_30) / len(last_30)
            recent_action_30 = sum(e.action for e in last_30) / len(last_30)
            recent_meaning_30 = sum(e.meaning for e in last_30) / len(last_30)
            if recent_strength_30 < 0.3 and recent_action_30 < 0.3 and recent_meaning_30 < 0.3:
                hopeless_penalty = 15

        # Type variety
        unique_types = len(set(e.hope_type for e in self._entries))

        score = (avg_strength * 25) + (avg_clarity * 15) + (avg_action * 25) + (avg_support * 10) + (avg_meaning * 10) + (recent_strength * 5) + (recent_action * 5) + (unique_types * 2) - hopeless_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_strength"] = round(sum(e.strength for e in self._entries) / len(self._entries), 2)
            self._stats["avg_action"] = round(sum(e.action for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_strength = sum(e.strength for e in recent) / len(recent)
                recent_action = sum(e.action for e in recent) / len(recent)
                recent_meaning = sum(e.meaning for e in recent) / len(recent)
                self._stats["hopelessness_risk"] = recent_strength < 0.3 and recent_action < 0.3 and recent_meaning < 0.3
            else:
                self._stats["hopelessness_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.hope_cultivator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.hope_cultivator")

    def _log_entry(self, entry: HopeEntry):
        try:
            with open(HOPE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "hope": entry.hope,
                    "hope_type": entry.hope_type,
                    "strength": entry.strength,
                    "action": entry.action,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.hope_cultivator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hc_instance: Optional[HopeCultivator] = None
_hc_lock = threading.Lock()


def get_hope_cultivator() -> HopeCultivator:
    global _hc_instance
    with _hc_lock:
        if _hc_instance is None:
            _hc_instance = HopeCultivator()
        return _hc_instance
