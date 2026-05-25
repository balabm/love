"""
LOVE Browser Monitor — Active Tab & Browsing Intelligence

Reads what's open in your browser RIGHT NOW using:
- Chrome/Edge: query via chrome-remote-debugging-protocol (if debug port open)
- Fallback: scan window titles from running processes
- Reads browser history from local SQLite DBs (Chrome, Firefox, Edge)

No browser extension needed. Pure local.

Setup (optional, for live tab reading):
  Chrome: add --remote-debugging-port=9222 to Chrome shortcut
  Or just let it fall back to window title scanning.
"""

import json
import os
import sqlite3
import subprocess
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
BROWSER_CACHE = DATA_DIR / "browser_cache.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CHROME_DEBUG_PORT = int(os.getenv("CHROME_DEBUG_PORT", "9222"))


class BrowserMonitor:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._active_tabs: List[Dict] = []
        self._recent_history: List[Dict] = []
        self._current_url: str = ""
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_cache()

    @classmethod
    def get_instance(cls) -> "BrowserMonitor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = BrowserMonitor()
            return cls._instance

    def _try_chrome_debug(self) -> List[Dict]:
        """Try to get tabs via Chrome DevTools Protocol."""
        try:
            import urllib.request
            url = f"http://localhost:{CHROME_DEBUG_PORT}/json"
            with urllib.request.urlopen(url, timeout=2) as r:
                tabs = json.loads(r.read())
            result = []
            for t in tabs:
                if t.get("type") == "page":
                    result.append({
                        "title": t.get("title", ""),
                        "url": t.get("url", ""),
                        "active": False,
                    })
            if result:
                result[0]["active"] = True
            return result
        except Exception:
            return []

    def _scan_window_titles(self) -> List[Dict]:
        """Scan process window titles to detect active browser."""
        try:
            import subprocess
            # Windows: use tasklist + PowerShell to get window titles
            ps_cmd = 'Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object ProcessName,MainWindowTitle | ConvertTo-Json'
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            browser_procs = {"chrome", "msedge", "firefox", "opera", "brave"}
            tabs = []
            for proc in (data or []):
                pname = proc.get("ProcessName", "").lower()
                if any(b in pname for b in browser_procs):
                    title = proc.get("MainWindowTitle", "")
                    if title and " - " in title:
                        # Title format: "Page Title - Browser Name"
                        page_title = title.rsplit(" - ", 1)[0]
                        tabs.append({"title": page_title, "url": "", "active": True, "browser": pname})
            return tabs[:5]
        except Exception:
            return []

    def _read_chrome_history(self, limit: int = 20) -> List[Dict]:
        """Read Chrome/Edge browsing history from local SQLite."""
        histories = []
        # Chrome
        chrome_history = Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data/Default/History"
        edge_history = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/User Data/Default/History"
        firefox_places = Path(os.environ.get("APPDATA", "")) / "Mozilla/Firefox/Profiles"

        for history_path in [chrome_history, edge_history]:
            if history_path.exists():
                try:
                    # Copy to temp to avoid lock issues
                    import shutil, tempfile
                    tmp = Path(tempfile.mktemp(suffix=".db"))
                    shutil.copy2(history_path, tmp)
                    conn = sqlite3.connect(str(tmp))
                    cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
                    # Chrome stores time as microseconds since 1601-01-01
                    chrome_epoch_offset = 11644473600
                    chrome_cutoff = int((cutoff + chrome_epoch_offset) * 1_000_000)
                    rows = conn.execute(
                        "SELECT title, url, visit_count, last_visit_time FROM urls "
                        "WHERE last_visit_time > ? ORDER BY last_visit_time DESC LIMIT ?",
                        (chrome_cutoff, limit)
                    ).fetchall()
                    conn.close()
                    tmp.unlink(missing_ok=True)
                    for row in rows:
                        title, url, visits, _ = row
                        if url and not url.startswith("chrome://"):
                            histories.append({"title": title or url[:50], "url": url, "visits": visits})
                    break  # Use first found browser
                except Exception:
                    pass
        return histories[:limit]

    def refresh(self):
        """Refresh active tabs and recent history."""
        tabs = self._try_chrome_debug()
        if not tabs:
            tabs = self._scan_window_titles()
        self._active_tabs = tabs
        if tabs:
            self._current_url = tabs[0].get("url", "") or tabs[0].get("title", "")
        # History (every 30 min max)
        try:
            self._recent_history = self._read_chrome_history(20)
        except Exception:
            pass
        self._save_cache()

    def get_active_tabs(self) -> List[Dict]:
        return self._active_tabs

    def get_current_context(self) -> str:
        """What is the user looking at right now?"""
        if self._active_tabs:
            t = self._active_tabs[0]
            title = t.get("title", "")
            url = t.get("url", "")
            if title:
                return f"Active browser tab: {title}" + (f" ({url[:60]})" if url else "")
        return ""

    def get_recent_topics(self, limit: int = 5) -> List[str]:
        """Extract topics from recent browsing history."""
        topics = []
        for h in self._recent_history[:limit]:
            title = h.get("title", "")
            if title and len(title) > 5:
                topics.append(title[:80])
        return topics

    def get_context_summary(self) -> str:
        ctx = self.get_current_context()
        if not ctx:
            return ""
        return f"[BROWSER] {ctx}"

    def start_monitoring(self, interval: int = 30):
        if self._running:
            return
        self._running = True
        def _loop():
            while self._running:
                try:
                    self.refresh()
                except Exception:
                    pass
                time.sleep(interval)
        self._thread = threading.Thread(target=_loop, daemon=True, name="LOVE-Browser")
        self._thread.start()

    def _save_cache(self):
        try:
            BROWSER_CACHE.write_text(json.dumps({
                "tabs": self._active_tabs,
                "history": self._recent_history[:20],
            }, default=str))
        except Exception:
            pass

    def _load_cache(self):
        try:
            if BROWSER_CACHE.exists():
                data = json.loads(BROWSER_CACHE.read_text())
                self._active_tabs = data.get("tabs", [])
                self._recent_history = data.get("history", [])
        except Exception:
            pass


def get_browser_monitor() -> BrowserMonitor:
    return BrowserMonitor.get_instance()
