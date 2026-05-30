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


# ── Router Registration ───────────────────────────────────────────────────


def register_modern_routes(app):
    """Register all modern AI routes with the FastAPI app."""
    app.include_router(router)
