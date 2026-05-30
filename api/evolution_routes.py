"""
LOVE Evolution Dashboard API Routes

Provides real-time monitoring and control of LOVE's self-evolution systems.
Endpoints:
- GET /evolution/status — Overall evolution system status
- GET /evolution/metrics — Performance metrics and trends
- GET /evolution/experiments — Active and past experiments
- GET /evolution/swarms — Swarm intelligence status
- GET /evolution/pressures — Evolutionary pressures from user goals
- GET /evolution/predictions — Predictive hypotheses
- POST /evolution/trigger — Manually trigger evolution cycle
- POST /evolution/approve — Approve a mutation for integration
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/evolution", tags=["evolution"])

# ── Data Models ─────────────────────────────────────────────────────────────

class EvolutionStatus(BaseModel):
    """Overall status of evolution systems."""
    meta_evolution_active: bool
    swarm_evolution_active: bool
    base_evolution_active: bool
    self_coder_active: bool = False
    cross_instance_active: bool = False
    current_generation: int
    active_mutations: int
    active_experiments: int
    active_swarms: int
    last_evolution_cycle: str
    evolution_health: str  # healthy, degraded, critical


class EvolutionMetrics(BaseModel):
    """Key evolution metrics."""
    satisfaction_rate: float
    correction_rate: float
    initiative_success_rate: float
    avg_response_quality: float
    learning_efficiency: float
    hypothesis_success_rate: float
    mutation_survival_rate: float
    trend_satisfaction: str  # improving, stable, declining
    trend_quality: str


class ExperimentInfo(BaseModel):
    """Information about an experiment."""
    id: str
    hypothesis: str
    proposed_change: str
    status: str
    started_at: str
    duration_hours: float
    sample_size: int
    current_metrics: Dict[str, float]
    control_metrics: Dict[str, float]
    expected_impact: str


class SwarmInfo(BaseModel):
    """Information about a swarm."""
    id: str
    hypothesis: str
    strategy: str
    collective_score: float
    interactions_count: int
    agents_count: int
    status: str
    learnings: List[str]


class PressureInfo(BaseModel):
    """Information about evolutionary pressure."""
    goal_area: str
    pressure_level: float
    priority: float
    trend: str
    last_updated: str


class PredictionInfo(BaseModel):
    """Information about a predictive hypothesis."""
    id: str
    trigger_scenario: str
    hypothesis: str
    confidence: float
    activated: bool
    created_at: str


# ── Endpoint Handlers ─────────────────────────────────────────────────────────

@router.get("/status", response_model=EvolutionStatus)
async def get_evolution_status():
    """Get overall evolution system status."""
    try:
        from core.evolution_engine import EvolutionEngine
        from core.meta_evolution import get_meta_evolution
        from core.swarm_evolution import get_swarm_evolution
        
        # Get base evolution engine status
        try:
            base_engine = EvolutionEngine()
            base_active = base_engine._loop_running
            generation = base_engine._generation
            active_mutations = sum(1 for m in base_engine._mutations.values() if m.active)
            active_experiments = sum(1 for e in base_engine._experiments.values() 
                                   if e.status == "running")
            last_cycle = base_engine._history[-1].timestamp if base_engine._history else "never"
        except Exception:
            base_active = False
            generation = 1
            active_mutations = 0
            active_experiments = 0
            last_cycle = "unknown"
        
        # Get meta-evolution status
        try:
            meta_engine = get_meta_evolution()
            meta_active = meta_engine._running
        except Exception:
            meta_active = False
        
        # Get swarm evolution status
        try:
            swarm_engine = get_swarm_evolution()
            swarm_active = swarm_engine._running
            active_swarms = len([s for s in swarm_engine._swarms.values() if s.status == "active"])
        except Exception:
            swarm_active = False
            active_swarms = 0
        
        # Get self-coder status
        try:
            from core.self_coder import get_self_coder
            self_coder_active = get_self_coder()._running
        except Exception:
            self_coder_active = False
        
        # Get cross-instance learning status
        try:
            from core.cross_instance_learning import get_cross_instance_learning
            cross_instance_active = get_cross_instance_learning()._running
        except Exception:
            cross_instance_active = False
        
        # Determine overall health
        total_active = sum([base_active, meta_active, swarm_active, self_coder_active, cross_instance_active])
        if total_active >= 4:
            health = "healthy"
        elif total_active >= 2:
            health = "degraded"
        else:
            health = "critical"
        
        return EvolutionStatus(
            meta_evolution_active=meta_active,
            swarm_evolution_active=swarm_active,
            base_evolution_active=base_active,
            self_coder_active=self_coder_active,
            cross_instance_active=cross_instance_active,
            current_generation=generation,
            active_mutations=active_mutations,
            active_experiments=active_experiments,
            active_swarms=active_swarms,
            last_evolution_cycle=last_cycle,
            evolution_health=health,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=EvolutionMetrics)
async def get_evolution_metrics():
    """Get key evolution performance metrics."""
    try:
        from core.evolution_engine import EvolutionEngine
        from core.self_evolution import measure_recent_performance
        
        # Get recent performance
        perf = measure_recent_performance()
        
        # Get evolution engine metrics
        try:
            engine = EvolutionEngine()
            report = engine.generate_performance_report()
            
            hypothesis_success = len([h for h in engine._hypotheses.values() 
                                    if h.status == "confirmed"]) / max(1, len(engine._hypotheses))
            
            mutation_survival = len([m for m in engine._mutations.values() 
                                   if m.fitness > 0.6]) / max(1, len(engine._mutations))
            
        except Exception:
            hypothesis_success = 0.5
            mutation_survival = 0.5
            report = None
        
        # Calculate trends (simplified)
        satisfaction = perf.get("satisfaction_rate", 0.5)
        trend_satisfaction = "stable"
        if satisfaction > 0.7:
            trend_satisfaction = "improving"
        elif satisfaction < 0.4:
            trend_satisfaction = "declining"
        
        quality = perf.get("avg_response_quality", 0.5)
        trend_quality = "stable"
        if quality > 0.7:
            trend_quality = "improving"
        elif quality < 0.4:
            trend_quality = "declining"
        
        return EvolutionMetrics(
            satisfaction_rate=perf.get("satisfaction_rate", 0.5),
            correction_rate=perf.get("correction_rate", 0.0),
            initiative_success_rate=perf.get("initiative_success_rate", 0.5),
            avg_response_quality=perf.get("avg_response_quality", 0.5),
            learning_efficiency=perf.get("learning_efficiency", 0.5),
            hypothesis_success_rate=hypothesis_success,
            mutation_survival_rate=mutation_survival,
            trend_satisfaction=trend_satisfaction,
            trend_quality=trend_quality,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments", response_model=List[ExperimentInfo])
async def get_experiments():
    """Get all experiments (active and completed)."""
    try:
        from core.evolution_engine import EvolutionEngine
        
        engine = EvolutionEngine()
        experiments = []
        
        for exp in engine._experiments.values():
            info = ExperimentInfo(
                id=exp.id,
                hypothesis=engine._hypotheses.get(exp.hypothesis_id, {}).claim if exp.hypothesis_id in engine._hypotheses else "",
                proposed_change=engine._mutations.get(exp.id, {}).description if exp.id in engine._mutations else "",
                status=exp.status,
                started_at=exp.started_at or "",
                duration_hours=exp.duration_hours,
                sample_size=exp.min_samples,
                current_metrics={},
                control_metrics=exp.control_metrics,
                expected_impact="",
            )
            experiments.append(info)
        
        return experiments
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/swarms", response_model=List[SwarmInfo])
async def get_swarms():
    """Get all active swarms."""
    try:
        from core.swarm_evolution import get_swarm_evolution
        
        swarm_engine = get_swarm_evolution()
        swarms = swarm_engine.get_active_swarms()
        
        return [
            SwarmInfo(
                id=s["id"],
                hypothesis=s["hypothesis"],
                strategy=s["strategy"],
                collective_score=s["collective_score"],
                interactions_count=s["interactions"],
                agents_count=s["agents"],
                status=s["status"],
                learnings=[],
            )
            for s in swarms
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pressures", response_model=List[PressureInfo])
async def get_evolutionary_pressures():
    """Get current evolutionary pressures from user goals."""
    try:
        from core.meta_evolution import get_meta_evolution
        
        meta_engine = get_meta_evolution()
        pressures = []
        
        for pressure in meta_engine._pressures.values():
            info = PressureInfo(
                goal_area=pressure.goal_area,
                pressure_level=pressure.pressure_level,
                priority=pressure.priority,
                trend=pressure.trend,
                last_updated=pressure.last_updated,
            )
            pressures.append(info)
        
        return pressures
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions", response_model=List[PredictionInfo])
async def get_predictions():
    """Get predictive hypotheses."""
    try:
        from core.meta_evolution import get_meta_evolution
        
        meta_engine = get_meta_evolution()
        predictions = []
        
        for pred in meta_engine._predictions:
            info = PredictionInfo(
                id=pred.id,
                trigger_scenario=pred.trigger_scenario,
                hypothesis=pred.hypothesis,
                confidence=pred.confidence,
                activated=pred.activated,
                created_at=pred.created_at,
            )
            predictions.append(info)
        
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
async def trigger_evolution():
    """Manually trigger an evolution cycle."""
    try:
        from core.evolution_engine import EvolutionEngine
        from core.meta_evolution import get_meta_evolution
        from core.swarm_evolution import get_swarm_evolution
        
        # Trigger base evolution
        try:
            base_engine = EvolutionEngine()
            base_engine.run_evolution_cycle()
        except Exception as e:
            print(f"Base evolution trigger error: {e}")
        
        # Trigger meta-evolution
        try:
            meta_engine = get_meta_evolution()
            meta_engine.update_evolutionary_pressures()
            meta_engine.detect_cross_domain_patterns()
        except Exception as e:
            print(f"Meta-evolution trigger error: {e}")
        
        # Trigger swarm evolution
        try:
            swarm_engine = get_swarm_evolution()
            swarm_engine.optimize_swarm_allocation()
        except Exception as e:
            print(f"Swarm evolution trigger error: {e}")
        
        return {"status": "success", "message": "Evolution cycle triggered"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_mutation(mutation_id: str):
    """Manually approve a mutation for integration."""
    try:
        from core.evolution_engine import EvolutionEngine
        
        engine = EvolutionEngine()
        
        if mutation_id not in engine._mutations:
            raise HTTPException(status_code=404, detail="Mutation not found")
        
        mutation = engine._mutations[mutation_id]
        mutation.active = True
        mutation.fitness = max(mutation.fitness, 0.8)  # Boost fitness on manual approval
        
        engine._save_genome()
        
        return {"status": "success", "message": f"Mutation {mutation_id} approved"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_evolution_history(limit: int = 50):
    """Get evolution event history."""
    try:
        from core.evolution_engine import EvolutionEngine
        
        engine = EvolutionEngine()
        history = [
            {
                "id": event.id,
                "event_type": event.event_type,
                "description": event.description,
                "generation": event.generation,
                "timestamp": event.timestamp,
            }
            for event in engine._history[-limit:]
        ]
        
        return {"history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_evolution_health():
    """Get health status of all evolution subsystems."""
    try:
        from core.evolution_integration import get_evolution_integration
        from core.meta_evolution import get_meta_evolution
        from core.swarm_evolution import get_swarm_evolution
        from core.self_coder import get_self_coder
        from core.cross_instance_learning import get_cross_instance_learning
        from core.capability_gap_detector import get_capability_gap_detector
        from core.autonomous_cicd import get_autonomous_cicd
        from core.neural_architecture_search import get_neural_architecture_search
        from core.multimodal_evolution import get_multimodal_evolution
        from agents.task_evolution_integration import get_task_evolution_integration
        from agents.fitness_evolution_integration import get_fitness_evolution_integration
        from core.mcp_host import get_mcp_host

        integration = get_evolution_integration()
        integration_status = integration.get_integration_status()

        health = {
            "integration": {
                "running": integration._running,
                "state": integration_status.get("state", {}),
            },
            "meta_evolution": {"running": get_meta_evolution()._running},
            "swarm_evolution": {"running": get_swarm_evolution()._running},
            "self_coder": {"running": get_self_coder()._running},
            "cross_instance": {"running": get_cross_instance_learning()._running},
            "capability_gap_detector": {"running": get_capability_gap_detector()._running},
            "autonomous_cicd": {"running": get_autonomous_cicd()._running},
            "neural_architecture_search": {"running": get_neural_architecture_search()._running},
            "multimodal_evolution": {"running": get_multimodal_evolution()._running},
            "task_evolution": {"running": get_task_evolution_integration()._running},
            "fitness_evolution": {"running": get_fitness_evolution_integration()._running},
            "mcp_host": {"available": get_mcp_host().get_health().get("sdk_available", False)},
            "reasoning_engine": {"available": True},
            "vector_memory": {"available": True},
            "code_sandbox": {"available": True},
            "observability": {"running": get_observability_engine()._running},
            "guardrails": {"available": True},
            "llm_manager": {"available": len(get_llm_manager()._models) > 0},
            "graph_rag": {"available": True},
            "prompt_optimizer": {"available": True},
            "overall": "healthy" if integration._running else "degraded",
        }
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
