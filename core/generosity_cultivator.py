"""
LOVE Generosity Cultivator — Giving Intelligence (Modern AI Pattern)

Most people misunderstand generosity. This cultivator:

1. GENEROSITY TRACKING
   - Record generosity moments and their characteristics
   - Track generosity types (time, money, attention, knowledge, connection, presence)
   - Log joy, reciprocity, and sustainability of giving

2. PATTERN ANALYSIS
   - Identify the user's generosity profile (stingy, balanced, over-giving, joyful)
   - Find generosity patterns that create connection vs depletion
   - Detect chronic over-giving and its costs

3. GENEROSITY BUILDING
   - Suggest practices for joyful, sustainable giving
   - Provide frameworks for boundaries in generosity
   - Recommend practices for receiving as well as giving

4. JOYFUL GIVING CULTIVATION
   - Track the correlation between generosity and wellbeing
   - Alert when giving is becoming self-destructive
   - Celebrate moments of genuine, joyful generosity

Architecture:
- record_generosity(gift, type, joy, reciprocity, sustainability): Log generosity
- get_generosity_stats(): Get generosity pattern analysis
- get_generosity_suggestion(capacity, context): Get suggestion
- get_generosity_score(): Calculate overall generosity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "generosity_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GENEROSITY_LOG = DATA_DIR / "generosities.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class GenerosityEntry:
    """A tracked generosity moment."""
    entry_id: str = ""
    gift: str = ""  # what was given
    generosity_type: str = ""  # time, money, attention, knowledge, connection, presence
    joy: float = 0.0  # 0-1
    reciprocity: float = 0.0  # 0-1
    sustainability: float = 0.0  # 0-1
    boundaries: float = 0.0  # 0-1
    receiving: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class GenerosityCultivator:
    """
    Intelligent generosity cultivator with depletion detection and joyful giving cultivation.
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
            "avg_joy": 0.0,
            "avg_sustainability": 0.0,
            "depletion_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_generosity(self, gift: str = "", generosity_type: str = "", joy: float = 0.0, reciprocity: float = 0.0, sustainability: float = 0.0, boundaries: float = 0.0, receiving: float = 0.0, notes: str = "") -> GenerosityEntry:
        """Record a generosity moment."""
        entry_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = GenerosityEntry(
            entry_id=entry_id,
            gift=gift or "unspecified",
            generosity_type=generosity_type or "time",
            joy=joy,
            reciprocity=reciprocity,
            sustainability=sustainability,
            boundaries=boundaries,
            receiving=receiving,
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

    def get_generosity_stats(self) -> Dict[str, Any]:
        """Get generosity pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "joy_sum": 0.0, "sustainability_sum": 0.0, "boundaries_sum": 0.0})
        for e in self._entries:
            by_type[e.generosity_type]["count"] += 1
            by_type[e.generosity_type]["joy_sum"] += e.joy
            by_type[e.generosity_type]["sustainability_sum"] += e.sustainability
            by_type[e.generosity_type]["boundaries_sum"] += e.boundaries

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_sustainability": round(data["sustainability_sum"] / count, 2),
                "avg_boundaries": round(data["boundaries_sum"] / count, 2),
            }

        # Joy analysis
        high_joy = [e for e in self._entries if e.joy > 0.7]
        low_joy = [e for e in self._entries if e.joy < 0.4]
        if high_joy and low_joy:
            high_joy_sust = sum(e.sustainability for e in high_joy) / len(high_joy)
            low_joy_sust = sum(e.sustainability for e in low_joy) / len(low_joy)
            high_joy_rec = sum(e.reciprocity for e in high_joy) / len(high_joy)
            low_joy_rec = sum(e.reciprocity for e in low_joy) / len(low_joy)
        else:
            high_joy_sust = 0
            low_joy_sust = 0
            high_joy_rec = 0
            low_joy_rec = 0

        # Boundaries analysis
        high_bound = [e for e in self._entries if e.boundaries > 0.7]
        low_bound = [e for e in self._entries if e.boundaries < 0.4]
        if high_bound and low_bound:
            high_bound_sust = sum(e.sustainability for e in high_bound) / len(high_bound)
            low_bound_sust = sum(e.sustainability for e in low_bound) / len(low_bound)
        else:
            high_bound_sust = 0
            low_bound_sust = 0

        # Depletion risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_sust = sum(e.sustainability for e in recent) / len(recent)
            recent_bound = sum(e.boundaries for e in recent) / len(recent)
            depletion_risk = recent_joy < 0.3 and recent_sust < 0.3 and recent_bound < 0.3
        else:
            depletion_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "joy_impact": {
                "high_joy_sustainability": round(high_joy_sust, 2),
                "low_joy_sustainability": round(low_joy_sust, 2),
                "high_joy_reciprocity": round(high_joy_rec, 2),
                "low_joy_reciprocity": round(low_joy_rec, 2),
            },
            "boundaries_effect": {
                "high_boundaries_sustainability": round(high_bound_sust, 2),
                "low_boundaries_sustainability": round(low_bound_sust, 2),
            },
            "depletion_risk": depletion_risk,
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
            "avg_sustainability": round(sum(e.sustainability for e in self._entries) / len(self._entries), 2),
        }

    def get_generosity_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get generosity suggestion."""
        suggestions = [
            "Generosity is not sacrifice. If giving makes you resentful, it's not generosity. It's martyrdom. And martyrdom helps no one. Give from overflow. Not from emptiness.",
            "The most generous gift is often presence. Not money. Not time on your phone while you're 'there.' Real, undivided attention. That's the rarest and most valuable thing you can give.",
            "You cannot pour from an empty cup. This is not selfishness. It's physics. Fill yourself first. Then give from the overflow. The world doesn't need your depletion. It needs your abundance.",
            "Generosity creates connection. But only when it's given freely. Obligated generosity is not generosity. It's debt. And the receiver feels it. Give only what you can give with joy.",
            "Receive as well as you give. Many people are excellent givers and terrible receivers. But receiving is also a gift. It lets others practice generosity. Learn to receive with grace.",
            "Track what giving costs you. Not just money. Energy. Time. Emotional labor. If the cost is too high, you're not being generous. You're being exploited. Even by yourself.",
            "Generosity is a practice, not a trait. Some days you have more to give. Some days less. Both are fine. The practice is noticing what you have and sharing it. Without forcing it.",
            "Give what you wish to receive. Attention. Kindness. Understanding. Forgiveness. The world mirrors your giving. Not always immediately. Not always from the same person. But it mirrors.",
            "The person who gives to be liked is not generous. They're performing. True generosity has no audience. It doesn't need recognition. It gives because giving is its own reward.",
            "Your greatest gift might be what comes easiest to you. The thing you take for granted. Your listening. Your humor. Your knowledge. Your calm. Give that. It's probably what people need most."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small gift. One moment of presence. One act of kindness that doesn't deplete you. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A generosity audit. A boundary check. A joyful giving practice. Medium cultivation."
        else:
            capacity_note = "Good capacity. Deep generosity work. A systematic shift from obligation to joy. You have the strength to give from abundance."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Generosity is not about giving everything away. It's about giving what you can give with joy. And that requires boundaries. The person who gives without boundaries is not generous. They're self-destructive. And they usually end up resentful, depleted, and unable to give at all. True generosity is sustainable. It comes from overflow, not emptiness. It creates connection, not obligation. And it includes receiving. Because receiving is also a gift. It allows others to practice generosity. The work of generosity cultivation is about finding the balance. About knowing what you have. About giving what you can give freely. And about protecting yourself so that you can keep giving. Not just today. But for a lifetime."
        }

    def get_generosity_score(self) -> int:
        """Calculate overall generosity health (0-100)."""
        if not self._entries:
            return 25

        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_sust = sum(e.sustainability for e in self._entries) / len(self._entries)
        avg_bound = sum(e.boundaries for e in self._entries) / len(self._entries)
        avg_rec = sum(e.reciprocity for e in self._entries) / len(self._entries)
        avg_recv = sum(e.receiving for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_sust = sum(e.sustainability for e in recent) / len(recent)
        else:
            recent_joy = 0
            recent_sust = 0

        # Depletion penalty
        depl_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            recent_sust_30 = sum(e.sustainability for e in last_30) / len(last_30)
            recent_bound_30 = sum(e.boundaries for e in last_30) / len(last_30)
            if recent_joy_30 < 0.3 and recent_sust_30 < 0.3 and recent_bound_30 < 0.3:
                depl_penalty = 15

        # Type variety
        unique_types = len(set(e.generosity_type for e in self._entries))

        score = (avg_joy * 25) + (avg_sust * 20) + (avg_bound * 20) + (avg_rec * 10) + (avg_recv * 10) + (recent_joy * 5) + (recent_sust * 5) + (unique_types * 2) - depl_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)
            self._stats["avg_sustainability"] = round(sum(e.sustainability for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_joy = sum(e.joy for e in recent) / len(recent)
                recent_sust = sum(e.sustainability for e in recent) / len(recent)
                recent_bound = sum(e.boundaries for e in recent) / len(recent)
                self._stats["depletion_risk"] = recent_joy < 0.3 and recent_sust < 0.3 and recent_bound < 0.3
            else:
                self._stats["depletion_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.generosity_cultivator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.generosity_cultivator")

    def _log_entry(self, entry: GenerosityEntry):
        try:
            with open(GENEROSITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "gift": entry.gift,
                    "generosity_type": entry.generosity_type,
                    "joy": entry.joy,
                    "sustainability": entry.sustainability,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.generosity_cultivator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gc_instance: Optional[GenerosityCultivator] = None
_gc_lock = threading.Lock()


def get_generosity_cultivator() -> GenerosityCultivator:
    global _gc_instance
    with _gc_lock:
        if _gc_instance is None:
            _gc_instance = GenerosityCultivator()
        return _gc_instance
