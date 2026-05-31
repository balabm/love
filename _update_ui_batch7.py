import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"finance_pattern_detector", "nutrition_analyzer",
                "exercise_optimizer", "meditation_coach"'''

new_filter = '''"finance_pattern_detector", "nutrition_analyzer",
                "exercise_optimizer", "meditation_coach",
                "reading_tracker", "writing_coach",
                "creativity_booster", "stress_response_coach"'''

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

old_modules = '''{ name: "meditation_coach", stats: modernStats.evolution_health?.meditation_coach },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "meditation_coach", stats: modernStats.evolution_health?.meditation_coach },
    { name: "reading_tracker", stats: modernStats.evolution_health?.reading_tracker },
    { name: "writing_coach", stats: modernStats.evolution_health?.writing_coach },
    { name: "creativity_booster", stats: modernStats.evolution_health?.creativity_booster },
    { name: "stress_response_coach", stats: modernStats.evolution_health?.stress_response_coach },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
