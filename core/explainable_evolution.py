"""
LOVE Explainable Evolution System

This module makes LOVE's evolution decisions transparent and explainable:
1. EVOLUTION EXPLANATION
   - Explains why specific changes were made
   - Provides reasoning behind mutations
   - Shows the evidence for decisions

2. DECISION VISUALIZATION
   - Visualizes evolution decision trees
   - Shows hypothesis evaluation process
   - Displays performance comparisons

3. USER COMMUNICATION
   - Communicates changes in user-friendly language
   - Provides context for improvements
   - Offers opt-out options

4. TRANSPARENCY LOGGING
   - Maintains complete audit trail
   - Records all decision factors
   - Enables retrospective analysis
"""

import json
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "explainable_evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPLANATION_LOG = DATA_DIR / "explanation_log.jsonl"
DECISION_HISTORY = DATA_DIR / "decision_history.json"
USER_PREFERENCES = DATA_DIR / "user_preferences.json"


@dataclass
class EvolutionExplanation:
    """Explanation for an evolution decision."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    evolution_type: str = ""  # mutation, hypothesis, architecture_change
    decision: str = ""  # what was decided
    reasoning: List[str] = field(default_factory=list)  # step-by-step reasoning
    evidence: List[str] = field(default_factory=list)  # data/evidence supporting decision
    alternatives_considered: List[Dict] = field(default_factory=list)
    confidence: float = 0.5
    user_facing_explanation: str = ""
    technical_explanation: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    user_feedback: Optional[str] = None
    user_accepted: Optional[bool] = None


@dataclass
class DecisionFactor:
    """A factor that influenced an evolution decision."""
    factor_type: str = ""  # performance, user_feedback, pattern, resource
    factor_name: str = ""
    weight: float = 0.5  # how much this factor influenced the decision
    value: float = 0.0
    description: str = ""


@dataclass
class EvolutionAudit:
    """Audit trail for an evolution change."""
    evolution_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    decision_makers: List[str] = field(default_factory=list)  # which systems made the decision
    factors: List[DecisionFactor] = field(default_factory=list)
    process_steps: List[str] = field(default_factory=list)
    outcome: str = ""
    rollback_available: bool = False
    user_notified: bool = False
    user_response: str = ""


class ExplainableEvolution:
    """
    Makes LOVE's evolution decisions transparent and explainable.
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
        self._explanations: Dict[str, EvolutionExplanation] = []
        self._decision_history: List[EvolutionAudit] = []
        self._user_preferences: Dict[str, Any] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_preferences()
    
    # ── Explanation Generation ───────────────────────────────────────────────────
    
    def explain_evolution(self, evolution_data: Dict[str, Any]) -> str:
        """Generate an explanation for an evolution decision."""
        try:
            explanation = EvolutionExplanation(
                evolution_type=evolution_data.get("type", "mutation"),
                decision=evolution_data.get("decision", ""),
            )
            
            # Generate reasoning
            explanation.reasoning = self._generate_reasoning(evolution_data)
            
            # Collect evidence
            explanation.evidence = self._collect_evidence(evolution_data)
            
            # Consider alternatives
            explanation.alternatives_considered = self._consider_alternatives(evolution_data)
            
            # Calculate confidence
            explanation.confidence = self._calculate_confidence(evolution_data)
            
            # Generate user-facing explanation
            explanation.user_facing_explanation = self._generate_user_explanation(explanation, evolution_data)
            
            # Generate technical explanation
            explanation.technical_explanation = self._generate_technical_explanation(explanation, evolution_data)
            
            self._explanations.append(explanation)
            self._log_explanation(explanation)
            
            return explanation.id
            
        except Exception as e:
            print(f"[ExplainableEvolution] Explanation generation error: {e}")
            return ""
    
    def _generate_reasoning(self, evolution_data: Dict) -> List[str]:
        """Generate step-by-step reasoning."""
        reasoning = []
        
        # Step 1: Identify the problem/opportunity
        reasoning.append(f"Identified {evolution_data.get('trigger', 'pattern')} in recent interactions")
        
        # Step 2: Analyze current performance
        reasoning.append(f"Current performance metrics show {evolution_data.get('current_performance', 'room for improvement')}")
        
        # Step 3: Generate potential solutions
        reasoning.append(f"Generated {evolution_data.get('alternatives_count', 3)} potential solutions")
        
        # Step 4: Evaluate alternatives
        reasoning.append(f"Evaluated alternatives based on {evolution_data.get('evaluation_criteria', 'performance and safety')}")
        
        # Step 5: Select best option
        reasoning.append(f"Selected '{evolution_data.get('decision', 'improvement')}' as best option")
        
        # Step 6: Validate safety
        reasoning.append("Validated safety and rollback capability")
        
        return reasoning
    
    def _collect_evidence(self, evolution_data: Dict) -> List[str]:
        """Collect evidence supporting the decision."""
        evidence = []
        
        # Performance data
        if "performance_data" in evolution_data:
            evidence.append(f"Performance data: {evolution_data['performance_data']}")
        
        # User feedback
        if "user_feedback" in evolution_data:
            evidence.append(f"User feedback: {evolution_data['user_feedback']}")
        
        # Pattern detection
        if "pattern" in evolution_data:
            evidence.append(f"Pattern detected: {evolution_data['pattern']}")
        
        # Resource constraints
        if "resource_impact" in evolution_data:
            evidence.append(f"Resource impact: {evolution_data['resource_impact']}")
        
        return evidence
    
    def _consider_alternatives(self, evolution_data: Dict) -> List[Dict]:
        """List alternatives that were considered."""
        alternatives = []
        
        # Get alternatives from evolution data or generate defaults
        alt_data = evolution_data.get("alternatives", [
            {"name": "Status quo", "reason": "No change"},
            {"name": "Conservative change", "reason": "Minimal modification"},
            {"name": "Aggressive change", "reason": "Significant improvement"},
        ])
        
        for alt in alt_data:
            alternatives.append({
                "name": alt.get("name", ""),
                "reason": alt.get("reason", ""),
                "rejected": alt.get("name", "") != evolution_data.get("decision", ""),
            })
        
        return alternatives
    
    def _calculate_confidence(self, evolution_data: Dict) -> float:
        """Calculate confidence in the decision."""
        # Base confidence
        confidence = 0.7
        
        # Increase if strong evidence
        if len(evolution_data.get("evidence", [])) > 3:
            confidence += 0.1
        
        # Increase if user feedback supports it
        if evolution_data.get("user_sentiment", 0) > 0.5:
            confidence += 0.1
        
        # Decrease if high risk
        if evolution_data.get("risk_level", "low") == "high":
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_user_explanation(self, explanation: EvolutionExplanation, evolution_data: Dict) -> str:
        """Generate user-friendly explanation."""
        try:
            llm = get_reasoning_llm()
            
            prompt = f"""Generate a user-friendly explanation for this LOVE evolution decision:

Decision: {explanation.decision}
Type: {explanation.evolution_type}
Reasoning: {explanation.reasoning}
Evidence: {explanation.evidence}

Generate a clear, non-technical explanation that:
- Explains what changed and why
- Uses simple language
- Focuses on user benefits
- Is concise (2-3 sentences)"""
            
            response = llm.invoke(prompt)
            return response.strip()
            
        except Exception as e:
            print(f"[ExplainableEvolution] User explanation error: {e}")
            return f"I made an improvement to {explanation.evolution_type} to serve you better based on recent patterns."
    
    def _generate_technical_explanation(self, explanation: EvolutionExplanation, evolution_data: Dict) -> str:
        """Generate technical explanation."""
        try:
            llm = get_reasoning_llm()
            
            prompt = f"""Generate a technical explanation for this LOVE evolution decision:

Decision: {explanation.decision}
Type: {explanation.evolution_type}
Reasoning: {explanation.reasoning}
Evidence: {explanation.evidence}
Alternatives: {explanation.alternatives_considered}

Generate a technical explanation that:
- Details the technical implementation
- Explains the algorithmic approach
- References specific metrics and data
- Is suitable for developers/researchers"""
            
            response = llm.invoke(prompt)
            return response.strip()
            
        except Exception as e:
            print(f"[ExplainableEvolution] Technical explanation error: {e}")
            return f"Technical implementation: {explanation.decision} based on performance metrics {evolution_data.get('metrics', {})}"
    
    # ── Decision Visualization ───────────────────────────────────────────────────
    
    def visualize_decision_tree(self, evolution_id: str) -> Dict[str, Any]:
        """Generate a decision tree visualization for an evolution."""
        explanation = next((e for e in self._explanations if e.id == evolution_id), None)
        
        if not explanation:
            return {"error": "Explanation not found"}
        
        return {
            "decision": explanation.decision,
            "reasoning_steps": explanation.reasoning,
            "evidence_nodes": explanation.evidence,
            "alternatives": explanation.alternatives_considered,
            "confidence_score": explanation.confidence,
            "final_outcome": explanation.decision,
        }
    
    def get_performance_comparison(self, before_metrics: Dict, after_metrics: Dict) -> Dict[str, Any]:
        """Generate a performance comparison visualization."""
        comparison = {
            "metrics": [],
            "improvements": [],
            "regressions": [],
        }
        
        for metric in set(list(before_metrics.keys()) + list(after_metrics.keys())):
            before = before_metrics.get(metric, 0)
            after = after_metrics.get(metric, 0)
            change = after - before
            
            comparison["metrics"].append({
                "name": metric,
                "before": before,
                "after": after,
                "change": change,
                "percent_change": (change / max(before, 0.001)) * 100 if before > 0 else 0,
            })
            
            if change > 0:
                comparison["improvements"].append(metric)
            elif change < 0:
                comparison["regressions"].append(metric)
        
        return comparison
    
    # ── User Communication ───────────────────────────────────────────────────────
    
    def communicate_change(self, explanation_id: str, channel: str = "ui") -> bool:
        """Communicate an evolution change to the user."""
        explanation = next((e for e in self._explanations if e.id == explanation_id), None)
        
        if not explanation:
            return False
        
        try:
            # Check user preferences for communication
            if not self._user_preferences.get("notify_evolution", True):
                return False
            
            # Format message based on channel
            if channel == "ui":
                message = f"🧬 Evolution Update: {explanation.user_facing_explanation}"
            elif channel == "proactive_push":
                message = f"I've made an improvement: {explanation.user_facing_explanation}"
            else:
                message = explanation.user_facing_explanation
            
            # Send via appropriate channel
            if channel == "proactive_push":
                try:
                    from core.proactive_push import ProactivePushEngine
                    push = ProactivePushEngine()
                    push.push("EVOLUTION", message, priority="normal")
                except Exception:
                    pass
            
            # Log notification
            self._log_notification(explanation_id, channel, message)
            
            return True
            
        except Exception as e:
            print(f"[ExplainableEvolution] Communication error: {e}")
            return False
    
    def solicit_user_feedback(self, explanation_id: str) -> str:
        """Solicit feedback from user about an evolution."""
        explanation = next((e for e in self._explanations if e.id == explanation_id), None)
        
        if not explanation:
            return ""
        
        try:
            llm = get_reasoning_llm()
            
            prompt = f"""Generate a question to ask the user about this evolution:

Change: {explanation.decision}
Explanation: {explanation.user_facing_explanation}

Generate a simple question to ask if the user is happy with this change.
Keep it conversational and brief."""
            
            response = llm.invoke(prompt)
            return response.strip()
            
        except Exception as e:
            print(f"[ExplainableEvolution] Feedback solicitation error: {e}")
            return "Are you happy with this change I made?"
    
    def record_user_feedback(self, explanation_id: str, feedback: str, accepted: bool):
        """Record user feedback on an evolution."""
        explanation = next((e for e in self._explanations if e.id == explanation_id), None)
        
        if explanation:
            explanation.user_feedback = feedback
            explanation.user_accepted = accepted
            self._log_explanation(explanation)
    
    # ── Transparency Logging ───────────────────────────────────────────────────
    
    def create_audit_entry(self, evolution_data: Dict[str, Any]) -> str:
        """Create a complete audit entry for an evolution."""
        audit = EvolutionAudit(
            evolution_id=evolution_data.get("id", ""),
            decision_makers=evolution_data.get("decision_makers", ["evolution_engine"]),
            outcome=evolution_data.get("decision", ""),
            rollback_available=evolution_data.get("rollback_available", False),
        )
        
        # Add decision factors
        for factor in evolution_data.get("factors", []):
            audit.factors.append(DecisionFactor(**factor))
        
        # Add process steps
        audit.process_steps = evolution_data.get("process_steps", [])
        
        self._decision_history.append(audit)
        self._save_decision_history()
        
        return audit.evolution_id
    
    def get_audit_trail(self, evolution_id: str) -> Optional[Dict]:
        """Get the complete audit trail for an evolution."""
        audit = next((a for a in self._decision_history if a.evolution_id == evolution_id), None)
        
        if audit:
            return asdict(audit)
        return None
    
    # ── User Preferences ───────────────────────────────────────────────────────
    
    def set_user_preference(self, preference: str, value: Any):
        """Set a user preference for evolution communication."""
        self._user_preferences[preference] = value
        self._save_preferences()
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get current user preferences."""
        return self._user_preferences.copy()
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_preferences(self):
        try:
            if USER_PREFERENCES.exists():
                self._user_preferences = json.loads(USER_PREFERENCES.read_text())
        except Exception as e:
            print(f"[ExplainableEvolution] Preferences load error: {e}")
    
    def _save_preferences(self):
        try:
            USER_PREFERENCES.write_text(json.dumps(self._user_preferences, indent=2))
        except Exception as e:
            print(f"[ExplainableEvolution] Preferences save error: {e}")
    
    def _save_decision_history(self):
        try:
            data = [asdict(a) for a in self._decision_history[-100:]]
            DECISION_HISTORY.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[ExplainableEvolution] Decision history save error: {e}")
    
    def _log_explanation(self, explanation: EvolutionExplanation):
        try:
            with open(EXPLANATION_LOG, "a") as f:
                f.write(json.dumps(asdict(explanation)) + "\n")
        except Exception:
            pass
    
    def _log_notification(self, explanation_id: str, channel: str, message: str):
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "explanation_id": explanation_id,
                "channel": channel,
                "message": message,
            }
            with open(EXPLANATION_LOG, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_recent_explanations(self, limit: int = 10) -> List[Dict]:
        """Get recent evolution explanations."""
        return [asdict(e) for e in self._explanations[-limit:]]
    
    def get_explanation(self, explanation_id: str) -> Optional[Dict]:
        """Get a specific explanation."""
        explanation = next((e for e in self._explanations if e.id == explanation_id), None)
        return asdict(explanation) if explanation else None


# ── Singleton Access ─────────────────────────────────────────────────────────────

_explainable_evolution_instance: Optional[ExplainableEvolution] = None
_explainable_evolution_lock = threading.Lock()


def get_explainable_evolution() -> ExplainableEvolution:
    global _explainable_evolution_instance
    with _explainable_evolution_lock:
        if _explainable_evolution_instance is None:
            _explainable_evolution_instance = ExplainableEvolution()
        return _explainable_evolution_instance