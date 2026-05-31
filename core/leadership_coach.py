"""
LOVE Leadership Coach — Influence Intelligence (Modern AI Pattern)

Most leadership fails because it's performative, not substantive. This coach:

1. LEADERSHIP TRACKING
   - Record leadership actions and their characteristics
   - Track leadership types (visionary, servant, democratic, coaching, pacesetting)
   - Log team outcomes and their effects on performance and morale

2. PATTERN ANALYSIS
   - Identify the user's leadership profile (commander, collaborator, coach, avoider)
   - Find leadership approaches that create engaged teams
   - Detect leadership avoidance or micromanagement patterns

3. LEADERSHIP BUILDING
   - Suggest leadership actions matched to team context
   - Provide feedback and delegation frameworks
   - Recommendation team development practices

4. INFLUENCE CULTIVATION
   - Track the correlation between leadership style and team outcomes
   - Alert when leadership is becoming authoritarian or absent
   - Celebrate moments of effective influence

Architecture:
- record_action(action, type, team, outcome): Log action
- get_leadership_stats(): Get leadership pattern analysis
- get_leadership_action(context, team_size): Get action
- get_leadership_score(): Calculate overall leadership health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "leadership_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEADERSHIP_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class LeadershipEntry:
    """A tracked leadership entry."""
    entry_id: str = ""
    action: str = ""  # what was done
    leadership_type: str = ""  # visionary, servant, democratic, coaching, pacesetting
    team: str = ""  # who was led
    team_size: int = 0
    autonomy_given: float = 0.5  # 0-1
    support_provided: float = 0.5  # 0-1
    clarity: float = 0.5  # 0-1
    team_performance: float = 0.5  # 0-1
    team_morale: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LeadershipCoach:
    """
    Intelligent leadership coach with team outcome tracking and style optimization.
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
            "avg_performance": 0.0,
            "avg_morale": 0.0,
            "micromanagement_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", leadership_type: str = "", team: str = "", team_size: int = 0, autonomy_given: float = 0.5, support_provided: float = 0.5, clarity: float = 0.5, team_performance: float = 0.5, team_morale: float = 0.5, notes: str = "") -> LeadershipEntry:
        """Record a leadership entry."""
        entry_id = f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = LeadershipEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            leadership_type=leadership_type or "coaching",
            team=team or "general",
            team_size=team_size,
            autonomy_given=autonomy_given,
            support_provided=support_provided,
            clarity=clarity,
            team_performance=team_performance,
            team_morale=team_morale,
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

    def get_leadership_stats(self) -> Dict[str, Any]:
        """Get leadership pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "perf_sum": 0.0, "morale_sum": 0.0, "auto_sum": 0.0, "support_sum": 0.0})
        for e in self._entries:
            by_type[e.leadership_type]["count"] += 1
            by_type[e.leadership_type]["perf_sum"] += e.team_performance
            by_type[e.leadership_type]["morale_sum"] += e.team_morale
            by_type[e.leadership_type]["auto_sum"] += e.autonomy_given
            by_type[e.leadership_type]["support_sum"] += e.support_provided

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_performance": round(data["perf_sum"] / count, 2),
                "avg_morale": round(data["morale_sum"] / count, 2),
                "avg_autonomy": round(data["auto_sum"] / count, 2),
                "avg_support": round(data["support_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_performance"] + x[1]["avg_morale"]) if type_stats else ("", {})

        # Team analysis
        by_team = defaultdict(lambda: {"count": 0, "perf_sum": 0.0, "morale_sum": 0.0})
        for e in self._entries:
            if e.team:
                by_team[e.team]["count"] += 1
                by_team[e.team]["perf_sum"] += e.team_performance
                by_team[e.team]["morale_sum"] += e.team_morale

        team_stats = {}
        for t, data in by_team.items():
            count = data["count"]
            if count >= 2:
                team_stats[t] = {
                    "count": count,
                    "avg_performance": round(data["perf_sum"] / count, 2),
                    "avg_morale": round(data["morale_sum"] / count, 2),
                }

        # Autonomy vs support balance
        high_auto = [e for e in self._entries if e.autonomy_given > 0.7]
        low_auto = [e for e in self._entries if e.autonomy_given < 0.4]
        if high_auto and low_auto:
            high_auto_perf = sum(e.team_performance for e in high_auto) / len(high_auto)
            low_auto_perf = sum(e.team_performance for e in low_auto) / len(low_auto)
            high_auto_morale = sum(e.team_morale for e in high_auto) / len(high_auto)
            low_auto_morale = sum(e.team_morale for e in low_auto) / len(low_auto)
        else:
            high_auto_perf = 0
            low_auto_perf = 0
            high_auto_morale = 0
            low_auto_morale = 0

        # Clarity impact
        high_clarity = [e for e in self._entries if e.clarity > 0.7]
        low_clarity = [e for e in self._entries if e.clarity < 0.4]
        if high_clarity and low_clarity:
            high_clarity_perf = sum(e.team_performance for e in high_clarity) / len(high_clarity)
            low_clarity_perf = sum(e.team_performance for e in low_clarity) / len(low_clarity)
        else:
            high_clarity_perf = 0
            low_clarity_perf = 0

        # Micromanagement detection
        low_auto_high_team_size = [e for e in self._entries if e.autonomy_given < 0.4 and e.team_size > 3]
        if low_auto_high_team_size:
            micromanagement_risk = True
        else:
            micromanagement_risk = False

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_perf = sum(e.team_performance for e in recent) / len(recent)
            recent_morale = sum(e.team_morale for e in recent) / len(recent)
            recent_auto = sum(e.autonomy_given for e in recent) / len(recent)
            recent_support = sum(e.support_provided for e in recent) / len(recent)
        else:
            recent_perf = 0
            recent_morale = 0
            recent_auto = 0
            recent_support = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_perf = sum(e.team_performance for e in older) / len(older)
            older_morale = sum(e.team_morale for e in older) / len(older)
            perf_trend = recent_perf - older_perf
            morale_trend = recent_morale - older_morale
        else:
            perf_trend = 0
            morale_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_leadership_type": best_type[0],
            "team_stats": team_stats,
            "autonomy_impact": {
                "high_autonomy_performance": round(high_auto_perf, 2),
                "low_autonomy_performance": round(low_auto_perf, 2),
                "high_autonomy_morale": round(high_auto_morale, 2),
                "low_autonomy_morale": round(low_auto_morale, 2),
            },
            "clarity_impact": {
                "high_clarity_performance": round(high_clarity_perf, 2),
                "low_clarity_performance": round(low_clarity_perf, 2),
            },
            "micromanagement_risk": micromanagement_risk,
            "avg_performance": round(sum(e.team_performance for e in self._entries) / len(self._entries), 2),
            "avg_morale": round(sum(e.team_morale for e in self._entries) / len(self._entries), 2),
            "performance_trend": round(perf_trend, 2),
            "morale_trend": round(morale_trend, 2),
            "recent_autonomy": round(recent_auto, 2),
            "recent_support": round(recent_support, 2),
        }

    def get_leadership_action(self, context: str = "", team_size: int = 5) -> Dict[str, Any]:
        """Get action."""
        actions = {
            "crisis": [
                "In crisis, clarity beats consensus. Decide fast. Communicate clearly. Course-correct later.",
                "Be visible. Your presence is the message. Show up before you're asked.",
                "Protect your team from chaos. Absorb uncertainty. Output calm.",
            ],
            "growth": [
                "Delegate the work that someone else can do 80% as well. Free yourself for what only you can do.",
                "Ask: 'What do you need from me?' Then provide it. Growth requires support.",
                "Celebrate progress loudly. People repeat what gets rewarded.",
            ],
            "stagnation": [
                "Change one thing. One process. One assumption. Momentum starts with disruption.",
                "Have the hard conversation. Stagnation is often a people problem dressed as a strategy problem.",
                "Bring in outside perspective. The fish is the last to discover water.",
            ],
            "conflict": [
                "Address it directly. Not in email. In person. Today.",
                "Listen to both sides separately first. Then together. Order matters.",
                "Find the shared goal. Conflict is usually about methods, not outcomes.",
            ],
            "general": [
                "Leadership is not a title. It's behavior. Anyone can lead from anywhere.",
                "The best leaders create more leaders. Not more followers.",
                "Your team doesn't need you to be perfect. They need you to be present.",
            ],
        }

        selected = actions.get(context, actions["general"])

        if team_size <= 3:
            size_note = "Small team. Deep relationship leadership works here. Know everyone personally."
        elif team_size <= 10:
            size_note = "Medium team. Balance personal attention with systems. Process becomes important."
        else:
            size_note = "Large team. Culture and systems are your levers. You can't know everyone. You can shape the environment."

        return {
            "context": context or "general",
            "team_size": team_size,
            "action": random.choice(selected),
            "size_note": size_note,
            "principle": "Most people think leadership is about having answers. It's not. It's about asking better questions. It's about creating conditions where others can thrive. The best leaders are invisible — their teams perform well without constant direction. That's the goal: to make yourself unnecessary.",
        }

    def get_leadership_score(self) -> int:
        """Calculate overall leadership health (0-100)."""
        if not self._entries:
            return 40

        # Performance and morale
        avg_perf = sum(e.team_performance for e in self._entries) / len(self._entries)
        avg_morale = sum(e.team_morale for e in self._entries) / len(self._entries)

        # Autonomy and support balance
        avg_auto = sum(e.autonomy_given for e in self._entries) / len(self._entries)
        avg_support = sum(e.support_provided for e in self._entries) / len(self._entries)

        # Clarity
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.leadership_type for e in self._entries))

        # Team variety
        unique_teams = len(set(e.team for e in self._entries if e.team))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_perf = sum(e.team_performance for e in recent) / len(recent)
            recent_morale = sum(e.team_morale for e in recent) / len(recent)
            recent_auto = sum(e.autonomy_given for e in recent) / len(recent)
            recent_support = sum(e.support_provided for e in recent) / len(recent)
        else:
            recent_perf = 0
            recent_morale = 0
            recent_auto = 0
            recent_support = 0

        # Micromanagement penalty
        micro_penalty = 0
        low_auto = [e for e in self._entries if e.autonomy_given < 0.4 and e.team_size > 3]
        if low_auto:
            micro_penalty = 10

        score = (avg_perf * 25) + (avg_morale * 25) + (avg_auto * 10) + (avg_support * 10) + (avg_clarity * 10) + (unique_types * 2) + (unique_teams * 2) + (recent_perf * 10) + (recent_morale * 10) + (recent_auto * 5) + (recent_support * 5) - micro_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_performance"] = round(sum(e.team_performance for e in self._entries) / len(self._entries), 2)
            self._stats["avg_morale"] = round(sum(e.team_morale for e in self._entries) / len(self._entries), 2)

            low_auto = [e for e in self._entries if e.autonomy_given < 0.4 and e.team_size > 3]
            self._stats["micromanagement_risk"] = len(low_auto) > 0

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

    def _log_entry(self, entry: LeadershipEntry):
        try:
            with open(LEADERSHIP_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "leadership_type": entry.leadership_type,
                    "team": entry.team,
                    "team_size": entry.team_size,
                    "autonomy_given": entry.autonomy_given,
                    "support_provided": entry.support_provided,
                    "clarity": entry.clarity,
                    "team_performance": entry.team_performance,
                    "team_morale": entry.team_morale,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lc_instance: Optional[LeadershipCoach] = None
_lc_lock = threading.Lock()


def get_leadership_coach() -> LeadershipCoach:
    global _lc_instance
    with _lc_lock:
        if _lc_instance is None:
            _lc_instance = LeadershipCoach()
        return _lc_instance
