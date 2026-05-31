import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"financial_independence_tracker": {"available": True},\n            "overall": "healthy"',
    '"financial_independence_tracker": {"available": True},\n            "sustainability_coach": {"available": True},\n            "nature_connector": {"available": True},\n            "eco_footprint_tracker": {"available": True},\n            "regenerative_living_guide": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Financial Independence Tracker (freedom intelligence)\n\nUsage:',
    '- Financial Independence Tracker (freedom intelligence)\n- Sustainability Coach (stewardship intelligence)\n- Nature Connector (biophilia intelligence)\n- Eco Footprint Tracker (impact intelligence)\n- Regenerative Living Guide (restoration intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Financial Independence Tracker", "core.financial_independence_tracker", "get_financial_independence_tracker"),\n    ]',
    '("Financial Independence Tracker", "core.financial_independence_tracker", "get_financial_independence_tracker"),\n        ("Sustainability Coach", "core.sustainability_coach", "get_sustainability_coach"),\n        ("Nature Connector", "core.nature_connector", "get_nature_connector"),\n        ("Eco Footprint Tracker", "core.eco_footprint_tracker", "get_eco_footprint_tracker"),\n        ("Regenerative Living Guide", "core.regenerative_living_guide", "get_regenerative_living_guide"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"income_diversifier", "financial_independence_tracker",\n            ]',
    '"income_diversifier", "financial_independence_tracker",\n                "sustainability_coach", "nature_connector",\n                "eco_footprint_tracker", "regenerative_living_guide",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("financial_independence_tracker", "Financial Independence Tracker"),\n            ]',
    '("financial_independence_tracker", "Financial Independence Tracker"),\n                ("sustainability_coach", "Sustainability Coach"),\n                ("nature_connector", "Nature Connector"),\n                ("eco_footprint_tracker", "Eco Footprint Tracker"),\n                ("regenerative_living_guide", "Regenerative Living Guide"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
