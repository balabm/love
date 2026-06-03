"""
LOVE Life Phase Navigator — Transition Intelligence (Modern AI Pattern)

Most people drift through life phases. This navigator:

1. PHASE TRACKING
   - Record life phases and their characteristics
   - Track phase types (career, relationship, location, identity, health)
   - Log satisfaction, growth, and readiness for transition

2. PATTERN ANALYSIS
   - Identify the user's phase profile (stuck, flowing, resisting, seeking)
   - Find transition patterns that create growth vs regression
   - Detect premature exits and overdue stays

3. TRANSITION OPTIMIZATION
   - Suggest readiness assessments for potential transitions
   - Provide frameworks for graceful exits and entries
   - Recommend timing and preparation for major changes

4. GROWTH CULTIVATION
   - Track the correlation between transitions and identity evolution
   - Alert when a phase has become a prison
   - Celebrate transitions that expanded the self

Architecture:
- record_phase(phase, type, satisfaction, growth, readiness): Log phase
- get_phase_stats(): Get phase pattern analysis
- get_transition_suggestion(phase, readiness, context): Get suggestion
- get_phase_score(): Calculate overall phase health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "life_phase_navigator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PHASE_LOG = DATA_DIR / "phases.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PhaseEntry:
    """A tracked life phase entry."""
    entry_id: str = ""
    phase: str = ""  # what phase
    phase_type: str = ""  # career, relationship, location, identity, health, creative
    satisfaction: float = 0.5  # 0-1
    growth: float = 0.0  # 0-1
    readiness: float = 0.0  # 0-1 ready to transition?
    duration_months: float = 0.0
    integration: float = 0.0  # 0-1 how well integrated?
    fear_of_change: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LifePhaseNavigator:
    """
    Intelligent life phase navigator with transition detection and growth optimization.
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
            "avg_satisfaction": 0.0,
            "avg_growth": 0.0,
            "phase_prison_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_phase(self, phase: str = "", phase_type: str = "", satisfaction: float = 0.5, growth: float = 0.0, readiness: float = 0.0, duration_months: float = 0.0, integration: float = 0.0, fear_of_change: float = 0.0, notes: str = "") -> PhaseEntry:
        """Record a phase entry."""
        entry_id = f"phs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PhaseEntry(
            entry_id=entry_id,
            phase=phase or "unspecified",
            phase_type=phase_type or "general",
            satisfaction=satisfaction,
            growth=growth,
            readiness=readiness,
            duration_months=duration_months,
            integration=integration,
            fear_of_change=fear_of_change,
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

    def get_phase_stats(self) -> Dict[str, Any]:
        """Get phase pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "satisfaction_sum": 0.0, "growth_sum": 0.0, "readiness_sum": 0.0})
        for e in self._entries:
            by_type[e.phase_type]["count"] += 1
            by_type[e.phase_type]["satisfaction_sum"] += e.satisfaction
            by_type[e.phase_type]["growth_sum"] += e.growth
            by_type[e.phase_type]["readiness_sum"] += e.readiness

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_readiness": round(data["readiness_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_growth"]) if type_stats else ("", {})

        # Satisfaction vs growth
        high_sat = [e for e in self._entries if e.satisfaction > 0.7]
        low_sat = [e for e in self._entries if e.satisfaction < 0.4]
        if high_sat and low_sat:
            high_sat_growth = sum(e.growth for e in high_sat) / len(high_sat)
            low_sat_growth = sum(e.growth for e in low_sat) / len(low_sat)
        else:
            high_sat_growth = 0
            low_sat_growth = 0

        # Readiness analysis
        high_ready = [e for e in self._entries if e.readiness > 0.7]
        low_ready = [e for e in self._entries if e.readiness < 0.4]
        if high_ready and low_ready:
            high_ready_sat = sum(e.satisfaction for e in high_ready) / len(high_ready)
            low_ready_sat = sum(e.satisfaction for e in low_ready) / len(low_ready)
            high_ready_fear = sum(e.fear_of_change for e in high_ready) / len(high_ready)
            low_ready_fear = sum(e.fear_of_change for e in low_ready) / len(low_ready)
        else:
            high_ready_sat = 0
            low_ready_sat = 0
            high_ready_fear = 0
            low_ready_fear = 0

        # Duration analysis
        long_phase = [e for e in self._entries if e.duration_months > 36]
        short_phase = [e for e in self._entries if e.duration_months < 12]
        if long_phase and short_phase:
            long_growth = sum(e.growth for e in long_phase) / len(long_phase)
            short_growth = sum(e.growth for e in short_phase) / len(short_phase)
        else:
            long_growth = 0
            short_growth = 0

        # Phase prison detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
        if recent:
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
            recent_fear = sum(e.fear_of_change for e in recent) / len(recent)
            phase_prison_risk = recent_sat < 0.4 and recent_growth < 0.3 and recent_fear > 0.6
        else:
            phase_prison_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "satisfaction_growth": {
                "high_satisfaction_growth": round(high_sat_growth, 2),
                "low_satisfaction_growth": round(low_sat_growth, 2),
            },
            "readiness_effect": {
                "high_readiness_satisfaction": round(high_ready_sat, 2),
                "low_readiness_satisfaction": round(low_ready_sat, 2),
                "high_readiness_fear": round(high_ready_fear, 2),
                "low_readiness_fear": round(low_ready_fear, 2),
            },
            "duration_effect": {
                "long_phase_growth": round(long_growth, 2),
                "short_phase_growth": round(short_growth, 2),
            },
            "phase_prison_risk": phase_prison_risk,
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
            "avg_growth": round(sum(e.growth for e in self._entries) / len(self._entries), 2),
        }

    def get_transition_suggestion(self, phase: str = "", readiness: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get transition suggestion."""
        suggestions = [
            "The fear you feel is not a signal to stop. It's a signal that you're growing. Every meaningful transition is preceded by fear. The absence of fear usually means the transition is too small.",
            "Don't leave until you know what you're leaving for. Clarity about the next phase makes the exit graceful. The worst transitions are escape, not pursuit.",
            "Grieve the ending. Even good transitions involve loss. The familiar. The identity. The competence. Let yourself feel it. Unmourned endings haunt new beginnings.",
            "Transitions are not events. They're processes. The new phase doesn't begin the day you leave the old one. It begins the day you start imagining it.",
            "Ask yourself: Am I staying because it's right, or because I'm afraid? If it's fear, the answer is almost always to go. Fear-based staying corrodes the soul.",
            "The person you become during transitions is more important than the transition itself. Transitions are identity laboratories. Who are you becoming?",
            "Don't make major decisions from exhaustion. Transition clarity requires energy. Rest first. Decide second. The decision made in depletion is rarely the right one.",
            "Tell people you're transitioning. Secrets increase fear. Vulnerability invites support. The transition you announce is easier than the transition you hide.",
            "Create a ritual for the ending. A letter. A gathering. A moment of acknowledgment. Rituals help the psyche close one door before opening another.",
            "Every phase has an expiration date. Not because it becomes bad. Because you become different. The phase that fit you at 25 cannot fit you at 45. That's not failure. That's growth.",
        ]

        if readiness < 0.3:
            readiness_note = "Low readiness. Don't force it. Explore. Imagine. Gather information. The transition will come when you're ready."
        elif readiness < 0.6:
            readiness_note = "Moderate readiness. Start preparing. Save money. Build skills. Strengthen relationships. Make the transition possible before you make it."
        else:
            readiness_note = "High readiness. You're ready. The only thing holding you back is fear. And fear is not a stop sign. It's a yield sign. Proceed with courage."

        return {
            "phase": phase or "general",
            "readiness": readiness,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "readiness_note": readiness_note,
            "principle": "Life is a series of phases. Each phase has something to teach. And each phase eventually becomes a cage if you stay too long. The art of living well is knowing when to commit and when to release. Most people stay too long in phases that have completed their purpose. They confuse loyalty with wisdom. They confuse comfort with rightness. The person who never transitions becomes a fossil of their former self. Transitions are not disruptions. They're the mechanism of growth. The self that emerges from transition is always larger than the self that entered it. That's the reward for the courage of change.",
        }

    def get_phase_score(self) -> int:
        """Calculate overall phase health (0-100)."""
        if not self._entries:
            return 25

        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)
        avg_readiness = sum(e.readiness for e in self._entries) / len(self._entries)
        avg_integration = sum(e.integration for e in self._entries) / len(self._entries)
        avg_fear = sum(e.fear_of_change for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-5:]
        if recent:
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
        else:
            recent_sat = 0
            recent_growth = 0

        # Phase prison penalty
        prison_penalty = 0
        last_180 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
        if last_180:
            recent_sat_180 = sum(e.satisfaction for e in last_180) / len(last_180)
            recent_growth_180 = sum(e.growth for e in last_180) / len(last_180)
            recent_fear_180 = sum(e.fear_of_change for e in last_180) / len(last_180)
            if recent_sat_180 < 0.4 and recent_growth_180 < 0.3 and recent_fear_180 > 0.6:
                prison_penalty = 15

        # Type variety
        unique_types = len(set(e.phase_type for e in self._entries))

        score = (avg_sat * 20) + (avg_growth * 25) + (avg_readiness * 15) + (avg_integration * 15) + (recent_sat * 10) + (recent_growth * 10) + (unique_types * 2) - (avg_fear * 5) - prison_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)
            self._stats["avg_growth"] = round(sum(e.growth for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
            if recent:
                recent_sat = sum(e.satisfaction for e in recent) / len(recent)
                recent_growth = sum(e.growth for e in recent) / len(recent)
                recent_fear = sum(e.fear_of_change for e in recent) / len(recent)
                self._stats["phase_prison_risk"] = recent_sat < 0.4 and recent_growth < 0.3 and recent_fear > 0.6
            else:
                self._stats["phase_prison_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.life_phase_navigator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.life_phase_navigator")

    def _log_entry(self, entry: PhaseEntry):
        try:
            with open(PHASE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "phase": entry.phase,
                    "phase_type": entry.phase_type,
                    "satisfaction": entry.satisfaction,
                    "growth": entry.growth,
                    "readiness": entry.readiness,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.life_phase_navigator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lpn_instance: Optional[LifePhaseNavigator] = None
_lpn_lock = threading.Lock()


def get_life_phase_navigator() -> LifePhaseNavigator:
    global _lpn_instance
    with _lpn_lock:
        if _lpn_instance is None:
            _lpn_instance = LifePhaseNavigator()
        return _lpn_instance
