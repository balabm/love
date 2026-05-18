"""
Predictive Intelligence for LOVE
Anticipates Karthi's needs, behaviors, and future states.
This is a core AGI capability - predicting what will happen before it does.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import statistics
from collections import defaultdict

from core.settings import get_settings
from core.context_engine import get_live_context
from core.psychological_model import get_psychological_model

SETTINGS = get_settings()


class PredictionType(Enum):
    """Types of predictions LOVE can make"""
    NEED = "need"  # What Karthi will need
    BEHAVIOR = "behavior"  # What Karthi will do
    EMOTIONAL_STATE = "emotional_state"  # How Karthi will feel
    DECISION = "decision"  # What Karthi will decide
    EVENT_IMPACT = "event_impact"  # How an event will affect Karthi
    RESOURCE_DEPLETION = "resource_depletion"  # When resources will run out
    OPPORTUNITY = "opportunity"  # Opportunities Karthi should pursue


class PredictionConfidence(Enum):
    """Confidence levels for predictions"""
    CERTAIN = 1.0
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    SPECULATIVE = 0.2


@dataclass
class Prediction:
    """A single prediction about the future"""
    id: str
    type: PredictionType
    description: str
    confidence: float  # 0-1
    timeframe: str  # e.g., "5 minutes", "1 hour", "today", "this week"
    impact: str  # "critical", "high", "medium", "low"
    evidence: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    outcome: Optional[str] = None  # What actually happened (for learning)


@dataclass
class Pattern:
    """A learned pattern in Karthi's behavior"""
    description: str
    frequency: float  # How often this pattern occurs
    conditions: List[str]  # Context conditions that trigger this pattern
    consequences: List[str]  # What typically happens
    confidence: float  # 0-1
    last_observed: str


class PredictiveEngine:
    """
    Predictive intelligence engine.
    Learns patterns and makes predictions about Karthi's future.
    """
    
    def __init__(self):
        self.predictions: Dict[str, Prediction] = {}
        self.patterns: List[Pattern] = []
        self.prediction_history: List[Dict] = []
        self.lock = threading.Lock()
        self._load_data()
        self.psych_model = get_psychological_model()
    
    def _load_data(self):
        """Load predictions and patterns from storage"""
        try:
            pred_file = SETTINGS.data_dir / "predictions.json"
            if pred_file.exists():
                with open(pred_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load predictions
                    for pred_id, pred_data in data.get("predictions", {}).items():
                        self.predictions[pred_id] = Prediction(
                            id=pred_id,
                            type=PredictionType(pred_data["type"]),
                            description=pred_data["description"],
                            confidence=pred_data["confidence"],
                            timeframe=pred_data["timeframe"],
                            impact=pred_data["impact"],
                            evidence=pred_data.get("evidence", []),
                            suggested_actions=pred_data.get("suggested_actions", []),
                            created_at=pred_data["created_at"],
                            expires_at=pred_data.get("expires_at"),
                            outcome=pred_data.get("outcome")
                        )
                    
                    # Load patterns
                    for pattern_data in data.get("patterns", []):
                        self.patterns.append(Pattern(
                            description=pattern_data["description"],
                            frequency=pattern_data["frequency"],
                            conditions=pattern_data.get("conditions", []),
                            consequences=pattern_data.get("consequences", []),
                            confidence=pattern_data["confidence"],
                            last_observed=pattern_data["last_observed"]
                        ))
                    
                    # Load history
                    self.prediction_history = data.get("prediction_history", [])
                    
        except Exception as e:
            print(f"[PredictiveEngine] Error loading data: {e}")
    
    def _save_data(self):
        """Save predictions and patterns to storage"""
        try:
            pred_file = SETTINGS.data_dir / "predictions.json"
            with self.lock:
                data = {
                    "predictions": {
                        pred_id: {
                            "type": pred.type.value,
                            "description": pred.description,
                            "confidence": pred.confidence,
                            "timeframe": pred.timeframe,
                            "impact": pred.impact,
                            "evidence": pred.evidence,
                            "suggested_actions": pred.suggested_actions,
                            "created_at": pred.created_at,
                            "expires_at": pred.expires_at,
                            "outcome": pred.outcome
                        }
                        for pred_id, pred in self.predictions.items()
                    },
                    "patterns": [
                        {
                            "description": p.description,
                            "frequency": p.frequency,
                            "conditions": p.conditions,
                            "consequences": p.consequences,
                            "confidence": p.confidence,
                            "last_observed": p.last_observed
                        }
                        for p in self.patterns
                    ],
                    "prediction_history": self.prediction_history[-1000:]  # Keep last 1000
                }
                with open(pred_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PredictiveEngine] Error saving data: {e}")
    
    def generate_predictions(self) -> List[Prediction]:
        """
        Generate predictions based on current context and learned patterns.
        This is the core predictive intelligence function.
        """
        predictions = []
        
        try:
            ctx = get_live_context()
            
            # Prediction: Meeting preparation need
            if ctx.next_event:
                minutes_away = ctx.next_event.get('minutes_away', 999)
                if minutes_away <= 30:
                    pred = Prediction(
                        id=f"pred_meeting_prep_{datetime.utcnow().timestamp()}",
                        type=PredictionType.NEED,
                        description=f"Karthi will need to prepare for '{ctx.next_event.get('title', 'meeting')}'",
                        confidence=0.9,
                        timeframe=f"{minutes_away} minutes",
                        impact="high",
                        evidence=[
                            f"Meeting starts in {minutes_away} minutes",
                            "Meeting preparation pattern observed in past"
                        ],
                        suggested_actions=[
                            "Review meeting agenda",
                            "Prepare talking points",
                            "Check relevant documents",
                            "Remind Karthi 5 minutes before"
                        ],
                        expires_at=(datetime.utcnow() + timedelta(minutes=minutes_away)).isoformat()
                    )
                    predictions.append(pred)
            
            # Prediction: Stress increase
            current_stress = ctx.stress_level
            if current_stress > 5:
                stress_prediction = self.psych_model.get_emotional_state_prediction(
                    {"work_hours": 9, "deadline_pressure": True}
                )
                predicted_stress = stress_prediction.get("predicted_stress", current_stress)
                
                if predicted_stress > current_stress:
                    pred = Prediction(
                        id=f"pred_stress_increase_{datetime.utcnow().timestamp()}",
                        type=PredictionType.EMOTIONAL_STATE,
                        description=f"Karthi's stress will likely increase to {predicted_stress}/10",
                        confidence=0.7,
                        timeframe="next 2 hours",
                        impact="high",
                        evidence=[
                            f"Current stress: {current_stress}/10",
                            "Psychological profile indicates stress sensitivity",
                            "Multiple tasks due today"
                        ],
                        suggested_actions=[
                            "Suggest break",
                            "Offer stress relief activity",
                            "Prioritize urgent tasks",
                            "Reduce non-essential notifications"
                        ],
                        expires_at=(datetime.utcnow() + timedelta(hours=2)).isoformat()
                    )
                    predictions.append(pred)
            
            # Prediction: Battery depletion
            if ctx.pc_battery:
                # Estimate time until 20% (assuming ~1% per hour usage)
                if ctx.pc_battery <= 30:
                    hours_left = (ctx.pc_battery - 20) / 1.0
                    pred = Prediction(
                        id=f"pred_battery_depletion_{datetime.utcnow().timestamp()}",
                        type=PredictionType.RESOURCE_DEPLETION,
                        description=f"PC battery will reach critical level in ~{hours_left:.1f} hours",
                        confidence=0.85,
                        timeframe=f"{hours_left:.1f} hours",
                        impact="medium",
                        evidence=[
                            f"Current battery: {ctx.pc_battery}%",
                            "Typical usage pattern: ~1%/hour"
                        ],
                        suggested_actions=[
                            "Remind to charge PC",
                            "Save work before battery dies",
                            "Find charging location"
                        ],
                        expires_at=(datetime.utcnow() + timedelta(hours=hours_left)).isoformat()
                    )
                    predictions.append(pred)
            
            # Prediction: Decision point
            if ctx.tasks_due_today > 3 and ctx.time_of_day == "morning":
                pred = Prediction(
                    id=f"pred_decision_point_{datetime.utcnow().timestamp()}",
                    type=PredictionType.DECISION,
                    description="Karthi will need to decide task priorities for today",
                    confidence=0.8,
                    timeframe="next hour",
                    impact="high",
                    evidence=[
                        f"{ctx.tasks_due_today} tasks due today",
                        "Morning is typical planning time",
                        "Psychological profile: conscientious decision-maker"
                    ],
                    suggested_actions=[
                        "Present prioritized task list",
                        "Suggest optimal schedule",
                        "Highlight deadline-sensitive tasks"
                    ],
                    expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
                )
                predictions.append(pred)
            
            # Prediction: Opportunity for deep work
            if ctx.time_of_day == "morning" and ctx.stress_level < 5 and not ctx.next_event:
                pred = Prediction(
                    id=f"pred_deep_work_opportunity_{datetime.utcnow().timestamp()}",
                    type=PredictionType.OPPORTUNITY,
                    description="Good opportunity for deep work session",
                    confidence=0.75,
                    timeframe="next 2 hours",
                    impact="medium",
                    evidence=[
                        "Morning time slot available",
                        "Low stress level",
                        "No immediate meetings",
                        "Psychological profile: values achievement and growth"
                    ],
                    suggested_actions=[
                        "Suggest deep work session",
                        "Block out time on calendar",
                        "Minimize notifications",
                        "Focus on high-impact task"
                    ],
                    expires_at=(datetime.utcnow() + timedelta(hours=2)).isoformat()
                )
                predictions.append(pred)
            
            # Prediction: End of day fatigue
            if ctx.time_of_day == "evening" and ctx.work_hours_today > 8:
                pred = Prediction(
                    id=f"pred_fatigue_{datetime.utcnow().timestamp()}",
                    type=PredictionType.EMOTIONAL_STATE,
                    description="Karthi likely experiencing fatigue after long work day",
                    confidence=0.85,
                    timeframe="now",
                    impact="medium",
                    evidence=[
                        f"Worked {ctx.work_hours_today} hours today",
                        "Evening time",
                        "Psychological profile: values balance (struggles with work-life balance)"
                    ],
                    suggested_actions=[
                        "Encourage ending work",
                        "Suggest relaxation activity",
                        "Celebrate day's achievements",
                        "Prepare for tomorrow"
                    ],
                    expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat()
                )
                predictions.append(pred)
            
            # Store predictions
            for pred in predictions:
                self.predictions[pred.id] = pred
            
            self._save_data()
            
            print(f"[PredictiveEngine] Generated {len(predictions)} predictions")
            return predictions
            
        except Exception as e:
            print(f"[PredictiveEngine] Error generating predictions: {e}")
            return []
    
    def record_outcome(self, prediction_id: str, outcome: str, success: bool):
        """
        Record the actual outcome of a prediction for learning.
        This is how LOVE improves its predictive accuracy over time.
        """
        try:
            if prediction_id in self.predictions:
                pred = self.predictions[prediction_id]
                pred.outcome = outcome
                
                # Record in history
                self.prediction_history.append({
                    "prediction_id": prediction_id,
                    "description": pred.description,
                    "confidence": pred.confidence,
                    "outcome": outcome,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Learn from outcome
                if success:
                    # Strengthen similar predictions
                    self._strengthen_pattern(pred)
                else:
                    # Weaken similar predictions
                    self._weaken_pattern(pred)
                
                self._save_data()
                
                print(f"[PredictiveEngine] Recorded outcome for {prediction_id}: {success}")
                
        except Exception as e:
            print(f"[PredictiveEngine] Error recording outcome: {e}")
    
    def _strengthen_pattern(self, prediction: Prediction):
        """Strengthen patterns that led to successful prediction"""
        # Find similar patterns and increase confidence
        for pattern in self.patterns:
            if prediction.description.lower() in pattern.description.lower():
                pattern.confidence = min(1.0, pattern.confidence + 0.05)
                pattern.frequency += 1
                pattern.last_observed = datetime.utcnow().isoformat()
    
    def _weaken_pattern(self, prediction: Prediction):
        """Weaken patterns that led to failed prediction"""
        for pattern in self.patterns:
            if prediction.description.lower() in pattern.description.lower():
                pattern.confidence = max(0.1, pattern.confidence - 0.1)
    
    def learn_pattern(self, context: Dict, behavior: str, outcome: str):
        """
        Learn a new pattern from observed behavior.
        """
        try:
            # Convert context to conditions
            conditions = []
            if context.get("time_of_day"):
                conditions.append(f"time_of_day={context['time_of_day']}")
            if context.get("stress_score"):
                conditions.append(f"stress_score={context['stress_score']}")
            if context.get("tasks_due_today"):
                conditions.append(f"tasks_due_today={context['tasks_due_today']}")
            
            pattern = Pattern(
                description=f"When {', '.join(conditions)}, Karthi tends to {behavior}",
                frequency=1,
                conditions=conditions,
                consequences=[outcome],
                confidence=0.3,  # Start low, increase with repetition
                last_observed=datetime.utcnow().isoformat()
            )
            
            self.patterns.append(pattern)
            self._save_data()
            
            print(f"[PredictiveEngine] Learned new pattern: {pattern.description}")
            
        except Exception as e:
            print(f"[PredictiveEngine] Error learning pattern: {e}")
    
    def get_active_predictions(self) -> List[Dict]:
        """Get all currently active (non-expired) predictions"""
        now = datetime.utcnow()
        active = []
        
        for pred_id, pred in self.predictions.items():
            if pred.expires_at:
                expires = datetime.fromisoformat(pred.expires_at)
                if expires > now:
                    active.append({
                        "id": pred.id,
                        "type": pred.type.value,
                        "description": pred.description,
                        "confidence": pred.confidence,
                        "timeframe": pred.timeframe,
                        "impact": pred.impact,
                        "evidence": pred.evidence,
                        "suggested_actions": pred.suggested_actions,
                        "expires_at": pred.expires_at
                    })
        
        # Sort by confidence and impact
        impact_priority = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        active.sort(key=lambda x: (x["confidence"], impact_priority.get(x["impact"], 0)), reverse=True)
        
        return active
    
    def get_prediction_accuracy(self) -> Dict:
        """Calculate prediction accuracy metrics"""
        if not self.prediction_history:
            return {"error": "No prediction history"}
        
        total = len(self.prediction_history)
        successful = sum(1 for h in self.prediction_history if h["success"])
        
        # Accuracy by type
        by_type = defaultdict(lambda: {"total": 0, "successful": 0})
        for h in self.prediction_history:
            pred = self.predictions.get(h["prediction_id"])
            if pred:
                by_type[pred.type.value]["total"] += 1
                if h["success"]:
                    by_type[pred.type.value]["successful"] += 1
        
        return {
            "overall_accuracy": successful / total if total > 0 else 0,
            "total_predictions": total,
            "successful_predictions": successful,
            "accuracy_by_type": {
                t: v["successful"] / v["total"] if v["total"] > 0 else 0
                for t, v in by_type.items()
            }
        }
    
    def anticipate_needs(self, context: Dict) -> List[Dict]:
        """
        Anticipate what Karthi will need in the near future.
        This is a key AGI capability - proactive assistance.
        Enhanced with LLM-based pattern recognition.
        """
        needs = []
        
        try:
            ctx = get_live_context()
            
            # Use LLM to analyze patterns and anticipate needs
            anticipation_prompt = f"""You are LOVE, an autonomous AI assistant helping Karthi.

CURRENT CONTEXT:
- Time: {datetime.utcnow().isoformat()}
- Active Project: {ctx.active_project or 'None'}
- Tasks Due Today: {ctx.tasks_due_today}
- Next Event: {ctx.next_event.get('title', 'None') if ctx.next_event else 'None'} ({ctx.next_event.get('minutes_away', 'N/A') if ctx.next_event else 'N/A'} minutes away)
- Stress Level: {ctx.stress_level}/10
- Energy Level: {ctx.energy_level}/10
- Time of Day: {ctx.time_of_day}
- PC Battery: {ctx.pc_battery}% if ctx.pc_battery else 'Unknown'
- Phone Battery: {ctx.phone_battery}% if ctx.phone_battery else 'Unknown'
- Active App: {ctx.active_app or 'None'}

KNOWN PATTERNS:
{self._get_pattern_summary()}

Analyze this context and predict what Karthi will need in the next 30-60 minutes.
Consider:
- Information needs (meeting prep, project context)
- Decision support needs (task prioritization)
- Resource needs (charging, tools, access)
- Emotional support needs (stress relief, encouragement)
- Learning needs (context refresh, skill development)

Return a JSON response with this structure:
{{
  "needs": [
    {{
      "type": "information|decision_support|resource|emotional_support|learning",
      "description": "What Karthi will need",
      "urgency": "high|medium|low",
      "reason": "Why this need is likely",
      "suggested_action": "What LOVE could do proactively"
    }}
  ]
}}"""

            from core.agent import chat
            response = chat(anticipation_prompt, mode="reasoning")
            
            plan_text = response.get("response", "")
            import re
            json_match = re.search(r'\{[\s\S]*\}', plan_text)
            
            if json_match:
                need_data = json.loads(json_match.group())
                for need_info in need_data.get("needs", []):
                    needs.append({
                        "type": need_info.get("type", "information"),
                        "description": need_info.get("description", ""),
                        "urgency": need_info.get("urgency", "medium"),
                        "reason": need_info.get("reason", ""),
                        "suggested_action": need_info.get("suggested_action", "")
                    })
            else:
                # Fallback to rule-based anticipation
                needs = self._fallback_anticipate_needs(ctx)
            
            # Sort by urgency
            urgency_priority = {"high": 3, "medium": 2, "low": 1}
            needs.sort(key=lambda x: urgency_priority.get(x.get("urgency", "low"), 0), reverse=True)
            
            return needs
            
        except Exception as e:
            print(f"[PredictiveEngine] Error anticipating needs: {e}")
            ctx = get_live_context()
            return self._fallback_anticipate_needs(ctx)
    
    def _get_pattern_summary(self) -> str:
        """Get a summary of learned patterns for LLM context"""
        if not self.patterns:
            return "No patterns learned yet."
        
        # Return top 5 patterns by confidence
        top_patterns = sorted(self.patterns, key=lambda p: p.confidence, reverse=True)[:5]
        pattern_summary = "\n".join([
            f"- {p.description} (confidence: {p.confidence:.2f}, frequency: {p.frequency})"
            for p in top_patterns
        ])
        return pattern_summary
    
    def _fallback_anticipate_needs(self, ctx) -> List[Dict]:
        """Fallback rule-based need anticipation if LLM fails."""
        needs = []
        
        # Information needs
        if ctx.next_event and ctx.next_event.get('minutes_away', 999) <= 15:
            needs.append({
                "type": "information",
                "description": "Meeting details and context",
                "urgency": "high",
                "reason": f"Meeting '{ctx.next_event.get('title')}' starting soon",
                "suggested_action": "Prepare meeting summary and talking points"
            })
        
        # Decision support needs
        if ctx.tasks_due_today > 3:
            needs.append({
                "type": "decision_support",
                "description": "Task prioritization",
                "urgency": "medium",
                "reason": "Multiple competing priorities",
                "suggested_action": "Suggest optimal task ordering"
            })
        
        # Resource needs
        if ctx.pc_battery and ctx.pc_battery < 30:
            needs.append({
                "type": "resource",
                "description": "Charging access",
                "urgency": "medium",
                "reason": "PC battery running low",
                "suggested_action": "Remind to charge PC"
            })
        
        # Emotional support needs
        if ctx.stress_level > 7:
            needs.append({
                "type": "emotional_support",
                "description": "Stress relief",
                "urgency": "high",
                "reason": "High stress level detected",
                "suggested_action": "Suggest stress relief activities"
            })
        
        # Learning needs
        if ctx.active_project and ctx.time_of_day == "morning":
            needs.append({
                "type": "learning",
                "description": "Project context refresh",
                "urgency": "low",
                "reason": "Morning routine - good time to refresh context",
                "suggested_action": "Provide project summary and recent changes"
            })
        
        return needs


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_predictive_engine() -> PredictiveEngine:
    """Get the singleton predictive engine instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = PredictiveEngine()
    return _instance
