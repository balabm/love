"""
LOVE Presence Detector — Attention Intelligence (Modern AI Pattern)

Most people are rarely fully present. This detector:

1. PRESENCE TRACKING
   - Record moments of full presence and their triggers
   - Track partial presence, autopilot, and dissociation
   - Log what brings the user back when attention wanders

2. PATTERN ANALYSIS
   - Identify the user's presence triggers (sensory anchors, activities, people, environments)
   - Find presence drainers (phones, multitasking, fatigue, anxiety)
   - Detect presence rhythms (time of day, after what activities)

3. PRESENCE RECALL
   - Suggest presence anchors and grounding techniques
   - Provide micro-presence exercises (10-second returns)
   - Recommend presence-enhancing environments and rituals

4. GROWTH SUPPORT
   - Track presence as a trainable capacity
   - Suggest presence experiments
   - Celebrate presence milestones

Architecture:
- record_presence(state, trigger, duration, quality): Log presence
- get_presence_stats(): Get presence pattern analysis
- get_presence_suggestion(current_state, environment): Get grounding technique
- get_presence_score(): Calculate overall presence health
"""

import json
import math
import random
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "presence_detector"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRESENCE_LOG = DATA_DIR / "presence.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PresenceMoment:
    """A tracked presence moment."""
    moment_id: str = ""
    state: str = ""  # full, partial, autopilot, distracted, dissociated, returning
    trigger: str = ""  # what caused this state
    trigger_type: str = ""  # sensory, activity, person, environment, thought, body
    duration_minutes: float = 0.0
    quality: float = 0.5  # 0-1, how present
    return_method: str = ""  # how they came back if distracted
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PresenceDetector:
    """
    Intelligent presence detector with pattern analysis and grounding technique generation.
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
        self._moments: deque = deque(maxlen=300)
        self._stats = {
            "total_moments": 0,
            "avg_quality": 0.0,
            "full_presence_rate": 0.0,
            "dominant_trigger": "",
            "return_success_rate": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_presence(self, state: str = "", trigger: str = "", trigger_type: str = "", duration: float = 0, quality: float = 0.5, return_method: str = "", notes: str = "") -> PresenceMoment:
        """Record a presence moment."""
        moment_id = f"presence_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._moments)}"
        moment = PresenceMoment(
            moment_id=moment_id,
            state=state or "partial",
            trigger=trigger or "unspecified",
            trigger_type=trigger_type or "activity",
            duration_minutes=duration,
            quality=quality,
            return_method=return_method,
            notes=notes,
        )

        with self._lock:
            self._moments.append(moment)
            self._stats["total_moments"] += 1
            self._update_stats()

        self._save_stats()
        self._log_moment(moment)

        return moment

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_presence_stats(self) -> Dict[str, Any]:
        """Get presence pattern analysis."""
        if not self._moments:
            return {"status": "insufficient_data"}

        # State distribution
        by_state = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "duration_sum": 0.0})
        for m in self._moments:
            by_state[m.state]["count"] += 1
            by_state[m.state]["quality_sum"] += m.quality
            by_state[m.state]["duration_sum"] += m.duration_minutes

        state_stats = {}
        for s, data in by_state.items():
            count = data["count"]
            state_stats[s] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
                "percentage": round(count / len(self._moments), 2),
            }

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "quality_sum": 0.0})
        for m in self._moments:
            by_trigger[m.trigger]["count"] += 1
            by_trigger[m.trigger]["quality_sum"] += m.quality

        trigger_stats = {}
        for t, data in by_trigger.items():
            count = data["count"]
            trigger_stats[t] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
            }

        dominant = max(trigger_stats.items(), key=lambda x: x[1]["count"]) if trigger_stats else ("", {})

        # Return method analysis
        returns = [m for m in self._moments if m.return_method]
        if returns:
            by_return = defaultdict(lambda: {"count": 0, "quality_after": 0.0})
            for m in returns:
                by_return[m.return_method]["count"] += 1
                by_return[m.return_method]["quality_after"] += m.quality
            
            return_stats = {}
            for r, data in by_return.items():
                count = data["count"]
                return_stats[r] = {
                    "count": count,
                    "avg_quality": round(data["quality_after"] / count, 2),
                }
        else:
            return_stats = {}

        # Time analysis
        by_hour = defaultdict(lambda: {"count": 0, "quality_sum": 0.0})
        for m in self._moments:
            hour = m.timestamp[11:13] if len(m.timestamp) > 13 else "00"
            by_hour[hour]["count"] += 1
            by_hour[hour]["quality_sum"] += m.quality

        time_stats = {}
        for h, data in by_hour.items():
            count = data["count"]
            if count >= 2:
                time_stats[h] = {
                    "count": count,
                    "avg_quality": round(data["quality_sum"] / count, 2),
                }

        return {
            "total_moments": len(self._moments),
            "state_distribution": state_stats,
            "trigger_stats": trigger_stats,
            "dominant_trigger": dominant[0],
            "return_method_stats": return_stats,
            "time_stats": time_stats,
            "avg_quality": round(sum(m.quality for m in self._moments) / len(self._moments), 2),
            "full_presence_rate": round(sum(1 for m in self._moments if m.state == "full") / len(self._moments), 2),
        }

    def get_presence_suggestion(self, current_state: str = "distracted", environment: str = "work") -> Dict[str, Any]:
        """Get grounding technique."""
        techniques = {
            "sensory": [
                "Feel your feet on the floor. All your weight. Right now.",
                "Notice 5 things you can see, 4 you can hear, 3 you can touch, 2 you can smell, 1 you can taste.",
                "Hold a cold glass of water. Feel the temperature. Drink slowly.",
                "Place one hand on your heart. Feel it beating. You're alive.",
            ],
            "breath": [
                "Breathe in for 4, hold for 4, out for 4, hold for 4. Do 3 cycles.",
                "Exhale completely. Let all the air out. Then let the next breath find you.",
                "Breathe as if you're smelling a flower, then blowing out a candle.",
                "Count 10 breaths. If you lose count, start over. No judgment.",
            ],
            "body": [
                "Do a quick body scan from toes to crown. Where is tension hiding?",
                "Stretch like a cat. Slow, deliberate, luxurious.",
                "Press your palms together hard for 10 seconds. Release. Feel the difference.",
                "Stand up. Feel your full height. Claim the space you occupy.",
            ],
            "mind": [
                "Name the emotion you're feeling. Just name it. Don't fix it.",
                "Ask: What am I avoiding feeling right now?",
                "Imagine your thoughts as clouds. You're the sky.",
                "Repeat silently: 'I am here. This is now.'",
            ],
            "action": [
                "Do the next small thing with full attention. Just that one thing.",
                "Put your phone in another room. For 10 minutes.",
                "Close your eyes and listen to one song fully.",
                "Walk slowly to get water. Notice every step.",
            ],
        }

        tech_type = random.choice(list(techniques.keys()))
        technique = random.choice(techniques[tech_type])

        if environment == "work":
            context_note = "At work, even 30 seconds of full presence is a reset."
        elif environment == "home":
            context_note = "At home, presence is a gift to yourself and those with you."
        else:
            context_note = "Wherever you are, you can always come back to now."

        return {
            "current_state": current_state,
            "technique_type": tech_type,
            "technique": technique,
            "environment": environment,
            "context_note": context_note,
            "duration": "10-60 seconds. Repeat as needed.",
            "after": "Notice: Did anything shift? Even slightly? That's enough.",
        }

    def get_presence_score(self) -> int:
        """Calculate overall presence health (0-100)."""
        if not self._moments:
            return 35

        # Quality
        avg_quality = sum(m.quality for m in self._moments) / len(self._moments)

        # Full presence rate
        full_rate = sum(1 for m in self._moments if m.state == "full") / len(self._moments)

        # Duration of presence moments
        presence_moments = [m for m in self._moments if m.quality > 0.6]
        avg_duration = sum(m.duration_minutes for m in presence_moments) / max(1, len(presence_moments))

        # Return success (coming back from distraction)
        returns = [m for m in self._moments if m.return_method]
        if returns:
            return_quality = sum(m.quality for m in returns) / len(returns)
        else:
            return_quality = avg_quality

        # Recent trend
        recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        recent_quality = sum(m.quality for m in recent) / max(1, len(recent))

        score = (avg_quality * 25) + (full_rate * 20) + (min(avg_duration / 30, 1) * 10) + (return_quality * 15) + (recent_quality * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._moments:
            self._stats["avg_quality"] = round(sum(m.quality for m in self._moments) / len(self._moments), 2)
            full_count = sum(1 for m in self._moments if m.state == "full")
            self._stats["full_presence_rate"] = round(full_count / len(self._moments), 2)

            by_trigger = defaultdict(int)
            for m in self._moments:
                by_trigger[m.trigger] += 1
            if by_trigger:
                self._stats["dominant_trigger"] = max(by_trigger.items(), key=lambda x: x[1])[0]

            returns = [m for m in self._moments if m.return_method]
            if returns:
                return_quality = sum(m.quality for m in returns) / len(returns)
                self._stats["return_success_rate"] = round(return_quality, 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.presence_detector")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.presence_detector")

    def _log_moment(self, moment: PresenceMoment):
        try:
            with open(PRESENCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": moment.timestamp,
                    "state": moment.state,
                    "trigger": moment.trigger,
                    "quality": moment.quality,
                    "return_method": moment.return_method,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.presence_detector")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pd_instance: Optional[PresenceDetector] = None
_pd_lock = threading.Lock()


def get_presence_detector() -> PresenceDetector:
    global _pd_instance
    with _pd_lock:
        if _pd_instance is None:
            _pd_instance = PresenceDetector()
        return _pd_instance
