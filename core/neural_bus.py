"""
LOVE Neural Bus - Wave 16: The Central Nervous System

This is the backbone that transforms LOVE from disconnected modules into a living brain.
Every module publishes events, every module subscribes to what matters.
The bus enables:
  - Real-time cross-module communication (no more file polling)
  - Event sourcing (replay any state from history)
  - Causal tracing (which event caused which)
  - Learning from event patterns (meta-intelligence)
  - Cross-device event propagation

Think of this as the corpus callosum connecting LOVE's brain hemispheres.
"""

import asyncio
import json
import time
import threading
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Coroutine
from concurrent.futures import ThreadPoolExecutor
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
EVENT_LOG = DATA_DIR / "neural_bus_events.jsonl"
BUS_STATE = DATA_DIR / "neural_bus_state.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class EventPriority(Enum):
    CRITICAL = 0    # System health, security threats
    HIGH = 1        # User needs, urgent insights
    NORMAL = 2      # Regular updates, learnings
    LOW = 3         # Background processing, curiosity
    AMBIENT = 4     # Passive observations, telemetry


class EventDomain(Enum):
    CONSCIOUSNESS = "consciousness"
    MEMORY = "memory"
    LEARNING = "learning"
    EMOTION = "emotion"
    RESEARCH = "research"
    SELF_EVOLUTION = "self_evolution"
    DEVICE = "device"
    USER = "user"
    SYSTEM = "system"
    TEACHING = "teaching"
    PREDICTION = "prediction"
    ACTION = "action"
    HEALTH = "health"


@dataclass
class NeuralEvent:
    """A single event flowing through LOVE's nervous system."""
    id: str
    domain: str
    event_type: str
    payload: Dict[str, Any]
    source_module: str
    priority: int = EventPriority.NORMAL.value
    timestamp: float = field(default_factory=time.time)
    iso_time: str = field(default_factory=lambda: datetime.now().isoformat())
    caused_by: Optional[str] = None      # ID of event that triggered this
    device_id: Optional[str] = None      # Which device generated this
    propagate: bool = True               # Should this sync to other devices
    ttl: int = 3600                      # Time-to-live in seconds (default 1hr)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "NeuralEvent":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Subscription:
    """A module's subscription to certain events."""
    subscriber_id: str
    domains: Set[str]                    # Which domains to listen to
    event_types: Set[str]               # Specific event types (empty = all)
    callback: Callable
    is_async: bool = False
    priority_filter: Optional[int] = None  # Only events at this priority or higher
    active: bool = True


class CausalChain:
    """Tracks causal relationships between events."""

    def __init__(self, max_depth: int = 10):
        self.chains: Dict[str, List[str]] = {}  # event_id -> [caused_event_ids]
        self.parents: Dict[str, str] = {}       # event_id -> parent_event_id
        self.max_depth = max_depth

    def record(self, event_id: str, caused_by: Optional[str]):
        if caused_by:
            self.parents[event_id] = caused_by
            if caused_by not in self.chains:
                self.chains[caused_by] = []
            self.chains[caused_by].append(event_id)

    def get_chain(self, event_id: str) -> List[str]:
        """Get the full causal chain leading to an event."""
        chain = []
        current = event_id
        depth = 0
        while current in self.parents and depth < self.max_depth:
            current = self.parents[current]
            chain.append(current)
            depth += 1
        return list(reversed(chain))

    def get_effects(self, event_id: str) -> List[str]:
        """Get all events caused by this event."""
        return self.chains.get(event_id, [])


class EventPatternDetector:
    """Detects recurring patterns in event streams — meta-intelligence."""

    def __init__(self, window_size: int = 100):
        self.recent_events: deque = deque(maxlen=window_size)
        self.detected_patterns: List[Dict] = []
        self.sequence_counts: Dict[str, int] = defaultdict(int)

    def observe(self, event: NeuralEvent):
        self.recent_events.append(event)
        # Track domain-event sequences
        if len(self.recent_events) >= 2:
            prev = self.recent_events[-2]
            seq_key = f"{prev.domain}:{prev.event_type} -> {event.domain}:{event.event_type}"
            self.sequence_counts[seq_key] += 1

    def get_frequent_sequences(self, min_count: int = 3) -> List[Dict]:
        """Return sequences that occur frequently — potential patterns."""
        return [
            {"sequence": seq, "count": count}
            for seq, count in self.sequence_counts.items()
            if count >= min_count
        ]

    def detect_bursts(self, domain: str, window_seconds: int = 60) -> bool:
        """Detect unusual bursts of events from a domain."""
        now = time.time()
        recent = [e for e in self.recent_events
                  if e.domain == domain and (now - e.timestamp) < window_seconds]
        return len(recent) > 10  # More than 10 events in window = burst


class NeuralBus:
    """
    The central nervous system of LOVE.
    Connects all modules through a publish/subscribe event bus.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.subscriptions: Dict[str, Subscription] = {}
        self.event_queue: deque = deque(maxlen=10000)
        self.event_history: deque = deque(maxlen=5000)
        self.causal_chain = CausalChain()
        self.pattern_detector = EventPatternDetector()
        self._lock = threading.Lock()
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._running = False
        self._process_thread: Optional[threading.Thread] = None
        self._stats = {
            "events_published": 0,
            "events_delivered": 0,
            "events_dropped": 0,
            "patterns_detected": 0,
            "started_at": datetime.now().isoformat(),
        }
        self._pending_propagation: deque = deque(maxlen=500)

        # Start processing
        self._start_processing()

    def _start_processing(self):
        """Start the event processing loop."""
        if self._running:
            return
        self._running = True
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._process_thread.start()

    def _process_loop(self):
        """Background loop that processes queued events."""
        while self._running:
            try:
                if self.event_queue:
                    event = self.event_queue.popleft()
                    self._deliver(event)
                else:
                    time.sleep(0.05)  # 50ms idle sleep
            except Exception as e:
                print(f"[NeuralBus] Process error: {e}")
                time.sleep(0.1)

    def subscribe(
        self,
        subscriber_id: str,
        domains: List[str],
        callback: Callable,
        event_types: List[str] = None,
        priority_filter: int = None,
        is_async: bool = False,
    ) -> str:
        """Subscribe a module to events from specific domains."""
        sub = Subscription(
            subscriber_id=subscriber_id,
            domains=set(domains),
            event_types=set(event_types) if event_types else set(),
            callback=callback,
            is_async=is_async,
            priority_filter=priority_filter,
        )
        self.subscriptions[subscriber_id] = sub
        return subscriber_id

    def unsubscribe(self, subscriber_id: str):
        """Remove a subscription."""
        self.subscriptions.pop(subscriber_id, None)

    def publish(
        self,
        domain: str,
        event_type: str,
        payload: Dict[str, Any],
        source_module: str,
        priority: EventPriority = EventPriority.NORMAL,
        caused_by: Optional[str] = None,
        device_id: Optional[str] = None,
        propagate: bool = True,
        ttl: int = 3600,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Publish an event to the neural bus. Returns event ID."""
        event = NeuralEvent(
            id=str(uuid.uuid4())[:12],
            domain=domain,
            event_type=event_type,
            payload=payload,
            source_module=source_module,
            priority=priority.value,
            caused_by=caused_by,
            device_id=device_id,
            propagate=propagate,
            ttl=ttl,
            metadata=metadata or {},
        )

        # Record causality
        self.causal_chain.record(event.id, caused_by)

        # Pattern detection
        self.pattern_detector.observe(event)

        # Queue for processing
        with self._lock:
            self.event_queue.append(event)
            self.event_history.append(event)
            self._stats["events_published"] += 1

        # Log critical/high priority events
        if priority.value <= EventPriority.HIGH.value:
            self._persist_event(event)

        # Mark for cross-device propagation
        if propagate:
            self._pending_propagation.append(event)

        return event.id

    def _deliver(self, event: NeuralEvent):
        """Deliver an event to all matching subscribers."""
        for sub_id, sub in list(self.subscriptions.items()):
            if not sub.active:
                continue

            # Domain match
            if event.domain not in sub.domains and "*" not in sub.domains:
                continue

            # Event type match
            if sub.event_types and event.event_type not in sub.event_types:
                continue

            # Priority filter
            if sub.priority_filter is not None and event.priority > sub.priority_filter:
                continue

            try:
                if sub.is_async and self._async_loop:
                    asyncio.run_coroutine_threadsafe(
                        sub.callback(event), self._async_loop
                    )
                else:
                    self._executor.submit(sub.callback, event)
                self._stats["events_delivered"] += 1
            except Exception as e:
                print(f"[NeuralBus] Delivery error to {sub_id}: {e}")
                self._stats["events_dropped"] += 1

    def _persist_event(self, event: NeuralEvent):
        """Persist important events to disk."""
        try:
            with open(EVENT_LOG, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.neural_bus")

    # ── Query Methods ────────────────────────────────────────────────────────

    def get_recent_events(
        self,
        domain: str = None,
        event_type: str = None,
        limit: int = 50,
        since_seconds: int = 3600,
    ) -> List[Dict]:
        """Query recent events with optional filters."""
        cutoff = time.time() - since_seconds
        results = []
        for event in reversed(list(self.event_history)):
            if event.timestamp < cutoff:
                break
            if domain and event.domain != domain:
                continue
            if event_type and event.event_type != event_type:
                continue
            results.append(event.to_dict())
            if len(results) >= limit:
                break
        return results

    def get_causal_chain(self, event_id: str) -> Dict:
        """Get the causal chain for an event."""
        chain = self.causal_chain.get_chain(event_id)
        effects = self.causal_chain.get_effects(event_id)
        return {"event_id": event_id, "causes": chain, "effects": effects}

    def get_patterns(self, min_count: int = 3) -> List[Dict]:
        """Get detected event patterns."""
        return self.pattern_detector.get_frequent_sequences(min_count)

    def get_stats(self) -> Dict:
        """Get bus statistics."""
        return {
            **self._stats,
            "active_subscriptions": len([s for s in self.subscriptions.values() if s.active]),
            "queue_depth": len(self.event_queue),
            "history_size": len(self.event_history),
            "pending_propagation": len(self._pending_propagation),
            "patterns_detected": len(self.pattern_detector.get_frequent_sequences()),
        }

    def get_pending_propagation(self, limit: int = 50) -> List[Dict]:
        """Get events pending cross-device propagation."""
        events = []
        while self._pending_propagation and len(events) < limit:
            event = self._pending_propagation.popleft()
            events.append(event.to_dict())
        return events

    # ── Convenience Publishers ───────────────────────────────────────────────

    def emit_learning(self, what: str, source: str, confidence: float = 0.7, caused_by: str = None):
        """Shortcut: LOVE learned something."""
        return self.publish(
            domain=EventDomain.LEARNING.value,
            event_type="new_learning",
            payload={"what": what, "confidence": confidence},
            source_module=source,
            caused_by=caused_by,
        )

    def emit_insight(self, insight: str, domain: str, source: str, caused_by: str = None):
        """Shortcut: LOVE generated an insight."""
        return self.publish(
            domain=EventDomain.PREDICTION.value,
            event_type="insight_generated",
            payload={"insight": insight, "about_domain": domain},
            source_module=source,
            priority=EventPriority.HIGH,
            caused_by=caused_by,
        )

    def emit_user_event(self, event_type: str, data: Dict, source: str):
        """Shortcut: Something happened with the user."""
        return self.publish(
            domain=EventDomain.USER.value,
            event_type=event_type,
            payload=data,
            source_module=source,
        )

    def emit_self_update(self, what_changed: str, details: Dict, source: str):
        """Shortcut: LOVE updated itself."""
        return self.publish(
            domain=EventDomain.SELF_EVOLUTION.value,
            event_type="self_updated",
            payload={"what_changed": what_changed, **details},
            source_module=source,
            priority=EventPriority.HIGH,
        )

    def emit_research(self, topic: str, findings: Dict, source: str, caused_by: str = None):
        """Shortcut: LOVE researched something."""
        return self.publish(
            domain=EventDomain.RESEARCH.value,
            event_type="research_complete",
            payload={"topic": topic, "findings": findings},
            source_module=source,
            caused_by=caused_by,
        )

    def emit_teaching(self, topic: str, content: str, source: str):
        """Shortcut: LOVE wants to teach something."""
        return self.publish(
            domain=EventDomain.TEACHING.value,
            event_type="teaching_ready",
            payload={"topic": topic, "content": content},
            source_module=source,
            priority=EventPriority.HIGH,
        )

    def emit_device_event(self, device_id: str, event_type: str, data: Dict, source: str):
        """Shortcut: A device event occurred."""
        return self.publish(
            domain=EventDomain.DEVICE.value,
            event_type=event_type,
            payload={"device_id": device_id, **data},
            source_module=source,
            device_id=device_id,
        )

    def emit_health(self, status: str, details: Dict, source: str):
        """Shortcut: System health update."""
        priority = EventPriority.CRITICAL if status == "error" else EventPriority.NORMAL
        return self.publish(
            domain=EventDomain.HEALTH.value,
            event_type="health_update",
            payload={"status": status, **details},
            source_module=source,
            priority=priority,
        )

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def shutdown(self):
        """Gracefully shut down the bus."""
        self._running = False
        if self._process_thread:
            self._process_thread.join(timeout=3)
        self._executor.shutdown(wait=False)
        self._save_state()

    def _save_state(self):
        """Save bus state for resumption."""
        try:
            state = {
                "stats": self._stats,
                "patterns": self.pattern_detector.get_frequent_sequences(2),
                "saved_at": datetime.now().isoformat(),
            }
            BUS_STATE.write_text(json.dumps(state, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.neural_bus")

    def set_async_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the async event loop for async subscribers."""
        self._async_loop = loop


# ── Singleton Access ─────────────────────────────────────────────────────────

_bus_instance: Optional[NeuralBus] = None


def get_neural_bus() -> NeuralBus:
    """Get the singleton NeuralBus instance."""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = NeuralBus()
    return _bus_instance
