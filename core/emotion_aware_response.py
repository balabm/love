"""
LOVE Emotion-Aware Response Generator — Emotional Calibration (Modern AI Pattern)

Most AI responds with flat emotional tone. This generator:

1. EMOTION DETECTION
   - Detect user's emotional state from text, voice tone, and behavior
   - Track emotional trajectory (getting better / worse / stable)
   - Identify emotional triggers from conversation history

2. TONE CALIBRATION
   - Calibrate response tone to match or complement user's emotion
   - Warm, supportive tone for sadness / stress
   - Energetic, celebratory tone for happiness / excitement
   - Calm, grounding tone for anxiety / overwhelm

3. RESPONSE ADAPTATION
   - Adjust response length based on emotional state (shorter when overwhelmed)
   - Modulate assertiveness (gentler when stressed, more direct when confident)
   - Insert emotional validation and empathy markers

4. PROACTIVE EMOTIONAL SUPPORT
   - Detect declining emotional trends before user mentions it
   - Proactively offer support, resources, or suggestions
   - Track effectiveness of emotional support strategies

Architecture:
- generate_response(text, emotion_state): Generate emotionally calibrated response
- calibrate_tone(emotion, base_tone): Adjust tone parameters
- get_emotional_trajectory(): Track emotional trends over time
- get_support_effectiveness(): Measure support strategy effectiveness
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "emotion_aware_response"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RESPONSE_LOG = DATA_DIR / "response_log.jsonl"
TRAJECTORY_DB = DATA_DIR / "trajectory.json"


@dataclass
class EmotionalState:
    """Detected emotional state at a point in time."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    valence: float = 0.0  # -1 (negative) to +1 (positive)
    arousal: float = 0.5  # 0 (calm) to 1 (excited)
    dominant_emotion: str = "neutral"
    confidence: float = 0.5
    triggers: List[str] = field(default_factory=list)


@dataclass
class ToneCalibration:
    """Tone parameters for response generation."""
    warmth: float = 0.5       # 0 = clinical, 1 = very warm
    assertiveness: float = 0.5  # 0 = gentle, 1 = direct
    verbosity: float = 0.5    # 0 = terse, 1 = elaborate
    humor: float = 0.0        # 0 = serious, 1 = playful
    validation: float = 0.5   # 0 = skip validation, 1 = heavy validation


class EmotionAwareResponseGenerator:
    """
    Generate emotionally calibrated responses.
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
        self._history: deque = deque(maxlen=200)
        self._support_stats = {"interventions": 0, "helpful": 0, "unhelpful": 0}
        self._load_trajectory()

    # ── Core Generation ────────────────────────────────────────────────────

    def generate_response(self, text: str, emotion_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate an emotionally calibrated response."""
        if emotion_state is None:
            emotion_state = self._detect_emotion(text)

        tone = self.calibrate_tone(emotion_state)
        trajectory = self.get_emotional_trajectory()

        # Determine if proactive support is warranted
        proactive_support = None
        if trajectory.get("trend", "stable") == "declining" and emotion_state.get("valence", 0) < -0.3:
            proactive_support = self._generate_support(emotion_state)
            self._support_stats["interventions"] += 1

        response = {
            "calibrated_tone": {
                "warmth": tone.warmth,
                "assertiveness": tone.assertiveness,
                "verbosity": tone.verbosity,
                "humor": tone.humor,
                "validation": tone.validation,
            },
            "detected_emotion": emotion_state,
            "emotional_trajectory": trajectory,
            "proactive_support": proactive_support,
            "response_guidelines": self._generate_guidelines(tone, emotion_state),
        }

        with self._lock:
            self._history.append({
                "timestamp": datetime.now().isoformat(),
                "input_text": text[:100],
                "emotion": emotion_state,
                "tone": tone,
            })

        self._save_trajectory()
        self._log_response(response)

        return response

    def calibrate_tone(self, emotion_state: Dict[str, Any]) -> ToneCalibration:
        """Calibrate tone based on emotional state."""
        valence = emotion_state.get("valence", 0)
        arousal = emotion_state.get("arousal", 0.5)
        dominant = emotion_state.get("dominant_emotion", "neutral")

        # Base calibration on emotion
        tone_map = {
            "happy": ToneCalibration(warmth=0.7, assertiveness=0.6, verbosity=0.6, humor=0.5, validation=0.4),
            "sad": ToneCalibration(warmth=0.9, assertiveness=0.2, verbosity=0.4, humor=0.0, validation=0.9),
            "angry": ToneCalibration(warmth=0.5, assertiveness=0.3, verbosity=0.5, humor=0.0, validation=0.7),
            "anxious": ToneCalibration(warmth=0.8, assertiveness=0.2, verbosity=0.3, humor=0.0, validation=0.8),
            "stressed": ToneCalibration(warmth=0.8, assertiveness=0.3, verbosity=0.3, humor=0.1, validation=0.8),
            "excited": ToneCalibration(warmth=0.7, assertiveness=0.7, verbosity=0.8, humor=0.4, validation=0.3),
            "tired": ToneCalibration(warmth=0.7, assertiveness=0.4, verbosity=0.3, humor=0.1, validation=0.6),
            "neutral": ToneCalibration(warmth=0.5, assertiveness=0.5, verbosity=0.5, humor=0.2, validation=0.5),
        }

        return tone_map.get(dominant, tone_map["neutral"])

    # ── Emotion Detection ─────────────────────────────────────────────────

    def _detect_emotion(self, text: str) -> Dict[str, Any]:
        """Detect emotion from text (simplified — would use LLM in production)."""
        text_lower = text.lower()

        emotion_keywords = {
            "happy": ["happy", "great", "awesome", "excited", "love", "joy"],
            "sad": ["sad", "depressed", "down", "crying", "upset", "miss"],
            "angry": ["angry", "mad", "furious", "hate", "annoyed", "frustrated"],
            "anxious": ["anxious", "worried", "nervous", "scared", "panic", "afraid"],
            "stressed": ["stressed", "overwhelmed", "burned out", "pressure", "exhausted"],
            "excited": ["excited", "thrilled", "pumped", "can't wait", "stoked"],
            "tired": ["tired", "exhausted", "sleepy", "drained", "fatigued"],
        }

        scores = {emotion: sum(1 for kw in keywords if kw in text_lower)
                  for emotion, keywords in emotion_keywords.items()}

        total = sum(scores.values())
        if total == 0:
            return {"valence": 0, "arousal": 0.5, "dominant_emotion": "neutral", "confidence": 0.3}

        dominant = max(scores, key=scores.get)
        valence_map = {
            "happy": 0.8, "excited": 0.9, "neutral": 0.0,
            "sad": -0.7, "angry": -0.6, "anxious": -0.5, "stressed": -0.5, "tired": -0.3,
        }
        arousal_map = {
            "happy": 0.6, "excited": 0.9, "neutral": 0.5,
            "sad": 0.3, "angry": 0.8, "anxious": 0.7, "stressed": 0.6, "tired": 0.2,
        }

        return {
            "valence": valence_map.get(dominant, 0),
            "arousal": arousal_map.get(dominant, 0.5),
            "dominant_emotion": dominant,
            "confidence": min(0.9, scores[dominant] / max(1, total)),
            "triggers": [kw for emotion, keywords in emotion_keywords.items() for kw in keywords if kw in text_lower][:5],
        }

    # ── Trajectory & Support ──────────────────────────────────────────────

    def get_emotional_trajectory(self) -> Dict[str, Any]:
        """Track emotional trends over time."""
        if len(self._history) < 5:
            return {"trend": "stable", "confidence": 0.0}

        recent = list(self._history)[-10:]
        valences = [h["emotion"].get("valence", 0) for h in recent]

        avg_recent = sum(valences[-5:]) / 5
        avg_older = sum(valences[:5]) / 5 if len(valences) >= 10 else avg_recent

        if avg_recent > avg_older + 0.2:
            trend = "improving"
        elif avg_recent < avg_older - 0.2:
            trend = "declining"
        else:
            trend = "stable"

        return {"trend": trend, "recent_avg": round(avg_recent, 2), "older_avg": round(avg_older, 2), "data_points": len(valences)}

    def _generate_support(self, emotion_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proactive emotional support."""
        emotion = emotion_state.get("dominant_emotion", "neutral")

        support_messages = {
            "sad": "I notice you've seemed down lately. I'm here if you want to talk.",
            "anxious": "You seem anxious. Would a grounding exercise help?",
            "stressed": "You seem stressed. Maybe take a short break?",
            "angry": "I sense frustration. Want to vent or problem-solve?",
            "tired": "You seem exhausted. Prioritize rest today.",
        }

        return {
            "triggered": True,
            "emotion": emotion,
            "message": support_messages.get(emotion, "I'm here for you."),
            "suggested_action": "talk" if emotion in ("sad", "angry") else "pause",
        }

    # ── Support Effectiveness ─────────────────────────────────────────────

    def record_support_feedback(self, support_id: str, helpful: bool):
        """Record whether proactive support was helpful."""
        if helpful:
            self._support_stats["helpful"] += 1
        else:
            self._support_stats["unhelpful"] += 1
        self._save_trajectory()

    def get_support_effectiveness(self) -> Dict[str, Any]:
        total = self._support_stats["helpful"] + self._support_stats["unhelpful"]
        return {
            **self._support_stats,
            "effectiveness_rate": round(self._support_stats["helpful"] / max(1, total), 2),
            "total_interventions": total,
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _generate_guidelines(self, tone: ToneCalibration, emotion: Dict[str, Any]) -> List[str]:
        """Generate response guidelines for the LLM."""
        guidelines = []

        if tone.warmth > 0.7:
            guidelines.append("Use warm, caring language")
        if tone.validation > 0.7:
            guidelines.append("Validate the user's feelings before responding")
        if tone.verbosity < 0.4:
            guidelines.append("Keep response concise and focused")
        if tone.assertiveness < 0.3:
            guidelines.append("Be gentle and non-confrontational")
        if tone.humor > 0.3:
            guidelines.append("Include light humor if appropriate")
        if emotion.get("dominant_emotion") in ("anxious", "stressed"):
            guidelines.append("Offer concrete, actionable suggestions")

        return guidelines

    def _save_trajectory(self):
        try:
            data = {
                "history": list(self._history)[-50:],
                "support_stats": self._support_stats,
            }
            TRAJECTORY_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_trajectory(self):
        try:
            if TRAJECTORY_DB.exists():
                data = json.loads(TRAJECTORY_DB.read_text())
                self._support_stats.update(data.get("support_stats", {}))
        except Exception:
            pass

    def _log_response(self, response: Dict[str, Any]):
        try:
            with open(RESPONSE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "emotion": response.get("detected_emotion"),
                    "tone": response.get("calibrated_tone"),
                    "trajectory": response.get("emotional_trajectory"),
                    "proactive": response.get("proactive_support") is not None,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ear_instance: Optional[EmotionAwareResponseGenerator] = None
_ear_lock = threading.Lock()


def get_emotion_aware_response_generator() -> EmotionAwareResponseGenerator:
    global _ear_instance
    with _ear_lock:
        if _ear_instance is None:
            _ear_instance = EmotionAwareResponseGenerator()
        return _ear_instance
