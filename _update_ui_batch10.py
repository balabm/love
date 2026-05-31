import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"environment_optimizer", "weather_suggester",
                "travel_planner", "gift_idea_generator"'''

new_filter = '''"environment_optimizer", "weather_suggester",
                "travel_planner", "gift_idea_generator",
                "emergency_preparedness_tracker", "home_maintenance_scheduler",
                "career_path_mapper", "skill_gap_analyzer"'''

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

old_modules = '''{ name: "gift_idea_generator", stats: modernStats.evolution_health?.gift_idea_generator },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "gift_idea_generator", stats: modernStats.evolution_health?.gift_idea_generator },
    { name: "emergency_preparedness_tracker", stats: modernStats.evolution_health?.emergency_preparedness_tracker },
    { name: "home_maintenance_scheduler", stats: modernStats.evolution_health?.home_maintenance_scheduler },
    { name: "career_path_mapper", stats: modernStats.evolution_health?.career_path_mapper },
    { name: "skill_gap_analyzer", stats: modernStats.evolution_health?.skill_gap_analyzer },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
