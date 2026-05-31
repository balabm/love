"""
LOVE Home Environment Optimizer — Spatial Intelligence (Modern AI Pattern)

Most people live in spaces that drain rather than restore. This optimizer:

1. ENVIRONMENT TRACKING
   - Record environmental assessments and their characteristics
   - Track environment types (sleep, work, social, restorative, creative)
   - Log comfort, functionality, beauty, and energy of spaces

2. PATTERN ANALYSIS
   - Identify the user's environment profile (nurturing, cluttered, sterile, chaotic)
   - Find environmental patterns that support or hinder wellbeing
   - Detect environmental stress and its sources

3. ENVIRONMENT OPTIMIZATION
   - Suggest changes matched to current capacity and constraints
   - Provide frameworks for decluttering and organizing
   - Recommend sensory adjustments (light, sound, scent, texture)

4. SPACE CULTIVATION
   - Track the correlation between environment and mood/productivity
   - Alert when space is becoming a source of stress
   - Celebrate moments of genuine environmental restoration

Architecture:
- record_assessment(space, type, comfort, functionality, beauty): Log assessment
- get_environment_stats(): Get environment pattern analysis
- get_optimization_suggestion(capacity, context): Get suggestion
- get_environment_score(): Calculate overall environment health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "home_environment_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENVIRONMENT_LOG = DATA_DIR / "assessments.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EnvironmentEntry:
    """A tracked environmental assessment."""
    entry_id: str = ""
    space: str = ""  # which space
    environment_type: str = ""  # sleep, work, social, restorative, creative
    comfort: float = 0.5  # 0-1
    functionality: float = 0.5  # 0-1
    beauty: float = 0.0  # 0-1
    energy: float = 0.0  # 0-1 does it energize or drain?
    calm: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HomeEnvironmentOptimizer:
    """
    Intelligent home environment optimizer with space detection and restoration cultivation.
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
            "avg_comfort": 0.0,
            "avg_energy": 0.0,
            "environmental_stress": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_assessment(self, space: str = "", environment_type: str = "", comfort: float = 0.5, functionality: float = 0.5, beauty: float = 0.0, energy: float = 0.0, calm: float = 0.0, notes: str = "") -> EnvironmentEntry:
        """Record an environmental assessment."""
        entry_id = f"env_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EnvironmentEntry(
            entry_id=entry_id,
            space=space or "unspecified",
            environment_type=environment_type or "general",
            comfort=comfort,
            functionality=functionality,
            beauty=beauty,
            energy=energy,
            calm=calm,
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

    def get_environment_stats(self) -> Dict[str, Any]:
        """Get environment pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Space analysis
        by_space = defaultdict(lambda: {"count": 0, "comfort_sum": 0.0, "functionality_sum": 0.0, "beauty_sum": 0.0})
        for e in self._entries:
            by_space[e.space]["count"] += 1
            by_space[e.space]["comfort_sum"] += e.comfort
            by_space[e.space]["functionality_sum"] += e.functionality
            by_space[e.space]["beauty_sum"] += e.beauty

        space_stats = {}
        for s, data in by_space.items():
            count = data["count"]
            space_stats[s] = {
                "count": count,
                "avg_comfort": round(data["comfort_sum"] / count, 2),
                "avg_functionality": round(data["functionality_sum"] / count, 2),
                "avg_beauty": round(data["beauty_sum"] / count, 2),
            }

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "energy_sum": 0.0, "calm_sum": 0.0})
        for e in self._entries:
            by_type[e.environment_type]["count"] += 1
            by_type[e.environment_type]["energy_sum"] += e.energy
            by_type[e.environment_type]["calm_sum"] += e.calm

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_energy": round(data["energy_sum"] / count, 2),
                "avg_calm": round(data["calm_sum"] / count, 2),
            }

        # Comfort analysis
        high_comfort = [e for e in self._entries if e.comfort > 0.7]
        low_comfort = [e for e in self._entries if e.comfort < 0.4]
        if high_comfort and low_comfort:
            high_comfort_energy = sum(e.energy for e in high_comfort) / len(high_comfort)
            low_comfort_energy = sum(e.energy for e in low_comfort) / len(low_comfort)
            high_comfort_calm = sum(e.calm for e in high_comfort) / len(high_comfort)
            low_comfort_calm = sum(e.calm for e in low_comfort) / len(low_comfort)
        else:
            high_comfort_energy = 0
            low_comfort_energy = 0
            high_comfort_calm = 0
            low_comfort_calm = 0

        # Beauty analysis
        high_beauty = [e for e in self._entries if e.beauty > 0.7]
        low_beauty = [e for e in self._entries if e.beauty < 0.4]
        if high_beauty and low_beauty:
            high_beauty_calm = sum(e.calm for e in high_beauty) / len(high_beauty)
            low_beauty_calm = sum(e.calm for e in low_beauty) / len(low_beauty)
        else:
            high_beauty_calm = 0
            low_beauty_calm = 0

        # Environmental stress detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_comfort = sum(e.comfort for e in recent) / len(recent)
            recent_energy = sum(e.energy for e in recent) / len(recent)
            environmental_stress = recent_comfort < 0.4 and recent_energy < 0.3
        else:
            environmental_stress = False

        return {
            "total_entries": len(self._entries),
            "space_stats": space_stats,
            "type_stats": type_stats,
            "comfort_impact": {
                "high_comfort_energy": round(high_comfort_energy, 2),
                "low_comfort_energy": round(low_comfort_energy, 2),
                "high_comfort_calm": round(high_comfort_calm, 2),
                "low_comfort_calm": round(low_comfort_calm, 2),
            },
            "beauty_effect": {
                "high_beauty_calm": round(high_beauty_calm, 2),
                "low_beauty_calm": round(low_beauty_calm, 2),
            },
            "environmental_stress": environmental_stress,
            "avg_comfort": round(sum(e.comfort for e in self._entries) / len(self._entries), 2),
            "avg_energy": round(sum(e.energy for e in self._entries) / len(self._entries), 2),
        }

    def get_optimization_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get optimization suggestion."""
        suggestions = [
            "Clear one surface. Just one. The desk. The table. The counter. Clarity in the environment creates clarity in the mind. Start with one.",
            "Add one living thing. A plant. Flowers. Fresh herbs. Life in the space changes the energy. It's a small thing. It makes a big difference.",
            "Fix the light. Open curtains. Add a lamp. Change the bulb. Light affects mood more than almost anything. Dark spaces create dark moods.",
            "Create a dedicated rest zone. Not a workspace. Not an eating space. A place for rest. A chair by the window. A corner with pillows. Somewhere that says: here, you can stop.",
            "Remove one thing that drains you. The pile of mail. The broken item. The gift you don't like. Your environment should support you. Not remind you of obligations.",
            "Add scent. A candle. Essential oil. Fresh air. Scent is the fastest route to the emotional brain. One good smell can change a whole room.",
            "Make your bed. It's a two-minute investment that pays all day. The bed made says: someone lives here with intention. That someone is you.",
            "Create a transition ritual. When you enter, take off your shoes. When you work, sit in a specific chair. When you rest, change the lighting. Spaces should have purposes.",
            "Your home is not a storage unit. It's a living space. If you haven't used it in a year, let it go. The space you free up is more valuable than the thing you keep.",
            "The space you live in is the container for your life. Make it beautiful. Make it functional. Make it yours. Your environment either supports your wellbeing or undermines it. Choose.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Make the bed. Open a window. One small change. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Clear a surface. Add a plant. Adjust lighting. Medium investment in your space."
        else:
            capacity_note = "Good capacity. A major reorganization. A design change. A full space transformation. You have the energy to create a real sanctuary."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Your physical environment is not neutral. It either supports you or it drains you. Every object in your space either adds energy or takes it. Every arrangement either creates flow or creates friction. Most people underestimate the power of their environment because it's invisible. It's just there. But it's shaping your mood, your productivity, your sleep, your creativity, every single day. The spaces we live in are the containers for our lives. And like any container, they should be designed for what they hold. Your life deserves a beautiful container.",
        }

    def get_environment_score(self) -> int:
        """Calculate overall environment health (0-100)."""
        if not self._entries:
            return 25

        avg_comfort = sum(e.comfort for e in self._entries) / len(self._entries)
        avg_functionality = sum(e.functionality for e in self._entries) / len(self._entries)
        avg_beauty = sum(e.beauty for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy for e in self._entries) / len(self._entries)
        avg_calm = sum(e.calm for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_comfort = sum(e.comfort for e in recent) / len(recent)
            recent_energy = sum(e.energy for e in recent) / len(recent)
        else:
            recent_comfort = 0
            recent_energy = 0

        # Environmental stress penalty
        stress_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_comfort_30 = sum(e.comfort for e in last_30) / len(last_30)
            recent_energy_30 = sum(e.energy for e in last_30) / len(last_30)
            if recent_comfort_30 < 0.4 and recent_energy_30 < 0.3:
                stress_penalty = 15

        # Space variety
        unique_spaces = len(set(e.space for e in self._entries))

        score = (avg_comfort * 25) + (avg_functionality * 15) + (avg_beauty * 15) + (avg_energy * 15) + (avg_calm * 10) + (recent_comfort * 10) + (recent_energy * 5) + (unique_spaces * 2) - stress_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_comfort"] = round(sum(e.comfort for e in self._entries) / len(self._entries), 2)
            self._stats["avg_energy"] = round(sum(e.energy for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_comfort = sum(e.comfort for e in recent) / len(recent)
                recent_energy = sum(e.energy for e in recent) / len(recent)
                self._stats["environmental_stress"] = recent_comfort < 0.4 and recent_energy < 0.3
            else:
                self._stats["environmental_stress"] = False

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

    def _log_entry(self, entry: EnvironmentEntry):
        try:
            with open(ENVIRONMENT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "space": entry.space,
                    "environment_type": entry.environment_type,
                    "comfort": entry.comfort,
                    "energy": entry.energy,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_heo_instance: Optional[HomeEnvironmentOptimizer] = None
_heo_lock = threading.Lock()


def get_home_environment_optimizer() -> HomeEnvironmentOptimizer:
    global _heo_instance
    with _heo_lock:
        if _heo_instance is None:
            _heo_instance = HomeEnvironmentOptimizer()
        return _heo_instance
