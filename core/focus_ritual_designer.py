"""
LOVE Focus Ritual Designer — Ritual Intelligence (Modern AI Pattern)

Most focus is ad-hoc and fragile. This designer:

1. RITUAL TRACKING
   - Record focus rituals and their effectiveness
   - Track ritual components (preparation, execution, recovery)
   - Log ritual adherence and its correlation with performance

2. PATTERN ANALYSIS
   - Identify the user's optimal ritual structure
   - Find which ritual components matter most
   - Detect ritual decay (when rituals lose effectiveness)

3. RITUAL DESIGN
   - Suggest personalized focus rituals for different contexts
   - Provide ritual templates for different work types
   - Recommend ritual evolution (when to refresh)

4. RITUAL CULTIVATION
   - Track ritual habit formation
   - Alert when rituals are being skipped
   - Celebrate ritual consistency

Architecture:
- record_ritual(name, components, duration, effectiveness): Log ritual
- get_ritual_stats(): Get ritual pattern analysis
- get_ritual_design(context, energy_level): Get design
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

DATA_DIR = Path(__file__).parent.parent / "data" / "focus_ritual_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RITUAL_LOG = DATA_DIR / "rituals.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RitualEntry:
    """A tracked ritual entry."""
    entry_id: str = ""
    name: str = ""
    context: str = ""  # deep_work, creative, analytical, administrative, collaborative
    components: List[str] = field(default_factory=list)
    duration_minutes: float = 0.0
    effectiveness: float = 0.5  # 0-1
    adherence: float = 0.5  # 0-1, how well they followed the ritual
    energy_before: float = 0.5  # 0-1
    energy_after: float = 0.5  # 0-1
    output_quality: float = 0.5  # 0-1
    skipped: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class FocusRitualDesigner:
    """
    Intelligent focus ritual designer with personalized design and decay detection.
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
            "avg_effectiveness": 0.0,
            "avg_adherence": 0.0,
            "best_context": "",
            "skip_rate": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_ritual(self, name: str = "", context: str = "", components: Optional[List[str]] = None, duration: float = 0, effectiveness: float = 0.5, adherence: float = 0.5, energy_before: float = 0.5, energy_after: float = 0.5, output_quality: float = 0.5, skipped: bool = False, notes: str = "") -> RitualEntry:
        """Record a ritual entry."""
        entry_id = f"rit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RitualEntry(
            entry_id=entry_id,
            name=name or "unspecified",
            context=context or "general",
            components=components or [],
            duration_minutes=duration,
            effectiveness=effectiveness,
            adherence=adherence,
            energy_before=energy_before,
            energy_after=energy_after,
            output_quality=output_quality,
            skipped=skipped,
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

    def get_ritual_stats(self) -> Dict[str, Any]:
        """Get ritual pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Context analysis
        by_context = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0, "adherence_sum": 0.0, "output_sum": 0.0, "skip_count": 0})
        for e in self._entries:
            by_context[e.context]["count"] += 1
            by_context[e.context]["effectiveness_sum"] += e.effectiveness
            by_context[e.context]["adherence_sum"] += e.adherence
            by_context[e.context]["output_sum"] += e.output_quality
            if e.skipped:
                by_context[e.context]["skip_count"] += 1

        context_stats = {}
        for c, data in by_context.items():
            count = data["count"]
            context_stats[c] = {
                "count": count,
                "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                "avg_adherence": round(data["adherence_sum"] / count, 2),
                "avg_output": round(data["output_sum"] / count, 2),
                "skip_rate": round(data["skip_count"] / count, 2),
            }

        best_context = max(context_stats.items(), key=lambda x: x[1]["avg_effectiveness"] * x[1]["avg_output"]) if context_stats else ("", {})

        # Component analysis
        by_component = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for e in self._entries:
            for comp in e.components:
                by_component[comp]["count"] += 1
                by_component[comp]["effectiveness_sum"] += e.effectiveness

        component_stats = {}
        for comp, data in by_component.items():
            count = data["count"]
            if count >= 2:
                component_stats[comp] = {
                    "count": count,
                    "avg_effectiveness": round(data["effectiveness_sum"] / count, 2),
                }

        best_components = sorted(component_stats.items(), key=lambda x: x[1]["avg_effectiveness"], reverse=True)[:5]

        # Ritual decay detection
        recent = list(self._entries)[-10:]
        if recent:
            recent_effectiveness = sum(e.effectiveness for e in recent) / len(recent)
        else:
            recent_effectiveness = 0
        older = list(self._entries)[:-10] if len(self._entries) > 10 else []
        if older:
            older_effectiveness = sum(e.effectiveness for e in older) / len(older)
            decay = older_effectiveness - recent_effectiveness > 0.15
        else:
            decay = False

        # Skip analysis
        skipped = sum(1 for e in self._entries if e.skipped)
        skip_rate = skipped / len(self._entries)

        # Duration analysis
        short = [e for e in self._entries if e.duration_minutes <= 5]
        long_ritual = [e for e in self._entries if e.duration_minutes > 15]
        if short and long_ritual:
            short_effectiveness = sum(e.effectiveness for e in short) / len(short)
            long_effectiveness = sum(e.effectiveness for e in long_ritual) / len(long_ritual)
            duration_insight = f"Short rituals: {short_effectiveness:.2f} effectiveness. Long rituals: {long_effectiveness:.2f} effectiveness."
        else:
            duration_insight = "insufficient_data"

        return {
            "total_entries": len(self._entries),
            "context_stats": context_stats,
            "best_context": best_context[0],
            "component_stats": component_stats,
            "best_components": best_components,
            "ritual_decay": decay,
            "skip_rate": round(skip_rate, 2),
            "avg_effectiveness": round(sum(e.effectiveness for e in self._entries) / len(self._entries), 2),
            "avg_adherence": round(sum(e.adherence for e in self._entries) / len(self._entries), 2),
            "duration_insight": duration_insight,
        }

    def get_ritual_design(self, context: str = "", energy_level: float = 0.5, available_time: float = 10) -> Dict[str, Any]:
        """Get design."""
        base_components = [
            "Clear workspace",
            "Close all non-essential apps",
            "Set a visible timer",
            "Write down the one thing you'll work on",
            "Take 3 deep breaths",
            "Put phone in another room",
            "Get water",
            "Play focus music (optional)",
        ]

        context_extras = {
            "deep_work": [
                "Enable Do Not Disturb on all devices",
                "Notify one person that you're entering deep work",
                "Review your 'not doing' list",
            ],
            "creative": [
                "Set a ridiculous constraint (one color, 100 words)",
                "Look at one inspiring image for 30 seconds",
                "Write 5 bad ideas. Quantity over quality.",
            ],
            "analytical": [
                "Write the question you're trying to answer",
                "Gather all relevant data before starting",
                "Define what 'done' looks like",
            ],
            "administrative": [
                "Batch similar tasks together",
                "Set a timer for 25 minutes. Race against it.",
                "Have a 'completion reward' ready",
            ],
            "collaborative": [
                "Review agenda before the session",
                "Set your intention for the interaction",
                "Prepare one question you want answered",
            ],
        }

        extras = context_extras.get(context, context_extras["deep_work"])

        if available_time <= 5:
            selected = ["Close all non-essential apps", "Set a visible timer", "Write down the one thing"]
            time_note = "Quick ritual. The basics matter more than the extras."
        elif available_time <= 10:
            selected = base_components[:5]
            time_note = "Standard ritual. Covers the essentials."
        else:
            selected = base_components + [random.choice(extras)]
            time_note = "Extended ritual. Use the extra time to set up perfectly."

        if energy_level < 0.3:
            energy_note = "Low energy. Shorten the ritual. The work matters more than the setup."
        elif energy_level < 0.6:
            energy_note = "Moderate energy. Standard ritual. Don't skip it."
        else:
            energy_note = "High energy. Use the ritual to channel energy productively."

        return {
            "context": context or "general",
            "energy_level": energy_level,
            "available_time": available_time,
            "components": selected,
            "time_note": time_note,
            "energy_note": energy_note,
            "principle": "Rituals are not superstition. They're behavioral triggers that prime your brain for a specific state. Design them deliberately.",
        }

    def get_ritual_score(self) -> int:
        """Calculate overall ritual health (0-100)."""
        if not self._entries:
            return 30

        # Effectiveness and adherence
        avg_effectiveness = sum(e.effectiveness for e in self._entries) / len(self._entries)
        avg_adherence = sum(e.adherence for e in self._entries) / len(self._entries)

        # Low skip rate
        skipped = sum(1 for e in self._entries if e.skipped)
        skip_rate = skipped / len(self._entries)

        # Output quality
        avg_output = sum(e.output_quality for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-10:]
        if recent:
            recent_effectiveness = sum(e.effectiveness for e in recent) / len(recent)
            recent_adherence = sum(e.adherence for e in recent) / len(recent)
        else:
            recent_effectiveness = 0
            recent_adherence = 0

        # Variety of contexts
        unique_contexts = len(set(e.context for e in self._entries))

        # Component richness
        all_components = set()
        for e in self._entries:
            all_components.update(e.components)

        score = (avg_effectiveness * 25) + (avg_adherence * 20) + ((1 - skip_rate) * 15) + (avg_output * 15) + (recent_effectiveness * 10) + (recent_adherence * 5) + (unique_contexts * 2) + (len(all_components) * 1)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_effectiveness"] = round(sum(e.effectiveness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_adherence"] = round(sum(e.adherence for e in self._entries) / len(self._entries), 2)

            skipped = sum(1 for e in self._entries if e.skipped)
            self._stats["skip_rate"] = round(skipped / len(self._entries), 2)

            by_context = defaultdict(lambda: {"effectiveness": 0.0, "output": 0.0, "count": 0})
            for e in self._entries:
                by_context[e.context]["effectiveness"] += e.effectiveness
                by_context[e.context]["output"] += e.output_quality
                by_context[e.context]["count"] += 1
            if by_context:
                best = max(by_context.items(), key=lambda x: (x[1]["effectiveness"] + x[1]["output"]) / max(1, x[1]["count"]))
                self._stats["best_context"] = best[0]

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

    def _log_entry(self, entry: RitualEntry):
        try:
            with open(RITUAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "name": entry.name,
                    "context": entry.context,
                    "duration": entry.duration_minutes,
                    "effectiveness": entry.effectiveness,
                    "adherence": entry.adherence,
                    "skipped": entry.skipped,
                    "output": entry.output_quality,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_frd_instance: Optional[FocusRitualDesigner] = None
_frd_lock = threading.Lock()


    
def get_focus_ritual_designer() -> FocusRitualDesigner:
    global _frd_instance
    with _frd_lock:
        if _frd_instance is None:
            _frd_instance = FocusRitualDesigner()
        return _frd_instance
