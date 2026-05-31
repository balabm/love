"""
LOVE Purpose Clarity Engine — Direction Intelligence (Modern AI Pattern)

Most people drift without clear purpose. This engine:

1. PURPOSE TRACKING
   - Record purpose explorations and their characteristics
   - Track purpose clarity levels and their fluctuations
   - Log purpose-aligned actions and their outcomes

2. PATTERN ANALYSIS
   - Identify the user's purpose profile (intrinsic, extrinsic, transcendent, emergent)
   - Find purpose anchors (what reliably brings meaning)
   - Detect purpose drift and its causes

3. CLARITY PRACTICES
   - Suggest purpose-clarification exercises
   - Provide values-purpose alignment checks
   - Recommendation vision-crafting practices

4. DIRECTION ALIGNMENT
   - Track the correlation between purpose clarity and decision quality
   - Alert when actions are diverging from purpose
   - Celebrate purpose-aligned choices

Architecture:
- record_exploration(theme, clarity, alignment, action): Log exploration
- get_purpose_stats(): Get purpose pattern analysis
- get_clarity_exercise(block, current_clarity): Get exercise
- get_purpose_score(): Calculate overall purpose health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "purpose_clarity_engine"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PURPOSE_LOG = DATA_DIR / "explorations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PurposeExploration:
    """A tracked purpose exploration."""
    exploration_id: str = ""
    theme: str = ""  # what they explored
    clarity_before: float = 0.5  # 0-1
    clarity_after: float = 0.5  # 0-1
    alignment: float = 0.5  # 0-1, how aligned current life is with purpose
    action_taken: str = ""  # what they did
    action_quality: float = 0.5  # 0-1
    energy_before: float = 0.5
    energy_after: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PurposeClarityEngine:
    """
    Intelligent purpose clarity engine with drift detection and alignment tracking.
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
        self._explorations: deque = deque(maxlen=300)
        self._stats = {
            "total_explorations": 0,
            "avg_clarity": 0.0,
            "avg_alignment": 0.0,
            "drift_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_exploration(self, theme: str = "", clarity_before: float = 0.5, clarity_after: float = 0.5, alignment: float = 0.5, action_taken: str = "", action_quality: float = 0.5, energy_before: float = 0.5, energy_after: float = 0.5, notes: str = "") -> PurposeExploration:
        """Record a purpose exploration."""
        exploration_id = f"purp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._explorations)}"
        exploration = PurposeExploration(
            exploration_id=exploration_id,
            theme=theme or "unspecified",
            clarity_before=clarity_before,
            clarity_after=clarity_after,
            alignment=alignment,
            action_taken=action_taken,
            action_quality=action_quality,
            energy_before=energy_before,
            energy_after=energy_after,
            notes=notes,
        )

        with self._lock:
            self._explorations.append(exploration)
            self._stats["total_explorations"] += 1
            self._update_stats()

        self._save_stats()
        self._log_exploration(exploration)

        return exploration

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_purpose_stats(self) -> Dict[str, Any]:
        """Get purpose pattern analysis."""
        if not self._explorations:
            return {"status": "insufficient_data"}

        # Theme analysis
        by_theme = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "alignment_sum": 0.0, "action_sum": 0.0})
        for e in self._explorations:
            by_theme[e.theme]["count"] += 1
            by_theme[e.theme]["clarity_sum"] += e.clarity_after
            by_theme[e.theme]["alignment_sum"] += e.alignment
            by_theme[e.theme]["action_sum"] += e.action_quality

        theme_stats = {}
        for t, data in by_theme.items():
            count = data["count"]
            theme_stats[t] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_alignment": round(data["alignment_sum"] / count, 2),
                "avg_action": round(data["action_sum"] / count, 2),
            }

        # Alignment analysis
        high_alignment = [e for e in self._explorations if e.alignment > 0.7]
        low_alignment = [e for e in self._explorations if e.alignment < 0.4]
        if high_alignment and low_alignment:
            high_energy = sum(e.energy_after for e in high_alignment) / len(high_alignment)
            low_energy = sum(e.energy_after for e in low_alignment) / len(low_energy)
            alignment_energy_correlation = high_energy - low_energy
        else:
            alignment_energy_correlation = 0

        # Drift detection
        recent = [e for e in self._explorations if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_alignment = sum(e.alignment for e in recent) / len(recent)
            recent_clarity = sum(e.clarity_after for e in recent) / len(recent)
        else:
            recent_alignment = 0
            recent_clarity = 0

        older = [e for e in self._explorations if e.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
        if older:
            older_alignment = sum(e.alignment for e in older) / len(older)
            older_clarity = sum(e.clarity_after for e in older) / len(older)
            alignment_drift = older_alignment - recent_alignment
            clarity_drift = older_clarity - recent_clarity
        else:
            alignment_drift = 0
            clarity_drift = 0

        drift_risk = alignment_drift > 0.2 or clarity_drift > 0.2

        # Action analysis
        with_action = [e for e in self._explorations if e.action_taken]
        action_rate = len(with_action) / len(self._explorations)
        if with_action:
            action_clarity = sum(e.clarity_after for e in with_action) / len(with_action)
        else:
            action_clarity = 0

        # Clarity gain
        avg_clarity_gain = sum(e.clarity_after - e.clarity_before for e in self._explorations) / len(self._explorations)

        return {
            "total_explorations": len(self._explorations),
            "theme_stats": theme_stats,
            "avg_clarity": round(sum(e.clarity_after for e in self._explorations) / len(self._explorations), 2),
            "avg_alignment": round(sum(e.alignment for e in self._explorations) / len(self._explorations), 2),
            "avg_action_quality": round(sum(e.action_quality for e in self._explorations) / len(self._explorations), 2),
            "alignment_energy_correlation": round(alignment_energy_correlation, 2),
            "drift_risk": drift_risk,
            "alignment_drift": round(alignment_drift, 2),
            "clarity_drift": round(clarity_drift, 2),
            "action_rate": round(action_rate, 2),
            "action_clarity": round(action_clarity, 2),
            "avg_clarity_gain": round(avg_clarity_gain, 2),
        }

    def get_clarity_exercise(self, block: str = "", current_clarity: float = 0.5) -> Dict[str, Any]:
        """Get exercise."""
        exercises = {
            "uncertainty": [
                "Write your own eulogy. What would you want it to say? What does that reveal about what matters?",
                "If you had 10 years left, what would you stop doing? Start doing?",
                "Ask 5 people who know you well: 'What do you think I'm here to do?' Notice patterns.",
            ],
            "conflict": [
                "List your top 5 values. Rank them. Now check: does your calendar reflect this ranking?",
                "Write two versions of your life: one where you follow society's script, one where you follow your own. Which feels more alive?",
                "What would you do if no one could judge you? That's closer to your truth.",
            ],
            "overwhelm": [
                "One word purpose exercise: If your life had one word as its theme, what would it be?",
                "The 'enough' question: What would be enough? Enough success? Enough money? Enough impact?",
                "Subtract, not add: What can you remove to get closer to what matters?",
            ],
            "boredom": [
                "What did you love doing at age 10? Before the world told you what to want?",
                "What problem in the world makes you angry? Anger often points to purpose.",
                "What would you teach if you were the world's leading expert on one thing?",
            ],
            "fear": [
                "What's the worst that happens if you pursue this purpose? Can you survive it?",
                "What would your 80-year-old self regret more: trying and failing, or never trying?",
                "Purpose doesn't require courage every day. It requires courage today. One step.",
            ],
            "general": [
                "The three questions: What are you good at? What do you love? What does the world need? The overlap is purpose.",
                "Purpose is not a destination. It's a direction. You don't 'find' it. You choose it, then refine it.",
                "Write a personal mission statement. One paragraph. Read it weekly. Edit it monthly.",
            ],
        }

        selected = exercises.get(block, exercises["general"])

        if current_clarity < 0.3:
            clarity_note = "Purpose fog. That's okay. Most people are foggy. The fog clears with exploration, not thinking."
        elif current_clarity < 0.6:
            clarity_note = "Emerging clarity. You have glimpses. Now test them with action."
        else:
            clarity_note = "Good clarity. Now the work is alignment. Live it, don't just know it."

        return {
            "block": block or "general",
            "current_clarity": current_clarity,
            "exercise": random.choice(selected),
            "clarity_note": clarity_note,
            "principle": "Purpose is not what the world needs from you. It's what you cannot not do. It's the thing that, when you do it, time disappears and you feel most alive. It's not found. It's recognized, then chosen, then lived.",
        }

    def get_purpose_score(self) -> int:
        """Calculate overall purpose health (0-100)."""
        if not self._explorations:
            return 30

        # Clarity and alignment
        avg_clarity = sum(e.clarity_after for e in self._explorations) / len(self._explorations)
        avg_alignment = sum(e.alignment for e in self._explorations) / len(self._explorations)

        # Action quality
        avg_action = sum(e.action_quality for e in self._explorations) / len(self._explorations)

        # Energy sustainability
        avg_energy_change = sum(e.energy_after - e.energy_before for e in self._explorations) / len(self._explorations)

        # Clarity gain
        avg_clarity_gain = sum(e.clarity_after - e.clarity_before for e in self._explorations) / len(self._explorations)

        # Recent trend
        recent = [e for e in self._explorations if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_clarity = sum(e.clarity_after for e in recent) / len(recent)
            recent_alignment = sum(e.alignment for e in recent) / len(recent)
        else:
            recent_clarity = 0
            recent_alignment = 0

        # Drift penalty
        older = [e for e in self._explorations if e.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
        if older:
            older_alignment = sum(e.alignment for e in older) / len(older)
            older_clarity = sum(e.clarity_after for e in older) / len(older)
            drift_penalty = 10 if (older_alignment - recent_alignment > 0.2 or older_clarity - recent_clarity > 0.2) else 0
        else:
            drift_penalty = 0

        # Theme variety
        unique_themes = len(set(e.theme for e in self._explorations))

        score = (avg_clarity * 25) + (avg_alignment * 25) + (avg_action * 15) + (avg_energy_change * 10) + (avg_clarity_gain * 10) + (recent_clarity * 10) + (recent_alignment * 10) + (unique_themes * 1) - drift_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._explorations:
            self._stats["avg_clarity"] = round(sum(e.clarity_after for e in self._explorations) / len(self._explorations), 2)
            self._stats["avg_alignment"] = round(sum(e.alignment for e in self._explorations) / len(self._explorations), 2)

            recent = [e for e in self._explorations if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            older = [e for e in self._explorations if e.timestamp <= (datetime.now() - timedelta(days=30)).isoformat()]
            if recent and older:
                recent_alignment = sum(e.alignment for e in recent) / len(recent)
                older_alignment = sum(e.alignment for e in older) / len(older)
                recent_clarity = sum(e.clarity_after for e in recent) / len(recent)
                older_clarity = sum(e.clarity_after for e in older) / len(older)
                self._stats["drift_risk"] = (older_alignment - recent_alignment > 0.2) or (older_clarity - recent_clarity > 0.2)

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

    def _log_exploration(self, exploration: PurposeExploration):
        try:
            with open(PURPOSE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": exploration.timestamp,
                    "theme": exploration.theme,
                    "clarity_before": exploration.clarity_before,
                    "clarity_after": exploration.clarity_after,
                    "alignment": exploration.alignment,
                    "action_taken": exploration.action_taken,
                    "action_quality": exploration.action_quality,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pce_instance: Optional[PurposeClarityEngine] = None
_pce_lock = threading.Lock()


def get_purpose_clarity_engine() -> PurposeClarityEngine:
    global _pce_instance
    with _pce_lock:
        if _pce_instance is None:
            _pce_instance = PurposeClarityEngine()
        return _pce_instance
