"""
LOVE Empathy Builder — Perspective Intelligence (Modern AI Pattern)

Most empathy failures come from assumption, not malice. This builder:

1. EMPATHY TRACKING
   - Record empathy attempts and their outcomes
   - Track perspective-taking accuracy (did I understand them correctly?)
   - Log empathy blocks (what got in the way)

2. PATTERN ANALYSIS
   - Identify the user's empathy style (cognitive, emotional, compassionate, somatic)
   - Find empathy strengths (who they empathize with easily) and gaps (who they struggle with)
   - Detect empathy fatigue and its signs

3. EMPATHY SKILL BUILDING
   - Suggest perspective-taking exercises
   - Provide listening technique recommendations
   - Recommend compassion practices for difficult people

4. BOUNDARY AWARENESS
   - Track the balance between empathy and self-protection
   - Alert when empathy is becoming enmeshment or burnout
   - Celebrate healthy empathy moments

Architecture:
- record_empathy_attempt(situation, target, accuracy, block): Log attempt
- get_empathy_stats(): Get empathy pattern analysis
- get_empathy_exercise(target_type, difficulty): Get exercise
- get_empathy_score(): Calculate overall empathy health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "empathy_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMPATHY_LOG = DATA_DIR / "empathy.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EmpathyAttempt:
    """A tracked empathy attempt."""
    attempt_id: str = ""
    situation: str = ""
    target: str = ""  # who they tried to empathize with
    target_type: str = ""  # close, colleague, stranger, difficult, group
    accuracy: float = 0.5  # 0-1, how accurate was understanding
    emotional_resonance: float = 0.5  # 0-1, how much they felt with them
    action_taken: str = ""  # what they did
    block: str = ""  # what got in the way
    cost: float = 0.0  # 0-1, emotional cost
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EmpathyBuilder:
    """
    Intelligent empathy builder with perspective-taking accuracy and boundary tracking.
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
        self._attempts: deque = deque(maxlen=200)
        self._stats = {
            "total_attempts": 0,
            "avg_accuracy": 0.0,
            "avg_cost": 0.0,
            "strongest_target": "",
            "weakest_target": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_empathy_attempt(self, situation: str = "", target: str = "", target_type: str = "", accuracy: float = 0.5, emotional_resonance: float = 0.5, action_taken: str = "", block: str = "", cost: float = 0.0, notes: str = "") -> EmpathyAttempt:
        """Record an empathy attempt."""
        attempt_id = f"emp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._attempts)}"
        attempt = EmpathyAttempt(
            attempt_id=attempt_id,
            situation=situation or "unspecified",
            target=target,
            target_type=target_type or "close",
            accuracy=accuracy,
            emotional_resonance=emotional_resonance,
            action_taken=action_taken,
            block=block,
            cost=cost,
            notes=notes,
        )

        with self._lock:
            self._attempts.append(attempt)
            self._stats["total_attempts"] += 1
            self._update_stats()

        self._save_stats()
        self._log_attempt(attempt)

        return attempt

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_empathy_stats(self) -> Dict[str, Any]:
        """Get empathy pattern analysis."""
        if not self._attempts:
            return {"status": "insufficient_data"}

        # Target type analysis
        by_type = defaultdict(lambda: {"count": 0, "accuracy_sum": 0.0, "resonance_sum": 0.0, "cost_sum": 0.0})
        for a in self._attempts:
            by_type[a.target_type]["count"] += 1
            by_type[a.target_type]["accuracy_sum"] += a.accuracy
            by_type[a.target_type]["resonance_sum"] += a.emotional_resonance
            by_type[a.target_type]["cost_sum"] += a.cost

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_accuracy": round(data["accuracy_sum"] / count, 2),
                "avg_resonance": round(data["resonance_sum"] / count, 2),
                "avg_cost": round(data["cost_sum"] / count, 2),
            }

        strongest = max(type_stats.items(), key=lambda x: x[1]["avg_accuracy"] * x[1]["avg_resonance"]) if type_stats else ("", {})
        weakest = min(type_stats.items(), key=lambda x: x[1]["avg_accuracy"] * x[1]["avg_resonance"]) if type_stats else ("", {})

        # Block analysis
        by_block = defaultdict(lambda: {"count": 0, "accuracy_sum": 0.0})
        for a in self._attempts:
            if a.block:
                by_block[a.block]["count"] += 1
                by_block[a.block]["accuracy_sum"] += a.accuracy

        block_stats = {}
        for b, data in by_block.items():
            count = data["count"]
            block_stats[b] = {
                "count": count,
                "avg_accuracy": round(data["accuracy_sum"] / count, 2),
            }

        # Cost analysis
        high_cost = [a for a in self._attempts if a.cost > 0.5]
        if high_cost:
            high_cost_targets = defaultdict(int)
            for a in high_cost:
                high_cost_targets[a.target_type] += 1
            empathy_fatigue_risk = len(high_cost) / len(self._attempts) > 0.3
        else:
            high_cost_targets = {}
            empathy_fatigue_risk = False

        # Action analysis
        actions = [a for a in self._attempts if a.action_taken]
        action_rate = len(actions) / len(self._attempts)

        return {
            "total_attempts": len(self._attempts),
            "type_stats": type_stats,
            "strongest_target": strongest[0],
            "weakest_target": weakest[0],
            "block_stats": block_stats,
            "avg_accuracy": round(sum(a.accuracy for a in self._attempts) / len(self._attempts), 2),
            "avg_resonance": round(sum(a.emotional_resonance for a in self._attempts) / len(self._attempts), 2),
            "avg_cost": round(sum(a.cost for a in self._attempts) / len(self._attempts), 2),
            "empathy_fatigue_risk": empathy_fatigue_risk,
            "action_rate": round(action_rate, 2),
        }

    def get_empathy_exercise(self, target_type: str = "", difficulty: float = 0.5) -> Dict[str, Any]:
        """Get exercise."""
        exercises = {
            "close": [
                "Ask: 'What do you need right now?' Don't assume. Let them tell you.",
                "Reflect back their emotions before offering solutions.",
                "Do one thing that shows you were listening to a previous conversation.",
            ],
            "colleague": [
                "Before a meeting, wonder: 'What might be stressing them today?'",
                "When they seem off, ask: 'Is everything okay?' with genuine curiosity.",
                "Acknowledge their contribution specifically, not generically.",
            ],
            "stranger": [
                "Make eye contact and smile at one stranger today. Small connections matter.",
                "Imagine the backstory of someone you see but don't know. Practice curiosity.",
                "Hold a door, offer a seat, give a compliment. Small acts of noticing.",
            ],
            "difficult": [
                "Ask: 'What would make them act this way?' Find the human beneath the behavior.",
                "Remember: Hurt people hurt people. Their behavior is about their pain, not your worth.",
                "Set boundaries with compassion. 'I care about you, and I can't accept this behavior.'",
            ],
            "group": [
                "Notice who's not speaking. Invite them in gently.",
                "When there's conflict, validate both sides before seeking resolution.",
                "Ask the group: 'What am I missing?' Open yourself to perspectives you don't see.",
            ],
        }

        selected = exercises.get(target_type, exercises["close"])

        if difficulty > 0.7:
            approach = "This is hard empathy. Protect yourself first. Boundaries enable sustainable empathy."
        elif difficulty > 0.4:
            approach = "Moderate difficulty. Focus on accuracy over resonance. Understanding is enough."
        else:
            approach = "Accessible empathy. Deepen the connection. Feel with them, not for them."

        return {
            "target_type": target_type or "general",
            "difficulty": difficulty,
            "exercise": random.choice(selected),
            "approach": approach,
            "boundary_reminder": "Empathy without boundaries is self-destruction. You can't pour from an empty cup.",
        }

    def get_empathy_score(self) -> int:
        """Calculate overall empathy health (0-100)."""
        if not self._attempts:
            return 35

        # Accuracy
        avg_accuracy = sum(a.accuracy for a in self._attempts) / len(self._attempts)

        # Resonance
        avg_resonance = sum(a.emotional_resonance for a in self._attempts) / len(self._attempts)

        # Low cost (sustainable empathy)
        avg_cost = sum(a.cost for a in self._attempts) / len(self._attempts)

        # Action rate
        actions = [a for a in self._attempts if a.action_taken]
        action_rate = len(actions) / len(self._attempts)

        # Target variety
        unique_targets = len(set(a.target_type for a in self._attempts))

        # Recent trend
        recent = list(self._attempts)[-10:]
        recent_accuracy = sum(a.accuracy for a in recent) / len(recent)
        older = list(self._attempts)[:-10] if len(self._attempts) > 10 else []
        if older:
            older_accuracy = sum(a.accuracy for a in older) / len(older)
            trend = recent_accuracy - older_accuracy
        else:
            trend = 0

        score = (avg_accuracy * 25) + (avg_resonance * 15) + ((1 - avg_cost) * 15) + (action_rate * 15) + (unique_targets * 2) + (trend * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._attempts:
            self._stats["avg_accuracy"] = round(sum(a.accuracy for a in self._attempts) / len(self._attempts), 2)
            self._stats["avg_cost"] = round(sum(a.cost for a in self._attempts) / len(self._attempts), 2)

            by_type = defaultdict(lambda: {"accuracy": 0.0, "resonance": 0.0, "count": 0})
            for a in self._attempts:
                by_type[a.target_type]["accuracy"] += a.accuracy
                by_type[a.target_type]["resonance"] += a.emotional_resonance
                by_type[a.target_type]["count"] += 1
            if by_type:
                strongest = max(by_type.items(), key=lambda x: (x[1]["accuracy"] + x[1]["resonance"]) / max(1, x[1]["count"]))
                weakest = min(by_type.items(), key=lambda x: (x[1]["accuracy"] + x[1]["resonance"]) / max(1, x[1]["count"]))
                self._stats["strongest_target"] = strongest[0]
                self._stats["weakest_target"] = weakest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.empathy_builder")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.empathy_builder")

    def _log_attempt(self, attempt: EmpathyAttempt):
        try:
            with open(EMPATHY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": attempt.timestamp,
                    "situation": attempt.situation,
                    "target_type": attempt.target_type,
                    "accuracy": attempt.accuracy,
                    "resonance": attempt.emotional_resonance,
                    "cost": attempt.cost,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.empathy_builder")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_eb_instance: Optional[EmpathyBuilder] = None
_eb_lock = threading.Lock()


def get_empathy_builder() -> EmpathyBuilder:
    global _eb_instance
    with _eb_lock:
        if _eb_instance is None:
            _eb_instance = EmpathyBuilder()
        return _eb_instance
