"""
LOVE MCP HTTP Server — Network-accessible MCP interface

Runs LOVE's MCP tools over HTTP so phones, tablets, and remote services
can interact with LOVE without stdio.

Start with: python mcp_server_http.py
Default port: 7432
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uvicorn

app = FastAPI(title="LOVE MCP HTTP", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ToolCallRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    message: str
    mode: str = "general"


@app.get("/")
def root():
    return {"status": "LOVE MCP HTTP running", "tools": [
        "chat", "memory_search", "get_context", "get_tasks",
        "record_mood", "get_insights", "evolution_status", "store_memory"
    ]}


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        from core.agent import chat
        result = chat(req.message, mode=req.mode)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/tool")
def tool_call(req: ToolCallRequest):
    """Generic tool call endpoint."""
    # Import and reuse the MCP server's tool handlers
    try:
        # Import handler from mcp_server
        sys.path.insert(0, str(PROJECT_ROOT))
        import importlib
        spec = importlib.util.spec_from_file_location("mcp_server", str(PROJECT_ROOT / "mcp_server.py"))
        if spec:
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                result = mod._handle_tool(req.tool, req.args)
                return {"success": True, "result": result}
            except Exception as e:
                pass
    except Exception:
        pass
    # Fallback: direct dispatch
    try:
        if req.tool == "love_chat":
            from core.agent import chat
            r = chat(req.args.get("message", ""), req.args.get("mode", "general"))
            return {"success": True, "result": r.get("response", "")}
        elif req.tool == "love_memory_search":
            from core.memory_architect import get_memory_architect
            ma = get_memory_architect()
            hits = ma.search(req.args.get("query", ""), limit=req.args.get("limit", 5))
            return {"success": True, "result": [h.item for h in hits]}
        else:
            raise HTTPException(400, f"Unknown tool: {req.tool}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/memory")
def search_memory(q: str, limit: int = 5):
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        hits = ma.search(q, limit=limit)
        return {"results": [{"tier": h.source_tier, "content": h.item.get("event", h.item.get("content", ""))} for h in hits]}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/status")
def status():
    info = {"status": "running"}
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        info["evolution_generation"] = evo.get_generation()
    except Exception:
        pass
    try:
        from core.constitution import get_constitution
        c = get_constitution()
        info["constitution_principles"] = c.get_stats().get("total_principles", 0)
    except Exception:
        pass
    return info


if __name__ == "__main__":
    print("LOVE MCP HTTP Server starting on http://0.0.0.0:7432")
    uvicorn.run(app, host="0.0.0.0", port=7432)
