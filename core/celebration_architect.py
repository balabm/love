"""
LOVE Celebration Architect — Recognition Intelligence (Modern AI Pattern)

Most people achieve without celebrating. This architect:

1. CELEBRATION TRACKING
   - Record celebrations and their characteristics
   - Track celebration types (achievement, milestone, effort, presence, relationship, survival)
   - Log joy, recognition, and integration from celebrations

2. PATTERN ANALYSIS
   - Identify the user's celebration profile (celebratory, dismissive, conditional, abundant)
   - Find celebration patterns that create motivation and wellbeing
   - Detect achievement without recognition and its costs

3. CELEBRATION BUILDING
   - Suggest celebrations matched to current achievements and capacity
   - Provide frameworks for meaningful recognition
   - Recommend celebrations of effort, not just outcomes

4. RECOGNITION CULTIVATION
   - Track the correlation between celebration and sustained motivation
   - Alert when achievements are being dismissed
   - Celebrate moments of genuine joy in accomplishment

Architecture:
- record_celebration(achievement, type, joy, recognition, integration): Log celebration
- get_celebration_stats(): Get celebration pattern analysis
- get_celebration_suggestion(capacity, context): Get suggestion
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
    """A tracked celebration."""
    entry_id: str = ""
    achievement: str = ""  # what was celebrated
    celebration_type: str = ""  # achievement, milestone, effort, presence, relationship, survival
    joy: float = 0.5  # 0-1
    recognition: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1 how well it was absorbed
    shared: float = 0.0  # 0-1 was it shared?
    gratitude: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CelebrationArchitect:
    """
    Intelligent celebration architect with recognition detection and joy cultivation.
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
            "avg_joy": 0.0,
            "avg_recognition": 0.0,
            "dismissal_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_celebration(self, achievement: str = "", celebration_type: str = "", joy: float = 0.5, recognition: float = 0.0, integration: float = 0.0, shared: float = 0.0, gratitude: float = 0.0, notes: str = "") -> CelebrationEntry:
        """Record a celebration."""
        entry_id = f"cel_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CelebrationEntry(
            entry_id=entry_id,
            achievement=achievement or "unspecified",
            celebration_type=celebration_type or "achievement",
            joy=joy,
            recognition=recognition,
            integration=integration,
            shared=shared,
            gratitude=gratitude,
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
        by_type = defaultdict(lambda: {"count": 0, "joy_sum": 0.0, "recognition_sum": 0.0, "integration_sum": 0.0})
        for e in self._entries:
            by_type[e.celebration_type]["count"] += 1
            by_type[e.celebration_type]["joy_sum"] += e.joy
            by_type[e.celebration_type]["recognition_sum"] += e.recognition
            by_type[e.celebration_type]["integration_sum"] += e.integration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_recognition": round(data["recognition_sum"] / count, 2),
                "avg_integration": round(data["integration_sum"] / count, 2),
            }

        # Joy analysis
        high_joy = [e for e in self._entries if e.joy > 0.7]
        low_joy = [e for e in self._entries if e.joy < 0.4]
        if high_joy and low_joy:
            high_joy_int = sum(e.integration for e in high_joy) / len(high_joy)
            low_joy_int = sum(e.integration for e in low_joy) / len(low_joy)
            high_joy_grat = sum(e.gratitude for e in high_joy) / len(high_joy)
            low_joy_grat = sum(e.gratitude for e in low_joy) / len(low_joy)
        else:
            high_joy_int = 0
            low_joy_int = 0
            high_joy_grat = 0
            low_joy_grat = 0

        # Recognition analysis
        high_rec = [e for e in self._entries if e.recognition > 0.7]
        low_rec = [e for e in self._entries if e.recognition < 0.4]
        if high_rec and low_rec:
            high_rec_int = sum(e.integration for e in high_rec) / len(high_rec)
            low_rec_int = sum(e.integration for e in low_rec) / len(low_rec)
        else:
            high_rec_int = 0
            low_rec_int = 0

        # Shared analysis
        high_shared = [e for e in self._entries if e.shared > 0.7]
        low_shared = [e for e in self._entries if e.shared < 0.4]
        if high_shared and low_shared:
            high_shared_joy = sum(e.joy for e in high_shared) / len(high_shared)
            low_shared_joy = sum(e.joy for e in low_shared) / len(low_shared)
        else:
            high_shared_joy = 0
            low_shared_joy = 0

        # Dismissal risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_recognition = sum(e.recognition for e in recent) / len(recent)
            dismissal_risk = recent_joy < 0.3 and recent_recognition < 0.3
        else:
            dismissal_risk = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "joy_impact": {
                "high_joy_integration": round(high_joy_int, 2),
                "low_joy_integration": round(low_joy_int, 2),
                "high_joy_gratitude": round(high_joy_grat, 2),
                "low_joy_gratitude": round(low_joy_grat, 2),
            },
            "recognition_effect": {
                "high_recognition_integration": round(high_rec_int, 2),
                "low_recognition_integration": round(low_rec_int, 2),
            },
            "shared_effect": {
                "high_shared_joy": round(high_shared_joy, 2),
                "low_shared_joy": round(low_shared_joy, 2),
            },
            "dismissal_risk": dismissal_risk,
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
            "avg_recognition": round(sum(e.recognition for e in self._entries) / len(self._entries), 2),
        }

    def get_celebration_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get celebration suggestion."""
        suggestions = [
            "Celebrate the effort, not just the outcome. You showed up. You tried. You did the hard thing. That deserves recognition even if the result wasn't perfect.",
            "Tell someone. Celebrations shared are celebrations amplified. Text a friend. Call a parent. Post it if you want. Let someone witness your win.",
            "Do something you enjoy. Not productive. Enjoyable. A meal. A movie. A walk. A purchase. Celebrate with pleasure. You earned it.",
            "Write it down. What you did. How it felt. What it took. The written celebration becomes a resource for hard times. Proof that you can.",
            "Celebrate small things. The email sent. The workout done. The difficult conversation had. If you only celebrate big wins, you'll rarely celebrate.",
            "Take a moment of genuine recognition. Stop. Feel it. Let it in. Most people rush past their achievements. Don't. Pause. Breathe. You did this.",
            "Celebrate survival. Some days, getting through is the achievement. The bad day you survived. The loss you endured. The illness you recovered from. These are wins too.",
            "Create a victory ritual. A dance. A phrase. A gesture. Something you do every time you achieve. Rituals make celebration automatic.",
            "Celebrate others too. Their wins. Their efforts. Their presence. Celebration is a culture. Create it around you.",
            "The person who never celebrates is the person who runs out of fuel. Motivation is not infinite. It needs replenishment. Celebration is the refueling station. Stop and fill up."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One acknowledgment. One breath of pride. One moment of recognition. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A small celebration. A treat. A shared moment. Medium recognition."
        else:
            capacity_note = "Good capacity. A real celebration. A ritual. A party. You have the energy to honor your achievement fully."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "We are terrible at celebrating ourselves. We achieve and immediately ask: what's next? We finish and immediately start the next thing. We succeed and immediately focus on what we could have done better. This is not humility. This is self-neglect. Celebration is not arrogance. It's not bragging. It's the acknowledgment that effort matters. That progress matters. That you matter. The person who never celebrates becomes the person who never feels satisfied. Who never feels accomplished. Who burns out chasing a finish line that keeps moving. Stop. Celebrate. Then keep going."
        }

    def get_celebration_score(self) -> int:
        """Calculate overall celebration health (0-100)."""
        if not self._entries:
            return 25

        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_recognition = sum(e.recognition for e in self._entries) / len(self._entries)
        avg_integration = sum(e.integration for e in self._entries) / len(self._entries)
        avg_shared = sum(e.shared for e in self._entries) / len(self._entries)
        avg_gratitude = sum(e.gratitude for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_joy = sum(e.joy for e in recent) / len(recent)
            recent_recognition = sum(e.recognition for e in recent) / len(recent)
        else:
            recent_joy = 0
            recent_recognition = 0

        # Dismissal penalty
        dismissal_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 2:
            dismissal_penalty = 15

        # Type variety
        unique_types = len(set(e.celebration_type for e in self._entries))

        score = (avg_joy * 25) + (avg_recognition * 20) + (avg_integration * 15) + (avg_shared * 15) + (avg_gratitude * 10) + (recent_joy * 5) + (recent_recognition * 5) + (unique_types * 2) - dismissal_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)
            self._stats["avg_recognition"] = round(sum(e.recognition for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_joy = sum(e.joy for e in recent) / len(recent)
                recent_recognition = sum(e.recognition for e in recent) / len(recent)
                self._stats["dismissal_risk"] = recent_joy < 0.3 and recent_recognition < 0.3
            else:
                self._stats["dismissal_risk"] = True

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
                    "joy": entry.joy,
                    "recognition": entry.recognition,
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
