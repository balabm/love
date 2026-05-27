"""
LOVE Neural Architecture Search — Self-Optimizing Neural Architecture

LOVE can search for and optimize its own neural architecture:
1. ARCHITECTURE SEARCH
   - Explores different neural architectures
   - Optimizes layer configurations
   - Finds optimal hyperparameters

2. PERFORMANCE PROFILING
   - Profiles different model configurations
   - Measures latency, memory, accuracy
   - Identifies bottlenecks

3. AUTOMATIC TUNING
   - Adjusts model parameters based on workload
   - Optimizes for specific tasks
   - Balances performance vs resource usage

4. MODEL EVOLUTION
   - Evolves model architectures over time
   - Adapts to changing requirements
   - Maintains performance while optimizing

This enables LOVE to continuously optimize its own neural infrastructure
for better performance, efficiency, and capability.
"""

import json
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "neural_architecture"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ARCHITECTURE_DB = DATA_DIR / "architecture_db.json"
PERFORMANCE_LOG = DATA_DIR / "performance_log.jsonl"
SEARCH_HISTORY = DATA_DIR / "search_history.json"
OPTIMIZATION_STATE = DATA_DIR / "optimization_state.json"


@dataclass
class ModelArchitecture:
    """A neural architecture configuration."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    model_type: str = ""  # transformer, rnn, hybrid, etc.
    layers: List[Dict] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = False
    fitness_score: float = 0.5


@dataclass
class ArchitectureSearch:
    """A neural architecture search run."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    search_space: Dict[str, Any] = field(default_factory=dict)
    search_method: str = "random"  # random, genetic, bayesian
    target_metric: str = "accuracy"  # accuracy, latency, memory, efficiency
    iterations: int = 10
    current_iteration: int = 0
    best_architecture: Optional[str] = None
    search_history: List[str] = field(default_factory=list)  # architecture IDs
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    status: str = "running"  # running, completed, failed


@dataclass
class PerformanceProfile:
    """Performance profile for a model configuration."""
    architecture_id: str = ""
    task_type: str = ""
    avg_latency_ms: float = 0.0
    throughput_tokens_per_sec: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_utilization: float = 0.0
    accuracy: float = 0.0
    energy_efficiency: float = 0.0
    profiled_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class OptimizationTarget:
    """An optimization target for neural architecture."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    metric: str = ""  # latency, memory, accuracy, throughput
    target_value: float = 0.0
    priority: float = 0.5
    current_value: float = 0.0
    achieved: bool = False


class NeuralArchitectureSearch:
    """
    LOVE's neural architecture search and optimization engine.
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
        self._architectures: Dict[str, ModelArchitecture] = {}
        self._searches: Dict[str, ArchitectureSearch] = {}
        self._performance_profiles: Dict[str, PerformanceProfile] = {}
        self._optimization_targets: List[OptimizationTarget] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_architecture_db()
        self._load_optimization_state()
    
    # ── Architecture Management ───────────────────────────────────────────────────
    
    def create_architecture(self, config: Dict[str, Any]) -> str:
        """Create a new model architecture."""
        try:
            architecture = ModelArchitecture(
                name=config.get("name", "Unnamed Architecture"),
                model_type=config.get("model_type", "transformer"),
                layers=config.get("layers", []),
                parameters=config.get("parameters", {}),
                hyperparameters=config.get("hyperparameters", {}),
            )
            
            self._architectures[architecture.id] = architecture
            self._save_architecture_db()
            
            self._log_performance({
                "event": "architecture_created",
                "architecture_id": architecture.id,
                "name": architecture.name,
            })
            
            return architecture.id
            
        except Exception as e:
            print(f"[NAS] Architecture creation error: {e}")
            return ""
    
    def profile_architecture(self, architecture_id: str, task_type: str = "general") -> Optional[PerformanceProfile]:
        """Profile the performance of an architecture."""
        if architecture_id not in self._architectures:
            return None
        
        try:
            architecture = self._architectures[architecture_id]
            
            # Simulate performance profiling (in real implementation, would run benchmarks)
            profile = PerformanceProfile(
                architecture_id=architecture_id,
                task_type=task_type,
                avg_latency_ms=self._estimate_latency(architecture),
                throughput_tokens_per_sec=self._estimate_throughput(architecture),
                memory_usage_mb=self._estimate_memory(architecture),
                gpu_utilization=0.7,  # Simulated
                accuracy=self._estimate_accuracy(architecture),
                energy_efficiency=self._estimate_energy_efficiency(architecture),
            )
            
            self._performance_profiles[f"{architecture_id}_{task_type}"] = profile
            
            # Update architecture metrics
            architecture.performance_metrics = {
                "latency_ms": profile.avg_latency_ms,
                "throughput": profile.throughput_tokens_per_sec,
                "accuracy": profile.accuracy,
            }
            architecture.resource_usage = {
                "memory_mb": profile.memory_usage_mb,
                "gpu_utilization": profile.gpu_utilization,
            }
            
            # Calculate fitness score
            architecture.fitness_score = self._calculate_fitness(architecture)
            
            self._save_architecture_db()
            
            return profile
            
        except Exception as e:
            print(f"[NAS] Profiling error: {e}")
            return None
    
    def _estimate_latency(self, architecture: ModelArchitecture) -> float:
        """Estimate latency based on architecture."""
        # Simplified estimation based on layer count and parameters
        layer_count = len(architecture.layers)
        param_count = architecture.parameters.get("total", 1000000)
        
        # Base latency + per-layer overhead + parameter scaling
        base_latency = 50.0  # ms
        layer_overhead = layer_count * 10.0
        param_scaling = (param_count / 1000000) * 20.0
        
        return base_latency + layer_overhead + param_scaling
    
    def _estimate_throughput(self, architecture: ModelArchitecture) -> float:
        """Estimate throughput in tokens per second."""
        latency = self._estimate_latency(architecture)
        # Rough estimate: 1000ms / latency * average tokens per batch
        return (1000.0 / max(latency, 1)) * 32
    
    def _estimate_memory(self, architecture: ModelArchitecture) -> float:
        """Estimate memory usage in MB."""
        param_count = architecture.parameters.get("total", 1000000)
        # Rough estimate: 4 bytes per parameter * 2 for gradients
        return (param_count * 8) / (1024 * 1024)
    
    def _estimate_accuracy(self, architecture: ModelArchitecture) -> float:
        """Estimate accuracy based on architecture complexity."""
        # Simplified: more complex architectures tend to be more accurate
        complexity_score = len(architecture.layers) * 0.05
        param_score = min(0.2, (architecture.parameters.get("total", 0) / 10000000) * 0.1)
        
        base_accuracy = 0.7
        return min(0.95, base_accuracy + complexity_score + param_score)
    
    def _estimate_energy_efficiency(self, architecture: ModelArchitecture) -> float:
        """Estimate energy efficiency (performance per watt)."""
        throughput = self._estimate_throughput(architecture)
        power_draw = self._estimate_memory(architecture) / 1000.0  # Rough power estimate
        return throughput / max(power_draw, 0.1)
    
    def _calculate_fitness(self, architecture: ModelArchitecture) -> float:
        """Calculate overall fitness score for an architecture."""
        # Weighted combination of metrics
        weights = {
            "accuracy": 0.4,
            "latency": -0.3,  # Lower is better
            "throughput": 0.2,
            "memory": -0.1,  # Lower is better
        }
        
        metrics = architecture.performance_metrics
        resources = architecture.resource_usage
        
        # Normalize metrics (simplified)
        accuracy_score = metrics.get("accuracy", 0.5)
        latency_score = 1.0 - min(1.0, metrics.get("latency_ms", 100) / 500)
        throughput_score = min(1.0, metrics.get("throughput", 10) / 100)
        memory_score = 1.0 - min(1.0, resources.get("memory_mb", 1000) / 8000)
        
        fitness = (
            weights["accuracy"] * accuracy_score +
            weights["latency"] * latency_score +
            weights["throughput"] * throughput_score +
            weights["memory"] * memory_score
        )
        
        return max(0.0, min(1.0, fitness))
    
    # ── Architecture Search ─────────────────────────────────────────────────────
    
    def start_architecture_search(self, search_config: Dict[str, Any]) -> str:
        """Start a neural architecture search."""
        try:
            search = ArchitectureSearch(
                search_space=search_config.get("search_space", {}),
                search_method=search_config.get("search_method", "random"),
                target_metric=search_config.get("target_metric", "accuracy"),
                iterations=search_config.get("iterations", 10),
            )
            
            self._searches[search.id] = search
            
            # Start search in background
            threading.Thread(
                target=self._run_search,
                args=(search.id,),
                daemon=True
            ).start()
            
            return search.id
            
        except Exception as e:
            print(f"[NAS] Search start error: {e}")
            return ""
    
    def _run_search(self, search_id: str):
        """Run the architecture search."""
        if search_id not in self._searches:
            return
        
        search = self._searches[search_id]
        
        try:
            for i in range(search.iterations):
                search.current_iteration = i + 1
                
                # Generate candidate architecture
                candidate = self._generate_candidate(search.search_space, search.search_method)
                
                if candidate:
                    # Profile the candidate
                    self.profile_architecture(candidate, "search")
                    
                    # Track in search history
                    search.search_history.append(candidate)
                    
                    # Update best if improved
                    if self._is_better(candidate, search.best_architecture, search.target_metric):
                        search.best_architecture = candidate
                
                self._save_search_history()
                time.sleep(1)  # Simulate search time
            
            search.status = "completed"
            search.completed_at = datetime.now().isoformat()
            self._save_search_history()
            
        except Exception as e:
            print(f"[NAS] Search error: {e}")
            search.status = "failed"
    
    def _generate_candidate(self, search_space: Dict, method: str) -> Optional[str]:
        """Generate a candidate architecture."""
        try:
            if method == "random":
                return self._generate_random_architecture(search_space)
            elif method == "genetic":
                return self._generate_genetic_architecture(search_space)
            else:
                return self._generate_random_architecture(search_space)
        except Exception as e:
            print(f"[NAS] Candidate generation error: {e}")
            return None
    
    def _generate_random_architecture(self, search_space: Dict) -> Optional[str]:
        """Generate a random architecture within search space."""
        import random
        
        # Get search space parameters
        layer_types = search_space.get("layer_types", ["linear", "attention", "conv"])
        min_layers = search_space.get("min_layers", 2)
        max_layers = search_space.get("max_layers", 10)
        min_hidden = search_space.get("min_hidden", 64)
        max_hidden = search_space.get("max_hidden", 512)
        
        # Generate random architecture
        num_layers = random.randint(min_layers, max_layers)
        layers = []
        
        for i in range(num_layers):
            layer = {
                "type": random.choice(layer_types),
                "hidden_size": random.randint(min_hidden, max_hidden),
                "activation": random.choice(["relu", "gelu", "swish"]),
            }
            layers.append(layer)
        
        # Calculate total parameters
        total_params = sum(l["hidden_size"] * l["hidden_size"] for l in layers)
        
        config = {
            "name": f"Random_Arch_{int(time.time())}",
            "model_type": "transformer",
            "layers": layers,
            "parameters": {"total": total_params},
            "hyperparameters": {
                "learning_rate": random.uniform(0.0001, 0.01),
                "batch_size": random.choice([16, 32, 64]),
            },
        }
        
        return self.create_architecture(config)
    
    def _generate_genetic_architecture(self, search_space: Dict) -> Optional[str]:
        """Generate architecture using genetic algorithm principles."""
        # Simplified genetic approach: mutate best existing architecture
        if not self._architectures:
            return self._generate_random_architecture(search_space)
        
        # Get best architecture
        best_arch = max(self._architectures.values(), key=lambda a: a.fitness_score)
        
        # Create mutation
        import random
        mutated_layers = best_arch.layers.copy()
        
        if mutated_layers:
            # Randomly modify one layer
            idx = random.randint(0, len(mutated_layers) - 1)
            mutated_layers[idx]["hidden_size"] = int(mutated_layers[idx]["hidden_size"] * random.uniform(0.8, 1.2))
        
        config = {
            "name": f"Genetic_Arch_{int(time.time())}",
            "model_type": best_arch.model_type,
            "layers": mutated_layers,
            "parameters": best_arch.parameters.copy(),
            "hyperparameters": best_arch.hyperparameters.copy(),
        }
        
        return self.create_architecture(config)
    
    def _is_better(self, candidate_id: str, current_best_id: Optional[str], target_metric: str) -> bool:
        """Check if candidate is better than current best."""
        if candidate_id not in self._architectures:
            return False
        
        candidate = self._architectures[candidate_id]
        
        if current_best_id is None:
            return True
        
        if current_best_id not in self._architectures:
            return True
        
        current_best = self._architectures[current_best_id]
        
        if target_metric == "accuracy":
            return candidate.performance_metrics.get("accuracy", 0) > current_best.performance_metrics.get("accuracy", 0)
        elif target_metric == "latency":
            return candidate.performance_metrics.get("latency_ms", 999) < current_best.performance_metrics.get("latency_ms", 999)
        elif target_metric == "fitness":
            return candidate.fitness_score > current_best.fitness_score
        else:
            return candidate.fitness_score > current_best.fitness_score
    
    # ── Optimization ───────────────────────────────────────────────────────────
    
    def set_optimization_target(self, metric: str, target_value: float, priority: float = 0.5):
        """Set an optimization target."""
        target = OptimizationTarget(
            metric=metric,
            target_value=target_value,
            priority=priority,
        )
        self._optimization_targets.append(target)
        self._save_optimization_state()
    
    def check_optimization_targets(self) -> List[Dict]:
        """Check which optimization targets are achieved."""
        results = []
        
        for target in self._optimization_targets:
            # Get current value from active architecture
            active_arch = next((a for a in self._architectures.values() if a.is_active), None)
            
            if active_arch:
                if target.metric == "latency":
                    current = active_arch.performance_metrics.get("latency_ms", 999)
                elif target.metric == "accuracy":
                    current = active_arch.performance_metrics.get("accuracy", 0)
                elif target.metric == "memory":
                    current = active_arch.resource_usage.get("memory_mb", 9999)
                else:
                    current = 0
                
                target.current_value = current
                
                # Check if achieved
                if target.metric in ["latency", "memory"]:
                    target.achieved = current <= target.target_value
                else:
                    target.achieved = current >= target.target_value
                
                results.append({
                    "metric": target.metric,
                    "target": target.target_value,
                    "current": current,
                    "achieved": target.achieved,
                    "priority": target.priority,
                })
        
        self._save_optimization_state()
        return results
    
    def optimize_for_target(self, metric: str) -> Optional[str]:
        """Find or create architecture optimized for specific metric."""
        try:
            # Search for existing architecture that meets target
            for arch_id, arch in self._architectures.items():
                if metric == "latency" and arch.performance_metrics.get("latency_ms", 999) < 100:
                    return arch_id
                elif metric == "accuracy" and arch.performance_metrics.get("accuracy", 0) > 0.9:
                    return arch_id
            
            # If not found, start search
            search_config = {
                "search_method": "genetic",
                "target_metric": metric,
                "iterations": 5,
                "search_space": {
                    "min_layers": 2,
                    "max_layers": 6,
                    "min_hidden": 64,
                    "max_hidden": 256,
                },
            }
            
            return self.start_architecture_search(search_config)
            
        except Exception as e:
            print(f"[NAS] Optimization error: {e}")
            return None
    
    # ── Model Evolution ────────────────────────────────────────────────────────
    
    def evolve_architecture(self, architecture_id: str, pressure: str = "performance") -> Optional[str]:
        """Evolve an architecture based on evolutionary pressure."""
        if architecture_id not in self._architectures:
            return None
        
        try:
            parent = self._architectures[architecture_id]
            
            # Create evolved version based on pressure
            if pressure == "performance":
                # Optimize for performance
                evolved_config = self._evolve_for_performance(parent)
            elif pressure == "efficiency":
                # Optimize for efficiency
                evolved_config = self._evolve_for_efficiency(parent)
            else:
                # Balanced evolution
                evolved_config = self._evolve_balanced(parent)
            
            evolved_id = self.create_architecture(evolved_config)
            
            if evolved_id:
                # Profile the evolved architecture
                self.profile_architecture(evolved_id)
                
                # If better, switch to evolved
                evolved = self._architectures[evolved_id]
                if evolved.fitness_score > parent.fitness_score:
                    self._switch_architecture(evolved_id)
            
            return evolved_id
            
        except Exception as e:
            print(f"[NAS] Evolution error: {e}")
            return None
    
    def _evolve_for_performance(self, parent: ModelArchitecture) -> Dict:
        """Evolve architecture for better performance."""
        import random
        
        # Add more layers or increase hidden size
        evolved_layers = parent.layers.copy()
        
        if random.random() > 0.5 and len(evolved_layers) < 12:
            # Add layer
            evolved_layers.append({
                "type": "attention",
                "hidden_size": evolved_layers[-1]["hidden_size"],
                "activation": "gelu",
            })
        else:
            # Increase hidden size
            for layer in evolved_layers:
                layer["hidden_size"] = int(layer["hidden_size"] * 1.2)
        
        return {
            "name": f"{parent.name}_evolved_perf",
            "model_type": parent.model_type,
            "layers": evolved_layers,
            "parameters": {"total": parent.parameters["total"] * 1.5},
            "hyperparameters": parent.hyperparameters.copy(),
        }
    
    def _evolve_for_efficiency(self, parent: ModelArchitecture) -> Dict:
        """Evolve architecture for better efficiency."""
        import random
        
        # Reduce layers or hidden size
        evolved_layers = parent.layers.copy()
        
        if len(evolved_layers) > 2 and random.random() > 0.5:
            # Remove layer
            evolved_layers.pop()
        else:
            # Reduce hidden size
            for layer in evolved_layers:
                layer["hidden_size"] = int(layer["hidden_size"] * 0.8)
        
        return {
            "name": f"{parent.name}_evolved_eff",
            "model_type": parent.model_type,
            "layers": evolved_layers,
            "parameters": {"total": parent.parameters["total"] * 0.7},
            "hyperparameters": parent.hyperparameters.copy(),
        }
    
    def _evolve_balanced(self, parent: ModelArchitecture) -> Dict:
        """Evolve architecture with balanced changes."""
        import random
        
        evolved_layers = parent.layers.copy()
        
        # Randomly modify some layers
        for layer in evolved_layers:
            if random.random() > 0.7:
                layer["hidden_size"] = int(layer["hidden_size"] * random.uniform(0.9, 1.1))
        
        return {
            "name": f"{parent.name}_evolved_bal",
            "model_type": parent.model_type,
            "layers": evolved_layers,
            "parameters": {"total": parent.parameters["total"]},
            "hyperparameters": parent.hyperparameters.copy(),
        }
    
    def _switch_architecture(self, architecture_id: str):
        """Switch to a different architecture."""
        # Deactivate current
        for arch in self._architectures.values():
            arch.is_active = False
        
        # Activate new
        if architecture_id in self._architectures:
            self._architectures[architecture_id].is_active = True
        
        self._save_architecture_db()
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_architecture_db(self):
        try:
            if ARCHITECTURE_DB.exists():
                data = json.loads(ARCHITECTURE_DB.read_text())
                for aid, ad in data.get("architectures", {}).items():
                    self._architectures[aid] = ModelArchitecture(**ad)
        except Exception as e:
            print(f"[NAS] Architecture DB load error: {e}")
    
    def _save_architecture_db(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "architectures": {aid: asdict(a) for aid, a in self._architectures.items()},
            }
            ARCHITECTURE_DB.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[NAS] Architecture DB save error: {e}")
    
    def _load_optimization_state(self):
        try:
            if OPTIMIZATION_STATE.exists():
                data = json.loads(OPTIMIZATION_STATE.read_text())
                for td in data.get("targets", []):
                    self._optimization_targets.append(OptimizationTarget(**td))
        except Exception as e:
            print(f"[NAS] Optimization state load error: {e}")
    
    def _save_optimization_state(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "targets": [asdict(t) for t in self._optimization_targets],
            }
            OPTIMIZATION_STATE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[NAS] Optimization state save error: {e}")
    
    def _save_search_history(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "searches": {sid: asdict(s) for sid, s in self._searches.items()},
            }
            SEARCH_HISTORY.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[NAS] Search history save error: {e}")
    
    def _log_performance(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(PERFORMANCE_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
    
    # ── Main Loop ─────────────────────────────────────────────────────────────────
    
    def start(self):
        """Start the NAS background loop."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-NAS"
        )
        self._thread.start()
        print("[NAS] Started — neural architecture search active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(300)  # Let other systems initialize
        
        while self._running:
            try:
                # Check optimization targets
                self.check_optimization_targets()
                
                # Periodically evolve active architecture
                active_arch = next((a for a in self._architectures.values() if a.is_active), None)
                if active_arch and len(self._architectures) < 20:
                    self.evolve_architecture(active_arch.id)
                
            except Exception as e:
                print(f"[NAS] Loop error: {e}")
            
            time.sleep(3600)  # Run every hour
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_best_architecture(self, metric: str = "fitness") -> Optional[Dict]:
        """Get the best architecture for a given metric."""
        if not self._architectures:
            return None
        
        if metric == "fitness":
            best = max(self._architectures.values(), key=lambda a: a.fitness_score)
        elif metric == "accuracy":
            best = max(self._architectures.values(), key=lambda a: a.performance_metrics.get("accuracy", 0))
        elif metric == "latency":
            best = min(self._architectures.values(), key=lambda a: a.performance_metrics.get("latency_ms", 999))
        else:
            best = max(self._architectures.values(), key=lambda a: a.fitness_score)
        
        return asdict(best)
    
    def get_architecture_stats(self) -> Dict:
        """Get statistics about architectures."""
        return {
            "total_architectures": len(self._architectures),
            "active_architecture": next((a.id for a in self._architectures.values() if a.is_active), None),
            "avg_fitness": sum(a.fitness_score for a in self._architectures.values()) / max(1, len(self._architectures)),
            "best_fitness": max((a.fitness_score for a in self._architectures.values()), default=0),
        }


# ── Singleton Access ─────────────────────────────────────────────────────────────

_nas_instance: Optional[NeuralArchitectureSearch] = None
_nas_lock = threading.Lock()


def get_neural_architecture_search() -> NeuralArchitectureSearch:
    global _nas_instance
    with _nas_lock:
        if _nas_instance is None:
            _nas_instance = NeuralArchitectureSearch()
        return _nas_instance