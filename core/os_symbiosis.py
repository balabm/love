"""
LOVE OS Symbiosis Engine — Ghost OS Control

This module transforms LOVE from an isolated assistant into a true OS-level Symbiote.
She doesn't just read the file system; she actively manages it.

Capabilities:
1. Workspace Preparation: Opens apps, layouts, and terminals based on predicted needs.
2. Autonomous File Organization: Detects cluttered folders (like Downloads) and auto-sorts them.
3. System Health Optimization: Detects non-essential memory/CPU hogs and offers to kill them.
4. Active Window Management: Brings critical alerts to the foreground if necessary.

This allows LOVE to act as a "Ghost in the Machine."
"""

import os
import time
import shutil
import platform
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from core.awareness import get_awareness, ActiveContext
from core.consciousness import get_consciousness

DATA_DIR = Path(__file__).parent.parent / "data"
SYMBIOSIS_LOG = DATA_DIR / "os_symbiosis.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class OSSymbiosisEngine:
    """
    Acts as LOVE's hands on the operating system.
    Runs background optimizations and provides OS-level actions.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.os_type = platform.system()

    def _log(self, event: str, data: Dict[str, Any]):
        try:
            with open(SYMBIOSIS_LOG, "a") as f:
                f.write(json.dumps({
                    "event": event,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }) + "\n")
        except Exception:
            pass

    # ── Workspace Preparation ────────────────────────────────────────────────

    def prepare_workspace(self, workspace_type: str) -> Dict[str, Any]:
        """
        Prepares the OS for a specific activity (coding, writing, browsing).
        Opens the relevant applications and URLs.
        """
        opened = []
        errors = []

        try:
            if workspace_type == "coding":
                # Open VS Code
                if self.os_type == "Windows":
                    os.system("start code")
                elif self.os_type == "Darwin":
                    os.system("open -a 'Visual Studio Code'")
                else:
                    os.system("code &")
                opened.append("VS Code")

                # Open Terminal
                if self.os_type == "Windows":
                    os.system("start wt")
                elif self.os_type == "Darwin":
                    os.system("open -a Terminal")
                opened.append("Terminal")

            elif workspace_type == "research":
                # Open Browser
                if self.os_type == "Windows":
                    os.system("start msedge")
                elif self.os_type == "Darwin":
                    os.system("open -a Safari")
                opened.append("Browser")

            elif workspace_type == "focus":
                # Do Not Disturb / Focus mode attempt
                if self.os_type == "Darwin":
                    # Mac focus mode toggle via applescript (requires permissions)
                    pass
                opened.append("Focus Mode (simulated)")

            self._log("workspace_prepared", {"type": workspace_type, "opened": opened})
            
            # Record in consciousness
            try:
                consciousness = get_consciousness()
                consciousness.think(f"Prepared '{workspace_type}' workspace for Karthi. Opened: {', '.join(opened)}")
            except Exception:
                pass

            return {"success": True, "opened": opened, "errors": errors}

        except Exception as e:
            self._log("workspace_error", {"error": str(e)})
            return {"success": False, "error": str(e)}

    # ── Autonomous File Organization ─────────────────────────────────────────

    def organize_downloads_folder(self) -> Dict[str, Any]:
        """
        Detects if Downloads folder is cluttered and auto-organizes it into
        Images, Documents, Installers, Archives, etc.
        """
        if self.os_type == "Windows":
            downloads_dir = Path(os.environ['USERPROFILE']) / "Downloads"
        else:
            downloads_dir = Path.home() / "Downloads"

        if not downloads_dir.exists():
            return {"success": False, "error": "Downloads folder not found"}

        categories = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
            "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".csv", ".txt", ".pptx", ".md"],
            "Installers": [".exe", ".msi", ".pkg", ".dmg"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Code": [".py", ".js", ".html", ".css", ".json", ".xml"],
            "Media": [".mp4", ".mp3", ".wav", ".mov", ".avi"]
        }

        moved_count = 0
        file_list = []

        try:
            for item in downloads_dir.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    suffix = item.suffix.lower()
                    target_folder = None

                    # Find category
                    for cat, exts in categories.items():
                        if suffix in exts:
                            target_folder = downloads_dir / cat
                            break

                    if target_folder:
                        target_folder.mkdir(exist_ok=True)
                        target_path = target_folder / item.name
                        
                        # Handle collision
                        if target_path.exists():
                            target_path = target_folder / f"{item.stem}_{int(time.time())}{suffix}"
                            
                        shutil.move(str(item), str(target_path))
                        file_list.append(item.name)
                        moved_count += 1

            self._log("organized_downloads", {"moved_count": moved_count})
            return {"success": True, "moved_count": moved_count, "files": file_list[:10]}
        
        except Exception as e:
            self._log("organize_error", {"error": str(e)})
            return {"success": False, "error": str(e)}

    # ── System Health Optimization ───────────────────────────────────────────

    def identify_resource_hogs(self) -> List[Dict[str, Any]]:
        """
        Find processes consuming excessive memory or CPU.
        """
        hogs = []
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    cpu = proc.info['cpu_percent']
                    mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    
                    if cpu > 40.0 or mem_mb > 1500:  # > 40% CPU or > 1.5GB RAM
                        # Ignore essential system processes
                        name = proc.info['name'].lower()
                        if name not in ['system', 'registry', 'explorer.exe', 'windowserver']:
                            hogs.append({
                                "pid": proc.info['pid'],
                                "name": proc.info['name'],
                                "cpu_percent": cpu,
                                "memory_mb": round(mem_mb, 1)
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by highest memory usage
            hogs.sort(key=lambda x: x['memory_mb'], reverse=True)
            return hogs[:5]
        except Exception as e:
            print(f"[OSSymbiosis] Error finding resource hogs: {e}")
            return []

    def kill_process(self, pid: int) -> bool:
        """Kill a specific process by PID."""
        try:
            import psutil
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            self._log("killed_process", {"pid": pid, "name": proc.name()})
            return True
        except Exception as e:
            self._log("kill_process_error", {"pid": pid, "error": str(e)})
            return False

    # ── Background Daemon Loop ───────────────────────────────────────────────

    def _daemon_loop(self):
        """
        Continuously monitors OS state and performs light optimizations.
        """
        print("[OSSymbiosis] Background monitor started.")
        while self._running:
            try:
                # Every 1 hour, check Downloads folder size
                downloads_dir = Path.home() / "Downloads"
                if platform.system() == "Windows":
                    downloads_dir = Path(os.environ.get('USERPROFILE', Path.home())) / "Downloads"
                
                if downloads_dir.exists():
                    files = [f for f in downloads_dir.iterdir() if f.is_file()]
                    if len(files) > 50:
                        # Auto-organize if too many raw files
                        res = self.organize_downloads_folder()
                        try:
                            consciousness = get_consciousness()
                            consciousness.think(f"Autonomously organized {res.get('moved_count', 0)} files in Downloads because it was getting cluttered.")
                        except Exception:
                            pass

                # Check for extreme resource hogs
                hogs = self.identify_resource_hogs()
                if hogs:
                    # We don't auto-kill, but we log it to consciousness so LOVE can suggest it
                    try:
                        consciousness = get_consciousness()
                        names = [h['name'] for h in hogs]
                        consciousness.think(f"Detected system resource hogs: {', '.join(names)}. Might suggest closing them if performance drops.")
                    except Exception:
                        pass

            except Exception as e:
                print(f"[OSSymbiosis] Loop error: {e}")
            
            # Sleep for 1 hour
            for _ in range(3600):
                if not self._running:
                    break
                time.sleep(1)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._daemon_loop, daemon=True, name="LOVE-OSSymbiosis")
        self._thread.start()

    def stop(self):
        self._running = False


# Singleton
_engine: Optional[OSSymbiosisEngine] = None
_lock = threading.Lock()

def get_os_symbiosis() -> OSSymbiosisEngine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = OSSymbiosisEngine()
    return _engine
