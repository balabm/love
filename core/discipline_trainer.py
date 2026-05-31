"""
LOVE Discipline Trainer — Self-Regulation Intelligence (Modern AI Pattern)

Most discipline fails because it's based on willpower. This trainer:

1. DISCIPLINE TRACKING
   - Record commitments made and kept vs broken
   - Track the environment, energy, and context around kept/broken commitments
   - Log the emotional cost of broken commitments

2. PATTERN ANALYSIS
   - Identify the user's discipline style (routine-based, identity-based, reward-based, fear-based)
   - Find discipline leak points (evening, weekends, transitions, social settings)
   - Detect the gap between intention and action

3. SYSTEM BUILDING
   - Suggest environment design to reduce friction
   - Provide implementation intention templates
   - Recommend commitment devices and accountability structures

4. GENTLE PROGRESS
   - Track discipline as a skill, not a moral trait
   - Distinguish between discipline and self-punishment
   - Celebrate disciplined choices without harshness

Architecture:
- record_commitment(commitment, kept, context): Log commitment
- get_discipline_stats(): Get discipline pattern analysis
- get_discipline_suggestion(goal, leak_point): Get system design
- get_discipline_score(): Calculate overall discipline health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "discipline_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMMITMENT_LOG = DATA_DIR / "commitments.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Commitment:
    """A tracked commitment."""
    commitment_id: str = ""
    commitment: str = ""
    category: str = ""  # health, work, learning, creativity, relationship, finance
    kept: bool = False
    context: str = ""  # morning, evening, weekend, workday, social, alone, tired, energized
    energy_level: float = 0.5  # 0-1
    friction_level: float = 0.5  # 0-1, how hard it was to do
    identity_statement: str = ""  # who they were being
    consequence_felt: str = ""  # how they felt after breaking/keeping
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DisciplineTrainer:
    """
    Intelligent discipline trainer with pattern analysis and system design.
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
        self._commitments: deque = deque(maxlen=300)
        self._stats = {
            "total_commitments": 0,
            "kept_rate": 0.0,
            "avg_friction": 0.0,
            "leakiest_context": "",
            "strongest_context": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_commitment(self, commitment: str = "", category: str = "", kept: bool = False, context: str = "", energy: float = 0.5, friction: float = 0.5, identity: str = "", consequence: str = "", notes: str = "") -> Commitment:
        """Record a commitment."""
        commitment_id = f"commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._commitments)}"
        c = Commitment(
            commitment_id=commitment_id,
            commitment=commitment or "unspecified",
            category=category or "general",
            kept=kept,
            context=context or "general",
            energy_level=energy,
            friction_level=friction,
            identity_statement=identity,
            consequence_felt=consequence,
            notes=notes,
        )

        with self._lock:
            self._commitments.append(c)
            self._stats["total_commitments"] += 1
            self._update_stats()

        self._save_stats()
        self._log_commitment(c)

        return c

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_discipline_stats(self) -> Dict[str, Any]:
        """Get discipline pattern analysis."""
        if not self._commitments:
            return {"status": "insufficient_data"}

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "kept": 0, "friction_sum": 0.0, "energy_sum": 0.0})
        for c in self._commitments:
            by_context[c.context]["count"] += 1
            if c.kept:
                by_context[c.context]["kept"] += 1
            by_context[c.context]["friction_sum"] += c.friction_level
            by_context[c.context]["energy_sum"] += c.energy_level

        context_stats = {}
        for ctx, data in by_context.items():
            count = data["count"]
            context_stats[ctx] = {
                "count": count,
                "kept_rate": round(data["kept"] / count, 2),
                "avg_friction": round(data["friction_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
            }

        leakiest = min(context_stats.items(), key=lambda x: x[1]["kept_rate"]) if context_stats else ("", {})
        strongest = max(context_stats.items(), key=lambda x: x[1]["kept_rate"]) if context_stats else ("", {})

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "kept": 0})
        for c in self._commitments:
            by_category[c.category]["count"] += 1
            if c.kept:
                by_category[c.category]["kept"] += 1

        category_stats = {}
        for cat, data in by_category.items():
            count = data["count"]
            category_stats[cat] = {
                "count": count,
                "kept_rate": round(data["kept"] / count, 2),
            }

        # Identity analysis
        by_identity = defaultdict(lambda: {"count": 0, "kept": 0})
        for c in self._commitments:
            if c.identity_statement:
                by_identity[c.identity_statement]["count"] += 1
                if c.kept:
                    by_identity[c.identity_statement]["kept"] += 1

        identity_stats = {}
        for ident, data in by_identity.items():
            count = data["count"]
            identity_stats[ident] = {
                "count": count,
                "kept_rate": round(data["kept"] / count, 2),
            }

        # Friction vs success
        kept = [c for c in self._commitments if c.kept]
        broken = [c for c in self._commitments if not c.kept]
        if kept and broken:
            avg_friction_kept = sum(c.friction_level for c in kept) / len(kept)
            avg_friction_broken = sum(c.friction_level for c in broken) / len(broken)
            friction_insight = f"Kept commitments had {avg_friction_kept:.2f} avg friction vs {avg_friction_broken:.2f} for broken"
        else:
            friction_insight = "insufficient_data"

        return {
            "total_commitments": len(self._commitments),
            "context_stats": context_stats,
            "leakiest_context": leakiest[0],
            "strongest_context": strongest[0],
            "category_stats": category_stats,
            "identity_stats": identity_stats,
            "kept_rate": round(sum(1 for c in self._commitments if c.kept) / len(self._commitments), 2),
            "avg_friction": round(sum(c.friction_level for c in self._commitments) / len(self._commitments), 2),
            "friction_insight": friction_insight,
        }

    def get_discipline_suggestion(self, goal: str = "", leak_point: str = "", energy_pattern: str = "") -> Dict[str, Any]:
        """Get system design."""
        environment_designs = {
            "evening": [
                "Set a phone alarm for your evening routine start time",
                "Prepare tomorrow's clothes/gear before dinner",
                "Use app blockers after 9pm",
                "Put temptations in hard-to-reach places",
            ],
            "weekend": [
                "Schedule one 'anchor event' each weekend morning",
                "Tell someone your weekend plan by Friday night",
                "Set environment cues (shoes by door, book on pillow)",
                "Plan one fun thing so discipline doesn't feel like punishment",
            ],
            "morning": [
                "Lay out everything the night before",
                "Use the 5-second rule: count down, then move",
                "Make the first task ridiculously small",
                "Put the alarm across the room",
            ],
            "tired": [
                "Lower the bar. Half effort is infinitely better than zero.",
                "Change the identity: 'I do this even when tired'",
                "Pair with something restorative (music, tea, fresh air)",
                "Do the absolute minimum version, then decide if you want more",
            ],
            "social": [
                "Tell friends your goal before the event",
                "Have an accountability text buddy for social situations",
                "Plan your 'no' in advance. Practice it.",
                "Choose social settings that align with your goals",
            ],
        }

        designs = environment_designs.get(leak_point, environment_designs["evening"])

        identity_templates = [
            f"I am someone who {goal}",
            f"{goal} is just what I do",
            f"I don't negotiate with myself about {goal}",
            f"Being someone who {goal} matters more than feeling like it",
        ]

        return {
            "goal": goal or "unspecified",
            "leak_point": leak_point or "evening",
            "environment_designs": random.sample(designs, min(2, len(designs))),
            "identity_statement": random.choice(identity_templates),
            "implementation_intention": f"When [situation], I will [specific action]",
            "reminder": "Discipline is remembering what you want. Not what you want right now. What you really want.",
        }

    def get_discipline_score(self) -> int:
        """Calculate overall discipline health (0-100)."""
        if not self._commitments:
            return 40

        # Kept rate
        kept_rate = sum(1 for c in self._commitments if c.kept) / len(self._commitments)

        # Low friction (system design reduces friction)
        avg_friction = sum(c.friction_level for c in self._commitments) / len(self._commitments)

        # Identity alignment
        identity_aligned = [c for c in self._commitments if c.identity_statement]
        if identity_aligned:
            identity_rate = sum(1 for c in identity_aligned if c.kept) / len(identity_aligned)
        else:
            identity_rate = 0

        # Recent trend
        recent = list(self._commitments)[-10:]
        recent_kept = sum(1 for c in recent if c.kept) / len(recent)
        older = list(self._commitments)[:-10] if len(self._commitments) > 10 else []
        if older:
            older_kept = sum(1 for c in older if c.kept) / len(older)
            trend = recent_kept - older_kept
        else:
            trend = 0

        # Variety of contexts (discipline across domains)
        unique_contexts = len(set(c.context for c in self._commitments))

        score = (kept_rate * 35) + ((1 - avg_friction) * 15) + (identity_rate * 15) + (trend * 15) + (unique_contexts * 2)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._commitments:
            kept = sum(1 for c in self._commitments if c.kept)
            self._stats["kept_rate"] = round(kept / len(self._commitments), 2)
            self._stats["avg_friction"] = round(sum(c.friction_level for c in self._commitments) / len(self._commitments), 2)

            by_context = defaultdict(lambda: {"kept": 0, "total": 0})
            for c in self._commitments:
                by_context[c.context]["total"] += 1
                if c.kept:
                    by_context[c.context]["kept"] += 1
            
            if by_context:
                leakiest = min(by_context.items(), key=lambda x: x[1]["kept"] / max(1, x[1]["total"]))
                strongest = max(by_context.items(), key=lambda x: x[1]["kept"] / max(1, x[1]["total"]))
                self._stats["leakiest_context"] = leakiest[0]
                self._stats["strongest_context"] = strongest[0]

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

    def _log_commitment(self, commitment: Commitment):
        try:
            with open(COMMITMENT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": commitment.timestamp,
                    "commitment": commitment.commitment,
                    "category": commitment.category,
                    "kept": commitment.kept,
                    "context": commitment.context,
                    "friction": commitment.friction_level,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dt_instance: Optional[DisciplineTrainer] = None
_dt_lock = threading.Lock()


def get_discipline_trainer() -> DisciplineTrainer:
    global _dt_instance
    with _dt_lock:
        if _dt_instance is None:
            _dt_instance = DisciplineTrainer()
        return _dt_instance
