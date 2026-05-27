"""
LOVE Collaborative Evolution — Multi-Instance Coordination

This module enables LOVE instances to collaborate on evolution:
1. COLLABORATIVE HYPOTHESIS TESTING
   - Multiple instances test different hypotheses
   - Share results and learn from each other
   - Coordinate to avoid redundant testing

2. DISTRIBUTED EVOLUTION
   - Distribute evolution workload across instances
   - Specialize instances for different evolution tasks
   - Aggregate collective intelligence

3. CONSENSUS MECHANISMS
   - Reach consensus on evolution decisions
   - Vote on major changes
   - Resolve conflicts between instances

4. COLLECTIVE INTELLIGENCE
   - Combine knowledge from all instances
   - Identify universal improvements
   - Filter out instance-specific biases
"""

import json
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority
from core.cross_instance_learning import get_cross_instance_learning

DATA_DIR = Path(__file__).parent.parent / "data" / "collaborative_evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COLLABORATION_STATE = DATA_DIR / "collaboration_state.json"
COLLABORATION_LOG = DATA_DIR / "collaboration_log.jsonl"
CONSENSUS_HISTORY = DATA_DIR / "consensus_history.json"


@dataclass
class CollaborationTask:
    """A collaborative evolution task distributed across instances."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    task_type: str = ""  # hypothesis_testing, pattern_discovery, validation
    description: str = ""
    assigned_instances: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None
    priority: str = "normal"  # low, normal, high, critical


@dataclass
class ConsensusProposal:
    """A proposal requiring consensus across instances."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    proposal_type: str = ""  # mutation, architecture_change, policy_update
    description: str = ""
    proposed_by: str = ""
    votes: Dict[str, str] = field(default_factory=dict)  # instance_id -> vote (approve/reject/abstain)
    required_votes: int = 3
    status: str = "pending"  # pending, approved, rejected, expired
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    final_decision: str = ""


@dataclass
class InstanceSpecialization:
    """Specialization of an instance for specific evolution tasks."""
    instance_id: str = ""
    specializations: List[str] = field(default_factory=list)  # areas of expertise
    performance_history: Dict[str, float] = field(default_factory=dict)
    availability: float = 1.0  # 0.0 to 1.0
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CollectiveInsight:
    """An insight derived from multiple instances."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    insight_type: str = ""  # universal_pattern, outlier_detection, best_practice
    description: str = ""
    contributing_instances: List[str] = field(default_factory=list)
    confidence: float = 0.5
    universality_score: float = 0.5  # how universal this insight is
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CollaborativeEvolution:
    """
    Manages collaborative evolution across multiple LOVE instances.
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
        self._tasks: Dict[str, CollaborationTask] = {}
        self._proposals: Dict[str, ConsensusProposal] = {}
        self._instance_specializations: Dict[str, InstanceSpecialization] = {}
        self._collective_insights: Dict[str, CollectiveInsight] = {}
        self._peer_instances: Set[str] = set()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_state()
    
    # ── Peer Management ───────────────────────────────────────────────────────
    
    def register_peer_instance(self, instance_id: str, capabilities: List[str]):
        """Register a peer LOVE instance for collaboration."""
        self._peer_instances.add(instance_id)
        
        # Create or update specialization
        if instance_id not in self._instance_specializations:
            self._instance_specializations[instance_id] = InstanceSpecialization(
                instance_id=instance_id,
                specializations=capabilities,
            )
        
        self._save_state()
        self._log_collaboration({
            "event": "peer_registered",
            "instance_id": instance_id,
            "capabilities": capabilities,
        })
    
    def update_instance_specialization(self, instance_id: str, specializations: List[str]):
        """Update an instance's specializations."""
        if instance_id in self._instance_specializations:
            self._instance_specializations[instance_id].specializations = specializations
            self._instance_specializations[instance_id].last_active = datetime.now().isoformat()
            self._save_state()
    
    def get_available_instances(self, specialization: str = "") -> List[str]:
        """Get instances available for collaboration, optionally filtered by specialization."""
        available = []
        
        for instance_id, spec in self._instance_specializations.items():
            # Check if instance is active (recent activity)
            try:
                last_active = datetime.fromisoformat(spec.last_active)
                if (datetime.now() - last_active).total_seconds() < 3600:  # Active within last hour
                    if not specialization or specialization in spec.specializations:
                        available.append(instance_id)
            except Exception:
                pass
        
        return available
    
    # ── Collaborative Task Management ───────────────────────────────────────────
    
    def create_collaborative_task(self, task_type: str, description: str, 
                                 specializations: List[str] = None) -> str:
        """Create a collaborative evolution task."""
        try:
            task = CollaborationTask(
                task_type=task_type,
                description=description,
            )
            
            # Assign to appropriate instances
            if specializations:
                for spec in specializations:
                    available = self.get_available_instances(spec)
                    task.assigned_instances.extend(available[:2])  # Assign up to 2 per specialization
            
            # If no assignments, assign to all available
            if not task.assigned_instances:
                task.assigned_instances = self.get_available_instances()
            
            self._tasks[task.id] = task
            self._save_state()
            
            # Notify assigned instances (in real implementation, would send messages)
            self._notify_instances(task.assigned_instances, task.id)
            
            return task.id
            
        except Exception as e:
            print(f"[CollaborativeEvolution] Task creation error: {e}")
            return ""
    
    def submit_task_result(self, task_id: str, instance_id: str, results: Dict[str, Any]):
        """Submit results for a collaborative task."""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        
        # Store results
        if "instance_results" not in task.results:
            task.results["instance_results"] = {}
        
        task.results["instance_results"][instance_id] = results
        
        # Check if all assigned instances have submitted
        submitted = set(task.results.get("instance_results", {}).keys())
        assigned = set(task.assigned_instances)
        
        if submitted >= assigned:
            task.status = "completed"
            # Aggregate results
            task.results["aggregated"] = self._aggregate_results(task.results["instance_results"])
            self._save_state()
    
    def _aggregate_results(self, instance_results: Dict[str, Dict]) -> Dict[str, Any]:
        """Aggregate results from multiple instances."""
        aggregated = {
            "participating_instances": len(instance_results),
            "consensus_score": 0.0,
            "collective_decision": "",
            "divergence": [],
        }
        
        if not instance_results:
            return aggregated
        
        # Calculate consensus score (simplified)
        values = list(instance_results.values())
        if values:
            # Check for agreement
            first_result = values[0]
            agreement_count = sum(1 for v in values if v == first_result)
            aggregated["consensus_score"] = agreement_count / len(values)
            
            # Identify divergences
            for instance_id, result in instance_results.items():
                if result != first_result:
                    aggregated["divergence"].append({
                        "instance": instance_id,
                        "result": result,
                    })
        
        return aggregated
    
    def _notify_instances(self, instance_ids: List[str], task_id: str):
        """Notify instances about a task assignment."""
        # In real implementation, would send messages via network
        for instance_id in instance_ids:
            self._log_collaboration({
                "event": "task_assigned",
                "instance_id": instance_id,
                "task_id": task_id,
            })
    
    # ── Consensus Mechanisms ───────────────────────────────────────────────────
    
    def create_proposal(self, proposal_type: str, description: str, 
                       proposed_by: str, required_votes: int = 3) -> str:
        """Create a proposal requiring consensus."""
        try:
            # Get instance ID
            from core.cross_instance_learning import get_cross_instance_learning
            cross_instance = get_cross_instance_learning()
            instance_id = cross_instance._instance_id
            
            proposal = ConsensusProposal(
                proposal_type=proposal_type,
                description=description,
                proposed_by=instance_id,
                required_votes=required_votes,
                expires_at=(datetime.now() + timedelta(hours=24)).isoformat(),
            )
            
            # Auto-vote from proposing instance
            proposal.votes[instance_id] = "approve"
            
            self._proposals[proposal.id] = proposal
            self._save_state()
            
            # Broadcast to peers for voting
            self._broadcast_proposal(proposal.id)
            
            return proposal.id
            
        except Exception as e:
            print(f"[CollaborativeEvolution] Proposal creation error: {e}")
            return ""
    
    def vote_on_proposal(self, proposal_id: str, vote: str) -> bool:
        """Vote on a proposal (approve/reject/abstain)."""
        if proposal_id not in self._proposals:
            return False
        
        proposal = self._proposals[proposal_id]
        
        # Get instance ID
        try:
            from core.cross_instance_learning import get_cross_instance_learning
            cross_instance = get_cross_instance_learning()
            instance_id = cross_instance._instance_id
        except Exception:
            return False
        
        # Check if already voted
        if instance_id in proposal.votes:
            return False
        
        # Check if proposal is still valid
        try:
            if datetime.now() > datetime.fromisoformat(proposal.expires_at):
                proposal.status = "expired"
                self._save_state()
                return False
        except Exception:
            pass
        
        # Record vote
        proposal.votes[instance_id] = vote
        
        # Check if consensus reached
        approve_count = sum(1 for v in proposal.votes.values() if v == "approve")
        reject_count = sum(1 for v in proposal.votes.values() if v == "reject")
        
        if approve_count >= proposal.required_votes:
            proposal.status = "approved"
            proposal.final_decision = "approved"
            self._execute_proposal(proposal)
        elif reject_count >= proposal.required_votes:
            proposal.status = "rejected"
            proposal.final_decision = "rejected"
        
        self._save_state()
        self._log_consensus(proposal)
        
        return True
    
    def _broadcast_proposal(self, proposal_id: str):
        """Broadcast proposal to peer instances."""
        proposal = self._proposals[proposal_id]
        
        for instance_id in self._peer_instances:
            self._log_collaboration({
                "event": "proposal_broadcast",
                "proposal_id": proposal_id,
                "target_instance": instance_id,
            })
    
    def _execute_proposal(self, proposal: ConsensusProposal):
        """Execute an approved proposal."""
        try:
            if proposal.proposal_type == "mutation":
                # Execute mutation
                from core.evolution_engine import EvolutionEngine
                engine = EvolutionEngine()
                # This would integrate with the actual mutation application
                pass
            elif proposal.proposal_type == "architecture_change":
                # Execute architecture change
                from core.neural_architecture_search import get_neural_architecture_search
                nas = get_neural_architecture_search()
                # This would integrate with NAS
                pass
            
            self._log_collaboration({
                "event": "proposal_executed",
                "proposal_id": proposal.id,
                "decision": proposal.final_decision,
            })
            
        except Exception as e:
            print(f"[CollaborativeEvolution] Proposal execution error: {e}")
    
    # ── Collective Intelligence ───────────────────────────────────────────────
    
    def derive_collective_insight(self, insight_type: str, data: Dict[str, Any]) -> str:
        """Derive a collective insight from multiple instances."""
        try:
            # Get instance ID
            from core.cross_instance_learning import get_cross_instance_learning
            cross_instance = get_cross_instance_learning()
            instance_id = cross_instance._instance_id
            
            insight = CollectiveInsight(
                insight_type=insight_type,
                description=data.get("description", ""),
                contributing_instances=[instance_id],
                confidence=data.get("confidence", 0.5),
            )
            
            # Check if similar insights exist from other instances
            similar_insights = [
                i for i in self._collective_insights.values()
                if i.insight_type == insight_type and 
                i.description.lower() == insight.description.lower()
            ]
            
            if similar_insights:
                # This is a universal pattern
                for similar in similar_insights:
                    similar.contributing_instances.append(instance_id)
                    similar.confidence = (similar.confidence + insight.confidence) / 2
                    similar.universality_score = min(1.0, similar.universality_score + 0.2)
                
                self._save_state()
                return similar_insights[0].id
            else:
                # New insight
                self._collective_insights[insight.id] = insight
                self._save_state()
                return insight.id
            
        except Exception as e:
            print(f"[CollaborativeEvolution] Insight derivation error: {e}")
            return ""
    
    def get_universal_insights(self, min_universality: float = 0.5) -> List[Dict]:
        """Get insights that are universal across instances."""
        universal = [
            asdict(i) for i in self._collective_insights.values()
            if i.universality_score >= min_universality
        ]
        
        return sorted(universal, key=lambda x: x["universality_score"], reverse=True)
    
    # ── Distributed Evolution Coordination ───────────────────────────────────
    
    def coordinate_distributed_evolution(self) -> Dict[str, Any]:
        """Coordinate distributed evolution across instances."""
        coordination = {
            "tasks_created": [],
            "proposals_created": [],
            "insights_derived": [],
        }
        
        # Create collaborative hypothesis testing task
        task_id = self.create_collaborative_task(
            task_type="hypothesis_testing",
            description="Test hypothesis: uncertainty prefix reduces corrections",
            specializations=["accuracy", "language"]
        )
        if task_id:
            coordination["tasks_created"].append(task_id)
        
        # Create proposal for major change if needed
        if len(self._peer_instances) >= 3:
            proposal_id = self.create_proposal(
                proposal_type="mutation",
                description="Adopt uncertainty prefix behavior across all instances",
                required_votes=len(self._peer_instances) // 2 + 1
            )
            if proposal_id:
                coordination["proposals_created"].append(proposal_id)
        
        return coordination
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        try:
            if COLLABORATION_STATE.exists():
                data = json.loads(COLLABORATION_STATE.read_text())
                for tid, td in data.get("tasks", {}).items():
                    self._tasks[tid] = CollaborationTask(**td)
                for pid, pd in data.get("proposals", {}).items():
                    self._proposals[pid] = ConsensusProposal(**pd)
                for iid, idd in data.get("specializations", {}).items():
                    self._instance_specializations[iid] = InstanceSpecialization(**idd)
                for iid, idd in data.get("insights", {}).items():
                    self._collective_insights[iid] = CollectiveInsight(**idd)
                self._peer_instances = set(data.get("peers", []))
        except Exception as e:
            print(f"[CollaborativeEvolution] State load error: {e}")
    
    def _save_state(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "tasks": {tid: asdict(t) for tid, t in self._tasks.items()},
                "proposals": {pid: asdict(p) for pid, p in self._proposals.items()},
                "specializations": {iid: asdict(i) for iid, i in self._instance_specializations.items()},
                "insights": {iid: asdict(i) for iid, i in self._collective_insights.items()},
                "peers": list(self._peer_instances),
            }
            COLLABORATION_STATE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[CollaborativeEvolution] State save error: {e}")
    
    def _log_collaboration(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(COLLABORATION_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
    
    def _log_consensus(self, proposal: ConsensusProposal):
        try:
            with open(CONSENSUS_HISTORY, "a") as f:
                f.write(json.dumps(asdict(proposal)) + "\n")
        except Exception:
            pass
    
    # ── Main Loop ─────────────────────────────────────────────────────────────────
    
    def start(self):
        """Start the collaborative evolution background loop."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-CollaborativeEvolution"
        )
        self._thread.start()
        print("[CollaborativeEvolution] Started — collaborative evolution active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(300)  # Let other systems initialize
        
        while self._running:
            try:
                # Coordinate distributed evolution
                if len(self._peer_instances) >= 2:
                    self.coordinate_distributed_evolution()
                
                # Clean up expired proposals
                now = datetime.now()
                for proposal_id, proposal in list(self._proposals.items()):
                    try:
                        if proposal.status == "pending":
                            expiry = datetime.fromisoformat(proposal.expires_at)
                            if now > expiry:
                                proposal.status = "expired"
                                self._save_state()
                    except Exception:
                        pass
                
                # Clean up old tasks
                cutoff = datetime.now() - timedelta(days=7)
                for task_id, task in list(self._tasks.items()):
                    try:
                        if datetime.fromisoformat(task.created_at) < cutoff:
                            del self._tasks[task_id]
                            self._save_state()
                    except Exception:
                        pass
                
            except Exception as e:
                print(f"[CollaborativeEvolution] Loop error: {e}")
            
            time.sleep(1800)  # Run every 30 minutes
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_collaboration_status(self) -> Dict[str, Any]:
        """Get overall collaboration status."""
        return {
            "peer_instances": len(self._peer_instances),
            "active_tasks": len([t for t in self._tasks.values() if t.status == "in_progress"]),
            "pending_proposals": len([p for p in self._proposals.values() if p.status == "pending"]),
            "collective_insights": len(self._collective_insights),
            "instance_specializations": {
                iid: asdict(s) for iid, s in self._instance_specializations.items()
            },
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task."""
        if task_id in self._tasks:
            return asdict(self._tasks[task_id])
        return None


# ── Singleton Access ─────────────────────────────────────────────────────────────

_collaborative_evolution_instance: Optional[CollaborativeEvolution] = None
_collaborative_evolution_lock = threading.Lock()


def get_collaborative_evolution() -> CollaborativeEvolution:
    global _collaborative_evolution_instance
    with _collaborative_evolution_lock:
        if _collaborative_evolution_instance is None:
            _collaborative_evolution_instance = CollaborativeEvolution()
        return _collaborative_evolution_instance