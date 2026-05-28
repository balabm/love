"""
LOVE Activity Log — Central persistent record of everything LOVE does autonomously.

This is the "black box recorder" for LOVE's AGI loop. Every module logs actions here,
and the UI displays them in real-time. Without this, LOVE works invisibly and the user
thinks "nothing happened."

Usage:
    from core.activity_log import log_activity, get_recent_activity, get_daily_report
    log_activity("research_engine", "completed_research", "Researched AI capabilities", {"topic": "AI assistants"})
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
ACTIVITY_FILE = DATA_DIR / "activity_log.jsonl"
ACTIVITY_FILE.parent.mkdir(parents=True, exist_ok=True)

_MAX_KEEP_DAYS = 7
_lock = threading.Lock()


def log_activity(
    component: str,
    action: str,
    description: str,
    metadata: Dict[str, Any] = None,
    importance: str = "normal",  # normal | high | critical
) -> str:
    """Log one autonomous activity. Thread-safe. Returns entry ID."""
    entry = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now().isoformat(),
        "component": component,
        "action": action,
        "description": description,
        "metadata": metadata or {},
        "importance": importance,
    }
    with _lock:
        try:
            with open(ACTIVITY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[ActivityLog] Write error: {e}")
    return entry["id"]


def get_recent_activity(
    hours: int = 24,
    components: List[str] = None,
    min_importance: str = "normal",
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get recent activity entries."""
    importance_order = {"normal": 0, "high": 1, "critical": 2}
    min_level = importance_order.get(min_importance, 0)
    cutoff = datetime.now() - timedelta(hours=hours)
    results = []

    try:
        if not ACTIVITY_FILE.exists():
            return []
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01"))
                    if ts < cutoff:
                        continue
                    if components and entry.get("component") not in components:
                        continue
                    if importance_order.get(entry.get("importance", "normal"), 0) < min_level:
                        continue
                    results.append(entry)
                except Exception:
                    continue
    except Exception as e:
        print(f"[ActivityLog] Read error: {e}")

    results.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return results[:limit]


def get_daily_report(date_str: str = None) -> Dict[str, Any]:
    """Get a summary report for a given date (YYYY-MM-DD) or today."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    entries = get_recent_activity(hours=24)
    day_entries = [e for e in entries if e.get("timestamp", "").startswith(date_str)]

    by_component = {}
    for e in day_entries:
        comp = e.get("component", "unknown")
        by_component.setdefault(comp, []).append(e)

    # Count distinct action types
    actions = set(e.get("action") for e in day_entries)

    # Find highlights (high/critical importance)
    highlights = [e for e in day_entries if e.get("importance") in ("high", "critical")]

    return {
        "date": date_str,
        "total_actions": len(day_entries),
        "unique_actions": len(actions),
        "by_component": {k: len(v) for k, v in by_component.items()},
        "highlights": highlights[:10],
        "components_active": list(by_component.keys()),
    }


def get_activity_stats(hours: int = 24) -> Dict[str, Any]:
    """Get activity stats for the dashboard."""
    entries = get_recent_activity(hours=hours, limit=500)
    if not entries:
        return {"total": 0, "by_component": {}, "trend": "idle", "last_action_at": None}

    by_component = {}
    for e in entries:
        comp = e.get("component", "unknown")
        by_component[comp] = by_component.get(comp, 0) + 1

    # Determine trend
    now = datetime.now()
    recent = [e for e in entries if datetime.fromisoformat(e["timestamp"]) > now - timedelta(hours=1)]
    trend = "active" if len(recent) >= 3 else "warming" if len(recent) >= 1 else "idle"

    return {
        "total": len(entries),
        "by_component": by_component,
        "trend": trend,
        "last_action_at": entries[0].get("timestamp") if entries else None,
    }


def _prune_old_entries():
    """Remove entries older than _MAX_KEEP_DAYS. Called automatically on write."""
    cutoff = datetime.now() - timedelta(days=_MAX_KEEP_DAYS)
    try:
        if not ACTIVITY_FILE.exists():
            return
        lines = []
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01"))
                    if ts >= cutoff:
                        lines.append(line)
                except Exception:
                    continue
        with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"[ActivityLog] Prune error: {e}")
