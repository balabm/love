"""
LOVE Recursive Goal Decomposition Engine

This is the "thinking about thinking about goals" engine.
Unlike the existing AutonomousAgent which does flat planning,
this engine does RECURSIVE decomposition:

  "Get healthy" →
    "Improve fitness" →
      "Create workout plan" →
        "Research exercises for back pain"
        "Schedule 3 gym sessions per week"
      "Track nutrition" →
        "Log meals for 1 week"
        "Identify caloric targets"
    "Improve sleep" →
      "Set consistent bedtime"
      "Reduce screen time after 10pm"

Each sub-goal inherits priority, deadline pressure, and progress tracking
from its parent. When a leaf-goal completes, progress propagates upward.

This is what AGI does that chatbots can't — decompose vague human desires
into executable atomic actions, recursively.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from pathlib import Path

from core.llm import get_reasoning_llm
from core.consciousness import get_consciousness
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
GOALS_FILE = DATA_DIR / "recursive_goals.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class GoalState(Enum):
    SEED = "seed"              # Just an idea, not decomposed yet
    DECOMPOSED = "decomposed"  # Broken into sub-goals
    ACTIVE = "active"          # Leaf goal, being worked on
    BLOCKED = "blocked"        # Waiting on something
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class RecursiveGoal:
    """A goal in the recursive hierarchy."""
    id: str
    title: str
    description: str
    state: GoalState = GoalState.SEED
    priority: float = 0.5                    # 0 (low) to 1 (critical)
    progress: float = 0.0                    # 0 to 1
    parent_id: Optional[str] = None          # None = root goal
    children_ids: List[str] = field(default_factory=list)
    depth: int = 0                           # 0 = root
    max_depth: int = 4                       # Prevent infinite recursion
    deadline: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    reasoning: str = ""                      # Why this goal exists
    success_criteria: str = ""               # How to know it's done
    blockers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class RecursiveGoalEngine:
    """
    Breaks high-level goals into executable sub-goals, recursively.
    Tracks progress, propagates completion, and re-plans when blocked.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.goals: Dict[str, RecursiveGoal] = {}
        self._load()

    # ── Goal Creation & Decomposition ────────────────────────────────────────

    def set_goal(self, title: str, description: str, priority: float = 0.5,
                 deadline: str = None, parent_id: str = None) -> str:
        """Create a new root or sub-goal."""
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        depth = 0
        if parent_id and parent_id in self.goals:
            depth = self.goals[parent_id].depth + 1
            self.goals[parent_id].children_ids.append(goal_id)

        goal = RecursiveGoal(
            id=goal_id,
            title=title,
            description=description,
            priority=priority,
            parent_id=parent_id,
            depth=depth,
            deadline=deadline,
        )
        self.goals[goal_id] = goal
        self._save()
        return goal_id

    def decompose(self, goal_id: str) -> List[str]:
        """
        Use LLM to decompose a goal into sub-goals.
        This is the recursive heart of the engine.
        """
        if goal_id not in self.goals:
            return []

        goal = self.goals[goal_id]

        if goal.depth >= goal.max_depth:
            # Reached max depth — this is a leaf/action node
            goal.state = GoalState.ACTIVE
            self._save()
            return []

        if goal.children_ids:
            # Already decomposed
            return goal.children_ids

        # Use LLM to break the goal into 2-5 sub-goals
        llm = get_reasoning_llm(temperature=0.4)

        # Build ancestry chain for context
        ancestry = self._get_ancestry(goal_id)
        ancestry_text = " → ".join(a.title for a in ancestry) if ancestry else "Root"

        prompt = f"""You are LOVE, an AGI system. Break this goal into 2-5 specific sub-goals.

GOAL HIERARCHY: {ancestry_text} → {goal.title}
GOAL: {goal.title}
DESCRIPTION: {goal.description}
DEPTH: {goal.depth}/{goal.max_depth} (deeper = more specific/actionable)
DEADLINE: {goal.deadline or "None"}

Rules:
- At depth 0-1: Sub-goals should be strategic themes
- At depth 2: Sub-goals should be specific projects
- At depth 3+: Sub-goals should be concrete actions (can be done in 1 session)
- Each sub-goal MUST be more specific than the parent
- Include success criteria for each

Return JSON array:
[
  {{
    "title": "Short actionable title",
    "description": "What specifically needs to happen",
    "success_criteria": "How to know this is done",
    "priority": 0.7,
    "reasoning": "Why this sub-goal is needed"
  }}
]"""

        try:
            response = str(llm.invoke(prompt))
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                sub_goals_data = json.loads(json_match.group())
                child_ids = []
                for sg in sub_goals_data[:5]:  # Max 5 sub-goals
                    child_id = self.set_goal(
                        title=sg.get("title", "Untitled"),
                        description=sg.get("description", ""),
                        priority=sg.get("priority", goal.priority),
                        deadline=goal.deadline,
                        parent_id=goal_id,
                    )
                    child = self.goals[child_id]
                    child.success_criteria = sg.get("success_criteria", "")
                    child.reasoning = sg.get("reasoning", "")
                    child_ids.append(child_id)

                goal.state = GoalState.DECOMPOSED
                self._save()

                # Log to consciousness
                try:
                    consciousness = get_consciousness()
                    consciousness.think(
                        f"Decomposed '{goal.title}' into {len(child_ids)} sub-goals at depth {goal.depth + 1}"
                    )
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.recursive_goals")

                return child_ids
        except Exception as e:
            print(f"[RecursiveGoals] Decomposition error: {e}")

        return []

    def decompose_fully(self, goal_id: str) -> Dict[str, Any]:
        """
        Recursively decompose a goal ALL the way down to leaf actions.
        Returns a tree structure.
        """
        if goal_id not in self.goals:
            return {}

        goal = self.goals[goal_id]

        # Decompose this level
        children = self.decompose(goal_id)

        # Recursively decompose children
        child_trees = []
        for child_id in children:
            child_tree = self.decompose_fully(child_id)
            child_trees.append(child_tree)

        return {
            "id": goal.id,
            "title": goal.title,
            "depth": goal.depth,
            "state": goal.state.value,
            "progress": goal.progress,
            "children": child_trees,
        }

    # ── Progress Tracking ────────────────────────────────────────────────────

    def complete_goal(self, goal_id: str) -> float:
        """
        Mark a goal as complete and propagate progress upward.
        Returns the new progress of the root ancestor.
        """
        if goal_id not in self.goals:
            return 0.0

        goal = self.goals[goal_id]
        goal.state = GoalState.COMPLETED
        goal.progress = 1.0
        goal.completed_at = datetime.now().isoformat()

        # Propagate upward
        if goal.parent_id:
            self._propagate_progress(goal.parent_id)

        self._save()

        # Log milestone
        try:
            consciousness = get_consciousness()
            consciousness.think(f"Completed goal: '{goal.title}' 🎯")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.recursive_goals")

        # Return root progress
        root = self._get_root(goal_id)
        return root.progress if root else 1.0

    def _propagate_progress(self, goal_id: str):
        """Propagate progress from children to parent."""
        if goal_id not in self.goals:
            return

        goal = self.goals[goal_id]
        if not goal.children_ids:
            return

        # Calculate progress as average of children
        children_progress = []
        for cid in goal.children_ids:
            if cid in self.goals:
                children_progress.append(self.goals[cid].progress)

        if children_progress:
            goal.progress = sum(children_progress) / len(children_progress)

            # If all children complete, mark parent complete
            if all(p >= 1.0 for p in children_progress):
                goal.state = GoalState.COMPLETED
                goal.completed_at = datetime.now().isoformat()

        # Continue propagation upward
        if goal.parent_id:
            self._propagate_progress(goal.parent_id)

    # ── Tree Queries ─────────────────────────────────────────────────────────

    def get_next_actions(self) -> List[RecursiveGoal]:
        """Get all leaf goals that are actionable right now."""
        actions = []
        for goal in self.goals.values():
            if (goal.state == GoalState.ACTIVE and
                    not goal.children_ids and
                    goal.progress < 1.0):
                actions.append(goal)

        # Sort by priority (highest first), then by deadline
        actions.sort(key=lambda g: (-g.priority, g.deadline or "9999"))
        return actions

    def get_goal_tree(self, root_id: str = None) -> Dict[str, Any]:
        """Get the full goal tree as a nested dict."""
        if root_id:
            return self._tree_node(root_id)

        # Return all root goals
        roots = [g for g in self.goals.values() if g.parent_id is None]
        return {
            "roots": [self._tree_node(r.id) for r in roots]
        }

    def _tree_node(self, goal_id: str) -> Dict[str, Any]:
        if goal_id not in self.goals:
            return {}
        g = self.goals[goal_id]
        return {
            "id": g.id,
            "title": g.title,
            "state": g.state.value,
            "progress": round(g.progress, 2),
            "priority": g.priority,
            "depth": g.depth,
            "success_criteria": g.success_criteria,
            "children": [self._tree_node(cid) for cid in g.children_ids],
        }

    def _get_ancestry(self, goal_id: str) -> List[RecursiveGoal]:
        """Get the chain of ancestors from root to this goal."""
        chain = []
        current_id = self.goals[goal_id].parent_id
        while current_id and current_id in self.goals:
            chain.insert(0, self.goals[current_id])
            current_id = self.goals[current_id].parent_id
        return chain

    def _get_root(self, goal_id: str) -> Optional[RecursiveGoal]:
        """Get the root ancestor of a goal."""
        current = self.goals.get(goal_id)
        while current and current.parent_id:
            current = self.goals.get(current.parent_id)
        return current

    def get_prompt_context(self) -> str:
        """Get goal context for LLM prompt injection."""
        actions = self.get_next_actions()
        if not actions:
            return ""

        roots = [g for g in self.goals.values() if g.parent_id is None and g.state != GoalState.COMPLETED]
        
        parts = []
        if roots:
            parts.append("ACTIVE LIFE GOALS:")
            for r in roots[:3]:
                parts.append(f"  • {r.title} ({r.progress:.0%} complete)")
        
        if actions:
            parts.append("NEXT ACTIONS:")
            for a in actions[:5]:
                ancestry = self._get_ancestry(a.id)
                path = " → ".join(x.title for x in ancestry) + f" → {a.title}" if ancestry else a.title
                parts.append(f"  → {path}")
        
        return "\n".join(parts)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self):
        try:
            if GOALS_FILE.exists():
                with open(GOALS_FILE, 'r') as f:
                    data = json.load(f)
                for gid, gdata in data.get("goals", {}).items():
                    self.goals[gid] = RecursiveGoal(
                        id=gid,
                        title=gdata["title"],
                        description=gdata.get("description", ""),
                        state=GoalState(gdata.get("state", "seed")),
                        priority=gdata.get("priority", 0.5),
                        progress=gdata.get("progress", 0.0),
                        parent_id=gdata.get("parent_id"),
                        children_ids=gdata.get("children_ids", []),
                        depth=gdata.get("depth", 0),
                        max_depth=gdata.get("max_depth", 4),
                        deadline=gdata.get("deadline"),
                        created_at=gdata.get("created_at", ""),
                        completed_at=gdata.get("completed_at"),
                        reasoning=gdata.get("reasoning", ""),
                        success_criteria=gdata.get("success_criteria", ""),
                        blockers=gdata.get("blockers", []),
                        tags=gdata.get("tags", []),
                    )
        except Exception as e:
            print(f"[RecursiveGoals] Load error: {e}")

    def _save(self):
        with self._lock:
            try:
                with open(GOALS_FILE, 'w') as f:
                    json.dump({
                        "goals": {
                            gid: {
                                "title": g.title, "description": g.description,
                                "state": g.state.value, "priority": g.priority,
                                "progress": g.progress, "parent_id": g.parent_id,
                                "children_ids": g.children_ids, "depth": g.depth,
                                "max_depth": g.max_depth, "deadline": g.deadline,
                                "created_at": g.created_at, "completed_at": g.completed_at,
                                "reasoning": g.reasoning, "success_criteria": g.success_criteria,
                                "blockers": g.blockers, "tags": g.tags,
                            }
                            for gid, g in self.goals.items()
                        }
                    }, f, indent=2)
            except Exception as e:
                print(f"[RecursiveGoals] Save error: {e}")


# Singleton
_engine: Optional[RecursiveGoalEngine] = None
_lock = threading.Lock()

def get_recursive_goals() -> RecursiveGoalEngine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = RecursiveGoalEngine()
    return _engine
