"""
LOVE Ritual Master — Ceremony Intelligence (Modern AI Pattern)

Most people have routines but no rituals. This master:

1. RITUAL TRACKING
   - Record rituals performed and their effects
   - Track ritual frequency, duration, and perceived meaningfulness
   - Log which rituals create transitions, which create meaning, which create protection

2. PATTERN ANALYSIS
   - Identify the user's ritual style (structured, spontaneous, symbolic, communal, solitary)
   - Find which rituals have the highest impact on mood, focus, and wellbeing
   - Detect ritual gaps (transitions without ceremony, losses without honoring)

3. RITUAL DESIGN
   - Suggest rituals for life transitions (beginnings, endings, changes)
   - Provide quick ritual formats for busy days
   - Recommend ritual elements matched to user style

4. TRANSITION MANAGEMENT
   - Track ritual effectiveness for work-life, sleep-wake, focus-rest transitions
   - Alert when transitions are rushed or missing
   - Celebrate well-executed transitions

Architecture:
- record_ritual(ritual, type, effect, duration): Log ritual
- get_ritual_stats(): Get ritual pattern analysis
- get_ritual_design(purpose, style, time): Get ritual plan
- get_ritual_score(): Calculate overall ritual health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "ritual_master"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RITUAL_LOG = DATA_DIR / "rituals.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Ritual:
    """A tracked ritual."""
    ritual_id: str = ""
    ritual: str = ""
    ritual_type: str = ""  # transition, meaning, protection, celebration, mourning, preparation, closure
    effect: float = 0.5  # 0-1
    meaningfulness: float = 0.5  # 0-1
    duration_minutes: float = 0.0
    transition: str = ""  # what transition this supports
    elements: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RitualMaster:
    """
    Intelligent ritual master with ceremony design and transition management.
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
        self._rituals: deque = deque(maxlen=200)
        self._stats = {
            "total_rituals": 0,
            "avg_effect": 0.0,
            "avg_meaningfulness": 0.0,
            "best_type": "",
            "favorite_elements": [],
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_ritual(self, ritual: str = "", ritual_type: str = "", effect: float = 0.5, meaningfulness: float = 0.5, duration: float = 0, transition: str = "", elements: Optional[List[str]] = None, notes: str = "") -> Ritual:
        """Record a ritual."""
        ritual_id = f"ritual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._rituals)}"
        r = Ritual(
            ritual_id=ritual_id,
            ritual=ritual or "unspecified",
            ritual_type=ritual_type or "transition",
            effect=effect,
            meaningfulness=meaningfulness,
            duration_minutes=duration,
            transition=transition,
            elements=elements or [],
            notes=notes,
        )

        with self._lock:
            self._rituals.append(r)
            self._stats["total_rituals"] += 1
            self._update_stats()

        self._save_stats()
        self._log_ritual(r)

        return r

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_ritual_stats(self) -> Dict[str, Any]:
        """Get ritual pattern analysis."""
        if not self._rituals:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "effect_sum": 0.0, "meaning_sum": 0.0})
        for r in self._rituals:
            by_type[r.ritual_type]["count"] += 1
            by_type[r.ritual_type]["effect_sum"] += r.effect
            by_type[r.ritual_type]["meaning_sum"] += r.meaningfulness

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
                "avg_meaningfulness": round(data["meaning_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_effect"] * x[1]["avg_meaningfulness"]) if type_stats else ("", {})

        # Transition analysis
        by_transition = defaultdict(lambda: {"count": 0, "effect_sum": 0.0})
        for r in self._rituals:
            if r.transition:
                by_transition[r.transition]["count"] += 1
                by_transition[r.transition]["effect_sum"] += r.effect

        transition_stats = {}
        for tr, data in by_transition.items():
            count = data["count"]
            transition_stats[tr] = {
                "count": count,
                "avg_effect": round(data["effect_sum"] / count, 2),
            }

        # Element analysis
        by_element = defaultdict(lambda: {"count": 0, "effect_sum": 0.0})
        for r in self._rituals:
            for el in r.elements:
                by_element[el]["count"] += 1
                by_element[el]["effect_sum"] += r.effect

        element_stats = {}
        for el, data in by_element.items():
            count = data["count"]
            if count >= 2:
                element_stats[el] = {
                    "count": count,
                    "avg_effect": round(data["effect_sum"] / count, 2),
                }

        favorite_elements = sorted(element_stats.items(), key=lambda x: x[1]["avg_effect"], reverse=True)[:3]

        # Duration sweet spot
        short = [r for r in self._rituals if r.duration_minutes <= 5]
        medium = [r for r in self._rituals if 5 < r.duration_minutes <= 20]
        long = [r for r in self._rituals if r.duration_minutes > 20]
        
        duration_effects = {}
        if short:
            duration_effects["short"] = round(sum(r.effect for r in short) / len(short), 2)
        if medium:
            duration_effects["medium"] = round(sum(r.effect for r in medium) / len(medium), 2)
        if long:
            duration_effects["long"] = round(sum(r.effect for r in long) / len(long), 2)

        return {
            "total_rituals": len(self._rituals),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "transition_stats": transition_stats,
            "element_stats": element_stats,
            "favorite_elements": [el[0] for el in favorite_elements],
            "duration_effects": duration_effects,
            "avg_effect": round(sum(r.effect for r in self._rituals) / len(self._rituals), 2),
            "avg_meaningfulness": round(sum(r.meaningfulness for r in self._rituals) / len(self._rituals), 2),
        }

    def get_ritual_design(self, purpose: str = "", style: str = "", time_available: float = 5) -> Dict[str, Any]:
        """Get ritual plan."""
        elements = {
            "lighting": ["Light a candle", "Dim the lights", "Open curtains to natural light", "Use colored light"],
            "sound": ["Ring a bell", "Play specific music", "Use silence", "Chant or hum"],
            "movement": ["Breathe deeply 3 times", "Stretch arms overhead", "Walk in a circle", "Bow or nod"],
            "object": ["Hold a meaningful object", "Write something down", "Burn or release something", "Place flowers"],
            "words": ["Say an intention aloud", "Read a poem or quote", "Name what you're grateful for", "Make a promise"],
            "space": ["Change location", "Clean or clear a surface", "Open a window", "Create an altar or focal point"],
        }

        if time_available <= 2:
            template = "Take one breath. Set one intention. Move forward."
        elif time_available <= 5:
            template = random.choice([
                "Light candle -> Breathe 3 times -> State intention -> Begin",
                "Stand up -> Stretch -> Say one sentence -> Move to next thing",
                "Close eyes -> Name one thing -> Open eyes -> Proceed",
            ])
        elif time_available <= 15:
            template = random.choice([
                "Prepare space -> Light candle -> Read poem -> Breathe -> Set intention -> Begin",
                "Clean surface -> Arrange objects -> Sit quietly -> Write intention -> Start",
                "Change clothes -> Make tea -> Sit by window -> Journal one sentence -> Transition",
            ])
        else:
            template = random.choice([
                "Full preparation: space, objects, music, words, movement, silence. Take your time. This matters.",
                "Create an environment of significance. Do things slowly. Let each action carry weight.",
                "Gather what you need. Arrange with care. Perform each step deliberately. Seal with silence.",
            ])

        if style == "minimal":
            selected_elements = ["movement", "words"]
        elif style == "sensory":
            selected_elements = ["lighting", "sound", "object"]
        elif style == "structured":
            selected_elements = ["space", "movement", "words", "object"]
        else:
            selected_elements = random.sample(list(elements.keys()), min(3, len(elements)))

        element_suggestions = []
        for el in selected_elements:
            element_suggestions.append(random.choice(elements[el]))

        purposes = {
            "morning": "Start the day with intention, not reaction.",
            "work_start": "Separate preparation from performance. Enter with presence.",
            "work_end": "Close the work mind. Open the life mind.",
            "evening": "Transition from doing to being. Prepare for rest.",
            "sleep": "Honor the day. Release what you carry. Welcome sleep.",
            "difficulty": "Acknowledge the hard thing. Gather your resources. Face it with dignity.",
            "celebration": "Mark the win. Let it land. Share the joy.",
            "loss": "Honor what was. Feel what is. Carry what remains.",
            "decision": "Center yourself. Name what matters. Choose with clarity.",
            "transition": "Close what was. Open what will be. Stand in the threshold.",
        }

        purpose_desc = purposes.get(purpose, "Create a moment of significance.")

        return {
            "purpose": purpose or "general",
            "style": style or "balanced",
            "time_available": time_available,
            "purpose_description": purpose_desc,
            "template": template,
            "elements": element_suggestions,
            "principle": "Rituals transform ordinary time into sacred time. They don't take time; they make time matter.",
        }

    def get_ritual_score(self) -> int:
        """Calculate overall ritual health (0-100)."""
        if not self._rituals:
            return 30

        # Effect
        avg_effect = sum(r.effect for r in self._rituals) / len(self._rituals)

        # Meaningfulness
        avg_meaning = sum(r.meaningfulness for r in self._rituals) / len(self._rituals)

        # Variety
        unique_types = len(set(r.ritual_type for r in self._rituals))
        unique_elements = len(set(el for r in self._rituals for el in r.elements))

        # Transition coverage
        transitions = set(r.transition for r in self._rituals if r.transition)
        transition_coverage = len(transitions)

        # Recent activity
        recent = [r for r in self._rituals if r.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        recent_bonus = min(15, len(recent) * 3)

        # Duration appropriateness (not too long, not too short)
        avg_duration = sum(r.duration_minutes for r in self._rituals) / len(self._rituals)
        duration_score = 1 - abs(avg_duration - 10) / 30  # optimal around 10 minutes

        score = (avg_effect * 25) + (avg_meaning * 20) + (unique_types * 3) + (unique_elements * 1) + (transition_coverage * 3) + recent_bonus + (duration_score * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._rituals:
            self._stats["avg_effect"] = round(sum(r.effect for r in self._rituals) / len(self._rituals), 2)
            self._stats["avg_meaningfulness"] = round(sum(r.meaningfulness for r in self._rituals) / len(self._rituals), 2)

            by_type = defaultdict(lambda: {"effect": 0.0, "meaning": 0.0, "count": 0})
            for r in self._rituals:
                by_type[r.ritual_type]["effect"] += r.effect
                by_type[r.ritual_type]["meaning"] += r.meaningfulness
                by_type[r.ritual_type]["count"] += 1
            if by_type:
                best = max(by_type.items(), key=lambda x: (x[1]["effect"] + x[1]["meaning"]) / max(1, x[1]["count"]))
                self._stats["best_type"] = best[0]

            by_element = defaultdict(lambda: {"effect": 0.0, "count": 0})
            for r in self._rituals:
                for el in r.elements:
                    by_element[el]["effect"] += r.effect
                    by_element[el]["count"] += 1
            if by_element:
                favorites = sorted(by_element.items(), key=lambda x: x[1]["effect"] / max(1, x[1]["count"]), reverse=True)[:3]
                self._stats["favorite_elements"] = [f[0] for f in favorites]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ritual_master")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ritual_master")

    def _log_ritual(self, ritual: Ritual):
        try:
            with open(RITUAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": ritual.timestamp,
                    "ritual": ritual.ritual,
                    "type": ritual.ritual_type,
                    "effect": ritual.effect,
                    "meaningfulness": ritual.meaningfulness,
                    "duration": ritual.duration_minutes,
                    "transition": ritual.transition,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.ritual_master")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rm_instance: Optional[RitualMaster] = None
_rm_lock = threading.Lock()


def get_ritual_master() -> RitualMaster:
    global _rm_instance
    with _rm_lock:
        if _rm_instance is None:
            _rm_instance = RitualMaster()
        return _rm_instance
