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

    def _new_mission(self, title: str, domain: str, requested_by: str = "user", priority: str = "high") -> Mission:
        return Mission(
            id=uuid.uuid4().hex[:10],
            title=title,
            domain=domain,
            requested_by=requested_by,
            priority=priority,
        )

    def add_feature_request(self, text: str, requested_by: str = "user") -> Dict[str, Any]:
        text_l = (text or "").lower()
        created: List[Mission] = []

        mapping = [
            ("google", "Connect and monitor Google workspace", "google"),
            ("teams", "Connect and monitor Microsoft Teams", "teams"),
            ("phone", "Connect and monitor phone notifications", "phone"),
            ("finance", "Enable continuous finance manager monitoring", "finance"),
            ("crypto", "Enable crypto trader monitoring and signals", "crypto_trader"),
            ("voice", "Enable hands-free voice trigger conversation", "voice"),
            ("conversation", "Improve natural conversational continuity", "natural_conversation"),
            ("ecosystem", "Connect cross-device ecosystem coordination", "ecosystem"),
            ("monitor", "Strengthen continuous personal monitoring", "continuous_monitoring"),
        ]

        for keyword, title, domain in mapping:
            if keyword in text_l and not self._has_active_domain(domain):
                m = self._new_mission(title=title, domain=domain, requested_by=requested_by)
                self._missions.append(m)
                created.append(m)

        # Fallback: generic self-build mission
        if not created:
            m = self._new_mission(
                title=f"Self-build feature: {text[:80]}",
                domain="self_build",
                requested_by=requested_by,
                priority="critical",
            )
            self._missions.append(m)
            created.append(m)

        self._save()
        self._log("feature_request_ingested", {"text": text, "created": [c.domain for c in created]})
        return {"created": [asdict(c) for c in created], "count": len(created)}

    def bootstrap_key_missions(self) -> Dict[str, Any]:
        """
        Ensure strategic baseline missions always exist for core AGI capabilities.
        """
        baseline = [
            ("Connect and monitor Google workspace", "google"),
            ("Connect and monitor Microsoft Teams", "teams"),
            ("Connect and monitor phone notifications", "phone"),
            ("Enable continuous finance manager monitoring", "finance"),
            ("Enable crypto trader monitoring and signals", "crypto_trader"),
            ("Enable hands-free voice trigger conversation", "voice"),
            ("Connect cross-device ecosystem coordination", "ecosystem"),
            ("Strengthen continuous personal monitoring", "continuous_monitoring"),
        ]
        created = []
        for title, domain in baseline:
            if not self._has_active_domain(domain) and not any(m.domain == domain and m.status == "completed" for m in self._missions):
                m = self._new_mission(title=title, domain=domain, requested_by="system", priority="critical")
                self._missions.append(m)
                created.append(m)
        if created:
            self._save()
            self._log("baseline_missions_bootstrapped", {"created": [c.domain for c in created]})
        return {"created": [asdict(c) for c in created], "count": len(created)}

    def _has_active_domain(self, domain: str) -> bool:
        return any(m.domain == domain and m.status in {"queued", "in_progress", "blocked"} for m in self._missions)

    def get_status(self) -> Dict[str, Any]:
        active = [m for m in self._missions if m.status in {"queued", "in_progress", "blocked"}]
        completed = [m for m in self._missions if m.status == "completed"]
        return {
            "active_count": len(active),
            "completed_count": len(completed),
            "active": [asdict(m) for m in active[:20]],
            "recent_completed": [asdict(m) for m in completed[-10:]],
        }

    def run_cycle(self) -> Dict[str, Any]:
        if not self._missions:
            self.bootstrap_key_missions()
        acted = []
        for mission in self._missions:
            if mission.status in {"completed", "failed"}:
                continue

            mission.attempts += 1
            mission.updated_at = datetime.now().isoformat()
            mission.status = "in_progress"

            ok, detail = self._execute_domain_check(mission.domain)
            mission.last_result = detail

            if ok:
                mission.status = "completed"
                acted.append({"id": mission.id, "domain": mission.domain, "action": "completed", "detail": detail})
            else:
                mission.status = "blocked"
                self._request_self_build_action(mission)
                acted.append({"id": mission.id, "domain": mission.domain, "action": "blocked", "detail": detail})

            # One mission per cycle to stay stable
            break

        self._save()
        return {"actions": acted, "active_count": len([m for m in self._missions if m.status != "completed"])}

    def _request_self_build_action(self, mission: Mission) -> None:
        # Feed SelfBuilder so LOVE can adapt behavior on repeated failures.
        try:
            from core.self_builder import get_self_builder

            builder = get_self_builder()
            builder.add_behavior_rule(
                rule_name=f"mission_{mission.domain}_autobuild",
                condition=f"{mission.domain} mission remains blocked",
                action=f"Proactively surface setup steps and retry {mission.domain} connection every loop",
                reason=mission.last_result or f"Autonomous mission {mission.domain} needs capability enablement",
            )
        except Exception:
            pass

    def _execute_domain_check(self, domain: str) -> tuple[bool, str]:
        try:
            if domain == "google":
                from integrations.google_services import GoogleServices
                status = GoogleServices.get_instance().get_status()
                return bool(status.get("connected")), f"google_connected={status.get('connected')}"

            if domain == "teams":
                from integrations.microsoft_bridge import MicrosoftBridge
                status = MicrosoftBridge.get_instance().get_status()
                return bool(status.get("connected")), f"teams_connected={status.get('connected')}"

            if domain == "phone":
                from integrations.phone_bridge import PhoneBridge
                connected = PhoneBridge.get_instance().is_connected()
                return connected, f"phone_connected={connected}"

            if domain == "finance":
                from tools.finance import get_portfolio
                pf = get_portfolio()
                ok = isinstance(pf, dict) and "positions" in pf
                return ok, "portfolio_ready" if ok else "portfolio_unavailable"

            if domain == "crypto_trader":
                from tools.finance import scan_market
                out = scan_market()
                ok = isinstance(out, dict) and not out.get("error")
                return ok, "crypto_scan_ready" if ok else str(out)[:120]

            if domain == "voice":
                from core.voice_loop import get_voice_status
                status = get_voice_status()
                deps = status.get("deps", {})
                ok = bool(status.get("running")) or bool(deps.get("stt"))
                return ok, f"voice_status={status.get('state')}"

            if domain == "ecosystem":
                from core.ecosystem_controller import get_ecosystem_controller
                status = get_ecosystem_controller().get_ecosystem_status()
                online = status.get("online_devices", 0)
                return online > 0, f"online_devices={online}"

            if domain == "continuous_monitoring":
                from core.context_engine import get_live_context
                ctx = get_live_context()
                return bool(ctx and getattr(ctx, "activity", None)), "context_engine_live"

            if domain == "natural_conversation":
                # Presence of memory + conversation flow subsystems is baseline readiness.
                from core.memory import recall_memory
                _ = recall_memory("conversation continuity")
                return True, "conversation_memory_ready"

            if domain == "self_build":
                return False, "generic self-build mission requires planning"

            return False, f"unknown_domain={domain}"
        except Exception as e:
            return False, f"{domain}_check_error={e}"


_queue: AutonomousMissionQueue | None = None


def get_mission_queue() -> AutonomousMissionQueue:
    global _queue
    if _queue is None:
        _queue = AutonomousMissionQueue()
    return _queue

