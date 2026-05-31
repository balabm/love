import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"courage_coach", "risk_intelligence_trainer",
                "vulnerability_builder", "authenticity_amplifier"'''

new_filter = '''"courage_coach", "risk_intelligence_trainer",
                "vulnerability_builder", "authenticity_amplifier",
                "humor_playfulness_trainer", "joy_cultivator",
                "celebration_architect", "spontaneity_generator"'''

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

old_modules = '''{ name: "authenticity_amplifier", stats: modernStats.evolution_health?.authenticity_amplifier },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "authenticity_amplifier", stats: modernStats.evolution_health?.authenticity_amplifier },
    { name: "humor_playfulness_trainer", stats: modernStats.evolution_health?.humor_playfulness_trainer },
    { name: "joy_cultivator", stats: modernStats.evolution_health?.joy_cultivator },
    { name: "celebration_architect", stats: modernStats.evolution_health?.celebration_architect },
    { name: "spontaneity_generator", stats: modernStats.evolution_health?.spontaneity_generator },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
