"""
LOVE Energy Protector — Vitality Intelligence (Modern AI Pattern)

Most people give away their energy without tracking where it goes. This protector:

1. ENERGY TRACKING
   - Record energy drains and energy sources throughout the day
   - Track energy by activity, person, environment, and time
   - Log recovery activities and their effectiveness

2. PATTERN ANALYSIS
   - Identify energy vampires (people, tasks, environments, apps)
   - Find energy amplifiers (activities, people, environments, times)
   - Detect energy debt accumulation before burnout

3. PROTECTION STRATEGIES
   - Suggest energy boundaries for current context
   - Provide recovery protocols for different energy states
   - Recommend energy-honoring scheduling

4. PROACTIVE MANAGEMENT
   - Alert when energy expenditure exceeds recovery
   - Suggest energy-protecting rituals and habits
   - Track energy ROI of commitments

Architecture:
- record_energy_event(type, source, impact, duration): Log event
- get_energy_stats(): Get energy pattern analysis
- get_protection_strategy(current_energy, upcoming): Get protection plan
- get_energy_score(): Calculate overall energy health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "energy_protector"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENERGY_LOG = DATA_DIR / "energy.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EnergyEvent:
    """A tracked energy event."""
    event_id: str = ""
    event_type: str = ""  # drain, source, recovery, neutral
    source: str = ""  # what caused it
    source_category: str = ""  # person, task, environment, app, food, sleep, movement, thought
    impact: float = 0.0  # -1 to 1
    duration_minutes: float = 0.0
    energy_before: float = 0.5  # 0-1
    energy_after: float = 0.5  # 0-1
    time_of_day: str = ""
    recoverable: bool = True  # can energy be recovered from this
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EnergyProtector:
    """
    Intelligent energy protector with drain/source analysis and proactive boundary setting.
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
            "avg_impact": 0.0,
            "biggest_drain": "",
            "best_source": "",
            "energy_balance": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_energy_event(self, event_type: str = "", source: str = "", source_category: str = "", impact: float = 0.0, duration: float = 0, energy_before: float = 0.5, energy_after: float = 0.5, time_of_day: str = "", recoverable: bool = True, notes: str = "") -> EnergyEvent:
        """Record an energy event."""
        event_id = f"energy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._events)}"
        event = EnergyEvent(
            event_id=event_id,
            event_type=event_type or "neutral",
            source=source or "unspecified",
            source_category=source_category or "task",
            impact=impact,
            duration_minutes=duration,
            energy_before=energy_before,
            energy_after=energy_after,
            time_of_day=time_of_day or datetime.now().strftime("%H:%M"),
            recoverable=recoverable,
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

    def get_energy_stats(self) -> Dict[str, Any]:
        """Get energy pattern analysis."""
        if not self._events:
            return {"status": "insufficient_data"}

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "impact_sum": 0.0, "duration": 0.0, "drain": 0, "source": 0})
        for e in self._events:
            by_source[e.source]["count"] += 1
            by_source[e.source]["impact_sum"] += e.impact
            by_source[e.source]["duration"] += e.duration_minutes
            if e.impact < -0.3:
                by_source[e.source]["drain"] += 1
            elif e.impact > 0.3:
                by_source[e.source]["source"] += 1

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_impact": round(data["impact_sum"] / count, 2),
                "total_duration": round(data["duration"], 1),
                "drain_count": data["drain"],
                "source_count": data["source"],
                "type": "drain" if data["impact_sum"] < -0.5 else "source" if data["impact_sum"] > 0.5 else "neutral",
            }

        biggest_drain = min(source_stats.items(), key=lambda x: x[1]["avg_impact"]) if source_stats else ("", {})
        best_source = max(source_stats.items(), key=lambda x: x[1]["avg_impact"]) if source_stats else ("", {})

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "impact_sum": 0.0})
        for e in self._events:
            by_category[e.source_category]["count"] += 1
            by_category[e.source_category]["impact_sum"] += e.impact

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            category_stats[c] = {
                "count": count,
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Time analysis
        by_hour = defaultdict(lambda: {"count": 0, "impact_sum": 0.0})
        for e in self._events:
            hour = e.time_of_day[:2] if e.time_of_day else "00"
            by_hour[hour]["count"] += 1
            by_hour[hour]["impact_sum"] += e.impact

        time_stats = {}
        for h, data in by_hour.items():
            count = data["count"]
            if count >= 2:
                time_stats[h] = {
                    "count": count,
                    "avg_impact": round(data["impact_sum"] / count, 2),
                }

        # Energy balance (last 7 days)
        recent = [e for e in self._events if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        if recent:
            balance = sum(e.impact for e in recent)
        else:
            balance = 0

        # Recovery analysis
        recoveries = [e for e in self._events if e.event_type == "recovery"]
        if recoveries:
            avg_recovery_effectiveness = sum(e.energy_after - e.energy_before for e in recoveries) / len(recoveries)
        else:
            avg_recovery_effectiveness = 0

        return {
            "total_events": len(self._events),
            "source_stats": source_stats,
            "biggest_drain": biggest_drain[0],
            "best_source": best_source[0],
            "category_stats": category_stats,
            "time_stats": time_stats,
            "energy_balance_7d": round(balance, 2),
            "avg_recovery_effectiveness": round(avg_recovery_effectiveness, 2),
            "current_trend": "depleting" if balance < -2 else "stable" if balance < 2 else "building",
        }

    def get_protection_strategy(self, current_energy: float = 0.5, upcoming_commitments: Optional[List[str]] = None, time_available: float = 10) -> Dict[str, Any]:
        """Get protection plan."""
        upcoming_commitments = upcoming_commitments or []

        if current_energy < 0.2:
            urgency = "critical"
            message = "Your energy is critically low. Cancel anything non-essential. Recovery is your only job right now."
            actions = [
                "Close your eyes for 5 minutes. Set a timer. Breathe.",
                "Eat something with protein and complex carbs.",
                "Drink a full glass of water.",
                "Do not make any important decisions right now.",
            ]
        elif current_energy < 0.4:
            urgency = "high"
            message = "Energy is low. Protect what you have. Do the minimum on commitments. Prioritize recovery."
            actions = [
                "Identify one commitment you can defer or delegate",
                "Do a 10-minute restorative activity (walk, stretch, music)",
                "Set your status to 'low energy - urgent only'",
                "Eat something nourishing within the next hour",
            ]
        elif current_energy < 0.6:
            urgency = "medium"
            message = "Moderate energy. Be selective. Say no to at least one thing today."
            actions = [
                "Before each task, ask: 'Does this build or drain energy?'",
                "Schedule a 15-minute recovery block",
                "Avoid energy vampires for the rest of the day",
                "Do one thing that reliably gives you energy",
            ]
        else:
            urgency = "low"
            message = "Good energy. Use it wisely. Don't spend it all. Bank some for tomorrow."
            actions = [
                "Do your hardest/most important task now",
                "Help someone else (giving energy often creates more)",
                "Set a boundary so you don't overspend",
                "Notice what's working and do more of it",
            ]

        # Commitment-specific advice
        commitment_notes = []
        for commitment in upcoming_commitments:
            if current_energy < 0.3:
                commitment_notes.append(f"'{commitment}' - Consider postponing or doing a minimal version")
            elif current_energy < 0.5:
                commitment_notes.append(f"'{commitment}' - Do a reduced version. 60% is better than 0%.")
            else:
                commitment_notes.append(f"'{commitment}' - You have energy for this. Give it your attention.")

        return {
            "current_energy": current_energy,
            "urgency": urgency,
            "message": message,
            "actions": actions,
            "commitment_notes": commitment_notes,
            "time_available": time_available,
            "reminder": "Energy is your most finite resource. Protect it like your life depends on it. Because it does.",
        }

    def get_energy_score(self) -> int:
        """Calculate overall energy health (0-100)."""
        if not self._events:
            return 45

        # Recent balance
        recent = [e for e in self._events if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        if recent:
            balance = sum(e.impact for e in recent)
        else:
            balance = 0

        # Recovery effectiveness
        recoveries = [e for e in self._events if e.event_type == "recovery"]
        if recoveries:
            recovery_effectiveness = sum(e.energy_after - e.energy_before for e in recoveries) / len(recoveries)
        else:
            recovery_effectiveness = 0

        # Source diversity
        unique_sources = len(set(e.source for e in self._events if e.impact > 0))

        # Drain management (recoverable drains)
        drains = [e for e in self._events if e.impact < -0.3]
        if drains:
            recoverable_rate = sum(1 for e in drains if e.recoverable) / len(drains)
        else:
            recoverable_rate = 1.0

        # Recent trend
        recent_events = list(self._events)[-20:]
        if len(recent_events) >= 10:
            recent_impact = sum(e.impact for e in recent_events) / len(recent_events)
        else:
            recent_impact = 0

        score = 50 + (balance * 3) + (recovery_effectiveness * 15) + (unique_sources * 2) + (recoverable_rate * 10) + (recent_impact * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._events:
            self._stats["avg_impact"] = round(sum(e.impact for e in self._events) / len(self._events), 2)
            self._stats["energy_balance"] = round(sum(e.impact for e in self._events), 2)

            by_source = defaultdict(lambda: {"impact": 0.0, "count": 0})
            for e in self._events:
                by_source[e.source]["impact"] += e.impact
                by_source[e.source]["count"] += 1
            
            if by_source:
                biggest_drain = min(by_source.items(), key=lambda x: x[1]["impact"] / max(1, x[1]["count"]))
                best_source = max(by_source.items(), key=lambda x: x[1]["impact"] / max(1, x[1]["count"]))
                self._stats["biggest_drain"] = biggest_drain[0]
                self._stats["best_source"] = best_source[0]

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

    def _log_event(self, event: EnergyEvent):
        try:
            with open(ENERGY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": event.timestamp,
                    "type": event.event_type,
                    "source": event.source,
                    "category": event.source_category,
                    "impact": event.impact,
                    "energy_before": event.energy_before,
                    "energy_after": event.energy_after,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ep_instance: Optional[EnergyProtector] = None
_ep_lock = threading.Lock()


def get_energy_protector() -> EnergyProtector:
    global _ep_instance
    with _ep_lock:
        if _ep_instance is None:
            _ep_instance = EnergyProtector()
        return _ep_instance
