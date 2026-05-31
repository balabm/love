import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"self_compassion_coach", "forgiveness_tracker",
                "vulnerability_builder", "trust_builder"'''

new_filter = '''"self_compassion_coach", "forgiveness_tracker",
                "vulnerability_builder", "trust_builder",
                "curiosity_spark", "play_coach",
                "adventure_planner", "wonder_tracker"'''

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

old_modules = '''{ name: "trust_builder", stats: modernStats.evolution_health?.trust_builder },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "trust_builder", stats: modernStats.evolution_health?.trust_builder },
    { name: "curiosity_spark", stats: modernStats.evolution_health?.curiosity_spark },
    { name: "play_coach", stats: modernStats.evolution_health?.play_coach },
    { name: "adventure_planner", stats: modernStats.evolution_health?.adventure_planner },
    { name: "wonder_tracker", stats: modernStats.evolution_health?.wonder_tracker },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
