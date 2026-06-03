"""
LOVE Conversation Continuity Manager — Context Persistence Across Long Gaps (Modern AI Pattern)

When conversations span hours or days, context is lost. This manager:

1. CONTEXT PRESERVATION
   - Capture key facts, decisions, and emotional state at conversation end
   - Store them in a structured "continuity snapshot"
   - Retrieve them when user returns after a gap

2. SMART RE-ENGAGEMENT
   - Detect when user returns after absence
   - Summarize what happened while they were away
   - Proactively surface unfinished threads and pending questions

3. THREAD TRACKING
   - Track multiple conversation threads (work, personal, projects)
   - Allow user to jump between threads without losing context
   - Suggest continuing interrupted threads

4. GAP INTELLIGENCE
   - Record system activity during user's absence
   - Summarize relevant events, predictions, and insights
   - Alert user to anything that requires their attention

Architecture:
- capture_snapshot(): Save conversation state at end
- restore_context(): Retrieve context when user returns
- get_gap_summary(): Summarize what happened during absence
- get_thread_status(): Show all active conversation threads
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "conversation_continuity"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_DB = DATA_DIR / "snapshots.json"
THREAD_DB = DATA_DIR / "threads.json"


@dataclass
class ContinuitySnapshot:
    """A snapshot of conversation state at a point in time."""
    id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    key_facts: List[str] = field(default_factory=list)
    pending_questions: List[str] = field(default_factory=list)
    emotional_state: Dict[str, Any] = field(default_factory=dict)
    unfinished_tasks: List[str] = field(default_factory=list)
    last_topics: List[str] = field(default_factory=list)
    thread_id: str = "default"


@dataclass
class ConversationThread:
    """A tracked conversation thread."""
    id: str = ""
    name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    snapshot_count: int = 0
    status: str = "active"  # active, paused, archived


class ConversationContinuityManager:
    """
    Preserve conversation context across long gaps.
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
        self._snapshots: Dict[str, ContinuitySnapshot] = {}
        self._threads: Dict[str, ConversationThread] = {}
        self._stats = {"snapshots_taken": 0, "contexts_restored": 0, "gaps_detected": 0}
        self._load_data()

    # ── Snapshot Capture ────────────────────────────────────────────────────

    def capture_snapshot(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Save a conversation state snapshot."""
        thread_id = context.get("thread_id", "default")
        snapshot_id = f"snap_{int(time.time())}"

        snapshot = ContinuitySnapshot(
            id=snapshot_id,
            key_facts=context.get("key_facts", []),
            pending_questions=context.get("pending_questions", []),
            emotional_state=context.get("emotional_state", {}),
            unfinished_tasks=context.get("unfinished_tasks", []),
            last_topics=context.get("last_topics", []),
            thread_id=thread_id,
        )

        with self._lock:
            self._snapshots[snapshot_id] = snapshot
            self._stats["snapshots_taken"] += 1

            # Update thread activity
            if thread_id in self._threads:
                self._threads[thread_id].last_active = datetime.now().isoformat()
                self._threads[thread_id].snapshot_count += 1
            else:
                self._threads[thread_id] = ConversationThread(
                    id=thread_id,
                    name=context.get("thread_name", thread_id),
                )

        self._save_data()
        return {"snapshot_id": snapshot_id, "thread_id": thread_id}

    # ── Context Restoration ─────────────────────────────────────────────────

    def restore_context(self, thread_id: str = "default") -> Dict[str, Any]:
        """Retrieve the most recent context for a thread."""
        thread_snapshots = [
            s for s in self._snapshots.values()
            if s.thread_id == thread_id
        ]

        if not thread_snapshots:
            return {"found": False, "message": "No previous context found"}

        # Get most recent snapshot
        latest = max(thread_snapshots, key=lambda s: s.timestamp)

        self._stats["contexts_restored"] += 1

        return {
            "found": True,
            "thread_id": thread_id,
            "last_active": latest.timestamp,
            "key_facts": latest.key_facts,
            "pending_questions": latest.pending_questions,
            "emotional_state": latest.emotional_state,
            "unfinished_tasks": latest.unfinished_tasks,
            "last_topics": latest.last_topics,
        }

    # ── Gap Detection ───────────────────────────────────────────────────────

    def get_gap_summary(self, thread_id: str = "default",
                        absence_hours: Optional[float] = None) -> Dict[str, Any]:
        """Summarize what happened during user's absence."""
        if absence_hours is None:
            absence_hours = 1.0  # Default 1 hour

        self._stats["gaps_detected"] += 1

        # Get thread snapshots within the absence period
        cutoff = (datetime.now() - timedelta(hours=absence_hours)).isoformat()
        recent_snapshots = [
            s for s in self._snapshots.values()
            if s.thread_id == thread_id and s.timestamp > cutoff
        ]

        if not recent_snapshots:
            return {
                "absence_hours": absence_hours,
                "events": [],
                "summary": "No significant activity while you were away.",
            }

        # Aggregate facts and pending items from recent snapshots
        all_facts = []
        all_pending = []
        for snap in recent_snapshots:
            all_facts.extend(snap.key_facts)
            all_pending.extend(snap.pending_questions)

        return {
            "absence_hours": absence_hours,
            "snapshot_count": len(recent_snapshots),
            "events": list(set(all_facts)),
            "pending_questions": list(set(all_pending)),
            "summary": f"{len(recent_snapshots)} conversation snapshots found from your absence.",
        }

    # ── Thread Management ─────────────────────────────────────────────────

    def get_thread_status(self) -> Dict[str, Any]:
        """Show all active conversation threads."""
        threads = []
        for thread in self._threads.values():
            threads.append({
                "id": thread.id,
                "name": thread.name,
                "last_active": thread.last_active,
                "snapshot_count": thread.snapshot_count,
                "status": thread.status,
            })

        return {
            "active_threads": [t for t in threads if t["status"] == "active"],
            "paused_threads": [t for t in threads if t["status"] == "paused"],
            "total_snapshots": self._stats["snapshots_taken"],
        }

    def create_thread(self, thread_id: str, name: str) -> Dict[str, Any]:
        """Create a new conversation thread."""
        self._threads[thread_id] = ConversationThread(
            id=thread_id,
            name=name,
        )
        self._save_data()
        return {"thread_id": thread_id, "name": name, "status": "created"}

    def pause_thread(self, thread_id: str) -> Dict[str, Any]:
        """Pause a conversation thread."""
        if thread_id in self._threads:
            self._threads[thread_id].status = "paused"
            self._save_data()
            return {"thread_id": thread_id, "status": "paused"}
        return {"error": "Thread not found"}

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_continuity_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "active_threads": sum(1 for t in self._threads.values() if t.status == "active"),
            "total_threads": len(self._threads),
            "total_snapshots": len(self._snapshots),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_data(self):
        try:
            data = {
                "snapshots": {
                    k: {
                        "id": s.id,
                        "timestamp": s.timestamp,
                        "key_facts": s.key_facts,
                        "pending_questions": s.pending_questions,
                        "emotional_state": s.emotional_state,
                        "unfinished_tasks": s.unfinished_tasks,
                        "last_topics": s.last_topics,
                        "thread_id": s.thread_id,
                    }
                    for k, s in self._snapshots.items()
                },
                "threads": {
                    k: {
                        "id": t.id,
                        "name": t.name,
                        "created_at": t.created_at,
                        "last_active": t.last_active,
                        "snapshot_count": t.snapshot_count,
                        "status": t.status,
                    }
                    for k, t in self._threads.items()
                },
                "stats": self._stats,
            }
            SNAPSHOT_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.conversation_continuity")

    def _load_data(self):
        try:
            if SNAPSHOT_DB.exists():
                data = json.loads(SNAPSHOT_DB.read_text())
                for k, s_data in data.get("snapshots", {}).items():
                    self._snapshots[k] = ContinuitySnapshot(**s_data)
                for k, t_data in data.get("threads", {}).items():
                    self._threads[k] = ConversationThread(**t_data)
                self._stats.update(data.get("stats", {}))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.conversation_continuity")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ccm_instance: Optional[ConversationContinuityManager] = None
_ccm_lock = threading.Lock()


def get_conversation_continuity_manager() -> ConversationContinuityManager:
    global _ccm_instance
    with _ccm_lock:
        if _ccm_instance is None:
            _ccm_instance = ConversationContinuityManager()
        return _ccm_instance
