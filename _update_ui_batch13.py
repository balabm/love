import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"event_planner", "habit_builder",
                "morning_routine_designer", "evening_wind_down_coach"'''

new_filter = '''"event_planner", "habit_builder",
                "morning_routine_designer", "evening_wind_down_coach",
                "conflict_resolution_coach", "boundaries_coach",
                "assertiveness_trainer", "active_listening_coach"'''

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

old_modules = '''{ name: "evening_wind_down_coach", stats: modernStats.evolution_health?.evening_wind_down_coach },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "evening_wind_down_coach", stats: modernStats.evolution_health?.evening_wind_down_coach },
    { name: "conflict_resolution_coach", stats: modernStats.evolution_health?.conflict_resolution_coach },
    { name: "boundaries_coach", stats: modernStats.evolution_health?.boundaries_coach },
    { name: "assertiveness_trainer", stats: modernStats.evolution_health?.assertiveness_trainer },
    { name: "active_listening_coach", stats: modernStats.evolution_health?.active_listening_coach },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
