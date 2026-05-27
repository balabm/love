"""
resource_governor.py  --  Host-resource watchdog for Project LOVE.

Monitors CPU, RAM, and GPU VRAM so LOVE can back off gracefully when the
host machine is under pressure.  Also detects heavyweight creative apps
(Unity, Blender, UE5, etc.) and treats their presence as load.

Usage:
    from core.resource_governor import get_resource_governor, yield_to_host

    gov = get_resource_governor()
    gov.start()

    @yield_to_host
    def expensive_work():
        ...
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import psutil

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("love.resource_governor")

# ---------------------------------------------------------------------------
# Global load flag  --  any thread / coroutine can check this cheaply.
# ---------------------------------------------------------------------------
SYSTEM_UNDER_LOAD: threading.Event = threading.Event()

# ---------------------------------------------------------------------------
# Heavy-process list (creative / dev tools that eat resources)
# ---------------------------------------------------------------------------
HEAVY_PROCESSES: list[str] = [
    "Unity.exe",
    "devenv.exe",
    "Blender.exe",
    "UE5Editor.exe",
    "godot.exe",
    "maya.exe",
    "3dsmax.exe",
]

# ---------------------------------------------------------------------------
# Data-log path  (relative to the repo root `love/`)
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_RESOURCE_LOG = _DATA_DIR / "resource_log.jsonl"


# ===================================================================== #
#  ResourceGovernor
# ===================================================================== #
class ResourceGovernor:
    """Daemon that samples host metrics and flips SYSTEM_UNDER_LOAD."""

    def __init__(
        self,
        cpu_threshold: float = 75.0,
        ram_threshold: float = 85.0,
        vram_threshold: float = 90.0,
        poll_interval: int = 5,
    ) -> None:
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold
        self.vram_threshold = vram_threshold
        self.poll_interval = poll_interval

        # Hysteresis: metrics must drop this many points *below* threshold
        # before we clear the flag  (threshold - hysteresis_margin).
        self._hysteresis_margin: float = 10.0

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._snapshot: Dict[str, Any] = {}
        self._last_log_time: float = 0.0
        self._log_interval: float = 60.0  # write to disk at most once / min
        
        # Load state change callbacks (Gap Analysis fix: connect to idle-mind)
        self._load_callbacks: list[Callable[[bool], None]] = []
        self._previous_load_state: bool = False

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    
    def register_load_callback(self, callback: Callable[[bool], None]) -> None:
        """Register a callback to be called when load state changes.
        
        Args:
            callback: Function that takes a boolean (True = entering load, False = exiting load)
        """
        if callback not in self._load_callbacks:
            self._load_callbacks.append(callback)
    
    def _notify_load_change(self, under_load: bool) -> None:
        """Notify registered callbacks of load state change."""
        if under_load != self._previous_load_state:
            for callback in self._load_callbacks:
                try:
                    callback(under_load)
                except Exception:
                    logger.exception("Load callback failed")
            self._previous_load_state = under_load
    def start(self) -> None:
        """Launch the monitor in a daemon thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self.monitor_host_health,
            name="love-resource-governor",
            daemon=True,
        )
        self._thread.start()
        logger.info("ResourceGovernor started  (poll every %ss)", self.poll_interval)

    def stop(self) -> None:
        """Signal the monitor loop to exit."""
        self._running = False
        logger.info("ResourceGovernor stopping.")

    def get_snapshot(self) -> Dict[str, Any]:
        """Return the latest metrics dict (thread-safe read)."""
        return dict(self._snapshot)

    @staticmethod
    def is_under_load() -> bool:
        """Quick check — is the host currently overloaded?"""
        return SYSTEM_UNDER_LOAD.is_set()

    # ------------------------------------------------------------------ #
    #  Background loop
    # ------------------------------------------------------------------ #
    def monitor_host_health(self) -> None:
        """Continuously sample CPU / RAM / VRAM and manage the load flag."""
        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                vram_pct = self._sample_vram()
                heavy_apps = self._detect_heavy_processes()

                snapshot: Dict[str, Any] = {
                    "ts": time.time(),
                    "cpu_pct": cpu,
                    "ram_pct": ram,
                    "vram_pct": vram_pct,
                    "heavy_apps": heavy_apps,
                    "under_load": False,
                }

                # --- decide load state -------------------------------- #
                reasons: list[str] = []
                if cpu > self.cpu_threshold:
                    reasons.append(f"CPU {cpu:.1f}% > {self.cpu_threshold}%")
                if ram > self.ram_threshold:
                    reasons.append(f"RAM {ram:.1f}% > {self.ram_threshold}%")
                if vram_pct > self.vram_threshold:
                    reasons.append(f"VRAM {vram_pct:.1f}% > {self.vram_threshold}%")
                if heavy_apps:
                    reasons.append(f"Heavy apps running: {', '.join(heavy_apps)}")

                if reasons:
                    if not SYSTEM_UNDER_LOAD.is_set():
                        logger.warning(
                            "SYSTEM_UNDER_LOAD set  --  %s", "; ".join(reasons)
                        )
                    SYSTEM_UNDER_LOAD.set()
                    snapshot["under_load"] = True
                    self._notify_load_change(True)
                else:
                    # Hysteresis: only *clear* when all metrics are well below
                    cpu_ok = cpu < (self.cpu_threshold - self._hysteresis_margin)
                    ram_ok = ram < (self.ram_threshold - self._hysteresis_margin)
                    vram_ok = vram_pct < (self.vram_threshold - self._hysteresis_margin)
                    no_heavy = len(heavy_apps) == 0

                    if cpu_ok and ram_ok and vram_ok and no_heavy:
                        if SYSTEM_UNDER_LOAD.is_set():
                            logger.info(
                                "SYSTEM_UNDER_LOAD cleared  --  all metrics recovered."
                            )
                        SYSTEM_UNDER_LOAD.clear()
                        snapshot["under_load"] = False
                        self._notify_load_change(False)

                self._snapshot = snapshot
                self._maybe_log_to_disk(snapshot)

            except Exception:
                logger.exception("ResourceGovernor tick failed")

            # Sleep in small increments so stop() is responsive.
            deadline = time.monotonic() + self.poll_interval
            while self._running and time.monotonic() < deadline:
                time.sleep(0.5)

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _sample_vram() -> float:
        """Query nvidia-smi for VRAM usage.  Returns 0 if unavailable."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode != 0:
                return 0.0
            # nvidia-smi may report multiple GPUs — take the worst case.
            worst: float = 0.0
            for line in result.stdout.strip().splitlines():
                parts = line.split(",")
                if len(parts) == 2:
                    used = float(parts[0].strip())
                    total = float(parts[1].strip())
                    if total > 0:
                        worst = max(worst, (used / total) * 100.0)
            return worst
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return 0.0

    @staticmethod
    def _detect_heavy_processes() -> list[str]:
        """Return names of known resource-heavy apps currently running."""
        heavy_lower = {name.lower() for name in HEAVY_PROCESSES}
        found: list[str] = []
        try:
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"]
                    if name and name.lower() in heavy_lower:
                        if name not in found:
                            found.append(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return found

    def _maybe_log_to_disk(self, snapshot: Dict[str, Any]) -> None:
        """Append snapshot to JSONL, at most once per minute."""
        now = time.time()
        if now - self._last_log_time < self._log_interval:
            return
        self._last_log_time = now
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(_RESOURCE_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(snapshot, default=str) + "\n")
        except Exception:
            logger.exception("Failed to write resource log")


# ===================================================================== #
#  @yield_to_host decorator
# ===================================================================== #
def yield_to_host(fn: Callable) -> Callable:
    """Skip *fn* entirely when the host is overloaded.

    - Sync functions: return ``None`` immediately.
    - Async functions: ``await asyncio.sleep(0)`` then return ``None``.
    """
    if asyncio.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
            if SYSTEM_UNDER_LOAD.is_set():
                logger.warning(
                    "yield_to_host: skipping async %s — system under load",
                    fn.__qualname__,
                )
                await asyncio.sleep(0)
                return None
            return await fn(*args, **kwargs)

        return _async_wrapper
    else:

        @functools.wraps(fn)
        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if SYSTEM_UNDER_LOAD.is_set():
                logger.warning(
                    "yield_to_host: skipping %s — system under load",
                    fn.__qualname__,
                )
                return None
            return fn(*args, **kwargs)

        return _sync_wrapper


# ===================================================================== #
#  Singleton accessor
# ===================================================================== #
_governor: Optional[ResourceGovernor] = None


def get_resource_governor(**kwargs: Any) -> ResourceGovernor:
    """Return (and lazily create) the singleton ResourceGovernor."""
    global _governor
    if _governor is None:
        _governor = ResourceGovernor(**kwargs)
    return _governor
