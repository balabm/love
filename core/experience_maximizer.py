"""
LOVE Experience Maximizer — Depth and Presence Intelligence (Modern AI Pattern)

Most people optimize for quantity of experiences. This engine optimizes for
quality, depth, and lasting impact. The most vivid memories are not from
longest experiences but from most present ones.

1. EXPERIENCE TRACKING
   - Record experiences and their characteristics
   - Track depth (flow, presence, absorption)
   - Track richness (sensory, emotional, intellectual)
   - Log lasting impact and integration

2. PATTERN ANALYSIS
   - Identify what makes experiences memorable and transformative
   - Find the gap between planned experience and actual depth
   - Detect shallow-living patterns (multitasking, documentation over presence)

3. EXPERIENCE OPTIMIZATION
   - Suggest techniques for deepening any experience
   - Provide pre-experience priming and post-experience integration
   - Recommend the right level of novelty vs comfort

4. DEPTH CULTIVATION
   - Track the user's "depth score" over time
   - Alert when life is becoming a series of shallow impressions
   - Celebrate moments of genuine absorption and presence

Architecture:
- record_experience(activity, depth, richness, impact): Log experience
- get_experience_stats(): Get pattern analysis
- get_depth_suggestion(activity, context): Get depth suggestion
- get_depth_score(): Calculate overall depth health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "experience_maximizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPERIENCE_LOG = DATA_DIR / "experiences.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ExperienceEntry:
    """A tracked experience entry."""
    entry_id: str = ""
    activity: str = ""  # what was experienced
    depth: float = 0.5  # 0-1 (flow, presence, absorption)
    richness: float = 0.5  # 0-1 (sensory, emotional, intellectual)
    novelty: float = 0.5  # 0-1 (newness)
    duration_minutes: float = 0.0
    impact: float = 0.0  # 0-1 lasting effect
    integration: float = 0.0  # 0-1 how well processed afterward
    multitasking: float = 0.0  # 0-1 (inverse of depth)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ExperienceMaximizer:
    """
    Intelligent experience optimizer with depth detection and presence cultivation.
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
            "avg_depth": 0.0,
            "avg_impact": 0.0,
            "shallow_living_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_experience(self, activity: str = "", depth: float = 0.5, richness: float = 0.5, novelty: float = 0.5, duration_minutes: float = 0.0, impact: float = 0.0, integration: float = 0.0, multitasking: float = 0.0, notes: str = "") -> ExperienceEntry:
        """Record an experience entry."""
        entry_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ExperienceEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            depth=depth,
            richness=richness,
            novelty=novelty,
            duration_minutes=duration_minutes,
            impact=impact,
            integration=integration,
            multitasking=multitasking,
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

    def get_experience_stats(self) -> Dict[str, Any]:
        """Get experience pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Depth vs impact
        deep = [e for e in self._entries if e.depth > 0.7]
        shallow = [e for e in self._entries if e.depth < 0.4]
        if deep and shallow:
            deep_impact = sum(e.impact for e in deep) / len(deep)
            shallow_impact = sum(e.impact for e in shallow) / len(shallow)
            deep_richness = sum(e.richness for e in deep) / len(deep)
            shallow_richness = sum(e.richness for e in shallow) / len(shallow)
        else:
            deep_impact = 0
            shallow_impact = 0
            deep_richness = 0
            shallow_richness = 0

        # Novelty analysis
        novel = [e for e in self._entries if e.novelty > 0.7]
        familiar = [e for e in self._entries if e.novelty < 0.4]
        if novel and familiar:
            novel_depth = sum(e.depth for e in novel) / len(novel)
            familiar_depth = sum(e.depth for e in familiar) / len(familiar)
        else:
            novel_depth = 0
            familiar_depth = 0

        # Multitasking penalty
        high_multi = [e for e in self._entries if e.multitasking > 0.5]
        low_multi = [e for e in self._entries if e.multitasking < 0.3]
        if high_multi and low_multi:
            high_multi_depth = sum(e.depth for e in high_multi) / len(high_multi)
            low_multi_depth = sum(e.depth for e in low_multi) / len(low_multi)
            high_multi_impact = sum(e.impact for e in high_multi) / len(high_multi)
            low_multi_impact = sum(e.impact for e in low_multi) / len(low_multi)
        else:
            high_multi_depth = 0
            low_multi_depth = 0
            high_multi_impact = 0
            low_multi_impact = 0

        # Integration analysis
        high_int = [e for e in self._entries if e.integration > 0.7]
        low_int = [e for e in self._entries if e.integration < 0.4]
        if high_int and low_int:
            high_int_impact = sum(e.impact for e in high_int) / len(high_int)
            low_int_impact = sum(e.impact for e in low_int) / len(low_int)
        else:
            high_int_impact = 0
            low_int_impact = 0

        # Shallow living detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_multi = sum(e.multitasking for e in recent) / len(recent)
            shallow_living_risk = recent_depth < 0.4 and recent_multi > 0.5
        else:
            shallow_living_risk = True

        # Duration sweet spot
        by_duration = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            bucket = "short" if e.duration_minutes < 30 else "medium" if e.duration_minutes < 120 else "long"
            by_duration[bucket]["count"] += 1
            by_duration[bucket]["depth_sum"] += e.depth
            by_duration[bucket]["impact_sum"] += e.impact

        duration_stats = {}
        for bucket, data in by_duration.items():
            count = data["count"]
            duration_stats[bucket] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        return {
            "total_entries": len(self._entries),
            "depth_impact": {
                "deep_impact": round(deep_impact, 2),
                "shallow_impact": round(shallow_impact, 2),
                "deep_richness": round(deep_richness, 2),
                "shallow_richness": round(shallow_richness, 2),
            },
            "novelty_effect": {
                "novel_depth": round(novel_depth, 2),
                "familiar_depth": round(familiar_depth, 2),
            },
            "multitasking_penalty": {
                "high_multi_depth": round(high_multi_depth, 2),
                "low_multi_depth": round(low_multi_depth, 2),
                "high_multi_impact": round(high_multi_impact, 2),
                "low_multi_impact": round(low_multi_impact, 2),
            },
            "integration_effect": {
                "high_integration_impact": round(high_int_impact, 2),
                "low_integration_impact": round(low_int_impact, 2),
            },
            "shallow_living_risk": shallow_living_risk,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 2),
            "duration_stats": duration_stats,
        }

    def get_depth_suggestion(self, activity: str = "", context: str = "") -> Dict[str, Any]:
        """Get suggestion for deepening an experience."""
        suggestions = [
            "Before you begin, take three breaths. Feel your feet on the ground. This is the threshold. Cross it consciously.",
            "Put the phone away. Not in your pocket. In another room. The thing you think you need to document is the thing you need to fully live first.",
            "Choose one sense and follow it. What do you hear that you never noticed? What do you smell? Sensory narrowing deepens everything.",
            "Ask yourself: What would make this unforgettable? Then do that. Unforgettable experiences are chosen, not accidental.",
            "After the experience ends, don't rush to the next thing. Sit with it for five minutes. Integration is where experience becomes memory.",
            "Notice when you're thinking about documenting instead of experiencing. That's the moment to put the device down and live.",
            "The best experiences are not the most expensive or exotic. They're the ones where you were most fully there. Presence is the ultimate luxury.",
            "If you find yourself thinking about work during leisure, you're not resting. You're just changing the subject. True rest requires full attention transfer.",
            "Before a meal, look at the food. Really look. Before a conversation, look at the person. Really look. The first minute determines the depth.",
            "The depth of an experience is inversely proportional to how much you're thinking about other experiences. One thing fully lived is worth more than ten things partially experienced.",
        ]

        return {
            "activity": activity or "general",
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "principle": "A life is not measured by the number of experiences it contains. It's measured by the depth of attention brought to each one. A single hour of genuine presence is worth more than a year of distraction. Most people die with a photo album full of shallow impressions and a heart full of unlived moments. Depth is a choice you make before the experience begins.",
        }

    def get_depth_score(self) -> int:
        """Calculate overall experience depth health (0-100)."""
        if not self._entries:
            return 25

        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_impact = sum(e.impact for e in self._entries) / len(self._entries)
        avg_richness = sum(e.richness for e in self._entries) / len(self._entries)
        avg_integration = sum(e.integration for e in self._entries) / len(self._entries)
        avg_multi = sum(e.multitasking for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_impact = sum(e.impact for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_impact = 0

        # Shallow living penalty
        shallow_penalty = 0
        if recent:
            recent_multi = sum(e.multitasking for e in recent) / len(recent)
            if recent_depth < 0.4 and recent_multi > 0.5:
                shallow_penalty = 20

        score = (avg_depth * 30) + (avg_impact * 25) + (avg_richness * 15) + (avg_integration * 15) + (recent_depth * 10) + (recent_impact * 5) - (avg_multi * 10) - shallow_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_impact"] = round(sum(e.impact for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_depth = sum(e.depth for e in recent) / len(recent)
                recent_multi = sum(e.multitasking for e in recent) / len(recent)
                self._stats["shallow_living_risk"] = recent_depth < 0.4 and recent_multi > 0.5
            else:
                self._stats["shallow_living_risk"] = True

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

    def _log_entry(self, entry: ExperienceEntry):
        try:
            with open(EXPERIENCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "depth": entry.depth,
                    "richness": entry.richness,
                    "impact": entry.impact,
                    "multitasking": entry.multitasking,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_em_instance: Optional[ExperienceMaximizer] = None
_em_lock = threading.Lock()


def get_experience_maximizer() -> ExperienceMaximizer:
    global _em_instance
    with _em_lock:
        if _em_instance is None:
            _em_instance = ExperienceMaximizer()
        return _em_instance
