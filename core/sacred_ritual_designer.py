"""
LOVE Sacred Ritual Designer — Ceremony Intelligence (Modern AI Pattern)

Most modern life lacks sacred structure. This designer:

1. RITUAL TRACKING
   - Record rituals and their characteristics
   - Track ritual types (daily, weekly, seasonal, life transition, grief, celebration)
   - Log engagement and transformation outcomes

2. PATTERN ANALYSIS
   - Identify the user's ritual profile (absent, sporadic, habitual, sacred)
   - Find ritual elements that create depth and meaning
   - Detect empty repetition vs genuine ritual

3. RITUAL BUILDING
   - Suggest rituals matched to current life context and need
   - Provide design and facilitation frameworks
   - Recommendation symbolism and intention practices

4. CEREMONY CULTIVATION
   - Track the correlation between ritual and life transition support
   - Alert when rituals are becoming rote
   - Celebrate moments of genuine sacred experience

Architecture:
- record_ritual(name, type, elements, engagement, transformation): Log ritual
- get_ritual_stats(): Get ritual pattern analysis
- get_ritual_design(occasion, participants, intention): Get design
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

DATA_DIR = Path(__file__).parent.parent / "data" / "sacred_ritual_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RITUAL_LOG = DATA_DIR / "rituals.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RitualEntry:
    """A tracked ritual entry."""
    entry_id: str = ""
    name: str = ""  # ritual name
    ritual_type: str = ""  # daily, weekly, seasonal, transition, grief, celebration
    elements: int = 0  # number of symbolic elements
    engagement: float = 0.5  # 0-1, how present were participants
    intention: float = 0.5  # 0-1, how clear was the intention
    transformation: float = 0.0  # 0-1, did it create change
    rote: bool = False  # was it empty repetition
    participants: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SacredRitualDesigner:
    """
    Intelligent sacred ritual designer with meaning tracking and rote detection.
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
            "avg_engagement": 0.0,
            "avg_transformation": 0.0,
            "rote_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_ritual(self, name: str = "", ritual_type: str = "", elements: int = 0, engagement: float = 0.5, intention: float = 0.5, transformation: float = 0.0, rote: bool = False, participants: int = 1, notes: str = "") -> RitualEntry:
        """Record a ritual entry."""
        entry_id = f"rit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RitualEntry(
            entry_id=entry_id,
            name=name or "unspecified",
            ritual_type=ritual_type or "daily",
            elements=elements,
            engagement=engagement,
            intention=intention,
            transformation=transformation,
            rote=rote,
            participants=participants,
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

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "eng_sum": 0.0, "int_sum": 0.0, "trans_sum": 0.0, "elements_sum": 0, "rote_count": 0})
        for e in self._entries:
            by_type[e.ritual_type]["count"] += 1
            by_type[e.ritual_type]["eng_sum"] += e.engagement
            by_type[e.ritual_type]["int_sum"] += e.intention
            by_type[e.ritual_type]["trans_sum"] += e.transformation
            by_type[e.ritual_type]["elements_sum"] += e.elements
            if e.rote:
                by_type[e.ritual_type]["rote_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_engagement": round(data["eng_sum"] / count, 2),
                "avg_intention": round(data["int_sum"] / count, 2),
                "avg_transformation": round(data["trans_sum"] / count, 2),
                "avg_elements": round(data["elements_sum"] / count, 1),
                "rote_rate": round(data["rote_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_transformation"]) if type_stats else ("", {})

        # Elements analysis
        high_elem = [e for e in self._entries if e.elements > 4]
        low_elem = [e for e in self._entries if e.elements < 2]
        if high_elem and low_elem:
            high_elem_trans = sum(e.transformation for e in high_elem) / len(high_elem)
            low_elem_trans = sum(e.transformation for e in low_elem) / len(low_elem)
            high_elem_eng = sum(e.engagement for e in high_elem) / len(high_elem)
            low_elem_eng = sum(e.engagement for e in low_elem) / len(low_elem)
        else:
            high_elem_trans = 0
            low_elem_trans = 0
            high_elem_eng = 0
            low_elem_eng = 0

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_trans = sum(e.transformation for e in high_int) / len(high_int)
            low_int_trans = sum(e.transformation for e in low_int) / len(low_int)
        else:
            high_int_trans = 0
            low_int_trans = 0

        # Rote vs engaged
        rote = [e for e in self._entries if e.rote]
        engaged = [e for e in self._entries if not e.rote]
        if rote and engaged:
            rote_trans = sum(e.transformation for e in rote) / len(rote)
            engaged_trans = sum(e.transformation for e in engaged) / len(engaged)
            rote_eng = sum(e.engagement for e in rote) / len(rote)
            engaged_eng = sum(e.engagement for e in engaged) / len(engaged)
        else:
            rote_trans = 0
            engaged_trans = 0
            rote_eng = 0
            engaged_eng = 0

        # Rote detection
        recent = list(self._entries)[-14:]
        if recent:
            recent_rote = sum(1 for e in recent if e.rote) / len(recent)
            recent_eng = sum(e.engagement for e in recent) / len(recent)
            rote_risk = recent_rote > 0.3 or recent_eng < 0.4
        else:
            rote_risk = False

        # Recent trend
        if recent:
            recent_intention = sum(e.intention for e in recent) / len(recent)
            recent_trans = sum(e.transformation for e in recent) / len(recent)
        else:
            recent_intention = 0
            recent_trans = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_eng = sum(e.engagement for e in older) / len(older)
            older_trans = sum(e.transformation for e in older) / len(older)
            eng_trend = recent_eng - older_eng
            trans_trend = recent_trans - older_trans
        else:
            eng_trend = 0
            trans_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "elements_impact": {
                "high_elements_transformation": round(high_elem_trans, 2),
                "low_elements_transformation": round(low_elem_trans, 2),
                "high_elements_engagement": round(high_elem_eng, 2),
                "low_elements_engagement": round(low_elem_eng, 2),
            },
            "intention_impact": {
                "high_intention_transformation": round(high_int_trans, 2),
                "low_intention_transformation": round(low_int_trans, 2),
            },
            "rote_vs_engaged": {
                "rote_transformation": round(rote_trans, 2),
                "engaged_transformation": round(engaged_trans, 2),
                "rote_engagement": round(rote_eng, 2),
                "engaged_engagement": round(engaged_eng, 2),
            },
            "rote_risk": rote_risk,
            "avg_engagement": round(sum(e.engagement for e in self._entries) / len(self._entries), 2),
            "avg_transformation": round(sum(e.transformation for e in self._entries) / len(self._entries), 2),
            "engagement_trend": round(eng_trend, 2),
            "transformation_trend": round(trans_trend, 2),
            "recent_intention": round(recent_intention, 2),
        }

    def get_ritual_design(self, occasion: str = "", participants: int = 1, intention: str = "") -> Dict[str, Any]:
        """Get design."""
        designs = {
            "morning": [
                "Light a candle. Set an intention. One minute of silence. That's a morning ritual. Start the day with consciousness.",
                "Journal three lines. What you hope for. What you fear. What you'll focus on. Signature. Begin.",
                "Make coffee or tea with full attention. The pour. The steam. The first sip. Let it be ceremony.",
            ],
            "evening": [
                "Extinguish a candle. Review the day. What mattered? What didn't? Release it. Sleep is permission to begin again.",
                "Write one line of gratitude. One apology. One hope. Close the book. Close the day.",
                "Walk outside. Look at the sky. Notice the transition. Day to night. Activity to rest. You're part of this rhythm.",
            ],
            "transition": [
                "Burn what you're leaving behind. Not literally (unless safe). Symbolically. A letter. A list. Transform it to smoke.",
                "Plant something for what you're becoming. A seed. A tree. Something that grows as you grow.",
                "Walk across a threshold. Pause at the doorway. Acknowledge the crossing. Then step through. Intentionally.",
            ],
            "grief": [
                "Create an altar. Photo. Object. Flower. Light a candle daily. Grief needs witness. Be the witness.",
                "Write a letter to the dead. Say what you didn't. Then burn it or bury it. Release is part of love.",
                "Cook their favorite meal. Eat it slowly. Remember. Cry if you need to. Ritual holds what you can't hold alone.",
            ],
            "celebration": [
                "Name what you're celebrating specifically. Not 'success.' 'The contract I fought for.' Specific joy is deeper.",
                "Share it with someone who understands. Not everyone. The right person. Joy multiplies in the right container.",
                "Mark it physically. A toast. A dance. A walk to a special place. Embodied celebration lasts longer.",
            ],
            "general": [
                "Ritual is not superstition. It's technology for the soul. It creates containers for experiences that don't fit ordinary time.",
                "The best rituals have three parts: threshold (entering), transformation (the work), return (integration). Design all three.",
                "Symbols matter. They carry meaning your words can't. Choose them carefully. They'll do the heavy lifting.",
            ],
        }

        selected = designs.get(occasion, designs["general"])

        if participants == 1:
            part_note = "Solo ritual. You're the designer and the participant. That's powerful. No compromise needed."
        elif participants <= 5:
            part_note = "Small group. Intimate. Deep. Design for participation, not performance. Everyone should do something."
        else:
            part_note = "Large group. Design for shared experience. Common words. Common actions. Unity through repetition."

        return {
            "occasion": occasion or "general",
            "participants": participants,
            "intention": intention or "general",
            "design": random.choice(selected),
            "participants_note": part_note,
            "principle": "Most modern people have no rituals. They have habits. Habits are mechanical. Rituals are meaningful. The difference is intention. Brushing your teeth is a habit. Brushing your teeth while reciting what you're grateful for is a ritual. Same action. Different meaning. You don't need more time. You need more intention. Every habit can become a ritual. Every ritual can become sacred. It's a question of attention, not activity.",
        }

    def get_ritual_score(self) -> int:
        """Calculate overall ritual health (0-100)."""
        if not self._entries:
            return 25

        # Engagement, intention, and transformation
        avg_eng = sum(e.engagement for e in self._entries) / len(self._entries)
        avg_int = sum(e.intention for e in self._entries) / len(self._entries)
        avg_trans = sum(e.transformation for e in self._entries) / len(self._entries)

        # Low rote
        rote_rate = sum(1 for e in self._entries if e.rote) / len(self._entries)

        # Elements (symbolic richness)
        avg_elements = sum(e.elements for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.ritual_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_eng = sum(e.engagement for e in recent) / len(recent)
            recent_int = sum(e.intention for e in recent) / len(recent)
            recent_trans = sum(e.transformation for e in recent) / len(recent)
            recent_rote = sum(1 for e in recent if e.rote) / len(recent)
        else:
            recent_eng = 0
            recent_int = 0
            recent_trans = 0
            recent_rote = 0

        # Rote penalty
        rote_penalty = 0
        if recent_rote > 0.3:
            rote_penalty = 15

        score = (avg_eng * 20) + (avg_int * 20) + (avg_trans * 20) + ((1 - rote_rate) * 10) + (avg_elements * 2) + (unique_types * 3) + (recent_eng * 10) + (recent_int * 10) + (recent_trans * 10) - rote_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_engagement"] = round(sum(e.engagement for e in self._entries) / len(self._entries), 2)
            self._stats["avg_transformation"] = round(sum(e.transformation for e in self._entries) / len(self._entries), 2)

            recent = list(self._entries)[-14:]
            if recent:
                recent_rote = sum(1 for e in recent if e.rote) / len(recent)
                recent_eng = sum(e.engagement for e in recent) / len(recent)
                self._stats["rote_risk"] = recent_rote > 0.3 or recent_eng < 0.4

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sacred_ritual_designer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sacred_ritual_designer")

    def _log_entry(self, entry: RitualEntry):
        try:
            with open(RITUAL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "name": entry.name,
                    "ritual_type": entry.ritual_type,
                    "elements": entry.elements,
                    "engagement": entry.engagement,
                    "intention": entry.intention,
                    "transformation": entry.transformation,
                    "rote": entry.rote,
                    "participants": entry.participants,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.sacred_ritual_designer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_srd_instance: Optional[SacredRitualDesigner] = None
_srd_lock = threading.Lock()


def get_sacred_ritual_designer() -> SacredRitualDesigner:
    global _srd_instance
    with _srd_lock:
        if _srd_instance is None:
            _srd_instance = SacredRitualDesigner()
        return _srd_instance
