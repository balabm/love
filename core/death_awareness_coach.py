"""
LOVE Death Awareness Coach — Mortality Intelligence (Modern AI Pattern)

Most people avoid thinking about death. This coach:

1. MORTALITY TRACKING
   - Record memento mori moments and their impact
   - Track mortality awareness exercises and their effects
   - Log what the user would do differently if they knew their time was limited

2. PATTERN ANALYSIS
   - Identify how mortality awareness affects decision-making
   - Find which mortality practices are most life-enhancing vs anxiety-inducing
   - Detect avoidance vs healthy integration of death awareness

3. INTEGRATION PRACTICES
   - Suggest stoic memento mori exercises
   - Provide death meditation prompts
   - Recommend mortality-aligned priority-setting

4. LIFE ENHANCEMENT
   - Track correlation between death awareness and life satisfaction
   - Alert when the user is living as if they have infinite time
   - Celebrate mortality-informed choices

Architecture:
- record_memento(trigger, emotional_response, insight): Log moment
- get_death_awareness_stats(): Get mortality pattern analysis
- get_memento_suggestion(style): Get mortality practice
- get_death_awareness_score(): Calculate healthy mortality integration
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

DATA_DIR = Path(__file__).parent.parent / "data" / "death_awareness_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MEMENTO_LOG = DATA_DIR / "memento.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MementoMoment:
    """A tracked memento mori moment."""
    moment_id: str = ""
    trigger: str = ""  # what triggered the awareness
    emotional_response: str = ""  # calm, anxious, grateful, motivated, sad, peaceful
    insight: str = ""  # what they realized
    life_change_considered: str = ""  # what they thought about changing
    time_sense: str = ""  # limited, precious, normal, infinite
    practice_type: str = ""  # meditation, reading, experience, reminder, dream, loss
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class DeathAwarenessCoach:
    """
    Intelligent death awareness coach with mortality integration and life enhancement.
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
        self._moments: deque = deque(maxlen=200)
        self._stats = {
            "total_moments": 0,
            "avg_time_sense": 0.0,
            "grateful_rate": 0.0,
            "anxiety_rate": 0.0,
            "dominant_practice": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_memento(self, trigger: str = "", emotional_response: str = "", insight: str = "", life_change: str = "", time_sense: str = "", practice_type: str = "", notes: str = "") -> MementoMoment:
        """Record a memento mori moment."""
        moment_id = f"memento_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._moments)}"
        moment = MementoMoment(
            moment_id=moment_id,
            trigger=trigger or "unspecified",
            emotional_response=emotional_response or "calm",
            insight=insight,
            life_change_considered=life_change,
            time_sense=time_sense or "normal",
            practice_type=practice_type or "reminder",
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

    def get_death_awareness_stats(self) -> Dict[str, Any]:
        """Get mortality pattern analysis."""
        if not self._moments:
            return {"status": "insufficient_data"}

        # Emotional response analysis
        by_emotion = defaultdict(int)
        for m in self._moments:
            by_emotion[m.emotional_response] += 1

        # Practice type analysis
        by_practice = defaultdict(lambda: {"count": 0, "grateful": 0, "anxious": 0})
        for m in self._moments:
            by_practice[m.practice_type]["count"] += 1
            if m.emotional_response in ["grateful", "motivated", "peaceful", "calm"]:
                by_practice[m.practice_type]["grateful"] += 1
            if m.emotional_response in ["anxious", "sad"]:
                by_practice[m.practice_type]["anxious"] += 1

        practice_stats = {}
        for p, data in by_practice.items():
            count = data["count"]
            practice_stats[p] = {
                "count": count,
                "positive_rate": round(data["grateful"] / count, 2),
                "anxiety_rate": round(data["anxious"] / count, 2),
            }

        dominant = max(practice_stats.items(), key=lambda x: x[1]["count"]) if practice_stats else ("", {})

        # Time sense analysis
        time_scores = {"infinite": 1, "normal": 2, "precious": 3, "limited": 4}
        avg_time = sum(time_scores.get(m.time_sense, 2) for m in self._moments) / len(self._moments)

        # Integration health
        positive = sum(1 for m in self._moments if m.emotional_response in ["grateful", "motivated", "peaceful", "calm"])
        negative = sum(1 for m in self._moments if m.emotional_response in ["anxious", "sad"])
        integration = positive / max(1, positive + negative)

        # Drought
        recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        drought = len(recent) == 0

        return {
            "total_moments": len(self._moments),
            "emotional_distribution": dict(by_emotion),
            "practice_stats": practice_stats,
            "dominant_practice": dominant[0],
            "avg_time_sense": round(avg_time, 2),
            "integration_health": round(integration, 2),
            "drought": drought,
        }

    def get_memento_suggestion(self, style: str = "gentle", time: float = 5) -> Dict[str, Any]:
        """Get mortality practice."""
        practices = {
            "gentle": [
                "Look at old photos. Notice how much life has happened. More will happen, then stop.",
                "Write a letter to your future self at 80. What do you want them to remember?",
                "Consider: This ordinary Tuesday is someone's last. Yours might be too. What would make it enough?",
                "Think of someone who died. What would they tell you to stop worrying about?",
            ],
            "stoic": [
                "Contemplate the shortness of life. Not to despair, but to focus.",
                "Ask: If I died tonight, would I be satisfied with how I spent today?",
                "Meditate on impermanence. Everything you see will one day be gone. Including you.",
                "Practice negative visualization: Imagine losing what you have. Then appreciate that you have it.",
            ],
            "creative": [
                "Write your own obituary. Not morbid—clarifying. What's the story you want told?",
                "Design your ideal funeral. What music? Who speaks? What legacy is celebrated?",
                "Create a 'time capsule' letter for someone to open after you're gone.",
                "Make art about death. It doesn't have to be dark. It can be beautiful.",
            ],
            "experiential": [
                "Visit a cemetery. Read names. Wonder about their stories. Feel the continuity of life.",
                "Volunteer with hospice or elderly. Their perspective on time will change yours.",
                "Experience something ancient (old tree, historic site, starlight). Feel deep time.",
                "Hold something fragile. Appreciate that everything is fragile, including you.",
            ],
        }

        selected = random.choice(practices.get(style, practices["gentle"]))

        return {
            "practice": selected,
            "style": style,
            "time": time,
            "instruction": "Don't rush. Let the insight settle. Then act on one thing it reveals.",
            "aftercare": "Be gentle with yourself. Mortality awareness is powerful medicine. Don't overdose.",
        }

    def get_death_awareness_score(self) -> int:
        """Calculate healthy mortality integration (0-100)."""
        if not self._moments:
            return 30

        # Integration (positive vs negative responses)
        positive = sum(1 for m in self._moments if m.emotional_response in ["grateful", "motivated", "peaceful", "calm"])
        integration = positive / len(self._moments)

        # Time sense (higher = more precious/limited = better awareness)
        time_scores = {"infinite": 1, "normal": 2, "precious": 3, "limited": 4}
        avg_time = sum(time_scores.get(m.time_sense, 2) for m in self._moments) / len(self._moments)

        # Frequency
        recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        frequency = len(recent)

        # Variety of practices
        unique_practices = len(set(m.practice_type for m in self._moments))

        # Life changes considered (action-oriented)
        changes = sum(1 for m in self._moments if m.life_change_considered)
        action_rate = changes / len(self._moments)

        score = (integration * 30) + (avg_time / 4 * 20) + (min(frequency, 8) * 3) + (unique_practices * 4) + (action_rate * 20)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._moments:
            time_scores = {"infinite": 1, "normal": 2, "precious": 3, "limited": 4}
            self._stats["avg_time_sense"] = round(sum(time_scores.get(m.time_sense, 2) for m in self._moments) / len(self._moments), 2)
            
            grateful = sum(1 for m in self._moments if m.emotional_response in ["grateful", "motivated", "peaceful"])
            self._stats["grateful_rate"] = round(grateful / len(self._moments), 2)
            
            anxious = sum(1 for m in self._moments if m.emotional_response in ["anxious", "sad"])
            self._stats["anxiety_rate"] = round(anxious / len(self._moments), 2)

            by_practice = defaultdict(int)
            for m in self._moments:
                by_practice[m.practice_type] += 1
            if by_practice:
                self._stats["dominant_practice"] = max(by_practice.items(), key=lambda x: x[1])[0]

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

    def _log_moment(self, moment: MementoMoment):
        try:
            with open(MEMENTO_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": moment.timestamp,
                    "trigger": moment.trigger,
                    "emotion": moment.emotional_response,
                    "time_sense": moment.time_sense,
                    "practice": moment.practice_type,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_dac_instance: Optional[DeathAwarenessCoach] = None
_dac_lock = threading.Lock()


def get_death_awareness_coach() -> DeathAwarenessCoach:
    global _dac_instance
    with _dac_lock:
        if _dac_instance is None:
            _dac_instance = DeathAwarenessCoach()
        return _dac_instance
