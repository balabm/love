"""
LOVE Clipboard Monitor — Clipboard Intelligence

Watches the clipboard for patterns:
- Copied text → infer what you're working on
- Copied URLs → extract page context
- Copied code → detect language/framework
- Copied addresses, amounts, dates → suggest related actions

Completely local — nothing leaves your machine.
"""

import re
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
CLIPBOARD_LOG = DATA_DIR / "clipboard_intelligence.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAX_LOG_SIZE = 200  # entries


class ClipboardMonitor:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content: str = ""
        self._history: List[Dict] = []
        self._current_signal: Optional[Dict] = None

    @classmethod
    def get_instance(cls) -> "ClipboardMonitor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = ClipboardMonitor()
            return cls._instance

    def _read_clipboard(self) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=3
            )
            return (result.stdout or "").strip()
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="integrations.clipboard_monitor")
        try:
            import tkinter as tk
            root = tk.Tk(); root.withdraw()
            content = root.clipboard_get()
            root.destroy()
            return content
        except Exception:
            return ""

    def _analyze(self, text: str) -> Dict[str, Any]:
        """Classify and extract signal from clipboard content."""
        result = {"type": "text", "signal": "", "action": None, "preview": text[:100]}

        # URL detection
        url_match = re.search(r"https?://[^\s]+", text)
        if url_match:
            url = url_match.group()
            domain = re.search(r"https?://([^/]+)", url)
            dn = domain.group(1) if domain else url
            result["type"] = "url"
            result["signal"] = f"Copied URL: {dn}"
            if any(s in dn for s in ["github.com", "gitlab.com"]):
                result["action"] = "github_url"
            elif any(s in dn for s in ["docs.google.com", "notion.so", "confluence"]):
                result["action"] = "document_url"
            elif any(s in dn for s in ["youtube.com", "youtu.be"]):
                result["action"] = "video_url"
            return result

        # Code detection
        code_signals = [
            (r"def\s+\w+\s*\(", "python"),
            (r"function\s+\w+\s*\(", "javascript"),
            (r"class\s+\w+\s*(:\s*\w+)?\s*\{", "java/csharp"),
            (r"SELECT\s+.*\s+FROM", "sql"),
            (r"<\?php", "php"),
            (r"import\s+\w+|from\s+\w+\s+import", "python"),
            (r"const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=", "javascript"),
        ]
        for pattern, lang in code_signals:
            if re.search(pattern, text, re.IGNORECASE):
                result["type"] = "code"
                result["signal"] = f"Copied {lang} code ({len(text)} chars)"
                result["language"] = lang
                return result

        # Error/stack trace
        if re.search(r"Traceback|Error:|Exception:|at\s+\w+\.\w+\(", text):
            result["type"] = "error"
            first_line = text.split("\n")[0][:100]
            result["signal"] = f"Copied error: {first_line}"
            result["action"] = "debug_help"
            return result

        # Phone/email
        if re.search(r"[\w.-]+@[\w.-]+\.\w+", text):
            result["type"] = "email"
            result["signal"] = "Copied email address"
            return result

        # Numbers/amounts
        if re.search(r"[\$₹€£]\s*[\d,]+|[\d,]+\s*[\$₹€£]", text):
            result["type"] = "amount"
            result["signal"] = f"Copied amount: {text[:30]}"
            return result

        # Generic text
        words = len(text.split())
        if words > 50:
            result["signal"] = f"Copied text ({words} words)"
        elif words > 5:
            result["signal"] = f"Copied: '{text[:60]}'"

        return result

    def _process(self, content: str):
        if content == self._last_content or not content.strip():
            return
        self._last_content = content
        analysis = self._analyze(content)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content_length": len(content),
            **analysis,
        }
        self._current_signal = entry
        self._history.insert(0, entry)
        if len(self._history) > MAX_LOG_SIZE:
            self._history = self._history[:MAX_LOG_SIZE]
        # Log to file
        try:
            with open(CLIPBOARD_LOG, "a", encoding="utf-8") as f:
                f.write(f'{{"timestamp":"{entry["timestamp"]}","type":"{entry["type"]}","signal":"{entry["signal"][:100]}"}}\n')
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="integrations.clipboard_monitor")
        # Push if it's an error (LOVE can proactively offer help)
        if analysis.get("action") == "debug_help":
            try:
                from core.proactive_push import get_push_engine
                get_push_engine().push(
                    "INSIGHT",
                    f"I see you copied an error. Want me to help debug? ({analysis['signal'][:80]})",
                    priority="normal",
                    metadata={"type": "debug_offer", "preview": content[:200]},
                )
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="integrations.clipboard_monitor")

    def get_current_signal(self) -> Optional[Dict]:
        return self._current_signal

    def get_context_summary(self) -> str:
        if self._current_signal:
            sig = self._current_signal.get("signal", "")
            if sig:
                return f"[CLIPBOARD] {sig}"
        return ""

    def get_recent(self, limit: int = 5) -> List[Dict]:
        return self._history[:limit]

    def start_monitoring(self, interval: float = 1.5):
        if self._running:
            return
        self._running = True
        def _loop():
            while self._running:
                try:
                    content = self._read_clipboard()
                    if content:
                        self._process(content)
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="integrations.clipboard_monitor")
                time.sleep(interval)
        self._thread = threading.Thread(target=_loop, daemon=True, name="LOVE-Clipboard")
        self._thread.start()

    def stop(self):
        self._running = False


def get_clipboard_monitor() -> ClipboardMonitor:
    return ClipboardMonitor.get_instance()
