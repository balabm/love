"""
Task Agent - Project Management & Productivity
Advanced task tracking with projects, priorities, and context-aware suggestions.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from core.settings import get_settings
from core.memory import save_log

SETTINGS = get_settings()
DATA_DIR = Path(__file__).parent.parent / "data"
TASKS_DB = DATA_DIR / "tasks_log.json"


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    project_id: Optional[str] = None
    status: str = TaskStatus.TODO.value
    priority: str = Priority.MEDIUM.name.lower()
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: Optional[str] = None
    estimated_minutes: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    completed_at: Optional[str] = None
    notes: str = ""
    energy_required: str = "medium"  # low, medium, high
    focus_required: str = "medium"  # shallow, medium, deep


@dataclass
class Project:
    id: str
    name: str
    description: str = ""
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    target_completion: Optional[str] = None
    color: str = "#3b82f6"  # Default blue


class TaskAgent:
    """Advanced task and project management agent."""
    
    def __init__(self):
        self.data_file = TASKS_DB
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        if not self.data_file.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_data({
                'tasks': [],
                'projects': [],
                'contexts': [],
                'archived': []
            })
    
    def _load_data(self) -> Dict:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {'tasks': [], 'projects': [], 'contexts': [], 'archived': []}
    
    def _save_data(self, data: Dict):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_project(self, name: str, description: str = "", 
                       target_date: Optional[str] = None, color: str = "#3b82f6") -> Dict[str, Any]:
        """Create a new project."""
        data = self._load_data()
        
        project = Project(
            id=f"proj_{len(data['projects'])+1}_{datetime.now().strftime('%Y%m%d')}",
            name=name,
            description=description,
            target_completion=target_date,
            color=color
        )
        
        data['projects'].append(asdict(project))
        self._save_data(data)
        
        return {
            'success': True,
            'project': asdict(project),
            'message': f"Project '{name}' created. Ready to add tasks."
        }
    
    def create_task(self, title: str, **kwargs) -> Dict[str, Any]:
        """Create a new task."""
        data = self._load_data()
        
        task = Task(
            id=f"task_{len(data['tasks'])+1}_{datetime.now().strftime('%Y%m%d%H%M')}",
            title=title,
            **kwargs
        )
        
        data['tasks'].append(asdict(task))
        self._save_data(data)
        
        save_log('tasks', {
            'event': 'task_created',
            'task_id': task.id,
            'title': title,
            'project': task.project_id
        })
        
        return {
            'success': True,
            'task': asdict(task),
            'message': f"Task added: {title}"
        }
    
    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """Mark task as complete."""
        data = self._load_data()
        
        for task in data['tasks']:
            if task['id'] == task_id:
                task['status'] = TaskStatus.DONE.value
                task['completed_at'] = datetime.now().isoformat()
                self._save_data(data)
                
                save_log('tasks', {
                    'event': 'task_completed',
                    'task_id': task_id,
                    'title': task['title']
                })
                
                # Calculate completion stats
                project_tasks = [t for t in data['tasks'] if t.get('project_id') == task.get('project_id')]
                project_done = [t for t in project_tasks if t['status'] == TaskStatus.DONE.value]
                
                if project_tasks:
                    progress = len(project_done) / len(project_tasks) * 100
                    return {
                        'success': True,
                        'task': task,
                        'message': f"{task['title']} done. Project {progress:.0f}% complete."
                    }
                
                return {
                    'success': True,
                    'task': task,
                    'message': f"{task['title']} completed. Good work."
                }
        
        return {'success': False, 'error': 'Task not found'}
    
    def get_task_overview(self) -> Dict[str, Any]:
        """Get comprehensive task overview."""
        data = self._load_data()
        
        # Active tasks
        active = [t for t in data['tasks'] if t['status'] != TaskStatus.DONE.value]
        done = [t for t in data['tasks'] if t['status'] == TaskStatus.DONE.value]
        
        # By status
        by_status = {}
        for status in TaskStatus:
            count = len([t for t in data['tasks'] if t['status'] == status.value])
            by_status[status.value] = count
        
        # By priority
        by_priority = {}
        for p in Priority:
            count = len([t for t in active if t.get('priority') == p.name.lower()])
            by_priority[p.name.lower()] = count
        
        # Due soon (next 3 days)
        soon = datetime.now() + timedelta(days=3)
        due_soon = [
            t for t in active
            if t.get('due_date') and datetime.fromisoformat(t['due_date']) <= soon
        ]
        
        # Stuck tasks (in progress for >3 days)
        stuck_threshold = datetime.now() - timedelta(days=3)
        stuck = [
            t for t in active
            if t['status'] == TaskStatus.IN_PROGRESS.value
            and datetime.fromisoformat(t.get('created_at', datetime.now().isoformat())) < stuck_threshold
        ]
        
        # Generate insight
        if len(due_soon) >= 3:
            insight = f"{len(due_soon)} tasks due soon. Prioritize what matters most."
        elif len(stuck) >= 2:
            insight = f"{len(stuck)} tasks stuck in-progress. Time to ship or cut scope."
        elif len(active) > 10:
            insight = f"{len(active)} active tasks. List is getting heavy. Review for pruning."
        elif len(active) == 0:
            insight = "No active tasks. Open window for deep work or new projects."
        else:
            insight = f"{len(active)} tasks active, {len(done)} completed. Steady progress."
        
        return {
            'active_count': len(active),
            'completed_count': len(done),
            'by_status': by_status,
            'by_priority': by_priority,
            'due_soon': due_soon,
            'stuck_tasks': stuck,
            'projects': data['projects'],
            'insight': insight,
            'suggestion': self._generate_task_suggestion(active, due_soon, stuck)
        }
    
    def _generate_task_suggestion(self, active: List[Dict], due_soon: List[Dict], 
                                   stuck: List[Dict]) -> str:
        """Generate task management suggestion."""
        if due_soon:
            return f"Focus on '{due_soon[0]['title']}' — due soonest."
        elif stuck:
            return f"'{stuck[0]['title']}' has been in-progress for days. Ship it or kill it."
        elif active:
            # Find high priority
            critical = [t for t in active if t.get('priority') == 'critical']
            if critical:
                return f"'{critical[0]['title']}' is critical priority. Do this first."
            
            # Find quick wins (<30 min, low energy)
            quick = [
                t for t in active
                if t.get('estimated_minutes', 60) <= 30
                and t.get('energy_required') == 'low'
            ]
            if quick:
                return f"Knock out '{quick[0]['title']}' — quick win, low energy."
        
        return "Review your task list. What moves the needle?"
    
    def suggest_task_by_context(self, time_of_day: str, energy_level: str, 
                              available_minutes: int) -> Optional[Dict[str, Any]]:
        """Suggest optimal task based on current context."""
        data = self._load_data()
        active = [t for t in data['tasks'] if t['status'] != TaskStatus.DONE.value]
        
        # Filter by energy and time
        candidates = [
            t for t in active
            if t.get('energy_required', 'medium') == energy_level
            and t.get('estimated_minutes', 60) <= available_minutes
        ]
        
        # Filter by focus level for time of day
        if time_of_day in ['morning', 'deep_work']:
            # Prefer deep focus tasks
            deep_tasks = [t for t in candidates if t.get('focus_required') == 'deep']
            if deep_tasks:
                return deep_tasks[0]
        elif time_of_day in ['afternoon', 'shallow_work']:
            # Prefer shallow tasks
            shallow = [t for t in candidates if t.get('focus_required') == 'shallow']
            if shallow:
                return shallow[0]
        
        # Return highest priority
        priority_order = ['critical', 'high', 'medium', 'low']
        for p in priority_order:
            for t in candidates:
                if t.get('priority') == p:
                    return t
        
        return candidates[0] if candidates else None
    
    def get_project_progress(self, project_id: str) -> Dict[str, Any]:
        """Get progress for a specific project."""
        data = self._load_data()
        
        project = None
        for p in data['projects']:
            if p['id'] == project_id:
                project = p
                break
        
        if not project:
            return {'error': 'Project not found'}
        
        project_tasks = [t for t in data['tasks'] if t.get('project_id') == project_id]
        done = [t for t in project_tasks if t['status'] == TaskStatus.DONE.value]
        
        return {
            'project': project,
            'total_tasks': len(project_tasks),
            'completed_tasks': len(done),
            'progress_percent': round(len(done) / len(project_tasks) * 100, 1) if project_tasks else 0,
            'tasks': project_tasks
        }
    
    def ai_prioritize_tasks(self, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Use AI to prioritize tasks based on context, deadlines, and dependencies."""
        try:
            from core.llm import get_reasoning_llm
            from core.context_engine import get_live_context
            
            data = self._load_data()
            active = [t for t in data['tasks'] if t['status'] != TaskStatus.DONE.value]
            
            if not active:
                return {'error': 'No active tasks to prioritize'}
            
            # Get context
            ctx = get_live_context() if not context else context
            
            # Prepare task list for AI
            task_list = []
            for task in active[:20]:  # Limit to 20 tasks
                task_info = {
                    'title': task['title'],
                    'priority': task.get('priority', 'medium'),
                    'due_date': task.get('due_date'),
                    'estimated_minutes': task.get('estimated_minutes'),
                    'energy_required': task.get('energy_required', 'medium'),
                    'focus_required': task.get('focus_required', 'medium'),
                }
                task_list.append(task_info)
            
            # Build prompt
            prompt = f"""You are a task prioritization assistant for Karthi. 
Current context:
- Time: {ctx.local_time} ({ctx.time_of_day})
- Mood: {ctx.mood_score if ctx.mood_score else 'unknown'}/10
- Stress: {ctx.stress_score if ctx.stress_score else 'unknown'}/10
- Energy: {ctx.energy_score if ctx.energy_score else 'unknown'}/10
- Active project: {ctx.active_project or 'none'}
- Tasks due today: {ctx.tasks_due_today}
- Upcoming meeting: {ctx.next_event.get('title') if ctx.next_event else 'none'}

Tasks to prioritize:
{json.dumps(task_list, indent=2)}

Analyze these tasks and provide a ranked list with scores (0-100) based on:
1. Deadline urgency
2. Alignment with current energy/focus
3. Project importance
4. Dependencies (if implied)
5. Quick win potential

Return JSON format:
{{
  "prioritized_tasks": [
    {{"task_title": "title", "score": 85, "reasoning": "brief explanation"}},
    ...
  ],
  "overall_strategy": "brief strategy for today"
}}"""

            llm = get_reasoning_llm(temperature=0.3, max_tokens=800)
            response = llm.invoke(prompt)
            
            # Parse response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    # Update task scores in database
                    for prioritized in result.get('prioritized_tasks', []):
                        for task in active:
                            if task['title'] == prioritized.get('task_title'):
                                task['ai_priority_score'] = prioritized.get('score', 50)
                                task['ai_priority_reasoning'] = prioritized.get('reasoning', '')
                                break
                    
                    self._save_data(data)
                    
                    return {
                        'success': True,
                        'prioritized_tasks': result.get('prioritized_tasks', []),
                        'strategy': result.get('overall_strategy', ''),
                        'total_tasks': len(active),
                        'message': f'Prioritized {len(active)} tasks with AI'
                    }
            except Exception as e:
                print(f"[TaskAgent] AI prioritization parsing error: {e}")
                return {'error': 'Failed to parse AI response'}
            
        except Exception as e:
            print(f"[TaskAgent] AI prioritization error: {e}")
            return {'error': str(e)}
    
    def get_smart_task_suggestions(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get AI-powered task suggestions based on current context."""
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            
            data = self._load_data()
            active = [t for t in data['tasks'] if t['status'] != TaskStatus.DONE.value]
            
            if not active:
                return []
            
            suggestions = []
            
            # Filter tasks based on context
            time_of_day = ctx.time_of_day
            energy = ctx.energy_score if ctx.energy_score else 5
            stress = ctx.stress_score if ctx.stress_score else 0
            
            # High stress -> suggest low energy, quick tasks
            if stress > 7:
                candidates = [
                    t for t in active
                    if t.get('energy_required') == 'low'
                    and t.get('estimated_minutes', 60) <= 30
                ]
                if candidates:
                    suggestions.append({
                        'type': 'stress_relief',
                        'task': candidates[0],
                        'reason': 'Low energy task to reduce stress'
                    })
            
            # Morning high energy -> suggest deep work
            elif time_of_day == 'morning' and energy > 6:
                candidates = [
                    t for t in active
                    if t.get('focus_required') == 'deep'
                    and t.get('priority') in ['critical', 'high']
                ]
                if candidates:
                    suggestions.append({
                        'type': 'deep_work',
                        'task': candidates[0],
                        'reason': 'Prime time for deep, focused work'
                    })
            
            # Afternoon slump -> suggest shallow tasks
            elif time_of_day == 'afternoon' and energy < 5:
                candidates = [
                    t for t in active
                    if t.get('focus_required') in ['shallow', 'medium']
                    and t.get('estimated_minutes', 60) <= 30
                ]
                if candidates:
                    suggestions.append({
                        'type': 'quick_win',
                        'task': candidates[0],
                        'reason': 'Quick win to maintain momentum'
                    })
            
            # Due soon tasks
            soon = datetime.now() + timedelta(hours=24)
            due_tasks = [
                t for t in active
                if t.get('due_date') and datetime.fromisoformat(t['due_date']) <= soon
            ]
            if due_tasks and len(suggestions) < count:
                for task in due_tasks[:2]:
                    if task not in [s.get('task') for s in suggestions]:
                        suggestions.append({
                            'type': 'deadline',
                            'task': task,
                            'reason': 'Due soon - prioritize'
                        })
            
            # Fill remaining with AI-prioritized tasks
            if len(suggestions) < count:
                prioritized = self.ai_prioritize_tasks()
                if prioritized.get('success'):
                    for pt in prioritized.get('prioritized_tasks', [])[:count - len(suggestions)]:
                        for task in active:
                            if task['title'] == pt.get('task_title'):
                                suggestions.append({
                                    'type': 'ai_prioritized',
                                    'task': task,
                                    'reason': pt.get('reasoning', 'AI prioritized')
                                })
                                break
            
            return suggestions[:count]
            
        except Exception as e:
            print(f"[TaskAgent] Smart suggestions error: {e}")
            return []


# Public API functions
def create_project(name: str, **kwargs) -> Dict[str, Any]:
    """Create a project."""
    agent = TaskAgent()
    return agent.create_project(name, **kwargs)


def get_task_overview() -> Dict[str, Any]:
    """Get task overview."""
    agent = TaskAgent()
    return agent.get_task_overview()


def suggest_next_task(energy: str = "medium", minutes: int = 60) -> Optional[Dict]:
    """Suggest next task based on context."""
    agent = TaskAgent()
    from datetime import datetime
    hour = datetime.now().hour
    
    if 6 <= hour < 12:
        time_context = 'morning'
    elif 12 <= hour < 17:
        time_context = 'afternoon'
    else:
        time_context = 'evening'
    
    return agent.suggest_task_by_context(time_context, energy, minutes)
