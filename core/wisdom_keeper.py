"""
LOVE Wisdom Keeper — Sage Intelligence (Modern AI Pattern)

Most people accumulate experience but not wisdom. This keeper:

1. WISDOM TRACKING
   - Record insights and their characteristics
   - Track insight types (philosophical, practical, relational, spiritual, ethical)
   - Log depth, applicability, and integration of insights

2. PATTERN ANALYSIS
   - Identify the user's wisdom profile (reflective, reactive, integrated, scattered)
   - Find patterns that turn experience into wisdom
   - Detect insight accumulation without integration

3. WISDOM OPTIMIZATION
   - Suggest practices for deepening and integrating insights
   - Provide frameworks for ethical decision-making
   - Recommend reflection and contemplation practices

4. INTEGRATION CULTIVATION
   - Track the correlation between reflection and life quality
   - Alert when insights are being collected but not lived
   - Celebrate moments of genuine wisdom-in-action

Architecture:
- record_insight(insight, type, depth, applicability, integration): Log insight
- get_wisdom_stats(): Get wisdom pattern analysis
- get_wisdom_suggestion(capacity, context): Get suggestion
- get_wisdom_score(): Calculate overall wisdom health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "wisdom_keeper"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WISDOM_LOG = DATA_DIR / "insights.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WisdomEntry:
    """A tracked wisdom insight."""
    entry_id: str = ""
    insight: str = ""  # the insight
    insight_type: str = ""  # philosophical, practical, relational, spiritual, ethical
    depth: float = 0.0  # 0-1
    applicability: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1 how well it's lived
    source: str = ""  # what led to the insight
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class WisdomKeeper:
    """
    Intelligent wisdom keeper with depth detection and integration cultivation.
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
            "avg_integration": 0.0,
            "hoarding_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_insight(self, insight: str = "", insight_type: str = "", depth: float = 0.0, applicability: float = 0.0, integration: float = 0.0, source: str = "", notes: str = "") -> WisdomEntry:
        """Record a wisdom insight."""
        entry_id = f"wis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = WisdomEntry(
            entry_id=entry_id,
            insight=insight or "unspecified",
            insight_type=insight_type or "practical",
            depth=depth,
            applicability=applicability,
            integration=integration,
            source=source or "reflection",
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

    def get_wisdom_stats(self) -> Dict[str, Any]:
        """Get wisdom pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "applicability_sum": 0.0, "integration_sum": 0.0})
        for e in self._entries:
            by_type[e.insight_type]["count"] += 1
            by_type[e.insight_type]["depth_sum"] += e.depth
            by_type[e.insight_type]["applicability_sum"] += e.applicability
            by_type[e.insight_type]["integration_sum"] += e.integration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_applicability": round(data["applicability_sum"] / count, 2),
                "avg_integration": round(data["integration_sum"] / count, 2),
            }

        # Depth analysis
        high_depth = [e for e in self._entries if e.depth > 0.7]
        low_depth = [e for e in self._entries if e.depth < 0.4]
        if high_depth and low_depth:
            high_depth_int = sum(e.integration for e in high_depth) / len(high_depth)
            low_depth_int = sum(e.integration for e in low_depth) / len(low_depth)
        else:
            high_depth_int = 0
            low_depth_int = 0

        # Integration analysis
        high_int = [e for e in self._entries if e.integration > 0.7]
        low_int = [e for e in self._entries if e.integration < 0.4]
        if high_int and low_int:
            high_int_appl = sum(e.applicability for e in high_int) / len(high_int)
            low_int_appl = sum(e.applicability for e in low_int) / len(low_int)
        else:
            high_int_appl = 0
            low_int_appl = 0

        # Hoarding risk detection
        high_insight_count = sum(1 for e in self._entries if e.depth > 0.6)
        low_integration_count = sum(1 for e in self._entries if e.integration < 0.3)
        if high_insight_count > 10 and low_integration_count > 10:
            hoarding_risk = True
        else:
            hoarding_risk = False

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "depth_sum": 0.0})
        for e in self._entries:
            by_source[e.source]["count"] += 1
            by_source[e.source]["depth_sum"] += e.depth

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
            }

        best_source = max(source_stats.items(), key=lambda x: x[1]["avg_depth"]) if source_stats else ("", {})

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "depth_impact": {
                "high_depth_integration": round(high_depth_int, 2),
                "low_depth_integration": round(low_depth_int, 2),
            },
            "integration_effect": {
                "high_integration_applicability": round(high_int_appl, 2),
                "low_integration_applicability": round(low_int_appl, 2),
            },
            "hoarding_risk": hoarding_risk,
            "source_stats": source_stats,
            "best_source": best_source[0],
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
        }

    def get_wisdom_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get wisdom suggestion."""
        suggestions = [
            "Wisdom is not knowledge. It's knowledge lived. You can read a thousand books. But if you don't apply what you learn, you haven't gained wisdom. You've gained trivia. Apply one insight today.",
            "Reflect on your day. Not in judgment. In curiosity. What happened? How did you respond? What would you do differently? The unexamined life is not worth living. The examined life is.",
            "Teach what you've learned. The best way to integrate wisdom is to transmit it. When you have to explain it, you understand it. When you have to model it, you live it.",
            "Seek the paradox. The wisest insights live in contradiction. Strength through vulnerability. Power through service. Life through death. Hold the tension. Don't resolve it too quickly.",
            "Your greatest failures are your greatest teachers. Not your successes. Success teaches repetition. Failure teaches transformation. Look back at your hardest moments. What did they teach you?",
            "Wisdom is slow. It takes time. You can't rush it. Be patient with your own development. The person who wants to be wise already is. The desire is the beginning.",
            "Listen to those who disagree with you. Not to argue. To understand. Wisdom requires the ability to hold multiple perspectives simultaneously. Not to choose one. To hold them all.",
            "Practice ethical clarity. In every decision, ask: Is this right? Not is this profitable. Not is it easy. Is it right? The wise person acts from principle, not convenience.",
            "Wisdom is contextual. What worked yesterday may not work today. What works here may not work there. Be flexible. Be humble. Be willing to revise.",
            "The wisest people know how little they know. Socrates was the wisest because he knew he knew nothing. Cultivate beginner's mind. Even in your expertise. There's always more to learn.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One reflection. One insight. One application. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A journal entry. A teaching conversation. A challenging read. Medium depth."
        else:
            capacity_note = "Good capacity. Deep contemplation. Complex ethical exploration. A major life principle to integrate. You have the energy for real wisdom work."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Wisdom is the integration of knowledge, experience, and reflection into a coherent way of being. It's not about being right. It's about being whole. The wise person doesn't have all the answers. They have the right questions. They don't avoid difficulty. They learn from it. They don't seek certainty. They seek truth. Wisdom is not the accumulation of insights. It's the transformation of the self. The person who has read everything but changed nothing is not wise. The person who has learned one thing and lived it is. Wisdom is not a destination. It's a direction. Keep walking.",
        }

    def get_wisdom_score(self) -> int:
        """Calculate overall wisdom health (0-100)."""
        if not self._entries:
            return 25

        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_applicability = sum(e.applicability for e in self._entries) / len(self._entries)
        avg_integration = sum(e.integration for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_integration = sum(e.integration for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_integration = 0

        # Hoarding penalty
        hoarding_penalty = 0
        high_insight_count = sum(1 for e in self._entries if e.depth > 0.6)
        low_integration_count = sum(1 for e in self._entries if e.integration < 0.3)
        if high_insight_count > 10 and low_integration_count > 10:
            hoarding_penalty = 15

        # Type variety
        unique_types = len(set(e.insight_type for e in self._entries))

        score = (avg_depth * 30) + (avg_applicability * 20) + (avg_integration * 30) + (recent_depth * 10) + (recent_integration * 10) + (unique_types * 2) - hoarding_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integration"] = round(sum(e.integration for e in self._entries) / len(self._entries), 2)

            high_insight_count = sum(1 for e in self._entries if e.depth > 0.6)
            low_integration_count = sum(1 for e in self._entries if e.integration < 0.3)
            self._stats["hoarding_risk"] = high_insight_count > 10 and low_integration_count > 10

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

    def _log_entry(self, entry: WisdomEntry):
        try:
            with open(WISDOM_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "insight": entry.insight,
                    "insight_type": entry.insight_type,
                    "depth": entry.depth,
                    "integration": entry.integration,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wk_instance: Optional[WisdomKeeper] = None
_wk_lock = threading.Lock()


def get_wisdom_keeper() -> WisdomKeeper:
    global _wk_instance
    with _wk_lock:
        if _wk_instance is None:
            _wk_instance = WisdomKeeper()
        return _wk_instance
