"""
LOVE Google Services Integration
Connects to: Google Calendar, Gmail, Google Drive
Uses OAuth2 — credentials stored locally, no cloud relay.

Setup:
  1. Go to https://console.cloud.google.com
  2. Create a project, enable Calendar API + Gmail API + Drive API
  3. Create OAuth 2.0 Desktop credentials
  4. Download as credentials.json → place in project root
  5. First run will open browser for one-time auth → token.json saved locally
  6. Add to .env:  GOOGLE_CREDENTIALS_PATH=./credentials.json
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import Lock

DATA_DIR = Path(__file__).parent.parent / "data"
CREDS_PATH = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json"))
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", "./data/google_token.json"))

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class GoogleServices:
    """
    Unified Google integration: Calendar + Gmail + Drive.
    Singleton — call GoogleServices.get_instance()
    """

    _instance = None
    _lock = Lock()

    def __init__(self):
        self._creds = None
        self._calendar_service = None
        self._gmail_service = None
        self._drive_service = None
        self._connected = False
        self._last_error: Optional[str] = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "GoogleServices":
        with cls._lock:
            if cls._instance is None:
                cls._instance = GoogleServices()
                cls._instance._try_connect()
            return cls._instance

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> Dict[str, Any]:
        try:
            import google.oauth2.credentials  # noqa
            packages_ok = True
        except ImportError:
            packages_ok = False
        return {
            "connected": self._connected,
            "packages_installed": packages_ok,
            "credentials_file_exists": CREDS_PATH.exists(),
            "token_file_exists": TOKEN_PATH.exists(),
            "error": self._last_error,
            "setup_instructions": (
                "1. Visit https://console.cloud.google.com\n"
                "2. Enable Calendar, Gmail, Drive APIs\n"
                "3. Create OAuth2 Desktop credentials\n"
                "4. Download as credentials.json → place in project root\n"
                "5. Set GOOGLE_CREDENTIALS_PATH=./credentials.json in .env\n"
                "6. Call POST /integrations/google/auth to authorize"
            ) if not self._connected else None
        }

    def authorize(self) -> Dict[str, Any]:
        """
        Trigger OAuth2 flow — opens browser for one-time auth.
        Call this from the /integrations/google/auth endpoint.
        """
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            if not CREDS_PATH.exists():
                return {"success": False, "error": f"credentials.json not found at {CREDS_PATH}"}

            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

            TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

            self._creds = creds
            self._build_services()
            self._connected = True
            return {"success": True, "message": "Google services authorized and connected"}
        except ImportError:
            return {
                "success": False,
                "error": "Missing package. Run: pip install google-auth-oauthlib google-api-python-client"
            }
        except Exception as e:
            self._last_error = str(e)
            return {"success": False, "error": str(e)}

    def _try_connect(self):
        """Silently try to connect using existing token."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
        except ImportError:
            self._last_error = "google packages not installed. Run: pip install google-auth-oauthlib google-api-python-client"
            return

        try:
            if not TOKEN_PATH.exists():
                return

            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())

            self._creds = creds
            self._build_services()
            self._connected = True
            print("[Google] Connected to Google services")
        except Exception as e:
            self._last_error = str(e)

    def _build_services(self):
        from googleapiclient.discovery import build
        self._calendar_service = build("calendar", "v3", credentials=self._creds)
        self._gmail_service = build("gmail", "v1", credentials=self._creds)
        self._drive_service = build("drive", "v3", credentials=self._creds)

    # ──────────────────────────────────────────────
    # CALENDAR
    # ──────────────────────────────────────────────

    def get_todays_events(self) -> List[Dict]:
        """Get all calendar events for today."""
        if not self._connected or not self._calendar_service:
            return []
        try:
            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            end = now.replace(hour=23, minute=59, second=59).isoformat()

            result = self._calendar_service.events().list(
                calendarId="primary",
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
                maxResults=20
            ).execute()

            events = []
            for item in result.get("items", []):
                start_raw = item.get("start", {})
                end_raw = item.get("end", {})

                start_str = start_raw.get("dateTime", start_raw.get("date", ""))
                end_str = end_raw.get("dateTime", end_raw.get("date", ""))

                start_dt = None
                end_dt = None
                try:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone()
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")).astimezone()
                except Exception:
                    pass

                minutes_away = None
                if start_dt:
                    delta = (start_dt - datetime.now().astimezone()).total_seconds() / 60
                    minutes_away = int(delta)

                events.append({
                    "title": item.get("summary", "Untitled"),
                    "start_str": start_dt.strftime("%I:%M %p") if start_dt else start_str,
                    "end_str": end_dt.strftime("%I:%M %p") if end_dt else end_str,
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "location": item.get("location", ""),
                    "description": (item.get("description", "") or "")[:200],
                    "meet_link": item.get("hangoutLink", ""),
                    "minutes_away": minutes_away,
                    "attendees": len(item.get("attendees", []))
                })

            return events
        except Exception as e:
            self._last_error = str(e)
            return []

    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Get upcoming events for the next N days."""
        if not self._connected or not self._calendar_service:
            return []
        try:
            now = datetime.now(timezone.utc)
            end = now + timedelta(days=days)

            result = self._calendar_service.events().list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=50
            ).execute()

            events = []
            for item in result.get("items", []):
                start_raw = item.get("start", {})
                start_str = start_raw.get("dateTime", start_raw.get("date", ""))
                events.append({
                    "title": item.get("summary", "Untitled"),
                    "start": start_str,
                    "location": item.get("location", ""),
                })
            return events
        except Exception as e:
            return []

    def get_calendar_insights(self) -> Dict[str, Any]:
        """Get calendar insights with smart suggestions."""
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            
            events_today = self.get_todays_events()
            insights = []
            suggestions = []

            # Meeting density analysis
            meeting_count = len([e for e in events_today if e.get("attendees", 0) > 1])
            total_hours = sum(
                (e.get("end_dt") - e.get("start_dt")).total_seconds() / 3600
                for e in events_today
                if e.get("start_dt") and e.get("end_dt")
            ) if events_today else 0

            if meeting_count >= 5:
                insights.append("Heavy meeting day scheduled - 5+ meetings")
                suggestions.append("Consider blocking focus time between meetings")
            elif total_hours > 6:
                insights.append(f"Long meeting day - {total_hours:.1f} hours scheduled")
                suggestions.append("Schedule breaks between long meetings")

            # Free time opportunities
            now_local = datetime.now()
            today_events_sorted = sorted(
                [e for e in events_today if e.get("start_dt")],
                key=lambda x: x.get("start_dt")
            )
            
            free_slots = []
            if today_events_sorted:
                # Morning free time
                first_event = today_events_sorted[0]
                if first_event.get("start_dt") and first_event["start_dt"] > now_local:
                    morning_free = (first_event["start_dt"] - now_local).total_seconds() / 3600
                    if morning_free > 1:
                        free_slots.append(f"{morning_free:.1f}h free before first meeting")
                
                # Between meetings
                for i in range(len(today_events_sorted) - 1):
                    current_end = today_events_sorted[i].get("end_dt")
                    next_start = today_events_sorted[i + 1].get("start_dt")
                    if current_end and next_start:
                        gap = (next_start - current_end).total_seconds() / 60
                        if gap > 30:
                            free_slots.append(f"{gap:.0f}min free between meetings")
                
                # Evening free time
                last_event = today_events_sorted[-1]
                if last_event.get("end_dt"):
                    evening_free = (now_local.replace(hour=18, minute=0) - last_event["end_dt"]).total_seconds() / 3600
                    if evening_free > 1:
                        free_slots.append(f"{evening_free:.1f}h free after last meeting")

            if free_slots:
                insights.append(f"Found {len(free_slots)} free time slots")
                suggestions.append("Use free slots for deep work or breaks")

            # Context-aware suggestions
            if ctx.stress_score and ctx.stress_score > 7:
                suggestions.append("High stress detected - consider rescheduling non-essential meetings")
            
            if ctx.tasks_due_today > 3:
                suggestions.append(f"{ctx.tasks_due_today} tasks due today - protect focus time")

            # Meeting preparation suggestions
            upcoming_meetings = [e for e in events_today if e.get("minutes_away", 999) <= 60]
            if upcoming_meetings:
                for meeting in upcoming_meetings[:2]:
                    title = meeting.get("title", "")
                    mins = meeting.get("minutes_away", 0)
                    if mins > 15:
                        suggestions.append(f"Prepare for '{title}' in {mins} minutes")

            return {
                "meeting_count": meeting_count,
                "total_meeting_hours": round(total_hours, 1),
                "free_slots": free_slots,
                "insights": insights,
                "suggestions": suggestions[:5],  # Top 5 suggestions
                "events_count": len(events_today),
            }

        except Exception as e:
            return {"error": str(e), "insights": [], "suggestions": []}

    # ──────────────────────────────────────────────
    # GMAIL
    # ──────────────────────────────────────────────

    def get_email_summary(self) -> Dict[str, Any]:
        """Get unread important email count and urgent email snippets."""
        if not self._connected or not self._gmail_service:
            return {"unread_important": 0, "urgent": []}
        try:
            # Important + unread
            result = self._gmail_service.users().messages().list(
                userId="me",
                q="is:unread is:important",
                maxResults=10
            ).execute()

            messages = result.get("messages", [])
            unread_important = len(messages)
            urgent = []

            for msg in messages[:5]:
                detail = self._gmail_service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()
                headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
                urgent.append({
                    "subject": headers.get("Subject", "")[:80],
                    "from": headers.get("From", "")[:60],
                    "snippet": detail.get("snippet", "")[:120]
                })

            return {"unread_important": unread_important, "urgent": urgent}
        except Exception as e:
            return {"unread_important": 0, "urgent": [], "error": str(e)}

    # ──────────────────────────────────────────────
    # DRIVE
    # ──────────────────────────────────────────────

    def get_recent_drive_files(self, count: int = 10) -> List[Dict]:
        """Get recently modified Drive files."""
        if not self._connected or not self._drive_service:
            return []
        try:
            result = self._drive_service.files().list(
                pageSize=count,
                orderBy="modifiedTime desc",
                fields="files(id, name, mimeType, modifiedTime, size, webViewLink)",
                q="trashed=false"
            ).execute()

            files = []
            for item in result.get("files", []):
                files.append({
                    "name": item.get("name", ""),
                    "type": item.get("mimeType", "").split(".")[-1],
                    "modified": item.get("modifiedTime", ""),
                    "link": item.get("webViewLink", ""),
                    "size_kb": round(int(item.get("size", 0)) / 1024, 1)
                })
            return files
        except Exception as e:
            return []

    def search_drive(self, query: str) -> List[Dict]:
        """Search Drive files by name or content."""
        if not self._connected or not self._drive_service:
            return []
        try:
            q = f"name contains '{query}' and trashed=false"
            result = self._drive_service.files().list(
                q=q,
                pageSize=10,
                fields="files(id, name, mimeType, modifiedTime, webViewLink)"
            ).execute()
            return [
                {
                    "name": f.get("name"),
                    "type": f.get("mimeType", "").split(".")[-1],
                    "modified": f.get("modifiedTime"),
                    "link": f.get("webViewLink")
                }
                for f in result.get("files", [])
            ]
        except Exception as e:
            return []


    # Proactive + Context

    def get_context_summary(self) -> str:
        if not self._connected:
            return ''
        parts = []
        try:
            events = self.get_todays_events()
            n = len(events)
            if n:
                parts.append('[CALENDAR] ' + str(n) + ' events today')
                for ev in events[:2]:
                    mins = ev.get('minutes_away')
                    if mins is not None and -5 <= mins <= 60:
                        when = 'NOW' if mins <= 0 else 'in ' + str(mins) + 'min'
                        meet = ' (Meet)' if ev.get('meet_link') else ''
                        parts.append('[CALENDAR] ' + ev['title'] + ' ' + when + meet)
        except Exception:
            pass
        try:
            email = self.get_email_summary()
            unread = email.get('unread_important', 0)
            if unread:
                parts.append('[GMAIL] ' + str(unread) + ' important unread emails')
        except Exception:
            pass
        return chr(10).join(parts)

    def get_proactive_alerts(self) -> list:
        if not self._connected:
            return []
        alerts = []
        try:
            events = self.get_todays_events()
            for ev in events:
                mins = ev.get('minutes_away')
                if mins is not None and 0 < mins <= 10:
                    meet = ' - Meet link ready' if ev.get('meet_link') else ''
                    alerts.append("Meeting '" + ev['title'] + "' starts in " + str(mins) + 'min' + meet)
        except Exception:
            pass
        try:
            email = self.get_email_summary()
            for msg in email.get('urgent', [])[:2]:
                subj = msg.get('subject', '')
                sender = msg.get('from', '')[:30]
                triggers = ['urgent', 'asap', 'immediately', 'action required']
                if any(kw in subj.lower() for kw in triggers):
                    alerts.append('Urgent email from ' + sender + ': ' + subj[:50])
        except Exception:
            pass
        return alerts

    def get_full_snapshot(self) -> dict:
        return {
            'connected': self._connected,
            'events_today': self.get_todays_events() if self._connected else [],
            'email_summary': self.get_email_summary() if self._connected else {},
            'recent_drive': self.get_recent_drive_files(5) if self._connected else [],
            'calendar_insights': self.get_calendar_insights() if self._connected else {},
        }
