"""
LOVE Tool Registry — Real tools for the ReAct agent loop.

Tools registered here:
  get_current_time       — ISO timestamp
  web_search             — DuckDuckGo HTML scrape (no API key needed)
  http_get               — Fetch any URL and return text/JSON
  read_file              — Read a local file
  write_file             — Write a local file
  list_directory         — List files in a directory
  execute_shell          — Run a shell command (sandboxed, 30s timeout)
  memory_recall          — Search long-term LOVE memory
  get_intelligence        — Snapshot of all connected sources from the hub
  send_notification      — Push an alert via proactive push engine
  get_current_context    — Active window / system context
  calculate              — Safe Python expression evaluator
"""

import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Callable, Dict

# ── Safety: shell commands that are never allowed ─────────────────────────────
_SHELL_BLOCKLIST = [
    "rm -rf /", "format c:", "del /f /s", "mkfs", ":(){:|:&};:",
    "dd if=/dev/zero", "chmod -R 777 /", "sudo rm", "drop table", "drop database",
]


def _shell_safe(command: str) -> bool:
    low = command.lower()
    return not any(b in low for b in _SHELL_BLOCKLIST)


# ── Tool implementations ──────────────────────────────────────────────────────

def _web_search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo HTML search — no API key, no JS required."""
    try:
        # Try duckduckgo-search package first
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if results:
                lines = []
                for r in results:
                    lines.append(f"[{r.get('title','?')}]\n{r.get('href','')}\n{r.get('body','')}")
                return "\n\n".join(lines)
        except ImportError:
            pass

        # Fallback: scrape DuckDuckGo HTML
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Extract result snippets
        snippets = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', html)[:max_results]
        bodies = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html)[:max_results]
        links = re.findall(r'uddg=(https?[^&"]+)', html)[:max_results]

        lines = []
        for i, snip in enumerate(snippets):
            body = bodies[i] if i < len(bodies) else ""
            link = urllib.parse.unquote(links[i]) if i < len(links) else ""
            title = re.sub(r'<[^>]+>', '', snip).strip()
            text = re.sub(r'<[^>]+>', '', body).strip()
            lines.append(f"[{title}]\n{link}\n{text}")

        return "\n\n".join(lines) if lines else f"No results found for: {query}"
    except Exception as e:
        return f"Search error: {e}"


def _http_get(url: str, as_json: bool = False) -> str:
    """Fetch a URL and return its text content (or JSON)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LOVE-AGI/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        if as_json:
            try:
                data = json.loads(raw)
                return json.dumps(data, indent=2)[:4000]
            except Exception:
                pass
        # Strip HTML tags for readability
        text = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s{3,}', '\n\n', text).strip()
        return text[:5000]
    except Exception as e:
        return f"HTTP error: {e}"


def _read_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()[:8000]
    except Exception as e:
        return f"Error reading file: {e}"


def _write_file(filepath: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} chars to {filepath}"
    except Exception as e:
        return f"Error writing file: {e}"


def _list_directory(dirpath: str) -> str:
    try:
        if not os.path.isdir(dirpath):
            return f"Not a directory: {dirpath}"
        items = []
        for item in sorted(os.listdir(dirpath)):
            full = os.path.join(dirpath, item)
            kind = "dir" if os.path.isdir(full) else "file"
            size = os.path.getsize(full) if kind == "file" else 0
            items.append({"name": item, "type": kind, "size": size})
        return json.dumps(items)
    except Exception as e:
        return f"Error listing directory: {e}"


def _execute_shell(command: str, timeout: int = 30) -> str:
    if not _shell_safe(command):
        return f"Blocked: command contains a dangerous pattern."
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0 and err:
            return f"[exit {result.returncode}] {err[:3000]}"
        return out[:3000] if out else f"[exit {result.returncode}] no output"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Shell error: {e}"


def _memory_recall(query: str, limit: int = 5) -> str:
    try:
        from core.memory import recall_memory
        results = recall_memory(query, limit=limit)
        if not results:
            return "No relevant memories found."
        if isinstance(results, list):
            return "\n---\n".join(str(r) for r in results[:limit])
        return str(results)[:3000]
    except Exception as e:
        return f"Memory recall error: {e}"


def _get_intelligence() -> str:
    """Return a JSON snapshot of the intelligence hub."""
    try:
        from core.intelligence_hub import get_intelligence_hub
        hub = get_intelligence_hub()
        snap = hub._snapshot
        return json.dumps({
            "system": snap.system,
            "browser": snap.browser,
            "clipboard": snap.clipboard,
            "finance": snap.finance,
            "github": snap.github,
            "phone": snap.phone,
            "google": snap.google,
            "microsoft": snap.microsoft,
            "cross_patterns": snap.cross_patterns,
            "active_alerts": snap.active_alerts,
            "timestamp": snap.timestamp,
        }, indent=2)
    except Exception as e:
        return f"Intelligence hub error: {e}"


def _send_notification(message: str, priority: str = "high") -> str:
    try:
        from core.proactive_push import get_push_engine
        get_push_engine().push("AgentLoop", message, priority=priority)
        return f"Notification sent: {message[:80]}"
    except Exception as e:
        return f"Notification error: {e}"


def _get_current_context() -> str:
    try:
        from core.context_engine import get_prompt_context
        ctx = get_prompt_context()
        return ctx or "No active context available."
    except Exception as e:
        return f"Context error: {e}"






def _ms_outlook_emails(limit: int = 5) -> str:
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge.get_instance()
        if not ms.is_connected():
            return 'Microsoft not connected. Set MICROSOFT_CLIENT_ID in .env and run auth.'
        emails = ms.get_unread_emails(limit=limit)
        if not emails:
            return 'No unread Outlook emails.'
        lines = []
        for em in emails:
            imp = '[IMPORTANT] ' if em.get('important') else ''
            lines.append(imp + 'From: ' + em.get('from','') + ' | ' + em.get('subject','')[:60])
            if em.get('preview'):
                lines.append('  ' + em['preview'][:100])
        return chr(10).join(lines)
    except Exception as e:
        return f'Outlook error: {e}'


def _ms_calendar_today() -> str:
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge.get_instance()
        if not ms.is_connected():
            return 'Microsoft not connected.'
        events = ms.get_todays_events()
        if not events:
            return 'No events today in Outlook calendar.'
        lines = []
        for ev in events:
            start = ev.get('start','')[:16].replace('T',' ')
            join = ' [Teams link]' if ev.get('join_url') else ''
            lines.append(start + ' - ' + ev.get('title','') + join)
        return chr(10).join(lines)
    except Exception as e:
        return f'Calendar error: {e}'


def _ms_teams_messages(limit: int = 5) -> str:
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge.get_instance()
        if not ms.is_connected():
            return 'Microsoft not connected.'
        msgs = ms.get_teams_messages(limit=limit)
        if not msgs:
            return 'No recent Teams messages.'
        lines = []
        for m in msgs:
            lines.append('[' + m.get('chat','') + '] ' + m.get('from','') + ': ' + m.get('text','')[:120])
        return chr(10).join(lines)
    except Exception as e:
        return f'Teams error: {e}'


def _ms_onedrive_recent(limit: int = 5) -> str:
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge.get_instance()
        if not ms.is_connected():
            return 'Microsoft not connected.'
        files = ms.get_recent_files(limit=limit)
        if not files:
            return 'No recent OneDrive files.'
        return chr(10).join(f.get('name','') + ' - ' + f.get('modified','')[:10] for f in files)
    except Exception as e:
        return f'OneDrive error: {e}'

def _google_calendar_today() -> str:
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return 'Google not connected. Run: python setup_credentials.py'
        import json
        events = gs.get_todays_events()
        if not events:
            return 'No events today.'
        lines = []
        for ev in events:
            mins = ev.get('minutes_away')
            when = ''
            if mins is not None:
                if mins < 0:
                    when = f' [ended {-mins}min ago]'
                elif mins == 0:
                    when = ' [NOW]'
                else:
                    when = f' [in {mins}min]'
            meet = ' | Meet: ' + ev['meet_link'] if ev.get('meet_link') else ''
            lines.append(f"{ev['start_str']} - {ev['title']}{when}{meet}")
        return chr(10).join(lines)
    except Exception as e:
        return f'Calendar error: {e}'


def _google_upcoming_events(days: int = 7) -> str:
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return 'Google not connected.'
        events = gs.get_upcoming_events(days=days)
        if not events:
            return f'No events in the next {days} days.'
        return chr(10).join(f"{ev.get('start', '')[:16]} - {ev.get('title', '')}{(' @ '+ev['location']) if ev.get('location') else ''}" for ev in events[:20])
    except Exception as e:
        return f'Calendar error: {e}'


def _google_email_summary() -> str:
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return 'Google not connected.'
        import json
        data = gs.get_email_summary()
        unread = data.get('unread_important', 0)
        urgent = data.get('urgent', [])
        lines = [f'{unread} unread important emails']
        for msg in urgent[:5]:
            lines.append(f"From: {msg.get('from','')[:40]} | Subject: {msg.get('subject','')[:60]}")
            if msg.get('snippet'):
                lines.append(f"  {msg['snippet'][:100]}")
        return chr(10).join(lines)
    except Exception as e:
        return f'Gmail error: {e}'


def _google_drive_recent(count: int = 10) -> str:
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return 'Google not connected.'
        files = gs.get_recent_drive_files(count=count)
        if not files:
            return 'No recent Drive files.'
        return chr(10).join(f"{f['name']} [{f.get('type','?')}] - modified {f.get('modified','')[:10]}" for f in files)
    except Exception as e:
        return f'Drive error: {e}'


def _google_drive_search(query: str) -> str:
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return 'Google not connected.'
        files = gs.search_drive(query)
        if not files:
            return f'No Drive files matching: {query}'
        return chr(10).join(f"{f['name']} [{f.get('type','?')}] - {f.get('link','')}" for f in files[:10])
    except Exception as e:
        return f'Drive search error: {e}'

def _calculate(expression: str) -> str:
    """Safely evaluate a Python math expression."""
    allowed = set("0123456789+-*/().% ,eE")
    # Allow math functions explicitly
    safe_names = {
        "abs": abs, "round": round, "min": min, "max": max,
        "int": int, "float": float, "pow": pow,
    }
    try:
        import math
        safe_names.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
        result = eval(expression, {"__builtins__": {}}, safe_names)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


# ── Registry class ────────────────────────────────────────────────────────────

class ToolRegistry:
    """
    Central tool registry for LOVE's ReAct agent loop.
    All tools are callable by the LLM via structured tool calls.
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

        # Extend with browser tools if available
        try:
            from core.browser_agent import register_browser_tools
            register_browser_tools(self)
        except ImportError:
            pass

        # Extend with infinite memory tools if available
        try:
            from core.infinite_memory import register_memory_tools
            register_memory_tools(self)
        except ImportError:
            pass

    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]):
        self.tools[name] = {"func": func, "description": description, "parameters": parameters}

    def get_tool_schema(self) -> str:
        schema = [
            {"name": n, "description": d["description"], "parameters": d["parameters"]}
            for n, d in self.tools.items()
        ]
        return json.dumps(schema, indent=2)

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found. Available: {list(self.tools.keys())}"
        try:
            return self.tools[tool_name]["func"](**parameters)
        except TypeError as e:
            return f"Parameter error for '{tool_name}': {e}"
        except Exception as e:
            return f"Tool '{tool_name}' failed: {e}"

    def _register_default_tools(self):
        self.register_tool(
            "get_current_time",
            lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "Get the current date and time.",
            {},
        )
        self.register_tool(
            "web_search",
            _web_search,
            "Search the web for real-time information using DuckDuckGo. Returns titles, URLs, and snippets.",
            {"query": "Search query string.", "max_results": "(optional) Number of results, default 5."},
        )
        self.register_tool(
            "http_get",
            _http_get,
            "Fetch any URL and return its text content. Set as_json=true for JSON APIs.",
            {"url": "Full URL to fetch.", "as_json": "(optional) Parse as JSON if true."},
        )
        self.register_tool(
            "read_file",
            _read_file,
            "Read the contents of a local file.",
            {"filepath": "Absolute or relative path to the file."},
        )
        self.register_tool(
            "write_file",
            _write_file,
            "Write content to a local file (creates directories if needed).",
            {"filepath": "Path to write to.", "content": "Text content to write."},
        )
        self.register_tool(
            "list_directory",
            _list_directory,
            "List files and subdirectories at a given path.",
            {"dirpath": "Directory path to list."},
        )
        self.register_tool(
            "execute_shell",
            _execute_shell,
            "Execute a shell command and return its output. Max 30s timeout. Dangerous commands are blocked.",
            {"command": "Shell command to run.", "timeout": "(optional) Timeout in seconds, default 30."},
        )
        # Keep old name for swarm.py compatibility
        self.register_tool(
            "execute_terminal_command",
            _execute_shell,
            "Alias for execute_shell.",
            {"command": "Shell command to run."},
        )
        self.register_tool(
            "memory_recall",
            _memory_recall,
            "Search LOVE's long-term memory for relevant past conversations and facts.",
            {"query": "What to search for.", "limit": "(optional) Max results, default 5."},
        )
        self.register_tool(
            "get_intelligence",
            _get_intelligence,
            "Get a full snapshot of all connected sources: browser, finance, github, system, etc.",
            {},
        )
        self.register_tool(
            "send_notification",
            _send_notification,
            "Send a desktop/Telegram notification to the user.",
            {"message": "Notification text.", "priority": "(optional) low/medium/high/critical."},
        )
        self.register_tool(
            "get_current_context",
            _get_current_context,
            "Get the current system context: active app, calendar, recent activity.",
            {},
        )
        self.register_tool(
            "calculate",
            _calculate,
            "Safely evaluate a math expression, e.g. '2 ** 32' or 'sqrt(144)'.",
            {"expression": "Python math expression string."},
        )
        self.register_tool(
            "google_calendar_today",
            _google_calendar_today,
            "Get today's Google Calendar events with times and meet links.",
            {},
        )
        self.register_tool(
            "google_upcoming_events",
            _google_upcoming_events,
            "Get Google Calendar events for the next N days.",
            {"days": "(optional) Number of days ahead, default 7."},
        )
        self.register_tool(
            "google_email_summary",
            _google_email_summary,
            "Get unread important Gmail emails with subjects and snippets.",
            {},
        )
        self.register_tool(
            "google_drive_recent",
            _google_drive_recent,
            "Get recently modified Google Drive files.",
            {"count": "(optional) Number of files, default 10."},
        )
        self.register_tool(
            "google_drive_search",
            _google_drive_search,
            "Search Google Drive files by name.",
            {"query": "Search term for file names."},
        )
        self.register_tool(
            "ms_outlook_emails",
            _ms_outlook_emails,
            "Get unread Outlook emails with subjects and previews.",
            {"limit": "(optional) Max emails, default 5."},
        )
        self.register_tool(
            "ms_calendar_today",
            _ms_calendar_today,
            "Get today's Outlook/Teams calendar events.",
            {},
        )
        self.register_tool(
            "ms_teams_messages",
            _ms_teams_messages,
            "Get recent Microsoft Teams chat messages.",
            {"limit": "(optional) Number of messages, default 5."},
        )
        self.register_tool(
            "ms_onedrive_recent",
            _ms_onedrive_recent,
            "Get recently modified OneDrive files.",
            {"limit": "(optional) Number of files, default 5."},
        )


# ── Singleton ─────────────────────────────────────────────────────────────────

_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
