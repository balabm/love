import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"meeting_optimizer": {"available": True},\n            "overall": "healthy"',
    '"meeting_optimizer": {"available": True},\n            "finance_pattern_detector": {"available": True},\n            "nutrition_analyzer": {"available": True},\n            "exercise_optimizer": {"available": True},\n            "meditation_coach": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Meeting Optimizer (meeting intelligence)\n\nUsage:',
    '- Meeting Optimizer (meeting intelligence)\n- Finance Pattern Detector (financial intelligence)\n- Nutrition Analyzer (dietary intelligence)\n- Exercise Optimizer (fitness intelligence)\n- Meditation Coach (mindfulness intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Meeting Optimizer", "core.meeting_optimizer", "get_meeting_optimizer"),\n    ]',
    '("Meeting Optimizer", "core.meeting_optimizer", "get_meeting_optimizer"),\n        ("Finance Pattern Detector", "core.finance_pattern_detector", "get_finance_pattern_detector"),\n        ("Nutrition Analyzer", "core.nutrition_analyzer", "get_nutrition_analyzer"),\n        ("Exercise Optimizer", "core.exercise_optimizer", "get_exercise_optimizer"),\n        ("Meditation Coach", "core.meditation_coach", "get_meditation_coach"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"task_batch_optimizer", "meeting_optimizer",\n            ]',
    '"task_batch_optimizer", "meeting_optimizer",\n                "finance_pattern_detector", "nutrition_analyzer",\n                "exercise_optimizer", "meditation_coach",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("meeting_optimizer", "Meeting Optimizer"),\n            ]',
    '("meeting_optimizer", "Meeting Optimizer"),\n                ("finance_pattern_detector", "Finance Pattern Detector"),\n                ("nutrition_analyzer", "Nutrition Analyzer"),\n                ("exercise_optimizer", "Exercise Optimizer"),\n                ("meditation_coach", "Meditation Coach"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
