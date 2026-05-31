"""
LOVE Social Connection Monitor — Relationship Intelligence (Modern AI Pattern)

Social connections are vital but often neglected. This monitor:

1. INTERACTION TRACKING
   - Track social interactions from conversations and logs
   - Identify who the user talks to most / least
   - Detect social isolation patterns

2. RELATIONSHIP HEALTH SCORING
   - Score relationship strength based on interaction frequency and quality
   - Detect declining relationships (interactions dropping off)
   - Identify relationships needing attention

3. PROACTIVE SOCIAL NUDGES
   - Suggest reaching out to neglected connections
   - Remind about important dates (birthdays, anniversaries)
   - Recommend social activities based on context

4. SOCIAL WELLBEING METRICS
   - Track daily/weekly social interaction counts
   - Calculate social wellbeing score
   - Correlate social activity with mood and energy

Architecture:
- record_interaction(person, type, quality): Log social interaction
- get_social_insights(): Get social pattern analysis
- get_social_score(): Get overall social wellbeing score
- get_reconnection_suggestions(): Suggest people to reach out to
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "social_connection_monitor"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SOCIAL_LOG = DATA_DIR / "social_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SocialInteraction:
    """A social interaction record."""
    person: str = ""
    interaction_type: str = ""  # message, call, in_person, video
    quality: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_minutes: float = 0.0
    topics: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    """Relationship health tracking."""
    person: str = ""
    total_interactions: int = 0
    last_interaction: Optional[str] = None
    avg_quality: float = 0.5
    interaction_frequency: float = 0.0  # interactions per week
    health_score: float = 0.5
    status: str = "active"  # active, declining, neglected, strong


class SocialConnectionMonitor:
    """
    Monitor social connections and provide relationship intelligence.
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
        self._interactions: deque = deque(maxlen=500)
        self._relationships: Dict[str, Relationship] = {}
        self._stats = {
            "total_interactions": 0,
            "daily_avg": 0.0,
            "social_score": 50,
            "isolation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, person: str, interaction_type: str = "message", quality: float = 0.5, duration: float = 0.0, topics: Optional[List[str]] = None):
        """Record a social interaction."""
        interaction = SocialInteraction(
            person=person,
            interaction_type=interaction_type,
            quality=quality,
            duration_minutes=duration,
            topics=topics or [],
        )

        with self._lock:
            self._interactions.append(interaction)
            self._stats["total_interactions"] += 1
            self._update_relationship(interaction)
            self._update_social_score()

        self._save_stats()
        self._log_interaction(interaction)

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_social_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get social pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [i for i in self._interactions if i.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Count by person
        by_person = defaultdict(int)
        by_type = defaultdict(int)
        for i in recent:
            by_person[i.person] += 1
            by_type[i.interaction_type] += 1

        # Isolation detection
        daily_counts = defaultdict(int)
        for i in recent:
            day = i.timestamp[:10]
            daily_counts[day] += 1

        avg_daily = sum(daily_counts.values()) / max(1, len(daily_counts))
        isolation_risk = avg_daily < 1 and len(self._relationships) < 3

        return {
            "days_analyzed": len(set(i.timestamp[:10] for i in recent)),
            "total_interactions": len(recent),
            "unique_contacts": len(by_person),
            "avg_daily_interactions": round(avg_daily, 1),
            "top_contacts": sorted(by_person.items(), key=lambda x: x[1], reverse=True)[:5],
            "interaction_types": dict(by_type),
            "isolation_risk": isolation_risk,
        }

    def get_social_score(self) -> int:
        """Calculate overall social wellbeing score (0-100)."""
        if not self._interactions:
            return 50

        recent = list(self._interactions)[-30:]
        daily_counts = defaultdict(int)
        for i in recent:
            day = i.timestamp[:10]
            daily_counts[day] += 1

        avg_daily = sum(daily_counts.values()) / max(1, len(daily_counts))
        unique_contacts = len(set(i.person for i in recent))
        avg_quality = sum(i.quality for i in recent) / max(1, len(recent))

        # Frequency score (2-5 interactions per day is healthy)
        freq_score = max(0, min(100, avg_daily * 25))

        # Diversity score (3+ unique contacts per week is healthy)
        diversity_score = min(100, unique_contacts * 20)

        # Quality score
        quality_score = avg_quality * 100

        overall = round(freq_score * 0.4 + diversity_score * 0.3 + quality_score * 0.3)
        self._stats["social_score"] = overall
        self._stats["isolation_risk"] = overall < 30
        return overall

    def get_reconnection_suggestions(self) -> List[Dict[str, Any]]:
        """Suggest people to reconnect with."""
        now = datetime.now()
        suggestions = []

        for person, rel in self._relationships.items():
            if not rel.last_interaction:
                continue

            try:
                last = datetime.fromisoformat(rel.last_interaction)
                days_since = (now - last).days
            except Exception:
                continue

            # Suggest if neglected
            if days_since > 14 and rel.health_score > 0.4:
                urgency = "high" if days_since > 30 else "medium"
                suggestions.append({
                    "person": person,
                    "days_since": days_since,
                    "last_quality": rel.avg_quality,
                    "suggested_action": "send message or call",
                    "urgency": urgency,
                    "reason": f"No contact for {days_since} days",
                })

        # Sort by urgency and days since
        suggestions.sort(key=lambda x: (x["urgency"] != "high", x["days_since"]), reverse=True)
        return suggestions[:5]

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_relationship(self, interaction: SocialInteraction):
        """Update relationship tracking."""
        person = interaction.person
        if person not in self._relationships:
            self._relationships[person] = Relationship(person=person)

        rel = self._relationships[person]
        rel.total_interactions += 1
        rel.last_interaction = interaction.timestamp

        # Update average quality
        prev_avg = rel.avg_quality
        rel.avg_quality = round((prev_avg * (rel.total_interactions - 1) + interaction.quality) / rel.total_interactions, 2)

        # Calculate frequency (interactions per week)
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        recent_count = sum(1 for i in self._interactions if i.person == person and i.timestamp > cutoff)
        rel.interaction_frequency = round(recent_count * 7 / 30, 1)

        # Health score
        rel.health_score = round(min(1.0, rel.interaction_frequency / 3 + rel.avg_quality * 0.3), 2)

        # Status
        if rel.interaction_frequency > 2:
            rel.status = "strong"
        elif rel.interaction_frequency > 0.5:
            rel.status = "active"
        elif rel.health_score > 0.3:
            rel.status = "declining"
        else:
            rel.status = "neglected"

    def _update_social_score(self):
        """Update overall social score."""
        score = self.get_social_score()
        self._stats["social_score"] = score

        # Update daily average
        today = datetime.now().date().isoformat()
        today_count = sum(1 for i in self._interactions if i.timestamp[:10] == today)

        prev_avg = self._stats.get("daily_avg", 0)
        n = min(30, len(self._interactions))
        self._stats["daily_avg"] = round((prev_avg * max(0, n - 1) + today_count) / max(1, n), 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "relationships": {k: {
                    "person": v.person,
                    "total_interactions": v.total_interactions,
                    "last_interaction": v.last_interaction,
                    "avg_quality": v.avg_quality,
                    "interaction_frequency": v.interaction_frequency,
                    "health_score": v.health_score,
                    "status": v.status,
                } for k, v in self._relationships.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("relationships", {}).items():
                    self._relationships[k] = Relationship(**v)
        except Exception:
            pass

    def _log_interaction(self, interaction: SocialInteraction):
        try:
            with open(SOCIAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": interaction.timestamp,
                    "person": interaction.person,
                    "type": interaction.interaction_type,
                    "quality": interaction.quality,
                    "duration": interaction.duration_minutes,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_scm_instance: Optional[SocialConnectionMonitor] = None
_scm_lock = threading.Lock()


def get_social_connection_monitor() -> SocialConnectionMonitor:
    global _scm_instance
    with _scm_lock:
        if _scm_instance is None:
            _scm_instance = SocialConnectionMonitor()
        return _scm_instance
