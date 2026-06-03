"""
LOVE Sound Healing Guide — Acoustic Intelligence (Modern AI Pattern)

Most people ignore sound. This guide:

1. SOUND TRACKING
   - Record sound healing moments and their characteristics
   - Track sound types (nature, binaural, white_noise, chanting, singing_bowl, silence)
   - Log relaxation, clarity, restoration, and healing quality

2. PATTERN ANALYSIS
   - Identify the user's sound profile (noisy, occasional, intentional, healing)
   - Find sound patterns that restore vs deplete
   - Detect chronic noise exposure and its costs

3. HEALING BUILDING
   - Suggest practices for intentional sound use
   - Provide frameworks for acoustic environments
   - Recommend practices for sound as medicine

4. ACOUSTIC RESTORATION CULTIVATION
   - Track the correlation between sound and restoration
   - Alert when noise pollution is dominating
   - Celebrate moments of genuine sonic healing

Architecture:
- record_sound(sound, type, relaxation, clarity, restoration, healing): Log sound
- get_sound_stats(): Get sound pattern analysis
- get_sound_suggestion(capacity, context): Get suggestion
- get_sound_score(): Calculate overall sound health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "sound_healing_guide"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SOUND_LOG = DATA_DIR / "sounds.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SoundEntry:
    """A tracked sound healing moment."""
    entry_id: str = ""
    sound: str = ""  # what was experienced
    sound_type: str = ""  # nature, binaural, white_noise, chanting, singing_bowl, silence
    relaxation: float = 0.0  # 0-1
    clarity: float = 0.0  # 0-1
    restoration: float = 0.0  # 0-1
    healing: float = 0.0  # 0-1
    intention: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SoundHealingGuide:
    """
    Intelligent sound healing guide with noise detection and acoustic restoration cultivation.
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
            "avg_relaxation": 0.0,
            "avg_restoration": 0.0,
            "noise_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_sound(self, sound: str = "", sound_type: str = "", relaxation: float = 0.0, clarity: float = 0.0, restoration: float = 0.0, healing: float = 0.0, intention: float = 0.0, notes: str = "") -> SoundEntry:
        """Record a sound healing moment."""
        entry_id = f"snd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SoundEntry(
            entry_id=entry_id,
            sound=sound or "unspecified",
            sound_type=sound_type or "nature",
            relaxation=relaxation,
            clarity=clarity,
            restoration=restoration,
            healing=healing,
            intention=intention,
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

    def get_sound_stats(self) -> Dict[str, Any]:
        """Get sound pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "relax_sum": 0.0, "restore_sum": 0.0, "healing_sum": 0.0})
        for e in self._entries:
            by_type[e.sound_type]["count"] += 1
            by_type[e.sound_type]["relax_sum"] += e.relaxation
            by_type[e.sound_type]["restore_sum"] += e.restoration
            by_type[e.sound_type]["healing_sum"] += e.healing

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_relaxation": round(data["relax_sum"] / count, 2),
                "avg_restoration": round(data["restore_sum"] / count, 2),
                "avg_healing": round(data["healing_sum"] / count, 2),
            }

        # Relaxation analysis
        high_rel = [e for e in self._entries if e.relaxation > 0.7]
        low_rel = [e for e in self._entries if e.relaxation < 0.4]
        if high_rel and low_rel:
            high_rel_rest = sum(e.restoration for e in high_rel) / len(high_rel)
            low_rel_rest = sum(e.restoration for e in low_rel) / len(low_rel)
            high_rel_heal = sum(e.healing for e in high_rel) / len(high_rel)
            low_rel_heal = sum(e.healing for e in low_rel) / len(low_rel)
        else:
            high_rel_rest = 0
            low_rel_rest = 0
            high_rel_heal = 0
            low_rel_heal = 0

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_rel = sum(e.relaxation for e in high_int) / len(high_int)
            low_int_rel = sum(e.relaxation for e in low_int) / len(low_int)
        else:
            high_int_rel = 0
            low_int_rel = 0

        # Noise risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_rel = sum(e.relaxation for e in recent) / len(recent)
            recent_restore = sum(e.restoration for e in recent) / len(recent)
            noise_risk = recent_rel < 0.3 and recent_restore < 0.3
        else:
            noise_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "relaxation_impact": {
                "high_relaxation_restoration": round(high_rel_rest, 2),
                "low_relaxation_restoration": round(low_rel_rest, 2),
                "high_relaxation_healing": round(high_rel_heal, 2),
                "low_relaxation_healing": round(low_rel_heal, 2),
            },
            "intention_effect": {
                "high_intention_relaxation": round(high_int_rel, 2),
                "low_intention_relaxation": round(low_int_rel, 2),
            },
            "noise_risk": noise_risk,
            "avg_relaxation": round(sum(e.relaxation for e in self._entries) / len(self._entries), 2),
            "avg_restoration": round(sum(e.restoration for e in self._entries) / len(self._entries), 2),
        }

    def get_sound_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get sound suggestion."""
        suggestions = [
            "Sound is not just what you hear. It's what you feel. The hum of a city. The rustle of leaves. The silence between notes. Pay attention to the acoustic environment. It shapes your nervous system.",
            "Nature sounds are medicine. Birdsong. Ocean waves. Rain. These sounds evolved with us. Our nervous systems recognize them as safe. Use them. Especially when you're stressed.",
            "Binaural beats can shift brain states. Different frequencies for different states. Delta for sleep. Theta for creativity. Alpha for relaxation. Beta for focus. Use them intentionally.",
            "Singing bowls are not just for monks. The vibrations penetrate the body. They massage the cells. They calm the mind. Find a bowl. Learn to play it. Or just listen.",
            "Silence is the most healing sound. And the rarest. Find it. Create it. Protect it. In a world of noise, silence is a radical act of self-care.",
            "Notice the sounds that drain you. Traffic. Construction. Alarms. Arguing. These are not neutral. They cost you. Minimize them. Use noise-cancelling headphones. Close windows. Leave.",
            "Chanting changes your physiology. The vibration in your chest. The extended exhale. The rhythmic repetition. It's not spiritual mumbo-jumbo. It's breath work with sound.",
            "White noise can mask disruptive sounds. But it can also be disruptive itself. Use it when you need to sleep or focus. But don't live in it. Silence is better.",
            "Your voice is a healing instrument. Humming. Singing. Toning. These vibrations soothe your vagus nerve. Calm your heart. Regulate your breath. Use your voice. Even alone.",
            "The person who curates their acoustic environment curates their mental environment. Sound is not background. It's foreground. It's medicine. Use it well."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One minute of nature sounds. One moment of silence. One hum. One deep listening. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A sound healing session. A curated acoustic environment. A chanting practice. Medium healing."
        else:
            capacity_note = "Good capacity. Deep acoustic work. A systematic practice of sonic healing and environmental curation. You have the strength to hear deeply."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Sound healing is not alternative medicine. It's ancient medicine. Every culture has used sound for healing. Drumming. Chanting. Singing bowls. Nature sounds. These are not superstitions. They're technologies. Technologies that work directly on the nervous system. On the brain waves. On the heart rate. On the breath. The modern world is full of noise pollution. Traffic. Alarms. Notifications. Construction. This noise is not neutral. It raises cortisol. It disrupts sleep. It fragments attention. The work of sound healing is about becoming conscious of your acoustic environment. About curating it. About using sound intentionally for restoration. And about understanding that silence is not the absence of sound. It's the presence of peace."
        }

    def get_sound_score(self) -> int:
        """Calculate overall sound health (0-100)."""
        if not self._entries:
            return 25

        avg_rel = sum(e.relaxation for e in self._entries) / len(self._entries)
        avg_clr = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_rest = sum(e.restoration for e in self._entries) / len(self._entries)
        avg_heal = sum(e.healing for e in self._entries) / len(self._entries)
        avg_int = sum(e.intention for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_rel = sum(e.relaxation for e in recent) / len(recent)
            recent_rest = sum(e.restoration for e in recent) / len(recent)
        else:
            recent_rel = 0
            recent_rest = 0

        # Noise penalty
        noise_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_rel_30 = sum(e.relaxation for e in last_30) / len(last_30)
            recent_rest_30 = sum(e.restoration for e in last_30) / len(last_30)
            if recent_rel_30 < 0.3 and recent_rest_30 < 0.3:
                noise_penalty = 15

        # Type variety
        unique_types = len(set(e.sound_type for e in self._entries))

        score = (avg_rel * 25) + (avg_clr * 15) + (avg_rest * 20) + (avg_heal * 15) + (avg_int * 10) + (recent_rel * 5) + (recent_rest * 5) + (unique_types * 2) - noise_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_relaxation"] = round(sum(e.relaxation for e in self._entries) / len(self._entries), 2)
            self._stats["avg_restoration"] = round(sum(e.restoration for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_rel = sum(e.relaxation for e in recent) / len(recent)
                recent_rest = sum(e.restoration for e in recent) / len(recent)
                self._stats["noise_risk"] = recent_rel < 0.3 and recent_rest < 0.3
            else:
                self._stats["noise_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sound_healing_guide")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sound_healing_guide")

    def _log_entry(self, entry: SoundEntry):
        try:
            with open(SOUND_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "sound": entry.sound,
                    "sound_type": entry.sound_type,
                    "relaxation": entry.relaxation,
                    "restoration": entry.restoration,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sound_healing_guide")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_shg_instance: Optional[SoundHealingGuide] = None
_shg_lock = threading.Lock()


def get_sound_healing_guide() -> SoundHealingGuide:
    global _shg_instance
    with _shg_lock:
        if _shg_instance is None:
            _shg_instance = SoundHealingGuide()
        return _shg_instance
