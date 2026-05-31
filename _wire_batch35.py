import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"vision_keeper": {"available": True},\n            "overall": "healthy"',
    '"vision_keeper": {"available": True},\n            "investment_strategist": {"available": True},\n            "wealth_builder": {"available": True},\n            "income_diversifier": {"available": True},\n            "financial_independence_tracker": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Vision Keeper (direction intelligence)\n\nUsage:',
    '- Vision Keeper (direction intelligence)\n- Investment Strategist (capital intelligence)\n- Wealth Builder (accumulation intelligence)\n- Income Diversifier (stream intelligence)\n- Financial Independence Tracker (freedom intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Vision Keeper", "core.vision_keeper", "get_vision_keeper"),\n    ]',
    '("Vision Keeper", "core.vision_keeper", "get_vision_keeper"),\n        ("Investment Strategist", "core.investment_strategist", "get_investment_strategist"),\n        ("Wealth Builder", "core.wealth_builder", "get_wealth_builder"),\n        ("Income Diversifier", "core.income_diversifier", "get_income_diversifier"),\n        ("Financial Independence Tracker", "core.financial_independence_tracker", "get_financial_independence_tracker"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"delegation_trainer", "vision_keeper",\n            ]',
    '"delegation_trainer", "vision_keeper",\n                "investment_strategist", "wealth_builder",\n                "income_diversifier", "financial_independence_tracker",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("vision_keeper", "Vision Keeper"),\n            ]',
    '("vision_keeper", "Vision Keeper"),\n                ("investment_strategist", "Investment Strategist"),\n                ("wealth_builder", "Wealth Builder"),\n                ("income_diversifier", "Income Diversifier"),\n                ("financial_independence_tracker", "Financial Independence Tracker"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
