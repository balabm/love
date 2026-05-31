import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"health_integrator": {"available": True},\n            "overall": "healthy"',
    '"health_integrator": {"available": True},\n            "digital_minimalism_coach": {"available": True},\n            "focus_ritual_designer": {"available": True},\n            "attention_recovery_specialist": {"available": True},\n            "cognitive_load_manager": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Health Integrator (holistic health intelligence)\n\nUsage:',
    '- Health Integrator (holistic health intelligence)\n- Digital Minimalism Coach (intentional tech intelligence)\n- Focus Ritual Designer (ritual intelligence)\n- Attention Recovery Specialist (attention restoration intelligence)\n- Cognitive Load Manager (mental bandwidth intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Health Integrator", "core.health_integrator", "get_health_integrator"),\n    ]',
    '("Health Integrator", "core.health_integrator", "get_health_integrator"),\n        ("Digital Minimalism Coach", "core.digital_minimalism_coach", "get_digital_minimalism_coach"),\n        ("Focus Ritual Designer", "core.focus_ritual_designer", "get_focus_ritual_designer"),\n        ("Attention Recovery Specialist", "core.attention_recovery_specialist", "get_attention_recovery_specialist"),\n        ("Cognitive Load Manager", "core.cognitive_load_manager", "get_cognitive_load_manager"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"health_integrator",\n            ]',
    '"health_integrator",\n                "digital_minimalism_coach", "focus_ritual_designer",\n                "attention_recovery_specialist", "cognitive_load_manager",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("health_integrator", "Health Integrator"),\n            ]',
    '("health_integrator", "Health Integrator"),\n                ("digital_minimalism_coach", "Digital Minimalism Coach"),\n                ("focus_ritual_designer", "Focus Ritual Designer"),\n                ("attention_recovery_specialist", "Attention Recovery Specialist"),\n                ("cognitive_load_manager", "Cognitive Load Manager"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
