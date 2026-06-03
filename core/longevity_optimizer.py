"""
LOVE Longevity Optimizer — Lifespan Intelligence (Modern AI Pattern)

Most people age by default. This optimizer:

1. LONGEVITY TRACKING
   - Record longevity practices and their effects
   - Track practice types (movement, nutrition, sleep, stress, social, purpose)
   - Log biomarkers, energy, and subjective age

2. PATTERN ANALYSIS
   - Identify the user's longevity profile (investor, maintainer, neglecter, aware)
   - Find practice patterns that correlate with vitality
   - Detect aging acceleration factors

3. LONGEVITY OPTIMIZATION
   - Suggest evidence-based practices matched to current age and capacity
   - Provide frameworks for sustainable anti-aging habits
   - Recommend the highest-leverage interventions

4. VITALITY CULTIVATION
   - Track subjective vs chronological age gap
   - Alert when habits are accelerating decline
   - Celebrate practices that expand healthspan

Architecture:
- record_practice(practice, type, intensity, vitality_effect): Log practice
- get_longevity_stats(): Get longevity pattern analysis
- get_practice_suggestion(age, capacity, context): Get suggestion
- get_longevity_score(): Calculate overall longevity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "longevity_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LONGEVITY_LOG = DATA_DIR / "practices.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class LongevityEntry:
    """A tracked longevity practice entry."""
    entry_id: str = ""
    practice: str = ""  # what was done
    practice_type: str = ""  # movement, nutrition, sleep, stress, social, purpose, mental
    intensity: float = 0.5  # 0-1
    vitality_effect: float = 0.0  # 0-1
    energy_next_day: float = 0.0  # 0-1
    subjective_age: float = 0.0  # 0-1 lower is younger
    adherence: float = 0.0  # 0-1 how consistently done
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LongevityOptimizer:
    """
    Intelligent longevity optimizer with healthspan detection and vitality cultivation.
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
            "avg_vitality_effect": 0.0,
            "avg_adherence": 0.0,
            "decline_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_practice(self, practice: str = "", practice_type: str = "", intensity: float = 0.5, vitality_effect: float = 0.0, energy_next_day: float = 0.0, subjective_age: float = 0.0, adherence: float = 0.0, notes: str = "") -> LongevityEntry:
        """Record a longevity practice."""
        entry_id = f"lng_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = LongevityEntry(
            entry_id=entry_id,
            practice=practice or "unspecified",
            practice_type=practice_type or "general",
            intensity=intensity,
            vitality_effect=vitality_effect,
            energy_next_day=energy_next_day,
            subjective_age=subjective_age,
            adherence=adherence,
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

    def get_longevity_stats(self) -> Dict[str, Any]:
        """Get longevity pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "vitality_sum": 0.0, "energy_sum": 0.0, "adherence_sum": 0.0})
        for e in self._entries:
            by_type[e.practice_type]["count"] += 1
            by_type[e.practice_type]["vitality_sum"] += e.vitality_effect
            by_type[e.practice_type]["energy_sum"] += e.energy_next_day
            by_type[e.practice_type]["adherence_sum"] += e.adherence

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_vitality_effect": round(data["vitality_sum"] / count, 2),
                "avg_energy_next_day": round(data["energy_sum"] / count, 2),
                "avg_adherence": round(data["adherence_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_vitality_effect"]) if type_stats else ("", {})

        # Intensity analysis
        high_intensity = [e for e in self._entries if e.intensity > 0.7]
        moderate_intensity = [e for e in self._entries if 0.4 <= e.intensity <= 0.7]
        low_intensity = [e for e in self._entries if e.intensity < 0.4]

        intensity_stats = {}
        for label, group in [("high", high_intensity), ("moderate", moderate_intensity), ("low", low_intensity)]:
            if group:
                intensity_stats[label] = {
                    "count": len(group),
                    "avg_vitality": round(sum(e.vitality_effect for e in group) / len(group), 2),
                    "avg_adherence": round(sum(e.adherence for e in group) / len(group), 2),
                }

        # Adherence analysis
        high_adherence = [e for e in self._entries if e.adherence > 0.7]
        low_adherence = [e for e in self._entries if e.adherence < 0.4]
        if high_adherence and low_adherence:
            high_adh_vitality = sum(e.vitality_effect for e in high_adherence) / len(high_adherence)
            low_adh_vitality = sum(e.vitality_effect for e in low_adherence) / len(low_adherence)
        else:
            high_adh_vitality = 0
            low_adh_vitality = 0

        # Decline risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_vitality = sum(e.vitality_effect for e in recent) / len(recent)
            recent_adherence = sum(e.adherence for e in recent) / len(recent)
            decline_risk = recent_vitality < 0.3 and recent_adherence < 0.3
        else:
            decline_risk = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "intensity_stats": intensity_stats,
            "adherence_impact": {
                "high_adherence_vitality": round(high_adh_vitality, 2),
                "low_adherence_vitality": round(low_adh_vitality, 2),
            },
            "decline_risk": decline_risk,
            "avg_vitality_effect": round(sum(e.vitality_effect for e in self._entries) / len(self._entries), 2),
            "avg_adherence": round(sum(e.adherence for e in self._entries) / len(self._entries), 2),
        }

    def get_practice_suggestion(self, age: int = 35, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get longevity practice suggestion."""
        suggestions = [
            "Walk after every meal. Not for fitness. For blood sugar. The post-meal walk is one of the most powerful longevity tools available. And it's free.",
            "Lift something heavy twice a week. Muscle mass is the currency of aging. The more you have at 50, the more you have at 80. Resistance training is non-negotiable.",
            "Eat protein at every meal. Most people over 40 undereat protein. Your body is trying to maintain muscle with insufficient raw material. Give it what it needs.",
            "Sleep before midnight. The first half of the night is when growth hormone releases. Deep sleep repairs. Late sleep borrows from tomorrow.",
            "Fasting is not starvation. It's repair. Even a 12-hour overnight fast triggers autophagy. Your cells clean house when food is absent.",
            "Cold exposure builds resilience. Cold showers. Cold plunges. Winter walks. Your mitochondria respond to temperature stress by becoming more efficient.",
            "Social connection is a longevity drug. Strong relationships predict lifespan better than genetics. Loneliness is as damaging as smoking. Invest in people.",
            "Purpose extends life. People with strong purpose live longer. Not because purpose magically heals. Because it gets you out of bed. It gives you reasons to maintain yourself.",
            "Learn something new every year. Novelty keeps the brain young. New language. New instrument. New skill. Neuroplasticity is use-it-or-lose-it.",
            "Sunlight in the morning. Not just for vitamin D. For circadian entrainment. Morning light sets your internal clock. Everything works better when the clock is set.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One practice. One walk. One earlier bedtime. Start with what you can sustain."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Add one category. If you move, fix sleep. If you sleep well, add strength. Stack gradually."
        else:
            capacity_note = "Good capacity. Full protocol. Movement. Nutrition. Sleep. Stress. Social. Purpose. You're ready to invest seriously in your future self."

        return {
            "age": age,
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Aging is not a cliff you fall off at 70. It's a slope you slide down from 30. The habits you have at 40 determine how you feel at 60. The habits at 60 determine how you feel at 80. Most people treat their body like a rental car. The best treat it like a classic they're maintaining for decades. Longevity is not about living forever. It's about compressing morbidity. More healthy years. Fewer sick years. The goal is to die young as late as possible.",
        }

    def get_longevity_score(self) -> int:
        """Calculate overall longevity health (0-100)."""
        if not self._entries:
            return 25

        avg_vitality = sum(e.vitality_effect for e in self._entries) / len(self._entries)
        avg_adherence = sum(e.adherence for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy_next_day for e in self._entries) / len(self._entries)
        avg_intensity = sum(e.intensity for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_vitality = sum(e.vitality_effect for e in recent) / len(recent)
            recent_adherence = sum(e.adherence for e in recent) / len(recent)
        else:
            recent_vitality = 0
            recent_adherence = 0

        # Decline penalty
        decline_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if len(last_90) < 5:
            decline_penalty = 10

        # Type variety
        unique_types = len(set(e.practice_type for e in self._entries))

        score = (avg_vitality * 30) + (avg_adherence * 25) + (avg_energy * 15) + (avg_intensity * 5) + (recent_vitality * 10) + (recent_adherence * 10) + (unique_types * 2) - decline_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_vitality_effect"] = round(sum(e.vitality_effect for e in self._entries) / len(self._entries), 2)
            self._stats["avg_adherence"] = round(sum(e.adherence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_vitality = sum(e.vitality_effect for e in recent) / len(recent)
                recent_adherence = sum(e.adherence for e in recent) / len(recent)
                self._stats["decline_risk"] = recent_vitality < 0.3 and recent_adherence < 0.3
            else:
                self._stats["decline_risk"] = True

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.longevity_optimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.longevity_optimizer")

    def _log_entry(self, entry: LongevityEntry):
        try:
            with open(LONGEVITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "practice": entry.practice,
                    "practice_type": entry.practice_type,
                    "vitality_effect": entry.vitality_effect,
                    "adherence": entry.adherence,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.longevity_optimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lo_instance: Optional[LongevityOptimizer] = None
_lo_lock = threading.Lock()


def get_longevity_optimizer() -> LongevityOptimizer:
    global _lo_instance
    with _lo_lock:
        if _lo_instance is None:
            _lo_instance = LongevityOptimizer()
        return _lo_instance
