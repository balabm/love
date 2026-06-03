"""
LOVE Contemplation Keeper — Depth Intelligence (Modern AI Pattern)

Most thinking is reactive. Contemplation is generative. This keeper:

1. CONTEMPLATION TRACKING
   - Record contemplative sessions and their characteristics
   - Track contemplation types (meditation, lectio, journaling, walking, artistic, dialogue)
   - Log insight and integration outcomes

2. PATTERN ANALYSIS
   - Identify the user's contemplation profile (distracted, dutiful, receptive, deep)
   - Find conditions that reliably produce insight
   - Detect avoidance disguised as contemplation

3. CONTEMPLATION BUILDING
   - Suggest contemplative practices matched to current question and capacity
   - Provide depth and duration frameworks
   - Recommendation integration practices

4. DEPTH CULTIVATION
   - Track the correlation between contemplation and life clarity
   - Alert when sessions are becoming shallow or performative
   - Celebrate moments of genuine insight

Architecture:
- record_session(practice, type, depth, insight, integration): Log session
- get_contemplation_stats(): Get contemplation pattern analysis
- get_contemplation_practice(question, capacity, context): Get practice
- get_contemplation_score(): Calculate overall contemplation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "contemplation_keeper"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONTEMPLATION_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ContemplationEntry:
    """A tracked contemplation entry."""
    entry_id: str = ""
    practice: str = ""  # what was done
    cont_type: str = ""  # meditation, lectio, journaling, walking, artistic, dialogue
    duration: float = 0.0  # minutes
    depth: float = 0.5  # 0-1
    insight: float = 0.0  # 0-1
    integration: float = 0.5  # 0-1
    question: str = ""  # what was contemplated
    performative: bool = False  # was it for show
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ContemplationKeeper:
    """
    Intelligent contemplation keeper with insight tracking and performative detection.
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
            "avg_insight": 0.0,
            "performative_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, practice: str = "", cont_type: str = "", duration: float = 0.0, depth: float = 0.5, insight: float = 0.0, integration: float = 0.5, question: str = "", performative: bool = False, notes: str = "") -> ContemplationEntry:
        """Record a contemplation entry."""
        entry_id = f"cont_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ContemplationEntry(
            entry_id=entry_id,
            practice=practice or "unspecified",
            cont_type=cont_type or "meditation",
            duration=duration,
            depth=depth,
            insight=insight,
            integration=integration,
            question=question,
            performative=performative,
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

    def get_contemplation_stats(self) -> Dict[str, Any]:
        """Get contemplation pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "insight_sum": 0.0, "int_sum": 0.0, "duration_sum": 0.0, "perf_count": 0})
        for e in self._entries:
            by_type[e.cont_type]["count"] += 1
            by_type[e.cont_type]["depth_sum"] += e.depth
            by_type[e.cont_type]["insight_sum"] += e.insight
            by_type[e.cont_type]["int_sum"] += e.integration
            by_type[e.cont_type]["duration_sum"] += e.duration
            if e.performative:
                by_type[e.cont_type]["perf_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_insight": round(data["insight_sum"] / count, 2),
                "avg_integration": round(data["int_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
                "performative_rate": round(data["perf_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_insight"] + x[1]["avg_integration"]) if type_stats else ("", {})

        # Duration analysis
        long_dur = [e for e in self._entries if e.duration > 45]
        short_dur = [e for e in self._entries if e.duration < 10]
        if long_dur and short_dur:
            long_insight = sum(e.insight for e in long_dur) / len(long_dur)
            short_insight = sum(e.insight for e in short_dur) / len(short_dur)
            long_depth = sum(e.depth for e in long_dur) / len(long_dur)
            short_depth = sum(e.depth for e in short_dur) / len(short_dur)
        else:
            long_insight = 0
            short_insight = 0
            long_depth = 0
            short_depth = 0

        # Depth vs insight
        high_depth = [e for e in self._entries if e.depth > 0.7]
        low_depth = [e for e in self._entries if e.depth < 0.4]
        if high_depth and low_depth:
            high_depth_insight = sum(e.insight for e in high_depth) / len(high_depth)
            low_depth_insight = sum(e.insight for e in low_depth) / len(low_depth)
            high_depth_int = sum(e.integration for e in high_depth) / len(high_depth)
            low_depth_int = sum(e.integration for e in low_depth) / len(low_depth)
        else:
            high_depth_insight = 0
            low_depth_insight = 0
            high_depth_int = 0
            low_depth_int = 0

        # Performative vs genuine
        performative = [e for e in self._entries if e.performative]
        genuine = [e for e in self._entries if not e.performative]
        if performative and genuine:
            perf_insight = sum(e.insight for e in performative) / len(performative)
            genuine_insight = sum(e.insight for e in genuine) / len(genuine)
            perf_depth = sum(e.depth for e in performative) / len(performative)
            genuine_depth = sum(e.depth for e in genuine) / len(genuine)
        else:
            perf_insight = 0
            genuine_insight = 0
            perf_depth = 0
            genuine_depth = 0

        # Integration analysis
        high_int = [e for e in self._entries if e.integration > 0.7]
        low_int = [e for e in self._entries if e.integration < 0.4]
        if high_int and low_int:
            high_int_insight = sum(e.insight for e in high_int) / len(high_int)
            low_int_insight = sum(e.insight for e in low_int) / len(low_int)
        else:
            high_int_insight = 0
            low_int_insight = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_insight = sum(e.insight for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            recent_perf = sum(1 for e in recent if e.performative) / len(recent)
        else:
            recent_depth = 0
            recent_insight = 0
            recent_int = 0
            recent_perf = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_depth = sum(e.depth for e in older) / len(older)
            older_insight = sum(e.insight for e in older) / len(older)
            depth_trend = recent_depth - older_depth
            insight_trend = recent_insight - older_insight
        else:
            depth_trend = 0
            insight_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "duration_impact": {
                "long_duration_insight": round(long_insight, 2),
                "short_duration_insight": round(short_insight, 2),
                "long_duration_depth": round(long_depth, 2),
                "short_duration_depth": round(short_depth, 2),
            },
            "depth_impact": {
                "high_depth_insight": round(high_depth_insight, 2),
                "low_depth_insight": round(low_depth_insight, 2),
                "high_depth_integration": round(high_depth_int, 2),
                "low_depth_integration": round(low_depth_int, 2),
            },
            "performative_analysis": {
                "performative_insight": round(perf_insight, 2),
                "genuine_insight": round(genuine_insight, 2),
                "performative_depth": round(perf_depth, 2),
                "genuine_depth": round(genuine_depth, 2),
            },
            "integration_impact": {
                "high_integration_insight": round(high_int_insight, 2),
                "low_integration_insight": round(low_int_insight, 2),
            },
            "performative_risk": recent_perf > 0.3,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_insight": round(sum(e.insight for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
            "depth_trend": round(depth_trend, 2),
            "insight_trend": round(insight_trend, 2),
            "recent_performative_rate": round(recent_perf, 2),
        }

    def get_contemplation_practice(self, question: str = "", capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "grief": [
                "Sit with the grief. Don't fix it. Don't explain it. Just be with it. Grief is love with nowhere to go. Be the container.",
                "Write a letter to what you've lost. Everything you didn't say. Then read it aloud. Let it be heard.",
                "Walk slowly. Let your body process what your mind can't. Movement metabolizes emotion.",
            ],
            "decision": [
                "Write the decision on paper. Sleep on it. See how your body feels in the morning. The body knows before the mind.",
                "Imagine choosing A. Feel it for 24 hours. Then imagine choosing B. Compare. Your future self is whispering.",
                "Ask: 'What would I do if I weren't afraid?' Then ask: 'What would I do if I were wise?' The answers are often different.",
            ],
            "creativity": [
                "Morning pages. Three pages. Longhand. No editing. No judgment. Let the unconscious surface.",
                "Sit with a blank page. Set a timer. 20 minutes. Don't write. Just wait. Creativity arrives when you're ready.",
                "Change your environment. Coffee shop. Park. Library. New context disrupts old patterns. Insights need disruption.",
            ],
            "relationship": [
                "Write their story from their perspective. Not to excuse. To understand. Understanding precedes resolution.",
                "What do you need to say that you haven't? Write it. Don't send it. Yet. Contemplation prepares the ground.",
                "Sit with the discomfort. The relationship problem you avoid is the teacher you need. Listen.",
            ],
            "existential": [
                "Contemplate death. Your own. Seriously. What would you do if you had one year? One month? One day? The answers reveal your priorities.",
                "Read a philosopher. Marcus Aurelius. Simone de Beauvoir. Alan Watts. Others have wrestled with this. Learn from their struggle.",
                "Look at the stars. Feel small. That's not depressing. That's liberating. Your problems shrink in cosmic perspective.",
            ],
            "general": [
                "Contemplation is not problem-solving. It's problem-sitting. Stay with the question. The answer arrives when you stop demanding it.",
                "Silence is the prerequisite. Noise prevents depth. Find silence. Outer and inner. Then begin.",
                "Write what arises. Don't judge. Don't edit. The page is a mirror. It shows you what you think.",
            ],
        }

        selected = practices.get(context, practices["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. 5 minutes. One question. One sentence. That's contemplation. It doesn't require hours."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. 20-30 minutes. One question. Stay with it. Push past the first answer."
        else:
            capacity_note = "Good capacity. Extended contemplation. Hours. Retreat. Go deep. The best insights come after the mind exhausts its usual answers."

        return {
            "question": question or "open",
            "capacity": capacity,
            "context": context or "general",
            "practice": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most people think contemplation is passive. It's not. It's the most active thing you can do. It requires holding a question without grasping for an answer. It demands sitting with discomfort without fleeing. It asks you to be still in a world that rewards motion. Contemplation is not laziness. It's the hard work of thinking. Real thinking. Not reactive. Not performative. Generative.",
        }

    def get_contemplation_score(self) -> int:
        """Calculate overall contemplation health (0-100)."""
        if not self._entries:
            return 25

        # Depth, insight, and integration
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_insight = sum(e.insight for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)

        # Low performative
        perf_rate = sum(1 for e in self._entries if e.performative) / len(self._entries)

        # Duration (longer tends to be deeper)
        avg_duration = sum(e.duration for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.cont_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_insight = sum(e.insight for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            recent_perf = sum(1 for e in recent if e.performative) / len(recent)
        else:
            recent_depth = 0
            recent_insight = 0
            recent_int = 0
            recent_perf = 0

        # Performative penalty
        perf_penalty = 0
        if recent_perf > 0.3:
            perf_penalty = 15

        score = (avg_depth * 20) + (avg_insight * 25) + (avg_int * 20) + ((1 - perf_rate) * 10) + (avg_duration / 5) + (unique_types * 2) + (recent_depth * 10) + (recent_insight * 10) + (recent_int * 10) - perf_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_insight"] = round(sum(e.insight for e in self._entries) / len(self._entries), 2)

            recent = list(self._entries)[-14:]
            if recent:
                recent_perf = sum(1 for e in recent if e.performative) / len(recent)
                self._stats["performative_risk"] = recent_perf > 0.3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.contemplation_keeper")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.contemplation_keeper")

    def _log_entry(self, entry: ContemplationEntry):
        try:
            with open(CONTEMPLATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "practice": entry.practice,
                    "cont_type": entry.cont_type,
                    "duration": entry.duration,
                    "depth": entry.depth,
                    "insight": entry.insight,
                    "integration": entry.integration,
                    "question": entry.question,
                    "performative": entry.performative,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.contemplation_keeper")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ck_instance: Optional[ContemplationKeeper] = None
_ck_lock = threading.Lock()


def get_contemplation_keeper() -> ContemplationKeeper:
    global _ck_instance
    with _ck_lock:
        if _ck_instance is None:
            _ck_instance = ContemplationKeeper()
        return _ck_instance
