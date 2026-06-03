"""
LOVE Weather Suggester — Weather Intelligence (Modern AI Pattern)

Most weather apps tell you the forecast. This suggester:

1. WEATHER TRACKING
   - Record daily weather conditions and user mood/energy correlation
   - Track how different weather affects productivity and mood
   - Log outdoor activity vs weather patterns

2. MOOD CORRELATION
   - Identify weather patterns that boost or drain energy
   - Detect seasonal mood patterns (SAD, summer energy, etc.)
   - Correlate weather with sleep quality and focus

3. ACTIVITY SUGGESTIONS
   - Suggest indoor activities for bad weather days
   - Recommend outdoor activities for perfect weather windows
   - Propose weather-appropriate commute or exercise options

4. PROACTIVE PLANNING
   - Alert about upcoming weather changes that might affect plans
   - Suggest rescheduling outdoor activities based on forecast
   - Recommend clothing/layering for the day's conditions

Architecture:
- record_weather(temp, condition, mood_impact): Log weather and effect
- get_weather_insights(): Get weather-mood correlation
- get_activity_suggestion(weather_forecast): Suggest activities
- get_weather_mood_score(): Calculate weather's impact on mood
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

DATA_DIR = Path(__file__).parent.parent / "data" / "weather_suggester"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WEATHER_LOG = DATA_DIR / "weather.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WeatherEntry:
    """A weather and mood entry."""
    temperature: float = 20.0  # celsius
    condition: str = ""  # sunny, cloudy, rainy, snowy, stormy, foggy
    humidity: float = 50.0  # %
    uv_index: float = 3.0
    mood_before: float = 5.0  # 1-10
    mood_after: float = 5.0
    energy_level: float = 5.0  # 1-10
    productivity: float = 5.0  # 1-10
    outdoor_activity: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class WeatherSuggester:
    """
    Personal weather intelligence with mood and activity correlation.
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
        self._entries: deque = deque(maxlen=500)
        self._stats = {
            "total_entries": 0,
            "avg_mood": 5.0,
            "avg_energy": 5.0,
            "best_condition": "",
            "worst_condition": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_weather(self, temperature: float = 20.0, condition: str = "", humidity: float = 50.0, uv_index: float = 3.0, mood_before: float = 5.0, mood_after: float = 5.0, energy_level: float = 5.0, productivity: float = 5.0, outdoor_activity: bool = False, notes: str = "") -> WeatherEntry:
        """Record weather conditions and their effect."""
        entry = WeatherEntry(
            temperature=temperature,
            condition=condition or "unknown",
            humidity=humidity,
            uv_index=uv_index,
            mood_before=mood_before,
            mood_after=mood_after,
            energy_level=energy_level,
            productivity=productivity,
            outdoor_activity=outdoor_activity,
            notes=notes,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_stats(entry)

        self._save_stats()
        self._log_entry(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_weather_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get weather-mood correlation analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [e for e in self._entries if e.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Condition analysis
        by_condition = defaultdict(lambda: {"moods": [], "energies": [], "productivities": [], "count": 0})
        for e in recent:
            c = e.condition
            by_condition[c]["moods"].append(e.mood_after)
            by_condition[c]["energies"].append(e.energy_level)
            by_condition[c]["productivities"].append(e.productivity)
            by_condition[c]["count"] += 1

        condition_stats = {}
        for c, data in by_condition.items():
            condition_stats[c] = {
                "count": data["count"],
                "avg_mood": round(sum(data["moods"]) / len(data["moods"]), 1),
                "avg_energy": round(sum(data["energies"]) / len(data["energies"]), 1),
                "avg_productivity": round(sum(data["productivities"]) / len(data["productivities"]), 1),
            }

        # Temperature correlation
        temp_ranges = defaultdict(list)
        for e in recent:
            if e.temperature < 10:
                range_key = "cold"
            elif e.temperature < 20:
                range_key = "cool"
            elif e.temperature < 30:
                range_key = "warm"
            else:
                range_key = "hot"
            temp_ranges[range_key].append(e.mood_after)

        temp_moods = {k: round(sum(v)/len(v), 1) for k, v in temp_ranges.items()}

        # Best and worst conditions
        if condition_stats:
            best = max(condition_stats.items(), key=lambda x: x[1]["avg_mood"])
            worst = min(condition_stats.items(), key=lambda x: x[1]["avg_mood"])
        else:
            best = ("", {})
            worst = ("", {})

        # Seasonal pattern
        by_month = defaultdict(list)
        for e in recent:
            month = e.timestamp[:7]  # YYYY-MM
            by_month[month].append(e.mood_after)

        monthly_trend = {k: round(sum(v)/len(v), 1) for k, v in sorted(by_month.items())}

        return {
            "days_analyzed": len(set(e.timestamp[:10] for e in recent)),
            "total_entries": len(recent),
            "condition_stats": condition_stats,
            "temperature_moods": temp_moods,
            "best_condition": best[0],
            "worst_condition": worst[0],
            "monthly_trend": monthly_trend,
        }

    def get_activity_suggestion(self, forecast_condition: str = "", forecast_temp: float = 20.0) -> Dict[str, Any]:
        """Suggest activities based on weather."""
        # Get user's historical preferences
        insights = self.get_weather_insights()
        condition = forecast_condition or "unknown"
        temp = forecast_temp

        # Default suggestions
        outdoor_suggestions = {
            "sunny": ["Go for a walk", "Have lunch outside", "Photography session", "Park workout"],
            "cloudy": ["Light jog", "Gardening", "Outdoor reading", "Bike ride"],
            "rainy": ["Indoor workout", "Cooking experiment", "Movie marathon", "Board games"],
            "snowy": ["Skiing/snowboarding", "Build a snowman", "Hot chocolate + book", "Indoor yoga"],
            "stormy": ["Stay home, deep work", "Indoor creative project", "Call a friend", "Meditation"],
            "foggy": ["Indoor gym", "Coffee shop work", "Museum visit", "Home organization"],
        }

        indoor_suggestions = {
            "sunny": ["Open curtains wide", "Work near window", "Short outdoor break every 2 hours"],
            "cloudy": ["Brighten workspace", "Vitamin D supplement", "Light therapy if needed"],
            "rainy": ["Cozy workspace setup", "Ambient rain sounds", "Warm tea while working"],
            "snowy": ["Warm workspace", "Layer up if going out", "Plan indoor activities"],
            "stormy": ["Backup power ready", "Comfort indoor setup", "Focus on indoor tasks"],
            "foggy": ["Extra lighting", "Careful driving if needed", "Museum or library visit"],
        }

        outdoor = outdoor_suggestions.get(condition, ["Check weather and decide"])
        indoor = indoor_suggestions.get(condition, ["Adjust workspace for comfort"])

        # Mood prediction
        condition_moods = insights.get("condition_stats", {})
        if condition in condition_moods:
            predicted_mood = condition_moods[condition]["avg_mood"]
            mood_advice = f"This weather typically puts you at {predicted_mood}/10 mood." if predicted_mood < 6 else f"This weather typically boosts you to {predicted_mood}/10 mood!"
        else:
            predicted_mood = 5
            mood_advice = "No data for this condition yet. See how you feel."

        return {
            "condition": condition,
            "temperature": temp,
            "outdoor_activities": outdoor[:2],
            "indoor_adjustments": indoor[:2],
            "predicted_mood": predicted_mood,
            "mood_advice": mood_advice,
            "clothing_suggestion": self._get_clothing_suggestion(temp, condition),
        }

    def get_weather_mood_score(self) -> int:
        """Calculate weather's current impact on mood (0-100)."""
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
        
        if not recent:
            return 50

        avg_mood = sum(e.mood_after for e in recent) / len(recent)
        avg_energy = sum(e.energy_level for e in recent) / len(recent)
        avg_productivity = sum(e.productivity for e in recent) / len(recent)

        overall = round(avg_mood * 10 * 0.4 + avg_energy * 10 * 0.3 + avg_productivity * 10 * 0.3)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _get_clothing_suggestion(self, temp: float, condition: str) -> str:
        """Get clothing suggestion based on weather."""
        if temp < 5:
            return "Heavy coat, gloves, scarf, warm layers."
        elif temp < 15:
            return "Jacket or sweater, long pants."
        elif temp < 25:
            return "Light layers, comfortable for range of temperatures."
        else:
            return "Light clothing, breathable fabrics, sun protection."

    def _update_stats(self, entry: WeatherEntry):
        """Update running statistics."""
        n = self._stats["total_entries"]
        self._stats["avg_mood"] = round((self._stats["avg_mood"] * (n - 1) + entry.mood_after) / n, 1)
        self._stats["avg_energy"] = round((self._stats["avg_energy"] * (n - 1) + entry.energy_level) / n, 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.weather_suggester")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.weather_suggester")

    def _log_entry(self, entry: WeatherEntry):
        try:
            with open(WEATHER_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "temp": entry.temperature,
                    "condition": entry.condition,
                    "mood_after": entry.mood_after,
                    "energy": entry.energy_level,
                    "productivity": entry.productivity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.weather_suggester")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ws_instance: Optional[WeatherSuggester] = None
_ws_lock = threading.Lock()


def get_weather_suggester() -> WeatherSuggester:
    global _ws_instance
    with _ws_lock:
        if _ws_instance is None:
            _ws_instance = WeatherSuggester()
        return _ws_instance
