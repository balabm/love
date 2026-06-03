"""
LOVE Wonder Tracker — Awe Intelligence (Modern AI Pattern)

Most people stop experiencing wonder. This tracker:

1. WONDER TRACKING
   - Record moments of awe, beauty, and transcendence
   - Track the intensity and duration of wonder experiences
   - Log what triggered the wonder and its after-effects

2. PATTERN ANALYSIS
   - Identify the user's wonder triggers (nature, art, people, ideas, vastness, intricacy)
   - Find wonder droughts and their impact on mood
   - Detect which times/places are most conducive to wonder

3. WONDER GENERATION
   - Suggest micro-wonders (30-second awe injections)
   - Recommend wonder-inducing experiences based on style
   - Provide wonder priming exercises

4. WELLNESS CONNECTION
   - Track the correlation between wonder and wellbeing
   - Alert when wonder has been absent too long
   - Suggest wonder as recovery after stress

Architecture:
- record_wonder(trigger, intensity, duration, after_effect): Log wonder
- get_wonder_stats(): Get wonder pattern analysis
- get_wonder_suggestion(style, time): Get wonder prompt
- get_wonder_score(): Calculate overall wonder health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "wonder_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WONDER_LOG = DATA_DIR / "wonders.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WonderMoment:
    """A tracked wonder moment."""
    wonder_id: str = ""
    trigger: str = ""  # what caused the wonder
    trigger_type: str = ""  # nature, art, people, idea, vastness, intricacy, connection, mystery
    intensity: float = 0.5  # 0-1
    duration_minutes: float = 0.0
    after_effect: str = ""  # calm, energized, grateful, inspired, humbled, connected
    mood_before: float = 0.5  # 0-1
    mood_after: float = 0.5
    location: str = ""
    time_of_day: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class WonderTracker:
    """
    Intelligent wonder tracker with awe pattern analysis and micro-wonder generation.
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
        self._wonders: deque = deque(maxlen=200)
        self._stats = {
            "total_wonders": 0,
            "avg_intensity": 0.0,
            "avg_duration": 0.0,
            "dominant_trigger": "",
            "wonder_drought": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_wonder(self, trigger: str = "", trigger_type: str = "", intensity: float = 0.5, duration: float = 0, after_effect: str = "", mood_before: float = 0.5, mood_after: float = 0.5, location: str = "", time_of_day: str = "", notes: str = "") -> WonderMoment:
        """Record a wonder moment."""
        wonder_id = f"wonder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._wonders)}"
        w = WonderMoment(
            wonder_id=wonder_id,
            trigger=trigger or "unspecified",
            trigger_type=trigger_type or "nature",
            intensity=intensity,
            duration_minutes=duration,
            after_effect=after_effect or "calm",
            mood_before=mood_before,
            mood_after=mood_after,
            location=location or "",
            time_of_day=time_of_day or datetime.now().strftime("%H:%M"),
            notes=notes,
        )

        with self._lock:
            self._wonders.append(w)
            self._stats["total_wonders"] += 1
            self._update_stats()

        self._save_stats()
        self._log_wonder(w)

        return w

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_wonder_stats(self) -> Dict[str, Any]:
        """Get wonder pattern analysis."""
        if not self._wonders:
            return {"status": "insufficient_data"}

        # Trigger type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "duration_sum": 0.0})
        for w in self._wonders:
            by_type[w.trigger_type]["count"] += 1
            by_type[w.trigger_type]["intensity_sum"] += w.intensity
            by_type[w.trigger_type]["duration_sum"] += w.duration_minutes

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
            }

        dominant = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Time analysis
        by_time = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for w in self._wonders:
            hour = w.time_of_day[:2] if w.time_of_day else "00"
            by_time[hour]["count"] += 1
            by_time[hour]["intensity_sum"] += w.intensity

        time_stats = {}
        for h, data in by_time.items():
            count = data["count"]
            if count >= 2:
                time_stats[h] = {
                    "count": count,
                    "avg_intensity": round(data["intensity_sum"] / count, 2),
                }

        # Mood impact
        mood_changes = [w.mood_after - w.mood_before for w in self._wonders]
        avg_mood_change = sum(mood_changes) / len(mood_changes) if mood_changes else 0

        # Drought
        recent = [w for w in self._wonders if w.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        drought = len(recent) < 2

        # After-effect analysis
        by_effect = defaultdict(int)
        for w in self._wonders:
            by_effect[w.after_effect] += 1

        return {
            "total_wonders": len(self._wonders),
            "type_stats": type_stats,
            "dominant_trigger": dominant[0],
            "time_stats": time_stats,
            "avg_intensity": round(sum(w.intensity for w in self._wonders) / len(self._wonders), 2),
            "avg_duration": round(sum(w.duration_minutes for w in self._wonders) / len(self._wonders), 1),
            "avg_mood_change": round(avg_mood_change, 2),
            "after_effect_distribution": dict(by_effect),
            "drought": drought,
        }

    def get_wonder_suggestion(self, style: str = "", time: float = 5, location: str = "indoors") -> Dict[str, Any]:
        """Get wonder prompt."""
        wonders = {
            "nature": [
                "Go outside. Look at the sky for 60 seconds. Notice the scale.",
                "Find a leaf, flower, or insect. Examine it like it's the most complex machine ever built.",
                "Watch clouds move. Imagine you're seeing Earth breathe.",
                "Stand barefoot on grass or soil. Feel the planet holding you up.",
                "Listen to birds. Each song is a unique creature's expression of being alive.",
            ],
            "art": [
                "Listen to a piece of music you've never heard. Close your eyes. Let it move through you.",
                "Look at a painting online for 3 minutes. Notice something new every 30 seconds.",
                "Read a poem aloud. Feel the rhythm in your body.",
                "Watch a dancer. Any dancer. Notice how the human body can become pure expression.",
                "Look at architecture around you. Someone imagined that, then built it.",
            ],
            "people": [
                "Think of someone who loves you. Let the fact of their love astonish you.",
                "Watch children playing. They're learning the world from scratch.",
                "Think about your ancestors 500 years ago. Their choices led to you.",
                "Look at a crowd. Each person has a universe inside them.",
                "Call someone and tell them one thing you genuinely admire about them.",
            ],
            "idea": [
                "Read about a scientific discovery that changed everything. We figured that out with brains.",
                "Think about infinity for 30 seconds. Your mind can conceive of the inconceivable.",
                "Learn one fact about the universe that makes you feel small but connected.",
                "Consider that you're made of star matter. Literally.",
                "Think about consciousness. You're aware that you're aware. That's extraordinary.",
            ],
            "vastness": [
                "Look up at night. Pick one star. Its light is ancient. You're time-traveling with your eyes.",
                "Watch the ocean or a large body of water. Feel the ancient patience of water.",
                "Look at a mountain. It was there before your grandparents. It will be after your grandchildren.",
                "Think about the age of the Earth. Your entire life is a blink.",
                "Watch a time-lapse of plants growing or cities changing.",
            ],
            "intricacy": [
                "Look at your own hand. The complexity of bone, muscle, nerve, and intention.",
                "Watch a slow-motion video of something ordinary (water drop, bird flight, eyelash blink).",
                "Think about how many processes are happening in your body right now without your conscious control.",
                "Look closely at a woven fabric, a spiderweb, or frost patterns.",
                "Consider the number of living cells in your body. 30 trillion. Each one working.",
            ],
            "connection": [
                "Think about how many people contributed to your morning coffee.",
                "Consider that someone, somewhere, is thinking about you right now.",
                "Think about the internet. Millions of humans connected, sharing, learning.",
                "Feel your heartbeat. It's been beating without stopping since before you were born.",
                "Think about language. We make sounds, and meaning appears in another person's mind.",
            ],
            "mystery": [
                "Think about something you don't understand. Let the not-knowing feel spacious, not anxious.",
                "Consider dreams. Every night, you enter a reality you don't control.",
                "Think about déjà vu or coincidence. Let the mystery be delightful.",
                "Consider that we don't know what consciousness is. You're a mystery to science.",
                "Think about death not with fear, but with curiosity. The ultimate unknown.",
            ],
        }

        if style and style in wonders:
            selected = random.choice(wonders[style])
        else:
            all_wonders = [w for cat in wonders.values() for w in cat]
            selected = random.choice(all_wonders)

        return {
            "prompt": selected,
            "style": style or "mixed",
            "time": time,
            "location": location,
            "instruction": "Don't analyze. Don't post about it. Just experience it. Let it fill you.",
            "after": "Notice how you feel for the next 10 minutes. No need to name it.",
        }

    def get_wonder_score(self) -> int:
        """Calculate overall wonder health (0-100)."""
        if not self._wonders:
            return 35

        # Intensity
        avg_intensity = sum(w.intensity for w in self._wonders) / len(self._wonders)

        # Frequency
        recent = [w for w in self._wonders if w.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        frequency = len(recent)

        # Mood improvement
        mood_changes = [w.mood_after - w.mood_before for w in self._wonders]
        avg_mood_change = sum(mood_changes) / len(mood_changes) if mood_changes else 0

        # Variety
        unique_types = len(set(w.trigger_type for w in self._wonders))

        # Duration (longer isn't always better, but very short suggests shallow)
        avg_duration = sum(w.duration_minutes for w in self._wonders) / len(self._wonders)

        score = (avg_intensity * 30) + (min(frequency, 8) * 5) + (avg_mood_change * 20) + (unique_types * 5) + (min(avg_duration / 10, 1) * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._wonders:
            self._stats["avg_intensity"] = round(sum(w.intensity for w in self._wonders) / len(self._wonders), 2)
            self._stats["avg_duration"] = round(sum(w.duration_minutes for w in self._wonders) / len(self._wonders), 1)

            by_type = defaultdict(int)
            for w in self._wonders:
                by_type[w.trigger_type] += 1
            if by_type:
                self._stats["dominant_trigger"] = max(by_type.items(), key=lambda x: x[1])[0]

            recent = [w for w in self._wonders if w.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            self._stats["wonder_drought"] = len(recent) < 2

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.wonder_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.wonder_tracker")

    def _log_wonder(self, wonder: WonderMoment):
        try:
            with open(WONDER_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": wonder.timestamp,
                    "trigger": wonder.trigger,
                    "type": wonder.trigger_type,
                    "intensity": wonder.intensity,
                    "after_effect": wonder.after_effect,
                    "mood_change": wonder.mood_after - wonder.mood_before,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.wonder_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wt_instance: Optional[WonderTracker] = None
_wt_lock = threading.Lock()


def get_wonder_tracker() -> WonderTracker:
    global _wt_instance
    with _wt_lock:
        if _wt_instance is None:
            _wt_instance = WonderTracker()
        return _wt_instance
