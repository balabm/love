"""
Teleological Feedback Loop - Outcome vs. Prediction Learning

Intelligence requires learning from the delta between expectation and reality. When the Causal
Simulator predicts an outcome, the system must verify if that outcome actually happened in the
physical world.

Implements RealityAnchor for tracking interventions, background daemon for outcome verification,
and automatic meta-learning integration for prediction error correction.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from collections import deque
import hashlib
import json
import threading
import time
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InterventionType(Enum):
    """Types of proactive interventions"""
    SCREEN_LOCK = "screen_lock"  # Lock screen to prevent distraction
    TRADE_SUGGESTION = "trade_suggestion"  # Suggest financial trade
    CODE_GENERATION = "code_generation"  # Generate code
    ALERT = "alert"  # Send alert/notification
    TASK_SUGGESTION = "task_suggestion"  # Suggest task
    BREAK_REMINDER = "break_reminder"  # Remind to take break
    MEETING_NUDGE = "meeting_nudge"  # Nudge for meeting
    WORK_LIMIT_WARNING = "work_limit_warning"  # Warn about work limit
    FINANCE_ALERT = "finance_alert"  # Financial market alert


class VerificationMethod(Enum):
    """Methods for verifying intervention outcomes"""
    OS_SENSORS = "os_sensors"  # Use OS awareness to verify
    GITHUB_COMMITS = "github_commits"  # Check GitHub for code changes
    BINANCE_API = "binance_api"  # Check financial markets
    USER_FEEDBACK = "user_feedback"  # Ask user for feedback
    SYSTEM_LOGS = "system_logs"  # Check system logs
    AUTOMATIC = "automatic"  # Automatic verification


@dataclass
class RealityAnchor:
    """
    Temporal anchor dropped when LOVE executes a proactive intervention.
    
    Contains the expected outcome and metadata for later verification.
    """
    anchor_id: str
    intervention_type: InterventionType
    intervention_description: str
    expected_outcome: Dict[str, Any]  # What LOVE predicted would happen
    prediction_confidence: float  # Confidence in the prediction
    actual_outcome: Optional[Dict[str, Any]] = None  # What actually happened
    verification_method: VerificationMethod = VerificationMethod.AUTOMATIC
    verification_time: Optional[datetime] = None  # When to verify
    verification_delay: timedelta = field(default_factory=lambda: timedelta(hours=1))
    outcome_verified: bool = False
    prediction_error: Optional[float] = None  # Delta between prediction and reality
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "anchor_id": self.anchor_id,
            "intervention_type": self.intervention_type.value,
            "intervention_description": self.intervention_description,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "prediction_confidence": self.prediction_confidence,
            "verification_method": self.verification_method.value,
            "verification_time": self.verification_time.isoformat() if self.verification_time else None,
            "verification_delay_hours": self.verification_delay.total_seconds() / 3600,
            "outcome_verified": self.outcome_verified,
            "prediction_error": self.prediction_error,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class PredictionError:
    """Represents a prediction error with learning implications"""
    error_id: str
    anchor_id: str
    intervention_type: InterventionType
    expected_outcome: Dict[str, Any]
    actual_outcome: Dict[str, Any]
    error_magnitude: float  # How wrong the prediction was
    error_type: str  # Type of error (overestimate, underestimate, wrong direction)
    severity: float  # 0.0 to 1.0
    learning_implications: List[str]  # What to learn from this error
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "error_id": self.error_id,
            "anchor_id": self.anchor_id,
            "intervention_type": self.intervention_type.value,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "error_magnitude": self.error_magnitude,
            "error_type": self.error_type,
            "severity": self.severity,
            "learning_implications": self.learning_implications,
            "timestamp": self.timestamp.isoformat()
        }


class OutcomeVerifier:
    """
    Verifies intervention outcomes using various methods.
    
    Uses OS sensors, GitHub commits, Binance API, and other sources
    to determine what actually happened after an intervention.
    """
    
    def __init__(self):
        self.verification_methods = {
            VerificationMethod.OS_SENSORS: self._verify_with_os_sensors,
            VerificationMethod.GITHUB_COMMITS: self._verify_with_github,
            VerificationMethod.BINANCE_API: self._verify_with_binance,
            VerificationMethod.USER_FEEDBACK: self._verify_with_user_feedback,
            VerificationMethod.SYSTEM_LOGS: self._verify_with_system_logs,
            VerificationMethod.AUTOMATIC: self._verify_automatically
        }
        self.verification_history: deque = deque(maxlen=1000)
        
    def verify_outcome(
        self, 
        anchor: RealityAnchor
    ) -> Dict[str, Any]:
        """Verify the actual outcome of an intervention"""
        verifier = self.verification_methods.get(anchor.verification_method)
        
        if verifier:
            try:
                actual_outcome = verifier(anchor)
                return {
                    "success": True,
                    "actual_outcome": actual_outcome,
                    "verification_method": anchor.verification_method.value,
                    "verification_time": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error verifying outcome with {anchor.verification_method.value}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "verification_method": anchor.verification_method.value
                }
        else:
            logger.warning(f"No verifier for method {anchor.verification_method.value}")
            return {
                "success": False,
                "error": f"No verifier for {anchor.verification_method.value}",
                "verification_method": anchor.verification_method.value
            }
    
    def _verify_with_os_sensors(self, anchor: RealityAnchor) -> Dict[str, Any]:
        """Verify outcome using OS sensors (awareness system)"""
        try:
            from core.awareness import get_awareness
            awareness = get_awareness()
            snapshot = awareness.get_snapshot()
            
            # Extract relevant information based on intervention type
            outcome = {}
            
            if anchor.intervention_type == InterventionType.SCREEN_LOCK:
                outcome["screen_locked"] = snapshot.get("screen_locked", False)
                outcome["user_activity"] = snapshot.get("current_activity", "unknown")
            
            elif anchor.intervention_type == InterventionType.BREAK_REMINDER:
                outcome["user_took_break"] = snapshot.get("idle_time", 0) > 300  # 5 minutes idle
                outcome["current_activity"] = snapshot.get("current_activity", "unknown")
            
            elif anchor.intervention_type == InterventionType.WORK_LIMIT_WARNING:
                outcome["work_hours"] = snapshot.get("work_hours", 0)
                outcome["user_stopped_working"] = snapshot.get("idle_time", 0) > 600  # 10 minutes idle
            
            else:
                outcome["snapshot"] = snapshot
            
            return outcome
            
        except ImportError:
            logger.warning("Awareness module not available")
            return {"error": "Awareness module not available"}
        except Exception as e:
            logger.error(f"Error verifying with OS sensors: {e}")
            return {"error": str(e)}
    
    def _verify_with_github(self, anchor: RealityAnchor) -> Dict[str, Any]:
        """Verify outcome using GitHub commits"""
        try:
            # Check if code was committed as expected
            from integrations.github_monitor import get_github_monitor
            gh = get_github_monitor()
            
            recent_events = gh.get_recent_events(10)
            
            outcome = {
                "recent_commits": len(recent_events),
                "commit_messages": [e.get("message", "") for e in recent_events]
            }
            
            # Check if expected code generation happened
            if "code_generated" in anchor.expected_outcome:
                outcome["code_committed"] = any(
                    "generated" in msg.lower() or "love" in msg.lower()
                    for msg in outcome["commit_messages"]
                )
            
            return outcome
            
        except ImportError:
            logger.warning("GitHub monitor not available")
            return {"error": "GitHub monitor not available"}
        except Exception as e:
            logger.error(f"Error verifying with GitHub: {e}")
            return {"error": str(e)}
    
    def _verify_with_binance(self, anchor: RealityAnchor) -> Dict[str, Any]:
        """Verify outcome using Binance API"""
        try:
            from tools.finance import get_market_signal
            from integrations.finance_intelligence import get_finance_intelligence
            
            # Get current market state
            finance = get_finance_intelligence()
            prices = finance.get_prices()
            
            outcome = {
                "current_prices": prices,
                "market_state": "active" if prices else "inactive"
            }
            
            # Check if expected trade outcome happened
            if "trade_suggestion" in anchor.expected_outcome:
                expected_symbol = anchor.expected_outcome.get("trade_suggestion", {}).get("symbol")
                if expected_symbol:
                    outcome["symbol_price"] = prices.get(expected_symbol, {}).get("price")
            
            return outcome
            
        except ImportError:
            logger.warning("Finance tools not available")
            return {"error": "Finance tools not available"}
        except Exception as e:
            logger.error(f"Error verifying with Binance: {e}")
            return {"error": str(e)}
    
    def _verify_with_user_feedback(self, anchor: RealityAnchor) -> Dict[str, Any]:
        """Verify outcome by asking user for feedback"""
        # This would trigger a user prompt
        # For now, return placeholder
        return {
            "user_feedback_requested": True,
            "feedback_pending": True,
            "note": "User feedback verification not implemented"
        }
    
    def _verify_with_system_logs(self, anchor: RealityAnchor) -> Dict[str, Any]:
        """Verify outcome using system logs"""
        try:
            # Check system logs for intervention results
            log_file = Path(__file__).parent.parent / "data" / "intervention_log.jsonl"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Look for log entries related to this intervention
                relevant_logs = [
                    json.loads(line) for line in lines
                    if anchor.anchor_id in line
                ]
                
                return {
                    "log_entries_found": len(relevant_logs),
                    "relevant_logs": relevant_logs
                }
            else:
                return {"error": "Log file not found"}
                
        except Exception as e:
            logger.error(f"Error verifying with system logs: {e}")
            return {"error": str(e)}
    
    def _verify_automatically(self, anchor: RealityAnchor) -> Dict[str, Any]:
        """Automatic verification based on system state"""
        # Use OS sensors as default automatic verification
        return self._verify_with_os_sensors(anchor)


class PredictionErrorAnalyzer:
    """
    Analyzes prediction errors and determines learning implications.
    
    Calculates prediction error magnitude, determines error type,
    and identifies what should be learned from the error.
    """
    
    def __init__(self):
        self.error_history: deque = deque(maxlen=1000)
        self.error_patterns: Dict[str, int] = {}  # Track error patterns
        
    def calculate_prediction_error(
        self, 
        expected: Dict[str, Any], 
        actual: Dict[str, Any],
        intervention_type: InterventionType
    ) -> PredictionError:
        """Calculate prediction error and learning implications"""
        error_id = hashlib.md5(
            f"{intervention_type.value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Calculate error magnitude
        error_magnitude = self._calculate_error_magnitude(expected, actual)
        
        # Determine error type
        error_type = self._determine_error_type(expected, actual)
        
        # Determine severity
        severity = min(1.0, error_magnitude)  # Scale to 0-1
        
        # Determine learning implications
        learning_implications = self._determine_learning_implications(
            expected, actual, intervention_type, error_type, severity
        )
        
        error = PredictionError(
            error_id=error_id,
            anchor_id="",  # Will be set by caller
            intervention_type=intervention_type,
            expected_outcome=expected,
            actual_outcome=actual,
            error_magnitude=error_magnitude,
            error_type=error_type,
            severity=severity,
            learning_implications=learning_implications
        )
        
        self.error_history.append(error)
        
        # Track error patterns
        pattern_key = f"{intervention_type.value}_{error_type}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        logger.info(f"Calculated prediction error: {error_type} (magnitude: {error_magnitude:.2f}, severity: {severity:.2f})")
        
        return error
    
    def _calculate_error_magnitude(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Calculate the magnitude of prediction error"""
        # Simple error calculation based on key differences
        error_score = 0.0
        
        # Check for boolean outcomes
        for key in expected:
            if key in actual:
                if isinstance(expected[key], bool) and isinstance(actual[key], bool):
                    if expected[key] != actual[key]:
                        error_score += 0.5
                elif isinstance(expected[key], (int, float)) and isinstance(actual[key], (int, float)):
                    # Relative error
                    if expected[key] != 0:
                        error_score += abs(expected[key] - actual[key]) / abs(expected[key])
                    else:
                        error_score += abs(expected[key] - actual[key])
        
        # Normalize to 0-1 range
        return min(error_score, 1.0)
    
    def _determine_error_type(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> str:
        """Determine the type of prediction error"""
        # Check for overestimation
        overestimated = False
        underestimated = False
        
        for key in expected:
            if key in actual:
                if isinstance(expected[key], (int, float)) and isinstance(actual[key], (int, float)):
                    if expected[key] > actual[key]:
                        overestimated = True
                    elif expected[key] < actual[key]:
                        underestimated = True
        
        if overestimated and not underestimated:
            return "overestimate"
        elif underestimated and not overestimated:
            return "underestimate"
        elif overestimated and underestimated:
            return "mixed"
        else:
            return "direction_error"
    
    def _determine_learning_implications(
        self, 
        expected: Dict[str, Any], 
        actual: Dict[str, Any],
        intervention_type: InterventionType,
        error_type: str,
        severity: float
    ) -> List[str]:
        """Determine what should be learned from this error"""
        implications = []
        
        # High severity errors require more learning
        if severity > 0.7:
            implications.append("high_severity_error_requires_weight_adjustment")
        
        # Type-specific implications
        if error_type == "overestimate":
            implications.append("reduce_prediction_confidence")
            implications.append("adjust_expected_outcome_downward")
        elif error_type == "underestimate":
            implications.append("increase_prediction_confidence")
            implications.append("adjust_expected_outcome_upward")
        
        # Intervention-specific implications
        if intervention_type == InterventionType.TRADE_SUGGESTION:
            if severity > 0.5:
                implications.append("financial_prediction_model_needs_retraining")
                implications.append("reduce_trade_suggestion_frequency")
        
        elif intervention_type == InterventionType.SCREEN_LOCK:
            if error_type == "overestimate":
                implications.append("screen_lock_intervention_too_aggressive")
            elif error_type == "underestimate":
                implications.append("screen_lock_intervention_not_effective")
        
        elif intervention_type == InterventionType.CODE_GENERATION:
            if severity > 0.6:
                implications.append("code_generation_predictions_inaccurate")
                implications.append("reduce_autonomous_code_generation")
        
        # General implications
        if severity > 0.8:
            implications.append("trigger_meta_learning_for_decision_reweighting")
        
        return implications


class MetaLearningIntegrator:
    """
    Integrates with meta-learning system to correct prediction errors.
    
    When prediction errors are high, triggers meta_learning.py to rewrite
    the weights of decision-making algorithms to prevent similar errors.
    """
    
    def __init__(self):
        self.integration_history: deque = deque(maxlen=500)
        
    def trigger_meta_learning(self, prediction_error: PredictionError) -> bool:
        """Trigger meta-learning to correct prediction error"""
        try:
            from evolution.meta_learning import get_meta_learning_engine
            
            meta_engine = get_meta_learning_engine()
            
            # Log the prediction error as a "solution" for learning
            meta_engine.log_solution(
                problem_description=f"Prediction error in {prediction_error.intervention_type.value}",
                solution_type=self._map_to_solution_type(prediction_error.intervention_type),
                original_approach=f"Predicted: {prediction_error.expected_outcome}",
                refined_approach=f"Actual: {prediction_error.actual_outcome}",
                success_metrics={
                    "error_magnitude": prediction_error.error_magnitude,
                    "error_corrected": 1.0 - prediction_error.error_magnitude
                },
                context={
                    "intervention_type": prediction_error.intervention_type.value,
                    "error_type": prediction_error.error_type,
                    "severity": prediction_error.severity
                },
                execution_time=0.1,
                iterations=1
            )
            
            # Extract principle from error
            principle = self._extract_error_principle(prediction_error)
            
            if principle:
                logger.info(f"Extracted principle from prediction error: {principle}")
            
            self.integration_history.append({
                "error_id": prediction_error.error_id,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
            logger.info(f"Triggered meta-learning for prediction error {prediction_error.error_id}")
            return True
            
        except ImportError:
            logger.warning("Meta-learning module not available")
            return False
        except Exception as e:
            logger.error(f"Error triggering meta-learning: {e}")
            return False
    
    def _map_to_solution_type(self, intervention_type: InterventionType) -> str:
        """Map intervention type to solution type for meta-learning"""
        mapping = {
            InterventionType.TRADE_SUGGESTION: "optimization",
            InterventionType.CODE_GENERATION: "algorithmic",
            InterventionType.SCREEN_LOCK: "planning",
            InterventionType.ALERT: "communication",
            InterventionType.TASK_SUGGESTION: "planning",
            InterventionType.BREAK_REMINDER: "planning",
            InterventionType.MEETING_NUDGE: "planning",
            InterventionType.WORK_LIMIT_WARNING: "planning",
            InterventionType.FINANCE_ALERT: "optimization"
        }
        return mapping.get(intervention_type, "heuristic")
    
    def _extract_error_principle(self, prediction_error: PredictionError) -> str:
        """Extract principle from prediction error"""
        principles = []
        
        # Extract principles from learning implications
        for implication in prediction_error.learning_implications:
            if "reduce" in implication:
                principles.append(f"Reduce {implication.replace('reduce_', '')}")
            elif "increase" in implication:
                principles.append(f"Increase {implication.replace('increase_', '')}")
            elif "adjust" in implication:
                principles.append(f"Adjust {implication.replace('adjust_', '')}")
        
        if principles:
            return f"Prediction error correction: {', '.join(principles)}"
        else:
            return f"Correct {prediction_error.intervention_type.value} prediction errors"


class TeleologicalFeedbackDaemon:
    """
    Background daemon that wakes up after interventions to verify outcomes.
    
    Monitors RealityAnchors and triggers verification when the delay has passed.
    Calculates prediction errors and triggers meta-learning when errors are high.
    """
    
    def __init__(self, check_interval_minutes: int = 5):
        self.anchors: Dict[str, RealityAnchor] = {}
        self.verifier = OutcomeVerifier()
        self.error_analyzer = PredictionErrorAnalyzer()
        self.meta_learning_integrator = MetaLearningIntegrator()
        
        self.check_interval = check_interval_minutes
        self.running = False
        self.lock = threading.Lock()
        
    def drop_anchor(self, anchor: RealityAnchor) -> None:
        """Drop a temporal anchor for an intervention"""
        with self.lock:
            self.anchors[anchor.anchor_id] = anchor
            logger.info(f"Dropped anchor {anchor.anchor_id} for {anchor.intervention_type.value}")
    
    def start_daemon(self) -> None:
        """Start the background daemon"""
        self.running = True
        logger.info(f"Starting Teleological Feedback Daemon (check interval: {self.check_interval} minutes)")
        
        def daemon_loop():
            while self.running:
                try:
                    self._check_anchors()
                    time.sleep(self.check_interval * 60)
                except Exception as e:
                    logger.error(f"Error in daemon loop: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=daemon_loop, daemon=True)
        thread.start()
    
    def stop_daemon(self) -> None:
        """Stop the daemon"""
        self.running = False
        logger.info("Stopped Teleological Feedback Daemon")
    
    def _check_anchors(self) -> None:
        """Check all anchors for verification"""
        now = datetime.now()
        anchors_to_verify = []
        
        with self.lock:
            for anchor_id, anchor in self.anchors.items():
                if not anchor.outcome_verified:
                    # Check if verification time has arrived
                    if anchor.verification_time:
                        if now >= anchor.verification_time:
                            anchors_to_verify.append(anchor)
                    else:
                        # Calculate verification time if not set
                        verification_time = anchor.timestamp + anchor.verification_delay
                        if now >= verification_time:
                            anchor.verification_time = verification_time
                            anchors_to_verify.append(anchor)
        
        # Verify anchors
        for anchor in anchors_to_verify:
            self._verify_anchor(anchor)
    
    def _verify_anchor(self, anchor: RealityAnchor) -> None:
        """Verify a specific anchor"""
        logger.info(f"Verifying anchor {anchor.anchor_id}")
        
        # Verify outcome
        verification_result = self.verifier.verify_outcome(anchor)
        
        if verification_result.get("success"):
            anchor.actual_outcome = verification_result.get("actual_outcome")
            anchor.outcome_verified = True
            
            # Calculate prediction error
            prediction_error = self.error_analyzer.calculate_prediction_error(
                anchor.expected_outcome,
                anchor.actual_outcome,
                anchor.intervention_type
            )
            prediction_error.anchor_id = anchor.anchor_id
            
            anchor.prediction_error = prediction_error.error_magnitude
            
            # If error is high, trigger meta-learning
            if prediction_error.severity > 0.5:  # High severity threshold
                logger.warning(f"High prediction error detected: {prediction_error.error_magnitude:.2f}")
                self.meta_learning_integrator.trigger_meta_learning(prediction_error)
            
            logger.info(f"Anchor {anchor.anchor_id} verified: prediction error {prediction_error.error_magnitude:.2f}")
        else:
            logger.error(f"Failed to verify anchor {anchor.anchor_id}: {verification_result.get('error')}")
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of feedback loop activity"""
        with self.lock:
            total_anchors = len(self.anchors)
            verified_anchors = sum(1 for a in self.anchors.values() if a.outcome_verified)
            pending_anchors = total_anchors - verified_anchors
            
            # Calculate average prediction error
            errors = [a.prediction_error for a in self.anchors.values() if a.prediction_error is not None]
            avg_error = sum(errors) / len(errors) if errors else 0.0
            
            # Get error patterns
            error_patterns = self.error_analyzer.error_patterns
            
            return {
                "total_anchors": total_anchors,
                "verified_anchors": verified_anchors,
                "pending_anchors": pending_anchors,
                "verification_rate": verified_anchors / total_anchors if total_anchors > 0 else 0.0,
                "average_prediction_error": avg_error,
                "error_patterns": error_patterns,
                "meta_learning_integrations": len(self.meta_learning_integrator.integration_history)
            }


class TeleologicalFeedbackEngine:
    """
    Main engine coordinating the teleological feedback loop.
    
    Manages RealityAnchors, outcome verification, prediction error analysis,
    and meta-learning integration for continuous improvement.
    """
    
    def __init__(self, check_interval_minutes: int = 5):
        self.daemon = TeleologicalFeedbackDaemon(check_interval_minutes)
        self.anchor_history: deque = deque(maxlen=2000)
        
    def drop_anchor(
        self, 
        intervention_type: InterventionType,
        description: str,
        expected_outcome: Dict[str, Any],
        prediction_confidence: float,
        verification_delay: timedelta = None,
        verification_method: VerificationMethod = VerificationMethod.AUTOMATIC
    ) -> RealityAnchor:
        """Drop a temporal anchor for an intervention"""
        anchor_id = hashlib.md5(
            f"{intervention_type.value}_{description}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        if verification_delay is None:
            verification_delay = timedelta(hours=1)  # Default 1 hour
        
        anchor = RealityAnchor(
            anchor_id=anchor_id,
            intervention_type=intervention_type,
            intervention_description=description,
            expected_outcome=expected_outcome,
            prediction_confidence=prediction_confidence,
            verification_method=verification_method,
            verification_delay=verification_delay
        )
        
        self.daemon.drop_anchor(anchor)
        self.anchor_history.append(anchor)
        
        logger.info(f"Dropped anchor {anchor_id} for {intervention_type.value}")
        return anchor
    
    def start_feedback_loop(self) -> None:
        """Start the teleological feedback loop"""
        self.daemon.start_daemon()
    
    def stop_feedback_loop(self) -> None:
        """Stop the teleological feedback loop"""
        self.daemon.stop_daemon()
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of feedback loop activity"""
        return self.daemon.get_feedback_summary()


# Singleton instance
_teleological_engine_instance: Optional[TeleologicalFeedbackEngine] = None
_engine_lock = threading.Lock()

def get_teleological_engine(check_interval_minutes: int = 5) -> TeleologicalFeedbackEngine:
    """Get the singleton Teleological Feedback Engine instance"""
    global _teleological_engine_instance
    with _engine_lock:
        if _teleological_engine_instance is None:
            _teleological_engine_instance = TeleologicalFeedbackEngine(check_interval_minutes)
            _teleological_engine_instance.start_feedback_loop()
        return _teleological_engine_instance


if __name__ == "__main__":
    # Test the Teleological Feedback Engine
    print("Testing Teleological Feedback Engine...")
    
    engine = get_teleological_engine()
    
    # Test dropping an anchor
    anchor = engine.drop_anchor(
        intervention_type=InterventionType.TRADE_SUGGESTION,
        description="Suggested BTC trade based on market analysis",
        expected_outcome={
            "trade_executed": True,
            "profit_expected": 0.05  # 5% profit expected
        },
        prediction_confidence=0.8,
        verification_delay=timedelta(hours=2),
        verification_method=VerificationMethod.BINANCE_API
    )
    
    print(f"\nDropped anchor: {anchor.anchor_id}")
    print(f"Intervention: {anchor.intervention_type.value}")
    print(f"Expected outcome: {anchor.expected_outcome}")
    print(f"Verification delay: {anchor.verification_delay}")
    
    # Test dropping another anchor with automatic verification
    anchor2 = engine.drop_anchor(
        intervention_type=InterventionType.SCREEN_LOCK,
        description="Locked screen to prevent distraction during deep work",
        expected_outcome={
            "screen_locked": True,
            "user_maintained_focus": True
        },
        prediction_confidence=0.9,
        verification_delay=timedelta(minutes=5),  # Short delay for testing
        verification_method=VerificationMethod.OS_SENSORS
    )
    
    print(f"\nDropped anchor: {anchor2.anchor_id}")
    print(f"Intervention: {anchor2.intervention_type.value}")
    print(f"Expected outcome: {anchor2.expected_outcome}")
    
    # Wait for verification (short delay for testing)
    print("\nWaiting for verification...")
    time.sleep(10)
    
    # Get feedback summary
    summary = engine.get_feedback_summary()
    print(f"\nFeedback Summary: {summary}")
    
    # Stop engine
    engine.stop_feedback_loop()
    
    print("\nTeleological Feedback Engine test completed successfully!")