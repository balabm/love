"""
LOVE Shadow Integrator — Unconscious Intelligence (Modern AI Pattern)

Most people reject their shadow, making it stronger. This integrator:

1. SHADOW TRACKING
   - Record shadow traits and their triggers
   - Track projection patterns (seeing your shadow in others)
   - Log integration attempts and their outcomes

2. PATTERN ANALYSIS
   - Identify the user's shadow themes (what they deny in themselves)
   - Find projection targets (who they project shadow onto)
   - Detect shadow activation contexts

3. INTEGRATION PRACTICES
   - Suggest shadow-acceptance exercises
   - Provide projection-awareness techniques
   - Recommend integration rituals for specific shadows

4. WHOLENESS TRACKING
   - Track the correlation between shadow integration and emotional stability
   - Alert when projection is distorting relationships
   - Celebrate integration milestones

Architecture:
- record_shadow(trait, trigger, projection_target, integration): Log shadow
- get_shadow_stats(): Get shadow pattern analysis
- get_integration_exercise(shadow, intensity): Get exercise
- get_shadow_score(): Calculate overall shadow integration health
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

SHADOW_LOG = DATA_DIR / "shadows.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ShadowEntry:
    """A tracked shadow entry."""
    entry_id: str = ""
    trait: str = ""  # anger, greed, jealousy, laziness, arrogance, vulnerability, etc.
    trigger: str = ""  # what activated it
    projection_target: str = ""  # who they see this in
    reaction: str = ""  # how they reacted
    integration_attempt: str = ""  # what they did to integrate
    integration_success: float = 0.0  # 0-1
    emotional_intensity: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ShadowIntegrator:
    """
    Intelligent shadow integrator with projection detection and wholeness tracking.
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
        self._entries: deque = deque(maxlen=200)
        self._stats = {
            "total_entries": 0,
            "avg_integration": 0.0,
            "avg_intensity": 0.0,
            "dominant_shadow": "",
            "top_projection_target": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_shadow(self, trait: str = "", trigger: str = "", projection_target: str = "", reaction: str = "", integration_attempt: str = "", integration_success: float = 0.0, emotional_intensity: float = 0.5, notes: str = "") -> ShadowEntry:
        """Record a shadow entry."""
        entry_id = f"shadow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ShadowEntry(
            entry_id=entry_id,
            trait=trait or "unspecified",
            trigger=trigger,
            projection_target=projection_target,
            reaction=reaction,
            integration_attempt=integration_attempt,
            integration_success=integration_success,
            emotional_intensity=emotional_intensity,
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

        # Trait analysis
        by_trait = defaultdict(lambda: {"count": 0, "integration_sum": 0.0, "intensity_sum": 0.0})
        for e in self._entries:
            by_trait[e.trait]["count"] += 1
            by_trait[e.trait]["integration_sum"] += e.integration_success
            by_trait[e.trait]["intensity_sum"] += e.emotional_intensity

        trait_stats = {}
        for t, data in by_trait.items():
            count = data["count"]
            trait_stats[t] = {
                "count": count,
                "avg_integration": round(data["integration_sum"] / count, 2),
                "avg_intensity": round(data["intensity_sum"] / count, 2),
            }

        dominant = max(trait_stats.items(), key=lambda x: x[1]["count"]) if trait_stats else ("", {})

        # Projection target analysis
        by_target = defaultdict(lambda: {"count": 0, "integration_sum": 0.0})
        for e in self._entries:
            if e.projection_target:
                by_target[e.projection_target]["count"] += 1
                by_target[e.projection_target]["integration_sum"] += e.integration_success

        target_stats = {}
        for target, data in by_target.items():
            count = data["count"]
            target_stats[target] = {
                "count": count,
                "avg_integration": round(data["integration_sum"] / count, 2),
            }

        top_target = max(target_stats.items(), key=lambda x: x[1]["count"]) if target_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for e in self._entries:
            if e.trigger:
                by_trigger[e.trigger]["count"] += 1
                by_trigger[e.trigger]["intensity_sum"] += e.emotional_intensity

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            trigger_stats[tr] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
            }

        # Integration trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_integration = sum(e.integration_success for e in recent) / len(recent)
        else:
            recent_integration = 0

        # High-intensity unintegrated shadows
        unintegrated = [e for e in self._entries if e.integration_success < 0.3 and e.emotional_intensity > 0.6]

        return {
            "total_entries": len(self._entries),
            "trait_stats": trait_stats,
            "dominant_shadow": dominant[0],
            "target_stats": target_stats,
            "top_projection_target": top_target[0],
            "trigger_stats": trigger_stats,
            "avg_integration": round(sum(e.integration_success for e in self._entries) / len(self._entries), 2),
            "avg_intensity": round(sum(e.emotional_intensity for e in self._entries) / len(self._entries), 2),
            "recent_integration": round(recent_integration, 2),
            "unintegrated_shadows": len(unintegrated),
        }

    def get_integration_exercise(self, shadow: str = "", intensity: float = 0.5, projection_target: str = "") -> Dict[str, Any]:
        """Get exercise."""
        exercises = [
            f"Write a letter to your {shadow} self. Thank it for protecting you. Ask what it needs.",
            f"When you see {shadow} in others, say to yourself: 'This is mine too. We share this.'",
            f"Draw your {shadow}. Give it a name. Talk to it. It has something to teach you.",
            f"List 3 ways your {shadow} has helped you in the past. Everything has a gift.",
            f"Sit with your {shadow} for 5 minutes. Don't try to fix it. Just be with it.",
            f"Ask someone you trust: 'When do you see my {shadow}?' Listen without defending.",
            f"Create an altar or space for your {shadow}. Honor it as part of your wholeness.",
            f"Write: 'I am learning to accept my {shadow}. It is part of me, not all of me.'",
        ]

        if intensity > 0.7:
            approach = f"Your {shadow} is very active right now. Don't fight it. Befriend it. It wants something."
        elif intensity > 0.4:
            approach = f"Your {shadow} is present but manageable. Practice noticing it before acting on it."
        else:
            approach = f"Your {shadow} is quiet now. This is a good time to do preventive integration work."

        if projection_target:
            projection_note = f"You often see this in {projection_target}. Next time, ask: 'Where is this in me?'"
        else:
            projection_note = "Notice who triggers strong reactions in you. They're often mirrors."

        return {
            "shadow": shadow or "unspecified",
            "intensity": intensity,
            "projection_target": projection_target or "varies",
            "approach": approach,
            "exercise": random.choice(exercises),
            "projection_note": projection_note,
            "principle": "What you reject in yourself, you fight in others. What you accept in yourself, you transform in the world.",
        }

    def get_shadow_score(self) -> int:
        """Calculate overall shadow integration health (0-100)."""
        if not self._entries:
            return 30

        # Integration rate
        avg_integration = sum(e.integration_success for e in self._entries) / len(self._entries)

        # Low unintegrated intensity
        unintegrated = [e for e in self._entries if e.integration_success < 0.3]
        if unintegrated:
            avg_unintegrated_intensity = sum(e.emotional_intensity for e in unintegrated) / len(unintegrated)
        else:
            avg_unintegrated_intensity = 0

        # Variety of shadows integrated (wholeness)
        integrated_traits = set(e.trait for e in self._entries if e.integration_success > 0.5)
        wholeness = len(integrated_traits)

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_integration = sum(e.integration_success for e in recent) / len(recent)
        else:
            recent_integration = 0

        # Projection awareness
        projection_entries = [e for e in self._entries if e.projection_target]
        if projection_entries:
            projection_integration = sum(e.integration_success for e in projection_entries) / len(projection_entries)
        else:
            projection_integration = 0

        score = (avg_integration * 30) + ((1 - avg_unintegrated_intensity) * 20) + (wholeness * 3) + (recent_integration * 15) + (projection_integration * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_integration"] = round(sum(e.integration_success for e in self._entries) / len(self._entries), 2)
            self._stats["avg_intensity"] = round(sum(e.emotional_intensity for e in self._entries) / len(self._entries), 2)

            by_trait = defaultdict(lambda: {"count": 0, "integration": 0.0})
            for e in self._entries:
                by_trait[e.trait]["count"] += 1
                by_trait[e.trait]["integration"] += e.integration_success
            if by_trait:
                dominant = max(by_trait.items(), key=lambda x: x[1]["count"])
                self._stats["dominant_shadow"] = dominant[0]

            by_target = defaultdict(lambda: {"count": 0, "integration": 0.0})
            for e in self._entries:
                if e.projection_target:
                    by_target[e.projection_target]["count"] += 1
                    by_target[e.projection_target]["integration"] += e.integration_success
            if by_target:
                top = max(by_target.items(), key=lambda x: x[1]["count"])
                self._stats["top_projection_target"] = top[0]

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
                    "trait": entry.trait,
                    "trigger": entry.trigger,
                    "projection_target": entry.projection_target,
                    "integration_success": entry.integration_success,
                    "emotional_intensity": entry.emotional_intensity,
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
