with open('start_evolution.py', 'r') as f:
    content = f.read()

# Find and replace the modern_modules list
old_list = '''    modern_modules = [
        ("LLM Manager", "core.llm_manager", "get_llm_manager"),
        ("Graph RAG", "core.graph_rag", "get_graph_rag_engine"),
        ("Prompt Optimizer", "core.prompt_optimizer", "get_prompt_optimizer"),
        ("Self-Reflection", "core.self_reflection", "get_self_reflection_engine"),
        ("Conversation Quality", "core.conversation_quality", "get_conversation_quality_analyzer"),
        ("Predictive Maintenance", "core.predictive_maintenance", "get_predictive_maintenance_engine"),
        ("Multi-Agent Orchestrator", "core.multi_agent_orchestrator", "get_multi_agent_orchestrator"),
        ("Intent Predictor", "core.intent_predictor", "get_intent_predictor"),
        ("Personality Adapter", "core.personality_adapter", "get_personality_adapter"),
        ("Response Cache", "core.response_cache", "get_response_cache"),
        ("Context Window Manager", "core.context_window_manager", "get_context_window_manager"),
        ("User Pattern Detector", "core.user_pattern_detector", "get_user_pattern_detector"),
        ("Goal Drift Detector", "core.goal_drift_detector", "get_goal_drift_detector"),
        ("Cross-Modal Fusion", "core.cross_modal_fusion", "get_cross_modal_fusion_engine"),
        ("Emotional Resonance", "core.emotional_resonance", "get_emotional_resonance_engine"),
        ("Knowledge Graph Builder", "core.knowledge_graph_builder", "get_knowledge_graph_builder"),
        ("Adaptive Learning Rate", "core.adaptive_learning_rate", "get_adaptive_learning_engine"),
        ("Conversation Continuity", "core.conversation_continuity", "get_conversation_continuity_manager"),
    ]'''

new_list = '''    modern_modules = [
        ("LLM Manager", "core.llm_manager", "get_llm_manager"),
        ("Graph RAG", "core.graph_rag", "get_graph_rag_engine"),
        ("Prompt Optimizer", "core.prompt_optimizer", "get_prompt_optimizer"),
        ("Self-Reflection", "core.self_reflection", "get_self_reflection_engine"),
        ("Conversation Quality", "core.conversation_quality", "get_conversation_quality_analyzer"),
        ("Predictive Maintenance", "core.predictive_maintenance", "get_predictive_maintenance_engine"),
        ("Multi-Agent Orchestrator", "core.multi_agent_orchestrator", "get_multi_agent_orchestrator"),
        ("Intent Predictor", "core.intent_predictor", "get_intent_predictor"),
        ("Personality Adapter", "core.personality_adapter", "get_personality_adapter"),
        ("Response Cache", "core.response_cache", "get_response_cache"),
        ("Context Window Manager", "core.context_window_manager", "get_context_window_manager"),
        ("User Pattern Detector", "core.user_pattern_detector", "get_user_pattern_detector"),
        ("Goal Drift Detector", "core.goal_drift_detector", "get_goal_drift_detector"),
        ("Cross-Modal Fusion", "core.cross_modal_fusion", "get_cross_modal_fusion_engine"),
        ("Emotional Resonance", "core.emotional_resonance", "get_emotional_resonance_engine"),
        ("Knowledge Graph Builder", "core.knowledge_graph_builder", "get_knowledge_graph_builder"),
        ("Adaptive Learning Rate", "core.adaptive_learning_rate", "get_adaptive_learning_engine"),
        ("Conversation Continuity", "core.conversation_continuity", "get_conversation_continuity_manager"),
        ("Memory Compressor", "core.memory_compressor", "get_memory_compressor"),
        ("Semantic Search Optimizer", "core.semantic_search_optimizer", "get_semantic_search_optimizer"),
        ("Emotion-Aware Response", "core.emotion_aware_response", "get_emotion_aware_response_generator"),
        ("Knowledge Injector", "core.knowledge_injector", "get_knowledge_injector"),
        ("Conversation Summarizer", "core.conversation_summarizer", "get_conversation_summarizer"),
        ("Context-Aware Task Prioritizer", "core.context_aware_prioritizer", "get_context_aware_prioritizer"),
        ("Wellness Nudger", "core.wellness_nudger", "get_wellness_nudger"),
        ("Notification Filter", "core.notification_filter", "get_notification_filter"),
        ("Deep Work Protector", "core.deep_work_protector", "get_deep_work_protector"),
        ("Energy Forecaster", "core.energy_forecaster", "get_energy_forecaster"),
        ("Smart Break Suggester", "core.smart_break_suggester", "get_smart_break_suggester"),
        ("Habit Streak Tracker", "core.habit_streak_tracker", "get_habit_streak_tracker"),
        ("Sleep Analyzer", "core.sleep_analyzer", "get_sleep_analyzer"),
        ("Social Connection Monitor", "core.social_connection_monitor", "get_social_connection_monitor"),
        ("Learning Path Optimizer", "core.learning_path_optimizer", "get_learning_path_optimizer"),
    ]'''

if old_list in content:
    content = content.replace(old_list, new_list)
    with open('start_evolution.py', 'w') as f:
        f.write(content)
    print('Updated start_evolution.py modern_modules list')
else:
    print('Could not find modern_modules list in start_evolution.py')
