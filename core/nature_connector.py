"""
LOVE Nature Connector — Biophilia Intelligence (Modern AI Pattern)

Most modern disconnection comes from forgetting we are nature. This connector:

1. NATURE TRACKING
   - Record nature interactions and their characteristics
   - Track nature types (forest, water, mountain, garden, sky, wildlife)
   - Log wellbeing outcomes and their effects on mental health

2. PATTERN ANALYSIS
   - Identify the user's nature profile (indoor, occasional, regular, immersed)
   - Find nature exposure patterns that create wellbeing benefits
   - Detect nature deficit and its consequences

3. CONNECTION BUILDING
   - Suggest nature interactions matched to current context and capacity
   - Provide noticing and grounding exercises
   - Recommendation regular exposure practices

4. BIOPHILIA CULTIVATION
   - Track the correlation between nature time and wellbeing
   - Alert when disconnection is becoming chronic
   - Celebrate moments of genuine awe

Architecture:
- record_interaction(environment, type, duration, wellbeing): Log interaction
- get_nature_stats(): Get nature pattern analysis
- get_nature_suggestion(context, capacity, season): Get suggestion
- get_nature_score(): Calculate overall nature health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "nature_connector"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NATURE_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class NatureEntry:
    """A tracked nature entry."""
    entry_id: str = ""
    environment: str = ""  # forest, water, mountain, garden, sky, wildlife
    interaction_type: str = ""  # walking, sitting, observing, gardening, swimming
    duration: float = 0.0  # minutes
    wellbeing_before: float = 0.5  # 0-1
    wellbeing_after: float = 0.5  # 0-1
    awe_experienced: bool = False
    season: str = ""  # spring, summer, fall, winter
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class NatureConnector:
    """
    Intelligent nature connector with biophilia tracking and deficit detection.
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
            "avg_duration": 0.0,
            "avg_wellbeing_change": 0.0,
            "deficit_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, environment: str = "", interaction_type: str = "", duration: float = 0.0, wellbeing_before: float = 0.5, wellbeing_after: float = 0.5, awe_experienced: bool = False, season: str = "", notes: str = "") -> NatureEntry:
        """Record a nature entry."""
        entry_id = f"nat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = NatureEntry(
            entry_id=entry_id,
            environment=environment or "garden",
            interaction_type=interaction_type or "walking",
            duration=duration,
            wellbeing_before=wellbeing_before,
            wellbeing_after=wellbeing_after,
            awe_experienced=awe_experienced,
            season=season or "spring",
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

    def get_nature_stats(self) -> Dict[str, Any]:
        """Get nature pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Environment analysis
        by_env = defaultdict(lambda: {"count": 0, "duration_sum": 0.0, "wellbeing_sum": 0.0, "awe_count": 0})
        for e in self._entries:
            by_env[e.environment]["count"] += 1
            by_env[e.environment]["duration_sum"] += e.duration
            by_env[e.environment]["wellbeing_sum"] += e.wellbeing_after - e.wellbeing_before
            if e.awe_experienced:
                by_env[e.environment]["awe_count"] += 1

        env_stats = {}
        for env, data in by_env.items():
            count = data["count"]
            env_stats[env] = {
                "count": count,
                "avg_duration": round(data["duration_sum"] / count, 1),
                "avg_wellbeing_change": round(data["wellbeing_sum"] / count, 2),
                "awe_rate": round(data["awe_count"] / count, 2),
            }

        best_env = max(env_stats.items(), key=lambda x: x[1]["avg_wellbeing_change"]) if env_stats else ("", {})

        # Duration analysis
        long_dur = [e for e in self._entries if e.duration > 60]
        short_dur = [e for e in self._entries if e.duration < 15]
        if long_dur and short_dur:
            long_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in long_dur) / len(long_dur)
            short_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in short_dur) / len(short_dur)
            long_awe = sum(1 for e in long_dur if e.awe_experienced) / len(long_dur)
            short_awe = sum(1 for e in short_dur if e.awe_experienced) / len(short_dur)
        else:
            long_wellbeing = 0
            short_wellbeing = 0
            long_awe = 0
            short_awe = 0

        # Awe analysis
        awe = [e for e in self._entries if e.awe_experienced]
        no_awe = [e for e in self._entries if not e.awe_experienced]
        if awe and no_awe:
            awe_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in awe) / len(awe)
            no_awe_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in no_awe) / len(no_awe)
        else:
            awe_wellbeing = 0
            no_awe_wellbeing = 0

        # Deficit detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_duration = sum(e.duration for e in recent) / len(recent)
            recent_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in recent) / len(recent)
            deficit_risk = recent_duration < 15 or recent_wellbeing < 0
        else:
            deficit_risk = True

        # Season analysis
        by_season = defaultdict(lambda: {"count": 0, "wellbeing_sum": 0.0})
        for e in self._entries:
            by_season[e.season]["count"] += 1
            by_season[e.season]["wellbeing_sum"] += e.wellbeing_after - e.wellbeing_before

        season_stats = {}
        for s, data in by_season.items():
            count = data["count"]
            season_stats[s] = {
                "count": count,
                "avg_wellbeing_change": round(data["wellbeing_sum"] / count, 2),
            }

        # Recent trend
        if recent:
            recent_awe = sum(1 for e in recent if e.awe_experienced) / len(recent)
        else:
            recent_awe = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_duration = sum(e.duration for e in older) / len(older)
            older_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in older) / len(older)
            duration_trend = (sum(e.duration for e in recent) / len(recent)) - older_duration if recent else 0
            wellbeing_trend = (sum(e.wellbeing_after - e.wellbeing_before for e in recent) / len(recent)) - older_wellbeing if recent else 0
        else:
            duration_trend = 0
            wellbeing_trend = 0

        return {
            "total_entries": len(self._entries),
            "environment_stats": env_stats,
            "best_environment": best_env[0],
            "duration_impact": {
                "long_duration_wellbeing": round(long_wellbeing, 2),
                "short_duration_wellbeing": round(short_wellbeing, 2),
                "long_awe_rate": round(long_awe, 2),
                "short_awe_rate": round(short_awe, 2),
            },
            "awe_impact": {
                "awe_wellbeing_change": round(awe_wellbeing, 2),
                "no_awe_wellbeing_change": round(no_awe_wellbeing, 2),
            },
            "deficit_risk": deficit_risk,
            "season_stats": season_stats,
            "avg_duration": round(sum(e.duration for e in self._entries) / len(self._entries), 1),
            "avg_wellbeing_change": round(sum(e.wellbeing_after - e.wellbeing_before for e in self._entries) / len(self._entries), 2),
            "duration_trend": round(duration_trend, 1),
            "wellbeing_trend": round(wellbeing_trend, 2),
            "recent_awe_rate": round(recent_awe, 2),
        }

    def get_nature_suggestion(self, context: str = "", capacity: float = 0.5, season: str = "") -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "urban": [
                "Find one tree. Sit under it. 10 minutes. Cities have nature. You just have to look.",
                "Visit a park. Any park. Walk slowly. Notice what's growing. Even dandelions are life.",
                "Look up. Clouds. Stars. Moon. The sky is nature. It's always there. Even in the city.",
            ],
            "suburban": [
                "Walk a different route. Notice the gardens. The birds. The changing trees. Suburbs are full of life.",
                "Start a small garden. Herbs. Tomatoes. Flowers. Growing things connects you to cycles.",
                "Find a trail. Most suburbs have them. Hidden creeks. Woods between developments. Explore.",
            ],
            "rural": [
                "You have access. Use it. Walk the land. Know it. The creek. The oak. The meadow. Name them.",
                "Sit outside at dawn. Before the world wakes. The birds. The light. The quiet. This is medicine.",
                "Learn the species. Birds. Plants. Insects. Knowing names deepens connection. You're not just visiting. You're home.",
            ],
            "indoor": [
                "Houseplants. Start with one. A succulent. A pothos. Care for it. Watch it grow.",
                "Nature documentaries. Not the same, but not nothing. BBC Earth. Planet Earth. Awe is transferable.",
                "Open a window. Fresh air. Bird sounds. Natural light. The simplest interventions matter.",
            ],
            "general": [
                "Nature is not a place. It's a relationship. You're in it right now. The air you breathe. The water you drink.",
                "20 minutes. That's the minimum effective dose. 20 minutes outside. Any outside. It changes your brain.",
                "Leave the phone. Nature requires attention. Attention requires absence of distraction. Be there. Fully.",
            ],
        }

        selected = suggestions.get(context, suggestions["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. 5 minutes. Stand outside. Breathe. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. 20-minute walk. Find green. Any green."
        else:
            capacity_note = "Good capacity. Half-day immersion. Hike. Camp. Garden. Deep connection requires time."

        return {
            "context": context or "general",
            "capacity": capacity,
            "season": season or "current",
            "suggestion": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most people think nature is a luxury. Something you visit on vacation. It's not. Nature is a necessity. Your nervous system evolved outdoors. Your brain needs natural light, fractal patterns, and fresh air. Without them, you become anxious, depressed, and scattered. Nature is not entertainment. It's maintenance. For your body, your mind, and your soul. The cost of disconnection is higher than you think.",
        }

    def get_nature_score(self) -> int:
        """Calculate overall nature health (0-100)."""
        if not self._entries:
            return 20

        # Duration and wellbeing change
        avg_duration = sum(e.duration for e in self._entries) / len(self._entries)
        avg_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in self._entries) / len(self._entries)

        # Awe rate
        awe_rate = sum(1 for e in self._entries if e.awe_experienced) / len(self._entries)

        # Environment variety
        unique_envs = len(set(e.environment for e in self._entries))

        # Season variety
        unique_seasons = len(set(e.season for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_duration = sum(e.duration for e in recent) / len(recent)
            recent_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in recent) / len(recent)
            recent_awe = sum(1 for e in recent if e.awe_experienced) / len(recent)
        else:
            recent_duration = 0
            recent_wellbeing = 0
            recent_awe = 0

        # Deficit penalty
        deficit_penalty = 0
        if recent:
            recent_dur = sum(e.duration for e in recent) / len(recent)
            recent_wb = sum(e.wellbeing_after - e.wellbeing_before for e in recent) / len(recent)
            if recent_dur < 15 or recent_wb < 0:
                deficit_penalty = 15

        score = (avg_duration / 2) + (avg_wellbeing * 25) + (awe_rate * 20) + (unique_envs * 3) + (unique_seasons * 3) + (recent_duration / 2) + (recent_wellbeing * 15) + (recent_awe * 10) - deficit_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_duration"] = round(sum(e.duration for e in self._entries) / len(self._entries), 1)
            self._stats["avg_wellbeing_change"] = round(sum(e.wellbeing_after - e.wellbeing_before for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if recent:
                recent_duration = sum(e.duration for e in recent) / len(recent)
                recent_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in recent) / len(recent)
                self._stats["deficit_risk"] = recent_duration < 15 or recent_wellbeing < 0
            else:
                self._stats["deficit_risk"] = True

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.nature_connector")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.nature_connector")

    def _log_entry(self, entry: NatureEntry):
        try:
            with open(NATURE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "environment": entry.environment,
                    "interaction_type": entry.interaction_type,
                    "duration": entry.duration,
                    "wellbeing_before": entry.wellbeing_before,
                    "wellbeing_after": entry.wellbeing_after,
                    "awe_experienced": entry.awe_experienced,
                    "season": entry.season,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.nature_connector")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_nc_instance: Optional[NatureConnector] = None
_nc_lock = threading.Lock()


def get_nature_connector() -> NatureConnector:
    global _nc_instance
    with _nc_lock:
        if _nc_instance is None:
            _nc_instance = NatureConnector()
        return _nc_instance
