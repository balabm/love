"""
LOVE Modern AI Engines Test Suite

Comprehensive tests for all modern AI engines.
Run with: pytest tests/test_modern_engines.py -v
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── MCP Host Tests ────────────────────────────────────────────────────────────

class TestMCPHost:
    def test_singleton(self):
        from core.mcp_host import get_mcp_host
        host1 = get_mcp_host()
        host2 = get_mcp_host()
        assert host1 is host2

    def test_health(self):
        from core.mcp_host import get_mcp_host
        host = get_mcp_host()
        health = host.get_health()
        assert isinstance(health, dict)


# ── Reasoning Engine Tests ────────────────────────────────────────────────────

class TestReasoningEngine:
    def test_singleton(self):
        from core.reasoning_engine import get_reasoning_engine
        e1 = get_reasoning_engine()
        e2 = get_reasoning_engine()
        assert e1 is e2

    def test_analyze(self):
        from core.reasoning_engine import get_reasoning_engine
        engine = get_reasoning_engine()
        chain = engine.analyze("Test situation", {})
        assert chain.situation == "Test situation"

    def test_decide(self):
        from core.reasoning_engine import get_reasoning_engine
        engine = get_reasoning_engine()
        result = engine.decide("What to do?", [
            {"id": "a", "description": "Option A"},
            {"id": "b", "description": "Option B"},
        ])
        assert isinstance(result, dict)
        assert "winner" in result


# ── Structured Output Tests ───────────────────────────────────────────────────

class TestStructuredOutput:
    def test_singleton(self):
        from core.structured_output import get_structured_engine
        e1 = get_structured_engine()
        e2 = get_structured_engine()
        assert e1 is e2

    def test_statistics(self):
        from core.structured_output import get_structured_engine
        engine = get_structured_engine()
        stats = engine.get_statistics()
        assert isinstance(stats, dict)


# ── Vector Memory Tests ──────────────────────────────────────────────────────

class TestVectorMemory:
    def test_singleton(self):
        from core.vector_memory import get_vector_engine
        e1 = get_vector_engine()
        e2 = get_vector_engine()
        assert e1 is e2

    def test_store_and_search(self):
        from core.vector_memory import get_vector_engine
        engine = get_vector_engine()
        mem_id = engine.store("Test memory about programming", source="test", tags=["test"])
        assert mem_id is not None
        results = engine.search("programming", top_k=5)
        assert isinstance(results, list)


# ── LLM Manager Tests ───────────────────────────────────────────────────────

class TestLLMManager:
    def test_singleton(self):
        from core.llm_manager import get_llm_manager
        m1 = get_llm_manager()
        m2 = get_llm_manager()
        assert m1 is m2

    def test_route_task(self):
        from core.llm_manager import get_llm_manager
        manager = get_llm_manager()
        route = manager.route_task("chat")
        assert isinstance(route, dict) or hasattr(route, "model")

    def test_record_performance(self):
        from core.llm_manager import get_llm_manager
        manager = get_llm_manager()
        manager.record_performance("test_model", 500.0, True, task_type="chat")

    def test_get_all_stats(self):
        from core.llm_manager import get_llm_manager
        manager = get_llm_manager()
        stats = manager.get_all_stats()
        assert isinstance(stats, dict)


# ── Graph RAG Tests ──────────────────────────────────────────────────────────

class TestGraphRAG:
    def test_singleton(self):
        from core.graph_rag import get_graph_rag_engine
        g1 = get_graph_rag_engine()
        g2 = get_graph_rag_engine()
        assert g1 is g2

    def test_query(self):
        from core.graph_rag import get_graph_rag_engine
        rag = get_graph_rag_engine()
        result = rag.query("What is AI?")
        assert hasattr(result, "answer") or isinstance(result, dict)

    def test_get_statistics(self):
        from core.graph_rag import get_graph_rag_engine
        rag = get_graph_rag_engine()
        stats = rag.get_statistics()
        assert isinstance(stats, dict)


# ── Prompt Optimizer Tests ────────────────────────────────────────────────────

class TestPromptOptimizer:
    def test_singleton(self):
        from core.prompt_optimizer import get_prompt_optimizer
        o1 = get_prompt_optimizer()
        o2 = get_prompt_optimizer()
        assert o1 is o2

    def test_register_template(self):
        from core.prompt_optimizer import get_prompt_optimizer
        optimizer = get_prompt_optimizer()
        optimizer.register_template("chat", "You are a helpful assistant.")

    def test_get_best_prompt(self):
        from core.prompt_optimizer import get_prompt_optimizer
        optimizer = get_prompt_optimizer()
        result = optimizer.get_best_prompt("chat")
        # May be None if no templates registered

    def test_get_statistics(self):
        from core.prompt_optimizer import get_prompt_optimizer
        optimizer = get_prompt_optimizer()
        stats = optimizer.get_statistics()
        assert isinstance(stats, dict)


# ── Self-Reflection Tests ─────────────────────────────────────────────────────

class TestSelfReflection:
    def test_singleton(self):
        from core.self_reflection import get_self_reflection_engine
        e1 = get_self_reflection_engine()
        e2 = get_self_reflection_engine()
        assert e1 is e2

    def test_record_decision(self):
        from core.self_reflection import get_self_reflection_engine
        engine = get_self_reflection_engine()
        engine.record_decision(
            "test_subsystem", "test_decision",
            {"context": "test"}, "do_something", "because it helps", "success"
        )

    def test_get_statistics(self):
        from core.self_reflection import get_self_reflection_engine
        engine = get_self_reflection_engine()
        stats = engine.get_statistics()
        assert isinstance(stats, dict)

    def test_get_recent_insights(self):
        from core.self_reflection import get_self_reflection_engine
        engine = get_self_reflection_engine()
        insights = engine.get_recent_insights(limit=5)
        assert isinstance(insights, list)


# ── Conversation Quality Tests ────────────────────────────────────────────────

class TestConversationQuality:
    def test_singleton(self):
        from core.conversation_quality import get_conversation_quality_analyzer
        c1 = get_conversation_quality_analyzer()
        c2 = get_conversation_quality_analyzer()
        assert c1 is c2

    def test_analyze_turn(self):
        from core.conversation_quality import get_conversation_quality_analyzer
        cq = get_conversation_quality_analyzer()
        result = cq.analyze_turn("How are you?", "I'm doing well, thanks for asking!")
        assert result is not None
        assert hasattr(result, "overall_score")

    def test_get_statistics(self):
        from core.conversation_quality import get_conversation_quality_analyzer
        cq = get_conversation_quality_analyzer()
        stats = cq.get_statistics()
        assert isinstance(stats, dict)


# ── Predictive Maintenance Tests ──────────────────────────────────────────────

class TestPredictiveMaintenance:
    def test_singleton(self):
        from core.predictive_maintenance import get_predictive_maintenance_engine
        p1 = get_predictive_maintenance_engine()
        p2 = get_predictive_maintenance_engine()
        assert p1 is p2

    def test_predict_failure(self):
        from core.predictive_maintenance import get_predictive_maintenance_engine
        pm = get_predictive_maintenance_engine()
        result = pm.predict_failure("test_subsystem")
        # May return None if no data, that's fine

    def test_record_snapshot(self):
        from core.predictive_maintenance import get_predictive_maintenance_engine
        pm = get_predictive_maintenance_engine()
        pm.record_snapshot("test_subsystem", 0.85)

    def test_get_statistics(self):
        from core.predictive_maintenance import get_predictive_maintenance_engine
        pm = get_predictive_maintenance_engine()
        stats = pm.get_statistics()
        assert isinstance(stats, dict)


# ── Multi-Agent Orchestrator Tests ────────────────────────────────────────────

class TestMultiAgentOrchestrator:
    def test_singleton(self):
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        o1 = get_multi_agent_orchestrator()
        o2 = get_multi_agent_orchestrator()
        assert o1 is o2

    def test_get_agent_status(self):
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        orch = get_multi_agent_orchestrator()
        status = orch.get_agent_status()
        assert isinstance(status, list)

    def test_get_statistics(self):
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        orch = get_multi_agent_orchestrator()
        stats = orch.get_statistics()
        assert isinstance(stats, dict)


# ── Intent Predictor Tests ────────────────────────────────────────────────────

class TestIntentPredictor:
    def test_singleton(self):
        from core.intent_predictor import get_intent_predictor
        p1 = get_intent_predictor()
        p2 = get_intent_predictor()
        assert p1 is p2

    def test_predict_next_intent(self):
        from core.intent_predictor import get_intent_predictor
        predictor = get_intent_predictor()
        result = predictor.predict_next_intent(["Hello", "What's the weather?"])
        # May return None if no match, that's fine

    def test_get_statistics(self):
        from core.intent_predictor import get_intent_predictor
        predictor = get_intent_predictor()
        stats = predictor.get_statistics()
        assert isinstance(stats, dict)


# ── Personality Adapter Tests ───────────────────────────────────────────────────

class TestPersonalityAdapter:
    def test_singleton(self):
        from core.personality_adapter import get_personality_adapter
        a1 = get_personality_adapter()
        a2 = get_personality_adapter()
        assert a1 is a2

    def test_analyze_context(self):
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        result = adapter.analyze_context(["Hello!"], task_type="greeting")
        assert isinstance(result, dict)

    def test_adapt_response(self):
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        result = adapter.adapt_response("Hello!", context={"mood": "happy"})
        assert isinstance(result, str)

    def test_get_personality_profile(self):
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        profile = adapter.get_personality_profile()
        assert isinstance(profile, dict)

    def test_get_statistics(self):
        from core.personality_adapter import get_personality_adapter
        adapter = get_personality_adapter()
        stats = adapter.get_statistics()
        assert isinstance(stats, dict)


# ── Response Cache Tests ─────────────────────────────────────────────────────

class TestResponseCache:
    def test_singleton(self):
        from core.response_cache import get_response_cache
        c1 = get_response_cache()
        c2 = get_response_cache()
        assert c1 is c2

    def test_get_response(self):
        from core.response_cache import get_response_cache
        cache = get_response_cache()
        result = cache.get_response("test_query")
        # May be None if not cached

    def test_get_cache_stats(self):
        from core.response_cache import get_response_cache
        cache = get_response_cache()
        stats = cache.get_cache_stats()
        assert isinstance(stats, dict)


# ── Context Window Manager Tests ─────────────────────────────────────────────

class TestContextWindowManager:
    def test_singleton(self):
        from core.context_window_manager import get_context_window_manager
        m1 = get_context_window_manager()
        m2 = get_context_window_manager()
        assert m1 is m2

    def test_optimize_context(self):
        from core.context_window_manager import get_context_window_manager, ContextSegment
        manager = get_context_window_manager()
        segments = [
            ContextSegment(content="System prompt here", segment_type="system", priority=1.0),
            ContextSegment(content="User profile info", segment_type="user_profile", priority=0.9),
            ContextSegment(content="A very long conversation history that should be summarized" * 50,
                           segment_type="conversation", priority=0.5),
        ]
        optimized = manager.optimize_context(segments)
        assert isinstance(optimized, list)
        assert len(optimized) >= 1

    def test_summarize_old_turns(self):
        from core.context_window_manager import get_context_window_manager
        manager = get_context_window_manager()
        conversation = [
            {"speaker": "user", "text": "Hello there, how are you doing today?"},
            {"speaker": "assistant", "text": "I'm doing great!"},
            {"speaker": "user", "text": "What's the weather like?"},
            {"speaker": "assistant", "text": "I don't have real-time weather data."},
            {"speaker": "user", "text": "Tell me a joke."},
        ]
        result = manager.summarize_old_turns(conversation, keep_recent=2)
        assert "summary" in result
        assert "recent" in result
        assert len(result["recent"]) == 2

    def test_get_token_estimate(self):
        from core.context_window_manager import get_context_window_manager
        manager = get_context_window_manager()
        tokens = manager.get_token_estimate("Hello world")
        assert tokens > 0

    def test_allocate_budget(self):
        from core.context_window_manager import get_context_window_manager
        manager = get_context_window_manager()
        budget = manager.allocate_budget("chat")
        assert isinstance(budget, dict)
        assert "system" in budget

    def test_get_context_stats(self):
        from core.context_window_manager import get_context_window_manager
        manager = get_context_window_manager()
        stats = manager.get_context_stats()
        assert isinstance(stats, dict)


# ── User Pattern Detector Tests ───────────────────────────────────────────────

class TestUserPatternDetector:
    def test_singleton(self):
        from core.user_pattern_detector import get_user_pattern_detector
        d1 = get_user_pattern_detector()
        d2 = get_user_pattern_detector()
        assert d1 is d2

    def test_detect_patterns(self):
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        activities = [
            {"type": "morning_routine", "timestamp": "2024-01-01T07:00:00", "energy_level": 8},
            {"type": "deep_work", "timestamp": "2024-01-01T09:00:00", "energy_level": 9},
            {"type": "break", "timestamp": "2024-01-01T10:30:00", "energy_level": 6},
            {"type": "morning_routine", "timestamp": "2024-01-02T07:15:00", "energy_level": 7},
            {"type": "deep_work", "timestamp": "2024-01-02T09:00:00", "energy_level": 8},
            {"type": "morning_routine", "timestamp": "2024-01-03T07:00:00", "energy_level": 8},
        ]
        patterns = detector.detect_patterns(activities)
        assert isinstance(patterns, list)

    def test_get_daily_insights(self):
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        insights = detector.get_daily_insights()
        assert isinstance(insights, list)

    def test_predict_next_activity(self):
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        prediction = detector.predict_next_activity()
        assert isinstance(prediction, dict)
        assert "predicted_activity" in prediction

    def test_get_pattern_stats(self):
        from core.user_pattern_detector import get_user_pattern_detector
        detector = get_user_pattern_detector()
        stats = detector.get_pattern_stats()
        assert isinstance(stats, dict)
