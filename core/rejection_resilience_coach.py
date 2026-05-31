"""
LOVE Rejection Resilience Coach — Rejection Intelligence (Modern AI Pattern)

Most people fear rejection more than anything. This coach:

1. REJECTION TRACKING
   - Record rejection experiences and their characteristics
   - Track rejection types (social, professional, romantic, creative, personal)
   - Log impact, learning, and recovery from rejections

2. PATTERN ANALYSIS
   - Identify the user's rejection profile (resilient, devastated, avoidant, growing)
   - Find rejection patterns that lead to growth vs paralysis
   - Detect rejection avoidance and its costs

3. RESILIENCE BUILDING
   - Suggest practices for processing rejection constructively
   - Provide frameworks for separating self-worth from outcomes
   - Recommend risk-taking despite fear of rejection

4. CONFIDENCE CULTIVATION
   - Track the correlation between rejection recovery and confidence
   - Alert when rejection sensitivity is limiting life
   - Celebrate moments of courageous vulnerability

Architecture:
- record_rejection(rejection, type, impact, learning, recovery): Log rejection
- get_rejection_stats(): Get rejection pattern analysis
- get_rejection_suggestion(capacity, context): Get suggestion
- get_rejection_score(): Calculate overall rejection resilience
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

DATA_DIR = Path(__file__).parent.parent / "data" / "rejection_resilience_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REJECTION_LOG = DATA_DIR / "rejections.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RejectionEntry:
    """A tracked rejection experience."""
    entry_id: str = ""
    rejection: str = ""  # what happened
    rejection_type: str = ""  # social, professional, romantic, creative, personal
    impact: float = 0.5  # 0-1
    learning: float = 0.0  # 0-1
    recovery: float = 0.0  # 0-1
    self_worth: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RejectionResilienceCoach:
    """
    Intelligent rejection resilience coach with recovery detection and confidence cultivation.
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
            "avg_recovery": 0.0,
            "avg_self_worth": 0.0,
            "avoidance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_rejection(self, rejection: str = "", rejection_type: str = "", impact: float = 0.5, learning: float = 0.0, recovery: float = 0.0, self_worth: float = 0.0, courage: float = 0.0, notes: str = "") -> RejectionEntry:
        """Record a rejection experience."""
        entry_id = f"rej_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RejectionEntry(
            entry_id=entry_id,
            rejection=rejection or "unspecified",
            rejection_type=rejection_type or "general",
            impact=impact,
            learning=learning,
            recovery=recovery,
            self_worth=self_worth,
            courage=courage,
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

    def get_rejection_stats(self) -> Dict[str, Any]:
        """Get rejection pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "impact_sum": 0.0, "recovery_sum": 0.0, "learning_sum": 0.0})
        for e in self._entries:
            by_type[e.rejection_type]["count"] += 1
            by_type[e.rejection_type]["impact_sum"] += e.impact
            by_type[e.rejection_type]["recovery_sum"] += e.recovery
            by_type[e.rejection_type]["learning_sum"] += e.learning

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_recovery": round(data["recovery_sum"] / count, 2),
                "avg_learning": round(data["learning_sum"] / count, 2),
            }

        # Recovery analysis
        high_rec = [e for e in self._entries if e.recovery > 0.7]
        low_rec = [e for e in self._entries if e.recovery < 0.4]
        if high_rec and low_rec:
            high_rec_worth = sum(e.self_worth for e in high_rec) / len(high_rec)
            low_rec_worth = sum(e.self_worth for e in low_rec) / len(low_rec)
            high_rec_learn = sum(e.learning for e in high_rec) / len(high_rec)
            low_rec_learn = sum(e.learning for e in low_rec) / len(low_rec)
        else:
            high_rec_worth = 0
            low_rec_worth = 0
            high_rec_learn = 0
            low_rec_learn = 0

        # Learning analysis
        high_learn = [e for e in self._entries if e.learning > 0.7]
        low_learn = [e for e in self._entries if e.learning < 0.4]
        if high_learn and low_learn:
            high_learn_cour = sum(e.courage for e in high_learn) / len(high_learn)
            low_learn_cour = sum(e.courage for e in low_learn) / len(low_learn)
        else:
            high_learn_cour = 0
            low_learn_cour = 0

        # Avoidance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_recovery = sum(e.recovery for e in recent) / len(recent)
            recent_courage = sum(e.courage for e in recent) / len(recent)
            avoidance_risk = recent_recovery < 0.3 and recent_courage < 0.3
        else:
            avoidance_risk = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "recovery_impact": {
                "high_recovery_self_worth": round(high_rec_worth, 2),
                "low_recovery_self_worth": round(low_rec_worth, 2),
                "high_recovery_learning": round(high_rec_learn, 2),
                "low_recovery_learning": round(low_rec_learn, 2),
            },
            "learning_effect": {
                "high_learning_courage": round(high_learn_cour, 2),
                "low_learning_courage": round(low_learn_cour, 2),
            },
            "avoidance_risk": avoidance_risk,
            "avg_recovery": round(sum(e.recovery for e in self._entries) / len(self._entries), 2),
            "avg_self_worth": round(sum(e.self_worth for e in self._entries) / len(self._entries), 2),
        }

    def get_rejection_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get rejection suggestion."""
        suggestions = [
            "Rejection is not a verdict on your worth. It's a mismatch. A timing issue. A preference. Not everyone will want you. Not everyone should. That's not a flaw. That's reality.",
            "Feel the sting. Then move on. Rejection hurts. Denying that it hurts doesn't help. Feel it. Name it. Then keep going. The people who succeed are not those who never feel rejection. They're those who don't let it stop them.",
            "Separate the event from your identity. 'They rejected my proposal' not 'They rejected me.' 'This didn't work out' not 'I am a failure.' Language matters.",
            "Ask for feedback. Not to argue. To learn. 'What could I have done better?' Some rejections come with lessons. Be humble enough to receive them.",
            "Reframe rejection as redirection. This door closed. Maybe a better door opens. Maybe this wasn't right for you either. Trust the redirect.",
            "Take another risk. The best cure for rejection is action. Another application. Another conversation. Another attempt. Momentum beats rumination.",
            "You are not the sum of your rejections. You are the sum of your courage. The person who tries and fails is infinitely more admirable than the person who never tries.",
            "Rejection is data. It tells you about fit. About timing. About presentation. It doesn't tell you about your value as a human being. Collect the data. Ignore the verdict.",
            "The people you admire have been rejected more than you know. Every successful person has a hidden history of no's. The difference is they kept going after the no's.",
            "Fear of rejection is fear of living. The person who avoids rejection avoids life. Love. Opportunity. Growth. They all require the risk of rejection. Choose life."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small risk. One tiny reach. One moment of courage. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A meaningful attempt. A conversation. An application. Medium vulnerability."
        else:
            capacity_note = "Good capacity. A bold move. A major ask. A significant risk. You have the strength to face rejection and grow."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Rejection is the tax you pay for a life worth living. The person who never experiences rejection is the person who never asks for anything. Who never applies. Who never loves. Who never creates. Who never risks. And that is not safety. That is poverty. Emotional poverty. Experiential poverty. Relational poverty. The person who faces rejection and keeps going is building something the rejection-avoider will never have: resilience. Confidence. Evidence that they can survive disappointment. And that evidence becomes the foundation for every future success. Because success is not the absence of rejection. It's the persistence through it."
        }

    def get_rejection_score(self) -> int:
        """Calculate overall rejection resilience (0-100)."""
        if not self._entries:
            return 25

        avg_recovery = sum(e.recovery for e in self._entries) / len(self._entries)
        avg_self_worth = sum(e.self_worth for e in self._entries) / len(self._entries)
        avg_learn = sum(e.learning for e in self._entries) / len(self._entries)
        avg_courage = sum(e.courage for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_recovery = sum(e.recovery for e in recent) / len(recent)
            recent_courage = sum(e.courage for e in recent) / len(recent)
        else:
            recent_recovery = 0
            recent_courage = 0

        # Avoidance penalty
        avoid_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if len(last_90) < 2:
            avoid_penalty = 15

        # Type variety
        unique_types = len(set(e.rejection_type for e in self._entries))

        # Impact normalization
        avg_impact = sum(e.impact for e in self._entries) / len(self._entries)

        score = (avg_recovery * 30) + (avg_self_worth * 20) + (avg_learn * 15) + (avg_courage * 15) + (recent_recovery * 10) + (recent_courage * 5) + (unique_types * 2) - avoid_penalty - (avg_impact * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_recovery"] = round(sum(e.recovery for e in self._entries) / len(self._entries), 2)
            self._stats["avg_self_worth"] = round(sum(e.self_worth for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_recovery = sum(e.recovery for e in recent) / len(recent)
                recent_courage = sum(e.courage for e in recent) / len(recent)
                self._stats["avoidance_risk"] = recent_recovery < 0.3 and recent_courage < 0.3
            else:
                self._stats["avoidance_risk"] = True

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

    def _log_entry(self, entry: RejectionEntry):
        try:
            with open(REJECTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "rejection": entry.rejection,
                    "rejection_type": entry.rejection_type,
                    "impact": entry.impact,
                    "recovery": entry.recovery,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rrc_instance: Optional[RejectionResilienceCoach] = None
_rrc_lock = threading.Lock()


def get_rejection_resilience_coach() -> RejectionResilienceCoach:
    global _rrc_instance
    with _rrc_lock:
        if _rrc_instance is None:
            _rrc_instance = RejectionResilienceCoach()
        return _rrc_instance
