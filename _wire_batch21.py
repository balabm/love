import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"attention_guardian": {"available": True},\n            "overall": "healthy"',
    '"attention_guardian": {"available": True},\n            "identity_designer": {"available": True},\n            "habit_architect": {"available": True},\n            "environment_curator": {"available": True},\n            "ritual_master": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Attention Guardian (focus intelligence)\n\nUsage:',
    '- Attention Guardian (focus intelligence)\n- Identity Designer (self-concept intelligence)\n- Habit Architect (behavior design intelligence)\n- Environment Curator (context intelligence)\n- Ritual Master (ceremony intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Attention Guardian", "core.attention_guardian", "get_attention_guardian"),\n    ]',
    '("Attention Guardian", "core.attention_guardian", "get_attention_guardian"),\n        ("Identity Designer", "core.identity_designer", "get_identity_designer"),\n        ("Habit Architect", "core.habit_architect", "get_habit_architect"),\n        ("Environment Curator", "core.environment_curator", "get_environment_curator"),\n        ("Ritual Master", "core.ritual_master", "get_ritual_master"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"attention_guardian",\n            ]',
    '"attention_guardian",\n                "identity_designer", "habit_architect",\n                "environment_curator", "ritual_master",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("attention_guardian", "Attention Guardian"),\n            ]',
    '("attention_guardian", "Attention Guardian"),\n                ("identity_designer", "Identity Designer"),\n                ("habit_architect", "Habit Architect"),\n                ("environment_curator", "Environment Curator"),\n                ("ritual_master", "Ritual Master"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
