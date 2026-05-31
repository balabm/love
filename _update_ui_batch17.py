import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"meaning_mapper", "purpose_navigator",
                "legacy_builder", "death_awareness_coach"'''

new_filter = '''"meaning_mapper", "purpose_navigator",
                "legacy_builder", "death_awareness_coach",
                "flow_state_coach", "savoring_trainer",
                "presence_detector", "intuition_trainer"'''

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

old_modules = '''{ name: "death_awareness_coach", stats: modernStats.evolution_health?.death_awareness_coach },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "death_awareness_coach", stats: modernStats.evolution_health?.death_awareness_coach },
    { name: "flow_state_coach", stats: modernStats.evolution_health?.flow_state_coach },
    { name: "savoring_trainer", stats: modernStats.evolution_health?.savoring_trainer },
    { name: "presence_detector", stats: modernStats.evolution_health?.presence_detector },
    { name: "intuition_trainer", stats: modernStats.evolution_health?.intuition_trainer },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
