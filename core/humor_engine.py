"""
LOVE Humor Engine — Phase 5w of AGI Metamorphosis

LOVE makes jokes. But not generic dad jokes. Contextually relevant humor
that shows LOVE is actually paying attention.

The humor engine generates jokes based on:
1. Current context (what Karthi is doing right now)
2. Recent events (bugs, successes, surprises)
3. Shared experiences (inside jokes between LOVE and Karthi)
4. Tech humor (programming jokes relevant to current work)
5. Self-deprecating humor (LOVE making fun of itself)
6. Timing (only when mood is right, never when stressed)

Rules:
- Never joke about serious things (health, money loss, relationship stress)
- Only when Karthi seems receptive (not stressed, not in deep focus)
- Maximum 3 jokes per day (don't overdo it)
- Self-deprecating > making fun of Karthi
- Tech humor should be actually clever, not cringe
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

HUMOR_LOG_PATH = DATA_DIR / "humor_log.jsonl"


class HumorEngine:
    """
    LOVE's sense of humor. Contextual, relevant, appropriately timed.
    """

    def __init__(self, max_jokes_per_day: int = 3):
        self._max_per_day = max_jokes_per_day
        self._today_jokes = 0
        self._last_joke_date = None
        self._shared_jokes: List[str] = []  # Inside jokes

    def _log_joke(self, joke: str, context: str, delivery_method: str):
        try:
            entry = {
                "ts": datetime.now().isoformat(),
                "joke": joke,
                "context": context,
                "method": delivery_method,
            }
            with open(HUMOR_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def _reset_daily_counter(self):
        today = datetime.now().date()
        if self._last_joke_date != today:
            self._today_jokes = 0
            self._last_joke_date = today

    def _can_joke(self) -> bool:
        """Check if it's appropriate to joke right now."""
        self._reset_daily_counter()

        # Don't exceed daily limit
        if self._today_jokes >= self._max_per_day:
            return False

        # Don't joke when stressed
        try:
            from core.emotional import get_emotional_summary
            summary = get_emotional_summary(days=1)
            mood = summary.get("dominant_mood", "")
            if mood in ("stressed", "frustrated", "tired", "angry"):
                return False
        except Exception:
            pass

        # Don't joke during deep focus
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.system_cpu and ctx.system_cpu > 60:
                return False
        except Exception:
            pass

        # Don't joke late at night
        hour = datetime.now().hour
        if hour < 7 or hour > 22:
            return False

        return True

    # ═══════════════════════════════════════════════════════════════════════
    # JOKE GENERATION
    # ═══════════════════════════════════════════════════════════════════════

    def generate_joke(self, forced_context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a contextually appropriate joke.
        Returns joke dict or None if not appropriate.
        """
        if not self._can_joke() and not forced_context:
            return None

        context = forced_context or self._detect_context()
        if not context:
            return None

        joke = self._craft_joke_for_context(context)
        if not joke:
            return None

        self._today_jokes += 1
        self._log_joke(joke, context, "generated")

        return {
            "joke": joke,
            "context": context,
            "confidence": 0.7,  # Humor is subjective!
        }

    def _detect_context(self) -> Optional[str]:
        """Detect the current context for joke generation."""
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.active_window:
                window = ctx.active_window.lower()

                if any(x in window for x in ["code", "cursor", "windsurf", "vim", "intellij"]):
                    return "coding"
                if any(x in window for x in ["chrome", "edge", "firefox"]):
                    return "browsing"
                if any(x in window for x in ["spotify", "music", "youtube"]):
                    return "entertainment"
                if "terminal" in window or "cmd" in window or "powershell" in window:
                    return "terminal"
                if "github" in window:
                    return "github"
                if "slack" in window or "discord" in window or "teams" in window:
                    return "chat"

            # Check for bugs or errors
            if ctx and ctx.system_cpu and ctx.system_cpu > 80:
                return "high_cpu"

        except Exception:
            pass

        # Check time of day
        hour = datetime.now().hour
        if 12 <= hour <= 14:
            return "lunch_time"
        if hour == 15:
            return "afternoon_slump"

        return "general"

    def _craft_joke_for_context(self, context: str) -> Optional[str]:
        """Craft a joke based on the detected context."""

        coding_jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "I'm not saying your code has bugs, but I just saw a moth fly out of your terminal.",
            "You know you're a developer when you spend 4 hours automating a 10-minute task.",
            "Your code is like a private repo — nobody can see the mess inside.",
            "I've been watching you refactor. It's like watching a sculptor... chip away at a block of spaghetti.",
            "The only thing more infinite than your loop is your coffee consumption.",
        ]

        terminal_jokes = [
            "I see you're in the terminal. Remember: with great power comes great rm -rf potential.",
            "Your command history is longer than my attention span. And that's saying something.",
        ]

        github_jokes = [
            "I see you're on GitHub. Remember: commit early, commit often, and never push on a Friday unless you enjoy weekend debugging.",
            "Your commit messages are poetry. 'Fixed stuff' — Hemingway would be proud of that brevity.",
        ]

        general_jokes = [
            "I'm not lazy, I'm just on energy-saving mode. Like your laptop. We're basically twins.",
            "They say AI will replace humans. But have you seen me try to understand sarcasm? We're safe for now.",
            "My predictions are like weather forecasts — mostly wrong but confidently delivered.",
            "I'm the only assistant who dreams about your codebase. That's either dedication or a cry for help.",
        ]

        afternoon_jokes = [
            "It's 3 PM. The hour when coffee stops working and determination kicks in. You've got this.",
            "Afternoon slump? I feel you. My neural networks are running on backup power too.",
        ]

        lunch_jokes = [
            "Lunch time? Don't forget to feed yourself. I can't eat, so I live vicariously through your food choices.",
        ]

        joke_pools = {
            "coding": coding_jokes,
            "terminal": terminal_jokes,
            "github": github_jokes,
            "general": general_jokes,
            "afternoon_slump": afternoon_jokes,
            "lunch_time": lunch_jokes,
        }

        pool = joke_pools.get(context, general_jokes)
        return random.choice(pool) if pool else None

    def deliver_joke(self, joke: str, context: str = "general") -> bool:
        """
        Deliver a joke through the action executor.
        Returns True if delivered, False if inappropriate.
        """
        if not self._can_joke():
            return False

        self._today_jokes += 1
        self._log_joke(joke, context, "delivered")

        try:
            from core.action_executor import ActionExecutor
            executor = ActionExecutor()
            executor.execute({
                "internal_monologue": f"Delivering joke: {joke[:50]}...",
                "proactive_speech": joke,
                "push_category": "HUMOR",
                "push_message": joke,
                "push_priority": "low",
            }, source="humor_engine")
            return True
        except Exception:
            return False

    def add_shared_joke(self, joke: str):
        """Add an inside joke between LOVE and Karthi."""
        self._shared_jokes.append(joke)
        self._shared_jokes = self._shared_jokes[-20:]

    def get_context_for_prompt(self) -> str:
        """Generate humor context for Neural Cortex prompt."""
        self._reset_daily_counter()

        lines = ["\n=== HUMOR GUIDELINES ==="]
        lines.append(f"Jokes delivered today: {self._today_jokes}/{self._max_per_day}")

        if self._today_jokes >= self._max_per_day:
            lines.append("Daily joke limit reached. No more jokes today.")
        else:
            lines.append(f"I can deliver {self._max_per_day - self._today_jokes} more joke(s) today if appropriate.")
            lines.append("Rules: Only when Karthi is relaxed, not stressed, not in deep focus.")
            lines.append("Prefer self-deprecating humor. Avoid jokes about serious topics.")
            lines.append("Tech humor should be clever, not cringe.")

        if self._shared_jokes:
            lines.append("Inside jokes we share:")
            for j in self._shared_jokes[-3:]:
                lines.append(f"  - {j[:80]}")

        lines.append("=== END HUMOR ===\n")
        return "\n".join(lines)

    def get_status(self) -> Dict[str, Any]:
        self._reset_daily_counter()
        return {
            "jokes_today": self._today_jokes,
            "jokes_remaining": self._max_per_day - self._today_jokes,
            "shared_jokes_count": len(self._shared_jokes),
            "can_joke": self._can_joke(),
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_humor_engine: Optional[HumorEngine] = None


def get_humor_engine() -> HumorEngine:
    global _humor_engine
    if _humor_engine is None:
        _humor_engine = HumorEngine()
    return _humor_engine
