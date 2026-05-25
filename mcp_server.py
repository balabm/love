"""
LOVE MCP Server — Model Context Protocol Interface

Exposes LOVE as an MCP server so it can be used by:
- Claude Desktop (via claude_desktop_config.json)
- Other AI agents that support MCP
- Any MCP-compatible client

Tools exposed:
- love_chat: Send a message to LOVE and get a response
- love_memory_search: Search LOVE's memory
- love_get_context: Get LOVE's current awareness snapshot
- love_get_tasks: Get current tasks and todos
- love_record_mood: Record an emotional/mood entry
- love_get_insights: Get cross-domain life insights
- love_get_evolution_status: Get LOVE's self-improvement status
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

server = Server("love")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="love_chat",
            description="Send a message to LOVE (your AI life companion) and get a thoughtful, context-aware response. LOVE remembers your history, tracks your emotions, tasks, and goals.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Your message to LOVE"},
                    "mode": {"type": "string", "description": "Mode: general, work, personal, emotional", "default": "general"}
                },
                "required": ["message"]
            }
        ),
        types.Tool(
            name="love_memory_search",
            description="Search LOVE's long-term memory for relevant past conversations, insights, and experiences.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for in memory"},
                    "limit": {"type": "integer", "description": "Max results to return", "default": 5}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="love_get_context",
            description="Get LOVE's current awareness snapshot: what apps are open, system state, recent activity.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="love_get_tasks",
            description="Get current tasks, overdue items, and today's focus list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter: all, overdue, today, in_progress", "default": "today"}
                }
            }
        ),
        types.Tool(
            name="love_record_mood",
            description="Record an emotional/mood entry for LOVE's emotional tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood_score": {"type": "integer", "description": "Mood score 1-10"},
                    "energy_level": {"type": "integer", "description": "Energy level 1-10"},
                    "emotions": {"type": "array", "items": {"type": "string"}, "description": "List of emotions"},
                    "notes": {"type": "string", "description": "Optional context note"}
                },
                "required": ["mood_score", "energy_level"]
            }
        ),
        types.Tool(
            name="love_get_insights",
            description="Get LOVE's cross-domain life insights: patterns across emotions, tasks, fitness, learning.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="love_get_evolution_status",
            description="Get LOVE's self-evolution status: current generation, active experiments, performance metrics.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="love_store_memory",
            description="Store something important in LOVE's long-term memory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "What to remember"},
                    "importance": {"type": "number", "description": "Importance 0.0-1.0", "default": 0.7}
                },
                "required": ["content"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _handle_tool, name, arguments)
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


def _handle_tool(name: str, args: dict) -> str:
    if name == "love_chat":
        return _tool_chat(args.get("message", ""), args.get("mode", "general"))
    elif name == "love_memory_search":
        return _tool_memory_search(args.get("query", ""), args.get("limit", 5))
    elif name == "love_get_context":
        return _tool_get_context()
    elif name == "love_get_tasks":
        return _tool_get_tasks(args.get("filter", "today"))
    elif name == "love_record_mood":
        return _tool_record_mood(args)
    elif name == "love_get_insights":
        return _tool_get_insights()
    elif name == "love_get_evolution_status":
        return _tool_evolution_status()
    elif name == "love_store_memory":
        return _tool_store_memory(args.get("content", ""), args.get("importance", 0.7))
    else:
        return f"Unknown tool: {name}"


def _tool_chat(message: str, mode: str = "general") -> str:
    try:
        from core.agent import chat
        result = chat(message, mode=mode)
        response = result.get("response", "")
        thinking = result.get("thinking", "")
        out = response
        if thinking:
            out = f"[Thinking: {thinking[:200]}...]\n\n{response}" if len(thinking) > 50 else response
        return out
    except Exception as e:
        return f"LOVE chat error: {e}"


def _tool_memory_search(query: str, limit: int = 5) -> str:
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        results = ma.search(query, limit=limit)
        if not results:
            # Fallback to conversation memory
            from core.memory import recall_memory
            past = recall_memory(query)
            return f"Conversation memory: {past}" if past else "No memories found."
        lines = [f"[{r.source_tier}] {r.item.get('event', r.item.get('content', ''))[:200]}" for r in results[:limit]]
        return "\n".join(lines)
    except Exception as e:
        return f"Memory search error: {e}"


def _tool_get_context() -> str:
    try:
        from core.context_engine import get_prompt_context
        return get_prompt_context()[:1500]
    except Exception as e:
        return f"Context unavailable: {e}"


def _tool_get_tasks(filter_type: str = "today") -> str:
    try:
        from agents.task_agent import TaskAgent
        ta = TaskAgent()
        if filter_type == "overdue":
            tasks = ta.get_overdue_tasks() if hasattr(ta, 'get_overdue_tasks') else []
        elif filter_type == "today":
            tasks = ta.get_todays_tasks() if hasattr(ta, 'get_todays_tasks') else []
        elif filter_type == "in_progress":
            tasks = [t for t in (ta.get_all_tasks() if hasattr(ta, 'get_all_tasks') else [])
                    if getattr(t, 'status', '') == 'in_progress']
        else:
            tasks = ta.get_all_tasks() if hasattr(ta, 'get_all_tasks') else []
        if not tasks:
            return "No tasks found."
        lines = []
        for t in tasks[:20]:
            title = getattr(t, 'title', str(t))
            status = getattr(t, 'status', '')
            priority = getattr(t, 'priority', '')
            lines.append(f"- [{priority}] {title} ({status})")
        return "\n".join(lines)
    except Exception as e:
        return f"Task retrieval error: {e}"


def _tool_record_mood(args: dict) -> str:
    try:
        from agents.emotional_agent import EmotionalAgent, MoodEntry
        ea = EmotionalAgent()
        entry = MoodEntry(
            timestamp=__import__('datetime').datetime.now().isoformat(),
            mood_score=args.get("mood_score", 5),
            energy_level=args.get("energy_level", 5),
            stress_level=args.get("stress_level", 5),
            emotions=args.get("emotions", []),
            notes=args.get("notes", ""),
        )
        if hasattr(ea, 'record_mood'):
            ea.record_mood(entry)
        return f"Mood recorded: score={entry.mood_score}, energy={entry.energy_level}"
    except Exception as e:
        return f"Mood recording error: {e}"


def _tool_get_insights() -> str:
    try:
        from core.orchestrator import NeuralOrchestrator
        orch = NeuralOrchestrator()
        patterns = getattr(orch, 'patterns', [])
        interventions = [i for i in getattr(orch, 'interventions', [])
                        if not getattr(i, 'dismissed', False)]
        lines = []
        for p in patterns[:3]:
            desc = getattr(p, 'description', str(p))
            lines.append(f"Pattern: {desc[:150]}")
        for i in interventions[:3]:
            msg = getattr(i, 'message', str(i))
            lines.append(f"Intervention: {msg[:150]}")
        if not lines:
            # Try cross-domain reasoning
            from core.cross_domain_reasoning import get_insights
            insights = get_insights() if callable(get_insights) else []
            for ins in (insights or [])[:5]:
                lines.append(str(ins)[:150])
        return "\n".join(lines) if lines else "No insights available yet. Keep using LOVE to build patterns."
    except Exception as e:
        return f"Insights error: {e}"


def _tool_evolution_status() -> str:
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        status = evo.get_status()
        return json.dumps(status, indent=2, default=str)
    except Exception as e:
        return f"Evolution status error: {e}"


def _tool_store_memory(content: str, importance: float = 0.7) -> str:
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        ma.store_episode(event=content, importance=importance, emotional_weight=0.3)
        return f"Stored in LOVE's memory (importance={importance})"
    except Exception as e:
        return f"Memory storage error: {e}"


# ── Claude Desktop Config Writer ──────────────────────────────────────────────

def write_claude_desktop_config():
    """Write the claude_desktop_config.json snippet for easy integration."""
    config = {
        "mcpServers": {
            "love": {
                "command": str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe"),
                "args": [str(PROJECT_ROOT / "mcp_server.py")],
                "env": {}
            }
        }
    }
    config_path = PROJECT_ROOT / "claude_desktop_config_snippet.json"
    config_path.write_text(json.dumps(config, indent=2))
    print(f"Claude Desktop config written to: {config_path}")
    print("Add the 'love' entry to your Claude Desktop config at:")
    print("  %APPDATA%\\Claude\\claude_desktop_config.json")


# ── Startup ───────────────────────────────────────────────────────────────────

async def main():
    write_claude_desktop_config()
    print("LOVE MCP Server starting...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
