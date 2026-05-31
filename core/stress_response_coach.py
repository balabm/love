"""
LOVE Stress Response Coach — Resilience Intelligence (Modern AI Pattern)

Most stress tools are reactive calming exercises. This coach:

1. STRESS PATTERN DETECTION
   - Track stress triggers, intensity, and duration over time
   - Identify early warning signs before full overwhelm
   - Detect stress patterns (time of day, preceding events, buildup speed)

2. RESPONSE EFFECTIVENESS
   - Track which coping strategies actually work for this user
   - Measure recovery time for different interventions
   - Identify fastest path from stressed to calm

3. PROACTIVE INTERVENTION
   - Suggest micro-interventions when stress is building
   - Recommend prevention strategies based on trigger patterns
   - Alert when stress patterns match past overwhelm episodes

4. RESILIENCE BUILDING
   - Track stress resilience over time (same trigger, lower response)
   - Suggest resilience practices (sleep, exercise, social connection)
   - Celebrate stress management improvements

Architecture:
- record_stress_event(trigger, intensity, response): Log stress event
- get_stress_patterns(): Get stress pattern analysis
- get_intervention(): Get personalized stress intervention
- get_resilience_score(): Calculate resilience score
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "stress_response_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STRESS_LOG = DATA_DIR / "stress_events.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class StressEvent:
    """A recorded stress event."""
    trigger: str = ""  # what caused the stress
    intensity: float = 0.5  # 0-1
    physical_symptoms: List[str] = field(default_factory=list)  # tension, headache, racing_heart, fatigue
    emotional_state: str = ""  # anxious, overwhelmed, frustrated, worried
    preceding_events: List[str] = field(default_factory=list)
    coping_strategy: str = ""  # what the user tried
    strategy_effectiveness: float = 0.5  # how well it worked
    recovery_minutes: float = 0.0  # time to return to baseline
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False
    notes: str = ""


@dataclass
class StrategyEffectiveness:
    """Track effectiveness of coping strategies."""
    strategy: str = ""
    times_used: int = 0
    avg_effectiveness: float = 0.0
    avg_recovery_minutes: float = 0.0
    success_rate: float = 0.0


class StressResponseCoach:
    """
    Personal stress response coach with pattern intelligence.
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
        self._events: deque = deque(maxlen=500)
        self._strategies: Dict[str, StrategyEffectiveness] = {}
        self._stats = {
            "total_events": 0,
            "avg_intensity": 0.0,
            "avg_recovery": 0.0,
            "resolved_count": 0,
            "current_stress_level": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_stress_event(self, trigger: str = "", intensity: float = 0.5, physical_symptoms: Optional[List[str]] = None, emotional_state: str = "", preceding_events: Optional[List[str]] = None, coping_strategy: str = "", strategy_effectiveness: float = 0.0, recovery_minutes: float = 0, notes: str = "") -> StressEvent:
        """Record a stress event."""
        event = StressEvent(
            trigger=trigger or "unspecified",
            intensity=intensity,
            physical_symptoms=physical_symptoms or [],
            emotional_state=emotional_state or "unspecified",
            preceding_events=preceding_events or [],
            coping_strategy=coping_strategy,
            strategy_effectiveness=strategy_effectiveness,
            recovery_minutes=recovery_minutes,
            notes=notes,
            resolved=strategy_effectiveness > 0.3,
        )

        with self._lock:
            self._events.append(event)
            self._stats["total_events"] += 1
            self._stats["current_stress_level"] = intensity
            if event.resolved:
                self._stats["resolved_count"] += 1
            self._update_strategy_stats(event)
            self._update_stats(event)

        self._save_stats()
        self._log_event(event)

        # Check for escalating pattern
        self._check_escalation()

        return event

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_stress_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Get stress pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self._events if e.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Trigger analysis
        trigger_counts = defaultdict(int)
        trigger_intensity = defaultdict(list)
        for e in recent:
            trigger_counts[e.trigger] += 1
            trigger_intensity[e.trigger].append(e.intensity)

        top_triggers = sorted(
            [(t, c, round(sum(trigger_intensity[t])/len(trigger_intensity[t]), 2)) for t, c in trigger_counts.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Time of day pattern
        by_hour = defaultdict(lambda: {"count": 0, "avg_intensity": 0.0})
        for e in recent:
            try:
                hour = datetime.fromisoformat(e.timestamp).hour
                by_hour[hour]["count"] += 1
                by_hour[hour]["avg_intensity"] = (by_hour[hour]["avg_intensity"] * (by_hour[hour]["count"] - 1) + e.intensity) / by_hour[hour]["count"]
            except Exception:
                pass

        risk_hours = [h for h, d in by_hour.items() if d["count"] >= 2 and d["avg_intensity"] > 0.6]

        # Recovery trend
        recovery_times = [e.recovery_minutes for e in recent if e.recovery_minutes > 0]
        avg_recovery = sum(recovery_times) / len(recovery_times) if recovery_times else 0

        # Physical symptom patterns
        symptom_counts = defaultdict(int)
        for e in recent:
            for s in e.physical_symptoms:
                symptom_counts[s] += 1

        return {
            "days_analyzed": len(set(e.timestamp[:10] for e in recent)),
            "total_events": len(recent),
            "avg_intensity": round(sum(e.intensity for e in recent) / len(recent), 2),
            "avg_recovery_minutes": round(avg_recovery, 1),
            "resolution_rate": round(sum(1 for e in recent if e.resolved) / len(recent) * 100, 1),
            "top_triggers": top_triggers,
            "risk_hours": sorted(risk_hours),
            "symptom_patterns": dict(symptom_counts),
            "escalation_risk": self._assess_escalation_risk(recent),
        }

    def get_intervention(self, current_stress: float = 0.0, trigger: str = "") -> Dict[str, Any]:
        """Get personalized stress intervention."""
        # Find most effective strategies
        effective = sorted(
            self._strategies.values(),
            key=lambda s: s.avg_effectiveness,
            reverse=True,
        )

        top_strategies = [s.strategy for s in effective[:3]] if effective else []

        # Strategy library
        strategy_library = {
            "box_breathing": {
                "name": "Box Breathing",
                "description": "Inhale 4 counts, hold 4, exhale 4, hold 4. Repeat for 2 minutes.",
                "duration": "2 minutes",
                "effectiveness": "immediate",
            },
            "grounding_5_4_3_2_1": {
                "name": "5-4-3-2-1 Grounding",
                "description": "Name 5 things you see, 4 you hear, 3 you can touch, 2 you smell, 1 you taste.",
                "duration": "1 minute",
                "effectiveness": "immediate",
            },
            "walk": {
                "name": "Take a Walk",
                "description": "Step outside. Walk for 5-10 minutes. No phone.",
                "duration": "10 minutes",
                "effectiveness": "5-10 minutes",
            },
            "cold_water": {
                "name": "Cold Water Reset",
                "description": "Splash cold water on your face or hold an ice cube. Activates the dive reflex.",
                "duration": "30 seconds",
                "effectiveness": "immediate",
            },
            "progressive_relaxation": {
                "name": "Progressive Muscle Relaxation",
                "description": "Tense and release each muscle group from toes to head.",
                "duration": "5 minutes",
                "effectiveness": "3-5 minutes",
            },
            "journaling": {
                "name": "Stress Dump",
                "description": "Write everything bothering you for 3 minutes. Don't edit. Then burn or delete it.",
                "duration": "3 minutes",
                "effectiveness": "3-5 minutes",
            },
        }

        # Pick strategy based on stress level and effectiveness
        if current_stress > 0.8:
            # High stress: immediate physical intervention
            chosen = "cold_water" if "cold_water" in top_strategies else "box_breathing"
        elif current_stress > 0.5:
            # Medium stress: grounding or breathing
            chosen = "grounding_5_4_3_2_1" if "grounding_5_4_3_2_1" in top_strategies else "box_breathing"
        else:
            # Low stress: preventive
            chosen = top_strategies[0] if top_strategies else "walk"

        detail = strategy_library.get(chosen, strategy_library["box_breathing"])

        return {
            "intervention": detail["name"],
            "description": detail["description"],
            "duration": detail["duration"],
            "expected_effectiveness": detail["effectiveness"],
            "reason": f"Based on your data, this technique resolves stress in ~{self._strategies.get(chosen, StrategyEffectiveness(strategy=chosen)).avg_recovery_minutes:.0f} minutes." if chosen in self._strategies else "A proven technique for stress reduction.",
            "alternative": [s for s in top_strategies[:2] if s != chosen],
        }

    def get_resilience_score(self) -> int:
        """Calculate resilience score (0-100)."""
        if not self._events:
            return 50

        recent = list(self._events)[-20:]
        n = len(recent)

        # Recovery speed trend
        recoveries = [e.recovery_minutes for e in recent if e.recovery_minutes > 0]
        if len(recoveries) >= 5:
            recent_avg = sum(recoveries[-5:]) / 5
            older_avg = sum(recoveries[:5]) / 5 if len(recoveries) >= 10 else recent_avg
            if recent_avg < older_avg:
                recovery_trend_score = 80  # improving
            else:
                recovery_trend_score = 40  # worsening
        else:
            recovery_trend_score = 50

        # Resolution rate
        resolution_rate = sum(1 for e in recent if e.resolved) / n * 100

        # Intensity trend (lower is better)
        intensity_trend = sum(e.intensity for e in recent) / n
        intensity_score = (1 - intensity_trend) * 100

        overall = round(recovery_trend_score * 0.3 + resolution_rate * 0.3 + intensity_score * 0.4)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_strategy_stats(self, event: StressEvent):
        """Update strategy effectiveness tracking."""
        if not event.coping_strategy:
            return

        strategy = event.coping_strategy
        if strategy not in self._strategies:
            self._strategies[strategy] = StrategyEffectiveness(strategy=strategy)

        se = self._strategies[strategy]
        se.times_used += 1
        se.avg_effectiveness = (se.avg_effectiveness * (se.times_used - 1) + event.strategy_effectiveness) / se.times_used
        if event.recovery_minutes > 0:
            se.avg_recovery_minutes = (se.avg_recovery_minutes * (se.times_used - 1) + event.recovery_minutes) / se.times_used
        se.success_rate = sum(1 for e in self._events if e.coping_strategy == strategy and e.resolved) / se.times_used

    def _update_stats(self, event: StressEvent):
        """Update running statistics."""
        n = self._stats["total_events"]
        self._stats["avg_intensity"] = round((self._stats["avg_intensity"] * (n - 1) + event.intensity) / n, 2)
        if event.recovery_minutes > 0:
            self._stats["avg_recovery"] = round((self._stats["avg_recovery"] * (self._stats["resolved_count"] - 1) + event.recovery_minutes) / self._stats["resolved_count"], 1) if self._stats["resolved_count"] > 0 else event.recovery_minutes

    def _check_escalation(self):
        """Check for stress escalation pattern."""
        recent = [e for e in self._events if e.timestamp > (datetime.now() - timedelta(hours=24)).isoformat()]
        if len(recent) >= 3:
            avg_intensity = sum(e.intensity for e in recent) / len(recent)
            if avg_intensity > 0.7:
                try:
                    from core.neural_bus import get_neural_bus
                    get_neural_bus().publish(
                        event_type="stress_escalation_alert",
                        domain="wellness",
                        payload={
                            "events_24h": len(recent),
                            "avg_intensity": round(avg_intensity, 2),
                            "suggestion": "Consider taking a full break. Your stress pattern is escalating.",
                        },
                    )
                except Exception:
                    pass

    def _assess_escalation_risk(self, events: List[StressEvent]) -> str:
        """Assess risk of stress escalation."""
        if len(events) < 5:
            return "insufficient_data"

        # Check increasing intensity trend
        intensities = [e.intensity for e in events]
        first_half = sum(intensities[:len(intensities)//2]) / max(1, len(intensities)//2)
        second_half = sum(intensities[len(intensities)//2:]) / max(1, len(intensities) - len(intensities)//2)

        if second_half > first_half * 1.3:
            return "escalating"
        elif second_half < first_half * 0.7:
            return "improving"
        else:
            return "stable"

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "strategies": {k: {
                    "strategy": v.strategy,
                    "times_used": v.times_used,
                    "avg_effectiveness": v.avg_effectiveness,
                    "avg_recovery_minutes": v.avg_recovery_minutes,
                    "success_rate": v.success_rate,
                } for k, v in self._strategies.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("strategies", {}).items():
                    self._strategies[k] = StrategyEffectiveness(**v)
        except Exception:
            pass

    def _log_event(self, event: StressEvent):
        try:
            with open(STRESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": event.timestamp,
                    "trigger": event.trigger,
                    "intensity": event.intensity,
                    "strategy": event.coping_strategy,
                    "effectiveness": event.strategy_effectiveness,
                    "recovery": event.recovery_minutes,
                    "resolved": event.resolved,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_src_instance: Optional[StressResponseCoach] = None
_src_lock = threading.Lock()


def get_stress_response_coach() -> StressResponseCoach:
    global _src_instance
    with _src_lock:
        if _src_instance is None:
            _src_instance = StressResponseCoach()
        return _src_instance
