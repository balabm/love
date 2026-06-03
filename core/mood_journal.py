"""
LOVE Mood Journal — Emotional Pattern Tracker (Modern AI Pattern)

Most mood tracking is passive logging. This journal:

1. MOOD LOGGING
   - Record mood with intensity, triggers, and context
   - Track mood shifts throughout the day
   - Identify mood anchors (people, places, activities that shift mood)

2. PATTERN DETECTION
   - Find cyclical mood patterns (weekly, monthly, seasonal)
   - Detect what precedes mood drops (sleep, social, work patterns)
   - Identify what reliably improves mood

3. EMOTIONAL INTELLIGENCE
   - Calculate emotional range (how much mood varies)
   - Track emotional resilience (recovery speed from bad moods)
   - Detect emotional burnout before it happens

4. PROACTIVE SUPPORT
   - Suggest mood-lifting activities based on proven personal patterns
   - Warn when mood patterns suggest burnout risk
   - Celebrate emotional growth and resilience improvements

Architecture:
- log_mood(mood, intensity, triggers): Record mood entry
- get_mood_insights(days): Get mood pattern analysis
- get_mood_score(): Get overall emotional wellbeing score
- get_support_suggestion(): Suggest mood support activity
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "mood_journal"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MOOD_LOG = DATA_DIR / "mood_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MoodEntry:
    """A mood journal entry."""
    mood: str = ""  # happy, sad, anxious, calm, excited, tired, angry, grateful
    intensity: float = 0.5  # 0-1
    triggers: List[str] = field(default_factory=list)
    context: str = ""  # work, home, social, alone, commute
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    energy_level: float = 0.5
    notes: str = ""


class MoodJournal:
    """
    Track mood patterns and provide emotional intelligence.
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
            "avg_intensity": 0.5,
            "emotional_range": 0.0,
            "resilience_score": 50,
            "burnout_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def log_mood(self, mood: str, intensity: float = 0.5, triggers: Optional[List[str]] = None, context: str = "", energy_level: float = 0.5, notes: str = "") -> MoodEntry:
        """Record a mood entry."""
        entry = MoodEntry(
            mood=mood,
            intensity=intensity,
            triggers=triggers or [],
            context=context,
            energy_level=energy_level,
            notes=notes,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_stats(entry)

        self._save_stats()
        self._log_entry(entry)

        # Check for significant mood events
        if intensity > 0.8 and mood in ["happy", "excited", "grateful"]:
            self._celebrate_positive_mood(entry)
        elif intensity > 0.7 and mood in ["sad", "anxious", "angry"]:
            self._alert_negative_mood(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_mood_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get mood pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self._entries if e.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Mood frequency
        mood_counts = defaultdict(int)
        for e in recent:
            mood_counts[e.mood] += 1

        # Trigger analysis
        trigger_impact = defaultdict(lambda: {"count": 0, "avg_intensity": 0.0})
        for e in recent:
            for trigger in e.triggers:
                trigger_impact[trigger]["count"] += 1
                trigger_impact[trigger]["avg_intensity"] += e.intensity

        for trigger in trigger_impact:
            trigger_impact[trigger]["avg_intensity"] = round(
                trigger_impact[trigger]["avg_intensity"] / trigger_impact[trigger]["count"], 2
            )

        # Context analysis
        context_scores = defaultdict(list)
        for e in recent:
            context_scores[e.context].append(e.intensity if e.mood in ["happy", "calm", "grateful", "excited"] else -e.intensity)

        best_context = max(context_scores.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if context_scores else ""
        worst_context = min(context_scores.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if context_scores else ""

        # Emotional range
        intensities = [e.intensity for e in recent]
        emotional_range = max(intensities) - min(intensities) if intensities else 0

        # Resilience (recovery from negative moods)
        resilience = self._calculate_resilience(recent)

        # Burnout risk detection
        negative_count = sum(1 for e in recent if e.mood in ["sad", "anxious", "tired", "angry"])
        burnout_risk = negative_count > len(recent) * 0.6 and len(recent) > 5

        return {
            "days_analyzed": len(set(e.timestamp[:10] for e in recent)),
            "total_entries": len(recent),
            "mood_distribution": dict(mood_counts),
            "most_common_mood": max(mood_counts.items(), key=lambda x: x[1])[0] if mood_counts else "",
            "top_triggers": sorted(trigger_impact.items(), key=lambda x: x[1]["count"], reverse=True)[:5],
            "best_context": best_context,
            "worst_context": worst_context,
            "emotional_range": round(emotional_range, 2),
            "resilience_score": resilience,
            "burnout_risk": burnout_risk,
        }

    def get_mood_score(self) -> int:
        """Calculate overall emotional wellbeing score (0-100)."""
        if not self._entries:
            return 50

        recent = list(self._entries)[-30:]
        positive = sum(1 for e in recent if e.mood in ["happy", "calm", "grateful", "excited"])
        negative = sum(1 for e in recent if e.mood in ["sad", "anxious", "tired", "angry"])

        # Positive ratio score
        total_rated = positive + negative
        if total_rated == 0:
            return 50
        pos_ratio = positive / total_rated
        pos_score = pos_ratio * 100

        # Intensity balance (high positive intensity is good, high negative is bad)
        pos_intensity = sum(e.intensity for e in recent if e.mood in ["happy", "calm", "grateful", "excited"])
        neg_intensity = sum(e.intensity for e in recent if e.mood in ["sad", "anxious", "tired", "angry"])
        balance_score = 50 + (pos_intensity - neg_intensity) * 25
        balance_score = max(0, min(100, balance_score))

        # Resilience bonus
        resilience = self._calculate_resilience(recent)

        overall = round(pos_score * 0.5 + balance_score * 0.3 + resilience * 0.2)
        return min(100, overall)

    def get_support_suggestion(self) -> Dict[str, Any]:
        """Suggest a mood support activity based on patterns."""
        insights = self.get_mood_insights(14)

        if insights.get("burnout_risk"):
            return {
                "activity": "Take a full day off. Rest is not optional right now.",
                "urgency": "high",
                "reason": "Burnout risk detected from mood patterns",
            }

        # Find what improves mood
        positive_triggers = []
        for trigger, stats in insights.get("top_triggers", []):
            if stats["avg_intensity"] > 0.6:
                positive_triggers.append(trigger)

        if "walk" in positive_triggers or "nature" in positive_triggers:
            return {
                "activity": "Go for a walk outside. Nature improves your mood.",
                "urgency": "medium",
                "reason": "Nature walks reliably improve your mood",
            }
        elif "music" in positive_triggers or "song" in positive_triggers:
            return {
                "activity": "Listen to your favorite music for 10 minutes.",
                "urgency": "medium",
                "reason": "Music is a proven mood lifter for you",
            }
        elif "friend" in positive_triggers or "social" in positive_triggers:
            return {
                "activity": "Call or message a friend.",
                "urgency": "medium",
                "reason": "Social connection improves your mood",
            }
        else:
            return {
                "activity": "Try a 5-minute breathing exercise or short walk.",
                "urgency": "low",
                "reason": "General mood support recommendation",
            }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _calculate_resilience(self, entries: List[MoodEntry]) -> int:
        """Calculate emotional resilience score."""
        if len(entries) < 5:
            return 50

        # Count how quickly mood recovers from negative to positive
        recoveries = 0
        recovery_times = []

        for i in range(1, len(entries)):
            prev = entries[i-1]
            curr = entries[i]
            if prev.mood in ["sad", "anxious", "angry"] and curr.mood in ["happy", "calm", "grateful"]:
                recoveries += 1
                try:
                    t1 = datetime.fromisoformat(prev.timestamp)
                    t2 = datetime.fromisoformat(curr.timestamp)
                    hours = (t2 - t1).total_seconds() / 3600
                    recovery_times.append(hours)
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.mood_journal")

        if not recovery_times:
            return 50

        avg_recovery = sum(recovery_times) / len(recovery_times)
        # Faster recovery = higher resilience (max 100 at < 2 hours, min 0 at > 24 hours)
        resilience = max(0, min(100, 100 - (avg_recovery - 2) * 4))
        return round(resilience)

    def _update_stats(self, entry: MoodEntry):
        """Update running statistics."""
        n = self._stats["total_entries"]
        self._stats["avg_intensity"] = round(
            (self._stats["avg_intensity"] * (n - 1) + entry.intensity) / n, 2
        )

    def _celebrate_positive_mood(self, entry: MoodEntry):
        """Celebrate significant positive mood."""
        try:
            from core.neural_bus import get_neural_bus
            get_neural_bus().publish(
                event_type="positive_mood",
                domain="wellness",
                payload={
                    "mood": entry.mood,
                    "intensity": entry.intensity,
                    "triggers": entry.triggers,
                },
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mood_journal")

    def _alert_negative_mood(self, entry: MoodEntry):
        """Alert about significant negative mood."""
        try:
            from core.neural_bus import get_neural_bus
            get_neural_bus().publish(
                event_type="negative_mood_alert",
                domain="wellness",
                payload={
                    "mood": entry.mood,
                    "intensity": entry.intensity,
                    "triggers": entry.triggers,
                    "context": entry.context,
                },
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mood_journal")

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "entries": [{
                    "mood": e.mood,
                    "intensity": e.intensity,
                    "triggers": e.triggers,
                    "context": e.context,
                    "timestamp": e.timestamp,
                    "energy_level": e.energy_level,
                    "notes": e.notes,
                } for e in self._entries],
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mood_journal")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for e in data.get("entries", []):
                    self._entries.append(MoodEntry(**e))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mood_journal")

    def _log_entry(self, entry: MoodEntry):
        try:
            with open(MOOD_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "mood": entry.mood,
                    "intensity": entry.intensity,
                    "context": entry.context,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.mood_journal")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mj_instance: Optional[MoodJournal] = None
_mj_lock = threading.Lock()


def get_mood_journal() -> MoodJournal:
    global _mj_instance
    with _mj_lock:
        if _mj_instance is None:
            _mj_instance = MoodJournal()
        return _mj_instance
