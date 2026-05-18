"""
LOVE Phone Bridge — Android / iOS Sync
Connects your phone to LOVE so it knows:
  - Where you are (location label: home / office / gym / transit)
  - Battery level
  - Missed calls & unread messages count
  - Active notifications (WhatsApp, Telegram, etc.)
  - Whether you're moving (walking/driving/stationary)

How it works:
  Android: Install KDE Connect (free, open source) → pairs over LAN
  iOS:     Use Shortcuts app + LOVE webhook endpoint
  
  KDE Connect on PC + Android exposes a local API on port 1716.
  LOVE polls it every minute for state.

Setup:
  1. Install KDE Connect on Android: play.google.com/store/apps/details?id=org.kde.kdeconnect_tp
  2. Install KDE Connect on Windows: https://apps.microsoft.com/store/detail/kde-connect/9N93MRMSXBF0
  3. Pair devices on same WiFi — they auto-discover
  4. Add to .env:  PHONE_DEVICE_ID=your_device_name (shown in KDE Connect)
  
  OR use the iOS Shortcuts webhook:
  1. Create a Shortcut with "Get Battery Level" + "Send HTTP POST" to http://YOUR_PC_IP:8000/integrations/phone/update
  2. Run shortcut periodically via Automation
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from threading import Lock, Thread

DATA_DIR = Path(__file__).parent.parent / "data"
PHONE_STATE_FILE = DATA_DIR / "phone_state.json"

PHONE_DEVICE_ID = os.getenv("PHONE_DEVICE_ID", "")
KDE_CONNECT_PORT = int(os.getenv("KDE_CONNECT_PORT", "1716"))


class PhoneBridge:
    """
    Connects LOVE to your phone via KDE Connect or iOS Shortcuts webhook.
    Provides: battery, location label, missed calls, unread messages,
    notifications, activity (stationary/walking/driving).
    """

    _instance = None
    _lock = Lock()

    def __init__(self):
        self._connected = False
        self._state: Dict[str, Any] = {}
        self._last_update: Optional[datetime] = None
        self._running = False
        self._thread: Optional[Thread] = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_persisted_state()

    @classmethod
    def get_instance(cls) -> "PhoneBridge":
        with cls._lock:
            if cls._instance is None:
                cls._instance = PhoneBridge()
                cls._instance._start_polling()
            return cls._instance

    def is_connected(self) -> bool:
        if not self._last_update:
            return False
        elapsed = (datetime.now() - self._last_update).total_seconds()
        return elapsed < 300  # Connected if updated within 5 minutes

    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self.is_connected(),
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "state": self._state,
            "kde_connect_available": self._check_kde_connect(),
            "device_id": PHONE_DEVICE_ID,
            "setup_instructions": {
                "android": (
                    "1. Install KDE Connect on Android from Play Store\n"
                    "2. Install KDE Connect on Windows from Microsoft Store\n"
                    "3. Connect both devices to same WiFi — they auto-pair\n"
                    "4. Set PHONE_DEVICE_ID=YourPhoneName in .env"
                ),
                "ios": (
                    "1. Open Shortcuts app on iPhone\n"
                    "2. Create automation to POST to http://YOUR_PC_IP:8000/integrations/phone/update\n"
                    "3. Include: battery, location, missed_calls in JSON body"
                )
            }
        }

    def update_from_webhook(self, data: Dict[str, Any]):
        """
        Called by POST /integrations/phone/update — used by iOS Shortcuts
        or any custom phone app to push state to LOVE.
        """
        self._state.update({
            "battery": data.get("battery"),
            "location_label": data.get("location", data.get("location_label", "")),
            "location_lat": data.get("lat"),
            "location_lon": data.get("lon"),
            "missed_calls": data.get("missed_calls", 0),
            "unread_messages": data.get("unread_messages", 0),
            "activity": data.get("activity", "stationary"),  # stationary/walking/driving
            "notifications": data.get("notifications", []),
            "wifi_ssid": data.get("wifi"),
            "source": "webhook"
        })
        self._last_update = datetime.now()
        self._connected = True
        self._persist_state()
        return {"received": True, "timestamp": self._last_update.isoformat()}

    # ──────────────────────────────────────────────
    # KDE Connect polling
    # ──────────────────────────────────────────────

    def _start_polling(self):
        if not PHONE_DEVICE_ID:
            return
        if not self._check_kde_connect():
            return
        self._running = True
        self._thread = Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"[PhoneBridge] KDE Connect polling started for: {PHONE_DEVICE_ID}")

    def _poll_loop(self):
        while self._running:
            try:
                self._poll_kde_connect()
            except Exception as e:
                pass
            time.sleep(60)

    def _poll_kde_connect(self):
        """Poll KDE Connect for phone state via kdeconnect-cli."""
        import subprocess

        device_id = PHONE_DEVICE_ID

        # Battery
        try:
            out = subprocess.check_output(
                ["kdeconnect-cli", "--device", device_id, "--get-battery"],
                timeout=5, stderr=subprocess.DEVNULL
            ).decode().strip()
            battery_line = [l for l in out.splitlines() if "%" in l]
            if battery_line:
                battery = int(''.join(filter(str.isdigit, battery_line[0])))
                self._state["battery"] = battery
        except Exception:
            pass

        # SMS / notifications via kdeconnect
        try:
            out = subprocess.check_output(
                ["kdeconnect-cli", "--device", device_id, "--list-notifications"],
                timeout=5, stderr=subprocess.DEVNULL
            ).decode().strip()
            notifs = [l.strip() for l in out.splitlines() if l.strip()]
            self._state["notifications"] = notifs[:10]
            self._state["unread_messages"] = len([n for n in notifs if any(
                app in n.lower() for app in ["whatsapp", "telegram", "messages", "sms"]
            )])
        except Exception:
            pass

        self._last_update = datetime.now()
        self._state["source"] = "kde_connect"
        self._persist_state()

    def _check_kde_connect(self) -> bool:
        """Check if kdeconnect-cli is available."""
        import subprocess
        try:
            subprocess.check_output(["kdeconnect-cli", "--help"], timeout=3, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    # ──────────────────────────────────────────────
    # Location Intelligence
    # ──────────────────────────────────────────────

    def infer_location_label(self, lat: float, lon: float) -> str:
        """
        Infer semantic location label from coordinates.
        Uses saved known locations from config.
        """
        known_locations = self._load_known_locations()
        if not known_locations or not lat or not lon:
            return ""

        import math
        for label, coords in known_locations.items():
            dist = math.sqrt((lat - coords["lat"]) ** 2 + (lon - coords["lon"]) ** 2)
            if dist < 0.005:  # ~500m radius
                return label
        return "unknown location"

    def _load_known_locations(self) -> Dict:
        loc_file = DATA_DIR / "known_locations.json"
        if loc_file.exists():
            try:
                with open(loc_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_location(self, label: str, lat: float, lon: float):
        """Save a named location (e.g., home, office, gym)."""
        locations = self._load_known_locations()
        locations[label] = {"lat": lat, "lon": lon}
        loc_file = DATA_DIR / "known_locations.json"
        with open(loc_file, "w") as f:
            json.dump(locations, f, indent=2)

    # ──────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────

    def _persist_state(self):
        try:
            state = dict(self._state)
            state["last_update"] = self._last_update.isoformat() if self._last_update else None
            with open(PHONE_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def _load_persisted_state(self):
        if PHONE_STATE_FILE.exists():
            try:
                with open(PHONE_STATE_FILE) as f:
                    data = json.load(f)
                last_update_str = data.pop("last_update", None)
                if last_update_str:
                    self._last_update = datetime.fromisoformat(last_update_str)
                self._state = data
            except Exception:
                pass
