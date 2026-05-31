import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"energy_protector", "boundary_enforcer",
                "time_sovereign", "attention_guardian"'''

new_filter = '''"energy_protector", "boundary_enforcer",
                "time_sovereign", "attention_guardian",
                "identity_designer", "habit_architect",
                "environment_curator", "ritual_master"'''

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

old_modules = '''{ name: "attention_guardian", stats: modernStats.evolution_health?.attention_guardian },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "attention_guardian", stats: modernStats.evolution_health?.attention_guardian },
    { name: "identity_designer", stats: modernStats.evolution_health?.identity_designer },
    { name: "habit_architect", stats: modernStats.evolution_health?.habit_architect },
    { name: "environment_curator", stats: modernStats.evolution_health?.environment_curator },
    { name: "ritual_master", stats: modernStats.evolution_health?.ritual_master },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
