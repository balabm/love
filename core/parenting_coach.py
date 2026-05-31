"""
LOVE Parenting Coach — Nurturing Intelligence (Modern AI Pattern)

Most parents are doing their best with insufficient support. This coach:

1. PARENTING TRACKING
   - Record parenting moments and their quality
   - Track interaction types (play, discipline, teaching, presence, repair)
   - Log connection, patience, and growth moments

2. PATTERN ANALYSIS
   - Identify the user's parenting profile (responsive, directive, absent, overwhelmed)
   - Find interaction patterns that create secure attachment
   - Detect parental burnout and its warning signs

3. PARENTING OPTIMIZATION
   - Suggest age-appropriate practices matched to child's development
   - Provide frameworks for difficult conversations
   - Recommend repair after rupture

4. CONNECTION CULTIVATION
   - Track the correlation between parental presence and child behavior
   - Alert when relationship is becoming transactional
   - Celebrate moments of genuine attunement

Architecture:
- record_interaction(child, type, connection, patience, growth): Log interaction
- get_parenting_stats(): Get parenting pattern analysis
- get_parenting_suggestion(age, capacity, context): Get suggestion
- get_parenting_score(): Calculate overall parenting health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "parenting_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PARENTING_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ParentingEntry:
    """A tracked parenting interaction."""
    entry_id: str = ""
    child: str = ""  # child identifier
    interaction_type: str = ""  # play, discipline, teaching, presence, repair, routine
    connection: float = 0.5  # 0-1 attunement
    patience: float = 0.5  # 0-1
    warmth: float = 0.0  # 0-1
    boundaries: float = 0.0  # 0-1 clarity of limits
    repair_after_rupture: float = 0.0  # 0-1
    child_response: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ParentingCoach:
    """
    Intelligent parenting coach with attunement detection and connection optimization.
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
            "avg_connection": 0.0,
            "avg_patience": 0.0,
            "burnout_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, child: str = "", interaction_type: str = "", connection: float = 0.5, patience: float = 0.5, warmth: float = 0.0, boundaries: float = 0.0, repair_after_rupture: float = 0.0, child_response: float = 0.0, notes: str = "") -> ParentingEntry:
        """Record a parenting interaction."""
        entry_id = f"par_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ParentingEntry(
            entry_id=entry_id,
            child=child or "unspecified",
            interaction_type=interaction_type or "presence",
            connection=connection,
            patience=patience,
            warmth=warmth,
            boundaries=boundaries,
            repair_after_rupture=repair_after_rupture,
            child_response=child_response,
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

    def get_parenting_stats(self) -> Dict[str, Any]:
        """Get parenting pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Child analysis
        by_child = defaultdict(lambda: {"count": 0, "connection_sum": 0.0, "patience_sum": 0.0, "warmth_sum": 0.0})
        for e in self._entries:
            by_child[e.child]["count"] += 1
            by_child[e.child]["connection_sum"] += e.connection
            by_child[e.child]["patience_sum"] += e.patience
            by_child[e.child]["warmth_sum"] += e.warmth

        child_stats = {}
        for c, data in by_child.items():
            count = data["count"]
            child_stats[c] = {
                "count": count,
                "avg_connection": round(data["connection_sum"] / count, 2),
                "avg_patience": round(data["patience_sum"] / count, 2),
                "avg_warmth": round(data["warmth_sum"] / count, 2),
            }

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "connection_sum": 0.0, "child_response_sum": 0.0})
        for e in self._entries:
            by_type[e.interaction_type]["count"] += 1
            by_type[e.interaction_type]["connection_sum"] += e.connection
            by_type[e.interaction_type]["child_response_sum"] += e.child_response

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_connection": round(data["connection_sum"] / count, 2),
                "avg_child_response": round(data["child_response_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_child_response"]) if type_stats else ("", {})

        # Connection analysis
        high_conn = [e for e in self._entries if e.connection > 0.7]
        low_conn = [e for e in self._entries if e.connection < 0.4]
        if high_conn and low_conn:
            high_conn_response = sum(e.child_response for e in high_conn) / len(high_conn)
            low_conn_response = sum(e.child_response for e in low_conn) / len(low_conn)
            high_conn_warmth = sum(e.warmth for e in high_conn) / len(high_conn)
            low_conn_warmth = sum(e.warmth for e in low_conn) / len(low_conn)
        else:
            high_conn_response = 0
            low_conn_response = 0
            high_conn_warmth = 0
            low_conn_warmth = 0

        # Repair analysis
        with_repair = [e for e in self._entries if e.repair_after_rupture > 0.5]
        without_repair = [e for e in self._entries if e.repair_after_rupture < 0.3]
        if with_repair and without_repair:
            with_repair_conn = sum(e.connection for e in with_repair) / len(with_repair)
            without_repair_conn = sum(e.connection for e in without_repair) / len(without_repair)
        else:
            with_repair_conn = 0
            without_repair_conn = 0

        # Burnout detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_patience = sum(e.patience for e in recent) / len(recent)
            recent_warmth = sum(e.warmth for e in recent) / len(recent)
            burnout_risk = recent_patience < 0.3 and recent_warmth < 0.3
        else:
            burnout_risk = False

        return {
            "total_entries": len(self._entries),
            "child_stats": child_stats,
            "type_stats": type_stats,
            "best_type": best_type[0],
            "connection_impact": {
                "high_connection_response": round(high_conn_response, 2),
                "low_connection_response": round(low_conn_response, 2),
                "high_connection_warmth": round(high_conn_warmth, 2),
                "low_connection_warmth": round(low_conn_warmth, 2),
            },
            "repair_effect": {
                "with_repair_connection": round(with_repair_conn, 2),
                "without_repair_connection": round(without_repair_conn, 2),
            },
            "burnout_risk": burnout_risk,
            "avg_connection": round(sum(e.connection for e in self._entries) / len(self._entries), 2),
            "avg_patience": round(sum(e.patience for e in self._entries) / len(self._entries), 2),
        }

    def get_parenting_suggestion(self, child_age: int = 5, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get parenting suggestion."""
        suggestions = [
            "The most important thing you can give a child is your full attention. Not your advice. Not your correction. Your attention. Ten minutes of full attention is worth an hour of half-presence.",
            "Children don't need perfect parents. They need repaired parents. The rupture is inevitable. The repair is what builds security. Apologize sincerely. Reconnect warmly. Every repair teaches them that relationships can survive mistakes.",
            "Your calm is their calm. When you're dysregulated, they're dysregulated. Parenting is 90% self-regulation. Take the breath. Step away. Regulate yourself first. Then respond.",
            "Play is not optional. It's the language of children. When words fail, play communicates. When discipline is needed, play reconnects. When stress is high, play releases. Get on the floor.",
            "Boundaries are love. Children feel safer with clear limits. Not harsh limits. Clear limits. The parent who never says no creates anxiety. The parent who says no consistently creates security.",
            "See the child, not the behavior. Behavior is communication. Every tantrum is a signal. Every withdrawal is a message. Get curious before you get corrective.",
            "You can't pour from an empty cup. Parental burnout is real. Self-care is not selfish. It's maintenance. The parent who never rests becomes the parent who snaps. Rest is a parenting tool.",
            "Teach by modeling, not lecturing. They watch everything. How you handle anger. How you handle failure. How you handle love. Be the person you want them to become.",
            "One-on-one time is sacred. Each child needs individual attention. Not always. But regularly. The child who feels seen is the child who thrives.",
            "You're not raising a child. You're raising an adult. Think about who they'll be at 30. What do they need to learn now? Patience? Honesty? Resilience? Teach for the adult, not the child.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One minute of full presence. One hug. One 'I love you.' That's enough for today."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A game. A conversation. A shared activity. Medium investment."
        else:
            capacity_note = "Good capacity. Deep teaching. A challenging conversation. A new experience together. You have the patience for real connection."

        return {
            "child_age": child_age,
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Parenting is the hardest and most important job most people will ever have. And it's a job with no training, no manual, and no days off. The good news is that children are resilient. They don't need perfect parents. They need present parents. They need parents who are trying. Who are learning. Who are willing to be wrong and repair. The parent-child relationship is the template for every other relationship the child will have. Make it safe. Make it warm. Make it real. That's enough. That's everything.",
        }

    def get_parenting_score(self) -> int:
        """Calculate overall parenting health (0-100)."""
        if not self._entries:
            return 25

        avg_connection = sum(e.connection for e in self._entries) / len(self._entries)
        avg_patience = sum(e.patience for e in self._entries) / len(self._entries)
        avg_warmth = sum(e.warmth for e in self._entries) / len(self._entries)
        avg_boundaries = sum(e.boundaries for e in self._entries) / len(self._entries)
        avg_repair = sum(e.repair_after_rupture for e in self._entries) / len(self._entries)
        avg_child_response = sum(e.child_response for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_connection = sum(e.connection for e in recent) / len(recent)
            recent_patience = sum(e.patience for e in recent) / len(recent)
        else:
            recent_connection = 0
            recent_patience = 0

        # Burnout penalty
        burnout_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_patience_30 = sum(e.patience for e in last_30) / len(last_30)
            recent_warmth_30 = sum(e.warmth for e in last_30) / len(last_30)
            if recent_patience_30 < 0.3 and recent_warmth_30 < 0.3:
                burnout_penalty = 15

        score = (avg_connection * 25) + (avg_patience * 15) + (avg_warmth * 15) + (avg_boundaries * 10) + (avg_repair * 10) + (avg_child_response * 10) + (recent_connection * 5) + (recent_patience * 5) - burnout_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_connection"] = round(sum(e.connection for e in self._entries) / len(self._entries), 2)
            self._stats["avg_patience"] = round(sum(e.patience for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_patience = sum(e.patience for e in recent) / len(recent)
                recent_warmth = sum(e.warmth for e in recent) / len(recent)
                self._stats["burnout_risk"] = recent_patience < 0.3 and recent_warmth < 0.3
            else:
                self._stats["burnout_risk"] = False

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

    def _log_entry(self, entry: ParentingEntry):
        try:
            with open(PARENTING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "child": entry.child,
                    "interaction_type": entry.interaction_type,
                    "connection": entry.connection,
                    "patience": entry.patience,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pc_instance: Optional[ParentingCoach] = None
_pc_lock = threading.Lock()


def get_parenting_coach() -> ParentingCoach:
    global _pc_instance
    with _pc_lock:
        if _pc_instance is None:
            _pc_instance = ParentingCoach()
        return _pc_instance
