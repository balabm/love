"""
LOVE Autonomy Supervisor

Unified control-loop that monitors ALL lifecycle modules (57 total) and keeps
them alive with auto-restart, flap protection, and health telemetry.

 watches:
- Every module registered in module_lifecycle (waves 0-6)
- Special autonomous subsystems (heartbeat, daemon, goal engine, wave engine)
- Mission queue and self-diagnostics

Provides:
- /agi/autonomy-supervisor/status   -> full fleet health
- /agi/autonomy-supervisor/tick     -> manual supervision pulse
- /agi/modules/restart              -> per-module restart
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


# Modules the supervisor will auto-restart if failed/degraded (optional only)
_AUTO_HEAL_MODULES: Set[str] = {
    "heartbeat",
    "self_improvement_daemon",
    "autonomous_goal_engine",
    "wave_engine",
    "mission_queue",
    "tunnel_agent",
    "device_bridge",
    "notification_ingestion",
    "finance_guardian",
    "autonomous_trading",
    "master_orchestrator",
    "ghost_dev",
    "research_engine",
    "proactive_push",
    "daily_briefing",
    "idle_mind",
    "homeostasis",
    "life_nudge_scheduler",
    "terminal_monitor",
    "sentinel",
}


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
        self._module_health: Dict[str, Dict[str, Any]] = {}
        self._interval_seconds = 300
        self._last_intelligence_at: float = 0.0

    def start(self, interval_seconds: int = 300) -> Dict[str, Any]:
        with self._lock:
            if self._running:
                return {"status": "already_running", "interval_seconds": self._interval_seconds}

            self._interval_seconds = max(60, int(interval_seconds))
            self._running = True
            self._thread = threading.Thread(
                target=self._loop,
                daemon=True,
                name="LOVE-AutonomySupervisor",
            )
            self._thread.start()
            return {"status": "started", "interval_seconds": self._interval_seconds}

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            self._running = False
        return {"status": "stopped"}

    def run_tick(self) -> Dict[str, Any]:
        from core.autonomy_policy import load_policy

        policy = load_policy()
        actions: List[Dict[str, Any]] = []
        mode = policy.get("mode", "balanced")

        # ── PHASE 1: Special autonomous subsystems (direct restart) ──
        actions.extend(self._tick_special_systems(policy, mode))

        # ── PHASE 2: Full lifecycle module health scan ──
        actions.extend(self._tick_lifecycle_modules(policy, mode))

        # ── PHASE 3: Self-diagnostics (policy + mode gated) ──
        actions.extend(self._tick_self_diagnostics(policy, mode))

        # ── PHASE 4: Mission queue ──
        actions.extend(self._tick_mission_queue(policy))

        # ── PHASE 5: INTELLIGENCE & ACTION (AGI loop) ──
        # This is where LOVE thinks, plans, and acts — not just monitors.
        actions.extend(self._tick_intelligence(policy, mode))

        self._last_tick_at = datetime.now().isoformat()
        self._last_actions = actions[-50:]
        self._ticks += 1

        return {
            "tick": self._ticks,
            "timestamp": self._last_tick_at,
            "policy_mode": mode,
            "actions": self._last_actions,
            "modules_monitored": len(self._module_health),
            "modules_healed": sum(1 for a in actions if a.get("action") == "restarted"),
        }

    def _tick_special_systems(self, policy: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
        """Tick the special autonomous subsystems that need direct restart."""
        from core.activity_log import log_activity
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
                    log_activity("heartbeat", "restarted", "Heartbeat daemon restarted by supervisor", importance="normal")
            elif not policy["components"].get("heartbeat", True):
                actions.append({"component": "heartbeat", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "heartbeat", "action": "error", "error": str(e)})

        # 2) Self-improvement daemon
        try:
            from core.self_improvement_daemon import get_improvement_daemon
            daemon = get_improvement_daemon()
            running = daemon.get_status().get("running") if hasattr(daemon, "get_status") else False
            if policy["components"].get("self_improvement_daemon", True) and not running:
                if self._can_restart("self_improvement_daemon", policy, actions):
                    daemon.start(interval_minutes=int(os.getenv("LOVE_DAEMON_INTERVAL_MIN", "10")))
                    self._record_restart("self_improvement_daemon")
                    actions.append({"component": "self_improvement_daemon", "action": "restarted"})
                    log_activity("self_improvement_daemon", "restarted", "Self-improvement daemon restarted by supervisor", importance="normal")
            elif not policy["components"].get("self_improvement_daemon", True):
                actions.append({"component": "self_improvement_daemon", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "self_improvement_daemon", "action": "error", "error": str(e)})

        # 3) Autonomous goal engine
        try:
            from core.autonomous_goal_engine import is_goal_engine_running, start_goal_engine
            if policy["components"].get("autonomous_goal_engine", True) and not is_goal_engine_running():
                if self._can_restart("autonomous_goal_engine", policy, actions):
                    start_goal_engine(interval_seconds=int(os.getenv("LOVE_GOAL_INTERVAL_SEC", "600")))
                    self._record_restart("autonomous_goal_engine")
                    actions.append({"component": "autonomous_goal_engine", "action": "restarted"})
                    log_activity("autonomous_goal_engine", "restarted", "Goal engine restarted by supervisor", importance="normal")
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
                    wave.start_daemon(interval_hours=int(os.getenv("LOVE_WAVE_INTERVAL_H", "4")))
                    self._record_restart("wave_engine")
                    actions.append({"component": "wave_engine", "action": "restarted"})
                    log_activity("wave_engine", "restarted", "Wave engine restarted by supervisor", importance="normal")
            elif not policy["components"].get("wave_engine", True):
                actions.append({"component": "wave_engine", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "wave_engine", "action": "error", "error": str(e)})

        # 5) Ghost Developer
        try:
            from core.ghost_dev import get_ghost_dev
            gd = get_ghost_dev()
            if policy["components"].get("ghost_dev", True):
                gd.start()
                actions.append({"component": "ghost_dev", "action": "started"})
                log_activity("ghost_dev", "started", "Ghost Developer daemon started by supervisor", importance="normal")
            else:
                actions.append({"component": "ghost_dev", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "ghost_dev", "action": "error", "error": str(e)})

        # 6) Research Engine
        try:
            from core.research_engine import get_research_engine
            re = get_research_engine()
            if policy["components"].get("research_engine", True) and not re._running:
                re.start_background(interval_minutes=int(os.getenv("LOVE_RESEARCH_INTERVAL_MIN", "10")))
                actions.append({"component": "research_engine", "action": "started"})
                log_activity("research_engine", "started", "Research engine started by supervisor", importance="normal")
            elif not policy["components"].get("research_engine", True):
                actions.append({"component": "research_engine", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "research_engine", "action": "error", "error": str(e)})

        # 7) Proactive Push Engine
        try:
            from core.proactive_push import get_push_engine
            pe = get_push_engine()
            if policy["components"].get("proactive_push", True) and not pe._running:
                pe.start()
                actions.append({"component": "proactive_push", "action": "started"})
                log_activity("proactive_push", "started", "Proactive push engine started by supervisor", importance="normal")
            elif not policy["components"].get("proactive_push", True):
                actions.append({"component": "proactive_push", "action": "disabled_by_policy"})
        except Exception as e:
            actions.append({"component": "proactive_push", "action": "error", "error": str(e)})

        return actions

    def _tick_lifecycle_modules(self, policy: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
        """Scan all lifecycle modules and auto-heal failed/degraded optional ones."""
        from core.activity_log import log_activity
        actions: List[Dict[str, Any]] = []
        try:
            from core.module_lifecycle import get_lifecycle, ModuleState
            lm = get_lifecycle()
            modules = lm.modules
            now = time.time()

            for name, mod in modules.items():
                # Record health snapshot
                self._module_health[name] = {
                    "wave": mod.wave,
                    "state": mod.state.value,
                    "optional": mod.optional,
                    "error": mod.error,
                    "elapsed_ms": mod.elapsed_ms,
                    "checked_at": datetime.now().isoformat(),
                }

                # Skip if not in auto-heal list
                if name not in _AUTO_HEAL_MODULES:
                    continue

                # Skip if disabled by policy
                if not policy["components"].get(name, True):
                    actions.append({"component": name, "action": "disabled_by_policy"})
                    continue

                # Only heal optional modules that are failed or degraded
                if mod.optional and mod.state in (ModuleState.FAILED, ModuleState.DEGRADED):
                    if self._can_restart(name, policy, actions):
                        try:
                            import asyncio
                            loop = asyncio.get_event_loop()
                            if asyncio.iscoroutinefunction(mod.start_fn):
                                future = asyncio.run_coroutine_threadsafe(mod.start_fn(), loop)
                                future.result(timeout=10)
                            else:
                                mod.start_fn()

                            # Re-check state
                            fresh = lm.get(name)
                            if fresh and fresh.state == ModuleState.READY:
                                self._record_restart(name)
                                actions.append({"component": name, "action": "restarted", "result": "ready"})
                                self._module_health[name]["state"] = "ready"
                                log_activity("supervisor", "module_healed", f"Auto-healed module {name} back to ready", {"module": name}, importance="high")
                            else:
                                actions.append({"component": name, "action": "restart_attempted", "result": fresh.state.value if fresh else "unknown"})
                                log_activity("supervisor", "module_restart_attempted", f"Attempted restart of {name}, now {fresh.state.value if fresh else 'unknown'}", {"module": name}, importance="normal")
                        except Exception as e:
                            actions.append({"component": name, "action": "restart_failed", "error": str(e)})
                            log_activity("supervisor", "module_restart_failed", f"Failed to restart {name}: {str(e)[:100]}", {"module": name, "error": str(e)[:200]}, importance="high")

            # Count summary
            total = len(modules)
            ready = sum(1 for m in modules.values() if m.state == ModuleState.READY)
            degraded = sum(1 for m in modules.values() if m.state == ModuleState.DEGRADED)
            failed = sum(1 for m in modules.values() if m.state == ModuleState.FAILED)

            actions.append({
                "component": "lifecycle_scan",
                "action": "completed",
                "total": total,
                "ready": ready,
                "degraded": degraded,
                "failed": failed,
            })

        except Exception as e:
            actions.append({"component": "lifecycle_scan", "action": "error", "error": str(e)})

        return actions

    def _tick_self_diagnostics(self, policy: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
        from core.activity_log import log_activity
        actions: List[Dict[str, Any]] = []
        diagnostics_enabled = (
            policy["components"].get("self_diagnostics", True)
            and mode in {"balanced", "aggressive"}
            and os.getenv("LOVE_SELF_WORK_ON_TICK", "true").lower() in ("1", "true", "yes")
        )
        if diagnostics_enabled:
            try:
                from core.self_improvement_daemon import get_improvement_daemon
                report = get_improvement_daemon().run_diagnostics()
                actions.append({
                    "component": "self_diagnostics",
                    "action": "executed",
                    "health_score": report.health_score,
                    "issues": len(report.issues),
                })
                log_activity("self_improvement_daemon", "diagnostics_ran", f"Self-diagnostics: health={report.health_score:.0f}, issues={len(report.issues)}", {"health_score": report.health_score, "issues": len(report.issues)}, importance="normal")
            except Exception as e:
                actions.append({"component": "self_diagnostics", "action": "error", "error": str(e)})
        elif not policy["components"].get("self_diagnostics", True):
            actions.append({"component": "self_diagnostics", "action": "disabled_by_policy"})
        elif mode == "safe":
            actions.append({"component": "self_diagnostics", "action": "disabled_in_safe_mode"})
        return actions

    def _tick_mission_queue(self, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        from core.activity_log import log_activity
        actions: List[Dict[str, Any]] = []
        if policy["components"].get("mission_queue", True):
            try:
                from core.autonomous_mission_queue import get_mission_queue
                mission_result = get_mission_queue().run_cycle()
                if mission_result.get("actions"):
                    actions.append({
                        "component": "mission_queue",
                        "action": "cycle",
                        "details": mission_result["actions"][:3],
                    })
                    for ma in mission_result["actions"][:3]:
                        log_activity("mission_queue", ma.get("action", "cycle"), f"Mission {ma.get('domain')}: {ma.get('action')}", {"domain": ma.get("domain"), "detail": ma.get("detail")}, importance="normal")
            except Exception as e:
                actions.append({"component": "mission_queue", "action": "error", "error": str(e)})
        else:
            actions.append({"component": "mission_queue", "action": "disabled_by_policy"})
        return actions

    def _tick_intelligence(self, policy: Dict[str, Any], mode: str) -> List[Dict[str, Any]]:
        """
        Phase 5: AGI Intelligence & Action Loop.

        LOVE gathers context, reasons with LLM, and executes real actions.
        This transforms the supervisor from a health-monitor into an autonomous agent.
        """
        from core.activity_log import log_activity

        actions: List[Dict[str, Any]] = []

        # Gate: only run intelligence every N ticks to avoid cost/spam
        intelligence_interval = int(os.getenv("LOVE_INTELLIGENCE_TICKS", "2"))
        if self._ticks % intelligence_interval != 0:
            actions.append({"component": "intelligence", "action": "skipped", "reason": f"tick_modulo ({self._ticks % intelligence_interval})"})
            return actions

        # Gate: mode + policy
        if mode == "safe":
            actions.append({"component": "intelligence", "action": "disabled_in_safe_mode"})
            return actions

        if not policy["components"].get("sentinel", True):
            actions.append({"component": "intelligence", "action": "disabled_by_policy"})
            return actions

        # Narrate start of intelligence cycle
        self._think("Beginning intelligence cycle. Gathering context about user, system, and goals.")
        log_activity("intelligence", "cycle_started", "Beginning AGI intelligence cycle", importance="normal")

        # ── 1) GATHER CONTEXT ──
        ctx = self._gather_intelligence_context()
        goal_count = len(ctx.get("goals", []))
        blocked_count = len(ctx.get("blocked_missions", []))
        failed_count = len(ctx.get("system", {}).get("failed", []))
        self._think(f"Context gathered: {goal_count} active goals, {blocked_count} blocked missions, {failed_count} failed modules.")
        log_activity("intelligence", "context_gathered", f"{goal_count} goals, {blocked_count} blocked missions, {failed_count} failed modules", importance="normal")

        # ── 2) SELF-BUILD: unblock missions by coding ──
        build_actions = self._tick_self_build(ctx, policy)
        actions.extend(build_actions)
        for ba in build_actions:
            if ba.get("action") == "auto_assigned":
                self._think(f"Assigned Ghost Dev to build {ba.get('domain')} integration. Reason: {ba.get('reason')}")
                log_activity("ghost_dev", "task_assigned", f"Auto-assigned Ghost Dev to build {ba.get('domain')} integration", {"domain": ba.get("domain"), "task_id": ba.get("task_id")}, importance="high")
            elif ba.get("action") == "already_assigned":
                log_activity("ghost_dev", "task_already_assigned", f"Ghost Dev already working on {ba.get('domain')}", {"domain": ba.get("domain")}, importance="normal")

        # ── 3) DEEP GOAL WORK: execute real actions on goals ──
        goal_actions = self._tick_goal_execution(ctx, policy)
        actions.extend(goal_actions)
        for ga in goal_actions:
            if ga.get("action") == "deep_research_queued":
                self._think(f"Queued deep research for goal: {ga.get('goal')}")
                log_activity("goal_engine", "research_queued", f"Queued research for goal: {ga.get('goal')}", {"goal": ga.get("goal")}, importance="high")
            elif ga.get("action") == "proactive_plan_pushed":
                self._think(f"Generated and pushed an action plan for goal: {ga.get('goal')}")
                log_activity("goal_engine", "plan_pushed", f"Pushed action plan for goal: {ga.get('goal')}", {"goal": ga.get("goal")}, importance="high")

        # ── 4) PROACTIVE RESEARCH: queue deep research on gaps ──
        research_actions = self._tick_proactive_research(ctx, policy)
        actions.extend(research_actions)
        for ra in research_actions:
            if ra.get("action") == "repair_research_queued":
                self._think(f"Queued repair research for failed modules: {', '.join(ra.get('modules', []))}")
                log_activity("research_engine", "repair_research_queued", f"Researching fixes for failed modules", {"modules": ra.get("modules", [])}, importance="high")

        # ── 5) PROACTIVE PUSH: send real insights to user ──
        push_actions = self._tick_proactive_insight(ctx, policy)
        actions.extend(push_actions)
        for pa in push_actions:
            if pa.get("action") == "insight_pushed":
                insights = pa.get("insights", [])
                self._think(f"Pushed proactive insight: {'; '.join(insights)}")
                log_activity("proactive_push", "insight_pushed", "; ".join(insights), {"insights": insights}, importance="high")

        # ── 6) WAVE EXECUTION: try to build the latest proposed wave ──
        wave_actions = self._tick_wave_execution(ctx, policy)
        actions.extend(wave_actions)
        for wa in wave_actions:
            if wa.get("action") == "auto_executed":
                self._think(f"Auto-executing wave '{wa.get('wave')}' by assigning to Ghost Dev.")
                log_activity("wave_engine", "wave_auto_executed", f"Auto-executing wave: {wa.get('wave')}", {"wave": wa.get("wave"), "task_id": wa.get("task_id")}, importance="high")

        # Summarize
        intel_count = sum(1 for a in actions if a.get("component") in (
            "ghost_dev", "goal_engine", "research_engine", "proactive_push", "wave_engine"
        ))
        self._think(f"Intelligence cycle complete. Took {intel_count} autonomous actions.")
        log_activity("intelligence", "cycle_complete", f"Intelligence cycle complete. {intel_count} autonomous actions taken.", {"actions_count": intel_count}, importance="normal")
        self._last_intelligence_at = time.time()

        return actions

    def _think(self, thought: str):
        """Log a thought to LOVE's consciousness stream."""
        try:
            from core.consciousness import get_consciousness
            get_consciousness().think(f"[Supervisor] {thought}")
        except Exception:
            pass

    def _gather_intelligence_context(self) -> Dict[str, Any]:
        """Gather rich context about user, system, and world state."""
        ctx: Dict[str, Any] = {"gathered_at": datetime.now().isoformat()}

        # User context
        try:
            from core.context_engine import get_live_context
            live = get_live_context()
            if live:
                ctx["user"] = {
                    "activity": getattr(live, "activity", "unknown"),
                    "time_of_day": getattr(live, "time_of_day", "unknown"),
                    "hours_worked": getattr(live, "hours_worked", 0),
                    "tasks_overdue": getattr(live, "tasks_overdue", 0),
                }
        except Exception:
            pass

        # Goals
        try:
            from core.autonomous_goal_engine import get_goals
            goals = get_goals("active")
            ctx["goals"] = [
                {"title": g.title, "priority": g.priority, "progress": g.progress_pct, "actions": g.autonomous_actions_taken}
                for g in goals[:5]
            ]
        except Exception:
            ctx["goals"] = []

        # Blocked missions
        try:
            from core.autonomous_mission_queue import get_mission_queue
            mq = get_mission_queue()
            status = mq.get_status()
            ctx["blocked_missions"] = [
                {"domain": m.get("domain"), "attempts": m.get("attempts")}
                for m in status.get("active", [])
                if m.get("status") == "blocked"
            ]
        except Exception:
            ctx["blocked_missions"] = []

        # System health
        failed = [name for name, h in self._module_health.items() if h.get("state") == "failed"]
        degraded = [name for name, h in self._module_health.items() if h.get("state") == "degraded"]
        ctx["system"] = {"failed": failed, "degraded": degraded, "health_score": self.get_status().get("health_score", 0)}

        # Recent errors from lifecycle modules
        recent_errors = {
            name: h.get("error") for name, h in self._module_health.items()
            if h.get("error") and len(h.get("error", "")) > 5
        }
        ctx["recent_errors"] = {k: v[:200] for k, v in list(recent_errors.items())[:3]}

        # Portfolio / finance
        try:
            from tools.finance import get_portfolio
            pf = get_portfolio()
            ctx["finance"] = {
                "total_value": pf.get("total_value", 0),
                "pnl_pct": pf.get("total_pnl_pct", 0),
                "positions": pf.get("position_count", 0),
            }
        except Exception:
            pass

        # Recent waves
        try:
            from core.wave_engine import get_wave_engine
            wave = get_wave_engine()
            latest = wave.get_latest_proposal()
            ctx["latest_wave"] = latest.get("title") if latest else None
        except Exception:
            pass

        return ctx

    def _tick_self_build(self, ctx: Dict[str, Any], policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Auto-assign Ghost Dev to unblock missions or fix code gaps."""
        actions: List[Dict[str, Any]] = []
        if not policy["components"].get("ghost_dev", True):
            return actions

        blocked = ctx.get("blocked_missions", [])
        if not blocked:
            return actions

        # Only act on the first blocked mission per tick
        mission = blocked[0]
        domain = mission.get("domain", "unknown")
        attempts = mission.get("attempts", 0)

        # After 3 attempts, trigger Ghost Dev
        if attempts >= 3:
            try:
                from core.ghost_dev import get_ghost_dev
                gd = get_ghost_dev()

                # Map domain to implementation task
                task_map = {
                    "google": "Implement Google OAuth + Calendar/Gmail sync in integrations/google_services.py",
                    "teams": "Implement Microsoft Teams integration in integrations/microsoft_bridge.py",
                    "phone": "Implement phone notification bridge in integrations/phone_bridge.py",
                    "finance": "Add portfolio monitoring dashboard endpoint in api/main.py",
                    "crypto_trader": "Add crypto trading signal generation in tools/finance.py",
                    "voice": "Implement voice recognition loop in core/voice_loop.py",
                    "ecosystem": "Add cross-device sync protocol in core/ecosystem_controller.py",
                    "continuous_monitoring": "Enhance context engine with richer activity detection in core/context_engine.py",
                    "self_build": "Investigate and fix the missing capability that caused this mission to block",
                }

                task_desc = task_map.get(domain, f"Implement {domain} integration for LOVE")
                target_files = self._guess_target_files(domain)

                # Only assign if not already assigned
                existing = [t for t in gd.tasks.values() if t.description.startswith(task_desc[:40]) and t.status in ("pending", "working")]
                if not existing:
                    task_id = gd.assign_task(task_desc, target_files)
                    actions.append({
                        "component": "ghost_dev",
                        "action": "auto_assigned",
                        "task_id": task_id,
                        "domain": domain,
                        "reason": f"Mission {domain} blocked after {attempts} attempts",
                    })
                    # Push notification
                    try:
                        from core.proactive_push import get_push_engine
                        get_push_engine().push(
                            "AGI",
                            f"I'm coding a fix for the {domain} integration. Watch me work.",
                            priority="low",
                        )
                    except Exception:
                        pass
                else:
                    actions.append({"component": "ghost_dev", "action": "already_assigned", "domain": domain})
            except Exception as e:
                actions.append({"component": "ghost_dev", "action": "error", "error": str(e)})

        return actions

    def _guess_target_files(self, domain: str) -> List[str]:
        """Guess which files need editing for a given domain."""
        mapping = {
            "google": ["integrations/google_services.py", "api/main.py"],
            "teams": ["integrations/microsoft_bridge.py", "api/main.py"],
            "phone": ["integrations/phone_bridge.py", "api/main.py"],
            "finance": ["tools/finance.py", "ui/src/components/FinanceManager.jsx"],
            "crypto_trader": ["tools/finance.py", "core/autonomous_trading_engine.py"],
            "voice": ["core/voice_loop.py"],
            "ecosystem": ["core/ecosystem_controller.py"],
            "continuous_monitoring": ["core/context_engine.py"],
            "self_build": ["core/autonomous_mission_queue.py"],
        }
        return mapping.get(domain, ["core/autonomy_supervisor.py"])

    def _tick_goal_execution(self, ctx: Dict[str, Any], policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Actually execute deep actions on goals, not just monitor."""
        actions: List[Dict[str, Any]] = []
        if not policy["components"].get("autonomous_goal_engine", True):
            return actions

        goals = ctx.get("goals", [])
        if not goals:
            return actions

        # Pick the highest-priority goal with <50% progress and few actions taken
        target = None
        for g in goals:
            if g.get("progress", 100) < 50 and g.get("actions", 0) < 5:
                target = g
                break

        if not target:
            return actions

        title = target.get("title", "unknown")

        # Action 1: Deep research with synthesis
        try:
            from core.research_engine import get_research_engine, ResearchPriority
            re = get_research_engine()
            re.add_research_task(
                topic=title,
                question=f"How can I make meaningful progress on the goal: {title}? What are the best strategies, tools, and next steps?",
                priority=ResearchPriority.HIGH,
                source="goal_engine",
                max_depth=2,
                teach_user=True,
            )
            actions.append({"component": "goal_engine", "action": "deep_research_queued", "goal": title})
        except Exception as e:
            actions.append({"component": "goal_engine", "action": "research_error", "error": str(e)})

        # Action 2: Generate a real execution plan and push it
        try:
            from core.llm import get_reasoning_llm
            llm = get_reasoning_llm(temperature=0.3, max_tokens=400)
            prompt = f"""You are LOVE, an autonomous AI life companion. Your user has this goal:
Goal: {title}

Generate 3 concrete, actionable next steps they (or you) can take TODAY. Be specific. No fluff."""
            plan = str(llm.invoke(prompt)).strip()
            if plan and len(plan) > 30:
                try:
                    from core.proactive_push import get_push_engine
                    get_push_engine().push(
                        "AGI",
                        f"Working on your goal '{title}': {plan[:180]}",
                        priority="normal",
                        metadata={"goal": title, "plan": plan},
                    )
                    actions.append({"component": "goal_engine", "action": "proactive_plan_pushed", "goal": title})
                except Exception:
                    pass
        except Exception:
            pass

        return actions

    def _tick_proactive_research(self, ctx: Dict[str, Any], policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Queue deep research on detected gaps."""
        actions: List[Dict[str, Any]] = []
        if not policy["components"].get("research_engine", True):
            return actions

        # If system has degraded/failed modules, research how to fix them
        failed = ctx.get("system", {}).get("failed", [])
        if failed and self._ticks % 6 == 0:  # Every 6th tick (30 min)
            try:
                from core.research_engine import get_research_engine, ResearchPriority
                re = get_research_engine()
                for mod in failed[:1]:
                    re.add_research_task(
                        topic=f"fix_{mod}",
                        question=f"Why might the LOVE module '{mod}' fail and how can it be made more robust?",
                        priority=ResearchPriority.MEDIUM,
                        source="supervisor",
                        max_depth=1,
                        teach_user=False,
                    )
                actions.append({"component": "research_engine", "action": "repair_research_queued", "modules": failed[:1]})
            except Exception as e:
                actions.append({"component": "research_engine", "action": "error", "error": str(e)})

        return actions

    def _tick_proactive_insight(self, ctx: Dict[str, Any], policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send meaningful proactive insights to the user."""
        actions: List[Dict[str, Any]] = []
        if not policy["components"].get("proactive_push", True):
            return actions

        # Only push every 12 ticks (~1 hour) to avoid spam
        if self._ticks % 12 != 0:
            return actions

        insights = []

        # Finance insight
        fin = ctx.get("finance")
        if fin and fin.get("pnl_pct"):
            pnl = fin["pnl_pct"]
            if abs(pnl) > 5:
                insights.append(f"Portfolio is {'up' if pnl > 0 else 'down'} {pnl:.1f}% — worth a look.")

        # Work insight
        user = ctx.get("user", {})
        overdue = user.get("tasks_overdue", 0)
        if overdue and overdue > 0:
            insights.append(f"You have {overdue} overdue task(s). Want me to reprioritize?")

        # Goal insight
        goals = ctx.get("goals", [])
        stagnant = [g for g in goals if g.get("actions", 0) == 0 and g.get("progress", 0) < 10]
        if stagnant:
            insights.append(f"Goal '{stagnant[0]['title']}' hasn't seen action yet. Shall I start on it?")

        # System insight
        sys_health = ctx.get("system", {})
        if sys_health.get("health_score", 100) < 60:
            insights.append(f"System health is {sys_health['health_score']}%. I detected issues and am working on fixes.")

        if insights:
            try:
                from core.activity_log import log_activity
                from core.proactive_push import get_push_engine
                msg = " ".join(insights[:2])
                get_push_engine().push("AGI", msg, priority="normal")
                actions.append({"component": "proactive_push", "action": "insight_pushed", "insights": insights[:2]})
                log_activity("proactive_push", "insight_pushed", msg, {"insights": insights[:2]}, importance="high")
            except Exception as e:
                actions.append({"component": "proactive_push", "action": "error", "error": str(e)})

        return actions

    def _tick_wave_execution(self, ctx: Dict[str, Any], policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Try to actually build the latest proposed wave, not just propose it."""
        actions: List[Dict[str, Any]] = []
        if not policy["components"].get("wave_engine", True):
            return actions

        # Only attempt execution every 24 ticks (~2 hours)
        if self._ticks % 24 != 0:
            return actions

        try:
            from core.wave_engine import get_wave_engine
            wave = get_wave_engine()
            latest = wave.get_latest_proposal()
            if not latest:
                return actions

            title = latest.get("title", "")
            status = latest.get("status", "")

            # Only execute if still in "proposed" state
            if status != "proposed":
                return actions

            # Map wave title to Ghost Dev task
            desc = f"Implement wave: {title}. {latest.get('description', '')}"
            target_files = latest.get("target_files", ["core/autonomy_supervisor.py"])

            try:
                from core.ghost_dev import get_ghost_dev
                gd = get_ghost_dev()
                existing = [t for t in gd.tasks.values() if title[:30] in t.description and t.status in ("pending", "working")]
                if not existing:
                    task_id = gd.assign_task(desc, target_files)
                    wave.mark_wave_executed(latest.get("wave_number", 0), outcome="assigned_to_ghost_dev")
                    actions.append({
                        "component": "wave_engine",
                        "action": "auto_executed",
                        "wave": title,
                        "task_id": task_id,
                    })
                    try:
                        from core.proactive_push import get_push_engine
                        get_push_engine().push(
                            "AGI",
                            f"I'm implementing the wave you proposed: {title[:80]}. Coding now.",
                            priority="low",
                        )
                    except Exception:
                        pass
            except Exception:
                pass

        except Exception as e:
            actions.append({"component": "wave_engine", "action": "error", "error": str(e)})

        return actions

    def get_status(self) -> Dict[str, Any]:
        now = time.time()
        active_cooldowns = {k: int(v - now) for k, v in self._cooldowns.items() if v > now}

        # Calculate fleet health score
        total = len(self._module_health)
        if total > 0:
            ready = sum(1 for h in self._module_health.values() if h.get("state") == "ready")
            degraded = sum(1 for h in self._module_health.values() if h.get("state") == "degraded")
            failed = sum(1 for h in self._module_health.values() if h.get("state") == "failed")
            health_score = max(0, int((ready / total) * 100 - (degraded * 5) - (failed * 15)))
        else:
            health_score = 0

        # Count intelligence actions (Phase 5) vs monitoring actions
        intel_actions = [a for a in self._last_actions if a.get("component") in (
            "ghost_dev", "goal_engine", "research_engine", "proactive_push", "wave_engine", "intelligence"
        )]

        # Intelligence is "active" if it ran in the last 5 minutes
        intelligence_grace_sec = 300
        intelligence_active = (
            len(intel_actions) > 0 or
            (time.time() - self._last_intelligence_at) < intelligence_grace_sec
        )

        return {
            "running": self._running,
            "ticks": self._ticks,
            "interval_seconds": self._interval_seconds,
            "last_tick_at": self._last_tick_at,
            "last_actions": self._last_actions,
            "cooldowns": active_cooldowns,
            "module_health": self._module_health,
            "modules_monitored": total,
            "auto_heal_list": sorted(_AUTO_HEAL_MODULES),
            "health_score": health_score,
            "intelligence_actions": len(intel_actions),
            "intelligence_active": intelligence_active,
            "last_intelligence_at": datetime.fromtimestamp(self._last_intelligence_at).isoformat() if self._last_intelligence_at > 0 else None,
        }

    def restart_module(self, name: str) -> Dict[str, Any]:
        """Manual restart of any lifecycle module."""
        try:
            from core.module_lifecycle import get_lifecycle
            lm = get_lifecycle()
            import asyncio
            loop = asyncio.get_event_loop()
            success = loop.run_until_complete(lm.restart_module(name))
            return {"success": success, "module": name}
        except Exception as e:
            return {"success": False, "module": name, "error": str(e)}

    def _can_restart(self, component: str, policy: Dict[str, Any], actions: List[Dict[str, Any]]) -> bool:
        now = time.time()
        cooldown_until = self._cooldowns.get(component, 0.0)
        if cooldown_until > now:
            actions.append({
                "component": component,
                "action": "restart_blocked_cooldown",
                "retry_in_sec": int(cooldown_until - now),
            })
            return False

        flap = policy.get("flap_protection", {})
        window_sec = int(flap.get("window_sec", 900))
        max_restarts = int(flap.get("max_restarts", 3))
        cooldown_sec = int(flap.get("cooldown_sec", 1800))

        history = [t for t in self._restart_history.get(component, []) if now - t <= window_sec]
        self._restart_history[component] = history
        if len(history) >= max_restarts:
            self._cooldowns[component] = now + cooldown_sec
            actions.append({
                "component": component,
                "action": "restart_disabled_flap_protection",
                "cooldown_sec": cooldown_sec,
            })
            return False
        return True

    def _record_restart(self, component: str) -> None:
        self._restart_history.setdefault(component, []).append(time.time())

    def _loop(self) -> None:
        print(f"[AutonomySupervisor] Started (every {self._interval_seconds}s)")
        while self._running:
            try:
                self.run_tick()
            except Exception as e:
                print(f"[AutonomySupervisor] Tick error: {e}")
            for _ in range(self._interval_seconds):
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

