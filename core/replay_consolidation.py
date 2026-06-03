"""
LOVE Replay Consolidation — Hippocampal Sleep Replay for Living Substrate

What the hippocampus does during sleep: replays high-surprise experiences to
strengthen cortical (world-model) representations. This is the offline
consolidation phase that makes "learning during the day" permanent.

Algorithm mirrors SHY (Synaptic Homeostasis Hypothesis) + sharp-wave ripple
replay in CA1 -> neocortex:
  1. Pull high-surprise events from ChromaDB (the "hippocampus")
  2. Sort them into temporal trajectories (time-ordered replay)
  3. Feed through LatentWorldModel at boosted lr (10x) — fast offline learning
  4. Also step the SSM so temporal context integrates the replay
  5. Track consolidation gain (prediction error before vs after)
  6. Mark saturated low-surprise memories as consolidated (metadata flag)
  7. Persist state, log everything, expose snapshot for /substrate endpoint

Triggering:
  - consolidate_now()           — call any time
  - start_daemon(hours=4)       — background thread, auto-runs every N hours
  - Auto-fires when homeostasis.fatigue > 0.7 (LOVE is "tired")
"""
from __future__ import annotations

import json
import math
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from core.execution_guard import log_error

# ── Paths ─────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "replay_consolidation"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "state.json"
LOG_FILE   = DATA_DIR / "log.jsonl"

CHROMA_PATH = Path(__file__).parent.parent / "data" / "memory"
COLLECTION_NAME = "love_memory"

EMBED_DIM      = 384
REPLAY_LR_MULT = 10.0          # fast-forward learning rate multiplier
REPLAY_BATCH   = 50            # default memories per consolidation run
SURPRISE_THRESH = 0.3          # free_energy / surprise metadata threshold
MAX_REPLAY_BEFORE_MARK = 3     # replays before a low-surprise memory is flagged
MARK_SURPRISE_CEIL     = 0.1   # if surprise < this AND replay_count > max -> mark consolidated
SSM_NORM_THRESHOLD     = 50.0  # if ssm state_norm > this, soft-reset


# ── State ─────────────────────────────────────────────────────────────────────

def _default_state() -> Dict[str, Any]:
    return {
        "total_replays": 0,
        "total_memories_consolidated": 0,
        "last_run": "",
        "consolidation_gain_history": [],   # list of floats (last 100 gains)
    }


def _load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.replay_consolidation")
    return _default_state()


def _save_state(state: Dict[str, Any]) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.replay_consolidation")


def _append_log(entry: Dict[str, Any]) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.replay_consolidation")


# ── ChromaDB client (lazy) ────────────────────────────────────────────────────

_chroma_client = None
_chroma_lock   = threading.Lock()


def _get_collection():
    """Return the love_memory ChromaDB collection, or None if unavailable."""
    global _chroma_client
    with _chroma_lock:
        try:
            if _chroma_client is None:
                import chromadb
                _chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            return _chroma_client.get_collection(COLLECTION_NAME)
        except Exception as e:
            print(f"[ReplayConsolidation] ChromaDB unavailable: {e}")
            return None


# ── Core class ────────────────────────────────────────────────────────────────

class ReplayConsolidation:
    """
    Hippocampal replay for the living substrate.

    Re-processes high-surprise experiences during low-activity periods to
    consolidate them into world-model transition weights and SSM long-term state.
    """

    _instance: Optional["ReplayConsolidation"] = None
    _singleton_lock = threading.Lock()

    def __new__(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._mu = threading.Lock()
        self._state = _load_state()
        self._daemon_thread: Optional[threading.Thread] = None
        self._daemon_running = False
        print("[ReplayConsolidation] online - hippocampal replay engine ready")

    # ── 1. Query high-surprise memories ───────────────────────────────────────

    def get_high_surprise_memories(
        self,
        n: int = REPLAY_BATCH,
        surprise_threshold: float = SURPRISE_THRESH,
    ) -> List[Dict[str, Any]]:
        """
        Pull up to n memories from ChromaDB whose surprise (free_energy) exceeds
        surprise_threshold.

        Falls back to returning the most recent memories sorted by any numeric
        metadata field if the primary query fails or returns nothing.
        """
        coll = _get_collection()
        if coll is None:
            return []

        # --- Primary: filter by free_energy metadata ---
        memories: List[Dict[str, Any]] = []
        for field_name in ("free_energy", "surprise"):
            try:
                result = coll.get(
                    where={field_name: {"$gte": surprise_threshold}},
                    limit=n,
                    include=["documents", "metadatas", "embeddings"],
                )
                ids = result.get("ids") or []
                if ids:
                    docs      = result.get("documents") or [None] * len(ids)
                    metas     = result.get("metadatas") or [{}] * len(ids)
                    _raw_emb  = result.get("embeddings")
                    embeddings = _raw_emb if _raw_emb is not None else [None] * len(ids)
                    for i, mid in enumerate(ids):
                        memories.append({
                            "id":        mid,
                            "document":  docs[i] if docs[i] else "",
                            "metadata":  metas[i] if metas[i] else {},
                            "embedding": embeddings[i],
                        })
                    return memories
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.replay_consolidation")

        # --- Fallback: get all recent memories (last 24 h) sorted by any numeric field ---
        try:
            result = coll.get(
                limit=min(n * 2, 200),
                include=["documents", "metadatas", "embeddings"],
            )
            ids = result.get("ids") or []
            if not ids:
                return []

            docs       = result.get("documents") or [None] * len(ids)
            metas      = result.get("metadatas") or [{}] * len(ids)
            _raw_emb   = result.get("embeddings")
            embeddings = _raw_emb if _raw_emb is not None else [None] * len(ids)

            now_ts = time.time()
            cutoff = now_ts - 86400  # 24 h

            candidates = []
            for i, mid in enumerate(ids):
                m = metas[i] or {}
                # Parse timestamp
                ts_raw = m.get("timestamp", "")
                ts = 0.0
                if ts_raw:
                    try:
                        ts = datetime.fromisoformat(str(ts_raw)).timestamp()
                    except Exception:
                        try:
                            ts = float(ts_raw)
                        except Exception:
                            ts = 0.0

                # Skip memories older than 24 h (unless we have nothing)
                if ts and ts < cutoff:
                    continue

                # Score = any numeric scalar field we can find
                score = 0.0
                for v in m.values():
                    try:
                        fv = float(v)        # only works for scalars
                        if fv > score:
                            score = fv
                    except (TypeError, ValueError, OverflowError) as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.replay_consolidation")

                candidates.append((score, mid, docs[i] or "", m, embeddings[i]))

            # If recent filter left us nothing, lift the cutoff
            if not candidates:
                candidates = [
                    (0.0, ids[i], docs[i] or "", metas[i] or {}, embeddings[i])
                    for i in range(len(ids))
                ]

            candidates.sort(key=lambda x: x[0], reverse=True)

            for score, mid, doc, meta, emb in candidates[:n]:
                memories.append({
                    "id":        mid,
                    "document":  doc,
                    "metadata":  meta,
                    "embedding": emb,
                })
        except Exception as e:
            print(f"[ReplayConsolidation] fallback query failed: {e}")

        return memories

    # ── 2. Replay trajectory ───────────────────────────────────────────────────

    def replay_trajectory(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Replay a list of memories through the world model at boosted learning rate.

        Returns a dict with replay stats (replayed, avg_error_before, avg_error_after, gain).
        """
        if not memories:
            return {"replayed": 0, "avg_error_before": 0.0,
                    "avg_error_after": 0.0, "gain": 0.0}

        # Lazy imports to avoid circular deps at module load time
        try:
            from core.world_model_latent import get_world_model_latent, embed
            wm = get_world_model_latent()
        except Exception as e:
            print(f"[ReplayConsolidation] world model unavailable: {e}")
            return {"replayed": 0, "avg_error_before": 0.0,
                    "avg_error_after": 0.0, "gain": 0.0, "error": str(e)}

        try:
            from core.state_space_memory import get_ssm_memory
            ssm = get_ssm_memory()
        except Exception:
            ssm = None

        # Sort by timestamp if available
        def _ts(m: Dict) -> float:
            ts_raw = m.get("metadata", {}).get("timestamp", "")
            if not ts_raw:
                return 0.0
            try:
                return datetime.fromisoformat(str(ts_raw)).timestamp()
            except Exception:
                try:
                    return float(ts_raw)
                except Exception:
                    return 0.0

        sorted_mems = sorted(memories, key=_ts)

        errors_before: List[float] = []
        errors_after:  List[float] = []

        for mem in sorted_mems:
            doc = mem.get("document", "") or ""
            raw_emb = mem.get("embedding")

            # Measure error *before* replay (current prediction vs this memory's state)
            try:
                err_before_obs = wm.observe.__self__._state.ema_free_energy  # type: ignore[attr-defined]
            except Exception:
                err_before_obs = wm.free_energy()

            # --- Temporarily boost learning rate ---
            try:
                with wm._mu:
                    orig_lr = wm._state.lr
                    wm._state.lr = min(orig_lr * REPLAY_LR_MULT, 0.5)
            except Exception:
                orig_lr = None

            # --- Run the observation (online Hebbian update at boosted lr) ---
            try:
                if raw_emb is not None:
                    # We have the stored embedding — use it directly to also
                    # push the SSM forward without calling embed() again.
                    vec = np.asarray(raw_emb, dtype=np.float32)
                    if vec.shape == (EMBED_DIM,):
                        # Normalise (ChromaDB stores raw, wm uses normalised)
                        n = np.linalg.norm(vec)
                        if n > 0:
                            vec = vec / n
                        # Run SSM step with the stored embedding
                        if ssm is not None:
                            try:
                                ssm.step(vec)
                            except Exception as e:
                                from core.execution_guard import log_error
                                log_error(e, module="core.replay_consolidation")

                # Call world model observe (always — it does the weight update)
                obs = wm.observe(doc if doc else " ", source="replay")
                err_after_obs = obs.pred_error

            except Exception as ex:
                print(f"[ReplayConsolidation] observe failed on memory {mem.get('id')}: {ex}")
                err_after_obs = err_before_obs
            finally:
                # --- Restore original learning rate ---
                if orig_lr is not None:
                    try:
                        with wm._mu:
                            wm._state.lr = orig_lr
                    except Exception as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.replay_consolidation")

            errors_before.append(err_before_obs)
            errors_after.append(err_after_obs)

        n_replayed = len(sorted_mems)
        avg_before = float(np.mean(errors_before)) if errors_before else 0.0
        avg_after  = float(np.mean(errors_after))  if errors_after  else 0.0
        gain       = avg_before - avg_after

        return {
            "replayed":         n_replayed,
            "avg_error_before": round(avg_before, 5),
            "avg_error_after":  round(avg_after,  5),
            "gain":             round(gain, 5),
        }

    # ── 3. Mark saturated memories ─────────────────────────────────────────────

    def _mark_consolidated_memories(
        self,
        memories: List[Dict[str, Any]],
    ) -> int:
        """
        For memories that have been replayed > MAX_REPLAY_BEFORE_MARK times
        and whose surprise has dropped below MARK_SURPRISE_CEIL, add metadata
        flag "consolidated": True.  Does NOT delete anything.
        """
        coll = _get_collection()
        if coll is None:
            return 0

        marked = 0
        for mem in memories:
            mid  = mem.get("id")
            meta = mem.get("metadata") or {}
            if not mid:
                continue

            # How many times has this been replayed?
            replay_count = int(meta.get("replay_count", 0)) + 1

            # Current surprise score
            surprise_val = 0.0
            for fk in ("free_energy", "surprise"):
                try:
                    surprise_val = float(meta.get(fk, 0.0))
                    if surprise_val > 0:
                        break
                except (TypeError, ValueError) as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.replay_consolidation")

            # Build updated metadata
            new_meta = dict(meta)
            new_meta["replay_count"] = replay_count
            new_meta["last_replayed"] = datetime.now().isoformat()

            if replay_count > MAX_REPLAY_BEFORE_MARK and surprise_val < MARK_SURPRISE_CEIL:
                new_meta["consolidated"] = True
                marked += 1

            try:
                # ChromaDB 0.4+ API
                doc = mem.get("document", "") or " "
                coll.update(ids=[mid], metadatas=[new_meta], documents=[doc])
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.replay_consolidation")

        return marked

    # ── 4. consolidate_now ────────────────────────────────────────────────────

    def consolidate_now(self, n_memories: int = REPLAY_BATCH) -> Dict[str, Any]:
        """
        Full consolidation cycle:
          1. Pull high-surprise memories
          2. Replay through world model + SSM
          3. Mark saturated memories as consolidated
          4. Soft-reset SSM if state_norm is too high
          5. Persist state + log

        Returns a consolidation report dict.
        """
        started = datetime.now().isoformat()
        report: Dict[str, Any] = {
            "started":    started,
            "n_requested": n_memories,
        }

        # 1. Get high-surprise memories
        memories = self.get_high_surprise_memories(n=n_memories)
        report["n_memories_found"] = len(memories)

        # 2. Replay trajectory
        traj_stats = self.replay_trajectory(memories)
        report.update(traj_stats)

        # 3. SSM sequential pair training
        ssm_steps = 0
        ssm_reset = False
        try:
            from core.state_space_memory import get_ssm_memory
            ssm = get_ssm_memory()

            # Step through sequential embedding pairs to bake temporal context
            # We already stepped in replay_trajectory; here we do a second pass
            # on pairs (t, t+1) to reinforce sequential dependencies.
            for mem in memories:
                raw_emb = mem.get("embedding")
                if raw_emb is not None:
                    vec = np.asarray(raw_emb, dtype=np.float32)
                    if vec.shape == (EMBED_DIM,):
                        n = np.linalg.norm(vec)
                        vec = vec / n if n > 0 else vec
                        try:
                            ssm.step(vec)
                            ssm_steps += 1
                        except Exception as e:
                            from core.execution_guard import log_error
                            log_error(e, module="core.replay_consolidation")

            # Soft-reset if state norm has saturated
            try:
                if ssm.state_norm() > SSM_NORM_THRESHOLD:
                    if hasattr(ssm, "soft_reset"):
                        ssm.soft_reset()
                    else:
                        # Fallback: scale h by 0.5 directly
                        try:
                            with ssm._mu:
                                ssm._h = ssm._h * 0.5
                        except Exception as e:
                            from core.execution_guard import log_error
                            log_error(e, module="core.replay_consolidation")
                    ssm_reset = True
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.replay_consolidation")

        except Exception as e:
            report["ssm_error"] = str(e)

        report["ssm_extra_steps"] = ssm_steps
        report["ssm_reset"]       = ssm_reset

        # 4. Mark consolidated memories
        marked = self._mark_consolidated_memories(memories)
        report["memories_marked_consolidated"] = marked

        # 5. Tell world model consolidation happened (halves EMA free energy)
        try:
            from core.world_model_latent import get_world_model_latent
            get_world_model_latent().reset_after_consolidation()
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.replay_consolidation")

        # 6. Update internal state (use .get() with defaults for forward-compat)
        gain = traj_stats.get("gain", 0.0)
        with self._mu:
            self._state["total_replays"] = self._state.get("total_replays", 0) + 1
            self._state["total_memories_consolidated"] = (
                self._state.get("total_memories_consolidated", 0) + marked
            )
            self._state["last_run"] = started

            history = self._state.get("consolidation_gain_history", [])
            history.append(round(gain, 5))
            if len(history) > 100:
                history = history[-100:]
            self._state["consolidation_gain_history"] = history

        _save_state(self._state)

        # 7. Log
        report["finished"] = datetime.now().isoformat()
        _append_log(report)

        print(
            f"[ReplayConsolidation] run complete - "
            f"{traj_stats.get('replayed', 0)} memories replayed, "
            f"gain={gain:+.4f}, marked={marked}"
        )
        return report

    # ── 5. Daemon ─────────────────────────────────────────────────────────────

    def start_daemon(self, interval_hours: float = 4.0) -> None:
        """
        Start background thread that calls consolidate_now() every interval_hours.
        Also fires immediately if homeostasis fatigue > 0.7.
        Thread is daemon=True so it won't block interpreter shutdown.
        """
        if self._daemon_running:
            return
        self._daemon_running = True
        self._daemon_thread = threading.Thread(
            target=self._daemon_loop,
            args=(interval_hours,),
            daemon=True,
            name="LOVE-ReplayConsolidation",
        )
        self._daemon_thread.start()
        print(f"[ReplayConsolidation] daemon started - interval={interval_hours}h")

    def _daemon_loop(self, interval_hours: float) -> None:
        interval_secs = interval_hours * 3600.0
        # Stagger boot so other substrate modules are ready
        time.sleep(30)

        while self._daemon_running:
            try:
                self._check_and_run_if_tired()
            except Exception as e:
                print(f"[ReplayConsolidation] daemon error: {e}")

            # Sleep in 60-second chunks so we can react to fatigue
            elapsed = 0.0
            while elapsed < interval_secs and self._daemon_running:
                time.sleep(60)
                elapsed += 60.0
                # Check fatigue mid-interval too
                try:
                    self._check_and_run_if_tired()
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.replay_consolidation")

    def _check_and_run_if_tired(self) -> None:
        """Fire consolidation immediately if LOVE is fatigued (homeostasis drive > 0.7)."""
        fatigue = 0.0
        try:
            from core.homeostasis import get_homeostasis
            h = get_homeostasis()
            fatigue = getattr(h._drives, "fatigue", 0.0)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.replay_consolidation")

        if fatigue > 0.7:
            # Avoid rapid re-triggering: check last run time
            last_run = self._state.get("last_run", "")
            if last_run:
                try:
                    secs_since = (
                        datetime.now() - datetime.fromisoformat(last_run)
                    ).total_seconds()
                    if secs_since < 1800:   # don't re-run within 30 min
                        return
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.replay_consolidation")
            print(f"[ReplayConsolidation] fatigue={fatigue:.2f} > 0.7 - triggering consolidation")
            self.consolidate_now()

    # ── 6. Snapshot ───────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        """Return current state for /substrate endpoint."""
        history = self._state.get("consolidation_gain_history", [])
        avg_gain = float(np.mean(history)) if history else 0.0
        return {
            "total_replays":              self._state.get("total_replays", 0),
            "total_memories_consolidated": self._state.get("total_memories_consolidated", 0),
            "last_run":                   self._state.get("last_run", ""),
            "avg_consolidation_gain":     round(avg_gain, 5),
            "recent_gains":               history[-10:],
            "daemon_running":             self._daemon_running,
        }


# ── Module-level singleton getter ─────────────────────────────────────────────

_instance: Optional[ReplayConsolidation] = None


def get_replay_consolidation() -> ReplayConsolidation:
    """Return the singleton ReplayConsolidation instance."""
    global _instance
    if _instance is None:
        _instance = ReplayConsolidation()
    return _instance
