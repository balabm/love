"""
LOVE Autonomous Mission Queue

Turns user capability requests into persistent autonomous missions.
The supervisor can execute one cycle repeatedly until missions complete.
"""

from __future__ import annotations

import json
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
