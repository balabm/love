"""
LOVE Active Listening Master — Presence Intelligence (Modern AI Pattern)

Most people listen to respond. This master listens to understand.

1. LISTENING TRACKING
   - Record listening moments and their characteristics
   - Track listening types (empathic, reflective, clarifying, supportive, silent)
   - Log presence, understanding, and impact of listening

2. PATTERN ANALYSIS
   - Identify the user's listening profile (distracted, polite, engaged, masterful)
   - Find listening patterns that create connection vs distance
   - Detect chronic non-listening and its costs

3. LISTENING MASTERY
   - Suggest practices for deeper, more present listening
   - Provide frameworks for reflective and empathic listening
   - Recommend practices for listening without fixing or judging

4. PRESENCE CULTIVATION
   - Track the correlation between listening quality and relationship depth
   - Alert when waiting-to-speak is replacing genuine listening
   - Celebrate moments of truly being present for another

Architecture:
- record_listening(situation, type, presence, understanding, impact): Log listening
- get_listening_stats(): Get listening pattern analysis
- get_listening_suggestion(capacity, context): Get suggestion
- get_listening_score(): Calculate overall listening health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "active_listening_master"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LISTENING_LOG = DATA_DIR / "listenings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ListeningEntry:
    """A tracked listening moment."""
    entry_id: str = ""
    situation: str = ""  # what was listened to
    listening_type: str = ""  # empathic, reflective, clarifying, supportive, silent
    presence: float = 0.0  # 0-1
    understanding: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    no_fixing: float = 0.0  # 0-1 resisted urge to fix?
    no_judging: float = 0.0  # 0-1 resisted urge to judge?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ActiveListeningMaster:
    """
    Intelligent active listening master with distraction detection and presence cultivation.
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
            "avg_presence": 0.0,
            "avg_understanding": 0.0,
            "distraction_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_listening(self, situation: str = "", listening_type: str = "", presence: float = 0.0, understanding: float = 0.0, impact: float = 0.0, no_fixing: float = 0.0, no_judging: float = 0.0, notes: str = "") -> ListeningEntry:
        """Record a listening moment."""
        entry_id = f"lst_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ListeningEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            listening_type=listening_type or "empathic",
            presence=presence,
            understanding=understanding,
            impact=impact,
            no_fixing=no_fixing,
            no_judging=no_judging,
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

    def get_listening_stats(self) -> Dict[str, Any]:
        """Get listening pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "presence_sum": 0.0, "understanding_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            by_type[e.listening_type]["count"] += 1
            by_type[e.listening_type]["presence_sum"] += e.presence
            by_type[e.listening_type]["understanding_sum"] += e.understanding
            by_type[e.listening_type]["impact_sum"] += e.impact

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_presence": round(data["presence_sum"] / count, 2),
                "avg_understanding": round(data["understanding_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Presence analysis
        high_pres = [e for e in self._entries if e.presence > 0.7]
        low_pres = [e for e in self._entries if e.presence < 0.4]
        if high_pres and low_pres:
            high_pres_imp = sum(e.impact for e in high_pres) / len(high_pres)
            low_pres_imp = sum(e.impact for e in low_pres) / len(low_pres)
            high_pres_und = sum(e.understanding for e in high_pres) / len(high_pres)
            low_pres_und = sum(e.understanding for e in low_pres) / len(low_pres)
        else:
            high_pres_imp = 0
            low_pres_imp = 0
            high_pres_und = 0
            low_pres_und = 0

        # No-fixing analysis
        high_nf = [e for e in self._entries if e.no_fixing > 0.7]
        low_nf = [e for e in self._entries if e.no_fixing < 0.4]
        if high_nf and low_nf:
            high_nf_imp = sum(e.impact for e in high_nf) / len(high_nf)
            low_nf_imp = sum(e.impact for e in low_nf) / len(low_nf)
        else:
            high_nf_imp = 0
            low_nf_imp = 0

        # Distraction risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_pres = sum(e.presence for e in recent) / len(recent)
            recent_und = sum(e.understanding for e in recent) / len(recent)
            distraction_risk = recent_pres < 0.4 and recent_und < 0.4
        else:
            distraction_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "presence_impact": {
                "high_presence_impact": round(high_pres_imp, 2),
                "low_presence_impact": round(low_pres_imp, 2),
                "high_presence_understanding": round(high_pres_und, 2),
                "low_presence_understanding": round(low_pres_und, 2),
            },
            "no_fixing_effect": {
                "high_no_fixing_impact": round(high_nf_imp, 2),
                "low_no_fixing_impact": round(low_nf_imp, 2),
            },
            "distraction_risk": distraction_risk,
            "avg_presence": round(sum(e.presence for e in self._entries) / len(self._entries), 2),
            "avg_understanding": round(sum(e.understanding for e in self._entries) / len(self._entries), 2),
        }

    def get_listening_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get listening suggestion."""
        suggestions = [
            "Most people don't listen. They wait to speak. Their mind is preparing their response while you're still talking. Don't be most people. Empty your mind. Listen. Then respond.",
            "Listening is not passive. It's active. It requires attention. It requires curiosity. It requires you to set aside your agenda. That's work. And it's the most important work in any relationship.",
            "Don't fix. Don't advise. Don't one-up. Just listen. Most people don't want solutions. They want to be heard. They want to know their experience matters. Be the person who gives them that.",
            "Reflect back what you heard. Not to show off. To confirm. 'What I'm hearing is...' This simple practice transforms listening from passive to active. From hearing to understanding.",
            "Put away your phone. Close your laptop. Turn toward the person. Your body language is part of listening. If your body is elsewhere, your mind is too. Be physically present. Mental presence follows.",
            "Listen for what's not being said. The hesitation. The sigh. The pause. The thing they almost said but didn't. The best listeners hear the silence. And they ask about it.",
            "Your opinions are not the gift. Your attention is. The person who feels truly listened to feels valued. Seen. Understood. That's a gift more precious than any advice you could give.",
            "Practice silence. After they finish speaking, wait. Count to three. Most people rush to fill silence. But silence is where reflection lives. It's where the deeper truth emerges.",
            "Don't judge what you're hearing. Not even internally. Judgment creates distance. Curiosity creates connection. Replace 'that's stupid' with 'help me understand.' Same information. Different effect.",
            "The person who listens well is never lonely. Because people are drawn to them. Because being heard is the deepest human need. And the person who provides it becomes indispensable."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of genuine listening. One phone put away. One response withheld. One breath of presence. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A reflective listening practice. A clarifying question. A moment of silence. Medium mastery."
        else:
            capacity_note = "Good capacity. Deep listening mastery. A systematic practice of full presence and understanding. You have the strength to truly hear."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Active listening is the most underrated skill in human life. It's more important than speaking. More important than intelligence. More important than charisma. Because listening is how connection happens. And connection is what humans need most. But most people don't listen. They perform listening. They nod while planning their response. They make eye contact while thinking about dinner. They say 'I understand' while completely missing the point. And the person speaking knows. They always know. The work of active listening mastery is about becoming someone who actually listens. Who is fully present. Who seeks to understand before seeking to be understood. Who can sit in silence without discomfort. Who can hear pain without rushing to fix it. Who can hear difference without rushing to judge it. That's the work. And it's the foundation of every meaningful relationship you'll ever have."
        }

    def get_listening_score(self) -> int:
        """Calculate overall listening health (0-100)."""
        if not self._entries:
            return 25

        avg_pres = sum(e.presence for e in self._entries) / len(self._entries)
        avg_und = sum(e.understanding for e in self._entries) / len(self._entries)
        avg_imp = sum(e.impact for e in self._entries) / len(self._entries)
        avg_nf = sum(e.no_fixing for e in self._entries) / len(self._entries)
        avg_nj = sum(e.no_judging for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_pres = sum(e.presence for e in recent) / len(recent)
            recent_und = sum(e.understanding for e in recent) / len(recent)
        else:
            recent_pres = 0
            recent_und = 0

        # Distraction penalty
        dist_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_pres_30 = sum(e.presence for e in last_30) / len(last_30)
            recent_und_30 = sum(e.understanding for e in last_30) / len(last_30)
            if recent_pres_30 < 0.4 and recent_und_30 < 0.4:
                dist_penalty = 15

        # Type variety
        unique_types = len(set(e.listening_type for e in self._entries))

        score = (avg_pres * 25) + (avg_und * 20) + (avg_imp * 15) + (avg_nf * 15) + (avg_nj * 10) + (recent_pres * 5) + (recent_und * 5) + (unique_types * 2) - dist_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_presence"] = round(sum(e.presence for e in self._entries) / len(self._entries), 2)
            self._stats["avg_understanding"] = round(sum(e.understanding for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_pres = sum(e.presence for e in recent) / len(recent)
                recent_und = sum(e.understanding for e in recent) / len(recent)
                self._stats["distraction_risk"] = recent_pres < 0.4 and recent_und < 0.4
            else:
                self._stats["distraction_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.active_listening_master")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.active_listening_master")

    def _log_entry(self, entry: ListeningEntry):
        try:
            with open(LISTENING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "listening_type": entry.listening_type,
                    "presence": entry.presence,
                    "understanding": entry.understanding,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.active_listening_master")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_alm_instance: Optional[ActiveListeningMaster] = None
_alm_lock = threading.Lock()


def get_active_listening_master() -> ActiveListeningMaster:
    global _alm_instance
    with _alm_lock:
        if _alm_instance is None:
            _alm_instance = ActiveListeningMaster()
        return _alm_instance
