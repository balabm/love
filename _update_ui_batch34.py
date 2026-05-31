import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '"boundary_architect",'
new_filter = '"boundary_architect",\n                "leadership_coach", "influence_builder",\n                "delegation_trainer", "vision_keeper",'

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

old_modules = '{ name: "boundary_architect", stats: modernStats.evolution_health?.boundary_architect },\n  ].filter(m => m.stats);'

new_modules = '{ name: "boundary_architect", stats: modernStats.evolution_health?.boundary_architect },\n    { name: "leadership_coach", stats: modernStats.evolution_health?.leadership_coach },\n    { name: "influence_builder", stats: modernStats.evolution_health?.influence_builder },\n    { name: "delegation_trainer", stats: modernStats.evolution_health?.delegation_trainer },\n    { name: "vision_keeper", stats: modernStats.evolution_health?.vision_keeper },\n  ].filter(m => m.stats);'

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
