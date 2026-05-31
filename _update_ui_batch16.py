import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"curiosity_spark", "play_coach",
                "adventure_planner", "wonder_tracker"'''

new_filter = '''"curiosity_spark", "play_coach",
                "adventure_planner", "wonder_tracker",
                "meaning_mapper", "purpose_navigator",
                "legacy_builder", "death_awareness_coach"'''

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

old_modules = '''{ name: "wonder_tracker", stats: modernStats.evolution_health?.wonder_tracker },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "wonder_tracker", stats: modernStats.evolution_health?.wonder_tracker },
    { name: "meaning_mapper", stats: modernStats.evolution_health?.meaning_mapper },
    { name: "purpose_navigator", stats: modernStats.evolution_health?.purpose_navigator },
    { name: "legacy_builder", stats: modernStats.evolution_health?.legacy_builder },
    { name: "death_awareness_coach", stats: modernStats.evolution_health?.death_awareness_coach },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
