"""
LOVE Visual Storytelling Coach — Visual Narrative Intelligence (Modern AI Pattern)

Most people share photos without story. This coach:

1. STORY TRACKING
   - Record visual storytelling moments and their characteristics
   - Track story types (sequence, contrast, progression, journey, transformation, emotion)
   - Log narrative, composition, emotion, continuity, and impact of visual stories

2. PATTERN ANALYSIS
   - Identify the user's storytelling profile (random, descriptive, developing, narrative)
   - Find storytelling patterns that create meaning vs noise
   - Detect chronic visual rambling and its costs

3. STORY BUILDING
   - Suggest practices for telling stories with images
   - Provide frameworks for visual sequences and arcs
   - Recommend practices for image-as-narrative

4. VISUAL NARRATIVE MASTERY CULTIVATION
   - Track the correlation between storytelling craft and emotional impact
   - Alert when dumping is replacing storytelling
   - Celebrate moments of genuine visual narrative power

Architecture:
- record_story(series, type, narrative, composition, emotion, continuity, impact): Log story
- get_story_stats(): Get story pattern analysis
- get_story_suggestion(capacity, context): Get suggestion
- get_story_score(): Calculate overall story health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "visual_storytelling_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STORY_LOG = DATA_DIR / "stories.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class StoryEntry:
    """A tracked visual storytelling moment."""
    entry_id: str = ""
    series: str = ""  # what series was created
    story_type: str = ""  # sequence, contrast, progression, journey, transformation, emotion
    narrative: float = 0.0  # 0-1
    composition: float = 0.0  # 0-1
    emotion: float = 0.0  # 0-1
    continuity: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    intention: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VisualStorytellingCoach:
    """
    Intelligent visual storytelling coach with rambling detection and visual narrative mastery cultivation.
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
            "avg_narrative": 0.0,
            "avg_impact": 0.0,
            "rambling_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_story(self, series: str = "", story_type: str = "", narrative: float = 0.0, composition: float = 0.0, emotion: float = 0.0, continuity: float = 0.0, impact: float = 0.0, intention: float = 0.0, notes: str = "") -> StoryEntry:
        """Record a visual storytelling moment."""
        entry_id = f"vst_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = StoryEntry(
            entry_id=entry_id,
            series=series or "unspecified",
            story_type=story_type or "sequence",
            narrative=narrative,
            composition=composition,
            emotion=emotion,
            continuity=continuity,
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

    def get_story_stats(self) -> Dict[str, Any]:
        """Get story pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "narrative_sum": 0.0, "composition_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            by_type[e.story_type]["count"] += 1
            by_type[e.story_type]["narrative_sum"] += e.narrative
            by_type[e.story_type]["composition_sum"] += e.composition
            by_type[e.story_type]["impact_sum"] += e.impact

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_narrative": round(data["narrative_sum"] / count, 2),
                "avg_composition": round(data["composition_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Narrative analysis
        high_nar = [e for e in self._entries if e.narrative > 0.7]
        low_nar = [e for e in self._entries if e.narrative < 0.4]
        if high_nar and low_nar:
            high_nar_imp = sum(e.impact for e in high_nar) / len(high_nar)
            low_nar_imp = sum(e.impact for e in low_nar) / len(low_nar)
            high_nar_emo = sum(e.emotion for e in high_nar) / len(high_nar)
            low_nar_emo = sum(e.emotion for e in low_nar) / len(low_nar)
        else:
            high_nar_imp = 0
            low_nar_imp = 0
            high_nar_emo = 0
            low_nar_emo = 0

        # Continuity analysis
        high_cont = [e for e in self._entries if e.continuity > 0.7]
        low_cont = [e for e in self._entries if e.continuity < 0.4]
        if high_cont and low_cont:
            high_cont_imp = sum(e.impact for e in high_cont) / len(high_cont)
            low_cont_imp = sum(e.impact for e in low_cont) / len(low_cont)
        else:
            high_cont_imp = 0
            low_cont_imp = 0

        # Rambling risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_nar = sum(e.narrative for e in recent) / len(recent)
            recent_imp = sum(e.impact for e in recent) / len(recent)
            rambling_risk = recent_nar < 0.3 and recent_imp < 0.3
        else:
            rambling_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "narrative_impact": {
                "high_narrative_impact": round(high_nar_imp, 2),
                "low_narrative_impact": round(low_nar_imp, 2),
                "high_narrative_emotion": round(high_nar_emo, 2),
                "low_narrative_emotion": round(low_nar_emo, 2),
            },
            "continuity_effect": {
                "high_continuity_impact": round(high_cont_imp, 2),
                "low_continuity_impact": round(low_cont_imp, 2),
            },
            "rambling_risk": rambling_risk,
            "avg_narrative": round(sum(e.narrative for e in self._entries) / len(self._entries), 2),
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 2),
        }

    def get_story_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get story suggestion."""
        suggestions = [
            "A photo is a sentence. A series is a story. Most people share sentences and call it a story. But a story has arc. It has change. It has beginning, middle, end. Don't share photos. Share stories.",
            "Sequence matters. The order of images is the order of meaning. First image: establish. Middle images: develop. Final image: resolve. Or don't resolve. But have an order. Random is not narrative.",
            "Use contrast. Light and dark. Before and after. Close and far. Old and young. Contrast creates tension. Tension creates interest. Interest creates engagement. And engagement creates memory.",
            "Show the journey. Not just the destination. The packing. The travel. The arrival. The struggle. The celebration. The return. Journeys are universal. Everyone understands a journey.",
            "Find the emotion. Not the spectacle. The quiet moment. The tear. The laugh. The glance. The touch. Emotion is what people remember. Not the view. Not the building. The feeling.",
            "Progression tells story. Seed. Sprout. Plant. Flower. Fruit. Decay. This is life. This is story. Show change over time. Show growth. Show transformation. That's what stories do.",
            "Limit your series. Three to seven images. Not fifty. Not two hundred. Curate ruthlessly. Each image must earn its place. If it doesn't advance the story, it doesn't belong.",
            "Write the story first. In your head. On paper. Then choose the images that tell it. The story guides the images. Not the other way around. Story is king. Images are servants.",
            "Share with intention. Not reflex. 'This is the story of...' 'Here's what happened...' 'This changed everything...' Context creates meaning. And meaning creates connection.",
            "The person who tells visual stories is not just sharing images. They're sharing meaning. They're sharing experience. They're saying 'this is what life looks like to me.' And that is the most generous thing you can do."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One three-image sequence. One contrast noticed. One emotion captured. One story told. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A visual arc created. A journey documented. A transformation shown. A series curated with care. Medium storytelling."
        else:
            capacity_note = "Good capacity. Deep visual narrative work. A systematic practice of telling stories through images. You have the strength to make people see what you see."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Visual storytelling is not about having a good camera. It's about having something to say. Most people share images without narrative. They dump photos. They post randomly. They share moments without meaning. And they wonder why nobody cares. Why nobody engages. Why nobody remembers. The work of visual storytelling coaching is about understanding that images are language. And like any language, they have grammar. They have structure. They have meaning. A single image is a word. A sequence is a sentence. A curated series is a story. And the person who learns to tell stories visually is not just a photographer. They're a communicator. They're an artist. They're someone who can make others see the world through their eyes. And that is a power worth cultivating."
        }

    def get_story_score(self) -> int:
        """Calculate overall story health (0-100)."""
        if not self._entries:
            return 25

        avg_nar = sum(e.narrative for e in self._entries) / len(self._entries)
        avg_comp = sum(e.composition for e in self._entries) / len(self._entries)
        avg_emo = sum(e.emotion for e in self._entries) / len(self._entries)
        avg_cont = sum(e.continuity for e in self._entries) / len(self._entries)
        avg_imp = sum(e.impact for e in self._entries) / len(self._entries)
        avg_int = sum(e.intention for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_nar = sum(e.narrative for e in recent) / len(recent)
            recent_imp = sum(e.impact for e in recent) / len(recent)
        else:
            recent_nar = 0
            recent_imp = 0

        # Rambling penalty
        ram_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_nar_30 = sum(e.narrative for e in last_30) / len(last_30)
            recent_imp_30 = sum(e.impact for e in last_30) / len(last_30)
            if recent_nar_30 < 0.3 and recent_imp_30 < 0.3:
                ram_penalty = 15

        # Type variety
        unique_types = len(set(e.story_type for e in self._entries))

        score = (avg_nar * 25) + (avg_comp * 10) + (avg_emo * 15) + (avg_cont * 10) + (avg_imp * 20) + (avg_int * 10) + (recent_nar * 5) + (recent_imp * 5) + (unique_types * 2) - ram_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_narrative"] = round(sum(e.narrative for e in self._entries) / len(self._entries), 2)
            self._stats["avg_impact"] = round(sum(e.impact for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_nar = sum(e.narrative for e in recent) / len(recent)
                recent_imp = sum(e.impact for e in recent) / len(recent)
                self._stats["rambling_risk"] = recent_nar < 0.3 and recent_imp < 0.3
            else:
                self._stats["rambling_risk"] = False

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

    def _log_entry(self, entry: StoryEntry):
        try:
            with open(STORY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "series": entry.series,
                    "story_type": entry.story_type,
                    "narrative": entry.narrative,
                    "impact": entry.impact,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vsc_instance: Optional[VisualStorytellingCoach] = None
_vsc_lock = threading.Lock()


def get_visual_storytelling_coach() -> VisualStorytellingCoach:
    global _vsc_instance
    with _vsc_lock:
        if _vsc_instance is None:
            _vsc_instance = VisualStorytellingCoach()
        return _vsc_instance
