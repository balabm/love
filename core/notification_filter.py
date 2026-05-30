"""
LOVE Smart Notification Filter — Contextual Relevance Filtering (Modern AI Pattern)

Notification overload is a major problem. This filter:

1. RELEVANCE SCORING
   - Score each notification by relevance to current user context
   - Weight by sender importance, content urgency, and user history
   - Consider time of day and focus mode

2. SMART BATCHING
   - Batch low-priority notifications into digest summaries
   - Deliver high-priority notifications immediately
   - Defer medium-priority notifications to appropriate times

3. CONTEXT AWARENESS
   - Suppress non-urgent notifications during deep work
   - Surface work-related notifications during work hours
   - Surface personal notifications during personal time

4. LEARNING
   - Learn which notifications the user acts on
   - Adapt filtering thresholds based on user behavior
   - Detect and filter notification spam

Architecture:
- filter_notifications(notifications, context): Filter and prioritize
- score_relevance(notification, context): Score single notification
- get_filter_stats(): Track filtering effectiveness
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "notification_filter"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FILTER_LOG = DATA_DIR / "filter_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Notification:
    """A notification to be filtered."""
    id: str = ""
    source: str = ""  # app, sender, system
    title: str = ""
    body: str = ""
    priority: str = "normal"  # low, normal, high, urgent
    category: str = "general"  # work, personal, social, system
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilteredNotification:
    """A notification after filtering."""
    notification: Notification = field(default_factory=Notification)
    relevance_score: float = 0.0
    action: str = "deliver"  # deliver, batch, defer, suppress
    reason: str = ""
    deliver_at: Optional[str] = None


class NotificationFilter:
    """
    Filter notifications by contextual relevance.
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
        self._stats = {
            "total_filtered": 0,
            "delivered": 0,
            "batched": 0,
            "deferred": 0,
            "suppressed": 0,
            "avg_relevance": 0.0,
        }
        self._source_scores: Dict[str, float] = defaultdict(float)
        self._load_stats()

    # ── Core Filtering ────────────────────────────────────────────────────

    def filter_notifications(self, notifications: List[Notification], context: Optional[Dict[str, Any]] = None) -> List[FilteredNotification]:
        """Filter and prioritize notifications."""
        if context is None:
            context = {}

        if not notifications:
            return []

        filtered = []
        for notif in notifications:
            score = self._score_relevance(notif, context)
            action, reason, deliver_at = self._determine_action(notif, score, context)

            filtered.append(FilteredNotification(
                notification=notif,
                relevance_score=round(score, 3),
                action=action,
                reason=reason,
                deliver_at=deliver_at,
            ))

        with self._lock:
            self._stats["total_filtered"] += len(notifications)
            for f in filtered:
                self._stats[f.action + "d"] = self._stats.get(f.action + "d", 0) + 1

        self._save_stats()
        self._log_filtering(filtered)

        return filtered

    def _score_relevance(self, notif: Notification, context: Dict[str, Any]) -> float:
        """Score notification relevance."""
        score = 0.3  # Base score

        # Priority boost
        priority_scores = {"low": 0.2, "normal": 0.5, "high": 0.8, "urgent": 1.0}
        score += priority_scores.get(notif.priority, 0.5) * 0.3

        # Source importance (learned)
        source_score = self._source_scores.get(notif.source, 0.5)
        score += source_score * 0.2

        # Category alignment with context
        current_activity = context.get("activity", "general")
        category_alignment = {
            "work": {"work": 1.0, "system": 0.7, "social": 0.2, "personal": 0.3},
            "personal": {"personal": 1.0, "social": 0.8, "work": 0.2, "system": 0.5},
            "deep_work": {"work": 0.3, "system": 0.5, "social": 0.0, "personal": 0.1},
        }
        alignment = category_alignment.get(current_activity, {})
        score += alignment.get(notif.category, 0.5) * 0.2

        # Time sensitivity
        try:
            notif_time = datetime.fromisoformat(notif.timestamp)
            age_hours = (datetime.now() - notif_time).total_seconds() / 3600
            if age_hours < 1:
                score += 0.1
            elif age_hours > 24:
                score -= 0.1
        except Exception:
            pass

        # Focus mode suppression
        if context.get("focus_mode", False) and notif.priority not in ("urgent", "high"):
            score *= 0.3

        return min(1.0, max(0.0, score))

    def _determine_action(self, notif: Notification, score: float, context: Dict[str, Any]) -> tuple:
        """Determine what to do with a notification."""
        focus_mode = context.get("focus_mode", False)
        work_hours = context.get("work_hours", False)

        # Urgent always delivers
        if notif.priority == "urgent":
            return "deliver", "urgent priority", None

        # During focus mode, only urgent/high delivers
        if focus_mode and notif.priority not in ("urgent", "high"):
            return "suppress", "focus mode active", None

        # Score-based action
        if score > 0.7:
            return "deliver", f"high relevance ({score:.2f})", None
        elif score > 0.4:
            if work_hours and notif.category == "personal":
                # Defer personal to after work
                return "defer", "personal during work hours", (datetime.now() + timedelta(hours=4)).isoformat()
            return "batch", f"medium relevance ({score:.2f})", None
        else:
            return "suppress", f"low relevance ({score:.2f})", None

    # ── Learning ──────────────────────────────────────────────────────────

    def record_interaction(self, notif_id: str, source: str, acted: bool):
        """Record whether user acted on notification."""
        if acted:
            self._source_scores[source] = min(1.0, self._source_scores.get(source, 0.5) + 0.05)
        else:
            self._source_scores[source] = max(0.0, self._source_scores.get(source, 0.5) - 0.02)
        self._save_stats()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_filter_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "source_scores": dict(self._source_scores),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "source_scores": dict(self._source_scores),
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                self._source_scores.update(data.get("source_scores", {}))
        except Exception:
            pass

    def _log_filtering(self, filtered: List[FilteredNotification]):
        try:
            with open(FILTER_LOG, "a") as f:
                for f_notif in filtered:
                    f.write(json.dumps({
                        "timestamp": datetime.now().isoformat(),
                        "notif_id": f_notif.notification.id,
                        "source": f_notif.notification.source,
                        "action": f_notif.action,
                        "relevance": f_notif.relevance_score,
                    }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_nf_instance: Optional[NotificationFilter] = None
_nf_lock = threading.Lock()


def get_notification_filter() -> NotificationFilter:
    global _nf_instance
    with _nf_lock:
        if _nf_instance is None:
            _nf_instance = NotificationFilter()
        return _nf_instance
