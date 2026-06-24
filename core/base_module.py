"""
BaseLOVEModule — The Atomic Unit of LOVE's Organism

Every module in LOVE (engine, agent, tool, cognition) must inherit from this.
It enforces:
  - Neural Bus heartbeat publication every 30s
  - Health reporting (so the Kernel can kill/heal)
  - Capability declaration (so the Gap Detector knows what's missing)
  - Dependency resolution (so startup order is deterministic)
  - Stress scoring (so heavy modules hibernate when RAM is scarce)

If a module does not inherit from BaseLOVEModule, the Module Registry will
not discover it. It will be invisible to the AGI Kernel and cannot participate
in the living system.

Deterministic & Atomic. No silent failures.
"""

from __future__ import annotations

import abc
import inspect
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from core.execution_guard import log_error

# Optional neural bus integration — modules must publish even if bus is temporarily down
try:
    from core.neural_bus import get_neural_bus, EventPriority, EventDomain
    NEURAL_BUS_AVAILABLE = True
except Exception:
    NEURAL_BUS_AVAILABLE = False
    EventPriority = None  # type: ignore
    EventDomain = None  # type: ignore


class ModuleState(Enum):
    """Lifecycle states of a LOVE module."""
    DISCOVERED = auto()      # Found on disk, not yet instantiated
    INITIALIZED = auto()     # __init__ called
    STARTING = auto()        # start() in progress
    ACTIVE = auto()           # Running and healthy
    DEGRADED = auto()       # Running but reporting errors
    HIBERNATING = auto()    # Suspended to save resources
    STOPPED = auto()        # Explicitly stopped
    DEAD = auto()           # Failed repeatedly, quarantined
    QUARANTINED = auto()    # Removed from rotation pending manual review


@dataclass
class ModuleCapabilities:
    """What this module can do."""
    domain: str = "general"
    actions: List[str] = field(default_factory=list)
    events_produced: List[str] = field(default_factory=list)
    events_consumed: List[str] = field(default_factory=list)
    external_apis: List[str] = field(default_factory=list)
    resource_heavy: bool = False
    user_facing: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModuleHealth:
    """Real-time health telemetry."""
    module_id: str = ""
    module_name: str = ""
    state: str = ModuleState.DISCOVERED.name
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    last_error: Optional[str] = None
    error_count: int = 0
    restart_count: int = 0
    missed_heartbeats: int = 0
    stress_score: float = 0.0  # 0.0 - 1.0
    ram_estimate_mb: float = 0.0
    cpu_estimate_percent: float = 0.0
    uptime_seconds: float = 0.0
    capabilities: ModuleCapabilities = field(default_factory=ModuleCapabilities)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseLOVEModule(abc.ABC):
    """
    Abstract base for every module in LOVE.

    Inheriting classes MUST implement:
      - get_capabilities() -> ModuleCapabilities
      - stress_score() -> float
      - dependencies() -> List[str]
    """

    # Every module gets a unique ID on instantiation
    _module_counter = 0
    _counter_lock = threading.Lock()

    def __init__(self, name: Optional[str] = None):
        with BaseLOVEModule._counter_lock:
            BaseLOVEModule._module_counter += 1
            self._instance_id = BaseLOVEModule._module_counter

        self.module_name = name or self.__class__.__name__
        self.module_id = f"{self.module_name}_{self._instance_id}_{uuid.uuid4().hex[:6]}"
        self._state = ModuleState.INITIALIZED
        self._started_at: Optional[datetime] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        self._health = ModuleHealth(
            module_id=self.module_id,
            module_name=self.module_name,
            state=self._state.name,
        )
        self._health.capabilities = self.get_capabilities()
        self._bus_subscriber_id: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════════════
    # ABSTRACT INTERFACE — MUST OVERRIDE
    # ═══════════════════════════════════════════════════════════════════════

    @abc.abstractmethod
    def get_capabilities(self) -> ModuleCapabilities:
        """Declare what this module can do."""
        raise NotImplementedError

    @abc.abstractmethod
    def stress_score(self) -> float:
        """
        Return 0.0-1.0 representing how much this module stresses the host.
        The Kernel uses this to decide hibernation order.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def dependencies(self) -> List[str]:
        """
        List of module class names that must be ACTIVE before this one starts.
        Used by the Registry for topological ordering.
        """
        return []

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE — start/stop with built-in heartbeat
    # ═══════════════════════════════════════════════════════════════════════

    def start(self) -> bool:
        """Start the module and its heartbeat thread. Returns success."""
        with self._lock:
            if self._state in (ModuleState.ACTIVE, ModuleState.STARTING):
                return True
            self._state = ModuleState.STARTING
            self._running = True
            self._started_at = datetime.now()

        try:
            self.on_start()
        except Exception as e:
            log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "on_start"})
            self._transition(ModuleState.DEAD)
            return False

        # Subscribe to neural bus for cross-module events
        self._subscribe_to_bus()

        # Start heartbeat thread
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name=f"LOVE-HB-{self.module_name}",
        )
        self._thread.start()

        self._transition(ModuleState.ACTIVE)
        self._publish_lifecycle_event("module_started")
        return True

    def stop(self) -> bool:
        """Gracefully stop the module."""
        with self._lock:
            if self._state in (ModuleState.STOPPED, ModuleState.DEAD, ModuleState.QUARANTINED):
                return True
            self._running = False

        self._unsubscribe_from_bus()

        try:
            self.on_stop()
        except Exception as e:
            log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "on_stop"})

        if self._thread:
            self._thread.join(timeout=5)

        self._transition(ModuleState.STOPPED)
        self._publish_lifecycle_event("module_stopped")
        return True

    def hibernate(self) -> bool:
        """
        Soft-stop the module to preserve resources.
        State is preserved so it can be resumed via wake().
        """
        with self._lock:
            if self._state != ModuleState.ACTIVE:
                return False
            self._running = False

        try:
            self.on_hibernate()
        except Exception as e:
            log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "on_hibernate"})

        if self._thread:
            self._thread.join(timeout=5)

        self._transition(ModuleState.HIBERNATING)
        self._publish_lifecycle_event("module_hibernated")
        return True

    def wake(self) -> bool:
        """Resume from hibernation."""
        with self._lock:
            if self._state != ModuleState.HIBERNATING:
                return False
            self._running = True

        try:
            self.on_wake()
        except Exception as e:
            log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "on_wake"})
            self._transition(ModuleState.DEAD)
            return False

        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name=f"LOVE-HB-{self.module_name}",
        )
        self._thread.start()

        self._transition(ModuleState.ACTIVE)
        self._publish_lifecycle_event("module_woken")
        return True

    # ═══════════════════════════════════════════════════════════════════════
    # OPTIONAL HOOKS — override if needed
    # ═══════════════════════════════════════════════════════════════════════

    def on_start(self):
        """Override to initialize resources."""
        pass

    def on_stop(self):
        """Override to release resources."""
        pass

    def on_hibernate(self):
        """Override to persist transient state before sleep."""
        pass

    def on_wake(self):
        """Override to restore transient state after sleep."""
        pass

    def on_bus_event(self, event: Dict[str, Any]):
        """Override to handle cross-module events."""
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # HEALTH & TELEMETRY
    # ═══════════════════════════════════════════════════════════════════════

    def health_check(self) -> ModuleHealth:
        """Return current health snapshot."""
        with self._lock:
            self._health.state = self._state.name
            self._health.stress_score = self.stress_score()
            if self._started_at:
                self._health.uptime_seconds = (datetime.now() - self._started_at).total_seconds()
            return self._health

    def record_error(self, error: Exception, context: Optional[Dict] = None):
        """Record an error and transition to DEGRADED if repeated."""
        with self._lock:
            self._health.error_count += 1
            self._health.last_error = f"{type(error).__name__}: {error}"
            if self._health.error_count >= 3:
                self._transition(ModuleState.DEGRADED)
        log_error(error, module=f"core.base_module.{self.module_name}", context=context)

    def log_info(self, message: str):
        """Convenience logger for info-level messages."""
        try:
            from core.central_logger import get_logger
            logger = get_logger(f"core.base_module.{self.module_name}")
            logger.info(message)
        except Exception:
            print(f"[{self.module_name}] INFO: {message}")

    def log_error(self, message: str):
        """Convenience logger for error-level messages."""
        try:
            from core.central_logger import get_logger
            logger = get_logger(f"core.base_module.{self.module_name}")
            logger.error(message)
        except Exception:
            print(f"[{self.module_name}] ERROR: {message}")

    def log_warning(self, message: str):
        """Convenience logger for warning-level messages."""
        try:
            from core.central_logger import get_logger
            logger = get_logger(f"core.base_module.{self.module_name}")
            logger.warning(message)
        except Exception:
            print(f"[{self.module_name}] WARNING: {message}")

    # ═══════════════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════════════

    def _transition(self, new_state: ModuleState):
        with self._lock:
            old = self._state
            self._state = new_state
            self._health.state = new_state.name
            if new_state in (ModuleState.ACTIVE,):
                self._health.missed_heartbeats = 0

    def _heartbeat_loop(self):
        """Publish health and state to the Neural Bus every 30 seconds."""
        # Initial delay so startup storms don't collide
        time.sleep(2)
        while self._running:
            try:
                self._publish_heartbeat()
            except Exception as e:
                log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "heartbeat"})
            # Sleep in chunks for responsive shutdown
            slept = 0
            while slept < 30 and self._running:
                time.sleep(1)
                slept += 1

    def _publish_heartbeat(self):
        health = self.health_check()
        payload = {
            "module_id": health.module_id,
            "module_name": health.module_name,
            "state": health.state,
            "stress_score": health.stress_score,
            "error_count": health.error_count,
            "uptime_seconds": health.uptime_seconds,
            "capabilities": health.capabilities.to_dict(),
        }
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="system",
                    event_type="module_heartbeat",
                    payload=payload,
                    source_module=self.module_name,
                    priority=EventPriority.NORMAL,
                )
            except Exception as e:
                log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "bus_publish"})

    def _publish_lifecycle_event(self, event_type: str):
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="system",
                    event_type=event_type,
                    payload={
                        "module_id": self.module_id,
                        "module_name": self.module_name,
                        "state": self._state.name,
                        "capabilities": self.get_capabilities().to_dict(),
                    },
                    source_module=self.module_name,
                    priority=EventPriority.NORMAL,
                )
            except Exception as e:
                log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "lifecycle_event"})

    def _subscribe_to_bus(self):
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            self._bus_subscriber_id = f"{self.module_id}_bus"
            cap = self.get_capabilities()
            my_domain = cap.domain if cap and cap.domain else "general"
            # Subscribe to ALL domains so modules can react to any cross-module event.
            # Each module's on_bus_event() filters for the events it cares about.
            bus.subscribe(
                subscriber_id=self._bus_subscriber_id,
                domains=[],  # Empty = all domains (NeuralBus v2 contract)
                callback=self._on_bus_event_wrapper,
                priority_filter=EventPriority.NORMAL.value,
            )
        except Exception as e:
            log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "bus_subscribe"})

    def _unsubscribe_from_bus(self):
        if not NEURAL_BUS_AVAILABLE or not self._bus_subscriber_id:
            return
        try:
            bus = get_neural_bus()
            bus.unsubscribe(self._bus_subscriber_id)
        except Exception as e:
            log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "bus_unsubscribe"})

    def _on_bus_event_wrapper(self, event):
        try:
            # NeuralEvent objects have .to_dict(); plain dicts pass through
            event_dict = event.to_dict() if hasattr(event, "to_dict") else event
            method = self.on_bus_event
            # Some modules override on_bus_event(self, event_name, data)
            # (the modern intelligence engines). The base contract is
            # on_bus_event(self, event_dict). Dispatch by arity so both
            # signatures work without touching every subclass.
            try:
                params = inspect.signature(method).parameters
                # Subtract 'self'
                arg_count = len([p for p in params.values()
                                 if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                                 and p.name != 'self'])
            except (ValueError, TypeError):
                arg_count = 1
            if arg_count >= 2:
                event_name = event_dict.get("event_type") or event_dict.get("type") or event_dict.get("name", "")
                data = event_dict.get("payload") or event_dict.get("data") or {}
                method(event_name, data)
            else:
                method(event_dict)
        except Exception as e:
            log_error(e, module=f"core.base_module.{self.module_name}", context={"phase": "on_bus_event"})
