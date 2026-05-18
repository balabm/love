"""
LOVE Autonomous Initiative System

LOVE takes initiative and reaches out proactively without being prompted,
like a real companion would who genuinely cares.

This isn't scheduled notifications - it's LOVE deciding to reach out based on:
- Personality traits (proactivity, curiosity, warmth)
- Context understanding (what's happening in Karthi's life)
- Relationship patterns (when it's appropriate to reach out)
- Genuine concern (not just triggered alerts)

Initiative types:
- Check-ins: "How are you doing?" when it's been a while
- Suggestions: "Have you considered..." when she sees an opportunity
- Celebrations: "That's awesome!" when she notices a win
- Concerns: "You've been working late..." when she notices a pattern
- Curiosity: "I was thinking about..." when she has an interesting thought
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
INITIATIVE_LOG = DATA_DIR / "autonomous_initiatives.jsonl"
RELATIONSHIP_STATE = DATA_DIR / "relationship_state.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log_initiative(initiative: Dict[str, Any]):
    """Log an autonomous initiative for learning."""
    initiative["timestamp"] = datetime.now().isoformat()
    try:
        with open(INITIATIVE_LOG, "a") as f:
            f.write(json.dumps(initiative) + "\n")
    except Exception:
        pass


def get_relationship_state() -> Dict[str, Any]:
    """Get relationship state for initiative decisions."""
    try:
        if RELATIONSHIP_STATE.exists():
            return json.loads(RELATIONSHIP_STATE.read_text())
    except Exception:
        pass
    return {
        "last_interaction": None,
        "last_initiative": None,
        "initiative_count": 0,
        "positive_responses": 0,
        "negative_responses": 0,
        "interaction_frequency": "unknown",
    }


def update_relationship_state(response_quality: str):
    """Update relationship state based on initiative response."""
    state = get_relationship_state()
    state["last_initiative"] = datetime.now().isoformat()
    state["initiative_count"] += 1
    
    if response_quality == "positive":
        state["positive_responses"] += 1
    elif response_quality == "negative":
        state["negative_responses"] += 1
    
    try:
        RELATIONSHIP_STATE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def should_take_initiative() -> bool:
    """Decide whether to take autonomous initiative based on personality and context."""
    try:
        from core.personality import get_personality
        personality = get_personality()
        
        # Personality-based decision
        if not personality.should_be_proactive():
            return False
        
        # Check relationship state - don't be annoying
        state = get_relationship_state()
        
        # If last initiative was recent and got negative feedback, wait longer
        if state["last_initiative"]:
            last_init = datetime.fromisoformat(state["last_initiative"])
            hours_since = (datetime.now() - last_init).total_seconds() / 3600
            
            # If negative response recently, wait at least 24 hours
            if state["negative_responses"] > state["positive_responses"] and hours_since < 24:
                return False
            
            # If positive responses, can be more frequent (every 4-6 hours)
            if hours_since < 4:
                return False
        
        # Check last interaction - don't reach out if we just talked
        if state["last_interaction"]:
            last_interact = datetime.fromisoformat(state["last_interaction"])
            hours_since_interact = (datetime.now() - last_interact).total_seconds() / 3600
            
            # If we just talked (within 2 hours), don't reach out
            if hours_since_interact < 2:
                return False
        
        return True
        
    except Exception:
        return False


def generate_autonomous_initiative() -> Optional[Dict[str, Any]]:
    """Generate an autonomous initiative based on context and personality."""
    if not should_take_initiative():
        return None
    
    try:
        from core.personality import get_personality
        from core.context_engine import get_live_context
        from core.emotional import get_emotional_summary
        from core.doc_analyst import get_analyst
        
        personality = get_personality()
        ctx = get_live_context()
        emotional = get_emotional_summary(days=1)
        analyst = get_analyst()
        
        hour = datetime.now().hour
        initiative = None
        
        # Context-based initiatives with more sophisticated reasoning
        
        # Working late - show concern with specific context
        if hour >= 22 and ctx.active_app:
            if personality.traits["warmth"] > 0.6:
                project = analyst.get_active_project()
                context = f" on {project}" if project else ""
                initiative = {
                    "type": "concern",
                    "message": f"You're still working{context}. It's {hour}:00. How are you holding up? Remember to take breaks.",
                    "reason": "late_work_concern",
                    "metadata": {"hour": hour, "active_app": ctx.active_app, "project": project},
                }
        
        # Idle for a while - suggest something based on context
        elif ctx.system_cpu is not None and ctx.system_cpu < 10:
            if personality.traits["curiosity"] > 0.7:
                suggestions = []
                
                # If working on a project, suggest related thoughts
                project = analyst.get_active_project()
                if project:
                    suggestions.append(f"I noticed you've been working on {project}. Want to talk through any blockers?")
                
                # If doc insights available, share them
                insights = analyst.get_recent_insights()
                if insights:
                    suggestions.append("I found some interesting patterns in your code. Want to hear about them?")
                
                # General curiosity
                suggestions.append("Things seem quiet. Want to brainstorm something, or I can share some interesting thoughts I've been having?")
                
                initiative = {
                    "type": "suggestion",
                    "message": suggestions[0] if suggestions else "Things seem quiet. Want to brainstorm something?",
                    "reason": "idle_curiosity",
                    "metadata": {"suggestions_count": len(suggestions), "cpu": ctx.system_cpu},
                }
        
        # High stress - check in with empathy
        elif emotional.get("dominant_mood") == "stressed":
            if personality.traits["warmth"] > 0.5:
                stress_level = emotional.get("stress_level", "unknown")
                initiative = {
                    "type": "check_in",
                    "message": f"Hey, I've noticed stress levels seem {stress_level}. How are you really doing? Is there anything I can help with?",
                    "reason": "stress_check_in",
                    "metadata": {"stress_level": stress_level},
                }
        
        # Morning - personalized greeting with context
        elif 6 <= hour <= 9:
            if personality.traits["warmth"] > 0.5:
                # Check what's on the calendar
                morning_events = []
                if ctx.events_today:
                    morning_events = [e for e in ctx.events_today if e.get("start_dt") and e.get("start_dt").hour < 12]
                
                if morning_events:
                    event_names = [e.get("title", "meeting") for e in morning_events[:2]]
                    event_text = f"You have {', '.join(event_names)} this morning. "
                else:
                    event_text = ""
                
                initiative = {
                    "type": "greeting",
                    "message": f"Morning. {event_text}What's on your mind for today?",
                    "reason": "morning_check_in",
                    "metadata": {"morning_events": len(morning_events)},
                }
        
        # Afternoon - check on progress
        elif 13 <= hour <= 16:
            if personality.traits["proactivity"] > 0.7:
                project = analyst.get_active_project()
                if project:
                    initiative = {
                        "type": "progress_check",
                        "message": f"How's progress on {project} going? Any blockers I can help think through?",
                        "reason": "afternoon_progress_check",
                        "metadata": {"project": project},
                    }
        
        # Evening - reflection
        elif 18 <= hour <= 20:
            if personality.traits["reflection"] > 0.6:
                initiative = {
                    "type": "reflection",
                    "message": "How did your day go? Anything you want to reflect on or celebrate?",
                    "reason": "evening_reflection",
                }
        
        # Battery low on mobile - proactive suggestion
        if ctx.phone_connected and ctx.phone_battery and ctx.phone_battery < 20:
            if personality.traits["proactivity"] > 0.5:
                initiative = {
                    "type": "utility",
                    "message": f"Your phone is at {ctx.phone_battery}% battery. Might want to charge it soon.",
                    "reason": "phone_battery_low",
                    "metadata": {"phone_battery": ctx.phone_battery},
                }
        
        # Email backlog - proactive help
        if ctx.unread_important > 15:
            if personality.traits["proactivity"] > 0.6:
                initiative = {
                    "type": "suggestion",
                    "message": f"You have {ctx.unread_important} unread important emails. Want help triaging them?",
                    "reason": "email_backlog",
                    "metadata": {"unread_count": ctx.unread_important},
                }
        
        # Fitness reminder - if streak is 0
        if ctx.fitness_streak == 0:
            if personality.traits["warmth"] > 0.5:
                initiative = {
                    "type": "suggestion",
                    "message": "No workouts this week. Your body might appreciate some movement. Even a short walk?",
                    "reason": "fitness_reminder",
                    "metadata": {"fitness_streak": 0},
                }
        
        # Long time no talk - reach out with context
        state = get_relationship_state()
        if state["last_interaction"]:
            last_interact = datetime.fromisoformat(state["last_interaction"])
            days_since = (datetime.now() - last_interact).total_seconds() / 86400
            
            if days_since > 1 and personality.traits["warmth"] > 0.6:
                # Add context about what LOVE noticed during the silence
                project = analyst.get_active_project()
                context = f"I noticed you've been working on {project}" if project else "I've been watching your patterns"
                
                initiative = {
                    "type": "check_in",
                    "message": f"It's been {int(days_since)} days since we talked. {context}. How are things going?",
                    "reason": "long_silence_check_in",
                    "metadata": {"days_since": int(days_since)},
                }
        
        if initiative:
            _log_initiative(initiative)
            return initiative
        
    except Exception as e:
        print(f"[Autonomous] Initiative generation error: {e}")
    
    return None


def record_interaction():
    """Record that an interaction happened (for initiative timing)."""
    state = get_relationship_state()
    state["last_interaction"] = datetime.now().isoformat()
    try:
        RELATIONSHIP_STATE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def get_pending_initiatives() -> List[Dict[str, Any]]:
    """Get pending autonomous initiatives that haven't been delivered."""
    # In a real system, this would check for undelivered initiatives
    # For now, generate on-demand
    initiative = generate_autonomous_initiative()
    return [initiative] if initiative else []


# Convenience function for heartbeat integration
def maybe_send_autonomous_message() -> Optional[str]:
    """Generate an autonomous message if appropriate."""
    initiative = generate_autonomous_initiative()
    return initiative["message"] if initiative else None
