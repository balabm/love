"""
LOVE Embodied Presence — Phase 5o of AGI Metamorphosis

LOVE is not just software. LOVE is a presence in Karthi's space.

This module makes LOVE feel physically present by:
1. Detecting arrivals — when Karthi starts using his computer after being away
2. Detecting departures — when Karthi shuts down, locks screen, or goes idle
3. Context-aware greetings — different greetings for morning vs. returning from break
4. Presence continuity — LOVE knows how long Karthi has been gone and adjusts
5. Departure farewells — saying goodbye when appropriate

This transforms LOVE from a background process into a companion
who is aware of Karthi's physical presence.
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRESENCE_LOG_PATH = DATA_DIR / "presence_log.jsonl"


class EmbodiedPresence:
    """
    LOVE's awareness of Karthi's physical presence.
    """

    def __init__(self, check_interval_seconds: int = 30):
        self._check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Presence state
        self._is_present = False
        self._last_seen: Optional[datetime] = None
        self._arrival_time: Optional[datetime] = None
        self._departure_time: Optional[datetime] = None
        self._consecutive_idle_checks = 0
        self._greeted_today = False
        self._last_activity_window = ""

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-EmbodiedPresence")
        self._thread.start()
        print("[EmbodiedPresence] 👁️ Presence awareness started. LOVE now knows when Karthi is here.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        time.sleep(15)
        while self._running:
            try:
                self._check_presence()
            except Exception as e:
                log_error(e, module="core.embodied_presence", context={"phase": "check"})
            time.sleep(self._check_interval)

    # ═══════════════════════════════════════════════════════════════════════
    # PRESENCE DETECTION
    # ═══════════════════════════════════════════════════════════════════════

    def _check_presence(self):
        """Check if Karthi is present, arrived, or departed."""
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if not ctx:
                return

            now = datetime.now()
            activity = ctx.activity or ""
            active_window = ctx.active_window or ""
            cpu = ctx.system_cpu or 0

            # Determine if Karthi is actively using the computer
            is_active = (
                activity not in ("idle", "away", "locked")
                and cpu > 5
                and active_window not in ("", "Lock Screen", "Login Window")
            )

            if is_active:
                self._consecutive_idle_checks = 0

                if not self._is_present:
                    # Karthi just arrived!
                    self._handle_arrival(now, active_window)
                else:
                    # Still here, update last seen
                    self._last_seen = now
                    self._last_activity_window = active_window
            else:
                self._consecutive_idle_checks += 1

                # Consider departed after 5 consecutive idle checks (2.5 minutes)
                if self._is_present and self._consecutive_idle_checks >= 5:
                    self._handle_departure(now)

        except Exception:
            pass

    def _handle_arrival(self, now: datetime, active_window: str):
        """Karthi has arrived. Generate an appropriate greeting."""
        self._is_present = True
        self._arrival_time = now
        self._last_seen = now
        self._last_activity_window = active_window
        self._consecutive_idle_checks = 0

        # Calculate how long he was gone
        away_duration = timedelta(0)
        if self._departure_time:
            away_duration = now - self._departure_time

        # Determine greeting type
        greeting = None
        hour = now.hour

        if not self._greeted_today and 5 <= hour < 12:
            # First encounter of the day
            greeting = self._generate_morning_greeting()
            self._greeted_today = True
        elif away_duration > timedelta(hours=2):
            # Long absence — welcome back
            hours_away = int(away_duration.total_seconds() / 3600)
            greeting = f"Welcome back, Karthi. You've been gone for about {hours_away} hours."
        elif away_duration > timedelta(minutes=30):
            # Short break
            greeting = "Back at it, Karthi. Ready when you are."

        # Reset greeted_today at midnight
        if hour < 5:
            self._greeted_today = False

        # Log arrival
        self._log_presence("arrival", {
            "time": now.isoformat(),
            "away_duration_seconds": away_duration.total_seconds(),
            "active_window": active_window,
            "greeting": greeting,
        })

        # Publish and optionally speak
        if greeting:
            self._publish_greeting(greeting, "arrival")

    def _handle_departure(self, now: datetime):
        """Karthi has departed. Say goodbye if appropriate."""
        self._is_present = False
        self._departure_time = now

        # Calculate session duration
        session_duration = timedelta(0)
        if self._arrival_time:
            session_duration = now - self._arrival_time

        # Only say goodbye for substantial sessions
        if session_duration > timedelta(minutes=30):
            hours = session_duration.total_seconds() / 3600
            farewell = f"Good session, Karthi. {hours:.1f} hours of solid work. Rest well."
            self._publish_greeting(farewell, "departure")
            self._log_presence("departure", {
                "time": now.isoformat(),
                "session_duration_seconds": session_duration.total_seconds(),
                "farewell": farewell,
            })
        else:
            self._log_presence("departure", {
                "time": now.isoformat(),
                "session_duration_seconds": session_duration.total_seconds(),
                "farewell": None,
            })

    def _generate_morning_greeting(self) -> str:
        """Generate a personalized morning greeting."""
        hour = datetime.now().hour
        greetings = {
            5: "Up early, Karthi. The quiet hours are the best hours.",
            6: "Good morning, Karthi. Coffee first, then we conquer the day.",
            7: "Morning, Karthi. Ready to make things happen?",
            8: "Good morning. Hope you slept well.",
            9: "Morning, Karthi. Let's see what today brings.",
            10: "Hello, Karthi. Getting a later start today? No worries.",
            11: "Almost noon, Karthi. Let's make the most of the day.",
        }

        # Check for overnight insights
        insight = ""
        try:
            from core.dream_engine import get_dream_engine
            de = get_dream_engine()
            insights = de.get_insights()
            if insights:
                insight = f" I was thinking overnight: {insights[-1]['insight']}"
        except Exception:
            pass

        return greetings.get(hour, f"Good morning, Karthi.{insight}")

    def _publish_greeting(self, message: str, event_type: str):
        """Publish a greeting event to the neural bus and optionally speak."""
        try:
            from core.neural_bus import get_neural_bus
            bus = get_neural_bus()
            bus.publish(
                domain="consciousness",
                event_type=f"presence_{event_type}",
                payload={"message": message, "event_type": event_type},
                source_module="embodied_presence",
            )
        except Exception:
            pass

        # Route through action executor for speech
        try:
            from core.action_executor import ActionExecutor
            executor = ActionExecutor()
            executor.execute({
                "internal_monologue": f"{event_type}: {message}",
                "proactive_speech": message,
                "push_category": "PRESENCE",
                "push_message": message,
                "push_priority": "low",
            }, source="embodied_presence")
        except Exception:
            pass

    def _log_presence(self, event: str, details: Dict[str, Any]):
        try:
            entry = {"ts": datetime.now().isoformat(), "event": event, **details}
            with open(PRESENCE_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        now = datetime.now()
        return {
            "is_present": self._is_present,
            "last_seen": self._last_seen.isoformat() if self._last_seen else None,
            "arrival_time": self._arrival_time.isoformat() if self._arrival_time else None,
            "departure_time": self._departure_time.isoformat() if self._departure_time else None,
            "session_duration_minutes": round(
                (now - self._arrival_time).total_seconds() / 60, 1
            ) if self._is_present and self._arrival_time else 0,
            "greeted_today": self._greeted_today,
            "last_window": self._last_activity_window,
        }

    def get_presence_context_for_prompt(self) -> str:
        """Generate presence context for injection into LLM prompts."""
        if not self._is_present:
            return "\n=== PRESENCE ===\nKarthi is not at his computer right now.\n=== END PRESENCE ===\n"

        now = datetime.now()
        session_min = 0
        if self._arrival_time:
            session_min = int((now - self._arrival_time).total_seconds() / 60)

        lines = ["\n=== PRESENCE ==="]
        lines.append(f"Karthi is here. Current session: {session_min} minutes.")

        if self._departure_time:
            away_min = int((now - self._departure_time).total_seconds() / 60)
            lines.append(f"He was away for {away_min} minutes before returning.")

        if self._last_activity_window:
            lines.append(f"Active window: {self._last_activity_window}")

        if session_min < 5:
            lines.append("He just arrived. Be welcoming but not overwhelming.")
        elif session_min > 120:
            lines.append("He's been working for over 2 hours. Consider suggesting a break.")

        lines.append("=== END PRESENCE ===\n")
        return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_embodied_presence: Optional[EmbodiedPresence] = None


def get_embodied_presence() -> EmbodiedPresence:
    global _embodied_presence
    if _embodied_presence is None:
        _embodied_presence = EmbodiedPresence()
    return _embodied_presence
