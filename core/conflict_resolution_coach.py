"""
LOVE Conflict Resolution Coach — Relational Repair Intelligence (Modern AI Pattern)

Most conflicts are handled poorly because people lack skills. This coach:

1. CONFLICT TRACKING
   - Record conflicts and their characteristics
   - Track conflict types (values, resources, communication, power, identity)
   - Log resolution quality, repair, and learning from conflicts

2. PATTERN ANALYSIS
   - Identify the user's conflict profile (avoidant, confrontational, collaborative, compromising)
   - Find conflict patterns that lead to resolution vs escalation
   - Detect recurring conflict themes and their triggers

3. RESOLUTION OPTIMIZATION
   - Suggest resolution strategies matched to conflict type and relationship
   - Provide frameworks for difficult conversations
   - Recommend repair practices after conflict

4. RELATIONSHIP CULTIVATION
   - Track the correlation between resolution quality and relationship health
   - Alert when conflicts are becoming destructive patterns
   - Celebrate moments of genuine repair and growth through conflict

Architecture:
- record_conflict(conflict, type, resolution, repair, learning): Log conflict
- get_conflict_stats(): Get conflict pattern analysis
- get_resolution_suggestion(capacity, context): Get suggestion
- get_conflict_score(): Calculate overall conflict health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "conflict_resolution_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFLICT_LOG = DATA_DIR / "conflicts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ConflictEntry:
    """A tracked conflict."""
    entry_id: str = ""
    conflict: str = ""  # what the conflict was about
    conflict_type: str = ""  # values, resources, communication, power, identity
    resolution: float = 0.0  # 0-1 how well it was resolved
    repair: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    relationship_impact: float = 0.0  # 0-1
    self_awareness: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ConflictResolutionCoach:
    """
    Intelligent conflict resolution coach with repair detection and relationship cultivation.
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
            "avg_resolution": 0.0,
            "avg_repair": 0.0,
            "destructive_pattern_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_conflict(self, conflict: str = "", conflict_type: str = "", resolution: float = 0.0, repair: float = 0.0, learning: float = 0.0, relationship_impact: float = 0.0, self_awareness: float = 0.0, notes: str = "") -> ConflictEntry:
        """Record a conflict."""
        entry_id = f"cnf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ConflictEntry(
            entry_id=entry_id,
            conflict=conflict or "unspecified",
            conflict_type=conflict_type or "communication",
            resolution=resolution,
            repair=repair,
            learning=learning,
            relationship_impact=relationship_impact,
            self_awareness=self_awareness,
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

    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get conflict pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "resolution_sum": 0.0, "repair_sum": 0.0, "learning_sum": 0.0})
        for e in self._entries:
            by_type[e.conflict_type]["count"] += 1
            by_type[e.conflict_type]["resolution_sum"] += e.resolution
            by_type[e.conflict_type]["repair_sum"] += e.repair
            by_type[e.conflict_type]["learning_sum"] += e.learning

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_resolution": round(data["resolution_sum"] / count, 2),
                "avg_repair": round(data["repair_sum"] / count, 2),
                "avg_learning": round(data["learning_sum"] / count, 2),
            }

        # Resolution analysis
        high_res = [e for e in self._entries if e.resolution > 0.7]
        low_res = [e for e in self._entries if e.resolution < 0.4]
        if high_res and low_res:
            high_res_repair = sum(e.repair for e in high_res) / len(high_res)
            low_res_repair = sum(e.repair for e in low_res) / len(low_res)
            high_res_rel = sum(e.relationship_impact for e in high_res) / len(high_res)
            low_res_rel = sum(e.relationship_impact for e in low_res) / len(low_res)
        else:
            high_res_repair = 0
            low_res_repair = 0
            high_res_rel = 0
            low_res_rel = 0

        # Self-awareness analysis
        high_sa = [e for e in self._entries if e.self_awareness > 0.7]
        low_sa = [e for e in self._entries if e.self_awareness < 0.4]
        if high_sa and low_sa:
            high_sa_res = sum(e.resolution for e in high_sa) / len(high_sa)
            low_sa_res = sum(e.resolution for e in low_sa) / len(low_sa)
        else:
            high_sa_res = 0
            low_sa_res = 0

        # Destructive pattern detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_resolution = sum(e.resolution for e in recent) / len(recent)
            recent_repair = sum(e.repair for e in recent) / len(recent)
            destructive_pattern_risk = recent_resolution < 0.4 and recent_repair < 0.3
        else:
            destructive_pattern_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "resolution_impact": {
                "high_resolution_repair": round(high_res_repair, 2),
                "low_resolution_repair": round(low_res_repair, 2),
                "high_resolution_relationship": round(high_res_rel, 2),
                "low_resolution_relationship": round(low_res_rel, 2),
            },
            "self_awareness_effect": {
                "high_awareness_resolution": round(high_sa_res, 2),
                "low_awareness_resolution": round(low_sa_res, 2),
            },
            "destructive_pattern_risk": destructive_pattern_risk,
            "avg_resolution": round(sum(e.resolution for e in self._entries) / len(self._entries), 2),
            "avg_repair": round(sum(e.repair for e in self._entries) / len(self._entries), 2),
        }

    def get_resolution_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get resolution suggestion."""
        suggestions = [
            "Name the conflict. Not the person. 'We have a disagreement about money' not 'You're bad with money.' Separate the issue from the identity.",
            "Listen first. Really listen. Not to respond. To understand. Repeat back what you heard. 'What I'm hearing is...' Most conflicts are listening failures.",
            "Find the need beneath the position. They want X. Why? What need are they trying to meet? Security? Respect? Autonomy? Address the need, not the demand.",
            "Take responsibility for your part. Even if it's 10%. Own it. 'I could have communicated better.' Responsibility disarms defensiveness.",
            "Use 'I' statements. 'I feel hurt when...' not 'You always...' Own your experience. Don't accuse. It changes the entire conversation.",
            "Take a break if needed. Not to avoid. To regulate. 'I need 20 minutes to calm down. Then I'll be back.' Disengagement with commitment is not avoidance.",
            "Focus on the future. Not the past. What do we want going forward? The past is a reference. The future is where solutions live.",
            "Repair after. Even if you resolved it well. An apology. A gesture. A check-in. Repair says: our relationship matters more than this conflict.",
            "Conflict is not bad. It's data. It tells you what's important to someone. What they need. What they fear. The goal is not zero conflict. It's healthy conflict.",
            "The person you're in conflict with is not your enemy. They're a person with needs, fears, and a different perspective. Treat them like a person. Even when they're wrong. Especially when they're wrong.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small repair. One honest sentence. One moment of listening. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A real conversation. A framework. A repair attempt. Medium investment in resolution."
        else:
            capacity_note = "Good capacity. A deep resolution process. A pattern conversation. A relationship reset. You have the energy for real repair."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Conflict is inevitable. In any relationship worth having, there will be disagreement. The question is not whether you will conflict. It's how. The people with the best relationships are not the people who never fight. They're the people who fight well. Who listen. Who repair. Who take responsibility. Who stay in the conversation even when it's hard. Conflict handled well deepens intimacy. It builds trust. It creates understanding. Conflict handled poorly destroys relationships. The difference is skill. And skill can be learned.",
        }

    def get_conflict_score(self) -> int:
        """Calculate overall conflict health (0-100)."""
        if not self._entries:
            return 25

        avg_resolution = sum(e.resolution for e in self._entries) / len(self._entries)
        avg_repair = sum(e.repair for e in self._entries) / len(self._entries)
        avg_learning = sum(e.learning for e in self._entries) / len(self._entries)
        avg_rel_impact = sum(e.relationship_impact for e in self._entries) / len(self._entries)
        avg_self_aware = sum(e.self_awareness for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_resolution = sum(e.resolution for e in recent) / len(recent)
            recent_repair = sum(e.repair for e in recent) / len(recent)
        else:
            recent_resolution = 0
            recent_repair = 0

        # Destructive pattern penalty
        destruct_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if last_90:
            recent_res_90 = sum(e.resolution for e in last_90) / len(last_90)
            recent_rep_90 = sum(e.repair for e in last_90) / len(last_90)
            if recent_res_90 < 0.4 and recent_rep_90 < 0.3:
                destruct_penalty = 20

        # Type variety
        unique_types = len(set(e.conflict_type for e in self._entries))

        score = (avg_resolution * 30) + (avg_repair * 20) + (avg_learning * 10) + (avg_rel_impact * 15) + (avg_self_aware * 10) + (recent_resolution * 10) + (recent_repair * 5) + (unique_types * 2) - destruct_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_resolution"] = round(sum(e.resolution for e in self._entries) / len(self._entries), 2)
            self._stats["avg_repair"] = round(sum(e.repair for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_resolution = sum(e.resolution for e in recent) / len(recent)
                recent_repair = sum(e.repair for e in recent) / len(recent)
                self._stats["destructive_pattern_risk"] = recent_resolution < 0.4 and recent_repair < 0.3
            else:
                self._stats["destructive_pattern_risk"] = False

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

    def _log_entry(self, entry: ConflictEntry):
        try:
            with open(CONFLICT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "conflict": entry.conflict,
                    "conflict_type": entry.conflict_type,
                    "resolution": entry.resolution,
                    "repair": entry.repair,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_crc_instance: Optional[ConflictResolutionCoach] = None
_crc_lock = threading.Lock()


def get_conflict_resolution_coach() -> ConflictResolutionCoach:
    global _crc_instance
    with _crc_lock:
        if _crc_instance is None:
            _crc_instance = ConflictResolutionCoach()
        return _crc_instance
