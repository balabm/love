"""
LOVE Stage Confidence Builder — Performance Intelligence (Modern AI Pattern)

Most people freeze on stage. This builder:

1. STAGE TRACKING
   - Record stage moments and their characteristics
   - Track stage types (presentation, performance, meeting, speech, pitch, ceremony)
   - Log confidence, preparation, delivery, recovery, and impact of stage work

2. PATTERN ANALYSIS
   - Identify the user's stage profile (avoidant, anxious, developing, commanding)
   - Find stage patterns that create confidence vs fear
   - Detect chronic stage fright and its costs

3. CONFIDENCE BUILDING
   - Suggest practices for building stage confidence
   - Provide frameworks for preparation and rehearsal
   - Recommend practices for managing stage anxiety

4. PERFORMANCE MASTERY CULTIVATION
   - Track the correlation between preparation and stage success
   - Alert when avoidance is becoming the default
   - Celebrate moments of genuine stage command

Architecture:
- record_stage(event, type, confidence, preparation, delivery, recovery, impact): Log stage
- get_stage_stats(): Get stage pattern analysis
- get_stage_suggestion(capacity, context): Get suggestion
- get_stage_score(): Calculate overall stage health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "stage_confidence_builder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STAGE_LOG = DATA_DIR / "stages.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class StageEntry:
    """A tracked stage moment."""
    entry_id: str = ""
    event: str = ""  # what was the event
    stage_type: str = ""  # presentation, performance, meeting, speech, pitch, ceremony
    confidence: float = 0.0  # 0-1
    preparation: float = 0.0  # 0-1
    delivery: float = 0.0  # 0-1
    recovery: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    fear: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class StageConfidenceBuilder:
    """
    Intelligent stage confidence builder with avoidance detection and performance mastery cultivation.
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
            "avg_confidence": 0.0,
            "avg_delivery": 0.0,
            "avoidance_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_stage(self, event: str = "", stage_type: str = "", confidence: float = 0.0, preparation: float = 0.0, delivery: float = 0.0, recovery: float = 0.0, impact: float = 0.0, fear: float = 0.0, notes: str = "") -> StageEntry:
        """Record a stage moment."""
        entry_id = f"stg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = StageEntry(
            entry_id=entry_id,
            event=event or "unspecified",
            stage_type=stage_type or "presentation",
            confidence=confidence,
            preparation=preparation,
            delivery=delivery,
            recovery=recovery,
            impact=impact,
            fear=fear,
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

    def get_stage_stats(self) -> Dict[str, Any]:
        """Get stage pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "confidence_sum": 0.0, "delivery_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            by_type[e.stage_type]["count"] += 1
            by_type[e.stage_type]["confidence_sum"] += e.confidence
            by_type[e.stage_type]["delivery_sum"] += e.delivery
            by_type[e.stage_type]["impact_sum"] += e.impact

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_confidence": round(data["confidence_sum"] / count, 2),
                "avg_delivery": round(data["delivery_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Confidence analysis
        high_conf = [e for e in self._entries if e.confidence > 0.7]
        low_conf = [e for e in self._entries if e.confidence < 0.4]
        if high_conf and low_conf:
            high_conf_del = sum(e.delivery for e in high_conf) / len(high_conf)
            low_conf_del = sum(e.delivery for e in low_conf) / len(low_conf)
            high_conf_imp = sum(e.impact for e in high_conf) / len(high_conf)
            low_conf_imp = sum(e.impact for e in low_conf) / len(low_conf)
        else:
            high_conf_del = 0
            low_conf_del = 0
            high_conf_imp = 0
            low_conf_imp = 0

        # Preparation analysis
        high_prep = [e for e in self._entries if e.preparation > 0.7]
        low_prep = [e for e in self._entries if e.preparation < 0.4]
        if high_prep and low_prep:
            high_prep_conf = sum(e.confidence for e in high_prep) / len(high_prep)
            low_prep_conf = sum(e.confidence for e in low_prep) / len(low_prep)
        else:
            high_prep_conf = 0
            low_prep_conf = 0

        # Avoidance risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_conf = sum(e.confidence for e in recent) / len(recent)
            recent_del = sum(e.delivery for e in recent) / len(recent)
            avoidance_risk = recent_conf < 0.3 and recent_del < 0.3
        else:
            avoidance_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "confidence_impact": {
                "high_confidence_delivery": round(high_conf_del, 2),
                "low_confidence_delivery": round(low_conf_del, 2),
                "high_confidence_impact": round(high_conf_imp, 2),
                "low_confidence_impact": round(low_conf_imp, 2),
            },
            "preparation_effect": {
                "high_preparation_confidence": round(high_prep_conf, 2),
                "low_preparation_confidence": round(low_prep_conf, 2),
            },
            "avoidance_risk": avoidance_risk,
            "avg_confidence": round(sum(e.confidence for e in self._entries) / len(self._entries), 2),
            "avg_delivery": round(sum(e.delivery for e in self._entries) / len(self._entries), 2),
        }

    def get_stage_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get stage suggestion."""
        suggestions = [
            "Stage fright is not a character flaw. It's a biological response. Your body thinks it's in danger. It's not. The audience wants you to succeed. They're on your side. Even if they don't know it yet.",
            "Prepare. Ruthlessly. Know your material so well that you could do it blind. Preparation is the antidote to anxiety. Because anxiety comes from uncertainty. And preparation eliminates uncertainty.",
            "Rehearse out loud. Not in your head. Not in the shower. Out loud. To a person. To a mirror. To a camera. Your brain processes spoken rehearsal differently. It builds muscle memory for your words.",
            "Arrive early. Get on the stage. Walk around. Feel the space. Own it. The person who is comfortable in the space is the person who commands it. Familiarity breeds confidence.",
            "Find a friendly face. In the audience. Early. Make eye contact. Smile. They're your anchor. When you feel lost, find them. They're your reminder that you're among humans. Not predators.",
            "Start strong. The first thirty seconds matter most. Start with something you know cold. Something that lands. Something that connects. A strong start builds momentum. Momentum carries you.",
            "Embrace the mistake. You will make one. Everyone does. The difference between professionals and amateurs is not the absence of mistakes. It's the recovery. Roll with it. Smile. Move on. The audience will forget the mistake. They'll remember the grace.",
            "Breathe. On stage. Before you speak. Between points. When you feel the fear rising. Breath is your anchor. It grounds you. It slows your heart. It reminds your body that you're safe.",
            "Remember: they're not judging you. They're listening to you. They want what you have. Information. Insight. Entertainment. Connection. Give it to them. Generously. Freely. That's why you're there.",
            "The person who commands the stage is not fearless. They're prepared. They're present. They're generous. And they understand that the stage is not a place of judgment. It's a place of sharing. Share what you have. The stage is yours."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small presentation. One rehearsal out loud. One deep breath on stage. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A prepared speech. An early arrival. A friendly face found. A strong start practiced. Medium confidence."
        else:
            capacity_note = "Good capacity. Deep stage work. A systematic practice of preparation, presence, and recovery. You have the strength to command any room."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Stage confidence is not about being fearless. It's about being prepared. Most people avoid the stage because they're afraid. They turn down presentations. They skip meetings. They hide in the back row. And they wonder why they're not advancing. Why they're not noticed. Why they're not respected. The work of stage confidence building is about understanding that fear is normal. That anxiety is biological. And that the only way through it is through it. It's about preparation. About rehearsal. About familiarity. About breathing. And about understanding that the audience is not your enemy. They're your opportunity. The person who builds stage confidence doesn't eliminate fear. They perform despite it. And eventually, because of it."
        }

    def get_stage_score(self) -> int:
        """Calculate overall stage health (0-100)."""
        if not self._entries:
            return 25

        avg_conf = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_prep = sum(e.preparation for e in self._entries) / len(self._entries)
        avg_del = sum(e.delivery for e in self._entries) / len(self._entries)
        avg_rec = sum(e.recovery for e in self._entries) / len(self._entries)
        avg_imp = sum(e.impact for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_conf = sum(e.confidence for e in recent) / len(recent)
            recent_del = sum(e.delivery for e in recent) / len(recent)
        else:
            recent_conf = 0
            recent_del = 0

        # Avoidance penalty
        avoid_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_conf_30 = sum(e.confidence for e in last_30) / len(last_30)
            recent_del_30 = sum(e.delivery for e in last_30) / len(last_30)
            if recent_conf_30 < 0.3 and recent_del_30 < 0.3:
                avoid_penalty = 15

        # Type variety
        unique_types = len(set(e.stage_type for e in self._entries))

        score = (avg_conf * 25) + (avg_prep * 15) + (avg_del * 20) + (avg_rec * 10) + (avg_imp * 15) + (recent_conf * 5) + (recent_del * 5) + (unique_types * 2) - avoid_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_confidence"] = round(sum(e.confidence for e in self._entries) / len(self._entries), 2)
            self._stats["avg_delivery"] = round(sum(e.delivery for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_conf = sum(e.confidence for e in recent) / len(recent)
                recent_del = sum(e.delivery for e in recent) / len(recent)
                self._stats["avoidance_risk"] = recent_conf < 0.3 and recent_del < 0.3
            else:
                self._stats["avoidance_risk"] = False

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

    def _log_entry(self, entry: StageEntry):
        try:
            with open(STAGE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "event": entry.event,
                    "stage_type": entry.stage_type,
                    "confidence": entry.confidence,
                    "delivery": entry.delivery,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_scb_instance: Optional[StageConfidenceBuilder] = None
_scb_lock = threading.Lock()


def get_stage_confidence_builder() -> StageConfidenceBuilder:
    global _scb_instance
    with _scb_lock:
        if _scb_instance is None:
            _scb_instance = StageConfidenceBuilder()
        return _scb_instance
