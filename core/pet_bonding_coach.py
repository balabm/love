"""
LOVE Pet Bonding Coach — Companion Intelligence (Modern AI Pattern)

Most people live with pets but don't truly bond. This coach:

1. BONDING TRACKING
   - Record pet bonding moments and their characteristics
   - Track bonding types (play, training, cuddling, walking, grooming, communication)
   - Log quality, reciprocity, joy, and depth of bonding

2. PATTERN ANALYSIS
   - Identify the user's bonding profile (distant, routine, developing, deep)
   - Find bonding patterns that create connection vs obligation
   - Detect chronic neglect and its costs

3. BONDING BUILDING
   - Suggest practices for deepening pet relationships
   - Provide frameworks for quality time and attention
   - Recommend practices for reading and responding to pet signals

4. COMPANIONSHIP CULTIVATION
   - Track the correlation between bonding and wellbeing
   - Alert when pet care is becoming purely functional
   - Celebrate moments of genuine, deep companionship

Architecture:
- record_bonding(activity, type, quality, reciprocity, joy, depth): Log bonding
- get_bonding_stats(): Get bonding pattern analysis
- get_bonding_suggestion(capacity, context): Get suggestion
- get_bonding_score(): Calculate overall bonding health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "pet_bonding_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BONDING_LOG = DATA_DIR / "bondings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BondingEntry:
    """A tracked pet bonding moment."""
    entry_id: str = ""
    activity: str = ""  # what was done
    bonding_type: str = ""  # play, training, cuddling, walking, grooming, communication
    quality: float = 0.0  # 0-1
    reciprocity: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    depth: float = 0.0  # 0-1
    attention: float = 0.0  # 0-1 was full attention given?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PetBondingCoach:
    """
    Intelligent pet bonding coach with neglect detection and companionship cultivation.
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
            "avg_quality": 0.0,
            "avg_depth": 0.0,
            "neglect_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_bonding(self, activity: str = "", bonding_type: str = "", quality: float = 0.0, reciprocity: float = 0.0, joy: float = 0.0, depth: float = 0.0, attention: float = 0.0, notes: str = "") -> BondingEntry:
        """Record a pet bonding moment."""
        entry_id = f"bnd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BondingEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            bonding_type=bonding_type or "play",
            quality=quality,
            reciprocity=reciprocity,
            joy=joy,
            depth=depth,
            attention=attention,
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

    def get_bonding_stats(self) -> Dict[str, Any]:
        """Get bonding pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "quality_sum": 0.0, "joy_sum": 0.0, "depth_sum": 0.0})
        for e in self._entries:
            by_type[e.bonding_type]["count"] += 1
            by_type[e.bonding_type]["quality_sum"] += e.quality
            by_type[e.bonding_type]["joy_sum"] += e.joy
            by_type[e.bonding_type]["depth_sum"] += e.depth

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_depth": round(data["depth_sum"] / count, 2),
            }

        # Quality analysis
        high_qual = [e for e in self._entries if e.quality > 0.7]
        low_qual = [e for e in self._entries if e.quality < 0.4]
        if high_qual and low_qual:
            high_qual_joy = sum(e.joy for e in high_qual) / len(high_qual)
            low_qual_joy = sum(e.joy for e in low_qual) / len(low_qual)
            high_qual_depth = sum(e.depth for e in high_qual) / len(high_qual)
            low_qual_depth = sum(e.depth for e in low_qual) / len(low_qual)
        else:
            high_qual_joy = 0
            low_qual_joy = 0
            high_qual_depth = 0
            low_qual_depth = 0

        # Attention analysis
        high_att = [e for e in self._entries if e.attention > 0.7]
        low_att = [e for e in self._entries if e.attention < 0.4]
        if high_att and low_att:
            high_att_rec = sum(e.reciprocity for e in high_att) / len(high_att)
            low_att_rec = sum(e.reciprocity for e in low_att) / len(low_att)
        else:
            high_att_rec = 0
            low_att_rec = 0

        # Neglect risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_qual = sum(e.quality for e in recent) / len(recent)
            recent_depth = sum(e.depth for e in recent) / len(recent)
            neglect_risk = recent_qual < 0.3 and recent_depth < 0.3
        else:
            neglect_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "quality_impact": {
                "high_quality_joy": round(high_qual_joy, 2),
                "low_quality_joy": round(low_qual_joy, 2),
                "high_quality_depth": round(high_qual_depth, 2),
                "low_quality_depth": round(low_qual_depth, 2),
            },
            "attention_effect": {
                "high_attention_reciprocity": round(high_att_rec, 2),
                "low_attention_reciprocity": round(low_att_rec, 2),
            },
            "neglect_risk": neglect_risk,
            "avg_quality": round(sum(e.quality for e in self._entries) / len(self._entries), 2),
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
        }

    def get_bonding_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get bonding suggestion."""
        suggestions = [
            "Your pet is not an accessory. They're a relationship. They have emotions. Preferences. Fears. Desires. They know you. They read you. They love you. Do you know them? Do you read them? Do you love them back?",
            "Put down your phone when you're with your pet. They notice. They always notice. Your attention is the greatest gift you can give. And the greatest sign of love. Be present. For them.",
            "Learn their language. The tail wag. The ear position. The eye contact. The vocalizations. They're talking to you. Constantly. Most people don't listen. Listen. You'll be amazed what you hear.",
            "Quality over quantity. Ten minutes of focused play is better than an hour of distracted presence. Your pet doesn't need more time. They need more you. Be there. Fully.",
            "Train with kindness. Not dominance. Your pet wants to understand you. They want to please you. Help them. Guide them. Reward them. Training is communication. And communication is love.",
            "Notice what they love. The specific toy. The specific spot. The specific treat. The specific way of being touched. These are their preferences. Honor them. That's how relationships deepen.",
            "Walk with them. Not just for exercise. For exploration. For sniffing. For being together in the world. The walk is not a chore. It's an adventure. For both of you.",
            "Groom them gently. Not just for cleanliness. For touch. For connection. For trust. The animals who trust you enough to let you groom them are the animals who love you most.",
            "When they're sick or scared, be there. Don't just fix the problem. Sit with the fear. Hold the pain. Your presence is medicine. Your calm is healing. Be the person they can always count on.",
            "The person who bonds deeply with their pet is not silly. They're wise. Because they understand that love is love. That connection is connection. And that the shortest path to the heart is often covered in fur."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Ten minutes of focused attention. One walk without your phone. One moment of really looking at them. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A training session. A grooming ritual. A new game learned. A communication breakthrough. Medium bonding."
        else:
            capacity_note = "Good capacity. Deep companionship work. A systematic practice of presence, understanding, and love with your animal. You have the strength to be their best friend."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Pet bonding is not about ownership. It's about relationship. Most people live with pets but don't truly know them. They feed them. They walk them. They clean up after them. But they don't bond with them. They don't understand their language. They don't read their signals. They don't respond to their needs. And the pet knows. They always know. The work of pet bonding coaching is about deepening the relationship between human and animal. About learning to communicate across species. About understanding that animals have emotions, preferences, and inner lives. About giving them the quality of attention they deserve. And about recognizing that the person who bonds deeply with their pet is not being childish. They're being wise. Because animals teach us about unconditional love. About presence. About loyalty. And about the simple, profound joy of companionship."
        }

    def get_bonding_score(self) -> int:
        """Calculate overall bonding health (0-100)."""
        if not self._entries:
            return 25

        avg_qual = sum(e.quality for e in self._entries) / len(self._entries)
        avg_recip = sum(e.reciprocity for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_att = sum(e.attention for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_qual = sum(e.quality for e in recent) / len(recent)
            recent_depth = sum(e.depth for e in recent) / len(recent)
        else:
            recent_qual = 0
            recent_depth = 0

        # Neglect penalty
        neg_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_qual_30 = sum(e.quality for e in last_30) / len(last_30)
            recent_depth_30 = sum(e.depth for e in last_30) / len(last_30)
            if recent_qual_30 < 0.3 and recent_depth_30 < 0.3:
                neg_penalty = 15

        # Type variety
        unique_types = len(set(e.bonding_type for e in self._entries))

        score = (avg_qual * 25) + (avg_recip * 15) + (avg_joy * 15) + (avg_depth * 15) + (avg_att * 10) + (recent_qual * 5) + (recent_depth * 5) + (unique_types * 2) - neg_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_quality"] = round(sum(e.quality for e in self._entries) / len(self._entries), 2)
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_qual = sum(e.quality for e in recent) / len(recent)
                recent_depth = sum(e.depth for e in recent) / len(recent)
                self._stats["neglect_risk"] = recent_qual < 0.3 and recent_depth < 0.3
            else:
                self._stats["neglect_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.pet_bonding_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.pet_bonding_coach")

    def _log_entry(self, entry: BondingEntry):
        try:
            with open(BONDING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "bonding_type": entry.bonding_type,
                    "quality": entry.quality,
                    "depth": entry.depth,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.pet_bonding_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pbc_instance: Optional[PetBondingCoach] = None
_pbc_lock = threading.Lock()


def get_pet_bonding_coach() -> PetBondingCoach:
    global _pbc_instance
    with _pbc_lock:
        if _pbc_instance is None:
            _pbc_instance = PetBondingCoach()
        return _pbc_instance
