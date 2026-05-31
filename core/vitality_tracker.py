"""
LOVE Vitality Tracker — Energy Intelligence (Modern AI Pattern)

Most people track steps. This tracker tracks the energy that makes steps worth taking.

1. VITALITY TRACKING
   - Record daily vitality and its components
   - Track vitality sources (sleep, movement, nutrition, joy, connection, purpose)
   - Log vitality drains and their magnitude

2. PATTERN ANALYSIS
   - Identify the user's vitality profile (abundant, cyclical, depleted, recovering)
   - Find vitality patterns that predict good days
   - Detect chronic depletion and its causes

3. VITALITY OPTIMIZATION
   - Suggest energy restoration practices
   - Provide frameworks for protecting peak energy hours
   - Recommend vitality amplifiers matched to current state

4. ENERGY CULTIVATION
   - Track the correlation between vitality and life quality
   - Alert when energy is being spent on things that don't matter
   - Celebrate days of genuine aliveness

Architecture:
- record_vitality(vitality, sources, drains, peak_hours): Log vitality
- get_vitality_stats(): Get vitality pattern analysis
- get_vitality_suggestion(state, context): Get suggestion
- get_vitality_score(): Calculate overall vitality health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "vitality_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VITALITY_LOG = DATA_DIR / "vitality.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class VitalityEntry:
    """A tracked vitality entry."""
    entry_id: str = ""
    vitality: float = 0.5  # 0-1 overall daily vitality
    physical_energy: float = 0.5  # 0-1
    mental_clarity: float = 0.5  # 0-1
    emotional_resilience: float = 0.5  # 0-1
    motivation: float = 0.5  # 0-1
    sleep_quality: float = 0.0  # 0-1
    movement: float = 0.0  # 0-1
    nutrition: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    drains: float = 0.0  # 0-1 how much was drained today
    peak_hours: float = 0.0  # hours of peak performance
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VitalityTracker:
    """
    Intelligent vitality tracker with energy detection and restoration optimization.
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
            "avg_vitality": 0.0,
            "avg_drains": 0.0,
            "depletion_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_vitality(self, vitality: float = 0.5, physical_energy: float = 0.5, mental_clarity: float = 0.5, emotional_resilience: float = 0.5, motivation: float = 0.5, sleep_quality: float = 0.0, movement: float = 0.0, nutrition: float = 0.0, joy: float = 0.0, drains: float = 0.0, peak_hours: float = 0.0, notes: str = "") -> VitalityEntry:
        """Record a vitality entry."""
        entry_id = f"vtl_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = VitalityEntry(
            entry_id=entry_id,
            vitality=vitality,
            physical_energy=physical_energy,
            mental_clarity=mental_clarity,
            emotional_resilience=emotional_resilience,
            motivation=motivation,
            sleep_quality=sleep_quality,
            movement=movement,
            nutrition=nutrition,
            joy=joy,
            drains=drains,
            peak_hours=peak_hours,
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

    def get_vitality_stats(self) -> Dict[str, Any]:
        """Get vitality pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Component analysis
        components = {
            "physical_energy": sum(e.physical_energy for e in self._entries) / len(self._entries),
            "mental_clarity": sum(e.mental_clarity for e in self._entries) / len(self._entries),
            "emotional_resilience": sum(e.emotional_resilience for e in self._entries) / len(self._entries),
            "motivation": sum(e.motivation for e in self._entries) / len(self._entries),
            "sleep_quality": sum(e.sleep_quality for e in self._entries) / len(self._entries),
            "movement": sum(e.movement for e in self._entries) / len(self._entries),
            "nutrition": sum(e.nutrition for e in self._entries) / len(self._entries),
            "joy": sum(e.joy for e in self._entries) / len(self._entries),
        }
        weakest = min(components.items(), key=lambda x: x[1])
        strongest = max(components.items(), key=lambda x: x[1])

        # Vitality vs drains
        high_vitality = [e for e in self._entries if e.vitality > 0.7]
        low_vitality = [e for e in self._entries if e.vitality < 0.4]
        if high_vitality and low_vitality:
            high_vit_sleep = sum(e.sleep_quality for e in high_vitality) / len(high_vitality)
            low_vit_sleep = sum(e.sleep_quality for e in low_vitality) / len(low_vitality)
            high_vit_joy = sum(e.joy for e in high_vitality) / len(high_vitality)
            low_vit_joy = sum(e.joy for e in low_vitality) / len(low_vitality)
            high_vit_drains = sum(e.drains for e in high_vitality) / len(high_vitality)
            low_vit_drains = sum(e.drains for e in low_vitality) / len(low_vitality)
        else:
            high_vit_sleep = 0
            low_vit_sleep = 0
            high_vit_joy = 0
            low_vit_joy = 0
            high_vit_drains = 0
            low_vit_drains = 0

        # Peak hours analysis
        high_peak = [e for e in self._entries if e.peak_hours > 4]
        low_peak = [e for e in self._entries if e.peak_hours < 2]
        if high_peak and low_peak:
            high_peak_vitality = sum(e.vitality for e in high_peak) / len(high_peak)
            low_peak_vitality = sum(e.vitality for e in low_peak) / len(low_peak)
        else:
            high_peak_vitality = 0
            low_peak_vitality = 0

        # Depletion risk
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_vitality = sum(e.vitality for e in recent) / len(recent)
            recent_drains = sum(e.drains for e in recent) / len(recent)
            depletion_risk = recent_vitality < 0.4 and recent_drains > 0.7
        else:
            depletion_risk = True

        return {
            "total_entries": len(self._entries),
            "components": {k: round(v, 2) for k, v in components.items()},
            "weakest_component": weakest[0],
            "strongest_component": strongest[0],
            "vitality_sleep": {
                "high_vitality_sleep": round(high_vit_sleep, 2),
                "low_vitality_sleep": round(low_vit_sleep, 2),
            },
            "vitality_joy": {
                "high_vitality_joy": round(high_vit_joy, 2),
                "low_vitality_joy": round(low_vit_joy, 2),
            },
            "vitality_drains": {
                "high_vitality_drains": round(high_vit_drains, 2),
                "low_vitality_drains": round(low_vit_drains, 2),
            },
            "peak_hours_effect": {
                "high_peak_vitality": round(high_peak_vitality, 2),
                "low_peak_vitality": round(low_peak_vitality, 2),
            },
            "depletion_risk": depletion_risk,
            "avg_vitality": round(sum(e.vitality for e in self._entries) / len(self._entries), 2),
            "avg_drains": round(sum(e.drains for e in self._entries) / len(self._entries), 2),
        }

    def get_vitality_suggestion(self, state: str = "", context: str = "") -> Dict[str, Any]:
        """Get vitality suggestion."""
        suggestions = [
            "Your energy is not infinite. It's a resource to be managed. The most productive people are not the ones who work hardest. They're the ones who protect their vitality most ruthlessly.",
            "Sleep is not lazy. It's performance. The difference between 6 hours and 8 hours is not 2 hours. It's the difference between creative and merely functional.",
            "Move your body before you need your mind. Morning movement primes the brain. Afternoon movement resets it. Evening movement deepens sleep.",
            "Joy is not optional. It's fuel. The days you laugh are the days you have energy. Schedule joy the way you schedule meetings.",
            "Protect your peak hours like a dragon guards gold. Those 2-4 hours of highest energy are worth 8 hours of mediocre energy. Defend them from all invaders.",
            "Nutrition is energy architecture. What you eat becomes what you think. Sugar crashes are real. Protein steadiness is real. Eat for the day you want to have.",
            "Emotional resilience is physical. You can't separate them. The body holds stress. Move it out. Breathe it out. Sleep it out.",
            "Motivation follows action. Not the other way. Start before you feel like it. The feeling comes after the first ten minutes. Always.",
            "Rest is not the opposite of work. It's the partner of work. The best rest is active. Walks. Hobbies. Conversations. Not scrolling. Scrolling is not rest.",
            "Your vitality is the most valuable thing you have. More than time. More than money. Because without vitality, time and money are useless. Guard it. Feed it. Celebrate it.",
        ]

        return {
            "state": state or "general",
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "principle": "Vitality is the background music of your life. When it's high, everything is possible. When it's low, everything is hard. Most people try to solve their problems by working harder. But often the problem is not effort. It's energy. You can't think clearly when depleted. You can't be creative when exhausted. You can't be kind when drained. The first step to improving any area of life is improving your vitality. Everything else is secondary.",
        }

    def get_vitality_score(self) -> int:
        """Calculate overall vitality health (0-100)."""
        if not self._entries:
            return 25

        avg_vitality = sum(e.vitality for e in self._entries) / len(self._entries)
        avg_physical = sum(e.physical_energy for e in self._entries) / len(self._entries)
        avg_mental = sum(e.mental_clarity for e in self._entries) / len(self._entries)
        avg_emotional = sum(e.emotional_resilience for e in self._entries) / len(self._entries)
        avg_motivation = sum(e.motivation for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_drains = sum(e.drains for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_vitality = sum(e.vitality for e in recent) / len(recent)
            recent_drains = sum(e.drains for e in recent) / len(recent)
        else:
            recent_vitality = 0
            recent_drains = 0

        # Depletion penalty
        depletion_penalty = 0
        if recent:
            if recent_vitality < 0.4 and recent_drains > 0.7:
                depletion_penalty = 20

        score = (avg_vitality * 25) + (avg_physical * 15) + (avg_mental * 15) + (avg_emotional * 10) + (avg_motivation * 10) + (avg_joy * 10) + (recent_vitality * 10) - (avg_drains * 10) - depletion_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_vitality"] = round(sum(e.vitality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_drains"] = round(sum(e.drains for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if recent:
                recent_vitality = sum(e.vitality for e in recent) / len(recent)
                recent_drains = sum(e.drains for e in recent) / len(recent)
                self._stats["depletion_risk"] = recent_vitality < 0.4 and recent_drains > 0.7
            else:
                self._stats["depletion_risk"] = True

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

    def _log_entry(self, entry: VitalityEntry):
        try:
            with open(VITALITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "vitality": entry.vitality,
                    "physical_energy": entry.physical_energy,
                    "mental_clarity": entry.mental_clarity,
                    "drains": entry.drains,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vt_instance: Optional[VitalityTracker] = None
_vt_lock = threading.Lock()


def get_vitality_tracker() -> VitalityTracker:
    global _vt_instance
    with _vt_lock:
        if _vt_instance is None:
            _vt_instance = VitalityTracker()
        return _vt_instance
