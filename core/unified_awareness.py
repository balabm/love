"""
LOVE Unified Awareness Fusion

Combines ALL signals into a single "what matters RIGHT NOW" assessment:
- PC awareness (CPU, RAM, active window, running apps)
- Phone bridge (battery, location, missed calls, notifications)
- Office laptop (Teams, Outlook via MS Graph)
- Web intelligence (news, trends relevant to user)
- Recent notifications (WhatsApp, SMS, etc)
- File activity (recently modified files)
- User state (mood, energy, time of day, receptivity)

Produces a ranked list of "situations" LOVE should be aware of,
with scores for whether to interrupt, search, or act.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FUSION_LOG = DATA_DIR / "awareness_fusion.jsonl"


@dataclass
class Situation:
    source: str           # "pc", "phone", "office", "web", "notification", "file"
    category: str         # "meeting", "message", "alert", "trend", "work", "social"
    title: str
    body: str
    urgency: str          # "critical", "high", "medium", "low"
    relevance_score: float
    timestamp: datetime
    raw_data: Dict[str, Any]


def _load_json(path: Path) -> Optional[Dict]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return None


def _log_fusion(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(FUSION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _get_pc_snapshot() -> List[Situation]:
    """Pull from awareness engine."""
    situations = []
    try:
        from core.awareness import get_full_snapshot
        snap = get_full_snapshot()
        cpu = snap.get("cpu_percent", 0)
        ram = snap.get("ram_percent", 0)
        battery = snap.get("battery_percent", 100)
        active = snap.get("active_window", "")
        apps = snap.get("top_processes", [])

        if cpu > 90:
            situations.append(Situation(
                source="pc", category="alert", title="CPU Critical",
                body=f"CPU at {cpu}% — might be a build or a runaway process.",
                urgency="medium", relevance_score=0.5,
                timestamp=datetime.now(), raw_data=snap
            ))
        if ram > 90:
            situations.append(Situation(
                source="pc", category="alert", title="RAM Critical",
                body=f"RAM at {ram}% — could cause slowdowns.",
                urgency="medium", relevance_score=0.5,
                timestamp=datetime.now(), raw_data=snap
            ))
        if battery < 20 and battery > 0:
            situations.append(Situation(
                source="pc", category="alert", title="PC Battery Low",
                body=f"Laptop battery at {battery}% — consider plugging in.",
                urgency="high" if battery < 10 else "medium",
                relevance_score=0.7 if battery < 10 else 0.5,
                timestamp=datetime.now(), raw_data=snap
            ))
        if active:
            situations.append(Situation(
                source="pc", category="work", title="Active Window",
                body=f"Currently using: {active}",
                urgency="low", relevance_score=0.3,
                timestamp=datetime.now(), raw_data=snap
            ))
    except Exception:
        pass
    return situations


def _get_phone_state() -> List[Situation]:
    situations = []
    try:
        from integrations.phone_bridge import PhoneBridge
        bridge = PhoneBridge.get_instance()
        if not bridge.is_connected():
            return situations

        state = bridge.get_state()
        battery = state.get("battery", 100)
        missed = state.get("missed_calls", 0)
        unread = state.get("unread_messages", 0)
        location = state.get("location", "")

        if battery < 20:
            situations.append(Situation(
                source="phone", category="alert", title="Phone Battery Low",
                body=f"Phone at {battery}%",
                urgency="high" if battery < 10 else "medium",
                relevance_score=0.6, timestamp=datetime.now(), raw_data=state
            ))
        if missed > 0:
            situations.append(Situation(
                source="phone", category="social", title="Missed Calls",
                body=f"{missed} missed call{'s' if missed > 1 else ''}",
                urgency="medium", relevance_score=0.5,
                timestamp=datetime.now(), raw_data=state
            ))
        if unread > 0:
            situations.append(Situation(
                source="phone", category="social", title="Unread Messages",
                body=f"{unread} unread message{'s' if unread > 1 else ''}",
                urgency="low", relevance_score=0.4,
                timestamp=datetime.now(), raw_data=state
            ))
        if location:
            situations.append(Situation(
                source="phone", category="context", title="Phone Location",
                body=f"Phone is at: {location}",
                urgency="low", relevance_score=0.2,
                timestamp=datetime.now(), raw_data=state
            ))

        # Parse detailed phone notifications
        notifications = state.get("notifications", [])
        for notif in notifications:
            urgency = "low"
            if any(w in notif.lower() for w in ["urgent", "asap", "emergency", "important", "help"]):
                urgency = "critical"
            elif any(w in notif.lower() for w in ["call", "meeting", "join", "where", "now"]):
                urgency = "high"
            elif any(w in notif.lower() for w in ["whatsapp", "telegram", "sms", "messages", "signal"]):
                urgency = "medium"

            situations.append(Situation(
                source="phone", category="social", title="Phone Notification",
                body=notif,
                urgency=urgency,
                relevance_score=0.75 if urgency == "critical" else 0.55 if urgency == "high" else 0.45,
                timestamp=datetime.now(),
                raw_data={"notification": notif}
            ))
    except Exception:
        pass
    return situations


def _get_office_state() -> List[Situation]:
    situations = []
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge()
        if not ms.is_connected():
            return situations

        # Check calendar for upcoming meetings
        try:
            cal = ms.get_calendar()
            for event in cal.get("events", [])[:3]:
                start = event.get("start", "")
                # If meeting within 15 min
                situations.append(Situation(
                    source="office", category="meeting",
                    title=f"Meeting: {event.get('subject', 'Unknown')}",
                    body=f"Starts at {start}. {event.get('organizer', '')}",
                    urgency="high", relevance_score=0.8,
                    timestamp=datetime.now(), raw_data=event
                ))
        except Exception:
            pass

        # Check unread email details
        try:
            unread_emails = ms.get_unread_emails(limit=5)
            for em in unread_emails:
                urgency = "high" if em.get("important") else "medium"
                if any(w in em.get("subject", "").lower() or w in em.get("preview", "").lower() for w in ["urgent", "asap", "action required", "priority"]):
                    urgency = "critical"
                
                situations.append(Situation(
                    source="office", category="work", 
                    title=f"Email from {em.get('from', 'Unknown')}: {em.get('subject', '')}",
                    body=em.get("preview", ""),
                    urgency=urgency,
                    relevance_score=0.7 if urgency == "critical" else 0.5,
                    timestamp=datetime.now(),
                    raw_data=em
                ))
        except Exception:
            pass

        # Check Teams messages
        try:
            teams_msgs = ms.get_teams_messages(limit=5)
            for msg in teams_msgs:
                situations.append(Situation(
                    source="office", category="social",
                    title=f"Teams message from {msg.get('from', 'Someone')} ({msg.get('chat', 'Direct')})",
                    body=msg.get("text", ""),
                    urgency="medium",
                    relevance_score=0.45,
                    timestamp=datetime.now(),
                    raw_data=msg
                ))
        except Exception:
            pass
    except Exception:
        pass
    return situations


def _get_github_state() -> List[Situation]:
    situations = []
    try:
        from integrations.github_monitor import GitHubMonitor
        git = GitHubMonitor.get_instance()
        if not git.is_connected():
            return situations
        notifs = git.get_notifications(limit=5)
        for n in notifs:
            urgency = "high" if n.get("reason") in ("mention", "review_requested", "assign") else "medium"
            situations.append(Situation(
                source="web", category="work",
                title=f"GitHub {n.get('reason', 'notification')} in {n.get('repo', '')}",
                body=n.get("title", ""),
                urgency=urgency,
                relevance_score=0.6 if urgency == "high" else 0.4,
                timestamp=datetime.now(), raw_data=n
            ))
    except Exception:
        pass
    return situations


def _get_recent_notifications() -> List[Situation]:
    """Pull from notification log."""
    situations = []
    try:
        today = datetime.now().date()
        log_file = DATA_DIR / f"notif_log_{today}.jsonl"
        if not log_file.exists():
            return situations

        lines = log_file.read_text().strip().split("\n")
        for line in lines[-10:]:
            if not line:
                continue
            try:
                entry = json.loads(line)
                sender = entry.get("sender", "")
                channel = entry.get("channel", "")
                body = entry.get("raw_body", "")
                if not body:
                    continue

                # Skip low-value
                if channel in {"ads", "promo", "shopping"}:
                    continue

                urgency = "medium" if channel in {"teams", "whatsapp", "sms", "signal"} else "low"
                situations.append(Situation(
                    source="notification", category="social",
                    title=f"{channel}: {sender}" if sender else channel,
                    body=body[:100],
                    urgency=urgency, relevance_score=0.45,
                    timestamp=datetime.now(), raw_data=entry
                ))
            except Exception:
                pass
    except Exception:
        pass
    return situations


def _get_file_activity() -> List[Situation]:
    situations = []
    try:
        from core.file_inspector import scan_directory, get_watch_paths
        for path in get_watch_paths():
            files = scan_directory(path, max_depth=1, max_files=5)
            for f in files:
                if f.get("is_recent") and f.get("score", 0) >= 3:
                    situations.append(Situation(
                        source="file", category="work",
                        title=f"Active file: {f['name']}",
                        body=f"Modified recently. {f.get('content_hint', '')}",
                        urgency="low", relevance_score=0.35,
                        timestamp=datetime.now(), raw_data=f
                    ))
    except Exception:
        pass
    return situations


def _score_situation(s: Situation) -> float:
    """Compute final importance score for a situation."""
    score = s.relevance_score

    # Urgency multiplier
    urgency_mult = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.7}
    score *= urgency_mult.get(s.urgency, 1.0)

    # Time decay — older = less relevant (handled by caller filtering)
    # Source bonus for social/work during work hours
    hour = datetime.now().hour
    if s.category in {"meeting", "work"} and 9 <= hour <= 18:
        score *= 1.2
    if s.category == "social" and (hour < 9 or hour > 19):
        score *= 0.8  # Less relevant outside social hours

    return min(score, 1.0)


def fuse_all() -> Dict[str, Any]:
    """
    Main entry: gather all signals, score them, return ranked situations.
    """
    all_situations = []
    all_situations.extend(_get_pc_snapshot())
    all_situations.extend(_get_phone_state())
    all_situations.extend(_get_office_state())
    all_situations.extend(_get_recent_notifications())
    all_situations.extend(_get_file_activity())
    all_situations.extend(_get_github_state())

    # Score and sort
    scored = []
    for s in all_situations:
        final_score = _score_situation(s)
        scored.append((final_score, s))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Convert to serializable
    results = []
    for score, s in scored:
        results.append({
            "score": round(score, 3),
            "source": s.source,
            "category": s.category,
            "title": s.title,
            "body": s.body,
            "urgency": s.urgency,
            "timestamp": s.timestamp.isoformat(),
        })

    # Top situation — what matters most right now
    top = results[0] if results else None

    summary = {
        "timestamp": datetime.now().isoformat(),
        "situation_count": len(results),
        "top_situation": top,
        "all_situations": results[:15],
        "sources": {},
    }

    for r in results:
        src = r["source"]
        summary["sources"][src] = summary["sources"].get(src, 0) + 1

    _log_fusion(summary)
    return summary


def what_should_love_do_now() -> Optional[Dict[str, Any]]:
    """
    The key function: fuse everything, then decide the single most important action.
    Returns: { action, reason, situation } or None if nothing important.
    """
    fusion = fuse_all()
    top = fusion.get("top_situation")
    if not top:
        return None

    score = top.get("score", 0)
    if score < 0.4:
        return None

    # Use decision engine
    try:
        from core.decisions import should_interrupt
        should, reason = should_interrupt(
            urgency=top.get("urgency", "low"),
            channel=top.get("source", ""),
            sender="",
            user_focus_mode=top.get("category") == "work" and top.get("source") == "pc",
        )

        if not should:
            return None

        return {
            "action": "notify_user",
            "reason": reason,
            "situation": top,
            "message": _format_proactive_message(top),
        }

    except Exception:
        # Fallback: direct notify if score high enough
        if score < 0.6:
            return None
        return {
            "action": "notify_user",
            "reason": f"High relevance score: {score}",
            "situation": top,
            "message": _format_proactive_message(top),
        }


def _format_proactive_message(top: Dict[str, Any]) -> str:
    """Format the top situation into a natural proactive message."""
    category = top.get("category", "")
    title = top.get("title", "")
    body = top.get("body", "")
    source = top.get("source", "")

    if category == "alert":
        return f"Heads up — {title}. {body}"
    if category == "meeting":
        return f"You have {title} coming up. {body}"
    if category == "social":
        return f"{title}: {body}"
    if category == "work":
        return f"I noticed {title}. {body}"
    if source == "web":
        return f"Saw something relevant: {title}. {body}"

    return f"{title}. {body}"
