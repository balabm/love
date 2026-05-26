"""
LOVE Global Workspace — GWT-style attention gating for LLM prompts.

Baars' Global Workspace Theory: there is a serial bottleneck (the "stage")
where only one coalition of modules' outputs can be "broadcast" at a time.
Everything else remains pre-conscious (available but not injected into the prompt).

Here:
  - The HPC attention weights (per level) determine which substrate keys are broadcast
  - The MoE router's winning expert is always broadcast (it won the routing contest)
  - Body/homeostasis signals are broadcast only when they exceed pain threshold
  - The SSM context vector is always broadcast (it IS the compressed past)
  - Raw world model state is broadcast only when surprise is high (>0.5)

Result: instead of injecting 500 tokens of substrate into every prompt,
we inject ~80-120 tokens of the most attention-worthy signals.

Broadcast rules summary
-----------------------
  ALWAYS   : ssm_memory  — compressed history (the "what have I lived through" vector)
  THRESHOLD: homeostasis drives > 0.6 on any single drive
  THRESHOLD: world_model.ema_free_energy > 0.4  (struggling to predict = noteworthy)
  CONDITIONAL: moe_winner is not None and not "core_agent_chat"
  CONDITIONAL: top HPC level error > 0.5
  CONDITIONAL: embodied_self pain > 0.3 OR comfort > 0.7
  NEVER    : raw numpy arrays, keys containing "err"
"""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional

# ── thresholds (named constants so they're easy to tune) ─────────────────────
_DRIVE_THRESHOLD        = 0.6    # drives above this enter the broadcast
_FREE_ENERGY_THRESHOLD  = 0.4    # world model surprise threshold
_HPC_ERROR_THRESHOLD    = 0.5    # per-level prediction error threshold
_BODY_PAIN_THRESHOLD    = 0.3    # pain level that warrants broadcasting
_BODY_COMFORT_THRESHOLD = 0.7    # high comfort worth noting (flow state)
_MAX_PROMPT_CHARS       = 600    # hard ceiling ~ 150 tokens at ~4 chars/token


# ── descriptions for MoE experts (mirrors living_substrate seed descriptions) ─
_EXPERT_DESCRIPTIONS: Dict[str, str] = {
    "core_memory_recall":  "recalling past conversations and facts",
    "web_search":          "live web search for current information",
    "finance_scan":        "scanning markets and portfolio",
    "task_overview":       "reviewing tasks and deadlines",
    "fitness_overview":    "checking fitness and recovery status",
    "doc_analysis":        "analysing a document or file",
    "self_introspection":  "reflecting on internal state",
    "core_agent_chat":     "",   # routing home — not interesting to broadcast
}

# ── HPC level labels for human-readable output ────────────────────────────────
_HPC_LEVEL_LABELS: Dict[str, str] = {
    "L1_sensory":  "sensory (raw surprise)",
    "L2_context":  "context (topic drift)",
    "L3_plan":     "plan (narrative shift)",
}


class GlobalWorkspace:
    """
    GWT-style gating layer.  Call gate_substrate_for_prompt() each turn to get
    the slim broadcast dict, then format_for_prompt() to convert it to a string
    ready to inject into the LLM prompt.
    """

    def __init__(self):
        self._mu = threading.Lock()

    # ── primary API ───────────────────────────────────────────────────────────

    def gate_substrate_for_prompt(
        self,
        substrate_snap: Any,
        hpc_attention: Dict[str, float],
        moe_winner: str,
    ) -> Dict[str, str]:
        """
        Filter a full substrate snapshot down to only the signals worth
        broadcasting into the LLM prompt.

        Parameters
        ----------
        substrate_snap : dict
            Output of living_substrate.substrate_snapshot() — keys are module
            names, values are their own snapshot dicts.
        hpc_attention : dict
            Output of hpc.snapshot()["attention"] or hpc.attention() —
            {"L1_sensory": float, "L2_context": float, "L3_plan": float}
        moe_winner : str
            The expert name that won the MoE routing contest this turn.

        Returns
        -------
        dict[str, str]
            Slim dict with string values only — safe to format into a prompt.
            Keys: memory | drives | attention | body | surprise | routing
        """
        if not isinstance(substrate_snap, dict):
            substrate_snap = {}

        gated: Dict[str, str] = {}

        # ── 1. SSM MEMORY — always broadcast ─────────────────────────────────
        ssm = substrate_snap.get("ssm_memory", {})
        if isinstance(ssm, dict) and not _has_error(ssm):
            steps   = ssm.get("steps", 0)
            horizon = ssm.get("effective_horizon_steps", 0)
            norm    = ssm.get("state_norm", 0)
            if steps > 0:
                gated["memory"] = (
                    f"{steps} steps compressed, "
                    f"horizon ~{int(horizon)} steps, "
                    f"state norm {norm:.2f}"
                )
            else:
                gated["memory"] = "initialising"

        # ── 2. HOMEOSTASIS DRIVES — threshold-gated ───────────────────────────
        homeo = substrate_snap.get("homeostasis", {})
        if isinstance(homeo, dict) and not _has_error(homeo):
            drives_raw = homeo.get("drives", {})
            if isinstance(drives_raw, dict):
                hot_drives = {
                    k: v for k, v in drives_raw.items()
                    if isinstance(v, (int, float)) and float(v) > _DRIVE_THRESHOLD
                }
                if hot_drives:
                    dominant = max(hot_drives, key=hot_drives.get)
                    val      = hot_drives[dominant]
                    # Format: "curiosity 0.81 (also: loneliness 0.72)"
                    others   = [
                        f"{k} {v:.2f}" for k, v in hot_drives.items()
                        if k != dominant
                    ]
                    text = f"{dominant} {val:.2f}"
                    if others:
                        text += f" (also: {', '.join(others)})"
                    gated["drives"] = text

        # ── 3. WORLD MODEL SURPRISE — free-energy-gated ──────────────────────
        wm = substrate_snap.get("world_model", {})
        if isinstance(wm, dict) and not _has_error(wm):
            ema_fe = float(wm.get("ema_free_energy", 0.0))
            if ema_fe > _FREE_ENERGY_THRESHOLD:
                channels = wm.get("channels", {})
                top_ch   = ""
                if isinstance(channels, dict) and channels:
                    top_ch = max(channels, key=channels.get)
                gated["surprise"] = (
                    f"free-energy {ema_fe:.3f}"
                    + (f" (hottest channel: {top_ch})" if top_ch else "")
                )

        # ── 4. HPC ATTENTION — error-threshold gated ─────────────────────────
        # Pull error values from substrate if available; fall back to hpc_attention
        hpc_snap = substrate_snap.get("hpc", {})
        level_errors: Dict[str, float] = {}
        if isinstance(hpc_snap, dict) and not _has_error(hpc_snap):
            levels = hpc_snap.get("levels", {})
            if isinstance(levels, dict):
                for lvl_name, lvl_data in levels.items():
                    if isinstance(lvl_data, dict):
                        level_errors[lvl_name] = float(lvl_data.get("error", 0.0))

        # Find the highest-attention level
        if hpc_attention:
            top_level = max(hpc_attention, key=hpc_attention.get)
            top_error = level_errors.get(top_level, 0.0)
            if top_error > _HPC_ERROR_THRESHOLD:
                label       = _HPC_LEVEL_LABELS.get(top_level, top_level)
                attn_weight = hpc_attention[top_level]
                activity    = ""
                if isinstance(hpc_snap, dict):
                    activity = hpc_snap.get("inferred_activity", "")
                gated["attention"] = (
                    f"{label} error {top_error:.3f} "
                    f"(attention weight {attn_weight:.2f})"
                    + (f" — activity: {activity}" if activity and activity != "unknown" else "")
                )

        # ── 5. EMBODIED SELF / BODY — pain or comfort threshold ──────────────
        body = substrate_snap.get("embodied_self", {})
        if isinstance(body, dict) and not _has_error(body):
            pain    = float(body.get("pain",    0.0))
            comfort = float(body.get("comfort", 0.0))
            if pain > _BODY_PAIN_THRESHOLD:
                gated["body"] = f"pain {pain:.2f} (cpu/ram/temp stress)"
            elif comfort > _BODY_COMFORT_THRESHOLD:
                gated["body"] = f"comfort {comfort:.2f} (flow state)"

        # ── 6. MOE WINNER — always broadcast unless it's the boring fallback ──
        if moe_winner and moe_winner != "core_agent_chat":
            desc = _EXPERT_DESCRIPTIONS.get(moe_winner, moe_winner.replace("_", " "))
            if desc:
                gated["routing"] = f"{moe_winner} ({desc})"

        return gated

    # ── formatting ────────────────────────────────────────────────────────────

    def format_for_prompt(self, gated: Dict[str, str]) -> str:
        """
        Convert the gated dict to a compact, readable string ≤ ~150 tokens.

        Output format:
            [LOVE substrate]
            memory: <ssm summary>
            drives: <dominant drive>
            attention: <top HPC level>
            body: <pain/comfort>
            surprise: <free energy>
            routing: <moe winner>

        Returns empty string if gated is empty.
        """
        if not gated:
            return ""

        # Defined display order + label overrides
        field_order = [
            ("memory",    "memory"),
            ("drives",    "drives"),
            ("attention", "attention"),
            ("body",      "body"),
            ("surprise",  "surprise"),
            ("routing",   "routing"),
        ]

        lines = ["[LOVE substrate]"]
        for key, label in field_order:
            val = gated.get(key, "")
            if val:
                lines.append(f"{label}: {val}")

        # Emit any extra keys not in the predefined order
        known = {k for k, _ in field_order}
        for key, val in gated.items():
            if key not in known and val:
                lines.append(f"{key}: {val}")

        result = "\n".join(lines)

        # Hard cap — truncate to avoid token blowout
        if len(result) > _MAX_PROMPT_CHARS:
            result = result[:_MAX_PROMPT_CHARS].rsplit("\n", 1)[0] + "\n[...truncated]"

        return result

    # ── gate check ────────────────────────────────────────────────────────────

    def should_inject(self, gated: Dict[str, str]) -> bool:
        """
        Return True if there is at least one signal worth injecting.
        If the only thing present is the SSM memory line (which just says
        "initialising" or a near-zero step count) we still inject it — the
        compressed history is always meaningful.
        """
        if not gated:
            return False

        # Always inject if any field other than memory has content
        non_memory = {k: v for k, v in gated.items() if k != "memory"}
        if non_memory:
            return True

        # Memory-only case: inject unless it's literally just "initialising"
        mem_val = gated.get("memory", "")
        return bool(mem_val) and mem_val != "initialising"


# ── helpers ───────────────────────────────────────────────────────────────────

def _has_error(d: dict) -> bool:
    """Return True if the snapshot dict contains an error marker."""
    for k in d:
        if "err" in str(k).lower():
            return True
    return False


def _is_numpy(val: Any) -> bool:
    """Return True if value is a numpy array (or similar) — never inject these."""
    # Avoid importing numpy at module level (heavy dep); check by type name.
    t = type(val).__name__
    return t in ("ndarray", "matrix", "memmap")


# ── module-level singleton ────────────────────────────────────────────────────

_gw_instance: Optional[GlobalWorkspace] = None
_gw_lock = threading.Lock()


def get_global_workspace() -> GlobalWorkspace:
    """Return the module-level GlobalWorkspace singleton."""
    global _gw_instance
    if _gw_instance is None:
        with _gw_lock:
            if _gw_instance is None:
                _gw_instance = GlobalWorkspace()
    return _gw_instance
