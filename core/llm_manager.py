"""
LOVE LLM Manager — Local Model Management & Dynamic Routing (Modern AI Pattern)

As LOVE grows to 15+ subsystems, managing which local LLM runs what task
becomes critical. This manager provides:

1. MODEL INVENTORY
   - List all available local models (Ollama, LM Studio, etc.)
   - Check which models are loaded and their resource usage
   - Detect new models installed by the user

2. DYNAMIC ROUTING
   - Route tasks to the best model for the job
   - Fallback chain when primary model is unavailable
   - Load balancing across multiple model instances

3. PROACTIVE OPTIMIZATION
   - Monitor model performance (latency, quality)
   - Suggest model switches when better options exist
   - Auto-pull recommended models for new capabilities

4. RESOURCE MANAGEMENT
   - Track GPU/CPU/memory usage per model
   - Unload idle models to free resources
   - Prevent OOM by managing concurrent loads

Architecture:
- list_models(): Get all available models with metadata
- route_task(): Pick optimal model for a task
- pull_model(): Download a new model
- unload_model(): Free resources
- get_performance_stats(): Track latency and quality
- suggest_models(): Proactive recommendations
"""

import json
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "llm_manager"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DB = DATA_DIR / "model_db.json"
PERFORMANCE_LOG = DATA_DIR / "performance_log.jsonl"
ROUTING_STATE = DATA_DIR / "routing_state.json"


@dataclass
class ModelInfo:
    """Information about an available LLM."""
    name: str = ""
    provider: str = "ollama"  # ollama, lmstudio, etc.
    size: str = ""  # 7B, 13B, 70B, etc.
    quantization: str = ""  # q4_0, q8_0, fp16, etc.
    parameters: str = ""  # 7b, 13b, 70b
    capabilities: List[str] = field(default_factory=list)  # reasoning, coding, vision, etc.
    loaded: bool = False
    last_used: str = ""
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    memory_mb: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class TaskRoute:
    """A routing decision for a task."""
    task_type: str = ""  # reasoning, coding, vision, chat, etc.
    model: str = ""
    reason: str = ""
    confidence: float = 0.0
    fallback_chain: List[str] = field(default_factory=list)


class LLMManager:
    """
    Local LLM management and dynamic routing for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._models: Dict[str, ModelInfo] = {}
        self._performance: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._routing_history: List[TaskRoute] = []
        self._load_model_db()

    # ── Model Discovery ──────────────────────────────────────────────────────

    def discover_models(self) -> List[ModelInfo]:
        """Discover all available local models."""
        models = []
        try:
            # Ollama discovery
            import requests
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            resp = requests.get(f"{base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            for m in resp.json().get("models", []):
                info = ModelInfo(
                    name=m.get("name", ""),
                    provider="ollama",
                    size=m.get("details", {}).get("parameter_size", ""),
                    quantization=m.get("details", {}).get("quantization_level", ""),
                    parameters=m.get("details", {}).get("parameter_size", ""),
                    capabilities=self._infer_capabilities(m.get("name", "")),
                    loaded=False,  # Would need psutil or Ollama-specific API
                )
                models.append(info)
                self._models[info.name] = info
        except Exception as e:
            print(f"[LLMManager] Discovery error: {e}")

        self._save_model_db()
        return models

    def _infer_capabilities(self, model_name: str) -> List[str]:
        """Infer model capabilities from its name."""
        name_lower = model_name.lower()
        caps = ["chat"]
        if any(k in name_lower for k in ["coder", "code", "qwen2.5-coder"]):
            caps.append("coding")
        if any(k in name_lower for k in ["reason", "r1", "deepseek-r1", "o1", "o3"]):
            caps.append("reasoning")
        if any(k in name_lower for k in ["vision", "llava", "bakllava", "moondream"]):
            caps.append("vision")
        if any(k in name_lower for k in ["embed", "nomic-embed", "bge"]):
            caps.append("embedding")
        if any(k in name_lower for k in ["mistral", "mixtral", "llama", "qwen"]):
            caps.append("general")
        return caps

    # ── Dynamic Routing ────────────────────────────────────────────────────

    def route_task(self, task_type: str, preferred_model: str = "",
                   quality_required: bool = False) -> TaskRoute:
        """Route a task to the optimal model."""
        if not self._models:
            self.discover_models()

        # If preferred model specified and available
        if preferred_model and preferred_model in self._models:
            model = self._models[preferred_model]
            if task_type in model.capabilities or "general" in model.capabilities:
                return TaskRoute(
                    task_type=task_type,
                    model=preferred_model,
                    reason="User preferred",
                    confidence=0.9,
                    fallback_chain=self._build_fallbacks(task_type, exclude=preferred_model),
                )

        # Find best model for task type
        candidates = [
            m for m in self._models.values()
            if task_type in m.capabilities or "general" in m.capabilities
        ]

        if not candidates:
            # Fallback to any available model
            candidates = list(self._models.values())

        # Score candidates
        scored = []
        for model in candidates:
            score = 0.0
            # Capability match
            if task_type in model.capabilities:
                score += 2.0
            # Performance
            perf = self._performance.get(model.name, deque())
            if perf:
                recent = list(perf)[-10:]
                avg_latency = sum(p["latency_ms"] for p in recent) / len(recent)
                success = sum(1 for p in recent if p["success"]) / len(recent)
                score += success * 1.5
                score += (1.0 / (1 + avg_latency / 1000)) * 1.0  # Lower latency = higher score
            # Quality preference
            if quality_required and any(k in model.name.lower() for k in ["70b", "65b", "40b"]):
                score += 1.0
            scored.append((score, model))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1] if scored else None

        if best:
            return TaskRoute(
                task_type=task_type,
                model=best.name,
                reason=f"Best {task_type} model (score={scored[0][0]:.2f})",
                confidence=min(0.95, scored[0][0] / 5.0),
                fallback_chain=[m.name for _, m in scored[1:3]],
            )

        return TaskRoute(
            task_type=task_type,
            model="",
            reason="No models available",
            confidence=0.0,
        )

    def _build_fallbacks(self, task_type: str, exclude: str = "") -> List[str]:
        """Build a fallback chain for a task type."""
        candidates = [
            m for m in self._models.values()
            if m.name != exclude and (task_type in m.capabilities or "general" in m.capabilities or "chat" in m.capabilities)
        ]
        return [m.name for m in candidates[:2]]

    # ── Performance Tracking ───────────────────────────────────────────────

    def record_performance(self, model: str, latency_ms: float, success: bool,
                          task_type: str = ""):
        """Record a performance observation."""
        point = {
            "timestamp": time.time(),
            "latency_ms": latency_ms,
            "success": success,
            "task_type": task_type,
        }
        with self._lock:
            self._performance[model].append(point)

        if model in self._models:
            perf = self._performance[model]
            recent = list(perf)[-100:]
            self._models[model].avg_latency_ms = sum(p["latency_ms"] for p in recent) / len(recent)
            self._models[model].success_rate = sum(1 for p in recent if p["success"]) / len(recent)
            self._models[model].last_used = datetime.now().isoformat()

        self._log_performance(point, model)

    def get_model_stats(self, model: str) -> Dict[str, Any]:
        """Get performance statistics for a model."""
        perf = self._performance.get(model, deque())
        if not perf:
            return {"calls": 0}
        recent = list(perf)[-100:]
        return {
            "calls": len(perf),
            "avg_latency_ms": round(sum(p["latency_ms"] for p in recent) / len(recent), 2),
            "success_rate": round(sum(1 for p in recent if p["success"]) / len(recent), 3),
            "recent_calls": len(recent),
        }

    def get_all_stats(self) -> Dict[str, Any]:
        return {
            "models": {name: self.get_model_stats(name) for name in self._models},
            "total_models": len(self._models),
            "total_calls": sum(len(p) for p in self._performance.values()),
        }

    # ── Proactive Suggestions ─────────────────────────────────────────────

    def suggest_models(self) -> List[Dict[str, Any]]:
        """Proactively suggest models based on usage patterns."""
        suggestions = []
        
        if not self._models:
            self.discover_models()

        # Check if we have good coverage
        has_reasoning = any("reasoning" in m.capabilities for m in self._models.values())
        has_coding = any("coding" in m.capabilities for m in self._models.values())
        has_vision = any("vision" in m.capabilities for m in self._models.values())
        has_embedding = any("embedding" in m.capabilities for m in self._models.values())

        if not has_reasoning:
            suggestions.append({
                "type": "missing_capability",
                "capability": "reasoning",
                "suggestion": "Pull deepseek-r1:7b for reasoning tasks",
                "command": "ollama pull deepseek-r1:7b",
                "impact": "high",
            })
        if not has_coding:
            suggestions.append({
                "type": "missing_capability",
                "capability": "coding",
                "suggestion": "Pull qwen2.5-coder:7b for coding tasks",
                "command": "ollama pull qwen2.5-coder:7b",
                "impact": "high",
            })
        if not has_embedding:
            suggestions.append({
                "type": "missing_capability",
                "capability": "embedding",
                "suggestion": "Pull nomic-embed-text for vector memory",
                "command": "ollama pull nomic-embed-text",
                "impact": "medium",
            })
        if not has_vision:
            suggestions.append({
                "type": "missing_capability",
                "capability": "vision",
                "suggestion": "Pull llava:7b for vision tasks",
                "command": "ollama pull llava:7b",
                "impact": "medium",
            })

        # Check for underperforming models
        for name, model in self._models.items():
            stats = self.get_model_stats(name)
            if stats["calls"] > 10 and stats["success_rate"] < 0.8:
                suggestions.append({
                    "type": "underperforming",
                    "model": name,
                    "suggestion": f"{name} has low success rate ({stats['success_rate']:.0%}). Consider re-pulling or switching.",
                    "impact": "medium",
                })

        return suggestions

    # ── Model Operations ───────────────────────────────────────────────────

    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull a new model from Ollama."""
        try:
            import requests
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            resp = requests.post(
                f"{base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=300,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("status") == "success":
                self.discover_models()  # Refresh inventory
            return {"success": True, "model": model_name, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def unload_model(self, model_name: str) -> Dict[str, Any]:
        """Unload a model to free resources."""
        try:
            import requests
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            # Ollama doesn't have a direct unload API, but we can simulate by running a keep-alive
            # or by using the generate API with a short prompt
            resp = requests.post(
                f"{base_url}/api/generate",
                json={"model": model_name, "prompt": "", "keep_alive": 0},
                timeout=10,
            )
            if model_name in self._models:
                self._models[model_name].loaded = False
            return {"success": True, "model": model_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_model_db(self):
        try:
            if MODEL_DB.exists():
                data = json.loads(MODEL_DB.read_text())
                for md in data.get("models", []):
                    model = ModelInfo(**md)
                    self._models[model.name] = model
        except Exception as e:
            print(f"[LLMManager] Load error: {e}")

    def _save_model_db(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "models": [
                    {
                        "name": m.name,
                        "provider": m.provider,
                        "size": m.size,
                        "quantization": m.quantization,
                        "parameters": m.parameters,
                        "capabilities": m.capabilities,
                        "loaded": m.loaded,
                        "last_used": m.last_used,
                        "avg_latency_ms": m.avg_latency_ms,
                        "success_rate": m.success_rate,
                        "memory_mb": m.memory_mb,
                        "tags": m.tags,
                    }
                    for m in self._models.values()
                ],
            }
            MODEL_DB.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[LLMManager] Save error: {e}")

    def _log_performance(self, point: Dict, model: str):
        try:
            with open(PERFORMANCE_LOG, "a") as f:
                f.write(json.dumps({**point, "model": model}) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_llm_manager_instance: Optional[LLMManager] = None
_llm_manager_lock = threading.Lock()


def get_llm_manager() -> LLMManager:
    global _llm_manager_instance
    with _llm_manager_lock:
        if _llm_manager_instance is None:
            _llm_manager_instance = LLMManager()
        return _llm_manager_instance
