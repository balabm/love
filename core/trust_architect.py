"""
LOVE Trust Architect — Reliability Intelligence (Modern AI Pattern)

Most trust is broken by inconsistency, not malice. This architect:

1. TRUST TRACKING
   - Record trust-building actions and their characteristics
   - Track trust types (competence, character, care, consistency)
   - Log trust outcomes and their effects on relationships

2. PATTERN ANALYSIS
   - Identify the user's trust profile (builder, eroder, repairer, guardian)
   - Find trust accelerators (what reliably builds trust)
   - Detect trust erosion patterns

3. TRUST BUILDING
   - Suggest trust-building actions matched to current deficits
   - Provide reliability exercises
   - Recommendation transparency practices

4. RELIABILITY CULTIVATION
   - Track the correlation between consistency and trust
   - Alert when commitments are being broken
   - Celebrate trust-building moments

Architecture:
- record_action(action, trust_type, relationship, outcome): Log action
- get_trust_stats(): Get trust pattern analysis
- get_trust_action(deficit, relationship): Get action
- get_trust_score(): Calculate overall trust health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "trust_architect"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRUST_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class TrustAction:
    """A tracked trust action."""
    action_id: str = ""
    action: str = ""
    trust_type: str = ""  # competence, character, care, consistency
    relationship: str = ""
    commitment_made: str = ""
    commitment_kept: bool = True
    transparency: float = 0.5  # 0-1
    trust_before: float = 0.5  # 0-1
    trust_after: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class TrustArchitect:
    """
    Intelligent trust architect with reliability tracking and deficit detection.
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
        self._actions: deque = deque(maxlen=300)
        self._stats = {
            "total_actions": 0,
            "avg_trust_change": 0.0,
            "commitment_rate": 0.0,
            "erosion_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", trust_type: str = "", relationship: str = "", commitment_made: str = "", commitment_kept: bool = True, transparency: float = 0.5, trust_before: float = 0.5, trust_after: float = 0.5, notes: str = "") -> TrustAction:
        """Record a trust action."""
        action_id = f"trust_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._actions)}"
        entry = TrustAction(
            action_id=action_id,
            action=action or "unspecified",
            trust_type=trust_type or "consistency",
            relationship=relationship,
            commitment_made=commitment_made,
            commitment_kept=commitment_kept,
            transparency=transparency,
            trust_before=trust_before,
            trust_after=trust_after,
            notes=notes,
        )

        with self._lock:
            self._actions.append(entry)
            self._stats["total_actions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_action(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_trust_stats(self) -> Dict[str, Any]:
        """Get trust pattern analysis."""
        if not self._actions:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "trust_change_sum": 0.0, "transparency_sum": 0.0, "kept_count": 0})
        for a in self._actions:
            by_type[a.trust_type]["count"] += 1
            by_type[a.trust_type]["trust_change_sum"] += a.trust_after - a.trust_before
            by_type[a.trust_type]["transparency_sum"] += a.transparency
            if a.commitment_kept:
                by_type[a.trust_type]["kept_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_trust_change": round(data["trust_change_sum"] / count, 2),
                "avg_transparency": round(data["transparency_sum"] / count, 2),
                "commitment_rate": round(data["kept_count"] / count, 2),
            }

        # Relationship analysis
        by_rel = defaultdict(lambda: {"count": 0, "trust_change_sum": 0.0, "kept_count": 0, "transparency_sum": 0.0})
        for a in self._actions:
            if a.relationship:
                by_rel[a.relationship]["count"] += 1
                by_rel[a.relationship]["trust_change_sum"] += a.trust_after - a.trust_before
                if a.commitment_kept:
                    by_rel[a.relationship]["kept_count"] += 1
                by_rel[a.relationship]["transparency_sum"] += a.transparency

        rel_stats = {}
        for r, data in by_rel.items():
            count = data["count"]
            if count >= 2:
                rel_stats[r] = {
                    "count": count,
                    "avg_trust_change": round(data["trust_change_sum"] / count, 2),
                    "commitment_rate": round(data["kept_count"] / count, 2),
                    "avg_transparency": round(data["transparency_sum"] / count, 2),
                }

        strongest_rel = max(rel_stats.items(), key=lambda x: x[1]["avg_trust_change"]) if rel_stats else ("", {})
        weakest_rel = min(rel_stats.items(), key=lambda x: x[1]["avg_trust_change"]) if rel_stats else ("", {})

        # Commitment analysis
        commitments = [a for a in self._actions if a.commitment_made]
        if commitments:
            kept = sum(1 for a in commitments if a.commitment_kept)
            commitment_rate = kept / len(commitments)
        else:
            commitment_rate = 0

        # Transparency analysis
        high_transparency = [a for a in self._actions if a.transparency > 0.7]
        low_transparency = [a for a in self._actions if a.transparency <= 0.4]
        if high_transparency and low_transparency:
            high_trans_change = sum(a.trust_after - a.trust_before for a in high_transparency) / len(high_transparency)
            low_trans_change = sum(a.trust_after - a.trust_before for a in low_transparency) / len(low_transparency)
        else:
            high_trans_change = 0
            low_trans_change = 0

        # Erosion detection
        recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_trust_change = sum(a.trust_after - a.trust_before for a in recent) / len(recent)
            recent_commitment = sum(1 for a in recent if a.commitment_kept) / len(recent)
            erosion_risk = recent_trust_change < -0.1 or recent_commitment < 0.6
        else:
            erosion_risk = False

        # Recent trend
        if recent:
            recent_transparency = sum(a.transparency for a in recent) / len(recent)
        else:
            recent_transparency = 0

        older = list(self._actions)[:-14] if len(self._actions) > 14 else []
        if older:
            older_trust_change = sum(a.trust_after - a.trust_before for a in older) / len(older)
            older_commitment = sum(1 for a in older if a.commitment_kept) / len(older)
            trust_trend = recent_trust_change - older_trust_change if recent else 0
            commitment_trend = recent_commitment - older_commitment if recent else 0
        else:
            trust_trend = 0
            commitment_trend = 0

        return {
            "total_actions": len(self._actions),
            "type_stats": type_stats,
            "relationship_stats": rel_stats,
            "strongest_relationship": strongest_rel[0],
            "weakest_relationship": weakest_rel[0],
            "commitment_rate": round(commitment_rate, 2),
            "transparency_analysis": {
                "high_transparency_trust_change": round(high_trans_change, 2),
                "low_transparency_trust_change": round(low_trans_change, 2),
            },
            "erosion_risk": erosion_risk,
            "avg_trust_change": round(sum(a.trust_after - a.trust_before for a in self._actions) / len(self._actions), 2),
            "avg_transparency": round(sum(a.transparency for a in self._actions) / len(self._actions), 2),
            "trust_trend": round(trust_trend, 2),
            "commitment_trend": round(commitment_trend, 2),
            "recent_transparency": round(recent_transparency, 2),
        }

    def get_trust_action(self, deficit: str = "", relationship: str = "") -> Dict[str, Any]:
        """Get action."""
        actions = {
            "competence": [
                "Deliver one thing early. Under-promise, over-deliver. Every time.",
                "Admit when you don't know. Then find out. Competence includes knowing limits.",
                "Document your process. Transparency about capability builds more trust than capability alone.",
            ],
            "character": [
                "Do the right thing when no one is watching. Character is what you do in the dark.",
                "Admit a mistake before it's discovered. Proactive honesty is the highest form of character.",
                "Keep a confidence. Even when tempted. Especially when tempted.",
            ],
            "care": [
                "Remember one detail they mentioned. Ask about it later. Care is attention.",
                "Show up when it's hard. Not just when it's easy. Presence is proof of care.",
                "Do one thing that's not required. The extra mile is where trust is built.",
            ],
            "consistency": [
                "Keep one small commitment perfectly. Reliability in small things creates trust in big things.",
                "Communicate when plans change. Surprises erode trust. Updates preserve it.",
                "Be the same person in every context. Consistency is authenticity over time.",
            ],
            "general": [
                "Trust is built in drops and lost in buckets. Add drops daily.",
                "Ask: 'What would make me more trustworthy?' Then do that.",
                "Trust is the residue of kept promises. Make fewer, keep more.",
            ],
        }

        selected = actions.get(deficit, actions["general"])

        if deficit == "competence":
            deficit_note = "Competence trust is about capability. Show, don't tell. Deliver consistently."
        elif deficit == "character":
            deficit_note = "Character trust is about values. Integrity when it's costly. That's what counts."
        elif deficit == "care":
            deficit_note = "Care trust is about attention. People need to feel seen. Show them they are."
        elif deficit == "consistency":
            deficit_note = "Consistency trust is about reliability. Be predictable in what matters.",
        else:
            deficit_note = "Trust is the foundation of everything. Invest in it daily."

        return {
            "deficit": deficit or "general",
            "relationship": relationship or "general",
            "action": random.choice(selected),
            "deficit_note": deficit_note,
            "principle": "Trust is not a feeling. It's a prediction based on evidence. Every kept commitment, every honest moment, every act of care is evidence. Build the evidence. The feeling follows.",
        }

    def get_trust_score(self) -> int:
        """Calculate overall trust health (0-100)."""
        if not self._actions:
            return 40

        # Trust change and transparency
        avg_trust_change = sum(a.trust_after - a.trust_before for a in self._actions) / len(self._actions)
        avg_transparency = sum(a.transparency for a in self._actions) / len(self._actions)

        # Commitment rate
        commitments = [a for a in self._actions if a.commitment_made]
        if commitments:
            commitment_rate = sum(1 for a in commitments if a.commitment_kept) / len(commitments)
        else:
            commitment_rate = 0

        # Type variety
        unique_types = len(set(a.trust_type for a in self._actions))

        # Relationship variety
        unique_rels = len(set(a.relationship for a in self._actions if a.relationship))

        # Recent trend
        recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_trust_change = sum(a.trust_after - a.trust_before for a in recent) / len(recent)
            recent_commitment = sum(1 for a in recent if a.commitment_kept) / len(recent)
            recent_transparency = sum(a.transparency for a in recent) / len(recent)
        else:
            recent_trust_change = 0
            recent_commitment = 0
            recent_transparency = 0

        # Erosion penalty
        erosion_penalty = 0
        if recent:
            recent_trust = sum(a.trust_after - a.trust_before for a in recent) / len(recent)
            recent_comm = sum(1 for a in recent if a.commitment_kept) / len(recent)
            if recent_trust < -0.1 or recent_comm < 0.6:
                erosion_penalty = 10

        score = (avg_trust_change * 25) + (avg_transparency * 15) + (commitment_rate * 20) + (unique_types * 2) + (unique_rels * 2) + (recent_trust_change * 15) + (recent_commitment * 10) + (recent_transparency * 10) - erosion_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._actions:
            self._stats["avg_trust_change"] = round(sum(a.trust_after - a.trust_before for a in self._actions) / len(self._actions), 2)

            commitments = [a for a in self._actions if a.commitment_made]
            if commitments:
                kept = sum(1 for a in commitments if a.commitment_kept)
                self._stats["commitment_rate"] = round(kept / len(commitments), 2)

            recent = [a for a in self._actions if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_trust = sum(a.trust_after - a.trust_before for a in recent) / len(recent)
                recent_commitment = sum(1 for a in recent if a.commitment_kept) / len(recent)
                self._stats["erosion_risk"] = recent_trust < -0.1 or recent_commitment < 0.6

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.trust_architect")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.trust_architect")

    def _log_action(self, action: TrustAction):
        try:
            with open(TRUST_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": action.timestamp,
                    "action": action.action,
                    "trust_type": action.trust_type,
                    "relationship": action.relationship,
                    "commitment_made": action.commitment_made,
                    "commitment_kept": action.commitment_kept,
                    "transparency": action.transparency,
                    "trust_before": action.trust_before,
                    "trust_after": action.trust_after,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.trust_architect")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ta_instance: Optional[TrustArchitect] = None
_ta_lock = threading.Lock()


def get_trust_architect() -> TrustArchitect:
    global _ta_instance
    with _ta_lock:
        if _ta_instance is None:
            _ta_instance = TrustArchitect()
        return _ta_instance
