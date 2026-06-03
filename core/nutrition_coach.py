"""
LOVE Nutrition Coach — Fuel Intelligence (Modern AI Pattern)

Most nutrition advice is generic and unsustainable. This coach:

1. NUTRITION TRACKING
   - Record meals and their nutritional characteristics
   - Track eating patterns (timing, speed, hunger, fullness)
   - Log energy and mood responses to different foods

2. PATTERN ANALYSIS
   - Identify the user's eating style (intuitive, planned, emotional, social)
   - Find foods that boost energy and those that drain it
   - Detect problematic patterns (skipped meals, emotional eating, restriction)

3. PERSONALIZED GUIDANCE
   - Suggest meals matched to energy needs and preferences
   - Provide mindful eating practices
   - Recommend hydration and meal timing strategies

4. SUSTAINABILITY
   - Track adherence to nutrition intentions
   - Alert when eating patterns are harming wellbeing
   - Celebrate nourishing choices

Architecture:
- record_meal(foods, context, energy_before, energy_after): Log meal
- get_nutrition_stats(): Get nutrition pattern analysis
- get_meal_suggestion(goal, preferences): Get suggestion
- get_nutrition_score(): Calculate overall nutrition health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "nutrition_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NUTRITION_LOG = DATA_DIR / "meals.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MealEntry:
    """A tracked meal entry."""
    entry_id: str = ""
    foods: List[str] = field(default_factory=list)
    meal_type: str = ""  # breakfast, lunch, dinner, snack
    context: str = ""  # planned, intuitive, emotional, social, rushed
    hunger_level: float = 0.5  # 0-1
    fullness_level: float = 0.5  # 0-1
    eating_speed: str = ""  # slow, moderate, fast
    energy_before: float = 0.5  # 0-1
    energy_after: float = 0.5  # 0-1
    mood_after: float = 0.5  # 0-1
    protein_present: bool = False
    vegetables_present: bool = False
    processed_food: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class NutritionCoach:
    """
    Intelligent nutrition coach with personalized guidance and sustainability tracking.
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
            "avg_energy_change": 0.0,
            "meal_pattern": "",
            "problematic_context": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_meal(self, foods: Optional[List[str]] = None, meal_type: str = "", context: str = "", hunger: float = 0.5, fullness: float = 0.5, speed: str = "", energy_before: float = 0.5, energy_after: float = 0.5, mood_after: float = 0.5, protein: bool = False, vegetables: bool = False, processed: bool = False, notes: str = "") -> MealEntry:
        """Record a meal entry."""
        entry_id = f"meal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = MealEntry(
            entry_id=entry_id,
            foods=foods or [],
            meal_type=meal_type or "unspecified",
            context=context or "planned",
            hunger_level=hunger,
            fullness_level=fullness,
            eating_speed=speed,
            energy_before=energy_before,
            energy_after=energy_after,
            mood_after=mood_after,
            protein_present=protein,
            vegetables_present=vegetables,
            processed_food=processed,
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

    def get_nutrition_stats(self) -> Dict[str, Any]:
        """Get nutrition pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "energy_change_sum": 0.0, "mood_sum": 0.0})
        for e in self._entries:
            by_context[e.context]["count"] += 1
            by_context[e.context]["energy_change_sum"] += (e.energy_after - e.energy_before)
            by_context[e.context]["mood_sum"] += e.mood_after

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_energy_change": round(data["energy_change_sum"] / count, 2),
                "avg_mood": round(data["mood_sum"] / count, 2),
            }

        # Meal type analysis
        by_type = defaultdict(lambda: {"count": 0, "energy_change_sum": 0.0, "protein": 0, "veg": 0, "processed": 0})
        for e in self._entries:
            by_type[e.meal_type]["count"] += 1
            by_type[e.meal_type]["energy_change_sum"] += (e.energy_after - e.energy_before)
            if e.protein_present:
                by_type[e.meal_type]["protein"] += 1
            if e.vegetables_present:
                by_type[e.meal_type]["veg"] += 1
            if e.processed_food:
                by_type[e.meal_type]["processed"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_energy_change": round(data["energy_change_sum"] / count, 2),
                "protein_rate": round(data["protein"] / count, 2),
                "veg_rate": round(data["veg"] / count, 2),
                "processed_rate": round(data["processed"] / count, 2),
            }

        # Hunger-fullness balance
        avg_hunger = sum(e.hunger_level for e in self._entries) / len(self._entries)
        avg_fullness = sum(e.fullness_level for e in self._entries) / len(self._entries)
        hunger_fullness_balance = avg_hunger - (1 - avg_fullness)

        # Eating speed analysis
        by_speed = defaultdict(lambda: {"count": 0, "energy_change_sum": 0.0})
        for e in self._entries:
            if e.eating_speed:
                by_speed[e.eating_speed]["count"] += 1
                by_speed[e.eating_speed]["energy_change_sum"] += (e.energy_after - e.energy_before)

        speed_stats = {}
        for s, data in by_speed.items():
            count = data["count"]
            if count >= 2:
                speed_stats[s] = {
                    "count": count,
                    "avg_energy_change": round(data["energy_change_sum"] / count, 2),
                }

        # Problematic context detection
        problematic = [c for c, d in context_stats.items() if d["avg_energy_change"] < -0.2 or d["avg_mood"] < 0.4]

        # Meal skipping detection
        recent_days = defaultdict(set)
        for e in self._entries:
            day = e.timestamp[:10]
            recent_days[day].add(e.meal_type)
        if recent_days:
            avg_meals = sum(len(meals) for meals in recent_days.values()) / len(recent_days)
            skip_risk = avg_meals < 3
        else:
            skip_risk = False

        return {
            "total_entries": len(self._entries),
            "context_stats": context_stats,
            "type_stats": type_stats,
            "avg_hunger": round(avg_hunger, 2),
            "avg_fullness": round(avg_fullness, 2),
            "hunger_fullness_balance": round(hunger_fullness_balance, 2),
            "speed_stats": speed_stats,
            "problematic_contexts": problematic,
            "skip_risk": skip_risk,
            "avg_energy_change": round(sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries), 2),
            "avg_mood": round(sum(e.mood_after for e in self._entries) / len(self._entries), 2),
        }

    def get_meal_suggestion(self, goal: str = "", preferences: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "energy": [
                "Protein + complex carb + healthy fat. E.g., eggs with avocado on whole grain toast.",
                "Smoothie with protein, greens, berries, and nut butter.",
                "Greek yogurt with nuts, seeds, and berries.",
            ],
            "focus": [
                "Omega-3 rich fish with leafy greens. Brain food.",
                "Berries and dark chocolate. Antioxidants for cognition.",
                "Eggs with spinach. Choline and iron for mental clarity.",
            ],
            "recovery": [
                "Salmon with sweet potato and broccoli. Protein + anti-inflammatory.",
                "Turmeric ginger tea with a protein-rich meal.",
                "Bone broth with vegetables. Gut healing + minerals.",
            ],
            "calm": [
                "Warm oatmeal with banana and honey. Comfort + tryptophan.",
                "Herbal tea with a small protein snack. No caffeine.",
                "Soup with root vegetables. Grounding and warm.",
            ],
            "general": [
                "Half plate vegetables, quarter protein, quarter whole grains.",
                "Eat the rainbow. Different colors = different nutrients.",
                "Add one vegetable to every meal, even breakfast.",
            ],
        }

        selected = suggestions.get(goal, suggestions["general"])

        mindful_practices = [
            "Eat without screens. Notice flavors, textures, temperatures.",
            "Put fork down between bites. Chew thoroughly.",
            "Rate hunger before and fullness after. Stop at 7/10.",
            "Drink a glass of water 20 minutes before eating.",
        ]

        return {
            "goal": goal or "general",
            "suggestion": random.choice(selected),
            "mindful_practice": random.choice(mindful_practices),
            "reminder": "Food is fuel, medicine, and pleasure. Don't sacrifice one for the others. Balance is sustainable.",
        }

    def get_nutrition_score(self) -> int:
        """Calculate overall nutrition health (0-100)."""
        if not self._entries:
            return 30

        # Energy response
        avg_energy_change = sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries)

        # Mood
        avg_mood = sum(e.mood_after for e in self._entries) / len(self._entries)

        # Protein and veg
        protein_rate = sum(1 for e in self._entries if e.protein_present) / len(self._entries)
        veg_rate = sum(1 for e in self._entries if e.vegetables_present) / len(self._entries)

        # Low processed
        processed_rate = sum(1 for e in self._entries if e.processed_food) / len(self._entries)

        # Mindful eating (slow, not emotional)
        slow_eating = sum(1 for e in self._entries if e.eating_speed == "slow") / len(self._entries)
        emotional_eating = sum(1 for e in self._entries if e.context == "emotional") / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_energy = sum(e.energy_after - e.energy_before for e in recent) / len(recent)
            recent_mood = sum(e.mood_after for e in recent) / len(recent)
        else:
            recent_energy = 0
            recent_mood = 0

        score = (avg_energy_change * 15) + (avg_mood * 15) + (protein_rate * 15) + (veg_rate * 15) + ((1 - processed_rate) * 10) + (slow_eating * 10) + ((1 - emotional_eating) * 10) + (recent_energy * 5) + (recent_mood * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_energy_change"] = round(sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries), 2)

            by_context = defaultdict(lambda: {"energy_change": 0.0, "count": 0})
            for e in self._entries:
                by_context[e.context]["energy_change"] += (e.energy_after - e.energy_before)
                by_context[e.context]["count"] += 1
            if by_context:
                problematic = min(by_context.items(), key=lambda x: x[1]["energy_change"] / max(1, x[1]["count"]))
                self._stats["problematic_context"] = problematic[0]

            by_type = defaultdict(int)
            for e in self._entries:
                by_type[e.meal_type] += 1
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1])
                self._stats["meal_pattern"] = dominant[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.nutrition_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.nutrition_coach")

    def _log_entry(self, entry: MealEntry):
        try:
            with open(NUTRITION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "meal_type": entry.meal_type,
                    "context": entry.context,
                    "hunger": entry.hunger_level,
                    "fullness": entry.fullness_level,
                    "energy_before": entry.energy_before,
                    "energy_after": entry.energy_after,
                    "mood_after": entry.mood_after,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.nutrition_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_nc_instance: Optional[NutritionCoach] = None
_nc_lock = threading.Lock()


def get_nutrition_coach() -> NutritionCoach:
    global _nc_instance
    with _nc_lock:
        if _nc_instance is None:
            _nc_instance = NutritionCoach()
        return _nc_instance
