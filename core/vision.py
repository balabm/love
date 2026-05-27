"""
LOVE Vision Engine

LOVE can see. Screenshots, photos, documents — she reads them, understands them,
detects objects, and reasons about what she sees.

Built on the on-demand model manager — pulls capabilities as needed.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VISION_LOG = DATA_DIR / "vision_log.jsonl"


def _log_vision(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        import json
        with open(VISION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def read_image_text(image_path: str) -> Dict[str, Any]:
    """
    OCR: Extract text from an image file.
    Falls back to asking user to install easyocr if not available.
    """
    path = Path(image_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {image_path}"}

    try:
        from core.on_demand_models import run_capability
        result = run_capability("ocr", image_path=str(path))
        _log_vision({"action": "ocr", "path": str(path), "result": result})
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def describe_image(image_path: str, detail_level: str = "normal") -> Dict[str, Any]:
    """
    Describe what's in an image using a vision model.
    Tries Ollama llava first, falls back to object detection summary.
    """
    path = Path(image_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {image_path}"}

    # Try Ollama vision model
    try:
        import requests
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        prompt = "Describe what you see in this image in a few sentences."
        if detail_level == "detailed":
            prompt = "Describe this image in detail. What objects, people, text, and scene elements do you see?"
        elif detail_level == "concise":
            prompt = "One sentence description of this image."

        resp = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "llava", "prompt": prompt, "images": [b64], "stream": False},
            timeout=60
        )
        if resp.status_code == 200:
            desc = resp.json().get("response", "")
            result = {"success": True, "description": desc.strip(), "model": "llava", "detail": detail_level}
            _log_vision({"action": "describe", "path": str(path), "result": result})
            return result
    except Exception:
        pass

    # Fallback: object detection summary
    try:
        from core.on_demand_models import run_capability
        detect_result = run_capability("object_detect", image_path=str(path))
        if detect_result.get("success"):
            objects = [f"{d['class']} ({d['confidence']:.0%})" for d in detect_result.get("detections", [])]
            desc = "I see: " + ", ".join(objects[:8]) if objects else "I couldn't identify anything specific."
            result = {
                "success": True,
                "description": desc,
                "model": "yolov8n-fallback",
                "detections": detect_result.get("detections", []),
                "note": "Used object detection fallback — vision model not available.",
            }
            _log_vision({"action": "describe", "path": str(path), "result": result})
            return result
    except Exception:
        pass

    return {"success": False, "error": "No vision model available. Try: ollama pull llava"}


def analyze_screenshot(image_path: str, user_question: str = "") -> Dict[str, Any]:
    """
    Smart screenshot analysis — OCR + description + reasoning.
    Optimized for desktop/mobile screenshots.
    """
    path = Path(image_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {image_path}"}

    # Step 1: OCR
    ocr_result = read_image_text(str(path))
    text = ocr_result.get("text", "") if ocr_result.get("success") else ""

    # Step 2: Description
    desc_result = describe_image(str(path), detail_level="detailed")
    description = desc_result.get("description", "") if desc_result.get("success") else ""

    # Step 3: If user asked a question, use LLM to answer based on both
    answer = ""
    if user_question:
        try:
            from core.llm import get_reasoning_llm
            llm = get_reasoning_llm(temperature=0.3, max_tokens=300)
            context = f"""I'm looking at a screenshot.

Visual description: {description}
Text extracted from image: {text}

The user asks: {user_question}
Answer based on what you see. Be specific and concise."""
            answer = llm.invoke(context).strip()
        except Exception:
            pass

    result = {
        "success": True,
        "text": text,
        "description": description,
        "answer": answer,
        "has_text": len(text) > 0,
        "has_visuals": len(description) > 0,
    }
    _log_vision({"action": "screenshot_analysis", "path": str(path), "question": user_question, "result": result})
    return result


def detect_image_objects(image_path: str, confidence: float = 0.5) -> Dict[str, Any]:
    """Object detection with confidence threshold."""
    path = Path(image_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {image_path}"}

    try:
        from core.on_demand_models import run_capability
        result = run_capability("object_detect", image_path=str(path))
        if result.get("success"):
            # Filter by confidence
            detections = [d for d in result.get("detections", []) if d.get("confidence", 0) >= confidence]
            result["detections"] = detections
            result["count"] = len(detections)
        _log_vision({"action": "object_detect", "path": str(path), "result": result})
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def should_process_image(user_input: str) -> bool:
    """Detect if user is asking about an image/screenshot."""
    triggers = [
        "screenshot", "image", "photo", "picture", "this file", "look at",
        "what does this say", "read this", "ocr", "scan", "describe this",
        "what's in this", "what do you see", "analyze this image",
    ]
    text = user_input.lower()
    return any(t in text for t in triggers)


def find_image_in_context(context: Dict[str, Any]) -> Optional[str]:
    """Look for image paths in chat context or recent uploads."""
    # Check explicit image path in context
    if "image_path" in context:
        return context["image_path"]
    # Check recent uploads directory
    upload_dir = DATA_DIR / "uploads"
    if upload_dir.exists():
        files = sorted(upload_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files:
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
                # Only recent (last 5 min)
                import time
                if time.time() - f.stat().st_mtime < 300:
                    return str(f)
    return None


# ── Desktop Context Awareness ───────────────────────────────────────────────

def capture_screenshot(output_path: Optional[str] = None) -> str:
    """Capture full desktop screenshot. Returns path to saved image."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        path = output_path or str(DATA_DIR / "screenshots" / f"desktop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        return path
    except Exception as e:
        _log_vision({"action": "screenshot", "error": str(e)})
        return ""


def get_active_window_info() -> Dict[str, Any]:
    """Get info about the currently focused window (Windows)."""
    info = {"title": "", "process": "", "platform": "unknown"}
    try:
        import platform
        sys_platform = platform.system()
        info["platform"] = sys_platform

        if sys_platform == "Windows":
            import ctypes
            from ctypes import wintypes
            import psutil

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()

            # Get window title
            length = user32.GetWindowTextLengthW(hwnd)
            title_buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, length + 1)
            info["title"] = title_buffer.value

            # Get process name from PID
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                proc = psutil.Process(pid.value)
                info["process"] = proc.name()
                info["exe"] = proc.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        elif sys_platform == "Darwin":
            import subprocess
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                info["process"] = result.stdout.strip()
            # Window title via AppleScript
            script2 = 'tell application "System Events" to get value of attribute "AXTitle" of (get front window of (first application process whose frontmost is true))'
            result2 = subprocess.run(["osascript", "-e", script2], capture_output=True, text=True)
            if result2.returncode == 0:
                info["title"] = result2.stdout.strip()
    except Exception as e:
        info["error"] = str(e)

    return info


def get_desktop_context() -> Dict[str, Any]:
    """Get full desktop context: active window + screenshot text."""
    result = {
        "active_window": get_active_window_info(),
        "timestamp": datetime.now().isoformat(),
        "screenshot_text": "",
        "screenshot_path": "",
    }

    # Capture screenshot
    ss_path = capture_screenshot()
    if ss_path:
        result["screenshot_path"] = ss_path
        # Quick OCR for text on screen
        try:
            ocr = read_image_text(ss_path)
            if ocr.get("success"):
                text = ocr.get("text", "")
                # Only keep meaningful text (not just window chrome)
                lines = [l for l in text.split("\n") if len(l) > 3 and not l.startswith("File Edit View")]
                result["screenshot_text"] = "\n".join(lines[:20])
        except Exception:
            pass

    _log_vision({"action": "desktop_context", "data": result})
    return result


def get_desktop_prompt_context() -> str:
    """Generate a compact context block for the LLM prompt about desktop state."""
    try:
        ctx = get_desktop_context()
        win = ctx.get("active_window", {})
        title = win.get("title", "")
        proc = win.get("process", "")
        text = ctx.get("screenshot_text", "")

        if not title and not proc:
            return ""

        parts = [f"Karthi's currently focused on: {proc} ({title})"]
        if text:
            # Truncate to avoid prompt bloat
            short_text = text[:300].replace("\n", " | ")
            parts.append(f"On screen: {short_text}")

        return "\n".join(parts)
    except Exception:
        return ""
