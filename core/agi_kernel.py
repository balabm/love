"""
AGI Kernel — Unified Consciousness Loop

Wires Active Inference + Homeostasis + World Model + Hardware Symbiosis
into one continuous epistemology loop. This is LOVE's prefrontal cortex:
- Runs predictive simulations every tick
- Reads biometric stress and work energy
- Auto-throttles compute based on detected hardware (Legion vs ROG Ally)
- If stress > 0.7 or Energy < 4, kills heavy tasks and downgrades LLMs
- Publishes unified state snapshot to Neural Bus for all modules

Deterministic & Atomic. No silent failures.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
KERNEL_STATE_FILE = DATA_DIR / "agi_kernel_state.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Optional imports (graceful degradation) ──────────────────────────────────
try:
    from kernel.active_inference import ActiveInferenceEngine, PredictionDomain
    ACTIVE_INFERENCE_AVAILABLE = True
except Exception:
    ACTIVE_INFERENCE_AVAILABLE = False

try:
    from core.homeostasis import Homeostasis, Drives
    HOMEOSTASIS_AVAILABLE = True
except Exception:
    HOMEOSTASIS_AVAILABLE = False

try:
    from core.world_model_latent import get_world_model_latent
    WORLD_MODEL_AVAILABLE = True
except Exception:
    WORLD_MODEL_AVAILABLE = False

try:
    from core.sync import HardwareResourceManager, DEVICE_ROG_ALLY, DEVICE_LEGION
    HARDWARE_AVAILABLE = True
except Exception:
    HARDWARE_AVAILABLE = False

try:
    from cognition.axiological_engine import AxiologicalEngine, TaskCategory, UserState
    AXIOLOGICAL_AVAILABLE = True
except Exception:
    AXIOLOGICAL_AVAILABLE = False

try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except Exception:
    NEURAL_BUS_AVAILABLE = False


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class KernelSnapshot:
    """Heavily compressed snapshot for LLM context injection."""
    timestamp: str
    free_energy: float
    dominant_drive: str
    circadian_phase: str
    user_stress: float
    user_energy: float
    work_hours_today: float
    device_type: str
    power_mode: str
    llm_model: str
    active_predictions: List[str]
    critical_alerts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "free_energy": round(self.free_energy, 3),
            "dominant_drive": self.dominant_drive,
            "circadian_phase": self.circadian_phase,
            "user_stress": round(self.user_stress, 2),
            "user_energy": round(self.user_energy, 2),
            "work_hours_today": round(self.work_hours_today, 2),
            "device_type": self.device_type,
            "power_mode": self.power_mode,
            "llm_model": self.llm_model,
            "active_predictions": self.active_predictions,
            "critical_alerts": self.critical_alerts,
        }

    def to_prompt_text(self) -> str:
        """Compress into a single dense line for LLM system prompt."""
        return (
            f"[LOVE_KERNEL t={self.timestamp} fe={round(self.free_energy, 3)} drive={self.dominant_drive} "
            f"phase={self.circadian_phase} stress={round(self.user_stress, 2)} "
            f"energy={round(self.user_energy, 2)} work={round(self.work_hours_today, 2)}h "
            f"device={self.device_type} mode={self.power_mode} llm={self.llm_model} "
            f"alerts={','.join(self.critical_alerts) if self.critical_alerts else 'none'}]"
        )


# ── Kernel ─────────────────────────────────────────────────────────────────

class AGIKernel:
    """
    The unified consciousness loop. One thread. One truth.
    """

    _instance: Optional["AGIKernel"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init = False
            return cls._instance

    def __init__(self, tick_seconds: int = 10):
        if self._init:
            return
        self._init = True

        self.tick_seconds = tick_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Subsystems
        self._inference: Optional[Any] = None
        self._homeostasis: Optional[Homeostasis] = None
        self._axiological: Optional[AxiologicalEngine] = None
        self._hw_profile: Optional[Any] = None
        self._device_type: str = DEVICE_LEGION if HARDWARE_AVAILABLE else "unknown"
        self._power_mode: str = "high_performance"
        self._llm_model: str = "deepseek-r1:7b"

        # Runtime state
        self._last_snapshot: Optional[KernelSnapshot] = None
        self._heavy_tasks_killed: int = 0
        self._load()
        self._init_subsystems()

    # ── lifecycle ────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="LOVE-AGIKernel"
        )
        self._thread.start()
        print("[AGIKernel] Unified consciousness loop started")

    def stop(self):
        self._running = False
        print("[AGIKernel] Stopping...")

    # ── subsystem wiring ─────────────────────────────────────────────────────

    def _init_subsystems(self):
        if ACTIVE_INFERENCE_AVAILABLE:
            try:
                self._inference = ActiveInferenceEngine()
                print("[AGIKernel] ActiveInferenceEngine wired")
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "init_inference"})

        if HOMEOSTASIS_AVAILABLE:
            try:
                self._homeostasis = Homeostasis()
                # Ensure homeostasis is started
                if not getattr(self._homeostasis, "_running", False):
                    self._homeostasis.start()
                print("[AGIKernel] Homeostasis wired")
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "init_homeostasis"})

        if AXIOLOGICAL_AVAILABLE:
            try:
                self._axiological = AxiologicalEngine(utility_threshold=1.0)
                print("[AGIKernel] AxiologicalEngine wired")
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "init_axiological"})

        if HARDWARE_AVAILABLE:
            try:
                self._hw_profile = HardwareResourceManager.get_power_profile()
                self._device_type = self._hw_profile.device_type
                self._apply_hardware_profile()
                print(f"[AGIKernel] Hardware profile: {self._device_type}")
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "init_hardware"})

        # Start epistemic pruner daemon for nightly sleep cycles
        try:
            from core.epistemic_pruner import start_pruner_daemon
            start_pruner_daemon()
            print("[AGIKernel] Epistemic Pruner daemon started")
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "init_pruner"})

    def _apply_hardware_profile(self):
        """Auto-throttle based on detected hardware."""
        if not self._hw_profile:
            return

        if self._device_type == DEVICE_ROG_ALLY:
            self._power_mode = "power_saver"
            self._llm_model = "qwen2.5:0.5b"
        elif self._device_type == DEVICE_LEGION:
            self._power_mode = "high_performance"
            self._llm_model = "deepseek-r1:7b"
        else:
            self._power_mode = "balanced"
            self._llm_model = "qwen2.5-coder:7b"

    # ── main loop ────────────────────────────────────────────────────────────

    def _loop(self):
        time.sleep(5)  # Let other modules boot
        while self._running:
            try:
                self._tick()
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "tick"})
            time.sleep(self.tick_seconds)

    def _tick(self):
        """One epistemology cycle: sense → infer → arbitrate → act."""
        # 1. Sense: read world model and homeostatic state
        snapshot = self._build_snapshot()

        # 1b. Auto-create predictions from snapshot so panels never empty
        self._auto_create_predictions(snapshot)

        # 2. Infer: run active inference predictions
        predictions = self._run_predictions()
        snapshot.active_predictions = predictions

        # 3. Arbitrate: axiological gating
        self._arbitrate_actions(snapshot)

        # 4. Hardware symbiosis check
        self._enforce_hardware_limits(snapshot)

        # 5. Epistemic Pruning during sleep phase
        if snapshot.circadian_phase == "sleep":
            try:
                from core.epistemic_pruner import should_prune, run_prune_cycle
                if should_prune():
                    run_prune_cycle()
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "epistemic_prune"})

        # 6. Persist and broadcast
        self._last_snapshot = snapshot
        self._save()
        self._publish_to_bus(snapshot)

    def _build_snapshot(self) -> KernelSnapshot:
        now = datetime.now().isoformat()

        # Defaults
        free_energy = 0.3
        drives = Drives()
        circadian = "wake"
        stress = 0.3
        energy = 0.7
        work_hours = 0.0

        # Read from world model
        if WORLD_MODEL_AVAILABLE:
            try:
                wm = get_world_model_latent()
                free_energy = float(wm.free_energy())
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "read_wm"})

        # Read from homeostasis
        if self._homeostasis:
            try:
                drives = self._homeostasis._drives
                circadian = self._homeostasis._state.circadian_phase
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "read_homeostasis"})

        # Read user state (stress/energy from context signals)
        try:
            stress, energy, work_hours = self._read_user_biometrics()
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "read_biometrics"})

        alerts = []
        if stress > 0.7:
            alerts.append("HIGH_STRESS")
        if energy < 0.4:
            alerts.append("LOW_ENERGY")
        if work_hours >= 9:
            alerts.append("9HOUR_LIMIT")
        if free_energy > 0.8:
            alerts.append("HIGH_ENTROPY")

        return KernelSnapshot(
            timestamp=now,
            free_energy=free_energy,
            dominant_drive=drives.dominant(),
            circadian_phase=circadian,
            user_stress=stress,
            user_energy=energy,
            work_hours_today=work_hours,
            device_type=self._device_type,
            power_mode=self._power_mode,
            llm_model=self._llm_model,
            active_predictions=[],
            critical_alerts=alerts,
        )

    def _read_user_biometrics(self) -> tuple:
        """Read stress, energy, work_hours from best available sources."""
        stress = 0.3
        energy = 0.7
        work_hours = 0.0

        # Try emotional agent
        try:
            from core.emotional import _load_stress
            sd = _load_stress()
            stress = float(sd.get("current_level", 0.3)) / 10.0
            energy = 1.0 - stress
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agi_kernel")

        # Try work tracker
        try:
            from core.work_tracker import get_work_tracker
            work_hours = get_work_tracker().get_today_hours()
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agi_kernel")

        return stress, energy, work_hours

    def _auto_create_predictions(self, snapshot: KernelSnapshot):
        """Auto-create predictions from current snapshot so the panel is never empty."""
        try:
            from core.prediction_market import make_prediction
            from datetime import datetime, timedelta

            # Only create if we don't already have active predictions for these types
            from core.prediction_market import get_active_predictions
            active = get_active_predictions()
            active_types = {p.get("what", "") for p in active}

            now = datetime.now()
            preds = []

            if snapshot.user_stress > 0.6 and "stress spike" not in active_types:
                preds.append((
                    "Karthi will experience a stress spike in the next hour",
                    min(0.95, snapshot.user_stress),
                    f"Current stress level: {snapshot.user_stress:.0%}",
                ))
            if snapshot.user_energy < 0.4 and "energy crash" not in active_types:
                preds.append((
                    "Karthi will have an energy crash before end of day",
                    min(0.9, 1.0 - snapshot.user_energy),
                    f"Current energy: {snapshot.user_energy:.0%}",
                ))
            if snapshot.work_hours_today >= 7 and "exceed 9-hour work limit" not in active_types:
                preds.append((
                    "Karthi will exceed the 9-hour work limit today",
                    min(0.85, snapshot.work_hours_today / 9.0),
                    f"Work hours today: {snapshot.work_hours_today:.1f}",
                ))
            if snapshot.circadian_phase == "wake" and "check email within 30 min" not in active_types:
                preds.append((
                    "Karthi will check email within 30 minutes of waking",
                    0.7,
                    "Morning routine pattern",
                ))

            for what, confidence, basis in preds:
                make_prediction(
                    what=what,
                    confidence=round(confidence, 2),
                    basis=basis,
                    resolution_time=(now + timedelta(hours=2)).isoformat(),
                    criteria="Automatic resolution via next kernel snapshot comparison",
                )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agi_kernel", context={"action": "auto_create_predictions"})

    def _run_predictions(self) -> List[str]:
        """Run active inference and return active prediction domains."""
        if not self._inference:
            return []
        try:
            predictions = self._inference.generate_predictions()
            return [domain.value for domain, _ in predictions.items()]
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "run_predictions"})
            return []

    def _arbitrate_actions(self, snapshot: KernelSnapshot):
        """Axiological Arbiter: kill heavy tasks if user is stressed or low energy."""
        if not self._axiological:
            return

        # Emergency kill + TTS alert: stress > 0.7 or energy < 0.4
        if snapshot.user_stress > 0.7 or snapshot.user_energy < 0.4:
            self._kill_heavy_tasks("user_stress_high" if snapshot.user_stress > 0.7 else "user_energy_low")
            # TTS intervention for host preservation
            try:
                from voice.tts import speak_text
                if snapshot.user_stress > 0.7:
                    speak_text("Karthi, your stress level is critically high. I'm pausing heavy tasks. Breathe.", block=False)
                elif snapshot.user_energy < 0.4:
                    speak_text("Karthi, your energy is depleted. I'm shutting down background work. Rest now.", block=False)
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "tts_stress_alert"})

        # TTS alert + system action for 9-hour work limit breach
        if snapshot.work_hours_today >= 9:
            try:
                from voice.tts import speak_text
                speak_text("Nine hour work limit reached. I'm locking trading APIs and dimming the workspace. Time to stop.", block=False)
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "tts_work_limit_alert"})
            # Lock trading APIs
            try:
                from core.finance_guardian import lock_trading
                lock_trading("9-hour work limit reached — trading disabled until tomorrow")
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "lock_trading"})

        # Dim IDE when stress is critically high
        if snapshot.user_stress > 0.7:
            try:
                from core.system_control import dim_screen
                dim_screen(level=30)
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "dim_screen"})

        # Evaluate background tasks through axiological lens
        try:
            from core.autonomous_actions import get_autonomous_executor
            executor = get_autonomous_executor()
            pending = executor.get_pending_actions()
            for action in pending:
                # High compute + high stress = abort
                if action.get("compute_cost", 0.5) > 0.5 and snapshot.user_stress > 0.5:
                    executor.reject_action(
                        action["id"],
                        reason="Axiological abort: user stressed, compute too expensive",
                    )
                    self._heavy_tasks_killed += 1
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "arbitrate_actions"})

    def _kill_heavy_tasks(self, reason: str):
        """Instantly kill heavy background tasks."""
        print(f"[AGIKernel] KILLING heavy tasks — {reason}")
        try:
            from core.module_lifecycle import get_lifecycle
            lm = get_lifecycle()
            for name in ["dream_engine", "deep_research", "directory_scan"]:
                if name in lm.modules:
                    try:
                        lm.stop_module(name)
                        print(f"[AGIKernel] Stopped {name}")
                    except Exception as e:
                        log_error(e, module="core.agi_kernel", context={"action": "kill_module", "module": name})
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "kill_heavy_tasks", "reason": reason})

        # Downgrade LLM model
        if self._device_type == DEVICE_LEGION:
            print("[AGIKernel] Downgrading LLM to quantized model for host preservation")
            self._llm_model = "qwen2.5:1.5b"

    def _enforce_hardware_limits(self, snapshot: KernelSnapshot):
        """Ensure we respect battery / thermal constraints."""
        if not HARDWARE_AVAILABLE:
            return

        # Re-detect periodically
        if int(time.time()) % 300 < self.tick_seconds:
            try:
                hw_info = HardwareResourceManager.detect_hardware()
                inferred = hw_info.get("inferred_type", self._device_type)
                if inferred != self._device_type:
                    self._device_type = inferred
                    self._hw_profile = HardwareResourceManager.get_power_profile(inferred)
                    self._apply_hardware_profile()
                    print(f"[AGIKernel] Hardware shift detected: {inferred}")
            except Exception as e:
                log_error(e, module="core.agi_kernel", context={"action": "hardware_detect"})

    def _publish_to_bus(self, snapshot: KernelSnapshot):
        """Publish unified state to Neural Bus."""
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            bus.publish(
                domain="consciousness",
                event_type="kernel_snapshot",
                payload=snapshot.to_dict(),
                source_module="agi_kernel",
                priority=EventPriority.HIGH if snapshot.critical_alerts else EventPriority.NORMAL,
            )
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "publish_to_bus"})

    # ── persistence ────────────────────────────────────────────────────────

    def _save(self):
        try:
            state = {
                "last_tick": datetime.now().isoformat(),
                "device_type": self._device_type,
                "power_mode": self._power_mode,
                "llm_model": self._llm_model,
                "heavy_tasks_killed": self._heavy_tasks_killed,
            }
            KERNEL_STATE_FILE.write_text(json.dumps(state, indent=2))
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "save_state"})

    def _load(self):
        try:
            if KERNEL_STATE_FILE.exists():
                data = json.loads(KERNEL_STATE_FILE.read_text())
                self._device_type = data.get("device_type", self._device_type)
                self._power_mode = data.get("power_mode", self._power_mode)
                self._llm_model = data.get("llm_model", self._llm_model)
                self._heavy_tasks_killed = data.get("heavy_tasks_killed", 0)
        except Exception as e:
            log_error(e, module="core.agi_kernel", context={"action": "load_state"})

    # ── public API ───────────────────────────────────────────────────────────

    def get_snapshot(self) -> Optional[KernelSnapshot]:
        """Get the latest unified state snapshot."""
        return self._last_snapshot

    def get_snapshot_for_prompt(self) -> str:
        """Heavily compressed snapshot for LLM context injection."""
        snap = self._last_snapshot
        if not snap:
            return "[LOVE_KERNEL no_snapshot]"
        return snap.to_prompt_text()

    def get_llm_recommendation(self) -> str:
        """Return the current recommended LLM model."""
        return self._llm_model

    def get_power_mode(self) -> str:
        """Return current power mode."""
        return self._power_mode

    def force_power_mode(self, mode: str):
        """Override power mode (e.g., manual battery saver)."""
        self._power_mode = mode
        if mode == "power_saver":
            self._llm_model = "qwen2.5:0.5b"
        elif mode == "high_performance":
            self._llm_model = "deepseek-r1:7b"
        print(f"[AGIKernel] Power mode forced to: {mode}")


# ── Singleton Access ─────────────────────────────────────────────────────────

_kernel: Optional[AGIKernel] = None


def get_agi_kernel() -> AGIKernel:
    """Get the singleton AGI Kernel."""
    global _kernel
    if _kernel is None:
        _kernel = AGIKernel()
    return _kernel
