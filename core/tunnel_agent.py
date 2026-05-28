"""
LOVE Tunnel Agent — Autonomous Cloudflare Tunnel Subagent

Spawns and manages a cloudflared tunnel as a background subprocess,
auto-extracts the public URL, updates the environment, and restarts
on failure. Zero user intervention after initial setup.

Workflow:
  1. Detects if cloudflared binary is available (path or system)
  2. Spawns: cloudflared tunnel --url http://localhost:8000
  3. Parses stdout for: Your quick Tunnel has been created! url=...
  4. Persists URL to .env and notifies device_bridge
  5. Health-checks every 30s — restarts if process dies
  6. Exposes status via singleton API

Env overrides:
  TUNNEL_AGENT_ENABLED=true        (default true)
  TUNNEL_LOCAL_URL=http://localhost:8000
  TUNNEL_BINARY_PATH=cloudflared   (or full path)
  TUNNEL_MAX_RETRIES=5
  TUNNEL_RETRY_DELAY_SECONDS=10
"""

import json
import os
import re
import sys
import time
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
TUNNEL_STATE_FILE = DATA_DIR / "tunnel_state.json"
ENV_FILE = Path(__file__).parent.parent / ".env"

TUNNEL_AGENT_ENABLED = os.getenv("TUNNEL_AGENT_ENABLED", "true").lower() in ("true", "1", "yes")
LOCAL_URL = os.getenv("TUNNEL_LOCAL_URL", "http://localhost:8000")
BINARY_PATH = os.getenv("TUNNEL_BINARY_PATH", "cloudflared")
NAMED_TUNNEL = os.getenv("CLOUDFLARE_TUNNEL_NAME", "").strip()
MAX_RETRIES = int(os.getenv("TUNNEL_MAX_RETRIES", "5"))
RETRY_DELAY = int(os.getenv("TUNNEL_RETRY_DELAY_SECONDS", "10"))


def _find_cloudflared() -> Optional[str]:
    """Locate cloudflared binary."""
    # 1. Explicit env path
    if os.path.isfile(BINARY_PATH):
        return BINARY_PATH

    # 2. System PATH
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(folder) / "cloudflared.exe"
        if candidate.exists():
            return str(candidate)
        candidate = Path(folder) / "cloudflared"
        if candidate.exists():
            return str(candidate)

    # 3. Common Windows locations
    common = [
        r"C:\Program Files\Cloudflare\cloudflared.exe",
        r"C:\Windows\System32\cloudflared.exe",
    ]
    for p in common:
        if os.path.isfile(p):
            return p

    return None


def _get_named_tunnel_info(binary: str, name: str) -> Optional[Dict[str, Any]]:
    """Query cloudflared for named tunnel ID and permanent URL."""
    try:
        result = subprocess.run(
            [binary, "tunnel", "list", "--output", "json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return None
        tunnels = json.loads(result.stdout)
        for t in tunnels:
            if t.get("name") == name:
                tunnel_id = t.get("id", "")
                # Permanent URL for named tunnels
                permanent_url = f"https://{tunnel_id}.cfargotunnel.com" if tunnel_id else None
                return {
                    "id": tunnel_id,
                    "name": name,
                    "url": permanent_url,
                }
        return None
    except Exception:
        return None


def _update_env_file(key: str, value: str):
    """Update or append a key in the .env file."""
    try:
        lines = []
        found = False
        if ENV_FILE.exists():
            lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}")
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Also update in-memory os.environ for immediate use
        os.environ[key] = value
    except Exception as e:
        print(f"[TunnelAgent] Failed to update .env: {e}")


class TunnelAgent:
    """
    Autonomous subagent that manages cloudflared lifecycle.
    Singleton — one tunnel per LOVE instance.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._proc: Optional[subprocess.Popen] = None
        self._url: Optional[str] = None
        self._status = "idle"  # idle | starting | running | error | missing_binary
        self._last_error: Optional[str] = None
        self._retry_count = 0
        self._started_at: Optional[str] = None
        self._stdout_buffer: str = ""
        self._named_tunnel: Optional[str] = NAMED_TUNNEL if NAMED_TUNNEL else None
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_state()
        # If named tunnel configured, try to resolve permanent URL early
        if self._named_tunnel:
            self._try_resolve_named_url()

    def _try_resolve_named_url(self):
        binary = _find_cloudflared()
        if not binary or not self._named_tunnel:
            return
        info = _get_named_tunnel_info(binary, self._named_tunnel)
        if info and info.get("url"):
            self._url = info["url"]
            _update_env_file("CLOUDFLARE_TUNNEL_URL", self._url)
            print(f"[TunnelAgent] Named tunnel '{self._named_tunnel}' → {self._url}")

    @classmethod
    def get_instance(cls) -> "TunnelAgent":
        with cls._lock:
            if cls._instance is None:
                cls._instance = TunnelAgent()
            return cls._instance

    # ─── Public API ────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "status": self._status,
            "url": self._url,
            "local_url": LOCAL_URL,
            "binary_found": _find_cloudflared() is not None,
            "binary_path": _find_cloudflared() or BINARY_PATH,
            "named_tunnel": self._named_tunnel,
            "started_at": self._started_at,
            "last_error": self._last_error,
            "retries": self._retry_count,
        }

    def get_url(self) -> Optional[str]:
        return self._url

    # ─── Lifecycle ───────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        if not TUNNEL_AGENT_ENABLED:
            self._status = "disabled"
            print("[TunnelAgent] Disabled via TUNNEL_AGENT_ENABLED=false")
            return

        binary = _find_cloudflared()
        if not binary:
            self._status = "missing_binary"
            self._last_error = "cloudflared binary not found. Install: winget install Cloudflare.cloudflared"
            print(f"[TunnelAgent] {self._last_error}")
            return

        # If named tunnel configured but not yet resolved, try now
        if self._named_tunnel and not self._url:
            self._try_resolve_named_url()

        self._running = True
        self._thread = threading.Thread(target=self._agent_loop, daemon=True, name="LOVE-TunnelAgent")
        self._thread.start()
        mode = f"named='{self._named_tunnel}'" if self._named_tunnel else "quick tunnel"
        print(f"[TunnelAgent] Started ({mode}). Binary: {binary}")

    def stop(self):
        self._running = False
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None
        self._status = "stopped"
        self._save_state()
        print("[TunnelAgent] Stopped.")

    # ─── Agent Loop ────────────────────────────────────────────────────────────

    def _agent_loop(self):
        """Main supervision loop: start tunnel, monitor, restart on failure."""
        time.sleep(3)  # Let LOVE finish startup
        while self._running:
            try:
                self._start_tunnel()
                if self._proc:
                    self._monitor_tunnel()
            except Exception as e:
                self._last_error = str(e)
                print(f"[TunnelAgent] Loop error: {e}")

            if not self._running:
                break

            self._retry_count += 1
            if self._retry_count > MAX_RETRIES:
                self._status = "error"
                self._last_error = f"Max retries ({MAX_RETRIES}) exceeded. Giving up."
                print(f"[TunnelAgent] {self._last_error}")
                break

            print(f"[TunnelAgent] Restarting in {RETRY_DELAY}s... (retry {self._retry_count}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)

    def _start_tunnel(self):
        """Spawn the cloudflared subprocess."""
        binary = _find_cloudflared()
        if not binary:
            raise RuntimeError("cloudflared binary disappeared")

        if self._named_tunnel:
            cmd = [binary, "tunnel", "run", self._named_tunnel]
            # Named tunnel URL is already known — resolve if missing
            if not self._url:
                self._try_resolve_named_url()
        else:
            cmd = [binary, "tunnel", "--url", LOCAL_URL]

        self._status = "starting"
        self._started_at = datetime.now().isoformat()
        self._stdout_buffer = ""
        print(f"[TunnelAgent] Spawning: {' '.join(cmd)}")

        try:
            if sys.platform == "win32":
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    text=True,
                    bufsize=1,
                )
            else:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                )
        except Exception as e:
            self._status = "error"
            self._last_error = f"Failed to spawn: {e}"
            raise

    def _monitor_tunnel(self):
        """Read stdout, extract URL, health-check the process."""
        if not self._proc or not self._proc.stdout:
            return

        start_time = time.time()
        # Named tunnels already have a permanent URL — skip URL parsing
        url_found = bool(self._named_tunnel and self._url)

        def _proc_alive() -> bool:
            return self._proc is not None and self._proc.poll() is None

        while self._running and _proc_alive():
            # Non-blocking read on stdout
            try:
                if sys.platform == "win32":
                    line = self._proc.stdout.readline()
                    if line:
                        self._process_line(line)
                        if self._url:
                            url_found = True
                else:
                    import select
                    ready, _, _ = select.select([self._proc.stdout], [], [], 1.0)
                    if ready:
                        line = self._proc.stdout.readline()
                        if line:
                            self._process_line(line)
                            if self._url:
                                url_found = True
            except Exception:
                pass

            # Health check: if URL found, just verify process alive
            if url_found:
                self._status = "running"
                time.sleep(5)
                if not _proc_alive():
                    self._status = "error"
                    self._last_error = "Tunnel process exited unexpectedly"
                    break
                continue

            # Timeout waiting for URL (only for quick tunnels)
            if time.time() - start_time > 60:
                self._status = "error"
                self._last_error = "Timeout: URL not received within 60s"
                self._kill_proc()
                break

        # Process died
        if self._proc and self._proc.poll() is not None:
            self._status = "error"
            rc = self._proc.returncode
            self._last_error = f"Tunnel exited with code {rc}"
            print(f"[TunnelAgent] {self._last_error}")

    def _process_line(self, line: str):
        """Parse a line of cloudflared output."""
        line = line.strip()
        if not line:
            return
        print(f"[cloudflared] {line}")
        self._stdout_buffer += line + "\n"

        # Extract URL
        match = re.search(r'url=(https://[\w\-\.]+\.trycloudflare\.com)', line)
        if match:
            new_url = match.group(1)
            old_url = getattr(self, '_prev_url', None)
            if new_url != old_url and old_url is not None:
                # URL changed — notify user via push
                self._push_url_change(old_url, new_url)
            self._prev_url = new_url
            if not self._url:
                self._url = new_url
                self._status = "running"
                print(f"[TunnelAgent] Tunnel URL: {self._url}")
                _update_env_file("CLOUDFLARE_TUNNEL_URL", self._url)
                self._save_state()
                # Notify device bridge that URL is available
                try:
                    from integrations.device_bridge import get_device_bridge
                    bridge = get_device_bridge()
                    print(f"[TunnelAgent] Device bridge notified. Webhook: {self._url}/device/webhook")
                except Exception:
                    pass

    def _push_url_change(self, old_url: str, new_url: str):
        """Push notification when tunnel URL changes."""
        try:
            from core.push_notifications import get_push_engine
            engine = get_push_engine()
            engine.push(
                category="SYSTEM",
                message=f"Tunnel URL changed. Update Tasker: {new_url}/device/webhook",
                priority="high",
                metadata={"source": "tunnel_agent", "old_url": old_url, "new_url": new_url},
            )
            print(f"[TunnelAgent] Push notification sent: URL changed {old_url} -> {new_url}")
        except Exception:
            pass

    def _kill_proc(self):
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _save_state(self):
        try:
            TUNNEL_STATE_FILE.write_text(
                json.dumps({
                    "url": self._url,
                    "status": self._status,
                    "started_at": self._started_at,
                    "last_error": self._last_error,
                }, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_state(self):
        if not TUNNEL_STATE_FILE.exists():
            return
        try:
            data = json.loads(TUNNEL_STATE_FILE.read_text(encoding="utf-8"))
            self._url = data.get("url")
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═════════════════════════════════════════════════════════════════════════════

def get_tunnel_agent() -> TunnelAgent:
    return TunnelAgent.get_instance()


def start_tunnel_agent():
    agent = get_tunnel_agent()
    agent.start()
    return agent


def stop_tunnel_agent():
    agent = get_tunnel_agent()
    agent.stop()
