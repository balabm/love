"""
LOVE Unified Device Bridge — Cross-Device Integration Without VPN

Connects mobile, office laptop, and team devices to LOVE without requiring
Tailscale or any VPN. Uses cloud-native, zero-config transports.

Supported transports (pick one or more in .env):
  1. CLOUDFLARE_TUNNEL — Permanent public URL for webhooks. Free, stable.
     .env: CLOUDFLARE_TUNNEL_URL=https://love-yourname.trycloudflare.com

  2. TELEGRAM_BOT — Phone forwards SMS/notifications to a Telegram bot.
     LOVE polls Telegram API. Works from anywhere, very reliable.
     .env: TELEGRAM_BOT_TOKEN=your_bot_token

  3. MQTT_PUBLIC — Lightweight pub/sub via HiveMQ public broker.
     Phone publishes, LOVE subscribes. Good for real-time.
     .env: MQTT_BROKER=broker.hivemq.com, MQTT_TOPIC=love/notifications

  4. SYNCTHING — P2P folder sync. No cloud account needed.
     Phone drops JSON files, LOVE watches folder.
     .env: SYNC_FOLDER=/path/to/sync/love_drop

  5. WEBHOOK_RELAY — Use webhook.site or similar as intermediary.
     .env: WEBHOOK_RELAY_URL=https://webhook.site/your-uuid

  6. DISCORD_WEBHOOK — Phone sends via Discord app, LOVE polls channel.
     .env: DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

Setup recommendation per use-case:
  - Notifications (bank SMS, app alerts): Telegram Bot or Cloudflare Tunnel
  - Files / screenshots / data: Syncthing or OneDrive/iCloud sync folder
  - Real-time sensor data: MQTT
  - Quick & dirty: Webhook relay

All transports feed into the same unified DeviceBridge.get_state() interface
used by notification_ingestion, finance_guardian, and other modules.
"""

import json
import os
import re
import time
import threading
import urllib.request
import urllib.parse
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# Neural Bus
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

# Proactive Push
try:
    from core.proactive_push import get_push_engine
    PUSH_AVAILABLE = True
except ImportError:
    PUSH_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"
DEVICE_STATE_FILE = DATA_DIR / "device_bridge_state.json"
DEVICE_MESSAGE_LOG = DATA_DIR / "device_messages.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Config ────────────────────────────────────────────────────────────────

# 1. Cloudflare Tunnel (or any public URL pointing to LOVE)
PUBLIC_TUNNEL_URL = os.getenv("CLOUDFLARE_TUNNEL_URL", "")

# 2. Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_POLL_INTERVAL = int(os.getenv("TELEGRAM_POLL_INTERVAL", "30"))

# 3. MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "love/notifications")
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "false").lower() in ("true", "1", "yes")

# 4. Syncthing / folder sync
SYNC_FOLDER = Path(os.getenv("SYNC_FOLDER", str(DATA_DIR / "sync_drop")))

# 5. Webhook relay
WEBHOOK_RELAY_URL = os.getenv("WEBHOOK_RELAY_URL", "")

# 6. Discord
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")

# Shared
DEVICE_BRIDGE_ENABLED = os.getenv("DEVICE_BRIDGE_ENABLED", "true").lower() in ("true", "1", "yes")


# ═════════════════════════════════════════════════════════════════════════════
#  TELEGRAM BOT TRANSPORT
# ═════════════════════════════════════════════════════════════════════════════

class TelegramTransport:
    """Polls Telegram Bot API for messages forwarded from phone."""

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, token: str, chat_id: str = ""):
        self.token = token
        self.chat_id = chat_id
        self.last_update_id = 0
        self.messages: deque = deque(maxlen=500)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running or not self.token:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="LOVE-Telegram")
        self._thread.start()
        print(f"[DeviceBridge] Telegram transport started (poll every {TELEGRAM_POLL_INTERVAL}s)")

    def stop(self):
        self._running = False

    def _poll_loop(self):
        while self._running:
            try:
                self._fetch_updates()
            except Exception as e:
                print(f"[Telegram] Poll error: {e}")
            time.sleep(TELEGRAM_POLL_INTERVAL)

    def _fetch_updates(self):
        url = f"{self.BASE_URL}{self.token}/getUpdates"
        params = {"offset": self.last_update_id + 1, "limit": 20}
        req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", timeout=15)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        if not data.get("ok"):
            return

        for update in data.get("result", []):
            self.last_update_id = max(self.last_update_id, update["update_id"])
            msg = update.get("message", {})
            text = msg.get("text", "")
            if not text:
                continue

            # Filter to configured chat if set
            if self.chat_id and str(msg.get("chat", {}).get("id", "")) != self.chat_id:
                continue

            entry = {
                "transport": "telegram",
                "text": text,
                "sender": msg.get("from", {}).get("username", "unknown"),
                "timestamp": datetime.fromtimestamp(msg.get("date", 0)).isoformat(),
                "raw": msg,
            }
            self.messages.append(entry)
            self._log_message(entry)

            # Publish to neural bus
            if NEURAL_BUS_AVAILABLE:
                try:
                    bus = get_neural_bus()
                    bus.publish(
                        domain="device", event_type="telegram_message",
                        payload=entry, source_module="device_bridge",
                        priority=EventPriority.NORMAL,
                    )
                except Exception:
                    pass

    def _log_message(self, entry: Dict):
        try:
            with open(DEVICE_MESSAGE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    def send(self, text: str) -> bool:
        """Send a message back to Telegram."""
        if not self.token:
            return False
        try:
            url = f"{self.BASE_URL}{self.token}/sendMessage"
            payload = urllib.parse.urlencode({"chat_id": self.chat_id or "@love_bridge",
                                               "text": text[:4000]}).encode()
            req = urllib.request.Request(url, data=payload,
                                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                                          method="POST")
            with urllib.request.urlopen(req, timeout=10):
                return True
        except Exception:
            return False

    def get_messages(self, limit: int = 50) -> List[Dict]:
        return list(self.messages)[-limit:]


# ═════════════════════════════════════════════════════════════════════════════
#  MQTT TRANSPORT
# ═════════════════════════════════════════════════════════════════════════════

class MQTTTransport:
    """Subscribes to a public MQTT broker for lightweight device messages."""

    def __init__(self, broker: str, port: int, topic: str):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.messages: deque = deque(maxlen=500)
        self._running = False
        self._client = None

    def start(self):
        if self._running:
            return
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            print("[DeviceBridge] MQTT transport requires: pip install paho-mqtt")
            return

        self._running = True

        def on_connect(client, _userdata, _flags, rc):
            if rc == 0:
                client.subscribe(self.topic)
                print(f"[MQTT] Connected to {self.broker}:{self.port}, subscribed to {self.topic}")
            else:
                print(f"[MQTT] Connection failed: {rc}")

        def on_message(_client, _userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
            except Exception:
                payload = {"text": msg.payload.decode()}
            entry = {
                "transport": "mqtt",
                "topic": msg.topic,
                "payload": payload,
                "timestamp": datetime.now().isoformat(),
            }
            self.messages.append(entry)
            self._log_message(entry)

        self._client = mqtt.Client()
        self._client.on_connect = on_connect
        self._client.on_message = on_message
        try:
            self._client.connect(self.broker, self.port, 60)
            self._client.loop_start()
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")
            self._running = False

    def stop(self):
        self._running = False
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    def _log_message(self, entry: Dict):
        try:
            with open(DEVICE_MESSAGE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    def get_messages(self, limit: int = 50) -> List[Dict]:
        return list(self.messages)[-limit:]


# ═════════════════════════════════════════════════════════════════════════════
#  FOLDER SYNC TRANSPORT (Syncthing / iCloud / OneDrive / Dropbox)
# ═════════════════════════════════════════════════════════════════════════════

class FolderSyncTransport:
    """
    Watches a sync folder (managed by Syncthing, iCloud, OneDrive, Dropbox, etc.)
    for JSON files dropped by phone or other devices.
    """

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.messages: deque = deque(maxlen=500)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._seen_files: set = set()
        self.folder.mkdir(parents=True, exist_ok=True)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="LOVE-FolderSync")
        self._thread.start()
        print(f"[DeviceBridge] Folder sync transport watching: {self.folder}")

    def stop(self):
        self._running = False

    def _watch_loop(self):
        time.sleep(5)
        while self._running:
            try:
                for fpath in self.folder.glob("*.json"):
                    if fpath.name in self._seen_files:
                        continue
                    self._seen_files.add(fpath.name)
                    try:
                        data = json.loads(fpath.read_text(encoding="utf-8"))
                        entry = {
                            "transport": "folder_sync",
                            "file": fpath.name,
                            "payload": data,
                            "timestamp": datetime.now().isoformat(),
                        }
                        self.messages.append(entry)
                        self._log_message(entry)
                    except Exception:
                        pass
                # Prune old entries to prevent memory growth
                if len(self._seen_files) > 1000:
                    self._seen_files = set(list(self._seen_files)[-500:])
                time.sleep(10)
            except Exception as e:
                print(f"[FolderSync] Watch error: {e}")
                time.sleep(30)

    def _log_message(self, entry: Dict):
        try:
            with open(DEVICE_MESSAGE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    def get_messages(self, limit: int = 50) -> List[Dict]:
        return list(self.messages)[-limit:]

    def write_to_sync(self, filename: str, data: Dict):
        """Write a file to the sync folder for other devices to pick up."""
        try:
            path = self.folder / filename
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False


# ═════════════════════════════════════════════════════════════════════════════
#  DISCORD WEBHOOK / BOT TRANSPORT
# ═════════════════════════════════════════════════════════════════════════════

class DiscordTransport:
    """Polls Discord channel for messages, or receives via webhook."""

    def __init__(self, webhook_url: str = "", bot_token: str = "", channel_id: str = ""):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.messages: deque = deque(maxlen=500)
        self._running = False
        self._last_message_id = ""
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running or not (self.bot_token and self.channel_id):
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="LOVE-Discord")
        self._thread.start()
        print("[DeviceBridge] Discord transport started")

    def stop(self):
        self._running = False

    def _poll_loop(self):
        while self._running:
            try:
                self._fetch_messages()
            except Exception as e:
                print(f"[Discord] Poll error: {e}")
            time.sleep(30)

    def _fetch_messages(self):
        url = f"https://discord.com/api/v10/channels/{self.channel_id}/messages"
        headers = {"Authorization": f"Bot {self.bot_token}", "Content-Type": "application/json"}
        params = {"limit": 10}
        if self._last_message_id:
            params["after"] = self._last_message_id

        req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}",
                                      headers=headers, timeout=10)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        for msg in reversed(data):
            self._last_message_id = msg["id"]
            text = msg.get("content", "")
            if not text:
                continue
            entry = {
                "transport": "discord",
                "text": text,
                "sender": msg.get("author", {}).get("username", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }
            self.messages.append(entry)
            self._log_message(entry)

    def _log_message(self, entry: Dict):
        try:
            with open(DEVICE_MESSAGE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    def get_messages(self, limit: int = 50) -> List[Dict]:
        return list(self.messages)[-limit:]


# ═════════════════════════════════════════════════════════════════════════════
#  UNIFIED DEVICE BRIDGE
# ═════════════════════════════════════════════════════════════════════════════

class DeviceBridge:
    """
    Unified bridge across all transports. Other modules interact with this only.
    Automatically selects and starts the best available transport(s).
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._running = False
        self._transports: Dict[str, Any] = {}
        self._state: Dict[str, Any] = {
            "connected": False,
            "active_transports": [],
            "last_message_time": None,
            "phone_battery": None,
            "phone_location": "unknown",
            "missed_calls": 0,
            "unread_messages": 0,
            "recent_notifications": [],
        }
        self._recent_messages: deque = deque(maxlen=200)
        self._message_callbacks: List[Callable] = []
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_state()

    @classmethod
    def get_instance(cls) -> "DeviceBridge":
        with cls._lock:
            if cls._instance is None:
                cls._instance = DeviceBridge()
            return cls._instance

    def start(self):
        if self._running:
            return
        self._running = True

        # 1. Telegram (most reliable for notifications)
        if TELEGRAM_BOT_TOKEN:
            t = TelegramTransport(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            t.start()
            self._transports["telegram"] = t
            self._state["active_transports"].append("telegram")

        # 2. MQTT (lightweight real-time)
        if MQTT_ENABLED:
            t = MQTTTransport(MQTT_BROKER, MQTT_PORT, MQTT_TOPIC)
            t.start()
            self._transports["mqtt"] = t
            self._state["active_transports"].append("mqtt")

        # 3. Folder Sync (Syncthing / iCloud / OneDrive)
        t = FolderSyncTransport(SYNC_FOLDER)
        t.start()
        self._transports["folder_sync"] = t
        self._state["active_transports"].append("folder_sync")

        # 4. Discord
        if DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID:
            t = DiscordTransport(DISCORD_WEBHOOK_URL, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID)
            t.start()
            self._transports["discord"] = t
            self._state["active_transports"].append("discord")

        # Start unified processor
        self._processor = threading.Thread(target=self._process_loop, daemon=True, name="LOVE-DeviceProcessor")
        self._processor.start()

        self._state["connected"] = len(self._state["active_transports"]) > 0
        self._save_state()

        print(f"[DeviceBridge] Started with transports: {self._state['active_transports']}")
        if PUBLIC_TUNNEL_URL:
            print(f"[DeviceBridge] Public tunnel URL: {PUBLIC_TUNNEL_URL}")
            print(f"  Configure phone Shortcuts/Tasker to POST to: {PUBLIC_TUNNEL_URL}/device/webhook")

    def stop(self):
        self._running = False
        for t in self._transports.values():
            try:
                t.stop()
            except Exception:
                pass
        self._save_state()

    def is_connected(self) -> bool:
        return self._state.get("connected", False)

    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        return list(self._recent_messages)[-limit:]

    def get_all_messages(self, limit: int = 100) -> List[Dict]:
        """Get messages from all transports unified."""
        all_msgs = []
        for name, transport in self._transports.items():
            try:
                msgs = transport.get_messages(limit=50)
                for m in msgs:
                    m["transport_name"] = name
                all_msgs.extend(msgs)
            except Exception:
                pass
        all_msgs.sort(key=lambda x: x.get("timestamp", ""))
        return all_msgs[-limit:]

    def register_callback(self, callback: Callable):
        self._message_callbacks.append(callback)

    def _process_loop(self):
        """Poll all transports, merge messages, extract context, publish events."""
        time.sleep(10)
        while self._running:
            try:
                for name, transport in self._transports.items():
                    try:
                        new_msgs = transport.get_messages(limit=10)
                        for msg in new_msgs:
                            # Skip duplicates by simple hash
                            msg_hash = hash(json.dumps(msg, sort_keys=True, default=str)) & 0xFFFFFFFF
                            if any(hash(json.dumps(m, sort_keys=True, default=str)) & 0xFFFFFFFF == msg_hash for m in self._recent_messages):
                                continue
                            self._recent_messages.append(msg)
                            self._on_new_message(msg, name)
                    except Exception:
                        pass
                time.sleep(5)
            except Exception as e:
                print(f"[DeviceBridge] Processor error: {e}")
                time.sleep(30)

    def _on_new_message(self, msg: Dict, transport_name: str):
        """Process a new unified message from any transport."""
        self._state["last_message_time"] = msg.get("timestamp", datetime.now().isoformat())

        # Extract text
        text = msg.get("text", "")
        payload = msg.get("payload", {})
        if not text and isinstance(payload, dict):
            text = payload.get("text", "")

        if not text:
            return

        # Check for phone state updates
        self._extract_phone_state(text, payload)

        # Check for financial content
        is_financial = self._looks_financial(text)

        # Publish to neural bus
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="device", event_type=f"{transport_name}_message",
                    payload={"text": text, "transport": transport_name, "timestamp": msg.get("timestamp")},
                    source_module="device_bridge",
                    priority=EventPriority.HIGH if is_financial else EventPriority.NORMAL,
                )
            except Exception:
                pass

        # Route to finance guardian if financial
        if is_financial:
            try:
                from core.finance_guardian import get_finance_guardian
                get_finance_guardian().ingest_from_notification(text, source=f"device_{transport_name}")
            except Exception:
                pass

        # Autonomous learning — feed EVERY message into pattern engine
        try:
            from core.notification_learning import get_notification_learning_engine
            learner = get_notification_learning_engine()
            learner.ingest({
                "text": text,
                "source": f"device_{transport_name}",
                "app": payload.get("app", transport_name),
                "timestamp": msg.get("timestamp", datetime.now().isoformat()),
                "payload": payload,
            })
        except Exception:
            pass

        # Run callbacks
        for cb in self._message_callbacks:
            try:
                cb(msg, transport_name)
            except Exception:
                pass

    def _extract_phone_state(self, text: str, payload: Dict):
        """Try to extract phone battery, location, etc. from message text."""
        # Battery: "battery: 45%" or "Battery 45"
        batt_match = re.search(r'battery[:\s]+(\d+)%?', text, re.IGNORECASE)
        if batt_match:
            self._state["phone_battery"] = int(batt_match.group(1))

        # Location keywords
        locations = ["home", "office", "gym", "transit", "car", "driving", "walking", "stationary"]
        for loc in locations:
            if re.search(rf'\b{loc}\b', text, re.IGNORECASE):
                self._state["phone_location"] = loc
                break

        # Missed calls / unread
        call_match = re.search(r'missed call[s]?:?\s*(\d+)', text, re.IGNORECASE)
        if call_match:
            self._state["missed_calls"] = int(call_match.group(1))
        msg_match = re.search(r'unread (?:message|msg)[s]?:?\s*(\d+)', text, re.IGNORECASE)
        if msg_match:
            self._state["unread_messages"] = int(msg_match.group(1))

        # Notifications list
        if payload.get("notifications"):
            self._state["recent_notifications"] = payload["notifications"][-10:]

        self._save_state()

    def _looks_financial(self, text: str) -> bool:
        keywords = [
            "debited", "credited", "spent", "purchase", "transaction", "payment",
            "withdrawn", "deposit", "balance", "account", "card", "bank",
            "upi", "emi", "loan", "refund", "transfer", "sent", "received",
            "merchant", "atm", "pos", "₹", "$", "€", "£",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords) or any(sym in text for sym in ["₹", "$", "€", "£"])

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def get_setup_instructions(self) -> Dict[str, str]:
        """Return setup instructions for each available transport."""
        instructions = {}
        if TELEGRAM_BOT_TOKEN:
            instructions["telegram"] = (
                f"1. Open Telegram, find your bot\n"
                f"2. Forward bank SMS/notifications to the bot\n"
                f"3. LOVE auto-reads every {TELEGRAM_POLL_INTERVAL}s"
            )
        if PUBLIC_TUNNEL_URL:
            instructions["webhook"] = (
                f"1. Install 'Shortcuts' (iOS) or 'Tasker' (Android)\n"
                f"2. Create automation: On SMS receive → HTTP POST to\n"
                f"   {PUBLIC_TUNNEL_URL}/device/webhook\n"
                f"3. JSON body: {{\"text\": \"{{SMS}}\", \"source\": \"phone\"}}"
            )
        if MQTT_ENABLED:
            instructions["mqtt"] = (
                f"1. Install MQTT client app (e.g. IoTMQTTPanel)\n"
                f"2. Broker: {MQTT_BROKER}:{MQTT_PORT}\n"
                f"3. Publish to topic: {MQTT_TOPIC}\n"
                f"4. JSON payload: {{\"text\": \"your message\"}}"
            )
        instructions["folder_sync"] = (
            f"1. Set up Syncthing / iCloud / OneDrive / Dropbox\n"
            f"2. Sync folder: {SYNC_FOLDER}\n"
            f"3. Drop .json files from phone with {{\"text\": \"...\"}}\n"
            f"4. LOVE auto-detects new files every 10s"
        )
        if DISCORD_WEBHOOK_URL or (DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID):
            instructions["discord"] = (
                f"1. Send messages to the configured Discord channel\n"
                f"2. LOVE auto-reads every 30s"
            )
        return instructions

    def get_zero_touch_config(self) -> Dict[str, Any]:
        """
        Return configuration for zero-touch auto-forwarding.
        Phone apps (Tasker, MacroDroid, Automate) can import this JSON
        to auto-forward ALL notifications without manual forwarding.
        """
        return {
            "version": 1,
            "endpoint": PUBLIC_TUNNEL_URL or "http://YOUR_PC_IP:8000",
            "webhook_path": "/device/webhook",
            "poll_interval_seconds": TELEGRAM_POLL_INTERVAL,
            "payload_template": {
                "text": "{{notification_text}}",
                "app": "{{notification_app}}",
                "title": "{{notification_title}}",
                "source": "phone_auto",
                "timestamp": "{{timestamp_iso}}",
                "battery": "{{device_battery}}",
                "location": "{{device_location}}",
            },
            "tasker_profile_xml": self._tasker_profile_xml(),
            "mqtt_config": {
                "broker": MQTT_BROKER,
                "port": MQTT_PORT,
                "topic": MQTT_TOPIC,
            } if MQTT_ENABLED else None,
        }

    def _tasker_profile_xml(self) -> str:
        """Generate a Tasker XML profile that auto-forwards all notifications."""
        endpoint = f"{PUBLIC_TUNNEL_URL}/device/webhook" if PUBLIC_TUNNEL_URL else "http://YOUR_PC_IP:8000/device/webhook"
        return f"""<TaskerData sr="">
  <Profile sr="prof0" ve="2">
    <cdate>0</cdate>
    <edate>0</edate>
    <id>1</id>
    <mid0>1</mid0>
    <nme>LOVE Auto Forward</nme>
    <Event sr="con0" ve="2">
      <code>461</code>
      <pri>0</pri>
      <Str sr="arg0" ve="3"/>
      <Str sr="arg1" ve="3"/>
    </Event>
  </Profile>
  <Task sr="task1">
    <cdate>0</cdate>
    <edate>0</edate>
    <id>1</id>
    <nme>LOVE Forward</nme>
    <Action sr="act0" ve="7">
      <code>598</code>
      <Str sr="arg0" ve="3">{endpoint}</Str>
      <Str sr="arg1" ve="3">application/json</Str>
      <Str sr="arg2" ve="3">POST</Str>
      <Str sr="arg3" ve="3">{{\"text\":\"%evtprm2\",\"app\":\"%evtprm1\",\"title\":\"%evtprm3\",\"source\":\"phone_auto\"}}</Str>
    </Action>
  </Task>
</TaskerData>"""

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _save_state(self):
        try:
            DEVICE_STATE_FILE.write_text(json.dumps(self._state, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass

    def _load_state(self):
        if not DEVICE_STATE_FILE.exists():
            return
        try:
            self._state = json.loads(DEVICE_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass


# ─── Singleton ────────────────────────────────────────────────────────────

def get_device_bridge() -> DeviceBridge:
    return DeviceBridge.get_instance()


def start_device_bridge():
    bridge = get_device_bridge()
    bridge.start()
    return bridge


def stop_device_bridge():
    bridge = get_device_bridge()
    bridge.stop()