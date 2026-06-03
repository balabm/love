"""
LOVE Attention Recovery Specialist — Attention Restoration Intelligence (Modern AI Pattern)

Most people never recover their attention fully. This specialist:

1. ATTENTION TRACKING
   - Record attention states and their characteristics
   - Track attention depletion events and their sources
   - Log attention recovery activities and their effectiveness

2. PATTERN ANALYSIS
   - Identify the user's attention profile (sustained, selective, divided, alternating)
   - Find attention drains and their cumulative effects
   - Detect attention bankruptcy (when focus is impossible)

3. RECOVERY DESIGN
   - Suggest attention restoration activities matched to depletion type
   - Provide micro-recovery options for busy periods
   - Recommend attention hygiene practices

4. PREVENTION
   - Track attention trends and predict bankruptcy
   - Alert when attention is being eroded
   - Celebrate attention wins

Architecture:
- record_attention_state(focus, source, duration): Log state
- get_attention_stats(): Get attention pattern analysis
- get_recovery_protocol(depletion_type, urgency): Get protocol
- get_attention_score(): Calculate overall attention health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "attention_recovery_specialist"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ATTENTION_LOG = DATA_DIR / "attention.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AttentionState:
    """A tracked attention state."""
    state_id: str = ""
    focus_level: float = 0.5  # 0-1
    attention_type: str = ""  # sustained, selective, divided, alternating
    source: str = ""  # work, social_media, meeting, notification, stress, fatigue
    duration_minutes: float = 0.0
    energy_level: float = 0.5  # 0-1
    recovery_activity: str = ""  # what they did to recover
    recovery_effectiveness: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AttentionRecoverySpecialist:
    """
    Intelligent attention recovery specialist with depletion prediction and personalized protocols.
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
        self._states: deque = deque(maxlen=300)
        self._stats = {
            "total_states": 0,
            "avg_focus": 0.0,
            "avg_recovery": 0.0,
            "primary_drain": "",
            "bankruptcy_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_attention_state(self, focus_level: float = 0.5, attention_type: str = "", source: str = "", duration: float = 0, energy_level: float = 0.5, recovery_activity: str = "", recovery_effectiveness: float = 0.0, notes: str = "") -> AttentionState:
        """Record an attention state."""
        state_id = f"att_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._states)}"
        state = AttentionState(
            state_id=state_id,
            focus_level=focus_level,
            attention_type=attention_type or "sustained",
            source=source or "unspecified",
            duration_minutes=duration,
            energy_level=energy_level,
            recovery_activity=recovery_activity,
            recovery_effectiveness=recovery_effectiveness,
            notes=notes,
        )

        with self._lock:
            self._states.append(state)
            self._stats["total_states"] += 1
            self._update_stats()

        self._save_stats()
        self._log_state(state)

        return state

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_attention_stats(self) -> Dict[str, Any]:
        """Get attention pattern analysis."""
        if not self._states:
            return {"status": "insufficient_data"}

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "focus_sum": 0.0, "duration_sum": 0.0, "recovery_sum": 0.0})
        for s in self._states:
            by_source[s.source]["count"] += 1
            by_source[s.source]["focus_sum"] += s.focus_level
            by_source[s.source]["duration_sum"] += s.duration_minutes
            by_source[s.source]["recovery_sum"] += s.recovery_effectiveness

        source_stats = {}
        for src, data in by_source.items():
            count = data["count"]
            source_stats[src] = {
                "count": count,
                "avg_focus": round(data["focus_sum"] / count, 2),
                "total_duration": round(data["duration_sum"], 1),
                "avg_recovery": round(data["recovery_sum"] / count, 2),
            }

        primary_drain = min(source_stats.items(), key=lambda x: x[1]["avg_focus"]) if source_stats else ("", {})

        # Attention type analysis
        by_type = defaultdict(lambda: {"count": 0, "focus_sum": 0.0})
        for s in self._states:
            by_type[s.attention_type]["count"] += 1
            by_type[s.attention_type]["focus_sum"] += s.focus_level

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_focus": round(data["focus_sum"] / count, 2),
            }

        # Recovery analysis
        with_recovery = [s for s in self._states if s.recovery_activity]
        if with_recovery:
            by_activity = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
            for s in with_recovery:
                by_activity[s.recovery_activity]["count"] += 1
                by_activity[s.recovery_activity]["effectiveness_sum"] += s.recovery_effectiveness

            recovery_stats = {}
            for act, data in by_activity.items():
                count = data["count"]
                if count >= 2:
                    recovery_stats[act] = {
                        "count": count,
                        "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                    }
        else:
            recovery_stats = {}

        best_recovery = max(recovery_stats.items(), key=lambda x: x[1]["avg_effectiveness"]) if recovery_stats else ("", {})

        # Bankruptcy risk (low focus + high drain over time)
        recent = list(self._states)[-14:]
        if recent:
            avg_recent_focus = sum(s.focus_level for s in recent) / len(recent)
            low_focus_days = sum(1 for s in recent if s.focus_level < 0.4)
            bankruptcy_risk = avg_recent_focus < 0.4 and low_focus_days > 7
        else:
            bankruptcy_risk = False

        # Trend
        if len(self._states) > 14:
            older = list(self._states)[:-14]
            recent_focus = sum(s.focus_level for s in recent) / len(recent)
            older_focus = sum(s.focus_level for s in older) / len(older)
            trend = recent_focus - older_focus
        else:
            trend = 0

        return {
            "total_states": len(self._states),
            "source_stats": source_stats,
            "primary_drain": primary_drain[0],
            "type_stats": type_stats,
            "recovery_stats": recovery_stats,
            "best_recovery": best_recovery[0],
            "avg_focus": round(sum(s.focus_level for s in self._states) / len(self._states), 2),
            "avg_recovery": round(sum(s.recovery_effectiveness for s in self._states if s.recovery_activity) / max(1, len([s for s in self._states if s.recovery_activity])), 2),
            "bankruptcy_risk": bankruptcy_risk,
            "trend": round(trend, 2),
        }

    def get_recovery_protocol(self, depletion_type: str = "", urgency: str = "normal") -> Dict[str, Any]:
        """Get protocol."""
        protocols = {
            "mental_fatigue": {
                "immediate": ["Close eyes for 2 minutes. Breathe deeply.", "Step outside for 5 minutes. Fresh air.", "Drink a full glass of water."],
                "short": ["Take a 15-minute walk without your phone.", "Do a 10-minute meditation.", "Lie down with eyes closed for 10 minutes."],
                "long": ["Take a 30-minute nap. Set an alarm.", "Spend 30 minutes in nature. No phone.", "Do gentle yoga or stretching for 20 minutes."],
            },
            "digital_overload": {
                "immediate": ["Look at something 20 feet away for 20 seconds. Repeat 3 times.", "Stand up and stretch. Roll shoulders.", "Close all non-essential apps."],
                "short": ["Take a screen-free walk for 15 minutes.", "Read a paper book for 10 minutes.", "Do a body scan meditation."],
                "long": ["Implement a digital sunset. No screens after 7pm.", "Take a full day off from all non-essential digital tools.", "Replace one digital activity with an analog equivalent."],
            },
            "social_exhaustion": {
                "immediate": ["Find a quiet space. Sit alone for 2 minutes.", "Put on noise-canceling headphones.", "Text one person: 'Need some alone time, talk later.'"],
                "short": ["Take a solo walk. No interaction.", "Journal for 10 minutes. Process the social input.", "Listen to calming music with headphones."],
                "long": ["Block out one evening with zero social obligations.", "Spend a half-day in solitude. Book, nature, silence.", "Set boundaries: 'I can do X, but not Y today.'"],
            },
            "emotional_drain": {
                "immediate": ["Place hand on heart. Breathe slowly for 1 minute.", "Name one emotion out loud.", "Text someone you trust: 'Having a hard moment.'"],
                "short": ["Write a stream-of-consciousness journal for 5 minutes. No editing.", "Call a safe person. Let them listen.", "Listen to music that matches your mood."],
                "long": ["See a therapist or counselor.", "Spend time with a pet or in nature.", "Do something creative: draw, color, play music."],
            },
            "sensory_overload": {
                "immediate": ["Close eyes. Cover ears. Breathe for 2 minutes.", "Move to a quieter space.", "Remove one layer of sensory input."],
                "short": ["Sit in silence for 10 minutes.", "Take a warm bath or shower.", "Lie down in a dark, quiet room."],
                "long": ["Spend time in nature. Natural sensory input is restorative.", "Create a sensory-minimal environment at home.", "Practice silence for one full hour."],
            },
        }

        selected = protocols.get(depletion_type, protocols["mental_fatigue"])

        if urgency == "critical":
            protocol = selected["immediate"]
            urgency_note = "Critical attention depletion. Stop what you're doing. Recover now."
        elif urgency == "high":
            protocol = selected["short"]
            urgency_note = "High depletion. Take a break within the next 30 minutes."
        else:
            protocol = selected["long"]
            urgency_note = "Moderate depletion. Plan recovery into your schedule today."

        return {
            "depletion_type": depletion_type or "general",
            "urgency": urgency,
            "protocol": random.choice(protocol),
            "urgency_note": urgency_note,
            "principle": "Attention is your most valuable resource. You can't think clearly, create deeply, or connect genuinely without it. Protect it fiercely.",
        }

    def get_attention_score(self) -> int:
        """Calculate overall attention health (0-100)."""
        if not self._states:
            return 30

        # Average focus
        avg_focus = sum(s.focus_level for s in self._states) / len(self._states)

        # Recovery effectiveness
        with_recovery = [s for s in self._states if s.recovery_activity]
        if with_recovery:
            avg_recovery = sum(s.recovery_effectiveness for s in with_recovery) / len(with_recovery)
        else:
            avg_recovery = 0

        # Low drain from worst source
        by_source = defaultdict(lambda: {"focus_sum": 0.0, "count": 0})
        for s in self._states:
            by_source[s.source]["focus_sum"] += s.focus_level
            by_source[s.source]["count"] += 1
        if by_source:
            worst_source = min(by_source.items(), key=lambda x: x[1]["focus_sum"] / max(1, x[1]["count"]))
            worst_focus = worst_source[1]["focus_sum"] / max(1, worst_source[1]["count"])
        else:
            worst_focus = 0.5

        # Recent trend
        recent = list(self._states)[-14:]
        if recent:
            recent_focus = sum(s.focus_level for s in recent) / len(recent)
        else:
            recent_focus = 0

        # Bankruptcy penalty
        if len(recent) > 7:
            low_focus_days = sum(1 for s in recent if s.focus_level < 0.4)
            bankruptcy_penalty = min(20, low_focus_days * 2)
        else:
            bankruptcy_penalty = 0

        score = (avg_focus * 30) + (avg_recovery * 20) + (worst_focus * 15) + (recent_focus * 20) - bankruptcy_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._states:
            self._stats["avg_focus"] = round(sum(s.focus_level for s in self._states) / len(self._states), 2)
            
            with_recovery = [s for s in self._states if s.recovery_activity]
            if with_recovery:
                self._stats["avg_recovery"] = round(sum(s.recovery_effectiveness for s in with_recovery) / len(with_recovery), 2)

            by_source = defaultdict(lambda: {"focus": 0.0, "count": 0})
            for s in self._states:
                by_source[s.source]["focus"] += s.focus_level
                by_source[s.source]["count"] += 1
            if by_source:
                worst = min(by_source.items(), key=lambda x: x[1]["focus"] / max(1, x[1]["count"]))
                self._stats["primary_drain"] = worst[0]

            recent = [s for s in self._states if s.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
            if recent:
                avg_recent_focus = sum(s.focus_level for s in recent) / len(recent)
                low_focus_days = sum(1 for s in recent if s.focus_level < 0.4)
                self._stats["bankruptcy_risk"] = avg_recent_focus < 0.4 and low_focus_days > 3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.attention_recovery_specialist")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.attention_recovery_specialist")

    def _log_state(self, state: AttentionState):
        try:
            with open(ATTENTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": state.timestamp,
                    "focus": state.focus_level,
                    "type": state.attention_type,
                    "source": state.source,
                    "duration": state.duration_minutes,
                    "recovery": state.recovery_effectiveness,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.attention_recovery_specialist")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ars_instance: Optional[AttentionRecoverySpecialist] = None
_ars_lock = threading.Lock()


def get_attention_recovery_specialist() -> AttentionRecoverySpecialist:
    global _ars_instance
    with _ars_lock:
        if _ars_instance is None:
            _ars_instance = AttentionRecoverySpecialist()
        return _ars_instance
