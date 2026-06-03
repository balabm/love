"""
LOVE Authenticity Amplifier — True Self Intelligence (Modern AI Pattern)

Most people perform versions of themselves. This amplifier:

1. AUTHENTICITY TRACKING
   - Record authentic moments and their characteristics
   - Track authenticity gaps (where performance exceeds reality)
   - Log authenticity costs (energy, relationships, wellbeing)

2. PATTERN ANALYSIS
   - Identify the user's authenticity profile (aligned, fragmented, exploring, recovering)
   - Find contexts where authenticity flourishes
   - Detect authenticity drains (where they feel they must perform)

3. AUTHENTICITY AMPLIFICATION
   - Suggest alignment practices matched to current gaps
   - Provide values-behavior congruence exercises
   - Recommendation boundary-setting practices

4. SELF-ALIGNMENT
   - Track the correlation between authenticity and energy
   - Alert when performance is becoming habitual
   - Celebrate moments of genuine self-expression

Architecture:
- record_moment(context, authenticity, cost, alignment): Log moment
- get_authenticity_stats(): Get authenticity pattern analysis
- get_authenticity_practice(gap, energy): Get practice
- get_authenticity_score(): Calculate overall authenticity health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "authenticity_amplifier"
DATA_DIR.mkdir(parents=True, exist_ok=True)

AUTHENTICITY_LOG = DATA_DIR / "moments.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AuthenticityMoment:
    """A tracked authenticity moment."""
    moment_id: str = ""
    context: str = ""  # work, social, family, alone, public, intimate
    authenticity: float = 0.5  # 0-1
    performance: float = 0.5  # 0-1, how much they were performing
    energy_cost: float = 0.0  # 0-1
    values_alignment: float = 0.5  # 0-1
    desired_response: str = ""  # what they wanted others to think
    true_self: str = ""  # who they actually were
    satisfaction: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AuthenticityAmplifier:
    """
    Intelligent authenticity amplifier with performance tracking and alignment exercises.
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
        self._moments: deque = deque(maxlen=300)
        self._stats = {
            "total_moments": 0,
            "avg_authenticity": 0.0,
            "avg_performance": 0.0,
            "performance_habit": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_moment(self, context: str = "", authenticity: float = 0.5, performance: float = 0.5, energy_cost: float = 0.0, values_alignment: float = 0.5, desired_response: str = "", true_self: str = "", satisfaction: float = 0.5, notes: str = "") -> AuthenticityMoment:
        """Record an authenticity moment."""
        moment_id = f"auth_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._moments)}"
        moment = AuthenticityMoment(
            moment_id=moment_id,
            context=context or "general",
            authenticity=authenticity,
            performance=performance,
            energy_cost=energy_cost,
            values_alignment=values_alignment,
            desired_response=desired_response,
            true_self=true_self,
            satisfaction=satisfaction,
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

    def get_authenticity_stats(self) -> Dict[str, Any]:
        """Get authenticity pattern analysis."""
        if not self._moments:
            return {"status": "insufficient_data"}

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "authenticity_sum": 0.0, "performance_sum": 0.0, "energy_sum": 0.0, "alignment_sum": 0.0, "satisfaction_sum": 0.0})
        for m in self._moments:
            by_context[m.context]["count"] += 1
            by_context[m.context]["authenticity_sum"] += m.authenticity
            by_context[m.context]["performance_sum"] += m.performance
            by_context[m.context]["energy_sum"] += m.energy_cost
            by_context[m.context]["alignment_sum"] += m.values_alignment
            by_context[m.context]["satisfaction_sum"] += m.satisfaction

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_authenticity": round(data["authenticity_sum"] / count, 2),
                "avg_performance": round(data["performance_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
                "avg_alignment": round(data["alignment_sum"] / count, 2),
                "avg_satisfaction": round(data["satisfaction_sum"] / count, 2),
            }

        authentic_contexts = sorted(context_stats.items(), key=lambda x: x[1]["avg_authenticity"], reverse=True)[:3]
        draining_contexts = sorted(context_stats.items(), key=lambda x: x[1]["avg_performance"] - x[1]["avg_authenticity"], reverse=True)[:3]

        # Performance habit detection
        recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_performance = sum(m.performance for m in recent) / len(recent)
            recent_authenticity = sum(m.authenticity for m in recent) / len(recent)
            performance_habit = recent_performance > recent_authenticity + 0.2
        else:
            performance_habit = False

        # Values-behavior gap
        values_gap = [m for m in self._moments if m.values_alignment < 0.4]
        values_gap_rate = len(values_gap) / len(self._moments)

        # Energy-authenticity correlation
        high_authenticity = [m for m in self._moments if m.authenticity > 0.7]
        low_authenticity = [m for m in self._moments if m.authenticity < 0.4]
        if high_authenticity and low_authenticity:
            high_auth_energy = sum(m.energy_cost for m in high_authenticity) / len(high_authenticity)
            low_auth_energy = sum(m.energy_cost for m in low_authenticity) / len(low_authenticity)
            energy_authenticity_correlation = low_auth_energy - high_auth_energy  # positive means authenticity saves energy
        else:
            energy_authenticity_correlation = 0

        # Satisfaction analysis
        high_satisfaction = [m for m in self._moments if m.satisfaction > 0.7]
        if high_satisfaction:
            high_sat_authenticity = sum(m.authenticity for m in high_satisfaction) / len(high_satisfaction)
        else:
            high_sat_authenticity = 0

        # Recent trend
        if recent:
            recent_authenticity_trend = sum(m.authenticity for m in recent) / len(recent)
            recent_performance_trend = sum(m.performance for m in recent) / len(recent)
            recent_satisfaction = sum(m.satisfaction for m in recent) / len(recent)
        else:
            recent_authenticity_trend = 0
            recent_performance_trend = 0
            recent_satisfaction = 0

        older = list(self._moments)[:-14] if len(self._moments) > 14 else []
        if older:
            older_authenticity = sum(m.authenticity for m in older) / len(older)
            older_performance = sum(m.performance for m in older) / len(older)
            authenticity_trend = recent_authenticity_trend - older_authenticity
            performance_trend = recent_performance_trend - older_performance
        else:
            authenticity_trend = 0
            performance_trend = 0

        return {
            "total_moments": len(self._moments),
            "context_stats": context_stats,
            "authentic_contexts": authentic_contexts,
            "draining_contexts": draining_contexts,
            "performance_habit": performance_habit,
            "values_gap_rate": round(values_gap_rate, 2),
            "energy_authenticity_correlation": round(energy_authenticity_correlation, 2),
            "high_satisfaction_authenticity": round(high_sat_authenticity, 2),
            "avg_authenticity": round(sum(m.authenticity for m in self._moments) / len(self._moments), 2),
            "avg_performance": round(sum(m.performance for m in self._moments) / len(self._moments), 2),
            "avg_energy": round(sum(m.energy_cost for m in self._moments) / len(self._moments), 2),
            "avg_alignment": round(sum(m.values_alignment for m in self._moments) / len(self._moments), 2),
            "authenticity_trend": round(authenticity_trend, 2),
            "performance_trend": round(performance_trend, 2),
            "recent_satisfaction": round(recent_satisfaction, 2),
        }

    def get_authenticity_practice(self, gap: str = "", energy: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "work": [
                "Say what you actually think in one meeting. Not everything. One thing. Small start.",
                "Stop apologizing for your expertise. Own it. 'I know this because...'",
                "Admit when you don't know. It's more respected than bluffing.",
            ],
            "social": [
                "Share one real thing about your day. Not the polished version. The real one.",
                "Say no to an invitation you don't want. No excuse needed. 'I can't make it.'",
                "Tell someone you appreciate them. Specific and genuine. Not generic.",
            ],
            "family": [
                "Express a need you usually suppress. 'I need...' not 'You should...'",
                "Share a fear with a family member. They want to know you, not your achievements.",
                "Set one boundary. 'I'm not available for that.' Love includes limits.",
            ],
            "public": [
                "Write or speak from your actual perspective. Not the one you think people want.",
                "Admit a mistake publicly. Accountability builds more trust than perfection.",
                "Share an unpopular opinion you hold. Respectfully. Truth is kind.",
            ],
            "intimate": [
                "Say what you want. Not what you think they want to hear.",
                "Share a insecurity. Let them see the real you. That's intimacy.",
                "Ask for what you need. Vulnerability in intimacy is strength.",
            ],
            "general": [
                "Notice when you're performing. Name it. 'I'm performing right now.' Awareness is the first step.",
                "Ask: 'What would I do if no one was watching?' Do that.",
                "Authenticity is not sharing everything. It's refusing to pretend. Start with refusal.",
            ],
        }

        selected = practices.get(gap, practices["general"])

        if energy < 0.3:
            energy_note = "Low energy. Performance is exhausting. Authenticity is energy-efficient. Try one small true thing."
        elif energy < 0.6:
            energy_note = "Moderate energy. Good time to practice authenticity where it's safe."
        else:
            energy_note = "Good energy. Expand your authentic range. Try contexts that used to require performance."

        return {
            "gap": gap or "general",
            "energy": energy,
            "practice": random.choice(selected),
            "energy_note": energy_note,
            "principle": "Authenticity is not a personality trait. It's a choice you make moment by moment. It's the decision to align your behavior with your values, your words with your thoughts, and your public self with your private self. The cost of inauthenticity is energy. The reward is peace.",
        }

    def get_authenticity_score(self) -> int:
        """Calculate overall authenticity health (0-100)."""
        if not self._moments:
            return 30

        # Authenticity and low performance
        avg_authenticity = sum(m.authenticity for m in self._moments) / len(self._moments)
        avg_performance = sum(m.performance for m in self._moments) / len(self._moments)

        # Values alignment
        avg_alignment = sum(m.values_alignment for m in self._moments) / len(self._moments)

        # Low energy cost
        avg_energy = sum(m.energy_cost for m in self._moments) / len(self._moments)

        # Satisfaction
        avg_satisfaction = sum(m.satisfaction for m in self._moments) / len(self._moments)

        # Context variety
        unique_contexts = len(set(m.context for m in self._moments))

        # Recent trend
        recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_authenticity = sum(m.authenticity for m in recent) / len(recent)
            recent_performance = sum(m.performance for m in recent) / len(recent)
            recent_satisfaction = sum(m.satisfaction for m in recent) / len(recent)
        else:
            recent_authenticity = 0
            recent_performance = 0
            recent_satisfaction = 0

        # Performance habit penalty
        performance_penalty = 10 if recent_performance > recent_authenticity + 0.2 else 0

        # Values gap penalty
        values_gap = [m for m in self._moments if m.values_alignment < 0.4]
        values_penalty = min(10, len(values_gap) / len(self._moments) * 10)

        score = (avg_authenticity * 25) + ((1 - avg_performance) * 15) + (avg_alignment * 20) + ((1 - avg_energy) * 10) + (avg_satisfaction * 10) + (unique_contexts * 2) + (recent_authenticity * 15) + (recent_satisfaction * 10) - performance_penalty - values_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._moments:
            self._stats["avg_authenticity"] = round(sum(m.authenticity for m in self._moments) / len(self._moments), 2)
            self._stats["avg_performance"] = round(sum(m.performance for m in self._moments) / len(self._moments), 2)

            recent = [m for m in self._moments if m.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if recent:
                recent_performance = sum(m.performance for m in recent) / len(recent)
                recent_authenticity = sum(m.authenticity for m in recent) / len(recent)
                self._stats["performance_habit"] = recent_performance > recent_authenticity + 0.2

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.authenticity_amplifier")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.authenticity_amplifier")

    def _log_moment(self, moment: AuthenticityMoment):
        try:
            with open(AUTHENTICITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": moment.timestamp,
                    "context": moment.context,
                    "authenticity": moment.authenticity,
                    "performance": moment.performance,
                    "energy_cost": moment.energy_cost,
                    "values_alignment": moment.values_alignment,
                    "desired_response": moment.desired_response,
                    "true_self": moment.true_self,
                    "satisfaction": moment.satisfaction,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.authenticity_amplifier")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_aa_instance: Optional[AuthenticityAmplifier] = None
_aa_lock = threading.Lock()


def get_authenticity_amplifier() -> AuthenticityAmplifier:
    global _aa_instance
    with _aa_lock:
        if _aa_instance is None:
            _aa_instance = AuthenticityAmplifier()
        return _aa_instance
