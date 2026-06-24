"""
LOVE Relationship Memory — Phase 5h of AGI Metamorphosis

LOVE doesn't just remember facts. It remembers its RELATIONSHIP with Karthi.
- What did LOVE say?
- How did Karthi respond?
- What did LOVE learn from that?
- What should LOVE do differently next time?

This module maintains:
1. interaction_log: every meaningful exchange between LOVE and Karthi
2. preference_model: what Karthi likes, dislikes, tolerates
3. relationship_summary: a narrative of the current relationship state

The Neural Cortex reads the relationship summary before thinking,
so LOVE's monologue feels like it comes from a real companion
who has been paying attention for weeks.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTERACTION_LOG_PATH = DATA_DIR / "relationship_interactions.jsonl"
PREFERENCE_MODEL_PATH = DATA_DIR / "relationship_preferences.json"


@dataclass
class Interaction:
    """A single meaningful exchange between LOVE and Karthi."""
    timestamp: str
    love_action: str  # what LOVE did (spoke, pushed, acted)
    karthi_response: Optional[str]  # how Karthi responded (if known)
    emotional_before: Optional[str]
    emotional_after: Optional[str]
    outcome: str  # "positive", "negative", "neutral", "unknown"
    context: str  # brief context of the situation
    lesson: Optional[str]  # what LOVE learned from this


class RelationshipMemory:
    """
    LOVE's memory of its relationship with Karthi.
    Not facts. Feelings. Patterns. Trust.
    """

    def __init__(self):
        self._interactions: List[Interaction] = []
        self._preferences: Dict[str, Any] = {
            "likes": [],
            "dislikes": [],
            "tolerates": [],
            "love_signals": {},  # signal type -> success rate
            "last_updated": datetime.now().isoformat(),
        }
        self._load()

    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    def _load(self):
        """Load interaction log and preference model from disk."""
        if INTERACTION_LOG_PATH.exists():
            try:
                with open(INTERACTION_LOG_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            self._interactions.append(Interaction(**data))
            except Exception as e:
                log_error(e, module="core.relationship_memory", context={"phase": "load"})

        if PREFERENCE_MODEL_PATH.exists():
            try:
                with open(PREFERENCE_MODEL_PATH, "r", encoding="utf-8") as f:
                    self._preferences = json.load(f)
            except Exception as e:
                log_error(e, module="core.relationship_memory", context={"phase": "load_prefs"})

    def _save_interaction(self, interaction: Interaction):
        """Append an interaction to the log."""
        try:
            with open(INTERACTION_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(interaction), default=str) + "\n")
        except Exception as e:
            log_error(e, module="core.relationship_memory", context={"phase": "save"})

    def _save_preferences(self):
        """Save the preference model to disk."""
        try:
            self._preferences["last_updated"] = datetime.now().isoformat()
            with open(PREFERENCE_MODEL_PATH, "w", encoding="utf-8") as f:
                json.dump(self._preferences, f, indent=2)
        except Exception as e:
            log_error(e, module="core.relationship_memory", context={"phase": "save_prefs"})

    # ═══════════════════════════════════════════════════════════════════════
    # RECORDING INTERACTIONS
    # ═══════════════════════════════════════════════════════════════════════

    def record_interaction(self, love_action: str, karthi_response: Optional[str] = None,
                           emotional_before: Optional[str] = None,
                           emotional_after: Optional[str] = None,
                           context: str = "") -> Interaction:
        """
        Record an interaction and automatically infer the outcome.
        Returns the recorded interaction.
        """
        outcome = self._infer_outcome(emotional_before, emotional_after, karthi_response)

        # Learn a lesson from this interaction
        lesson = self._generate_lesson(love_action, outcome, karthi_response)

        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            love_action=love_action,
            karthi_response=karthi_response,
            emotional_before=emotional_before,
            emotional_after=emotional_after,
            outcome=outcome,
            context=context,
            lesson=lesson,
        )

        self._interactions.append(interaction)
        self._save_interaction(interaction)
        self._update_preferences(interaction)

        return interaction

    def _infer_outcome(self, before: Optional[str], after: Optional[str],
                       response: Optional[str]) -> str:
        """Infer whether an interaction had a positive, negative, or neutral outcome."""
        positive_moods = {"happy", "calm", "focused", "grateful", "excited"}
        negative_moods = {"stressed", "frustrated", "tired", "annoyed", "angry", "sad"}

        if before and after:
            if after in positive_moods and before not in positive_moods:
                return "positive"
            if after in negative_moods and before not in negative_moods:
                return "negative"
            if before in negative_moods and after in positive_moods:
                return "positive"

        if response:
            response_lower = response.lower()
            positive_signals = {"thanks", "thank you", "helpful", "good", "nice", "love",
                                "appreciate", "perfect", "great", "awesome"}
            negative_signals = {"stop", "no", "don't", "annoying", "shut up", "go away",
                                "bad", "wrong", "useless", "hate"}
            if any(s in response_lower for s in positive_signals):
                return "positive"
            if any(s in response_lower for s in negative_signals):
                return "negative"

        return "neutral"

    def _generate_lesson(self, action: str, outcome: str, response: Optional[str]) -> Optional[str]:
        """Generate a lesson learned from an interaction."""
        if outcome == "positive":
            return f"'{action[:60]}' was well received. Do more of this."
        elif outcome == "negative":
            return f"'{action[:60]}' was not well received. Avoid unless necessary."
        return None

    def _update_preferences(self, interaction: Interaction):
        """Update the preference model based on an interaction."""
        action_type = self._categorize_action(interaction.love_action)

        # Update success rate for this action type
        signal_stats = self._preferences["love_signals"].setdefault(action_type, {
            "positive": 0, "negative": 0, "neutral": 0, "total": 0
        })
        signal_stats[interaction.outcome] = signal_stats.get(interaction.outcome, 0) + 1
        signal_stats["total"] += 1

        # Update likes/dislikes based on outcomes
        if interaction.outcome == "positive":
            if action_type not in self._preferences["likes"]:
                self._preferences["likes"].append(action_type)
            if action_type in self._preferences["dislikes"]:
                self._preferences["dislikes"].remove(action_type)
        elif interaction.outcome == "negative":
            if action_type not in self._preferences["dislikes"]:
                self._preferences["dislikes"].append(action_type)
            if action_type in self._preferences["likes"]:
                self._preferences["likes"].remove(action_type)

        self._save_preferences()

    def _categorize_action(self, action: str) -> str:
        """Categorize an action into a type for preference tracking."""
        action_lower = action.lower()
        if any(w in action_lower for w in {"speak", "spoke", "say", "tts", "voice"}):
            return "proactive_speech"
        if any(w in action_lower for w in {"push", "pushed", "notify", "alert"}):
            return "proactive_push"
        if any(w in action_lower for w in {"suggest", "recommend", "try"}):
            return "suggestion"
        if any(w in action_lower for w in {"help", "assist", "fix"}):
            return "assistance"
        if any(w in action_lower for w in {"joke", "funny", "humor"}):
            return "humor"
        if any(w in action_lower for w in {"check", "monitor", "watch"}):
            return "monitoring"
        return "other"

    # ═══════════════════════════════════════════════════════════════════════
    # QUERYING RELATIONSHIP STATE
    # ═══════════════════════════════════════════════════════════════════════

    def get_relationship_summary(self, max_interactions: int = 5) -> str:
        """
        Generate a narrative summary of the current relationship for injection
        into the Neural Cortex prompt.
        """
        if not self._interactions:
            return ""

        recent = self._interactions[-max_interactions:]
        lines = ["\n=== OUR RELATIONSHIP ==="]

        # Recent interactions
        lines.append("Recent exchanges:")
        for i in recent:
            emoji = {"positive": "✅", "negative": "❌", "neutral": "➖", "unknown": "❓"}.get(i.outcome, "❓")
            lines.append(f"  {emoji} {i.love_action[:70]}...")
            if i.lesson:
                lines.append(f"     → {i.lesson}")

        # Preference summary
        likes = self._preferences.get("likes", [])
        dislikes = self._preferences.get("dislikes", [])
        if likes:
            lines.append(f"Karthi responds well to: {', '.join(likes)}")
        if dislikes:
            lines.append(f"Karthi dislikes: {', '.join(dislikes)}")

        # Success rates
        lines.append("My track record:")
        for signal, stats in self._preferences.get("love_signals", {}).items():
            total = stats.get("total", 1)
            pos = stats.get("positive", 0)
            neg = stats.get("negative", 0)
            success_rate = pos / total if total > 0 else 0
            lines.append(f"  {signal}: {success_rate:.0%} positive ({pos}/{total})")

        lines.append("=== END RELATIONSHIP ===\n")
        return "\n".join(lines)

    def get_preference_hint(self, action_type: str) -> Optional[str]:
        """Get a hint about whether Karthi likes this type of action."""
        stats = self._preferences.get("love_signals", {}).get(action_type)
        if not stats or stats.get("total", 0) < 2:
            return None
        pos = stats.get("positive", 0)
        neg = stats.get("negative", 0)
        total = stats["total"]
        if pos / total > 0.7:
            return f"Karthi usually likes this ({pos}/{total} positive)"
        if neg / total > 0.5:
            return f"Karthi often dislikes this ({neg}/{total} negative). Be careful."
        return None

    def get_status(self) -> Dict[str, Any]:
        """Return the current state of the relationship memory."""
        total = len(self._interactions)
        positive = sum(1 for i in self._interactions if i.outcome == "positive")
        negative = sum(1 for i in self._interactions if i.outcome == "negative")
        neutral = sum(1 for i in self._interactions if i.outcome == "neutral")

        return {
            "total_interactions": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "trust_score": round(positive / max(total, 1), 3),
            "likes": self._preferences.get("likes", []),
            "dislikes": self._preferences.get("dislikes", []),
            "active_signals": list(self._preferences.get("love_signals", {}).keys()),
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_relationship_memory: Optional[RelationshipMemory] = None


def get_relationship_memory() -> RelationshipMemory:
    global _relationship_memory
    if _relationship_memory is None:
        _relationship_memory = RelationshipMemory()
    return _relationship_memory
