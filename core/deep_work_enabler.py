"""
LOVE Deep Work Enabler — Cognitive Excellence Intelligence (Modern AI Pattern)

Most deep work is interrupted by shallow demands. This enabler:

1. DEEP WORK TRACKING
   - Record deep work sessions and their characteristics
   - Track depth indicators (flow, complexity, output quality)
   - Log interruptions and their sources

2. PATTERN ANALYSIS
   - Identify the user's deep work profile (morning, night, sprint, marathon)
   - Find optimal deep work conditions (time, place, preparation)
   - Detect deep work debt (accumulated shallow work)

3. DEEP WORK DESIGN
   - Suggest session structures matched to task type
   - Provide pre-session rituals and environment setup
   - Recommend post-session integration practices

4. PROTECTION
   - Alert when deep work time is being eroded
   - Suggest boundary-setting for deep work blocks
   - Track the correlation between deep work and meaningful output

Architecture:
- record_session(task, duration, depth, interruptions): Log session
- get_deep_work_stats(): Get deep work pattern analysis
- get_session_design(task_type, available_time): Get design
- get_deep_work_score(): Calculate overall deep work health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "deep_work_enabler"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class DeepWorkSession:
    """A tracked deep work session."""
    session_id: str = ""
    task: str = ""
    task_type: str = ""  # writing, coding, analysis, design, research, creative
    duration_minutes: float = 0.0
    depth: float = 0.5  # 0-1, how deep
    output_quality: float = 0.5  # 0-1
    flow_score: float = 0.0  # 0-1
    interruptions: int = 0
    interruption_sources: List[str] = field(default_factory=list)
    preparation_time: float = 0.0
    recovery_time: float = 0.0
    time_of_day: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DeepWorkEnabler:
    """
    Intelligent deep work enabler with session design and interruption protection.
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
        self._sessions: deque = deque(maxlen=200)
        self._stats = {
            "total_sessions": 0,
            "avg_depth": 0.0,
            "avg_interruptions": 0.0,
            "best_time": "",
            "best_task_type": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, task: str = "", task_type: str = "", duration: float = 0, depth: float = 0.5, output_quality: float = 0.5, flow_score: float = 0.0, interruptions: int = 0, interruption_sources: Optional[List[str]] = None, prep_time: float = 0, recovery_time: float = 0, time_of_day: str = "", notes: str = "") -> DeepWorkSession:
        """Record a deep work session."""
        session_id = f"deep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = DeepWorkSession(
            session_id=session_id,
            task=task or "unspecified",
            task_type=task_type or "general",
            duration_minutes=duration,
            depth=depth,
            output_quality=output_quality,
            flow_score=flow_score,
            interruptions=interruptions,
            interruption_sources=interruption_sources or [],
            preparation_time=prep_time,
            recovery_time=recovery_time,
            time_of_day=time_of_day or datetime.now().strftime("%H:%M"),
            notes=notes,
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_session(session)

        return session

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_deep_work_stats(self) -> Dict[str, Any]:
        """Get deep work pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Task type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "output_sum": 0.0, "flow_sum": 0.0, "interruption_sum": 0})
        for s in self._sessions:
            by_type[s.task_type]["count"] += 1
            by_type[s.task_type]["depth_sum"] += s.depth
            by_type[s.task_type]["output_sum"] += s.output_quality
            by_type[s.task_type]["flow_sum"] += s.flow_score
            by_type[s.task_type]["interruption_sum"] += s.interruptions

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_output": round(data["output_sum"] / count, 2),
                "avg_flow": round(data["flow_sum"] / count, 2),
                "avg_interruptions": round(data["interruption_sum"] / count, 1),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_depth"] * x[1]["avg_output"]) if type_stats else ("", {})

        # Time of day analysis
        by_hour = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "output_sum": 0.0})
        for s in self._sessions:
            hour = s.time_of_day[:2] if s.time_of_day else "00"
            by_hour[hour]["count"] += 1
            by_hour[hour]["depth_sum"] += s.depth
            by_hour[hour]["output_sum"] += s.output_quality

        hour_stats = {}
        for h, data in by_hour.items():
            count = data["count"]
            if count >= 2:
                hour_stats[h] = {
                    "count": count,
                    "avg_depth": round(data["depth_sum"] / count, 2),
                    "avg_output": round(data["output_sum"] / count, 2),
                }

        best_time = max(hour_stats.items(), key=lambda x: x[1]["avg_depth"] * x[1]["avg_output"]) if hour_stats else ("", {})

        # Interruption analysis
        by_source = defaultdict(int)
        for s in self._sessions:
            for src in s.interruption_sources:
                by_source[src] += 1

        # Duration analysis
        short = [s for s in self._sessions if s.duration_minutes <= 60]
        medium = [s for s in self._sessions if 60 < s.duration_minutes <= 120]
        long_sessions = [s for s in self._sessions if s.duration_minutes > 120]

        duration_stats = {}
        if short:
            duration_stats["short"] = {
                "count": len(short),
                "avg_depth": round(sum(s.depth for s in short) / len(short), 2),
            }
        if medium:
            duration_stats["medium"] = {
                "count": len(medium),
                "avg_depth": round(sum(s.depth for s in medium) / len(medium), 2),
            }
        if long_sessions:
            duration_stats["long"] = {
                "count": len(long_sessions),
                "avg_depth": round(sum(s.depth for s in long_sessions) / len(long_sessions), 2),
            }

        # Preparation effectiveness
        with_prep = [s for s in self._sessions if s.preparation_time > 0]
        without_prep = [s for s in self._sessions if s.preparation_time == 0]
        if with_prep and without_prep:
            prep_effect = (sum(s.depth for s in with_prep) / len(with_prep)) - (sum(s.depth for s in without_prep) / len(without_prep))
        else:
            prep_effect = 0

        return {
            "total_sessions": len(self._sessions),
            "type_stats": type_stats,
            "best_task_type": best_type[0],
            "hour_stats": hour_stats,
            "best_time": best_time[0],
            "interruption_sources": dict(by_source),
            "duration_stats": duration_stats,
            "prep_effectiveness": round(prep_effect, 2),
            "avg_depth": round(sum(s.depth for s in self._sessions) / len(self._sessions), 2),
            "avg_output": round(sum(s.output_quality for s in self._sessions) / len(self._sessions), 2),
            "avg_interruptions": round(sum(s.interruptions for s in self._sessions) / len(self._sessions), 1),
        }

    def get_session_design(self, task_type: str = "", available_time: float = 60, energy_level: float = 0.5) -> Dict[str, Any]:
        """Get design."""
        structures = {
            "writing": [
                "5 min: Brain dump everything you know about the topic",
                "10 min: Outline the structure. Don't write yet.",
                "Main block: Write the messiest first draft possible.",
                "5 min: Walk away. No editing.",
                "10 min: Edit one section. Just one.",
            ],
            "coding": [
                "5 min: Write down the goal and one test case",
                "10 min: Pseudocode the approach. No syntax.",
                "Main block: Code with frequent commits. Every 15 min.",
                "5 min: Run tests. Fix one bug if needed.",
                "10 min: Refactor one function. Just one.",
            ],
            "analysis": [
                "5 min: Define the question precisely",
                "10 min: Gather data sources. Don't analyze yet.",
                "Main block: Analyze with note-taking. Question every assumption.",
                "5 min: Summarize findings in one sentence",
                "10 min: Create one visualization or summary",
            ],
            "design": [
                "5 min: Define constraints and success criteria",
                "10 min: Sketch 3 radically different approaches",
                "Main block: Develop the strongest approach. Don't refine yet.",
                "5 min: Get feedback from one person",
                "10 min: Refine based on feedback",
            ],
            "creative": [
                "5 min: Set a ridiculous constraint (one color, 100 words)",
                "10 min: Generate 10 bad ideas. Quantity over quality.",
                "Main block: Develop the most interesting bad idea",
                "5 min: Step back. Look at it upside down.",
                "10 min: Add one unexpected element",
            ],
            "research": [
                "5 min: Define the research question narrowly",
                "10 min: Find 3 key sources. Stop there.",
                "Main block: Read with a question in mind. Take notes.",
                "5 min: Synthesize what you learned",
                "10 min: Write one paragraph explaining it to a child",
            ],
        }

        base = structures.get(task_type, structures["writing"])

        if energy_level < 0.3:
            session_length = min(available_time, 45)
            energy_note = "Low energy. Short, focused burst. Quality over duration."
        elif energy_level < 0.6:
            session_length = min(available_time, 90)
            energy_note = "Moderate energy. Standard deep work block."
        else:
            session_length = available_time
            energy_note = "High energy. This is your peak window. Use it fully."

        # Scale structure to available time
        main_block = session_length - 30  # 5 + 10 + 5 + 10 = 30 for other phases
        if main_block < 20:
            structure = [base[0], base[2]]  # Just prep and main
        else:
            structure = base

        return {
            "task_type": task_type or "general",
            "available_time": available_time,
            "session_length": session_length,
            "energy_level": energy_level,
            "energy_note": energy_note,
            "structure": structure,
            "preparation": [
                "Clear desk. Close all non-essential apps.",
                "Put phone in another room. Set Do Not Disturb.",
                "Have water and snacks within reach.",
                "Set a visible timer. Commit to the full block.",
            ],
            "protection": "If interrupted, write down where you were. Return in 2 minutes or finish the interruption and restart.",
        }

    def get_deep_work_score(self) -> int:
        """Calculate overall deep work health (0-100)."""
        if not self._sessions:
            return 35

        # Average depth
        avg_depth = sum(s.depth for s in self._sessions) / len(self._sessions)

        # Low interruptions
        avg_interruptions = sum(s.interruptions for s in self._sessions) / len(self._sessions)

        # Output quality
        avg_output = sum(s.output_quality for s in self._sessions) / len(self._sessions)

        # Flow
        avg_flow = sum(s.flow_score for s in self._sessions) / len(self._sessions)

        # Recent trend
        recent = list(self._sessions)[-10:]
        recent_depth = sum(s.depth for s in recent) / len(recent)
        older = list(self._sessions)[:-10] if len(self._sessions) > 10 else []
        if older:
            older_depth = sum(s.depth for s in older) / len(older)
            trend = recent_depth - older_depth
        else:
            trend = 0

        # Preparation use
        prep_sessions = [s for s in self._sessions if s.preparation_time > 0]
        prep_rate = len(prep_sessions) / len(self._sessions)

        score = (avg_depth * 25) + ((5 - avg_interruptions) / 5 * 15) + (avg_output * 20) + (avg_flow * 15) + (trend * 10) + (prep_rate * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_depth"] = round(sum(s.depth for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_interruptions"] = round(sum(s.interruptions for s in self._sessions) / len(self._sessions), 1)

            by_type = defaultdict(lambda: {"depth": 0.0, "output": 0.0, "count": 0})
            for s in self._sessions:
                by_type[s.task_type]["depth"] += s.depth
                by_type[s.task_type]["output"] += s.output_quality
                by_type[s.task_type]["count"] += 1
            if by_type:
                best = max(by_type.items(), key=lambda x: (x[1]["depth"] + x[1]["output"]) / max(1, x[1]["count"]))
                self._stats["best_task_type"] = best[0]

            by_hour = defaultdict(lambda: {"depth": 0.0, "output": 0.0, "count": 0})
            for s in self._sessions:
                hour = s.time_of_day[:2] if s.time_of_day else "00"
                by_hour[hour]["depth"] += s.depth
                by_hour[hour]["output"] += s.output_quality
                by_hour[hour]["count"] += 1
            if by_hour:
                best_hour = max(by_hour.items(), key=lambda x: (x[1]["depth"] + x[1]["output"]) / max(1, x[1]["count"]))
                self._stats["best_time"] = best_hour[0]

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

    def _log_session(self, session: DeepWorkSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "task": session.task,
                    "type": session.task_type,
                    "duration": session.duration_minutes,
                    "depth": session.depth,
                    "output": session.output_quality,
                    "flow": session.flow_score,
                    "interruptions": session.interruptions,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dwe_instance: Optional[DeepWorkEnabler] = None
_dwe_lock = threading.Lock()


def get_deep_work_enabler() -> DeepWorkEnabler:
    global _dwe_instance
    with _dwe_lock:
        if _dwe_instance is None:
            _dwe_instance = DeepWorkEnabler()
        return _dwe_instance
