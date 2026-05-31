import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"authenticity_amplifier": {"available": True},\n            "overall": "healthy"',
    '"authenticity_amplifier": {"available": True},\n            "humor_playfulness_trainer": {"available": True},\n            "joy_cultivator": {"available": True},\n            "celebration_architect": {"available": True},\n            "spontaneity_generator": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Authenticity Amplifier (true self intelligence)\n\nUsage:',
    '- Authenticity Amplifier (true self intelligence)\n- Humor & Playfulness Trainer (lightness intelligence)\n- Joy Cultivator (delight intelligence)\n- Celebration Architect (recognition intelligence)\n- Spontaneity Generator (surprise intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Authenticity Amplifier", "core.authenticity_amplifier", "get_authenticity_amplifier"),\n    ]',
    '("Authenticity Amplifier", "core.authenticity_amplifier", "get_authenticity_amplifier"),\n        ("Humor & Playfulness Trainer", "core.humor_playfulness_trainer", "get_humor_playfulness_trainer"),\n        ("Joy Cultivator", "core.joy_cultivator", "get_joy_cultivator"),\n        ("Celebration Architect", "core.celebration_architect", "get_celebration_architect"),\n        ("Spontaneity Generator", "core.spontaneity_generator", "get_spontaneity_generator"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"authenticity_amplifier",\n            ]',
    '"authenticity_amplifier",\n                "humor_playfulness_trainer", "joy_cultivator",\n                "celebration_architect", "spontaneity_generator",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("authenticity_amplifier", "Authenticity Amplifier"),\n            ]',
    '("authenticity_amplifier", "Authenticity Amplifier"),\n                ("humor_playfulness_trainer", "Humor & Playfulness Trainer"),\n                ("joy_cultivator", "Joy Cultivator"),\n                ("celebration_architect", "Celebration Architect"),\n                ("spontaneity_generator", "Spontaneity Generator"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
