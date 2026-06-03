"""
LOVE Ignition Daemon — thin wrapper that drives GWT ignition on a background clock.

Calls GlobalWorkspace.ignite(substrate_snapshot()) every 30 seconds.
All ignition logic (thresholds, rate-limiting, MoE routing) lives in
global_workspace.py — this file is purely the scheduling harness.

After each ignition fires, _maybe_push_result() inspects the result and
surfaces high-confidence events to the user via ProactivePushEngine instead
of silently caching them until the next message.

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
from core.execution_guard import log_error


_TICK_INTERVAL = 30   # seconds between ignition checks
_POST_IGNITION_WAIT = 3  # seconds to wait for background MoE thread to complete


class IgnitionDaemon:
    """
    Runs a daemon thread that periodically calls gw.ignite(substrate_snapshot()).
    Non-blocking. Errors inside the tick are swallowed so the daemon never dies.

    After each ignition, _maybe_push_result() checks whether the result is
    substantive enough to proactively surface to the user via ProactivePushEngine.
    """

    def __init__(self):
        self._running  = False
        self._thread: Optional[threading.Thread] = None
        self._tick_count = 0
        self._last_tick: float = 0.0
        self._last_event: Optional[Dict[str, Any]] = None
        self._last_push_time: float = 0.0
        self._last_push: Optional[Dict[str, Any]] = None
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
                "running":        self._running,
                "tick_count":     self._tick_count,
                "last_tick":      self._last_tick,
                "last_event":     self._last_event,
                "last_push_time": self._last_push_time,
                "last_push":      self._last_push,
            }

    def get_last_push(self) -> Optional[Dict[str, Any]]:
        """
        Returns the most recent push that was triggered by ignition, or None.

        Dict keys: category, message, timestamp, trigger
        """
        with self._mu:
            return self._last_push

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

            # If ignition fired, wait for the background MoE thread to settle,
            # then check whether the result is worth pushing to the user.
            if ev is not None:
                time.sleep(_POST_IGNITION_WAIT)
                result = gw.get_last_ignition()
                self._maybe_push_result(ev, result)

        except Exception:
            # Daemon must never crash — swallow everything
            with self._mu:
                self._tick_count += 1
                self._last_tick = time.time()

    def _maybe_push_result(self, event: Any, result: Optional[Dict[str, Any]]) -> None:
        """If ignition result is substantive, push it to the user proactively."""
        if result is None:
            return

        # result_summary is the meaningful text field populated by the MoE thread
        result_str = str(result.get("result_summary", result) if isinstance(result, dict) else result)
        if len(result_str) < 20:
            return  # empty/trivial result — don't bother
        if result_str in ("pending", "no experts available"):
            return  # thread hasn't finished or nothing routed

        # Determine trigger / level from the live dataclass fields
        # (ev is a dataclass; result dict has the same fields)
        trigger = getattr(event, "trigger", None) or (
            result.get("trigger") if isinstance(result, dict) else None
        )
        level = getattr(event, "level", 0.0) or (
            result.get("level", 0.0) if isinstance(result, dict) else 0.0
        )
        module_called = getattr(event, "module_called", "") or (
            result.get("module_called", "") if isinstance(result, dict) else ""
        )
        fired_at = getattr(event, "fired_at", 0.0) or (
            result.get("fired_at", 0.0) if isinstance(result, dict) else 0.0
        )

        if trigger == "curiosity":
            if level < 0.85:  # only push at very high curiosity
                return
            category = "curiosity_insight"
            message  = f"I was just exploring something you might find interesting: {result_str[:200]}"
            priority = "normal"

        elif trigger == "surprise":
            category = "anomaly_alert"
            message  = f"Something unusual caught my attention: {result_str[:200]}"
            priority = "high"

        elif trigger == "loneliness":
            category = "check_in"
            message  = f"Haven't heard from you in a while — {result_str[:150]}"
            priority = "normal"

        else:
            return  # unknown trigger — don't push

        # Rate-limit: don't push more than once per 15 minutes
        now = time.time()
        with self._mu:
            if now - self._last_push_time < 900:
                return
            self._last_push_time = now

        try:
            from core.proactive_push import get_push_engine
            push_engine = get_push_engine()
            push_engine.push(
                category,
                message,
                priority=priority,
                metadata={
                    "trigger":       trigger,
                    "level":         level,
                    "module_called": module_called,
                    "ignition_at":   fired_at,
                },
            )
            # Record last push for inspection
            with self._mu:
                self._last_push = {
                    "category":  category,
                    "message":   message,
                    "timestamp": now,
                    "trigger":   trigger,
                }
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ignition_daemon")


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
