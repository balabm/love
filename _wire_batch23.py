import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"inner_critic_manager": {"available": True},\n            "overall": "healthy"',
    '"inner_critic_manager": {"available": True},\n            "emotional_intelligence_trainer": {"available": True},\n            "empathy_builder": {"available": True},\n            "compassion_generator": {"available": True},\n            "gratitude_amplifier": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Inner Critic Manager (self-talk intelligence)\n\nUsage:',
    '- Inner Critic Manager (self-talk intelligence)\n- Emotional Intelligence Trainer (EQ intelligence)\n- Empathy Builder (perspective intelligence)\n- Compassion Generator (loving-kindness intelligence)\n- Gratitude Amplifier (appreciation intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Inner Critic Manager", "core.inner_critic_manager", "get_inner_critic_manager"),\n    ]',
    '("Inner Critic Manager", "core.inner_critic_manager", "get_inner_critic_manager"),\n        ("Emotional Intelligence Trainer", "core.emotional_intelligence_trainer", "get_emotional_intelligence_trainer"),\n        ("Empathy Builder", "core.empathy_builder", "get_empathy_builder"),\n        ("Compassion Generator", "core.compassion_generator", "get_compassion_generator"),\n        ("Gratitude Amplifier", "core.gratitude_amplifier", "get_gratitude_amplifier"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"inner_critic_manager",\n            ]',
    '"inner_critic_manager",\n                "emotional_intelligence_trainer", "empathy_builder",\n                "compassion_generator", "gratitude_amplifier",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("inner_critic_manager", "Inner Critic Manager"),\n            ]',
    '("inner_critic_manager", "Inner Critic Manager"),\n                ("emotional_intelligence_trainer", "Emotional Intelligence Trainer"),\n                ("empathy_builder", "Empathy Builder"),\n                ("compassion_generator", "Compassion Generator"),\n                ("gratitude_amplifier", "Gratitude Amplifier"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
