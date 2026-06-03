"""
LOVE Proactive Interruption Engine

Jarvis doesn't just answer questions — he INTERRUPTS when it matters.
But he knows WHEN to shut up.

This module decides:
- SHOULD I interrupt right now?
- WHAT channel? (TTS on PC, push notification on phone, both, or just log silently)
- WHAT do I say? (context-aware, brief, actionable)

It learns from Karthi's reactions:
- Ignored/dismissed → lower weight for that situation type
- Engaged/acted on → higher weight
- Explicit "don't bother me" → blacklist for N hours
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERRUPTION_LOG = DATA_DIR / "interruptions.jsonl"
RECEPTIVITY_FILE = DATA_DIR / "receptivity.json"
BLACKLIST_FILE = DATA_DIR / "interruption_blacklist.json"

# ── Configuration ────────────────────────────────────────────────────────────

DEFAULT_RULES = {
    "meeting_imminent":   {"urgency": 0.9, "min_score": 0.6, "cooldown_min": 5,  "channel": "both"},
    "battery_critical":   {"urgency": 0.85, "min_score": 0.5, "cooldown_min": 15, "channel": "tts"},
    "phone_battery_low":  {"urgency": 0.7, "min_score": 0.5, "cooldown_min": 20, "channel": "push"},
    "email_from_boss":    {"urgency": 0.8, "min_score": 0.7, "cooldown_min": 10, "channel": "both"},
    "missed_call":        {"urgency": 0.7, "min_score": 0.5, "cooldown_min": 5,  "channel": "push"},
    "calendar_conflict":  {"urgency": 0.85, "min_score": 0.6, "cooldown_min": 10, "channel": "both"},
    "long_focus_session": {"urgency": 0.4, "min_score": 0.75, "cooldown_min": 60, "channel": "tts"},
    "predicted_need":     {"urgency": 0.5, "min_score": 0.8, "cooldown_min": 30, "channel": "tts"},
    "system_alert":       {"urgency": 0.9, "min_score": 0.4, "cooldown_min": 5,  "channel": "both"},
    "stale_project":      {"urgency": 0.3, "min_score": 0.85, "cooldown_min": 240,"channel": "tts"},
    "news_digest_ready":  {"urgency": 0.2, "min_score": 0.9, "cooldown_min": 120,"channel": "tts"},
}

# ── State loading ─────────────────────────────────────────────────────────────

def _load_receptivity() -> Dict[str, Any]:
    if RECEPTIVITY_FILE.exists():
        try:
            return json.loads(RECEPTIVITY_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive")
    return {
        "global_score": 0.5,       # 0 = hates interruptions, 1 = loves them
        "by_type": {},              # situation_type -> {score, count}
        "by_hour": {},              # "9" -> score
        "last_interruption": None,
        "consecutive_ignored": 0,
    }


def _save_receptivity(r: Dict[str, Any]):
    try:
        RECEPTIVITY_FILE.write_text(json.dumps(r, indent=2))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.proactive")


def _load_blacklist() -> Dict[str, Any]:
    if BLACKLIST_FILE.exists():
        try:
            return json.loads(BLACKLIST_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive")
    return {"until": None, "types": [], "reason": ""}


def _save_blacklist(b: Dict[str, Any]):
    try:
        BLACKLIST_FILE.write_text(json.dumps(b, indent=2))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.proactive")


# ── Scoring ─────────────────────────────────────────────────────────────────

def _is_blacklisted(situation_type: str) -> bool:
    b = _load_blacklist()
    if b.get("until"):
        try:
            until = datetime.fromisoformat(b["until"])
            if datetime.now() < until:
                return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive")
    if situation_type in b.get("types", []):
        return True
    return False


def _time_since_last_interruption() -> float:
    r = _load_receptivity()
    last = r.get("last_interruption")
    if not last:
        return 9999
    try:
        return (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 60
    except Exception:
        return 9999


def _get_type_score(situation_type: str) -> float:
    r = _load_receptivity()
    t = r.get("by_type", {}).get(situation_type, {})
    if t.get("count", 0) < 3:
        return 0.5  # Neutral
    return t.get("score", 0.5)


def _get_hour_receptivity() -> float:
    r = _load_receptivity()
    hour = str(datetime.now().hour)
    return r.get("by_hour", {}).get(hour, 0.5)


def score_interruption(situation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score whether LOVE should interrupt for this situation.
    Returns: { should_interrupt, score, channel, reason, cooldown_remaining }
    """
    situation_type = situation.get("type", "unknown")
    urgency = situation.get("urgency", 0.5)

    # Check blacklist
    if _is_blacklisted(situation_type):
        return {"should_interrupt": False, "score": 0, "reason": "Blacklisted", "channel": "none"}

    # Get rule
    rule = DEFAULT_RULES.get(situation_type, {
        "urgency": urgency, "min_score": 0.7, "cooldown_min": 15, "channel": "tts"
    })

    # Time since last interruption
    mins_since = _time_since_last_interruption()
    cooldown_ok = mins_since >= rule["cooldown_min"]
    cooldown_remaining = max(0, rule["cooldown_min"] - mins_since)

    # Receptivity signals
    type_score = _get_type_score(situation_type)
    hour_score = _get_hour_receptivity()
    global_score = _load_receptivity().get("global_score", 0.5)

    # Consecutive ignored penalty
    ignored = _load_receptivity().get("consecutive_ignored", 0)
    ignored_penalty = min(ignored * 0.15, 0.5)

    # Compute final score
    raw_score = (
        urgency * 0.35 +
        type_score * 0.25 +
        hour_score * 0.15 +
        global_score * 0.15 -
        ignored_penalty * 0.10
    )

    # Normalize
    score = max(0.0, min(1.0, raw_score))

    should = score >= rule["min_score"] and cooldown_ok

    return {
        "should_interrupt": should,
        "score": round(score, 3),
        "urgency": urgency,
        "channel": rule["channel"] if should else "none",
        "reason": f"type={situation_type}, score={score:.2f}, min={rule['min_score']}, cooldown={cooldown_ok}",
        "cooldown_remaining_min": round(cooldown_remaining, 1),
        "situation_type": situation_type,
    }


# ── Action channels ────────────────────────────────────────────────────────

def _send_tts(text: str) -> bool:
    """Speak via TTS on the PC."""
    try:
        from voice.tts import speak_text, is_tts_available
        if is_tts_available():
            speak_text(text, block=False)
            return True
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.proactive")
    return False


def _send_push(title: str, body: str, data: dict = None) -> bool:
    """Send push notification to companion app via LOVE backend."""
    try:
        import requests
        from core.settings import get_settings
        settings = get_settings()
        port = getattr(settings, 'api_port', 8000)
        host = getattr(settings, 'api_host', '127.0.0.1')
        resp = requests.post(
            f"http://{host}:{port}/devices/push-send",
            json={"title": title, "body": body, "data": data or {}},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.proactive")
    return False


def deliver_interruption(text: str, channel: str, situation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deliver the interruption via the chosen channel.
    Returns delivery result and logs for learning.
    """
    results = {"tts": False, "push": False}

    if channel in ("tts", "both"):
        results["tts"] = _send_tts(text)

    if channel in ("push", "both"):
        # Use the situation title if available, else truncate
        title = situation.get("title", "LOVE")
        body = text[:200]
        results["push"] = _send_push(title, body)

    # Log
    entry = {
        "ts": datetime.now().isoformat(),
        "text": text,
        "channel": channel,
        "situation": situation,
        "delivered": results,
        "engaged": None,  # Will be updated when user responds
    }
    try:
        with open(INTERRUPTION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.proactive")

    # Update last interruption
    r = _load_receptivity()
    r["last_interruption"] = datetime.now().isoformat()
    _save_receptivity(r)

    return {
        "success": results["tts"] or results["push"],
        "tts": results["tts"],
        "push": results["push"],
        "text": text,
    }


# ── Learning from reactions ─────────────────────────────────────────────────

def record_reaction(interruption_ts: str, reaction: str) -> Dict[str, Any]:
    """
    Record how Karthi reacted to an interruption.
    reaction: "engaged" | "ignored" | "dismissed" | "annoyed" | "grateful"
    """
    r = _load_receptivity()

    # Find the interruption
    situation_type = None
    try:
        if INTERRUPTION_LOG.exists():
            lines = INTERRUPTION_LOG.read_text().strip().split("\n")
            for line in reversed(lines):
                entry = json.loads(line)
                if entry.get("ts") == interruption_ts:
                    situation_type = entry.get("situation", {}).get("type", "unknown")
                    break
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.proactive")

    if not situation_type:
        return {"error": "Interruption not found"}

    # Update type score
    t = r.setdefault("by_type", {}).setdefault(situation_type, {"score": 0.5, "count": 0})
    t["count"] += 1

    delta = {
        "engaged": 0.15,
        "grateful": 0.20,
        "ignored": -0.05,
        "dismissed": -0.15,
        "annoyed": -0.25,
    }.get(reaction, 0)

    t["score"] = max(0.0, min(1.0, t["score"] + delta))

    # Update hour score
    hour = str(datetime.now().hour)
    h = r.setdefault("by_hour", {}).setdefault(hour, 0.5)
    r["by_hour"][hour] = max(0.0, min(1.0, h + delta * 0.5))

    # Update global
    r["global_score"] = max(0.0, min(1.0, r.get("global_score", 0.5) + delta * 0.1))

    # Track consecutive ignored
    if reaction in ("ignored", "dismissed"):
        r["consecutive_ignored"] = r.get("consecutive_ignored", 0) + 1
    else:
        r["consecutive_ignored"] = 0

    _save_receptivity(r)

    return {
        "situation_type": situation_type,
        "reaction": reaction,
        "new_type_score": t["score"],
        "new_global_score": r["global_score"],
        "consecutive_ignored": r["consecutive_ignored"],
    }


def set_do_not_disturb(minutes: int = 60, reason: str = "") -> Dict[str, Any]:
    """Blacklist all interruptions for N minutes."""
    until = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    b = {"until": until, "types": [], "reason": reason or "user requested"}
    _save_blacklist(b)
    return {"dnd_until": until, "minutes": minutes, "reason": b["reason"]}


def clear_dnd() -> Dict[str, Any]:
    _save_blacklist({"until": None, "types": [], "reason": ""})
    return {"dnd_cleared": True}


# ── High-level: evaluate a situation and act ───────────────────────────────

def evaluate_and_act(situation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Full pipeline: score → decide → deliver.
    Returns delivery result or None if skipped.
    """
    scored = score_interruption(situation)
    if not scored["should_interrupt"]:
        return None

    # Compose message
    text = situation.get("message", situation.get("title", "Something needs your attention."))

    return deliver_interruption(text, scored["channel"], situation)


# ── Stats ──────────────────────────────────────────────────────────────────

def get_interruption_stats(n: int = 50) -> Dict[str, Any]:
    r = _load_receptivity()
    b = _load_blacklist()
    recent = []
    try:
        if INTERRUPTION_LOG.exists():
            lines = INTERRUPTION_LOG.read_text().strip().split("\n")
            for line in lines[-n:]:
                recent.append(json.loads(line))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.proactive")

    return {
        "global_receptivity": r.get("global_score", 0.5),
        "consecutive_ignored": r.get("consecutive_ignored", 0),
        "by_type": r.get("by_type", {}),
        "dnd": b.get("until"),
        "recent_interruptions": recent,
        "total_logged": len(recent),
    }
