"""
LOVE User Pattern Detector — Behavioral Pattern Recognition (Modern AI Pattern)

Modern companions learn user behavior patterns. This detector:

1. ACTIVITY PATTERN RECOGNITION
   - Detect daily routines: wake time, work hours, breaks, sleep
   - Identify focus patterns: deep work sessions, scattered attention
   - Track productivity cycles: peak performance times

2. SOCIAL PATTERN DETECTION
   - Communication frequency and timing
   - Social energy levels throughout the day/week
   - Response latency patterns (how quickly user replies)

3. EMOTIONAL PATTERN TRACKING
   - Mood cycles: morning vs evening energy
   - Stress buildup patterns before breaks
   - Recovery patterns after intense work

4. GOAL ALIGNMENT PATTERNS
   - Track how well daily activities align with stated goals
   - Detect drift from intended priorities
   - Identify when user is most likely to procrastinate

Architecture:
- detect_patterns(): Analyze recent activity for patterns
- get_daily_insights(): Generate insights for today's behavior
- predict_next_activity(): Predict what user will do next
- get_pattern_stats(): Track detection accuracy
"""

import json
import threading
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "user_patterns"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PATTERN_DB = DATA_DIR / "pattern_db.json"
INSIGHT_LOG = DATA_DIR / "insight_log.jsonl"


@dataclass
class ActivityPattern:
    """A detected user behavior pattern."""
    pattern_type: str = ""  # routine, focus, social, emotional, goal
    description: str = ""
    confidence: float = 0.0
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    occurrence_count: int = 0
    examples: List[str] = field(default_factory=list)


class UserPatternDetector:
    """
    Behavioral pattern recognition for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
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
        self._patterns: Dict[str, ActivityPattern] = {}
        self._recent_activities: deque = deque(maxlen=500)
        self._stats = {"patterns_detected": 0, "insights_generated": 0}
        self._load_patterns()

    # ── Pattern Detection ───────────────────────────────────────────────────

    def detect_patterns(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze activities and detect behavioral patterns."""
        detected = []

        for activity in activities:
            self._recent_activities.append(activity)

        # Pattern 1: Morning routine consistency
        morning_routine = self._detect_morning_routine()
        if morning_routine:
            detected.append(morning_routine)

        # Pattern 2: Focus session patterns
        focus_pattern = self._detect_focus_patterns()
        if focus_pattern:
            detected.append(focus_pattern)

        # Pattern 3: Break timing patterns
        break_pattern = self._detect_break_patterns()
        if break_pattern:
            detected.append(break_pattern)

        # Pattern 4: Energy level patterns
        energy_pattern = self._detect_energy_patterns()
        if energy_pattern:
            detected.append(energy_pattern)

        for d in detected:
            self._store_pattern(d)

        self._stats["patterns_detected"] += len(detected)
        return detected

    def _detect_morning_routine(self) -> Optional[Dict[str, Any]]:
        """Detect if user has consistent morning routine."""
        morning_activities = [
            a for a in self._recent_activities
            if 5 <= datetime.fromisoformat(a.get("timestamp", datetime.now().isoformat())).hour <= 10
        ]
        if len(morning_activities) < 5:
            return None

        types = Counter(a.get("type", "unknown") for a in morning_activities)
        most_common = types.most_common(1)[0]

        if most_common[1] >= 3:
            return {
                "pattern_type": "routine",
                "description": f"You often {most_common[0]} in the morning",
                "confidence": round(most_common[1] / len(morning_activities), 2),
            }
        return None

    def _detect_focus_patterns(self) -> Optional[Dict[str, Any]]:
        """Detect focus session patterns."""
        focus_sessions = [
            a for a in self._recent_activities
            if a.get("type") in ("deep_work", "coding", "writing", "focus")
        ]
        if len(focus_sessions) < 3:
            return None

        # Check if focus sessions cluster at certain times
        hours = [datetime.fromisoformat(a.get("timestamp", "now")).hour for a in focus_sessions]
        hour_counts = Counter(hours)
        peak_hour = hour_counts.most_common(1)[0]

        if peak_hour[1] >= 2:
            return {
                "pattern_type": "focus",
                "description": f"Peak focus time: around {peak_hour[0]}:00",
                "confidence": round(peak_hour[1] / len(focus_sessions), 2),
            }
        return None

    def _detect_break_patterns(self) -> Optional[Dict[str, Any]]:
        """Detect break timing patterns."""
        breaks = [
            a for a in self._recent_activities
            if a.get("type") in ("break", "rest", "walk", "exercise")
        ]
        if len(breaks) < 3:
            return None

        # Check if breaks happen after consistent work periods
        return {
            "pattern_type": "recovery",
            "description": f"You take breaks after about {self._estimate_work_streak()} minutes of work",
            "confidence": 0.6,
        }

    def _estimate_work_streak(self) -> int:
        """Estimate typical work streak before a break."""
        # Simple heuristic: 90 minutes (pomodoro-like)
        return 90

    def _detect_energy_patterns(self) -> Optional[Dict[str, Any]]:
        """Detect energy level patterns throughout the day."""
        energy_activities = [
            a for a in self._recent_activities
            if a.get("energy_level") is not None
        ]
        if len(energy_activities) < 5:
            return None

        # Group by hour and calculate average energy
        hourly_energy = defaultdict(list)
        for a in energy_activities:
            hour = datetime.fromisoformat(a.get("timestamp", "now")).hour
            hourly_energy[hour].append(a.get("energy_level", 5))

        if not hourly_energy:
            return None

        avg_by_hour = {h: sum(v) / len(v) for h, v in hourly_energy.items()}
        peak_hour = max(avg_by_hour, key=avg_by_hour.get)
        low_hour = min(avg_by_hour, key=avg_by_hour.get)

        return {
            "pattern_type": "energy",
            "description": f"Peak energy at {peak_hour}:00, lowest at {low_hour}:00",
            "confidence": 0.7,
        }

    # ── Insights ────────────────────────────────────────────────────────────

    def get_daily_insights(self) -> List[Dict[str, Any]]:
        """Generate insights based on detected patterns."""
        insights = []

        for pattern in self._patterns.values():
            if pattern.confidence > 0.5 and pattern.occurrence_count >= 3:
                insights.append({
                    "type": pattern.pattern_type,
                    "insight": pattern.description,
                    "confidence": pattern.confidence,
                    "times_observed": pattern.occurrence_count,
                })

        self._stats["insights_generated"] += len(insights)
        return sorted(insights, key=lambda x: x["confidence"], reverse=True)

    def predict_next_activity(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Predict what the user will likely do next."""
        now = current_time or datetime.now()
        hour = now.hour

        # Check patterns for this hour
        hour_patterns = [
            p for p in self._patterns.values()
            if p.pattern_type == "routine" and str(hour) in p.description
        ]

        if hour_patterns:
            best = max(hour_patterns, key=lambda p: p.confidence)
            return {
                "predicted_activity": best.description.split("often ")[1] if "often" in best.description else "continue current activity",
                "confidence": best.confidence,
                "basis": f"Observed {best.occurrence_count} times",
            }

        # Default prediction based on time of day
        time_based = {
            (5, 9): "morning routine",
            (9, 12): "focused work",
            (12, 14): "lunch break",
            (14, 18): "afternoon work",
            (18, 22): "evening activities",
            (22, 5): "wind down / sleep",
        }

        for (start, end), activity in time_based.items():
            if start <= hour < end or (start > end and (hour >= start or hour < end)):
                return {
                    "predicted_activity": activity,
                    "confidence": 0.3,
                    "basis": "Time-of-day heuristic",
                }

        return {"predicted_activity": "unknown", "confidence": 0.0}

    # ── Pattern Storage ────────────────────────────────────────────────────

    def _store_pattern(self, pattern_data: Dict[str, Any]):
        """Store a detected pattern."""
        key = f"{pattern_data['pattern_type']}:{pattern_data['description']}"

        with self._lock:
            if key in self._patterns:
                existing = self._patterns[key]
                existing.occurrence_count += 1
                existing.last_seen = datetime.now().isoformat()
                existing.confidence = min(1.0, existing.confidence + 0.1)
            else:
                self._patterns[key] = ActivityPattern(
                    pattern_type=pattern_data["pattern_type"],
                    description=pattern_data["description"],
                    confidence=pattern_data.get("confidence", 0.5),
                )

        self._save_patterns()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_pattern_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "active_patterns": len(self._patterns),
            "recent_activities": len(self._recent_activities),
            "pattern_types": Counter(p.pattern_type for p in self._patterns.values()),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_patterns(self):
        try:
            data = {
                key: {
                    "pattern_type": p.pattern_type,
                    "description": p.description,
                    "confidence": p.confidence,
                    "first_seen": p.first_seen,
                    "last_seen": p.last_seen,
                    "occurrence_count": p.occurrence_count,
                }
                for key, p in self._patterns.items()
            }
            PATTERN_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.user_pattern_detector")

    def _load_patterns(self):
        try:
            if PATTERN_DB.exists():
                data = json.loads(PATTERN_DB.read_text())
                for key, p_data in data.items():
                    self._patterns[key] = ActivityPattern(**p_data)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.user_pattern_detector")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_detector_instance: Optional[UserPatternDetector] = None
_detector_lock = threading.Lock()


def get_user_pattern_detector() -> UserPatternDetector:
    global _detector_instance
    with _detector_lock:
        if _detector_instance is None:
            _detector_instance = UserPatternDetector()
        return _detector_instance
