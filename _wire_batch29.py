import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"perspective_shifter": {"available": True},\n            "overall": "healthy"',
    '"perspective_shifter": {"available": True},\n            "curiosity_cultivator": {"available": True},\n            "learning_acceleration_engine": {"available": True},\n            "knowledge_synthesizer": {"available": True},\n            "wisdom_distiller": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Perspective Shifter (cognitive flexibility intelligence)\n\nUsage:',
    '- Perspective Shifter (cognitive flexibility intelligence)\n- Curiosity Cultivator (wonder intelligence)\n- Learning Acceleration Engine (rapid acquisition intelligence)\n- Knowledge Synthesizer (integration intelligence)\n- Wisdom Distiller (deep understanding intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Perspective Shifter", "core.perspective_shifter", "get_perspective_shifter"),\n    ]',
    '("Perspective Shifter", "core.perspective_shifter", "get_perspective_shifter"),\n        ("Curiosity Cultivator", "core.curiosity_cultivator", "get_curiosity_cultivator"),\n        ("Learning Acceleration Engine", "core.learning_acceleration_engine", "get_learning_acceleration_engine"),\n        ("Knowledge Synthesizer", "core.knowledge_synthesizer", "get_knowledge_synthesizer"),\n        ("Wisdom Distiller", "core.wisdom_distiller", "get_wisdom_distiller"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"perspective_shifter",\n            ]',
    '"perspective_shifter",\n                "curiosity_cultivator", "learning_acceleration_engine",\n                "knowledge_synthesizer", "wisdom_distiller",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("perspective_shifter", "Perspective Shifter"),\n            ]',
    '("perspective_shifter", "Perspective Shifter"),\n                ("curiosity_cultivator", "Curiosity Cultivator"),\n                ("learning_acceleration_engine", "Learning Acceleration Engine"),\n                ("knowledge_synthesizer", "Knowledge Synthesizer"),\n                ("wisdom_distiller", "Wisdom Distiller"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
