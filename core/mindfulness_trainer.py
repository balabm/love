"""
LOVE Mindfulness Trainer — Awareness Intelligence (Modern AI Pattern)

Most mindfulness is sporadic and shallow. This trainer:

1. MINDFULNESS TRACKING
   - Record mindfulness practices and their characteristics
   - Track practice types (breath, body scan, walking, eating, open awareness)
   - Log practice depth and its correlation with wellbeing

2. PATTERN ANALYSIS
   - Identify the user's mindfulness style (focused, open, body-based, movement-based)
   - Find optimal practice conditions (time, place, duration)
   - Detect practice gaps and their consequences

3. SKILL BUILDING
   - Suggest practices matched to current state and goals
   - Provide progressive deepening exercises
   - Recommend integration practices (mindfulness in daily activities)

4. AWARENESS CULTIVATION
   - Track the correlation between mindfulness and stress, focus, mood
   - Alert when practice is becoming mechanical
   - Celebrate moments of genuine presence

Architecture:
- record_practice(type, duration, depth, distractions): Log practice
- get_mindfulness_stats(): Get mindfulness pattern analysis
- get_practice_suggestion(goal, experience_level): Get suggestion
- get_mindfulness_score(): Calculate overall mindfulness health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "mindfulness_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRACTICE_LOG = DATA_DIR / "practices.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MindfulnessPractice:
    """A tracked mindfulness practice."""
    practice_id: str = ""
    practice_type: str = ""  # breath, body_scan, walking, eating, open_awareness, loving_kindness, noting
    duration_minutes: float = 0.0
    depth: float = 0.5  # 0-1
    distractions: int = 0
    return_to_focus: int = 0  # how many times they returned
    body_awareness: float = 0.0  # 0-1
    emotional_clarity: float = 0.0  # 0-1
    calm_after: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MindfulnessTrainer:
    """
    Intelligent mindfulness trainer with practice matching and progressive deepening.
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
        self._practices: deque = deque(maxlen=300)
        self._stats = {
            "total_practices": 0,
            "avg_depth": 0.0,
            "avg_calm": 0.0,
            "best_type": "",
            "practice_gap": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_practice(self, practice_type: str = "", duration: float = 0, depth: float = 0.5, distractions: int = 0, returns: int = 0, body_awareness: float = 0.0, emotional_clarity: float = 0.0, calm_after: float = 0.0, notes: str = "") -> MindfulnessPractice:
        """Record a mindfulness practice."""
        practice_id = f"mind_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._practices)}"
        practice = MindfulnessPractice(
            practice_id=practice_id,
            practice_type=practice_type or "breath",
            duration_minutes=duration,
            depth=depth,
            distractions=distractions,
            return_to_focus=returns,
            body_awareness=body_awareness,
            emotional_clarity=emotional_clarity,
            calm_after=calm_after,
            notes=notes,
        )

        with self._lock:
            self._practices.append(practice)
            self._stats["total_practices"] += 1
            self._update_stats()

        self._save_stats()
        self._log_practice(practice)

        return practice

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_mindfulness_stats(self) -> Dict[str, Any]:
        """Get mindfulness pattern analysis."""
        if not self._practices:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "calm_sum": 0.0, "duration_sum": 0.0})
        for p in self._practices:
            by_type[p.practice_type]["count"] += 1
            by_type[p.practice_type]["depth_sum"] += p.depth
            by_type[p.practice_type]["calm_sum"] += p.calm_after
            by_type[p.practice_type]["duration_sum"] += p.duration_minutes

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_calm": round(data["calm_sum"] / count, 2),
                "avg_duration": round(data["duration_sum"] / count, 1),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_depth"] + x[1]["avg_calm"]) if type_stats else ("", {})

        # Duration analysis
        short = [p for p in self._practices if p.duration_minutes <= 5]
        medium = [p for p in self._practices if 5 < p.duration_minutes <= 15]
        long_practice = [p for p in self._practices if p.duration_minutes > 15]

        duration_stats = {}
        if short:
            duration_stats["short"] = {"count": len(short), "avg_depth": round(sum(p.depth for p in short) / len(short), 2)}
        if medium:
            duration_stats["medium"] = {"count": len(medium), "avg_depth": round(sum(p.depth for p in medium) / len(medium), 2)}
        if long_practice:
            duration_stats["long"] = {"count": len(long_practice), "avg_depth": round(sum(p.depth for p in long_practice) / len(long_practice), 2)}

        # Distraction analysis
        avg_distractions = sum(p.distractions for p in self._practices) / len(self._practices)
        avg_returns = sum(p.return_to_focus for p in self._practices) / len(self._practices)
        return_rate = avg_returns / max(1, avg_distractions)

        # Practice gap detection
        recent_days = defaultdict(list)
        for p in self._practices:
            day = p.timestamp[:10]
            recent_days[day].append(p)
        if recent_days:
            sorted_days = sorted(recent_days.keys())
            if len(sorted_days) >= 2:
                gaps = [(datetime.strptime(sorted_days[i], "%Y-%m-%d") - datetime.strptime(sorted_days[i-1], "%Y-%m-%d")).days for i in range(1, len(sorted_days))]
                max_gap = max(gaps)
                practice_gap = max_gap > 3
            else:
                practice_gap = False
        else:
            practice_gap = False

        # Depth trend
        recent = list(self._practices)[-14:]
        if recent:
            recent_depth = sum(p.depth for p in recent) / len(recent)
        else:
            recent_depth = 0
        older = list(self._practices)[:-14] if len(self._practices) > 14 else []
        if older:
            older_depth = sum(p.depth for p in older) / len(older)
            depth_trend = recent_depth - older_depth
        else:
            depth_trend = 0

        return {
            "total_practices": len(self._practices),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "duration_stats": duration_stats,
            "avg_distractions": round(avg_distractions, 1),
            "avg_returns": round(avg_returns, 1),
            "return_rate": round(return_rate, 2),
            "practice_gap": practice_gap,
            "avg_depth": round(sum(p.depth for p in self._practices) / len(self._practices), 2),
            "avg_calm": round(sum(p.calm_after for p in self._practices) / len(self._practices), 2),
            "depth_trend": round(depth_trend, 2),
        }

    def get_practice_suggestion(self, goal: str = "", experience_level: float = 0.5) -> Dict[str, Any]:
        """Get suggestion."""
        practices = {
            "stress": [
                "Breath awareness: Follow 10 breaths. When distracted, start again.",
                "Body scan: Notice tension. Breathe into it. Let it soften.",
                "Loving-kindness: 'May I be peaceful. May I be free from stress.'",
            ],
            "focus": [
                "Focused attention: Pick one object. Notice every detail for 5 minutes.",
                "Noting practice: Label distractions. 'Thinking,' 'Hearing,' 'Feeling.' Return.",
                "One breath at a time. Nothing else exists except this breath.",
            ],
            "sleep": [
                "Body scan lying down. Start at toes. Move up. Don't reach the head.",
                "Countdown meditation: 100... 99... 98... Let each number fade.",
                "Loving-kindness for yourself. 'May I rest deeply. May I be at peace.'",
            ],
            "emotion": [
                "RAIN technique: Recognize, Allow, Investigate, Nurture.",
                "Open awareness: Let emotions come and go like weather. You're the sky.",
                "Noting emotions: 'Anger.' 'Sadness.' Label without judgment.",
            ],
            "body": [
                "Walking meditation: Feel each step. Heel, arch, toe. Slow and deliberate.",
                "Mindful eating: One bite. Taste, texture, temperature. Chew 20 times.",
                "Body scan: Notice every sensation. Pleasant, unpleasant, neutral.",
            ],
            "general": [
                "Breath counting: 1 on inhale, 2 on exhale. Up to 10. Start again.",
                "Open awareness: Just sit. Let experience come to you. No agenda.",
                "5-minute mini-practice: Set a timer. Follow breath. That's enough.",
            ],
        }

        selected = practices.get(goal, practices["general"])

        if experience_level < 0.3:
            level_note = "Beginner. Start with 5 minutes. Consistency beats duration."
        elif experience_level < 0.6:
            level_note = "Intermediate. Experiment with different practices. Find what fits."
        else:
            level_note = "Advanced. Deepen your practice. Longer sits, more subtle awareness."

        return {
            "goal": goal or "general",
            "experience_level": experience_level,
            "suggestion": random.choice(selected),
            "level_note": level_note,
            "reminder": "Mindfulness is not about stopping thoughts. It's about noticing them without being swept away. The goal is awareness, not emptiness.",
        }

    def get_mindfulness_score(self) -> int:
        """Calculate overall mindfulness health (0-100)."""
        if not self._practices:
            return 25

        # Depth
        avg_depth = sum(p.depth for p in self._practices) / len(self._practices)

        # Calm after
        avg_calm = sum(p.calm_after for p in self._practices) / len(self._practices)

        # Return rate (noticing distraction and returning)
        avg_distractions = sum(p.distractions for p in self._practices) / len(self._practices)
        avg_returns = sum(p.return_to_focus for p in self._practices) / len(self._practices)
        return_rate = avg_returns / max(1, avg_distractions)

        # Body awareness
        avg_body = sum(p.body_awareness for p in self._practices) / len(self._practices)

        # Emotional clarity
        avg_clarity = sum(p.emotional_clarity for p in self._practices) / len(self._practices)

        # Consistency
        recent_days = defaultdict(list)
        for p in self._practices:
            day = p.timestamp[:10]
            recent_days[day].append(p)
        if recent_days:
            active_days = len(recent_days)
            sorted_days = sorted(recent_days.keys())
            if len(sorted_days) >= 2:
                total_span = (datetime.strptime(sorted_days[-1], "%Y-%m-%d") - datetime.strptime(sorted_days[0], "%Y-%m-%d")).days + 1
                consistency = active_days / total_span
            else:
                consistency = 1
        else:
            consistency = 0

        # Recent trend
        recent = list(self._practices)[-14:]
        if recent:
            recent_depth = sum(p.depth for p in recent) / len(recent)
        else:
            recent_depth = 0

        score = (avg_depth * 20) + (avg_calm * 15) + (return_rate * 15) + (avg_body * 15) + (avg_clarity * 10) + (consistency * 15) + (recent_depth * 5)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._practices:
            self._stats["avg_depth"] = round(sum(p.depth for p in self._practices) / len(self._practices), 2)
            self._stats["avg_calm"] = round(sum(p.calm_after for p in self._practices) / len(self._practices), 2)

            by_type = defaultdict(lambda: {"depth": 0.0, "calm": 0.0, "count": 0})
            for p in self._practices:
                by_type[p.practice_type]["depth"] += p.depth
                by_type[p.practice_type]["calm"] += p.calm_after
                by_type[p.practice_type]["count"] += 1
            if by_type:
                best = max(by_type.items(), key=lambda x: (x[1]["depth"] + x[1]["calm"]) / max(1, x[1]["count"]))
                self._stats["best_type"] = best[0]

            recent_days = defaultdict(list)
            for p in self._practices:
                day = p.timestamp[:10]
                recent_days[day].append(p)
            if recent_days:
                sorted_days = sorted(recent_days.keys())
                if len(sorted_days) >= 2:
                    gaps = [(datetime.strptime(sorted_days[i], "%Y-%m-%d") - datetime.strptime(sorted_days[i-1], "%Y-%m-%d")).days for i in range(1, len(sorted_days))]
                    self._stats["practice_gap"] = max(gaps) > 3

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

    def _log_practice(self, practice: MindfulnessPractice):
        try:
            with open(PRACTICE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": practice.timestamp,
                    "type": practice.practice_type,
                    "duration": practice.duration_minutes,
                    "depth": practice.depth,
                    "distractions": practice.distractions,
                    "returns": practice.return_to_focus,
                    "calm": practice.calm_after,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mt_instance: Optional[MindfulnessTrainer] = None
_mt_lock = threading.Lock()


    
def get_mindfulness_trainer() -> MindfulnessTrainer:
    global _mt_instance
    with _mt_lock:
        if _mt_instance is None:
            _mt_instance = MindfulnessTrainer()
        return _mt_instance
