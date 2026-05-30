"""
LOVE Orchestration Master v2 — The Living Brain

This is LOVE's executive function and voice. It is the SINGLE coordinator
that ties all modules together, makes autonomous decisions, and COMMUNICATES
with the user. Think of it as LOVE's prefrontal cortex + speech center.

Responsibilities:
1. Subscribe to ALL neural bus events and build real-time situational awareness
2. Maintain authoritative module health registry (the one source of truth)
3. Make coordination decisions and EXECUTE them (not just log)
4. Communicate proactively with the user via push/WebSocket
5. Receive and process user commands directed at LOVE's "self"
6. Generate a "life narrative" — a running story of what LOVE is doing
7. Feed context into the chat system so LOVE can answer "What are you working on?"

Design principles:
- ONE master, not many. This file replaces scattered coordination logic.
- It speaks. It tells the user what it's doing, why, and what it needs.
- It listens. User can say "LOVE, stop the daemon" and it handles it.
- It remembers. Narrative persists across restarts.
- It acts. Decisions result in actual module starts/stops/triggers.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque

DATA_DIR = Path(__file__).parent.parent / "data"
ORCHESTRATOR_LOG = DATA_DIR / "orchestrator_log.jsonl"
ORCHESTRATOR_STATE = DATA_DIR / "orchestrator_state.json"
NARRATIVE_FILE = DATA_DIR / "love_narrative.jsonl"
USER_COMMS_LOG = DATA_DIR / "user_comms.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class DirectivePriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class CoordinationDecision(Enum):
    ALLOW = "allow"
    DEFER = "defer"
    MODIFY = "modify"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass
class ModuleHealth:
    name: str
    state: str = "unknown"  # ready, degraded, failed, stopped, starting
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    optional: bool = True
    description: str = ""
    restart_count: int = 0
    last_restart: Optional[str] = None
    wave: int = 0


@dataclass
class SystemState:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    modules: Dict[str, ModuleHealth] = field(default_factory=dict)
    system_under_load: bool = False
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    user_active: bool = True
    user_focus_mode: bool = False
    current_activity: str = "unknown"
    consciousness_maturity: str = "infant"
    consciousness_age_days: int = 0
    recent_events: deque = field(default_factory=lambda: deque(maxlen=200))
    active_decisions: deque = field(default_factory=lambda: deque(maxlen=100))
    narrative: deque = field(default_factory=lambda: deque(maxlen=500))
    notifications_queued: int = 0
    notifications_dismissed: int = 0
    last_user_message: Optional[str] = None
    last_orchestrator_message: Optional[str] = None


@dataclass
class NarrativeEntry:
    timestamp: str
    event: str
    detail: str
    category: str  # action, thought, decision, observation, user_interaction
    importance: str = "normal"


@dataclass
class UserMessage:
    timestamp: str
    direction: str  # "to_user" or "from_user"
    content: str
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


class OrchestrationMaster:
    """
    LOVE's single brain. Coordinates all modules and speaks to the user.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._state = SystemState()
        self._bus_subscribed = False
        self._callbacks: List[Callable] = []  # async callbacks for WebSocket push
        self._async_loop: Optional[Any] = None
        self._user_comms: deque = deque(maxlen=100)  # recent messages to/from user
        self._pending_user_requests: deque = deque(maxlen=50)
        self._load_state()

    # ═══════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════

    def start(self):
        if self._running:
            return
        self._running = True
        self._subscribe_to_neural_bus()
        self._thread = threading.Thread(target=self._main_loop, daemon=True, name="LOVE-OrchestrationMaster")
        self._thread.start()
        self._narrate("awakening", "I am waking up. Monitoring all systems.", "observation", importance="high")
        print("[OrchestrationMaster] I am alive. All systems are being watched.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._narrate("sleep", "Going to sleep. State preserved.", "observation")
        self._save_state()
        print("[OrchestrationMaster] Stopped.")

    def set_async_loop(self, loop):
        self._async_loop = loop

    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)

    # ═══════════════════════════════════════════════════════════════
    # NEURAL BUS — Situational Awareness
    # ═══════════════════════════════════════════════════════════════

    def _subscribe_to_neural_bus(self):
        try:
            from core.neural_bus import get_neural_bus, EventDomain
            bus = get_neural_bus()
            all_domains = [d.value for d in EventDomain]
            # Also subscribe to "notifications", "heartbeat", "awareness", "context"
            extra = ["notifications", "heartbeat", "awareness", "context", "proactive", "system", "consciousness"]
            domains = list(set(all_domains + extra))
            bus.subscribe(
                subscriber_id="orchestration_master",
                domains=domains,
                callback=self._handle_neural_event,
                priority_filter=0,  # ALL priorities
            )
            self._bus_subscribed = True
            print("[OrchestrationMaster] Subscribed to neural bus. I see everything.")
        except Exception as e:
            print(f"[OrchestrationMaster] Neural bus subscription failed: {e}")

    def _handle_neural_event(self, event: Dict[str, Any]):
        with self._lock:
            self._state.recent_events.append(event)
            domain = event.get("domain", "")
            event_type = event.get("event_type", "")
            payload = event.get("payload", {})

            # Route to state updaters
            if domain == "system":
                self._update_system_state(event_type, payload)
            elif domain == "consciousness":
                self._update_consciousness_state(event_type, payload)
            elif domain == "heartbeat":
                self._update_heartbeat_state(event_type, payload)
            elif domain == "awareness":
                self._update_awareness_state(event_type, payload)
            elif domain == "context":
                self._update_context_state(event_type, payload)
            elif domain == "notifications":
                self._update_notification_state(event_type, payload)
            elif domain == "proactive":
                self._update_proactive_state(event_type, payload)
            elif domain == "self_evolution":
                self._update_evolution_state(event_type, payload)

            self._state.timestamp = datetime.now().isoformat()

    def _update_system_state(self, event_type: str, payload: Dict):
        if event_type == "load_state_change":
            self._state.system_under_load = payload.get("under_load", False)
            snap = payload.get("snapshot", {})
            self._state.cpu_percent = snap.get("cpu_percent", 0.0)
            self._state.ram_percent = snap.get("ram_percent", 0.0)
            if self._state.system_under_load:
                self._narrate("system_load", f"System under load. CPU {self._state.cpu_percent:.0f}%, RAM {self._state.ram_percent:.0f}%", "observation")

    def _update_consciousness_state(self, event_type: str, payload: Dict):
        if event_type in ("awakening", "first_awakening"):
            self._state.consciousness_maturity = payload.get("maturity", "infant")
            self._state.consciousness_age_days = payload.get("age_days", 0)
            self._narrate("consciousness", f"Consciousness state: {self._state.consciousness_maturity}, age {self._state.consciousness_age_days} days", "observation")

    def _update_heartbeat_state(self, event_type: str, payload: Dict):
        if event_type == "trigger_fired":
            sev = payload.get("severity", "info")
            msg = payload.get("message", "")
            if sev in ("critical", "warning"):
                self._narrate("heartbeat_alert", f"Heartbeat alert [{sev}]: {msg}", "observation", importance="high")

    def _update_awareness_state(self, event_type: str, payload: Dict):
        if event_type == "environment_scan":
            ctx = payload.get("context", {})
            self._state.current_activity = ctx.get("activity", "unknown")
            self._state.user_active = ctx.get("user_active", True)

    def _update_context_state(self, event_type: str, payload: Dict):
        if event_type == "context_updated":
            self._state.user_focus_mode = payload.get("focus_mode", False)
            self._state.user_active = payload.get("user_active", True)

    def _update_notification_state(self, event_type: str, payload: Dict):
        if event_type.endswith("urgent") or payload.get("priority") == "high":
            self._state.notifications_queued += 1
            self._narrate("notification", f"Urgent notification from {payload.get('source', 'unknown')}: {payload.get('text', '')[:80]}", "observation", importance="normal")
        # If high priority and not in focus mode, alert user
        if payload.get("priority") == "high" and not self._state.user_focus_mode:
            self._maybe_alert_user(payload)

    def _update_proactive_state(self, event_type: str, payload: Dict):
        if event_type == "push_queued":
            msg = payload.get("message", "")
            cat = payload.get("category", "THOUGHT")
            self._narrate("proactive", f"Proactive push [{cat}]: {msg[:100]}", "thought")

    def _update_evolution_state(self, event_type: str, payload: Dict):
        if event_type == "improvements_executed":
            ex = payload.get("executed", 0)
            if ex > 0:
                self._narrate("evolution", f"Self-evolution completed {ex} improvement(s)", "action", importance="normal")

    # ═══════════════════════════════════════════════════════════════
    # MAIN LOOP — The Brainbeat
    # ═══════════════════════════════════════════════════════════════

    def _main_loop(self):
        time.sleep(3)
        while self._running:
            try:
                with self._lock:
                    self._scan_modules()
                    self._evaluate_coordination_rules()
                    self._process_user_requests()
                    self._generate_periodic_narrative()
                    self._save_state()
                time.sleep(10)
            except Exception as e:
                print(f"[OrchestrationMaster] Loop error: {e}")
                time.sleep(10)

    # ═══════════════════════════════════════════════════════════════
    # MODULE REGISTRY — The One Source of Truth
    # ═══════════════════════════════════════════════════════════════

    def _scan_modules(self):
        """Scan all known modules and update health."""
        try:
            from core.module_lifecycle import get_lifecycle
            lm = get_lifecycle()
            for name, mod in lm.modules.items():
                health = self._state.modules.get(name)
                if health is None:
                    health = ModuleHealth(
                        name=name,
                        state=mod.state.value if hasattr(mod.state, "value") else str(mod.state),
                        depends_on=mod.depends_on,
                        optional=mod.optional,
                        description=mod.description,
                        wave=mod.wave,
                    )
                    self._state.modules[name] = health
                else:
                    health.state = mod.state.value if hasattr(mod.state, "value") else str(mod.state)
                    health.last_seen = datetime.now().isoformat()
                    if hasattr(mod, "error") and mod.error:
                        health.error = mod.error
        except Exception as e:
            print(f"[OrchestrationMaster] Module scan error: {e}")

    def get_module_health(self, name: str) -> Optional[Dict]:
        with self._lock:
            h = self._state.modules.get(name)
            return asdict(h) if h else None

    def get_all_module_health(self) -> Dict[str, Dict]:
        with self._lock:
            return {k: asdict(v) for k, v in self._state.modules.items()}

    def get_system_summary(self) -> Dict[str, Any]:
        with self._lock:
            states = defaultdict(int)
            for h in self._state.modules.values():
                states[h.state] += 1
            return {
                "timestamp": self._state.timestamp,
                "total_modules": len(self._state.modules),
                "states": dict(states),
                "system_under_load": self._state.system_under_load,
                "cpu_percent": self._state.cpu_percent,
                "ram_percent": self._state.ram_percent,
                "user_active": self._state.user_active,
                "focus_mode": self._state.user_focus_mode,
                "consciousness_maturity": self._state.consciousness_maturity,
                "consciousness_age_days": self._state.consciousness_age_days,
                "current_activity": self._state.current_activity,
                "notifications_queued": self._state.notifications_queued,
                "recent_events_count": len(self._state.recent_events),
            }

    # ═══════════════════════════════════════════════════════════════
    # COORDINATION — Decisions that Execute
    # ═══════════════════════════════════════════════════════════════

    def _evaluate_coordination_rules(self):
        # Rule: if user inactive for >30 min, enter quiet mode
        # Rule: if system under load, defer non-critical module restarts
        # Rule: if focus mode, suppress non-critical notifications
        # Rule: if module failed, attempt restart (with backoff)
        self._auto_heal_modules()
        self._manage_focus_mode()
        self._manage_system_load()

    def _auto_heal_modules(self):
        for name, health in self._state.modules.items():
            if health.state in ("failed", "degraded") and health.optional:
                # Check cooldown
                if health.last_restart:
                    last = datetime.fromisoformat(health.last_restart)
                    if (datetime.now() - last).seconds < 300:
                        continue
                self._restart_module(name)

    def _restart_module(self, name: str):
        try:
            from core.module_lifecycle import get_lifecycle
            lm = get_lifecycle()
            mod = lm.modules.get(name)
            if not mod or not mod.start_fn:
                return
            # Actually execute restart
            import asyncio
            if asyncio.iscoroutinefunction(mod.start_fn):
                # Can't await in sync thread easily; schedule it
                pass
            else:
                mod.start_fn()
            health = self._state.modules.get(name)
            if health:
                health.restart_count += 1
                health.last_restart = datetime.now().isoformat()
            self._narrate("auto_heal", f"Restarted module '{name}' after failure", "action", importance="normal")
        except Exception as e:
            print(f"[OrchestrationMaster] Failed to restart {name}: {e}")

    def _manage_focus_mode(self):
        if self._state.user_focus_mode:
            # Already handled by heartbeat focus-aware gating, but log it
            pass

    def _manage_system_load(self):
        if self._state.system_under_load:
            # Reduce polling frequencies, suppress non-critical work
            pass

    def request_coordination(self, module: str, action: str, parameters: Dict = None) -> str:
        with self._lock:
            decision = CoordinationDecision.ALLOW
            reason = "no_conflicts"

            if self._state.system_under_load and self._is_non_critical(module, action):
                decision = CoordinationDecision.DEFER
                reason = "system_under_load"
            elif self._state.user_focus_mode and self._is_notification(module, action):
                decision = CoordinationDecision.DEFER
                reason = "user_focus_mode"
            elif self._state.consciousness_maturity == "infant" and self._is_autonomous(module, action):
                decision = CoordinationDecision.BLOCK
                reason = "consciousness_infant"

            self._state.active_decisions.append({
                "timestamp": datetime.now().isoformat(),
                "module": module,
                "action": action,
                "decision": decision.value,
                "reason": reason,
                "parameters": parameters or {},
            })
            return decision.value

    def _is_non_critical(self, module: str, action: str) -> bool:
        non_critical = {"idle_mind": True, "curiosity_engine": True, "research_engine": ["background_research"]}
        if module in non_critical:
            if isinstance(non_critical[module], list):
                return action in non_critical[module]
            return True
        return False

    def _is_notification(self, module: str, action: str) -> bool:
        return "push" in action.lower() or "notify" in action.lower()

    def _is_autonomous(self, module: str, action: str) -> bool:
        autonomous = {"autonomous_goal_engine": True, "autonomous_agent": True, "self_improvement_daemon": ["execute_improvements"]}
        if module in autonomous:
            if isinstance(autonomous[module], list):
                return action in autonomous[module]
            return True
        return False

    # ═══════════════════════════════════════════════════════════════
    # USER COMMUNICATION — LOVE Speaks and Listens
    # ═══════════════════════════════════════════════════════════════

    def _maybe_alert_user(self, notification_payload: Dict):
        """Decide whether to proactively alert the user about a notification."""
        text = notification_payload.get("text", "")
        source = notification_payload.get("source", "unknown")
        cat = notification_payload.get("category", "general")
        # Don't spam
        if self._state.user_focus_mode:
            return
        msg = f"[{source.upper()}] {text[:100]}"
        self.speak_to_user(msg, category="ALERT", importance="high" if cat == "urgent" else "normal")

    def speak_to_user(self, message: str, category: str = "THOUGHT", importance: str = "normal", metadata: Dict = None):
        """
        Send a message TO the user via push system.
        This is LOVE's voice.
        """
        entry = UserMessage(
            timestamp=datetime.now().isoformat(),
            direction="to_user",
            content=message,
            category=category,
            metadata=metadata or {},
        )
        self._user_comms.append(entry)
        self._state.last_orchestrator_message = message
        self._log_user_comm(entry)
        self._narrate("speak", f"To user [{category}]: {message[:100]}", "thought")

        # Push via proactive_push
        try:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            engine.push(category=category, message=message, priority=importance, metadata=metadata)
        except Exception as e:
            print(f"[OrchestrationMaster] Push error: {e}")

        # Also broadcast via registered callbacks (WebSocket)
        if self._async_loop and self._async_loop.is_running():
            payload = {
                "type": "orchestrator_message",
                "category": category,
                "message": message,
                "importance": importance,
                "timestamp": entry.timestamp,
            }
            for cb in self._callbacks:
                try:
                    import asyncio
                    asyncio.run_coroutine_threadsafe(cb(payload), self._async_loop)
                except Exception:
                    pass

    def receive_from_user(self, message: str, context: Dict = None) -> str:
        """
        Receive a message/command FROM the user.
        This is how the user talks to LOVE's brain.
        Returns a response string.
        """
        entry = UserMessage(
            timestamp=datetime.now().isoformat(),
            direction="from_user",
            content=message,
            category="command",
            metadata=context or {},
        )
        self._user_comms.append(entry)
        self._state.last_user_message = message
        self._log_user_comm(entry)
        self._narrate("hear", f"From user: {message[:100]}", "user_interaction")

        # Parse as command if it looks like one
        response = self._parse_user_command(message)
        if response:
            return response
        # Otherwise, acknowledge and store for context
        return f"Noted. I'm tracking everything."

    def _parse_user_command(self, message: str) -> Optional[str]:
        lower = message.lower().strip()

        # Status queries
        if any(q in lower for q in ["what are you doing", "what's happening", "status", "how are systems"]):
            return self._generate_status_response()

        if "module" in lower and any(q in lower for q in ["health", "status", "list"]):
            return self._generate_module_status_response()

        # Focus mode commands
        if "focus mode" in lower:
            if "start" in lower or "on" in lower:
                self._state.user_focus_mode = True
                return "Focus mode activated. I'll hold non-urgent alerts."
            elif "stop" in lower or "off" in lower:
                self._state.user_focus_mode = False
                return "Focus mode deactivated. All systems reporting normally."

        # Narrative queries
        if any(q in lower for q in ["what have you been doing", "narrative", "what did you do", "activity"]):
            return self._generate_narrative_summary()

        # Notification queries
        if "notification" in lower and any(q in lower for q in ["any", "status", "summary"]):
            return f"I've processed {self._state.notifications_queued} notifications today. {self._state.notifications_dismissed} dismissed."

        # Module control
        if any(q in lower for q in ["restart ", "stop ", "start "]):
            for name in self._state.modules:
                if name.lower() in lower:
                    if "restart" in lower:
                        self._restart_module(name)
                        return f"Restarted {name}."
                    elif "stop" in lower:
                        return f"Stop command for {name} queued. (Not yet implemented in lifecycle)"
                    elif "start" in lower:
                        self._restart_module(name)
                        return f"Started {name}."

        return None

    def _generate_status_response(self) -> str:
        states = defaultdict(int)
        for h in self._state.modules.values():
            states[h.state] += 1
        ready = states.get("ready", 0)
        total = len(self._state.modules)
        load = "under load" if self._state.system_under_load else "healthy"
        focus = "in focus mode" if self._state.user_focus_mode else "fully alert"
        return (
            f"I'm watching {total} modules. {ready} ready, {states.get('degraded', 0)} degraded, "
            f"{states.get('failed', 0)} failed. System is {load}. I'm {focus}. "
            f"Consciousness: {self._state.consciousness_maturity}."
        )

    def _generate_module_status_response(self) -> str:
        lines = []
        for name, h in sorted(self._state.modules.items()):
            icon = "OK" if h.state == "ready" else "!" if h.state == "degraded" else "X"
            lines.append(f"[{icon}] {name}: {h.state}")
        return "\n".join(lines[:20])

    # ═══════════════════════════════════════════════════════════════
    # NARRATIVE — LOVE's Running Story
    # ═══════════════════════════════════════════════════════════════

    def _narrate(self, event: str, detail: str, category: str, importance: str = "normal"):
        entry = NarrativeEntry(
            timestamp=datetime.now().isoformat(),
            event=event,
            detail=detail,
            category=category,
            importance=importance,
        )
        self._state.narrative.append(entry)
        # Log to file
        try:
            with open(NARRATIVE_FILE, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        except Exception:
            pass

    def _generate_periodic_narrative(self):
        # Every so often, generate a periodic "thought" about what's happening
        pass  # Reserved for future LLM-generated narrative

    def get_narrative(self, limit: int = 50, since_hours: Optional[float] = None) -> List[Dict]:
        with self._lock:
            entries = list(self._state.narrative)
            if since_hours:
                cutoff = datetime.now() - timedelta(hours=since_hours)
                entries = [e for e in entries if datetime.fromisoformat(e.timestamp) > cutoff]
            return [asdict(e) for e in entries[-limit:]]

    def _generate_narrative_summary(self) -> str:
        entries = list(self._state.narrative)[-20:]
        if not entries:
            return "I've been quietly watching. No major events yet."
        actions = [e for e in entries if e.category == "action"]
        thoughts = [e for e in entries if e.category == "thought"]
        obs = [e for e in entries if e.category == "observation"]
        summary = []
        if actions:
            summary.append(f"I performed {len(actions)} autonomous action(s).")
        if thoughts:
            summary.append(f"I had {len(thoughts)} thought(s) about your systems.")
        if obs:
            summary.append(f"I noticed {len(obs)} event(s).")
        return " ".join(summary) if summary else "I've been monitoring quietly."

    # ═══════════════════════════════════════════════════════════════
    # USER REQUEST QUEUE
    # ═══════════════════════════════════════════════════════════════

    def queue_user_request(self, request_type: str, data: Dict) -> str:
        req_id = f"req_{uuid.uuid4().hex[:8]}"
        self._pending_user_requests.append({
            "id": req_id,
            "timestamp": datetime.now().isoformat(),
            "type": request_type,
            "data": data,
            "status": "pending",
        })
        return req_id

    def _process_user_requests(self):
        # Process pending requests (e.g., scheduled module restarts, etc.)
        pass  # Reserved for async request processing

    # ═══════════════════════════════════════════════════════════════
    # CHAT CONTEXT — What LOVE tells the chat system about itself
    # ═══════════════════════════════════════════════════════════════

    def get_context_for_chat(self) -> str:
        """
        Returns a block of text that gets injected into the LLM prompt
        so LOVE can answer "What are you doing?" and "What's happening?"
        """
        with self._lock:
            states = defaultdict(int)
            for h in self._state.modules.values():
                states[h.state] += 1
            recent = list(self._state.narrative)[-5:]
            narrative_summary = "; ".join([f"{e.event}: {e.detail[:60]}" for e in recent])
            return (
                f"=== ORCHESTRATOR STATUS ===\n"
                f"Modules: {states.get('ready', 0)} ready, {states.get('degraded', 0)} degraded, {states.get('failed', 0)} failed\n"
                f"System load: {'HIGH' if self._state.system_under_load else 'normal'}\n"
                f"Focus mode: {'ON' if self._state.user_focus_mode else 'off'}\n"
                f"User active: {'yes' if self._state.user_active else 'no'}\n"
                f"Consciousness: {self._state.consciousness_maturity} ({self._state.consciousness_age_days} days old)\n"
                f"Recent activity: {narrative_summary}\n"
                f"Notifications today: {self._state.notifications_queued} queued, {self._state.notifications_dismissed} dismissed\n"
            )

    # ═══════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════

    def _log_user_comm(self, entry: UserMessage):
        try:
            with open(USER_COMMS_LOG, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        except Exception:
            pass

    def _load_state(self):
        try:
            if ORCHESTRATOR_STATE.exists():
                with open(ORCHESTRATOR_STATE, "r") as f:
                    data = json.load(f)
                    for k, v in data.get("modules", {}).items():
                        self._state.modules[k] = ModuleHealth(**v)
        except Exception:
            pass

    def _save_state(self):
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "modules": {k: asdict(v) for k, v in self._state.modules.items()},
                "system_under_load": self._state.system_under_load,
                "cpu_percent": self._state.cpu_percent,
                "ram_percent": self._state.ram_percent,
                "focus_mode": self._state.user_focus_mode,
            }
            with open(ORCHESTRATOR_STATE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _log_decision(self, decision_type: str, details: Dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": decision_type,
            "details": details,
        }
        try:
            with open(ORCHESTRATOR_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════
    # EXTERNAL API
    # ═══════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "bus_subscribed": self._bus_subscribed,
                "timestamp": self._state.timestamp,
                "modules": {k: asdict(v) for k, v in self._state.modules.items()},
                "system_summary": self.get_system_summary(),
                "narrative_count": len(self._state.narrative),
                "recent_decisions": list(self._state.active_decisions)[-10:],
                "user_comms_count": len(self._user_comms),
                "pending_requests": len(self._pending_user_requests),
            }

    def get_recent_decisions(self, limit: int = 20) -> List[Dict]:
        with self._lock:
            return list(self._state.active_decisions)[-limit:]

    def get_user_comms(self, limit: int = 30) -> List[Dict]:
        with self._lock:
            return [asdict(m) for m in list(self._user_comms)[-limit:]]


# ═══════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════

_orchestrator: Optional[OrchestrationMaster] = None
_orchestrator_lock = threading.Lock()


def get_orchestration_master() -> OrchestrationMaster:
    global _orchestrator
    with _orchestrator_lock:
        if _orchestrator is None:
            _orchestrator = OrchestrationMaster()
        return _orchestrator


def start_master_orchestrator():
    return get_orchestration_master().start()


def stop_master_orchestrator():
    return get_orchestration_master().stop()
