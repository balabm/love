"""
LOVE Emotional Regulation Coach — Affective Intelligence (Modern AI Pattern)

Most emotional reactions are habits, not choices. This coach:

1. REGULATION TRACKING
   - Record emotional events and regulation attempts
   - Track regulation strategies and their effectiveness
   - Log emotional triggers and their patterns

2. PATTERN ANALYSIS
   - Identify the user's regulation style (suppression, expression, reappraisal, distraction)
   - Find regulation strategies that work for specific emotions
   - Detect regulation gaps (emotions that are poorly managed)

3. SKILL BUILDING
   - Suggest regulation techniques matched to emotion and context
   - Provide reappraisal exercises
   - Recommend somatic regulation practices

4. EMOTIONAL AGILITY
   - Track the ability to feel emotions without being controlled by them
   - Alert when emotional avoidance is becoming problematic
   - Celebrate emotional wisdom moments

Architecture:
- record_emotion(emotion, trigger, intensity, regulation): Log emotion
- get_regulation_stats(): Get regulation pattern analysis
- get_regulation_technique(emotion, context, skill_level): Get technique
- get_regulation_score(): Calculate overall regulation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "emotional_regulation_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMOTION_LOG = DATA_DIR / "emotions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EmotionEntry:
    """A tracked emotion entry."""
    entry_id: str = ""
    emotion: str = ""  # anger, sadness, fear, joy, shame, guilt, envy, anxiety
    trigger: str = ""
    intensity: float = 0.5  # 0-1
    regulation_strategy: str = ""  # suppression, expression, reappraisal, distraction, acceptance, problem_solving
    strategy_effectiveness: float = 0.5  # 0-1
    context: str = ""  # work, home, social, alone, public
    body_sensation: str = ""  # where they felt it
    outcome: str = ""  # what happened
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EmotionalRegulationCoach:
    """
    Intelligent emotional regulation coach with strategy matching and somatic awareness.
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
            "avg_effectiveness": 0.0,
            "dominant_strategy": "",
            "hardest_emotion": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_emotion(self, emotion: str = "", trigger: str = "", intensity: float = 0.5, regulation_strategy: str = "", strategy_effectiveness: float = 0.5, context: str = "", body_sensation: str = "", outcome: str = "", notes: str = "") -> EmotionEntry:
        """Record an emotion entry."""
        entry_id = f"ereg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EmotionEntry(
            entry_id=entry_id,
            emotion=emotion or "unspecified",
            trigger=trigger,
            intensity=intensity,
            regulation_strategy=regulation_strategy or "distraction",
            strategy_effectiveness=strategy_effectiveness,
            context=context or "general",
            body_sensation=body_sensation,
            outcome=outcome,
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

    def get_regulation_stats(self) -> Dict[str, Any]:
        """Get regulation pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Emotion analysis
        by_emotion = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "effectiveness_sum": 0.0})
        for e in self._entries:
            by_emotion[e.emotion]["count"] += 1
            by_emotion[e.emotion]["intensity_sum"] += e.intensity
            by_emotion[e.emotion]["effectiveness_sum"] += e.strategy_effectiveness

        emotion_stats = {}
        for em, data in by_emotion.items():
            count = data["count"]
            emotion_stats[em] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
            }

        hardest_emotion = min(emotion_stats.items(), key=lambda x: x[1]["avg_effectiveness"]) if emotion_stats else ("", {})

        # Strategy analysis
        by_strategy = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for e in self._entries:
            by_strategy[e.regulation_strategy]["count"] += 1
            by_strategy[e.regulation_strategy]["effectiveness_sum"] += e.strategy_effectiveness

        strategy_stats = {}
        for s, data in by_strategy.items():
            count = data["count"]
            strategy_stats[s] = {
                "count": count,
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
            }

        dominant_strategy = max(strategy_stats.items(), key=lambda x: x[1]["count"]) if strategy_stats else ("", {})

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for e in self._entries:
            by_context[e.context]["count"] += 1
            by_context[e.context]["effectiveness_sum"] += e.strategy_effectiveness

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
            }

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "effectiveness_sum": 0.0})
        for e in self._entries:
            by_trigger[e.trigger]["count"] += 1
            by_trigger[e.trigger]["intensity_sum"] += e.intensity
            by_trigger[e.trigger]["effectiveness_sum"] += e.strategy_effectiveness

        trigger_stats = {}
        for t, data in by_trigger.items():
            count = data["count"]
            if count >= 2:
                trigger_stats[t] = {
                    "count": count,
                    "avg_intensity": round(data["intensity_sum"] / count, 2),
                    "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                }

        # Avoidance detection
        suppressed = sum(1 for e in self._entries if e.regulation_strategy == "suppression")
        suppression_rate = suppressed / len(self._entries)
        avoidance_risk = suppression_rate > 0.4

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_effectiveness = sum(e.strategy_effectiveness for e in recent) / len(recent)
        else:
            recent_effectiveness = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_effectiveness = sum(e.strategy_effectiveness for e in older) / len(older)
            trend = recent_effectiveness - older_effectiveness
        else:
            trend = 0

        return {
            "total_entries": len(self._entries),
            "emotion_stats": emotion_stats,
            "hardest_emotion": hardest_emotion[0],
            "strategy_stats": strategy_stats,
            "dominant_strategy": dominant_strategy[0],
            "context_stats": context_stats,
            "trigger_stats": trigger_stats,
            "avoidance_risk": avoidance_risk,
            "suppression_rate": round(suppression_rate, 2),
            "avg_effectiveness": round(sum(e.strategy_effectiveness for e in self._entries) / len(self._entries), 2),
            "trend": round(trend, 2),
            "recent_effectiveness": round(recent_effectiveness, 2),
        }

    def get_regulation_technique(self, emotion: str = "", context: str = "", skill_level: float = 0.5) -> Dict[str, Any]:
        """Get technique."""
        techniques = {
            "anger": [
                "Name it: 'I am angry.' Not 'I am an angry person.' You are not your emotion.",
                "Take a walk. Physical movement helps discharge anger without harm.",
                "Write an angry letter. Don't send it. Burn it.",
                "Ask: 'What boundary was crossed?' Anger often signals a boundary violation.",
            ],
            "sadness": [
                "Allow it. Sadness is not weakness. It's the price of caring.",
                "Reach out. Connection is the antidote to isolation in sadness.",
                "Create something. Art, music, writing. Transform sadness into beauty.",
                "Rest. Sadness is exhausting. Give yourself permission to slow down.",
            ],
            "fear": [
                "Ground yourself. Feet on floor. Name your location. Time and date.",
                "Ask: 'What's the actual risk?' Fear often overestimates danger.",
                "Take one small step. Action reduces fear. Even tiny action counts.",
                "Breathe deeply. Fear lives in shallow breathing. Deep breaths signal safety.",
            ],
            "anxiety": [
                "Worry time: Schedule 15 minutes to worry. Outside that time, write it down and let it go.",
                "5-4-3-2-1 grounding: Name 5 things you see, 4 you hear, 3 you feel, 2 you smell, 1 you taste.",
                "Ask: 'Is this a problem or a fact?' Problems have solutions. Facts need acceptance.",
                "Move your body. Anxiety is energy. Move it through you.",
            ],
            "shame": [
                "Shame thrives in secrecy. Tell one safe person. Shame cannot survive empathy.",
                "Ask: 'Would I say this to a friend?' Treat yourself with the same compassion.",
                "Separate behavior from worth. You made a mistake. You are not a mistake.",
                "Practice self-compassion: 'This is hard. I'm doing my best. That's enough.'",
            ],
            "joy": [
                "Savor it. Don't rush past joy. Linger in it.",
                "Share it. Joy multiplies when shared.",
                "Record it. Write it down. You'll need this memory later.",
                "Let it be imperfect. Joy doesn't need to be perfect to be real.",
            ],
        }

        selected = techniques.get(emotion, techniques["anxiety"])

        if skill_level < 0.3:
            level_note = "Beginner. Start with naming emotions. Everything else builds on awareness."
        elif skill_level < 0.6:
            level_note = "Intermediate. Work on specific strategies for your hardest emotions."
        else:
            level_note = "Advanced. Focus on preemptive regulation. Notice the trigger before the reaction."

        return {
            "emotion": emotion or "general",
            "context": context or "general",
            "skill_level": skill_level,
            "technique": random.choice(selected),
            "level_note": level_note,
            "reminder": "Emotions are data, not directives. Feel them, learn from them, then choose your response. You are not at the mercy of your emotions. You are their interpreter.",
        }

    def get_regulation_score(self) -> int:
        """Calculate overall regulation health (0-100)."""
        if not self._entries:
            return 30

        # Strategy effectiveness
        avg_effectiveness = sum(e.strategy_effectiveness for e in self._entries) / len(self._entries)

        # Low suppression (avoidance is costly)
        suppressed = sum(1 for e in self._entries if e.regulation_strategy == "suppression")
        suppression_rate = suppressed / len(self._entries)

        # Emotion granularity (variety of emotions managed)
        unique_emotions = len(set(e.emotion for e in self._entries))

        # Strategy variety
        unique_strategies = len(set(e.regulation_strategy for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_effectiveness = sum(e.strategy_effectiveness for e in recent) / len(recent)
        else:
            recent_effectiveness = 0

        # Body awareness
        body_aware = [e for e in self._entries if e.body_sensation]
        body_rate = len(body_aware) / len(self._entries)

        # Context variety
        unique_contexts = len(set(e.context for e in self._entries))

        score = (avg_effectiveness * 30) + ((1 - suppression_rate) * 15) + (unique_emotions * 2) + (unique_strategies * 2) + (recent_effectiveness * 15) + (body_rate * 15) + (unique_contexts * 2)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_effectiveness"] = round(sum(e.strategy_effectiveness for e in self._entries) / len(self._entries), 2)

            by_strategy = defaultdict(int)
            for e in self._entries:
                by_strategy[e.regulation_strategy] += 1
            if by_strategy:
                dominant = max(by_strategy.items(), key=lambda x: x[1])
                self._stats["dominant_strategy"] = dominant[0]

            by_emotion = defaultdict(lambda: {"effectiveness": 0.0, "count": 0})
            for e in self._entries:
                by_emotion[e.emotion]["effectiveness"] += e.strategy_effectiveness
                by_emotion[e.emotion]["count"] += 1
            if by_emotion:
                hardest = min(by_emotion.items(), key=lambda x: x[1]["effectiveness"] / max(1, x[1]["count"]))
                self._stats["hardest_emotion"] = hardest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emotional_regulation_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emotional_regulation_coach")

    def _log_entry(self, entry: EmotionEntry):
        try:
            with open(EMOTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "emotion": entry.emotion,
                    "trigger": entry.trigger,
                    "intensity": entry.intensity,
                    "strategy": entry.regulation_strategy,
                    "effectiveness": entry.strategy_effectiveness,
                    "context": entry.context,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emotional_regulation_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_erc_instance: Optional[EmotionalRegulationCoach] = None
_erc_lock = threading.Lock()


def get_emotional_regulation_coach() -> EmotionalRegulationCoach:
    global _erc_instance
    with _erc_lock:
        if _erc_instance is None:
            _erc_instance = EmotionalRegulationCoach()
        return _erc_instance
