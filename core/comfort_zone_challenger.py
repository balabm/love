"""
LOVE Comfort Zone Challenger — Growth Intelligence (Modern AI Pattern)

Most people stay where they are because it's comfortable. This challenger:

1. CHALLENGE TRACKING
   - Record challenges and their characteristics
   - Track challenge types (social, physical, intellectual, creative, emotional)
   - Log growth, discomfort, and outcome from challenges

2. PATTERN ANALYSIS
   - Identify the user's challenge profile (seeker, avoider, balanced, stuck)
   - Find challenge patterns that create growth without burnout
   - Detect comfort addiction and its costs

3. CHALLENGE BUILDING
   - Suggest challenges matched to current capacity and growth goals
   - Provide frameworks for navigating discomfort
   - Recommend progressive challenges that build confidence

4. GROWTH CULTIVATION
   - Track the correlation between challenge and life satisfaction
   - Alert when comfort has become the primary value
   - Celebrate moments of genuine growth through discomfort

Architecture:
- record_challenge(challenge, type, discomfort, growth, outcome): Log challenge
- get_challenge_stats(): Get challenge pattern analysis
- get_challenge_suggestion(capacity, context): Get suggestion
- get_challenge_score(): Calculate overall challenge health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "comfort_zone_challenger"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CHALLENGE_LOG = DATA_DIR / "challenges.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ChallengeEntry:
    """A tracked challenge."""
    entry_id: str = ""
    challenge: str = ""  # what was done
    challenge_type: str = ""  # social, physical, intellectual, creative, emotional
    discomfort: float = 0.5  # 0-1
    growth: float = 0.0  # 0-1
    outcome: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    meaning: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ComfortZoneChallenger:
    """
    Intelligent comfort zone challenger with growth detection and discomfort cultivation.
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
            "avg_growth": 0.0,
            "avg_discomfort": 0.0,
            "comfort_addiction": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_challenge(self, challenge: str = "", challenge_type: str = "", discomfort: float = 0.5, growth: float = 0.0, outcome: float = 0.0, confidence: float = 0.0, meaning: float = 0.0, notes: str = "") -> ChallengeEntry:
        """Record a challenge."""
        entry_id = f"czc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ChallengeEntry(
            entry_id=entry_id,
            challenge=challenge or "unspecified",
            challenge_type=challenge_type or "general",
            discomfort=discomfort,
            growth=growth,
            outcome=outcome,
            confidence=confidence,
            meaning=meaning,
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

    def get_challenge_stats(self) -> Dict[str, Any]:
        """Get challenge pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "discomfort_sum": 0.0, "growth_sum": 0.0, "outcome_sum": 0.0})
        for e in self._entries:
            by_type[e.challenge_type]["count"] += 1
            by_type[e.challenge_type]["discomfort_sum"] += e.discomfort
            by_type[e.challenge_type]["growth_sum"] += e.growth
            by_type[e.challenge_type]["outcome_sum"] += e.outcome

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_discomfort": round(data["discomfort_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_outcome": round(data["outcome_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_growth"]) if type_stats else ("", {})

        # Discomfort analysis
        high_discomfort = [e for e in self._entries if e.discomfort > 0.7]
        low_discomfort = [e for e in self._entries if e.discomfort < 0.4]
        if high_discomfort and low_discomfort:
            high_dis_growth = sum(e.growth for e in high_discomfort) / len(high_discomfort)
            low_dis_growth = sum(e.growth for e in low_discomfort) / len(low_discomfort)
            high_dis_conf = sum(e.confidence for e in high_discomfort) / len(high_discomfort)
            low_dis_conf = sum(e.confidence for e in low_discomfort) / len(low_discomfort)
        else:
            high_dis_growth = 0
            low_dis_growth = 0
            high_dis_conf = 0
            low_dis_conf = 0

        # Outcome analysis
        high_outcome = [e for e in self._entries if e.outcome > 0.7]
        low_outcome = [e for e in self._entries if e.outcome < 0.4]
        if high_outcome and low_outcome:
            high_outcome_conf = sum(e.confidence for e in high_outcome) / len(high_outcome)
            low_outcome_conf = sum(e.confidence for e in low_outcome) / len(low_outcome)
        else:
            high_outcome_conf = 0
            low_outcome_conf = 0

        # Comfort addiction detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_discomfort = sum(e.discomfort for e in recent) / len(recent)
            recent_growth = sum(e.growth for e in recent) / len(recent)
            comfort_addiction = recent_discomfort < 0.3 and recent_growth < 0.3
        else:
            comfort_addiction = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "discomfort_impact": {
                "high_discomfort_growth": round(high_dis_growth, 2),
                "low_discomfort_growth": round(low_dis_growth, 2),
                "high_discomfort_confidence": round(high_dis_conf, 2),
                "low_discomfort_confidence": round(low_dis_conf, 2),
            },
            "outcome_effect": {
                "high_outcome_confidence": round(high_outcome_conf, 2),
                "low_outcome_confidence": round(low_outcome_conf, 2),
            },
            "comfort_addiction": comfort_addiction,
            "avg_discomfort": round(sum(e.discomfort for e in self._entries) / len(self._entries), 2),
            "avg_growth": round(sum(e.growth for e in self._entries) / len(self._entries), 2),
        }

    def get_challenge_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get challenge suggestion."""
        suggestions = [
            "Do one thing that scares you. Not something dangerous. Something uncomfortable. A conversation. A performance. A new route. The thing you're avoiding is where growth lives.",
            "Say yes to something you'd normally decline. Not out of obligation. Out of stretch. The invitation that makes you nervous is the invitation that's worth accepting.",
            "Start before you're ready. Most people wait until they feel confident. Confidence comes from action, not the other way around. Begin. The confidence will follow.",
            "Ask for something you want. Most people don't get what they want because they don't ask. The fear of rejection is worse than rejection itself. Ask.",
            "Try something you're bad at. Not to become good. To experience being a beginner again. Beginners are humble. Beginners are curious. Beginners grow fast.",
            "Speak in front of people. Even a small group. Even a toast. Public speaking is one of the most common fears. And one of the most valuable skills. Start small.",
            "Travel somewhere new. Not necessarily far. A new neighborhood. A new restaurant. A new activity. Novelty stretches the mind. New places create new thoughts.",
            "Admit you were wrong. About something. To someone. The person who can admit error has already surpassed most of humanity. It's uncomfortable. And it's liberating.",
            "Set a goal that feels impossible. Not to achieve it necessarily. To discover what's possible. The stretch goal reveals your real capacity. And it's always more than you think.",
            "Comfort is the enemy of growth. The warm bed. The familiar routine. The safe choice. These feel good. And they keep you exactly where you are. Growth requires the willingness to be uncomfortable. To be uncertain. To be bad at something. To fail. The person who never leaves their comfort zone never discovers who they could become.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One tiny step. One small risk. One minor discomfort. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A meaningful challenge. A stretch. A step beyond the familiar. Medium growth."
        else:
            capacity_note = "Good capacity. A major challenge. A leap. Something that truly scares you. You have the energy for real transformation."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Growth and comfort cannot coexist. This is not a metaphor. It's a neurological reality. The brain only rewires under challenge. Only adapts under stress. Only grows under discomfort. The person who avoids discomfort avoids growth. And the person who avoids growth is already dying. Not physically. But in the sense that they are no longer becoming. They are just maintaining. And maintenance is not living. Living is becoming. Living is stretching. Living is the willingness to be uncomfortable in service of who you might become. The challenge is not to eliminate discomfort. It's to become comfortable with discomfort. To seek it. To welcome it. To know that on the other side of discomfort is everything you want.",
        }

    def get_challenge_score(self) -> int:
        """Calculate overall challenge health (0-100)."""
        if not self._entries:
            return 25

        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)
        avg_outcome = sum(e.outcome for e in self._entries) / len(self._entries)
        avg_confidence = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_meaning = sum(e.meaning for e in self._entries) / len(self._entries)
        avg_discomfort = sum(e.discomfort for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_growth = sum(e.growth for e in recent) / len(recent)
            recent_confidence = sum(e.confidence for e in recent) / len(recent)
        else:
            recent_growth = 0
            recent_confidence = 0

        # Comfort addiction penalty
        comfort_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if len(last_90) < 3:
            comfort_penalty = 20

        # Type variety
        unique_types = len(set(e.challenge_type for e in self._entries))

        score = (avg_growth * 30) + (avg_outcome * 20) + (avg_confidence * 15) + (avg_meaning * 15) + (recent_growth * 10) + (recent_confidence * 5) + (unique_types * 2) - comfort_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_growth"] = round(sum(e.growth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_discomfort"] = round(sum(e.discomfort for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_discomfort = sum(e.discomfort for e in recent) / len(recent)
                recent_growth = sum(e.growth for e in recent) / len(recent)
                self._stats["comfort_addiction"] = recent_discomfort < 0.3 and recent_growth < 0.3
            else:
                self._stats["comfort_addiction"] = True

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.comfort_zone_challenger")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.comfort_zone_challenger")

    def _log_entry(self, entry: ChallengeEntry):
        try:
            with open(CHALLENGE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "challenge": entry.challenge,
                    "challenge_type": entry.challenge_type,
                    "discomfort": entry.discomfort,
                    "growth": entry.growth,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.comfort_zone_challenger")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_czc_instance: Optional[ComfortZoneChallenger] = None
_czc_lock = threading.Lock()


def get_comfort_zone_challenger() -> ComfortZoneChallenger:
    global _czc_instance
    with _czc_lock:
        if _czc_instance is None:
            _czc_instance = ComfortZoneChallenger()
        return _czc_instance
