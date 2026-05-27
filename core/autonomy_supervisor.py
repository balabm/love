"""
LOVE Autonomy Supervisor

Single control-loop that keeps core autonomous systems alive and self-healing:
- Proactive heartbeat
- Self-improvement daemon
- Autonomous goal engine
- Wave engine
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List


class AutonomySupervisor:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_tick_at: str | None = None
        self._last_actions: List[Dict[str, Any]] = []
        self._ticks = 0
        self._restart_history: Dict[str, List[float]] = {}
        self._cooldowns: Dict[str, float] = {}

    def start(self, interval_seconds: int = 300) -> Dict[str, Any]:
        with self._lock:
            if self._running:
                return {"status": "already_running", "interval_seconds": interval_seconds}

            interval_seconds = max(30, int(interval_seconds))
            self._running = True
            self._thread = threading.Thread(
                target=self._loop,
                args=(interval_seconds,),
                daemon=True,
                name="LOVE-AutonomySupervisor",
            )
            self._thread.start()
            return {"status": "started", "interval_seconds": interval_seconds}

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            self._running = False
        return {"status": "stopped"}

    def run_tick(self) -> Dict[str, Any]:
        from core.autonomy_policy import load_policy

        policy = load_policy()
        actions: List[Dict[str, Any]] = []

        # 1) Heartbeat
        try:
            from core.heartbeat import get_heartbeat, start_heartbeat

            hb = get_heartbeat()
            if policy["components"].get("heartbeat", True) and not hb.running:
                if self._can_restart("heartbeat", policy, actions):
                    start_heartbeat()
                    self._record_restart("heartbeat")
                    actions.append({"component": "heartbeat", "action": "restarted"})
            elif not policy["components"].get("heartbeat", True):
                actions.append({"component": "heartbeat", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "heartbeat", "action": "error", "error": str(e)})

        # 2) Self-improvement daemon
        try:
            from core.self_improvement_daemon import get_improvement_daemon

            daemon = get_improvement_daemon()
            if policy["components"].get("self_improvement_daemon", True) and not daemon.get_status().get("running"):
                if self._can_restart("self_improvement_daemon", policy, actions):
                    daemon.start(interval_minutes=int(os.getenv("LOVE_DAEMON_INTERVAL_MIN", "30")))
                    self._record_restart("self_improvement_daemon")
                    actions.append({"component": "self_improvement_daemon", "action": "restarted"})
            elif not policy["components"].get("self_improvement_daemon", True):
                actions.append({"component": "self_improvement_daemon", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "self_improvement_daemon", "action": "error", "error": str(e)})

        # 3) Autonomous goal engine
        try:
            from core.autonomous_goal_engine import is_goal_engine_running, start_goal_engine

            if policy["components"].get("autonomous_goal_engine", True) and not is_goal_engine_running():
                if self._can_restart("autonomous_goal_engine", policy, actions):
                    start_goal_engine(interval_seconds=int(os.getenv("LOVE_GOAL_INTERVAL_SEC", "7200")))
                    self._record_restart("autonomous_goal_engine")
                    actions.append({"component": "autonomous_goal_engine", "action": "restarted"})
            elif not policy["components"].get("autonomous_goal_engine", True):
                actions.append({"component": "autonomous_goal_engine", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "autonomous_goal_engine", "action": "error", "error": str(e)})

        # 4) Wave engine
        try:
            from core.wave_engine import get_wave_engine

            wave = get_wave_engine()
            status = wave.get_status() if hasattr(wave, "get_status") else {}
            if policy["components"].get("wave_engine", True) and not status.get("running"):
                if self._can_restart("wave_engine", policy, actions):
                    wave.start_daemon(interval_hours=int(os.getenv("LOVE_WAVE_INTERVAL_H", "24")))
                    self._record_restart("wave_engine")
                    actions.append({"component": "wave_engine", "action": "restarted"})
            elif not policy["components"].get("wave_engine", True):
                actions.append({"component": "wave_engine", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "wave_engine", "action": "error", "error": str(e)})

        # 5) Optional immediate self-work pulse (policy + mode gated)
        mode = policy.get("mode", "balanced")
        diagnostics_enabled = (
            policy["components"].get("self_diagnostics", True)
            and mode in {"balanced", "aggressive"}
            and os.getenv("LOVE_SELF_WORK_ON_TICK", "true").lower() in ("1", "true", "yes")
        )
        if diagnostics_enabled:
            try:
                from core.self_improvement_daemon import get_improvement_daemon

                report = get_improvement_daemon().run_diagnostics()
                actions.append(
                    {
                        "component": "self_diagnostics",
                        "action": "executed",
                        "health_score": report.health_score,
                        "issues": len(report.issues),
                    }
                )
            except Exception as e:
                actions.append({"component": "self_diagnostics", "action": "error", "error": str(e)})
        elif not policy["components"].get("self_diagnostics", True):
            actions.append({"component": "self_diagnostics", "action": "disabled_by_policy"})
        elif mode == "safe":
            actions.append({"component": "self_diagnostics", "action": "disabled_in_safe_mode"})

        # 6) Mission queue: convert capability goals into continuous build attempts
        if policy["components"].get("mission_queue", True):
            try:
                from core.autonomous_mission_queue import get_mission_queue

                mission_result = get_mission_queue().run_cycle()
                if mission_result.get("actions"):
                    actions.append(
                        {
                            "component": "mission_queue",
                            "action": "cycle",
                            "details": mission_result["actions"][:3],
                        }
                    )
            except Exception as e:
                actions.append({"component": "mission_queue", "action": "error", "error": str(e)})
        else:
            actions.append({"component": "mission_queue", "action": "disabled_by_policy"})

        self._last_tick_at = datetime.now().isoformat()
        self._last_actions = actions[-25:]
        self._ticks += 1
        return {
            "tick": self._ticks,
            "timestamp": self._last_tick_at,
            "policy_mode": mode,
            "actions": self._last_actions,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "ticks": self._ticks,
            "last_tick_at": self._last_tick_at,
            "last_actions": self._last_actions,
            "cooldowns": {k: int(v - time.time()) for k, v in self._cooldowns.items() if v > time.time()},
        }

    def _can_restart(self, component: str, policy: Dict[str, Any], actions: List[Dict[str, Any]]) -> bool:
        now = time.time()
        cooldown_until = self._cooldowns.get(component, 0.0)
        if cooldown_until > now:
            actions.append(
                {
                    "component": component,
                    "action": "restart_blocked_cooldown",
                    "retry_in_sec": int(cooldown_until - now),
                }
            )
            return False

        flap = policy.get("flap_protection", {})
        window_sec = int(flap.get("window_sec", 900))
        max_restarts = int(flap.get("max_restarts", 3))
        cooldown_sec = int(flap.get("cooldown_sec", 1800))

        history = [t for t in self._restart_history.get(component, []) if now - t <= window_sec]
        self._restart_history[component] = history
        if len(history) >= max_restarts:
            self._cooldowns[component] = now + cooldown_sec
            actions.append(
                {
                    "component": component,
                    "action": "restart_disabled_flap_protection",
                    "cooldown_sec": cooldown_sec,
                }
            )
            return False
        return True

    def _record_restart(self, component: str) -> None:
        self._restart_history.setdefault(component, []).append(time.time())

    def _loop(self, interval_seconds: int) -> None:
        print(f"[AutonomySupervisor] Started (every {interval_seconds}s)")
        while self._running:
            try:
                self.run_tick()
            except Exception as e:
                print(f"[AutonomySupervisor] Tick error: {e}")
            for _ in range(interval_seconds):
                if not self._running:
                    break
                time.sleep(1)
        print("[AutonomySupervisor] Stopped")


_supervisor: AutonomySupervisor | None = None
_supervisor_lock = threading.Lock()


def get_autonomy_supervisor() -> AutonomySupervisor:
    global _supervisor
    if _supervisor is None:
        with _supervisor_lock:
            if _supervisor is None:
                _supervisor = AutonomySupervisor()
    return _supervisor

