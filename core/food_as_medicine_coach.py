"""
LOVE Food as Medicine Coach — Nutritional Intelligence (Modern AI Pattern)

Most people treat food as calories. This coach:

1. FOOD TRACKING
   - Record food-medicine moments and their characteristics
   - Track food types (anti-inflammatory, energizing, calming, gut-healing, immune, brain)
   - Log effect, symptom, intention, and healing quality of food

2. PATTERN ANALYSIS
   - Identify the user's nutritional profile (reactive, conventional, developing, therapeutic)
   - Find food patterns that heal vs harm
   - Detect chronic inflammatory eating and its costs

3. HEALING BUILDING
   - Suggest practices for using food as medicine
   - Provide frameworks for symptom-based eating
   - Recommend practices for food-based prevention

4. THERAPEUTIC NUTRITION CULTIVATION
   - Track the correlation between food choices and body symptoms
   - Alert when inflammatory patterns are dominating
   - Celebrate moments of genuine food-based healing

Architecture:
- record_food(food, type, effect, symptom, intention, healing): Log food
- get_food_stats(): Get food pattern analysis
- get_food_suggestion(capacity, context): Get suggestion
- get_food_score(): Calculate overall food health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "food_as_medicine_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FOOD_LOG = DATA_DIR / "foods.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class FoodEntry:
    """A tracked food-medicine moment."""
    entry_id: str = ""
    food: str = ""  # what was eaten
    food_type: str = ""  # anti-inflammatory, energizing, calming, gut-healing, immune, brain
    effect: float = 0.0  # 0-1
    symptom: float = 0.0  # 0-1 severity of symptom addressed
    intention: float = 0.0  # 0-1
    healing: float = 0.0  # 0-1
    prevention: float = 0.0  # 0-1 was it preventive?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class FoodAsMedicineCoach:
    """
    Intelligent food as medicine coach with inflammation detection and therapeutic nutrition cultivation.
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
            "avg_effect": 0.0,
            "avg_healing": 0.0,
            "inflammation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_food(self, food: str = "", food_type: str = "", effect: float = 0.0, symptom: float = 0.0, intention: float = 0.0, healing: float = 0.0, prevention: float = 0.0, notes: str = "") -> FoodEntry:
        """Record a food-medicine moment."""
        entry_id = f"fmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = FoodEntry(
            entry_id=entry_id,
            food=food or "unspecified",
            food_type=food_type or "anti-inflammatory",
            effect=effect,
            symptom=symptom,
            intention=intention,
            healing=healing,
            prevention=prevention,
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

    def get_food_stats(self) -> Dict[str, Any]:
        """Get food pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "effect_sum": 0.0, "healing_sum": 0.0, "symptom_sum": 0.0})
        for e in self._entries:
            by_type[e.food_type]["count"] += 1
            by_type[e.food_type]["effect_sum"] += e.effect
            by_type[e.food_type]["healing_sum"] += e.healing
            by_type[e.food_type]["symptom_sum"] += e.symptom

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
                "avg_healing": round(data["healing_sum"] / count, 2),
                "avg_symptom": round(data["symptom_sum"] / count, 2),
            }

        # Effect analysis
        high_eff = [e for e in self._entries if e.effect > 0.7]
        low_eff = [e for e in self._entries if e.effect < 0.4]
        if high_eff and low_eff:
            high_eff_heal = sum(e.healing for e in high_eff) / len(high_eff)
            low_eff_heal = sum(e.healing for e in low_eff) / len(low_eff)
            high_eff_sym = sum(e.symptom for e in high_eff) / len(high_eff)
            low_eff_sym = sum(e.symptom for e in low_eff) / len(low_eff)
        else:
            high_eff_heal = 0
            low_eff_heal = 0
            high_eff_sym = 0
            low_eff_sym = 0

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_eff = sum(e.effect for e in high_int) / len(high_int)
            low_int_eff = sum(e.effect for e in low_int) / len(low_int)
        else:
            high_int_eff = 0
            low_int_eff = 0

        # Inflammation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_eff = sum(e.effect for e in recent) / len(recent)
            recent_heal = sum(e.healing for e in recent) / len(recent)
            inflammation_risk = recent_eff < 0.3 and recent_heal < 0.3
        else:
            inflammation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "effect_impact": {
                "high_effect_healing": round(high_eff_heal, 2),
                "low_effect_healing": round(low_eff_heal, 2),
                "high_effect_symptom": round(high_eff_sym, 2),
                "low_effect_symptom": round(low_eff_sym, 2),
            },
            "intention_effect": {
                "high_intention_effect": round(high_int_eff, 2),
                "low_intention_effect": round(low_int_eff, 2),
            },
            "inflammation_risk": inflammation_risk,
            "avg_effect": round(sum(e.effect for e in self._entries) / len(self._entries), 2),
            "avg_healing": round(sum(e.healing for e in self._entries) / len(self._entries), 2),
        }

    def get_food_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get food suggestion."""
        suggestions = [
            "Food is medicine. Not metaphorically. Literally. Every bite either heals or harms. Every meal either reduces inflammation or increases it. Every choice either supports your body or taxes it. Choose.",
            "Notice how food makes you feel. Not just while eating. After. An hour later. The next morning. Some foods energize. Some deplete. Some inflame. Some heal. Your body is giving you data. Listen.",
            "Eat for your symptoms. Stressed? Calming foods. Tired? Energizing foods. Inflamed? Anti-inflammatory foods. Your body is asking for specific things. Learn the language. Respond.",
            "Prevention is easier than cure. The foods that prevent illness are the same foods that heal it. Vegetables. Fruits. Whole grains. Healthy fats. Fermented foods. Eat them before you need them.",
            "Gut health is brain health. Your gut microbiome produces neurotransmitters. Regulates mood. Influences cognition. Feed it well. Fermented foods. Fiber. Diversity. Your gut is your second brain. Treat it well.",
            "Don't fight your cravings. Understand them. Craving sugar? Maybe you need energy. Craving salt? Maybe you're stressed. Craving crunch? Maybe you're angry. The craving is information. Decode it. Then choose wisely.",
            "One healing meal is not enough. Consistency is the medicine. The person who eats anti-inflammatory foods once a month gets no benefit. The person who eats them daily transforms their health. Be consistent.",
            "Cook your medicine. Don't buy it in a pill. The act of cooking is part of the healing. The intention. The attention. The transformation of raw ingredients into nourishment. That's medicine too.",
            "Food connects you to place. To season. To earth. To farmers. To tradition. To culture. Eating locally. Eating seasonally. Eating traditionally. These are not trends. They're wisdom. And they're healing.",
            "The person who treats food as medicine is not obsessive. They're wise. They understand that what they eat becomes what they are. Every cell. Every thought. Every mood. Food is the foundation. Build well."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One healing food chosen. One symptom noticed. One meal eaten with intention. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A symptom-based meal plan. An anti-inflammatory practice. A gut-healing food added. Medium medicine."
        else:
            capacity_note = "Good capacity. Deep therapeutic nutrition work. A systematic practice of food as medicine. You have the strength to heal yourself with every bite."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Food as medicine is not a new idea. It's the oldest idea. Every traditional culture has used food for healing. Before pharmaceuticals. Before supplements. Before doctors. There was food. And it worked. The modern world has forgotten this. We treat food as fuel. As calories. As macronutrients. And we treat disease as something to be fixed with pills. But the body is not a machine to be repaired. It's an ecosystem to be nourished. And food is the primary input. The work of food as medicine coaching is about reconnecting with the healing power of food. About noticing what foods heal you and what foods harm you. About eating preventively. About understanding that every meal is an opportunity for healing. And about recognizing that the person who treats food as medicine is not being extreme. They're being wise. Because food is the most powerful medicine available. And it's available to everyone. Three times a day."
        }

    def get_food_score(self) -> int:
        """Calculate overall food health (0-100)."""
        if not self._entries:
            return 25

        avg_eff = sum(e.effect for e in self._entries) / len(self._entries)
        avg_sym = sum(e.symptom for e in self._entries) / len(self._entries)
        avg_int = sum(e.intention for e in self._entries) / len(self._entries)
        avg_heal = sum(e.healing for e in self._entries) / len(self._entries)
        avg_prev = sum(e.prevention for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_eff = sum(e.effect for e in recent) / len(recent)
            recent_heal = sum(e.healing for e in recent) / len(recent)
        else:
            recent_eff = 0
            recent_heal = 0

        # Inflammation penalty
        infl_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_eff_30 = sum(e.effect for e in last_30) / len(last_30)
            recent_heal_30 = sum(e.healing for e in last_30) / len(last_30)
            if recent_eff_30 < 0.3 and recent_heal_30 < 0.3:
                infl_penalty = 15

        # Type variety
        unique_types = len(set(e.food_type for e in self._entries))

        score = (avg_eff * 25) + (avg_heal * 20) + (avg_int * 15) + (avg_prev * 15) + (recent_eff * 5) + (recent_heal * 5) + (unique_types * 2) - (avg_sym * 5) - infl_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_effect"] = round(sum(e.effect for e in self._entries) / len(self._entries), 2)
            self._stats["avg_healing"] = round(sum(e.healing for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_eff = sum(e.effect for e in recent) / len(recent)
                recent_heal = sum(e.healing for e in recent) / len(recent)
                self._stats["inflammation_risk"] = recent_eff < 0.3 and recent_heal < 0.3
            else:
                self._stats["inflammation_risk"] = False

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

    def _log_entry(self, entry: FoodEntry):
        try:
            with open(FOOD_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "food": entry.food,
                    "food_type": entry.food_type,
                    "effect": entry.effect,
                    "healing": entry.healing,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_fmc_instance: Optional[FoodAsMedicineCoach] = None
_fmc_lock = threading.Lock()


def get_food_as_medicine_coach() -> FoodAsMedicineCoach:
    global _fmc_instance
    with _fmc_lock:
        if _fmc_instance is None:
            _fmc_instance = FoodAsMedicineCoach()
        return _fmc_instance
