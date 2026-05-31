import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"gratitude_amplifier": {"available": True},\n            "overall": "healthy"',
    '"gratitude_amplifier": {"available": True},\n            "deep_work_enabler": {"available": True},\n            "recovery_optimizer": {"available": True},\n            "peak_performance_tracker": {"available": True},\n            "mindful_productivity_coach": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Gratitude Amplifier (appreciation intelligence)\n\nUsage:',
    '- Gratitude Amplifier (appreciation intelligence)\n- Deep Work Enabler (cognitive excellence intelligence)\n- Recovery Optimizer (restoration intelligence)\n- Peak Performance Tracker (excellence intelligence)\n- Mindful Productivity Coach (conscious efficiency intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Gratitude Amplifier", "core.gratitude_amplifier", "get_gratitude_amplifier"),\n    ]',
    '("Gratitude Amplifier", "core.gratitude_amplifier", "get_gratitude_amplifier"),\n        ("Deep Work Enabler", "core.deep_work_enabler", "get_deep_work_enabler"),\n        ("Recovery Optimizer", "core.recovery_optimizer", "get_recovery_optimizer"),\n        ("Peak Performance Tracker", "core.peak_performance_tracker", "get_peak_performance_tracker"),\n        ("Mindful Productivity Coach", "core.mindful_productivity_coach", "get_mindful_productivity_coach"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"gratitude_amplifier",\n            ]',
    '"gratitude_amplifier",\n                "deep_work_enabler", "recovery_optimizer",\n                "peak_performance_tracker", "mindful_productivity_coach",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("gratitude_amplifier", "Gratitude Amplifier"),\n            ]',
    '("gratitude_amplifier", "Gratitude Amplifier"),\n                ("deep_work_enabler", "Deep Work Enabler"),\n                ("recovery_optimizer", "Recovery Optimizer"),\n                ("peak_performance_tracker", "Peak Performance Tracker"),\n                ("mindful_productivity_coach", "Mindful Productivity Coach"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
