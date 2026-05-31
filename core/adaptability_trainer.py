"""
LOVE Adaptability Trainer — Change Intelligence (Modern AI Pattern)

Most people resist change even when they know it's needed. This trainer:

1. ADAPTABILITY TRACKING
   - Record changes faced and the user's response
   - Track adaptation speed, resistance level, and outcome quality
   - Log what helped vs hindered adaptation

2. PATTERN ANALYSIS
   - Identify the user's adaptation style (planner, improviser, gradual, sudden)
   - Find which changes are hardest to adapt to (chosen vs imposed, expected vs sudden)
   - Detect adaptation predictors (preparation, support, agency, meaning)

3. ADAPTATION FACILITATION
   - Suggest adaptation strategies for current changes
   - Provide resistance-to-acceptance bridge exercises
   - Recommend micro-adaptations to build flexibility

4. FLEXIBILITY BUILDING
   - Track adaptability as a muscle that strengthens with use
   - Suggest controlled disruptions for practice
   - Celebrate adaptation successes

Architecture:
- record_adaptation(change, type, response, outcome): Log adaptation
- get_adaptability_stats(): Get adaptation pattern analysis
- get_adaptation_strategy(change_type, resistance_level): Get strategy
- get_adaptability_score(): Calculate overall adaptability health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "adaptability_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ADAPTATION_LOG = DATA_DIR / "adaptations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Adaptation:
    """A tracked adaptation to change."""
    adaptation_id: str = ""
    change: str = ""
    change_type: str = ""  # chosen, imposed, expected, sudden, gradual, role, environment, routine
    size: str = ""  # micro, small, medium, large, life
    personal_agency: float = 0.5  # 0-1, how much control they had
    initial_resistance: float = 0.5  # 0-1
    adaptation_speed: str = ""  # immediate, fast, moderate, slow, stuck
    strategies_used: List[str] = field(default_factory=list)
    support_used: List[str] = field(default_factory=list)
    outcome: str = ""  # thriving, coping, surviving, struggling, regressed
    outcome_quality: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AdaptabilityTrainer:
    """
    Intelligent adaptability trainer with change pattern analysis and resistance bridging.
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
        self._adaptations: deque = deque(maxlen=200)
        self._stats = {
            "total_adaptations": 0,
            "avg_resistance": 0.0,
            "avg_agency": 0.0,
            "thriving_rate": 0.0,
            "dominant_type": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_adaptation(self, change: str = "", change_type: str = "", size: str = "", agency: float = 0.5, resistance: float = 0.5, speed: str = "", strategies: Optional[List[str]] = None, support: Optional[List[str]] = None, outcome: str = "", outcome_quality: float = 0.5, notes: str = "") -> Adaptation:
        """Record an adaptation."""
        adaptation_id = f"adapt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._adaptations)}"
        adapt = Adaptation(
            adaptation_id=adaptation_id,
            change=change or "unspecified",
            change_type=change_type or "imposed",
            size=size or "medium",
            personal_agency=agency,
            initial_resistance=resistance,
            adaptation_speed=speed or "moderate",
            strategies_used=strategies or [],
            support_used=support or [],
            outcome=outcome or "coping",
            outcome_quality=outcome_quality,
            notes=notes,
        )

        with self._lock:
            self._adaptations.append(adapt)
            self._stats["total_adaptations"] += 1
            self._update_stats()

        self._save_stats()
        self._log_adaptation(adapt)

        return adapt

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_adaptability_stats(self) -> Dict[str, Any]:
        """Get adaptation pattern analysis."""
        if not self._adaptations:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "resistance_sum": 0.0, "outcome_sum": 0.0, "thriving": 0})
        for a in self._adaptations:
            by_type[a.change_type]["count"] += 1
            by_type[a.change_type]["resistance_sum"] += a.initial_resistance
            by_type[a.change_type]["outcome_sum"] += a.outcome_quality
            if a.outcome == "thriving":
                by_type[a.change_type]["thriving"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_resistance": round(data["resistance_sum"] / count, 2),
                "avg_outcome": round(data["outcome_sum"] / count, 2),
                "thriving_rate": round(data["thriving"] / count, 2),
            }

        dominant = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Size analysis
        by_size = defaultdict(lambda: {"count": 0, "outcome_sum": 0.0})
        for a in self._adaptations:
            by_size[a.size]["count"] += 1
            by_size[a.size]["outcome_sum"] += a.outcome_quality

        size_stats = {}
        for s, data in by_size.items():
            count = data["count"]
            size_stats[s] = {
                "count": count,
                "avg_outcome": round(data["outcome_sum"] / count, 2),
            }

        # Speed analysis
        by_speed = defaultdict(lambda: {"count": 0, "outcome_sum": 0.0})
        for a in self._adaptations:
            by_speed[a.adaptation_speed]["count"] += 1
            by_speed[a.adaptation_speed]["outcome_sum"] += a.outcome_quality

        speed_stats = {}
        for sp, data in by_speed.items():
            count = data["count"]
            speed_stats[sp] = {
                "count": count,
                "avg_outcome": round(data["outcome_sum"] / count, 2),
            }

        # Agency correlation
        high_agency = [a for a in self._adaptations if a.personal_agency > 0.6]
        low_agency = [a for a in self._adaptations if a.personal_agency <= 0.4]
        agency_effect = "positive" if (sum(a.outcome_quality for a in high_agency) / max(1, len(high_agency))) > (sum(a.outcome_quality for a in low_agency) / max(1, len(low_agency))) else "mixed"

        return {
            "total_adaptations": len(self._adaptations),
            "type_stats": type_stats,
            "dominant_type": dominant[0],
            "size_stats": size_stats,
            "speed_stats": speed_stats,
            "agency_effect": agency_effect,
            "avg_resistance": round(sum(a.initial_resistance for a in self._adaptations) / len(self._adaptations), 2),
            "avg_outcome": round(sum(a.outcome_quality for a in self._adaptations) / len(self._adaptations), 2),
            "thriving_rate": round(sum(1 for a in self._adaptations if a.outcome == "thriving") / len(self._adaptations), 2),
        }

    def get_adaptation_strategy(self, change_type: str = "", resistance_level: float = 0.5, size: str = "medium") -> Dict[str, Any]:
        """Get adaptation strategy."""
        strategies = {
            "chosen": {
                "approach": "You chose this. Remember your why when it gets hard.",
                "steps": [
                    "Reconnect with the original motivation",
                    "Notice the gap between expectation and reality—it's normal",
                    "Celebrate small wins toward the new state",
                    "Grieve what you left behind without abandoning the choice",
                ],
            },
            "imposed": {
                "approach": "You didn't choose this. Find agency within the constraint.",
                "steps": [
                    "Acknowledge the loss of control. It's real.",
                    "Find one small choice you still have",
                    "Reframe: What would I choose if I were choosing?",
                    "Build something new within the new constraints",
                ],
            },
            "expected": {
                "approach": "You've been preparing. Trust the preparation.",
                "steps": [
                    "Review what you planned—adjust as needed",
                    "Notice anxiety is excitement without breath",
                    "Take one planned step. Then another.",
                    "The anticipation was harder than the reality will be",
                ],
            },
            "sudden": {
                "approach": "This is a shock. Go slow. Shock first, then strategy.",
                "steps": [
                    "Allow 24-48 hours of just feeling before deciding",
                    "Secure basic needs: sleep, food, safety, connection",
                    "Find one trustworthy person to process with",
                    "When ready, make one small decision. Just one.",
                ],
            },
        }

        base = strategies.get(change_type, strategies["imposed"])

        if resistance_level > 0.7:
            resistance_note = "High resistance. Don't force adaptation. Start with acceptance. Resistance is information—what is it protecting?"
        elif resistance_level > 0.4:
            resistance_note = "Moderate resistance. Find the fear beneath it. Name it. Then choose one tiny step forward."
        else:
            resistance_note = "Low resistance. You're ready. Use this energy to build momentum before doubt arrives."

        return {
            "change_type": change_type or "general",
            "size": size,
            "resistance": resistance_level,
            **base,
            "resistance_note": resistance_note,
            "flexibility_practice": "This week, change one small routine daily. Notice you survive. Build from there.",
        }

    def get_adaptability_score(self) -> int:
        """Calculate overall adaptability health (0-100)."""
        if not self._adaptations:
            return 40

        # Outcome quality
        avg_outcome = sum(a.outcome_quality for a in self._adaptations) / len(self._adaptations)

        # Thriving rate
        thriving_rate = sum(1 for a in self._adaptations if a.outcome == "thriving") / len(self._adaptations)

        # Low resistance to positive outcomes
        successful = [a for a in self._adaptations if a.outcome_quality > 0.6]
        if successful:
            avg_resistance_success = sum(a.initial_resistance for a in successful) / len(successful)
        else:
            avg_resistance_success = 1.0

        # Strategy variety
        all_strategies = []
        for a in self._adaptations:
            all_strategies.extend(a.strategies_used)
        unique_strategies = len(set(all_strategies))

        # Recent activity
        recent = [a for a in self._adaptations if a.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        recent_bonus = min(10, len(recent) * 2)

        # Speed (faster adaptation is generally better, but not always)
        speed_scores = {"immediate": 5, "fast": 4, "moderate": 3, "slow": 2, "stuck": 1}
        avg_speed = sum(speed_scores.get(a.adaptation_speed, 3) for a in self._adaptations) / len(self._adaptations)

        score = (avg_outcome * 25) + (thriving_rate * 20) + ((1 - avg_resistance_success) * 15) + (unique_strategies * 2) + recent_bonus + (avg_speed / 5 * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._adaptations:
            self._stats["avg_resistance"] = round(sum(a.initial_resistance for a in self._adaptations) / len(self._adaptations), 2)
            self._stats["avg_agency"] = round(sum(a.personal_agency for a in self._adaptations) / len(self._adaptations), 2)
            thriving = sum(1 for a in self._adaptations if a.outcome == "thriving")
            self._stats["thriving_rate"] = round(thriving / len(self._adaptations), 2)

            by_type = defaultdict(int)
            for a in self._adaptations:
                by_type[a.change_type] += 1
            if by_type:
                self._stats["dominant_type"] = max(by_type.items(), key=lambda x: x[1])[0]

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

    def _log_adaptation(self, adaptation: Adaptation):
        try:
            with open(ADAPTATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": adaptation.timestamp,
                    "change": adaptation.change,
                    "type": adaptation.change_type,
                    "size": adaptation.size,
                    "resistance": adaptation.initial_resistance,
                    "speed": adaptation.adaptation_speed,
                    "outcome": adaptation.outcome,
                    "quality": adaptation.outcome_quality,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_at_instance: Optional[AdaptabilityTrainer] = None
_at_lock = threading.Lock()


def get_adaptability_trainer() -> AdaptabilityTrainer:
    global _at_instance
    with _at_lock:
        if _at_instance is None:
            _at_instance = AdaptabilityTrainer()
        return _at_instance
