from core.settings import get_settings
from dotenv import load_dotenv
import os
import requests
import json
import re
import threading
import hashlib
import time
from functools import lru_cache
from core.execution_guard import log_error

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

# Throttle concurrent LLM calls to prevent Ollama overload
# Only 1 request hits Ollama at a time on local single-GPU setups
_LLM_SEMAPHORE = threading.Semaphore(1)

# Circuit breaker: track consecutive timeouts and enter cooldown
_CIRCUIT_LOCK = threading.Lock()
_consecutive_timeouts = 0
_circuit_cooldown_until = 0.0
_CIRCUIT_LAST_PRINT = 0.0  # rate-limit "Circuit breaker active" spam

# Prompt cache: 30-second TTL deduplication for duplicate background calls
_PROMPT_CACHE: dict = {}
_PROMPT_CACHE_TTL = 30  # seconds
_PROMPT_CACHE_LOCK = threading.Lock()


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

# Track which models are being pulled so we don't spam /api/pull
_pulling_lock = threading.Lock()
_pulling_models: set = set()


def _check_model_exists(model: str, base_url: str) -> bool:
    """Check if a model is available in Ollama, with caching."""
    global _available_models, _model_check_done
    if _model_check_done:
        return model in _available_models
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=2, proxies={"http": None, "https": None})
        if resp.status_code == 200:
            data = resp.json()
            _available_models = {m.get("name", "") for m in data.get("models", [])}
            _model_check_done = True
            return model in _available_models
    except Exception:
        pass  # Ollama not available; cache empty result to prevent repeated timeouts
    _model_check_done = True
    _available_models = set()
    return True  # fail open


def _auto_pull_model(model: str, base_url: str) -> None:
    """Start a background thread to pull a missing Ollama model. Non-blocking."""
    with _pulling_lock:
        if model in _pulling_models:
            return
        _pulling_models.add(model)

    def _do_pull():
        try:
            print(f"[LLM] Auto-pulling missing model '{model}' from Ollama...")
            resp = requests.post(
                f"{base_url}/api/pull",
                json={"name": model, "stream": False},
                timeout=300,
                proxies={"http": None, "https": None},
            )
            if resp.status_code == 200:
                print(f"[LLM] Successfully pulled model '{model}'")
                # Invalidate cache so next check picks it up
                global _model_check_done
                _model_check_done = False
            else:
                print(f"[LLM] Pull failed for '{model}': {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"[LLM] Pull error for '{model}': {e}")
        finally:
            with _pulling_lock:
                _pulling_models.discard(model)

    threading.Thread(target=_do_pull, daemon=True, name=f"pull-{model}").start()


def _effective_prompt_limit() -> int:
    """
    Cap prompt chars using both explicit override and ctx window approximation.
    Approximation: ~4 chars/token with a little headroom.
    """
    ctx_limit = max(12000, int(OLLAMA_NUM_CTX * 3.8))
    return max(12000, min(MAX_PROMPT_CHARS, ctx_limit))


class DirectOllama:
    def __init__(self, base_url, model, temperature=0.4, timeout=None, system_prefix: str = "", fallback_model: str = None, **kwargs):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.system_prefix = system_prefix
        self.fallback_model = fallback_model
        # Reasoning models (especially deepseek-r1) need more time
        if timeout is not None:
            self.timeout = timeout
        elif "deepseek-r1" in model.lower():
            self.timeout = max(OLLAMA_TIMEOUT, 120)
        else:
            self.timeout = OLLAMA_TIMEOUT

    def _build_payload(self, system_prompt: str, conversation: str, prompt: str) -> dict:
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
        return payload

    def _send(self, payload: dict) -> str:
        global _consecutive_timeouts, _circuit_cooldown_until

        # Circuit breaker check
        with _CIRCUIT_LOCK:
            if time.time() < _circuit_cooldown_until:
                remaining = int(_circuit_cooldown_until - time.time())
                global _CIRCUIT_LAST_PRINT
                if time.time() - _CIRCUIT_LAST_PRINT > 10:
                    _CIRCUIT_LAST_PRINT = time.time()
                    print(f"[DirectOllama] Circuit breaker active — cooling down for {remaining}s")
                return f"[Ollama circuit breaker: cooling down for {remaining}s]"

        url = f"{self.base_url}/api/generate"
        print(f"[DirectOllama] Sending POST to {url} with model {payload['model']} (timeout={self.timeout})")

        # Prompt cache check (skip for chat/short prompts)
        cache_key = None
        prompt_text = payload.get("prompt", "")
        if len(prompt_text) > 200:
            cache_key = hashlib.sha256(f"{payload['model']}:{prompt_text[:1000]}".encode()).hexdigest()
            with _PROMPT_CACHE_LOCK:
                cached = _PROMPT_CACHE.get(cache_key)
                if cached and (time.time() - cached["ts"]) < _PROMPT_CACHE_TTL:
                    print(f"[DirectOllama] Cache hit — returning cached response")
                    return cached["response"]

        acquired = _LLM_SEMAPHORE.acquire(timeout=15)
        if not acquired:
            print(f"[DirectOllama] Semaphore timeout — Ollama is overloaded, fast-failing")
            with _CIRCUIT_LOCK:
                _consecutive_timeouts += 1
                _circuit_cooldown_until = time.time() + min(30 * (2 ** min(_consecutive_timeouts - 1, 3)), 300)
            return f"[Ollama overloaded: request timed out waiting for slot]"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout, proxies={"http": None, "https": None})
            print(f"[DirectOllama] Got response: {resp.status_code}")
            resp.raise_for_status()
            response_text = resp.json().get("response", "")
            # Reset circuit breaker on success
            with _CIRCUIT_LOCK:
                _consecutive_timeouts = 0
                _circuit_cooldown_until = 0.0
            # Cache the response
            if cache_key:
                with _PROMPT_CACHE_LOCK:
                    _PROMPT_CACHE[cache_key] = {"response": response_text, "ts": time.time()}
            return response_text
        except requests.exceptions.Timeout:
            with _CIRCUIT_LOCK:
                _consecutive_timeouts += 1
                cooldown = min(30 * (2 ** min(_consecutive_timeouts - 1, 3)), 300)
                _circuit_cooldown_until = time.time() + cooldown
                print(f"[DirectOllama] Timeout #{_consecutive_timeouts}. Circuit breaker: {cooldown}s cooldown")
            raise
        finally:
            _LLM_SEMAPHORE.release()

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

        payload = self._build_payload(system_prompt, conversation, prompt)

        try:
            return self._send(payload)
        except requests.exceptions.Timeout as e:
            print(f"[DirectOllama] Timeout after {self.timeout}s with {self.model}: {e}")
            if self.fallback_model and self.fallback_model != self.model:
                print(f"[DirectOllama] Retrying with fallback model: {self.fallback_model}")
                payload["model"] = self.fallback_model
                try:
                    return self._send(payload)
                except Exception as e2:
                    print(f"[DirectOllama] Fallback also failed: {e2}")
                    return f"[Error connecting to Ollama: primary timed out, fallback failed: {e2}]"
            return f"[Error connecting to Ollama: timed out after {self.timeout}s]"
        except Exception as e:
            print(f"[DirectOllama] error: {e}")
            return f"[Error connecting to Ollama: {e}]"

def get_reasoning_llm(temperature: float = None, max_tokens: int = None):
    """Get reasoning LLM with optional override parameters."""
    base_url = os.getenv("OLLAMA_BASE_URL", SETTINGS.models.base_url)
    model = os.getenv("REASONING_MODEL", SETTINGS.models.reasoning)
    # Default to faster model if still set to deepseek-r1
    if model and "deepseek-r1" in model.lower():
        model = "qwen2.5:7b"
        print("[LLM] Auto-upgraded reasoning model from deepseek-r1 to qwen2.5:7b for speed")

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
        # Model not available — trigger auto-pull in background, then fall back
        _auto_pull_model(model, base_url)
        available_fallbacks = ["qwen2.5:7b", "qwen2.5:0.5b", "llama3.2:1b", "qwen2.5-coder:1.5b"]
        fallback = next((m for m in available_fallbacks if _check_model_exists(m, base_url)), FALLBACK_MODEL)
        print(f"[LLM] Model '{model}' not found in Ollama. Pulling in background; falling back to: {fallback}")
        model = fallback
    else:
        print(f"[LLM] Selected reasoning model: {model}")
    return DirectOllama(base_url=base_url, model=model, temperature=temperature, system_prefix=system_prefix, fallback_model=FALLBACK_MODEL)

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
        _auto_pull_model(model, base_url)
        available_fallbacks = ["qwen2.5-coder:7b", "qwen2.5-coder:1.5b", "deepseek-r1:7b"]
        fallback = next((m for m in available_fallbacks if _check_model_exists(m, base_url)), FALLBACK_MODEL)
        print(f"[LLM] Coding model '{model}' not found. Pulling in background; falling back to: {fallback}")
        model = fallback
    else:
        print(f"[LLM] Selected coding model: {model}")
    # Cap coding timeout at 45s so background threads free up faster
    coding_timeout = min(45, OLLAMA_TIMEOUT)
    return DirectOllama(base_url=base_url, model=model, temperature=temperature, timeout=coding_timeout, system_prefix=system_prefix, fallback_model=FALLBACK_MODEL)

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


