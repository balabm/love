"""
LOVE Modern AI Routes — MCP, Reasoning, Browser Automation

Cutting-edge 2025 endpoints for:
- MCP (Model Context Protocol) server management
- Reasoning engine (chain-of-thought, reflection)
- Enhanced browser automation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

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
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="api.modern_routes")
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


# ── Response Cache ─────────────────────────────────────────────────────────────

@router.get("/cache/stats")
async def cache_stats():
    """Get response cache statistics."""
    try:
        from core.response_cache import get_response_cache
        cache = get_response_cache()
        return cache.get_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache(context_type: str = "all"):
    """Invalidate cache entries."""
    try:
        from core.response_cache import get_response_cache
        cache = get_response_cache()
        removed = cache.invalidate_context(context_type)
        return {"removed": removed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/cleanup")
async def cleanup_cache():
    """Remove expired cache entries."""
    try:
        from core.response_cache import get_response_cache
        cache = get_response_cache()
        removed = cache.cleanup_expired()
        return {"removed": removed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Context Window Manager ──────────────────────────────────────────────────────

@router.post("/context/optimize")
async def optimize_context(segments: List[Dict[str, Any]] = []):
    """Optimize context segments to fit within LLM window."""
    try:
        from core.context_window_manager import get_context_window_manager, ContextSegment
        manager = get_context_window_manager()
        ctx_segments = [
            ContextSegment(
                content=s.get("content", ""),
                segment_type=s.get("segment_type", "default"),
                priority=s.get("priority", 1.0),
                created_at=s.get("created_at", 0.0),
            )
            for s in segments
        ]
        optimized = manager.optimize_context(ctx_segments)
        return {
            "optimized": [
                {
                    "content": o.content[:200],
                    "segment_type": o.segment_type,
                    "priority": o.priority,
                    "tokens": o.tokens,
                }
                for o in optimized
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/summarize")
async def summarize_conversation(conversation: List[Dict[str, Any]] = [], keep_recent: int = 5):
    """Summarize old conversation turns."""
    try:
        from core.context_window_manager import get_context_window_manager
        manager = get_context_window_manager()
        result = manager.summarize_old_turns(conversation, keep_recent)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/tokens")
async def estimate_tokens(text: str):
    """Estimate token count for text."""
    try:
        from core.context_window_manager import get_context_window_manager
        manager = get_context_window_manager()
        return {"tokens": manager.get_token_estimate(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/stats")
async def context_stats():
    """Get context window manager statistics."""
    try:
        from core.context_window_manager import get_context_window_manager
        manager = get_context_window_manager()
        return manager.get_context_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── User Pattern Detector ──────────────────────────────────────────────────────

@router.post("/patterns/detect")
async def detect_patterns(activities: List[Dict[str, Any]] = []):
    """Detect behavioral patterns from user activities."""
    try:
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        return {"patterns": detector.detect_patterns(activities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/insights")
async def pattern_insights():
    """Get daily insights based on detected patterns."""
    try:
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        return {"insights": detector.get_daily_insights()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/predict")
async def predict_activity():
    """Predict the user's next activity."""
    try:
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        return detector.predict_next_activity()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/stats")
async def pattern_stats():
    """Get pattern detector statistics."""
    try:
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        return detector.get_pattern_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ── Goal Drift Detector ───────────────────────────────────────────────────────

class GoalSetRequest(BaseModel):
    goal_id: str
    description: str
    priority: float
    target_metrics: Optional[Dict[str, Any]] = None


class ActivityLogRequest(BaseModel):
    activity_type: str
    description: str
    duration: float
    goal_alignment_score: float
    linked_goal_ids: Optional[List[str]] = None


@router.post("/goals/set")
async def set_goal(req: GoalSetRequest):
    """Register a user goal."""
    try:
        from core.goal_drift_detector import get_goal_drift_detector
        detector = get_goal_drift_detector()
        goal = detector.set_goal(
            goal_id=req.goal_id,
            description=req.description,
            priority=req.priority,
            target_metrics=req.target_metrics or {},
        )
        return {"success": True, "goal": goal.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goals/activity")
async def log_activity(req: ActivityLogRequest):
    """Log a daily activity."""
    try:
        from core.goal_drift_detector import get_goal_drift_detector
        detector = get_goal_drift_detector()
        activity = detector.record_activity(
            activity_type=req.activity_type,
            description=req.description,
            duration=req.duration,
            goal_alignment_score=req.goal_alignment_score,
            linked_goal_ids=req.linked_goal_ids or [],
        )
        return {"success": True, "activity": activity.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals/drift")
async def detect_drift():
    """Detect goal drift based on recent activities."""
    try:
        from core.goal_drift_detector import get_goal_drift_detector
        detector = get_goal_drift_detector()
        alerts = detector.detect_drift()
        return {"alerts": [a.__dict__ for a in alerts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals/alerts")
async def get_drift_alerts(include_acknowledged: bool = False):
    """Get active drift warnings with severity."""
    try:
        from core.goal_drift_detector import get_goal_drift_detector
        detector = get_goal_drift_detector()
        return {"alerts": detector.get_drift_alerts(include_acknowledged=include_acknowledged)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals/progress")
async def get_goal_progress(goal_id: str):
    """Get progress toward a specific goal."""
    try:
        from core.goal_drift_detector import get_goal_drift_detector
        detector = get_goal_drift_detector()
        return detector.get_goal_progress(goal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals/stats")
async def get_drift_stats():
    """Get detector statistics."""
    try:
        from core.goal_drift_detector import get_goal_drift_detector
        detector = get_goal_drift_detector()
        return detector.get_drift_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ── Cross-Modal Fusion ────────────────────────────────────────────────────────

@router.post("/fusion/fuse")
async def fusion_fuse(
    text_insights: list = None,
    visual_insights: list = None,
    voice_insights: list = None,
):
    """Fuse insights from multiple modalities into unified understanding."""
    try:
        from core.cross_modal_fusion import get_cross_modal_fusion_engine
        engine = get_cross_modal_fusion_engine()
        result = engine.fuse_insights(
            text_insights=text_insights,
            visual_insights=visual_insights,
            voice_insights=voice_insights,
        )
        return {
            "id": result.id,
            "unified_themes": result.unified_themes,
            "dominant_emotion": result.dominant_emotion,
            "dominant_entities": result.dominant_entities,
            "confidence": result.confidence,
            "modality_weights": result.modality_weights,
            "resolved_conflicts": result.resolved_conflicts,
            "proactive_suggestion": result.proactive_suggestion,
            "timestamp": result.timestamp,
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fusion/conflicts")
async def fusion_conflicts(modalities: list):
    """Detect modality conflicts across insights."""
    try:
        from core.cross_modal_fusion import get_cross_modal_fusion_engine
        engine = get_cross_modal_fusion_engine()
        reports = engine.detect_modal_conflicts(modalities)
        return {
            "conflicts": [
                {
                    "id": r.id,
                    "entity": r.entity,
                    "conflict_type": r.conflict_type,
                    "modalities_involved": r.modalities_involved,
                    "signals": r.signals,
                    "severity": r.severity,
                    "recommendation": r.recommendation,
                }
                for r in reports
            ]
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fusion/summary")
async def fusion_summary(sources: list):
    """Generate a cross-modal summary weighted by confidence."""
    try:
        from core.cross_modal_fusion import get_cross_modal_fusion_engine
        engine = get_cross_modal_fusion_engine()
        summary = engine.get_cross_modal_summary(sources)
        return {
            "id": summary.id,
            "sources": summary.sources,
            "summary": summary.summary_text,
            "key_themes": summary.key_themes,
            "emotional_tone": summary.emotional_tone,
            "confidence": summary.confidence,
            "suggested_action": summary.suggested_action,
            "timestamp": summary.timestamp,
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fusion/stats")
async def fusion_stats():
    """Get cross-modal fusion engine statistics."""
    try:
        from core.cross_modal_fusion import get_cross_modal_fusion_engine
        engine = get_cross_modal_fusion_engine()
        return engine.get_fusion_stats()
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))




# ── Emotional Resonance Engine ────────────────────────────────────────────────

class EmotionalAnalyzeRequest(BaseModel):
    text: str


class EmotionalResonanceRequest(BaseModel):
    user_text: str
    love_response: str


@router.post("/emotion/analyze")
async def analyze_emotion(req: EmotionalAnalyzeRequest):
    """Deep emotional analysis beyond surface sentiment."""
    try:
        from core.emotional_resonance import get_emotional_resonance_engine
        engine = get_emotional_resonance_engine()
        state = engine.analyze_emotional_depth(req.text)
        return {
            "state_id": state.state_id,
            "timestamp": state.timestamp,
            "valence": state.valence,
            "arousal": state.arousal,
            "dominance": state.dominance,
            "sarcasm": state.sarcasm,
            "suppressed_frustration": state.suppressed_frustration,
            "growing_anxiety": state.growing_anxiety,
            "hidden_excitement": state.hidden_excitement,
            "emotional_numbness": state.emotional_numbness,
            "defensiveness": state.defensiveness,
            "vulnerability": state.vulnerability,
            "masked_distress": state.masked_distress,
            "primary_emotion": state.primary_emotion,
            "depth_score": state.depth_score,
            "transparency": state.transparency,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion/shifts")
async def detect_emotion_shifts():
    """Detect emotional shifts in recent history."""
    try:
        from core.emotional_resonance import get_emotional_resonance_engine
        engine = get_emotional_resonance_engine()
        alerts = engine.detect_emotional_shifts()
        return {
            "shifts_detected": len(alerts),
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "shift_type": a.shift_type,
                    "severity": a.severity,
                    "description": a.description,
                    "recommendation": a.recommendation,
                    "timestamp": a.timestamp,
                }
                for a in alerts
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion/resonance")
async def measure_resonance(req: EmotionalResonanceRequest):
    """Measure how well LOVE's response resonated emotionally."""
    try:
        from core.emotional_resonance import get_emotional_resonance_engine
        engine = get_emotional_resonance_engine()
        reading = engine.measure_resonance(req.user_text, req.love_response)
        return {
            "reading_id": reading.reading_id,
            "timestamp": reading.timestamp,
            "emotional_match": reading.emotional_match,
            "validation_felt": reading.validation_felt,
            "tone_alignment": reading.tone_alignment,
            "depth_reciprocity": reading.depth_reciprocity,
            "overall_resonance": reading.overall_resonance,
            "suggestions": reading.suggestions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotion/forecast")
async def emotional_forecast():
    """Get emotional trajectory forecast."""
    try:
        from core.emotional_resonance import get_emotional_resonance_engine
        engine = get_emotional_resonance_engine()
        return engine.get_emotional_forecast()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotion/stats")
async def emotion_stats():
    """Get Emotional Resonance Engine statistics."""
    try:
        from core.emotional_resonance import get_emotional_resonance_engine
        engine = get_emotional_resonance_engine()
        return engine.get_resonance_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Knowledge Graph Auto-Builder ──────────────────────────────────────────────

@router.post("/kg/extract")
async def extract_entities(text: str):
    """Extract entities from text."""
    try:
        from core.knowledge_graph_builder import get_knowledge_graph_builder
        builder = get_knowledge_graph_builder()
        return {"entities": builder.extract_entities(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/relations")
async def extract_relations(text: str):
    """Extract relations from text."""
    try:
        from core.knowledge_graph_builder import get_knowledge_graph_builder
        builder = get_knowledge_graph_builder()
        entities = builder.extract_entities(text)
        return {"relations": builder.extract_relations(text, entities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/build")
async def build_graph(texts: List[str] = []):
    """Build knowledge graph from texts."""
    try:
        from core.knowledge_graph_builder import get_knowledge_graph_builder
        builder = get_knowledge_graph_builder()
        return builder.build_graph(texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/query")
async def query_graph(entity: str, depth: int = 1):
    """Query graph for entity connections."""
    try:
        from core.knowledge_graph_builder import get_knowledge_graph_builder
        builder = get_knowledge_graph_builder()
        return builder.query_graph(entity, depth)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/stats")
async def kg_stats():
    """Get knowledge graph statistics."""
    try:
        from core.knowledge_graph_builder import get_knowledge_graph_builder
        builder = get_knowledge_graph_builder()
        return builder.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/export")
async def export_graph():
    """Export knowledge graph as JSON."""
    try:
        from core.knowledge_graph_builder import get_knowledge_graph_builder
        builder = get_knowledge_graph_builder()
        return builder.export_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Adaptive Learning Rate Engine ─────────────────────────────────────────────

@router.post("/learning/adjust")
async def adjust_parameters(feedback: Dict[str, Any] = {}):
    """Adjust system parameters based on feedback."""
    try:
        from core.adaptive_learning_rate import get_adaptive_learning_engine
        engine = get_adaptive_learning_engine()
        return engine.adjust_parameters(feedback)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/temperature")
async def get_temperature(task_type: str = "general"):
    """Get optimal temperature for a task type."""
    try:
        from core.adaptive_learning_rate import get_adaptive_learning_engine
        engine = get_adaptive_learning_engine()
        return {"temperature": engine.get_optimal_temperature(task_type), "task_type": task_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/exploration")
async def get_exploration():
    """Get current exploration rate."""
    try:
        from core.adaptive_learning_rate import get_adaptive_learning_engine
        engine = get_adaptive_learning_engine()
        return {"exploration_rate": engine.get_exploration_rate(), "should_explore": engine.should_explore()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/stats")
async def learning_stats():
    """Get learning engine statistics."""
    try:
        from core.adaptive_learning_rate import get_adaptive_learning_engine
        engine = get_adaptive_learning_engine()
        return engine.get_learning_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Conversation Continuity Manager ───────────────────────────────────────────

@router.post("/continuity/snapshot")
async def capture_snapshot(context: Dict[str, Any] = {}):
    """Save a conversation state snapshot."""
    try:
        from core.conversation_continuity import get_conversation_continuity_manager
        manager = get_conversation_continuity_manager()
        return manager.capture_snapshot(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/continuity/restore")
async def restore_context(thread_id: str = "default"):
    """Retrieve the most recent context for a thread."""
    try:
        from core.conversation_continuity import get_conversation_continuity_manager
        manager = get_conversation_continuity_manager()
        return manager.restore_context(thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/continuity/gap")
async def gap_summary(thread_id: str = "default", absence_hours: float = 1.0):
    """Summarize what happened during user's absence."""
    try:
        from core.conversation_continuity import get_conversation_continuity_manager
        manager = get_conversation_continuity_manager()
        return manager.get_gap_summary(thread_id, absence_hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/continuity/threads")
async def thread_status():
    """Show all active conversation threads."""
    try:
        from core.conversation_continuity import get_conversation_continuity_manager
        manager = get_conversation_continuity_manager()
        return manager.get_thread_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continuity/threads")
async def create_thread(thread_id: str, name: str):
    """Create a new conversation thread."""
    try:
        from core.conversation_continuity import get_conversation_continuity_manager
        manager = get_conversation_continuity_manager()
        return manager.create_thread(thread_id, name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/continuity/stats")
async def continuity_stats():
    """Get conversation continuity statistics."""
    try:
        from core.conversation_continuity import get_conversation_continuity_manager
        manager = get_conversation_continuity_manager()
        return manager.get_continuity_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Rate Limiter ────────────────────────────────────────────────────────────

@router.get("/rate-limit/status")
async def rate_limit_status(client_id: str = "default"):
    """Get current rate limit status for a client."""
    try:
        from api.rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        bucket = limiter.get_bucket(client_id)
        return {
            "client_id": client_id,
            "remaining": int(bucket.tokens),
            "limit": bucket.capacity,
            "reset_after": round(bucket.get_wait_time(), 1),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit/stats")
async def rate_limit_stats():
    """Get rate limiter global statistics."""
    try:
        from api.rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        return limiter.get_rate_limit_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Memory Compressor ───────────────────────────────────────────────────────

@router.post("/memory/compress")
async def compress_memory(turns: List[Dict[str, Any]] = []):
    """Compress conversation turns."""
    try:
        from core.memory_compressor import get_memory_compressor
        compressor = get_memory_compressor()
        return compressor.compress_conversation(turns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/compress/stats")
async def compression_stats():
    """Get memory compression statistics."""
    try:
        from core.memory_compressor import get_memory_compressor
        compressor = get_memory_compressor()
        return compressor.get_compression_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/compress/estimate")
async def estimate_savings(total_turns: int = 100):
    """Estimate compression savings."""
    try:
        from core.memory_compressor import get_memory_compressor
        compressor = get_memory_compressor()
        return compressor.estimate_savings(total_turns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Semantic Search Optimizer ───────────────────────────────────────────────

@router.post("/search/optimize")
async def optimize_search(query: Dict[str, Any] = {}):
    """Optimize a search query for better retrieval."""
    try:
        from core.semantic_search_optimizer import get_semantic_search_optimizer
        optimizer = get_semantic_search_optimizer()
        q = query.get("query", "")
        context = query.get("context", [])
        return optimizer.search_with_optimization(q, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/rerank")
async def rerank_search(results: List[Dict[str, Any]] = [], query: str = ""):
    """Rerank search results using multiple signals."""
    try:
        from core.semantic_search_optimizer import get_semantic_search_optimizer
        optimizer = get_semantic_search_optimizer()
        return {"reranked": [r.__dict__ if hasattr(r, '__dict__') else r for r in optimizer.rerank_results(results, query)]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/stats")
async def search_optimizer_stats():
    """Get search optimizer statistics."""
    try:
        from core.semantic_search_optimizer import get_semantic_search_optimizer
        optimizer = get_semantic_search_optimizer()
        return optimizer.get_search_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Emotion-Aware Response Generator ────────────────────────────────────────

@router.post("/emotion/generate")
async def generate_emotion_aware_response(data: Dict[str, Any] = {}):
    """Generate an emotionally calibrated response."""
    try:
        from core.emotion_aware_response import get_emotion_aware_response_generator
        generator = get_emotion_aware_response_generator()
        return generator.generate_response(data.get("text", ""), data.get("emotion_state"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion/feedback")
async def emotion_support_feedback(data: Dict[str, Any] = {}):
    """Record feedback on emotional support."""
    try:
        from core.emotion_aware_response import get_emotion_aware_response_generator
        generator = get_emotion_aware_response_generator()
        generator.record_support_feedback(data.get("support_id", ""), data.get("helpful", False))
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotion/stats")
async def emotion_aware_stats():
    """Get emotional support effectiveness statistics."""
    try:
        from core.emotion_aware_response import get_emotion_aware_response_generator
        generator = get_emotion_aware_response_generator()
        return generator.get_support_effectiveness()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotion/trajectory")
async def emotion_trajectory():
    """Get emotional trajectory over time."""
    try:
        from core.emotion_aware_response import get_emotion_aware_response_generator
        generator = get_emotion_aware_response_generator()
        return generator.get_emotional_trajectory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Knowledge Injector ────────────────────────────────────────────────────────

@router.post("/knowledge/inject")
async def inject_knowledge(data: Dict[str, Any] = {}):
    """Propose knowledge to inject into the conversation."""
    try:
        from core.knowledge_injector import get_knowledge_injector
        injector = get_knowledge_injector()
        return injector.inject_knowledge(data.get("text", ""), data.get("context", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/feedback")
async def knowledge_injection_feedback(data: Dict[str, Any] = {}):
    """Record feedback on knowledge injection."""
    try:
        from core.knowledge_injector import get_knowledge_injector
        injector = get_knowledge_injector()
        injector.record_injection_feedback(data.get("injection_id", ""), data.get("accepted", False))
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
async def knowledge_injector_stats():
    """Get knowledge injector statistics."""
    try:
        from core.knowledge_injector import get_knowledge_injector
        injector = get_knowledge_injector()
        return injector.get_injection_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Conversation Summarizer ─────────────────────────────────────────────────

@router.post("/conversation/summarize")
async def summarize_conversation(data: Dict[str, Any] = {}):
    """Summarize a conversation from turns."""
    try:
        from core.conversation_summarizer import get_conversation_summarizer
        summarizer = get_conversation_summarizer()
        turns = data.get("turns", [])
        return summarizer.summarize_conversation(turns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/summary/stats")
async def conversation_summary_stats():
    """Get conversation summarizer statistics."""
    try:
        from core.conversation_summarizer import get_conversation_summarizer
        summarizer = get_conversation_summarizer()
        return summarizer.get_summary_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Context-Aware Task Prioritizer ──────────────────────────────────────────

@router.post("/tasks/prioritize")
async def prioritize_tasks(data: Dict[str, Any] = {}):
    """Prioritize tasks based on user context."""
    try:
        from core.context_aware_prioritizer import get_context_aware_prioritizer
        prioritizer = get_context_aware_prioritizer()
        tasks = data.get("tasks", [])
        context = data.get("context", {})
        return {"prioritized": prioritizer.prioritize_tasks(tasks, context)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/suggest-next")
async def suggest_next_task(data: Dict[str, Any] = {}):
    """Suggest the best next task."""
    try:
        from core.context_aware_prioritizer import get_context_aware_prioritizer
        prioritizer = get_context_aware_prioritizer()
        tasks = data.get("tasks", [])
        context = data.get("context", {})
        next_task = prioritizer.suggest_next_task(tasks, context)
        return {"next_task": next_task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/prioritize/stats")
async def prioritization_stats():
    """Get prioritization statistics."""
    try:
        from core.context_aware_prioritizer import get_context_aware_prioritizer
        prioritizer = get_context_aware_prioritizer()
        return prioritizer.get_prioritization_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Wellness Nudger ───────────────────────────────────────────────────────

@router.post("/wellness/nudge")
async def detect_wellness_nudge(data: Dict[str, Any] = {}):
    """Detect wellness patterns and generate nudge."""
    try:
        from core.wellness_nudger import get_wellness_nudger
        nudger = get_wellness_nudger()
        return {"nudge": nudger.detect_and_nudge(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wellness/nudge/feedback")
async def nudge_feedback(data: Dict[str, Any] = {}):
    """Record nudge response."""
    try:
        from core.wellness_nudger import get_wellness_nudger
        nudger = get_wellness_nudger()
        nudger.record_nudge_response(data.get("nudge_id", ""), data.get("acted", False))
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wellness/nudge/stats")
async def nudge_stats():
    """Get nudge statistics."""
    try:
        from core.wellness_nudger import get_wellness_nudger
        nudger = get_wellness_nudger()
        return nudger.get_nudge_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Notification Filter ───────────────────────────────────────────────────

@router.post("/notifications/filter")
async def filter_notifications(data: Dict[str, Any] = {}):
    """Filter notifications by contextual relevance."""
    try:
        from core.notification_filter import get_notification_filter
        nf = get_notification_filter()
        notifications = data.get("notifications", [])
        context = data.get("context", {})
        return {"filtered": nf.filter_notifications(notifications, context)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/feedback")
async def notification_feedback(data: Dict[str, Any] = {}):
    """Record notification interaction feedback."""
    try:
        from core.notification_filter import get_notification_filter
        nf = get_notification_filter()
        nf.record_interaction(data.get("notif_id", ""), data.get("source", ""), data.get("acted", False))
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/filter/stats")
async def notification_filter_stats():
    """Get notification filter statistics."""
    try:
        from core.notification_filter import get_notification_filter
        nf = get_notification_filter()
        return nf.get_filter_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Deep Work Protector ───────────────────────────────────────────────────

@router.post("/focus/start")
async def start_focus_session(data: Dict[str, Any] = {}):
    """Start a protected focus session."""
    try:
        from core.deep_work_protector import get_deep_work_protector
        protector = get_deep_work_protector()
        session = protector.start_session(
            data.get("duration_minutes", 25),
            data.get("context", "")
        )
        return {"session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/focus/end")
async def end_focus_session():
    """End the current focus session."""
    try:
        from core.deep_work_protector import get_deep_work_protector
        protector = get_deep_work_protector()
        session = protector.end_session()
        return {"session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/focus/status")
async def focus_status():
    """Get current focus session status."""
    try:
        from core.deep_work_protector import get_deep_work_protector
        protector = get_deep_work_protector()
        return {
            "active": protector.is_focus_mode(),
            "session": protector.get_active_session(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/focus/stats")
async def focus_stats():
    """Get focus session statistics."""
    try:
        from core.deep_work_protector import get_deep_work_protector
        protector = get_deep_work_protector()
        return protector.get_focus_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Energy Forecaster ─────────────────────────────────────────────────────

@router.get("/energy/forecast")
async def energy_forecast(hours_ahead: int = 4):
    """Forecast energy levels for upcoming hours."""
    try:
        from core.energy_forecaster import get_energy_forecaster
        ef = get_energy_forecaster()
        return {"forecasts": ef.forecast_energy(hours_ahead)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/energy/report")
async def report_energy(data: Dict[str, Any] = {}):
    """Report actual energy level."""
    try:
        from core.energy_forecaster import get_energy_forecaster
        ef = get_energy_forecaster()
        ef.report_actual_energy(data.get("level", 0.5), data.get("factors"), data.get("activity", ""))
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy/insights")
async def energy_insights():
    """Get energy pattern insights."""
    try:
        from core.energy_forecaster import get_energy_forecaster
        ef = get_energy_forecaster()
        return ef.get_energy_insights()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/energy/recommendations")
async def energy_recommendations(data: Dict[str, Any] = {}):
    """Get task timing recommendations based on energy forecast."""
    try:
        from core.energy_forecaster import get_energy_forecaster
        ef = get_energy_forecaster()
        return {"recommendations": ef.get_recommendations(data.get("tasks", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Smart Break Suggester ─────────────────────────────────────────────────

@router.post("/breaks/suggest")
async def suggest_break(data: Dict[str, Any] = {}):
    """Suggest a break based on current context."""
    try:
        from core.smart_break_suggester import get_smart_break_suggester
        sbs = get_smart_break_suggester()
        return {"suggestion": sbs.suggest_break(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breaks/schedule")
async def optimal_schedule(data: Dict[str, Any] = {}):
    """Get optimal task+break schedule."""
    try:
        from core.smart_break_suggester import get_smart_break_suggester
        sbs = get_smart_break_suggester()
        return {"schedule": sbs.get_optimal_schedule(data.get("tasks", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breaks/record")
async def record_break(data: Dict[str, Any] = {}):
    """Record that a break was taken."""
    try:
        from core.smart_break_suggester import get_smart_break_suggester
        sbs = get_smart_break_suggester()
        sbs.record_break_taken(
            data.get("suggestion_id", ""),
            data.get("break_type", ""),
            data.get("planned_duration", 0),
            data.get("actual_duration", 0.0),
            data.get("activities", []),
        )
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breaks/effectiveness")
async def break_effectiveness(data: Dict[str, Any] = {}):
    """Record break effectiveness."""
    try:
        from core.smart_break_suggester import get_smart_break_suggester
        sbs = get_smart_break_suggester()
        sbs.record_break_effectiveness(
            data.get("break_id", ""),
            data.get("effectiveness", 0.5),
            data.get("post_break_energy", 0.5),
        )
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breaks/stats")
async def break_stats():
    """Get break statistics."""
    try:
        from core.smart_break_suggester import get_smart_break_suggester
        sbs = get_smart_break_suggester()
        return sbs.get_break_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Router Registration ───────────────────────────────────────────────────


def register_modern_routes(app):
    """Register all modern AI routes with the FastAPI app."""
    app.include_router(router)
