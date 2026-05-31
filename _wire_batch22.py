import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"ritual_master": {"available": True},\n            "overall": "healthy"',
    '"ritual_master": {"available": True},\n            "values_explorer": {"available": True},\n            "belief_examiner": {"available": True},\n            "shadow_integrator": {"available": True},\n            "inner_critic_manager": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Ritual Master (ceremony intelligence)\n\nUsage:',
    '- Ritual Master (ceremony intelligence)\n- Values Explorer (axiology intelligence)\n- Belief Examiner (epistemology intelligence)\n- Shadow Integrator (unconscious intelligence)\n- Inner Critic Manager (self-talk intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Ritual Master", "core.ritual_master", "get_ritual_master"),\n    ]',
    '("Ritual Master", "core.ritual_master", "get_ritual_master"),\n        ("Values Explorer", "core.values_explorer", "get_values_explorer"),\n        ("Belief Examiner", "core.belief_examiner", "get_belief_examiner"),\n        ("Shadow Integrator", "core.shadow_integrator", "get_shadow_integrator"),\n        ("Inner Critic Manager", "core.inner_critic_manager", "get_inner_critic_manager"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"ritual_master",\n            ]',
    '"ritual_master",\n                "values_explorer", "belief_examiner",\n                "shadow_integrator", "inner_critic_manager",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("ritual_master", "Ritual Master"),\n            ]',
    '("ritual_master", "Ritual Master"),\n                ("values_explorer", "Values Explorer"),\n                ("belief_examiner", "Belief Examiner"),\n                ("shadow_integrator", "Shadow Integrator"),\n                ("inner_critic_manager", "Inner Critic Manager"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
