"""
LOVE Presence Amplifier — Embodied Awareness Intelligence (Modern AI Pattern)

Most presence is lost in thought about the past or future. This amplifier:

1. PRESENCE TRACKING
   - Record presence moments and their characteristics
   - Track presence depth and its correlation with experience quality
   - Log presence interruptions and their sources

2. PATTERN ANALYSIS
   - Identify the user's presence profile (somatic, sensory, relational, environmental)
   - Find presence anchors (what reliably brings them into the present)
   - Detect presence gaps (when they were physically present but mentally absent)

3. PRESENCE PRACTICES
   - Suggest presence techniques matched to context and capacity
   - Provide micro-presence practices for busy moments
   - Recommend deep presence rituals for important experiences

4. AMPLIFICATION
   - Track the correlation between presence and satisfaction
   - Alert when presence is being compromised by digital or mental distractions
   - Celebrate moments of full presence

Architecture:
- record_presence(context, depth, anchors, interruptions): Log presence
- get_presence_stats(): Get presence pattern analysis
- get_presence_practice(context, capacity): Get practice
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

DATA_DIR = Path(__file__).parent.parent / "data" / "presence_amplifier"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRESENCE_LOG = DATA_DIR / "presence.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PresenceEntry:
    """A tracked presence entry."""
    entry_id: str = ""
    context: str = ""  # meal, conversation, work, nature, commute, shower, bedtime
    depth: float = 0.5  # 0-1
    anchors: List[str] = field(default_factory=list)  # what brought them into presence
    interruptions: List[str] = field(default_factory=list)  # what pulled them away
    satisfaction: float = 0.5  # 0-1
    duration_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PresenceAmplifier:
    """
    Intelligent presence amplifier with anchor identification and interruption management.
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
            "avg_satisfaction": 0.0,
            "best_anchor": "",
            "primary_interruption": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_presence(self, context: str = "", depth: float = 0.5, anchors: Optional[List[str]] = None, interruptions: Optional[List[str]] = None, satisfaction: float = 0.5, duration: float = 0, notes: str = "") -> PresenceEntry:
        """Record a presence entry."""
        entry_id = f"pres_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PresenceEntry(
            entry_id=entry_id,
            context=context or "general",
            depth=depth,
            anchors=anchors or [],
            interruptions=interruptions or [],
            satisfaction=satisfaction,
            duration_minutes=duration,
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

    def get_presence_stats(self) -> Dict[str, Any]:
        """Get presence pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "satisfaction_sum": 0.0, "duration_sum": 0.0})
        for e in self._entries:
            by_context[e.context]["count"] += 1
            by_context[e.context]["depth_sum"] += e.depth
            by_context[e.context]["satisfaction_sum"] += e.satisfaction
            by_context[e.context]["duration_sum"] += e.duration_minutes

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
            }

        # Anchor analysis
        by_anchor = defaultdict(lambda: {"count": 0, "depth_sum": 0.0})
        for e in self._entries:
            for anchor in e.anchors:
                by_anchor[anchor]["count"] += 1
                by_anchor[anchor]["depth_sum"] += e.depth

        anchor_stats = {}
        for a, data in by_anchor.items():
            count = data["count"]
            if count >= 2:
                anchor_stats[a] = {
                    "count": count,
                    "avg_depth": round(data["depth_sum"] / count, 2),
                }

        best_anchor = max(anchor_stats.items(), key=lambda x: x[1]["avg_depth"]) if anchor_stats else ("", {})

        # Interruption analysis
        by_interruption = defaultdict(lambda: {"count": 0, "depth_sum": 0.0})
        for e in self._entries:
            for inter in e.interruptions:
                by_interruption[inter]["count"] += 1
                by_interruption[inter]["depth_sum"] += e.depth

        interruption_stats = {}
        for inter, data in by_interruption.items():
            count = data["count"]
            interruption_stats[inter] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
            }

        primary_interruption = min(interruption_stats.items(), key=lambda x: x[1]["avg_depth"]) if interruption_stats else ("", {})

        # Depth trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_satisfaction = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_depth = sum(e.depth for e in older) / len(older)
            older_satisfaction = sum(e.satisfaction for e in older) / len(older)
            depth_trend = recent_depth - older_depth
            satisfaction_trend = recent_satisfaction - older_satisfaction
        else:
            depth_trend = 0
            satisfaction_trend = 0

        # Presence gap detection
        high_interruption = sum(1 for e in self._entries if len(e.interruptions) > 2) / len(self._entries)
        presence_gap_risk = high_interruption > 0.3

        return {
            "total_entries": len(self._entries),
            "context_stats": context_stats,
            "anchor_stats": anchor_stats,
            "best_anchor": best_anchor[0],
            "interruption_stats": interruption_stats,
            "primary_interruption": primary_interruption[0],
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_satisfaction": round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2),
            "depth_trend": round(depth_trend, 2),
            "satisfaction_trend": round(satisfaction_trend, 2),
            "presence_gap_risk": presence_gap_risk,
        }

    def get_presence_practice(self, context: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "meal": [
                "Eat the first 3 bites with full attention. Taste, texture, temperature.",
                "Put fork down between bites. Chew thoroughly.",
                "Notice the colors on your plate. Appreciate the arrangement.",
            ],
            "conversation": [
                "Listen without planning your response. Let them finish completely.",
                "Notice their body language. What's not being said?",
                "Make eye contact. Let them know you're fully here.",
            ],
            "work": [
                "Set a 25-minute timer. Commit to one task. Nothing else.",
                "Notice your breath before starting. One conscious breath.",
                "When distracted, pause. Notice where your mind went. Return gently.",
            ],
            "nature": [
                "Find one small thing and examine it fully. A leaf, a stone, a flower.",
                "Listen for 5 different sounds. Near and far.",
                "Feel the air on your skin. Temperature, movement, humidity.",
            ],
            "commute": [
                "Feel your body in the seat. Weight, pressure, temperature.",
                "Look at one thing outside and really see it. Not just glance.",
                "Breathe deeply 3 times. Arrive calm, not rushed.",
            ],
            "shower": [
                "Feel the water on each part of your body. Start at head, move down.",
                "Notice the temperature change as you move.",
                "Listen to the sound of the water. Just that sound.",
            ],
            "bedtime": [
                "Feel the weight of your body on the bed. Sink into it.",
                "Notice 3 breaths. Inhale cool, exhale warm.",
                "Let go of today. Nothing needs to be solved right now.",
            ],
        }

        selected = practices.get(context, practices["work"])

        if capacity < 0.3:
            capacity_note = "Low capacity. Choose one tiny moment of presence. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A few minutes of full presence will restore you."
        else:
            capacity_note = "High capacity. This is a good time for deeper presence practices."

        return {
            "context": context or "general",
            "capacity": capacity,
            "practice": random.choice(selected),
            "capacity_note": capacity_note,
            "reminder": "Presence is not a state you achieve. It's a choice you make, moment by moment. The past is memory. The future is imagination. Only the present is real.",
        }

    def get_presence_score(self) -> int:
        """Calculate overall presence health (0-100)."""
        if not self._entries:
            return 30

        # Depth
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)

        # Satisfaction correlation
        avg_satisfaction = sum(e.satisfaction for e in self._entries) / len(self._entries)

        # Low interruptions
        avg_interruptions = sum(len(e.interruptions) for e in self._entries) / len(self._entries)

        # Anchor variety
        all_anchors = set()
        for e in self._entries:
            all_anchors.update(e.anchors)

        # Context variety
        unique_contexts = len(set(e.context for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_satisfaction = sum(e.satisfaction for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_satisfaction = 0

        # Duration (longer presence = deeper)
        avg_duration = sum(e.duration_minutes for e in self._entries) / len(self._entries)

        score = (avg_depth * 25) + (avg_satisfaction * 20) + ((5 - avg_interruptions) / 5 * 15) + (len(all_anchors) * 2) + (unique_contexts * 2) + (recent_depth * 15) + (recent_satisfaction * 10) + (avg_duration / 60 * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_satisfaction"] = round(sum(e.satisfaction for e in self._entries) / len(self._entries), 2)

            by_anchor = defaultdict(lambda: {"depth": 0.0, "count": 0})
            for e in self._entries:
                for a in e.anchors:
                    by_anchor[a]["depth"] += e.depth
                    by_anchor[a]["count"] += 1
            if by_anchor:
                best = max(by_anchor.items(), key=lambda x: x[1]["depth"] / max(1, x[1]["count"]))
                self._stats["best_anchor"] = best[0]

            by_interruption = defaultdict(lambda: {"depth": 0.0, "count": 0})
            for e in self._entries:
                for i in e.interruptions:
                    by_interruption[i]["depth"] += e.depth
                    by_interruption[i]["count"] += 1
            if by_interruption:
                worst = min(by_interruption.items(), key=lambda x: x[1]["depth"] / max(1, x[1]["count"]))
                self._stats["primary_interruption"] = worst[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.presence_amplifier")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.presence_amplifier")

    def _log_entry(self, entry: PresenceEntry):
        try:
            with open(PRESENCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "context": entry.context,
                    "depth": entry.depth,
                    "anchors": entry.anchors,
                    "interruptions": entry.interruptions,
                    "satisfaction": entry.satisfaction,
                    "duration": entry.duration_minutes,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.presence_amplifier")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pa_instance: Optional[PresenceAmplifier] = None
_pa_lock = threading.Lock()


    
def get_presence_amplifier() -> PresenceAmplifier:
    global _pa_instance
    with _pa_lock:
        if _pa_instance is None:
            _pa_instance = PresenceAmplifier()
        return _pa_instance
