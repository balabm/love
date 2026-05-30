"""
LOVE Evolution Integration — Unified Evolution System

This module integrates all evolution systems into a cohesive whole:
- Base evolution engine (performance-based hypothesis testing)
- Meta-evolution (learning how to learn better)
- Swarm evolution (parallel hypothesis testing)
- Self-coder (automated code generation)
- Cross-instance learning (distributed intelligence)

The integration layer ensures all systems work together harmoniously
and provides a unified interface for evolution control and monitoring.
"""

import json
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.evolution_engine import EvolutionEngine
from core.meta_evolution import get_meta_evolution
from core.swarm_evolution import get_swarm_evolution
from core.self_coder import get_self_coder
from core.cross_instance_learning import get_cross_instance_learning
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "evolution_integration"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTEGRATION_STATE = DATA_DIR / "integration_state.json"
INTEGRATION_LOG = DATA_DIR / "integration_log.jsonl"


@dataclass
class IntegrationState:
    """State of the evolution integration."""
    last_full_cycle: str = ""
    base_evolution_active: bool = False
    meta_evolution_active: bool = False
    swarm_evolution_active: bool = False
    self_coder_active: bool = False
    cross_instance_active: bool = False
    autonomous_cicd_active: bool = False
    total_mutations_applied: int = 0
    total_hypotheses_tested: int = 0
    total_code_modifications: int = 0
    successful_cross_adoptions: int = 0


class EvolutionIntegration:
    """
    Unified evolution system that coordinates all evolution components.
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
        self._state = IntegrationState()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_state()
    
    # ── Lifecycle Management ─────────────────────────────────────────────────────
    
    def start_all(self):
        """Start all evolution systems."""
        print("[EvolutionIntegration] Starting all evolution systems...")
        
        # Start base evolution engine
        try:
            base_engine = EvolutionEngine()
            base_engine.start_evolution_loop()
            self._state.base_evolution_active = True
            print("[EvolutionIntegration] Base evolution engine started")
        except Exception as e:
            print(f"[EvolutionIntegration] Base evolution error: {e}")
        
        # Start meta-evolution
        try:
            meta_engine = get_meta_evolution()
            meta_engine.initialize_strategies()
            meta_engine.start()
            self._state.meta_evolution_active = True
            print("[EvolutionIntegration] Meta-evolution started")
        except Exception as e:
            print(f"[EvolutionIntegration] Meta-evolution error: {e}")
        
        # Start swarm evolution
        try:
            swarm_engine = get_swarm_evolution()
            swarm_engine.start()
            self._state.swarm_evolution_active = True
            print("[EvolutionIntegration] Swarm evolution started")
        except Exception as e:
            print(f"[EvolutionIntegration] Swarm evolution error: {e}")
        
        # Start self-coder
        try:
            self_coder = get_self_coder()
            self_coder.start()
            self._state.self_coder_active = True
            print("[EvolutionIntegration] Self-coder started")
        except Exception as e:
            print(f"[EvolutionIntegration] Self-coder error: {e}")
        
        # Start cross-instance learning
        try:
            cross_instance = get_cross_instance_learning()
            cross_instance.start()
            self._state.cross_instance_active = True
            print("[EvolutionIntegration] Cross-instance learning started")
        except Exception as e:
            print(f"[EvolutionIntegration] Cross-instance error: {e}")
        
        # Start autonomous CI/CD
        try:
            from core.autonomous_cicd import get_autonomous_cicd
            cicd = get_autonomous_cicd()
            cicd.start()
            self._state.autonomous_cicd_active = True
            print('[EvolutionIntegration] Autonomous CI/CD started')
        except Exception as e:
            print(f'[EvolutionIntegration] Autonomous CI/CD error: {e}')
        
        # Start MCP Host (modern tool protocol)
        try:
            from core.mcp_host import get_mcp_host
            mcp = get_mcp_host()
            mcp.start()
            print('[EvolutionIntegration] MCP Host started')
        except Exception as e:
            print(f'[EvolutionIntegration] MCP Host error: {e}')
        
        # Start Reasoning Engine (chain-of-thought)
        try:
            from core.reasoning_engine import get_reasoning_engine
            re = get_reasoning_engine()
            print('[EvolutionIntegration] Reasoning Engine initialized')
        except Exception as e:
            print(f'[EvolutionIntegration] Reasoning Engine error: {e}')
        
        # Start Neural Architecture Search
        try:
            from core.neural_architecture_search import get_neural_architecture_search
            nas = get_neural_architecture_search()
            nas.start()
            print('[EvolutionIntegration] Neural Architecture Search started')
        except Exception as e:
            print(f'[EvolutionIntegration] NAS error: {e}')
        
        # Start Multi-Modal Evolution
        try:
            from core.multimodal_evolution import get_multimodal_evolution
            mme = get_multimodal_evolution()
            mme.start()
            print('[EvolutionIntegration] Multi-Modal Evolution started')
        except Exception as e:
            print(f'[EvolutionIntegration] Multi-Modal error: {e}')
        
        # Start integration loop
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-EvolutionIntegration"
        )
        self._thread.start()
        
        self._save_state()
        print("[EvolutionIntegration] All evolution systems started")
    
    def stop_all(self):
        """Stop all evolution systems."""
        print("[EvolutionIntegration] Stopping all evolution systems...")
        
        self._running = False
        
        try:
            get_meta_evolution().stop()
        except Exception:
            pass
        
        try:
            get_swarm_evolution().stop()
        except Exception:
            pass
        
        try:
            get_self_coder().stop()
        except Exception:
            pass
        
        try:
            from core.autonomous_cicd import get_autonomous_cicd
            get_autonomous_cicd().stop()
        except Exception:
            pass
        
        try:
            get_cross_instance_learning().stop()
        except Exception:
            pass
        
        print("[EvolutionIntegration] All evolution systems stopped")
    
    # ── Coordination Loop ───────────────────────────────────────────────────────
    
    def _main_loop(self):
        """Main coordination loop that keeps all systems in sync."""
        time.sleep(300)  # Let systems initialize
        
        while self._running:
            try:
                self._run_full_cycle()
            except Exception as e:
                print(f"[EvolutionIntegration] Cycle error: {e}")
            
            time.sleep(1800)  # Run full cycle every 30 minutes
    
    def _run_full_cycle(self):
        """Run a full evolution coordination cycle."""
        cycle_start = datetime.now()
        
        self._log_integration({
            "event": "cycle_start",
            "timestamp": cycle_start.isoformat(),
        })
        
        # 1. Get evolutionary pressures from meta-evolution
        try:
            meta_engine = get_meta_evolution()
            pressures = meta_engine.update_evolutionary_pressures()
            priorities = meta_engine.get_evolutionary_priorities()
            
            self._log_integration({
                "event": "pressures_updated",
                "priorities": priorities[:3],
            })
        except Exception as e:
            print(f"[EvolutionIntegration] Pressure update error: {e}")
        
        # 2. Check for predictive hypotheses that should be activated
        try:
            current_state = self._get_current_state()
            activated = meta_engine.check_predictive_triggers(current_state)
            
            if activated:
                self._log_integration({
                    "event": "predictive_hypotheses_activated",
                    "count": len(activated),
                })
        except Exception as e:
            print(f"[EvolutionIntegration] Predictive trigger error: {e}")
        
        # 3. Share successful mutations with cross-instance learning
        try:
            self._share_successful_mutations()
        except Exception as e:
            print(f"[EvolutionIntegration] Share mutations error: {e}")
        
        # 4. Discover and adopt beneficial mutations from peers
        try:
            self._discover_and_adopt_mutations()
        except Exception as e:
            print(f"[EvolutionIntegration] Adopt mutations error: {e}")
        
        # 5. Coordinate swarm testing if multiple hypotheses exist
        try:
            self._coordinate_swarm_testing()
        except Exception as e:
            print(f"[EvolutionIntegration] Swarm coordination error: {e}")
        
        # 6. Generate code modifications for high-confidence improvements
        try:
            self._generate_code_improvements()
        except Exception as e:
            print(f"[EvolutionIntegration] Code generation error: {e}")
        
        # 7. Self-heal: check and restart crashed subsystems
        try:
            self._heal_subsystems()
        except Exception as e:
            print(f"[EvolutionIntegration] Self-heal error: {e}")
        
        # Update state
        self._state.last_full_cycle = datetime.now().isoformat()
        self._save_state()
        
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        self._log_integration({
            "event": "cycle_complete",
            "duration_seconds": cycle_duration,
        })
        
        # ── REPORT TO ORCHESTRATOR ──
        # If we made improvements, tell the user through the orchestrator
        try:
            from core.master_orchestrator import get_orchestration_master
            om = get_orchestration_master()
            total_mods = self._state.total_code_modifications
            total_muts = self._state.total_mutations_applied
            total_adopt = self._state.successful_cross_adoptions
            
            if total_mods > 0 or total_muts > 0:
                om._narrate(
                    "evolution_cycle",
                    f"Evolution cycle complete in {cycle_duration:.0f}s. Total: {total_mods} code mods, {total_muts} mutations, {total_adopt} adoptions.",
                    "action",
                    importance="normal"
                )
                # Only notify user about significant milestones
                if total_mods > 0 and total_mods % 5 == 0:
                    om.speak_to_user(
                        f"I've made {total_mods} code improvements through self-evolution. "
                        "I'm learning how to serve you better.",
                        category="EVOLUTION",
                        importance="normal"
                    )
        except Exception:
            pass
    
    def _heal_subsystems(self):
        """Check subsystem health and restart any that have crashed."""
        subsystems = [
            ("meta_evolution", get_meta_evolution, "start"),
            ("swarm_evolution", get_swarm_evolution, "start"),
            ("self_coder", get_self_coder, "start"),
            ("cross_instance", get_cross_instance_learning, "start"),
        ]
        restarted = 0
        for name, getter, method in subsystems:
            try:
                instance = getter()
                if not getattr(instance, '_running', False):
                    getattr(instance, method)()
                    restarted += 1
                    print(f"[EvolutionIntegration] Self-healed: restarted {name}")
            except Exception as e:
                print(f"[EvolutionIntegration] Could not heal {name}: {e}")
        if restarted > 0:
            self._log_integration({
                "event": "subsystems_healed",
                "restarted_count": restarted,
            })

    def _get_current_state(self) -> Dict[str, Any]:
        """Get current state for predictive trigger checking."""
        state = {}
        
        try:
            from agents.task_agent import get_task_overview
            tasks = get_task_overview()
            state["overdue_count"] = tasks.get("overdue_count", 0)
            state["upcoming_deadline_hours"] = 999  # Simplified
        except Exception:
            pass
        
        try:
            from integrations.finance_intelligence import get_finance_intelligence
            fi = get_finance_intelligence()
            prices = fi.get_prices()
            # Calculate market change (simplified)
            state["market_change"] = 0.0
        except Exception:
            pass
        
        return state
    
    def _share_successful_mutations(self):
        """Share successful mutations with cross-instance learning."""
        try:
            base_engine = EvolutionEngine()
            cross_instance = get_cross_instance_learning()
            
            # Find successful mutations
            successful = [
                m for m in base_engine._mutations.values()
                if m.active and m.fitness > 0.7 and m.interactions_since_applied > 5
            ]
            
            for mutation in successful:
                # Check if already shared
                if mutation.id in [m.id for m in cross_instance._shared_mutations.values()]:
                    continue
                
                # Share with cross-instance learning
                cross_instance.share_mutation({
                    "mutation_type": mutation.mutation_type,
                    "description": mutation.description,
                    "prompt_modification": mutation.prompt_modification,
                    "success_rate": mutation.fitness,
                    "sample_size": mutation.interactions_since_applied,
                    "risk_level": "low" if mutation.fitness > 0.8 else "medium",
                })
            
            if successful:
                self._log_integration({
                    "event": "mutations_shared",
                    "count": len(successful),
                })
                
        except Exception as e:
            print(f"[EvolutionIntegration] Share mutations error: {e}")
    
    def _discover_and_adopt_mutations(self):
        """Discover and adopt beneficial mutations from peers."""
        try:
            cross_instance = get_cross_instance_learning()
            
            # Get high-priority domain from meta-evolution
            meta_engine = get_meta_evolution()
            priorities = meta_engine.get_evolutionary_priorities()
            target_domain = priorities[0][0] if priorities else ""
            
            # Discover mutations for this domain
            discovered = cross_instance.discover_mutations(
                domain=target_domain,
                min_success_rate=0.7
            )
            
            # Adopt top mutations
            for mutation in discovered[:2]:  # Adopt up to 2
                if cross_instance.adopt_mutation(mutation.id):
                    self._state.successful_cross_adoptions += 1
                    self._log_integration({
                        "event": "mutation_adopted",
                        "mutation_id": mutation.id,
                        "source": mutation.source_instance_id,
                    })
                    
        except Exception as e:
            print(f"[EvolutionIntegration] Adopt mutations error: {e}")
    
    def _coordinate_swarm_testing(self):
        """Coordinate swarm testing for multiple hypotheses."""
        try:
            base_engine = EvolutionEngine()
            swarm_engine = get_swarm_evolution()
            
            # Get proposed hypotheses
            proposed = [
                h for h in base_engine._hypotheses.values()
                if h.status == "proposed"
            ]
            
            if len(proposed) >= 2:
                # Convert to swarm format
                hypotheses_data = [
                    {
                        "id": h.id,
                        "hypothesis": h.claim,
                        "proposed_change": h.rationale,
                    }
                    for h in proposed[:3]
                ]
                
                # Spawn swarms
                swarm_ids = swarm_engine.spawn_swarms(hypotheses_data)
                
                if swarm_ids:
                    # Start competition
                    swarm_engine.start_competition(swarm_ids)
                    
                    self._log_integration({
                        "event": "swarm_competition_started",
                        "swarm_count": len(swarm_ids),
                    })
                    
        except Exception as e:
            print(f"[EvolutionIntegration] Swarm coordination error: {e}")
    
    def _generate_code_improvements(self):
        """Generate code improvements for high-confidence hypotheses."""
        try:
            base_engine = EvolutionEngine()
            self_coder = get_self_coder()
            
            # Find high-confidence confirmed hypotheses
            confirmed = [
                h for h in base_engine._hypotheses.values()
                if h.status == "confirmed" and h.confidence > 0.8
            ]
            
            for hypothesis in confirmed[:2]:  # Generate up to 2 per cycle
                # Determine target file based on hypothesis
                target_file = self._map_hypothesis_to_file(hypothesis)
                
                if target_file:
                    # Generate modification
                    modification = self_coder.generate_modification(
                        hypothesis=hypothesis.claim,
                        file_path=target_file,
                        improvement_type="enhancement"
                    )
                    
                    if modification:
                        # Test the modification
                        if self_coder.test_modification(modification.id):
                            # Apply if tests pass
                            if self_coder.apply_modification(modification.id):
                                self._state.total_code_modifications += 1
                                self._log_integration({
                                    "event": "code_modification_applied",
                                    "modification_id": modification.id,
                                    "file": target_file,
                                })
                    
        except Exception as e:
            print(f"[EvolutionIntegration] Code generation error: {e}")
    
    def _map_hypothesis_to_file(self, hypothesis) -> Optional[str]:
        """Map a hypothesis to a target file for code modification."""
        # Simplified mapping - in real implementation would be more sophisticated
        hypothesis_text = hypothesis.claim.lower()
        
        if "proactive" in hypothesis_text or "initiative" in hypothesis_text:
            return "core/proactive_push.py"
        elif "memory" in hypothesis_text or "recall" in hypothesis_text:
            return "core/memory.py"
        elif "evolution" in hypothesis_text or "learning" in hypothesis_text:
            return "core/evolution_engine.py"
        elif "swarm" in hypothesis_text or "parallel" in hypothesis_text:
            return "core/swarm_evolution.py"
        else:
            return None
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        try:
            if INTEGRATION_STATE.exists():
                data = json.loads(INTEGRATION_STATE.read_text())
                self._state = IntegrationState(**data)
        except Exception as e:
            print(f"[EvolutionIntegration] State load error: {e}")
    
    def _save_state(self):
        try:
            from dataclasses import asdict
            INTEGRATION_STATE.write_text(json.dumps(asdict(self._state), indent=2, default=str))
        except Exception as e:
            print(f"[EvolutionIntegration] State save error: {e}")
    
    def _log_integration(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(INTEGRATION_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get overall integration status."""
        return {
            "running": self._running,
            "last_full_cycle": self._state.last_full_cycle,
            "systems": {
                "base_evolution": self._state.base_evolution_active,
                "meta_evolution": self._state.meta_evolution_active,
                "swarm_evolution": self._state.swarm_evolution_active,
                "self_coder": self._state.self_coder_active,
                "cross_instance": self._state.cross_instance_active,
            },
            "statistics": {
                "total_mutations_applied": self._state.total_mutations_applied,
                "total_hypotheses_tested": self._state.total_hypotheses_tested,
                "total_code_modifications": self._state.total_code_modifications,
                "successful_cross_adoptions": self._state.successful_cross_adoptions,
            },
        }
    
    def trigger_manual_cycle(self):
        """Manually trigger a full evolution cycle."""
        if not self._running:
            print("[EvolutionIntegration] Integration not running")
            return
        
        print("[EvolutionIntegration] Triggering manual cycle...")
        threading.Thread(target=self._run_full_cycle, daemon=True).start()


# ── Singleton Access ─────────────────────────────────────────────────────────────

_evolution_integration_instance: Optional[EvolutionIntegration] = None
_evolution_integration_lock = threading.Lock()


def get_evolution_integration() -> EvolutionIntegration:
    global _evolution_integration_instance
    with _evolution_integration_lock:
        if _evolution_integration_instance is None:
            _evolution_integration_instance = EvolutionIntegration()
        return _evolution_integration_instance