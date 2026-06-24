"""
LOVE Interruption Etiquette Engine — Phase 5l of AGI Metamorphosis

A real companion knows when to speak and when to stay silent.
This engine determines whether LOVE should interrupt Karthi right now,
based on his focus state, past interruption outcomes, and the urgency
of what LOVE has to say.

Signals:
- Deep focus (coding, writing) → don't interrupt unless critical
- Light focus (browsing, music) → okay to interrupt
- Idle → open to conversation
- Stressed → be very careful
- Late night → only urgent things
- Previous negative reactions to interruptions → back off

Output: interruption_score (0-1) and a reason.
The Action Executor checks this before speaking.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

INTERRUPTION_HISTORY_PATH = DATA_DIR / "interruption_history.jsonl"


class InterruptionEtiquette:
    """
    LOVE's sense of social timing.
    Knows when Karthi is approachable and when he's in the zone.
    """

    def __init__(self):
        self._interruption_history: List[Dict[str, Any]] = []
        self._last_interruption_time: float = 0
        self._load_history()

    def _load_history(self):
        if INTERRUPTION_HISTORY_PATH.exists():
            try:
                with open(INTERRUPTION_HISTORY_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            self._interruption_history.append(json.loads(line))
            except Exception:
                pass

    def _log_interruption(self, event: str, score: float, reason: str, action_taken: str):
        try:
            entry = {
                "ts": datetime.now().isoformat(),
                "event": event,
                "score": score,
                "reason": reason,
                "action": action_taken,
            }
            with open(INTERRUPTION_HISTORY_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            self._interruption_history.append(entry)
        except Exception:
            pass

    def assess_interruption(self, message_urgency: str = "normal") -> Dict[str, Any]:
        """
        Assess whether it's appropriate to interrupt Karthi right now.

        Args:
            message_urgency: "critical", "high", "normal", "low"

        Returns:
            {"score": float (0-1), "allowed": bool, "reason": str}
        """
        now = datetime.now()
        hour = now.hour
        scores = []
        reasons = []

        # 1. Focus depth — what is Karthi doing right now?
        focus_depth = 0.5  # default
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx:
                app = (ctx.active_window or "").lower()
                cpu = ctx.system_cpu or 0
                activity = (ctx.activity or "").lower()

                # Deep focus apps
                deep_focus_apps = {
                    "code.exe", "cursor.exe", "windsurf.exe", "devenv.exe",
                    "vim", "nvim", "emacs", "intellij", "pycharm",
                    "clion", "rider", "goland", "webstorm",
                    "notepad", "obsidian", "word", "excel",
                }
                # Light focus apps
                light_apps = {
                    "chrome", "edge", "firefox", "spotify", "discord",
                    "telegram", "whatsapp", "slack", "teams",
                }

                if any(a in app for a in deep_focus_apps):
                    focus_depth = 0.9  # Very focused
                    reasons.append(f"Deep focus app: {app}")
                elif any(a in app for a in light_apps):
                    focus_depth = 0.4  # Light browsing
                    reasons.append(f"Light activity: {app}")
                elif activity == "idle":
                    focus_depth = 0.1  # Idle
                    reasons.append("User is idle")
                else:
                    focus_depth = 0.6
                    reasons.append(f"Unknown activity: {app}")

                # High CPU = working hard
                if cpu > 70:
                    focus_depth = min(1.0, focus_depth + 0.2)
                    reasons.append(f"High CPU ({cpu}%)")
        except Exception:
            pass

        scores.append((1.0 - focus_depth) * 0.35)  # Invert: high focus = low score

        # 2. Time of day
        time_score = 0.5
        if 23 <= hour or hour < 6:
            time_score = 0.1  # Late night / early morning — be very careful
            reasons.append("Late night / early morning")
        elif 6 <= hour < 9:
            time_score = 0.6  # Morning — might be getting ready
            reasons.append("Early morning")
        elif 9 <= hour < 18:
            time_score = 0.7  # Work hours — generally okay
            reasons.append("Work hours")
        elif 18 <= hour < 23:
            time_score = 0.8  # Evening — more relaxed
            reasons.append("Evening")
        scores.append(time_score * 0.15)

        # 3. Recent interruption outcomes
        reputation_penalty = 0.0
        try:
            recent = [h for h in self._interruption_history
                      if datetime.fromisoformat(h["ts"]) > now - timedelta(hours=2)]
            negative = [h for h in recent if h.get("event") == "negative_reaction"]
            positive = [h for h in recent if h.get("event") == "positive_reaction"]
            if negative:
                reputation_penalty = len(negative) * 0.2
                reasons.append(f"Recent negative reactions: {len(negative)}")
            elif positive:
                reputation_penalty = -0.1  # Slight bonus for being well-received
                reasons.append(f"Recent positive reactions: {len(positive)}")
        except Exception:
            pass
        scores.append(max(0, 0.5 - reputation_penalty) * 0.25)

        # 4. Emotional state
        emotional_score = 0.5
        try:
            from core.emotional import get_emotional_summary
            summary = get_emotional_summary(days=1)
            mood = summary.get("dominant_mood", "")
            if mood in ("stressed", "frustrated", "tired"):
                emotional_score = 0.2
                reasons.append(f"Karthi is {mood}")
            elif mood in ("happy", "calm", "focused"):
                emotional_score = 0.8
                reasons.append(f"Karthi is {mood}")
        except Exception:
            pass
        scores.append(emotional_score * 0.15)

        # 5. Urgency override
        urgency_multiplier = 1.0
        if message_urgency == "critical":
            urgency_multiplier = 2.0
            reasons.append("CRITICAL message — urgency override")
        elif message_urgency == "high":
            urgency_multiplier = 1.5
            reasons.append("High urgency")
        elif message_urgency == "low":
            urgency_multiplier = 0.5
            reasons.append("Low urgency")

        # Calculate final score
        base_score = sum(scores) / len(scores) if scores else 0.5
        final_score = min(1.0, base_score * urgency_multiplier)

        # Thresholds
        if message_urgency == "critical":
            allowed = final_score > 0.3  # Critical can interrupt almost anything
        elif message_urgency == "high":
            allowed = final_score > 0.5
        else:
            allowed = final_score > 0.7

        reason_str = "; ".join(reasons) if reasons else "Default assessment"

        return {
            "score": round(final_score, 3),
            "allowed": allowed,
            "reason": reason_str,
            "focus_depth": round(focus_depth, 2),
        }

    def record_reaction(self, was_positive: bool, message: str = ""):
        """
        Record how Karthi reacted to an interruption.
        Call this when Karthi responds to LOVE's proactive speech.
        """
        event = "positive_reaction" if was_positive else "negative_reaction"
        self._log_interruption(event, 0, f"Reaction to: {message[:100]}", "recorded")

    def get_status(self) -> Dict[str, Any]:
        """Return current interruption etiquette status."""
        recent = [h for h in self._interruption_history
                  if datetime.fromisoformat(h["ts"]) > datetime.now() - timedelta(hours=2)]
        negative = sum(1 for h in recent if h.get("event") == "negative_reaction")
        positive = sum(1 for h in recent if h.get("event") == "positive_reaction")

        return {
            "recent_interruptions": len(recent),
            "negative_reactions": negative,
            "positive_reactions": positive,
            "reputation": "good" if positive > negative else "caution" if negative > 0 else "neutral",
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_etiquette: Optional[InterruptionEtiquette] = None


def get_interruption_etiquette() -> InterruptionEtiquette:
    global _etiquette
    if _etiquette is None:
        _etiquette = InterruptionEtiquette()
    return _etiquette
