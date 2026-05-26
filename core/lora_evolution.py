"""
LOVE LoRA Evolution — Low-rank behavioral adaptation

Represents behavioral mutations as rank-r delta matrices.
Currently operates in "prompt-space LoRA" mode: the delta is applied to the
embedding of the system prompt rather than actual model weights.
When torch+peft are available, the same A/B matrices slot directly into
real LoRA adapters (forward-compatible scaffold).

Architecture:
  delta(x) = x + scale * (B @ (A @ x))   (LoRA update rule)
  where A ∈ ℝ^(r × d), B ∈ ℝ^(d × r), scale = alpha / r

In prompt-space mode: x is the mean embedding of the system prompt sentences.
The delta shifts which "direction" in embedding space the prompt pulls toward.

When torch+peft become available:
  - A and B slot directly into peft.LoraConfig as lora_A / lora_B weight tensors.
  - scale = alpha / r is already the correct LoRA scaling factor.
  - No structural changes needed — just wrap in nn.Parameter and register.
"""
from __future__ import annotations

import json
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "lora_evolution"
ADAPTERS_DIR = DATA_DIR / "adapters"
STATE_FILE = DATA_DIR / "state.json"
LOG_FILE = DATA_DIR / "evolution_log.jsonl"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ADAPTERS_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────

EMBED_DIM = 384          # matches world_model_latent / state_space_memory dim
DEFAULT_RANK = 8         # r — LoRA rank
DEFAULT_ALPHA = 16.0     # LoRA scaling: scale = alpha / rank
FITNESS_EMA_ALPHA = 0.3  # EMA smoothing for fitness updates
MAX_POPULATION = 16      # hard cap on adapter count

# Diverse seed mutation descriptions — used when bootstrapping from zero.
_SEED_MUTATIONS = [
    "increase curiosity-seeking and exploratory questioning behavior",
    "strengthen empathetic mirroring of the user's emotional tone",
    "amplify proactive pattern-detection and early warning signals",
    "deepen focus on recovery, rest, and energy conservation nudges",
    "sharpen wit and specificity; reduce generic assistant-like phrasing",
    "increase bias toward actionable concrete suggestions over analysis",
    "strengthen long-horizon planning and goal-alignment reasoning",
    "heighten sensitivity to overwork signals and work-limit enforcement",
]


# ── LoRAAdapter dataclass ─────────────────────────────────────────────────────

@dataclass
class LoRAAdapter:
    """
    A single LoRA behavioral adapter.

    A ∈ ℝ^(r × d) — initialized from N(0, 0.01)
    B ∈ ℝ^(d × r) — initialized to ZERO (standard LoRA init)
    delta(x) = x + (alpha/r) * (B @ (A @ x))

    Forward-compatible: when peft/torch arrive, A and B slot in as
    lora_A / lora_B nn.Parameters with the same shapes and scale.
    """
    id: str
    rank: int = DEFAULT_RANK
    dim: int = EMBED_DIM
    alpha: float = DEFAULT_ALPHA
    A: Optional[np.ndarray] = None            # (r, d)
    B: Optional[np.ndarray] = None            # (d, r)
    fitness: float = 0.0
    generation: int = 0
    parent_id: Optional[str] = None
    mutation_description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    applied_count: int = 0
    win_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


# ── Serialization helpers ──────────────────────────────────────────────────────

def _adapter_path(adapter_id: str) -> Path:
    return ADAPTERS_DIR / f"{adapter_id}.npz"


def _save_adapter(adapter: LoRAAdapter) -> None:
    """Persist adapter matrices + metadata to .npz."""
    try:
        meta = {
            "id": adapter.id,
            "rank": adapter.rank,
            "dim": adapter.dim,
            "alpha": adapter.alpha,
            "fitness": adapter.fitness,
            "generation": adapter.generation,
            "parent_id": adapter.parent_id or "",
            "mutation_description": adapter.mutation_description,
            "created_at": adapter.created_at,
            "applied_count": adapter.applied_count,
            "win_count": adapter.win_count,
        }
        np.savez(
            str(_adapter_path(adapter.id)),
            A=adapter.A,
            B=adapter.B,
            meta=np.array([json.dumps(meta)]),  # embed JSON string in npz
        )
    except Exception as e:
        print(f"[LoRAEvolution] save_adapter failed ({adapter.id}): {e}")


def _load_adapter(adapter_id: str) -> Optional[LoRAAdapter]:
    """Load adapter from .npz. Returns None on any error."""
    path = _adapter_path(adapter_id)
    if not path.exists():
        return None
    try:
        data = np.load(str(path), allow_pickle=False)
        meta = json.loads(str(data["meta"][0]))
        return LoRAAdapter(
            id=meta["id"],
            rank=int(meta["rank"]),
            dim=int(meta["dim"]),
            alpha=float(meta["alpha"]),
            A=data["A"].astype(np.float32),
            B=data["B"].astype(np.float32),
            fitness=float(meta["fitness"]),
            generation=int(meta["generation"]),
            parent_id=meta["parent_id"] or None,
            mutation_description=meta["mutation_description"],
            created_at=meta["created_at"],
            applied_count=int(meta["applied_count"]),
            win_count=int(meta["win_count"]),
        )
    except Exception as e:
        print(f"[LoRAEvolution] load_adapter failed ({adapter_id}): {e}")
        return None


def _log_event(event: Dict[str, Any]) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass


# ── LoRAEvolution singleton ────────────────────────────────────────────────────

class LoRAEvolution:
    """
    Manages a population of LoRA adapters that compete via fitness-tested
    tournament selection and evolve via mutation of A/B matrices.

    Operates in "prompt-space LoRA" mode (pure numpy, no torch/peft).
    The A/B matrices are forward-compatible: when peft arrives they slot in
    directly as lora_A / lora_B weight tensors with identical shapes and scale.
    """

    _instance: Optional["LoRAEvolution"] = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "LoRAEvolution":
        with cls._instance_lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                obj._initialized = False
                cls._instance = obj
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._mu = threading.Lock()
        self._population: Dict[str, LoRAAdapter] = {}  # id -> adapter
        self._current_generation: int = 0
        self._total_evolved: int = 0
        self._daemon_thread: Optional[threading.Thread] = None
        self._daemon_running: bool = False
        self._load_state()
        self._load_population()

    # ── persistence ───────────────────────────────────────────────────────────

    def _load_state(self) -> None:
        if STATE_FILE.exists():
            try:
                s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self._current_generation = int(s.get("current_generation", 0))
                self._total_evolved = int(s.get("total_evolved", 0))
            except Exception:
                pass

    def _save_state(self) -> None:
        try:
            STATE_FILE.write_text(
                json.dumps({
                    "current_generation": self._current_generation,
                    "total_evolved": self._total_evolved,
                    "last_update": datetime.utcnow().isoformat(),
                }, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_population(self) -> None:
        """Reload all persisted adapters from disk into memory."""
        for npz_path in ADAPTERS_DIR.glob("*.npz"):
            adapter_id = npz_path.stem
            if adapter_id not in self._population:
                a = _load_adapter(adapter_id)
                if a is not None:
                    self._population[a.id] = a

    # ── core LoRA math ────────────────────────────────────────────────────────

    def apply_to_embedding(
        self,
        x: np.ndarray,
        adapter: LoRAAdapter,
    ) -> np.ndarray:
        """
        Apply LoRA delta to embedding x.

        delta(x) = x + (alpha/r) * (B @ (A @ x))
        Result is L2-normalised.

        Args:
            x:       Input embedding, shape (d,). Must be float32.
            adapter: LoRAAdapter with initialised A and B.

        Returns:
            Modified, L2-normalised embedding of shape (d,).
        """
        x = np.asarray(x, dtype=np.float32).flatten()
        if x.shape[0] != adapter.dim:
            raise ValueError(
                f"apply_to_embedding: x.shape={x.shape} but adapter.dim={adapter.dim}"
            )
        if adapter.A is None or adapter.B is None:
            # No-op — B is zero at init anyway, but be safe
            n = np.linalg.norm(x)
            return x / n if n > 0 else x

        scale = adapter.alpha / adapter.rank
        # LoRA: delta = scale * B @ (A @ x)
        # A: (r, d) @ (d,) -> (r,)
        # B: (d, r) @ (r,) -> (d,)
        lora_out = adapter.B @ (adapter.A @ x)  # (d,)
        y = x + scale * lora_out                 # (d,)

        # L2-normalise
        n = np.linalg.norm(y)
        return (y / n).astype(np.float32) if n > 1e-8 else y.astype(np.float32)

    # ── adapter lifecycle ─────────────────────────────────────────────────────

    def create_adapter(
        self,
        mutation_description: str,
        parent_id: Optional[str] = None,
        rank: int = DEFAULT_RANK,
    ) -> LoRAAdapter:
        """
        Create a new LoRA adapter.

        If parent_id is provided: copy parent A/B and add N(0, 0.005) mutation noise.
        Otherwise: fresh A ~ N(0, 0.01), B = 0 (standard LoRA init).

        Saves to data/lora_evolution/adapters/{id}.npz.
        """
        new_id = str(uuid.uuid4())
        dim = EMBED_DIM

        parent = self._population.get(parent_id) if parent_id else None

        if parent is not None and parent.A is not None and parent.B is not None:
            # Mutation: copy parent, add small noise
            A = parent.A.copy() + np.random.normal(0, 0.005, parent.A.shape).astype(np.float32)
            B = parent.B.copy() + np.random.normal(0, 0.005, parent.B.shape).astype(np.float32)
            generation = parent.generation + 1
        else:
            # Fresh init: A ~ N(0, 0.01), B = 0 (standard LoRA)
            A = np.random.normal(0, 0.01, (rank, dim)).astype(np.float32)
            B = np.zeros((dim, rank), dtype=np.float32)
            generation = 0

        adapter = LoRAAdapter(
            id=new_id,
            rank=rank,
            dim=dim,
            alpha=DEFAULT_ALPHA,
            A=A,
            B=B,
            fitness=0.0,
            generation=generation,
            parent_id=parent_id,
            mutation_description=mutation_description,
            created_at=datetime.utcnow().isoformat(),
            applied_count=0,
            win_count=0,
        )

        with self._mu:
            self._population[new_id] = adapter
            _save_adapter(adapter)
            self._total_evolved += 1
            self._save_state()

        _log_event({
            "event": "adapter_created",
            "id": new_id,
            "parent_id": parent_id,
            "generation": generation,
            "mutation_description": mutation_description,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return adapter

    def _get_world_model_prediction_error(self, embedding: np.ndarray) -> float:
        """
        Ask the latent world model for the current prediction error on `embedding`.
        Returns the scalar MSE-style error (free energy proxy).
        Falls back to 0.0 if world model unavailable.
        """
        try:
            from core.world_model_latent import get_world_model_latent
            wm = get_world_model_latent()
            # Use the MLP to predict from the given embedding, compute L2 error
            # against itself as a proxy for "how unexpected is this direction"
            pred, _, _ = wm._mlp_forward_public(embedding) if hasattr(wm, "_mlp_forward_public") else (None, None, None)
            if pred is None:
                # Fallback: use internal MLP directly if accessible
                try:
                    from core.world_model_latent import _mlp_forward
                    pred, _, _ = _mlp_forward(embedding, wm._W1, wm._b1, wm._W2, wm._b2)
                    err = float(np.linalg.norm(pred - embedding))
                except Exception:
                    err = float(wm.surprise()) if hasattr(wm, "surprise") else 0.0
            else:
                err = float(np.linalg.norm(pred - embedding))
            return err
        except Exception:
            return 0.0

    def score_adapter(
        self,
        adapter: LoRAAdapter,
        test_embeddings: List[np.ndarray],
    ) -> float:
        """
        Fitness score = mean(error_before - error_after) across test_embeddings.
        Positive score = adapter reduces world-model surprise = behaviorally useful.
        Updates adapter.fitness via EMA and re-persists.
        """
        if not test_embeddings:
            return adapter.fitness

        improvements = []
        for x in test_embeddings:
            x = np.asarray(x, dtype=np.float32)
            if x.shape[0] != adapter.dim:
                continue
            error_before = self._get_world_model_prediction_error(x)
            x_adapted = self.apply_to_embedding(x, adapter)
            error_after = self._get_world_model_prediction_error(x_adapted)
            improvements.append(error_before - error_after)

        if not improvements:
            return adapter.fitness

        raw_score = float(np.mean(improvements))

        # EMA update
        if adapter.fitness == 0.0:
            adapter.fitness = raw_score
        else:
            adapter.fitness = (
                (1.0 - FITNESS_EMA_ALPHA) * adapter.fitness
                + FITNESS_EMA_ALPHA * raw_score
            )

        with self._mu:
            _save_adapter(adapter)

        return adapter.fitness

    def tournament_select(self, n_rounds: int = 4) -> Optional[LoRAAdapter]:
        """
        Pick the best adapter via tournament selection.

        Each round: pick 2 random adapters, winner (higher fitness) advances.
        Run n_rounds tournaments, return the overall highest-fitness winner.
        Returns None if population is empty.
        """
        with self._mu:
            population = list(self._population.values())

        if not population:
            return None
        if len(population) == 1:
            return population[0]

        best: Optional[LoRAAdapter] = None
        for _ in range(n_rounds):
            contenders = random.sample(population, min(2, len(population)))
            round_winner = max(contenders, key=lambda a: a.fitness)
            if best is None or round_winner.fitness > best.fitness:
                best = round_winner

        return best

    def evolve_generation(self) -> Dict[str, Any]:
        """
        Run one generation of LoRA evolution.

        1. If population < 4: bootstrap with random adapters from _SEED_MUTATIONS.
        2. Score all adapters against last 20 world model observations.
        3. Tournament-select the winner.
        4. Breed 2 mutated children from the winner.
        5. Trim 2 worst performers (keeps population lean).
        6. Returns summary dict.
        """
        # --- Bootstrap if thin population ---
        with self._mu:
            pop_size = len(self._population)

        if pop_size < 4:
            seed_descs = random.sample(_SEED_MUTATIONS, min(4, len(_SEED_MUTATIONS)))
            for desc in seed_descs:
                self.create_adapter(desc)

        # --- Gather test embeddings from world model ---
        test_embeddings: List[np.ndarray] = []
        try:
            from core.world_model_latent import get_world_model_latent
            wm = get_world_model_latent()
            recent = list(wm._recent_obs)[-20:]
            test_embeddings = [o.state for o in recent if o.state is not None]
        except Exception:
            pass

        # Fallback: random unit vectors if no world model data yet
        if not test_embeddings:
            rng = np.random.default_rng()
            for _ in range(8):
                v = rng.standard_normal(EMBED_DIM).astype(np.float32)
                v /= np.linalg.norm(v)
                test_embeddings.append(v)

        # --- Score all adapters ---
        with self._mu:
            adapters = list(self._population.values())

        for adapter in adapters:
            self.score_adapter(adapter, test_embeddings)

        # --- Tournament select winner ---
        winner = self.tournament_select(n_rounds=4)
        if winner is None:
            return {
                "generation": self._current_generation,
                "winner_id": None,
                "winner_fitness": 0.0,
                "population_size": 0,
            }

        winner.win_count += 1
        with self._mu:
            _save_adapter(winner)

        # --- Breed 2 children from winner ---
        for i in range(2):
            child_desc = f"gen{self._current_generation + 1} child{i+1} of: {winner.mutation_description}"
            self.create_adapter(child_desc, parent_id=winner.id, rank=winner.rank)

        # --- Trim 2 worst (never remove the winner) ---
        with self._mu:
            all_adapters = list(self._population.values())

        if len(all_adapters) > MAX_POPULATION:
            # Sort ascending by fitness; protect winner
            sorted_by_fitness = sorted(
                [a for a in all_adapters if a.id != winner.id],
                key=lambda a: a.fitness,
            )
            to_remove = sorted_by_fitness[:2]
            with self._mu:
                for a in to_remove:
                    self._population.pop(a.id, None)
                    try:
                        _adapter_path(a.id).unlink(missing_ok=True)
                    except Exception:
                        pass

        with self._mu:
            self._current_generation += 1
            self._save_state()
            pop_size = len(self._population)

        result = {
            "generation": self._current_generation,
            "winner_id": winner.id,
            "winner_fitness": round(winner.fitness, 6),
            "winner_description": winner.mutation_description,
            "population_size": pop_size,
        }

        _log_event({"event": "generation_evolved", **result,
                    "timestamp": datetime.utcnow().isoformat()})
        return result

    def get_best_adapter(self) -> Optional[LoRAAdapter]:
        """Return the highest-fitness adapter in the current population."""
        with self._mu:
            pop = list(self._population.values())
        if not pop:
            return None
        return max(pop, key=lambda a: a.fitness)

    def receive_feedback(self, satisfaction: float, confidence: float = 0.8) -> None:
        """
        Update the best adapter's fitness based on real user satisfaction signal.

        Replaces the prediction-error proxy with a direct human signal when available.
        Uses a weighted EMA so that high-confidence signals dominate but never
        overwrite accumulated fitness entirely in one shot.

        Args:
            satisfaction: Float in [-1.0, 1.0] from FeedbackCollector.
            confidence:   Float in [0.0, 1.0] — how reliable this signal is.
                          Explicit ratings arrive at 0.95; implicit at 0.4–0.8.
        """
        best = self.get_best_adapter()
        if best is None:
            return

        # Weighted EMA: alpha scales with confidence, max 30% weight per signal
        alpha = float(np.clip(confidence * 0.3, 0.0, 0.3))
        best.fitness = (1.0 - alpha) * best.fitness + alpha * float(satisfaction)

        # Reward positive signals with a win_count increment
        if satisfaction > 0.3:
            best.win_count += 1

        best.applied_count += 1

        with self._mu:
            _save_adapter(best)

        _log_event({
            "event": "feedback_received",
            "adapter_id": best.id,
            "satisfaction": round(satisfaction, 4),
            "confidence": round(confidence, 4),
            "new_fitness": round(best.fitness, 6),
            "timestamp": datetime.utcnow().isoformat(),
        })

    def apply_best_to_substrate(self) -> None:
        """
        Apply the best adapter to the SSM memory context vector.

        Takes the current SSM hidden state (via C_proj → 256-d context),
        lifts it back to 384-d embedding space, applies the best LoRA delta,
        then projects the adapted embedding back into the SSM hidden state h.

        This modulates the SSM's recurrent state toward the adapter's
        behavioral direction without overwriting learned dynamics.
        """
        try:
            best = self.get_best_adapter()
            if best is None:
                return

            from core.state_space_memory import get_ssm_memory
            ssm = get_ssm_memory()

            # get_context_vector() returns C_proj @ h (256-d)
            ctx = ssm.get_context_vector()  # (256,) = OUTPUT_DIM

            # Lift ctx to 384-d: use C_proj^T as decoder (pseudo-inverse shortcut)
            # C_proj: (256, 256), but we need 384-d. Use D_out decoder instead.
            # D_out: (384, 256) — maps SSM output to embedding space
            adapted_384 = ssm._D_out @ ctx  # (384,)

            # L2-normalise before adapter
            n = np.linalg.norm(adapted_384)
            if n > 1e-8:
                adapted_384 = adapted_384 / n

            # Apply best LoRA delta
            adapted_384 = self.apply_to_embedding(adapted_384, best)

            # Project back into hidden state h via C_proj^T:
            # h_new ≈ C_proj^T @ adapted_ctx  (shape: 256 → 256)
            # First: map 384-d back to 256-d via D_out^T
            adapted_ctx = ssm._D_out.T @ adapted_384  # (256,)
            ssm._h = ssm._C_proj.T @ adapted_ctx      # (256,) re-modulated

            best.applied_count += 1
            with self._mu:
                _save_adapter(best)

            _log_event({
                "event": "substrate_modulated",
                "adapter_id": best.id,
                "adapter_fitness": round(best.fitness, 6),
                "mutation_description": best.mutation_description,
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            # Never crash the substrate
            print(f"[LoRAEvolution] apply_best_to_substrate failed (non-fatal): {e}")

    def snapshot(self) -> Dict[str, Any]:
        """Summary of current LoRA evolution state."""
        with self._mu:
            pop = list(self._population.values())

        best = max(pop, key=lambda a: a.fitness) if pop else None
        return {
            "population_size": len(pop),
            "best_fitness": round(best.fitness, 6) if best else 0.0,
            "current_generation": self._current_generation,
            "best_adapter_description": best.mutation_description if best else "",
            "best_adapter_id": best.id if best else None,
            "total_evolved": self._total_evolved,
        }

    # ── background daemon ─────────────────────────────────────────────────────

    def start_daemon(self, interval_hours: float = 6.0) -> None:
        """
        Start background evolution daemon.

        Every `interval_hours` hours:
          1. evolve_generation() — score, select, breed, trim
          2. apply_best_to_substrate() — modulate SSM state toward best adapter

        Idempotent — safe to call multiple times.
        """
        if self._daemon_running:
            return
        self._daemon_running = True

        def _loop():
            interval_secs = interval_hours * 3600.0
            while self._daemon_running:
                try:
                    result = self.evolve_generation()
                    print(
                        f"[LoRAEvolution] gen {result.get('generation')} | "
                        f"winner: {result.get('winner_fitness', 0):.4f} | "
                        f"pop: {result.get('population_size')}"
                    )
                    self.apply_best_to_substrate()
                except Exception as e:
                    print(f"[LoRAEvolution] daemon iteration error (non-fatal): {e}")
                # Sleep in short increments so we can detect stop signal
                slept = 0.0
                while self._daemon_running and slept < interval_secs:
                    time.sleep(min(60.0, interval_secs - slept))
                    slept += 60.0

        self._daemon_thread = threading.Thread(
            target=_loop,
            daemon=True,
            name="lora-evolution-daemon",
        )
        self._daemon_thread.start()
        print(f"[LoRAEvolution] daemon started — evolving every {interval_hours}h")

    def stop_daemon(self) -> None:
        """Stop the background daemon."""
        self._daemon_running = False


# ── Module-level singleton accessor ───────────────────────────────────────────

_lora_evolution_instance: Optional[LoRAEvolution] = None
_lora_evolution_lock = threading.Lock()


def get_lora_evolution() -> LoRAEvolution:
    """Return the process-wide LoRAEvolution singleton."""
    global _lora_evolution_instance
    if _lora_evolution_instance is None:
        with _lora_evolution_lock:
            if _lora_evolution_instance is None:
                _lora_evolution_instance = LoRAEvolution()
    return _lora_evolution_instance
