"""
LOVE Executive Assistant

Jarvis doesn't just chat — he PREPS, REMINDS, and HANDLES.

- Before a meeting: pulls relevant emails, calendar context, notes
- During conversation: extracts action items, creates tasks
- After meetings: drafts follow-up emails, sets reminders
- Daily: briefs Karthi on what matters today
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TASKS_FILE = DATA_DIR / "tasks.json"
REMINDERS_FILE = DATA_DIR / "reminders.jsonl"
BRIEF_LOG = DATA_DIR / "briefs.jsonl"


def _load_tasks() -> List[Dict[str, Any]]:
    if TASKS_FILE.exists():
        try:
            return json.loads(TASKS_FILE.read_text())
        except Exception:
            pass
    return []


def _save_tasks(tasks: List[Dict[str, Any]]):
    try:
        TASKS_FILE.write_text(json.dumps(tasks, indent=2))
    except Exception:
        pass


def _log_reminder(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(REMINDERS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ── Meeting Prep ──────────────────────────────────────────────────────────

def prep_for_meeting(subject: str, start_time: str = None) -> Dict[str, Any]:
    """
    Gather everything Karthi needs before a meeting.
    Returns: context summary + suggested talking points.
    """
    context_parts = []

    # 1. Calendar context
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge()
        calendar = ms.get_calendar()
        if calendar and not isinstance(calendar, dict) or calendar.get("events"):
            events = calendar.get("events", []) if isinstance(calendar, dict) else []
            for e in events[:3]:
                if subject.lower() in e.get("subject", "").lower():
                    context_parts.append(f"📅 This meeting: {e.get('subject')} at {e.get('start')}")
                    if e.get("attendees"):
                        names = [a.get("name", "") for a in e["attendees"]]
                        context_parts.append(f"   Attendees: {', '.join(names)}")
                    break
    except Exception:
        pass

    # 2. Recent emails related to meeting
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge()
        emails = ms.get_email(count=10)
        related = []
        for em in emails:
            body = (em.get("subject", "") + " " + em.get("body_preview", "")).lower()
            if any(w in body for w in subject.lower().split()):
                related.append(f"📧 {em.get('subject')} from {em.get('from', {}).get('name', '?')}")
        if related:
            context_parts.append("Related emails:")
            context_parts.extend(related[:5])
    except Exception:
        pass

    # 3. Knowledge graph — who are these people?
    try:
        from core.knowledge_graph import find_entities, get_relations
        # Extract potential names from subject
        words = subject.split()
        for w in words:
            if len(w) > 3 and w[0].isupper():
                people = find_entities(w, etype="person", limit=2)
                for p in people:
                    rels = get_relations(p["name"], "person", direction="both", limit=5)
                    if rels:
                        context_parts.append(f"👤 {p['name']}: {len(rels)} known connections")
    except Exception:
        pass

    # 4. Recent project work
    try:
        from core.doc_analyst import inspect_and_ask
        docs = inspect_and_ask()
        if docs:
            context_parts.append("📁 Active project files:")
            for d in docs.get("files", [])[:3]:
                context_parts.append(f"   {d.get('name', 'file')}")
    except Exception:
        pass

    summary = "\n".join(context_parts) if context_parts else "No context found."

    return {
        "meeting": subject,
        "prep_summary": summary,
        "talking_points": context_parts[:8],
        "timestamp": datetime.now().isoformat(),
    }


# ── Task Extraction ─────────────────────────────────────────────────────────

TASK_PATTERNS = [
    r"(?:need to|should|must|have to|going to)\s+(.+?)(?:\.|$|\,)",
    r"(?:remind me to|don't forget to)\s+(.+?)(?:\.|$|\,)",
    r"(?:create a task|add a task|make a note)\s*:?\s*(.+?)(?:\.|$)",
    r"(?:by)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week|end of day|eod| cob)",
]


def extract_tasks(text: str) -> List[Dict[str, Any]]:
    """Pull actionable items from a conversation."""
    tasks = []
    text_lower = text.lower()

    for pattern in TASK_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            task_text = m.group(1).strip() if m.groups() else m.group(0).strip()
            if len(task_text) < 5:
                continue

            # Determine deadline from context
            deadline = None
            dl_patterns = {
                "tomorrow": lambda: (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "monday": lambda: _next_weekday(0),
                "tuesday": lambda: _next_weekday(1),
                "wednesday": lambda: _next_weekday(2),
                "thursday": lambda: _next_weekday(3),
                "friday": lambda: _next_weekday(4),
                "end of day": lambda: datetime.now().strftime("%Y-%m-%d"),
                "eod": lambda: datetime.now().strftime("%Y-%m-%d"),
                "cob": lambda: datetime.now().strftime("%Y-%m-%d"),
            }
            for keyword, fn in dl_patterns.items():
                if keyword in text_lower:
                    try:
                        deadline = fn()
                    except Exception:
                        pass
                    break

            tasks.append({
                "text": task_text,
                "deadline": deadline,
                "created": datetime.now().isoformat(),
                "source": "conversation",
                "done": False,
            })

    return tasks


def _next_weekday(target_weekday: int) -> str:
    """target_weekday: 0=Mon, 6=Sun"""
    today = datetime.now()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def add_task(text: str, deadline: str = None, source: str = "manual") -> Dict[str, Any]:
    """Add a task and save."""
    tasks = _load_tasks()
    task = {
        "id": len(tasks) + 1,
        "text": text,
        "deadline": deadline,
        "created": datetime.now().isoformat(),
        "source": source,
        "done": False,
    }
    tasks.append(task)
    _save_tasks(tasks)
    _log_reminder({"event": "task_created", "task": task})
    return task


def complete_task(task_id: int) -> Dict[str, Any]:
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            t["completed_at"] = datetime.now().isoformat()
            _save_tasks(tasks)
            return {"success": True, "task": t}
    return {"success": False, "error": "Task not found"}


def get_tasks(filter: str = "active") -> List[Dict[str, Any]]:
    tasks = _load_tasks()
    if filter == "active":
        return [t for t in tasks if not t.get("done")]
    if filter == "today":
        today = datetime.now().strftime("%Y-%m-%d")
        return [t for t in tasks if not t.get("done") and t.get("deadline") == today]
    if filter == "overdue":
        today = datetime.now().strftime("%Y-%m-%d")
        return [t for t in tasks if not t.get("done") and t.get("deadline") and t["deadline"] < today]
    return tasks


# ── Follow-up Email Drafting ────────────────────────────────────────────────

def draft_follow_up(meeting_subject: str, key_points: List[str] = None,
                      action_items: List[str] = None, recipient: str = None) -> str:
    """
    Draft a follow-up email after a meeting.
    """
    points = key_points or []
    actions = action_items or []

    lines = [
        f"Hi {recipient or 'team'},",
        "",
        f"Thanks for the time today. Quick summary from our discussion on {meeting_subject}:",
        "",
    ]
    for p in points:
        lines.append(f"  • {p}")
    lines.append("")

    if actions:
        lines.append("Next steps:")
        for a in actions:
            lines.append(f"  • {a}")
        lines.append("")

    lines.append("Let me know if I missed anything.")
    lines.append("")
    lines.append("Best,")
    lines.append("Karthi")

    return "\n".join(lines)


# ── Daily Brief ─────────────────────────────────────────────────────────────

def generate_daily_brief() -> Dict[str, Any]:
    """
    LOVE's morning briefing for Karthi.
    Combines: calendar, tasks, emails, health, predictions.
    """
    sections = []

    # Calendar
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge()
        cal = ms.get_calendar()
        if cal and isinstance(cal, dict) and cal.get("events"):
            today_events = [e for e in cal["events"]
                              if e.get("start", "").startswith(datetime.now().strftime("%Y-%m-%d"))]
            if today_events:
                sections.append(f"📅 {len(today_events)} meeting(s) today")
                for e in today_events[:3]:
                    sections.append(f"   {e.get('start', '')[11:16]} — {e.get('subject', 'No title')}")
    except Exception:
        pass

    # Tasks
    tasks_today = get_tasks("today")
    tasks_overdue = get_tasks("overdue")
    if tasks_today:
        sections.append(f"✅ {len(tasks_today)} task(s) due today")
    if tasks_overdue:
        sections.append(f"⚠ {len(tasks_overdue)} overdue task(s)")

    # Emails
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge()
        emails = ms.get_email(count=5)
        if emails:
            sections.append(f"📧 {len(emails)} recent email(s)")
    except Exception:
        pass

    # Predictions
    try:
        from core.predictive import predict_next_need
        pred = predict_next_need()
        if pred:
            sections.append(f"🔮 {pred['prediction']} — {pred['suggested_action']}")
    except Exception:
        pass

    # Health / system
    try:
        from core.awareness import get_full_snapshot
        snap = get_full_snapshot()
        if snap.get("battery_percent", 100) < 30:
            sections.append(f"🔋 PC battery at {snap['battery_percent']}%")
    except Exception:
        pass

    brief = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sections": sections,
        "summary": " | ".join(sections[:4]) if sections else "Quiet day ahead.",
    }

    try:
        with open(BRIEF_LOG, "a") as f:
            f.write(json.dumps(brief) + "\n")
    except Exception:
        pass

    return brief


# ── Reminder Scheduler ─────────────────────────────────────────────────────

def set_reminder(text: str, trigger_at: str) -> Dict[str, Any]:
    """
    trigger_at: ISO datetime string or relative like "+30m", "+2h", "tomorrow 9am"
    """
    now = datetime.now()
    if trigger_at.startswith("+"):
        unit = trigger_at[-1]
        val = int(trigger_at[1:-1])
        if unit == "m":
            trigger_dt = now + timedelta(minutes=val)
        elif unit == "h":
            trigger_dt = now + timedelta(hours=val)
        elif unit == "d":
            trigger_dt = now + timedelta(days=val)
        else:
            return {"error": f"Unknown time unit: {unit}"}
    elif trigger_at.lower() == "tomorrow":
        trigger_dt = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
    else:
        try:
            trigger_dt = datetime.fromisoformat(trigger_at)
        except Exception:
            return {"error": f"Cannot parse time: {trigger_at}"}

    entry = {
        "text": text,
        "trigger_at": trigger_dt.isoformat(),
        "created": now.isoformat(),
        "delivered": False,
    }
    _log_reminder(entry)
    return {"success": True, "reminder": entry}


def check_due_reminders() -> List[Dict[str, Any]]:
    """Get reminders that are now due."""
    due = []
    try:
        if not REMINDERS_FILE.exists():
            return []
        lines = REMINDERS_FILE.read_text().strip().split("\n")
        now = datetime.now()
        for line in lines:
            entry = json.loads(line)
            if not entry.get("delivered"):
                try:
                    trigger = datetime.fromisoformat(entry["trigger_at"])
                    if trigger <= now:
                        due.append(entry)
                except Exception:
                    pass
    except Exception:
        pass
    return due
