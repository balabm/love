"""
LOVE Compassion Generator — Loving-Kindness Intelligence (Modern AI Pattern)

Most compassion is conditional. This generator:

1. COMPASSION TRACKING
   - Record compassion practices and their effects
   - Track self-compassion vs other-compassion balance
   - Log compassion blocks and their sources

2. PATTERN ANALYSIS
   - Identify compassion style (tender, fierce, universal, selective)
   - Find compassion gaps (who is hard to feel compassion for)
   - Detect compassion fatigue and its precursors

3. COMPASSION PRACTICES
   - Suggest loving-kindness meditations for specific targets
   - Provide self-compassion breaks and exercises
   - Recommend fierce compassion practices for boundaries

4. TRANSFORMATION
   - Track the correlation between compassion and wellbeing
   - Alert when compassion is absent in situations that need it
   - Celebrate compassion breakthroughs

Architecture:
- record_compassion(target, type, intensity, effect): Log compassion
- get_compassion_stats(): Get compassion pattern analysis
- get_compassion_practice(target_type, difficulty): Get practice
- get_compassion_score(): Calculate overall compassion health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "compassion_generator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMPASSION_LOG = DATA_DIR / "compassion.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CompassionEntry:
    """A tracked compassion entry."""
    entry_id: str = ""
    target: str = ""  # who compassion was directed toward
    target_type: str = ""  # self, loved_one, stranger, difficult, enemy, all_beings
    compassion_type: str = ""  # tender, fierce, appreciative, equanimous
    intensity: float = 0.5  # 0-1
    effect: float = 0.5  # 0-1
    practice_used: str = ""  # what they did
    block_encountered: str = ""  # what got in the way
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CompassionGenerator:
    """
    Intelligent compassion generator with practice matching and fatigue detection.
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
        self._entries: deque = deque(maxlen=200)
        self._stats = {
            "total_entries": 0,
            "avg_intensity": 0.0,
            "avg_effect": 0.0,
            "hardest_target": "",
            "easiest_target": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_compassion(self, target: str = "", target_type: str = "", compassion_type: str = "", intensity: float = 0.5, effect: float = 0.5, practice: str = "", block: str = "", notes: str = "") -> CompassionEntry:
        """Record a compassion entry."""
        entry_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CompassionEntry(
            entry_id=entry_id,
            target=target,
            target_type=target_type or "self",
            compassion_type=compassion_type or "tender",
            intensity=intensity,
            effect=effect,
            practice_used=practice,
            block_encountered=block,
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

    def get_compassion_stats(self) -> Dict[str, Any]:
        """Get compassion pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Target type analysis
        by_target = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "effect_sum": 0.0, "block_count": 0})
        for e in self._entries:
            by_target[e.target_type]["count"] += 1
            by_target[e.target_type]["intensity_sum"] += e.intensity
            by_target[e.target_type]["effect_sum"] += e.effect
            if e.block_encountered:
                by_target[e.target_type]["block_count"] += 1

        target_stats = {}
        for t, data in by_target.items():
            count = data["count"]
            target_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_effect": round(data["effect_sum"] / count, 2),
                "block_rate": round(data["block_count"] / count, 2),
            }

        easiest = max(target_stats.items(), key=lambda x: x[1]["avg_effect"]) if target_stats else ("", {})
        hardest = min(target_stats.items(), key=lambda x: x[1]["avg_effect"]) if target_stats else ("", {})

        # Compassion type analysis
        by_type = defaultdict(lambda: {"count": 0, "effect_sum": 0.0})
        for e in self._entries:
            by_type[e.compassion_type]["count"] += 1
            by_type[e.compassion_type]["effect_sum"] += e.effect

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
            }

        # Block analysis
        by_block = defaultdict(lambda: {"count": 0, "target_types": set()})
        for e in self._entries:
            if e.block_encountered:
                by_block[e.block_encountered]["count"] += 1
                by_block[e.block_encountered]["target_types"].add(e.target_type)

        block_stats = {}
        for b, data in by_block.items():
            block_stats[b] = {
                "count": data["count"],
                "target_types": list(data["target_types"]),
            }

        # Self vs other balance
        self_entries = [e for e in self._entries if e.target_type == "self"]
        other_entries = [e for e in self._entries if e.target_type != "self"]
        if self_entries and other_entries:
            self_avg = sum(e.intensity for e in self_entries) / len(self_entries)
            other_avg = sum(e.intensity for e in other_entries) / len(other_entries)
            balance = self_avg / max(1, other_avg)
        else:
            balance = 1

        # Fatigue detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_blocks = sum(1 for e in recent if e.block_encountered) / len(recent)
            recent_low_effect = sum(1 for e in recent if e.effect < 0.3) / len(recent)
            fatigue_risk = recent_blocks > 0.4 or recent_low_effect > 0.4
        else:
            fatigue_risk = False

        return {
            "total_entries": len(self._entries),
            "target_stats": target_stats,
            "easiest_target": easiest[0],
            "hardest_target": hardest[0],
            "type_stats": type_stats,
            "block_stats": block_stats,
            "self_other_balance": round(balance, 2),
            "fatigue_risk": fatigue_risk,
            "avg_intensity": round(sum(e.intensity for e in self._entries) / len(self._entries), 2),
            "avg_effect": round(sum(e.effect for e in self._entries) / len(self._entries), 2),
        }

    def get_compassion_practice(self, target_type: str = "", difficulty: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "self": [
                "Put your hand on your heart. Say: 'This is a moment of suffering. Suffering is part of life. May I be kind to myself.'",
                "Write a letter to yourself from the perspective of a loving friend.",
                "Ask: 'What do I need right now?' Then give yourself that, even if it's small.",
            ],
            "loved_one": [
                "Visualize them happy and healthy. Send the wish: 'May you be safe. May you be happy. May you be healthy. May you live with ease.'",
                "Recall one kind thing they did for you. Let gratitude warm your heart toward them.",
                "Send them a message of appreciation, no occasion needed.",
            ],
            "stranger": [
                "Look at someone you don't know. Silently wish: 'May you be free from suffering.'",
                "Imagine their life: their struggles, their joys, their hopes. Recognize shared humanity.",
                "Perform one anonymous act of kindness. Compassion in action.",
            ],
            "difficult": [
                "Recall: 'Hurt people hurt people.' Their behavior is about their pain, not your worth.",
                "Visualize them as a child. See the vulnerability beneath the behavior.",
                "Set boundaries with love: 'I care about you, and I cannot accept this behavior.'",
            ],
            "enemy": [
                "This is advanced. Start with neutrality, not love. 'May you be free from suffering' is enough.",
                "Ask: 'What pain drives them?' You don't need to like them to understand them.",
                "Remember: Compassion for enemies protects you from bitterness. It's for you, not them.",
            ],
            "all_beings": [
                "Sit quietly. Expand the circle of your care with each breath. Self, loved ones, strangers, difficult people, all beings.",
                "Walk outside. Look at trees, birds, people. Wish them all well.",
                "Before sleep: 'May all beings everywhere be happy and free.'",
            ],
        }

        selected = practices.get(target_type, practices["self"])

        if difficulty > 0.7:
            approach = "This is hard. Don't force it. Start with neutrality. Love may come later."
        elif difficulty > 0.4:
            approach = "Moderate difficulty. Use cognitive compassion first. Understanding opens the heart."
        else:
            approach = "Accessible. Let the feeling arise naturally. Don't manufacture it."

        return {
            "target_type": target_type or "self",
            "difficulty": difficulty,
            "practice": random.choice(selected),
            "approach": approach,
            "reminder": "Compassion isn't about being nice. It's about recognizing suffering and responding wisely.",
        }

    def get_compassion_score(self) -> int:
        """Calculate overall compassion health (0-100)."""
        if not self._entries:
            return 30

        # Average effect
        avg_effect = sum(e.effect for e in self._entries) / len(self._entries)

        # Intensity
        avg_intensity = sum(e.intensity for e in self._entries) / len(self._entries)

        # Target variety
        unique_targets = len(set(e.target_type for e in self._entries))

        # Low block rate
        blocked = sum(1 for e in self._entries if e.block_encountered)
        block_rate = blocked / len(self._entries)

        # Self-other balance
        self_entries = [e for e in self._entries if e.target_type == "self"]
        other_entries = [e for e in self._entries if e.target_type != "self"]
        if self_entries and other_entries:
            self_avg = sum(e.intensity for e in self_entries) / len(self_entries)
            other_avg = sum(e.intensity for e in other_entries) / len(other_entries)
            balance = 1 - abs(self_avg - other_avg)  # closer to 1 is better
        else:
            balance = 0.5

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_effect = sum(e.effect for e in recent) / len(recent)
        else:
            recent_effect = 0

        score = (avg_effect * 25) + (avg_intensity * 15) + (unique_targets * 3) + ((1 - block_rate) * 15) + (balance * 15) + (recent_effect * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intensity"] = round(sum(e.intensity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_effect"] = round(sum(e.effect for e in self._entries) / len(self._entries), 2)

            by_target = defaultdict(lambda: {"intensity": 0.0, "effect": 0.0, "count": 0})
            for e in self._entries:
                by_target[e.target_type]["intensity"] += e.intensity
                by_target[e.target_type]["effect"] += e.effect
                by_target[e.target_type]["count"] += 1
            if by_target:
                easiest = max(by_target.items(), key=lambda x: x[1]["effect"] / max(1, x[1]["count"]))
                hardest = min(by_target.items(), key=lambda x: x[1]["effect"] / max(1, x[1]["count"]))
                self._stats["easiest_target"] = easiest[0]
                self._stats["hardest_target"] = hardest[0]

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

    def _log_entry(self, entry: CompassionEntry):
        try:
            with open(COMPASSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "target": entry.target,
                    "target_type": entry.target_type,
                    "compassion_type": entry.compassion_type,
                    "intensity": entry.intensity,
                    "effect": entry.effect,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cg_instance: Optional[CompassionGenerator] = None
_cg_lock = threading.Lock()


def get_compassion_generator() -> CompassionGenerator:
    global _cg_instance
    with _cg_lock:
        if _cg_instance is None:
            _cg_instance = CompassionGenerator()
        return _cg_instance
