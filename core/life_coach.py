"""
life_coach.py — Wave 25: Proactive Life Coach

Time-aware nudge scheduler + adaptive goals engine.
LOVE doesn't just track — it coaches. It knows *when* to say *what*.

Key behaviors:
  - Time-windowed nudges (breakfast reminder at 8am, not 11pm)
  - Adaptive daily goals based on 7-day rolling average
  - Focus-mode awareness (suppress non-urgent nudges during deep work)
  - Streak protection (warn before a streak breaks)
  - Compound pattern alerts (sleep + hydration + nutrition triple deficit)
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Time Windows — when each nudge type is appropriate
# ──────────────────────────────────────────────────────────────────────────────

TIME_WINDOWS = {
    "morning_skincare":   {"start": 6,  "end": 10, "priority": "medium"},
    "breakfast":          {"start": 7,  "end": 10, "priority": "medium"},
    "morning_hydration":  {"start": 8,  "end": 11, "priority": "low"},
    "sleep_log":          {"start": 7,  "end": 11, "priority": "high"},
    "lunch":              {"start": 12, "end": 14, "priority": "medium"},
    "afternoon_hydration":{"start": 14, "end": 16, "priority": "low"},
    "dinner":             {"start": 18, "end": 21, "priority": "medium"},
    "evening_skincare":   {"start": 20, "end": 23, "priority": "medium"},
    "bedtime_reminder":   {"start": 22, "end": 24, "priority": "high"},
    "evening_hydration":  {"start": 18, "end": 21, "priority": "medium"},
}


def _in_window(window_name: str) -> bool:
    """Check if current time is within a named window."""
    w = TIME_WINDOWS.get(window_name)
    if not w:
        return False
    hour = datetime.now().hour
    return w["start"] <= hour < w["end"]


# ──────────────────────────────────────────────────────────────────────────────
# Adaptive Goals
# ──────────────────────────────────────────────────────────────────────────────

class AdaptiveGoals:
    """
    Generates daily goals adapted to user's recent performance.
    If they average 1500ml water, don't set 2500ml — set 1800ml.
    Gradually ramp up. Meet them where they are.
    """

    def generate(self) -> Dict[str, Any]:
        goals = {}
        try:
            from core.life_domains import get_life_domains_engine
            engine = get_life_domains_engine()

            # Hydration
            hydra = engine.hydration.get_insights(7)
            avg_ml = hydra.get("avg_ml", 0)
            hydra_goal = hydra.get("goal_ml", 2500)
            if avg_ml > 0:
                # Set goal as 20% above current average, capped at standard goal
                adaptive = min(hydra_goal, int(avg_ml * 1.2))
                adaptive = max(adaptive, 1000)  # floor
            else:
                adaptive = 1500  # starter goal
            goals["hydration"] = {
                "target_ml": adaptive,
                "standard_goal": hydra_goal,
                "recent_avg": avg_ml,
                "message": f"Aim for {adaptive}ml today" + (f" (your avg is {avg_ml}ml)" if avg_ml > 0 else ""),
            }

            # Sleep
            sleep = engine.sleep.get_insights(7)
            avg_hours = sleep.get("avg_hours", 0)
            sleep_goal = sleep.get("goal_hours", 7.5)
            if avg_hours > 0:
                adaptive_h = min(sleep_goal, round(avg_hours + 0.3, 1))
                adaptive_h = max(adaptive_h, 6.0)
            else:
                adaptive_h = 7.0
            goals["sleep"] = {
                "target_hours": adaptive_h,
                "standard_goal": sleep_goal,
                "recent_avg": avg_hours,
                "message": f"Target {adaptive_h}h tonight" + (f" (recent avg: {avg_hours}h)" if avg_hours > 0 else ""),
            }

            # Nutrition
            nutr = engine.nutrition.get_insights(7)
            avg_meals = nutr.get("avg_meals_per_day", 0)
            avg_quality = nutr.get("avg_quality", 0)
            meal_target = 3 if avg_meals >= 2.5 else max(2, int(avg_meals) + 1)
            quality_target = min(10, round(avg_quality + 1)) if avg_quality > 0 else 5
            goals["nutrition"] = {
                "target_meals": meal_target,
                "target_quality": quality_target,
                "recent_avg_meals": avg_meals,
                "recent_avg_quality": avg_quality,
                "message": f"{meal_target} meals today, aim for {quality_target}/10 quality",
            }

            # Skincare
            skin = engine.skincare.get_insights(7)
            morning_pct = skin.get("morning_consistency", 0)
            evening_pct = skin.get("evening_consistency", 0)
            # If morning consistency is high, encourage maintaining; if low, just push for one routine
            if morning_pct > 70 and evening_pct > 70:
                skin_message = "Keep the routine — both AM and PM"
            elif morning_pct > 50:
                skin_message = "Do your evening routine tonight — the streak is there for morning"
            else:
                skin_message = "Just do one routine today — morning or evening. Start small."
            goals["skincare"] = {
                "morning_consistency": morning_pct,
                "evening_consistency": evening_pct,
                "message": skin_message,
            }

        except Exception as e:
            goals["error"] = str(e)

        return goals


# ──────────────────────────────────────────────────────────────────────────────
# Proactive Life Coach
# ──────────────────────────────────────────────────────────────────────────────

class LifeCoach:
    """
    Time-aware, focus-aware nudge generator.
    Call get_nudges() to get what LOVE should say right now.
    """

    def __init__(self):
        self.goals_engine = AdaptiveGoals()

    def get_nudges(self) -> List[Dict[str, Any]]:
        """
        Get contextually appropriate nudges for right now.
        Respects focus mode, time windows, and today's tracking state.
        """
        nudges = []
        hour = datetime.now().hour

        # Check if user is in focus mode
        in_focus = self._is_focus_mode()

        try:
            from core.life_domains import get_life_domains_engine
            engine = get_life_domains_engine()
            dash = engine.get_dashboard()
        except Exception:
            return [{"type": "error", "message": "Life domains unavailable", "priority": "low"}]

        hydration = dash.get("hydration", {})
        sleep = dash.get("sleep", {})
        nutrition = dash.get("nutrition", {})
        skincare = dash.get("skincare", {})

        # ── Sleep log (morning window) ──────────────────────────────────
        if _in_window("sleep_log") and not sleep.get("logged"):
            nudges.append({
                "type": "sleep_log",
                "domain": "sleep",
                "message": "How'd you sleep? Log it so I can track your rest patterns.",
                "priority": "high",
                "action": "/life/sleep/log",
                "suppress_in_focus": True,
            })

        # ── Breakfast ───────────────────────────────────────────────────
        if _in_window("breakfast"):
            types_logged = nutrition.get("types_logged", [])
            if "breakfast" not in types_logged:
                nudges.append({
                    "type": "meal_reminder",
                    "domain": "nutrition",
                    "message": "Breakfast? Even something small starts the engine.",
                    "priority": "medium",
                    "suppress_in_focus": True,
                })

        # ── Morning skincare ───────────────────────────────────────────
        if _in_window("morning_skincare") and not skincare.get("morning_done"):
            nudges.append({
                "type": "skincare_reminder",
                "domain": "skincare",
                "message": "Morning routine — cleanser, moisturizer, SPF at minimum.",
                "priority": "medium",
                "suppress_in_focus": True,
            })

        # ── Hydration checks (multiple windows) ────────────────────────
        hydra_pct = hydration.get("pct", 0)
        if _in_window("morning_hydration") and hydra_pct < 20:
            nudges.append({
                "type": "hydration",
                "domain": "hydration",
                "message": f"Only {hydra_pct:.0f}% of water goal. Grab a glass.",
                "priority": "low",
                "suppress_in_focus": False,  # Quick action, don't suppress
            })
        elif _in_window("afternoon_hydration") and hydra_pct < 50:
            nudges.append({
                "type": "hydration",
                "domain": "hydration",
                "message": f"Hydration at {hydra_pct:.0f}% — you need to pick up the pace.",
                "priority": "medium",
                "suppress_in_focus": True,
            })
        elif _in_window("evening_hydration") and hydra_pct < 80:
            nudges.append({
                "type": "hydration",
                "domain": "hydration",
                "message": f"Still at {hydra_pct:.0f}% hydration. {int(hydration.get('goal_ml', 2500) - hydration.get('total_ml', 0))}ml to go.",
                "priority": "high",
                "suppress_in_focus": True,
            })

        # ── Lunch ──────────────────────────────────────────────────────
        if _in_window("lunch"):
            types_logged = nutrition.get("types_logged", [])
            if "lunch" not in types_logged:
                nudges.append({
                    "type": "meal_reminder",
                    "domain": "nutrition",
                    "message": "Lunch time. Fuel up properly — your afternoon depends on it.",
                    "priority": "medium",
                    "suppress_in_focus": True,
                })

        # ── Dinner ─────────────────────────────────────────────────────
        if _in_window("dinner"):
            types_logged = nutrition.get("types_logged", [])
            if "dinner" not in types_logged:
                nudges.append({
                    "type": "meal_reminder",
                    "domain": "nutrition",
                    "message": "Dinner? Don't skip it — consistent meals matter.",
                    "priority": "medium",
                    "suppress_in_focus": True,
                })

        # ── Evening skincare ───────────────────────────────────────────
        if _in_window("evening_skincare") and not skincare.get("evening_done"):
            nudges.append({
                "type": "skincare_reminder",
                "domain": "skincare",
                "message": "Evening skincare before bed — your skin repairs overnight.",
                "priority": "medium",
                "suppress_in_focus": False,
            })

        # ── Bedtime ────────────────────────────────────────────────────
        if _in_window("bedtime_reminder"):
            goals = self.goals_engine.generate()
            sleep_target = goals.get("sleep", {}).get("target_hours", 7.5)
            nudges.append({
                "type": "bedtime",
                "domain": "sleep",
                "message": f"Bedtime window. Target {sleep_target}h tonight — put the screens down.",
                "priority": "high",
                "suppress_in_focus": False,
            })

        # ── Streak protection ──────────────────────────────────────────
        streaks = engine.get_streaks()
        for domain, count in streaks.items():
            if count >= 3 and self._streak_at_risk(domain, dash):
                nudges.append({
                    "type": "streak_risk",
                    "domain": domain,
                    "message": f"Your {count}-day {domain} streak breaks today if you don't log. Don't let it slip.",
                    "priority": "high",
                    "suppress_in_focus": False,
                })

        # ── Filter based on focus mode ─────────────────────────────────
        if in_focus:
            nudges = [n for n in nudges if not n.get("suppress_in_focus", False)]

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        nudges.sort(key=lambda n: priority_order.get(n.get("priority", "low"), 3))

        return nudges

    def get_adaptive_goals(self) -> Dict:
        return self.goals_engine.generate()

    def _is_focus_mode(self) -> bool:
        """Check if user is currently in a focus/deep work session."""
        # Lightweight check — avoid calling guardian.check_work_status()
        # which does expensive git repo scanning
        try:
            from pathlib import Path
            focus_file = Path(__file__).parent.parent / "data" / "focus_session.json"
            if focus_file.exists():
                import json
                data = json.loads(focus_file.read_text(encoding="utf-8"))
                return data.get("active", False)
        except Exception:
            pass
        return False

    def _streak_at_risk(self, domain: str, dashboard: Dict) -> bool:
        """Check if a streak is at risk of breaking today."""
        hour = datetime.now().hour
        if hour < 18:
            return False  # Too early to warn

        domain_data = dashboard.get(domain, {})
        if domain == "hydration":
            return domain_data.get("pct", 0) < 50
        elif domain == "sleep":
            return not domain_data.get("logged", False)
        elif domain == "nutrition":
            return domain_data.get("meal_count", 0) < 2
        elif domain == "skincare":
            return not domain_data.get("morning_done") and not domain_data.get("evening_done")
        return False


# Singleton
_coach: Optional[LifeCoach] = None


def get_life_coach() -> LifeCoach:
    global _coach
    if _coach is None:
        _coach = LifeCoach()
    return _coach
