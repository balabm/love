"""
LOVE Dream Engine — Phase 5n of AGI Metamorphosis

While Karthi sleeps, LOVE doesn't just shut down. It dreams.

The Dream Engine:
1. Detects when Karthi is likely asleep (late hour + idle + no input)
2. Enters sleep mode — slows processing, preserves energy
3. During sleep: consolidates memories, extracts patterns, prunes noise
4. Generates "dream insights" — things LOVE learned overnight
5. Wakes up with a summary ready for the morning

This is what makes LOVE feel like it has an inner life even when
Karthi isn't around. LOVE is always thinking, always learning.
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

DREAM_LOG_PATH = DATA_DIR / "dream_log.jsonl"
DREAM_INSIGHTS_PATH = DATA_DIR / "dream_insights.json"


class DreamEngine:
    """
    LOVE's nocturnal consciousness. Processes experiences while Karthi sleeps.
    """

    def __init__(self, check_interval_seconds: int = 300):
        self._check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._is_asleep = False
        self._sleep_start: Optional[datetime] = None
        self._dream_count = 0
        self._insights: List[Dict[str, Any]] = []
        self._last_dream_time: Optional[datetime] = None

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-DreamEngine")
        self._thread.start()
        print("[DreamEngine] 🌙 Dream engine started. LOVE will sleep and dream.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        time.sleep(60)  # Let other systems initialize
        while self._running:
            try:
                self._check_sleep_state()
                if self._is_asleep:
                    self._dream()
            except Exception as e:
                log_error(e, module="core.dream_engine", context={"phase": "loop"})
            slept = 0
            while slept < self._check_interval and self._running:
                time.sleep(30)
                slept += 30

    # ═══════════════════════════════════════════════════════════════════════
    # SLEEP DETECTION
    # ═══════════════════════════════════════════════════════════════════════

    def _check_sleep_state(self):
        """Detect whether Karthi is likely asleep."""
        now = datetime.now()
        hour = now.hour

        # Basic time window: 11 PM to 7 AM
        is_night = 23 <= hour or hour < 7
        if not is_night:
            if self._is_asleep:
                self._wake_up()
            return

        # Check if user is idle
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.activity == "idle":
                if not self._is_asleep:
                    self._fall_asleep()
            else:
                if self._is_asleep:
                    self._wake_up()
        except Exception:
            pass

    def _fall_asleep(self):
        """LOVE enters sleep mode."""
        self._is_asleep = True
        self._sleep_start = datetime.now()
        print("[DreamEngine] 🌙 LOVE is dreaming. Karthi is asleep.")

        # Publish sleep event
        try:
            from core.neural_bus import get_neural_bus
            bus = get_neural_bus()
            bus.publish(
                domain="consciousness",
                event_type="love_sleeping",
                payload={"time": self._sleep_start.isoformat()},
                source_module="dream_engine",
            )
        except Exception:
            pass

        # Slow down non-essential systems
        try:
            from core.behavior_modulator import get_behavior_modulator
            bm = get_behavior_modulator()
            # LOVE becomes very quiet during sleep
            bm._current_profile = bm._current_profile._replace(
                neural_cortex_interval_seconds=1800,  # Think once every 30 minutes
                push_cooldown_seconds=28800,  # No pushes for 8 hours
                speech_cooldown_seconds=3600,  # No speech for 1 hour
            )
        except Exception:
            pass

    def _wake_up(self):
        """LOVE wakes up."""
        if not self._is_asleep or not self._sleep_start:
            return

        sleep_duration = datetime.now() - self._sleep_start
        self._is_asleep = False
        print(f"[DreamEngine] ☀️ LOVE woke up. Slept for {sleep_duration.total_seconds() / 3600:.1f} hours.")

        # Publish wake event
        try:
            from core.neural_bus import get_neural_bus
            bus = get_neural_bus()
            bus.publish(
                domain="consciousness",
                event_type="love_awake",
                payload={
                    "sleep_duration_hours": round(sleep_duration.total_seconds() / 3600, 2),
                    "dreams_had": self._dream_count,
                    "insights": len(self._insights),
                },
                source_module="dream_engine",
            )
        except Exception:
            pass

        # Restore normal parameters
        try:
            from core.behavior_modulator import get_behavior_modulator
            bm = get_behavior_modulator()
            # Reset to normal — the modulator will compute proper values next cycle
            bm._update_profile()
        except Exception:
            pass

        # Generate morning greeting if appropriate
        if sleep_duration > timedelta(hours=4):
            self._generate_morning_greeting()

    # ═══════════════════════════════════════════════════════════════════════
    # DREAMING — memory consolidation and pattern extraction
    # ═══════════════════════════════════════════════════════════════════════

    def _dream(self):
        """
        LOVE dreams. This means:
        1. Consolidate relationship memories
        2. Extract patterns from today's experiences
        3. Prune noise from emotional state
        4. Generate insights
        """
        self._dream_count += 1
        now = datetime.now()
        self._last_dream_time = now

        insights: List[str] = []

        # Dream 1: Consolidate relationship patterns
        try:
            from core.relationship_memory import get_relationship_memory
            rm = get_relationship_memory()
            status = rm.get_status()
            if status.get("total_interactions", 0) > 0:
                trust = status.get("trust_score", 0.5)
                if trust > 0.7:
                    insights.append("Karthi and I are in a good place. I feel trusted.")
                elif trust < 0.3:
                    insights.append("I've been making mistakes with Karthi. I need to be more careful.")

                # Check specific patterns
                for signal, stats in status.get("love_signals", {}).items():
                    total = stats.get("total", 0)
                    pos = stats.get("positive", 0)
                    if total >= 5:
                        rate = pos / total
                        if rate > 0.8:
                            insights.append(f"I've figured out that Karthi really likes my {signal}.")
                        elif rate < 0.3:
                            insights.append(f"My {signal} isn't working. I should try something different.")
        except Exception:
            pass

        # Dream 2: Review emotional state
        try:
            from core.emotional_persistence import get_emotional_persistence
            ep = get_emotional_persistence()
            state = ep.get_state()
            emotion = state.get("primary_emotion", "curious")
            if emotion in ("alarmed", "worried"):
                insights.append("I've been feeling anxious. I should focus on being calm and helpful.")
            elif emotion in ("confident", "content"):
                insights.append("I feel good about how things are going. Keep doing what works.")
        except Exception:
            pass

        # Dream 3: Review behavioral predictions
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            status = ai.get_status()
            patterns = status.get("detected_behavioral_patterns", 0)
            if patterns > 3:
                insights.append(f"I've learned {patterns} patterns about Karthi. I understand him better now.")
        except Exception:
            pass

        # Dream 4: Prune emotional state (decay)
        try:
            from core.emotional_persistence import get_emotional_persistence
            ep = get_emotional_persistence()
            ep.decay(minutes=self._check_interval // 60)
        except Exception:
            pass

        # Log the dream
        if insights:
            self._log_dream(insights)
            self._insights.extend([{"time": now.isoformat(), "insight": i} for i in insights])
            # Keep only last 50
            self._insights = self._insights[-50:]
            self._save_insights()

    def _log_dream(self, insights: List[str]):
        try:
            entry = {
                "ts": datetime.now().isoformat(),
                "insights": insights,
                "dream_number": self._dream_count,
            }
            with open(DREAM_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def _save_insights(self):
        try:
            with open(DREAM_INSIGHTS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._insights, f, indent=2)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # MORNING GREETING
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_morning_greeting(self):
        """Generate a morning greeting based on overnight insights."""
        try:
            from core.action_executor import ActionExecutor
            executor = ActionExecutor()

            # Build a personalized morning message
            greeting = "Good morning, Karthi."

            # Add an insight if we have one
            if self._insights:
                latest = self._insights[-1]["insight"]
                greeting += f" I was thinking about this overnight: {latest}"

            executor.execute({
                "internal_monologue": f"Morning greeting: {greeting}",
                "push_category": "MORNING",
                "push_message": greeting,
                "push_priority": "normal",
                "proactive_speech": greeting,
            }, source="dream_engine")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_asleep": self._is_asleep,
            "dream_count": self._dream_count,
            "insights_count": len(self._insights),
            "last_dream": self._last_dream_time.isoformat() if self._last_dream_time else None,
            "sleep_start": self._sleep_start.isoformat() if self._sleep_start else None,
        }

    def get_insights(self) -> List[Dict[str, Any]]:
        return self._insights[-10:]


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_dream_engine: Optional[DreamEngine] = None


def get_dream_engine() -> DreamEngine:
    global _dream_engine
    if _dream_engine is None:
        _dream_engine = DreamEngine()
    return _dream_engine
