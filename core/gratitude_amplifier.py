"""
LOVE Gratitude Amplifier — Appreciation Intelligence (Modern AI Pattern)

Most gratitude is reactive and shallow. This amplifier:

1. GRATITUDE TRACKING
   - Record gratitude moments and their depth
   - Track gratitude targets (people, experiences, abilities, simple things)
   - Log gratitude practices and their effectiveness

2. PATTERN ANALYSIS
   - Identify gratitude style (event-based, person-based, ability-based, micro)
   - Find gratitude gaps (what's taken for granted)
   - Detect gratitude inflation (when it becomes automatic and loses meaning)

3. AMPLIFICATION PRACTICES
   - Suggest depth-building gratitude exercises
   - Provide novelty-seeking gratitude practices
   - Recommend gratitude expression methods

4. WELLBEING CORRELATION
   - Track the correlation between gratitude depth and mood
   - Alert when gratitude practice is becoming rote
   - Celebrate genuine appreciation moments

Architecture:
- record_gratitude(target, depth, category, practice): Log gratitude
- get_gratitude_stats(): Get gratitude pattern analysis
- get_amplification_exercise(style, gap): Get exercise
- get_gratitude_score(): Calculate overall gratitude health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "gratitude_amplifier"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GRATITUDE_LOG = DATA_DIR / "gratitude.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class GratitudeEntry:
    """A tracked gratitude entry."""
    entry_id: str = ""
    target: str = ""  # what they're grateful for
    target_type: str = ""  # person, experience, ability, thing, nature, challenge, simple
    depth: float = 0.5  # 0-1, how deeply they felt it
    novelty: float = 0.5  # 0-1, how new/unexpected this was
    practice_used: str = ""  # what practice they used
    expressed: bool = False  # did they express it to someone
    mood_before: float = 0.5  # 0-1
    mood_after: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class GratitudeAmplifier:
    """
    Intelligent gratitude amplifier with depth analysis and novelty-seeking.
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
        self._entries: deque = deque(maxlen=300)
        self._stats = {
            "total_entries": 0,
            "avg_depth": 0.0,
            "avg_novelty": 0.0,
            "expression_rate": 0.0,
            "gratitude_gap": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_gratitude(self, target: str = "", target_type: str = "", depth: float = 0.5, novelty: float = 0.5, practice: str = "", expressed: bool = False, mood_before: float = 0.5, mood_after: float = 0.5, notes: str = "") -> GratitudeEntry:
        """Record a gratitude entry."""
        entry_id = f"grat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = GratitudeEntry(
            entry_id=entry_id,
            target=target or "unspecified",
            target_type=target_type or "simple",
            depth=depth,
            novelty=novelty,
            practice_used=practice,
            expressed=expressed,
            mood_before=mood_before,
            mood_after=mood_after,
            notes=notes,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_stats()

        self._save_stats()
        self._log_entry(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_gratitude_stats(self) -> Dict[str, Any]:
        """Get gratitude pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Target type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "novelty_sum": 0.0, "expressed": 0, "mood_boost": 0.0})
        for e in self._entries:
            by_type[e.target_type]["count"] += 1
            by_type[e.target_type]["depth_sum"] += e.depth
            by_type[e.target_type]["novelty_sum"] += e.novelty
            if e.expressed:
                by_type[e.target_type]["expressed"] += 1
            by_type[e.target_type]["mood_boost"] += (e.mood_after - e.mood_before)

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_novelty": round(data["novelty_sum"] / count, 2),
                "expression_rate": round(data["expressed"] / count, 2),
                "avg_mood_boost": round(data["mood_boost"] / count, 2),
            }

        # Gap analysis (categories with few entries = potential gaps)
        all_types = {"person", "experience", "ability", "thing", "nature", "challenge", "simple"}
        present_types = set(type_stats.keys())
        gaps = list(all_types - present_types)

        # Depth trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_novelty = sum(e.novelty for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_novelty = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_depth = sum(e.depth for e in older) / len(older)
            older_novelty = sum(e.novelty for e in older) / len(older)
            depth_trend = recent_depth - older_depth
            novelty_trend = recent_novelty - older_novelty
        else:
            depth_trend = 0
            novelty_trend = 0

        # Rote detection (low novelty, consistent targets)
        target_counts = defaultdict(int)
        for e in self._entries:
            target_counts[e.target] += 1
        frequent_targets = {t: c for t, c in target_counts.items() if c > 3}
        rote_risk = len(frequent_targets) > 5

        # Expression analysis
        expressed = sum(1 for e in self._entries if e.expressed)
        expression_rate = expressed / len(self._entries)

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "gaps": gaps,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_novelty": round(sum(e.novelty for e in self._entries) / len(self._entries), 2),
            "expression_rate": round(expression_rate, 2),
            "depth_trend": round(depth_trend, 2),
            "novelty_trend": round(novelty_trend, 2),
            "rote_risk": rote_risk,
            "frequent_targets": list(frequent_targets.keys())[:5],
        }

    def get_amplification_exercise(self, style: str = "", gap: str = "") -> Dict[str, Any]:
        """Get exercise."""
        exercises = {
            "depth": [
                "Instead of 'I'm grateful for my job,' go deeper: 'I'm grateful for the colleague who noticed my struggle.'",
                "Use the 5 Whys on gratitude. Why are you grateful? And why is that? Keep asking.",
                "Write a thank-you note of at least 200 words. Specificity breeds depth.",
            ],
            "novelty": [
                "Find one new thing to be grateful for today. Something you've never noticed before.",
                "Gratitude scavenger hunt: Find gratitude in a color, a sound, a texture, a smell.",
                "Ask someone: 'What are you grateful for today?' Their answer will open your eyes.",
            ],
            "expression": [
                "Tell one person specifically why you're grateful for them. Be awkward. Do it anyway.",
                "Write a gratitude letter you don't send. Then send it.",
                "Create a gratitude video message. Speaking makes it more real than writing.",
            ],
            "challenge": [
                "Find gratitude for one difficulty you're facing. What is it teaching you?",
                "Think of a past struggle you're now grateful for. Apply that lens to current struggles.",
                "Gratitude for the ordinary: running water, electricity, literacy. Most of humanity lacks these.",
            ],
            "simple": [
                "Notice 5 small things in the next hour. A warm mug. A comfortable chair. Light through a window.",
                "Savor one bite of food. Really taste it. Gratitude lives in attention.",
                "Feel your feet on the ground. Gratitude for gravity, for support, for being here.",
            ],
        }

        selected = exercises.get(style, exercises["depth"])

        if gap:
            gap_note = f"You rarely express gratitude for {gap}. This week, find one thing in that category."
        else:
            gap_note = "Your gratitude is well-rounded. Now deepen it."

        return {
            "style": style or "general",
            "gap": gap or "none",
            "exercise": random.choice(selected),
            "gap_note": gap_note,
            "reminder": "Gratitude isn't about being positive. It's about noticing what's already there. Depth over volume.",
        }

    def get_gratitude_score(self) -> int:
        """Calculate overall gratitude health (0-100)."""
        if not self._entries:
            return 30

        # Depth
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)

        # Novelty
        avg_novelty = sum(e.novelty for e in self._entries) / len(self._entries)

        # Expression
        expressed = sum(1 for e in self._entries if e.expressed)
        expression_rate = expressed / len(self._entries)

        # Mood boost
        mood_boosts = [e.mood_after - e.mood_before for e in self._entries]
        avg_mood_boost = sum(mood_boosts) / len(mood_boosts)

        # Variety
        unique_types = len(set(e.target_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_novelty = sum(e.novelty for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_novelty = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_depth = sum(e.depth for e in older) / len(older)
            older_novelty = sum(e.novelty for e in older) / len(older)
            trend = (recent_depth + recent_novelty) - (older_depth + older_novelty)
        else:
            trend = 0

        # Rote penalty
        target_counts = defaultdict(int)
        for e in self._entries:
            target_counts[e.target] += 1
        frequent = sum(1 for t, c in target_counts.items() if c > 3)
        rote_penalty = min(15, frequent)

        score = (avg_depth * 25) + (avg_novelty * 20) + (expression_rate * 15) + (avg_mood_boost * 10) + (unique_types * 3) + (trend * 10) - rote_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_novelty"] = round(sum(e.novelty for e in self._entries) / len(self._entries), 2)
            
            expressed = sum(1 for e in self._entries if e.expressed)
            self._stats["expression_rate"] = round(expressed / len(self._entries), 2)

            by_type = defaultdict(int)
            for e in self._entries:
                by_type[e.target_type] += 1
            all_types = {"person", "experience", "ability", "thing", "nature", "challenge", "simple"}
            gaps = list(all_types - set(by_type.keys()))
            if gaps:
                self._stats["gratitude_gap"] = gaps[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gratitude_amplifier")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gratitude_amplifier")

    def _log_entry(self, entry: GratitudeEntry):
        try:
            with open(GRATITUDE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "target": entry.target,
                    "target_type": entry.target_type,
                    "depth": entry.depth,
                    "novelty": entry.novelty,
                    "expressed": entry.expressed,
                    "mood_before": entry.mood_before,
                    "mood_after": entry.mood_after,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gratitude_amplifier")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ga_instance: Optional[GratitudeAmplifier] = None
_ga_lock = threading.Lock()


def get_gratitude_amplifier() -> GratitudeAmplifier:
    global _ga_instance
    with _ga_lock:
        if _ga_instance is None:
            _ga_instance = GratitudeAmplifier()
        return _ga_instance
