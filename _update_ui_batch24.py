import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"emotional_intelligence_trainer", "empathy_builder",
                "compassion_generator", "gratitude_amplifier"'''

new_filter = '''"emotional_intelligence_trainer", "empathy_builder",
                "compassion_generator", "gratitude_amplifier",
                "deep_work_enabler", "recovery_optimizer",
                "peak_performance_tracker", "mindful_productivity_coach"'''

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

old_modules = '''{ name: "gratitude_amplifier", stats: modernStats.evolution_health?.gratitude_amplifier },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "gratitude_amplifier", stats: modernStats.evolution_health?.gratitude_amplifier },
    { name: "deep_work_enabler", stats: modernStats.evolution_health?.deep_work_enabler },
    { name: "recovery_optimizer", stats: modernStats.evolution_health?.recovery_optimizer },
    { name: "peak_performance_tracker", stats: modernStats.evolution_health?.peak_performance_tracker },
    { name: "mindful_productivity_coach", stats: modernStats.evolution_health?.mindful_productivity_coach },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
