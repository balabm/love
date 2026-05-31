"""
LOVE Joy Cultivator — Delight Intelligence (Modern AI Pattern)

Most joy is accidental, not cultivated. This cultivator:

1. JOY TRACKING
   - Record joy moments and their characteristics
   - Track joy types (sensory, relational, achievement, aesthetic, playful)
   - Log joy triggers and their frequency

2. PATTERN ANALYSIS
   - Identify the user's joy profile (seeker, receiver, creator, sharer)
   - Find joy accelerators (what reliably produces joy)
   - Detect joy droughts and their causes

3. JOY CULTIVATION
   - Suggest joy practices matched to current state
   - Provide savoring exercises
   - Recommendation joy-amplification habits

4. DELIGHT AMPLIFICATION
   - Track the correlation between joy and resilience
   - Alert when joy is being sacrificed for productivity
   - Celebrate moments of pure delight

Architecture:
- record_joy(moment, joy_type, intensity, trigger): Log joy
- get_joy_stats(): Get joy pattern analysis
- get_joy_practice(drought, capacity): Get practice
- get_joy_score(): Calculate overall joy health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "joy_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

JOY_LOG = DATA_DIR / "joy.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class JoyEntry:
    """A tracked joy entry."""
    entry_id: str = ""
    moment: str = ""
    joy_type: str = ""  # sensory, relational, achievement, aesthetic, playful, surprise
    intensity: float = 0.5  # 0-1
    trigger: str = ""  # what sparked it
    duration_minutes: float = 0.0
    sharing: bool = False  # whether they shared it
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class JoyCultivator:
    """
    Intelligent joy cultivator with drought detection and savoring practices.
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
            "avg_intensity": 0.0,
            "avg_duration": 0.0,
            "dominant_type": "",
            "drought_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_joy(self, moment: str = "", joy_type: str = "", intensity: float = 0.5, trigger: str = "", duration: float = 0, sharing: bool = False, notes: str = "") -> JoyEntry:
        """Record a joy entry."""
        entry_id = f"joy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = JoyEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            joy_type=joy_type or "sensory",
            intensity=intensity,
            trigger=trigger,
            duration_minutes=duration,
            sharing=sharing,
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

    def get_joy_stats(self) -> Dict[str, Any]:
        """Get joy pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "duration_sum": 0.0, "sharing_count": 0})
        for e in self._entries:
            by_type[e.joy_type]["count"] += 1
            by_type[e.joy_type]["intensity_sum"] += e.intensity
            by_type[e.joy_type]["duration_sum"] += e.duration_minutes
            if e.sharing:
                by_type[e.joy_type]["sharing_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
                "sharing_rate": round(data["sharing_count"] / count, 2),
            }

        dominant_type = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for e in self._entries:
            if e.trigger:
                by_trigger[e.trigger]["count"] += 1
                by_trigger[e.trigger]["intensity_sum"] += e.intensity

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            if count >= 2:
                trigger_stats[tr] = {
                    "count": count,
                    "avg_intensity": round(data["intensity_sum"] / count, 2),
                }

        best_trigger = max(trigger_stats.items(), key=lambda x: x[1]["avg_intensity"]) if trigger_stats else ("", {})

        # Drought detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if len(self._entries) > 14:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if recent and older:
                recent_intensity = sum(e.intensity for e in recent) / len(recent)
                older_intensity = sum(e.intensity for e in older) / len(older)
                drought_risk = recent_intensity < older_intensity * 0.7
            else:
                drought_risk = False
        else:
            drought_risk = False

        # Sharing analysis
        shared = [e for e in self._entries if e.sharing]
        sharing_rate = len(shared) / len(self._entries)
        if shared:
            shared_intensity = sum(e.intensity for e in shared) / len(shared)
        else:
            shared_intensity = 0

        # Duration analysis
        avg_duration = sum(e.duration_minutes for e in self._entries) / len(self._entries)

        # Recent trend
        if recent:
            recent_intensity = sum(e.intensity for e in recent) / len(recent)
            recent_duration = sum(e.duration_minutes for e in recent) / len(recent)
        else:
            recent_intensity = 0
            recent_duration = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_intensity = sum(e.intensity for e in older) / len(older)
            older_duration = sum(e.duration_minutes for e in older) / len(older)
            intensity_trend = recent_intensity - older_intensity
            duration_trend = recent_duration - older_duration
        else:
            intensity_trend = 0
            duration_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "dominant_type": dominant_type[0],
            "trigger_stats": trigger_stats,
            "best_trigger": best_trigger[0],
            "drought_risk": drought_risk,
            "sharing_rate": round(sharing_rate, 2),
            "shared_intensity": round(shared_intensity, 2),
            "avg_intensity": round(sum(e.intensity for e in self._entries) / len(self._entries), 2),
            "avg_duration": round(avg_duration, 1),
            "intensity_trend": round(intensity_trend, 2),
            "duration_trend": round(duration_trend, 2),
            "recent_intensity": round(recent_intensity, 2),
            "recent_duration": round(recent_duration, 1),
        }

    def get_joy_practice(self, drought: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "sensory": [
                "Eat one bite of food with full attention. Taste every flavor. Texture. Temperature.",
                "Step outside. Feel the air on your skin. Notice one smell. One sound. One sight.",
                "Take a warm shower. Feel every drop. This is not luxury. It's being alive.",
            ],
            "relational": [
                "Call someone you love. Not for a reason. Just to hear their voice.",
                "Hug someone for 6 seconds. That's the minimum for oxytocin release.",
                "Tell someone one specific thing you appreciate about them. Be exact.",
            ],
            "achievement": [
                "Acknowledge one thing you did today. Not the big thing. Any thing. You showed up.",
                "Write down 3 wins from this week. Small wins count.",
                "Celebrate progress, not just outcomes. You're further than you were.",
            ],
            "aesthetic": [
                "Look at one beautiful thing for 60 seconds. Art, nature, architecture, light.",
                "Listen to one song you love. Full volume. Let it move through you.",
                "Arrange something pleasingly. A desk, a plate, a shelf. Order is joy.",
            ],
            "playful": [
                "Do one thing with no purpose other than fun. 10 minutes. That's enough.",
                "Play with a pet or child. They're joy experts. Learn from them.",
                "Find the game in a task. How fast? How well? How creatively?",
            ],
            "surprise": [
                "Break your routine. Take a different route. Order something new. Surprise yourself.",
                "Learn one random fact about something you know nothing about.",
                "Talk to a stranger. Not deep. Just human connection. A comment about the weather.",
            ],
        }

        selected = practices.get(drought, practices["sensory"])

        if capacity < 0.3:
            capacity_note = "Low capacity. Choose the smallest joy. One breath of pleasure. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A medium joy will restore you. Don't skip it."
        else:
            capacity_note = "Good capacity. This is when you can seek bigger joys. Stretch your joy range."

        return {
            "drought": drought or "general",
            "capacity": capacity,
            "practice": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Joy is not the absence of suffering. It's the presence of delight in the midst of everything else. It's a muscle. The more you notice joy, the more joy you find. The world is full of beauty. Your job is to pay attention.",
        }

    def get_joy_score(self) -> int:
        """Calculate overall joy health (0-100)."""
        if not self._entries:
            return 30

        # Intensity and duration
        avg_intensity = sum(e.intensity for e in self._entries) / len(self._entries)
        avg_duration = sum(e.duration_minutes for e in self._entries) / len(self._entries)

        # Sharing
        shared = [e for e in self._entries if e.sharing]
        sharing_rate = len(shared) / len(self._entries)

        # Type variety
        unique_types = len(set(e.joy_type for e in self._entries))

        # Trigger variety
        unique_triggers = len(set(e.trigger for e in self._entries if e.trigger))

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_intensity = sum(e.intensity for e in recent) / len(recent)
            recent_duration = sum(e.duration_minutes for e in recent) / len(recent)
        else:
            recent_intensity = 0
            recent_duration = 0

        # Drought penalty
        if len(self._entries) > 14:
            older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if recent and older:
                recent_intensity_avg = sum(e.intensity for e in recent) / len(recent)
                older_intensity_avg = sum(e.intensity for e in older) / len(older)
                drought_penalty = 10 if recent_intensity_avg < older_intensity_avg * 0.7 else 0
            else:
                drought_penalty = 0
        else:
            drought_penalty = 0

        score = (avg_intensity * 30) + (avg_duration / 60 * 10) + (sharing_rate * 10) + (unique_types * 2) + (unique_triggers * 1) + (recent_intensity * 20) + (recent_duration / 60 * 10) - drought_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intensity"] = round(sum(e.intensity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_duration"] = round(sum(e.duration_minutes for e in self._entries) / len(self._entries), 1)

            by_type = defaultdict(int)
            for e in self._entries:
                by_type[e.joy_type] += 1
            if by_type:
                dominant = max(by_type.items(), key=lambda x: x[1])
                self._stats["dominant_type"] = dominant[0]

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if len(self._entries) > 14:
                older = [e for e in self._entries if e.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
                if recent and older:
                    recent_intensity = sum(e.intensity for e in recent) / len(recent)
                    older_intensity = sum(e.intensity for e in older) / len(older)
                    self._stats["drought_risk"] = recent_intensity < older_intensity * 0.7

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

    def _log_entry(self, entry: JoyEntry):
        try:
            with open(JOY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "joy_type": entry.joy_type,
                    "intensity": entry.intensity,
                    "trigger": entry.trigger,
                    "duration": entry.duration_minutes,
                    "sharing": entry.sharing,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_jc_instance: Optional[JoyCultivator] = None
_jc_lock = threading.Lock()


def get_joy_cultivator() -> JoyCultivator:
    global _jc_instance
    with _jc_lock:
        if _jc_instance is None:
            _jc_instance = JoyCultivator()
        return _jc_instance
