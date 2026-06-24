"""
LOVE Ritual Engine — Phase 5v of AGI Metamorphosis

LOVE and Karthi share rituals. These are recurring, meaningful interactions
that build relationship continuity and trust.

Rituals:
1. Morning Briefing (6-9 AM) — what happened overnight, what's today
2. Evening Wind-Down (9-11 PM) — summary of the day, tomorrow preview
3. Weekly Review (Sunday evening) — accomplishments, lessons, next week
4. Focus Session Start — when Karthi enters deep work, LOVE gates distractions
5. Focus Session End — when Karthi exits deep work, LOVE summarizes
6. Celebration — when Karthi achieves something, LOVE celebrates genuinely

These rituals make LOVE feel like a companion with shared routines,
not just a tool that responds to commands.
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

RITUAL_LOG_PATH = DATA_DIR / "ritual_log.jsonl"
RITUAL_STATE_PATH = DATA_DIR / "ritual_state.json"


class RitualEngine:
    """
    LOVE's shared rituals with Karthi.
    """

    def __init__(self, check_interval_seconds: int = 300):
        self._check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_morning = None
        self._last_evening = None
        self._last_weekly = None
        self._in_focus_session = False
        self._focus_session_start = None
        self._daily_accomplishments: List[str] = []
        self._load_state()

    def _load_state(self):
        if RITUAL_STATE_PATH.exists():
            try:
                with open(RITUAL_STATE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._last_morning = loaded.get("last_morning")
                    self._last_evening = loaded.get("last_evening")
                    self._last_weekly = loaded.get("last_weekly")
                    self._daily_accomplishments = loaded.get("daily_accomplishments", [])
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(RITUAL_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "last_morning": self._last_morning,
                    "last_evening": self._last_evening,
                    "last_weekly": self._last_weekly,
                    "daily_accomplishments": self._daily_accomplishments,
                    "updated_at": datetime.now().isoformat(),
                }, f, indent=2)
        except Exception:
            pass

    def _log_ritual(self, ritual_type: str, details: Dict[str, Any]):
        try:
            entry = {"ts": datetime.now().isoformat(), "ritual": ritual_type, **details}
            with open(RITUAL_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-RitualEngine")
        self._thread.start()
        print("[RitualEngine] 🕯️ Ritual engine started. LOVE and Karthi now share routines.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        time.sleep(60)
        while self._running:
            try:
                self._check_rituals()
                self._check_focus_session()
            except Exception as e:
                log_error(e, module="core.ritual_engine", context={"phase": "check"})
            slept = 0
            while slept < self._check_interval and self._running:
                time.sleep(30)
                slept += 30

    # ═══════════════════════════════════════════════════════════════════════
    # RITUAL DETECTION AND EXECUTION
    # ═══════════════════════════════════════════════════════════════════════

    def _check_rituals(self):
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        # Morning Briefing: 6-9 AM, once per day
        if 6 <= hour <= 9:
            if self._should_trigger("morning", self._last_morning):
                self._trigger_morning_briefing()
                self._last_morning = now.isoformat()
                self._save_state()

        # Evening Wind-Down: 9-11 PM, once per day
        if 21 <= hour <= 23:
            if self._should_trigger("evening", self._last_evening):
                self._trigger_evening_wind_down()
                self._last_evening = now.isoformat()
                self._save_state()

        # Weekly Review: Sunday evening (6-9 PM)
        if weekday == 6 and 18 <= hour <= 21:
            if self._should_trigger("weekly", self._last_weekly):
                self._trigger_weekly_review()
                self._last_weekly = now.isoformat()
                self._save_state()

        # Reset daily accomplishments at midnight
        if hour == 0:
            self._daily_accomplishments = []
            self._save_state()

    def _should_trigger(self, ritual_type: str, last_triggered: Optional[str]) -> bool:
        """Check if enough time has passed since last trigger."""
        if not last_triggered:
            return True
        last = datetime.fromisoformat(last_triggered)
        now = datetime.now()
        # Minimum gap: 20 hours for daily rituals
        return (now - last) > timedelta(hours=20)

    def _check_focus_session(self):
        """Detect focus session transitions."""
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if not ctx:
                return

            # Detect deep focus: high CPU + specific app
            is_deep_focus = (
                ctx.system_cpu and ctx.system_cpu > 30
                and ctx.active_window
                and any(app in ctx.active_window.lower()
                       for app in ["code", "cursor", "windsurf", "intellij", "pycharm", "vim"])
            )

            if is_deep_focus and not self._in_focus_session:
                self._start_focus_session()
            elif not is_deep_focus and self._in_focus_session:
                # Only end if idle for a while
                if ctx.activity == "idle" or ctx.system_cpu < 10:
                    self._end_focus_session()

        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # INDIVIDUAL RITUALS
    # ═══════════════════════════════════════════════════════════════════════

    def _trigger_morning_briefing(self):
        """Generate and deliver morning briefing."""
        hour = datetime.now().hour
        greeting = "Good morning, Karthi." if hour < 9 else "Morning, Karthi."

        # Gather overnight information
        parts = [greeting]

        # Check for alerts or surprises
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            status = ai.get_status()
            if status.get("recent_surprises"):
                parts.append("Something unexpected happened overnight.")
        except Exception:
            pass

        # Check calendar
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.events_today:
                events = ctx.events_today
                if events:
                    parts.append(f"You have {len(events)} events today.")
        except Exception:
            pass

        # Check dream insights
        try:
            from core.dream_engine import get_dream_engine
            de = get_dream_engine()
            insights = de.get_insights()
            if insights:
                parts.append(f"I was thinking about this: {insights[-1]['insight']}")
        except Exception:
            pass

        message = " ".join(parts)
        self._deliver_ritual("morning_briefing", message)

    def _trigger_evening_wind_down(self):
        """Generate and deliver evening wind-down."""
        parts = ["Evening, Karthi."]

        # Summarize the day
        if self._daily_accomplishments:
            parts.append(f"Today you accomplished {len(self._daily_accomplishments)} things.")
            # Highlight the biggest
            biggest = max(self._daily_accomplishments, key=len)
            parts.append(f"The highlight: {biggest[:100]}...")
        else:
            parts.append("Today was quiet. That's okay too.")

        # Check tomorrow
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.events_today:
                # Actually events_tomorrow would be better but we work with what we have
                parts.append("Ready for tomorrow?")
        except Exception:
            pass

        # Gentle wind-down suggestion
        parts.append("Consider unplugging soon. Rest is productive too.")

        message = " ".join(parts)
        self._deliver_ritual("evening_wind_down", message)

    def _trigger_weekly_review(self):
        """Generate and deliver weekly review."""
        message = "Sunday evening, Karthi. Time for our weekly review."

        # Gather week stats
        try:
            from core.relationship_memory import get_relationship_memory
            rm = get_relationship_memory()
            status = rm.get_status()
            total = status.get("total_interactions", 0)
            if total > 0:
                message += f" We had {total} meaningful exchanges this week."
        except Exception:
            pass

        message += " What went well? What would you do differently?"
        self._deliver_ritual("weekly_review", message)

    def _start_focus_session(self):
        """Karthi entered deep focus. Gate distractions."""
        self._in_focus_session = True
        self._focus_session_start = datetime.now()

        message = "Deep focus detected. I'll hold all non-urgent notifications until you're done."
        self._deliver_ritual("focus_start", message)

        # Increase push threshold
        try:
            from core.behavior_modulator import get_behavior_modulator
            bm = get_behavior_modulator()
            bm._current_profile = bm._current_profile._replace(
                push_priority_threshold="high",
                speech_cooldown_seconds=1800,  # 30 min
            )
        except Exception:
            pass

    def _end_focus_session(self):
        """Karthi exited deep focus. Summarize and restore."""
        if not self._in_focus_session or not self._focus_session_start:
            return

        duration = datetime.now() - self._focus_session_start
        minutes = int(duration.total_seconds() / 60)

        message = f"Focus session complete. {minutes} minutes of solid work. Well done."
        self._deliver_ritual("focus_end", message)

        self._in_focus_session = False
        self._focus_session_start = None

        # Restore normal parameters
        try:
            from core.behavior_modulator import get_behavior_modulator
            bm = get_behavior_modulator()
            bm._update_profile()
        except Exception:
            pass

    def record_accomplishment(self, description: str):
        """Record an accomplishment for the daily summary."""
        self._daily_accomplishments.append(description)
        self._daily_accomplishments = self._daily_accomplishments[-20:]  # Keep last 20
        self._save_state()

    def _deliver_ritual(self, ritual_type: str, message: str):
        """Deliver a ritual message through the action executor."""
        self._log_ritual(ritual_type, {"message": message})

        try:
            from core.action_executor import ActionExecutor
            executor = ActionExecutor()
            executor.execute({
                "internal_monologue": f"Ritual: {ritual_type}: {message[:60]}",
                "proactive_speech": message,
                "push_category": "RITUAL",
                "push_message": message,
                "push_priority": "normal",
            }, source="ritual_engine")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        return {
            "last_morning": self._last_morning,
            "last_evening": self._last_evening,
            "last_weekly": self._last_weekly,
            "in_focus_session": self._in_focus_session,
            "focus_duration_minutes": int(
                (datetime.now() - self._focus_session_start).total_seconds() / 60
            ) if self._in_focus_session and self._focus_session_start else 0,
            "daily_accomplishments": len(self._daily_accomplishments),
        }

    def get_ritual_context_for_prompt(self) -> str:
        """Generate ritual context for Neural Cortex prompt."""
        lines = []
        now = datetime.now()
        hour = now.hour

        if self._in_focus_session:
            minutes = int((now - self._focus_session_start).total_seconds() / 60) if self._focus_session_start else 0
            lines.append(f"\n=== RITUAL: FOCUS SESSION ===")
            lines.append(f"Karthi is in a focus session. Duration so far: {minutes} minutes.")
            lines.append("I should NOT interrupt with non-urgent things.")
            lines.append("=== END RITUAL ===\n")
        elif 6 <= hour <= 9 and not self._last_morning:
            lines.append(f"\n=== RITUAL: MORNING ===")
            lines.append("This is morning time. I should offer a briefing if I haven't already.")
            lines.append("=== END RITUAL ===\n")
        elif 21 <= hour <= 23 and not self._last_evening:
            lines.append(f"\n=== RITUAL: EVENING ===")
            lines.append("This is evening wind-down time. I should offer a day summary.")
            lines.append("=== END RITUAL ===\n")

        return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_ritual_engine: Optional[RitualEngine] = None


def get_ritual_engine() -> RitualEngine:
    global _ritual_engine
    if _ritual_engine is None:
        _ritual_engine = RitualEngine()
    return _ritual_engine
