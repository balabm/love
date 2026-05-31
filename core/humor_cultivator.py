"""
LOVE Humor Cultivator — Levity Intelligence (Modern AI Pattern)

Most adults lose their sense of humor under the weight of responsibility.
This cultivator:

1. HUMOR TRACKING
   - Record moments of laughter and their triggers
   - Track humor types (wit, absurdity, wordplay, physical, dark, self-deprecating)
   - Log lightness, connection, and stress relief from humor

2. PATTERN ANALYSIS
   - Identify the user's humor profile (playful, serious, sarcastic, joyful)
   - Find humor patterns that create resilience and connection
   - Detect humor droughts and their consequences

3. HUMOR BUILDING
   - Suggest ways to cultivate lightness in daily life
   - Provide frameworks for appropriate humor in difficult situations
   - Recommend humor styles that match the user's personality

4. LEVITY CULTIVATION
   - Track the correlation between laughter and wellbeing
   - Alert when life has become excessively serious
   - Celebrate moments of genuine joy and absurdity

Architecture:
- record_laughter(moment, type, lightness, connection, relief): Log laughter
- get_humor_stats(): Get humor pattern analysis
- get_humor_suggestion(capacity, context): Get suggestion
- get_humor_score(): Calculate overall humor health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "humor_cultivator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HUMOR_LOG = DATA_DIR / "laughter.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class HumorEntry:
    """A tracked humor/laughter entry."""
    entry_id: str = ""
    moment: str = ""  # what was funny
    humor_type: str = ""  # wit, absurdity, wordplay, physical, dark, self_deprecating, situational
    lightness: float = 0.5  # 0-1
    connection: float = 0.0  # 0-1 did it connect people?
    stress_relief: float = 0.0  # 0-1
    creativity_boost: float = 0.0  # 0-1
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HumorCultivator:
    """
    Intelligent humor cultivator with lightness detection and levity cultivation.
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
            "avg_lightness": 0.0,
            "avg_stress_relief": 0.0,
            "seriousness_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_laughter(self, moment: str = "", humor_type: str = "", lightness: float = 0.5, connection: float = 0.0, stress_relief: float = 0.0, creativity_boost: float = 0.0, duration_minutes: float = 0.0, notes: str = "") -> HumorEntry:
        """Record a humor/laughter entry."""
        entry_id = f"hum_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = HumorEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            humor_type=humor_type or "situational",
            lightness=lightness,
            connection=connection,
            stress_relief=stress_relief,
            creativity_boost=creativity_boost,
            duration_minutes=duration_minutes,
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

    def get_humor_stats(self) -> Dict[str, Any]:
        """Get humor pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "lightness_sum": 0.0, "connection_sum": 0.0, "relief_sum": 0.0})
        for e in self._entries:
            by_type[e.humor_type]["count"] += 1
            by_type[e.humor_type]["lightness_sum"] += e.lightness
            by_type[e.humor_type]["connection_sum"] += e.connection
            by_type[e.humor_type]["relief_sum"] += e.stress_relief

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_lightness": round(data["lightness_sum"] / count, 2),
                "avg_connection": round(data["connection_sum"] / count, 2),
                "avg_stress_relief": round(data["relief_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_connection"]) if type_stats else ("", {})

        # Lightness analysis
        high_light = [e for e in self._entries if e.lightness > 0.7]
        low_light = [e for e in self._entries if e.lightness < 0.4]
        if high_light and low_light:
            high_light_relief = sum(e.stress_relief for e in high_light) / len(high_light)
            low_light_relief = sum(e.stress_relief for e in low_light) / len(low_light)
            high_light_conn = sum(e.connection for e in high_light) / len(high_light)
            low_light_conn = sum(e.connection for e in low_light) / len(low_light)
        else:
            high_light_relief = 0
            low_light_relief = 0
            high_light_conn = 0
            low_light_conn = 0

        # Connection analysis
        high_conn = [e for e in self._entries if e.connection > 0.7]
        low_conn = [e for e in self._entries if e.connection < 0.4]
        if high_conn and low_conn:
            high_conn_creativity = sum(e.creativity_boost for e in high_conn) / len(high_conn)
            low_conn_creativity = sum(e.creativity_boost for e in low_conn) / len(low_conn)
        else:
            high_conn_creativity = 0
            low_conn_creativity = 0

        # Seriousness risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_lightness = sum(e.lightness for e in recent) / len(recent)
            recent_stress_relief = sum(e.stress_relief for e in recent) / len(recent)
            seriousness_risk = recent_lightness < 0.3 and recent_stress_relief < 0.3
        else:
            seriousness_risk = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "lightness_impact": {
                "high_lightness_relief": round(high_light_relief, 2),
                "low_lightness_relief": round(low_light_relief, 2),
                "high_lightness_connection": round(high_light_conn, 2),
                "low_lightness_connection": round(low_light_conn, 2),
            },
            "connection_effect": {
                "high_connection_creativity": round(high_conn_creativity, 2),
                "low_connection_creativity": round(low_conn_creativity, 2),
            },
            "seriousness_risk": seriousness_risk,
            "avg_lightness": round(sum(e.lightness for e in self._entries) / len(self._entries), 2),
            "avg_stress_relief": round(sum(e.stress_relief for e in self._entries) / len(self._entries), 2),
        }

    def get_humor_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get humor suggestion."""
        suggestions = [
            "Watch something funny. Not as distraction. As medicine. Laughter reduces cortisol. It boosts immunity. It increases pain tolerance. Comedy is healthcare.",
            "Make fun of yourself. Gently. Self-deprecating humor is a sign of security. It says: I know I'm flawed and I'm okay with it. That's magnetic.",
            "Find the absurd in the mundane. The ridiculous traffic jam. The bizarre email. The strange coincidence. Absurdity is everywhere if you look for it.",
            "Play with language. Puns. Wordplay. Misheard lyrics. Language is a toy. Most people treat it like a tool. Play with it.",
            "Be silly with someone you trust. Dance in the kitchen. Sing badly. Make faces. Adult silliness is a rebellion against the gravity of existence.",
            "Collect funny things. A note. A photo. A story. Keep a humor file. When you're down, read it. Laughter is a resource you can store.",
            "Comedy reveals truth. The best humor points at what we all see but nobody says. Be the person who names the elephant. With a smile.",
            "Laugh at fear. Not to dismiss it. To shrink it. Fear can't survive being laughed at. The thing you're afraid of is rarely as powerful as you imagine.",
            "Humor is social glue. The shared joke. The inside reference. The collective groan. Laughter creates instant intimacy. Use it.",
            "Life is inherently absurd. You will die. Everyone you love will die. The universe doesn't care about your plans. Given that context, taking yourself seriously is the only real foolishness.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One funny video. One silly thought. One smile. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A comedy show. A playful conversation. A joke shared. Medium lightness."
        else:
            capacity_note = "Good capacity. Full levity. Be the source of humor. Create absurdity. You have the energy to make others laugh too."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Humor is not trivial. It's essential. The ability to laugh is the ability to survive. People who maintain humor through difficulty are not denying reality. They're asserting their humanity. Laughter says: you can hurt me but you cannot destroy my spirit. The most serious people are often the most afraid. The most playful people are often the most free. Life is short and uncertain. The only rational response is to take it lightly. Not because it doesn't matter. Because it matters too much to spend it grim.",
        }

    def get_humor_score(self) -> int:
        """Calculate overall humor health (0-100)."""
        if not self._entries:
            return 25

        avg_lightness = sum(e.lightness for e in self._entries) / len(self._entries)
        avg_relief = sum(e.stress_relief for e in self._entries) / len(self._entries)
        avg_connection = sum(e.connection for e in self._entries) / len(self._entries)
        avg_creativity = sum(e.creativity_boost for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_lightness = sum(e.lightness for e in recent) / len(recent)
            recent_relief = sum(e.stress_relief for e in recent) / len(recent)
        else:
            recent_lightness = 0
            recent_relief = 0

        # Seriousness penalty
        seriousness_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 3:
            seriousness_penalty = 15

        # Type variety
        unique_types = len(set(e.humor_type for e in self._entries))

        score = (avg_lightness * 25) + (avg_relief * 20) + (avg_connection * 15) + (avg_creativity * 10) + (recent_lightness * 15) + (recent_relief * 10) + (unique_types * 2) - seriousness_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_lightness"] = round(sum(e.lightness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_stress_relief"] = round(sum(e.stress_relief for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_lightness = sum(e.lightness for e in recent) / len(recent)
                recent_relief = sum(e.stress_relief for e in recent) / len(recent)
                self._stats["seriousness_risk"] = recent_lightness < 0.3 and recent_relief < 0.3
            else:
                self._stats["seriousness_risk"] = True

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

    def _log_entry(self, entry: HumorEntry):
        try:
            with open(HUMOR_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "humor_type": entry.humor_type,
                    "lightness": entry.lightness,
                    "stress_relief": entry.stress_relief,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hc_instance: Optional[HumorCultivator] = None
_hc_lock = threading.Lock()


def get_humor_cultivator() -> HumorCultivator:
    global _hc_instance
    with _hc_lock:
        if _hc_instance is None:
            _hc_instance = HumorCultivator()
        return _hc_instance
