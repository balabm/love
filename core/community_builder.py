"""
LOVE Community Builder — Social Ecosystem Intelligence (Modern AI Pattern)

Most people think community is about finding your people. It's actually about
becoming someone worth finding. This builder:

1. COMMUNITY TRACKING
   - Record community interactions and their quality
   - Track community types (local, interest, work, spiritual, online)
   - Log belonging, contribution, and support received

2. PATTERN ANALYSIS
   - Identify the user's community profile (isolated, consumer, contributor, builder)
   - Find community patterns that create lasting belonging
   - Detect community decay and its causes

3. COMMUNITY BUILDING
   - Suggest ways to deepen existing community ties
   - Provide frameworks for starting new community containers
   - Recommend contribution styles matched to current capacity

4. BELONGING CULTIVATION
   - Track the correlation between community and wellbeing
   - Alert when isolation risk is rising
   - Celebrate moments of genuine connection and contribution

Architecture:
- record_interaction(community, type, belonging, contribution, support): Log interaction
- get_community_stats(): Get community pattern analysis
- get_building_suggestion(capacity, context): Get suggestion
- get_community_score(): Calculate overall community health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "community_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMMUNITY_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CommunityEntry:
    """A tracked community interaction."""
    entry_id: str = ""
    community: str = ""  # which community
    interaction_type: str = ""  # gathering, contribution, support, casual, deep
    belonging: float = 0.5  # 0-1
    contribution: float = 0.0  # 0-1
    support_received: float = 0.0  # 0-1
    support_given: float = 0.0  # 0-1
    new_connection: bool = False
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CommunityBuilder:
    """
    Intelligent community builder with belonging detection and contribution optimization.
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
            "avg_belonging": 0.0,
            "avg_contribution": 0.0,
            "isolation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, community: str = "", interaction_type: str = "", belonging: float = 0.5, contribution: float = 0.0, support_received: float = 0.0, support_given: float = 0.0, new_connection: bool = False, duration_minutes: float = 0.0, notes: str = "") -> CommunityEntry:
        """Record a community interaction."""
        entry_id = f"com_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CommunityEntry(
            entry_id=entry_id,
            community=community or "unspecified",
            interaction_type=interaction_type or "casual",
            belonging=belonging,
            contribution=contribution,
            support_received=support_received,
            support_given=support_given,
            new_connection=new_connection,
            duration_minutes=duration_minutes,
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

    def get_community_stats(self) -> Dict[str, Any]:
        """Get community pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Community analysis
        by_community = defaultdict(lambda: {"count": 0, "belonging_sum": 0.0, "contribution_sum": 0.0, "support_sum": 0.0})
        for e in self._entries:
            by_community[e.community]["count"] += 1
            by_community[e.community]["belonging_sum"] += e.belonging
            by_community[e.community]["contribution_sum"] += e.contribution
            by_community[e.community]["support_sum"] += e.support_received + e.support_given

        community_stats = {}
        for c, data in by_community.items():
            count = data["count"]
            community_stats[c] = {
                "count": count,
                "avg_belonging": round(data["belonging_sum"] / count, 2),
                "avg_contribution": round(data["contribution_sum"] / count, 2),
                "avg_support": round(data["support_sum"] / count, 2),
            }

        best_community = max(community_stats.items(), key=lambda x: x[1]["avg_belonging"]) if community_stats else ("", {})

        # Contribution analysis
        high_contribution = [e for e in self._entries if e.contribution > 0.7]
        low_contribution = [e for e in self._entries if e.contribution < 0.3]
        if high_contribution and low_contribution:
            high_cont_belonging = sum(e.belonging for e in high_contribution) / len(high_contribution)
            low_cont_belonging = sum(e.belonging for e in low_contribution) / len(low_contribution)
        else:
            high_cont_belonging = 0
            low_cont_belonging = 0

        # Support analysis
        high_support = [e for e in self._entries if e.support_received + e.support_given > 1.0]
        low_support = [e for e in self._entries if e.support_received + e.support_given < 0.5]
        if high_support and low_support:
            high_sup_belonging = sum(e.belonging for e in high_support) / len(high_support)
            low_sup_belonging = sum(e.belonging for e in low_support) / len(low_support)
        else:
            high_sup_belonging = 0
            low_sup_belonging = 0

        # New connections
        with_new = [e for e in self._entries if e.new_connection]
        without_new = [e for e in self._entries if not e.new_connection]
        if with_new and without_new:
            new_belonging = sum(e.belonging for e in with_new) / len(with_new)
            old_belonging = sum(e.belonging for e in without_new) / len(without_new)
        else:
            new_belonging = 0
            old_belonging = 0

        # Isolation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_belonging = sum(e.belonging for e in recent) / len(recent)
            recent_interactions = len(recent)
            isolation_risk = recent_belonging < 0.4 and recent_interactions < 3
        else:
            isolation_risk = True

        return {
            "total_entries": len(self._entries),
            "community_stats": community_stats,
            "best_community": best_community[0],
            "contribution_impact": {
                "high_contribution_belonging": round(high_cont_belonging, 2),
                "low_contribution_belonging": round(low_cont_belonging, 2),
            },
            "support_impact": {
                "high_support_belonging": round(high_sup_belonging, 2),
                "low_support_belonging": round(low_sup_belonging, 2),
            },
            "new_connection_effect": {
                "with_new_belonging": round(new_belonging, 2),
                "without_new_belonging": round(old_belonging, 2),
            },
            "isolation_risk": isolation_risk,
            "avg_belonging": round(sum(e.belonging for e in self._entries) / len(self._entries), 2),
            "avg_contribution": round(sum(e.contribution for e in self._entries) / len(self._entries), 2),
        }

    def get_building_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get community building suggestion."""
        suggestions = [
            "Community is not something you find. It's something you build. One conversation at a time. One vulnerability at a time. One kept promise at a time.",
            "Host something. Anything. A dinner. A walk. A book discussion. The person who creates the container is the person who creates the community.",
            "Remember someone's name. Remember their story. Remember what they care about. Attention is the currency of belonging.",
            "Show up when you don't need anything. That's when trust is built. The best community members are the ones who are present during ordinary times.",
            "Introduce two people who should know each other. Be a connector. The strength of your network is measured by how many useful connections you create for others.",
            "Ask for help. Vulnerability invites intimacy. The person who never needs anything is the person nobody feels close to.",
            "Celebrate other people's wins publicly. Grieve their losses privately. Community is built on shared emotion.",
            "Be consistent. Show up again and again. Reliability is the foundation of trust. The person who is always there becomes indispensable.",
            "Create rituals. Weekly calls. Monthly dinners. Annual trips. Rituals turn groups into communities and communities into families.",
            "The quality of your community is the quality of your life. Invest accordingly. Time in community is never wasted. It's multiplied.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small interaction. A text. A call. A comment. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Attend something. A gathering. A meeting. Be present."
        else:
            capacity_note = "Good capacity. Host something. Invite people. Create the container. You have the energy to give."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Humans are tribal animals. We need belonging the way we need food and water. Modern life isolates us by design. The default setting of society is isolation. Community requires intention. It requires showing up. It requires vulnerability. It requires consistency. The person who has strong community is not luckier than everyone else. They're more intentional. They invest time before they need help. They create belonging for others before they demand it for themselves. Community is a verb, not a noun.",
        }

    def get_community_score(self) -> int:
        """Calculate overall community health (0-100)."""
        if not self._entries:
            return 25

        avg_belonging = sum(e.belonging for e in self._entries) / len(self._entries)
        avg_contribution = sum(e.contribution for e in self._entries) / len(self._entries)
        avg_support_rx = sum(e.support_received for e in self._entries) / len(self._entries)
        avg_support_gv = sum(e.support_given for e in self._entries) / len(self._entries)
        new_conn_ratio = sum(1 for e in self._entries if e.new_connection) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_belonging = sum(e.belonging for e in recent) / len(recent)
            recent_contribution = sum(e.contribution for e in recent) / len(recent)
        else:
            recent_belonging = 0
            recent_contribution = 0

        # Isolation penalty
        isolation_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 3:
            isolation_penalty = 15

        # Community variety
        unique_communities = len(set(e.community for e in self._entries))

        score = (avg_belonging * 30) + (avg_contribution * 20) + (avg_support_rx * 15) + (avg_support_gv * 15) + (new_conn_ratio * 10) + (recent_belonging * 5) + (recent_contribution * 5) + (unique_communities * 2) - isolation_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_belonging"] = round(sum(e.belonging for e in self._entries) / len(self._entries), 2)
            self._stats["avg_contribution"] = round(sum(e.contribution for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_belonging = sum(e.belonging for e in recent) / len(recent)
                recent_interactions = len(recent)
                self._stats["isolation_risk"] = recent_belonging < 0.4 and recent_interactions < 3
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

    def _log_entry(self, entry: CommunityEntry):
        try:
            with open(COMMUNITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "community": entry.community,
                    "interaction_type": entry.interaction_type,
                    "belonging": entry.belonging,
                    "contribution": entry.contribution,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cb_instance: Optional[CommunityBuilder] = None
_cb_lock = threading.Lock()


def get_community_builder() -> CommunityBuilder:
    global _cb_instance
    with _cb_lock:
        if _cb_instance is None:
            _cb_instance = CommunityBuilder()
        return _cb_instance
