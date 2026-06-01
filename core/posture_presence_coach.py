"""
LOVE Posture & Presence Coach — Embodied Presence Intelligence (Modern AI Pattern)

Most people collapse unconsciously. This coach:

1. PRESENCE TRACKING
   - Record posture/presence moments and their characteristics
   - Track presence types (upright, open, grounded, aligned, expansive, receptive)
   - Log posture quality, presence, confidence, and energy

2. PATTERN ANALYSIS
   - Identify the user's presence profile (collapsed, guarded, developing, radiant)
   - Find posture patterns that create confidence vs diminishment
   - Detect chronic collapsing and its costs

3. PRESENCE BUILDING
   - Suggest practices for improving posture and embodied presence
   - Provide frameworks for power posing and open body language
   - Recommend practices for aligning body and state

4. EMBODIED CONFIDENCE CULTIVATION
   - Track the correlation between posture and internal state
   - Alert when collapsing is becoming the default
   - Celebrate moments of genuine, upright presence

Architecture:
- record_presence(situation, type, posture, presence, confidence, energy): Log presence
- get_presence_stats(): Get presence pattern analysis
- get_presence_suggestion(capacity, context): Get suggestion
- get_presence_score(): Calculate overall presence health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "posture_presence_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRESENCE_LOG = DATA_DIR / "presences.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PresenceEntry:
    """A tracked posture/presence moment."""
    entry_id: str = ""
    situation: str = ""  # what was happening
    presence_type: str = ""  # upright, open, grounded, aligned, expansive, receptive
    posture: float = 0.0  # 0-1
    presence: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    energy: float = 0.0  # 0-1
    openness: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PosturePresenceCoach:
    """
    Intelligent posture & presence coach with collapsing detection and embodied confidence cultivation.
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
            "avg_posture": 0.0,
            "avg_presence": 0.0,
            "collapse_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_presence(self, situation: str = "", presence_type: str = "", posture: float = 0.0, presence: float = 0.0, confidence: float = 0.0, energy: float = 0.0, openness: float = 0.0, notes: str = "") -> PresenceEntry:
        """Record a posture/presence moment."""
        entry_id = f"prs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = PresenceEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            presence_type=presence_type or "upright",
            posture=posture,
            presence=presence,
            confidence=confidence,
            energy=energy,
            openness=openness,
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

    def get_presence_stats(self) -> Dict[str, Any]:
        """Get presence pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "posture_sum": 0.0, "presence_sum": 0.0, "confidence_sum": 0.0})
        for e in self._entries:
            by_type[e.presence_type]["count"] += 1
            by_type[e.presence_type]["posture_sum"] += e.posture
            by_type[e.presence_type]["presence_sum"] += e.presence
            by_type[e.presence_type]["confidence_sum"] += e.confidence

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_posture": round(data["posture_sum"] / count, 2),
                "avg_presence": round(data["presence_sum"] / count, 2),
                "avg_confidence": round(data["confidence_sum"] / count, 2),
            }

        # Posture analysis
        high_post = [e for e in self._entries if e.posture > 0.7]
        low_post = [e for e in self._entries if e.posture < 0.4]
        if high_post and low_post:
            high_post_conf = sum(e.confidence for e in high_post) / len(high_post)
            low_post_conf = sum(e.confidence for e in low_post) / len(low_post)
            high_post_en = sum(e.energy for e in high_post) / len(high_post)
            low_post_en = sum(e.energy for e in low_post) / len(low_post)
        else:
            high_post_conf = 0
            low_post_conf = 0
            high_post_en = 0
            low_post_en = 0

        # Openness analysis
        high_open = [e for e in self._entries if e.openness > 0.7]
        low_open = [e for e in self._entries if e.openness < 0.4]
        if high_open and low_open:
            high_open_pres = sum(e.presence for e in high_open) / len(high_open)
            low_open_pres = sum(e.presence for e in low_open) / len(low_open)
        else:
            high_open_pres = 0
            low_open_pres = 0

        # Collapse risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_post = sum(e.posture for e in recent) / len(recent)
            recent_pres = sum(e.presence for e in recent) / len(recent)
            collapse_risk = recent_post < 0.3 and recent_pres < 0.3
        else:
            collapse_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "posture_impact": {
                "high_posture_confidence": round(high_post_conf, 2),
                "low_posture_confidence": round(low_post_conf, 2),
                "high_posture_energy": round(high_post_en, 2),
                "low_posture_energy": round(low_post_en, 2),
            },
            "openness_effect": {
                "high_openness_presence": round(high_open_pres, 2),
                "low_openness_presence": round(low_open_pres, 2),
            },
            "collapse_risk": collapse_risk,
            "avg_posture": round(sum(e.posture for e in self._entries) / len(self._entries), 2),
            "avg_presence": round(sum(e.presence for e in self._entries) / len(self._entries), 2),
        }

    def get_presence_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get presence suggestion."""
        suggestions = [
            "Your posture shapes your mind. Sit up straight. Shoulders back. Chin level. Feel the difference? You just changed your biochemistry. Posture is not etiquette. It's psychology.",
            "Open your body to open your mind. Crossed arms. Slumped shoulders. Downcast eyes. These are defensive positions. They create defensive minds. Open your body. Open your mind.",
            "Stand like you belong. Most people make themselves small. They shrink. They apologize with their posture. Don't. Take up space. You have permission. You always did.",
            "Ground yourself. Feel your feet. Your seat. Your connection to the earth. The more grounded you are, the more present you are. And the more present you are, the more powerful you are.",
            "Your face is part of your posture. Soft eyes. Relaxed jaw. Open expression. These signal safety to your nervous system. And to others. Your face is a billboard. Make it say: I'm here.",
            "Power posing works. Not because it's magic. Because it changes your hormones. Two minutes of expansive posture increases testosterone and decreases cortisol. Your body is a pharmacy. Pose accordingly.",
            "Notice when you collapse. When you sink. When you shrink. That's the moment. The stress response. The submission response. Straighten up. One inch at a time. Reclaim your verticality.",
            "Align your body with your intention. If you want to be confident, stand confidently. If you want to be open, sit openly. If you want to be present, be physically present. The body leads the state.",
            "Your posture is a habit. Not a trait. You can change it. But it takes awareness. And practice. And patience. Every time you straighten up, you're rewiring. Keep rewiring.",
            "The person who is physically present is mentally present. You can't be checked out in your body and checked in in your mind. Presence is embodied. Or it's not presence."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One deep breath that lifts your chest. One shoulder roll. One moment of upright stillness. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A posture check. A power pose. A grounding practice. Medium coaching."
        else:
            capacity_note = "Good capacity. Deep embodied presence work. A systematic practice of aligning posture with intention and state. You have the strength to be truly present."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Posture is not about etiquette. It's about psychology. Your body position shapes your mental state. Slumped shoulders create defeated thoughts. Crossed arms create defensive minds. Downcast eyes create diminished selves. And the reverse is also true. Upright posture creates confident thoughts. Open arms create receptive minds. Forward gaze creates engaged selves. This is not positive thinking. It's embodied cognition. The body and mind are not separate. They are one system. And you can hack that system by changing your posture. By opening your body. By grounding yourself. By taking up space. The work of posture and presence coaching is about becoming conscious of your body position. About noticing when you collapse. About choosing to expand. And about understanding that your physical presence is your psychological presence. You cannot be mentally present while physically absent."
        }

    def get_presence_score(self) -> int:
        """Calculate overall presence health (0-100)."""
        if not self._entries:
            return 25

        avg_post = sum(e.posture for e in self._entries) / len(self._entries)
        avg_pres = sum(e.presence for e in self._entries) / len(self._entries)
        avg_conf = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_en = sum(e.energy for e in self._entries) / len(self._entries)
        avg_open = sum(e.openness for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_post = sum(e.posture for e in recent) / len(recent)
            recent_pres = sum(e.presence for e in recent) / len(recent)
        else:
            recent_post = 0
            recent_pres = 0

        # Collapse penalty
        collapse_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_post_30 = sum(e.posture for e in last_30) / len(last_30)
            recent_pres_30 = sum(e.presence for e in last_30) / len(last_30)
            if recent_post_30 < 0.3 and recent_pres_30 < 0.3:
                collapse_penalty = 15

        # Type variety
        unique_types = len(set(e.presence_type for e in self._entries))

        score = (avg_post * 25) + (avg_pres * 20) + (avg_conf * 15) + (avg_en * 15) + (avg_open * 10) + (recent_post * 5) + (recent_pres * 5) + (unique_types * 2) - collapse_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_posture"] = round(sum(e.posture for e in self._entries) / len(self._entries), 2)
            self._stats["avg_presence"] = round(sum(e.presence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_post = sum(e.posture for e in recent) / len(recent)
                recent_pres = sum(e.presence for e in recent) / len(recent)
                self._stats["collapse_risk"] = recent_post < 0.3 and recent_pres < 0.3
            else:
                self._stats["collapse_risk"] = False

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

    def _log_entry(self, entry: PresenceEntry):
        try:
            with open(PRESENCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "presence_type": entry.presence_type,
                    "posture": entry.posture,
                    "presence": entry.presence,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ppc_instance: Optional[PosturePresenceCoach] = None
_ppc_lock = threading.Lock()


def get_posture_presence_coach() -> PosturePresenceCoach:
    global _ppc_instance
    with _ppc_lock:
        if _ppc_instance is None:
            _ppc_instance = PosturePresenceCoach()
        return _ppc_instance
