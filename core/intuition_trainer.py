"""
LOVE Intuition Trainer — Inner Wisdom Intelligence (Modern AI Pattern)

Most people ignore or distrust their intuition. This trainer:

1. INTUITION TRACKING
   - Record intuitive hunches and their outcomes
   - Track gut feelings, bodily knowing, and sudden clarity
   - Log when intuition was followed vs ignored and the results

2. PATTERN ANALYSIS
   - Identify the user's intuitive style (somatic, cognitive, emotional, dream-based)
   - Find which domains the user has strong vs weak intuition
   - Detect intuition suppression patterns (rationalization, fear, people-pleasing)

3. INTUITION DEVELOPMENT
   - Suggest intuition-strengthening exercises
   - Provide discernment practices (intuition vs fear vs wishful thinking)
   - Recommend intuition-honoring experiments

4. TRUST BUILDING
   - Track the accuracy rate of followed intuitions
   - Celebrate when intuition proves correct
   - Gently note when ignoring intuition led to poor outcomes

Architecture:
- record_hunch(hunch, domain, confidence, followed, outcome): Log hunch
- get_intuition_stats(): Get intuition pattern analysis
- get_intuition_exercise(style, domain): Get training exercise
- get_intuition_score(): Calculate overall intuition health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "intuition_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTUITION_LOG = DATA_DIR / "intuition.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class IntuitiveHunch:
    """A tracked intuitive hunch."""
    hunch_id: str = ""
    hunch: str = ""  # what the intuition said
    domain: str = ""  # relationship, work, health, creativity, safety, people, path
    intuitive_type: str = ""  # somatic, cognitive, emotional, dream, synchronous
    confidence: float = 0.5  # 0-1
    followed: bool = False
    outcome: str = ""  # confirmed, missed, neutral, premature, unclear
    rational_override: str = ""  # what the mind said instead
    result_description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class IntuitionTrainer:
    """
    Intelligent intuition trainer with pattern analysis and discernment development.
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
        self._hunches: deque = deque(maxlen=200)
        self._stats = {
            "total_hunches": 0,
            "follow_rate": 0.0,
            "accuracy_rate": 0.0,
            "avg_confidence": 0.0,
            "dominant_type": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_hunch(self, hunch: str = "", domain: str = "", intuitive_type: str = "", confidence: float = 0.5, followed: bool = False, outcome: str = "", rational_override: str = "", result_description: str = "", notes: str = "") -> IntuitiveHunch:
        """Record an intuitive hunch."""
        hunch_id = f"hunch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._hunches)}"
        ih = IntuitiveHunch(
            hunch_id=hunch_id,
            hunch=hunch or "unspecified",
            domain=domain or "general",
            intuitive_type=intuitive_type or "cognitive",
            confidence=confidence,
            followed=followed,
            outcome=outcome or "unclear",
            rational_override=rational_override,
            result_description=result_description,
            notes=notes,
        )

        with self._lock:
            self._hunches.append(ih)
            self._stats["total_hunches"] += 1
            self._update_stats()

        self._save_stats()
        self._log_hunch(ih)

        return ih

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_intuition_stats(self) -> Dict[str, Any]:
        """Get intuition pattern analysis."""
        if not self._hunches:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "followed": 0, "confirmed": 0, "confidence_sum": 0.0})
        for h in self._hunches:
            by_type[h.intuitive_type]["count"] += 1
            if h.followed:
                by_type[h.intuitive_type]["followed"] += 1
            if h.outcome == "confirmed":
                by_type[h.intuitive_type]["confirmed"] += 1
            by_type[h.intuitive_type]["confidence_sum"] += h.confidence

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "follow_rate": round(data["followed"] / count, 2),
                "accuracy": round(data["confirmed"] / max(1, data["followed"]), 2),
                "avg_confidence": round(data["confidence_sum"] / count, 2),
            }

        dominant = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "followed": 0, "confirmed": 0, "ignored_confirmed": 0})
        for h in self._hunches:
            by_domain[h.domain]["count"] += 1
            if h.followed:
                by_domain[h.domain]["followed"] += 1
            if h.outcome == "confirmed":
                by_domain[h.domain]["confirmed"] += 1
            if not h.followed and h.outcome == "confirmed":
                by_domain[h.domain]["ignored_confirmed"] += 1

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "follow_rate": round(data["followed"] / count, 2),
                "accuracy": round(data["confirmed"] / max(1, data["followed"]), 2),
                "missed_intuitions": data["ignored_confirmed"],
            }

        # Rational override analysis
        overrides = [h for h in self._hunches if h.rational_override]
        override_stats = {}
        if overrides:
            overridden_confirmed = sum(1 for h in overrides if not h.followed and h.outcome == "confirmed")
            override_stats = {
                "total_overrides": len(overrides),
                "overrode_correct_intuition": overridden_confirmed,
                "override_cost": overridden_confirmed / len(overrides),
            }

        # Follow vs ignore outcomes
        followed = [h for h in self._hunches if h.followed]
        ignored = [h for h in self._hunches if not h.followed]

        return {
            "total_hunches": len(self._hunches),
            "type_stats": type_stats,
            "dominant_type": dominant[0],
            "domain_stats": domain_stats,
            "override_stats": override_stats,
            "follow_rate": round(len(followed) / len(self._hunches), 2),
            "accuracy_rate": round(sum(1 for h in followed if h.outcome == "confirmed") / max(1, len(followed)), 2),
            "avg_confidence": round(sum(h.confidence for h in self._hunches) / len(self._hunches), 2),
            "followed_outcomes": {outcome: sum(1 for h in followed if h.outcome == outcome) for outcome in set(h.outcome for h in followed)},
            "ignored_outcomes": {outcome: sum(1 for h in ignored if h.outcome == outcome) for outcome in set(h.outcome for h in ignored)},
        }

    def get_intuition_exercise(self, style: str = "", domain: str = "") -> Dict[str, Any]:
        """Get training exercise."""
        exercises = {
            "somatic": [
                "Before a decision, scan your body. Does it feel expanded or contracted?",
                "Notice when your gut reacts to someone before they speak. Track if it was accurate.",
                "Do a body scan before bed. What tensions are trying to tell you something?",
                "When you feel 'off' about a situation, describe the physical sensation precisely.",
            ],
            "cognitive": [
                "When you have a sudden knowing, write it down before logic argues with it.",
                "Practice 'first thought, best thought' for one day. Act on initial impressions.",
                "Notice when you 'just know' something about a person. Verify later.",
                "Ask yourself questions before sleep. Notice what you know upon waking.",
            ],
            "emotional": [
                "Distinguish between fear (constricting) and intuition (clear but may be uncomfortable).",
                "Notice when you feel drawn toward or repelled from something without reason.",
                "Track your emotional responses to people. Do they predict later truths?",
                "When you feel uneasy, ask: Is this fear, or is this knowing?",
            ],
            "dream": [
                "Keep a dream journal for one week. Look for themes about decisions you're facing.",
                "Before sleep, ask a specific question. Note any dreams that feel significant.",
                "When a dream feels important, don't dismiss it. What would you tell a friend who had it?",
                "Notice if dream symbols appear in waking life. Track the pattern.",
            ],
            "synchronous": [
                "Track coincidences for one week. Do they cluster around any decision or person?",
                "When you hear the same message from three unrelated sources, pay attention.",
                "Notice repeated numbers, words, or themes. What might they be pointing to?",
                "When something feels like a sign, don't dismiss it immediately. Consider what it means.",
            ],
        }

        if style and style in exercises:
            selected = random.choice(exercises[style])
        else:
            all_exercises = [e for cat in exercises.values() for e in cat]
            selected = random.choice(all_exercises)

        return {
            "exercise": selected,
            "style": style or "mixed",
            "domain": domain or "general",
            "duration": "One week of observation, then review.",
            "discernment_tip": "Intuition tends to be quiet, steady, and non-dramatic. Fear is loud and urgent. Excitement is energizing but may be wishful thinking.",
        }

    def get_intuition_score(self) -> int:
        """Calculate overall intuition health (0-100)."""
        if not self._hunches:
            return 35

        # Follow rate (following intuition is good)
        follow_rate = sum(1 for h in self._hunches if h.followed) / len(self._hunches)

        # Accuracy (of followed intuitions)
        followed = [h for h in self._hunches if h.followed]
        if followed:
            accuracy = sum(1 for h in followed if h.outcome == "confirmed") / len(followed)
        else:
            accuracy = 0

        # Confidence calibration (confidence should match accuracy)
        avg_confidence = sum(h.confidence for h in self._hunches) / len(self._hunches)
        calibration = 1 - abs(avg_confidence - accuracy)

        # Domain variety
        unique_domains = len(set(h.domain for h in self._hunches))

        # Type variety
        unique_types = len(set(h.intuitive_type for h in self._hunches))

        # Recent activity
        recent = [h for h in self._hunches if h.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        recent_bonus = min(10, len(recent) * 2)

        score = (follow_rate * 20) + (accuracy * 30) + (calibration * 15) + (unique_domains * 3) + (unique_types * 3) + recent_bonus
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._hunches:
            followed = [h for h in self._hunches if h.followed]
            self._stats["follow_rate"] = round(len(followed) / len(self._hunches), 2)
            
            if followed:
                confirmed = sum(1 for h in followed if h.outcome == "confirmed")
                self._stats["accuracy_rate"] = round(confirmed / len(followed), 2)
            
            self._stats["avg_confidence"] = round(sum(h.confidence for h in self._hunches) / len(self._hunches), 2)

            by_type = defaultdict(int)
            for h in self._hunches:
                by_type[h.intuitive_type] += 1
            if by_type:
                self._stats["dominant_type"] = max(by_type.items(), key=lambda x: x[1])[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intuition_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intuition_trainer")

    def _log_hunch(self, hunch: IntuitiveHunch):
        try:
            with open(INTUITION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": hunch.timestamp,
                    "hunch": hunch.hunch[:100],
                    "domain": hunch.domain,
                    "type": hunch.intuitive_type,
                    "confidence": hunch.confidence,
                    "followed": hunch.followed,
                    "outcome": hunch.outcome,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intuition_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_it_instance: Optional[IntuitionTrainer] = None
_it_lock = threading.Lock()


def get_intuition_trainer() -> IntuitionTrainer:
    global _it_instance
    with _it_lock:
        if _it_instance is None:
            _it_instance = IntuitionTrainer()
        return _it_instance
