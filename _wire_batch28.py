import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"presence_amplifier": {"available": True},\n            "overall": "healthy"',
    '"presence_amplifier": {"available": True},\n            "creativity_catalyst": {"available": True},\n            "innovation_spark_generator": {"available": True},\n            "problem_reframer": {"available": True},\n            "perspective_shifter": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Presence Amplifier (embodied awareness intelligence)\n\nUsage:',
    '- Presence Amplifier (embodied awareness intelligence)\n- Creativity Catalyst (creative intelligence)\n- Innovation Spark Generator (breakthrough intelligence)\n- Problem Reframer (solution intelligence)\n- Perspective Shifter (cognitive flexibility intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Presence Amplifier", "core.presence_amplifier", "get_presence_amplifier"),\n    ]',
    '("Presence Amplifier", "core.presence_amplifier", "get_presence_amplifier"),\n        ("Creativity Catalyst", "core.creativity_catalyst", "get_creativity_catalyst"),\n        ("Innovation Spark Generator", "core.innovation_spark_generator", "get_innovation_spark_generator"),\n        ("Problem Reframer", "core.problem_reframer", "get_problem_reframer"),\n        ("Perspective Shifter", "core.perspective_shifter", "get_perspective_shifter"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"presence_amplifier",\n            ]',
    '"presence_amplifier",\n                "creativity_catalyst", "innovation_spark_generator",\n                "problem_reframer", "perspective_shifter",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("presence_amplifier", "Presence Amplifier"),\n            ]',
    '("presence_amplifier", "Presence Amplifier"),\n                ("creativity_catalyst", "Creativity Catalyst"),\n                ("innovation_spark_generator", "Innovation Spark Generator"),\n                ("problem_reframer", "Problem Reframer"),\n                ("perspective_shifter", "Perspective Shifter"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
