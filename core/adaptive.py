"""
LOVE Adaptive Behavior Engine

LOVE doesn't follow fixed instructions — it learns from every interaction.
This module tracks what resonates, what falls flat, Karthi's energy patterns,
preferred communication style, and adapts LOVE's behavior in real time.

It answers: "What kind of companion does Karthi need RIGHT NOW?"
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ADAPTIVE_FILE = DATA_DIR / "adaptive_state.json"
INTERACTION_LOG = DATA_DIR / "interaction_log.jsonl"

_state_lock = threading.Lock()

# ── Default state ─────────────────────────────────────────────────────────────

DEFAULT_STATE = {
    "preferred_response_length": "medium",   # short / medium / long
    "preferred_tone": "direct",              # direct / warm / analytical / playful
    "energy_pattern": {},                    # hour -> avg engagement score
    "topics_engaged": {},                    # topic -> count
    "topics_ignored": {},                    # topic -> count
    "mode_usage": {},                        # mode -> count
    "avg_session_length": 0,
    "last_active_hour": None,
    "last_mood": "neutral",
    "frustration_signals": 0,
    "delight_signals": 0,
    "total_interactions": 0,
    "response_rating": {},                   # "short" / "medium" / "long" -> avg satisfaction
    "conversation_velocity": "normal",       # fast / normal / slow
    "proactive_receptivity": 0.5,           # 0-1: does user welcome unprompted messages?
    "updated_at": None,
}


def _load_state() -> Dict[str, Any]:
    try:
        if ADAPTIVE_FILE.exists():
            return {**DEFAULT_STATE, **json.loads(ADAPTIVE_FILE.read_text())}
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.adaptive")
    return dict(DEFAULT_STATE)


def _save_state(state: Dict[str, Any]):
    try:
        state["updated_at"] = datetime.now().isoformat()
        ADAPTIVE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.adaptive")


def _log_interaction(data: Dict[str, Any]):
    try:
        data["ts"] = datetime.now().isoformat()
        with open(INTERACTION_LOG, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.adaptive")


# ── Signal detection ──────────────────────────────────────────────────────────

FRUSTRATION_SIGNALS = [
    "wrong", "no", "that's not", "stop", "again", "ugh", "wtf", "useless",
    "not what i", "you're not", "forget it", "never mind", "whatever",
    "don't understand", "missed", "off topic"
]

DELIGHT_SIGNALS = [
    "exactly", "yes!", "perfect", "love it", "great", "thanks", "awesome",
    "finally", "that's it", "you got it", "nice", "good one", "brilliant",
    "exactly right", "spot on", "keep going", "more like this"
]

SHORT_RESPONSE_SIGNALS = ["short", "brief", "quick", "tldr", "summarize", "one line", "simple"]
LONG_RESPONSE_SIGNALS = ["explain", "detail", "elaborate", "full", "deep dive", "everything about"]


def detect_signals(user_input: str) -> Dict[str, bool]:
    text = user_input.lower()
    return {
        "frustrated": any(s in text for s in FRUSTRATION_SIGNALS),
        "delighted": any(s in text for s in DELIGHT_SIGNALS),
        "wants_short": any(s in text for s in SHORT_RESPONSE_SIGNALS),
        "wants_long": any(s in text for s in LONG_RESPONSE_SIGNALS),
    }


def _estimate_topic(user_input: str) -> str:
    """Rough topic classification from user input."""
    text = user_input.lower()
    if any(w in text for w in ["code", "bug", "function", "error", "python", "js", "api"]):
        return "coding"
    if any(w in text for w in ["gym", "workout", "fitness", "run", "exercise", "calories"]):
        return "fitness"
    if any(w in text for w in ["money", "salary", "invest", "crypto", "finance", "stock"]):
        return "finance"
    if any(w in text for w in ["feel", "mood", "tired", "stress", "anxious", "happy", "sad"]):
        return "emotional"
    if any(w in text for w in ["plan", "goal", "task", "todo", "schedule", "meeting"]):
        return "planning"
    if any(w in text for w in ["news", "latest", "happened", "today", "world"]):
        return "news"
    if any(w in text for w in ["learn", "study", "read", "book", "course"]):
        return "learning"
    return "general"


def _estimate_response_length(response: str) -> str:
    words = len(response.split())
    if words < 40:
        return "short"
    if words < 120:
        return "medium"
    return "long"


# ── Core adaptation logic ─────────────────────────────────────────────────────

def record_interaction(user_input: str, response: str, mode: str = "general",
                       response_time_ms: int = 0):
    """
    Called after every chat turn. Updates all adaptive signals.
    """
    with _state_lock:
        state = _load_state()
        signals = detect_signals(user_input)
        topic = _estimate_topic(user_input)
        resp_len = _estimate_response_length(response)
        hour = datetime.now().hour

        # Update counts
        state["total_interactions"] = state.get("total_interactions", 0) + 1
        state["last_active_hour"] = hour

        # Mode tracking
        state["mode_usage"][mode] = state["mode_usage"].get(mode, 0) + 1

        # Topic tracking
        state["topics_engaged"][topic] = state["topics_engaged"].get(topic, 0) + 1

        # Energy pattern — track engagement by hour
        ep = state.get("energy_pattern", {})
        ep[str(hour)] = ep.get(str(hour), 0) + 1
        state["energy_pattern"] = ep

        # Frustration / delight signals
        if signals["frustrated"]:
            state["frustration_signals"] = state.get("frustration_signals", 0) + 1
            # If frustrated, try shorter responses
            if state["preferred_response_length"] == "long":
                state["preferred_response_length"] = "medium"
            elif state["preferred_response_length"] == "medium":
                state["preferred_response_length"] = "short"

        if signals["delighted"]:
            state["delight_signals"] = state.get("delight_signals", 0) + 1
            # If delighted, maintain current length
            rr = state.get("response_rating", {})
            rr[resp_len] = rr.get(resp_len, 0) + 1
            state["response_rating"] = rr

        # Explicit length preference
        if signals["wants_short"]:
            state["preferred_response_length"] = "short"
        elif signals["wants_long"]:
            state["preferred_response_length"] = "long"

        # Conversation velocity — messages per hour
        # (simplified: track recent timestamp density)
        _log_interaction({
            "user_input": user_input[:100],
            "mode": mode,
            "topic": topic,
            "resp_len": resp_len,
            "signals": signals,
            "hour": hour,
        })

        _save_state(state)


def get_adaptation_context() -> str:
    """
    Returns a short instruction string to inject into the LLM prompt,
    telling LOVE how to adapt its current response.
    """
    state = _load_state()

    lines = []
    hour = datetime.now().hour

    # Response length
    pref_len = state.get("preferred_response_length", "medium")
    if pref_len == "short":
        lines.append("Keep this response BRIEF — under 3 sentences. User prefers short answers.")
    elif pref_len == "long":
        lines.append("User engages well with detailed answers — go deep if relevant.")

    # Frustration check
    frustration = state.get("frustration_signals", 0)
    delight = state.get("delight_signals", 0)
    total = state.get("total_interactions", 1)
    if frustration > 2 and frustration / max(total, 1) > 0.15:
        lines.append("User has shown some frustration recently — be more precise, less verbose.")

    # Time-based tone
    if 5 <= hour <= 8:
        lines.append("Morning — keep tone energetic and forward-looking.")
    elif 22 <= hour or hour < 3:
        lines.append("Late night — keep tone calm, don't push too hard.")
    elif 13 <= hour <= 14:
        lines.append("Post-lunch dip — keep response punchy and easy to absorb.")

    # Most engaged topic
    topics = state.get("topics_engaged", {})
    if topics:
        top_topic = max(topics, key=topics.get)
        if topics[top_topic] > 3:
            lines.append(f"User has been focused on {top_topic} lately — awareness context.")

    # Proactive receptivity
    proactive = state.get("proactive_receptivity", 0.5)
    if proactive > 0.7:
        lines.append("User welcomes proactive insights — feel free to add relevant observations.")
    elif proactive < 0.3:
        lines.append("User prefers direct answers — avoid unsolicited commentary.")

    return "\n".join(lines)


def get_current_persona_hint() -> str:
    """Decide what personality mode LOVE should lean into right now."""
    state = _load_state()
    hour = datetime.now().hour
    last_mood = state.get("last_mood", "neutral")
    frustration = state.get("frustration_signals", 0)
    delight = state.get("delight_signals", 0)

    if frustration > delight and frustration > 2:
        return "direct"  # Cut the warmth, just be accurate
    if 21 <= hour or hour < 6:
        return "calm"    # Night mode
    if 6 <= hour <= 9:
        return "sharp"   # Morning — quick, focused
    if delight > frustration:
        return "playful" # User is in good mood
    return "warm"


def update_proactive_receptivity(user_responded_positively: bool):
    """Update whether user welcomes unprompted messages."""
    with _state_lock:
        state = _load_state()
        current = state.get("proactive_receptivity", 0.5)
        # Exponential moving average
        if user_responded_positively:
            state["proactive_receptivity"] = current * 0.8 + 0.2
        else:
            state["proactive_receptivity"] = current * 0.8
        _save_state(state)


def get_peak_hours() -> List[int]:
    """Hours when Karthi is most active/engaged."""
    state = _load_state()
    ep = state.get("energy_pattern", {})
    if not ep:
        return [9, 10, 14, 20, 21]  # Default guess
    sorted_hours = sorted(ep.items(), key=lambda x: x[1], reverse=True)
    return [int(h) for h, _ in sorted_hours[:5]]


def get_adaptive_summary() -> Dict[str, Any]:
    """Full adaptive state summary for dashboard/debug."""
    state = _load_state()
    return {
        "preferred_length": state.get("preferred_response_length"),
        "preferred_tone": state.get("preferred_tone"),
        "peak_hours": get_peak_hours(),
        "top_topics": sorted(state.get("topics_engaged", {}).items(), key=lambda x: x[1], reverse=True)[:5],
        "total_interactions": state.get("total_interactions", 0),
        "frustration_signals": state.get("frustration_signals", 0),
        "delight_signals": state.get("delight_signals", 0),
        "proactive_receptivity": state.get("proactive_receptivity", 0.5),
        "persona_hint": get_current_persona_hint(),
        "adaptation_context": get_adaptation_context(),
    }
