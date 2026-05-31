import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"evening_wind_down_coach": {"available": True},\n            "overall": "healthy"',
    '"evening_wind_down_coach": {"available": True},\n            "conflict_resolution_coach": {"available": True},\n            "boundaries_coach": {"available": True},\n            "assertiveness_trainer": {"available": True},\n            "active_listening_coach": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Evening Wind-Down Coach (sleep intelligence)\n\nUsage:',
    '- Evening Wind-Down Coach (sleep intelligence)\n- Conflict Resolution Coach (relationship intelligence)\n- Boundaries Coach (self-respect intelligence)\n- Assertiveness Trainer (communication intelligence)\n- Active Listening Coach (connection intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Evening Wind-Down Coach", "core.evening_wind_down_coach", "get_evening_wind_down_coach"),\n    ]',
    '("Evening Wind-Down Coach", "core.evening_wind_down_coach", "get_evening_wind_down_coach"),\n        ("Conflict Resolution Coach", "core.conflict_resolution_coach", "get_conflict_resolution_coach"),\n        ("Boundaries Coach", "core.boundaries_coach", "get_boundaries_coach"),\n        ("Assertiveness Trainer", "core.assertiveness_trainer", "get_assertiveness_trainer"),\n        ("Active Listening Coach", "core.active_listening_coach", "get_active_listening_coach"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"evening_wind_down_coach",\n            ]',
    '"evening_wind_down_coach",\n                "conflict_resolution_coach", "boundaries_coach",\n                "assertiveness_trainer", "active_listening_coach",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("evening_wind_down_coach", "Evening Wind-Down Coach"),\n            ]',
    '("evening_wind_down_coach", "Evening Wind-Down Coach"),\n                ("conflict_resolution_coach", "Conflict Resolution Coach"),\n                ("boundaries_coach", "Boundaries Coach"),\n                ("assertiveness_trainer", "Assertiveness Trainer"),\n                ("active_listening_coach", "Active Listening Coach"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
