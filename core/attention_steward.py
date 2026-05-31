"""
LOVE Attention Steward — Focus Intelligence (Modern AI Pattern)

Most people give their attention away without intention. This steward:

1. ATTENTION TRACKING
   - Record attention allocations and their characteristics
   - Track attention types (deep, shallow, reactive, intentional, passive)
   - Log quality, satisfaction, and return from attention investments

2. PATTERN ANALYSIS
   - Identify the user's attention profile (intentional, scattered, reactive, absorbed)
   - Find attention patterns that create value vs waste
   - Detect attention fragmentation and its costs

3. ATTENTION OPTIMIZATION
   - Suggest attention practices matched to current goals and energy
   - Provide frameworks for deep work and intentional focus
   - Recommend attention recovery after fragmentation

4. PRESENCE CULTIVATION
   - Track the correlation between attention quality and life satisfaction
   - Alert when attention is being chronically stolen
   - Celebrate moments of genuine focus and flow

Architecture:
- record_attention(activity, type, quality, satisfaction, return): Log attention
- get_attention_stats(): Get attention pattern analysis
- get_attention_suggestion(capacity, context): Get suggestion
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

DATA_DIR = Path(__file__).parent.parent / "data" / "attention_steward"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ATTENTION_LOG = DATA_DIR / "attention.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AttentionEntry:
    """A tracked attention allocation."""
    entry_id: str = ""
    activity: str = ""  # what received attention
    attention_type: str = ""  # deep, shallow, reactive, intentional, passive
    quality: float = 0.5  # 0-1
    satisfaction: float = 0.0  # 0-1
    value_return: float = 0.0  # 0-1
    duration_minutes: float = 0.0
    interruptions: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AttentionSteward:
    """
    Intelligent attention steward with quality detection and presence cultivation.
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
            "avg_quality": 0.0,
            "avg_value_return": 0.0,
            "fragmentation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_attention(self, activity: str = "", attention_type: str = "", quality: float = 0.5, satisfaction: float = 0.0, value_return: float = 0.0, duration_minutes: float = 0.0, interruptions: int = 0, notes: str = "") -> AttentionEntry:
        """Record an attention allocation."""
        entry_id = f"att_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = AttentionEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            attention_type=attention_type or "shallow",
            quality=quality,
            satisfaction=satisfaction,
            value_return=value_return,
            duration_minutes=duration_minutes,
            interruptions=interruptions,
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

    def get_attention_stats(self) -> Dict[str, Any]:
        """Get attention pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "satisfaction_sum": 0.0, "return_sum": 0.0})
        for e in self._entries:
            by_type[e.attention_type]["count"] += 1
            by_type[e.attention_type]["quality_sum"] += e.quality
            by_type[e.attention_type]["satisfaction_sum"] += e.satisfaction
            by_type[e.attention_type]["return_sum"] += e.value_return

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
                "avg_value_return": round(data["return_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_value_return"]) if type_stats else ("", {})

        # Quality analysis
        high_qual = [e for e in self._entries if e.quality > 0.7]
        low_qual = [e for e in self._entries if e.quality < 0.4]
        if high_qual and low_qual:
            high_qual_sat = sum(e.satisfaction for e in high_qual) / len(high_qual)
            low_qual_sat = sum(e.satisfaction for e in low_qual) / len(low_qual)
            high_qual_ret = sum(e.value_return for e in high_qual) / len(high_qual)
            low_qual_ret = sum(e.value_return for e in low_qual) / len(low_qual)
        else:
            high_qual_sat = 0
            low_qual_sat = 0
            high_qual_ret = 0
            low_qual_ret = 0

        # Interruption analysis
        low_int = [e for e in self._entries if e.interruptions < 2]
        high_int = [e for e in self._entries if e.interruptions > 5]
        if low_int and high_int:
            low_int_qual = sum(e.quality for e in low_int) / len(low_int)
            high_int_qual = sum(e.quality for e in high_int) / len(high_int)
        else:
            low_int_qual = 0
            high_int_qual = 0

        # Fragmentation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_qual = sum(e.quality for e in recent) / len(recent)
            recent_int = sum(e.interruptions for e in recent) / len(recent)
            fragmentation_risk = recent_qual < 0.4 and recent_int > 5
        else:
            fragmentation_risk = False

        return {
            "total_entries": len(self._entries),
            "total_hours": round(sum(e.duration_minutes for e in self._entries) / 60, 1),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "quality_impact": {
                "high_quality_satisfaction": round(high_qual_sat, 2),
                "low_quality_satisfaction": round(low_qual_sat, 2),
                "high_quality_return": round(high_qual_ret, 2),
                "low_quality_return": round(low_qual_ret, 2),
            },
            "interruption_effect": {
                "low_interruption_quality": round(low_int_qual, 2),
                "high_interruption_quality": round(high_int_qual, 2),
            },
            "fragmentation_risk": fragmentation_risk,
            "avg_quality": round(sum(e.quality for e in self._entries) / len(self._entries), 2),
            "avg_value_return": round(sum(e.value_return for e in self._entries) / len(self._entries), 2),
        }

    def get_attention_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get attention suggestion."""
        suggestions = [
            "Single-task. Not multi-task. The research is clear: multi-tasking is a lie. You're not doing multiple things. You're rapidly switching, doing all of them poorly. Pick one thing. Do it fully. Then the next.",
            "Turn off notifications. All of them. Email. Messages. Social media. They are attention thieves. And they steal from the most important thing: your focused mind.",
            "Create attention rules. No phone during meals. No email before 10am. No screens after 9pm. Rules protect your attention from your own impulses.",
            "The attention you give is the life you live. If you give your attention to trivial things, you live a trivial life. If you give it to what matters, you live a life that matters. Choose.",
            "Do deep work. Block time. Shut the door. Turn off the internet if you have to. The ability to focus deeply is becoming a superpower. Cultivate it.",
            "Notice when your attention is being stolen. By anxiety. By rumination. By distraction. The first step to reclaiming attention is noticing it's gone.",
            "Your attention is finite. Treat it like money. You wouldn't throw money away randomly. Don't throw attention away either. Invest it where it returns value.",
            "Practice attention recovery. When you notice you've been distracted, don't judge. Just return. To the breath. To the task. To the conversation. Return is the practice.",
            "Attention is love. Where you put your attention is where you put your love. Your children. Your partner. Your work. Yourself. Attention is the purest expression of care.",
            "The world is designed to steal your attention. Every app. Every notification. Every headline. Every ad. They all want your attention. And they're getting it. Reclaim it. It's yours."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Five minutes of single focus. One distraction turned off. One deep breath of attention. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A focused session. A notification-free hour. A deep conversation. Medium attention investment."
        else:
            capacity_note = "Good capacity. A deep work block. A full digital sabbath. A complete attention reset. You have the energy to reclaim real focus."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Attention is the most valuable resource you have. More valuable than time. More valuable than money. Because attention is what turns time into experience. What turns money into meaning. What turns relationships into connection. And yet we give it away for free. To notifications. To headlines. to strangers on the internet. To worries about things we can't control. The person who controls their attention controls their life. The person who doesn't is controlled by whoever wants their attention. Reclaim it. Protect it. Invest it wisely. Your attention is your life. Spend it well."
        }

    def get_attention_score(self) -> int:
        """Calculate overall attention health (0-100)."""
        if not self._entries:
            return 25

        avg_quality = sum(e.quality for e in self._entries) / len(self._entries)
        avg_satisfaction = sum(e.satisfaction for e in self._entries) / len(self._entries)
        avg_return = sum(e.value_return for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_quality = sum(e.quality for e in recent) / len(recent)
            recent_return = sum(e.value_return for e in recent) / len(recent)
        else:
            recent_quality = 0
            recent_return = 0

        # Fragmentation penalty
        frag_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_qual_30 = sum(e.quality for e in last_30) / len(last_30)
            recent_int_30 = sum(e.interruptions for e in last_30) / len(last_30)
            if recent_qual_30 < 0.4 and recent_int_30 > 5:
                frag_penalty = 15

        # Type variety
        unique_types = len(set(e.attention_type for e in self._entries))

        # Interruption penalty
        avg_interruptions = sum(e.interruptions for e in self._entries) / len(self._entries)
        interrupt_penalty = min(15, avg_interruptions * 2)

        score = (avg_quality * 30) + (avg_satisfaction * 15) + (avg_return * 25) + (recent_quality * 10) + (recent_return * 10) + (unique_types * 2) - frag_penalty - interrupt_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_quality"] = round(sum(e.quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_value_return"] = round(sum(e.value_return for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_qual = sum(e.quality for e in recent) / len(recent)
                recent_int = sum(e.interruptions for e in recent) / len(recent)
                self._stats["fragmentation_risk"] = recent_qual < 0.4 and recent_int > 5
            else:
                self._stats["fragmentation_risk"] = False

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

    def _log_entry(self, entry: AttentionEntry):
        try:
            with open(ATTENTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "attention_type": entry.attention_type,
                    "quality": entry.quality,
                    "interruptions": entry.interruptions,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_as_instance: Optional[AttentionSteward] = None
_as_lock = threading.Lock()


def get_attention_steward() -> AttentionSteward:
    global _as_instance
    with _as_lock:
        if _as_instance is None:
            _as_instance = AttentionSteward()
        return _as_instance
