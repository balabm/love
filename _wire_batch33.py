import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"repair_specialist": {"available": True},\n            "overall": "healthy"',
    '"repair_specialist": {"available": True},\n            "deep_listener": {"available": True},\n            "conflict_navigator": {"available": True},\n            "assertiveness_builder": {"available": True},\n            "boundary_architect": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Repair Specialist (restoration intelligence)\n\nUsage:',
    '- Repair Specialist (restoration intelligence)\n- Deep Listener (presence intelligence)\n- Conflict Navigator (resolution intelligence)\n- Assertiveness Builder (voice intelligence)\n- Boundary Architect (protection intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Repair Specialist", "core.repair_specialist", "get_repair_specialist"),\n    ]',
    '("Repair Specialist", "core.repair_specialist", "get_repair_specialist"),\n        ("Deep Listener", "core.deep_listener", "get_deep_listener"),\n        ("Conflict Navigator", "core.conflict_navigator", "get_conflict_navigator"),\n        ("Assertiveness Builder", "core.assertiveness_builder", "get_assertiveness_builder"),\n        ("Boundary Architect", "core.boundary_architect", "get_boundary_architect"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"trust_architect", "repair_specialist",\n            ]',
    '"trust_architect", "repair_specialist",\n                "deep_listener", "conflict_navigator",\n                "assertiveness_builder", "boundary_architect",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("repair_specialist", "Repair Specialist"),\n            ]',
    '("repair_specialist", "Repair Specialist"),\n                ("deep_listener", "Deep Listener"),\n                ("conflict_navigator", "Conflict Navigator"),\n                ("assertiveness_builder", "Assertiveness Builder"),\n                ("boundary_architect", "Boundary Architect"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
