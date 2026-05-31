import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"antifragility_tracker": {"available": True},\n            "overall": "healthy"',
    '"antifragility_tracker": {"available": True},\n            "discipline_trainer": {"available": True},\n            "consistency_coach": {"available": True},\n            "accountability_partner": {"available": True},\n            "progress_celebrator": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Antifragility Tracker (stress-to-strength intelligence)\n\nUsage:',
    '- Antifragility Tracker (stress-to-strength intelligence)\n- Discipline Trainer (self-regulation intelligence)\n- Consistency Coach (steady-state intelligence)\n- Accountability Partner (external support intelligence)\n- Progress Celebrator (recognition intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Antifragility Tracker", "core.antifragility_tracker", "get_antifragility_tracker"),\n    ]',
    '("Antifragility Tracker", "core.antifragility_tracker", "get_antifragility_tracker"),\n        ("Discipline Trainer", "core.discipline_trainer", "get_discipline_trainer"),\n        ("Consistency Coach", "core.consistency_coach", "get_consistency_coach"),\n        ("Accountability Partner", "core.accountability_partner", "get_accountability_partner"),\n        ("Progress Celebrator", "core.progress_celebrator", "get_progress_celebrator"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"antifragility_tracker",\n            ]',
    '"antifragility_tracker",\n                "discipline_trainer", "consistency_coach",\n                "accountability_partner", "progress_celebrator",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("antifragility_tracker", "Antifragility Tracker"),\n            ]',
    '("antifragility_tracker", "Antifragility Tracker"),\n                ("discipline_trainer", "Discipline Trainer"),\n                ("consistency_coach", "Consistency Coach"),\n                ("accountability_partner", "Accountability Partner"),\n                ("progress_celebrator", "Progress Celebrator"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
