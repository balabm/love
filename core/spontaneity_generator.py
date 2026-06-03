"""
LOVE Spontaneity Generator — Surprise Intelligence (Modern AI Pattern)

Most life is scripted and predictable. This generator:

1. SPONTANEITY TRACKING
   - Record spontaneous moments and their characteristics
   - Track spontaneity types (social, creative, physical, experiential, decision)
   - Log spontaneity outcomes and their effects

2. PATTERN ANALYSIS
   - Identify the user's spontaneity profile (planner, improviser, reactor, initiator)
   - Find spontaneity contexts that produce delight
   - Detect over-planning and rigidity accumulation

3. SPONTANEITY GENERATION
   - Suggest spontaneous actions matched to current state
   - Provide low-risk spontaneity exercises
   - Recommendation surprise and novelty practices

4. FLEXIBILITY CULTIVATION
   - Track the correlation between spontaneity and adaptability
   - Alert when life is becoming too scripted
   - Celebrate unplanned delights

Architecture:
- record_spontaneity(moment, type, risk, outcome): Log spontaneity
- get_spontaneity_stats(): Get spontaneity pattern analysis
- get_spontaneous_suggestion(rigidity, energy): Get suggestion
- get_spontaneity_score(): Calculate overall spontaneity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "spontaneity_generator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SPONTANEITY_LOG = DATA_DIR / "spontaneity.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SpontaneityEntry:
    """A tracked spontaneity entry."""
    entry_id: str = ""
    moment: str = ""
    spontaneity_type: str = ""  # social, creative, physical, experiential, decision
    risk_level: float = 0.5  # 0-1
    planning_abandoned: float = 0.0  # 0-1, how much planning was dropped
    delight: float = 0.5  # 0-1
    energy_change: float = 0.0  # -1 to 1
    would_repeat: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SpontaneityGenerator:
    """
    Intelligent spontaneity generator with rigidity detection and surprise cultivation.
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
            "avg_delight": 0.0,
            "avg_risk": 0.0,
            "rigidity_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_spontaneity(self, moment: str = "", spontaneity_type: str = "", risk_level: float = 0.5, planning_abandoned: float = 0.0, delight: float = 0.5, energy_change: float = 0.0, would_repeat: bool = False, notes: str = "") -> SpontaneityEntry:
        """Record a spontaneity entry."""
        entry_id = f"spon_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SpontaneityEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            spontaneity_type=spontaneity_type or "experiential",
            risk_level=risk_level,
            planning_abandoned=planning_abandoned,
            delight=delight,
            energy_change=energy_change,
            would_repeat=would_repeat,
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

    def get_spontaneity_stats(self) -> Dict[str, Any]:
        """Get spontaneity pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "delight_sum": 0.0, "risk_sum": 0.0, "energy_sum": 0.0, "repeat_count": 0})
        for e in self._entries:
            by_type[e.spontaneity_type]["count"] += 1
            by_type[e.spontaneity_type]["delight_sum"] += e.delight
            by_type[e.spontaneity_type]["risk_sum"] += e.risk_level
            by_type[e.spontaneity_type]["energy_sum"] += e.energy_change
            if e.would_repeat:
                by_type[e.spontaneity_type]["repeat_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_delight": round(data["delight_sum"] / count, 2),
                "avg_risk": round(data["risk_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
                "repeat_rate": round(data["repeat_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_delight"] + x[1]["avg_energy"]) if type_stats else ("", {})

        # Risk-delight analysis
        low_risk = [e for e in self._entries if e.risk_level <= 0.3]
        high_risk = [e for e in self._entries if e.risk_level > 0.7]
        if low_risk and high_risk:
            low_risk_delight = sum(e.delight for e in low_risk) / len(low_risk)
            high_risk_delight = sum(e.delight for e in high_risk) / len(high_risk)
            low_risk_energy = sum(e.energy_change for e in low_risk) / len(low_risk)
            high_risk_energy = sum(e.energy_change for e in high_risk) / len(high_risk)
        else:
            low_risk_delight = 0
            high_risk_delight = 0
            low_risk_energy = 0
            high_risk_energy = 0

        # Rigidity detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(self._entries) > 30:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
            if recent and older:
                recent_spontaneity = len(recent) / max(1, len(older) / 2)
                rigidity_risk = recent_spontaneity < 0.5
            else:
                rigidity_risk = False
        else:
            rigidity_risk = False

        # Repeat analysis
        repeat_entries = [e for e in self._entries if e.would_repeat]
        repeat_rate = len(repeat_entries) / len(self._entries)
        if repeat_entries:
            repeat_delight = sum(e.delight for e in repeat_entries) / len(repeat_entries)
        else:
            repeat_delight = 0

        # Planning abandoned analysis
        avg_planning_abandoned = sum(e.planning_abandoned for e in self._entries) / len(self._entries)

        # Recent trend
        if recent:
            recent_delight = sum(e.delight for e in recent) / len(recent)
            recent_risk = sum(e.risk_level for e in recent) / len(recent)
            recent_energy = sum(e.energy_change for e in recent) / len(recent)
        else:
            recent_delight = 0
            recent_risk = 0
            recent_energy = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_delight = sum(e.delight for e in older) / len(older)
            older_energy = sum(e.energy_change for e in older) / len(older)
            delight_trend = recent_delight - older_delight
            energy_trend = recent_energy - older_energy
        else:
            delight_trend = 0
            energy_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "risk_analysis": {
                "low_risk_delight": round(low_risk_delight, 2),
                "high_risk_delight": round(high_risk_delight, 2),
                "low_risk_energy": round(low_risk_energy, 2),
                "high_risk_energy": round(high_risk_energy, 2),
            },
            "rigidity_risk": rigidity_risk,
            "repeat_rate": round(repeat_rate, 2),
            "repeat_delight": round(repeat_delight, 2),
            "avg_planning_abandoned": round(avg_planning_abandoned, 2),
            "avg_delight": round(sum(e.delight for e in self._entries) / len(self._entries), 2),
            "avg_risk": round(sum(e.risk_level for e in self._entries) / len(self._entries), 2),
            "avg_energy_change": round(sum(e.energy_change for e in self._entries) / len(self._entries), 2),
            "delight_trend": round(delight_trend, 2),
            "energy_trend": round(energy_trend, 2),
            "recent_delight": round(recent_delight, 2),
            "recent_risk": round(recent_risk, 2),
        }

    def get_spontaneous_suggestion(self, rigidity: float = 0.5, energy: float = 0.5) -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = [
            "Take a different route home. Notice 3 new things.",
            "Text someone you haven't talked to in months. 'Thinking of you.'",
            "Order something at a restaurant you've never tried. Trust the universe.",
            "Go to a part of town you've never been. Walk for 20 minutes. No agenda.",
            "Wear something that doesn't 'match.' On purpose. See what happens.",
            "Do the opposite of your plan. If you planned to work, rest. If rest, create.",
            "Say yes to the next invitation you receive. Even if it's inconvenient.",
            "Start a conversation with a stranger. Compliment their shoes. Ask about their day.",
            "Change your environment. Work from a different room. A cafe. A park.",
            "Do something artistic with no skill required. Finger paint. Doodle. Collage.",
            "Make a decision by coin flip. Heads = do it. Tails = don't. Trust chance.",
            "Sing in public. Not loudly. Just hum. See how it feels.",
            "Buy something small and give it to someone. For no reason.",
            "Take a photo of something ordinary. Make it look extraordinary.",
            "Write a poem about your current situation. Badly. That's the point.",
        ]

        if rigidity > 0.8:
            rigidity_note = "High rigidity detected. Your life is a script. Rip out one page. Do something unplanned today."
        elif rigidity > 0.5:
            rigidity_note = "Moderate rigidity. You could use some surprise. Choose one spontaneous thing."
        else:
            rigidity_note = "Good flexibility. Keep the spontaneity alive. It's a superpower."

        if energy < 0.3:
            energy_note = "Low energy. Spontaneity doesn't have to be big. A small surprise is enough."
        elif energy < 0.6:
            energy_note = "Moderate energy. A medium spontaneity will refresh you."
        else:
            energy_note = "High energy. This is when you can handle bigger surprises. Go for it."

        return {
            "rigidity": rigidity,
            "energy": energy,
            "suggestion": random.choice(suggestions),
            "rigidity_note": rigidity_note,
            "energy_note": energy_note,
            "principle": "Spontaneity is not chaos. It's the deliberate introduction of novelty into a predictable life. It's how you stay flexible, discover new things, and remember that you're not a machine. The best memories are usually unplanned.",
        }

    def get_spontaneity_score(self) -> int:
        """Calculate overall spontaneity health (0-100)."""
        if not self._entries:
            return 30

        # Delight and energy
        avg_delight = sum(e.delight for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy_change for e in self._entries) / len(self._entries)

        # Risk calibration (not too high, not too low)
        avg_risk = sum(e.risk_level for e in self._entries) / len(self._entries)
        risk_score = 1 - abs(avg_risk - 0.4)

        # Repeat rate (would they do it again?)
        repeat_entries = [e for e in self._entries if e.would_repeat]
        repeat_rate = len(repeat_entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.spontaneity_type for e in self._entries))

        # Planning abandoned (some, but not all)
        avg_planning = sum(e.planning_abandoned for e in self._entries) / len(self._entries)
        planning_score = 1 - abs(avg_planning - 0.3)

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_delight = sum(e.delight for e in recent) / len(recent)
            recent_energy = sum(e.energy_change for e in recent) / len(recent)
            recent_risk = sum(e.risk_level for e in recent) / len(recent)
        else:
            recent_delight = 0
            recent_energy = 0
            recent_risk = 0

        # Rigidity penalty
        if len(self._entries) > 30:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
            if recent and older:
                recent_spontaneity = len(recent) / max(1, len(older) / 2)
                rigidity_penalty = 10 if recent_spontaneity < 0.5 else 0
            else:
                rigidity_penalty = 0
        else:
            rigidity_penalty = 0

        score = (avg_delight * 25) + (avg_energy * 15) + (risk_score * 10) + (repeat_rate * 15) + (unique_types * 2) + (planning_score * 10) + (recent_delight * 15) + (recent_energy * 10) + (recent_risk * 5) - rigidity_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_delight"] = round(sum(e.delight for e in self._entries) / len(self._entries), 2)
            self._stats["avg_risk"] = round(sum(e.risk_level for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if len(self._entries) > 30:
                older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
                if recent and older:
                    recent_spontaneity = len(recent) / max(1, len(older) / 2)
                    self._stats["rigidity_risk"] = recent_spontaneity < 0.5

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.spontaneity_generator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.spontaneity_generator")

    def _log_entry(self, entry: SpontaneityEntry):
        try:
            with open(SPONTANEITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "spontaneity_type": entry.spontaneity_type,
                    "risk_level": entry.risk_level,
                    "planning_abandoned": entry.planning_abandoned,
                    "delight": entry.delight,
                    "energy_change": entry.energy_change,
                    "would_repeat": entry.would_repeat,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.spontaneity_generator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sg_instance: Optional[SpontaneityGenerator] = None
_sg_lock = threading.Lock()


def get_spontaneity_generator() -> SpontaneityGenerator:
    global _sg_instance
    with _sg_lock:
        if _sg_instance is None:
            _sg_instance = SpontaneityGenerator()
        return _sg_instance
