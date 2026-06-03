"""
LOVE Vulnerable Communication Trainer — Courage Intelligence (Modern AI Pattern)

Most people protect themselves instead of connecting. This trainer:

1. VULNERABILITY TRACKING
   - Record vulnerability moments and their characteristics
   - Track vulnerability types (emotional, need, fear, failure, longing, apology)
   - Log courage, reception, and connection from vulnerability

2. PATTERN ANALYSIS
   - Identify the user's vulnerability profile (guarded, selective, developing, open)
   - Find vulnerability patterns that create intimacy vs harm
   - Detect chronic protection and its costs

3. VULNERABILITY BUILDING
   - Suggest practices for communicating with increasing vulnerability
   - Provide frameworks for safe vulnerability vs oversharing
   - Recommend practices for receiving vulnerability well

4. COURAGEOUS CONNECTION CULTIVATION
   - Track the correlation between vulnerability and relationship depth
   - Alert when armor is becoming the default
   - Celebrate moments of genuine, brave vulnerability

Architecture:
- record_vulnerability(vulnerability, type, courage, reception, connection): Log vulnerability
- get_vulnerability_stats(): Get vulnerability pattern analysis
- get_vulnerability_suggestion(capacity, context): Get suggestion
- get_vulnerability_score(): Calculate overall vulnerability health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "vulnerable_communication_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VULNERABILITY_LOG = DATA_DIR / "vulnerabilities.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class VulnerabilityEntry:
    """A tracked vulnerability moment."""
    entry_id: str = ""
    vulnerability: str = ""  # what was shared
    vulnerability_type: str = ""  # emotional, need, fear, failure, longing, apology
    courage: float = 0.0  # 0-1
    reception: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    safety: float = 0.0  # 0-1 was it safe?
    reciprocity: float = 0.0  # 0-1 did they share back?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VulnerableCommunicationTrainer:
    """
    Intelligent vulnerable communication trainer with armor detection and courageous connection cultivation.
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
            "avg_courage": 0.0,
            "avg_connection": 0.0,
            "armor_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_vulnerability(self, vulnerability: str = "", vulnerability_type: str = "", courage: float = 0.0, reception: float = 0.0, connection: float = 0.0, safety: float = 0.0, reciprocity: float = 0.0, notes: str = "") -> VulnerabilityEntry:
        """Record a vulnerability moment."""
        entry_id = f"vul_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = VulnerabilityEntry(
            entry_id=entry_id,
            vulnerability=vulnerability or "unspecified",
            vulnerability_type=vulnerability_type or "emotional",
            courage=courage,
            reception=reception,
            connection=connection,
            safety=safety,
            reciprocity=reciprocity,
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

    def get_vulnerability_stats(self) -> Dict[str, Any]:
        """Get vulnerability pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "courage_sum": 0.0, "connection_sum": 0.0, "safety_sum": 0.0})
        for e in self._entries:
            by_type[e.vulnerability_type]["count"] += 1
            by_type[e.vulnerability_type]["courage_sum"] += e.courage
            by_type[e.vulnerability_type]["connection_sum"] += e.connection
            by_type[e.vulnerability_type]["safety_sum"] += e.safety

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_courage": round(data["courage_sum"] / count, 2),
                "avg_connection": round(data["connection_sum"] / count, 2),
                "avg_safety": round(data["safety_sum"] / count, 2),
            }

        # Courage analysis
        high_cour = [e for e in self._entries if e.courage > 0.7]
        low_cour = [e for e in self._entries if e.courage < 0.4]
        if high_cour and low_cour:
            high_cour_conn = sum(e.connection for e in high_cour) / len(high_cour)
            low_cour_conn = sum(e.connection for e in low_cour) / len(low_cour)
            high_cour_rec = sum(e.reception for e in high_cour) / len(high_cour)
            low_cour_rec = sum(e.reception for e in low_cour) / len(low_cour)
        else:
            high_cour_conn = 0
            low_cour_conn = 0
            high_cour_rec = 0
            low_cour_rec = 0

        # Safety analysis
        high_safe = [e for e in self._entries if e.safety > 0.7]
        low_safe = [e for e in self._entries if e.safety < 0.4]
        if high_safe and low_safe:
            high_safe_conn = sum(e.connection for e in high_safe) / len(high_safe)
            low_safe_conn = sum(e.connection for e in low_safe) / len(low_safe)
        else:
            high_safe_conn = 0
            low_safe_conn = 0

        # Armor risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cour = sum(e.courage for e in recent) / len(recent)
            recent_conn = sum(e.connection for e in recent) / len(recent)
            armor_risk = recent_cour < 0.3 and recent_conn < 0.3
        else:
            armor_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "courage_impact": {
                "high_courage_connection": round(high_cour_conn, 2),
                "low_courage_connection": round(low_cour_conn, 2),
                "high_courage_reception": round(high_cour_rec, 2),
                "low_courage_reception": round(low_cour_rec, 2),
            },
            "safety_effect": {
                "high_safety_connection": round(high_safe_conn, 2),
                "low_safety_connection": round(low_safe_conn, 2),
            },
            "armor_risk": armor_risk,
            "avg_courage": round(sum(e.courage for e in self._entries) / len(self._entries), 2),
            "avg_connection": round(sum(e.connection for e in self._entries) / len(self._entries), 2),
        }

    def get_vulnerability_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get vulnerability suggestion."""
        suggestions = [
            "Vulnerability is not weakness. It's courage. The willingness to be seen. To be known. To risk rejection for the chance of connection. That's not weakness. That's the strongest thing a person can do.",
            "Share one level deeper than you usually would. If you usually share facts, share feelings. If you usually share feelings, share fears. If you usually share fears, share failures. Go one level deeper.",
            "Vulnerability requires safety. Don't be vulnerable with people who use your vulnerability against you. Be vulnerable with people who hold it gently. Safety first. Then vulnerability.",
            "The person who never shows vulnerability is not strong. They're afraid. Afraid of being seen. Afraid of being rejected. Afraid of being hurt. And that fear costs them the very thing they want: connection.",
            "Start with 'I feel' not 'You make me feel.' Own your vulnerability. Don't blame it on others. 'I feel anxious' is vulnerable. 'You make me anxious' is an attack. Same feeling. Different delivery. Different result.",
            "Vulnerability is contagious. When you share your truth, others feel permission to share theirs. You create the space. You go first. That's leadership. That's love. That's courage.",
            "Don't overshare. Vulnerability is not dumping. It's not telling everyone everything. It's sharing appropriately with people who have earned your trust. Discernment is part of the practice.",
            "Receiving vulnerability is as important as sharing it. When someone shares their truth, receive it. Don't fix it. Don't minimize it. Just witness it. That's the gift. Being seen is the deepest human need.",
            "Your failures are your credentials. The person who has never failed has never tried. Share your failures. They make you human. They make you relatable. They make you real.",
            "The armor you wear to protect yourself is the same armor that prevents connection. You cannot be protected and connected at the same time. Choose. And choose wisely."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small share. One feeling named. One fear admitted. One step out from behind the armor. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A deeper share with a safe person. A vulnerability practice. A courage exercise. Medium training."
        else:
            capacity_note = "Good capacity. Deep vulnerable communication. A systematic practice of courageous connection. You have the strength to be truly seen."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Vulnerability is the birthplace of connection. And the graveyard of isolation. Most people choose isolation because it feels safer. But safety without connection is just loneliness with better walls. The work of vulnerable communication is about dismantling those walls. About sharing your truth with people who can hold it. About being seen. About being known. And about creating the safety for others to do the same. It's not about oversharing. It's not about being reckless with your heart. It's about being intentional. About choosing who to be vulnerable with. About going one level deeper than you usually do. And about understanding that the person who is never vulnerable is not strong. They're just well-armored. And armor is heavy. And lonely."
        }

    def get_vulnerability_score(self) -> int:
        """Calculate overall vulnerability health (0-100)."""
        if not self._entries:
            return 25

        avg_cour = sum(e.courage for e in self._entries) / len(self._entries)
        avg_conn = sum(e.connection for e in self._entries) / len(self._entries)
        avg_rec = sum(e.reception for e in self._entries) / len(self._entries)
        avg_safe = sum(e.safety for e in self._entries) / len(self._entries)
        avg_recip = sum(e.reciprocity for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cour = sum(e.courage for e in recent) / len(recent)
            recent_conn = sum(e.connection for e in recent) / len(recent)
        else:
            recent_cour = 0
            recent_conn = 0

        # Armor penalty
        armor_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cour_30 = sum(e.courage for e in last_30) / len(last_30)
            recent_conn_30 = sum(e.connection for e in last_30) / len(last_30)
            if recent_cour_30 < 0.3 and recent_conn_30 < 0.3:
                armor_penalty = 15

        # Type variety
        unique_types = len(set(e.vulnerability_type for e in self._entries))

        score = (avg_cour * 25) + (avg_conn * 25) + (avg_rec * 10) + (avg_safe * 10) + (avg_recip * 10) + (recent_cour * 5) + (recent_conn * 5) + (unique_types * 2) - armor_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_courage"] = round(sum(e.courage for e in self._entries) / len(self._entries), 2)
            self._stats["avg_connection"] = round(sum(e.connection for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cour = sum(e.courage for e in recent) / len(recent)
                recent_conn = sum(e.connection for e in recent) / len(recent)
                self._stats["armor_risk"] = recent_cour < 0.3 and recent_conn < 0.3
            else:
                self._stats["armor_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.vulnerable_communication_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.vulnerable_communication_trainer")

    def _log_entry(self, entry: VulnerabilityEntry):
        try:
            with open(VULNERABILITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "vulnerability": entry.vulnerability,
                    "vulnerability_type": entry.vulnerability_type,
                    "courage": entry.courage,
                    "connection": entry.connection,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.vulnerable_communication_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vct_instance: Optional[VulnerableCommunicationTrainer] = None
_vct_lock = threading.Lock()


def get_vulnerable_communication_trainer() -> VulnerableCommunicationTrainer:
    global _vct_instance
    with _vct_lock:
        if _vct_instance is None:
            _vct_instance = VulnerableCommunicationTrainer()
        return _vct_instance
