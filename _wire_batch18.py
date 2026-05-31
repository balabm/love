import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"intuition_trainer": {"available": True},\n            "overall": "healthy"',
    '"intuition_trainer": {"available": True},\n            "resilience_builder": {"available": True},\n            "growth_mindset_coach": {"available": True},\n            "adaptability_trainer": {"available": True},\n            "antifragility_tracker": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Intuition Trainer (inner wisdom intelligence)\n\nUsage:',
    '- Intuition Trainer (inner wisdom intelligence)\n- Resilience Builder (bounce-back intelligence)\n- Growth Mindset Coach (belief intelligence)\n- Adaptability Trainer (change intelligence)\n- Antifragility Tracker (stress-to-strength intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Intuition Trainer", "core.intuition_trainer", "get_intuition_trainer"),\n    ]',
    '("Intuition Trainer", "core.intuition_trainer", "get_intuition_trainer"),\n        ("Resilience Builder", "core.resilience_builder", "get_resilience_builder"),\n        ("Growth Mindset Coach", "core.growth_mindset_coach", "get_growth_mindset_coach"),\n        ("Adaptability Trainer", "core.adaptability_trainer", "get_adaptability_trainer"),\n        ("Antifragility Tracker", "core.antifragility_tracker", "get_antifragility_tracker"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"intuition_trainer",\n            ]',
    '"intuition_trainer",\n                "resilience_builder", "growth_mindset_coach",\n                "adaptability_trainer", "antifragility_tracker",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("intuition_trainer", "Intuition Trainer"),\n            ]',
    '("intuition_trainer", "Intuition Trainer"),\n                ("resilience_builder", "Resilience Builder"),\n                ("growth_mindset_coach", "Growth Mindset Coach"),\n                ("adaptability_trainer", "Adaptability Trainer"),\n                ("antifragility_tracker", "Antifragility Tracker"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
