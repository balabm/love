"""
LOVE Intent Predictor — Proactive Response Preparation (Modern AI Pattern)

Modern companions don't just react — they anticipate. This predictor:

1. PATTERN RECOGNITION
   - Identify recurring conversation patterns
   - Detect incomplete thoughts the user is likely to finish
   - Recognize when the user is building toward a question

2. PROACTIVE PREPARATION
   - Pre-compute likely responses before the user asks
   - Warm up relevant models and memory contexts
   - Pre-fetch data the user is likely to need

3. INTENT CLASSIFICATION
   - Classify user intent: question, command, social, emotional, etc.
   - Predict follow-up questions based on conversation flow
   - Detect implicit needs the user hasn't stated

4. CONFIDENCE SCORING
   - Score prediction confidence
   - Only act on high-confidence predictions
   - Learn from prediction accuracy over time

Architecture:
- predict_next_intent(): Predict what the user will do next
- prepare_response(): Pre-compute response for predicted intent
- classify_intent(): Classify current user message intent
- get_prediction_stats(): Track prediction accuracy
"""

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "intent_predictor"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PREDICTION_LOG = DATA_DIR / "prediction_log.jsonl"
ACCURACY_DB = DATA_DIR / "accuracy_db.json"


@dataclass
class IntentPrediction:
    """A prediction of user intent."""
    prediction_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    predicted_intent: str = ""  # question, command, social, emotional, etc.
    confidence: float = 0.0
    predicted_message: str = ""  # What we think they'll say
    suggested_response: str = ""  # Pre-computed response
    context_trigger: str = ""  # What triggered this prediction
    validated: bool = False  # Did the user actually do this?
    correct: bool = False  # Was the prediction correct?


class IntentPredictor:
    """
    Proactive intent prediction for LOVE.
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
        self._predictions: deque = deque(maxlen=500)
        self._pattern_memory: Dict[str, int] = defaultdict(int)
        self._intent_sequences: deque = deque(maxlen=100)
        self._stats = {"predictions": 0, "correct": 0, "false_positives": 0}
        self._load_accuracy()

    # ── Intent Classification ────────────────────────────────────────────────

    def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify the intent of a user message."""
        msg = message.lower().strip()

        # Simple rule-based classification
        intents = {
            "question": any(w in msg for w in ["?", "what", "how", "why", "when", "where", "who", "which"]),
            "command": any(w in msg for w in ["do", "make", "create", "send", "schedule", "remind", "set"]),
            "social": any(w in msg for w in ["hello", "hi", "hey", "thanks", "thank you", "goodbye", "bye"]),
            "emotional": any(w in msg for w in ["feel", "sad", "happy", "angry", "worried", "excited", "stressed"]),
            "request_info": any(w in msg for w in ["tell me", "show me", "explain", "describe", "what is"]),
        }

        # Pick the most likely intent
        detected = [k for k, v in intents.items() if v]
        primary = detected[0] if detected else "general"

        # Confidence based on keyword strength
        confidence = 0.7 if detected else 0.3
        if "?" in msg:
            confidence = min(1.0, confidence + 0.2)

        # Record in sequence memory
        self._intent_sequences.append(primary)

        return {
            "intent": primary,
            "confidence": round(confidence, 3),
            "all_detected": detected,
            "message_preview": msg[:50],
        }

    # ── Intent Prediction ───────────────────────────────────────────────────

    def predict_next_intent(self, recent_messages: List[str]) -> Optional[IntentPrediction]:
        """Predict what the user will do next."""
        if not recent_messages:
            return None

        last_message = recent_messages[-1].lower()
        prediction = IntentPrediction(prediction_id=f"pred_{int(time.time())}")

        # Pattern 1: Incomplete questions
        if last_message.endswith(("...", "-", ",")) or last_message.startswith(("what about", "how about", "and")):
            prediction.predicted_intent = "follow_up"
            prediction.predicted_message = "[User continues previous topic]"
            prediction.suggested_response = "Let me continue from where we left off..."
            prediction.confidence = 0.7
            prediction.context_trigger = "incomplete_thought"

        # Pattern 2: Question followed by silence = likely follow-up question
        elif self._intent_sequences and self._intent_sequences[-1] == "question" and len(recent_messages) > 1:
            prediction.predicted_intent = "question"
            prediction.predicted_message = "[Follow-up question]"
            prediction.suggested_response = "You might also want to know..."
            prediction.confidence = 0.5
            prediction.context_trigger = "after_question"

        # Pattern 3: Command detected = likely verification
        elif self._intent_sequences and self._intent_sequences[-1] == "command":
            prediction.predicted_intent = "command"
            prediction.predicted_message = "[Confirmation or follow-up command]"
            prediction.suggested_response = "Just to confirm, you want me to..."
            prediction.confidence = 0.6
            prediction.context_trigger = "after_command"

        # Pattern 4: Emotional message = likely needs support
        elif self._intent_sequences and self._intent_sequences[-1] == "emotional":
            prediction.predicted_intent = "emotional"
            prediction.predicted_message = "[More context about feelings]"
            prediction.suggested_response = "I'm here for you. Tell me more..."
            prediction.confidence = 0.6
            prediction.context_trigger = "emotional_expression"

        else:
            return None

        with self._lock:
            self._predictions.append(prediction)
        self._stats["predictions"] += 1
        self._log_prediction(prediction)

        return prediction

    # ── Prediction Validation ────────────────────────────────────────────────

    def validate_prediction(self, prediction_id: str, actual_message: str) -> bool:
        """Check if a prediction was correct."""
        for pred in self._predictions:
            if pred.prediction_id == prediction_id:
                pred.validated = True

                # Check if actual matches predicted intent
                actual_intent = self.classify_intent(actual_message)["intent"]
                pred.correct = (actual_intent == pred.predicted_intent)

                if pred.correct:
                    self._stats["correct"] += 1
                else:
                    self._stats["false_positives"] += 1

                self._save_accuracy()
                return pred.correct

        return False

    # ── Proactive Preparation ─────────────────────────────────────────────────

    def prepare_response(self, prediction: IntentPrediction) -> Dict[str, Any]:
        """Prepare a response for a predicted intent."""
        if prediction.confidence < 0.5:
            return {"prepared": False, "reason": "confidence too low"}

        # Pre-warm relevant systems
        warmed = []
        try:
            from core.vector_memory import get_vector_engine
            vm = get_vector_engine()
            warmed.append("vector_memory")
        except Exception:
            pass

        try:
            from core.knowledge_graph import query_knowledge
            warmed.append("knowledge_graph")
        except Exception:
            pass

        return {
            "prepared": True,
            "prediction": prediction.predicted_intent,
            "suggested_response": prediction.suggested_response,
            "confidence": prediction.confidence,
            "warmed_systems": warmed,
        }

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        total = self._stats["predictions"]
        correct = self._stats["correct"]
        accuracy = correct / max(total, 1)

        return {
            **self._stats,
            "accuracy": round(accuracy, 3),
            "recent_predictions": len(self._predictions),
            "pattern_memory_size": len(self._pattern_memory),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log_prediction(self, prediction: IntentPrediction):
        try:
            with open(PREDICTION_LOG, "a") as f:
                f.write(json.dumps({
                    "prediction_id": prediction.prediction_id,
                    "timestamp": prediction.timestamp,
                    "predicted_intent": prediction.predicted_intent,
                    "confidence": prediction.confidence,
                    "validated": prediction.validated,
                    "correct": prediction.correct,
                }) + "\n")
        except Exception:
            pass

    def _save_accuracy(self):
        try:
            ACCURACY_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def _load_accuracy(self):
        try:
            if ACCURACY_DB.exists():
                self._stats = json.loads(ACCURACY_DB.read_text())
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_predictor_instance: Optional[IntentPredictor] = None
_predictor_lock = threading.Lock()


def get_intent_predictor() -> IntentPredictor:
    global _predictor_instance
    with _predictor_lock:
        if _predictor_instance is None:
            _predictor_instance = IntentPredictor()
        return _predictor_instance
