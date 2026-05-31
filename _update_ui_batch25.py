import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"deep_work_enabler", "recovery_optimizer",
                "peak_performance_tracker", "mindful_productivity_coach"'''

new_filter = '''"deep_work_enabler", "recovery_optimizer",
                "peak_performance_tracker", "mindful_productivity_coach",
                "sleep_optimizer", "nutrition_coach",
                "movement_tracker", "health_integrator"'''

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

old_modules = '''{ name: "mindful_productivity_coach", stats: modernStats.evolution_health?.mindful_productivity_coach },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "mindful_productivity_coach", stats: modernStats.evolution_health?.mindful_productivity_coach },
    { name: "sleep_optimizer", stats: modernStats.evolution_health?.sleep_optimizer },
    { name: "nutrition_coach", stats: modernStats.evolution_health?.nutrition_coach },
    { name: "movement_tracker", stats: modernStats.evolution_health?.movement_tracker },
    { name: "health_integrator", stats: modernStats.evolution_health?.health_integrator },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
