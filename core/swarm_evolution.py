"""
LOVE Swarm Evolution — Parallel Hypothesis Testing System

Instead of testing hypotheses one at a time, LOVE spawns multiple
"agent swarms" that test different hypotheses in parallel.

Swarm architecture:
1. HYPOTHESIS SWARMS
   - Each swarm tests a specific hypothesis
   - Swarms run in parallel with different user interactions
   - Results are compared to find the most effective mutation

2. EXPLORATION-EXPLOITATION BALANCE
   - Some swarms explore radically different approaches
   - Some swarms exploit known successful patterns
   - Dynamic allocation based on confidence levels

3. SWARM INTELLIGENCE
   - Swarms share successful patterns with each other
   - Failed approaches are quickly abandoned
   - Collective learning accelerates evolution

4. COMPETITIVE SELECTION
   - Swarms compete based on user satisfaction
   - Best-performing swarm's mutation is integrated
   - Losing swarms are disbanded or repurposed
"""

import json
import random
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

DATA_DIR = Path(__file__).parent.parent / "data" / "swarm_evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SWARM_STATE_FILE = DATA_DIR / "swarm_state.json"
SWARM_LOG = DATA_DIR / "swarm_log.jsonl"
COMPETITION_RESULTS = DATA_DIR / "competition_results.json"


@dataclass
class SwarmAgent:
    """A single agent within a swarm."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    role: str = ""  # explorer, exploiter, validator, synthesizer
    hypothesis_id: str = ""
    performance_score: float = 0.5
    interactions_count: int = 0
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Swarm:
    """A collection of agents testing a hypothesis."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    hypothesis_id: str = ""
    hypothesis: str = ""
    mutation: str = ""
    strategy: str = ""  # exploration, exploitation, balanced
    agents: List[SwarmAgent] = field(default_factory=list)
    collective_score: float = 0.5
    interactions_count: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"  # active, completed, disbanded, winner
    phase: str = "testing"  # testing, validating, synthesizing
    learnings: List[str] = field(default_factory=list)


@dataclass
class Competition:
    """A competition between swarms to select the best mutation."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    swarms: List[str] = field(default_factory=list)  # swarm IDs
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    winner_swarm_id: Optional[str] = None
    winning_mutation: str = ""
    criteria: List[str] = field(default_factory=list)
    results: Dict[str, float] = field(default_factory=dict)  # swarm_id -> score


@dataclass
class SwarmSignal:
    """A signal shared between swarms."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    source_swarm_id: str = ""
    signal_type: str = ""  # success, failure, pattern, insight
    content: str = ""
    strength: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SwarmEvolutionEngine:
    """
    Manages parallel hypothesis testing using agent swarms.
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
        self._swarms: Dict[str, Swarm] = {}
        self._competitions: Dict[str, Competition] = {}
        self._signals: List[SwarmSignal] = []
        self._active_competition: Optional[str] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._max_swarms = 5
        self._agents_per_swarm = 3
        self._load_state()
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        try:
            if SWARM_STATE_FILE.exists():
                data = json.loads(SWARM_STATE_FILE.read_text())
                for sid, sd in data.get("swarms", {}).items():
                    swarm = Swarm(**sd)
                    swarm.agents = [SwarmAgent(**a) for a in swarm.agents]
                    # Only keep active swarms; discard completed/disbanded from previous runs
                    if swarm.status == "active":
                        self._swarms[sid] = swarm
                for cid, cd in data.get("competitions", {}).items():
                    self._competitions[cid] = Competition(**cd)
        except Exception as e:
            print(f"[SwarmEvolution] Load error: {e}")
    
    def _save_state(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "active_competition": self._active_competition,
                "swarms": {sid: asdict(s) for sid, s in self._swarms.items()},
                "competitions": {cid: asdict(c) for cid, c in self._competitions.items()},
            }
            SWARM_STATE_FILE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[SwarmEvolution] Save error: {e}")
    
    def _log_swarm(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(SWARM_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
    
    # ── Swarm Management ─────────────────────────────────────────────────────────
    
    def spawn_swarms(self, hypotheses: List[Dict[str, Any]]) -> List[str]:
        """Spawn multiple swarms to test different hypotheses in parallel."""
        active_count = sum(1 for s in self._swarms.values() if s.status == "active")
        if active_count >= self._max_swarms:
            return []

        spawned_ids = []

        for i, hyp in enumerate(hypotheses):
            active_count = sum(1 for s in self._swarms.values() if s.status == "active")
            if active_count >= self._max_swarms:
                break
            
            # Determine strategy based on index
            strategies = ["exploration", "exploitation", "balanced"]
            strategy = strategies[i % len(strategies)]
            
            swarm = Swarm(
                hypothesis_id=hyp.get("id", ""),
                hypothesis=hyp.get("hypothesis", ""),
                mutation=hyp.get("proposed_change", ""),
                strategy=strategy,
            )
            
            # Spawn agents for this swarm
            agent_roles = ["explorer", "exploiter", "validator"]
            for role in agent_roles:
                agent = SwarmAgent(
                    role=role,
                    hypothesis_id=hyp.get("id", ""),
                )
                swarm.agents.append(agent)
            
            self._swarms[swarm.id] = swarm
            spawned_ids.append(swarm.id)
            
            self._log_swarm({
                "event": "swarm_spawned",
                "swarm_id": swarm.id,
                "hypothesis": hyp.get("hypothesis", ""),
                "strategy": strategy,
            })
        
        self._save_state()
        print(f"[SwarmEvolution] Spawned {len(spawned_ids)} swarms")
        return spawned_ids
    
    def update_swarm_performance(self, swarm_id: str, user_feedback: float, interaction_data: Dict):
        """Update swarm performance based on user interaction."""
        if swarm_id not in self._swarms:
            return
        
        swarm = self._swarms[swarm_id]
        swarm.interactions_count += 1
        
        # Update collective score with exponential smoothing
        alpha = 0.2
        swarm.collective_score = (alpha * user_feedback + 
                                 (1 - alpha) * swarm.collective_score)
        
        # Update individual agents
        for agent in swarm.agents:
            agent.interactions_count += 1
            # Agents closer to the interaction get more credit
            agent.performance_score = (alpha * user_feedback + 
                                     (1 - alpha) * agent.performance_score)
            agent.last_active = datetime.now().isoformat()
        
        # Modern module swarm: check AGI spine health for module swarms
        if swarm.hypothesis and swarm.hypothesis.startswith("modern_module:"):
            try:
                from core.agi_spine import get_agi_system_flags
                flags = get_agi_system_flags()
                module_name = swarm.hypothesis.replace("modern_module:", "").strip()
                if flags.get(module_name, False):
                    swarm.collective_score = min(1.0, swarm.collective_score + 0.1)
                else:
                    swarm.collective_score = max(0.0, swarm.collective_score - 0.2)
            except Exception:
                pass
        
        # Share signal if performance is notably good or bad
        if user_feedback > 0.8:
            self._share_signal(swarm_id, "success", 
                             f"Strong positive feedback: {interaction_data}", 
                             strength=user_feedback)
        elif user_feedback < 0.3:
            self._share_signal(swarm_id, "failure",
                             f"Poor performance detected: {interaction_data}",
                             strength=1.0 - user_feedback)
        
        self._save_state()
    
    def _share_signal(self, swarm_id: str, signal_type: str, content: str, strength: float):
        """Share a learning signal with other swarms."""
        signal = SwarmSignal(
            source_swarm_id=swarm_id,
            signal_type=signal_type,
            content=content,
            strength=strength,
        )
        self._signals.append(signal)
        
        # Keep only recent signals
        if len(self._signals) > 50:
            self._signals = self._signals[-50:]
        
        # Other swarms can learn from this signal
        for other_id, other_swarm in self._swarms.items():
            if other_id != swarm_id and other_swarm.status == "active":
                if signal_type == "success":
                    other_swarm.learnings.append(f"Swarm {swarm_id[:4]} succeeded: {content[:100]}")
                elif signal_type == "failure":
                    other_swarm.learnings.append(f"Swarm {swarm_id[:4]} failed: {content[:100]}")
    
    # ── Competition Management ───────────────────────────────────────────────────
    
    def start_competition(self, swarm_ids: List[str], criteria: List[str] = None) -> str:
        """Start a competition between swarms to select the best mutation."""
        if not swarm_ids:
            return ""
        
        competition = Competition(
            swarms=swarm_ids,
            criteria=criteria or ["user_satisfaction", "effectiveness", "efficiency"],
        )
        
        self._competitions[competition.id] = competition
        self._active_competition = competition.id
        
        self._log_swarm({
            "event": "competition_started",
            "competition_id": competition.id,
            "swarms": swarm_ids,
            "criteria": criteria,
        })
        
        self._save_state()
        return competition.id
    
    def evaluate_competition(self, competition_id: str) -> Optional[Competition]:
        """Evaluate competition results and select a winner."""
        if competition_id not in self._competitions:
            return None
        
        competition = self._competitions[competition_id]
        
        # Calculate scores for each swarm
        results = {}
        for swarm_id in competition.swarms:
            if swarm_id in self._swarms:
                swarm = self._swarms[swarm_id]
                # Score based on collective performance and interaction count
                score = swarm.collective_score
                # Bonus for more interactions (more data)
                interaction_bonus = min(0.1, swarm.interactions_count * 0.01)
                results[swarm_id] = score + interaction_bonus
        
        competition.results = results
        
        # Select winner
        if results:
            winner_id = max(results.keys(), key=lambda k: results[k])
            competition.winner_swarm_id = winner_id
            competition.winning_mutation = self._swarms[winner_id].mutation
            competition.ended_at = datetime.now().isoformat()
            
            # Mark winner and losers
            self._swarms[winner_id].status = "winner"
            for swarm_id in competition.swarms:
                if swarm_id != winner_id:
                    self._swarms[swarm_id].status = "completed"
        
        self._active_competition = None
        self._save_state()
        
        self._log_swarm({
            "event": "competition_completed",
            "competition_id": competition_id,
            "winner": competition.winner_swarm_id,
            "results": results,
        })
        
        return competition
    
    # ── Swarm Intelligence ───────────────────────────────────────────────────────
    
    def optimize_swarm_allocation(self):
        """Dynamically reallocate agents based on swarm performance."""
        if not self._swarms:
            return
        
        # Sort swarms by performance
        sorted_swarms = sorted(
            self._swarms.items(),
            key=lambda x: x[1].collective_score,
            reverse=True
        )
        
        # Top performers get more agents, poor performers get fewer
        for i, (swarm_id, swarm) in enumerate(sorted_swarms):
            if swarm.status != "active":
                continue
            
            target_agents = self._agents_per_swarm
            
            # Top 2 get bonus agents
            if i < 2:
                target_agents += 1
            # Bottom 2 lose agents
            elif i >= len(sorted_swarms) - 2:
                target_agents = max(1, target_agents - 1)
            
            # Reallocate agents
            current_agents = len(swarm.agents)
            if current_agents < target_agents:
                # Add agents
                for _ in range(target_agents - current_agents):
                    agent = SwarmAgent(
                        role="validator",  # New agents start as validators
                        hypothesis_id=swarm.hypothesis_id,
                    )
                    swarm.agents.append(agent)
            elif current_agents > target_agents:
                # Remove agents (least active first)
                swarm.agents.sort(key=lambda a: a.interactions_count)
                swarm.agents = swarm.agents[:target_agents]
        
        self._save_state()
    
    def synthesize_learnings(self) -> str:
        """Synthesize learnings from all swarms into a unified insight."""
        if not self._swarms:
            return ""
        
        all_learnings = []
        for swarm in self._swarms.values():
            all_learnings.extend(swarm.learnings)
        
        if not all_learnings:
            return ""
        
        # Use LLM to synthesize
        try:
            llm = get_reasoning_llm()
            
            prompt = f"""Synthesize these swarm learnings into a unified insight:
{chr(10).join(f"- {l}" for l in all_learnings[:20])}

Provide:
1. Key patterns discovered
2. What worked well
3. What didn't work
4. Recommended next steps"""
            
            response = llm.invoke(prompt)
            return response
            
        except Exception as e:
            print(f"[SwarmEvolution] Synthesis error: {e}")
            return ""
    
    # ── Main Loop ─────────────────────────────────────────────────────────────────
    
    def start(self):
        """Start the swarm evolution background loop."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-SwarmEvolution"
        )
        self._thread.start()
        print("[SwarmEvolution] Started — swarm intelligence active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(180)  # Let other systems initialize
        
        while self._running:
            try:
                # Optimize agent allocation
                self.optimize_swarm_allocation()
                
                # Check if competition should be evaluated
                if self._active_competition:
                    comp = self._competitions[self._active_competition]
                    # Evaluate after 24 hours or when all swarms have enough data
                    time_since_start = (datetime.now() - datetime.fromisoformat(comp.started_at)).total_seconds()
                    min_interactions = min(
                        self._swarms[sid].interactions_count 
                        for sid in comp.swarms 
                        if sid in self._swarms
                    ) if comp.swarms else 0
                    
                    if time_since_start > 86400 or min_interactions >= 10:
                        self.evaluate_competition(self._active_competition)
                
                # ── EVALUATE ACTIVE SWARMS ──
                for s in list(self._swarms.values()):
                    if s.status == "active" and s.interactions_count >= 3:
                        score = s.collective_score
                        if score > 0.7:
                            from core.evolution_engine import EvolutionEngine
                            engine = EvolutionEngine()
                            engine.create_mutation(
                                mutation_type="swarm_validated",
                                description=f"Swarm-validated: {s.hypothesis[:60]}",
                                prompt_modification=s.hypothesis,
                                injection_point="system_suffix",
                            )
                            s.status = "winner"
                            print(f"[SwarmEvolution] Swarm {s.id} winner (score {score:.2f})")
                            try:
                                from core.master_orchestrator import get_orchestration_master
                                om = get_orchestration_master()
                                om._narrate("swarm_evolution", f"Swarm validated hypothesis (score {score:.2f})", "action")
                            except Exception:
                                pass
                        elif score < 0.3 and s.interactions_count >= 5:
                            s.status = "disbanded"
                            print(f"[SwarmEvolution] Disbanded swarm {s.id} (score {score:.2f})")
                
            except Exception as e:
                print(f"[SwarmEvolution] Loop error: {e}")
            
            time.sleep(300)  # Run every 5 minutes
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_active_swarms(self) -> List[Dict]:
        """Get information about currently active swarms."""
        return [
            {
                "id": s.id,
                "hypothesis": s.hypothesis,
                "strategy": s.strategy,
                "collective_score": s.collective_score,
                "interactions": s.interactions_count,
                "agents": len(s.agents),
                "status": s.status,
            }
            for s in self._swarms.values()
            if s.status == "active"
        ]
    
    def get_competition_status(self) -> Optional[Dict]:
        """Get status of the current competition."""
        if not self._active_competition:
            return None
        
        comp = self._competitions.get(self._active_competition)
        if not comp:
            return None
        
        return {
            "id": comp.id,
            "swarms": comp.swarms,
            "criteria": comp.criteria,
            "results": comp.results,
            "started_at": comp.started_at,
        }


# ── Singleton Access ─────────────────────────────────────────────────────────────

_swarm_evolution_instance: Optional[SwarmEvolutionEngine] = None
_swarm_lock = threading.Lock()


def get_swarm_evolution() -> SwarmEvolutionEngine:
    global _swarm_evolution_instance
    with _swarm_lock:
        if _swarm_evolution_instance is None:
            _swarm_evolution_instance = SwarmEvolutionEngine()
        return _swarm_evolution_instance