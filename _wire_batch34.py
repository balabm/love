import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"boundary_architect": {"available": True},\n            "overall": "healthy"',
    '"boundary_architect": {"available": True},\n            "leadership_coach": {"available": True},\n            "influence_builder": {"available": True},\n            "delegation_trainer": {"available": True},\n            "vision_keeper": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Boundary Architect (protection intelligence)\n\nUsage:',
    '- Boundary Architect (protection intelligence)\n- Leadership Coach (influence intelligence)\n- Influence Builder (persuasion intelligence)\n- Delegation Trainer (distribution intelligence)\n- Vision Keeper (direction intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Boundary Architect", "core.boundary_architect", "get_boundary_architect"),\n    ]',
    '("Boundary Architect", "core.boundary_architect", "get_boundary_architect"),\n        ("Leadership Coach", "core.leadership_coach", "get_leadership_coach"),\n        ("Influence Builder", "core.influence_builder", "get_influence_builder"),\n        ("Delegation Trainer", "core.delegation_trainer", "get_delegation_trainer"),\n        ("Vision Keeper", "core.vision_keeper", "get_vision_keeper"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"assertiveness_builder", "boundary_architect",\n            ]',
    '"assertiveness_builder", "boundary_architect",\n                "leadership_coach", "influence_builder",\n                "delegation_trainer", "vision_keeper",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("boundary_architect", "Boundary Architect"),\n            ]',
    '("boundary_architect", "Boundary Architect"),\n                ("leadership_coach", "Leadership Coach"),\n                ("influence_builder", "Influence Builder"),\n                ("delegation_trainer", "Delegation Trainer"),\n                ("vision_keeper", "Vision Keeper"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
