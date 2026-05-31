import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"stress_resilience_trainer", "emotional_regulation_coach",
                "mindfulness_trainer", "presence_amplifier"'''

new_filter = '''"stress_resilience_trainer", "emotional_regulation_coach",
                "mindfulness_trainer", "presence_amplifier",
                "creativity_catalyst", "innovation_spark_generator",
                "problem_reframer", "perspective_shifter"'''

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

old_modules = '''{ name: "presence_amplifier", stats: modernStats.evolution_health?.presence_amplifier },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "presence_amplifier", stats: modernStats.evolution_health?.presence_amplifier },
    { name: "creativity_catalyst", stats: modernStats.evolution_health?.creativity_catalyst },
    { name: "innovation_spark_generator", stats: modernStats.evolution_health?.innovation_spark_generator },
    { name: "problem_reframer", stats: modernStats.evolution_health?.problem_reframer },
    { name: "perspective_shifter", stats: modernStats.evolution_health?.perspective_shifter },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
