"""
LOVE Living Substrate — Boot orchestrator for the new architectural layer.

One import, one call: start_living_substrate(). Brings up:
  - LatentWorldModel (predictive coding base)
  - StateSpaceMemory (Mamba-style long-horizon state)
  - MoERouter (with self-registered seed experts)
  - Homeostasis (drives, metabolism)
  - EmbodiedSelf (proprioception loop)
  - HierarchicalPredictiveCoding (multi-level attention)

Designed to be safe to import from api/main.py without breaking older paths
if any submodule fails — each system starts with try/except and reports.
"""
from __future__ import annotations

import threading
from typing import Any, Dict


_started_lock = threading.Lock()
_started = False


def _register_seed_experts():
    """Pre-register the major LOVE subsystems as MoE experts with prototype seeds."""
    try:
        from core.moe_router import get_moe_router
    except Exception:
        return
    r = get_moe_router()

    # The handlers below are thin shims — they just call into existing modules
    # and return their result. The router learns *which* one to call.

    def _h_memory(q, ctx):
        from core.memory import recall_memory
        return recall_memory(q, n=5)

    def _h_web(q, ctx):
        from core.internet import web_search
        return web_search(q)

    def _h_finance(q, ctx):
        from tools.finance import scan_all_markets
        return scan_all_markets()

    def _h_tasks(q, ctx):
        from agents.task_agent import get_task_overview
        return get_task_overview()

    def _h_fitness(q, ctx):
        from agents.fitness_agent import get_fitness_status
        return get_fitness_status()

    def _h_doc(q, ctx):
        from core.doc_analyst import get_analyst
        a = get_analyst()
        return getattr(a, "answer", lambda x: None)(q) if a else None

    def _h_self(q, ctx):
        return {
            "world_model": __import__("core.world_model_latent", fromlist=["x"]).get_world_model_latent().snapshot(),
            "ssm":         __import__("core.state_space_memory",  fromlist=["x"]).get_ssm_memory().snapshot(),
            "homeostasis": __import__("core.homeostasis",         fromlist=["x"]).get_homeostasis().snapshot(),
            "body":        __import__("core.embodied_self",       fromlist=["x"]).get_embodied_self().snapshot(),
            "hpc":         __import__("core.hierarchical_predictive_coding", fromlist=["x"]).get_hpc().snapshot(),
        }

    # Anchor expert — every conversation reinforces this. Lets reward signal land.
    def _h_chat(q, ctx):
        return None   # never invoked by router; serves as reward target only

    seeds = [
        ("core_memory_recall", _h_memory,
         "Recall past conversations, facts, decisions",
         ["what did we discuss", "remember when", "recall my last", "history of"]),
        ("web_search", _h_web,
         "Live web / news / facts I might not know",
         ["search the web for", "what is the latest", "news about", "current price of"]),
        ("finance_scan", _h_finance,
         "Markets, crypto, portfolio, trading",
         ["btc", "stock price", "portfolio", "market scan", "alpha opportunity"]),
        ("task_overview", _h_tasks,
         "Tasks, projects, deadlines, productivity",
         ["what's overdue", "my tasks", "next deadline", "todo list"]),
        ("fitness_overview", _h_fitness,
         "Workouts, recovery, fitness consistency",
         ["did i work out", "fitness streak", "training plan", "rest day"]),
        ("doc_analysis", _h_doc,
         "Parsing files, PDFs, documents the user dropped",
         ["read this pdf", "analyze the doc", "summarize this file"]),
        ("self_introspection", _h_self,
         "Internal state — drives, free energy, body, attention",
         ["how are you", "what are you feeling", "your state", "introspect"]),
        ("core_agent_chat", _h_chat,
         "General conversation handled by main agent",
         ["chat", "talk", "tell me about", "what do you think"]),
    ]

    for name, handler, desc, seeds_text in seeds:
        try:
            r.register(name, handler, description=desc, seed_examples=seeds_text)
        except Exception as e:
            print(f"[LivingSubstrate] expert seed {name} failed: {e}")


def start_living_substrate() -> Dict[str, Any]:
    """Idempotent boot. Returns status dict."""
    global _started
    status: Dict[str, Any] = {}
    with _started_lock:
        if _started:
            return {"already_started": True}
        _started = True

    # 1. World model (passive — observed-on-demand, no thread needed yet)
    try:
        from core.world_model_latent import get_world_model_latent
        get_world_model_latent()
        status["world_model"] = "ok"
    except Exception as e:
        status["world_model"] = f"err:{e}"

    # 2. SSM memory
    try:
        from core.state_space_memory import get_ssm_memory
        get_ssm_memory()
        status["ssm_memory"] = "ok"
    except Exception as e:
        status["ssm_memory"] = f"err:{e}"

    # 3. MoE router + seed experts
    try:
        from core.moe_router import get_moe_router
        get_moe_router()
        _register_seed_experts()
        status["moe_router"] = "ok"
    except Exception as e:
        status["moe_router"] = f"err:{e}"

    # 4. Homeostasis (starts thread)
    try:
        from core.homeostasis import get_homeostasis
        get_homeostasis().start()
        status["homeostasis"] = "ok"
    except Exception as e:
        status["homeostasis"] = f"err:{e}"

    # 5. Embodied self (starts thread)
    try:
        from core.embodied_self import get_embodied_self
        get_embodied_self().start()
        status["embodied_self"] = "ok"
    except Exception as e:
        status["embodied_self"] = f"err:{e}"

    # 6. HPC (starts thread)
    try:
        from core.hierarchical_predictive_coding import get_hpc
        get_hpc().start()
        status["hpc"] = "ok"
    except Exception as e:
        status["hpc"] = f"err:{e}"


    # 7. Replay consolidation daemon
    try:
        from core.replay_consolidation import get_replay_consolidation
        get_replay_consolidation().start_daemon(interval_hours=4)
        status["replay_consolidation"] = "ok"
    except Exception as e:
        status["replay_consolidation"] = f"err:{e}"
    print(f"[LivingSubstrate] startup status: {status}")
    return status


def substrate_snapshot() -> Dict[str, Any]:
    """One-stop introspection across all substrate layers."""
    snap: Dict[str, Any] = {}
    try:
        from core.world_model_latent import get_world_model_latent
        snap["world_model"] = get_world_model_latent().snapshot()
    except Exception as e:
        snap["world_model"] = {"err": str(e)}
    try:
        from core.state_space_memory import get_ssm_memory
        snap["ssm_memory"] = get_ssm_memory().snapshot()
    except Exception as e:
        snap["ssm_memory"] = {"err": str(e)}
    try:
        from core.moe_router import get_moe_router
        snap["moe_router"] = get_moe_router().snapshot()
    except Exception as e:
        snap["moe_router"] = {"err": str(e)}
    try:
        from core.homeostasis import get_homeostasis
        snap["homeostasis"] = get_homeostasis().snapshot()
    except Exception as e:
        snap["homeostasis"] = {"err": str(e)}
    try:
        from core.embodied_self import get_embodied_self
        snap["embodied_self"] = get_embodied_self().snapshot()
    except Exception as e:
        snap["embodied_self"] = {"err": str(e)}
    try:
        from core.hierarchical_predictive_coding import get_hpc
        snap["hpc"] = get_hpc().snapshot()
    except Exception as e:
        snap["hpc"] = {"err": str(e)}
    # replay_consolidation snapshot
    try:
        from core.replay_consolidation import get_replay_consolidation
        snap["replay_consolidation"] = get_replay_consolidation().snapshot()
    except Exception as e:
        snap["replay_consolidation"] = {"err": str(e)}
    return snap
