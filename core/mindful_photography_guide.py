"""
LOVE Mindful Photography Guide — Contemplative Visual Intelligence (Modern AI Pattern)

Most people photograph to capture. This guide:

1. PRACTICE TRACKING
   - Record mindful photography sessions and their characteristics
   - Track practice types (see_first, slow_look, single_frame, light_study, detail_exploration, waiting)
   - Log attention, patience, stillness, seeing, and presence of practice

2. PATTERN ANALYSIS
   - Identify the user's practice profile (rushed, snapshot, developing, contemplative)
   - Find practice patterns that create depth vs surface
   - Detect chronic camera-first seeing and its costs

3. CONTEMPLATIVE PRACTICE BUILDING
   - Suggest practices for seeing before shooting
   - Provide frameworks for slow, intentional photography
   - Recommend practices for photographic meditation

4. DEEP SEEING CULTIVATION
   - Track the correlation between stillness and image depth
   - Alert when capturing is replacing seeing
   - Celebrate moments of genuine contemplative vision

Architecture:
- record_practice(session, type, attention, patience, stillness, seeing, presence): Log practice
- get_practice_stats(): Get practice pattern analysis
- get_practice_suggestion(capacity, context): Get suggestion
- get_practice_score(): Calculate overall practice health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "mindful_photography_guide"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRACTICE_LOG = DATA_DIR / "practices.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PracticeEntry:
    """A tracked mindful photography session."""
    entry_id: str = ""
    session: str = ""  # what session was done
    practice_type: str = ""  # see_first, slow_look, single_frame, light_study, detail_exploration, waiting
    attention: float = 0.0  # 0-1
    patience: float = 0.0  # 0-1
    stillness: float = 0.0  # 0-1
    seeing: float = 0.0  # 0-1
    presence: float = 0.0  # 0-1
    surrender: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MindfulPhotographyGuide:
    """
    Intelligent mindful photography guide with rushing detection and deep seeing cultivation.
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
            "avg_attention": 0.0,
            "avg_stillness": 0.0,
            "rushing_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_practice(self, session: str = "", practice_type: str = "", attention: float = 0.0, patience: float = 0.0, stillness: float = 0.0, seeing: float = 0.0, presence: float = 0.0, surrender: float = 0.0, notes: str = "") -> PracticeEntry:
        """Record a mindful photography session."""
        entry_id = f"mpr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PracticeEntry(
            entry_id=entry_id,
            session=session or "unspecified",
            practice_type=practice_type or "see_first",
            attention=attention,
            patience=patience,
            stillness=stillness,
            seeing=seeing,
            presence=presence,
            surrender=surrender,
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

    def get_practice_stats(self) -> Dict[str, Any]:
        """Get practice pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "attention_sum": 0.0, "stillness_sum": 0.0, "seeing_sum": 0.0})
        for e in self._entries:
            by_type[e.practice_type]["count"] += 1
            by_type[e.practice_type]["attention_sum"] += e.attention
            by_type[e.practice_type]["stillness_sum"] += e.stillness
            by_type[e.practice_type]["seeing_sum"] += e.seeing

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_attention": round(data["attention_sum"] / count, 2),
                "avg_stillness": round(data["stillness_sum"] / count, 2),
                "avg_seeing": round(data["seeing_sum"] / count, 2),
            }

        # Attention analysis
        high_att = [e for e in self._entries if e.attention > 0.7]
        low_att = [e for e in self._entries if e.attention < 0.4]
        if high_att and low_att:
            high_att_see = sum(e.seeing for e in high_att) / len(high_att)
            low_att_see = sum(e.seeing for e in low_att) / len(low_att)
            high_att_pres = sum(e.presence for e in high_att) / len(high_att)
            low_att_pres = sum(e.presence for e in low_att) / len(low_att)
        else:
            high_att_see = 0
            low_att_see = 0
            high_att_pres = 0
            low_att_pres = 0

        # Stillness analysis
        high_still = [e for e in self._entries if e.stillness > 0.7]
        low_still = [e for e in self._entries if e.stillness < 0.4]
        if high_still and low_still:
            high_still_see = sum(e.seeing for e in high_still) / len(high_still)
            low_still_see = sum(e.seeing for e in low_still) / len(low_still)
        else:
            high_still_see = 0
            low_still_see = 0

        # Rushing risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_att = sum(e.attention for e in recent) / len(recent)
            recent_still = sum(e.stillness for e in recent) / len(recent)
            rushing_risk = recent_att < 0.3 and recent_still < 0.3
        else:
            rushing_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "attention_impact": {
                "high_attention_seeing": round(high_att_see, 2),
                "low_attention_seeing": round(low_att_see, 2),
                "high_attention_presence": round(high_att_pres, 2),
                "low_attention_presence": round(low_att_pres, 2),
            },
            "stillness_effect": {
                "high_stillness_seeing": round(high_still_see, 2),
                "low_stillness_seeing": round(low_still_see, 2),
            },
            "rushing_risk": rushing_risk,
            "avg_attention": round(sum(e.attention for e in self._entries) / len(self._entries), 2),
            "avg_stillness": round(sum(e.stillness for e in self._entries) / len(self._entries), 2),
        }

    def get_practice_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get practice suggestion."""
        suggestions = [
            "The camera is a barrier. Put it down. Look. Really look. Not for a photo. For the sake of seeing. The light on the wall. The shadow on the floor. The pattern in the leaf. See first. Photograph second. Or not at all.",
            "Take one frame. Not ten. Not fifty. One. Make it count. The constraint creates attention. The limit creates care. The single frame is a meditation. And the meditation is the practice.",
            "Wait. For the light. For the moment. For the feeling. Photography is not hunting. It's receiving. The image comes to you. When you're ready. When you're still. When you're present. Wait.",
            "Study light. For an hour. Without taking a photo. Just watch. How it moves. How it changes. How it falls. How it rises. Understand light. And you'll understand photography. And you'll understand seeing.",
            "Explore one detail. The bark of a tree. The wrinkles of a hand. The texture of fabric. The reflection in water. One detail. Deeply. Not broadly. The detail contains the universe. If you look deeply enough.",
            "Photograph without looking at the screen. Trust your eye. Trust your instinct. The screen is a distraction. It's a judge. It's a corrector. It's a meddler. Your eye is enough. Trust it.",
            "Move slowly. Not quickly. The hurried photographer sees nothing. The slow photographer sees everything. Because they're present. Because they're not thinking about the next shot. Because they're in this shot. Fully.",
            "Let go of the result. The photo doesn't matter. The seeing matters. The being there matters. The attention matters. The practice matters. The image is a byproduct. A trace. A memory. Not the goal.",
            "Return to the same place. Again and again. Same time. Different light. Same subject. Different mood. The place teaches you. The repetition deepens you. The familiar becomes infinite. If you look.",
            "The person who practices mindful photography is not a photographer. They're a meditator. Who uses a camera. The camera is the breath. The viewfinder is the cushion. The image is the insight. And the practice is the path."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One deep look. One slow breath. One frame waited for. One moment truly seen. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A single-frame practice. A light study. A detail explored. A session without reviewing. Medium contemplation."
        else:
            capacity_note = "Good capacity. Deep mindful photography work. A systematic practice of seeing before shooting, stillness before capture, and presence before result. You have the strength to see."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Mindful photography is not a technique. It's a way of being. Most people pick up a camera and start shooting. They hunt for images. They chase moments. They accumulate photographs. And they miss the moment entirely. The work of mindful photography coaching is about understanding that the camera is not a tool for capture. It's a tool for attention. For presence. For stillness. And for seeing. It's about putting the camera down. About looking without photographing. About waiting. About patience. About understanding that the best photograph might be the one you don't take. Because you were too busy seeing. And that the person who learns to see without a camera will take better photographs than the person who never stops shooting."
        }

    def get_practice_score(self) -> int:
        """Calculate overall practice health (0-100)."""
        if not self._entries:
            return 25

        avg_att = sum(e.attention for e in self._entries) / len(self._entries)
        avg_pat = sum(e.patience for e in self._entries) / len(self._entries)
        avg_still = sum(e.stillness for e in self._entries) / len(self._entries)
        avg_see = sum(e.seeing for e in self._entries) / len(self._entries)
        avg_pres = sum(e.presence for e in self._entries) / len(self._entries)
        avg_sur = sum(e.surrender for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_att = sum(e.attention for e in recent) / len(recent)
            recent_still = sum(e.stillness for e in recent) / len(recent)
        else:
            recent_att = 0
            recent_still = 0

        # Rushing penalty
        rush_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_att_30 = sum(e.attention for e in last_30) / len(last_30)
            recent_still_30 = sum(e.stillness for e in last_30) / len(last_30)
            if recent_att_30 < 0.3 and recent_still_30 < 0.3:
                rush_penalty = 15

        # Type variety
        unique_types = len(set(e.practice_type for e in self._entries))

        score = (avg_att * 25) + (avg_pat * 10) + (avg_still * 20) + (avg_see * 15) + (avg_pres * 10) + (avg_sur * 10) + (recent_att * 5) + (recent_still * 5) + (unique_types * 2) - rush_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_attention"] = round(sum(e.attention for e in self._entries) / len(self._entries), 2)
            self._stats["avg_stillness"] = round(sum(e.stillness for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_att = sum(e.attention for e in recent) / len(recent)
                recent_still = sum(e.stillness for e in recent) / len(recent)
                self._stats["rushing_risk"] = recent_att < 0.3 and recent_still < 0.3
            else:
                self._stats["rushing_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mindful_photography_guide")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mindful_photography_guide")

    def _log_entry(self, entry: PracticeEntry):
        try:
            with open(PRACTICE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "session": entry.session,
                    "practice_type": entry.practice_type,
                    "attention": entry.attention,
                    "stillness": entry.stillness,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mindful_photography_guide")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mpg_instance: Optional[MindfulPhotographyGuide] = None
_mpg_lock = threading.Lock()


def get_mindful_photography_guide() -> MindfulPhotographyGuide:
    global _mpg_instance
    with _mpg_lock:
        if _mpg_instance is None:
            _mpg_instance = MindfulPhotographyGuide()
        return _mpg_instance
