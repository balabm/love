import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"creativity_catalyst", "innovation_spark_generator",
                "problem_reframer", "perspective_shifter"'''

new_filter = '''"creativity_catalyst", "innovation_spark_generator",
                "problem_reframer", "perspective_shifter",
                "curiosity_cultivator", "learning_acceleration_engine",
                "knowledge_synthesizer", "wisdom_distiller"'''

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

old_modules = '''{ name: "perspective_shifter", stats: modernStats.evolution_health?.perspective_shifter },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "perspective_shifter", stats: modernStats.evolution_health?.perspective_shifter },
    { name: "curiosity_cultivator", stats: modernStats.evolution_health?.curiosity_cultivator },
    { name: "learning_acceleration_engine", stats: modernStats.evolution_health?.learning_acceleration_engine },
    { name: "knowledge_synthesizer", stats: modernStats.evolution_health?.knowledge_synthesizer },
    { name: "wisdom_distiller", stats: modernStats.evolution_health?.wisdom_distiller },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
