"""
LOVE Family Harmony Builder — Domestic Ecosystem Intelligence (Modern AI Pattern)

Most families coexist rather than connect. This builder:

1. FAMILY TRACKING
   - Record family interactions and their quality
   - Track interaction types (meal, conflict, ritual, support, fun, decision)
   - Log harmony, communication, and repair moments

2. PATTERN ANALYSIS
   - Identify the user's family profile (harmonious, fractured, distant, enmeshed)
   - Find interaction patterns that create family resilience
   - Detect chronic conflict patterns and their triggers

3. HARMONY BUILDING
   - Suggest rituals and practices for family connection
   - Provide frameworks for family decision-making
   - Recommend repair strategies after rupture

4. RELATIONSHIP CULTIVATION
   - Track the correlation between family harmony and individual wellbeing
   - Alert when family is becoming a source of stress
   - Celebrate moments of genuine family joy

Architecture:
- record_interaction(member, type, harmony, communication, repair): Log interaction
- get_family_stats(): Get family pattern analysis
- get_harmony_suggestion(capacity, context): Get suggestion
- get_family_score(): Calculate overall family health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "family_harmony_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FAMILY_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class FamilyEntry:
    """A tracked family interaction."""
    entry_id: str = ""
    member: str = ""  # family member involved
    interaction_type: str = ""  # meal, conflict, ritual, support, fun, decision
    harmony: float = 0.5  # 0-1
    communication: float = 0.5  # 0-1 clarity and respect
    support: float = 0.0  # 0-1
    repair: float = 0.0  # 0-1 repair after difficulty
    fun: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class FamilyHarmonyBuilder:
    """
    Intelligent family harmony builder with conflict detection and repair optimization.
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
            "avg_harmony": 0.0,
            "avg_communication": 0.0,
            "chronic_conflict_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, member: str = "", interaction_type: str = "", harmony: float = 0.5, communication: float = 0.5, support: float = 0.0, repair: float = 0.0, fun: float = 0.0, notes: str = "") -> FamilyEntry:
        """Record a family interaction."""
        entry_id = f"fam_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = FamilyEntry(
            entry_id=entry_id,
            member=member or "unspecified",
            interaction_type=interaction_type or "casual",
            harmony=harmony,
            communication=communication,
            support=support,
            repair=repair,
            fun=fun,
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

    def get_family_stats(self) -> Dict[str, Any]:
        """Get family pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Member analysis
        by_member = defaultdict(lambda: {"count": 0, "harmony_sum": 0.0, "communication_sum": 0.0, "support_sum": 0.0})
        for e in self._entries:
            by_member[e.member]["count"] += 1
            by_member[e.member]["harmony_sum"] += e.harmony
            by_member[e.member]["communication_sum"] += e.communication
            by_member[e.member]["support_sum"] += e.support

        member_stats = {}
        for m, data in by_member.items():
            count = data["count"]
            member_stats[m] = {
                "count": count,
                "avg_harmony": round(data["harmony_sum"] / count, 2),
                "avg_communication": round(data["communication_sum"] / count, 2),
                "avg_support": round(data["support_sum"] / count, 2),
            }

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "harmony_sum": 0.0, "fun_sum": 0.0})
        for e in self._entries:
            by_type[e.interaction_type]["count"] += 1
            by_type[e.interaction_type]["harmony_sum"] += e.harmony
            by_type[e.interaction_type]["fun_sum"] += e.fun

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_harmony": round(data["harmony_sum"] / count, 2),
                "avg_fun": round(data["fun_sum"] / count, 2),
            }

        # Conflict analysis
        conflicts = [e for e in self._entries if e.interaction_type == "conflict"]
        if conflicts:
            avg_conflict_harmony = sum(e.harmony for e in conflicts) / len(conflicts)
            avg_conflict_repair = sum(e.repair for e in conflicts) / len(conflicts)
            avg_conflict_comm = sum(e.communication for e in conflicts) / len(conflicts)
        else:
            avg_conflict_harmony = 0
            avg_conflict_repair = 0
            avg_conflict_comm = 0

        # Repair analysis
        with_repair = [e for e in self._entries if e.repair > 0.5]
        without_repair = [e for e in self._entries if e.repair < 0.3]
        if with_repair and without_repair:
            with_repair_harmony = sum(e.harmony for e in with_repair) / len(with_repair)
            without_repair_harmony = sum(e.harmony for e in without_repair) / len(without_repair)
        else:
            with_repair_harmony = 0
            without_repair_harmony = 0

        # Chronic conflict detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_harmony = sum(e.harmony for e in recent) / len(recent)
            recent_comm = sum(e.communication for e in recent) / len(recent)
            chronic_conflict_risk = recent_harmony < 0.4 and recent_comm < 0.4
        else:
            chronic_conflict_risk = False

        return {
            "total_entries": len(self._entries),
            "member_stats": member_stats,
            "type_stats": type_stats,
            "conflict_stats": {
                "avg_conflict_harmony": round(avg_conflict_harmony, 2),
                "avg_conflict_repair": round(avg_conflict_repair, 2),
                "avg_conflict_communication": round(avg_conflict_comm, 2),
            },
            "repair_effect": {
                "with_repair_harmony": round(with_repair_harmony, 2),
                "without_repair_harmony": round(without_repair_harmony, 2),
            },
            "chronic_conflict_risk": chronic_conflict_risk,
            "avg_harmony": round(sum(e.harmony for e in self._entries) / len(self._entries), 2),
            "avg_communication": round(sum(e.communication for e in self._entries) / len(self._entries), 2),
        }

    def get_harmony_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get harmony suggestion."""
        suggestions = [
            "Eat together. Not every meal. But some meals. The table is the original family technology. Conversation flows. Connection happens. Put the phones away.",
            "Create a family ritual. Friday movie night. Sunday breakfast. Annual camping trip. Rituals create belonging. They say: we are a family and this is what we do.",
            "Appreciate out loud. Name what each person did well today. Gratitude in front of each other creates positive culture. Complaints are easy. Appreciation is a practice.",
            "Deal with conflict directly. Not through silence. Not through sarcasm. Direct, kind, clear. Conflict avoided becomes resentment stored. Conflict addressed becomes intimacy built.",
            "Support individual interests. The family that celebrates each member's uniqueness is stronger than the family that demands conformity. Go to their game. Ask about their project. Show interest.",
            "Laugh together. Find something funny. Watch comedy. Tell jokes. Play games. Families that laugh together survive stress together. Humor is family glue.",
            "Make decisions together. Even small ones. What to eat. Where to go. Everyone gets a voice. The family where only one person decides becomes a hierarchy. Not a team.",
            "Touch base daily. Five minutes. How was your day? Not as information gathering. As care. The family that checks in daily is the family that stays connected.",
            "Repair fast. When someone is hurt, don't wait. Apologize. Acknowledge. Make it right. The family that repairs quickly is the family that trusts deeply.",
            "Family is not a destination. It's a practice. It requires intention every day. The families that are close are not luckier. They're more deliberate. They choose connection. Again and again.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One kind word. One shared meal. One moment of presence. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A family activity. A conversation. A repair. Medium investment."
        else:
            capacity_note = "Good capacity. A new ritual. A family meeting. A shared adventure. You have the energy to build real family culture."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Family is the first community and the last refuge. It's where we learn about love, conflict, repair, and belonging. The quality of your family relationships is one of the strongest predictors of your overall life satisfaction. Not because family is always easy. Because family is always real. The work of family is the work of showing up. Again and again. Through conflict. Through distance. Through change. The family that lasts is not the family that never struggles. It's the family that never stops repairing.",
        }

    def get_family_score(self) -> int:
        """Calculate overall family health (0-100)."""
        if not self._entries:
            return 25

        avg_harmony = sum(e.harmony for e in self._entries) / len(self._entries)
        avg_comm = sum(e.communication for e in self._entries) / len(self._entries)
        avg_support = sum(e.support for e in self._entries) / len(self._entries)
        avg_repair = sum(e.repair for e in self._entries) / len(self._entries)
        avg_fun = sum(e.fun for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_harmony = sum(e.harmony for e in recent) / len(recent)
            recent_comm = sum(e.communication for e in recent) / len(recent)
        else:
            recent_harmony = 0
            recent_comm = 0

        # Chronic conflict penalty
        conflict_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_harmony_30 = sum(e.harmony for e in last_30) / len(last_30)
            recent_comm_30 = sum(e.communication for e in last_30) / len(last_30)
            if recent_harmony_30 < 0.4 and recent_comm_30 < 0.4:
                conflict_penalty = 15

        # Member variety
        unique_members = len(set(e.member for e in self._entries))

        score = (avg_harmony * 25) + (avg_comm * 20) + (avg_support * 15) + (avg_repair * 15) + (avg_fun * 10) + (recent_harmony * 5) + (recent_comm * 5) + (unique_members * 2) - conflict_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_harmony"] = round(sum(e.harmony for e in self._entries) / len(self._entries), 2)
            self._stats["avg_communication"] = round(sum(e.communication for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_harmony = sum(e.harmony for e in recent) / len(recent)
                recent_comm = sum(e.communication for e in recent) / len(recent)
                self._stats["chronic_conflict_risk"] = recent_harmony < 0.4 and recent_comm < 0.4
            else:
                self._stats["chronic_conflict_risk"] = False

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

    def _log_entry(self, entry: FamilyEntry):
        try:
            with open(FAMILY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "member": entry.member,
                    "interaction_type": entry.interaction_type,
                    "harmony": entry.harmony,
                    "communication": entry.communication,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_fhb_instance: Optional[FamilyHarmonyBuilder] = None
_fhb_lock = threading.Lock()


def get_family_harmony_builder() -> FamilyHarmonyBuilder:
    global _fhb_instance
    with _fhb_lock:
        if _fhb_instance is None:
            _fhb_instance = FamilyHarmonyBuilder()
        return _fhb_instance
