"""
LOVE Environment Curator — Context Intelligence (Modern AI Pattern)

Most behavior is shaped by environment, not willpower. This curator:

1. ENVIRONMENT TRACKING
   - Record environment assessments and their effects on behavior
   - Track environmental changes and their impact on habits, mood, and productivity
   - Log friction points and enablers in current spaces

2. PATTERN ANALYSIS
   - Identify the user's environmental profile (minimalist, maximalist, natural, urban, social, solitary)
   - Find which environmental factors most affect which behaviors
   - Detect environment-behavior mismatches

3. CURATION DESIGN
   - Suggest environmental modifications for specific goals
   - Provide space-design principles matched to user type
   - Recommend object placement, lighting, sound, and scent

4. IMPLEMENTATION SUPPORT
   - Track the correlation between environmental changes and behavior change
   - Alert when environment is working against goals
   - Celebrate environmental wins

Architecture:
- record_environment(space, factor, effect, behavior): Log environment
- get_environment_stats(): Get environment pattern analysis
- get_curation_suggestion(goal, space_type): Get design plan
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
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "environment_curator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENV_LOG = DATA_DIR / "environments.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EnvironmentEntry:
    """A tracked environment entry."""
    entry_id: str = ""
    space: str = ""  # bedroom, office, kitchen, living_room, gym, outdoors, commute
    factor: str = ""  # lighting, clutter, noise, temperature, objects, people, scent, layout
    effect: float = 0.0  # -1 to 1
    behavior_supported: str = ""  # what behavior this affects
    behavior_change: float = 0.0  # how much behavior changed
    modification_made: str = ""  # what was changed
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EnvironmentCurator:
    """
    Intelligent environment curator with space analysis and behavioral design.
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
            "avg_effect": 0.0,
            "best_space": "",
            "worst_factor": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_environment(self, space: str = "", factor: str = "", effect: float = 0.0, behavior_supported: str = "", behavior_change: float = 0.0, modification: str = "", notes: str = "") -> EnvironmentEntry:
        """Record an environment entry."""
        entry_id = f"env_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EnvironmentEntry(
            entry_id=entry_id,
            space=space or "general",
            factor=factor or "general",
            effect=effect,
            behavior_supported=behavior_supported,
            behavior_change=behavior_change,
            modification_made=modification,
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
        by_space = defaultdict(lambda: {"count": 0, "effect_sum": 0.0, "behavior_change_sum": 0.0})
        for e in self._entries:
            by_space[e.space]["count"] += 1
            by_space[e.space]["effect_sum"] += e.effect
            by_space[e.space]["behavior_change_sum"] += e.behavior_change

        space_stats = {}
        for s, data in by_space.items():
            count = data["count"]
            space_stats[s] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
                "avg_behavior_change": round(data["behavior_change_sum"] / count, 2),
            }

        best_space = max(space_stats.items(), key=lambda x: x[1]["avg_effect"]) if space_stats else ("", {})

        # Factor analysis
        by_factor = defaultdict(lambda: {"count": 0, "effect_sum": 0.0, "behavior_change_sum": 0.0})
        for e in self._entries:
            by_factor[e.factor]["count"] += 1
            by_factor[e.factor]["effect_sum"] += e.effect
            by_factor[e.factor]["behavior_change_sum"] += e.behavior_change

        factor_stats = {}
        for f, data in by_factor.items():
            count = data["count"]
            factor_stats[f] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
                "avg_behavior_change": round(data["behavior_change_sum"] / count, 2),
            }

        worst_factor = min(factor_stats.items(), key=lambda x: x[1]["avg_effect"]) if factor_stats else ("", {})

        # Modification effectiveness
        modified = [e for e in self._entries if e.modification_made]
        if modified:
            avg_mod_effect = sum(e.behavior_change for e in modified) / len(modified)
        else:
            avg_mod_effect = 0

        # Behavior correlation
        by_behavior = defaultdict(lambda: {"count": 0, "effect_sum": 0.0})
        for e in self._entries:
            if e.behavior_supported:
                by_behavior[e.behavior_supported]["count"] += 1
                by_behavior[e.behavior_supported]["effect_sum"] += e.effect

        behavior_stats = {}
        for b, data in by_behavior.items():
            count = data["count"]
            behavior_stats[b] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
            }

        return {
            "total_entries": len(self._entries),
            "space_stats": space_stats,
            "best_space": best_space[0],
            "factor_stats": factor_stats,
            "worst_factor": worst_factor[0],
            "avg_mod_effectiveness": round(avg_mod_effect, 2),
            "behavior_stats": behavior_stats,
            "avg_effect": round(sum(e.effect for e in self._entries) / len(self._entries), 2),
        }

    def get_curation_suggestion(self, goal: str = "", space_type: str = "", budget: str = "low") -> Dict[str, Any]:
        """Get design plan."""
        modifications = {
            "focus": {
                "low": [
                    "Clear desk to only essential items",
                    "Face a wall or window, not the room entrance",
                    "Use noise-canceling headphones or brown noise",
                    "Put phone in another room",
                ],
                "medium": [
                    "Add a second monitor to reduce window-switching",
                    "Invest in a comfortable, supportive chair",
                    "Use a desk lamp with adjustable color temperature",
                    "Add a plant (studies show 15% productivity boost)",
                ],
                "high": [
                    "Create a dedicated office space with a door",
                    "Install sound-dampening panels",
                    "Upgrade to a sit-stand desk",
                    "Add air purifier and optimal lighting system",
                ],
            },
            "sleep": {
                "low": [
                    "Remove all screens from bedroom",
                    "Use blackout curtains or eye mask",
                    "Set thermostat to 65-68F (18-20C)",
                    "Keep phone charger in another room",
                ],
                "medium": [
                    "Invest in quality mattress or topper",
                    "Add white noise machine",
                    "Use lavender spray or essential oil diffuser",
                    "Get weighted blanket",
                ],
                "high": [
                    "Upgrade to temperature-regulating mattress",
                    "Install circadian lighting system",
                    "Soundproof bedroom walls",
                    "Create dedicated sleep sanctuary (no work items)",
                ],
            },
            "creativity": {
                "low": [
                    "Change one thing in your space (move desk, new art)",
                    "Add natural elements (plant, stones, wood)",
                    "Play instrumental music at low volume",
                    "Work from a different location once a week",
                ],
                "medium": [
                    "Create a dedicated creative corner with supplies visible",
                    "Add colorful or inspiring visual elements",
                    "Use scented candles or incense for ritual",
                    "Get a comfortable creative chair (different from work chair)",
                ],
                "high": [
                    "Design a full creative studio with zones for different activities",
                    "Install adjustable lighting for different creative modes",
                    "Add inspiration wall with rotating images/quotes",
                    "Create sensory variety (textures, colors, sounds)",
                ],
            },
            "social": {
                "low": [
                    "Create a conversation corner (two chairs facing each other)",
                    "Remove TV as the room's focal point",
                    "Add board games or cards to visible storage",
                    "Use warm, dim lighting for evenings",
                ],
                "medium": [
                    "Add comfortable seating arranged for conversation",
                    "Create a shared cooking or prep space",
                    "Add music system for ambient sound",
                    "Set up a beverage station for hosting",
                ],
                "high": [
                    "Design open-concept gathering space",
                    "Add outdoor seating or fire pit",
                    "Create themed hosting areas (dining, lounge, activity)",
                    "Install smart lighting for different social moods",
                ],
            },
        }

        goal_mods = modifications.get(goal, modifications["focus"])
        budget_mods = goal_mods.get(budget, goal_mods["low"])

        principles = [
            "Environment is the invisible hand that shapes behavior.",
            "Make the good choice the easy choice. Make the bad choice hard.",
            "Your space should reflect who you're becoming, not who you were.",
            "Small environmental changes often outperform big willpower efforts.",
        ]

        return {
            "goal": goal or "general",
            "space_type": space_type or "general",
            "budget": budget,
            "modifications": random.sample(budget_mods, min(2, len(budget_mods))),
            "principles": random.choice(principles),
            "quick_win": "Change one thing in your primary space today. Just one. Notice the effect.",
        }

    def get_environment_score(self) -> int:
        """Calculate overall environment health (0-100)."""
        if not self._entries:
            return 40

        # Positive effect rate
        positive = sum(1 for e in self._entries if e.effect > 0)
        positive_rate = positive / len(self._entries)

        # Behavior change effectiveness
        avg_behavior_change = sum(e.behavior_change for e in self._entries) / len(self._entries)

        # Modification effectiveness
        modified = [e for e in self._entries if e.modification_made]
        if modified:
            mod_effectiveness = sum(e.behavior_change for e in modified) / len(modified)
        else:
            mod_effectiveness = 0

        # Space variety
        unique_spaces = len(set(e.space for e in self._entries))

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_effect = sum(e.effect for e in recent) / len(recent)
        else:
            recent_effect = 0

        score = (positive_rate * 25) + (avg_behavior_change * 20) + (mod_effectiveness * 15) + (unique_spaces * 3) + (recent_effect * 15) + 10
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_effect"] = round(sum(e.effect for e in self._entries) / len(self._entries), 2)

            by_space = defaultdict(lambda: {"effect": 0.0, "count": 0})
            for e in self._entries:
                by_space[e.space]["effect"] += e.effect
                by_space[e.space]["count"] += 1
            if by_space:
                best = max(by_space.items(), key=lambda x: x[1]["effect"] / max(1, x[1]["count"]))
                self._stats["best_space"] = best[0]

            by_factor = defaultdict(lambda: {"effect": 0.0, "count": 0})
            for e in self._entries:
                by_factor[e.factor]["effect"] += e.effect
                by_factor[e.factor]["count"] += 1
            if by_factor:
                worst = min(by_factor.items(), key=lambda x: x[1]["effect"] / max(1, x[1]["count"]))
                self._stats["worst_factor"] = worst[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.environment_curator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.environment_curator")

    def _log_entry(self, entry: EnvironmentEntry):
        try:
            with open(ENV_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "space": entry.space,
                    "factor": entry.factor,
                    "effect": entry.effect,
                    "behavior": entry.behavior_supported,
                    "behavior_change": entry.behavior_change,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.environment_curator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ec_instance: Optional[EnvironmentCurator] = None
_ec_lock = threading.Lock()


def get_environment_curator() -> EnvironmentCurator:
    global _ec_instance
    with _ec_lock:
        if _ec_instance is None:
            _ec_instance = EnvironmentCurator()
        return _ec_instance
