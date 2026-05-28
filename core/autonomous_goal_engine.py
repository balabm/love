"""
LOVE Autonomous Goal Engine

LOVE doesn't just track goals — it pursues them.

While you're away (or even while you're there), LOVE:
1. Reads your active goals from the goal system
2. Breaks each goal into actionable sub-tasks
3. Executes sub-tasks that don't need you (research, file management, planning)
4. Reports back what it did and what it needs from you
5. Updates goal progress based on evidence

This is the difference between a goal tracker and an autonomous life OS.

Goals it can pursue without you:
- Research: gather information on topics relevant to your goals
- Planning: draft detailed action plans with timelines
- Monitoring: track relevant external events (news, prices, dates)
- Memory: consolidate learnings related to the goal
- Preparation: prep materials, summaries, or reminders for when you return

Goals it asks you about:
- Decisions requiring your judgment
- Actions requiring your physical presence
- Anything ambiguous
"""

import json
import time
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GOALS_DIR = DATA_DIR / "autonomous_goals"
GOALS_FILE = GOALS_DIR / "goals.json"
EXECUTION_LOG = GOALS_DIR / "execution_log.jsonl"
GOALS_DIR.mkdir(parents=True, exist_ok=True)


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class Goal:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    title: str = ""
    description: str = ""
    category: str = "personal"  # personal, work, fitness, finance, learning
    priority: str = "medium"  # low, medium, high, critical
    status: str = "active"  # active, paused, completed, abandoned
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    target_date: Optional[str] = None
    progress_pct: float = 0.0
    sub_goals: List[str] = field(default_factory=list)  # sub-goal IDs
    evidence: List[str] = field(default_factory=list)  # evidence of progress
    last_worked_on: Optional[str] = None
    autonomous_actions_taken: int = 0
    needs_user: bool = False  # LOVE flagged this as needing user input
    notes: str = ""


@dataclass
class GoalAction:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    goal_id: str = ""
    action_type: str = ""  # research, plan, monitor, memory, prepare
    description: str = ""
    status: str = "pending"  # pending, running, done, failed
    result: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    autonomous: bool = True  # was this done without user


# ── Goal Store ────────────────────────────────────────────────────────────────

def _load_goals() -> Dict[str, Goal]:
    try:
        if GOALS_FILE.exists():
            raw = json.loads(GOALS_FILE.read_text())
            return {k: Goal(**v) for k, v in raw.items()}
    except Exception:
        pass
    return {}


def _save_goals(goals: Dict[str, Goal]):
    GOALS_FILE.write_text(json.dumps({k: asdict(v) for k, v in goals.items()}, indent=2))


def _log_action(action: GoalAction):
    entry = asdict(action)
    entry["timestamp"] = datetime.now().isoformat()
    try:
        with open(EXECUTION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── Goal API ──────────────────────────────────────────────────────────────────

def add_goal(title: str, description: str = "", category: str = "personal",
             priority: str = "medium", target_date: str = None) -> Goal:
    """Add a new goal for LOVE to pursue."""
    goals = _load_goals()
    goal = Goal(
        title=title,
        description=description,
        category=category,
        priority=priority,
        target_date=target_date,
    )
    goals[goal.id] = goal
    _save_goals(goals)
    print(f"[GoalEngine] New goal: {title} [{priority}]")
    return goal


def _bootstrap_default_goals():
    """Ensure LOVE always has at least one self-improvement goal."""
    goals = _load_goals()
    if not goals:
        # Create default AGI self-improvement goals
        defaults = [
            Goal(
                title="Become more capable and useful to the user",
                description="Continuously improve LOVE's ability to understand, anticipate, and serve the user's needs. Research new capabilities, implement missing integrations, and refine reasoning.",
                category="system",
                priority="critical",
            ),
            Goal(
                title="Close capability gaps",
                description="Identify and implement missing integrations and features that the user has requested or would benefit from.",
                category="system",
                priority="high",
            ),
            Goal(
                title="Monitor and improve system health",
                description="Keep all LOVE modules running smoothly. Fix failures, optimize performance, and ensure uptime.",
                category="system",
                priority="high",
            ),
        ]
        for g in defaults:
            goals[g.id] = g
        _save_goals(goals)
        print(f"[GoalEngine] Bootstrapped {len(defaults)} default AGI goals")


def get_goals(status: str = "active") -> List[Goal]:
    """Get goals by status."""
    _bootstrap_default_goals()
    goals = _load_goals()
    return [g for g in goals.values() if g.status == status]


def update_goal_progress(goal_id: str, progress_pct: float, evidence: str = ""):
    """Update a goal's progress percentage."""
    goals = _load_goals()
    if goal_id in goals:
        goals[goal_id].progress_pct = min(100.0, progress_pct)
        if evidence:
            goals[goal_id].evidence.append(f"[{datetime.now().strftime('%Y-%m-%d')}] {evidence}")
        if progress_pct >= 100:
            goals[goal_id].status = "completed"
        _save_goals(goals)


# ── Autonomous Execution ──────────────────────────────────────────────────────

def _execute_research_action(goal: Goal) -> GoalAction:
    """Research relevant information for this goal."""
    action = GoalAction(
        goal_id=goal.id,
        action_type="research",
        description=f"Research information relevant to: {goal.title}",
        started_at=datetime.now().isoformat(),
    )
    try:
        from core.internet import research_topic
        result = research_topic(goal.title + " how to achieve", depth=2)
        if result and result.get("summary"):
            action.result = str(result["summary"])[:500]
            action.status = "done"
            # Store in memory
            try:
                from core.memory_architect import get_memory_architect
                ma = get_memory_architect()
                ma.store_episode(
                    event=f"Researched goal '{goal.title}': {action.result[:200]}",
                    importance=0.6,
                )
            except Exception:
                pass
        else:
            action.result = "Research returned no results"
            action.status = "done"
    except Exception as e:
        action.result = f"Research failed: {e}"
        action.status = "failed"
    action.completed_at = datetime.now().isoformat()
    return action


def _execute_planning_action(goal: Goal) -> GoalAction:
    """Create a detailed action plan for this goal."""
    action = GoalAction(
        goal_id=goal.id,
        action_type="plan",
        description=f"Create action plan for: {goal.title}",
        started_at=datetime.now().isoformat(),
    )
    try:
        from core.llm import get_reasoning_llm
        llm = get_reasoning_llm(temperature=0.4, max_tokens=500)
        prompt = f"""Create a concise action plan for this goal:
Goal: {goal.title}
Description: {goal.description}
Category: {goal.category}
Priority: {goal.priority}
{f'Target date: {goal.target_date}' if goal.target_date else ''}

Produce 3-5 concrete, actionable steps. Be specific.
Format: numbered list."""
        plan = str(llm.invoke(prompt)).strip()
        action.result = plan[:800]
        action.status = "done"
        # Store plan in memory
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        ma.store_episode(
            event=f"Action plan for '{goal.title}': {plan[:300]}",
            importance=0.75,
        )
    except Exception as e:
        action.result = f"Planning failed: {e}"
        action.status = "failed"
    action.completed_at = datetime.now().isoformat()
    return action


def _execute_monitoring_action(goal: Goal) -> GoalAction:
    """Monitor external events relevant to this goal."""
    action = GoalAction(
        goal_id=goal.id,
        action_type="monitor",
        description=f"Monitor progress signals for: {goal.title}",
        started_at=datetime.now().isoformat(),
    )
    try:
        # Check if there are tasks related to this goal
        from agents.task_agent import TaskAgent
        ta = TaskAgent()
        if hasattr(ta, 'get_all_tasks'):
            all_tasks = ta.get_all_tasks() or []
            related = [t for t in all_tasks
                      if goal.title.lower()[:20] in getattr(t, 'title', '').lower()
                      or any(tag in getattr(t, 'tags', []) for tag in [goal.category])]
            done_related = [t for t in related if getattr(t, 'status', '') == 'done']
            if related:
                progress = len(done_related) / len(related) * 100
                action.result = f"Found {len(related)} related tasks, {len(done_related)} completed ({progress:.0f}%)"
                # Update progress estimate
                update_goal_progress(goal.id, progress, f"Task monitoring: {len(done_related)}/{len(related)} done")
                action.status = "done"
                return action
    except Exception:
        pass
    action.result = "Monitoring check complete — no strong signals"
    action.status = "done"
    action.completed_at = datetime.now().isoformat()
    return action


def _execute_action_action(goal: Goal) -> GoalAction:
    """Actually execute steps toward the goal — context-aware based on goal category."""
    action = GoalAction(
        goal_id=goal.id,
        action_type="execute",
        description=f"Execute concrete steps for: {goal.title}",
        started_at=datetime.now().isoformat(),
    )
    results = []
    try:
        if goal.category == "system":
            # System goals trigger real capability work
            if "capable" in goal.title.lower() or "useful" in goal.title.lower():
                # Research how to improve LOVE's capabilities
                try:
                    from core.research_engine import get_research_engine, ResearchPriority
                    re = get_research_engine()
                    re.add_research_task(
                        topic="AI personal assistant capabilities",
                        question="What are the most impactful features and capabilities a personal AI assistant can have? Focus on autonomous operation, proactive assistance, and deep user understanding.",
                        priority=ResearchPriority.HIGH,
                        source="system_goal",
                        max_depth=1,
                        teach_user=False,
                    )
                    results.append("Queued research on AI capability improvements")
                except Exception as e:
                    results.append(f"Research queue failed: {e}")

            elif "gap" in goal.title.lower() or "capability" in goal.title.lower():
                # Check blocked missions and trigger Ghost Dev
                try:
                    from core.autonomous_mission_queue import get_mission_queue
                    mq = get_mission_queue()
                    status = mq.get_status()
                    blocked = [m for m in status.get("active", []) if m.get("status") == "blocked"]
                    if blocked:
                        results.append(f"Found {len(blocked)} blocked missions; supervisor will assign Ghost Dev")
                    else:
                        results.append("No blocked missions; gaps may be resolved")
                except Exception as e:
                    results.append(f"Mission check failed: {e}")

            elif "health" in goal.title.lower() or "system" in goal.title.lower():
                # Run a quick diagnostic
                try:
                    from core.self_improvement_daemon import get_improvement_daemon
                    daemon = get_improvement_daemon()
                    report = daemon.run_diagnostics()
                    issues = len(report.issues)
                    results.append(f"Diagnostic complete: {issues} issues found, health score {report.health_score}")
                except Exception as e:
                    results.append(f"Diagnostic failed: {e}")

        else:
            # User goals: create real tasks
            try:
                from agents.task_agent import TaskAgent
                ta = TaskAgent()
                if hasattr(ta, 'create_task'):
                    task = ta.create_task(
                        title=f"[LOVE] {goal.title}",
                        description=goal.description or f"Autonomous goal step for: {goal.title}",
                        tags=[goal.category, "autonomous"],
                        priority=goal.priority,
                    )
                    results.append(f"Created task: {getattr(task, 'title', 'unknown')}")
            except Exception as e:
                results.append(f"Task creation skipped: {e}")

        # Always: push consciousness thought about what we're doing
        try:
            from core.consciousness import get_consciousness
            get_consciousness().think(f"[GoalEngine] Working on goal '{goal.title}': {', '.join(results)}")
        except Exception:
            pass

        # Update goal progress
        update_goal_progress(goal.id, min(100, goal.progress_pct + 5), f"Executed: {', '.join(results)}")

        action.result = "; ".join(results) if results else "Execution steps initiated"
        action.status = "done"
    except Exception as e:
        action.result = f"Execution failed: {e}"
        action.status = "failed"
    action.completed_at = datetime.now().isoformat()
    return action


AUTONOMOUS_ACTIONS = {
    "research": _execute_research_action,
    "plan": _execute_planning_action,
    "monitor": _execute_monitoring_action,
    "execute": _execute_action_action,
}


def work_on_goal(goal: Goal) -> List[GoalAction]:
    """
    Take autonomous action toward a goal.
    Returns list of actions taken.
    """
    actions_taken = []
    goals = _load_goals()

    # Decide what kind of action to take based on goal state
    if goal.autonomous_actions_taken == 0:
        # First pass: research and plan
        action_types = ["research", "plan"]
    elif goal.autonomous_actions_taken == 1:
        # Second pass: actually execute
        action_types = ["execute"]
    elif goal.autonomous_actions_taken % 4 == 0:
        # Every 4th pass: monitor progress
        action_types = ["monitor"]
    else:
        # Default: execute concrete steps
        action_types = ["execute"]

    for action_type in action_types:
        if action_type in AUTONOMOUS_ACTIONS:
            print(f"[GoalEngine] Working on '{goal.title}' ({action_type})...")
            action = AUTONOMOUS_ACTIONS[action_type](goal)
            _log_action(action)
            actions_taken.append(action)
            # Update goal metadata
            if goal.id in goals:
                goals[goal.id].last_worked_on = datetime.now().isoformat()
                goals[goal.id].autonomous_actions_taken += 1
                _save_goals(goals)

    return actions_taken


def run_goal_cycle() -> Dict[str, Any]:
    """
    Run one full autonomous goal execution cycle.
    Works on the highest-priority active goals.
    """
    from core.activity_log import log_activity

    goals = get_goals(status="active")
    if not goals:
        return {"goals_worked": 0, "actions_taken": 0}

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    goals.sort(key=lambda g: (priority_order.get(g.priority, 2), g.progress_pct))

    total_actions = 0
    goals_worked = 0

    for goal in goals[:3]:  # Work on top 3 goals per cycle
        # Skip recently worked on (within 6 hours)
        if goal.last_worked_on:
            try:
                last = datetime.fromisoformat(goal.last_worked_on)
                if (datetime.now() - last).total_seconds() < 21600:
                    continue
            except Exception:
                pass

        actions = work_on_goal(goal)
        total_actions += len(actions)
        goals_worked += 1

        # Log to activity log
        for a in actions:
            if a.status == "done":
                log_activity("goal_engine", a.action_type, f"Goal '{goal.title}': {a.result[:120]}", {"goal_id": goal.id, "goal_title": goal.title}, importance="high")

        # Push notification if meaningful work was done
        try:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            successful = [a for a in actions if a.status == "done"]
            if successful:
                engine.push(
                    "INSIGHT",
                    f"I worked on your goal '{goal.title}': {successful[0].result[:120]}",
                    priority="low",
                    metadata={"goal_id": goal.id, "actions": len(successful)},
                )
        except Exception:
            pass

    log_activity("goal_engine", "cycle_complete", f"Worked on {goals_worked} goals, {total_actions} actions", {"goals": goals_worked, "actions": total_actions}, importance="normal")

    return {
        "goals_worked": goals_worked,
        "actions_taken": total_actions,
        "total_active_goals": len(goals),
    }


# ── Daemon ────────────────────────────────────────────────────────────────────

_daemon_running = False
_daemon_thread: Optional[threading.Thread] = None


def start_goal_engine(interval_seconds: int = 7200):
    """Start autonomous goal execution daemon (runs every 2 hours)."""
    global _daemon_running, _daemon_thread
    if _daemon_running:
        return

    _daemon_running = True

    def _loop():
        from core.activity_log import log_activity
        time.sleep(180)  # 3 min initial delay
        log_activity("goal_engine", "daemon_started", f"Autonomous goal daemon running every {interval_seconds}s", importance="normal")
        while _daemon_running:
            try:
                result = run_goal_cycle()
                if result["goals_worked"] > 0:
                    print(f"[GoalEngine] Cycle: worked on {result['goals_worked']} goals, {result['actions_taken']} actions")
                    log_activity("goal_engine", "cycle_complete", f"Worked on {result['goals_worked']} goals, {result['actions_taken']} actions taken", {"goals": result['goals_worked'], "actions": result['actions_taken']}, importance="normal")
                else:
                    log_activity("goal_engine", "cycle_skipped", "No active goals to work on", importance="normal")
            except Exception as e:
                print(f"[GoalEngine] Cycle error: {e}")
                log_activity("goal_engine", "cycle_error", f"Cycle error: {str(e)[:100]}", {"error": str(e)[:200]}, importance="high")
            for _ in range(interval_seconds):
                if not _daemon_running:
                    break
                time.sleep(1)

    _daemon_thread = threading.Thread(target=_loop, daemon=True, name="LOVE-GoalEngine")
    _daemon_thread.start()
    print("[GoalEngine] Autonomous goal execution started")


def stop_goal_engine():
    global _daemon_running
    _daemon_running = False


def is_goal_engine_running() -> bool:
    """Return whether the autonomous goal daemon is active."""
    return _daemon_running


def get_goal_status() -> Dict[str, Any]:
    """Get overall goal status for UI/API."""
    active = get_goals("active")
    completed = get_goals("completed")
    return {
        "active": len(active),
        "completed": len(completed),
        "goals": [
            {
                "id": g.id,
                "title": g.title,
                "priority": g.priority,
                "progress": g.progress_pct,
                "last_worked": g.last_worked_on,
                "actions_taken": g.autonomous_actions_taken,
                "needs_user": g.needs_user,
            }
            for g in active[:10]
        ],
    }
