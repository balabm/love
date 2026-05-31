import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r') as f:
    content = f.read()
content = content.replace(
    '"smart_break_suggester": {"available": True},\n            "overall": "healthy"',
    '"smart_break_suggester": {"available": True},\n            "habit_streak_tracker": {"available": True},\n            "sleep_analyzer": {"available": True},\n            "social_connection_monitor": {"available": True},\n            "learning_path_optimizer": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py
with open('start_evolution.py', 'r') as f:
    content = f.read()
content = content.replace(
    '- Smart Break Suggester (optimal break timing)\n\nUsage:',
    '- Smart Break Suggester (optimal break timing)\n- Habit Streak Tracker (consistency and momentum)\n- Sleep Analyzer (sleep pattern intelligence)\n- Social Connection Monitor (relationship health)\n- Learning Path Optimizer (adaptive learning sequences)\n\nUsage:'
)
with open('start_evolution.py', 'w') as f:
    f.write(content)
print('Updated start_evolution.py')

# 3. daily_briefing.py
with open('core/daily_briefing.py', 'r') as f:
    content = f.read()
content = content.replace(
    '"emotion_aware_response", "knowledge_injector",\n            ]',
    '"emotion_aware_response", "knowledge_injector",\n                "habit_streak_tracker", "sleep_analyzer",\n                "social_connection_monitor", "learning_path_optimizer",\n            ]'
)
with open('core/daily_briefing.py', 'w') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 4. heartbeat.py
with open('core/heartbeat.py', 'r') as f:
    content = f.read()
content = content.replace(
    '("conversation_continuity", "Conversation Continuity"),\n            ]',
    '("conversation_continuity", "Conversation Continuity"),\n                ("habit_streak_tracker", "Habit Streak Tracker"),\n                ("sleep_analyzer", "Sleep Analyzer"),\n                ("social_connection_monitor", "Social Connection Monitor"),\n                ("learning_path_optimizer", "Learning Path Optimizer"),\n            ]'
)
with open('core/heartbeat.py', 'w') as f:
    f.write(content)
print('Updated core/heartbeat.py')
