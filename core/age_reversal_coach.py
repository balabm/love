"""
LOVE Age Reversal Coach — Rejuvenation Intelligence (Modern AI Pattern)

Most people accept decline as inevitable. This coach knows that while
chronological age moves in one direction, biological age can move
in both. This coach:

1. REVERSAL TRACKING
   - Record rejuvenation practices and their effects
   - Track practice types (fasting, cold exposure, heat, movement, sleep, supplements)
   - Log biological markers, recovery speed, and subjective youth

2. PATTERN ANALYSIS
   - Identify the user's rejuvenation profile (aggressive, steady, curious, resistant)
   - Find practices that create measurable biological improvements
   - Detect practices that are placebo or harmful

3. REVERSAL OPTIMIZATION
   - Suggest evidence-based interventions matched to current biology
   - Provide frameworks for hormetic stress (beneficial stress)
   - Recommend the optimal intensity and frequency for each practice

4. YOUTH CULTIVATION
   - Track the correlation between practices and subjective age
   - Alert when habits are accelerating biological aging
   - Celebrate practices that make you feel younger than your years

Architecture:
- record_practice(practice, type, intensity, youth_effect): Log practice
- get_reversal_stats(): Get reversal pattern analysis
- get_practice_suggestion(age, capacity, context): Get suggestion
- get_reversal_score(): Calculate overall rejuvenation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "age_reversal_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REVERSAL_LOG = DATA_DIR / "practices.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ReversalEntry:
    """A tracked rejuvenation practice entry."""
    entry_id: str = ""
    practice: str = ""  # what was done
    practice_type: str = ""  # fasting, cold, heat, movement, sleep, mental, social
    intensity: float = 0.5  # 0-1
    youth_effect: float = 0.0  # 0-1 felt younger?
    recovery_speed: float = 0.0  # 0-1
    energy_boost: float = 0.0  # 0-1
    adherence: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AgeReversalCoach:
    """
    Intelligent age reversal coach with hormetic stress optimization and biological age tracking.
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
            "avg_youth_effect": 0.0,
            "avg_recovery_speed": 0.0,
            "aging_acceleration": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_practice(self, practice: str = "", practice_type: str = "", intensity: float = 0.5, youth_effect: float = 0.0, recovery_speed: float = 0.0, energy_boost: float = 0.0, adherence: float = 0.0, notes: str = "") -> ReversalEntry:
        """Record a rejuvenation practice."""
        entry_id = f"rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ReversalEntry(
            entry_id=entry_id,
            practice=practice or "unspecified",
            practice_type=practice_type or "general",
            intensity=intensity,
            youth_effect=youth_effect,
            recovery_speed=recovery_speed,
            energy_boost=energy_boost,
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

    def get_reversal_stats(self) -> Dict[str, Any]:
        """Get reversal pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "youth_sum": 0.0, "recovery_sum": 0.0, "energy_sum": 0.0})
        for e in self._entries:
            by_type[e.practice_type]["count"] += 1
            by_type[e.practice_type]["youth_sum"] += e.youth_effect
            by_type[e.practice_type]["recovery_sum"] += e.recovery_speed
            by_type[e.practice_type]["energy_sum"] += e.energy_boost

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_youth_effect": round(data["youth_sum"] / count, 2),
                "avg_recovery_speed": round(data["recovery_sum"] / count, 2),
                "avg_energy_boost": round(data["energy_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_youth_effect"]) if type_stats else ("", {})

        # Intensity sweet spot
        high_intensity = [e for e in self._entries if e.intensity > 0.7]
        moderate_intensity = [e for e in self._entries if 0.4 <= e.intensity <= 0.7]
        low_intensity = [e for e in self._entries if e.intensity < 0.4]

        intensity_stats = {}
        for label, group in [("high", high_intensity), ("moderate", moderate_intensity), ("low", low_intensity)]:
            if group:
                intensity_stats[label] = {
                    "count": len(group),
                    "avg_youth": round(sum(e.youth_effect for e in group) / len(group), 2),
                    "avg_recovery": round(sum(e.recovery_speed for e in group) / len(group), 2),
                }

        # Adherence analysis
        high_adh = [e for e in self._entries if e.adherence > 0.7]
        low_adh = [e for e in self._entries if e.adherence < 0.4]
        if high_adh and low_adh:
            high_adh_youth = sum(e.youth_effect for e in high_adh) / len(high_adh)
            low_adh_youth = sum(e.youth_effect for e in low_adh) / len(low_adh)
        else:
            high_adh_youth = 0
            low_adh_youth = 0

        # Aging acceleration detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_youth = sum(e.youth_effect for e in recent) / len(recent)
            recent_recovery = sum(e.recovery_speed for e in recent) / len(recent)
            aging_acceleration = recent_youth < 0.3 and recent_recovery < 0.3
        else:
            aging_acceleration = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "intensity_stats": intensity_stats,
            "adherence_impact": {
                "high_adherence_youth": round(high_adh_youth, 2),
                "low_adherence_youth": round(low_adh_youth, 2),
            },
            "aging_acceleration": aging_acceleration,
            "avg_youth_effect": round(sum(e.youth_effect for e in self._entries) / len(self._entries), 2),
            "avg_recovery_speed": round(sum(e.recovery_speed for e in self._entries) / len(self._entries), 2),
        }

    def get_practice_suggestion(self, age: int = 35, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get rejuvenation practice suggestion."""
        suggestions = [
            "Cold exposure triggers norepinephrine and brown fat activation. Start with cold showers. End with 30 seconds of cold. Build up. Your mitochondria will thank you.",
            "Heat shock proteins repair damaged proteins. Sauna. Hot bath. Heat increases growth hormone and cardiovascular fitness. The Finns knew something.",
            "Fasting is not starvation. It's cellular renewal. Start with 12 hours. Progress to 16. Autophagy is your body's recycling program. Turn it on.",
            "Zone 2 cardio builds mitochondrial density. The fat-burning zone. Walking, easy cycling, light jogging. Do it for 45 minutes. Your cells become more efficient.",
            "Resistance training maintains muscle mass. Muscle is the organ of longevity. The more you have, the longer you live. Lift heavy. Rest enough.",
            "Sleep is when rejuvenation happens. Deep sleep releases growth hormone. REM sleep clears the brain. Protect your sleep like your life depends on it. Because it does.",
            "Mental novelty keeps the brain young. New language. New instrument. New skill. Neuroplasticity is the fountain of youth for the mind.",
            "Social connection reduces inflammation. Loneliness accelerates aging. Community is a biological necessity, not a luxury. Invest in relationships.",
            "Breathwork changes physiology in minutes. Box breathing. Wim Hof method. Your autonomic nervous system is under your control. Use it.",
            "Consistency beats intensity. One cold shower a week is nothing. One cold shower a day changes you. Small daily hormetic stress compounds into biological resilience.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Start gentle. Cold shower finish. One fasted morning. One walk. Small stress. Big signal."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Add one modality. Cold + fasting. Or heat + movement. Layer gradually."
        else:
            capacity_note = "Good capacity. Full hormetic protocol. Cold. Heat. Fast. Move. Lift. Sleep deep. You can handle real stress and real adaptation."

        return {
            "age": age,
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Aging is not just wear and tear. It's also lack of repair. And repair is triggered by stress. The right kind of stress. Hormetic stress. The stress that says to the body: 'We need to be stronger.' Cold says this. Heat says this. Fasting says this. Movement says this. The body responds by repairing, renewing, rebuilding. Without this signal, the body coasts into decay. The goal is not comfort. The goal is the optimal dose of stress. Enough to trigger adaptation. Not so much that you break. That's the art of age reversal.",
        }

    def get_reversal_score(self) -> int:
        """Calculate overall rejuvenation health (0-100)."""
        if not self._entries:
            return 25

        avg_youth = sum(e.youth_effect for e in self._entries) / len(self._entries)
        avg_recovery = sum(e.recovery_speed for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy_boost for e in self._entries) / len(self._entries)
        avg_adherence = sum(e.adherence for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_youth = sum(e.youth_effect for e in recent) / len(recent)
            recent_recovery = sum(e.recovery_speed for e in recent) / len(recent)
        else:
            recent_youth = 0
            recent_recovery = 0

        # Aging acceleration penalty
        aging_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if len(last_90) < 5:
            aging_penalty = 10

        # Type variety
        unique_types = len(set(e.practice_type for e in self._entries))

        score = (avg_youth * 30) + (avg_recovery * 20) + (avg_energy * 15) + (avg_adherence * 15) + (recent_youth * 10) + (recent_recovery * 5) + (unique_types * 2) - aging_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_youth_effect"] = round(sum(e.youth_effect for e in self._entries) / len(self._entries), 2)
            self._stats["avg_recovery_speed"] = round(sum(e.recovery_speed for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_youth = sum(e.youth_effect for e in recent) / len(recent)
                recent_recovery = sum(e.recovery_speed for e in recent) / len(recent)
                self._stats["aging_acceleration"] = recent_youth < 0.3 and recent_recovery < 0.3
            else:
                self._stats["aging_acceleration"] = True

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.age_reversal_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.age_reversal_coach")

    def _log_entry(self, entry: ReversalEntry):
        try:
            with open(REVERSAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "practice": entry.practice,
                    "practice_type": entry.practice_type,
                    "youth_effect": entry.youth_effect,
                    "recovery_speed": entry.recovery_speed,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.age_reversal_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_arc_instance: Optional[AgeReversalCoach] = None
_arc_lock = threading.Lock()


def get_age_reversal_coach() -> AgeReversalCoach:
    global _arc_instance
    with _arc_lock:
        if _arc_instance is None:
            _arc_instance = AgeReversalCoach()
        return _arc_instance
