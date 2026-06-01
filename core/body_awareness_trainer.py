"""
LOVE Body Awareness Trainer — Embodied Intelligence (Modern AI Pattern)

Most people live in their heads. This trainer:

1. BODY TRACKING
   - Record body awareness moments and their characteristics
   - Track body areas (tension, pain, comfort, energy, grounding, sensation)
   - Log awareness, response, and integration of body signals

2. PATTERN ANALYSIS
   - Identify the user's body awareness profile (dissociated, occasional, aware, integrated)
   - Find body awareness patterns that create health vs disconnection
   - Detect chronic dissociation and its costs

3. AWARENESS BUILDING
   - Suggest practices for increasing body awareness
   - Provide frameworks for somatic intelligence
   - Recommend practices for listening to the body

4. EMBODIMENT CULTIVATION
   - Track the correlation between body awareness and wellbeing
   - Alert when dissociation is becoming the default
   - Celebrate moments of genuine embodied presence

Architecture:
- record_body(sensation, area, awareness, response, integration): Log body
- get_body_stats(): Get body pattern analysis
- get_body_suggestion(capacity, context): Get suggestion
- get_body_score(): Calculate overall body health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "body_awareness_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BODY_LOG = DATA_DIR / "bodies.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BodyEntry:
    """A tracked body awareness moment."""
    entry_id: str = ""
    sensation: str = ""  # what was noticed
    body_area: str = ""  # tension, pain, comfort, energy, grounding, sensation
    awareness: float = 0.0  # 0-1
    response: float = 0.0  # 0-1 did you respond?
    integration: float = 0.0  # 0-1
    grounding: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BodyAwarenessTrainer:
    """
    Intelligent body awareness trainer with dissociation detection and embodiment cultivation.
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
            "avg_awareness": 0.0,
            "avg_integration": 0.0,
            "dissociation_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_body(self, sensation: str = "", body_area: str = "", awareness: float = 0.0, response: float = 0.0, integration: float = 0.0, grounding: float = 0.0, notes: str = "") -> BodyEntry:
        """Record a body awareness moment."""
        entry_id = f"bdy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BodyEntry(
            entry_id=entry_id,
            sensation=sensation or "unspecified",
            body_area=body_area or "general",
            awareness=awareness,
            response=response,
            integration=integration,
            grounding=grounding,
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

    def get_body_stats(self) -> Dict[str, Any]:
        """Get body pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "awareness_sum": 0.0, "response_sum": 0.0, "integration_sum": 0.0})
        for e in self._entries:
            by_type[e.body_area]["count"] += 1
            by_type[e.body_area]["awareness_sum"] += e.awareness
            by_type[e.body_area]["response_sum"] += e.response
            by_type[e.body_area]["integration_sum"] += e.integration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_awareness": round(data["awareness_sum"] / count, 2),
                "avg_response": round(data["response_sum"] / count, 2),
                "avg_integration": round(data["integration_sum"] / count, 2),
            }

        # Awareness analysis
        high_aware = [e for e in self._entries if e.awareness > 0.7]
        low_aware = [e for e in self._entries if e.awareness < 0.4]
        if high_aware and low_aware:
            high_aware_resp = sum(e.response for e in high_aware) / len(high_aware)
            low_aware_resp = sum(e.response for e in low_aware) / len(low_aware)
            high_aware_int = sum(e.integration for e in high_aware) / len(high_aware)
            low_aware_int = sum(e.integration for e in low_aware) / len(low_aware)
        else:
            high_aware_resp = 0
            low_aware_resp = 0
            high_aware_int = 0
            low_aware_int = 0

        # Grounding analysis
        high_gr = [e for e in self._entries if e.grounding > 0.7]
        low_gr = [e for e in self._entries if e.grounding < 0.4]
        if high_gr and low_gr:
            high_gr_aware = sum(e.awareness for e in high_gr) / len(high_gr)
            low_gr_aware = sum(e.awareness for e in low_gr) / len(low_gr)
        else:
            high_gr_aware = 0
            low_gr_aware = 0

        # Dissociation risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
            dissociation_risk = recent_aware < 0.3 and recent_int < 0.3
        else:
            dissociation_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "awareness_impact": {
                "high_awareness_response": round(high_aware_resp, 2),
                "low_awareness_response": round(low_aware_resp, 2),
                "high_awareness_integration": round(high_aware_int, 2),
                "low_awareness_integration": round(low_aware_int, 2),
            },
            "grounding_effect": {
                "high_grounding_awareness": round(high_gr_aware, 2),
                "low_grounding_awareness": round(low_gr_aware, 2),
            },
            "dissociation_risk": dissociation_risk,
            "avg_awareness": round(sum(e.awareness for e in self._entries) / len(self._entries), 2),
            "avg_integration": round(sum(e.integration for e in self._entries) / len(self._entries), 2),
        }

    def get_body_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get body suggestion."""
        suggestions = [
            "Your body is not a vehicle for your mind. It's part of your intelligence. It holds information your mind ignores. Tension in your shoulders. Tightness in your chest. Numbness in your hands. These are signals. Listen.",
            "Most people live in their heads because their bodies are uncomfortable. The body holds stress. Trauma. Unprocessed emotion. Coming back to the body means facing what you've been avoiding. That's why it's hard. And that's why it's necessary.",
            "Notice where you are right now. Feet on the floor. Back against the chair. Breath moving in your chest. That's embodiment. That's presence. You don't need a meditation retreat. You need attention.",
            "The body doesn't lie. Your mind can rationalize. Your body cannot. If your gut says no, it's no. If your chest tightens, something is wrong. If your shoulders relax, something is right. Trust the body.",
            "Scan your body from toes to head. What's tight? What's loose? What's warm? What's cold? What's numb? Don't fix anything. Just notice. Awareness is the first intervention.",
            "Your body remembers what your mind forgets. The childhood fear. The ungrieved loss. The unexpressed anger. It lives in your tissues. Not your thoughts. Healing happens in the body first. Then the mind.",
            "Ground yourself. Feel your feet. Notice the weight of your body. The support of the chair. The floor. The earth. You're not floating. You're held. That's grounding. And it's available in every moment.",
            "Notice when you dissociate. When you check out. When you go into your head to escape discomfort. That's the moment. Come back. One breath. One sensation. One step back into your body.",
            "Movement is not exercise. It's expression. Dance. Walk. Stretch. Shake. Your body needs to move. Not to burn calories. To process energy. To release tension. To feel alive.",
            "The person who is not in their body is not fully alive. They're a floating head. A brain in a jar. Come back. The body is where life happens. Where pleasure lives. Where grief moves. Where joy dances. Come back."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One breath felt. One sensation noticed. One moment back in your body. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A body scan. A grounding practice. A movement session. Medium training."
        else:
            capacity_note = "Good capacity. Deep somatic work. A systematic practice of embodied presence and somatic intelligence. You have the strength to be truly in your body."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Body awareness is the most neglected form of intelligence in modern life. We treat the body as a vehicle for the mind. As something to be fed, clothed, and exercised, but not listened to. And we pay the price. Chronic tension becomes chronic pain. Ignored sensations become illness. Dissociation becomes numbness. The body holds information that the mind cannot access. It knows things before the mind understands them. The tight chest before the anxiety is named. The gut feeling before the decision is analyzed. The yawn before the fatigue is acknowledged. The work of body awareness training is about coming back to the body. About listening to its signals. About responding to its needs. About integrating body and mind so that they work together rather than against each other. Because the person who is embodied is present. And the person who is present is alive."
        }

    def get_body_score(self) -> int:
        """Calculate overall body health (0-100)."""
        if not self._entries:
            return 25

        avg_aware = sum(e.awareness for e in self._entries) / len(self._entries)
        avg_resp = sum(e.response for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_gr = sum(e.grounding for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_aware = sum(e.awareness for e in recent) / len(recent)
            recent_int = sum(e.integration for e in recent) / len(recent)
        else:
            recent_aware = 0
            recent_int = 0

        # Dissociation penalty
        diss_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_aware_30 = sum(e.awareness for e in last_30) / len(last_30)
            recent_int_30 = sum(e.integration for e in last_30) / len(last_30)
            if recent_aware_30 < 0.3 and recent_int_30 < 0.3:
                diss_penalty = 15

        # Type variety
        unique_types = len(set(e.body_area for e in self._entries))

        score = (avg_aware * 25) + (avg_resp * 20) + (avg_int * 20) + (avg_gr * 15) + (recent_aware * 5) + (recent_int * 5) + (unique_types * 2) - diss_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_awareness"] = round(sum(e.awareness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_integration"] = round(sum(e.integration for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_aware = sum(e.awareness for e in recent) / len(recent)
                recent_int = sum(e.integration for e in recent) / len(recent)
                self._stats["dissociation_risk"] = recent_aware < 0.3 and recent_int < 0.3
            else:
                self._stats["dissociation_risk"] = False

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

    def _log_entry(self, entry: BodyEntry):
        try:
            with open(BODY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "sensation": entry.sensation,
                    "body_area": entry.body_area,
                    "awareness": entry.awareness,
                    "integration": entry.integration,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_bat_instance: Optional[BodyAwarenessTrainer] = None
_bat_lock = threading.Lock()


def get_body_awareness_trainer() -> BodyAwarenessTrainer:
    global _bat_instance
    with _bat_lock:
        if _bat_instance is None:
            _bat_instance = BodyAwarenessTrainer()
        return _bat_instance
