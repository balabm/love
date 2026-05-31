import re

# 1. Update SentinelPanel.jsx
with open('ui/src/components/SentinelPanel.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_filter = '''"llm_manager", "graph_rag", "prompt_optimizer", "self_reflection",
                "conversation_quality", "predictive_maintenance", "multi_agent_orchestrator",
                "intent_predictor", "personality_adapter", "response_cache",
                "context_window_manager", "user_pattern_detector", "goal_drift_detector",
                "cross_modal_fusion", "emotional_resonance", "knowledge_graph_builder",
                "adaptive_learning_rate", "conversation_continuity"'''

new_filter = '''"llm_manager", "graph_rag", "prompt_optimizer", "self_reflection",
                "conversation_quality", "predictive_maintenance", "multi_agent_orchestrator",
                "intent_predictor", "personality_adapter", "response_cache",
                "context_window_manager", "user_pattern_detector", "goal_drift_detector",
                "cross_modal_fusion", "emotional_resonance", "knowledge_graph_builder",
                "adaptive_learning_rate", "conversation_continuity",
                "memory_compressor", "semantic_search_optimizer", "emotion_aware_response",
                "knowledge_injector", "conversation_summarizer", "context_aware_prioritizer",
                "wellness_nudger", "notification_filter", "deep_work_protector",
                "energy_forecaster", "smart_break_suggester", "habit_streak_tracker",
                "sleep_analyzer", "social_connection_monitor", "learning_path_optimizer",
                "focus_recovery_tracker", "decision_journal", "mood_journal",
                "values_alignment_checker", "gratitude_tracker", "energy_audit_tool",
                "time_audit_tool", "reflection_prompt_generator"'''

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

old_modules = '''{ name: "llm_manager", stats: modernStats.evolution_health?.llm_manager },
    { name: "graph_rag", stats: modernStats.evolution_health?.graph_rag },
    { name: "prompt_optimizer", stats: modernStats.evolution_health?.prompt_optimizer },
    { name: "self_reflection", stats: modernStats.evolution_health?.self_reflection },
    { name: "conversation_quality", stats: modernStats.evolution_health?.conversation_quality },
    { name: "predictive_maintenance", stats: modernStats.evolution_health?.predictive_maintenance },
    { name: "multi_agent_orchestrator", stats: modernStats.evolution_health?.multi_agent_orchestrator },
    { name: "intent_predictor", stats: modernStats.evolution_health?.intent_predictor },
    { name: "personality_adapter", stats: modernStats.evolution_health?.personality_adapter },
    { name: "response_cache", stats: modernStats.evolution_health?.response_cache },
    { name: "context_window_manager", stats: modernStats.evolution_health?.context_window_manager },
    { name: "user_pattern_detector", stats: modernStats.evolution_health?.user_pattern_detector },
    { name: "goal_drift_detector", stats: modernStats.evolution_health?.goal_drift_detector },
    { name: "cross_modal_fusion", stats: modernStats.evolution_health?.cross_modal_fusion },
    { name: "emotional_resonance", stats: modernStats.evolution_health?.emotional_resonance },
    { name: "knowledge_graph_builder", stats: modernStats.evolution_health?.knowledge_graph_builder },
  ].filter(m => m.stats);'''

new_modules = '''{ name: "llm_manager", stats: modernStats.evolution_health?.llm_manager },
    { name: "graph_rag", stats: modernStats.evolution_health?.graph_rag },
    { name: "prompt_optimizer", stats: modernStats.evolution_health?.prompt_optimizer },
    { name: "self_reflection", stats: modernStats.evolution_health?.self_reflection },
    { name: "conversation_quality", stats: modernStats.evolution_health?.conversation_quality },
    { name: "predictive_maintenance", stats: modernStats.evolution_health?.predictive_maintenance },
    { name: "multi_agent_orchestrator", stats: modernStats.evolution_health?.multi_agent_orchestrator },
    { name: "intent_predictor", stats: modernStats.evolution_health?.intent_predictor },
    { name: "personality_adapter", stats: modernStats.evolution_health?.personality_adapter },
    { name: "response_cache", stats: modernStats.evolution_health?.response_cache },
    { name: "context_window_manager", stats: modernStats.evolution_health?.context_window_manager },
    { name: "user_pattern_detector", stats: modernStats.evolution_health?.user_pattern_detector },
    { name: "goal_drift_detector", stats: modernStats.evolution_health?.goal_drift_detector },
    { name: "cross_modal_fusion", stats: modernStats.evolution_health?.cross_modal_fusion },
    { name: "emotional_resonance", stats: modernStats.evolution_health?.emotional_resonance },
    { name: "knowledge_graph_builder", stats: modernStats.evolution_health?.knowledge_graph_builder },
    { name: "adaptive_learning_rate", stats: modernStats.evolution_health?.adaptive_learning_rate },
    { name: "conversation_continuity", stats: modernStats.evolution_health?.conversation_continuity },
    { name: "memory_compressor", stats: modernStats.evolution_health?.memory_compressor },
    { name: "semantic_search_optimizer", stats: modernStats.evolution_health?.semantic_search_optimizer },
    { name: "emotion_aware_response", stats: modernStats.evolution_health?.emotion_aware_response },
    { name: "knowledge_injector", stats: modernStats.evolution_health?.knowledge_injector },
    { name: "conversation_summarizer", stats: modernStats.evolution_health?.conversation_summarizer },
    { name: "context_aware_prioritizer", stats: modernStats.evolution_health?.context_aware_prioritizer },
    { name: "wellness_nudger", stats: modernStats.evolution_health?.wellness_nudger },
    { name: "notification_filter", stats: modernStats.evolution_health?.notification_filter },
    { name: "deep_work_protector", stats: modernStats.evolution_health?.deep_work_protector },
    { name: "energy_forecaster", stats: modernStats.evolution_health?.energy_forecaster },
    { name: "smart_break_suggester", stats: modernStats.evolution_health?.smart_break_suggester },
    { name: "habit_streak_tracker", stats: modernStats.evolution_health?.habit_streak_tracker },
    { name: "sleep_analyzer", stats: modernStats.evolution_health?.sleep_analyzer },
    { name: "social_connection_monitor", stats: modernStats.evolution_health?.social_connection_monitor },
    { name: "learning_path_optimizer", stats: modernStats.evolution_health?.learning_path_optimizer },
    { name: "focus_recovery_tracker", stats: modernStats.evolution_health?.focus_recovery_tracker },
    { name: "decision_journal", stats: modernStats.evolution_health?.decision_journal },
    { name: "mood_journal", stats: modernStats.evolution_health?.mood_journal },
    { name: "values_alignment_checker", stats: modernStats.evolution_health?.values_alignment_checker },
    { name: "gratitude_tracker", stats: modernStats.evolution_health?.gratitude_tracker },
    { name: "energy_audit_tool", stats: modernStats.evolution_health?.energy_audit_tool },
    { name: "time_audit_tool", stats: modernStats.evolution_health?.time_audit_tool },
    { name: "reflection_prompt_generator", stats: modernStats.evolution_health?.reflection_prompt_generator },
  ].filter(m => m.stats);'''

if old_modules in content:
    content = content.replace(old_modules, new_modules)
    with open('ui/src/components/IntelligenceDashboard.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated IntelligenceDashboard.jsx')
else:
    print('Could not find IntelligenceDashboard.jsx modernModules list')
