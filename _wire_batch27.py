import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"cognitive_load_manager": {"available": True},\n            "overall": "healthy"',
    '"cognitive_load_manager": {"available": True},\n            "stress_resilience_trainer": {"available": True},\n            "emotional_regulation_coach": {"available": True},\n            "mindfulness_trainer": {"available": True},\n            "presence_amplifier": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Cognitive Load Manager (mental bandwidth intelligence)\n\nUsage:',
    '- Cognitive Load Manager (mental bandwidth intelligence)\n- Stress Resilience Trainer (adaptive capacity intelligence)\n- Emotional Regulation Coach (affective intelligence)\n- Mindfulness Trainer (awareness intelligence)\n- Presence Amplifier (embodied awareness intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Cognitive Load Manager", "core.cognitive_load_manager", "get_cognitive_load_manager"),\n    ]',
    '("Cognitive Load Manager", "core.cognitive_load_manager", "get_cognitive_load_manager"),\n        ("Stress Resilience Trainer", "core.stress_resilience_trainer", "get_stress_resilience_trainer"),\n        ("Emotional Regulation Coach", "core.emotional_regulation_coach", "get_emotional_regulation_coach"),\n        ("Mindfulness Trainer", "core.mindfulness_trainer", "get_mindfulness_trainer"),\n        ("Presence Amplifier", "core.presence_amplifier", "get_presence_amplifier"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"cognitive_load_manager",\n            ]',
    '"cognitive_load_manager",\n                "stress_resilience_trainer", "emotional_regulation_coach",\n                "mindfulness_trainer", "presence_amplifier",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("cognitive_load_manager", "Cognitive Load Manager"),\n            ]',
    '("cognitive_load_manager", "Cognitive Load Manager"),\n                ("stress_resilience_trainer", "Stress Resilience Trainer"),\n                ("emotional_regulation_coach", "Emotional Regulation Coach"),\n                ("mindfulness_trainer", "Mindfulness Trainer"),\n                ("presence_amplifier", "Presence Amplifier"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
