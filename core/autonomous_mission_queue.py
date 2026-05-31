"""
LOVE Autonomous Mission Queue

Turns user capability requests into persistent autonomous missions.
The supervisor can execute one cycle repeatedly until missions complete.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).parent.parent / "data"
MISSION_DIR = DATA_DIR / "autonomous_missions"
MISSION_FILE = MISSION_DIR / "missions.json"
MISSION_LOG = MISSION_DIR / "mission_log.jsonl"
MISSION_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Mission:
    id: str
    title: str
    domain: str
    requested_by: str = "user"
    status: str = "queued"  # queued | in_progress | blocked | completed | failed
    priority: str = "high"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    attempts: int = 0
    last_result: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutonomousMissionQueue:
    def __init__(self) -> None:
        self._missions: List[Mission] = []
        self._load()

    def _load(self) -> None:
        try:
            if MISSION_FILE.exists():
                raw = json.loads(MISSION_FILE.read_text(encoding="utf-8"))
                self._missions = [Mission(**m) for m in raw]
        except Exception:
            self._missions = []

    def _save(self) -> None:
        MISSION_FILE.write_text(
            json.dumps([asdict(m) for m in self._missions], indent=2),
            encoding="utf-8",
        )

    def _log(self, event: str, data: Dict[str, Any]) -> None:
        rec = {"ts": datetime.now().isoformat(), "event": event, "data": data}
        try:
            with open(MISSION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception:
            pass

    def get_missions(self, status: str = '', limit: int = 50):
        if status:
            return [m for m in self._missions if m.status == status][:limit]
        return self._missions[:limit]

    def add_mission(self, title: str, domain: str, priority: str = 'high', metadata=None):
        import uuid
        m = Mission(
            id=str(uuid.uuid4())[:8],
            title=title,
            domain=domain,
            priority=priority,
            metadata=metadata or {},
        )
        self._missions.append(m)
        self._save()
        self._log('added', {'id': m.id, 'title': m.title})
        return m

    def update_mission(self, mission_id: str, status: str = '', last_result: str = '', metadata=None) -> bool:
        for m in self._missions:
            if m.id == mission_id:
                if status:
                    m.status = status
                if last_result:
                    m.last_result = last_result
                if metadata:
                    m.metadata.update(metadata)
                m.updated_at = datetime.now().isoformat()
                m.attempts += 1
                self._save()
                self._log('updated', {'id': m.id, 'status': m.status})
                return True
        return False


# Singleton
_mission_queue_instance = None
_mission_queue_lock = threading.Lock()


def get_mission_queue():
    global _mission_queue_instance
    with _mission_queue_lock:
        if _mission_queue_instance is None:
            _mission_queue_instance = AutonomousMissionQueue()
        return _mission_queue_instance
