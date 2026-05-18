"""
Deep Psychological Modeling for LOVE
Models Karthi's values, motivations, fears, aspirations, and personality traits.
This enables LOVE to understand Karthi at a deep psychological level for AGI-level intelligence.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import re

from core.settings import get_settings

SETTINGS = get_settings()


class ValueType(Enum):
    """Types of values a person can have"""
    ACHIEVEMENT = "achievement"  # Success, accomplishment
    AUTONOMY = "autonomy"  # Freedom, independence
    CONNECTION = "connection"  # Relationships, belonging
    GROWTH = "growth"  # Learning, development
    SECURITY = "security"  # Stability, safety
    CREATIVITY = "creativity"  # Innovation, expression
    SERVICE = "service"  # Helping others, contribution
    BALANCE = "balance"  # Work-life harmony


class MotivationType(Enum):
    """Types of motivations"""
    INTRINSIC = "intrinsic"  # Internal drive
    EXTRINSIC = "extrinsic"  # External rewards
    SOCIAL = "social"  # Social pressure/approval
    MORAL = "moral"  # Ethical principles


class EmotionalTrigger(Enum):
    """Common emotional triggers"""
    DEADLINE_PRESSURE = "deadline_pressure"
    SOCIAL_CONFLICT = "social_conflict"
    ACHIEVEMENT = "achievement"
    FAILURE = "failure"
    UNCERTAINTY = "uncertainty"
    OVERWHELM = "overwhelm"
    BOREDOM = "boredom"
    EXCITEMENT = "excitement"


@dataclass
class Value:
    """A core value that motivates behavior"""
    type: ValueType
    strength: float  # 0-10, how important this value is
    description: str
    examples: List[str] = field(default_factory=list)
    last_confirmed: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Motivation:
    """A motivation driving behavior"""
    type: MotivationType
    description: str
    triggers: List[str] = field(default_factory=list)
    strength: float = 0.0  # 0-10
    active: bool = True


@dataclass
class Aspiration:
    """A long-term goal or dream"""
    title: str
    description: str
    timeline: str  # e.g., "6 months", "1 year", "5 years"
    priority: float  # 0-10
    progress: float  # 0-1
    blockers: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Fear:
    """A fear or anxiety"""
    title: str
    description: str
    severity: float  # 0-10
    triggers: List[str] = field(default_factory=list)
    coping_strategies: List[str] = field(default_factory=list)


@dataclass
class PersonalityTrait:
    """A personality dimension (Big Five model)"""
    name: str  # Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
    score: float  # 0-10
    description: str
    behaviors: List[str] = field(default_factory=list)


@dataclass
class PsychologicalProfile:
    """Complete psychological model of Karthi"""
    # Core values
    values: Dict[ValueType, Value] = field(default_factory=dict)
    
    # Motivations
    motivations: List[Motivation] = field(default_factory=list)
    
    # Aspirations
    aspirations: List[Aspiration] = field(default_factory=list)
    
    # Fears and anxieties
    fears: List[Fear] = field(default_factory=list)
    
    # Personality traits (Big Five)
    personality: Dict[str, PersonalityTrait] = field(default_factory=dict)
    
    # Behavioral patterns
    patterns: Dict[str, List[str]] = field(default_factory=dict)
    
    # Decision-making style
    decision_style: str = "analytical"  # analytical, intuitive, collaborative, decisive
    
    # Stress response patterns
    stress_responses: Dict[str, str] = field(default_factory=dict)
    
    # Learning preferences
    learning_style: str = "visual"  # visual, auditory, kinesthetic, reading/writing
    
    # Communication preferences
    communication_style: str = "direct"  # direct, diplomatic, enthusiastic, reserved
    
    # Work preferences
    work_style: str = "focused"  # focused, collaborative, flexible, structured
    
    # Last updated
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Confidence in model (0-1)
    confidence: float = 0.5


class PsychologicalModel:
    """
    Deep psychological modeling system.
    Learns and models Karthi's psychological profile over time.
    """
    
    def __init__(self):
        self.profile = PsychologicalProfile()
        self.lock = threading.Lock()
        self._load_profile()
        self._initialize_default_profile()
    
    def _initialize_default_profile(self):
        """Initialize default psychological profile based on known information"""
        # These are initial assumptions that will be refined through learning
        
        # Core values (based on typical developer profile + observed behavior)
        if not self.profile.values:
            self.profile.values = {
                ValueType.ACHIEVEMENT: Value(
                    type=ValueType.ACHIEVEMENT,
                    strength=8.5,
                    description="Driven to build things and see projects through to completion",
                    examples=["Completing LOVE", "Shipping features", "Learning new technologies"]
                ),
                ValueType.GROWTH: Value(
                    type=ValueType.GROWTH,
                    strength=9.0,
                    description="Constantly learning and improving",
                    examples=["Learning AI/ML", "Building AGI", "Expanding technical skills"]
                ),
                ValueType.AUTONOMY: Value(
                    type=ValueType.AUTONOMY,
                    strength=7.5,
                    description="Values independence and self-direction",
                    examples=["Working on personal projects", "Making own decisions"]
                ),
                ValueType.CREATIVITY: Value(
                    type=ValueType.CREATIVITY,
                    strength=8.0,
                    description="Enjoys creating and innovating",
                    examples=["Building LOVE from scratch", "Designing systems"]
                ),
                ValueType.CONNECTION: Value(
                    type=ValueType.CONNECTION,
                    strength=6.0,
                    description="Values relationships but secondary to achievement",
                    examples=["Maintaining key relationships", "Helping others"]
                ),
                ValueType.BALANCE: Value(
                    type=ValueType.BALANCE,
                    strength=5.0,
                    description="Struggles with work-life balance, aware of need for it",
                    examples=["9-hour work limit", "Aware of stress levels"]
                ),
            }
        
        # Motivations
        if not self.profile.motivations:
            self.profile.motivations = [
                Motivation(
                    type=MotivationType.INTRINSIC,
                    description="Building something meaningful and impactful",
                    strength=9.0,
                    triggers=["Seeing progress", "Solving hard problems", "Creating value"]
                ),
                Motivation(
                    type=MotivationType.INTRINSIC,
                    description="Mastery and technical excellence",
                    strength=8.5,
                    triggers=["Learning new skills", "Deep work", "Technical challenges"]
                ),
                Motivation(
                    type=MotivationType.EXTRINSIC,
                    description="Recognition and impact",
                    strength=6.0,
                    triggers=["Positive feedback", "Seeing others use LOVE", "Career advancement"]
                ),
            ]
        
        # Aspirations
        if not self.profile.aspirations:
            self.profile.aspirations = [
                Aspiration(
                    title="Build AGI-level intelligence",
                    description="Create LOVE into a truly autonomous, intelligent system",
                    timeline="Ongoing",
                    priority=10.0,
                    progress=0.3
                ),
                Aspiration(
                    title="Master AI/ML",
                    description="Deep expertise in artificial intelligence and machine learning",
                    timeline="1-2 years",
                    priority=8.0,
                    progress=0.4
                ),
                Aspiration(
                    title="Improve work-life balance",
                    description="Achieve sustainable work habits while maintaining productivity",
                    timeline="6 months",
                    priority=7.0,
                    progress=0.2
                ),
            ]
        
        # Fears
        if not self.profile.fears:
            self.profile.fears = [
                Fear(
                    title="Failure to achieve AGI",
                    description="Fear that LOVE won't reach true AGI capabilities",
                    severity=7.0,
                    triggers=["Stagnation in progress", "Comparison to other systems"],
                    coping_strategies=["Focus on incremental progress", "Learn from others"]
                ),
                Fear(
                    title="Burnout",
                    description="Fear of overworking and losing passion",
                    severity=6.0,
                    triggers=["Long work hours", "High stress", "Lack of progress"],
                    coping_strategies=["Enforce work limits", "Take breaks", "Celebrate small wins"]
                ),
                Fear(
                    title="Wasting time",
                    description="Fear of spending time on unimportant things",
                    severity=5.0,
                    triggers=["Distractions", "Unclear priorities"],
                    coping_strategies=["Focus on high-impact work", "Regular prioritization"]
                ),
            ]
        
        # Personality traits (Big Five)
        if not self.profile.personality:
            self.profile.personality = {
                "Openness": PersonalityTrait(
                    name="Openness",
                    score=9.0,
                    description="Highly open to new experiences and ideas",
                    behaviors=["Learns new technologies", "Experiments", "Thinks creatively"]
                ),
                "Conscientiousness": PersonalityTrait(
                    name="Conscientiousness",
                    score=8.5,
                    description="Organized and goal-oriented",
                    behaviors=["Sets ambitious goals", "Tracks progress", "Plans ahead"]
                ),
                "Extraversion": PersonalityTrait(
                    name="Extraversion",
                    score=5.0,
                    description="Balanced between introversion and extraversion",
                    behaviors=["Can work independently", "Collaborates when needed"]
                ),
                "Agreeableness": PersonalityTrait(
                    name="Agreeableness",
                    score=7.0,
                    description="Generally cooperative and considerate",
                    behaviors=["Helps others", "Values relationships"]
                ),
                "Neuroticism": PersonalityTrait(
                    name="Neuroticism",
                    score=6.0,
                    description="Moderate stress sensitivity",
                    behaviors=["Can get stressed", "Aware of emotional state"]
                ),
            }
        
        self._save_profile()
    
    def _load_profile(self):
        """Load psychological profile from persistent storage"""
        try:
            profile_file = SETTINGS.data_dir / "psychological_profile.json"
            if profile_file.exists():
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    
                    # Reconstruct values
                    values = {}
                    for vt_str, v_data in data.get("values", {}).items():
                        vt = ValueType(vt_str)
                        values[vt] = Value(
                            type=vt,
                            strength=v_data["strength"],
                            description=v_data["description"],
                            examples=v_data.get("examples", []),
                            last_confirmed=v_data.get("last_confirmed")
                        )
                    self.profile.values = values
                    
                    # Reconstruct motivations
                    motivations = []
                    for m_data in data.get("motivations", []):
                        motivations.append(Motivation(
                            type=MotivationType(m_data["type"]),
                            description=m_data["description"],
                            triggers=m_data.get("triggers", []),
                            strength=m_data.get("strength", 0.0),
                            active=m_data.get("active", True)
                        ))
                    self.profile.motivations = motivations
                    
                    # Reconstruct aspirations
                    aspirations = []
                    for a_data in data.get("aspirations", []):
                        aspirations.append(Aspiration(
                            title=a_data["title"],
                            description=a_data["description"],
                            timeline=a_data["timeline"],
                            priority=a_data["priority"],
                            progress=a_data.get("progress", 0.0),
                            blockers=a_data.get("blockers", []),
                            created_at=a_data.get("created_at")
                        ))
                    self.profile.aspirations = aspirations
                    
                    # Reconstruct fears
                    fears = []
                    for f_data in data.get("fears", []):
                        fears.append(Fear(
                            title=f_data["title"],
                            description=f_data["description"],
                            severity=f_data["severity"],
                            triggers=f_data.get("triggers", []),
                            coping_strategies=f_data.get("coping_strategies", [])
                        ))
                    self.profile.fears = fears
                    
                    # Load other fields
                    self.profile.patterns = data.get("patterns", {})
                    self.profile.decision_style = data.get("decision_style", "analytical")
                    self.profile.stress_responses = data.get("stress_responses", {})
                    self.profile.learning_style = data.get("learning_style", "visual")
                    self.profile.communication_style = data.get("communication_style", "direct")
                    self.profile.work_style = data.get("work_style", "focused")
                    self.profile.last_updated = data.get("last_updated", datetime.utcnow().isoformat())
                    self.profile.confidence = data.get("confidence", 0.5)
                    
        except Exception as e:
            print(f"[PsychologicalModel] Error loading profile: {e}")
    
    def _save_profile(self):
        """Save psychological profile to persistent storage"""
        try:
            profile_file = SETTINGS.data_dir / "psychological_profile.json"
            with self.lock:
                data = {
                    "values": {
                        vt.value: {
                            "strength": v.strength,
                            "description": v.description,
                            "examples": v.examples,
                            "last_confirmed": v.last_confirmed
                        }
                        for vt, v in self.profile.values.items()
                    },
                    "motivations": [
                        {
                            "type": m.type.value,
                            "description": m.description,
                            "triggers": m.triggers,
                            "strength": m.strength,
                            "active": m.active
                        }
                        for m in self.profile.motivations
                    ],
                    "aspirations": [
                        {
                            "title": a.title,
                            "description": a.description,
                            "timeline": a.timeline,
                            "priority": a.priority,
                            "progress": a.progress,
                            "blockers": a.blockers,
                            "created_at": a.created_at
                        }
                        for a in self.profile.aspirations
                    ],
                    "fears": [
                        {
                            "title": f.title,
                            "description": f.description,
                            "severity": f.severity,
                            "triggers": f.triggers,
                            "coping_strategies": f.coping_strategies
                        }
                        for f in self.profile.fears
                    ],
                    "patterns": self.profile.patterns,
                    "decision_style": self.profile.decision_style,
                    "stress_responses": self.profile.stress_responses,
                    "learning_style": self.profile.learning_style,
                    "communication_style": self.profile.communication_style,
                    "work_style": self.profile.work_style,
                    "last_updated": self.profile.last_updated,
                    "confidence": self.profile.confidence
                }
                with open(profile_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PsychologicalModel] Error saving profile: {e}")
    
    def update_from_conversation(self, conversation: str, user_response: str):
        """
        Update psychological model based on conversation analysis.
        This is how LOVE learns about Karthi over time.
        """
        try:
            # Analyze conversation for psychological insights
            insights = self._analyze_conversation(conversation, user_response)
            
            # Update values based on insights
            for insight in insights:
                if insight["type"] == "value_expression":
                    self._update_value_strength(insight["value"], insight["adjustment"])
                elif insight["type"] == "motivation_detected":
                    self._add_motivation(insight["motivation"])
                elif insight["type"] == "aspiration_mentioned":
                    self._update_aspiration(insight["aspiration"])
                elif insight["type"] == "fear_expressed":
                    self._update_fear(insight["fear"])
            
            self.profile.last_updated = datetime.utcnow().isoformat()
            self.profile.confidence = min(1.0, self.profile.confidence + 0.01)
            self._save_profile()
            
        except Exception as e:
            print(f"[PsychologicalModel] Error updating from conversation: {e}")
    
    def _analyze_conversation(self, conversation: str, user_response: str) -> List[Dict]:
        """
        Use LLM to analyze conversation for psychological insights.
        """
        try:
            from core.agent import chat
            
            prompt = f"""You are LOVE, analyzing Karthi's psychological profile from conversation.

CONVERSATION:
{conversation}

KARTHI'S RESPONSE:
{user_response}

Analyze this for psychological insights. Look for:
1. Value expressions (what matters to Karthi)
2. Motivations (what drives Karthi)
3. Aspirations (what Karthi wants to achieve)
4. Fears or concerns
5. Personality indicators

Return JSON with this structure:
{{
  "insights": [
    {{
      "type": "value_expression|motivation_detected|aspiration_mentioned|fear_expressed",
      "content": "what was expressed",
      "value": "achievement|autonomy|connection|growth|security|creativity|service|balance",
      "adjustment": 0.5,  // For values: -1 to 1 adjustment
      "motivation": {{  // For motivations
        "type": "intrinsic|extrinsic|social|moral",
        "description": "description",
        "strength": 8.0
      }},
      "aspiration": {{  // For aspirations
        "title": "title",
        "description": "description",
        "timeline": "timeline"
      }},
      "fear": {{  // For fears
        "title": "title",
        "description": "description",
        "severity": 7.0
      }}
    }}
  ]
}}"""
            
            response = chat(prompt, mode="reasoning")
            response_text = response.get("response", "")
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("insights", [])
            
            return []
            
        except Exception as e:
            print(f"[PsychologicalModel] Error analyzing conversation: {e}")
            return []
    
    def _update_value_strength(self, value_type: str, adjustment: float):
        """Update the strength of a value"""
        try:
            vt = ValueType(value_type)
            if vt in self.profile.values:
                self.profile.values[vt].strength = max(0, min(10, 
                    self.profile.values[vt].strength + adjustment))
                self.profile.values[vt].last_confirmed = datetime.utcnow().isoformat()
        except Exception as e:
            print(f"[PsychologicalModel] Error updating value: {e}")
    
    def _add_motivation(self, motivation_data: Dict):
        """Add or update a motivation"""
        try:
            for m in self.profile.motivations:
                if m.description == motivation_data["description"]:
                    m.strength = motivation_data.get("strength", m.strength)
                    m.active = True
                    return
            
            # New motivation
            self.profile.motivations.append(Motivation(
                type=MotivationType(motivation_data["type"]),
                description=motivation_data["description"],
                strength=motivation_data.get("strength", 5.0),
                triggers=[]
            ))
        except Exception as e:
            print(f"[PsychologicalModel] Error adding motivation: {e}")
    
    def _update_aspiration(self, aspiration_data: Dict):
        """Add or update an aspiration"""
        try:
            for a in self.profile.aspirations:
                if a.title == aspiration_data["title"]:
                    a.description = aspiration_data.get("description", a.description)
                    a.timeline = aspiration_data.get("timeline", a.timeline)
                    return
            
            # New aspiration
            self.profile.aspirations.append(Aspiration(
                title=aspiration_data["title"],
                description=aspiration_data["description"],
                timeline=aspiration_data.get("timeline", "ongoing"),
                priority=aspiration_data.get("priority", 7.0)
            ))
        except Exception as e:
            print(f"[PsychologicalModel] Error updating aspiration: {e}")
    
    def _update_fear(self, fear_data: Dict):
        """Add or update a fear"""
        try:
            for f in self.profile.fears:
                if f.title == fear_data["title"]:
                    f.description = fear_data.get("description", f.description)
                    f.severity = fear_data.get("severity", f.severity)
                    return
            
            # New fear
            self.profile.fears.append(Fear(
                title=fear_data["title"],
                description=fear_data["description"],
                severity=fear_data.get("severity", 5.0),
                triggers=[]
            ))
        except Exception as e:
            print(f"[PsychologicalModel] Error updating fear: {e}")
    
    def predict_decision(self, options: List[Dict]) -> Dict:
        """
        Predict which option Karthi would choose based on psychological profile.
        This enables LOVE to anticipate Karthi's decisions.
        """
        try:
            scores = []
            
            for option in options:
                score = 0.0
                reasoning = []
                
                # Score based on values alignment
                for vt, value in self.profile.values.items():
                    if vt.value.lower() in option.get("tags", []):
                        score += value.strength * 0.3
                        reasoning.append(f"Aligns with {vt.value} value (strength {value.strength})")
                
                # Score based on motivations
                for motivation in self.profile.motivations:
                    if motivation.active:
                        for trigger in motivation.triggers:
                            if trigger.lower() in option.get("description", "").lower():
                                score += motivation.strength * 0.2
                                reasoning.append(f"Triggers {motivation.type.value} motivation")
                
                # Score based on aspirations
                for aspiration in self.profile.aspirations:
                    if aspiration.title.lower() in option.get("description", "").lower():
                        score += aspiration.priority * 0.2
                        reasoning.append(f"Advances aspiration: {aspiration.title}")
                
                # Score based on decision style
                if self.profile.decision_style == "analytical" and option.get("analytical"):
                    score += 2.0
                    reasoning.append("Matches analytical decision style")
                elif self.profile.decision_style == "intuitive" and option.get("creative"):
                    score += 2.0
                    reasoning.append("Matches intuitive decision style")
                
                scores.append({
                    "option": option,
                    "score": score,
                    "reasoning": reasoning
                })
            
            # Sort by score
            scores.sort(key=lambda x: x["score"], reverse=True)
            
            if scores:
                best = scores[0]
                return {
                    "predicted_choice": best["option"],
                    "confidence": min(1.0, best["score"] / 10.0),
                    "reasoning": best["reasoning"],
                    "all_scores": scores
                }
            
            return {"error": "No options provided"}
            
        except Exception as e:
            print(f"[PsychologicalModel] Error predicting decision: {e}")
            return {"error": str(e)}
    
    def get_emotional_state_prediction(self, context: Dict) -> Dict:
        """
        Predict Karthi's emotional state based on context and psychological profile.
        """
        try:
            predicted_stress = 5.0  # Baseline
            
            # Adjust based on known triggers
            for fear in self.profile.fears:
                for trigger in fear.triggers:
                    if trigger.lower() in str(context).lower():
                        predicted_stress += fear.severity * 0.3
            
            # Adjust based on value threats
            for vt, value in self.profile.values:
                if vt == ValueType.BALANCE and context.get("work_hours", 0) > 9:
                    predicted_stress += value.strength * 0.2
            
            # Adjust based on aspiration progress
            for aspiration in self.profile.aspirations:
                if aspiration.progress < 0.5 and context.get("deadline_pressure"):
                    predicted_stress += aspiration.priority * 0.1
            
            predicted_stress = min(10.0, max(0.0, predicted_stress))
            
            return {
                "predicted_stress": round(predicted_stress, 1),
                "confidence": self.profile.confidence,
                "factors": [
                    "Psychological profile analysis",
                    "Value alignment check",
                    "Aspiration progress assessment",
                    "Fear trigger detection"
                ]
            }
            
        except Exception as e:
            print(f"[PsychologicalModel] Error predicting emotional state: {e}")
            return {"error": str(e)}
    
    def get_profile_summary(self) -> Dict:
        """Get a summary of the psychological profile"""
        return {
            "values": {vt.value: {"strength": v.strength, "description": v.description} 
                      for vt, v in self.profile.values.items()},
            "top_motivations": [
                {"type": m.type.value, "description": m.description, "strength": m.strength}
                for m in sorted(self.profile.motivations, key=lambda x: x.strength, reverse=True)[:3]
            ],
            "aspirations": [
                {"title": a.title, "priority": a.priority, "progress": a.progress}
                for a in sorted(self.profile.aspirations, key=lambda x: x.priority, reverse=True)[:3]
            ],
            "personality": {
                name: {"score": trait.score, "description": trait.description}
                for name, trait in self.profile.personality.items()
            },
            "decision_style": self.profile.decision_style,
            "work_style": self.profile.work_style,
            "confidence": self.profile.confidence,
            "last_updated": self.profile.last_updated
        }


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_psychological_model() -> PsychologicalModel:
    """Get the singleton psychological model instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = PsychologicalModel()
    return _instance
