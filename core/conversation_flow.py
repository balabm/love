"""
LOVE Conversation Flow Tracker

Multi-turn coherence: LOVE actually follows the thread of conversation.

- Tracks the current topic across turns
- Resolves "it", "that", "him" to actual entities from previous turns
- Detects follow-up questions vs new topics
- Surfaces "you said X earlier" callbacks naturally
- Knows when Karthi changes subject
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FLOW_FILE = DATA_DIR / "conversation_flow.json"

# Maximum turns to track in active conversation
MAX_TURNS = 20
SESSION_TIMEOUT_MINUTES = 30


# ── State ────────────────────────────────────────────────────────────────────

def _load_flow() -> Dict[str, Any]:
    if FLOW_FILE.exists():
        try:
            return json.loads(FLOW_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.conversation_flow")
    return {
        "session_id": None,
        "session_started": None,
        "last_turn_at": None,
        "turns": [],
        "current_topic": None,
        "current_entities": {},  # type -> [names]
        "open_threads": [],      # unresolved questions/topics
    }


def _save_flow(flow: Dict[str, Any]):
    try:
        FLOW_FILE.write_text(json.dumps(flow, indent=2))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.conversation_flow")


def _is_session_active(flow: Dict[str, Any]) -> bool:
    last = flow.get("last_turn_at")
    if not last:
        return False
    try:
        last_dt = datetime.fromisoformat(last)
        return (datetime.now() - last_dt).total_seconds() < SESSION_TIMEOUT_MINUTES * 60
    except Exception:
        return False


def _new_session() -> Dict[str, Any]:
    sid = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "session_id": sid,
        "session_started": datetime.now().isoformat(),
        "last_turn_at": datetime.now().isoformat(),
        "turns": [],
        "current_topic": None,
        "current_entities": {},
        "open_threads": [],
    }


# ── Pronoun & reference resolution ──────────────────────────────────────────

PRONOUN_PATTERNS = {
    "he": "person", "she": "person", "him": "person", "her": "person",
    "his": "person", "they": "person", "them": "person", "their": "person",
    "it": "any", "that": "any", "this": "any", "those": "any", "these": "any",
}


def has_pronouns(text: str) -> bool:
    """Detect if text contains anaphoric pronouns."""
    words = re.findall(r"\b\w+\b", text.lower())
    return any(w in PRONOUN_PATTERNS for w in words)


def resolve_pronouns(text: str, flow: Dict[str, Any]) -> Dict[str, str]:
    """
    For each pronoun in text, suggest its likely referent.
    Returns dict of pronoun -> resolved entity.
    """
    if not has_pronouns(text):
        return {}

    resolutions = {}
    text_lower = text.lower()
    entities = flow.get("current_entities", {})

    # Find most recently mentioned person/project
    recent_person = None
    recent_project = None
    recent_any = None

    for turn in reversed(flow.get("turns", [])[-3:]):
        ents = turn.get("entities", {})
        for p in ents.get("person", []):
            recent_person = recent_person or p
        for p in ents.get("project", []):
            recent_project = recent_project or p
            recent_any = recent_any or p
        if not recent_any:
            for etype, names in ents.items():
                if names:
                    recent_any = names[0]
                    break

    for pronoun, ptype in PRONOUN_PATTERNS.items():
        if re.search(rf"\b{pronoun}\b", text_lower):
            if ptype == "person" and recent_person:
                resolutions[pronoun] = recent_person
            elif ptype == "any":
                resolutions[pronoun] = recent_project or recent_any or recent_person

    # Filter empty
    return {k: v for k, v in resolutions.items() if v}


# ── Topic detection ─────────────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "work": ["work", "job", "office", "boss", "colleague", "task", "project", "deadline", "meeting"],
    "coding": ["code", "bug", "function", "deploy", "git", "pull request", "PR", "commit", "debug"],
    "health": ["tired", "sleep", "gym", "workout", "exercise", "food", "ate", "headache", "energy"],
    "finance": ["money", "salary", "invest", "stock", "crypto", "expense", "budget", "saving"],
    "social": ["friend", "family", "brother", "sister", "mom", "dad", "called", "messaged"],
    "emotional": ["feel", "stressed", "happy", "sad", "anxious", "excited", "worried", "frustrated"],
    "planning": ["plan", "tomorrow", "next week", "weekend", "schedule", "todo", "want to"],
    "learning": ["learn", "study", "read", "book", "course", "tutorial", "video"],
}


def detect_topic(text: str) -> Optional[str]:
    text_lower = text.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for k in keywords if k in text_lower)
        if score > 0:
            scores[topic] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


def is_topic_continuation(prev_topic: str, new_text: str) -> bool:
    """Is the new turn continuing the previous topic?"""
    if not prev_topic:
        return False
    new_topic = detect_topic(new_text)
    return new_topic == prev_topic or new_topic is None  # No clear new topic = continuation


# ── Follow-up detection ─────────────────────────────────────────────────────

FOLLOWUP_PATTERNS = [
    r"^(?:and|but|so|also|then|what about|how about|why|how|when|where)\b",
    r"^(?:tell me more|more|explain|elaborate|continue|go on)",
    r"^(?:yes|yeah|yep|right|exactly|true)\b",
    r"^(?:no|nope|nah|wrong)\b",
]


def is_followup(text: str) -> bool:
    text_lower = text.lower().strip()
    return any(re.match(p, text_lower) for p in FOLLOWUP_PATTERNS) or len(text_lower.split()) <= 4


# ── Open thread tracking ─────────────────────────────────────────────────────

def _detect_open_thread(love_response: str) -> Optional[str]:
    """
    Did LOVE ask a question or leave something open in her response?
    Returns the open thread description or None.
    """
    # Question marks
    questions = re.findall(r'([^.!?]+\?)', love_response)
    if questions:
        return questions[-1].strip()

    # "Let me know"-style invitations
    if re.search(r"let me know|tell me|let\s*'?s\s*talk|want to|should we|shall we", love_response, re.IGNORECASE):
        return love_response[:100]

    return None


# ── Main API ────────────────────────────────────────────────────────────────

def record_turn(user_input: str, love_response: str, mode: str = "general") -> Dict[str, Any]:
    """Add a turn to the active conversation flow."""
    flow = _load_flow()

    if not _is_session_active(flow):
        flow = _new_session()

    # Extract entities
    try:
        from core.knowledge_graph import extract_entities
        entities = extract_entities(user_input)
    except Exception:
        entities = {}

    topic = detect_topic(user_input)
    is_fu = is_followup(user_input)

    turn = {
        "ts": datetime.now().isoformat(),
        "user": user_input,
        "love": love_response,
        "topic": topic,
        "is_followup": is_fu,
        "entities": entities,
        "mode": mode,
    }

    turns = flow.get("turns", [])
    turns.append(turn)
    flow["turns"] = turns[-MAX_TURNS:]

    # Update current state
    flow["last_turn_at"] = turn["ts"]
    if topic and not is_fu:
        flow["current_topic"] = topic

    # Merge entities
    cur_ents = flow.get("current_entities", {})
    for etype, names in entities.items():
        existing = cur_ents.get(etype, [])
        for n in names:
            if n not in existing:
                existing.append(n)
        cur_ents[etype] = existing[-10:]
    flow["current_entities"] = cur_ents

    # Track open threads from LOVE's response
    open_thread = _detect_open_thread(love_response)
    if open_thread:
        flow.setdefault("open_threads", []).append({
            "thread": open_thread,
            "ts": turn["ts"],
            "responded": False,
        })
        flow["open_threads"] = flow["open_threads"][-5:]
    else:
        # If user answered a previous open thread, mark resolved
        threads = flow.get("open_threads", [])
        if threads and not threads[-1]["responded"]:
            threads[-1]["responded"] = True

    _save_flow(flow)
    return turn


def get_flow_context(user_input: str) -> str:
    """
    Build a context string for the LLM prompt with conversation flow info.
    """
    flow = _load_flow()
    if not _is_session_active(flow):
        return ""

    lines = []
    turns = flow.get("turns", [])

    if turns:
        lines.append(f"CONVERSATION FLOW (session: {len(turns)} turns):")

        # Recent topic
        if flow.get("current_topic"):
            lines.append(f"  Active topic: {flow['current_topic']}")

        # Pronoun resolution
        resolutions = resolve_pronouns(user_input, flow)
        if resolutions:
            res_str = ", ".join(f"'{p}' = {ent}" for p, ent in resolutions.items())
            lines.append(f"  Pronoun refs: {res_str}")

        # Open threads
        open_threads = [t for t in flow.get("open_threads", []) if not t.get("responded")]
        if open_threads:
            lines.append(f"  Open thread from before: {open_threads[-1]['thread'][:100]}")

        # Recent context (last 2 turns)
        recent = turns[-2:]
        if len(recent) > 0:
            lines.append("  Recent exchange:")
            for t in recent:
                u = t["user"][:80]
                l = t["love"][:80]
                lines.append(f"    {u} → {l}")

        # Is this a follow-up?
        if is_followup(user_input):
            lines.append("  [This appears to be a follow-up — continue the previous thread.]")

    return "\n".join(lines)


def get_session_summary() -> Dict[str, Any]:
    """For dashboard."""
    flow = _load_flow()
    return {
        "active": _is_session_active(flow),
        "session_id": flow.get("session_id"),
        "started": flow.get("session_started"),
        "last_turn": flow.get("last_turn_at"),
        "turns_count": len(flow.get("turns", [])),
        "current_topic": flow.get("current_topic"),
        "current_entities": flow.get("current_entities", {}),
        "open_threads": flow.get("open_threads", []),
    }


def reset_session() -> Dict[str, Any]:
    """Force a new session."""
    flow = _new_session()
    _save_flow(flow)
    return {"reset": True, "session_id": flow["session_id"]}
