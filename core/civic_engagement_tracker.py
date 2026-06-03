"""
LOVE Civic Engagement Tracker — Citizenship Intelligence (Modern AI Pattern)

Most people feel powerless about the world around them. This tracker:

1. ENGAGEMENT TRACKING
   - Record civic activities and their characteristics
   - Track activity types (voting, advocacy, volunteering, local, education)
   - Log impact, learning, and connection from civic participation

2. PATTERN ANALYSIS
   - Identify the user's civic profile (active, informed, disengaged, overwhelmed)
   - Find engagement patterns that create empowerment vs burnout
   - Detect civic disengagement and its causes

3. ENGAGEMENT OPTIMIZATION
   - Suggest civic actions matched to current capacity and interests
   - Provide frameworks for effective advocacy
   - Recommend local engagement as foundation

4. CITIZENSHIP CULTIVATION
   - Track the correlation between engagement and sense of agency
   - Alert when overwhelm is becoming apathy
   - Celebrate moments of genuine civic contribution

Architecture:
- record_activity(activity, type, impact, learning, connection): Log activity
- get_civic_stats(): Get civic pattern analysis
- get_engagement_suggestion(capacity, context): Get suggestion
- get_civic_score(): Calculate overall civic health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "civic_engagement_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CIVIC_LOG = DATA_DIR / "activities.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CivicEntry:
    """A tracked civic activity entry."""
    entry_id: str = ""
    activity: str = ""  # what was done
    activity_type: str = ""  # voting, advocacy, volunteering, local, education
    impact: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    empowerment: float = 0.0  # 0-1
    sustainability: float = 0.0  # 0-1
    hours: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CivicEngagementTracker:
    """
    Intelligent civic engagement tracker with empowerment detection and citizenship cultivation.
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
            "avg_impact": 0.0,
            "avg_empowerment": 0.0,
            "apathy_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_activity(self, activity: str = "", activity_type: str = "", impact: float = 0.0, learning: float = 0.0, connection: float = 0.0, empowerment: float = 0.0, sustainability: float = 0.0, hours: float = 0.0, notes: str = "") -> CivicEntry:
        """Record a civic activity."""
        entry_id = f"cvc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CivicEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            activity_type=activity_type or "general",
            impact=impact,
            learning=learning,
            connection=connection,
            empowerment=empowerment,
            sustainability=sustainability,
            hours=hours,
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

    def get_civic_stats(self) -> Dict[str, Any]:
        """Get civic pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "impact_sum": 0.0, "learning_sum": 0.0, "empowerment_sum": 0.0})
        for e in self._entries:
            by_type[e.activity_type]["count"] += 1
            by_type[e.activity_type]["impact_sum"] += e.impact
            by_type[e.activity_type]["learning_sum"] += e.learning
            by_type[e.activity_type]["empowerment_sum"] += e.empowerment

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_learning": round(data["learning_sum"] / count, 2),
                "avg_empowerment": round(data["empowerment_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_empowerment"]) if type_stats else ("", {})

        # Impact analysis
        high_impact = [e for e in self._entries if e.impact > 0.7]
        low_impact = [e for e in self._entries if e.impact < 0.4]
        if high_impact and low_impact:
            high_impact_empower = sum(e.empowerment for e in high_impact) / len(high_impact)
            low_impact_empower = sum(e.empowerment for e in low_impact) / len(low_impact)
        else:
            high_impact_empower = 0
            low_impact_empower = 0

        # Connection analysis
        high_conn = [e for e in self._entries if e.connection > 0.7]
        low_conn = [e for e in self._entries if e.connection < 0.4]
        if high_conn and low_conn:
            high_conn_sustain = sum(e.sustainability for e in high_conn) / len(high_conn)
            low_conn_sustain = sum(e.sustainability for e in low_conn) / len(low_conn)
        else:
            high_conn_sustain = 0
            low_conn_sustain = 0

        # Apathy risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_empower = sum(e.empowerment for e in recent) / len(recent)
            recent_impact = sum(e.impact for e in recent) / len(recent)
            apathy_risk = recent_empower < 0.3 and recent_impact < 0.3
        else:
            apathy_risk = True

        return {
            "total_entries": len(self._entries),
            "total_hours": round(sum(e.hours for e in self._entries), 1),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "impact_effect": {
                "high_impact_empowerment": round(high_impact_empower, 2),
                "low_impact_empowerment": round(low_impact_empower, 2),
            },
            "connection_effect": {
                "high_connection_sustainability": round(high_conn_sustain, 2),
                "low_connection_sustainability": round(low_conn_sustain, 2),
            },
            "apathy_risk": apathy_risk,
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 2),
            "avg_empowerment": round(sum(e.empowerment for e in self._entries) / len(self._entries), 2),
        }

    def get_engagement_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get engagement suggestion."""
        suggestions = [
            "Start local. Attend a town hall. Join a neighborhood group. Volunteer at a local organization. Local engagement is where you have the most power. And where you see the most direct results.",
            "Vote in every election. Not just the big ones. School board. City council. Local elections have more impact on your daily life than national ones. And they need more voters.",
            "Educate yourself before you advocate. Read about the issue from multiple perspectives. Talk to people affected. The most effective advocates are the most informed ones.",
            "Use your specific skills. Lawyer? Pro bono. Writer? Advocacy. Engineer? Infrastructure. Everyone has something to offer. Find your civic niche.",
            "Speak up in your circles. When someone says something harmful, challenge it. Not aggressively. Gently. Silence is permission. Your voice matters in small conversations too.",
            "Support organizations doing good work. Time. Money. Skills. Amplification. You don't have to start something new. You can strengthen what already exists.",
            "Run for something. School board. Neighborhood association. Local office. Democracy needs good people willing to serve. That might be you.",
            "Teach others what you've learned. The best way to solidify your own civic education is to share it. Host a discussion. Write a post. Have a conversation.",
            "Don't let perfect be the enemy of good. The system is flawed. Everything is flawed. Do what you can with what you have. Partial engagement is better than total disengagement.",
            "Civic engagement is not a hobby. It's a responsibility. Democracy is not a spectator sport. It requires participants. Be one.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One informed vote. One local action. One conversation. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Regular engagement. A cause. A group. A recurring commitment."
        else:
            capacity_note = "Good capacity. Major civic action. Leadership. Advocacy. You have the energy to make real systemic contribution."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "The world is changed by people who show up. Not by people who complain on the internet. Not by people who wait for the perfect candidate. By people who vote. Who volunteer. Who speak up. Who run for office. Who do the boring, unglamorous work of maintaining a society. Democracy is fragile. It requires care. It requires attention. It requires you. The person who thinks their contribution doesn't matter is the person whose absence makes the difference. Be present. Be active. Be a citizen.",
        }

    def get_civic_score(self) -> int:
        """Calculate overall civic health (0-100)."""
        if not self._entries:
            return 25

        avg_impact = sum(e.impact for e in self._entries) / len(self._entries)
        avg_empower = sum(e.empowerment for e in self._entries) / len(self._entries)
        avg_learning = sum(e.learning for e in self._entries) / len(self._entries)
        avg_connection = sum(e.connection for e in self._entries) / len(self._entries)
        avg_sustain = sum(e.sustainability for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_empower = sum(e.empowerment for e in recent) / len(recent)
            recent_impact = sum(e.impact for e in recent) / len(recent)
        else:
            recent_empower = 0
            recent_impact = 0

        # Apathy penalty
        apathy_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if len(last_90) < 2:
            apathy_penalty = 15

        # Type variety
        unique_types = len(set(e.activity_type for e in self._entries))

        score = (avg_impact * 25) + (avg_empower * 20) + (avg_learning * 15) + (avg_connection * 10) + (avg_sustain * 10) + (recent_empower * 10) + (recent_impact * 5) + (unique_types * 2) - apathy_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_impact"] = round(sum(e.impact for e in self._entries) / len(self._entries), 2)
            self._stats["avg_empowerment"] = round(sum(e.empowerment for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_empower = sum(e.empowerment for e in recent) / len(recent)
                recent_impact = sum(e.impact for e in recent) / len(recent)
                self._stats["apathy_risk"] = recent_empower < 0.3 and recent_impact < 0.3
            else:
                self._stats["apathy_risk"] = True

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.civic_engagement_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.civic_engagement_tracker")

    def _log_entry(self, entry: CivicEntry):
        try:
            with open(CIVIC_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "activity_type": entry.activity_type,
                    "impact": entry.impact,
                    "empowerment": entry.empowerment,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.civic_engagement_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cet_instance: Optional[CivicEngagementTracker] = None
_cet_lock = threading.Lock()


def get_civic_engagement_tracker() -> CivicEngagementTracker:
    global _cet_instance
    with _cet_lock:
        if _cet_instance is None:
            _cet_instance = CivicEngagementTracker()
        return _cet_instance
