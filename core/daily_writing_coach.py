"""
LOVE Daily Writing Coach — Writing Practice Intelligence (Modern AI Pattern)

Most people want to write but don't. This coach:

1. WRITING TRACKING
   - Record writing sessions and their characteristics
   - Track writing types (journal, essay, fiction, poetry, professional, reflection)
   - Log flow, clarity, courage, consistency, and joy of writing

2. PATTERN ANALYSIS
   - Identify the user's writing profile (avoidant, sporadic, developing, fluent)
   - Find writing patterns that create momentum vs resistance
   - Detect chronic procrastination and its costs

3. PRACTICE BUILDING
   - Suggest practices for building a daily writing habit
   - Provide frameworks for overcoming writer's block
   - Recommend practices for finding voice and clarity

4. WRITING MASTERY CULTIVATION
   - Track the correlation between daily practice and writing quality
   - Alert when perfectionism is replacing practice
   - Celebrate moments of genuine writing breakthrough

Architecture:
- record_writing(piece, type, flow, clarity, courage, consistency, joy): Log writing
- get_writing_stats(): Get writing pattern analysis
- get_writing_suggestion(capacity, context): Get suggestion
- get_writing_score(): Calculate overall writing health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "daily_writing_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WRITING_LOG = DATA_DIR / "writings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WritingEntry:
    """A tracked writing session."""
    entry_id: str = ""
    piece: str = ""  # what was written
    writing_type: str = ""  # journal, essay, fiction, poetry, professional, reflection
    flow: float = 0.0  # 0-1
    clarity: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    consistency: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    voice: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DailyWritingCoach:
    """
    Intelligent daily writing coach with procrastination detection and writing mastery cultivation.
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
            "avg_flow": 0.0,
            "avg_joy": 0.0,
            "procrastination_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_writing(self, piece: str = "", writing_type: str = "", flow: float = 0.0, clarity: float = 0.0, courage: float = 0.0, consistency: float = 0.0, joy: float = 0.0, voice: float = 0.0, notes: str = "") -> WritingEntry:
        """Record a writing session."""
        entry_id = f"wri_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = WritingEntry(
            entry_id=entry_id,
            piece=piece or "unspecified",
            writing_type=writing_type or "journal",
            flow=flow,
            clarity=clarity,
            courage=courage,
            consistency=consistency,
            joy=joy,
            voice=voice,
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

    def get_writing_stats(self) -> Dict[str, Any]:
        """Get writing pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "flow_sum": 0.0, "clarity_sum": 0.0, "joy_sum": 0.0})
        for e in self._entries:
            by_type[e.writing_type]["count"] += 1
            by_type[e.writing_type]["flow_sum"] += e.flow
            by_type[e.writing_type]["clarity_sum"] += e.clarity
            by_type[e.writing_type]["joy_sum"] += e.joy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_flow": round(data["flow_sum"] / count, 2),
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Flow analysis
        high_flow = [e for e in self._entries if e.flow > 0.7]
        low_flow = [e for e in self._entries if e.flow < 0.4]
        if high_flow and low_flow:
            high_flow_clar = sum(e.clarity for e in high_flow) / len(high_flow)
            low_flow_clar = sum(e.clarity for e in low_flow) / len(low_flow)
            high_flow_joy = sum(e.joy for e in high_flow) / len(high_flow)
            low_flow_joy = sum(e.joy for e in low_flow) / len(low_flow)
        else:
            high_flow_clar = 0
            low_flow_clar = 0
            high_flow_joy = 0
            low_flow_joy = 0

        # Courage analysis
        high_cour = [e for e in self._entries if e.courage > 0.7]
        low_cour = [e for e in self._entries if e.courage < 0.4]
        if high_cour and low_cour:
            high_cour_flow = sum(e.flow for e in high_cour) / len(high_cour)
            low_cour_flow = sum(e.flow for e in low_cour) / len(low_cour)
        else:
            high_cour_flow = 0
            low_cour_flow = 0

        # Procrastination risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_flow = sum(e.flow for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
            procrastination_risk = recent_flow < 0.3 and recent_joy < 0.3
        else:
            procrastination_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "flow_impact": {
                "high_flow_clarity": round(high_flow_clar, 2),
                "low_flow_clarity": round(low_flow_clar, 2),
                "high_flow_joy": round(high_flow_joy, 2),
                "low_flow_joy": round(low_flow_joy, 2),
            },
            "courage_effect": {
                "high_courage_flow": round(high_cour_flow, 2),
                "low_courage_flow": round(low_cour_flow, 2),
            },
            "procrastination_risk": procrastination_risk,
            "avg_flow": round(sum(e.flow for e in self._entries) / len(self._entries), 2),
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
        }

    def get_writing_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get writing suggestion."""
        suggestions = [
            "Most people want to write but don't. They have ideas. They have stories. They have thoughts. And they sit down to write and nothing comes. Or what comes feels wrong. Or they write one sentence and delete it. And they conclude they can't write. The truth is simpler: they haven't practiced enough. Writing is a muscle. And muscles atrophy without use.",
            "Write badly. On purpose. Deliberately. Write the worst sentence you can imagine. Write clichés. Write nonsense. Write drivel. The point is not to produce good work. The point is to produce. Because the person who writes badly writes. And the person who writes eventually writes well.",
            "Lower the bar. Not the standards. The entry requirements. You don't need an hour. You don't need inspiration. You don't need a perfect idea. You need ten minutes. A blank page. And the willingness to put words on it. The person who writes for ten minutes every day writes more than the person who waits for the perfect hour that never comes.",
            "Write what you know. Not what you think you should know. Not what sounds impressive. What you actually know. Your experiences. Your observations. Your opinions. Your questions. Your fears. Your joys. Authenticity is the only requirement. Everything else is optional.",
            "Separate writing from editing. They are different activities. Different brain states. Different skills. Write first. Edit later. Never at the same time. The person who tries to write and edit simultaneously writes nothing. Because editing is judgment. And judgment silences the voice.",
            "Find your time. Not someone else's. Morning. Night. Lunch break. Commute. The time doesn't matter. The consistency does. The same time. Every day. The brain learns to write at that time. It prepares. It expects. It produces. Routine is the writer's best friend.",
            "Read what you want to write. Not just anything. The genre. The style. The voice. The form. Read the best. Read the worst. Read everything in between. Reading is the writer's training. It teaches rhythm. It teaches structure. It teaches what works and what doesn't.",
            "Embrace the shitty first draft. Every great piece of writing started as a mess. Every author writes garbage. The difference between published authors and unpublished writers is not talent. It's revision. It's the willingness to create garbage and then sculpt it into art.",
            "Write for one person. Not the world. Not your audience. Not your critics. One person. Someone you know. Someone you love. Someone you want to reach. Writing for one person is intimate. It's focused. It's powerful. And it's much easier than writing for everyone.",
            "The person who writes daily is not a special person. They're a person who made a choice. A small choice. Repeated daily. The choice to sit down. To open the page. To put words on it. To do it again tomorrow. That's it. That's the secret. There is no other secret."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One sentence. One paragraph. One ten-minute session. One bad draft. One small choice. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A daily practice. A lowered bar. A separated edit. A found time. A small streak. Medium momentum."
        else:
            capacity_note = "Good capacity. Deep writing work. A systematic practice of daily creation, courage, voice development, and revision. You have the strength to write anything."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Daily writing coaching is not about becoming a famous author. It's about becoming a person who writes. Most people want to write but don't. They have ideas, stories, and thoughts that never make it to the page. They wait for inspiration, time, and permission that never come. The work of daily writing coaching is about understanding that writing is a practice, not a gift. That it improves with use. That the only way to write well is to write badly first. That the only way to find your voice is to use it. And that the person who writes daily - however imperfectly - is the person who eventually writes powerfully."
        }

    def get_writing_score(self) -> int:
        """Calculate overall writing health (0-100)."""
        if not self._entries:
            return 25

        avg_flow = sum(e.flow for e in self._entries) / len(self._entries)
        avg_clar = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_cour = sum(e.courage for e in self._entries) / len(self._entries)
        avg_cons = sum(e.consistency for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_voice = sum(e.voice for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_flow = sum(e.flow for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
        else:
            recent_flow = 0
            recent_joy = 0

        # Procrastination penalty
        proc_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_flow_30 = sum(e.flow for e in last_30) / len(last_30)
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            if recent_flow_30 < 0.3 and recent_joy_30 < 0.3:
                proc_penalty = 15

        # Type variety
        unique_types = len(set(e.writing_type for e in self._entries))

        score = (avg_flow * 25) + (avg_clar * 10) + (avg_cour * 15) + (avg_cons * 15) + (avg_joy * 15) + (avg_voice * 10) + (recent_flow * 5) + (recent_joy * 5) + (unique_types * 2) - proc_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_flow"] = round(sum(e.flow for e in self._entries) / len(self._entries), 2)
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_flow = sum(e.flow for e in recent) / len(recent)
                recent_joy = sum(e.joy for e in recent) / len(recent)
                self._stats["procrastination_risk"] = recent_flow < 0.3 and recent_joy < 0.3
            else:
                self._stats["procrastination_risk"] = False

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

    def _log_entry(self, entry: WritingEntry):
        try:
            with open(WRITING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "piece": entry.piece,
                    "writing_type": entry.writing_type,
                    "flow": entry.flow,
                    "joy": entry.joy,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dwc_instance: Optional[DailyWritingCoach] = None
_dwc_lock = threading.Lock()


def get_daily_writing_coach() -> DailyWritingCoach:
    global _dwc_instance
    with _dwc_lock:
        if _dwc_instance is None:
            _dwc_instance = DailyWritingCoach()
        return _dwc_instance
