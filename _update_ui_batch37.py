import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '"regenerative_living_guide",'
new_filter = '"regenerative_living_guide",\n                "spiritual_practice_coach", "transcendence_guide",\n                "sacred_ritual_designer", "contemplation_keeper",'

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

old_modules = '{ name: "regenerative_living_guide", stats: modernStats.evolution_health?.regenerative_living_guide },\n  ].filter(m => m.stats);'

new_modules = '{ name: "regenerative_living_guide", stats: modernStats.evolution_health?.regenerative_living_guide },\n    { name: "spiritual_practice_coach", stats: modernStats.evolution_health?.spiritual_practice_coach },\n    { name: "transcendence_guide", stats: modernStats.evolution_health?.transcendence_guide },\n    { name: "sacred_ritual_designer", stats: modernStats.evolution_health?.sacred_ritual_designer },\n    { name: "contemplation_keeper", stats: modernStats.evolution_health?.contemplation_keeper },\n  ].filter(m => m.stats);'

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
