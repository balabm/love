"""
LOVE Action Engine — Wave 9 Omnimodal Computer Use
Allows LOVE to physically interact with Karthi's computer autonomously.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import subprocess
import importlib

PYAUTOGUI_AVAILABLE = False
GW_AVAILABLE = False

try:
    import pyautogui
    # Safety settings: PyAutoGUI fail-safe triggers if mouse moves to a corner.
    pyautogui.FAILSAFE = True
    # Small pause after every action so Karthi can interrupt
    pyautogui.PAUSE = 0.5 
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    # Try to auto-install optional package
    def _try_install_and_import(pkg_name, import_name=None):
        import_name = import_name or pkg_name
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
            mod = importlib.import_module(import_name)
            return mod
        except Exception as e:
            try:
                from core.self_healing import _log_healing
                _log_healing({
                    "error_type": "auto_install_failed",
                    "package": pkg_name,
                    "error": str(e)
                })
            except Exception:
                pass
            return None

    mod = _try_install_and_import("pyautogui")
    if mod is not None:
        pyautogui = mod
        try:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.5
            PYAUTOGUI_AVAILABLE = True
        except Exception:
            PYAUTOGUI_AVAILABLE = True
    else:
        print("[ActionEngine] pyautogui not installed — computer control disabled")

try:
    import pygetwindow as gw
    GW_AVAILABLE = True
except ImportError:
    mod = None
    try:
        mod = _try_install_and_import("pygetwindow", "pygetwindow")
    except Exception:
        mod = None
    if mod is not None:
        gw = mod
        GW_AVAILABLE = True
    else:
        print("[ActionEngine] pygetwindow not installed — window control disabled")

class ActionEngine:
    """Provides computer use capabilities (Computer-Use style)."""
    
    def __init__(self):
        self.enabled = True
        
    def _ensure_active(self):
        if not self.enabled:
            raise RuntimeError("Action Engine is currently disabled.")
        if not PYAUTOGUI_AVAILABLE:
            raise RuntimeError("Action Engine is disabled because pyautogui is not installed.")
            
    def click(self, x: int, y: int, right_click: bool = False):
        """Click at specific coordinates on screen."""
        self._ensure_active()
        # SAFETY CHECK: Require user approval for clicking
        approval_required = os.getenv("LOVE_AUTO_COMPUTER_CONTROL", "").lower() in {"1", "true", "yes"}
        if not approval_required:
            print(f"[ActionEngine] ⚠️ Click BLOCKED - user approval required.")
            print(f"[ActionEngine] Set LOVE_AUTO_COMPUTER_CONTROL=1 to enable (not recommended)")
            return
        print(f"[ActionEngine] 🖱️ Clicking at ({x}, {y})")
        if right_click:
            pyautogui.rightClick(x, y)
        else:
            pyautogui.click(x, y)
            
    def type_text(self, text: str, enter: bool = True):
        """Type text as if using the keyboard."""
        self._ensure_active()
        # SAFETY CHECK: Require user approval for typing
        approval_required = os.getenv("LOVE_AUTO_COMPUTER_CONTROL", "").lower() in {"1", "true", "yes"}
        if not approval_required:
            print(f"[ActionEngine] ⚠️ Typing BLOCKED - user approval required.")
            print(f"[ActionEngine] Set LOVE_AUTO_COMPUTER_CONTROL=1 to enable (not recommended)")
            return
        print(f"[ActionEngine] ⌨️ Typing: '{text}'")
        pyautogui.write(text, interval=0.01)
        if enter:
            pyautogui.press("enter")
            
    def press_key(self, key_combo: str):
        """Press a key combination (e.g., 'ctrl+c', 'win+d')."""
        self._ensure_active()
        # SAFETY CHECK: Require user approval for key presses
        approval_required = os.getenv("LOVE_AUTO_COMPUTER_CONTROL", "").lower() in {"1", "true", "yes"}
        if not approval_required:
            print(f"[ActionEngine] ⚠️ Key press BLOCKED - user approval required.")
            print(f"[ActionEngine] Set LOVE_AUTO_COMPUTER_CONTROL=1 to enable (not recommended)")
            return
        print(f"[ActionEngine] ⌨️ Pressing combo: {key_combo}")
        keys = [k.strip() for k in key_combo.split("+")]
        pyautogui.hotkey(*keys)
        
    def get_windows(self) -> list:
        """List all open window titles."""
        if not GW_AVAILABLE:
            print("[ActionEngine] pygetwindow not installed, cannot list windows.")
            return []
        windows = gw.getAllTitles()
        return [w for w in windows if w.strip()]
        
    def focus_window(self, title_substring: str) -> bool:
        """Bring a specific window to the foreground."""
        self._ensure_active()
        if not GW_AVAILABLE:
            print("[ActionEngine] pygetwindow not installed, cannot focus window.")
            return False
        windows = gw.getWindowsWithTitle(title_substring)
        if windows:
            win = windows[0]
            try:
                if win.isMinimized:
                    win.restore()
                win.activate()
                print(f"[ActionEngine] 🪟 Focused window: {win.title}")
                return True
            except Exception as e:
                print(f"[ActionEngine] Failed to focus window: {e}")
                return False
        return False
        
    def execute_action_plan(self, plan: list) -> Dict[str, Any]:
        """
        Execute a sequence of actions.
        plan is a list of dicts: {"action": "type_text", "args": {"text": "hello"}}
        """
        # SAFETY CHECK: Require user approval for any computer control
        approval_required = os.getenv("LOVE_AUTO_COMPUTER_CONTROL", "").lower() in {"1", "true", "yes"}
        if not approval_required:
            print(f"[ActionEngine] ⚠️ Computer control BLOCKED - user approval required.")
            print(f"[ActionEngine] Set LOVE_AUTO_COMPUTER_CONTROL=1 to enable (not recommended)")
            return {"success": False, "error": "Computer control disabled - user approval required", "blocked_plan": plan}
        results = []
        for step in plan:
            action = step.get("action")
            args = step.get("args", {})
            try:
                if action == "click":
                    self.click(args.get("x", 0), args.get("y", 0), args.get("right_click", False))
                elif action == "type":
                    self.type_text(args.get("text", ""), args.get("enter", True))
                elif action == "hotkey":
                    self.press_key(args.get("combo", ""))
                elif action == "focus":
                    success = self.focus_window(args.get("title", ""))
                    if not success:
                        results.append({"step": action, "status": "failed", "reason": "window not found"})
                        break
                elif action == "wait":
                    time.sleep(args.get("seconds", 1))
                
                results.append({"step": action, "status": "success"})
            except Exception as e:
                results.append({"step": action, "status": "error", "error": str(e)})
                break
                
        return {"status": "completed" if all(r["status"] == "success" for r in results) else "incomplete", "results": results}

_engine = None

def get_action_engine() -> ActionEngine:
    global _engine
    if _engine is None:
        _engine = ActionEngine()
    return _engine
