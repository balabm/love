"""
LOVE User Feedback Evolutionary Pressure System

This module creates evolutionary pressure directly from user feedback:
1. FEEDBACK COLLECTION
   - Collects explicit user feedback
   - Infers implicit feedback from interactions
   - Tracks sentiment and satisfaction

2. PRESSURE CALCULATION
   - Converts feedback into evolutionary pressure
   - Identifies areas needing improvement
   - Prioritizes based on user sentiment

3. ADAPTIVE RESPONSE
   - Adjusts evolution based on feedback intensity
   - Triggers urgent evolution for critical issues
   - Calms evolution when user is satisfied

4. FEEDBACK LOOPS
   - Creates virtuous cycles of improvement
   - Learns from feedback patterns
   - Adapts to user communication style
"""

import json
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "feedback_evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FEEDBACK_LOG = DATA_DIR / "feedback_log.jsonl"
PRESSURE_STATE = DATA_DIR / "pressure_state.json"
FEEDBACK_PATTERNS = DATA_DIR / "feedback_patterns.json"


@dataclass
class UserFeedback:
    """User feedback on LOVE's performance."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    feedback_type: str = ""  # explicit, implicit, inferred
    category: str = ""  # accuracy, helpfulness, tone, speed, proactivity
    sentiment: float = 0.5  # -1.0 to 1.0 (negative to positive)
    intensity: float = 0.5  # 0.0 to 1.0 (how strong the feedback is)
    context: str = ""
    raw_feedback: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    addressed: bool = False
    evolution_triggered: str = ""  # ID of evolution triggered


@dataclass
class EvolutionaryPressure:
    """Pressure for evolution based on feedback."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    source_category: str = ""
    pressure_level: float = 0.5  # 0.0 to 1.0
    urgency: str = "normal"  # low, normal, high, critical
    source_feedback_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    evolution_triggered: bool = False
    evolution_id: str = ""


@dataclass
class FeedbackPattern:
    """A pattern in user feedback."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    pattern_type: str = ""
    description: str = ""
    frequency: int = 0
    avg_sentiment: float = 0.5
    last_observed: str = field(default_factory=lambda: datetime.now().isoformat())


class FeedbackEvolutionPressure:
    """
    Creates evolutionary pressure from user feedback.
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
        self._feedback_history: List[UserFeedback] = []
        self._pressures: Dict[str, EvolutionaryPressure] = {}
        self._patterns: Dict[str, FeedbackPattern] = {}
        self._category_pressure: Dict[str, float] = defaultdict(float)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_state()
    
    # ── Feedback Collection ───────────────────────────────────────────────────────
    
    def collect_explicit_feedback(self, category: str, sentiment: float, 
                                 context: str, raw_feedback: str = "") -> str:
        """Collect explicit user feedback."""
        feedback = UserFeedback(
            feedback_type="explicit",
            category=category,
            sentiment=sentiment,
            intensity=abs(sentiment),  # Intensity based on sentiment strength
            context=context,
            raw_feedback=raw_feedback,
        )
        
        self._feedback_history.append(feedback)
        self._update_category_pressure(category, sentiment)
        self._log_feedback(feedback)
        self._save_state()
        
        # Check if this should trigger urgent evolution
        if abs(sentiment) > 0.8:
            self._trigger_urgent_evolution(category, sentiment)
        
        return feedback.id
    
    def infer_implicit_feedback(self, interaction: Dict[str, Any]) -> str:
        """Infer feedback from interaction patterns."""
        try:
            # Analyze interaction for implicit feedback signals
            sentiment = 0.0
            category = "general"
            intensity = 0.3
            
            # Check for correction patterns
            user_message = interaction.get("user_message", "").lower()
            if any(word in user_message for word in ["wrong", "incorrect", "not that", "no"]):
                sentiment = -0.5
                category = "accuracy"
                intensity = 0.6
            elif any(word in user_message for word in ["thanks", "perfect", "great", "good"]):
                sentiment = 0.7
                category = "helpfulness"
                intensity = 0.5
            
            # Check for response length (very short might indicate dissatisfaction)
            love_response = interaction.get("love_response", "")
            if len(love_response) < 50 and len(user_message) > 20:
                sentiment -= 0.2
                category = "helpfulness"
            
            # Only record if there's significant sentiment
            if abs(sentiment) > 0.2:
                feedback = UserFeedback(
                    feedback_type="implicit",
                    category=category,
                    sentiment=sentiment,
                    intensity=intensity,
                    context=f"Inferred from interaction: {user_message[:50]}...",
                    raw_feedback=love_response[:100],
                )
                
                self._feedback_history.append(feedback)
                self._update_category_pressure(category, sentiment)
                self._log_feedback(feedback)
                self._save_state()
                
                return feedback.id
            
            return ""
            
        except Exception as e:
            print(f"[FeedbackPressure] Implicit feedback inference error: {e}")
            return ""
    
    def analyze_sentiment_from_text(self, text: str) -> Tuple[float, str]:
        """Analyze sentiment from text using LLM."""
        try:
            llm = get_reasoning_llm()
            
            prompt = f"""Analyze the sentiment of this user feedback:
"{text}"

Return a JSON object with:
- sentiment: float from -1.0 (very negative) to 1.0 (very positive)
- category: one of [accuracy, helpfulness, tone, speed, proactivity, general]
- intensity: float from 0.0 to 1.0 (how strong the sentiment is)"""
            
            response = llm.invoke(prompt)
            
            try:
                data = json.loads(response)
                return data.get("sentiment", 0.0), data.get("category", "general")
            except json.JSONDecodeError:
                # Fallback to simple analysis
                text_lower = text.lower()
                if any(word in text_lower for word in ["bad", "wrong", "hate", "terrible"]):
                    return -0.7, "general"
                elif any(word in text_lower for word in ["good", "great", "love", "excellent"]):
                    return 0.7, "general"
                else:
                    return 0.0, "general"
                    
        except Exception as e:
            print(f"[FeedbackPressure] Sentiment analysis error: {e}")
            return 0.0, "general"
    
    # ── Pressure Calculation ───────────────────────────────────────────────────
    
    def _update_category_pressure(self, category: str, sentiment: float):
        """Update evolutionary pressure for a category."""
        # Negative sentiment increases pressure
        pressure_adjustment = -sentiment * 0.1
        self._category_pressure[category] = max(0.0, min(1.0, 
            self._category_pressure[category] + pressure_adjustment))
        
        # Check if pressure exceeds threshold
        if self._category_pressure[category] > 0.7:
            self._create_pressure(category, self._category_pressure[category])
    
    def _create_pressure(self, category: str, level: float):
        """Create an evolutionary pressure entry."""
        # Check if recent pressure already exists for this category
        recent_pressures = [
            p for p in self._pressures.values()
            if p.source_category == category and 
            (datetime.now() - datetime.fromisoformat(p.created_at)).total_seconds() < 3600
        ]
        
        if recent_pressures:
            # Update existing pressure
            existing = recent_pressures[0]
            existing.pressure_level = max(existing.pressure_level, level)
            if level > 0.8:
                existing.urgency = "high"
            if level > 0.9:
                existing.urgency = "critical"
        else:
            # Create new pressure
            urgency = "normal"
            if level > 0.7:
                urgency = "high"
            if level > 0.9:
                urgency = "critical"
            
            pressure = EvolutionaryPressure(
                source_category=category,
                pressure_level=level,
                urgency=urgency,
            )
            
            self._pressures[pressure.id] = pressure
    
    def get_pressure_summary(self) -> Dict[str, Any]:
        """Get summary of current evolutionary pressures."""
        return {
            "category_pressures": dict(self._category_pressure),
            "active_pressures": [
                {
                    "id": p.id,
                    "category": p.source_category,
                    "level": p.pressure_level,
                    "urgency": p.urgency,
                }
                for p in self._pressures.values()
                if not p.evolution_triggered
            ],
            "total_feedback": len(self._feedback_history),
            "avg_sentiment": sum(f.sentiment for f in self._feedback_history[-100:]) / max(1, len(self._feedback_history[-100:])),
        }
    
    # ── Urgent Evolution Triggering ────────────────────────────────────────────
    
    def _trigger_urgent_evolution(self, category: str, sentiment: float):
        """Trigger urgent evolution for critical feedback."""
        try:
            from core.evolution_integration import get_evolution_integration
            integration = get_evolution_integration()
            
            # Trigger manual evolution cycle
            integration.trigger_manual_cycle()
            
            # Log the trigger
            print(f"[FeedbackPressure] Urgent evolution triggered for {category} (sentiment: {sentiment})")
            
        except Exception as e:
            print(f"[FeedbackPressure] Urgent evolution trigger error: {e}")
    
    # ── Pattern Detection ───────────────────────────────────────────────────────
    
    def detect_feedback_patterns(self) -> List[FeedbackPattern]:
        """Detect patterns in user feedback."""
        new_patterns = []
        
        if len(self._feedback_history) < 10:
            return new_patterns
        
        recent = self._feedback_history[-50:]
        
        # Pattern: Consistently negative feedback on accuracy
        accuracy_feedback = [f for f in recent if f.category == "accuracy"]
        if len(accuracy_feedback) >= 5:
            avg_sentiment = sum(f.sentiment for f in accuracy_feedback) / len(accuracy_feedback)
            if avg_sentiment < -0.3:
                pattern = FeedbackPattern(
                    pattern_type="negative_accuracy",
                    description="Consistently negative feedback on accuracy",
                    frequency=len(accuracy_feedback),
                    avg_sentiment=avg_sentiment,
                )
                if pattern.id not in self._patterns:
                    self._patterns[pattern.id] = pattern
                    new_patterns.append(pattern)
        
        # Pattern: Consistently positive feedback on helpfulness
        helpfulness_feedback = [f for f in recent if f.category == "helpfulness"]
        if len(helpfulness_feedback) >= 5:
            avg_sentiment = sum(f.sentiment for f in helpfulness_feedback) / len(helpfulness_feedback)
            if avg_sentiment > 0.6:
                pattern = FeedbackPattern(
                    pattern_type="positive_helpfulness",
                    description="Consistently positive feedback on helpfulness",
                    frequency=len(helpfulness_feedback),
                    avg_sentiment=avg_sentiment,
                )
                if pattern.id not in self._patterns:
                    self._patterns[pattern.id] = pattern
                    new_patterns.append(pattern)
        
        if new_patterns:
            self._save_state()
        
        return new_patterns
    
    # ── Adaptive Response ───────────────────────────────────────────────────────
    
    def get_adaptive_response_strategy(self) -> Dict[str, Any]:
        """Get adaptive response strategy based on feedback."""
        strategy = {
            "tone": "normal",
            "verbosity": "medium",
            "proactivity": "balanced",
            "confidence": "moderate",
        }
        
        if len(self._feedback_history) < 10:
            return strategy
        
        recent = self._feedback_history[-20:]
        avg_sentiment = sum(f.sentiment for f in recent) / len(recent)
        
        # Adjust based on overall sentiment
        if avg_sentiment < -0.3:
            # User is unhappy - be more cautious
            strategy["tone"] = "humble"
            strategy["confidence"] = "low"
            strategy["proactivity"] = "reduced"
        elif avg_sentiment > 0.5:
            # User is happy - can be more confident
            strategy["tone"] = "confident"
            strategy["confidence"] = "high"
            strategy["proactivity"] = "increased"
        
        # Check for specific category patterns
        tone_feedback = [f for f in recent if f.category == "tone"]
        if tone_feedback:
            avg_tone_sentiment = sum(f.sentiment for f in tone_feedback) / len(tone_feedback)
            if avg_tone_sentiment < -0.2:
                strategy["tone"] = "more_casual"
            elif avg_tone_sentiment > 0.4:
                strategy["tone"] = "maintain"
        
        return strategy
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        try:
            if PRESSURE_STATE.exists():
                data = json.loads(PRESSURE_STATE.read_text())
                self._category_pressure = defaultdict(float, data.get("category_pressure", {}))
                for pid, pd in data.get("pressures", {}).items():
                    self._pressures[pid] = EvolutionaryPressure(**pd)
            if FEEDBACK_PATTERNS.exists():
                data = json.loads(FEEDBACK_PATTERNS.read_text())
                for pid, pd in data.get("patterns", {}).items():
                    self._patterns[pid] = FeedbackPattern(**pd)
        except Exception as e:
            print(f"[FeedbackPressure] State load error: {e}")
    
    def _save_state(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "category_pressure": dict(self._category_pressure),
                "pressures": {pid: asdict(p) for pid, p in self._pressures.items()},
            }
            PRESSURE_STATE.write_text(json.dumps(data, indent=2, default=str))
            
            pattern_data = {
                "last_updated": datetime.now().isoformat(),
                "patterns": {pid: asdict(p) for pid, p in self._patterns.items()},
            }
            FEEDBACK_PATTERNS.write_text(json.dumps(pattern_data, indent=2, default=str))
        except Exception as e:
            print(f"[FeedbackPressure] State save error: {e}")
    
    def _log_feedback(self, feedback: UserFeedback):
        try:
            with open(FEEDBACK_LOG, "a") as f:
                f.write(json.dumps(asdict(feedback)) + "\n")
        except Exception:
            pass
    
    # ── Main Loop ─────────────────────────────────────────────────────────────────
    
    def start(self):
        """Start the feedback pressure background loop."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-FeedbackPressure"
        )
        self._thread.start()
        print("[FeedbackPressure] Started — user feedback evolutionary pressure active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(180)  # Let other systems initialize
        
        while self._running:
            try:
                # Detect feedback patterns
                self.detect_feedback_patterns()
                
                # Decay old pressures (reduce pressure over time if no new feedback)
                for category in list(self._category_pressure.keys()):
                    self._category_pressure[category] = max(0.0, 
                        self._category_pressure[category] * 0.95)  # 5% decay per cycle
                
                # Clean up old pressures
                cutoff = datetime.now() - timedelta(hours=24)
                to_remove = [
                    pid for pid, p in self._pressures.items()
                    if datetime.fromisoformat(p.created_at) < cutoff and not p.evolution_triggered
                ]
                for pid in to_remove:
                    del self._pressures[pid]
                
                if to_remove:
                    self._save_state()
                
            except Exception as e:
                print(f"[FeedbackPressure] Loop error: {e}")
            
            time.sleep(600)  # Run every 10 minutes
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_recent_feedback(self, limit: int = 20) -> List[Dict]:
        """Get recent feedback entries."""
        return [asdict(f) for f in self._feedback_history[-limit:]]
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of feedback statistics."""
        if not self._feedback_history:
            return {"total": 0, "avg_sentiment": 0.0}
        
        recent = self._feedback_history[-100:]
        
        return {
            "total": len(self._feedback_history),
            "recent": len(recent),
            "avg_sentiment": sum(f.sentiment for f in recent) / len(recent),
            "by_category": {
                cat: sum(1 for f in recent if f.category == cat)
                for cat in set(f.category for f in recent)
            },
            "by_type": {
                ftype: sum(1 for f in recent if f.feedback_type == ftype)
                for ftype in set(f.feedback_type for f in recent)
            },
        }


# ── Singleton Access ─────────────────────────────────────────────────────────────

_feedback_pressure_instance: Optional[FeedbackEvolutionPressure] = None
_feedback_pressure_lock = threading.Lock()


def get_feedback_evolution_pressure() -> FeedbackEvolutionPressure:
    global _feedback_pressure_instance
    with _feedback_pressure_lock:
        if _feedback_pressure_instance is None:
            _feedback_pressure_instance = FeedbackEvolutionPressure()
        return _feedback_pressure_instance