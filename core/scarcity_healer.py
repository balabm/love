"""
LOVE Scarcity Healer — Sufficiency Intelligence (Modern AI Pattern)

Most people live in manufactured scarcity. This healer:

1. SCARCITY TRACKING
   - Record scarcity moments and their characteristics
   - Track scarcity types (time, money, love, energy, opportunity, attention)
   - Log distress, reality, and response to scarcity triggers

2. PATTERN ANALYSIS
   - Identify the user's scarcity profile (chronic, situational, perceived, recovering)
   - Find scarcity patterns that motivate vs paralyze
   - Detect chronic scarcity and its costs

3. SCARCITY HEALING
   - Suggest practices for recognizing manufactured scarcity
   - Provide frameworks for sufficiency and enough-ness
   - Recommend practices for gratitude and perspective

4. SUFFICIENCY CULTIVATION
   - Track the correlation between perceived scarcity and wellbeing
   - Alert when scarcity is becoming the default lens
   - Celebrate moments of genuine "I have enough"

Architecture:
- record_scarcity(situation, type, distress, reality, response): Log scarcity
- get_scarcity_stats(): Get scarcity pattern analysis
- get_scarcity_suggestion(capacity, context): Get suggestion
- get_scarcity_score(): Calculate overall scarcity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "scarcity_healer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SCARCITY_LOG = DATA_DIR / "scarcities.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ScarcityEntry:
    """A tracked scarcity moment."""
    entry_id: str = ""
    situation: str = ""  # what happened
    scarcity_type: str = ""  # time, money, love, energy, opportunity, attention
    distress: float = 0.0  # 0-1
    reality: float = 0.0  # 0-1 actual scarcity vs perceived
    response: float = 0.0  # 0-1 how well you responded
    gratitude: float = 0.0  # 0-1
    perspective: float = 0.0  # 0-1
    sufficiency: float = 0.0  # 0-1 feeling of enough-ness
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ScarcityHealer:
    """
    Intelligent scarcity healer with distress detection and sufficiency cultivation.
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
            "avg_distress": 0.0,
            "avg_sufficiency": 0.0,
            "scarcity_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_scarcity(self, situation: str = "", scarcity_type: str = "", distress: float = 0.0, reality: float = 0.0, response: float = 0.0, gratitude: float = 0.0, perspective: float = 0.0, sufficiency: float = 0.0, notes: str = "") -> ScarcityEntry:
        """Record a scarcity moment."""
        entry_id = f"scr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ScarcityEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            scarcity_type=scarcity_type or "time",
            distress=distress,
            reality=reality,
            response=response,
            gratitude=gratitude,
            perspective=perspective,
            sufficiency=sufficiency,
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

    def get_scarcity_stats(self) -> Dict[str, Any]:
        """Get scarcity pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "distress_sum": 0.0, "reality_sum": 0.0, "sufficiency_sum": 0.0})
        for e in self._entries:
            by_type[e.scarcity_type]["count"] += 1
            by_type[e.scarcity_type]["distress_sum"] += e.distress
            by_type[e.scarcity_type]["reality_sum"] += e.reality
            by_type[e.scarcity_type]["sufficiency_sum"] += e.sufficiency

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_distress": round(data["distress_sum"] / count, 2),
                "avg_reality": round(data["reality_sum"] / count, 2),
                "avg_sufficiency": round(data["sufficiency_sum"] / count, 2),
            }

        # Perceived vs real scarcity
        high_distress = [e for e in self._entries if e.distress > 0.7]
        low_distress = [e for e in self._entries if e.distress < 0.4]
        if high_distress and low_distress:
            high_dist_resp = sum(e.response for e in high_distress) / len(high_distress)
            low_dist_resp = sum(e.response for e in low_distress) / len(low_distress)
            high_dist_real = sum(e.reality for e in high_distress) / len(high_distress)
            low_dist_real = sum(e.reality for e in low_distress) / len(low_distress)
        else:
            high_dist_resp = 0
            low_dist_resp = 0
            high_dist_real = 0
            low_dist_real = 0

        # Sufficiency analysis
        high_suff = [e for e in self._entries if e.sufficiency > 0.7]
        low_suff = [e for e in self._entries if e.sufficiency < 0.4]
        if high_suff and low_suff:
            high_suff_gr = sum(e.gratitude for e in high_suff) / len(high_suff)
            low_suff_gr = sum(e.gratitude for e in low_suff) / len(low_suff)
        else:
            high_suff_gr = 0
            low_suff_gr = 0

        # Scarcity risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_distress = sum(e.distress for e in recent) / len(recent)
            recent_suff = sum(e.sufficiency for e in recent) / len(recent)
            scarcity_risk = recent_distress > 0.7 and recent_suff < 0.3
        else:
            scarcity_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "distress_impact": {
                "high_distress_response": round(high_dist_resp, 2),
                "low_distress_response": round(low_dist_resp, 2),
                "high_distress_reality": round(high_dist_real, 2),
                "low_distress_reality": round(low_dist_real, 2),
            },
            "sufficiency_effect": {
                "high_sufficiency_gratitude": round(high_suff_gr, 2),
                "low_sufficiency_gratitude": round(low_suff_gr, 2),
            },
            "scarcity_risk": scarcity_risk,
            "avg_distress": round(sum(e.distress for e in self._entries) / len(self._entries), 2),
            "avg_sufficiency": round(sum(e.sufficiency for e in self._entries) / len(self._entries), 2),
        }

    def get_scarcity_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get scarcity suggestion."""
        suggestions = [
            "Most scarcity is manufactured. Not by marketers. By your mind. You have enough time. You have enough money. You have enough love. You just don't believe it.",
            "The scarcity mindset creates the scarcity. When you believe there's not enough, you hoard. You cling. You fear. And that behavior makes sure there's never enough. It's a self-fulfilling prophecy.",
            "Count what you have. Not what you lack. The scarcity mind counts deficits. The sufficiency mind counts assets. You have more than you think. Count.",
            "Time scarcity is usually priority scarcity. You don't lack time. You lack boundaries. You say yes to everything. Then you wonder why you're exhausted. Protect your time like it's precious. Because it is.",
            "Money scarcity is often spending scarcity. You're spending on things that don't matter. Then you don't have money for things that do. Track your spending. Align it with your values. Watch scarcity fade.",
            "Love scarcity is usually connection scarcity. You're surrounded by people but you're not connected. Reach out. One real conversation. One genuine moment. Scarcity of love is usually scarcity of courage to connect.",
            "Energy scarcity is usually rest scarcity. You're not tired because you do too much. You're tired because you don't recover. Rest is not laziness. It's maintenance. Take it seriously.",
            "Enough is a decision. Not a quantity. You can decide you have enough at any level of wealth, any level of time, any level of anything. The decision is what creates sufficiency.",
            "Scarcity thrives in comparison. When you compare what you have to what others have, you'll always find someone with more. Compare to what you need. That's the only comparison that matters.",
            "The antidote to scarcity is not abundance. It's gratitude. The person who is grateful for what they have never feels scarcity. The person who is not grateful never feels abundance. Gratitude is the lens."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of gratitude. One recognition of what you have. One breath of sufficiency. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A scarcity audit. A sufficiency practice. A perspective shift. Medium healing."
        else:
            capacity_note = "Good capacity. Deep scarcity healing. A systematic shift from perceived lack to genuine sufficiency. You have the strength to know you have enough."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Scarcity is not just a financial condition. It's a psychological condition. It's the belief that there's not enough. And that belief is usually false. Most people in the developed world have enough food, enough shelter, enough safety. But they don't feel like they have enough. Because feeling enough is not about having enough. It's about believing you have enough. And that belief is created by attention. What you pay attention to grows. If you pay attention to what you lack, you feel scarcity. If you pay attention to what you have, you feel sufficiency. The work of scarcity healing is not about getting more. It's about seeing what you already have. It's about recognizing that most of your scarcity is manufactured. By advertising. By social media. By comparison. By your own fearful mind. And it's about choosing a different lens. The lens of enough."
        }

    def get_scarcity_score(self) -> int:
        """Calculate overall scarcity health (0-100)."""
        if not self._entries:
            return 25

        avg_distress = sum(e.distress for e in self._entries) / len(self._entries)
        avg_suff = sum(e.sufficiency for e in self._entries) / len(self._entries)
        avg_resp = sum(e.response for e in self._entries) / len(self._entries)
        avg_grat = sum(e.gratitude for e in self._entries) / len(self._entries)
        avg_pers = sum(e.perspective for e in self._entries) / len(self._entries)
        avg_real = sum(e.reality for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_distress = sum(e.distress for e in recent) / len(recent)
            recent_suff = sum(e.sufficiency for e in recent) / len(recent)
        else:
            recent_distress = 0
            recent_suff = 0

        # Scarcity penalty
        scarcity_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_distress_30 = sum(e.distress for e in last_30) / len(last_30)
            recent_suff_30 = sum(e.sufficiency for e in last_30) / len(last_30)
            if recent_distress_30 > 0.7 and recent_suff_30 < 0.3:
                scarcity_penalty = 15

        # Type variety
        unique_types = len(set(e.scarcity_type for e in self._entries))

        score = (avg_suff * 30) + (avg_resp * 15) + (avg_grat * 15) + (avg_pers * 10) + (avg_real * 10) + (recent_suff * 10) + (recent_suff * 5) + (unique_types * 2) - (avg_distress * 15) - scarcity_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_distress"] = round(sum(e.distress for e in self._entries) / len(self._entries), 2)
            self._stats["avg_sufficiency"] = round(sum(e.sufficiency for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_distress = sum(e.distress for e in recent) / len(recent)
                recent_suff = sum(e.sufficiency for e in recent) / len(recent)
                self._stats["scarcity_risk"] = recent_distress > 0.7 and recent_suff < 0.3
            else:
                self._stats["scarcity_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.scarcity_healer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.scarcity_healer")

    def _log_entry(self, entry: ScarcityEntry):
        try:
            with open(SCARCITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "scarcity_type": entry.scarcity_type,
                    "distress": entry.distress,
                    "sufficiency": entry.sufficiency,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.scarcity_healer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sh_instance: Optional[ScarcityHealer] = None
_sh_lock = threading.Lock()


def get_scarcity_healer() -> ScarcityHealer:
    global _sh_instance
    with _sh_lock:
        if _sh_instance is None:
            _sh_instance = ScarcityHealer()
        return _sh_instance
