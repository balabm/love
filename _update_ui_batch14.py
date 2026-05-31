import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"conflict_resolution_coach", "boundaries_coach",
                "assertiveness_trainer", "active_listening_coach"'''

new_filter = '''"conflict_resolution_coach", "boundaries_coach",
                "assertiveness_trainer", "active_listening_coach",
                "self_compassion_coach", "forgiveness_tracker",
                "vulnerability_builder", "trust_builder"'''

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

old_modules = '''{ name: "active_listening_coach", stats: modernStats.evolution_health?.active_listening_coach },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "active_listening_coach", stats: modernStats.evolution_health?.active_listening_coach },
    { name: "self_compassion_coach", stats: modernStats.evolution_health?.self_compassion_coach },
    { name: "forgiveness_tracker", stats: modernStats.evolution_health?.forgiveness_tracker },
    { name: "vulnerability_builder", stats: modernStats.evolution_health?.vulnerability_builder },
    { name: "trust_builder", stats: modernStats.evolution_health?.trust_builder },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
