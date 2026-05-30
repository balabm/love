"""
LOVE Modern AI Routes — MCP, Reasoning, Browser Automation

Cutting-edge 2025 endpoints for:
- MCP (Model Context Protocol) server management
- Reasoning engine (chain-of-thought, reflection)
- Enhanced browser automation
"""

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/modern", tags=["modern"])


# ── MCP (Model Context Protocol) ──────────────────────────────────────────────

@router.get("/mcp/status")
async def get_mcp_status():
    """Get MCP host status and discovered servers."""
    try:
        from core.mcp_host import get_mcp_host
        host = get_mcp_host()
        return {
            "sdk_available": True,  # Simplified; actual check in module
            "health": host.get_health(),
            "servers": host.list_servers(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mcp/connect")
async def connect_mcp_server(server_id: str):
    """Connect to a specific MCP server."""
    try:
        from core.mcp_host import get_mcp_host
        host = get_mcp_host()
        success = host.connect_server(server_id)
        return {"success": success, "server_id": server_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mcp/tools")
async def get_mcp_tools():
    """List all MCP tools available across connected servers."""
    try:
        from core.mcp_host import get_mcp_host
        host = get_mcp_host()
        return host.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Reasoning Engine ────────────────────────────────────────────────────────

@router.post("/reasoning/analyze")
async def analyze_situation(situation: str, context: Optional[Dict] = None):
    """Run chain-of-thought analysis on a situation."""
    try:
        from core.reasoning_engine import get_reasoning_engine
        engine = get_reasoning_engine()
        chain = engine.analyze(situation, context or {})
        return {
            "chain_id": chain.id,
            "situation": chain.situation,
            "steps": chain.steps,
            "conclusion": chain.conclusion,
            "confidence": chain.confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reasoning/decide")
async def make_decision(question: str, options: List[Dict[str, str]]):
    """Make a decision by reasoning about options."""
    try:
        from core.reasoning_engine import get_reasoning_engine
        engine = get_reasoning_engine()
        result = engine.decide(question, options)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reasoning/reflect")
async def reflect_on_action(chain_id: str, outcome: str, success: bool):
    """Reflect on a completed reasoning chain."""
    try:
        from core.reasoning_engine import get_reasoning_engine
        engine = get_reasoning_engine()
        reflection = engine.reflect(chain_id, outcome, success)
        return {"reflection": reflection}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reasoning/patterns")
async def get_reasoning_patterns(pattern_type: Optional[str] = None):
    """Get learned reasoning patterns."""
    try:
        from core.reasoning_engine import get_reasoning_engine
        engine = get_reasoning_engine()
        patterns = engine.get_patterns(pattern_type or "")
        return {
            "patterns": [
                {
                    "id": p.id,
                    "type": p.pattern_type,
                    "description": p.description,
                    "success_rate": p.success_rate,
                    "usage_count": p.usage_count,
                }
                for p in patterns
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Enhanced Browser ──────────────────────────────────────────────────────────

@router.post("/browser/search")
async def enhanced_search(query: str, engine: str = "duckduckgo"):
    """Search the web using multiple providers."""
    try:
        from core.browser_agent import get_browser
        browser = get_browser()
        # The existing search_web uses DuckDuckGo
        results = browser.search_web(query)
        return {"query": query, "engine": engine, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/browser/navigate")
async def browser_navigate(url: str):
    """Navigate to a URL and extract content."""
    try:
        from core.browser_agent import get_browser
        browser = get_browser()
        content = browser.navigate(url)
        return {"url": url, "content_length": len(content), "content": content[:2000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Structured Output ─────────────────────────────────────────────────────────

@router.post("/structured/generate")
async def structured_generate(prompt: str, schema_type: str = "reasoning"):
    """Generate structured JSON output from a prompt."""
    try:
        from core.structured_output import get_structured_engine, SchemaField
        engine = get_structured_engine()
        if schema_type == "reasoning":
            schema = engine.reasoning_schema()
        elif schema_type == "decision":
            schema = engine.decision_schema(["option_a", "option_b", "option_c"])
        else:
            schema = engine.build_schema("custom", [SchemaField("result", "string", "Generated result")])
        result = engine.generate(prompt, schema)
        return {
            "success": result.success,
            "data": result.data,
            "attempts": result.attempts,
            "latency_ms": result.latency_ms,
            "errors": result.validation_errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/structured/stats")
async def structured_stats():
    """Get structured output engine statistics."""
    try:
        from core.structured_output import get_structured_engine
        engine = get_structured_engine()
        return engine.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Vector Memory ─────────────────────────────────────────────────────────────

@router.post("/vector/store")
async def vector_store(text: str, source: str = "api", tags: str = ""):
    """Store a memory with vector embedding for semantic search."""
    try:
        from core.vector_memory import get_vector_engine
        engine = get_vector_engine()
        mem_id = engine.store(text, source=source, tags=tags.split(",") if tags else [])
        return {"stored": bool(mem_id), "id": mem_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector/search")
async def vector_search(query: str, top_k: int = 5, threshold: float = 0.6):
    """Semantic search over stored memories."""
    try:
        from core.vector_memory import get_vector_engine
        engine = get_vector_engine()
        results = engine.search(query, top_k=top_k, threshold=threshold)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector/recall")
async def vector_recall(context: str, days: int = 30):
    """Contextual recall with temporal filtering."""
    try:
        from core.vector_memory import get_vector_engine
        engine = get_vector_engine()
        results = engine.recall(context, time_range_days=days)
        return {"context": context, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector/stats")
async def vector_stats():
    """Get vector memory engine statistics."""
    try:
        from core.vector_memory import get_vector_engine
        engine = get_vector_engine()
        return engine.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector/clusters")
async def vector_clusters(n: int = 5):
    """Get semantic clusters of stored memories."""
    try:
        from core.vector_memory import get_vector_engine
        engine = get_vector_engine()
        clusters = engine.cluster_memories(n_clusters=n)
        return {"clusters": clusters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Neural Architecture Search ────────────────────────────────────────────────

@router.get("/nas/status")
async def nas_status():
    """Get NAS engine status and best architectures."""
    try:
        from core.neural_architecture_search import get_neural_architecture_search
        nas = get_neural_architecture_search()
        return {
            "running": nas._running,
            "architectures": nas.get_architecture_stats(),
            "best": nas.get_best_architecture(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nas/create")
async def nas_create(config: dict):
    """Create a new architecture configuration."""
    try:
        from core.neural_architecture_search import get_neural_architecture_search
        nas = get_neural_architecture_search()
        arch_id = nas.create_architecture(config)
        return {"architecture_id": arch_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nas/profile")
async def nas_profile(architecture_id: str, task_type: str = "general"):
    """Profile an architecture's performance."""
    try:
        from core.neural_architecture_search import get_neural_architecture_search
        nas = get_neural_architecture_search()
        profile = nas.profile_architecture(architecture_id, task_type)
        return {"profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Multi-Modal Evolution ─────────────────────────────────────────────────────

@router.get("/multimodal/status")
async def multimodal_status():
    """Get multi-modal evolution status."""
    try:
        from core.multimodal_evolution import get_multimodal_evolution
        mme = get_multimodal_evolution()
        return {
            "running": mme._running,
            "capabilities": {k: {"accuracy": v.accuracy, "speed": v.speed} for k, v in mme._capabilities.items()},
            "patterns": len(mme._cross_modal_patterns),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal/recommend")
async def multimodal_recommend(task: str, context: dict = None):
    """Get modality recommendations for a task."""
    try:
        from core.multimodal_evolution import get_multimodal_evolution
        mme = get_multimodal_evolution()
        recs = mme.get_modality_recommendations(task, context or {})
        return {"task": task, "recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Code Sandbox ──────────────────────────────────────────────────────────────

@router.post("/sandbox/execute")
async def sandbox_execute(code: str, timeout: float = 10.0):
    """Execute Python code in a restricted sandbox."""
    try:
        from core.code_sandbox import get_code_sandbox
        sandbox = get_code_sandbox()
        result = sandbox.execute(code, timeout=timeout)
        return {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "blocked": result.blocked,
            "block_reason": result.block_reason,
            "execution_time_ms": result.execution_time_ms,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sandbox/stats")
async def sandbox_stats():
    """Get sandbox execution statistics."""
    try:
        from core.code_sandbox import get_code_sandbox
        sandbox = get_code_sandbox()
        return sandbox.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Observability ─────────────────────────────────────────────────────────────

@router.get("/observability/health")
async def observability_health():
    """Get health scores for all subsystems."""
    try:
        from core.observability import get_observability_engine
        obs = get_observability_engine()
        return {"scores": obs.get_all_health_scores()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/observability/metrics")
async def observability_metrics(name: str, subsystem: str = "", window: int = 60):
    """Get metric statistics for a subsystem."""
    try:
        from core.observability import get_observability_engine
        obs = get_observability_engine()
        return obs.get_metric_stats(name, subsystem, window)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/observability/alerts")
async def observability_alerts(severity: str = "", limit: int = 50):
    """Get recent anomaly alerts."""
    try:
        from core.observability import get_observability_engine
        obs = get_observability_engine()
        alerts = [a for a in obs._alerts if not severity or a.severity == severity]
        return {
            "alerts": [
                {
                    "id": a.id,
                    "severity": a.severity,
                    "subsystem": a.subsystem,
                    "title": a.title,
                    "description": a.description,
                    "suggested_action": a.suggested_action,
                    "created_at": a.created_at,
                }
                for a in sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Guardrails ────────────────────────────────────────────────────────────────

@router.post("/guardrails/scan")
async def guardrails_scan(text: str, context: str = ""):
    """Scan content for safety issues."""
    try:
        from core.guardrails import get_guardrails_engine
        gr = get_guardrails_engine()
        result = gr.scan(text, context)
        return {
            "allowed": result.allowed,
            "confidence": result.confidence,
            "flags": result.flags,
            "pii_detected": result.pii_detected,
            "redacted_text": result.redacted_text,
            "suggested_action": result.suggested_action,
            "block_reason": result.block_reason,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guardrails/goals")
async def guardrails_goals(goals: list):
    """Set user goals for drift detection."""
    try:
        from core.guardrails import get_guardrails_engine
        gr = get_guardrails_engine()
        gr.set_user_goals(goals)
        return {"goals_set": len(goals)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/rate-limit")
async def guardrails_rate_limit(resource: str):
    """Check rate limit for a resource."""
    try:
        from core.guardrails import get_guardrails_engine
        gr = get_guardrails_engine()
        return gr.check_rate_limit(resource)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/stats")
async def guardrails_stats():
    """Get guardrails statistics."""
    try:
        from core.guardrails import get_guardrails_engine
        gr = get_guardrails_engine()
        return gr.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── LLM Manager ───────────────────────────────────────────────────────────────

@router.get("/llm/models")
async def llm_models():
    """List all available local LLM models."""
    try:
        from core.llm_manager import get_llm_manager
        mgr = get_llm_manager()
        models = mgr.discover_models()
        return {
            "models": [
                {
                    "name": m.name,
                    "provider": m.provider,
                    "size": m.size,
                    "quantization": m.quantization,
                    "capabilities": m.capabilities,
                    "loaded": m.loaded,
                    "avg_latency_ms": m.avg_latency_ms,
                    "success_rate": m.success_rate,
                }
                for m in models
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/route")
async def llm_route(task_type: str, preferred_model: str = "", quality: bool = False):
    """Get the best model for a task type."""
    try:
        from core.llm_manager import get_llm_manager
        mgr = get_llm_manager()
        route = mgr.route_task(task_type, preferred_model, quality)
        return {
            "task_type": route.task_type,
            "model": route.model,
            "reason": route.reason,
            "confidence": route.confidence,
            "fallback_chain": route.fallback_chain,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/stats")
async def llm_stats():
    """Get LLM performance statistics."""
    try:
        from core.llm_manager import get_llm_manager
        mgr = get_llm_manager()
        return mgr.get_all_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/suggestions")
async def llm_suggestions():
    """Get proactive model suggestions."""
    try:
        from core.llm_manager import get_llm_manager
        mgr = get_llm_manager()
        return {"suggestions": mgr.suggest_models()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/pull")
async def llm_pull(model: str):
    """Pull a new model from Ollama."""
    try:
        from core.llm_manager import get_llm_manager
        mgr = get_llm_manager()
        return mgr.pull_model(model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Graph RAG ───────────────────────────────────────────────────────────────────

@router.post("/graph-rag/query")
async def graph_rag_query(question: str, top_k: int = 5):
    """Query using knowledge graph + vector memory hybrid retrieval."""
    try:
        from core.graph_rag import get_graph_rag_engine
        engine = get_graph_rag_engine()
        result = engine.query(question, top_k=top_k)
        return {
            "answer": result.answer,
            "entities": result.entities,
            "paths": [
                {"steps": p.steps, "confidence": p.confidence, "source": p.source}
                for p in result.paths
            ],
            "semantic_matches": result.semantic_matches,
            "suggested_questions": result.suggested_questions,
            "confidence": result.confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph-rag/stats")
async def graph_rag_stats():
    """Get Graph RAG engine statistics."""
    try:
        from core.graph_rag import get_graph_rag_engine
        engine = get_graph_rag_engine()
        return engine.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Prompt Optimizer ──────────────────────────────────────────────────────────

@router.post("/prompts/register")
async def register_prompt(task_type: str, template: str, prompt_id: str = "", tags: str = ""):
    """Register a new prompt template for optimization."""
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        opt = get_prompt_optimizer()
        pid = opt.register_template(task_type, template, prompt_id, tags.split(",") if tags else [])
        return {"prompt_id": pid, "registered": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/record")
async def record_prompt(prompt_id: str, latency_ms: float, success: bool, quality: float = 0.0):
    """Record prompt performance."""
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        opt = get_prompt_optimizer()
        opt.record_prompt(prompt_id, "", latency_ms, success, quality)
        return {"recorded": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/experiment")
async def start_experiment(task_type: str, base_prompt_id: str, min_samples: int = 50):
    """Start an A/B test for a prompt."""
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        opt = get_prompt_optimizer()
        exp_id = opt.start_experiment(task_type, base_prompt_id, min_samples)
        return {"experiment_id": exp_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/experiment/{exp_id}")
async def evaluate_experiment(exp_id: str):
    """Evaluate an experiment and determine winner."""
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        opt = get_prompt_optimizer()
        result = opt.evaluate_experiment(exp_id)
        return result or {"status": "not_found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/suggestions")
async def prompt_suggestions():
    """Get proactive prompt improvement suggestions."""
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        opt = get_prompt_optimizer()
        return {"suggestions": opt.suggest_improvements()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/stats")
async def prompt_stats():
    """Get prompt optimizer statistics."""
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        opt = get_prompt_optimizer()
        return opt.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/best")
async def best_prompt(task_type: str):
    """Get the best performing prompt for a task type."""
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        opt = get_prompt_optimizer()
        template = opt.get_best_prompt(task_type)
        return {"task_type": task_type, "template": template}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Self-Reflection ───────────────────────────────────────────────────────────

@router.post("/self-reflection/reflect")
async def self_reflect():
    """Trigger a self-reflection cycle."""
    try:
        from core.self_reflection import get_self_reflection_engine
        engine = get_self_reflection_engine()
        result = engine.reflect()
        return {
            "patterns_found": len(result["behavioral_patterns"]),
            "capabilities_assessed": len(result["capability_assessment"]),
            "decisions_audited": len(result["decision_quality"]),
            "insights_generated": len(result["new_insights"]),
            "insights": [
                {"category": i.category, "observation": i.observation, "severity": i.severity}
                for i in result["new_insights"]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/self-reflection/insights")
async def self_reflection_insights(limit: int = 10):
    """Get recent self-reflection insights."""
    try:
        from core.self_reflection import get_self_reflection_engine
        engine = get_self_reflection_engine()
        return {"insights": engine.get_recent_insights(limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/self-reflection/stats")
async def self_reflection_stats():
    """Get self-reflection engine statistics."""
    try:
        from core.self_reflection import get_self_reflection_engine
        engine = get_self_reflection_engine()
        return engine.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Conversation Quality ──────────────────────────────────────────────────────

@router.post("/conversation/analyze-turn")
async def analyze_turn(user_message: str, love_response: str, response_time_ms: float = 0.0):
    """Analyze a single conversation turn for quality."""
    try:
        from core.conversation_quality import get_conversation_quality_analyzer
        analyzer = get_conversation_quality_analyzer()
        result = analyzer.analyze_turn(user_message, love_response, response_time_ms)
        return {
            "turn_id": result.turn_id,
            "engagement": result.engagement_score,
            "clarity": result.clarity_score,
            "relevance": result.relevance_score,
            "emotional_tone": result.emotional_tone,
            "response_time_ms": result.response_time_ms,
            "overall_score": result.overall_score,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/analyze")
async def analyze_conversation():
    """Analyze the current conversation for quality."""
    try:
        from core.conversation_quality import get_conversation_quality_analyzer
        analyzer = get_conversation_quality_analyzer()
        result = analyzer.analyze_conversation()
        return {
            "conversation_id": result.conversation_id,
            "turn_count": result.turn_count,
            "avg_quality": result.avg_quality,
            "best_turn": result.best_turn,
            "worst_turn": result.worst_turn,
            "dominant_emotion": result.dominant_emotion,
            "suggestions": result.suggestions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/trends")
async def conversation_trends(days: int = 7):
    """Get conversation quality trends."""
    try:
        from core.conversation_quality import get_conversation_quality_analyzer
        analyzer = get_conversation_quality_analyzer()
        return analyzer.get_quality_trends(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/stats")
async def conversation_stats():
    """Get conversation quality statistics."""
    try:
        from core.conversation_quality import get_conversation_quality_analyzer
        analyzer = get_conversation_quality_analyzer()
        return analyzer.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Predictive Maintenance ────────────────────────────────────────────────────

@router.get("/predictive/health/{subsystem}")
async def health_forecast(subsystem: str, hours: int = 24):
    """Get health forecast for a subsystem."""
    try:
        from core.predictive_maintenance import get_predictive_maintenance_engine
        engine = get_predictive_maintenance_engine()
        return engine.get_health_forecast(subsystem, hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictive/predictions")
async def all_predictions():
    """Get all current failure predictions."""
    try:
        from core.predictive_maintenance import get_predictive_maintenance_engine
        engine = get_predictive_maintenance_engine()
        return {"predictions": engine.get_all_predictions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictive/snapshot")
async def record_snapshot(subsystem: str, health_score: float, latency_ms: float = 0.0,
                         error_rate: float = 0.0):
    """Record a health snapshot for a subsystem."""
    try:
        from core.predictive_maintenance import get_predictive_maintenance_engine
        engine = get_predictive_maintenance_engine()
        engine.record_snapshot(subsystem, health_score, latency_ms, error_rate)
        return {"recorded": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictive/stats")
async def predictive_stats():
    """Get predictive maintenance statistics."""
    try:
        from core.predictive_maintenance import get_predictive_maintenance_engine
        engine = get_predictive_maintenance_engine()
        return engine.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Multi-Agent Orchestrator ────────────────────────────────────────────────────

@router.post("/agents/orchestrate")
async def orchestrate_task(goal: str):
    """Run a multi-agent orchestration for a high-level goal."""
    try:
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        orch = get_multi_agent_orchestrator()
        return orch.run_orchestration(goal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/task")
async def create_agent_task(description: str, role: str = "", dependencies: str = ""):
    """Create a new task for an agent."""
    try:
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator, AgentRole
        orch = get_multi_agent_orchestrator()
        agent_role = None
        if role:
            try:
                agent_role = AgentRole(role)
            except ValueError:
                pass
        deps = dependencies.split(",") if dependencies else []
        task_id = orch.create_task(description, agent_role, deps)
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/status")
async def agent_status():
    """Get status of all agents."""
    try:
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        orch = get_multi_agent_orchestrator()
        return {"agents": orch.get_agent_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/tasks")
async def task_status():
    """Get status of all tasks."""
    try:
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        orch = get_multi_agent_orchestrator()
        return {"tasks": orch.get_task_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/messages")
async def agent_messages(limit: int = 20):
    """Get recent inter-agent messages."""
    try:
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        orch = get_multi_agent_orchestrator()
        return {"messages": orch.get_recent_messages(limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/stats")
async def agent_stats():
    """Get multi-agent orchestrator statistics."""
    try:
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        orch = get_multi_agent_orchestrator()
        return orch.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Intent Predictor ──────────────────────────────────────────────────────────

@router.post("/intent/classify")
async def classify_intent(message: str):
    """Classify the intent of a user message."""
    try:
        from core.intent_predictor import get_intent_predictor
        predictor = get_intent_predictor()
        return predictor.classify_intent(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intent/predict")
async def predict_intent(recent_messages: List[str] = []):
    """Predict the user's next intent based on recent messages."""
    try:
        from core.intent_predictor import get_intent_predictor
        predictor = get_intent_predictor()
        result = predictor.predict_next_intent(recent_messages)
        if result:
            return {
                "prediction_id": result.prediction_id,
                "predicted_intent": result.predicted_intent,
                "confidence": result.confidence,
                "predicted_message": result.predicted_message,
                "suggested_response": result.suggested_response,
                "context_trigger": result.context_trigger,
            }
        return {"prediction": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intent/prepare")
async def prepare_response(prediction_id: str):
    """Prepare a response for a predicted intent."""
    try:
        from core.intent_predictor import get_intent_predictor, IntentPrediction
        predictor = get_intent_predictor()
        # Find the prediction
        for pred in predictor._predictions:
            if pred.prediction_id == prediction_id:
                return predictor.prepare_response(pred)
        return {"prepared": False, "reason": "prediction not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/stats")
async def intent_stats():
    """Get intent predictor statistics."""
    try:
        from core.intent_predictor import get_intent_predictor
        predictor = get_intent_predictor()
        return predictor.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Personality Adapter ────────────────────────────────────────────────────────

@router.post("/personality/analyze")
async def analyze_personality_context(messages: List[str] = [], task_type: str = ""):
    """Analyze conversation context to determine appropriate tone."""
    try:
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        return adapter.analyze_context(messages, task_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personality/adapt")
async def adapt_response(response: str, messages: List[str] = []):
    """Adapt a response based on conversation context."""
    try:
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        context = adapter.analyze_context(messages)
        return {"adapted_response": adapter.adapt_response(response, context)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality/profile")
async def personality_profile():
    """Get current personality profile."""
    try:
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        return adapter.get_personality_profile()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality/stats")
async def personality_stats():
    """Get personality adapter statistics."""
    try:
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        return adapter.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Router Registration ───────────────────────────────────────────────────


def register_modern_routes(app):
    """Register all modern AI routes with the FastAPI app."""
    app.include_router(router)
