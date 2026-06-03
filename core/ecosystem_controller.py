"""
LOVE Ecosystem Controller - Wave 16: Omnipresent Device Orchestration

This goes beyond sync — LOVE actively orchestrates all devices as ONE intelligence.
Not "device A syncs with device B" but "LOVE uses device A and device B as its limbs."

Features:
  1. Active device orchestration (send commands to any device)
  2. Context-aware device switching (know which device user is on)
  3. Distributed task execution (run tasks on the best device)
  4. Unified notification routing (reach user on the right device)
  5. Device health monitoring and self-maintenance
  6. Presence awareness (where is the user, what are they doing)
  7. Cross-device workflow continuity (pick up where you left off)
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
ECOSYSTEM_DIR = DATA_DIR / "ecosystem"
ECOSYSTEM_DIR.mkdir(parents=True, exist_ok=True)

DEVICES_STATE = ECOSYSTEM_DIR / "devices_state.json"
COMMAND_QUEUE = ECOSYSTEM_DIR / "command_queue.json"
WORKFLOW_STATE = ECOSYSTEM_DIR / "workflow_state.json"
ECOSYSTEM_LOG = ECOSYSTEM_DIR / "ecosystem_log.jsonl"


class DeviceCapability(Enum):
    COMPUTE = "compute"              # Can run heavy tasks (LLM, build)
    DISPLAY = "display"              # Has a screen for notifications
    AUDIO = "audio"                  # Can play audio/TTS
    CAMERA = "camera"                # Has camera for vision
    LOCATION = "location"            # Tracks user location
    NOTIFICATION = "notification"    # Can push notifications
    KEYBOARD = "keyboard"            # Can type/interact
    BROWSER = "browser"              # Can browse web
    MICROSOFT = "microsoft"          # Has Microsoft integration
    GOOGLE = "google"                # Has Google integration


class DeviceRole(Enum):
    SERVER = "server"                # Main LOVE brain (home PC)
    COMPANION = "companion"          # Always-with device (phone)
    WORKSTATION = "workstation"      # Office/work device
    DISPLAY = "display"              # Passive display (tablet)
    SENSOR = "sensor"                # IoT/passive data source


class CommandStatus(Enum):
    QUEUED = "queued"
    SENT = "sent"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class DeviceState:
    """Full state of a device in the ecosystem."""
    device_id: str
    name: str
    role: str
    capabilities: List[str]
    online: bool = False
    last_seen: float = 0
    battery: Optional[float] = None
    cpu_usage: Optional[float] = None
    current_activity: str = "idle"    # idle, working, browsing, meeting, gaming, sleeping
    user_present: bool = False        # Is the user actively using this device
    ip_address: str = ""
    os_type: str = ""                 # windows, android, ios, linux
    love_version: str = ""
    context: Dict[str, Any] = field(default_factory=dict)  # Device-specific context
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DeviceCommand:
    """A command LOVE sends to a device."""
    id: str
    target_device: str
    command_type: str                 # notify, speak, open_app, run_task, sync_state, lock, screenshot
    payload: Dict[str, Any]
    priority: int = 2
    status: str = CommandStatus.QUEUED.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sent_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    timeout_seconds: int = 30


@dataclass
class WorkflowContext:
    """A cross-device workflow that maintains continuity."""
    id: str
    name: str                         # What the user was doing
    last_device: str                  # Which device they were on
    state: Dict[str, Any]            # Workflow-specific state
    transferable: bool = True         # Can this be continued on another device
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EcosystemController:
    """
    LOVE's omnipresent device orchestrator.
    Treats all devices as extensions of a single intelligence.
    """

    def __init__(self):
        self._devices: Dict[str, DeviceState] = {}
        self._command_queue: List[DeviceCommand] = []
        self._workflows: Dict[str, WorkflowContext] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self._load_state()

    def _load_state(self):
        """Load ecosystem state."""
        try:
            if DEVICES_STATE.exists():
                data = json.loads(DEVICES_STATE.read_text())
                for dev_id, dev_data in data.items():
                    self._devices[dev_id] = DeviceState(**dev_data)
        except Exception:
            self._devices = {}

        try:
            if COMMAND_QUEUE.exists():
                data = json.loads(COMMAND_QUEUE.read_text())
                self._command_queue = [DeviceCommand(**c) for c in data]
        except Exception:
            self._command_queue = []

        try:
            if WORKFLOW_STATE.exists():
                data = json.loads(WORKFLOW_STATE.read_text())
                for wf_id, wf_data in data.items():
                    self._workflows[wf_id] = WorkflowContext(**wf_data)
        except Exception:
            self._workflows = {}

    def _save_state(self):
        """Persist ecosystem state."""
        try:
            dev_data = {k: asdict(v) for k, v in self._devices.items()}
            DEVICES_STATE.write_text(json.dumps(dev_data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ecosystem_controller")

        try:
            cmd_data = [asdict(c) for c in self._command_queue[-100:]]
            COMMAND_QUEUE.write_text(json.dumps(cmd_data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ecosystem_controller")

        try:
            wf_data = {k: asdict(v) for k, v in self._workflows.items()}
            WORKFLOW_STATE.write_text(json.dumps(wf_data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ecosystem_controller")

    def _log(self, entry: Dict):
        entry["ts"] = datetime.now().isoformat()
        try:
            with open(ECOSYSTEM_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ecosystem_controller")

    # ── Device Management ────────────────────────────────────────────────────

    def register_device(
        self,
        device_id: str,
        name: str,
        role: str,
        capabilities: List[str],
        ip_address: str = "",
        os_type: str = "",
    ) -> Dict:
        """Register a new device in the ecosystem."""
        device = DeviceState(
            device_id=device_id,
            name=name,
            role=role,
            capabilities=capabilities,
            online=True,
            last_seen=time.time(),
            ip_address=ip_address,
            os_type=os_type,
        )
        self._devices[device_id] = device
        self._save_state()
        self._log({"event": "device_registered", "device_id": device_id, "name": name})

        # Emit event
        try:
            from core.neural_bus import get_neural_bus, EventPriority
            bus = get_neural_bus()
            bus.emit_device_event(device_id, "registered", {
                "name": name, "role": role, "capabilities": capabilities
            }, "ecosystem_controller")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ecosystem_controller")

        return {"success": True, "device": asdict(device)}

    def heartbeat(self, device_id: str, state_update: Dict = None) -> Dict:
        """Update device heartbeat and optionally its state."""
        if device_id not in self._devices:
            return {"error": "Device not registered"}

        device = self._devices[device_id]
        device.online = True
        device.last_seen = time.time()

        if state_update:
            if "battery" in state_update:
                device.battery = state_update["battery"]
            if "cpu_usage" in state_update:
                device.cpu_usage = state_update["cpu_usage"]
            if "current_activity" in state_update:
                device.current_activity = state_update["current_activity"]
            if "user_present" in state_update:
                device.user_present = state_update["user_present"]
            if "context" in state_update:
                device.context.update(state_update["context"])

        self._save_state()

        # Return any pending commands for this device
        pending = [c for c in self._command_queue
                  if c.target_device == device_id and c.status == CommandStatus.QUEUED.value]

        return {
            "success": True,
            "pending_commands": [asdict(c) for c in pending[:5]],
        }

    def mark_offline(self, timeout_seconds: int = 120):
        """Mark devices that haven't sent heartbeat as offline."""
        now = time.time()
        for device in self._devices.values():
            if device.online and (now - device.last_seen) > timeout_seconds:
                device.online = False
                device.user_present = False
        self._save_state()

    # ── Intelligence: Where is the User? ─────────────────────────────────────

    def get_user_presence(self) -> Dict:
        """Determine where the user is and what they're doing."""
        self.mark_offline()

        active_devices = [d for d in self._devices.values() if d.online and d.user_present]
        all_online = [d for d in self._devices.values() if d.online]

        if not active_devices:
            # User not actively using any device
            return {
                "present": False,
                "likely_activity": "away",
                "active_device": None,
                "online_devices": [d.device_id for d in all_online],
            }

        # Find the primary active device
        primary = max(active_devices, key=lambda d: d.last_seen)

        return {
            "present": True,
            "likely_activity": primary.current_activity,
            "active_device": primary.device_id,
            "active_device_name": primary.name,
            "all_active": [d.device_id for d in active_devices],
            "online_devices": [d.device_id for d in all_online],
            "battery_status": {d.device_id: d.battery for d in all_online if d.battery is not None},
        }

    def get_best_device_for(self, capability: str) -> Optional[str]:
        """Find the best online device for a given capability."""
        self.mark_offline()
        candidates = [
            d for d in self._devices.values()
            if d.online and capability in d.capabilities
        ]
        if not candidates:
            return None

        # Prefer device where user is present
        user_devices = [d for d in candidates if d.user_present]
        if user_devices:
            return user_devices[0].device_id

        # Otherwise pick the one with best battery/resources
        return candidates[0].device_id

    # ── Command Execution ────────────────────────────────────────────────────

    def send_command(
        self,
        target_device: str,
        command_type: str,
        payload: Dict[str, Any],
        priority: int = 2,
        timeout: int = 30,
    ) -> str:
        """Send a command to a specific device."""
        import uuid
        cmd_id = str(uuid.uuid4())[:12]

        command = DeviceCommand(
            id=cmd_id,
            target_device=target_device,
            command_type=command_type,
            payload=payload,
            priority=priority,
            timeout_seconds=timeout,
        )
        self._command_queue.append(command)
        self._save_state()

        self._log({"event": "command_sent", "cmd_id": cmd_id, "target": target_device, "type": command_type})
        return cmd_id

    def notify_user(self, message: str, priority: int = 2, prefer_device: str = None) -> str:
        """
        Send a notification to the user on the best available device.
        LOVE figures out which device to use.
        """
        # Determine best device
        if prefer_device and prefer_device in self._devices and self._devices[prefer_device].online:
            target = prefer_device
        else:
            # Find best notification device
            target = self.get_best_device_for(DeviceCapability.NOTIFICATION.value)
            if not target:
                target = self.get_best_device_for(DeviceCapability.DISPLAY.value)

        if not target:
            self._log({"event": "notify_failed", "reason": "no_device_available"})
            return ""

        return self.send_command(target, "notify", {
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        }, priority=priority)

    def speak_to_user(self, text: str, prefer_device: str = None) -> str:
        """Speak to the user on the best available audio device."""
        target = prefer_device or self.get_best_device_for(DeviceCapability.AUDIO.value)
        if not target:
            return ""

        return self.send_command(target, "speak", {"text": text})

    def run_on_device(self, device_id: str, task: str, params: Dict = None) -> str:
        """Run a task on a specific device."""
        return self.send_command(device_id, "run_task", {
            "task": task,
            "params": params or {},
        }, timeout=60)

    # ── Command Status ───────────────────────────────────────────────────────

    def report_command_result(self, cmd_id: str, status: str, result: Dict = None) -> Dict:
        """Device reports back the result of a command."""
        for cmd in self._command_queue:
            if cmd.id == cmd_id:
                cmd.status = status
                cmd.result = result
                cmd.completed_at = datetime.now().isoformat()
                self._save_state()
                return {"success": True}
        return {"error": "Command not found"}

    # ── Workflow Continuity ───────────────────────────────────────────────────

    def save_workflow(self, workflow_name: str, device_id: str, state: Dict) -> str:
        """Save a workflow state for cross-device continuity."""
        import uuid
        wf_id = f"wf_{workflow_name.replace(' ', '_')[:20]}"

        if wf_id in self._workflows:
            wf = self._workflows[wf_id]
            wf.state = state
            wf.last_device = device_id
            wf.updated_at = datetime.now().isoformat()
        else:
            wf = WorkflowContext(
                id=wf_id,
                name=workflow_name,
                last_device=device_id,
                state=state,
            )
            self._workflows[wf_id] = wf

        self._save_state()
        return wf_id

    def resume_workflow(self, workflow_name: str) -> Optional[Dict]:
        """Get workflow state to resume on current device."""
        wf_id = f"wf_{workflow_name.replace(' ', '_')[:20]}"
        if wf_id in self._workflows:
            wf = self._workflows[wf_id]
            return {
                "name": wf.name,
                "last_device": wf.last_device,
                "state": wf.state,
                "updated_at": wf.updated_at,
            }
        return None

    # ── Smart Routing ────────────────────────────────────────────────────────

    def route_action(self, action: str, context: Dict = None) -> Dict:
        """
        Intelligently route an action to the best device.
        LOVE decides where to execute based on capabilities and user presence.
        """
        context = context or {}

        # Determine required capability
        capability_map = {
            "notify": DeviceCapability.NOTIFICATION.value,
            "speak": DeviceCapability.AUDIO.value,
            "browse": DeviceCapability.BROWSER.value,
            "compute": DeviceCapability.COMPUTE.value,
            "screenshot": DeviceCapability.DISPLAY.value,
            "type": DeviceCapability.KEYBOARD.value,
            "email": DeviceCapability.MICROSOFT.value,
            "calendar": DeviceCapability.GOOGLE.value,
        }

        required_cap = capability_map.get(action, DeviceCapability.COMPUTE.value)
        target = self.get_best_device_for(required_cap)

        if not target:
            return {"routed": False, "reason": f"No device with {required_cap} capability online"}

        return {
            "routed": True,
            "target_device": target,
            "device_name": self._devices[target].name,
            "capability": required_cap,
        }

    # ── Ecosystem Status ─────────────────────────────────────────────────────

    def get_ecosystem_status(self) -> Dict:
        """Get full ecosystem overview."""
        self.mark_offline()

        devices = []
        for dev in self._devices.values():
            devices.append({
                "id": dev.device_id,
                "name": dev.name,
                "role": dev.role,
                "online": dev.online,
                "user_present": dev.user_present,
                "battery": dev.battery,
                "activity": dev.current_activity,
                "last_seen": datetime.fromtimestamp(dev.last_seen).isoformat() if dev.last_seen else None,
            })

        presence = self.get_user_presence()

        return {
            "devices": devices,
            "online_count": len([d for d in self._devices.values() if d.online]),
            "total_devices": len(self._devices),
            "user_presence": presence,
            "pending_commands": len([c for c in self._command_queue if c.status == "queued"]),
            "active_workflows": len(self._workflows),
        }

    def get_device_health(self) -> List[Dict]:
        """Get health status of all devices."""
        self.mark_offline()
        health = []
        for dev in self._devices.values():
            status = "healthy"
            issues = []

            if not dev.online:
                status = "offline"
            elif dev.battery is not None and dev.battery < 20:
                status = "low_battery"
                issues.append(f"Battery at {dev.battery}%")
            elif dev.cpu_usage is not None and dev.cpu_usage > 90:
                status = "high_load"
                issues.append(f"CPU at {dev.cpu_usage}%")

            health.append({
                "device_id": dev.device_id,
                "name": dev.name,
                "status": status,
                "issues": issues,
                "last_seen_seconds_ago": int(time.time() - dev.last_seen) if dev.last_seen else None,
            })

        return health


# ── Singleton ────────────────────────────────────────────────────────────────

_controller: Optional[EcosystemController] = None


def get_ecosystem_controller() -> EcosystemController:
    """Get the singleton EcosystemController instance."""
    global _controller
    if _controller is None:
        _controller = EcosystemController()
    return _controller
