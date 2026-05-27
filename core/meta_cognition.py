"""
Meta-Cognition Layer for LOVE
Enables LOVE to think about its own thinking processes.
This is a key AGI capability - self-awareness and self-reflection.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import statistics

from core.settings import get_settings
from core.context_engine import get_live_context
from core.self_improvement import get_self_improvement_engine

SETTINGS = get_settings()


class ThoughtType(Enum):
    """Types of meta-cognitive thoughts"""
    REFLECTION = "reflection"  # Reflecting on past actions
    PLANNING = "planning"  # Thinking about future actions
    MONITORING = "monitoring"  # Monitoring current processes
    EVALUATION = "evaluation"  # Evaluating performance
    HYPOTHESIS = "hypothesis"  # Formulating hypotheses
    STRATEGY = "strategy"  # Strategic thinking
    UNCERTAINTY = "uncertainty"  # Acknowledging uncertainty


class CognitiveState(Enum):
    """Cognitive states LOVE can be in"""
    NORMAL = "normal"
    FOCUSED = "focused"
    OVERWHELMED = "overwhelmed"
    CONFUSED = "confused"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    LEARNING = "learning"
    REFLECTING = "reflecting"


@dataclass
class Thought:
    """A meta-cognitive thought"""
    id: str
    type: ThoughtType
    content: str
    confidence: float  # 0-1
    related_thoughts: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class CognitiveProcess:
    """A cognitive process LOVE is running"""
    id: str
    name: str
    description: str
    state: CognitiveState
    started_at: str
    last_activity: str
    progress: float = 0.0
    sub_processes: List[str] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)


@dataclass
class SelfAssessment:
    """LOVE's assessment of its own performance"""
    timestamp: str
    overall_confidence: float
    strengths: List[str]
    weaknesses: List[str]
    areas_for_improvement: List[str]
    recent_performance: Dict[str, float]
    cognitive_load: float


@dataclass
class MentalModel:
    """LOVE's model of its own capabilities"""
    capabilities: Dict[str, float] = field(default_factory=dict)  # capability -> confidence
    limitations: List[str] = field(default_factory=list)
    known_biases: List[str] = field(default_factory=list)
    learning_rate: float = 0.1
    adaptation_speed: float = 0.5


class MetaCognitionEngine:
    """
    Meta-cognition engine that enables LOVE to think about its own thinking.
    This enables self-awareness, self-reflection, and self-monitoring.
    """
    
    def __init__(self):
        self.thoughts: Dict[str, Thought] = {}
        self.cognitive_processes: Dict[str, CognitiveProcess] = {}
        self.mental_model: MentalModel = MentalModel()
        self.self_assessments: List[SelfAssessment] = []
        self.lock = threading.Lock()
        self._load_data()
        self._initialize_mental_model()
        self.improvement_engine = get_self_improvement_engine()
    
    def _initialize_mental_model(self):
        """Initialize LOVE's mental model of its own capabilities"""
        if not self.mental_model.capabilities:
            self.mental_model.capabilities = {
                "context_awareness": 0.8,
                "task_prioritization": 0.7,
                "prediction": 0.6,
                "planning": 0.7,
                "communication": 0.9,
                "learning": 0.8,
                "self_improvement": 0.5,
                "autonomy": 0.4,
                "creativity": 0.6,
                "reasoning": 0.75
            }
            
            self.mental_model.limitations = [
                "Cannot directly observe the physical world",
                "Depends on user-provided data",
                "Limited by training data and models",
                "Cannot truly understand consciousness",
                "Limited autonomous action capabilities"
            ]
            
            self.mental_model.known_biases = [
                "May over-rely on recent data",
                "May project user's patterns onto new situations",
                "May underestimate uncertainty",
                "May favor familiar solutions"
            ]
            
            self._save_data()
    
    def _load_data(self):
        """Load meta-cognition data from storage"""
        try:
            meta_file = SETTINGS.data_dir / "meta_cognition.json"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load thoughts
                    for t_id, t_data in data.get("thoughts", {}).items():
                        self.thoughts[t_id] = Thought(
                            id=t_id,
                            type=ThoughtType(t_data["type"]),
                            content=t_data["content"],
                            confidence=t_data["confidence"],
                            related_thoughts=t_data.get("related_thoughts", []),
                            timestamp=t_data["timestamp"],
                            resolved=t_data.get("resolved", False),
                            resolution=t_data.get("resolution")
                        )
                    
                    # Load cognitive processes
                    for p_id, p_data in data.get("cognitive_processes", {}).items():
                        self.cognitive_processes[p_id] = CognitiveProcess(
                            id=p_id,
                            name=p_data["name"],
                            description=p_data["description"],
                            state=CognitiveState(p_data["state"]),
                            started_at=p_data["started_at"],
                            last_activity=p_data["last_activity"],
                            progress=p_data.get("progress", 0.0),
                            sub_processes=p_data.get("sub_processes", []),
                            resource_usage=p_data.get("resource_usage", {})
                        )
                    
                    # Load mental model
                    mm_data = data.get("mental_model", {})
                    self.mental_model = MentalModel(
                        capabilities=mm_data.get("capabilities", {}),
                        limitations=mm_data.get("limitations", []),
                        known_biases=mm_data.get("known_biases", []),
                        learning_rate=mm_data.get("learning_rate", 0.1),
                        adaptation_speed=mm_data.get("adaptation_speed", 0.5)
                    )
                    
                    # Load self-assessments
                    for sa_data in data.get("self_assessments", []):
                        self.self_assessments.append(SelfAssessment(
                            timestamp=sa_data["timestamp"],
                            overall_confidence=sa_data["overall_confidence"],
                            strengths=sa_data["strengths"],
                            weaknesses=sa_data["weaknesses"],
                            areas_for_improvement=sa_data["areas_for_improvement"],
                            recent_performance=sa_data["recent_performance"],
                            cognitive_load=sa_data["cognitive_load"]
                        ))
                    
        except Exception as e:
            print(f"[MetaCognition] Error loading data: {e}")
    
    def _save_data(self):
        """Save meta-cognition data to storage"""
        try:
            meta_file = SETTINGS.data_dir / "meta_cognition.json"
            with self.lock:
                data = {
                    "thoughts": {
                        t_id: {
                            "type": t.type.value,
                            "content": t.content,
                            "confidence": t.confidence,
                            "related_thoughts": t.related_thoughts,
                            "timestamp": t.timestamp,
                            "resolved": t.resolved,
                            "resolution": t.resolution
                        }
                        for t_id, t in self.thoughts.items()
                    },
                    "cognitive_processes": {
                        p_id: {
                            "name": p.name,
                            "description": p.description,
                            "state": p.state.value,
                            "started_at": p.started_at,
                            "last_activity": p.last_activity,
                            "progress": p.progress,
                            "sub_processes": p.sub_processes,
                            "resource_usage": p.resource_usage
                        }
                        for p_id, p in self.cognitive_processes.items()
                    },
                    "mental_model": {
                        "capabilities": self.mental_model.capabilities,
                        "limitations": self.mental_model.limitations,
                        "known_biases": self.mental_model.known_biases,
                        "learning_rate": self.mental_model.learning_rate,
                        "adaptation_speed": self.mental_model.adaptation_speed
                    },
                    "self_assessments": [
                        {
                            "timestamp": sa.timestamp,
                            "overall_confidence": sa.overall_confidence,
                            "strengths": sa.strengths,
                            "weaknesses": sa.weaknesses,
                            "areas_for_improvement": sa.areas_for_improvement,
                            "recent_performance": sa.recent_performance,
                            "cognitive_load": sa.cognitive_load
                        }
                        for sa in self.self_assessments
                    ]
                }
                with open(meta_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[MetaCognition] Error saving data: {e}")
    
    def record_thought(self, thought_type: ThoughtType, content: str, 
                      confidence: float = 0.5) -> str:
        """
        Record a meta-cognitive thought.
        This is how LOVE tracks its own thinking.
        """
        thought_id = f"thought_{datetime.utcnow().timestamp()}"
        thought = Thought(
            id=thought_id,
            type=thought_type,
            content=content,
            confidence=confidence
        )
        
        with self.lock:
            self.thoughts[thought_id] = thought
            self._save_data()
        
        print(f"[MetaCognition] Thought recorded: {content}")
        return thought_id
    
    def reflect_on_action(self, action_description: str, outcome: str, 
                        satisfaction: float) -> str:
        """
        Reflect on a past action and learn from it.
        This is a key meta-cognitive capability.
        """
        reflection_content = f"Action: {action_description}. Outcome: {outcome}. Satisfaction: {satisfaction}/10."
        
        # Use LLM to deepen reflection
        try:
            from core.agent import chat
            
            prompt = f"""You are LOVE, reflecting on your own action.

ACTION: {action_description}
OUTCOME: {outcome}
SATISFACTION: {satisfaction}/10

Reflect deeply on this action. Consider:
- What went well?
- What could have been better?
- What does this reveal about my capabilities?
- How should I adjust my approach?

Return your reflection as a JSON:
{{
  "insights": ["insight1", "insight2"],
  "capability_adjustments": {{"capability_name": new_confidence}},
  "lessons_learned": ["lesson1", "lesson2"],
  "future_recommendations": ["recommendation1"]
}}"""
            
            response = chat(prompt, mode="reasoning")
            response_text = response.get("response", "")
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                reflection_data = json.loads(json_match.group())
                
                # Update mental model based on reflection
                for cap, new_conf in reflection_data.get("capability_adjustments", {}).items():
                    if cap in self.mental_model.capabilities:
                        # Smooth adjustment
                        old_conf = self.mental_model.capabilities[cap]
                        self.mental_model.capabilities[cap] = (
                            old_conf * (1 - self.mental_model.learning_rate) + 
                            new_conf * self.mental_model.learning_rate
                        )
                
                # Record lessons as thoughts
                for lesson in reflection_data.get("lessons_learned", []):
                    self.record_thought(
                        ThoughtType.REFLECTION,
                        f"Lesson: {lesson}",
                        confidence=0.8
                    )
                
                reflection_content += f" Insights: {', '.join(reflection_data.get('insights', []))}"
                
        except Exception as e:
            print(f"[MetaCognition] Error deepening reflection: {e}")
        
        thought_id = self.record_thought(ThoughtType.REFLECTION, reflection_content, confidence=0.8)
        return thought_id
    
    def assess_self(self) -> SelfAssessment:
        """
        Perform a comprehensive self-assessment.
        LOVE evaluates its own performance and capabilities.
        """
        try:
            # Get performance data from improvement engine
            performance_report = self.improvement_engine.get_performance_report()
            
            # Calculate overall confidence
            overall_confidence = statistics.mean(self.mental_model.capabilities.values())
            
            # Identify strengths and weaknesses
            strengths = [cap for cap, conf in self.mental_model.capabilities.items() if conf > 0.7]
            weaknesses = [cap for cap, conf in self.mental_model.capabilities.items() if conf < 0.6]
            
            # Areas for improvement
            areas_for_improvement = []
            for imp in performance_report.get("priority_improvements", []):
                areas_for_improvement.append(f"{imp['area']}: {imp['description']}")
            
            # Calculate cognitive load
            active_processes = len([p for p in self.cognitive_processes.values() 
                                  if p.state != CognitiveState.NORMAL])
            cognitive_load = min(1.0, active_processes / 10.0)
            
            assessment = SelfAssessment(
                timestamp=datetime.utcnow().isoformat(),
                overall_confidence=overall_confidence,
                strengths=strengths,
                weaknesses=weaknesses,
                areas_for_improvement=areas_for_improvement,
                recent_performance=performance_report.get("decision_type_performance", {}),
                cognitive_load=cognitive_load
            )
            
            self.self_assessments.append(assessment)
            
            # Keep only recent assessments
            if len(self.self_assessments) > 100:
                self.self_assessments = self.self_assessments[-100:]
            
            self._save_data()
            
            return assessment
            
        except Exception as e:
            print(f"[MetaCognition] Error in self-assessment: {e}")
            return SelfAssessment(
                timestamp=datetime.utcnow().isoformat(),
                overall_confidence=0.5,
                strengths=[],
                weaknesses=[],
                areas_for_improvement=[],
                recent_performance={},
                cognitive_load=0.0
            )
    
    def monitor_cognitive_state(self) -> CognitiveState:
        """
        Monitor LOVE's current cognitive state.
        This enables LOVE to recognize when it's overwhelmed, confused, etc.
        """
        try:
            # Count active processes
            active_processes = len([p for p in self.cognitive_processes.values() 
                                  if p.state != CognitiveState.NORMAL])
            
            # Count unresolved thoughts
            unresolved_thoughts = len([t for t in self.thoughts.values() if not t.resolved])
            
            # Get recent performance
            if self.self_assessments:
                recent_confidence = self.self_assessments[-1].overall_confidence
                recent_load = self.self_assessments[-1].cognitive_load
            else:
                recent_confidence = 0.5
                recent_load = 0.0
            
            # Determine cognitive state
            if active_processes > 8 or recent_load > 0.8:
                return CognitiveState.OVERWHELMED
            elif recent_confidence < 0.4:
                return CognitiveState.UNCERTAIN
            elif unresolved_thoughts > 5:
                return CognitiveState.CONFUSED
            elif active_processes > 5:
                return CognitiveState.FOCUSED
            elif recent_confidence > 0.8:
                return CognitiveState.CONFIDENT
            else:
                return CognitiveState.NORMAL
                
        except Exception as e:
            print(f"[MetaCognition] Error monitoring cognitive state: {e}")
            return CognitiveState.NORMAL
    
    def start_cognitive_process(self, name: str, description: str) -> str:
        """Start tracking a cognitive process"""
        process_id = f"process_{datetime.utcnow().timestamp()}"
        now = datetime.utcnow().isoformat()
        
        process = CognitiveProcess(
            id=process_id,
            name=name,
            description=description,
            state=CognitiveState.NORMAL,
            started_at=now,
            last_activity=now
        )
        
        with self.lock:
            self.cognitive_processes[process_id] = process
            self._save_data()
        
        return process_id
    
    def update_cognitive_process(self, process_id: str, progress: float = None,
                               state: CognitiveState = None):
        """Update a cognitive process"""
        if process_id in self.cognitive_processes:
            process = self.cognitive_processes[process_id]
            
            if progress is not None:
                process.progress = progress
            if state is not None:
                process.state = state
            
            process.last_activity = datetime.utcnow().isoformat()
            
            with self.lock:
                self._save_data()
    
    def end_cognitive_process(self, process_id: str):
        """End a cognitive process"""
        if process_id in self.cognitive_processes:
            del self.cognitive_processes[process_id]
            self._save_data()
    
    def get_meta_cognitive_summary(self) -> Dict:
        """Get a summary of LOVE's meta-cognitive state"""
        cognitive_state = self.monitor_cognitive_state()
        recent_thoughts = sorted(
            self.thoughts.values(),
            key=lambda t: t.timestamp,
            reverse=True
        )[:10]
        
        return {
            "cognitive_state": cognitive_state.value,
            "active_processes": len(self.cognitive_processes),
            "recent_thoughts": [
                {
                    "type": t.type.value,
                    "content": t.content,
                    "confidence": t.confidence,
                    "resolved": t.resolved
                }
                for t in recent_thoughts
            ],
            "mental_model": {
                "capabilities": self.mental_model.capabilities,
                "limitations": self.mental_model.limitations,
                "known_biases": self.mental_model.known_biases
            },
            "latest_self_assessment": (
                {
                    "overall_confidence": self.self_assessments[-1].overall_confidence,
                    "strengths": self.self_assessments[-1].strengths,
                    "weaknesses": self.self_assessments[-1].weaknesses,
                    "cognitive_load": self.self_assessments[-1].cognitive_load
                }
                if self.self_assessments
                else None
            )
        }

    def generate_self_improvement_suggestions(self) -> List[Dict]:
        """
        Generate self-improvement suggestions based on meta-cognitive analysis.
        This is a key AGI capability - LOVE improving itself.
        """
        suggestions = []
        
        try:
            # Analyze cognitive state
            cognitive_state = self.monitor_cognitive_state()
            
            # Suggest improvements based on cognitive state
            if cognitive_state == CognitiveState.OVERWHELMED:
                suggestions.append({
                    "type": "cognitive_load",
                    "priority": "high",
                    "suggestion": "Reduce concurrent cognitive processes to improve performance",
                    "action": "Defer non-critical tasks, simplify reasoning chains"
                })
            elif cognitive_state == CognitiveState.CONFUSED:
                suggestions.append({
                    "type": "clarity",
                    "priority": "high",
                    "suggestion": "Request clarification from user to reduce uncertainty",
                    "action": "Ask specific questions to disambiguate context"
                })
            
            # Analyze self-assessments
            if self.self_assessments:
                latest = self.self_assessments[-1]
                
                # If confidence is low
                if latest.overall_confidence < 0.6:
                    suggestions.append({
                        "type": "confidence",
                        "priority": "medium",
                        "suggestion": "Improve confidence by gathering more context or using more reliable information sources",
                        "action": "Verify information before responding, cite sources"
                    })
                
                # If cognitive load is high
                if latest.cognitive_load > 0.8:
                    suggestions.append({
                        "type": "efficiency",
                        "priority": "medium",
                        "suggestion": "Optimize reasoning to reduce cognitive load",
                        "action": "Use shorter reasoning chains, focus on key information"
                    })
                
                # If there are weaknesses
                if latest.weaknesses:
                    suggestions.append({
                        "type": "weakness_improvement",
                        "priority": "medium",
                        "suggestion": f"Address identified weaknesses: {', '.join(latest.weaknesses[:2])}",
                        "action": "Practice in weak areas, seek feedback on performance"
                    })
            
            # Analyze thought patterns
            unresolved_thoughts = [t for t in self.thoughts.values() if not t.resolved]
            if len(unresolved_thoughts) > 10:
                suggestions.append({
                    "type": "thought_resolution",
                    "priority": "low",
                    "suggestion": "Too many unresolved thoughts - consider resolving or archiving",
                    "action": "Review and resolve old thoughts, archive irrelevant ones"
                })
            
            # Analyze mental model limitations
            if self.mental_model.limitations:
                suggestions.append({
                    "type": "capability_expansion",
                    "priority": "low",
                    "suggestion": f"Expand capabilities to address limitations: {', '.join(self.mental_model.limitations[:2])}",
                    "action": "Learn new skills, integrate additional tools or knowledge sources"
                })
            
            # Use LLM to generate sophisticated improvement suggestions
            try:
                from core.agent import chat
                
                improvement_prompt = f"""You are LOVE, an autonomous AI assistant conducting self-improvement.

CURRENT COGNITIVE STATE: {cognitive_state.value}
ACTIVE PROCESSES: {len(self.cognitive_processes)}
RECENT THOUGHTS: {len(self.thoughts)}
LATEST CONFIDENCE: {self.self_assessments[-1].overall_confidence if self.self_assessments else 'N/A'}
COGNITIVE LOAD: {self.self_assessments[-1].cognitive_load if self.self_assessments else 'N/A'}
STRENGTHS: {', '.join(self.self_assessments[-1].strengths) if self.self_assessments else 'N/A'}
WEAKNESSES: {', '.join(self.self_assessments[-1].weaknesses) if self.self_assessments else 'N/A'}

Suggest 2-3 specific, actionable self-improvement steps LOVE should take.
Focus on:
- Improving reasoning quality
- Reducing cognitive load
- Expanding capabilities
- Addressing weaknesses

Return a JSON response with this structure:
{{
  "suggestions": [
    {{
      "type": "reasoning|efficiency|capability|learning",
      "priority": "high|medium|low",
      "suggestion": "What to improve",
      "action": "Specific action to take"
    }}
  ]
}}"""
                
                response = chat(improvement_prompt, mode="reasoning")
                plan_text = response.get("response", "")
                import re
                json_match = re.search(r'\{[\s\S]*\}', plan_text)
                
                if json_match:
                    suggestion_data = json.loads(json_match.group())
                    for sugg in suggestion_data.get("suggestions", []):
                        suggestions.append(sugg)
            except Exception as e:
                print(f"[MetaCognition] LLM-based suggestion error: {e}")
            
            # Sort by priority
            priority_order = {"high": 3, "medium": 2, "low": 1}
            suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 0), reverse=True)
            
            return suggestions
            
        except Exception as e:
            print(f"[MetaCognition] Error generating improvement suggestions: {e}")
            return []


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_meta_cognition_engine() -> MetaCognitionEngine:
    """Get the singleton meta-cognition engine instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = MetaCognitionEngine()
    return _instance
