import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"discipline_trainer", "consistency_coach",
                "accountability_partner", "progress_celebrator"'''

new_filter = '''"discipline_trainer", "consistency_coach",
                "accountability_partner", "progress_celebrator",
                "energy_protector", "boundary_enforcer",
                "time_sovereign", "attention_guardian"'''

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

old_modules = '''{ name: "progress_celebrator", stats: modernStats.evolution_health?.progress_celebrator },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "progress_celebrator", stats: modernStats.evolution_health?.progress_celebrator },
    { name: "energy_protector", stats: modernStats.evolution_health?.energy_protector },
    { name: "boundary_enforcer", stats: modernStats.evolution_health?.boundary_enforcer },
    { name: "time_sovereign", stats: modernStats.evolution_health?.time_sovereign },
    { name: "attention_guardian", stats: modernStats.evolution_health?.attention_guardian },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
