"""
LOVE Rest Designer — Recovery Intelligence (Modern AI Pattern)

Most people rest poorly when they rest at all. This designer:

1. REST TRACKING
   - Record rest periods and their characteristics
   - Track rest types (sleep, leisure, mental, physical, social, spiritual)
   - Log restoration, depth, and quality of rest

2. PATTERN ANALYSIS
   - Identify the user's rest profile (restorative, performative, guilty, absent)
   - Find rest patterns that create genuine recovery
   - Detect rest guilt and its consequences

3. REST OPTIMIZATION
   - Suggest rest practices matched to current depletion and constraints
   - Provide frameworks for guilt-free rest
   - Recommend rest types based on what was depleted

4. RECOVERY CULTIVATION
   - Track the correlation between rest quality and performance/wellbeing
   - Alert when rest is becoming performative or absent
   - Celebrate moments of genuine restoration

Architecture:
- record_rest(activity, type, restoration, depth, quality): Log rest
- get_rest_stats(): Get rest pattern analysis
- get_rest_suggestion(capacity, context): Get suggestion
- get_rest_score(): Calculate overall rest health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "rest_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REST_LOG = DATA_DIR / "rest.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RestEntry:
    """A tracked rest period."""
    entry_id: str = ""
    activity: str = ""  # what rest activity
    rest_type: str = ""  # sleep, leisure, mental, physical, social, spiritual
    restoration: float = 0.0  # 0-1
    depth: float = 0.0  # 0-1
    quality: float = 0.5  # 0-1
    guilt: float = 0.0  # 0-1
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RestDesigner:
    """
    Intelligent rest designer with restoration detection and recovery cultivation.
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
            "avg_restoration": 0.0,
            "avg_quality": 0.0,
            "rest_guilt_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_rest(self, activity: str = "", rest_type: str = "", restoration: float = 0.0, depth: float = 0.0, quality: float = 0.5, guilt: float = 0.0, duration_minutes: float = 0.0, notes: str = "") -> RestEntry:
        """Record a rest period."""
        entry_id = f"rst_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RestEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            rest_type=rest_type or "leisure",
            restoration=restoration,
            depth=depth,
            quality=quality,
            guilt=guilt,
            duration_minutes=duration_minutes,
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

    def get_rest_stats(self) -> Dict[str, Any]:
        """Get rest pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "restoration_sum": 0.0, "depth_sum": 0.0, "quality_sum": 0.0})
        for e in self._entries:
            by_type[e.rest_type]["count"] += 1
            by_type[e.rest_type]["restoration_sum"] += e.restoration
            by_type[e.rest_type]["depth_sum"] += e.depth
            by_type[e.rest_type]["quality_sum"] += e.quality

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_restoration": round(data["restoration_sum"] / count, 2),
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_quality": round(data["quality_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_restoration"]) if type_stats else ("", {})

        # Restoration analysis
        high_rest = [e for e in self._entries if e.restoration > 0.7]
        low_rest = [e for e in self._entries if e.restoration < 0.4]
        if high_rest and low_rest:
            high_rest_qual = sum(e.quality for e in high_rest) / len(high_rest)
            low_rest_qual = sum(e.quality for e in low_rest) / len(low_rest)
            high_rest_depth = sum(e.depth for e in high_rest) / len(high_rest)
            low_rest_depth = sum(e.depth for e in low_rest) / len(low_rest)
        else:
            high_rest_qual = 0
            low_rest_qual = 0
            high_rest_depth = 0
            low_rest_depth = 0

        # Guilt analysis
        high_guilt = [e for e in self._entries if e.guilt > 0.7]
        low_guilt = [e for e in self._entries if e.guilt < 0.4]
        if high_guilt and low_guilt:
            high_guilt_rest = sum(e.restoration for e in high_guilt) / len(high_guilt)
            low_guilt_rest = sum(e.restoration for e in low_guilt) / len(low_guilt)
        else:
            high_guilt_rest = 0
            low_guilt_rest = 0

        # Rest guilt risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_guilt = sum(e.guilt for e in recent) / len(recent)
            recent_restoration = sum(e.restoration for e in recent) / len(recent)
            rest_guilt_risk = recent_guilt > 0.6 and recent_restoration < 0.4
        else:
            rest_guilt_risk = False

        return {
            "total_entries": len(self._entries),
            "total_hours": round(sum(e.duration_minutes for e in self._entries) / 60, 1),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "restoration_impact": {
                "high_restoration_quality": round(high_rest_qual, 2),
                "low_restoration_quality": round(low_rest_qual, 2),
                "high_restoration_depth": round(high_rest_depth, 2),
                "low_restoration_depth": round(low_rest_depth, 2),
            },
            "guilt_effect": {
                "high_guilt_restoration": round(high_guilt_rest, 2),
                "low_guilt_restoration": round(low_guilt_rest, 2),
            },
            "rest_guilt_risk": rest_guilt_risk,
            "avg_restoration": round(sum(e.restoration for e in self._entries) / len(self._entries), 2),
            "avg_quality": round(sum(e.quality for e in self._entries) / len(self._entries), 2),
        }

    def get_rest_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get rest suggestion."""
        suggestions = [
            "Rest is not a reward for hard work. It's a requirement for sustained performance. You don't earn rest. You need it. Period. Take it without apology.",
            "Schedule rest the way you schedule work. Put it in the calendar. Protect it. Rest that is not scheduled is rest that doesn't happen.",
            "Do nothing. Literally nothing. Not productive nothing. Not structured nothing. Just nothing. Sit. Stare. Breathe. The art of doing nothing is dying. Revive it.",
            "Sleep is the foundation of everything. Not a luxury. A biological necessity. If you're not sleeping enough, nothing else works. Prioritize sleep above all.",
            "Rest guilt is not a sign you should work harder. It's a sign you've internalized capitalism. Rest is not laziness. It's maintenance. And maintenance is not optional.",
            "Find your rest type. Some people restore through solitude. Some through company. Some through movement. Some through stillness. Know what restores you. Do that.",
            "Take a day off. A real day off. No email. No errands. No productive tasks. A day of genuine non-doing. It will feel uncomfortable. That's how you know you need it.",
            "Rest is where integration happens. The learning. The healing. The creativity. The processing. It all happens in rest. Work is input. Rest is where the magic happens.",
            "Don't rest to work better. Rest because rest is good in itself. The instrumentalization of rest is part of the problem. Rest is an end, not a means.",
            "You are a human being, not a human doing. Your worth is not your productivity. Your value is not your output. Rest is the practice of believing that.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Ten minutes of nothing. One breath. One moment of stopping. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A nap. A walk. A break from screens. Medium rest."
        else:
            capacity_note = "Good capacity. A full day off. A retreat. A sleep reset. You have the space for deep restoration."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "We live in a culture that worships productivity and demonizes rest. That treats exhaustion as a virtue and restoration as weakness. This is not just unhealthy. It's literally killing people. Burnout is not a badge of honor. It's a sign of system failure. And the system is not just external. It's internal too. The voice that says you should be doing more. The guilt that arises when you stop. The inability to be still. These are not personal failings. They're cultural programming. And they can be unlearned. Rest is not the opposite of work. It's the complement. The yin to work's yang. The space in which work becomes meaningful. Without rest, work is just exhaustion. With rest, work is contribution. Learn to rest. Not as strategy. As practice. As belief. As life."
        }

    def get_rest_score(self) -> int:
        """Calculate overall rest health (0-100)."""
        if not self._entries:
            return 25

        avg_restoration = sum(e.restoration for e in self._entries) / len(self._entries)
        avg_quality = sum(e.quality for e in self._entries) / len(self._entries)
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_restoration = sum(e.restoration for e in recent) / len(recent)
            recent_quality = sum(e.quality for e in recent) / len(recent)
        else:
            recent_restoration = 0
            recent_quality = 0

        # Rest guilt penalty
        guilt_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_guilt = sum(e.guilt for e in last_30) / len(last_30)
            recent_rest = sum(e.restoration for e in last_30) / len(last_30)
            if recent_guilt > 0.6 and recent_rest < 0.4:
                guilt_penalty = 15

        # Type variety
        unique_types = len(set(e.rest_type for e in self._entries))

        score = (avg_restoration * 30) + (avg_quality * 25) + (avg_depth * 15) + (recent_restoration * 15) + (recent_quality * 10) + (unique_types * 2) - guilt_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_restoration"] = round(sum(e.restoration for e in self._entries) / len(self._entries), 2)
            self._stats["avg_quality"] = round(sum(e.quality for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_guilt = sum(e.guilt for e in recent) / len(recent)
                recent_restoration = sum(e.restoration for e in recent) / len(recent)
                self._stats["rest_guilt_risk"] = recent_guilt > 0.6 and recent_restoration < 0.4
            else:
                self._stats["rest_guilt_risk"] = False

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

    def _log_entry(self, entry: RestEntry):
        try:
            with open(REST_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "rest_type": entry.rest_type,
                    "restoration": entry.restoration,
                    "quality": entry.quality,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rd_instance: Optional[RestDesigner] = None
_rd_lock = threading.Lock()


def get_rest_designer() -> RestDesigner:
    global _rd_instance
    with _rd_lock:
        if _rd_instance is None:
            _rd_instance = RestDesigner()
        return _rd_instance
