# LOVE LLM configuration - updated for efficient model switching
try:
    from langchain_ollama import OllamaLLM as Ollama
except ImportError:
    from langchain_community.llms import Ollama
from core.settings import get_settings
from dotenv import load_dotenv
import os

load_dotenv()

# Load settings for model configuration
SETTINGS = get_settings()

import requests
import json

class DirectOllama:
    def __init__(self, base_url, model, temperature=0.4, timeout=300, **kwargs):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        
    def invoke(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        # Auto-detect if the prompt is asking for JSON and enforce it
        if "Return a JSON" in prompt or "JSON response" in prompt or "JSON structure" in prompt:
            payload["format"] = "json"
            
        print(f"[DirectOllama] Sending POST to {url} with model {self.model} (timeout={self.timeout})")
        try:
            import requests
            resp = requests.post(url, json=payload, timeout=self.timeout, proxies={"http": None, "https": None})
            print(f"[DirectOllama] Got response: {resp.status_code}")
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            print(f"[DirectOllama] error: {e}")
            return f"[Error connecting to Ollama: {e}]"

def get_reasoning_llm(temperature: float = None, max_tokens: int = None):
    """Get reasoning LLM with optional override parameters."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("REASONING_MODEL", SETTINGS.models.reasoning)
    
    if temperature is None:
        temperature = SETTINGS.devices.power_profiles.get(
            SETTINGS.devices.primary_device_type or 'desktop',
            type('obj', (object,), {'llm_temperature': 0.4})()
        ).llm_temperature if SETTINGS.devices.power_profiles else 0.4
    
    return DirectOllama(base_url=base_url, model=model, temperature=temperature)

def get_coding_llm(temperature: float = 0.3, max_tokens: int = None):
    """Get coding LLM with optional parameters."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("CODING_MODEL", SETTINGS.models.coding)
    return DirectOllama(base_url=base_url, model=model, temperature=temperature)

def get_embedding_model():
    """Get embedding model for vector search."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("EMBED_MODEL", SETTINGS.models.embedding)
    return DirectOllama(base_url=base_url, model=model, temperature=0.0)

def route_llm(user_input: str):
    """Route to the right model based on input type."""
    coding_keywords = [
        "code", "script", "function", "bug", "error", "python",
        "javascript", "program", "debug", "build", "fix", "refactor",
        "class", "method", "api", "endpoint", "database", "sql"
    ]
    
    device_type = SETTINGS.devices.primary_device_type
    power_profile = SETTINGS.devices.power_profiles.get(device_type) if device_type else None
    
    if power_profile and power_profile.use_quantized:
        return get_reasoning_llm(temperature=0.5)
    
    if any(word in user_input.lower() for word in coding_keywords):
        return get_coding_llm()
    
    return get_reasoning_llm()
