"""
LOVE Problem Reframer — Solution Intelligence (Modern AI Pattern)

Most problems persist because they're framed incorrectly. This reframer:

1. PROBLEM TRACKING
   - Record problems and their framing attempts
   - Track reframing strategies and their effectiveness
   - Log solution outcomes and their quality

2. PATTERN ANALYSIS
   - Identify the user's problem-solving style (analytical, intuitive, systematic, creative)
   - Find reframing strategies that unlock solutions
   - Detect stuck patterns (problems that resist reframing)

3. REFRAMING
   - Suggest reframes matched to problem type
   - Provide perspective-shifting exercises
   - Recommend assumption-challenging practices

4. SOLUTION CULTIVATION
   - Track the correlation between reframe quality and solution quality
   - Alert when problems are being approached with stale frames
   - Celebrate elegant reframes

Architecture:
- record_problem(problem, frame, reframe, solution): Log problem
- get_reframing_stats(): Get reframing pattern analysis
- get_reframe_suggestion(problem_type, stuckness): Get suggestion
- get_reframing_score(): Calculate overall reframing health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "problem_reframer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROBLEM_LOG = DATA_DIR / "problems.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ProblemEntry:
    """A tracked problem entry."""
    entry_id: str = ""
    problem: str = ""
    problem_type: str = ""  # technical, relational, strategic, creative, emotional, logistical
    initial_frame: str = ""  # how they initially saw it
    reframe: str = ""  # how they reframed it
    reframe_strategy: str = ""  # inversion, scaling, personification, analogy, first_principles
    solution_quality: float = 0.5  # 0-1
    time_to_solution: float = 0.0  # minutes
    satisfaction: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ProblemReframer:
    """
    Intelligent problem reframer with strategy matching and stuckness detection.
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
            "avg_solution_quality": 0.0,
            "avg_time": 0.0,
            "best_strategy": "",
            "stuck_rate": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_problem(self, problem: str = "", problem_type: str = "", initial_frame: str = "", reframe: str = "", reframe_strategy: str = "", solution_quality: float = 0.5, time_to_solution: float = 0, satisfaction: float = 0.5, notes: str = "") -> ProblemEntry:
        """Record a problem entry."""
        entry_id = f"prob_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ProblemEntry(
            entry_id=entry_id,
            problem=problem or "unspecified",
            problem_type=problem_type or "general",
            initial_frame=initial_frame,
            reframe=reframe,
            reframe_strategy=reframe_strategy or "analogy",
            solution_quality=solution_quality,
            time_to_solution=time_to_solution,
            satisfaction=satisfaction,
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

    def get_reframing_stats(self) -> Dict[str, Any]:
        """Get reframing pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Problem type analysis
        by_type = defaultdict(lambda: {"count": 0, "solution_sum": 0.0, "time_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.problem_type]["count"] += 1
            by_type[e.problem_type]["solution_sum"] += e.solution_quality
            by_type[e.problem_type]["time_sum"] += e.time_to_solution
            by_type[e.problem_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_solution": round(data["solution_sum"] / count, 2),
                "avg_time": round(data["time_sum"] / count, 1),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Reframe strategy analysis
        by_strategy = defaultdict(lambda: {"count": 0, "solution_sum": 0.0, "time_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_strategy[e.reframe_strategy]["count"] += 1
            by_strategy[e.reframe_strategy]["solution_sum"] += e.solution_quality
            by_strategy[e.reframe_strategy]["time_sum"] += e.time_to_solution
            by_strategy[e.reframe_strategy]["satisfaction_sum"] += e.satisfaction

        strategy_stats = {}
        for s, data in by_strategy.items():
            count = data["count"]
            strategy_stats[s] = {
                "count": count,
                "avg_solution": round(data["solution_sum"] / count, 2),
                "avg_time": round(data["time_sum"] / count, 1),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        best_strategy = max(strategy_stats.items(), key=lambda x: x[1]["avg_solution"] * x[1]["avg_satisfaction"]) if strategy_stats else ("", {})

        # Stuck detection (low solution quality, high time)
        stuck = [e for e in self._entries if e.solution_quality < 0.4 and e.time_to_solution > 60]
        stuck_rate = len(stuck) / len(self._entries)

        # Reframe effectiveness (did reframe improve solution?)
        with_reframe = [e for e in self._entries if e.reframe]
        without_reframe = [e for e in self._entries if not e.reframe]
        if with_reframe and without_reframe:
            reframe_solution = sum(e.solution_quality for e in with_reframe) / len(with_reframe)
            no_reframe_solution = sum(e.solution_quality for e in without_reframe) / len(without_reframe)
            reframe_effectiveness = reframe_solution - no_reframe_solution
        else:
            reframe_effectiveness = 0

        # Recent trend
        recent = list(self._entries)[-10:]
        if recent:
            recent_solution = sum(e.solution_quality for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_solution = 0
            recent_satisfaction = 0

        older = list(self._entries)[:-10] if len(self._entries) > 10 else []
        if older:
            older_solution = sum(e.solution_quality for e in older) / len(older)
            older_satisfaction = sum(e.satisfaction for e in older) / len(older)
            solution_trend = recent_solution - older_solution
            satisfaction_trend = recent_satisfaction - older_satisfaction
        else:
            solution_trend = 0
            satisfaction_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "strategy_stats": strategy_stats,
            "best_strategy": best_strategy[0],
            "stuck_rate": round(stuck_rate, 2),
            "reframe_effectiveness": round(reframe_effectiveness, 2),
            "avg_solution": round(sum(e.solution_quality for e in self._entries) / len(self._entries), 2),
            "avg_time": round(sum(e.time_to_solution for e in self._entries) / len(self._entries), 1),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
            "solution_trend": round(solution_trend, 2),
            "satisfaction_trend": round(satisfaction_trend, 2),
        }

    def get_reframe_suggestion(self, problem_type: str = "", stuckness: float = 0.5) -> Dict[str, Any]:
        """Get suggestion."""
        reframes = {
            "technical": [
                "Invert the problem: Instead of 'how do I build this?', ask 'what would make this impossible?' Then avoid those things.",
                "Scale it: What would the solution look like for 1 person? For 1 million? For 1?",
                "Abstract it: What's the underlying pattern? What category does this belong to?",
            ],
            "relational": [
                "Personification: If this relationship were a story, what genre is it? Comedy? Tragedy? Adventure?",
                "Perspective shift: What would the other person say about this problem?",
                "Temporal: Will this matter in 5 years? 5 weeks? 5 minutes?",
            ],
            "strategic": [
                "First principles: What are we actually trying to achieve? Strip away all inherited assumptions.",
                "Analogical: How did a completely different industry solve a similar challenge?",
                "Constraint: What if you had to solve this with 10% of the resources?",
            ],
            "creative": [
                "Opposite: What if you did the exact opposite of your current approach?",
                "Random stimulus: Pick a random object. Force a connection between it and your problem.",
                "Beginner's mind: Pretend you've never encountered this problem. What would a novice suggest?",
            ],
            "emotional": [
                "Naming: Give the emotion a name. 'This is anxiety about rejection.' Naming creates distance.",
                "Physical: Where do you feel this in your body? What happens if you breathe into that place?",
                "Narrative: What story are you telling yourself? Is there another story that fits the facts?",
            ],
            "logistical": [
                "Systems thinking: What's the bottleneck? What's the constraint? Optimize that first.",
                "Elimination: What can you stop doing? Often, the solution is subtraction, not addition.",
                "Parallel: What can be done simultaneously instead of sequentially?",
            ],
        }

        selected = reframes.get(problem_type, reframes["technical"])

        if stuckness > 0.7:
            stuck_note = "You're deeply stuck. This calls for radical reframing. Challenge your most basic assumptions."
        elif stuckness > 0.4:
            stuck_note = "Moderately stuck. Try a different reframe strategy. Your usual approach isn't working."
        else:
            stuck_note = "Not deeply stuck yet. Preventive reframing. Look at the problem from one new angle before committing."

        return {
            "problem_type": problem_type or "general",
            "stuckness": stuckness,
            "reframe": random.choice(selected),
            "stuck_note": stuck_note,
            "principle": "The way you frame a problem determines the solutions you can see. Change the frame, change the game. Most problems are not solved. They're reframed out of existence.",
        }

    def get_reframing_score(self) -> int:
        """Calculate overall reframing health (0-100)."""
        if not self._entries:
            return 35

        # Solution quality
        avg_solution = sum(e.solution_quality for e in self._entries) / len(self._entries)

        # Satisfaction
        avg_satisfaction = sum(e.satisfaction for e in self._entries) / len(self._entries)

        # Speed (lower time = better)
        avg_time = sum(e.time_to_solution for e in self._entries) / len(self._entries)
        speed_score = max(0, 1 - avg_time / 120)

        # Low stuck rate
        stuck = [e for e in self._entries if e.solution_quality < 0.4 and e.time_to_solution > 60]
        stuck_rate = len(stuck) / len(self._entries)

        # Reframe variety
        unique_strategies = len(set(e.reframe_strategy for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-10:]
        if recent:
            recent_solution = sum(e.solution_quality for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_solution = 0
            recent_satisfaction = 0

        # Reframe effectiveness
        with_reframe = [e for e in self._entries if e.reframe]
        without_reframe = [e for e in self._entries if not e.reframe]
        if with_reframe and without_reframe:
            reframe_boost = (sum(e.solution_quality for e in with_reframe) / len(with_reframe)) - (sum(e.solution_quality for e in without_reframe) / len(without_reframe))
        else:
            reframe_boost = 0

        score = (avg_solution * 25) + (avg_satisfaction * 20) + (speed_score * 15) + ((1 - stuck_rate) * 15) + (unique_strategies * 2) + (recent_solution * 10) + (reframe_boost * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_solution_quality"] = round(sum(e.solution_quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_time"] = round(sum(e.time_to_solution for e in self._entries) / len(self._entries), 1)

            by_strategy = defaultdict(lambda: {"solution": 0.0, "satisfaction": 0.0, "count": 0})
            for e in self._entries:
                by_strategy[e.reframe_strategy]["solution"] += e.solution_quality
                by_strategy[e.reframe_strategy]["satisfaction"] += e.satisfaction
                by_strategy[e.reframe_strategy]["count"] += 1
            if by_strategy:
                best = max(by_strategy.items(), key=lambda x: (x[1]["solution"] + x[1]["satisfaction"]) / max(1, x[1]["count"]))
                self._stats["best_strategy"] = best[0]

            stuck = [e for e in self._entries if e.solution_quality < 0.4 and e.time_to_solution > 60]
            self._stats["stuck_rate"] = round(len(stuck) / len(self._entries), 2)

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

    def _log_entry(self, entry: ProblemEntry):
        try:
            with open(PROBLEM_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "problem": entry.problem,
                    "problem_type": entry.problem_type,
                    "initial_frame": entry.initial_frame,
                    "reframe": entry.reframe,
                    "reframe_strategy": entry.reframe_strategy,
                    "solution_quality": entry.solution_quality,
                    "time_to_solution": entry.time_to_solution,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pr_instance: Optional[ProblemReframer] = None
_pr_lock = threading.Lock()


def get_problem_reframer() -> ProblemReframer:
    global _pr_instance
    with _pr_lock:
        if _pr_instance is None:
            _pr_instance = ProblemReframer()
        return _pr_instance
