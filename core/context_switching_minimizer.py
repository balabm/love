"""
LOVE Context Switching Minimizer — Flow State Protector (Modern AI Pattern)

Context switching is the silent productivity killer. This minimizer:

1. SWITCH DETECTION
   - Track task switches in real-time
   - Detect rapid switching (switching before completing anything)
   - Measure switch cost (time to regain focus after each switch)

2. BATCH SUGGESTIONS
   - Group similar tasks together to minimize mental context changes
   - Suggest "theme hours" (email hour, coding hour, admin hour)
   - Recommend task ordering that minimizes switches

3. INTERRUPTION SHIELDING
   - Detect when the user is in flow and warn about context switches
   - Suggest deferring new tasks until current context is complete
   - Calculate and display real-time context switch cost

4. FLOW PROTECTION
   - Monitor flow state indicators (focus depth, task duration, interruption rate)
   - Alert when flow is about to be broken
   - Suggest batch windows for specific task types

Architecture:
- record_task_switch(from_task, to_task, duration): Log a context switch
- get_switch_stats(): Get context switching analytics
- get_batch_suggestion(): Suggest task batching to minimize switches
- protect_flow(current_task): Get flow protection recommendations
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "context_switching_minimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SWITCH_LOG = DATA_DIR / "switch_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ContextSwitch:
    """A recorded context switch."""
    from_task: str = ""
    from_category: str = ""
    to_task: str = ""
    to_category: str = ""
    switch_time_seconds: float = 0.0  # time spent switching
    recovery_time_seconds: float = 0.0  # time to regain focus
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    flow_broken: bool = False


class ContextSwitchingMinimizer:
    """
    Minimize context switching to protect flow state.
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
        self._switches: deque = deque(maxlen=500)
        self._current_task: str = ""
        self._current_category: str = ""
        self._task_start: Optional[datetime] = None
        self._stats = {
            "total_switches": 0,
            "avg_switch_cost": 0.0,
            "flow_broken_count": 0,
            "switches_per_hour": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_task_switch(self, to_task: str, to_category: str = "", switch_time: float = 0.0, recovery_time: float = 0.0) -> ContextSwitch:
        """Record a context switch."""
        now = datetime.now()

        # Calculate time spent on previous task if we have a start time
        if self._task_start:
            time_on_previous = (now - self._task_start).total_seconds()
        else:
            time_on_previous = 0

        # Determine if flow was broken (switched before 15 min on task)
        flow_broken = time_on_previous < 900  # 15 minutes

        switch = ContextSwitch(
            from_task=self._current_task,
            from_category=self._current_category,
            to_task=to_task,
            to_category=to_category,
            switch_time_seconds=switch_time,
            recovery_time_seconds=recovery_time,
            flow_broken=flow_broken,
        )

        with self._lock:
            self._switches.append(switch)
            self._stats["total_switches"] += 1
            if flow_broken:
                self._stats["flow_broken_count"] += 1

        # Update current task
        self._current_task = to_task
        self._current_category = to_category
        self._task_start = now

        self._update_stats()
        self._save_stats()
        self._log_switch(switch)

        return switch

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_switch_stats(self, hours: int = 4) -> Dict[str, Any]:
        """Get context switching analytics."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        recent = [s for s in self._switches if s.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Calculate switch cost
        costs = [s.switch_time_seconds + s.recovery_time_seconds for s in recent]
        avg_cost = sum(costs) / len(costs)

        # Category switch matrix
        category_switches = defaultdict(int)
        for s in recent:
            if s.from_category and s.to_category:
                pair = tuple(sorted([s.from_category, s.to_category]))
                category_switches[pair] += 1

        # Most costly switches
        costly_switches = sorted(
            [(s.from_task, s.to_task, s.switch_time_seconds + s.recovery_time_seconds) for s in recent],
            key=lambda x: x[2],
            reverse=True,
        )[:5]

        # Switches per hour
        time_span_hours = hours
        switches_per_hour = len(recent) / max(1, time_span_hours)

        return {
            "hours_analyzed": hours,
            "total_switches": len(recent),
            "avg_switch_cost_seconds": round(avg_cost, 1),
            "flow_broken_pct": round(sum(1 for s in recent if s.flow_broken) / len(recent) * 100, 1),
            "switches_per_hour": round(switches_per_hour, 1),
            "top_category_switches": [(k[0], k[1], v) for k, v in sorted(category_switches.items(), key=lambda x: x[1], reverse=True)[:5]],
            "costliest_switches": costly_switches,
            "estimated_daily_switch_cost_minutes": round(switches_per_hour * avg_cost / 60 * 8, 1),  # 8-hour day
        }

    def get_batch_suggestion(self) -> Dict[str, Any]:
        """Suggest task batching to minimize switches."""
        # Analyze recent switches to find patterns
        stats = self.get_switch_stats(24)
        if stats.get("status") == "insufficient_data":
            return {
                "suggestion": "Start tracking tasks to get batching suggestions",
                "theme_hours": [],
            }

        # Identify most frequent category switches
        category_pairs = stats.get("top_category_switches", [])

        # Suggest theme hours based on frequent switches
        all_categories = set()
        for pair in category_pairs:
            all_categories.add(pair[0])
            all_categories.add(pair[1])

        theme_hours = []
        for cat in sorted(all_categories)[:3]:  # Top 3 categories
            theme_hours.append({
                "category": cat,
                "suggested_time": "morning" if cat in ["creative", "coding", "deep_work"] else "afternoon",
                "reason": f"Batch all {cat} tasks to minimize context switching",
            })

        return {
            "suggestion": f"You switched contexts {stats['switches_per_hour']:.1f} times/hour recently. Consider theme hours.",
            "estimated_savings_minutes": round(stats.get("estimated_daily_switch_cost_minutes", 0) * 0.5, 1),
            "theme_hours": theme_hours,
            "tip": "Group similar tasks. Your brain pays a tax every time you switch contexts.",
        }

    def protect_flow(self, current_task: str = "", current_category: str = "") -> Dict[str, Any]:
        """Get flow protection recommendations."""
        if current_task:
            self._current_task = current_task
            self._current_category = current_category
            if not self._task_start:
                self._task_start = datetime.now()

        if not self._task_start:
            return {"status": "no_active_task"}

        time_on_task = (datetime.now() - self._task_start).total_seconds()
        minutes_on_task = time_on_task / 60

        # Flow depth estimation
        flow_depth = min(1.0, minutes_on_task / 20)  # 20 min to full flow

        recommendations = []
        if minutes_on_task < 5:
            recommendations.append("You're just getting started. Avoid switching for at least 15 minutes.")
        elif minutes_on_task < 15:
            recommendations.append("Entering flow zone. Any switch now would cost significant recovery time.")
        else:
            recommendations.append("Deep flow state. Protect this at all costs.")

        return {
            "current_task": self._current_task,
            "minutes_on_task": round(minutes_on_task, 1),
            "flow_depth": round(flow_depth, 2),
            "flow_state": "deep" if flow_depth > 0.8 else "building" if flow_depth > 0.4 else "shallow",
            "recommendations": recommendations,
            "switch_cost_warning": f"Switching now would cost ~{int(5 + (1 - flow_depth) * 10)} minutes of recovery",
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._switches:
            costs = [s.switch_time_seconds + s.recovery_time_seconds for s in self._switches]
            self._stats["avg_switch_cost"] = round(sum(costs) / len(costs), 1)

            # Switches per hour (last 4 hours)
            cutoff = (datetime.now() - timedelta(hours=4)).isoformat()
            recent = [s for s in self._switches if s.timestamp > cutoff]
            self._stats["switches_per_hour"] = round(len(recent) / 4, 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "current_task": self._current_task,
                "current_category": self._current_category,
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                self._current_task = data.get("current_task", "")
                self._current_category = data.get("current_category", "")
        except Exception:
            pass

    def _log_switch(self, switch: ContextSwitch):
        try:
            with open(SWITCH_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": switch.timestamp,
                    "from_task": switch.from_task,
                    "from_category": switch.from_category,
                    "to_task": switch.to_task,
                    "to_category": switch.to_category,
                    "switch_time": switch.switch_time_seconds,
                    "recovery_time": switch.recovery_time_seconds,
                    "flow_broken": switch.flow_broken,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_csm_instance: Optional[ContextSwitchingMinimizer] = None
_csm_lock = threading.Lock()


def get_context_switching_minimizer() -> ContextSwitchingMinimizer:
    global _csm_instance
    with _csm_lock:
        if _csm_instance is None:
            _csm_instance = ContextSwitchingMinimizer()
        return _csm_instance
