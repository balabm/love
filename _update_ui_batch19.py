import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"resilience_builder", "growth_mindset_coach",
                "adaptability_trainer", "antifragility_tracker"'''

new_filter = '''"resilience_builder", "growth_mindset_coach",
                "adaptability_trainer", "antifragility_tracker",
                "discipline_trainer", "consistency_coach",
                "accountability_partner", "progress_celebrator"'''

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

old_modules = '''{ name: "antifragility_tracker", stats: modernStats.evolution_health?.antifragility_tracker },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "antifragility_tracker", stats: modernStats.evolution_health?.antifragility_tracker },
    { name: "discipline_trainer", stats: modernStats.evolution_health?.discipline_trainer },
    { name: "consistency_coach", stats: modernStats.evolution_health?.consistency_coach },
    { name: "accountability_partner", stats: modernStats.evolution_health?.accountability_partner },
    { name: "progress_celebrator", stats: modernStats.evolution_health?.progress_celebrator },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
