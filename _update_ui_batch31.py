import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"purpose_clarity_engine", "legacy_builder",
                "impact_maximizer", "meaning_amplifier"'''

new_filter = '''"purpose_clarity_engine", "legacy_builder",
                "impact_maximizer", "meaning_amplifier",
                "courage_coach", "risk_intelligence_trainer",
                "vulnerability_builder", "authenticity_amplifier"'''

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

old_modules = '''{ name: "meaning_amplifier", stats: modernStats.evolution_health?.meaning_amplifier },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "meaning_amplifier", stats: modernStats.evolution_health?.meaning_amplifier },
    { name: "courage_coach", stats: modernStats.evolution_health?.courage_coach },
    { name: "risk_intelligence_trainer", stats: modernStats.evolution_health?.risk_intelligence_trainer },
    { name: "vulnerability_builder", stats: modernStats.evolution_health?.vulnerability_builder },
    { name: "authenticity_amplifier", stats: modernStats.evolution_health?.authenticity_amplifier },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
