"""
LOVE Conflict Resolution Coach — Relationship Intelligence (Modern AI Pattern)

Most conflict advice is reactive. This coach:

1. CONFLICT TRACKING
   - Record conflicts with trigger, parties, intensity, and outcome
   - Track resolution time and emotional cost
   - Log which strategies worked vs failed

2. PATTERN ANALYSIS
   - Identify recurring conflict triggers and themes
   - Detect escalation patterns before they explode
   - Find user's default conflict style (avoidant, accommodating, compromising, collaborative, competitive)

3. STRATEGY RECOMMENDATION
   - Suggest de-escalation techniques based on conflict type
   - Recommend I-statements and active listening scripts
   - Propose timing and setting for difficult conversations

4. PROACTIVE PREVENTION
   - Alert when similar conflict patterns emerge
   - Suggest boundary-setting before issues escalate
   - Track relationship health scores over time

Architecture:
- record_conflict(trigger, parties, intensity, resolution): Log conflict
- get_conflict_patterns(): Get recurring theme analysis
- get_resolution_strategy(conflict_type): Get tailored strategy
- get_relationship_health(): Calculate relationship status
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "conflict_resolution_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFLICT_LOG = DATA_DIR / "conflicts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Conflict:
    """A tracked conflict."""
    conflict_id: str = ""
    trigger: str = ""  # what started it
    parties: List[str] = field(default_factory=list)
    conflict_type: str = ""  # values, needs, power, misunderstanding, external_stress
    intensity: float = 5.0  # 1-10
    duration_minutes: float = 0.0
    user_style: str = ""  # avoidant, accommodating, compromising, collaborative, competitive
    resolution: str = ""  # resolved, unresolved, ongoing, escalated
    strategies_used: List[str] = field(default_factory=list)
    outcome_satisfaction: float = 0.5
    emotional_cost: float = 0.5  # 0-1, how draining it was
    lessons_learned: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ConflictResolutionCoach:
    """
    Intelligent conflict coach with pattern analysis and proactive prevention.
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
        self._conflicts: deque = deque(maxlen=200)
        self._stats = {
            "total_conflicts": 0,
            "avg_intensity": 0.0,
            "resolution_rate": 0.0,
            "avg_emotional_cost": 0.0,
            "dominant_style": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_conflict(self, trigger: str = "", parties: Optional[List[str]] = None, conflict_type: str = "", intensity: float = 5.0, duration: float = 0, user_style: str = "", resolution: str = "", strategies: Optional[List[str]] = None, outcome: float = 0.5, emotional_cost: float = 0.5, lessons: Optional[List[str]] = None) -> Conflict:
        """Record a conflict."""
        conflict_id = f"conflict_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._conflicts)}"
        conflict = Conflict(
            conflict_id=conflict_id,
            trigger=trigger or "unspecified",
            parties=parties or [],
            conflict_type=conflict_type or "misunderstanding",
            intensity=intensity,
            duration_minutes=duration,
            user_style=user_style or "unspecified",
            resolution=resolution or "unresolved",
            strategies_used=strategies or [],
            outcome_satisfaction=outcome,
            emotional_cost=emotional_cost,
            lessons_learned=lessons or [],
        )

        with self._lock:
            self._conflicts.append(conflict)
            self._stats["total_conflicts"] += 1
            self._update_stats(conflict)

        self._save_stats()
        self._log_conflict(conflict)

        return conflict

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_conflict_patterns(self) -> Dict[str, Any]:
        """Get recurring theme analysis."""
        if not self._conflicts:
            return {"status": "insufficient_data"}

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "avg_intensity": 0.0, "resolution_rate": 0.0})
        for c in self._conflicts:
            by_trigger[c.trigger]["count"] += 1
            by_trigger[c.trigger]["avg_intensity"] += c.intensity
            if c.resolution == "resolved":
                by_trigger[c.trigger]["resolution_rate"] += 1

        trigger_stats = {}
        for t, data in by_trigger.items():
            count = data["count"]
            trigger_stats[t] = {
                "count": count,
                "avg_intensity": round(data["avg_intensity"] / count, 1),
                "resolution_rate": round(data["resolution_rate"] / count, 2),
                "risk": "high" if data["avg_intensity"] / count > 7 else "medium" if data["avg_intensity"] / count > 4 else "low",
            }

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "avg_intensity": 0.0, "emotional_cost": 0.0})
        for c in self._conflicts:
            by_type[c.conflict_type]["count"] += 1
            by_type[c.conflict_type]["avg_intensity"] += c.intensity
            by_type[c.conflict_type]["emotional_cost"] += c.emotional_cost

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["avg_intensity"] / count, 1),
                "avg_emotional_cost": round(data["emotional_cost"] / count, 2),
            }

        # Style analysis
        by_style = defaultdict(int)
        for c in self._conflicts:
            if c.user_style:
                by_style[c.user_style] += 1

        dominant_style = max(by_style.items(), key=lambda x: x[1])[0] if by_style else "unspecified"

        # Escalation detection
        recent = [c for c in self._conflicts if c.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        escalation_trend = sum(c.intensity for c in recent) / max(1, len(recent)) if recent else 0

        return {
            "total_conflicts": len(self._conflicts),
            "trigger_stats": trigger_stats,
            "type_stats": type_stats,
            "dominant_style": dominant_style,
            "escalation_trend": "rising" if escalation_trend > 6 else "stable" if escalation_trend > 3 else "calm",
            "most_common_trigger": max(trigger_stats.items(), key=lambda x: x[1]["count"])[0] if trigger_stats else "",
            "highest_risk_trigger": max(trigger_stats.items(), key=lambda x: x[1]["avg_intensity"])[0] if trigger_stats else "",
        }

    def get_resolution_strategy(self, conflict_type: str = "", intensity: float = 5.0, parties: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get tailored conflict resolution strategy."""
        strategies = {
            "values": {
                "approach": "Find common ground, respect differences",
                "techniques": ["Acknowledge their values", "Find shared values", "Agree to disagree respectfully", "Set boundaries on the topic"],
                "timing": "When emotions have cooled",
                "setting": "Neutral, private space",
            },
            "needs": {
                "approach": "Identify underlying needs, brainstorm solutions",
                "techniques": ["Ask 'What do you need?'", "Share your needs", "Brainstorm options together", "Find creative compromise"],
                "timing": "When both parties have energy",
                "setting": "Comfortable, distraction-free",
            },
            "power": {
                "approach": "Address imbalance directly but respectfully",
                "techniques": ["Name the dynamic", "Focus on behavior not person", "Propose concrete changes", "Seek mediation if needed"],
                "timing": "Prepare first, don't ambush",
                "setting": "With witness/mediator if necessary",
            },
            "misunderstanding": {
                "approach": "Clarify, paraphrase, repair",
                "techniques": ["Paraphrase what you heard", "Ask clarifying questions", "Own your misunderstanding", "Repair with humor if appropriate"],
                "timing": "As soon as noticed",
                "setting": "Anywhere, but privately",
            },
            "external_stress": {
                "approach": "Team up against the stress, not each other",
                "techniques": ["Acknowledge external pressure", "Say 'it's us vs the problem'", "Offer support", "Plan decompression together"],
                "timing": "When stress is acknowledged",
                "setting": "Comfortable, low-pressure",
            },
        }

        base = strategies.get(conflict_type, strategies["misunderstanding"])

        # Intensity adjustments
        if intensity > 7:
            base["urgency"] = "high"
            base["advice"] = "High intensity conflict. Take a break if needed. Don't try to resolve while flooded."
            base["techniques"].insert(0, "Take a 20-minute break")
        elif intensity > 4:
            base["urgency"] = "medium"
            base["advice"] = "Moderate intensity. Stay calm, use I-statements, listen more than you speak."
        else:
            base["urgency"] = "low"
            base["advice"] = "Low intensity. Good time to practice collaborative skills."

        # Party-specific advice
        if parties and len(parties) > 2:
            base["techniques"].append("With multiple parties, use round-robin speaking")

        return base

    def get_relationship_health(self, party: str = "") -> int:
        """Calculate relationship health score (0-100)."""
        if not self._conflicts:
            return 70  # Neutral baseline

        # Filter by party if specified
        conflicts = [c for c in self._conflicts if not party or party in c.parties]
        if not conflicts:
            return 70

        # Resolution rate
        resolved = sum(1 for c in conflicts if c.resolution == "resolved")
        resolution_rate = resolved / len(conflicts)

        # Average emotional cost
        avg_cost = sum(c.emotional_cost for c in conflicts) / len(conflicts)

        # Recency weighting (recent conflicts hurt more)
        recent = [c for c in conflicts if c.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        recent_penalty = len(recent) * 5

        # Calculate score
        base = 70
        resolution_bonus = (resolution_rate - 0.5) * 40
        cost_penalty = avg_cost * 30
        
        score = base + resolution_bonus - cost_penalty - recent_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, conflict: Conflict):
        """Update running statistics."""
        n = self._stats["total_conflicts"]
        self._stats["avg_intensity"] = round((self._stats["avg_intensity"] * (n - 1) + conflict.intensity) / n, 1)
        self._stats["avg_emotional_cost"] = round((self._stats["avg_emotional_cost"] * (n - 1) + conflict.emotional_cost) / n, 2)
        
        resolved = sum(1 for c in self._conflicts if c.resolution == "resolved")
        self._stats["resolution_rate"] = round(resolved / n, 2)

        styles = defaultdict(int)
        for c in self._conflicts:
            if c.user_style:
                styles[c.user_style] += 1
        if styles:
            self._stats["dominant_style"] = max(styles.items(), key=lambda x: x[1])[0]

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

    def _log_conflict(self, conflict: Conflict):
        try:
            with open(CONFLICT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": conflict.timestamp,
                    "trigger": conflict.trigger,
                    "type": conflict.conflict_type,
                    "intensity": conflict.intensity,
                    "resolution": conflict.resolution,
                    "emotional_cost": conflict.emotional_cost,
                    "outcome": conflict.outcome_satisfaction,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_crc_instance: Optional[ConflictResolutionCoach] = None
_crc_lock = threading.Lock()


def get_conflict_resolution_coach() -> ConflictResolutionCoach:
    global _crc_instance
    with _crc_lock:
        if _crc_instance is None:
            _crc_instance = ConflictResolutionCoach()
        return _crc_instance
