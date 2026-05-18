"""
Project LOVE - Specialized Agents
Modular agents for fitness, learning, emotional wellness, and productivity.
"""

from .fitness_agent import FitnessAgent, get_fitness_status, log_workout
from .learning_agent import LearningAgent, get_learning_progress, add_study_material
from .emotional_agent import EmotionalAgent, log_mood, get_emotional_insights
from .task_agent import TaskAgent, get_task_overview, create_project

__all__ = [
    'FitnessAgent', 'get_fitness_status', 'log_workout',
    'LearningAgent', 'get_learning_progress', 'add_study_material',
    'EmotionalAgent', 'log_mood', 'get_emotional_insights',
    'TaskAgent', 'get_task_overview', 'create_project',
]
