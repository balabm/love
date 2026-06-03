"""
LOVE Dress for Joy Coach — Joyful Dressing Intelligence (Modern AI Pattern)

Most people dress for obligation. This coach:

1. JOY TRACKING
   - Record dressing moments and their characteristics
   - Track joy types (color, texture, comfort, expression, ritual, celebration)
   - Log joy, confidence, energy, playfulness, and self-love of dressing

2. PATTERN ANALYSIS
   - Identify the user's dressing profile (obligated, dutiful, developing, joyful)
   - Find dressing patterns that create happiness vs drudgery
   - Detect chronic obligation dressing and its costs

3. JOY BUILDING
   - Suggest practices for dressing as an act of self-love
   - Provide frameworks for joyful, intentional dressing
   - Recommend practices for playful, expressive clothing

4. JOYFUL DRESSING MASTERY CULTIVATION
   - Track the correlation between dressing joy and overall wellbeing
   - Alert when obligation is replacing joy
   - Celebrate moments of genuine dressing delight

Architecture:
- record_dress(choice, type, joy, confidence, energy, playfulness, self_love): Log dress
- get_dress_stats(): Get dress pattern analysis
- get_dress_suggestion(capacity, context): Get suggestion
- get_dress_score(): Calculate overall dress health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "dress_for_joy_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DRESS_LOG = DATA_DIR / "dresses.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class DressEntry:
    """A tracked dressing moment."""
    entry_id: str = ""
    choice: str = ""  # what was chosen
    dress_type: str = ""  # color, texture, comfort, expression, ritual, celebration
    joy: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    energy: float = 0.0  # 0-1
    playfulness: float = 0.0  # 0-1
    self_love: float = 0.0  # 0-1
    intention: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DressForJoyCoach:
    """
    Intelligent dress for joy coach with obligation detection and joyful dressing mastery cultivation.
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
            "avg_joy": 0.0,
            "avg_self_love": 0.0,
            "obligation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_dress(self, choice: str = "", dress_type: str = "", joy: float = 0.0, confidence: float = 0.0, energy: float = 0.0, playfulness: float = 0.0, self_love: float = 0.0, intention: float = 0.0, notes: str = "") -> DressEntry:
        """Record a dressing moment."""
        entry_id = f"drj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = DressEntry(
            entry_id=entry_id,
            choice=choice or "unspecified",
            dress_type=dress_type or "color",
            joy=joy,
            confidence=confidence,
            energy=energy,
            playfulness=playfulness,
            self_love=self_love,
            intention=intention,
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

    def get_dress_stats(self) -> Dict[str, Any]:
        """Get dress pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "joy_sum": 0.0, "confidence_sum": 0.0, "energy_sum": 0.0})
        for e in self._entries:
            by_type[e.dress_type]["count"] += 1
            by_type[e.dress_type]["joy_sum"] += e.joy
            by_type[e.dress_type]["confidence_sum"] += e.confidence
            by_type[e.dress_type]["energy_sum"] += e.energy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_confidence": round(data["confidence_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
            }

        # Joy analysis
        high_joy = [e for e in self._entries if e.joy > 0.7]
        low_joy = [e for e in self._entries if e.joy < 0.4]
        if high_joy and low_joy:
            high_joy_conf = sum(e.confidence for e in high_joy) / len(high_joy)
            low_joy_conf = sum(e.confidence for e in low_joy) / len(low_joy)
            high_joy_energy = sum(e.energy for e in high_joy) / len(high_joy)
            low_joy_energy = sum(e.energy for e in low_joy) / len(low_joy)
        else:
            high_joy_conf = 0
            low_joy_conf = 0
            high_joy_energy = 0
            low_joy_energy = 0

        # Playfulness analysis
        high_play = [e for e in self._entries if e.playfulness > 0.7]
        low_play = [e for e in self._entries if e.playfulness < 0.4]
        if high_play and low_play:
            high_play_joy = sum(e.joy for e in high_play) / len(high_play)
            low_play_joy = sum(e.joy for e in low_play) / len(low_play)
        else:
            high_play_joy = 0
            low_play_joy = 0

        # Obligation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_self_love = sum(e.self_love for e in recent) / len(recent)
            obligation_risk = recent_joy < 0.3 and recent_self_love < 0.3
        else:
            obligation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "joy_impact": {
                "high_joy_confidence": round(high_joy_conf, 2),
                "low_joy_confidence": round(low_joy_conf, 2),
                "high_joy_energy": round(high_joy_energy, 2),
                "low_joy_energy": round(low_joy_energy, 2),
            },
            "playfulness_effect": {
                "high_playfulness_joy": round(high_play_joy, 2),
                "low_playfulness_joy": round(low_play_joy, 2),
            },
            "obligation_risk": obligation_risk,
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
            "avg_self_love": round(sum(e.self_love for e in self._entries) / len(self._entries), 2),
        }

    def get_dress_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get dress suggestion."""
        suggestions = [
            "Most people dress because they have to. Because it's expected. Because it's appropriate. Because it's Tuesday. And they wonder why they feel dull. Why they feel heavy. Why they feel like they're getting through the day instead of living it. The answer is in their closet. They're dressing for obligation. Not for joy.",
            "Dress for joy. Not for approval. Not for expectation. Not for the meeting. Not for the commute. For joy. Wear the color that makes you smile. The fabric that feels good on your skin. The shoes that make you want to dance. The accessory that reminds you of something beautiful. Dress like you love yourself. Because you should.",
            "Make dressing a ritual. Not a chore. Light a candle. Play music. Take your time. Feel the fabric. Notice the color. Appreciate the fit. The person who rushes through dressing rushes through self-care. And self-care is not optional. It's foundational.",
            "Wear what makes you feel alive. Not what makes you look appropriate. Not what makes you blend in. What makes you feel like you. The you that is vibrant. The you that is playful. The you that is joyful. That might be bright. That might be soft. That might be bold. That might be simple. It doesn't matter what it is. It matters how it makes you feel.",
            "Experiment with playfulness. A fun sock. A unexpected color. A vintage piece. A handmade accessory. Something that says 'I don't take myself too seriously.' Playfulness is joy made visible. And visible joy is contagious. Including to yourself.",
            "Dress for the energy you want. Not the energy you have. Tired? Wear something that energizes. Anxious? Wear something that grounds. Confident? Wear something that amplifies. Your clothes are tools for state management. Use them intentionally.",
            "Appreciate your body. Dress it with care. Not because it looks a certain way. Because it's yours. Because it carries you through the world. Because it deserves to feel good. The person who dresses their body with love is the person who loves their body. And that is revolutionary.",
            "Celebrate small moments. The perfect outfit for a Tuesday. The cozy sweater for a rainy day. The special piece for no reason at all. Dressing for joy doesn't require a special occasion. It IS the special occasion.",
            "Ignore the rules. Not the safety ones. The fashion ones. The age rules. The body type rules. The color rules. The season rules. They're not rules. They're suggestions. From people who don't know you. Dress for joy. The only rule that matters.",
            "The person who dresses for joy is not frivolous. They're wise. They understand that joy is not a luxury. It's a necessity. That how you feel affects everything you do. And that dressing is one of the most direct ways to influence how you feel. Every single day. Every single morning. Choose joy."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One joyful choice. One color that makes you smile. One fabric that feels good. One moment of dressing with intention. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A dressing ritual. A playful experiment. A self-love practice. An energy shift made with clothes. Medium joy."
        else:
            capacity_note = "Good capacity. Deep joyful dressing work. A systematic practice of dressing as an act of self-love, playfulness, and energy management. You have the strength to wear your joy."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Dressing for joy is not about fashion. It's about self-love. Most people treat dressing as an obligation. Something they have to do. Something they rush through. Something they don't think about. And they wonder why they feel dull. Why they feel disconnected from themselves. Why they feel like they're just getting through the day. The work of dressing for joy coaching is about understanding that what you wear affects how you feel. That dressing is an opportunity for self-expression. For self-care. For playfulness. For energy management. And for joy. The person who dresses with intention and joy is not being frivolous. They're being wise. They understand that joy is not a luxury. It's a necessity. And that one of the most direct ways to create joy is to put it on. Every morning. Every day. Every choice."
        }

    def get_dress_score(self) -> int:
        """Calculate overall dress health (0-100)."""
        if not self._entries:
            return 25

        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_conf = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy for e in self._entries) / len(self._entries)
        avg_play = sum(e.playfulness for e in self._entries) / len(self._entries)
        avg_self_love = sum(e.self_love for e in self._entries) / len(self._entries)
        avg_int = sum(e.intention for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_self_love = sum(e.self_love for e in recent) / len(recent)
        else:
            recent_joy = 0
            recent_self_love = 0

        # Obligation penalty
        oblig_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            recent_self_love_30 = sum(e.self_love for e in last_30) / len(last_30)
            if recent_joy_30 < 0.3 and recent_self_love_30 < 0.3:
                oblig_penalty = 15

        # Type variety
        unique_types = len(set(e.dress_type for e in self._entries))

        score = (avg_joy * 25) + (avg_conf * 10) + (avg_energy * 15) + (avg_play * 15) + (avg_self_love * 20) + (avg_int * 10) + (recent_joy * 5) + (recent_self_love * 5) + (unique_types * 2) - oblig_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)
            self._stats["avg_self_love"] = round(sum(e.self_love for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_joy = sum(e.joy for e in recent) / len(recent)
                recent_self_love = sum(e.self_love for e in recent) / len(recent)
                self._stats["obligation_risk"] = recent_joy < 0.3 and recent_self_love < 0.3
            else:
                self._stats["obligation_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.dress_for_joy_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.dress_for_joy_coach")

    def _log_entry(self, entry: DressEntry):
        try:
            with open(DRESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "choice": entry.choice,
                    "dress_type": entry.dress_type,
                    "joy": entry.joy,
                    "self_love": entry.self_love,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.dress_for_joy_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dfj_instance: Optional[DressForJoyCoach] = None
_dfj_lock = threading.Lock()


def get_dress_for_joy_coach() -> DressForJoyCoach:
    global _dfj_instance
    with _dfj_lock:
        if _dfj_instance is None:
            _dfj_instance = DressForJoyCoach()
        return _dfj_instance
