"""
LOVE Mentorship Weaver — Transmission Intelligence (Modern AI Pattern)

Most people have wisdom to share but no system for sharing it. This weaver:

1. MENTORSHIP TRACKING
   - Record mentorship interactions and their quality
   - Track mentorship types (formal, informal, peer, reverse, sponsorship)
   - Log growth, impact, and satisfaction for both mentor and mentee

2. PATTERN ANALYSIS
   - Identify the user's mentorship profile (generous, withholding, growing, seeking)
   - Find mentorship patterns that create lasting transformation
   - Detect mentorship burnout and capacity limits

3. MENTORSHIP OPTIMIZATION
   - Suggest mentorship opportunities matched to current wisdom and capacity
   - Provide frameworks for effective guidance
   - Recommend both giving and receiving mentorship

4. TRANSMISSION CULTIVATION
   - Track the correlation between mentorship and life meaning
   - Alert when wisdom is being hoarded instead of shared
   - Celebrate moments of genuine transformation through mentorship

Architecture:
- record_interaction(role, type, growth, impact, satisfaction): Log interaction
- get_mentorship_stats(): Get mentorship pattern analysis
- get_mentorship_suggestion(capacity, context): Get suggestion
- get_mentorship_score(): Calculate overall mentorship health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "mentorship_weaver"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MENTORSHIP_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MentorshipEntry:
    """A tracked mentorship interaction."""
    entry_id: str = ""
    role: str = ""  # mentor, mentee, peer
    person: str = ""  # who
    interaction_type: str = ""  # formal, informal, peer, reverse, sponsorship
    growth: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    satisfaction: float = 0.5  # 0-1
    reciprocity: float = 0.0  # 0-1
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MentorshipWeaver:
    """
    Intelligent mentorship weaver with transmission detection and wisdom cultivation.
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
            "avg_growth": 0.0,
            "avg_satisfaction": 0.0,
            "hoarding_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, role: str = "", person: str = "", interaction_type: str = "", growth: float = 0.0, impact: float = 0.0, satisfaction: float = 0.5, reciprocity: float = 0.0, duration_minutes: float = 0.0, notes: str = "") -> MentorshipEntry:
        """Record a mentorship interaction."""
        entry_id = f"men_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = MentorshipEntry(
            entry_id=entry_id,
            role=role or "mentee",
            person=person or "unspecified",
            interaction_type=interaction_type or "informal",
            growth=growth,
            impact=impact,
            satisfaction=satisfaction,
            reciprocity=reciprocity,
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

    def get_mentorship_stats(self) -> Dict[str, Any]:
        """Get mentorship pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Role analysis
        by_role = defaultdict(lambda: {"count": 0, "growth_sum": 0.0, "impact_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_role[e.role]["count"] += 1
            by_role[e.role]["growth_sum"] += e.growth
            by_role[e.role]["impact_sum"] += e.impact
            by_role[e.role]["satisfaction_sum"] += e.satisfaction

        role_stats = {}
        for r, data in by_role.items():
            count = data["count"]
            role_stats[r] = {
                "count": count,
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "growth_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.interaction_type]["count"] += 1
            by_type[e.interaction_type]["growth_sum"] += e.growth
            by_type[e.interaction_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Growth analysis
        high_growth = [e for e in self._entries if e.growth > 0.7]
        low_growth = [e for e in self._entries if e.growth < 0.4]
        if high_growth and low_growth:
            high_growth_sat = sum(e.satisfaction for e in high_growth) / len(high_growth)
            low_growth_sat = sum(e.satisfaction for e in low_growth) / len(low_growth)
        else:
            high_growth_sat = 0
            low_growth_sat = 0

        # Reciprocity analysis
        high_recip = [e for e in self._entries if e.reciprocity > 0.7]
        low_recip = [e for e in self._entries if e.reciprocity < 0.4]
        if high_recip and low_recip:
            high_recip_sat = sum(e.satisfaction for e in high_recip) / len(high_recip)
            low_recip_sat = sum(e.satisfaction for e in low_recip) / len(low_recip)
        else:
            high_recip_sat = 0
            low_recip_sat = 0

        # Hoarding risk detection
        mentor_entries = [e for e in self._entries if e.role == "mentor"]
        recent_mentor = [e for e in mentor_entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
        if self._entries and len(recent_mentor) < 2:
            hoarding_risk = True
        else:
            hoarding_risk = False

        return {
            "total_entries": len(self._entries),
            "role_stats": role_stats,
            "type_stats": type_stats,
            "growth_impact": {
                "high_growth_satisfaction": round(high_growth_sat, 2),
                "low_growth_satisfaction": round(low_growth_sat, 2),
            },
            "reciprocity_effect": {
                "high_reciprocity_satisfaction": round(high_recip_sat, 2),
                "low_reciprocity_satisfaction": round(low_recip_sat, 2),
            },
            "hoarding_risk": hoarding_risk,
            "avg_growth": round(sum(e.growth for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
        }

    def get_mentorship_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get mentorship suggestion."""
        suggestions = [
            "Everyone has something to teach. Not because you're an expert. Because you've lived. Your failures. Your recoveries. Your particular way through difficulty. Share them.",
            "Mentorship is not about being wise. It's about being present. The mentor who listens is worth more than the mentor who lectures. Presence is the greatest gift.",
            "Ask someone to mentor you. Not formally. Just ask for advice. People love to be asked. And you'll learn more in one conversation than in ten books.",
            "Reverse mentorship is real. Learn from people younger than you. Different from you. The person who thinks they have nothing to learn from the next generation is already obsolete.",
            "Sponsor, don't just mentor. Mentorship is advice. Sponsorship is using your power to create opportunities for someone else. That's where real transformation happens.",
            "Be specific in your mentorship. Not 'you're great.' But 'when you handled that difficult conversation, you showed real skill.' Specificity creates learning.",
            "Mentorship is a relationship, not a transaction. It takes time. Trust. Consistency. The best mentorship relationships last years. Invest in the long term.",
            "You don't need to have all the answers. The best mentors say 'I don't know' often. They model curiosity. They model learning. They model humility.",
            "Peer mentorship is underrated. Someone at your level. Facing similar challenges. Walking beside you. The shared struggle is its own wisdom.",
            "Wisdom unused is wisdom wasted. If you have learned something hard, someone else is about to learn it. Help them. The transmission of wisdom is how civilization survives.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One question. One answer. One moment of guidance. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Regular conversations. A mentee. A mentor. Medium investment in transmission."
        else:
            capacity_note = "Good capacity. Formal mentorship. Multiple relationships. You have the energy to be a real force in others' development."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Wisdom is not a possession. It's a responsibility. The things you've learned. The mistakes you've made. The insights you've gained. They don't belong to you alone. They belong to everyone who comes after you. Mentorship is how we transmit what matters across generations. It's how we prevent every person from having to relearn everything the hard way. The mentor who hoards their wisdom is not wise. They're selfish. Share what you know. Learn what you don't. Be part of the chain of human knowledge. That's the real legacy.",
        }

    def get_mentorship_score(self) -> int:
        """Calculate overall mentorship health (0-100)."""
        if not self._entries:
            return 25

        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)
        avg_impact = sum(e.impact for e in self._entries) / len(self._entries)
        avg_satisfaction = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_reciprocity = sum(e.reciprocity for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_growth = sum(e.growth for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_growth = 0
            recent_satisfaction = 0

        # Hoarding penalty
        hoarding_penalty = 0
        mentor_entries = [e for e in self._entries if e.role == "mentor"]
        recent_mentor = [e for e in mentor_entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
        if len(recent_mentor) < 2:
            hoarding_penalty = 10

        # Role balance
        roles = defaultdict(int)
        for e in self._entries:
            roles[e.role] += 1
        role_balance = len(roles)

        score = (avg_growth * 20) + (avg_impact * 20) + (avg_satisfaction * 20) + (avg_reciprocity * 15) + (recent_growth * 10) + (recent_satisfaction * 10) + (role_balance * 3) - hoarding_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_growth"] = round(sum(e.growth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            mentor_entries = [e for e in self._entries if e.role == "mentor"]
            recent_mentor = [e for e in mentor_entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
            self._stats["hoarding_risk"] = len(recent_mentor) < 2

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mentorship_weaver")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mentorship_weaver")

    def _log_entry(self, entry: MentorshipEntry):
        try:
            with open(MENTORSHIP_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "role": entry.role,
                    "person": entry.person,
                    "interaction_type": entry.interaction_type,
                    "growth": entry.growth,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mentorship_weaver")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mw_instance: Optional[MentorshipWeaver] = None
_mw_lock = threading.Lock()


def get_mentorship_weaver() -> MentorshipWeaver:
    global _mw_instance
    with _mw_lock:
        if _mw_instance is None:
            _mw_instance = MentorshipWeaver()
        return _mw_instance
