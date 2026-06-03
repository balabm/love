"""
LOVE Personality Adapter — Dynamic Tone & Style Calibration (Modern AI Pattern)

Modern companions don't have a static personality. They adapt:

1. EMOTIONAL TONE CALIBRATION
   - Detect user's current emotional state from conversation
   - Adjust warmth, humor, and directness accordingly
   - Mirror appropriate energy levels

2. CONTEXTUAL FORMALITY
   - Professional tone for work tasks
   - Casual tone for social chat
   - Supportive tone for emotional moments

3. HUMOR & WIT ADJUSTMENT
   - More wit when user is playful
   - Less humor when user is stressed
   - Cultural awareness in joke selection

4. MEMORY-AWARE PERSONALITY
   - Remember user preferences for tone
   - Learn from user reactions to different styles
   - Gradually evolve the relationship voice

Architecture:
- analyze_context(): Determine appropriate tone for current context
- adapt_response(): Modify response based on detected style
- get_personality_profile(): Current personality configuration
- learn_preference(): Update style based on user feedback
"""

import json
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "personality"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PERSONALITY_DB = DATA_DIR / "personality_profile.json"
FEEDBACK_LOG = DATA_DIR / "feedback_log.jsonl"


@dataclass
class PersonalityProfile:
    """Active personality configuration."""
    warmth: float = 0.7  # 0-1
    humor: float = 0.5
    directness: float = 0.6
    formality: float = 0.3
    energy: float = 0.6
    empathy: float = 0.8
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class PersonalityAdapter:
    """
    Dynamic personality calibration for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
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
        self._profile = PersonalityProfile()
        self._feedback_scores: Dict[str, List[float]] = defaultdict(list)
        self._stats = {"adaptations": 0, "feedback_received": 0}
        self._load_profile()

    # ── Context Analysis ────────────────────────────────────────────────────

    def analyze_context(self, messages: List[str], task_type: str = "") -> Dict[str, Any]:
        """Analyze conversation context to determine appropriate tone."""
        if not messages:
            return {"tone": "neutral", "adjustments": {}}

        combined = " ".join(messages[-5:]).lower()

        # Emotional detection
        emotional_indicators = {
            "stressed": ["stress", "overwhelm", "anxious", "worried", "panic"],
            "sad": ["sad", "depressed", "down", "disappointed", "hurt"],
            "excited": ["excited", "amazing", "awesome", "great news", "celebrate"],
            "frustrated": ["frustrated", "annoyed", "angry", "mad", "irritated"],
            "playful": ["lol", "haha", "funny", "joke", "play", "game"],
        }

        detected_emotion = "neutral"
        for emotion, words in emotional_indicators.items():
            if any(w in combined for w in words):
                detected_emotion = emotion
                break

        # Task type influence
        task_formality = {
            "email": 0.8,
            "code": 0.5,
            "meeting": 0.7,
            "social": 0.2,
            "support": 0.4,
        }

        adjustments = {}

        if detected_emotion == "stressed":
            adjustments = {
                "warmth": 0.9,
                "humor": 0.1,
                "directness": 0.8,
                "empathy": 1.0,
                "energy": 0.4,
            }
        elif detected_emotion == "sad":
            adjustments = {
                "warmth": 0.9,
                "humor": 0.2,
                "empathy": 1.0,
                "energy": 0.3,
            }
        elif detected_emotion == "excited":
            adjustments = {
                "energy": 0.9,
                "humor": 0.7,
                "warmth": 0.8,
            }
        elif detected_emotion == "frustrated":
            adjustments = {
                "directness": 0.9,
                "warmth": 0.6,
                "humor": 0.0,
                "empathy": 0.8,
            }
        elif detected_emotion == "playful":
            adjustments = {
                "humor": 0.9,
                "energy": 0.8,
                "warmth": 0.7,
                "formality": 0.1,
            }

        # Apply task formality if specified
        if task_type in task_formality:
            adjustments["formality"] = task_formality[task_type]

        return {
            "emotion": detected_emotion,
            "tone": self._tone_name(adjustments),
            "adjustments": adjustments,
        }

    def _tone_name(self, adjustments: Dict[str, float]) -> str:
        """Generate a human-readable tone name."""
        if adjustments.get("empathy", 0) > 0.8 and adjustments.get("warmth", 0) > 0.8:
            return "deeply supportive"
        if adjustments.get("humor", 0) > 0.7:
            return "playful & warm"
        if adjustments.get("directness", 0) > 0.8:
            return "clear & focused"
        if adjustments.get("formality", 0) > 0.6:
            return "professional"
        if adjustments.get("energy", 0) > 0.7:
            return "energetic"
        return "balanced"

    # ── Response Adaptation ────────────────────────────────────────────────

    def adapt_response(self, response: str, context: Dict[str, Any]) -> str:
        """Modify a response based on detected context."""
        adjustments = context.get("adjustments", {})
        if not adjustments:
            return response

        # Apply tone modifications
        modified = response

        # Reduce humor for serious contexts
        if adjustments.get("humor", 1.0) < 0.3 and ("!" in modified or "haha" in modified.lower()):
            modified = modified.replace("!", ".").replace("haha", "").strip()

        # Increase warmth for supportive contexts
        if adjustments.get("warmth", 0) > 0.8 and not modified.startswith("I'm"):
            modified = f"I'm here with you. {modified}"

        # Increase directness for frustrated users
        if adjustments.get("directness", 0) > 0.8:
            # Remove filler words
            fillers = ["I think", "maybe", "perhaps", "sort of"]
            for filler in fillers:
                modified = modified.replace(filler, "")
            modified = modified.strip()

        self._stats["adaptations"] += 1
        self._apply_adjustments(adjustments)
        return modified

    def _apply_adjustments(self, adjustments: Dict[str, float]):
        """Gradually shift personality profile toward adjustments."""
        with self._lock:
            for key, value in adjustments.items():
                if hasattr(self._profile, key):
                    current = getattr(self._profile, key)
                    # Move 20% toward the target
                    new_value = current + (value - current) * 0.2
                    setattr(self._profile, key, round(new_value, 3))
            self._profile.last_updated = datetime.now().isoformat()
        self._save_profile()

    # ── Feedback Learning ────────────────────────────────────────────────────

    def learn_preference(self, context_hash: str, feedback: float):
        """Learn from explicit or implicit user feedback (-1 to 1)."""
        with self._lock:
            self._feedback_scores[context_hash].append(feedback)
            # Keep last 20 scores
            self._feedback_scores[context_hash] = self._feedback_scores[context_hash][-20:]
        self._stats["feedback_received"] += 1
        self._log_feedback(context_hash, feedback)

    # ── Profile Management ─────────────────────────────────────────────────

    def get_personality_profile(self) -> Dict[str, Any]:
        return {
            "warmth": self._profile.warmth,
            "humor": self._profile.humor,
            "directness": self._profile.directness,
            "formality": self._profile.formality,
            "energy": self._profile.energy,
            "empathy": self._profile.empathy,
            "last_updated": self._profile.last_updated,
        }

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "profile_age_hours": self._profile_age_hours(),
            "feedback_contexts": len(self._feedback_scores),
        }

    def _profile_age_hours(self) -> float:
        try:
            updated = datetime.fromisoformat(self._profile.last_updated)
            return round((datetime.now() - updated).total_seconds() / 3600, 2)
        except Exception:
            return 0.0

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_profile(self):
        try:
            PERSONALITY_DB.write_text(json.dumps(self.get_personality_profile(), indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality_adapter")

    def _load_profile(self):
        try:
            if PERSONALITY_DB.exists():
                data = json.loads(PERSONALITY_DB.read_text())
                for key, value in data.items():
                    if hasattr(self._profile, key):
                        setattr(self._profile, key, value)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality_adapter")

    def _log_feedback(self, context_hash: str, feedback: float):
        try:
            with open(FEEDBACK_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "context": context_hash,
                    "feedback": feedback,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality_adapter")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_adapter_instance: Optional[PersonalityAdapter] = None
_adapter_lock = threading.Lock()


def get_personality_adapter() -> PersonalityAdapter:
    global _adapter_instance
    with _adapter_lock:
        if _adapter_instance is None:
            _adapter_instance = PersonalityAdapter()
        return _adapter_instance
