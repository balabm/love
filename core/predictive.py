"""
LOVE Predictive Engine

Anticipates Karthi's needs before he asks.

Examples:
- 8:55am every weekday → "Daily standup at 9. Want me to pull yesterday's commits?"
- Friday 5pm → "Heads up — weekend. Want me to summarize the week?"
- After 3 hours of coding → "You've been at this for 3 hours. Break?"
- New email from manager → "Quick — your manager just emailed. Want the gist?"
- Battery <15% + meeting in 20min → "Plug in now or you'll lose it during the call"

Built on top of: heartbeat, context_engine, adaptive, unified_awareness.
Pattern detection is the secret sauce — LOVE learns what Karthi does WHEN.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PATTERNS_FILE = DATA_DIR / "patterns.json"
PREDICTIONS_LOG = DATA_DIR / "predictions.jsonl"
ROUTINE_FILE = DATA_DIR / "routines.json"


# ── Pattern detection ────────────────────────────────────────────────────────

def _load_patterns() -> Dict[str, Any]:
    if PATTERNS_FILE.exists():
        try:
            return json.loads(PATTERNS_FILE.read_text())
        except Exception:
            pass
    return {
        "hourly_topics": {},      # "9": ["coding", "email", ...]
        "weekday_topics": {},     # "Monday": [...]
        "app_sequences": {},      # "vscode -> chrome": count
        "topic_transitions": {},  # "coding -> break": count
        "routines": [],           # detected: "every Mon 9am: standup"
        "last_seen": {},          # "topic" -> last timestamp
    }


def _save_patterns(p: Dict[str, Any]):
    try:
        PATTERNS_FILE.write_text(json.dumps(p, indent=2))
    except Exception:
        pass


def record_event(event_type: str, details: Dict[str, Any] = None):
    """Record any event for pattern learning."""
    patterns = _load_patterns()
    now = datetime.now()
    hour = str(now.hour)
    weekday = now.strftime("%A")

    # Hourly distribution
    ht = patterns.setdefault("hourly_topics", {}).setdefault(hour, [])
    ht.append(event_type)
    patterns["hourly_topics"][hour] = ht[-50:]  # Keep last 50

    # Weekday distribution
    wt = patterns.setdefault("weekday_topics", {}).setdefault(weekday, [])
    wt.append(event_type)
    patterns["weekday_topics"][weekday] = wt[-50:]

    # Last seen
    patterns.setdefault("last_seen", {})[event_type] = now.isoformat()

    _save_patterns(patterns)


def detect_routines() -> List[Dict[str, Any]]:
    """Find recurring patterns: 'every weekday 9am: coding'"""
    patterns = _load_patterns()
    routines = []

    hourly = patterns.get("hourly_topics", {})
    for hour_str, events in hourly.items():
        if len(events) < 5:
            continue
        counter = Counter(events)
        most_common, count = counter.most_common(1)[0]
        if count / len(events) > 0.4:  # >40% consistency
            routines.append({
                "type": "hourly",
                "hour": int(hour_str),
                "topic": most_common,
                "confidence": round(count / len(events), 2),
                "occurrences": count,
            })

    weekday = patterns.get("weekday_topics", {})
    for day, events in weekday.items():
        if len(events) < 5:
            continue
        counter = Counter(events)
        most_common, count = counter.most_common(1)[0]
        if count / len(events) > 0.5:
            routines.append({
                "type": "weekday",
                "day": day,
                "topic": most_common,
                "confidence": round(count / len(events), 2),
                "occurrences": count,
            })

    routines.sort(key=lambda r: r["confidence"], reverse=True)

    # Save routines
    try:
        ROUTINE_FILE.write_text(json.dumps(routines, indent=2))
    except Exception:
        pass

    return routines


# ── Predictions ──────────────────────────────────────────────────────────────

def predict_next_need() -> Optional[Dict[str, Any]]:
    """
    Based on time, recent context, and routines — predict what Karthi might need.
    Returns: { prediction, confidence, suggested_action, reason, metadata }
    """
    now = datetime.now()
    hour = now.hour
    weekday = now.strftime("%A")
    minute = now.minute

    predictions = []

    # ── Time-based predictions ──
    # Morning standup window
    if weekday in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        if hour == 8 and minute > 30:
            predictions.append({
                "prediction": "Daily standup approaching",
                "confidence": 0.6,
                "suggested_action": "summarize yesterday's work + today's plan",
                "reason": "Weekday morning, near typical standup hour",
                "metadata": {"time_type": "morning_standup"},
            })
        if hour == 17 and minute > 30:
            predictions.append({
                "prediction": "End of work day — wind down",
                "confidence": 0.65,
                "suggested_action": "summarize today's progress, surface tomorrow's priorities",
                "reason": "5:30pm on a weekday",
                "metadata": {"time_type": "end_of_day"},
            })

    # Friday wind down
    if weekday == "Friday" and hour >= 16:
        predictions.append({
            "prediction": "Weekend approaching",
            "confidence": 0.7,
            "suggested_action": "weekly summary + weekend ideas",
            "reason": "Friday late afternoon",
            "metadata": {"time_type": "friday_winddown"},
        })

    # Late night working
    if hour >= 23 or hour < 2:
        predictions.append({
            "prediction": "Late-night work — may affect sleep",
            "confidence": 0.7,
            "suggested_action": "gentle nudge to wrap up + save context for tomorrow",
            "reason": f"Active at {hour}:00",
            "metadata": {"time_type": "late_night"},
        })

    # Lunch time
    if 12 <= hour < 14 and minute < 30:
        predictions.append({
            "prediction": "Lunch break window",
            "confidence": 0.5,
            "suggested_action": "remind about food, suggest break",
            "reason": "Typical lunch hours",
            "metadata": {"time_type": "lunch"},
        })

    # ── Routine-based predictions ──
    routines = detect_routines()
    for r in routines:
        if r["type"] == "hourly" and r["hour"] == hour and r["confidence"] > 0.5:
            predictions.append({
                "prediction": f"You usually {r['topic']} at this hour",
                "confidence": r["confidence"],
                "suggested_action": f"prepare for {r['topic']}",
                "reason": f"Pattern: {r['confidence']*100:.0f}% of {r['hour']}:00 activity is {r['topic']}",
                "metadata": {"routine_type": "hourly", "topic": r["topic"]},
            })

    # ── Context-based predictions ──
    pred_from_context = _predict_from_context()
    if pred_from_context:
        predictions.extend(pred_from_context)

    # ── Health predictions ──
    pred_from_health = _predict_from_health()
    if pred_from_health:
        predictions.extend(pred_from_health)

    if not predictions:
        return None

    # Pick highest confidence
    predictions.sort(key=lambda p: p["confidence"], reverse=True)
    top = predictions[0]
    top["timestamp"] = now.isoformat()

    _log_prediction(top)
    return top


def _predict_from_context() -> List[Dict[str, Any]]:
    """Use live context engine signals to predict needs."""
    predictions = []
    try:
        from core.context_engine import get_live_context
        ctx = get_live_context()

        # Meeting imminent
        if ctx.next_event:
            mins = ctx.next_event.get("minutes_away", 999)
            if 0 < mins <= 15:
                predictions.append({
                    "prediction": f"Meeting in {mins}min: {ctx.next_event.get('title', 'Unknown')}",
                    "confidence": 0.9,
                    "suggested_action": "prep meeting context, mute notifications",
                    "reason": f"Calendar event {mins} minutes away",
                    "metadata": {"event_title": ctx.next_event.get("title"), "minutes_away": mins},
                })

        # Active app context
        app = ctx.active_window.lower() if ctx.active_window else ""
        if "vscode" in app or "code" in app or "windsurf" in app:
            # Check session length based on activity
            if ctx.activity == "working":
                predictions.append({
                    "prediction": "Deep work session in progress",
                    "confidence": 0.7,
                    "suggested_action": "protect focus time, defer non-urgent interruptions",
                    "reason": "Active coding session detected",
                    "metadata": {"active_app": ctx.active_app, "activity": ctx.activity},
                })

        # Email backlog prediction
        if ctx.unread_important > 20:
            predictions.append({
                "prediction": f"Email backlog: {ctx.unread_important} unread important emails",
                "confidence": 0.8,
                "suggested_action": "suggest email triage session",
                "reason": "High unread email count",
                "metadata": {"unread_count": ctx.unread_important},
            })

        # Task deadline prediction
        if ctx.tasks_due_today > 3:
            predictions.append({
                "prediction": f"{ctx.tasks_due_today} tasks due today",
                "confidence": 0.75,
                "suggested_action": "prioritize today's tasks, suggest focus blocks",
                "reason": "Multiple deadlines today",
                "metadata": {"tasks_due": ctx.tasks_due_today},
            })

        # Phone battery prediction
        if ctx.phone_connected and ctx.phone_battery and ctx.phone_battery < 25:
            predictions.append({
                "prediction": f"Phone battery at {ctx.phone_battery}%",
                "confidence": 0.85,
                "suggested_action": "remind to charge phone",
                "reason": "Mobile device low battery",
                "metadata": {"phone_battery": ctx.phone_battery},
            })

        # Fitness prediction
        if ctx.fitness_streak == 0:
            predictions.append({
                "prediction": "No workouts this week",
                "confidence": 0.7,
                "suggested_action": "suggest movement, even short walk",
                "reason": "Zero fitness streak detected",
                "metadata": {"fitness_streak": 0},
            })

    except Exception:
        pass
    return predictions


def _predict_from_health() -> List[Dict[str, Any]]:
    """Battery + meeting + activity health signals."""
    predictions = []
    try:
        from core.context_engine import get_live_context
        ctx = get_live_context()

        # PC battery
        if ctx.battery is not None and ctx.battery < 25:
            predictions.append({
                "prediction": f"PC battery at {ctx.battery:.0f}%",
                "confidence": 0.85 if ctx.battery < 15 else 0.6,
                "suggested_action": "remind to plug in",
                "reason": "Low battery",
                "metadata": {"battery": ctx.battery, "charging": ctx.battery_charging},
            })

        # CPU usage
        if ctx.system_cpu is not None and ctx.system_cpu > 85:
            predictions.append({
                "prediction": f"CPU at {ctx.system_cpu:.0f}% — system under load",
                "confidence": 0.55,
                "suggested_action": "check for runaway processes",
                "reason": "High CPU usage",
                "metadata": {"cpu": ctx.system_cpu},
            })

        # Meeting + battery combo prediction
        if ctx.next_event and ctx.battery is not None:
            mins = ctx.next_event.get("minutes_away", 999)
            if 0 < mins <= 30 and ctx.battery < 30 and not ctx.battery_charging:
                predictions.append({
                    "prediction": f"Meeting in {mins}min with {ctx.battery:.0f}% battery",
                    "confidence": 0.9,
                    "suggested_action": "plug in now to avoid running out during call",
                    "reason": "Meeting approaching with low battery",
                    "metadata": {"minutes_away": mins, "battery": ctx.battery},
                })

    except Exception:
        pass
    return predictions


def _log_prediction(p: Dict[str, Any]):
    try:
        with open(PREDICTIONS_LOG, "a") as f:
            f.write(json.dumps(p) + "\n")
    except Exception:
        pass


# ── Public API ───────────────────────────────────────────────────────────────

def get_anticipation_message() -> Optional[str]:
    """Get a natural proactive message for current moment, or None."""
    pred = predict_next_need()
    if not pred:
        return None
    if pred["confidence"] < 0.6:
        return None

    # Format as a natural message
    return f"{pred['prediction']}. {pred['suggested_action']}."


def get_predictive_summary() -> Dict[str, Any]:
    """Full predictive state for dashboard."""
    routines = detect_routines()
    current = predict_next_need()
    patterns = _load_patterns()

    return {
        "current_prediction": current,
        "detected_routines": routines[:10],
        "tracked_events": sum(len(v) for v in patterns.get("hourly_topics", {}).values()),
        "active_hours": list(patterns.get("hourly_topics", {}).keys()),
    }


def get_recent_predictions(n: int = 20) -> List[Dict]:
    try:
        if not PREDICTIONS_LOG.exists():
            return []
        lines = PREDICTIONS_LOG.read_text().strip().split("\n")
        return [json.loads(l) for l in lines[-n:] if l]
    except Exception:
        return []


def analyze_patterns(days: int = 7) -> Dict[str, Any]:
    """Analyze recent patterns from the last N days."""
    patterns = _load_patterns()
    
    # Count recent events
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    
    hourly_activity = {}
    weekday_activity = {}
    
    for hour, events in patterns.get("hourly_topics", {}).items():
        hourly_activity[hour] = len(events)
    
    for weekday, events in patterns.get("weekday_topics", {}).items():
        weekday_activity[weekday] = len(events)
    
    # Find most active hours and days
    most_active_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None
    most_active_day = max(weekday_activity.items(), key=lambda x: x[1])[0] if weekday_activity else None
    
    return {
        "analysis_period_days": days,
        "most_active_hour": most_active_hour,
        "most_active_day": most_active_day,
        "hourly_distribution": hourly_activity,
        "weekday_distribution": weekday_activity,
        "detected_routines": len(detect_routines()),
        "total_tracked_events": sum(hourly_activity.values()),
    }


def generate_predictions() -> List[Dict[str, Any]]:
    """Generate multiple predictions based on current patterns."""
    predictions = []
    
    # Get current prediction
    current = predict_next_need()
    if current:
        predictions.append(current)
    
    # Detect routines and generate predictions from them
    routines = detect_routines()
    for routine in routines[:5]:  # Top 5 routines
        if routine.get("confidence", 0) > 0.6:
            predictions.append({
                "prediction": f"Routine: {routine.get('pattern', 'Unknown')}",
                "confidence": routine.get("confidence", 0.5),
                "suggested_action": "Based on detected routine",
                "reason": f"Recurring pattern detected ({routine.get('occurrences', 0)} times)",
            })
    
    return predictions
