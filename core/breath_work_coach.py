"""
LOVE Breath Work Coach — Respiratory Intelligence (Modern AI Pattern)

Most people breathe unconsciously. This coach:

1. BREATH TRACKING
   - Record breath work sessions and their characteristics
   - Track breath types (deep, box, 4_7_8, wim_hof, coherent, diaphragmatic)
   - Log calm, energy, clarity, and practice quality

2. PATTERN ANALYSIS
   - Identify the user's breath profile (shallow, occasional, practiced, masterful)
   - Find breath patterns that create calm vs agitation
   - Detect chronic shallow breathing and its costs

3. BREATH BUILDING
   - Suggest practices for conscious breathing
   - Provide frameworks for breath-based regulation
   - Recommend practices for breath as anchor

4. RESPIRATORY WISDOM CULTIVATION
   - Track the correlation between breath work and state regulation
   - Alert when shallow breathing is dominating
   - Celebrate moments of genuine breath mastery

Architecture:
- record_breath(technique, type, calm, energy, clarity, practice): Log breath
- get_breath_stats(): Get breath pattern analysis
- get_breath_suggestion(capacity, context): Get suggestion
- get_breath_score(): Calculate overall breath health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "breath_work_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BREATH_LOG = DATA_DIR / "breaths.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BreathEntry:
    """A tracked breath work session."""
    entry_id: str = ""
    technique: str = ""  # what was practiced
    breath_type: str = ""  # deep, box, 4_7_8, wim_hof, coherent, diaphragmatic
    calm: float = 0.0  # 0-1
    energy: float = 0.0  # 0-1
    clarity: float = 0.0  # 0-1
    practice: float = 0.0  # 0-1 quality of practice
    duration: float = 0.0  # minutes
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BreathWorkCoach:
    """
    Intelligent breath work coach with shallow breathing detection and respiratory wisdom cultivation.
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
            "avg_calm": 0.0,
            "avg_clarity": 0.0,
            "shallow_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_breath(self, technique: str = "", breath_type: str = "", calm: float = 0.0, energy: float = 0.0, clarity: float = 0.0, practice: float = 0.0, duration: float = 0.0, notes: str = "") -> BreathEntry:
        """Record a breath work session."""
        entry_id = f"brth_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BreathEntry(
            entry_id=entry_id,
            technique=technique or "unspecified",
            breath_type=breath_type or "deep",
            calm=calm,
            energy=energy,
            clarity=clarity,
            practice=practice,
            duration=duration,
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

    def get_breath_stats(self) -> Dict[str, Any]:
        """Get breath pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "calm_sum": 0.0, "energy_sum": 0.0, "clarity_sum": 0.0})
        for e in self._entries:
            by_type[e.breath_type]["count"] += 1
            by_type[e.breath_type]["calm_sum"] += e.calm
            by_type[e.breath_type]["energy_sum"] += e.energy
            by_type[e.breath_type]["clarity_sum"] += e.clarity

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_calm": round(data["calm_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
                "avg_clarity": round(data["clarity_sum"] / count, 2),
            }

        # Calm analysis
        high_calm = [e for e in self._entries if e.calm > 0.7]
        low_calm = [e for e in self._entries if e.calm < 0.4]
        if high_calm and low_calm:
            high_calm_prac = sum(e.practice for e in high_calm) / len(high_calm)
            low_calm_prac = sum(e.practice for e in low_calm) / len(low_calm)
            high_calm_clr = sum(e.clarity for e in high_calm) / len(high_calm)
            low_calm_clr = sum(e.clarity for e in low_calm) / len(low_calm)
        else:
            high_calm_prac = 0
            low_calm_prac = 0
            high_calm_clr = 0
            low_calm_clr = 0

        # Practice analysis
        high_prac = [e for e in self._entries if e.practice > 0.7]
        low_prac = [e for e in self._entries if e.practice < 0.4]
        if high_prac and low_prac:
            high_prac_calm = sum(e.calm for e in high_prac) / len(high_prac)
            low_prac_calm = sum(e.calm for e in low_prac) / len(low_prac)
        else:
            high_prac_calm = 0
            low_prac_calm = 0

        # Shallow risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_calm = sum(e.calm for e in recent) / len(recent)
            recent_prac = sum(e.practice for e in recent) / len(recent)
            shallow_risk = recent_calm < 0.3 and recent_prac < 0.3
        else:
            shallow_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "calm_impact": {
                "high_calm_practice": round(high_calm_prac, 2),
                "low_calm_practice": round(low_calm_prac, 2),
                "high_calm_clarity": round(high_calm_clr, 2),
                "low_calm_clarity": round(low_calm_clr, 2),
            },
            "practice_effect": {
                "high_practice_calm": round(high_prac_calm, 2),
                "low_practice_calm": round(low_prac_calm, 2),
            },
            "shallow_risk": shallow_risk,
            "avg_calm": round(sum(e.calm for e in self._entries) / len(self._entries), 2),
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
        }

    def get_breath_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get breath suggestion."""
        suggestions = [
            "Your breath is the only autonomic function you can consciously control. That's not an accident. It's a bridge between your conscious and unconscious mind. Use it.",
            "Box breathing: inhale four counts. Hold four counts. Exhale four counts. Hold four counts. Do this for five minutes. It will change your state. Not because it's magic. Because it's physiology.",
            "When you're anxious, your breath is shallow. When you're calm, your breath is deep. But the causality works both ways. Breathe deeply. Become calm. The body leads the mind.",
            "Notice your breath right now. Don't change it. Just notice. Is it shallow? Deep? Fast? Slow? Held? Your breath is a real-time report on your nervous system. Read it.",
            "The 4-7-8 breath: inhale for 4, hold for 7, exhale for 8. Do this four times. It's like a tranquilizer for your nervous system. Fast. Free. Available anywhere.",
            "Breath is the anchor. When your mind wanders, come back to the breath. Not as a meditation technique. As a life technique. The breath is always here. Always now. Always available.",
            "Most people chest-breathe. That's shallow. That's stress breathing. Learn to belly-breathe. Put your hand on your belly. Feel it rise on the inhale. Fall on the exhale. That's diaphragmatic breathing. That's calm breathing.",
            "Your breath connects you to time. You can't breathe in the past. You can't breathe in the future. Every breath is now. Use it as an anchor to the present moment.",
            "When you're overwhelmed, exhale longer than you inhale. This activates the parasympathetic nervous system. The relaxation response. One long exhale is a reset button.",
            "Breath work is not woo-woo. It's neuroscience. Controlled breathing changes heart rate variability. Changes vagal tone. Changes brain waves. It's the most powerful free tool you have."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Three deep breaths. One conscious exhale. One moment of noticing. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A five-minute breath practice. A box breathing session. A diaphragmatic check. Medium coaching."
        else:
            capacity_note = "Good capacity. Deep breath work. A systematic practice of conscious breathing for state regulation. You have the strength to breathe with mastery."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Breath is life. Not metaphorically. Literally. And yet most people breathe unconsciously. Shallowly. Rapidly. As if they're always running from something. Because they are. From their thoughts. From their feelings. From their bodies. And the breath reflects this. Shallow breathing creates anxiety. Anxiety creates shallow breathing. It's a vicious cycle. But it can be broken. Conscious breathing is the key. Because the breath is the bridge between the autonomic and the voluntary nervous systems. You can't directly control your heart rate. But you can control your breathing. And your breathing controls your heart rate. That's the power of breath work. It's not mystical. It's physiological. And it's available to anyone who remembers to use it."
        }

    def get_breath_score(self) -> int:
        """Calculate overall breath health (0-100)."""
        if not self._entries:
            return 25

        avg_calm = sum(e.calm for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy for e in self._entries) / len(self._entries)
        avg_clr = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_prac = sum(e.practice for e in self._entries) / len(self._entries)
        avg_dur = sum(e.duration for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_calm = sum(e.calm for e in recent) / len(recent)
            recent_prac = sum(e.practice for e in recent) / len(recent)
        else:
            recent_calm = 0
            recent_prac = 0

        # Shallow penalty
        shallow_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_calm_30 = sum(e.calm for e in last_30) / len(last_30)
            recent_prac_30 = sum(e.practice for e in last_30) / len(last_30)
            if recent_calm_30 < 0.3 and recent_prac_30 < 0.3:
                shallow_penalty = 15

        # Type variety
        unique_types = len(set(e.breath_type for e in self._entries))

        score = (avg_calm * 25) + (avg_energy * 15) + (avg_clr * 15) + (avg_prac * 20) + (recent_calm * 5) + (recent_prac * 5) + (unique_types * 2) + min(5, avg_dur / 10) - shallow_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_calm"] = round(sum(e.calm for e in self._entries) / len(self._entries), 2)
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_calm = sum(e.calm for e in recent) / len(recent)
                recent_prac = sum(e.practice for e in recent) / len(recent)
                self._stats["shallow_risk"] = recent_calm < 0.3 and recent_prac < 0.3
            else:
                self._stats["shallow_risk"] = False

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

    def _log_entry(self, entry: BreathEntry):
        try:
            with open(BREATH_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "technique": entry.technique,
                    "breath_type": entry.breath_type,
                    "calm": entry.calm,
                    "clarity": entry.clarity,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_bwc_instance: Optional[BreathWorkCoach] = None
_bwc_lock = threading.Lock()


def get_breath_work_coach() -> BreathWorkCoach:
    global _bwc_instance
    with _bwc_lock:
        if _bwc_instance is None:
            _bwc_instance = BreathWorkCoach()
        return _bwc_instance
