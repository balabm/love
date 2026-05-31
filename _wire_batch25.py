import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"mindful_productivity_coach": {"available": True},\n            "overall": "healthy"',
    '"mindful_productivity_coach": {"available": True},\n            "sleep_optimizer": {"available": True},\n            "nutrition_coach": {"available": True},\n            "movement_tracker": {"available": True},\n            "health_integrator": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Mindful Productivity Coach (conscious efficiency intelligence)\n\nUsage:',
    '- Mindful Productivity Coach (conscious efficiency intelligence)\n- Sleep Optimizer (rest intelligence)\n- Nutrition Coach (fuel intelligence)\n- Movement Tracker (body intelligence)\n- Health Integrator (holistic health intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Mindful Productivity Coach", "core.mindful_productivity_coach", "get_mindful_productivity_coach"),\n    ]',
    '("Mindful Productivity Coach", "core.mindful_productivity_coach", "get_mindful_productivity_coach"),\n        ("Sleep Optimizer", "core.sleep_optimizer", "get_sleep_optimizer"),\n        ("Nutrition Coach", "core.nutrition_coach", "get_nutrition_coach"),\n        ("Movement Tracker", "core.movement_tracker", "get_movement_tracker"),\n        ("Health Integrator", "core.health_integrator", "get_health_integrator"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"mindful_productivity_coach",\n            ]',
    '"mindful_productivity_coach",\n                "sleep_optimizer", "nutrition_coach",\n                "movement_tracker", "health_integrator",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("mindful_productivity_coach", "Mindful Productivity Coach"),\n            ]',
    '("mindful_productivity_coach", "Mindful Productivity Coach"),\n                ("sleep_optimizer", "Sleep Optimizer"),\n                ("nutrition_coach", "Nutrition Coach"),\n                ("movement_tracker", "Movement Tracker"),\n                ("health_integrator", "Health Integrator"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
