import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"progress_celebrator": {"available": True},\n            "overall": "healthy"',
    '"progress_celebrator": {"available": True},\n            "energy_protector": {"available": True},\n            "boundary_enforcer": {"available": True},\n            "time_sovereign": {"available": True},\n            "attention_guardian": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Progress Celebrator (recognition intelligence)\n\nUsage:',
    '- Progress Celebrator (recognition intelligence)\n- Energy Protector (vitality intelligence)\n- Boundary Enforcer (limit intelligence)\n- Time Sovereign (temporal autonomy intelligence)\n- Attention Guardian (focus intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Progress Celebrator", "core.progress_celebrator", "get_progress_celebrator"),\n    ]',
    '("Progress Celebrator", "core.progress_celebrator", "get_progress_celebrator"),\n        ("Energy Protector", "core.energy_protector", "get_energy_protector"),\n        ("Boundary Enforcer", "core.boundary_enforcer", "get_boundary_enforcer"),\n        ("Time Sovereign", "core.time_sovereign", "get_time_sovereign"),\n        ("Attention Guardian", "core.attention_guardian", "get_attention_guardian"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"progress_celebrator",\n            ]',
    '"progress_celebrator",\n                "energy_protector", "boundary_enforcer",\n                "time_sovereign", "attention_guardian",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("progress_celebrator", "Progress Celebrator"),\n            ]',
    '("progress_celebrator", "Progress Celebrator"),\n                ("energy_protector", "Energy Protector"),\n                ("boundary_enforcer", "Boundary Enforcer"),\n                ("time_sovereign", "Time Sovereign"),\n                ("attention_guardian", "Attention Guardian"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
