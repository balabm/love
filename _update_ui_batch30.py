import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"curiosity_cultivator", "learning_acceleration_engine",
                "knowledge_synthesizer", "wisdom_distiller"'''

new_filter = '''"curiosity_cultivator", "learning_acceleration_engine",
                "knowledge_synthesizer", "wisdom_distiller",
                "purpose_clarity_engine", "legacy_builder",
                "impact_maximizer", "meaning_amplifier"'''

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

old_modules = '''{ name: "wisdom_distiller", stats: modernStats.evolution_health?.wisdom_distiller },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "wisdom_distiller", stats: modernStats.evolution_health?.wisdom_distiller },
    { name: "purpose_clarity_engine", stats: modernStats.evolution_health?.purpose_clarity_engine },
    { name: "legacy_builder", stats: modernStats.evolution_health?.legacy_builder },
    { name: "impact_maximizer", stats: modernStats.evolution_health?.impact_maximizer },
    { name: "meaning_amplifier", stats: modernStats.evolution_health?.meaning_amplifier },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
