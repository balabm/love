import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"regenerative_living_guide": {"available": True},\n            "overall": "healthy"',
    '"regenerative_living_guide": {"available": True},\n            "spiritual_practice_coach": {"available": True},\n            "transcendence_guide": {"available": True},\n            "sacred_ritual_designer": {"available": True},\n            "contemplation_keeper": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Regenerative Living Guide (restoration intelligence)\n\nUsage:',
    '- Regenerative Living Guide (restoration intelligence)\n- Spiritual Practice Coach (sacred intelligence)\n- Transcendence Guide (elevation intelligence)\n- Sacred Ritual Designer (ceremony intelligence)\n- Contemplation Keeper (depth intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Regenerative Living Guide", "core.regenerative_living_guide", "get_regenerative_living_guide"),\n    ]',
    '("Regenerative Living Guide", "core.regenerative_living_guide", "get_regenerative_living_guide"),\n        ("Spiritual Practice Coach", "core.spiritual_practice_coach", "get_spiritual_practice_coach"),\n        ("Transcendence Guide", "core.transcendence_guide", "get_transcendence_guide"),\n        ("Sacred Ritual Designer", "core.sacred_ritual_designer", "get_sacred_ritual_designer"),\n        ("Contemplation Keeper", "core.contemplation_keeper", "get_contemplation_keeper"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"eco_footprint_tracker", "regenerative_living_guide",\n            ]',
    '"eco_footprint_tracker", "regenerative_living_guide",\n                "spiritual_practice_coach", "transcendence_guide",\n                "sacred_ritual_designer", "contemplation_keeper",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("regenerative_living_guide", "Regenerative Living Guide"),\n            ]',
    '("regenerative_living_guide", "Regenerative Living Guide"),\n                ("spiritual_practice_coach", "Spiritual Practice Coach"),\n                ("transcendence_guide", "Transcendence Guide"),\n                ("sacred_ritual_designer", "Sacred Ritual Designer"),\n                ("contemplation_keeper", "Contemplation Keeper"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
