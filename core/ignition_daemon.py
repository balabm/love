"""
LOVE Ignition Daemon — thin wrapper that drives GWT ignition on a background clock.

Calls GlobalWorkspace.ignite(substrate_snapshot()) every 30 seconds.
All ignition logic (thresholds, rate-limiting, MoE routing) lives in
global_workspace.py — this file is purely the scheduling harness.

Usage
-----
    from core.ignition_daemon import start_ignition_daemon, get_ignition_daemon
    start_ignition_daemon()   # safe to call multiple times (idempotent)

    # Later inspection:
    daemon = get_ignition_daemon()
    print(daemon.status())    # {"running": True, "tick_count": 42, ...}
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional


_TICK_INTERVAL = 30   # seconds between ignition checks


class IgnitionDaemon:
    """
    Runs a daemon thread that periodically calls gw.ignite(substrate_snapshot()).
    Non-blocking. Errors inside the tick are swallowed so the daemon never dies.
    """

    def __init__(self):
        self._running  = False
        self._thread: Optional[threading.Thread] = None
        self._tick_count = 0
        self._last_tick: float = 0.0
        self._last_event: Optional[Dict[str, Any]] = None
        self._mu = threading.Lock()

    # ── public API ────────────────────────────────────────────────────────────

    def start(self, interval: float = _TICK_INTERVAL) -> None:
        """Start the daemon thread. Idempotent — safe to call multiple times."""
        with self._mu:
            if self._running:
                return
            self._running = True

        self._thread = threading.Thread(
            target=self._loop,
            args=(interval,),
            daemon=True,
            name="love-ignition-daemon",
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the daemon to stop. Thread will exit at the next tick boundary."""
        with self._mu:
            self._running = False

    def status(self) -> Dict[str, Any]:
        """Return a compact health dict."""
        with self._mu:
            return {
                "running":    self._running,
                "tick_count": self._tick_count,
                "last_tick":  self._last_tick,
                "last_event": self._last_event,
            }

    # ── internal ──────────────────────────────────────────────────────────────

    def _loop(self, interval: float) -> None:
        """Main daemon loop. Runs until stop() is called."""
        while True:
            with self._mu:
                if not self._running:
                    break

            self._tick()

            # Sleep in small slices so stop() is responsive
            deadline = time.time() + interval
            while time.time() < deadline:
                with self._mu:
                    if not self._running:
                        return
                time.sleep(1)

    def _tick(self) -> None:
        """Single ignition check — all errors are swallowed."""
        try:
            from core.global_workspace import get_global_workspace
            from core.living_substrate import substrate_snapshot

            gw   = get_global_workspace()
            snap = substrate_snapshot()
            ev   = gw.ignite(snap)

            with self._mu:
                self._tick_count += 1
                self._last_tick = time.time()
                if ev is not None:
                    from dataclasses import asdict
                    self._last_event = asdict(ev)

        except Exception:
            # Daemon must never crash — swallow everything
            with self._mu:
                self._tick_count += 1
                self._last_tick = time.time()


# ── module-level singleton ────────────────────────────────────────────────────

_daemon_instance: Optional[IgnitionDaemon] = None
_daemon_lock = threading.Lock()


def get_ignition_daemon() -> IgnitionDaemon:
    """Return (creating if necessary) the module-level IgnitionDaemon singleton."""
    global _daemon_instance
    if _daemon_instance is None:
        with _daemon_lock:
            if _daemon_instance is None:
                _daemon_instance = IgnitionDaemon()
    return _daemon_instance


def start_ignition_daemon(interval: float = _TICK_INTERVAL) -> IgnitionDaemon:
    """
    Convenience function: get the singleton daemon and start it if not running.
    Returns the daemon so callers can inspect status().
    """
    daemon = get_ignition_daemon()
    daemon.start(interval=interval)
    return daemon
