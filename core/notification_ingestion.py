"""
LOVE Notification Ingestion Engine
Silently runs in the background, siphoning notifications from Phone (KDE Connect/Webhook)
and Microsoft 365 (Teams/Outlook) directly into the Knowledge Graph.
Builds the World Model without requiring the user to explicitly talk to LOVE.
"""

import time
import hashlib
from threading import Thread, Lock
from typing import Set, Optional

from core import knowledge_graph
from integrations.phone_bridge import PhoneBridge
from integrations.microsoft_bridge import MicrosoftBridge


class NotificationIngestionEngine:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._running = False
        self._thread: Optional[Thread] = None
        self._seen_hashes: Set[str] = set()

    @classmethod
    def get_instance(cls) -> "NotificationIngestionEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = NotificationIngestionEngine()
            return cls._instance

    def start(self, interval_seconds: int = 60):
        if self._running:
            return
        self._running = True
        self._thread = Thread(target=self._loop, args=(interval_seconds,), daemon=True)
        self._thread.start()
        print(f"[Ingestion] Notification Ingestion Engine started ({interval_seconds}s interval)")

    def stop(self):
        self._running = False

    def _loop(self, interval: int):
        # Allow bridges to initialize first
        time.sleep(5)
        while self._running:
            try:
                self._poll_and_ingest()
            except Exception as e:
                print(f"[Ingestion] Polling error: {e}")
            time.sleep(interval)

    def _hash_text(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

    def _poll_and_ingest(self):
        phone = PhoneBridge.get_instance()
        ms = MicrosoftBridge.get_instance()

        # 1. Phone Notifications
        if phone.is_connected():
            state = phone.get_state()
            notifs = state.get("notifications", [])
            for n in notifs:
                if not n.strip():
                    continue
                h = self._hash_text("phone_" + n)
                if h not in self._seen_hashes:
                    self._seen_hashes.add(h)
                    try:
                        # Extract and ingest
                        knowledge_graph.ingest_text(n, source="phone_notification")
                    except Exception as e:
                        print(f"[Ingestion] KG ingest error for phone: {e}")

        # 2. Microsoft Teams Messages
        if ms.is_connected():
            try:
                teams_msgs = ms.get_teams_messages(limit=5)
                for msg in teams_msgs:
                    content = msg.get("text", "")
                    sender = msg.get("from", "Unknown")
                    chat = msg.get("chat", "Direct message")
                    if not content:
                        continue
                    
                    full_text = f"{sender} in {chat}: {content}"
                    h = self._hash_text("teams_" + full_text)
                    if h not in self._seen_hashes:
                        self._seen_hashes.add(h)
                        knowledge_graph.ingest_text(full_text, source="teams_message")
            except Exception as e:
                pass

            # 3. Microsoft Outlook Emails
            try:
                emails = ms.get_unread_emails(limit=5)
                for email in emails:
                    subj = email.get("subject", "")
                    sender = email.get("from", "Unknown")
                    preview = email.get("preview", "")
                    if not subj:
                        continue

                    full_text = f"Email from {sender} about {subj}. Preview: {preview}"
                    h = self._hash_text("email_" + full_text)
                    if h not in self._seen_hashes:
                        self._seen_hashes.add(h)
                        knowledge_graph.ingest_text(full_text, source="outlook_email")
            except Exception as e:
                pass

        # Keep set from growing indefinitely (cap at 10,000)
        if len(self._seen_hashes) > 10000:
            self._seen_hashes = set(list(self._seen_hashes)[-5000:])


def start_ingestion():
    engine = NotificationIngestionEngine.get_instance()
    engine.start()
    return engine
