import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"meaning_amplifier": {"available": True},\n            "overall": "healthy"',
    '"meaning_amplifier": {"available": True},\n            "courage_coach": {"available": True},\n            "risk_intelligence_trainer": {"available": True},\n            "vulnerability_builder": {"available": True},\n            "authenticity_amplifier": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Meaning Amplifier (significance intelligence)\n\nUsage:',
    '- Meaning Amplifier (significance intelligence)\n- Courage Coach (brave action intelligence)\n- Risk Intelligence Trainer (calculated risk intelligence)\n- Vulnerability Builder (openness intelligence)\n- Authenticity Amplifier (true self intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Meaning Amplifier", "core.meaning_amplifier", "get_meaning_amplifier"),\n    ]',
    '("Meaning Amplifier", "core.meaning_amplifier", "get_meaning_amplifier"),\n        ("Courage Coach", "core.courage_coach", "get_courage_coach"),\n        ("Risk Intelligence Trainer", "core.risk_intelligence_trainer", "get_risk_intelligence_trainer"),\n        ("Vulnerability Builder", "core.vulnerability_builder", "get_vulnerability_builder"),\n        ("Authenticity Amplifier", "core.authenticity_amplifier", "get_authenticity_amplifier"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"meaning_amplifier",\n            ]',
    '"meaning_amplifier",\n                "courage_coach", "risk_intelligence_trainer",\n                "vulnerability_builder", "authenticity_amplifier",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("meaning_amplifier", "Meaning Amplifier"),\n            ]',
    '("meaning_amplifier", "Meaning Amplifier"),\n                ("courage_coach", "Courage Coach"),\n                ("risk_intelligence_trainer", "Risk Intelligence Trainer"),\n                ("vulnerability_builder", "Vulnerability Builder"),\n                ("authenticity_amplifier", "Authenticity Amplifier"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
