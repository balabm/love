"""
LOVE Assertiveness Trainer — Communication Intelligence (Modern AI Pattern)

Most assertiveness training is theoretical. This trainer:

1. SKILL TRACKING
   - Record assertiveness attempts and their outcomes
   - Track communication style (passive, aggressive, passive-aggressive, assertive)
   - Log body language, tone, and word choice during difficult conversations

2. PATTERN ANALYSIS
   - Identify situations where the user reverts to passive or aggressive
   - Find the gap between intended and actual assertiveness
   - Detect which people or contexts trigger non-assertive behavior

3. SCRIPT GENERATION
   - Generate assertive responses for specific situations
   - Provide graded exposure exercises (easy → hard)
   - Suggest body language and tone adjustments

4. PROGRESS TRACKING
   - Calculate assertiveness score over time
   - Identify the user's assertiveness growth curve
   - Celebrate milestones and breakthrough moments

Architecture:
- record_attempt(situation, intended_style, actual_style, outcome): Log attempt
- get_assertiveness_stats(): Get assertiveness pattern analysis
- get_script(situation, goal): Get assertive response script
- get_assertiveness_score(): Calculate overall assertiveness level
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "assertiveness_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ATTEMPT_LOG = DATA_DIR / "attempts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AssertivenessAttempt:
    """A tracked assertiveness attempt."""
    attempt_id: str = ""
    situation: str = ""  # what was happening
    goal: str = ""  # what the user wanted
    intended_style: str = ""  # assertive, passive, aggressive
    actual_style: str = ""  # what they actually did
    outcome: str = ""  # achieved, partial, failed, reversed
    anxiety_level: float = 0.5  # 0-1 before the interaction
    body_language: str = ""  # open, closed, tense, confident
    tone: str = ""  # calm, shaky, loud, monotone
    words_used: List[str] = field(default_factory=list)
    what_went_well: List[str] = field(default_factory=list)
    what_to_improve: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AssertivenessTrainer:
    """
    Intelligent assertiveness trainer with script generation and progress tracking.
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
            "assertive_rate": 0.0,
            "avg_anxiety": 0.0,
            "success_rate": 0.0,
            "weakest_context": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_attempt(self, situation: str = "", goal: str = "", intended_style: str = "", actual_style: str = "", outcome: str = "", anxiety: float = 0.5, body_language: str = "", tone: str = "", words: Optional[List[str]] = None, went_well: Optional[List[str]] = None, to_improve: Optional[List[str]] = None) -> AssertivenessAttempt:
        """Record an assertiveness attempt."""
        attempt_id = f"assert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._attempts)}"
        attempt = AssertivenessAttempt(
            attempt_id=attempt_id,
            situation=situation or "unspecified",
            goal=goal,
            intended_style=intended_style or "assertive",
            actual_style=actual_style or "unspecified",
            outcome=outcome or "failed",
            anxiety_level=anxiety,
            body_language=body_language,
            tone=tone,
            words_used=words or [],
            what_went_well=went_well or [],
            what_to_improve=to_improve or [],
        )

        with self._lock:
            self._attempts.append(attempt)
            self._stats["total_attempts"] += 1
            self._update_stats()

        self._save_stats()
        self._log_attempt(attempt)

        return attempt

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_assertiveness_stats(self) -> Dict[str, Any]:
        """Get assertiveness pattern analysis."""
        if not self._attempts:
            return {"status": "insufficient_data"}

        # Style analysis
        by_style = defaultdict(int)
        for a in self._attempts:
            by_style[a.actual_style] += 1

        total = len(self._attempts)
        style_distribution = {k: round(v / total, 2) for k, v in by_style.items()}

        # Situation analysis
        by_situation = defaultdict(lambda: {"count": 0, "assertive": 0, "anxiety_sum": 0.0, "success": 0})
        for a in self._attempts:
            by_situation[a.situation]["count"] += 1
            if a.actual_style == "assertive":
                by_situation[a.situation]["assertive"] += 1
            by_situation[a.situation]["anxiety_sum"] += a.anxiety_level
            if a.outcome in ["achieved", "partial"]:
                by_situation[a.situation]["success"] += 1

        situation_stats = {}
        for s, data in by_situation.items():
            count = data["count"]
            situation_stats[s] = {
                "count": count,
                "assertive_rate": round(data["assertive"] / count, 2),
                "avg_anxiety": round(data["anxiety_sum"] / count, 2),
                "success_rate": round(data["success"] / count, 2),
            }

        # Weakest context
        weakest = min(situation_stats.items(), key=lambda x: x[1]["assertive_rate"]) if situation_stats else ("", {})

        # Trend
        recent = [a for a in self._attempts if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_assertive = sum(1 for a in recent if a.actual_style == "assertive")
            recent_rate = recent_assertive / len(recent)
            older = [a for a in self._attempts if a.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
            if older:
                older_assertive = sum(1 for a in older if a.actual_style == "assertive")
                older_rate = older_assertive / len(older)
                trend = "improving" if recent_rate > older_rate + 0.1 else "declining" if recent_rate < older_rate - 0.1 else "stable"
            else:
                trend = "new"
        else:
            trend = "stable"

        return {
            "total_attempts": total,
            "style_distribution": style_distribution,
            "situation_stats": situation_stats,
            "weakest_context": weakest[0],
            "assertive_rate": round(sum(1 for a in self._attempts if a.actual_style == "assertive") / total, 2),
            "success_rate": round(sum(1 for a in self._attempts if a.outcome in ["achieved", "partial"]) / total, 2),
            "avg_anxiety": round(sum(a.anxiety_level for a in self._attempts) / total, 2),
            "trend": trend,
        }

    def get_script(self, situation: str = "", goal: str = "", difficulty: str = "medium") -> Dict[str, Any]:
        """Get assertive response script."""
        scripts = {
            "saying_no": {
                "easy": "I can't take that on right now, but thank you for thinking of me.",
                "medium": "I appreciate the offer, but I need to say no. I'm at capacity.",
                "hard": "No. I won't be doing that. Let's find another solution.",
            },
            "asking_for_raise": {
                "easy": "I'd like to discuss my compensation when you have time.",
                "medium": "I've taken on more responsibility. Can we review my salary to reflect that?",
                "hard": "My role has expanded significantly. I need a raise to [specific number] to reflect the value I bring.",
            },
            "expressing_disagreement": {
                "easy": "I see it differently. Here's my perspective...",
                "medium": "I respect your view, but I disagree. The data suggests...",
                "hard": "I strongly disagree with that approach. Here's why, and here's what I recommend instead.",
            },
            "setting_boundary": {
                "easy": "I prefer to keep weekends for family.",
                "medium": "I don't check email after 7 PM. I'll respond in the morning.",
                "hard": "You crossed a line. That behavior is unacceptable to me.",
            },
            "asking_for_help": {
                "easy": "Could you help me with this when you have a minute?",
                "medium": "I need your expertise on this. Can we schedule 30 minutes?",
                "hard": "I need you to take ownership of this piece. It's beyond my scope and deadline.",
            },
            "giving_feedback": {
                "easy": "I noticed something. Can I share it with you?",
                "medium": "When you [behavior], it [impact]. I'd prefer [alternative].",
                "hard": "Your approach isn't working. Here's what needs to change, and by when.",
            },
        }

        base = scripts.get(situation, scripts["saying_no"])
        script = base.get(difficulty, base["medium"])

        return {
            "situation": situation,
            "goal": goal,
            "difficulty": difficulty,
            "script": script,
            "body_language": "Eye contact, open posture, steady voice" if difficulty != "easy" else "Relaxed posture, friendly tone",
            "tone": "Calm and firm" if difficulty != "easy" else "Warm but clear",
            "prep": "Practice in mirror 3 times" if difficulty == "hard" else "Rehearse once",
        }

    def get_assertiveness_score(self) -> int:
        """Calculate overall assertiveness level (0-100)."""
        if not self._attempts:
            return 40  # Baseline for beginners

        # Assertive rate
        assertive = sum(1 for a in self._attempts if a.actual_style == "assertive")
        rate = assertive / len(self._attempts)

        # Success rate
        success = sum(1 for a in self._attempts if a.outcome in ["achieved", "partial"])
        success_rate = success / len(self._attempts)

        # Anxiety (lower is better)
        avg_anxiety = sum(a.anxiety_level for a in self._attempts) / len(self._attempts)

        # Recency bonus
        recent = [a for a in self._attempts if a.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_assertive = sum(1 for a in recent if a.actual_style == "assertive")
            recent_rate = recent_assertive / len(recent)
        else:
            recent_rate = rate

        score = (rate * 30) + (success_rate * 30) + ((1 - avg_anxiety) * 20) + (recent_rate * 20)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._attempts:
            assertive = sum(1 for a in self._attempts if a.actual_style == "assertive")
            self._stats["assertive_rate"] = round(assertive / len(self._attempts), 2)
            self._stats["avg_anxiety"] = round(sum(a.anxiety_level for a in self._attempts) / len(self._attempts), 2)
            success = sum(1 for a in self._attempts if a.outcome in ["achieved", "partial"])
            self._stats["success_rate"] = round(success / len(self._attempts), 2)

            by_situation = defaultdict(lambda: {"assertive": 0, "total": 0})
            for a in self._attempts:
                by_situation[a.situation]["total"] += 1
                if a.actual_style == "assertive":
                    by_situation[a.situation]["assertive"] += 1
            
            if by_situation:
                weakest = min(by_situation.items(), key=lambda x: x[1]["assertive"] / max(1, x[1]["total"]))
                self._stats["weakest_context"] = weakest[0]

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

    def _log_attempt(self, attempt: AssertivenessAttempt):
        try:
            with open(ATTEMPT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": attempt.timestamp,
                    "situation": attempt.situation,
                    "intended": attempt.intended_style,
                    "actual": attempt.actual_style,
                    "outcome": attempt.outcome,
                    "anxiety": attempt.anxiety_level,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_at_instance: Optional[AssertivenessTrainer] = None
_at_lock = threading.Lock()


def get_assertiveness_trainer() -> AssertivenessTrainer:
    global _at_instance
    with _at_lock:
        if _at_instance is None:
            _at_instance = AssertivenessTrainer()
        return _at_instance
