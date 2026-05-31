import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"meditation_coach": {"available": True},\n            "overall": "healthy"',
    '"meditation_coach": {"available": True},\n            "reading_tracker": {"available": True},\n            "writing_coach": {"available": True},\n            "creativity_booster": {"available": True},\n            "stress_response_coach": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Meditation Coach (mindfulness intelligence)\n\nUsage:',
    '- Meditation Coach (mindfulness intelligence)\n- Reading Tracker (knowledge intelligence)\n- Writing Coach (writing intelligence)\n- Creativity Booster (creative intelligence)\n- Stress Response Coach (resilience intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Meditation Coach", "core.meditation_coach", "get_meditation_coach"),\n    ]',
    '("Meditation Coach", "core.meditation_coach", "get_meditation_coach"),\n        ("Reading Tracker", "core.reading_tracker", "get_reading_tracker"),\n        ("Writing Coach", "core.writing_coach", "get_writing_coach"),\n        ("Creativity Booster", "core.creativity_booster", "get_creativity_booster"),\n        ("Stress Response Coach", "core.stress_response_coach", "get_stress_response_coach"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"meditation_coach",\n            ]',
    '"meditation_coach",\n                "reading_tracker", "writing_coach",\n                "creativity_booster", "stress_response_coach",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("meditation_coach", "Meditation Coach"),\n            ]',
    '("meditation_coach", "Meditation Coach"),\n                ("reading_tracker", "Reading Tracker"),\n                ("writing_coach", "Writing Coach"),\n                ("creativity_booster", "Creativity Booster"),\n                ("stress_response_coach", "Stress Response Coach"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
