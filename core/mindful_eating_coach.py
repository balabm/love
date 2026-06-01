"""
LOVE Mindful Eating Coach — Nourishment Intelligence (Modern AI Pattern)

Most people eat unconsciously. This coach:

1. EATING TRACKING
   - Record mindful eating moments and their characteristics
   - Track eating types (meal, snack, emotional, social, rushed, celebratory)
   - Log awareness, satisfaction, hunger accuracy, and digestion comfort

2. PATTERN ANALYSIS
   - Identify the user's eating profile (unconscious, distracted, developing, mindful)
   - Find eating patterns that create nourishment vs distress
   - Detect chronic mindless eating and its costs

3. MINDFULNESS BUILDING
   - Suggest practices for eating with full attention
   - Provide frameworks for hunger/fullness awareness
   - Recommend practices for slowing down and savoring

4. NOURISHMENT CULTIVATION
   - Track the correlation between mindful eating and wellbeing
   - Alert when unconscious eating is becoming the default
   - Celebrate moments of genuine, present eating

Architecture:
- record_eating(food, type, awareness, satisfaction, hunger_accuracy, digestion): Log eating
- get_eating_stats(): Get eating pattern analysis
- get_eating_suggestion(capacity, context): Get suggestion
- get_eating_score(): Calculate overall eating health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "mindful_eating_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EATING_LOG = DATA_DIR / "eatings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EatingEntry:
    """A tracked mindful eating moment."""
    entry_id: str = ""
    food: str = ""  # what was eaten
    eating_type: str = ""  # meal, snack, emotional, social, rushed, celebratory
    awareness: float = 0.0  # 0-1
    satisfaction: float = 0.0  # 0-1
    hunger_accuracy: float = 0.0  # 0-1 were you actually hungry?
    digestion_comfort: float = 0.0  # 0-1
    savoring: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MindfulEatingCoach:
    """
    Intelligent mindful eating coach with mindlessness detection and nourishment cultivation.
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
            "avg_satisfaction": 0.0,
            "mindlessness_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_eating(self, food: str = "", eating_type: str = "", awareness: float = 0.0, satisfaction: float = 0.0, hunger_accuracy: float = 0.0, digestion_comfort: float = 0.0, savoring: float = 0.0, notes: str = "") -> EatingEntry:
        """Record a mindful eating moment."""
        entry_id = f"eat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EatingEntry(
            entry_id=entry_id,
            food=food or "unspecified",
            eating_type=eating_type or "meal",
            awareness=awareness,
            satisfaction=satisfaction,
            hunger_accuracy=hunger_accuracy,
            digestion_comfort=digestion_comfort,
            savoring=savoring,
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

    def get_eating_stats(self) -> Dict[str, Any]:
        """Get eating pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "aware_sum": 0.0, "sat_sum": 0.0, "digest_sum": 0.0})
        for e in self._entries:
            by_type[e.eating_type]["count"] += 1
            by_type[e.eating_type]["aware_sum"] += e.awareness
            by_type[e.eating_type]["sat_sum"] += e.satisfaction
            by_type[e.eating_type]["digest_sum"] += e.digestion_comfort

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_awareness": round(data["aware_sum"] / count, 2),
                "avg_satisfaction": round(data["sat_sum"] / count, 2),
                "avg_digestion": round(data["digest_sum"] / count, 2),
            }

        # Awareness analysis
        high_aware = [e for e in self._entries if e.awareness > 0.7]
        low_aware = [e for e in self._entries if e.awareness < 0.4]
        if high_aware and low_aware:
            high_aware_sat = sum(e.satisfaction for e in high_aware) / len(high_aware)
            low_aware_sat = sum(e.satisfaction for e in low_aware) / len(low_aware)
            high_aware_dig = sum(e.digestion_comfort for e in high_aware) / len(high_aware)
            low_aware_dig = sum(e.digestion_comfort for e in low_aware) / len(low_aware)
        else:
            high_aware_sat = 0
            low_aware_sat = 0
            high_aware_dig = 0
            low_aware_dig = 0

        # Hunger accuracy analysis
        high_hun = [e for e in self._entries if e.hunger_accuracy > 0.7]
        low_hun = [e for e in self._entries if e.hunger_accuracy < 0.4]
        if high_hun and low_hun:
            high_hun_sat = sum(e.satisfaction for e in high_hun) / len(high_hun)
            low_hun_sat = sum(e.satisfaction for e in low_hun) / len(low_hun)
        else:
            high_hun_sat = 0
            low_hun_sat = 0

        # Mindlessness risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            mindlessness_risk = recent_aware < 0.3 and recent_sat < 0.3
        else:
            mindlessness_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "awareness_impact": {
                "high_awareness_satisfaction": round(high_aware_sat, 2),
                "low_awareness_satisfaction": round(low_aware_sat, 2),
                "high_awareness_digestion": round(high_aware_dig, 2),
                "low_awareness_digestion": round(low_aware_dig, 2),
            },
            "hunger_effect": {
                "high_hunger_satisfaction": round(high_hun_sat, 2),
                "low_hunger_satisfaction": round(low_hun_sat, 2),
            },
            "mindlessness_risk": mindlessness_risk,
            "avg_awareness": round(sum(e.awareness for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
        }

    def get_eating_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get eating suggestion."""
        suggestions = [
            "Most people eat with their eyes on a screen. They don't taste their food. They don't feel their fullness. They don't notice their satisfaction. They're not eating. They're consuming. Be a eater. Not a consumer.",
            "Before you eat, pause. Ask: am I hungry? Or am I bored? Stressed? Lonely? The answer matters. Because food can't fix boredom. It can't fix stress. It can't fix loneliness. But it can fix hunger. Know the difference.",
            "Put down the fork between bites. Chew slowly. Taste the texture. The temperature. The flavor. This is not etiquette. It's biology. The more you chew, the more nutrients you absorb. The more satisfied you feel. The less you need to eat.",
            "Notice when you're full. Not stuffed. Full. There's a difference. The body sends signals. But you have to listen. And you can't listen if you're distracted. One more bite is rarely one more bite. It's usually too much.",
            "Savor your food. Not just the first bite. Every bite. The first bite is free. The last bite is earned. Make the middle count too. That's where the pleasure lives. In the attention. In the presence. In the savoring.",
            "Eat with others when you can. Food is social. It's connection. It's ritual. The person who eats alone too often is missing more than nutrients. They're missing belonging. Share a meal. It's medicine.",
            "Don't eat while working. Or driving. Or watching TV. Or scrolling. Eating deserves its own time. Its own space. Its own attention. When you multitask eating, you lose. Every time.",
            "Notice how different foods make you feel. Not just while eating. After. An hour later. The next day. Some foods energize. Some deplete. Your body is giving you data. Collect it. Use it.",
            "Emotional eating is not weakness. It's a signal. A signal that something needs attention. Something needs care. Something needs comfort. Food is the substitute. Find the real need. Address it. Then eat if you're hungry.",
            "The person who eats mindfully is not on a diet. They're in a relationship. With their body. With their food. With their hunger. With their satisfaction. Relationships require attention. Give it."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One bite noticed. One pause before eating. One moment of tasting. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A meal eaten without screens. A hunger check. A savoring practice. Medium mindfulness."
        else:
            capacity_note = "Good capacity. Deep mindful eating work. A systematic practice of nourishment and presence. You have the strength to truly taste your life."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Mindful eating is not about what you eat. It's about how you eat. Most people eat unconsciously. They shovel food into their mouths while staring at screens. They eat until the container is empty, not until their body is satisfied. They confuse hunger with boredom, stress, and loneliness. And they wonder why they feel unsatisfied. Why they overeat. Why they don't enjoy their meals. The work of mindful eating coaching is about bringing consciousness to the most fundamental act of self-care: nourishment. It's about noticing hunger. About tasting food. About recognizing fullness. About eating when you're hungry and stopping when you're satisfied. And about understanding that the way you eat is as important as what you eat. Because the person who eats mindfully nourishes their body and their soul. And the person who eats mindlessly consumes empty calories and empty moments."
        }

    def get_eating_score(self) -> int:
        """Calculate overall eating health (0-100)."""
        if not self._entries:
            return 25

        avg_aware = sum(e.awareness for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_hun = sum(e.hunger_accuracy for e in self._entries) / len(self._entries)
        avg_dig = sum(e.digestion_comfort for e in self._entries) / len(self._entries)
        avg_sav = sum(e.savoring for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_aware = 0
            recent_sat = 0

        # Mindlessness penalty
        mind_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_aware_30 = sum(e.awareness for e in last_30) / len(last_30)
            recent_sat_30 = sum(e.satisfaction for e in last_30) / len(last_30)
            if recent_aware_30 < 0.3 and recent_sat_30 < 0.3:
                mind_penalty = 15

        # Type variety
        unique_types = len(set(e.eating_type for e in self._entries))

        score = (avg_aware * 25) + (avg_sat * 20) + (avg_hun * 15) + (avg_dig * 10) + (avg_sav * 10) + (recent_aware * 5) + (recent_sat * 5) + (unique_types * 2) - mind_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_awareness"] = round(sum(e.awareness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_aware = sum(e.awareness for e in recent) / len(recent)
                recent_sat = sum(e.satisfaction for e in recent) / len(recent)
                self._stats["mindlessness_risk"] = recent_aware < 0.3 and recent_sat < 0.3
            else:
                self._stats["mindlessness_risk"] = False

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

    def _log_entry(self, entry: EatingEntry):
        try:
            with open(EATING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "food": entry.food,
                    "eating_type": entry.eating_type,
                    "awareness": entry.awareness,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mec_instance: Optional[MindfulEatingCoach] = None
_mec_lock = threading.Lock()


def get_mindful_eating_coach() -> MindfulEatingCoach:
    global _mec_instance
    with _mec_lock:
        if _mec_instance is None:
            _mec_instance = MindfulEatingCoach()
        return _mec_instance
