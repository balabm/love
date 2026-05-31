"""
LOVE Stress Resilience Trainer — Adaptive Capacity Intelligence (Modern AI Pattern)

Most stress management is reactive. This trainer:

1. STRESS TRACKING
   - Record stress events and their characteristics
   - Track stress responses (fight, flight, freeze, fawn, tend-and-befriend)
   - Log recovery time and effectiveness

2. PATTERN ANALYSIS
   - Identify the user's stress profile (anticipatory, acute, chronic, traumatic)
   - Find stress triggers and their frequency
   - Detect resilience trends (recovery speed over time)

3. RESILIENCE BUILDING
   - Suggest stress inoculation practices
   - Provide recovery acceleration techniques
   - Recommend resilience-building habits

4. ADAPTIVE CAPACITY
   - Track the user's stress window of tolerance
   - Alert when approaching overwhelm or shutdown
   - Celebrate resilience growth

Architecture:
- record_stress_event(trigger, intensity, response, recovery): Log event
- get_stress_stats(): Get stress pattern analysis
- get_resilience_practice(stress_type, current_capacity): Get practice
- get_resilience_score(): Calculate overall resilience health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "stress_resilience_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STRESS_LOG = DATA_DIR / "stress.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class StressEvent:
    """A tracked stress event."""
    event_id: str = ""
    trigger: str = ""
    stress_type: str = ""  # anticipatory, acute, chronic, traumatic, positive
    intensity: float = 0.5  # 0-1
    response: str = ""  # fight, flight, freeze, fawn, tend-and-befriend, challenge
    duration_minutes: float = 0.0
    recovery_time: float = 0.0  # minutes to return to baseline
    recovery_method: str = ""
    energy_before: float = 0.5
    energy_after: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class StressResilienceTrainer:
    """
    Intelligent stress resilience trainer with adaptive capacity tracking and recovery acceleration.
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
        self._events: deque = deque(maxlen=300)
        self._stats = {
            "total_events": 0,
            "avg_intensity": 0.0,
            "avg_recovery": 0.0,
            "primary_trigger": "",
            "resilience_trend": "stable",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_stress_event(self, trigger: str = "", stress_type: str = "", intensity: float = 0.5, response: str = "", duration: float = 0, recovery_time: float = 0, recovery_method: str = "", energy_before: float = 0.5, energy_after: float = 0.5, notes: str = "") -> StressEvent:
        """Record a stress event."""
        event_id = f"str_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._events)}"
        event = StressEvent(
            event_id=event_id,
            trigger=trigger or "unspecified",
            stress_type=stress_type or "acute",
            intensity=intensity,
            response=response or "freeze",
            duration_minutes=duration,
            recovery_time=recovery_time,
            recovery_method=recovery_method,
            energy_before=energy_before,
            energy_after=energy_after,
            notes=notes,
        )

        with self._lock:
            self._events.append(event)
            self._stats["total_events"] += 1
            self._update_stats()

        self._save_stats()
        self._log_event(event)

        return event

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_stress_stats(self) -> Dict[str, Any]:
        """Get stress pattern analysis."""
        if not self._events:
            return {"status": "insufficient_data"}

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "recovery_sum": 0.0})
        for e in self._events:
            by_trigger[e.trigger]["count"] += 1
            by_trigger[e.trigger]["intensity_sum"] += e.intensity
            by_trigger[e.trigger]["recovery_sum"] += e.recovery_time

        trigger_stats = {}
        for t, data in by_trigger.items():
            count = data["count"]
            trigger_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_recovery": round(data["recovery_sum"] / count, 1),
            }

        primary_trigger = max(trigger_stats.items(), key=lambda x: x[1]["count"]) if trigger_stats else ("", {})

        # Response analysis
        by_response = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "recovery_sum": 0.0})
        for e in self._events:
            by_response[e.response]["count"] += 1
            by_response[e.response]["intensity_sum"] += e.intensity
            by_response[e.response]["recovery_sum"] += e.recovery_time

        response_stats = {}
        for r, data in by_response.items():
            count = data["count"]
            response_stats[r] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_recovery": round(data["recovery_sum"] / count, 1),
            }

        # Stress type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "recovery_sum": 0.0})
        for e in self._events:
            by_type[e.stress_type]["count"] += 1
            by_type[e.stress_type]["intensity_sum"] += e.intensity
            by_type[e.stress_type]["recovery_sum"] += e.recovery_time

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_recovery": round(data["recovery_sum"] / count, 1),
            }

        # Recovery trend
        recent = list(self._events)[-10:]
        older = list(self._events)[:-10] if len(self._events) > 10 else []
        if recent and older:
            recent_recovery = sum(e.recovery_time for e in recent) / len(recent)
            older_recovery = sum(e.recovery_time for e in older) / len(older)
            recovery_trend = older_recovery - recent_recovery  # positive means faster recovery
        else:
            recovery_trend = 0

        # Resilience trend
        if len(self._events) >= 20:
            first_half = list(self._events)[:len(self._events)//2]
            second_half = list(self._events)[len(self._events)//2:]
            first_recovery = sum(e.recovery_time for e in first_half) / len(first_half)
            second_recovery = sum(e.recovery_time for e in second_half) / len(second_half)
            if second_recovery < first_recovery * 0.8:
                resilience_trend = "improving"
            elif second_recovery > first_recovery * 1.2:
                resilience_trend = "declining"
            else:
                resilience_trend = "stable"
        else:
            resilience_trend = "insufficient_data"

        # Window of tolerance
        if recent:
            avg_intensity = sum(e.intensity for e in recent) / len(recent)
            high_intensity = sum(1 for e in recent if e.intensity > 0.7) / len(recent)
            window_status = "narrow" if high_intensity > 0.4 else "optimal" if avg_intensity < 0.4 else "adequate"
        else:
            window_status = "unknown"

        return {
            "total_events": len(self._events),
            "trigger_stats": trigger_stats,
            "primary_trigger": primary_trigger[0],
            "response_stats": response_stats,
            "type_stats": type_stats,
            "avg_intensity": round(sum(e.intensity for e in self._events) / len(self._events), 2),
            "avg_recovery": round(sum(e.recovery_time for e in self._events) / len(self._events), 1),
            "recovery_trend": round(recovery_trend, 1),
            "resilience_trend": resilience_trend,
            "window_status": window_status,
        }

    def get_resilience_practice(self, stress_type: str = "", current_capacity: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "anticipatory": [
                "Worry scheduling: Write down worries at a set time. Not before bed.",
                "Prepare, don't ruminate. One concrete action beats hours of worry.",
                "Ask: 'What's the worst that could happen? Can I survive that?' Usually, yes.",
            ],
            "acute": [
                "Box breathing: 4 counts in, hold, out, hold. Do 10 rounds.",
                "Name 5 things you see, 4 you hear, 3 you feel, 2 you smell, 1 you taste. Grounding.",
                "Tense all muscles for 5 seconds, release. Progressive relaxation.",
            ],
            "chronic": [
                "Set boundaries. 'No' is a complete sentence. Practice saying it.",
                "Find one thing you can control. Focus there. Let the rest go.",
                "Build recovery into every day. Not just weekends. Daily.",
            ],
            "traumatic": [
                "This is advanced. See a trauma-informed therapist. You don't have to do this alone.",
                "Grounding techniques: Feet on floor. Name your location. Time and date.",
                "Create safety signals: A scent, a song, a texture that means 'I'm safe now.'",
            ],
            "positive": [
                "Eustress is still stress. Excitement and anxiety share physiology.",
                "Channel the energy. Use it. Don't suppress it.",
                "Recover anyway. Positive stress still depletes. Rest after achievement.",
            ],
        }

        selected = practices.get(stress_type, practices["acute"])

        if current_capacity < 0.3:
            capacity_note = "Your resilience tank is low. Prioritize recovery over challenge. This is not weakness, it's wisdom."
        elif current_capacity < 0.6:
            capacity_note = "Moderate capacity. Match challenges to your current state. Don't take on more."
        else:
            capacity_note = "Good capacity. This is when you can stretch yourself. But still recover."

        return {
            "stress_type": stress_type or "general",
            "current_capacity": current_capacity,
            "practice": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Resilience is not about never breaking. It's about recovering faster each time. And knowing when to rest before you break.",
        }

    def get_resilience_score(self) -> int:
        """Calculate overall resilience health (0-100)."""
        if not self._events:
            return 35

        # Recovery speed (faster is better)
        avg_recovery = sum(e.recovery_time for e in self._events) / len(self._events)
        recovery_score = max(0, 1 - avg_recovery / 120)  # 120 min as baseline

        # Low intensity
        avg_intensity = sum(e.intensity for e in self._events) / len(self._events)

        # Response diversity (not always same response)
        unique_responses = len(set(e.response for e in self._events))

        # Energy sustainability
        avg_energy_change = sum(e.energy_after - e.energy_before for e in self._events) / len(self._events)

        # Recovery trend
        recent = list(self._events)[-10:]
        older = list(self._events)[:-10] if len(self._events) > 10 else []
        if recent and older:
            recent_recovery = sum(e.recovery_time for e in recent) / len(recent)
            older_recovery = sum(e.recovery_time for e in older) / len(older)
            trend = older_recovery - recent_recovery
        else:
            trend = 0

        # Positive stress ratio
        positive_stress = sum(1 for e in self._events if e.stress_type == "positive")
        positive_ratio = positive_stress / len(self._events)

        score = (recovery_score * 25) + ((1 - avg_intensity) * 15) + (unique_responses * 3) + (avg_energy_change * 15) + (trend * 15) + (positive_ratio * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._events:
            self._stats["avg_intensity"] = round(sum(e.intensity for e in self._events) / len(self._events), 2)
            self._stats["avg_recovery"] = round(sum(e.recovery_time for e in self._events) / len(self._events), 1)

            by_trigger = defaultdict(lambda: {"intensity": 0.0, "count": 0})
            for e in self._events:
                by_trigger[e.trigger]["intensity"] += e.intensity
                by_trigger[e.trigger]["count"] += 1
            if by_trigger:
                primary = max(by_trigger.items(), key=lambda x: x[1]["count"])
                self._stats["primary_trigger"] = primary[0]

            if len(self._events) >= 20:
                first_half = list(self._events)[:len(self._events)//2]
                second_half = list(self._events)[len(self._events)//2:]
                first_recovery = sum(e.recovery_time for e in first_half) / len(first_half)
                second_recovery = sum(e.recovery_time for e in second_half) / len(second_half)
                if second_recovery < first_recovery * 0.8:
                    self._stats["resilience_trend"] = "improving"
                elif second_recovery > first_recovery * 1.2:
                    self._stats["resilience_trend"] = "declining"
                else:
                    self._stats["resilience_trend"] = "stable"

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

    def _log_event(self, event: StressEvent):
        try:
            with open(STRESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": event.timestamp,
                    "trigger": event.trigger,
                    "stress_type": event.stress_type,
                    "intensity": event.intensity,
                    "response": event.response,
                    "recovery_time": event.recovery_time,
                    "recovery_method": event.recovery_method,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_srt_instance: Optional[StressResilienceTrainer] = None
_srt_lock = threading.Lock()


def get_stress_resilience_trainer() -> StressResilienceTrainer:
    global _srt_instance
    with _srt_lock:
        if _srt_instance is None:
            _srt_instance = StressResilienceTrainer()
        return _srt_instance
