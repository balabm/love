"""
cross_domain_intelligence.py — Wave 24: Cross-Domain Intelligence

Detects correlations and patterns across all of LOVE's life domains:
  - Sleep quality -> next-day productivity
  - Hydration levels -> stress/focus
  - Nutrition quality -> energy/mood
  - Skincare consistency -> routine discipline
  - Work hours -> recovery needs

Returns actionable insights, not raw data.
Philosophy: LOVE notices what the user can't see about themselves.
"""

from datetime import date, timedelta
from typing import Dict, List, Any, Optional


def get_correlations(days: int = 7) -> Dict[str, Any]:
    """
    Analyze cross-domain correlations over the past N days.
    Returns insights the user can act on.
    """
    correlations = []
    warnings = []
    positives = []

    try:
        from core.life_domains import get_life_domains_engine
        engine = get_life_domains_engine()
        sleep_insights = engine.sleep.get_insights(days)
        hydration_insights = engine.hydration.get_insights(days)
        nutrition_insights = engine.nutrition.get_insights(days)
        skincare_insights = engine.skincare.get_insights(days)
    except Exception:
        return {"correlations": [], "warnings": [], "positives": [], "error": "Life domains unavailable"}

    # ── Sleep vs everything ───────────────────────────────────────────────
    avg_sleep = sleep_insights.get("avg_hours", 0)
    avg_quality = sleep_insights.get("avg_quality", 0)
    sleep_history = sleep_insights.get("history", [])

    if avg_sleep > 0 and avg_sleep < 6.5:
        warnings.append(f"Averaging only {avg_sleep}h sleep — expect focus and mood to degrade. Consider a bedtime alarm.")
    elif avg_sleep >= 7.5:
        positives.append(f"Sleep is solid at {avg_sleep}h average — this fuels everything else.")

    if avg_quality > 0 and avg_quality < 5:
        warnings.append(f"Sleep quality averaging {avg_quality}/10 — even with enough hours, poor quality hurts recovery.")

    # Sleep + hydration correlation
    hydration_history = hydration_insights.get("history", [])
    if len(sleep_history) >= 3 and len(hydration_history) >= 3:
        # Check if low hydration days correlate with poor sleep
        low_hydra_poor_sleep = 0
        checked = 0
        for i in range(min(len(sleep_history), len(hydration_history)) - 1):
            h_day = hydration_history[i]
            s_next = sleep_history[i + 1] if i + 1 < len(sleep_history) else None
            if h_day.get("total_ml", 0) < 1500 and s_next and s_next.get("quality", 10) < 5:
                low_hydra_poor_sleep += 1
            if h_day.get("total_ml", 0) > 0:
                checked += 1
        if checked > 2 and low_hydra_poor_sleep >= 2:
            correlations.append("Low hydration days are followed by poor sleep — try finishing your water goal by 6pm.")

    # ── Nutrition consistency ─────────────────────────────────────────────
    avg_meals = nutrition_insights.get("avg_meals_per_day", 0)
    avg_meal_quality = nutrition_insights.get("avg_quality", 0)

    if avg_meals > 0 and avg_meals < 2.5:
        warnings.append(f"Averaging {avg_meals} meals/day — skipping meals tanks your energy and focus. Even a quick snack helps.")

    if avg_meal_quality > 0 and avg_meal_quality < 4:
        warnings.append(f"Meal quality averaging {avg_meal_quality}/10 — junk food compounds stress. One good meal a day makes a difference.")
    elif avg_meal_quality >= 7:
        positives.append(f"Nutrition quality at {avg_meal_quality}/10 — your body is getting what it needs.")

    # ── Skincare discipline as routine proxy ──────────────────────────────
    morning_pct = skincare_insights.get("morning_consistency", 0)
    evening_pct = skincare_insights.get("evening_consistency", 0)
    skincare_streak = skincare_insights.get("streak", 0)

    if morning_pct > 70 and evening_pct > 70:
        positives.append(f"Skincare consistency is high ({morning_pct}% AM, {evening_pct}% PM) — strong routine discipline.")
    elif morning_pct < 30 and evening_pct < 30 and (morning_pct + evening_pct) > 0:
        warnings.append("Both morning and evening skincare routines are inconsistent — this suggests your daily structure is slipping.")

    # ── Hydration ─────────────────────────────────────────────────────────
    avg_hydra = hydration_insights.get("avg_ml", 0)
    hydra_goal = hydration_insights.get("goal_ml", 2500)
    if avg_hydra > 0 and avg_hydra < hydra_goal * 0.6:
        warnings.append(f"Only averaging {avg_hydra}ml water/day (goal: {hydra_goal}ml). Dehydration kills focus before you notice it.")
    elif avg_hydra >= hydra_goal * 0.9:
        positives.append(f"Hydration on track at {avg_hydra}ml/day — well done.")

    # ── Streak analysis ───────────────────────────────────────────────────
    streaks = {
        "hydration": hydration_insights.get("streak", 0),
        "sleep": sleep_insights.get("streak", 0),
        "nutrition": nutrition_insights.get("streak", 0),
        "skincare": skincare_streak,
    }
    active_streaks = {k: v for k, v in streaks.items() if v >= 3}
    broken_streaks = [k for k, v in streaks.items() if v == 0]

    if len(active_streaks) >= 3:
        streak_str = ", ".join(f"{k} ({v}d)" for k, v in active_streaks.items())
        positives.append(f"Multiple active streaks: {streak_str} — momentum is building.")
    if len(broken_streaks) >= 3:
        correlations.append(f"No active streaks in {', '.join(broken_streaks)} — small daily wins rebuild momentum.")

    # ── Cross-domain compound effects ─────────────────────────────────────
    if avg_sleep < 6 and avg_meals < 2 and avg_hydra < 1500:
        correlations.append("Sleep, nutrition, and hydration are all low — this triple deficit compounds fast. Pick one to fix today.")
    elif avg_sleep >= 7 and avg_meals >= 2.5 and avg_hydra >= 2000:
        correlations.append("Sleep, nutrition, and hydration are all in good shape — your physical foundation is solid.")

    # ── Adaptive goal suggestions ─────────────────────────────────────────
    suggestions = []
    if avg_sleep > 0 and avg_sleep < 7:
        suggestions.append({"domain": "sleep", "suggestion": f"Try for {min(8, avg_sleep + 0.5)}h tonight", "reason": "incremental improvement"})
    if avg_hydra > 0 and avg_hydra < hydra_goal:
        target = min(hydra_goal, avg_hydra + 500)
        suggestions.append({"domain": "hydration", "suggestion": f"Aim for {target}ml today", "reason": "step up gradually"})
    if avg_meal_quality > 0 and avg_meal_quality < 6:
        suggestions.append({"domain": "nutrition", "suggestion": "Make one meal today a 7+ quality", "reason": "one good meal lifts the average"})

    return {
        "correlations": correlations,
        "warnings": warnings,
        "positives": positives,
        "suggestions": suggestions,
        "streaks": streaks,
        "period_days": days,
    }


def get_life_report(days: int = 7) -> Dict[str, Any]:
    """
    Generate a complete life report combining domain data + correlations.
    Used for the daily briefing and Wave Engine.
    """
    correlations = get_correlations(days)

    try:
        from core.life_domains import get_life_domains_engine
        engine = get_life_domains_engine()
        dashboard = engine.get_dashboard()
        insights = engine.get_weekly_insights()
    except Exception:
        dashboard = {}
        insights = {}

    return {
        "dashboard": dashboard,
        "insights": insights,
        "correlations": correlations,
        "generated_for_days": days,
    }
