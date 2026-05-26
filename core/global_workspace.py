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

GWT Ignition (v2)
-----------------
  If internal drives or surprise exceed thresholds, ignite() proactively fires
  MoE expert calls in background daemon threads BEFORE the user's message arrives.
  Results are cached and injected into the next gate_substrate_for_prompt() call
  so the answer is already warming when the user speaks.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── thresholds (named constants so they're easy to tune) ─────────────────────
_DRIVE_THRESHOLD        = 0.6    # drives above this enter the broadcast
_FREE_ENERGY_THRESHOLD  = 0.4    # world model surprise threshold
_HPC_ERROR_THRESHOLD    = 0.5    # per-level prediction error threshold
_BODY_PAIN_THRESHOLD    = 0.3    # pain level that warrants broadcasting
_BODY_COMFORT_THRESHOLD = 0.7    # high comfort worth noting (flow state)
_MAX_PROMPT_CHARS       = 600    # hard ceiling ~ 150 tokens at ~4 chars/token

# ── ignition thresholds ───────────────────────────────────────────────────────
_IGN_CURIOSITY_THRESHOLD  = 0.75   # curiosity drive level to fire probe
_IGN_SURPRISE_THRESHOLD   = 0.60   # world model free-energy to fire anomaly check
_IGN_LONELINESS_THRESHOLD = 0.80   # loneliness drive level to fire user check-in
_IGN_COOLDOWN_CURIOSITY   = 600    # 10 min between curiosity ignitions (seconds)
_IGN_COOLDOWN_SURPRISE    = 300    # 5 min between surprise ignitions
_IGN_COOLDOWN_LONELINESS  = 1800   # 30 min between loneliness ignitions
_IGN_GLOBAL_COOLDOWN      = 300    # max 1 ignition per 5 min total
_IGN_RESULT_TTL           = 120    # inject ignition result if <2 min old

# ── data storage ─────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data" / "global_workspace"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_IGNITION_LOG = _DATA_DIR / "ignition_log.jsonl"


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


# ── IgnitionEvent dataclass ───────────────────────────────────────────────────

@dataclass
class IgnitionEvent:
    """
    Records a proactive GWT ignition: a background MoE expert call fired
    because an internal drive or surprise exceeded its threshold.
    """
    trigger: str         # "curiosity" | "surprise" | "loneliness"
    level: float         # 0–1 signal strength that caused the ignition
    fired_at: float      # time.time() when the ignition was triggered
    module_called: str   # which expert was proactively invoked
    result_summary: str  # short string summary of what was fetched
    latency_ms: float    # end-to-end time from fire to result


class GlobalWorkspace:
    """
    GWT-style gating layer with proactive ignition.

    Call gate_substrate_for_prompt() each turn to get the slim broadcast dict,
    then format_for_prompt() to convert it to a string ready to inject into
    the LLM prompt.

    Additionally, call ignite(substrate_snap) periodically (e.g. every 30s)
    to check internal drives and fire proactive background MoE expert calls
    when curiosity / surprise / loneliness spike above their thresholds.
    """

    def __init__(self):
        self._mu = threading.Lock()

        # ignition state
        self._last_ignition_time: float = 0.0          # last global ignition timestamp
        self._last_ignition_by_trigger: Dict[str, float] = {}  # per-trigger last time
        self._last_ignition_result: Optional[IgnitionEvent] = None
        self._ignition_history: List[IgnitionEvent] = []       # in-memory ring (last 50)

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
            Keys: memory | drives | attention | body | surprise | routing | ignition
        """
        if not isinstance(substrate_snap, dict):
            substrate_snap = {}

        gated: Dict[str, str] = {}

        # ── 1. SSM MEMORY — always broadcast ─────────────────────────────────
        ssm = substrate_snap.get("ssm_memory", {})
        if isinstance(ssm, dict) and not _has_error(ssm):
            steps   = ssm.get("steps", 0)
            horizon = ssm.get("effective_horizon_steps", ssm.get("effective_horizon", 0))
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
                channels = wm.get("channels", wm.get("channel_surprise", {}))
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

        # ── 7. IGNITION RESULT — inject if recent (<2 min old) ──────────────
        with self._mu:
            event = self._last_ignition_result
        if event is not None:
            age = time.time() - event.fired_at
            if age < _IGN_RESULT_TTL:
                gated["ignition"] = (
                    f"{event.trigger} -> {event.module_called}: "
                    f"{event.result_summary[:100]}"
                )

        return gated

    # ── ignition ──────────────────────────────────────────────────────────────

    def ignite(self, substrate_snap: dict) -> Optional[IgnitionEvent]:
        """
        GWT ignition check. Runs after each substrate update.

        Examines internal drives and world model surprise; if a threshold is
        crossed and rate-limiting permits, fires a proactive MoE expert call
        in a daemon background thread and records the IgnitionEvent.

        Parameters
        ----------
        substrate_snap : dict
            Same format as accepted by gate_substrate_for_prompt().

        Returns
        -------
        IgnitionEvent if an ignition was triggered this call, else None.
        Note: the MoE call runs async — the event is returned immediately
        with result_summary="pending" and updated when the thread completes.
        """
        if not isinstance(substrate_snap, dict):
            return None

        now = time.time()

        # ── Global rate-limit: max 1 ignition per 5 min ──────────────────────
        with self._mu:
            since_last_global = now - self._last_ignition_time
            if since_last_global < _IGN_GLOBAL_COOLDOWN:
                return None

        # ── Read drives and free energy ───────────────────────────────────────
        homeo = substrate_snap.get("homeostasis", {})
        drives: Dict[str, float] = {}
        if isinstance(homeo, dict):
            raw = homeo.get("drives", {})
            if isinstance(raw, dict):
                drives = {k: float(v) for k, v in raw.items() if isinstance(v, (int, float))}

        wm = substrate_snap.get("world_model", {})
        ema_fe = 0.0
        if isinstance(wm, dict):
            ema_fe = float(wm.get("ema_free_energy", 0.0))

        # ── Determine which trigger fires (priority: curiosity > surprise > loneliness)
        trigger      = None
        level        = 0.0
        probe_text   = ""
        cooldown     = 0

        curiosity  = drives.get("curiosity",  0.0)
        loneliness = drives.get("loneliness", 0.0)

        last_curiosity  = self._last_ignition_by_trigger.get("curiosity",  0.0)
        last_surprise   = self._last_ignition_by_trigger.get("surprise",   0.0)
        last_loneliness = self._last_ignition_by_trigger.get("loneliness", 0.0)

        if (curiosity > _IGN_CURIOSITY_THRESHOLD
                and (now - last_curiosity) > _IGN_COOLDOWN_CURIOSITY):
            trigger    = "curiosity"
            level      = curiosity
            probe_text = "curiosity probe: what should LOVE explore right now?"
            cooldown   = _IGN_COOLDOWN_CURIOSITY

        elif (ema_fe > _IGN_SURPRISE_THRESHOLD
                and (now - last_surprise) > _IGN_COOLDOWN_SURPRISE):
            trigger    = "surprise"
            level      = ema_fe
            probe_text = "high surprise: investigate anomaly"
            cooldown   = _IGN_COOLDOWN_SURPRISE

        elif (loneliness > _IGN_LONELINESS_THRESHOLD
                and (now - last_loneliness) > _IGN_COOLDOWN_LONELINESS):
            trigger    = "loneliness"
            level      = loneliness
            probe_text = "user check-in: what does the user need right now?"
            cooldown   = _IGN_COOLDOWN_LONELINESS

        if trigger is None:
            return None

        # ── Commit the ignition (reserve the slot before firing thread) ───────
        with self._mu:
            # Double-check global cooldown under lock
            if (time.time() - self._last_ignition_time) < _IGN_GLOBAL_COOLDOWN:
                return None
            self._last_ignition_time = now
            self._last_ignition_by_trigger[trigger] = now

        # Create the event with "pending" summary — thread will update it
        event = IgnitionEvent(
            trigger=trigger,
            level=level,
            fired_at=now,
            module_called="pending",
            result_summary="pending",
            latency_ms=0.0,
        )

        # Store immediately so get_last_ignition() works before thread finishes
        with self._mu:
            self._last_ignition_result = event

        # ── Fire background daemon thread ─────────────────────────────────────
        def _run(evt: IgnitionEvent, query: str):
            t0 = time.time()
            try:
                from core.moe_router import get_moe_router
                router = get_moe_router()
                results = router.route(query, {})
                if results:
                    winning = results[0]
                    expert  = winning.get("expert", "unknown")
                    output  = winning.get("output")
                    summary = _summarise_output(output)
                else:
                    expert  = "none"
                    summary = "no experts available"
            except Exception as ex:
                expert  = "error"
                summary = f"ignition error: {ex}"

            dt_ms = (time.time() - t0) * 1000.0

            # Update the event in-place (dataclass is mutable)
            evt.module_called = expert
            evt.result_summary = summary
            evt.latency_ms = round(dt_ms, 1)

            # Persist to log
            _append_ignition_log(evt)

            # Keep in-memory ring (last 50)
            with self._mu:
                self._ignition_history.append(evt)
                if len(self._ignition_history) > 50:
                    self._ignition_history = self._ignition_history[-50:]

        t = threading.Thread(target=_run, args=(event, probe_text), daemon=True)
        t.start()

        return event

    # ── ignition inspection ────────────────────────────────────────────────────

    def get_last_ignition(self) -> Optional[dict]:
        """Returns the most recent IgnitionEvent as a dict, or None."""
        with self._mu:
            ev = self._last_ignition_result
        if ev is None:
            return None
        return asdict(ev)

    def get_ignition_history(self, n: int = 10) -> List[dict]:
        """
        Returns the last N IgnitionEvents from the persistent log file.
        Falls back to the in-memory ring if the log is unavailable.
        """
        records: List[dict] = []
        try:
            if _IGNITION_LOG.exists():
                lines = _IGNITION_LOG.read_text(encoding="utf-8").splitlines()
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
                    if len(records) >= n:
                        break
                return records
        except Exception:
            pass

        # Fallback: in-memory ring
        with self._mu:
            ring = list(self._ignition_history)
        return [asdict(ev) for ev in reversed(ring)][:n]

    # ── snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """
        Returns a compact status dict for monitoring / introspection.

        Keys:
          last_ignition      : most recent IgnitionEvent as dict, or None
          ignition_count_24h : how many ignitions fired in the last 24 h
          rate_limited       : True if global cooldown is currently active
          thresholds         : dict of the current threshold constants
        """
        now = time.time()
        with self._mu:
            last_ev       = self._last_ignition_result
            since_global  = now - self._last_ignition_time
            ring_copy     = list(self._ignition_history)

        # Count ignitions in last 24h (from persistent log if possible)
        count_24h = 0
        cutoff_24h = now - 86400
        try:
            if _IGNITION_LOG.exists():
                for line in _IGNITION_LOG.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("fired_at", 0) >= cutoff_24h:
                            count_24h += 1
                    except Exception:
                        pass
        except Exception:
            count_24h = sum(1 for ev in ring_copy if ev.fired_at >= cutoff_24h)

        return {
            "last_ignition": asdict(last_ev) if last_ev else None,
            "ignition_count_24h": count_24h,
            "rate_limited": since_global < _IGN_GLOBAL_COOLDOWN,
            "thresholds": {
                "curiosity": _IGN_CURIOSITY_THRESHOLD,
                "surprise": _IGN_SURPRISE_THRESHOLD,
                "loneliness": _IGN_LONELINESS_THRESHOLD,
                "global_cooldown_s": _IGN_GLOBAL_COOLDOWN,
            },
        }

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
            ignition: <proactive probe result, if recent>

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
            ("ignition",  "ignition"),
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


def _summarise_output(output: Any) -> str:
    """Convert MoE expert output to a short human-readable summary string."""
    if output is None:
        return "no result"
    if isinstance(output, str):
        return output[:200].strip() or "empty string"
    if isinstance(output, dict):
        # Try to find a useful key
        for key in ("summary", "result", "text", "answer", "content", "message"):
            val = output.get(key)
            if val and isinstance(val, str):
                return val[:200].strip()
        # Fallback: first non-empty string value
        for val in output.values():
            if isinstance(val, str) and val.strip():
                return val[:200].strip()
        return str(output)[:200]
    if isinstance(output, list):
        if output:
            return _summarise_output(output[0])
        return "empty list"
    return str(output)[:200]


def _append_ignition_log(event: IgnitionEvent) -> None:
    """Append an IgnitionEvent to the persistent JSONL log (best-effort)."""
    try:
        record = asdict(event)
        record["fired_at_iso"] = datetime.fromtimestamp(
            event.fired_at, tz=timezone.utc
        ).isoformat()
        line = json.dumps(record, ensure_ascii=False)
        with open(_IGNITION_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass  # logging must never crash the caller


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
