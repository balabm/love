"""
LOVE Boundary Coach — Limits Intelligence (Modern AI Pattern)

Most people have porous boundaries and suffer for it. This coach:

1. BOUNDARY TRACKING
   - Record boundary situations and their characteristics
   - Track boundary types (time, emotional, physical, digital, relational)
   - Log clarity, enforcement, and comfort with boundaries

2. PATTERN ANALYSIS
   - Identify the user's boundary profile (firm, porous, rigid, unclear)
   - Find boundary patterns that create wellbeing vs resentment
   - Detect boundary violations and their sources

3. BOUNDARY BUILDING
   - Suggest boundary practices matched to current relationships and capacity
   - Provide frameworks for saying no and setting limits
   - Recommend boundary repair after violation

4. AUTONOMY CULTIVATION
   - Track the correlation between boundaries and energy levels
   - Alert when boundaries are becoming chronically violated
   - Celebrate moments of genuine boundary clarity and enforcement

Architecture:
- record_boundary(situation, type, clarity, enforced, comfort): Log boundary
- get_boundary_stats(): Get boundary pattern analysis
- get_boundary_suggestion(capacity, context): Get suggestion
- get_boundary_score(): Calculate overall boundary health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "boundary_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BOUNDARY_LOG = DATA_DIR / "boundaries.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BoundaryEntry:
    """A tracked boundary situation."""
    entry_id: str = ""
    situation: str = ""  # what happened
    boundary_type: str = ""  # time, emotional, physical, digital, relational
    clarity: float = 0.5  # 0-1
    enforced: float = 0.0  # 0-1
    comfort: float = 0.0  # 0-1
    consequence: float = 0.0  # 0-1 result of enforcement
    respect_received: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BoundaryCoach:
    """
    Intelligent boundary coach with clarity detection and autonomy cultivation.
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
            "avg_clarity": 0.0,
            "avg_enforced": 0.0,
            "violation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_boundary(self, situation: str = "", boundary_type: str = "", clarity: float = 0.5, enforced: float = 0.0, comfort: float = 0.0, consequence: float = 0.0, respect_received: float = 0.0, notes: str = "") -> BoundaryEntry:
        """Record a boundary situation."""
        entry_id = f"bnd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BoundaryEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            boundary_type=boundary_type or "relational",
            clarity=clarity,
            enforced=enforced,
            comfort=comfort,
            consequence=consequence,
            respect_received=respect_received,
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

    def get_boundary_stats(self) -> Dict[str, Any]:
        """Get boundary pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "enforced_sum": 0.0, "comfort_sum": 0.0})
        for e in self._entries:
            by_type[e.boundary_type]["count"] += 1
            by_type[e.boundary_type]["clarity_sum"] += e.clarity
            by_type[e.boundary_type]["enforced_sum"] += e.enforced
            by_type[e.boundary_type]["comfort_sum"] += e.comfort

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_enforced": round(data["enforced_sum"] / count, 2),
                "avg_comfort": round(data["comfort_sum"] / count, 2),
            }

        # Clarity analysis
        high_clarity = [e for e in self._entries if e.clarity > 0.7]
        low_clarity = [e for e in self._entries if e.clarity < 0.4]
        if high_clarity and low_clarity:
            high_clar_enf = sum(e.enforced for e in high_clarity) / len(high_clarity)
            low_clar_enf = sum(e.enforced for e in low_clarity) / len(low_clarity)
            high_clar_comf = sum(e.comfort for e in high_clarity) / len(high_clarity)
            low_clar_comf = sum(e.comfort for e in low_clarity) / len(low_clarity)
        else:
            high_clar_enf = 0
            low_clar_enf = 0
            high_clar_comf = 0
            low_clar_comf = 0

        # Enforcement analysis
        high_enf = [e for e in self._entries if e.enforced > 0.7]
        low_enf = [e for e in self._entries if e.enforced < 0.4]
        if high_enf and low_enf:
            high_enf_resp = sum(e.respect_received for e in high_enf) / len(high_enf)
            low_enf_resp = sum(e.respect_received for e in low_enf) / len(low_enf)
            high_enf_conseq = sum(e.consequence for e in high_enf) / len(high_enf)
            low_enf_conseq = sum(e.consequence for e in low_enf) / len(low_enf)
        else:
            high_enf_resp = 0
            low_enf_resp = 0
            high_enf_conseq = 0
            low_enf_conseq = 0

        # Violation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_clarity = sum(e.clarity for e in recent) / len(recent)
            recent_enforced = sum(e.enforced for e in recent) / len(recent)
            recent_comfort = sum(e.comfort for e in recent) / len(recent)
            violation_risk = recent_clarity < 0.4 and recent_enforced < 0.4 and recent_comfort < 0.4
        else:
            violation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "clarity_impact": {
                "high_clarity_enforced": round(high_clar_enf, 2),
                "low_clarity_enforced": round(low_clar_enf, 2),
                "high_clarity_comfort": round(high_clar_comf, 2),
                "low_clarity_comfort": round(low_clar_comf, 2),
            },
            "enforcement_effect": {
                "high_enforcement_respect": round(high_enf_resp, 2),
                "low_enforcement_respect": round(low_enf_resp, 2),
                "high_enforcement_consequence": round(high_enf_conseq, 2),
                "low_enforcement_consequence": round(low_enf_conseq, 2),
            },
            "violation_risk": violation_risk,
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
            "avg_enforced": round(sum(e.enforced for e in self._entries) / len(self._entries), 2),
        }

    def get_boundary_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get boundary suggestion."""
        suggestions = [
            "No is a complete sentence. You don't need to justify. You don't need to explain. You don't need to apologize. 'No, thank you.' That's enough.",
            "Start small. Say no to one thing today. A request. An invitation. A demand. Practice the muscle. It gets easier.",
            "Your time is not communal property. It's yours. Protect it. Schedule your priorities first. Let everything else fill the gaps. Not the other way around.",
            "Boundaries are not walls. They're doors. You decide who enters, when, and for how long. The people who respect your doors are the people who get to stay.",
            "Guilt is not a sign your boundary is wrong. It's a sign your boundary is new. The guilt will pass. The boundary will remain. Hold the line.",
            "Communicate your boundaries before you're resentful. Resentment is the accumulation of unexpressed boundaries. Speak early. Speak clearly.",
            "People who get angry at your boundaries are the reason you need boundaries. Their reaction is information. Not a reason to abandon the boundary.",
            "Boundaries are self-respect in action. When you honor your own limits, you teach others to honor them too. When you ignore them, you teach others to ignore them too.",
            "Digital boundaries matter too. Turn off notifications. Don't answer after hours. Protect your attention. It's the most valuable thing you have.",
            "You cannot pour from an empty cup. And you cannot be a good partner, parent, friend, or worker if you're chronically depleted. Boundaries are how you protect your capacity to show up for the things that matter."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small no. One small limit. One moment of self-protection. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A clear boundary. A difficult conversation. A protected block of time. Medium investment in autonomy."
        else:
            capacity_note = "Good capacity. A major boundary reset. A relationship renegotiation. A systematic change in how you allocate your energy. You have the strength to reclaim your space."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Boundaries are the architecture of self-respect. Without them, you are not a person. You are a resource. Available to anyone. At any time. For any purpose. And that is not living. That is existing in service of other people's convenience. The people who love you will respect your boundaries. The people who don't were never really loving you. They were using you. And the person who uses you is not your friend. They're your consumer. Boundaries are how you say: I am a person. With limits. With needs. With a right to my own time, energy, and attention. And that right is non-negotiable."
        }

    def get_boundary_score(self) -> int:
        """Calculate overall boundary health (0-100)."""
        if not self._entries:
            return 25

        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_enforced = sum(e.enforced for e in self._entries) / len(self._entries)
        avg_comfort = sum(e.comfort for e in self._entries) / len(self._entries)
        avg_respect = sum(e.respect_received for e in self._entries) / len(self._entries)
        avg_consequence = sum(e.consequence for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_clarity = sum(e.clarity for e in recent) / len(recent)
            recent_enforced = sum(e.enforced for e in recent) / len(recent)
        else:
            recent_clarity = 0
            recent_enforced = 0

        # Violation penalty
        violation_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_clar_30 = sum(e.clarity for e in last_30) / len(last_30)
            recent_enf_30 = sum(e.enforced for e in last_30) / len(last_30)
            recent_comf_30 = sum(e.comfort for e in last_30) / len(last_30)
            if recent_clar_30 < 0.4 and recent_enf_30 < 0.4 and recent_comf_30 < 0.4:
                violation_penalty = 15

        # Type variety
        unique_types = len(set(e.boundary_type for e in self._entries))

        score = (avg_clarity * 25) + (avg_enforced * 25) + (avg_comfort * 15) + (avg_respect * 10) + (avg_consequence * 10) + (recent_clarity * 5) + (recent_enforced * 5) + (unique_types * 2) - violation_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_enforced"] = round(sum(e.enforced for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_clarity = sum(e.clarity for e in recent) / len(recent)
                recent_enforced = sum(e.enforced for e in recent) / len(recent)
                recent_comfort = sum(e.comfort for e in recent) / len(recent)
                self._stats["violation_risk"] = recent_clarity < 0.4 and recent_enforced < 0.4 and recent_comfort < 0.4
            else:
                self._stats["violation_risk"] = False

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

    def _log_entry(self, entry: BoundaryEntry):
        try:
            with open(BOUNDARY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "boundary_type": entry.boundary_type,
                    "clarity": entry.clarity,
                    "enforced": entry.enforced,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_bc_instance: Optional[BoundaryCoach] = None
_bc_lock = threading.Lock()


def get_boundary_coach() -> BoundaryCoach:
    global _bc_instance
    with _bc_lock:
        if _bc_instance is None:
            _bc_instance = BoundaryCoach()
        return _bc_instance
