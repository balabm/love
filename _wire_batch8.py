import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"stress_response_coach": {"available": True},\n            "overall": "healthy"',
    '"stress_response_coach": {"available": True},\n            "communication_analyzer": {"available": True},\n            "goal_progress_visualizer": {"available": True},\n            "life_balance_wheel": {"available": True},\n            "productivity_gamifier": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Stress Response Coach (resilience intelligence)\n\nUsage:',
    '- Stress Response Coach (resilience intelligence)\n- Communication Analyzer (communication intelligence)\n- Goal Progress Visualizer (goal intelligence)\n- Life Balance Wheel (life intelligence)\n- Productivity Gamifier (gamification intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Stress Response Coach", "core.stress_response_coach", "get_stress_response_coach"),\n    ]',
    '("Stress Response Coach", "core.stress_response_coach", "get_stress_response_coach"),\n        ("Communication Analyzer", "core.communication_analyzer", "get_communication_analyzer"),\n        ("Goal Progress Visualizer", "core.goal_progress_visualizer", "get_goal_progress_visualizer"),\n        ("Life Balance Wheel", "core.life_balance_wheel", "get_life_balance_wheel"),\n        ("Productivity Gamifier", "core.productivity_gamifier", "get_productivity_gamifier"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"stress_response_coach",\n            ]',
    '"stress_response_coach",\n                "communication_analyzer", "goal_progress_visualizer",\n                "life_balance_wheel", "productivity_gamifier",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("stress_response_coach", "Stress Response Coach"),\n            ]',
    '("stress_response_coach", "Stress Response Coach"),\n                ("communication_analyzer", "Communication Analyzer"),\n                ("goal_progress_visualizer", "Goal Progress Visualizer"),\n                ("life_balance_wheel", "Life Balance Wheel"),\n                ("productivity_gamifier", "Productivity Gamifier"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
