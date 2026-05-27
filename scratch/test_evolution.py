import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add workspace root to path
WORKSPACE_DIR = r"C:\Users\balab\.gemini\antigravity\brain\4cc794b6-a5f4-4544-8e03-3660f8bf931b\.system_generated\worktrees\subagent-Core-Module-Auditor-module-auditor-718cf717"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# Mock external/heavy dependencies
sys.modules['core.llm'] = MagicMock()
sys.modules['core.neural_bus'] = MagicMock()

class TestEvolutionEngine(unittest.TestCase):
    
    @patch('core.evolution_engine.GENOME_FILE')
    @patch('core.evolution_engine.METRICS_FILE')
    @patch('core.evolution_engine.EXPERIMENTS_FILE')
    @patch('core.evolution_engine.HISTORY_FILE')
    def setUp(self, mock_history, mock_experiments, mock_metrics, mock_genome):
        # Prevent actually writing to files during tests
        mock_genome.exists.return_value = False
        mock_metrics.exists.return_value = False
        mock_experiments.exists.return_value = False
        mock_history.exists.return_value = False
        
        # Reset singleton instance
        from core.evolution_engine import EvolutionEngine
        EvolutionEngine._instance = None
        
        self.engine = EvolutionEngine()
        
    def test_record_and_get_performance(self):
        # Initially no metrics
        rpt = self.engine.get_performance_metrics()
        self.assertEqual(rpt.total_interactions, 0)
        
        # Record some interactions
        self.engine.record_interaction(interaction_type="chat", response_quality=0.8, latency_ms=120.0)
        self.engine.record_interaction(interaction_type="chat", response_quality=0.9, latency_ms=80.0)
        self.engine.record_interaction(interaction_type="tool", response_quality=0.4, latency_ms=300.0, error_occurred=True)
        
        rpt = self.engine.get_performance_metrics()
        self.assertEqual(rpt.total_interactions, 3)
        self.assertAlmostEqual(rpt.avg_quality, (0.8 + 0.9 + 0.4) / 3.0)
        self.assertAlmostEqual(rpt.avg_latency_ms, (120.0 + 80.0 + 300.0) / 3.0)
        self.assertAlmostEqual(rpt.error_rate, 1.0 / 3.0)
        
    def test_validate_mutation(self):
        # Create a mock mutation
        from core.evolution_engine import Mutation
        mut = Mutation(
            mutation_type="tone_shift",
            description="Test Mutation",
            prompt_modification="Be polite",
            active=True
        )
        self.engine._mutations[mut.id] = mut
        
        # Insufficient data initially (needs 5 post-interactions)
        res = self.engine.validate_mutation(mut.id)
        self.assertEqual(res.get("status"), "insufficient_data")
        
        # Let's populate interactions: pre and post
        from datetime import datetime, timedelta
        
        # applied_at is now, let's make pre-interactions
        pre_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        post_time = (datetime.now() + timedelta(minutes=10)).isoformat()
        
        # Set mutation applied_at to datetime.now()
        mut.applied_at = datetime.now().isoformat()
        
        # Pre-interactions (mean around 0.7 with variance)
        pre_qualities = [0.68, 0.72, 0.7, 0.69, 0.71]
        for q in pre_qualities:
            rec = self.engine.record_interaction(response_quality=q)
            rec.timestamp = pre_time
            
        # Post-interactions (mean around 0.9 with variance)
        post_qualities = [0.88, 0.92, 0.9, 0.89, 0.91, 0.9]
        for q in post_qualities:
            rec = self.engine.record_interaction(response_quality=q)
            rec.timestamp = post_time
            
        mut.interactions_since_applied = 6
        
        res = self.engine.validate_mutation(mut.id)
        self.assertTrue(res.get("valid"))
        self.assertGreater(res.get("post_mean"), res.get("pre_mean"))
        self.assertEqual(res.get("recommendation"), "keep")
        
if __name__ == '__main__':
    unittest.main()
