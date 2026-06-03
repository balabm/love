"""
LOVE Emotional Intelligence Trainer — EQ Intelligence (Modern AI Pattern)

Most people react to emotions rather than understand them. This trainer:

1. EMOTION TRACKING
   - Record emotional experiences and their context
   - Track emotional granularity (how precisely emotions are identified)
   - Log emotional regulation strategies and their effectiveness

2. PATTERN ANALYSIS
   - Identify emotional triggers and their patterns
   - Find regulation strategies that work for specific emotions
   - Detect emotional blind spots (emotions that are avoided or denied)

3. EQ SKILL BUILDING
   - Suggest emotion-labeling exercises for better granularity
   - Provide regulation technique recommendations
   - Recommend empathy and social awareness practices

4. RELATIONSHIP TRACKING
   - Track the correlation between EQ and relationship quality
   - Alert when emotional patterns are damaging relationships
   - Celebrate emotional growth moments

Architecture:
- record_emotion(emotion, trigger, regulation, effectiveness): Log emotion
- get_eq_stats(): Get EQ pattern analysis
- get_eq_exercise(skill_area, current_level): Get exercise
- get_eq_score(): Calculate overall EQ health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "emotional_intelligence_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMOTION_LOG = DATA_DIR / "emotions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EmotionEntry:
    """A tracked emotion entry."""
    entry_id: str = ""
    emotion: str = ""  # specific emotion word
    emotion_category: str = ""  # joy, sadness, anger, fear, surprise, disgust, love
    trigger: str = ""
    intensity: float = 0.5  # 0-1
    regulation_strategy: str = ""  # what they did
    regulation_effectiveness: float = 0.0  # 0-1
    social_context: str = ""  # alone, family, work, friend, public
    body_sensation: str = ""  # where they felt it
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EmotionalIntelligenceTrainer:
    """
    Intelligent EQ trainer with granularity analysis and regulation skill building.
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
            "avg_regulation": 0.0,
            "granularity_score": 0.0,
            "dominant_emotion": "",
            "best_strategy": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_emotion(self, emotion: str = "", emotion_category: str = "", trigger: str = "", intensity: float = 0.5, regulation_strategy: str = "", regulation_effectiveness: float = 0.0, social_context: str = "", body_sensation: str = "", notes: str = "") -> EmotionEntry:
        """Record an emotion entry."""
        entry_id = f"eq_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EmotionEntry(
            entry_id=entry_id,
            emotion=emotion or "unspecified",
            emotion_category=emotion_category or "general",
            trigger=trigger,
            intensity=intensity,
            regulation_strategy=regulation_strategy,
            regulation_effectiveness=regulation_effectiveness,
            social_context=social_context,
            body_sensation=body_sensation,
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

    def get_eq_stats(self) -> Dict[str, Any]:
        """Get EQ pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Emotion analysis
        by_emotion = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "regulation_sum": 0.0})
        for e in self._entries:
            by_emotion[e.emotion]["count"] += 1
            by_emotion[e.emotion]["intensity_sum"] += e.intensity
            by_emotion[e.emotion]["regulation_sum"] += e.regulation_effectiveness

        emotion_stats = {}
        for em, data in by_emotion.items():
            count = data["count"]
            emotion_stats[em] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_regulation": round(data["regulation_sum"] / count, 2),
            }

        dominant = max(emotion_stats.items(), key=lambda x: x[1]["count"]) if emotion_stats else ("", {})

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "regulation_sum": 0.0})
        for e in self._entries:
            by_category[e.emotion_category]["count"] += 1
            by_category[e.emotion_category]["intensity_sum"] += e.intensity
            by_category[e.emotion_category]["regulation_sum"] += e.regulation_effectiveness

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            category_stats[c] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_regulation": round(data["regulation_sum"] / count, 2),
            }

        # Strategy analysis
        by_strategy = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for e in self._entries:
            if e.regulation_strategy:
                by_strategy[e.regulation_strategy]["count"] += 1
                by_strategy[e.regulation_strategy]["effectiveness_sum"] += e.regulation_effectiveness

        strategy_stats = {}
        for s, data in by_strategy.items():
            count = data["count"]
            if count >= 2:
                strategy_stats[s] = {
                    "count": count,
                    "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                }

        best_strategy = max(strategy_stats.items(), key=lambda x: x[1]["avg_effectiveness"]) if strategy_stats else ("", {})

        # Granularity (how many distinct emotion words vs generic categories)
        unique_emotions = len(set(e.emotion for e in self._entries))
        unique_categories = len(set(e.emotion_category for e in self._entries))
        granularity = unique_emotions / max(1, unique_categories)

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for e in self._entries:
            if e.trigger:
                by_trigger[e.trigger]["count"] += 1
                by_trigger[e.trigger]["intensity_sum"] += e.intensity

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            if count >= 2:
                trigger_stats[tr] = {
                    "count": count,
                    "avg_intensity": round(data["intensity_sum"] / count, 2),
                }

        # Blind spots (categories with high intensity but low regulation)
        blind_spots = [c for c, d in category_stats.items() if d["avg_intensity"] > 0.6 and d["avg_regulation"] < 0.3]

        return {
            "total_entries": len(self._entries),
            "emotion_stats": emotion_stats,
            "dominant_emotion": dominant[0],
            "category_stats": category_stats,
            "strategy_stats": strategy_stats,
            "best_strategy": best_strategy[0],
            "granularity": round(granularity, 2),
            "trigger_stats": trigger_stats,
            "blind_spots": blind_spots,
            "avg_regulation": round(sum(e.regulation_effectiveness for e in self._entries) / len(self._entries), 2),
        }

    def get_eq_exercise(self, skill_area: str = "", current_level: float = 0.5) -> Dict[str, Any]:
        """Get exercise."""
        exercises = {
            "granularity": [
                "Instead of 'bad', try: sad, lonely, anxious, disappointed, frustrated, weary",
                "Keep an emotion journal. Use 3 specific words daily.",
                "Read emotion wheel. Pick 2 new emotions to notice this week.",
            ],
            "regulation": [
                "Name it to tame it. Say the emotion aloud. It reduces amygdala activation.",
                "Box breathing: 4 counts in, hold, out, hold. Do 5 rounds.",
                "Temperature change: Cold water on face, or hot tea. Physiological reset.",
                "Movement: 5 minutes of walking, stretching, or shaking. Emotion lives in body.",
            ],
            "empathy": [
                "Before responding, ask: 'What might they be feeling right now?'",
                "Reflect back: 'It sounds like you're feeling...' Let them correct you.",
                "Ask one feeling question per conversation: 'How did that feel for you?'",
            ],
            "social_awareness": [
                "In a group, notice who's speaking and who's silent. Check in with the quiet ones.",
                "Watch for micro-expressions. What's the gap between what they say and what they show?",
                "Before a meeting, set intention: 'I'll notice emotions, not just content.'",
            ],
        }

        selected = exercises.get(skill_area, exercises["granularity"])

        if current_level < 0.3:
            level_note = "Beginner. Start with naming emotions accurately. Everything else builds on this."
        elif current_level < 0.6:
            level_note = "Intermediate. Focus on regulation. You can name emotions; now manage them."
        else:
            level_note = "Advanced. Work on empathy and social awareness. Your EQ can benefit others now."

        return {
            "skill_area": skill_area or "general",
            "current_level": current_level,
            "exercise": random.choice(selected),
            "level_note": level_note,
            "daily_practice": "Three times today, pause and name your emotion before acting on it.",
        }

    def get_eq_score(self) -> int:
        """Calculate overall EQ health (0-100)."""
        if not self._entries:
            return 35

        # Granularity
        unique_emotions = len(set(e.emotion for e in self._entries))
        unique_categories = len(set(e.emotion_category for e in self._entries))
        granularity = unique_emotions / max(1, unique_categories)

        # Regulation effectiveness
        avg_regulation = sum(e.regulation_effectiveness for e in self._entries) / len(self._entries)

        # Body awareness
        body_aware = [e for e in self._entries if e.body_sensation]
        body_rate = len(body_aware) / len(self._entries)

        # Strategy variety
        unique_strategies = len(set(e.regulation_strategy for e in self._entries if e.regulation_strategy))

        # Recent trend
        recent = list(self._entries)[-14:]
        recent_regulation = sum(e.regulation_effectiveness for e in recent) / len(recent)
        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_regulation = sum(e.regulation_effectiveness for e in older) / len(older)
            trend = recent_regulation - older_regulation
        else:
            trend = 0

        # Social context awareness
        social_contexts = set(e.social_context for e in self._entries)

        score = (granularity * 15) + (avg_regulation * 25) + (body_rate * 15) + (unique_strategies * 2) + (trend * 15) + (len(social_contexts) * 2) + 10
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_regulation"] = round(sum(e.regulation_effectiveness for e in self._entries) / len(self._entries), 2)

            unique_emotions = len(set(e.emotion for e in self._entries))
            unique_categories = len(set(e.emotion_category for e in self._entries))
            self._stats["granularity_score"] = round(unique_emotions / max(1, unique_categories), 2)

            by_emotion = defaultdict(lambda: {"count": 0, "intensity": 0.0})
            for e in self._entries:
                by_emotion[e.emotion]["count"] += 1
                by_emotion[e.emotion]["intensity"] += e.intensity
            if by_emotion:
                dominant = max(by_emotion.items(), key=lambda x: x[1]["count"])
                self._stats["dominant_emotion"] = dominant[0]

            by_strategy = defaultdict(lambda: {"count": 0, "effectiveness": 0.0})
            for e in self._entries:
                if e.regulation_strategy:
                    by_strategy[e.regulation_strategy]["count"] += 1
                    by_strategy[e.regulation_strategy]["effectiveness"] += e.regulation_effectiveness
            if by_strategy:
                best = max(by_strategy.items(), key=lambda x: x[1]["effectiveness"] / max(1, x[1]["count"]))
                self._stats["best_strategy"] = best[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emotional_intelligence_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emotional_intelligence_trainer")

    def _log_entry(self, entry: EmotionEntry):
        try:
            with open(EMOTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "emotion": entry.emotion,
                    "category": entry.emotion_category,
                    "intensity": entry.intensity,
                    "regulation": entry.regulation_effectiveness,
                    "strategy": entry.regulation_strategy,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emotional_intelligence_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_eq_instance: Optional[EmotionalIntelligenceTrainer] = None
_eq_lock = threading.Lock()


def get_emotional_intelligence_trainer() -> EmotionalIntelligenceTrainer:
    global _eq_instance
    with _eq_lock:
        if _eq_instance is None:
            _eq_instance = EmotionalIntelligenceTrainer()
        return _eq_instance
