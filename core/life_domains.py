"""
life_domains.py — Wave 22 Life Domains Engine

Tracks and nudges across four core physical life domains:
  - Hydration  (daily water intake, glass count)
  - Sleep      (bedtime, wake time, quality, duration)
  - Nutrition  (meals, macros, meal quality score)
  - Skincare   (morning/evening routines, products used, skin notes)

Each domain has:
  - log()       → record an event
  - get_today() → today's summary
  - get_streak()→ consecutive-day streak
  - needs_nudge()→ True if user is overdue for action
  - get_insights(days)→ multi-day analysis
"""

import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.settings import get_settings


# ──────────────────────────────────────────────────────────────────────────────
# Storage helpers
# ──────────────────────────────────────────────────────────────────────────────

def _data_dir() -> Path:
    d = get_settings().data_dir / "life_domains"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _domain_file(domain: str, day: Optional[date] = None) -> Path:
    if day is None:
        day = date.today()
    return _data_dir() / domain / f"{day.isoformat()}.json"


def _load_day(domain: str, day: Optional[date] = None) -> Dict:
    f = _domain_file(domain, day)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_day(domain: str, data: Dict, day: Optional[date] = None):
    f = _domain_file(domain, day)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_range(domain: str, days: int = 7) -> List[Dict]:
    results = []
    today = date.today()
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        rec = _load_day(domain, d)
        rec["_date"] = d.isoformat()
        results.append(rec)
    return results


# ──────────────────────────────────────────────────────────────────────────────
# HYDRATION
# ──────────────────────────────────────────────────────────────────────────────

HYDRATION_GOAL_ML = 2500  # ml per day
GLASS_ML = 250            # 1 glass = 250 ml


class HydrationTracker:
    domain = "hydration"

    def log_glass(self, count: int = 1, ml: Optional[int] = None) -> Dict:
        """Log one or more glasses / custom ml."""
        rec = _load_day(self.domain)
        if "entries" not in rec:
            rec["entries"] = []
        entry_ml = ml if ml is not None else count * GLASS_ML
        rec["entries"].append({
            "ts": datetime.now().isoformat(),
            "ml": entry_ml,
            "glasses": count
        })
        rec["total_ml"] = sum(e["ml"] for e in rec["entries"])
        rec["total_glasses"] = rec["total_ml"] // GLASS_ML
        rec["goal_ml"] = HYDRATION_GOAL_ML
        rec["pct"] = round(min(100, rec["total_ml"] / HYDRATION_GOAL_ML * 100), 1)
        _save_day(self.domain, rec)
        return rec

    def get_today(self) -> Dict:
        rec = _load_day(self.domain)
        return {
            "total_ml": rec.get("total_ml", 0),
            "total_glasses": rec.get("total_glasses", 0),
            "goal_ml": HYDRATION_GOAL_ML,
            "pct": rec.get("pct", 0),
            "entries": rec.get("entries", []),
            "needs_nudge": self.needs_nudge()
        }

    def needs_nudge(self) -> bool:
        rec = _load_day(self.domain)
        total = rec.get("total_ml", 0)
        # Nudge if below 40% by noon, below 70% by 3pm, or below 100% by 8pm
        hour = datetime.now().hour
        if hour >= 20 and total < HYDRATION_GOAL_ML:
            return True
        if hour >= 15 and total < HYDRATION_GOAL_ML * 0.7:
            return True
        if hour >= 12 and total < HYDRATION_GOAL_ML * 0.4:
            return True
        return False

    def get_streak(self) -> int:
        streak = 0
        today = date.today()
        for i in range(1, 31):
            d = today - timedelta(days=i)
            rec = _load_day(self.domain, d)
            if rec.get("total_ml", 0) >= HYDRATION_GOAL_ML * 0.8:
                streak += 1
            else:
                break
        return streak

    def get_insights(self, days: int = 7) -> Dict:
        history = _load_range(self.domain, days)
        totals = [r.get("total_ml", 0) for r in history]
        met = [t >= HYDRATION_GOAL_ML * 0.8 for t in totals]
        return {
            "days": days,
            "avg_ml": round(sum(totals) / len(totals)) if totals else 0,
            "goal_ml": HYDRATION_GOAL_ML,
            "days_goal_met": sum(met),
            "streak": self.get_streak(),
            "history": [{"date": r["_date"], "total_ml": r.get("total_ml", 0)} for r in history]
        }


# ──────────────────────────────────────────────────────────────────────────────
# SLEEP
# ──────────────────────────────────────────────────────────────────────────────

SLEEP_GOAL_HOURS = 7.5


class SleepTracker:
    domain = "sleep"

    def log_sleep(self, bedtime: str, wake_time: str, quality: int = 5, notes: str = "") -> Dict:
        """
        Log a sleep session.
        bedtime / wake_time: "HH:MM" strings (24h)
        quality: 1–10
        """
        rec = _load_day(self.domain)
        # Calculate duration
        try:
            today = date.today()
            bt = datetime.strptime(f"{today.isoformat()} {bedtime}", "%Y-%m-%d %H:%M")
            wt = datetime.strptime(f"{today.isoformat()} {wake_time}", "%Y-%m-%d %H:%M")
            if wt <= bt:
                wt += timedelta(days=1)
            hours = round((wt - bt).total_seconds() / 3600, 2)
        except Exception:
            hours = 0.0

        rec["bedtime"] = bedtime
        rec["wake_time"] = wake_time
        rec["hours"] = hours
        rec["quality"] = quality
        rec["notes"] = notes
        rec["goal_hours"] = SLEEP_GOAL_HOURS
        rec["score"] = round(min(100, (hours / SLEEP_GOAL_HOURS) * 60 + quality * 4), 1)
        rec["logged_at"] = datetime.now().isoformat()
        _save_day(self.domain, rec)
        return rec

    def get_today(self) -> Dict:
        rec = _load_day(self.domain)
        return {
            "hours": rec.get("hours", 0),
            "quality": rec.get("quality", 0),
            "bedtime": rec.get("bedtime"),
            "wake_time": rec.get("wake_time"),
            "goal_hours": SLEEP_GOAL_HOURS,
            "score": rec.get("score", 0),
            "logged": bool(rec.get("bedtime")),
            "needs_nudge": self.needs_nudge()
        }

    def needs_nudge(self) -> bool:
        rec = _load_day(self.domain)
        hour = datetime.now().hour
        # Nudge if not logged by 10am (morning window to log last night's sleep)
        if hour >= 10 and not rec.get("bedtime"):
            return True
        # Bedtime reminder after 10pm
        if hour >= 22 and rec.get("hours", 0) < SLEEP_GOAL_HOURS:
            return True
        return False

    def get_streak(self) -> int:
        streak = 0
        today = date.today()
        for i in range(1, 31):
            d = today - timedelta(days=i)
            rec = _load_day(self.domain, d)
            if rec.get("hours", 0) >= SLEEP_GOAL_HOURS * 0.85:
                streak += 1
            else:
                break
        return streak

    def get_insights(self, days: int = 7) -> Dict:
        history = _load_range(self.domain, days)
        hours_list = [r.get("hours", 0) for r in history]
        quality_list = [r.get("quality", 0) for r in history if r.get("quality")]
        return {
            "days": days,
            "avg_hours": round(sum(hours_list) / max(1, len([h for h in hours_list if h > 0])), 2),
            "avg_quality": round(sum(quality_list) / max(1, len(quality_list)), 1),
            "goal_hours": SLEEP_GOAL_HOURS,
            "days_goal_met": sum(1 for h in hours_list if h >= SLEEP_GOAL_HOURS * 0.85),
            "streak": self.get_streak(),
            "history": [{"date": r["_date"], "hours": r.get("hours", 0), "quality": r.get("quality", 0)} for r in history]
        }


# ──────────────────────────────────────────────────────────────────────────────
# NUTRITION
# ──────────────────────────────────────────────────────────────────────────────

NUTRITION_MEAL_GOAL = 3  # meals per day target


class NutritionTracker:
    domain = "nutrition"

    def log_meal(self, meal_type: str, description: str, quality: int = 5,
                 calories: Optional[int] = None, protein_g: Optional[int] = None,
                 carbs_g: Optional[int] = None, fat_g: Optional[int] = None) -> Dict:
        """
        Log a meal.
        meal_type: breakfast|lunch|dinner|snack
        quality: 1–10 (subjective health score)
        """
        rec = _load_day(self.domain)
        if "meals" not in rec:
            rec["meals"] = []
        meal = {
            "ts": datetime.now().isoformat(),
            "type": meal_type,
            "description": description,
            "quality": quality,
        }
        if calories is not None:
            meal["calories"] = calories
        if protein_g is not None:
            meal["protein_g"] = protein_g
        if carbs_g is not None:
            meal["carbs_g"] = carbs_g
        if fat_g is not None:
            meal["fat_g"] = fat_g
        rec["meals"].append(meal)
        rec["meal_count"] = len(rec["meals"])
        rec["avg_quality"] = round(sum(m["quality"] for m in rec["meals"]) / len(rec["meals"]), 1)
        rec["total_calories"] = sum(m.get("calories", 0) for m in rec["meals"])
        _save_day(self.domain, rec)
        return rec

    def get_today(self) -> Dict:
        rec = _load_day(self.domain)
        meals = rec.get("meals", [])
        types_logged = {m["type"] for m in meals}
        return {
            "meals": meals,
            "meal_count": len(meals),
            "avg_quality": rec.get("avg_quality", 0),
            "total_calories": rec.get("total_calories", 0),
            "types_logged": list(types_logged),
            "missing_meals": [t for t in ["breakfast", "lunch", "dinner"] if t not in types_logged],
            "needs_nudge": self.needs_nudge()
        }

    def needs_nudge(self) -> bool:
        rec = _load_day(self.domain)
        meals = rec.get("meals", [])
        types = {m["type"] for m in meals}
        hour = datetime.now().hour
        if hour >= 9 and "breakfast" not in types:
            return True
        if hour >= 14 and "lunch" not in types:
            return True
        if hour >= 20 and "dinner" not in types:
            return True
        return False

    def get_streak(self) -> int:
        streak = 0
        today = date.today()
        for i in range(1, 31):
            d = today - timedelta(days=i)
            rec = _load_day(self.domain, d)
            if rec.get("meal_count", 0) >= NUTRITION_MEAL_GOAL:
                streak += 1
            else:
                break
        return streak

    def get_insights(self, days: int = 7) -> Dict:
        history = _load_range(self.domain, days)
        counts = [r.get("meal_count", 0) for r in history]
        qualities = [r.get("avg_quality", 0) for r in history if r.get("avg_quality")]
        return {
            "days": days,
            "avg_meals_per_day": round(sum(counts) / max(1, len(counts)), 1),
            "avg_quality": round(sum(qualities) / max(1, len(qualities)), 1) if qualities else 0,
            "days_goal_met": sum(1 for c in counts if c >= NUTRITION_MEAL_GOAL),
            "streak": self.get_streak(),
            "history": [{"date": r["_date"], "meals": r.get("meal_count", 0), "quality": r.get("avg_quality", 0)} for r in history]
        }


# ──────────────────────────────────────────────────────────────────────────────
# SKINCARE
# ──────────────────────────────────────────────────────────────────────────────

class SkincareTracker:
    domain = "skincare"

    ROUTINE_STEPS = {
        "morning": ["cleanser", "toner", "serum", "moisturizer", "spf"],
        "evening": ["cleanser", "toner", "serum", "moisturizer", "treatment"]
    }

    def log_routine(self, routine_type: str, steps_done: List[str],
                    products: Optional[Dict[str, str]] = None,
                    skin_notes: str = "", feeling: int = 5) -> Dict:
        """
        Log a skincare routine.
        routine_type: morning|evening
        steps_done: list of step names (e.g. ["cleanser","moisturizer","spf"])
        products: dict step→product name
        feeling: 1–10 skin feeling score
        """
        rec = _load_day(self.domain)
        key = f"routine_{routine_type}"
        target_steps = self.ROUTINE_STEPS.get(routine_type, [])
        completion = round(len([s for s in steps_done if s in target_steps]) / max(1, len(target_steps)) * 100, 1)
        rec[key] = {
            "ts": datetime.now().isoformat(),
            "type": routine_type,
            "steps_done": steps_done,
            "products": products or {},
            "skin_notes": skin_notes,
            "feeling": feeling,
            "completion_pct": completion
        }
        # Overall daily score
        routines = [v for k, v in rec.items() if k.startswith("routine_")]
        rec["daily_score"] = round(sum(r["completion_pct"] for r in routines) / max(1, len(routines)), 1)
        rec["routines_logged"] = len(routines)
        _save_day(self.domain, rec)
        return rec[key]

    def log_concern(self, concern: str, severity: int = 3) -> Dict:
        """Log a skin concern (breakout, dryness, etc.)"""
        rec = _load_day(self.domain)
        if "concerns" not in rec:
            rec["concerns"] = []
        rec["concerns"].append({
            "ts": datetime.now().isoformat(),
            "concern": concern,
            "severity": severity
        })
        _save_day(self.domain, rec)
        return rec

    def get_today(self) -> Dict:
        rec = _load_day(self.domain)
        morning = rec.get("routine_morning")
        evening = rec.get("routine_evening")
        hour = datetime.now().hour
        return {
            "morning_done": morning is not None,
            "evening_done": evening is not None,
            "morning": morning,
            "evening": evening,
            "concerns": rec.get("concerns", []),
            "daily_score": rec.get("daily_score", 0),
            "needs_nudge": self.needs_nudge()
        }

    def needs_nudge(self) -> bool:
        rec = _load_day(self.domain)
        hour = datetime.now().hour
        if hour >= 9 and not rec.get("routine_morning"):
            return True
        if hour >= 21 and not rec.get("routine_evening"):
            return True
        return False

    def get_streak(self) -> int:
        streak = 0
        today = date.today()
        for i in range(1, 31):
            d = today - timedelta(days=i)
            rec = _load_day(self.domain, d)
            if rec.get("routines_logged", 0) >= 1:
                streak += 1
            else:
                break
        return streak

    def get_insights(self, days: int = 7) -> Dict:
        history = _load_range(self.domain, days)
        scores = [r.get("daily_score", 0) for r in history]
        morning_done = sum(1 for r in history if r.get("routine_morning"))
        evening_done = sum(1 for r in history if r.get("routine_evening"))
        return {
            "days": days,
            "avg_score": round(sum(scores) / max(1, len(scores)), 1),
            "morning_consistency": round(morning_done / days * 100, 1),
            "evening_consistency": round(evening_done / days * 100, 1),
            "streak": self.get_streak(),
            "history": [{"date": r["_date"], "score": r.get("daily_score", 0),
                         "morning": bool(r.get("routine_morning")), "evening": bool(r.get("routine_evening"))} for r in history]
        }


# ──────────────────────────────────────────────────────────────────────────────
# UNIFIED LIFE DOMAINS ENGINE
# ──────────────────────────────────────────────────────────────────────────────

class LifeDomainsEngine:
    """Unified access point for all life domain trackers."""

    def __init__(self):
        self.hydration = HydrationTracker()
        self.sleep = SleepTracker()
        self.nutrition = NutritionTracker()
        self.skincare = SkincareTracker()

    def get_dashboard(self) -> Dict:
        """Full today snapshot across all domains."""
        hydration = self.hydration.get_today()
        sleep_ = self.sleep.get_today()
        nutrition = self.nutrition.get_today()
        skincare = self.skincare.get_today()

        # Overall life score (0–100)
        scores = []
        if hydration["goal_ml"] > 0:
            scores.append(hydration["pct"])
        scores.append(min(100, (sleep_["hours"] / 7.5) * 100) if sleep_["hours"] else 0)
        scores.append(min(100, nutrition["meal_count"] / 3 * 100))
        scores.append(skincare["daily_score"])
        life_score = round(sum(scores) / len(scores), 1) if scores else 0

        nudges = []
        if hydration["needs_nudge"]:
            remaining = hydration["goal_ml"] - hydration["total_ml"]
            nudges.append(f"Drink {remaining}ml more water today ({hydration['pct']:.0f}% done)")
        if sleep_["needs_nudge"]:
            if not sleep_["logged"]:
                nudges.append("Log last night's sleep to track your rest patterns")
            else:
                nudges.append(f"Consider sleeping soon — aim for {7.5}h")
        if nutrition["needs_nudge"]:
            missing = nutrition["missing_meals"]
            if missing:
                nudges.append(f"Haven't logged {', '.join(missing)} yet today")
        if skincare["needs_nudge"]:
            if not skincare["morning_done"]:
                nudges.append("Morning skincare routine not done yet")
            elif not skincare["evening_done"]:
                nudges.append("Evening skincare routine not done yet")

        return {
            "life_score": life_score,
            "nudges": nudges,
            "hydration": hydration,
            "sleep": sleep_,
            "nutrition": nutrition,
            "skincare": skincare,
            "timestamp": datetime.now().isoformat()
        }

    def get_weekly_insights(self) -> Dict:
        return {
            "hydration": self.hydration.get_insights(7),
            "sleep": self.sleep.get_insights(7),
            "nutrition": self.nutrition.get_insights(7),
            "skincare": self.skincare.get_insights(7),
        }

    def get_active_nudges(self, emotional_state: dict = None) -> List[str]:
        nudges = self.get_dashboard()["nudges"]
        if emotional_state:
            stress = emotional_state.get("current_stress", 0) or emotional_state.get("stress", 0)
            if stress and float(stress) > 70:
                # Drop exercise/workout nudges — wrong time to push physical exertion
                nudges = [n for n in nudges if not any(
                    kw in n.lower() for kw in ("exercise", "workout", "gym", "run", "training")
                )]
                # Inject a stress-aware recovery nudge if not already present
                recovery = "You're carrying a lot right now — even 5 minutes away from the screen helps."
                if recovery not in nudges:
                    nudges.insert(0, recovery)
        return nudges

    def get_streaks(self) -> Dict:
        return {
            "hydration": self.hydration.get_streak(),
            "sleep": self.sleep.get_streak(),
            "nutrition": self.nutrition.get_streak(),
            "skincare": self.skincare.get_streak(),
        }


# Singleton
_engine: Optional[LifeDomainsEngine] = None


def get_life_domains_engine() -> LifeDomainsEngine:
    global _engine
    if _engine is None:
        _engine = LifeDomainsEngine()
    return _engine
