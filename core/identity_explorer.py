"""
LOVE Identity Explorer — Selfhood Intelligence (Modern AI Pattern)

Most people never examine who they are. This explorer:

1. IDENTITY TRACKING
   - Record identity reflections and their characteristics
   - Track identity aspects (roles, values, traits, aspirations, history)
   - Log clarity, authenticity, and integration of identity

2. PATTERN ANALYSIS
   - Identify the user's identity profile (integrated, fragmented, borrowed, evolving)
   - Find identity patterns that create coherence vs confusion
   - Detect identity drift and its causes

3. IDENTITY BUILDING
   - Suggest practices for self-discovery and authenticity
   - Provide frameworks for integrating competing roles
   - Recommend identity anchoring during change

4. AUTHENTICITY CULTIVATION
   - Track the correlation between identity clarity and life satisfaction
   - Alert when identity is becoming performative
   - Celebrate moments of genuine self-discovery

Architecture:
- record_reflection(reflection, aspect, clarity, authenticity, integration): Log reflection
- get_identity_stats(): Get identity pattern analysis
- get_identity_suggestion(capacity, context): Get suggestion
- get_identity_score(): Calculate overall identity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "identity_explorer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

IDENTITY_LOG = DATA_DIR / "reflections.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class IdentityEntry:
    """A tracked identity reflection."""
    entry_id: str = ""
    reflection: str = ""  # the reflection
    aspect: str = ""  # roles, values, traits, aspirations, history
    clarity: float = 0.0  # 0-1
    authenticity: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1
    alignment: float = 0.0  # 0-1 alignment between inner and outer
    growth: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class IdentityExplorer:
    """
    Intelligent identity explorer with clarity detection and authenticity cultivation.
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
            "avg_authenticity": 0.0,
            "performative_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_reflection(self, reflection: str = "", aspect: str = "", clarity: float = 0.0, authenticity: float = 0.0, integration: float = 0.0, alignment: float = 0.0, growth: float = 0.0, notes: str = "") -> IdentityEntry:
        """Record an identity reflection."""
        entry_id = f"idt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = IdentityEntry(
            entry_id=entry_id,
            reflection=reflection or "unspecified",
            aspect=aspect or "general",
            clarity=clarity,
            authenticity=authenticity,
            integration=integration,
            alignment=alignment,
            growth=growth,
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

    def get_identity_stats(self) -> Dict[str, Any]:
        """Get identity pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Aspect analysis
        by_aspect = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "authenticity_sum": 0.0, "integration_sum": 0.0})
        for e in self._entries:
            by_aspect[e.aspect]["count"] += 1
            by_aspect[e.aspect]["clarity_sum"] += e.clarity
            by_aspect[e.aspect]["authenticity_sum"] += e.authenticity
            by_aspect[e.aspect]["integration_sum"] += e.integration

        aspect_stats = {}
        for a, data in by_aspect.items():
            count = data["count"]
            aspect_stats[a] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_authenticity": round(data["authenticity_sum"] / count, 2),
                "avg_integration": round(data["integration_sum"] / count, 2),
            }

        # Clarity analysis
        high_clarity = [e for e in self._entries if e.clarity > 0.7]
        low_clarity = [e for e in self._entries if e.clarity < 0.4]
        if high_clarity and low_clarity:
            high_clar_auth = sum(e.authenticity for e in high_clarity) / len(high_clarity)
            low_clar_auth = sum(e.authenticity for e in low_clarity) / len(low_clarity)
            high_clar_align = sum(e.alignment for e in high_clarity) / len(high_clarity)
            low_clar_align = sum(e.alignment for e in low_clarity) / len(low_clarity)
        else:
            high_clar_auth = 0
            low_clar_auth = 0
            high_clar_align = 0
            low_clar_align = 0

        # Authenticity analysis
        high_auth = [e for e in self._entries if e.authenticity > 0.7]
        low_auth = [e for e in self._entries if e.authenticity < 0.4]
        if high_auth and low_auth:
            high_auth_int = sum(e.integration for e in high_auth) / len(high_auth)
            low_auth_int = sum(e.integration for e in low_auth) / len(low_auth)
        else:
            high_auth_int = 0
            low_auth_int = 0

        # Performative risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            recent_align = sum(e.alignment for e in recent) / len(recent)
            performative_risk = recent_auth < 0.4 and recent_align < 0.4
        else:
            performative_risk = False

        return {
            "total_entries": len(self._entries),
            "aspect_stats": aspect_stats,
            "clarity_impact": {
                "high_clarity_authenticity": round(high_clar_auth, 2),
                "low_clarity_authenticity": round(low_clar_auth, 2),
                "high_clarity_alignment": round(high_clar_align, 2),
                "low_clarity_alignment": round(low_clar_align, 2),
            },
            "authenticity_effect": {
                "high_authenticity_integration": round(high_auth_int, 2),
                "low_authenticity_integration": round(low_auth_int, 2),
            },
            "performative_risk": performative_risk,
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
            "avg_authenticity": round(sum(e.authenticity for e in self._entries) / len(self._entries), 2),
        }

    def get_identity_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get identity suggestion."""
        suggestions = [
            "Ask yourself: who am I when no one is watching? The answer is closer to your real self than any role you play. Spend time there.",
            "Your identity is not fixed. It's a story you're continuously writing. You can change the narrative. You can become someone new. That's not failure. That's growth.",
            "List your roles. Parent. Worker. Friend. Citizen. Which ones fit? Which ones chafe? Identity integration starts with honest assessment.",
            "The person you pretend to be is exhausting. The person you are is enough. Authenticity is not about being perfect. It's about being real.",
            "What did you love as a child? Before the world told you who to be? That child still lives in you. Their passions are clues to your authentic self.",
            "Identity is not what you do. It's who you are when you're doing it. Two people can do the same job. One is a sellout. One is an artist. The difference is identity.",
            "You are allowed to outgrow your past. The person you were at 20 is not the person you are at 40. And that's not a betrayal. It's evolution.",
            "Write your own eulogy. What do you want to be remembered for? That's your real identity. Not your title. Not your income. Your impact. Your character.",
            "The roles that consume you are not your identity. They are costumes. Don't mistake the costume for the actor. You are more than any single role.",
            "Knowing yourself is the beginning of all wisdom. Not in an abstract philosophical sense. In a practical, daily sense. What do you need? What do you want? What do you value? What do you fear? The clearer your answers, the clearer your path."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One honest thought. One true feeling. One moment of self-recognition. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A journaling session. A values clarification. A role assessment. Medium self-exploration."
        else:
            capacity_note = "Good capacity. Deep identity work. A life review. A major realignment. You have the strength for real self-discovery."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Identity is not something you discover once and then possess. It's a continuous negotiation between who you've been, who you are, and who you're becoming. Most people live with borrowed identities. The expectations of parents. The demands of society. The templates of success. And they wonder why they feel hollow. Authentic identity is earned. It's the result of honest examination, difficult choices, and the courage to be misunderstood. The person who knows who they are is immune to manipulation. They're immune to comparison. They're immune to the anxiety of not fitting in. Because they know they fit in with themselves. And that's enough."
        }

    def get_identity_score(self) -> int:
        """Calculate overall identity health (0-100)."""
        if not self._entries:
            return 25

        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_align = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_clarity = sum(e.clarity for e in recent) / len(recent)
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
        else:
            recent_clarity = 0
            recent_auth = 0

        # Performative penalty
        perf_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_auth_30 = sum(e.authenticity for e in last_30) / len(last_30)
            recent_align_30 = sum(e.alignment for e in last_30) / len(last_30)
            if recent_auth_30 < 0.4 and recent_align_30 < 0.4:
                perf_penalty = 15

        # Aspect variety
        unique_aspects = len(set(e.aspect for e in self._entries))

        score = (avg_clarity * 25) + (avg_auth * 25) + (avg_int * 15) + (avg_align * 15) + (avg_growth * 10) + (recent_clarity * 5) + (recent_auth * 5) + (unique_aspects * 2) - perf_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_authenticity"] = round(sum(e.authenticity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_auth = sum(e.authenticity for e in recent) / len(recent)
                recent_align = sum(e.alignment for e in recent) / len(recent)
                self._stats["performative_risk"] = recent_auth < 0.4 and recent_align < 0.4
            else:
                self._stats["performative_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.identity_explorer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.identity_explorer")

    def _log_entry(self, entry: IdentityEntry):
        try:
            with open(IDENTITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "reflection": entry.reflection,
                    "aspect": entry.aspect,
                    "clarity": entry.clarity,
                    "authenticity": entry.authenticity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.identity_explorer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ie_instance: Optional[IdentityExplorer] = None
_ie_lock = threading.Lock()


def get_identity_explorer() -> IdentityExplorer:
    global _ie_instance
    with _ie_lock:
        if _ie_instance is None:
            _ie_instance = IdentityExplorer()
        return _ie_instance
