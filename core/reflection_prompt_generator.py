"""
LOVE Reflection Prompt Generator — Self-Awareness Catalyst (Modern AI Pattern)

Most reflection is generic ("What are you grateful for?"). This generator:

1. CONTEXTUAL PROMPTS
   - Generate prompts based on recent activities, moods, and events
   - Surface blind spots the user hasn't noticed
   - Ask questions that only LOVE could know to ask (based on tracked data)

2. PATTERN-BASED QUESTIONS
   - Ask about recurring themes in user's life
   - Probe decisions that align or conflict with values
   - Question assumptions revealed by behavior patterns

3. DEPTH CALIBRATION
   - Start light, go deeper based on user's engagement
   - Detect resistance and back off or lean in appropriately
   - Match emotional readiness to question intensity

4. PROACTIVE TIMING
   - Suggest reflection after significant events
   - Recommend reflection when patterns suggest stuckness
   - Celebrate insights and growth moments

Architecture:
- generate_prompt(context): Create a personalized reflection prompt
- get_daily_prompt(): Get a prompt for the day
- get_event_prompt(event_type, event_data): Get prompt triggered by event
- get_blind_spot_prompt(): Surface something the user might be missing
"""

import json
import math
import threading
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "reflection_prompts"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROMPT_LOG = DATA_DIR / "prompt_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ReflectionPrompt:
    """A generated reflection prompt."""
    prompt: str = ""
    category: str = ""  # daily, event, blind_spot, growth, values
    context: str = ""
    suggested_time: str = ""  # morning, evening, after_event
    depth: int = 1  # 1-3 (light to deep)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ReflectionPromptGenerator:
    """
    Generate personalized reflection prompts based on user's life data.
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
        self._history: deque = deque(maxlen=200)
        self._stats = {
            "total_prompts": 0,
            "avg_engagement": 0.5,
            "most_used_category": "",
        }
        self._load_stats()

    # ── Core Generation ─────────────────────────────────────────────────────

    def generate_prompt(self, context: str = "", category: str = "daily", depth: int = 1) -> ReflectionPrompt:
        """Generate a personalized reflection prompt."""
        prompt_text = self._build_prompt(context, category, depth)

        prompt = ReflectionPrompt(
            prompt=prompt_text,
            category=category,
            context=context,
            depth=depth,
            suggested_time=self._suggest_time(category),
        )

        with self._lock:
            self._history.append(prompt)
            self._stats["total_prompts"] += 1

        self._save_stats()
        self._log_prompt(prompt)

        return prompt

    def get_daily_prompt(self) -> ReflectionPrompt:
        """Get a prompt for the day."""
        # Gather context from various modules
        context_parts = []

        # Check for recent decisions
        try:
            from core.decision_journal import get_decision_journal
            dj = get_decision_journal()
            stats = dj.get_decision_stats(7)
            if stats.get("total_decisions", 0) > 0:
                context_parts.append(f"decisions: {stats['total_decisions']}")
        except Exception:
            pass

        # Check for mood patterns
        try:
            from core.mood_journal import get_mood_journal
            mj = get_mood_journal()
            insights = mj.get_mood_insights(7)
            if insights.get("most_common_mood"):
                context_parts.append(f"mood: {insights['most_common_mood']}")
        except Exception:
            pass

        # Check for values alignment
        try:
            from core.values_alignment_checker import get_values_alignment_checker
            vac = get_values_alignment_checker()
            score = vac.get_alignment_score()
            context_parts.append(f"alignment: {score}")
        except Exception:
            pass

        context = ", ".join(context_parts) if context_parts else "general"
        return self.generate_prompt(context, "daily", depth=1)

    def get_event_prompt(self, event_type: str, event_data: Dict[str, Any]) -> ReflectionPrompt:
        """Get a prompt triggered by a significant event."""
        prompts = {
            "decision_made": [
                "You just made a significant decision. What values guided your choice?",
                "How does this decision align with the person you want to become?",
                "What would you tell your future self about this decision?",
            ],
            "mood_drop": [
                "Your mood dropped recently. What's one small thing you could do right now?",
                "What triggered this shift? Is it temporary or a signal?",
                "When has your mood recovered before? What helped then?",
            ],
            "streak_broken": [
                "A streak ended today. What can you learn from this interruption?",
                "Was the break intentional or circumstantial?",
                "What's the smallest step to restart?",
            ],
            "goal_achieved": [
                "You achieved something. How did it feel? Was it what you expected?",
                "What did this achievement reveal about your capabilities?",
                "What's the next mountain?",
            ],
            "conflict": [
                "A values conflict appeared. Which value feels more true right now?",
                "Is there a way to honor both values, even partially?",
                "What would your ideal self do in this situation?",
            ],
            "energy_crash": [
                "Your energy crashed. What were you doing the hour before?",
                "Is this a pattern or an exception?",
                "What recharges you fastest? Can you do that now?",
            ],
        }

        options = prompts.get(event_type, ["What's on your mind right now?"])
        prompt_text = random.choice(options)

        return self.generate_prompt(f"event: {event_type}", "event", depth=2)

    def get_blind_spot_prompt(self) -> ReflectionPrompt:
        """Surface something the user might be missing."""
        blind_spots = [
            "You haven't mentioned {area} in a while. Is it still important to you?",
            "Your actions suggest {pattern}, but you've never explicitly said this. Does it fit?",
            "You keep choosing {choice} even though you say you value {value}. What's the real priority?",
            "You seem to avoid {topic}. What would happen if you faced it?",
            "Your energy drops every {time_pattern}. Have you noticed this?",
        ]

        # Try to personalize based on available data
        area = "your health"
        pattern = "prioritizing work over rest"
        choice = "working late"
        value = "balance"
        topic = "saying no"
        time_pattern = "afternoon"

        try:
            from core.values_alignment_checker import get_values_alignment_checker
            vac = get_values_alignment_checker()
            neglected = vac.get_neglected_values(14)
            if neglected:
                area = neglected[0]["name"]
        except Exception:
            pass

        try:
            from core.energy_audit_tool import get_energy_audit_tool
            eat = get_energy_audit_tool()
            profile = eat.get_energy_profile(7)
            if profile.get("time_of_day_energy"):
                worst_time = min(profile["time_of_day_energy"].items(), key=lambda x: x[1])
                time_pattern = worst_time[0]
        except Exception:
            pass

        template = random.choice(blind_spots)
        prompt_text = template.format(area=area, pattern=pattern, choice=choice, value=value, topic=topic, time_pattern=time_pattern)

        return self.generate_prompt("blind_spot_detection", "blind_spot", depth=2)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _build_prompt(self, context: str, category: str, depth: int) -> str:
        """Build a prompt based on context and depth."""
        daily_light = [
            "What's one small win from today?",
            "What made you smile today?",
            "What's something you're looking forward to tomorrow?",
            "What are you grateful for right now?",
            "What would make today feel complete?",
        ]

        daily_medium = [
            "What challenged you today? What did you learn?",
            "When did you feel most like yourself today?",
            "What would you do differently if you could relive today?",
            "Who had an impact on your day, and how?",
        ]

        daily_deep = [
            "What fear did you face (or avoid) today?",
            "What did you do today that aligns with your deepest values?",
            "If you only had this day to live, would you be satisfied with how you spent it?",
            "What truth are you avoiding about your current path?",
        ]

        growth_prompts = [
            "What's one belief you've changed your mind about recently?",
            "What feedback have you been resisting?",
            "What's the gap between who you are and who you want to be?",
            "What would you attempt if you knew you couldn't fail?",
        ]

        values_prompts = [
            "Which of your values got the most attention this week? Which got the least?",
            "When did you compromise on something important to you?",
            "What would your life look like if you honored all your values equally?",
        ]

        if category == "daily":
            pool = daily_light if depth == 1 else daily_medium if depth == 2 else daily_deep
        elif category == "growth":
            pool = growth_prompts
        elif category == "values":
            pool = values_prompts
        else:
            pool = daily_light

        return random.choice(pool)

    def _suggest_time(self, category: str) -> str:
        """Suggest optimal time for reflection."""
        if category == "daily":
            return "evening"
        elif category == "event":
            return "after_event"
        elif category == "blind_spot":
            return "morning"
        else:
            return "anytime"

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception:
            pass

    def _log_prompt(self, prompt: ReflectionPrompt):
        try:
            with open(PROMPT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": prompt.timestamp,
                    "prompt": prompt.prompt,
                    "category": prompt.category,
                    "depth": prompt.depth,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rpg_instance: Optional[ReflectionPromptGenerator] = None
_rpg_lock = threading.Lock()


def get_reflection_prompt_generator() -> ReflectionPromptGenerator:
    global _rpg_instance
    with _rpg_lock:
        if _rpg_instance is None:
            _rpg_instance = ReflectionPromptGenerator()
        return _rpg_instance
