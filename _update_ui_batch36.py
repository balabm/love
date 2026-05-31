import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '"financial_independence_tracker",'
new_filter = '"financial_independence_tracker",\n                "sustainability_coach", "nature_connector",\n                "eco_footprint_tracker", "regenerative_living_guide",'

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

old_modules = '{ name: "financial_independence_tracker", stats: modernStats.evolution_health?.financial_independence_tracker },\n  ].filter(m => m.stats);'

new_modules = '{ name: "financial_independence_tracker", stats: modernStats.evolution_health?.financial_independence_tracker },\n    { name: "sustainability_coach", stats: modernStats.evolution_health?.sustainability_coach },\n    { name: "nature_connector", stats: modernStats.evolution_health?.nature_connector },\n    { name: "eco_footprint_tracker", stats: modernStats.evolution_health?.eco_footprint_tracker },\n    { name: "regenerative_living_guide", stats: modernStats.evolution_health?.regenerative_living_guide },\n  ].filter(m => m.stats);'

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
