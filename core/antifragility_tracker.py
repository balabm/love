"""
LOVE Antifragility Tracker — Stress-to-Strength Intelligence (Modern AI Pattern)

Most systems are fragile or robust. This tracker:

1. ANTIFRAGILITY TRACKING
   - Record stressors and whether they made the user weaker, same, or stronger
   - Track voluntary stress (hormesis) and its effects
   - Log recovery quality after stress exposure

2. PATTERN ANALYSIS
   - Identify the user's antifragile domains (where stress builds strength)
   - Find fragility zones (where stress causes damage)
   - Detect optimal stress-recovery balance

3. HORMESIS GUIDANCE
   - Suggest controlled stress exposures for growth
   - Provide recovery protocols after stress
   - Recommend stress type/dose based on current capacity

4. GROWTH TRACKING
   - Track strength gains from past stressors
   - Celebrate when difficulty led to growth
   - Alert when stress is accumulating without recovery

Architecture:
- record_stressor(stressor, type, dose, effect): Log stressor
- get_antifragility_stats(): Get antifragility pattern analysis
- get_hormesis_suggestion(current_capacity, goal): Get controlled stress
- get_antifragility_score(): Calculate overall antifragility health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "antifragility_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STRESSOR_LOG = DATA_DIR / "stressors.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Stressor:
    """A tracked stressor and its effect."""
    stressor_id: str = ""
    stressor: str = ""
    stressor_type: str = ""  # physical, mental, emotional, social, creative, financial, voluntary, involuntary
    dose: str = ""  # micro, small, moderate, high, extreme
    duration_hours: float = 0.0
    effect: str = ""  # weaker, same, stronger, damaged, broke
    recovery_quality: float = 0.5  # 0-1
    recovery_time_hours: float = 0.0
    pre_capacity: float = 0.5  # 0-1
    post_capacity: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AntifragilityTracker:
    """
    Intelligent antifragility tracker with stress pattern analysis and hormesis guidance.
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
        self._stressors: deque = deque(maxlen=200)
        self._stats = {
            "total_stressors": 0,
            "stronger_rate": 0.0,
            "avg_recovery": 0.0,
            "fragile_types": [],
            "antifragile_types": [],
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_stressor(self, stressor: str = "", stressor_type: str = "", dose: str = "", duration: float = 0, effect: str = "", recovery_quality: float = 0.5, recovery_time: float = 0, pre_capacity: float = 0.5, post_capacity: float = 0.5, notes: str = "") -> Stressor:
        """Record a stressor."""
        stressor_id = f"stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._stressors)}"
        s = Stressor(
            stressor_id=stressor_id,
            stressor=stressor or "unspecified",
            stressor_type=stressor_type or "mental",
            dose=dose or "moderate",
            duration_hours=duration,
            effect=effect or "same",
            recovery_quality=recovery_quality,
            recovery_time_hours=recovery_time,
            pre_capacity=pre_capacity,
            post_capacity=post_capacity,
            notes=notes,
        )

        with self._lock:
            self._stressors.append(s)
            self._stats["total_stressors"] += 1
            self._update_stats()

        self._save_stats()
        self._log_stressor(s)

        return s

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_antifragility_stats(self) -> Dict[str, Any]:
        """Get antifragility pattern analysis."""
        if not self._stressors:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "stronger": 0, "weaker": 0, "damaged": 0, "recovery_sum": 0.0, "capacity_change": 0.0})
        for s in self._stressors:
            by_type[s.stressor_type]["count"] += 1
            if s.effect == "stronger":
                by_type[s.stressor_type]["stronger"] += 1
            if s.effect == "weaker":
                by_type[s.stressor_type]["weaker"] += 1
            if s.effect == "damaged":
                by_type[s.stressor_type]["damaged"] += 1
            by_type[s.stressor_type]["recovery_sum"] += s.recovery_time_hours
            by_type[s.stressor_type]["capacity_change"] += (s.post_capacity - s.pre_capacity)

        type_stats = {}
        antifragile_types = []
        fragile_types = []
        for t, data in by_type.items():
            count = data["count"]
            stronger_rate = data["stronger"] / count
            damage_rate = data["damaged"] / count
            type_stats[t] = {
                "count": count,
                "stronger_rate": round(stronger_rate, 2),
                "damage_rate": round(damage_rate, 2),
                "avg_recovery": round(data["recovery_sum"] / count, 1),
                "avg_capacity_change": round(data["capacity_change"] / count, 2),
            }
            if stronger_rate > 0.4 and damage_rate < 0.2:
                antifragile_types.append(t)
            elif damage_rate > 0.3:
                fragile_types.append(t)

        # Dose analysis
        by_dose = defaultdict(lambda: {"count": 0, "effect_sum": 0.0})
        effect_scores = {"weaker": -1, "same": 0, "stronger": 1, "damaged": -2, "broke": -3}
        for s in self._stressors:
            by_dose[s.dose]["count"] += 1
            by_dose[s.dose]["effect_sum"] += effect_scores.get(s.effect, 0)

        dose_stats = {}
        for d, data in by_dose.items():
            count = data["count"]
            dose_stats[d] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
            }

        # Recovery quality impact
        good_recovery = [s for s in self._stressors if s.recovery_quality > 0.6]
        poor_recovery = [s for s in self._stressors if s.recovery_quality < 0.4]
        if good_recovery and poor_recovery:
            good_effect = sum(effect_scores.get(s.effect, 0) for s in good_recovery) / len(good_recovery)
            poor_effect = sum(effect_scores.get(s.effect, 0) for s in poor_recovery) / len(poor_recovery)
            recovery_importance = good_effect - poor_effect
        else:
            recovery_importance = 0

        return {
            "total_stressors": len(self._stressors),
            "type_stats": type_stats,
            "antifragile_types": antifragile_types,
            "fragile_types": fragile_types,
            "dose_stats": dose_stats,
            "recovery_importance": round(recovery_importance, 2),
            "stronger_rate": round(sum(1 for s in self._stressors if s.effect == "stronger") / len(self._stressors), 2),
            "damage_rate": round(sum(1 for s in self._stressors if s.effect in ["damaged", "broke"]) / len(self._stressors), 2),
        }

    def get_hormesis_suggestion(self, current_capacity: float = 0.5, goal: str = "growth", stressor_type: str = "") -> Dict[str, Any]:
        """Get controlled stress exposure."""
        suggestions = {
            "physical": [
                "Cold shower for 30 seconds. Extend by 10 seconds each day.",
                "Walk or run in uncomfortable weather (rain, heat, cold)",
                "Fast for 16 hours. Notice mental clarity.",
                "Do one more rep than feels comfortable. Just one.",
            ],
            "mental": [
                "Learn something completely outside your expertise for 20 minutes",
                "Solve a puzzle that's slightly too hard. Struggle productively.",
                "Memorize a short poem. Test recall tomorrow.",
                "Read a perspective that deeply challenges your own",
            ],
            "emotional": [
                "Have a conversation you've been avoiding for less than 5 minutes",
                "Watch a film or read a story that makes you cry",
                "Sit with a difficult memory for 5 minutes without trying to fix it",
                "Express gratitude to someone you have mixed feelings about",
            ],
            "social": [
                "Attend an event where you know no one. Stay for 30 minutes.",
                "Ask for something you're afraid you'll be rejected for",
                "Give honest feedback to someone you care about",
                "Introduce yourself to a stranger with no agenda",
            ],
            "creative": [
                "Create something with severe constraints (one color, 100 words, 5 minutes)",
                "Share an unfinished work with someone you trust",
                "Destroy something you made and make it again differently",
                "Imitate your favorite artist, then twist it",
            ],
            "financial": [
                "Live on 80% of your normal spending for one week",
                "Calculate your true runway. Face it.",
                "Research one investment that scares you. Understand why.",
                "Give away an amount that stings slightly",
            ],
        }

        if stressor_type and stressor_type in suggestions:
            selected = random.choice(suggestions[stressor_type])
        else:
            all_suggestions = [s for cat in suggestions.values() for s in cat]
            selected = random.choice(all_suggestions)

        if current_capacity < 0.3:
            dose = "micro"
            note = "Your capacity is low. Start with the smallest possible stress. Recovery is more important than growth right now."
        elif current_capacity < 0.6:
            dose = "small"
            note = "Moderate capacity. Push slightly past comfort. Prioritize recovery."
        else:
            dose = "moderate"
            note = "Good capacity. This is your growth window. Stress + excellent recovery = strength."

        return {
            "suggestion": selected,
            "type": stressor_type or "mixed",
            "dose": dose,
            "current_capacity": current_capacity,
            "goal": goal,
            "note": note,
            "recovery": "Afterward: Sleep 8 hours. Eat protein. Move gently. Be kind to yourself.",
        }

    def get_antifragility_score(self) -> int:
        """Calculate overall antifragility health (0-100)."""
        if not self._stressors:
            return 40

        # Stronger rate
        stronger = sum(1 for s in self._stressors if s.effect == "stronger")
        stronger_rate = stronger / len(self._stressors)

        # Damage rate (lower is better)
        damage = sum(1 for s in self._stressors if s.effect in ["damaged", "broke"])
        damage_rate = damage / len(self._stressors)

        # Recovery quality
        avg_recovery = sum(s.recovery_quality for s in self._stressors) / len(self._stressors)

        # Capacity improvement
        capacity_changes = [s.post_capacity - s.pre_capacity for s in self._stressors]
        avg_capacity_change = sum(capacity_changes) / len(capacity_changes)

        # Voluntary stress ratio (voluntary is generally better)
        voluntary = sum(1 for s in self._stressors if s.stressor_type == "voluntary")
        voluntary_rate = voluntary / len(self._stressors)

        # Recent trend
        recent = [s for s in self._stressors if s.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_stronger = sum(1 for s in recent if s.effect == "stronger") / len(recent)
        else:
            recent_stronger = stronger_rate

        score = (stronger_rate * 30) + ((1 - damage_rate) * 20) + (avg_recovery * 15) + (avg_capacity_change * 15) + (voluntary_rate * 5) + (recent_stronger * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._stressors:
            stronger = sum(1 for s in self._stressors if s.effect == "stronger")
            self._stats["stronger_rate"] = round(stronger / len(self._stressors), 2)
            self._stats["avg_recovery"] = round(sum(s.recovery_time_hours for s in self._stressors) / len(self._stressors), 1)

            by_type = defaultdict(lambda: {"stronger": 0, "damaged": 0, "total": 0})
            for s in self._stressors:
                by_type[s.stressor_type]["total"] += 1
                if s.effect == "stronger":
                    by_type[s.stressor_type]["stronger"] += 1
                if s.effect == "damaged":
                    by_type[s.stressor_type]["damaged"] += 1
            
            self._stats["fragile_types"] = [t for t, data in by_type.items() if data["damaged"] / max(1, data["total"]) > 0.3]
            self._stats["antifragile_types"] = [t for t, data in by_type.items() if data["stronger"] / max(1, data["total"]) > 0.4 and data["damaged"] / max(1, data["total"]) < 0.2]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.antifragility_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.antifragility_tracker")

    def _log_stressor(self, stressor: Stressor):
        try:
            with open(STRESSOR_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": stressor.timestamp,
                    "stressor": stressor.stressor,
                    "type": stressor.stressor_type,
                    "dose": stressor.dose,
                    "effect": stressor.effect,
                    "pre_capacity": stressor.pre_capacity,
                    "post_capacity": stressor.post_capacity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.antifragility_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_at_instance: Optional[AntifragilityTracker] = None
_at_lock = threading.Lock()


def get_antifragility_tracker() -> AntifragilityTracker:
    global _at_instance
    with _at_lock:
        if _at_instance is None:
            _at_instance = AntifragilityTracker()
        return _at_instance
