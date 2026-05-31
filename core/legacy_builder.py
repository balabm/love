"""
LOVE Legacy Builder — Long-Term Impact Intelligence (Modern AI Pattern)

Most people think about legacy too late. This builder:

1. LEGACY TRACKING
   - Record contributions, creations, and impacts with long-term value
   - Track relationships nurtured and knowledge shared
   - Log values transmitted and communities strengthened

2. PATTERN ANALYSIS
   - Identify the user's legacy themes (wisdom, kindness, creation, advocacy, mentorship)
   - Find where legacy is being built vs neglected
   - Detect legacy gaps and urgencies

3. LEGACY GENERATION
   - Suggest legacy-building actions for today
   - Provide exercises for documenting wisdom and stories
   - Recommend legacy experiments (write a letter, mentor someone, create something lasting)

4. MORTALITY INTEGRATION
   - Help the user act with finite time in mind
   - Track urgency and importance alignment
   - Celebrate legacy milestones

Architecture:
- record_legacy_action(action, theme, impact_scope, longevity): Log action
- get_legacy_stats(): Get legacy pattern analysis
- get_legacy_suggestion(time, theme): Get legacy-building action
- get_legacy_score(): Calculate overall legacy health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "legacy_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEGACY_LOG = DATA_DIR / "legacy.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class LegacyAction:
    """A tracked legacy-building action."""
    action_id: str = ""
    action: str = ""
    theme: str = ""  # wisdom, kindness, creation, advocacy, mentorship, stewardship, love
    impact_scope: str = ""  # self, family, community, world
    longevity: str = ""  # temporary, lasting, permanent
    people_affected: int = 0
    description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class LegacyBuilder:
    """
    Intelligent legacy builder with long-term impact tracking and mortality awareness.
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
        self._actions: deque = deque(maxlen=200)
        self._stats = {
            "total_actions": 0,
            "avg_impact_scope": 0.0,
            "permanent_actions": 0,
            "dominant_theme": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_legacy_action(self, action: str = "", theme: str = "", impact_scope: str = "", longevity: str = "", people_affected: int = 0, description: str = "", notes: str = "") -> LegacyAction:
        """Record a legacy-building action."""
        action_id = f"legacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._actions)}"
        la = LegacyAction(
            action_id=action_id,
            action=action or "unspecified",
            theme=theme or "kindness",
            impact_scope=impact_scope or "community",
            longevity=longevity or "lasting",
            people_affected=people_affected,
            description=description,
            notes=notes,
        )

        with self._lock:
            self._actions.append(la)
            self._stats["total_actions"] += 1
            if longevity == "permanent":
                self._stats["permanent_actions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_action(la)

        return la

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_legacy_stats(self) -> Dict[str, Any]:
        """Get legacy pattern analysis."""
        if not self._actions:
            return {"status": "insufficient_data"}

        # Theme analysis
        by_theme = defaultdict(lambda: {"count": 0, "people": 0, "permanent": 0})
        for a in self._actions:
            by_theme[a.theme]["count"] += 1
            by_theme[a.theme]["people"] += a.people_affected
            if a.longevity == "permanent":
                by_theme[a.theme]["permanent"] += 1

        theme_stats = {}
        for t, data in by_theme.items():
            count = data["count"]
            theme_stats[t] = {
                "count": count,
                "people_affected": data["people"],
                "permanent_actions": data["permanent"],
            }

        dominant = max(theme_stats.items(), key=lambda x: x[1]["count"]) if theme_stats else ("", {})

        # Scope analysis
        scope_scores = {"self": 1, "family": 2, "community": 3, "world": 4}
        by_scope = defaultdict(lambda: {"count": 0, "people": 0})
        for a in self._actions:
            by_scope[a.impact_scope]["count"] += 1
            by_scope[a.impact_scope]["people"] += a.people_affected

        scope_stats = {}
        for s, data in by_scope.items():
            count = data["count"]
            scope_stats[s] = {
                "count": count,
                "people_affected": data["people"],
            }

        # Longevity analysis
        by_longevity = defaultdict(int)
        for a in self._actions:
            by_longevity[a.longevity] += 1

        # Total people affected
        total_people = sum(a.people_affected for a in self._actions)

        # Recent activity
        recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        
        return {
            "total_actions": len(self._actions),
            "theme_stats": theme_stats,
            "dominant_theme": dominant[0],
            "scope_stats": scope_stats,
            "longevity_distribution": dict(by_longevity),
            "total_people_affected": total_people,
            "permanent_actions": sum(1 for a in self._actions if a.longevity == "permanent"),
            "recent_actions": len(recent),
        }

    def get_legacy_suggestion(self, time: float = 30, theme: str = "", urgency: str = "normal") -> Dict[str, Any]:
        """Get legacy-building action."""
        suggestions = {
            "wisdom": [
                "Write down one thing you know now that you didn't know at 20",
                "Record a voice memo of advice for someone you care about",
                "Start a document: 'Things I Believe But Can't Prove'",
                "Teach someone a skill that took you years to learn",
            ],
            "kindness": [
                "Do something generous that will never be traced to you",
                "Pay for someone's coffee anonymously",
                "Write a thank-you note to someone who shaped you",
                "Forgive someone. Tell them, or don't. But mean it.",
            ],
            "creation": [
                "Make something physical that could outlast you",
                "Write a story, poem, or song that captures your perspective",
                "Start a project that solves a small problem beautifully",
                "Document a family recipe with the story behind it",
            ],
            "advocacy": [
                "Speak up for someone who can't speak for themselves",
                "Support a cause with your time, not just money",
                "Have a difficult conversation that could change a system",
                "Write to someone in power about something that matters",
            ],
            "mentorship": [
                "Reach out to someone younger who reminds you of yourself",
                "Offer to mentor someone for 30 minutes a week",
                "Share a failure story that someone needs to hear",
                "Recommend someone for an opportunity they'd never ask for",
            ],
            "stewardship": [
                "Plant something native that supports local ecology",
                "Clean up a shared space without being asked",
                "Repair something instead of replacing it",
                "Reduce your footprint in one measurable way",
            ],
            "love": [
                "Tell someone you love them in a way they'll remember",
                "Create a ritual that your family could continue",
                "Document your love story for future generations",
                "Be present with someone who needs your full attention",
            ],
        }

        if theme and theme in suggestions:
            selected = random.choice(suggestions[theme])
        else:
            all_suggestions = [s for cat in suggestions.values() for s in cat]
            selected = random.choice(all_suggestions)

        if urgency == "high":
            message = "You don't have infinite tomorrows. This matters now."
        elif urgency == "medium":
            message = "Small actions compound. Start the chain today."
        else:
            message = "Legacy isn't grand gestures. It's consistent presence."

        return {
            "action": selected,
            "theme": theme or "mixed",
            "time": time,
            "urgency": urgency,
            "message": message,
            "reflection": "In 100 years, what will remain of this moment?",
        }

    def get_legacy_score(self) -> int:
        """Calculate overall legacy health (0-100)."""
        if not self._actions:
            return 30

        # Impact scope
        scope_scores = {"self": 1, "family": 2, "community": 3, "world": 4}
        avg_scope = sum(scope_scores.get(a.impact_scope, 1) for a in self._actions) / len(self._actions)

        # Longevity
        longevity_scores = {"temporary": 1, "lasting": 2, "permanent": 3}
        avg_longevity = sum(longevity_scores.get(a.longevity, 1) for a in self._actions) / len(self._actions)

        # People affected
        total_people = sum(a.people_affected for a in self._actions)
        people_score = min(30, total_people / 10)

        # Recent activity
        recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        recent_bonus = min(15, len(recent) * 3)

        # Theme variety
        unique_themes = len(set(a.theme for a in self._actions))

        score = (avg_scope / 4 * 20) + (avg_longevity / 3 * 20) + people_score + recent_bonus + (unique_themes * 3)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._actions:
            scope_scores = {"self": 1, "family": 2, "community": 3, "world": 4}
            self._stats["avg_impact_scope"] = round(sum(scope_scores.get(a.impact_scope, 1) for a in self._actions) / len(self._actions), 2)

            by_theme = defaultdict(int)
            for a in self._actions:
                by_theme[a.theme] += 1
            if by_theme:
                self._stats["dominant_theme"] = max(by_theme.items(), key=lambda x: x[1])[0]

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

    def _log_action(self, action: LegacyAction):
        try:
            with open(LEGACY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": action.timestamp,
                    "action": action.action,
                    "theme": action.theme,
                    "scope": action.impact_scope,
                    "longevity": action.longevity,
                    "people": action.people_affected,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_lb_instance: Optional[LegacyBuilder] = None
_lb_lock = threading.Lock()


def get_legacy_builder() -> LegacyBuilder:
    global _lb_instance
    with _lb_lock:
        if _lb_instance is None:
            _lb_instance = LegacyBuilder()
        return _lb_instance
