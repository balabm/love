"""
LOVE Evening Wind-Down Coach — Sleep Intelligence (Modern AI Pattern)

Most evening routines are an afterthought. This coach:

1. EVENING TRACKING
   - Record evening activities and their impact on sleep quality
   - Track screen time, caffeine, and stimulation in the evening
   - Log wind-down routine completion and consistency

2. SLEEP PREDICTION
   - Predict sleep quality based on evening choices
   - Identify which activities hurt vs help sleep
   - Detect patterns of overstimulation before bed

3. PERSONALIZED WIND-DOWN
   - Generate custom wind-down routines based on current energy
   - Suggest optimal bedtime based on wake time and sleep needs
   - Adapt routine length based on how wired the user is

4. PROACTIVE GUIDANCE
   - Alert when it's time to start winding down
   - Suggest specific activities to lower arousal
   - Recommend when to put devices away

Architecture:
- record_evening_activity(activity, duration, stimulation_level): Log activity
- get_sleep_prediction(): Predict tonight's sleep quality
- get_wind_down_routine(current_energy, time_available): Get custom routine
- get_optimal_bedtime(wake_time, sleep_needed): Get bedtime recommendation
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "evening_wind_down_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EVENING_LOG = DATA_DIR / "evenings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EveningActivity:
    """An evening activity."""
    activity: str = ""
    category: str = ""  # screen, movement, food, hygiene, mindfulness, social, work
    duration_minutes: float = 0.0
    stimulation_level: float = 5.0  # 1-10 (relaxing to stimulating)
    sleep_impact: float = 0.0  # -5 to +5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class EveningRecord:
    """A complete evening record."""
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    activities: List[str] = field(default_factory=list)
    total_screen_time: float = 0.0
    caffeine_after_4pm: bool = False
    heavy_meal_after_7pm: bool = False
    work_after_8pm: bool = False
    wind_down_start: str = ""
    bed_time: str = ""
    sleep_quality: float = 0.5  # reported next morning
    time_to_fall_asleep: float = 0.0  # minutes
    notes: str = ""


class EveningWindDownCoach:
    """
    Intelligent evening wind-down coach for better sleep.
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
        self._activities: deque = deque(maxlen=300)
        self._evenings: deque = deque(maxlen=100)
        self._stats = {
            "total_evenings": 0,
            "avg_sleep_quality": 0.5,
            "avg_time_to_sleep": 0.0,
            "best_wind_down_time": "21:00",
            "avg_screen_time": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_evening_activity(self, activity: str = "", category: str = "", duration: float = 0, stimulation_level: float = 5.0, sleep_impact: float = 0, notes: str = "") -> EveningActivity:
        """Record an evening activity."""
        act = EveningActivity(
            activity=activity or "untitled",
            category=category or "general",
            duration_minutes=duration,
            stimulation_level=stimulation_level,
            sleep_impact=sleep_impact,
            notes=notes,
        )

        with self._lock:
            self._activities.append(act)
            self._update_activity_stats()

        self._save_stats()
        self._log_activity(act)

        return act

    def record_evening(self, activities: Optional[List[str]] = None, total_screen_time: float = 0, caffeine_after_4pm: bool = False, heavy_meal_after_7pm: bool = False, work_after_8pm: bool = False, wind_down_start: str = "", bed_time: str = "", sleep_quality: float = 0.5, time_to_fall_asleep: float = 0, notes: str = "") -> EveningRecord:
        """Record a complete evening."""
        evening = EveningRecord(
            activities=activities or [],
            total_screen_time=total_screen_time,
            caffeine_after_4pm=caffeine_after_4pm,
            heavy_meal_after_7pm=heavy_meal_after_7pm,
            work_after_8pm=work_after_8pm,
            wind_down_start=wind_down_start,
            bed_time=bed_time,
            sleep_quality=sleep_quality,
            time_to_fall_asleep=time_to_fall_asleep,
            notes=notes,
        )

        with self._lock:
            self._evenings.append(evening)
            self._stats["total_evenings"] += 1
            self._update_evening_stats()

        self._save_stats()
        self._log_evening(evening)

        return evening

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_sleep_prediction(self) -> Dict[str, Any]:
        """Predict tonight's sleep quality based on current evening."""
        # Get today's activities
        today = datetime.now().date().isoformat()
        today_acts = [a for a in self._activities if a.timestamp[:10] == today]
        
        if not today_acts and not self._evenings:
            return {"status": "insufficient_data", "prediction": "neutral"}

        # Calculate stimulation score
        total_stimulation = sum(a.stimulation_level * a.duration_minutes for a in today_acts) / max(1, sum(a.duration_minutes for a in today_acts))
        
        # Screen time penalty
        screen_time = sum(a.duration_minutes for a in today_acts if a.category == "screen")
        screen_penalty = min(30, screen_time / 30)  # 2 hours = -30 points

        # Late activities penalty
        late_acts = [a for a in today_acts if a.timestamp[11:13] >= "21" and a.stimulation_level > 6]
        late_penalty = len(late_acts) * 10

        # Base prediction
        base_score = 70
        stimulation_penalty = (total_stimulation - 3) * 5  # Above 3 = penalty
        
        predicted_score = base_score - stimulation_penalty - screen_penalty - late_penalty
        
        # Add patterns from history
        if self._evenings:
            avg_quality = sum(e.sleep_quality for e in self._evenings) / len(self._evenings)
            predicted_score = (predicted_score + avg_quality * 100) / 2

        predicted_score = max(0, min(100, round(predicted_score)))

        if predicted_score >= 80:
            prediction = "excellent"
            advice = "Your evening looks sleep-friendly. Keep it up."
        elif predicted_score >= 60:
            prediction = "good"
            advice = "Decent evening, but you could optimize a bit more."
        elif predicted_score >= 40:
            prediction = "fair"
            advice = "Consider reducing stimulation in the next hour."
        else:
            prediction = "poor"
            advice = "Your evening is too stimulating. Start winding down now."

        return {
            "predicted_sleep_quality": predicted_score,
            "prediction": prediction,
            "advice": advice,
            "factors": {
                "stimulation_level": round(total_stimulation, 1),
                "screen_time_minutes": round(screen_time, 0),
                "late_stimulating_activities": len(late_acts),
            },
        }

    def get_wind_down_routine(self, current_energy: str = "medium", time_available: float = 30) -> List[Dict[str, Any]]:
        """Get custom wind-down routine."""
        energy_map = {"low": 3, "medium": 5, "high": 8}
        energy = energy_map.get(current_energy, 5)

        # Activity pool
        activities = [
            {"name": "Put away all screens", "duration": 2, "stimulation": 1, "category": "hygiene", "priority": "critical"},
            {"name": "Dim the lights", "duration": 2, "stimulation": 1, "category": "environment", "priority": "high"},
            {"name": "Gentle stretching", "duration": 10, "stimulation": 3, "category": "movement", "priority": "medium"},
            {"name": "Breathing exercise (4-7-8)", "duration": 5, "stimulation": 1, "category": "mindfulness", "priority": "high"},
            {"name": "Read fiction (paper book)", "duration": 15, "stimulation": 2, "category": "mindfulness", "priority": "medium"},
            {"name": "Warm shower/bath", "duration": 15, "stimulation": 2, "category": "hygiene", "priority": "medium"},
            {"name": "Journaling (tomorrow's plan)", "duration": 5, "stimulation": 3, "category": "mindfulness", "priority": "medium"},
            {"name": "Gratitude reflection", "duration": 3, "stimulation": 1, "category": "mindfulness", "priority": "low"},
            {"name": "Herbal tea (chamomile)", "duration": 5, "stimulation": 1, "category": "food", "priority": "low"},
            {"name": "Tidy tomorrow's clothes", "duration": 3, "stimulation": 2, "category": "preparation", "priority": "low"},
            {"name": "Progressive muscle relaxation", "duration": 10, "stimulation": 1, "category": "mindfulness", "priority": "medium"},
            {"name": "Light walk", "duration": 15, "stimulation": 3, "category": "movement", "priority": "low"},
        ]

        # For high energy, include more calming activities
        if energy > 6:
            activities.append({"name": "Extended breathing meditation", "duration": 15, "stimulation": 1, "category": "mindfulness", "priority": "high"})
            activities.append({"name": "Cold shower (brief)", "duration": 3, "stimulation": 4, "category": "hygiene", "priority": "medium"})

        # Sort by priority and select within time budget
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        activities.sort(key=lambda x: priority_order[x["priority"]])

        selected = []
        remaining = time_available

        for act in activities:
            if remaining >= act["duration"]:
                selected.append(act)
                remaining -= act["duration"]

        return selected

    def get_optimal_bedtime(self, wake_time: str = "07:00", sleep_needed: float = 8.0) -> Dict[str, Any]:
        """Get bedtime recommendation."""
        try:
            wake = datetime.strptime(wake_time, "%H:%M")
            bedtime = wake - timedelta(hours=sleep_needed)
            
            # Adjust based on historical data
            if self._evenings:
                good_sleep = [e for e in self._evenings if e.sleep_quality > 0.7]
                if good_sleep:
                    avg_bedtime = sum(int(e.bed_time[:2]) * 60 + int(e.bed_time[3:5]) for e in good_sleep if e.bed_time) / max(1, len(good_sleep))
                    if avg_bedtime > 0:
                        # Compare with calculated bedtime
                        calculated_minutes = bedtime.hour * 60 + bedtime.minute
                        if abs(avg_bedtime - calculated_minutes) > 30:
                            # User's optimal is different from theoretical
                            optimal_hour = int(avg_bedtime // 60) % 24
                            optimal_minute = int(avg_bedtime % 60)
                            return {
                                "calculated_bedtime": bedtime.strftime("%H:%M"),
                                "historical_optimal": f"{optimal_hour:02d}:{optimal_minute:02d}",
                                "recommendation": f"Based on your data, aim for bed by {optimal_hour:02d}:{optimal_minute:02d}.",
                                "reason": "Your historical sleep quality is best with this bedtime.",
                            }

            return {
                "calculated_bedtime": bedtime.strftime("%H:%M"),
                "historical_optimal": None,
                "recommendation": f"Aim to be in bed by {bedtime.strftime('%H:%M')} for {sleep_needed} hours of sleep.",
                "reason": f"To wake at {wake_time}, you need to sleep by {bedtime.strftime('%H:%M')}.",
            }
        except Exception:
            return {
                "calculated_bedtime": "22:00",
                "recommendation": "Aim for bed by 22:00 for 8 hours of sleep.",
                "reason": "Default recommendation for 8 hours of sleep.",
            }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_activity_stats(self):
        """Update activity statistics."""
        today = datetime.now().date().isoformat()
        today_acts = [a for a in self._activities if a.timestamp[:10] == today]
        if today_acts:
            self._stats["avg_screen_time"] = round(sum(a.duration_minutes for a in today_acts if a.category == "screen") / 60, 1)

    def _update_evening_stats(self):
        """Update evening statistics."""
        if self._evenings:
            self._stats["avg_sleep_quality"] = round(sum(e.sleep_quality for e in self._evenings) / len(self._evenings), 2)
            self._stats["avg_time_to_sleep"] = round(sum(e.time_to_fall_asleep for e in self._evenings) / len(self._evenings), 1)
            
            # Find best wind-down time
            good_sleep = [e for e in self._evenings if e.sleep_quality > 0.7 and e.wind_down_start]
            if good_sleep:
                avg_start = sum(int(e.wind_down_start[:2]) * 60 + int(e.wind_down_start[3:5]) for e in good_sleep) / len(good_sleep)
                hour = int(avg_start // 60) % 24
                minute = int(avg_start % 60)
                self._stats["best_wind_down_time"] = f"{hour:02d}:{minute:02d}"

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.evening_wind_down_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.evening_wind_down_coach")

    def _log_activity(self, activity: EveningActivity):
        try:
            with open(EVENING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": activity.timestamp,
                    "activity": activity.activity,
                    "category": activity.category,
                    "duration": activity.duration_minutes,
                    "stimulation": activity.stimulation_level,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.evening_wind_down_coach")

    def _log_evening(self, evening: EveningRecord):
        try:
            with open(EVENING_LOG, "a") as f:
                f.write(json.dumps({
                    "date": evening.date,
                    "screen_time": evening.total_screen_time,
                    "caffeine": evening.caffeine_after_4pm,
                    "heavy_meal": evening.heavy_meal_after_7pm,
                    "work_late": evening.work_after_8pm,
                    "bed_time": evening.bed_time,
                    "sleep_quality": evening.sleep_quality,
                    "time_to_sleep": evening.time_to_fall_asleep,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.evening_wind_down_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ewdc_instance: Optional[EveningWindDownCoach] = None
_ewdc_lock = threading.Lock()


def get_evening_wind_down_coach() -> EveningWindDownCoach:
    global _ewdc_instance
    with _ewdc_lock:
        if _ewdc_instance is None:
            _ewdc_instance = EveningWindDownCoach()
        return _ewdc_instance
