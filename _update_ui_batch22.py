import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"identity_designer", "habit_architect",
                "environment_curator", "ritual_master"'''

new_filter = '''"identity_designer", "habit_architect",
                "environment_curator", "ritual_master",
                "values_explorer", "belief_examiner",
                "shadow_integrator", "inner_critic_manager"'''

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

old_modules = '''{ name: "ritual_master", stats: modernStats.evolution_health?.ritual_master },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "ritual_master", stats: modernStats.evolution_health?.ritual_master },
    { name: "values_explorer", stats: modernStats.evolution_health?.values_explorer },
    { name: "belief_examiner", stats: modernStats.evolution_health?.belief_examiner },
    { name: "shadow_integrator", stats: modernStats.evolution_health?.shadow_integrator },
    { name: "inner_critic_manager", stats: modernStats.evolution_health?.inner_critic_manager },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
