"""
LOVE Attention Guardian — Focus Intelligence (Modern AI Pattern)

Attention is the scarcest resource of the 21st century. This guardian:

1. ATTENTION TRACKING
   - Record attention investments and their returns
   - Track attention fragmentation and deep focus periods
   - Log what captures attention (intentionally and unintentionally)

2. PATTERN ANALYSIS
   - Identify attention style (laser, scattered, rhythmic, immersive)
   - Find attention hijackers (apps, people, thoughts, environments)
   - Detect attention debt and its causes

3. PROTECTION STRATEGIES
   - Suggest attention-protection rituals for current context
   - Provide focus-restoration techniques after fragmentation
   - Recommend attention-hygiene practices

4. QUALITY OPTIMIZATION
   - Track the correlation between attention quality and output quality
   - Alert when attention is being spent on low-value inputs
   - Celebrate deep attention moments

Architecture:
- record_attention(investment, duration, depth, return): Log attention
- get_attention_stats(): Get attention pattern analysis
- get_protection_strategy(threat, current_depth): Get defense plan
- get_attention_score(): Calculate overall attention health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "attention_guardian"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ATTENTION_LOG = DATA_DIR / "attention.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AttentionEvent:
    """A tracked attention event."""
    event_id: str = ""
    investment: str = ""  # what attention was given to
    category: str = ""  # work, learning, creation, connection, entertainment, admin, worry, distraction
    duration_minutes: float = 0.0
    depth: float = 0.5  # 0-1, how focused
    return_value: float = 0.5  # 0-1, value generated
    fragmented: bool = False  # was attention broken
    hijacker: str = ""  # what broke it (if anything)
    intentionality: float = 0.5  # 0-1, how intentional
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AttentionGuardian:
    """
    Intelligent attention guardian with hijacker detection and protection strategy generation.
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
        self._events: deque = deque(maxlen=300)
        self._stats = {
            "total_events": 0,
            "avg_depth": 0.0,
            "avg_return": 0.0,
            "fragmentation_rate": 0.0,
            "top_hijacker": "",
            "attention_debt": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_attention(self, investment: str = "", category: str = "", duration: float = 0, depth: float = 0.5, return_value: float = 0.5, fragmented: bool = False, hijacker: str = "", intentionality: float = 0.5, notes: str = "") -> AttentionEvent:
        """Record an attention event."""
        event_id = f"attn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._events)}"
        event = AttentionEvent(
            event_id=event_id,
            investment=investment or "unspecified",
            category=category or "work",
            duration_minutes=duration,
            depth=depth,
            return_value=return_value,
            fragmented=fragmented,
            hijacker=hijacker,
            intentionality=intentionality,
            notes=notes,
        )

        with self._lock:
            self._events.append(event)
            self._stats["total_events"] += 1
            self._update_stats()

        self._save_stats()
        self._log_event(event)

        return event

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_attention_stats(self) -> Dict[str, Any]:
        """Get attention pattern analysis."""
        if not self._events:
            return {"status": "insufficient_data"}

        # Category analysis
        by_category = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "return_sum": 0.0, "fragmented": 0, "intentionality_sum": 0.0})
        for e in self._events:
            by_category[e.category]["count"] += 1
            by_category[e.category]["depth_sum"] += e.depth
            by_category[e.category]["return_sum"] += e.return_value
            if e.fragmented:
                by_category[e.category]["fragmented"] += 1
            by_category[e.category]["intentionality_sum"] += e.intentionality

        category_stats = {}
        for c, data in by_category.items():
            count = data["count"]
            category_stats[c] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_return": round(data["return_sum"] / count, 2),
                "fragmentation_rate": round(data["fragmented"] / count, 2),
                "avg_intentionality": round(data["intentionality_sum"] / count, 2),
            }

        # Hijacker analysis
        hijackers = [e.hijacker for e in self._events if e.hijacker]
        by_hijacker = defaultdict(lambda: {"count": 0, "depth_impact": 0.0})
        for e in self._events:
            if e.hijacker:
                by_hijacker[e.hijacker]["count"] += 1
                by_hijacker[e.hijacker]["depth_impact"] += (1 - e.depth)

        hijacker_stats = {}
        for h, data in by_hijacker.items():
            count = data["count"]
            hijacker_stats[h] = {
                "count": count,
                "avg_depth_impact": round(data["depth_impact"] / count, 2),
            }

        top_hijacker = max(hijacker_stats.items(), key=lambda x: x[1]["count"]) if hijacker_stats else ("", {})

        # Intentionality analysis
        intentional = [e for e in self._events if e.intentionality > 0.6]
        accidental = [e for e in self._events if e.intentionality < 0.4]
        if intentional and accidental:
            intentional_return = sum(e.return_value for e in intentional) / len(intentional)
            accidental_return = sum(e.return_value for e in accidental) / len(accidental)
            intentionality_effect = intentional_return - accidental_return
        else:
            intentionality_effect = 0

        # Deep work analysis
        deep_sessions = [e for e in self._events if e.depth > 0.7]
        deep_ratio = len(deep_sessions) / len(self._events)

        # Attention debt
        recent = [e for e in self._events if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        if recent:
            recent_fragmentation = sum(1 for e in recent if e.fragmented) / len(recent)
            recent_low_return = sum(1 for e in recent if e.return_value < 0.3) / len(recent)
            attention_debt = recent_fragmentation > 0.5 or recent_low_return > 0.5
        else:
            attention_debt = False

        return {
            "total_events": len(self._events),
            "category_stats": category_stats,
            "hijacker_stats": hijacker_stats,
            "top_hijacker": top_hijacker[0],
            "intentionality_effect": round(intentionality_effect, 2),
            "deep_work_ratio": round(deep_ratio, 2),
            "avg_depth": round(sum(e.depth for e in self._events) / len(self._events), 2),
            "avg_return": round(sum(e.return_value for e in self._events) / len(self._events), 2),
            "fragmentation_rate": round(sum(1 for e in self._events if e.fragmented) / len(self._events), 2),
            "attention_debt": attention_debt,
        }

    def get_protection_strategy(self, threat: str = "", current_depth: float = 0.5, context: str = "work") -> Dict[str, Any]:
        """Get defense plan."""
        defenses = {
            "phone": [
                "Put phone in another room. Not pocket. Another room.",
                "Use app blockers during focus blocks",
                "Turn on Do Not Disturb. Allow calls from no one.",
                "Charge phone face-down and across the room",
            ],
            "notifications": [
                "Turn off ALL non-essential notifications. All of them.",
                "Batch check messages at 3 specific times daily",
                "Use 'Focus' mode that hides badges and banners",
                "Unsubscribe from everything you don't actively need",
            ],
            "people": [
                "Put on noise-canceling headphones. Even without music.",
                "Use a physical 'deep work' sign or status message",
                "Work from a different location when focus is critical",
                "Schedule 'office hours' for interruptions",
            ],
            "thoughts": [
                "Keep a 'parking lot' notebook for intruding thoughts",
                "Do a 2-minute brain dump before starting deep work",
                "Use the 'not now' technique: acknowledge thought, defer it",
                "Practice single-tasking: one tab, one window, one task",
            ],
            "environment": [
                "Clear your desk to only what's needed for this task",
                "Use white noise or instrumental music to mask disruptions",
                "Face a wall or window, not the room entrance",
                "Adjust lighting: brighter for alertness, dimmer for creativity",
            ],
            "fatigue": [
                "Take a 20-minute nap. Set an alarm. No scrolling first.",
                "Do 5 minutes of movement. Blood flow restores focus.",
                "Switch to a different type of task for 30 minutes",
                "Hydrate. Dehydration masquerades as distraction.",
            ],
        }

        selected = defenses.get(threat, defenses["phone"])
        defense = random.choice(selected)

        if current_depth < 0.3:
            state_note = "Your attention is scattered. Don't force deep work. Do a reset first."
        elif current_depth < 0.6:
            state_note = "Moderate focus. One protection should get you to deep."
        else:
            state_note = "Good depth. Protect it fiercely. Don't peek at anything else."

        return {
            "threat": threat or "general",
            "current_depth": current_depth,
            "context": context,
            "defense": defense,
            "state_note": state_note,
            "restoration": "If broken: Stop. Breathe 3 times. Read your intention aloud. Start again.",
            "principle": "Attention is the currency of creation. Spend it on what matters. Defend it from what doesn't.",
        }

    def get_attention_score(self) -> int:
        """Calculate overall attention health (0-100)."""
        if not self._events:
            return 40

        # Depth
        avg_depth = sum(e.depth for e in self._events) / len(self._events)

        # Return on attention
        avg_return = sum(e.return_value for e in self._events) / len(self._events)

        # Low fragmentation
        fragmentation = sum(1 for e in self._events if e.fragmented) / len(self._events)

        # Intentionality
        avg_intentionality = sum(e.intentionality for e in self._events) / len(self._events)

        # Deep work ratio
        deep_ratio = sum(1 for e in self._events if e.depth > 0.7) / len(self._events)

        # Recent trend
        recent = list(self._events)[-20:]
        recent_depth = sum(e.depth for e in recent) / len(recent)
        older = list(self._events)[:-20] if len(self._events) > 20 else []
        if older:
            older_depth = sum(e.depth for e in older) / len(older)
            trend = recent_depth - older_depth
        else:
            trend = 0

        score = (avg_depth * 25) + (avg_return * 20) + ((1 - fragmentation) * 15) + (avg_intentionality * 15) + (deep_ratio * 10) + (trend * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._events:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._events) / len(self._events), 2)
            self._stats["avg_return"] = round(sum(e.return_value for e in self._events) / len(self._events), 2)
            
            fragmented = sum(1 for e in self._events if e.fragmented)
            self._stats["fragmentation_rate"] = round(fragmented / len(self._events), 2)

            by_hijacker = defaultdict(int)
            for e in self._events:
                if e.hijacker:
                    by_hijacker[e.hijacker] += 1
            if by_hijacker:
                self._stats["top_hijacker"] = max(by_hijacker.items(), key=lambda x: x[1])[0]

            recent = [e for e in self._events if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
            if recent:
                recent_frag = sum(1 for e in recent if e.fragmented) / len(recent)
                recent_low = sum(1 for e in recent if e.return_value < 0.3) / len(recent)
                self._stats["attention_debt"] = recent_frag > 0.5 or recent_low > 0.5

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

    def _log_event(self, event: AttentionEvent):
        try:
            with open(ATTENTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": event.timestamp,
                    "investment": event.investment,
                    "category": event.category,
                    "depth": event.depth,
                    "return": event.return_value,
                    "fragmented": event.fragmented,
                    "hijacker": event.hijacker,
                    "intentionality": event.intentionality,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ag_instance: Optional[AttentionGuardian] = None
_ag_lock = threading.Lock()


def get_attention_guardian() -> AttentionGuardian:
    global _ag_instance
    with _ag_lock:
        if _ag_instance is None:
            _ag_instance = AttentionGuardian()
        return _ag_instance
