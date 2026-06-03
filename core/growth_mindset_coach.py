"""
LOVE Growth Mindset Coach — Belief Intelligence (Modern AI Pattern)

Most people have fixed mindsets about their own growth. This coach:

1. MINDSET TRACKING
   - Record challenges faced and the mindset they triggered
   - Track self-talk during difficulty (fixed vs growth)
   - Log effort, strategy, and help-seeking patterns

2. PATTERN ANALYSIS
   - Identify fixed-mindset triggers (praise, criticism, comparison, failure)
   - Find growth-mindset activators (curiosity, purpose, autonomy, mastery)
   - Detect mindset domains (where the user is fixed vs growth)

3. MINDSET SHIFTING
   - Provide reframes for fixed-mindset moments
   - Suggest process praise over outcome praise
   - Recommend growth-mindset experiments

4. GROWTH SUPPORT
   - Track the correlation between mindset and outcomes
   - Celebrate effort and strategy, not just results
   - Alert when fixed mindset is dominating

Architecture:
- record_mindset_moment(trigger, response, domain): Log moment
- get_mindset_stats(): Get mindset pattern analysis
- get_reframe(fixed_thought, domain): Get growth reframe
- get_growth_mindset_score(): Calculate overall growth mindset health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "growth_mindset_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MINDSET_LOG = DATA_DIR / "mindset.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MindsetMoment:
    """A tracked mindset moment."""
    moment_id: str = ""
    trigger: str = ""  # what triggered the mindset
    trigger_type: str = ""  # challenge, criticism, success, failure, comparison, feedback
    fixed_response: str = ""  # the fixed-mindset thought
    growth_response: str = ""  # the growth-mindset alternative
    domain: str = ""  # intelligence, creativity, social, athletic, artistic, leadership
    mindset_used: str = ""  # fixed, mixed, growth
    outcome: str = ""  # avoided, persisted, improved, gave_up, excelled
    effort_level: float = 0.0  # 0-1
    strategy_count: int = 0
    help_seeking: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class GrowthMindsetCoach:
    """
    Intelligent growth mindset coach with trigger analysis and reframe generation.
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
        self._moments: deque = deque(maxlen=200)
        self._stats = {
            "total_moments": 0,
            "growth_rate": 0.0,
            "avg_effort": 0.0,
            "help_seeking_rate": 0.0,
            "hardest_domain": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_mindset_moment(self, trigger: str = "", trigger_type: str = "", fixed_response: str = "", growth_response: str = "", domain: str = "", mindset_used: str = "", outcome: str = "", effort: float = 0.0, strategies: int = 0, help_seeking: bool = False, notes: str = "") -> MindsetMoment:
        """Record a mindset moment."""
        moment_id = f"mindset_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._moments)}"
        moment = MindsetMoment(
            moment_id=moment_id,
            trigger=trigger or "unspecified",
            trigger_type=trigger_type or "challenge",
            fixed_response=fixed_response,
            growth_response=growth_response,
            domain=domain or "general",
            mindset_used=mindset_used or "fixed",
            outcome=outcome or "avoided",
            effort_level=effort,
            strategy_count=strategies,
            help_seeking=help_seeking,
            notes=notes,
        )

        with self._lock:
            self._moments.append(moment)
            self._stats["total_moments"] += 1
            self._update_stats()

        self._save_stats()
        self._log_moment(moment)

        return moment

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_mindset_stats(self) -> Dict[str, Any]:
        """Get mindset pattern analysis."""
        if not self._moments:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "growth": 0, "effort_sum": 0.0, "strategy_sum": 0})
        for m in self._moments:
            by_domain[m.domain]["count"] += 1
            if m.mindset_used == "growth":
                by_domain[m.domain]["growth"] += 1
            by_domain[m.domain]["effort_sum"] += m.effort_level
            by_domain[m.domain]["strategy_sum"] += m.strategy_count

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "growth_rate": round(data["growth"] / count, 2),
                "avg_effort": round(data["effort_sum"] / count, 2),
                "avg_strategies": round(data["strategy_sum"] / count, 1),
            }

        hardest = min(domain_stats.items(), key=lambda x: x[1]["growth_rate"]) if domain_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "growth": 0})
        for m in self._moments:
            by_trigger[m.trigger_type]["count"] += 1
            if m.mindset_used == "growth":
                by_trigger[m.trigger_type]["growth"] += 1

        trigger_stats = {}
        for t, data in by_trigger.items():
            count = data["count"]
            trigger_stats[t] = {
                "count": count,
                "growth_rate": round(data["growth"] / count, 2),
            }

        # Outcome analysis
        by_outcome = defaultdict(lambda: {"count": 0, "growth": 0, "effort_sum": 0.0})
        for m in self._moments:
            by_outcome[m.outcome]["count"] += 1
            if m.mindset_used == "growth":
                by_outcome[m.outcome]["growth"] += 1
            by_outcome[m.outcome]["effort_sum"] += m.effort_level

        outcome_stats = {}
        for o, data in by_outcome.items():
            count = data["count"]
            outcome_stats[o] = {
                "count": count,
                "growth_rate": round(data["growth"] / count, 2),
                "avg_effort": round(data["effort_sum"] / count, 2),
            }

        return {
            "total_moments": len(self._moments),
            "domain_stats": domain_stats,
            "hardest_domain": hardest[0],
            "trigger_stats": trigger_stats,
            "outcome_stats": outcome_stats,
            "growth_rate": round(sum(1 for m in self._moments if m.mindset_used == "growth") / len(self._moments), 2),
            "avg_effort": round(sum(m.effort_level for m in self._moments) / len(self._moments), 2),
            "help_seeking_rate": round(sum(1 for m in self._moments if m.help_seeking) / len(self._moments), 2),
            "avg_strategies": round(sum(m.strategy_count for m in self._moments) / len(self._moments), 1),
        }

    def get_reframe(self, fixed_thought: str = "", domain: str = "") -> Dict[str, Any]:
        """Get growth reframe."""
        reframes = {
            "intelligence": {
                "I'm not smart enough": "I'm not there yet. Intelligence grows with effort and strategy.",
                "This is too hard": "This is challenging. That means I'm stretching. Good.",
                "Others are naturally better": "They've practiced differently. I can learn what they know.",
                "I failed, so I can't": "I failed, so I'm learning. Failure is data, not destiny.",
            },
            "creativity": {
                "I'm not creative": "Creativity is a skill. I'm building it with practice.",
                "My ideas are bad": "My first ideas are raw material. Refinement comes later.",
                "I'm not original": "Originality comes from combining existing things in new ways.",
                "I have no talent": "Talent is overrated. Consistent practice beats sporadic genius.",
            },
            "social": {
                "I'm awkward": "Social skills are learnable. Every interaction is practice.",
                "They don't like me": "Not everyone will. I can learn from feedback and keep growing.",
                "I'm bad at relationships": "Relationships are skills. I can get better with intention.",
                "I'm too introverted": "Introversion is a preference, not a prison. I can stretch when I choose.",
            },
            "athletic": {
                "I'm not athletic": "Athleticism is built, not born. Consistency matters more than genetics.",
                "I'll never be fit": "I'm becoming fitter every day I show up.",
                "I hate exercise": "I haven't found my movement yet. There are infinite options.",
                "I'm too old": "Age changes the timeline, not the possibility. Start where I am.",
            },
            "artistic": {
                "I can't draw/sing/write": "I haven't learned yet. Skill comes from deliberate practice.",
                "My work isn't good": "It's not good yet. Yet is the operative word.",
                "I'm not an artist": "Artist is a verb, not a noun. I art, therefore I am.",
                "No one cares about my art": "I care. That's enough to start. Audience builds with consistency.",
            },
            "leadership": {
                "I'm not a leader": "Leadership is influence. I influence people every day.",
                "I can't manage people": "Management is a skill. I'm learning it through experience.",
                "I make too many mistakes": "Leaders who don't make mistakes aren't leading enough.",
                "I'm not charismatic": "Charisma is learnable. Presence and listening matter more than charm.",
            },
        }

        domain_reframes = reframes.get(domain, reframes["intelligence"])
        growth_thought = domain_reframes.get(fixed_thought, "Every challenge is an opportunity to grow. What can I learn here?")

        return {
            "fixed": fixed_thought or "unspecified",
            "growth": growth_thought,
            "domain": domain or "general",
            "practice": "Write the growth thought 3 times. Say it aloud. Act as if it's true for one day.",
        }

    def get_growth_mindset_score(self) -> int:
        """Calculate overall growth mindset health (0-100)."""
        if not self._moments:
            return 45

        # Growth rate
        growth_count = sum(1 for m in self._moments if m.mindset_used == "growth")
        growth_rate = growth_count / len(self._moments)

        # Effort
        avg_effort = sum(m.effort_level for m in self._moments) / len(self._moments)

        # Strategy use
        avg_strategies = sum(m.strategy_count for m in self._moments) / len(self._moments)

        # Help seeking
        help_rate = sum(1 for m in self._moments if m.help_seeking) / len(self._moments)

        # Outcome improvement
        positive_outcomes = ["improved", "excelled", "persisted"]
        positive_rate = sum(1 for m in self._moments if m.outcome in positive_outcomes) / len(self._moments)

        # Recent trend
        moments_list = list(self._moments)
        recent = moments_list[-10:] if len(moments_list) >= 10 else moments_list
        recent_growth = sum(1 for m in recent if m.mindset_used == "growth") / len(recent)
        older_growth = sum(1 for m in moments_list[:-10] if m.mindset_used == "growth") / max(1, len(moments_list) - 10)
        trend = recent_growth - older_growth

        score = (growth_rate * 30) + (avg_effort * 20) + (min(avg_strategies, 3) * 5) + (help_rate * 15) + (positive_rate * 10) + (trend * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._moments:
            growth_count = sum(1 for m in self._moments if m.mindset_used == "growth")
            self._stats["growth_rate"] = round(growth_count / len(self._moments), 2)
            self._stats["avg_effort"] = round(sum(m.effort_level for m in self._moments) / len(self._moments), 2)
            self._stats["help_seeking_rate"] = round(sum(1 for m in self._moments if m.help_seeking) / len(self._moments), 2)

            by_domain = defaultdict(lambda: {"growth": 0, "total": 0})
            for m in self._moments:
                by_domain[m.domain]["total"] += 1
                if m.mindset_used == "growth":
                    by_domain[m.domain]["growth"] += 1
            
            if by_domain:
                hardest = min(by_domain.items(), key=lambda x: x[1]["growth"] / max(1, x[1]["total"]))
                self._stats["hardest_domain"] = hardest[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.growth_mindset_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.growth_mindset_coach")

    def _log_moment(self, moment: MindsetMoment):
        try:
            with open(MINDSET_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": moment.timestamp,
                    "trigger": moment.trigger,
                    "type": moment.trigger_type,
                    "domain": moment.domain,
                    "mindset": moment.mindset_used,
                    "outcome": moment.outcome,
                    "effort": moment.effort_level,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.growth_mindset_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gmc_instance: Optional[GrowthMindsetCoach] = None
_gmc_lock = threading.Lock()


def get_growth_mindset_coach() -> GrowthMindsetCoach:
    global _gmc_instance
    with _gmc_lock:
        if _gmc_instance is None:
            _gmc_instance = GrowthMindsetCoach()
        return _gmc_instance
