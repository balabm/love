import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"learning_path_optimizer": {"available": True},\n            "overall": "healthy"',
    '"learning_path_optimizer": {"available": True},\n            "focus_recovery_tracker": {"available": True},\n            "decision_journal": {"available": True},\n            "mood_journal": {"available": True},\n            "values_alignment_checker": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Learning Path Optimizer (adaptive learning sequences)\n\nUsage:',
    '- Learning Path Optimizer (adaptive learning sequences)\n- Focus Recovery Tracker (focus session intelligence)\n- Decision Journal (decision quality tracker)\n- Mood Journal (emotional pattern tracker)\n- Values Alignment Checker (integrity monitor)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Learning Path Optimizer", "core.learning_path_optimizer", "get_learning_path_optimizer"),\n    ]',
    '("Learning Path Optimizer", "core.learning_path_optimizer", "get_learning_path_optimizer"),\n        ("Focus Recovery Tracker", "core.focus_recovery_tracker", "get_focus_recovery_tracker"),\n        ("Decision Journal", "core.decision_journal", "get_decision_journal"),\n        ("Mood Journal", "core.mood_journal", "get_mood_journal"),\n        ("Values Alignment Checker", "core.values_alignment_checker", "get_values_alignment_checker"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"social_connection_monitor", "learning_path_optimizer",\n            ]',
    '"social_connection_monitor", "learning_path_optimizer",\n                "focus_recovery_tracker", "decision_journal",\n                "mood_journal", "values_alignment_checker",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("learning_path_optimizer", "Learning Path Optimizer"),\n            ]',
    '("learning_path_optimizer", "Learning Path Optimizer"),\n                ("focus_recovery_tracker", "Focus Recovery Tracker"),\n                ("decision_journal", "Decision Journal"),\n                ("mood_journal", "Mood Journal"),\n                ("values_alignment_checker", "Values Alignment Checker"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
