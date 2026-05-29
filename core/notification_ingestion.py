"""
LOVE Notification Ingestion Engine v2 — Smart Classification, Noise Filtering, Cross-Device Monitoring

Silently runs in the background, siphoning notifications from Phone (KDE Connect/Webhook)
and Microsoft 365 (Teams/Outlook). Now with:
  - Smart classification (urgent, work, social, promo, system, financial, etc.)
  - Noise / signal scoring — drops spam, surfaces what matters
  - Entity extraction (names, deadlines, action words, locations)
  - Cross-device semantic deduplication
  - Rich structured NeuralBus events
  - Integration with FinanceGuardian for bank/finance notifications
"""

import json
import re
import time
import hashlib
from datetime import datetime
from threading import Thread, Lock
from typing import Set, Optional, Dict, List, Any
from collections import defaultdict, deque

from core import knowledge_graph
from integrations.phone_bridge import PhoneBridge

# Microsoft Teams integration (optional — only if azure is installed)
try:
    from integrations.microsoft_bridge import MicrosoftBridge
    MICROSOFT_AVAILABLE = True
except ImportError:
    MICROSOFT_AVAILABLE = False
    _ms_bridge_instance = None
    class MicrosoftBridge:
        @staticmethod
        def get_instance():
            global _ms_bridge_instance
            if _ms_bridge_instance is None:
                _ms_bridge_instance = MicrosoftBridge()
            return _ms_bridge_instance
        def is_connected(self):
            return False
        def poll_notifications(self):
            return []
        def get_teams_messages(self, limit=5):
            return []
        def get_unread_count(self):
            return 0
        def get_next_event(self):
            return None
        def get_context_summary(self):
            return None

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

# Proactive Push integration
try:
    from core.proactive_push import get_push_engine
    PUSH_AVAILABLE = True
except ImportError:
    PUSH_AVAILABLE = False


class SmartNotificationClassifier:
    """Heuristic classifier that scores notifications for relevance and type."""

    # Urgency signals
    URGENT_KEYWORDS = [
        "urgent", "asap", "immediately", "critical", "alert", "warning",
        "failed", "error", "declined", "overdue", "expired", "suspended",
        "locked", "fraud", "unauthorized", "breach", "emergency",
    ]

    # Work-related signals
    WORK_KEYWORDS = [
        "meeting", "deadline", "project", "client", "boss", "manager",
        "report", "review", "interview", "offer", "contract", "invoice",
        " teams ", "slack", "jira", "github", "pull request", "deploy",
        "calendar", "schedule", "appointment", "reminder",
    ]

    # Social signals
    SOCIAL_KEYWORDS = [
        "whatsapp", "telegram", "message", "call", "missed call", "voicemail",
        "instagram", "facebook", "twitter", "snapchat", "tiktok",
        "birthday", "party", "dinner", "lunch", "catch up",
    ]

    # Promotional / spam signals (negative score)
    PROMO_KEYWORDS = [
        "sale", "discount", "offer", "coupon", "deal", "promo",
        "subscribe", "newsletter", "promotion", " cashback", "reward",
        "limited time", "act now", "free shipping", "buy now", "shop now",
        "advertisement", "sponsored", "unsubscribe",
    ]

    # Financial signals
    FINANCE_KEYWORDS = [
        "debited", "credited", "spent", "purchase", "transaction", "payment",
        "withdrawn", "deposit", "balance", "account", "card", "bank",
        "upi", "emi", "loan", "refund", "transfer", "sent", "received",
    ]

    # System / low-value signals
    SYSTEM_KEYWORDS = [
        "update available", "backup complete", "synced", "upload complete",
        "download complete", "battery full", "wifi connected", "bluetooth",
        "app update", "software update", "storage", "cache cleared",
    ]

    def classify(self, text: str, source: str = "unknown") -> Dict[str, Any]:
        text_lower = text.lower()
        scores = defaultdict(int)

        # Base scoring by keyword presence
        for kw in self.URGENT_KEYWORDS:
            if kw in text_lower:
                scores["urgent"] += 3
                scores["signal"] += 2

        for kw in self.WORK_KEYWORDS:
            if kw in text_lower:
                scores["work"] += 2
                scores["signal"] += 1

        for kw in self.SOCIAL_KEYWORDS:
            if kw in text_lower:
                scores["social"] += 2
                scores["signal"] += 1

        for kw in self.PROMO_KEYWORDS:
            if kw in text_lower:
                scores["promotional"] += 3
                scores["noise"] += 2

        for kw in self.FINANCE_KEYWORDS:
            if kw in text_lower:
                scores["financial"] += 3
                scores["signal"] += 2

        for kw in self.SYSTEM_KEYWORDS:
            if kw in text_lower:
                scores["system"] += 2
                scores["noise"] += 1

        # Source-based priors
        if source in ("teams", "outlook", "work_email"):
            scores["work"] += 2
            scores["signal"] += 1
        if source == "phone" and "call" in text_lower:
            scores["social"] += 1
            scores["signal"] += 1

        # Determine primary category
        category_scores = {
            "urgent": scores["urgent"],
            "work": scores["work"],
            "social": scores["social"],
            "promotional": scores["promotional"],
            "financial": scores["financial"],
            "system": scores["system"],
        }
        primary = max(category_scores, key=category_scores.get) if max(category_scores.values()) > 0 else "general"

        # Signal vs noise score (0-100)
        signal = scores["signal"]
        noise = scores["noise"]
        if primary == "promotional":
            signal_score = max(0, 20 - noise * 10)
        elif primary == "urgent":
            signal_score = min(100, 60 + signal * 10)
        elif primary == "financial":
            signal_score = min(100, 50 + signal * 8)
        elif primary == "work":
            signal_score = min(100, 40 + signal * 8)
        else:
            signal_score = min(100, 30 + signal * 5)

        # Priority mapping
        if primary == "urgent" and signal_score >= 60:
            priority = "high"
        elif primary == "financial" and signal_score >= 60:
            priority = "high"
        elif primary == "promotional":
            priority = "low"
        elif primary == "system":
            priority = "low"
        elif signal_score >= 50:
            priority = "normal"
        else:
            priority = "low"

        return {
            "category": primary,
            "signal_score": signal_score,
            "priority": priority,
            "is_noise": signal_score < 25 or primary == "promotional",
            "raw_scores": dict(scores),
        }

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract actionable entities from notification text."""
        entities = {
            "names": [],
            "deadlines": [],
            "amounts": [],
            "action_items": [],
            "locations": [],
        }

        # Names: capitalized words after "from", "to", "by"
        name_patterns = [
            r"from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ]
        for pat in name_patterns:
            for m in re.finditer(pat, text):
                name = m.group(1).strip()
                if len(name) > 2 and name not in entities["names"]:
                    entities["names"].append(name)

        # Deadlines: date/time mentions
        date_patterns = [
            r"(today|tomorrow|tonight|next\s+\w+|by\s+\w+\s+\d{1,2})",
            r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)",
            r"(deadline[s]?\s*:?\s*\w+)",
        ]
        for pat in date_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                dl = m.group(1).strip()
                if dl not in entities["deadlines"]:
                    entities["deadlines"].append(dl)

        # Amounts: currency patterns
        amount_pattern = r"(?:Rs\.?|₹|\$|€|£|USD|EUR|GBP|INR)?\s*([\d,]+(?:\.\d{2})?)"
        for m in re.finditer(amount_pattern, text):
            try:
                amt = float(m.group(1).replace(",", ""))
                if amt > 0:
                    entities["amounts"].append(amt)
            except ValueError:
                pass

        # Action items: imperative sentences
        action_starters = ["please", "need", "required", "action", "review", "approve", "sign", "submit", "confirm", "pay", "complete", "finish", "check", "verify"]
        sentences = re.split(r'[.!?\n]', text)
        for sent in sentences:
            sent_lower = sent.strip().lower()
            for starter in action_starters:
                if sent_lower.startswith(starter) or f" {starter} " in f" {sent_lower} ":
                    action = sent.strip()
                    if action and action not in entities["action_items"]:
                        entities["action_items"].append(action[:120])
                    break

        return entities


class NotificationIngestionEngine:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._running = False
        self._thread: Optional[Thread] = None
        self._seen_hashes: Set[str] = set()
        self._classifier = SmartNotificationClassifier()
        self._recent_notifications: deque = deque(maxlen=200)
        self._stats = {
            "ingested_total": 0,
            "dropped_noise": 0,
            "dropped_duplicate": 0,
            "urgent_pushed": 0,
            "financial_routed": 0,
        }

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
        print(f"[Ingestion] Smart Notification Ingestion Engine started ({interval_seconds}s interval)")

    def stop(self):
        self._running = False

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    def _loop(self, interval: int):
        time.sleep(5)
        while self._running:
            try:
                self._poll_and_ingest()
            except Exception as e:
                print(f"[Ingestion] Polling error: {e}")
            time.sleep(interval)

    def _hash_text(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

    def _is_semantic_duplicate(self, text: str) -> bool:
        """Check if this notification is similar to a recent one (cross-device dedup)."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w{4,}\b', text_lower))
        if not words:
            return False
        for recent in self._recent_notifications:
            recent_words = set(re.findall(r'\b\w{4,}\b', recent.lower()))
            if not recent_words:
                continue
            overlap = len(words & recent_words)
            union = len(words | recent_words)
            if union > 0 and overlap / union > 0.75:
                return True
        return False

    def _ingest_notification(self, text: str, source: str, extra_meta: Dict = None):
        """Ingest a single notification through the full pipeline."""
        if not text or not text.strip():
            return

        # 1. Hash dedup
        h = self._hash_text(f"{source}_{text}")
        if h in self._seen_hashes:
            self._stats["dropped_duplicate"] += 1
            return
        self._seen_hashes.add(h)

        # 2. Semantic dedup (cross-device)
        if self._is_semantic_duplicate(text):
            self._stats["dropped_duplicate"] += 1
            return

        self._recent_notifications.append(text)

        # 3. Classify
        classification = self._classifier.classify(text, source)
        entities = self._classifier.extract_entities(text)

        # 4. Noise gate
        if classification["is_noise"] and classification["signal_score"] < 20:
            self._stats["dropped_noise"] += 1
            return

        self._stats["ingested_total"] += 1

        # 5. Build structured payload
        payload = {
            "text": text,
            "source": source,
            "category": classification["category"],
            "signal_score": classification["signal_score"],
            "priority": classification["priority"],
            "entities": entities,
            "is_noise": classification["is_noise"],
            "timestamp": datetime.now().isoformat(),
        }
        if extra_meta:
            payload.update(extra_meta)

        # 6. Route financial notifications to FinanceGuardian
        if classification["category"] == "financial":
            self._stats["financial_routed"] += 1
            try:
                from core.finance_guardian import get_finance_guardian
                guardian = get_finance_guardian()
                guardian.ingest_from_notification(text, source=f"notification_{source}")
            except Exception as e:
                print(f"[Ingestion] FinanceGuardian routing error: {e}")

        # 7. Ingest into Knowledge Graph
        try:
            knowledge_graph.ingest_text(text, source=f"{source}_notification")
        except Exception as e:
            print(f"[Ingestion] KG ingest error for {source}: {e}")

        # 8. Publish to Neural Bus
        if NEURAL_BUS_AVAILABLE:
            try:
                priority_map = {
                    "high": EventPriority.HIGH,
                    "normal": EventPriority.NORMAL,
                    "low": EventPriority.LOW,
                }
                bus = get_neural_bus()
                bus.publish(
                    domain="notifications",
                    event_type=f"{source}_{classification['category']}",
                    payload=payload,
                    source_module="notification_ingestion",
                    priority=priority_map.get(classification["priority"], EventPriority.NORMAL),
                )
            except Exception as e:
                print(f"[Ingestion] Neural bus publish error: {e}")

        # 9. Learn patterns autonomously from ALL notifications
        try:
            from core.notification_learning import get_notification_learning_engine
            learner = get_notification_learning_engine()
            learner.ingest({
                "text": text,
                "source": source,
                "app": extra_meta.get("app", source) if extra_meta else source,
                "timestamp": payload["timestamp"],
                "payload": extra_meta or {},
            })
        except Exception:
            pass

        # 10. Proactive push for urgent notifications
        if classification["priority"] == "high" and PUSH_AVAILABLE:
            try:
                engine = get_push_engine()
                engine.push(
                    category="ALERT",
                    message=f"[{source.upper()}] {text[:120]}",
                    priority="high",
                    metadata={"source": "notification_ingestion", "category": classification["category"], "entities": entities},
                )
                self._stats["urgent_pushed"] += 1
            except Exception as e:
                print(f"[Ingestion] Push error: {e}")

    def _poll_and_ingest(self):
        phone = PhoneBridge.get_instance()
        ms = MicrosoftBridge.get_instance()

        # 1. Phone Notifications (KDE Connect)
        if phone.is_connected():
            state = phone.get_state()
            notifs = state.get("notifications", [])
            for n in notifs:
                self._ingest_notification(n, "phone")

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
                    self._ingest_notification(full_text, "teams", extra_meta={"sender": sender, "chat": chat})
            except Exception:
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
                    self._ingest_notification(full_text, "outlook", extra_meta={"sender": sender, "subject": subj})
            except Exception:
                pass

        # 4. Unified Device Bridge (Telegram, MQTT, folder sync, Discord, webhook)
        try:
            from integrations.device_bridge import get_device_bridge
            bridge = get_device_bridge()
            if bridge.is_connected():
                msgs = bridge.get_all_messages(limit=10)
                for msg in msgs:
                    text = msg.get("text", "")
                    transport = msg.get("transport_name", "device")
                    if text:
                        self._ingest_notification(text, transport, extra_meta={"transport": transport, "raw": msg})
        except Exception:
            pass

        # Keep sets from growing indefinitely
        if len(self._seen_hashes) > 10000:
            self._seen_hashes = set(list(self._seen_hashes)[-5000:])


def start_ingestion():
    engine = NotificationIngestionEngine.get_instance()
    engine.start()
    return engine