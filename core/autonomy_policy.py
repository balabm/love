"""
Runtime autonomy policy for LOVE.

Controls how aggressive the autonomous loops should be and which components
are allowed to auto-restart or self-execute.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
POLICY_FILE = DATA_DIR / "autonomy_policy.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


DEFAULT_POLICY: Dict[str, Any] = {
    "mode": "balanced",  # safe | balanced | aggressive
    "components": {
        # Core autonomous loops
        "heartbeat": True,
        "self_improvement_daemon": True,
        "autonomous_goal_engine": True,
        "wave_engine": True,
        "self_diagnostics": True,
        "mission_queue": True,
        # Infrastructure & bridges
        "device_bridge": True,
        "notification_ingestion": True,
        # Finance & trading
        "finance_guardian": True,
        "autonomous_trading": True,
        # Coordination
        "master_orchestrator": True,
        # Wave 5 autonomous modules
        "ghost_dev": True,
        "research_engine": True,
        "proactive_push": True,
        "daily_briefing": True,
        "idle_mind": True,
        "homeostasis": True,
        "life_nudge_scheduler": True,
        "terminal_monitor": True,
        "sentinel": True,
    },
    "flap_protection": {
        "window_sec": 900,
        "max_restarts": 3,
        "cooldown_sec": 1800,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_policy() -> Dict[str, Any]:
    try:
        if POLICY_FILE.exists():
            raw = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
            return _deep_merge(DEFAULT_POLICY, raw)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.autonomy_policy")
    return deepcopy(DEFAULT_POLICY)


def save_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    merged = _deep_merge(DEFAULT_POLICY, policy or {})
    POLICY_FILE.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def set_mode(mode: str) -> Dict[str, Any]:
    mode = (mode or "").strip().lower()
    if mode not in {"safe", "balanced", "aggressive"}:
        raise ValueError("mode must be one of: safe, balanced, aggressive")

    policy = load_policy()
    policy["mode"] = mode

    # Mode presets
    if mode == "safe":
        policy["components"]["self_diagnostics"] = False
        policy["components"]["wave_engine"] = False
        policy["flap_protection"]["max_restarts"] = 2
    elif mode == "balanced":
        policy["components"]["self_diagnostics"] = True
        policy["components"]["wave_engine"] = True
        policy["flap_protection"]["max_restarts"] = 3
    else:  # aggressive
        policy["components"]["self_diagnostics"] = True
        policy["components"]["wave_engine"] = True
        policy["flap_protection"]["max_restarts"] = 5

    return save_policy(policy)

