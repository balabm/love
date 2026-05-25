"""
LOVE Neural Mesh API Routes - Wave 16
All endpoints for the self-evolving intelligence ecosystem.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/neural", tags=["neural-mesh"])


# ── Request Models ───────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    topic: str
    question: str
    priority: str = "medium"  # urgent, high, medium, low, ambient
    source: str = "user"
    max_depth: int = 3
    teach_user: bool = True


class MonitorTopicRequest(BaseModel):
    topic: str
    keywords: List[str]
    relevance: str
    check_interval_hours: int = 24


class EvolvePromptRequest(BaseModel):
    category: str
    content: str
    reason: str


class BehaviorRuleRequest(BaseModel):
    rule_name: str
    condition: str
    action: str
    reason: str


class DeviceRegisterRequest(BaseModel):
    device_id: str
    name: str
    role: str
    capabilities: List[str]
    ip_address: str = ""
    os_type: str = ""


class DeviceHeartbeatRequest(BaseModel):
    device_id: str
    battery: Optional[float] = None
    cpu_usage: Optional[float] = None
    current_activity: str = "idle"
    user_present: bool = False
    context: Dict[str, Any] = {}


class CommandRequest(BaseModel):
    target_device: str
    command_type: str
    payload: Dict[str, Any] = {}
    priority: int = 2


class NotifyRequest(BaseModel):
    message: str
    priority: int = 2
    prefer_device: Optional[str] = None


class TeachingReactionRequest(BaseModel):
    lesson_id: str
    reaction: str = "neutral"  # positive, neutral, negative


class UserInterestsRequest(BaseModel):
    interests: List[str]


# ── Wave 17 Request Models ──────────────────────────────────────────────────

class DilemmaRequest(BaseModel):
    situation: str
    options: List[str]

class PrincipleProposalRequest(BaseModel):
    text: str
    category: str
    evidence: str
    reasoning: str

class MemorySearchRequest(BaseModel):
    query: str
    tiers: List[str] = ["all"]
    limit: int = 10

class EvolutionExperimentRequest(BaseModel):
    hypothesis_id: str


# ── Neural Bus Endpoints ─────────────────────────────────────────────────────

@router.get("/events")
async def get_neural_events(limit: int = 20, domain: str = None, since: int = 3600):
    """Get recent neural bus events."""
    try:
        from core.neural_bus import get_neural_bus
        bus = get_neural_bus()
        events = bus.get_recent_events(domain=domain, limit=limit, since_seconds=since)
        return {"events": events, "total": len(events)}
    except Exception as e:
        return {"events": [], "error": str(e)}


@router.get("/bus/stats")
async def get_bus_stats():
    """Get neural bus statistics."""
    try:
        from core.neural_bus import get_neural_bus
        bus = get_neural_bus()
        return bus.get_stats()
    except Exception as e:
        return {"error": str(e)}


@router.get("/patterns")
async def get_neural_patterns():
    """Get detected event patterns."""
    try:
        from core.neural_bus import get_neural_bus
        bus = get_neural_bus()
        return {"patterns": bus.get_patterns(min_count=2)}
    except Exception as e:
        return {"patterns": [], "error": str(e)}


@router.get("/causal/{event_id}")
async def get_causal_chain(event_id: str):
    """Get the causal chain for an event."""
    try:
        from core.neural_bus import get_neural_bus
        bus = get_neural_bus()
        return bus.get_causal_chain(event_id)
    except Exception as e:
        return {"error": str(e)}


# ── Research Engine Endpoints ────────────────────────────────────────────────

@router.get("/research/status")
async def get_research_status():
    """Get research engine status."""
    try:
        from core.research_engine import get_research_engine
        engine = get_research_engine()
        return engine.get_status()
    except Exception as e:
        return {"error": str(e)}


@router.post("/research/add")
async def add_research_task(req: ResearchRequest):
    """Add a research task to the queue."""
    try:
        from core.research_engine import get_research_engine, ResearchPriority
        engine = get_research_engine()

        priority_map = {
            "urgent": ResearchPriority.URGENT,
            "high": ResearchPriority.HIGH,
            "medium": ResearchPriority.MEDIUM,
            "low": ResearchPriority.LOW,
            "ambient": ResearchPriority.AMBIENT,
        }
        priority = priority_map.get(req.priority, ResearchPriority.MEDIUM)

        task_id = engine.add_research_task(
            topic=req.topic,
            question=req.question,
            priority=priority,
            source=req.source,
            max_depth=req.max_depth,
            teach_user=req.teach_user,
        )
        return {"success": True, "task_id": task_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/research/execute")
async def execute_research():
    """Execute the next research task in queue."""
    try:
        from core.research_engine import get_research_engine
        engine = get_research_engine()
        result = engine.execute_next_task()
        if result:
            return {"success": True, "result": result}
        return {"success": False, "message": "No tasks in queue"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/research/monitor")
async def add_monitored_topic(req: MonitorTopicRequest):
    """Add a topic for continuous monitoring."""
    try:
        from core.research_engine import get_research_engine
        engine = get_research_engine()
        topic_id = engine.add_monitored_topic(
            topic=req.topic,
            keywords=req.keywords,
            relevance=req.relevance,
            check_interval_hours=req.check_interval_hours,
        )
        return {"success": True, "topic_id": topic_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/research/knowledge")
async def get_knowledge(topic: str = None, tag: str = None):
    """Get acquired knowledge entries."""
    try:
        from core.research_engine import get_research_engine
        engine = get_research_engine()
        entries = engine.get_knowledge(topic=topic, tag=tag)
        return {"entries": entries, "total": len(entries)}
    except Exception as e:
        return {"entries": [], "error": str(e)}


# ── Self-Builder Endpoints ───────────────────────────────────────────────────

@router.get("/builder/status")
async def get_builder_status():
    """Get self-builder status."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.get_status()
    except Exception as e:
        return {"error": str(e)}


@router.get("/growth")
async def get_growth_summary(days: int = 7):
    """Get LOVE's growth summary over the past N days."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.get_growth_summary(days=days)
    except Exception as e:
        return {"error": str(e)}


@router.post("/builder/evolve-prompt")
async def evolve_prompt(req: EvolvePromptRequest):
    """Evolve a prompt gene."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.evolve_prompt(req.category, req.content, req.reason)
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/builder/add-rule")
async def add_behavior_rule(req: BehaviorRuleRequest):
    """Add a learned behavior rule."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.add_behavior_rule(req.rule_name, req.condition, req.action, req.reason)
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/builder/rules")
async def get_learned_rules():
    """Get all active behavior rules."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return {"rules": builder.get_active_rules()}
    except Exception as e:
        return {"rules": [], "error": str(e)}


@router.get("/builder/approvals")
async def get_pending_approvals():
    """Get modifications waiting for user approval."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return {"approvals": builder.get_pending_approvals()}
    except Exception as e:
        return {"approvals": [], "error": str(e)}


@router.post("/builder/approve/{mod_id}")
async def approve_modification(mod_id: str):
    """Approve a pending modification."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.approve_modification(mod_id)
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/builder/reject/{mod_id}")
async def reject_modification(mod_id: str):
    """Reject a pending modification."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.reject_modification(mod_id)
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/builder/rollback")
async def rollback_last():
    """Rollback the last modification."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.rollback_last()
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/builder/evolve-cycle")
async def run_evolution_cycle():
    """Run one self-evolution cycle."""
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        return builder.run_evolution_cycle()
    except Exception as e:
        return {"error": str(e)}


# ── Teaching Engine Endpoints ────────────────────────────────────────────────

@router.get("/teaching/status")
async def get_teaching_status():
    """Get teaching engine status."""
    try:
        from core.teaching_engine import get_teaching_engine
        engine = get_teaching_engine()
        return engine.get_status()
    except Exception as e:
        return {"error": str(e)}


@router.get("/teaching/next")
async def get_next_lesson(context: str = ""):
    """Get the next lesson to deliver."""
    try:
        from core.teaching_engine import get_teaching_engine
        engine = get_teaching_engine()
        lesson = engine.get_next_lesson(context=context)
        return {"lesson": lesson}
    except Exception as e:
        return {"lesson": None, "error": str(e)}


@router.post("/teaching/delivered")
async def mark_lesson_delivered(req: TeachingReactionRequest):
    """Mark a lesson as delivered and record reaction."""
    try:
        from core.teaching_engine import get_teaching_engine
        engine = get_teaching_engine()
        engine.mark_delivered(req.lesson_id, req.reaction)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/teaching/briefing")
async def get_morning_briefing():
    """Get the morning briefing."""
    try:
        from core.teaching_engine import get_teaching_engine
        engine = get_teaching_engine()
        return engine.generate_morning_briefing()
    except Exception as e:
        return {"error": str(e)}


@router.post("/teaching/interests")
async def update_user_interests(req: UserInterestsRequest):
    """Update user's learning interests."""
    try:
        from core.teaching_engine import get_teaching_engine
        engine = get_teaching_engine()
        engine.update_user_interests(req.interests)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/teaching/gaps")
async def get_knowledge_gaps():
    """Get user's knowledge gaps."""
    try:
        from core.teaching_engine import get_teaching_engine
        engine = get_teaching_engine()
        return {"gaps": engine.get_user_knowledge_gaps()}
    except Exception as e:
        return {"gaps": [], "error": str(e)}


# ── Ecosystem Controller Endpoints ──────────────────────────────────────────

@router.get("/ecosystem")
async def get_ecosystem_status():
    """Get full ecosystem status."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        return controller.get_ecosystem_status()
    except Exception as e:
        return {"error": str(e)}


@router.post("/ecosystem/register")
async def register_ecosystem_device(req: DeviceRegisterRequest):
    """Register a device in the ecosystem."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        return controller.register_device(
            device_id=req.device_id,
            name=req.name,
            role=req.role,
            capabilities=req.capabilities,
            ip_address=req.ip_address,
            os_type=req.os_type,
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/ecosystem/heartbeat")
async def ecosystem_heartbeat(req: DeviceHeartbeatRequest):
    """Send device heartbeat with state update."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        return controller.heartbeat(req.device_id, {
            "battery": req.battery,
            "cpu_usage": req.cpu_usage,
            "current_activity": req.current_activity,
            "user_present": req.user_present,
            "context": req.context,
        })
    except Exception as e:
        return {"error": str(e)}


@router.get("/ecosystem/presence")
async def get_user_presence():
    """Get user's current presence across devices."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        return controller.get_user_presence()
    except Exception as e:
        return {"error": str(e)}


@router.post("/ecosystem/command")
async def send_device_command(req: CommandRequest):
    """Send a command to a device."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        cmd_id = controller.send_command(
            target_device=req.target_device,
            command_type=req.command_type,
            payload=req.payload,
            priority=req.priority,
        )
        return {"success": True, "command_id": cmd_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/ecosystem/notify")
async def notify_user(req: NotifyRequest):
    """Send a notification to the user on the best device."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        cmd_id = controller.notify_user(req.message, req.priority, req.prefer_device)
        return {"success": True, "command_id": cmd_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/ecosystem/health")
async def get_device_health():
    """Get health status of all devices."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        return {"devices": controller.get_device_health()}
    except Exception as e:
        return {"devices": [], "error": str(e)}


@router.get("/ecosystem/route/{action}")
async def route_action(action: str):
    """Find best device for an action."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        return controller.route_action(action)
    except Exception as e:
        return {"routed": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE 17: COGNITIVE EVOLUTION ARCHITECTURE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


# ── Cognitive Architecture Endpoints ────────────────────────────────────────

@router.get("/cognitive/stats")
async def get_cognitive_stats():
    """Get reasoning strategy performance stats."""
    try:
        from core.cognitive_architecture import get_cognitive_architecture
        cog = get_cognitive_architecture()
        return {
            "strategy_stats": cog.get_reasoning_stats(),
            "health": cog.get_cognitive_health(),
            "recent_learnings": cog.get_recent_learnings(limit=10),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/cognitive/health")
async def get_cognitive_health():
    """Get cognitive system health metrics."""
    try:
        from core.cognitive_architecture import get_cognitive_architecture
        cog = get_cognitive_architecture()
        return cog.get_cognitive_health()
    except Exception as e:
        return {"error": str(e)}


@router.post("/cognitive/classify")
async def classify_query(query: str):
    """Classify a query and get routing recommendation."""
    try:
        from core.cognitive_architecture import get_cognitive_architecture
        cog = get_cognitive_architecture()
        routing = cog.classify_and_route(query)
        return {
            "category": routing.category.value if hasattr(routing.category, 'value') else str(routing.category),
            "confidence": routing.confidence,
            "recommended_strategy": routing.recommended_strategy.value if hasattr(routing.recommended_strategy, 'value') else str(routing.recommended_strategy),
            "recommended_budget": routing.recommended_budget.value if hasattr(routing.recommended_budget, 'value') else str(routing.recommended_budget),
        }
    except Exception as e:
        return {"error": str(e)}


# ── Constitution Endpoints ──────────────────────────────────────────────────

@router.get("/constitution")
async def get_constitution_status():
    """Get constitution and principles overview."""
    try:
        from core.constitution import get_constitution
        c = get_constitution()
        return {
            "stats": c.get_stats(),
            "health": c.get_principle_health(),
            "character": c.get_character_prompt(),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/constitution/principles")
async def get_principles(category: str = None):
    """Get all principles or filter by category."""
    try:
        from core.constitution import get_constitution
        c = get_constitution()
        if category:
            principles = c.get_principles_by_category(category)
        else:
            principles = c.principles
        return {"principles": [p.to_dict() for p in principles]}
    except Exception as e:
        return {"principles": [], "error": str(e)}


@router.post("/constitution/critique")
async def critique_response_api(response: str, query: str):
    """Run constitutional critique on a response."""
    try:
        from core.constitution import get_constitution
        c = get_constitution()
        result = c.critique_response(response, query, "")
        return result.to_dict() if result else {"score": 1.0, "violations": []}
    except Exception as e:
        return {"error": str(e)}


@router.post("/constitution/dilemma")
async def reason_dilemma(req: DilemmaRequest):
    """Reason through an ethical dilemma."""
    try:
        from core.constitution import get_constitution
        c = get_constitution()
        analysis = c.reason_about_dilemma(req.situation, req.options)
        return analysis.to_dict() if analysis else {"error": "Could not analyze"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/constitution/drift")
async def get_drift_status():
    """Check for value drift."""
    try:
        from core.constitution import get_constitution
        c = get_constitution()
        report = c.check_drift([])
        return report.to_dict() if report else {"drift_score": 0.0}
    except Exception as e:
        return {"error": str(e)}


@router.post("/constitution/propose")
async def propose_principle(req: PrincipleProposalRequest):
    """Propose a new principle for LOVE's constitution."""
    try:
        from core.constitution import get_constitution
        c = get_constitution()
        proposal = c.propose_principle_update(req.evidence, req.reasoning)
        if proposal:
            approved = c.evaluate_proposal(proposal)
            if approved:
                c.adopt_principle(proposal)
                return {"success": True, "adopted": True, "principle": proposal.to_dict()}
            return {"success": True, "adopted": False, "reason": "Did not pass evaluation"}
        return {"success": False, "error": "Could not generate proposal"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Evolution Engine Endpoints ──────────────────────────────────────────────

@router.get("/evolution")
async def get_evolution_status():
    """Get evolution engine status and genome."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        return {
            "status": evo.get_status(),
            "generation": evo.get_generation(),
            "genome": evo.get_current_genome(),
            "active_mutations": [vars(m) if hasattr(m, '__dict__') else m for m in evo.get_active_mutations()],
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/evolution/metrics")
async def get_evolution_metrics(window: str = "24h"):
    """Get performance metrics for evolution."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        report = evo.get_performance_metrics(window=window)
        return vars(report) if hasattr(report, '__dict__') else report
    except Exception as e:
        return {"error": str(e)}


@router.get("/evolution/history")
async def get_evolution_history_api(limit: int = 50):
    """Get evolution history."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        history = evo.get_evolution_history(limit=limit)
        return {"history": [vars(h) if hasattr(h, '__dict__') else h for h in history]}
    except Exception as e:
        return {"history": [], "error": str(e)}


@router.get("/evolution/narrative")
async def get_evolution_narrative(period: str = "30d"):
    """Get human-readable evolution story."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        return {"narrative": evo.explain_evolution(period=period)}
    except Exception as e:
        return {"narrative": "Evolution story unavailable.", "error": str(e)}


@router.post("/evolution/hypothesize")
async def generate_hypotheses():
    """Generate improvement hypotheses."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        hypotheses = evo.generate_hypotheses()
        return {"hypotheses": [vars(h) if hasattr(h, '__dict__') else h for h in hypotheses]}
    except Exception as e:
        return {"hypotheses": [], "error": str(e)}


@router.post("/evolution/experiment")
async def start_experiment(req: EvolutionExperimentRequest):
    """Create and start an experiment from a hypothesis."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        exp = evo.create_experiment(req.hypothesis_id)
        if exp:
            evo.run_experiment(exp.id if hasattr(exp, 'id') else exp)
            return {"success": True, "experiment": vars(exp) if hasattr(exp, '__dict__') else exp}
        return {"success": False, "error": "Could not create experiment"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/evolution/gaps")
async def get_capability_gaps():
    """Get identified capability gaps."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        gaps = evo.identify_gaps()
        return {"gaps": [vars(g) if hasattr(g, '__dict__') else g for g in gaps]}
    except Exception as e:
        return {"gaps": [], "error": str(e)}


@router.get("/evolution/priorities")
async def get_improvement_priorities():
    """Get prioritized improvement list."""
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        return {"priorities": evo.get_improvement_priorities()}
    except Exception as e:
        return {"priorities": [], "error": str(e)}


# ── Memory Architect Endpoints ──────────────────────────────────────────────

@router.get("/memory")
async def get_memory_status():
    """Get memory system status."""
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        stats = ma.get_memory_stats()
        return {
            "total": stats.total,
            "per_tier": stats.per_tier,
            "consolidation_health": stats.consolidation_health,
            "oldest": stats.oldest,
            "newest": stats.newest,
            "avg_stability": stats.avg_stability,
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/memory/search")
async def search_memory(req: MemorySearchRequest):
    """Search across all memory tiers."""
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        results = ma.search(req.query, memory_tiers=req.tiers, limit=req.limit)
        return {"results": [r.to_dict() if hasattr(r, 'to_dict') else vars(r) for r in results]}
    except Exception as e:
        return {"results": [], "error": str(e)}


@router.get("/memory/wisdom")
async def get_wisdom(topic: str = None):
    """Get crystallized wisdom."""
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        if topic:
            wisdom = ma.get_wisdom(topic)
        else:
            wisdom = ma.extract_wisdom()
        return {"wisdom": [w.to_dict() if hasattr(w, 'to_dict') else vars(w) for w in wisdom]}
    except Exception as e:
        return {"wisdom": [], "error": str(e)}


@router.get("/memory/dying")
async def get_dying_memories():
    """Get memories about to be forgotten."""
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        dying = ma.get_dying_memories()
        return {"dying": [d.to_dict() if hasattr(d, 'to_dict') else vars(d) for d in dying]}
    except Exception as e:
        return {"dying": [], "error": str(e)}


@router.post("/memory/consolidate")
async def trigger_consolidation():
    """Trigger manual memory consolidation."""
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        ma.consolidate(force=True)
        return {"success": True, "message": "Memory consolidation completed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/memory/issues")
async def get_memory_issues():
    """Detect memory health issues."""
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        issues = ma.detect_memory_issues()
        return {"issues": [vars(i) if hasattr(i, '__dict__') else i for i in issues]}
    except Exception as e:
        return {"issues": [], "error": str(e)}


@router.get("/memory/connections")
async def find_connections(topic: str):
    """Find unexpected memory connections."""
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        connections = ma.find_unexpected_connections(topic)
        return {"connections": connections}
    except Exception as e:
        return {"connections": [], "error": str(e)}


# ── Metacognitive Monitor Endpoints ─────────────────────────────────────────

@router.get("/metacognition")
async def get_metacognition_status():
    """Get full metacognitive state."""
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        return {
            "load": vars(meta.get_current_load()) if meta.get_current_load() else None,
            "weakness": meta.identify_weakness(),
            "strength": meta.identify_strength(),
            "strategy_report": meta.get_strategy_report(),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/metacognition/report")
async def get_self_report(detail: str = "summary"):
    """Get LOVE's self-assessment report."""
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        return {"report": meta.generate_self_report(detail=detail)}
    except Exception as e:
        return {"report": "Self-report unavailable.", "error": str(e)}


@router.get("/metacognition/growth")
async def get_growth_story():
    """Get LOVE's growth narrative."""
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        return {"narrative": meta.get_growth_narrative()}
    except Exception as e:
        return {"narrative": "Growth narrative unavailable.", "error": str(e)}


@router.get("/metacognition/calibration")
async def get_calibration(domain: str = None):
    """Get confidence calibration data."""
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        curve = meta.get_calibration_curve(domain=domain)
        return {"calibration": curve}
    except Exception as e:
        return {"calibration": {}, "error": str(e)}


@router.get("/metacognition/performance")
async def get_performance_trend(window: str = "7d"):
    """Get performance trends over time."""
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        return {"trends": meta.get_performance_trend(window=window)}
    except Exception as e:
        return {"trends": {}, "error": str(e)}


@router.get("/metacognition/plateaus")
async def get_learning_plateaus():
    """Detect learning plateaus."""
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        return {"plateaus": meta.detect_plateaus()}
    except Exception as e:
        return {"plateaus": [], "error": str(e)}


@router.get("/metacognition/anomalies")
async def detect_anomalies():
    """Check for behavioral anomalies."""
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        anomaly = meta.detect_behavioral_anomaly(None)
        if anomaly:
            return {"anomaly_detected": True, "report": vars(anomaly) if hasattr(anomaly, '__dict__') else anomaly}
        return {"anomaly_detected": False}
    except Exception as e:
        return {"error": str(e)}


# ── Unified Intelligence Dashboard ─────────────────────────────────────────

@router.get("/intelligence")
async def get_intelligence_dashboard():
    """Get complete intelligence overview — all Wave 16+17 systems."""
    result = {
        "wave16": {},
        "wave17": {},
        "overall_health": "unknown",
    }

    # Wave 16 systems
    try:
        from core.neural_bus import get_neural_bus
        result["wave16"]["neural_bus"] = get_neural_bus().get_stats()
    except Exception:
        result["wave16"]["neural_bus"] = None
    try:
        from core.research_engine import get_research_engine
        result["wave16"]["research"] = get_research_engine().get_status()
    except Exception:
        result["wave16"]["research"] = None
    try:
        from core.teaching_engine import get_teaching_engine
        result["wave16"]["teaching"] = get_teaching_engine().get_status()
    except Exception:
        result["wave16"]["teaching"] = None
    try:
        from core.self_builder import get_self_builder
        result["wave16"]["self_builder"] = get_self_builder().get_status()
    except Exception:
        result["wave16"]["self_builder"] = None
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        result["wave16"]["ecosystem"] = get_ecosystem_controller().get_ecosystem_status()
    except Exception:
        result["wave16"]["ecosystem"] = None

    # Wave 17 systems
    try:
        from core.cognitive_architecture import get_cognitive_architecture
        result["wave17"]["cognitive"] = get_cognitive_architecture().get_cognitive_health()
    except Exception:
        result["wave17"]["cognitive"] = None
    try:
        from core.constitution import get_constitution
        result["wave17"]["constitution"] = get_constitution().get_stats()
    except Exception:
        result["wave17"]["constitution"] = None
    try:
        from core.evolution_engine import get_evolution_engine
        result["wave17"]["evolution"] = get_evolution_engine().get_status()
    except Exception:
        result["wave17"]["evolution"] = None
    try:
        from core.memory_architect import get_memory_architect
        stats = get_memory_architect().get_memory_stats()
        result["wave17"]["memory"] = {"total": stats.total, "per_tier": stats.per_tier, "health": stats.consolidation_health}
    except Exception:
        result["wave17"]["memory"] = None
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        result["wave17"]["metacognition"] = {
            "load": vars(meta.get_current_load()) if meta.get_current_load() else None,
            "weakness": meta.identify_weakness(),
            "strength": meta.identify_strength(),
        }
    except Exception:
        result["wave17"]["metacognition"] = None

    # Overall health
    active_w16 = sum(1 for v in result["wave16"].values() if v is not None)
    active_w17 = sum(1 for v in result["wave17"].values() if v is not None)
    total = active_w16 + active_w17
    result["overall_health"] = "excellent" if total >= 8 else "good" if total >= 5 else "degraded" if total >= 3 else "critical"
    result["systems_online"] = total
    result["systems_total"] = 10

    return result


# ── Proactive Push Routes ────────────────────────────────────────────────────

@router.get("/push/pending")
async def get_pending_pushes(limit: int = 10):
    """Get pending proactive messages LOVE wants to send."""
    try:
        from core.proactive_push import get_push_engine
        engine = get_push_engine()
        return {"pending": engine.get_pending(limit), "count": len(engine.get_pending(limit))}
    except Exception as e:
        return {"error": str(e)}


@router.get("/push/history")
async def get_push_history(limit: int = 50):
    """Get history of proactive messages LOVE has sent."""
    try:
        from core.proactive_push import get_push_engine
        engine = get_push_engine()
        return {"history": engine.get_history(limit)}
    except Exception as e:
        return {"error": str(e)}


@router.post("/push/trigger")
async def trigger_push_scan():
    """Manually trigger a proactive push scan."""
    try:
        from core.proactive_push import get_push_engine
        engine = get_push_engine()
        engine._run_scan()
        return {"status": "scan triggered", "pending": len(engine.get_pending())}
    except Exception as e:
        return {"error": str(e)}


# ── Autonomous Goal Engine Routes ────────────────────────────────────────────

@router.get("/goals")
async def get_goals_status():
    """Get all active goals and their autonomous execution status."""
    try:
        from core.autonomous_goal_engine import get_goal_status
        return get_goal_status()
    except Exception as e:
        return {"error": str(e)}


@router.post("/goals/add")
async def add_goal_endpoint(request: Request):
    """Add a new goal for LOVE to autonomously pursue."""
    try:
        body = await request.json()
        from core.autonomous_goal_engine import add_goal
        goal = add_goal(
            title=body.get("title", ""),
            description=body.get("description", ""),
            category=body.get("category", "personal"),
            priority=body.get("priority", "medium"),
            target_date=body.get("target_date"),
        )
        from dataclasses import asdict
        return {"success": True, "goal": asdict(goal)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/goals/run_cycle")
async def trigger_goal_cycle():
    """Manually trigger one goal execution cycle."""
    try:
        from core.autonomous_goal_engine import run_goal_cycle
        result = run_goal_cycle()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Integrations Status Routes ───────────────────────────────────────────────

# What env key is required for each integration to be considered "configured"
_INTEGRATION_CONFIG = {
    "system":    {"label": "System",    "icon": "▣",  "always_on": True,  "env_keys": [], "description": "CPU, battery, active window"},
    "browser":   {"label": "Browser",   "icon": "◉",  "always_on": True,  "env_keys": [], "description": "Active tabs via Chrome DevTools Protocol"},
    "clipboard": {"label": "Clipboard", "icon": "◻",  "always_on": True,  "env_keys": [], "description": "Clipboard pattern detection"},
    "finance":   {"label": "Finance",   "icon": "◈",  "always_on": True,  "env_keys": [], "description": "Live crypto + stock prices (public APIs)"},
    "google":    {"label": "Google",    "icon": "G",  "always_on": False, "env_keys": ["GOOGLE_CREDENTIALS_PATH"], "description": "Calendar, Gmail, Drive"},
    "microsoft": {"label": "Microsoft", "icon": "M",  "always_on": False, "env_keys": ["MICROSOFT_CLIENT_ID"], "description": "Outlook, Teams, OneDrive"},
    "github":    {"label": "GitHub",    "icon": "⌥",  "always_on": False, "env_keys": ["GITHUB_TOKEN", "GITHUB_USERNAME"], "description": "Repos, PRs, notifications"},
    "phone":     {"label": "Phone",     "icon": "◷",  "always_on": False, "env_keys": ["PHONE_DEVICE_ID"], "description": "KDE Connect / iOS bridge"},
    "telegram":  {"label": "Telegram",  "icon": "▶",  "always_on": False, "env_keys": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"], "description": "Push alert delivery"},
}


@router.get("/integrations/status")
async def get_integrations_status():
    """Return per-source connection status, config state, and snapshot data."""
    import os

    # Hub source map
    hub_sources: dict = {}
    hub_snapshot: dict = {}
    hub_alerts: list = []
    hub_last_poll: str = ""
    try:
        from core.intelligence_hub import get_intelligence_hub
        hub = get_intelligence_hub()
        status = hub.get_status()
        hub_sources = status.get("sources", {})
        hub_alerts = status.get("active_alerts", [])
        hub_last_poll = status.get("last_snapshot", "")
        snap = hub._snapshot
        hub_snapshot = {
            "system":    snap.system,
            "google":    snap.google,
            "microsoft": snap.microsoft,
            "phone":     snap.phone,
            "github":    snap.github,
            "finance":   snap.finance,
            "browser":   snap.browser,
            "clipboard": snap.clipboard,
        }
    except Exception:
        pass

    integrations = []
    for key, cfg in _INTEGRATION_CONFIG.items():
        # Is it configured? (all required env keys present and non-empty)
        configured = all(bool(os.getenv(k, "").strip()) for k in cfg["env_keys"]) if cfg["env_keys"] else True
        connected = hub_sources.get(key, False)
        data = hub_snapshot.get(key, {})

        # Build a one-line status summary from snapshot data
        summary = _build_summary(key, data)

        integrations.append({
            "id": key,
            "label": cfg["label"],
            "icon": cfg["icon"],
            "description": cfg["description"],
            "always_on": cfg["always_on"],
            "env_keys": cfg["env_keys"],
            "configured": configured,
            "connected": connected,
            "summary": summary,
            "data": data,
        })

    return {
        "integrations": integrations,
        "hub_last_poll": hub_last_poll,
        "hub_alerts": hub_alerts,
        "connected_count": sum(1 for i in integrations if i["connected"]),
        "total": len(integrations),
    }


@router.post("/integrations/poll")
async def trigger_hub_poll():
    """Force an immediate full poll of all intelligence sources."""
    try:
        from core.intelligence_hub import get_intelligence_hub
        hub = get_intelligence_hub()
        hub.poll_all()
        return {"success": True, "last_poll": hub._snapshot.timestamp}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_summary(key: str, data: dict) -> str:
    if not data:
        return ""
    try:
        if key == "system":
            app = data.get("active_context", {})
            if isinstance(app, dict):
                app = app.get("active_app", "")
            cpu = data.get("cpu_percent", data.get("cpu", ""))
            parts = []
            if app:
                parts.append(str(app)[:30])
            if cpu:
                parts.append(f"CPU {cpu}%")
            return " · ".join(parts)
        if key == "browser":
            tab = data.get("active_tab", {})
            title = tab.get("title", "") if isinstance(tab, dict) else ""
            count = data.get("tab_count", 0)
            return f"{count} tabs" + (f" · {title[:35]}" if title else "")
        if key == "clipboard":
            t = data.get("type", "")
            sig = data.get("signal", "")
            return f"{t}: {sig[:40]}" if t else ""
        if key == "finance":
            prices = data.get("prices", {})
            parts = [f"{k} ${v.get('price', '?')}" for k, v in list(prices.items())[:3]]
            return " · ".join(parts)
        if key == "google":
            n = data.get("events_today", 0)
            mins = data.get("next_event_mins")
            nxt = (data.get("next_event") or {}).get("title", "")
            base = f"{n} events today"
            if nxt and mins is not None:
                base += f" · next: {nxt[:25]} in {mins}min"
            return base
        if key == "microsoft":
            unread = data.get("unread_emails", 0)
            nxt = (data.get("next_meeting") or {}).get("subject", "")
            return f"{unread} unread" + (f" · {nxt[:30]}" if nxt else "")
        if key == "github":
            notifs = data.get("unread_notifications", 0)
            ev = data.get("recent_event", "")
            return f"{notifs} notifications" + (f" · {ev[:40]}" if ev else "")
        if key == "phone":
            bat = data.get("battery", data.get("battery_level", ""))
            loc = data.get("location_label", data.get("location", ""))
            parts = []
            if bat:
                parts.append(f"Battery {bat}%")
            if loc:
                parts.append(str(loc)[:25])
            return " · ".join(parts)
        if key == "telegram":
            return "delivery channel"
    except Exception:
        pass
    return ""
