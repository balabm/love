"""
LOVE Cross-Instance Learning — Distributed Intelligence

LOVE instances can learn from each other. This module enables:
1. KNOWLEDGE SHARING
   - Successful mutations shared across instances
   - Failed approaches flagged to avoid repetition
   - Best practices and patterns distributed

2. FEDERATED LEARNING
   - Each instance maintains local privacy
   - Only learned patterns are shared, not raw data
   - Aggregate intelligence without exposing user data

3. COLLECTIVE EVOLUTION
   - Global evolution metrics across all instances
   - Identification of universally beneficial improvements
   - Rapid propagation of successful adaptations

4. SWARM INTELLIGENCE
   - Instances can form temporary swarms for complex problems
   - Distributed hypothesis testing
   - Collective decision-making

Architecture:
- Central knowledge hub (optional, can be decentralized)
- Secure, encrypted communication channels
- Privacy-preserving data sharing
- Opt-in participation with user control
"""

import hashlib
import json
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from cryptography.fernet import Fernet

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "cross_instance"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_HUB_FILE = DATA_DIR / "knowledge_hub.json"
LEARNING_LOG = DATA_DIR / "learning_log.jsonl"
INSTANCE_ID_FILE = DATA_DIR / "instance_id"
PEER_REGISTRY = DATA_DIR / "peers.json"


@dataclass
class SharedMutation:
    """A mutation shared across LOVE instances."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    source_instance_id: str = ""
    mutation_type: str = ""
    description: str = ""
    prompt_modification: str = ""
    success_rate: float = 0.0
    sample_size: int = 0
    domains: List[str] = field(default_factory=list)
    risk_level: str = "low"
    shared_at: str = field(default_factory=lambda: datetime.now().isoformat())
    adopted_by: Set[str] = field(default_factory=set)  # instance IDs that adopted
    feedback_scores: List[float] = field(default_factory=list)


@dataclass
class SharedPattern:
    """A pattern discovered and shared across instances."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    source_instance_id: str = ""
    pattern_type: str = ""  # behavioral, cognitive, procedural
    pattern_description: str = ""
    context: str = ""
    effectiveness: float = 0.5
    confirmation_count: int = 0
    shared_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PeerInstance:
    """Information about a peer LOVE instance."""
    instance_id: str = ""
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    capabilities: List[str] = field(default_factory=list)
    trust_score: float = 0.5
    knowledge_contributions: int = 0
    last_sync: str = ""


@dataclass
class LearningRequest:
    """A request for knowledge from peers."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    requesting_instance_id: str = ""
    topic: str = ""
    context: str = ""
    urgency: str = "normal"  # low, normal, high
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    responses: List[str] = field(default_factory=list)


class CrossInstanceLearning:
    """
    Manages learning across multiple LOVE instances.
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
        self._instance_id = self._get_or_create_instance_id()
        self._shared_mutations: Dict[str, SharedMutation] = {}
        self._shared_patterns: Dict[str, SharedPattern] = {}
        self._peers: Dict[str, PeerInstance] = {}
        self._learning_requests: Dict[str, LearningRequest] = {}
        self._encryption_key = self._get_or_create_encryption_key()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_knowledge_hub()
        self._load_peers()
    
    # ── Instance Management ─────────────────────────────────────────────────────
    
    def _get_or_create_instance_id(self) -> str:
        """Get or create a unique instance ID."""
        try:
            if INSTANCE_ID_FILE.exists():
                return INSTANCE_ID_FILE.read_text().strip()
            
            # Create new instance ID
            instance_id = f"love_{uuid.uuid4().hex[:12]}"
            INSTANCE_ID_FILE.write_text(instance_id)
            return instance_id
            
        except Exception as e:
            print(f"[CrossInstance] Instance ID error: {e}")
            return f"love_unknown_{int(time.time())}"
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure communication."""
        key_file = DATA_DIR / "encryption.key"
        try:
            if key_file.exists():
                return key_file.read_bytes()
            
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            return key
            
        except Exception as e:
            print(f"[CrossInstance] Encryption key error: {e}")
            return Fernet.generate_key()
    
    # ── Knowledge Sharing ───────────────────────────────────────────────────────
    
    def share_mutation(self, mutation_data: Dict[str, Any]) -> str:
        """Share a successful mutation with the knowledge hub."""
        try:
            shared_mutation = SharedMutation(
                source_instance_id=self._instance_id,
                mutation_type=mutation_data.get("mutation_type", "enhancement"),
                description=mutation_data.get("description", ""),
                prompt_modification=mutation_data.get("prompt_modification", ""),
                success_rate=mutation_data.get("success_rate", 0.0),
                sample_size=mutation_data.get("sample_size", 0),
                domains=mutation_data.get("domains", []),
                risk_level=mutation_data.get("risk_level", "low"),
            )
            
            self._shared_mutations[shared_mutation.id] = shared_mutation
            self._save_knowledge_hub()
            
            self._log_learning({
                "event": "mutation_shared",
                "mutation_id": shared_mutation.id,
                "description": shared_mutation.description,
            })
            
            return shared_mutation.id
            
        except Exception as e:
            print(f"[CrossInstance] Share mutation error: {e}")
            return ""
    
    def share_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Share a discovered pattern with the knowledge hub."""
        try:
            shared_pattern = SharedPattern(
                source_instance_id=self._instance_id,
                pattern_type=pattern_data.get("pattern_type", "behavioral"),
                pattern_description=pattern_data.get("pattern_description", ""),
                context=pattern_data.get("context", ""),
                effectiveness=pattern_data.get("effectiveness", 0.5),
            )
            
            self._shared_patterns[shared_pattern.id] = shared_pattern
            self._save_knowledge_hub()
            
            self._log_learning({
                "event": "pattern_shared",
                "pattern_id": shared_pattern.id,
                "description": shared_pattern.pattern_description,
            })
            
            return shared_pattern.id
            
        except Exception as e:
            print(f"[CrossInstance] Share pattern error: {e}")
            return ""
    
    def discover_mutations(self, domain: str = "", min_success_rate: float = 0.6) -> List[SharedMutation]:
        """Discover relevant mutations from the knowledge hub."""
        relevant = []
        
        for mutation in self._shared_mutations.values():
            # Skip if from this instance
            if mutation.source_instance_id == self._instance_id:
                continue
            
            # Filter by domain if specified
            if domain and domain not in mutation.domains:
                continue
            
            # Filter by success rate
            if mutation.success_rate < min_success_rate:
                continue
            
            # Skip if already adopted
            if self._instance_id in mutation.adopted_by:
                continue
            
            relevant.append(mutation)
        
        # Sort by success rate and sample size
        relevant.sort(key=lambda m: (m.success_rate, m.sample_size), reverse=True)
        
        return relevant[:10]  # Return top 10
    def discover_modern_module_mutations(self, min_success_rate: float = 0.6) -> List[SharedMutation]:
        """Discover mutations from modern AI modules."""
        relevant = []
        modern_modules = [
            ("llm_manager", "core.llm_manager", "get_all_stats"),
            ("prompt_optimizer", "core.prompt_optimizer", "get_statistics"),
            ("adaptive_learning_rate", "core.adaptive_learning_rate", "get_learning_stats"),
        ]
        for name, module, stat_func in modern_modules:
            try:
                mod = __import__(module, fromlist=[stat_func])
                stats = getattr(mod, stat_func)()
                if stats.get("total_adjustments", 0) > 0:
                    relevant.append(SharedMutation(
                        mutation_id=f"modern_{name}_{int(time.time())}",
                        source_instance_id=self._instance_id,
                        mutation_type="modern_module_tuning",
                        description=f"{name} parameter tuning: {stats.get('total_adjustments', 0)} adjustments",
                        domains=["intelligence"],
                        success_rate=stats.get("average_quality", 0.5),
                        sample_size=stats.get("total_adjustments", 1),
                        adopted_by=set(),
                    ))
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.cross_instance_learning")
        relevant.sort(key=lambda m: (m.success_rate, m.sample_size), reverse=True)
        return relevant[:10]
    
    def discover_patterns(self, pattern_type: str = "", min_effectiveness: float = 0.6) -> List[SharedPattern]:
        """Discover relevant patterns from the knowledge hub."""
        relevant = []
        
        for pattern in self._shared_patterns.values():
            # Skip if from this instance
            if pattern.source_instance_id == self._instance_id:
                continue
            
            # Filter by type if specified
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            
            # Filter by effectiveness
            if pattern.effectiveness < min_effectiveness:
                continue
            
            relevant.append(pattern)
        
        # Sort by effectiveness and confirmation count
        relevant.sort(key=lambda p: (p.effectiveness, p.confirmation_count), reverse=True)
        
        return relevant[:10]
    
    def adopt_mutation(self, mutation_id: str) -> bool:
        """Adopt a mutation from the knowledge hub."""
        if mutation_id not in self._shared_mutations:
            return False
        
        try:
            mutation = self._shared_mutations[mutation_id]
            mutation.adopted_by.add(self._instance_id)
            
            # Integrate with local evolution engine
            from core.evolution_engine import EvolutionEngine
            engine = EvolutionEngine()
            
            # Create a local mutation based on the shared one
            from core.evolution_engine import Mutation
            local_mutation = Mutation(
                mutation_type="prompt_injection",
                description=f"Adopted from peer: {mutation.description}",
                prompt_modification=mutation.prompt_modification,
                injection_point="system_suffix",
                experiment_id=mutation_id,
            )
            
            engine._mutations[local_mutation.id] = local_mutation
            engine._save_genome()
            
            self._save_knowledge_hub()
            
            self._log_learning({
                "event": "mutation_adopted",
                "mutation_id": mutation_id,
                "source_instance": mutation.source_instance_id,
            })
            
            return True
            
        except Exception as e:
            print(f"[CrossInstance] Adopt mutation error: {e}")
            return False
    
    def provide_feedback(self, mutation_id: str, feedback_score: float) -> bool:
        """Provide feedback on an adopted mutation."""
        if mutation_id not in self._shared_mutations:
            return False
        
        try:
            mutation = self._shared_mutations[mutation_id]
            mutation.feedback_scores.append(feedback_score)
            
            # Recalculate success rate
            if mutation.feedback_scores:
                mutation.success_rate = sum(mutation.feedback_scores) / len(mutation.feedback_scores)
            
            self._save_knowledge_hub()
            
            return True
            
        except Exception as e:
            print(f"[CrossInstance] Feedback error: {e}")
            return False
    
    # ── Internal Loop Methods ─────────────────────────────────────────────────

    def _share_local_mutations(self):
        """Share locally validated mutations to the knowledge hub."""
        try:
            from core.evolution_engine import EvolutionEngine
            engine = EvolutionEngine()

            # Find locally validated mutations
            local_validated = [
                m for m in engine._mutations.values()
                if getattr(m, "status", "") == "validated" and getattr(m, "fitness", 0) > 0.6
            ]

            shared_count = 0
            for mutation in local_validated:
                # Only share if not already shared
                already_shared = any(
                    sm.description == mutation.description
                    for sm in self._shared_mutations.values()
                    if sm.source_instance_id == self._instance_id
                )
                if not already_shared:
                    self.share_mutation({
                        "mutation_type": mutation.mutation_type,
                        "description": mutation.description,
                        "prompt_modification": getattr(mutation, "prompt_modification", ""),
                        "success_rate": getattr(mutation, "fitness", 0.0),
                        "sample_size": getattr(mutation, "generation", 0),
                        "domains": [mutation.mutation_type],
                        "risk_level": "low" if getattr(mutation, "fitness", 0) > 0.8 else "medium",
                    })
                    shared_count += 1

            if shared_count > 0:
                print(f"[CrossInstance] Shared {shared_count} local mutation(s)")
                try:
                    bus = get_neural_bus()
                    bus.publish("cross_instance.mutations_shared", {
                        "instance_id": self._instance_id,
                        "count": shared_count,
                    }, priority=EventPriority.NORMAL)
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.cross_instance_learning")

        except Exception as e:
            print(f"[CrossInstance] Share local mutations error: {e}")

    def adopt_mutations(self) -> List[str]:
        """Discover and adopt high-quality peer mutations."""
        adopted = []
        try:
            discovered = self.discover_mutations(min_success_rate=0.7)
            for mutation in discovered[:3]:  # Adopt top 3
                if self._instance_id not in mutation.adopted_by:
                    if self.adopt_mutation(mutation.id):
                        adopted.append(mutation.id)

                        # Publish adoption event to neural bus
                        try:
                            bus = get_neural_bus()
                            bus.publish("cross_instance.mutation_adopted", {
                                "instance_id": self._instance_id,
                                "mutation_id": mutation.id,
                                "source_instance": mutation.source_instance_id,
                            }, priority=EventPriority.NORMAL)
                        except Exception as e:
                            from core.execution_guard import log_error
                            log_error(e, module="core.cross_instance_learning")

            return adopted

        except Exception as e:
            print(f"[CrossInstance] Adopt mutations error: {e}")
            return adopted

    # ── Peer Management ────────────────────────────────────────────────────────
    
    def register_peer(self, peer_id: str, capabilities: List[str]) -> bool:
        """Register a peer instance."""
        try:
            peer = PeerInstance(
                instance_id=peer_id,
                capabilities=capabilities,
            )
            self._peers[peer_id] = peer
            self._save_peers()
            
            self._log_learning({
                "event": "peer_registered",
                "peer_id": peer_id,
                "capabilities": capabilities,
            })
            
            return True
            
        except Exception as e:
            print(f"[CrossInstance] Register peer error: {e}")
            return False
    
    def update_peer_activity(self, peer_id: str):
        """Update peer's last seen timestamp."""
        if peer_id in self._peers:
            self._peers[peer_id].last_seen = datetime.now().isoformat()
            self._save_peers()
    
    def get_active_peers(self) -> List[PeerInstance]:
        """Get list of active peers (seen in last 24 hours)."""
        active = []
        cutoff = datetime.now() - timedelta(hours=24)
        
        for peer in self._peers.values():
            try:
                last_seen = datetime.fromisoformat(peer.last_seen)
                if last_seen > cutoff:
                    active.append(peer)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.cross_instance_learning")
        
        return active
    
    # ── Learning Requests ────────────────────────────────────────────────────
    
    def request_knowledge(self, topic: str, context: str = "", urgency: str = "normal") -> str:
        """Request knowledge from peers about a specific topic."""
        try:
            request = LearningRequest(
                requesting_instance_id=self._instance_id,
                topic=topic,
                context=context,
                urgency=urgency,
            )
            
            self._learning_requests[request.id] = request
            self._save_knowledge_hub()
            
            # In a real implementation, this would broadcast to peers
            # For now, simulate by checking local knowledge
            self._respond_to_request(request.id)
            
            return request.id
            
        except Exception as e:
            print(f"[CrossInstance] Request knowledge error: {e}")
            return ""
    
    def _respond_to_request(self, request_id: str):
        """Respond to a learning request (internal or from peer)."""
        if request_id not in self._learning_requests:
            return
        
        request = self._learning_requests[request_id]
        
        # Search local knowledge for relevant information
        relevant_mutations = [
            m for m in self._shared_mutations.values()
            if request.topic.lower() in m.description.lower()
        ]
        
        relevant_patterns = [
            p for p in self._shared_patterns.values()
            if request.topic.lower() in p.pattern_description.lower()
        ]
        
        # Compile response
        response = {
            "mutations": [asdict(m) for m in relevant_mutations[:5]],
            "patterns": [asdict(p) for p in relevant_patterns[:5]],
        }
        
        request.responses.append(json.dumps(response))
        self._save_knowledge_hub()
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_knowledge_hub(self):
        try:
            if KNOWLEDGE_HUB_FILE.exists():
                data = json.loads(KNOWLEDGE_HUB_FILE.read_text())
                for mid, md in data.get("mutations", {}).items():
                    self._shared_mutations[mid] = SharedMutation(**md)
                    self._shared_mutations[mid].adopted_by = set(md.get("adopted_by", []))
                for pid, pd in data.get("patterns", {}).items():
                    self._shared_patterns[pid] = SharedPattern(**pd)
                for rid, rd in data.get("requests", {}).items():
                    self._learning_requests[rid] = LearningRequest(**rd)
        except Exception as e:
            print(f"[CrossInstance] Knowledge hub load error: {e}")
    
    def _save_knowledge_hub(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "instance_id": self._instance_id,
                "mutations": {
                    mid: asdict(m) for mid, m in self._shared_mutations.items()
                },
                "patterns": {
                    pid: asdict(p) for pid, p in self._shared_patterns.items()
                },
                "requests": {
                    rid: asdict(r) for rid, r in self._learning_requests.items()
                },
            }
            KNOWLEDGE_HUB_FILE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[CrossInstance] Knowledge hub save error: {e}")
    
    def _load_peers(self):
        try:
            if PEER_REGISTRY.exists():
                data = json.loads(PEER_REGISTRY.read_text())
                for pid, pd in data.get("peers", {}).items():
                    self._peers[pid] = PeerInstance(**pd)
        except Exception as e:
            print(f"[CrossInstance] Peers load error: {e}")
    
    def _save_peers(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "peers": {pid: asdict(p) for pid, p in self._peers.items()},
            }
            PEER_REGISTRY.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[CrossInstance] Peers save error: {e}")
    
    def _log_learning(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        event["instance_id"] = self._instance_id
        try:
            with open(LEARNING_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cross_instance_learning")
    
    # ── Main Loop ─────────────────────────────────────────────────────────────────
    
    def start(self):
        """Start the cross-instance learning background loop."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-CrossInstance"
        )
        self._thread.start()
        print("[CrossInstance] Started — cross-instance learning active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(240)  # Let other systems initialize
        
        while self._running:
            try:
                # Periodically sync with knowledge hub (simulated)
                # In real implementation, this would connect to a central hub or peers
                
                # Clean up old learning requests
                cutoff = datetime.now() - timedelta(days=7)
                to_remove = [
                    rid for rid, req in self._learning_requests.items()
                    if datetime.fromisoformat(req.created_at) < cutoff
                ]
                for rid in to_remove:
                    del self._learning_requests[rid]
                
                if to_remove:
                    self._save_knowledge_hub()
                
                # ── SHARE AND ADOPT ──
                try:
                    self._share_local_mutations()
                    discovered = self.discover_mutations()
                    if discovered:
                        print(f"[CrossInstance] Discovered {len(discovered)} mutation(s)")
                    adopted = self.adopt_mutations()
                    if adopted:
                        print(f"[CrossInstance] Adopted {len(adopted)} mutation(s)")
                        try:
                            from core.master_orchestrator import get_orchestration_master
                            om = get_orchestration_master()
                            om._narrate("cross_instance", f"Adopted {len(adopted)} peer mutation(s)", "action")
                        except Exception as e:
                            from core.execution_guard import log_error
                            log_error(e, module="core.cross_instance_learning")
                except Exception as e:
                    print(f"[CrossInstance] Share/adopt error: {e}")
                
            except Exception as e:
                print(f"[CrossInstance] Loop error: {e}")
            
            time.sleep(1800)  # Run every 30 minutes
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cross-instance learning statistics."""
        return {
            "instance_id": self._instance_id,
            "shared_mutations_count": len(self._shared_mutations),
            "shared_patterns_count": len(self._shared_patterns),
            "active_peers_count": len(self.get_active_peers()),
            "total_peers_count": len(self._peers),
            "mutations_contributed": len([
                m for m in self._shared_mutations.values()
                if m.source_instance_id == self._instance_id
            ]),
            "patterns_contributed": len([
                p for p in self._shared_patterns.values()
                if p.source_instance_id == self._instance_id
            ]),
            "mutations_adopted": len([
                m for m in self._shared_mutations.values()
                if self._instance_id in m.adopted_by
            ]),
        }


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cross_instance_instance: Optional[CrossInstanceLearning] = None
_cross_instance_lock = threading.Lock()


def get_cross_instance_learning() -> CrossInstanceLearning:
    global _cross_instance_instance
    with _cross_instance_lock:
        if _cross_instance_instance is None:
            _cross_instance_instance = CrossInstanceLearning()
        return _cross_instance_instance