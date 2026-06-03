"""
LOVE Language Immersion Coach — Linguistic Intelligence (Modern AI Pattern)

Most people study languages without immersion. This coach:

1. IMMERSION TRACKING
   - Record language immersion moments and their characteristics
   - Track immersion types (listening, speaking, reading, writing, thinking, dreaming)
   - Log exposure, comprehension, courage, consistency, and joy of immersion

2. PATTERN ANALYSIS
   - Identify the user's immersion profile (avoidant, studious, developing, immersed)
   - Find immersion patterns that create fluency vs stagnation
   - Detect chronic classroom-only learning and its costs

3. IMMERSION BUILDING
   - Suggest practices for genuine language immersion
   - Provide frameworks for daily exposure and interaction
   - Recommend practices for overcoming the fear of speaking

4. FLUENCY CULTIVATION
   - Track the correlation between immersion time and language growth
   - Alert when studying is replacing using
   - Celebrate moments of genuine language breakthrough

Architecture:
- record_immersion(activity, type, exposure, comprehension, courage, consistency, joy): Log immersion
- get_immersion_stats(): Get immersion pattern analysis
- get_immersion_suggestion(capacity, context): Get suggestion
- get_immersion_score(): Calculate overall immersion health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "language_immersion_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

IMMERSION_LOG = DATA_DIR / "immersions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ImmersionEntry:
    """A tracked language immersion moment."""
    entry_id: str = ""
    activity: str = ""  # what was the activity
    immersion_type: str = ""  # listening, speaking, reading, writing, thinking, dreaming
    exposure: float = 0.0  # 0-1
    comprehension: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    consistency: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    authenticity: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LanguageImmersionCoach:
    """
    Intelligent language immersion coach with avoidance detection and fluency cultivation.
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
            "avg_exposure": 0.0,
            "avg_courage": 0.0,
            "avoidance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_immersion(self, activity: str = "", immersion_type: str = "", exposure: float = 0.0, comprehension: float = 0.0, courage: float = 0.0, consistency: float = 0.0, joy: float = 0.0, authenticity: float = 0.0, notes: str = "") -> ImmersionEntry:
        """Record a language immersion moment."""
        entry_id = f"imm_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ImmersionEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            immersion_type=immersion_type or "listening",
            exposure=exposure,
            comprehension=comprehension,
            courage=courage,
            consistency=consistency,
            joy=joy,
            authenticity=authenticity,
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

    def get_immersion_stats(self) -> Dict[str, Any]:
        """Get immersion pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "exposure_sum": 0.0, "comprehension_sum": 0.0, "joy_sum": 0.0})
        for e in self._entries:
            by_type[e.immersion_type]["count"] += 1
            by_type[e.immersion_type]["exposure_sum"] += e.exposure
            by_type[e.immersion_type]["comprehension_sum"] += e.comprehension
            by_type[e.immersion_type]["joy_sum"] += e.joy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_exposure": round(data["exposure_sum"] / count, 2),
                "avg_comprehension": round(data["comprehension_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Exposure analysis
        high_exp = [e for e in self._entries if e.exposure > 0.7]
        low_exp = [e for e in self._entries if e.exposure < 0.4]
        if high_exp and low_exp:
            high_exp_comp = sum(e.comprehension for e in high_exp) / len(high_exp)
            low_exp_comp = sum(e.comprehension for e in low_exp) / len(low_exp)
            high_exp_joy = sum(e.joy for e in high_exp) / len(high_exp)
            low_exp_joy = sum(e.joy for e in low_exp) / len(low_exp)
        else:
            high_exp_comp = 0
            low_exp_comp = 0
            high_exp_joy = 0
            low_exp_joy = 0

        # Courage analysis
        high_cour = [e for e in self._entries if e.courage > 0.7]
        low_cour = [e for e in self._entries if e.courage < 0.4]
        if high_cour and low_cour:
            high_cour_comp = sum(e.comprehension for e in high_cour) / len(high_cour)
            low_cour_comp = sum(e.comprehension for e in low_cour) / len(low_cour)
        else:
            high_cour_comp = 0
            low_cour_comp = 0

        # Avoidance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_exp = sum(e.exposure for e in recent) / len(recent)
            recent_cour = sum(e.courage for e in recent) / len(recent)
            avoidance_risk = recent_exp < 0.3 and recent_cour < 0.3
        else:
            avoidance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "exposure_impact": {
                "high_exposure_comprehension": round(high_exp_comp, 2),
                "low_exposure_comprehension": round(low_exp_comp, 2),
                "high_exposure_joy": round(high_exp_joy, 2),
                "low_exposure_joy": round(low_exp_joy, 2),
            },
            "courage_effect": {
                "high_courage_comprehension": round(high_cour_comp, 2),
                "low_courage_comprehension": round(low_cour_comp, 2),
            },
            "avoidance_risk": avoidance_risk,
            "avg_exposure": round(sum(e.exposure for e in self._entries) / len(self._entries), 2),
            "avg_courage": round(sum(e.courage for e in self._entries) / len(self._entries), 2),
        }

    def get_immersion_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get immersion suggestion."""
        suggestions = [
            "Most people study languages but never learn them. They do apps. They do flashcards. They do grammar exercises. And they wonder why they can't hold a conversation. Why they can't understand a movie. Why they can't think in the language. The answer is simple: they're studying. Not immersing.",
            "Surround yourself. Change your phone. Your computer. Your social media. Your music. Your podcasts. Your shows. To the target language. Not sometimes. Always. The person who lives in the language learns the language. The person who visits occasionally never moves in.",
            "Speak from day one. Not when you're ready. You're never ready. Speak broken. Speak wrong. Speak with mistakes. Every mistake is a lesson. Every correction is a gift. The person who waits to speak perfectly never speaks. The person who speaks badly speaks. And improves. Every day.",
            "Listen to what you love. Not textbooks. Not drills. Songs. Movies. Shows. Podcasts. Audiobooks. About topics you actually care about. The brain learns what it loves. Feed it love. Not obligation.",
            "Think in the language. Not translate. When you see a tree, think the word. When you feel hungry, think the phrase. When you plan your day, plan it in the language. Thinking is the highest form of immersion. And it's free. And it's always available.",
            "Find a conversation partner. Not a teacher. A friend. Someone you want to talk to. About real things. Your life. Their life. The world. Shared interests. The conversation is the classroom. The relationship is the curriculum. The connection is the motivation.",
            "Read what you enjoy. Not graded readers. Not children's books (unless you love them). Articles about your hobbies. Blogs you would read anyway. Books you would read in your native language. Reading is immersion. But only if you actually want to read it.",
            "Embrace the plateau. You will stall. You will feel like you're not improving. You are. The plateau is where the brain is reorganizing. Consolidating. Making connections. Don't quit on the plateau. Celebrate it. It means you're about to jump.",
            "Make mistakes loudly. Not quietly. Not apologetically. Confidently. The person who is afraid to make mistakes is afraid to learn. The person who makes mistakes boldly learns boldly. And is corrected. And improves. And becomes fluent.",
            "The person who immerses in a language is not just learning words. They're learning a world. A culture. A way of thinking. A way of being. They're becoming multilingual. And multilinguality is not just a skill. It's a superpower. It multiplies your world."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One song in the target language. One thought translated. One hello spoken. One show watched. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A daily podcast. A weekly conversation. A phone in the target language. A thought in the new tongue. Medium immersion."
        else:
            capacity_note = "Good capacity. Deep linguistic immersion. A systematic practice of surrounding, speaking, thinking, and living in the language. You have the strength to become fluent."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Language immersion coaching is not about studying harder. It's about living the language. Most people treat language learning as an academic subject. They study grammar. They memorize vocabulary. They take tests. And they never become fluent. Because fluency doesn't come from studying. It comes from immersion. From surrounding yourself with the language. From speaking it imperfectly. From thinking in it. From making it part of your daily life. The work of language immersion coaching is about understanding that your brain is designed to acquire language through exposure and use. Not through drills and exercises. The person who immerses themselves in a language doesn't just learn it. They absorb it. They live it. And eventually, they become it."
        }

    def get_immersion_score(self) -> int:
        """Calculate overall immersion health (0-100)."""
        if not self._entries:
            return 25

        avg_exp = sum(e.exposure for e in self._entries) / len(self._entries)
        avg_comp = sum(e.comprehension for e in self._entries) / len(self._entries)
        avg_cour = sum(e.courage for e in self._entries) / len(self._entries)
        avg_cons = sum(e.consistency for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_exp = sum(e.exposure for e in recent) / len(recent)
            recent_cour = sum(e.courage for e in recent) / len(recent)
        else:
            recent_exp = 0
            recent_cour = 0

        # Avoidance penalty
        avoid_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_exp_30 = sum(e.exposure for e in last_30) / len(last_30)
            recent_cour_30 = sum(e.courage for e in last_30) / len(last_30)
            if recent_exp_30 < 0.3 and recent_cour_30 < 0.3:
                avoid_penalty = 15

        # Type variety
        unique_types = len(set(e.immersion_type for e in self._entries))

        score = (avg_exp * 25) + (avg_comp * 15) + (avg_cour * 15) + (avg_cons * 10) + (avg_joy * 15) + (avg_auth * 10) + (recent_exp * 5) + (recent_cour * 5) + (unique_types * 2) - avoid_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_exposure"] = round(sum(e.exposure for e in self._entries) / len(self._entries), 2)
            self._stats["avg_courage"] = round(sum(e.courage for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_exp = sum(e.exposure for e in recent) / len(recent)
                recent_cour = sum(e.courage for e in recent) / len(recent)
                self._stats["avoidance_risk"] = recent_exp < 0.3 and recent_cour < 0.3
            else:
                self._stats["avoidance_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.language_immersion_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.language_immersion_coach")

    def _log_entry(self, entry: ImmersionEntry):
        try:
            with open(IMMERSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "immersion_type": entry.immersion_type,
                    "exposure": entry.exposure,
                    "courage": entry.courage,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.language_immersion_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lic_instance: Optional[LanguageImmersionCoach] = None
_lic_lock = threading.Lock()


def get_language_immersion_coach() -> LanguageImmersionCoach:
    global _lic_instance
    with _lic_lock:
        if _lic_instance is None:
            _lic_instance = LanguageImmersionCoach()
        return _lic_instance
