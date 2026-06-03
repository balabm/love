"""
LOVE Newsletter Creator — Newsletter Intelligence (Modern AI Pattern)

Most people want a newsletter but don't create one. This creator:

1. NEWSLETTER TRACKING
   - Record newsletter moments and their characteristics
   - Track newsletter types (idea, draft, edit, send, analyze, iterate)
   - Log clarity, value, voice, consistency, and engagement of newsletters

2. PATTERN ANALYSIS
   - Identify the user's newsletter profile (aspiring, sporadic, developing, masterful)
   - Find newsletter patterns that create subscribers vs unsubscribes
   - Detect chronic inconsistency and its costs

3. CREATION BUILDING
   - Suggest practices for building newsletter habit
   - Provide frameworks for valuable newsletter content
   - Recommend practices for growing subscriber base

4. NEWSLETTER MASTERY CULTIVATION
   - Track the correlation between consistency and subscriber growth
   - Alert when silence is replacing sending
   - Celebrate moments of genuine newsletter impact

Architecture:
- record_newsletter(issue, type, clarity, value, voice, consistency, engagement): Log newsletter
- get_newsletter_stats(): Get newsletter pattern analysis
- get_newsletter_suggestion(capacity, context): Get suggestion
- get_newsletter_score(): Calculate overall newsletter health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "newsletter_creator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NEWSLETTER_LOG = DATA_DIR / "newsletters.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class NewsletterEntry:
    """A tracked newsletter moment."""
    entry_id: str = ""
    issue: str = ""  # what was the issue
    newsletter_type: str = ""  # idea, draft, edit, send, analyze, iterate
    clarity: float = 0.0  # 0-1
    value: float = 0.0  # 0-1
    voice: float = 0.0  # 0-1
    consistency: float = 0.0  # 0-1
    engagement: float = 0.0  # 0-1
    growth: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class NewsletterCreator:
    """
    Intelligent newsletter creator with inconsistency detection and newsletter mastery cultivation.
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
            "avg_clarity": 0.0,
            "avg_engagement": 0.0,
            "inconsistency_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_newsletter(self, issue: str = "", newsletter_type: str = "", clarity: float = 0.0, value: float = 0.0, voice: float = 0.0, consistency: float = 0.0, engagement: float = 0.0, growth: float = 0.0, notes: str = "") -> NewsletterEntry:
        """Record a newsletter moment."""
        entry_id = f"nws_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = NewsletterEntry(
            entry_id=entry_id,
            issue=issue or "unspecified",
            newsletter_type=newsletter_type or "draft",
            clarity=clarity,
            value=value,
            voice=voice,
            consistency=consistency,
            engagement=engagement,
            growth=growth,
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

    def get_newsletter_stats(self) -> Dict[str, Any]:
        """Get newsletter pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "value_sum": 0.0, "engagement_sum": 0.0})
        for e in self._entries:
            by_type[e.newsletter_type]["count"] += 1
            by_type[e.newsletter_type]["clarity_sum"] += e.clarity
            by_type[e.newsletter_type]["value_sum"] += e.value
            by_type[e.newsletter_type]["engagement_sum"] += e.engagement

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_value": round(data["value_sum"] / count, 2),
                "avg_engagement": round(data["engagement_sum"] / count, 2),
            }

        # Clarity analysis
        high_clar = [e for e in self._entries if e.clarity > 0.7]
        low_clar = [e for e in self._entries if e.clarity < 0.4]
        if high_clar and low_clar:
            high_clar_eng = sum(e.engagement for e in high_clar) / len(high_clar)
            low_clar_eng = sum(e.engagement for e in low_clar) / len(low_clar)
            high_clar_val = sum(e.value for e in high_clar) / len(high_clar)
            low_clar_val = sum(e.value for e in low_clar) / len(low_clar)
        else:
            high_clar_eng = 0
            low_clar_eng = 0
            high_clar_val = 0
            low_clar_val = 0

        # Value analysis
        high_val = [e for e in self._entries if e.value > 0.7]
        low_val = [e for e in self._entries if e.value < 0.4]
        if high_val and low_val:
            high_val_eng = sum(e.engagement for e in high_val) / len(high_val)
            low_val_eng = sum(e.engagement for e in low_val) / len(low_val)
        else:
            high_val_eng = 0
            low_val_eng = 0

        # Inconsistency risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            recent_eng = sum(e.engagement for e in recent) / len(recent)
            inconsistency_risk = recent_cons < 0.3 and recent_eng < 0.3
        else:
            inconsistency_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "clarity_impact": {
                "high_clarity_engagement": round(high_clar_eng, 2),
                "low_clarity_engagement": round(low_clar_eng, 2),
                "high_clarity_value": round(high_clar_val, 2),
                "low_clarity_value": round(low_clar_val, 2),
            },
            "value_effect": {
                "high_value_engagement": round(high_val_eng, 2),
                "low_value_engagement": round(low_val_eng, 2),
            },
            "inconsistency_risk": inconsistency_risk,
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
            "avg_engagement": round(sum(e.engagement for e in self._entries) / len(self._entries), 2),
        }

    def get_newsletter_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get newsletter suggestion."""
        suggestions = [
            "Most people want a newsletter but don't create one. They have ideas. They have expertise. They have stories. And they sit down to write the first issue and feel overwhelmed. What should I write about? Who would read it? What if nobody cares? And they never send the first issue. The newsletter dies in their head.",
            "Start with one subscriber. You. Send the first issue to yourself. Read it. Does it provide value? Does it sound like you? Does it make you want to read the next one? If yes, send it to one friend. Then two. Then ten. Growth is gradual. But it starts with one.",
            "Write what you wish existed. The newsletter you would subscribe to. The content you would read. The voice you would trust. Don't guess what others want. Write what you want. Your ideal subscriber is someone like you. And there are more of them than you think.",
            "Keep it short. Not shallow. Short. One idea. One story. One lesson. One insight. The newsletter that respects the reader's time is the newsletter that gets read. The newsletter that demands thirty minutes is the newsletter that gets deleted.",
            "Be consistent. Not prolific. Weekly. Biweekly. Monthly. The schedule matters more than the frequency. The reader who knows when to expect your newsletter trusts you. The reader who doesn't know when to expect it forgets you. Consistency is the craft.",
            "Sign off like a person. Not a brand. Use your name. Share a thought. Ask a question. Invite a reply. The newsletter is a conversation. Not a broadcast. The person who writes like a person builds a relationship. The person who writes like a brand builds a wall.",
            "One call to action. Not five. Not three. One. What do you want the reader to do? Reply? Share? Click? Read something? Do one thing. One clear action. The reader who knows what to do does it. The reader who doesn't know does nothing.",
            "Share your process. Not just your results. The draft. The revision. The doubt. The breakthrough. The behind-the-scenes. People subscribe to newsletters for personality. For humanity. For the journey. Not just the destination.",
            "Study your data. Not obsessively. Curiously. What got opened? What got clicked? What got replies? What got unsubscribes? Data is feedback. Not judgment. Use it to improve. Not to panic.",
            "The person who creates a newsletter is not a special person. They're a person who made a decision. A decision to share. To be consistent. To provide value. To build a relationship. One issue at a time. One subscriber at a time. One week at a time. And that decision is available to everyone. Including you."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One issue. One subscriber. One short piece. One consistent schedule. One personal sign-off. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A weekly issue. A growing list. A clear value. A personal voice. A studied metric. Medium mastery."
        else:
            capacity_note = "Good capacity. Deep newsletter work. A systematic practice of consistent creation, clear value, personal voice, and genuine engagement. You have the strength to build a world-class newsletter."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Newsletter creation coaching is not about becoming a famous writer. It's about becoming a consistent one. Most people want a newsletter but never create one. They have ideas, expertise, and stories that never reach an audience. They get overwhelmed by the first issue. They worry about subscribers, metrics, and perfection. And they never send. The work of newsletter creation coaching is about understanding that a newsletter is a relationship. That it requires consistency. That it requires value. That it requires a personal voice. And that the person who commits to regular creation - however small - is the person who eventually builds a loyal audience and makes a genuine impact."
        }

    def get_newsletter_score(self) -> int:
        """Calculate overall newsletter health (0-100)."""
        if not self._entries:
            return 25

        avg_clar = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_val = sum(e.value for e in self._entries) / len(self._entries)
        avg_voi = sum(e.voice for e in self._entries) / len(self._entries)
        avg_cons = sum(e.consistency for e in self._entries) / len(self._entries)
        avg_eng = sum(e.engagement for e in self._entries) / len(self._entries)
        avg_growth = sum(e.growth for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            recent_eng = sum(e.engagement for e in recent) / len(recent)
        else:
            recent_cons = 0
            recent_eng = 0

        # Inconsistency penalty
        inc_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cons_30 = sum(e.consistency for e in last_30) / len(last_30)
            recent_eng_30 = sum(e.engagement for e in last_30) / len(last_30)
            if recent_cons_30 < 0.3 and recent_eng_30 < 0.3:
                inc_penalty = 15

        # Type variety
        unique_types = len(set(e.newsletter_type for e in self._entries))

        score = (avg_clar * 20) + (avg_val * 20) + (avg_voi * 10) + (avg_cons * 20) + (avg_eng * 15) + (avg_growth * 10) + (recent_cons * 5) + (recent_eng * 5) + (unique_types * 2) - inc_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_engagement"] = round(sum(e.engagement for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cons = sum(e.consistency for e in recent) / len(recent)
                recent_eng = sum(e.engagement for e in recent) / len(recent)
                self._stats["inconsistency_risk"] = recent_cons < 0.3 and recent_eng < 0.3
            else:
                self._stats["inconsistency_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.newsletter_creator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.newsletter_creator")

    def _log_entry(self, entry: NewsletterEntry):
        try:
            with open(NEWSLETTER_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "issue": entry.issue,
                    "newsletter_type": entry.newsletter_type,
                    "clarity": entry.clarity,
                    "engagement": entry.engagement,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.newsletter_creator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_nc_instance: Optional[NewsletterCreator] = None
_nc_lock = threading.Lock()


def get_newsletter_creator() -> NewsletterCreator:
    global _nc_instance
    with _nc_lock:
        if _nc_instance is None:
            _nc_instance = NewsletterCreator()
        return _nc_instance
