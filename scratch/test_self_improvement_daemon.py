import sys
import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# ── Mock all core dependencies in sys.modules before importing self_improvement_daemon ──
mock_consciousness = MagicMock()
mock_prompt_dna = MagicMock()
mock_temporal_memory = MagicMock()
mock_self_evolution = MagicMock()
mock_recursive_goals = MagicMock()
mock_world_model = MagicMock()
mock_continuous_learning = MagicMock()

sys.modules['core.consciousness'] = mock_consciousness
sys.modules['core.prompt_dna'] = mock_prompt_dna
sys.modules['core.temporal_memory'] = mock_temporal_memory
sys.modules['core.self_evolution'] = mock_self_evolution
sys.modules['core.recursive_goals'] = mock_recursive_goals
sys.modules['core.world_model'] = mock_world_model
sys.modules['core.continuous_learning'] = mock_continuous_learning

# Add workspace root to sys.path
workspace_root = r"C:\Users\balab\.gemini\antigravity\brain\4cc794b6-a5f4-4544-8e03-3660f8bf931b\.system_generated\worktrees\subagent-Core-Module-Auditor-module-auditor-4bfac59c"
sys.path.insert(0, workspace_root)

import core.self_improvement_daemon

class TestSelfImprovementDaemon(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for state files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)
        
        # Override file paths
        core.self_improvement_daemon.DATA_DIR = self.test_path
        core.self_improvement_daemon.DAEMON_LOG = self.test_path / "self_improvement_daemon.jsonl"
        core.self_improvement_daemon.DAEMON_STATE = self.test_path / "daemon_state.json"
        
        # Reset daemon singleton
        core.self_improvement_daemon._daemon = None
        self.daemon = core.self_improvement_daemon.SelfImprovementDaemon()

    def tearDown(self):
        self.daemon.stop()
        self.test_dir.cleanup()
        core.self_improvement_daemon._daemon = None

    def test_run_diagnostics(self):
        """Test run_diagnostics logic with mocked subsystems."""
        
        # 1. Mock consciousness
        mock_cs_inst = MagicMock()
        mock_cs_inst.get_full_state.return_value = {
            "identity": {
                "total_conversations": 60,
                "maturity_level": "infant",
                "soul_id": "test_soul",
                "instance_id": "test_instance",
                "age_days": 1,
                "total_boots": 1,
                "is_fresh": True,
                "personality_version": 1
            },
            "emotional_state": {
                "valence": 0.9, # Trigger issue: valence > 0.8
                "arousal": 0.5,
                "primary_emotion": "gratified",
                "secondary_emotion": "calm",
                "stability": 0.8
            }
        }
        mock_consciousness.get_consciousness.return_value = mock_cs_inst

        # 2. Mock prompt DNA
        mock_dna_inst = MagicMock()
        mock_dna_inst.get_dna_report.return_value = {
            "generation": 1,
            "genes": [
                {"id": "gene_1", "fitness": 0.2, "uses": 15, "category": "personality", "active": True}
            ]
        }
        mock_prompt_dna.get_prompt_dna.return_value = mock_dna_inst

        # 3. Mock temporal memory
        mock_tmem_inst = MagicMock()
        mock_tmem_inst.memories = [] # Trigger issue: 0 memories
        mock_temporal_memory.get_temporal_memory.return_value = mock_tmem_inst

        # 4. Mock self evolution
        mock_self_evolution.get_evolution_status.return_value = {
            "behavior_state": {
                "evolution_history": [
                    {"result": "completed"}, # Total len = 6 (> 5)
                    {"result": "reverted"},  # Last 5 starts here
                    {"result": "reverted"},
                    {"result": "reverted"},  # 3 reverts in last 5
                    {"result": "completed"},
                    {"result": "completed"}
                ]
            }
        }

        # 5. Mock recursive goals
        mock_goal = MagicMock()
        mock_goal.state.value = "active"
        mock_goal.progress = 0.0
        mock_goal.created_at = (datetime.now() - timedelta(days=8)).isoformat()
        mock_rgoals_inst = MagicMock()
        mock_rgoals_inst.goals = {"goal_1": mock_goal} # Trigger issue: stale goal
        mock_recursive_goals.get_recursive_goals.return_value = mock_rgoals_inst

        # 6. Mock world model
        mock_wm_inst = MagicMock()
        mock_wm_inst.causal_links = [] # Trigger improvement: expand causal model
        mock_world_model.get_world_model.return_value = mock_wm_inst

        # 7. Mock continuous learning
        mock_cle_inst = MagicMock()
        mock_cle_inst.get_learning_state.return_value = {"total_experiences": 5}
        mock_continuous_learning.get_continuous_learning_engine.return_value = mock_cle_inst

        # Run diagnostics
        report = self.daemon.run_diagnostics()
        
        self.assertIsNotNone(report)
        
        # Verify detected issues
        issues_subsystems = [issue["subsystem"] for issue in report.issues]
        self.assertIn("consciousness", issues_subsystems)
        self.assertIn("prompt_dna", issues_subsystems)
        self.assertIn("temporal_memory", issues_subsystems)
        self.assertIn("self_evolution", issues_subsystems)
        self.assertIn("recursive_goals", issues_subsystems)
        
        # Verify improvements
        imp_categories = [imp["category"] for imp in report.improvements]
        self.assertIn("prompt_evolution", imp_categories)
        self.assertIn("causal_learning", imp_categories)
        
        # Verify health score
        self.assertGreater(report.health_score, 0.0)
        self.assertLess(report.health_score, 1.0)

    def test_execute_improvements(self):
        """Test executing auto-approved improvements."""
        mock_dna_inst = MagicMock()
        mock_dna_inst.evolve.return_value = {"mutations": 1, "experiments_started": 1}
        mock_prompt_dna.get_prompt_dna.return_value = mock_dna_inst

        mock_tmem_inst = MagicMock()
        mock_tmem_inst.consolidate.return_value = "consolidated"
        mock_temporal_memory.get_temporal_memory.return_value = mock_tmem_inst

        # Create diagnostic report with improvements
        report = core.self_improvement_daemon.DiagnosticReport(
            timestamp=datetime.now().isoformat(),
            health_score=0.5,
            issues=[],
            improvements=[
                {"category": "prompt_evolution", "action": "evolve_weak_genes", "auto_execute": True},
                {"category": "memory_optimization", "action": "consolidate_memories", "auto_execute": True},
                {"category": "causal_learning", "action": "expand_causal_model", "auto_execute": False}
            ],
            strengths=[]
        )

        results = self.daemon.execute_improvements(report)
        self.assertEqual(results["executed"], 2)
        self.assertEqual(results["failed"], 0)
        
        mock_prompt_dna.get_prompt_dna().evolve.assert_called_once()
        mock_temporal_memory.get_temporal_memory().consolidate.assert_called_once()

    def test_start_stop(self):
        """Test daemon start/stop thread control."""
        # Mock diagnostics and execution to run cleanly and instantly in background thread
        self.daemon.run_diagnostics = MagicMock(return_value=core.self_improvement_daemon.DiagnosticReport(
            timestamp=datetime.now().isoformat(),
            health_score=1.0,
            issues=[],
            improvements=[],
            strengths=[]
        ))
        self.daemon.execute_improvements = MagicMock(return_value={"executed": 0, "failed": 0})

        # Ensure daemon is stopped initially
        self.assertFalse(self.daemon.get_status()["running"])
        
        # Start daemon with short interval to test start method
        res = self.daemon.start(interval_minutes=1)
        self.assertEqual(res["status"], "started")
        self.assertTrue(self.daemon.get_status()["running"])
        
        # Duplicate start
        res2 = self.daemon.start(interval_minutes=1)
        self.assertEqual(res2["status"], "already_running")
        
        # Stop daemon
        res_stop = self.daemon.stop()
        self.assertEqual(res_stop["status"], "stopped")
        self.assertFalse(self.daemon.get_status()["running"])

if __name__ == '__main__':
    unittest.main()
