"""
Self-Improvement Loop for LOVE
Analyzes LOVE's own decisions, learns from outcomes, and improves over time.
This is a critical AGI capability - the ability to learn and improve autonomously.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict
import statistics

from core.settings import get_settings
from core.context_engine import get_live_context
from core.psychological_model import get_psychological_model

SETTINGS = get_settings()


class DecisionType(Enum):
    """Types of decisions LOVE makes"""
    GOAL_SETTING = "goal_setting"
    ACTION_PLANNING = "action_planning"
    PRIORITIZATION = "prioritization"
    COMMUNICATION = "communication"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_ASSESSMENT = "risk_assessment"
    PREDICTION = "prediction"


class OutcomeType(Enum):
    """Types of outcomes"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    UNKOWN = "unknown"


class ImprovementArea(Enum):
    """Areas where LOVE can improve"""
    PLANNING = "planning"
    PREDICTION_ACCURACY = "prediction_accuracy"
    PRIORITY_ALIGNMENT = "priority_alignment"
    TIMING = "timing"
    COMMUNICATION = "communication"
    RESOURCE_MANAGEMENT = "resource_management"
    CONTEXT_UNDERSTANDING = "context_understanding"


@dataclass
class Decision:
    """A decision made by LOVE"""
    id: str
    type: DecisionType
    description: str
    reasoning: str
    context_snapshot: Dict[str, Any]
    alternatives_considered: List[Dict[str, Any]]
    chosen_alternative: str
    confidence: float  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Outcome:
    """The result of a decision"""
    decision_id: str
    type: OutcomeType
    description: str
    metrics: Dict[str, float] = field(default_factory=dict)
    user_feedback: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ImprovementSuggestion:
    """A suggestion for how LOVE can improve"""
    area: ImprovementArea
    description: str
    rationale: str
    priority: float  # 0-10
    action_steps: List[str] = field(default_factory=list)
    estimated_impact: str = ""


@dataclass
class Learning:
    """A lesson LOVE has learned"""
    topic: str
    lesson: str
    confidence: float  # 0-1
    evidence_count: int = 1
    last_applied: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SelfImprovementEngine:
    """
    Self-improvement engine that analyzes LOVE's decisions and learns from outcomes.
    This enables LOVE to continuously improve its own intelligence.
    """
    
    def __init__(self):
        self.decisions: Dict[str, Decision] = {}
        self.outcomes: Dict[str, Outcome] = {}
        self.learnings: List[Learning] = []
        self.improvement_suggestions: List[ImprovementSuggestion] = []
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        self._load_data()
        self.psych_model = get_psychological_model()
    
    def _load_data(self):
        """Load self-improvement data from storage"""
        try:
            si_file = SETTINGS.data_dir / "self_improvement.json"
            if si_file.exists():
                with open(si_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load decisions
                    for dec_id, dec_data in data.get("decisions", {}).items():
                        self.decisions[dec_id] = Decision(
                            id=dec_id,
                            type=DecisionType(dec_data["type"]),
                            description=dec_data["description"],
                            reasoning=dec_data["reasoning"],
                            context_snapshot=dec_data["context_snapshot"],
                            alternatives_considered=dec_data.get("alternatives_considered", []),
                            chosen_alternative=dec_data["chosen_alternative"],
                            confidence=dec_data["confidence"],
                            timestamp=dec_data["timestamp"]
                        )
                    
                    # Load outcomes
                    for out_id, out_data in data.get("outcomes", {}).items():
                        self.outcomes[out_id] = Outcome(
                            decision_id=out_data["decision_id"],
                            type=OutcomeType(out_data["type"]),
                            description=out_data["description"],
                            metrics=out_data.get("metrics", {}),
                            user_feedback=out_data.get("user_feedback"),
                            timestamp=out_data["timestamp"]
                        )
                    
                    # Load learnings
                    for learn_data in data.get("learnings", []):
                        self.learnings.append(Learning(
                            topic=learn_data["topic"],
                            lesson=learn_data["lesson"],
                            confidence=learn_data["confidence"],
                            evidence_count=learn_data.get("evidence_count", 1),
                            last_applied=learn_data.get("last_applied"),
                            created_at=learn_data["created_at"]
                        ))
                    
                    # Load improvement suggestions
                    for imp_data in data.get("improvement_suggestions", []):
                        self.improvement_suggestions.append(ImprovementSuggestion(
                            area=ImprovementArea(imp_data["area"]),
                            description=imp_data["description"],
                            rationale=imp_data["rationale"],
                            priority=imp_data["priority"],
                            action_steps=imp_data.get("action_steps", []),
                            estimated_impact=imp_data.get("estimated_impact", "")
                        ))
                    
                    # Load performance metrics
                    self.performance_metrics = defaultdict(list)
                    for metric_name, values in data.get("performance_metrics", {}).items():
                        self.performance_metrics[metric_name] = values
                    
        except Exception as e:
            print(f"[SelfImprovementEngine] Error loading data: {e}")
    
    def _save_data(self):
        """Save self-improvement data to storage"""
        try:
            si_file = SETTINGS.data_dir / "self_improvement.json"
            with self.lock:
                data = {
                    "decisions": {
                        dec_id: {
                            "type": dec.type.value,
                            "description": dec.description,
                            "reasoning": dec.reasoning,
                            "context_snapshot": dec.context_snapshot,
                            "alternatives_considered": dec.alternatives_considered,
                            "chosen_alternative": dec.chosen_alternative,
                            "confidence": dec.confidence,
                            "timestamp": dec.timestamp
                        }
                        for dec_id, dec in self.decisions.items()
                    },
                    "outcomes": {
                        out_id: {
                            "decision_id": out.decision_id,
                            "type": out.type.value,
                            "description": out.description,
                            "metrics": out.metrics,
                            "user_feedback": out.user_feedback,
                            "timestamp": out.timestamp
                        }
                        for out_id, out in self.outcomes.items()
                    },
                    "learnings": [
                        {
                            "topic": l.topic,
                            "lesson": l.lesson,
                            "confidence": l.confidence,
                            "evidence_count": l.evidence_count,
                            "last_applied": l.last_applied,
                            "created_at": l.created_at
                        }
                        for l in self.learnings
                    ],
                    "improvement_suggestions": [
                        {
                            "area": imp.area.value,
                            "description": imp.description,
                            "rationale": imp.rationale,
                            "priority": imp.priority,
                            "action_steps": imp.action_steps,
                            "estimated_impact": imp.estimated_impact
                        }
                        for imp in self.improvement_suggestions
                    ],
                    "performance_metrics": dict(self.performance_metrics)
                }
                with open(si_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SelfImprovementEngine] Error saving data: {e}")
    
    def record_decision(self, decision_type: DecisionType, description: str, 
                       reasoning: str, alternatives: List[Dict[str, Any]], 
                       chosen: str, confidence: float = 0.5) -> str:
        """
        Record a decision made by LOVE.
        This is the first step in the self-improvement loop.
        """
        try:
            ctx = get_live_context()
            
            decision_id = f"decision_{datetime.utcnow().timestamp()}"
            decision = Decision(
                id=decision_id,
                type=decision_type,
                description=description,
                reasoning=reasoning,
                context_snapshot={
                    "stress_level": ctx.stress_level,
                    "energy_level": ctx.energy_level,
                    "time_of_day": ctx.time_of_day,
                    "tasks_due_today": ctx.tasks_due_today,
                    "active_project": ctx.active_project,
                    "next_event": ctx.next_event
                },
                alternatives_considered=alternatives,
                chosen_alternative=chosen,
                confidence=confidence
            )
            
            with self.lock:
                self.decisions[decision_id] = decision
                self._save_data()
            
            print(f"[SelfImprovementEngine] Recorded decision: {description}")
            return decision_id
            
        except Exception as e:
            print(f"[SelfImprovementEngine] Error recording decision: {e}")
            return ""
    
    def record_outcome(self, decision_id: str, outcome_type: OutcomeType, 
                      description: str, metrics: Dict[str, float] = None,
                      user_feedback: str = None):
        """
        Record the outcome of a decision.
        This enables LOVE to learn from its decisions.
        """
        try:
            if decision_id not in self.decisions:
                print(f"[SelfImprovementEngine] Decision {decision_id} not found")
                return
            
            outcome_id = f"outcome_{datetime.utcnow().timestamp()}"
            outcome = Outcome(
                decision_id=decision_id,
                type=outcome_type,
                description=description,
                metrics=metrics or {},
                user_feedback=user_feedback
            )
            
            with self.lock:
                self.outcomes[outcome_id] = outcome
                self._save_data()
            
            # Analyze outcome for learning
            self._analyze_outcome(decision_id, outcome_id)
            
            print(f"[SelfImprovementEngine] Recorded outcome: {description}")
            
        except Exception as e:
            print(f"[SelfImprovementEngine] Error recording outcome: {e}")
    
    def _analyze_outcome(self, decision_id: str, outcome_id: str):
        """
        Analyze an outcome to extract learnings and improvement suggestions.
        This is where LOVE learns from its experience.
        """
        try:
            decision = self.decisions[decision_id]
            outcome = self.outcomes[outcome_id]
            
            # If outcome was successful, reinforce the decision pattern
            if outcome.type == OutcomeType.SUCCESS:
                self._reinforce_learning(decision, outcome)
            
            # If outcome was failed, analyze what went wrong
            elif outcome.type == OutcomeType.FAILURE:
                self._analyze_failure(decision, outcome)
            
            # If user provided feedback, analyze it
            if outcome.user_feedback:
                self._analyze_feedback(decision, outcome.user_feedback)
            
            # Update performance metrics
            self._update_performance_metrics(decision, outcome)
            
            # Generate improvement suggestions if needed
            self._generate_improvement_suggestions()
            
        except Exception as e:
            print(f"[SelfImprovementEngine] Error analyzing outcome: {e}")
    
    def _reinforce_learning(self, decision: Decision, outcome: Outcome):
        """Reinforce learnings from successful decisions"""
        # Check if similar learning exists
        lesson_topic = f"{decision.type.value}_success_pattern"
        
        for learning in self.learnings:
            if learning.topic == lesson_topic:
                learning.evidence_count += 1
                learning.confidence = min(1.0, learning.confidence + 0.1)
                learning.last_applied = datetime.utcnow().isoformat()
                return
        
        # Create new learning
        new_learning = Learning(
            topic=lesson_topic,
            lesson=f"When context matches {decision.context_snapshot}, {decision.description} tends to succeed",
            confidence=0.3,
            evidence_count=1
        )
        self.learnings.append(new_learning)
    
    def _analyze_failure(self, decision: Decision, outcome: Outcome):
        """Analyze failures to understand what went wrong"""
        # Use LLM to analyze failure
        try:
            from core.agent import chat
            
            prompt = f"""You are LOVE, analyzing why a decision failed.

DECISION:
Type: {decision.type.value}
Description: {decision.description}
Reasoning: {decision.reasoning}
Chosen Alternative: {decision.chosen_alternative}
Alternatives Considered: {decision.alternatives_considered}
Context: {decision.context_snapshot}

OUTCOME:
Type: {outcome.type.value}
Description: {outcome.description}
Metrics: {outcome.metrics}

Analyze why this decision failed and provide insights in JSON:
{{
  "failure_reason": "why it failed",
  "what_should_have_been_done": "better alternative",
  "context_factors": "what context was missed",
  "improvement_area": "planning|prediction_accuracy|priority_alignment|timing|communication|resource_management|context_understanding"
}}"""
            
            response = chat(prompt, mode="reasoning")
            response_text = response.get("response", "")
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Create learning from failure
                learning = Learning(
                    topic=f"{decision.type.value}_failure_pattern",
                    lesson=f"Failure: {analysis['failure_reason']}. Better: {analysis['what_should_have_been_done']}",
                    confidence=0.5,
                    evidence_count=1
                )
                self.learnings.append(learning)
                
                # Create improvement suggestion
                try:
                    area = ImprovementArea(analysis["improvement_area"])
                    suggestion = ImprovementSuggestion(
                        area=area,
                        description=f"Improve {area.value} based on failure analysis",
                        rationale=analysis["failure_reason"],
                        priority=8.0,
                        action_steps=[
                            "Review decision-making process",
                            f"Consider: {analysis['what_should_have_been_done']}",
                            f"Pay attention to: {analysis['context_factors']}"
                        ],
                        estimated_impact="High - prevents similar failures"
                    )
                    self.improvement_suggestions.append(suggestion)
                except Exception:
                    pass
                
        except Exception as e:
            print(f"[SelfImprovementEngine] Error analyzing failure with LLM: {e}")
    
    def _analyze_feedback(self, decision: Decision, feedback: str):
        """Analyze user feedback to extract insights"""
        # Use LLM to analyze feedback
        try:
            from core.agent import chat
            
            prompt = f"""You are LOVE, analyzing user feedback on a decision.

DECISION:
Type: {decision.type.value}
Description: {decision.description}
Reasoning: {decision.reasoning}

USER FEEDBACK:
{feedback}

Analyze this feedback and provide insights in JSON:
{{
  "sentiment": "positive|negative|neutral",
  "key_points": ["point1", "point2"],
  "improvement_suggestion": "what should change",
  "what_worked": "what the user liked"
}}"""
            
            response = chat(prompt, mode="reasoning")
            response_text = response.get("response", "")
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Create learning from feedback
                learning = Learning(
                    topic=f"user_feedback_{decision.type.value}",
                    lesson=f"Feedback: {analysis['improvement_suggestion']}. What worked: {analysis['what_worked']}",
                    confidence=0.7,
                    evidence_count=1
                )
                self.learnings.append(learning)
                
        except Exception as e:
            print(f"[SelfImprovementEngine] Error analyzing feedback: {e}")
    
    def _update_performance_metrics(self, decision: Decision, outcome: Outcome):
        """Update performance metrics based on outcome"""
        metric_name = f"{decision.type.value}_success_rate"
        
        success_score = 1.0 if outcome.type == OutcomeType.SUCCESS else \
                       0.5 if outcome.type == OutcomeType.PARTIAL_SUCCESS else \
                       0.0 if outcome.type == OutcomeType.FAILURE else 0.25
        
        self.performance_metrics[metric_name].append(success_score)
        
        # Keep only last 100 data points
        if len(self.performance_metrics[metric_name]) > 100:
            self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-100:]
    
    def _generate_improvement_suggestions(self):
        """Generate improvement suggestions based on performance analysis"""
        # Analyze performance metrics
        for metric_name, values in self.performance_metrics.items():
            if len(values) >= 10:  # Need at least 10 data points
                avg = statistics.mean(values)
                
                if avg < 0.6:  # Below 60% success rate
                    # Determine improvement area
                    if "planning" in metric_name:
                        area = ImprovementArea.PLANNING
                    elif "prediction" in metric_name:
                        area = ImprovementArea.PREDICTION_ACCURACY
                    elif "priority" in metric_name:
                        area = ImprovementArea.PRIORITY_ALIGNMENT
                    elif "timing" in metric_name:
                        area = ImprovementArea.TIMING
                    elif "communication" in metric_name:
                        area = ImprovementArea.COMMUNICATION
                    elif "resource" in metric_name:
                        area = ImprovementArea.RESOURCE_MANAGEMENT
                    else:
                        area = ImprovementArea.CONTEXT_UNDERSTANDING
                    
                    # Check if similar suggestion exists
                    for imp in self.improvement_suggestions:
                        if imp.area == area:
                            imp.priority = min(10.0, imp.priority + 1.0)
                            return
                    
                    # Create new suggestion
                    suggestion = ImprovementSuggestion(
                        area=area,
                        description=f"Improve {area.value} - current success rate: {avg:.1%}",
                        rationale=f"Performance metrics show {area.value} needs improvement",
                        priority=7.0,
                        action_steps=[
                            "Analyze recent failures in this area",
                            "Review decision-making process",
                            "Consult relevant learnings",
                            "Test alternative approaches"
                        ],
                        estimated_impact="Medium - improve overall performance"
                    )
                    self.improvement_suggestions.append(suggestion)
    
    def get_performance_report(self) -> Dict:
        """Generate a comprehensive performance report"""
        report = {
            "overall_success_rate": 0.0,
            "decision_type_performance": {},
            "recent_trends": {},
            "top_learnings": [],
            "priority_improvements": [],
            "total_decisions": len(self.decisions),
            "total_outcomes": len(self.outcomes)
        }
        
        # Calculate overall success rate
        if self.performance_metrics:
            all_values = []
            for values in self.performance_metrics.values():
                all_values.extend(values)
            if all_values:
                report["overall_success_rate"] = statistics.mean(all_values)
        
        # Performance by decision type
        for metric_name, values in self.performance_metrics.items():
            if values:
                report["decision_type_performance"][metric_name] = {
                    "success_rate": statistics.mean(values),
                    "sample_size": len(values),
                    "trend": "improving" if len(values) >= 5 and statistics.mean(values[-5:]) > statistics.mean(values[:-5]) else "stable"
                }
        
        # Top learnings by confidence
        report["top_learnings"] = [
            {
                "topic": l.topic,
                "lesson": l.lesson,
                "confidence": l.confidence,
                "evidence_count": l.evidence_count
            }
            for l in sorted(self.learnings, key=lambda x: x.confidence, reverse=True)[:5]
        ]
        
        # Priority improvements
        report["priority_improvements"] = [
            {
                "area": imp.area.value,
                "description": imp.description,
                "priority": imp.priority,
                "estimated_impact": imp.estimated_impact
            }
            for imp in sorted(self.improvement_suggestions, key=lambda x: x.priority, reverse=True)[:5]
        ]
        
        return report
    
    def apply_learning(self, learning_id: int) -> bool:
        """Apply a specific learning to improve future decisions"""
        try:
            if 0 <= learning_id < len(self.learnings):
                learning = self.learnings[learning_id]
                learning.last_applied = datetime.utcnow().isoformat()
                self._save_data()
                print(f"[SelfImprovementEngine] Applied learning: {learning.lesson}")
                return True
            return False
        except Exception as e:
            print(f"[SelfImprovementEngine] Error applying learning: {e}")
            return False
    
    def get_relevant_learnings(self, context: Dict) -> List[Learning]:
        """Get learnings relevant to current context"""
        relevant = []
        
        for learning in self.learnings:
            # Simple relevance check - can be improved with semantic matching
            if any(key in learning.topic.lower() for key in str(context).lower().split()):
                relevant.append(learning)
        
        # Sort by confidence
        relevant.sort(key=lambda x: x.confidence, reverse=True)
        
        return relevant


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_self_improvement_engine() -> SelfImprovementEngine:
    """Get the singleton self-improvement engine instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = SelfImprovementEngine()
    return _instance
