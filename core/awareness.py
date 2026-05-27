"""
LOVE Awareness Engine - Real-Time Environment Scanner
Jarvis-level situational awareness: what's running, what's open, what time is it,
what is the user doing RIGHT NOW, system health, location, active context.
Runs continuously in the background, feeds everything to the ContextEngine.
"""

import os
import sys
import json
import time
import platform

def _platform_system() -> str:
    """Return platform name without blocking (avoids platform.system() WMI hang)."""
    import sys as _sys
    if _sys.platform == "win32": return "Windows"
    if _sys.platform == "darwin": return "Darwin"
    return "Linux"
import subprocess
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from threading import Lock, Thread

from core.central_logger import get_logger

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class SystemSnapshot:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hostname: str = ""
    platform: str = ""
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    disk_free_gb: float = 0.0
    battery_percent: Optional[float] = None
    battery_plugged: Optional[bool] = None
    gpu_name: Optional[str] = None
    uptime_hours: float = 0.0
    network_connected: bool = True


@dataclass
class ActiveContext:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    active_window: str = ""
    active_app: str = ""
    running_apps: List[str] = field(default_factory=list)
    open_browsers: List[str] = field(default_factory=list)
    open_terminals: List[str] = field(default_factory=list)
    open_editors: List[str] = field(default_factory=list)
    time_of_day: str = ""          # morning / afternoon / evening / night
    day_of_week: str = ""
    is_weekend: bool = False
    local_time: str = ""
    recent_files: List[str] = field(default_factory=list)
    dev_activity: str = ""         # idle / coding / browsing / communicating


@dataclass
class FileActivity:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    recently_modified: List[Dict] = field(default_factory=list)
    watched_folders: List[str] = field(default_factory=list)
    new_files: List[str] = field(default_factory=list)
    project_summary: Dict = field(default_factory=dict)


class AwarenessEngine:
    """
    Jarvis-level environmental awareness.
    Continuously scans: system resources, active window, running processes,
    time context, recent file activity, network status.
    """

    KNOWN_EDITORS = ["code", "devenv", "rider", "pycharm", "intellij", "vim", "nvim", "notepad++", "sublime"]
    KNOWN_BROWSERS = ["chrome", "firefox", "msedge", "opera", "brave", "arc"]
    KNOWN_TERMINALS = ["windowsterminal", "powershell", "cmd", "wt", "alacritty", "hyper", "conemu"]
    KNOWN_COMMS = ["slack", "teams", "discord", "telegram", "whatsapp", "zoom", "skype"]

    def __init__(self):
        self._lock = Lock()
        self._system: Optional[SystemSnapshot] = None
        self._context: Optional[ActiveContext] = None
        self._files: Optional[FileActivity] = None
        self._running = False
        self._thread: Optional[Thread] = None
        self._watched_paths: List[Path] = []
        self._last_scan: Optional[datetime] = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────

    def start(self, interval_seconds: int = 30):
        if self._running:
            return
        self._running = True
        # Run one immediate scan so data is available right away
        try:
            self._scan()
        except Exception as e:
            logger.error(f"Initial scan error: {e}")
        self._thread = Thread(target=self._loop, args=(interval_seconds,), daemon=True)
        self._thread.start()
        logger.info(f"Environment scanner started ({interval_seconds}s interval)")

    def stop(self):
        self._running = False

    def add_watch_path(self, path: str):
        p = Path(path)
        if p.exists() and p not in self._watched_paths:
            self._watched_paths.append(p)

    def get_snapshot(self) -> Dict[str, Any]:
        """Get the latest full awareness snapshot."""
        with self._lock:
            return {
                "system": asdict(self._system) if self._system else {},
                "context": asdict(self._context) if self._context else {},
                "files": asdict(self._files) if self._files else {},
                "last_scan": self._last_scan.isoformat() if self._last_scan else None
            }

    def get_context_summary(self) -> str:
        """
        Human-readable summary of what LOVE knows RIGHT NOW.
        Injected into the system prompt so LOVE always has situational awareness.
        """
        snap = self.get_snapshot()
        ctx = snap.get("context", {})
        sys_s = snap.get("system", {})
        files = snap.get("files", {})

        now = datetime.now()
        parts = []

        # Time context
        parts.append(f"Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d %Y')} ({ctx.get('time_of_day', 'day')})")

        # System
        if sys_s.get("cpu_percent"):
            parts.append(f"System: CPU {sys_s['cpu_percent']:.0f}%, RAM {sys_s.get('ram_percent', 0):.0f}% ({sys_s.get('ram_used_gb', 0):.1f}/{sys_s.get('ram_total_gb', 0):.1f} GB)")
        if sys_s.get("battery_percent") is not None:
            plugged = "charging" if sys_s.get("battery_plugged") else "on battery"
            parts.append(f"Battery: {sys_s['battery_percent']:.0f}% ({plugged})")

        # Active window
        if ctx.get("active_window"):
            parts.append(f"Currently active: {ctx['active_window']}")

        # What's running
        editors = ctx.get("open_editors", [])
        browsers = ctx.get("open_browsers", [])
        terminals = ctx.get("open_terminals", [])
        comms = [a for a in ctx.get("running_apps", []) if any(c in a.lower() for c in self.KNOWN_COMMS)]

        if editors:
            parts.append(f"Editors open: {', '.join(editors[:3])}")
        if browsers:
            parts.append(f"Browsers: {', '.join(browsers[:3])}")
        if terminals:
            parts.append(f"Terminals: {', '.join(terminals[:2])}")
        if comms:
            parts.append(f"Comms: {', '.join(comms[:3])}")

        # Dev activity
        activity = ctx.get("dev_activity", "")
        if activity and activity != "idle":
            parts.append(f"Detected activity: {activity}")

        # Recent file changes
        recent = files.get("recently_modified", [])
        if recent:
            names = [f.get("name", "") for f in recent[:3]]
            parts.append(f"Recently modified files: {', '.join(names)}")

        return "\n".join(parts) if parts else "No environment data available yet."

    # ──────────────────────────────────────────────
    # INTERNAL SCAN LOOP
    # ──────────────────────────────────────────────

    def _loop(self, interval: int):
        while self._running:
            try:
                self._scan()
            except Exception as e:
                logger.error(f"Scan error: {e}")
            time.sleep(interval)

    def _scan(self):
        system = self._scan_system()
        context = self._scan_context()
        files = self._scan_files()

        with self._lock:
            self._system = system
            self._context = context
            self._files = files
            self._last_scan = datetime.now()

        self._save_snapshot()

        # Publish to neural bus for cross-module awareness
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="awareness",
                    event_type="environment_scan",
                    payload={
                        "system": asdict(system),
                        "context": asdict(context),
                        "files": asdict(files),
                        "timestamp": datetime.now().isoformat()
                    },
                    source_module="awareness",
                    priority=EventPriority.AMBIENT
                )
            except Exception as e:
                logger.error(f"Neural bus publish error: {e}")

    # ──────────────────────────────────────────────
    # SYSTEM SCANNER
    # ──────────────────────────────────────────────

    def _scan_system(self) -> SystemSnapshot:
        snap = SystemSnapshot()
        snap.hostname = socket.gethostname()
        snap.platform = _platform_system()

        try:
            import psutil
            snap.cpu_percent = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            snap.ram_percent = mem.percent
            snap.ram_used_gb = round(mem.used / 1e9, 2)
            snap.ram_total_gb = round(mem.total / 1e9, 2)
            disk = psutil.disk_usage("/")
            snap.disk_free_gb = round(disk.free / 1e9, 1)
            boot_time = psutil.boot_time()
            snap.uptime_hours = round((time.time() - boot_time) / 3600, 1)
            if hasattr(psutil, "sensors_battery"):
                batt = psutil.sensors_battery()
                if batt:
                    snap.battery_percent = round(batt.percent, 1)
                    snap.battery_plugged = batt.power_plugged
        except ImportError:
            pass

        try:
            import socket as s
            s.create_connection(("8.8.8.8", 53), timeout=2)
            snap.network_connected = True
        except OSError:
            snap.network_connected = False

        try:
            snap.gpu_name = self._get_gpu_name()
        except Exception:
            pass

        return snap

    def _get_gpu_name(self) -> Optional[str]:
        if _platform_system() == "Windows":
            try:
                out = subprocess.check_output(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    stderr=subprocess.DEVNULL, timeout=5
                ).decode()
                lines = [l.strip() for l in out.strip().splitlines() if l.strip() and "Name" not in l]
                return lines[0] if lines else None
            except Exception:
                return None
        return None

    # ──────────────────────────────────────────────
    # CONTEXT SCANNER (Active Window + Processes)
    # ──────────────────────────────────────────────

    def _scan_context(self) -> ActiveContext:
        ctx = ActiveContext()
        now = datetime.now()

        # Time context
        hour = now.hour
        if 5 <= hour < 12:
            ctx.time_of_day = "morning"
        elif 12 <= hour < 17:
            ctx.time_of_day = "afternoon"
        elif 17 <= hour < 21:
            ctx.time_of_day = "evening"
        else:
            ctx.time_of_day = "night"

        ctx.day_of_week = now.strftime("%A")
        ctx.is_weekend = now.weekday() >= 5
        ctx.local_time = now.strftime("%I:%M %p")

        # Active window
        ctx.active_window, ctx.active_app = self._get_active_window()

        # Running processes
        running = self._get_running_apps()
        ctx.running_apps = running

        ctx.open_editors = [a for a in running if any(e in a.lower() for e in self.KNOWN_EDITORS)]
        ctx.open_browsers = [a for a in running if any(b in a.lower() for b in self.KNOWN_BROWSERS)]
        ctx.open_terminals = [a for a in running if any(t in a.lower() for t in self.KNOWN_TERMINALS)]

        # Infer activity
        ctx.dev_activity = self._infer_activity(ctx)

        return ctx

    def _get_active_window(self):
        """Get the currently focused window title and app name."""
        if _platform_system() != "Windows":
            return "", ""
        try:
            import ctypes
            import ctypes.wintypes as wt

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value

            # Get process name
            pid = wt.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                import psutil
                proc = psutil.Process(pid.value)
                app = proc.name().replace(".exe", "")
            except Exception:
                app = ""

            return title[:120], app
        except Exception:
            return "", ""

    def _get_running_apps(self) -> List[str]:
        """Get list of unique running application names."""
        apps = set()
        try:
            import psutil
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"]
                    if name:
                        apps.add(name.replace(".exe", "").lower())
                except Exception:
                    pass
        except ImportError:
            pass
        return sorted(list(apps))

    def _infer_activity(self, ctx: ActiveContext) -> str:
        """Infer what the user is doing from app context."""
        window_lower = ctx.active_window.lower()
        app_lower = ctx.active_app.lower()

        if any(e in app_lower for e in self.KNOWN_EDITORS):
            return "coding"
        if any(b in app_lower for b in self.KNOWN_BROWSERS):
            if any(kw in window_lower for kw in ["stackoverflow", "github", "docs", "mdn", "learn"]):
                return "researching"
            if any(kw in window_lower for kw in ["youtube", "netflix", "twitch", "spotify"]):
                return "consuming_media"
            return "browsing"
        if any(t in app_lower for t in self.KNOWN_TERMINALS):
            return "terminal_work"
        if any(c in app_lower for c in self.KNOWN_COMMS):
            return "communicating"
        if not ctx.active_app:
            return "idle"
        return "working"

    # ──────────────────────────────────────────────
    # FILE ACTIVITY SCANNER
    # ──────────────────────────────────────────────

    def _scan_files(self) -> FileActivity:
        fa = FileActivity()
        fa.watched_folders = [str(p) for p in self._watched_paths]

        cutoff = datetime.now() - timedelta(hours=2)
        recent = []

        for watch_path in self._watched_paths:
            try:
                for item in watch_path.rglob("*"):
                    if item.is_file():
                        try:
                            mtime = datetime.fromtimestamp(item.stat().st_mtime)
                            if mtime > cutoff:
                                suffix = item.suffix.lower()
                                if suffix in [".py", ".cs", ".dart", ".js", ".ts", ".jsx", ".tsx",
                                              ".md", ".txt", ".json", ".yaml", ".toml", ".sql"]:
                                    recent.append({
                                        "name": item.name,
                                        "path": str(item),
                                        "ext": suffix,
                                        "modified": mtime.isoformat(),
                                        "size_kb": round(item.stat().st_size / 1024, 1)
                                    })
                        except Exception:
                            pass
            except Exception:
                pass

        recent.sort(key=lambda x: x.get("modified", ""), reverse=True)
        fa.recently_modified = recent[:20]

        # Project summary by extension
        ext_counts: Dict[str, int] = {}
        for f in recent:
            ext = f.get("ext", "")
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        fa.project_summary = ext_counts

        return fa

    # ──────────────────────────────────────────────
    # PERSISTENCE
    # ──────────────────────────────────────────────

    def _save_snapshot(self):
        snap_file = DATA_DIR / "awareness_snapshot.json"
        try:
            with open(snap_file, "w") as f:
                json.dump(self.get_snapshot(), f, indent=2)
        except Exception:
            pass


# ──────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────

_engine: Optional[AwarenessEngine] = None


def get_awareness() -> AwarenessEngine:
    global _engine
    if _engine is None:
        _engine = AwarenessEngine()
    return _engine


def start_awareness(watch_paths: List[str] = None):
    engine = get_awareness()
    if watch_paths:
        for p in watch_paths:
            engine.add_watch_path(p)
    engine.start()
    return engine


def get_context_summary() -> str:
    return get_awareness().get_context_summary()


def get_full_snapshot() -> Dict[str, Any]:
    return get_awareness().get_snapshot()
