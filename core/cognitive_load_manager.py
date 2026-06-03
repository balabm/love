"""
LOVE Cognitive Load Manager — Mental Bandwidth Intelligence (Modern AI Pattern)

Most cognitive overload is invisible until it crashes you. This manager:

1. LOAD TRACKING
   - Record cognitive load events and their characteristics
   - Track load sources (decisions, information, tasks, emotions, context switches)
   - Log load indicators (errors, forgetfulness, irritability, fatigue)

2. PATTERN ANALYSIS
   - Identify the user's cognitive load profile (high intrinsic, high extraneous, low germane)
   - Find load spikes and their triggers
   - Detect chronic overload patterns

3. LOAD MANAGEMENT
   - Suggest load reduction strategies
   - Provide cognitive offloading techniques
   - Recommend peak load scheduling

4. PREVENTION
   - Track cognitive trends and predict overload
   - Alert when load is approaching capacity
   - Celebrate effective load management

Architecture:
- record_load_event(source, intensity, indicators): Log event
- get_cognitive_stats(): Get cognitive load pattern analysis
- get_load_reduction(strategy, current_load): Get strategy
- get_cognitive_score(): Calculate overall cognitive health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "cognitive_load_manager"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOAD_LOG = DATA_DIR / "load.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class LoadEvent:
    """A tracked cognitive load event."""
    event_id: str = ""
    source: str = ""  # decisions, information, tasks, emotions, context_switches, interruptions, uncertainty
    intensity: float = 0.5  # 0-1
    duration_minutes: float = 0.0
    indicators: List[str] = field(default_factory=list)  # errors, forgetfulness, irritability, fatigue, confusion, headache
    energy_before: float = 0.5
    energy_after: float = 0.5
    performance: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CognitiveLoadManager:
    """
    Intelligent cognitive load manager with overload prediction and reduction strategies.
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
            "peak_source": "",
            "overload_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_load_event(self, source: str = "", intensity: float = 0.5, duration: float = 0, indicators: Optional[List[str]] = None, energy_before: float = 0.5, energy_after: float = 0.5, performance: float = 0.5, notes: str = "") -> LoadEvent:
        """Record a load event."""
        event_id = f"load_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._events)}"
        event = LoadEvent(
            event_id=event_id,
            source=source or "unspecified",
            intensity=intensity,
            duration_minutes=duration,
            indicators=indicators or [],
            energy_before=energy_before,
            energy_after=energy_after,
            performance=performance,
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

    def get_cognitive_stats(self) -> Dict[str, Any]:
        """Get cognitive load pattern analysis."""
        if not self._events:
            return {"status": "insufficient_data"}

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "duration_sum": 0.0, "performance_sum": 0.0})
        for e in self._events:
            by_source[e.source]["count"] += 1
            by_source[e.source]["intensity_sum"] += e.intensity
            by_source[e.source]["duration_sum"] += e.duration_minutes
            by_source[e.source]["performance_sum"] += e.performance

        source_stats = {}
        for src, data in by_source.items():
            count = data["count"]
            source_stats[src] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "total_duration": round(data["duration_sum"], 1),
                "avg_performance": round(data["performance_sum"] / count, 2),
            }

        peak_source = max(source_stats.items(), key=lambda x: x[1]["avg_intensity"] * x[1]["count"]) if source_stats else ("", {})

        # Indicator analysis
        by_indicator = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for e in self._events:
            for ind in e.indicators:
                by_indicator[ind]["count"] += 1
                by_indicator[ind]["intensity_sum"] += e.intensity

        indicator_stats = {}
        for ind, data in by_indicator.items():
            count = data["count"]
            indicator_stats[ind] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
            }

        # Load trend
        recent = list(self._events)[-14:]
        if recent:
            recent_intensity = sum(e.intensity for e in recent) / len(recent)
            recent_indicators = sum(len(e.indicators) for e in recent) / len(recent)
        else:
            recent_intensity = 0
            recent_indicators = 0

        older = list(self._events)[:-14] if len(self._events) > 14 else []
        if older:
            older_intensity = sum(e.intensity for e in older) / len(older)
            older_indicators = sum(len(e.indicators) for e in older) / len(older)
            intensity_trend = recent_intensity - older_intensity
            indicator_trend = recent_indicators - older_indicators
        else:
            intensity_trend = 0
            indicator_trend = 0

        # Overload risk
        if recent:
            high_intensity = sum(1 for e in recent if e.intensity > 0.7) / len(recent)
            many_indicators = sum(1 for e in recent if len(e.indicators) > 2) / len(recent)
            overload_risk = high_intensity > 0.3 or many_indicators > 0.3
        else:
            overload_risk = False

        # Performance impact
        high_load = [e for e in self._events if e.intensity > 0.6]
        low_load = [e for e in self._events if e.intensity <= 0.4]
        if high_load and low_load:
            high_perf = sum(e.performance for e in high_load) / len(high_load)
            low_perf = sum(e.performance for e in low_load) / len(low_load)
            perf_impact = low_perf - high_perf
        else:
            perf_impact = 0

        return {
            "total_events": len(self._events),
            "source_stats": source_stats,
            "peak_source": peak_source[0],
            "indicator_stats": indicator_stats,
            "avg_intensity": round(sum(e.intensity for e in self._events) / len(self._events), 2),
            "avg_performance": round(sum(e.performance for e in self._events) / len(self._events), 2),
            "intensity_trend": round(intensity_trend, 2),
            "indicator_trend": round(indicator_trend, 2),
            "overload_risk": overload_risk,
            "performance_impact": round(perf_impact, 2),
        }

    def get_load_reduction(self, strategy: str = "", current_load: float = 0.5) -> Dict[str, Any]:
        """Get strategy."""
        strategies = {
            "decision": [
                "Make trivial decisions in advance. Wardrobe, meals, routes. Save decision energy for what matters.",
                "Use the 2-minute rule: If it takes less than 2 minutes, do it now. Don't let small decisions accumulate.",
                "Set defaults. Every default decision you make is one less decision later.",
            ],
            "information": [
                "Close all tabs except the one you're using. Information is not knowledge.",
                "Unsubscribe from one email list today. Information diet.",
                "Use the 5-second rule: If you can't decide in 5 seconds, bookmark it and move on.",
            ],
            "tasks": [
                "Do one thing at a time. Multitasking is task-switching with a fancy name.",
                "Batch similar tasks. Context switching is expensive.",
                "Delegate or eliminate one task today. You don't have to do it all.",
            ],
            "emotions": [
                "Name the emotion. 'I'm anxious about X.' Naming reduces amygdala activation.",
                "Set a timer for 10 minutes. Worry only during that time. Then stop.",
                "Write it down. Paper can hold the worry so your brain doesn't have to.",
            ],
            "context": [
                "Turn off all notifications. Every ping is a context switch you didn't choose.",
                "Use Do Not Disturb mode for 2-hour blocks. Protect your focus.",
                "Close your door. Put on headphones. Signal that you're unavailable.",
            ],
            "general": [
                "Take a 5-minute break every 25 minutes. Your brain can't sustain focus indefinitely.",
                "Walk away from the problem. Physical movement helps cognitive processing.",
                "Sleep on it. Your brain processes information during sleep.",
            ],
        }

        selected = strategies.get(strategy, strategies["general"])

        if current_load > 0.8:
            urgency = "Critical cognitive overload. Stop adding tasks. Start removing them."
        elif current_load > 0.6:
            urgency = "High load. Prioritize ruthlessly. Not everything needs to happen today."
        elif current_load > 0.4:
            urgency = "Moderate load. Manage carefully. Don't let it accumulate."
        else:
            urgency = "Low load. Good time to tackle complex tasks. Use this bandwidth wisely."

        return {
            "strategy": strategy or "general",
            "current_load": current_load,
            "reduction_technique": random.choice(selected),
            "urgency": urgency,
            "principle": "Your brain has limited working memory. Every decision, every notification, every unresolved task takes up space. Clear the clutter.",
        }

    def get_cognitive_score(self) -> int:
        """Calculate overall cognitive health (0-100)."""
        if not self._events:
            return 35

        # Low intensity
        avg_intensity = sum(e.intensity for e in self._events) / len(self._events)

        # High performance
        avg_performance = sum(e.performance for e in self._events) / len(self._events)

        # Low indicators
        avg_indicators = sum(len(e.indicators) for e in self._events) / len(self._events)

        # Energy sustainability
        avg_energy_change = sum(e.energy_after - e.energy_before for e in self._events) / len(self._events)

        # Recent trend
        recent = list(self._events)[-14:]
        if recent:
            recent_intensity = sum(e.intensity for e in recent) / len(recent)
            recent_performance = sum(e.performance for e in recent) / len(recent)
        else:
            recent_intensity = 0
            recent_performance = 0

        older = list(self._events)[:-14] if len(self._events) > 14 else []
        if older:
            older_intensity = sum(e.intensity for e in older) / len(older)
            trend = older_intensity - recent_intensity  # positive is good
        else:
            trend = 0

        # Overload penalty
        if recent:
            high_intensity = sum(1 for e in recent if e.intensity > 0.7) / len(recent)
            overload_penalty = min(20, high_intensity * 30)
        else:
            overload_penalty = 0

        score = ((1 - avg_intensity) * 20) + (avg_performance * 25) + ((3 - avg_indicators) / 3 * 15) + (avg_energy_change * 10) + (recent_performance * 15) + (trend * 10) - overload_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._events:
            self._stats["avg_intensity"] = round(sum(e.intensity for e in self._events) / len(self._events), 2)

            by_source = defaultdict(lambda: {"intensity": 0.0, "count": 0})
            for e in self._events:
                by_source[e.source]["intensity"] += e.intensity
                by_source[e.source]["count"] += 1
            if by_source:
                peak = max(by_source.items(), key=lambda x: x[1]["intensity"] / max(1, x[1]["count"]))
                self._stats["peak_source"] = peak[0]

            recent = [e for e in self._events if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
            if recent:
                high_intensity = sum(1 for e in recent if e.intensity > 0.7) / len(recent)
                many_indicators = sum(1 for e in recent if len(e.indicators) > 2) / len(recent)
                self._stats["overload_risk"] = high_intensity > 0.3 or many_indicators > 0.3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_load_manager")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_load_manager")

    def _log_event(self, event: LoadEvent):
        try:
            with open(LOAD_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": event.timestamp,
                    "source": event.source,
                    "intensity": event.intensity,
                    "duration": event.duration_minutes,
                    "indicators": event.indicators,
                    "performance": event.performance,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_load_manager")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_clm_instance: Optional[CognitiveLoadManager] = None
_clm_lock = threading.Lock()


def get_cognitive_load_manager() -> CognitiveLoadManager:
    global _clm_instance
    with _clm_lock:
        if _clm_instance is None:
            _clm_instance = CognitiveLoadManager()
        return _clm_instance
