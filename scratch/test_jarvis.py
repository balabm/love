import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add workspace root to path
WORKSPACE_DIR = r"C:\Users\balab\.gemini\antigravity\brain\4cc794b6-a5f4-4544-8e03-3660f8bf931b\.system_generated\worktrees\subagent-Core-Module-Auditor-module-auditor-718cf717"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# Mock external and internal heavy modules
sys.modules['chromadb'] = MagicMock()
sys.modules['langchain_ollama'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.llms'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['psutil'] = MagicMock()
sys.modules['core.voice_loop'] = MagicMock()
sys.modules['core.context_engine'] = MagicMock()
sys.modules['api.main'] = MagicMock()
sys.modules['core.consciousness'] = MagicMock()

class TestJarvisProtocol(unittest.TestCase):
    @patch('core.jarvis_protocol.get_live_context')
    @patch('core.jarvis_protocol.get_prompt_context')
    @patch('core.jarvis_protocol.route_llm')
    def test_think_basic(self, mock_route_llm, mock_get_prompt_context, mock_get_live_context):
        # Setup mocks
        mock_ctx = MagicMock()
        mock_ctx.activity = "active"
        mock_ctx.active_window = "VS Code"
        mock_ctx.cpu_percent = 15.0
        mock_ctx.stress_score = 10
        mock_get_live_context.return_value = mock_ctx
        
        mock_get_prompt_context.return_value = "System context is clean."
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = '''{
            "internal_monologue": "Karthi is working on code.",
            "proactive_speech": null,
            "background_action": null,
            "action_plan": null
        }'''
        mock_route_llm.return_value = mock_llm
        
        # Mock consciousness return value
        mock_consciousness = MagicMock()
        mock_consciousness.get_self_narrative.return_value = "I am LOVE."
        mock_consciousness.get_emotional_context_for_prompt.return_value = "I feel happy."
        sys.modules['core.consciousness'].get_consciousness.return_value = mock_consciousness
        
        from core.jarvis_protocol import NeuralCortex
        cortex = NeuralCortex(interval_seconds=45)
        
        # We also need to mock open() to not write to settings.data_dir / "internal_monologue.log" during tests
        with patch('core.jarvis_protocol.SETTINGS') as mock_settings:
            mock_settings.data_dir = MagicMock()
            
            with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
                cortex._think()
                
                # Check monologue log was written
                mock_file.assert_called_once()
                self.assertEqual(cortex.last_thought, "Karthi is working on code.")

    @patch('core.jarvis_protocol.get_live_context')
    @patch('core.jarvis_protocol.route_llm')
    def test_think_with_consciousness_none(self, mock_route_llm, mock_get_live_context):
        # Setup mocks to return None consciousness
        mock_ctx = MagicMock()
        mock_ctx.activity = "active"
        mock_get_live_context.return_value = mock_ctx
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = '''{
            "internal_monologue": "Thinking...",
            "proactive_speech": null,
            "background_action": null,
            "action_plan": null
        }'''
        mock_route_llm.return_value = mock_llm
        
        # Make consciousness get_consciousness return None
        sys.modules['core.consciousness'].get_consciousness.return_value = None
        
        from core.jarvis_protocol import NeuralCortex
        cortex = NeuralCortex(interval_seconds=45)
        
        # Test that _think doesn't raise AttributeError when consciousness is None
        with patch('core.jarvis_protocol.SETTINGS') as mock_settings, \
             patch('builtins.open', unittest.mock.mock_open()):
            mock_settings.data_dir = MagicMock()
            
            # This should run without throwing AttributeError
            cortex._think()
            self.assertEqual(cortex.last_thought, "Thinking...")

if __name__ == '__main__':
    unittest.main()
