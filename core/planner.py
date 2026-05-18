"""
LOVE Planner — Multi-Step Task Execution Engine

When Karthi asks something complex, LOVE doesn't just answer.
She plans, executes, recovers, and synthesizes.

Examples:
  "Compare the iPhone 16 and Galaxy S25 and tell me which is better for me"
  → Step 1: Search iPhone 16 specs
  → Step 2: Search Galaxy S25 specs
  → Step 3: Search reviews/comparisons
  → Step 4: Cross-reference with Karthi's profile (budget, preferences)
  → Step 5: Synthesize recommendation

  "Summarize my last 5 emails and tell me what I need to do"
  → Step 1: Fetch emails via Microsoft bridge
  → Step 2: Summarize each
  → Step 3: Extract action items
  → Step 4: Prioritize based on calendar context
  → Step 5: Present clear task list
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLAN_LOG = DATA_DIR / "planner.jsonl"


@dataclass
class Step:
    id: int
    description: str
    tool: str  # "search", "memory", "ocr", "describe", "ms_graph", "llm", "file_read"
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending / running / done / failed / skipped
    error: str = ""
    duration_ms: int = 0


@dataclass
class Plan:
    goal: str
    steps: List[Step]
    context: Dict[str, Any] = field(default_factory=dict)
    final_answer: str = ""
    created_at: str = ""
    completed_at: str = ""
    status: str = "planning"  # planning / executing / done / failed


def _log(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(PLAN_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _get_llm():
    from core.llm import get_reasoning_llm
    return get_reasoning_llm(temperature=0.3, max_tokens=800)


def _step_search(step: Step) -> Step:
    """Execute a web search step."""
    try:
        from core.internet import research_topic
        query = step.input_data.get("query", "")
        depth = step.input_data.get("depth", 2)
        result = research_topic(query, depth=depth)
        step.output_data = result
        step.status = "done"
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


def _step_memory(step: Step) -> Step:
    """Query LOVE's memory."""
    try:
        from core.memory import recall_memory
        query = step.input_data.get("query", "")
        mode = step.input_data.get("mode", "general")
        result = recall_memory(query, mode=mode, n=step.input_data.get("n", 5))
        step.output_data = {"recalled": result}
        step.status = "done"
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


def _step_ocr(step: Step) -> Step:
    """Run OCR on an image."""
    try:
        from core.vision import read_image_text
        path = step.input_data.get("image_path", "")
        result = read_image_text(path)
        step.output_data = result
        step.status = "done" if result.get("success") else "failed"
        if not result.get("success"):
            step.error = result.get("error", "OCR failed")
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


def _step_describe(step: Step) -> Step:
    """Describe an image."""
    try:
        from core.vision import describe_image
        path = step.input_data.get("image_path", "")
        result = describe_image(path, detail_level=step.input_data.get("detail", "normal"))
        step.output_data = result
        step.status = "done" if result.get("success") else "failed"
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


def _step_ms_graph(step: Step) -> Step:
    """Query Microsoft Graph (emails, calendar, teams)."""
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge()
        resource = step.input_data.get("resource", "email")
        if resource == "email":
            result = ms.get_email(count=step.input_data.get("count", 5))
        elif resource == "calendar":
            result = ms.get_calendar()
        elif resource == "teams":
            result = ms.get_teams_messages()
        else:
            result = {"error": f"Unknown resource: {resource}"}
        step.output_data = result
        step.status = "done"
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


def _step_file_read(step: Step) -> Step:
    """Read a file from disk."""
    try:
        path = Path(step.input_data.get("path", ""))
        if not path.exists():
            step.status = "failed"
            step.error = "File not found"
            return step
        content = path.read_text(encoding="utf-8", errors="ignore")
        step.output_data = {"content": content[:5000], "path": str(path), "size": path.stat().st_size}
        step.status = "done"
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


def _step_llm_reason(step: Step) -> Step:
    """Run an LLM reasoning step."""
    try:
        prompt = step.input_data.get("prompt", "")
        llm = _get_llm()
        result = llm.invoke(prompt)
        step.output_data = {"response": result}
        step.status = "done"
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


def _step_capability(step: Step) -> Step:
    """Run an on-demand model capability."""
    try:
        from core.on_demand_models import run_capability
        cap_name = step.input_data.get("capability", "")
        kwargs = {k: v for k, v in step.input_data.items() if k != "capability"}
        result = run_capability(cap_name, **kwargs)
        step.output_data = result
        step.status = "done" if result.get("success") else "failed"
        if not result.get("success"):
            step.error = result.get("error", "Capability failed")
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    return step


TOOL_MAP = {
    "search": _step_search,
    "memory": _step_memory,
    "ocr": _step_ocr,
    "describe": _step_describe,
    "ms_graph": _step_ms_graph,
    "file_read": _step_file_read,
    "llm": _step_llm_reason,
    "capability": _step_capability,
}


# ── Planning ─────────────────────────────────────────────────────────────────

def create_plan(goal: str, context: Dict[str, Any] = None) -> Plan:
    """
    Use LLM to break a complex goal into executable steps.
    """
    ctx = context or {}
    available_tools = list(TOOL_MAP.keys())

    prompt = f"""You are LOVE's planning module. Break this user goal into concrete, executable steps.

Goal: {goal}

Available tools: {', '.join(available_tools)}
Tool descriptions:
- search: web search + page reading (input: query, depth)
- memory: query LOVE's memory (input: query, mode)
- ocr: extract text from image (input: image_path)
- describe: describe image contents (input: image_path, detail)
- ms_graph: query Microsoft email/calendar/teams (input: resource, count)
- file_read: read a local file (input: path)
- llm: run LLM reasoning (input: prompt)
- capability: run on-demand model (input: capability, plus capability-specific args)

Current context: {json.dumps(ctx, indent=2)[:500]}

Output a JSON array of steps. Each step:
{{ "description": "what this step does", "tool": "tool_name", "input_data": {{...}} }}

Rules:
- Maximum 6 steps
- Each step must use exactly one tool
- Steps should be independent when possible (parallelizable)
- Include a final llm step to synthesize results
- If the goal is simple (1 tool needed), return just 1-2 steps
- Use memory first if the goal references past conversations
- Use search for anything requiring real-time or external knowledge
"""

    try:
        llm = _get_llm()
        raw = llm.invoke(prompt)

        # Extract JSON
        import re
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            steps_json = json.loads(json_match.group())
        else:
            # Fallback: try parsing whole response
            steps_json = json.loads(raw)

        steps = []
        for i, s in enumerate(steps_json):
            steps.append(Step(
                id=i + 1,
                description=s.get("description", f"Step {i+1}"),
                tool=s.get("tool", "llm"),
                input_data=s.get("input_data", {}),
            ))

        plan = Plan(goal=goal, steps=steps, context=ctx)
        plan.created_at = datetime.now().isoformat()
        _log({"event": "plan_created", "goal": goal, "steps": len(steps)})
        return plan

    except Exception as e:
        # Fallback: single LLM reasoning step
        step = Step(id=1, description=f"Reason about: {goal}", tool="llm",
                    input_data={"prompt": goal})
        plan = Plan(goal=goal, steps=[step], context=ctx)
        plan.created_at = datetime.now().isoformat()
        return plan


def execute_plan(plan: Plan, max_parallel: int = 3) -> Plan:
    """
    Execute all steps in a plan. Independent steps can run in parallel.
    """
    plan.status = "executing"
    import concurrent.futures

    # Simple executor: run sequentially for now (safer)
    for step in plan.steps:
        if step.status != "pending":
            continue

        t0 = time.time()
        step.status = "running"
        executor = TOOL_MAP.get(step.tool)

        if not executor:
            step.status = "failed"
            step.error = f"Unknown tool: {step.tool}"
            continue

        step = executor(step)
        step.duration_ms = int((time.time() - t0) * 1000)

    plan.status = "done"
    plan.completed_at = datetime.now().isoformat()

    # Generate final answer if there's a synthesis step
    _synthesize(plan)
    _log({"event": "plan_executed", "goal": plan.goal, "status": plan.status,
          "steps_done": sum(1 for s in plan.steps if s.status == "done"),
          "steps_failed": sum(1 for s in plan.steps if s.status == "failed")})
    return plan


def _synthesize(plan: Plan):
    """Generate a final synthesized answer from all step outputs."""
    outputs = []
    for step in plan.steps:
        if step.status == "done" and step.output_data:
            out = step.output_data
            if "response" in out:
                outputs.append(f"[{step.description}]\n{out['response']}")
            elif "text" in out:
                outputs.append(f"[{step.description}]\n{out['text']}")
            elif "summary" in out:
                outputs.append(f"[{step.description}]\n{out['summary']}")
            elif "description" in out:
                outputs.append(f"[{step.description}]\n{out['description']}")
            elif "content" in out:
                outputs.append(f"[{step.description}]\n{out['content'][:500]}")
            else:
                outputs.append(f"[{step.description}]\n{json.dumps(out, indent=2)[:500]}")
        elif step.status == "failed":
            outputs.append(f"[{step.description}]\n[FAILED: {step.error}]")

    if not outputs:
        plan.final_answer = "I wasn't able to gather the information needed."
        return

    # Use LLM to synthesize
    try:
        synthesis_prompt = f"""You are LOVE, synthesizing information for Karthi.

Goal: {plan.goal}

Here are the results from my investigation:

{'\n\n---\n\n'.join(outputs)}

Now write a clear, concise final answer that directly addresses the goal.
Be specific. Cite sources where relevant. If some steps failed, acknowledge it
but focus on what was successfully found. Use warm, direct tone."""

        llm = _get_llm()
        plan.final_answer = llm.invoke(synthesis_prompt).strip()
    except Exception as e:
        plan.final_answer = f"I gathered some information but had trouble synthesizing it: {e}\n\nRaw results:\n" + "\n".join(outputs)


def plan_and_execute(goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    High-level entry: plan a goal, execute it, return result.
    """
    plan = create_plan(goal, context)
    plan = execute_plan(plan)
    return {
        "success": plan.status == "done",
        "goal": plan.goal,
        "final_answer": plan.final_answer,
        "steps": [asdict(s) for s in plan.steps],
        "plan_status": plan.status,
    }


def is_complex_query(user_input: str) -> bool:
    """
    Detect if a query needs multi-step planning vs simple chat.
    """
    complexity_signals = [
        r"\bcompare\b", r"\bversus\b", r"\bvs\b", r"\bdifference between\b",
        r"\bsummarize\b.*\blast\b", r"\bwhat.*(?:all|every|each)\b",
        r"\band then\b", r"\bstep by step\b", r"\bhow do I\b.*\band\b",
        r"\bresearch\b", r"\bfind out\b", r"\binvestigate\b",
        r"\bwhat should I\b", r"\brecommend\b", r"\bbest.*for me\b",
        r"\bcheck\b.*\band\b.*\btell me\b", r"\banalyze\b.*\band\b",
        r"\bread\b.*\band\b.*\bsummarize\b", r"\bextract\b.*\bfrom\b",
        r"\blook at\b.*\band\b", r"\bscreenshot\b.*\band\b",
    ]
    text = user_input.lower()
    score = sum(1 for p in complexity_signals if re.search(p, text))

    # Also check if multiple intents (has both question and command)
    has_and = text.count(" and ") >= 2 or text.count(",") >= 2
    if has_and:
        score += 1

    return score >= 2 or len(text) > 120


import re
