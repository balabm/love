"""
LOVE Meal Ritual Designer — Ritual Intelligence (Modern AI Pattern)

Most people eat on autopilot. This designer:

1. RITUAL TRACKING
   - Record meal ritual moments and their characteristics
   - Track ritual types (setting, beginning, gratitude, connection, closing, cleanup)
   - Log intention, atmosphere, meaning, and continuity of rituals

2. PATTERN ANALYSIS
   - Identify the user's ritual profile (absent, rushed, developing, sacred)
   - Find ritual patterns that create meaning vs emptiness
   - Detect chronic ritual absence and its costs

3. RITUAL BUILDING
   - Suggest practices for creating meaningful meal rituals
   - Provide frameworks for table setting, gratitude, and presence
   - Recommend practices for ritual as grounding practice

4. SACRED ORDINARY CULTIVATION
   - Track the correlation between ritual and life meaning
   - Alert when meals are becoming purely functional
   - Celebrate moments of genuine ritual beauty

Architecture:
- record_ritual(meal, type, intention, atmosphere, meaning, continuity): Log ritual
- get_ritual_stats(): Get ritual pattern analysis
- get_ritual_suggestion(capacity, context): Get suggestion
- get_ritual_score(): Calculate overall ritual health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "meal_ritual_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RITUAL_LOG = DATA_DIR / "rituals.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RitualEntry:
    """A tracked meal ritual moment."""
    entry_id: str = ""
    meal: str = ""  # what meal was ritualized
    ritual_type: str = ""  # setting, beginning, gratitude, connection, closing, cleanup
    intention: float = 0.0  # 0-1
    atmosphere: float = 0.0  # 0-1
    meaning: float = 0.0  # 0-1
    continuity: float = 0.0  # 0-1 did you maintain the ritual?
    presence: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MealRitualDesigner:
    """
    Intelligent meal ritual designer with absence detection and sacred ordinary cultivation.
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
            "avg_intention": 0.0,
            "avg_meaning": 0.0,
            "absence_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_ritual(self, meal: str = "", ritual_type: str = "", intention: float = 0.0, atmosphere: float = 0.0, meaning: float = 0.0, continuity: float = 0.0, presence: float = 0.0, notes: str = "") -> RitualEntry:
        """Record a meal ritual moment."""
        entry_id = f"rtl_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RitualEntry(
            entry_id=entry_id,
            meal=meal or "unspecified",
            ritual_type=ritual_type or "beginning",
            intention=intention,
            atmosphere=atmosphere,
            meaning=meaning,
            continuity=continuity,
            presence=presence,
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

    def get_ritual_stats(self) -> Dict[str, Any]:
        """Get ritual pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intention_sum": 0.0, "atmosphere_sum": 0.0, "meaning_sum": 0.0})
        for e in self._entries:
            by_type[e.ritual_type]["count"] += 1
            by_type[e.ritual_type]["intention_sum"] += e.intention
            by_type[e.ritual_type]["atmosphere_sum"] += e.atmosphere
            by_type[e.ritual_type]["meaning_sum"] += e.meaning

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intention": round(data["intention_sum"] / count, 2),
                "avg_atmosphere": round(data["atmosphere_sum"] / count, 2),
                "avg_meaning": round(data["meaning_sum"] / count, 2),
            }

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_mean = sum(e.meaning for e in high_int) / len(high_int)
            low_int_mean = sum(e.meaning for e in low_int) / len(low_int)
            high_int_atm = sum(e.atmosphere for e in high_int) / len(high_int)
            low_int_atm = sum(e.atmosphere for e in low_int) / len(low_int)
        else:
            high_int_mean = 0
            low_int_mean = 0
            high_int_atm = 0
            low_int_atm = 0

        # Continuity analysis
        high_cont = [e for e in self._entries if e.continuity > 0.7]
        low_cont = [e for e in self._entries if e.continuity < 0.4]
        if high_cont and low_cont:
            high_cont_mean = sum(e.meaning for e in high_cont) / len(high_cont)
            low_cont_mean = sum(e.meaning for e in low_cont) / len(low_cont)
        else:
            high_cont_mean = 0
            low_cont_mean = 0

        # Absence risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_int = sum(e.intention for e in recent) / len(recent)
            recent_mean = sum(e.meaning for e in recent) / len(recent)
            absence_risk = recent_int < 0.3 and recent_mean < 0.3
        else:
            absence_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "intention_impact": {
                "high_intention_meaning": round(high_int_mean, 2),
                "low_intention_meaning": round(low_int_mean, 2),
                "high_intention_atmosphere": round(high_int_atm, 2),
                "low_intention_atmosphere": round(low_int_atm, 2),
            },
            "continuity_effect": {
                "high_continuity_meaning": round(high_cont_mean, 2),
                "low_continuity_meaning": round(low_cont_mean, 2),
            },
            "absence_risk": absence_risk,
            "avg_intention": round(sum(e.intention for e in self._entries) / len(self._entries), 2),
            "avg_meaning": round(sum(e.meaning for e in self._entries) / len(self._entries), 2),
        }

    def get_ritual_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get ritual suggestion."""
        suggestions = [
            "Rituals are not superstition. They're structure. They're meaning. They're the difference between a meal and a communion. Between eating and nourishing. Between surviving and living.",
            "Set the table. Even for one. A placemat. A napkin. A glass. Not because you're fancy. Because you're worth the effort. Because the ordinary deserves the extraordinary.",
            "Pause before eating. One breath. Two breaths. Notice the food. The colors. The steam. The aroma. This pause is the ritual. It transforms consumption into nourishment.",
            "Say gratitude. Not a prayer if that's not your thing. Just acknowledgment. 'This is good.' 'I'm lucky.' 'Someone grew this. Someone cooked this.' Gratitude is the first ritual.",
            "Light a candle. Or dim the lights. Or play music. Create an atmosphere. The environment shapes the experience. And the experience shapes the memory. And the memory shapes the life.",
            "Eat at the table. Not the desk. Not the couch. Not the car. The table is the altar. The meal is the offering. You are the priest. And the congregation. And the god.",
            "Clean up with care. Wash the dishes with attention. Dry them gently. Put them away. The closing ritual is as important as the opening. It completes the circle. It honors the experience.",
            "Create one consistent ritual. The same thing every meal. A phrase. A gesture. A moment. Consistency creates meaning. And meaning creates sacredness. Even in scrambled eggs.",
            "Invite someone into your ritual. Share a meal. Share the pause. Share the gratitude. Rituals are bridges. Between people. Between moments. Between the mundane and the meaningful.",
            "The person who eats with ritual eats with reverence. And reverence is the opposite of麻木 (numbness). It's the antidote to autopilot. It's the practice of being alive. One meal at a time."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One breath before eating. One thank you. One moment of setting the table. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A gratitude practice. An atmosphere created. A closing ritual added. Medium design."
        else:
            capacity_note = "Good capacity. Deep ritual work. A systematic practice of sacred ordinary moments. You have the strength to make every meal a communion."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Meal rituals are the practice of making the ordinary sacred. Most people eat like they're refueling a car. Quick. Functional. Forgettable. And they wonder why they feel empty. Why their days blur together. Why nothing feels special. The work of meal ritual design is about creating structure and meaning around the most repeated activity of human life: eating. It's about setting the table with intention. About pausing before the first bite. About expressing gratitude. About creating atmosphere. About closing with care. And about understanding that rituals don't require religion. They require attention. They require repetition. They require meaning. And they transform the mundane into the memorable. The person who eats with ritual is not just nourishing their body. They're nourishing their soul. One meal at a time."
        }

    def get_ritual_score(self) -> int:
        """Calculate overall ritual health (0-100)."""
        if not self._entries:
            return 25

        avg_int = sum(e.intention for e in self._entries) / len(self._entries)
        avg_atm = sum(e.atmosphere for e in self._entries) / len(self._entries)
        avg_mean = sum(e.meaning for e in self._entries) / len(self._entries)
        avg_cont = sum(e.continuity for e in self._entries) / len(self._entries)
        avg_pres = sum(e.presence for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_int = sum(e.intention for e in recent) / len(recent)
            recent_mean = sum(e.meaning for e in recent) / len(recent)
        else:
            recent_int = 0
            recent_mean = 0

        # Absence penalty
        abs_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_int_30 = sum(e.intention for e in last_30) / len(last_30)
            recent_mean_30 = sum(e.meaning for e in last_30) / len(last_30)
            if recent_int_30 < 0.3 and recent_mean_30 < 0.3:
                abs_penalty = 15

        # Type variety
        unique_types = len(set(e.ritual_type for e in self._entries))

        score = (avg_int * 25) + (avg_atm * 15) + (avg_mean * 20) + (avg_cont * 15) + (avg_pres * 10) + (recent_int * 5) + (recent_mean * 5) + (unique_types * 2) - abs_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intention"] = round(sum(e.intention for e in self._entries) / len(self._entries), 2)
            self._stats["avg_meaning"] = round(sum(e.meaning for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_int = sum(e.intention for e in recent) / len(recent)
                recent_mean = sum(e.meaning for e in recent) / len(recent)
                self._stats["absence_risk"] = recent_int < 0.3 and recent_mean < 0.3
            else:
                self._stats["absence_risk"] = False

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

    def _log_entry(self, entry: RitualEntry):
        try:
            with open(RITUAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "meal": entry.meal,
                    "ritual_type": entry.ritual_type,
                    "intention": entry.intention,
                    "meaning": entry.meaning,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mrd_instance: Optional[MealRitualDesigner] = None
_mrd_lock = threading.Lock()


def get_meal_ritual_designer() -> MealRitualDesigner:
    global _mrd_instance
    with _mrd_lock:
        if _mrd_instance is None:
            _mrd_instance = MealRitualDesigner()
        return _mrd_instance
