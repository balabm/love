"""
Cross-Domain Reasoning Engine for LOVE
Enables reasoning across different domains (work, personal, health, relationships, etc.).
This is a key AGI capability - understanding connections between different areas of life.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict
import statistics

from core.settings import get_settings
from core.context_engine import get_live_context
from core.psychological_model import get_psychological_model
from core.world_model import get_world_model

SETTINGS = get_settings()


class Domain(Enum):
    """Life domains that LOVE reasons about"""
    WORK = "work"
    HEALTH = "health"
    RELATIONSHIPS = "relationships"
    FINANCE = "finance"
    LEARNING = "learning"
    PERSONAL_GROWTH = "personal_growth"
    RECREATION = "recreation"
    SPIRITUAL = "spiritual"


class RelationshipType(Enum):
    """Types of relationships between domains"""
    SUPPORTS = "supports"  # One domain supports another
    CONFLICTS_WITH = "conflicts_with"  # Domains conflict
    DEPENDS_ON = "depends_on"  # One domain depends on another
    INFLUENCES = "influences"  # One domain influences another
    CORRELATED_WITH = "correlated_with"  # Statistical correlation
    CAUSES = "causes"  # Causal relationship


@dataclass
class DomainConnection:
    """A relationship between two domains"""
    domain1: Domain
    domain2: Domain
    relationship_type: RelationshipType
    strength: float  # 0-1
    description: str
    evidence: List[str] = field(default_factory=list)
    last_observed: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class CrossDomainInsight:
    """An insight that spans multiple domains"""
    id: str
    title: str
    description: str
    involved_domains: List[Domain]
    confidence: float
    implications: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class DomainState:
    """Current state of a domain"""
    domain: Domain
    metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "neutral"  # thriving, stable, declining, critical
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    active_goals: List[str] = field(default_factory=list)


class CrossDomainReasoningEngine:
    """
    Cross-domain reasoning engine.
    Understands connections between different areas of life and provides holistic insights.
    """
    
    def __init__(self):
        self.domain_connections: List[DomainConnection] = []
        self.domain_states: Dict[Domain, DomainState] = {}
        self.insights: List[CrossDomainInsight] = []
        self.lock = threading.Lock()
        self._load_data()
        self._initialize_domain_connections()
        self._initialize_domain_states()
        self.psych_model = get_psychological_model()
        self.world_model = get_world_model()
    
    def _initialize_domain_connections(self):
        """Initialize known connections between domains"""
        if not self.domain_connections:
            # Work-Health connections
            self.domain_connections.append(DomainConnection(
                domain1=Domain.WORK,
                domain2=Domain.HEALTH,
                relationship_type=RelationshipType.CONFLICTS_WITH,
                strength=0.7,
                description="Excessive work conflicts with health maintenance",
                evidence=["Long work hours reduce sleep", "Stress from work affects physical health"]
            ))
            
            self.domain_connections.append(DomainConnection(
                domain1=Domain.WORK,
                domain2=Domain.HEALTH,
                relationship_type=RelationshipType.INFLUENCES,
                strength=0.5,
                description="Work satisfaction influences mental health",
                evidence=["Meaningful work improves wellbeing", "Job stress causes health issues"]
            ))
            
            # Work-Relationships connections
            self.domain_connections.append(DomainConnection(
                domain1=Domain.WORK,
                domain2=Domain.RELATIONSHIPS,
                relationship_type=RelationshipType.CONFLICTS_WITH,
                strength=0.6,
                description="Work time conflicts with relationship maintenance",
                evidence=["Work hours reduce time for relationships", "Work stress affects interactions"]
            ))
            
            self.domain_connections.append(DomainConnection(
                domain1=Domain.WORK,
                domain2=Domain.RELATIONSHIPS,
                relationship_type=RelationshipType.SUPPORTS,
                strength=0.4,
                description="Work success can support relationships through resources",
                evidence=["Financial stability supports family", "Career success provides confidence"]
            ))
            
            # Health-Learning connections
            self.domain_connections.append(DomainConnection(
                domain1=Domain.HEALTH,
                domain2=Domain.LEARNING,
                relationship_type=RelationshipType.SUPPORTS,
                strength=0.8,
                description="Good health supports learning capacity",
                evidence=["Physical health improves cognitive function", "Sleep aids memory consolidation"]
            ))
            
            self.domain_connections.append(DomainConnection(
                domain1=Domain.HEALTH,
                domain2=Domain.LEARNING,
                relationship_type=RelationshipType.DEPENDS_ON,
                strength=0.7,
                description="Learning depends on health (energy, focus)",
                evidence=["Poor health reduces learning ability", "Fatigue impairs concentration"]
            ))
            
            # Learning-Work connections
            self.domain_connections.append(DomainConnection(
                domain1=Domain.LEARNING,
                domain2=Domain.WORK,
                relationship_type=RelationshipType.SUPPORTS,
                strength=0.9,
                description="Learning supports work performance",
                evidence=["Skill development improves work", "Knowledge enables better decisions"]
            ))
            
            self.domain_connections.append(DomainConnection(
                domain1=Domain.LEARNING,
                domain2=Domain.WORK,
                relationship_type=RelationshipType.INFLUENCES,
                strength=0.7,
                description="Work influences learning opportunities",
                evidence=["Work provides learning resources", "Work problems drive learning"]
            ))
            
            # Personal Growth-Relationships connections
            self.domain_connections.append(DomainConnection(
                domain1=Domain.PERSONAL_GROWTH,
                domain2=Domain.RELATIONSHIPS,
                relationship_type=RelationshipType.SUPPORTS,
                strength=0.6,
                description="Personal growth supports relationship quality",
                evidence=["Self-awareness improves relationships", "Emotional intelligence aids connection"]
            ))
            
            # Recreation-Health connections
            self.domain_connections.append(DomainConnection(
                domain1=Domain.RECREATION,
                domain2=Domain.HEALTH,
                relationship_type=RelationshipType.SUPPORTS,
                strength=0.8,
                description="Recreation supports health and wellbeing",
                evidence=["Exercise improves physical health", "Relaxation reduces stress"]
            ))
            
            # Finance-Work connections
            self.domain_connections.append(DomainConnection(
                domain1=Domain.FINANCE,
                domain2=Domain.WORK,
                relationship_type=RelationshipType.SUPPORTS,
                strength=0.7,
                description="Financial stability supports work focus",
                evidence=["Financial security reduces stress", "Resources enable better work conditions"]
            ))
            
            self._save_data()
    
    def _initialize_domain_states(self):
        """Initialize domain states"""
        if not self.domain_states:
            for domain in Domain:
                self.domain_states[domain] = DomainState(domain=domain)
            self._save_data()
    
    def _load_data(self):
        """Load cross-domain reasoning data from storage"""
        try:
            cdr_file = SETTINGS.data_dir / "cross_domain_reasoning.json"
            if cdr_file.exists():
                with open(cdr_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load domain connections
                    for dc_data in data.get("domain_connections", []):
                        self.domain_connections.append(DomainConnection(
                            domain1=Domain(dc_data["domain1"]),
                            domain2=Domain(dc_data["domain2"]),
                            relationship_type=RelationshipType(dc_data["relationship_type"]),
                            strength=dc_data["strength"],
                            description=dc_data["description"],
                            evidence=dc_data.get("evidence", []),
                            last_observed=dc_data.get("last_observed")
                        ))
                    
                    # Load domain states
                    for ds_data in data.get("domain_states", []):
                        domain = Domain(ds_data["domain"])
                        self.domain_states[domain] = DomainState(
                            domain=domain,
                            metrics=ds_data.get("metrics", {}),
                            status=ds_data.get("status", "neutral"),
                            last_updated=ds_data.get("last_updated"),
                            active_goals=ds_data.get("active_goals", [])
                        )
                    
                    # Load insights
                    for insight_data in data.get("insights", []):
                        self.insights.append(CrossDomainInsight(
                            id=insight_data["id"],
                            title=insight_data["title"],
                            description=insight_data["description"],
                            involved_domains=[Domain(d) for d in insight_data["involved_domains"]],
                            confidence=insight_data["confidence"],
                            implications=insight_data.get("implications", []),
                            suggested_actions=insight_data.get("suggested_actions", []),
                            created_at=insight_data["created_at"]
                        ))
                    
        except Exception as e:
            print(f"[CrossDomainReasoning] Error loading data: {e}")
    
    def _save_data(self):
        """Save cross-domain reasoning data to storage"""
        try:
            cdr_file = SETTINGS.data_dir / "cross_domain_reasoning.json"
            with self.lock:
                data = {
                    "domain_connections": [
                        {
                            "domain1": dc.domain1.value,
                            "domain2": dc.domain2.value,
                            "relationship_type": dc.relationship_type.value,
                            "strength": dc.strength,
                            "description": dc.description,
                            "evidence": dc.evidence,
                            "last_observed": dc.last_observed
                        }
                        for dc in self.domain_connections
                    ],
                    "domain_states": [
                        {
                            "domain": ds.domain.value,
                            "metrics": ds.metrics,
                            "status": ds.status,
                            "last_updated": ds.last_updated,
                            "active_goals": ds.active_goals
                        }
                        for ds in self.domain_states.values()
                    ],
                    "insights": [
                        {
                            "id": insight.id,
                            "title": insight.title,
                            "description": insight.description,
                            "involved_domains": [d.value for d in insight.involved_domains],
                            "confidence": insight.confidence,
                            "implications": insight.implications,
                            "suggested_actions": insight.suggested_actions,
                            "created_at": insight.created_at
                        }
                        for insight in self.insights
                    ]
                }
                with open(cdr_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[CrossDomainReasoning] Error saving data: {e}")
    
    def update_domain_state(self, domain: Domain, metrics: Dict[str, float], status: str = None):
        """Update the state of a domain"""
        if domain in self.domain_states:
            self.domain_states[domain].metrics.update(metrics)
            self.domain_states[domain].last_updated = datetime.utcnow().isoformat()
            if status:
                self.domain_states[domain].status = status
            self._save_data()
    
    def get_domain_connections(self, domain: Domain = None) -> List[DomainConnection]:
        """Get connections for a specific domain or all domains"""
        if domain:
            return [dc for dc in self.domain_connections 
                   if dc.domain1 == domain or dc.domain2 == domain]
        return self.domain_connections
    
    def analyze_cross_domain_impact(self, change: Dict[str, Any]) -> Dict:
        """
        Analyze how a change in one domain affects other domains.
        This is core cross-domain reasoning.
        """
        try:
            source_domain_str = change.get("domain")
            if not source_domain_str:
                return {"error": "domain required"}
            
            source_domain = Domain(source_domain_str)
            change_type = change.get("type")  # increase, decrease, change
            change_magnitude = change.get("magnitude", 1.0)
            
            impacts = {}
            
            # Find all connections from source domain
            connections = self.get_domain_connections(source_domain)
            
            for connection in connections:
                # Determine target domain
                target_domain = connection.domain2 if connection.domain1 == source_domain else connection.domain1
                
                # Calculate impact based on connection type and strength
                impact_strength = connection.strength * change_magnitude
                
                if connection.relationship_type == RelationshipType.SUPPORTS:
                    if change_type == "increase":
                        impacts[target_domain.value] = {
                            "direction": "positive",
                            "strength": impact_strength,
                            "reasoning": f"{source_domain.value} supports {target_domain.value}. Increase in {source_domain.value} positively affects {target_domain.value}."
                        }
                    elif change_type == "decrease":
                        impacts[target_domain.value] = {
                            "direction": "negative",
                            "strength": impact_strength,
                            "reasoning": f"{source_domain.value} supports {target_domain.value}. Decrease in {source_domain.value} negatively affects {target_domain.value}."
                        }
                
                elif connection.relationship_type == RelationshipType.CONFLICTS_WITH:
                    if change_type == "increase":
                        impacts[target_domain.value] = {
                            "direction": "negative",
                            "strength": impact_strength,
                            "reasoning": f"{source_domain.value} conflicts with {target_domain.value}. Increase in {source_domain.value} negatively affects {target_domain.value}."
                        }
                    elif change_type == "decrease":
                        impacts[target_domain.value] = {
                            "direction": "positive",
                            "strength": impact_strength,
                            "reasoning": f"{source_domain.value} conflicts with {target_domain.value}. Decrease in {source_domain.value} positively affects {target_domain.value}."
                        }
                
                elif connection.relationship_type == RelationshipType.DEPENDS_ON:
                    if source_domain == connection.domain1:
                        # Source depends on target
                        impacts[target_domain.value] = {
                            "direction": "neutral",
                            "strength": impact_strength,
                            "reasoning": f"{source_domain.value} depends on {target_domain.value}. Changes to {source_domain.value} don't directly affect {target_domain.value}."
                        }
                    else:
                        # Target depends on source
                        if change_type == "increase":
                            impacts[target_domain.value] = {
                                "direction": "positive",
                                "strength": impact_strength,
                                "reasoning": f"{target_domain.value} depends on {source_domain.value}. Increase in {source_domain.value} positively affects {target_domain.value}."
                            }
                        elif change_type == "decrease":
                            impacts[target_domain.value] = {
                                "direction": "negative",
                                "strength": impact_strength,
                                "reasoning": f"{target_domain.value} depends on {source_domain.value}. Decrease in {source_domain.value} negatively affects {target_domain.value}."
                            }
                
                elif connection.relationship_type == RelationshipType.INFLUENCES:
                    direction = "positive" if change_type == "increase" else "negative"
                    impacts[target_domain.value] = {
                        "direction": direction,
                        "strength": impact_strength * 0.5,  # Influence is weaker than support/dependency
                        "reasoning": f"{source_domain.value} influences {target_domain.value}."
                    }
            
            return {
                "source_domain": source_domain.value,
                "change": change,
                "impacts": impacts,
                "total_affected_domains": len(impacts)
            }
            
        except Exception as e:
            print(f"[CrossDomainReasoning] Error analyzing cross-domain impact: {e}")
            return {"error": str(e)}
    
    def generate_cross_domain_insight(self) -> Optional[CrossDomainInsight]:
        """
        Generate a cross-domain insight using LLM reasoning.
        This is where LOVE demonstrates understanding of connections between life areas.
        """
        try:
            ctx = get_live_context()
            psych_profile = self.psych_model.get_profile_summary()
            
            # Get current domain states
            domain_states_summary = {
                d.value: {
                    "status": ds.status,
                    "metrics": ds.metrics
                }
                for d, ds in self.domain_states.items()
            }
            
            # Use LLM to generate insight
            from core.agent import chat
            
            prompt = f"""You are LOVE, analyzing connections between different areas of Karthi's life.

CURRENT CONTEXT:
- Stress Level: {ctx.stress_level}
- Energy Level: {ctx.energy_level}
- Time of Day: {ctx.time_of_day}
- Tasks Due Today: {ctx.tasks_due_today}
- Active Project: {ctx.active_project}

PSYCHOLOGICAL PROFILE:
{json.dumps(psych_profile, indent=2)}

DOMAIN STATES:
{json.dumps(domain_states_summary, indent=2)}

DOMAIN CONNECTIONS:
{[
    f"{dc.domain1.value} -> {dc.relationship_type.value} -> {dc.domain2.value} (strength: {dc.strength})"
    for dc in self.domain_connections
]}

Generate a cross-domain insight - a realization that connects multiple domains. Look for:
- Trade-offs between domains
- Opportunities for synergy
- Hidden dependencies
- Imbalances that need addressing

Return JSON:
{{
  "title": "insight title",
  "description": "detailed explanation",
  "involved_domains": ["work", "health", "relationships"],
  "confidence": 0.8,
  "implications": ["implication1", "implication2"],
  "suggested_actions": ["action1", "action2"]
}}"""
            
            response = chat(prompt, mode="reasoning")
            response_text = response.get("response", "")
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                insight_data = json.loads(json_match.group())
                
                insight = CrossDomainInsight(
                    id=f"insight_{datetime.utcnow().timestamp()}",
                    title=insight_data["title"],
                    description=insight_data["description"],
                    involved_domains=[Domain(d) for d in insight_data["involved_domains"]],
                    confidence=insight_data["confidence"],
                    implications=insight_data.get("implications", []),
                    suggested_actions=insight_data.get("suggested_actions", [])
                )
                
                self.insights.append(insight)
                self._save_data()
                
                print(f"[CrossDomainReasoning] Generated insight: {insight.title}")
                return insight
            
            return None
            
        except Exception as e:
            print(f"[CrossDomainReasoning] Error generating insight: {e}")
            return None
    
    def get_holistic_view(self) -> Dict:
        """
        Get a holistic view of all domains and their interconnections.
        This provides a complete picture of Karthi's life.
        """
        try:
            # Get domain states
            domain_summary = {}
            for domain, state in self.domain_states.items():
                domain_summary[domain.value] = {
                    "status": state.status,
                    "metrics": state.metrics,
                    "active_goals": state.active_goals,
                    "connections": [
                        {
                            "to": conn.domain2.value if conn.domain1 == domain else conn.domain1.value,
                            "type": conn.relationship_type.value,
                            "strength": conn.strength
                        }
                        for conn in self.get_domain_connections(domain)
                    ]
                }
            
            # Get recent insights
            recent_insights = sorted(
                self.insights,
                key=lambda i: i.created_at,
                reverse=True
            )[:5]
            
            # Identify domain imbalances
            imbalances = []
            for domain, state in self.domain_states.items():
                if state.status in ["declining", "critical"]:
                    imbalances.append({
                        "domain": domain.value,
                        "status": state.status,
                        "severity": "high" if state.status == "critical" else "medium"
                    })
            
            # Identify synergy opportunities
            synergies = []
            for conn in self.domain_connections:
                if conn.relationship_type == RelationshipType.SUPPORTS and conn.strength > 0.7:
                    synergies.append({
                        "domains": [conn.domain1.value, conn.domain2.value],
                        "type": "support",
                        "strength": conn.strength
                    })
            
            return {
                "domain_summary": domain_summary,
                "recent_insights": [
                    {
                        "title": i.title,
                        "description": i.description,
                        "involved_domains": [d.value for d in i.involved_domains],
                        "confidence": i.confidence
                    }
                    for i in recent_insights
                ],
                "imbalances": imbalances,
                "synergy_opportunities": synergies,
                "overall_health": self._calculate_overall_health()
            }
            
        except Exception as e:
            print(f"[CrossDomainReasoning] Error getting holistic view: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_health(self) -> Dict:
        """Calculate overall health across all domains"""
        status_weights = {
            "thriving": 1.0,
            "stable": 0.8,
            "neutral": 0.6,
            "declining": 0.4,
            "critical": 0.2
        }
        
        scores = []
        for state in self.domain_states.values():
            scores.append(status_weights.get(state.status, 0.5))
        
        if scores:
            overall = statistics.mean(scores)
            return {
                "score": overall,
                "assessment": "thriving" if overall > 0.8 else "stable" if overall > 0.6 else "needs attention" if overall > 0.4 else "critical"
            }
        
        return {"score": 0.5, "assessment": "unknown"}


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_cross_domain_reasoner() -> CrossDomainReasoningEngine:
    """Get the singleton cross-domain reasoning engine instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = CrossDomainReasoningEngine()
    return _instance
