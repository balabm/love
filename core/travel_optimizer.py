"""
LOVE Travel Optimizer — Journey Intelligence (Modern AI Pattern)

Travel is not about distance. It's about disruption of routine and exposure
to the unfamiliar. This optimizer:

1. TRAVEL TRACKING
   - Record trips and their characteristics
   - Track trip types (local exploration, regional, international, inner journey)
   - Log travel outcomes: disruption, learning, restoration, connection

2. PATTERN ANALYSIS
   - Identify the user's travel profile (homebody, weekend warrior, nomad, pilgrim)
   - Find travel patterns that create lasting change vs temporary escape
   - Detect comfort-zone travel (same type, same places, same companions)

3. TRAVEL OPTIMIZATION
   - Suggest trips matched to current needs (restoration, challenge, connection, perspective)
   - Provide pre-trip priming and post-trip integration
   - Recommend the optimal travel frequency and duration

4. JOURNEY CULTIVATION
   - Track the correlation between travel and life satisfaction
   - Alert when life has become too geographically predictable
   - Celebrate journeys that changed something important

Architecture:
- record_trip(destination, type, duration, outcomes): Log trip
- get_travel_stats(): Get travel pattern analysis
- get_trip_suggestion(need, capacity, context): Get suggestion
- get_travel_score(): Calculate overall travel health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "travel_optimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRAVEL_LOG = DATA_DIR / "trips.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TripEntry:
    """A tracked trip entry."""
    entry_id: str = ""
    destination: str = ""  # where
    trip_type: str = ""  # local, regional, international, inner
    duration_days: float = 0.0
    novelty: float = 0.5  # 0-1
    challenge: float = 0.5  # 0-1
    restoration: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    perspective_shift: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1 how well processed afterward
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class TravelOptimizer:
    """
    Intelligent travel optimizer with pattern detection and journey cultivation.
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
            "avg_learning": 0.0,
            "travel_stagnation": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_trip(self, destination: str = "", trip_type: str = "", duration_days: float = 0.0, novelty: float = 0.5, challenge: float = 0.5, restoration: float = 0.0, learning: float = 0.0, connection: float = 0.0, perspective_shift: float = 0.0, integration: float = 0.0, notes: str = "") -> TripEntry:
        """Record a trip entry."""
        entry_id = f"trp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = TripEntry(
            entry_id=entry_id,
            destination=destination or "unspecified",
            trip_type=trip_type or "local",
            duration_days=duration_days,
            novelty=novelty,
            challenge=challenge,
            restoration=restoration,
            learning=learning,
            connection=connection,
            perspective_shift=perspective_shift,
            integration=integration,
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

    def get_travel_stats(self) -> Dict[str, Any]:
        """Get travel pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "restoration_sum": 0.0, "learning_sum": 0.0, "connection_sum": 0.0, "shift_sum": 0.0})
        for e in self._entries:
            by_type[e.trip_type]["count"] += 1
            by_type[e.trip_type]["restoration_sum"] += e.restoration
            by_type[e.trip_type]["learning_sum"] += e.learning
            by_type[e.trip_type]["connection_sum"] += e.connection
            by_type[e.trip_type]["shift_sum"] += e.perspective_shift

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_restoration": round(data["restoration_sum"] / count, 2),
                "avg_learning": round(data["learning_sum"] / count, 2),
                "avg_connection": round(data["connection_sum"] / count, 2),
                "avg_shift": round(data["shift_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_shift"]) if type_stats else ("", {})

        # Novelty analysis
        high_novelty = [e for e in self._entries if e.novelty > 0.7]
        low_novelty = [e for e in self._entries if e.novelty < 0.4]
        if high_novelty and low_novelty:
            high_novelty_shift = sum(e.perspective_shift for e in high_novelty) / len(high_novelty)
            low_novelty_shift = sum(e.perspective_shift for e in low_novelty) / len(low_novelty)
            high_novelty_learning = sum(e.learning for e in high_novelty) / len(high_novelty)
            low_novelty_learning = sum(e.learning for e in low_novelty) / len(low_novelty)
        else:
            high_novelty_shift = 0
            low_novelty_shift = 0
            high_novelty_learning = 0
            low_novelty_learning = 0

        # Duration sweet spot
        short = [e for e in self._entries if e.duration_days < 3]
        medium = [e for e in self._entries if 3 <= e.duration_days < 14]
        long = [e for e in self._entries if e.duration_days >= 14]
        duration_stats = {}
        for label, group in [("short", short), ("medium", medium), ("long", long)]:
            if group:
                duration_stats[label] = {
                    "count": len(group),
                    "avg_restoration": round(sum(e.restoration for e in group) / len(group), 2),
                    "avg_learning": round(sum(e.learning for e in group) / len(group), 2),
                    "avg_shift": round(sum(e.perspective_shift for e in group) / len(group), 2),
                }

        # Integration analysis
        high_int = [e for e in self._entries if e.integration > 0.7]
        low_int = [e for e in self._entries if e.integration < 0.4]
        if high_int and low_int:
            high_int_shift = sum(e.perspective_shift for e in high_int) / len(high_int)
            low_int_shift = sum(e.perspective_shift for e in low_int) / len(low_int)
        else:
            high_int_shift = 0
            low_int_shift = 0

        # Travel stagnation detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
        if recent:
            recent_novelty = sum(e.novelty for e in recent) / len(recent)
            recent_challenge = sum(e.challenge for e in recent) / len(recent)
            travel_stagnation = recent_novelty < 0.3 and recent_challenge < 0.3
        else:
            travel_stagnation = True

        # Trend
        if len(self._entries) > 5:
            older = list(self._entries)[-10:-5]
            recent_entries = list(self._entries)[-5:]
            if older and recent_entries:
                older_shift = sum(e.perspective_shift for e in older) / len(older)
                recent_shift = sum(e.perspective_shift for e in recent_entries) / len(recent_entries)
                shift_trend = recent_shift - older_shift
            else:
                shift_trend = 0
        else:
            shift_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "novelty_impact": {
                "high_novelty_shift": round(high_novelty_shift, 2),
                "low_novelty_shift": round(low_novelty_shift, 2),
                "high_novelty_learning": round(high_novelty_learning, 2),
                "low_novelty_learning": round(low_novelty_learning, 2),
            },
            "duration_stats": duration_stats,
            "integration_effect": {
                "high_integration_shift": round(high_int_shift, 2),
                "low_integration_shift": round(low_int_shift, 2),
            },
            "travel_stagnation": travel_stagnation,
            "avg_restoration": round(sum(e.restoration for e in self._entries) / len(self._entries), 2),
            "avg_learning": round(sum(e.learning for e in self._entries) / len(self._entries), 2),
            "avg_connection": round(sum(e.connection for e in self._entries) / len(self._entries), 2),
            "shift_trend": round(shift_trend, 2),
        }

    def get_trip_suggestion(self, need: str = "", capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get trip suggestion."""
        suggestions = {
            "restoration": [
                "Go somewhere quiet. Not fancy. Just quiet. No agenda. No photos. Just be somewhere your phone doesn't work and your mind finally does.",
                "Take a train instead of driving. Look out the window. The world moves slower from a train. That's the point.",
                "Sleep somewhere you've never slept. A friend's couch. A cheap hotel. A tent. The unfamiliar bed resets the familiar mind.",
            ],
            "challenge": [
                "Go somewhere where you don't speak the language. Where you can't read the signs. Where you have to be humble. That's travel as education.",
                "Travel alone. To somewhere that scares you a little. The fear is the doorway. Courage is what you find on the other side.",
                "Take the cheapest possible trip. Constraints create creativity. The best stories come from things going slightly wrong.",
            ],
            "connection": [
                "Visit an old friend. Not for an event. Just to be in their presence. Travel for people, not places.",
                "Go to a gathering of people who share something you care about. A conference. A retreat. A festival. Shared passion is instant connection.",
                "Visit family. Even the difficult ones. Especially the difficult ones. Travel can repair what distance has frozen.",
            ],
            "perspective": [
                "Go somewhere very different from where you live. Different climate. Different economy. Different values. Perspective requires contrast.",
                "Visit a place of historical significance. Stand where history happened. Time collapses. You realize your worries are small and your life is brief.",
                "Go to the poorest place you can ethically visit. Not to feel guilty. To understand. Perspective is the gift of seeing how others live.",
            ],
            "general": [
                "The best trip is the one you almost didn't take. Book it before you're ready. The readiness comes during.",
                "Travel is not about collecting places. It's about disrupting the story you tell about yourself. The you who travels is not the you who stays home.",
                "If you haven't been somewhere that changed your mind in the last year, you haven't really traveled. You've just relocated.",
            ],
        }

        selected = suggestions.get(need, suggestions["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. Local exploration. A new neighborhood. A different cafe. A park you've never visited."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Weekend trip. Nearby city. Day hike. Small adventure."
        else:
            capacity_note = "Good capacity. Real travel. The trip you've been thinking about. Do it. The person who returns will thank you."

        return {
            "need": need or "general",
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Travel is not a luxury. It's a necessity for anyone who wants to avoid becoming a caricature of themselves. The person who never leaves home becomes a fossil of their own habits. Travel breaks the mold. Even bad travel teaches you what you actually need. Even uncomfortable travel shows you what you're capable of. The goal is not relaxation. The goal is transformation. Every trip should change something. If it doesn't, it was just transportation.",
        }

    def get_travel_score(self) -> int:
        """Calculate overall travel health (0-100)."""
        if not self._entries:
            return 25

        avg_restoration = sum(e.restoration for e in self._entries) / len(self._entries)
        avg_learning = sum(e.learning for e in self._entries) / len(self._entries)
        avg_connection = sum(e.connection for e in self._entries) / len(self._entries)
        avg_shift = sum(e.perspective_shift for e in self._entries) / len(self._entries)
        avg_integration = sum(e.integration for e in self._entries) / len(self._entries)
        avg_novelty = sum(e.novelty for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-5:]
        if recent:
            recent_shift = sum(e.perspective_shift for e in recent) / len(recent)
            recent_learning = sum(e.learning for e in recent) / len(recent)
        else:
            recent_shift = 0
            recent_learning = 0

        # Stagnation penalty
        stagnation_penalty = 0
        last_180 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
        if len(last_180) < 2:
            stagnation_penalty = 15

        # Type variety
        unique_types = len(set(e.trip_type for e in self._entries))

        score = (avg_restoration * 15) + (avg_learning * 20) + (avg_connection * 15) + (avg_shift * 20) + (avg_integration * 10) + (avg_novelty * 10) + (recent_shift * 5) + (recent_learning * 5) + (unique_types * 2) - stagnation_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_restoration"] = round(sum(e.restoration for e in self._entries) / len(self._entries), 2)
            self._stats["avg_learning"] = round(sum(e.learning for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=180)).isoformat()]
            if recent:
                recent_novelty = sum(e.novelty for e in recent) / len(recent)
                recent_challenge = sum(e.challenge for e in recent) / len(recent)
                self._stats["travel_stagnation"] = recent_novelty < 0.3 and recent_challenge < 0.3
            else:
                self._stats["travel_stagnation"] = True

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

    def _log_entry(self, entry: TripEntry):
        try:
            with open(TRAVEL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "destination": entry.destination,
                    "trip_type": entry.trip_type,
                    "duration_days": entry.duration_days,
                    "perspective_shift": entry.perspective_shift,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_to_instance: Optional[TravelOptimizer] = None
_to_lock = threading.Lock()


def get_travel_optimizer() -> TravelOptimizer:
    global _to_instance
    with _to_lock:
        if _to_instance is None:
            _to_instance = TravelOptimizer()
        return _to_instance
