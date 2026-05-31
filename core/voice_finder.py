"""
LOVE Voice Finder — Expression Intelligence (Modern AI Pattern)

Most people suppress their authentic voice. This finder:

1. VOICE TRACKING
   - Record expressions and their characteristics
   - Track expression types (spoken, written, creative, professional, intimate)
   - Log authenticity, impact, and comfort with expression

2. PATTERN ANALYSIS
   - Identify the user's voice profile (authentic, muted, performative, developing)
   - Find expression patterns that create impact vs suppression
   - Detect voice loss and its causes

3. VOICE BUILDING
   - Suggest practices for finding and using authentic voice
   - Provide frameworks for expressing difficult truths
   - Recommend expression practices matched to context

4. AUTHENTICITY CULTIVATION
   - Track the correlation between authentic voice and wellbeing
   - Alert when voice is becoming chronically suppressed
   - Celebrate moments of genuine expression

Architecture:
- record_expression(expression, type, authenticity, impact, comfort): Log expression
- get_voice_stats(): Get voice pattern analysis
- get_voice_suggestion(capacity, context): Get suggestion
- get_voice_score(): Calculate overall voice health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "voice_finder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VOICE_LOG = DATA_DIR / "expressions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class VoiceEntry:
    """A tracked expression."""
    entry_id: str = ""
    expression: str = ""  # what was expressed
    expression_type: str = ""  # spoken, written, creative, professional, intimate
    authenticity: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    comfort: float = 0.0  # 0-1
    clarity: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VoiceFinder:
    """
    Intelligent voice finder with authenticity detection and expression cultivation.
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
            "avg_authenticity": 0.0,
            "avg_impact": 0.0,
            "suppression_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_expression(self, expression: str = "", expression_type: str = "", authenticity: float = 0.0, impact: float = 0.0, comfort: float = 0.0, clarity: float = 0.0, courage: float = 0.0, notes: str = "") -> VoiceEntry:
        """Record an expression."""
        entry_id = f"voc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = VoiceEntry(
            entry_id=entry_id,
            expression=expression or "unspecified",
            expression_type=expression_type or "spoken",
            authenticity=authenticity,
            impact=impact,
            comfort=comfort,
            clarity=clarity,
            courage=courage,
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

    def get_voice_stats(self) -> Dict[str, Any]:
        """Get voice pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "authenticity_sum": 0.0, "impact_sum": 0.0, "comfort_sum": 0.0})
        for e in self._entries:
            by_type[e.expression_type]["count"] += 1
            by_type[e.expression_type]["authenticity_sum"] += e.authenticity
            by_type[e.expression_type]["impact_sum"] += e.impact
            by_type[e.expression_type]["comfort_sum"] += e.comfort

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_authenticity": round(data["authenticity_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_comfort": round(data["comfort_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_authenticity"]) if type_stats else ("", {})

        # Authenticity analysis
        high_auth = [e for e in self._entries if e.authenticity > 0.7]
        low_auth = [e for e in self._entries if e.authenticity < 0.4]
        if high_auth and low_auth:
            high_auth_imp = sum(e.impact for e in high_auth) / len(high_auth)
            low_auth_imp = sum(e.impact for e in low_auth) / len(low_auth)
            high_auth_comf = sum(e.comfort for e in high_auth) / len(high_auth)
            low_auth_comf = sum(e.comfort for e in low_auth) / len(low_auth)
        else:
            high_auth_imp = 0
            low_auth_imp = 0
            high_auth_comf = 0
            low_auth_comf = 0

        # Clarity analysis
        high_clar = [e for e in self._entries if e.clarity > 0.7]
        low_clar = [e for e in self._entries if e.clarity < 0.4]
        if high_clar and low_clar:
            high_clar_imp = sum(e.impact for e in high_clar) / len(high_clar)
            low_clar_imp = sum(e.impact for e in low_clar) / len(low_clar)
        else:
            high_clar_imp = 0
            low_clar_imp = 0

        # Suppression risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            recent_impact = sum(e.impact for e in recent) / len(recent)
            suppression_risk = recent_auth < 0.3 and recent_impact < 0.3
        else:
            suppression_risk = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "authenticity_impact": {
                "high_authenticity_impact": round(high_auth_imp, 2),
                "low_authenticity_impact": round(low_auth_imp, 2),
                "high_authenticity_comfort": round(high_auth_comf, 2),
                "low_authenticity_comfort": round(low_auth_comf, 2),
            },
            "clarity_effect": {
                "high_clarity_impact": round(high_clar_imp, 2),
                "low_clarity_impact": round(low_clar_imp, 2),
            },
            "suppression_risk": suppression_risk,
            "avg_authenticity": round(sum(e.authenticity for e in self._entries) / len(self._entries), 2),
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 2),
        }

    def get_voice_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get voice suggestion."""
        suggestions = [
            "Say the thing you're afraid to say. Not aggressively. Not cruelly. Honestly. The truth you withhold is the relationship you never build.",
            "Your voice is not your vocabulary. It's not your accent. It's your willingness to say what you actually think and feel. That's the voice. Find it. Use it.",
            "Write what you can't say. The page doesn't judge. It doesn't interrupt. It doesn't misunderstand. Write the truth. Then decide if you want to speak it.",
            "Practice with small truths. 'I don't like this restaurant.' 'I prefer this color.' 'I disagree.' Small truths build the muscle for big ones.",
            "Your voice is your signature. It's how you leave your mark on the world. Don't let others write your signature for you. Sign your own name.",
            "Speak before you're ready. The perfect words rarely come. The right words come when you start speaking. Begin. The clarity follows.",
            "Your voice matters. Not because you're special. Because you're here. Because you have a perspective no one else has. Because the world needs to hear what you have to say.",
            "Don't dilute your voice to be liked. The person who likes the diluted you doesn't like you. They like the performance. Find people who like the real you.",
            "Listen to yourself. Record yourself. Read your writing aloud. Your voice is a instrument. Tune it. Practice it. Master it.",
            "The world is full of muted voices. People with important things to say who are too afraid to say them. Don't be one of them. Speak. The world needs your voice."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One honest word. One true sentence. One moment of real expression. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A real conversation. A written truth. A creative expression. Medium voice work."
        else:
            capacity_note = "Good capacity. A bold statement. A public expression. A significant truth. You have the energy to use your real voice."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Your voice is the externalization of your inner self. When you suppress your voice, you suppress yourself. When you find your voice, you find yourself. And the person who has found their voice is immune to manipulation. They're immune to being controlled. They're immune to being made small. Because they know who they are. And they say it. Out loud. In public. Without apology. The person who has lost their voice has lost themselves. And the work of finding your voice is the work of finding yourself. It's not about being loud. It's about being real. It's not about being articulate. It's about being honest. Your voice is your freedom. Use it."
        }

    def get_voice_score(self) -> int:
        """Calculate overall voice health (0-100)."""
        if not self._entries:
            return 25

        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_impact = sum(e.impact for e in self._entries) / len(self._entries)
        avg_comfort = sum(e.comfort for e in self._entries) / len(self._entries)
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_courage = sum(e.courage for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            recent_impact = sum(e.impact for e in recent) / len(recent)
        else:
            recent_auth = 0
            recent_impact = 0

        # Suppression penalty
        suppress_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 2:
            suppress_penalty = 15

        # Type variety
        unique_types = len(set(e.expression_type for e in self._entries))

        score = (avg_auth * 30) + (avg_impact * 20) + (avg_comfort * 10) + (avg_clarity * 15) + (avg_courage * 15) + (recent_auth * 5) + (recent_impact * 5) + (unique_types * 2) - suppress_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_authenticity"] = round(sum(e.authenticity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_impact"] = round(sum(e.impact for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_auth = sum(e.authenticity for e in recent) / len(recent)
                recent_impact = sum(e.impact for e in recent) / len(recent)
                self._stats["suppression_risk"] = recent_auth < 0.3 and recent_impact < 0.3
            else:
                self._stats["suppression_risk"] = True

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

    def _log_entry(self, entry: VoiceEntry):
        try:
            with open(VOICE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "expression": entry.expression,
                    "expression_type": entry.expression_type,
                    "authenticity": entry.authenticity,
                    "impact": entry.impact,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vf_instance: Optional[VoiceFinder] = None
_vf_lock = threading.Lock()


def get_voice_finder() -> VoiceFinder:
    global _vf_instance
    with _vf_lock:
        if _vf_instance is None:
            _vf_instance = VoiceFinder()
        return _vf_instance
