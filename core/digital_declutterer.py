"""
LOVE Digital Declutterer — Digital Wellness Intelligence (Modern AI Pattern)

Most decluttering is manual and overwhelming. This declutterer:

1. CLUTTER TRACKING
   - Track digital storage across devices (files, photos, downloads, desktop)
   - Record app usage and screen time patterns
   - Log notification load and distraction sources

2. USAGE ANALYSIS
   - Identify which apps/files are actually used
   - Find digital hoarding patterns (old downloads, screenshots)
   - Detect notification overload and its impact on focus

3. DECLUTTER SUGGESTIONS
   - Suggest files to archive or delete (large, old, unused)
   - Recommend app uninstalls based on low usage
   - Propose notification batching or muting

4. WELLNESS ALERTS
   - Alert when digital clutter affects productivity
   - Suggest digital detox periods
   - Track decluttering streaks and celebrate progress

Architecture:
- record_storage_scan(category, size_gb, item_count): Log storage state
- record_app_usage(app, duration): Track app usage
- get_clutter_score(): Get digital clutter score
- get_declutter_plan(): Get prioritized cleanup suggestions
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "digital_declutterer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STORAGE_LOG = DATA_DIR / "storage.jsonl"
APP_LOG = DATA_DIR / "app_usage.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class StorageRecord:
    """A storage scan record."""
    category: str = ""  # downloads, desktop, documents, photos, videos, cache, temp
    size_gb: float = 0.0
    item_count: int = 0
    large_files: List[Dict[str, Any]] = field(default_factory=list)
    old_files: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AppUsage:
    """An app usage record."""
    app_name: str = ""
    duration_minutes: float = 0.0
    category: str = ""  # social, work, entertainment, utility, communication
    was_productive: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DigitalDeclutterer:
    """
    Intelligent digital declutterer with wellness focus.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._storage_records: deque = deque(maxlen=100)
        self._app_usage: deque = deque(maxlen=500)
        self._stats = {
            "total_scans": 0,
            "total_app_usage_records": 0,
            "avg_clutter_score": 50,
            "declutter_streak": 0,
            "last_declutter": None,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_storage_scan(self, category: str = "", size_gb: float = 0, item_count: int = 0, large_files: Optional[List[Dict]] = None, old_files: Optional[List[Dict]] = None) -> StorageRecord:
        """Record a storage scan."""
        record = StorageRecord(
            category=category or "general",
            size_gb=size_gb,
            item_count=item_count,
            large_files=large_files or [],
            old_files=old_files or [],
        )

        with self._lock:
            self._storage_records.append(record)
            self._stats["total_scans"] += 1
            self._update_stats()

        self._save_stats()
        self._log_storage(record)

        return record

    def record_app_usage(self, app_name: str = "", duration: float = 0, category: str = "", was_productive: bool = False) -> AppUsage:
        """Record app usage."""
        record = AppUsage(
            app_name=app_name or "unknown",
            duration_minutes=duration,
            category=category or "general",
            was_productive=was_productive,
        )

        with self._lock:
            self._app_usage.append(record)
            self._stats["total_app_usage_records"] += 1
            self._update_stats()

        self._save_stats()
        self._log_app(record)

        return record

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_clutter_score(self) -> int:
        """Calculate digital clutter score (0-100, lower is better)."""
        # Storage clutter
        recent_storage = [r for r in self._storage_records if r.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        total_gb = sum(r.size_gb for r in recent_storage)
        storage_clutter = min(50, total_gb / 10)  # 200GB = 50 points

        # App clutter (too many low-value apps)
        recent_apps = [r for r in self._app_usage if r.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        unproductive_time = sum(r.duration_minutes for r in recent_apps if not r.was_productive)
        app_clutter = min(30, unproductive_time / 60)  # 30 hours unproductive = 30 points

        # Notification/load clutter
        total_usage = sum(r.duration_minutes for r in recent_apps)
        notification_clutter = min(20, total_usage / 120)  # 40 hours total = 20 points

        overall = round(storage_clutter + app_clutter + notification_clutter)
        return min(100, overall)

    def get_declutter_plan(self) -> List[Dict[str, Any]]:
        """Get prioritized cleanup suggestions."""
        suggestions = []

        # Storage suggestions
        recent_storage = [r for r in self._storage_records if r.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        for record in recent_storage:
            if record.size_gb > 5:
                suggestions.append({
                    "category": record.category,
                    "type": "storage",
                    "priority": "high" if record.size_gb > 20 else "medium",
                    "suggestion": f"{record.category} is using {record.size_gb:.1f} GB.",
                    "action": f"Review {len(record.large_files)} large files and {len(record.old_files)} old files in {record.category}.",
                    "potential_savings_gb": round(record.size_gb * 0.3, 1),
                })

        # App suggestions
        recent_apps = [r for r in self._app_usage if r.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        app_summary = defaultdict(lambda: {"duration": 0.0, "count": 0})
        for r in recent_apps:
            app_summary[r.app_name]["duration"] += r.duration_minutes
            app_summary[r.app_name]["count"] += 1

        # Find low-usage apps that might be clutter
        for app, data in app_summary.items():
            if data["duration"] < 30 and data["count"] < 3:  # Less than 30 mins total, used < 3 times
                suggestions.append({
                    "category": "apps",
                    "type": "unused_app",
                    "priority": "low",
                    "suggestion": f"You used {app} for only {data['duration']:.0f} minutes this month.",
                    "action": "Consider uninstalling or moving to web version.",
                    "potential_savings_gb": 0.5,  # Estimated
                })

        # Find high-distraction apps
        unproductive_apps = [(app, data["duration"]) for app, data in app_summary.items() if app in [r.app_name for r in recent_apps if not r.was_productive]]
        unproductive_apps.sort(key=lambda x: x[1], reverse=True)
        
        for app, duration in unproductive_apps[:3]:
            hours = duration / 60
            if hours > 5:
                suggestions.append({
                    "category": "apps",
                    "type": "distraction",
                    "priority": "medium",
                    "suggestion": f"You spent {hours:.1f} hours on {app} this month.",
                    "action": "Set app time limits or move it off your home screen.",
                    "potential_savings_gb": 0,
                })

        # Desktop/Downloads cleanup
        desktop_downloads = [r for r in recent_storage if r.category in ["desktop", "downloads"]]
        for record in desktop_downloads:
            if record.item_count > 20:
                suggestions.append({
                    "category": record.category,
                    "type": "organization",
                    "priority": "medium",
                    "suggestion": f"{record.category} has {record.item_count} items. That's messy.",
                    "action": "Spend 10 minutes sorting into folders or deleting.",
                    "potential_savings_gb": 0,
                })

        return sorted(suggestions, key=lambda x: ({"high": 0, "medium": 1, "low": 2}[x["priority"]], -x.get("potential_savings_gb", 0)))

    def get_digital_wellness_score(self) -> int:
        """Calculate overall digital wellness score (0-100)."""
        clutter = self.get_clutter_score()
        
        # Screen time wellness
        recent_apps = [r for r in self._app_usage if r.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        total_hours = sum(r.duration_minutes for r in recent_apps) / 60
        productive_hours = sum(r.duration_minutes for r in recent_apps if r.was_productive) / 60
        
        # Screen time score (ideal: 4-8 hours/day = 28-56 hrs/week)
        if total_hours < 20:
            screen_score = 80  # Very low screen time
        elif total_hours < 40:
            screen_score = 90  # Balanced
        elif total_hours < 60:
            screen_score = 70  # Getting high
        else:
            screen_score = 50  # Too much

        # Productivity ratio
        if total_hours > 0:
            productivity_ratio = productive_hours / total_hours
            productivity_score = productivity_ratio * 100
        else:
            productivity_score = 50

        # Declutter streak bonus
        streak_bonus = min(10, self._stats["declutter_streak"])

        overall = round((100 - clutter) * 0.4 + screen_score * 0.3 + productivity_score * 0.2 + streak_bonus)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        self._stats["avg_clutter_score"] = round(self.get_clutter_score(), 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception:
            pass

    def _log_storage(self, record: StorageRecord):
        try:
            with open(STORAGE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": record.timestamp,
                    "category": record.category,
                    "size_gb": record.size_gb,
                    "item_count": record.item_count,
                }) + "\n")
        except Exception:
            pass

    def _log_app(self, record: AppUsage):
        try:
            with open(APP_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": record.timestamp,
                    "app": record.app_name,
                    "duration": record.duration_minutes,
                    "category": record.category,
                    "productive": record.was_productive,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dd_instance: Optional[DigitalDeclutterer] = None
_dd_lock = threading.Lock()


def get_digital_declutterer() -> DigitalDeclutterer:
    global _dd_instance
    with _dd_lock:
        if _dd_instance is None:
            _dd_instance = DigitalDeclutterer()
        return _dd_instance
