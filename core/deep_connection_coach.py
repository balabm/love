"""
LOVE Deep Connection Coach — Bonding Intelligence (Modern AI Pattern)

Most people have relationships. Few have connections. This coach:

1. CONNECTION TRACKING
   - Record deep connection moments and their characteristics
   - Track connection types (friendship, family, romantic, community, mentorship, self)
   - Log depth, authenticity, reciprocity, and meaning of connection

2. PATTERN ANALYSIS
   - Identify the user's connection profile (isolated, surface, developing, deep)
   - Find connection patterns that create belonging vs loneliness
   - Detect chronic disconnection and its costs

3. CONNECTION BUILDING
   - Suggest practices for deepening existing connections
   - Provide frameworks for creating new meaningful bonds
   - Recommend practices for maintaining connection over time

4. BELONGING CULTIVATION
   - Track the correlation between connection depth and life satisfaction
   - Alert when isolation is becoming the default
   - Celebrate moments of genuine, deep connection

Architecture:
- record_connection(person, type, depth, authenticity, reciprocity, meaning): Log connection
- get_connection_stats(): Get connection pattern analysis
- get_connection_suggestion(capacity, context): Get suggestion
- get_connection_score(): Calculate overall connection health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "deep_connection_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONNECTION_LOG = DATA_DIR / "connections.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ConnectionEntry:
    """A tracked deep connection moment."""
    entry_id: str = ""
    person: str = ""  # who was connected with
    connection_type: str = ""  # friendship, family, romantic, community, mentorship, self
    depth: float = 0.0  # 0-1
    authenticity: float = 0.0  # 0-1
    reciprocity: float = 0.0  # 0-1
    meaning: float = 0.0  # 0-1
    maintenance: float = 0.0  # 0-1 effort to maintain
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DeepConnectionCoach:
    """
    Intelligent deep connection coach with isolation detection and belonging cultivation.
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
            "avg_meaning": 0.0,
            "isolation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_connection(self, person: str = "", connection_type: str = "", depth: float = 0.0, authenticity: float = 0.0, reciprocity: float = 0.0, meaning: float = 0.0, maintenance: float = 0.0, notes: str = "") -> ConnectionEntry:
        """Record a deep connection moment."""
        entry_id = f"con_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ConnectionEntry(
            entry_id=entry_id,
            person=person or "unspecified",
            connection_type=connection_type or "friendship",
            depth=depth,
            authenticity=authenticity,
            reciprocity=reciprocity,
            meaning=meaning,
            maintenance=maintenance,
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

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "authenticity_sum": 0.0, "meaning_sum": 0.0})
        for e in self._entries:
            by_type[e.connection_type]["count"] += 1
            by_type[e.connection_type]["depth_sum"] += e.depth
            by_type[e.connection_type]["authenticity_sum"] += e.authenticity
            by_type[e.connection_type]["meaning_sum"] += e.meaning

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_authenticity": round(data["authenticity_sum"] / count, 2),
                "avg_meaning": round(data["meaning_sum"] / count, 2),
            }

        # Depth analysis
        high_depth = [e for e in self._entries if e.depth > 0.7]
        low_depth = [e for e in self._entries if e.depth < 0.4]
        if high_depth and low_depth:
            high_depth_mean = sum(e.meaning for e in high_depth) / len(high_depth)
            low_depth_mean = sum(e.meaning for e in low_depth) / len(low_depth)
            high_depth_auth = sum(e.authenticity for e in high_depth) / len(high_depth)
            low_depth_auth = sum(e.authenticity for e in low_depth) / len(low_depth)
        else:
            high_depth_mean = 0
            low_depth_mean = 0
            high_depth_auth = 0
            low_depth_auth = 0

        # Maintenance analysis
        high_maint = [e for e in self._entries if e.maintenance > 0.7]
        low_maint = [e for e in self._entries if e.maintenance < 0.4]
        if high_maint and low_maint:
            high_maint_depth = sum(e.depth for e in high_maint) / len(high_maint)
            low_maint_depth = sum(e.depth for e in low_maint) / len(low_maint)
        else:
            high_maint_depth = 0
            low_maint_depth = 0

        # Isolation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_mean = sum(e.meaning for e in recent) / len(recent)
            isolation_risk = recent_depth < 0.3 and recent_mean < 0.3
        else:
            isolation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "depth_impact": {
                "high_depth_meaning": round(high_depth_mean, 2),
                "low_depth_meaning": round(low_depth_mean, 2),
                "high_depth_authenticity": round(high_depth_auth, 2),
                "low_depth_authenticity": round(low_depth_auth, 2),
            },
            "maintenance_effect": {
                "high_maintenance_depth": round(high_maint_depth, 2),
                "low_maintenance_depth": round(low_maint_depth, 2),
            },
            "isolation_risk": isolation_risk,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_meaning": round(sum(e.meaning for e in self._entries) / len(self._entries), 2),
        }

    def get_connection_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get connection suggestion."""
        suggestions = [
            "Deep connection is not about quantity. It's about quality. You don't need more friends. You need deeper ones. One person who truly sees you is worth a hundred who merely know you.",
            "Reach out to someone you miss. Not for a reason. Just because. Connection doesn't need a purpose. It needs presence. Send the text. Make the call. Show up.",
            "Ask deeper questions. 'What are you afraid of?' 'What do you dream about?' 'What broke you?' 'What healed you?' Surface questions create surface connections. Depth questions create depth.",
            "Be the person who remembers. Their birthday. Their dog's name. Their story. The small details. Remembering is love made visible. And it builds connection like nothing else.",
            "Connection requires maintenance. Like a garden. You can't plant seeds and walk away. Water them. Weed them. Tend them. Relationships are gardens. Tend them.",
            "Share your struggles. Not to burden. To bond. Vulnerability is the currency of connection. The person who only shares successes is not connecting. They're performing. Share the real.",
            "Listen for the emotion behind the words. 'I'm fine' often means 'I'm not.' 'It's okay' often means 'It hurts.' Listen deeper. Hear what they're not saying.",
            "Create rituals of connection. Weekly calls. Monthly dinners. Annual trips. Rituals create predictability. Predictability creates safety. Safety creates depth.",
            "Connection with self is the foundation. If you don't know yourself, you can't share yourself. Spend time alone. Know your thoughts. Your feelings. Your needs. Then share them.",
            "The person who is connected is never truly alone. Because connection lives in memory. In the people who know you. Who have seen you. Who carry you with them. Build those connections."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One text. One call. One deeper question. One small reach. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A meaningful conversation. A repair attempt. A ritual created. A vulnerability shared. Medium connection work."
        else:
            capacity_note = "Good capacity. Deep connection work. A systematic practice of building and maintaining meaningful bonds. You have the strength to belong."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Deep connection is the antidote to the fundamental human condition of isolation. We are born alone. We die alone. And in between, we long for connection. Real connection. Not proximity. Not acquaintance. Not performance. But the experience of being truly known. Of being truly seen. Of being truly accepted. Most people never experience this. They have relationships. They have conversations. They have interactions. But they don't have connection. Because connection requires vulnerability. It requires authenticity. It requires the willingness to be seen as you are. And that is terrifying. But it's also the only thing that makes life worth living. The work of deep connection coaching is about building the skills to create and maintain meaningful bonds. About learning to be vulnerable. About learning to listen. About learning to remember. And about understanding that the quality of your life is determined by the quality of your connections."
        }

    def get_connection_score(self) -> int:
        """Calculate overall connection health (0-100)."""
        if not self._entries:
            return 25

        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_recip = sum(e.reciprocity for e in self._entries) / len(self._entries)
        avg_mean = sum(e.meaning for e in self._entries) / len(self._entries)
        avg_maint = sum(e.maintenance for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_mean = sum(e.meaning for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_mean = 0

        # Isolation penalty
        iso_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_depth_30 = sum(e.depth for e in last_30) / len(last_30)
            recent_mean_30 = sum(e.meaning for e in last_30) / len(last_30)
            if recent_depth_30 < 0.3 and recent_mean_30 < 0.3:
                iso_penalty = 15

        # Type variety
        unique_types = len(set(e.connection_type for e in self._entries))

        score = (avg_depth * 25) + (avg_auth * 15) + (avg_recip * 15) + (avg_mean * 15) + (avg_maint * 10) + (recent_depth * 5) + (recent_mean * 5) + (unique_types * 2) - iso_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_meaning"] = round(sum(e.meaning for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_depth = sum(e.depth for e in recent) / len(recent)
                recent_mean = sum(e.meaning for e in recent) / len(recent)
                self._stats["isolation_risk"] = recent_depth < 0.3 and recent_mean < 0.3
            else:
                self._stats["isolation_risk"] = False

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

    def _log_entry(self, entry: ConnectionEntry):
        try:
            with open(CONNECTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "person": entry.person,
                    "connection_type": entry.connection_type,
                    "depth": entry.depth,
                    "meaning": entry.meaning,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dcc_instance: Optional[DeepConnectionCoach] = None
_dcc_lock = threading.Lock()


def get_deep_connection_coach() -> DeepConnectionCoach:
    global _dcc_instance
    with _dcc_lock:
        if _dcc_instance is None:
            _dcc_instance = DeepConnectionCoach()
        return _dcc_instance
