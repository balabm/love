from core.settings import get_settings
from dotenv import load_dotenv
import os
import requests
import json
import re

load_dotenv()
SETTINGS = get_settings()

FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "qwen2.5-coder:7b")
FALLBACK_SYSTEM_PREFIX = "[SYSTEM UNDER LOAD - keep answer to 1-2 sentences, no deep reasoning] "
OLLAMA_AUTO_FALLBACK = os.getenv("OLLAMA_AUTO_FALLBACK", "false").lower() in ("1", "true", "yes")
OLLAMA_FORCE_HIGH_QUALITY = os.getenv("OLLAMA_FORCE_HIGH_QUALITY", "false").lower() in ("1", "true", "yes")

# Safety limits to prevent local hangs while preserving rich context.
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "42000"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "90"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "512"))


def _is_system_under_load() -> bool:
    """Check if host system is under heavy load via resource governor."""
    try:
        from core.resource_governor import get_resource_governor
        return get_resource_governor().is_under_load()
    except Exception:
        return False


def _should_use_fallback() -> bool:
    """Decide whether fallback model switching is allowed."""
    if OLLAMA_FORCE_HIGH_QUALITY:
        print("[LLM] OLLAMA_FORCE_HIGH_QUALITY enabled - bypassing fallback and quantized profiles.")
        return False
    return OLLAMA_AUTO_FALLBACK and _is_system_under_load()


_available_models: set = set()
_model_check_done: bool = False

def _check_model_exists(model: str, base_url: str) -> bool:
    """Check if a model is available in Ollama, with caching."""
    global _available_models, _model_check_done
    if _model_check_done and _available_models:
        return model in _available_models
    try:
        import requests
        resp = requests.get(f"{base_url}/api/tags", timeout=3, proxies={"http": None, "https": None})
        if resp.status_code == 200:
            data = resp.json()
            _available_models = {m.get("name", "") for m in data.get("models", [])}
            _model_check_done = True
            return model in _available_models
    except Exception:
        pass
    # If we can't check, assume it exists (fail open)
    return True


def _effective_prompt_limit() -> int:
    """
    Cap prompt chars using both explicit override and ctx window approximation.
    Approximation: ~4 chars/token with a little headroom.
    """
    ctx_limit = max(12000, int(OLLAMA_NUM_CTX * 3.8))
    return max(12000, min(MAX_PROMPT_CHARS, ctx_limit))


class DirectOllama:
    def __init__(self, base_url, model, temperature=0.4, timeout=None, system_prefix: str = "", **kwargs):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout if timeout is not None else OLLAMA_TIMEOUT
        self.system_prefix = system_prefix

    def invoke(self, prompt: str) -> str:
        if self.system_prefix:
            prompt = self.system_prefix + prompt

        # Split system prompt and user prompt
        match = re.search(r"\n\n[^\n]{1,50}:\s", prompt)
        if match:
            system_prompt = prompt[:match.start()].rstrip()
            conversation = prompt[match.start():].strip()
        else:
            system_prompt = prompt[:4000].rstrip()
            conversation = prompt[4000:].strip()

        prompt_limit = _effective_prompt_limit()
        if len(prompt) > prompt_limit:
            separator = "\n\n[... prior context trimmed to fit model window ...]\n\n"
            available = prompt_limit - len(system_prompt) - len(separator)
            tail_length = max(2000, available)
            if tail_length < 2000:
                tail_length = 2000
                if len(system_prompt) + tail_length + len(separator) > prompt_limit:
                    system_prompt = system_prompt[: max(0, prompt_limit - tail_length - len(separator))].rstrip()

            conversation = separator + conversation[-tail_length:]
            prompt = system_prompt + conversation
            print(f"[DirectOllama] Prompt truncated to {len(prompt)} chars (limit {prompt_limit})")

        with open('data/last_prompt.txt', 'w', encoding='utf-8') as f:
            f.write(f"SYSTEM:\n{system_prompt}\n\nUSER:\n{conversation}")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": conversation,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": OLLAMA_NUM_CTX,
                "num_predict": OLLAMA_NUM_PREDICT,
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

    system_prefix = ""
    if _should_use_fallback():
        model = FALLBACK_MODEL
        system_prefix = FALLBACK_SYSTEM_PREFIX
        print(f"[LLM] System under load - downgrading to {model}")
    elif not _check_model_exists(model, base_url):
        # Model not available, fall back to a known working model
        available_fallbacks = ["deepseek-r1:7b", "qwen2.5:0.5b", "llama3.2:1b", "qwen2.5-coder:1.5b"]
        fallback = next((m for m in available_fallbacks if _check_model_exists(m, base_url)), FALLBACK_MODEL)
        print(f"[LLM] Model '{model}' not found in Ollama. Falling back to: {fallback}")
        model = fallback
    else:
        print(f"[LLM] Selected reasoning model: {model}")
    return DirectOllama(base_url=base_url, model=model, temperature=temperature, system_prefix=system_prefix)

def get_coding_llm(temperature: float = 0.3, max_tokens: int = None):
    """Get coding LLM with optional parameters."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("CODING_MODEL", SETTINGS.models.coding)
    system_prefix = ""
    if _should_use_fallback():
        model = FALLBACK_MODEL
        system_prefix = FALLBACK_SYSTEM_PREFIX
        print(f"[LLM] System under load - downgrading coding model to {model}")
    elif not _check_model_exists(model, base_url):
        available_fallbacks = ["qwen2.5-coder:7b", "qwen2.5-coder:1.5b", "deepseek-r1:7b"]
        fallback = next((m for m in available_fallbacks if _check_model_exists(m, base_url)), FALLBACK_MODEL)
        print(f"[LLM] Coding model '{model}' not found. Falling back to: {fallback}")
        model = fallback
    else:
        print(f"[LLM] Selected coding model: {model}")
    return DirectOllama(base_url=base_url, model=model, temperature=temperature, system_prefix=system_prefix)

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

    if power_profile and power_profile.use_quantized and not OLLAMA_FORCE_HIGH_QUALITY:
        print("[LLM] Using quantized-mode profile for lower-cost reasoning.")
        return get_reasoning_llm(temperature=0.5)

    if any(word in user_input.lower() for word in coding_keywords):
        return get_coding_llm()

    return get_reasoning_llm()

def get_current_model_info() -> dict:
    """Return which models are currently active and whether we're in fallback mode."""
    under_load = _is_system_under_load()
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    return {
        "under_load": under_load,
        "auto_fallback": OLLAMA_AUTO_FALLBACK,
        "force_high_quality": OLLAMA_FORCE_HIGH_QUALITY,
        "reasoning_model": FALLBACK_MODEL if under_load else os.getenv("REASONING_MODEL", SETTINGS.models.reasoning),
        "coding_model": FALLBACK_MODEL if under_load else os.getenv("CODING_MODEL", SETTINGS.models.coding),
        "fallback_model": FALLBACK_MODEL,
        "base_url": base_url,
    }


