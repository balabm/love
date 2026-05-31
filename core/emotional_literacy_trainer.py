"""
LOVE Emotional Literacy Trainer — Emotion Intelligence (Modern AI Pattern)

Most people feel emotions without understanding them. This trainer:

1. EMOTION TRACKING
   - Record emotional experiences and their characteristics
   - Track emotion types (joy, sadness, anger, fear, shame, envy, love)
   - Log awareness, labeling, and regulation of emotions

2. PATTERN ANALYSIS
   - Identify the user's emotional literacy profile (literate, alexithymic, reactive, integrated)
   - Find emotional patterns that lead to wise action vs impulsive reaction
   - Detect emotional suppression and its costs

3. LITERACY BUILDING
   - Suggest practices for recognizing and naming emotions
   - Provide frameworks for understanding emotional triggers
   - Recommend regulation strategies matched to emotion type

4. EMOTIONAL WISDOM CULTIVATION
   - Track the correlation between emotional awareness and decision quality
   - Alert when emotions are being acted upon without understanding
   - Celebrate moments of genuine emotional intelligence

Architecture:
- record_emotion(emotion, type, awareness, labeling, regulation): Log emotion
- get_emotion_stats(): Get emotion pattern analysis
- get_emotion_suggestion(capacity, context): Get suggestion
- get_emotion_score(): Calculate overall emotional literacy
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

DATA_DIR = Path(__file__).parent.parent / "data" / "emotional_literacy_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMOTION_LOG = DATA_DIR / "emotions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EmotionEntry:
    """A tracked emotional experience."""
    entry_id: str = ""
    emotion: str = ""  # what was felt
    emotion_type: str = ""  # joy, sadness, anger, fear, shame, envy, love, anxiety
    awareness: float = 0.0  # 0-1
    labeling: float = 0.0  # 0-1
    regulation: float = 0.0  # 0-1
    trigger: str = ""  # what triggered it
    action: float = 0.0  # 0-1 how well action aligned with values
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class EmotionalLiteracyTrainer:
    """
    Intelligent emotional literacy trainer with awareness detection and wisdom cultivation.
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
            "avg_awareness": 0.0,
            "avg_regulation": 0.0,
            "suppression_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_emotion(self, emotion: str = "", emotion_type: str = "", awareness: float = 0.0, labeling: float = 0.0, regulation: float = 0.0, trigger: str = "", action: float = 0.0, notes: str = "") -> EmotionEntry:
        """Record an emotional experience."""
        entry_id = f"emt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EmotionEntry(
            entry_id=entry_id,
            emotion=emotion or "unspecified",
            emotion_type=emotion_type or "general",
            awareness=awareness,
            labeling=labeling,
            regulation=regulation,
            trigger=trigger or "unspecified",
            action=action,
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

    def get_emotion_stats(self) -> Dict[str, Any]:
        """Get emotion pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "awareness_sum": 0.0, "regulation_sum": 0.0, "action_sum": 0.0})
        for e in self._entries:
            by_type[e.emotion_type]["count"] += 1
            by_type[e.emotion_type]["awareness_sum"] += e.awareness
            by_type[e.emotion_type]["regulation_sum"] += e.regulation
            by_type[e.emotion_type]["action_sum"] += e.action

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_awareness": round(data["awareness_sum"] / count, 2),
                "avg_regulation": round(data["regulation_sum"] / count, 2),
                "avg_action": round(data["action_sum"] / count, 2),
            }

        # Awareness analysis
        high_aware = [e for e in self._entries if e.awareness > 0.7]
        low_aware = [e for e in self._entries if e.awareness < 0.4]
        if high_aware and low_aware:
            high_aware_reg = sum(e.regulation for e in high_aware) / len(high_aware)
            low_aware_reg = sum(e.regulation for e in low_aware) / len(low_aware)
            high_aware_act = sum(e.action for e in high_aware) / len(high_aware)
            low_aware_act = sum(e.action for e in low_aware) / len(low_aware)
        else:
            high_aware_reg = 0
            low_aware_reg = 0
            high_aware_act = 0
            low_aware_act = 0

        # Labeling analysis
        high_label = [e for e in self._entries if e.labeling > 0.7]
        low_label = [e for e in self._entries if e.labeling < 0.4]
        if high_label and low_label:
            high_label_reg = sum(e.regulation for e in high_label) / len(high_label)
            low_label_reg = sum(e.regulation for e in low_label) / len(low_label)
        else:
            high_label_reg = 0
            low_label_reg = 0

        # Suppression risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_label = sum(e.labeling for e in recent) / len(recent)
            recent_reg = sum(e.regulation for e in recent) / len(recent)
            suppression_risk = recent_aware < 0.3 and recent_label < 0.3 and recent_reg < 0.3
        else:
            suppression_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "awareness_impact": {
                "high_awareness_regulation": round(high_aware_reg, 2),
                "low_awareness_regulation": round(low_aware_reg, 2),
                "high_awareness_action": round(high_aware_act, 2),
                "low_awareness_action": round(low_aware_act, 2),
            },
            "labeling_effect": {
                "high_labeling_regulation": round(high_label_reg, 2),
                "low_labeling_regulation": round(low_label_reg, 2),
            },
            "suppression_risk": suppression_risk,
            "avg_awareness": round(sum(e.awareness for e in self._entries) / len(self._entries), 2),
            "avg_regulation": round(sum(e.regulation for e in self._entries) / len(self._entries), 2),
        }

    def get_emotion_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get emotion suggestion."""
        suggestions = [
            "Name it to tame it. When you feel something intense, name the emotion. 'I am angry.' 'I am sad.' 'I am afraid.' Naming creates distance. Distance creates choice.",
            "Emotions are data, not directives. They tell you something is important. They don't tell you what to do about it. Feel the emotion. Then choose the action.",
            "Where do you feel it in your body? The chest. The stomach. The throat. The jaw. Emotions are physical. Tune into the body. It knows before the mind does.",
            "Ask: what need is beneath this emotion? Anger often masks hurt. Shame often masks fear of rejection. Find the need. Address the need.",
            "Don't act on emotions in the first 90 seconds. The physiological wave lasts 90 seconds. After that, you're choosing. Wait. Breathe. Then decide.",
            "All emotions are valid. Not all emotional expressions are helpful. You can be angry without being cruel. You can be sad without being paralyzed. You can be afraid without being frozen.",
            "Emotions that are suppressed don't disappear. They find other exits. Somatic symptoms. Irritability. Projection. The body keeps the score. Feel them. Process them.",
            "Develop an emotional vocabulary. Not just 'bad' or 'stressed.' Anxious. Disappointed. Resentful. Lonely. Envious. Guilty. The more precise your vocabulary, the more precise your understanding.",
            "Your emotions are not who you are. You are not your anger. You are not your sadness. You are the one who feels them. The witness. The observer. The one who chooses.",
            "Emotional literacy is not the absence of difficult emotions. It's the ability to navigate them. To feel them fully without being controlled by them. To use them as information rather than instructions."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One breath. One name. One moment of noticing. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A journaling session. A reflection. A conversation about feelings. Medium emotional work."
        else:
            capacity_note = "Good capacity. Deep emotional exploration. Pattern analysis. Healing work. You have the strength for real emotional growth."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Emotions are the native language of the body. They're not mistakes. They're not weaknesses. They're signals. Every emotion carries information about what you need, what you value, what you're afraid of, what you want. The person who ignores their emotions is flying blind. The person who is controlled by their emotions is in a tailspin. The person who understands their emotions has a navigation system. Emotional literacy is not about becoming emotionless. It's about becoming fluent in your own internal landscape. It's about being able to read the signals, understand the meanings, and choose your responses. That is freedom. That is power. That is wisdom."
        }

    def get_emotion_score(self) -> int:
        """Calculate overall emotional literacy (0-100)."""
        if not self._entries:
            return 25

        avg_aware = sum(e.awareness for e in self._entries) / len(self._entries)
        avg_label = sum(e.labeling for e in self._entries) / len(self._entries)
        avg_reg = sum(e.regulation for e in self._entries) / len(self._entries)
        avg_action = sum(e.action for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_reg = sum(e.regulation for e in recent) / len(recent)
        else:
            recent_aware = 0
            recent_reg = 0

        # Suppression penalty
        suppress_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_aware_30 = sum(e.awareness for e in last_30) / len(last_30)
            recent_label_30 = sum(e.labeling for e in last_30) / len(last_30)
            recent_reg_30 = sum(e.regulation for e in last_30) / len(last_30)
            if recent_aware_30 < 0.3 and recent_label_30 < 0.3 and recent_reg_30 < 0.3:
                suppress_penalty = 15

        # Type variety
        unique_types = len(set(e.emotion_type for e in self._entries))

        score = (avg_aware * 25) + (avg_label * 15) + (avg_reg * 25) + (avg_action * 15) + (recent_aware * 10) + (recent_reg * 5) + (unique_types * 2) - suppress_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_awareness"] = round(sum(e.awareness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_regulation"] = round(sum(e.regulation for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_aware = sum(e.awareness for e in recent) / len(recent)
                recent_label = sum(e.labeling for e in recent) / len(recent)
                recent_reg = sum(e.regulation for e in recent) / len(recent)
                self._stats["suppression_risk"] = recent_aware < 0.3 and recent_label < 0.3 and recent_reg < 0.3
            else:
                self._stats["suppression_risk"] = False

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

    def _log_entry(self, entry: EmotionEntry):
        try:
            with open(EMOTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "emotion": entry.emotion,
                    "emotion_type": entry.emotion_type,
                    "awareness": entry.awareness,
                    "regulation": entry.regulation,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_elt_instance: Optional[EmotionalLiteracyTrainer] = None
_elt_lock = threading.Lock()


def get_emotional_literacy_trainer() -> EmotionalLiteracyTrainer:
    global _elt_instance
    with _elt_lock:
        if _elt_instance is None:
            _elt_instance = EmotionalLiteracyTrainer()
        return _elt_instance
