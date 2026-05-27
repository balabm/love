"""
Active Inference Kernel - Markov Blanket Architecture

Implements Karl Friston's Free Energy Principle for continuous surprise minimization
between internal world-model and external data streams.

Free Energy: F = E[q(log p)] - H[q]
Where:
- E[q(log p)] is the expected energy (prediction error)
- H[q] is the entropy of the variational distribution

The system maintains a Markov Blanket separating:
- Internal states (cognitive, beliefs, goals)
- Sensory states (APIs, UI, logs, biometrics)
- Active states (actions, interventions, outputs)
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
import json
from collections import deque
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of states in the Markov Blanket"""
    INTERNAL = "internal"  # Cognitive states, beliefs, goals
    SENSORY = "sensory"    # External inputs: APIs, UI, logs, biometrics
    ACTIVE = "active"      # Actions, interventions, outputs


class PredictionDomain(Enum):
    """Domains for user state prediction"""
    CODE_CONTEXT = "code_context"
    BIOMETRIC_STRESS = "biometric_stress"
    FINANCIAL_RISK = "financial_risk"
    EMOTIONAL_STATE = "emotional_state"
    WORK_ENERGY = "work_energy"


@dataclass
class State:
    """A state in the Markov Blanket"""
    state_id: str
    state_type: StateType
    value: Any
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for serialization"""
        return {
            "state_id": self.state_id,
            "state_type": self.state_type.value,
            "value": str(self.value) if not isinstance(self.value, (dict, list)) else self.value,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class Prediction:
    """A predictive model of user state"""
    domain: PredictionDomain
    predicted_value: Any
    confidence: float
    timestamp: datetime
    prediction_horizon: timedelta  # How far into the future this predicts
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert prediction to dictionary"""
        return {
            "domain": self.domain.value,
            "predicted_value": str(self.predicted_value) if not isinstance(self.predicted_value, (dict, list)) else self.predicted_value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "prediction_horizon_seconds": self.prediction_horizon.total_seconds(),
            "model_parameters": self.model_parameters
        }


@dataclass
class SurpriseEvent:
    """Represents a surprise event (prediction error)"""
    domain: PredictionDomain
    predicted_value: Any
    actual_value: Any
    surprise_magnitude: float  # Free energy contribution
    timestamp: datetime
    threshold_exceeded: bool
    
    def to_dict(self) -> Dict:
        """Convert surprise event to dictionary"""
        return {
            "domain": self.domain.value,
            "predicted_value": str(self.predicted_value) if not isinstance(self.predicted_value, (dict, list)) else self.predicted_value,
            "actual_value": str(self.actual_value) if not isinstance(self.actual_value, (dict, list)) else self.actual_value,
            "surprise_magnitude": self.surprise_magnitude,
            "timestamp": self.timestamp.isoformat(),
            "threshold_exceeded": self.threshold_exceeded
        }


class MarkovBlanket:
    """
    Markov Blanket architecture separating internal cognitive states from external sensory states.
    
    The blanket maintains conditional independence:
    - Internal states depend only on the blanket
    - External states depend only on the blanket
    - The blanket mediates all interactions
    """
    
    def __init__(self, surprise_threshold: float = 2.0):
        self.internal_states: Dict[str, State] = {}
        self.sensory_states: Dict[str, State] = {}
        self.active_states: Dict[str, State] = {}
        self.surprise_threshold = surprise_threshold
        self.state_history: deque = deque(maxlen=1000)
        
    def add_internal_state(self, state: State) -> None:
        """Add an internal cognitive state"""
        self.internal_states[state.state_id] = state
        self.state_history.append(("internal", state))
        logger.debug(f"Added internal state: {state.state_id}")
        
    def add_sensory_state(self, state: State) -> None:
        """Add a sensory state (external input)"""
        self.sensory_states[state.state_id] = state
        self.state_history.append(("sensory", state))
        logger.debug(f"Added sensory state: {state.state_id}")
        
    def add_active_state(self, state: State) -> None:
        """Add an active state (action/output)"""
        self.active_states[state.state_id] = state
        self.state_history.append(("active", state))
        logger.debug(f"Added active state: {state.state_id}")
        
    def get_state(self, state_id: str) -> Optional[State]:
        """Get a state by ID from any layer"""
        return (self.internal_states.get(state_id) or 
                self.sensory_states.get(state_id) or 
                self.active_states.get(state_id))
    
    def get_states_by_type(self, state_type: StateType) -> List[State]:
        """Get all states of a specific type"""
        if state_type == StateType.INTERNAL:
            return list(self.internal_states.values())
        elif state_type == StateType.SENSORY:
            return list(self.sensory_states.values())
        elif state_type == StateType.ACTIVE:
            return list(self.active_states.values())
        return []
    
    def get_recent_sensory_states(self, seconds: int = 60) -> List[State]:
        """Get sensory states from the last N seconds"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return [s for s in self.sensory_states.values() if s.timestamp > cutoff]
    
    def clear_old_states(self, seconds: int = 3600) -> None:
        """Clear states older than specified seconds"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        
        self.internal_states = {
            k: v for k, v in self.internal_states.items() 
            if v.timestamp > cutoff
        }
        self.sensory_states = {
            k: v for k, v in self.sensory_states.items() 
            if v.timestamp > cutoff
        }
        self.active_states = {
            k: v for k, v in self.active_states.items() 
            if v.timestamp > cutoff
        }
        logger.debug(f"Cleared states older than {seconds} seconds")


class FreeEnergyCalculator:
    """
    Calculates Free Energy using the variational principle.
    
    F = E[q(log p)] - H[q]
    
    Where:
    - E[q(log p)] is the expected energy (how well predictions match reality)
    - H[q] is the entropy of the variational distribution (model uncertainty)
    """
    
    def __init__(self):
        self.energy_history: deque = deque(maxlen=100)
        self.entropy_history: deque = deque(maxlen=100)
        
    def calculate_expected_energy(
        self, 
        predicted: Any, 
        actual: Any, 
        confidence: float = 1.0
    ) -> float:
        """
        Calculate expected energy E[q(log p)].
        
        This measures prediction error - how well the model's predictions
        match the actual observed data.
        """
        try:
            # Handle different data types
            if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                # Numerical prediction error
                error = abs(predicted - actual)
                energy = error * (1.0 / (confidence + 0.01))  # Lower confidence = higher energy penalty
            elif isinstance(predicted, str) and isinstance(actual, str):
                # String similarity (simple edit distance approximation)
                energy = 0.0 if predicted == actual else 1.0
            elif isinstance(predicted, (list, dict)) and isinstance(actual, (list, dict)):
                # Structural comparison
                energy = 0.0 if predicted == actual else 1.0
            else:
                # Fallback to binary match
                energy = 0.0 if predicted == actual else 1.0
            
            self.energy_history.append(energy)
            return energy
            
        except Exception as e:
            logger.error(f"Error calculating expected energy: {e}")
            return 1.0  # Maximum energy on error
    
    def calculate_entropy(self, confidence: float, uncertainty_factors: List[float] = None) -> float:
        """
        Calculate entropy H[q] of the variational distribution.
        
        Higher entropy means more uncertainty in the model.
        Lower confidence and more uncertainty factors increase entropy.
        """
        try:
            # Base entropy from confidence (lower confidence = higher entropy)
            base_entropy = -math.log(confidence + 0.01)
            
            # Add entropy from uncertainty factors
            if uncertainty_factors:
                factor_entropy = sum(-math.log(f + 0.01) for f in uncertainty_factors)
                entropy = base_entropy + (factor_entropy / len(uncertainty_factors))
            else:
                entropy = base_entropy
            
            self.entropy_history.append(entropy)
            return entropy
            
        except Exception as e:
            logger.error(f"Error calculating entropy: {e}")
            return 1.0
    
    def calculate_free_energy(
        self, 
        predicted: Any, 
        actual: Any, 
        confidence: float = 1.0,
        uncertainty_factors: List[float] = None
    ) -> float:
        """
        Calculate total Free Energy: F = E[q(log p)] - H[q]
        
        The system seeks to minimize this value through:
        1. Better predictions (lower expected energy)
        2. More confident models (lower entropy)
        """
        expected_energy = self.calculate_expected_energy(predicted, actual, confidence)
        entropy = self.calculate_entropy(confidence, uncertainty_factors)
        
        free_energy = expected_energy - entropy
        logger.debug(f"Free Energy: {free_energy:.4f} (Energy: {expected_energy:.4f}, Entropy: {entropy:.4f})")
        
        return free_energy
    
    def get_average_free_energy(self, window: int = 10) -> Optional[float]:
        """Get average free energy over recent calculations"""
        if len(self.energy_history) < window or len(self.entropy_history) < window:
            return None
        
        recent_energy = list(self.energy_history)[-window:]
        recent_entropy = list(self.entropy_history)[-window:]
        
        avg_energy = sum(recent_energy) / len(recent_energy)
        avg_entropy = sum(recent_entropy) / len(recent_entropy)
        
        return avg_energy - avg_entropy


class PredictiveModel:
    """
    Base class for predictive models of user state.
    
    Each model learns patterns and generates predictions for a specific domain.
    """
    
    def __init__(self, domain: PredictionDomain):
        self.domain = domain
        self.observations: deque = deque(maxlen=100)
        self.predictions: deque = deque(maxlen=100)
        self.model_parameters: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        
    def add_observation(self, value: Any, timestamp: datetime = None) -> None:
        """Add a new observation to the model"""
        if timestamp is None:
            timestamp = datetime.now()
        self.observations.append((value, timestamp))
        self.last_update = timestamp
        
    def generate_prediction(self, horizon: timedelta = timedelta(minutes=5)) -> Prediction:
        """
        Generate a prediction for the specified time horizon.
        
        Subclasses should implement specific prediction logic.
        """
        raise NotImplementedError("Subclasses must implement generate_prediction")
    
    def update_model(self) -> None:
        """
        Update model parameters based on recent observations.
        
        Subclasses should implement specific update logic.
        """
        raise NotImplementedError("Subclasses must implement update_model")
    
    def get_confidence(self) -> float:
        """Calculate model confidence based on observation history"""
        if len(self.observations) < 3:
            return 0.1  # Low confidence with insufficient data
        
        # More observations = higher confidence (up to a point)
        obs_count = len(self.observations)
        base_confidence = min(0.9, 0.3 + (obs_count / 100.0))
        
        return base_confidence


class CodeContextModel(PredictiveModel):
    """Predictive model for user's code context and development state"""
    
    def __init__(self):
        super().__init__(PredictionDomain.CODE_CONTEXT)
        self.model_parameters = {
            "active_files": [],
            "language_distribution": {},
            "edit_frequency": 0.0,
            "complexity_trend": "stable"
        }
    
    def generate_prediction(self, horizon: timedelta = timedelta(minutes=5)) -> Prediction:
        """Predict code context state"""
        if len(self.observations) < 2:
            # Default prediction with low confidence
            return Prediction(
                domain=self.domain,
                predicted_value={"state": "unknown", "activity": "idle"},
                confidence=0.1,
                timestamp=datetime.now(),
                prediction_horizon=horizon,
                model_parameters=self.model_parameters.copy()
            )
        
        # Simple trend analysis
        recent_obs = [obs[0] for obs in list(self.observations)[-5:]]
        
        # Predict based on recent activity
        if isinstance(recent_obs[-1], dict):
            last_state = recent_obs[-1].get("state", "unknown")
            predicted_state = last_state  # Persistence prediction
        else:
            predicted_state = "coding"
        
        confidence = self.get_confidence()
        
        prediction = Prediction(
            domain=self.domain,
            predicted_value={
                "state": predicted_state,
                "activity": "coding" if predicted_state != "idle" else "idle",
                "expected_files": self.model_parameters.get("active_files", [])
            },
            confidence=confidence,
            timestamp=datetime.now(),
            prediction_horizon=horizon,
            model_parameters=self.model_parameters.copy()
        )
        
        self.predictions.append(prediction)
        return prediction
    
    def update_model(self) -> None:
        """Update code context model parameters"""
        if len(self.observations) < 2:
            return
        
        recent_obs = list(self.observations)[-10:]
        
        # Extract file information
        files = set()
        languages = {}
        
        for obs in recent_obs:
            if isinstance(obs[0], dict):
                if "files" in obs[0]:
                    files.update(obs[0]["files"])
                if "language" in obs[0]:
                    lang = obs[0]["language"]
                    languages[lang] = languages.get(lang, 0) + 1
        
        self.model_parameters["active_files"] = list(files)
        self.model_parameters["language_distribution"] = languages
        
        # Calculate edit frequency
        if len(recent_obs) >= 2:
            time_span = (recent_obs[-1][1] - recent_obs[0][1]).total_seconds()
            if time_span > 0:
                self.model_parameters["edit_frequency"] = len(recent_obs) / time_span


class BiometricStressModel(PredictiveModel):
    """Predictive model for user's biometric stress levels"""
    
    def __init__(self):
        super().__init__(PredictionDomain.BIOMETRIC_STRESS)
        self.model_parameters = {
            "baseline_stress": 0.5,
            "stress_trend": "stable",
            "variability": 0.1
        }
    
    def generate_prediction(self, horizon: timedelta = timedelta(minutes=5)) -> Prediction:
        """Predict stress level"""
        if len(self.observations) < 3:
            return Prediction(
                domain=self.domain,
                predicted_value={"stress_level": 0.5, "state": "unknown"},
                confidence=0.1,
                timestamp=datetime.now(),
                prediction_horizon=horizon,
                model_parameters=self.model_parameters.copy()
            )
        
        recent_values = []
        for obs in list(self.observations)[-10:]:
            if isinstance(obs[0], (int, float)):
                recent_values.append(obs[0])
            elif isinstance(obs[0], dict) and "stress_level" in obs[0]:
                recent_values.append(obs[0]["stress_level"])
        
        if not recent_values:
            recent_values = [0.5]
        
        # Simple moving average prediction
        avg_stress = sum(recent_values) / len(recent_values)
        
        # Detect trend
        if len(recent_values) >= 3:
            trend = recent_values[-1] - recent_values[0]
            if trend > 0.1:
                predicted_stress = min(1.0, avg_stress + 0.05)
                self.model_parameters["stress_trend"] = "increasing"
            elif trend < -0.1:
                predicted_stress = max(0.0, avg_stress - 0.05)
                self.model_parameters["stress_trend"] = "decreasing"
            else:
                predicted_stress = avg_stress
                self.model_parameters["stress_trend"] = "stable"
        else:
            predicted_stress = avg_stress
        
        # Determine state
        if predicted_stress < 0.3:
            state = "relaxed"
        elif predicted_stress < 0.6:
            state = "moderate"
        else:
            state = "high"
        
        confidence = self.get_confidence()
        
        prediction = Prediction(
            domain=self.domain,
            predicted_value={
                "stress_level": predicted_stress,
                "state": state,
                "trend": self.model_parameters["stress_trend"]
            },
            confidence=confidence,
            timestamp=datetime.now(),
            prediction_horizon=horizon,
            model_parameters=self.model_parameters.copy()
        )
        
        self.predictions.append(prediction)
        return prediction
    
    def update_model(self) -> None:
        """Update stress model parameters"""
        if len(self.observations) < 3:
            return
        
        values = []
        for obs in self.observations:
            if isinstance(obs[0], (int, float)):
                values.append(obs[0])
            elif isinstance(obs[0], dict) and "stress_level" in obs[0]:
                values.append(obs[0]["stress_level"])
        
        if values:
            self.model_parameters["baseline_stress"] = sum(values) / len(values)
            
            if len(values) >= 2:
                variance = sum((v - self.model_parameters["baseline_stress"])**2 for v in values) / len(values)
                self.model_parameters["variability"] = math.sqrt(variance)


class FinancialRiskModel(PredictiveModel):
    """Predictive model for financial risk assessment"""
    
    def __init__(self):
        super().__init__(PredictionDomain.FINANCIAL_RISK)
        self.model_parameters = {
            "risk_level": "low",
            "spending_trend": "stable",
            "budget_health": 0.8
        }
    
    def generate_prediction(self, horizon: timedelta = timedelta(hours=1)) -> Prediction:
        """Predict financial risk state"""
        if len(self.observations) < 2:
            return Prediction(
                domain=self.domain,
                predicted_value={"risk_level": "unknown", "budget_health": 0.8},
                confidence=0.1,
                timestamp=datetime.now(),
                prediction_horizon=horizon,
                model_parameters=self.model_parameters.copy()
            )
        
        recent_obs = list(self.observations)[-5:]
        
        # Extract budget health
        health_values = []
        for obs in recent_obs:
            if isinstance(obs[0], dict) and "budget_health" in obs[0]:
                health_values.append(obs[0]["budget_health"])
            elif isinstance(obs[0], (int, float)):
                health_values.append(obs[0])
        
        if health_values:
            avg_health = sum(health_values) / len(health_values)
            self.model_parameters["budget_health"] = avg_health
            
            if avg_health > 0.7:
                risk_level = "low"
            elif avg_health > 0.4:
                risk_level = "moderate"
            else:
                risk_level = "high"
        else:
            avg_health = 0.8
            risk_level = "low"
        
        self.model_parameters["risk_level"] = risk_level
        
        confidence = self.get_confidence()
        
        prediction = Prediction(
            domain=self.domain,
            predicted_value={
                "risk_level": risk_level,
                "budget_health": avg_health,
                "spending_trend": self.model_parameters["spending_trend"]
            },
            confidence=confidence,
            timestamp=datetime.now(),
            prediction_horizon=horizon,
            model_parameters=self.model_parameters.copy()
        )
        
        self.predictions.append(prediction)
        return prediction
    
    def update_model(self) -> None:
        """Update financial risk model parameters"""
        # This would analyze spending patterns, budget adherence, etc.
        # For now, maintain existing parameters
        pass


class EmotionalStateModel(PredictiveModel):
    """Predictive model for user's emotional state"""
    
    def __init__(self):
        super().__init__(PredictionDomain.EMOTIONAL_STATE)
        self.model_parameters = {
            "dominant_emotion": "neutral",
            "emotional_stability": 0.8,
            "valence": 0.0,
            "arousal": 0.0
        }
    
    def generate_prediction(self, horizon: timedelta = timedelta(minutes=10)) -> Prediction:
        """Predict emotional state"""
        if len(self.observations) < 2:
            return Prediction(
                domain=self.domain,
                predicted_value={"emotion": "neutral", "valence": 0.0, "arousal": 0.0},
                confidence=0.1,
                timestamp=datetime.now(),
                prediction_horizon=horizon,
                model_parameters=self.model_parameters.copy()
            )
        
        recent_obs = list(self.observations)[-5:]
        
        # Extract emotional data
        emotions = []
        valences = []
        arousals = []
        
        for obs in recent_obs:
            if isinstance(obs[0], dict):
                emotions.append(obs[0].get("emotion", "neutral"))
                valences.append(obs[0].get("valence", 0.0))
                arousals.append(obs[0].get("arousal", 0.0))
        
        if emotions:
            # Most common emotion
            from collections import Counter
            emotion_counts = Counter(emotions)
            dominant_emotion = emotion_counts.most_common(1)[0][0]
            
            avg_valence = sum(valences) / len(valences) if valences else 0.0
            avg_arousal = sum(arousals) / len(arousals) if arousals else 0.0
            
            self.model_parameters["dominant_emotion"] = dominant_emotion
            self.model_parameters["valence"] = avg_valence
            self.model_parameters["arousal"] = avg_arousal
        else:
            dominant_emotion = "neutral"
            avg_valence = 0.0
            avg_arousal = 0.0
        
        confidence = self.get_confidence()
        
        prediction = Prediction(
            domain=self.domain,
            predicted_value={
                "emotion": dominant_emotion,
                "valence": avg_valence,
                "arousal": avg_arousal
            },
            confidence=confidence,
            timestamp=datetime.now(),
            prediction_horizon=horizon,
            model_parameters=self.model_parameters.copy()
        )
        
        self.predictions.append(prediction)
        return prediction
    
    def update_model(self) -> None:
        """Update emotional state model parameters"""
        # Calculate emotional stability based on variance
        if len(self.observations) < 3:
            return
        
        valences = []
        for obs in list(self.observations)[-10:]:
            if isinstance(obs[0], dict) and "valence" in obs[0]:
                valences.append(obs[0]["valence"])
        
        if len(valences) >= 2:
            variance = sum((v - sum(valences)/len(valences))**2 for v in valences) / len(valences)
            stability = max(0.0, 1.0 - variance)
            self.model_parameters["emotional_stability"] = stability


class WorkEnergyModel(PredictiveModel):
    """Predictive model for user's work energy and productivity state"""
    
    def __init__(self):
        super().__init__(PredictionDomain.WORK_ENERGY)
        self.model_parameters = {
            "energy_level": 0.8,
            "productivity_trend": "stable",
            "focus_quality": 0.7,
            "time_worked_today": 0.0
        }
    
    def generate_prediction(self, horizon: timedelta = timedelta(minutes=15)) -> Prediction:
        """Predict work energy state"""
        if len(self.observations) < 2:
            return Prediction(
                domain=self.domain,
                predicted_value={"energy_level": 0.8, "state": "unknown"},
                confidence=0.1,
                timestamp=datetime.now(),
                prediction_horizon=horizon,
                model_parameters=self.model_parameters.copy()
            )
        
        recent_obs = list(self.observations)[-5:]
        
        energy_values = []
        for obs in recent_obs:
            if isinstance(obs[0], dict) and "energy_level" in obs[0]:
                energy_values.append(obs[0]["energy_level"])
            elif isinstance(obs[0], (int, float)):
                energy_values.append(obs[0])
        
        if energy_values:
            avg_energy = sum(energy_values) / len(energy_values)
            
            # Detect trend
            if len(energy_values) >= 3:
                trend = energy_values[-1] - energy_values[0]
                if trend > 0.1:
                    self.model_parameters["productivity_trend"] = "increasing"
                    predicted_energy = min(1.0, avg_energy + 0.02)
                elif trend < -0.1:
                    self.model_parameters["productivity_trend"] = "decreasing"
                    predicted_energy = max(0.0, avg_energy - 0.02)
                else:
                    self.model_parameters["productivity_trend"] = "stable"
                    predicted_energy = avg_energy
            else:
                predicted_energy = avg_energy
        else:
            predicted_energy = 0.8
        
        # Determine state
        if predicted_energy > 0.7:
            state = "high"
        elif predicted_energy > 0.4:
            state = "moderate"
        else:
            state = "low"
        
        self.model_parameters["energy_level"] = predicted_energy
        
        confidence = self.get_confidence()
        
        prediction = Prediction(
            domain=self.domain,
            predicted_value={
                "energy_level": predicted_energy,
                "state": state,
                "trend": self.model_parameters["productivity_trend"]
            },
            confidence=confidence,
            timestamp=datetime.now(),
            prediction_horizon=horizon,
            model_parameters=self.model_parameters.copy()
        )
        
        self.predictions.append(prediction)
        return prediction
    
    def update_model(self) -> None:
        """Update work energy model parameters"""
        # This would analyze work patterns, breaks, focus sessions, etc.
        pass


class ActiveInferenceEngine:
    """
    Main Active Inference Engine implementing the Continuous Epistemology loop.
    
    The engine:
    1. Maintains predictive models across multiple domains
    2. Continuously generates predictions
    3. Compares predictions to actual sensory data
    4. Calculates Free Energy (surprise)
    5. Triggers WorldModel updates when surprise exceeds threshold
    """
    
    def __init__(self, surprise_threshold: float = 2.0):
        self.markov_blanket = MarkovBlanket(surprise_threshold)
        self.free_energy_calculator = FreeEnergyCalculator()
        
        # Initialize predictive models for each domain
        self.predictive_models: Dict[PredictionDomain, PredictiveModel] = {
            PredictionDomain.CODE_CONTEXT: CodeContextModel(),
            PredictionDomain.BIOMETRIC_STRESS: BiometricStressModel(),
            PredictionDomain.FINANCIAL_RISK: FinancialRiskModel(),
            PredictionDomain.EMOTIONAL_STATE: EmotionalStateModel(),
            PredictionDomain.WORK_ENERGY: WorkEnergyModel()
        }
        
        self.surprise_events: deque = deque(maxlen=100)
        self.world_model_update_callbacks: List[Callable] = []
        self.is_running = False
        self.update_interval = 5.0  # seconds
        
        logger.info("Active Inference Engine initialized")
    
    def register_world_model_update_callback(self, callback: Callable) -> None:
        """Register a callback to be triggered on world model updates"""
        self.world_model_update_callbacks.append(callback)
        logger.info(f"Registered world model update callback: {callback.__name__}")
    
    def add_sensory_input(self, domain: PredictionDomain, value: Any, metadata: Dict = None) -> None:
        """
        Add sensory input to the system.
        
        This is the main entry point for external data streams.
        """
        state = State(
            state_id=f"{domain.value}_{datetime.now().timestamp()}",
            state_type=StateType.SENSORY,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.markov_blanket.add_sensory_state(state)
        
        # Add observation to the appropriate predictive model
        if domain in self.predictive_models:
            self.predictive_models[domain].add_observation(value)
        
        logger.debug(f"Added sensory input for domain {domain.value}")
    
    def generate_predictions(self) -> Dict[PredictionDomain, Prediction]:
        """Generate predictions for all domains"""
        predictions = {}
        
        for domain, model in self.predictive_models.items():
            try:
                prediction = model.generate_prediction()
                predictions[domain] = prediction
                
                # Store prediction as internal state
                state = State(
                    state_id=f"prediction_{domain.value}_{datetime.now().timestamp()}",
                    state_type=StateType.INTERNAL,
                    value=prediction.to_dict(),
                    timestamp=datetime.now(),
                    confidence=prediction.confidence,
                    metadata={"domain": domain.value}
                )
                self.markov_blanket.add_internal_state(state)
                
            except Exception as e:
                logger.error(f"Error generating prediction for {domain.value}: {e}")
        
        return predictions
    
    def detect_surprise(self, predictions: Dict[PredictionDomain, Prediction]) -> List[SurpriseEvent]:
        """
        Detect surprise by comparing predictions to actual sensory data.
        
        Returns list of surprise events that exceed the threshold.
        """
        surprise_events = []
        
        for domain, prediction in predictions.items():
            # Get recent sensory data for this domain
            recent_sensory = self.markov_blanket.get_recent_sensory_states(seconds=10)
            
            # Filter for this domain
            domain_sensory = [
                s for s in recent_sensory 
                if s.metadata.get("domain") == domain.value or 
                   domain.value in s.state_id
            ]
            
            if not domain_sensory:
                continue
            
            # Get the most recent sensory data
            latest_sensory = domain_sensory[-1]
            
            # Calculate Free Energy (surprise)
            free_energy = self.free_energy_calculator.calculate_free_energy(
                predicted=prediction.predicted_value,
                actual=latest_sensory.value,
                confidence=prediction.confidence
            )
            
            # Create surprise event
            surprise = SurpriseEvent(
                domain=domain,
                predicted_value=prediction.predicted_value,
                actual_value=latest_sensory.value,
                surprise_magnitude=free_energy,
                timestamp=datetime.now(),
                threshold_exceeded=free_energy > self.markov_blanket.surprise_threshold
            )
            
            surprise_events.append(surprise)
            self.surprise_events.append(surprise)
            
            if surprise.threshold_exceeded:
                logger.warning(
                    f"Surprise threshold exceeded for {domain.value}: "
                    f"magnitude={free_energy:.4f}"
                )
        
        return surprise_events
    
    def trigger_world_model_update(self, surprise_events: List[SurpriseEvent]) -> None:
        """
        Trigger world model update when surprise is detected.
        
        This updates the predictive models to reduce future surprise.
        """
        threshold_exceeded = [s for s in surprise_events if s.threshold_exceeded]
        
        if not threshold_exceeded:
            return
        
        logger.info(f"Triggering world model update for {len(threshold_exceeded)} domains")
        
        # Update models for domains with high surprise
        for surprise in threshold_exceeded:
            domain = surprise.domain
            if domain in self.predictive_models:
                try:
                    self.predictive_models[domain].update_model()
                    logger.info(f"Updated predictive model for {domain.value}")
                except Exception as e:
                    logger.error(f"Error updating model for {domain.value}: {e}")
        
        # Call registered callbacks
        for callback in self.world_model_update_callbacks:
            try:
                callback(threshold_exceeded)
            except Exception as e:
                logger.error(f"Error in world model update callback: {e}")
    
    async def epistemology_loop(self) -> None:
        """
        Continuous Epistemology loop.
        
        This is the main loop that:
        1. Generates predictions
        2. Detects surprise
        3. Updates world model when needed
        """
        logger.info("Starting Continuous Epistemology loop")
        
        while self.is_running:
            try:
                # Generate predictions
                predictions = self.generate_predictions()
                
                # Detect surprise
                surprise_events = self.detect_surprise(predictions)
                
                # Update world model if surprise detected
                if surprise_events:
                    self.trigger_world_model_update(surprise_events)
                
                # Clean up old states
                self.markov_blanket.clear_old_states(seconds=3600)
                
                # Wait for next iteration
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in epistemology loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    def start(self) -> None:
        """Start the active inference engine"""
        if self.is_running:
            logger.warning("Active Inference Engine is already running")
            return
        
        self.is_running = True
        logger.info("Active Inference Engine started")
        
        # Start the epistemology loop in the background
        asyncio.create_task(self.epistemology_loop())
    
    def stop(self) -> None:
        """Stop the active inference engine"""
        self.is_running = False
        logger.info("Active Inference Engine stopped")
    
    def get_system_state(self) -> Dict:
        """Get current system state for monitoring"""
        return {
            "is_running": self.is_running,
            "internal_states_count": len(self.markov_blanket.internal_states),
            "sensory_states_count": len(self.markov_blanket.sensory_states),
            "active_states_count": len(self.markov_blanket.active_states),
            "surprise_events_count": len(self.surprise_events),
            "average_free_energy": self.free_energy_calculator.get_average_free_energy(),
            "predictive_models": {
                domain.value: {
                    "observations": len(model.observations),
                    "predictions": len(model.predictions),
                    "confidence": model.get_confidence()
                }
                for domain, model in self.predictive_models.items()
            }
        }
    
    def export_state(self) -> Dict:
        """Export system state for persistence"""
        return {
            "markov_blanket": {
                "internal_states": [s.to_dict() for s in self.markov_blanket.internal_states.values()],
                "sensory_states": [s.to_dict() for s in self.markov_blanket.sensory_states.values()],
                "active_states": [s.to_dict() for s in self.markov_blanket.active_states.values()]
            },
            "surprise_events": [s.to_dict() for s in self.surprise_events],
            "predictive_models": {
                domain.value: {
                    "model_parameters": model.model_parameters,
                    "observations_count": len(model.observations)
                }
                for domain, model in self.predictive_models.items()
            },
            "system_state": self.get_system_state()
        }


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Create the engine
        engine = ActiveInferenceEngine(surprise_threshold=1.5)
        
        # Register a callback for world model updates
        def on_world_model_update(surprises):
            print(f"World model update triggered by {len(surprises)} surprises")
            for surprise in surprises:
                print(f"  - {surprise.domain.value}: {surprise.surprise_magnitude:.4f}")
        
        engine.register_world_model_update_callback(on_world_model_update)
        
        # Start the engine
        engine.start()
        
        # Simulate some sensory inputs
        print("\nSimulating sensory inputs...")
        
        # Code context inputs
        engine.add_sensory_input(
            PredictionDomain.CODE_CONTEXT,
            {"state": "coding", "files": ["main.py", "utils.py"], "language": "python"}
        )
        
        # Biometric stress inputs
        engine.add_sensory_input(
            PredictionDomain.BIOMETRIC_STRESS,
            {"stress_level": 0.4, "heart_rate": 75}
        )
        
        # Work energy inputs
        engine.add_sensory_input(
            PredictionDomain.WORK_ENERGY,
            {"energy_level": 0.8, "focus_quality": 0.7}
        )
        
        # Let the loop run for a bit
        await asyncio.sleep(15)
        
        # Add some surprising inputs
        print("\nAdding surprising inputs...")
        engine.add_sensory_input(
            PredictionDomain.BIOMETRIC_STRESS,
            {"stress_level": 0.9, "heart_rate": 120}  # High stress surprise
        )
        
        await asyncio.sleep(10)
        
        # Print system state
        print("\nSystem State:")
        import json
        print(json.dumps(engine.get_system_state(), indent=2))
        
        # Stop the engine
        engine.stop()
        print("\nEngine stopped")
    
    asyncio.run(main())
