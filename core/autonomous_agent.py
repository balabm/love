"""
Autonomous Agent System for LOVE
Enables LOVE to set goals, plan multi-step strategies, and execute autonomously.
This is a critical component for AGI-level intelligence.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import threading

from core.settings import get_settings
from core.context_engine import get_live_context
from core.heartbeat import ProactiveHeartbeat
from core.tool_registry import get_tool_registry

SETTINGS = get_settings()


class GoalPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class GoalStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(Enum):
    """Types of autonomous actions LOVE can take"""
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    COMMUNICATE = "communicate"
    REMIND = "remind"
    RESEARCH = "research"
    ORGANIZE = "organize"
    OPTIMIZE = "optimize"
    LEARN = "learn"


@dataclass
class Action:
    """A single step in a plan"""
    id: str
    type: ActionType
    description: str
    tool: Optional[str] = None  # Which tool/function to use
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # IDs of actions this depends on
    status: GoalStatus = GoalStatus.PENDING
    result: Optional[Any] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Goal:
    """A high-level goal LOVE wants to achieve"""
    id: str
    title: str
    description: str
    priority: GoalPriority
    status: GoalStatus = GoalStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    deadline: Optional[str] = None
    plan: List[Action] = field(default_factory=list)
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""  # Why LOVE set this goal


class AutonomousAgent:
    """
    Autonomous agent that can set goals, plan strategies, and execute actions.
    This is the core of AGI-level autonomy.
    """
    
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.active_plan: Optional[str] = None  # ID of currently executing plan
        self.lock = threading.Lock()
        self._load_goals()
        from core.heartbeat import get_heartbeat
        self.heartbeat = get_heartbeat()
    
    def _load_goals(self):
        """Load goals from persistent storage"""
        try:
            import os
            goals_file = SETTINGS.data_dir / "autonomous_goals.json"
            if goals_file.exists():
                with open(goals_file, 'r') as f:
                    data = json.load(f)
                    for goal_id, goal_data in data.items():
                        # Reconstruct Goal objects
                        actions = [Action(**a) for a in goal_data.get('plan', [])]
                        self.goals[goal_id] = Goal(
                            id=goal_id,
                            title=goal_data['title'],
                            description=goal_data['description'],
                            priority=GoalPriority(goal_data['priority']),
                            status=GoalStatus(goal_data['status']),
                            created_at=goal_data['created_at'],
                            deadline=goal_data.get('deadline'),
                            plan=actions,
                            progress=goal_data.get('progress', 0.0),
                            metadata=goal_data.get('metadata', {}),
                            reasoning=goal_data.get('reasoning', '')
                        )
        except Exception as e:
            print(f"[AutonomousAgent] Error loading goals: {e}")
    
    def _save_goals(self):
        """Save goals to persistent storage"""
        try:
            import os
            goals_file = SETTINGS.data_dir / "autonomous_goals.json"
            with self.lock:
                data = {}
                for goal_id, goal in self.goals.items():
                    data[goal_id] = {
                        'id': goal.id,
                        'title': goal.title,
                        'description': goal.description,
                        'priority': goal.priority.value,
                        'status': goal.status.value,
                        'created_at': goal.created_at,
                        'deadline': goal.deadline,
                        'plan': [
                            {
                                'id': a.id,
                                'type': a.type.value,
                                'description': a.description,
                                'tool': a.tool,
                                'parameters': a.parameters,
                                'dependencies': a.dependencies,
                                'status': a.status.value,
                                'result': a.result,
                                'timestamp': a.timestamp
                            }
                            for a in goal.plan
                        ],
                        'progress': goal.progress,
                        'metadata': goal.metadata,
                        'reasoning': goal.reasoning
                    }
                with open(goals_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AutonomousAgent] Error saving goals: {e}")
    
    def set_goal(self, title: str, description: str, priority: GoalPriority = GoalPriority.MEDIUM,
                 reasoning: str = "", deadline: Optional[str] = None) -> str:
        """
        Set a new autonomous goal.
        LOVE uses this to self-initiate goals based on context.
        """
        goal_id = f"goal_{datetime.utcnow().timestamp()}"
        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            priority=priority,
            reasoning=reasoning,
            deadline=deadline
        )
        
        with self.lock:
            self.goals[goal_id] = goal
            self._save_goals()
        
        print(f"[AutonomousAgent] New goal set: {title} ({priority.name})")
        print(f"[AutonomousAgent] Reasoning: {reasoning}")
        
        return goal_id
    
    def plan_goal(self, goal_id: str) -> bool:
        """
        Use LLM to generate a multi-step plan for achieving a goal.
        This is where LOVE demonstrates planning intelligence.
        """
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.PLANNING
        
        try:
            # Get current context for planning
            ctx = get_live_context()
            
            # Retrieve dynamic tool schema for AGI-level function calling
            tool_registry = get_tool_registry()
            available_tools_schema = tool_registry.get_tool_schema()
            
            # Build planning prompt
            planning_prompt = f"""You are LOVE, an autonomous AI assistant helping Karthi.

CURRENT CONTEXT:
- Time: {datetime.utcnow().isoformat()}
- Active Project: {ctx.active_project or 'None'}
- Tasks Due Today: {ctx.tasks_due_today}
- Next Event: {ctx.next_event.get('title', 'None') if ctx.next_event else 'None'}
- Stress Level: {ctx.stress_level}
- Energy Level: {ctx.energy_level}
- Time of Day: {ctx.time_of_day}

AVAILABLE TOOLS FOR EXECUTION:
{available_tools_schema}

GOAL TO ACHIEVE:
Title: {goal.title}
Description: {goal.description}
Reasoning: {goal.reasoning}

Generate a detailed multi-step plan to achieve this goal. Each step should be:
- Specific and actionable
- Dependent on previous steps where needed
- Use available tools exactly as defined in the schema. In the "tool" field, use the exact name of the tool, and in "parameters", provide the required arguments.

Return a JSON plan with this structure:
{{
  "actions": [
    {{
      "type": "analyze|plan|execute|communicate|remind|research|organize|optimize|learn",
      "description": "What to do",
      "tool": "which_function_to_use",
      "parameters": {{}},
      "dependencies": ["action_id_1", "action_id_2"]
    }}
  ]
}}"""
            
            # Use reasoning LLM for planning
            from core.agent import chat
            response = chat(planning_prompt, mode="reasoning")
            
            # Parse plan from response
            plan_text = response.get("response", "")
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', plan_text)
            if json_match:
                plan_data = json.loads(json_match.group())
                actions = []
                for idx, action_data in enumerate(plan_data.get("actions", [])):
                    action = Action(
                        id=f"{goal_id}_action_{idx}",
                        type=ActionType(action_data.get("type", "execute")),
                        description=action_data.get("description", ""),
                        tool=action_data.get("tool"),
                        parameters=action_data.get("parameters", {}),
                        dependencies=action_data.get("dependencies", [])
                    )
                    actions.append(action)
                
                goal.plan = actions
                goal.status = GoalStatus.PENDING
                with self.lock:
                    self._save_goals()
                
                print(f"[AutonomousAgent] Plan generated for {goal.title}: {len(actions)} actions")
                return True
            
            return False
            
        except Exception as e:
            print(f"[AutonomousAgent] Planning error: {e}")
            goal.status = GoalStatus.PENDING
            return False
    
    def execute_goal(self, goal_id: str) -> bool:
        """
        Execute a goal's plan step by step.
        This is where LOVE demonstrates autonomous execution.
        """
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        if not goal.plan:
            if not self.plan_goal(goal_id):
                return False
        
        goal.status = GoalStatus.IN_PROGRESS
        self.active_plan = goal_id
        
        try:
            # Execute actions in dependency order
            executed_actions = set()
            
            while len(executed_actions) < len(goal.plan):
                progress_made = False
                
                for action in goal.plan:
                    if action.id in executed_actions:
                        continue
                    
                    # Check if dependencies are met
                    deps_met = all(dep in executed_actions for dep in action.dependencies)
                    if not deps_met:
                        continue
                    
                    # Execute action
                    print(f"[AutonomousAgent] Executing: {action.description}")
                    result = self._execute_action(action)
                    
                    action.result = result
                    action.status = GoalStatus.COMPLETED if result else GoalStatus.FAILED
                    executed_actions.add(action.id)
                    progress_made = True
                    
                    # Update progress
                    goal.progress = len(executed_actions) / len(goal.plan)
                    with self.lock:
                        self._save_goals()
                    
                    # Small delay between actions
                    asyncio.sleep(0.5)
                
                if not progress_made:
                    print(f"[AutonomousAgent] Blocked: circular dependencies or all actions failed")
                    goal.status = GoalStatus.BLOCKED
                    break
            
            if len(executed_actions) == len(goal.plan):
                goal.status = GoalStatus.COMPLETED
                goal.progress = 1.0
                print(f"[AutonomousAgent] Goal completed: {goal.title}")
            else:
                goal.status = GoalStatus.FAILED
            
            with self.lock:
                self._save_goals()
            
            self.active_plan = None
            return goal.status == GoalStatus.COMPLETED
            
        except Exception as e:
            print(f"[AutonomousAgent] Execution error: {e}")
            goal.status = GoalStatus.FAILED
            with self.lock:
                self._save_goals()
            self.active_plan = None
            return False
    
    def _execute_action(self, action: Action) -> Any:
        """Execute a single action using appropriate tools"""
        try:
            # 1. Check if there is a specific dynamic tool defined
            if action.tool:
                registry = get_tool_registry()
                if action.tool in registry.tools:
                    print(f"[AutonomousAgent] Executing Dynamic Tool: {action.tool} with {action.parameters}")
                    return registry.execute_tool(action.tool, action.parameters)

            # 2. Map action types to legacy implementations
            if action.type == ActionType.ANALYZE:
                return self._action_analyze(action)
            elif action.type == ActionType.PLAN:
                return self._action_plan(action)
            elif action.type == ActionType.COMMUNICATE:
                return self._action_communicate(action)
            elif action.type == ActionType.REMIND:
                return self._action_remind(action)
            elif action.type == ActionType.RESEARCH:
                return self._action_research(action)
            elif action.type == ActionType.ORGANIZE:
                return self._action_organize(action)
            elif action.type == ActionType.OPTIMIZE:
                return self._action_optimize(action)
            elif action.type == ActionType.LEARN:
                return self._action_learn(action)
            else:
                print(f"[AutonomousAgent] Unknown action type: {action.type}")
                return None
        except Exception as e:
            print(f"[AutonomousAgent] Action execution error: {e}")
            return None
    
    def _action_analyze(self, action: Action) -> Any:
        """Analyze data or situation"""
        # Placeholder - integrate with context engine
        ctx = get_live_context()
        return {"context": str(ctx)}
    
    def _action_plan(self, action: Action) -> Any:
        """Create a plan"""
        # Placeholder - use LLM for planning
        return True
    
    def _action_communicate(self, action: Action) -> Any:
        """Send a message or notification"""
        # Placeholder - integrate with notification system
        message = action.parameters.get("message", action.description)
        print(f"[AutonomousAgent] Communication: {message}")
        return True
    
    def _action_remind(self, action: Action) -> Any:
        """Set a reminder"""
        # Placeholder - integrate with calendar/tasks
        return True
    
    def _action_research(self, action: Action) -> Any:
        """Research information"""
        # Placeholder - integrate with search
        return True
    
    def _action_organize(self, action: Action) -> Any:
        """Organize data or tasks"""
        # Placeholder - integrate with task agent
        return True
    
    def _action_optimize(self, action: Action) -> Any:
        """Optimize something"""
        # Placeholder - integrate with various systems
        return True
    
    def _action_learn(self, action: Action) -> Any:
        """Learn from experience"""
        # Placeholder - integrate with memory/learning
        return True
    
    def generate_autonomous_goals(self) -> List[str]:
        """
        Analyze current context and generate autonomous goals using LLM reasoning.
        This is where LOVE demonstrates proactive intelligence.
        """
        goals_created = []
        
        try:
            ctx = get_live_context()
            
            # Use LLM to analyze context and suggest goals
            goal_generation_prompt = f"""You are LOVE, an autonomous AI assistant helping Karthi.

CURRENT CONTEXT:
- Time: {datetime.utcnow().isoformat()}
- Active Project: {ctx.active_project or 'None'}
- Tasks Due Today: {ctx.tasks_due_today}
- Next Event: {ctx.next_event.get('title', 'None') if ctx.next_event else 'None'} ({ctx.next_event.get('minutes_away', 'N/A') if ctx.next_event else 'N/A'} minutes away)
- Stress Level: {ctx.stress_level}/10
- Energy Level: {ctx.energy_level}/10
- Time of Day: {ctx.time_of_day}
- PC Battery: {ctx.pc_battery}% if ctx.pc_battery else 'Unknown'
- Phone Battery: {ctx.phone_battery}% if ctx.phone_battery else 'Unknown'
- Active App: {ctx.active_app or 'None'}
- CPU Usage: {ctx.system_cpu}% if ctx.system_cpu else 'Unknown'

Analyze this context and suggest 2-3 autonomous goals LOVE should set for Karthi.
Each goal should be:
- Proactive and helpful
- Based on the current situation
- Actionable and specific
- Prioritized appropriately

Return a JSON response with this structure:
{{
  "goals": [
    {{
      "title": "Goal title",
      "description": "Detailed description of what needs to be done",
      "priority": "critical|high|medium|low",
      "reasoning": "Why this goal is important right now"
    }}
  ]
}}"""

            # Use reasoning LLM for goal generation
            from core.agent import chat
            response = chat(goal_generation_prompt, mode="reasoning")
            
            # Parse goals from response
            plan_text = response.get("response", "")
            import re
            json_match = re.search(r'\{[\s\S]*\}', plan_text)
            
            if json_match:
                goal_data = json.loads(json_match.group())
                for goal_info in goal_data.get("goals", []):
                    priority_map = {
                        "critical": GoalPriority.CRITICAL,
                        "high": GoalPriority.HIGH,
                        "medium": GoalPriority.MEDIUM,
                        "low": GoalPriority.LOW
                    }
                    priority = priority_map.get(goal_info.get("priority", "medium"), GoalPriority.MEDIUM)
                    
                    goal_id = self.set_goal(
                        title=goal_info.get("title", "Autonomous Goal"),
                        description=goal_info.get("description", ""),
                        priority=priority,
                        reasoning=goal_info.get("reasoning", "Generated by autonomous analysis")
                    )
                    goals_created.append(goal_id)
                    self.plan_goal(goal_id)
            else:
                # Fallback to rule-based goals if LLM fails
                self._fallback_goal_generation(ctx, goals_created)
            
            print(f"[AutonomousAgent] Generated {len(goals_created)} autonomous goals")
            return goals_created
            
        except Exception as e:
            print(f"[AutonomousAgent] Goal generation error: {e}")
            # Fallback to rule-based generation
            ctx = get_live_context()
            return self._fallback_goal_generation(ctx, goals_created)
    
    def _fallback_goal_generation(self, ctx, goals_created: List[str]) -> List[str]:
        """Fallback rule-based goal generation if LLM fails."""
        # Goal: Prepare for upcoming meeting
        if ctx.next_event and ctx.next_event.get('minutes_away', 999) <= 30:
            goal_id = self.set_goal(
                title=f"Prepare for {ctx.next_event.get('title', 'meeting')}",
                description=f"Review relevant documents, prepare talking points, and ensure Karthi is ready for upcoming meeting",
                priority=GoalPriority.HIGH,
                reasoning=f"Meeting '{ctx.next_event.get('title')}' starts in {ctx.next_event.get('minutes_away')} minutes. Karthi needs preparation time."
            )
            goals_created.append(goal_id)
            self.plan_goal(goal_id)
        
        # Goal: Manage high stress
        if ctx.stress_level > 7:
            goal_id = self.set_goal(
                title="Reduce Karthi's stress",
                description="Identify stress sources and suggest stress relief activities",
                priority=GoalPriority.CRITICAL,
                reasoning=f"Karthi's stress level is {ctx.stress_level}/10. This is unacceptably high and requires immediate attention."
            )
            goals_created.append(goal_id)
            self.plan_goal(goal_id)
        
        # Goal: Complete urgent tasks
        if ctx.tasks_due_today > 3:
            goal_id = self.set_goal(
                title="Help complete today's urgent tasks",
                description=f"Prioritize and assist with {ctx.tasks_due_today} tasks due today",
                priority=GoalPriority.HIGH,
                reasoning=f"Karthi has {ctx.tasks_due_today} tasks due today. Proactive assistance needed to ensure completion."
            )
            goals_created.append(goal_id)
            self.plan_goal(goal_id)
        
        return goals_created
    
    def get_goal_status(self, goal_id: str) -> Optional[Dict]:
        """Get status of a specific goal"""
        if goal_id not in self.goals:
            return None
        goal = self.goals[goal_id]
        return {
            "id": goal.id,
            "title": goal.title,
            "description": goal.description,
            "status": goal.status.value,
            "priority": goal.priority.name,
            "progress": goal.progress,
            "actions_count": len(goal.plan),
            "completed_actions": sum(1 for a in goal.plan if a.status == GoalStatus.COMPLETED),
            "reasoning": goal.reasoning,
            "created_at": goal.created_at,
            "deadline": goal.deadline
        }
    
    def get_all_goals(self) -> List[Dict]:
        """Get all goals with their status"""
        return [self.get_goal_status(gid) for gid in self.goals.keys()]


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_autonomous_agent() -> AutonomousAgent:
    """Get the singleton autonomous agent instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = AutonomousAgent()
    return _instance
