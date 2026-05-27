"""
Global Workspace Buffer - Consciousness Bus

Implements Global Workspace Theory where specialized sub-agents compete to broadcast
their state to the entire system. Only the agent that most effectively reduces 
current system entropy wins the broadcast rights.

Based on Bernard Baars' Global Workspace Theory and integrated with the
Free Energy Principle for entropy-based competition.
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import json
from collections import deque
import threading
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialized agents in the global workspace"""
    MATH = "math"
    CODE = "code"
    EMOTION = "emotion"
    MEMORY = "memory"
    PERCEPTION = "perception"
    PLANNING = "planning"
    EXECUTION = "execution"
    METACOGNITION = "metacognition"


@dataclass
class BroadcastProposal:
    """A proposal from an agent to broadcast to the global workspace"""
    agent_id: str
    agent_type: AgentType
    content: Any
    entropy_reduction: float  # How much this broadcast reduces system entropy
    confidence: float
    priority: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert proposal to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "content": str(self.content) if not isinstance(self.content, (dict, list)) else self.content,
            "entropy_reduction": self.entropy_reduction,
            "confidence": self.confidence,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class GlobalBroadcast:
    """A successful broadcast to the global workspace"""
    winning_agent: str
    agent_type: AgentType
    content: Any
    entropy_before: float
    entropy_after: float
    broadcast_time: datetime
    duration: timedelta
    reach: List[str]  # Which agents received this broadcast
    impact_score: float
    
    def to_dict(self) -> Dict:
        """Convert broadcast to dictionary"""
        return {
            "winning_agent": self.winning_agent,
            "agent_type": self.agent_type.value,
            "content": str(self.content) if not isinstance(self.content, (dict, list)) else self.content,
            "entropy_before": self.entropy_before,
            "entropy_after": self.entropy_after,
            "broadcast_time": self.broadcast_time.isoformat(),
            "duration_seconds": self.duration.total_seconds(),
            "reach": self.reach,
            "impact_score": self.impact_score
        }


class WorkspaceAgent:
    """
    A specialized agent that competes for broadcast rights in the global workspace.
    
    Each agent maintains its own local processing and can propose broadcasts
    when it has information that would reduce system entropy.
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.local_state: Dict[str, Any] = {}
        self.broadcast_history: deque = deque(maxlen=100)
        self.successful_broadcasts = 0
        self.failed_broadcasts = 0
        self.competitive_score = 0.5  # Starts neutral, evolves based on success
        
    def update_local_state(self, state: Dict[str, Any]) -> None:
        """Update the agent's local state"""
        self.local_state.update(state)
        logger.debug(f"Agent {self.agent_id} updated local state")
        
    def calculate_entropy_reduction(self, current_system_entropy: float) -> float:
        """
        Calculate how much this agent's current state would reduce system entropy.
        
        This is the core competitive metric - agents that can most reduce
        system uncertainty get broadcast priority.
        """
        # Base entropy reduction from state complexity
        state_complexity = len(self.local_state) * 0.1
        
        # Boost for recent successful broadcasts (momentum)
        momentum = min(self.successful_broadcasts * 0.05, 0.5)
        
        # Penalty for recent failed broadcasts
        failure_penalty = min(self.failed_broadcasts * 0.03, 0.3)
        
        # Competitive score based on historical performance
        competitive_boost = self.competitive_score * 0.2
        
        entropy_reduction = state_complexity + momentum + competitive_boost - failure_penalty
        return max(0.0, min(1.0, entropy_reduction))
    
    def propose_broadcast(
        self, 
        content: Any, 
        current_system_entropy: float,
        confidence: float = 0.8,
        priority: float = 0.5
    ) -> BroadcastProposal:
        """Create a broadcast proposal"""
        entropy_reduction = self.calculate_entropy_reduction(current_system_entropy)
        
        proposal = BroadcastProposal(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            content=content,
            entropy_reduction=entropy_reduction,
            confidence=confidence,
            priority=priority,
            timestamp=datetime.now(),
            metadata={"local_state_size": len(self.local_state)}
        )
        
        logger.debug(f"Agent {self.agent_id} proposed broadcast with entropy reduction: {entropy_reduction:.3f}")
        return proposal
    
    def record_broadcast_result(self, success: bool, impact_score: float = 0.5) -> None:
        """Record the outcome of a broadcast attempt"""
        if success:
            self.successful_broadcasts += 1
            # Update competitive score based on impact
            self.competitive_score = min(1.0, self.competitive_score + impact_score * 0.1)
        else:
            self.failed_broadcasts += 1
            # Decay competitive score
            self.competitive_score = max(0.0, self.competitive_score - 0.05)
        
        logger.debug(f"Agent {self.agent_id} broadcast result: {success}, competitive score: {self.competitive_score:.3f}")


class ConsciousnessBus:
    """
    Global Workspace Buffer - implements consciousness as a competitive broadcast system.
    
    The consciousness bus manages:
    1. Agent registration and management
    2. Broadcast proposal collection and evaluation
    3. Entropy calculation and winner selection
    4. Global broadcast distribution
    5. System-wide state synchronization
    """
    
    def __init__(self, competition_interval: float = 0.1):
        self.agents: Dict[str, WorkspaceAgent] = {}
        self.competition_interval = competition_interval
        self.current_system_entropy = 1.0  # Starts at maximum entropy
        self.broadcast_history: deque = deque(maxlen=1000)
        self.proposal_queue: deque = deque(maxlen=100)
        self.active_broadcasts: Dict[str, GlobalBroadcast] = {}
        self.running = False
        self.lock = threading.Lock()
        
        # System-wide state that all agents can access
        self.global_state: Dict[str, Any] = {
            "current_focus": None,
            "active_tasks": [],
            "emotional_context": {},
            "perceptual_context": {},
            "working_memory": [],
            "episodic_buffer": []
        }
        
    def register_agent(self, agent_id: str, agent_type: AgentType) -> WorkspaceAgent:
        """Register a new agent in the global workspace"""
        agent = WorkspaceAgent(agent_id, agent_type)
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id} of type {agent_type.value}")
        return agent
    
    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the global workspace"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[WorkspaceAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def calculate_system_entropy(self) -> float:
        """
        Calculate current system entropy based on:
        1. State variance across agents
        2. Global state uncertainty
        3. Recent broadcast success rates
        """
        if not self.agents:
            return 1.0  # Maximum entropy when no agents
        
        # Calculate variance in agent states
        agent_entropies = []
        for agent in self.agents.values():
            # Entropy from local state complexity
            state_entropy = min(len(agent.local_state) * 0.05, 0.5)
            # Entropy from competitive uncertainty
            competitive_entropy = 1.0 - agent.competitive_score
            agent_entropies.append(state_entropy + competitive_entropy)
        
        # Average agent entropy
        avg_agent_entropy = np.mean(agent_entropies) if agent_entropies else 0.5
        
        # Global state entropy
        global_entropy = min(len(self.global_state) * 0.03, 0.3)
        
        # Recent broadcast uncertainty
        if self.broadcast_history:
            recent_impacts = [b.impact_score for b in list(self.broadcast_history)[-10:]]
            broadcast_entropy = 1.0 - np.mean(recent_impacts) if recent_impacts else 0.5
        else:
            broadcast_entropy = 0.5
        
        # Combined system entropy
        total_entropy = (avg_agent_entropy * 0.4 + 
                       global_entropy * 0.3 + 
                       broadcast_entropy * 0.3)
        
        self.current_system_entropy = max(0.0, min(1.0, total_entropy))
        return self.current_system_entropy
    
    def submit_proposal(self, proposal: BroadcastProposal) -> None:
        """Submit a broadcast proposal to the queue"""
        self.proposal_queue.append(proposal)
        logger.debug(f"Proposal submitted from {proposal.agent_id}")
    
    def evaluate_proposals(self) -> Optional[BroadcastProposal]:
        """
        Evaluate all pending proposals and select the winner.
        
        The winner is the proposal that:
        1. Most reduces system entropy
        2. Has highest confidence
        3. Has appropriate priority
        """
        if not self.proposal_queue:
            return None
        
        with self.lock:
            proposals = list(self.proposal_queue)
            self.proposal_queue.clear()
        
        if not proposals:
            return None
        
        # Score each proposal
        scored_proposals = []
        for proposal in proposals:
            # Combined score: entropy reduction + confidence + priority
            score = (proposal.entropy_reduction * 0.5 + 
                    proposal.confidence * 0.3 + 
                    proposal.priority * 0.2)
            scored_proposals.append((score, proposal))
        
        # Sort by score and select winner
        scored_proposals.sort(key=lambda x: x[0], reverse=True)
        winner = scored_proposals[0][1]
        
        logger.info(f"Broadcast winner: {winner.agent_id} with score {scored_proposals[0][0]:.3f}")
        return winner
    
    def execute_broadcast(self, proposal: BroadcastProposal) -> GlobalBroadcast:
        """
        Execute the winning broadcast to the global workspace.
        
        This updates the global state and notifies all registered agents.
        """
        entropy_before = self.current_system_entropy
        
        # Update global state based on broadcast content
        if isinstance(proposal.content, dict):
            self.global_state.update(proposal.content)
        else:
            self.global_state["last_broadcast"] = str(proposal.content)
        
        # Calculate new entropy
        entropy_after = self.calculate_system_entropy()
        
        # Determine which agents receive this broadcast
        reach = [agent_id for agent_id in self.agents.keys() if agent_id != proposal.agent_id]
        
        # Calculate impact score
        entropy_reduction = entropy_before - entropy_after
        impact_score = max(0.0, entropy_reduction * proposal.confidence)
        
        # Create broadcast record
        broadcast = GlobalBroadcast(
            winning_agent=proposal.agent_id,
            agent_type=proposal.agent_type,
            content=proposal.content,
            entropy_before=entropy_before,
            entropy_after=entropy_after,
            broadcast_time=datetime.now(),
            duration=timedelta(seconds=0),  # Would be measured in real execution
            reach=reach,
            impact_score=impact_score
        )
        
        # Store broadcast
        self.broadcast_history.append(broadcast)
        self.active_broadcasts[proposal.agent_id] = broadcast
        
        # Notify the winning agent
        if proposal.agent_id in self.agents:
            self.agents[proposal.agent_id].record_broadcast_result(True, impact_score)
        
        # Notify competing agents (they lost)
        for agent_id, agent in self.agents.items():
            if agent_id != proposal.agent_id:
                agent.record_broadcast_result(False, 0.0)
        
        logger.info(f"Broadcast executed by {proposal.agent_id}, entropy change: {entropy_before:.3f} → {entropy_after:.3f}")
        return broadcast
    
    def start_competition_loop(self) -> None:
        """Start the continuous competition loop"""
        self.running = True
        logger.info("Starting consciousness bus competition loop")
        
        def competition_loop():
            while self.running:
                try:
                    # Calculate current system entropy
                    self.calculate_system_entropy()
                    
                    # Evaluate and execute broadcasts
                    winner = self.evaluate_proposals()
                    if winner:
                        self.execute_broadcast(winner)
                    
                    # Small delay to prevent CPU spinning
                    asyncio.sleep(self.competition_interval)
                    
                except Exception as e:
                    logger.error(f"Error in competition loop: {e}")
                    asyncio.sleep(1.0)
        
        # Run in background thread
        thread = threading.Thread(target=competition_loop, daemon=True)
        thread.start()
    
    def stop_competition_loop(self) -> None:
        """Stop the competition loop"""
        self.running = False
        logger.info("Stopped consciousness bus competition loop")
    
    def get_global_state(self) -> Dict[str, Any]:
        """Get the current global state"""
        return self.global_state.copy()
    
    def get_broadcast_history(self, limit: int = 10) -> List[GlobalBroadcast]:
        """Get recent broadcast history"""
        return list(self.broadcast_history)[-limit:]
    
    def get_agent_status(self) -> Dict[str, Dict]:
        """Get status of all registered agents"""
        return {
            agent_id: {
                "type": agent.agent_type.value,
                "competitive_score": agent.competitive_score,
                "successful_broadcasts": agent.successful_broadcasts,
                "failed_broadcasts": agent.failed_broadcasts,
                "local_state_size": len(agent.local_state)
            }
            for agent_id, agent in self.agents.items()
        }


# Singleton instance
_consciousness_bus_instance: Optional[ConsciousnessBus] = None
_bus_lock = threading.Lock()

def get_consciousness_bus() -> ConsciousnessBus:
    """Get the singleton consciousness bus instance"""
    global _consciousness_bus_instance
    with _bus_lock:
        if _consciousness_bus_instance is None:
            _consciousness_bus_instance = ConsciousnessBus()
            _consciousness_bus_instance.start_competition_loop()
        return _consciousness_bus_instance


# Convenience functions for common operations
def register_math_agent(agent_id: str = "math_agent") -> WorkspaceAgent:
    """Register a math-specialized agent"""
    bus = get_consciousness_bus()
    return bus.register_agent(agent_id, AgentType.MATH)

def register_code_agent(agent_id: str = "code_agent") -> WorkspaceAgent:
    """Register a code-specialized agent"""
    bus = get_consciousness_bus()
    return bus.register_agent(agent_id, AgentType.CODE)

def register_emotion_agent(agent_id: str = "emotion_agent") -> WorkspaceAgent:
    """Register an emotion-specialized agent"""
    bus = get_consciousness_bus()
    return bus.register_agent(agent_id, AgentType.EMOTION)

def submit_broadcast(agent_id: str, content: Any, confidence: float = 0.8, priority: float = 0.5) -> bool:
    """Submit a broadcast proposal from an agent"""
    bus = get_consciousness_bus()
    agent = bus.get_agent(agent_id)
    if not agent:
        logger.warning(f"Agent {agent_id} not found")
        return False
    
    proposal = agent.propose_broadcast(
        content=content,
        current_system_entropy=bus.current_system_entropy,
        confidence=confidence,
        priority=priority
    )
    bus.submit_proposal(proposal)
    return True


if __name__ == "__main__":
    # Test the consciousness bus
    print("Testing Consciousness Bus...")
    
    bus = get_consciousness_bus()
    
    # Register specialized agents
    math_agent = register_math_agent("math_specialist")
    code_agent = register_code_agent("code_specialist") 
    emotion_agent = register_emotion_agent("emotion_specialist")
    
    # Update agent states
    math_agent.update_local_state({"current_problem": "optimization", "confidence": 0.9})
    code_agent.update_local_state({"current_task": "debugging", "complexity": 0.7})
    emotion_agent.update_local_state({"user_mood": "frustrated", "intensity": 0.8})
    
    # Submit broadcast proposals
    submit_broadcast("math_specialist", {"solution": "Use gradient descent"}, confidence=0.9, priority=0.7)
    submit_broadcast("code_specialist", {"fix": "Add null check"}, confidence=0.8, priority=0.6)
    submit_broadcast("emotion_specialist", {"suggestion": "Take a break"}, confidence=0.7, priority=0.8)
    
    # Let the competition loop process
    import time
    time.sleep(1)
    
    # Check results
    print(f"\nSystem Entropy: {bus.current_system_entropy:.3f}")
    print(f"Broadcast History: {len(bus.broadcast_history)} broadcasts")
    print(f"Agent Status: {bus.get_agent_status()}")
    
    print("\nConsciousness Bus test completed successfully!")