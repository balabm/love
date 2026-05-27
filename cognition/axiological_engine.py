"""
Axiological Engine - The "Is It Useful?" Arbiter

Computation is expensive; attention is finite. The system must possess a Utility Function
that strictly measures the real-world value of its own actions against Karthi's overarching
life goals.

Before executing any background task, the Axiological Engine calculates a Utility Score.
If (Predicted Outcome Value) / (Compute Cost + User Interruption Friction) < Threshold,
the Engine must brutally kill the process and log the abortion reason.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
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


class CoreTenet(Enum):
    """Karthi's Core Life Tenets as vectors"""
    PROTECT_WORK_LIMIT = "protect_work_limit"  # Protect 9-hour work limit
    GROW_BUSINESS = "grow_business"  # Grow pizzeria business
    SHIP_UNITY_GAME = "ship_unity_game"  # Ship Unity game
    MAINTAIN_SANITY = "maintain_sanity"  # Maintain mental health
    FINANCIAL_HEALTH = "financial_health"  # Financial stability
    RELATIONSHIP_MAINTENANCE = "relationship_maintenance"  # Personal relationships
    SKILL_DEVELOPMENT = "skill_development"  # Continuous learning
    PHYSICAL_HEALTH = "physical_health"  # Physical well-being


class TaskCategory(Enum):
    """Categories of tasks the system might execute"""
    MARKET_ANALYSIS = "market_analysis"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    SYSTEM_MAINTENANCE = "system_maintenance"


class UserState(Enum):
    """User's current state affecting utility calculation"""
    HIGH_FLOW = "high_flow"  # Deep work, high productivity
    LOW_ENERGY = "low_energy"  # Tired, drained
    FOCUSED = "focused"  # Concentrated on specific task
    DISTRACTED = "distracted"  # Scattered attention
    STRESSED = "stressed"  # High stress, low capacity
    RELAXED = "relaxed"  # Calm, receptive
    OFF_DUTY = "off_duty"  # Not working, personal time


@dataclass
class TenetVector:
    """Vector representation of a core tenet"""
    tenet: CoreTenet
    weight: float  # Importance weight (0.0 to 1.0)
    current_value: float  # Current satisfaction level (0.0 to 1.0)
    target_value: float  # Target satisfaction level (0.0 to 1.0)
    decay_rate: float  # How fast this tenet decays without attention
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "tenet": self.tenet.value,
            "weight": self.weight,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "decay_rate": self.decay_rate,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class ActionProposal:
    """A proposed action for utility evaluation"""
    action_id: str
    task_category: TaskCategory
    description: str
    predicted_outcome: Dict[str, Any]  # Expected results
    compute_cost: float  # Estimated computation cost (0.0 to 1.0)
    interruption_friction: float  # User interruption cost (0.0 to 1.0)
    estimated_duration: timedelta
    tenet_alignment: Dict[CoreTenet, float]  # Alignment with each tenet
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "action_id": self.action_id,
            "task_category": self.task_category.value,
            "description": self.description,
            "predicted_outcome": self.predicted_outcome,
            "compute_cost": self.compute_cost,
            "interruption_friction": self.interruption_friction,
            "estimated_duration_seconds": self.estimated_duration.total_seconds(),
            "tenet_alignment": {k.value: v for k, v in self.tenet_alignment.items()},
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class UtilityEvaluation:
    """Result of utility evaluation for an action"""
    evaluation_id: str
    action_id: str
    utility_score: float  # Final utility score
    predicted_value: float  # Predicted outcome value
    total_cost: float  # Compute cost + interruption friction
    threshold: float  # Utility threshold
    approved: bool  # Whether action is approved
    rejection_reason: Optional[str]  # Reason for rejection
    tenet_contributions: Dict[CoreTenet, float]  # How each tenet contributed
    user_state: UserState
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "evaluation_id": self.evaluation_id,
            "action_id": self.action_id,
            "utility_score": self.utility_score,
            "predicted_value": self.predicted_value,
            "total_cost": self.total_cost,
            "threshold": self.threshold,
            "approved": self.approved,
            "rejection_reason": self.rejection_reason,
            "tenet_contributions": {k.value: v for k, v in self.tenet_contributions.items()},
            "user_state": self.user_state.value,
            "timestamp": self.timestamp.isoformat()
        }


class TenetManager:
    """
    Manages Karthi's Core Tenets as vectors.
    
    Maintains current state of each tenet, tracks decay, and provides
    vector representations for utility calculations.
    """
    
    def __init__(self):
        self.tenets: Dict[CoreTenet, TenetVector] = {}
        self._initialize_default_tenets()
        self.decay_history: deque = deque(maxlen=1000)
        
    def _initialize_default_tenets(self) -> None:
        """Initialize default tenet vectors based on Karthi's goals"""
        # Core tenets with weights and targets
        self.tenets = {
            CoreTenet.PROTECT_WORK_LIMIT: TenetVector(
                tenet=CoreTenet.PROTECT_WORK_LIMIT,
                weight=0.9,  # High importance
                current_value=0.8,  # Currently doing well
                target_value=0.95,  # Target: excellent work limit adherence
                decay_rate=0.05  # Decays without monitoring
            ),
            CoreTenet.GROW_BUSINESS: TenetVector(
                tenet=CoreTenet.GROW_BUSINESS,
                weight=0.8,  # High importance
                current_value=0.6,  # Room for improvement
                target_value=0.9,  # Target: thriving business
                decay_rate=0.03  # Moderate decay
            ),
            CoreTenet.SHIP_UNITY_GAME: TenetVector(
                tenet=CoreTenet.SHIP_UNITY_GAME,
                weight=0.7,  # Important but not critical
                current_value=0.4,  # In progress
                target_value=1.0,  # Target: shipped
                decay_rate=0.02  # Slow decay
            ),
            CoreTenet.MAINTAIN_SANITY: TenetVector(
                tenet=CoreTenet.MAINTAIN_SANITY,
                weight=0.95,  # Critical importance
                current_value=0.7,  # Good but could be better
                target_value=0.9,  # Target: excellent mental health
                decay_rate=0.1  # Fast decay without attention
            ),
            CoreTenet.FINANCIAL_HEALTH: TenetVector(
                tenet=CoreTenet.FINANCIAL_HEALTH,
                weight=0.85,  # High importance
                current_value=0.75,  # Good financial state
                target_value=0.9,  # Target: excellent financial health
                decay_rate=0.04  # Moderate decay
            ),
            CoreTenet.RELATIONSHIP_MAINTENANCE: TenetVector(
                tenet=CoreTenet.RELATIONSHIP_MAINTENANCE,
                weight=0.6,  # Moderate importance
                current_value=0.5,  # Average
                target_value=0.8,  # Target: good relationships
                decay_rate=0.06  # Moderate decay
            ),
            CoreTenet.SKILL_DEVELOPMENT: TenetVector(
                tenet=CoreTenet.SKILL_DEVELOPMENT,
                weight=0.7,  # Important
                current_value=0.65,  # Learning steadily
                target_value=0.85,  # Target: strong skill base
                decay_rate=0.02  # Slow decay
            ),
            CoreTenet.PHYSICAL_HEALTH: TenetVector(
                tenet=CoreTenet.PHYSICAL_HEALTH,
                weight=0.9,  # Critical importance
                current_value=0.7,  # Good but could improve
                target_value=0.9,  # Target: excellent health
                decay_rate=0.08  # Fast decay
            )
        }
        
        logger.info("Initialized Karthi's Core Tenets")
    
    def get_tenet_vector(self, tenet: CoreTenet) -> Optional[TenetVector]:
        """Get vector for a specific tenet"""
        return self.tenets.get(tenet)
    
    def update_tenet_value(self, tenet: CoreTenet, new_value: float) -> None:
        """Update current value of a tenet"""
        if tenet in self.tenets:
            self.tenets[tenet].current_value = max(0.0, min(1.0, new_value))
            self.tenets[tenet].last_updated = datetime.now()
            logger.debug(f"Updated {tenet.value} to {new_value:.2f}")
    
    def apply_decay(self) -> None:
        """Apply decay to all tenets based on time since last update"""
        now = datetime.now()
        
        for tenet, vector in self.tenets.items():
            time_since_update = (now - vector.last_updated).total_seconds()
            decay_amount = vector.decay_rate * (time_since_update / 3600.0)  # Decay per hour
            
            vector.current_value = max(0.0, vector.current_value - decay_amount)
            vector.last_updated = now
            
            if decay_amount > 0.01:  # Only log significant decay
                logger.debug(f"Applied decay to {tenet.value}: {decay_amount:.3f}")
        
        self.decay_history.append({
            "timestamp": now.isoformat(),
            "tenet_values": {k.value: v.current_value for k, v in self.tenets.items()}
        })
    
    def get_tenet_state(self) -> Dict[str, float]:
        """Get current state of all tenets"""
        return {tenet.value: vector.current_value for tenet, vector in self.tenets.items()}
    
    def get_critical_tenets(self) -> List[CoreTenet]:
        """Get tenets that need attention (below target value)"""
        critical = []
        for tenet, vector in self.tenets.items():
            if vector.current_value < vector.target_value * 0.8:  # Below 80% of target
                critical.append(tenet)
        return critical


class UserStateDetector:
    """
    Detects the user's current state to inform utility calculations.
    
    Analyzes user activity, time of day, work patterns, and other signals
    to determine if the user is in high-flow, low-energy, stressed, etc.
    """
    
    def __init__(self):
        self.state_history: deque = deque(maxlen=500)
        self.state_transitions: deque = deque(maxlen=100)
        
    def detect_user_state(self, context: Dict[str, Any]) -> UserState:
        """Detect user's current state from context"""
        # Extract relevant signals
        current_time = datetime.now().time()
        work_hours = context.get("work_hours", 8)
        current_activity = context.get("current_activity", "unknown")
        focus_depth = context.get("focus_depth", 0.5)
        stress_level = context.get("stress_level", 0.3)
        energy_level = context.get("energy_level", 0.7)
        
        # Determine state based on signals
        if stress_level > 0.7:
            return UserState.STRESSED
        elif energy_level < 0.3:
            return UserState.LOW_ENERGY
        elif focus_depth > 0.8 and current_activity in ["coding", "writing", "design"]:
            return UserState.HIGH_FLOW
        elif focus_depth > 0.6:
            return UserState.FOCUSED
        elif focus_depth < 0.3:
            return UserState.DISTRACTED
        elif work_hours >= 9:
            return UserState.OFF_DUTY
        elif stress_level < 0.3 and energy_level > 0.7:
            return UserState.RELAXED
        else:
            return UserState.FOCUSED  # Default to focused
    
    def get_interruption_friction(self, user_state: UserState) -> float:
        """Calculate interruption friction based on user state"""
        friction_scores = {
            UserState.HIGH_FLOW: 0.9,  # Very high friction during deep work
            UserState.LOW_ENERGY: 0.3,  # Low friction when tired
            UserState.FOCUSED: 0.7,  # High friction when focused
            UserState.DISTRACTED: 0.2,  # Low friction when distracted
            UserState.STRESSED: 0.8,  # High friction when stressed
            UserState.RELAXED: 0.4,  # Moderate friction when relaxed
            UserState.OFF_DUTY: 0.1,  # Very low friction when off duty
        }
        
        return friction_scores.get(user_state, 0.5)


class UtilityCalculator:
    """
    Calculates utility scores for proposed actions.
    
    Uses Karthi's Core Tenets as vectors to evaluate whether an action
    provides real-world value proportional to its cost.
    """
    
    def __init__(self, tenet_manager: TenetManager):
        self.tenet_manager = tenet_manager
        self.utility_threshold = 1.0  # Default threshold
        self.calculation_history: deque = deque(maxlen=1000)
        
    def calculate_utility(
        self, 
        action: ActionProposal, 
        user_state: UserState
    ) -> UtilityEvaluation:
        """
        Calculate utility score for an action.
        
        Formula: Utility = Predicted Outcome Value / (Compute Cost + Interruption Friction)
        """
        # Calculate predicted outcome value based on tenet alignment
        predicted_value = self._calculate_predicted_value(action, user_state)
        
        # Calculate total cost
        total_cost = action.compute_cost + action.interruption_friction
        
        # Calculate utility score
        if total_cost > 0:
            utility_score = predicted_value / total_cost
        else:
            utility_score = 0.0
        
        # Determine approval
        approved = utility_score >= self.utility_threshold
        
        # Generate rejection reason if not approved
        rejection_reason = None
        if not approved:
            rejection_reason = self._generate_rejection_reason(action, user_state, utility_score, total_cost)
        
        # Get tenet contributions
        tenet_contributions = self._calculate_tenet_contributions(action)
        
        evaluation_id = hashlib.md5(
            f"{action.action_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        evaluation = UtilityEvaluation(
            evaluation_id=evaluation_id,
            action_id=action.action_id,
            utility_score=utility_score,
            predicted_value=predicted_value,
            total_cost=total_cost,
            threshold=self.utility_threshold,
            approved=approved,
            rejection_reason=rejection_reason,
            tenet_contributions=tenet_contributions,
            user_state=user_state
        )
        
        self.calculation_history.append(evaluation)
        
        if approved:
            logger.info(f"Action approved: {action.description} (utility: {utility_score:.2f})")
        else:
            logger.warning(f"Action aborted: {action.description} (utility: {utility_score:.2f} < {self.utility_threshold:.2f})")
            logger.warning(f"Rejection reason: {rejection_reason}")
        
        return evaluation
    
    def _calculate_predicted_value(self, action: ActionProposal, user_state: UserState) -> float:
        """Calculate predicted outcome value based on tenet alignment"""
        total_value = 0.0
        
        for tenet, alignment in action.tenet_alignment.items():
            tenet_vector = self.tenet_manager.get_tenet_vector(tenet)
            if tenet_vector:
                # Value = tenet weight × alignment × (1 - current_value / target_value)
                # Higher value when tenet needs more attention
                need_attention = 1.0 - (tenet_vector.current_value / tenet_vector.target_value)
                tenet_value = tenet_vector.weight * alignment * need_attention
                total_value += tenet_value
        
        # Adjust based on user state
        state_multipliers = {
            UserState.HIGH_FLOW: 0.5,  # Reduce value during deep work
            UserState.LOW_ENERGY: 0.7,  # Slightly reduce when tired
            UserState.FOCUSED: 0.8,  # Moderate reduction when focused
            UserState.DISTRACTED: 1.2,  # Increase value when distracted
            UserState.STRESSED: 0.6,  # Reduce value when stressed
            UserState.RELAXED: 1.1,  # Slightly increase when relaxed
            UserState.OFF_DUTY: 1.5  # Increase value when off duty
        }
        
        multiplier = state_multipliers.get(user_state, 1.0)
        total_value *= multiplier
        
        return min(total_value, 2.0)  # Cap at 2.0
    
    def _calculate_tenet_contributions(self, action: ActionProposal) -> Dict[CoreTenet, float]:
        """Calculate how each tenet contributed to the utility score"""
        contributions = {}
        
        for tenet, alignment in action.tenet_alignment.items():
            tenet_vector = self.tenet_manager.get_tenet_vector(tenet)
            if tenet_vector:
                need_attention = 1.0 - (tenet_vector.current_value / tenet_vector.target_value)
                contribution = tenet_vector.weight * alignment * need_attention
                contributions[tenet] = contribution
        
        return contributions
    
    def _generate_rejection_reason(
        self, 
        action: ActionProposal, 
        user_state: UserState,
        utility_score: float,
        total_cost: float
    ) -> str:
        """Generate human-readable rejection reason"""
        reasons = []
        
        # Check user state
        if user_state == UserState.HIGH_FLOW:
            reasons.append(f"user in high-flow state on {action.task_category.value}")
        elif user_state == UserState.STRESSED:
            reasons.append("user is stressed, intervention would be disruptive")
        elif user_state == UserState.OFF_DUTY:
            reasons.append("user is off duty, personal time takes priority")
        
        # Check cost
        if action.compute_cost > 0.7:
            reasons.append(f"high compute cost ({action.compute_cost:.2f})")
        if action.interruption_friction > 0.6:
            reasons.append(f"high interruption friction ({action.interruption_friction:.2f})")
        
        # Check tenet alignment
        critical_tenets = self.tenet_manager.get_critical_tenets()
        aligned_critical = [t for t in critical_tenets if action.tenet_alignment.get(t, 0) > 0.5]
        
        if not aligned_critical:
            reasons.append("action doesn't align with critical tenets")
        
        # Combine reasons
        if reasons:
            return "; ".join(reasons)
        else:
            return f"utility score {utility_score:.2f} below threshold {self.utility_threshold:.2f}"
    
    def set_threshold(self, threshold: float) -> None:
        """Set the utility threshold"""
        self.utility_threshold = max(0.1, min(2.0, threshold))
        logger.info(f"Utility threshold set to {self.utility_threshold:.2f}")


class AxiologicalEngine:
    """
    Main engine coordinating utility-based action evaluation.
    
    Implements the "Is It Useful?" arbiter that evaluates whether
    proposed actions provide real-world value proportional to their cost.
    """
    
    def __init__(self, utility_threshold: float = 1.0):
        self.tenet_manager = TenetManager()
        self.user_state_detector = UserStateDetector()
        self.utility_calculator = UtilityCalculator(self.tenet_manager)
        self.utility_calculator.set_threshold(utility_threshold)
        
        self.evaluation_history: deque = deque(maxlen=2000)
        self.aborted_actions: deque = deque(maxlen=500)
        self.approved_actions: deque = deque(maxlen=500)
        
        self.running = False
        self.lock = threading.Lock()
        
    def evaluate_action(
        self, 
        task_category: TaskCategory,
        description: str,
        predicted_outcome: Dict[str, Any],
        compute_cost: float,
        estimated_duration: timedelta,
        context: Dict[str, Any]
    ) -> UtilityEvaluation:
        """
        Evaluate a proposed action for utility.
        
        Returns evaluation with approval/rejection decision.
        """
        # Detect user state
        user_state = self.user_state_detector.detect_user_state(context)
        
        # Calculate interruption friction
        interruption_friction = self.user_state_detector.get_interruption_friction(user_state)
        
        # Calculate tenet alignment (simplified for now)
        tenet_alignment = self._calculate_tenet_alignment(task_category, predicted_outcome, context)
        
        # Create action proposal
        action_id = hashlib.md5(
            f"{task_category.value}_{description}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        action = ActionProposal(
            action_id=action_id,
            task_category=task_category,
            description=description,
            predicted_outcome=predicted_outcome,
            compute_cost=compute_cost,
            interruption_friction=interruption_friction,
            estimated_duration=estimated_duration,
            tenet_alignment=tenet_alignment
        )
        
        # Calculate utility
        evaluation = self.utility_calculator.calculate_utility(action, user_state)
        
        # Store in appropriate history
        if evaluation.approved:
            self.approved_actions.append(evaluation)
        else:
            self.aborted_actions.append(evaluation)
        
        self.evaluation_history.append(evaluation)
        
        return evaluation
    
    def _calculate_tenet_alignment(
        self, 
        task_category: TaskCategory, 
        predicted_outcome: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[CoreTenet, float]:
        """Calculate alignment of action with each tenet"""
        alignment = {}
        
        # Default alignments based on task category
        category_alignments = {
            TaskCategory.MARKET_ANALYSIS: {
                CoreTenet.FINANCIAL_HEALTH: 0.8,
                CoreTenet.GROW_BUSINESS: 0.6,
                CoreTenet.PROTECT_WORK_LIMIT: 0.3
            },
            TaskCategory.CODE_GENERATION: {
                CoreTenet.SHIP_UNITY_GAME: 0.7,
                CoreTenet.SKILL_DEVELOPMENT: 0.6,
                CoreTenet.GROW_BUSINESS: 0.4
            },
            TaskCategory.DOCUMENTATION: {
                CoreTenet.SHIP_UNITY_GAME: 0.5,
                CoreTenet.SKILL_DEVELOPMENT: 0.4,
                CoreTenet.GROW_BUSINESS: 0.3
            },
            TaskCategory.RESEARCH: {
                CoreTenet.SKILL_DEVELOPMENT: 0.7,
                CoreTenet.GROW_BUSINESS: 0.5,
                CoreTenet.FINANCIAL_HEALTH: 0.3
            },
            TaskCategory.MONITORING: {
                CoreTenet.PROTECT_WORK_LIMIT: 0.6,
                CoreTenet.FINANCIAL_HEALTH: 0.5,
                CoreTenet.MAINTAIN_SANITY: 0.4
            },
            TaskCategory.OPTIMIZATION: {
                CoreTenet.PROTECT_WORK_LIMIT: 0.7,
                CoreTenet.SKILL_DEVELOPMENT: 0.5,
                CoreTenet.FINANCIAL_HEALTH: 0.3
            },
            TaskCategory.SYSTEM_MAINTENANCE: {
                CoreTenet.PROTECT_WORK_LIMIT: 0.5,
                CoreTenet.MAINTAIN_SANITY: 0.4,
                CoreTenet.FINANCIAL_HEALTH: 0.3
            }
        }
        
        base_alignment = category_alignments.get(task_category, {})
        
        # Adjust based on predicted outcome
        if "financial_gain" in predicted_outcome:
            alignment[CoreTenet.FINANCIAL_HEALTH] = base_alignment.get(CoreTenet.FINANCIAL_HEALTH, 0.5) + 0.3
        if "business_growth" in predicted_outcome:
            alignment[CoreTenet.GROW_BUSINESS] = base_alignment.get(CoreTenet.GROW_BUSINESS, 0.5) + 0.3
        if "stress_reduction" in predicted_outcome:
            alignment[CoreTenet.MAINTAIN_SANITY] = base_alignment.get(CoreTenet.MAINTAIN_SANITY, 0.5) + 0.3
        
        # Ensure all tenets have some alignment value
        for tenet in CoreTenet:
            if tenet not in alignment:
                alignment[tenet] = base_alignment.get(tenet, 0.1)
        
        return alignment
    
    def start_decay_cycle(self, interval_minutes: int = 60) -> None:
        """Start periodic tenet decay cycle"""
        self.running = True
        logger.info(f"Starting tenet decay cycle (interval: {interval_minutes} minutes)")
        
        def decay_loop():
            while self.running:
                try:
                    self.tenet_manager.apply_decay()
                    time.sleep(interval_minutes * 60)
                except Exception as e:
                    logger.error(f"Error in decay cycle: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=decay_loop, daemon=True)
        thread.start()
    
    def stop_decay_cycle(self) -> None:
        """Stop the decay cycle"""
        self.running = False
        logger.info("Stopped tenet decay cycle")
    
    def get_utility_summary(self) -> Dict[str, Any]:
        """Get summary of utility evaluations"""
        with self.lock:
            total_evaluations = len(self.evaluation_history)
            approved_count = len(self.approved_actions)
            aborted_count = len(self.aborted_actions)
            
            recent_evaluations = list(self.evaluation_history)[-20:]
            
            return {
                "total_evaluations": total_evaluations,
                "approved_count": approved_count,
                "aborted_count": aborted_count,
                "approval_rate": approved_count / total_evaluations if total_evaluations > 0 else 0.0,
                "average_utility_score": np.mean([e.utility_score for e in recent_evaluations]) if recent_evaluations else 0.0,
                "current_tenet_state": self.tenet_manager.get_tenet_state(),
                "critical_tenets": [t.value for t in self.tenet_manager.get_critical_tenets()],
                "recent_evaluations": [e.to_dict() for e in recent_evaluations]
            }
    
    def manually_update_tenet(self, tenet: CoreTenet, new_value: float) -> bool:
        """Manually update a tenet's current value"""
        try:
            self.tenet_manager.update_tenet_value(tenet, new_value)
            logger.info(f"Manually updated {tenet.value} to {new_value:.2f}")
            return True
        except Exception as e:
            logger.error(f"Error updating tenet: {e}")
            return False


# Singleton instance
_axiological_engine_instance: Optional[AxiologicalEngine] = None
_engine_lock = threading.Lock()

def get_axiological_engine(utility_threshold: float = 1.0) -> AxiologicalEngine:
    """Get the singleton Axiological Engine instance"""
    global _axiological_engine_instance
    with _engine_lock:
        if _axiological_engine_instance is None:
            _axiological_engine_instance = AxiologicalEngine(utility_threshold)
            _axiological_engine_instance.start_decay_cycle()
        return _axiological_engine_instance


if __name__ == "__main__":
    # Test the Axiological Engine
    print("Testing Axiological Engine...")
    
    engine = get_axiological_engine()
    
    # Test action evaluation during high-flow state
    evaluation = engine.evaluate_action(
        task_category=TaskCategory.MARKET_ANALYSIS,
        description="Analyze 50 crypto charts for trading opportunities",
        predicted_outcome={
            "financial_gain": 0.3,
            "business_growth": 0.1
        },
        compute_cost=0.8,  # High compute cost
        estimated_duration=timedelta(minutes=30),
        context={
            "current_activity": "coding",
            "focus_depth": 0.9,
            "stress_level": 0.2,
            "energy_level": 0.8,
            "work_hours": 6
        }
    )
    
    print(f"\nEvaluation Result:")
    print(f"Action: {evaluation.action_id}")
    print(f"Approved: {evaluation.approved}")
    print(f"Utility Score: {evaluation.utility_score:.2f}")
    print(f"Threshold: {evaluation.threshold:.2f}")
    print(f"User State: {evaluation.user_state.value}")
    if evaluation.rejection_reason:
        print(f"Rejection Reason: {evaluation.rejection_reason}")
    
    # Test action evaluation during off-duty state
    evaluation2 = engine.evaluate_action(
        task_category=TaskCategory.CODE_GENERATION,
        description="Generate 100 lines of Flutter boilerplate",
        predicted_outcome={
            "business_growth": 0.4,
            "skill_development": 0.2
        },
        compute_cost=0.6,
        estimated_duration=timedelta(minutes=15),
        context={
            "current_activity": "gaming",
            "focus_depth": 0.2,
            "stress_level": 0.1,
            "energy_level": 0.9,
            "work_hours": 9
        }
    )
    
    print(f"\nSecond Evaluation Result:")
    print(f"Action: {evaluation2.action_id}")
    print(f"Approved: {evaluation2.approved}")
    print(f"Utility Score: {evaluation2.utility_score:.2f}")
    print(f"User State: {evaluation2.user_state.value}")
    if evaluation2.rejection_reason:
        print(f"Rejection Reason: {evaluation2.rejection_reason}")
    
    # Get utility summary
    summary = engine.get_utility_summary()
    print(f"\nUtility Summary: {summary}")
    
    # Stop engine
    engine.stop_decay_cycle()
    
    print("\nAxiological Engine test completed successfully!")