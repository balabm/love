"""
LOVE Celebration Architect — Recognition Intelligence (Modern AI Pattern)

Most achievements pass unnoticed. This architect:

1. CELEBRATION TRACKING
   - Record celebrations and their characteristics
   - Track celebration types (milestone, effort, progress, relationship, recovery)
   - Log celebration outcomes and their effects

2. PATTERN ANALYSIS
   - Identify the user's celebration profile (minimizer, acknowledge, celebrator, over-celebrator)
   - Find celebration styles that increase motivation
   - Detect celebration gaps (achievements without recognition)

3. CELEBRATION DESIGN
   - Suggest celebration practices matched to achievement size
   - Provide celebration planning for milestones
   - Recommendation recognition rituals

4. RECOGNITION CULTIVATION
   - Track the correlation between celebration and sustained motivation
   - Alert when achievements are being rushed past
   - Celebrate the act of celebrating

Architecture:
- record_celebration(achievement, type, celebration, effect): Log celebration
- get_celebration_stats(): Get celebration pattern analysis
- get_celebration_plan(achievement_size, energy): Get plan
- get_celebration_score(): Calculate overall celebration health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "celebration_architect"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CELEBRATION_LOG = DATA_DIR / "celebrations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CelebrationEntry:
    """A tracked celebration entry."""
    entry_id: str = ""
    achievement: str = ""
    celebration_type: str = ""  # milestone, effort, progress, relationship, recovery, daily_win
    celebration_action: str = ""  # what they did to celebrate
    effort_invested: float = 0.5  # 0-1
    celebration_size: float = 0.5  # 0-1, how big the celebration was
    motivation_after: float = 0.5  # 0-1
    satisfaction: float = 0.5  # 0-1
    shared: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CelebrationArchitect:
    """
    Intelligent celebration architect with gap detection and recognition rituals.
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
            "avg_celebration_size": 0.0,
            "avg_motivation": 0.0,
            "celebration_gap": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_celebration(self, achievement: str = "", celebration_type: str = "", celebration_action: str = "", effort_invested: float = 0.5, celebration_size: float = 0.5, motivation_after: float = 0.5, satisfaction: float = 0.5, shared: bool = False, notes: str = "") -> CelebrationEntry:
        """Record a celebration entry."""
        entry_id = f"cel_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CelebrationEntry(
            entry_id=entry_id,
            achievement=achievement or "unspecified",
            celebration_type=celebration_type or "effort",
            celebration_action=celebration_action,
            effort_invested=effort_invested,
            celebration_size=celebration_size,
            motivation_after=motivation_after,
            satisfaction=satisfaction,
            shared=shared,
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

    def get_celebration_stats(self) -> Dict[str, Any]:
        """Get celebration pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "effort_sum": 0.0, "size_sum": 0.0, "motivation_sum": 0.0, "satisfaction_sum": 0.0})
        for e in self._entries:
            by_type[e.celebration_type]["count"] += 1
            by_type[e.celebration_type]["effort_sum"] += e.effort_invested
            by_type[e.celebration_type]["size_sum"] += e.celebration_size
            by_type[e.celebration_type]["motivation_sum"] += e.motivation_after
            by_type[e.celebration_type]["satisfaction_sum"] += e.satisfaction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_effort": round(data["effort_sum"] / count, 2),
                "avg_size": round(data["size_sum"] / count, 2),
                "avg_motivation": round(data["motivation_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        # Size-effort correlation
        high_effort = [e for e in self._entries if e.effort_invested > 0.7]
        if high_effort:
            high_effort_size = sum(e.celebration_size for e in high_effort) / len(high_effort)
        else:
            high_effort_size = 0

        low_effort = [e for e in self._entries if e.effort_invested <= 0.4]
        if low_effort:
            low_effort_size = sum(e.celebration_size for e in low_effort) / len(low_effort)
        else:
            low_effort_size = 0

        # Celebration gap (high effort, small celebration)
        celebration_gap = high_effort_size < 0.4 and len(high_effort) > 3

        # Sharing analysis
        shared = [e for e in self._entries if e.shared]
        sharing_rate = len(shared) / len(self._entries)
        if shared:
            shared_motivation = sum(e.motivation_after for e in shared) / len(shared)
            shared_satisfaction = sum(e.satisfaction for e in shared) / len(shared)
        else:
            shared_motivation = 0
            shared_satisfaction = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_size = sum(e.celebration_size for e in recent) / len(recent)
            recent_motivation = sum(e.motivation_after for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_size = 0
            recent_motivation = 0
            recent_satisfaction = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_size = sum(e.celebration_size for e in older) / len(older)
            older_motivation = sum(e.motivation_after for e in older) / len(older)
            size_trend = recent_size - older_size
            motivation_trend = recent_motivation - older_motivation
        else:
            size_trend = 0
            motivation_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "size_effort_analysis": {
                "high_effort_avg_size": round(high_effort_size, 2),
                "low_effort_avg_size": round(low_effort_size, 2),
            },
            "celebration_gap": celebration_gap,
            "sharing_rate": round(sharing_rate, 2),
            "shared_motivation": round(shared_motivation, 2),
            "shared_satisfaction": round(shared_satisfaction, 2),
            "avg_size": round(sum(e.celebration_size for e in self._entries) / len(self._entries), 2),
            "avg_motivation": round(sum(e.motivation_after for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
            "size_trend": round(size_trend, 2),
            "motivation_trend": round(motivation_trend, 2),
            "recent_size": round(recent_size, 2),
            "recent_motivation": round(recent_motivation, 2),
            "recent_satisfaction": round(recent_satisfaction, 2),
        }

    def get_celebration_plan(self, achievement_size: float = 0.5, energy: float = 0.5) -> Dict[str, Any]:
        """Get plan."""
        if achievement_size < 0.3:
            size_category = "small"
        elif achievement_size < 0.7:
            size_category = "medium"
        else:
            size_category = "large"

        small_celebrations = [
            "Take a 5-minute walk. No phone. Just breathe.",
            "Get a coffee or tea you love. Sit and savor it.",
            "Send yourself a congratulatory text. Seriously.",
            "Do a little dance. 30 seconds. Feel ridiculous. Feel good.",
            "Write 'done' on a sticky note. Put it somewhere you'll see it.",
        ]

        medium_celebrations = [
            "Buy yourself something small you've been wanting. Under $20.",
            "Take an afternoon off. Do something fun. Guilt-free.",
            "Cook or order your favorite meal. Eat it slowly.",
            "Call a friend and tell them what you accomplished. Let them celebrate you.",
            "Watch an episode of your favorite show. No multitasking.",
        ]

        large_celebrations = [
            "Plan an experience. A day trip. A concert. A museum. Something to remember.",
            "Buy the thing. The one you've been putting off. You earned it.",
            "Throw a small gathering. Even if it's just 2 people. Celebrate together.",
            "Take a day off. Sleep in. Do nothing productive. Rest is celebration.",
            "Document the achievement. Write about it. Photo. Video. Make it real.",
        ]

        if size_category == "small":
            selected = small_celebrations
            size_note = "Small win. Don't skip the celebration. Small celebrations build the habit."
        elif size_category == "medium":
            selected = medium_celebrations
            size_note = "Medium win. This deserves real recognition. Not just a mental nod."
        else:
            selected = large_celebrations
            size_note = "Big win. Celebrate properly. This is not indulgence. It's justice."

        if energy < 0.3:
            energy_note = "Low energy. Choose the easiest celebration. Rest counts."
        elif energy < 0.6:
            energy_note = "Moderate energy. A medium celebration will restore you."
        else:
            energy_note = "Good energy. Go big. You have the bandwidth to enjoy it fully."

        return {
            "achievement_size": achievement_size,
            "size_category": size_category,
            "energy": energy,
            "celebration": random.choice(selected),
            "size_note": size_note,
            "energy_note": energy_note,
            "principle": "Celebration is not frivolous. It's the psychological close of a loop. Without it, your brain doesn't register the achievement. You keep chasing, never arriving. Celebrate to mark progress. Celebrate to build motivation. Celebrate because you are worth celebrating.",
        }

    def get_celebration_score(self) -> int:
        """Calculate overall celebration health (0-100)."""
        if not self._entries:
            return 30

        # Celebration size relative to effort
        avg_size = sum(e.celebration_size for e in self._entries) / len(self._entries)
        avg_effort = sum(e.effort_invested for e in self._entries) / len(self._entries)
        size_effort_ratio = avg_size / max(0.1, avg_effort)

        # Motivation and satisfaction
        avg_motivation = sum(e.motivation_after for e in self._entries) / len(self._entries)
        avg_satisfaction = sum(e.satisfaction for e in self._entries) / len(self._entries)

        # Sharing
        shared = [e for e in self._entries if e.shared]
        sharing_rate = len(shared) / len(self._entries)

        # Type variety
        unique_types = len(set(e.celebration_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_size = sum(e.celebration_size for e in recent) / len(recent)
            recent_motivation = sum(e.motivation_after for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_size = 0
            recent_motivation = 0
            recent_satisfaction = 0

        # Gap penalty
        high_effort = [e for e in self._entries if e.effort_invested > 0.7]
        if high_effort:
            high_effort_size = sum(e.celebration_size for e in high_effort) / len(high_effort)
            gap_penalty = 10 if high_effort_size < 0.4 else 0
        else:
            gap_penalty = 0

        score = (avg_size * 15) + (size_effort_ratio * 15) + (avg_motivation * 20) + (avg_satisfaction * 15) + (sharing_rate * 10) + (unique_types * 2) + (recent_size * 15) + (recent_motivation * 10) + (recent_satisfaction * 10) - gap_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_celebration_size"] = round(sum(e.celebration_size for e in self._entries) / len(self._entries), 2)
            self._stats["avg_motivation"] = round(sum(e.motivation_after for e in self._entries) / len(self._entries), 2)

            high_effort = [e for e in self._entries if e.effort_invested > 0.7]
            if high_effort:
                high_effort_size = sum(e.celebration_size for e in high_effort) / len(high_effort)
                self._stats["celebration_gap"] = high_effort_size < 0.4

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

    def _log_entry(self, entry: CelebrationEntry):
        try:
            with open(CELEBRATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "achievement": entry.achievement,
                    "celebration_type": entry.celebration_type,
                    "celebration_action": entry.celebration_action,
                    "effort_invested": entry.effort_invested,
                    "celebration_size": entry.celebration_size,
                    "motivation_after": entry.motivation_after,
                    "satisfaction": entry.satisfaction,
                    "shared": entry.shared,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ca_instance: Optional[CelebrationArchitect] = None
_ca_lock = threading.Lock()


def get_celebration_architect() -> CelebrationArchitect:
    global _ca_instance
    with _ca_lock:
        if _ca_instance is None:
            _ca_instance = CelebrationArchitect()
        return _ca_instance
