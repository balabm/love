"""
LOVE Meaning Mapper — Significance Intelligence (Modern AI Pattern)

Most people seek meaning but never map it. This mapper:

1. MEANING TRACKING
   - Record experiences that feel meaningful and their characteristics
   - Track the intensity and duration of meaning-making moments
   - Log what made something feel significant vs empty

2. PATTERN ANALYSIS
   - Identify the user's meaning sources (connection, creation, contribution, challenge, transcendence)
   - Find meaning droughts and their triggers
   - Detect the gap between what the user says matters and where they spend time

3. MEANING GENERATION
   - Suggest meaning-rich activities based on mapped patterns
   - Provide meaning prompts for ordinary moments
   - Recommend meaning-making rituals

4. ALIGNMENT SUPPORT
   - Track alignment between daily activities and meaning sources
   - Alert when the user drifts from what matters
   - Celebrate meaning-rich periods

Architecture:
- record_moment(description, source, intensity, duration): Log meaning
- get_meaning_stats(): Get meaning pattern analysis
- get_meaning_suggestion(time, energy): Get meaning-rich activity
- get_meaning_score(): Calculate overall meaning health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "meaning_mapper"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MEANING_LOG = DATA_DIR / "meaning.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MeaningMoment:
    """A tracked meaning moment."""
    moment_id: str = ""
    description: str = ""
    source: str = ""  # connection, creation, contribution, challenge, transcendence, coherence, legacy
    intensity: float = 0.5  # 0-1
    duration_minutes: float = 0.0
    context: str = ""  # work, home, nature, social, alone, travel
    people_involved: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MeaningMapper:
    """
    Intelligent meaning mapper with pattern analysis and meaning-rich activity generation.
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
            "avg_intensity": 0.0,
            "avg_duration": 0.0,
            "dominant_source": "",
            "meaning_drought": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_moment(self, description: str = "", source: str = "", intensity: float = 0.5, duration: float = 0, context: str = "", people: Optional[List[str]] = None, notes: str = "") -> MeaningMoment:
        """Record a meaning moment."""
        moment_id = f"meaning_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._moments)}"
        moment = MeaningMoment(
            moment_id=moment_id,
            description=description or "unspecified",
            source=source or "connection",
            intensity=intensity,
            duration_minutes=duration,
            context=context or "general",
            people_involved=people or [],
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

    def get_meaning_stats(self) -> Dict[str, Any]:
        """Get meaning pattern analysis."""
        if not self._moments:
            return {"status": "insufficient_data"}

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "duration_sum": 0.0})
        for m in self._moments:
            by_source[m.source]["count"] += 1
            by_source[m.source]["intensity_sum"] += m.intensity
            by_source[m.source]["duration_sum"] += m.duration_minutes

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
            }

        dominant = max(source_stats.items(), key=lambda x: x[1]["count"]) if source_stats else ("", {})

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for m in self._moments:
            by_context[m.context]["count"] += 1
            by_context[m.context]["intensity_sum"] += m.intensity

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
            }

        # Drought
        recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        drought = len(recent) < 3

        # Trend
        if len(self._moments) > 5:
            recent_intensity = sum(m.intensity for m in recent) / max(1, len(recent))
            older = [m for m in self._moments if m.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if older:
                older_intensity = sum(m.intensity for m in older) / len(older)
                trend = "rising" if recent_intensity > older_intensity + 0.05 else "falling" if recent_intensity < older_intensity - 0.05 else "stable"
            else:
                trend = "new"
        else:
            trend = "stable"

        return {
            "total_moments": len(self._moments),
            "source_stats": source_stats,
            "dominant_source": dominant[0],
            "context_stats": context_stats,
            "avg_intensity": round(sum(m.intensity for m in self._moments) / len(self._moments), 2),
            "avg_duration": round(sum(m.duration_minutes for m in self._moments) / len(self._moments), 1),
            "drought": drought,
            "trend": trend,
        }

    def get_meaning_suggestion(self, time: float = 30, energy: str = "medium", source: str = "") -> Dict[str, Any]:
        """Get meaning-rich activity."""
        activities = {
            "connection": [
                "Have a conversation without looking at your phone",
                "Write a letter (not text) to someone you love",
                "Ask someone about their most meaningful memory",
                "Cook and eat a meal with someone, no distractions",
                "Tell someone specifically what they mean to you",
            ],
            "creation": [
                "Make something with your hands. Anything.",
                "Write one true sentence about how you feel right now",
                "Rearrange a space to reflect who you're becoming",
                "Start a small project with no commercial purpose",
                "Document something beautiful with photo, words, or sound",
            ],
            "contribution": [
                "Do one anonymous good deed",
                "Help someone with a task they've been avoiding",
                "Share knowledge that could change someone's path",
                "Clean up a shared space without being asked",
                "Leave an unexpectedly kind review for someone",
            ],
            "challenge": [
                "Do something that scares you slightly",
                "Learn one thing that stretches your mind",
                "Push your physical comfort zone for 10 minutes",
                "Have a difficult conversation you've been avoiding",
                "Attempt something you might fail at",
            ],
            "transcendence": [
                "Watch the sunrise or sunset in silence",
                "Listen to music that gives you chills",
                "Sit in nature and feel your smallness in the best way",
                "Read about something vast (universe, deep time, oceans)",
                "Contemplate a mystery you can't solve",
            ],
            "coherence": [
                "Connect two experiences from your life that seemed unrelated",
                "Notice a pattern in your choices. Journal about it.",
                "Tell your story to someone, including the hard parts",
                "Find the thread that connects your past to your future",
                "Make a decision that aligns all parts of your life",
            ],
            "legacy": [
                "Write something you want your great-grandchildren to know",
                "Teach someone a skill that took you years to learn",
                "Plant something that will outlive you",
                "Document a family story before it's forgotten",
                "Start something that others can continue",
            ],
        }

        if source and source in activities:
            selected = random.choice(activities[source])
        else:
            all_activities = [a for cat in activities.values() for a in cat]
            selected = random.choice(all_activities)

        return {
            "activity": selected,
            "source": source or "mixed",
            "time": time,
            "energy": energy,
            "why": "Meaning isn't found. It's made. This is raw material.",
            "prompt": "Afterward, note: What made this feel significant?",
        }

    def get_meaning_score(self) -> int:
        """Calculate overall meaning health (0-100)."""
        if not self._moments:
            return 40

        # Intensity
        avg_intensity = sum(m.intensity for m in self._moments) / len(self._moments)

        # Frequency
        recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        frequency = len(recent)

        # Variety
        unique_sources = len(set(m.source for m in self._moments))

        # Duration
        avg_duration = sum(m.duration_minutes for m in self._moments) / len(self._moments)

        # People involvement
        social = sum(1 for m in self._moments if m.people_involved)
        social_rate = social / len(self._moments)

        score = (avg_intensity * 30) + (min(frequency, 10) * 4) + (unique_sources * 5) + (min(avg_duration / 30, 1) * 10) + (social_rate * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._moments:
            self._stats["avg_intensity"] = round(sum(m.intensity for m in self._moments) / len(self._moments), 2)
            self._stats["avg_duration"] = round(sum(m.duration_minutes for m in self._moments) / len(self._moments), 1)

            by_source = defaultdict(int)
            for m in self._moments:
                by_source[m.source] += 1
            if by_source:
                self._stats["dominant_source"] = max(by_source.items(), key=lambda x: x[1])[0]

            recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            self._stats["meaning_drought"] = len(recent) < 3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meaning_mapper")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meaning_mapper")

    def _log_moment(self, moment: MeaningMoment):
        try:
            with open(MEANING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": moment.timestamp,
                    "source": moment.source,
                    "intensity": moment.intensity,
                    "context": moment.context,
                    "description": moment.description[:100],
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.meaning_mapper")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mm_instance: Optional[MeaningMapper] = None
_mm_lock = threading.Lock()


def get_meaning_mapper() -> MeaningMapper:
    global _mm_instance
    with _mm_lock:
        if _mm_instance is None:
            _mm_instance = MeaningMapper()
        return _mm_instance
