"""
LOVE Wonder Cultivator — Awe and Beauty Intelligence (Modern AI Pattern)

Most adults lose wonder gradually. This cultivator:

1. WONDER TRACKING
   - Record awe moments and their triggers
   - Track wonder sources (nature, art, vastness, connection, mystery)
   - Log beauty encounters and their emotional effects

2. PATTERN ANALYSIS
   - Identify the user's wonder profile (cultivator, seeker, dormant, resistant)
   - Find wonder patterns that create lasting perspective shifts
   - Detect wonder droughts and their consequences

3. WONDER BUILDING
   - Suggest micro-wonders accessible right now
   - Provide perspective shifts that restore awe
   - Recommend beauty encounters matched to current capacity

4. AWE CULTIVATION
   - Track the correlation between wonder and wellbeing
   - Alert when wonder has been absent too long
   - Celebrate moments of genuine awe

Architecture:
- record_wonder(moment, source, intensity, effect): Log wonder
- get_wonder_stats(): Get wonder pattern analysis
- get_wonder_suggestion(context, capacity): Get suggestion
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

DATA_DIR = Path(__file__).parent.parent / "data" / "wonder_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WONDER_LOG = DATA_DIR / "wonders.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WonderEntry:
    """A tracked wonder entry."""
    entry_id: str = ""
    moment: str = ""  # what caused wonder
    source: str = ""  # nature, art, vastness, connection, mystery, skill, birth, death, etc
    intensity: float = 0.5  # 0-1
    perspective_shift: float = 0.0  # 0-1 did it change how you see things?
    beauty: float = 0.0  # 0-1
    duration_minutes: float = 0.0
    gratitude: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class WonderCultivator:
    """
    Intelligent wonder cultivator with awe detection and beauty cultivation.
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
            "avg_perspective_shift": 0.0,
            "wonder_drought": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_wonder(self, moment: str = "", source: str = "", intensity: float = 0.5, perspective_shift: float = 0.0, beauty: float = 0.0, duration_minutes: float = 0.0, gratitude: float = 0.0, notes: str = "") -> WonderEntry:
        """Record a wonder entry."""
        entry_id = f"wnd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = WonderEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            source=source or "general",
            intensity=intensity,
            perspective_shift=perspective_shift,
            beauty=beauty,
            duration_minutes=duration_minutes,
            gratitude=gratitude,
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

    def get_wonder_stats(self) -> Dict[str, Any]:
        """Get wonder pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "shift_sum": 0.0, "beauty_sum": 0.0})
        for e in self._entries:
            by_source[e.source]["count"] += 1
            by_source[e.source]["intensity_sum"] += e.intensity
            by_source[e.source]["shift_sum"] += e.perspective_shift
            by_source[e.source]["beauty_sum"] += e.beauty

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_shift": round(data["shift_sum"] / count, 2),
                "avg_beauty": round(data["beauty_sum"] / count, 2),
            }

        best_source = max(source_stats.items(), key=lambda x: x[1]["avg_intensity"]) if source_stats else ("", {})

        # Intensity vs perspective shift
        high_intensity = [e for e in self._entries if e.intensity > 0.7]
        low_intensity = [e for e in self._entries if e.intensity < 0.4]
        if high_intensity and low_intensity:
            high_shift = sum(e.perspective_shift for e in high_intensity) / len(high_intensity)
            low_shift = sum(e.perspective_shift for e in low_intensity) / len(low_intensity)
            high_gratitude = sum(e.gratitude for e in high_intensity) / len(high_intensity)
            low_gratitude = sum(e.gratitude for e in low_intensity) / len(low_intensity)
        else:
            high_shift = 0
            low_shift = 0
            high_gratitude = 0
            low_gratitude = 0

        # Beauty analysis
        high_beauty = [e for e in self._entries if e.beauty > 0.7]
        low_beauty = [e for e in self._entries if e.beauty < 0.4]
        if high_beauty and low_beauty:
            high_beauty_shift = sum(e.perspective_shift for e in high_beauty) / len(high_beauty)
            low_beauty_shift = sum(e.perspective_shift for e in low_beauty) / len(low_beauty)
        else:
            high_beauty_shift = 0
            low_beauty_shift = 0

        # Wonder drought detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        wonder_drought = len(recent) < 3

        # Trend
        if len(self._entries) > 14:
            older = list(self._entries)[-28:-14]
            recent_entries = list(self._entries)[-14:]
            if older and recent_entries:
                older_intensity = sum(e.intensity for e in older) / len(older)
                recent_intensity = sum(e.intensity for e in recent_entries) / len(recent_entries)
                intensity_trend = recent_intensity - older_intensity
            else:
                intensity_trend = 0
        else:
            intensity_trend = 0

        return {
            "total_entries": len(self._entries),
            "source_stats": source_stats,
            "best_source": best_source[0],
            "intensity_impact": {
                "high_intensity_shift": round(high_shift, 2),
                "low_intensity_shift": round(low_shift, 2),
                "high_intensity_gratitude": round(high_gratitude, 2),
                "low_intensity_gratitude": round(low_gratitude, 2),
            },
            "beauty_impact": {
                "high_beauty_shift": round(high_beauty_shift, 2),
                "low_beauty_shift": round(low_beauty_shift, 2),
            },
            "wonder_drought": wonder_drought,
            "avg_intensity": round(sum(e.intensity for e in self._entries) / len(self._entries), 2),
            "avg_perspective_shift": round(sum(e.perspective_shift for e in self._entries) / len(self._entries), 2),
            "intensity_trend": round(intensity_trend, 2),
        }

    def get_wonder_suggestion(self, context: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get wonder suggestion."""
        micro_wonders = [
            "Look at the sky right now. Not quickly. For thirty seconds. Notice the color gradient. If it's night, find a star. The same sky has been above every human who ever lived. You're part of that continuity.",
            "Find a leaf. Any leaf. Look at its veins. That's a river system. That's lungs. That's lightning. The universe repeats patterns at every scale. You're looking at infinity in miniature.",
            "Listen to a piece of music you loved as a teenager. Close your eyes. Remember who you were. Notice who you are now. The gap between those people is the story of your life.",
            "Watch someone who is excellent at something. Anything. A barista. A musician. A parent. Excellence is beautiful because it shows what's possible with devotion.",
            "Think of someone who has died. Remember their laugh. Their particular way of being. Death makes life precious. That's not morbid. That's the price of love.",
            "Hold a baby or pet an animal. If neither is available, watch a video of either. New life is wonder made visible. It never gets old.",
            "Read a poem aloud. Even if you don't understand it. The sound of language being used with care is beauty. Poetry is compressed wonder.",
            "Stand outside at night. Look at a light from a distant window. Someone is living an entire life in there. With their own wonders and griefs. You're both alive at the same time. That's connection.",
            "Watch the ocean, a river, or even rain. Water is ancient. The water you see has been clouds and glaciers and dinosaur blood. It's been everywhere. It's going everywhere.",
            "Look at your hands. Really look. They have done so much. Held so much. Created so much. They're evidence of a life lived. That's wonder.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Micro-wonder. Ten seconds of noticing. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Small wonder. A walk. A song. A conversation."
        else:
            capacity_note = "Good capacity. Big wonder. Seek something that expands your sense of what's possible."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(micro_wonders),
            "capacity_note": capacity_note,
            "principle": "Wonder is not the same as happiness. Wonder is the feeling that the world is bigger than you understood. It requires a willingness to be surprised. Adults who lose wonder don't lose it because the world becomes less wondrous. They lose it because they stop looking. The cure is attention. Attention is the doorway to wonder. And wonder is the doorway to gratitude. And gratitude is the doorway to contentment.",
        }

    def get_wonder_score(self) -> int:
        """Calculate overall wonder health (0-100)."""
        if not self._entries:
            return 25

        avg_intensity = sum(e.intensity for e in self._entries) / len(self._entries)
        avg_shift = sum(e.perspective_shift for e in self._entries) / len(self._entries)
        avg_beauty = sum(e.beauty for e in self._entries) / len(self._entries)
        avg_gratitude = sum(e.gratitude for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_intensity = sum(e.intensity for e in recent) / len(recent)
            recent_shift = sum(e.perspective_shift for e in recent) / len(recent)
        else:
            recent_intensity = 0
            recent_shift = 0

        # Wonder drought penalty
        drought_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 3:
            drought_penalty = 15

        # Source variety bonus
        unique_sources = len(set(e.source for e in self._entries))

        score = (avg_intensity * 25) + (avg_shift * 25) + (avg_beauty * 15) + (avg_gratitude * 10) + (recent_intensity * 10) + (recent_shift * 10) + (unique_sources * 2) - drought_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intensity"] = round(sum(e.intensity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_perspective_shift"] = round(sum(e.perspective_shift for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            self._stats["wonder_drought"] = len(recent) < 3

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

    def _log_entry(self, entry: WonderEntry):
        try:
            with open(WONDER_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "source": entry.source,
                    "intensity": entry.intensity,
                    "perspective_shift": entry.perspective_shift,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wc_instance: Optional[WonderCultivator] = None
_wc_lock = threading.Lock()


def get_wonder_cultivator() -> WonderCultivator:
    global _wc_instance
    with _wc_lock:
        if _wc_instance is None:
            _wc_instance = WonderCultivator()
        return _wc_instance
