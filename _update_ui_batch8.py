import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"reading_tracker", "writing_coach",
                "creativity_booster", "stress_response_coach"'''

new_filter = '''"reading_tracker", "writing_coach",
                "creativity_booster", "stress_response_coach",
                "communication_analyzer", "goal_progress_visualizer",
                "life_balance_wheel", "productivity_gamifier"'''

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

old_modules = '''{ name: "stress_response_coach", stats: modernStats.evolution_health?.stress_response_coach },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "stress_response_coach", stats: modernStats.evolution_health?.stress_response_coach },
    { name: "communication_analyzer", stats: modernStats.evolution_health?.communication_analyzer },
    { name: "goal_progress_visualizer", stats: modernStats.evolution_health?.goal_progress_visualizer },
    { name: "life_balance_wheel", stats: modernStats.evolution_health?.life_balance_wheel },
    { name: "productivity_gamifier", stats: modernStats.evolution_health?.productivity_gamifier },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
