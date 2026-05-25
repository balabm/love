"""
LOVE Microsoft Bridge — Teams, Outlook, Calendar, OneDrive
Connects your office Microsoft account so LOVE knows:
  - Outlook unread emails + calendar events
  - Teams unread messages + @mentions
  - OneDrive recent files
  - Meeting join links

Uses Microsoft Graph API with OAuth2 device-code flow
(works even without a browser on the home PC).

Setup:
  1. Go to https://portal.azure.com → App registrations → New registration
  2. Name: "LOVE Assistant", Supported: Personal + Work accounts
  3. API permissions: Mail.Read, Calendars.Read, Chat.Read, Files.Read.All (all Delegated)
  4. Authentication → Add platform → Mobile/Desktop → tick urn:ietf:wg:oauth:2.0:oob
  5. Note your Application (client) ID
  6. Add to .env:  MICROSOFT_CLIENT_ID=your_client_id
"""

import json
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

DATA_DIR = Path(__file__).parent.parent / "data"
MS_TOKEN_FILE = DATA_DIR / "ms_token.json"

CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
SCOPES = [
    "Mail.Read",
    "Calendars.Read",
    "Chat.Read",
    "Files.Read.All",
    "User.Read",
    "Presence.Read",
]


class MicrosoftBridge:
    """
    Microsoft 365 integration: Outlook, Teams, Calendar, OneDrive.
    Uses MSAL device-code flow — no browser needed on home PC.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._connected = False
        self._token: Optional[Dict] = None
        self._user_info: Optional[Dict] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._last_error = ""
        self._auth_pending = False
        self._device_code_data: Optional[Dict] = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._try_load_token()

    @classmethod
    def get_instance(cls) -> "MicrosoftBridge":
        with cls._lock:
            if cls._instance is None:
                cls._instance = MicrosoftBridge()
            return cls._instance

    # ──────────────────────────────────────────────
    # Auth
    # ──────────────────────────────────────────────

    def _try_load_token(self):
        """Load saved token and check validity."""
        if not MS_TOKEN_FILE.exists():
            return
        try:
            with open(MS_TOKEN_FILE) as f:
                token = json.load(f)
            # Check expiry
            expires_at = token.get("expires_at", 0)
            if time.time() < expires_at - 60:
                self._token = token
                self._connected = True
                print("[Microsoft] Loaded saved token — connected")
            else:
                # Try refresh
                self._refresh_token(token)
        except Exception as e:
            self._last_error = str(e)

    def _refresh_token(self, old_token: Dict) -> bool:
        """Refresh an expired token using the refresh_token."""
        try:
            import urllib.request
            import urllib.parse

            refresh_token = old_token.get("refresh_token")
            if not refresh_token or not CLIENT_ID:
                return False

            data = urllib.parse.urlencode({
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": " ".join(SCOPES),
            }).encode()

            req = urllib.request.Request(
                f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
                data=data,
                method="POST"
            )
            res = urllib.request.urlopen(req, timeout=15)
            token_data = json.loads(res.read())
            token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
            self._token = token_data
            self._connected = True
            self._save_token()
            print("[Microsoft] Token refreshed")
            return True
        except Exception as e:
            self._last_error = f"Token refresh failed: {e}"
            return False

    def start_device_code_auth(self) -> Dict[str, Any]:
        """
        Initiate device-code auth flow.
        Returns: { user_code, verification_uri, expires_in, device_code }
        User visits the URI and enters the code — no browser on home PC needed.
        """
        if not CLIENT_ID:
            return {"error": "MICROSOFT_CLIENT_ID not set in .env", "success": False}

        try:
            import urllib.request, urllib.parse

            data = urllib.parse.urlencode({
                "client_id": CLIENT_ID,
                "scope": " ".join(SCOPES),
            }).encode()

            req = urllib.request.Request(
                f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode",
                data=data, method="POST"
            )
            res = urllib.request.urlopen(req, timeout=15)
            device_data = json.loads(res.read())
            self._device_code_data = device_data
            self._auth_pending = True

            # Start polling in background
            t = threading.Thread(target=self._poll_device_code, daemon=True)
            t.start()

            return {
                "success": True,
                "user_code": device_data.get("user_code"),
                "verification_uri": device_data.get("verification_uri"),
                "message": device_data.get("message"),
                "expires_in": device_data.get("expires_in", 900),
            }
        except Exception as e:
            self._last_error = str(e)
            return {"success": False, "error": str(e)}

    def _poll_device_code(self):
        """Poll until user completes device-code auth."""
        if not self._device_code_data:
            return

        import urllib.request, urllib.parse

        device_code = self._device_code_data.get("device_code")
        interval = self._device_code_data.get("interval", 5)
        expires_in = self._device_code_data.get("expires_in", 900)
        start = time.time()

        while self._auth_pending and (time.time() - start) < expires_in:
            time.sleep(interval)
            try:
                data = urllib.parse.urlencode({
                    "client_id": CLIENT_ID,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                }).encode()

                req = urllib.request.Request(
                    f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
                    data=data, method="POST"
                )
                res = urllib.request.urlopen(req, timeout=15)
                token_data = json.loads(res.read())

                if "access_token" in token_data:
                    token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
                    self._token = token_data
                    self._connected = True
                    self._auth_pending = False
                    self._save_token()
                    print("[Microsoft] Device code auth successful — connected!")
                    # Fetch user info
                    self._fetch_user_info()
                    return

            except Exception as e:
                err = str(e)
                if "authorization_pending" in err:
                    continue
                elif "expired" in err.lower():
                    self._auth_pending = False
                    self._last_error = "Device code expired — try again"
                    return

    def _fetch_user_info(self):
        try:
            data = self._graph_get("/me?$select=displayName,mail,userPrincipalName")
            self._user_info = data
            print(f"[Microsoft] Signed in as: {data.get('displayName')} ({data.get('mail')})")
        except Exception:
            pass

    def _save_token(self):
        with open(MS_TOKEN_FILE, "w") as f:
            json.dump(self._token, f, indent=2)

    # ──────────────────────────────────────────────
    # Graph API helpers
    # ──────────────────────────────────────────────

    def _graph_get(self, path: str, cache_ttl: int = 120) -> Dict:
        """Make a Graph API GET request with simple caching."""
        cache_key = path
        if cache_key in self._cache and time.time() < self._cache_ttl.get(cache_key, 0):
            return self._cache[cache_key]

        if not self._token:
            raise Exception("Not authenticated")

        # Refresh if needed
        if time.time() >= self._token.get("expires_at", 0) - 60:
            if not self._refresh_token(self._token):
                raise Exception("Token expired and refresh failed")

        import urllib.request
        url = f"https://graph.microsoft.com/v1.0{path}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self._token['access_token']}",
            "Accept": "application/json",
        })
        res = urllib.request.urlopen(req, timeout=15)
        data = json.loads(res.read())

        self._cache[cache_key] = data
        self._cache_ttl[cache_key] = time.time() + cache_ttl
        return data

    # ──────────────────────────────────────────────
    # Outlook
    # ──────────────────────────────────────────────

    def get_unread_emails(self, limit: int = 10) -> List[Dict]:
        """Get unread emails from Outlook."""
        try:
            data = self._graph_get(
                f"/me/mailFolders/inbox/messages"
                f"?$filter=isRead eq false&$top={limit}"
                f"&$select=subject,from,receivedDateTime,importance,bodyPreview",
                cache_ttl=60
            )
            return [
                {
                    "subject": m.get("subject", ""),
                    "from": m.get("from", {}).get("emailAddress", {}).get("name", ""),
                    "from_email": m.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "received": m.get("receivedDateTime", ""),
                    "preview": m.get("bodyPreview", "")[:200],
                    "important": m.get("importance") == "high",
                }
                for m in data.get("value", [])
            ]
        except Exception as e:
            return []

    def get_unread_count(self) -> int:
        try:
            data = self._graph_get("/me/mailFolders/inbox?$select=unreadItemCount", cache_ttl=60)
            return data.get("unreadItemCount", 0)
        except Exception:
            return 0

    # ──────────────────────────────────────────────
    # Calendar
    # ──────────────────────────────────────────────

    def get_todays_events(self) -> List[Dict]:
        """Get today's calendar events."""
        try:
            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0).isoformat()
            end = now.replace(hour=23, minute=59, second=59).isoformat()

            data = self._graph_get(
                f"/me/calendarView?startDateTime={start}&endDateTime={end}"
                f"&$select=subject,start,end,location,onlineMeetingUrl,isOnlineMeeting,organizer"
                f"&$orderby=start/dateTime&$top=20",
                cache_ttl=120
            )
            return [
                {
                    "title": e.get("subject", ""),
                    "start": e.get("start", {}).get("dateTime", ""),
                    "end": e.get("end", {}).get("dateTime", ""),
                    "location": e.get("location", {}).get("displayName", ""),
                    "is_online": e.get("isOnlineMeeting", False),
                    "join_url": e.get("onlineMeetingUrl", ""),
                    "organizer": e.get("organizer", {}).get("emailAddress", {}).get("name", ""),
                }
                for e in data.get("value", [])
            ]
        except Exception:
            return []

    def get_next_event(self) -> Optional[Dict]:
        """Get the next upcoming event."""
        try:
            events = self.get_todays_events()
            now = datetime.now(timezone.utc)
            for event in events:
                start_str = event.get("start", "")
                if not start_str:
                    continue
                try:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if start_dt > now:
                        delta = int((start_dt - now).total_seconds() / 60)
                        return {**event, "minutes_away": delta,
                                "time": start_dt.strftime("%I:%M %p")}
                except Exception:
                    continue
        except Exception:
            pass
        return None

    # ──────────────────────────────────────────────
    # Teams
    # ──────────────────────────────────────────────

    def get_teams_messages(self, limit: int = 5) -> List[Dict]:
        """Get recent unread Teams messages (requires Chat.Read)."""
        try:
            chats = self._graph_get("/me/chats?$select=id,topic,chatType", cache_ttl=60)
            messages = []
            for chat in (chats.get("value") or [])[:5]:
                chat_id = chat.get("id")
                msgs = self._graph_get(
                    f"/me/chats/{chat_id}/messages?$top=3&$select=body,from,createdDateTime",
                    cache_ttl=60
                )
                for m in (msgs.get("value") or [])[:2]:
                    messages.append({
                        "chat": chat.get("topic") or "Direct message",
                        "from": m.get("from", {}).get("user", {}).get("displayName", ""),
                        "text": m.get("body", {}).get("content", "")[:200],
                        "time": m.get("createdDateTime", ""),
                    })
            return messages[:limit]
        except Exception:
            return []

    def get_my_presence(self) -> Dict:
        """Get current Teams presence status."""
        try:
            data = self._graph_get("/me/presence", cache_ttl=30)
            return {
                "availability": data.get("availability", "Unknown"),
                "activity": data.get("activity", ""),
            }
        except Exception:
            return {}

    # ──────────────────────────────────────────────
    # OneDrive
    # ──────────────────────────────────────────────

    def get_recent_files(self, limit: int = 5) -> List[Dict]:
        """Get recently accessed OneDrive files."""
        try:
            data = self._graph_get(
                f"/me/drive/recent?$top={limit}&$select=name,lastModifiedDateTime,webUrl",
                cache_ttl=300
            )
            return [
                {
                    "name": f.get("name", ""),
                    "modified": f.get("lastModifiedDateTime", ""),
                    "url": f.get("webUrl", ""),
                }
                for f in data.get("value", [])
            ]
        except Exception:
            return []

    # ──────────────────────────────────────────────
    # Status & Summary
    # ──────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self._connected,
            "client_id_set": bool(CLIENT_ID),
            "auth_pending": self._auth_pending,
            "user": self._user_info,
            "error": self._last_error,
            "device_code_data": {
                "user_code": self._device_code_data.get("user_code") if self._device_code_data else None,
                "verification_uri": self._device_code_data.get("verification_uri") if self._device_code_data else None,
                "message": self._device_code_data.get("message") if self._device_code_data else None,
            } if self._auth_pending and self._device_code_data else None,
        }

    def get_context_summary(self) -> str:
        """Summary for injection into LOVE's context prompt."""
        if not self._connected:
            return ""
        parts = []
        try:
            unread = self.get_unread_count()
            if unread > 0:
                parts.append(f"[OUTLOOK] {unread} unread emails")

            next_event = self.get_next_event()
            if next_event:
                parts.append(f"[TEAMS MEETING] {next_event['title']} in {next_event['minutes_away']}min")

            presence = self.get_my_presence()
            if presence.get("availability"):
                parts.append(f"[TEAMS STATUS] {presence['availability']} — {presence.get('activity','')}")
        except Exception:
            pass
        return "\n".join(parts)

    def is_connected(self) -> bool:
        return self._connected

    def get_proactive_alerts(self) -> list:
        if not self._connected:
            return []
        alerts = []
        try:
            nxt = self.get_next_event()
            if nxt:
                mins = nxt.get('minutes_away', 999)
                if 0 < mins <= 10:
                    join = ' - Join link ready' if nxt.get('join_url') else ''
                    alerts.append('Teams meeting in ' + str(mins) + 'min: ' + nxt.get('title','') + join)
        except Exception:
            pass
        try:
            emails = self.get_unread_emails(limit=5)
            for em in emails[:3]:
                if em.get('important'):
                    subj = em.get('subject','')
                    sender = em.get('from','')[:30]
                    alerts.append('High importance email from ' + sender + ': ' + subj[:50])
        except Exception:
            pass
        return alerts

    def get_full_snapshot(self) -> dict:
        return {
            'connected': self._connected,
            'unread_emails': self.get_unread_emails(10) if self._connected else [],
            'todays_events': self.get_todays_events() if self._connected else [],
            'teams_messages': self.get_teams_messages(5) if self._connected else [],
            'onedrive_recent': self.get_recent_files(5) if self._connected else [],
            'presence': self.get_my_presence() if self._connected else {},
        }
