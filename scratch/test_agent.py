import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Define mock classes
class MockOllama:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    def invoke(self, prompt, **kwargs):
        return "Mock response <think>thought</think>"
    def __call__(self, prompt, **kwargs):
        return "Mock response <think>thought</think>"

# Mock the heavy modules
sys.modules['chromadb'] = MagicMock()
sys.modules['langchain_ollama'] = MagicMock()
sys.modules['langchain_ollama'].OllamaLLM = MockOllama
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.llms'] = MagicMock()
sys.modules['langchain_community.llms'].Ollama = MockOllama
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.language_models'] = MagicMock()

# Mock psutil as well since context engines use it
sys.modules['psutil'] = MagicMock()

# Add workspace to path
WORKSPACE_DIR = r"C:\Users\balab\.gemini\antigravity\brain\4cc794b6-a5f4-4544-8e03-3660f8bf931b\.system_generated\worktrees\subagent-Core-Module-Auditor-module-auditor-718cf717"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

class TestAgent(unittest.TestCase):
    def test_extract_thinking(self):
        from core.agent import extract_thinking
        text = "<think>this is thinking</think>this is the response"
        thinking, response = extract_thinking(text)
        self.assertEqual(thinking, "this is thinking")
        self.assertEqual(response, "this is the response")

        text_no_think = "just response"
        thinking, response = extract_thinking(text_no_think)
        self.assertEqual(thinking, "")
        self.assertEqual(response, "just response")

    def test_clean_response(self):
        from core.agent import clean_response
        
        # Test markdown stripping
        self.assertEqual(clean_response("**bold** and *italic*"), "bold and italic")
        
        # Test generic intros stripping
        self.assertEqual(clean_response("Here's a breakdown of your day: You are busy."), "You are busy.")
        
        # Test generic closings stripping
        self.assertEqual(clean_response("I hope this summary helps!"), "")
        
        # Test bullet points conversion
        bullet_text = "- First point\n- Second point"
        self.assertEqual(clean_response(bullet_text), "First point Second point")

    def test_ltm_available_and_imports(self):
        # We check LTM_AVAILABLE after patching or mock imports
        import core.agent as agent
        print(f"\n[Test] LTM_AVAILABLE in core.agent: {agent.LTM_AVAILABLE}")
        
        # Our check on the fixes:
        self.assertTrue(hasattr(agent, 'remember') or not agent.LTM_AVAILABLE, "remember should be defined/imported if LTM_AVAILABLE")
        self.assertTrue(hasattr(agent, 'format_memory_for_chat') or not agent.LTM_AVAILABLE, "format_memory_for_chat should be defined/imported if LTM_AVAILABLE")

if __name__ == '__main__':
    unittest.main()
