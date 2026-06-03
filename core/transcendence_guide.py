"""
LOVE Transcendence Guide — Elevation Intelligence (Modern AI Pattern)

Most people live within the bounds of their personality. This guide:

1. TRANSCENDENCE TRACKING
   - Record transcendence experiences and their characteristics
   - Track transcendence types (ego dissolution, unity, timelessness, sacred, awe)
   - Log integration and transformation outcomes

2. PATTERN ANALYSIS
   - Identify the user's transcendence profile (rare, occasional, seeker, integrated)
   - Find conditions that reliably produce transcendent experiences
   - Detect spiritual materialism and experience-chasing

3. TRANSCENDENCE BUILDING
   - Suggest practices matched to current capacity and longing
   - Provide preparation and integration frameworks
   - Recommendation sustainable transcendence practices

4. ELEVATION CULTIVATION
   - Track the correlation between transcendence and life satisfaction
   - Alert when seeking is becoming addiction
   - Celebrate moments of genuine elevation

Architecture:
- record_experience(trigger, type, depth, integration): Log experience
- get_transcendence_stats(): Get transcendence pattern analysis
- get_transcendence_practice(longing, capacity): Get practice
- get_transcendence_score(): Calculate overall transcendence health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "transcendence_guide"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRANSCENDENCE_LOG = DATA_DIR / "experiences.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TranscendenceEntry:
    """A tracked transcendence entry."""
    entry_id: str = ""
    trigger: str = ""  # what triggered it
    trans_type: str = ""  # ego_dissolution, unity, timelessness, sacred, awe
    depth: float = 0.5  # 0-1
    duration: float = 0.0  # minutes
    integration: float = 0.5  # 0-1, how much carried into life
    life_change: float = 0.0  # 0-1, did it change behavior
    chasing: bool = False  # was this experience-chasing
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class TranscendenceGuide:
    """
    Intelligent transcendence guide with integration tracking and addiction detection.
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
            "avg_depth": 0.0,
            "avg_integration": 0.0,
            "chasing_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_experience(self, trigger: str = "", trans_type: str = "", depth: float = 0.5, duration: float = 0.0, integration: float = 0.5, life_change: float = 0.0, chasing: bool = False, notes: str = "") -> TranscendenceEntry:
        """Record a transcendence entry."""
        entry_id = f"trans_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = TranscendenceEntry(
            entry_id=entry_id,
            trigger=trigger or "unspecified",
            trans_type=trans_type or "awe",
            depth=depth,
            duration=duration,
            integration=integration,
            life_change=life_change,
            chasing=chasing,
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

    def get_transcendence_stats(self) -> Dict[str, Any]:
        """Get transcendence pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "int_sum": 0.0, "change_sum": 0.0, "chase_count": 0})
        for e in self._entries:
            by_type[e.trans_type]["count"] += 1
            by_type[e.trans_type]["depth_sum"] += e.depth
            by_type[e.trans_type]["int_sum"] += e.integration
            by_type[e.trans_type]["change_sum"] += e.life_change
            if e.chasing:
                by_type[e.trans_type]["chase_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_integration": round(data["int_sum"] / count, 2),
                "avg_life_change": round(data["change_sum"] / count, 2),
                "chasing_rate": round(data["chase_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_life_change"]) if type_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "change_sum": 0.0})
        for e in self._entries:
            by_trigger[e.trigger]["count"] += 1
            by_trigger[e.trigger]["depth_sum"] += e.depth
            by_trigger[e.trigger]["change_sum"] += e.life_change

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            trigger_stats[tr] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_life_change": round(data["change_sum"] / count, 2),
            }

        best_trigger = max(trigger_stats.items(), key=lambda x: x[1]["avg_depth"] + x[1]["avg_life_change"]) if trigger_stats else ("", {})

        # Integration vs depth
        high_int = [e for e in self._entries if e.integration > 0.7]
        low_int = [e for e in self._entries if e.integration < 0.4]
        if high_int and low_int:
            high_int_change = sum(e.life_change for e in high_int) / len(high_int)
            low_int_change = sum(e.life_change for e in low_int) / len(low_int)
        else:
            high_int_change = 0
            low_int_change = 0

        # Chasing detection
        chasing = [e for e in self._entries if e.chasing]
        if chasing:
            chasing_depth = sum(e.depth for e in chasing) / len(chasing)
            chasing_int = sum(e.integration for e in chasing) / len(chasing)
            chasing_rate = len(chasing) / len(self._entries)
            chasing_risk = chasing_rate > 0.3 and chasing_int < 0.4
        else:
            chasing_depth = 0
            chasing_int = 0
            chasing_rate = 0
            chasing_risk = False

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            recent_change = sum(e.life_change for e in recent) / len(recent)
            recent_chase = sum(1 for e in recent if e.chasing) / len(recent)
        else:
            recent_depth = 0
            recent_int = 0
            recent_change = 0
            recent_chase = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_depth = sum(e.depth for e in older) / len(older)
            older_int = sum(e.integration for e in older) / len(older)
            depth_trend = recent_depth - older_depth
            int_trend = recent_int - older_int
        else:
            depth_trend = 0
            int_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "trigger_stats": trigger_stats,
            "best_trigger": best_trigger[0],
            "integration_impact": {
                "high_integration_change": round(high_int_change, 2),
                "low_integration_change": round(low_int_change, 2),
            },
            "chasing_analysis": {
                "chasing_depth": round(chasing_depth, 2),
                "chasing_integration": round(chasing_int, 2),
                "chasing_rate": round(chasing_rate, 2),
            },
            "chasing_risk": chasing_risk,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
            "avg_life_change": round(sum(e.life_change for e in self._entries) / len(self._entries), 2),
            "depth_trend": round(depth_trend, 2),
            "integration_trend": round(int_trend, 2),
            "recent_chasing_rate": round(recent_chase, 2),
        }

    def get_transcendence_practice(self, longing: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "ego_dissolution": [
                "Who is aware of your thoughts? Not the thinker. Something prior. Rest there.",
                "The 'I' that seeks ego dissolution is the ego. Stop seeking. What's left?",
                "Question every identification. 'I am angry' -> 'Anger is present.' Who is the witness?",
            ],
            "unity": [
                "Look at anything. A tree. A person. Feel the space between you. Is it separate? Or continuous?",
                "Breathe in what the tree exhales. The tree breathes what you exhale. You've never been separate.",
                "Touch your skin. Feel the boundary. Now feel the air touching your skin. Where do you end?",
            ],
            "timelessness": [
                "Stop measuring time. No clocks. No agendas. Just now. Time is a concept. Now is real.",
                "Recall a moment when time disappeared. What were you doing? Do more of that.",
                "The past is memory. The future is imagination. Only now exists. Rest in the only real thing.",
            ],
            "sacred": [
                "Light a candle. Watch the flame. The flame has been burning since the first star. You're part of that chain.",
                "Read a sacred text slowly. One sentence. Let it read you. Don't interpret. Receive.",
                "Visit a place that feels sacred to you. Not necessarily religious. A forest. A mountain. Your grandmother's kitchen.",
            ],
            "awe": [
                "Look at the night sky. Not briefly. Stare. Consider the distances. The time. You are made of that.",
                "Watch a storm. The power. The indifference. You are small. That's not insulting. That's relief.",
                "Hold a newborn. Or an old person dying. The threshold moments. Birth and death. Awe lives at thresholds.",
            ],
            "general": [
                "Transcendence is not escape. It's deeper engagement. With reality. With yourself. With the mystery.",
                "Don't chase experiences. They come. They go. The real work is integration. What changes when you return?",
                "The ordinary is the gateway to the extraordinary. Washing dishes. Walking. Breathing. Start there.",
            ],
        }

        selected = practices.get(longing, practices["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of full attention. That's a transcendent experience. You don't need more."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Extended contemplation. 30 minutes. Silence. See what arises."
        else:
            capacity_note = "High capacity. This is when you sit with a teacher. Or go on retreat. Or take psychedelics with intention."

        return {
            "longing": longing or "general",
            "capacity": capacity,
            "practice": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most people think transcendence is about leaving the world. It's not. It's about seeing through it. The world doesn't change. Your relationship to it does. The same traffic jam can be hell or meditation. The same job can be drudgery or service. Transcendence is not an experience. It's a lens. And lenses can be cultivated.",
        }

    def get_transcendence_score(self) -> int:
        """Calculate overall transcendence health (0-100)."""
        if not self._entries:
            return 20

        # Depth, integration, and life change
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_change = sum(e.life_change for e in self._entries) / len(self._entries)

        # Low chasing
        chasing_rate = sum(1 for e in self._entries if e.chasing) / len(self._entries)

        # Type variety
        unique_types = len(set(e.trans_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            recent_change = sum(e.life_change for e in recent) / len(recent)
            recent_chase = sum(1 for e in recent if e.chasing) / len(recent)
        else:
            recent_depth = 0
            recent_int = 0
            recent_change = 0
            recent_chase = 0

        # Chasing penalty
        chasing_penalty = 0
        if recent_chase > 0.3:
            chasing_penalty = 15

        score = (avg_depth * 25) + (avg_int * 25) + (avg_change * 15) + ((1 - chasing_rate) * 10) + (unique_types * 3) + (recent_depth * 10) + (recent_int * 10) + (recent_change * 5) - chasing_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integration"] = round(sum(e.integration for e in self._entries) / len(self._entries), 2)

            chasing = [e for e in self._entries if e.chasing]
            if chasing:
                chasing_int = sum(e.integration for e in chasing) / len(chasing)
                chasing_rate = len(chasing) / len(self._entries)
                self._stats["chasing_risk"] = chasing_rate > 0.3 and chasing_int < 0.4

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.transcendence_guide")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.transcendence_guide")

    def _log_entry(self, entry: TranscendenceEntry):
        try:
            with open(TRANSCENDENCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "trigger": entry.trigger,
                    "trans_type": entry.trans_type,
                    "depth": entry.depth,
                    "duration": entry.duration,
                    "integration": entry.integration,
                    "life_change": entry.life_change,
                    "chasing": entry.chasing,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.transcendence_guide")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_tg_instance: Optional[TranscendenceGuide] = None
_tg_lock = threading.Lock()


def get_transcendence_guide() -> TranscendenceGuide:
    global _tg_instance
    with _tg_lock:
        if _tg_instance is None:
            _tg_instance = TranscendenceGuide()
        return _tg_instance
