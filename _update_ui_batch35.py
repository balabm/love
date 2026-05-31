import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '"vision_keeper",'
new_filter = '"vision_keeper",\n                "investment_strategist", "wealth_builder",\n                "income_diversifier", "financial_independence_tracker",'

if old_filter in content:
    content = content.replace(old_filter, new_filter)
    with open('ui/src/components/SentinelPanel.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated SentinelPanel.jsx')
else:
    print('Could not find SentinelPanel.jsx filter list')

# 2. Update IntelligenceDashboard.jsx
with open('ui/src/components/IntelligenceDashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_modules = '{ name: "vision_keeper", stats: modernStats.evolution_health?.vision_keeper },\n  ].filter(m => m.stats);'

new_modules = '{ name: "vision_keeper", stats: modernStats.evolution_health?.vision_keeper },\n    { name: "investment_strategist", stats: modernStats.evolution_health?.investment_strategist },\n    { name: "wealth_builder", stats: modernStats.evolution_health?.wealth_builder },\n    { name: "income_diversifier", stats: modernStats.evolution_health?.income_diversifier },\n    { name: "financial_independence_tracker", stats: modernStats.evolution_health?.financial_independence_tracker },\n  ].filter(m => m.stats);'

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
