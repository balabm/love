"""
LOVE Purpose Navigator — Direction Intelligence (Modern AI Pattern)

Most people drift without a compass. This navigator:

1. PURPOSE TRACKING
   - Record purpose-aligned and purpose-misaligned activities
   - Track the felt sense of purpose in different life areas
   - Log decisions made with/against purpose

2. PATTERN ANALYSIS
   - Identify the user's purpose themes (service, creation, discovery, protection, connection, expression)
   - Find where purpose feels strong vs absent
   - Detect purpose drift and its causes

3. NAVIGATION GUIDANCE
   - Suggest small purpose-aligned actions for today
   - Provide purpose-clarifying questions and exercises
   - Recommend purpose experiments (try something for a week)

4. ALIGNMENT SUPPORT
   - Track the percentage of time spent in purpose-aligned activities
   - Alert when drift exceeds threshold
   - Celebrate purpose-aligned decisions

Architecture:
- record_alignment(activity, aligned, purpose_theme, felt_sense): Log alignment
- get_purpose_stats(): Get purpose pattern analysis
- get_navigation_suggestion(current_drift): Get corrective action
- get_purpose_score(): Calculate overall purpose alignment
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

DATA_DIR = Path(__file__).parent.parent / "data" / "purpose_navigator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PURPOSE_LOG = DATA_DIR / "purpose.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class PurposeAlignment:
    """A tracked purpose alignment moment."""
    alignment_id: str = ""
    activity: str = ""
    aligned: bool = True
    purpose_theme: str = ""  # service, creation, discovery, protection, connection, expression, mastery
    felt_sense: float = 0.5  # 0-1, how purposeful it felt
    life_area: str = ""  # work, relationships, health, creativity, community, spirituality
    hours_spent: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PurposeNavigator:
    """
    Intelligent purpose navigator with drift detection and alignment guidance.
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
        self._alignments: deque = deque(maxlen=300)
        self._stats = {
            "total_alignments": 0,
            "alignment_rate": 0.0,
            "avg_felt_sense": 0.0,
            "dominant_theme": "",
            "drift_score": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_alignment(self, activity: str = "", aligned: bool = True, purpose_theme: str = "", felt_sense: float = 0.5, life_area: str = "", hours: float = 0, notes: str = "") -> PurposeAlignment:
        """Record a purpose alignment moment."""
        alignment_id = f"purpose_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._alignments)}"
        pa = PurposeAlignment(
            alignment_id=alignment_id,
            activity=activity or "unspecified",
            aligned=aligned,
            purpose_theme=purpose_theme or "service",
            felt_sense=felt_sense,
            life_area=life_area or "work",
            hours_spent=hours,
            notes=notes,
        )

        with self._lock:
            self._alignments.append(pa)
            self._stats["total_alignments"] += 1
            self._update_stats()

        self._save_stats()
        self._log_alignment(pa)

        return pa

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_purpose_stats(self) -> Dict[str, Any]:
        """Get purpose pattern analysis."""
        if not self._alignments:
            return {"status": "insufficient_data"}

        # Theme analysis
        by_theme = defaultdict(lambda: {"count": 0, "aligned": 0, "felt_sum": 0.0, "hours": 0.0})
        for a in self._alignments:
            by_theme[a.purpose_theme]["count"] += 1
            if a.aligned:
                by_theme[a.purpose_theme]["aligned"] += 1
            by_theme[a.purpose_theme]["felt_sum"] += a.felt_sense
            by_theme[a.purpose_theme]["hours"] += a.hours_spent

        theme_stats = {}
        for t, data in by_theme.items():
            count = data["count"]
            theme_stats[t] = {
                "count": count,
                "alignment_rate": round(data["aligned"] / count, 2),
                "avg_felt_sense": round(data["felt_sum"] / count, 2),
                "total_hours": round(data["hours"], 1),
            }

        dominant = max(theme_stats.items(), key=lambda x: x[1]["count"]) if theme_stats else ("", {})

        # Life area analysis
        by_area = defaultdict(lambda: {"count": 0, "aligned": 0, "hours": 0.0})
        for a in self._alignments:
            by_area[a.life_area]["count"] += 1
            if a.aligned:
                by_area[a.life_area]["aligned"] += 1
            by_area[a.life_area]["hours"] += a.hours_spent

        area_stats = {}
        for area, data in by_area.items():
            count = data["count"]
            area_stats[area] = {
                "count": count,
                "alignment_rate": round(data["aligned"] / count, 2),
                "total_hours": round(data["hours"], 1),
            }

        # Drift detection
        recent = [a for a in self._alignments if a.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_aligned = sum(1 for a in recent if a.aligned)
            recent_rate = recent_aligned / len(recent)
            older = [a for a in self._alignments if a.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if older:
                older_aligned = sum(1 for a in older if a.aligned)
                older_rate = older_aligned / len(older)
                drift = older_rate - recent_rate
            else:
                drift = 0
        else:
            drift = 0
            recent_rate = 0

        return {
            "total_alignments": len(self._alignments),
            "theme_stats": theme_stats,
            "dominant_theme": dominant[0],
            "area_stats": area_stats,
            "alignment_rate": round(sum(1 for a in self._alignments if a.aligned) / len(self._alignments), 2),
            "avg_felt_sense": round(sum(a.felt_sense for a in self._alignments) / len(self._alignments), 2),
            "drift": round(drift, 2),
            "recent_alignment_rate": round(recent_rate, 2),
            "drifting": drift > 0.15,
        }

    def get_navigation_suggestion(self, drift: float = 0.0, theme: str = "", time: float = 30) -> Dict[str, Any]:
        """Get corrective action."""
        if drift > 0.3:
            urgency = "high"
            message = "You've drifted significantly. One purpose-aligned action today matters more than usual."
        elif drift > 0.15:
            urgency = "medium"
            message = "Purpose drift detected. Small correction now prevents big correction later."
        else:
            urgency = "low"
            message = "Purpose alignment is good. Deepen it with one meaningful action."

        quick_actions = {
            "service": "Help one person with something you're good at. No expectation of return.",
            "creation": "Make something that didn't exist this morning. Even 5 minutes counts.",
            "discovery": "Learn one thing that changes how you see something familiar.",
            "protection": "Stand up for someone or something vulnerable today.",
            "connection": "Reach out to someone you care about. Not for a reason. Just because.",
            "expression": "Say or write something true that you've been holding in.",
            "mastery": "Practice one thing you want to be excellent at. Deliberately, not passively.",
        }

        action = quick_actions.get(theme, random.choice(list(quick_actions.values())))

        return {
            "urgency": urgency,
            "message": message,
            "action": action,
            "theme": theme or "general",
            "time": time,
            "reflection": "Afterward: Did that feel like 'you'? What made it matter?",
        }

    def get_purpose_score(self) -> int:
        """Calculate overall purpose alignment (0-100)."""
        if not self._alignments:
            return 45

        # Alignment rate
        aligned = sum(1 for a in self._alignments if a.aligned)
        alignment_rate = aligned / len(self._alignments)

        # Felt sense
        avg_felt = sum(a.felt_sense for a in self._alignments) / len(self._alignments)

        # Recent alignment
        recent = [a for a in self._alignments if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_aligned = sum(1 for a in recent if a.aligned)
            recent_rate = recent_aligned / len(recent)
        else:
            recent_rate = alignment_rate

        # Hours in aligned activities
        aligned_hours = sum(a.hours_spent for a in self._alignments if a.aligned)
        total_hours = sum(a.hours_spent for a in self._alignments)
        hour_ratio = aligned_hours / max(1, total_hours)

        score = (alignment_rate * 30) + (avg_felt * 25) + (recent_rate * 20) + (hour_ratio * 25)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._alignments:
            aligned = sum(1 for a in self._alignments if a.aligned)
            self._stats["alignment_rate"] = round(aligned / len(self._alignments), 2)
            self._stats["avg_felt_sense"] = round(sum(a.felt_sense for a in self._alignments) / len(self._alignments), 2)

            by_theme = defaultdict(lambda: {"aligned": 0, "total": 0})
            for a in self._alignments:
                by_theme[a.purpose_theme]["total"] += 1
                if a.aligned:
                    by_theme[a.purpose_theme]["aligned"] += 1
            
            if by_theme:
                dominant = max(by_theme.items(), key=lambda x: x[1]["total"])
                self._stats["dominant_theme"] = dominant[0]

            recent = [a for a in self._alignments if a.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
            if recent and len(self._alignments) > len(recent):
                recent_aligned = sum(1 for a in recent if a.aligned)
                older_aligned = sum(1 for a in self._alignments if a.timestamp <= (datetime.now() - timedelta(days=14)).isoformat() and a.aligned)
                older_total = len(self._alignments) - len(recent)
                self._stats["drift_score"] = round((older_aligned / max(1, older_total)) - (recent_aligned / max(1, len(recent))), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.purpose_navigator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.purpose_navigator")

    def _log_alignment(self, alignment: PurposeAlignment):
        try:
            with open(PURPOSE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": alignment.timestamp,
                    "activity": alignment.activity,
                    "aligned": alignment.aligned,
                    "theme": alignment.purpose_theme,
                    "felt_sense": alignment.felt_sense,
                    "area": alignment.life_area,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.purpose_navigator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pn_instance: Optional[PurposeNavigator] = None
_pn_lock = threading.Lock()


def get_purpose_navigator() -> PurposeNavigator:
    global _pn_instance
    with _pn_lock:
        if _pn_instance is None:
            _pn_instance = PurposeNavigator()
        return _pn_instance
