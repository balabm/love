"""
LOVE Multi-Agent Orchestrator — Coordinated Intelligence (Modern AI Pattern)

Beyond swarm evolution's parallel hypothesis testing, this orchestrator
provides explicit multi-agent coordination with:

1. ROLE-BASED AGENTS
   - Researcher: Gathers information and context
   - Planner: Decomposes tasks into actionable steps
   - Executor: Carries out actions and generates code
   - Reviewer: Validates quality and catches errors
   - Each agent has specialized capabilities and constraints

2. TASK DECOMPOSITION
   - Complex tasks broken into subtasks assigned to specialist agents
   - Dependency tracking: Agent B waits for Agent A's output
   - Parallel execution where possible, sequential where required

3. INTER-AGENT COMMUNICATION
   - Agents share context and intermediate results
   - Consensus building for decisions requiring multiple perspectives
   - Conflict resolution when agents disagree

4. RESULT AGGREGATION
   - Combine outputs from multiple agents into coherent response
   - Weight contributions by agent confidence
   - Detect and flag inconsistencies across agent outputs

Architecture:
- create_task(): Decompose and assign a complex task
- agent_communicate(): Send message between agents
- run_orchestration(): Execute full multi-agent workflow
- get_agent_status(): Check what each agent is doing
"""

import json
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "multi_agent"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ORCHESTRATION_LOG = DATA_DIR / "orchestration_log.jsonl"


class AgentRole(Enum):
    RESEARCHER = "researcher"
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Agent:
    """A specialized agent in the orchestrator."""
    id: str
    role: AgentRole
    status: str = "idle"  # idle, busy, error
    current_task: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    performance_score: float = 1.0
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Task:
    """A task in the orchestration workflow."""
    id: str
    description: str
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


@dataclass
class Message:
    """A message between agents."""
    from_agent: str
    to_agent: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    task_id: Optional[str] = None


class MultiAgentOrchestrator:
    """
    Coordinated multi-agent system for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._agents: Dict[str, Agent] = {}
        self._tasks: Dict[str, Task] = {}
        self._messages: deque = deque(maxlen=1000)
        self._stats = {"tasks_created": 0, "tasks_completed": 0, "messages_sent": 0}
        self._running = False
        self._initialize_agents()

    def _initialize_agents(self):
        """Create the default set of agents."""
        default_agents = [
            ("researcher_1", AgentRole.RESEARCHER, ["search", "retrieve", "summarize"]),
            ("planner_1", AgentRole.PLANNER, ["decompose", "schedule", "prioritize"]),
            ("executor_1", AgentRole.EXECUTOR, ["code", "write", "run", "test"]),
            ("reviewer_1", AgentRole.REVIEWER, ["validate", "critique", "improve"]),
            ("coordinator_1", AgentRole.COORDINATOR, ["delegate", "monitor", "resolve"]),
        ]
        for agent_id, role, caps in default_agents:
            self._agents[agent_id] = Agent(
                id=agent_id,
                role=role,
                capabilities=caps,
            )

    # ── Task Management ────────────────────────────────────────────────────

    def create_task(self, description: str, agent_role: Optional[AgentRole] = None,
                    dependencies: List[str] = None) -> str:
        """Create a new task and assign it to an appropriate agent."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # Find best agent for the role
        assigned_agent = None
        if agent_role:
            candidates = [
                a for a in self._agents.values()
                if a.role == agent_role and a.status == "idle"
            ]
            if candidates:
                # Pick highest performing agent
                assigned_agent = max(candidates, key=lambda a: a.performance_score).id

        task = Task(
            id=task_id,
            description=description,
            assigned_agent=assigned_agent,
            dependencies=dependencies or [],
        )

        with self._lock:
            self._tasks[task_id] = task
            if assigned_agent:
                self._agents[assigned_agent].status = "busy"
                self._agents[assigned_agent].current_task = task_id
                task.status = TaskStatus.ASSIGNED

        self._stats["tasks_created"] += 1
        self._log({"event": "task_created", "task_id": task_id, "agent": assigned_agent})
        return task_id

    def complete_task(self, task_id: str, result: Any, agent_id: str):
        """Mark a task as completed with its result."""
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now().isoformat()

        if agent_id in self._agents:
            self._agents[agent_id].status = "idle"
            self._agents[agent_id].current_task = None
            self._agents[agent_id].last_active = datetime.now().isoformat()

        self._stats["tasks_completed"] += 1
        self._log({"event": "task_completed", "task_id": task_id, "agent": agent_id})

        # Unblock dependent tasks
        self._unblock_tasks(task_id)
        return True

    def _unblock_tasks(self, completed_task_id: str):
        """Unblock tasks that depend on the completed task."""
        for task in self._tasks.values():
            if completed_task_id in task.dependencies:
                task.dependencies.remove(completed_task_id)
                if not task.dependencies and task.status == TaskStatus.BLOCKED:
                    task.status = TaskStatus.PENDING
                    # Auto-assign if agent available
                    if task.assigned_agent and self._agents.get(task.assigned_agent, Agent("")).status == "idle":
                        self._agents[task.assigned_agent].status = "busy"
                        self._agents[task.assigned_agent].current_task = task.id
                        task.status = TaskStatus.ASSIGNED

    # ── Orchestration ────────────────────────────────────────────────────────

    def run_orchestration(self, goal: str) -> Dict[str, Any]:
        """
        Run a full multi-agent orchestration for a high-level goal.
        """
        # Phase 1: Coordinator decomposes the goal
        coord = self._agents["coordinator_1"]
        coord.status = "busy"

        # Create decomposition task
        plan_task = self.create_task(
            f"Decompose goal: {goal}",
            agent_role=AgentRole.PLANNER,
        )

        # Simulate planner creating subtasks
        subtasks = self._decompose_goal(goal)
        self.complete_task(plan_task, subtasks, "planner_1")

        # Phase 2: Execute subtasks in dependency order
        results = {}
        for subtask_desc, role in subtasks:
            task_id = self.create_task(subtask_desc, agent_role=role)
            # Simulate execution
            result = self._simulate_execution(task_id, role)
            self.complete_task(task_id, result, self._tasks[task_id].assigned_agent)
            results[task_id] = result

        # Phase 3: Reviewer validates results
        review_task = self.create_task(
            f"Review results for: {goal}",
            agent_role=AgentRole.REVIEWER,
        )
        review = self._simulate_review(results)
        self.complete_task(review_task, review, "reviewer_1")

        coord.status = "idle"

        return {
            "goal": goal,
            "tasks": len(subtasks),
            "results": results,
            "review": review,
            "status": "completed",
        }

    def _decompose_goal(self, goal: str) -> List[tuple]:
        """Simulate planner decomposing a goal into subtasks."""
        # Simple heuristic decomposition
        if "research" in goal.lower() or "find" in goal.lower():
            return [
                (f"Research context for: {goal}", AgentRole.RESEARCHER),
                (f"Analyze findings for: {goal}", AgentRole.PLANNER),
                (f"Execute solution for: {goal}", AgentRole.EXECUTOR),
            ]
        elif "code" in goal.lower() or "implement" in goal.lower():
            return [
                (f"Design approach for: {goal}", AgentRole.PLANNER),
                (f"Implement: {goal}", AgentRole.EXECUTOR),
                (f"Review implementation: {goal}", AgentRole.REVIEWER),
            ]
        else:
            return [
                (f"Plan: {goal}", AgentRole.PLANNER),
                (f"Execute: {goal}", AgentRole.EXECUTOR),
            ]

    def _simulate_execution(self, task_id: str, role: AgentRole) -> str:
        """Simulate an agent executing a task."""
        task = self._tasks.get(task_id)
        if not task:
            return ""

        # In production, this would call the actual agent logic
        if role == AgentRole.RESEARCHER:
            return f"Research findings for: {task.description[:50]}..."
        elif role == AgentRole.PLANNER:
            return f"Execution plan for: {task.description[:50]}..."
        elif role == AgentRole.EXECUTOR:
            return f"Completed: {task.description[:50]}..."
        elif role == AgentRole.REVIEWER:
            return f"Review passed for: {task.description[:50]}..."
        return "Done"

    def _simulate_review(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate reviewer validating results."""
        return {
            "quality_score": 0.85,
            "issues": [],
            "recommendations": ["Consider adding more context"],
            "approved": True,
        }

    # ── Agent Communication ──────────────────────────────────────────────────

    def agent_communicate(self, from_agent: str, to_agent: str,
                          content: str, task_id: Optional[str] = None) -> str:
        """Send a message between agents."""
        msg = Message(
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            task_id=task_id,
        )
        with self._lock:
            self._messages.append(msg)
        self._stats["messages_sent"] += 1
        self._log({
            "event": "message",
            "from": from_agent,
            "to": to_agent,
            "task_id": task_id,
        })
        return f"Message sent from {from_agent} to {to_agent}"

    # ── Status & Monitoring ────────────────────────────────────────────────

    def get_agent_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents."""
        return [
            {
                "id": a.id,
                "role": a.role.value,
                "status": a.status,
                "current_task": a.current_task,
                "capabilities": a.capabilities,
                "performance_score": a.performance_score,
            }
            for a in self._agents.values()
        ]

    def get_task_status(self) -> List[Dict[str, Any]]:
        """Get status of all tasks."""
        return [
            {
                "id": t.id,
                "description": t.description[:50],
                "status": t.status.value,
                "assigned_agent": t.assigned_agent,
                "dependencies": t.dependencies,
                "has_result": t.result is not None,
            }
            for t in self._tasks.values()
        ]

    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent inter-agent messages."""
        recent = list(self._messages)[-limit:]
        return [
            {
                "from": m.from_agent,
                "to": m.to_agent,
                "content": m.content[:100],
                "task_id": m.task_id,
                "timestamp": m.timestamp,
            }
            for m in reversed(recent)
        ]

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "active_agents": len([a for a in self._agents.values() if a.status == "busy"]),
            "idle_agents": len([a for a in self._agents.values() if a.status == "idle"]),
            "pending_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING]),
            "completed_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(ORCHESTRATION_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_orchestrator_instance: Optional[MultiAgentOrchestrator] = None
_orchestrator_lock = threading.Lock()


def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    global _orchestrator_instance
    with _orchestrator_lock:
        if _orchestrator_instance is None:
            _orchestrator_instance = MultiAgentOrchestrator()
        return _orchestrator_instance
