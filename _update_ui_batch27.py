import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"digital_minimalism_coach", "focus_ritual_designer",
                "attention_recovery_specialist", "cognitive_load_manager"'''

new_filter = '''"digital_minimalism_coach", "focus_ritual_designer",
                "attention_recovery_specialist", "cognitive_load_manager",
                "stress_resilience_trainer", "emotional_regulation_coach",
                "mindfulness_trainer", "presence_amplifier"'''

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

old_modules = '''{ name: "cognitive_load_manager", stats: modernStats.evolution_health?.cognitive_load_manager },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "cognitive_load_manager", stats: modernStats.evolution_health?.cognitive_load_manager },
    { name: "stress_resilience_trainer", stats: modernStats.evolution_health?.stress_resilience_trainer },
    { name: "emotional_regulation_coach", stats: modernStats.evolution_health?.emotional_regulation_coach },
    { name: "mindfulness_trainer", stats: modernStats.evolution_health?.mindfulness_trainer },
    { name: "presence_amplifier", stats: modernStats.evolution_health?.presence_amplifier },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
