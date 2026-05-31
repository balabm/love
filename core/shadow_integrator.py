"""
LOVE Shadow Integrator — Wholeness Intelligence (Modern AI Pattern)

Most people deny their shadow and project it onto others. This integrator:

1. SHADOW TRACKING
   - Record shadow encounters and their characteristics
   - Track shadow types (anger, envy, greed, lust, pride, fear, shame)
   - Log awareness, acceptance, and integration of shadow aspects

2. PATTERN ANALYSIS
   - Identify the user's shadow profile (integrated, repressed, projected, exploring)
   - Find shadow patterns that lead to wholeness vs fragmentation
   - Detect chronic repression and its consequences

3. SHADOW BUILDING
   - Suggest practices for meeting and integrating shadow aspects
   - Provide frameworks for understanding what triggers projection
   - Recommend practices for owning disowned parts

4. WHOLENESS CULTIVATION
   - Track the correlation between shadow integration and authenticity
   - Alert when shadow is being heavily projected
   - Celebrate moments of genuine self-acceptance

Architecture:
- record_encounter(shadow, type, awareness, acceptance, integration): Log encounter
- get_shadow_stats(): Get shadow pattern analysis
- get_shadow_suggestion(capacity, context): Get suggestion
- get_shadow_score(): Calculate overall shadow health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "shadow_integrator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SHADOW_LOG = DATA_DIR / "encounters.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ShadowEntry:
    """A tracked shadow encounter."""
    entry_id: str = ""
    shadow: str = ""  # what was encountered
    shadow_type: str = ""  # anger, envy, greed, lust, pride, fear, shame
    awareness: float = 0.0  # 0-1
    acceptance: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1
    trigger: str = ""  # what triggered it
    projection: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ShadowIntegrator:
    """
    Intelligent shadow integrator with awareness detection and wholeness cultivation.
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
            "avg_awareness": 0.0,
            "avg_integration": 0.0,
            "repression_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_encounter(self, shadow: str = "", shadow_type: str = "", awareness: float = 0.0, acceptance: float = 0.0, integration: float = 0.0, trigger: str = "", projection: float = 0.0, notes: str = "") -> ShadowEntry:
        """Record a shadow encounter."""
        entry_id = f"shd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ShadowEntry(
            entry_id=entry_id,
            shadow=shadow or "unspecified",
            shadow_type=shadow_type or "general",
            awareness=awareness,
            acceptance=acceptance,
            integration=integration,
            trigger=trigger or "unspecified",
            projection=projection,
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

    def get_shadow_stats(self) -> Dict[str, Any]:
        """Get shadow pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "awareness_sum": 0.0, "acceptance_sum": 0.0, "integration_sum": 0.0})
        for e in self._entries:
            by_type[e.shadow_type]["count"] += 1
            by_type[e.shadow_type]["awareness_sum"] += e.awareness
            by_type[e.shadow_type]["acceptance_sum"] += e.acceptance
            by_type[e.shadow_type]["integration_sum"] += e.integration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_awareness": round(data["awareness_sum"] / count, 2),
                "avg_acceptance": round(data["acceptance_sum"] / count, 2),
                "avg_integration": round(data["integration_sum"] / count, 2),
            }

        # Awareness analysis
        high_aware = [e for e in self._entries if e.awareness > 0.7]
        low_aware = [e for e in self._entries if e.awareness < 0.4]
        if high_aware and low_aware:
            high_aware_acc = sum(e.acceptance for e in high_aware) / len(high_aware)
            low_aware_acc = sum(e.acceptance for e in low_aware) / len(low_aware)
            high_aware_int = sum(e.integration for e in high_aware) / len(high_aware)
            low_aware_int = sum(e.integration for e in low_aware) / len(low_aware)
        else:
            high_aware_acc = 0
            low_aware_acc = 0
            high_aware_int = 0
            low_aware_int = 0

        # Projection analysis
        high_proj = [e for e in self._entries if e.projection > 0.7]
        low_proj = [e for e in self._entries if e.projection < 0.4]
        if high_proj and low_proj:
            high_proj_int = sum(e.integration for e in high_proj) / len(high_proj)
            low_proj_int = sum(e.integration for e in low_proj) / len(low_proj)
        else:
            high_proj_int = 0
            low_proj_int = 0

        # Repression risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_accept = sum(e.acceptance for e in recent) / len(recent)
            repression_risk = recent_aware < 0.3 and recent_accept < 0.3
        else:
            repression_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "awareness_impact": {
                "high_awareness_acceptance": round(high_aware_acc, 2),
                "low_awareness_acceptance": round(low_aware_acc, 2),
                "high_awareness_integration": round(high_aware_int, 2),
                "low_awareness_integration": round(low_aware_int, 2),
            },
            "projection_effect": {
                "high_projection_integration": round(high_proj_int, 2),
                "low_projection_integration": round(low_proj_int, 2),
            },
            "repression_risk": repression_risk,
            "avg_awareness": round(sum(e.awareness for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
        }

    def get_shadow_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get shadow suggestion."""
        suggestions = [
            "The trait you judge most harshly in others is the shadow you deny in yourself. Next time you're triggered by someone's behavior, ask: where do I do this too?",
            "Your shadow is not your enemy. It's the part of you that wasn't loved. That wasn't accepted. That had to hide. Meet it with compassion. It's been lonely.",
            "Write a letter from your shadow. Let it speak. What does it want? What does it need? What has it been trying to tell you? Listen without judgment.",
            "Everyone has a shadow. The person who denies it is the most dangerous. Not because they're evil. Because they're unconscious. Awareness is the first integration.",
            "Your anger is not bad. Your envy is not bad. Your greed is not bad. They're signals. They tell you what's unmet. What's violated. What you want. Listen.",
            "Integration is not acting out. It's acknowledging. 'I feel jealous. And that's okay. I don't need to sabotage anyone. I just need to acknowledge what I want.'",
            "The wholeness you seek is not the absence of shadow. It's the integration of it. The person who is only light is not whole. They're half.",
            "Your shadow holds your power. The rage you've suppressed is your boundary-setting power. The lust you've denied is your life force. Reclaim them. Channel them.",
            "Stop projecting. When you say 'they're so selfish,' ask: when am I selfish? When you say 'they're so lazy,' ask: where do I procrastinate? Own it.",
            "You cannot become whole by being good. You become whole by being real. The shadow is real. Meet it. Accept it. Integrate it. That's the path to wholeness."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One honest glance at your shadow. One admission. One moment of self-recognition. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A shadow journaling session. A projection analysis. Medium integration work."
        else:
            capacity_note = "Good capacity. Deep shadow work. A major integration. You have the strength to meet your disowned parts."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "The shadow is everything about yourself that you don't want to be. The anger. The envy. The greed. The lust. The pride. The fear. The shame. And the more you deny it, the more it controls you. Not by being expressed. But by being projected. The person who denies their anger sees anger everywhere. The person who denies their envy judges everyone as envious. The person who denies their shame shames others constantly. The work of shadow integration is not about becoming perfect. It's about becoming whole. It's about owning all of yourself. The light and the dark. The acceptable and the unacceptable. Because the person who owns their shadow is free. And the person who denies it is a prisoner."
        }

    def get_shadow_score(self) -> int:
        """Calculate overall shadow health (0-100)."""
        if not self._entries:
            return 25

        avg_aware = sum(e.awareness for e in self._entries) / len(self._entries)
        avg_accept = sum(e.acceptance for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_proj = sum(e.projection for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
        else:
            recent_aware = 0
            recent_int = 0

        # Repression penalty
        rep_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_aware_30 = sum(e.awareness for e in last_30) / len(last_30)
            recent_accept_30 = sum(e.acceptance for e in last_30) / len(last_30)
            if recent_aware_30 < 0.3 and recent_accept_30 < 0.3:
                rep_penalty = 15

        # Type variety
        unique_types = len(set(e.shadow_type for e in self._entries))

        # Projection penalty
        proj_penalty = min(15, avg_proj * 15)

        score = (avg_aware * 25) + (avg_accept * 20) + (avg_int * 25) + (recent_aware * 10) + (recent_int * 5) + (unique_types * 2) - rep_penalty - proj_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_awareness"] = round(sum(e.awareness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integration"] = round(sum(e.integration for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_aware = sum(e.awareness for e in recent) / len(recent)
                recent_accept = sum(e.acceptance for e in recent) / len(recent)
                self._stats["repression_risk"] = recent_aware < 0.3 and recent_accept < 0.3
            else:
                self._stats["repression_risk"] = False

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

    def _log_entry(self, entry: ShadowEntry):
        try:
            with open(SHADOW_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "shadow": entry.shadow,
                    "shadow_type": entry.shadow_type,
                    "awareness": entry.awareness,
                    "integration": entry.integration,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_si_instance: Optional[ShadowIntegrator] = None
_si_lock = threading.Lock()


def get_shadow_integrator() -> ShadowIntegrator:
    global _si_instance
    with _si_lock:
        if _si_instance is None:
            _si_instance = ShadowIntegrator()
        return _si_instance
