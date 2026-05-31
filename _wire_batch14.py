import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"active_listening_coach": {"available": True},\n            "overall": "healthy"',
    '"active_listening_coach": {"available": True},\n            "self_compassion_coach": {"available": True},\n            "forgiveness_tracker": {"available": True},\n            "vulnerability_builder": {"available": True},\n            "trust_builder": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Active Listening Coach (connection intelligence)\n\nUsage:',
    '- Active Listening Coach (connection intelligence)\n- Self-Compassion Coach (inner kindness intelligence)\n- Forgiveness Tracker (emotional freedom intelligence)\n- Vulnerability Builder (emotional courage intelligence)\n- Trust Builder (relational intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Active Listening Coach", "core.active_listening_coach", "get_active_listening_coach"),\n    ]',
    '("Active Listening Coach", "core.active_listening_coach", "get_active_listening_coach"),\n        ("Self-Compassion Coach", "core.self_compassion_coach", "get_self_compassion_coach"),\n        ("Forgiveness Tracker", "core.forgiveness_tracker", "get_forgiveness_tracker"),\n        ("Vulnerability Builder", "core.vulnerability_builder", "get_vulnerability_builder"),\n        ("Trust Builder", "core.trust_builder", "get_trust_builder"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"active_listening_coach",\n            ]',
    '"active_listening_coach",\n                "self_compassion_coach", "forgiveness_tracker",\n                "vulnerability_builder", "trust_builder",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("active_listening_coach", "Active Listening Coach"),\n            ]',
    '("active_listening_coach", "Active Listening Coach"),\n                ("self_compassion_coach", "Self-Compassion Coach"),\n                ("forgiveness_tracker", "Forgiveness Tracker"),\n                ("vulnerability_builder", "Vulnerability Builder"),\n                ("trust_builder", "Trust Builder"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
