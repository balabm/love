import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"memory_compressor", "semantic_search_optimizer", "emotion_aware_response",
                "knowledge_injector", "conversation_summarizer", "context_aware_prioritizer",
                "wellness_nudger", "notification_filter", "deep_work_protector",
                "energy_forecaster", "smart_break_suggester", "habit_streak_tracker",
                "sleep_analyzer", "social_connection_monitor", "learning_path_optimizer",
                "focus_recovery_tracker", "decision_journal", "mood_journal",
                "values_alignment_checker", "gratitude_tracker", "energy_audit_tool",
                "time_audit_tool", "reflection_prompt_generator"'''

new_filter = '''"memory_compressor", "semantic_search_optimizer", "emotion_aware_response",
                "knowledge_injector", "conversation_summarizer", "context_aware_prioritizer",
                "wellness_nudger", "notification_filter", "deep_work_protector",
                "energy_forecaster", "smart_break_suggester", "habit_streak_tracker",
                "sleep_analyzer", "social_connection_monitor", "learning_path_optimizer",
                "focus_recovery_tracker", "decision_journal", "mood_journal",
                "values_alignment_checker", "gratitude_tracker", "energy_audit_tool",
                "time_audit_tool", "reflection_prompt_generator",
                "proactive_preparation_engine", "context_switching_minimizer",
                "task_batch_optimizer", "meeting_optimizer"'''

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

old_modules = '''{ name: "time_audit_tool", stats: modernStats.evolution_health?.time_audit_tool },
    { name: "reflection_prompt_generator", stats: modernStats.evolution_health?.reflection_prompt_generator },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "time_audit_tool", stats: modernStats.evolution_health?.time_audit_tool },
    { name: "reflection_prompt_generator", stats: modernStats.evolution_health?.reflection_prompt_generator },
    { name: "proactive_preparation_engine", stats: modernStats.evolution_health?.proactive_preparation_engine },
    { name: "context_switching_minimizer", stats: modernStats.evolution_health?.context_switching_minimizer },
    { name: "task_batch_optimizer", stats: modernStats.evolution_health?.task_batch_optimizer },
    { name: "meeting_optimizer", stats: modernStats.evolution_health?.meeting_optimizer },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
