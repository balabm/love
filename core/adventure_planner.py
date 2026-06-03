"""
LOVE Adventure Planner — Exploration Intelligence (Modern AI Pattern)

Most people confuse comfort with safety. This planner:

1. ADVENTURE TRACKING
   - Record adventures and their characteristics
   - Track adventure types (physical, intellectual, emotional, social, creative)
   - Log growth outcomes and their effects on courage and capacity

2. PATTERN ANALYSIS
   - Identify the user's adventure profile (avoider, dabbler, explorer, pioneer)
   - Find adventure patterns that create lasting expansion
   - Detect comfort-seeking and its costs

3. ADVENTURE BUILDING
   - Suggest adventures matched to current capacity and growth edge
   - Provide risk assessment and preparation frameworks
   - Recommendation stepping-stone practices

4. EXPLORATION CULTIVATION
   - Track the correlation between adventure and life satisfaction
   - Alert when comfort zone is becoming a prison
   - Celebrate moments of genuine expansion

Architecture:
- record_adventure(adventure, type, challenge, growth): Log adventure
- get_adventure_stats(): Get adventure pattern analysis
- get_adventure_suggestion(capacity, edge, context): Get suggestion
- get_adventure_score(): Calculate overall adventure health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "adventure_planner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ADVENTURE_LOG = DATA_DIR / "adventures.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AdventureEntry:
    """A tracked adventure entry."""
    entry_id: str = ""
    adventure: str = ""  # what was done
    activity: str = ""  # backward-compat alias for adventure
    adventure_type: str = ""  # physical, intellectual, emotional, social, creative
    challenge_level: float = 0.5  # 0-1
    fear_before: float = 0.5  # 0-1
    growth: float = 0.0  # 0-1
    completion: float = 0.0  # 0-1
    preparation: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""
    location: str = ""  # backward-compat
    difficulty: float = 0.0  # backward-compat
    fulfillment: float = 0.0  # backward-compat
    duration: float = 0.0  # backward-compat
    solo: bool = False  # backward-compat
    new_location: bool = False  # backward-compat
    cost: float = 0.0  # backward-compat

    def __post_init__(self):
        if self.activity and not self.adventure:
            self.adventure = self.activity
        elif self.adventure and not self.activity:
            self.activity = self.adventure


class AdventurePlanner:
    """
    Intelligent adventure planner with comfort zone detection and growth optimization.
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
            "avg_challenge": 0.0,
            "comfort_prison_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_adventure(self, adventure: str = "", adventure_type: str = "", challenge_level: float = 0.5, fear_before: float = 0.5, growth: float = 0.0, completion: float = 0.0, preparation: float = 0.5, notes: str = "", *args) -> AdventureEntry:
        """Record an adventure entry. Supports backward-compat extra positional args."""
        entry_id = f"adv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        if args and len(args) >= 3:
            duration = challenge_level
            difficulty = fear_before
            fulfillment = growth
            prep = completion
            solo = preparation
            new_location = notes
            location = args[2] if len(args) > 2 else ""
            note_text = args[3] if len(args) > 3 else ""
            entry = AdventureEntry(
                entry_id=entry_id,
                adventure=adventure or "unspecified",
                activity=adventure or "unspecified",
                adventure_type=adventure_type or "physical",
                challenge_level=float(difficulty) if isinstance(difficulty, (int, float)) else 0.5,
                fear_before=0.5,
                growth=float(fulfillment) if isinstance(fulfillment, (int, float)) else 0.0,
                completion=1.0 if fulfillment and float(fulfillment) > 0.5 else 0.0,
                preparation=float(prep) if isinstance(prep, (int, float)) else 0.5,
                notes=str(note_text) if note_text else "",
                location=str(location) if location else "",
                difficulty=float(difficulty) if isinstance(difficulty, (int, float)) else 0.0,
                fulfillment=float(fulfillment) if isinstance(fulfillment, (int, float)) else 0.0,
                duration=float(duration) if isinstance(duration, (int, float)) else 0.0,
                solo=bool(solo),
                new_location=bool(new_location),
                cost=float(args[1]) if len(args) > 1 and isinstance(args[1], (int, float)) else 0.0,
            )
        else:
            entry = AdventureEntry(
                entry_id=entry_id,
                adventure=adventure or "unspecified",
                activity=adventure or "unspecified",
                adventure_type=adventure_type or "physical",
                challenge_level=challenge_level,
                fear_before=fear_before,
                growth=growth,
                completion=completion,
                preparation=preparation,
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

    def get_adventure_stats(self) -> Dict[str, Any]:
        """Get adventure pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "challenge_sum": 0.0, "growth_sum": 0.0, "fear_sum": 0.0, "completion_sum": 0.0})
        for e in self._entries:
            by_type[e.adventure_type]["count"] += 1
            by_type[e.adventure_type]["challenge_sum"] += e.challenge_level
            by_type[e.adventure_type]["growth_sum"] += e.growth
            by_type[e.adventure_type]["fear_sum"] += e.fear_before
            by_type[e.adventure_type]["completion_sum"] += e.completion

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_challenge": round(data["challenge_sum"] / count, 2),
                "avg_growth": round(data["growth_sum"] / count, 2),
                "avg_fear": round(data["fear_sum"] / count, 2),
                "avg_completion": round(data["completion_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_growth"]) if type_stats else ("", {})

        # Challenge vs growth
        high_challenge = [e for e in self._entries if e.challenge_level > 0.7]
        low_challenge = [e for e in self._entries if e.challenge_level < 0.4]
        if high_challenge and low_challenge:
            high_challenge_growth = sum(e.growth for e in high_challenge) / len(high_challenge)
            low_challenge_growth = sum(e.growth for e in low_challenge) / len(low_challenge)
            high_challenge_fear = sum(e.fear_before for e in high_challenge) / len(high_challenge)
            low_challenge_fear = sum(e.fear_before for e in low_challenge) / len(low_challenge)
        else:
            high_challenge_growth = 0
            low_challenge_growth = 0
            high_challenge_fear = 0
            low_challenge_fear = 0

        # Fear analysis
        high_fear = [e for e in self._entries if e.fear_before > 0.7]
        low_fear = [e for e in self._entries if e.fear_before < 0.4]
        if high_fear and low_fear:
            high_fear_growth = sum(e.growth for e in high_fear) / len(high_fear)
            low_fear_growth = sum(e.growth for e in low_fear) / len(low_fear)
        else:
            high_fear_growth = 0
            low_fear_growth = 0

        # Preparation analysis
        high_prep = [e for e in self._entries if e.preparation > 0.7]
        low_prep = [e for e in self._entries if e.preparation < 0.4]
        if high_prep and low_prep:
            high_prep_completion = sum(e.completion for e in high_prep) / len(high_prep)
            low_prep_completion = sum(e.completion for e in low_prep) / len(low_prep)
        else:
            high_prep_completion = 0
            low_prep_completion = 0

        # Comfort prison detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_challenge = sum(e.challenge_level for e in recent) / len(recent)
            recent_fear = sum(e.fear_before for e in recent) / len(recent)
            comfort_prison_risk = recent_challenge < 0.3 and recent_fear < 0.3
        else:
            comfort_prison_risk = True

        # Recent trend
        if recent:
            recent_growth = sum(e.growth for e in recent) / len(recent)
            recent_completion = sum(e.completion for e in recent) / len(recent)
        else:
            recent_growth = 0
            recent_completion = 0

        older = list(self._entries)[-14:] if len(self._entries) > 14 else []
        if older:
            older_challenge = sum(e.challenge_level for e in older) / len(older)
            older_growth = sum(e.growth for e in older) / len(older)
            challenge_trend = (sum(e.challenge_level for e in recent) / len(recent)) - older_challenge if recent else 0
            growth_trend = (sum(e.growth for e in recent) / len(recent)) - older_growth if recent else 0
        else:
            challenge_trend = 0
            growth_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "challenge_impact": {
                "high_challenge_growth": round(high_challenge_growth, 2),
                "low_challenge_growth": round(low_challenge_growth, 2),
                "high_challenge_fear": round(high_challenge_fear, 2),
                "low_challenge_fear": round(low_challenge_fear, 2),
            },
            "fear_impact": {
                "high_fear_growth": round(high_fear_growth, 2),
                "low_fear_growth": round(low_fear_growth, 2),
            },
            "preparation_impact": {
                "high_prep_completion": round(high_prep_completion, 2),
                "low_prep_completion": round(low_prep_completion, 2),
            },
            "comfort_prison_risk": comfort_prison_risk,
            "avg_challenge": round(sum(e.challenge_level for e in self._entries) / len(self._entries), 2),
            "avg_growth": round(sum(e.growth for e in self._entries) / len(self._entries), 2),
            "challenge_trend": round(challenge_trend, 2),
            "growth_trend": round(growth_trend, 2),
            "recent_growth": round(recent_growth, 2),
        }

    def get_adventure_suggestion(self, capacity: float = 0.5, edge: str = "", context: str = "", solo: bool = False) -> Dict[str, Any]:
        """Get suggestion."""
        suggestions = {
            "physical": [
                "Do something that scares you physically. Not dangerously. Just enough. Rock climbing. Open water swimming. A new sport.",
                "Go somewhere you've never been. On foot. Without GPS. Get lost. Find your way back. That's adventure.",
                "Sign up for a race. Not to win. To finish. The training is the adventure. The finish line is just permission to celebrate.",
            ],
            "intellectual": [
                "Study something completely foreign. A language. A field. A philosophy. Beginner's mind is an adventure.",
                "Attend a conference outside your field. Listen without judging. New connections emerge at boundaries.",
                "Read a book you disagree with. Not to debate. To understand. Intellectual adventure requires leaving your tribe.",
            ],
            "emotional": [
                "Have the conversation you've been avoiding. The hard one. The vulnerable one. Emotional adventure is often the scariest.",
                "Apologize to someone. Sincerely. Without excuse. See what happens. Emotional risk creates the deepest growth.",
                "Express love first. Without knowing if it's returned. That's emotional bungee jumping. And it's worth it.",
            ],
            "social": [
                "Go to an event where you know no one. A meetup. A party. A class. Social adventure builds resilience.",
                "Make a friend from a different generation. Different culture. Different worldview. Expansion lives in difference.",
                "Host something. A dinner. A discussion. A workshop. Creating container for others is its own adventure.",
            ],
            "creative": [
                "Create something you've never created. A song. A painting. A business. The blank page is the adventure.",
                "Share your creation before it's perfect. Publish the draft. Post the sketch. The vulnerability is the adventure.",
                "Collaborate with someone very different from you. Different style. Different process. Friction creates art.",
            ],
            "general": [
                "Adventure is not about danger. It's about uncertainty. If you know the outcome, it's not an adventure. It's a plan.",
                "Start before you're ready. Preparation is good. Over-preparation is procrastination. The adventure begins when you step off.",
                "The best adventures expand your identity. You return different. That's the point. Not the story. The transformation.",
            ],
        }

        selected = suggestions.get(edge, suggestions["general"])

        # Backward-compat: old API passed string risk levels for capacity
        if isinstance(capacity, str):
            risk_map = {"low": 0.2, "micro": 0.1, "medium": 0.5, "high": 0.8, "extreme": 0.95}
            capacity = risk_map.get(capacity.lower(), 0.5)

        if capacity < 0.3:
            capacity_note = "Low capacity. Tiny adventure. Eat at a new restaurant. Take a different route home. Start small."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Medium adventure. Overnight trip. New class. Conversation with a stranger."
        else:
            capacity_note = "Good capacity. Big adventure. The one you've been thinking about for years. Do it. The time is now."

        return {
            "capacity": capacity,
            "edge": edge or "general",
            "context": context or "general",
            "suggestion": random.choice(selected),
            "activity": random.choice(selected),  # backward-compat alias
            "capacity_note": capacity_note,
            "principle": "Most people overestimate risk and underestimate regret. The thing you're afraid of is rarely as bad as you imagine. The regret of not trying is always worse than the memory of failing. Adventure is not about being reckless. It's about being willing. Willing to be uncomfortable. Willing to be bad at something. Willing to be changed. The comfort zone is a beautiful place. But nothing grows there.",
        }

    def get_adventure_score(self) -> int:
        """Calculate overall adventure health (0-100)."""
        if not self._entries:
            return 25

        # Growth and challenge
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)
        avg_challenge = sum(e.challenge_level for e in self._entries) / len(self._entries)

        # Fear management (not too low, not paralyzing)
        avg_fear = sum(e.fear_before for e in self._entries) / len(self._entries)

        # Completion and preparation
        avg_completion = sum(e.completion for e in self._entries) / len(self._entries)
        avg_prep = sum(e.preparation for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.adventure_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_growth = sum(e.growth for e in recent) / len(recent)
            recent_challenge = sum(e.challenge_level for e in recent) / len(recent)
            recent_completion = sum(e.completion for e in recent) / len(recent)
        else:
            recent_growth = 0
            recent_challenge = 0
            recent_completion = 0

        # Comfort prison penalty
        comfort_penalty = 0
        if recent:
            recent_ch = sum(e.challenge_level for e in recent) / len(recent)
            recent_fr = sum(e.fear_before for e in recent) / len(recent)
            if recent_ch < 0.3 and recent_fr < 0.3:
                comfort_penalty = 15

        score = (avg_growth * 30) + (avg_challenge * 15) + (avg_fear * 5) + (avg_completion * 10) + (avg_prep * 5) + (unique_types * 3) + (recent_growth * 15) + (recent_challenge * 10) + (recent_completion * 10) - comfort_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_growth"] = round(sum(e.growth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_challenge"] = round(sum(e.challenge_level for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_challenge = sum(e.challenge_level for e in recent) / len(recent)
                recent_fear = sum(e.fear_before for e in recent) / len(recent)
                self._stats["comfort_prison_risk"] = recent_challenge < 0.3 and recent_fear < 0.3
            else:
                self._stats["comfort_prison_risk"] = True

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.adventure_planner")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.adventure_planner")

    def _log_entry(self, entry: AdventureEntry):
        try:
            with open(ADVENTURE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "adventure": entry.adventure,
                    "adventure_type": entry.adventure_type,
                    "challenge_level": entry.challenge_level,
                    "fear_before": entry.fear_before,
                    "growth": entry.growth,
                    "completion": entry.completion,
                    "preparation": entry.preparation,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.adventure_planner")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ap_instance: Optional[AdventurePlanner] = None
_ap_lock = threading.Lock()


def get_adventure_planner() -> AdventurePlanner:
    global _ap_instance
    with _ap_lock:
        if _ap_instance is None:
            _ap_instance = AdventurePlanner()
        return _ap_instance
