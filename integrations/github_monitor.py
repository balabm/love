"""
LOVE GitHub Monitor — Repository Intelligence

Monitors your GitHub repos, PRs, issues, commits in real-time.
No webhook needed — polls GitHub REST API.

Setup:
  1. Go to https://github.com/settings/tokens
  2. Generate classic token with: repo, notifications scopes
  3. Add to .env: GITHUB_TOKEN=ghp_your_token
  4. Add to .env: GITHUB_USERNAME=your_username
"""

import json
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GITHUB_CACHE = DATA_DIR / "github_cache.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
POLL_INTERVAL = 300  # 5 minutes


class GitHubMonitor:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._connected = False
        self._cache: Dict[str, Any] = {}
        self._last_poll: Optional[float] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._events: List[Dict] = []
        self._repos: List[Dict] = []
        self._notifications: List[Dict] = []
        self._load_cache()
        if GITHUB_TOKEN:
            self._try_connect()

    @classmethod
    def get_instance(cls) -> "GitHubMonitor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = GitHubMonitor()
            return cls._instance

    def _headers(self) -> Dict:
        return {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LOVE-Intelligence/1.0",
        }

    def _get(self, url: str, timeout: int = 8) -> Optional[Dict]:
        if not GITHUB_TOKEN:
            return None
        try:
            import urllib.request, urllib.error
            req = urllib.request.Request(url, headers=self._headers())
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception:
            return None

    def _try_connect(self):
        result = self._get("https://api.github.com/user")
        if result and result.get("login"):
            self._connected = True
            self._cache["user"] = result
            self._save_cache()

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> Dict:
        return {
            "connected": self._connected,
            "token_set": bool(GITHUB_TOKEN),
            "username": GITHUB_USERNAME or self._cache.get("user", {}).get("login", ""),
            "repos_tracked": len(self._repos),
            "unread_notifications": len(self._notifications),
            "last_poll": self._last_poll,
        }

    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """Get recent GitHub events (pushes, PRs, issues, stars)."""
        if not self._connected:
            return self._cache.get("events", [])[:limit]
        try:
            username = GITHUB_USERNAME or self._cache.get("user", {}).get("login", "")
            if not username:
                return []
            data = self._get(f"https://api.github.com/users/{username}/events?per_page={limit}")
            if not isinstance(data, list):
                return []
            events = []
            for ev in data[:limit]:
                repo = ev.get("repo", {}).get("name", "")
                etype = ev.get("type", "")
                payload = ev.get("payload", {})
                created = ev.get("created_at", "")
                summary = ""
                if etype == "PushEvent":
                    commits = payload.get("commits", [])
                    msg = commits[0].get("message", "")[:80] if commits else ""
                    summary = f"Pushed to {repo}: {msg}"
                elif etype == "PullRequestEvent":
                    action = payload.get("action", "")
                    pr = payload.get("pull_request", {})
                    summary = f"PR {action}: {pr.get('title', '')[:80]} in {repo}"
                elif etype == "IssuesEvent":
                    action = payload.get("action", "")
                    issue = payload.get("issue", {})
                    summary = f"Issue {action}: {issue.get('title', '')[:80]} in {repo}"
                elif etype == "CreateEvent":
                    ref_type = payload.get("ref_type", "")
                    summary = f"Created {ref_type} in {repo}"
                elif etype == "WatchEvent":
                    summary = f"Starred {repo}"
                else:
                    summary = f"{etype} in {repo}"
                events.append({"type": etype, "repo": repo, "summary": summary, "created_at": created})
            self._events = events
            self._cache["events"] = events
            self._save_cache()
            return events
        except Exception:
            return self._cache.get("events", [])

    def get_notifications(self, limit: int = 10) -> List[Dict]:
        """Get unread GitHub notifications (@mentions, PR reviews, etc.)."""
        if not self._connected:
            return []
        try:
            data = self._get("https://api.github.com/notifications?all=false")
            if not isinstance(data, list):
                return []
            notifs = []
            for n in data[:limit]:
                subj = n.get("subject", {})
                notifs.append({
                    "title": subj.get("title", ""),
                    "type": subj.get("type", ""),
                    "repo": n.get("repository", {}).get("full_name", ""),
                    "reason": n.get("reason", ""),
                    "updated": n.get("updated_at", ""),
                })
            self._notifications = notifs
            return notifs
        except Exception:
            return []

    def get_open_prs(self) -> List[Dict]:
        """Get open PRs where you're involved."""
        if not self._connected:
            return []
        try:
            username = GITHUB_USERNAME or self._cache.get("user", {}).get("login", "")
            if not username:
                return []
            data = self._get(f"https://api.github.com/search/issues?q=is:open+is:pr+author:{username}&per_page=10")
            if not data:
                return []
            items = data.get("items", [])
            return [{"title": i.get("title", ""), "repo": i.get("repository_url", "").split("/")[-1],
                     "url": i.get("html_url", ""), "created": i.get("created_at", "")} for i in items[:10]]
        except Exception:
            return []

    def get_context_summary(self) -> str:
        """Summary for injection into LOVE's context prompt."""
        if not self._connected:
            return ""
        parts = []
        try:
            notifs = self._notifications or self.get_notifications(5)
            if notifs:
                parts.append(f"[GITHUB] {len(notifs)} unread notification(s)")
                for n in notifs[:2]:
                    parts.append(f"  • {n['reason']}: {n['title'][:60]} ({n['repo']})")
            events = self._events or self.get_recent_events(3)
            if events:
                parts.append(f"[GITHUB] Recent: {events[0]['summary'][:80]}")
        except Exception:
            pass
        return "\n".join(parts)

    def start_polling(self, interval: int = POLL_INTERVAL):
        if self._running or not self._connected:
            return
        self._running = True
        def _loop():
            while self._running:
                try:
                    self.get_recent_events(10)
                    self.get_notifications(10)
                    self._last_poll = time.time()
                    # Push important notifications
                    try:
                        from core.proactive_push import get_push_engine
                        engine = get_push_engine()
                        urgent = [n for n in self._notifications if n.get("reason") in ("mention", "review_requested", "assign")]
                        if urgent:
                            engine.push("ALERT", f"GitHub: {urgent[0]['title'][:100]} ({urgent[0]['reason']})", priority="high", metadata={"source": "github"})
                    except Exception:
                        pass
                except Exception:
                    pass
                time.sleep(interval)
        self._thread = threading.Thread(target=_loop, daemon=True, name="LOVE-GitHub")
        self._thread.start()

    def _save_cache(self):
        try:
            GITHUB_CACHE.write_text(json.dumps(self._cache, default=str, indent=2))
        except Exception:
            pass

    def _load_cache(self):
        try:
            if GITHUB_CACHE.exists():
                self._cache = json.loads(GITHUB_CACHE.read_text())
        except Exception:
            self._cache = {}


def get_github_monitor() -> GitHubMonitor:
    return GitHubMonitor.get_instance()
