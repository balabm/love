"""
LOVE Innovation Spark Generator — Breakthrough Intelligence (Modern AI Pattern)

Most innovation comes from connecting existing ideas, not inventing new ones. This generator:

1. INNOVATION TRACKING
   - Record innovation attempts and their outcomes
   - Track idea sources (analogies, combinations, constraints, failures)
   - Log breakthrough moments and their precursors

2. PATTERN ANALYSIS
   - Identify the user's innovation style (combinatorial, analogical, constraint-driven, first-principles)
   - Find innovation triggers (what reliably sparks new ideas)
   - Detect innovation droughts and their causes

3. SPARK GENERATION
   - Suggest idea generation techniques matched to current challenge
   - Provide cross-domain analogy exercises
   - Recommendation constraint-based innovation practices

4. BREAKTHROUGH CULTIVATION
   - Track the correlation between diverse inputs and breakthroughs
   - Alert when thinking is becoming too narrow
   - Celebrate novel connections

Architecture:
- record_innovation(idea, source, domain, outcome): Log innovation
- get_innovation_stats(): Get innovation pattern analysis
- get_spark_challenge(domain, block): Get challenge
- get_innovation_score(): Calculate overall innovation health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "innovation_spark_generator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INNOVATION_LOG = DATA_DIR / "innovations.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class InnovationEntry:
    """A tracked innovation entry."""
    entry_id: str = ""
    idea: str = ""
    source: str = ""  # analogy, combination, constraint, failure, question, observation
    domain: str = ""  # where the idea applies
    cross_domain: str = ""  # where the idea came from
    novelty: float = 0.5  # 0-1
    feasibility: float = 0.5  # 0-1
    excitement: float = 0.5  # 0-1
    outcome: str = ""  # implemented, prototyped, abandoned, shelved
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class InnovationSparkGenerator:
    """
    Intelligent innovation spark generator with cross-domain analogy and constraint-based creativity.
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
            "avg_novelty": 0.0,
            "avg_excitement": 0.0,
            "best_source": "",
            "implementation_rate": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_innovation(self, idea: str = "", source: str = "", domain: str = "", cross_domain: str = "", novelty: float = 0.5, feasibility: float = 0.5, excitement: float = 0.5, outcome: str = "", notes: str = "") -> InnovationEntry:
        """Record an innovation entry."""
        entry_id = f"inn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = InnovationEntry(
            entry_id=entry_id,
            idea=idea or "unspecified",
            source=source or "observation",
            domain=domain or "general",
            cross_domain=cross_domain,
            novelty=novelty,
            feasibility=feasibility,
            excitement=excitement,
            outcome=outcome or "shelved",
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

    def get_innovation_stats(self) -> Dict[str, Any]:
        """Get innovation pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Source analysis
        by_source = defaultdict(lambda: {"count": 0, "novelty_sum": 0.0, "excitement_sum": 0.0, "feasibility_sum": 0.0})
        for e in self._entries:
            by_source[e.source]["count"] += 1
            by_source[e.source]["novelty_sum"] += e.novelty
            by_source[e.source]["excitement_sum"] += e.excitement
            by_source[e.source]["feasibility_sum"] += e.feasibility

        source_stats = {}
        for s, data in by_source.items():
            count = data["count"]
            source_stats[s] = {
                "count": count,
                "avg_novelty": round(data["novelty_sum"] / count, 2),
                "avg_excitement": round(data["excitement_sum"] / count, 2),
                "avg_feasibility": round(data["feasibility_sum"] / count, 2),
            }

        best_source = max(source_stats.items(), key=lambda x: x[1]["avg_novelty"] + x[1]["avg_excitement"]) if source_stats else ("", {})

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "novelty_sum": 0.0, "excitement_sum": 0.0})
        for e in self._entries:
            by_domain[e.domain]["count"] += 1
            by_domain[e.domain]["novelty_sum"] += e.novelty
            by_domain[e.domain]["excitement_sum"] += e.excitement

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "avg_novelty": round(data["novelty_sum"] / count, 2),
                "avg_excitement": round(data["excitement_sum"] / count, 2),
            }

        # Cross-domain analysis
        cross_domain_entries = [e for e in self._entries if e.cross_domain]
        if cross_domain_entries:
            cross_novelty = sum(e.novelty for e in cross_domain_entries) / len(cross_domain_entries)
            cross_excitement = sum(e.excitement for e in cross_domain_entries) / len(cross_domain_entries)
        else:
            cross_novelty = 0
            cross_excitement = 0

        # Outcome analysis
        by_outcome = defaultdict(int)
        for e in self._entries:
            by_outcome[e.outcome] += 1

        implemented = by_outcome.get("implemented", 0)
        prototyped = by_outcome.get("prototyped", 0)
        implementation_rate = (implemented + prototyped) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_novelty = sum(e.novelty for e in recent) / len(recent)
            recent_excitement = sum(e.excitement for e in recent) / len(recent)
        else:
            recent_novelty = 0
            recent_excitement = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_novelty = sum(e.novelty for e in older) / len(older)
            older_excitement = sum(e.excitement for e in older) / len(older)
            novelty_trend = recent_novelty - older_novelty
            excitement_trend = recent_excitement - older_excitement
        else:
            novelty_trend = 0
            excitement_trend = 0

        # Drought detection
        if recent:
            low_novelty = sum(1 for e in recent if e.novelty < 0.4) / len(recent)
            drought_risk = low_novelty > 0.5
        else:
            drought_risk = False

        return {
            "total_entries": len(self._entries),
            "source_stats": source_stats,
            "best_source": best_source[0],
            "domain_stats": domain_stats,
            "cross_domain_effectiveness": {
                "avg_novelty": round(cross_novelty, 2),
                "avg_excitement": round(cross_excitement, 2),
            },
            "outcome_stats": dict(by_outcome),
            "implementation_rate": round(implementation_rate, 2),
            "avg_novelty": round(sum(e.novelty for e in self._entries) / len(self._entries), 2),
            "avg_excitement": round(sum(e.excitement for e in self._entries) / len(self._entries), 2),
            "novelty_trend": round(novelty_trend, 2),
            "excitement_trend": round(excitement_trend, 2),
            "drought_risk": drought_risk,
        }

    def get_spark_challenge(self, domain: str = "", block: str = "") -> Dict[str, Any]:
        """Get challenge."""
        challenges = {
            "analogy": [
                "How would nature solve this? (biomimicry)",
                "How would a 5-year-old explain this?",
                "What would this look like in music? In architecture? In cooking?",
                "How did people solve this 100 years ago? 1000 years ago?",
            ],
            "combination": [
                "Combine your domain with something completely unrelated. E.g., finance + gardening.",
                "Take two ideas you had this month. Force them together.",
                "What if you added the opposite of what you're doing now?",
            ],
            "constraint": [
                "Solve this with half the resources. What would you keep? What would you cut?",
                "You can only use one color. One word. One shape. What emerges?",
                "What if you had 24 hours to solve this? What's the minimum viable solution?",
            ],
            "first_principles": [
                "Strip away all assumptions. What's actually true? What do you know for certain?",
                "Ask 'Why?' 5 times. Go deeper each time.",
                "If you were starting from scratch today, would you do it the same way?",
            ],
            "question": [
                "What would you attempt if you knew you could not fail?",
                "What problem are you solving that no one else sees?",
                "What would the opposite of your current approach look like?",
            ],
        }

        selected = challenges.get(block, challenges["analogy"])

        if block == "analogy":
            block_note = "Analogical thinking is the engine of innovation. Most 'new' ideas are old ideas in new contexts."
        elif block == "combination":
            block_note = "Innovation is often recombination, not invention. The more diverse your inputs, the more novel your outputs."
        elif block == "constraint":
            block_note = "Constraints don't limit creativity. They focus it. The blank page is paralyzing. The constraint is liberating."
        elif block == "first_principles":
            block_note = "First-principles thinking is hard. It requires questioning everything you assume. But it's where breakthroughs live."
        else:
            block_note = "Questions are the origin of innovation. Better questions lead to better ideas."

        return {
            "domain": domain or "general",
            "block": block or "general",
            "challenge": random.choice(selected),
            "block_note": block_note,
            "principle": "Innovation is not about having better ideas. It's about having more ideas, then connecting them in unexpected ways. Quantity leads to quality.",
        }

    def get_innovation_score(self) -> int:
        """Calculate overall innovation health (0-100)."""
        if not self._entries:
            return 30

        # Novelty and excitement
        avg_novelty = sum(e.novelty for e in self._entries) / len(self._entries)
        avg_excitement = sum(e.excitement for e in self._entries) / len(self._entries)

        # Feasibility
        avg_feasibility = sum(e.feasibility for e in self._entries) / len(self._entries)

        # Implementation
        implemented = sum(1 for e in self._entries if e.outcome == "implemented")
        prototyped = sum(1 for e in self._entries if e.outcome == "prototyped")
        implementation_rate = (implemented + prototyped) / len(self._entries)

        # Cross-domain
        cross_domain_entries = [e for e in self._entries if e.cross_domain]
        cross_domain_ratio = len(cross_domain_entries) / len(self._entries)

        # Source variety
        unique_sources = len(set(e.source for e in self._entries))

        # Domain variety
        unique_domains = len(set(e.domain for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_novelty = sum(e.novelty for e in recent) / len(recent)
            recent_excitement = sum(e.excitement for e in recent) / len(recent)
        else:
            recent_novelty = 0
            recent_excitement = 0

        score = (avg_novelty * 20) + (avg_excitement * 15) + (avg_feasibility * 15) + (implementation_rate * 15) + (cross_domain_ratio * 10) + (unique_sources * 2) + (unique_domains * 2) + (recent_novelty * 10) + (recent_excitement * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_novelty"] = round(sum(e.novelty for e in self._entries) / len(self._entries), 2)
            self._stats["avg_excitement"] = round(sum(e.excitement for e in self._entries) / len(self._entries), 2)

            by_source = defaultdict(lambda: {"novelty": 0.0, "excitement": 0.0, "count": 0})
            for e in self._entries:
                by_source[e.source]["novelty"] += e.novelty
                by_source[e.source]["excitement"] += e.excitement
                by_source[e.source]["count"] += 1
            if by_source:
                best = max(by_source.items(), key=lambda x: (x[1]["novelty"] + x[1]["excitement"]) / max(1, x[1]["count"]))
                self._stats["best_source"] = best[0]

            implemented = sum(1 for e in self._entries if e.outcome == "implemented")
            prototyped = sum(1 for e in self._entries if e.outcome == "prototyped")
            self._stats["implementation_rate"] = round((implemented + prototyped) / len(self._entries), 2)

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

    def _log_entry(self, entry: InnovationEntry):
        try:
            with open(INNOVATION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "idea": entry.idea,
                    "source": entry.source,
                    "domain": entry.domain,
                    "cross_domain": entry.cross_domain,
                    "novelty": entry.novelty,
                    "feasibility": entry.feasibility,
                    "outcome": entry.outcome,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_isg_instance: Optional[InnovationSparkGenerator] = None
_isg_lock = threading.Lock()


def get_innovation_spark_generator() -> InnovationSparkGenerator:
    global _isg_instance
    with _isg_lock:
        if _isg_instance is None:
            _isg_instance = InnovationSparkGenerator()
        return _isg_instance
