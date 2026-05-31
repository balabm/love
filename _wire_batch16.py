import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"wonder_tracker": {"available": True},\n            "overall": "healthy"',
    '"wonder_tracker": {"available": True},\n            "meaning_mapper": {"available": True},\n            "purpose_navigator": {"available": True},\n            "legacy_builder": {"available": True},\n            "death_awareness_coach": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Wonder Tracker (awe intelligence)\n\nUsage:',
    '- Wonder Tracker (awe intelligence)\n- Meaning Mapper (significance intelligence)\n- Purpose Navigator (direction intelligence)\n- Legacy Builder (long-term impact intelligence)\n- Death Awareness Coach (mortality intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Wonder Tracker", "core.wonder_tracker", "get_wonder_tracker"),\n    ]',
    '("Wonder Tracker", "core.wonder_tracker", "get_wonder_tracker"),\n        ("Meaning Mapper", "core.meaning_mapper", "get_meaning_mapper"),\n        ("Purpose Navigator", "core.purpose_navigator", "get_purpose_navigator"),\n        ("Legacy Builder", "core.legacy_builder", "get_legacy_builder"),\n        ("Death Awareness Coach", "core.death_awareness_coach", "get_death_awareness_coach"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"wonder_tracker",\n            ]',
    '"wonder_tracker",\n                "meaning_mapper", "purpose_navigator",\n                "legacy_builder", "death_awareness_coach",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("wonder_tracker", "Wonder Tracker"),\n            ]',
    '("wonder_tracker", "Wonder Tracker"),\n                ("meaning_mapper", "Meaning Mapper"),\n                ("purpose_navigator", "Purpose Navigator"),\n                ("legacy_builder", "Legacy Builder"),\n                ("death_awareness_coach", "Death Awareness Coach"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
