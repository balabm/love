import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"values_explorer", "belief_examiner",
                "shadow_integrator", "inner_critic_manager"'''

new_filter = '''"values_explorer", "belief_examiner",
                "shadow_integrator", "inner_critic_manager",
                "emotional_intelligence_trainer", "empathy_builder",
                "compassion_generator", "gratitude_amplifier"'''

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

old_modules = '''{ name: "inner_critic_manager", stats: modernStats.evolution_health?.inner_critic_manager },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "inner_critic_manager", stats: modernStats.evolution_health?.inner_critic_manager },
    { name: "emotional_intelligence_trainer", stats: modernStats.evolution_health?.emotional_intelligence_trainer },
    { name: "empathy_builder", stats: modernStats.evolution_health?.empathy_builder },
    { name: "compassion_generator", stats: modernStats.evolution_health?.compassion_generator },
    { name: "gratitude_amplifier", stats: modernStats.evolution_health?.gratitude_amplifier },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
