"""
LOVE Mindful Productivity Coach — Conscious Efficiency Intelligence (Modern AI Pattern)

Most productivity is mindless busyness. This coach:

1. PRODUCTIVITY TRACKING
   - Record productive periods and their characteristics
   - Track intention-action alignment (did you do what you intended?)
   - Log productivity quality vs quantity

2. PATTERN ANALYSIS
   - Identify the user's productivity style (batch, flow, sprint, steady)
   - Find productivity levers (what actually moves the needle)
   - Detect productivity traps (busy work, perfectionism, procrastination)

3. MINDFUL DESIGN
   - Suggest intention-setting practices for each work block
   - Provide mid-block awareness checks
   - Recommend end-of-block reflection

4. SUSTAINABILITY
   - Track the correlation between mindful productivity and burnout
   - Alert when productivity is becoming compulsive
   - Celebrate quality over quantity

Architecture:
- record_block(intention, actions, quality, alignment): Log block
- get_productivity_stats(): Get productivity pattern analysis
- get_mindful_practice(style, trap): Get practice
- get_productivity_score(): Calculate overall mindful productivity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "mindful_productivity_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTIVITY_LOG = DATA_DIR / "productivity.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ProductivityBlock:
    """A tracked productivity block."""
    block_id: str = ""
    intention: str = ""  # what they intended to do
    actions: List[str] = field(default_factory=list)  # what they actually did
    quality: float = 0.5  # 0-1, how well they did it
    alignment: float = 0.5  # 0-1, how aligned actions were with intention
    satisfaction: float = 0.5  # 0-1
    energy_before: float = 0.5
    energy_after: float = 0.5
    trap: str = ""  # busy_work, perfectionism, procrastination, interruption, none
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MindfulProductivityCoach:
    """
    Intelligent mindful productivity coach with intention-alignment tracking and trap detection.
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
        self._blocks: deque = deque(maxlen=200)
        self._stats = {
            "total_blocks": 0,
            "avg_quality": 0.0,
            "avg_alignment": 0.0,
            "dominant_trap": "",
            "best_intention": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_block(self, intention: str = "", actions: Optional[List[str]] = None, quality: float = 0.5, alignment: float = 0.5, satisfaction: float = 0.5, energy_before: float = 0.5, energy_after: float = 0.5, trap: str = "", notes: str = "") -> ProductivityBlock:
        """Record a productivity block."""
        block_id = f"prod_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._blocks)}"
        block = ProductivityBlock(
            block_id=block_id,
            intention=intention or "unspecified",
            actions=actions or [],
            quality=quality,
            alignment=alignment,
            satisfaction=satisfaction,
            energy_before=energy_before,
            energy_after=energy_after,
            trap=trap or "none",
            notes=notes,
        )

        with self._lock:
            self._blocks.append(block)
            self._stats["total_blocks"] += 1
            self._update_stats()

        self._save_stats()
        self._log_block(block)

        return block

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_productivity_stats(self) -> Dict[str, Any]:
        """Get productivity pattern analysis."""
        if not self._blocks:
            return {"status": "insufficient_data"}

        # Intention analysis
        by_intention = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "alignment_sum": 0.0, "satisfaction_sum": 0.0})
        for b in self._blocks:
            by_intention[b.intention]["count"] += 1
            by_intention[b.intention]["quality_sum"] += b.quality
            by_intention[b.intention]["alignment_sum"] += b.alignment
            by_intention[b.intention]["satisfaction_sum"] += b.satisfaction

        intention_stats = {}
        for i, data in by_intention.items():
            count = data["count"]
            intention_stats[i] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_alignment": round(data["alignment_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        best_intention = max(intention_stats.items(), key=lambda x: x[1]["avg_quality"] * x[1]["avg_alignment"]) if intention_stats else ("", {})

        # Trap analysis
        by_trap = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "alignment_sum": 0.0})
        for b in self._blocks:
            by_trap[b.trap]["count"] += 1
            by_trap[b.trap]["quality_sum"] += b.quality
            by_trap[b.trap]["alignment_sum"] += b.alignment

        trap_stats = {}
        for t, data in by_trap.items():
            count = data["count"]
            trap_stats[t] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_alignment": round(data["alignment_sum"] / count, 2),
            }

        dominant_trap = max(trap_stats.items(), key=lambda x: x[1]["count"]) if trap_stats else ("", {})

        # Energy analysis
        energy_changes = [b.energy_after - b.energy_before for b in self._blocks]
        avg_energy_change = sum(energy_changes) / len(energy_changes)

        # Satisfaction correlation
        high_satisfaction = [b for b in self._blocks if b.satisfaction > 0.7]
        low_satisfaction = [b for b in self._blocks if b.satisfaction < 0.4]
        if high_satisfaction and low_satisfaction:
            high_alignment = sum(b.alignment for b in high_satisfaction) / len(high_satisfaction)
            low_alignment = sum(b.alignment for b in low_satisfaction) / len(low_satisfaction)
            satisfaction_driver = high_alignment - low_alignment
        else:
            satisfaction_driver = 0

        # Compulsivity detection
        recent = [b for b in self._blocks if b.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        if recent:
            high_energy_low_satisfaction = sum(1 for b in recent if b.energy_after > 0.6 and b.satisfaction < 0.4)
            compulsivity_risk = high_energy_low_satisfaction / len(recent) > 0.3
        else:
            compulsivity_risk = False

        return {
            "total_blocks": len(self._blocks),
            "intention_stats": intention_stats,
            "best_intention": best_intention[0],
            "trap_stats": trap_stats,
            "dominant_trap": dominant_trap[0],
            "avg_quality": round(sum(b.quality for b in self._blocks) / len(self._blocks), 2),
            "avg_alignment": round(sum(b.alignment for b in self._blocks) / len(self._blocks), 2),
            "avg_satisfaction": round(sum(b.satisfaction for b in self._blocks) / len(self._blocks), 2),
            "avg_energy_change": round(avg_energy_change, 2),
            "satisfaction_driver": round(satisfaction_driver, 2),
            "compulsivity_risk": compulsivity_risk,
        }

    def get_mindful_practice(self, style: str = "", trap: str = "") -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "busy_work": [
                "Before each task, ask: 'Does this matter? Will I care about this in a year?'",
                "Set a 'not doing' list. What are you intentionally ignoring today?",
                "Track one metric that matters. Ignore the rest.",
            ],
            "perfectionism": [
                "Set a 'good enough' standard before starting. Write it down.",
                "Use the 80/20 rule: 80% of value comes from 20% of effort. Find the 20%.",
                "Set a timer. When it goes off, ship it. Perfection is the enemy of done.",
            ],
            "procrastination": [
                "Do the smallest possible version first. Momentum beats motivation.",
                "Set a 5-minute timer. Promise yourself you can stop after. You probably won't.",
                "Ask: 'What am I afraid of?' Procrastination is often fear in disguise.",
            ],
            "interruption": [
                "Before opening any app, ask: 'Is this what I intended to do right now?'",
                "Use the 10-minute rule: Wait 10 minutes before responding to any non-urgent interruption.",
                "Batch all interruptions into one block. Protect your focused time fiercely.",
            ],
            "none": [
                "Set one clear intention before each work block. Write it where you can see it.",
                "Halfway through the block, pause. Ask: 'Am I still doing what I intended?'",
                "At the end, rate: quality, alignment, satisfaction. Learn from the pattern.",
            ],
        }

        selected = practices.get(trap, practices["none"])

        if style == "batch":
            style_note = "You work best in batches. Group similar tasks. Minimize transitions."
        elif style == "flow":
            style_note = "You need long uninterrupted blocks. Protect 2+ hour chunks fiercely."
        elif style == "sprint":
            style_note = "Short, intense bursts work for you. Use pomodoros or time-boxing."
        else:
            style_note = "Steady pace. Consistency beats intensity. Show up every day."

        return {
            "style": style or "steady",
            "trap": trap or "none",
            "practice": random.choice(selected),
            "style_note": style_note,
            "reminder": "Productivity without presence is just busyness. Notice what you're doing. Choose it deliberately.",
        }

    def get_productivity_score(self) -> int:
        """Calculate overall mindful productivity health (0-100)."""
        if not self._blocks:
            return 35

        # Quality and alignment
        avg_quality = sum(b.quality for b in self._blocks) / len(self._blocks)
        avg_alignment = sum(b.alignment for b in self._blocks) / len(self._blocks)

        # Satisfaction
        avg_satisfaction = sum(b.satisfaction for b in self._blocks) / len(self._blocks)

        # Low trap rate
        trapped = sum(1 for b in self._blocks if b.trap != "none")
        trap_rate = trapped / len(self._blocks)

        # Energy sustainability
        avg_energy_change = sum(b.energy_after - b.energy_before for b in self._blocks) / len(self._blocks)

        # Recent trend
        recent = list(self._blocks)[-14:]
        recent_alignment = sum(b.alignment for b in recent) / len(recent)
        older = list(self._blocks)[:-14] if len(self._blocks) > 14 else []
        if older:
            older_alignment = sum(b.alignment for b in older) / len(older)
            trend = recent_alignment - older_alignment
        else:
            trend = 0

        # Intention clarity
        clear_intentions = sum(1 for b in self._blocks if b.intention and b.intention != "unspecified")
        intention_rate = clear_intentions / len(self._blocks)

        score = (avg_quality * 20) + (avg_alignment * 20) + (avg_satisfaction * 15) + ((1 - trap_rate) * 15) + (avg_energy_change * 10) + (trend * 10) + (intention_rate * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._blocks:
            self._stats["avg_quality"] = round(sum(b.quality for b in self._blocks) / len(self._blocks), 2)
            self._stats["avg_alignment"] = round(sum(b.alignment for b in self._blocks) / len(self._blocks), 2)

            by_intention = defaultdict(lambda: {"quality": 0.0, "alignment": 0.0, "count": 0})
            for b in self._blocks:
                by_intention[b.intention]["quality"] += b.quality
                by_intention[b.intention]["alignment"] += b.alignment
                by_intention[b.intention]["count"] += 1
            if by_intention:
                best = max(by_intention.items(), key=lambda x: (x[1]["quality"] + x[1]["alignment"]) / max(1, x[1]["count"]))
                self._stats["best_intention"] = best[0]

            by_trap = defaultdict(int)
            for b in self._blocks:
                by_trap[b.trap] += 1
            if by_trap:
                dominant = max(by_trap.items(), key=lambda x: x[1])
                self._stats["dominant_trap"] = dominant[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mindful_productivity_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mindful_productivity_coach")

    def _log_block(self, block: ProductivityBlock):
        try:
            with open(PRODUCTIVITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": block.timestamp,
                    "intention": block.intention,
                    "quality": block.quality,
                    "alignment": block.alignment,
                    "satisfaction": block.satisfaction,
                    "trap": block.trap,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mindful_productivity_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mpc_instance: Optional[MindfulProductivityCoach] = None
_mpc_lock = threading.Lock()


def get_mindful_productivity_coach() -> MindfulProductivityCoach:
    global _mpc_instance
    with _mpc_lock:
        if _mpc_instance is None:
            _mpc_instance = MindfulProductivityCoach()
        return _mpc_instance
