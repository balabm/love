"""
LOVE Flow State Coach — Optimal Experience Intelligence (Modern AI Pattern)

Most people rarely experience flow. This coach:

1. FLOW TRACKING
   - Record flow sessions with challenge-skill balance, immersion, and timelessness
   - Track what triggers flow and what interrupts it
   - Log flow recovery time after interruptions

2. PATTERN ANALYSIS
   - Identify the user's flow triggers (activities, environments, times, mindsets)
   - Find flow blockers (distractions, mismatched challenge, anxiety, boredom)
   - Detect the optimal challenge-skill ratio for flow

3. FLOW FACILITATION
   - Suggest pre-flow rituals and environment setups
   - Provide real-time flow protection strategies
   - Recommend flow-compatible task design

4. GROWTH SUPPORT
   - Track flow frequency and depth over time
   - Suggest skill upgrades to match growing challenge appetite
   - Celebrate flow milestones

Architecture:
- record_flow_session(activity, challenge, skill, immersion, timelessness): Log session
- get_flow_stats(): Get flow pattern analysis
- get_flow_suggestion(current_task, skill_level): Get flow facilitation
- get_flow_score(): Calculate overall flow health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "flow_state_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FLOW_LOG = DATA_DIR / "flow.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class FlowSession:
    """A tracked flow session."""
    session_id: str = ""
    activity: str = ""
    challenge_level: float = 0.5  # 0-1
    skill_level: float = 0.5  # 0-1
    immersion: float = 0.5  # 0-1, how absorbed
    timelessness: float = 0.5  # 0-1, how time distorted
    clarity: float = 0.5  # 0-1, how clear the next step was
    energy_after: float = 0.5  # 0-1
    interruptions: int = 0
    duration_minutes: float = 0.0
    pre_flow_ritual: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class FlowStateCoach:
    """
    Intelligent flow state coach with challenge-skill optimization and interruption recovery.
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
            "avg_immersion": 0.0,
            "avg_timelessness": 0.0,
            "optimal_challenge_skill_ratio": 0.0,
            "flow_rate": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_flow_session(self, activity: str = "", challenge: float = 0.5, skill: float = 0.5, immersion: float = 0.5, timelessness: float = 0.5, clarity: float = 0.5, energy_after: float = 0.5, interruptions: int = 0, duration: float = 0, ritual: str = "", notes: str = "") -> FlowSession:
        """Record a flow session."""
        session_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = FlowSession(
            session_id=session_id,
            activity=activity or "unspecified",
            challenge_level=challenge,
            skill_level=skill,
            immersion=immersion,
            timelessness=timelessness,
            clarity=clarity,
            energy_after=energy_after,
            interruptions=interruptions,
            duration_minutes=duration,
            pre_flow_ritual=ritual,
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

    def get_flow_stats(self) -> Dict[str, Any]:
        """Get flow pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Flow detection (immersion > 0.7 and timelessness > 0.5)
        flow_sessions = [s for s in self._sessions if s.immersion > 0.7 and s.timelessness > 0.5]
        flow_rate = len(flow_sessions) / len(self._sessions)

        # Activity analysis
        by_activity = defaultdict(lambda: {"count": 0, "immersion_sum": 0.0, "timelessness_sum": 0.0, "flow_count": 0})
        for s in self._sessions:
            by_activity[s.activity]["count"] += 1
            by_activity[s.activity]["immersion_sum"] += s.immersion
            by_activity[s.activity]["timelessness_sum"] += s.timelessness
            if s.immersion > 0.7 and s.timelessness > 0.5:
                by_activity[s.activity]["flow_count"] += 1

        activity_stats = {}
        for a, data in by_activity.items():
            count = data["count"]
            activity_stats[a] = {
                "count": count,
                "avg_immersion": round(data["immersion_sum"] / count, 2),
                "avg_timelessness": round(data["timelessness_sum"] / count, 2),
                "flow_rate": round(data["flow_count"] / count, 2),
            }

        # Challenge-skill analysis
        ratios = [s.challenge_level / max(0.1, s.skill_level) for s in self._sessions]
        avg_ratio = sum(ratios) / len(ratios)
        optimal_ratio = 1.05  # slightly above skill

        # Best sessions
        best = max(self._sessions, key=lambda s: s.immersion + s.timelessness) if self._sessions else None

        # Interruption impact
        interrupted = [s for s in self._sessions if s.interruptions > 0]
        if interrupted:
            avg_immersion_with = sum(s.immersion for s in interrupted) / len(interrupted)
            not_interrupted = [s for s in self._sessions if s.interruptions == 0]
            if not_interrupted:
                avg_immersion_without = sum(s.immersion for s in not_interrupted) / len(not_interrupted)
                interruption_cost = avg_immersion_without - avg_immersion_with
            else:
                interruption_cost = 0
        else:
            interruption_cost = 0

        return {
            "total_sessions": len(self._sessions),
            "flow_sessions": len(flow_sessions),
            "flow_rate": round(flow_rate, 2),
            "activity_stats": activity_stats,
            "avg_challenge_skill_ratio": round(avg_ratio, 2),
            "optimal_ratio": optimal_ratio,
            "best_activity": best.activity if best else "",
            "interruption_cost": round(interruption_cost, 2),
            "avg_duration": round(sum(s.duration_minutes for s in self._sessions) / len(self._sessions), 1),
        }

    def get_flow_suggestion(self, current_task: str = "", skill_level: float = 0.5, time_available: float = 60) -> Dict[str, Any]:
        """Get flow facilitation."""
        # Determine if challenge needs adjustment
        if skill_level > 0.8:
            challenge_adjustment = "Increase challenge. You're bored because it's too easy. Add constraints, speed, or complexity."
        elif skill_level < 0.3:
            challenge_adjustment = "Lower challenge. You're anxious because it's too hard. Break it down, get help, or practice fundamentals."
        else:
            challenge_adjustment = "Challenge is well-matched. Focus on removing distractions and deepening immersion."

        rituals = [
            "Put phone in another room",
            "Set a visible timer for the session",
            "Drink water, use bathroom, grab snack before starting",
            "Put on noise-canceling headphones with one specific playlist",
            "Write down your current worry on paper, then put it away",
            "Set a clear, single intention for this session",
        ]

        protections = [
            "Close all non-essential tabs and apps",
            "Set status to 'Do Not Disturb' on all platforms",
            "Tell someone you won't be available for X minutes",
            "Use a physical 'flow in progress' sign if co-located",
            "Batch all potential interruptions before starting",
        ]

        return {
            "task": current_task or "unspecified",
            "skill_level": skill_level,
            "challenge_adjustment": challenge_adjustment,
            "pre_flow_ritual": random.choice(rituals),
            "protection": random.choice(protections),
            "time_block": time_available,
            "reminder": "Flow requires surrender. Stop checking the clock. Let the work pull you in.",
        }

    def get_flow_score(self) -> int:
        """Calculate overall flow health (0-100)."""
        if not self._sessions:
            return 35

        # Flow rate
        flow_sessions = [s for s in self._sessions if s.immersion > 0.7 and s.timelessness > 0.5]
        flow_rate = len(flow_sessions) / len(self._sessions)

        # Average immersion
        avg_immersion = sum(s.immersion for s in self._sessions) / len(self._sessions)

        # Average timelessness
        avg_timelessness = sum(s.timelessness for s in self._sessions) / len(self._sessions)

        # Duration (deeper flow tends to be longer)
        avg_duration = sum(s.duration_minutes for s in self._sessions) / len(self._sessions)

        # Recent activity
        recent = [s for s in self._sessions if s.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        recent_bonus = min(15, len(recent) * 3)

        # Interruption management
        interrupted_rate = sum(1 for s in self._sessions if s.interruptions > 0) / len(self._sessions)

        score = (flow_rate * 25) + (avg_immersion * 20) + (avg_timelessness * 15) + (min(avg_duration / 60, 1) * 10) + recent_bonus + ((1 - interrupted_rate) * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_immersion"] = round(sum(s.immersion for s in self._sessions) / len(self._sessions), 2)
            self._stats["avg_timelessness"] = round(sum(s.timelessness for s in self._sessions) / len(self._sessions), 2)
            
            flow_sessions = [s for s in self._sessions if s.immersion > 0.7 and s.timelessness > 0.5]
            self._stats["flow_rate"] = round(len(flow_sessions) / len(self._sessions), 2)

            ratios = [s.challenge_level / max(0.1, s.skill_level) for s in self._sessions]
            self._stats["optimal_challenge_skill_ratio"] = round(sum(ratios) / len(ratios), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.flow_state_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.flow_state_coach")

    def _log_session(self, session: FlowSession):
        try:
            with open(FLOW_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "activity": session.activity,
                    "challenge": session.challenge_level,
                    "skill": session.skill_level,
                    "immersion": session.immersion,
                    "timelessness": session.timelessness,
                    "interruptions": session.interruptions,
                    "duration": session.duration_minutes,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.flow_state_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_fsc_instance: Optional[FlowStateCoach] = None
_fsc_lock = threading.Lock()


def get_flow_state_coach() -> FlowStateCoach:
    global _fsc_instance
    with _fsc_lock:
        if _fsc_instance is None:
            _fsc_instance = FlowStateCoach()
        return _fsc_instance
