"""
LOVE Context Engine - The Master Situational Awareness Fuser
Combines: system awareness + google calendar + phone + docs + life agents
into a single rich context object that LOVE always knows about.
This is what makes LOVE proactive — it always knows what's happening.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from threading import Lock, Thread
from dataclasses import dataclass, field, asdict

DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class LiveContext:
    """
    The complete picture of what's happening RIGHT NOW.
    LOVE always has this — no need to ask.
    """
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # ── Environment ──
    active_app: str = ""
    active_window: str = ""
    activity: str = ""           # coding / browsing / communicating / idle
    time_of_day: str = ""        # morning / afternoon / evening / night
    day_type: str = ""           # weekday / weekend
    local_time: str = ""
    system_cpu: float = 0.0
    system_ram: float = 0.0
    battery: Optional[float] = None
    battery_charging: Optional[bool] = None
    network_up: bool = True

    # ── Calendar & Schedule ──
    next_event: Optional[Dict] = None
    events_today: List[Dict] = field(default_factory=list)
    is_in_meeting: bool = False
    free_until: Optional[str] = None

    # ── Gmail ──
    unread_important: int = 0
    urgent_emails: List[Dict] = field(default_factory=list)

    # ── Phone / Mobile ──
    phone_connected: bool = False
    phone_battery: Optional[float] = None
    phone_location: Optional[str] = None
    missed_calls: int = 0
    unread_messages: int = 0
    phone_notifications: List[Dict] = field(default_factory=list)

    # ── Documents & Code ──
    recent_files: List[Dict] = field(default_factory=list)
    active_project: Optional[str] = None
    doc_insights: List[str] = field(default_factory=list)

    # ── Life Agents State ──
    mood_score: Optional[float] = None
    energy_score: Optional[float] = None
    stress_score: Optional[float] = None
    hours_worked_today: float = 0.0
    work_limit_hours: float = 9.0
    tasks_overdue: int = 0
    tasks_due_today: int = 0
    fitness_streak: int = 0
    learning_streak: int = 0

    # ── LOVE Insights ──
    proactive_alerts: List[str] = field(default_factory=list)
    suggested_action: Optional[str] = None
    context_summary: str = ""

    @property
    def stress_level(self):
        return self.stress_score if self.stress_score is not None else 0.0
        
    @property
    def energy_level(self):
        return self.energy_score if self.energy_score is not None else 0.0
        
    @property
    def pc_battery(self):
        return self.battery

    @property
    def cpu_percent(self):
        return self.system_cpu

class ContextEngine:
    """
    Master context fusion engine.
    Pulls from all sources and maintains a live LiveContext object.
    Heartbeat and agent.py both read from this.
    """

    def __init__(self):
        self._lock = Lock()
        self._ctx = LiveContext()
        self._running = False
        self._thread: Optional[Thread] = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def start(self, interval_seconds: int = 60):
        if self._running:
            return
        self._running = True
        # Defer initial scan to background -- avoids blocking startup
        self._thread = Thread(target=self._loop, args=(interval_seconds,), daemon=True)
        self._thread.start()
        print(f"[ContextEngine] Live context engine started ({interval_seconds}s refresh)")

    def stop(self):
        self._running = False

    def get(self) -> LiveContext:
        with self._lock:
            return self._ctx

    def get_dict(self) -> Dict[str, Any]:
        with self._lock:
            return asdict(self._ctx)

    def get_prompt_context(self) -> str:
        """
        Returns RICH context with actual data — email subjects, calendar details,
        task names, file activity. This is what makes LOVE truly aware.
        """
        ctx = self.get()
        lines = []

        # Time & environment
        lines.append(f"[NOW] {ctx.local_time} | {ctx.day_type} {ctx.time_of_day}")
        if ctx.active_window:
            lines.append(f"[SCREEN] {ctx.active_app} — \"{ctx.active_window[:100]}\"")
        if ctx.activity and ctx.activity != "idle":
            lines.append(f"[ACTIVITY] {ctx.activity}")

        # System health
        if ctx.battery is not None:
            status = "charging" if ctx.battery_charging else "draining"
            lines.append(f"[PC] Battery {ctx.battery:.0f}% ({status}) | CPU {ctx.system_cpu:.0f}% | RAM {ctx.system_ram:.0f}%")
        elif ctx.system_cpu > 0:
            lines.append(f"[PC] CPU {ctx.system_cpu:.0f}% | RAM {ctx.system_ram:.0f}%")

        # Calendar — ACTUAL EVENT DETAILS
        if ctx.is_in_meeting:
            lines.append("[CALENDAR] Currently in a meeting")
        if ctx.events_today:
            lines.append(f"[CALENDAR] Today's schedule ({len(ctx.events_today)} events):")
            for ev in ctx.events_today[:8]:
                loc = f" @ {ev.get('location')}" if ev.get("location") else ""
                att = f" ({ev.get('attendees', 0)} people)" if ev.get("attendees", 0) > 1 else ""
                lines.append(f"  • {ev.get('start_str', '?')} – {ev.get('end_str', '?')}: {ev.get('title', 'Untitled')}{loc}{att}")
        elif ctx.next_event:
            ev = ctx.next_event
            lines.append(f"[CALENDAR] Next: \"{ev.get('title', '')}\" at {ev.get('time', '')} ({ev.get('minutes_away', '?')} min away)")

        # Email — ACTUAL SUBJECTS AND SENDERS
        if ctx.unread_important > 0:
            lines.append(f"[EMAIL] {ctx.unread_important} important unread:")
            for em in ctx.urgent_emails[:5]:
                sender = em.get("from", "Unknown")
                # Extract just the name from "Name <email>" format
                if "<" in sender:
                    sender = sender.split("<")[0].strip().strip('"')
                subj = em.get("subject", "(no subject)")
                snippet = em.get("snippet", "")[:80]
                lines.append(f"  • From {sender}: \"{subj}\"")
                if snippet:
                    lines.append(f"    Preview: {snippet}")

        # Tasks — ACTUAL TASK NAMES
        task_detail = self._get_task_details()
        if task_detail:
            lines.append(task_detail)

        # Phone
        if ctx.phone_connected:
            phone_parts = ["[PHONE] Connected"]
            if ctx.phone_battery is not None:
                phone_parts.append(f"battery {ctx.phone_battery:.0f}%")
            if ctx.phone_location:
                phone_parts.append(f"at {ctx.phone_location}")
            lines.append(" | ".join(phone_parts))
            if ctx.missed_calls > 0:
                lines.append(f"  {ctx.missed_calls} missed call(s)")
            if ctx.unread_messages > 0:
                lines.append(f"  {ctx.unread_messages} unread message(s)")

        # Life state
        if ctx.mood_score is not None:
            lines.append(f"[WELLNESS] Mood {ctx.mood_score:.1f}/10 | Energy {ctx.energy_score:.1f}/10 | Stress {ctx.stress_score:.1f}/10")
        if ctx.hours_worked_today > 0:
            remaining = ctx.work_limit_hours - ctx.hours_worked_today
            lines.append(f"[WORK] {ctx.hours_worked_today:.1f}h worked / {ctx.work_limit_hours}h limit ({max(0, remaining):.1f}h left)")

        # Streaks
        streaks = []
        if ctx.fitness_streak > 0:
            streaks.append(f"Fitness {ctx.fitness_streak}d")
        if ctx.learning_streak > 0:
            streaks.append(f"Learning {ctx.learning_streak}d")
        if streaks:
            lines.append(f"[STREAKS] {' | '.join(streaks)}")

        # Recent file activity
        if ctx.recent_files:
            names = [f.get("name", "") for f in ctx.recent_files[:5] if f.get("name")]
            if names:
                lines.append(f"[FILES] Recently touched: {', '.join(names)}")

        # Active project
        if ctx.active_project:
            lines.append(f"[PROJECT] Working on: {ctx.active_project}")

        # Doc insights
        for insight in ctx.doc_insights[:3]:
            lines.append(f"[DOC] {insight}")

        # Proactive alerts
        if ctx.proactive_alerts:
            lines.append("[ALERTS]")
            for alert in ctx.proactive_alerts[:5]:
                lines.append(f"  ⚠ {alert}")

        return "\n".join(lines)

    def _get_task_details(self) -> str:
        """Pull actual task names/titles for the prompt."""
        try:
            from agents.task_agent import get_task_overview
            overview = get_task_overview()
            parts = []
            due_soon = overview.get("due_soon", [])
            stuck = overview.get("stuck_tasks", [])
            active_count = overview.get("active_count", 0)

            if active_count > 0:
                parts.append(f"[TASKS] {active_count} active")
            if due_soon:
                parts.append(f" | {len(due_soon)} due soon:")
                for t in due_soon[:5]:
                    due = ""
                    if t.get("due_date"):
                        due = f" (due {t['due_date'][:10]})"
                    parts.append(f"\n  • {t.get('title', 'Untitled')}{due}")
            if stuck:
                parts.append(f"\n  Stuck: {', '.join(t.get('title', '?') for t in stuck[:3])}")
            suggestion = overview.get("suggestion", "")
            if suggestion:
                parts.append(f"\n  Suggested focus: {suggestion}")
            return "".join(parts) if parts else ""
        except Exception:
            return ""

    # ──────────────────────────────────────────────
    # INTERNAL LOOP
    # ──────────────────────────────────────────────

    def _loop(self, interval: int):
        while self._running:
            time.sleep(interval)
            try:
                self._refresh()
            except Exception as e:
                print(f"[ContextEngine] Refresh error: {e}")

    def _refresh(self):
        ctx = LiveContext()

        self._pull_awareness(ctx)
        self._pull_calendar(ctx)
        self._pull_gmail(ctx)
        self._pull_phone(ctx)
        self._pull_life_agents(ctx)
        self._pull_docs(ctx)
        self._compute_alerts(ctx)
        ctx.context_summary = self._build_summary(ctx)
        ctx.timestamp = datetime.now().isoformat()

        with self._lock:
            self._ctx = ctx

        self._persist(ctx)

    # ──────────────────────────────────────────────
    # SOURCE PULLERS
    # ──────────────────────────────────────────────

    def _pull_awareness(self, ctx: LiveContext):
        try:
            from core.awareness import get_full_snapshot
            snap = get_full_snapshot()
            system = snap.get("system", {})
            context = snap.get("context", {})
            files = snap.get("files", {})

            ctx.active_app = context.get("active_app", "")
            ctx.active_window = context.get("active_window", "")
            ctx.activity = context.get("dev_activity", "")
            ctx.time_of_day = context.get("time_of_day", "")
            ctx.local_time = context.get("local_time", datetime.now().strftime("%I:%M %p"))
            ctx.day_type = "weekend" if context.get("is_weekend") else "weekday"
            ctx.system_cpu = system.get("cpu_percent", 0.0)
            ctx.system_ram = system.get("ram_percent", 0.0)
            ctx.battery = system.get("battery_percent")
            ctx.battery_charging = system.get("battery_plugged")
            ctx.network_up = system.get("network_connected", True)
            ctx.recent_files = files.get("recently_modified", [])
        except Exception:
            ctx.local_time = datetime.now().strftime("%I:%M %p")
            now = datetime.now()
            hour = now.hour
            ctx.time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening" if hour < 21 else "night"
            ctx.day_type = "weekend" if now.weekday() >= 5 else "weekday"

    def _pull_calendar(self, ctx: LiveContext):
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            if not gs.is_connected():
                return
            events = gs.get_todays_events()
            ctx.events_today = events
            now = datetime.now()
            upcoming = [
                e for e in events
                if e.get("start_dt") and e["start_dt"] > now
            ]
            if upcoming:
                nxt = upcoming[0]
                ctx.next_event = {
                    "title": nxt.get("title", ""),
                    "time": nxt.get("start_str", ""),
                    "location": nxt.get("location", ""),
                    "minutes_away": nxt.get("minutes_away", 0)
                }
            # Check if currently in a meeting
            active = [
                e for e in events
                if e.get("start_dt") and e.get("end_dt")
                and e["start_dt"] <= now <= e["end_dt"]
            ]
            ctx.is_in_meeting = len(active) > 0
            
            # Calculate free time until next event
            if upcoming and not ctx.is_in_meeting:
                ctx.free_until = upcoming[0].get("start_str", "")
            elif not upcoming:
                ctx.free_until = None
        except Exception as e:
            print(f"[ContextEngine] Calendar pull error: {e}")

    def _pull_gmail(self, ctx: LiveContext):
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            if not gs.is_connected():
                return
            summary = gs.get_email_summary()
            ctx.unread_important = summary.get("unread_important", 0)
            ctx.urgent_emails = summary.get("urgent", [])
            
            # Add email backlog alert if significant
            if ctx.unread_important > 20:
                ctx.proactive_alerts.append(f"{ctx.unread_important} unread important emails - consider triage")
        except Exception as e:
            print(f"[ContextEngine] Gmail pull error: {e}")

    def _pull_phone(self, ctx: LiveContext):
        try:
            from integrations.phone_bridge import PhoneBridge
            bridge = PhoneBridge.get_instance()
            if not bridge.is_connected():
                return
            state = bridge.get_state()
            ctx.phone_connected = True
            ctx.phone_battery = state.get("battery")
            ctx.phone_location = state.get("location_label")
            ctx.missed_calls = state.get("missed_calls", 0)
            ctx.unread_messages = state.get("unread_messages", 0)
            ctx.phone_notifications = state.get("notifications", [])
        except Exception:
            pass

    def _pull_life_agents(self, ctx: LiveContext):
        try:
            from agents.emotional_agent import get_emotional_insights
            wellness = get_emotional_insights(days=1)
            if isinstance(wellness, dict):
                ctx.mood_score = wellness.get("avg_mood")
                ctx.energy_score = wellness.get("avg_energy")
                ctx.stress_score = wellness.get("avg_stress")
        except Exception:
            pass

        try:
            from tools.guardian import check_work_status
            from core.settings import get_settings
            status = check_work_status()
            ctx.hours_worked_today = status.get("hours_today", 0.0)
            ctx.work_limit_hours = get_settings().work.daily_limit_hours
        except Exception:
            pass

        try:
            from agents.task_agent import get_task_overview
            overview = get_task_overview()
            due_soon = overview.get("due_soon", [])
            ctx.tasks_due_today = len(due_soon)
            ctx.tasks_overdue = overview.get("overdue_count", 0)
        except Exception:
            pass

        try:
            from agents.fitness_agent import get_fitness_status
            fit = get_fitness_status()
            ctx.fitness_streak = fit.get("streak", 0)
        except Exception:
            pass

        try:
            from agents.learning_agent import get_learning_progress
            learn = get_learning_progress()
            ctx.learning_streak = learn.get("current_streak", 0)
        except Exception:
            pass

    def _pull_docs(self, ctx: LiveContext):
        try:
            from core.doc_analyst import get_analyst
            analyst = get_analyst()
            insights = analyst.get_recent_insights()
            ctx.doc_insights = insights
            ctx.active_project = analyst.get_active_project()
            
            # Also pull recent file changes for context
            summary = analyst.get_project_summary()
            if summary:
                recent_changes = summary.get("recent_changes", [])
                if recent_changes:
                    ctx.recent_files = recent_changes[:10]
        except Exception as e:
            print(f"[ContextEngine] Doc pull error: {e}")

    def _compute_alerts(self, ctx: LiveContext):
        alerts = []

        # Battery critical
        if ctx.battery is not None and ctx.battery < 15 and not ctx.battery_charging:
            alerts.append(f"Battery at {ctx.battery:.0f}% — plug in now")

        # Battery + meeting combo (high priority)
        if ctx.next_event and ctx.battery is not None:
            mins = ctx.next_event.get("minutes_away", 999)
            if 0 < mins <= 30 and ctx.battery < 30 and not ctx.battery_charging:
                alerts.append(f"Meeting in {mins}min with {ctx.battery:.0f}% battery — plug in now")

        # Meeting soon
        if ctx.next_event and ctx.next_event.get("minutes_away", 999) <= 10:
            alerts.append(f"Meeting in {ctx.next_event['minutes_away']} min: {ctx.next_event['title']}")

        # Work limit approaching
        remaining = ctx.work_limit_hours - ctx.hours_worked_today
        if 0 < remaining <= 0.5:
            alerts.append(f"Work limit in {int(remaining * 60)} minutes")
        elif ctx.hours_worked_today >= ctx.work_limit_hours:
            alerts.append("Work limit reached — time to stop")

        # Overdue tasks
        if ctx.tasks_overdue > 0:
            alerts.append(f"{ctx.tasks_overdue} task(s) overdue")

        # Tasks due today (if many)
        if ctx.tasks_due_today > 5:
            alerts.append(f"{ctx.tasks_due_today} tasks due today — prioritize")

        # Important emails
        if ctx.unread_important >= 3:
            alerts.append(f"{ctx.unread_important} important emails unread")
        elif ctx.unread_important >= 10:
            alerts.append(f"{ctx.unread_important} unread emails — consider triage")

        # Phone
        if ctx.missed_calls > 0:
            alerts.append(f"{ctx.missed_calls} missed call(s) on phone")
        if ctx.unread_messages > 0:
            alerts.append(f"{ctx.unread_messages} unread message(s) on phone")

        # Phone battery low
        if ctx.phone_connected and ctx.phone_battery and ctx.phone_battery < 20:
            alerts.append(f"Phone battery at {ctx.phone_battery:.0f}%")

        # Fitness streak broken
        if ctx.fitness_streak == 0 and ctx.day_type == "weekday":
            alerts.append("No workouts this week — consider movement")

        # High stress detected
        if ctx.stress_score and ctx.stress_score > 7:
            alerts.append("High stress detected — consider a break")

        # Deep work session (opportunity for focus protection)
        if ctx.activity == "working" and ctx.hours_worked_today > 2 and not ctx.is_in_meeting:
            alerts.append("Deep work session in progress — protect focus time")

        # Free time available (opportunity)
        if ctx.free_until and ctx.tasks_due_today == 0:
            alerts.append(f"Free until {ctx.free_until} — good time for deep work or break")

        # Late night working
        if ctx.time_of_day == "night" and ctx.activity == "working":
            alerts.append("Late night work — consider wrapping up")

        # Sort alerts by priority (critical first)
        priority_keywords = ["battery", "meeting", "limit", "overdue", "stress", "missed"]
        alerts.sort(key=lambda a: any(kw in a.lower() for kw in priority_keywords), reverse=True)

        ctx.proactive_alerts = alerts[:10]  # Keep top 10

        # Single most important suggested action (highest priority)
        if alerts:
            ctx.suggested_action = alerts[0]

    def _build_summary(self, ctx: LiveContext) -> str:
        parts = [
            f"It's {ctx.local_time} on a {ctx.day_type} {ctx.time_of_day}.",
        ]
        if ctx.activity and ctx.activity != "idle":
            parts.append(f"User appears to be {ctx.activity.replace('_', ' ')}.")
        if ctx.is_in_meeting:
            parts.append("Currently in a meeting.")
        if ctx.proactive_alerts:
            parts.append("Active alerts: " + "; ".join(ctx.proactive_alerts[:3]))
        return " ".join(parts)

    def _persist(self, ctx: LiveContext):
        try:
            ctx_file = DATA_DIR / "live_context.json"
            with open(ctx_file, "w") as f:
                json.dump(asdict(ctx), f, indent=2, default=str)
        except Exception:
            pass


# ──────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────

_engine: Optional[ContextEngine] = None


def get_context_engine() -> ContextEngine:
    global _engine
    if _engine is None:
        _engine = ContextEngine()
    return _engine


def start_context_engine(interval_seconds: int = 60):
    engine = get_context_engine()
    engine.start(interval_seconds)
    return engine


def get_live_context() -> LiveContext:
    return get_context_engine().get()


def get_prompt_context() -> str:
    return get_context_engine().get_prompt_context()


def get_context_dict() -> Dict[str, Any]:
    return get_context_engine().get_dict()
