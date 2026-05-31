import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"spontaneity_generator": {"available": True},\n            "overall": "healthy"',
    '"spontaneity_generator": {"available": True},\n            "forgiveness_coach": {"available": True},\n            "reconciliation_builder": {"available": True},\n            "trust_architect": {"available": True},\n            "repair_specialist": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Spontaneity Generator (unexpected joy intelligence)\n\nUsage:',
    '- Spontaneity Generator (unexpected joy intelligence)\n- Forgiveness Coach (release intelligence)\n- Reconciliation Builder (repair intelligence)\n- Trust Architect (reliability intelligence)\n- Repair Specialist (restoration intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Spontaneity Generator", "core.spontaneity_generator", "get_spontaneity_generator"),\n    ]',
    '("Spontaneity Generator", "core.spontaneity_generator", "get_spontaneity_generator"),\n        ("Forgiveness Coach", "core.forgiveness_coach", "get_forgiveness_coach"),\n        ("Reconciliation Builder", "core.reconciliation_builder", "get_reconciliation_builder"),\n        ("Trust Architect", "core.trust_architect", "get_trust_architect"),\n        ("Repair Specialist", "core.repair_specialist", "get_repair_specialist"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"celebration_architect", "spontaneity_generator",\n            ]',
    '"celebration_architect", "spontaneity_generator",\n                "forgiveness_coach", "reconciliation_builder",\n                "trust_architect", "repair_specialist",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("spontaneity_generator", "Spontaneity Generator"),\n            ]',
    '("spontaneity_generator", "Spontaneity Generator"),\n                ("forgiveness_coach", "Forgiveness Coach"),\n                ("reconciliation_builder", "Reconciliation Builder"),\n                ("trust_architect", "Trust Architect"),\n                ("repair_specialist", "Repair Specialist"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
