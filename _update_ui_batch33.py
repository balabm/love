import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '"repair_specialist",'
new_filter = '"repair_specialist",\n                "deep_listener", "conflict_navigator",\n                "assertiveness_builder", "boundary_architect",'

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

old_modules = '{ name: "repair_specialist", stats: modernStats.evolution_health?.repair_specialist },\n  ].filter(m => m.stats);'

new_modules = '{ name: "repair_specialist", stats: modernStats.evolution_health?.repair_specialist },\n    { name: "deep_listener", stats: modernStats.evolution_health?.deep_listener },\n    { name: "conflict_navigator", stats: modernStats.evolution_health?.conflict_navigator },\n    { name: "assertiveness_builder", stats: modernStats.evolution_health?.assertiveness_builder },\n    { name: "boundary_architect", stats: modernStats.evolution_health?.boundary_architect },\n  ].filter(m => m.stats);'

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
