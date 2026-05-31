import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"wisdom_distiller": {"available": True},\n            "overall": "healthy"',
    '"wisdom_distiller": {"available": True},\n            "purpose_clarity_engine": {"available": True},\n            "legacy_builder": {"available": True},\n            "impact_maximizer": {"available": True},\n            "meaning_amplifier": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Wisdom Distiller (deep understanding intelligence)\n\nUsage:',
    '- Wisdom Distiller (deep understanding intelligence)\n- Purpose Clarity Engine (direction intelligence)\n- Legacy Builder (long-term impact intelligence)\n- Impact Maximizer (leverage intelligence)\n- Meaning Amplifier (significance intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Wisdom Distiller", "core.wisdom_distiller", "get_wisdom_distiller"),\n    ]',
    '("Wisdom Distiller", "core.wisdom_distiller", "get_wisdom_distiller"),\n        ("Purpose Clarity Engine", "core.purpose_clarity_engine", "get_purpose_clarity_engine"),\n        ("Legacy Builder", "core.legacy_builder", "get_legacy_builder"),\n        ("Impact Maximizer", "core.impact_maximizer", "get_impact_maximizer"),\n        ("Meaning Amplifier", "core.meaning_amplifier", "get_meaning_amplifier"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"wisdom_distiller",\n            ]',
    '"wisdom_distiller",\n                "purpose_clarity_engine", "legacy_builder",\n                "impact_maximizer", "meaning_amplifier",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("wisdom_distiller", "Wisdom Distiller"),\n            ]',
    '("wisdom_distiller", "Wisdom Distiller"),\n                ("purpose_clarity_engine", "Purpose Clarity Engine"),\n                ("legacy_builder", "Legacy Builder"),\n                ("impact_maximizer", "Impact Maximizer"),\n                ("meaning_amplifier", "Meaning Amplifier"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
