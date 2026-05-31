import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"digital_declutterer": {"available": True},\n            "overall": "healthy"',
    '"digital_declutterer": {"available": True},\n            "event_planner": {"available": True},\n            "habit_builder": {"available": True},\n            "morning_routine_designer": {"available": True},\n            "evening_wind_down_coach": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Digital Declutterer (digital wellness intelligence)\n\nUsage:',
    '- Digital Declutterer (digital wellness intelligence)\n- Event Planner (event intelligence)\n- Habit Builder (habit intelligence)\n- Morning Routine Designer (morning intelligence)\n- Evening Wind-Down Coach (sleep intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Digital Declutterer", "core.digital_declutterer", "get_digital_declutterer"),\n    ]',
    '("Digital Declutterer", "core.digital_declutterer", "get_digital_declutterer"),\n        ("Event Planner", "core.event_planner", "get_event_planner"),\n        ("Habit Builder", "core.habit_builder", "get_habit_builder"),\n        ("Morning Routine Designer", "core.morning_routine_designer", "get_morning_routine_designer"),\n        ("Evening Wind-Down Coach", "core.evening_wind_down_coach", "get_evening_wind_down_coach"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"digital_declutterer",\n            ]',
    '"digital_declutterer",\n                "event_planner", "habit_builder",\n                "morning_routine_designer", "evening_wind_down_coach",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("digital_declutterer", "Digital Declutterer"),\n            ]',
    '("digital_declutterer", "Digital Declutterer"),\n                ("event_planner", "Event Planner"),\n                ("habit_builder", "Habit Builder"),\n                ("morning_routine_designer", "Morning Routine Designer"),\n                ("evening_wind_down_coach", "Evening Wind-Down Coach"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
