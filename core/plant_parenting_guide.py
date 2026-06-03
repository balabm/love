"""
LOVE Plant Parenting Guide — Botanical Intelligence (Modern AI Pattern)

Most people kill plants through ignorance. This guide:

1. PLANT TRACKING
   - Record plant parenting moments and their characteristics
   - Track care types (watering, feeding, pruning, repotting, propagating, observing)
   - Log attentiveness, health, learning, and joy of plant care

2. PATTERN ANALYSIS
   - Identify the user's plant parent profile (neglectful, anxious, developing, nurturing)
   - Find care patterns that create thriving vs suffering plants
   - Detect chronic over/under-care and its costs

3. NURTURE BUILDING
   - Suggest practices for becoming a better plant parent
   - Provide frameworks for reading plant signals
   - Recommend practices for plant-specific care

4. BOTANICAL RELATIONSHIP CULTIVATION
   - Track the correlation between care quality and plant health
   - Alert when anxiety or neglect is harming the relationship
   - Celebrate moments of successful propagation and growth

Architecture:
- record_care(plant, type, attentiveness, health, learning, joy): Log care
- get_care_stats(): Get care pattern analysis
- get_care_suggestion(capacity, context): Get suggestion
- get_care_score(): Calculate overall care health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "plant_parenting_guide"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CARE_LOG = DATA_DIR / "cares.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CareEntry:
    """A tracked plant parenting moment."""
    entry_id: str = ""
    plant: str = ""  # what plant was cared for
    care_type: str = ""  # watering, feeding, pruning, repotting, propagating, observing
    attentiveness: float = 0.0  # 0-1
    health: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    observation: float = 0.0  # 0-1 did you observe before acting?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PlantParentingGuide:
    """
    Intelligent plant parenting guide with anxiety/neglect detection and botanical relationship cultivation.
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
            "avg_attentiveness": 0.0,
            "avg_health": 0.0,
            "care_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_care(self, plant: str = "", care_type: str = "", attentiveness: float = 0.0, health: float = 0.0, learning: float = 0.0, joy: float = 0.0, observation: float = 0.0, notes: str = "") -> CareEntry:
        """Record a plant parenting moment."""
        entry_id = f"car_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CareEntry(
            entry_id=entry_id,
            plant=plant or "unspecified",
            care_type=care_type or "watering",
            attentiveness=attentiveness,
            health=health,
            learning=learning,
            joy=joy,
            observation=observation,
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

    def get_care_stats(self) -> Dict[str, Any]:
        """Get care pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "attentiveness_sum": 0.0, "health_sum": 0.0, "joy_sum": 0.0})
        for e in self._entries:
            by_type[e.care_type]["count"] += 1
            by_type[e.care_type]["attentiveness_sum"] += e.attentiveness
            by_type[e.care_type]["health_sum"] += e.health
            by_type[e.care_type]["joy_sum"] += e.joy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_attentiveness": round(data["attentiveness_sum"] / count, 2),
                "avg_health": round(data["health_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Attentiveness analysis
        high_att = [e for e in self._entries if e.attentiveness > 0.7]
        low_att = [e for e in self._entries if e.attentiveness < 0.4]
        if high_att and low_att:
            high_att_joy = sum(e.joy for e in high_att) / len(high_att)
            low_att_joy = sum(e.joy for e in low_att) / len(low_att)
            high_att_hea = sum(e.health for e in high_att) / len(high_att)
            low_att_hea = sum(e.health for e in low_att) / len(low_att)
        else:
            high_att_joy = 0
            low_att_joy = 0
            high_att_hea = 0
            low_att_hea = 0

        # Observation analysis
        high_obs = [e for e in self._entries if e.observation > 0.7]
        low_obs = [e for e in self._entries if e.observation < 0.4]
        if high_obs and low_obs:
            high_obs_heal = sum(e.health for e in high_obs) / len(high_obs)
            low_obs_heal = sum(e.health for e in low_obs) / len(low_obs)
        else:
            high_obs_heal = 0
            low_obs_heal = 0

        # Care risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_att = sum(e.attentiveness for e in recent) / len(recent)
            recent_hea = sum(e.health for e in recent) / len(recent)
            care_risk = recent_att < 0.3 and recent_hea < 0.3
        else:
            care_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "attentiveness_impact": {
                "high_attentiveness_joy": round(high_att_joy, 2),
                "low_attentiveness_joy": round(low_att_joy, 2),
                "high_attentiveness_health": round(high_att_hea, 2),
                "low_attentiveness_health": round(low_att_hea, 2),
            },
            "observation_effect": {
                "high_observation_health": round(high_obs_heal, 2),
                "low_observation_health": round(low_obs_heal, 2),
            },
            "care_risk": care_risk,
            "avg_attentiveness": round(sum(e.attentiveness for e in self._entries) / len(self._entries), 2),
            "avg_health": round(sum(e.health for e in self._entries) / len(self._entries), 2),
        }

    def get_care_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get care suggestion."""
        suggestions = [
            "Plants don't need perfection. They need consistency. The person who waters on a schedule is better than the person who drowns them with love once a month. Small, regular care beats sporadic intensity.",
            "Look before you water. Is the soil dry? Are the leaves drooping? Or are you just worried? Most plant deaths are from overwatering, not underwatering. When in doubt, wait. Plants are resilient.",
            "Learn your plant's language. Yellow leaves might mean too much water. Brown tips might mean too little humidity. Leggy growth means not enough light. These are not failures. They're communications. Learn the language.",
            "Don't helicopter parent. Plants don't need you to fuss over them every day. They need you to understand their needs and meet them appropriately. Give them space. Let them do what they do best: grow.",
            "Start with easy plants. Pothos. Snake plants. ZZ plants. These are forgiving. They build confidence. Once you have success, branch out. Plant parenting is a skill. Skills develop gradually.",
            "Repot with courage. When roots are circling. When soil is exhausted. When the plant is top-heavy. Repotting is renewal. It's saying 'you've outgrown this. Here's more space.' That's love.",
            "Propagate. Share cuttings. Give baby plants to friends. This is the circle of plant life. The plant that gives also grows. And the friend who receives a plant receives a piece of you.",
            "Notice new growth. The unfurling leaf. The new shoot. The bud forming. These are victories. Evidence of your care. Of your patience. Of your attention. Celebrate them.",
            "Accept some losses. Not every plant will thrive in your space. Not every technique will work. This is not failure. It's data. Learn. Adjust. Try again. Or try something new.",
            "The person who keeps plants alive is not lucky. They're attentive. They're patient. They're consistent. And they're in relationship. With beings who don't speak. But who communicate beautifully. If you listen."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One plant checked. One watering done with observation. One new leaf noticed. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A repotting done. A propagation attempted. A plant problem diagnosed. Medium nurturing."
        else:
            capacity_note = "Good capacity. Deep plant parenting. A systematic practice of observation, learning, and care. You have the strength to be a green thumb."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Plant parenting is a practice of patience, observation, and consistency. Most people either neglect their plants or smother them with anxious attention. Neither works. Plants need understanding. They need you to learn their specific needs: how much light, how much water, what kind of soil, what humidity level. And they need you to be consistent in meeting those needs. The work of plant parenting guidance is about helping you develop the attentiveness and patience that plants require. About teaching you to read plant signals. About helping you find joy in the slow, steady process of nurturing life. And about understanding that the skills you develop as a plant parent—observation, patience, consistency, responsiveness—are the same skills that serve you in all your relationships. Because plants, like people, thrive when they're truly seen."
        }

    def get_care_score(self) -> int:
        """Calculate overall care health (0-100)."""
        if not self._entries:
            return 25

        avg_att = sum(e.attentiveness for e in self._entries) / len(self._entries)
        avg_hea = sum(e.health for e in self._entries) / len(self._entries)
        avg_learn = sum(e.learning for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_obs = sum(e.observation for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_att = sum(e.attentiveness for e in recent) / len(recent)
            recent_hea = sum(e.health for e in recent) / len(recent)
        else:
            recent_att = 0
            recent_hea = 0

        # Care risk penalty
        care_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_att_30 = sum(e.attentiveness for e in last_30) / len(last_30)
            recent_hea_30 = sum(e.health for e in last_30) / len(last_30)
            if recent_att_30 < 0.3 and recent_hea_30 < 0.3:
                care_penalty = 15

        # Type variety
        unique_types = len(set(e.care_type for e in self._entries))

        score = (avg_att * 25) + (avg_hea * 20) + (avg_learn * 10) + (avg_joy * 15) + (avg_obs * 10) + (recent_att * 5) + (recent_hea * 5) + (unique_types * 2) - care_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_attentiveness"] = round(sum(e.attentiveness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_health"] = round(sum(e.health for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_att = sum(e.attentiveness for e in recent) / len(recent)
                recent_hea = sum(e.health for e in recent) / len(recent)
                self._stats["care_risk"] = recent_att < 0.3 and recent_hea < 0.3
            else:
                self._stats["care_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.plant_parenting_guide")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.plant_parenting_guide")

    def _log_entry(self, entry: CareEntry):
        try:
            with open(CARE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "plant": entry.plant,
                    "care_type": entry.care_type,
                    "attentiveness": entry.attentiveness,
                    "health": entry.health,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.plant_parenting_guide")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ppg_instance: Optional[PlantParentingGuide] = None
_ppg_lock = threading.Lock()


def get_plant_parenting_guide() -> PlantParentingGuide:
    global _ppg_instance
    with _ppg_lock:
        if _ppg_instance is None:
            _ppg_instance = PlantParentingGuide()
        return _ppg_instance
