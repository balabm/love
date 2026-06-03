"""
LOVE Voice Presence Coach — Vocal Intelligence (Modern AI Pattern)

Most people speak without presence. This coach:

1. VOICE TRACKING
   - Record voice moments and their characteristics
   - Track voice types (speaking, presenting, singing, reading, storytelling, comforting)
   - Log presence, power, clarity, warmth, and authenticity of voice

2. PATTERN ANALYSIS
   - Identify the user's voice profile (timid, rushed, developing, commanding)
   - Find voice patterns that create impact vs invisibility
   - Detect chronic vocal self-diminishment and its costs

3. PRESENCE BUILDING
   - Suggest practices for vocal presence and power
   - Provide frameworks for breath-supported speaking
   - Recommend practices for finding one's true voice

4. VOCAL IMPACT CULTIVATION
   - Track the correlation between voice presence and influence
   - Alert when shrinking is becoming the default
   - Celebrate moments of genuine vocal authority

Architecture:
- record_voice(context, type, presence, power, clarity, warmth, authenticity): Log voice
- get_voice_stats(): Get voice pattern analysis
- get_voice_suggestion(capacity, context): Get suggestion
- get_voice_score(): Calculate overall voice health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "voice_presence_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VOICE_LOG = DATA_DIR / "voices.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class VoiceEntry:
    """A tracked voice moment."""
    entry_id: str = ""
    context: str = ""  # what was the situation
    voice_type: str = ""  # speaking, presenting, singing, reading, storytelling, comforting
    presence: float = 0.0  # 0-1
    power: float = 0.0  # 0-1
    clarity: float = 0.0  # 0-1
    warmth: float = 0.0  # 0-1
    authenticity: float = 0.0  # 0-1
    breath: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VoicePresenceCoach:
    """
    Intelligent voice presence coach with diminishment detection and vocal impact cultivation.
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
            "avg_presence": 0.0,
            "avg_authenticity": 0.0,
            "diminishment_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_voice(self, context: str = "", voice_type: str = "", presence: float = 0.0, power: float = 0.0, clarity: float = 0.0, warmth: float = 0.0, authenticity: float = 0.0, breath: float = 0.0, notes: str = "") -> VoiceEntry:
        """Record a voice moment."""
        entry_id = f"voi_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = VoiceEntry(
            entry_id=entry_id,
            context=context or "unspecified",
            voice_type=voice_type or "speaking",
            presence=presence,
            power=power,
            clarity=clarity,
            warmth=warmth,
            authenticity=authenticity,
            breath=breath,
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

    def get_voice_stats(self) -> Dict[str, Any]:
        """Get voice pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "presence_sum": 0.0, "clarity_sum": 0.0, "warmth_sum": 0.0})
        for e in self._entries:
            by_type[e.voice_type]["count"] += 1
            by_type[e.voice_type]["presence_sum"] += e.presence
            by_type[e.voice_type]["clarity_sum"] += e.clarity
            by_type[e.voice_type]["warmth_sum"] += e.warmth

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_presence": round(data["presence_sum"] / count, 2),
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_warmth": round(data["warmth_sum"] / count, 2),
            }

        # Presence analysis
        high_pres = [e for e in self._entries if e.presence > 0.7]
        low_pres = [e for e in self._entries if e.presence < 0.4]
        if high_pres and low_pres:
            high_pres_power = sum(e.power for e in high_pres) / len(high_pres)
            low_pres_power = sum(e.power for e in low_pres) / len(low_pres)
            high_pres_auth = sum(e.authenticity for e in high_pres) / len(high_pres)
            low_pres_auth = sum(e.authenticity for e in low_pres) / len(low_pres)
        else:
            high_pres_power = 0
            low_pres_power = 0
            high_pres_auth = 0
            low_pres_auth = 0

        # Breath analysis
        high_breath = [e for e in self._entries if e.breath > 0.7]
        low_breath = [e for e in self._entries if e.breath < 0.4]
        if high_breath and low_breath:
            high_breath_clarity = sum(e.clarity for e in high_breath) / len(high_breath)
            low_breath_clarity = sum(e.clarity for e in low_breath) / len(low_breath)
        else:
            high_breath_clarity = 0
            low_breath_clarity = 0

        # Diminishment risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_pres = sum(e.presence for e in recent) / len(recent)
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            diminishment_risk = recent_pres < 0.3 and recent_auth < 0.3
        else:
            diminishment_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "presence_impact": {
                "high_presence_power": round(high_pres_power, 2),
                "low_presence_power": round(low_pres_power, 2),
                "high_presence_authenticity": round(high_pres_auth, 2),
                "low_presence_authenticity": round(low_pres_auth, 2),
            },
            "breath_effect": {
                "high_breath_clarity": round(high_breath_clarity, 2),
                "low_breath_clarity": round(low_breath_clarity, 2),
            },
            "diminishment_risk": diminishment_risk,
            "avg_presence": round(sum(e.presence for e in self._entries) / len(self._entries), 2),
            "avg_authenticity": round(sum(e.authenticity for e in self._entries) / len(self._entries), 2),
        }

    def get_voice_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get voice suggestion."""
        suggestions = [
            "Your voice is not just sound. It's presence. It's power. It's the physical manifestation of your authority. Most people speak from their throat. They rush. They trail off. They apologize with their tone. Don't be most people.",
            "Breathe before you speak. Not just a shallow breath. A deep one. Into your belly. Your voice rides on breath. No breath, no power. Shallow breath, thin voice. Deep breath, full voice.",
            "Slow down. Most people speak too fast when they're nervous. And too fast when they're excited. And too fast when they want to be heard. Slow speech is powerful speech. It says 'I deserve your attention.'",
            "End your sentences. Don't let them trail off into question marks. Declarative statements end with periods. They land. They settle. They're heard. Practice landing your sentences.",
            "Lower your pitch slightly. Not artificially. Just stop tightening your throat. Relax your jaw. Let your voice drop into its natural register. A relaxed voice is a powerful voice.",
            "Pause. Between sentences. Between thoughts. Between words. Silence is not empty. It's full. It creates space for your words to land. And it says you're not afraid of being heard.",
            "Speak to the back of the room. Not just the front. Project. Not shout. Project. Imagine your voice traveling. Reaching. Touching. Your voice can go further than you think.",
            "Record yourself. Listen. Most people hate the sound of their own voice. Get over it. You need to know how you sound. What you do unconsciously. Where you rush. Where you fade. Data.",
            "Warm up your voice. Humming. Lip trills. Tongue twisters. Your voice is an instrument. Instruments need tuning. You wouldn't play a cold violin. Don't speak with a cold voice.",
            "The person who speaks with presence is not loud. They're grounded. Their voice comes from their body, not their throat. From their breath, not their anxiety. From their truth, not their fear. That's the practice."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One deep breath before speaking. One sentence landed. One pause taken. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A vocal warm-up. A recording listened to. A slower speech practiced. Medium presence."
        else:
            capacity_note = "Good capacity. Deep vocal work. A systematic practice of breath, presence, and authentic power. You have the strength to be heard."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Voice presence is not about being loud. It's about being present. Most people speak as if they're trying not to be noticed. They mumble. They rush. They trail off. They apologize with their tone. And they wonder why they're not heard. Why they're not respected. Why they're not taken seriously. The work of voice presence coaching is about reclaiming the power of your voice. About understanding that how you speak is as important as what you say. About breath. About pace. About pitch. About pause. And about recognizing that your voice is the vehicle for your truth. When you speak with presence, people listen. Not because you're loud. Because you're there."
        }

    def get_voice_score(self) -> int:
        """Calculate overall voice health (0-100)."""
        if not self._entries:
            return 25

        avg_pres = sum(e.presence for e in self._entries) / len(self._entries)
        avg_power = sum(e.power for e in self._entries) / len(self._entries)
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_warmth = sum(e.warmth for e in self._entries) / len(self._entries)
        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_breath = sum(e.breath for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_pres = sum(e.presence for e in recent) / len(recent)
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
        else:
            recent_pres = 0
            recent_auth = 0

        # Diminishment penalty
        dim_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_pres_30 = sum(e.presence for e in last_30) / len(last_30)
            recent_auth_30 = sum(e.authenticity for e in last_30) / len(last_30)
            if recent_pres_30 < 0.3 and recent_auth_30 < 0.3:
                dim_penalty = 15

        # Type variety
        unique_types = len(set(e.voice_type for e in self._entries))

        score = (avg_pres * 25) + (avg_power * 15) + (avg_clarity * 15) + (avg_warmth * 10) + (avg_auth * 15) + (avg_breath * 10) + (recent_pres * 5) + (recent_auth * 5) + (unique_types * 2) - dim_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_presence"] = round(sum(e.presence for e in self._entries) / len(self._entries), 2)
            self._stats["avg_authenticity"] = round(sum(e.authenticity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_pres = sum(e.presence for e in recent) / len(recent)
                recent_auth = sum(e.authenticity for e in recent) / len(recent)
                self._stats["diminishment_risk"] = recent_pres < 0.3 and recent_auth < 0.3
            else:
                self._stats["diminishment_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.voice_presence_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.voice_presence_coach")

    def _log_entry(self, entry: VoiceEntry):
        try:
            with open(VOICE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "context": entry.context,
                    "voice_type": entry.voice_type,
                    "presence": entry.presence,
                    "authenticity": entry.authenticity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.voice_presence_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vpc_instance: Optional[VoicePresenceCoach] = None
_vpc_lock = threading.Lock()


def get_voice_presence_coach() -> VoicePresenceCoach:
    global _vpc_instance
    with _vpc_lock:
        if _vpc_instance is None:
            _vpc_instance = VoicePresenceCoach()
        return _vpc_instance
