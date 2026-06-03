"""
LOVE Sensory Awareness Trainer — Perception Intelligence (Modern AI Pattern)

Most people experience the world through concepts. This trainer:

1. SENSORY TRACKING
   - Record sensory awareness moments and their characteristics
   - Track sensory types (sight, sound, touch, taste, smell, proprioception)
   - Log vividness, presence, and pleasure of sensory experience

2. PATTERN ANALYSIS
   - Identify the user's sensory profile (numb, distracted, developing, vivid)
   - Find sensory patterns that create aliveness vs dullness
   - Detect chronic sensory numbing and its costs

3. SENSORY BUILDING
   - Suggest practices for increasing sensory vividness
   - Provide frameworks for mindful sensing
   - Recommend practices for sensory pleasure and curiosity

4. VIVID PERCEPTION CULTIVATION
   - Track the correlation between sensory awareness and aliveness
   - Alert when numbing is becoming the default
   - Celebrate moments of genuine, vivid perception

Architecture:
- record_sensory(experience, type, vividness, presence, pleasure): Log sensory
- get_sensory_stats(): Get sensory pattern analysis
- get_sensory_suggestion(capacity, context): Get suggestion
- get_sensory_score(): Calculate overall sensory health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "sensory_awareness_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SENSORY_LOG = DATA_DIR / "sensories.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SensoryEntry:
    """A tracked sensory awareness moment."""
    entry_id: str = ""
    experience: str = ""  # what was noticed
    sensory_type: str = ""  # sight, sound, touch, taste, smell, proprioception
    vividness: float = 0.0  # 0-1
    presence: float = 0.0  # 0-1
    pleasure: float = 0.0  # 0-1
    curiosity: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SensoryAwarenessTrainer:
    """
    Intelligent sensory awareness trainer with numbing detection and vivid perception cultivation.
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
            "avg_vividness": 0.0,
            "avg_presence": 0.0,
            "numbing_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_sensory(self, experience: str = "", sensory_type: str = "", vividness: float = 0.0, presence: float = 0.0, pleasure: float = 0.0, curiosity: float = 0.0, notes: str = "") -> SensoryEntry:
        """Record a sensory awareness moment."""
        entry_id = f"sns_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SensoryEntry(
            entry_id=entry_id,
            experience=experience or "unspecified",
            sensory_type=sensory_type or "sight",
            vividness=vividness,
            presence=presence,
            pleasure=pleasure,
            curiosity=curiosity,
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

    def get_sensory_stats(self) -> Dict[str, Any]:
        """Get sensory pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "vividness_sum": 0.0, "pleasure_sum": 0.0, "presence_sum": 0.0})
        for e in self._entries:
            by_type[e.sensory_type]["count"] += 1
            by_type[e.sensory_type]["vividness_sum"] += e.vividness
            by_type[e.sensory_type]["pleasure_sum"] += e.pleasure
            by_type[e.sensory_type]["presence_sum"] += e.presence

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_vividness": round(data["vividness_sum"] / count, 2),
                "avg_pleasure": round(data["pleasure_sum"] / count, 2),
                "avg_presence": round(data["presence_sum"] / count, 2),
            }

        # Vividness analysis
        high_viv = [e for e in self._entries if e.vividness > 0.7]
        low_viv = [e for e in self._entries if e.vividness < 0.4]
        if high_viv and low_viv:
            high_viv_pleas = sum(e.pleasure for e in high_viv) / len(high_viv)
            low_viv_pleas = sum(e.pleasure for e in low_viv) / len(low_viv)
            high_viv_pres = sum(e.presence for e in high_viv) / len(high_viv)
            low_viv_pres = sum(e.presence for e in low_viv) / len(low_viv)
        else:
            high_viv_pleas = 0
            low_viv_pleas = 0
            high_viv_pres = 0
            low_viv_pres = 0

        # Curiosity analysis
        high_cur = [e for e in self._entries if e.curiosity > 0.7]
        low_cur = [e for e in self._entries if e.curiosity < 0.4]
        if high_cur and low_cur:
            high_cur_viv = sum(e.vividness for e in high_cur) / len(high_cur)
            low_cur_viv = sum(e.vividness for e in low_cur) / len(low_cur)
        else:
            high_cur_viv = 0
            low_cur_viv = 0

        # Numbing risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_viv = sum(e.vividness for e in recent) / len(recent)
            recent_pres = sum(e.presence for e in recent) / len(recent)
            numbing_risk = recent_viv < 0.3 and recent_pres < 0.3
        else:
            numbing_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "vividness_impact": {
                "high_vividness_pleasure": round(high_viv_pleas, 2),
                "low_vividness_pleasure": round(low_viv_pleas, 2),
                "high_vividness_presence": round(high_viv_pres, 2),
                "low_vividness_presence": round(low_viv_pres, 2),
            },
            "curiosity_effect": {
                "high_curiosity_vividness": round(high_cur_viv, 2),
                "low_curiosity_vividness": round(low_cur_viv, 2),
            },
            "numbing_risk": numbing_risk,
            "avg_vividness": round(sum(e.vividness for e in self._entries) / len(self._entries), 2),
            "avg_presence": round(sum(e.presence for e in self._entries) / len(self._entries), 2),
        }

    def get_sensory_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get sensory suggestion."""
        suggestions = [
            "Most people don't taste their food. They eat it. They don't hear music. They play it. They don't feel the breeze. They tolerate it. Wake up your senses. They're dying of neglect.",
            "Pick one sense. Just one. Spend five minutes with it. If it's hearing, listen. Really listen. The hum of the fridge. The wind in the trees. Your own breath. The world is a symphony you usually ignore.",
            "Touch something with attention. Not to identify it. To feel it. The texture. The temperature. The weight. Your hands are sense organs. Use them for sensing, not just doing.",
            "Smell is the most neglected sense. And the most emotional. Scents bypass the thinking brain and go straight to memory and emotion. Notice smells. Name them. They'll unlock doors you forgot existed.",
            "Look at something as if you've never seen it before. Because in a way, you haven't. Every moment is new. The light is different. The angle is different. You are different. See it fresh.",
            "Savor one thing today. One bite. One sound. One touch. Give it your full attention. Not while doing something else. Just that. That's enough. That's practice. That's awakening.",
            "Your senses are portals to the present moment. You can't taste the future. You can't smell the past. Sensing happens now. Use your senses as anchors. Whenever you're lost, come back to what you can sense.",
            "Numbing is not just emotional. It's sensory. When you shut down feeling, you shut down sensing. When you open to sensation, you open to feeling. The path to aliveness is through the senses.",
            "The world is more vivid than you think. You're just not looking. The sky is not just blue. It's cerulean, azure, periwinkle. The coffee is not just hot. It's smoky, nutty, bitter. Look closer.",
            "Children are sensory beings. They touch everything. Smell everything. Stare at everything. We teach them not to. Be a child again. Touch the wall. Smell the flower. Stare at the cloud. Be alive."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One sense noticed. One smell named. One texture felt. One color seen. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A sensory walk. A mindful eating practice. A listening meditation. Medium training."
        else:
            capacity_note = "Good capacity. Deep sensory work. A systematic awakening of all senses. You have the strength to perceive vividly."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Sensory awareness is the foundation of presence. And presence is the foundation of aliveness. Most people don't perceive the world. They conceptualize it. They see a tree and think 'tree.' They don't see the bark. The way the light hits the leaves. The sway in the wind. They don't smell the sap. They don't feel the texture. They just think 'tree.' And they miss the tree. The work of sensory awareness training is about coming back to direct perception. About experiencing the world as it is, not as you think it is. About noticing the vividness that's always there but usually ignored. Because when you wake up your senses, you wake up your life. And the world becomes more beautiful, more interesting, and more alive than you ever imagined."
        }

    def get_sensory_score(self) -> int:
        """Calculate overall sensory health (0-100)."""
        if not self._entries:
            return 25

        avg_viv = sum(e.vividness for e in self._entries) / len(self._entries)
        avg_pres = sum(e.presence for e in self._entries) / len(self._entries)
        avg_pleas = sum(e.pleasure for e in self._entries) / len(self._entries)
        avg_cur = sum(e.curiosity for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_viv = sum(e.vividness for e in recent) / len(recent)
            recent_pres = sum(e.presence for e in recent) / len(recent)
        else:
            recent_viv = 0
            recent_pres = 0

        # Numbing penalty
        numbing_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_viv_30 = sum(e.vividness for e in last_30) / len(last_30)
            recent_pres_30 = sum(e.presence for e in last_30) / len(last_30)
            if recent_viv_30 < 0.3 and recent_pres_30 < 0.3:
                numbing_penalty = 15

        # Type variety
        unique_types = len(set(e.sensory_type for e in self._entries))

        score = (avg_viv * 25) + (avg_pres * 20) + (avg_pleas * 20) + (avg_cur * 15) + (recent_viv * 5) + (recent_pres * 5) + (unique_types * 2) - numbing_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_vividness"] = round(sum(e.vividness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_presence"] = round(sum(e.presence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_viv = sum(e.vividness for e in recent) / len(recent)
                recent_pres = sum(e.presence for e in recent) / len(recent)
                self._stats["numbing_risk"] = recent_viv < 0.3 and recent_pres < 0.3
            else:
                self._stats["numbing_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sensory_awareness_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sensory_awareness_trainer")

    def _log_entry(self, entry: SensoryEntry):
        try:
            with open(SENSORY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "experience": entry.experience,
                    "sensory_type": entry.sensory_type,
                    "vividness": entry.vividness,
                    "pleasure": entry.pleasure,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sensory_awareness_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sat_instance: Optional[SensoryAwarenessTrainer] = None
_sat_lock = threading.Lock()


def get_sensory_awareness_trainer() -> SensoryAwarenessTrainer:
    global _sat_instance
    with _sat_lock:
        if _sat_instance is None:
            _sat_instance = SensoryAwarenessTrainer()
        return _sat_instance
