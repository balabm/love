"""
LOVE Passion Cultivator — Desire Intelligence (Modern AI Pattern)

Most people let their passions fade. This cultivator:

1. PASSION TRACKING
   - Record passion moments and their characteristics
   - Track passion types (creative, intellectual, relational, physical, spiritual, experiential)
   - Log intensity, duration, satisfaction, and integration of passion

2. PATTERN ANALYSIS
   - Identify the user's passion profile (dormant, flickering, burning, blazing)
   - Find passion patterns that create vitality vs apathy
   - Detect chronic passion suppression and its costs

3. PASSION BUILDING
   - Suggest practices for rekindling and sustaining passion
   - Provide frameworks for passion discovery and deepening
   - Recommend practices for integrating passion into daily life

4. VITAL DESIRE CULTIVATION
   - Track the correlation between passion and life satisfaction
   - Alert when apathy is becoming the default
   - Celebrate moments of genuine, burning passion

Architecture:
- record_passion(activity, type, intensity, duration, satisfaction, integration): Log passion
- get_passion_stats(): Get passion pattern analysis
- get_passion_suggestion(capacity, context): Get suggestion
- get_passion_score(): Calculate overall passion health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "passion_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PASSION_LOG = DATA_DIR / "passions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PassionEntry:
    """A tracked passion moment."""
    entry_id: str = ""
    activity: str = ""  # what was done
    passion_type: str = ""  # creative, intellectual, relational, physical, spiritual, experiential
    intensity: float = 0.0  # 0-1
    duration: float = 0.0  # hours
    satisfaction: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1 in life
    vitality: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PassionCultivator:
    """
    Intelligent passion cultivator with apathy detection and vital desire cultivation.
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
            "avg_intensity": 0.0,
            "avg_satisfaction": 0.0,
            "apathy_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_passion(self, activity: str = "", passion_type: str = "", intensity: float = 0.0, duration: float = 0.0, satisfaction: float = 0.0, integration: float = 0.0, vitality: float = 0.0, notes: str = "") -> PassionEntry:
        """Record a passion moment."""
        entry_id = f"psn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PassionEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            passion_type=passion_type or "creative",
            intensity=intensity,
            duration=duration,
            satisfaction=satisfaction,
            integration=integration,
            vitality=vitality,
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

    def get_passion_stats(self) -> Dict[str, Any]:
        """Get passion pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "satisfaction_sum": 0.0, "vitality_sum": 0.0})
        for e in self._entries:
            by_type[e.passion_type]["count"] += 1
            by_type[e.passion_type]["intensity_sum"] += e.intensity
            by_type[e.passion_type]["satisfaction_sum"] += e.satisfaction
            by_type[e.passion_type]["vitality_sum"] += e.vitality

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                "avg_vitality": round(data["vitality_sum"] / count, 2),
            }

        # Intensity analysis
        high_int = [e for e in self._entries if e.intensity > 0.7]
        low_int = [e for e in self._entries if e.intensity < 0.4]
        if high_int and low_int:
            high_int_sat = sum(e.satisfaction for e in high_int) / len(high_int)
            low_int_sat = sum(e.satisfaction for e in low_int) / len(low_int)
            high_int_vit = sum(e.vitality for e in high_int) / len(high_int)
            low_int_vit = sum(e.vitality for e in low_int) / len(low_int)
        else:
            high_int_sat = 0
            low_int_sat = 0
            high_int_vit = 0
            low_int_vit = 0

        # Integration analysis
        high_integ = [e for e in self._entries if e.integration > 0.7]
        low_integ = [e for e in self._entries if e.integration < 0.4]
        if high_integ and low_integ:
            high_integ_sat = sum(e.satisfaction for e in high_integ) / len(high_integ)
            low_integ_sat = sum(e.satisfaction for e in low_integ) / len(low_integ)
        else:
            high_integ_sat = 0
            low_integ_sat = 0

        # Apathy risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_int = sum(e.intensity for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
            apathy_risk = recent_int < 0.3 and recent_sat < 0.3
        else:
            apathy_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "intensity_impact": {
                "high_intensity_satisfaction": round(high_int_sat, 2),
                "low_intensity_satisfaction": round(low_int_sat, 2),
                "high_intensity_vitality": round(high_int_vit, 2),
                "low_intensity_vitality": round(low_int_vit, 2),
            },
            "integration_effect": {
                "high_integration_satisfaction": round(high_integ_sat, 2),
                "low_integration_satisfaction": round(low_integ_sat, 2),
            },
            "apathy_risk": apathy_risk,
            "avg_intensity": round(sum(e.intensity for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
        }

    def get_passion_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get passion suggestion."""
        suggestions = [
            "Passion is not a luxury. It's oxygen for the soul. The person without passion is not calm. They're suffocating. Slowly. Quietly. And they call it maturity. It's not maturity. It's resignation.",
            "What did you love as a child? Before you were told what was practical? Before you learned what was acceptable? That's where your passion lives. Go back. Find it. It's still there. Waiting.",
            "Passion is not about being good at something. It's about loving it. The person who paints badly but loves painting is more alive than the person who paints well but hates it. Passion is love. Not competence.",
            "Start small. You don't need to quit your job to pursue your passion. Fifteen minutes. One hour. One small step. Passion doesn't require grand gestures. It requires consistent attention.",
            "Passion is contagious. When you're passionate, others feel it. They want to be around it. They want to help it. Passion attracts resources. Apathy repels them. Be passionate. The world will respond.",
            "Don't wait for inspiration. Inspiration is a byproduct of action. The painter who waits for inspiration never paints. The writer who waits for inspiration never writes. Start. Passion follows.",
            "Your passion is not selfish. It's your gift to the world. The passionate person is a light. They inspire others. They create energy. They make the world more interesting. Your passion is service.",
            "Notice when you lose track of time. That's passion. When hours feel like minutes. When you forget to eat. When you can't stop. That's the sign. Follow it. Build a life around it.",
            "Passion can be rekindled. If it went dormant, it's not dead. It's sleeping. Wake it up. Remember what you loved. Do one small thing. Feel the spark. Fan it. It will grow.",
            "The person with passion is never bored. Because they see the world as fascinating. Because they have something to do. Something to learn. Something to create. Passion is the cure for boredom. And for much of what ails us."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small passion moment. One thing you love. Fifteen minutes of it. One spark rekindled. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A passion project. A creative session. A hobby revisited. A desire honored. Medium cultivation."
        else:
            capacity_note = "Good capacity. Deep passion work. A systematic cultivation of desire and vitality. You have the strength to burn brightly."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Passion is not a feeling. It's a practice. It's the practice of doing what you love, regularly, intentionally, even when you don't feel like it. Especially when you don't feel like it. Because passion is not the spark that starts the fire. It's the fire that keeps burning after the spark is gone. Most people think passion is something that happens to them. They wait for it. They search for it. They complain when they can't find it. But passion is not found. It's cultivated. It's built. It's maintained. Through action. Through commitment. Through showing up for what you love, even when it's hard. Even when you're tired. Even when no one is watching. The work of passion cultivation is about choosing what you love. About making time for it. About protecting it from the demands of a world that wants you to be practical. And about understanding that the person who has passion is not luckier than the person who doesn't. They're just more committed."
        }

    def get_passion_score(self) -> int:
        """Calculate overall passion health (0-100)."""
        if not self._entries:
            return 25

        avg_int = sum(e.intensity for e in self._entries) / len(self._entries)
        avg_sat = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_integ = sum(e.integration for e in self._entries) / len(self._entries)
        avg_vit = sum(e.vitality for e in self._entries) / len(self._entries)
        avg_dur = sum(e.duration for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_int = sum(e.intensity for e in recent) / len(recent)
            recent_sat = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_int = 0
            recent_sat = 0

        # Apathy penalty
        apathy_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_int_30 = sum(e.intensity for e in last_30) / len(last_30)
            recent_sat_30 = sum(e.satisfaction for e in last_30) / len(last_30)
            if recent_int_30 < 0.3 and recent_sat_30 < 0.3:
                apathy_penalty = 15

        # Type variety
        unique_types = len(set(e.passion_type for e in self._entries))

        score = (avg_int * 25) + (avg_sat * 20) + (avg_integ * 15) + (avg_vit * 15) + (recent_int * 5) + (recent_sat * 5) + (unique_types * 2) + min(5, avg_dur / 10) - apathy_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intensity"] = round(sum(e.intensity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_int = sum(e.intensity for e in recent) / len(recent)
                recent_sat = sum(e.satisfaction for e in recent) / len(recent)
                self._stats["apathy_risk"] = recent_int < 0.3 and recent_sat < 0.3
            else:
                self._stats["apathy_risk"] = False

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

    def _log_entry(self, entry: PassionEntry):
        try:
            with open(PASSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "passion_type": entry.passion_type,
                    "intensity": entry.intensity,
                    "satisfaction": entry.satisfaction,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pc_instance: Optional[PassionCultivator] = None
_pc_lock = threading.Lock()


def get_passion_cultivator() -> PassionCultivator:
    global _pc_instance
    with _pc_lock:
        if _pc_instance is None:
            _pc_instance = PassionCultivator()
        return _pc_instance
