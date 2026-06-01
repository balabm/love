"""
LOVE Blog Craft Coach — Blogging Intelligence (Modern AI Pattern)

Most people blog without craft. This coach:

1. BLOG TRACKING
   - Record blog moments and their characteristics
   - Track blog types (idea, draft, edit, publish, promote, engage)
   - Log clarity, voice, structure, value, and resonance of blogging

2. PATTERN ANALYSIS
   - Identify the user's blogging profile (occasional, inconsistent, developing, masterful)
   - Find blogging patterns that create engagement vs silence
   - Detect chronic inconsistency and its costs

3. CRAFT BUILDING
   - Suggest practices for building blogging skill
   - Provide frameworks for compelling blog writing
   - Recommend practices for building readership

4. BLOGGING MASTERY CULTIVATION
   - Track the correlation between consistency and audience growth
   - Alert when sporadic posting is replacing reliable publishing
   - Celebrate moments of genuine blog breakthrough

Architecture:
- record_blog(post, type, clarity, voice, structure, value, resonance): Log blog
- get_blog_stats(): Get blog pattern analysis
- get_blog_suggestion(capacity, context): Get suggestion
- get_blog_score(): Calculate overall blog health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "blog_craft_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BLOG_LOG = DATA_DIR / "blogs.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BlogEntry:
    """A tracked blog moment."""
    entry_id: str = ""
    post: str = ""  # what was the post
    blog_type: str = ""  # idea, draft, edit, publish, promote, engage
    clarity: float = 0.0  # 0-1
    voice: float = 0.0  # 0-1
    structure: float = 0.0  # 0-1
    value: float = 0.0  # 0-1
    resonance: float = 0.0  # 0-1
    consistency: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BlogCraftCoach:
    """
    Intelligent blog craft coach with inconsistency detection and blogging mastery cultivation.
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
            "avg_resonance": 0.0,
            "inconsistency_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_blog(self, post: str = "", blog_type: str = "", clarity: float = 0.0, voice: float = 0.0, structure: float = 0.0, value: float = 0.0, resonance: float = 0.0, consistency: float = 0.0, notes: str = "") -> BlogEntry:
        """Record a blog moment."""
        entry_id = f"blg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BlogEntry(
            entry_id=entry_id,
            post=post or "unspecified",
            blog_type=blog_type or "draft",
            clarity=clarity,
            voice=voice,
            structure=structure,
            value=value,
            resonance=resonance,
            consistency=consistency,
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

    def get_blog_stats(self) -> Dict[str, Any]:
        """Get blog pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "voice_sum": 0.0, "value_sum": 0.0})
        for e in self._entries:
            by_type[e.blog_type]["count"] += 1
            by_type[e.blog_type]["clarity_sum"] += e.clarity
            by_type[e.blog_type]["voice_sum"] += e.voice
            by_type[e.blog_type]["value_sum"] += e.value

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_voice": round(data["voice_sum"] / count, 2),
                "avg_value": round(data["value_sum"] / count, 2),
            }

        # Clarity analysis
        high_clar = [e for e in self._entries if e.clarity > 0.7]
        low_clar = [e for e in self._entries if e.clarity < 0.4]
        if high_clar and low_clar:
            high_clar_res = sum(e.resonance for e in high_clar) / len(high_clar)
            low_clar_res = sum(e.resonance for e in low_clar) / len(low_clar)
            high_clar_val = sum(e.value for e in high_clar) / len(high_clar)
            low_clar_val = sum(e.value for e in low_clar) / len(low_clar)
        else:
            high_clar_res = 0
            low_clar_res = 0
            high_clar_val = 0
            low_clar_val = 0

        # Voice analysis
        high_voi = [e for e in self._entries if e.voice > 0.7]
        low_voi = [e for e in self._entries if e.voice < 0.4]
        if high_voi and low_voi:
            high_voi_res = sum(e.resonance for e in high_voi) / len(high_voi)
            low_voi_res = sum(e.resonance for e in low_voi) / len(low_voi)
        else:
            high_voi_res = 0
            low_voi_res = 0

        # Inconsistency risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            recent_res = sum(e.resonance for e in recent) / len(recent)
            inconsistency_risk = recent_cons < 0.3 and recent_res < 0.3
        else:
            inconsistency_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "clarity_impact": {
                "high_clarity_resonance": round(high_clar_res, 2),
                "low_clarity_resonance": round(low_clar_res, 2),
                "high_clarity_value": round(high_clar_val, 2),
                "low_clarity_value": round(low_clar_val, 2),
            },
            "voice_effect": {
                "high_voice_resonance": round(high_voi_res, 2),
                "low_voice_resonance": round(low_voi_res, 2),
            },
            "inconsistency_risk": inconsistency_risk,
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
            "avg_resonance": round(sum(e.resonance for e in self._entries) / len(self._entries), 2),
        }

    def get_blog_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get blog suggestion."""
        suggestions = [
            "Most people blog without craft. They write when they feel like it. They publish when they have time. They write about whatever comes to mind. And they wonder why nobody reads. Why they have no audience. Why their blog is a ghost town. The answer is simple: they're not crafting. They're not consistent. They're not creating value.",
            "Write one clear idea. Not ten. Not five. One. One idea per post. One argument. One story. One lesson. Clarity is the craft. The reader who understands one thing remembers it. The reader who understands nothing remembers nothing.",
            "Find your voice. Not someone else's. Not the voice you think sounds professional. Your voice. The way you actually talk. The way you actually think. The words you actually use. Authentic voice is magnetic. Manufactured voice is invisible.",
            "Structure for the reader. Not for yourself. Short paragraphs. Subheadings. Bullets. White space. The reader scans. They don't read every word. Structure for the scanner. Make it easy to consume. Easy to digest. Easy to remember.",
            "Create value. Every post. Not sometimes. Every single one. What does the reader get? A new idea. A new skill. A new perspective. A new feeling. Something useful. Something meaningful. Something they didn't have before they read it. Value is the currency of attention.",
            "Write headlines that promise. Not clickbait. Promise. Tell the reader what they'll get. Why they should read. What they'll learn. What they'll feel. A good headline is a contract. It makes a promise. The post delivers it.",
            "Publish on a schedule. Weekly. Biweekly. Monthly. The schedule builds trust. The schedule builds expectation. The schedule builds audience. Sporadic posting builds nothing. Consistency is the craft.",
            "Engage with readers. Reply to comments. Ask questions. Create conversation. The blog is not a broadcast. It's a dialogue. The person who engages builds community. The person who broadcasts builds silence.",
            "Study what works. Not what you like. What gets read. What gets shared. What gets commented on. Learn from it. Not to copy. To understand. Why did it work? What can you adapt? What can you make your own?",
            "The person who crafts their blog is not just a writer. They're a publisher. An editor. A marketer. A community builder. They understand that blogging is not just writing. It's a complete craft. And they commit to mastering it. Every post. Every edit. Every headline. Every engagement. That's the craft."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One clear idea. One authentic voice. One structured post. One piece of value. One headline written. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A weekly schedule. A found voice. A structured format. A value creation practice. An engagement habit. Medium craft."
        else:
            capacity_note = "Good capacity. Deep blog craft work. A systematic practice of clear ideas, authentic voice, strong structure, real value, and consistent publishing. You have the strength to build a world-class blog."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Blog craft coaching is not about becoming a famous blogger. It's about becoming a skilled one. Most people blog without craft. They write when they feel like it. They publish without editing. They write without structure. They create without value. And they wonder why nobody reads. The work of blog craft coaching is about understanding that blogging is a craft. That it requires clarity. Voice. Structure. Value. Consistency. And engagement. And that the person who approaches blogging as a craft - who studies it, practices it, and improves it - is the person who eventually builds an audience, has an impact, and makes a difference through their writing."
        }

    def get_blog_score(self) -> int:
        """Calculate overall blog health (0-100)."""
        if not self._entries:
            return 25

        avg_clar = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_voi = sum(e.voice for e in self._entries) / len(self._entries)
        avg_struc = sum(e.structure for e in self._entries) / len(self._entries)
        avg_val = sum(e.value for e in self._entries) / len(self._entries)
        avg_res = sum(e.resonance for e in self._entries) / len(self._entries)
        avg_cons = sum(e.consistency for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            recent_res = sum(e.resonance for e in recent) / len(recent)
        else:
            recent_cons = 0
            recent_res = 0

        # Inconsistency penalty
        inc_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_cons_30 = sum(e.consistency for e in last_30) / len(last_30)
            recent_res_30 = sum(e.resonance for e in last_30) / len(last_30)
            if recent_cons_30 < 0.3 and recent_res_30 < 0.3:
                inc_penalty = 15

        # Type variety
        unique_types = len(set(e.blog_type for e in self._entries))

        score = (avg_clar * 20) + (avg_voi * 15) + (avg_struc * 10) + (avg_val * 20) + (avg_res * 15) + (avg_cons * 15) + (recent_cons * 5) + (recent_res * 5) + (unique_types * 2) - inc_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_resonance"] = round(sum(e.resonance for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_cons = sum(e.consistency for e in recent) / len(recent)
                recent_res = sum(e.resonance for e in recent) / len(recent)
                self._stats["inconsistency_risk"] = recent_cons < 0.3 and recent_res < 0.3
            else:
                self._stats["inconsistency_risk"] = False

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

    def _log_entry(self, entry: BlogEntry):
        try:
            with open(BLOG_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "post": entry.post,
                    "blog_type": entry.blog_type,
                    "clarity": entry.clarity,
                    "resonance": entry.resonance,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_bcc_instance: Optional[BlogCraftCoach] = None
_bcc_lock = threading.Lock()


def get_blog_craft_coach() -> BlogCraftCoach:
    global _bcc_instance
    with _bcc_lock:
        if _bcc_instance is None:
            _bcc_instance = BlogCraftCoach()
        return _bcc_instance
