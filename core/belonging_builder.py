"""
LOVE Belonging Builder — Connection Intelligence (Modern AI Pattern)

Most people feel lonely despite being surrounded by others. This builder:

1. BELONGING TRACKING
   - Record belonging experiences and their characteristics
   - Track belonging types (community, friendship, partnership, family, tribe)
   - Log acceptance, safety, and mattering from belonging

2. PATTERN ANALYSIS
   - Identify the user's belonging profile (connected, isolated, performing, secure)
   - Find belonging patterns that create genuine connection vs loneliness
   - Detect belonging deficits and their sources

3. BELONGING BUILDING
   - Suggest practices for finding and deepening belonging
   - Provide frameworks for vulnerability that creates connection
   - Recommend communities and relationships worth investing in

4. CONNECTION CULTIVATION
   - Track the correlation between belonging and wellbeing
   - Alert when loneliness is becoming normalized
   - Celebrate moments of genuine acceptance and mattering

Architecture:
- record_experience(experience, type, acceptance, safety, mattering): Log experience
- get_belonging_stats(): Get belonging pattern analysis
- get_belonging_suggestion(capacity, context): Get suggestion
- get_belonging_score(): Calculate overall belonging health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "belonging_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BELONGING_LOG = DATA_DIR / "experiences.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BelongingEntry:
    """A tracked belonging experience."""
    entry_id: str = ""
    experience: str = ""  # what happened
    belonging_type: str = ""  # community, friendship, partnership, family, tribe
    acceptance: float = 0.0  # 0-1
    safety: float = 0.0  # 0-1
    mattering: float = 0.0  # 0-1
    vulnerability: float = 0.0  # 0-1
    reciprocity: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BelongingBuilder:
    """
    Intelligent belonging builder with connection detection and acceptance cultivation.
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
            "avg_acceptance": 0.0,
            "avg_mattering": 0.0,
            "isolation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_experience(self, experience: str = "", belonging_type: str = "", acceptance: float = 0.0, safety: float = 0.0, mattering: float = 0.0, vulnerability: float = 0.0, reciprocity: float = 0.0, notes: str = "") -> BelongingEntry:
        """Record a belonging experience."""
        entry_id = f"blg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BelongingEntry(
            entry_id=entry_id,
            experience=experience or "unspecified",
            belonging_type=belonging_type or "community",
            acceptance=acceptance,
            safety=safety,
            mattering=mattering,
            vulnerability=vulnerability,
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

    def get_belonging_stats(self) -> Dict[str, Any]:
        """Get belonging pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "acceptance_sum": 0.0, "safety_sum": 0.0, "mattering_sum": 0.0})
        for e in self._entries:
            by_type[e.belonging_type]["count"] += 1
            by_type[e.belonging_type]["acceptance_sum"] += e.acceptance
            by_type[e.belonging_type]["safety_sum"] += e.safety
            by_type[e.belonging_type]["mattering_sum"] += e.mattering

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_acceptance": round(data["acceptance_sum"] / count, 2),
                "avg_safety": round(data["safety_sum"] / count, 2),
                "avg_mattering": round(data["mattering_sum"] / count, 2),
            }

        # Acceptance analysis
        high_accept = [e for e in self._entries if e.acceptance > 0.7]
        low_accept = [e for e in self._entries if e.acceptance < 0.4]
        if high_accept and low_accept:
            high_acc_safe = sum(e.safety for e in high_accept) / len(high_accept)
            low_acc_safe = sum(e.safety for e in low_accept) / len(low_accept)
            high_acc_mat = sum(e.mattering for e in high_accept) / len(high_accept)
            low_acc_mat = sum(e.mattering for e in low_accept) / len(low_accept)
        else:
            high_acc_safe = 0
            low_acc_safe = 0
            high_acc_mat = 0
            low_acc_mat = 0

        # Vulnerability analysis
        high_vuln = [e for e in self._entries if e.vulnerability > 0.7]
        low_vuln = [e for e in self._entries if e.vulnerability < 0.4]
        if high_vuln and low_vuln:
            high_vuln_acc = sum(e.acceptance for e in high_vuln) / len(high_vuln)
            low_vuln_acc = sum(e.acceptance for e in low_vuln) / len(low_vuln)
        else:
            high_vuln_acc = 0
            low_vuln_acc = 0

        # Isolation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_accept = sum(e.acceptance for e in recent) / len(recent)
            recent_mat = sum(e.mattering for e in recent) / len(recent)
            isolation_risk = recent_accept < 0.3 and recent_mat < 0.3
        else:
            isolation_risk = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "acceptance_impact": {
                "high_acceptance_safety": round(high_acc_safe, 2),
                "low_acceptance_safety": round(low_acc_safe, 2),
                "high_acceptance_mattering": round(high_acc_mat, 2),
                "low_acceptance_mattering": round(low_acc_mat, 2),
            },
            "vulnerability_effect": {
                "high_vulnerability_acceptance": round(high_vuln_acc, 2),
                "low_vulnerability_acceptance": round(low_vuln_acc, 2),
            },
            "isolation_risk": isolation_risk,
            "avg_acceptance": round(sum(e.acceptance for e in self._entries) / len(self._entries), 2),
            "avg_mattering": round(sum(e.mattering for e in self._entries) / len(self._entries), 2),
        }

    def get_belonging_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get belonging suggestion."""
        suggestions = [
            "Show up. Not perfectly. Just present. The person who consistently shows up becomes part of the fabric. Consistency builds belonging.",
            "Share something real. Not your highlight reel. Your struggle. Your doubt. Your weirdness. Vulnerability is the price of admission for real connection.",
            "Join something. A club. A class. A group. A team. Shared purpose creates belonging faster than shared interests.",
            "Be the initiator. Invite someone. Organize something. Create the gathering you want to attend. Don't wait to be included. Include others.",
            "Accept the invitation. Even when you're tired. Even when it's inconvenient. Belonging is built through shared experience, not shared ideas.",
            "Remember names. Remember details. Remember stories. The person who remembers makes others feel like they matter. And mattering is the heart of belonging.",
            "Create rituals with people. Weekly dinner. Monthly hike. Annual trip. Rituals create belonging through repetition. They say: we are a group and this is what we do.",
            "Don't try to belong everywhere. Find your people. The ones who get you. The ones who make you feel like yourself. Quality of belonging beats quantity of contacts.",
            "Belonging starts with self-acceptance. The person who rejects themselves will always feel rejected by others. Accept yourself. Then find your people.",
            "You are not meant to be alone. Humans are tribal animals. Isolation is a warning signal, not a personality trait. Find your tribe. Create your tribe. Belong."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small reach. One text. One moment of presence. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A real conversation. A shared activity. An invitation. Medium connection."
        else:
            capacity_note = "Good capacity. Deep vulnerability. A new community. A significant investment in relationship. You have the energy to build real belonging."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Belonging is not a luxury. It's a biological necessity. The human nervous system is wired for connection. Without it, we wither. Literally. Studies show that social isolation is as dangerous as smoking. As dangerous as obesity. As dangerous as alcoholism. And yet we treat it as a personal failing. It's not. It's a societal failure and a personal emergency. The person who feels they don't belong is not broken. They're human. And the solution is not to become more interesting or more impressive. It's to become more present. More vulnerable. More available. Belonging is not earned. It's built. One interaction at a time. One shared experience at a time. One moment of being seen at a time."
        }

    def get_belonging_score(self) -> int:
        """Calculate overall belonging health (0-100)."""
        if not self._entries:
            return 25

        avg_accept = sum(e.acceptance for e in self._entries) / len(self._entries)
        avg_safe = sum(e.safety for e in self._entries) / len(self._entries)
        avg_mat = sum(e.mattering for e in self._entries) / len(self._entries)
        avg_vuln = sum(e.vulnerability for e in self._entries) / len(self._entries)
        avg_recip = sum(e.reciprocity for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_accept = sum(e.acceptance for e in recent) / len(recent)
            recent_mat = sum(e.mattering for e in recent) / len(recent)
        else:
            recent_accept = 0
            recent_mat = 0

        # Isolation penalty
        iso_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 3:
            iso_penalty = 15

        # Type variety
        unique_types = len(set(e.belonging_type for e in self._entries))

        score = (avg_accept * 25) + (avg_safe * 20) + (avg_mat * 20) + (avg_vuln * 10) + (avg_recip * 10) + (recent_accept * 5) + (recent_mat * 5) + (unique_types * 2) - iso_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_acceptance"] = round(sum(e.acceptance for e in self._entries) / len(self._entries), 2)
            self._stats["avg_mattering"] = round(sum(e.mattering for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_accept = sum(e.acceptance for e in recent) / len(recent)
                recent_mat = sum(e.mattering for e in recent) / len(recent)
                self._stats["isolation_risk"] = recent_accept < 0.3 and recent_mat < 0.3
            else:
                self._stats["isolation_risk"] = True

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

    def _log_entry(self, entry: BelongingEntry):
        try:
            with open(BELONGING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "experience": entry.experience,
                    "belonging_type": entry.belonging_type,
                    "acceptance": entry.acceptance,
                    "mattering": entry.mattering,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_bb_instance: Optional[BelongingBuilder] = None
_bb_lock = threading.Lock()


def get_belonging_builder() -> BelongingBuilder:
    global _bb_instance
    with _bb_lock:
        if _bb_instance is None:
            _bb_instance = BelongingBuilder()
        return _bb_instance
