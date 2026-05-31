"""
LOVE Meaning Amplifier — Significance Intelligence (Modern AI Pattern)

Most experiences are neutral until meaning is assigned. This amplifier:

1. MEANING TRACKING
   - Record meaning assignments and their characteristics
   - Track meaning types (narrative, symbolic, relational, transcendent)
   - Log meaning shifts and their triggers

2. PATTERN ANALYSIS
   - Identify the user's meaning profile (maker, seeker, connector, witness)
   - Find meaning-making strategies that increase wellbeing
   - Detect meaning droughts and their causes

3. MEANING AMPLIFICATION
   - Suggest meaning-making practices matched to current experience
   - Provide narrative reframing exercises
   - Recommendation gratitude and ritual practices

4. SIGNIFICANCE CULTIVATION
   - Track the correlation between meaning and life satisfaction
   - Alert when experiences are being consumed without meaning extraction
   - Celebrate moments of profound significance

Architecture:
- record_experience(experience, meaning, type, significance): Log experience
- get_meaning_stats(): Get meaning pattern analysis
- get_meaning_practice(drought, domain): Get practice
- get_meaning_score(): Calculate overall meaning health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "meaning_amplifier"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MEANING_LOG = DATA_DIR / "experiences.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MeaningEntry:
    """A tracked meaning entry."""
    entry_id: str = ""
    experience: str = ""
    meaning: str = ""  # what meaning was assigned
    meaning_type: str = ""  # narrative, symbolic, relational, transcendent, growth
    significance: float = 0.5  # 0-1
    wellbeing_before: float = 0.5
    wellbeing_after: float = 0.5
    context: str = ""  # work, relationships, solitude, nature, challenge, routine
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MeaningAmplifier:
    """
    Intelligent meaning amplifier with drought detection and narrative enrichment.
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
            "avg_significance": 0.0,
            "avg_wellbeing_change": 0.0,
            "drought_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_experience(self, experience: str = "", meaning: str = "", meaning_type: str = "", significance: float = 0.5, wellbeing_before: float = 0.5, wellbeing_after: float = 0.5, context: str = "", notes: str = "") -> MeaningEntry:
        """Record a meaning entry."""
        entry_id = f"mean_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = MeaningEntry(
            entry_id=entry_id,
            experience=experience or "unspecified",
            meaning=meaning,
            meaning_type=meaning_type or "narrative",
            significance=significance,
            wellbeing_before=wellbeing_before,
            wellbeing_after=wellbeing_after,
            context=context or "general",
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

    def get_meaning_stats(self) -> Dict[str, Any]:
        """Get meaning pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "significance_sum": 0.0, "wellbeing_sum": 0.0})
        for e in self._entries:
            by_context[e.context]["count"] += 1
            by_context[e.context]["significance_sum"] += e.significance
            by_context[e.context]["wellbeing_sum"] += e.wellbeing_after - e.wellbeing_before

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_significance": round(data["significance_sum"] / count, 2),
                "avg_wellbeing_change": round(data["wellbeing_sum"] / count, 2),
            }

        # Meaning type analysis
        by_type = defaultdict(lambda: {"count": 0, "significance_sum": 0.0, "wellbeing_sum": 0.0})
        for e in self._entries:
            by_type[e.meaning_type]["count"] += 1
            by_type[e.meaning_type]["significance_sum"] += e.significance
            by_type[e.meaning_type]["wellbeing_sum"] += e.wellbeing_after - e.wellbeing_before

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_significance": round(data["significance_sum"] / count, 2),
                "avg_wellbeing_change": round(data["wellbeing_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_significance"] + x[1]["avg_wellbeing_change"]) if type_stats else ("", {})

        # Drought detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_significance = sum(e.significance for e in recent) / len(recent)
            low_significance = sum(1 for e in recent if e.significance < 0.4) / len(recent)
            drought_risk = recent_significance < 0.4 or low_significance > 0.5
        else:
            drought_risk = False

        # Wellbeing correlation
        avg_wellbeing_change = sum(e.wellbeing_after - e.wellbeing_before for e in self._entries) / len(self._entries)

        # Meaning assignment rate
        with_meaning = [e for e in self._entries if e.meaning]
        meaning_rate = len(with_meaning) / len(self._entries)

        # Recent trend
        if recent:
            recent_significance = sum(e.significance for e in recent) / len(recent)
            recent_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in recent) / len(recent)
        else:
            recent_significance = 0
            recent_wellbeing = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_significance = sum(e.significance for e in older) / len(older)
            older_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in older) / len(older)
            significance_trend = recent_significance - older_significance
            wellbeing_trend = recent_wellbeing - older_wellbeing
        else:
            significance_trend = 0
            wellbeing_trend = 0

        return {
            "total_entries": len(self._entries),
            "context_stats": context_stats,
            "type_stats": type_stats,
            "best_type": best_type[0],
            "drought_risk": drought_risk,
            "avg_significance": round(sum(e.significance for e in self._entries) / len(self._entries), 2),
            "avg_wellbeing_change": round(avg_wellbeing_change, 2),
            "meaning_rate": round(meaning_rate, 2),
            "significance_trend": round(significance_trend, 2),
            "wellbeing_trend": round(wellbeing_trend, 2),
            "recent_significance": round(recent_significance, 2),
            "recent_wellbeing": round(recent_wellbeing, 2),
        }

    def get_meaning_practice(self, drought: str = "", domain: str = "") -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "existential": [
                "Write your story from the third person. What would a biographer find meaningful?",
                "If this were your last week, what would matter? Do one of those things today.",
                "Ask: 'What am I building that will outlast me?' Even small things count.",
            ],
            "mundane": [
                "Pick one routine task. Do it as if it were a sacred ritual. Full attention.",
                "Find one beautiful thing in your ordinary day. A shadow. A sound. A texture.",
                "Thank one object that serves you. Your chair. Your pen. Your shoes. Silly, but it shifts perspective.",
            ],
            "suffering": [
                "This is hard. Ask: 'What is this teaching me?' Not to dismiss the pain. To find the meaning within it.",
                "Who else has been here? You're not alone in this experience. Connection is meaning.",
                "How will this shape who you become? The meaning of suffering is often retrospective.",
            ],
            "success": [
                "Celebrate fully. Don't rush to the next thing. Savor this moment of achievement.",
                "Who helped you get here? Gratitude amplifies meaning more than pride.",
                "What does this success mean about what matters to you? Follow that thread.",
            ],
            "transition": [
                "Endings are meaning-rich. What are you leaving? What are you carrying forward?",
                "Ritualize the transition. A small ceremony. A written reflection. A kept object.",
                "What is possible now that wasn't before? New beginnings carry fresh meaning.",
            ],
            "general": [
                "Ask 'So what?' about anything you're doing. If the answer is empty, reconsider. If it's full, dig deeper.",
                "Connect today's action to a larger story. You're not just sending an email. You're building trust.",
                "Meaning is not found. It's made. Choose to assign significance. It's a creative act.",
            ],
        }

        selected = practices.get(drought, practices["general"])

        if drought == "existential":
            drought_note = "Existential drought is the deepest. It asks: 'Why anything?' The answer is not in thinking. It's in doing what makes you feel alive."
        elif drought == "mundane":
            drought_note = "The mundane is not meaningless. It's where meaning hides. Look closer."
        elif drought == "suffering":
            drought_note = "Suffering is not inherently meaningful. But meaning can be extracted from it. That's the work."
        elif drought == "success":
            drought_note = "Success without meaning is hollow. The work now is integration, not accumulation."
        elif drought == "transition":
            drought_note = "Transitions are liminal spaces. Rich with potential meaning. Don't rush through them."
        else:
            drought_note = "Meaning is a practice, not a state. Assign significance deliberately. It's a muscle."

        return {
            "drought": drought or "none",
            "domain": domain or "general",
            "practice": random.choice(selected),
            "drought_note": drought_note,
            "principle": "Meaning is not what happens to you. It's what you make of what happens to you. Two people can live identical lives and find them either meaningless or profoundly significant. The difference is not the life. It's the attention, the narrative, and the choice to care.",
        }

    def get_meaning_score(self) -> int:
        """Calculate overall meaning health (0-100)."""
        if not self._entries:
            return 30

        # Significance and wellbeing
        avg_significance = sum(e.significance for e in self._entries) / len(self._entries)
        avg_wellbeing_change = sum(e.wellbeing_after - e.wellbeing_before for e in self._entries) / len(self._entries)

        # Meaning assignment rate
        with_meaning = [e for e in self._entries if e.meaning]
        meaning_rate = len(with_meaning) / len(self._entries)

        # Context variety
        unique_contexts = len(set(e.context for e in self._entries))

        # Type variety
        unique_types = len(set(e.meaning_type for e in self._entries))

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_significance = sum(e.significance for e in recent) / len(recent)
            recent_wellbeing = sum(e.wellbeing_after - e.wellbeing_before for e in recent) / len(recent)
        else:
            recent_significance = 0
            recent_wellbeing = 0

        # Drought penalty
        if recent:
            low_significance = sum(1 for e in recent if e.significance < 0.4) / len(recent)
            drought_penalty = 10 if (recent_significance < 0.4 or low_significance > 0.5) else 0
        else:
            drought_penalty = 0

        # Depth (wellbeing improvement)
        positive_experiences = [e for e in self._entries if e.wellbeing_after > e.wellbeing_before]
        depth_score = len(positive_experiences) / len(self._entries)

        score = (avg_significance * 25) + (avg_wellbeing_change * 15) + (meaning_rate * 15) + (unique_contexts * 2) + (unique_types * 2) + (recent_significance * 15) + (recent_wellbeing * 10) + (depth_score * 10) - drought_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_significance"] = round(sum(e.significance for e in self._entries) / len(self._entries), 2)
            self._stats["avg_wellbeing_change"] = round(sum(e.wellbeing_after - e.wellbeing_before for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if recent:
                recent_significance = sum(e.significance for e in recent) / len(recent)
                low_significance = sum(1 for e in recent if e.significance < 0.4) / len(recent)
                self._stats["drought_risk"] = recent_significance < 0.4 or low_significance > 0.5

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

    def _log_entry(self, entry: MeaningEntry):
        try:
            with open(MEANING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "experience": entry.experience,
                    "meaning": entry.meaning,
                    "meaning_type": entry.meaning_type,
                    "significance": entry.significance,
                    "wellbeing_before": entry.wellbeing_before,
                    "wellbeing_after": entry.wellbeing_after,
                    "context": entry.context,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ma_instance: Optional[MeaningAmplifier] = None
_ma_lock = threading.Lock()


def get_meaning_amplifier() -> MeaningAmplifier:
    global _ma_instance
    with _ma_lock:
        if _ma_instance is None:
            _ma_instance = MeaningAmplifier()
        return _ma_instance
