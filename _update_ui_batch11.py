import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"emergency_preparedness_tracker", "home_maintenance_scheduler",
                "career_path_mapper", "skill_gap_analyzer"'''

new_filter = '''"emergency_preparedness_tracker", "home_maintenance_scheduler",
                "career_path_mapper", "skill_gap_analyzer",
                "document_organizer", "password_health_checker",
                "subscription_manager", "digital_declutterer"'''

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

old_modules = '''{ name: "skill_gap_analyzer", stats: modernStats.evolution_health?.skill_gap_analyzer },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "skill_gap_analyzer", stats: modernStats.evolution_health?.skill_gap_analyzer },
    { name: "document_organizer", stats: modernStats.evolution_health?.document_organizer },
    { name: "password_health_checker", stats: modernStats.evolution_health?.password_health_checker },
    { name: "subscription_manager", stats: modernStats.evolution_health?.subscription_manager },
    { name: "digital_declutterer", stats: modernStats.evolution_health?.digital_declutterer },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
