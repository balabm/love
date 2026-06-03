"""
LOVE Volunteer Coordinator — Service Intelligence (Modern AI Pattern)

Most people want to help but don't know where to start. This coordinator:

1. VOLUNTEER TRACKING
   - Record volunteer activities and their characteristics
   - Track volunteer types (direct service, skill-based, advocacy, creation)
   - Log satisfaction, impact, and sustainability of volunteer work

2. PATTERN ANALYSIS
   - Identify the user's volunteer profile (sporadic, committed, burnout-prone, sustainable)
   - Find volunteer patterns that create lasting fulfillment
   - Detect volunteer burnout and its warning signs

3. VOLUNTEER OPTIMIZATION
   - Suggest volunteer opportunities matched to skills and capacity
   - Provide frameworks for sustainable service
   - Recommend commitment levels that don't deplete

4. SERVICE CULTIVATION
   - Track the correlation between volunteering and life satisfaction
   - Alert when service has become obligation rather than gift
   - Celebrate moments of genuine contribution

Architecture:
- record_activity(activity, type, hours, satisfaction, impact): Log activity
- get_volunteer_stats(): Get volunteer pattern analysis
- get_opportunity_suggestion(skills, capacity, context): Get suggestion
- get_volunteer_score(): Calculate overall volunteer health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "volunteer_coordinator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VOLUNTEER_LOG = DATA_DIR / "activities.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class VolunteerEntry:
    """A tracked volunteer activity."""
    entry_id: str = ""
    activity: str = ""  # what was done
    volunteer_type: str = ""  # direct_service, skill_based, advocacy, creation
    hours: float = 0.0
    satisfaction: float = 0.5  # 0-1
    impact: float = 0.0  # 0-1
    sustainability: float = 0.0  # 0-1 will this continue?
    alignment: float = 0.0  # 0-1 alignment with skills/values
    energy_change: float = 0.0  # -1 to 1 (negative = draining)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VolunteerCoordinator:
    """
    Intelligent volunteer coordinator with burnout detection and sustainable service optimization.
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
            "avg_satisfaction": 0.0,
            "avg_energy_change": 0.0,
            "burnout_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_activity(self, activity: str = "", volunteer_type: str = "", hours: float = 0.0, satisfaction: float = 0.5, impact: float = 0.0, sustainability: float = 0.0, alignment: float = 0.0, energy_change: float = 0.0, notes: str = "") -> VolunteerEntry:
        """Record a volunteer activity."""
        entry_id = f"vol_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = VolunteerEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            volunteer_type=volunteer_type or "direct_service",
            hours=hours,
            satisfaction=satisfaction,
            impact=impact,
            sustainability=sustainability,
            alignment=alignment,
            energy_change=energy_change,
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

    def get_volunteer_stats(self) -> Dict[str, Any]:
        """Get volunteer pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "satisfaction_sum": 0.0, "impact_sum": 0.0, "energy_sum": 0.0})
        for e in self._entries:
            by_type[e.volunteer_type]["count"] += 1
            by_type[e.volunteer_type]["satisfaction_sum"] += e.satisfaction
            by_type[e.volunteer_type]["impact_sum"] += e.impact
            by_type[e.volunteer_type]["energy_sum"] += e.energy_change

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_energy_change": round(data["energy_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_satisfaction"]) if type_stats else ("", {})

        # Satisfaction vs sustainability
        high_sat = [e for e in self._entries if e.satisfaction > 0.7]
        low_sat = [e for e in self._entries if e.satisfaction < 0.4]
        if high_sat and low_sat:
            high_sat_sustain = sum(e.sustainability for e in high_sat) / len(high_sat)
            low_sat_sustain = sum(e.sustainability for e in low_sat) / len(low_sat)
        else:
            high_sat_sustain = 0
            low_sat_sustain = 0

        # Alignment analysis
        high_align = [e for e in self._entries if e.alignment > 0.7]
        low_align = [e for e in self._entries if e.alignment < 0.4]
        if high_align and low_align:
            high_align_sat = sum(e.satisfaction for e in high_align) / len(high_align)
            low_align_sat = sum(e.satisfaction for e in low_align) / len(low_align)
            high_align_energy = sum(e.energy_change for e in high_align) / len(high_align)
            low_align_energy = sum(e.energy_change for e in low_align) / len(low_align)
        else:
            high_align_sat = 0
            low_align_sat = 0
            high_align_energy = 0
            low_align_energy = 0

        # Burnout detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=60)).isoformat()]
        if recent:
            recent_energy = sum(e.energy_change for e in recent) / len(recent)
            recent_hours = sum(e.hours for e in recent)
            burnout_risk = recent_energy < -0.3 and recent_hours > 20
        else:
            burnout_risk = False

        # Hours trend
        if len(self._entries) > 5:
            older = list(self._entries)[-10:-5]
            recent_entries = list(self._entries)[-5:]
            if older and recent_entries:
                older_hours = sum(e.hours for e in older) / len(older)
                recent_hours_avg = sum(e.hours for e in recent_entries) / len(recent_entries)
                hours_trend = recent_hours_avg - older_hours
            else:
                hours_trend = 0
        else:
            hours_trend = 0

        return {
            "total_entries": len(self._entries),
            "total_hours": round(sum(e.hours for e in self._entries), 1),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "satisfaction_impact": {
                "high_satisfaction_sustainability": round(high_sat_sustain, 2),
                "low_satisfaction_sustainability": round(low_sat_sustain, 2),
            },
            "alignment_effect": {
                "high_alignment_satisfaction": round(high_align_sat, 2),
                "low_alignment_satisfaction": round(low_align_sat, 2),
                "high_alignment_energy": round(high_align_energy, 2),
                "low_alignment_energy": round(low_align_energy, 2),
            },
            "burnout_risk": burnout_risk,
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
            "avg_energy_change": round(sum(e.energy_change for e in self._entries) / len(self._entries), 2),
            "hours_trend": round(hours_trend, 2),
        }

    def get_opportunity_suggestion(self, skills: str = "", capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get volunteer opportunity suggestion."""
        suggestions = [
            "The best volunteer work is not the most impressive. It's the most sustainable. One hour a week for a year is worth more than a weekend blitz that burns you out.",
            "Match your volunteering to your energy, not just your skills. If you're drained from work, don't volunteer doing the same thing. Do something physical. Or creative. Or social.",
            "Start smaller than you think you should. Most people overcommit to volunteering and then quit. Underpromise. Overdeliver. Stay for the long term.",
            "Volunteer for the cause, not the recognition. The moment you need applause for your service, it becomes performance. Service is most pure when it's invisible.",
            "Teach what you know. Not in a classroom. Just to one person. One skill transfer changes two lives. Yours and theirs.",
            "Advocacy is volunteering. Speaking up. Sharing information. Contacting representatives. Your voice has power. Use it for people who have less.",
            "Physical labor is underrated. Building. Cleaning. Moving. Gardening. The body needs to serve too. Not just the mind.",
            "Volunteer with people very different from you. Age. Background. Belief. Serving across difference destroys prejudice faster than any conversation.",
            "Create something for a cause. A website. A flyer. A video. A tool. Skill-based volunteering leverages what you do best.",
            "Show up. That's 90% of volunteering. Most causes don't need heroes. They need reliable people who do what they said they'd do.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Micro-volunteering. One hour. One task. One favor. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Regular commitment. Weekly or monthly. Something you can sustain."
        else:
            capacity_note = "Good capacity. Significant commitment. Project-based. Skill-based. You have the energy to make a real difference."

        return {
            "skills": skills or "general",
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Volunteering is not about being a good person. It's about being a person who knows they're part of something larger. The healthiest people have some form of service in their lives. Not because they're saints. Because humans need to feel useful. The paradox of service is that you think you're giving, but you're actually receiving. Purpose. Connection. Perspective. The sense that your life matters to someone else. That's not charity. That's sanity.",
        }

    def get_volunteer_score(self) -> int:
        """Calculate overall volunteer health (0-100)."""
        if not self._entries:
            return 25

        avg_satisfaction = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_impact = sum(e.impact for e in self._entries) / len(self._entries)
        avg_sustainability = sum(e.sustainability for e in self._entries) / len(self._entries)
        avg_alignment = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy_change for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-10:]
        if recent:
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            recent_energy = sum(e.energy_change for e in recent) / len(recent)
        else:
            recent_sat = 0
            recent_energy = 0

        # Burnout penalty
        burnout_penalty = 0
        last_60 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=60)).isoformat()]
        if last_60:
            recent_energy_60 = sum(e.energy_change for e in last_60) / len(last_60)
            recent_hours = sum(e.hours for e in last_60)
            if recent_energy_60 < -0.3 and recent_hours > 20:
                burnout_penalty = 20

        # Type variety
        unique_types = len(set(e.volunteer_type for e in self._entries))

        score = (avg_satisfaction * 25) + (avg_impact * 20) + (avg_sustainability * 15) + (avg_alignment * 15) + (recent_sat * 10) + (recent_energy * 5) + (unique_types * 2) - (avg_energy * -5) - burnout_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)
            self._stats["avg_energy_change"] = round(sum(e.energy_change for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=60)).isoformat()]
            if recent:
                recent_energy = sum(e.energy_change for e in recent) / len(recent)
                recent_hours = sum(e.hours for e in recent)
                self._stats["burnout_risk"] = recent_energy < -0.3 and recent_hours > 20
            else:
                self._stats["burnout_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.volunteer_coordinator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.volunteer_coordinator")

    def _log_entry(self, entry: VolunteerEntry):
        try:
            with open(VOLUNTEER_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "volunteer_type": entry.volunteer_type,
                    "hours": entry.hours,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.volunteer_coordinator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vc_instance: Optional[VolunteerCoordinator] = None
_vc_lock = threading.Lock()


def get_volunteer_coordinator() -> VolunteerCoordinator:
    global _vc_instance
    with _vc_lock:
        if _vc_instance is None:
            _vc_instance = VolunteerCoordinator()
        return _vc_instance
