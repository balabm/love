"""
LOVE Gratitude Tracker — Appreciation & Positivity Engine (Modern AI Pattern)

Gratitude is the antidote to stress and negativity. This tracker:

1. GRATITUDE LOGGING
   - Record daily gratitude entries with depth and category
   - Track who/what the user is grateful for
   - Measure gratitude frequency and consistency

2. PATTERN DETECTION
   - Identify recurring sources of gratitude (people, nature, achievements)
   - Detect gratitude gaps (days without appreciation)
   - Find correlations between gratitude and mood/energy

3. POSITIVITY AMPLIFICATION
   - Surface past gratitudes when the user is stressed
   - Suggest new angles for gratitude when entries feel repetitive
   - Celebrate gratitude streaks and milestones

4. SOCIAL CONNECTION
   - Track gratitude directed at specific people
   - Suggest expressing gratitude to neglected connections
   - Strengthen relationships through appreciation

Architecture:
- log_gratitude(what, depth, category): Record gratitude entry
- get_gratitude_insights(days): Get gratitude pattern analysis
- get_gratitude_score(): Get overall gratitude wellbeing score
- get_gratitude_suggestion(): Suggest something to appreciate
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "gratitude_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GRATITUDE_LOG = DATA_DIR / "gratitude_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class GratitudeEntry:
    """A gratitude journal entry."""
    what: str = ""
    depth: float = 0.5  # 0-1 how deeply felt
    category: str = ""  # people, nature, achievement, health, experience, material
    person: str = ""  # if gratitude is directed at someone
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context: str = ""  # work, home, commute, social


class GratitudeTracker:
    """
    Track gratitude patterns and amplify positivity.
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
        self._entries: deque = deque(maxlen=500)
        self._stats = {
            "total_entries": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "avg_depth": 0.5,
            "gratitude_score": 50,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def log_gratitude(self, what: str, depth: float = 0.5, category: str = "", person: str = "", context: str = "") -> GratitudeEntry:
        """Record a gratitude entry."""
        entry = GratitudeEntry(
            what=what,
            depth=depth,
            category=category or "experience",
            person=person,
            context=context,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_streak(entry)
            self._update_stats(entry)

        self._save_stats()
        self._log_entry(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_gratitude_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get gratitude pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self._entries if e.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Category distribution
        category_counts = defaultdict(int)
        for e in recent:
            category_counts[e.category] += 1

        # Person-directed gratitude
        person_gratitude = defaultdict(int)
        for e in recent:
            if e.person:
                person_gratitude[e.person] += 1

        # Depth analysis
        depths = [e.depth for e in recent]
        avg_depth = sum(depths) / len(depths)

        # Streak info
        daily_counts = defaultdict(int)
        for e in recent:
            daily_counts[e.timestamp[:10]] += 1
        avg_per_day = sum(daily_counts.values()) / max(1, len(daily_counts))

        # Detect gratitude gaps
        today = datetime.now().date().isoformat()
        has_today = any(e.timestamp[:10] == today for e in recent)

        return {
            "days_analyzed": len(set(e.timestamp[:10] for e in recent)),
            "total_entries": len(recent),
            "avg_depth": round(avg_depth, 2),
            "avg_per_day": round(avg_per_day, 1),
            "category_distribution": dict(category_counts),
            "top_people": sorted(person_gratitude.items(), key=lambda x: x[1], reverse=True)[:5],
            "current_streak": self._stats["current_streak"],
            "longest_streak": self._stats["longest_streak"],
            "has_entry_today": has_today,
        }

    def get_gratitude_score(self) -> int:
        """Calculate overall gratitude wellbeing score (0-100)."""
        if not self._entries:
            return 50

        recent = list(self._entries)[-30:]
        depths = [e.depth for e in recent]
        daily_counts = defaultdict(int)
        for e in recent:
            daily_counts[e.timestamp[:10]] += 1

        # Consistency score (entries on most days = good)
        days_with_entries = len(daily_counts)
        consistency_score = min(100, days_with_entries * 3.3)

        # Depth score
        avg_depth = sum(depths) / len(depths)
        depth_score = avg_depth * 100

        # Streak bonus
        streak_bonus = min(20, self._stats["current_streak"])

        overall = round(consistency_score * 0.4 + depth_score * 0.4 + streak_bonus)
        self._stats["gratitude_score"] = min(100, overall)
        return min(100, overall)

    def get_gratitude_suggestion(self) -> Dict[str, Any]:
        """Suggest something to be grateful for."""
        # Get recent categories to avoid repetition
        recent_categories = set()
        for e in list(self._entries)[-10:]:
            recent_categories.add(e.category)

        suggestions = {
            "people": "Think of someone who made your life better recently",
            "nature": "Notice something beautiful in your environment right now",
            "health": "Appreciate one thing your body does for you today",
            "achievement": "Acknowledge a small win from today",
            "experience": "Recall a moment today that brought you joy",
            "material": "Appreciate one object that makes your life easier",
            "challenge": "Find the lesson or growth in a recent difficulty",
        }

        # Pick a category not used recently
        for cat, suggestion in suggestions.items():
            if cat not in recent_categories:
                return {"category": cat, "suggestion": suggestion, "fresh": True}

        # If all categories used, return a creative angle
        return {
            "category": "creative",
            "suggestion": "What is something you usually take for granted that you could appreciate today?",
            "fresh": True,
        }

    def get_gratitude_for_person(self, person: str) -> List[Dict[str, Any]]:
        """Get all gratitude entries for a specific person."""
        entries = [e for e in self._entries if e.person == person]
        return [
            {
                "what": e.what,
                "depth": e.depth,
                "timestamp": e.timestamp,
            }
            for e in entries
        ]

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_streak(self, entry: GratitudeEntry):
        """Update gratitude streak."""
        today = datetime.now().date()
        entry_date = datetime.fromisoformat(entry.timestamp).date()

        if self._entries and len(self._entries) > 1:
            last_entry = list(self._entries)[-2] if len(self._entries) > 1 else None
            if last_entry:
                try:
                    last_date = datetime.fromisoformat(last_entry.timestamp).date()
                    if (entry_date - last_date).days == 1:
                        self._stats["current_streak"] += 1
                    elif (entry_date - last_date).days > 1:
                        self._stats["current_streak"] = 1
                except Exception:
                    self._stats["current_streak"] = 1
        else:
            self._stats["current_streak"] = 1

        self._stats["longest_streak"] = max(self._stats["longest_streak"], self._stats["current_streak"])

    def _update_stats(self, entry: GratitudeEntry):
        """Update running statistics."""
        n = self._stats["total_entries"]
        self._stats["avg_depth"] = round(
            (self._stats["avg_depth"] * (n - 1) + entry.depth) / n, 2
        )

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

    def _log_entry(self, entry: GratitudeEntry):
        try:
            with open(GRATITUDE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "what": entry.what,
                    "depth": entry.depth,
                    "category": entry.category,
                    "person": entry.person,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gt_instance: Optional[GratitudeTracker] = None
_gt_lock = threading.Lock()


def get_gratitude_tracker() -> GratitudeTracker:
    global _gt_instance
    with _gt_lock:
        if _gt_instance is None:
            _gt_instance = GratitudeTracker()
        return _gt_instance
