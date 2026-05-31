import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"communication_analyzer", "goal_progress_visualizer",
                "life_balance_wheel", "productivity_gamifier"'''

new_filter = '''"communication_analyzer", "goal_progress_visualizer",
                "life_balance_wheel", "productivity_gamifier",
                "environment_optimizer", "weather_suggester",
                "travel_planner", "gift_idea_generator"'''

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

old_modules = '''{ name: "productivity_gamifier", stats: modernStats.evolution_health?.productivity_gamifier },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "productivity_gamifier", stats: modernStats.evolution_health?.productivity_gamifier },
    { name: "environment_optimizer", stats: modernStats.evolution_health?.environment_optimizer },
    { name: "weather_suggester", stats: modernStats.evolution_health?.weather_suggester },
    { name: "travel_planner", stats: modernStats.evolution_health?.travel_planner },
    { name: "gift_idea_generator", stats: modernStats.evolution_health?.gift_idea_generator },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
