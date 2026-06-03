"""
LOVE Rhythmic Living Coach — Temporal Intelligence (Modern AI Pattern)

Most people fight time. This coach:

1. RHYTHM TRACKING
   - Record rhythm moments and their characteristics
   - Track rhythm types (circadian, ultradian, weekly, seasonal, project, social)
   - Log alignment, energy, sustainability, and flow of rhythms

2. PATTERN ANALYSIS
   - Identify the user's rhythm profile (chaotic, rigid, developing, flowing)
   - Find rhythm patterns that create harmony vs friction
   - Detect chronic misalignment and its costs

3. RHYTHM BUILDING
   - Suggest practices for aligning with natural rhythms
   - Provide frameworks for personal tempo discovery
   - Recommend practices for rhythm-aware scheduling

4. TEMPORAL HARMONY CULTIVATION
   - Track the correlation between rhythm alignment and wellbeing
   - Alert when fighting natural rhythms is becoming the default
   - Celebrate moments of genuine temporal flow

Architecture:
- record_rhythm(period, type, alignment, energy, sustainability, flow): Log rhythm
- get_rhythm_stats(): Get rhythm pattern analysis
- get_rhythm_suggestion(capacity, context): Get suggestion
- get_rhythm_score(): Calculate overall rhythm health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "rhythmic_living_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RHYTHM_LOG = DATA_DIR / "rhythms.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RhythmEntry:
    """A tracked rhythm moment."""
    entry_id: str = ""
    period: str = ""  # what period was tracked
    rhythm_type: str = ""  # circadian, ultradian, weekly, seasonal, project, social
    alignment: float = 0.0  # 0-1 with natural rhythm
    energy: float = 0.0  # 0-1
    sustainability: float = 0.0  # 0-1
    flow: float = 0.0  # 0-1
    rest: float = 0.0  # 0-1 did you rest appropriately?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RhythmicLivingCoach:
    """
    Intelligent rhythmic living coach with misalignment detection and temporal harmony cultivation.
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
            "avg_alignment": 0.0,
            "avg_flow": 0.0,
            "misalignment_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_rhythm(self, period: str = "", rhythm_type: str = "", alignment: float = 0.0, energy: float = 0.0, sustainability: float = 0.0, flow: float = 0.0, rest: float = 0.0, notes: str = "") -> RhythmEntry:
        """Record a rhythm moment."""
        entry_id = f"rhy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RhythmEntry(
            entry_id=entry_id,
            period=period or "unspecified",
            rhythm_type=rhythm_type or "circadian",
            alignment=alignment,
            energy=energy,
            sustainability=sustainability,
            flow=flow,
            rest=rest,
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

    def get_rhythm_stats(self) -> Dict[str, Any]:
        """Get rhythm pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "align_sum": 0.0, "energy_sum": 0.0, "flow_sum": 0.0})
        for e in self._entries:
            by_type[e.rhythm_type]["count"] += 1
            by_type[e.rhythm_type]["align_sum"] += e.alignment
            by_type[e.rhythm_type]["energy_sum"] += e.energy
            by_type[e.rhythm_type]["flow_sum"] += e.flow

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_alignment": round(data["align_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
                "avg_flow": round(data["flow_sum"] / count, 2),
            }

        # Alignment analysis
        high_align = [e for e in self._entries if e.alignment > 0.7]
        low_align = [e for e in self._entries if e.alignment < 0.4]
        if high_align and low_align:
            high_align_en = sum(e.energy for e in high_align) / len(high_align)
            low_align_en = sum(e.energy for e in low_align) / len(low_align)
            high_align_flow = sum(e.flow for e in high_align) / len(high_align)
            low_align_flow = sum(e.flow for e in low_align) / len(low_align)
        else:
            high_align_en = 0
            low_align_en = 0
            high_align_flow = 0
            low_align_flow = 0

        # Rest analysis
        high_rest = [e for e in self._entries if e.rest > 0.7]
        low_rest = [e for e in self._entries if e.rest < 0.4]
        if high_rest and low_rest:
            high_rest_sus = sum(e.sustainability for e in high_rest) / len(high_rest)
            low_rest_sus = sum(e.sustainability for e in low_rest) / len(low_rest)
        else:
            high_rest_sus = 0
            low_rest_sus = 0

        # Misalignment risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_align = sum(e.alignment for e in recent) / len(recent)
            recent_flow = sum(e.flow for e in recent) / len(recent)
            misalignment_risk = recent_align < 0.3 and recent_flow < 0.3
        else:
            misalignment_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "alignment_impact": {
                "high_alignment_energy": round(high_align_en, 2),
                "low_alignment_energy": round(low_align_en, 2),
                "high_alignment_flow": round(high_align_flow, 2),
                "low_alignment_flow": round(low_align_flow, 2),
            },
            "rest_effect": {
                "high_rest_sustainability": round(high_rest_sus, 2),
                "low_rest_sustainability": round(low_rest_sus, 2),
            },
            "misalignment_risk": misalignment_risk,
            "avg_alignment": round(sum(e.alignment for e in self._entries) / len(self._entries), 2),
            "avg_flow": round(sum(e.flow for e in self._entries) / len(self._entries), 2),
        }

    def get_rhythm_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get rhythm suggestion."""
        suggestions = [
            "You have rhythms. Everyone does. Circadian. Ultradian. Weekly. Seasonal. The question is whether you align with them or fight them. Most people fight them. And wonder why they're tired.",
            "Your energy is not constant. It ebbs and flows. The person who ignores this and tries to work at the same pace all day is fighting biology. Work with your rhythms. Not against them.",
            "Track your energy for a week. When do you peak? When do you crash? When do you focus best? When do you need rest? This is your rhythm. Once you know it, you can use it.",
            "The afternoon crash is real. Don't fight it. Rest. Nap. Walk. It's not laziness. It's biology. The person who pushes through the crash produces worse work. Rest is strategic.",
            "Align your hardest work with your peak energy. Don't schedule meetings during your creative hours. Don't do email when you're fresh. Match the task to the rhythm.",
            "Your week has a rhythm too. Some days are for deep work. Some for admin. Some for rest. Some for connection. Don't try to do everything every day. Assign days their purpose.",
            "Seasons matter. Winter is for rest. Spring for planting. Summer for growth. Fall for harvest. Your year has a rhythm. Respect it. Don't expect summer energy in winter.",
            "Rest is part of the rhythm. Not the absence of work. The other side of work. The exhale after the inhale. Without rest, the rhythm breaks. And so do you.",
            "Notice when you're in flow. That's your rhythm speaking. When time disappears. When work feels effortless. That's your natural tempo. Find it. Protect it. Repeat it.",
            "The person who lives rhythmically is not rigid. They're fluid. They move with time instead of against it. They surf the waves instead of fighting the tide. That's the practice."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One energy check. One rest taken. One rhythm noticed. One small alignment. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A weekly rhythm map. A peak-time protected. A rest ritual created. Medium coaching."
        else:
            capacity_note = "Good capacity. Deep temporal work. A systematic practice of living in harmony with natural rhythms. You have the strength to flow with time."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Rhythmic living is about understanding that you are not a machine. You don't run at constant speed. You have peaks and valleys. Ebb and flow. Inhale and exhale. The modern world pretends this isn't true. It demands constant output. Consistent performance. But biology doesn't work that way. You have circadian rhythms. Ultradian rhythms. Weekly rhythms. Seasonal rhythms. And when you fight them, you lose. The work of rhythmic living coaching is about discovering your personal tempo. About aligning your schedule with your energy. About working when you're fresh and resting when you're tired. About understanding that rest is not the opposite of productivity. It's part of it. And about creating a life that flows rather than one that grinds."
        }

    def get_rhythm_score(self) -> int:
        """Calculate overall rhythm health (0-100)."""
        if not self._entries:
            return 25

        avg_align = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_en = sum(e.energy for e in self._entries) / len(self._entries)
        avg_sus = sum(e.sustainability for e in self._entries) / len(self._entries)
        avg_flow = sum(e.flow for e in self._entries) / len(self._entries)
        avg_rest = sum(e.rest for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_align = sum(e.alignment for e in recent) / len(recent)
            recent_flow = sum(e.flow for e in recent) / len(recent)
        else:
            recent_align = 0
            recent_flow = 0

        # Misalignment penalty
        mis_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_align_30 = sum(e.alignment for e in last_30) / len(last_30)
            recent_flow_30 = sum(e.flow for e in last_30) / len(last_30)
            if recent_align_30 < 0.3 and recent_flow_30 < 0.3:
                mis_penalty = 15

        # Type variety
        unique_types = len(set(e.rhythm_type for e in self._entries))

        score = (avg_align * 25) + (avg_en * 15) + (avg_sus * 15) + (avg_flow * 15) + (avg_rest * 10) + (recent_align * 5) + (recent_flow * 5) + (unique_types * 2) - mis_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_alignment"] = round(sum(e.alignment for e in self._entries) / len(self._entries), 2)
            self._stats["avg_flow"] = round(sum(e.flow for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_align = sum(e.alignment for e in recent) / len(recent)
                recent_flow = sum(e.flow for e in recent) / len(recent)
                self._stats["misalignment_risk"] = recent_align < 0.3 and recent_flow < 0.3
            else:
                self._stats["misalignment_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.rhythmic_living_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.rhythmic_living_coach")

    def _log_entry(self, entry: RhythmEntry):
        try:
            with open(RHYTHM_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "period": entry.period,
                    "rhythm_type": entry.rhythm_type,
                    "alignment": entry.alignment,
                    "flow": entry.flow,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.rhythmic_living_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rlc_instance: Optional[RhythmicLivingCoach] = None
_rlc_lock = threading.Lock()


def get_rhythmic_living_coach() -> RhythmicLivingCoach:
    global _rlc_instance
    with _rlc_lock:
        if _rlc_instance is None:
            _rlc_instance = RhythmicLivingCoach()
        return _rlc_instance
