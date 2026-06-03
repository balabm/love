"""
LOVE Recovery Optimizer — Restoration Intelligence (Modern AI Pattern)

Most people recover poorly, leading to chronic depletion. This optimizer:

1. RECOVERY TRACKING
   - Record recovery activities and their effectiveness
   - Track recovery types (sleep, movement, social, nature, creative, mental)
   - Log recovery gaps and their consequences

2. PATTERN ANALYSIS
   - Identify the user's recovery style (active, passive, social, solitary)
   - Find which recovery methods work best for which depletion types
   - Detect recovery debt accumulation

3. RECOVERY DESIGN
   - Suggest recovery activities matched to current depletion
   - Provide micro-recovery options for busy periods
   - Recommend recovery scheduling around work demands

4. OPTIMIZATION
   - Track the correlation between recovery quality and performance
   - Alert when recovery is insufficient for upcoming demands
   - Celebrate effective recovery practices

Architecture:
- record_recovery(activity, type, effectiveness, depletion): Log recovery
- get_recovery_stats(): Get recovery pattern analysis
- get_recovery_recommendation(depletion_type, time): Get recommendation
- get_recovery_score(): Calculate overall recovery health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "recovery_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RECOVERY_LOG = DATA_DIR / "recoveries.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RecoveryEntry:
    """A tracked recovery entry."""
    entry_id: str = ""
    activity: str = ""
    recovery_type: str = ""  # sleep, movement, social, nature, creative, mental, sensory, emotional
    effectiveness: float = 0.5  # 0-1
    depletion_type: str = ""  # mental, physical, emotional, social, creative
    duration_minutes: float = 0.0
    energy_before: float = 0.3  # 0-1
    energy_after: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RecoveryOptimizer:
    """
    Intelligent recovery optimizer with depletion-matched recommendation and debt tracking.
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
        self._entries: deque = deque(maxlen=200)
        self._stats = {
            "total_entries": 0,
            "avg_effectiveness": 0.0,
            "avg_energy_gain": 0.0,
            "best_activity": "",
            "recovery_debt": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_recovery(self, activity: str = "", recovery_type: str = "", effectiveness: float = 0.5, depletion_type: str = "", duration: float = 0, energy_before: float = 0.3, energy_after: float = 0.5, notes: str = "") -> RecoveryEntry:
        """Record a recovery entry."""
        entry_id = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RecoveryEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            recovery_type=recovery_type or "mental",
            effectiveness=effectiveness,
            depletion_type=depletion_type or "mental",
            duration_minutes=duration,
            energy_before=energy_before,
            energy_after=energy_after,
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

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Recovery type analysis
        by_type = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0, "energy_gain_sum": 0.0, "duration_sum": 0.0})
        for e in self._entries:
            by_type[e.recovery_type]["count"] += 1
            by_type[e.recovery_type]["effectiveness_sum"] += e.effectiveness
            by_type[e.recovery_type]["energy_gain_sum"] += (e.energy_after - e.energy_before)
            by_type[e.recovery_type]["duration_sum"] += e.duration_minutes

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                "avg_energy_gain": round(data["energy_gain_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
            }

        # Activity analysis
        by_activity = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0, "energy_gain_sum": 0.0})
        for e in self._entries:
            by_activity[e.activity]["count"] += 1
            by_activity[e.activity]["effectiveness_sum"] += e.effectiveness
            by_activity[e.activity]["energy_gain_sum"] += (e.energy_after - e.energy_before)

        activity_stats = {}
        for a, data in by_activity.items():
            count = data["count"]
            activity_stats[a] = {
                "count": count,
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                "avg_energy_gain": round(data["energy_gain_sum"] / count, 2),
            }

        best_activity = max(activity_stats.items(), key=lambda x: x[1]["avg_effectiveness"]) if activity_stats else ("", {})

        # Depletion matching
        by_depletion = defaultdict(lambda: {"types": defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})})
        for e in self._entries:
            by_depletion[e.depletion_type]["types"][e.recovery_type]["count"] += 1
            by_depletion[e.depletion_type]["types"][e.recovery_type]["effectiveness_sum"] += e.effectiveness

        depletion_matches = {}
        for dep, data in by_depletion.items():
            best_match = max(data["types"].items(), key=lambda x: x[1]["effectiveness_sum"] / max(1, x[1]["count"]))
            depletion_matches[dep] = best_match[0]

        # Recovery debt (low recovery relative to depletion)
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        if recent:
            avg_recent_gain = sum(e.energy_after - e.energy_before for e in recent) / len(recent)
            recovery_debt = avg_recent_gain < 0.2
        else:
            recovery_debt = False

        # Duration effectiveness
        short = [e for e in self._entries if e.duration_minutes <= 15]
        long_rec = [e for e in self._entries if e.duration_minutes > 60]
        if short and long_rec:
            short_effectiveness = sum(e.effectiveness for e in short) / len(short)
            long_effectiveness = sum(e.effectiveness for e in long_rec) / len(long_rec)
            duration_insight = f"Short recovery: {short_effectiveness:.2f} effectiveness. Long recovery: {long_effectiveness:.2f} effectiveness."
        else:
            duration_insight = "insufficient_data"

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "activity_stats": activity_stats,
            "best_activity": best_activity[0],
            "depletion_matches": depletion_matches,
            "avg_effectiveness": round(sum(e.effectiveness for e in self._entries) / len(self._entries), 2),
            "avg_energy_gain": round(sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries), 2),
            "recovery_debt": recovery_debt,
            "duration_insight": duration_insight,
        }

    def get_recovery_recommendation(self, depletion_type: str = "", time_available: float = 15, energy_level: float = 0.3) -> Dict[str, Any]:
        """Get recommendation."""
        recommendations = {
            "mental": {
                "micro": ["Close eyes for 2 minutes. Breathe.", "Stand up and look out a window.", "Drink a full glass of water slowly."],
                "short": ["Take a 10-minute walk without your phone.", "Do a 5-minute meditation.", "Listen to one song with full attention."],
                "medium": ["Take a 30-minute nap. Set an alarm.", "Do light stretching or yoga for 20 minutes.", "Read fiction for pleasure for 30 minutes."],
                "long": ["Spend 2 hours in nature without technology.", "Take a full day off from all mentally demanding tasks.", "Sleep 9 hours tonight. No alarm if possible."],
            },
            "physical": {
                "micro": ["Stretch arms overhead. Roll shoulders back.", "Stand up and walk to get water.", "Do 5 squats or push-ups."],
                "short": ["Take a 15-minute walk.", "Do a 10-minute body scan relaxation.", "Take a hot shower."],
                "medium": ["Get a massage or do self-massage with a ball.", "Take a warm bath with Epsom salts.", "Do gentle yoga for 45 minutes."],
                "long": ["Spend a full day doing only restorative movement.", "Sleep 10 hours. Prioritize physical recovery tonight.", "Take a float tank or sauna session."],
            },
            "emotional": {
                "micro": ["Place hand on heart. Breathe slowly for 1 minute.", "Text a friend: 'Thinking of you.'", "Name one emotion out loud."],
                "short": ["Journal for 10 minutes. No editing.", "Call someone who makes you feel safe.", "Listen to music that matches your mood."],
                "medium": ["Spend 30 minutes with a pet or in nature.", "Write a letter you don't send. Then burn or shred it.", "Do something creative: draw, color, play music."],
                "long": ["Spend a day with people who refill your cup.", "Take a retreat day. No obligations, only what feels good.", "See a therapist or counselor."],
            },
            "social": {
                "micro": ["Send one kind text. Expect nothing back.", "Smile at a stranger. Small connections matter.", "Step away from a group conversation for 2 minutes."],
                "short": ["Have a 15-minute one-on-one with someone you trust.", "Sit in a cafe and people-watch without interacting.", "Call a family member."],
                "medium": ["Have a meal with a close friend. No phones.", "Join a group activity purely for enjoyment.", "Have a deep conversation with someone."],
                "long": ["Plan a weekend with close friends.", "Attend a retreat or workshop with like-minded people.", "Take a trip to visit someone you love."],
            },
            "creative": {
                "micro": ["Doodle for 2 minutes. No judgment.", "Look at art or nature photos for 3 minutes.", "Hum or whistle a tune."],
                "short": ["Write a 6-word story.", "Take 10 photos of interesting textures.", "Cook something without a recipe."],
                "medium": ["Work on a creative hobby for 30 minutes.", "Visit a museum, gallery, or bookstore.", "Watch a film known for its visual beauty."],
                "long": ["Take a full day for creative play. No output pressure.", "Attend a workshop in a new creative medium.", "Start and finish one small creative project."],
            },
        }

        if time_available <= 5:
            duration_key = "micro"
        elif time_available <= 20:
            duration_key = "short"
        elif time_available <= 60:
            duration_key = "medium"
        else:
            duration_key = "long"

        rec_type = recommendations.get(depletion_type, recommendations["mental"])
        selected = rec_type.get(duration_key, rec_type["short"])
        recommendation = random.choice(selected)

        if energy_level < 0.2:
            urgency = "Critical. You're depleted. Any recovery is better than none. Even 2 minutes counts."
        elif energy_level < 0.4:
            urgency = "Moderate depletion. Match recovery to depletion type for maximum effect."
        else:
            urgency = "Preventive recovery. Build reserves before you need them."

        return {
            "depletion_type": depletion_type or "general",
            "time_available": time_available,
            "energy_level": energy_level,
            "recommendation": recommendation,
            "urgency": urgency,
            "principle": "Recovery is not a reward for work. It's a prerequisite for performance.",
        }

    def get_recovery_score(self) -> int:
        """Calculate overall recovery health (0-100)."""
        if not self._entries:
            return 30

        # Average effectiveness
        avg_effectiveness = sum(e.effectiveness for e in self._entries) / len(self._entries)

        # Average energy gain
        avg_gain = sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries)

        # Depletion type coverage
        depletion_types = set(e.depletion_type for e in self._entries)

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        if recent:
            recent_effectiveness = sum(e.effectiveness for e in recent) / len(recent)
            recent_gain = sum(e.energy_after - e.energy_before for e in recent) / len(recent)
        else:
            recent_effectiveness = 0
            recent_gain = 0

        # Recovery type variety
        recovery_types = set(e.recovery_type for e in self._entries)

        # Recovery debt check
        if recent:
            recovery_debt = sum(e.energy_after - e.energy_before for e in recent) / len(recent) < 0.2
        else:
            recovery_debt = False

        debt_penalty = 10 if recovery_debt else 0

        score = (avg_effectiveness * 25) + (avg_gain * 25) + (len(depletion_types) * 3) + (recent_effectiveness * 10) + (len(recovery_types) * 2) - debt_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_effectiveness"] = round(sum(e.effectiveness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_energy_gain"] = round(sum(e.energy_after - e.energy_before for e in self._entries) / len(self._entries), 2)

            by_activity = defaultdict(lambda: {"effectiveness": 0.0, "count": 0})
            for e in self._entries:
                by_activity[e.activity]["effectiveness"] += e.effectiveness
                by_activity[e.activity]["count"] += 1
            if by_activity:
                best = max(by_activity.items(), key=lambda x: x[1]["effectiveness"] / max(1, x[1]["count"]))
                self._stats["best_activity"] = best[0]

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
            if recent:
                avg_recent_gain = sum(e.energy_after - e.energy_before for e in recent) / len(recent)
                self._stats["recovery_debt"] = avg_recent_gain < 0.2

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.recovery_optimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.recovery_optimizer")

    def _log_entry(self, entry: RecoveryEntry):
        try:
            with open(RECOVERY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "recovery_type": entry.recovery_type,
                    "effectiveness": entry.effectiveness,
                    "depletion": entry.depletion_type,
                    "energy_before": entry.energy_before,
                    "energy_after": entry.energy_after,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.recovery_optimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ro_instance: Optional[RecoveryOptimizer] = None
_ro_lock = threading.Lock()


def get_recovery_optimizer() -> RecoveryOptimizer:
    global _ro_instance
    with _ro_lock:
        if _ro_instance is None:
            _ro_instance = RecoveryOptimizer()
        return _ro_instance
