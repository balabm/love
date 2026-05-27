"""
Causal & Counterfactual Awareness - The "What-If" Engine

Implements Judea Pearl's Do-Calculus (Interventional logic) for counterfactual reasoning.
Standard AI predicts the next token. This AI predicts branching alternate realities and 
navigates causal graphs.

Before executing any high-stakes action (e.g., executing a Binance trade, sending an automated 
work log, rewriting a core module), the system spawns a CounterfactualThread that simulates 
three parallel timelines:
(a) The optimal outcome, (b) The catastrophic failure outcome, (c) The null (do nothing) outcome.

The system calculates the cascading effects of each timeline out to 3 degrees of separation,
weighting them by probability, and only executes the action if the integral of the positive 
timeline significantly outweighs the risk delta of the negative timeline.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
from collections import deque
import hashlib
import json
import threading
import asyncio
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions requiring causal analysis"""
    TRADE = "trade"  # Financial trades
    WORK_LOG = "work_log"  # Automated work logging
    CODE_REWRITE = "code_rewrite"  # Core module modifications
    SYSTEM_CHANGE = "system_change"  # System configuration changes
    COMMUNICATION = "communication"  # Automated communications
    RESOURCE_ALLOCATION = "resource_allocation"  # Resource decisions
    DEPLOYMENT = "deployment"  # Software deployments
    DATA_MODIFICATION = "data_modification"  # Data changes


class RiskLevel(Enum):
    """Risk levels for actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimelineType(Enum):
    """Types of counterfactual timelines"""
    OPTIMAL = "optimal"  # Best possible outcome
    CATASTROPHIC = "catastrophic"  # Worst possible outcome
    NULL = "null"  # Do nothing scenario


@dataclass
class CausalNode:
    """A node in a causal graph"""
    node_id: str
    name: str
    value: Any
    parents: Set[str]  # Parent node IDs
    children: Set[str]  # Child node IDs
    intervention_value: Optional[Any] = None  # Value if intervened upon
    is_intervened: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "value": str(self.value) if not isinstance(self.value, (dict, list)) else self.value,
            "parents": list(self.parents),
            "children": list(self.children),
            "intervention_value": str(self.intervention_value) if self.intervention_value else None,
            "is_intervened": self.is_intervened
        }


@dataclass
class CausalGraph:
    """A directed acyclic graph representing causal relationships"""
    graph_id: str
    nodes: Dict[str, CausalNode]
    edges: List[Tuple[str, str]]  # (parent, child)
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "graph_id": self.graph_id,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": self.edges,
            "description": self.description,
            "timestamp": self.timestamp.isoformat()
        }
    
    def get_node(self, node_id: str) -> Optional[CausalNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def add_edge(self, parent_id: str, child_id: str) -> None:
        """Add a causal edge"""
        if parent_id in self.nodes and child_id in self.nodes:
            self.nodes[parent_id].children.add(child_id)
            self.nodes[child_id].parents.add(parent_id)
            if (parent_id, child_id) not in self.edges:
                self.edges.append((parent_id, child_id))
    
    def intervene(self, node_id: str, value: Any) -> None:
        """Perform intervention on a node (do-calculus)"""
        if node_id in self.nodes:
            self.nodes[node_id].intervention_value = value
            self.nodes[node_id].is_intervened = True
            logger.info(f"Intervened on node {node_id} with value {value}")


@dataclass
class CounterfactualTimeline:
    """A simulated counterfactual timeline"""
    timeline_id: str
    timeline_type: TimelineType
    action: ActionType
    intervention: Dict[str, Any]  # The intervention being simulated
    outcomes: Dict[str, Any]  # Simulated outcomes
    probability: float
    cascading_effects: List[Dict[str, Any]]  # Effects up to 3 degrees
    utility_score: float  # Expected utility
    risk_score: float  # Risk assessment
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "timeline_id": self.timeline_id,
            "timeline_type": self.timeline_type.value,
            "action": self.action.value,
            "intervention": self.intervention,
            "outcomes": self.outcomes,
            "probability": self.probability,
            "cascading_effects": self.cascading_effects,
            "utility_score": self.utility_score,
            "risk_score": self.risk_score,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CausalAnalysis:
    """Result of causal analysis for an action"""
    analysis_id: str
    action: ActionType
    action_description: str
    risk_level: RiskLevel
    timelines: List[CounterfactualTimeline]
    recommendation: str  # "execute", "defer", "reject"
    confidence: float
    expected_value: float
    risk_delta: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "analysis_id": self.analysis_id,
            "action": self.action.value,
            "action_description": self.action_description,
            "risk_level": self.risk_level.value,
            "timelines": [t.to_dict() for t in self.timelines],
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "expected_value": self.expected_value,
            "risk_delta": self.risk_delta,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


class CausalGraphBuilder:
    """
    Builds causal graphs for different domains and action types.
    
    Creates directed acyclic graphs representing the causal structure
    of systems for counterfactual reasoning.
    """
    
    def __init__(self):
        self.graph_templates: Dict[ActionType, Callable[[], CausalGraph]] = {
            ActionType.TRADE: self._build_trading_graph,
            ActionType.WORK_LOG: self._build_work_log_graph,
            ActionType.CODE_REWRITE: self._build_code_rewrite_graph,
            ActionType.SYSTEM_CHANGE: self._build_system_change_graph,
            ActionType.DEPLOYMENT: self._build_deployment_graph
        }
    
    def build_graph(self, action_type: ActionType, context: Dict[str, Any]) -> CausalGraph:
        """Build a causal graph for the given action type"""
        builder = self.graph_templates.get(action_type)
        if builder:
            return builder(context)
        else:
            return self._build_generic_graph(action_type, context)
    
    def _build_trading_graph(self, context: Dict[str, Any]) -> CausalGraph:
        """Build causal graph for trading actions"""
        graph_id = hashlib.md5(f"trade_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        nodes = {
            "market_price": CausalNode("market_price", "Market Price", context.get("price", 0), set()),
            "portfolio_value": CausalNode("portfolio_value", "Portfolio Value", context.get("portfolio", 0), set()),
            "trade_volume": CausalNode("trade_volume", "Trade Volume", context.get("volume", 0), set()),
            "risk_exposure": CausalNode("risk_exposure", "Risk Exposure", 0.5, set()),
            "liquidity": CausalNode("liquidity", "Market Liquidity", 0.8, set()),
            "profit_loss": CausalNode("profit_loss", "Profit/Loss", 0.0, set()),
            "market_sentiment": CausalNode("market_sentiment", "Market Sentiment", 0.5, set())
        }
        
        graph = CausalGraph(
            graph_id=graph_id,
            nodes=nodes,
            edges=[],
            description="Causal graph for trading decisions"
        )
        
        # Add causal edges
        graph.add_edge("market_price", "portfolio_value")
        graph.add_edge("trade_volume", "risk_exposure")
        graph.add_edge("market_price", "profit_loss")
        graph.add_edge("market_sentiment", "market_price")
        graph.add_edge("liquidity", "trade_volume")
        graph.add_edge("risk_exposure", "profit_loss")
        
        return graph
    
    def _build_work_log_graph(self, context: Dict[str, Any]) -> CausalGraph:
        """Build causal graph for work logging actions"""
        graph_id = hashlib.md5(f"work_log_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        nodes = {
            "task_completion": CausalNode("task_completion", "Task Completion", context.get("completion", 0.5), set()),
            "work_hours": CausalNode("work_hours", "Work Hours", context.get("hours", 8), set()),
            "productivity": CausalNode("productivity", "Productivity", 0.7, set()),
            "team_perception": CausalNode("team_perception", "Team Perception", 0.8, set()),
            "career_progress": CausalNode("career_progress", "Career Progress", 0.5, set()),
            "stress_level": CausalNode("stress_level", "Stress Level", 0.3, set()),
            "work_life_balance": CausalNode("work_life_balance", "Work-Life Balance", 0.6, set())
        }
        
        graph = CausalGraph(
            graph_id=graph_id,
            nodes=nodes,
            edges=[],
            description="Causal graph for work logging decisions"
        )
        
        # Add causal edges
        graph.add_edge("task_completion", "productivity")
        graph.add_edge("work_hours", "stress_level")
        graph.add_edge("productivity", "career_progress")
        graph.add_edge("team_perception", "career_progress")
        graph.add_edge("stress_level", "work_life_balance")
        graph.add_edge("work_hours", "work_life_balance")
        
        return graph
    
    def _build_code_rewrite_graph(self, context: Dict[str, Any]) -> CausalGraph:
        """Build causal graph for code rewrite actions"""
        graph_id = hashlib.md5(f"code_rewrite_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        nodes = {
            "code_quality": CausalNode("code_quality", "Code Quality", context.get("quality", 0.7), set()),
            "system_stability": CausalNode("system_stability", "System Stability", 0.9, set()),
            "performance": CausalNode("performance", "Performance", 0.8, set()),
            "maintainability": CausalNode("maintainability", "Maintainability", 0.6, set()),
            "bug_risk": CausalNode("bug_risk", "Bug Risk", 0.2, set()),
            "development_time": CausalNode("development_time", "Development Time", context.get("dev_time", 1.0), set()),
            "user_satisfaction": CausalNode("user_satisfaction", "User Satisfaction", 0.8, set())
        }
        
        graph = CausalGraph(
            graph_id=graph_id,
            nodes=nodes,
            edges=[],
            description="Causal graph for code rewrite decisions"
        )
        
        # Add causal edges
        graph.add_edge("code_quality", "system_stability")
        graph.add_edge("code_quality", "maintainability")
        graph.add_edge("code_quality", "bug_risk")
        graph.add_edge("performance", "user_satisfaction")
        graph.add_edge("system_stability", "user_satisfaction")
        graph.add_edge("bug_risk", "user_satisfaction")
        graph.add_edge("development_time", "code_quality")
        
        return graph
    
    def _build_system_change_graph(self, context: Dict[str, Any]) -> CausalGraph:
        """Build causal graph for system change actions"""
        graph_id = hashlib.md5(f"system_change_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        nodes = {
            "system_config": CausalNode("system_config", "System Configuration", context.get("config", {}), set()),
            "system_performance": CausalNode("system_performance", "System Performance", 0.8, set()),
            "security": CausalNode("security", "Security", 0.9, set()),
            "compatibility": CausalNode("compatibility", "Compatibility", 0.7, set()),
            "user_experience": CausalNode("user_experience", "User Experience", 0.8, set()),
            "downtime_risk": CausalNode("downtime_risk", "Downtime Risk", 0.1, set()),
            "recovery_time": CausalNode("recovery_time", "Recovery Time", 0.2, set())
        }
        
        graph = CausalGraph(
            graph_id=graph_id,
            nodes=nodes,
            edges=[],
            description="Causal graph for system change decisions"
        )
        
        # Add causal edges
        graph.add_edge("system_config", "system_performance")
        graph.add_edge("system_config", "security")
        graph.add_edge("system_config", "compatibility")
        graph.add_edge("system_performance", "user_experience")
        graph.add_edge("security", "downtime_risk")
        graph.add_edge("compatibility", "user_experience")
        graph.add_edge("downtime_risk", "recovery_time")
        
        return graph
    
    def _build_deployment_graph(self, context: Dict[str, Any]) -> CausalGraph:
        """Build causal graph for deployment actions"""
        graph_id = hashlib.md5(f"deployment_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        nodes = {
            "code_version": CausalNode("code_version", "Code Version", context.get("version", "1.0"), set()),
            "deployment_speed": CausalNode("deployment_speed", "Deployment Speed", 0.7, set()),
            "testing_coverage": CausalNode("testing_coverage", "Testing Coverage", context.get("coverage", 0.8), set()),
            "production_stability": CausalNode("production_stability", "Production Stability", 0.9, set()),
            "user_impact": CausalNode("user_impact", "User Impact", 0.5, set()),
            "rollback_complexity": CausalNode("rollback_complexity", "Rollback Complexity", 0.3, set()),
            "business_value": CausalNode("business_value", "Business Value", 0.8, set())
        }
        
        graph = CausalGraph(
            graph_id=graph_id,
            nodes=nodes,
            edges=[],
            description="Causal graph for deployment decisions"
        )
        
        # Add causal edges
        graph.add_edge("code_version", "production_stability")
        graph.add_edge("testing_coverage", "production_stability")
        graph.add_edge("deployment_speed", "user_impact")
        graph.add_edge("production_stability", "user_impact")
        graph.add_edge("production_stability", "business_value")
        graph.add_edge("rollback_complexity", "user_impact")
        graph.add_edge("testing_coverage", "rollback_complexity")
        
        return graph
    
    def _build_generic_graph(self, action_type: ActionType, context: Dict[str, Any]) -> CausalGraph:
        """Build a generic causal graph"""
        graph_id = hashlib.md5(f"generic_{action_type.value}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        nodes = {
            "action": CausalNode("action", "Action", context.get("action", {}), set()),
            "immediate_effect": CausalNode("immediate_effect", "Immediate Effect", 0.5, set()),
            "secondary_effect": CausalNode("secondary_effect", "Secondary Effect", 0.3, set()),
            "long_term_effect": CausalNode("long_term_effect", "Long-term Effect", 0.2, set()),
            "utility": CausalNode("utility", "Utility", 0.5, set()),
            "risk": CausalNode("risk", "Risk", 0.3, set())
        }
        
        graph = CausalGraph(
            graph_id=graph_id,
            nodes=nodes,
            edges=[],
            description=f"Generic causal graph for {action_type.value}"
        )
        
        # Add generic causal edges
        graph.add_edge("action", "immediate_effect")
        graph.add_edge("immediate_effect", "secondary_effect")
        graph.add_edge("secondary_effect", "long_term_effect")
        graph.add_edge("immediate_effect", "utility")
        graph.add_edge("long_term_effect", "risk")
        
        return graph


class DoCalculusEngine:
    """
    Implements Judea Pearl's Do-Calculus for interventional reasoning.
    
    The do-calculus provides rules for manipulating causal graphs to compute
    the effects of interventions.
    """
    
    def __init__(self):
        self.intervention_history: deque = deque(maxlen=1000)
        
    def apply_intervention(
        self, 
        graph: CausalGraph, 
        node_id: str, 
        intervention_value: Any
    ) -> CausalGraph:
        """
        Apply do-calculus intervention to a causal graph.
        
        Intervention (do(X = x)) sets a variable to a value, removing all
        incoming edges and modifying the causal structure.
        """
        # Create a copy of the graph
        new_graph = CausalGraph(
            graph_id=graph.graph_id + "_intervened",
            nodes={k: CausalNode(
                v.node_id, v.name, v.value, v.parents.copy(), v.children.copy(),
                v.intervention_value, v.is_intervened
            ) for k, v in graph.nodes.items()},
            edges=graph.edges.copy(),
            description=graph.description + " (with intervention)",
            timestamp=datetime.now()
        )
        
        # Apply intervention
        if node_id in new_graph.nodes:
            # Remove incoming edges (do-calculus rule)
            parents = list(new_graph.nodes[node_id].parents)
            for parent in parents:
                new_graph.nodes[parent].children.discard(node_id)
                new_graph.edges = [(p, c) for p, c in new_graph.edges if not (p == parent and c == node_id)]
            
            new_graph.nodes[node_id].parents.clear()
            new_graph.nodes[node_id].intervention_value = intervention_value
            new_graph.nodes[node_id].is_intervened = True
            
            logger.info(f"Applied do-calculus intervention: do({node_id} = {intervention_value})")
        
        self.intervention_history.append({
            "original_graph": graph.graph_id,
            "intervened_graph": new_graph.graph_id,
            "node_id": node_id,
            "intervention_value": intervention_value,
            "timestamp": datetime.now().isoformat()
        })
        
        return new_graph
    
    def compute_causal_effect(
        self, 
        graph: CausalGraph, 
        intervention_node: str, 
        intervention_value: Any,
        target_node: str
    ) -> float:
        """
        Compute the causal effect of an intervention on a target node.
        
        Returns the expected change in the target node's value due to the intervention.
        """
        # Apply intervention
        intervened_graph = self.apply_intervention(graph, intervention_node, intervention_value)
        
        # Propagate effects through the graph
        effect = self._propagate_causal_effect(intervened_graph, intervention_node, target_node)
        
        return effect
    
    def _propagate_causal_effect(
        self, 
        graph: CausalGraph, 
        source_node: str, 
        target_node: str
    ) -> float:
        """
        Propagate causal effects through the graph using simple propagation rules.
        
        In production, this would use more sophisticated causal inference algorithms.
        """
        if source_node not in graph.nodes or target_node not in graph.nodes:
            return 0.0
        
        # Find causal path
        path = self._find_causal_path(graph, source_node, target_node)
        
        if not path:
            return 0.0
        
        # Calculate effect based on path length and node values
        effect = 1.0 / (len(path) + 1)  # Simple decay model
        
        # Adjust for intervention value
        source_node_obj = graph.nodes[source_node]
        if source_node_obj.intervention_value is not None:
            if isinstance(source_node_obj.intervention_value, (int, float)):
                effect *= abs(source_node_obj.intervention_value)
        
        return effect
    
    def _find_causal_path(
        self, 
        graph: CausalGraph, 
        source: str, 
        target: str
    ) -> Optional[List[str]]:
        """Find a causal path from source to target using BFS"""
        from collections import deque
        
        queue = deque([(source, [source])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target:
                return path
            
            # Get children (causal descendants)
            current_node = graph.nodes.get(current)
            if current_node:
                for child in current_node.children:
                    if child not in visited:
                        visited.add(child)
                        queue.append((child, path + [child]))
        
        return None


class CounterfactualSimulator:
    """
    Simulates counterfactual timelines for decision making.
    
    Creates parallel simulations of different outcomes to support
    evidence-based decision making under uncertainty.
    """
    
    def __init__(self):
        self.simulation_history: deque = deque(maxlen=500)
        self.do_calculus = DoCalculusEngine()
        
    def simulate_counterfactuals(
        self, 
        action: ActionType, 
        action_description: str,
        context: Dict[str, Any],
        intervention: Dict[str, Any]
    ) -> List[CounterfactualTimeline]:
        """
        Simulate three counterfactual timelines:
        1. Optimal outcome
        2. Catastrophic outcome  
        3. Null (do nothing) outcome
        """
        # Build causal graph
        graph_builder = CausalGraphBuilder()
        causal_graph = graph_builder.build_graph(action, context)
        
        timelines = []
        
        # Simulate optimal timeline
        optimal_timeline = self._simulate_timeline(
            causal_graph, action, action_description, intervention,
            TimelineType.OPTIMAL, context
        )
        timelines.append(optimal_timeline)
        
        # Simulate catastrophic timeline
        catastrophic_timeline = self._simulate_timeline(
            causal_graph, action, action_description, intervention,
            TimelineType.CATASTROPHIC, context
        )
        timelines.append(catastrophic_timeline)
        
        # Simulate null timeline
        null_timeline = self._simulate_timeline(
            causal_graph, action, action_description, {},
            TimelineType.NULL, context
        )
        timelines.append(null_timeline)
        
        self.simulation_history.append({
            "action": action.value,
            "timelines": [t.timeline_id for t in timelines],
            "timestamp": datetime.now().isoformat()
        })
        
        return timelines
    
    def _simulate_timeline(
        self, 
        graph: CausalGraph, 
        action: ActionType, 
        action_description: str,
        intervention: Dict[str, Any],
        timeline_type: TimelineType,
        context: Dict[str, Any]
    ) -> CounterfactualTimeline:
        """Simulate a specific counterfactual timeline"""
        timeline_id = hashlib.md5(
            f"{action.value}_{timeline_type.value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Apply intervention if not null timeline
        if timeline_type != TimelineType.NULL and intervention:
            for node_id, value in intervention.items():
                if node_id in graph.nodes:
                    graph = self.do_calculus.apply_intervention(graph, node_id, value)
        
        # Simulate outcomes based on timeline type
        outcomes = self._generate_outcomes(graph, timeline_type, context)
        
        # Calculate cascading effects (3 degrees of separation)
        cascading_effects = self._calculate_cascading_effects(graph, timeline_type, context)
        
        # Calculate probability based on timeline type
        probability = self._estimate_probability(timeline_type, context)
        
        # Calculate utility and risk scores
        utility_score = self._calculate_utility(outcomes, timeline_type)
        risk_score = self._calculate_risk(cascading_effects, timeline_type)
        
        timeline = CounterfactualTimeline(
            timeline_id=timeline_id,
            timeline_type=timeline_type,
            action=action,
            intervention=intervention,
            outcomes=outcomes,
            probability=probability,
            cascading_effects=cascading_effects,
            utility_score=utility_score,
            risk_score=risk_score
        )
        
        return timeline
    
    def _generate_outcomes(
        self, 
        graph: CausalGraph, 
        timeline_type: TimelineType,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate outcomes for the timeline"""
        outcomes = {}
        
        for node_id, node in graph.nodes.items():
            if timeline_type == TimelineType.OPTIMAL:
                # Optimistic outcomes
                if isinstance(node.value, (int, float)):
                    outcomes[node_id] = node.value * 1.2  # 20% improvement
                else:
                    outcomes[node_id] = "optimal_" + str(node.value)
            elif timeline_type == TimelineType.CATASTROPHIC:
                # Pessimistic outcomes
                if isinstance(node.value, (int, float)):
                    outcomes[node_id] = node.value * 0.5  # 50% degradation
                else:
                    outcomes[node_id] = "catastrophic_" + str(node.value)
            else:  # NULL
                # Baseline outcomes
                outcomes[node_id] = node.value
        
        return outcomes
    
    def _calculate_cascading_effects(
        self, 
        graph: CausalGraph, 
        timeline_type: TimelineType,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate cascading effects up to 3 degrees of separation"""
        effects = []
        
        # Get intervened nodes
        intervened_nodes = [
            node_id for node_id, node in graph.nodes.items() 
            if node.is_intervened
        ]
        
        if not intervened_nodes:
            return effects
        
        # Calculate effects for each degree of separation
        for degree in range(1, 4):  # 3 degrees
            degree_effects = []
            
            for source_node in intervened_nodes:
                # Find nodes at this degree
                nodes_at_degree = self._find_nodes_at_degree(graph, source_node, degree)
                
                for target_node in nodes_at_degree:
                    effect_magnitude = self._calculate_effect_magnitude(graph, source_node, target_node, timeline_type)
                    degree_effects.append({
                        "source": source_node,
                        "target": target_node,
                        "degree": degree,
                        "effect_magnitude": effect_magnitude
                    })
            
            if degree_effects:
                effects.append({
                    "degree": degree,
                    "effects": degree_effects,
                    "total_effect": sum(e["effect_magnitude"] for e in degree_effects)
                })
        
        return effects
    
    def _find_nodes_at_degree(
        self, 
        graph: CausalGraph, 
        source: str, 
        degree: int
    ) -> List[str]:
        """Find nodes at a specific degree of separation"""
        if degree == 0:
            return [source]
        
        current_level = {source}
        visited = {source}
        
        for d in range(degree):
            next_level = set()
            for node in current_level:
                node_obj = graph.nodes.get(node)
                if node_obj:
                    for child in node_obj.children:
                        if child not in visited:
                            visited.add(child)
                            next_level.add(child)
            current_level = next_level
            
            if not current_level:
                break
        
        return list(current_level)
    
    def _calculate_effect_magnitude(
        self, 
        graph: CausalGraph, 
        source: str, 
        target: str,
        timeline_type: TimelineType
    ) -> float:
        """Calculate the magnitude of effect between nodes"""
        base_effect = 0.5  # Base effect magnitude
        
        # Adjust based on timeline type
        if timeline_type == TimelineType.OPTIMAL:
            base_effect *= 1.5
        elif timeline_type == TimelineType.CATASTROPHIC:
            base_effect *= 2.0
        
        # Adjust based on graph structure
        path_length = len(self._find_causal_path(graph, source, target) or [])
        if path_length > 0:
            base_effect /= path_length
        
        return base_effect
    
    def _find_causal_path(
        self, 
        graph: CausalGraph, 
        source: str, 
        target: str
    ) -> Optional[List[str]]:
        """Find causal path using BFS"""
        from collections import deque
        
        queue = deque([(source, [source])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target:
                return path
            
            current_node = graph.nodes.get(current)
            if current_node:
                for child in current_node.children:
                    if child not in visited:
                        visited.add(child)
                        queue.append((child, path + [child]))
        
        return None
    
    def _estimate_probability(self, timeline_type: TimelineType, context: Dict[str, Any]) -> float:
        """Estimate probability of timeline occurring"""
        base_probabilities = {
            TimelineType.OPTIMAL: 0.3,
            TimelineType.CATASTROPHIC: 0.1,
            TimelineType.NULL: 0.6
        }
        
        # Adjust based on context
        risk_factor = context.get("risk_factor", 0.5)
        
        if timeline_type == TimelineType.CATASTROPHIC:
            return base_probabilities[timeline_type] * (1.0 + risk_factor)
        elif timeline_type == TimelineType.OPTIMAL:
            return base_probabilities[timeline_type] * (1.0 - risk_factor * 0.5)
        else:
            return base_probabilities[timeline_type]
    
    def _calculate_utility(self, outcomes: Dict[str, Any], timeline_type: TimelineType) -> float:
        """Calculate utility score for outcomes"""
        if timeline_type == TimelineType.OPTIMAL:
            return 0.8
        elif timeline_type == TimelineType.CATASTROPHIC:
            return -0.6
        else:
            return 0.0
    
    def _calculate_risk(self, cascading_effects: List[Dict[str, Any]], timeline_type: TimelineType) -> float:
        """Calculate risk score based on cascading effects"""
        if not cascading_effects:
            return 0.0
        
        total_effect = sum(effect["total_effect"] for effect in cascading_effects)
        
        if timeline_type == TimelineType.CATASTROPHIC:
            return min(total_effect, 1.0)
        elif timeline_type == TimelineType.OPTIMAL:
            return max(0.0, total_effect - 0.3)
        else:
            return total_effect * 0.5


class CausalDecisionEngine:
    """
    Main engine for causal decision making using counterfactual reasoning.
    
    Evaluates high-stakes actions by simulating counterfactual timelines
    and providing evidence-based recommendations.
    """
    
    def __init__(self):
        self.simulator = CounterfactualSimulator()
        self.analysis_history: deque = deque(maxlen=200)
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.9
        }
        
    def analyze_action(
        self, 
        action: ActionType, 
        action_description: str,
        context: Dict[str, Any],
        intervention: Dict[str, Any]
    ) -> CausalAnalysis:
        """
        Perform comprehensive causal analysis of an action.
        
        Simulates counterfactual timelines and provides recommendation
        based on expected value vs risk delta.
        """
        # Determine risk level
        risk_level = self._assess_risk_level(action, context)
        
        # Simulate counterfactual timelines
        timelines = self.simulator.simulate_counterfactuals(
            action, action_description, context, intervention
        )
        
        # Calculate expected value and risk delta
        expected_value = self._calculate_expected_value(timelines)
        risk_delta = self._calculate_risk_delta(timelines)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            expected_value, risk_delta, risk_level, timelines
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(timelines, expected_value, risk_delta)
        
        # Calculate confidence
        confidence = self._calculate_confidence(timelines, risk_level)
        
        analysis_id = hashlib.md5(
            f"{action.value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        analysis = CausalAnalysis(
            analysis_id=analysis_id,
            action=action,
            action_description=action_description,
            risk_level=risk_level,
            timelines=timelines,
            recommendation=recommendation,
            confidence=confidence,
            expected_value=expected_value,
            risk_delta=risk_delta,
            reasoning=reasoning
        )
        
        self.analysis_history.append(analysis)
        logger.info(f"Causal analysis completed: {recommendation} (confidence: {confidence:.2%})")
        
        return analysis
    
    def _assess_risk_level(self, action: ActionType, context: Dict[str, Any]) -> RiskLevel:
        """Assess the risk level of an action"""
        risk_scores = {
            ActionType.TRADE: RiskLevel.HIGH,
            ActionType.CODE_REWRITE: RiskLevel.MEDIUM,
            ActionType.DEPLOYMENT: RiskLevel.HIGH,
            ActionType.SYSTEM_CHANGE: RiskLevel.MEDIUM,
            ActionType.WORK_LOG: RiskLevel.LOW,
            ActionType.COMMUNICATION: RiskLevel.LOW,
            ActionType.RESOURCE_ALLOCATION: RiskLevel.MEDIUM,
            ActionType.DATA_MODIFICATION: RiskLevel.MEDIUM
        }
        
        base_risk = risk_scores.get(action, RiskLevel.MEDIUM)
        
        # Adjust based on context
        risk_factor = context.get("risk_factor", 0.5)
        if risk_factor > 0.7 and base_risk == RiskLevel.MEDIUM:
            return RiskLevel.HIGH
        elif risk_factor > 0.9 and base_risk == RiskLevel.HIGH:
            return RiskLevel.CRITICAL
        
        return base_risk
    
    def _calculate_expected_value(self, timelines: List[CounterfactualTimeline]) -> float:
        """Calculate expected value across all timelines"""
        expected_value = 0.0
        
        for timeline in timelines:
            expected_value += timeline.probability * timeline.utility_score
        
        return expected_value
    
    def _calculate_risk_delta(self, timelines: List[CounterfactualTimeline]) -> float:
        """Calculate risk delta between optimal and catastrophic timelines"""
        optimal = next((t for t in timelines if t.timeline_type == TimelineType.OPTIMAL), None)
        catastrophic = next((t for t in timelines if t.timeline_type == TimelineType.CATASTROPHIC), None)
        
        if optimal and catastrophic:
            return catastrophic.risk_score - optimal.risk_score
        return 0.0
    
    def _generate_recommendation(
        self, 
        expected_value: float, 
        risk_delta: float, 
        risk_level: RiskLevel,
        timelines: List[CounterfactualTimeline]
    ) -> str:
        """Generate action recommendation"""
        # Get risk threshold
        risk_threshold = self.risk_thresholds.get(risk_level, 0.5)
        
        # Decision logic
        if expected_value > 0.3 and risk_delta < risk_threshold:
            return "execute"
        elif expected_value > 0.0 and risk_delta < risk_threshold * 1.5:
            return "defer"
        else:
            return "reject"
    
    def _generate_reasoning(
        self, 
        timelines: List[CounterfactualTimeline], 
        expected_value: float,
        risk_delta: float
    ) -> str:
        """Generate human-readable reasoning"""
        optimal = next((t for t in timelines if t.timeline_type == TimelineType.OPTIMAL), None)
        catastrophic = next((t for t in timelines if t.timeline_type == TimelineType.CATASTROPHIC), None)
        
        reasoning = f"Expected value: {expected_value:.3f}, Risk delta: {risk_delta:.3f}. "
        
        if optimal:
            reasoning += f"Optimal outcome probability: {optimal.probability:.2%}, "
        if catastrophic:
            reasoning += f"Catastrophic outcome probability: {catastrophic.probability:.2%}. "
        
        reasoning += "Based on counterfactual simulation of 3 timelines."
        
        return reasoning
    
    def _calculate_confidence(
        self, 
        timelines: List[CounterfactualTimeline], 
        risk_level: RiskLevel
    ) -> float:
        """Calculate confidence in the analysis"""
        # Base confidence
        confidence = 0.7
        
        # Adjust based on risk level
        if risk_level == RiskLevel.CRITICAL:
            confidence = 0.9
        elif risk_level == RiskLevel.HIGH:
            confidence = 0.8
        elif risk_level == RiskLevel.LOW:
            confidence = 0.6
        
        # Adjust based on timeline probability spread
        probabilities = [t.probability for t in timelines]
        prob_variance = np.var(probabilities) if len(probabilities) > 1 else 0
        confidence -= prob_variance * 0.5
        
        return max(0.0, min(1.0, confidence))


# Singleton instance
_causal_simulator_instance: Optional[CausalDecisionEngine] = None
_engine_lock = threading.Lock()

def get_causal_simulator() -> CausalDecisionEngine:
    """Get the singleton Causal Simulator instance"""
    global _causal_simulator_instance
    with _engine_lock:
        if _causal_simulator_instance is None:
            _causal_simulator_instance = CausalDecisionEngine()
        return _causal_simulator_instance


if __name__ == "__main__":
    # Test the Causal Simulator
    print("Testing Causal Simulator...")
    
    simulator = get_causal_simulator()
    
    # Test a high-stakes trading decision
    analysis = simulator.analyze_action(
        action=ActionType.TRADE,
        action_description="Execute large Bitcoin trade",
        context={
            "price": 45000,
            "volume": 10,
            "portfolio": 100000,
            "risk_factor": 0.8
        },
        intervention={
            "trade_volume": 10,
            "trade_type": "buy"
        }
    )
    
    print(f"\nCausal Analysis Result:")
    print(f"Action: {analysis.action.value}")
    print(f"Risk Level: {analysis.risk_level.value}")
    print(f"Recommendation: {analysis.recommendation}")
    print(f"Confidence: {analysis.confidence:.2%}")
    print(f"Expected Value: {analysis.expected_value:.3f}")
    print(f"Risk Delta: {analysis.risk_delta:.3f}")
    print(f"Reasoning: {analysis.reasoning}")
    
    print(f"\nTimeline Simulations:")
    for timeline in analysis.timelines:
        print(f"  {timeline.timeline_type.value}: utility={timeline.utility_score:.3f}, "
              f"probability={timeline.probability:.2%}, risk={timeline.risk_score:.3f}")
    
    print("\nCausal Simulator test completed successfully!")