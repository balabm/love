"""
LOVE Comparison Detoxifier — Contentment Intelligence (Modern AI Pattern)

Most people compare themselves into misery. This detoxifier:

1. COMPARISON TRACKING
   - Record comparison moments and their characteristics
   - Track comparison types (upward, downward, lateral, social media, achievement)
   - Log distress, accuracy, and response to comparisons

2. PATTERN ANALYSIS
   - Identify the user's comparison profile (chronic, selective, aware, recovered)
   - Find comparison patterns that motivate vs demoralize
   - Detect chronic comparison and its costs

3. DETOX BUILDING
   - Suggest practices for releasing comparison habits
   - Provide frameworks for self-referencing vs other-referencing
   - Recommend gratitude and self-compassion as antidotes

4. CONTENTMENT CULTIVATION
   - Track the correlation between comparison and wellbeing
   - Alert when comparison is becoming the default
   - Celebrate moments of genuine self-contentment

Architecture:
- record_comparison(comparison, type, distress, accuracy, response): Log comparison
- get_comparison_stats(): Get comparison pattern analysis
- get_comparison_suggestion(capacity, context): Get suggestion
- get_comparison_score(): Calculate overall comparison health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "comparison_detoxifier"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMPARISON_LOG = DATA_DIR / "comparisons.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ComparisonEntry:
    """A tracked comparison moment."""
    entry_id: str = ""
    comparison: str = ""  # what you compared
    comparison_type: str = ""  # upward, downward, lateral, social_media, achievement
    distress: float = 0.0  # 0-1
    accuracy: float = 0.0  # 0-1 was the comparison accurate?
    response: float = 0.0  # 0-1 how well you responded
    gratitude: float = 0.0  # 0-1
    self_compassion: float = 0.0  # 0-1
    self_reference: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ComparisonDetoxifier:
    """
    Intelligent comparison detoxifier with distress detection and contentment cultivation.
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
            "avg_distress": 0.0,
            "avg_gratitude": 0.0,
            "detox_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_comparison(self, comparison: str = "", comparison_type: str = "", distress: float = 0.0, accuracy: float = 0.0, response: float = 0.0, gratitude: float = 0.0, self_compassion: float = 0.0, self_reference: float = 0.0, notes: str = "") -> ComparisonEntry:
        """Record a comparison moment."""
        entry_id = f"cmp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ComparisonEntry(
            entry_id=entry_id,
            comparison=comparison or "unspecified",
            comparison_type=comparison_type or "upward",
            distress=distress,
            accuracy=accuracy,
            response=response,
            gratitude=gratitude,
            self_compassion=self_compassion,
            self_reference=self_reference,
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

    def get_comparison_stats(self) -> Dict[str, Any]:
        """Get comparison pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "distress_sum": 0.0, "accuracy_sum": 0.0, "gratitude_sum": 0.0})
        for e in self._entries:
            by_type[e.comparison_type]["count"] += 1
            by_type[e.comparison_type]["distress_sum"] += e.distress
            by_type[e.comparison_type]["accuracy_sum"] += e.accuracy
            by_type[e.comparison_type]["gratitude_sum"] += e.gratitude

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_distress": round(data["distress_sum"] / count, 2),
                "avg_accuracy": round(data["accuracy_sum"] / count, 2),
                "avg_gratitude": round(data["gratitude_sum"] / count, 2),
            }

        # Distress analysis
        high_dist = [e for e in self._entries if e.distress > 0.7]
        low_dist = [e for e in self._entries if e.distress < 0.4]
        if high_dist and low_dist:
            high_dist_resp = sum(e.response for e in high_dist) / len(high_dist)
            low_dist_resp = sum(e.response for e in low_dist) / len(low_dist)
            high_dist_gr = sum(e.gratitude for e in high_dist) / len(high_dist)
            low_dist_gr = sum(e.gratitude for e in low_dist) / len(low_dist)
        else:
            high_dist_resp = 0
            low_dist_resp = 0
            high_dist_gr = 0
            low_dist_gr = 0

        # Self-reference analysis
        high_sr = [e for e in self._entries if e.self_reference > 0.7]
        low_sr = [e for e in self._entries if e.self_reference < 0.4]
        if high_sr and low_sr:
            high_sr_gr = sum(e.gratitude for e in high_sr) / len(high_sr)
            low_sr_gr = sum(e.gratitude for e in low_sr) / len(low_sr)
        else:
            high_sr_gr = 0
            low_sr_gr = 0

        # Detox risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_distress = sum(e.distress for e in recent) / len(recent)
            recent_gratitude = sum(e.gratitude for e in recent) / len(recent)
            detox_risk = recent_distress > 0.7 and recent_gratitude < 0.3
        else:
            detox_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "distress_impact": {
                "high_distress_response": round(high_dist_resp, 2),
                "low_distress_response": round(low_dist_resp, 2),
                "high_distress_gratitude": round(high_dist_gr, 2),
                "low_distress_gratitude": round(low_dist_gr, 2),
            },
            "self_reference_effect": {
                "high_self_reference_gratitude": round(high_sr_gr, 2),
                "low_self_reference_gratitude": round(low_sr_gr, 2),
            },
            "detox_risk": detox_risk,
            "avg_distress": round(sum(e.distress for e in self._entries) / len(self._entries), 2),
            "avg_gratitude": round(sum(e.gratitude for e in self._entries) / len(self._entries), 2),
        }

    def get_comparison_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get comparison suggestion."""
        suggestions = [
            "Comparison is the thief of joy. Not because others have more. But because you're measuring your life with someone else's ruler. Use your own.",
            "You don't know their full story. You see the highlight reel. The promotion. The vacation. The relationship. You don't see the debt. The anxiety. The loneliness. The divorce. Nobody posts the bad parts.",
            "Your only competition is who you were yesterday. Not your neighbor. Not your colleague. Not the influencer. You. Are you better than yesterday? That's the only comparison that matters.",
            "Gratitude is the antidote to comparison. When you're grateful for what you have, you stop noticing what others have. Count your blessings. Literally. Write three things. Now.",
            "Social media is a comparison machine. Designed to make you feel inadequate so you'll buy things. Limit it. Or at least recognize it for what it is: a curated fiction.",
            "The person you're comparing yourself to is probably comparing themselves to someone else. It's a chain of inadequacy. Break the chain. Refuse to play.",
            "Your path is not their path. They started earlier. Or later. They had different parents. Different luck. Different struggles. Different gifts. Different everything. Comparing is comparing apples to spaceships.",
            "Envy is information. It tells you what you want. But it doesn't tell you that you can't have it. It tells you to go get it. Or to want something else. Use it as a compass, not a weapon.",
            "You're not behind. You're not ahead. You're on your own timeline. The 25-year-old millionaire and the 50-year-old graduate are both exactly where they need to be. So are you.",
            "The person who has what you want probably wants what someone else has. It's infinite. It's a game without winners. The only way to win is to stop playing. Choose contentment. Choose your own life."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of gratitude. One recognition that comparison hurts. One breath of contentment. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A comparison detox practice. A gratitude list. A social media break. Medium detox work."
        else:
            capacity_note = "Good capacity. Deep self-reference work. A systematic shift from external to internal metrics. You have the strength to be content with your own path."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Comparison is the most efficient way to make yourself miserable. And it's completely voluntary. Nobody is forcing you to scroll through someone else's curated life and measure your own against it. The comparison habit is a reflex. You see someone succeed and you immediately feel inadequate. But that's a choice. A conditioned choice, but a choice. And it can be unchosen. The alternative is self-reference. Measuring yourself against your own past. Your own potential. Your own values. Not anyone else's. The person who lives by self-reference is immune to comparison. Because they don't care where anyone else is. They care where they are. And where they're going. That's contentment. And it's available to anyone who stops looking at other people's paths and starts walking their own."
        }

    def get_comparison_score(self) -> int:
        """Calculate overall comparison health (0-100)."""
        if not self._entries:
            return 25

        avg_distress = sum(e.distress for e in self._entries) / len(self._entries)
        avg_gratitude = sum(e.gratitude for e in self._entries) / len(self._entries)
        avg_resp = sum(e.response for e in self._entries) / len(self._entries)
        avg_sc = sum(e.self_compassion for e in self._entries) / len(self._entries)
        avg_sr = sum(e.self_reference for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_distress = sum(e.distress for e in recent) / len(recent)
            recent_gratitude = sum(e.gratitude for e in recent) / len(recent)
        else:
            recent_distress = 0
            recent_gratitude = 0

        # Detox penalty
        detox_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_distress_30 = sum(e.distress for e in last_30) / len(last_30)
            recent_gratitude_30 = sum(e.gratitude for e in last_30) / len(last_30)
            if recent_distress_30 > 0.7 and recent_gratitude_30 < 0.3:
                detox_penalty = 15

        # Type variety
        unique_types = len(set(e.comparison_type for e in self._entries))

        score = (avg_gratitude * 30) + (avg_resp * 20) + (avg_sc * 15) + (avg_sr * 15) + (recent_gratitude * 10) + (recent_gratitude * 5) + (unique_types * 2) - (avg_distress * 15) - detox_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_distress"] = round(sum(e.distress for e in self._entries) / len(self._entries), 2)
            self._stats["avg_gratitude"] = round(sum(e.gratitude for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_distress = sum(e.distress for e in recent) / len(recent)
                recent_gratitude = sum(e.gratitude for e in recent) / len(recent)
                self._stats["detox_risk"] = recent_distress > 0.7 and recent_gratitude < 0.3
            else:
                self._stats["detox_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.comparison_detoxifier")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.comparison_detoxifier")

    def _log_entry(self, entry: ComparisonEntry):
        try:
            with open(COMPARISON_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "comparison": entry.comparison,
                    "comparison_type": entry.comparison_type,
                    "distress": entry.distress,
                    "gratitude": entry.gratitude,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.comparison_detoxifier")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cd_instance: Optional[ComparisonDetoxifier] = None
_cd_lock = threading.Lock()


def get_comparison_detoxifier() -> ComparisonDetoxifier:
    global _cd_instance
    with _cd_lock:
        if _cd_instance is None:
            _cd_instance = ComparisonDetoxifier()
        return _cd_instance
