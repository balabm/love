"""
LOVE Forgiveness Facilitator — Release Intelligence (Modern AI Pattern)

Most people carry resentment that poisons their present. This facilitator:

1. FORGIVENESS TRACKING
   - Record forgiveness work and its characteristics
   - Track forgiveness types (self, other, situation, collective)
   - Log release, compassion, and freedom from forgiveness

2. PATTERN ANALYSIS
   - Identify the user's forgiveness profile (stuck, processing, released, cycling)
   - Find forgiveness patterns that create genuine release
   - Detect resentment accumulation and its costs

3. FORGIVENESS BUILDING
   - Suggest forgiveness practices matched to current capacity and hurt
   - Provide frameworks for understanding without condoning
   - Recommend release rituals and practices

4. FREEDOM CULTIVATION
   - Track the correlation between forgiveness and emotional freedom
   - Alert when resentment is becoming identity
   - Celebrate moments of genuine release and peace

Architecture:
- record_forgiveness(target, type, release, compassion, freedom): Log forgiveness
- get_forgiveness_stats(): Get forgiveness pattern analysis
- get_forgiveness_suggestion(capacity, context): Get suggestion
- get_forgiveness_score(): Calculate overall forgiveness health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "forgiveness_facilitator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FORGIVENESS_LOG = DATA_DIR / "forgiveness.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ForgivenessEntry:
    """A tracked forgiveness work entry."""
    entry_id: str = ""
    target: str = ""  # who or what is being forgiven
    forgiveness_type: str = ""  # self, other, situation, collective
    release: float = 0.0  # 0-1
    compassion: float = 0.0  # 0-1
    freedom: float = 0.0  # 0-1
    understanding: float = 0.0  # 0-1
    self_compassion: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ForgivenessFacilitator:
    """
    Intelligent forgiveness facilitator with release detection and freedom cultivation.
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
            "avg_release": 0.0,
            "avg_freedom": 0.0,
            "resentment_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_forgiveness(self, target: str = "", forgiveness_type: str = "", release: float = 0.0, compassion: float = 0.0, freedom: float = 0.0, understanding: float = 0.0, self_compassion: float = 0.0, notes: str = "") -> ForgivenessEntry:
        """Record a forgiveness work entry."""
        entry_id = f"frg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ForgivenessEntry(
            entry_id=entry_id,
            target=target or "unspecified",
            forgiveness_type=forgiveness_type or "other",
            release=release,
            compassion=compassion,
            freedom=freedom,
            understanding=understanding,
            self_compassion=self_compassion,
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

    def get_forgiveness_stats(self) -> Dict[str, Any]:
        """Get forgiveness pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "release_sum": 0.0, "compassion_sum": 0.0, "freedom_sum": 0.0})
        for e in self._entries:
            by_type[e.forgiveness_type]["count"] += 1
            by_type[e.forgiveness_type]["release_sum"] += e.release
            by_type[e.forgiveness_type]["compassion_sum"] += e.compassion
            by_type[e.forgiveness_type]["freedom_sum"] += e.freedom

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_release": round(data["release_sum"] / count, 2),
                "avg_compassion": round(data["compassion_sum"] / count, 2),
                "avg_freedom": round(data["freedom_sum"] / count, 2),
            }

        # Release analysis
        high_release = [e for e in self._entries if e.release > 0.7]
        low_release = [e for e in self._entries if e.release < 0.4]
        if high_release and low_release:
            high_rel_free = sum(e.freedom for e in high_release) / len(high_release)
            low_rel_free = sum(e.freedom for e in low_release) / len(low_release)
            high_rel_comp = sum(e.compassion for e in high_release) / len(high_release)
            low_rel_comp = sum(e.compassion for e in low_release) / len(low_release)
        else:
            high_rel_free = 0
            low_rel_free = 0
            high_rel_comp = 0
            low_rel_comp = 0

        # Compassion analysis
        high_comp = [e for e in self._entries if e.compassion > 0.7]
        low_comp = [e for e in self._entries if e.compassion < 0.4]
        if high_comp and low_comp:
            high_comp_under = sum(e.understanding for e in high_comp) / len(high_comp)
            low_comp_under = sum(e.understanding for e in low_comp) / len(low_comp)
        else:
            high_comp_under = 0
            low_comp_under = 0

        # Resentment risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_release = sum(e.release for e in recent) / len(recent)
            recent_freedom = sum(e.freedom for e in recent) / len(recent)
            resentment_risk = recent_release < 0.3 and recent_freedom < 0.3
        else:
            resentment_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "release_impact": {
                "high_release_freedom": round(high_rel_free, 2),
                "low_release_freedom": round(low_rel_free, 2),
                "high_release_compassion": round(high_rel_comp, 2),
                "low_release_compassion": round(low_rel_comp, 2),
            },
            "compassion_effect": {
                "high_compassion_understanding": round(high_comp_under, 2),
                "low_compassion_understanding": round(low_comp_under, 2),
            },
            "resentment_risk": resentment_risk,
            "avg_release": round(sum(e.release for e in self._entries) / len(self._entries), 2),
            "avg_freedom": round(sum(e.freedom for e in self._entries) / len(self._entries), 2),
        }

    def get_forgiveness_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get forgiveness suggestion."""
        suggestions = [
            "Forgiveness is not forgetting. It's not condoning. It's not reconciliation. Forgiveness is the decision to stop letting the past control your present. It's for you. Not them.",
            "Write a letter you don't send. Say everything. The anger. The hurt. The disappointment. Then burn it. Or delete it. The act of expression is the beginning of release.",
            "Understand without condoning. What happened was wrong. And there are reasons it happened. Not excuses. Reasons. Understanding creates distance between you and the event.",
            "Forgive yourself first. Most people are harder on themselves than anyone else. The self-criticism. The regret. The shame. Forgive yourself. You're human. You're learning. You're doing your best.",
            "Forgiveness is a practice, not an event. You don't forgive once and it's done. You forgive again and again. Each time the memory arises. Each time the feeling returns. Keep choosing release.",
            "The person who hurt you is not thinking about you. They're living their life. You're the one carrying the weight. Forgiveness is putting down the burden. For your own back.",
            "Compassion for the perpetrator is not betrayal of the victim. Understanding someone's suffering doesn't excuse their actions. It just frees you from the need for them to be monsters.",
            "Forgiveness doesn't require an apology. It doesn't require remorse. It doesn't require anything from the other person. It's a unilateral decision. A gift you give yourself.",
            "Sit with the feeling. Don't rush to forgive. Feel the anger. The betrayal. The sadness. Forgiveness that skips the feeling is not forgiveness. It's suppression.",
            "Resentment is like drinking poison and expecting the other person to die. It doesn't harm them. It harms you. Forgiveness is the antidote. Not for them. For you.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of release. One breath of letting go. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A forgiveness practice. A letter. A ritual. Medium release."
        else:
            capacity_note = "Good capacity. Deep forgiveness work. A major release. You have the strength to let go of something significant."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Forgiveness is the most selfish act you can perform. Not in the negative sense. In the most positive sense. It's an act of radical self-care. The person who forgives is not weak. They're not a doormat. They're not saying what happened was okay. They're saying: I refuse to let this define me. I refuse to carry this weight. I refuse to let the past steal my present. Forgiveness is not about the other person. It's about your freedom. And your freedom is worth everything. The Buddha said that holding onto anger is like grasping a hot coal with the intent of throwing it at someone else. You're the one who gets burned. Let go. Not for them. For you.",
        }

    def get_forgiveness_score(self) -> int:
        """Calculate overall forgiveness health (0-100)."""
        if not self._entries:
            return 25

        avg_release = sum(e.release for e in self._entries) / len(self._entries)
        avg_compassion = sum(e.compassion for e in self._entries) / len(self._entries)
        avg_freedom = sum(e.freedom for e in self._entries) / len(self._entries)
        avg_understanding = sum(e.understanding for e in self._entries) / len(self._entries)
        avg_self_comp = sum(e.self_compassion for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_release = sum(e.release for e in recent) / len(recent)
            recent_freedom = sum(e.freedom for e in recent) / len(recent)
        else:
            recent_release = 0
            recent_freedom = 0

        # Resentment penalty
        resent_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if last_90:
            recent_release_90 = sum(e.release for e in last_90) / len(last_90)
            recent_freedom_90 = sum(e.freedom for e in last_90) / len(last_90)
            if recent_release_90 < 0.3 and recent_freedom_90 < 0.3:
                resent_penalty = 15

        # Type variety
        unique_types = len(set(e.forgiveness_type for e in self._entries))

        score = (avg_release * 30) + (avg_compassion * 15) + (avg_freedom * 25) + (avg_understanding * 10) + (avg_self_comp * 10) + (recent_release * 5) + (recent_freedom * 5) + (unique_types * 2) - resent_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_release"] = round(sum(e.release for e in self._entries) / len(self._entries), 2)
            self._stats["avg_freedom"] = round(sum(e.freedom for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_release = sum(e.release for e in recent) / len(recent)
                recent_freedom = sum(e.freedom for e in recent) / len(recent)
                self._stats["resentment_risk"] = recent_release < 0.3 and recent_freedom < 0.3
            else:
                self._stats["resentment_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.forgiveness_facilitator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.forgiveness_facilitator")

    def _log_entry(self, entry: ForgivenessEntry):
        try:
            with open(FORGIVENESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "target": entry.target,
                    "forgiveness_type": entry.forgiveness_type,
                    "release": entry.release,
                    "freedom": entry.freedom,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.forgiveness_facilitator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ff_instance: Optional[ForgivenessFacilitator] = None
_ff_lock = threading.Lock()


def get_forgiveness_facilitator() -> ForgivenessFacilitator:
    global _ff_instance
    with _ff_lock:
        if _ff_instance is None:
            _ff_instance = ForgivenessFacilitator()
        return _ff_instance
