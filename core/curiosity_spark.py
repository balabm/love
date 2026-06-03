"""
LOVE Curiosity Spark — Wonder Intelligence (Modern AI Pattern)

Most adults lose curiosity. This spark:

1. CURIOSITY TRACKING
   - Record what the user is curious about and explores
   - Track depth vs breadth of exploration
   - Log which topics sustain interest vs fizzle

2. PATTERN ANALYSIS
   - Identify the user's curiosity style (deep diver, broad scanner, problem solver, aesthetic explorer)
   - Find which contexts spark curiosity (books, conversations, nature, problems)
   - Detect curiosity droughts and their causes

3. SPARK GENERATION
   - Suggest questions, topics, and experiences to reignite curiosity
   - Connect current interests to adjacent fascinating areas
   - Provide micro-curiosities (5-minute explorations)

4. GROWTH SUPPORT
   - Track curiosity as a skill that strengthens with practice
   - Suggest curiosity habits (question journals, wonder walks)
   - Celebrate curiosity milestones

Architecture:
- record_exploration(topic, depth, source, satisfaction): Log exploration
- get_curiosity_stats(): Get curiosity pattern analysis
- get_spark(current_interests, time_available): Get curiosity ignition
- get_curiosity_score(): Calculate overall curiosity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "curiosity_spark"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXPLORE_LOG = DATA_DIR / "explorations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Exploration:
    """A tracked curiosity exploration."""
    explore_id: str = ""
    topic: str = ""
    category: str = ""  # science, art, history, people, nature, tech, philosophy, culture
    depth: str = ""  # surface, moderate, deep, obsession
    source: str = ""  # book, conversation, article, video, experience, question
    duration_minutes: float = 0.0
    satisfaction: float = 0.5  # 0-1
    questions_generated: int = 0
    shared_with: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CuriositySpark:
    """
    Intelligent curiosity spark with pattern analysis and micro-exploration generation.
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
        self._explorations: deque = deque(maxlen=300)
        self._stats = {
            "total_explorations": 0,
            "avg_satisfaction": 0.0,
            "avg_depth_score": 0.0,
            "dominant_category": "",
            "curiosity_style": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_exploration(self, topic: str = "", category: str = "", depth: str = "", source: str = "", duration: float = 0, satisfaction: float = 0.5, questions: int = 0, shared: Optional[List[str]] = None, notes: str = "") -> Exploration:
        """Record a curiosity exploration."""
        explore_id = f"explore_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._explorations)}"
        exp = Exploration(
            explore_id=explore_id,
            topic=topic or "unspecified",
            category=category or "general",
            depth=depth or "surface",
            source=source or "unknown",
            duration_minutes=duration,
            satisfaction=satisfaction,
            questions_generated=questions,
            shared_with=shared or [],
            notes=notes,
        )

        with self._lock:
            self._explorations.append(exp)
            self._stats["total_explorations"] += 1
            self._update_stats()

        self._save_stats()
        self._log_exploration(exp)

        return exp

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_curiosity_stats(self) -> Dict[str, Any]:
        """Get curiosity pattern analysis."""
        if not self._explorations:
            return {"status": "insufficient_data"}

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "satisfaction_sum": 0.0, "depth_sum": 0.0})
        depth_scores = {"surface": 1, "moderate": 2, "deep": 3, "obsession": 4}
        for e in self._explorations:
            by_category[e.category]["count"] += 1
            by_category[e.category]["satisfaction_sum"] += e.satisfaction
            by_category[e.category]["depth_sum"] += depth_scores.get(e.depth, 1)

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            category_stats[c] = {
                "count": count,
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                "avg_depth": round(data["depth_sum"] / count, 1),
            }

        dominant = max(category_stats.items(), key=lambda x: x[1]["count"]) if category_stats else ("", {})

        # Source analysis
        by_source = defaultdict(int)
        for e in self._explorations:
            by_source[e.source] += 1

        # Curiosity style
        avg_depth = sum(depth_scores.get(e.depth, 1) for e in self._explorations) / len(self._explorations)
        unique_topics = len(set(e.topic for e in self._explorations))
        question_rate = sum(e.questions_generated for e in self._explorations) / len(self._explorations)

        if avg_depth > 2.5 and unique_topics < len(self._explorations) * 0.5:
            style = "deep diver"
        elif unique_topics > len(self._explorations) * 0.7:
            style = "broad scanner"
        elif question_rate > 2:
            style = "problem solver"
        elif by_source.get("experience", 0) > len(self._explorations) * 0.3:
            style = "aesthetic explorer"
        else:
            style = "balanced explorer"

        # Drought detection
        recent = [e for e in self._explorations if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        drought = len(recent) < 3

        return {
            "total_explorations": len(self._explorations),
            "category_stats": category_stats,
            "dominant_category": dominant[0],
            "source_distribution": dict(by_source),
            "curiosity_style": style,
            "avg_satisfaction": round(sum(e.satisfaction for e in self._explorations) / len(self._explorations), 2),
            "avg_depth": round(avg_depth, 1),
            "drought": drought,
        }

    def get_spark(self, current_interests: Optional[List[str]] = None, time_available: float = 5, category: str = "") -> Dict[str, Any]:
        """Get curiosity ignition."""
        current_interests = current_interests or []

        # Micro-curiosities by category
        sparks = {
            "science": [
                "What would happen if you could see radio waves?",
                "How do trees communicate through fungi networks?",
                "What is the closest living relative to dinosaurs today?",
                "Why does time seem to speed up as we age?",
            ],
            "art": [
                "What emotion does the color you've seen most today evoke?",
                "Listen to a song in a genre you never explore. What do you notice?",
                "Find an ordinary object and describe it like a poet would.",
                "What would your life look like as a 3-minute film?",
            ],
            "history": [
                "What was daily life like for a teenager 500 years ago?",
                "What invention seemed useless at first but changed everything?",
                "What did people believe before they knew about germs?",
                "What would surprise a time traveler from 1920 about today?",
            ],
            "people": [
                "Ask someone about a skill they've never told you about.",
                "What would your closest friend say is your hidden talent?",
                "Observe a stranger for 30 seconds. What's their story?",
                "What question have you never asked your parents?",
            ],
            "nature": [
                "Go outside and find something you've never noticed before.",
                "What animal has the most unusual survival strategy?",
                "How old is the oldest living thing near where you are?",
                "What would this place look like in 10,000 years?",
            ],
            "tech": [
                "What problem could AI solve that humans find boring?",
                "How would you explain the internet to a medieval scholar?",
                "What everyday object has the most complex engineering?",
                "What technology from sci-fi do you actually want?",
            ],
            "philosophy": [
                "What belief have you changed your mind about recently?",
                "If you could only ask one question for the rest of your life, what would it be?",
                "What would a truly perfect day look like?",
                "What do you know now that you wish you'd known at 20?",
            ],
            "culture": [
                "What food have you never tried that you suspect you'd love?",
                "What tradition from another culture resonates with you?",
                "What would your neighborhood look like in a different country?",
                "What language sounds most beautiful to you? Why?",
            ],
        }

        if category and category in sparks:
            selected = random.choice(sparks[category])
        else:
            all_sparks = [s for cat in sparks.values() for s in cat]
            selected = random.choice(all_sparks)

        # Adjust for time
        if time_available < 5:
            activity = "Just ponder the question. Let your mind wander."
        elif time_available < 30:
            activity = "Do a quick search or ask someone about it. Follow one thread."
        else:
            activity = "Dive deep. Read, watch, or experience something related."

        return {
            "spark": selected,
            "category": category or "mixed",
            "time_suggested": time_available,
            "activity": activity,
            "why": "Curiosity is a muscle. This is a light weight to lift.",
        }

    def get_curiosity_score(self) -> int:
        """Calculate overall curiosity health (0-100)."""
        if not self._explorations:
            return 45

        # Satisfaction
        avg_sat = sum(e.satisfaction for e in self._explorations) / len(self._explorations)

        # Depth
        depth_scores = {"surface": 1, "moderate": 2, "deep": 3, "obsession": 4}
        avg_depth = sum(depth_scores.get(e.depth, 1) for e in self._explorations) / len(self._explorations)

        # Frequency
        recent = [e for e in self._explorations if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        frequency = len(recent)

        # Question generation
        question_rate = sum(e.questions_generated for e in self._explorations) / len(self._explorations)

        # Sharing (higher is better)
        sharing = sum(1 for e in self._explorations if e.shared_with) / len(self._explorations)

        score = (avg_sat * 25) + (avg_depth / 4 * 20) + (min(frequency, 10) * 3) + (min(question_rate, 5) * 5) + (sharing * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._explorations:
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._explorations) / len(self._explorations), 2)
            depth_scores = {"surface": 1, "moderate": 2, "deep": 3, "obsession": 4}
            self._stats["avg_depth_score"] = round(sum(depth_scores.get(e.depth, 1) for e in self._explorations) / len(self._explorations), 1)

            by_category = defaultdict(int)
            for e in self._explorations:
                by_category[e.category] += 1
            if by_category:
                self._stats["dominant_category"] = max(by_category.items(), key=lambda x: x[1])[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.curiosity_spark")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.curiosity_spark")

    def _log_exploration(self, exp: Exploration):
        try:
            with open(EXPLORE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": exp.timestamp,
                    "topic": exp.topic,
                    "category": exp.category,
                    "depth": exp.depth,
                    "satisfaction": exp.satisfaction,
                    "questions": exp.questions_generated,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.curiosity_spark")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cs_instance: Optional[CuriositySpark] = None
_cs_lock = threading.Lock()


def get_curiosity_spark() -> CuriositySpark:
    global _cs_instance
    with _cs_lock:
        if _cs_instance is None:
            _cs_instance = CuriositySpark()
        return _cs_instance
