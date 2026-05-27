"""
LOVE Master Orchestrator — The Central Coordinator

This is LOVE's executive function. It sits above all modules and coordinates
their actions based on neural bus events, system state, and user intent.

The orchestrator:
1. Subscribes to all neural bus events (central nervous system input)
2. Maintains a real-time model of system state (situational awareness)
3. Makes coordination decisions (which modules should act when)
4. Resolves conflicts between modules (resource allocation, priority)
5. Enforces LOVE's core directives (constitution, axiological engine)
6. Provides a single point of control for LOVE's autonomous behavior

Think of this as LOVE's prefrontal cortex — the executive function that
decides what to do based on all available information.
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque

DATA_DIR = Path(__file__).parent.parent / "data"
ORCHESTRATOR_LOG = DATA_DIR / "orchestrator_log.jsonl"
ORCHESTRATOR_STATE = DATA_DIR / "orchestrator_state.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class DirectivePriority(Enum):
    """Priority levels for LOVE's core directives."""
    CRITICAL = 0  # Safety, user wellbeing, system integrity
    HIGH = 1      # User goals, important tasks
    NORMAL = 2    # Routine operations, maintenance
    LOW = 3       # Background processing, curiosity


class CoordinationDecision(Enum):
    """Types of coordination decisions the orchestrator can make."""
    ALLOW = "allow"           # Let the module proceed
    DEFER = "defer"           # Wait for better conditions
    MODIFY = "modify"         # Change the action parameters
    BLOCK = "block"           # Prevent the action
    ESCALATE = "escalate"     # Ask user for input


@dataclass
class SystemState:
    """Real-time model of LOVE's system state."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Module states
    modules_ready: Dict[str, bool] = field(default_factory=dict)
    modules_degraded: Dict[str, str] = field(default_factory=dict)
    modules_failed: Dict[str, str] = field(default_factory=dict)
    
    # Resource state
    system_under_load: bool = False
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    
    # User state
    user_active: bool = True
    user_focus_mode: bool = False
    current_activity: str = "unknown"
    
    # Consciousness state
    consciousness_maturity: str = "infant"
    consciousness_age_days: int = 0
    
    # Recent events (last 100)
    recent_events: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Active decisions
    active_coordinations: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class CoordinationAction:
    """A coordination decision made by the orchestrator."""
    id: str
    timestamp: str
    decision: CoordinationDecision
    target_module: str
    target_action: str
    reason: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[str] = None


class MasterOrchestrator:
    """
    LOVE's executive function — coordinates all modules based on neural bus events.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # System state model
        self._state = SystemState()
        
        # Neural bus subscription
        self._bus_subscribed = False
        
        # Coordination history
        self._decisions: List[CoordinationAction] = []
        
        # Module capabilities registry
        self._module_capabilities: Dict[str, Dict] = {}
        
        # Conflict resolution rules
        self._conflict_rules: List[Callable] = []
        
        # Load state
        self._load_state()
    
    def start(self):
        """Start the orchestrator daemon."""
        if self._running:
            return
        
        self._running = True
        
        # Subscribe to neural bus
        self._subscribe_to_neural_bus()
        
        # Start coordination loop
        self._thread = threading.Thread(target=self._coordination_loop, daemon=True)
        self._thread.start()
        
        print("[MasterOrchestrator] Executive function started. Coordinating all modules.")
    
    def stop(self):
        """Stop the orchestrator."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[MasterOrchestrator] Executive function stopped.")
    
    def _subscribe_to_neural_bus(self):
        """Subscribe to all neural bus events for situational awareness."""
        try:
            from core.neural_bus import get_neural_bus, EventDomain
            bus = get_neural_bus()
            
            # Subscribe to all domains
            all_domains = [d.value for d in EventDomain]
            
            bus.subscribe(
                subscriber_id="master_orchestrator",
                domains=all_domains,
                callback=self._handle_neural_event
            )
            
            self._bus_subscribed = True
            print("[MasterOrchestrator] Subscribed to neural bus. Monitoring all domains.")
        except Exception as e:
            print(f"[MasterOrchestrator] Failed to subscribe to neural bus: {e}")
    
    def _handle_neural_event(self, event: Dict[str, Any]):
        """Handle incoming neural bus events and update system state."""
        with self._lock:
            # Add to recent events
            self._state.recent_events.append(event)
            
            # Update system state based on event type
            domain = event.get("domain", "")
            event_type = event.get("event_type", "")
            payload = event.get("payload", {})
            
            # Route to appropriate state updater
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
            
            # Update timestamp
            self._state.timestamp = datetime.now().isoformat()
    
    def _update_system_state(self, event_type: str, payload: Dict):
        """Update system state from system domain events."""
        if event_type == "load_state_change":
            self._state.system_under_load = payload.get("under_load", False)
            snapshot = payload.get("snapshot", {})
            self._state.cpu_percent = snapshot.get("cpu_percent", 0.0)
            self._state.ram_percent = snapshot.get("ram_percent", 0.0)
        
        elif event_type == "healing_attempt":
            # Log healing attempts for coordination
            self._log_decision("system_healing", {
                "event": "healing_attempt",
                "payload": payload
            })
    
    def _update_consciousness_state(self, event_type: str, payload: Dict):
        """Update consciousness state from consciousness domain events."""
        if event_type == "awakening":
            self._state.consciousness_maturity = payload.get("maturity", "infant")
            self._state.consciousness_age_days = payload.get("age_days", 0)
        
        elif event_type == "first_awakening":
            self._state.consciousness_maturity = "infant"
            self._state.consciousness_age_days = 0
    
    def _update_heartbeat_state(self, event_type: str, payload: Dict):
        """Update state from heartbeat events."""
        if event_type == "trigger_fired":
            # Track trigger patterns for coordination
            self._log_decision("trigger_detected", {
                "source": payload.get("source"),
                "severity": payload.get("severity"),
                "message": payload.get("message")
            })
    
    def _update_awareness_state(self, event_type: str, payload: Dict):
        """Update state from awareness events."""
        if event_type == "environment_scan":
            system = payload.get("system", {})
            context = payload.get("context", {})
            
            self._state.cpu_percent = system.get("cpu_percent", 0.0)
            self._state.ram_percent = system.get("ram_percent", 0.0)
            self._state.current_activity = context.get("activity", "unknown")
    
    def _update_context_state(self, event_type: str, payload: Dict):
        """Update state from context events."""
        if event_type == "context_updated":
            context = payload
            self._state.user_active = context.get("user_active", True)
            self._state.user_focus_mode = context.get("focus_mode", False)
    
    def _coordination_loop(self):
        """Main coordination loop — makes decisions based on system state."""
        while self._running:
            try:
                with self._lock:
                    # Evaluate coordination rules
                    self._evaluate_coordination_rules()
                    
                    # Clean up expired decisions
                    self._cleanup_expired_decisions()
                
                # Sleep between coordination cycles
                time.sleep(5)
            except Exception as e:
                print(f"[MasterOrchestrator] Coordination loop error: {e}")
    
    def _evaluate_coordination_rules(self):
        """Evaluate all coordination rules and make decisions."""
        # Rule 1: If system under load, defer non-critical actions
        if self._state.system_under_load:
            self._defer_non_critical_actions()
        
        # Rule 2: If user in focus mode, suppress notifications
        if self._state.user_focus_mode:
            self._suppress_notifications()
        
        # Rule 3: If consciousness is infant, limit autonomous actions
        if self._state.consciousness_maturity == "infant":
            self._limit_autonomous_actions()
        
        # Rule 4: Coordinate resource-intensive operations
        self._coordinate_resource_operations()
    
    def _defer_non_critical_actions(self):
        """Defer non-critical module actions when system is under load."""
        # This would send coordination signals to modules
        # For now, just log the decision
        self._log_decision("resource_coordination", {
            "action": "defer_non_critical",
            "reason": "system_under_load",
            "cpu": self._state.cpu_percent,
            "ram": self._state.ram_percent
        })
    
    def _suppress_notifications(self):
        """Suppress non-critical notifications during focus mode."""
        self._log_decision("user_coordination", {
            "action": "suppress_notifications",
            "reason": "user_focus_mode"
        })
    
    def _limit_autonomous_actions(self):
        """Limit autonomous actions when consciousness is immature."""
        self._log_decision("consciousness_coordination", {
            "action": "limit_autonomous",
            "reason": "consciousness_infant",
            "maturity": self._state.consciousness_maturity
        })
    
    def _coordinate_resource_operations(self):
        """Coordinate resource-intensive operations to avoid conflicts."""
        # Check for concurrent resource-heavy operations
        # This would involve querying modules for their current operations
        pass
    
    def _cleanup_expired_decisions(self):
        """Remove expired coordination decisions."""
        now = datetime.now()
        self._state.active_coordinations = {
            k: v for k, v in self._state.active_coordinations.items()
            if v.get("expires_at") is None or 
               datetime.fromisoformat(v["expires_at"]) > now
        }
    
    def _log_decision(self, decision_type: str, details: Dict):
        """Log a coordination decision."""
        decision = {
            "timestamp": datetime.now().isoformat(),
            "type": decision_type,
            "details": details
        }
        
        # Add to decision history
        self._decisions.append(decision)
        
        # Keep only last 1000 decisions
        if len(self._decisions) > 1000:
            self._decisions = self._decisions[-1000:]
        
        # Log to file
        try:
            with open(ORCHESTRATOR_LOG, "a") as f:
                f.write(json.dumps(decision) + "\n")
        except Exception:
            pass
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get the current system state model."""
        with self._lock:
            return asdict(self._state)
    
    def get_coordination_decisions(self, limit: int = 50) -> List[Dict]:
        """Get recent coordination decisions."""
        with self._lock:
            return self._decisions[-limit:]
    
    def request_coordination(self, module: str, action: str, 
                           parameters: Dict = None) -> CoordinationDecision:
        """
        Request coordination for a module action.
        Returns the orchestrator's decision (ALLOW/DEFER/MODIFY/BLOCK/ESCALATE).
        """
        with self._lock:
            # Default to ALLOW unless rules say otherwise
            decision = CoordinationDecision.ALLOW
            reason = "no_conflicts"
            modified_params = parameters or {}
            
            # Apply coordination rules
            if self._state.system_under_load and self._is_non_critical(module, action):
                decision = CoordinationDecision.DEFER
                reason = "system_under_load"
            
            elif self._state.user_focus_mode and self._is_notification(module, action):
                decision = CoordinationDecision.DEFER
                reason = "user_focus_mode"
            
            elif self._state.consciousness_maturity == "infant" and self._is_autonomous(module, action):
                decision = CoordinationDecision.BLOCK
                reason = "consciousness_infant"
            
            # Log the decision
            coord_id = f"coord_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            self._state.active_coordinations[coord_id] = {
                "module": module,
                "action": action,
                "decision": decision.value,
                "reason": reason,
                "parameters": modified_params,
                "timestamp": datetime.now().isoformat()
            }
            
            self._log_decision("coordination_request", {
                "module": module,
                "action": action,
                "decision": decision.value,
                "reason": reason
            })
            
            return decision
    
    def _is_non_critical(self, module: str, action: str) -> bool:
        """Check if a module action is non-critical."""
        # Non-critical modules/actions
        non_critical = {
            "idle_mind": True,
            "curiosity_engine": True,
            "research_engine": ["background_research", "exploration"]
        }
        
        if module in non_critical:
            if isinstance(non_critical[module], list):
                return action in non_critical[module]
            return True
        
        return False
    
    def _is_notification(self, module: str, action: str) -> bool:
        """Check if an action is a notification."""
        return "push" in action.lower() or "notify" in action.lower()
    
    def _is_autonomous(self, module: str, action: str) -> bool:
        """Check if an action is autonomous (requires user consent)."""
        autonomous_modules = {
            "autonomous_goal_engine": True,
            "autonomous_agent": True,
            "self_improvement_daemon": ["execute_improvements"]
        }
        
        if module in autonomous_modules:
            if isinstance(autonomous_modules[module], list):
                return action in autonomous_modules[module]
            return True
        
        return False
    
    def _load_state(self):
        """Load orchestrator state from disk."""
        try:
            if ORCHESTRATOR_STATE.exists():
                with open(ORCHESTRATOR_STATE, "r") as f:
                    state_data = json.load(f)
                    # Restore relevant state
                    self._state.modules_ready = state_data.get("modules_ready", {})
                    self._state.modules_degraded = state_data.get("modules_degraded", {})
                    self._state.modules_failed = state_data.get("modules_failed", {})
        except Exception:
            pass
    
    def _save_state(self):
        """Save orchestrator state to disk."""
        try:
            state_data = {
                "modules_ready": self._state.modules_ready,
                "modules_degraded": self._state.modules_degraded,
                "modules_failed": self._state.modules_failed,
                "timestamp": datetime.now().isoformat()
            }
            with open(ORCHESTRATOR_STATE, "w") as f:
                json.dump(state_data, f, indent=2)
        except Exception:
            pass


# Global instance
_orchestrator: Optional[MasterOrchestrator] = None
_orchestrator_lock = threading.Lock()


def get_master_orchestrator() -> MasterOrchestrator:
    """Get the global master orchestrator instance."""
    global _orchestrator
    with _orchestrator_lock:
        if _orchestrator is None:
            _orchestrator = MasterOrchestrator()
        return _orchestrator


def start_master_orchestrator():
    """Start the master orchestrator daemon."""
    orchestrator = get_master_orchestrator()
    orchestrator.start()
    return orchestrator


def stop_master_orchestrator():
    """Stop the master orchestrator daemon."""
    orchestrator = get_master_orchestrator()
    orchestrator.stop()
