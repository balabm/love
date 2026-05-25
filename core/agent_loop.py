"""
LOVE Agent Loop — ReAct (Reason + Act) executor.

Runs a structured thought → tool_call → observation loop until the LLM
produces a final answer or hits the step limit.

Design:
  - Each step: LLM outputs either a THOUGHT+ACTION block or a FINAL_ANSWER block
  - Supports both JSON tool calls (```json ... ```) and inline XML-style tags
  - Emits step events to the neural bus for UI streaming
  - Records full trace for transparency / audit
  - Detects tool needs from the user query before running the loop

Usage:
    from core.agent_loop import run_agent_loop, needs_agent_loop

    if needs_agent_loop(user_message):
        result = run_agent_loop(user_message, context=context_str)
        # result.final_answer, result.steps, result.success
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class LoopStep:
    step: int
    thought: str
    tool_name: Optional[str]
    tool_params: Dict[str, Any]
    observation: str
    duration_ms: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LoopResult:
    success: bool
    final_answer: str
    steps: List[LoopStep] = field(default_factory=list)
    total_steps: int = 0
    total_ms: int = 0
    stopped_reason: str = ""   # "final_answer" | "max_steps" | "error"
    error: str = ""


# ── Trigger detection — when to use the agent loop ───────────────────────────

_TOOL_TRIGGER_PATTERNS = [
    # Web / research
    r"\b(search|google|look up|find out|what is the latest|current price|news about|research)\b",
    # File ops
    r"\b(read|open|write|save|create|delete|list files|show me the file|edit the file)\b",
    # Shell / system
    r"\b(run|execute|terminal|command|install|build|compile|ping|check if)\b",
    # Finance / live data
    r"\b(btc|eth|bitcoin|ethereum|stock|price|crypto|market)\b",
    # Memory
    r"\b(remember|recall|did I|last time|history|past conversations?)\b",
    # Calculation
    r"\b(calculate|compute|how many|how much|percentage|math|formula)\b",
    # Notification
    r"\b(notify|remind|alert|ping me|send me)\b",
]

_TOOL_TRIGGER_RE = re.compile(
    "|".join(_TOOL_TRIGGER_PATTERNS), re.IGNORECASE
)


def needs_agent_loop(message: str) -> bool:
    """Return True if this message should go through the ReAct loop."""
    return bool(_TOOL_TRIGGER_RE.search(message))


# ── System prompt for the ReAct loop ─────────────────────────────────────────

def _build_system_prompt(tool_schema: str, context: str = "") -> str:
    ctx_block = f"\n\nCurrent context:\n{context}" if context else ""
    return f"""You are LOVE, an autonomous AI companion running a tool-use loop.
You have access to real tools. Use them when you need live data, files, or computation.{ctx_block}

Available tools:
{tool_schema}

## Format rules (STRICT)

For EVERY response, start with your reasoning:
<thought>
Your step-by-step reasoning here.
</thought>

If you need a tool, immediately follow with a tool call:
```json
{{"tool": "tool_name", "params": {{"arg1": "value1"}}}}
```

If you have enough information to answer without more tools:
<final_answer>
Your complete, helpful answer here.
</final_answer>

## Rules
- Never fabricate tool results. Only use real observations.
- Keep thoughts concise (1-3 sentences max).
- If a tool returns an error, try an alternative approach or acknowledge the limitation.
- After receiving an observation, decide whether you need another tool or can answer.
- Maximum {'{MAX_STEPS}'} steps. After that you MUST give a final_answer.
"""


# ── Response parser ───────────────────────────────────────────────────────────

def _parse_response(text: str) -> Dict[str, Any]:
    """Parse LLM response into thought, tool_call, and/or final_answer."""
    result = {"thought": "", "tool_name": None, "tool_params": {}, "final_answer": None}

    # Extract thought
    thought_m = re.search(r"<thought>(.*?)</thought>", text, re.DOTALL)
    if thought_m:
        result["thought"] = thought_m.group(1).strip()
    else:
        # Fallback: everything before a ```json block or <final_answer>
        pre = re.split(r"```json|<final_answer>", text)[0].strip()
        result["thought"] = pre[:500]

    # Extract final answer
    fa_m = re.search(r"<final_answer>(.*?)</final_answer>", text, re.DOTALL)
    if fa_m:
        result["final_answer"] = fa_m.group(1).strip()
        return result

    # Also accept plain FINAL_ANSWER tag (swarm.py style)
    fa_m2 = re.search(r"<FINAL_ANSWER>(.*?)</FINAL_ANSWER>", text, re.DOTALL)
    if fa_m2:
        result["final_answer"] = fa_m2.group(1).strip()
        return result

    # Extract tool call from ```json block
    json_m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_m:
        try:
            call = json.loads(json_m.group(1))
            result["tool_name"] = call.get("tool") or call.get("tool_name")
            result["tool_params"] = call.get("params") or call.get("parameters") or {}
        except json.JSONDecodeError:
            result["thought"] += "\n[Parse error on tool call JSON]"

    return result


# ── Main loop ─────────────────────────────────────────────────────────────────

MAX_STEPS = 8


def run_agent_loop(
    query: str,
    context: str = "",
    max_steps: int = MAX_STEPS,
    allowed_tools: Optional[List[str]] = None,
) -> LoopResult:
    """
    Run a full ReAct loop for the given query.

    Args:
        query: The user's request / task.
        context: Optional context string injected into the system prompt.
        max_steps: Maximum tool-use steps before forcing a final answer.
        allowed_tools: If set, only these tool names are available.

    Returns:
        LoopResult with final_answer and step trace.
    """
    from core.tool_registry import get_tool_registry
    from core.llm import route_llm

    registry = get_tool_registry()
    loop_start = time.time()
    steps: List[LoopStep] = []

    # Filter tools if needed
    if allowed_tools:
        schema_dict = {n: d for n, d in registry.tools.items() if n in allowed_tools}
        schema_str = json.dumps([
            {"name": n, "description": d["description"], "parameters": d["parameters"]}
            for n, d in schema_dict.items()
        ], indent=2)
    else:
        schema_str = registry.get_tool_schema()

    system_prompt = _build_system_prompt(schema_str, context).replace("{MAX_STEPS}", str(max_steps))
    conversation = f"{system_prompt}\n\nUser query: {query}\n"

    llm = route_llm(query)

    for step_num in range(1, max_steps + 1):
        step_start = time.time()

        try:
            raw = str(llm.invoke(conversation))
        except Exception as e:
            return LoopResult(
                success=False,
                final_answer="",
                steps=steps,
                total_steps=len(steps),
                total_ms=int((time.time() - loop_start) * 1000),
                stopped_reason="error",
                error=str(e),
            )

        parsed = _parse_response(raw)
        thought = parsed["thought"]
        tool_name = parsed["tool_name"]
        tool_params = parsed["tool_params"]
        final_answer = parsed["final_answer"]

        # ── Final answer ──
        if final_answer:
            steps.append(LoopStep(
                step=step_num,
                thought=thought,
                tool_name=None,
                tool_params={},
                observation="[final answer]",
                duration_ms=int((time.time() - step_start) * 1000),
            ))
            _emit_event("final_answer", step_num, thought, None, {}, final_answer)
            return LoopResult(
                success=True,
                final_answer=final_answer,
                steps=steps,
                total_steps=len(steps),
                total_ms=int((time.time() - loop_start) * 1000),
                stopped_reason="final_answer",
            )

        # ── Tool call ──
        if tool_name:
            # Check tool allowed
            if allowed_tools and tool_name not in allowed_tools:
                observation = f"Tool '{tool_name}' is not permitted in this context."
            elif tool_name not in registry.tools:
                observation = f"Unknown tool '{tool_name}'. Available: {list(registry.tools.keys())[:10]}"
            else:
                try:
                    obs_raw = registry.execute_tool(tool_name, tool_params)
                    observation = str(obs_raw)[:3000]
                except Exception as e:
                    observation = f"Tool error: {e}"

            step = LoopStep(
                step=step_num,
                thought=thought,
                tool_name=tool_name,
                tool_params=tool_params,
                observation=observation,
                duration_ms=int((time.time() - step_start) * 1000),
            )
            steps.append(step)
            _emit_event("tool_call", step_num, thought, tool_name, tool_params, observation)

            # Feed observation back
            conversation += (
                f"\nAssistant (step {step_num}):\n{raw}\n"
                f"\nObservation from {tool_name}:\n{observation}\n"
                f"\nContinue reasoning. If done, use <final_answer>...</final_answer>.\n"
            )
        else:
            # LLM gave neither tool nor final answer — nudge it
            conversation += (
                f"\nAssistant (step {step_num}):\n{raw}\n"
                f"\nYou must either call a tool or provide <final_answer>. What is your next step?\n"
            )
            steps.append(LoopStep(
                step=step_num,
                thought=thought or raw[:200],
                tool_name=None,
                tool_params={},
                observation="[no action — nudging]",
                duration_ms=int((time.time() - step_start) * 1000),
            ))

    # Max steps reached — force final answer
    try:
        force_prompt = conversation + (
            f"\n\nYou have used {max_steps} steps. "
            "Summarize everything you know and give your best final answer NOW using <final_answer>...</final_answer>."
        )
        raw = str(llm.invoke(force_prompt))
        parsed = _parse_response(raw)
        final = parsed.get("final_answer") or parsed.get("thought") or raw[:1000]
    except Exception as e:
        final = f"Agent loop exhausted {max_steps} steps. Last observation: {steps[-1].observation if steps else 'none'}"

    return LoopResult(
        success=True,
        final_answer=final,
        steps=steps,
        total_steps=len(steps),
        total_ms=int((time.time() - loop_start) * 1000),
        stopped_reason="max_steps",
    )


# ── Neural bus event emitter ──────────────────────────────────────────────────

def _emit_event(event_type: str, step: int, thought: str, tool: Optional[str],
                params: dict, observation: str):
    try:
        from core.neural_bus import get_neural_bus
        get_neural_bus().publish(
            event_type=f"agent_loop.{event_type}",
            domain="agent_loop",
            payload={
                "step": step,
                "thought": thought[:200],
                "tool": tool,
                "params": {k: str(v)[:100] for k, v in (params or {}).items()},
                "observation": observation[:300],
            },
        )
    except Exception:
        pass


# ── Convenience wrapper ───────────────────────────────────────────────────────

def run_loop_for_query(query: str, context: str = "") -> str:
    """
    Simple wrapper: run agent loop and return the final answer string.
    Falls back to empty string on failure.
    """
    result = run_agent_loop(query, context=context)
    return result.final_answer if result.success else (result.error or "")
