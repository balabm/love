import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"sleep_optimizer", "nutrition_coach",
                "movement_tracker", "health_integrator"'''

new_filter = '''"sleep_optimizer", "nutrition_coach",
                "movement_tracker", "health_integrator",
                "digital_minimalism_coach", "focus_ritual_designer",
                "attention_recovery_specialist", "cognitive_load_manager"'''

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

old_modules = '''{ name: "health_integrator", stats: modernStats.evolution_health?.health_integrator },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "health_integrator", stats: modernStats.evolution_health?.health_integrator },
    { name: "digital_minimalism_coach", stats: modernStats.evolution_health?.digital_minimalism_coach },
    { name: "focus_ritual_designer", stats: modernStats.evolution_health?.focus_ritual_designer },
    { name: "attention_recovery_specialist", stats: modernStats.evolution_health?.attention_recovery_specialist },
    { name: "cognitive_load_manager", stats: modernStats.evolution_health?.cognitive_load_manager },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
