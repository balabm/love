"""
LOVE Forgiveness Tracker — Emotional Freedom Intelligence (Modern AI Pattern)

Most forgiveness is either forced or avoided. This tracker:

1. FORGIVENESS TRACKING
   - Record forgiveness attempts for self and others
   - Track the emotional weight before and after forgiveness
   - Log what made forgiveness possible or blocked it

2. PATTERN ANALYSIS
   - Identify who/what the user struggles to forgive
   - Detect whether the user is harder on themselves or others
   - Find which forgiveness methods work best

3. PROCESS GUIDANCE
   - Suggest forgiveness steps based on the relationship
   - Provide scripts for requesting or offering forgiveness
   - Track the stages: hurt, anger, understanding, release

4. PROACTIVE SUPPORT
   - Alert when resentment is accumulating
   - Suggest forgiveness practices for ongoing grudges
   - Track the health impact of held resentments

Architecture:
- record_forgiveness(who, what, type, weight_before, weight_after): Log forgiveness
- get_forgiveness_stats(): Get forgiveness pattern analysis
- get_forgiveness_suggestion(who, duration): Get tailored guidance
- get_forgiveness_score(): Calculate emotional freedom level
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "forgiveness_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FORGIVENESS_LOG = DATA_DIR / "forgiveness.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Forgiveness:
    """A tracked forgiveness moment."""
    forgiveness_id: str = ""
    who: str = ""  # who is being forgiven (or "self")
    what: str = ""  # what happened
    forgiveness_type: str = ""  # self, other, received
    weight_before: float = 0.5  # 0-1, emotional burden
    weight_after: float = 0.5
    method: str = ""  # letter, conversation, ritual, time, understanding
    stage: str = ""  # hurt, anger, understanding, release, complete
    blocked_by: str = ""  # what's blocking forgiveness
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ForgivenessTracker:
    """
    Intelligent forgiveness tracker with process guidance and health monitoring.
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
        self._forgivenesses: deque = deque(maxlen=200)
        self._stats = {
            "total_forgivenesses": 0,
            "avg_weight_before": 0.0,
            "avg_weight_after": 0.0,
            "release_rate": 0.0,
            "hardest_to_forgive": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_forgiveness(self, who: str = "", what: str = "", forgiveness_type: str = "", weight_before: float = 0.5, weight_after: float = 0.5, method: str = "", stage: str = "", blocked_by: str = "", notes: str = "") -> Forgiveness:
        """Record a forgiveness moment."""
        forgiveness_id = f"forgive_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._forgivenesses)}"
        f = Forgiveness(
            forgiveness_id=forgiveness_id,
            who=who or "unspecified",
            what=what,
            forgiveness_type=forgiveness_type or "other",
            weight_before=weight_before,
            weight_after=weight_after,
            method=method or "time",
            stage=stage or "understanding",
            blocked_by=blocked_by,
            notes=notes,
        )

        with self._lock:
            self._forgivenesses.append(f)
            self._stats["total_forgivenesses"] += 1
            self._update_stats()

        self._save_stats()
        self._log_forgiveness(f)

        return f

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_forgiveness_stats(self) -> Dict[str, Any]:
        """Get forgiveness pattern analysis."""
        if not self._forgivenesses:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "weight_before_sum": 0.0, "weight_after_sum": 0.0, "release": 0})
        for f in self._forgivenesses:
            by_type[f.forgiveness_type]["count"] += 1
            by_type[f.forgiveness_type]["weight_before_sum"] += f.weight_before
            by_type[f.forgiveness_type]["weight_after_sum"] += f.weight_after
            if f.weight_after < 0.3:
                by_type[f.forgiveness_type]["release"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_weight_before": round(data["weight_before_sum"] / count, 2),
                "avg_weight_after": round(data["weight_after_sum"] / count, 2),
                "release_rate": round(data["release"] / count, 2),
            }

        # Who analysis
        by_who = defaultdict(lambda: {"count": 0, "weight_before_sum": 0.0, "weight_after_sum": 0.0, "blocked": 0})
        for f in self._forgivenesses:
            by_who[f.who]["count"] += 1
            by_who[f.who]["weight_before_sum"] += f.weight_before
            by_who[f.who]["weight_after_sum"] += f.weight_after
            if f.weight_after > 0.5:
                by_who[f.who]["blocked"] += 1

        who_stats = {}
        for w, data in by_who.items():
            count = data["count"]
            who_stats[w] = {
                "count": count,
                "avg_weight_before": round(data["weight_before_sum"] / count, 2),
                "avg_weight_after": round(data["weight_after_sum"] / count, 2),
                "blocked_rate": round(data["blocked"] / count, 2),
            }

        # Hardest to forgive
        hardest = max(who_stats.items(), key=lambda x: x[1]["avg_weight_after"]) if who_stats else ("", {})

        # Method effectiveness
        by_method = defaultdict(lambda: {"count": 0, "weight_change": 0.0})
        for f in self._forgivenesses:
            by_method[f.method]["count"] += 1
            by_method[f.method]["weight_change"] += (f.weight_before - f.weight_after)

        method_stats = {}
        for m, data in by_method.items():
            count = data["count"]
            method_stats[m] = {
                "count": count,
                "avg_weight_release": round(data["weight_change"] / count, 2),
            }

        return {
            "total_forgivenesses": len(self._forgivenesses),
            "type_stats": type_stats,
            "who_stats": who_stats,
            "hardest_to_forgive": hardest[0],
            "method_stats": method_stats,
            "avg_weight_before": round(sum(f.weight_before for f in self._forgivenesses) / len(self._forgivenesses), 2),
            "avg_weight_after": round(sum(f.weight_after for f in self._forgivenesses) / len(self._forgivenesses), 2),
            "overall_release": round(sum(1 for f in self._forgivenesses if f.weight_after < 0.3) / len(self._forgivenesses), 2),
        }

    def get_forgiveness_suggestion(self, who: str = "", duration_months: int = 0, forgiveness_type: str = "") -> Dict[str, Any]:
        """Get tailored forgiveness guidance."""
        suggestions = {
            "self": {
                "approach": "Treat yourself as you would a dear friend",
                "steps": [
                    "Acknowledge the pain you caused yourself",
                    "Recognize you did the best you could with what you knew",
                    "Write a letter of forgiveness to yourself",
                    "Do one kind thing for yourself today",
                ],
                "script": "I forgive myself for [specific action]. I was doing my best. I choose to release this burden.",
            },
            "other": {
                "approach": "Forgiveness is for you, not them",
                "steps": [
                    "Acknowledge the hurt without minimizing it",
                    "Understand their humanity (not excuse, but explain)",
                    "Decide what forgiveness means for you (don't have to reconcile)",
                    "Release the expectation that they change",
                ],
                "script": "I release the hold this has on me. Their actions were about them. My peace is about me.",
            },
            "received": {
                "approach": "Accept that you are forgivable",
                "steps": [
                    "Listen without defending",
                    "Acknowledge the hurt you caused",
                    "Accept their forgiveness without self-flagellation",
                    "Commit to doing better, then let it go",
                ],
                "script": "Thank you for forgiving me. I will carry this as a lesson, not a burden.",
            },
        }

        base = suggestions.get(forgiveness_type, suggestions["other"])

        # Duration adjustments
        if duration_months > 12:
            base["note"] = "This has been heavy for a long time. Consider professional support if you're stuck."
            base["steps"].insert(0, "Consider talking to a therapist about this")
        elif duration_months > 6:
            base["note"] = "You've carried this for a while. You deserve to set it down."
            base["steps"].append("Do a physical ritual: write it down and burn/bury it")
        else:
            base["note"] = "Early in the process. Be patient with yourself."

        return {
            **base,
            "who": who,
            "duration": f"{duration_months} months" if duration_months else "unspecified",
        }

    def get_forgiveness_score(self) -> int:
        """Calculate emotional freedom level (0-100)."""
        if not self._forgivenesses:
            return 50

        # Release rate (weight_after < 0.3)
        released = sum(1 for f in self._forgivenesses if f.weight_after < 0.3)
        release_rate = released / len(self._forgivenesses)

        # Average weight reduction
        avg_reduction = sum(f.weight_before - f.weight_after for f in self._forgivenesses) / len(self._forgivenesses)

        # Self vs other balance
        self_forgiveness = [f for f in self._forgivenesses if f.forgiveness_type == "self"]
        other_forgiveness = [f for f in self._forgivenesses if f.forgiveness_type == "other"]
        
        balance = 1.0
        if self_forgiveness and other_forgiveness:
            self_release = sum(1 for f in self_forgiveness if f.weight_after < 0.3) / len(self_forgiveness)
            other_release = sum(1 for f in other_forgiveness if f.weight_after < 0.3) / len(other_forgiveness)
            balance = 1 - abs(self_release - other_release)

        # Recent trend
        recent = [f for f in self._forgivenesses if f.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_reduction = sum(f.weight_before - f.weight_after for f in recent) / len(recent)
        else:
            recent_reduction = avg_reduction

        score = (release_rate * 30) + (avg_reduction * 30) + (balance * 20) + (recent_reduction * 20)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._forgivenesses:
            self._stats["avg_weight_before"] = round(sum(f.weight_before for f in self._forgivenesses) / len(self._forgivenesses), 2)
            self._stats["avg_weight_after"] = round(sum(f.weight_after for f in self._forgivenesses) / len(self._forgivenesses), 2)
            released = sum(1 for f in self._forgivenesses if f.weight_after < 0.3)
            self._stats["release_rate"] = round(released / len(self._forgivenesses), 2)

            by_who = defaultdict(lambda: {"weight_after": 0.0, "count": 0})
            for f in self._forgivenesses:
                by_who[f.who]["weight_after"] += f.weight_after
                by_who[f.who]["count"] += 1
            
            if by_who:
                hardest = max(by_who.items(), key=lambda x: x[1]["weight_after"] / max(1, x[1]["count"]))
                self._stats["hardest_to_forgive"] = hardest[0]

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

    def _log_forgiveness(self, forgiveness: Forgiveness):
        try:
            with open(FORGIVENESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": forgiveness.timestamp,
                    "who": forgiveness.who,
                    "type": forgiveness.forgiveness_type,
                    "weight_before": forgiveness.weight_before,
                    "weight_after": forgiveness.weight_after,
                    "stage": forgiveness.stage,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ft_instance: Optional[ForgivenessTracker] = None
_ft_lock = threading.Lock()


def get_forgiveness_tracker() -> ForgivenessTracker:
    global _ft_instance
    with _ft_lock:
        if _ft_instance is None:
            _ft_instance = ForgivenessTracker()
        return _ft_instance
