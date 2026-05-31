"""
LOVE Storytelling Coach — Narrative Intelligence (Modern AI Pattern)

Most people live without understanding the power of their own story. This coach:

1. STORY TRACKING
   - Record storytelling moments and their characteristics
   - Track story types (personal, relational, aspirational, healing, teaching)
   - Log clarity, impact, and authenticity of stories

2. PATTERN ANALYSIS
   - Identify the user's storytelling profile (natural, hesitant, performative, healing)
   - Find storytelling patterns that create connection vs distance
   - Detect silence and its costs

3. STORY BUILDING
   - Suggest practices for crafting and sharing meaningful stories
   - Provide frameworks for turning experience into narrative
   - Recommend stories that heal, connect, and inspire

4. NARRATIVE CULTIVATION
   - Track the correlation between storytelling and life meaning
   - Alert when the user's story is being written by others
   - Celebrate moments of genuine narrative power

Architecture:
- record_story(story, type, clarity, impact, authenticity): Log story
- get_storytelling_stats(): Get storytelling pattern analysis
- get_storytelling_suggestion(capacity, context): Get suggestion
- get_storytelling_score(): Calculate overall storytelling health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "storytelling_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STORY_LOG = DATA_DIR / "stories.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class StoryEntry:
    """A tracked storytelling moment."""
    entry_id: str = ""
    story: str = ""  # what was shared
    story_type: str = ""  # personal, relational, aspirational, healing, teaching
    clarity: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    authenticity: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    courage: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class StorytellingCoach:
    """
    Intelligent storytelling coach with impact detection and narrative cultivation.
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
            "avg_impact": 0.0,
            "avg_authenticity": 0.0,
            "silence_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_story(self, story: str = "", story_type: str = "", clarity: float = 0.0, impact: float = 0.0, authenticity: float = 0.0, connection: float = 0.0, courage: float = 0.0, notes: str = "") -> StoryEntry:
        """Record a storytelling moment."""
        entry_id = f"stc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = StoryEntry(
            entry_id=entry_id,
            story=story or "unspecified",
            story_type=story_type or "personal",
            clarity=clarity,
            impact=impact,
            authenticity=authenticity,
            connection=connection,
            courage=courage,
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

    def get_storytelling_stats(self) -> Dict[str, Any]:
        """Get storytelling pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "impact_sum": 0.0, "authenticity_sum": 0.0, "connection_sum": 0.0})
        for e in self._entries:
            by_type[e.story_type]["count"] += 1
            by_type[e.story_type]["impact_sum"] += e.impact
            by_type[e.story_type]["authenticity_sum"] += e.authenticity
            by_type[e.story_type]["connection_sum"] += e.connection

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_impact": round(data["impact_sum"] / count, 2),
                "avg_authenticity": round(data["authenticity_sum"] / count, 2),
                "avg_connection": round(data["connection_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_connection"]) if type_stats else ("", {})

        # Impact analysis
        high_impact = [e for e in self._entries if e.impact > 0.7]
        low_impact = [e for e in self._entries if e.impact < 0.4]
        if high_impact and low_impact:
            high_imp_conn = sum(e.connection for e in high_impact) / len(high_impact)
            low_imp_conn = sum(e.connection for e in low_impact) / len(low_impact)
            high_imp_cour = sum(e.courage for e in high_impact) / len(high_impact)
            low_imp_cour = sum(e.courage for e in low_impact) / len(low_impact)
        else:
            high_imp_conn = 0
            low_imp_conn = 0
            high_imp_cour = 0
            low_imp_cour = 0

        # Authenticity analysis
        high_auth = [e for e in self._entries if e.authenticity > 0.7]
        low_auth = [e for e in self._entries if e.authenticity < 0.4]
        if high_auth and low_auth:
            high_auth_imp = sum(e.impact for e in high_auth) / len(high_auth)
            low_auth_imp = sum(e.impact for e in low_auth) / len(low_auth)
        else:
            high_auth_imp = 0
            low_auth_imp = 0

        # Silence risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_impact = sum(e.impact for e in recent) / len(recent)
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
            silence_risk = recent_impact < 0.3 and recent_auth < 0.3
        else:
            silence_risk = True

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "impact_analysis": {
                "high_impact_connection": round(high_imp_conn, 2),
                "low_impact_connection": round(low_imp_conn, 2),
                "high_impact_courage": round(high_imp_cour, 2),
                "low_impact_courage": round(low_imp_cour, 2),
            },
            "authenticity_effect": {
                "high_authenticity_impact": round(high_auth_imp, 2),
                "low_authenticity_impact": round(low_auth_imp, 2),
            },
            "silence_risk": silence_risk,
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 2),
            "avg_authenticity": round(sum(e.authenticity for e in self._entries) / len(self._entries), 2),
        }

    def get_storytelling_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get storytelling suggestion."""
        suggestions = [
            "Tell your story. Not the polished version. The real one. The failures. The doubts. The turning points. Real stories create real connection. Polished stories create distance.",
            "Stories are how we make sense of chaos. When life doesn't make sense, tell the story. The act of narrating creates meaning. Even if the meaning is just: I survived.",
            "Listen to other people's stories. Everyone has one. The person who seems boring has a story that would break your heart. Be curious. Ask. Listen.",
            "Your story is not over. No matter how old you are. No matter what you've done. The ending is not written. You can change the narrative. You can become the hero.",
            "Share the lesson, not just the wound. Wounds without lessons are just pain. Wounds with lessons are wisdom. What did you learn? How did you change?",
            "Practice telling your story. In the mirror. To a friend. In writing. The better you tell it, the more power it has. For you. And for others.",
            "The stories you tell about yourself become your identity. Tell stories of resilience. Of growth. Of love. Not stories of victimhood. Of bitterness. Of defeat.",
            "Stories connect across difference. The person who doesn't look like you. Who doesn't believe what you believe. They have a story too. And in the story, you meet as humans.",
            "Write your story down. Journal. Memoir. Letter. The written story is different from the remembered story. It's more honest. More complete. More powerful.",
            "You are the author of your life. Not the editor. Not the critic. The author. Write boldly. Edit later. But first, write. Your story deserves to be told."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One sentence. One memory. One shared moment. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A real story. A conversation. A written reflection. Medium narrative work."
        else:
            capacity_note = "Good capacity. A major story. A public share. A life narrative. You have the energy for real storytelling."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Humans are storytelling animals. We don't experience life as data. We experience it as narrative. The story of who we are. The story of where we came from. The story of where we're going. And the quality of our lives is deeply connected to the quality of our stories. The person who tells a story of victimhood lives as a victim. The person who tells a story of survival lives as a survivor. The person who tells a story of growth lives as a growing person. Your story is not just a description of your life. It's a prescription for it. Choose your narrative carefully. Because you will live it."
        }

    def get_storytelling_score(self) -> int:
        """Calculate overall storytelling health (0-100)."""
        if not self._entries:
            return 25

        avg_impact = sum(e.impact for e in self._entries) / len(self._entries)
        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_conn = sum(e.connection for e in self._entries) / len(self._entries)
        avg_courage = sum(e.courage for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_impact = sum(e.impact for e in recent) / len(recent)
            recent_auth = sum(e.authenticity for e in recent) / len(recent)
        else:
            recent_impact = 0
            recent_auth = 0

        # Silence penalty
        silence_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(last_30) < 2:
            silence_penalty = 15

        # Type variety
        unique_types = len(set(e.story_type for e in self._entries))

        score = (avg_impact * 25) + (avg_auth * 25) + (avg_clarity * 15) + (avg_conn * 15) + (avg_courage * 10) + (recent_impact * 5) + (recent_auth * 5) + (unique_types * 2) - silence_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_impact"] = round(sum(e.impact for e in self._entries) / len(self._entries), 2)
            self._stats["avg_authenticity"] = round(sum(e.authenticity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_impact = sum(e.impact for e in recent) / len(recent)
                recent_auth = sum(e.authenticity for e in recent) / len(recent)
                self._stats["silence_risk"] = recent_impact < 0.3 and recent_auth < 0.3
            else:
                self._stats["silence_risk"] = True

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

    def _log_entry(self, entry: StoryEntry):
        try:
            with open(STORY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "story": entry.story,
                    "story_type": entry.story_type,
                    "impact": entry.impact,
                    "authenticity": entry.authenticity,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sc_instance: Optional[StorytellingCoach] = None
_sc_lock = threading.Lock()


def get_storytelling_coach() -> StorytellingCoach:
    global _sc_instance
    with _sc_lock:
        if _sc_instance is None:
            _sc_instance = StorytellingCoach()
        return _sc_instance
