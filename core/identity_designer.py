"""
LOVE Identity Designer — Self-Concept Intelligence (Modern AI Pattern)

Most identity change fails because people try to change behavior before identity. This designer:

1. IDENTITY TRACKING
   - Record current identity statements and their evidence
   - Track identity shifts and what triggered them
   - Log the gap between stated identity and actual behavior

2. PATTERN ANALYSIS
   - Identify the user's identity anchors (what they believe about themselves)
   - Find identity contradictions (where belief and behavior conflict)
   - Detect aspirational vs actual identity gaps

3. IDENTITY DESIGN
   - Suggest small identity shifts that enable behavior change
   - Provide evidence-gathering exercises for new identities
   - Recommend identity-supporting environments and communities

4. BEHAVIOR ALIGNMENT
   - Track how behavior changes after identity shifts
   - Alert when behavior contradicts desired identity
   - Celebrate identity-behavior alignment

Architecture:
- record_identity(identity, evidence, strength, type): Log identity
- get_identity_stats(): Get identity pattern analysis
- get_identity_design(target_identity, current_gap): Get design plan
- get_identity_score(): Calculate overall identity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "identity_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

IDENTITY_LOG = DATA_DIR / "identities.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class IdentityEntry:
    """A tracked identity entry."""
    entry_id: str = ""
    identity_statement: str = ""
    evidence: List[str] = field(default_factory=list)
    strength: float = 0.5  # 0-1
    identity_type: str = ""  # current, aspirational, past, feared, hidden
    behavioral_alignment: float = 0.5  # 0-1, how much behavior matches
    source: str = ""  # self, peer, family, culture, trauma, choice
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class IdentityDesigner:
    """
    Intelligent identity designer with evidence-based identity engineering.
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
            "avg_strength": 0.0,
            "avg_alignment": 0.0,
            "strongest_identity": "",
            "biggest_gap": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_identity(self, identity_statement: str = "", evidence: Optional[List[str]] = None, strength: float = 0.5, identity_type: str = "", alignment: float = 0.5, source: str = "", notes: str = "") -> IdentityEntry:
        """Record an identity entry."""
        entry_id = f"id_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = IdentityEntry(
            entry_id=entry_id,
            identity_statement=identity_statement or "unspecified",
            evidence=evidence or [],
            strength=strength,
            identity_type=identity_type or "current",
            behavioral_alignment=alignment,
            source=source or "self",
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

    def get_identity_stats(self) -> Dict[str, Any]:
        """Get identity pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "strength_sum": 0.0, "alignment_sum": 0.0})
        for e in self._entries:
            by_type[e.identity_type]["count"] += 1
            by_type[e.identity_type]["strength_sum"] += e.strength
            by_type[e.identity_type]["alignment_sum"] += e.behavioral_alignment

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_strength": round(data["strength_sum"] / count, 2),
                "avg_alignment": round(data["alignment_sum"] / count, 2),
            }

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "strength_sum": 0.0})
        for e in self._entries:
            by_source[e.source]["count"] += 1
            by_source[e.source]["strength_sum"] += e.strength

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_strength": round(data["strength_sum"] / count, 2),
            }

        # Gap analysis (aspirational vs current)
        aspirational = [e for e in self._entries if e.identity_type == "aspirational"]
        current = [e for e in self._entries if e.identity_type == "current"]
        
        gaps = []
        for a in aspirational:
            matching_current = [c for c in current if self._similar_identity(c.identity_statement, a.identity_statement)]
            if matching_current:
                for c in matching_current:
                    gap = a.strength - c.strength
                    gaps.append({
                        "aspirational": a.identity_statement,
                        "current": c.identity_statement,
                        "gap": round(gap, 2),
                    })
            else:
                gaps.append({
                    "aspirational": a.identity_statement,
                    "current": "none",
                    "gap": round(a.strength, 2),
                })

        # Strongest identity
        strongest = max(self._entries, key=lambda e: e.strength)
        
        # Biggest gap
        biggest_gap = max(gaps, key=lambda g: g["gap"]) if gaps else {"aspirational": "", "current": "", "gap": 0}

        # Contradiction detection
        contradictions = []
        current_entries = [e for e in self._entries if e.identity_type == "current"]
        for i, e1 in enumerate(current_entries):
            for e2 in current_entries[i+1:]:
                if self._contradictory(e1.identity_statement, e2.identity_statement):
                    contradictions.append({
                        "identity1": e1.identity_statement,
                        "identity2": e2.identity_statement,
                        "strength1": e1.strength,
                        "strength2": e2.strength,
                    })

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "source_stats": source_stats,
            "strongest_identity": strongest.identity_statement,
            "strongest_strength": strongest.strength,
            "biggest_gap": biggest_gap,
            "gaps": gaps,
            "contradictions": contradictions,
            "avg_strength": round(sum(e.strength for e in self._entries) / len(self._entries), 2),
            "avg_alignment": round(sum(e.behavioral_alignment for e in self._entries) / len(self._entries), 2),
        }

    def _similar_identity(self, id1: str, id2: str) -> bool:
        """Check if two identity statements are similar."""
        words1 = set(id1.lower().split())
        words2 = set(id2.lower().split())
        overlap = len(words1 & words2)
        return overlap >= 2

    def _contradictory(self, id1: str, id2: str) -> bool:
        """Check if two identities contradict."""
        contradictions = [
            ("patient", "impatient"), ("organized", "disorganized"), ("healthy", "unhealthy"),
            ("disciplined", "undisciplined"), ("social", "antisocial"), ("optimistic", "pessimistic"),
        ]
        for a, b in contradictions:
            if (a in id1.lower() and b in id2.lower()) or (b in id1.lower() and a in id2.lower()):
                return True
        return False

    def get_identity_design(self, target_identity: str = "", current_gap: float = 0.5, domain: str = "") -> Dict[str, Any]:
        """Get identity design plan."""
        small_steps = [
            f"Start each day by saying: 'Today I am someone who {target_identity}'",
            f"Ask yourself before decisions: 'What would someone who {target_identity} do?'",
            f"Find one tiny action that proves you {target_identity}. Do it daily.",
            f"Journal: 'I {target_identity} because...' List 3 pieces of evidence.",
            f"Surround yourself with people who already {target_identity}. Identity is contagious.",
        ]

        evidence_exercises = [
            "Track one behavior for 7 days that aligns with this identity",
            "Write a letter from your future self who fully embodies this identity",
            "Create a visual reminder (photo, quote, object) that represents this identity",
            "Teach someone else about this identity. Teaching cements learning.",
        ]

        if current_gap > 0.7:
            approach = "This is a big shift. Start with the smallest possible version. One minute a day."
        elif current_gap > 0.4:
            approach = "Moderate gap. Focus on evidence gathering. Each aligned action strengthens belief."
        else:
            approach = "Close gap. You're almost there. Consolidate with community and environment design."

        return {
            "target_identity": target_identity or "unspecified",
            "current_gap": current_gap,
            "domain": domain or "general",
            "approach": approach,
            "small_steps": random.sample(small_steps, min(2, len(small_steps))),
            "evidence_exercises": random.sample(evidence_exercises, min(2, len(evidence_exercises))),
            "reminder": "You don't need to believe it fully. You just need to act as if it's true, one small step at a time. Belief follows behavior.",
        }

    def get_identity_score(self) -> int:
        """Calculate overall identity health (0-100)."""
        if not self._entries:
            return 40

        # Average strength
        avg_strength = sum(e.strength for e in self._entries) / len(self._entries)

        # Behavioral alignment
        avg_alignment = sum(e.behavioral_alignment for e in self._entries) / len(self._entries)

        # Low contradiction
        contradictions = 0
        current_entries = [e for e in self._entries if e.identity_type == "current"]
        for i, e1 in enumerate(current_entries):
            for e2 in current_entries[i+1:]:
                if self._contradictory(e1.identity_statement, e2.identity_statement):
                    contradictions += 1
        contradiction_penalty = min(20, contradictions * 5)

        # Gap management
        aspirational = [e for e in self._entries if e.identity_type == "aspirational"]
        if aspirational and current_entries:
            gaps = []
            for a in aspirational:
                matching = [c for c in current_entries if self._similar_identity(c.identity_statement, a.identity_statement)]
                if matching:
                    for c in matching:
                        gaps.append(a.strength - c.strength)
                else:
                    gaps.append(a.strength)
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
        else:
            avg_gap = 0

        # Evidence richness
        avg_evidence = sum(len(e.evidence) for e in self._entries) / len(self._entries)

        score = (avg_strength * 20) + (avg_alignment * 25) + ((1 - avg_gap) * 20) + (avg_evidence * 5) - contradiction_penalty + 20
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_strength"] = round(sum(e.strength for e in self._entries) / len(self._entries), 2)
            self._stats["avg_alignment"] = round(sum(e.behavioral_alignment for e in self._entries) / len(self._entries), 2)
            
            strongest = max(self._entries, key=lambda e: e.strength)
            self._stats["strongest_identity"] = strongest.identity_statement

            aspirational = [e for e in self._entries if e.identity_type == "aspirational"]
            current = [e for e in self._entries if e.identity_type == "current"]
            if aspirational and current:
                gaps = []
                for a in aspirational:
                    matching = [c for c in current if self._similar_identity(c.identity_statement, a.identity_statement)]
                    if matching:
                        for c in matching:
                            gaps.append(a.strength - c.strength)
                    else:
                        gaps.append(a.strength)
                if gaps:
                    biggest_gap = max(gaps)
                    self._stats["biggest_gap"] = f"{biggest_gap:.2f}"

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

    def _log_entry(self, entry: IdentityEntry):
        try:
            with open(IDENTITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "identity": entry.identity_statement,
                    "type": entry.identity_type,
                    "strength": entry.strength,
                    "alignment": entry.behavioral_alignment,
                    "evidence_count": len(entry.evidence),
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_id_instance: Optional[IdentityDesigner] = None
_id_lock = threading.Lock()


def get_identity_designer() -> IdentityDesigner:
    global _id_instance
    with _id_lock:
        if _id_instance is None:
            _id_instance = IdentityDesigner()
        return _id_instance
