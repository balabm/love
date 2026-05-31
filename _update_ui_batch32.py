import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '"celebration_architect", "spontaneity_generator",'
new_filter = '"celebration_architect", "spontaneity_generator",\n                "forgiveness_coach", "reconciliation_builder",\n                "trust_architect", "repair_specialist",'

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

old_modules = '{ name: "spontaneity_generator", stats: modernStats.evolution_health?.spontaneity_generator },\n  ].filter(m => m.stats);'

new_modules = '{ name: "spontaneity_generator", stats: modernStats.evolution_health?.spontaneity_generator },\n    { name: "forgiveness_coach", stats: modernStats.evolution_health?.forgiveness_coach },\n    { name: "reconciliation_builder", stats: modernStats.evolution_health?.reconciliation_builder },\n    { name: "trust_architect", stats: modernStats.evolution_health?.trust_architect },\n    { name: "repair_specialist", stats: modernStats.evolution_health?.repair_specialist },\n  ].filter(m => m.stats);'

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
