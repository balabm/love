"""
LOVE Speech Craft Coach — Rhetorical Intelligence (Modern AI Pattern)

Most people speak without crafting. This coach:

1. SPEECH TRACKING
   - Record speech craft moments and their characteristics
   - Track craft types (opening, argument, evidence, transition, closing, call_to_action)
   - Log structure, clarity, persuasion, memorability, and impact of speech craft

2. PATTERN ANALYSIS
   - Identify the user's craft profile (rambling, disorganized, developing, masterful)
   - Find craft patterns that create clarity vs confusion
   - Detect chronic structurelessness and its costs

3. CRAFT BUILDING
   - Suggest practices for structuring compelling communication
   - Provide frameworks for openings, transitions, and closings
   - Recommend practices for rhetorical effectiveness

4. RHETORICAL MASTERY CULTIVATION
   - Track the correlation between speech craft and audience impact
   - Alert when stream-of-consciousness is replacing intentionality
   - Celebrate moments of genuine rhetorical brilliance

Architecture:
- record_speech(section, type, structure, clarity, persuasion, memorability, impact): Log speech
- get_speech_stats(): Get speech pattern analysis
- get_speech_suggestion(capacity, context): Get suggestion
- get_speech_score(): Calculate overall speech health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "speech_craft_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SPEECH_LOG = DATA_DIR / "speeches.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SpeechEntry:
    """A tracked speech craft moment."""
    entry_id: str = ""
    section: str = ""  # what section was crafted
    speech_type: str = ""  # opening, argument, evidence, transition, closing, call_to_action
    structure: float = 0.0  # 0-1
    clarity: float = 0.0  # 0-1
    persuasion: float = 0.0  # 0-1
    memorability: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    intention: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SpeechCraftCoach:
    """
    Intelligent speech craft coach with structurelessness detection and rhetorical mastery cultivation.
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
            "avg_structure": 0.0,
            "avg_impact": 0.0,
            "structurelessness_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_speech(self, section: str = "", speech_type: str = "", structure: float = 0.0, clarity: float = 0.0, persuasion: float = 0.0, memorability: float = 0.0, impact: float = 0.0, intention: float = 0.0, notes: str = "") -> SpeechEntry:
        """Record a speech craft moment."""
        entry_id = f"spc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SpeechEntry(
            entry_id=entry_id,
            section=section or "unspecified",
            speech_type=speech_type or "opening",
            structure=structure,
            clarity=clarity,
            persuasion=persuasion,
            memorability=memorability,
            impact=impact,
            intention=intention,
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

    def get_speech_stats(self) -> Dict[str, Any]:
        """Get speech pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "structure_sum": 0.0, "clarity_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            by_type[e.speech_type]["count"] += 1
            by_type[e.speech_type]["structure_sum"] += e.structure
            by_type[e.speech_type]["clarity_sum"] += e.clarity
            by_type[e.speech_type]["impact_sum"] += e.impact

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_structure": round(data["structure_sum"] / count, 2),
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Structure analysis
        high_str = [e for e in self._entries if e.structure > 0.7]
        low_str = [e for e in self._entries if e.structure < 0.4]
        if high_str and low_str:
            high_str_imp = sum(e.impact for e in high_str) / len(high_str)
            low_str_imp = sum(e.impact for e in low_str) / len(low_str)
            high_str_mem = sum(e.memorability for e in high_str) / len(high_str)
            low_str_mem = sum(e.memorability for e in low_str) / len(low_str)
        else:
            high_str_imp = 0
            low_str_imp = 0
            high_str_mem = 0
            low_str_mem = 0

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_clar = sum(e.clarity for e in high_int) / len(high_int)
            low_int_clar = sum(e.clarity for e in low_int) / len(low_int)
        else:
            high_int_clar = 0
            low_int_clar = 0

        # Structurelessness risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_str = sum(e.structure for e in recent) / len(recent)
            recent_imp = sum(e.impact for e in recent) / len(recent)
            structurelessness_risk = recent_str < 0.3 and recent_imp < 0.3
        else:
            structurelessness_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "structure_impact": {
                "high_structure_impact": round(high_str_imp, 2),
                "low_structure_impact": round(low_str_imp, 2),
                "high_structure_memorability": round(high_str_mem, 2),
                "low_structure_memorability": round(low_str_mem, 2),
            },
            "intention_effect": {
                "high_intention_clarity": round(high_int_clar, 2),
                "low_intention_clarity": round(low_int_clar, 2),
            },
            "structurelessness_risk": structurelessness_risk,
            "avg_structure": round(sum(e.structure for e in self._entries) / len(self._entries), 2),
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 2),
        }

    def get_speech_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get speech suggestion."""
        suggestions = [
            "Structure is not a cage. It's a skeleton. It holds your ideas up so they can walk. The person who speaks without structure is not free. They're lost. And they lose their audience with them.",
            "Open with impact. Not with apology. Not with throat-clearing. Not with 'so, um, basically...' Start strong. A story. A question. A startling fact. A bold claim. Give them a reason to listen in the first ten seconds.",
            "One idea at a time. Not three. Not five. One. Develop it. Illustrate it. Land it. Then move to the next. The person who tries to say everything says nothing. The person who says one thing well changes minds.",
            "Use transitions. Don't just jump. 'Now that we've seen X, let's consider Y.' 'This leads us to...' 'But there's another side.' Transitions are bridges. Without them, your audience falls into the river.",
            "Support with evidence. Not just opinion. A story. A statistic. An example. A quote. Evidence makes your argument credible. And credibility makes your argument persuasive.",
            "Close with purpose. Don't just stop. Summarize. Call to action. Leave them with something. The closing is the last thing they hear. And the last thing they hear is the first thing they remember.",
            "Repeat the important. Not everything. Just the important. The key message. The core idea. The central claim. Repetition creates memory. And memory creates action.",
            "Use contrast. Not to manipulate. To clarify. 'Most people think X. But the truth is Y.' Contrast creates mental hooks. It makes ideas sticky. It makes arguments compelling.",
            "Speak in threes. Not twos. Not fours. Threes. 'Life, liberty, and the pursuit of happiness.' 'Blood, sweat, and tears.' Three is the magic number of rhetoric. Use it.",
            "The person who crafts their speech is not being artificial. They're being respectful. Respectful of their audience's time. Their attention. Their intelligence. Craft is care. And care is love made audible."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One opening crafted. One transition planned. One closing designed. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A structured argument. A clear transition. A memorable close. A call to action added. Medium craft."
        else:
            capacity_note = "Good capacity. Deep rhetorical work. A systematic practice of speech craft from opening to close. You have the strength to move minds with words."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Speech craft is not about being eloquent. It's about being clear. Most people speak as they think. In streams. With digressions. With returns. With parentheses. And they wonder why nobody follows. Why nobody remembers. Why nobody acts. The work of speech craft coaching is about understanding that communication is architecture. That ideas need structure to stand. That openings need hooks. That transitions need bridges. That evidence needs support. That closings need purpose. And that the person who crafts their communication is not being inauthentic. They're being respectful. Of their audience's time. Of their audience's attention. Of their audience's intelligence. Because the uncrafted speech wastes all three. And the crafted speech honors them."
        }

    def get_speech_score(self) -> int:
        """Calculate overall speech health (0-100)."""
        if not self._entries:
            return 25

        avg_str = sum(e.structure for e in self._entries) / len(self._entries)
        avg_clar = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_pers = sum(e.persuasion for e in self._entries) / len(self._entries)
        avg_mem = sum(e.memorability for e in self._entries) / len(self._entries)
        avg_imp = sum(e.impact for e in self._entries) / len(self._entries)
        avg_int = sum(e.intention for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_str = sum(e.structure for e in recent) / len(recent)
            recent_imp = sum(e.impact for e in recent) / len(recent)
        else:
            recent_str = 0
            recent_imp = 0

        # Structurelessness penalty
        struct_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_str_30 = sum(e.structure for e in last_30) / len(last_30)
            recent_imp_30 = sum(e.impact for e in last_30) / len(last_30)
            if recent_str_30 < 0.3 and recent_imp_30 < 0.3:
                struct_penalty = 15

        # Type variety
        unique_types = len(set(e.speech_type for e in self._entries))

        score = (avg_str * 25) + (avg_clar * 15) + (avg_pers * 10) + (avg_mem * 10) + (avg_imp * 15) + (avg_int * 10) + (recent_str * 5) + (recent_imp * 5) + (unique_types * 2) - struct_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_structure"] = round(sum(e.structure for e in self._entries) / len(self._entries), 2)
            self._stats["avg_impact"] = round(sum(e.impact for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_str = sum(e.structure for e in recent) / len(recent)
                recent_imp = sum(e.impact for e in recent) / len(recent)
                self._stats["structurelessness_risk"] = recent_str < 0.3 and recent_imp < 0.3
            else:
                self._stats["structurelessness_risk"] = False

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

    def _log_entry(self, entry: SpeechEntry):
        try:
            with open(SPEECH_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "section": entry.section,
                    "speech_type": entry.speech_type,
                    "structure": entry.structure,
                    "impact": entry.impact,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_scc_instance: Optional[SpeechCraftCoach] = None
_scc_lock = threading.Lock()


def get_speech_craft_coach() -> SpeechCraftCoach:
    global _scc_instance
    with _scc_lock:
        if _scc_instance is None:
            _scc_instance = SpeechCraftCoach()
        return _scc_instance
