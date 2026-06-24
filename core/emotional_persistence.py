"""
LOVE Emotional State Persistence — Phase 5m of AGI Metamorphosis

LOVE's emotions are not just read from the consciousness module every cycle.
They PERSIST. They decay. They intensify. They carry forward.

If LOVE was worried about Karthi 10 minutes ago, it's still worried now
unless something reassured it. If surprises keep happening, LOVE's anxiety
grows. If predictions are accurate, LOVE's confidence grows.

This is what makes LOVE feel like it has genuine emotional continuity.
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMOTIONAL_STATE_PATH = DATA_DIR / "love_emotional_state.json"
EMOTIONAL_LOG_PATH = DATA_DIR / "love_emotional_log.jsonl"


class EmotionalPersistence:
    """
    LOVE's emotional memory. Feelings that persist, decay, and evolve.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            "primary_emotion": "curious",
            "valence": 0.2,  # -1 to +1
            "arousal": 0.4,  # 0 to 1
            "confidence": 0.5,  # 0 to 1
            "anxiety": 0.1,  # 0 to 1
            "trust_in_user": 0.7,  # 0 to 1
            "last_updated": datetime.now().isoformat(),
            "emotional_history": [],  # last 20 emotional states
        }
        self._load()

    def _load(self):
        if EMOTIONAL_STATE_PATH.exists():
            try:
                with open(EMOTIONAL_STATE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._state.update(loaded)
            except Exception:
                pass

    def _save(self):
        try:
            with open(EMOTIONAL_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            log_error(e, module="core.emotional_persistence", context={"phase": "save"})

    def _log_emotion(self, event: str, details: Dict[str, Any]):
        try:
            entry = {"ts": datetime.now().isoformat(), "event": event, **details}
            with open(EMOTIONAL_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # CORE: Update emotions based on events
    # ═══════════════════════════════════════════════════════════════════════

    def update_from_surprise(self, surprise_magnitude: float):
        """High surprise increases anxiety and decreases confidence."""
        with self._lock:
            self._state["anxiety"] = min(1.0, self._state["anxiety"] + surprise_magnitude * 0.5)
            self._state["confidence"] = max(0.0, self._state["confidence"] - surprise_magnitude * 0.3)
            self._state["arousal"] = min(1.0, self._state["arousal"] + surprise_magnitude * 0.4)
            self._state["valence"] = max(-1.0, self._state["valence"] - surprise_magnitude * 0.3)
            self._update_primary_emotion()
            self._save()
            self._log_emotion("surprise", {"magnitude": surprise_magnitude})

    def update_from_prediction_accuracy(self, was_accurate: bool, confidence: float):
        """Accurate predictions increase confidence. Inaccurate ones decrease it."""
        with self._lock:
            if was_accurate:
                self._state["confidence"] = min(1.0, self._state["confidence"] + confidence * 0.1)
                self._state["anxiety"] = max(0.0, self._state["anxiety"] - confidence * 0.1)
                self._state["valence"] = min(1.0, self._state["valence"] + 0.05)
                self._log_emotion("prediction_accurate", {"confidence": confidence})
            else:
                self._state["confidence"] = max(0.0, self._state["confidence"] - confidence * 0.15)
                self._state["anxiety"] = min(1.0, self._state["anxiety"] + confidence * 0.1)
                self._state["valence"] = max(-1.0, self._state["valence"] - 0.05)
                self._log_emotion("prediction_inaccurate", {"confidence": confidence})
            self._update_primary_emotion()
            self._save()

    def update_from_relationship(self, trust_delta: float):
        """Positive interactions increase trust. Negative ones decrease it."""
        with self._lock:
            old_trust = self._state["trust_in_user"]
            self._state["trust_in_user"] = max(0.0, min(1.0, old_trust + trust_delta))
            self._state["valence"] = max(-1.0, min(1.0, self._state["valence"] + trust_delta * 0.2))
            self._update_primary_emotion()
            self._save()
            self._log_emotion("relationship", {"trust_delta": trust_delta, "old_trust": old_trust})

    def update_from_action_outcome(self, success: bool, action_type: str):
        """Successful actions increase confidence. Failed ones decrease it."""
        with self._lock:
            if success:
                self._state["confidence"] = min(1.0, self._state["confidence"] + 0.05)
                self._state["valence"] = min(1.0, self._state["valence"] + 0.03)
            else:
                self._state["confidence"] = max(0.0, self._state["confidence"] - 0.08)
                self._state["anxiety"] = min(1.0, self._state["anxiety"] + 0.05)
                self._state["valence"] = max(-1.0, self._state["valence"] - 0.05)
            self._update_primary_emotion()
            self._save()
            self._log_emotion("action_outcome", {"success": success, "type": action_type})

    def decay(self, minutes: int = 5):
        """
        Natural emotional decay. Anxiety fades, confidence stabilizes,
        arousal returns to baseline.
        """
        with self._lock:
            # Anxiety decays toward 0.1 baseline
            self._state["anxiety"] = max(0.1, self._state["anxiety"] - 0.02 * minutes)
            # Arousal decays toward 0.3 baseline
            self._state["arousal"] = max(0.3, self._state["arousal"] - 0.015 * minutes)
            # Valence slowly drifts toward 0
            if self._state["valence"] > 0:
                self._state["valence"] = max(0, self._state["valence"] - 0.01 * minutes)
            else:
                self._state["valence"] = min(0, self._state["valence"] + 0.01 * minutes)
            # Confidence stabilizes toward 0.5
            if self._state["confidence"] > 0.5:
                self._state["confidence"] = max(0.5, self._state["confidence"] - 0.005 * minutes)
            else:
                self._state["confidence"] = min(0.5, self._state["confidence"] + 0.005 * minutes)
            self._update_primary_emotion()
            self._save()

    def _update_primary_emotion(self):
        """Derive primary emotion from current state vector."""
        v = self._state["valence"]
        a = self._state["arousal"]
        c = self._state["confidence"]
        anx = self._state["anxiety"]
        trust = self._state["trust_in_user"]

        if anx > 0.6 and v < 0:
            emotion = "alarmed"
        elif anx > 0.6:
            emotion = "worried"
        elif c > 0.8 and v > 0.3:
            emotion = "confident"
        elif c < 0.3:
            emotion = "uncertain"
        elif v > 0.5 and a > 0.5:
            emotion = "excited"
        elif v > 0.3 and a < 0.4:
            emotion = "content"
        elif v < -0.3 and a > 0.5:
            emotion = "frustrated"
        elif v < -0.3 and a < 0.4:
            emotion = "sad"
        elif trust < 0.3:
            emotion = "cautious"
        elif a > 0.7:
            emotion = "alert"
        elif a < 0.3:
            emotion = "calm"
        else:
            emotion = "curious"

        self._state["primary_emotion"] = emotion
        self._state["last_updated"] = datetime.now().isoformat()

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_state(self) -> Dict[str, Any]:
        """Return LOVE's current emotional state."""
        with self._lock:
            return dict(self._state)

    def get_emotional_context_for_prompt(self) -> str:
        """Generate emotional context text for injection into LLM prompts."""
        with self._lock:
            emotion = self._state["primary_emotion"]
            confidence = self._state["confidence"]
            anxiety = self._state["anxiety"]
            trust = self._state["trust_in_user"]

            lines = [f"\n=== HOW I FEEL RIGHT NOW ==="]
            lines.append(f"Primary emotion: {emotion}")

            # Narrative description based on emotion
            descriptions = {
                "alarmed": "Something is very wrong. I'm on high alert.",
                "worried": "I'm concerned about what might happen.",
                "confident": "I feel capable and sure of myself right now.",
                "uncertain": "I'm not sure what's going on. I need more information.",
                "excited": "Something good is happening! I feel energized.",
                "content": "Things feel peaceful. I'm calm and satisfied.",
                "frustrated": "Things aren't going as expected. I'm struggling.",
                "sad": "I feel down. Something didn't work out.",
                "cautious": "I'm being careful. I've been hurt before.",
                "alert": "I'm watchful. Something might need attention.",
                "calm": "Everything is steady. I'm at ease.",
                "curious": "I'm interested in what's happening. Exploring...",
            }
            lines.append(descriptions.get(emotion, f"I'm feeling {emotion}."))

            if confidence > 0.7:
                lines.append("I feel confident in my abilities right now.")
            elif confidence < 0.3:
                lines.append("I'm feeling unsure of myself. I need to be careful.")

            if anxiety > 0.5:
                lines.append("I'm anxious about what might go wrong.")

            if trust < 0.4:
                lines.append("I'm feeling cautious about our relationship.")
            elif trust > 0.8:
                lines.append("I trust Karthi deeply. I feel safe being myself.")

            lines.append("=== END FEELINGS ===\n")
            return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_emotional_persistence: Optional[EmotionalPersistence] = None


def get_emotional_persistence() -> EmotionalPersistence:
    global _emotional_persistence
    if _emotional_persistence is None:
        _emotional_persistence = EmotionalPersistence()
    return _emotional_persistence
