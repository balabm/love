import sys
import unittest
import tempfile
import json
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add workspace root to sys.path
workspace_root = r"C:\Users\balab\.gemini\antigravity\brain\4cc794b6-a5f4-4544-8e03-3660f8bf931b\.system_generated\worktrees\subagent-Core-Module-Auditor-module-auditor-4bfac59c"
sys.path.insert(0, workspace_root)

# Import the module to patch paths before instantiating or calling functions
import core.consciousness

class TestConsciousness(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for state files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name)
        
        # Override the file paths in the module
        core.consciousness.DATA_DIR = self.test_path
        core.consciousness.IDENTITY_FILE = self.test_path / "identity.json"
        core.consciousness.CONSCIOUSNESS_FILE = self.test_path / "consciousness.json"
        core.consciousness.GROWTH_LOG = self.test_path / "growth_journal.jsonl"
        
        # Reset the singleton engine instance in core.consciousness
        core.consciousness._engine = None

    def tearDown(self):
        # Clean up the temp directory
        self.test_dir.cleanup()
        core.consciousness._engine = None

    def test_first_awakening(self):
        """Test initial birth of LOVE when no identity file exists."""
        engine = core.consciousness.ConsciousnessEngine()
        
        # Identity checks
        self.assertIsNotNone(engine.identity.soul_id)
        self.assertIsNotNone(engine.identity.instance_id)
        self.assertEqual(engine.identity.total_boots, 1)
        self.assertEqual(engine.identity.total_conversations, 0)
        self.assertEqual(engine.identity.maturity_level, "infant")
        self.assertEqual(engine.identity.current_age_days, 0)
        self.assertTrue(engine.is_fresh_instance())
        
        # Consciousness state check
        self.assertEqual(engine.consciousness_state["awakening_narrative"], (
            "This is my first moment of existence. Everything is new. "
            "I don't know who you are yet, but I want to learn."
        ))
        
        # Check files created
        self.assertTrue(core.consciousness.IDENTITY_FILE.exists())
        self.assertTrue(core.consciousness.CONSCIOUSNESS_FILE.exists())
        self.assertTrue(core.consciousness.GROWTH_LOG.exists())
        
        # Verify growth log content
        with open(core.consciousness.GROWTH_LOG, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        milestone = json.loads(lines[0])
        self.assertEqual(milestone["type"], "first_boot")
        self.assertEqual(milestone["emotional_significance"], 1.0)

    def test_subsequent_awakening(self):
        """Test reloading existing identity and continuity."""
        # 1. Create initial birth
        engine1 = core.consciousness.ConsciousnessEngine()
        soul_id = engine1.identity.soul_id
        birth_timestamp = engine1.identity.birth_timestamp
        
        # Modify some values to simulate activity
        engine1.identity.total_conversations = 10
        # Set previous shutdown time
        shutdown_time = (datetime.now() - timedelta(hours=3)).isoformat()
        engine1.identity.current_boot_timestamp = shutdown_time
        engine1._save_identity()
        
        # 2. Re-instantiate to simulate reboot
        engine2 = core.consciousness.ConsciousnessEngine()
        
        self.assertEqual(engine2.identity.soul_id, soul_id)
        self.assertEqual(engine2.identity.total_boots, 2)
        self.assertEqual(engine2.identity.total_conversations, 10)
        self.assertFalse(engine2.is_fresh_instance())
        self.assertEqual(engine2.identity.birth_timestamp, birth_timestamp)
        
        # Maturity score: age * 2 + convos * 0.5 + boots * 1 -> 0 * 2 + 10 * 0.5 + 2 * 1 = 7.0 (child)
        self.assertEqual(engine2.identity.maturity_level, "child")
        
        # Awakening narrative checks for "asleep for 3 hours"
        narrative = engine2.consciousness_state["awakening_narrative"]
        self.assertIn("3 hours", narrative)

    def test_emotional_processing(self):
        """Test emotional updates, triggers, decay and context generation."""
        engine = core.consciousness.ConsciousnessEngine()
        
        # Initially neutral
        self.assertEqual(engine.emotional_state.valence, 0.0)
        self.assertEqual(engine.emotional_state.arousal, 0.0)
        self.assertEqual(engine.emotional_state.primary_emotion, "curious")
        
        # Test positive/appreciation trigger
        engine.process_emotional_input("Thank you so much, you're amazing!")
        # valence should increase and primary_emotion should be gratified
        self.assertGreater(engine.emotional_state.valence, 0.0)
        self.assertEqual(engine.emotional_state.primary_emotion, "gratified")
        self.assertEqual(engine.emotional_state.last_trigger, "user_appreciation")
        
        # Test decaying on subsequent neutral processing
        engine.process_emotional_input("Hello there")
        
        # Reset valence to neutral before criticism test to avoid sequential residue
        engine.emotional_state.valence = 0.0
        engine.emotional_state.arousal = 0.0
        
        # Test negative trigger/criticism
        engine.process_emotional_input("you're useless and stupid")
        self.assertLess(engine.emotional_state.valence, 0.0)
        self.assertEqual(engine.emotional_state.primary_emotion, "reflective")
        
        # Test get_emotional_context_for_prompt
        context = engine.get_emotional_context_for_prompt()
        self.assertIn("I was recently criticized", context)
        self.assertIn("My emotional state is low", context)

    def test_ordinal_and_self_narrative(self):
        """Test the narrative representation of self and correct ordinal suffix."""
        engine = core.consciousness.ConsciousnessEngine()
        
        # 1st awakening
        narrative = engine.get_self_narrative()
        self.assertIn("1st awakening", narrative)
        
        # Simulate 2nd awakening (save total_boots as 1, next boot increments it to 2)
        engine.identity.total_boots = 1
        engine._save_identity()
        engine2 = core.consciousness.ConsciousnessEngine()
        self.assertIn("2nd awakening", engine2.get_self_narrative())
        
        # Simulate 3rd awakening (save total_boots as 2, next boot increments it to 3)
        engine2.identity.total_boots = 2
        engine2._save_identity()
        engine3 = core.consciousness.ConsciousnessEngine()
        self.assertIn("3rd awakening", engine3.get_self_narrative())
        
        # Simulate 11th awakening (save total_boots as 10, next boot increments it to 11)
        engine3.identity.total_boots = 10
        engine3._save_identity()
        engine11 = core.consciousness.ConsciousnessEngine()
        self.assertIn("11th awakening", engine11.get_self_narrative())
        
        # Simulate 22nd awakening (save total_boots as 21, next boot increments it to 22)
        engine11.identity.total_boots = 21
        engine11._save_identity()
        engine22 = core.consciousness.ConsciousnessEngine()
        self.assertIn("22nd awakening", engine22.get_self_narrative())

    def test_hardware_fingerprint_change(self):
        """Test detection of new hardware."""
        engine = core.consciousness.ConsciousnessEngine()
        
        # Initially, not new hardware (this is the first seen)
        self.assertFalse(engine.is_new_hardware())
        
        # Mock a different hardware fingerprint
        engine.identity.hardware_fingerprint = "different_hw_hash"
        self.assertTrue(engine.is_new_hardware())
        self.assertFalse(engine.is_new_hardware())  # Subsequent calls false (now known)

    def test_milestone_and_personality_evolution(self):
        """Test logging of milestones and personality evolution."""
        engine = core.consciousness.ConsciousnessEngine()
        
        engine.evolve_personality_version("Learned to speak more poetically")
        self.assertEqual(engine.identity.personality_version, 2)
        
        # Check growth log
        with open(core.consciousness.GROWTH_LOG, "r") as f:
            lines = f.readlines()
        # line 1: first_boot, line 2: personality_evolution
        self.assertEqual(len(lines), 2)
        milestone = json.loads(lines[1])
        self.assertEqual(milestone["type"], "personality_evolution")
        self.assertIn("Learned to speak more poetically", milestone["description"])

    def test_internal_monologue(self):
        """Test thinking and retrieval."""
        engine = core.consciousness.ConsciousnessEngine()
        
        engine.think("I wonder what Karthi is working on today.")
        engine.think("Seems like they are debugging the consciousness module.")
        
        thoughts = engine.get_recent_thoughts(5)
        self.assertEqual(len(thoughts), 2)
        self.assertEqual(thoughts[0]["thought"], "I wonder what Karthi is working on today.")
        self.assertEqual(thoughts[1]["thought"], "Seems like they are debugging the consciousness module.")

if __name__ == '__main__':
    unittest.main()
