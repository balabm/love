"""
Module Registry — Auto-Discovery & Lifecycle Governance

The single source of truth for every module in LOVE's organism.

Responsibilities:
  1. Scan core/, agents/, cognition/, tools/ for BaseLOVEModule subclasses
  2. Instantiate modules in topological order (respecting dependencies)
  3. Enforce heartbeat timeouts: miss 3 heartbeats → DEGRADED → hibernate
  4. Provide the Kernel with: active modules, capabilities manifest, stress map
  5. Persist registry state across restarts
  6. Quarantine modules that crash repeatedly on startup

If a module is not in this registry, it does not exist to LOVE.
"""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type

from core.execution_guard import log_error

# Base module contract
try:
    from core.base_module import BaseLOVEModule, ModuleState, ModuleCapabilities
    BASE_MODULE_AVAILABLE = True
except Exception:
    BASE_MODULE_AVAILABLE = False
    BaseLOVEModule = None  # type: ignore
    ModuleState = None  # type: ignore
    ModuleCapabilities = None  # type: ignore

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except Exception:
    NEURAL_BUS_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data" / "module_registry"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY_STATE_FILE = DATA_DIR / "registry_state.json"
REGISTRY_LOG_FILE = DATA_DIR / "registry_log.jsonl"
QUARANTINE_FILE = DATA_DIR / "quarantine_list.json"

# Directories to scan for modules
SCAN_PATHS = [
    Path(__file__).parent.parent / "core",
    Path(__file__).parent.parent / "agents",
    Path(__file__).parent.parent / "cognition",
    Path(__file__).parent.parent / "tools",
]

# Blacklist: modules that must never be auto-loaded (critical system files, tests)
BLACKLIST = {
    "__init__",
    "base_module",
    "module_registry",
    "execution_guard",
    "neural_bus",
    "agi_spine",
    "master_orchestrator",
    "settings",
    "memory",
    "llm",
    "test_",
}


@dataclass
class RegistryEntry:
    """A single module in the registry."""
    class_name: str
    module_path: str  # Python module path e.g. 'core.finance_guardian'
    file_path: str
    instance: Optional[Any] = None
    state: str = ModuleState.DISCOVERED.name if BASE_MODULE_AVAILABLE else "unknown"
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    last_heartbeat: Optional[str] = None
    missed_heartbeats: int = 0
    capabilities: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    stress_score: float = 0.0
    error_count: int = 0
    is_legacy: bool = False  # True if module does NOT inherit BaseLOVEModule
    quarantine_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name": self.class_name,
            "module_path": self.module_path,
            "file_path": self.file_path,
            "state": self.state,
            "discovered_at": self.discovered_at,
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
            "missed_heartbeats": self.missed_heartbeats,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "stress_score": self.stress_score,
            "error_count": self.error_count,
            "is_legacy": self.is_legacy,
            "quarantine_reason": self.quarantine_reason,
        }


class ModuleRegistry:
    """
    The master registry. Singleton.
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

        self._entries: Dict[str, RegistryEntry] = {}
        self._lock = threading.RLock()
        self._running = False
        self._watchdog_thread: Optional[threading.Thread] = None
        self._quarantine_list: Set[str] = set()
        self._load_quarantine()
        self._load_state()

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def discover_all(self):
        """Scan all SCAN_PATHS for BaseLOVEModule subclasses."""
        print("[ModuleRegistry] Beginning auto-discovery sweep...")
        discovered_count = 0
        for scan_path in SCAN_PATHS:
            if not scan_path.exists():
                continue
            discovered_count += self._scan_directory(scan_path)
        print(f"[ModuleRegistry] Discovered {discovered_count} BaseLOVEModule subclass(es) (wave-registered modules handled separately)")
        self._save_state()
        self._log_event("discovery_complete", {"count": discovered_count})

    def start_all(self, max_concurrent: int = 20) -> Dict[str, Any]:
        """
        Start modules in dependency order.
        Returns report of successes and failures.
        """
        report = {"started": [], "failed": [], "skipped": [], "deferred": []}
        with self._lock:
            # Build dependency graph
            order = self._topological_sort()

            active_count = 0
            for class_name in order:
                entry = self._entries.get(class_name)
                if not entry:
                    continue
                if entry.class_name in self._quarantine_list:
                    report["skipped"].append(class_name)
                    continue
                if entry.is_legacy:
                    # Legacy modules are noted but not lifecycle-managed
                    report["skipped"].append(class_name)
                    continue
                if active_count >= max_concurrent:
                    report["deferred"].append(class_name)
                    continue

                success = self._start_entry(entry)
                if success:
                    report["started"].append(class_name)
                    active_count += 1
                else:
                    report["failed"].append(class_name)

        self._save_state()
        self._log_event("start_all", report)
        self._start_watchdog()
        return report

    def stop_all(self):
        """Gracefully stop all active modules."""
        with self._lock:
            for entry in list(self._entries.values()):
                if entry.instance and hasattr(entry.instance, "stop"):
                    try:
                        entry.instance.stop()
                        entry.state = ModuleState.STOPPED.name if BASE_MODULE_AVAILABLE else "stopped"
                    except Exception as e:
                        log_error(e, module="core.module_registry", context={"action": "stop_all", "target": entry.class_name})
        self._running = False
        self._save_state()
        self._log_event("stop_all", {})

    def get_entry(self, class_name: str) -> Optional[RegistryEntry]:
        with self._lock:
            return self._entries.get(class_name)

    def get_active_modules(self) -> List[RegistryEntry]:
        with self._lock:
            return [e for e in self._entries.values() if e.state == (ModuleState.ACTIVE.name if BASE_MODULE_AVAILABLE else "active")]

    def get_all_entries(self) -> List[RegistryEntry]:
        with self._lock:
            return list(self._entries.values())

    def get_capabilities_manifest(self) -> Dict[str, Dict[str, Any]]:
        """Return a map of module_name -> capabilities for the Gap Detector."""
        with self._lock:
            return {
                e.class_name: e.capabilities
                for e in self._entries.values()
                if e.capabilities
            }

    def get_stress_map(self) -> Dict[str, float]:
        """Return module_name -> stress_score for the Resource Governor."""
        with self._lock:
            return {
                e.class_name: e.stress_score
                for e in self._entries.values()
                if e.state == (ModuleState.ACTIVE.name if BASE_MODULE_AVAILABLE else "active")
            }

    def hibernate_module(self, class_name: str) -> bool:
        entry = self.get_entry(class_name)
        if not entry or not entry.instance or entry.is_legacy:
            return False
        try:
            if hasattr(entry.instance, "hibernate"):
                entry.instance.hibernate()
            entry.state = ModuleState.HIBERNATING.name if BASE_MODULE_AVAILABLE else "hibernating"
            self._save_state()
            self._log_event("hibernate", {"module": class_name})
            return True
        except Exception as e:
            log_error(e, module="core.module_registry", context={"action": "hibernate", "target": class_name})
            return False

    def wake_module(self, class_name: str) -> bool:
        entry = self.get_entry(class_name)
        if not entry or not entry.instance or entry.is_legacy:
            return False
        try:
            if hasattr(entry.instance, "wake"):
                entry.instance.wake()
            entry.state = ModuleState.ACTIVE.name if BASE_MODULE_AVAILABLE else "active"
            self._save_state()
            self._log_event("wake", {"module": class_name})
            return True
        except Exception as e:
            log_error(e, module="core.module_registry", context={"action": "wake", "target": class_name})
            return False

    def quarantine_module(self, class_name: str, reason: str):
        """Permanently remove a module from rotation."""
        with self._lock:
            self._quarantine_list.add(class_name)
            entry = self._entries.get(class_name)
            if entry:
                entry.quarantine_reason = reason
                entry.state = ModuleState.QUARANTINED.name if BASE_MODULE_AVAILABLE else "quarantined"
                if entry.instance and hasattr(entry.instance, "stop"):
                    try:
                        entry.instance.stop()
                    except Exception:
                        pass
        self._save_quarantine()
        self._save_state()
        self._log_event("quarantine", {"module": class_name, "reason": reason})

    def register_legacy_module(self, name: str, instance: Any, capabilities: Optional[Dict] = None):
        """
        Register a module that does NOT inherit BaseLOVEModule.
        This is a bridge for existing code until full migration.
        """
        entry = RegistryEntry(
            class_name=name,
            module_path="legacy",
            file_path="legacy",
            instance=instance,
            state="active",
            is_legacy=True,
            capabilities=capabilities or {},
        )
        with self._lock:
            self._entries[name] = entry
        self._save_state()

    # ═══════════════════════════════════════════════════════════════════════
    # DISCOVERY
    # ═══════════════════════════════════════════════════════════════════════

    def _scan_directory(self, scan_path: Path) -> int:
        discovered = 0
        # Convert filesystem path to python package prefix
        if "core" in str(scan_path):
            pkg_prefix = "core"
        elif "agents" in str(scan_path):
            pkg_prefix = "agents"
        elif "cognition" in str(scan_path):
            pkg_prefix = "cognition"
        elif "tools" in str(scan_path):
            pkg_prefix = "tools"
        else:
            pkg_prefix = ""

        # Ensure parent of scan_path is on sys.path for imports
        parent = str(scan_path.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)

        for _, mod_name, is_pkg in pkgutil.iter_modules([str(scan_path)]):
            if is_pkg:
                continue
            if any(mod_name.startswith(bl) or bl in mod_name for bl in BLACKLIST):
                continue
            if mod_name in self._quarantine_list:
                continue

            full_module_path = f"{pkg_prefix}.{mod_name}" if pkg_prefix else mod_name
            file_path = str(scan_path / f"{mod_name}.py")

            try:
                module = importlib.import_module(full_module_path)
            except Exception as e:
                # Quarantine after 3 import failures
                fail_key = f"import_fail:{mod_name}"
                if not hasattr(self, "_import_failures"):
                    self._import_failures = {}
                self._import_failures[fail_key] = self._import_failures.get(fail_key, 0) + 1
                if self._import_failures[fail_key] >= 3:
                    self.quarantine_module(mod_name, f"Repeated import failure: {e}")
                continue

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.startswith("_"):
                    continue
                if BASE_MODULE_AVAILABLE and issubclass(obj, BaseLOVEModule) and obj is not BaseLOVEModule:
                    entry = RegistryEntry(
                        class_name=name,
                        module_path=full_module_path,
                        file_path=file_path,
                    )
                    # Introspect class without instantiating for capabilities/dependencies
                    try:
                        # Create a temporary instance just for metadata
                        temp = obj(name=name)
                        entry.capabilities = temp.get_capabilities().to_dict()
                        entry.dependencies = temp.dependencies()
                        entry.stress_score = temp.stress_score()
                        # Immediately destroy temp — real start() will create a fresh one
                        del temp
                    except Exception as e:
                        log_error(e, module="core.module_registry", context={"action": "metadata_extract", "target": name})
                        entry.is_legacy = True  # Can't introspect, treat as legacy

                    with self._lock:
                        self._entries[name] = entry
                    discovered += 1

        return discovered

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def _start_entry(self, entry: RegistryEntry) -> bool:
        """Instantiate and start a single module. Returns success."""
        if entry.is_legacy or entry.state in ("ACTIVE", "active"):
            return True

        try:
            module = importlib.import_module(entry.module_path)
            cls = getattr(module, entry.class_name, None)
            # Fallback: if exact class name not found, scan module for BaseLOVEModule subclass
            if cls is None and BASE_MODULE_AVAILABLE:
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name.startswith("_"):
                        continue
                    if issubclass(obj, BaseLOVEModule) and obj is not BaseLOVEModule:
                        cls = obj
                        break
            if cls is None:
                raise AttributeError(f"Module '{entry.module_path}' has no class '{entry.class_name}' or any BaseLOVEModule subclass")
            instance = cls(name=entry.class_name)

            success = instance.start()
            if not success:
                entry.error_count += 1
                entry.state = ModuleState.DEAD.name if BASE_MODULE_AVAILABLE else "dead"
                return False

            entry.instance = instance
            entry.state = ModuleState.ACTIVE.name if BASE_MODULE_AVAILABLE else "active"
            entry.started_at = datetime.now().isoformat()
            entry.last_heartbeat = datetime.now().isoformat()
            return True

        except Exception as e:
            entry.error_count += 1
            entry.state = ModuleState.DEAD.name if BASE_MODULE_AVAILABLE else "dead"
            log_error(e, module="core.module_registry", context={"action": "start_entry", "target": entry.class_name})
            if entry.error_count >= 3:
                self.quarantine_module(entry.class_name, f"Startup crash x{entry.error_count}: {e}")
            return False

    def _topological_sort(self) -> List[str]:
        """Kahn's algorithm for dependency ordering."""
        with self._lock:
            graph = {e.class_name: set(e.dependencies) for e in self._entries.values() if not e.is_legacy}
            in_degree = {name: 0 for name in graph}
            for deps in graph.values():
                for dep in deps:
                    if dep in in_degree:
                        in_degree[dep] = in_degree.get(dep, 0)  # ensure exists
            for name, deps in graph.items():
                for dep in deps:
                    if dep in in_degree:
                        in_degree[dep] += 1

            queue = [n for n, d in in_degree.items() if d == 0]
            order = []
            while queue:
                node = queue.pop(0)
                order.append(node)
                for other, deps in graph.items():
                    if node in deps and other in in_degree:
                        in_degree[other] -= 1
                        if in_degree[other] == 0:
                            queue.append(other)

            # Append any remaining (circular deps or unmet deps) at the end
            remaining = [n for n in graph if n not in order]
            order.extend(remaining)
            return order

    # ═══════════════════════════════════════════════════════════════════════
    # WATCHDOG — Heartbeat Enforcement
    # ═══════════════════════════════════════════════════════════════════════

    def _start_watchdog(self):
        if self._running:
            return
        self._running = True
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="LOVE-RegistryWatchdog",
        )
        self._watchdog_thread.start()
        print("[ModuleRegistry] Watchdog started")

    def _watchdog_loop(self):
        """Every 60s, check for missed heartbeats and enforce policy."""
        time.sleep(10)  # Let startup settle
        while self._running:
            try:
                self._enforce_heartbeats()
            except Exception as e:
                log_error(e, module="core.module_registry", context={"phase": "watchdog"})
            # Sleep in chunks for responsive shutdown
            slept = 0
            while slept < 60 and self._running:
                time.sleep(5)
                slept += 5

    def _enforce_heartbeats(self):
        now = datetime.now()
        with self._lock:
            for entry in list(self._entries.values()):
                if entry.is_legacy or not entry.instance:
                    continue
                if entry.state != (ModuleState.ACTIVE.name if BASE_MODULE_AVAILABLE else "active"):
                    continue

                # Check last heartbeat via instance health if available
                try:
                    if hasattr(entry.instance, "health_check"):
                        health = entry.instance.health_check()
                        hb_str = health.last_heartbeat or entry.last_heartbeat
                        if hb_str:
                            hb_time = datetime.fromisoformat(hb_str)
                            elapsed = (now - hb_time).total_seconds()
                            if elapsed > 120:
                                entry.missed_heartbeats += 1
                            else:
                                entry.missed_heartbeats = 0
                except Exception:
                    entry.missed_heartbeats += 1

                # Policy enforcement
                if entry.missed_heartbeats >= 3:
                    entry.state = ModuleState.DEGRADED.name if BASE_MODULE_AVAILABLE else "degraded"
                    self._log_event("degraded", {"module": entry.class_name, "reason": "missed_heartbeats"})
                    # Attempt hibernation
                    try:
                        if hasattr(entry.instance, "hibernate"):
                            entry.instance.hibernate()
                        entry.state = ModuleState.HIBERNATING.name if BASE_MODULE_AVAILABLE else "hibernating"
                    except Exception as e:
                        log_error(e, module="core.module_registry", context={"action": "auto_hibernate", "target": entry.class_name})
                        entry.state = ModuleState.DEAD.name if BASE_MODULE_AVAILABLE else "dead"

        self._save_state()

    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    def _save_state(self):
        try:
            with self._lock:
                data = {
                    "saved_at": datetime.now().isoformat(),
                    "entries": {k: v.to_dict() for k, v in self._entries.items()},
                }
            REGISTRY_STATE_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            log_error(e, module="core.module_registry", context={"phase": "save_state"})

    def _load_state(self):
        if not REGISTRY_STATE_FILE.exists():
            return
        try:
            data = json.loads(REGISTRY_STATE_FILE.read_text(encoding="utf-8"))
            for class_name, entry_data in data.get("entries", {}).items():
                # Only restore metadata, not instances
                entry = RegistryEntry(
                    class_name=entry_data.get("class_name", class_name),
                    module_path=entry_data.get("module_path", ""),
                    file_path=entry_data.get("file_path", ""),
                    state=entry_data.get("state", ModuleState.DISCOVERED.name if BASE_MODULE_AVAILABLE else "unknown"),
                    discovered_at=entry_data.get("discovered_at", datetime.now().isoformat()),
                    capabilities=entry_data.get("capabilities", {}),
                    dependencies=entry_data.get("dependencies", []),
                    stress_score=entry_data.get("stress_score", 0.0),
                    is_legacy=entry_data.get("is_legacy", False),
                    quarantine_reason=entry_data.get("quarantine_reason"),
                )
                self._entries[class_name] = entry
        except Exception as e:
            log_error(e, module="core.module_registry", context={"phase": "load_state"})

    def _save_quarantine(self):
        try:
            QUARANTINE_FILE.write_text(json.dumps(list(self._quarantine_list), indent=2), encoding="utf-8")
        except Exception as e:
            log_error(e, module="core.module_registry", context={"phase": "save_quarantine"})

    def _load_quarantine(self):
        if not QUARANTINE_FILE.exists():
            return
        try:
            self._quarantine_list = set(json.loads(QUARANTINE_FILE.read_text(encoding="utf-8")))
        except Exception as e:
            log_error(e, module="core.module_registry", context={"phase": "load_quarantine"})

    def _log_event(self, event_type: str, payload: Dict[str, Any]):
        try:
            line = json.dumps({
                "ts": datetime.now().isoformat(),
                "event": event_type,
                **payload,
            }, default=str)
            with open(REGISTRY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            log_error(e, module="core.module_registry", context={"phase": "log_event"})

        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="system",
                    event_type=f"registry_{event_type}",
                    payload=payload,
                    source_module="module_registry",
                    priority=EventPriority.NORMAL,
                )
            except Exception:
                pass


# Convenience singleton getter
def get_module_registry() -> ModuleRegistry:
    return ModuleRegistry()
