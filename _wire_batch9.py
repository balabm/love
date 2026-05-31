import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"productivity_gamifier": {"available": True},\n            "overall": "healthy"',
    '"productivity_gamifier": {"available": True},\n            "environment_optimizer": {"available": True},\n            "weather_suggester": {"available": True},\n            "travel_planner": {"available": True},\n            "gift_idea_generator": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Productivity Gamifier (gamification intelligence)\n\nUsage:',
    '- Productivity Gamifier (gamification intelligence)\n- Environment Optimizer (space intelligence)\n- Weather Suggester (weather intelligence)\n- Travel Planner (travel intelligence)\n- Gift Idea Generator (gift intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Productivity Gamifier", "core.productivity_gamifier", "get_productivity_gamifier"),\n    ]',
    '("Productivity Gamifier", "core.productivity_gamifier", "get_productivity_gamifier"),\n        ("Environment Optimizer", "core.environment_optimizer", "get_environment_optimizer"),\n        ("Weather Suggester", "core.weather_suggester", "get_weather_suggester"),\n        ("Travel Planner", "core.travel_planner", "get_travel_planner"),\n        ("Gift Idea Generator", "core.gift_idea_generator", "get_gift_idea_generator"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"productivity_gamifier",\n            ]',
    '"productivity_gamifier",\n                "environment_optimizer", "weather_suggester",\n                "travel_planner", "gift_idea_generator",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("productivity_gamifier", "Productivity Gamifier"),\n            ]',
    '("productivity_gamifier", "Productivity Gamifier"),\n                ("environment_optimizer", "Environment Optimizer"),\n                ("weather_suggester", "Weather Suggester"),\n                ("travel_planner", "Travel Planner"),\n                ("gift_idea_generator", "Gift Idea Generator"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
