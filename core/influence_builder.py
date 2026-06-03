"""
LOVE Influence Builder — Persuasion Intelligence (Modern AI Pattern)

Most influence fails because it's transactional, not relational. This builder:

1. INFLUENCE TRACKING
   - Record influence attempts and their characteristics
   - Track influence types (rational, emotional, social proof, authority, reciprocity)
   - Log persuasion outcomes and their durability

2. PATTERN ANALYSIS
   - Identify the user's influence profile (coercive, convincing, inspiring, collaborative)
   - Find influence approaches that create lasting commitment
   - Detect manipulation vs genuine influence patterns

3. INFLUENCE BUILDING
   - Suggest influence strategies matched to audience and goal
   - Provide framing and storytelling frameworks
   - Recommendation trust-building practices

4. PERSUASION CULTIVATION
   - Track the correlation between influence approach and outcome
   - Alert when influence is becoming manipulative
   - Celebrate moments of ethical persuasion

Architecture:
- record_attempt(audience, goal, approach, outcome): Log attempt
- get_influence_stats(): Get influence pattern analysis
- get_influence_strategy(audience, goal, context): Get strategy
- get_influence_score(): Calculate overall influence health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "influence_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INFLUENCE_LOG = DATA_DIR / "attempts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class InfluenceEntry:
    """A tracked influence entry."""
    entry_id: str = ""
    audience: str = ""  # who was influenced
    goal: str = ""  # what was the goal
    influence_type: str = ""  # rational, emotional, social_proof, authority, reciprocity
    approach: str = ""  # collaborative, convincing, inspiring, coercive
    trust_before: float = 0.5  # 0-1
    commitment: float = 0.5  # 0-1, how committed were they
    durability: float = 0.5  # 0-1, did the commitment last
    ethical: bool = True  # was it ethical
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class InfluenceBuilder:
    """
    Intelligent influence builder with persuasion tracking and ethics detection.
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
            "avg_commitment": 0.0,
            "avg_durability": 0.0,
            "manipulation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_attempt(self, audience: str = "", goal: str = "", influence_type: str = "", approach: str = "", trust_before: float = 0.5, commitment: float = 0.5, durability: float = 0.5, ethical: bool = True, notes: str = "") -> InfluenceEntry:
        """Record an influence entry."""
        entry_id = f"inf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = InfluenceEntry(
            entry_id=entry_id,
            audience=audience or "unspecified",
            goal=goal or "general",
            influence_type=influence_type or "rational",
            approach=approach or "collaborative",
            trust_before=trust_before,
            commitment=commitment,
            durability=durability,
            ethical=ethical,
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

    def get_influence_stats(self) -> Dict[str, Any]:
        """Get influence pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "commit_sum": 0.0, "dur_sum": 0.0, "trust_sum": 0.0, "ethical_count": 0})
        for e in self._entries:
            by_type[e.influence_type]["count"] += 1
            by_type[e.influence_type]["commit_sum"] += e.commitment
            by_type[e.influence_type]["dur_sum"] += e.durability
            by_type[e.influence_type]["trust_sum"] += e.trust_before
            if e.ethical:
                by_type[e.influence_type]["ethical_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_commitment": round(data["commit_sum"] / count, 2),
                "avg_durability": round(data["dur_sum"] / count, 2),
                "avg_trust": round(data["trust_sum"] / count, 2),
                "ethical_rate": round(data["ethical_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_durability"] + x[1]["avg_commitment"]) if type_stats else ("", {})

        # Approach analysis
        by_approach = defaultdict(lambda: {"count": 0, "commit_sum": 0.0, "dur_sum": 0.0, "ethical_count": 0})
        for e in self._entries:
            by_approach[e.approach]["count"] += 1
            by_approach[e.approach]["commit_sum"] += e.commitment
            by_approach[e.approach]["dur_sum"] += e.durability
            if e.ethical:
                by_approach[e.approach]["ethical_count"] += 1

        approach_stats = {}
        for a, data in by_approach.items():
            count = data["count"]
            approach_stats[a] = {
                "count": count,
                "avg_commitment": round(data["commit_sum"] / count, 2),
                "avg_durability": round(data["dur_sum"] / count, 2),
                "ethical_rate": round(data["ethical_count"] / count, 2),
            }

        best_approach = max(approach_stats.items(), key=lambda x: x[1]["avg_durability"]) if approach_stats else ("", {})

        # Trust vs outcome
        high_trust = [e for e in self._entries if e.trust_before > 0.7]
        low_trust = [e for e in self._entries if e.trust_before < 0.4]
        if high_trust and low_trust:
            high_trust_commit = sum(e.commitment for e in high_trust) / len(high_trust)
            low_trust_commit = sum(e.commitment for e in low_trust) / len(low_trust)
            high_trust_dur = sum(e.durability for e in high_trust) / len(high_trust)
            low_trust_dur = sum(e.durability for e in low_trust) / len(low_trust)
        else:
            high_trust_commit = 0
            low_trust_commit = 0
            high_trust_dur = 0
            low_trust_dur = 0

        # Manipulation detection
        coercive = [e for e in self._entries if e.approach == "coercive"]
        if coercive:
            coercive_dur = sum(e.durability for e in coercive) / len(coercive)
            coercive_ethical = sum(1 for e in coercive if e.ethical) / len(coercive)
            manipulation_risk = coercive_dur < 0.3 or coercive_ethical < 0.5
        else:
            manipulation_risk = False

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_commit = sum(e.commitment for e in recent) / len(recent)
            recent_dur = sum(e.durability for e in recent) / len(recent)
            recent_ethical = sum(1 for e in recent if e.ethical) / len(recent)
        else:
            recent_commit = 0
            recent_dur = 0
            recent_ethical = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_commit = sum(e.commitment for e in older) / len(older)
            older_dur = sum(e.durability for e in older) / len(older)
            commit_trend = recent_commit - older_commit
            dur_trend = recent_dur - older_dur
        else:
            commit_trend = 0
            dur_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_influence_type": best_type[0],
            "approach_stats": approach_stats,
            "best_approach": best_approach[0],
            "trust_impact": {
                "high_trust_commitment": round(high_trust_commit, 2),
                "low_trust_commitment": round(low_trust_commit, 2),
                "high_trust_durability": round(high_trust_dur, 2),
                "low_trust_durability": round(low_trust_dur, 2),
            },
            "manipulation_risk": manipulation_risk,
            "avg_commitment": round(sum(e.commitment for e in self._entries) / len(self._entries), 2),
            "avg_durability": round(sum(e.durability for e in self._entries) / len(self._entries), 2),
            "commitment_trend": round(commit_trend, 2),
            "durability_trend": round(dur_trend, 2),
            "recent_ethical_rate": round(recent_ethical, 2),
        }

    def get_influence_strategy(self, audience: str = "", goal: str = "", context: str = "") -> Dict[str, Any]:
        """Get strategy."""
        strategies = {
            "rational": [
                "Show the data. But don't bury them in it. Three compelling facts. No more.",
                "Find the shared logic. What do you both agree on? Start there. Build from consensus.",
                "Anticipate objections. Address them before they're raised. Preparation is persuasion.",
            ],
            "emotional": [
                "Tell a story. Facts convince. Stories move. People act on emotion, justify with logic.",
                "Connect to their values. What do they care about? Show how this serves that.",
                "Use contrast. Show the gap between what is and what could be. Make it visceral.",
            ],
            "social_proof": [
                "Show who else is doing it. Especially people they respect. We are social creatures.",
                "Use testimonials. Real voices. Specific results. Vague praise is useless.",
                "Create scarcity. Not manipulation. Honest scarcity. 'This opportunity closes Friday.'",
            ],
            "authority": [
                "Establish credibility first. Then make your case. Order matters.",
                "Admit a weakness. It makes everything else more believable. 'This isn't perfect, but...'",
                "Use precise numbers. 43.7% is more credible than 'about half.'",
            ],
            "reciprocity": [
                "Give first. Genuine value. No strings. Reciprocity is human nature.",
                "Make a concession. They'll feel obligated to make one back.",
                "Offer a small favor. It creates a debt. Use it wisely and ethically.",
            ],
            "general": [
                "Influence is not about getting your way. It's about finding mutual benefit and making it visible.",
                "Listen first. Influence starts with understanding. You can't persuade someone you don't understand.",
                "The best influence is invisible. They feel like it was their idea. That's the highest form.",
            ],
        }

        selected = strategies.get(context, strategies["general"])

        return {
            "audience": audience or "general",
            "goal": goal or "general",
            "context": context or "general",
            "strategy": random.choice(selected),
            "principle": "Most people think influence is about talking. It's not. It's about listening, understanding, and framing. The most influential people are the most curious. They ask questions until they understand the other person's world. Then they connect their goal to that world. That's not manipulation. That's translation.",
        }

    def get_influence_score(self) -> int:
        """Calculate overall influence health (0-100)."""
        if not self._entries:
            return 35

        # Commitment and durability
        avg_commit = sum(e.commitment for e in self._entries) / len(self._entries)
        avg_dur = sum(e.durability for e in self._entries) / len(self._entries)

        # Ethical rate
        ethical = sum(1 for e in self._entries if e.ethical)
        ethical_rate = ethical / len(self._entries)

        # Trust building
        avg_trust = sum(e.trust_before for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.influence_type for e in self._entries))

        # Approach variety
        unique_approaches = len(set(e.approach for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_commit = sum(e.commitment for e in recent) / len(recent)
            recent_dur = sum(e.durability for e in recent) / len(recent)
            recent_ethical = sum(1 for e in recent if e.ethical) / len(recent)
        else:
            recent_commit = 0
            recent_dur = 0
            recent_ethical = 0

        # Coercive penalty
        coercive = [e for e in self._entries if e.approach == "coercive"]
        if coercive:
            coercive_dur = sum(e.durability for e in coercive) / len(coercive)
            coercive_penalty = 15 if coercive_dur < 0.3 else 0
        else:
            coercive_penalty = 0

        score = (avg_commit * 25) + (avg_dur * 25) + (ethical_rate * 15) + (avg_trust * 10) + (unique_types * 2) + (unique_approaches * 2) + (recent_commit * 10) + (recent_dur * 10) + (recent_ethical * 5) - coercive_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_commitment"] = round(sum(e.commitment for e in self._entries) / len(self._entries), 2)
            self._stats["avg_durability"] = round(sum(e.durability for e in self._entries) / len(self._entries), 2)

            coercive = [e for e in self._entries if e.approach == "coercive"]
            if coercive:
                coercive_dur = sum(e.durability for e in coercive) / len(coercive)
                coercive_ethical = sum(1 for e in coercive if e.ethical) / len(coercive)
                self._stats["manipulation_risk"] = coercive_dur < 0.3 or coercive_ethical < 0.5

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.influence_builder")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.influence_builder")

    def _log_entry(self, entry: InfluenceEntry):
        try:
            with open(INFLUENCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "audience": entry.audience,
                    "goal": entry.goal,
                    "influence_type": entry.influence_type,
                    "approach": entry.approach,
                    "trust_before": entry.trust_before,
                    "commitment": entry.commitment,
                    "durability": entry.durability,
                    "ethical": entry.ethical,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.influence_builder")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ib_instance: Optional[InfluenceBuilder] = None
_ib_lock = threading.Lock()


def get_influence_builder() -> InfluenceBuilder:
    global _ib_instance
    with _ib_lock:
        if _ib_instance is None:
            _ib_instance = InfluenceBuilder()
        return _ib_instance
