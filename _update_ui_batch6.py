import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"proactive_preparation_engine", "context_switching_minimizer",
                "task_batch_optimizer", "meeting_optimizer"'''

new_filter = '''"proactive_preparation_engine", "context_switching_minimizer",
                "task_batch_optimizer", "meeting_optimizer",
                "finance_pattern_detector", "nutrition_analyzer",
                "exercise_optimizer", "meditation_coach"'''

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

old_modules = '''{ name: "meeting_optimizer", stats: modernStats.evolution_health?.meeting_optimizer },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "meeting_optimizer", stats: modernStats.evolution_health?.meeting_optimizer },
    { name: "finance_pattern_detector", stats: modernStats.evolution_health?.finance_pattern_detector },
    { name: "nutrition_analyzer", stats: modernStats.evolution_health?.nutrition_analyzer },
    { name: "exercise_optimizer", stats: modernStats.evolution_health?.exercise_optimizer },
    { name: "meditation_coach", stats: modernStats.evolution_health?.meditation_coach },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
