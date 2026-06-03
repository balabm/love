"""
LOVE DIY Project Planner — Project Craft Intelligence (Modern AI Pattern)

Most people start DIY projects without planning. This planner:

1. PROJECT TRACKING
   - Record DIY project moments and their characteristics
   - Track project types (build, repair, decorate, upcycle, create, restore)
   - Log planning, execution, patience, creativity, and satisfaction of projects

2. PATTERN ANALYSIS
   - Identify the user's project profile (impulsive, stalled, developing, accomplished)
   - Find project patterns that create completion vs abandonment
   - Detect chronic project abandonment and its costs

3. PROJECT BUILDING
   - Suggest practices for planning and executing DIY projects
   - Provide frameworks for project scoping and sequencing
   - Recommend practices for staying motivated through difficulty

4. PROJECT MASTERY CULTIVATION
   - Track the correlation between planning and project success
   - Alert when starting is replacing finishing
   - Celebrate moments of genuine project completion

Architecture:
- record_project(project, type, planning, execution, patience, creativity, satisfaction): Log project
- get_project_stats(): Get project pattern analysis
- get_project_suggestion(capacity, context): Get suggestion
- get_project_score(): Calculate overall project health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "diy_project_planner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_LOG = DATA_DIR / "projects.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ProjectEntry:
    """A tracked DIY project moment."""
    entry_id: str = ""
    project: str = ""  # what was the project
    project_type: str = ""  # build, repair, decorate, upcycle, create, restore
    planning: float = 0.0  # 0-1
    execution: float = 0.0  # 0-1
    patience: float = 0.0  # 0-1
    creativity: float = 0.0  # 0-1
    satisfaction: float = 0.0  # 0-1
    completion: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DIYProjectPlanner:
    """
    Intelligent DIY project planner with abandonment detection and project mastery cultivation.
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
            "avg_planning": 0.0,
            "avg_completion": 0.0,
            "abandonment_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_project(self, project: str = "", project_type: str = "", planning: float = 0.0, execution: float = 0.0, patience: float = 0.0, creativity: float = 0.0, satisfaction: float = 0.0, completion: float = 0.0, notes: str = "") -> ProjectEntry:
        """Record a DIY project moment."""
        entry_id = f"diy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ProjectEntry(
            entry_id=entry_id,
            project=project or "unspecified",
            project_type=project_type or "build",
            planning=planning,
            execution=execution,
            patience=patience,
            creativity=creativity,
            satisfaction=satisfaction,
            completion=completion,
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

    def get_project_stats(self) -> Dict[str, Any]:
        """Get project pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "planning_sum": 0.0, "execution_sum": 0.0, "completion_sum": 0.0})
        for e in self._entries:
            by_type[e.project_type]["count"] += 1
            by_type[e.project_type]["planning_sum"] += e.planning
            by_type[e.project_type]["execution_sum"] += e.execution
            by_type[e.project_type]["completion_sum"] += e.completion

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_planning": round(data["planning_sum"] / count, 2),
                "avg_execution": round(data["execution_sum"] / count, 2),
                "avg_completion": round(data["completion_sum"] / count, 2),
            }

        # Planning analysis
        high_plan = [e for e in self._entries if e.planning > 0.7]
        low_plan = [e for e in self._entries if e.planning < 0.4]
        if high_plan and low_plan:
            high_plan_comp = sum(e.completion for e in high_plan) / len(high_plan)
            low_plan_comp = sum(e.completion for e in low_plan) / len(low_plan)
            high_plan_sat = sum(e.satisfaction for e in high_plan) / len(high_plan)
            low_plan_sat = sum(e.satisfaction for e in low_plan) / len(low_plan)
        else:
            high_plan_comp = 0
            low_plan_comp = 0
            high_plan_sat = 0
            low_plan_sat = 0

        # Patience analysis
        high_pat = [e for e in self._entries if e.patience > 0.7]
        low_pat = [e for e in self._entries if e.patience < 0.4]
        if high_pat and low_pat:
            high_pat_comp = sum(e.completion for e in high_pat) / len(high_pat)
            low_pat_comp = sum(e.completion for e in low_pat) / len(low_pat)
        else:
            high_pat_comp = 0
            low_pat_comp = 0

        # Abandonment risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_plan = sum(e.planning for e in recent) / len(recent)
            recent_comp = sum(e.completion for e in recent) / len(recent)
            abandonment_risk = recent_plan > 0.5 and recent_comp < 0.3
        else:
            abandonment_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "planning_impact": {
                "high_planning_completion": round(high_plan_comp, 2),
                "low_planning_completion": round(low_plan_comp, 2),
                "high_planning_satisfaction": round(high_plan_sat, 2),
                "low_planning_satisfaction": round(low_plan_sat, 2),
            },
            "patience_effect": {
                "high_patience_completion": round(high_pat_comp, 2),
                "low_patience_completion": round(low_pat_comp, 2),
            },
            "abandonment_risk": abandonment_risk,
            "avg_planning": round(sum(e.planning for e in self._entries) / len(self._entries), 2),
            "avg_completion": round(sum(e.completion for e in self._entries) / len(self._entries), 2),
        }

    def get_project_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get project suggestion."""
        suggestions = [
            "Most DIY projects fail in the planning. Not the doing. People buy materials before they know what they need. They start before they know where they're going. And they end up with half-finished projects and full garages. Plan first. Do second.",
            "Scope before you start. What is the actual goal? What is the minimum viable version? What is the dream version? Start with the minimum. Finish it. Then iterate. The person who scopes well finishes. The person who dreams big and starts big abandons.",
            "Break it into steps. Not vague steps. Specific steps. 'Buy wood.' 'Cut to length.' 'Sand.' 'Assemble.' 'Finish.' Each step should be completable in one session. If it's not, break it more. Small steps create momentum. Momentum creates completion.",
            "Budget time. Not just money. How long will each step take? Double it. Then add buffer. Projects take longer than you think. Always. The person who budgets time well is the person who doesn't abandon when it takes longer than expected.",
            "Gather everything before you start. Materials. Tools. Space. Time. Knowledge. If you have to stop to buy something, you might not restart. The prepared workspace is the completed workspace.",
            "Document as you go. Photos. Notes. Mistakes. Learnings. The documentation is for you. For next time. For the person you might teach. And for the satisfaction of seeing where you started.",
            "Expect problems. They will come. The wrong size. The broken part. The unexpected difficulty. They're not failures. They're the project. The person who expects problems is the person who doesn't quit when they arrive.",
            "Finish before you start the next one. One project at a time. Not five. Not ten. One. Finish it. Celebrate it. Then start the next. The person who finishes one is more accomplished than the person who starts ten.",
            "Share your work. Not for validation. For community. For inspiration. For the joy of showing what you made. The maker who shares is the maker who is part of something bigger than their garage.",
            "The person who plans and finishes DIY projects is not just building things. They're building themselves. They're proving that they can imagine something and make it real. That is the most fundamental human capability. And it extends to everything."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small project planned. One step broken down. One hour budgeted. One tool gathered. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A scoped project. A step-by-step plan. A prepared workspace. A problem expected and overcome. Medium project craft."
        else:
            capacity_note = "Good capacity. Deep project mastery work. A systematic practice of planning, execution, patience, and completion. You have the strength to build what you imagine."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "DIY project planning is not about being handy. It's about being intentional. Most people start projects impulsively. They see something they want. They buy materials. They start working. And they abandon it when it gets hard. Or boring. Or when a new idea comes along. The work of DIY project planning is about understanding that finishing is more important than starting. That planning is more important than doing. That patience is more important than speed. And that the person who learns to plan, execute, and finish projects is not just building things. They're building the capability to make ideas real. And that capability is the foundation of all creation."
        }

    def get_project_score(self) -> int:
        """Calculate overall project health (0-100)."""
        if not self._entries:
            return 25

        avg_plan = sum(e.planning for e in self._entries) / len(self._entries)
        avg_exec = sum(e.execution for e in self._entries) / len(self._entries)
        avg_pat = sum(e.patience for e in self._entries) / len(self._entries)
        avg_creat = sum(e.creativity for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_comp = sum(e.completion for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_plan = sum(e.planning for e in recent) / len(recent)
            recent_comp = sum(e.completion for e in recent) / len(recent)
        else:
            recent_plan = 0
            recent_comp = 0

        # Abandonment penalty
        aban_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_plan_30 = sum(e.planning for e in last_30) / len(last_30)
            recent_comp_30 = sum(e.completion for e in last_30) / len(last_30)
            if recent_plan_30 > 0.5 and recent_comp_30 < 0.3:
                aban_penalty = 15

        # Type variety
        unique_types = len(set(e.project_type for e in self._entries))

        score = (avg_plan * 25) + (avg_exec * 15) + (avg_pat * 10) + (avg_creat * 10) + (avg_sat * 10) + (avg_comp * 20) + (recent_plan * 5) + (recent_comp * 5) + (unique_types * 2) - aban_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_planning"] = round(sum(e.planning for e in self._entries) / len(self._entries), 2)
            self._stats["avg_completion"] = round(sum(e.completion for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_plan = sum(e.planning for e in recent) / len(recent)
                recent_comp = sum(e.completion for e in recent) / len(recent)
                self._stats["abandonment_risk"] = recent_plan > 0.5 and recent_comp < 0.3
            else:
                self._stats["abandonment_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.diy_project_planner")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.diy_project_planner")

    def _log_entry(self, entry: ProjectEntry):
        try:
            with open(PROJECT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "project": entry.project,
                    "project_type": entry.project_type,
                    "planning": entry.planning,
                    "completion": entry.completion,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.diy_project_planner")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dpp_instance: Optional[DIYProjectPlanner] = None
_dpp_lock = threading.Lock()


def get_diy_project_planner() -> DIYProjectPlanner:
    global _dpp_instance
    with _dpp_lock:
        if _dpp_instance is None:
            _dpp_instance = DIYProjectPlanner()
        return _dpp_instance
