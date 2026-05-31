"""
LOVE Accountability Partner — External Support Intelligence (Modern AI Pattern)

Most accountability fails because it's either too harsh or too absent. This partner:

1. ACCOUNTABILITY TRACKING
   - Record commitments shared with others and their outcomes
   - Track check-in frequency, format, and effectiveness
   - Log who provides the most supportive vs effective accountability

2. PATTERN ANALYSIS
   - Identify the user's accountability style (public, private, peer, professional)
   - Find the optimal check-in frequency and format
   - Detect accountability avoidance (hiding from check-ins, sandbagging goals)

3. ACCOUNTABILITY DESIGN
   - Suggest accountability structures for current goals
   - Provide check-in scripts and templates
   - Recommend accountability partner matching

4. SUPPORT OPTIMIZATION
   - Balance challenge and support in accountability
   - Track the emotional tone of accountability interactions
   - Alert when accountability is becoming counterproductive

Architecture:
- record_commitment_shared(commitment, with_whom, check_ins, outcome): Log commitment
- get_accountability_stats(): Get accountability pattern analysis
- get_accountability_design(goal, preference): Get structure
- get_accountability_score(): Calculate overall accountability health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "accountability_partner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACCOUNTABILITY_LOG = DATA_DIR / "accountability.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SharedCommitment:
    """A tracked shared commitment."""
    commitment_id: str = ""
    commitment: str = ""
    shared_with: str = ""
    relationship: str = ""  # friend, partner, colleague, mentor, coach, group, public
    check_in_frequency: str = ""  # daily, weekly, monthly, ad_hoc
    check_in_count: int = 0
    completed: bool = False
    tone: str = ""  # supportive, challenging, neutral, harsh, absent
    helpfulness: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AccountabilityPartner:
    """
    Intelligent accountability partner with structure design and support optimization.
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
        self._commitments: deque = deque(maxlen=200)
        self._stats = {
            "total_commitments": 0,
            "completion_rate": 0.0,
            "avg_helpfulness": 0.0,
            "best_partner": "",
            "optimal_frequency": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_commitment_shared(self, commitment: str = "", shared_with: str = "", relationship: str = "", frequency: str = "", check_ins: int = 0, completed: bool = False, tone: str = "", helpfulness: float = 0.5, notes: str = "") -> SharedCommitment:
        """Record a shared commitment."""
        commitment_id = f"acct_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._commitments)}"
        sc = SharedCommitment(
            commitment_id=commitment_id,
            commitment=commitment or "unspecified",
            shared_with=shared_with or "unspecified",
            relationship=relationship or "friend",
            check_in_frequency=frequency or "weekly",
            check_in_count=check_ins,
            completed=completed,
            tone=tone or "supportive",
            helpfulness=helpfulness,
            notes=notes,
        )

        with self._lock:
            self._commitments.append(sc)
            self._stats["total_commitments"] += 1
            self._update_stats()

        self._save_stats()
        self._log_commitment(sc)

        return sc

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_accountability_stats(self) -> Dict[str, Any]:
        """Get accountability pattern analysis."""
        if not self._commitments:
            return {"status": "insufficient_data"}

        # Partner analysis
        by_partner = defaultdict(lambda: {"count": 0, "completed": 0, "helpfulness_sum": 0.0, "check_ins": 0})
        for c in self._commitments:
            by_partner[c.shared_with]["count"] += 1
            if c.completed:
                by_partner[c.shared_with]["completed"] += 1
            by_partner[c.shared_with]["helpfulness_sum"] += c.helpfulness
            by_partner[c.shared_with]["check_ins"] += c.check_in_count

        partner_stats = {}
        for p, data in by_partner.items():
            count = data["count"]
            partner_stats[p] = {
                "count": count,
                "completion_rate": round(data["completed"] / count, 2),
                "avg_helpfulness": round(data["helpfulness_sum"] / count, 2),
                "total_check_ins": data["check_ins"],
            }

        best = max(partner_stats.items(), key=lambda x: x[1]["completion_rate"] * x[1]["avg_helpfulness"]) if partner_stats else ("", {})

        # Frequency analysis
        by_freq = defaultdict(lambda: {"count": 0, "completed": 0, "helpfulness_sum": 0.0})
        for c in self._commitments:
            by_freq[c.check_in_frequency]["count"] += 1
            if c.completed:
                by_freq[c.check_in_frequency]["completed"] += 1
            by_freq[c.check_in_frequency]["helpfulness_sum"] += c.helpfulness

        freq_stats = {}
        for f, data in by_freq.items():
            count = data["count"]
            freq_stats[f] = {
                "count": count,
                "completion_rate": round(data["completed"] / count, 2),
                "avg_helpfulness": round(data["helpfulness_sum"] / count, 2),
            }

        optimal = max(freq_stats.items(), key=lambda x: x[1]["completion_rate"] * x[1]["avg_helpfulness"]) if freq_stats else ("", {})

        # Tone analysis
        by_tone = defaultdict(lambda: {"count": 0, "completed": 0, "helpfulness_sum": 0.0})
        for c in self._commitments:
            by_tone[c.tone]["count"] += 1
            if c.completed:
                by_tone[c.tone]["completed"] += 1
            by_tone[c.tone]["helpfulness_sum"] += c.helpfulness

        tone_stats = {}
        for t, data in by_tone.items():
            count = data["count"]
            tone_stats[t] = {
                "count": count,
                "completion_rate": round(data["completed"] / count, 2),
                "avg_helpfulness": round(data["helpfulness_sum"] / count, 2),
            }

        # Relationship type analysis
        by_rel = defaultdict(lambda: {"count": 0, "completed": 0})
        for c in self._commitments:
            by_rel[c.relationship]["count"] += 1
            if c.completed:
                by_rel[c.relationship]["completed"] += 1

        rel_stats = {}
        for r, data in by_rel.items():
            count = data["count"]
            rel_stats[r] = {
                "count": count,
                "completion_rate": round(data["completed"] / count, 2),
            }

        return {
            "total_commitments": len(self._commitments),
            "partner_stats": partner_stats,
            "best_partner": best[0],
            "frequency_stats": freq_stats,
            "optimal_frequency": optimal[0],
            "tone_stats": tone_stats,
            "relationship_stats": rel_stats,
            "completion_rate": round(sum(1 for c in self._commitments if c.completed) / len(self._commitments), 2),
            "avg_helpfulness": round(sum(c.helpfulness for c in self._commitments) / len(self._commitments), 2),
        }

    def get_accountability_design(self, goal: str = "", preference: str = "private", risk_level: str = "low") -> Dict[str, Any]:
        """Get accountability structure."""
        structures = {
            "private": {
                "description": "One trusted person who checks in regularly",
                "check_in": "Weekly text or call",
                "setup": "Ask: 'Can I tell you my goal and check in with you weekly? I just need you to ask how it's going.'",
            },
            "public": {
                "description": "Announce goal publicly with regular updates",
                "check_in": "Social media or group post every 2 weeks",
                "setup": "Post your goal and deadline. Update on progress. Let social pressure work for you.",
            },
            "peer": {
                "description": "Mutual accountability with someone pursuing a similar goal",
                "check_in": "Weekly co-working or progress share",
                "setup": "Find someone with a similar goal. Share weekly wins and blocks. Celebrate each other.",
            },
            "professional": {
                "description": "Paid accountability (coach, trainer, therapist)",
                "check_in": "Scheduled sessions with homework review",
                "setup": "Hire someone whose job is to hold you accountable. The investment increases commitment.",
            },
            "self": {
                "description": "Structured self-accountability with systems",
                "check_in": "Daily journaling or habit tracker review",
                "setup": "Use a habit tracker, calendar reminders, or a commitment device. Be your own best accountability partner.",
            },
        }

        base = structures.get(preference, structures["private"])

        if risk_level == "high":
            escalation = "Consider combining two structures. Public + peer, or private + professional. High-stakes goals need multiple supports."
        elif risk_level == "medium":
            escalation = "One strong structure is enough. Make sure check-ins are weekly at minimum."
        else:
            escalation = "Start simple. You can always add more accountability later."

        check_in_scripts = [
            "This week I committed to [goal]. Here's what happened...",
            "I said I'd do [goal]. I did / didn't because...",
            "My win this week was... My challenge was...",
        ]

        return {
            "goal": goal or "unspecified",
            "preference": preference,
            "risk_level": risk_level,
            **base,
            "escalation": escalation,
            "check_in_script": random.choice(check_in_scripts),
            "reminder": "Accountability isn't about shame. It's about creating a structure that makes success easier than failure.",
        }

    def get_accountability_score(self) -> int:
        """Calculate overall accountability health (0-100)."""
        if not self._commitments:
            return 35

        # Completion rate
        completion = sum(1 for c in self._commitments if c.completed) / len(self._commitments)

        # Helpfulness
        avg_helpfulness = sum(c.helpfulness for c in self._commitments) / len(self._commitments)

        # Check-in frequency (more is generally better, up to a point)
        avg_check_ins = sum(c.check_in_count for c in self._commitments) / len(self._commitments)

        # Variety (different partners/approaches)
        unique_partners = len(set(c.shared_with for c in self._commitments))
        unique_frequencies = len(set(c.check_in_frequency for c in self._commitments))

        # Recent activity
        recent = [c for c in self._commitments if c.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        recent_completion = sum(1 for c in recent if c.completed) / max(1, len(recent))

        # Tone balance (supportive tones tend to work better)
        supportive = sum(1 for c in self._commitments if c.tone in ["supportive", "challenging"])
        tone_rate = supportive / len(self._commitments)

        score = (completion * 30) + (avg_helpfulness * 20) + (min(avg_check_ins, 5) * 3) + (unique_partners * 2) + (unique_frequencies * 2) + (recent_completion * 10) + (tone_rate * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._commitments:
            completed = sum(1 for c in self._commitments if c.completed)
            self._stats["completion_rate"] = round(completed / len(self._commitments), 2)
            self._stats["avg_helpfulness"] = round(sum(c.helpfulness for c in self._commitments) / len(self._commitments), 2)

            by_partner = defaultdict(lambda: {"completed": 0, "helpfulness": 0.0, "count": 0})
            for c in self._commitments:
                by_partner[c.shared_with]["count"] += 1
                if c.completed:
                    by_partner[c.shared_with]["completed"] += 1
                by_partner[c.shared_with]["helpfulness"] += c.helpfulness
            
            if by_partner:
                best = max(by_partner.items(), key=lambda x: (x[1]["completed"] / max(1, x[1]["count"])) * (x[1]["helpfulness"] / max(1, x[1]["count"])))
                self._stats["best_partner"] = best[0]

            by_freq = defaultdict(lambda: {"completed": 0, "helpfulness": 0.0, "count": 0})
            for c in self._commitments:
                by_freq[c.check_in_frequency]["count"] += 1
                if c.completed:
                    by_freq[c.check_in_frequency]["completed"] += 1
                by_freq[c.check_in_frequency]["helpfulness"] += c.helpfulness
            
            if by_freq:
                optimal = max(by_freq.items(), key=lambda x: (x[1]["completed"] / max(1, x[1]["count"])) * (x[1]["helpfulness"] / max(1, x[1]["count"])))
                self._stats["optimal_frequency"] = optimal[0]

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

    def _log_commitment(self, commitment: SharedCommitment):
        try:
            with open(ACCOUNTABILITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": commitment.timestamp,
                    "commitment": commitment.commitment,
                    "shared_with": commitment.shared_with,
                    "relationship": commitment.relationship,
                    "frequency": commitment.check_in_frequency,
                    "completed": commitment.completed,
                    "helpfulness": commitment.helpfulness,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ap_instance: Optional[AccountabilityPartner] = None
_ap_lock = threading.Lock()


def get_accountability_partner() -> AccountabilityPartner:
    global _ap_instance
    with _ap_lock:
        if _ap_instance is None:
            _ap_instance = AccountabilityPartner()
        return _ap_instance
