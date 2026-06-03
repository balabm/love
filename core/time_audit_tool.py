"""
LOVE Time Audit Tool — Temporal Intelligence (Modern AI Pattern)

Most time tracking is passive logging. This audit tool:

1. TIME ALLOCATION
   - Track how time is spent across categories (work, rest, social, learning, transit, etc.)
   - Compare actual vs intended time allocation
   - Identify time leaks (untracked or wasted time)

2. TIME QUALITY SCORING
   - Score time blocks by alignment with goals and values
   - Identify high-value vs low-value time usage
   - Calculate time ROI (return on time invested)

3. PATTERN DETECTION
   - Find peak productivity hours
   - Detect time-of-day preferences
   - Identify time waste patterns (excessive context switching, doom scrolling)

4. OPTIMIZATION SUGGESTIONS
   - Suggest time reallocation based on goals
   - Recommend batching similar tasks
   - Warn about time debt (overcommitment)

Architecture:
- record_time_block(category, duration, quality, goal_aligned): Log time usage
- get_time_allocation(days): Get time breakdown
- get_time_quality_score(): Get overall time quality score
- get_time_leaks(): Identify wasted time
- get_optimization_suggestions(): Suggest time improvements
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "time_audit"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TIME_LOG = DATA_DIR / "time_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TimeBlock:
    """A recorded time block."""
    category: str = ""  # work, rest, social, learning, transit, admin, entertainment, exercise
    duration_minutes: float = 0.0
    quality: float = 0.5  # 0-1 how valuable was this time
    goal_aligned: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    task: str = ""
    interrupted: bool = False
    context: str = ""  # morning, afternoon, evening, night


class TimeAuditTool:
    """
    Audit time usage and optimize allocation.
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
        self._blocks: deque = deque(maxlen=500)
        self._stats = {
            "total_minutes_logged": 0,
            "avg_quality": 0.5,
            "goal_aligned_pct": 0.5,
            "time_leak_hours": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_time_block(self, category: str, duration: float, quality: float = 0.5, goal_aligned: bool = True, task: str = "", interrupted: bool = False) -> TimeBlock:
        """Record a time block."""
        block = TimeBlock(
            category=category,
            duration_minutes=duration,
            quality=quality,
            goal_aligned=goal_aligned,
            task=task,
            interrupted=interrupted,
            context=self._get_time_context(),
        )

        with self._lock:
            self._blocks.append(block)
            self._stats["total_minutes_logged"] += duration
            self._update_stats(block)

        self._save_stats()
        self._log_block(block)

        return block

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_time_allocation(self, days: int = 7) -> Dict[str, Any]:
        """Get time breakdown by category."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [b for b in self._blocks if b.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Category totals
        by_category = defaultdict(lambda: {"minutes": 0.0, "count": 0, "quality_sum": 0.0, "goal_aligned": 0})
        total_minutes = 0.0

        for b in recent:
            cat = b.category
            by_category[cat]["minutes"] += b.duration_minutes
            by_category[cat]["count"] += 1
            by_category[cat]["quality_sum"] += b.quality
            if b.goal_aligned:
                by_category[cat]["goal_aligned"] += 1
            total_minutes += b.duration_minutes

        # Calculate percentages
        for cat in by_category:
            by_category[cat]["pct"] = round(by_category[cat]["minutes"] / max(1, total_minutes) * 100, 1)
            by_category[cat]["avg_quality"] = round(by_category[cat]["quality_sum"] / by_category[cat]["count"], 2)

        # Hours per day
        days_logged = len(set(b.timestamp[:10] for b in recent))
        hours_per_day = total_minutes / 60 / max(1, days_logged)

        return {
            "days_analyzed": days_logged,
            "total_hours": round(total_minutes / 60, 1),
            "hours_per_day": round(hours_per_day, 1),
            "by_category": dict(by_category),
            "categories": sorted(by_category.keys()),
        }

    def get_time_quality_score(self) -> int:
        """Calculate overall time quality score (0-100)."""
        if not self._blocks:
            return 50

        recent = list(self._blocks)[-30:]
        total_minutes = sum(b.duration_minutes for b in recent)
        if total_minutes == 0:
            return 50

        # Quality-weighted minutes
        quality_weighted = sum(b.duration_minutes * b.quality for b in recent)
        quality_score = (quality_weighted / total_minutes) * 100

        # Goal alignment score
        aligned_minutes = sum(b.duration_minutes for b in recent if b.goal_aligned)
        alignment_score = (aligned_minutes / total_minutes) * 100

        # Interruption penalty
        interrupted_count = sum(1 for b in recent if b.interrupted)
        interruption_penalty = min(20, interrupted_count * 2)

        overall = round(quality_score * 0.5 + alignment_score * 0.5 - interruption_penalty)
        return max(0, min(100, overall))

    def get_time_leaks(self, days: int = 7) -> List[Dict[str, Any]]:
        """Identify wasted time."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [b for b in self._blocks if b.timestamp > cutoff]

        leaks = []

        # Low-quality blocks
        low_quality = [b for b in recent if b.quality < 0.3 and b.duration_minutes > 15]
        if low_quality:
            total_minutes = sum(b.duration_minutes for b in low_quality)
            leaks.append({
                "type": "low_quality_time",
                "description": f"{len(low_quality)} low-quality blocks totaling {total_minutes:.0f} minutes",
                "severity": "medium" if total_minutes < 120 else "high",
                "minutes": total_minutes,
            })

        # Frequent interruptions
        interrupted = [b for b in recent if b.interrupted]
        if len(interrupted) > 3:
            leaks.append({
                "type": "interruption_damage",
                "description": f"{len(interrupted)} interrupted sessions - context switching tax",
                "severity": "high",
                "minutes": len(interrupted) * 10,  # estimated recovery time
            })

        # Entertainment overuse
        entertainment = [b for b in recent if b.category == "entertainment"]
        entertainment_minutes = sum(b.duration_minutes for b in entertainment)
        if entertainment_minutes > 180:
            leaks.append({
                "type": "entertainment_overuse",
                "description": f"{entertainment_minutes/60:.1f} hours entertainment (over 3h threshold)",
                "severity": "medium",
                "minutes": entertainment_minutes - 180,
            })

        return leaks

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest time improvements."""
        suggestions = []
        allocation = self.get_time_allocation(7)
        leaks = self.get_time_leaks(7)

        if allocation.get("status") == "insufficient_data":
            return [{"suggestion": "Start logging time blocks to get optimization suggestions", "impact": "high"}]

        # Check work/rest balance
        work_minutes = allocation.get("by_category", {}).get("work", {}).get("minutes", 0)
        rest_minutes = allocation.get("by_category", {}).get("rest", {}).get("minutes", 0)
        work_hours = work_minutes / 60
        rest_hours = rest_minutes / 60

        if work_hours > 10 and rest_hours < 2:
            suggestions.append({
                "suggestion": "You're working too much and resting too little. Schedule at least 2 hours of rest daily.",
                "impact": "high",
                "category": "balance",
            })

        # Check for batching opportunities
        categories = allocation.get("by_category", {})
        admin = categories.get("admin", {})
        if admin.get("count", 0) > 5 and admin.get("minutes", 0) < 60:
            suggestions.append({
                "suggestion": f"You did {admin['count']} admin tasks in short bursts. Try batching them into one focused session.",
                "impact": "medium",
                "category": "batching",
            })

        # Address leaks
        for leak in leaks:
            if leak["type"] == "interruption_damage":
                suggestions.append({
                    "suggestion": "Turn off notifications during deep work. Each interruption costs ~10 minutes of recovery.",
                    "impact": "high",
                    "category": "focus",
                })
            elif leak["type"] == "entertainment_overuse":
                suggestions.append({
                    "suggestion": "Consider setting a daily entertainment limit. Try replacing 30 min with reading or walking.",
                    "impact": "medium",
                    "category": "limits",
                })

        # Time-of-day optimization
        peak_hours = self._find_peak_hours()
        if peak_hours:
            suggestions.append({
                "suggestion": f"Your peak energy seems to be {peak_hours}. Schedule important work then.",
                "impact": "high",
                "category": "scheduling",
            })

        return suggestions

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _get_time_context(self) -> str:
        """Get time-of-day context."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _find_peak_hours(self) -> str:
        """Find peak productivity hours from data."""
        if not self._blocks:
            return ""

        by_hour = defaultdict(lambda: {"quality_sum": 0.0, "count": 0})
        for b in self._blocks:
            try:
                hour = datetime.fromisoformat(b.timestamp).hour
                by_hour[hour]["quality_sum"] += b.quality
                by_hour[hour]["count"] += 1
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.time_audit_tool")

        if not by_hour:
            return ""

        avg_by_hour = {h: stats["quality_sum"] / stats["count"] for h, stats in by_hour.items() if stats["count"] >= 2}
        if not avg_by_hour:
            return ""

        best_hour = max(avg_by_hour.items(), key=lambda x: x[1])[0]
        return f"{best_hour}:00-{best_hour+1}:00"

    def _update_stats(self, block: TimeBlock):
        """Update running statistics."""
        n = len(self._blocks)
        self._stats["avg_quality"] = round(
            (self._stats["avg_quality"] * (n - 1) + block.quality) / n, 2
        )

        # Goal alignment percentage
        aligned_count = sum(1 for b in self._blocks if b.goal_aligned)
        self._stats["goal_aligned_pct"] = round(aligned_count / max(1, n), 2)

        # Calculate time leaks
        leaks = self.get_time_leaks(7)
        self._stats["time_leak_hours"] = round(sum(l["minutes"] for l in leaks) / 60, 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.time_audit_tool")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.time_audit_tool")

    def _log_block(self, block: TimeBlock):
        try:
            with open(TIME_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": block.timestamp,
                    "category": block.category,
                    "duration": block.duration_minutes,
                    "quality": block.quality,
                    "goal_aligned": block.goal_aligned,
                    "task": block.task,
                    "interrupted": block.interrupted,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.time_audit_tool")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_tat_instance: Optional[TimeAuditTool] = None
_tat_lock = threading.Lock()


def get_time_audit_tool() -> TimeAuditTool:
    global _tat_instance
    with _tat_lock:
        if _tat_instance is None:
            _tat_instance = TimeAuditTool()
        return _tat_instance
