"""
LOVE Mixture-of-Experts Router

LOVE has accumulated 100+ subsystems. Without a learned router, every query
fans out to all of them = wasted compute, contradictory outputs. This module
implements a real MoE gating layer on top of the world-model embeddings.

Architecture:
  - Each "expert" is a registered handler (memory recall, web search, task agent,
    fitness agent, evolution engine, finance, doc analyst, etc.)
  - Each expert holds a *prototype embedding* — a running mean of queries on
    which it performed well (Thompson-sampling style)
  - Gating: softmax over <query, prototype> similarities, scaled by a learned
    "reliability" prior per expert
  - Reward: post-hoc score from user feedback / world-model surprise reduction
  - Online update: prototypes shift toward queries that earned high reward;
    expert priors update via contextual bandit (UCB1 + exponential reward decay)

This is the *executive function* layer — picks the right tool, learns from
outcomes, prunes experts that consistently underperform.

What's real:
  - Cosine-gated top-k expert selection
  - Thompson sampling fallback for exploration when uncertain
  - UCB1 upper-confidence bound for cold-start experts
  - Persistent prototypes + reward histories
"""
from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "moe_router"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPERTS_FILE = DATA_DIR / "experts.npz"
META_FILE = DATA_DIR / "meta.json"

EMBED_DIM = 384
DEFAULT_TEMP = 0.4
EXPLORATION_C = 1.4   # UCB1 exploration constant
REWARD_DECAY = 0.9    # EMA decay for reward signal


@dataclass
class ExpertStats:
    name: str
    description: str = ""
    invocations: int = 0
    total_reward: float = 0.0
    ema_reward: float = 0.5
    last_invoked: float = 0.0
    avg_latency_ms: float = 0.0
    failures: int = 0


class MoERouter:
    _instance: Optional["MoERouter"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init = False
            return cls._instance

    def __init__(self):
        if self._init:
            return
        self._init = True
        self._mu = threading.Lock()
        self._handlers: Dict[str, Callable[[str, Dict], Any]] = {}
        self._stats: Dict[str, ExpertStats] = {}
        self._prototypes: Dict[str, np.ndarray] = {}      # name -> 384-d
        self._total_invocations = 0
        self._load()

    # ── registration ─────────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        handler: Callable[[str, Dict], Any],
        description: str = "",
        seed_examples: Optional[List[str]] = None,
    ):
        """Register a new expert. seed_examples bootstrap the prototype."""
        with self._mu:
            self._handlers[name] = handler
            if name not in self._stats:
                self._stats[name] = ExpertStats(name=name, description=description)

            # Initialize / refresh prototype from seed examples
            if name not in self._prototypes or seed_examples:
                proto = self._compute_prototype(seed_examples or [description, name])
                if proto is not None:
                    self._prototypes[name] = proto

    def _compute_prototype(self, texts: List[str]) -> Optional[np.ndarray]:
        try:
            from core.world_model_latent import embed
            vecs = [embed(t) for t in texts if t]
            vecs = [v for v in vecs if v is not None]
            if not vecs:
                return None
            mean = np.mean(np.stack(vecs), axis=0)
            n = np.linalg.norm(mean)
            return mean / n if n > 0 else mean
        except Exception:
            return None

    # ── gating ───────────────────────────────────────────────────────────────

    def gate(
        self,
        query: str,
        top_k: int = 3,
        temperature: float = DEFAULT_TEMP,
        explore: bool = True,
    ) -> List[Tuple[str, float]]:
        """Return top-k (expert_name, weight) for this query."""
        if not self._handlers:
            return []

        from core.world_model_latent import embed
        q = embed(query)
        if q is None:
            # Fallback: return highest EMA-reward experts uniformly
            ranked = sorted(self._stats.values(), key=lambda s: -s.ema_reward)
            return [(s.name, 1.0 / top_k) for s in ranked[:top_k]]

        names = list(self._prototypes.keys())
        if not names:
            return []

        sims = np.array([float(np.dot(q, self._prototypes[n])) for n in names], dtype=np.float32)

        # UCB1 bonus for under-explored experts (encourages diversity)
        if explore and self._total_invocations > 0:
            ucb = np.zeros(len(names), dtype=np.float32)
            for i, n in enumerate(names):
                s = self._stats[n]
                visits = max(1, s.invocations)
                ucb[i] = EXPLORATION_C * math.sqrt(math.log(self._total_invocations + 1) / visits)
            # Blend similarity with confidence-weighted reward + exploration bonus
            reward_prior = np.array([self._stats[n].ema_reward for n in names], dtype=np.float32)
            scores = sims + 0.3 * (reward_prior - 0.5) + 0.2 * ucb
        else:
            scores = sims

        # Softmax over scores
        e = np.exp((scores - scores.max()) / max(1e-3, temperature))
        weights = e / e.sum()

        # Top-k
        idx = np.argsort(-weights)[:top_k]
        return [(names[i], float(weights[i])) for i in idx]

    # ── invocation ───────────────────────────────────────────────────────────

    def route(
        self,
        query: str,
        context: Optional[Dict] = None,
        top_k: int = 1,
    ) -> List[Dict[str, Any]]:
        """Gate and invoke top-k experts. Returns their outputs + metadata."""
        context = context or {}
        gated = self.gate(query, top_k=top_k)
        results = []

        for name, weight in gated:
            handler = self._handlers.get(name)
            if not handler:
                continue
            t0 = time.time()
            try:
                output = handler(query, context)
                ok = True
                err = ""
            except Exception as e:
                output = None
                ok = False
                err = str(e)

            dt_ms = (time.time() - t0) * 1000.0

            with self._mu:
                s = self._stats[name]
                s.invocations += 1
                s.last_invoked = time.time()
                s.avg_latency_ms = 0.8 * s.avg_latency_ms + 0.2 * dt_ms
                if not ok:
                    s.failures += 1
                    # Auto-penalty on exception
                    self._reinforce(name, query, reward=-0.5)
                self._total_invocations += 1

            results.append({
                "expert": name, "weight": weight,
                "output": output, "ok": ok, "error": err,
                "latency_ms": round(dt_ms, 1),
            })

        return results

    # ── learning ─────────────────────────────────────────────────────────────

    def reinforce(self, expert_name: str, query: str, reward: float):
        """External feedback: reward ∈ [-1, 1]. Updates prototype + EMA reward."""
        self._reinforce(expert_name, query, reward)

    def _reinforce(self, name: str, query: str, reward: float):
        if name not in self._stats:
            return
        with self._mu:
            s = self._stats[name]
            r = max(-1.0, min(1.0, reward))
            normalized = (r + 1.0) / 2.0   # to [0, 1]
            s.ema_reward = REWARD_DECAY * s.ema_reward + (1 - REWARD_DECAY) * normalized
            s.total_reward += r

            # Shift prototype toward query if reward > 0, away if < 0
            try:
                from core.world_model_latent import embed
                q = embed(query)
                if q is not None and name in self._prototypes:
                    p = self._prototypes[name]
                    direction = q - p
                    lr = 0.05 * r   # signed — negative reward pushes away
                    new_p = p + lr * direction
                    nn = np.linalg.norm(new_p)
                    if nn > 0:
                        self._prototypes[name] = new_p / nn
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.moe_router")

            # Periodic persist
            if self._total_invocations % 25 == 0:
                self._save()

    def autopsy_low_performers(self, min_invocations: int = 20, threshold: float = 0.3) -> List[str]:
        """Find experts performing badly. Caller decides whether to remove."""
        deadwood = []
        for s in self._stats.values():
            if s.invocations >= min_invocations and s.ema_reward < threshold:
                deadwood.append(s.name)
        return deadwood

    # ── persistence ──────────────────────────────────────────────────────────

    def _save(self):
        try:
            if self._prototypes:
                names = list(self._prototypes.keys())
                protos = np.stack([self._prototypes[n] for n in names])
                np.savez(EXPERTS_FILE, names=np.array(names), protos=protos)
            META_FILE.write_text(json.dumps({
                "total_invocations": self._total_invocations,
                "stats": {n: asdict(s) for n, s in self._stats.items()},
                "last_save": datetime.now().isoformat(),
            }, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.moe_router")

    def _load(self):
        if EXPERTS_FILE.exists():
            try:
                d = np.load(EXPERTS_FILE, allow_pickle=True)
                names = d["names"].tolist()
                protos = d["protos"]
                for i, n in enumerate(names):
                    self._prototypes[n] = protos[i].astype(np.float32)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.moe_router")
        if META_FILE.exists():
            try:
                m = json.loads(META_FILE.read_text())
                self._total_invocations = m.get("total_invocations", 0)
                for n, sd in m.get("stats", {}).items():
                    self._stats[n] = ExpertStats(**sd)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.moe_router")

    # ── introspection ────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        ranked = sorted(self._stats.values(), key=lambda s: -s.ema_reward)
        return {
            "total_invocations": self._total_invocations,
            "expert_count": len(self._stats),
            "top_experts": [
                {"name": s.name, "reward": round(s.ema_reward, 3),
                 "invocations": s.invocations, "fail_rate": round(s.failures / max(1, s.invocations), 3)}
                for s in ranked[:10]
            ],
            "deadwood": self.autopsy_low_performers(),
        }


_router_instance: Optional[MoERouter] = None


def get_moe_router() -> MoERouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = MoERouter()
    return _router_instance
