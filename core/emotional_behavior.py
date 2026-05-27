"""
LOVE Emotional Behavior Engine — Wave 27

Mood doesn't just change LOVE's tone. It changes what LOVE does.

When you're stressed → LOVE stops suggesting tasks, starts suggesting breaks.
When you're tired → LOVE offers lighter work, defers meetings.
When you're focused → LOVE silences low-priority nudges, protects your flow.
When you're overwhelmed → LOVE gives you one thing at a time.
When you're in crisis → LOVE pushes a recovery message immediately.
"""

from typing import Dict, Any, List, Optional


# ── Behavioral Rules ────────────────────────────────────────────────────────

def apply_emotional_filter(interventions: List[Dict], mood_state: Optional[Dict] = None) -> List[Dict]:
    """
    Filter and modify orchestrator interventions based on current emotional state.

    - stressed/overwhelmed: suppress task suggestions, inject break nudge
    - tired: soften task language, suppress meetings
    - focused: drop low-priority interruptions
    - neutral/positive: pass through unchanged
    """
    if not mood_state:
        try:
            from core.emotional import get_current_dominant_mood
            mood_state = get_current_dominant_mood()
        except Exception:
            return interventions

    mood = mood_state.get("mood", "neutral")
    stress = mood_state.get("stress", 0)
    is_overwhelmed = mood_state.get("is_overwhelmed", False)
    needs_break = mood_state.get("needs_break", False)
    is_tired = mood_state.get("is_tired", False)
    is_focused = mood_state.get("is_focused", False)

    result = list(interventions)

    if is_overwhelmed or stress > 75:
        # Remove task suggestions entirely
        result = [i for i in result if i.get("category") not in ("task_suggestion", "task", "deadline")]
        # Inject a break nudge at the top
        result.insert(0, {
            "id": "emotional_break_now",
            "category": "nudge",
            "priority": "high",
            "message": "You're overwhelmed. Stop. One thing: breathe for 2 minutes, then pick just one small task.",
            "action": "suggest_break",
            "source": "emotional_behavior",
        })

    elif needs_break or stress > 60:
        # Soften task suggestions, add recovery nudge
        result = [i for i in result if i.get("category") not in ("deadline",)]
        for i in result:
            if i.get("category") in ("task_suggestion", "task"):
                i["message"] = f"[When you're ready] {i.get('message', '')}"
        result.insert(0, {
            "id": "emotional_break_suggested",
            "category": "nudge",
            "priority": "medium",
            "message": "Stress is elevated. A 10-minute break now will save 30 minutes of degraded focus later.",
            "action": "suggest_break",
            "source": "emotional_behavior",
        })

    elif is_tired:
        # Defer meetings, soften tasks, suggest lighter work
        result = [i for i in result if i.get("category") != "meeting_prep"]
        for i in result:
            if i.get("category") in ("task_suggestion", "task"):
                i["message"] = f"Light version: {i.get('message', '')} (you're running low on energy)"

    elif is_focused:
        # Drop low-priority interruptions entirely — protect the zone
        result = [i for i in result if i.get("priority") not in ("low",)]

    return result


def get_proactive_mood_response(mood_state: Dict) -> Optional[Dict]:
    """
    Given a mood state, return a proactive push message if warranted.
    Returns None if no push needed (e.g. neutral, positive).
    """
    mood = mood_state.get("mood", "neutral")
    stress = mood_state.get("stress", 0)
    trend = mood_state.get("trend", "stable")

    if stress > 85:
        return {
            "category": "CRISIS",
            "priority": "critical",
            "message": (
                "Stress is critical right now. Please stop what you're doing. "
                "Walk away from the screen for 5 minutes. You can come back to it."
            ),
        }
    elif stress > 70 and trend == "rising":
        return {
            "category": "NUDGE",
            "priority": "high",
            "message": "Stress is rising steadily. Take a break before it peaks — 10 minutes now prevents a crash later.",
        }
    elif mood == "overwhelmed":
        return {
            "category": "NUDGE",
            "priority": "high",
            "message": "You're overwhelmed. Let's simplify: what is the single most important thing right now? Everything else waits.",
        }
    elif mood == "sad":
        return {
            "category": "NUDGE",
            "priority": "medium",
            "message": "Noticed you're feeling low. You don't have to push through. Rest is valid. I'm here.",
        }
    elif mood == "anxious":
        return {
            "category": "NUDGE",
            "priority": "medium",
            "message": "Anxiety detected. Ground yourself: name 5 things you can see right now. Then one small next step.",
        }

    return None


def get_focus_mode_interventions(active_tasks: List[Dict]) -> List[Dict]:
    """
    When in focus mode, return only the single most important task.
    Strip all nudges, suggestions, and low-priority items.
    """
    critical = [t for t in active_tasks if t.get("priority") in ("critical", "high")]
    if critical:
        top = critical[0]
        return [{
            "id": "focus_top_task",
            "category": "task",
            "priority": "high",
            "message": f"You're in focus mode. Top task: {top.get('title', top.get('message', 'unknown'))}",
            "source": "emotional_behavior",
        }]
    return []
