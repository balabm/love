"""
LOVE Vision Keeper — Direction Intelligence (Modern AI Pattern)

Most teams drift because the vision is vague or forgotten. This keeper:

1. VISION TRACKING
   - Record vision-related actions and their characteristics
   - Track vision types (personal, team, organizational, societal)
   - Log alignment outcomes and their effects on motivation

2. PATTERN ANALYSIS
   - Identify the user's vision profile (clear, vague, evolving, forgotten)
   - Find vision practices that create sustained alignment
   - Detect vision drift and its consequences

3. VISION BUILDING
   - Suggest vision practices matched to current context
   - Provide articulation and communication frameworks
   - Recommendation alignment checks

4. DIRECTION CULTIVATION
   - Track the correlation between vision clarity and motivation
   - Alert when daily actions are diverging from stated vision
   - Celebrate moments of genuine alignment

Architecture:
- record_action(action, vision_type, alignment, motivation): Log action
- get_vision_stats(): Get vision pattern analysis
- get_vision_practice(context, clarity): Get practice
- get_vision_score(): Calculate overall vision health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "vision_keeper"
DATA_DIR.mkdir(parents=True, exist_ok=True)

VISION_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class VisionEntry:
    """A tracked vision entry."""
    entry_id: str = ""
    action: str = ""  # what was done
    vision_type: str = ""  # personal, team, organizational, societal
    vision_statement: str = ""  # what is the vision
    alignment: float = 0.5  # 0-1, how aligned was the action
    motivation: float = 0.5  # 0-1, how motivated after
    clarity: float = 0.5  # 0-1, how clear was the vision
    communication: float = 0.5  # 0-1, how well was it communicated
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class VisionKeeper:
    """
    Intelligent vision keeper with drift detection and alignment optimization.
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
            "avg_alignment": 0.0,
            "avg_motivation": 0.0,
            "avg_clarity": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", vision_type: str = "", vision_statement: str = "", alignment: float = 0.5, motivation: float = 0.5, clarity: float = 0.5, communication: float = 0.5, notes: str = "") -> VisionEntry:
        """Record a vision entry."""
        entry_id = f"vis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = VisionEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            vision_type=vision_type or "personal",
            vision_statement=vision_statement,
            alignment=alignment,
            motivation=motivation,
            clarity=clarity,
            communication=communication,
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

    def get_vision_stats(self) -> Dict[str, Any]:
        """Get vision pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "align_sum": 0.0, "mot_sum": 0.0, "clarity_sum": 0.0, "comm_sum": 0.0})
        for e in self._entries:
            by_type[e.vision_type]["count"] += 1
            by_type[e.vision_type]["align_sum"] += e.alignment
            by_type[e.vision_type]["mot_sum"] += e.motivation
            by_type[e.vision_type]["clarity_sum"] += e.clarity
            by_type[e.vision_type]["comm_sum"] += e.communication

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_alignment": round(data["align_sum"] / count, 2),
                "avg_motivation": round(data["mot_sum"] / count, 2),
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_communication": round(data["comm_sum"] / count, 2),
            }

        # Clarity impact
        high_clarity = [e for e in self._entries if e.clarity > 0.7]
        low_clarity = [e for e in self._entries if e.clarity < 0.4]
        if high_clarity and low_clarity:
            high_clarity_align = sum(e.alignment for e in high_clarity) / len(high_clarity)
            low_clarity_align = sum(e.alignment for e in low_clarity) / len(low_clarity)
            high_clarity_mot = sum(e.motivation for e in high_clarity) / len(high_clarity)
            low_clarity_mot = sum(e.motivation for e in low_clarity) / len(low_clarity)
        else:
            high_clarity_align = 0
            low_clarity_align = 0
            high_clarity_mot = 0
            low_clarity_mot = 0

        # Communication impact
        high_comm = [e for e in self._entries if e.communication > 0.7]
        low_comm = [e for e in self._entries if e.communication < 0.4]
        if high_comm and low_comm:
            high_comm_align = sum(e.alignment for e in high_comm) / len(high_comm)
            low_comm_align = sum(e.alignment for e in low_comm) / len(low_comm)
        else:
            high_comm_align = 0
            low_comm_align = 0

        # Drift detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_align = sum(e.alignment for e in recent) / len(recent)
            recent_clarity = sum(e.clarity for e in recent) / len(recent)
            drift_risk = recent_align < 0.4 or recent_clarity < 0.4
        else:
            drift_risk = False

        # Recent trend
        if recent:
            recent_mot = sum(e.motivation for e in recent) / len(recent)
            recent_comm = sum(e.communication for e in recent) / len(recent)
        else:
            recent_mot = 0
            recent_comm = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_align = sum(e.alignment for e in older) / len(older)
            older_clarity = sum(e.clarity for e in older) / len(older)
            align_trend = recent_align - older_align if recent else 0
            clarity_trend = recent_clarity - older_clarity if recent else 0
        else:
            align_trend = 0
            clarity_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "clarity_impact": {
                "high_clarity_alignment": round(high_clarity_align, 2),
                "low_clarity_alignment": round(low_clarity_align, 2),
                "high_clarity_motivation": round(high_clarity_mot, 2),
                "low_clarity_motivation": round(low_clarity_mot, 2),
            },
            "communication_impact": {
                "high_communication_alignment": round(high_comm_align, 2),
                "low_communication_alignment": round(low_comm_align, 2),
            },
            "drift_risk": drift_risk,
            "avg_alignment": round(sum(e.alignment for e in self._entries) / len(self._entries), 2),
            "avg_motivation": round(sum(e.motivation for e in self._entries) / len(self._entries), 2),
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
            "alignment_trend": round(align_trend, 2),
            "clarity_trend": round(clarity_trend, 2),
            "recent_motivation": round(recent_mot, 2),
            "recent_communication": round(recent_comm, 2),
        }

    def get_vision_practice(self, context: str = "", clarity: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "personal": [
                "Write your vision in one sentence. If you can't, it's too vague. Refine until it's clear.",
                "Review your vision weekly. Not daily. Weekly is enough to keep it alive without obsession.",
                "Ask: 'Is what I'm doing today moving me toward my vision?' If not, why not?",
            ],
            "team": [
                "State the vision at the start of every meeting. Not the mission. The vision. The future you're building.",
                "Connect every task to the vision. 'We're doing this because...' Context creates commitment.",
                "Check alignment quarterly. 'Is this still our vision? Does everyone still see it?'",
            ],
            "organizational": [
                "Make the vision visible. Posters. Screensavers. Slack status. Repetition creates belief.",
                "Hire for vision fit. Skills can be taught. Belief in the vision cannot.",
                "Tell stories that illustrate the vision. Abstract visions die. Storytelling visions live.",
            ],
            "societal": [
                "Your personal vision and the world's needs intersect there. That's your calling.",
                "Start small. Global visions begin with local action. One person. One community.",
                "Find others who share the vision. Movements are lonely alone. Community sustains them.",
            ],
            "general": [
                "Vision without action is hallucination. Action without vision is chaos. You need both.",
                "The best visions are slightly impossible. If it's obviously achievable, it's not a vision. It's a plan.",
                "Revisit your vision when you're exhausted. That's when you need it most. Not when you're motivated.",
            ],
        }

        selected = practices.get(context, practices["general"])

        if clarity < 0.3:
            clarity_note = "Low clarity. Start with 'What do I want to be true in 5 years?' Write it down. Refine it."
        elif clarity < 0.6:
            clarity_note = "Moderate clarity. Good start. Now test it. Share it with someone. Does it resonate?"
        else:
            clarity_note = "Good clarity. Now focus on communication. The best vision that no one knows is useless."

        return {
            "context": context or "general",
            "clarity": clarity,
            "practice": random.choice(selected),
            "clarity_note": clarity_note,
            "principle": "Most people don't have a vision. They have a to-do list. A vision is a filter. It tells you what to say yes to and what to say no to. Without it, you say yes to everything and accomplish nothing. With it, you say no to most things and achieve what matters. The vision is not the goal. It's the compass.",
        }

    def get_vision_score(self) -> int:
        """Calculate overall vision health (0-100)."""
        if not self._entries:
            return 35

        # Alignment and motivation
        avg_align = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_mot = sum(e.motivation for e in self._entries) / len(self._entries)

        # Clarity and communication
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_comm = sum(e.communication for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.vision_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_align = sum(e.alignment for e in recent) / len(recent)
            recent_mot = sum(e.motivation for e in recent) / len(recent)
            recent_clarity = sum(e.clarity for e in recent) / len(recent)
            recent_comm = sum(e.communication for e in recent) / len(recent)
        else:
            recent_align = 0
            recent_mot = 0
            recent_clarity = 0
            recent_comm = 0

        # Drift penalty
        drift_penalty = 0
        if recent:
            recent_align_val = sum(e.alignment for e in recent) / len(recent)
            recent_clarity_val = sum(e.clarity for e in recent) / len(recent)
            if recent_align_val < 0.4 or recent_clarity_val < 0.4:
                drift_penalty = 10

        score = (avg_align * 25) + (avg_mot * 15) + (avg_clarity * 20) + (avg_comm * 15) + (unique_types * 2) + (recent_align * 10) + (recent_mot * 10) + (recent_clarity * 10) + (recent_comm * 5) - drift_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_alignment"] = round(sum(e.alignment for e in self._entries) / len(self._entries), 2)
            self._stats["avg_motivation"] = round(sum(e.motivation for e in self._entries) / len(self._entries), 2)
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)

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

    def _log_entry(self, entry: VisionEntry):
        try:
            with open(VISION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "vision_type": entry.vision_type,
                    "vision_statement": entry.vision_statement,
                    "alignment": entry.alignment,
                    "motivation": entry.motivation,
                    "clarity": entry.clarity,
                    "communication": entry.communication,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_vk_instance: Optional[VisionKeeper] = None
_vk_lock = threading.Lock()


def get_vision_keeper() -> VisionKeeper:
    global _vk_instance
    with _vk_lock:
        if _vk_instance is None:
            _vk_instance = VisionKeeper()
        return _vk_instance
