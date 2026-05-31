"""
LOVE Belief Examiner — Epistemology Intelligence (Modern AI Pattern)

Most people don't examine their beliefs. This examiner:

1. BELIEF TRACKING
   - Record beliefs and their evidence strength
   - Track belief changes and what caused them
   - Log beliefs that drive behavior vs beliefs that are just inherited

2. PATTERN ANALYSIS
   - Identify the user's belief style (fixed, exploratory, evidence-based, intuition-based)
   - Find limiting beliefs and their behavioral impact
   - Detect belief clusters (interconnected beliefs that reinforce each other)

3. BELIEF EXAMINATION
   - Suggest evidence-gathering for challenged beliefs
   - Provide counter-evidence exercises for rigid beliefs
   - Recommend belief-update protocols

4. EMPOWERMENT
   - Track the correlation between belief flexibility and adaptability
   - Alert when beliefs are causing suffering without evidence
   - Celebrate belief updates that enable growth

Architecture:
- record_belief(belief, evidence, strength, impact): Log belief
- get_belief_stats(): Get belief pattern analysis
- get_examination_exercise(belief, rigidity): Get exercise
- get_belief_score(): Calculate overall belief health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "belief_examiner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BELIEF_LOG = DATA_DIR / "beliefs.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BeliefEntry:
    """A tracked belief entry."""
    entry_id: str = ""
    belief: str = ""
    evidence: List[str] = field(default_factory=list)
    evidence_strength: float = 0.5  # 0-1
    emotional_charge: float = 0.5  # 0-1
    rigidity: float = 0.5  # 0-1, how fixed the belief is
    behavioral_impact: float = 0.5  # 0-1, how much it affects behavior
    origin: str = ""  # childhood, culture, trauma, education, experience, choice
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BeliefExaminer:
    """
    Intelligent belief examiner with evidence analysis and rigidity detection.
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
        self._entries: deque = deque(maxlen=200)
        self._stats = {
            "total_entries": 0,
            "avg_evidence": 0.0,
            "avg_rigidity": 0.0,
            "limiting_beliefs": [],
            "flexible_beliefs": [],
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_belief(self, belief: str = "", evidence: Optional[List[str]] = None, evidence_strength: float = 0.5, emotional_charge: float = 0.5, rigidity: float = 0.5, behavioral_impact: float = 0.5, origin: str = "", notes: str = "") -> BeliefEntry:
        """Record a belief entry."""
        entry_id = f"belief_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BeliefEntry(
            entry_id=entry_id,
            belief=belief or "unspecified",
            evidence=evidence or [],
            evidence_strength=evidence_strength,
            emotional_charge=emotional_charge,
            rigidity=rigidity,
            behavioral_impact=behavioral_impact,
            origin=origin or "unknown",
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

    def get_belief_stats(self) -> Dict[str, Any]:
        """Get belief pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Belief analysis
        by_belief = defaultdict(lambda: {"count": 0, "evidence_sum": 0.0, "rigidity_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            by_belief[e.belief]["count"] += 1
            by_belief[e.belief]["evidence_sum"] += e.evidence_strength
            by_belief[e.belief]["rigidity_sum"] += e.rigidity
            by_belief[e.belief]["impact_sum"] += e.behavioral_impact

        belief_stats = {}
        for b, data in by_belief.items():
            count = data["count"]
            belief_stats[b] = {
                "count": count,
                "avg_evidence": round(data["evidence_sum"] / count, 2),
                "avg_rigidity": round(data["rigidity_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Limiting beliefs (high impact, low evidence, high rigidity)
        limiting = [b for b, d in belief_stats.items() if d["avg_impact"] > 0.6 and d["avg_evidence"] < 0.4 and d["avg_rigidity"] > 0.6]
        
        # Flexible beliefs (low rigidity, high evidence)
        flexible = [b for b, d in belief_stats.items() if d["avg_rigidity"] < 0.4 and d["avg_evidence"] > 0.6]

        # Origin analysis
        by_origin = defaultdict(lambda: {"count": 0, "evidence_sum": 0.0, "rigidity_sum": 0.0})
        for e in self._entries:
            by_origin[e.origin]["count"] += 1
            by_origin[e.origin]["evidence_sum"] += e.evidence_strength
            by_origin[e.origin]["rigidity_sum"] += e.rigidity

        origin_stats = {}
        for o, data in by_origin.items():
            count = data["count"]
            origin_stats[o] = {
                "count": count,
                "avg_evidence": round(data["evidence_sum"] / count, 2),
                "avg_rigidity": round(data["rigidity_sum"] / count, 2),
            }

        # Emotional charge analysis
        high_charge = [e for e in self._entries if e.emotional_charge > 0.7]
        if high_charge:
            high_charge_evidence = sum(e.evidence_strength for e in high_charge) / len(high_charge)
            high_charge_rigidity = sum(e.rigidity for e in high_charge) / len(high_charge)
        else:
            high_charge_evidence = 0
            high_charge_rigidity = 0

        return {
            "total_entries": len(self._entries),
            "belief_stats": belief_stats,
            "limiting_beliefs": limiting,
            "flexible_beliefs": flexible,
            "origin_stats": origin_stats,
            "avg_evidence": round(sum(e.evidence_strength for e in self._entries) / len(self._entries), 2),
            "avg_rigidity": round(sum(e.rigidity for e in self._entries) / len(self._entries), 2),
            "high_charge_evidence": round(high_charge_evidence, 2),
            "high_charge_rigidity": round(high_charge_rigidity, 2),
        }

    def get_examination_exercise(self, belief: str = "", rigidity: float = 0.5, origin: str = "") -> Dict[str, Any]:
        """Get exercise."""
        exercises = [
            "Write the belief on paper. Under it, list 3 pieces of evidence FOR it and 3 pieces AGAINST it.",
            "Ask: 'If my best friend had this belief, what would I tell them?'",
            "Imagine it's 10 years from now. Looking back, how true does this belief seem?",
            "Find one person you respect who doesn't hold this belief. What do they believe instead?",
            "Ask: 'What would I need to believe to feel better and act better?' Try that belief on for size.",
            "Trace the belief back to its origin. Did you choose it, or was it given to you? Do you still choose it?",
            "Rate the belief on a scale of 0-100. What evidence would move it 10 points? Go find that evidence.",
            "Ask: 'Is this belief useful?' Not 'Is it true?' Truth is hard. Usefulness is actionable.",
        ]

        if rigidity > 0.7:
            approach = "This belief is rigid. Don't try to destroy it. Just loosen it. Find one exception. One.",
        elif rigidity > 0.4:
            approach = "Moderate flexibility. You can examine this directly. Gather evidence. Update as needed.",
        else:
            approach = "This belief is already flexible. You're doing well. Keep updating as new evidence arrives.",

        if origin == "trauma":
            trauma_note = "This belief came from pain. Be gentle. It protected you once. Ask if it still serves you."
        elif origin == "childhood":
            trauma_note = "This belief was installed before you could choose. You're allowed to outgrow it."
        elif origin == "culture":
            trauma_note = "This belief came from your environment. Not all cultural beliefs fit all individuals."
        else:
            trauma_note = "Examine this belief with curiosity, not judgment. Beliefs are tools, not tattoos."

        return {
            "belief": belief or "unspecified",
            "rigidity": rigidity,
            "origin": origin or "unknown",
            "approach": approach,
            "exercise": random.choice(exercises),
            "trauma_note": trauma_note,
            "reminder": "The goal isn't to have no beliefs. It's to hold them lightly and update them eagerly.",
        }

    def get_belief_score(self) -> int:
        """Calculate overall belief health (0-100)."""
        if not self._entries:
            return 35

        # Evidence strength
        avg_evidence = sum(e.evidence_strength for e in self._entries) / len(self._entries)

        # Low rigidity (flexibility is good)
        avg_rigidity = sum(e.rigidity for e in self._entries) / len(self._entries)

        # Behavioral alignment (beliefs that drive positive action)
        positive_impact = sum(1 for e in self._entries if e.behavioral_impact > 0.5) / len(self._entries)

        # Low emotional charge without evidence
        high_charge_low_evidence = [e for e in self._entries if e.emotional_charge > 0.7 and e.evidence_strength < 0.3]
        hcle_penalty = min(20, len(high_charge_low_evidence) * 5)

        # Origin diversity (beliefs from multiple sources are healthier)
        origins = set(e.origin for e in self._entries)
        origin_bonus = len(origins) * 2

        # Recent trend
        recent = list(self._entries)[-10:]
        recent_rigidity = sum(e.rigidity for e in recent) / len(recent)
        older = list(self._entries)[:-10] if len(self._entries) > 10 else []
        if older:
            older_rigidity = sum(e.rigidity for e in older) / len(older)
            trend = older_rigidity - recent_rigidity  # lower rigidity is better
        else:
            trend = 0

        score = (avg_evidence * 20) + ((1 - avg_rigidity) * 20) + (positive_impact * 15) + (trend * 15) + origin_bonus - hcle_penalty + 15
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_evidence"] = round(sum(e.evidence_strength for e in self._entries) / len(self._entries), 2)
            self._stats["avg_rigidity"] = round(sum(e.rigidity for e in self._entries) / len(self._entries), 2)

            by_belief = defaultdict(lambda: {"evidence": 0.0, "rigidity": 0.0, "impact": 0.0, "count": 0})
            for e in self._entries:
                by_belief[e.belief]["evidence"] += e.evidence_strength
                by_belief[e.belief]["rigidity"] += e.rigidity
                by_belief[e.belief]["impact"] += e.behavioral_impact
                by_belief[e.belief]["count"] += 1
            
            limiting = []
            flexible = []
            for b, d in by_belief.items():
                avg_evidence = d["evidence"] / max(1, d["count"])
                avg_rigidity = d["rigidity"] / max(1, d["count"])
                avg_impact = d["impact"] / max(1, d["count"])
                if avg_impact > 0.6 and avg_evidence < 0.4 and avg_rigidity > 0.6:
                    limiting.append(b)
                if avg_rigidity < 0.4 and avg_evidence > 0.6:
                    flexible.append(b)
            
            self._stats["limiting_beliefs"] = limiting
            self._stats["flexible_beliefs"] = flexible

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

    def _log_entry(self, entry: BeliefEntry):
        try:
            with open(BELIEF_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "belief": entry.belief,
                    "evidence_strength": entry.evidence_strength,
                    "emotional_charge": entry.emotional_charge,
                    "rigidity": entry.rigidity,
                    "origin": entry.origin,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_be_instance: Optional[BeliefExaminer] = None
_be_lock = threading.Lock()


def get_belief_examiner() -> BeliefExaminer:
    global _be_instance
    with _be_lock:
        if _be_instance is None:
            _be_instance = BeliefExaminer()
        return _be_instance
