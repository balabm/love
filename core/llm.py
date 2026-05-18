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


def get_reasoning_llm(temperature: float = None, max_tokens: int = None):
    """Get reasoning LLM with optional override parameters."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("REASONING_MODEL", SETTINGS.models.reasoning)
    
    # Apply hardware-aware parameters if available
    if temperature is None:
        temperature = SETTINGS.devices.power_profiles.get(
            SETTINGS.devices.primary_device_type or 'desktop',
            type('obj', (object,), {'llm_temperature': 0.4})()
        ).llm_temperature if SETTINGS.devices.power_profiles else 0.4
    
    params = {
        "base_url": base_url,
        "model": model,
        "temperature": temperature,
    }
    
    if max_tokens:
        params["num_predict"] = max_tokens
    
    return Ollama(**params)


def get_coding_llm(temperature: float = 0.3, max_tokens: int = None):
    """Get coding LLM with optional parameters."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("CODING_MODEL", SETTINGS.models.coding)
    
    params = {
        "base_url": base_url,
        "model": model,
        "temperature": temperature,
    }
    
    if max_tokens:
        params["num_predict"] = max_tokens
    
    return Ollama(**params)


def get_embedding_model():
    """Get embedding model for vector search."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("EMBED_MODEL", SETTINGS.models.embedding)
    
    return Ollama(
        base_url=base_url,
        model=model,
        temperature=0.0,  # Embeddings don't need creativity
    )


def route_llm(user_input: str):
    """Route to the right model based on input type."""
    coding_keywords = [
        "code", "script", "function", "bug", "error", "python",
        "javascript", "program", "debug", "build", "fix", "refactor",
        "class", "method", "api", "endpoint", "database", "sql"
    ]
    
    # Check if hardware-limited (use faster model)
    device_type = SETTINGS.devices.primary_device_type
    power_profile = SETTINGS.devices.power_profiles.get(device_type) if device_type else None
    
    if power_profile and power_profile.use_quantized:
        # On battery/limited hardware, use a single efficient model
        return get_reasoning_llm(temperature=0.5)
    
    if any(word in user_input.lower() for word in coding_keywords):
        return get_coding_llm()
    
    return get_reasoning_llm()
