import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"flow_state_coach", "savoring_trainer",
                "presence_detector", "intuition_trainer"'''

new_filter = '''"flow_state_coach", "savoring_trainer",
                "presence_detector", "intuition_trainer",
                "resilience_builder", "growth_mindset_coach",
                "adaptability_trainer", "antifragility_tracker"'''

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

old_modules = '''{ name: "intuition_trainer", stats: modernStats.evolution_health?.intuition_trainer },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "intuition_trainer", stats: modernStats.evolution_health?.intuition_trainer },
    { name: "resilience_builder", stats: modernStats.evolution_health?.resilience_builder },
    { name: "growth_mindset_coach", stats: modernStats.evolution_health?.growth_mindset_coach },
    { name: "adaptability_trainer", stats: modernStats.evolution_health?.adaptability_trainer },
    { name: "antifragility_tracker", stats: modernStats.evolution_health?.antifragility_tracker },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
