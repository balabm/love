"""
LOVE Publishing Navigator — Publishing Intelligence (Modern AI Pattern)

Most people write but never publish. This navigator:

1. PUBLISHING TRACKING
   - Record publishing moments and their characteristics
   - Track publishing types (draft, edit, submit, publish, promote, reflect)
   - Log readiness, clarity, courage, strategy, and impact of publishing

2. PATTERN ANALYSIS
   - Identify the user's publishing profile (hoarder, hesitant, developing, prolific)
   - Find publishing patterns that create reach vs obscurity
   - Detect chronic perfectionism and its costs

3. PUBLISHING BUILDING
   - Suggest practices for overcoming publishing fear
   - Provide frameworks for strategic publishing
   - Recommend practices for building audience and impact

4. PUBLISHING MASTERY CULTIVATION
   - Track the correlation between publishing frequency and growth
   - Alert when hoarding is replacing sharing
   - Celebrate moments of genuine published work

Architecture:
- record_publishing(work, type, readiness, clarity, courage, strategy, impact): Log publishing
- get_publishing_stats(): Get publishing pattern analysis
- get_publishing_suggestion(capacity, context): Get suggestion
- get_publishing_score(): Calculate overall publishing health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "publishing_navigator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PUBLISHING_LOG = DATA_DIR / "publishings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PublishingEntry:
    """A tracked publishing moment."""
    entry_id: str = ""
    work: str = ""  # what was the work
    publishing_type: str = ""  # draft, edit, submit, publish, promote, reflect
    readiness: float = 0.0  # 0-1
    clarity: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    strategy: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    audience: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PublishingNavigator:
    """
    Intelligent publishing navigator with perfectionism detection and publishing mastery cultivation.
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
            "avg_readiness": 0.0,
            "avg_courage": 0.0,
            "perfectionism_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_publishing(self, work: str = "", publishing_type: str = "", readiness: float = 0.0, clarity: float = 0.0, courage: float = 0.0, strategy: float = 0.0, impact: float = 0.0, audience: float = 0.0, notes: str = "") -> PublishingEntry:
        """Record a publishing moment."""
        entry_id = f"pub_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PublishingEntry(
            entry_id=entry_id,
            work=work or "unspecified",
            publishing_type=publishing_type or "draft",
            readiness=readiness,
            clarity=clarity,
            courage=courage,
            strategy=strategy,
            impact=impact,
            audience=audience,
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

    def get_publishing_stats(self) -> Dict[str, Any]:
        """Get publishing pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "readiness_sum": 0.0, "courage_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            by_type[e.publishing_type]["count"] += 1
            by_type[e.publishing_type]["readiness_sum"] += e.readiness
            by_type[e.publishing_type]["courage_sum"] += e.courage
            by_type[e.publishing_type]["impact_sum"] += e.impact

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_readiness": round(data["readiness_sum"] / count, 2),
                "avg_courage": round(data["courage_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Readiness analysis
        high_ready = [e for e in self._entries if e.readiness > 0.7]
        low_ready = [e for e in self._entries if e.readiness < 0.4]
        if high_ready and low_ready:
            high_ready_imp = sum(e.impact for e in high_ready) / len(high_ready)
            low_ready_imp = sum(e.impact for e in low_ready) / len(low_ready)
            high_ready_aud = sum(e.audience for e in high_ready) / len(high_ready)
            low_ready_aud = sum(e.audience for e in low_ready) / len(low_ready)
        else:
            high_ready_imp = 0
            low_ready_imp = 0
            high_ready_aud = 0
            low_ready_aud = 0

        # Courage analysis
        high_cour = [e for e in self._entries if e.courage > 0.7]
        low_cour = [e for e in self._entries if e.courage < 0.4]
        if high_cour and low_cour:
            high_cour_imp = sum(e.impact for e in high_cour) / len(high_cour)
            low_cour_imp = sum(e.impact for e in low_cour) / len(low_cour)
        else:
            high_cour_imp = 0
            low_cour_imp = 0

        # Perfectionism risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_ready = sum(e.readiness for e in recent) / len(recent)
            recent_cour = sum(e.courage for e in recent) / len(recent)
            perfectionism_risk = recent_ready > 0.8 and recent_cour < 0.3
        else:
            perfectionism_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "readiness_impact": {
                "high_readiness_impact": round(high_ready_imp, 2),
                "low_readiness_impact": round(low_ready_imp, 2),
                "high_readiness_audience": round(high_ready_aud, 2),
                "low_readiness_audience": round(low_ready_aud, 2),
            },
            "courage_effect": {
                "high_courage_impact": round(high_cour_imp, 2),
                "low_courage_impact": round(low_cour_imp, 2),
            },
            "perfectionism_risk": perfectionism_risk,
            "avg_readiness": round(sum(e.readiness for e in self._entries) / len(self._entries), 2),
            "avg_courage": round(sum(e.courage for e in self._entries) / len(self._entries), 2),
        }

    def get_publishing_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get publishing suggestion."""
        suggestions = [
            "Most people write but never publish. They have drafts. They have ideas. They have finished pieces sitting in folders. And they wonder why nobody reads their work. Why they have no audience. Why they feel invisible. The answer is simple: they're not publishing.",
            "Perfect is the enemy of published. Your draft will never be perfect. It will never be ready. It will never be good enough. Publish it anyway. The person who publishes imperfect work reaches people. The person who waits for perfect work reaches no one.",
            "Start small. A tweet. A post. A comment. A short article. Not a book. Not a manifesto. Small pieces. Published frequently. Small is not less valuable. Small is accessible. Small builds momentum. Small leads to big.",
            "Publish before you're ready. Before you feel ready. Before you think it's good enough. The courage to publish is more important than the quality of the first piece. Because the first piece is just the beginning. And you can't have a second piece without a first.",
            "Find your platform. Not every platform. The one that fits your work. Your audience. Your style. Your goals. A blog. A newsletter. Medium. Substack. LinkedIn. Twitter. You don't need to be everywhere. You need to be somewhere. Consistently.",
            "Build in public. Share your process. Your drafts. Your failures. Your learnings. Your behind-the-scenes. People don't just want the finished product. They want the journey. They want to see how it's made. Build in public and you build an audience.",
            "Ignore the metrics. At first. Don't check views. Don't check likes. Don't check shares. Just publish. Focus on the work. The metrics will come. But not if you're chasing them. Chase the work. The metrics chase you.",
            "Embrace negative feedback. It's not an attack. It's information. Some of it is wrong. Some of it is right. All of it is useful. The person who fears feedback fears growth. The person who welcomes feedback grows faster.",
            "Publish on a schedule. Not when you feel like it. Weekly. Biweekly. Monthly. The schedule creates pressure. Pressure creates productivity. Productivity creates practice. Practice creates mastery. The schedule is the engine.",
            "The person who publishes regularly is not a special person. They're a person who made a decision. A decision to share. To be seen. To be vulnerable. To contribute. And that decision is available to everyone. Including you. Right now. Today."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One tweet. One post. One short piece. One share. One small publication. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A weekly publication. A found platform. A small audience. A schedule kept. Medium reach."
        else:
            capacity_note = "Good capacity. Deep publishing work. A systematic practice of regular creation, strategic sharing, and audience building. You have the strength to be widely read."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Publishing navigation is not about becoming famous. It's about being read. Most people create work and hide it. They write but don't publish. They create but don't share. They have ideas but don't express them publicly. And they wonder why they have no impact. Why they have no audience. Why they feel invisible. The work of publishing navigation is about understanding that publishing is a skill. That it requires courage. That it requires strategy. That it requires consistency. And that the person who publishes regularly - however imperfectly - is the person who eventually builds an audience, has an impact, and makes a difference."
        }

    def get_publishing_score(self) -> int:
        """Calculate overall publishing health (0-100)."""
        if not self._entries:
            return 25

        avg_ready = sum(e.readiness for e in self._entries) / len(self._entries)
        avg_clar = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_cour = sum(e.courage for e in self._entries) / len(self._entries)
        avg_strat = sum(e.strategy for e in self._entries) / len(self._entries)
        avg_imp = sum(e.impact for e in self._entries) / len(self._entries)
        avg_aud = sum(e.audience for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cour = sum(e.courage for e in recent) / len(recent)
            recent_imp = sum(e.impact for e in recent) / len(recent)
        else:
            recent_cour = 0
            recent_imp = 0

        # Perfectionism penalty
        perf_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_ready_30 = sum(e.readiness for e in last_30) / len(last_30)
            recent_cour_30 = sum(e.courage for e in last_30) / len(last_30)
            if recent_ready_30 > 0.8 and recent_cour_30 < 0.3:
                perf_penalty = 15

        # Type variety
        unique_types = len(set(e.publishing_type for e in self._entries))

        score = (avg_ready * 15) + (avg_clar * 10) + (avg_cour * 25) + (avg_strat * 15) + (avg_imp * 15) + (avg_aud * 10) + (recent_cour * 5) + (recent_imp * 5) + (unique_types * 2) - perf_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_readiness"] = round(sum(e.readiness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_courage"] = round(sum(e.courage for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_ready = sum(e.readiness for e in recent) / len(recent)
                recent_cour = sum(e.courage for e in recent) / len(recent)
                self._stats["perfectionism_risk"] = recent_ready > 0.8 and recent_cour < 0.3
            else:
                self._stats["perfectionism_risk"] = False

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

    def _log_entry(self, entry: PublishingEntry):
        try:
            with open(PUBLISHING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "work": entry.work,
                    "publishing_type": entry.publishing_type,
                    "readiness": entry.readiness,
                    "courage": entry.courage,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pn_instance: Optional[PublishingNavigator] = None
_pn_lock = threading.Lock()


def get_publishing_navigator() -> PublishingNavigator:
    global _pn_instance
    with _pn_lock:
        if _pn_instance is None:
            _pn_instance = PublishingNavigator()
        return _pn_instance
