"""
LOVE Conflict Navigator — Resolution Intelligence (Modern AI Pattern)

Most conflicts escalate because navigation fails early. This navigator:

1. CONFLICT TRACKING
   - Record conflicts and their characteristics
   - Track conflict types (values, resource, power, information, emotional)
   - Log resolution outcomes and their durability

2. PATTERN ANALYSIS
   - Identify the user's conflict profile (avoider, seeker, resolver, escalator)
   - Find resolution strategies that create lasting peace
   - Detect conflict avoidance costs

3. NAVIGATION BUILDING
   - Suggest resolution strategies matched to conflict type and intensity
   - Provide de-escalation frameworks
   - Recommendation repair and reconciliation practices

4. PEACE CULTIVATION
   - Track the correlation between resolution approach and outcome
   - Alert when conflicts are being suppressed rather than resolved
   - Celebrate successful navigation

Architecture:
- record_conflict(party, type, intensity, strategy, outcome): Log conflict
- get_conflict_stats(): Get conflict pattern analysis
- get_resolution_strategy(conflict_type, intensity): Get strategy
- get_conflict_score(): Calculate overall conflict health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "conflict_navigator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFLICT_LOG = DATA_DIR / "conflicts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ConflictEntry:
    """A tracked conflict entry."""
    entry_id: str = ""
    party: str = ""  # who was involved
    conflict_type: str = ""  # values, resource, power, information, emotional
    intensity: float = 0.5  # 0-1
    strategy: str = ""  # compromise, collaboration, accommodation, avoidance, competition
    de_escalation: float = 0.5  # 0-1, how well de-escalation worked
    outcome: str = ""  # resolved, improved, stale, escalated
    durability: float = 0.5  # 0-1
    lessons: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ConflictNavigator:
    """
    Intelligent conflict navigator with de-escalation training and resolution strategy matching.
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
            "avg_durability": 0.0,
            "avg_de_escalation": 0.0,
            "avoidance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_conflict(self, party: str = "", conflict_type: str = "", intensity: float = 0.5, strategy: str = "", de_escalation: float = 0.5, outcome: str = "", durability: float = 0.5, lessons: str = "") -> ConflictEntry:
        """Record a conflict entry."""
        entry_id = f"conf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ConflictEntry(
            entry_id=entry_id,
            party=party or "unspecified",
            conflict_type=conflict_type or "values",
            intensity=intensity,
            strategy=strategy or "compromise",
            de_escalation=de_escalation,
            outcome=outcome or "stale",
            durability=durability,
            lessons=lessons,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_stats()

        self._save_stats()
        self._log_entry(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get conflict pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "de_esc_sum": 0.0, "dur_sum": 0.0})
        for e in self._entries:
            by_type[e.conflict_type]["count"] += 1
            by_type[e.conflict_type]["intensity_sum"] += e.intensity
            by_type[e.conflict_type]["de_esc_sum"] += e.de_escalation
            by_type[e.conflict_type]["dur_sum"] += e.durability

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_de_escalation": round(data["de_esc_sum"] / count, 2),
                "avg_durability": round(data["dur_sum"] / count, 2),
            }

        # Strategy analysis
        by_strategy = defaultdict(lambda: {"count": 0, "de_esc_sum": 0.0, "dur_sum": 0.0, "outcome_resolved": 0})
        for e in self._entries:
            by_strategy[e.strategy]["count"] += 1
            by_strategy[e.strategy]["de_esc_sum"] += e.de_escalation
            by_strategy[e.strategy]["dur_sum"] += e.durability
            if e.outcome in ["resolved", "improved"]:
                by_strategy[e.strategy]["outcome_resolved"] += 1

        strategy_stats = {}
        for s, data in by_strategy.items():
            count = data["count"]
            strategy_stats[s] = {
                "count": count,
                "avg_de_escalation": round(data["de_esc_sum"] / count, 2),
                "avg_durability": round(data["dur_sum"] / count, 2),
                "success_rate": round(data["outcome_resolved"] / count, 2),
            }

        best_strategy = max(strategy_stats.items(), key=lambda x: x[1]["success_rate"] + x[1]["avg_durability"]) if strategy_stats else ("", {})

        # Outcome analysis
        by_outcome = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for e in self._entries:
            by_outcome[e.outcome]["count"] += 1
            by_outcome[e.outcome]["intensity_sum"] += e.intensity

        outcome_stats = {}
        for o, data in by_outcome.items():
            count = data["count"]
            outcome_stats[o] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
            }

        # Avoidance detection
        avoidance = [e for e in self._entries if e.strategy == "avoidance"]
        if avoidance:
            avoidance_durability = sum(e.durability for e in avoidance) / len(avoidance)
            avoidance_escalated = sum(1 for e in avoidance if e.outcome == "escalated")
            avoidance_risk = avoidance_durability < 0.3 or avoidance_escalated / len(avoidance) > 0.3
        else:
            avoidance_risk = False

        # De-escalation analysis
        high_de_esc = [e for e in self._entries if e.de_escalation > 0.7]
        low_de_esc = [e for e in self._entries if e.de_escalation < 0.4]
        if high_de_esc and low_de_esc:
            high_de_esc_dur = sum(e.durability for e in high_de_esc) / len(high_de_esc)
            low_de_esc_dur = sum(e.durability for e in low_de_esc) / len(low_de_esc)
        else:
            high_de_esc_dur = 0
            low_de_esc_dur = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_de_esc = sum(e.de_escalation for e in recent) / len(recent)
            recent_dur = sum(e.durability for e in recent) / len(recent)
            recent_int = sum(e.intensity for e in recent) / len(recent)
        else:
            recent_de_esc = 0
            recent_dur = 0
            recent_int = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_de_esc = sum(e.de_escalation for e in older) / len(older)
            older_dur = sum(e.durability for e in older) / len(older)
            de_esc_trend = recent_de_esc - older_de_esc
            dur_trend = recent_dur - older_dur
        else:
            de_esc_trend = 0
            dur_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "strategy_stats": strategy_stats,
            "best_strategy": best_strategy[0],
            "outcome_stats": outcome_stats,
            "avoidance_risk": avoidance_risk,
            "de_escalation_impact": {
                "high_de_escalation_durability": round(high_de_esc_dur, 2),
                "low_de_escalation_durability": round(low_de_esc_dur, 2),
            },
            "avg_de_escalation": round(sum(e.de_escalation for e in self._entries) / len(self._entries), 2),
            "avg_durability": round(sum(e.durability for e in self._entries) / len(self._entries), 2),
            "avg_intensity": round(sum(e.intensity for e in self._entries) / len(self._entries), 2),
            "de_escalation_trend": round(de_esc_trend, 2),
            "durability_trend": round(dur_trend, 2),
            "recent_intensity": round(recent_int, 2),
        }

    def get_resolution_strategy(self, conflict_type: str = "", intensity: float = 0.5) -> Dict[str, Any]:
        """Get strategy."""
        strategies = {
            "values": [
                "Values conflicts can't be 'won.' They can only be understood. Ask: 'What value is driving your position?'",
                "Find the shared value beneath the disagreement. Almost every values conflict has one.",
                "Agree to disagree on implementation. Align on principle. The how can vary.",
            ],
            "resource": [
                "Expand the pie before dividing it. What resources are undiscovered?",
                "Prioritize by impact, not by equality. Who needs this more?",
                "Trade across time. You get this now, I get that later.",
            ],
            "power": [
                "Power conflicts are often fear in disguise. What are they afraid of losing?",
                "Offer autonomy. People fight for control. Give it where you can.",
                "Document everything. Power conflicts need transparency to resolve fairly.",
            ],
            "information": [
                "Information conflicts are the easiest. Share data. Verify sources. Done.",
                "Admit when you're wrong first. It creates permission for them to do the same.",
                "Bring in a third party. Fresh eyes see what entrenched minds miss.",
            ],
            "emotional": [
                "Emotional conflicts need cooling first. 24 hours. Minimum.",
                "Name the emotion, not the behavior. 'You seem frustrated' not 'You're being difficult.'",
                "Apologize for the impact, not the intention. 'I'm sorry that hurt you.'",
            ],
            "general": [
                "Most conflicts are 10% disagreement and 90% tone. Fix the tone first.",
                "Ask what they need. Not what they want. Needs are deeper and more negotiable.",
                "Conflict is not the enemy. Unresolved conflict is. Address it early.",
            ],
        }

        selected = strategies.get(conflict_type, strategies["general"])

        if intensity > 0.7:
            intensity_note = "High intensity. De-escalate first. Nothing productive happens at this temperature."
        elif intensity > 0.4:
            intensity_note = "Moderate intensity. You can work with this. Focus on interests, not positions."
        else:
            intensity_note = "Low intensity. Address it now before it grows. Small conflicts are cheap. Large ones are expensive."

        return {
            "conflict_type": conflict_type or "general",
            "intensity": intensity,
            "strategy": random.choice(selected),
            "intensity_note": intensity_note,
            "principle": "Conflict is information. It tells you where boundaries are, where values differ, where needs are unmet. The goal is not to eliminate conflict. It's to navigate it skillfully. Every resolved conflict makes the relationship stronger. Every avoided conflict makes it weaker.",
        }

    def get_conflict_score(self) -> int:
        """Calculate overall conflict health (0-100)."""
        if not self._entries:
            return 40

        # De-escalation and durability
        avg_de_esc = sum(e.de_escalation for e in self._entries) / len(self._entries)
        avg_dur = sum(e.durability for e in self._entries) / len(self._entries)

        # Resolution rate
        resolved = sum(1 for e in self._entries if e.outcome in ["resolved", "improved"])
        resolution_rate = resolved / len(self._entries)

        # Low intensity or well-managed
        avg_int = sum(e.intensity for e in self._entries) / len(self._entries)

        # Strategy variety
        unique_strategies = len(set(e.strategy for e in self._entries))

        # Avoidance penalty
        avoidance = [e for e in self._entries if e.strategy == "avoidance"]
        if avoidance:
            avoidance_dur = sum(e.durability for e in avoidance) / len(avoidance)
            avoidance_penalty = 10 if avoidance_dur < 0.3 else 0
        else:
            avoidance_penalty = 0

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_de_esc = sum(e.de_escalation for e in recent) / len(recent)
            recent_dur = sum(e.durability for e in recent) / len(recent)
            recent_resolved = sum(1 for e in recent if e.outcome in ["resolved", "improved"]) / len(recent)
        else:
            recent_de_esc = 0
            recent_dur = 0
            recent_resolved = 0

        score = (avg_de_esc * 25) + (avg_dur * 25) + (resolution_rate * 20) + ((1 - avg_int) * 10) + (unique_strategies * 2) + (recent_de_esc * 10) + (recent_dur * 10) + (recent_resolved * 5) - avoidance_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_durability"] = round(sum(e.durability for e in self._entries) / len(self._entries), 2)
            self._stats["avg_de_escalation"] = round(sum(e.de_escalation for e in self._entries) / len(self._entries), 2)

            avoidance = [e for e in self._entries if e.strategy == "avoidance"]
            if avoidance:
                avoidance_dur = sum(e.durability for e in avoidance) / len(avoidance)
                avoidance_esc = sum(1 for e in avoidance if e.outcome == "escalated")
                self._stats["avoidance_risk"] = avoidance_dur < 0.3 or avoidance_esc / len(avoidance) > 0.3

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

    def _log_entry(self, entry: ConflictEntry):
        try:
            with open(CONFLICT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "party": entry.party,
                    "conflict_type": entry.conflict_type,
                    "intensity": entry.intensity,
                    "strategy": entry.strategy,
                    "de_escalation": entry.de_escalation,
                    "outcome": entry.outcome,
                    "durability": entry.durability,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cn_instance: Optional[ConflictNavigator] = None
_cn_lock = threading.Lock()


def get_conflict_navigator() -> ConflictNavigator:
    global _cn_instance
    with _cn_lock:
        if _cn_instance is None:
            _cn_instance = ConflictNavigator()
        return _cn_instance
