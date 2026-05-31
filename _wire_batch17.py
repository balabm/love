import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"death_awareness_coach": {"available": True},\n            "overall": "healthy"',
    '"death_awareness_coach": {"available": True},\n            "flow_state_coach": {"available": True},\n            "savoring_trainer": {"available": True},\n            "presence_detector": {"available": True},\n            "intuition_trainer": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Death Awareness Coach (mortality intelligence)\n\nUsage:',
    '- Death Awareness Coach (mortality intelligence)\n- Flow State Coach (optimal experience intelligence)\n- Savoring Trainer (positive experience amplification intelligence)\n- Presence Detector (attention intelligence)\n- Intuition Trainer (inner wisdom intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Death Awareness Coach", "core.death_awareness_coach", "get_death_awareness_coach"),\n    ]',
    '("Death Awareness Coach", "core.death_awareness_coach", "get_death_awareness_coach"),\n        ("Flow State Coach", "core.flow_state_coach", "get_flow_state_coach"),\n        ("Savoring Trainer", "core.savoring_trainer", "get_savoring_trainer"),\n        ("Presence Detector", "core.presence_detector", "get_presence_detector"),\n        ("Intuition Trainer", "core.intuition_trainer", "get_intuition_trainer"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"death_awareness_coach",\n            ]',
    '"death_awareness_coach",\n                "flow_state_coach", "savoring_trainer",\n                "presence_detector", "intuition_trainer",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("death_awareness_coach", "Death Awareness Coach"),\n            ]',
    '("death_awareness_coach", "Death Awareness Coach"),\n                ("flow_state_coach", "Flow State Coach"),\n                ("savoring_trainer", "Savoring Trainer"),\n                ("presence_detector", "Presence Detector"),\n                ("intuition_trainer", "Intuition Trainer"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
