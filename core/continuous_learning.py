"""
Continuous Learning System for LOVE
Learns from all experiences over time and integrates knowledge across systems.
This is the final piece - enabling LOVE to continuously improve and adapt.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque

from core.settings import get_settings
from core.context_engine import get_live_context
from core.self_improvement import get_self_improvement_engine, DecisionType, OutcomeType
from core.psychological_model import get_psychological_model
from core.world_model import get_world_model
from core.meta_cognition import get_meta_cognition_engine, ThoughtType

SETTINGS = get_settings()


class LearningSourceType(Enum):
    """Sources of learning experiences"""
    DECISION_OUTCOME = "decision_outcome"
    USER_FEEDBACK = "user_feedback"
    PREDICTION_RESULT = "prediction_result"
    CONVERSATION = "conversation"
    ACTION_EXECUTION = "action_execution"
    PATTERN_OBSERVATION = "pattern_observation"
    SYSTEM_ERROR = "system_error"
    SUCCESS = "success"


class LearningType(Enum):
    """Types of learnings"""
    PATTERN = "pattern"  # Recognized patterns
    RULE = "rule"  # conditional rules
    PREFERENCE = "preference"  # User preferences
    CAPABILITY = "capability"  # What LOVE can/cannot do
    CONTEXT = "context"  # Contextual knowledge
    STRATEGY = "strategy"  # Effective strategies
    AVOIDANCE = "avoidance"  # What to avoid


@dataclass
class LearningExperience:
    """A learning experience"""
    id: str
    source_type: LearningSourceType
    learning_type: LearningType
    description: str
    context: Dict[str, Any]
    outcome: str  # What happened
    lesson: str  # What was learned
    confidence: float  # 0-1
    application_count: int = 0  # How many times this learning has been applied
    success_rate: float = 1.0  # Success rate when applied
    last_applied: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None


@dataclass
class LearningPattern:
    """A pattern that LOVE has learned"""
    id: str
    pattern: str  # The pattern itself
    conditions: List[str]  # When this pattern applies
    consequences: List[str]  # What typically happens
    frequency: int = 1  # How often this pattern occurs
    confidence: float = 0.3  # Starts low, increases with repetition
    last_observed: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Adaptation:
    """An adaptation LOVE has made based on learning"""
    id: str
    description: str
    reason: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    effectiveness: float  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ContinuousLearningEngine:
    """
    Continuous learning engine that integrates learnings from all systems.
    This enables LOVE to continuously improve and adapt.
    """
    
    def __init__(self):
        self.experiences: Dict[str, LearningExperience] = {}
        self.patterns: List[LearningPattern] = []
        self.adaptations: List[Adaptation] = []
        self.learning_stats: Dict[str, Any] = defaultdict(int)
        self.lock = threading.Lock()
        self._load_data()
        self.improvement_engine = get_self_improvement_engine()
        self.psych_model = get_psychological_model()
        self.world_model = get_world_model()
        self.meta_cognition = get_meta_cognition_engine()
        
        # Neural bus integration
        self._bus = None
        self._neural_bus_available = False
        self._init_neural_bus()
    
    def _init_neural_bus(self):
        """Initialize neural bus connection for learning events."""
        try:
            from core.neural_bus import get_neural_bus, EventPriority, EventDomain
            self._bus = get_neural_bus()
            self._neural_bus_available = True
        except Exception as e:
            print(f"[ContinuousLearning] Neural bus unavailable: {e}")
            self._neural_bus_available = False
    
    def _publish_learning_event(self, event_type: str, payload: dict, priority: str = "NORMAL"):
        """Publish learning events to neural bus."""
        if not self._neural_bus_available or not self._bus:
            return
        
        try:
            from core.neural_bus import EventPriority, EventDomain
            priority_map = {
                "CRITICAL": EventPriority.CRITICAL,
                "HIGH": EventPriority.HIGH,
                "NORMAL": EventPriority.NORMAL,
                "LOW": EventPriority.LOW,
            }
            
            self._bus.publish(
                domain=EventDomain.LEARNING,
                event_type=event_type,
                payload=payload,
                priority=priority_map.get(priority, EventPriority.NORMAL)
            )
        except Exception as e:
            print(f"[ContinuousLearning] Failed to publish event: {e}")
    
    def _load_data(self):
        """Load learning data from storage"""
        try:
            learning_file = SETTINGS.data_dir / "continuous_learning.json"
            if learning_file.exists():
                with open(learning_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load experiences
                    for exp_id, exp_data in data.get("experiences", {}).items():
                        self.experiences[exp_id] = LearningExperience(
                            id=exp_id,
                            source_type=LearningSourceType(exp_data["source_type"]),
                            learning_type=LearningType(exp_data["learning_type"]),
                            description=exp_data["description"],
                            context=exp_data["context"],
                            outcome=exp_data["outcome"],
                            lesson=exp_data["lesson"],
                            confidence=exp_data["confidence"],
                            application_count=exp_data.get("application_count", 0),
                            success_rate=exp_data.get("success_rate", 1.0),
                            last_applied=exp_data.get("last_applied"),
                            created_at=exp_data["created_at"],
                            expires_at=exp_data.get("expires_at")
                        )
                    
                    # Load patterns
                    for pattern_data in data.get("patterns", []):
                        self.patterns.append(LearningPattern(
                            id=pattern_data["id"],
                            pattern=pattern_data["pattern"],
                            conditions=pattern_data.get("conditions", []),
                            consequences=pattern_data.get("consequences", []),
                            frequency=pattern_data.get("frequency", 1),
                            confidence=pattern_data.get("confidence", 0.3),
                            last_observed=pattern_data.get("last_observed")
                        ))
                    
                    # Load adaptations
                    for adapt_data in data.get("adaptations", []):
                        self.adaptations.append(Adaptation(
                            id=adapt_data["id"],
                            description=adapt_data["description"],
                            reason=adapt_data["reason"],
                            before_state=adapt_data["before_state"],
                            after_state=adapt_data["after_state"],
                            effectiveness=adapt_data["effectiveness"],
                            timestamp=adapt_data["timestamp"]
                        ))
                    
                    # Load stats
                    self.learning_stats = defaultdict(int, data.get("learning_stats", {}))
                    
        except Exception as e:
            print(f"[ContinuousLearning] Error loading data: {e}")
    
    def _save_data(self):
        """Save learning data to storage"""
        try:
            learning_file = SETTINGS.data_dir / "continuous_learning.json"
            with self.lock:
                data = {
                    "experiences": {
                        exp_id: {
                            "source_type": exp.source_type.value,
                            "learning_type": exp.learning_type.value,
                            "description": exp.description,
                            "context": exp.context,
                            "outcome": exp.outcome,
                            "lesson": exp.lesson,
                            "confidence": exp.confidence,
                            "application_count": exp.application_count,
                            "success_rate": exp.success_rate,
                            "last_applied": exp.last_applied,
                            "created_at": exp.created_at,
                            "expires_at": exp.expires_at
                        }
                        for exp_id, exp in self.experiences.items()
                    },
                    "patterns": [
                        {
                            "id": p.id,
                            "pattern": p.pattern,
                            "conditions": p.conditions,
                            "consequences": p.consequences,
                            "frequency": p.frequency,
                            "confidence": p.confidence,
                            "last_observed": p.last_observed
                        }
                        for p in self.patterns
                    ],
                    "adaptations": [
                        {
                            "id": a.id,
                            "description": a.description,
                            "reason": a.reason,
                            "before_state": a.before_state,
                            "after_state": a.after_state,
                            "effectiveness": a.effectiveness,
                            "timestamp": a.timestamp
                        }
                        for a in self.adaptations
                    ],
                    "learning_stats": dict(self.learning_stats)
                }
                with open(learning_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ContinuousLearning] Error saving data: {e}")
    
    def record_experience(self, source_type: LearningSourceType, learning_type: LearningType,
                         description: str, context: Dict[str, Any], outcome: str,
                         lesson: str, confidence: float = 0.5) -> str:
        """
        Record a learning experience.
        This is the primary way LOVE learns.
        """
        exp_id = f"exp_{datetime.utcnow().timestamp()}"
        experience = LearningExperience(
            id=exp_id,
            source_type=source_type,
            learning_type=learning_type,
            description=description,
            context=context,
            outcome=outcome,
            lesson=lesson,
            confidence=confidence
        )
        
        with self.lock:
            self.experiences[exp_id] = experience
            self.learning_stats["total_experiences"] += 1
            self.learning_stats[f"source_{source_type.value}"] += 1
            self.learning_stats[f"type_{learning_type.value}"] += 1
            self._save_data()
        
        # Integrate with other systems
        self._integrate_experience(experience)
        
        # Publish to neural bus
        self._publish_learning_event("experience_recorded", {
            "experience_id": exp_id,
            "source_type": source_type.value,
            "learning_type": learning_type.value,
            "description": description,
            "lesson": lesson,
            "confidence": confidence,
            "total_experiences": self.learning_stats["total_experiences"]
        }, priority="NORMAL")
        
        print(f"[ContinuousLearning] Recorded experience: {description}")
        return exp_id
    
    def _integrate_experience(self, experience: LearningExperience):
        """Integrate a learning experience with other LOVE systems"""
        # Update psychological model if relevant
        if experience.learning_type == LearningType.PREFERENCE:
            # This would update user preferences in psych model
            pass
        
        # Update world model if relevant
        if experience.learning_type == LearningType.CONTEXT:
            subject = experience.context.get("subject", "unknown")
            predicate = experience.context.get("predicate", "unknown")
            self.world_model.learn_from_interaction(
                subject, predicate, 
                confidence=experience.confidence,
                source="continuous_learning"
            )
        
        # Record meta-cognitive thought
        self.meta_cognition.record_thought(
            ThoughtType.REFLECTION,
            f"Learned: {experience.lesson}",
            confidence=experience.confidence
        )
        
        # Check if this reinforces a pattern
        self._check_pattern_reinforcement(experience)
    
    def _check_pattern_reinforcement(self, experience: LearningExperience):
        """Check if this experience reinforces an existing pattern"""
        for pattern in self.patterns:
            # Check if conditions match
            if all(str(cond).lower() in str(experience.context).lower() 
                   for cond in pattern.conditions):
                # Reinforce pattern
                pattern.frequency += 1
                pattern.confidence = min(1.0, pattern.confidence + 0.1)
                pattern.last_observed = datetime.utcnow().isoformat()
                self._save_data()
                return
        
        # Check if this should create a new pattern
        if experience.learning_type in [LearningType.PATTERN, LearningType.STRATEGY]:
            self._create_pattern_from_experience(experience)
    
    def _create_pattern_from_experience(self, experience: LearningExperience):
        """Create a new pattern from an experience"""
        pattern_id = f"pattern_{datetime.utcnow().timestamp()}"
        
        # Extract conditions from context
        conditions = []
        for key, value in experience.context.items():
            if value is not None:
                conditions.append(f"{key}={value}")
        
        pattern = LearningPattern(
            id=pattern_id,
            pattern=experience.lesson,
            conditions=conditions,
            consequences=[experience.outcome],
            frequency=1,
            confidence=0.3
        )
        
        self.patterns.append(pattern)
        self._save_data()
        
        # Publish to neural bus
        self._publish_learning_event("pattern_discovered", {
            "pattern_id": pattern_id,
            "pattern": pattern.pattern,
            "conditions": pattern.conditions,
            "confidence": pattern.confidence,
            "total_patterns": len(self.patterns)
        }, priority="HIGH")
    
    def apply_learning(self, experience_id: str, context: Dict[str, Any]) -> bool:
        """
        Apply a learning to a new situation.
        This is how LOVE uses what it has learned.
        """
        if experience_id not in self.experiences:
            return False
        
        experience = self.experiences[experience_id]
        
        # Check if learning applies to this context
        if not self._learning_applies(experience, context):
            return False
        
        # Apply the learning
        experience.application_count += 1
        experience.last_applied = datetime.utcnow().isoformat()
        
        # Update success rate (simplified - would need actual outcome tracking)
        # For now, assume success to encourage application
        experience.success_rate = (experience.success_rate * experience.application_count + 1.0) / (experience.application_count + 1)
        
        self._save_data()
        
        print(f"[ContinuousLearning] Applied learning: {experience.lesson}")
        return True
    
    def _learning_applies(self, experience: LearningExperience, context: Dict[str, Any]) -> bool:
        """Check if a learning applies to the given context"""
        # Simple matching - can be improved with semantic similarity
        for key, value in experience.context.items():
            if key in context:
                if context[key] != value:
                    # Context mismatch
                    return False
        return True
    
    def learn_from_decision(self, decision_id: str, outcome_type: OutcomeType, 
                          outcome_description: str, success: bool):
        """
        Learn from a decision outcome.
        Integrates with the self-improvement engine.
        """
        try:
            # Get decision details from improvement engine
            # This would need to be implemented in the improvement engine
            # For now, create a learning experience directly
            
            lesson = f"Decision led to {outcome_type.value}. " + \
                     ("Strategy worked" if success else "Strategy needs adjustment")
            
            self.record_experience(
                source_type=LearningSourceType.DECISION_OUTCOME,
                learning_type=LearningType.STRATEGY if success else LearningType.AVOIDANCE,
                description=f"Decision outcome: {outcome_description}",
                context={"decision_id": decision_id},
                outcome=outcome_description,
                lesson=lesson,
                confidence=0.7 if success else 0.5
            )
            
        except Exception as e:
            print(f"[ContinuousLearning] Error learning from decision: {e}")
    
    def learn_from_prediction(self, prediction_id: str, actual_outcome: str, 
                           success: bool):
        """
        Learn from a prediction result.
        Integrates with the predictive engine.
        """
        lesson = f"Prediction was {'correct' if success else 'incorrect'}. " + \
                 f"Expected something different: {actual_outcome}"
        
        self.record_experience(
            source_type=LearningSourceType.PREDICTION_RESULT,
            learning_type=LearningType.PATTERN if success else LearningType.AVOIDANCE,
            description=f"Prediction result for {prediction_id}",
            context={"prediction_id": prediction_id},
            outcome=actual_outcome,
            lesson=lesson,
            confidence=0.6
        )
    
    def learn_from_feedback(self, feedback: str, context: Dict[str, Any]):
        """
        Learn from user feedback.
        This is a high-value learning source.
        """
        try:
            # Use LLM to extract learnings from feedback
            from core.agent import chat
            
            prompt = f"""You are LOVE, learning from user feedback.

USER FEEDBACK:
{feedback}

CONTEXT:
{json.dumps(context, indent=2)}

Extract what LOVE should learn from this feedback. Return JSON:
{{
  "learnings": [
    {{
      "type": "preference|pattern|capability|strategy|avoidance",
      "lesson": "what was learned",
      "confidence": 0.8
    }}
  ]
}}"""
            
            response = chat(prompt, mode="reasoning")
            response_text = response.get("response", "")
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                learning_data = json.loads(json_match.group())
                
                for learning in learning_data.get("learnings", []):
                    self.record_experience(
                        source_type=LearningSourceType.USER_FEEDBACK,
                        learning_type=LearningType(learning["type"]),
                        description=f"Learned from feedback",
                        context=context,
                        outcome="feedback received",
                        lesson=learning["lesson"],
                        confidence=learning["confidence"]
                    )
            
        except Exception as e:
            print(f"[ContinuousLearning] Error learning from feedback: {e}")
    
    def get_relevant_learnings(self, context: Dict[str, Any], 
                              learning_type: LearningType = None) -> List[LearningExperience]:
        """
        Get learnings relevant to the current context.
        This enables LOVE to apply past learnings to current situations.
        """
        relevant = []
        
        for exp in self.experiences.values():
            # Filter by learning type if specified
            if learning_type and exp.learning_type != learning_type:
                continue
            
            # Check if learning applies to context
            if self._learning_applies(exp, context):
                relevant.append(exp)
        
        # Sort by confidence and application count
        relevant.sort(key=lambda e: (e.confidence, e.application_count), reverse=True)
        
        return relevant
    
    def adapt(self, reason: str, before_state: Dict[str, Any], 
             after_state: Dict[str, Any]) -> str:
        """
        Record an adaptation LOVE has made based on learning.
        """
        adaptation_id = f"adapt_{datetime.utcnow().timestamp()}"
        
        # Calculate effectiveness (simplified)
        effectiveness = 0.5  # Would need actual measurement
        
        adaptation = Adaptation(
            id=adaptation_id,
            description=f"Adaptation: {reason}",
            reason=reason,
            before_state=before_state,
            after_state=after_state,
            effectiveness=effectiveness
        )
        
        self.adaptations.append(adaptation)
        self._save_data()
        
        # Publish to neural bus
        self._publish_learning_event("adaptation_made", {
            "adaptation_id": adaptation_id,
            "description": adaptation.description,
            "reason": reason,
            "effectiveness": effectiveness,
            "total_adaptations": len(self.adaptations)
        }, priority="HIGH")
        
        return adaptation_id
    
    def get_learning_summary(self) -> Dict:
        """Get a summary of LOVE's learning"""
        by_type = defaultdict(int)
        for exp in self.experiences.values():
            by_type[exp.learning_type.value] += 1
        
        by_source = defaultdict(int)
        for exp in self.experiences.values():
            by_source[exp.source_type.value] += 1
        
        return {
            "total_experiences": len(self.experiences),
            "total_patterns": len(self.patterns),
            "total_adaptations": len(self.adaptations),
            "experiences_by_type": dict(by_type),
            "experiences_by_source": dict(by_source),
            "learning_stats": dict(self.learning_stats),
            "most_applied_learnings": sorted(
                self.experiences.values(),
                key=lambda e: e.application_count,
                reverse=True
            )[:5],
            "highest_confidence_patterns": sorted(
                self.patterns,
                key=lambda p: p.confidence,
                reverse=True
            )[:5]
        }
    
    def consolidate_learnings(self):
        """
        Consolidate similar learnings to reduce redundancy.
        This keeps the knowledge base efficient.
        """
        try:
            # Group similar learnings
            by_lesson = defaultdict(list)
            for exp_id, exp in self.experiences.items():
                by_lesson[exp.lesson].append(exp)
            
            # For groups with multiple entries, consolidate
            for lesson, experiences in by_lesson.items():
                if len(experiences) > 1:
                    # Keep the one with highest confidence
                    best = max(experiences, key=lambda e: e.confidence)
                    
                    # Remove others
                    for exp in experiences:
                        if exp.id != best.id:
                            del self.experiences[exp.id]
                    
                    # Update the kept one
                    best.confidence = min(1.0, best.confidence + 0.1)
            
            self._save_data()
            
            print(f"[ContinuousLearning] Consolidated {len(by_lesson)} learning groups")
            
        except Exception as e:
            print(f"[ContinuousLearning] Error consolidating learnings: {e}")


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_continuous_learning_engine() -> ContinuousLearningEngine:
    """Get the singleton continuous learning engine instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = ContinuousLearningEngine()
    return _instance
