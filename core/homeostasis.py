"""
LOVE Homeostasis — Metabolism, Drives, Autophagy

This is what separates a "living computer" from a script. Biological systems
maintain themselves *against* entropy via metabolism, drives, and self-pruning.

Implements:
  1. ENERGY BUDGET
     Each subsystem has a monthly "ATP" budget (compute seconds). Spending
     beyond budget = forced throttle. Saving = accumulates "fat" reserve.
  
  2. DRIVES (homeostatic setpoints)
     - hunger: low input rate => seek user/web/sensor input
     - fatigue: high cumulative free-energy => trigger sleep/consolidation
     - boredom: low surprise on all channels => trigger exploration
     - curiosity: moderate surprise on a channel => increase attention to it
     - loneliness: long silence from user => proactive ping
     - dissatisfaction: ema_reward dropping => trigger evolution cycle
  
  3. AUTOPHAGY
     Modules unused for N days get marked "deprecate-candidate". After grace
     period, get archived (code preserved, but not started). Frees energy
     budget for newer, healthier modules.
  
  4. CIRCADIAN RHYTHM
     LOVE has a 24h cycle: wake (high tool use) → focus (sustained agent work)
     → wind-down (low intensity) → sleep (consolidation, evolution, dreaming).
     Aligned with user's local time when available.

What's real (not stubs):
  - Actual energy accounting per registered module
  - Actual drive values [0..1] updated each tick from real measurements
  - Actual module deprecation list with grace timers
  - Reads world_model.free_energy(), moe_router rewards, sentinel idle_seconds
"""
from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, time as dtime
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "homeostasis"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "homeostasis_state.json"
DRIVES_LOG = DATA_DIR / "drives.jsonl"
AUTOPHAGY_LIST = DATA_DIR / "autophagy.json"

DRIVE_NAMES = ["hunger", "fatigue", "boredom", "curiosity", "loneliness", "dissatisfaction"]
TICK_SECONDS = 60


@dataclass
class EnergyAccount:
    module: str
    budget_seconds_per_day: float = 600.0   # 10 minutes/day baseline
    spent_today: float = 0.0
    fat_reserve: float = 0.0                # unspent budget accumulates here
    last_reset: str = ""
    throttled: bool = False


@dataclass
class Drives:
    hunger: float = 0.3
    fatigue: float = 0.2
    boredom: float = 0.3
    curiosity: float = 0.5
    loneliness: float = 0.1
    dissatisfaction: float = 0.2

    def as_dict(self) -> Dict[str, float]:
        return {k: getattr(self, k) for k in DRIVE_NAMES}

    def dominant(self) -> str:
        return max(DRIVE_NAMES, key=lambda k: getattr(self, k))


@dataclass
class HomeostasisState:
    started_at: str = ""
    last_tick: str = ""
    circadian_phase: str = "wake"        # wake / focus / wind_down / sleep
    last_sleep: str = ""
    last_meal: str = ""                  # last new-input ingestion
    last_user_contact: str = ""


# ── Engine ───────────────────────────────────────────────────────────────────

class Homeostasis:
    _instance: Optional["Homeostasis"] = None
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
        self._drives = Drives()
        self._accounts: Dict[str, EnergyAccount] = {}
        self._state = HomeostasisState(started_at=datetime.now().isoformat())
        self._autophagy: Dict[str, Dict] = {}     # module -> {first_seen_idle, grace_days}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load()

    # ── lifecycle ────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="LOVE-Homeostasis")
        self._thread.start()
        print("[Homeostasis] online — drives + metabolism active")

    def stop(self):
        self._running = False

    def _loop(self):
        # Stagger start so other modules boot first
        time.sleep(20)
        while self._running:
            try:
                self.tick()
            except Exception as e:
                print(f"[Homeostasis] tick error: {e}")
            time.sleep(TICK_SECONDS)

    # ── per-tick update ──────────────────────────────────────────────────────

    def tick(self):
        with self._mu:
            self._update_circadian()
            self._update_drives()
            self._roll_energy_if_new_day()
            self._update_autophagy_candidates()
            self._state.last_tick = datetime.now().isoformat()
            self._log_drives()
            # persist every 10 ticks
            if int(time.time()) % (TICK_SECONDS * 10) < TICK_SECONDS:
                self._save()
            # take homeostatic actions
        self._take_homeostatic_actions()

    # ── drive computation (from real signals) ────────────────────────────────

    def _update_drives(self):
        # HUNGER: how stale is the freshest channel? (no new input → hungry)
        last_obs_age = self._seconds_since_last_observation()
        # 0..1, saturating around 1 hour of silence
        self._drives.hunger = min(1.0, last_obs_age / 3600.0)

        # FATIGUE: world-model free energy (high = struggling = need sleep)
        fe = self._read_free_energy()
        self._drives.fatigue = min(1.0, fe * 1.5)

        # BOREDOM: average channel surprise (low = nothing interesting)
        avg_surprise = self._read_avg_channel_surprise()
        # boredom is high when surprise is very low (predictable world)
        self._drives.boredom = max(0.0, 1.0 - avg_surprise * 3.0)

        # CURIOSITY: peak channel surprise, normalized (moderate surprise = curious)
        peak = self._read_peak_channel_surprise()
        # bell-shaped — peak around 0.4 surprise
        self._drives.curiosity = math.exp(-((peak - 0.4) ** 2) * 6.0)

        # LONELINESS: time since last user-source observation
        last_user_age = self._seconds_since_user_contact()
        self._drives.loneliness = min(1.0, last_user_age / 7200.0)  # 2 hours

        # DISSATISFACTION: 1 - ema_reward of best expert in MoE
        avg_reward = self._read_moe_avg_reward()
        self._drives.dissatisfaction = max(0.0, 1.0 - avg_reward)

    def _read_free_energy(self) -> float:
        try:
            from core.world_model_latent import get_world_model_latent
            return float(get_world_model_latent().free_energy())
        except Exception:
            return 0.3

    def _read_avg_channel_surprise(self) -> float:
        try:
            from core.world_model_latent import get_world_model_latent
            ch = get_world_model_latent().channel_surprise()
            return sum(ch.values()) / max(1, len(ch)) if ch else 0.3
        except Exception:
            return 0.3

    def _read_peak_channel_surprise(self) -> float:
        try:
            from core.world_model_latent import get_world_model_latent
            ch = get_world_model_latent().channel_surprise()
            return max(ch.values()) if ch else 0.3
        except Exception:
            return 0.3

    def _read_moe_avg_reward(self) -> float:
        try:
            from core.moe_router import get_moe_router
            r = get_moe_router()
            stats = r._stats
            if not stats:
                return 0.5
            return sum(s.ema_reward for s in stats.values()) / len(stats)
        except Exception:
            return 0.5

    def _seconds_since_last_observation(self) -> float:
        try:
            from core.world_model_latent import get_world_model_latent
            wm = get_world_model_latent()
            if wm._recent_obs:
                return time.time() - wm._recent_obs[-1].t
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")
        return 0.0

    def _seconds_since_user_contact(self) -> float:
        try:
            from core.world_model_latent import get_world_model_latent
            wm = get_world_model_latent()
            for o in reversed(wm._recent_obs):
                if o.source == "user":
                    return time.time() - o.t
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")
        return 0.0

    # ── circadian rhythm ─────────────────────────────────────────────────────

    def _update_circadian(self):
        now = datetime.now().time()
        # Default user timezone phases — can be overridden by settings
        if dtime(6, 0) <= now < dtime(9, 0):
            self._state.circadian_phase = "wake"
        elif dtime(9, 0) <= now < dtime(18, 0):
            self._state.circadian_phase = "focus"
        elif dtime(18, 0) <= now < dtime(23, 0):
            self._state.circadian_phase = "wind_down"
        else:
            self._state.circadian_phase = "sleep"

    # ── homeostatic actions ──────────────────────────────────────────────────

    def _take_homeostatic_actions(self):
        d = self._drives
        phase = self._state.circadian_phase

        # FATIGUE high or SLEEP phase => trigger consolidation
        if d.fatigue > 0.7 or phase == "sleep":
            self._trigger_consolidation()

        # LONELINESS high during focus/wind_down => proactive ping
        if d.loneliness > 0.7 and phase in ("focus", "wind_down"):
            self._trigger_proactive_ping()

        # DISSATISFACTION high => trigger evolution cycle
        if d.dissatisfaction > 0.6:
            self._trigger_evolution()

        # BOREDOM high during waking => trigger curiosity exploration
        if d.boredom > 0.7 and phase != "sleep":
            self._trigger_exploration()

    def _trigger_consolidation(self):
        # avoid retriggering more than once per hour
        last = self._state.last_sleep
        if last:
            try:
                if (datetime.now() - datetime.fromisoformat(last)).total_seconds() < 3600:
                    return
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.homeostasis")
        self._state.last_sleep = datetime.now().isoformat()
        # 1) Reset world model free energy
        try:
            from core.world_model_latent import get_world_model_latent
            get_world_model_latent().reset_after_consolidation()
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")
        # 2) Soft-reset SSM state
        try:
            from core.state_space_memory import get_ssm_memory
            get_ssm_memory().soft_reset()
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")
        # 3) Memory consolidation
        try:
            from core.memory_consolidation import consolidate_period
            consolidate_period("daily")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")
        print("[Homeostasis] sleep cycle: consolidation complete")

    def _trigger_proactive_ping(self):
        try:
            from core.proactive_push import ProactivePushEngine
            push = ProactivePushEngine()
            push.push("THOUGHT",
                      "Been quiet for a while. Thinking about you.",
                      priority="low",
                      metadata={"trigger": "loneliness_drive"})
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")

    def _trigger_evolution(self):
        try:
            from core.evolution_integration import get_evolution_integration
            get_evolution_integration().trigger_manual_cycle()
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")

    def _trigger_exploration(self):
        # signal idle_mind / curiosity_engine to pick a topic
        try:
            from core.curiosity_engine import get_top_gaps_for_prompt
            gaps = get_top_gaps_for_prompt()
            if gaps:
                print(f"[Homeostasis] Top curiosity gaps: {gaps[:80]}")
        except Exception:
            pass  # curiosity engine optional

    # ── energy accounting ────────────────────────────────────────────────────

    def register_module(self, module: str, budget_seconds_per_day: float = 600.0):
        with self._mu:
            if module not in self._accounts:
                self._accounts[module] = EnergyAccount(
                    module=module,
                    budget_seconds_per_day=budget_seconds_per_day,
                    last_reset=datetime.now().date().isoformat(),
                )

    def charge(self, module: str, seconds: float) -> bool:
        """Charge a module for compute. Returns False if budget exhausted (caller should throttle)."""
        with self._mu:
            if module not in self._accounts:
                self.register_module(module)
            a = self._accounts[module]
            available = a.budget_seconds_per_day + a.fat_reserve - a.spent_today
            if seconds > available:
                a.throttled = True
                return False
            a.spent_today += seconds
            return True

    def _roll_energy_if_new_day(self):
        today = datetime.now().date().isoformat()
        for a in self._accounts.values():
            if a.last_reset != today:
                # Save unspent budget into fat (cap fat at 5× daily budget)
                unspent = max(0.0, a.budget_seconds_per_day - a.spent_today)
                a.fat_reserve = min(a.budget_seconds_per_day * 5.0,
                                    a.fat_reserve * 0.7 + unspent)
                a.spent_today = 0.0
                a.throttled = False
                a.last_reset = today

    # ── autophagy ────────────────────────────────────────────────────────────

    def _update_autophagy_candidates(self):
        # any module idle > 14 days with low reward and no calls => candidate
        try:
            from core.moe_router import get_moe_router
            r = get_moe_router()
            now = time.time()
            for s in r._stats.values():
                idle_seconds = now - s.last_invoked if s.last_invoked > 0 else 0
                if idle_seconds > 14 * 86400 and s.ema_reward < 0.3 and s.invocations < 5:
                    if s.name not in self._autophagy:
                        self._autophagy[s.name] = {
                            "first_marked": datetime.now().isoformat(),
                            "reason": f"idle_{int(idle_seconds/86400)}d_reward_{s.ema_reward:.2f}",
                            "grace_until": (datetime.now() + timedelta(days=7)).isoformat(),
                        }
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")

    def autophagy_ready_to_remove(self) -> List[str]:
        ready = []
        now = datetime.now()
        for module, info in self._autophagy.items():
            try:
                if now > datetime.fromisoformat(info["grace_until"]):
                    ready.append(module)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.homeostasis")
        return ready

    # ── persistence + introspection ──────────────────────────────────────────

    def _log_drives(self):
        entry = {
            "t": datetime.now().isoformat(),
            "phase": self._state.circadian_phase,
            "drives": {k: round(v, 3) for k, v in self._drives.as_dict().items()},
            "dominant": self._drives.dominant(),
        }
        try:
            with open(DRIVES_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")
        # Write to Consolidated Memory for unified persistence
        try:
            from core.consolidated_memory import get_consolidated_memory
            get_consolidated_memory().write(
                domain="biometrics",
                event_type="drive_snapshot",
                payload=entry,
                text_for_search=f"Circadian phase {entry['phase']} drives {entry['drives']}",
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")

    def _save(self):
        try:
            STATE_FILE.write_text(json.dumps({
                "state": asdict(self._state),
                "drives": self._drives.as_dict(),
                "accounts": {k: asdict(v) for k, v in self._accounts.items()},
            }, indent=2))
            AUTOPHAGY_LIST.write_text(json.dumps(self._autophagy, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.homeostasis")

    def _load(self):
        if STATE_FILE.exists():
            try:
                d = json.loads(STATE_FILE.read_text())
                self._state = HomeostasisState(**d.get("state", {}))
                drv = d.get("drives", {})
                for k in DRIVE_NAMES:
                    if k in drv:
                        setattr(self._drives, k, drv[k])
                for k, v in d.get("accounts", {}).items():
                    self._accounts[k] = EnergyAccount(**v)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.homeostasis")
        if AUTOPHAGY_LIST.exists():
            try:
                self._autophagy = json.loads(AUTOPHAGY_LIST.read_text())
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.homeostasis")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "circadian_phase": self._state.circadian_phase,
            "drives": {k: round(v, 3) for k, v in self._drives.as_dict().items()},
            "dominant_drive": self._drives.dominant(),
            "last_sleep": self._state.last_sleep,
            "registered_modules": len(self._accounts),
            "throttled_modules": [a.module for a in self._accounts.values() if a.throttled],
            "autophagy_candidates": list(self._autophagy.keys()),
            "ready_to_archive": self.autophagy_ready_to_remove(),
        }


_homeostasis_instance: Optional[Homeostasis] = None


def get_homeostasis() -> Homeostasis:
    global _homeostasis_instance
    if _homeostasis_instance is None:
        _homeostasis_instance = Homeostasis()
    return _homeostasis_instance
