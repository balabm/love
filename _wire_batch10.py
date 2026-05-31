import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"gift_idea_generator": {"available": True},\n            "overall": "healthy"',
    '"gift_idea_generator": {"available": True},\n            "emergency_preparedness_tracker": {"available": True},\n            "home_maintenance_scheduler": {"available": True},\n            "career_path_mapper": {"available": True},\n            "skill_gap_analyzer": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Gift Idea Generator (gift intelligence)\n\nUsage:',
    '- Gift Idea Generator (gift intelligence)\n- Emergency Preparedness Tracker (safety intelligence)\n- Home Maintenance Scheduler (home intelligence)\n- Career Path Mapper (career intelligence)\n- Skill Gap Analyzer (capability intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Gift Idea Generator", "core.gift_idea_generator", "get_gift_idea_generator"),\n    ]',
    '("Gift Idea Generator", "core.gift_idea_generator", "get_gift_idea_generator"),\n        ("Emergency Preparedness Tracker", "core.emergency_preparedness_tracker", "get_emergency_preparedness_tracker"),\n        ("Home Maintenance Scheduler", "core.home_maintenance_scheduler", "get_home_maintenance_scheduler"),\n        ("Career Path Mapper", "core.career_path_mapper", "get_career_path_mapper"),\n        ("Skill Gap Analyzer", "core.skill_gap_analyzer", "get_skill_gap_analyzer"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"gift_idea_generator",\n            ]',
    '"gift_idea_generator",\n                "emergency_preparedness_tracker", "home_maintenance_scheduler",\n                "career_path_mapper", "skill_gap_analyzer",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("gift_idea_generator", "Gift Idea Generator"),\n            ]',
    '("gift_idea_generator", "Gift Idea Generator"),\n                ("emergency_preparedness_tracker", "Emergency Preparedness Tracker"),\n                ("home_maintenance_scheduler", "Home Maintenance Scheduler"),\n                ("career_path_mapper", "Career Path Mapper"),\n                ("skill_gap_analyzer", "Skill Gap Analyzer"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
