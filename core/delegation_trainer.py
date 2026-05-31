"""
LOVE Delegation Trainer — Distribution Intelligence (Modern AI Pattern)

Most burnout comes from doing everything yourself. This trainer:

1. DELEGATION TRACKING
   - Record delegation actions and their characteristics
   - Track delegation types (task, decision, responsibility, authority)
   - Log outcomes and their effects on capacity and development

2. PATTERN ANALYSIS
   - Identify the user's delegation profile (hoarder, dumper, developer, strategic)
   - Find delegation approaches that create capable teams
   - Detect delegation failure patterns

3. DELEGATION BUILDING
   - Suggest delegation targets matched to task and person
   - Provide handoff and support frameworks
   - Recommendation follow-up practices

4. CAPACITY CULTIVATION
   - Track the correlation between delegation and team capability
   - Alert when delegation is becoming abdication
   - Celebrate moments of effective distribution

Architecture:
- record_delegation(task, person, type, support, outcome): Log delegation
- get_delegation_stats(): Get delegation pattern analysis
- get_delegation_plan(task, person_capacity): Get plan
- get_delegation_score(): Calculate overall delegation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "delegation_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DELEGATION_LOG = DATA_DIR / "delegations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class DelegationEntry:
    """A tracked delegation entry."""
    entry_id: str = ""
    task: str = ""  # what was delegated
    person: str = ""  # who received it
    delegation_type: str = ""  # task, decision, responsibility, authority
    clarity: float = 0.5  # 0-1, how clear were the expectations
    support: float = 0.5  # 0-1, how much support was provided
    autonomy: float = 0.5  # 0-1, how much freedom did they have
    completion: float = 0.0  # 0-1, how well was it completed
    development: float = 0.0  # 0-1, did the person grow
    time_saved: float = 0.0  # hours
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DelegationTrainer:
    """
    Intelligent delegation trainer with capacity optimization and development tracking.
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
            "avg_completion": 0.0,
            "avg_development": 0.0,
            "avg_time_saved": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_delegation(self, task: str = "", person: str = "", delegation_type: str = "", clarity: float = 0.5, support: float = 0.5, autonomy: float = 0.5, completion: float = 0.0, development: float = 0.0, time_saved: float = 0.0, notes: str = "") -> DelegationEntry:
        """Record a delegation entry."""
        entry_id = f"del_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = DelegationEntry(
            entry_id=entry_id,
            task=task or "unspecified",
            person=person or "unspecified",
            delegation_type=delegation_type or "task",
            clarity=clarity,
            support=support,
            autonomy=autonomy,
            completion=completion,
            development=development,
            time_saved=time_saved,
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

    def get_delegation_stats(self) -> Dict[str, Any]:
        """Get delegation pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "comp_sum": 0.0, "dev_sum": 0.0, "time_sum": 0.0})
        for e in self._entries:
            by_type[e.delegation_type]["count"] += 1
            by_type[e.delegation_type]["comp_sum"] += e.completion
            by_type[e.delegation_type]["dev_sum"] += e.development
            by_type[e.delegation_type]["time_sum"] += e.time_saved

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_completion": round(data["comp_sum"] / count, 2),
                "avg_development": round(data["dev_sum"] / count, 2),
                "avg_time_saved": round(data["time_sum"] / count, 1),
            }

        # Person analysis
        by_person = defaultdict(lambda: {"count": 0, "comp_sum": 0.0, "dev_sum": 0.0})
        for e in self._entries:
            by_person[e.person]["count"] += 1
            by_person[e.person]["comp_sum"] += e.completion
            by_person[e.person]["dev_sum"] += e.development

        person_stats = {}
        for p, data in by_person.items():
            count = data["count"]
            if count >= 2:
                person_stats[p] = {
                    "count": count,
                    "avg_completion": round(data["comp_sum"] / count, 2),
                    "avg_development": round(data["dev_sum"] / count, 2),
                }

        best_person = max(person_stats.items(), key=lambda x: x[1]["avg_completion"] + x[1]["avg_development"]) if person_stats else ("", {})

        # Clarity impact
        high_clarity = [e for e in self._entries if e.clarity > 0.7]
        low_clarity = [e for e in self._entries if e.clarity < 0.4]
        if high_clarity and low_clarity:
            high_clarity_comp = sum(e.completion for e in high_clarity) / len(high_clarity)
            low_clarity_comp = sum(e.completion for e in low_clarity) / len(low_clarity)
        else:
            high_clarity_comp = 0
            low_clarity_comp = 0

        # Support vs autonomy balance
        high_support = [e for e in self._entries if e.support > 0.7]
        low_support = [e for e in self._entries if e.support < 0.4]
        if high_support and low_support:
            high_support_comp = sum(e.completion for e in high_support) / len(high_support)
            low_support_comp = sum(e.completion for e in low_support) / len(low_support)
        else:
            high_support_comp = 0
            low_support_comp = 0

        # Abdication detection
        high_auto_low_support = [e for e in self._entries if e.autonomy > 0.7 and e.support < 0.3]
        if high_auto_low_support:
            abdication_risk = True
        else:
            abdication_risk = False

        # Hoarding detection
        low_auto_high_task = [e for e in self._entries if e.autonomy < 0.3 and e.delegation_type == "task"]
        if low_auto_high_task:
            hoarding_risk = True
        else:
            hoarding_risk = False

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_comp = sum(e.completion for e in recent) / len(recent)
            recent_dev = sum(e.development for e in recent) / len(recent)
            recent_time = sum(e.time_saved for e in recent) / len(recent)
        else:
            recent_comp = 0
            recent_dev = 0
            recent_time = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_comp = sum(e.completion for e in older) / len(older)
            older_dev = sum(e.development for e in older) / len(older)
            comp_trend = recent_comp - older_comp
            dev_trend = recent_dev - older_dev
        else:
            comp_trend = 0
            dev_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "person_stats": person_stats,
            "best_person": best_person[0],
            "clarity_impact": {
                "high_clarity_completion": round(high_clarity_comp, 2),
                "low_clarity_completion": round(low_clarity_comp, 2),
            },
            "support_impact": {
                "high_support_completion": round(high_support_comp, 2),
                "low_support_completion": round(low_support_comp, 2),
            },
            "abdication_risk": abdication_risk,
            "hoarding_risk": hoarding_risk,
            "avg_completion": round(sum(e.completion for e in self._entries) / len(self._entries), 2),
            "avg_development": round(sum(e.development for e in self._entries) / len(self._entries), 2),
            "avg_time_saved": round(sum(e.time_saved for e in self._entries) / len(self._entries), 1),
            "completion_trend": round(comp_trend, 2),
            "development_trend": round(dev_trend, 2),
            "recent_time_saved": round(recent_time, 1),
        }

    def get_delegation_plan(self, task: str = "", person_capacity: float = 0.5) -> Dict[str, Any]:
        """Get plan."""
        plans = {
            "simple": [
                "What: [specific task]. By when: [date]. Standard: [specific criteria]. Check-in: [when]. That's it.",
                "Delegate the outcome, not the method. 'Get this result.' Not 'Do it this way.'",
                "Set a deadline. People without deadlines drift. Give them one. Then trust them.",
            ],
            "complex": [
                "Break it into milestones. Delegating complexity requires scaffolding. Milestone 1, 2, 3.",
                "Provide context. Why does this matter? What depends on it? Context creates ownership.",
                "Schedule check-ins. Not to micromanage. To remove blockers. 'What's in your way?'",
            ],
            "developmental": [
                "This is slightly above their current level. That's the sweet spot. Challenging but achievable.",
                "Let them struggle. Don't rescue. Struggle is where growth happens. Be available, not intrusive.",
                "Debrief afterwards. What worked? What didn't? What would you do differently? This is the real development.",
            ],
            "urgent": [
                "Urgent + important = you may need to stay closer. But don't take it back. Co-pilot, don't drive.",
                "Provide resources immediately. Urgent tasks need urgent support. Remove every barrier.",
                "Define 'good enough.' Perfectionism kills urgency. What's the minimum viable outcome?",
            ],
            "general": [
                "If they can do it 80% as well as you, delegate it. Your 80% is their growth opportunity.",
                "Delegation is not abdication. You still own the outcome. You're just not doing the work.",
                "The best delegations create future leaders. Not just completed tasks.",
            ],
        }

        if person_capacity < 0.3:
            capacity_note = "Low capacity person. Start with very simple tasks. Heavy support. High clarity."
        elif person_capacity < 0.6:
            capacity_note = "Medium capacity. They can handle moderate complexity. Provide scaffolding."
        else:
            capacity_note = "High capacity. Give them authority, not just tasks. Challenge them."

        return {
            "task": task or "general",
            "person_capacity": person_capacity,
            "plan": random.choice(plans["general"]),
            "capacity_note": capacity_note,
            "principle": "Most people don't delegate because they think it takes longer to explain than to do. They're wrong. The first time, yes. The tenth time, no. Delegation is an investment. You pay upfront in training time. You earn returns in capacity forever. The math only works if you play the long game.",
        }

    def get_delegation_score(self) -> int:
        """Calculate overall delegation health (0-100)."""
        if not self._entries:
            return 30

        # Completion and development
        avg_comp = sum(e.completion for e in self._entries) / len(self._entries)
        avg_dev = sum(e.development for e in self._entries) / len(self._entries)

        # Time saved
        avg_time = sum(e.time_saved for e in self._entries) / len(self._entries)
        time_score = min(10, avg_time / 10)

        # Clarity and support
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_support = sum(e.support for e in self._entries) / len(self._entries)

        # Autonomy (not too high, not too low)
        avg_auto = sum(e.autonomy for e in self._entries) / len(self._entries)
        auto_score = 1 - abs(avg_auto - 0.6) * 2

        # Type variety
        unique_types = len(set(e.delegation_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_comp = sum(e.completion for e in recent) / len(recent)
            recent_dev = sum(e.development for e in recent) / len(recent)
            recent_time = sum(e.time_saved for e in recent) / len(recent)
        else:
            recent_comp = 0
            recent_dev = 0
            recent_time = 0

        # Abdication penalty
        abdication = [e for e in self._entries if e.autonomy > 0.7 and e.support < 0.3]
        abdication_penalty = 10 if len(abdication) > 2 else 0

        # Hoarding penalty
        hoarding = [e for e in self._entries if e.autonomy < 0.3 and e.delegation_type == "task"]
        hoarding_penalty = 10 if len(hoarding) > 2 else 0

        score = (avg_comp * 20) + (avg_dev * 20) + (time_score * 5) + (avg_clarity * 10) + (avg_support * 10) + (auto_score * 10) + (unique_types * 2) + (recent_comp * 10) + (recent_dev * 10) + (recent_time * 5) - abdication_penalty - hoarding_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_completion"] = round(sum(e.completion for e in self._entries) / len(self._entries), 2)
            self._stats["avg_development"] = round(sum(e.development for e in self._entries) / len(self._entries), 2)
            self._stats["avg_time_saved"] = round(sum(e.time_saved for e in self._entries) / len(self._entries), 1)

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

    def _log_entry(self, entry: DelegationEntry):
        try:
            with open(DELEGATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "task": entry.task,
                    "person": entry.person,
                    "delegation_type": entry.delegation_type,
                    "clarity": entry.clarity,
                    "support": entry.support,
                    "autonomy": entry.autonomy,
                    "completion": entry.completion,
                    "development": entry.development,
                    "time_saved": entry.time_saved,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dt_instance: Optional[DelegationTrainer] = None
_dt_lock = threading.Lock()


def get_delegation_trainer() -> DelegationTrainer:
    global _dt_instance
    with _dt_lock:
        if _dt_instance is None:
            _dt_instance = DelegationTrainer()
        return _dt_instance
