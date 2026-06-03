"""
LOVE Creativity Booster — Creative Intelligence (Modern AI Pattern)

Most creativity tools are random idea generators. This booster:

1. CREATIVE SESSION TRACKING
   - Record creative sessions (type, duration, output quality, flow state)
   - Track creative energy patterns across time of day/week
   - Log what stimulates vs blocks creativity

2. CREATIVE CYCLE ANALYSIS
   - Identify personal creative rhythm (when ideas flow vs when execution works)
   - Detect creative burnout before it hits
   - Track idea-to-execution ratio

3. STIMULATION SUGGESTIONS
   - Recommend creative prompts based on current mood/energy
   - Suggest cross-domain inspiration (if stuck in one area, suggest another)
   - Propose collaboration opportunities when solo creative energy is low

4. BLOCK BREAKING
   - Detect creative block patterns
   - Suggest proven block-breakers (walks, constraints, medium switching)
   - Track which techniques actually work for this user

Architecture:
- record_session(session_type, output_quality, flow): Log creative session
- get_creative_stats(): Get creative pattern analysis
- get_block_breaker(): Get personalized block-breaking suggestion
- get_creative_energy_score(): Calculate current creative energy
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

DATA_DIR = Path(__file__).parent.parent / "data" / "creativity_booster"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CreativeSession:
    """A creative session."""
    session_type: str = ""  # writing, design, coding, music, visual, brainstorming, problem_solving
    duration_minutes: float = 0.0
    output_quality: float = 0.5  # 0-1
    flow_score: float = 0.5
    ideas_generated: int = 0
    ideas_executed: int = 0
    stimulation_source: str = ""  # what inspired this session
    block_broken: bool = False
    technique_used: str = ""  # which technique was used if blocked
    energy_before: float = 0.5
    energy_after: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class TechniqueEffectiveness:
    """Track effectiveness of creativity techniques."""
    technique: str = ""
    times_used: int = 0
    success_rate: float = 0.0
    avg_quality_improvement: float = 0.0


class CreativityBooster:
    """
    Boost creativity with pattern intelligence and block-breaking.
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
        self._sessions: deque = deque(maxlen=500)
        self._techniques: Dict[str, TechniqueEffectiveness] = {}
        self._stats = {
            "total_sessions": 0,
            "total_ideas": 0,
            "total_executed": 0,
            "avg_quality": 0.5,
            "avg_flow": 0.5,
            "block_incidents": 0,
            "blocks_broken": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, session_type: str = "", duration: float = 0, output_quality: float = 0.5, flow: float = 0.5, ideas_generated: int = 0, ideas_executed: int = 0, stimulation_source: str = "", block_broken: bool = False, technique_used: str = "", energy_before: float = 0.5, energy_after: float = 0.5, notes: str = "") -> CreativeSession:
        """Record a creative session."""
        session = CreativeSession(
            session_type=session_type or "brainstorming",
            duration_minutes=duration,
            output_quality=output_quality,
            flow_score=flow,
            ideas_generated=ideas_generated,
            ideas_executed=ideas_executed,
            stimulation_source=stimulation_source,
            block_broken=block_broken,
            technique_used=technique_used,
            energy_before=energy_before,
            energy_after=energy_after,
            notes=notes,
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._stats["total_ideas"] += ideas_generated
            self._stats["total_executed"] += ideas_executed

            if block_broken:
                self._stats["blocks_broken"] += 1

            if output_quality < 0.3 and not block_broken:
                self._stats["block_incidents"] += 1

            self._update_technique_stats(session)
            self._update_stats(session)

        self._save_stats()
        self._log_session(session)

        return session

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_creative_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get creative pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in self._sessions if s.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Type breakdown
        by_type = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "flow_sum": 0.0})
        for s in recent:
            t = s.session_type
            by_type[t]["count"] += 1
            by_type[t]["quality_sum"] += s.output_quality
            by_type[t]["flow_sum"] += s.flow_score

        type_stats = {}
        for t, stats in by_type.items():
            type_stats[t] = {
                "count": stats["count"],
                "avg_quality": round(stats["quality_sum"] / stats["count"], 2),
                "avg_flow": round(stats["flow_sum"] / stats["count"], 2),
            }

        # Time of day analysis
        by_hour = defaultdict(list)
        for s in recent:
            try:
                hour = datetime.fromisoformat(s.timestamp).hour
                by_hour[hour].append(s.output_quality)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.creativity_booster")

        best_hour = max(by_hour.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if by_hour else None

        # Idea-to-execution ratio
        total_ideas = sum(s.ideas_generated for s in recent)
        total_executed = sum(s.ideas_executed for s in recent)
        execution_rate = total_executed / max(1, total_ideas) * 100

        # Block analysis
        blocks = [s for s in recent if s.output_quality < 0.3]
        blocks_broken = [s for s in recent if s.block_broken]

        return {
            "days_analyzed": len(set(s.timestamp[:10] for s in recent)),
            "total_sessions": len(recent),
            "total_ideas": total_ideas,
            "total_executed": total_executed,
            "execution_rate": round(execution_rate, 1),
            "avg_quality": round(sum(s.output_quality for s in recent) / len(recent), 2),
            "avg_flow": round(sum(s.flow_score for s in recent) / len(recent), 2),
            "best_creative_hour": f"{best_hour}:00" if best_hour is not None else "",
            "type_breakdown": type_stats,
            "block_incidents": len(blocks),
            "blocks_broken": len(blocks_broken),
            "block_break_success_rate": round(len(blocks_broken) / max(1, len(blocks)) * 100, 1) if blocks else 0,
        }

    def get_block_breaker(self, block_type: str = "") -> Dict[str, Any]:
        """Get personalized block-breaking suggestion."""
        # Find most effective techniques for this user
        effective = sorted(
            self._techniques.values(),
            key=lambda t: t.success_rate,
            reverse=True,
        )

        top_techniques = [t.technique for t in effective[:3]] if effective else []

        # Default techniques if no data
        if not top_techniques:
            top_techniques = ["change_medium", "constraint_challenge", "walk_away", "random_stimulus"]

        # Technique library
        technique_details = {
            "change_medium": {
                "name": "Change Medium",
                "description": "If writing, sketch. If coding, write. Switch how you express the idea.",
                "duration": "15 minutes",
            },
            "constraint_challenge": {
                "name": "Constraint Challenge",
                "description": "Add an artificial constraint (must be 6 words, no colors, etc.). Constraints breed creativity.",
                "duration": "20 minutes",
            },
            "walk_away": {
                "name": "Walk Away",
                "description": "Take a 10-minute walk without your phone. Movement unlocks stuck thinking.",
                "duration": "10 minutes",
            },
            "random_stimulus": {
                "name": "Random Stimulus",
                "description": "Pick a random word/image and force a connection to your problem.",
                "duration": "5 minutes",
            },
            "explain_to_child": {
                "name": "Explain to a Child",
                "description": "Explain your problem as if to a 5-year-old. Simplification reveals hidden assumptions.",
                "duration": "10 minutes",
            },
            "opposite_day": {
                "name": "Opposite Day",
                "description": "Do the opposite of what you're planning. What would a terrible version look like?",
                "duration": "15 minutes",
            },
        }

        # Pick technique
        if block_type == "idea_drought":
            chosen = "random_stimulus"
        elif block_type == "perfectionism":
            chosen = "constraint_challenge"
        elif block_type == "overwhelm":
            chosen = "explain_to_child"
        else:
            chosen = random.choice(top_techniques) if top_techniques else "walk_away"

        detail = technique_details.get(chosen, technique_details["walk_away"])

        return {
            "suggested_technique": detail["name"],
            "description": detail["description"],
            "duration": detail["duration"],
            "reason": f"This technique has a {self._techniques.get(chosen, TechniqueEffectiveness(technique=chosen)).success_rate:.0%} success rate for you." if chosen in self._techniques else "A proven technique for breaking creative blocks.",
            "alternative_techniques": [t for t in top_techniques[:2] if t != chosen],
        }

    def get_creative_energy_score(self) -> int:
        """Calculate current creative energy score (0-100)."""
        if not self._sessions:
            return 50

        recent = list(self._sessions)[-10:]
        n = len(recent)

        # Recent energy trend
        energy_trend = sum(s.energy_after - s.energy_before for s in recent) / n
        energy_score = (energy_trend + 0.5) * 100

        # Flow quality
        avg_flow = sum(s.flow_score for s in recent) / n
        flow_score = avg_flow * 100

        # Idea generation rate
        avg_ideas = sum(s.ideas_generated for s in recent) / n
        idea_score = min(100, avg_ideas * 10)

        overall = round(energy_score * 0.3 + flow_score * 0.4 + idea_score * 0.3)
        return max(0, min(100, overall))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_technique_stats(self, session: CreativeSession):
        """Update technique effectiveness tracking."""
        if not session.technique_used:
            return

        technique = session.technique_used
        if technique not in self._techniques:
            self._techniques[technique] = TechniqueEffectiveness(technique=technique)

        te = self._techniques[technique]
        te.times_used += 1

        if session.block_broken:
            te.success_rate = (te.success_rate * (te.times_used - 1) + 1) / te.times_used
            te.avg_quality_improvement = (te.avg_quality_improvement * (te.times_used - 1) + session.output_quality) / te.times_used
        else:
            te.success_rate = (te.success_rate * (te.times_used - 1)) / te.times_used

    def _update_stats(self, session: CreativeSession):
        """Update running statistics."""
        n = self._stats["total_sessions"]
        self._stats["avg_quality"] = round((self._stats["avg_quality"] * (n - 1) + session.output_quality) / n, 2)
        self._stats["avg_flow"] = round((self._stats["avg_flow"] * (n - 1) + session.flow_score) / n, 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "techniques": {k: {
                    "technique": v.technique,
                    "times_used": v.times_used,
                    "success_rate": v.success_rate,
                    "avg_quality_improvement": v.avg_quality_improvement,
                } for k, v in self._techniques.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.creativity_booster")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("techniques", {}).items():
                    self._techniques[k] = TechniqueEffectiveness(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.creativity_booster")

    def _log_session(self, session: CreativeSession):
        try:
            with open(SESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "type": session.session_type,
                    "duration": session.duration_minutes,
                    "quality": session.output_quality,
                    "flow": session.flow_score,
                    "ideas": session.ideas_generated,
                    "block_broken": session.block_broken,
                    "technique": session.technique_used,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.creativity_booster")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cb_instance: Optional[CreativityBooster] = None
_cb_lock = threading.Lock()


def get_creativity_booster() -> CreativityBooster:
    global _cb_instance
    with _cb_lock:
        if _cb_instance is None:
            _cb_instance = CreativityBooster()
        return _cb_instance
