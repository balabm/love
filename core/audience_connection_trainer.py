"""
LOVE Audience Connection Trainer — Engagement Intelligence (Modern AI Pattern)

Most people talk AT audiences. This trainer:

1. CONNECTION TRACKING
   - Record audience connection moments and their characteristics
   - Track connection types (eye_contact, storytelling, question, humor, vulnerability, invitation)
   - Log engagement, empathy, responsiveness, reciprocity, and energy of connection

2. PATTERN ANALYSIS
   - Identify the user's connection profile (distant, transactional, developing, magnetic)
   - Find connection patterns that create engagement vs disconnection
   - Detect chronic broadcasting and its costs

3. CONNECTION BUILDING
   - Suggest practices for genuine audience engagement
   - Provide frameworks for reading room energy
   - Recommend practices for responsive, adaptive communication

4. MAGNETIC ENGAGEMENT CULTIVATION
   - Track the correlation between connection quality and audience response
   - Alert when monologue is replacing dialogue
   - Celebrate moments of genuine, two-way human connection

Architecture:
- record_connection(moment, type, engagement, empathy, responsiveness, reciprocity, energy): Log connection
- get_connection_stats(): Get connection pattern analysis
- get_connection_suggestion(capacity, context): Get suggestion
- get_connection_score(): Calculate overall connection health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "audience_connection_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONNECTION_LOG = DATA_DIR / "connections.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AudienceConnectionEntry:
    """A tracked audience connection moment."""
    entry_id: str = ""
    moment: str = ""  # what was the moment
    connection_type: str = ""  # eye_contact, storytelling, question, humor, vulnerability, invitation
    engagement: float = 0.0  # 0-1
    empathy: float = 0.0  # 0-1
    responsiveness: float = 0.0  # 0-1
    reciprocity: float = 0.0  # 0-1
    energy: float = 0.0  # 0-1
    adaptation: float = 0.0  # 0-1 did you adapt to audience?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AudienceConnectionTrainer:
    """
    Intelligent audience connection trainer with broadcasting detection and magnetic engagement cultivation.
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
            "avg_engagement": 0.0,
            "avg_reciprocity": 0.0,
            "broadcasting_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_connection(self, moment: str = "", connection_type: str = "", engagement: float = 0.0, empathy: float = 0.0, responsiveness: float = 0.0, reciprocity: float = 0.0, energy: float = 0.0, adaptation: float = 0.0, notes: str = "") -> AudienceConnectionEntry:
        """Record an audience connection moment."""
        entry_id = f"aud_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = AudienceConnectionEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            connection_type=connection_type or "eye_contact",
            engagement=engagement,
            empathy=empathy,
            responsiveness=responsiveness,
            reciprocity=reciprocity,
            energy=energy,
            adaptation=adaptation,
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

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "engagement_sum": 0.0, "empathy_sum": 0.0, "energy_sum": 0.0})
        for e in self._entries:
            by_type[e.connection_type]["count"] += 1
            by_type[e.connection_type]["engagement_sum"] += e.engagement
            by_type[e.connection_type]["empathy_sum"] += e.empathy
            by_type[e.connection_type]["energy_sum"] += e.energy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_engagement": round(data["engagement_sum"] / count, 2),
                "avg_empathy": round(data["empathy_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
            }

        # Engagement analysis
        high_eng = [e for e in self._entries if e.engagement > 0.7]
        low_eng = [e for e in self._entries if e.engagement < 0.4]
        if high_eng and low_eng:
            high_eng_recip = sum(e.reciprocity for e in high_eng) / len(high_eng)
            low_eng_recip = sum(e.reciprocity for e in low_eng) / len(low_eng)
            high_eng_ener = sum(e.energy for e in high_eng) / len(high_eng)
            low_eng_ener = sum(e.energy for e in low_eng) / len(low_eng)
        else:
            high_eng_recip = 0
            low_eng_recip = 0
            high_eng_ener = 0
            low_eng_ener = 0

        # Adaptation analysis
        high_adapt = [e for e in self._entries if e.adaptation > 0.7]
        low_adapt = [e for e in self._entries if e.adaptation < 0.4]
        if high_adapt and low_adapt:
            high_adapt_eng = sum(e.engagement for e in high_adapt) / len(high_adapt)
            low_adapt_eng = sum(e.engagement for e in low_adapt) / len(low_adapt)
        else:
            high_adapt_eng = 0
            low_adapt_eng = 0

        # Broadcasting risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_eng = sum(e.engagement for e in recent) / len(recent)
            recent_recip = sum(e.reciprocity for e in recent) / len(recent)
            broadcasting_risk = recent_eng < 0.3 and recent_recip < 0.3
        else:
            broadcasting_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "engagement_impact": {
                "high_engagement_reciprocity": round(high_eng_recip, 2),
                "low_engagement_reciprocity": round(low_eng_recip, 2),
                "high_engagement_energy": round(high_eng_ener, 2),
                "low_engagement_energy": round(low_eng_ener, 2),
            },
            "adaptation_effect": {
                "high_adaptation_engagement": round(high_adapt_eng, 2),
                "low_adaptation_engagement": round(low_adapt_eng, 2),
            },
            "broadcasting_risk": broadcasting_risk,
            "avg_engagement": round(sum(e.engagement for e in self._entries) / len(self._entries), 2),
            "avg_reciprocity": round(sum(e.reciprocity for e in self._entries) / len(self._entries), 2),
        }

    def get_connection_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get connection suggestion."""
        suggestions = [
            "The audience is not a wall. They're humans. With faces. With feelings. With attention spans. With needs. Talk to them. Not at them. Not through them. To them.",
            "Make eye contact. Not creepy. Sustained. Move around the room. Look at different people. Let them feel seen. Because they are. And when they feel seen, they pay attention.",
            "Tell stories. Not facts. Facts inform. Stories involve. The person who tells stories creates connection. Because stories are shared human experience. And shared experience is connection.",
            "Ask questions. Even rhetorical ones. Questions engage. They create mental participation. They turn passive listeners into active thinkers. And active thinkers are connected.",
            "Read the room. Are they bored? Energized? Confused? Lost? You can tell. Look at their faces. Their posture. Their energy. Then adapt. Speed up. Slow down. Go deeper. Shift. The person who reads the room and responds is the person who owns the room.",
            "Invite participation. A show of hands. A thought to share. A moment of silence. An invitation to imagine. Participation is the bridge between speaker and audience. Build it.",
            "Be vulnerable. Share a failure. A doubt. A human moment. Perfection is alienating. Vulnerability is connecting. The person who shows they're human is the person the audience trusts.",
            "Use humor. Even a little. A chuckle creates rapport. It releases tension. It makes you approachable. But don't force it. Forced humor is worse than no humor. Be natural.",
            "Remember their names. If you can. Remember their faces. If you can't. Remember that they came. That they gave you their time. That they chose to listen. Honor that.",
            "The person who connects with their audience doesn't have fans. They have relationships. They have trust. They have people who want them to succeed. And that is the most valuable thing any speaker can have."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One eye contact held. One story told. One question asked. One smile exchanged. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A room read. An adaptation made. A moment of vulnerability shared. A laugh earned. Medium connection."
        else:
            capacity_note = "Good capacity. Deep audience work. A systematic practice of engagement, empathy, and magnetic presence. You have the strength to move a room."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Audience connection is not about charisma. It's about respect. Most people treat audiences as targets. As receptacles for information. As obstacles to overcome. And they wonder why nobody cares. Why nobody remembers. Why nobody acts. The work of audience connection training is about understanding that every person in the room is a human being with their own life, their own concerns, their own dreams. And that the speaker's job is not to deliver content. It's to create a shared experience. It's about eye contact. About stories. About questions. About vulnerability. About reading the room and adapting in real time. And about understanding that the person who truly connects with their audience doesn't just deliver a message. They create a relationship. And relationships are what change minds, move hearts, and inspire action."
        }

    def get_connection_score(self) -> int:
        """Calculate overall connection health (0-100)."""
        if not self._entries:
            return 25

        avg_eng = sum(e.engagement for e in self._entries) / len(self._entries)
        avg_emp = sum(e.empathy for e in self._entries) / len(self._entries)
        avg_resp = sum(e.responsiveness for e in self._entries) / len(self._entries)
        avg_recip = sum(e.reciprocity for e in self._entries) / len(self._entries)
        avg_ener = sum(e.energy for e in self._entries) / len(self._entries)
        avg_adapt = sum(e.adaptation for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_eng = sum(e.engagement for e in recent) / len(recent)
            recent_recip = sum(e.reciprocity for e in recent) / len(recent)
        else:
            recent_eng = 0
            recent_recip = 0

        # Broadcasting penalty
        broad_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_eng_30 = sum(e.engagement for e in last_30) / len(last_30)
            recent_recip_30 = sum(e.reciprocity for e in last_30) / len(last_30)
            if recent_eng_30 < 0.3 and recent_recip_30 < 0.3:
                broad_penalty = 15

        # Type variety
        unique_types = len(set(e.connection_type for e in self._entries))

        score = (avg_eng * 25) + (avg_emp * 10) + (avg_resp * 10) + (avg_recip * 15) + (avg_ener * 10) + (avg_adapt * 15) + (recent_eng * 5) + (recent_recip * 5) + (unique_types * 2) - broad_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_engagement"] = round(sum(e.engagement for e in self._entries) / len(self._entries), 2)
            self._stats["avg_reciprocity"] = round(sum(e.reciprocity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_eng = sum(e.engagement for e in recent) / len(recent)
                recent_recip = sum(e.reciprocity for e in recent) / len(recent)
                self._stats["broadcasting_risk"] = recent_eng < 0.3 and recent_recip < 0.3
            else:
                self._stats["broadcasting_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.audience_connection_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.audience_connection_trainer")

    def _log_entry(self, entry: AudienceConnectionEntry):
        try:
            with open(CONNECTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "connection_type": entry.connection_type,
                    "engagement": entry.engagement,
                    "reciprocity": entry.reciprocity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.audience_connection_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_act_instance: Optional[AudienceConnectionTrainer] = None
_act_lock = threading.Lock()


def get_audience_connection_trainer() -> AudienceConnectionTrainer:
    global _act_instance
    with _act_lock:
        if _act_instance is None:
            _act_instance = AudienceConnectionTrainer()
        return _act_instance
