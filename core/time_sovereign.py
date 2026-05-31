"""
LOVE Time Sovereign — Temporal Autonomy Intelligence (Modern AI Pattern)

Most people feel time-poor despite having the same 24 hours. This sovereign:

1. TIME TRACKING
   - Record how time is spent vs how it was intended to be spent
   - Track time leaks (transitions, buffers, decision fatigue)
   - Log time investments and their returns

2. PATTERN ANALYSIS
   - Identify the user's time profile (reactive, planned, flow-seeking, scattered)
   - Find the biggest time leaks and their causes
   - Detect time scarcity beliefs and their effects

3. SOVEREIGNTY BUILDING
   - Suggest time-blocking strategies matched to energy patterns
   - Provide delegation and elimination frameworks
   - Recommend time-protection rituals

4. PROACTIVE MANAGEMENT
   - Alert when time debt is accumulating
   - Suggest time reclamation tactics
   - Track the correlation between time sovereignty and wellbeing

Architecture:
- record_time_block(activity, intended, actual, return): Log block
- get_time_stats(): Get time pattern analysis
- get_sovereignty_suggestion(current_leak, goal): Get tactic
- get_time_score(): Calculate overall time sovereignty health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "time_sovereign"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TIME_LOG = DATA_DIR / "time.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TimeBlock:
    """A tracked time block."""
    block_id: str = ""
    activity: str = ""
    category: str = ""  # deep_work, shallow_work, admin, rest, social, transition, waste
    intended_duration: float = 0.0
    actual_duration: float = 0.0
    return_value: float = 0.5  # 0-1, value generated
    energy_required: str = ""  # low, medium, high
    time_of_day: str = ""
    interrupted: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class TimeSovereign:
    """
    Intelligent time sovereign with leak detection and sovereignty tactic generation.
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
        self._blocks: deque = deque(maxlen=300)
        self._stats = {
            "total_blocks": 0,
            "avg_return": 0.0,
            "avg_leak": 0.0,
            "biggest_leak": "",
            "best_return": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_time_block(self, activity: str = "", category: str = "", intended: float = 0, actual: float = 0, return_value: float = 0.5, energy: str = "", time_of_day: str = "", interrupted: bool = False, notes: str = "") -> TimeBlock:
        """Record a time block."""
        block_id = f"time_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._blocks)}"
        block = TimeBlock(
            block_id=block_id,
            activity=activity or "unspecified",
            category=category or "shallow_work",
            intended_duration=intended,
            actual_duration=actual,
            return_value=return_value,
            energy_required=energy or "medium",
            time_of_day=time_of_day or datetime.now().strftime("%H:%M"),
            interrupted=interrupted,
            notes=notes,
        )

        with self._lock:
            self._blocks.append(block)
            self._stats["total_blocks"] += 1
            self._update_stats()

        self._save_stats()
        self._log_block(block)

        return block

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_time_stats(self) -> Dict[str, Any]:
        """Get time pattern analysis."""
        if not self._blocks:
            return {"status": "insufficient_data"}

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "intended_sum": 0.0, "actual_sum": 0.0, "return_sum": 0.0, "interrupted": 0})
        for b in self._blocks:
            by_category[b.category]["count"] += 1
            by_category[b.category]["intended_sum"] += b.intended_duration
            by_category[b.category]["actual_sum"] += b.actual_duration
            by_category[b.category]["return_sum"] += b.return_value
            if b.interrupted:
                by_category[b.category]["interrupted"] += 1

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            intended = data["intended_sum"]
            actual = data["actual_sum"]
            category_stats[c] = {
                "count": count,
                "total_intended": round(intended, 1),
                "total_actual": round(actual, 1),
                "leak": round(actual - intended, 1),
                "avg_return": round(data["return_sum"] / count, 2),
                "interruption_rate": round(data["interrupted"] / count, 2),
                "roi": round(data["return_sum"] / max(1, actual), 2),
            }

        # Leak analysis
        leaks = {c: d["leak"] for c, d in category_stats.items() if d["leak"] > 0}
        biggest_leak = max(leaks.items(), key=lambda x: x[1]) if leaks else ("", 0)

        # Return analysis
        returns = {c: d["avg_return"] for c, d in category_stats.items()}
        best_return = max(returns.items(), key=lambda x: x[1]) if returns else ("", 0)

        # Time of day analysis
        by_hour = defaultdict(lambda: {"count": 0, "return_sum": 0.0})
        for b in self._blocks:
            hour = b.time_of_day[:2] if b.time_of_day else "00"
            by_hour[hour]["count"] += 1
            by_hour[hour]["return_sum"] += b.return_value

        time_stats = {}
        for h, data in by_hour.items():
            count = data["count"]
            if count >= 2:
                time_stats[h] = {
                    "count": count,
                    "avg_return": round(data["return_sum"] / count, 2),
                }

        # Sovereignty metrics
        total_intended = sum(b.intended_duration for b in self._blocks)
        total_actual = sum(b.actual_duration for b in self._blocks)
        total_leak = total_actual - total_intended
        planned_ratio = sum(1 for b in self._blocks if b.category in ["deep_work", "rest", "social"]) / len(self._blocks)

        return {
            "total_blocks": len(self._blocks),
            "category_stats": category_stats,
            "biggest_leak": biggest_leak[0],
            "best_return": best_return[0],
            "time_stats": time_stats,
            "total_leak_hours": round(total_leak / 60, 1),
            "planned_time_ratio": round(planned_ratio, 2),
            "interruption_rate": round(sum(1 for b in self._blocks if b.interrupted) / len(self._blocks), 2),
            "sovereignty_score": round(1 - (total_leak / max(1, total_actual)), 2),
        }

    def get_sovereignty_suggestion(self, current_leak: str = "", goal: str = "", time_available: float = 30) -> Dict[str, Any]:
        """Get tactic."""
        tactics = {
            "transitions": [
                "Batch similar tasks. Every switch costs 15+ minutes.",
                "Set a 5-minute buffer between meetings. No back-to-backs.",
                "Use the '2-minute rule': if it takes less than 2 minutes, do it now. Otherwise, batch it.",
                "Theme your days: Monday for admin, Tuesday for deep work, etc.",
            ],
            "interruptions": [
                "Set 'office hours' when people can interrupt you. Protect the rest.",
                "Put a sign on your door/virtual status: 'Deep work until X time'",
                "Turn off all notifications for 90-minute blocks",
                "Tell people: 'I'm in focus mode. I'll respond at 3pm.'",
            ],
            "decision_fatigue": [
                "Automate or ritualize decisions: same breakfast, same morning routine",
                "Make important decisions before noon. Trivial decisions after 4pm.",
                "Use if-then rules: 'If it's Tuesday, I go to the gym.' No decision needed.",
                "Delegate decisions that don't require your unique judgment",
            ],
            "scrolling": [
                "Delete apps that you open without intention",
                "Use app timers. When they run out, the app is done for the day.",
                "Charge your phone in another room overnight",
                "Before opening an app, ask: 'What am I looking for?'",
            ],
            "meetings": [
                "Default meeting length: 25 or 50 minutes, not 30 or 60",
                "Require agendas. No agenda, no meeting.",
                "Stand for meetings under 15 minutes",
                "Decline meetings where you're optional. Seriously.",
            ],
            "overcommitment": [
                "Before saying yes, say: 'Let me check my calendar and energy'",
                "For every new yes, identify one no",
                "Keep a 'not doing' list. It's as important as a to-do list.",
                "Practice 'no, but' or 'not now' instead of 'yes, but I'll suffer'",
            ],
        }

        selected = tactics.get(current_leak, tactics["transitions"])
        tactic = random.choice(selected)

        return {
            "current_leak": current_leak or "general",
            "goal": goal or "reclaim_time",
            "tactic": tactic,
            "time_to_implement": time_available,
            "principle": "Time is not money. Time is life. Spend it like it matters.",
            "challenge": "This week, track one category of time. Just observe. Awareness precedes change.",
        }

    def get_time_score(self) -> int:
        """Calculate overall time sovereignty health (0-100)."""
        if not self._blocks:
            return 40

        # Low leak ratio
        total_intended = sum(b.intended_duration for b in self._blocks)
        total_actual = sum(b.actual_duration for b in self._blocks)
        leak_ratio = (total_actual - total_intended) / max(1, total_actual)

        # High return on time
        avg_return = sum(b.return_value for b in self._blocks) / len(self._blocks)

        # Low interruption
        interruption_rate = sum(1 for b in self._blocks if b.interrupted) / len(self._blocks)

        # Planned time ratio
        planned = sum(1 for b in self._blocks if b.category in ["deep_work", "rest", "social"])
        planned_ratio = planned / len(self._blocks)

        # Recent trend
        recent = list(self._blocks)[-14:]
        recent_return = sum(b.return_value for b in recent) / len(recent)
        older = list(self._blocks)[:-14] if len(self._blocks) > 14 else []
        if older:
            older_return = sum(b.return_value for b in older) / len(older)
            trend = recent_return - older_return
        else:
            trend = 0

        score = ((1 - leak_ratio) * 25) + (avg_return * 25) + ((1 - interruption_rate) * 15) + (planned_ratio * 15) + (trend * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._blocks:
            self._stats["avg_return"] = round(sum(b.return_value for b in self._blocks) / len(self._blocks), 2)
            
            total_intended = sum(b.intended_duration for b in self._blocks)
            total_actual = sum(b.actual_duration for b in self._blocks)
            self._stats["avg_leak"] = round((total_actual - total_intended) / len(self._blocks), 1)

            by_category = defaultdict(lambda: {"actual": 0.0, "intended": 0.0, "return": 0.0})
            for b in self._blocks:
                by_category[b.category]["actual"] += b.actual_duration
                by_category[b.category]["intended"] += b.intended_duration
                by_category[b.category]["return"] += b.return_value
            
            if by_category:
                biggest_leak = max(by_category.items(), key=lambda x: x[1]["actual"] - x[1]["intended"])
                best_return = max(by_category.items(), key=lambda x: x[1]["return"] / max(1, x[1]["actual"]))
                self._stats["biggest_leak"] = biggest_leak[0]
                self._stats["best_return"] = best_return[0]

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

    def _log_block(self, block: TimeBlock):
        try:
            with open(TIME_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": block.timestamp,
                    "activity": block.activity,
                    "category": block.category,
                    "intended": block.intended_duration,
                    "actual": block.actual_duration,
                    "return": block.return_value,
                    "interrupted": block.interrupted,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ts_instance: Optional[TimeSovereign] = None
_ts_lock = threading.Lock()


def get_time_sovereign() -> TimeSovereign:
    global _ts_instance
    with _ts_lock:
        if _ts_instance is None:
            _ts_instance = TimeSovereign()
        return _ts_instance
