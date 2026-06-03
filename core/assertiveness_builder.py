"""
LOVE Assertiveness Builder — Voice Intelligence (Modern AI Pattern)

Most resentment comes from silence. This builder:

1. ASSERTIVENESS TRACKING
   - Record assertive interactions and their characteristics
   - Track assertiveness types (request, refusal, boundary, opinion, need)
   - Log outcomes and their effects on self-respect and relationships

2. PATTERN ANALYSIS
   - Identify the user's assertiveness profile (passive, aggressive, passive-aggressive, assertive)
   - Find assertiveness accelerators (what helps them speak up)
   - Detect assertiveness suppression patterns

3. ASSERTIVENESS BUILDING
   - Suggest assertive communication matched to current situation
   - Provide scripts and frameworks for difficult conversations
   - Recommendation practice opportunities

4. VOICE CULTIVATION
   - Track the correlation between assertiveness and self-respect
   - Alert when needs are being chronically unexpressed
   - Celebrate moments of honest expression

Architecture:
- record_interaction(situation, type, approach, outcome): Log interaction
- get_assertiveness_stats(): Get assertiveness pattern analysis
- get_assertiveness_script(situation, type): Get script
- get_assertiveness_score(): Calculate overall assertiveness health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "assertiveness_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ASSERTIVENESS_LOG = DATA_DIR / "interactions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AssertivenessEntry:
    """A tracked assertiveness entry."""
    entry_id: str = ""
    situation: str = ""  # what was the context
    assertiveness_type: str = ""  # request, refusal, boundary, opinion, need
    approach: str = ""  # direct, diplomatic, delayed, avoided
    anxiety_before: float = 0.5  # 0-1
    self_respect_after: float = 0.5  # 0-1
    relationship_after: float = 0.5  # 0-1
    outcome: str = ""  # positive, neutral, negative, unknown
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AssertivenessBuilder:
    """
    Intelligent assertiveness builder with voice tracking and suppression detection.
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
            "avg_self_respect": 0.0,
            "avg_relationship": 0.0,
            "suppression_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_interaction(self, situation: str = "", assertiveness_type: str = "", approach: str = "", anxiety_before: float = 0.5, self_respect_after: float = 0.5, relationship_after: float = 0.5, outcome: str = "", notes: str = "") -> AssertivenessEntry:
        """Record an assertiveness entry."""
        entry_id = f"assert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = AssertivenessEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            assertiveness_type=assertiveness_type or "request",
            approach=approach or "direct",
            anxiety_before=anxiety_before,
            self_respect_after=self_respect_after,
            relationship_after=relationship_after,
            outcome=outcome or "unknown",
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

    def get_assertiveness_stats(self) -> Dict[str, Any]:
        """Get assertiveness pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "anxiety_sum": 0.0, "respect_sum": 0.0, "rel_sum": 0.0, "positive_count": 0})
        for e in self._entries:
            by_type[e.assertiveness_type]["count"] += 1
            by_type[e.assertiveness_type]["anxiety_sum"] += e.anxiety_before
            by_type[e.assertiveness_type]["respect_sum"] += e.self_respect_after
            by_type[e.assertiveness_type]["rel_sum"] += e.relationship_after
            if e.outcome == "positive":
                by_type[e.assertiveness_type]["positive_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_anxiety": round(data["anxiety_sum"] / count, 2),
                "avg_self_respect": round(data["respect_sum"] / count, 2),
                "avg_relationship": round(data["rel_sum"] / count, 2),
                "positive_rate": round(data["positive_count"] / count, 2),
            }

        # Approach analysis
        by_approach = defaultdict(lambda: {"count": 0, "respect_sum": 0.0, "rel_sum": 0.0})
        for e in self._entries:
            by_approach[e.approach]["count"] += 1
            by_approach[e.approach]["respect_sum"] += e.self_respect_after
            by_approach[e.approach]["rel_sum"] += e.relationship_after

        approach_stats = {}
        for a, data in by_approach.items():
            count = data["count"]
            approach_stats[a] = {
                "count": count,
                "avg_self_respect": round(data["respect_sum"] / count, 2),
                "avg_relationship": round(data["rel_sum"] / count, 2),
            }

        best_approach = max(approach_stats.items(), key=lambda x: x[1]["avg_self_respect"] + x[1]["avg_relationship"]) if approach_stats else ("", {})

        # Anxiety vs outcome
        high_anxiety = [e for e in self._entries if e.anxiety_before > 0.7]
        low_anxiety = [e for e in self._entries if e.anxiety_before < 0.4]
        if high_anxiety and low_anxiety:
            high_anxiety_respect = sum(e.self_respect_after for e in high_anxiety) / len(high_anxiety)
            low_anxiety_respect = sum(e.self_respect_after for e in low_anxiety) / len(low_anxiety)
            high_anxiety_rel = sum(e.relationship_after for e in high_anxiety) / len(high_anxiety)
            low_anxiety_rel = sum(e.relationship_after for e in low_anxiety) / len(low_anxiety)
        else:
            high_anxiety_respect = 0
            low_anxiety_respect = 0
            high_anxiety_rel = 0
            low_anxiety_rel = 0

        # Suppression detection
        avoided = [e for e in self._entries if e.approach == "avoided"]
        if avoided:
            avoided_respect = sum(e.self_respect_after for e in avoided) / len(avoided)
            suppression_risk = avoided_respect < 0.3
        else:
            suppression_risk = False

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_respect = sum(e.self_respect_after for e in recent) / len(recent)
            recent_rel = sum(e.relationship_after for e in recent) / len(recent)
            recent_anxiety = sum(e.anxiety_before for e in recent) / len(recent)
            recent_positive = sum(1 for e in recent if e.outcome == "positive") / len(recent)
        else:
            recent_respect = 0
            recent_rel = 0
            recent_anxiety = 0
            recent_positive = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_respect = sum(e.self_respect_after for e in older) / len(older)
            older_rel = sum(e.relationship_after for e in older) / len(older)
            respect_trend = recent_respect - older_respect
            rel_trend = recent_rel - older_rel
        else:
            respect_trend = 0
            rel_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "approach_stats": approach_stats,
            "best_approach": best_approach[0],
            "anxiety_impact": {
                "high_anxiety_self_respect": round(high_anxiety_respect, 2),
                "low_anxiety_self_respect": round(low_anxiety_respect, 2),
                "high_anxiety_relationship": round(high_anxiety_rel, 2),
                "low_anxiety_relationship": round(low_anxiety_rel, 2),
            },
            "suppression_risk": suppression_risk,
            "avg_self_respect": round(sum(e.self_respect_after for e in self._entries) / len(self._entries), 2),
            "avg_relationship": round(sum(e.relationship_after for e in self._entries) / len(self._entries), 2),
            "avg_anxiety": round(sum(e.anxiety_before for e in self._entries) / len(self._entries), 2),
            "respect_trend": round(respect_trend, 2),
            "relationship_trend": round(rel_trend, 2),
            "recent_anxiety": round(recent_anxiety, 2),
            "recent_positive_rate": round(recent_positive, 2),
        }

    def get_assertiveness_script(self, situation: str = "", assertiveness_type: str = "") -> Dict[str, Any]:
        """Get script."""
        scripts = {
            "request": [
                "I need [specific thing]. It would help me because [reason]. Would that be possible?",
                "I'm struggling with [situation]. Could you [specific request]? I'd really appreciate it.",
                "I want to ask for [thing]. I know it's a lot, and I understand if you can't. But I need to ask.",
            ],
            "refusal": [
                "I can't do that. Not because I don't care, but because [reason]. I hope you understand.",
                "No. I'm not available for that. [Optional: I can do this instead].",
                "I need to say no to this. It's not right for me right now. Thank you for asking.",
            ],
            "boundary": [
                "I need to set a boundary here. [Specific boundary]. This is about protecting my energy, not about you.",
                "When you [behavior], I feel [feeling]. I need [specific change]. Can we agree on that?",
                "I'm not comfortable with [thing]. I need you to stop. If it continues, I will [consequence].",
            ],
            "opinion": [
                "I see it differently. My view is [opinion]. I understand you may disagree, and that's okay.",
                "I respect your perspective, and I have a different one. Here's what I think: [opinion]",
                "I disagree. Not to argue, but because I think [opinion]. Let's find the best answer together.",
            ],
            "need": [
                "I need [need]. Not want. Need. And I need to express it because it's not being met.",
                "I've been quiet about this, but I need [need]. Pretending I don't is hurting both of us.",
                "This is hard for me to say, but I need [need]. Can we talk about how to make that happen?",
            ],
            "general": [
                "Your needs are valid. Your voice matters. Speak as if both are true. Because they are.",
                "Assertiveness is not aggression. It's honesty with respect. You can be kind and clear.",
                "The people who matter won't mind. The people who mind don't matter. Speak your truth.",
            ],
        }

        selected = scripts.get(assertiveness_type, scripts["general"])

        if assertiveness_type == "request":
            type_note = "Requests are not burdens. They're invitations for others to care for you. Make them specific."
        elif assertiveness_type == "refusal":
            type_note = "No is a complete sentence. You don't owe explanations. But if you give one, make it honest."
        elif assertiveness_type == "boundary":
            type_note = "Boundaries are not walls. They're fences with gates. You control the gate."
        elif assertiveness_type == "opinion":
            type_note = "Your perspective is unique. That's why it's valuable. Share it."
        elif assertiveness_type == "need":
            type_note = "Needs are not weaknesses. They're the foundation of healthy relationships."
        else:
            type_note = "Assertiveness is a muscle. The more you use it, the stronger it gets."

        return {
            "situation": situation or "general",
            "assertiveness_type": assertiveness_type or "general",
            "script": random.choice(selected),
            "type_note": type_note,
            "principle": "Most people are not assertive because they confuse it with aggression. Assertiveness is honesty with respect. It's saying what you need, what you think, and what you feel — without attacking, blaming, or demanding. It's the middle path between silence and shouting.",
        }

    def get_assertiveness_score(self) -> int:
        """Calculate overall assertiveness health (0-100)."""
        if not self._entries:
            return 30

        # Self-respect and relationship maintenance
        avg_respect = sum(e.self_respect_after for e in self._entries) / len(self._entries)
        avg_rel = sum(e.relationship_after for e in self._entries) / len(self._entries)

        # Low anxiety or anxiety managed well
        avg_anxiety = sum(e.anxiety_before for e in self._entries) / len(self._entries)

        # Positive outcome rate
        positive = sum(1 for e in self._entries if e.outcome == "positive")
        positive_rate = positive / len(self._entries)

        # Approach variety
        unique_approaches = len(set(e.approach for e in self._entries))

        # Type variety
        unique_types = len(set(e.assertiveness_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_respect = sum(e.self_respect_after for e in recent) / len(recent)
            recent_rel = sum(e.relationship_after for e in recent) / len(recent)
            recent_positive = sum(1 for e in recent if e.outcome == "positive") / len(recent)
        else:
            recent_respect = 0
            recent_rel = 0
            recent_positive = 0

        # Suppression penalty
        avoided = [e for e in self._entries if e.approach == "avoided"]
        if avoided:
            avoided_respect = sum(e.self_respect_after for e in avoided) / len(avoided)
            suppression_penalty = 15 if avoided_respect < 0.3 else 0
        else:
            suppression_penalty = 0

        score = (avg_respect * 25) + (avg_rel * 20) + ((1 - avg_anxiety) * 10) + (positive_rate * 15) + (unique_approaches * 2) + (unique_types * 2) + (recent_respect * 10) + (recent_rel * 10) + (recent_positive * 5) - suppression_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_self_respect"] = round(sum(e.self_respect_after for e in self._entries) / len(self._entries), 2)
            self._stats["avg_relationship"] = round(sum(e.relationship_after for e in self._entries) / len(self._entries), 2)

            avoided = [e for e in self._entries if e.approach == "avoided"]
            if avoided:
                avoided_respect = sum(e.self_respect_after for e in avoided) / len(avoided)
                self._stats["suppression_risk"] = avoided_respect < 0.3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.assertiveness_builder")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.assertiveness_builder")

    def _log_entry(self, entry: AssertivenessEntry):
        try:
            with open(ASSERTIVENESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "assertiveness_type": entry.assertiveness_type,
                    "approach": entry.approach,
                    "anxiety_before": entry.anxiety_before,
                    "self_respect_after": entry.self_respect_after,
                    "relationship_after": entry.relationship_after,
                    "outcome": entry.outcome,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.assertiveness_builder")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ab_instance: Optional[AssertivenessBuilder] = None
_ab_lock = threading.Lock()


def get_assertiveness_builder() -> AssertivenessBuilder:
    global _ab_instance
    with _ab_lock:
        if _ab_instance is None:
            _ab_instance = AssertivenessBuilder()
        return _ab_instance
