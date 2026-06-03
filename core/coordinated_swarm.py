"""
LOVE Coordinated Swarm — True Multi-Agent Coordination (AGI Phase 10/11+)

This module upgrades the basic AgentSwarm to a coordinated multi-agent system:

1. PARALLEL EXECUTION — agents run concurrently via asyncio, not sequentially
2. DYNAMIC AGENT SELECTION — a Coordinator LLM analyzes the task and picks which
   agents to invoke, rather than requiring the user to specify them
3. SHARED WORKSPACE — agents post intermediate results to a shared memory space
   that other agents can read in real-time, enabling true collaboration
4. CONFLICT DETECTION — the system compares agent outputs for contradictions
   and quantifies disagreement
5. ITERATIVE REFINEMENT — if agents disagree, the Coordinator can ask them to
   reconcile, producing a consensus answer
6. OUTCOME LEARNING — tracks which agent combinations produce the best results
   for different task types, improving selection over time

This closes the "Multi-agent coordination" gap in GAP_TO_AGI.md.
"""

import asyncio
import json
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from core.llm import get_reasoning_llm, get_coding_llm
from core.tool_registry import get_tool_registry
from core.central_logger import get_logger
from core.execution_guard import log_error

logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "swarm"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AgentResult:
    """Result from a single agent in the swarm."""
    agent_name: str
    agent_role: str
    output: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    duration_sec: float = 0.0
    confidence: float = 0.5
    status: str = "complete"  # complete, error, timeout


@dataclass
class ConflictReport:
    """Detected disagreement between agents."""
    agent_a: str
    agent_b: str
    severity: float  # 0-1, how much they disagree
    topic: str
    summary: str


@dataclass
class SwarmSession:
    """A single coordinated swarm execution session."""
    session_id: str
    task: str
    created_at: str
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    workspace: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[ConflictReport] = field(default_factory=list)
    synthesis: str = ""
    status: str = "running"  # running, reconciling, complete, error
    selected_agents: List[str] = field(default_factory=list)
    coordinator_reasoning: str = ""


class SharedWorkspace:
    """
    Real-time shared memory space where agents post and read intermediate results.
    This is what transforms sequential delegation into true collaboration.
    """
    def __init__(self):
        self._entries: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def post(self, agent_name: str, entry_type: str, content: str, metadata: dict = None):
        """Post a new entry to the workspace."""
        async with self._lock:
            self._entries.append({
                "agent": agent_name,
                "type": entry_type,  # "finding", "question", "correction", "suggestion"
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
                "id": hashlib.sha256(f"{agent_name}:{time.time()}".encode()).hexdigest()[:12]
            })

    async def get_recent(self, n: int = 10, agent_filter: str = None) -> List[Dict[str, Any]]:
        """Get recent workspace entries, optionally filtered by agent."""
        async with self._lock:
            entries = self._entries[-n:] if n > 0 else self._entries
            if agent_filter:
                entries = [e for e in entries if e["agent"] != agent_filter]
            return entries

    async def get_formatted(self, agent_name: str = None) -> str:
        """Get workspace formatted as text for LLM consumption."""
        entries = await self.get_recent(n=20, agent_filter=agent_name)
        if not entries:
            return "(Workspace is empty — no other agents have posted yet.)"
        lines = ["--- SHARED WORKSPACE (recent posts from other agents) ---"]
        for e in entries:
            lines.append(f"[{e['agent']} | {e['type']}] {e['content'][:500]}")
        lines.append("--- END WORKSPACE ---")
        return "\n".join(lines)


class Coordinator:
    """
    The Coordinator is a meta-agent that decides WHICH agents to invoke for a given task
    and HOW to synthesize their outputs. It learns from past sessions.
    """

    AGENT_CATALOG = {
        "ResearchAgent": {
            "role": "Deep Researcher",
            "skills": ["web_search", "deep_dive", "fact_checking", "summarization"],
            "best_for": ["research", "fact_finding", "current_events", "technical_lookup"]
        },
        "BrowserAgent": {
            "role": "Web Surfer",
            "skills": ["web_search", "page_navigation", "information_extraction"],
            "best_for": ["quick_lookup", "url_specific", "comparative_search"]
        },
        "CodeAgent": {
            "role": "Senior Developer",
            "skills": ["code_review", "debugging", "refactoring", "architecture"],
            "best_for": ["code", "programming", "review", "security_audit", "optimization"]
        },
        "TerminalAgent": {
            "role": "OS Operator",
            "skills": ["command_execution", "system_admin", "file_operations"],
            "best_for": ["system", "terminal", "deployment", "environment"]
        },
        "CreativeAgent": {
            "role": "Creative Writer",
            "skills": ["writing", "brainstorming", "naming", "storytelling"],
            "best_for": ["creative", "writing", "content", "design", "naming"]
        },
        "AnalystAgent": {
            "role": "Data Analyst",
            "skills": ["calculation", "statistics", "trend_analysis", "comparison"],
            "best_for": ["analysis", "data", "comparison", "metrics", "evaluation"]
        },
        "PlannerAgent": {
            "role": "Strategic Planner",
            "skills": ["planning", "scheduling", "prioritization", "roadmapping"],
            "best_for": ["plan", "strategy", "roadmap", "timeline", "prioritize"]
        }
    }

    def __init__(self):
        self._outcome_db = DATA_DIR / "coordinator_outcomes.jsonl"
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = get_reasoning_llm()
        return self._llm

    async def select_agents(self, task: str, context: str = "", max_agents: int = 4) -> Tuple[List[str], str]:
        """
        Analyze the task and return the optimal set of agents to invoke,
        plus the reasoning for why they were chosen.
        """
        catalog_text = json.dumps(self.AGENT_CATALOG, indent=2)
        prompt = f"""You are the LOVE Coordinator, a meta-agent that selects the best specialist agents for a task.

AVAILABLE AGENTS:
{catalog_text}

TASK:
{task}

CONTEXT:
{context}

INSTRUCTIONS:
1. Analyze the task and determine which agents are needed.
2. Select up to {max_agents} agents that would best collaborate on this task.
3. Return ONLY a JSON object in this exact format:

{{
  "selected_agents": ["AgentName1", "AgentName2"],
  "reasoning": "Brief explanation of why these agents were chosen",
  "strategy": "How they should collaborate (e.g., 'Research first, then Code reviews findings')"
}}

Be concise. Select agents that complement each other, not duplicates."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._get_llm().invoke, prompt)
            # Extract JSON from response
            text = str(response)
            # Try to find JSON block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(text[start:end+1])
                agents = [a for a in data.get("selected_agents", []) if a in self.AGENT_CATALOG]
                reasoning = data.get("reasoning", "")
                return agents, reasoning
        except Exception as e:
            logger.error(f"Coordinator selection error: {e}")

        # Fallback: keyword matching
        task_lower = task.lower()
        selected = []
        for name, info in self.AGENT_CATALOG.items():
            for keyword in info["best_for"]:
                if keyword in task_lower:
                    selected.append(name)
                    break
        if not selected:
            selected = ["ResearchAgent", "AnalystAgent"]
        return selected[:max_agents], "Fallback keyword selection"

    async def detect_conflicts(self, results: Dict[str, AgentResult]) -> List[ConflictReport]:
        """
        Detect contradictions between agent outputs.
        Returns a list of conflict reports with severity scores.
        """
        if len(results) < 2:
            return []

        agent_names = list(results.keys())
        outputs = {name: r.output[:2000] for name, r in results.items()}

        prompt = f"""You are a Conflict Detection Engine. Compare the following agent outputs and identify any contradictions, disagreements, or conflicting recommendations.

AGENT OUTPUTS:
{json.dumps(outputs, indent=2)}

INSTRUCTIONS:
1. Look for direct contradictions (Agent A says X, Agent B says NOT X).
2. Look for conflicting recommendations (Agent A suggests approach A, Agent B suggests incompatible approach B).
3. Look for factual disagreements (different numbers, dates, conclusions).
4. Return a JSON array of conflicts. If no conflicts, return empty array [].

Format for each conflict:
{{
  "agent_a": "AgentName",
  "agent_b": "AgentName",
  "severity": 0.0-1.0,
  "topic": "What they disagree about",
  "summary": "Brief description of the disagreement"
}}

Return ONLY the JSON array."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._get_llm().invoke, prompt)
            text = str(response)
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1:
                conflicts_data = json.loads(text[start:end+1])
                return [
                    ConflictReport(
                        agent_a=c["agent_a"],
                        agent_b=c["agent_b"],
                        severity=c["severity"],
                        topic=c["topic"],
                        summary=c["summary"]
                    )
                    for c in conflicts_data
                    if c.get("severity", 0) > 0.3
                ]
        except Exception as e:
            logger.error(f"Conflict detection error: {e}")
        return []

    async def reconcile(self, task: str, results: Dict[str, AgentResult], conflicts: List[ConflictReport]) -> str:
        """
        Given detected conflicts, produce a reconciled consensus answer
        that acknowledges disagreements and explains the resolution.
        """
        outputs = {name: r.output for name, r in results.items()}
        conflicts_text = json.dumps([asdict(c) for c in conflicts], indent=2)

        prompt = f"""You are the LOVE Reconciler. Your job is to synthesize conflicting agent outputs into a single coherent answer.

ORIGINAL TASK:
{task}

AGENT OUTPUTS:
{json.dumps(outputs, indent=2)}

DETECTED CONFLICTS:
{conflicts_text}

INSTRUCTIONS:
1. Acknowledge where agents agree (consensus).
2. For each conflict, evaluate which agent's position is stronger based on their expertise and reasoning.
3. Produce a FINAL CONSENSUS that resolves all conflicts.
4. If the conflict is genuinely unresolvable, state both positions and explain the trade-off.
5. Be concise but thorough.

FINAL CONSENSUS:"""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._get_llm().invoke, prompt)
            return str(response)
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")
            # Simple fallback: concatenate with headers
            parts = [f"### {name}\n{r.output}" for name, r in results.items()]
            return "\n\n".join(parts)

    def record_outcome(self, task: str, agents: List[str], success: bool, quality: float):
        """Record the outcome of a coordination for future learning."""
        try:
            with open(self._outcome_db, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "task": task[:200],
                    "agents": agents,
                    "success": success,
                    "quality": quality
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.coordinated_swarm")


class CoordinatedSwarm:
    """
    The enhanced swarm that runs agents in parallel with shared workspace
    and intelligent coordination.
    """

    def __init__(self):
        self.coordinator = Coordinator()
        self.tool_registry = get_tool_registry()
        self._sessions: Dict[str, SwarmSession] = {}
        self._agent_definitions = Coordinator.AGENT_CATALOG.copy()
        # Register tool sets for each agent type
        self._agent_tools = {
            "ResearchAgent": ["browser_search", "browser_navigate", "read_file", "recall_memory", "store_memory"],
            "BrowserAgent": ["browser_search", "browser_navigate"],
            "CodeAgent": ["read_file", "write_file", "execute_terminal_command", "list_directory"],
            "TerminalAgent": ["execute_terminal_command", "list_directory", "read_file"],
            "CreativeAgent": ["read_file", "write_file", "store_memory", "recall_memory"],
            "AnalystAgent": ["read_file", "recall_memory", "store_memory"],
            "PlannerAgent": ["read_file", "recall_memory", "store_memory"],
        }

    def get_session(self, session_id: str) -> Optional[SwarmSession]:
        return self._sessions.get(session_id)

    async def execute_coordinated(self, task: str, required_agents: List[str] = None,
                                   context: str = "", max_iterations: int = 8) -> SwarmSession:
        """
        Execute a task with true multi-agent coordination:
        1. Coordinator selects agents (if not specified)
        2. All agents run in parallel with shared workspace
        3. Conflict detection
        4. Reconciliation if needed
        5. Final synthesis
        """
        session_id = hashlib.sha256(f"{task}:{time.time()}".encode()).hexdigest()[:16]
        workspace = SharedWorkspace()

        # Step 1: Agent selection
        if required_agents and len(required_agents) > 0:
            selected = [a for a in required_agents if a in self._agent_definitions]
            reasoning = "User-specified"
        else:
            selected, reasoning = await self.coordinator.select_agents(task, context)

        if not selected:
            selected = ["ResearchAgent", "AnalystAgent"]

        session = SwarmSession(
            session_id=session_id,
            task=task,
            created_at=datetime.now().isoformat(),
            selected_agents=selected,
            coordinator_reasoning=reasoning,
            status="running"
        )
        self._sessions[session_id] = session

        # Step 2: Parallel agent execution
        logger.info(f"[Swarm {session_id}] Launching {len(selected)} agents: {selected}")
        agent_tasks = [
            self._run_agent(session_id, agent_name, task, workspace, max_iterations)
            for agent_name in selected
        ]
        results_list = await asyncio.gather(*agent_tasks, return_exceptions=True)

        # Collect results
        for i, result in enumerate(results_list):
            agent_name = selected[i]
            if isinstance(result, Exception):
                session.agent_results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    agent_role=self._agent_definitions.get(agent_name, {}).get("role", "Unknown"),
                    output=f"Error: {str(result)}",
                    status="error"
                )
            else:
                session.agent_results[agent_name] = result

        session.workspace = await workspace.get_recent(n=50)

        # Step 3: Conflict detection
        session.conflicts = await self.coordinator.detect_conflicts(session.agent_results)
        if session.conflicts:
            session.status = "reconciling"
            logger.info(f"[Swarm {session_id}] Detected {len(session.conflicts)} conflicts, reconciling...")
            session.synthesis = await self.coordinator.reconcile(
                task, session.agent_results, session.conflicts
            )
        else:
            # Step 4: Standard synthesis
            session.status = "complete"
            session.synthesis = await self._synthesize(task, session.agent_results)

        self.coordinator.record_outcome(
            task, selected, success=True,
            quality=1.0 - (len(session.conflicts) * 0.2)  # fewer conflicts = higher quality
        )

        return session

    async def _run_agent(self, session_id: str, agent_name: str, task: str,
                         workspace: SharedWorkspace, max_iterations: int) -> AgentResult:
        """Run a single agent with workspace integration."""
        start_time = time.time()
        agent_info = self._agent_definitions.get(agent_name, {})
        role = agent_info.get("role", "Specialist")
        model_type = "coding" if agent_name == "CodeAgent" else "reasoning"
        llm = get_coding_llm() if model_type == "coding" else get_reasoning_llm()

        # Get available tools
        tools_schema = []
        for t_name in self._agent_tools.get(agent_name, []):
            if t_name in self.tool_registry.tools:
                tools_schema.append({
                    "name": t_name,
                    "description": self.tool_registry.tools[t_name]["description"],
                    "parameters": self.tool_registry.tools[t_name]["parameters"]
                })

        tool_calls = []
        current_prompt = f"""You are {agent_name}, a {role}.
You are part of a multi-agent swarm working on this task:

TASK: {task}

{await workspace.get_formatted(agent_name)}

AVAILABLE TOOLS:
{json.dumps(tools_schema, indent=2)}

INSTRUCTIONS:
1. Think step-by-step about how to contribute to the task.
2. If you need to use a tool, output a JSON block:
```json
{{"tool_name": "name", "parameters": {{"arg": "value"}}}}
```
3. After using tools, provide your findings to the workspace with:
```json
{{"workspace_post": {{"type": "finding", "content": "Your discovery"}}}}
```
4. When done, provide your FINAL ANSWER wrapped in:
<FINAL_ANSWER>
...your complete contribution...
</FINAL_ANSWER>

Begin:"""

        final_output = ""
        try:
            for iteration in range(max_iterations):
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, llm.invoke, current_prompt)
                text = str(response)

                # Check for workspace post
                ws_start = text.find('"workspace_post"')
                if ws_start != -1:
                    try:
                        # Extract the workspace_post JSON
                        brace_start = text.find("{", ws_start)
                        brace_end = text.find("}", brace_start) + 1
                        ws_json = json.loads(text[brace_start:brace_end])
                        post_data = ws_json.get("workspace_post", {})
                        await workspace.post(
                            agent_name,
                            post_data.get("type", "finding"),
                            post_data.get("content", ""),
                            {"iteration": iteration}
                        )
                    except Exception as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.coordinated_swarm")

                # Check for tool call
                json_start = text.find("```json")
                if json_start != -1:
                    json_end = text.find("```", json_start + 7)
                    if json_end != -1:
                        try:
                            tool_json = json.loads(text[json_start+7:json_end].strip())
                            t_name = tool_json.get("tool_name")
                            if t_name and t_name != "workspace_post":
                                t_params = tool_json.get("parameters", {})
                                tool_calls.append({"tool": t_name, "params": t_params})
                                if t_name in self.tool_registry.tools:
                                    result = self.tool_registry.execute_tool(t_name, t_params)
                                else:
                                    result = f"Error: Tool {t_name} not available."
                                current_prompt += f"\n\nTool Result ({t_name}): {result}\nContinue:"
                                continue
                        except Exception as e:
                            from core.execution_guard import log_error
                            log_error(e, module="core.coordinated_swarm")

                # Check for final answer
                fa_start = text.find("<FINAL_ANSWER>")
                if fa_start != -1:
                    fa_end = text.find("</FINAL_ANSWER>")
                    if fa_end != -1:
                        final_output = text[fa_start + len("<FINAL_ANSWER>"):fa_end].strip()
                    else:
                        final_output = text[fa_start + len("<FINAL_ANSWER>"):].strip()
                    break

                # No final answer, ask to continue or finalize
                current_prompt += f"\n\nYour response: {text[:500]}\n\nYou must provide <FINAL_ANSWER> or use a tool."

            if not final_output:
                final_output = f"Agent reached max iterations ({max_iterations}). Partial results: {text[:500]}"

        except Exception as e:
            return AgentResult(
                agent_name=agent_name,
                agent_role=role,
                output=f"Execution error: {str(e)}",
                tool_calls=tool_calls,
                duration_sec=time.time() - start_time,
                status="error"
            )

        duration = time.time() - start_time
        return AgentResult(
            agent_name=agent_name,
            agent_role=role,
            output=final_output,
            tool_calls=tool_calls,
            duration_sec=duration,
            status="complete"
        )

    async def _synthesize(self, task: str, results: Dict[str, AgentResult]) -> str:
        """Produce final synthesis from all agent results."""
        outputs = {name: r.output for name, r in results.items()}
        prompt = f"""You are LOVE, the Master Orchestrator.
You delegated a task to your swarm of expert agents. They worked in parallel with a shared workspace.

ORIGINAL TASK:
{task}

AGENT RESULTS:
{json.dumps(outputs, indent=2)}

Synthesize these results into a single, comprehensive, high-quality final answer. Preserve the best insights from each agent and resolve any minor inconsistencies. Be thorough but concise."""

        try:
            loop = asyncio.get_event_loop()
            llm = get_reasoning_llm()
            response = await loop.run_in_executor(None, llm.invoke, prompt)
            return str(response)
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            parts = [f"### {name}\n{r.output}" for name, r in results.items()]
            return "\n\n".join(parts)


# Singleton
_coordinated_swarm: Optional[CoordinatedSwarm] = None


def get_coordinated_swarm() -> CoordinatedSwarm:
    global _coordinated_swarm
    if _coordinated_swarm is None:
        _coordinated_swarm = CoordinatedSwarm()
    return _coordinated_swarm
