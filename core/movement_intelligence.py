"""
LOVE Movement Intelligence — Kinetic Intelligence (Modern AI Pattern)

Most people move unconsciously. This intelligence:

1. MOVEMENT TRACKING
   - Record movement sessions and their characteristics
   - Track movement types (walking, stretching, dancing, strength, play, restorative)
   - Log joy, energy, ease, and integration of movement

2. PATTERN ANALYSIS
   - Identify the user's movement profile (sedentary, occasional, regular, joyful)
   - Find movement patterns that create vitality vs depletion
   - Detect chronic sedentary behavior and its costs

3. MOVEMENT BUILDING
   - Suggest practices for joyful, sustainable movement
   - Provide frameworks for movement as expression, not punishment
   - Recommend practices for integrating movement into daily life

4. KINETIC VITALITY CULTIVATION
   - Track the correlation between movement and energy
   - Alert when sedentary patterns are dominating
   - Celebrate moments of genuine, joyful movement

Architecture:
- record_movement(activity, type, joy, energy, ease, integration): Log movement
- get_movement_stats(): Get movement pattern analysis
- get_movement_suggestion(capacity, context): Get suggestion
- get_movement_score(): Calculate overall movement health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "movement_intelligence"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MOVEMENT_LOG = DATA_DIR / "movements.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MovementEntry:
    """A tracked movement session."""
    entry_id: str = ""
    activity: str = ""  # what was done
    movement_type: str = ""  # walking, stretching, dancing, strength, play, restorative
    joy: float = 0.0  # 0-1
    energy: float = 0.0  # 0-1
    ease: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1
    duration: float = 0.0  # minutes
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MovementIntelligence:
    """
    Intelligent movement intelligence with sedentary detection and kinetic vitality cultivation.
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
            "avg_joy": 0.0,
            "avg_energy": 0.0,
            "sedentary_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_movement(self, activity: str = "", movement_type: str = "", joy: float = 0.0, energy: float = 0.0, ease: float = 0.0, integration: float = 0.0, duration: float = 0.0, notes: str = "") -> MovementEntry:
        """Record a movement session."""
        entry_id = f"mov_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = MovementEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            movement_type=movement_type or "walking",
            joy=joy,
            energy=energy,
            ease=ease,
            integration=integration,
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

    def get_movement_stats(self) -> Dict[str, Any]:
        """Get movement pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "joy_sum": 0.0, "energy_sum": 0.0, "ease_sum": 0.0})
        for e in self._entries:
            by_type[e.movement_type]["count"] += 1
            by_type[e.movement_type]["joy_sum"] += e.joy
            by_type[e.movement_type]["energy_sum"] += e.energy
            by_type[e.movement_type]["ease_sum"] += e.ease

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
                "avg_ease": round(data["ease_sum"] / count, 2),
            }

        # Joy analysis
        high_joy = [e for e in self._entries if e.joy > 0.7]
        low_joy = [e for e in self._entries if e.joy < 0.4]
        if high_joy and low_joy:
            high_joy_eng = sum(e.energy for e in high_joy) / len(high_joy)
            low_joy_eng = sum(e.energy for e in low_joy) / len(low_joy)
            high_joy_int = sum(e.integration for e in high_joy) / len(high_joy)
            low_joy_int = sum(e.integration for e in low_joy) / len(low_joy)
        else:
            high_joy_eng = 0
            low_joy_eng = 0
            high_joy_int = 0
            low_joy_int = 0

        # Ease analysis
        high_ease = [e for e in self._entries if e.ease > 0.7]
        low_ease = [e for e in self._entries if e.ease < 0.4]
        if high_ease and low_ease:
            high_ease_joy = sum(e.joy for e in high_ease) / len(high_ease)
            low_ease_joy = sum(e.joy for e in low_ease) / len(low_ease)
        else:
            high_ease_joy = 0
            low_ease_joy = 0

        # Sedentary risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_eng = sum(e.energy for e in recent) / len(recent)
            sedentary_risk = recent_joy < 0.3 and recent_eng < 0.3
        else:
            sedentary_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "joy_impact": {
                "high_joy_energy": round(high_joy_eng, 2),
                "low_joy_energy": round(low_joy_eng, 2),
                "high_joy_integration": round(high_joy_int, 2),
                "low_joy_integration": round(low_joy_int, 2),
            },
            "ease_effect": {
                "high_ease_joy": round(high_ease_joy, 2),
                "low_ease_joy": round(low_ease_joy, 2),
            },
            "sedentary_risk": sedentary_risk,
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
            "avg_energy": round(sum(e.energy for e in self._entries) / len(self._entries), 2),
        }

    def get_movement_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get movement suggestion."""
        suggestions = [
            "Movement is not exercise. Exercise is a subset of movement. Movement is what bodies do. Walk. Dance. Stretch. Play. Climb. Swim. Move because it feels good. Not because you should.",
            "The best movement is the movement you enjoy. If you hate running, don't run. If you love dancing, dance. If you love walking, walk. Joy is the best motivator. And the best indicator of sustainability.",
            "Sedentary behavior is the new smoking. Not because sitting is bad. Because not moving is bad. Your body is designed for movement. Not for chairs. Not for screens. For movement.",
            "Walk more. Not for fitness. For thinking. For feeling. For being. The best ideas come on walks. The best feelings move on walks. Walk.",
            "Stretch when you wake up. Not because a guru said so. Because your body has been still for hours. It needs to unfold. To lengthen. To remember what it feels like to be awake.",
            "Dance alone. In your room. To music you love. No one is watching. And even if they were, who cares? Dance is joy made visible. And your body needs joy.",
            "Notice how movement changes your mind. The fog lifts. The mood shifts. The energy returns. This is not placebo. It's physiology. Movement creates neurotransmitters. Use them.",
            "Play is movement. Chase a ball. Throw a frisbee. Climb a tree. Play is not childish. It's childlike. And childlike is what your body remembers. And what it needs.",
            "Restorative movement is still movement. Gentle yoga. Slow walking. Stretching. These are not less than intense exercise. They're different. And they're necessary. Especially when you're stressed.",
            "Your body is not a machine to be optimized. It's an animal to be lived. Animals move. They run. They stretch. They play. They rest. Be an animal. Not a machine."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One walk. One stretch. One dance move. One moment of movement. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A walk around the block. A stretch break. A dance to one song. Medium movement."
        else:
            capacity_note = "Good capacity. Deep kinetic work. A systematic practice of joyful, sustainable movement. You have the strength to be truly alive in your body."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Movement is not a chore. It's a birthright. Your body is designed to move. To walk. To run. To dance. To stretch. To play. And yet modern life has made movement optional. We sit. We stand still. We stare at screens. And we wonder why we feel stiff. Why we feel low. Why we feel disconnected from our bodies. The work of movement intelligence is about reconnecting with the joy of movement. About finding movement that feels good, not just movement that looks good. About understanding that the body is not a machine to be optimized but an animal to be lived. And about creating a life where movement is woven into the fabric of the day, not squeezed into a gym session. Because the person who moves joyfully moves often. And the person who moves often is alive."
        }

    def get_movement_score(self) -> int:
        """Calculate overall movement health (0-100)."""
        if not self._entries:
            return 25

        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_eng = sum(e.energy for e in self._entries) / len(self._entries)
        avg_ease = sum(e.ease for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_dur = sum(e.duration for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_eng = sum(e.energy for e in recent) / len(recent)
        else:
            recent_joy = 0
            recent_eng = 0

        # Sedentary penalty
        sed_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            recent_eng_30 = sum(e.energy for e in last_30) / len(last_30)
            if recent_joy_30 < 0.3 and recent_eng_30 < 0.3:
                sed_penalty = 15

        # Type variety
        unique_types = len(set(e.movement_type for e in self._entries))

        score = (avg_joy * 25) + (avg_eng * 20) + (avg_ease * 15) + (avg_int * 15) + (recent_joy * 5) + (recent_eng * 5) + (unique_types * 2) + min(5, avg_dur / 10) - sed_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)
            self._stats["avg_energy"] = round(sum(e.energy for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_joy = sum(e.joy for e in recent) / len(recent)
                recent_eng = sum(e.energy for e in recent) / len(recent)
                self._stats["sedentary_risk"] = recent_joy < 0.3 and recent_eng < 0.3
            else:
                self._stats["sedentary_risk"] = False

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

    def _log_entry(self, entry: MovementEntry):
        try:
            with open(MOVEMENT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "movement_type": entry.movement_type,
                    "joy": entry.joy,
                    "energy": entry.energy,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mi_instance: Optional[MovementIntelligence] = None
_mi_lock = threading.Lock()


def get_movement_intelligence() -> MovementIntelligence:
    global _mi_instance
    with _mi_lock:
        if _mi_instance is None:
            _mi_instance = MovementIntelligence()
        return _mi_instance
