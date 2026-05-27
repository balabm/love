"""
LOVE Evolution Systems Test Suite

Comprehensive tests for all evolution systems:
- Base evolution engine
- Meta-evolution
- Swarm evolution
- Self-coder
- Cross-instance learning
- Capability gap detector
- Autonomous CI/CD
- Evolution integration

Run with: pytest tests/test_evolution_systems.py -v
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import evolution systems
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.evolution_engine import EvolutionEngine, InteractionRecord, Mutation, Hypothesis
from core.meta_evolution import MetaEvolutionEngine, LearningStrategy, EvolutionaryPressure
from core.swarm_evolution import SwarmEvolutionEngine, Swarm, SwarmAgent
from core.self_coder import SelfCoder, CodeModification, SafetyRule
from core.cross_instance_learning import CrossInstanceLearning, SharedMutation
from core.capability_gap_detector import CapabilityGapDetector, CapabilityGap
from core.autonomous_cicd import AutonomousCICD, Deployment
from core.evolution_integration import EvolutionIntegration


# ── Base Evolution Engine Tests ───────────────────────────────────────────────

class TestEvolutionEngine:
    """Test the base evolution engine."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh evolution engine instance."""
        return EvolutionEngine()
    
    def test_singleton(self, engine):
        """Test that EvolutionEngine is a singleton."""
        engine2 = EvolutionEngine()
        assert engine is engine2
    
    def test_record_interaction(self, engine):
        """Test recording an interaction."""
        interaction = InteractionRecord(
            interaction_type="conversation",
            user_satisfaction=0.8,
            response_quality=0.7,
            latency_ms=500,
        )
        engine.record_interaction(interaction)
        
        assert len(engine._interactions) == 1
        assert engine._interactions[0].user_satisfaction == 0.8
    
    def test_generate_performance_report(self, engine):
        """Test performance report generation."""
        # Add some interactions
        for i in range(10):
            interaction = InteractionRecord(
                interaction_type="conversation",
                user_satisfaction=0.7 + (i % 3) * 0.1,
                response_quality=0.6 + (i % 2) * 0.2,
                latency_ms=400 + i * 50,
            )
            engine.record_interaction(interaction)
        
        report = engine.generate_performance_report()
        
        assert report.total_interactions == 10
        assert report.avg_quality > 0
        assert report.avg_latency_ms > 0
    
    def test_create_hypothesis(self, engine):
        """Test hypothesis creation."""
        hypothesis = engine.create_hypothesis(
            claim="Adding uncertainty prefix will reduce corrections",
            rationale="High correction rate detected",
            target_metric="correction_rate",
            predicted_delta=-0.2,
        )
        
        assert hypothesis.id in engine._hypotheses
        assert hypothesis.claim == "Adding uncertainty prefix will reduce corrections"
        assert hypothesis.status == "proposed"
    
    def test_create_mutation(self, engine):
        """Test mutation creation."""
        mutation = engine.create_mutation(
            mutation_type="prompt_injection",
            description="Add uncertainty prefix",
            prompt_modification="When uncertain, start with 'I think...'",
            injection_point="system_suffix",
        )
        
        assert mutation.id in engine._mutations
        assert mutation.active == True
        assert mutation.fitness == 0.5  # Default fitness


# ── Meta-Evolution Engine Tests ───────────────────────────────────────────────

class TestMetaEvolutionEngine:
    """Test the meta-evolution engine."""
    
    @pytest.fixture
    def meta_engine(self):
        """Create a fresh meta-evolution engine instance."""
        return MetaEvolutionEngine()
    
    def test_singleton(self, meta_engine):
        """Test that MetaEvolutionEngine is a singleton."""
        engine2 = MetaEvolutionEngine()
        assert meta_engine is engine2
    
    def test_initialize_strategies(self, meta_engine):
        """Test strategy initialization."""
        meta_engine.initialize_strategies()
        
        assert len(meta_engine._strategies) > 0
        assert any(s.name == "correction_based" for s in meta_engine._strategies.values())
    
    def test_record_strategy_outcome(self, meta_engine):
        """Test recording strategy outcomes."""
        meta_engine.initialize_strategies()
        strategy_id = list(meta_engine._strategies.keys())[0]
        
        initial_rate = meta_engine._strategies[strategy_id].success_rate
        
        # Record successful outcome
        meta_engine.record_strategy_outcome(
            strategy_id=strategy_id,
            success=True,
            effect_size=0.3,
            domain="factual_accuracy"
        )
        
        # Success rate should have changed
        assert meta_engine._strategies[strategy_id].success_rate != initial_rate
        assert meta_engine._strategies[strategy_id].usage_count == 1
    
    def test_get_best_strategy(self, meta_engine):
        """Test getting best strategy for a domain."""
        meta_engine.initialize_strategies()
        
        best = meta_engine.get_best_strategy(domain="factual_accuracy")
        
        assert best is not None
        assert best.domain_effectiveness.get("factual_accuracy", 0) > 0
    
    def test_update_evolutionary_pressures(self, meta_engine):
        """Test updating evolutionary pressures."""
        pressures = meta_engine.update_evolutionary_pressures()
        
        assert isinstance(pressures, dict)
        assert "career" in pressures or "health" in pressures
    
    def test_get_evolutionary_priorities(self, meta_engine):
        """Test getting evolutionary priorities."""
        meta_engine.update_evolutionary_pressures()
        priorities = meta_engine.get_evolutionary_priorities()
        
        assert len(priorities) > 0
        assert all(isinstance(p, tuple) and len(p) == 2 for p in priorities)


# ── Swarm Evolution Engine Tests ───────────────────────────────────────────────

class TestSwarmEvolutionEngine:
    """Test the swarm evolution engine."""
    
    @pytest.fixture
    def swarm_engine(self):
        """Create a fresh swarm evolution engine instance."""
        return SwarmEvolutionEngine()
    
    def test_singleton(self, swarm_engine):
        """Test that SwarmEvolutionEngine is a singleton."""
        engine2 = SwarmEvolutionEngine()
        assert swarm_engine is engine2
    
    def test_spawn_swarms(self, swarm_engine):
        """Test spawning swarms."""
        hypotheses = [
            {"id": "h1", "hypothesis": "Test hypothesis 1", "proposed_change": "Change 1"},
            {"id": "h2", "hypothesis": "Test hypothesis 2", "proposed_change": "Change 2"},
        ]
        
        swarm_ids = swarm_engine.spawn_swarms(hypotheses)
        
        assert len(swarm_ids) == 2
        assert all(sid in swarm_engine._swarms for sid in swarm_ids)
    
    def test_update_swarm_performance(self, swarm_engine):
        """Test updating swarm performance."""
        hypotheses = [{"id": "h1", "hypothesis": "Test", "proposed_change": "Change"}]
        swarm_ids = swarm_engine.spawn_swarms(hypotheses)
        
        swarm_id = swarm_ids[0]
        swarm_engine.update_swarm_performance(
            swarm_id=swarm_id,
            user_feedback=0.8,
            interaction_data={"type": "test"}
        )
        
        assert swarm_engine._swarms[swarm_id].collective_score > 0.5
        assert swarm_engine._swarms[swarm_id].interactions_count == 1
    
    def test_start_competition(self, swarm_engine):
        """Test starting a competition."""
        hypotheses = [
            {"id": "h1", "hypothesis": "Test 1", "proposed_change": "Change 1"},
            {"id": "h2", "hypothesis": "Test 2", "proposed_change": "Change 2"},
        ]
        swarm_ids = swarm_engine.spawn_swarms(hypotheses)
        
        comp_id = swarm_engine.start_competition(swarm_ids)
        
        assert comp_id in swarm_engine._competitions
        assert swarm_engine._competitions[comp_id].swarms == swarm_ids
    
    def test_optimize_swarm_allocation(self, swarm_engine):
        """Test optimizing swarm allocation."""
        hypotheses = [{"id": "h1", "hypothesis": "Test", "proposed_change": "Change"}]
        swarm_ids = swarm_engine.spawn_swarms(hypotheses)
        
        # Update performance to trigger reallocation
        swarm_engine.update_swarm_performance(swarm_ids[0], 0.9, {})
        
        initial_agents = len(swarm_engine._swarms[swarm_ids[0]].agents)
        swarm_engine.optimize_swarm_allocation()
        
        # Agent count may have changed
        assert len(swarm_engine._swarms[swarm_ids[0]].agents) >= 1


# ── Self-Coder Tests ───────────────────────────────────────────────────────────

class TestSelfCoder:
    """Test the self-coder module."""
    
    @pytest.fixture
    def self_coder(self):
        """Create a fresh self-coder instance."""
        return SelfCoder()
    
    def test_singleton(self, self_coder):
        """Test that SelfCoder is a singleton."""
        coder2 = SelfCoder()
        assert self_coder is coder2
    
    def test_safety_rules_loaded(self, self_coder):
        """Test that safety rules are loaded."""
        assert len(self_coder._safety_rules) > 0
        
        # Check for critical safety rules
        rule_patterns = [r.pattern for r in self_coder._safety_rules.values()]
        assert "rm -rf" in rule_patterns
    
    def test_check_safety(self, self_coder):
        """Test safety checking."""
        safe_code = "def hello():\n    return 'world'"
        unsafe_code = "import os\nos.system('rm -rf /')"
        
        is_safe, warnings = self_coder.check_safety(safe_code, "test.py")
        assert is_safe == True
        assert len(warnings) == 0
        
        is_safe, warnings = self_coder.check_safety(unsafe_code, "test.py")
        assert is_safe == False
        assert len(warnings) > 0
    
    def test_analyze_file(self, self_coder, tmp_path):
        """Test file analysis."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def test_function():
    return 42

class TestClass:
    def method(self):
        pass
""")
        
        analysis = self_coder.analyze_file(str(test_file))
        
        assert analysis.file_path == str(test_file)
        assert "test_function" in analysis.functions
        assert "TestClass" in analysis.classes
        assert analysis.lines_of_code > 0
    
    def test_generate_modification(self, self_coder, tmp_path):
        """Test modification generation."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def old_function():\n    pass")
        
        # Mock the LLM to return a modification
        with patch('core.self_coder.get_coding_llm') as mock_llm:
            mock_llm.return_value.invoke.return_value = "def new_function():\n    return 'improved'"
            
            modification = self_coder.generate_modification(
                hypothesis="Improve the function",
                file_path=str(test_file),
                improvement_type="enhancement"
            )
            
            assert modification is not None
            assert modification.file_path == str(test_file)
            assert modification.test_status == "pending"


# ── Cross-Instance Learning Tests ────────────────────────────────────────────

class TestCrossInstanceLearning:
    """Test cross-instance learning."""
    
    @pytest.fixture
    def cross_instance(self):
        """Create a fresh cross-instance learning instance."""
        return CrossInstanceLearning()
    
    def test_singleton(self, cross_instance):
        """Test that CrossInstanceLearning is a singleton."""
        instance2 = CrossInstanceLearning()
        assert cross_instance is instance2
    
    def test_instance_id_generation(self, cross_instance):
        """Test instance ID generation."""
        assert cross_instance._instance_id.startswith("love_")
        assert len(cross_instance._instance_id) > 10
    
    def test_share_mutation(self, cross_instance):
        """Test sharing a mutation."""
        mutation_id = cross_instance.share_mutation({
            "mutation_type": "enhancement",
            "description": "Test mutation",
            "prompt_modification": "Test modification",
            "success_rate": 0.8,
            "sample_size": 10,
        })
        
        assert mutation_id in cross_instance._shared_mutations
        assert cross_instance._shared_mutations[mutation_id].description == "Test mutation"
    
    def test_share_pattern(self, cross_instance):
        """Test sharing a pattern."""
        pattern_id = cross_instance.share_pattern({
            "pattern_type": "behavioral",
            "pattern_description": "Test pattern",
            "effectiveness": 0.7,
        })
        
        assert pattern_id in cross_instance._shared_patterns
        assert cross_instance._shared_patterns[pattern_id].pattern_description == "Test pattern"
    
    def test_discover_mutations(self, cross_instance):
        """Test discovering mutations."""
        # Share a mutation first
        cross_instance.share_mutation({
            "mutation_type": "enhancement",
            "description": "High success mutation",
            "prompt_modification": "Test",
            "success_rate": 0.9,
            "sample_size": 20,
            "domains": ["health"],
        })
        
        # Discover mutations
        discovered = cross_instance.discover_mutations(domain="health", min_success_rate=0.7)
        
        # Should not return our own mutation
        assert len(discovered) == 0  # Only from other instances


# ── Capability Gap Detector Tests ────────────────────────────────────────────

class TestCapabilityGapDetector:
    """Test capability gap detector."""
    
    @pytest.fixture
    def gap_detector(self):
        """Create a fresh gap detector instance."""
        return CapabilityGapDetector()
    
    def test_singleton(self, gap_detector):
        """Test that CapabilityGapDetector is a singleton."""
        detector2 = CapabilityGapDetector()
        assert gap_detector is detector2
    
    def test_detect_health_gaps(self, gap_detector):
        """Test health gap detection."""
        gaps = gap_detector._detect_health_gaps()
        
        assert isinstance(gaps, list)
        # May return empty if no health data available
    
    def test_detect_career_gaps(self, gap_detector):
        """Test career gap detection."""
        gaps = gap_detector._detect_career_gaps()
        
        assert isinstance(gaps, list)
        # May return empty if no career data available
    
    def test_prioritize_gaps(self, gap_detector):
        """Test gap prioritization."""
        # Add some test gaps
        gap1 = CapabilityGap(
            domain="health",
            subdomain="test",
            description="Test gap 1",
            severity=0.8,
            impact=0.7,
            urgency=0.6,
        )
        gap2 = CapabilityGap(
            domain="career",
            subdomain="test",
            description="Test gap 2",
            severity=0.5,
            impact=0.4,
            urgency=0.3,
        )
        
        gap_detector._gaps[gap1.id] = gap1
        gap_detector._gaps[gap2.id] = gap2
        
        prioritized = gap_detector.prioritize_gaps()
        
        assert len(prioritized) == 2
        # Higher priority gap should come first
        assert prioritized[0].id == gap1.id
    
    def test_mark_gap_resolved(self, gap_detector):
        """Test marking a gap as resolved."""
        gap = CapabilityGap(
            domain="test",
            subdomain="test",
            description="Test gap",
        )
        gap_detector._gaps[gap.id] = gap
        
        gap_detector.mark_gap_resolved(gap.id, "Fixed by user action")
        
        assert gap_detector._gaps[gap.id].status == "resolved"
        assert gap_detector._gaps[gap.id].resolution_notes == "Fixed by user action"


# ── Autonomous CI/CD Tests ───────────────────────────────────────────────────

class TestAutonomousCICD:
    """Test autonomous CI/CD."""
    
    @pytest.fixture
    def cicd(self):
        """Create a fresh CI/CD instance."""
        return AutonomousCICD()
    
    def test_singleton(self, cicd):
        """Test that AutonomousCICD is a singleton."""
        cicd2 = AutonomousCICD()
        assert cicd is cicd2
    
    def test_rollback_triggers_initialized(self, cicd):
        """Test that rollback triggers are initialized."""
        assert len(cicd._rollback_triggers) > 0
        
        # Check for critical triggers
        trigger_metrics = [t.metric_name for t in cicd._rollback_triggers]
        assert "error_rate" in trigger_metrics
        assert "satisfaction_rate" in trigger_metrics
    
    def test_create_deployment(self, cicd):
        """Test deployment creation."""
        deployment_id = cicd.create_deployment(
            modification_ids=["mod1", "mod2"],
            description="Test deployment"
        )
        
        assert deployment_id in cicd._deployments
        assert cicd._deployments[deployment_id].description == "Test deployment"
        assert len(cicd._deployments[deployment_id].stages) == 5  # build, test, staging, deploy, monitor
    
    def test_check_rollback_triggers(self, cicd):
        """Test rollback trigger checking."""
        # Create a test deployment
        deployment_id = cicd.create_deployment(["mod1"], "Test")
        deployment = cicd._deployments[deployment_id]
        
        # Set metrics that should trigger rollback
        deployment.metrics = {
            "error_rate": 0.1,  # Above 0.05 threshold
            "satisfaction_rate": 0.2,  # Below 0.3 threshold
        }
        
        should_rollback, reason = cicd._check_rollback_triggers(deployment)
        
        assert should_rollback == True
        assert "error_rate" in reason or "satisfaction_rate" in reason


# ── Evolution Integration Tests ───────────────────────────────────────────────

class TestEvolutionIntegration:
    """Test evolution integration."""
    
    @pytest.fixture
    def integration(self):
        """Create a fresh integration instance."""
        return EvolutionIntegration()
    
    def test_singleton(self, integration):
        """Test that EvolutionIntegration is a singleton."""
        integration2 = EvolutionIntegration()
        assert integration is integration2
    
    def test_get_integration_status(self, integration):
        """Test getting integration status."""
        status = integration.get_integration_status()
        
        assert "running" in status
        assert "systems" in status
        assert "statistics" in status
        assert "base_evolution" in status["systems"]
    
    def test_get_current_state(self, integration):
        """Test getting current state."""
        state = integration._get_current_state()
        
        assert isinstance(state, dict)


# ── Integration Tests ───────────────────────────────────────────────────────

class TestEvolutionIntegration:
    """Test integration between evolution systems."""
    
    def test_meta_evolution_with_base_evolution(self):
        """Test meta-evolution working with base evolution."""
        meta_engine = MetaEvolutionEngine()
        base_engine = EvolutionEngine()
        
        # Initialize strategies
        meta_engine.initialize_strategies()
        
        # Record some interactions in base engine
        for i in range(5):
            interaction = InteractionRecord(
                interaction_type="conversation",
                user_satisfaction=0.8,
                response_quality=0.7,
            )
            base_engine.record_interaction(interaction)
        
        # Generate performance report
        report = base_engine.generate_performance_report()
        
        assert report.total_interactions == 5
    
    def test_swarm_with_hypotheses(self):
        """Test swarm evolution with hypotheses."""
        swarm_engine = SwarmEvolutionEngine()
        
        hypotheses = [
            {"id": "h1", "hypothesis": "Test 1", "proposed_change": "Change 1"},
            {"id": "h2", "hypothesis": "Test 2", "proposed_change": "Change 2"},
        ]
        
        swarm_ids = swarm_engine.spawn_swarms(hypotheses)
        
        # Update performance
        for swarm_id in swarm_ids:
            swarm_engine.update_swarm_performance(swarm_id, 0.7, {})
        
        # Start competition
        comp_id = swarm_engine.start_competition(swarm_ids)
        
        assert comp_id in swarm_engine._competitions


# ── Performance Tests ───────────────────────────────────────────────────────

class TestEvolutionPerformance:
    """Test performance of evolution systems."""
    
    def test_interaction_recording_performance(self):
        """Test that interaction recording is fast."""
        engine = EvolutionEngine()
        
        start = time.time()
        for i in range(100):
            interaction = InteractionRecord(
                interaction_type="conversation",
                user_satisfaction=0.7,
                response_quality=0.6,
            )
            engine.record_interaction(interaction)
        
        duration = time.time() - start
        
        # Should record 100 interactions in less than 1 second
        assert duration < 1.0
    
    def test_hypothesis_generation_performance(self):
        """Test that hypothesis generation is reasonable."""
        engine = EvolutionEngine()
        
        start = time.time()
        for i in range(10):
            engine.create_hypothesis(
                claim=f"Test hypothesis {i}",
                rationale="Test rationale",
                target_metric="test_metric",
                predicted_delta=0.1,
            )
        
        duration = time.time() - start
        
        # Should generate 10 hypotheses in less than 0.5 seconds
        assert duration < 0.5


# ── Run Tests ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])