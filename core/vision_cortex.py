"""
LOVE Vision Cortex — Wave 9 Omnimodal Processing
Allows LOVE to 'see' the user's screen in real-time.
"""

import time
import base64
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import mss
    from PIL import Image
    import io
    _VISION_AVAILABLE = True
except Exception:
    _VISION_AVAILABLE = False  # mss / PIL optional — expected on some environments

from core.settings import get_settings
from core.execution_guard import log_error

SETTINGS = get_settings()
VISION_DATA_DIR = SETTINGS.data_dir / "vision"
VISION_DATA_DIR.mkdir(parents=True, exist_ok=True)
LATEST_FRAME_PATH = VISION_DATA_DIR / "latest_frame.jpg"

class VisionCortex:
    def __init__(self):
        self.enabled = True
        try:
            self.sct = mss.mss()
        except Exception:
            self.sct = None
            
    def take_snapshot(self) -> Optional[str]:
        """Takes a screenshot, saves it, and returns base64 encoded image."""
        if not self.enabled or not self.sct:
            return None
            
        try:
            # Capture primary monitor
            monitor = self.sct.monitors[1]
            sct_img = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Downscale for performance (we don't need 4K for context)
            img.thumbnail((1280, 720))
            
            # Save compressed
            img.save(LATEST_FRAME_PATH, format="JPEG", quality=75)
            
            # Return base64 for LLM usage
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=75)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return img_str
        except Exception as e:
            print(f"[VisionCortex] Snapshot failed: {e}")
            return None

    def analyze_screen(self, query: str = "What is happening on the screen right now?") -> str:
        """
        Takes a snapshot and asks the Vision Language Model (VLM) about it.
        (Uses the multimodal LLM configured in LOVE)
        """
        img_b64 = self.take_snapshot()
        if not img_b64:
            return "Screen capture failed or vision is disabled."
            
        from core.llm import get_reasoning_llm
        try:
            # We assume the reasoning LLM supports image inputs if configured correctly.
            # For this implementation, we will mock the visual analysis or use a text-based fallback 
            # if the local LLM doesn't support images natively in this wrapper.
            # In a real VLM like Gemini 1.5 Pro, we'd pass the base64 image.
            
            # Note: LangChain's HumanMessage can take image URLs.
            from langchain_core.messages import HumanMessage
            
            msg = HumanMessage(
                content=[
                    {"type": "text", "text": query},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    },
                ]
            )
            llm = get_reasoning_llm()
            response = llm.invoke([msg])
            return response.content
        except Exception as e:
            return f"Vision processing error: {str(e)}"

_cortex = None

def get_vision_cortex() -> VisionCortex:
    global _cortex
    if _cortex is None:
        _cortex = VisionCortex()
    return _cortex
