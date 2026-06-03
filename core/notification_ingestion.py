"""
LOVE Notification Ingestion Engine v3 — The Digital Ear

Ingests, classifies, deduplicates, and routes ALL external signals:
- Phone notifications (KDE Connect, ADB, webhook)
- Microsoft 365 (Teams, Outlook)
- Unified Device Bridge (Telegram, Discord, MQTT, webhook)
- WhatsApp Web (if available)
- System notifications (if available)

Features:
  - Smart classification with confidence scoring
  - Temporal + semantic deduplication (prevents spam)
  - Entity extraction (names, deadlines, amounts, action items)
  - Actionable detection (can LOVE reply/dismiss/snooze?)
  - Orchestrator-aware delivery (respects focus mode, system load)
  - NeuralBus events for cross-module awareness
  - FinanceGuardian routing for bank notifications
  - Knowledge Graph ingestion for relational memory
"""

import json
import re
import time
import hashlib
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Set, Optional, Dict, List, Any
from collections import defaultdict, deque

from core import knowledge_graph
from integrations.phone_bridge import PhoneBridge
from core.execution_guard import log_error

# Microsoft Teams integration (optional)
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
        def is_connected(self): return False
        def poll_notifications(self): return []
        def get_teams_messages(self, limit=5): return []
        def get_unread_emails(self, limit=5): return []
        def get_unread_count(self): return 0
        def get_next_event(self): return None
        def get_context_summary(self): return None

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

# Orchestration Master integration
try:
    from core.master_orchestrator import get_orchestration_master
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False


class SmartNotificationClassifier:
    """Heuristic classifier that scores notifications for relevance and type."""

    URGENT_KEYWORDS = [
        "urgent", "asap", "immediately", "critical", "alert", "warning",
        "failed", "error", "declined", "overdue", "expired", "suspended",
        "locked", "fraud", "unauthorized", "breach", "emergency", "911",
    ]

    WORK_KEYWORDS = [
        "meeting", "deadline", "project", "client", "boss", "manager",
        "report", "review", "interview", "offer", "contract", "invoice",
        "teams", "slack", "jira", "github", "pull request", "deploy",
        "calendar", "schedule", "appointment", "reminder", "standup",
        "sprint", "milestone", "deliverable", "feedback", "approval",
    ]

    SOCIAL_KEYWORDS = [
        "whatsapp", "telegram", "message", "call", "missed call", "voicemail",
        "instagram", "facebook", "twitter", "snapchat", "tiktok", "snap",
        "birthday", "party", "dinner", "lunch", "catch up", "weekend",
        "family", "friend", "invite", "rsvp", "ongoing call",
    ]

    PROMO_KEYWORDS = [
        "sale", "discount", "offer", "coupon", "deal", "promo",
        "subscribe", "newsletter", "promotion", "cashback", "reward",
        "limited time", "act now", "free shipping", "buy now", "shop now",
        "advertisement", "sponsored", "unsubscribe", "flash sale",
    ]

    FINANCE_KEYWORDS = [
        "debited", "credited", "spent", "purchase", "transaction", "payment",
        "withdrawn", "deposit", "balance", "account", "card", "bank",
        "upi", "emi", "loan", "refund", "transfer",
        "investment", "dividend", "stock", "crypto", "bitcoin", "nft",
        "portfolio", "interest", "mortgage", "insurance",
        "inr", "rs.", "rupees", "usd", "$", "€", "£",
    ]

    SYSTEM_KEYWORDS = [
        "update available", "backup complete", "synced", "upload complete",
        "download complete", "battery full", "wifi connected", "bluetooth",
        "app update", "software update", "storage", "cache cleared",
        "system restart", "shutdown", "login", "logout",
    ]

    ACTION_KEYWORDS = [
        "reply", "respond", "call back", "approve", "sign", "review",
        "confirm", "verify", "pay", "submit", "upload", "download",
        "join", "rsvp", "accept", "decline", "reschedule", "forward",
    ]

    def classify(self, text: str, source: str = "unknown") -> Dict[str, Any]:
        text_lower = text.lower()
        scores = defaultdict(int)

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
        if source in ("teams", "outlook", "work_email", "calendar"):
            scores["work"] += 2
            scores["signal"] += 1
        if source in ("phone", "sms") and "call" in text_lower:
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

        # Signal vs noise score
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

        # Detect actionable items
        actionable = any(kw in text_lower for kw in self.ACTION_KEYWORDS)

        return {
            "category": primary,
            "signal_score": signal_score,
            "priority": priority,
            "is_noise": signal_score < 25 or primary == "promotional",
            "raw_scores": dict(scores),
            "is_actionable": actionable,
        }

    def extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {
            "names": [],
            "deadlines": [],
            "amounts": [],
            "action_items": [],
            "locations": [],
            "urls": [],
        }

        # Names
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

        # Deadlines
        date_patterns = [
            r"(today|tomorrow|tonight|next\s+\w+|by\s+\w+\s+\d{1,2})",
            r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)",
            r"(deadline[s]?\s*:?\s*\w+)",
            r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)",
        ]
        for pat in date_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                dl = m.group(1).strip()
                if dl not in entities["deadlines"]:
                    entities["deadlines"].append(dl)

        # Amounts
        amount_pattern = r"(?:Rs\.?|₹|\$|€|£|USD|EUR|GBP|INR)?\s*([\d,]+(?:\.\d{2})?)"
        for m in re.finditer(amount_pattern, text):
            raw = m.group(1).replace(",", "")
            if not raw:
                continue
            try:
                amt = float(raw)
                if amt > 0:
                    entities["amounts"].append(amt)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.notification_ingestion")

        # Action items
        action_starters = ["please", "need", "required", "action", "review", "approve", "sign", "submit", "confirm", "pay", "complete", "finish", "check", "verify", "respond", "reply"]
        sentences = re.split(r'[.!?\n]', text)
        for sent in sentences:
            sent_lower = sent.strip().lower()
            for starter in action_starters:
                if sent_lower.startswith(starter) or f" {starter} " in f" {sent_lower} ":
                    action = sent.strip()
                    if action and action not in entities["action_items"]:
                        entities["action_items"].append(action[:120])
                    break

        # URLs
        url_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
        for m in re.finditer(url_pattern, text):
            entities["urls"].append(m.group(0))

        return entities


class NotificationIngestionEngine:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._running = False
        self._thread: Optional[Thread] = None
        self._seen_hashes: Set[str] = set()
        self._classifier = SmartNotificationClassifier()
        self._recent_texts: deque = deque(maxlen=100)  # runtime dedup cache only
        self._stats = {
            "ingested_total": 0,
            "dropped_noise": 0,
            "dropped_duplicate": 0,
            "urgent_pushed": 0,
            "financial_routed": 0,
            "actionable_detected": 0,
        }
        self._pending_actionable: deque = deque(maxlen=50)
        self._last_alert_time: float = 0
        self._alert_cooldown: float = 30  # seconds between alerts
        self._cm = None

    def _get_cm(self):
        if self._cm is None:
            from core.consolidated_memory import get_consolidated_memory
            self._cm = get_consolidated_memory()
        return self._cm

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
        # Auto-start ntfy bridge so notifications flow immediately
        try:
            from integrations.ntfy_bridge import NtfyBridge
            NtfyBridge.get_instance().start()
        except Exception:
            pass
        # Register notification learner as ConsolidatedMemory callback
        try:
            from core.notification_learning import get_notification_learning_engine
            learner = get_notification_learning_engine()
            self._get_cm().register_learner(lambda entry: learner.ingest({
                "text": entry.get("payload", {}).get("text", ""),
                "source": entry.get("payload", {}).get("source", "unknown"),
                "app": entry.get("payload", {}).get("source", "unknown"),
                "timestamp": entry.get("timestamp", ""),
                "payload": entry.get("payload", {}),
            }))
            print("[Ingestion] Notification learner registered with ConsolidatedMemory")
        except Exception:
            pass
        print(f"[Ingestion] Notification Ingestion Engine v3 started ({interval_seconds}s interval)")

    def stop(self):
        self._running = False

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    def get_pending_actionable(self) -> List[Dict]:
        return list(self._pending_actionable)

    def get_recent_notifications(self, hours: int = 24, limit: int = 200) -> List[Dict]:
        """Get recent notifications from persistent ConsolidatedMemory (survives restart)."""
        try:
            raw = self._get_cm().get_recent(domain="notification", hours=hours, limit=limit)
            structured = []
            for entry in raw:
                payload = entry.get("payload", {})
                structured.append({
                    "category": payload.get("category", entry.get("event_type", "notification")),
                    "message": payload.get("text", entry.get("text_for_search", "")),
                    "ts": payload.get("timestamp", entry.get("timestamp", "")),
                    "source": payload.get("source", ""),
                    "priority": payload.get("priority", "normal"),
                    "signal_score": payload.get("signal_score", 0),
                })
            return structured
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.notification_ingestion")
            return []

    def dismiss_actionable(self, index: int):
        try:
            pending = list(self._pending_actionable)
            if 0 <= index < len(pending):
                pending.pop(index)
                self._pending_actionable = deque(pending, maxlen=50)
                return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.notification_ingestion")
        return False

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
        text_lower = text.lower()
        words = set(re.findall(r'\b\w{4,}\b', text_lower))
        if not words:
            return False
        for recent in self._recent_texts:
            recent_words = set(re.findall(r'\b\w{4,}\b', recent.lower()))
            if not recent_words:
                continue
            overlap = len(words & recent_words)
            union = len(words | recent_words)
            if union > 0 and overlap / union > 0.75:
                return True
        return False

    def _ingest_notification(self, text: str, source: str, extra_meta: Dict = None):
        if not text or not text.strip():
            return

        # 1. Hash dedup
        h = self._hash_text(f"{source}_{text}")
        if h in self._seen_hashes:
            self._stats["dropped_duplicate"] += 1
            return
        self._seen_hashes.add(h)

        # 2. Semantic dedup
        if self._is_semantic_duplicate(text):
            self._stats["dropped_duplicate"] += 1
            return

        self._recent_texts.append(text)

        # 3. Classify
        classification = self._classifier.classify(text, source)
        entities = self._classifier.extract_entities(text)

        # 4. Noise gate
        if classification["is_noise"] and classification["signal_score"] < 20:
            self._stats["dropped_noise"] += 1
            return

        self._stats["ingested_total"] += 1

        # 5. Build payload
        payload = {
            "text": text,
            "source": source,
            "category": classification["category"],
            "signal_score": classification["signal_score"],
            "priority": classification["priority"],
            "entities": entities,
            "is_noise": classification["is_noise"],
            "is_actionable": classification["is_actionable"],
            "timestamp": datetime.now().isoformat(),
        }
        if extra_meta:
            payload.update(extra_meta)

        # Track actionable
        if classification["is_actionable"]:
            self._stats["actionable_detected"] += 1
            self._pending_actionable.append(payload)

        # 6. Persist to Consolidated Memory (survives restart + semantic recall)
        try:
            self._get_cm().write(
                domain="notification",
                event_type=classification["category"],
                payload=payload,
                text_for_search=text,
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.notification_ingestion")

        # 7. Route financial
        if classification["category"] == "financial":
            self._stats["financial_routed"] += 1
            try:
                from core.finance_guardian import get_finance_guardian
                guardian = get_finance_guardian()
                guardian.ingest_from_notification(text, source=f"notification_{source}")
            except Exception as e:
                print(f"[Ingestion] FinanceGuardian routing error: {e}")

        # 8. Knowledge Graph
        try:
            knowledge_graph.ingest_text(text, source=f"{source}_notification")
        except Exception as e:
            print(f"[Ingestion] KG ingest error for {source}: {e}")

        # 9. Neural Bus
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

        # 10. Pattern learning (also handled by CM learner callback, but keep direct for safety)
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
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.notification_ingestion")

        # 11. Auto-create tasks/missions from actionable notifications
        self._route_to_action_system(payload, classification)

        # 12. Delivery to user (via orchestrator if available, else direct push)
        if classification["priority"] == "high":
            self._deliver_to_user(payload)

    def _route_to_action_system(self, payload: Dict, classification: Dict):
        """Intelligently route notifications to task/mission systems so data is actually used."""
        category = classification["category"]
        text = payload.get("text", "")
        source = payload.get("source", "")
        is_actionable = classification.get("is_actionable", False)

        # ── WORK / CALENDAR → Executive Tasks ──
        if category in ("work", "system") or "calendar" in source.lower():
            try:
                from core.executive import add_task
                # Extract deadline if present
                entities = payload.get("entities", {})
                deadlines = entities.get("deadlines", [])
                deadline = deadlines[0] if deadlines else None
                add_task(
                    text=f"[{source.upper()}] {text[:120]}",
                    deadline=deadline,
                    source="notification"
                )
                print(f"[Ingestion] Auto-created task from {source} notification")
            except Exception as e:
                log_error(e, module="core.notification_ingestion")

        # ── ACTIONABLE → Autonomous Mission Queue ──
        if is_actionable and category in ("work", "urgent", "financial"):
            try:
                from core.autonomous_mission_queue import get_mission_queue
                mq = get_mission_queue()
                mq.add_mission(
                    title=text[:100],
                    domain=category,
                    priority=payload.get("priority", "normal"),
                    description=f"Auto-created from {source} notification. Full text: {text}",
                    source="notification_ingestion"
                )
                print(f"[Ingestion] Auto-created mission from actionable {source} notification")
            except Exception as e:
                log_error(e, module="core.notification_ingestion")

        # ── SOCIAL / CALL → Relationship memory ──
        if category == "social" or "call" in text.lower():
            try:
                # Extract name from text if possible
                names = payload.get("entities", {}).get("names", [])
                sender_name = names[0] if names else source
                self._get_cm().write(
                    domain="relationships",
                    event_type="interaction",
                    payload={
                        "text": text,
                        "source": source,
                        "category": category,
                        "person": sender_name,
                        "timestamp": datetime.now().isoformat(),
                    },
                    text_for_search=f"{sender_name}: {text}",
                )
            except Exception as e:
                log_error(e, module="core.notification_ingestion")

    def _deliver_to_user(self, payload: Dict):
        """Deliver notification to user, respecting orchestrator state."""
        now = time.time()
        if now - self._last_alert_time < self._alert_cooldown:
            return
        self._last_alert_time = now

        text = payload.get("text", "")
        source = payload.get("source", "unknown")
        category = payload.get("category", "general")

        # Check orchestrator state
        if ORCHESTRATOR_AVAILABLE:
            try:
                om = get_orchestration_master()
                state = om.get_system_summary()
                if state.get("focus_mode"):
                    # Don't alert during focus mode
                    return
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.notification_ingestion")

        if PUSH_AVAILABLE:
            try:
                engine = get_push_engine()
                engine.push(
                    category="ALERT",
                    message=f"[{source.upper()}] {text[:120]}",
                    priority="high",
                    metadata={"source": "notification_ingestion", "category": category, "entities": payload.get("entities", {})},
                )
                self._stats["urgent_pushed"] += 1
            except Exception as e:
                print(f"[Ingestion] Push error: {e}")

    def _poll_and_ingest(self):
        phone = PhoneBridge.get_instance()
        ms = MicrosoftBridge.get_instance()

        # 1. Phone Notifications
        if phone.is_connected():
            try:
                state = phone.get_state()
                notifs = state.get("notifications", [])
                for n in notifs:
                    self._ingest_notification(n, "phone")
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.notification_ingestion")

        # 2. Microsoft Teams
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
                    self._ingest_notification(full_text, "teams", extra_meta={"sender": sender, "chat": chat, "type": "chat"})
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.notification_ingestion")

            # 3. Microsoft Outlook
            try:
                emails = ms.get_unread_emails(limit=5)
                for email in emails:
                    subj = email.get("subject", "")
                    sender = email.get("from", "Unknown")
                    preview = email.get("preview", "")
                    if not subj:
                        continue
                    full_text = f"Email from {sender}: {subj}. {preview}"
                    self._ingest_notification(full_text, "outlook", extra_meta={"sender": sender, "subject": subj, "type": "email"})
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.notification_ingestion")

            # 4. Calendar events
            try:
                event = ms.get_next_event()
                if event:
                    title = event.get("title", "")
                    start_time = event.get("start", "")
                    if title:
                        self._ingest_notification(f"Upcoming: {title} at {start_time}", "calendar", extra_meta={"type": "calendar", "start": start_time})
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.notification_ingestion")

        # 5. Unified Device Bridge
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
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.notification_ingestion")

        # 6. WhatsApp Web (if available)
        try:
            from integrations.whatsapp_bridge import get_whatsapp_bridge
            wa = get_whatsapp_bridge()
            if wa and wa.is_connected():
                msgs = wa.get_messages(limit=5)
                for msg in msgs:
                    text = msg.get("text", "")
                    sender = msg.get("sender", "Unknown")
                    if text:
                        self._ingest_notification(f"{sender}: {text}", "whatsapp", extra_meta={"sender": sender, "type": "chat"})
        except (ModuleNotFoundError, ImportError):
            pass  # WhatsApp bridge not installed — optional
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.notification_ingestion")

        # 7. Ntfy Bridge
        try:
            from integrations.ntfy_bridge import NtfyBridge
            ntfy = NtfyBridge.get_instance()
            if ntfy.is_connected():
                msgs = ntfy.get_messages(limit=10)
                for msg in msgs:
                    text = msg.get("text", "")
                    if text:
                        self._ingest_notification(text, "ntfy", extra_meta={"type": "ntfy", "raw": msg})
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.notification_ingestion")

        # Keep sets from growing indefinitely
        if len(self._seen_hashes) > 10000:
            self._seen_hashes = set(list(self._seen_hashes)[-5000:])


def start_ingestion():
    engine = NotificationIngestionEngine.get_instance()
    engine.start()
    return engine
