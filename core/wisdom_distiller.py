"""
LOVE Wisdom Distiller — Deep Understanding Intelligence (Modern AI Pattern)

Most information is noise. Wisdom is signal. This distiller:

1. WISDOM TRACKING
   - Record wisdom moments and their characteristics
   - Track distillations (complex to simple, noise to signal)
   - Log wisdom sources and their reliability

2. PATTERN ANALYSIS
   - Identify the user's wisdom style (experiential, reflective, integrative, intuitive)
   - Find distillation patterns that produce clarity
   - Detect wisdom gaps (areas where complexity reigns)

3. DISTILLATION PRACTICES
   - Suggest distillation exercises matched to current complexity
   - Provide simplification techniques
   - Recommendation principle-extraction practices

4. CLARITY CULTIVATION
   - Track the correlation between distillation and decision quality
   - Alert when complexity is masking confusion
   - Celebrate moments of profound simplicity

Architecture:
- record_wisdom(situation, complexity, distillation, principle): Log wisdom
- get_wisdom_stats(): Get wisdom pattern analysis
- get_distillation_practice(complexity, domain): Get practice
- get_wisdom_score(): Calculate overall wisdom health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "wisdom_distiller"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WISDOM_LOG = DATA_DIR / "wisdom.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WisdomEntry:
    """A tracked wisdom entry."""
    entry_id: str = ""
    situation: str = ""
    complexity_before: float = 0.5  # 0-1
    distillation: str = ""  # the simplified insight
    principle: str = ""  # underlying principle
    clarity_after: float = 0.5  # 0-1
    decision_quality: float = 0.5  # 0-1
    domain: str = ""  # where this wisdom applies
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class WisdomDistiller:
    """
    Intelligent wisdom distiller with complexity tracking and principle extraction.
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
            "avg_clarity": 0.0,
            "avg_decision_quality": 0.0,
            "best_domain": "",
            "complexity_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_wisdom(self, situation: str = "", complexity_before: float = 0.5, distillation: str = "", principle: str = "", clarity_after: float = 0.5, decision_quality: float = 0.5, domain: str = "", notes: str = "") -> WisdomEntry:
        """Record a wisdom entry."""
        entry_id = f"wis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = WisdomEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            complexity_before=complexity_before,
            distillation=distillation,
            principle=principle,
            clarity_after=clarity_after,
            decision_quality=decision_quality,
            domain=domain or "general",
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

    def get_wisdom_stats(self) -> Dict[str, Any]:
        """Get wisdom pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "decision_sum": 0.0, "complexity_sum": 0.0})
        for e in self._entries:
            by_domain[e.domain]["count"] += 1
            by_domain[e.domain]["clarity_sum"] += e.clarity_after
            by_domain[e.domain]["decision_sum"] += e.decision_quality
            by_domain[e.domain]["complexity_sum"] += e.complexity_before

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_decision": round(data["decision_sum"] / count, 2),
                "avg_complexity": round(data["complexity_sum"] / count, 2),
            }

        best_domain = max(domain_stats.items(), key=lambda x: x[1]["avg_clarity"] * x[1]["avg_decision"]) if domain_stats else ("", {})

        # Principle analysis
        by_principle = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0})
        for e in self._entries:
            if e.principle:
                by_principle[e.principle]["count"] += 1
                by_principle[e.principle]["clarity_sum"] += e.clarity_after

        principle_stats = {}
        for p, data in by_principle.items():
            count = data["count"]
            if count >= 2:
                principle_stats[p] = {
                    "count": count,
                    "avg_clarity": round(data["clarity_sum"] / count, 2),
                }

        best_principles = sorted(principle_stats.items(), key=lambda x: x[1]["avg_clarity"], reverse=True)[:5]

        # Complexity analysis
        high_complexity = [e for e in self._entries if e.complexity_before > 0.7]
        if high_complexity:
            high_complexity_clarity = sum(e.clarity_after for e in high_complexity) / len(high_complexity)
        else:
            high_complexity_clarity = 0

        low_complexity = [e for e in self._entries if e.complexity_before <= 0.4]
        if low_complexity:
            low_complexity_clarity = sum(e.clarity_after for e in low_complexity) / len(low_complexity)
        else:
            low_complexity_clarity = 0

        # Distillation effectiveness
        avg_distillation = sum(e.clarity_after - e.complexity_before for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_clarity = sum(e.clarity_after for e in recent) / len(recent)
            recent_decision = sum(e.decision_quality for e in recent) / len(recent)
            recent_complexity = sum(e.complexity_before for e in recent) / len(recent)
        else:
            recent_clarity = 0
            recent_decision = 0
            recent_complexity = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_clarity = sum(e.clarity_after for e in older) / len(older)
            older_decision = sum(e.decision_quality for e in older) / len(older)
            clarity_trend = recent_clarity - older_clarity
            decision_trend = recent_decision - older_decision
        else:
            clarity_trend = 0
            decision_trend = 0

        # Complexity risk (high complexity without clarity)
        complexity_risk = recent_complexity > 0.6 and recent_clarity < 0.5

        return {
            "total_entries": len(self._entries),
            "domain_stats": domain_stats,
            "best_domain": best_domain[0],
            "best_principles": best_principles,
            "complexity_stats": {
                "high_complexity_clarity": round(high_complexity_clarity, 2),
                "low_complexity_clarity": round(low_complexity_clarity, 2),
            },
            "distillation_effectiveness": round(avg_distillation, 2),
            "avg_clarity": round(sum(e.clarity_after for e in self._entries) / len(self._entries), 2),
            "avg_decision": round(sum(e.decision_quality for e in self._entries) / len(self._entries), 2),
            "avg_complexity": round(sum(e.complexity_before for e in self._entries) / len(self._entries), 2),
            "clarity_trend": round(clarity_trend, 2),
            "decision_trend": round(decision_trend, 2),
            "complexity_risk": complexity_risk,
        }

    def get_distillation_practice(self, complexity: float = 0.5, domain: str = "") -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "high_complexity": [
                "Write the problem in one sentence. Then in 10 words. Then in 5. If you can't, you don't understand it.",
                "List all factors. Cross out everything that doesn't change the answer. What's left?",
                "Ask: 'What would I tell a friend in this situation?' Distance creates clarity.",
            ],
            "medium_complexity": [
                "Find the one thing that, if true, makes everything else fall into place.",
                "Draw the situation. Visual processing uses different brain circuits than verbal.",
                "Explain it to a 10-year-old. If they don't get it, simplify more.",
            ],
            "low_complexity": [
                "Challenge yourself: Is this actually simple, or am I missing complexity? Sometimes simplicity is blindness.",
                "Stress-test your simple answer. What would make it wrong?",
                "Find the edge case that breaks your simple model. That's where wisdom deepens.",
            ],
            "principle_extraction": [
                "Ask: 'What is this an example of?' Find the category. Then the principle.",
                "If you had to bet your life savings on one principle from this situation, which would it be?",
                "What would remain true if all the details changed? That's the principle.",
            ],
            "general": [
                "Inversion: Instead of 'how do I succeed?', ask 'how do I guarantee failure?' Avoid that.",
                "Occam's Razor: The simplest explanation is usually correct. Resist adding complexity.",
                "Second-order thinking: What happens after what happens? Think two steps ahead.",
            ],
        }

        if complexity > 0.7:
            selected = practices["high_complexity"]
            complexity_note = "High complexity detected. This is where most people get lost. Your job is to find the signal in the noise."
        elif complexity > 0.4:
            selected = practices["medium_complexity"]
            complexity_note = "Moderate complexity. Good distillation territory. Find the leverage point."
        else:
            selected = practices["low_complexity"]
            complexity_note = "Low complexity. Either you've found clarity or you're oversimplifying. Check which."

        return {
            "complexity": complexity,
            "domain": domain or "general",
            "practice": random.choice(selected),
            "complexity_note": complexity_note,
            "principle": "Wisdom is not knowing more. It's seeing the simple truth beneath the complex surface. It's the ability to hold complexity in one hand and simplicity in the other. Most people choose one. Wisdom requires both.",
        }

    def get_wisdom_score(self) -> int:
        """Calculate overall wisdom health (0-100)."""
        if not self._entries:
            return 30

        # Clarity and decision quality
        avg_clarity = sum(e.clarity_after for e in self._entries) / len(self._entries)
        avg_decision = sum(e.decision_quality for e in self._entries) / len(self._entries)

        # Distillation effectiveness (clarity gain)
        avg_distillation = sum(e.clarity_after - e.complexity_before for e in self._entries) / len(self._entries)

        # Principle extraction
        with_principle = [e for e in self._entries if e.principle]
        principle_rate = len(with_principle) / len(self._entries)

        # Domain variety
        unique_domains = len(set(e.domain for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_clarity = sum(e.clarity_after for e in recent) / len(recent)
            recent_decision = sum(e.decision_quality for e in recent) / len(recent)
            recent_complexity = sum(e.complexity_before for e in recent) / len(recent)
        else:
            recent_clarity = 0
            recent_decision = 0
            recent_complexity = 0

        # Complexity risk penalty
        complexity_risk = recent_complexity > 0.6 and recent_clarity < 0.5
        risk_penalty = 10 if complexity_risk else 0

        score = (avg_clarity * 25) + (avg_decision * 20) + (avg_distillation * 15) + (principle_rate * 15) + (unique_domains * 2) + (recent_clarity * 15) + (recent_decision * 10) - risk_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_clarity"] = round(sum(e.clarity_after for e in self._entries) / len(self._entries), 2)
            self._stats["avg_decision_quality"] = round(sum(e.decision_quality for e in self._entries) / len(self._entries), 2)

            by_domain = defaultdict(lambda: {"clarity": 0.0, "decision": 0.0, "count": 0})
            for e in self._entries:
                by_domain[e.domain]["clarity"] += e.clarity_after
                by_domain[e.domain]["decision"] += e.decision_quality
                by_domain[e.domain]["count"] += 1
            if by_domain:
                best = max(by_domain.items(), key=lambda x: (x[1]["clarity"] + x[1]["decision"]) / max(1, x[1]["count"]))
                self._stats["best_domain"] = best[0]

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if recent:
                recent_clarity = sum(e.clarity_after for e in recent) / len(recent)
                recent_complexity = sum(e.complexity_before for e in recent) / len(recent)
                self._stats["complexity_risk"] = recent_complexity > 0.6 and recent_clarity < 0.5

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.wisdom_distiller")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.wisdom_distiller")

    def _log_entry(self, entry: WisdomEntry):
        try:
            with open(WISDOM_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "complexity_before": entry.complexity_before,
                    "distillation": entry.distillation,
                    "principle": entry.principle,
                    "clarity_after": entry.clarity_after,
                    "decision_quality": entry.decision_quality,
                    "domain": entry.domain,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.wisdom_distiller")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wd_instance: Optional[WisdomDistiller] = None
_wd_lock = threading.Lock()


def get_wisdom_distiller() -> WisdomDistiller:
    global _wd_instance
    with _wd_lock:
        if _wd_instance is None:
            _wd_instance = WisdomDistiller()
        return _wd_instance
