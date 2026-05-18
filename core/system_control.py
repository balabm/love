"""
LOVE System Control — Actual Actions on Karthi's PC

This is what makes LOVE Jarvis. Not "I can help you with that" — actually doing it.

Capabilities:
- Open apps (Chrome, VSCode, Spotify, etc.)
- Type text into active window
- Take screenshots
- Control media (play/pause, volume)
- Lock screen, sleep
- Run shell commands (whitelisted)
- Open URLs / files / folders
- Window management
"""

import os
import sys
import time
import json
import subprocess
import platform
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ACTIONS_LOG = DATA_DIR / "system_actions.jsonl"
SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


def _log(action: str, details: Dict[str, Any], success: bool, error: str = ""):
    try:
        entry = {
            "ts": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "success": success,
            "error": error,
        }
        with open(ACTIONS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── App registry ────────────────────────────────────────────────────────────

WINDOWS_APP_PATHS = {
    "chrome": ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
               "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"],
    "edge": ["C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"],
    "firefox": ["C:\\Program Files\\Mozilla Firefox\\firefox.exe"],
    "vscode": ["C:\\Users\\{user}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
               "C:\\Program Files\\Microsoft VS Code\\Code.exe"],
    "spotify": ["C:\\Users\\{user}\\AppData\\Roaming\\Spotify\\Spotify.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "terminal": ["wt.exe", "cmd.exe"],
    "powershell": ["powershell.exe"],
    "explorer": ["explorer.exe"],
    "discord": ["C:\\Users\\{user}\\AppData\\Local\\Discord\\app-1.0.9013\\Discord.exe"],
    "telegram": ["C:\\Users\\{user}\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe"],
    "obsidian": ["C:\\Users\\{user}\\AppData\\Local\\Obsidian\\Obsidian.exe"],
    "settings": ["ms-settings:"],
    "task manager": ["taskmgr.exe"],
}


def open_app(name: str) -> Dict[str, Any]:
    """Open an application by friendly name."""
    name_lower = name.lower().strip()

    if not IS_WINDOWS:
        return _open_app_unix(name_lower)

    # Look up in registry
    paths = WINDOWS_APP_PATHS.get(name_lower)
    if paths:
        user = os.environ.get("USERNAME", "")
        for path in paths:
            resolved = path.replace("{user}", user)
            try:
                if resolved.startswith("ms-settings:"):
                    subprocess.Popen(["explorer.exe", resolved])
                elif Path(resolved).exists() or "\\" not in resolved:
                    subprocess.Popen([resolved])
                else:
                    continue
                _log("open_app", {"name": name, "path": resolved}, True)
                return {"success": True, "app": name, "path": resolved}
            except Exception as e:
                continue

    # Fallback: try `start` command
    try:
        subprocess.run(["cmd", "/c", "start", "", name_lower], shell=False, timeout=5)
        _log("open_app", {"name": name, "method": "start"}, True)
        return {"success": True, "app": name, "method": "start"}
    except Exception as e:
        _log("open_app", {"name": name}, False, str(e))
        return {"success": False, "error": str(e)}


def _open_app_unix(name: str) -> Dict[str, Any]:
    try:
        if IS_MAC:
            subprocess.Popen(["open", "-a", name])
        else:
            subprocess.Popen([name])
        _log("open_app", {"name": name}, True)
        return {"success": True, "app": name}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── URL / File ──────────────────────────────────────────────────────────────

def open_url(url: str) -> Dict[str, Any]:
    """Open a URL in default browser."""
    try:
        import webbrowser
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        _log("open_url", {"url": url}, True)
        return {"success": True, "url": url}
    except Exception as e:
        _log("open_url", {"url": url}, False, str(e))
        return {"success": False, "error": str(e)}


def open_file(path: str) -> Dict[str, Any]:
    """Open a file with the default application."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"success": False, "error": f"File not found: {p}"}
        if IS_WINDOWS:
            os.startfile(str(p))
        elif IS_MAC:
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])
        _log("open_file", {"path": str(p)}, True)
        return {"success": True, "path": str(p)}
    except Exception as e:
        _log("open_file", {"path": path}, False, str(e))
        return {"success": False, "error": str(e)}


def open_folder(path: str) -> Dict[str, Any]:
    """Open a folder in file explorer."""
    return open_file(path)


# ── Screenshot ───────────────────────────────────────────────────────────────

def take_screenshot(region: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
    """
    Capture screen. Returns path to PNG.
    region: (x, y, width, height) or None for full screen.
    """
    try:
        from PIL import ImageGrab
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = SCREENSHOT_DIR / f"screen_{timestamp}.png"

        if region:
            bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
            img = ImageGrab.grab(bbox=bbox)
        else:
            img = ImageGrab.grab()

        img.save(out_path)
        _log("screenshot", {"path": str(out_path), "region": region}, True)
        return {"success": True, "path": str(out_path), "size": img.size}
    except ImportError:
        return {"success": False, "error": "Pillow not installed. pip install Pillow"}
    except Exception as e:
        _log("screenshot", {}, False, str(e))
        return {"success": False, "error": str(e)}


# ── Type / Click ─────────────────────────────────────────────────────────────

def type_text(text: str, interval: float = 0.02) -> Dict[str, Any]:
    """Type text into the currently focused window."""
    try:
        import pyautogui
        pyautogui.write(text, interval=interval)
        _log("type_text", {"length": len(text)}, True)
        return {"success": True, "typed_chars": len(text)}
    except ImportError:
        return {"success": False, "error": "pyautogui not installed. pip install pyautogui"}
    except Exception as e:
        _log("type_text", {}, False, str(e))
        return {"success": False, "error": str(e)}


def press_key(key: str) -> Dict[str, Any]:
    """Press a single key or hotkey combo (e.g. 'ctrl+s', 'enter')."""
    try:
        import pyautogui
        if "+" in key:
            keys = [k.strip() for k in key.split("+")]
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        _log("press_key", {"key": key}, True)
        return {"success": True, "key": key}
    except ImportError:
        return {"success": False, "error": "pyautogui not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> Dict[str, Any]:
    """Click at coordinates (or current position if None)."""
    try:
        import pyautogui
        pyautogui.click(x=x, y=y, button=button)
        _log("click", {"x": x, "y": y, "button": button}, True)
        return {"success": True}
    except ImportError:
        return {"success": False, "error": "pyautogui not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Media control ────────────────────────────────────────────────────────────

def media_control(action: str) -> Dict[str, Any]:
    """play_pause / next / prev / volume_up / volume_down / mute"""
    if not IS_WINDOWS:
        return {"success": False, "error": "Media control currently Windows-only"}

    actions = {
        "play_pause": "playpause",
        "play": "playpause",
        "pause": "playpause",
        "next": "nexttrack",
        "prev": "prevtrack",
        "previous": "prevtrack",
        "volume_up": "volumeup",
        "volume_down": "volumedown",
        "mute": "volumemute",
    }
    key = actions.get(action.lower())
    if not key:
        return {"success": False, "error": f"Unknown media action: {action}"}

    try:
        import pyautogui
        pyautogui.press(key)
        _log("media", {"action": action, "key": key}, True)
        return {"success": True, "action": action}
    except ImportError:
        # Fallback: use Win32 API directly
        try:
            import ctypes
            VK_MEDIA = {
                "playpause": 0xB3, "nexttrack": 0xB0, "prevtrack": 0xB1,
                "volumeup": 0xAF, "volumedown": 0xAE, "volumemute": 0xAD,
            }
            vk = VK_MEDIA[key]
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
            _log("media", {"action": action, "method": "win32"}, True)
            return {"success": True, "action": action}
        except Exception as e:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Power ────────────────────────────────────────────────────────────────────

def lock_screen() -> Dict[str, Any]:
    try:
        if IS_WINDOWS:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        elif IS_MAC:
            subprocess.run(["pmset", "displaysleepnow"])
        else:
            subprocess.run(["xdg-screensaver", "lock"])
        _log("lock_screen", {}, True)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Window management ───────────────────────────────────────────────────────

def list_open_windows() -> Dict[str, Any]:
    """List visible windows with titles."""
    if not IS_WINDOWS:
        return {"success": False, "error": "Currently Windows-only"}

    try:
        import ctypes
        from ctypes import wintypes

        EnumWindows = ctypes.windll.user32.EnumWindows
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible

        windows = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        def enum_callback(hwnd, lParam):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buf, length + 1)
                    if buf.value.strip():
                        windows.append({"hwnd": hwnd, "title": buf.value})
            return True

        EnumWindows(enum_callback, 0)
        return {"success": True, "windows": windows[:30], "count": len(windows)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def focus_window(title_substring: str) -> Dict[str, Any]:
    """Bring a window matching title to front."""
    if not IS_WINDOWS:
        return {"success": False, "error": "Currently Windows-only"}
    try:
        import ctypes
        result = list_open_windows()
        if not result.get("success"):
            return result
        for w in result["windows"]:
            if title_substring.lower() in w["title"].lower():
                ctypes.windll.user32.SetForegroundWindow(w["hwnd"])
                ctypes.windll.user32.ShowWindow(w["hwnd"], 9)  # SW_RESTORE
                _log("focus_window", {"title": w["title"]}, True)
                return {"success": True, "title": w["title"]}
        return {"success": False, "error": f"No window matching '{title_substring}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Shell commands (whitelisted) ─────────────────────────────────────────────

SAFE_COMMANDS = {
    "git", "python", "node", "npm", "yarn", "pip", "dir", "ls", "echo",
    "where", "which", "whoami", "hostname", "ipconfig", "ifconfig",
    "ping", "tracert", "tasklist", "ps", "uptime", "date", "time",
}


def run_shell(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Run a shell command if it starts with a whitelisted root.
    Returns stdout, stderr, returncode.
    """
    parts = command.strip().split()
    if not parts:
        return {"success": False, "error": "Empty command"}

    root = parts[0].lower().split("/")[-1].split("\\")[-1].split(".")[0]
    if root not in SAFE_COMMANDS:
        return {"success": False, "error": f"Command '{root}' not in whitelist. Allowed: {', '.join(sorted(SAFE_COMMANDS))}"}

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout
        )
        _log("run_shell", {"command": command, "rc": result.returncode}, result.returncode == 0)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-3000:],
            "stderr": result.stderr[-1000:],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Natural language → action ──────────────────────────────────────────────

ACTION_PATTERNS = [
    # Open something
    (r"\bopen\s+(.+?)(?:\s*$|\s+(?:in|with|please))", "open"),
    (r"\blaunch\s+(.+?)(?:\s*$|\s+(?:please))", "open"),
    (r"\bstart\s+(.+?)(?:\s*$|\s+(?:please))", "open"),
    # Search the web
    (r"\b(?:google|search|look up)\s+(.+)", "search"),
    # Media
    (r"\b(?:play|resume|pause|stop)\b\s*(?:music|song|video|spotify)?", "media_play_pause"),
    (r"\b(?:next|skip)\s*(?:track|song)?\b", "media_next"),
    (r"\b(?:previous|prev|last)\s*(?:track|song)\b", "media_prev"),
    (r"\bvolume\s+up\b|\bturn\s+(?:up|louder)\b", "media_vol_up"),
    (r"\bvolume\s+down\b|\bturn\s+(?:down|quieter)\b", "media_vol_down"),
    (r"\bmute\b|\bsilence\b", "media_mute"),
    # Screenshot
    (r"\b(?:take\s+a?\s*)?screenshot\b|\bcapture\s+(?:the\s+)?screen", "screenshot"),
    # Lock
    (r"\block\s+(?:my\s+)?(?:screen|computer|pc)\b", "lock"),
    # Type
    (r"\btype\s+['\"](.+?)['\"]", "type"),
    # Focus window
    (r"\b(?:focus|switch to|bring up)\s+(?:the\s+)?(.+?)\s+window", "focus"),
]


def parse_action(user_input: str) -> Optional[Dict[str, Any]]:
    """Parse natural language into an action dict, or None if no action detected."""
    text = user_input.lower().strip()
    for pattern, action in ACTION_PATTERNS:
        m = re.search(pattern, text)
        if m:
            arg = m.group(1).strip() if m.groups() else None
            return {"action": action, "arg": arg, "raw": user_input}
    return None


def execute_action(action_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a parsed action."""
    action = action_data.get("action", "")
    arg = action_data.get("arg")

    if action == "open":
        # Decide if it's a URL, file, or app
        if arg.startswith(("http://", "https://", "www.")) or "." in arg.split()[0]:
            if "." in arg and "/" in arg or arg.startswith("www."):
                return open_url(arg)
        # Check if it's a file path
        if os.sep in arg or arg.startswith("/") or (len(arg) > 1 and arg[1] == ":"):
            return open_file(arg)
        # Otherwise, treat as app name
        return open_app(arg)

    if action == "search":
        return open_url(f"https://www.google.com/search?q={arg.replace(' ', '+')}")

    if action.startswith("media_"):
        media_map = {
            "media_play_pause": "play_pause",
            "media_next": "next",
            "media_prev": "prev",
            "media_vol_up": "volume_up",
            "media_vol_down": "volume_down",
            "media_mute": "mute",
        }
        return media_control(media_map[action])

    if action == "screenshot":
        return take_screenshot()

    if action == "lock":
        return lock_screen()

    if action == "type" and arg:
        return type_text(arg)

    if action == "focus" and arg:
        return focus_window(arg)

    return {"success": False, "error": f"Unknown action: {action}"}


def handle_user_command(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Top-level: try to detect and execute a system action.
    Returns result dict if action executed, None if no action detected.
    """
    parsed = parse_action(user_input)
    if not parsed:
        return None

    result = execute_action(parsed)
    result["parsed"] = parsed
    return result


# ── Clipboard ────────────────────────────────────────────────────────────────

def get_clipboard() -> Dict[str, Any]:
    """Read clipboard content."""
    try:
        import pyperclip
        text = pyperclip.paste()
        _log("clipboard_read", {"length": len(text)}, True)
        return {"success": True, "text": text, "length": len(text)}
    except ImportError:
        # Try ctypes Win32 fallback
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            CF_UNICODETEXT = 13
            if not user32.OpenClipboard(0):
                return {"success": False, "error": "Could not open clipboard"}
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                user32.CloseClipboard()
                return {"success": True, "text": "", "length": 0}
            data = kernel32.GlobalLock(handle)
            text = ctypes.wchar_p(data).value or ""
            kernel32.GlobalUnlock(handle)
            user32.CloseClipboard()
            return {"success": True, "text": text, "length": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_clipboard(text: str) -> Dict[str, Any]:
    """Write text to clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        _log("clipboard_write", {"length": len(text)}, True)
        return {"success": True, "length": len(text)}
    except ImportError:
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            GMEM_MOVEABLE = 0x0002
            CF_UNICODETEXT = 13
            size = (len(text) + 1) * 2
            hGlobal = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            ptr = kernel32.GlobalLock(hGlobal)
            ctypes.memmove(ptr, text.encode('utf-16le'), len(text) * 2)
            ctypes.c_ushort.from_address(ptr + len(text) * 2).value = 0
            kernel32.GlobalUnlock(hGlobal)
            user32.OpenClipboard(0)
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_UNICODETEXT, hGlobal)
            user32.CloseClipboard()
            return {"success": True, "length": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Active Window ────────────────────────────────────────────────────────────

def get_active_window() -> Dict[str, Any]:
    """Get the currently focused window title and process."""
    if not IS_WINDOWS:
        return {"success": False, "error": "Currently Windows-only"}
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)

        # Get process name
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        proc_handle = kernel32.OpenProcess(0x0410, False, pid.value)
        proc_name = "unknown"
        if proc_handle:
            name_buf = ctypes.create_unicode_buffer(260)
            psapi = ctypes.windll.psapi
            psapi.GetModuleBaseNameW(proc_handle, None, name_buf, 260)
            proc_name = name_buf.value
            kernel32.CloseHandle(proc_handle)

        return {
            "success": True,
            "title": buf.value,
            "process": proc_name,
            "hwnd": hwnd,
            "pid": pid.value,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Process Management ───────────────────────────────────────────────────────

def list_processes(name_filter: str = None, top_n: int = 20) -> Dict[str, Any]:
    """List running processes, optionally filtered by name."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = p.info
                if name_filter and name_filter.lower() not in info['name'].lower():
                    continue
                procs.append(info)
            except Exception:
                pass
        # Sort by CPU
        procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        return {"success": True, "processes": procs[:top_n], "count": len(procs)}
    except ImportError:
        return {"success": False, "error": "psutil not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def kill_process(name: str = None, pid: int = None) -> Dict[str, Any]:
    """Kill a process by name or PID."""
    try:
        import psutil
        if pid:
            p = psutil.Process(pid)
            p.terminate()
            return {"success": True, "killed": f"PID {pid}"}
        elif name:
            killed = []
            for p in psutil.process_iter(['pid', 'name']):
                if name.lower() in p.info['name'].lower():
                    psutil.Process(p.info['pid']).terminate()
                    killed.append(p.info['name'])
            return {"success": True, "killed": killed}
        return {"success": False, "error": "Provide name or pid"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── File Search ───────────────────────────────────────────────────────────────

def search_files(query: str, root: str = None, max_results: int = 20) -> Dict[str, Any]:
    """Search for files by name substring. Defaults to user's home."""
    if root is None:
        root = str(Path.home())
    results = []
    try:
        root_path = Path(root)
        for p in root_path.rglob("*"):
            if p.is_file() and query.lower() in p.name.lower():
                results.append({
                    "path": str(p),
                    "name": p.name,
                    "size": p.stat().st_size,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                })
                if len(results) >= max_results:
                    break
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── System Info ──────────────────────────────────────────────────────────────

def get_system_info() -> Dict[str, Any]:
    """Snapshot of system health."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu = psutil.cpu_percent(interval=0.5)
        boot = datetime.fromtimestamp(psutil.boot_time()).isoformat()
        return {
            "success": True,
            "cpu_percent": cpu,
            "memory": {
                "total_gb": round(mem.total / (1024**3), 1),
                "used_gb": round(mem.used / (1024**3), 1),
                "percent": mem.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 1),
                "used_gb": round(disk.used / (1024**3), 1),
                "percent": round(disk.used / disk.total * 100, 1),
            },
            "uptime_since": boot,
        }
    except ImportError:
        return {"success": False, "error": "psutil not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Recent action log ────────────────────────────────────────────────────────

def get_recent_actions(n: int = 10) -> List[Dict]:
    try:
        if not ACTIONS_LOG.exists():
            return []
        lines = ACTIONS_LOG.read_text().strip().split("\n")
        return [json.loads(l) for l in lines[-n:] if l]
    except Exception:
        return []
