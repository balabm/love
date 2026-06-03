"""
LOVE Intimacy Coach — Closeness Intelligence (Modern AI Pattern)

Most people confuse intimacy with proximity. This coach:

1. INTIMACY TRACKING
   - Record intimacy moments and their characteristics
   - Track intimacy types (emotional, physical, intellectual, spiritual, experiential)
   - Log depth, safety, reciprocity, and satisfaction of intimacy

2. PATTERN ANALYSIS
   - Identify the user's intimacy profile (avoidant, guarded, developing, deep)
   - Find intimacy patterns that create closeness vs distance
   - Detect chronic avoidance and its costs

3. INTIMACY BUILDING
   - Suggest practices for deepening intimacy in relationships
   - Provide frameworks for vulnerability, trust, and closeness
   - Recommend practices for repairing intimacy ruptures

4. CLOSENESS CULTIVATION
   - Track the correlation between intimacy depth and relationship quality
   - Alert when avoidance is becoming the default
   - Celebrate moments of genuine, deep connection

Architecture:
- record_intimacy(moments, type, depth, safety, reciprocity, satisfaction): Log intimacy
- get_intimacy_stats(): Get intimacy pattern analysis
- get_intimacy_suggestion(capacity, context): Get suggestion
- get_intimacy_score(): Calculate overall intimacy health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "intimacy_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTIMACY_LOG = DATA_DIR / "intimacies.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class IntimacyEntry:
    """A tracked intimacy moment."""
    entry_id: str = ""
    moment: str = ""  # what happened
    intimacy_type: str = ""  # emotional, physical, intellectual, spiritual, experiential
    depth: float = 0.0  # 0-1
    safety: float = 0.0  # 0-1
    reciprocity: float = 0.0  # 0-1
    satisfaction: float = 0.0  # 0-1
    repair: float = 0.0  # 0-1 was a repair attempted?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class IntimacyCoach:
    """
    Intelligent intimacy coach with avoidance detection and closeness cultivation.
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
            "avg_depth": 0.0,
            "avg_satisfaction": 0.0,
            "avoidance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_intimacy(self, moment: str = "", intimacy_type: str = "", depth: float = 0.0, safety: float = 0.0, reciprocity: float = 0.0, satisfaction: float = 0.0, repair: float = 0.0, notes: str = "") -> IntimacyEntry:
        """Record an intimacy moment."""
        entry_id = f"int_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = IntimacyEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            intimacy_type=intimacy_type or "emotional",
            depth=depth,
            safety=safety,
            reciprocity=reciprocity,
            satisfaction=satisfaction,
            repair=repair,
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

    def get_intimacy_stats(self) -> Dict[str, Any]:
        """Get intimacy pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "safety_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.intimacy_type]["count"] += 1
            by_type[e.intimacy_type]["depth_sum"] += e.depth
            by_type[e.intimacy_type]["safety_sum"] += e.safety
            by_type[e.intimacy_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_safety": round(data["safety_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Depth analysis
        high_depth = [e for e in self._entries if e.depth > 0.7]
        low_depth = [e for e in self._entries if e.depth < 0.4]
        if high_depth and low_depth:
            high_depth_sat = sum(e.satisfaction for e in high_depth) / len(high_depth)
            low_depth_sat = sum(e.satisfaction for e in low_depth) / len(low_depth)
            high_depth_safe = sum(e.safety for e in high_depth) / len(high_depth)
            low_depth_safe = sum(e.safety for e in low_depth) / len(low_depth)
        else:
            high_depth_sat = 0
            low_depth_sat = 0
            high_depth_safe = 0
            low_depth_safe = 0

        # Safety analysis
        high_safe = [e for e in self._entries if e.safety > 0.7]
        low_safe = [e for e in self._entries if e.safety < 0.4]
        if high_safe and low_safe:
            high_safe_rec = sum(e.reciprocity for e in high_safe) / len(high_safe)
            low_safe_rec = sum(e.reciprocity for e in low_safe) / len(low_safe)
        else:
            high_safe_rec = 0
            low_safe_rec = 0

        # Avoidance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            avoidance_risk = recent_depth < 0.3 and recent_sat < 0.3
        else:
            avoidance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "depth_impact": {
                "high_depth_satisfaction": round(high_depth_sat, 2),
                "low_depth_satisfaction": round(low_depth_sat, 2),
                "high_depth_safety": round(high_depth_safe, 2),
                "low_depth_safety": round(low_depth_safe, 2),
            },
            "safety_effect": {
                "high_safety_reciprocity": round(high_safe_rec, 2),
                "low_safety_reciprocity": round(low_safe_rec, 2),
            },
            "avoidance_risk": avoidance_risk,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
        }

    def get_intimacy_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get intimacy suggestion."""
        suggestions = [
            "Intimacy is not sex. It's not even touch. It's the willingness to be known. To be seen. To let someone into your inner world. Most people have sex without intimacy. They touch without connection. Don't be most people.",
            "Start with emotional intimacy. Share your day. Your thoughts. Your fears. Your dreams. Before you share your body, share your mind. Before you share your mind, share your heart.",
            "Intimacy requires safety. You cannot be intimate with someone who judges you. Who uses your vulnerability against you. Who isn't trustworthy. Choose your intimates wisely. Safety first.",
            "Reciprocity is the heartbeat of intimacy. It cannot be one-sided. If you're always sharing and they're always receiving, that's not intimacy. That's a confession. Intimacy is mutual. Both giving. Both receiving.",
            "Physical intimacy without emotional intimacy is empty. Emotional intimacy without physical intimacy is incomplete. Spiritual intimacy without either is disconnected. True intimacy integrates all three.",
            "Repair ruptures quickly. When intimacy is broken, fix it. Apologize. Explain. Reconnect. Don't let the rupture become a wall. Intimacy is repaired in the repair, not in the perfection.",
            "Ask questions that go deeper. Not 'how was your day?' but 'what was the best part of your day and why?' Not 'are you okay?' but 'what do you need right now?' Depth creates intimacy.",
            "Be present during intimate moments. Not on your phone. Not thinking about work. Not planning what to say next. Present. Here. Now. With this person. That's the gift. That's the intimacy.",
            "Intimacy is built in small moments. The glance across the room. The hand on the shoulder. The question asked with genuine curiosity. These are not trivial. They're the threads of intimacy.",
            "The person who fears intimacy fears being known. Because being known means being seen. And being seen means being vulnerable. And being vulnerable means risking rejection. But the alternative is loneliness. Choose vulnerability."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One deeper question. One honest share. One moment of genuine presence. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. An intimate conversation. A repair attempt. A vulnerability practice. Medium intimacy work."
        else:
            capacity_note = "Good capacity. Deep intimacy work. A systematic practice of closeness and connection. You have the strength to be truly known."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Intimacy is the most human experience. And the most feared. Because intimacy means being known. And being known means being vulnerable. And being vulnerable means risking rejection. So most people settle for proximity instead of intimacy. They live with people. They sleep with people. They share space with people. But they don't share themselves. They don't let anyone in. And they wonder why they feel lonely. Why they feel unseen. Why their relationships feel hollow. The work of intimacy coaching is about learning to let people in. About creating safety. About building trust. About sharing yourself. And about understanding that the risk of rejection is less painful than the certainty of loneliness. Because intimacy is the antidote to the fundamental human condition of isolation. And it's available to anyone who is willing to be brave enough to be known."
        }

    def get_intimacy_score(self) -> int:
        """Calculate overall intimacy health (0-100)."""
        if not self._entries:
            return 25

        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_safe = sum(e.safety for e in self._entries) / len(self._entries)
        avg_recip = sum(e.reciprocity for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_repair = sum(e.repair for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_sat = 0

        # Avoidance penalty
        avoid_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_depth_30 = sum(e.depth for e in last_30) / len(last_30)
            recent_sat_30 = sum(e.satisfaction for e in last_30) / len(last_30)
            if recent_depth_30 < 0.3 and recent_sat_30 < 0.3:
                avoid_penalty = 15

        # Type variety
        unique_types = len(set(e.intimacy_type for e in self._entries))

        score = (avg_depth * 25) + (avg_safe * 20) + (avg_recip * 15) + (avg_sat * 15) + (avg_repair * 10) + (recent_depth * 5) + (recent_sat * 5) + (unique_types * 2) - avoid_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_depth = sum(e.depth for e in recent) / len(recent)
                recent_sat = sum(e.satisfaction for e in recent) / len(recent)
                self._stats["avoidance_risk"] = recent_depth < 0.3 and recent_sat < 0.3
            else:
                self._stats["avoidance_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intimacy_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intimacy_coach")

    def _log_entry(self, entry: IntimacyEntry):
        try:
            with open(INTIMACY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "intimacy_type": entry.intimacy_type,
                    "depth": entry.depth,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.intimacy_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ic_instance: Optional[IntimacyCoach] = None
_ic_lock = threading.Lock()


def get_intimacy_coach() -> IntimacyCoach:
    global _ic_instance
    with _ic_lock:
        if _ic_instance is None:
            _ic_instance = IntimacyCoach()
        return _ic_instance
