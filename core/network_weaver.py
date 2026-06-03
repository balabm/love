"""
LOVE Network Weaver — Relationship Ecosystem Intelligence (Modern AI Pattern)

Most people network transactionally. This weaver:

1. NETWORK TRACKING
   - Record network interactions and their quality
   - Track connection types (strong, weak, dormant, potential)
   - Log reciprocity, trust, and value exchange

2. PATTERN ANALYSIS
   - Identify the user's network profile (connector, gatherer, avoider, hoarder)
   - Find network patterns that create opportunities and resilience
   - Detect network decay and its causes

3. NETWORK OPTIMIZATION
   - Suggest connections to strengthen or reactivate
   - Provide frameworks for introductions and bridges
   - Recommend network diversity and its benefits

4. RELATIONSHIP CULTIVATION
   - Track the correlation between network health and opportunities
   - Alert when relationships are becoming purely transactional
   - Celebrate moments of genuine connection and reciprocity

Architecture:
- record_interaction(contact, type, quality, reciprocity, value): Log interaction
- get_network_stats(): Get network pattern analysis
- get_weaving_suggestion(capacity, context): Get suggestion
- get_network_score(): Calculate overall network health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "network_weaver"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NETWORK_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class NetworkEntry:
    """A tracked network interaction."""
    entry_id: str = ""
    contact: str = ""  # who
    interaction_type: str = ""  # strong, weak, dormant_reactivation, new_connection
    quality: float = 0.5  # 0-1 depth of interaction
    reciprocity: float = 0.5  # 0-1 balance of give/take
    value_exchange: float = 0.0  # 0-1 mutual value created
    trust: float = 0.0  # 0-1
    shared_context: str = ""  # work, interest, history, geography
    initiated_by_user: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class NetworkWeaver:
    """
    Intelligent network weaver with relationship detection and ecosystem optimization.
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
            "avg_quality": 0.0,
            "avg_reciprocity": 0.0,
            "transactional_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, contact: str = "", interaction_type: str = "", quality: float = 0.5, reciprocity: float = 0.5, value_exchange: float = 0.0, trust: float = 0.0, shared_context: str = "", initiated_by_user: bool = False, notes: str = "") -> NetworkEntry:
        """Record a network interaction."""
        entry_id = f"net_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = NetworkEntry(
            entry_id=entry_id,
            contact=contact or "unspecified",
            interaction_type=interaction_type or "casual",
            quality=quality,
            reciprocity=reciprocity,
            value_exchange=value_exchange,
            trust=trust,
            shared_context=shared_context or "general",
            initiated_by_user=initiated_by_user,
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

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Contact analysis
        by_contact = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "reciprocity_sum": 0.0, "trust_sum": 0.0, "last_seen": ""})
        for e in self._entries:
            by_contact[e.contact]["count"] += 1
            by_contact[e.contact]["quality_sum"] += e.quality
            by_contact[e.contact]["reciprocity_sum"] += e.reciprocity
            by_contact[e.contact]["trust_sum"] += e.trust
            if e.timestamp > by_contact[e.contact]["last_seen"]:
                by_contact[e.contact]["last_seen"] = e.timestamp

        contact_stats = {}
        for c, data in by_contact.items():
            count = data["count"]
            contact_stats[c] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_reciprocity": round(data["reciprocity_sum"] / count, 2),
                "avg_trust": round(data["trust_sum"] / count, 2),
                "last_seen": data["last_seen"],
            }

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "value_sum": 0.0})
        for e in self._entries:
            by_type[e.interaction_type]["count"] += 1
            by_type[e.interaction_type]["quality_sum"] += e.quality
            by_type[e.interaction_type]["value_sum"] += e.value_exchange

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_value": round(data["value_sum"] / count, 2),
            }

        # Quality vs reciprocity
        high_quality = [e for e in self._entries if e.quality > 0.7]
        low_quality = [e for e in self._entries if e.quality < 0.4]
        if high_quality and low_quality:
            high_qual_recip = sum(e.reciprocity for e in high_quality) / len(high_quality)
            low_qual_recip = sum(e.reciprocity for e in low_quality) / len(low_quality)
            high_qual_value = sum(e.value_exchange for e in high_quality) / len(high_quality)
            low_qual_value = sum(e.value_exchange for e in low_quality) / len(low_quality)
        else:
            high_qual_recip = 0
            low_qual_recip = 0
            high_qual_value = 0
            low_qual_value = 0

        # User initiation analysis
        user_init = [e for e in self._entries if e.initiated_by_user]
        other_init = [e for e in self._entries if not e.initiated_by_user]
        if user_init and other_init:
            user_init_qual = sum(e.quality for e in user_init) / len(user_init)
            other_init_qual = sum(e.quality for e in other_init) / len(other_init)
        else:
            user_init_qual = 0
            other_init_qual = 0

        # Transactional risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_recip = sum(e.reciprocity for e in recent) / len(recent)
            recent_value = sum(e.value_exchange for e in recent) / len(recent)
            transactional_risk = recent_recip < 0.3 and recent_value > 0.7
        else:
            transactional_risk = False

        return {
            "total_entries": len(self._entries),
            "unique_contacts": len(contact_stats),
            "contact_stats": contact_stats,
            "type_stats": type_stats,
            "quality_reciprocity": {
                "high_quality_reciprocity": round(high_qual_recip, 2),
                "low_quality_reciprocity": round(low_qual_recip, 2),
                "high_quality_value": round(high_qual_value, 2),
                "low_quality_value": round(low_qual_value, 2),
            },
            "initiation_effect": {
                "user_initiated_quality": round(user_init_qual, 2),
                "other_initiated_quality": round(other_init_qual, 2),
            },
            "transactional_risk": transactional_risk,
            "avg_quality": round(sum(e.quality for e in self._entries) / len(self._entries), 2),
            "avg_reciprocity": round(sum(e.reciprocity for e in self._entries) / len(self._entries), 2),
        }

    def get_weaving_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get network weaving suggestion."""
        suggestions = [
            "Introduce two people who should know each other. Not for your benefit. For theirs. The best networkers are generous connectors.",
            "Reach out to someone you haven't spoken to in a year. Not because you need something. Just to say you were thinking of them. Reactivation is a gift.",
            "Ask someone for advice. People love to feel useful. And asking creates connection. The person who never asks for help is the person nobody feels close to.",
            "Remember details about people. Their kid's name. Their project. Their struggle. Reference it next time you talk. Being remembered is the greatest compliment.",
            "Show up for people when they don't expect it. The congratulations. The condolence. The encouragement when they're doubting themselves. Unexpected presence is the strongest bond.",
            "Share opportunities without expectation. A job opening. An event. An introduction. Give before you need. The network you build before you need it is the only network that matters.",
            "Be the person who says what everyone is thinking but nobody says. The honest feedback. The naming of the elephant. Trust is built on honesty, not flattery.",
            "Create shared experiences. Not just conversations. Do something together. Walk. Eat. Build. Shared experience is the fastest path to trust.",
            "Follow up after introductions. Did the connection work? Can you help further? The introducer who follows up is rare and valuable.",
            "Your network is not your net worth. It's your net resilience. The people who would help you if everything fell apart. Invest in those relationships when everything is fine.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One message. One check-in. One small gesture. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A call. A coffee. An introduction. Medium weaving."
        else:
            capacity_note = "Good capacity. Host a gathering. Make multiple introductions. Be a hub. You have the social energy to create real network value."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Your network is not a collection of contacts. It's an ecosystem. And like any ecosystem, it needs diversity, reciprocity, and care. Most people network when they need something. That's like only watering plants when they're dying. The best time to build relationships is when you don't need anything. The strongest network is built on generosity, not transaction. Give first. Give often. Give without keeping score. The return comes, but not always from where you gave. That's the beautiful, unpredictable nature of real human connection.",
        }

    def get_network_score(self) -> int:
        """Calculate overall network health (0-100)."""
        if not self._entries:
            return 25

        avg_quality = sum(e.quality for e in self._entries) / len(self._entries)
        avg_reciprocity = sum(e.reciprocity for e in self._entries) / len(self._entries)
        avg_value = sum(e.value_exchange for e in self._entries) / len(self._entries)
        avg_trust = sum(e.trust for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_quality = sum(e.quality for e in recent) / len(recent)
            recent_recip = sum(e.reciprocity for e in recent) / len(recent)
        else:
            recent_quality = 0
            recent_recip = 0

        # Contact variety
        unique_contacts = len(set(e.contact for e in self._entries))

        # Context variety
        unique_contexts = len(set(e.shared_context for e in self._entries))

        # Transactional penalty
        transactional_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if last_90:
            recent_recip_90 = sum(e.reciprocity for e in last_90) / len(last_90)
            recent_value_90 = sum(e.value_exchange for e in last_90) / len(last_90)
            if recent_recip_90 < 0.3 and recent_value_90 > 0.7:
                transactional_penalty = 15

        score = (avg_quality * 25) + (avg_reciprocity * 20) + (avg_value * 10) + (avg_trust * 10) + (recent_quality * 10) + (recent_recip * 10) + (unique_contacts * 2) + (unique_contexts * 2) - transactional_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_quality"] = round(sum(e.quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_reciprocity"] = round(sum(e.reciprocity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_recip = sum(e.reciprocity for e in recent) / len(recent)
                recent_value = sum(e.value_exchange for e in recent) / len(recent)
                self._stats["transactional_risk"] = recent_recip < 0.3 and recent_value > 0.7
            else:
                self._stats["transactional_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.network_weaver")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.network_weaver")

    def _log_entry(self, entry: NetworkEntry):
        try:
            with open(NETWORK_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "contact": entry.contact,
                    "interaction_type": entry.interaction_type,
                    "quality": entry.quality,
                    "reciprocity": entry.reciprocity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.network_weaver")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_nw_instance: Optional[NetworkWeaver] = None
_nw_lock = threading.Lock()


def get_network_weaver() -> NetworkWeaver:
    global _nw_instance
    with _nw_lock:
        if _nw_instance is None:
            _nw_instance = NetworkWeaver()
        return _nw_instance
