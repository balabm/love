"""
LOVE Decision Quality Tracker — Decision Intelligence (Modern AI Pattern)

Most people make decisions reactively. This tracker:

1. DECISION TRACKING
   - Record decisions and their characteristics
   - Track decision types (strategic, tactical, emotional, financial, relational)
   - Log quality, speed, information, and outcome of decisions

2. PATTERN ANALYSIS
   - Identify the user's decision profile (impulsive, analytical, balanced, paralyzed)
   - Find decision patterns that create good vs bad outcomes
   - Detect chronic poor decision-making and its costs

3. QUALITY BUILDING
   - Suggest practices for improving decision quality
   - Provide frameworks for better decision-making
   - Recommend practices for slowing down or speeding up appropriately

4. DECISION WISDOM CULTIVATION
   - Track the correlation between decision process and outcomes
   - Alert when decisions are becoming reactive or paralyzed
   - Celebrate moments of genuine decision wisdom

Architecture:
- record_decision(decision, type, quality, speed, information, outcome): Log decision
- get_decision_stats(): Get decision pattern analysis
- get_decision_suggestion(capacity, context): Get suggestion
- get_decision_score(): Calculate overall decision health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "decision_quality_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DECISION_LOG = DATA_DIR / "decisions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class DecisionEntry:
    """A tracked decision."""
    entry_id: str = ""
    decision: str = ""  # what was decided
    decision_type: str = ""  # strategic, tactical, emotional, financial, relational
    quality: float = 0.0  # 0-1 process quality
    speed: float = 0.0  # 0-1 appropriate speed
    information: float = 0.0  # 0-1 information gathered
    outcome: float = 0.0  # 0-1 outcome quality
    clarity: float = 0.0  # 0-1
    values_alignment: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DecisionQualityTracker:
    """
    Intelligent decision quality tracker with pattern detection and wisdom cultivation.
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
            "avg_quality": 0.0,
            "avg_outcome": 0.0,
            "reactive_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_decision(self, decision: str = "", decision_type: str = "", quality: float = 0.0, speed: float = 0.0, information: float = 0.0, outcome: float = 0.0, clarity: float = 0.0, values_alignment: float = 0.0, notes: str = "") -> DecisionEntry:
        """Record a decision."""
        entry_id = f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = DecisionEntry(
            entry_id=entry_id,
            decision=decision or "unspecified",
            decision_type=decision_type or "tactical",
            quality=quality,
            speed=speed,
            information=information,
            outcome=outcome,
            clarity=clarity,
            values_alignment=values_alignment,
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

    def get_decision_stats(self) -> Dict[str, Any]:
        """Get decision pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "outcome_sum": 0.0, "speed_sum": 0.0})
        for e in self._entries:
            by_type[e.decision_type]["count"] += 1
            by_type[e.decision_type]["quality_sum"] += e.quality
            by_type[e.decision_type]["outcome_sum"] += e.outcome
            by_type[e.decision_type]["speed_sum"] += e.speed

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_outcome": round(data["outcome_sum"] / count, 2),
                "avg_speed": round(data["speed_sum"] / count, 2),
            }

        # Quality vs outcome
        high_qual = [e for e in self._entries if e.quality > 0.7]
        low_qual = [e for e in self._entries if e.quality < 0.4]
        if high_qual and low_qual:
            high_qual_out = sum(e.outcome for e in high_qual) / len(high_qual)
            low_qual_out = sum(e.outcome for e in low_qual) / len(low_qual)
            high_qual_info = sum(e.information for e in high_qual) / len(high_qual)
            low_qual_info = sum(e.information for e in low_qual) / len(low_qual)
        else:
            high_qual_out = 0
            low_qual_out = 0
            high_qual_info = 0
            low_qual_info = 0

        # Speed analysis
        high_speed = [e for e in self._entries if e.speed > 0.7]
        low_speed = [e for e in self._entries if e.speed < 0.4]
        if high_speed and low_speed:
            high_speed_out = sum(e.outcome for e in high_speed) / len(high_speed)
            low_speed_out = sum(e.outcome for e in low_speed) / len(low_speed)
        else:
            high_speed_out = 0
            low_speed_out = 0

        # Reactive risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_qual = sum(e.quality for e in recent) / len(recent)
            recent_info = sum(e.information for e in recent) / len(recent)
            reactive_risk = recent_qual < 0.4 and recent_info < 0.3
        else:
            reactive_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "quality_impact": {
                "high_quality_outcome": round(high_qual_out, 2),
                "low_quality_outcome": round(low_qual_out, 2),
                "high_quality_information": round(high_qual_info, 2),
                "low_quality_information": round(low_qual_info, 2),
            },
            "speed_effect": {
                "high_speed_outcome": round(high_speed_out, 2),
                "low_speed_outcome": round(low_speed_out, 2),
            },
            "reactive_risk": reactive_risk,
            "avg_quality": round(sum(e.quality for e in self._entries) / len(self._entries), 2),
            "avg_outcome": round(sum(e.outcome for e in self._entries) / len(self._entries), 2),
        }

    def get_decision_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get decision suggestion."""
        suggestions = [
            "Most bad decisions are made in haste. Not because the decision was wrong. But because it was made before the mind was ready. When you're emotional, wait. When you're tired, wait. When you're pressured, wait. Time is a decision-making tool.",
            "The best decisions are made with enough information, not all the information. Perfect information is a myth. But zero information is recklessness. Gather enough. Then decide. The difference between enough and all is the difference between action and paralysis.",
            "Sleep on it. Seriously. Your brain processes decisions during sleep. The decision that seems brilliant at 11 PM often seems ridiculous at 7 AM. And vice versa. Let your unconscious mind have a vote.",
            "Write down the decision criteria before you decide. What matters? Speed? Cost? Quality? Alignment with values? If you don't know your criteria, any decision seems right. Or wrong. Depending on your mood.",
            "Consider the opposite. What if you're wrong? What would that look like? What would it cost? People who only consider being right make terrible decisions. Because they never prepare for being wrong.",
            "Decisions are bets on the future. You don't know the outcome. You know the odds. And you know your edge. Bet accordingly. Don't bet your entire life on a coin flip. But don't refuse to bet on a sure thing either.",
            "The person who fears making the wrong decision is already making the wrong decision. Because indecision is a decision. It's a decision to let circumstances choose for you. And circumstances are terrible choosers.",
            "Your past decisions are data. Not verdicts. If you made a bad decision, learn from it. Don't let it define you. The person who learns from bad decisions becomes a good decision-maker. The person who is defined by them becomes paralyzed.",
            "Values-aligned decisions feel right even when they're hard. If a decision feels easy but wrong, it probably is. If it feels hard but right, it probably is. Trust the feeling of alignment.",
            "The quality of your life is the quality of your decisions. Not your circumstances. Two people with the same circumstances make different decisions. And those decisions create different lives. Choose wisely."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One pause before one decision. One moment of clarity. One question: what do I actually want? That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A decision journal entry. A criteria review. A pros and cons list. Medium tracking."
        else:
            capacity_note = "Good capacity. Deep decision analysis. A systematic improvement of your decision process. You have the strength to make truly wise choices."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Decisions are the building blocks of life. Every decision you make shapes your future. The small ones accumulate. The big ones define. And most people make them poorly. Not because they're stupid. But because they're reactive. They decide when they're emotional. When they're pressured. When they lack information. When they're tired. And then they wonder why their life doesn't look like they want it to. Good decision-making is a skill. It's not intuition. It's not luck. It's a process. And that process can be learned. It involves gathering information. It involves sleeping on it. It involves considering the opposite. It involves aligning with values. It involves accepting that you can't know the future. And it involves making the best bet you can with what you know. That's decision wisdom. And it's the most valuable skill you can develop."
        }

    def get_decision_score(self) -> int:
        """Calculate overall decision health (0-100)."""
        if not self._entries:
            return 25

        avg_qual = sum(e.quality for e in self._entries) / len(self._entries)
        avg_out = sum(e.outcome for e in self._entries) / len(self._entries)
        avg_info = sum(e.information for e in self._entries) / len(self._entries)
        avg_speed = sum(e.speed for e in self._entries) / len(self._entries)
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_values = sum(e.values_alignment for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_qual = sum(e.quality for e in recent) / len(recent)
            recent_out = sum(e.outcome for e in recent) / len(recent)
        else:
            recent_qual = 0
            recent_out = 0

        # Reactive penalty
        react_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_qual_30 = sum(e.quality for e in last_30) / len(last_30)
            recent_info_30 = sum(e.information for e in last_30) / len(last_30)
            if recent_qual_30 < 0.4 and recent_info_30 < 0.3:
                react_penalty = 15

        # Type variety
        unique_types = len(set(e.decision_type for e in self._entries))

        score = (avg_qual * 25) + (avg_out * 15) + (avg_info * 15) + (avg_speed * 10) + (avg_clarity * 10) + (avg_values * 10) + (recent_qual * 5) + (recent_out * 5) + (unique_types * 2) - react_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_quality"] = round(sum(e.quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_outcome"] = round(sum(e.outcome for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_qual = sum(e.quality for e in recent) / len(recent)
                recent_info = sum(e.information for e in recent) / len(recent)
                self._stats["reactive_risk"] = recent_qual < 0.4 and recent_info < 0.3
            else:
                self._stats["reactive_risk"] = False

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

    def _log_entry(self, entry: DecisionEntry):
        try:
            with open(DECISION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "decision": entry.decision,
                    "decision_type": entry.decision_type,
                    "quality": entry.quality,
                    "outcome": entry.outcome,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dqt_instance: Optional[DecisionQualityTracker] = None
_dqt_lock = threading.Lock()


def get_decision_quality_tracker() -> DecisionQualityTracker:
    global _dqt_instance
    with _dqt_lock:
        if _dqt_instance is None:
            _dqt_instance = DecisionQualityTracker()
        return _dqt_instance
