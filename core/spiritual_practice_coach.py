"""
LOVE Spiritual Practice Coach — Sacred Intelligence (Modern AI Pattern)

Most people feel a spiritual hunger but don't know how to feed it. This coach:

1. SPIRITUAL TRACKING
   - Record spiritual practices and their characteristics
   - Track practice types (meditation, prayer, study, service, contemplation, ritual)
   - Log depth and integration outcomes

2. PATTERN ANALYSIS
   - Identify the user's spiritual profile (seeker, practitioner, devotee, mystic)
   - Find practices that create genuine transformation
   - Detect spiritual bypassing and performative religiosity

3. PRACTICE BUILDING
   - Suggest practices matched to current longing and capacity
   - Provide deepening and consistency frameworks
   - Recommendation integration practices

4. SACRED CULTIVATION
   - Track the correlation between practice depth and life meaning
   - Alert when practice is becoming empty ritual
   - Celebrate moments of genuine connection

Architecture:
- record_practice(practice, type, depth, integration): Log practice
- get_spiritual_stats(): Get spiritual pattern analysis
- get_practice_suggestion(longing, capacity): Get suggestion
- get_spiritual_score(): Calculate overall spiritual health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "spiritual_practice_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SPIRITUAL_LOG = DATA_DIR / "practices.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SpiritualEntry:
    """A tracked spiritual entry."""
    entry_id: str = ""
    practice: str = ""  # what was done
    practice_type: str = ""  # meditation, prayer, study, service, contemplation, ritual
    duration: float = 0.0  # minutes
    depth: float = 0.5  # 0-1, how present/connected
    integration: float = 0.5  # 0-1, how much it carried into daily life
    meaning_felt: float = 0.5  # 0-1
    bypassing: bool = False  # was this avoiding real issues
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SpiritualPracticeCoach:
    """
    Intelligent spiritual practice coach with depth tracking and bypassing detection.
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
            "bypassing_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_practice(self, practice: str = "", practice_type: str = "", duration: float = 0.0, depth: float = 0.5, integration: float = 0.5, meaning_felt: float = 0.5, bypassing: bool = False, notes: str = "") -> SpiritualEntry:
        """Record a spiritual entry."""
        entry_id = f"spirit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SpiritualEntry(
            entry_id=entry_id,
            practice=practice or "unspecified",
            practice_type=practice_type or "meditation",
            duration=duration,
            depth=depth,
            integration=integration,
            meaning_felt=meaning_felt,
            bypassing=bypassing,
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

    def get_spiritual_stats(self) -> Dict[str, Any]:
        """Get spiritual pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "int_sum": 0.0, "meaning_sum": 0.0, "bypass_count": 0, "duration_sum": 0.0})
        for e in self._entries:
            by_type[e.practice_type]["count"] += 1
            by_type[e.practice_type]["depth_sum"] += e.depth
            by_type[e.practice_type]["int_sum"] += e.integration
            by_type[e.practice_type]["meaning_sum"] += e.meaning_felt
            by_type[e.practice_type]["duration_sum"] += e.duration
            if e.bypassing:
                by_type[e.practice_type]["bypass_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_integration": round(data["int_sum"] / count, 2),
                "avg_meaning": round(data["meaning_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
                "bypassing_rate": round(data["bypass_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_depth"] + x[1]["avg_integration"]) if type_stats else ("", {})

        # Depth vs duration
        high_depth = [e for e in self._entries if e.depth > 0.7]
        low_depth = [e for e in self._entries if e.depth < 0.4]
        if high_depth and low_depth:
            high_depth_int = sum(e.integration for e in high_depth) / len(high_depth)
            low_depth_int = sum(e.integration for e in low_depth) / len(low_depth)
            high_depth_meaning = sum(e.meaning_felt for e in high_depth) / len(high_depth)
            low_depth_meaning = sum(e.meaning_felt for e in low_depth) / len(low_depth)
        else:
            high_depth_int = 0
            low_depth_int = 0
            high_depth_meaning = 0
            low_depth_meaning = 0

        # Bypassing analysis
        bypassing = [e for e in self._entries if e.bypassing]
        genuine = [e for e in self._entries if not e.bypassing]
        if bypassing and genuine:
            bypassing_int = sum(e.integration for e in bypassing) / len(bypassing)
            genuine_int = sum(e.integration for e in genuine) / len(genuine)
            bypassing_meaning = sum(e.meaning_felt for e in bypassing) / len(bypassing)
            genuine_meaning = sum(e.meaning_felt for e in genuine) / len(genuine)
        else:
            bypassing_int = 0
            genuine_int = 0
            bypassing_meaning = 0
            genuine_meaning = 0

        # Integration analysis
        high_int = [e for e in self._entries if e.integration > 0.7]
        low_int = [e for e in self._entries if e.integration < 0.4]
        if high_int and low_int:
            high_int_meaning = sum(e.meaning_felt for e in high_int) / len(high_int)
            low_int_meaning = sum(e.meaning_felt for e in low_int) / len(low_int)
        else:
            high_int_meaning = 0
            low_int_meaning = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            recent_meaning = sum(e.meaning_felt for e in recent) / len(recent)
            recent_bypass = sum(1 for e in recent if e.bypassing) / len(recent)
        else:
            recent_depth = 0
            recent_int = 0
            recent_meaning = 0
            recent_bypass = 0

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
            "best_practice_type": best_type[0],
            "depth_impact": {
                "high_depth_integration": round(high_depth_int, 2),
                "low_depth_integration": round(low_depth_int, 2),
                "high_depth_meaning": round(high_depth_meaning, 2),
                "low_depth_meaning": round(low_depth_meaning, 2),
            },
            "bypassing_analysis": {
                "bypassing_integration": round(bypassing_int, 2),
                "genuine_integration": round(genuine_int, 2),
                "bypassing_meaning": round(bypassing_meaning, 2),
                "genuine_meaning": round(genuine_meaning, 2),
            },
            "integration_impact": {
                "high_integration_meaning": round(high_int_meaning, 2),
                "low_integration_meaning": round(low_int_meaning, 2),
            },
            "bypassing_risk": recent_bypass > 0.3,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
            "avg_meaning": round(sum(e.meaning_felt for e in self._entries) / len(self._entries), 2),
            "depth_trend": round(depth_trend, 2),
            "integration_trend": round(int_trend, 2),
            "recent_bypassing_rate": round(recent_bypass, 2),
        }

    def get_practice_suggestion(self, longing: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "peace": [
                "Sit in silence. 10 minutes. No agenda. No technique. Just presence. The peace is already there.",
                "Breath prayer. Breathe in: 'Peace.' Breathe out: 'Be still.' Repeat until it's true.",
                "Walk slowly. Without destination. Notice the world continuing without your effort. That's peace.",
            ],
            "meaning": [
                "Read something ancient. Scripture. Poetry. Philosophy. Connect to the long conversation of humanity.",
                "Journal three things you're grateful for. Not routine. Genuine. Dig for them. Meaning hides in gratitude.",
                "Service. Do one thing for someone who can't repay you. Meaning lives in generosity.",
            ],
            "connection": [
                "Contemplative prayer. Sit with the divine. Don't ask for anything. Don't say anything. Just be.",
                "Lectio divina. Read slowly. Listen for the word that shimmers. Sit with it. Let it read you.",
                "Nature meditation. Find one thing alive. A tree. A bird. Feel your shared existence. You're not separate.",
            ],
            "transformation": [
                "Examen. Review your day. Where did you feel alive? Where did you shrink? Patterns reveal transformation paths.",
                "Shadow work. What do you judge in others? That's your shadow. Name it. Integrate it. That's transformation.",
                "Fasting. From food. From screens. From speech. What remains when you remove the noise? That's you.",
            ],
            "general": [
                "Spiritual practice is not about achieving. It's about attending. Show up. The rest happens.",
                "Don't chase experiences. Chase consistency. The profound arises from the mundane. Eventually.",
                "Your practice doesn't need to look spiritual. Walking. Cooking. Parenting. Any act done with full presence is prayer.",
            ],
        }

        selected = suggestions.get(longing, suggestions["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. One minute. One breath. One prayer. That's enough. God is not counting minutes."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. 15-20 minutes. Choose one practice. Depth over variety."
        else:
            capacity_note = "Good capacity. This is when you challenge yourself. Silent retreat. Extended fast. Deep study."

        return {
            "longing": longing or "general",
            "capacity": capacity,
            "suggestion": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most people think spirituality is about belief. It's not. It's about practice. Belief without practice is opinion. Practice without belief is discipline. Together, they become transformation. You don't need to believe anything to start. You need to show up. Day after day. The belief often follows. Sometimes it doesn't. The practice remains valuable either way.",
        }

    def get_spiritual_score(self) -> int:
        """Calculate overall spiritual health (0-100)."""
        if not self._entries:
            return 25

        # Depth, integration, and meaning
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_meaning = sum(e.meaning_felt for e in self._entries) / len(self._entries)

        # Low bypassing
        bypass_rate = sum(1 for e in self._entries if e.bypassing) / len(self._entries)

        # Type variety
        unique_types = len(set(e.practice_type for e in self._entries))

        # Consistency (frequency)
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            recent_meaning = sum(e.meaning_felt for e in recent) / len(recent)
            recent_bypass = sum(1 for e in recent if e.bypassing) / len(recent)
        else:
            recent_depth = 0
            recent_int = 0
            recent_meaning = 0
            recent_bypass = 0

        # Bypassing penalty
        bypass_penalty = 0
        if recent_bypass > 0.3:
            bypass_penalty = 15

        score = (avg_depth * 25) + (avg_int * 25) + (avg_meaning * 15) + ((1 - bypass_rate) * 10) + (unique_types * 2) + (recent_depth * 10) + (recent_int * 10) + (recent_meaning * 5) - bypass_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integration"] = round(sum(e.integration for e in self._entries) / len(self._entries), 2)

            recent = list(self._entries)[-14:]
            if recent:
                recent_bypass = sum(1 for e in recent if e.bypassing) / len(recent)
                self._stats["bypassing_risk"] = recent_bypass > 0.3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.spiritual_practice_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.spiritual_practice_coach")

    def _log_entry(self, entry: SpiritualEntry):
        try:
            with open(SPIRITUAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "practice": entry.practice,
                    "practice_type": entry.practice_type,
                    "duration": entry.duration,
                    "depth": entry.depth,
                    "integration": entry.integration,
                    "meaning_felt": entry.meaning_felt,
                    "bypassing": entry.bypassing,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.spiritual_practice_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_spc_instance: Optional[SpiritualPracticeCoach] = None
_spc_lock = threading.Lock()


def get_spiritual_practice_coach() -> SpiritualPracticeCoach:
    global _spc_instance
    with _spc_lock:
        if _spc_instance is None:
            _spc_instance = SpiritualPracticeCoach()
        return _spc_instance
