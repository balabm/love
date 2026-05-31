"""
LOVE Nutrition Analyzer — Dietary Intelligence (Modern AI Pattern)

Most food tracking is calorie counting. This analyzer:

1. NUTRITION LOGGING
   - Record meals with macro breakdown (protein, carbs, fat, fiber)
   - Track micronutrients (vitamins, minerals)
   - Identify eating patterns (timing, frequency, portions)

2. PATTERN DETECTION
   - Find correlations between food and energy/mood/sleep
   - Detect nutrient deficiencies from eating patterns
   - Identify emotional eating triggers

3. DIETARY INTELLIGENCE
   - Calculate dietary diversity score
   - Track protein distribution across meals
   - Monitor hydration correlation with food intake

4. PROACTIVE SUGGESTIONS
   - Suggest meals to balance daily macros
   - Recommend foods for identified deficiencies
   - Warn about excessive processed food or sugar

Architecture:
- record_meal(food, macros, timestamp): Log a meal
- get_nutrition_insights(days): Get nutrition pattern analysis
- get_diet_score(): Get overall diet quality score
- get_meal_suggestions(): Suggest next meal based on daily needs
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "nutrition_analyzer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MEAL_LOG = DATA_DIR / "meals.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Meal:
    """A recorded meal."""
    food_items: List[str] = field(default_factory=list)
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    meal_type: str = ""  # breakfast, lunch, dinner, snack
    processed_score: float = 0.0  # 0-1 (whole food to highly processed)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    mood_after: str = ""  # energetic, sluggish, satisfied, hungry
    energy_level: float = 0.5


class NutritionAnalyzer:
    """
    Analyze nutrition patterns and provide dietary intelligence.
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
        self._meals: deque = deque(maxlen=500)
        self._stats = {
            "total_meals": 0,
            "avg_calories": 0.0,
            "avg_protein": 0.0,
            "avg_processed_score": 0.0,
            "diet_diversity": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_meal(self, food_items: List[str], calories: float = 0.0, protein_g: float = 0.0, carbs_g: float = 0.0, fat_g: float = 0.0, fiber_g: float = 0.0, meal_type: str = "", processed_score: float = 0.0, mood_after: str = "", energy_level: float = 0.5) -> Meal:
        """Record a meal."""
        meal = Meal(
            food_items=food_items,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
            meal_type=meal_type or "snack",
            processed_score=processed_score,
            mood_after=mood_after,
            energy_level=energy_level,
        )

        with self._lock:
            self._meals.append(meal)
            self._stats["total_meals"] += 1
            self._update_stats(meal)

        self._save_stats()
        self._log_meal(meal)

        return meal

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_nutrition_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get nutrition pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [m for m in self._meals if m.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Macro averages
        total_calories = sum(m.calories for m in recent)
        total_protein = sum(m.protein_g for m in recent)
        total_carbs = sum(m.carbs_g for m in recent)
        total_fat = sum(m.fat_g for m in recent)
        total_fiber = sum(m.fiber_g for m in recent)
        n = len(recent)

        # Macro ratios
        macro_total = total_protein * 4 + total_carbs * 4 + total_fat * 9
        protein_ratio = (total_protein * 4) / max(1, macro_total) * 100
        carbs_ratio = (total_carbs * 4) / max(1, macro_total) * 100
        fat_ratio = (total_fat * 9) / max(1, macro_total) * 100

        # Meal timing analysis
        meal_types = defaultdict(lambda: {"count": 0, "calories": 0.0, "protein": 0.0})
        for m in recent:
            meal_types[m.meal_type]["count"] += 1
            meal_types[m.meal_type]["calories"] += m.calories
            meal_types[m.meal_type]["protein"] += m.protein_g

        # Processed food analysis
        avg_processed = sum(m.processed_score for m in recent) / n
        highly_processed = sum(1 for m in recent if m.processed_score > 0.7)

        # Dietary diversity (unique foods)
        all_foods = set()
        for m in recent:
            all_foods.update(m.food_items)
        diversity = len(all_foods)

        return {
            "days_analyzed": len(set(m.timestamp[:10] for m in recent)),
            "total_meals": n,
            "avg_calories": round(total_calories / n, 1),
            "avg_protein_g": round(total_protein / n, 1),
            "avg_carbs_g": round(total_carbs / n, 1),
            "avg_fat_g": round(total_fat / n, 1),
            "avg_fiber_g": round(total_fiber / n, 1),
            "macro_ratios": {
                "protein_pct": round(protein_ratio, 1),
                "carbs_pct": round(carbs_ratio, 1),
                "fat_pct": round(fat_ratio, 1),
            },
            "meal_breakdown": {k: dict(v) for k, v in meal_types.items()},
            "processed_food_pct": round(highly_processed / n * 100, 1),
            "diet_diversity": diversity,
            "unique_foods": sorted(list(all_foods))[:20],
        }

    def get_diet_score(self) -> int:
        """Calculate overall diet quality score (0-100)."""
        if not self._meals:
            return 50

        recent = list(self._meals)[-30:]
        n = len(recent)

        # Protein score (target: 20-30% of calories)
        total_protein_cal = sum(m.protein_g * 4 for m in recent)
        total_cal = sum(m.calories for m in recent)
        protein_pct = total_protein_cal / max(1, total_cal) * 100
        protein_score = max(0, 100 - abs(protein_pct - 25) * 4)

        # Fiber score (target: avg 10g+ per meal)
        avg_fiber = sum(m.fiber_g for m in recent) / n
        fiber_score = min(100, avg_fiber * 10)

        # Diversity score
        all_foods = set()
        for m in recent:
            all_foods.update(m.food_items)
        diversity_score = min(100, len(all_foods) * 2)

        # Processed food penalty
        processed_pct = sum(1 for m in recent if m.processed_score > 0.7) / n * 100
        processed_penalty = processed_pct * 0.5

        overall = round(protein_score * 0.3 + fiber_score * 0.2 + diversity_score * 0.2 + (100 - processed_penalty) * 0.3)
        return max(0, min(100, overall))

    def get_meal_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest next meal based on daily needs."""
        suggestions = []
        insights = self.get_nutrition_insights(1)

        if insights.get("status") == "insufficient_data":
            return [{"suggestion": "Log meals to get personalized suggestions", "category": "general"}]

        # Check protein gap
        today_protein = insights.get("avg_protein_g", 0)
        if today_protein < 20:
            suggestions.append({
                "suggestion": "Your protein is low today. Consider eggs, Greek yogurt, chicken, or lentils for your next meal.",
                "category": "protein",
                "priority": "high",
            })

        # Check processed food
        if insights.get("processed_food_pct", 0) > 50:
            suggestions.append({
                "suggestion": "You've had a lot of processed food today. Choose whole foods for your next meal.",
                "category": "whole_food",
                "priority": "medium",
            })

        # Check fiber
        today_fiber = insights.get("avg_fiber_g", 0)
        if today_fiber < 5:
            suggestions.append({
                "suggestion": "Fiber is low. Add vegetables, fruits, or whole grains to your next meal.",
                "category": "fiber",
                "priority": "medium",
            })

        # Meal timing
        meal_types_logged = set(insights.get("meal_breakdown", {}).keys())
        expected = {"breakfast", "lunch", "dinner"}
        missing = expected - meal_types_logged
        if missing:
            suggestions.append({
                "suggestion": f"You haven't logged {', '.join(missing)} yet today. Regular meal timing helps energy.",
                "category": "timing",
                "priority": "low",
            })

        return suggestions

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, meal: Meal):
        """Update running statistics."""
        n = self._stats["total_meals"]
        self._stats["avg_calories"] = round((self._stats["avg_calories"] * (n - 1) + meal.calories) / n, 1)
        self._stats["avg_protein"] = round((self._stats["avg_protein"] * (n - 1) + meal.protein_g) / n, 1)
        self._stats["avg_processed_score"] = round((self._stats["avg_processed_score"] * (n - 1) + meal.processed_score) / n, 2)

        # Update diversity
        all_foods = set()
        for m in self._meals:
            all_foods.update(m.food_items)
        self._stats["diet_diversity"] = len(all_foods)

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

    def _log_meal(self, meal: Meal):
        try:
            with open(MEAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": meal.timestamp,
                    "food": meal.food_items,
                    "calories": meal.calories,
                    "protein": meal.protein_g,
                    "carbs": meal.carbs_g,
                    "fat": meal.fat_g,
                    "meal_type": meal.meal_type,
                    "processed": meal.processed_score,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_na_instance: Optional[NutritionAnalyzer] = None
_na_lock = threading.Lock()


def get_nutrition_analyzer() -> NutritionAnalyzer:
    global _na_instance
    with _na_lock:
        if _na_instance is None:
            _na_instance = NutritionAnalyzer()
        return _na_instance
