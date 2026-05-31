"""
LOVE Perspective Shifter — Cognitive Flexibility Intelligence (Modern AI Pattern)

Most thinking is rigid and habitual. This shifter:

1. PERSPECTIVE TRACKING
   - Record perspective shifts and their contexts
   - Track shift techniques and their effectiveness
   - Log stuck perspectives and their costs

2. PATTERN ANALYSIS
   - Identify the user's cognitive rigidity profile (confirmation bias, anchoring, framing, availability)
   - Find perspective shifts that unlock progress
   - Detect cognitive rigidity accumulation

3. PERSPECTIVE GENERATION
   - Suggest perspective shifts matched to current stuckness
   - Provide role-taking exercises
   - Recommend temporal and spatial perspective shifts

4. COGNITIVE FLEXIBILITY
   - Track the correlation between perspective variety and decision quality
   - Alert when thinking is becoming too narrow
   - Celebrate perspective breakthroughs

Architecture:
- record_shift(situation, old_view, new_view, technique): Log shift
- get_perspective_stats(): Get perspective pattern analysis
- get_perspective_shift(situation, rigidity_type): Get shift
- get_perspective_score(): Calculate overall perspective health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "perspective_shifter"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SHIFT_LOG = DATA_DIR / "shifts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PerspectiveShift:
    """A tracked perspective shift."""
    shift_id: str = ""
    situation: str = ""
    old_view: str = ""
    new_view: str = ""
    shift_technique: str = ""  # role_taking, temporal, spatial, inversion, analogy, stakeholder
    effectiveness: float = 0.5  # 0-1
    outcome: str = ""  # what happened after the shift
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PerspectiveShifter:
    """
    Intelligent perspective shifter with rigidity detection and multi-technique perspective generation.
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
        self._shifts: deque = deque(maxlen=300)
        self._stats = {
            "total_shifts": 0,
            "avg_effectiveness": 0.0,
            "best_technique": "",
            "rigidity_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_shift(self, situation: str = "", old_view: str = "", new_view: str = "", shift_technique: str = "", effectiveness: float = 0.5, outcome: str = "", notes: str = "") -> PerspectiveShift:
        """Record a perspective shift."""
        shift_id = f"pers_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._shifts)}"
        shift = PerspectiveShift(
            shift_id=shift_id,
            situation=situation or "unspecified",
            old_view=old_view,
            new_view=new_view,
            shift_technique=shift_technique or "analogy",
            effectiveness=effectiveness,
            outcome=outcome,
            notes=notes,
        )

        with self._lock:
            self._shifts.append(shift)
            self._stats["total_shifts"] += 1
            self._update_stats()

        self._save_stats()
        self._log_shift(shift)

        return shift

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_perspective_stats(self) -> Dict[str, Any]:
        """Get perspective pattern analysis."""
        if not self._shifts:
            return {"status": "insufficient_data"}

        # Technique analysis
        by_technique = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for s in self._shifts:
            by_technique[s.shift_technique]["count"] += 1
            by_technique[s.shift_technique]["effectiveness_sum"] += s.effectiveness

        technique_stats = {}
        for t, data in by_technique.items():
            count = data["count"]
            technique_stats[t] = {
                "count": count,
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
            }

        best_technique = max(technique_stats.items(), key=lambda x: x[1]["avg_effectiveness"]) if technique_stats else ("", {})

        # Situation analysis
        by_situation = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for s in self._shifts:
            by_situation[s.situation]["count"] += 1
            by_situation[s.situation]["effectiveness_sum"] += s.effectiveness

        situation_stats = {}
        for sit, data in by_situation.items():
            count = data["count"]
            if count >= 2:
                situation_stats[sit] = {
                    "count": count,
                    "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                }

        # Outcome analysis
        by_outcome = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for s in self._shifts:
            by_outcome[s.outcome]["count"] += 1
            by_outcome[s.outcome]["effectiveness_sum"] += s.effectiveness

        outcome_stats = {}
        for o, data in by_outcome.items():
            count = data["count"]
            outcome_stats[o] = {
                "count": count,
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
            }

        # Rigidity detection (low effectiveness shifts, same technique overused)
        if len(self._shifts) >= 10:
            recent = list(self._shifts)[-10:]
            avg_effectiveness = sum(s.effectiveness for s in recent) / len(recent)
            technique_counts = defaultdict(int)
            for s in recent:
                technique_counts[s.shift_technique] += 1
            dominant = max(technique_counts.items(), key=lambda x: x[1])
            technique_dominance = dominant[1] / len(recent)
            rigidity_risk = avg_effectiveness < 0.4 or technique_dominance > 0.6
        else:
            rigidity_risk = False

        # Recent trend
        recent = list(self._shifts)[-10:]
        if recent:
            recent_effectiveness = sum(s.effectiveness for s in recent) / len(recent)
        else:
            recent_effectiveness = 0

        older = list(self._shifts)[:-10] if len(self._shifts) > 10 else []
        if older:
            older_effectiveness = sum(s.effectiveness for s in older) / len(older)
            trend = recent_effectiveness - older_effectiveness
        else:
            trend = 0

        return {
            "total_shifts": len(self._shifts),
            "technique_stats": technique_stats,
            "best_technique": best_technique[0],
            "situation_stats": situation_stats,
            "outcome_stats": outcome_stats,
            "avg_effectiveness": round(sum(s.effectiveness for s in self._shifts) / len(self._shifts), 2),
            "rigidity_risk": rigidity_risk,
            "recent_effectiveness": round(recent_effectiveness, 2),
            "trend": round(trend, 2),
        }

    def get_perspective_shift(self, situation: str = "", rigidity_type: str = "") -> Dict[str, Any]:
        """Get shift."""
        shifts = {
            "confirmation_bias": [
                "Actively seek disconfirming evidence. What would prove you wrong?",
                "Find someone who disagrees with you. Listen to understand, not to refute.",
                "Write the strongest argument for the opposite position. Make it compelling.",
            ],
            "anchoring": [
                "Forget the first number you heard. What's a completely different starting point?",
                "Ask: 'If I knew nothing about this, what would I guess?'",
                "Get an outside opinion. Someone not anchored to your starting point.",
            ],
            "framing": [
                "Reframe as gain instead of loss. Or loss instead of gain. Which feels different?",
                "What would you advise a friend in this exact situation?",
                "How would you explain this to a 10-year-old? Simplicity reveals framing.",
            ],
            "availability": [
                "Seek base rates, not anecdotes. What's the statistical reality?",
                "What evidence are you not seeing because it's not memorable?",
                "Wait 24 hours before deciding. Availability bias fades with time.",
            ],
            "general": [
                "Temporal shift: Will this matter in 5 years? 5 weeks? 5 minutes?",
                "Role shift: What would [someone you admire] do? What would your future self want?",
                "Spatial shift: How would this look from another country? Another culture? Another species?",
                "Inversion shift: Instead of 'how do I achieve X?', ask 'how do I guarantee failure at X?'",
            ],
        }

        selected = shifts.get(rigidity_type, shifts["general"])

        if rigidity_type == "confirmation_bias":
            bias_note = "You're seeking confirmation. This is automatic. Override it by deliberately looking for what contradicts your view."
        elif rigidity_type == "anchoring":
            bias_note = "You're anchored. The first number, idea, or impression is disproportionately influencing you. Break the anchor."
        elif rigidity_type == "framing":
            bias_note = "The frame is the message. How you describe the problem determines what solutions you can see. Reframe it."
        elif rigidity_type == "availability":
            bias_note = "You're overvaluing what comes to mind easily. The most memorable is not the most probable. Seek the invisible."
        else:
            bias_note = "Cognitive flexibility requires practice. Deliberately adopt a different perspective. It's a muscle."

        return {
            "situation": situation or "general",
            "rigidity_type": rigidity_type or "general",
            "shift": random.choice(selected),
            "bias_note": bias_note,
            "principle": "Your mind is a prediction machine, not a truth machine. It conserves energy by repeating patterns. Perspective shifts are deliberate interruptions of those patterns. They cost energy but buy accuracy.",
        }

    def get_perspective_score(self) -> int:
        """Calculate overall perspective health (0-100)."""
        if not self._shifts:
            return 30

        # Effectiveness
        avg_effectiveness = sum(s.effectiveness for s in self._shifts) / len(self._shifts)

        # Technique variety
        unique_techniques = len(set(s.shift_technique for s in self._shifts))

        # Situation variety
        unique_situations = len(set(s.situation for s in self._shifts))

        # Outcome variety
        unique_outcomes = len(set(s.outcome for s in self._shifts if s.outcome))

        # Recent trend
        recent = list(self._shifts)[-10:]
        if recent:
            recent_effectiveness = sum(s.effectiveness for s in recent) / len(recent)
        else:
            recent_effectiveness = 0

        # Low rigidity
        if len(recent) >= 10:
            technique_counts = defaultdict(int)
            for s in recent:
                technique_counts[s.shift_technique] += 1
            dominant = max(technique_counts.items(), key=lambda x: x[1])
            technique_dominance = dominant[1] / len(recent)
            rigidity_penalty = min(15, technique_dominance * 15)
        else:
            rigidity_penalty = 0

        # Depth (old_view vs new_view difference)
        depth_score = sum(1 for s in self._shifts if s.old_view and s.new_view and s.old_view != s.new_view) / len(self._shifts)

        score = (avg_effectiveness * 30) + (unique_techniques * 3) + (unique_situations * 2) + (unique_outcomes * 2) + (recent_effectiveness * 15) + (depth_score * 15) - rigidity_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._shifts:
            self._stats["avg_effectiveness"] = round(sum(s.effectiveness for s in self._shifts) / len(self._shifts), 2)

            by_technique = defaultdict(lambda: {"effectiveness": 0.0, "count": 0})
            for s in self._shifts:
                by_technique[s.shift_technique]["effectiveness"] += s.effectiveness
                by_technique[s.shift_technique]["count"] += 1
            if by_technique:
                best = max(by_technique.items(), key=lambda x: x[1]["effectiveness"] / max(1, x[1]["count"]))
                self._stats["best_technique"] = best[0]

            if len(self._shifts) >= 10:
                recent = list(self._shifts)[-10:]
                avg_effectiveness = sum(s.effectiveness for s in recent) / len(recent)
                technique_counts = defaultdict(int)
                for s in recent:
                    technique_counts[s.shift_technique] += 1
                dominant = max(technique_counts.items(), key=lambda x: x[1])
                technique_dominance = dominant[1] / len(recent)
                self._stats["rigidity_risk"] = avg_effectiveness < 0.4 or technique_dominance > 0.6

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

    def _log_shift(self, shift: PerspectiveShift):
        try:
            with open(SHIFT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": shift.timestamp,
                    "situation": shift.situation,
                    "old_view": shift.old_view,
                    "new_view": shift.new_view,
                    "technique": shift.shift_technique,
                    "effectiveness": shift.effectiveness,
                    "outcome": shift.outcome,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ps_instance: Optional[PerspectiveShifter] = None
_ps_lock = threading.Lock()


def get_perspective_shifter() -> PerspectiveShifter:
    global _ps_instance
    with _ps_lock:
        if _ps_instance is None:
            _ps_instance = PerspectiveShifter()
        return _ps_instance
