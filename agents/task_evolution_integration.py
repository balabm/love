"""
Evolution Integration for Task Agent

This module adds evolution capabilities to the task agent:
1. EVOLUTION-AWARE TASK MANAGEMENT
   - Tasks can trigger evolution hypotheses
   - Task completion patterns inform evolution
   - Productivity metrics guide evolutionary pressures

2. ADAPTIVE PRIORITIZATION
   - Learns from user task patterns
   - Evolves prioritization strategies
   - Adapts to changing work styles

3. PERFORMANCE TRACKING
   - Tracks task completion efficiency
   - Measures time estimation accuracy
   - Identifies productivity bottlenecks

4. EVOLUTIONARY FEEDBACK
   - Provides feedback to evolution system
   - Reports capability gaps
   - Suggests process improvements
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

DATA_DIR = Path(__file__).parent.parent / "data" / "task_evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TASK_EVOLUTION_STATE = DATA_DIR / "task_evolution_state.json"
PRODUCTIVITY_METRICS = DATA_DIR / "productivity_metrics.jsonl"
EVOLUTION_FEEDBACK = DATA_DIR / "evolution_feedback.jsonl"


@dataclass
class TaskPattern:
    """A pattern in task management."""
    id: str = ""
    pattern_type: str = ""  # completion_time, prioritization, estimation
    description: str = ""
    frequency: int = 0
    effectiveness: float = 0.5
    last_observed: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProductivityMetric:
    """Productivity metric for evolution feedback."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat)
    tasks_completed: int = 0
    tasks_created: int = 0
    completion_rate: float = 0.0
    avg_completion_time: float = 0.0
    estimation_accuracy: float = 0.0
    focus_efficiency: float = 0.0
    energy_alignment: float = 0.0


class TaskEvolutionIntegration:
    """
    Integration between task agent and evolution system.
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
        self._patterns: Dict[str, TaskPattern] = {}
        self._productivity_history: List[ProductivityMetric] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_state()
    
    # ── Task Pattern Detection ───────────────────────────────────────────────────
    
    def analyze_task_patterns(self, tasks: List[Any]) -> List[TaskPattern]:
        """Analyze tasks to detect patterns."""
        new_patterns = []
        
        if not tasks:
            return new_patterns
        
        # Pattern: Tasks consistently take longer than estimated
        overdue_tasks = [t for t in tasks if hasattr(t, 'due_date') and t.due_date and 
                        hasattr(t, 'completed_at') and t.completed_at]
        if overdue_tasks:
            pattern = TaskPattern(
                id="time_estimation_pattern",
                pattern_type="estimation",
                description="Tasks consistently exceed time estimates",
                frequency=len(overdue_tasks),
                effectiveness=0.3,  # Low effectiveness indicates issue
            )
            if pattern.id not in self._patterns:
                self._patterns[pattern.id] = pattern
                new_patterns.append(pattern)
        
        # Pattern: High priority tasks completed faster
        high_priority_completed = [t for t in tasks if hasattr(t, 'priority') and 
                                   t.priority == "high" and hasattr(t, 'status') and t.status == "done"]
        if len(high_priority_completed) > 5:
            pattern = TaskPattern(
                id="high_priority_efficiency",
                pattern_type="prioritization",
                description="High priority tasks show good completion rates",
                frequency=len(high_priority_completed),
                effectiveness=0.8,
            )
            if pattern.id not in self._patterns:
                self._patterns[pattern.id] = pattern
                new_patterns.append(pattern)
        
        if new_patterns:
            self._save_state()
        
        return new_patterns
    
    # ── Productivity Tracking ───────────────────────────────────────────────────
    
    def track_productivity(self, tasks: List[Any]) -> ProductivityMetric:
        """Track productivity metrics for evolution feedback."""
        try:
            completed = [t for t in tasks if hasattr(t, 'status') and t.status == "done"]
            total = len(tasks)
            
            metric = ProductivityMetric(
                tasks_completed=len(completed),
                tasks_created=total,
                completion_rate=len(completed) / max(1, total),
            )
            
            # Calculate average completion time
            if completed:
                completion_times = []
                for task in completed:
                    if hasattr(task, 'created_at') and hasattr(task, 'completed_at'):
                        try:
                            created = datetime.fromisoformat(task.created_at)
                            completed = datetime.fromisoformat(task.completed_at)
                            duration = (completed - created).total_seconds() / 60  # minutes
                            completion_times.append(duration)
                        except Exception:
                            pass
                
                if completion_times:
                    metric.avg_completion_time = sum(completion_times) / len(completion_times)
            
            # Calculate estimation accuracy
            estimated_tasks = [t for t in tasks if hasattr(t, 'estimated_minutes') and t.estimated_minutes]
            if estimated_tasks and completed:
                accurate_estimations = 0
                for task in estimated_tasks:
                    if hasattr(task, 'status') and task.status == "done":
                        # Simplified accuracy check
                        if hasattr(task, 'created_at') and hasattr(task, 'completed_at'):
                            try:
                                created = datetime.fromisoformat(task.created_at)
                                completed = datetime.fromisoformat(task.completed_at)
                                actual_time = (completed - created).total_seconds() / 60
                                if abs(actual_time - task.estimated_minutes) / task.estimated_minutes < 0.2:
                                    accurate_estimations += 1
                            except Exception:
                                pass
                
                metric.estimation_accuracy = accurate_estimations / max(1, len(estimated_tasks))
            
            self._productivity_history.append(metric)
            self._log_productivity(metric)
            self._save_state()
            
            return metric
            
        except Exception as e:
            print(f"[TaskEvolution] Productivity tracking error: {e}")
            return ProductivityMetric()
    
    # ── Evolution Feedback ─────────────────────────────────────────────────────
    
    def provide_evolution_feedback(self) -> Dict[str, Any]:
        """Provide feedback to the evolution system."""
        try:
            feedback = {
                "capability_gaps": [],
                "evolutionary_pressures": {},
                "suggested_improvements": [],
            }
            
            # Analyze recent productivity
            if self._productivity_history:
                recent = self._productivity_history[-10:]
                avg_completion_rate = sum(m.completion_rate for m in recent) / len(recent)
                avg_estimation_accuracy = sum(m.estimation_accuracy for m in recent) / len(recent)
                
                # Identify capability gaps
                if avg_completion_rate < 0.5:
                    feedback["capability_gaps"].append({
                        "area": "task_management",
                        "severity": "high",
                        "description": "Low task completion rate",
                    })
                
                if avg_estimation_accuracy < 0.6:
                    feedback["capability_gaps"].append({
                        "area": "time_estimation",
                        "severity": "medium",
                        "description": "Poor time estimation accuracy",
                    })
                
                # Set evolutionary pressures
                feedback["evolutionary_pressures"] = {
                    "career": 1.0 - avg_completion_rate,  # Higher pressure when completion is low
                    "productivity": 1.0 - avg_estimation_accuracy,
                }
                
                # Suggest improvements
                if avg_completion_rate < 0.5:
                    feedback["suggested_improvements"].append(
                        "Implement better task prioritization strategies"
                    )
                if avg_estimation_accuracy < 0.6:
                    feedback["suggested_improvements"].append(
                        "Improve time estimation through historical analysis"
                    )
            
            self._log_evolution_feedback(feedback)
            
            return feedback
            
        except Exception as e:
            print(f"[TaskEvolution] Feedback generation error: {e}")
            return {}
    
    # ── Adaptive Prioritization ───────────────────────────────────────────────────
    
    def get_adaptive_prioritization(self, tasks: List[Any]) -> Dict[str, Any]:
        """Get adaptive prioritization suggestions based on patterns."""
        suggestions = {
            "strategy": "default",
            "reasoning": "",
            "adjustments": [],
        }
        
        # Check for patterns
        if "high_priority_efficiency" in self._patterns:
            pattern = self._patterns["high_priority_efficiency"]
            if pattern.effectiveness > 0.7:
                suggestions["strategy"] = "priority_focused"
                suggestions["reasoning"] = "High priority tasks show good completion rates"
                suggestions["adjustments"].append("Increase weight of high priority tasks")
        
        if "time_estimation_pattern" in self._patterns:
            pattern = self._patterns["time_estimation_pattern"]
            if pattern.effectiveness < 0.5:
                suggestions["adjustments"].append("Add buffer to time estimates")
                suggestions["adjustments"].append("Break down large tasks")
        
        return suggestions
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        try:
            if TASK_EVOLUTION_STATE.exists():
                data = json.loads(TASK_EVOLUTION_STATE.read_text())
                for pid, pd in data.get("patterns", {}).items():
                    self._patterns[pid] = TaskPattern(**pd)
        except Exception as e:
            print(f"[TaskEvolution] State load error: {e}")
    
    def _save_state(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "patterns": {pid: asdict(p) for pid, p in self._patterns.items()},
            }
            TASK_EVOLUTION_STATE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[TaskEvolution] State save error: {e}")
    
    def _log_productivity(self, metric: ProductivityMetric):
        try:
            with open(PRODUCTIVITY_METRICS, "a") as f:
                f.write(json.dumps(asdict(metric)) + "\n")
        except Exception:
            pass
    
    def _log_evolution_feedback(self, feedback: Dict):
        try:
            with open(EVOLUTION_FEEDBACK, "a") as f:
                f.write(json.dumps(feedback) + "\n")
        except Exception:
            pass
    
    # ── Integration Hooks ───────────────────────────────────────────────────────
    
    def on_task_completed(self, task: Any):
        """Called when a task is completed."""
        # Track completion for pattern detection
        pass
    
    def on_task_created(self, task: Any):
        """Called when a task is created."""
        # Track creation for productivity metrics
        pass
    
    def on_tasks_changed(self, tasks: List[Any]):
        """Called when tasks change."""
        # Analyze patterns and provide feedback
        self.analyze_task_patterns(tasks)
        self.track_productivity(tasks)


    # ── Background Loop ───────────────────────────────────────────────────────
    
    def start(self):
        """Start the task evolution background loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-TaskEvolution"
        )
        self._thread.start()
        print("[TaskEvolution] Started — task evolution active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(180)
        while self._running:
            try:
                # Periodic pattern analysis
                from agents.task_agent import get_task_overview
                tasks = get_task_overview()
                self.analyze_task_patterns(tasks)
                self.track_productivity(tasks)
            except Exception as e:
                print(f"[TaskEvolution] Loop error: {e}")
            time.sleep(3600)
    
# ── Singleton Access ─────────────────────────────────────────────────────────────

_task_evolution_instance: Optional[TaskEvolutionIntegration] = None
_task_evolution_lock = threading.Lock()


def get_task_evolution_integration() -> TaskEvolutionIntegration:
    global _task_evolution_instance
    with _task_evolution_lock:
        if _task_evolution_instance is None:
            _task_evolution_instance = TaskEvolutionIntegration()
        return _task_evolution_instance


# ── Integration with Task Agent ───────────────────────────────────────────────────

def enhance_task_agent_with_evolution():
    """
    Enhance the task agent with evolution capabilities.
    Call this from the task agent module to add evolution integration.
    """
    try:
        evolution = get_task_evolution_integration()
        
        # Hook into task agent functions (would need to modify task_agent.py)
        # This is a template for integration
        
        print("[TaskEvolution] Evolution integration loaded")
        return True
        
    except Exception as e:
        print(f"[TaskEvolution] Integration error: {e}")
        return False