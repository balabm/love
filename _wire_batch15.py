import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"trust_builder": {"available": True},\n            "overall": "healthy"',
    '"trust_builder": {"available": True},\n            "curiosity_spark": {"available": True},\n            "play_coach": {"available": True},\n            "adventure_planner": {"available": True},\n            "wonder_tracker": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Trust Builder (relational intelligence)\n\nUsage:',
    '- Trust Builder (relational intelligence)\n- Curiosity Spark (wonder intelligence)\n- Play Coach (joy intelligence)\n- Adventure Planner (experience intelligence)\n- Wonder Tracker (awe intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Trust Builder", "core.trust_builder", "get_trust_builder"),\n    ]',
    '("Trust Builder", "core.trust_builder", "get_trust_builder"),\n        ("Curiosity Spark", "core.curiosity_spark", "get_curiosity_spark"),\n        ("Play Coach", "core.play_coach", "get_play_coach"),\n        ("Adventure Planner", "core.adventure_planner", "get_adventure_planner"),\n        ("Wonder Tracker", "core.wonder_tracker", "get_wonder_tracker"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"trust_builder",\n            ]',
    '"trust_builder",\n                "curiosity_spark", "play_coach",\n                "adventure_planner", "wonder_tracker",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("trust_builder", "Trust Builder"),\n            ]',
    '("trust_builder", "Trust Builder"),\n                ("curiosity_spark", "Curiosity Spark"),\n                ("play_coach", "Play Coach"),\n                ("adventure_planner", "Adventure Planner"),\n                ("wonder_tracker", "Wonder Tracker"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
