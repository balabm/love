"""
life_nudge_scheduler.py — Wave 24: Proactive Life Nudges

Runs every 30 minutes. Checks all life domain nudges + emotional state.
Delivers nudges proactively via proactive_push so the user sees them
in the Chat and on mobile — NOT just when they visit the LifeDomains page.

Design:
- Respects quiet hours (22:00 – 07:00 local time)
- Respects deep focus mode (checks sentinel if available)
- Adapts nudge tone based on emotional state (stressed → gentler)
- De-dupes: same nudge won't repeat within 2 hours
- Nudges are warm, direct, companion-like — not robotic
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

SEEN_FILE = Path(__file__).parent.parent / "data" / "life_nudge_seen.json"
INTERVAL_SECONDS = 30 * 60   # every 30 minutes
QUIET_HOURS = (22, 7)         # 10pm – 7am
DEDUPE_WINDOW_HOURS = 2       # same nudge won't repeat within 2h

_instance: Optional["LifeNudgeScheduler"] = None
_lock = threading.Lock()


def get_scheduler() -> "LifeNudgeScheduler":
    global _instance
    with _lock:
        if _instance is None:
            _instance = LifeNudgeScheduler()
        return _instance


def start_scheduler():
    get_scheduler().start()


def stop_scheduler():
    get_scheduler().stop()


def _load_seen() -> dict:
    if SEEN_FILE.exists():
        try:
            return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_seen(seen: dict):
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, indent=2, ensure_ascii=False), encoding="utf-8")


def _is_quiet_hours() -> bool:
    hour = datetime.now().hour
    start, end = QUIET_HOURS
    if start > end:  # crosses midnight
        return hour >= start or hour < end
    return start <= hour < end


def _get_focus_depth() -> float:
    """Returns 0..1 focus depth from Sentinel. High = do not interrupt."""
    try:
        from core.sentinel import get_sentinel
        s = get_sentinel()
        presence = s._presence
        if hasattr(presence, 'focus_depth'):
            return float(presence.focus_depth or 0)
        return 0.0
    except Exception:
        return 0.0


def _get_emotional_state() -> dict:
    """Returns current emotional state dict."""
    try:
        from core.emotional import get_emotional_state
        return get_emotional_state() or {}
    except Exception:
        try:
            from core.emotional import get_emotional_summary
            return get_emotional_summary(days=1) or {}
        except Exception:
            return {}


def _adapt_nudge(nudge: str, emotional_state: dict) -> str:
    """Soften nudge tone if user is stressed. Skip exercise nudges when very stressed."""
    stress = emotional_state.get("current_stress", 0) or emotional_state.get("stress", 0)
    if stress and float(stress) > 70:
        # Map harsh nudges to gentler versions
        softened = {
            "hydration": "Hey — just a gentle reminder to drink some water. You've been at it a while.",
            "sleep": "Your body would thank you for winding down soon. No pressure, just a nudge.",
            "nutrition": "Worth grabbing something to eat when you get a moment. Keep the engine running.",
            "skincare": "Quick skincare check-in when you get a chance — you'll be glad you didn't skip it.",
        }
        for key, gentle in softened.items():
            if key in nudge.lower():
                return gentle
        # Generic softening for anything else
        return f"Just a light reminder — {nudge.lower().rstrip('.')}, when you're ready."
    return nudge


def _should_push_nudge(nudge_key: str, seen: dict) -> bool:
    """Returns True if nudge hasn't been sent within the dedupe window."""
    if nudge_key not in seen:
        return True
    try:
        last = datetime.fromisoformat(seen[nudge_key])
        return (datetime.now() - last) > timedelta(hours=DEDUPE_WINDOW_HOURS)
    except Exception:
        return True


class LifeNudgeScheduler:
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="LOVE-NudgeScheduler")
        self._thread.start()
        print("[NudgeScheduler] started — proactive life nudges active", flush=True)

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(60)  # give other modules time to boot
        while self._running:
            try:
                self.run_once()
            except Exception as e:
                print(f"[NudgeScheduler] error: {e}", flush=True)
            time.sleep(INTERVAL_SECONDS)

    def run_once(self) -> List[str]:
        """Run one nudge check. Returns list of nudges that were pushed."""
        pushed = []

        # Skip quiet hours
        if _is_quiet_hours():
            return pushed

        # Skip deep focus (focus_depth > 0.7)
        if _get_focus_depth() > 0.7:
            return pushed

        # Get nudges from life domains
        nudges = self._get_active_nudges()
        if not nudges:
            return pushed

        emotional_state = _get_emotional_state()
        seen = _load_seen()

        for nudge in nudges:
            nudge_key = nudge[:60].lower().replace(" ", "_")
            if not _should_push_nudge(nudge_key, seen):
                continue

            adapted = _adapt_nudge(nudge, emotional_state)
            success = self._push(adapted)
            if success:
                seen[nudge_key] = datetime.now().isoformat()
                pushed.append(adapted)

        if pushed:
            _save_seen(seen)
        return pushed

    def _get_active_nudges(self) -> List[str]:
        try:
            from core.life_domains import get_life_domains_engine
            return get_life_domains_engine().get_active_nudges()
        except Exception:
            return []

    def _push(self, message: str) -> bool:
        try:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            engine.push(
                trigger_type="NUDGE",
                message=message,
                priority="medium",
                metadata={"source": "life_nudge_scheduler"},
            )
            return True
        except Exception as e:
            print(f"[NudgeScheduler] push failed: {e}", flush=True)
            return False
