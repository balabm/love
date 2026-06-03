"""
LOVE On-Demand Model Manager

LOVE doesn't come with every model pre-installed.
Instead, it detects when a task needs a specialized capability,
checks if it's available, and either:
  1. Uses it directly (cached)
  2. Downloads/installs it on the fly (with size warning)
  3. Falls back to an Ollama model
  4. Tells the user what's needed

Capabilities: OCR, sentiment analysis, image captioning, object detection,
summarization, translation, speech recognition.
"""

import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODEL_STATUS_FILE = DATA_DIR / "model_status.json"

_lock = threading.Lock()

# ── Capability registry ─────────────────────────────────────────────────────

@dataclass
class Capability:
    name: str
    description: str
    pip_packages: List[str]
    model_size_mb: float
    check_fn: Callable[[], bool]
    run_fn: Callable
    ollama_fallback: Optional[str] = None  # e.g. "llava" for vision


def _check_easyocr() -> bool:
    try:
        import easyocr
        return True
    except ImportError:
        return False


def _check_transformers() -> bool:
    try:
        import transformers
        import torch
        return True
    except ImportError:
        return False


def _check_ultralytics() -> bool:
    try:
        import ultralytics
        return True
    except ImportError:
        return False


def _check_ollama_model(model_name: str) -> bool:
    """Check if an Ollama model is pulled locally."""
    try:
        import requests
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return any(m.get("name", "").startswith(model_name) for m in models)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.on_demand_models")
    return False


# ── Lazy imports for run functions ────────────────────────────────────────────

def _run_ocr(image_path: str, lang: List[str] = None) -> Dict[str, Any]:
    import easyocr
    reader = easyocr.Reader(lang or ["en"], gpu=False, verbose=False)
    results = reader.readtext(image_path, detail=1)
    lines = [r[1] for r in results]
    return {
        "text": "\n".join(lines),
        "lines": lines,
        "bbox_count": len(results),
        "model": "easyocr",
    }


def _run_sentiment(text: str) -> Dict[str, Any]:
    from transformers import pipeline
    pipe = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    result = pipe(text[:512])[0]
    return {
        "label": result["label"],
        "score": result["score"],
        "model": "distilbert-sst2",
    }


def _run_summarize(text: str, max_length: int = 150) -> Dict[str, Any]:
    from transformers import pipeline
    pipe = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    result = pipe(text[:1024], max_length=max_length, min_length=30, do_sample=False)[0]
    return {
        "summary": result["summary_text"],
        "model": "distilbart-cnn",
    }


def _run_object_detect(image_path: str) -> Dict[str, Any]:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt", verbose=False)
    results = model(image_path, verbose=False)
    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": r.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()[0] if hasattr(box.xyxy, "tolist") else list(box.xyxy[0]),
            })
    return {
        "detections": detections,
        "count": len(detections),
        "model": "yolov8n",
    }


def _run_ollama_vision(image_path: str, prompt: str = "Describe this image.") -> Dict[str, Any]:
    import base64
    import requests
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    resp = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={"model": "llava", "prompt": prompt, "images": [b64], "stream": False},
        timeout=60
    )
    resp.raise_for_status()
    return {"description": resp.json().get("response", ""), "model": "llava-ollama"}


# ── Registry ─────────────────────────────────────────────────────────────────

CAPABILITIES: Dict[str, Capability] = {
    "ocr": Capability(
        name="ocr",
        description="Read text from images (screenshots, photos, documents)",
        pip_packages=["easyocr"],
        model_size_mb=80,
        check_fn=_check_easyocr,
        run_fn=_run_ocr,
        ollama_fallback=None,
    ),
    "sentiment": Capability(
        name="sentiment",
        description="Analyze emotional tone of text",
        pip_packages=["transformers", "torch", "sentencepiece"],
        model_size_mb=250,
        check_fn=_check_transformers,
        run_fn=_run_sentiment,
        ollama_fallback=None,
    ),
    "summarize": Capability(
        name="summarize",
        description="Summarize long text into key points",
        pip_packages=["transformers", "torch"],
        model_size_mb=1200,
        check_fn=_check_transformers,
        run_fn=_run_summarize,
        ollama_fallback=None,
    ),
    "object_detect": Capability(
        name="object_detect",
        description="Detect objects in images (people, cars, etc.)",
        pip_packages=["ultralytics"],
        model_size_mb=6,
        check_fn=_check_ultralytics,
        run_fn=_run_object_detect,
        ollama_fallback=None,
    ),
    "image_caption": Capability(
        name="image_caption",
        description="Describe what's in an image",
        pip_packages=[],
        model_size_mb=0,
        check_fn=lambda: _check_ollama_model("llava"),
        run_fn=_run_ollama_vision,
        ollama_fallback="llava",
    ),
}


# ── Status tracking ───────────────────────────────────────────────────────────

def _load_status() -> Dict[str, Any]:
    if MODEL_STATUS_FILE.exists():
        try:
            return json.loads(MODEL_STATUS_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.on_demand_models")
    return {}


def _save_status(status: Dict[str, Any]):
    try:
        MODEL_STATUS_FILE.write_text(json.dumps(status, indent=2))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.on_demand_models")


def check_capability(name: str) -> Dict[str, Any]:
    """Check if a capability is available right now."""
    cap = CAPABILITIES.get(name)
    if not cap:
        return {"available": False, "error": f"Unknown capability: {name}"}

    available = cap.check_fn()
    status = _load_status()
    status[name] = {"available": available, "last_checked": str(datetime.now().isoformat())}
    _save_status(status)

    return {
        "name": name,
        "available": available,
        "description": cap.description,
        "pip_packages": cap.pip_packages,
        "model_size_mb": cap.model_size_mb,
        "ollama_fallback": cap.ollama_fallback,
    }


def install_capability(name: str) -> Dict[str, Any]:
    """Try to pip install the required packages for a capability."""
    cap = CAPABILITIES.get(name)
    if not cap:
        return {"success": False, "error": f"Unknown capability: {name}"}

    if not cap.pip_packages:
        return {"success": True, "message": "No packages needed"}

    results = []
    for pkg in cap.pip_packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True, text=True, timeout=300
            )
            results.append({
                "package": pkg,
                "success": result.returncode == 0,
                "output": result.stdout[-500:] if result.stdout else "",
                "error": result.stderr[-500:] if result.stderr else "",
            })
        except Exception as e:
            results.append({"package": pkg, "success": False, "error": str(e)})

    all_ok = all(r["success"] for r in results)
    if all_ok:
        status = _load_status()
        status[name] = {"available": True, "installed_at": str(datetime.now().isoformat())}
        _save_status(status)

    return {
        "success": all_ok,
        "results": results,
        "size_mb": cap.model_size_mb,
    }


def run_capability(name: str, **kwargs) -> Dict[str, Any]:
    """
    Run a capability. If not available, tries to install or use fallback.
    Returns result dict with 'success' key.
    """
    cap = CAPABILITIES.get(name)
    if not cap:
        return {"success": False, "error": f"Unknown capability: {name}"}

    # Check availability
    if not cap.check_fn():
        # Try installing
        if cap.pip_packages:
            install_result = install_capability(name)
            if not install_result["success"]:
                return {"success": False, "error": f"Failed to install {name}", "install_log": install_result}
        else:
            # No pip packages, probably needs Ollama model pull
            if cap.ollama_fallback:
                return {
                    "success": False,
                    "error": f"Ollama model '{cap.ollama_fallback}' not pulled. Run: ollama pull {cap.ollama_fallback}",
                }
            return {"success": False, "error": f"Capability {name} not available and no install path"}

    # Run it
    try:
        result = cap.run_fn(**kwargs)
        result["success"] = True
        result["capability"] = name
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "capability": name}


def list_capabilities() -> List[Dict[str, Any]]:
    """List all capabilities and their current availability."""
    return [check_capability(name) for name in CAPABILITIES]


def auto_detect_needed_capability(user_input: str, has_image: bool = False) -> Optional[str]:
    """
    Detect what capability a user query might need.
    Returns capability name or None.
    """
    text = user_input.lower()

    if has_image:
        if any(w in text for w in ["read", "text", "ocr", "scan", "extract", "what does it say"]):
            return "ocr"
        if any(w in text for w in ["what is in", "describe", "what do you see", "objects", "people", "detect"]):
            return "object_detect"
        return "image_caption"

    if any(w in text for w in ["sentiment", "tone", "mood", "emotion", "feeling", "attitude"]):
        return "sentiment"
    if any(w in text for w in ["summarize", "tl;dr", "tldr", "short version", "key points", "summary"]):
        return "summarize"

    return None


# Need datetime for status tracking
from datetime import datetime
from core.execution_guard import log_error
