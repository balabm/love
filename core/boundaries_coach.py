"""
LOVE Boundaries Coach — Self-Respect Intelligence (Modern AI Pattern)

Most boundary advice is guilt-laden. This coach:

1. BOUNDARY TRACKING
   - Record boundary settings and their outcomes
   - Track violations, enforcements, and consequences
   - Log emotional cost of maintaining vs abandoning boundaries

2. PATTERN ANALYSIS
   - Identify which boundaries are respected vs repeatedly violated
   - Detect boundary erosion over time
   - Find which areas of life have the weakest boundaries

3. SMART BOUNDARY DESIGN
   - Generate boundary scripts for specific situations
   - Suggest incremental boundary strengthening
   - Recommend boundary maintenance frequency

4. PROACTIVE SUPPORT
   - Alert when boundary violations are trending up
   - Suggest pre-emptive boundaries before predictable stressors
   - Track boundary confidence and guilt levels

Architecture:
- record_boundary(area, boundary, outcome): Log boundary
- get_boundary_stats(): Get boundary health analysis
- get_boundary_script(situation): Get specific boundary language
- get_boundary_strength_score(): Calculate overall boundary health
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "boundaries_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BOUNDARY_LOG = DATA_DIR / "boundaries.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Boundary:
    """A tracked boundary."""
    boundary_id: str = ""
    area: str = ""  # work, family, romantic, friends, self, digital, time
    boundary_text: str = ""  # the actual boundary statement
    context: str = ""  # when/where it applies
    enforcement_level: str = "medium"  # soft, medium, firm, absolute
    outcome: str = ""  # respected, violated_once, repeatedly_violated, abandoned
    emotional_cost: float = 0.3  # guilt, anxiety, fear of rejection
    confidence_level: float = 0.5  # 0-1
    consequences_set: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class BoundariesCoach:
    """
    Intelligent boundaries coach with pattern analysis and script generation.
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
        self._boundaries: deque = deque(maxlen=200)
        self._stats = {
            "total_boundaries": 0,
            "respected_rate": 0.0,
            "avg_confidence": 0.0,
            "avg_emotional_cost": 0.0,
            "weakest_area": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_boundary(self, area: str = "", boundary_text: str = "", context: str = "", enforcement: str = "medium", outcome: str = "", emotional_cost: float = 0.3, confidence: float = 0.5, consequences_set: bool = False, notes: str = "") -> Boundary:
        """Record a boundary."""
        boundary_id = f"boundary_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._boundaries)}"
        boundary = Boundary(
            boundary_id=boundary_id,
            area=area or "general",
            boundary_text=boundary_text or "unspecified",
            context=context,
            enforcement_level=enforcement,
            outcome=outcome or "respected",
            emotional_cost=emotional_cost,
            confidence_level=confidence,
            consequences_set=consequences_set,
            notes=notes,
        )

        with self._lock:
            self._boundaries.append(boundary)
            self._stats["total_boundaries"] += 1
            self._update_stats()

        self._save_stats()
        self._log_boundary(boundary)

        return boundary

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_boundary_stats(self) -> Dict[str, Any]:
        """Get boundary health analysis."""
        if not self._boundaries:
            return {"status": "insufficient_data"}

        # Area analysis
        by_area = defaultdict(lambda: {"count": 0, "respected": 0, "violated": 0, "avg_confidence": 0.0, "avg_cost": 0.0})
        for b in self._boundaries:
            area = b.area
            by_area[area]["count"] += 1
            if b.outcome == "respected":
                by_area[area]["respected"] += 1
            else:
                by_area[area]["violated"] += 1
            by_area[area]["avg_confidence"] += b.confidence_level
            by_area[area]["avg_cost"] += b.emotional_cost

        area_stats = {}
        for area, data in by_area.items():
            count = data["count"]
            area_stats[area] = {
                "count": count,
                "respected_rate": round(data["respected"] / count, 2),
                "violation_rate": round(data["violated"] / count, 2),
                "avg_confidence": round(data["avg_confidence"] / count, 2),
                "avg_emotional_cost": round(data["avg_cost"] / count, 2),
                "health": "strong" if data["respected"] / count > 0.7 else "moderate" if data["respected"] / count > 0.4 else "weak",
            }

        # Weakest area
        weakest = min(area_stats.items(), key=lambda x: x[1]["respected_rate"]) if area_stats else ("", {})

        # Trend analysis
        recent = [b for b in self._boundaries if b.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_respected = sum(1 for b in recent if b.outcome == "respected")
            recent_rate = recent_respected / len(recent)
            trend = "improving" if recent_rate > 0.6 else "declining" if recent_rate < 0.4 else "stable"
        else:
            trend = "stable"

        return {
            "total_boundaries": len(self._boundaries),
            "area_stats": area_stats,
            "weakest_area": weakest[0],
            "weakest_area_rate": weakest[1].get("respected_rate", 0),
            "overall_respected_rate": round(sum(1 for b in self._boundaries if b.outcome == "respected") / len(self._boundaries), 2),
            "trend": trend,
            "avg_confidence": round(sum(b.confidence_level for b in self._boundaries) / len(self._boundaries), 2),
        }

    def get_boundary_script(self, situation: str = "", area: str = "", severity: str = "medium") -> Dict[str, Any]:
        """Get specific boundary language."""
        scripts = {
            "work": {
                "soft": "I prefer not to take calls after 6 PM. I'll respond by 9 AM the next day.",
                "medium": "I can't take on that project right now. My plate is full until [date].",
                "firm": "I'm not available for overtime this week. My work hours are 9-5.",
                "absolute": "I will not work weekends. Period.",
            },
            "family": {
                "soft": "I'd appreciate a heads-up before you drop by.",
                "medium": "I need some space this weekend. I'll call you Tuesday.",
                "firm": "I won't discuss my salary/career at family dinners anymore.",
                "absolute": "If you insult my partner, I will leave immediately.",
            },
            "romantic": {
                "soft": "I need a little alone time to recharge. It's not about you.",
                "medium": "I need you to tell me if you'll be late. It helps me plan.",
                "firm": "I won't tolerate being yelled at. Let's talk when we're calm.",
                "absolute": "If this happens again, I'm ending the relationship.",
            },
            "friends": {
                "soft": "I'm saving money right now, so I'll skip the expensive dinners.",
                "medium": "I can't be your only support person. I care, but I can't carry this alone.",
                "firm": "I need our plans to be respected. Last-minute cancellations drain me.",
                "absolute": "I won't lend money anymore. Let's keep friendship and finances separate.",
            },
            "self": {
                "soft": "I'll try to get to bed by 10 PM tonight.",
                "medium": "I'm saying no to that invitation. I need rest.",
                "firm": "I will not check work email on vacation.",
                "absolute": "My health comes first. Everything else is secondary.",
            },
            "digital": {
                "soft": "I prefer text over calls unless it's urgent.",
                "medium": "I won't respond to work messages after 7 PM.",
                "firm": "I need you to ask before posting photos of me online.",
                "absolute": "I block anyone who sends me hate messages. No exceptions.",
            },
            "time": {
                "soft": "Can we keep this meeting to 30 minutes?",
                "medium": "I have until 3 PM free. After that, I'm unavailable.",
                "firm": "I don't do same-day requests anymore. Plan ahead.",
                "absolute": "My morning focus time is sacred. No interruptions.",
            },
        }

        base = scripts.get(area, scripts["self"])
        script = base.get(severity, base["medium"])

        return {
            "area": area,
            "severity": severity,
            "script": script,
            "delivery_tips": [
                "Use 'I' statements, not 'you' accusations",
                "Keep it short and clear",
                "Don't over-explain or apologize",
                "Repeat calmly if challenged",
            ],
            "situation": situation,
        }

    def get_boundary_strength_score(self) -> int:
        """Calculate overall boundary health (0-100)."""
        if not self._boundaries:
            return 50

        # Respected rate
        respected = sum(1 for b in self._boundaries if b.outcome == "respected")
        rate = respected / len(self._boundaries)

        # Confidence
        avg_confidence = sum(b.confidence_level for b in self._boundaries) / len(self._boundaries)

        # Consequences set
        consequences = sum(1 for b in self._boundaries if b.consequences_set)
        consequence_rate = consequences / len(self._boundaries)

        # Emotional cost (lower is better)
        avg_cost = sum(b.emotional_cost for b in self._boundaries) / len(self._boundaries)

        score = (rate * 40) + (avg_confidence * 30) + (consequence_rate * 20) + ((1 - avg_cost) * 10)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._boundaries:
            respected = sum(1 for b in self._boundaries if b.outcome == "respected")
            self._stats["respected_rate"] = round(respected / len(self._boundaries), 2)
            self._stats["avg_confidence"] = round(sum(b.confidence_level for b in self._boundaries) / len(self._boundaries), 2)
            self._stats["avg_emotional_cost"] = round(sum(b.emotional_cost for b in self._boundaries) / len(self._boundaries), 2)

            by_area = defaultdict(lambda: {"respected": 0, "total": 0})
            for b in self._boundaries:
                by_area[b.area]["total"] += 1
                if b.outcome == "respected":
                    by_area[b.area]["respected"] += 1
            
            if by_area:
                weakest = min(by_area.items(), key=lambda x: x[1]["respected"] / max(1, x[1]["total"]))
                self._stats["weakest_area"] = weakest[0]

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

    def _log_boundary(self, boundary: Boundary):
        try:
            with open(BOUNDARY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": boundary.timestamp,
                    "area": boundary.area,
                    "boundary": boundary.boundary_text,
                    "outcome": boundary.outcome,
                    "confidence": boundary.confidence_level,
                    "emotional_cost": boundary.emotional_cost,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_bc_instance: Optional[BoundariesCoach] = None
_bc_lock = threading.Lock()


def get_boundaries_coach() -> BoundariesCoach:
    global _bc_instance
    with _bc_lock:
        if _bc_instance is None:
            _bc_instance = BoundariesCoach()
        return _bc_instance
