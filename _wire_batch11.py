import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"skill_gap_analyzer": {"available": True},\n            "overall": "healthy"',
    '"skill_gap_analyzer": {"available": True},\n            "document_organizer": {"available": True},\n            "password_health_checker": {"available": True},\n            "subscription_manager": {"available": True},\n            "digital_declutterer": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Skill Gap Analyzer (capability intelligence)\n\nUsage:',
    '- Skill Gap Analyzer (capability intelligence)\n- Document Organizer (document intelligence)\n- Password Health Checker (security intelligence)\n- Subscription Manager (finance intelligence)\n- Digital Declutterer (digital wellness intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Skill Gap Analyzer", "core.skill_gap_analyzer", "get_skill_gap_analyzer"),\n    ]',
    '("Skill Gap Analyzer", "core.skill_gap_analyzer", "get_skill_gap_analyzer"),\n        ("Document Organizer", "core.document_organizer", "get_document_organizer"),\n        ("Password Health Checker", "core.password_health_checker", "get_password_health_checker"),\n        ("Subscription Manager", "core.subscription_manager", "get_subscription_manager"),\n        ("Digital Declutterer", "core.digital_declutterer", "get_digital_declutterer"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"skill_gap_analyzer",\n            ]',
    '"skill_gap_analyzer",\n                "document_organizer", "password_health_checker",\n                "subscription_manager", "digital_declutterer",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("skill_gap_analyzer", "Skill Gap Analyzer"),\n            ]',
    '("skill_gap_analyzer", "Skill Gap Analyzer"),\n                ("document_organizer", "Document Organizer"),\n                ("password_health_checker", "Password Health Checker"),\n                ("subscription_manager", "Subscription Manager"),\n                ("digital_declutterer", "Digital Declutterer"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
