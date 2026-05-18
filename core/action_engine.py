"""
LOVE Action Engine — Wave 9 Omnimodal Computer Use
Allows LOVE to physically interact with Karthi's computer autonomously.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pyautogui
import pygetwindow as gw

# Safety settings: PyAutoGUI fail-safe triggers if mouse moves to a corner.
pyautogui.FAILSAFE = True
# Small pause after every action so Karthi can interrupt
pyautogui.PAUSE = 0.5 

class ActionEngine:
    """Provides computer use capabilities (Computer-Use style)."""
    
    def __init__(self):
        self.enabled = True
        
    def _ensure_active(self):
        if not self.enabled:
            raise RuntimeError("Action Engine is currently disabled.")
            
    def click(self, x: int, y: int, right_click: bool = False):
        """Click at specific coordinates on screen."""
        self._ensure_active()
        print(f"[ActionEngine] 🖱️ Clicking at ({x}, {y})")
        if right_click:
            pyautogui.rightClick(x, y)
        else:
            pyautogui.click(x, y)
            
    def type_text(self, text: str, enter: bool = True):
        """Type text as if using the keyboard."""
        self._ensure_active()
        print(f"[ActionEngine] ⌨️ Typing: '{text}'")
        pyautogui.write(text, interval=0.01)
        if enter:
            pyautogui.press("enter")
            
    def press_key(self, key_combo: str):
        """Press a key combination (e.g., 'ctrl+c', 'win+d')."""
        self._ensure_active()
        print(f"[ActionEngine] ⌨️ Pressing combo: {key_combo}")
        keys = [k.strip() for k in key_combo.split("+")]
        pyautogui.hotkey(*keys)
        
    def get_windows(self) -> list:
        """List all open window titles."""
        windows = gw.getAllTitles()
        return [w for w in windows if w.strip()]
        
    def focus_window(self, title_substring: str) -> bool:
        """Bring a specific window to the foreground."""
        self._ensure_active()
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
