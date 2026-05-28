"""
LOVE Notification Learning Engine — Autonomous Pattern Discovery

Zero-touch. LOVE passively observes ALL notifications across devices,
learns your patterns, and builds a rich model of your behavior:
  - Financial: merchants, spending by time/location, recurring charges
  - Location: where you are, commute patterns, geofence triggers
  - Mood: stress signals, social activity, sleep patterns from timestamps
  - Social: who messages you, when, what apps, response latency
  - Anomalies: deviations from learned patterns → proactive alerts

No forwarding required. LOVE reads everything it's connected to.
"""

import json
import os
import re
import time
import threading
from collections import defaultdict, deque, Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

DATA_DIR = Path(__file__).parent.parent / "data"
LEARNED_STATE_FILE = DATA_DIR / "learned_state.json"
LEARNED_LOG = DATA_DIR / "learned_events.jsonl"
NOTIFICATION_HISTORY = DATA_DIR / "notification_history.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)

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


# ═════════════════════════════════════════════════════════════════════════════
#  USER BEHAVIOR PROFILE — Persistent learned model
# ═════════════════════════════════════════════════════════════════════════════

class UserBehaviorProfile:
    """
    Persistent profile built from observed notifications.
    Stored as JSON and reloaded on restart.
    """

    def __init__(self, data: Optional[Dict] = None):
        self._data = data or {}
        self._dirty = False

        # Spending
        self.merchants: Counter = Counter(self._data.get("merchants", {}))
        self.merchant_amounts: Dict[str, List[float]] = defaultdict(list, self._data.get("merchant_amounts", {}))
        self.spending_by_hour: Counter = Counter(self._data.get("spending_by_hour", {}))
        self.spending_by_day: Counter = Counter(self._data.get("spending_by_day", {}))
        self.recurring_charges: List[Dict] = self._data.get("recurring_charges", [])
        self.total_spent: float = self._data.get("total_spent", 0.0)
        self.total_transactions: int = self._data.get("total_transactions", 0)

        # Location
        self.known_locations: Set[str] = set(self._data.get("known_locations", []))
        self.location_history: deque = deque(self._data.get("location_history", []), maxlen=1000)
        self.location_by_hour: Dict[str, Counter] = defaultdict(Counter, {k: Counter(v) for k, v in self._data.get("location_by_hour", {}).items()})

        # Social
        self.frequent_contacts: Counter = Counter(self._data.get("frequent_contacts", {}))
        self.active_apps: Counter = Counter(self._data.get("active_apps", {}))
        self.message_times: deque = deque(self._data.get("message_times", []), maxlen=500)

        # Mood / Health signals
        self.sleep_window: Optional[Tuple[int, int]] = None  # inferred (bedtime, wake_time)
        self.stress_signals: int = self._data.get("stress_signals", 0)
        self.positive_signals: int = self._data.get("positive_signals", 0)
        self.notification_velocity: deque = deque(self._data.get("notification_velocity", []), maxlen=100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merchants": dict(self.merchants),
            "merchant_amounts": {k: v[-20:] for k, v in self.merchant_amounts.items()},
            "spending_by_hour": dict(self.spending_by_hour),
            "spending_by_day": dict(self.spending_by_day),
            "recurring_charges": self.recurring_charges,
            "total_spent": self.total_spent,
            "total_transactions": self.total_transactions,
            "known_locations": list(self.known_locations),
            "location_history": list(self.location_history)[-200:],
            "location_by_hour": {k: dict(v) for k, v in self.location_by_hour.items()},
            "frequent_contacts": dict(self.frequent_contacts),
            "active_apps": dict(self.active_apps),
            "message_times": list(self.message_times)[-100:],
            "sleep_window": self.sleep_window,
            "stress_signals": self.stress_signals,
            "positive_signals": self.positive_signals,
            "notification_velocity": list(self.notification_velocity),
        }

    def save(self):
        try:
            LEARNED_STATE_FILE.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
            self._dirty = False
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════════
#  ENTITY EXTRACTORS — Lightweight regex-based, no ML dependencies
# ═════════════════════════════════════════════════════════════════════════════

class EntityExtractor:
    """Extract structured entities from raw notification text."""

    # Currency patterns: ₹1,234.56, $12.34, 1,234, EUR 50, etc.
    MONEY_RE = re.compile(
        r"[\₹\$\£\€]?\s?\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?|\d+\.\d{2}|[\₹\$\£\€]\s?\d+",
        re.IGNORECASE,
    )

    # Percentages
    PERCENT_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?%")

    # Time
    TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\b")

    # Dates
    DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b")

    # Merchant / sender names (common patterns)
    MERCHANT_RE = re.compile(
        r"(?:from|at|by|to|merchant|via)\s+([A-Z][A-Za-z0-9\s&]{2,40})",
        re.IGNORECASE,
    )

    # UPI / transaction IDs
    TXN_RE = re.compile(r"(?:txn|transaction|ref|upi)[#\s:\-]*([A-Za-z0-9]{8,30})", re.IGNORECASE)

    # App names from structured notifications
    KNOWN_MERCHANTS = {
        "amazon", "flipkart", "myntra", "swiggy", "zomato", "uber", "ola",
        "paytm", "phonepe", "gpay", "google pay", "bhim", "cred", "slice",
        "amazon pay", "netflix", "spotify", "youtube", "prime",
        "apple", "app store", "play store", "steam",
    }

    @classmethod
    def extract(cls, text: str, app: str = "") -> Dict[str, Any]:
        """Extract all entities from a notification text."""
        text_lower = text.lower()
        entities = {
            "amounts": cls._extract_amounts(text),
            "percentages": cls.PERCENT_RE.findall(text),
            "times": cls.TIME_RE.findall(text),
            "dates": cls.DATE_RE.findall(text),
            "transaction_ids": cls._extract_txn_ids(text),
            "merchant": cls._extract_merchant(text, app),
            "app": app,
        }
        return entities

    @classmethod
    def _extract_amounts(cls, text: str) -> List[Dict]:
        """Extract monetary values with currency."""
        results = []
        for m in cls.MONEY_RE.finditer(text):
            val = m.group()
            # Determine currency
            currency = "UNKNOWN"
            if "₹" in val:
                currency = "INR"
            elif "$" in val:
                currency = "USD"
            elif "£" in val:
                currency = "GBP"
            elif "€" in val:
                currency = "EUR"
            # Clean number
            clean = re.sub(r"[\₹\$\£\€\s,]", "", val)
            try:
                num = float(clean)
                if 0.01 < num < 1000000:  # Sanity range
                    results.append({"raw": val, "value": num, "currency": currency})
            except ValueError:
                pass
        return results

    @classmethod
    def _extract_txn_ids(cls, text: str) -> List[str]:
        """Extract transaction/reference IDs."""
        ids = []
        for m in cls.TXN_RE.finditer(text):
            ids.append(m.group(1))
        return ids

    @classmethod
    def _extract_merchant(cls, text: str, app: str) -> Optional[str]:
        """Extract merchant name from text or app name."""
        text_lower = text.lower()

        # 1. Known merchant list
        for known in cls.KNOWN_MERCHANTS:
            if known in text_lower:
                return known.title()

        # 2. Pattern match
        m = cls.MERCHANT_RE.search(text)
        if m:
            merchant = m.group(1).strip()
            if len(merchant) > 2:
                return merchant

        # 3. Fall back to app name if it looks like a merchant
        if app and app.lower() not in {"android system", "settings", "system ui", "google play services"}:
            return app

        return None


# ═════════════════════════════════════════════════════════════════════════════
#  PATTERN LEARNERS — Statistical pattern detection
# ═════════════════════════════════════════════════════════════════════════════

class PatternLearner:
    """Statistical learning engine that updates the user profile."""

    @staticmethod
    def learn_financial(notification: Dict, profile: UserBehaviorProfile):
        """Update financial profile from a bank/transaction notification."""
        text = notification.get("text", "")
        entities = EntityExtractor.extract(text, notification.get("app", ""))
        amounts = entities.get("amounts", [])
        merchant = entities.get("merchant")

        # Determine direction (debit vs credit)
        direction = "unknown"
        text_lower = text.lower()
        if any(k in text_lower for k in ("debited", "spent", "paid", "purchase", "withdrawn", "deducted")):
            direction = "debit"
        elif any(k in text_lower for k in ("credited", "received", "refund", "deposit", "added")):
            direction = "credit"

        # Log merchant
        if merchant:
            profile.merchants[merchant] += 1

        # Log amounts
        for amt in amounts:
            val = amt["value"]
            if direction == "debit":
                profile.total_spent += val
                if merchant:
                    profile.merchant_amounts[merchant].append(val)
            profile.total_transactions += 1

            # Spending by hour
            try:
                ts = notification.get("timestamp", "")
                if ts:
                    hour = datetime.fromisoformat(ts.replace("Z", "+00:00")).hour
                    profile.spending_by_hour[str(hour)] += 1
            except Exception:
                pass

            # Detect recurring charge
            if merchant and direction == "debit":
                PatternLearner._check_recurring(profile, merchant, val, notification.get("timestamp"))

    @staticmethod
    def _check_recurring(profile: UserBehaviorProfile, merchant: str, amount: float, timestamp: str):
        """Detect if a charge is recurring (same merchant, similar amount, ~30 days apart)."""
        now = datetime.now()
        for rc in profile.recurring_charges:
            if rc.get("merchant") == merchant:
                last_seen = datetime.fromisoformat(rc.get("last_seen", "2000-01-01"))
                if abs(rc.get("amount", 0) - amount) / max(rc["amount"], 1) < 0.15:
                    days_diff = (now - last_seen).days
                    if 25 <= days_diff <= 35:
                        rc["last_seen"] = timestamp or now.isoformat()
                        rc["count"] = rc.get("count", 1) + 1
                        return

        # New potential recurring
        profile.recurring_charges.append({
            "merchant": merchant,
            "amount": amount,
            "first_seen": timestamp or now.isoformat(),
            "last_seen": timestamp or now.isoformat(),
            "count": 1,
        })

    @staticmethod
    def learn_location(notification: Dict, profile: UserBehaviorProfile):
        """Update location profile from location-aware notifications."""
        text = notification.get("text", "")
        text_lower = text.lower()

        locations = {
            "home": ["home", "at home", "reached home", "left home"],
            "office": ["office", "at work", "reached office", "workplace", "desk"],
            "gym": ["gym", "fitness", "workout", "exercise"],
            "transit": ["driving", "in transit", "commuting", "train", "bus", "metro", "airport", "flight"],
            "restaurant": ["restaurant", "dining", "cafe", "food delivery"],
        }

        detected = None
        for loc, keywords in locations.items():
            if any(kw in text_lower for kw in keywords):
                detected = loc
                break

        # Also check explicit payload location
        payload = notification.get("payload", {})
        if not detected and payload.get("location"):
            detected = payload["location"].lower()

        if detected:
            profile.known_locations.add(detected)
            profile.location_history.append({
                "location": detected,
                "timestamp": notification.get("timestamp", datetime.now().isoformat()),
            })

            # Location by hour
            try:
                ts = notification.get("timestamp", "")
                if ts:
                    hour = datetime.fromisoformat(ts.replace("Z", "+00:00")).hour
                    profile.location_by_hour[detected][str(hour)] += 1
            except Exception:
                pass

    @staticmethod
    def learn_mood(notification: Dict, profile: UserBehaviorProfile):
        """Infer mood signals from notification patterns."""
        text = notification.get("text", "")
        text_lower = text.lower()
        app = notification.get("app", "").lower()

        # Stress signals
        stress_keywords = ["overdue", "failed", "declined", "urgent", "critical",
                           "deadline", "penalty", "fine", "fraud", "suspended",
                           "limited", "blocked", "error", "issue", "problem"]
        if any(kw in text_lower for kw in stress_keywords):
            profile.stress_signals += 1

        # Positive signals
        positive_keywords = ["congratulations", "success", "approved", "completed",
                             "delivered", "thank you", "reward", "bonus", "gift",
                             "welcome", "confirmed", "matched", "won"]
        if any(kw in text_lower for kw in positive_keywords):
            profile.positive_signals += 1

        # Social velocity — many social apps = active social life
        social_apps = {"whatsapp", "instagram", "telegram", "snapchat", "messenger", "signal", "discord"}
        if app in social_apps:
            profile.message_times.append(notification.get("timestamp", datetime.now().isoformat()))

        # Notification velocity (notifications per 10-min window)
        profile.notification_velocity.append({
            "timestamp": notification.get("timestamp", datetime.now().isoformat()),
            "app": app,
        })

    @staticmethod
    def learn_social(notification: Dict, profile: UserBehaviorProfile):
        """Update social/contact patterns."""
        app = notification.get("app", "")
        if app:
            profile.active_apps[app] += 1

        # Try extract sender/contact name
        text = notification.get("text", "")
        # "John: message" or "From: John" patterns
        sender_match = re.search(r'(?:from[:\s]+|"?)([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)', text)
        if sender_match:
            sender = sender_match.group(1)
            if len(sender) > 2:
                profile.frequent_contacts[sender] += 1

    @staticmethod
    def detect_anomaly(notification: Dict, profile: UserBehaviorProfile) -> Optional[str]:
        """Compare notification against learned profile. Returns anomaly description or None."""
        text = notification.get("text", "")
        text_lower = text.lower()
        entities = EntityExtractor.extract(text, notification.get("app", ""))
        anomalies = []

        # 1. Unusual spending amount for merchant
        merchant = entities.get("merchant")
        amounts = entities.get("amounts", [])
        if merchant and amounts:
            merchant_amts = profile.merchant_amounts.get(merchant, [])
            if len(merchant_amts) >= 3:
                avg = sum(merchant_amts) / len(merchant_amts)
                val = amounts[0]["value"]
                if val > avg * 3:
                    anomalies.append(f"Unusually high amount at {merchant}: {val} (avg {avg:.0f})")
                elif val < avg * 0.1 and val > 100:
                    anomalies.append(f"Unusually low amount at {merchant}: {val}")

        # 2. New merchant
        if merchant and merchant not in profile.merchants and any(k in text_lower for k in ("debited", "spent", "purchase")):
            anomalies.append(f"First transaction with {merchant}")

        # 3. Unusual time
        try:
            ts = notification.get("timestamp", "")
            if ts:
                hour = datetime.fromisoformat(ts.replace("Z", "+00:00")).hour
                if hour < 5 or hour > 23:
                    anomalies.append("Late night transaction")
        except Exception:
            pass

        # 4. Location mismatch
        payload = notification.get("payload", {})
        if payload.get("location"):
            loc = payload["location"].lower()
            hour_locs = dict(profile.location_by_hour.get(loc, Counter()))
            if hour_locs and sum(hour_locs.values()) > 5:
                # Check if user is usually elsewhere at this hour
                pass

        # 5. High velocity anomaly
        recent = [v for v in profile.notification_velocity
                  if (datetime.now() - datetime.fromisoformat(v["timestamp"].replace("Z", "+00:00"))).total_seconds() < 600]
        if len(recent) > 20:
            anomalies.append("Unusually high notification rate (possible spam attack)")

        return " | ".join(anomalies) if anomalies else None


# ═════════════════════════════════════════════════════════════════════════════
#  NOTIFICATION LEARNING ENGINE — Main singleton
# ═════════════════════════════════════════════════════════════════════════════

class NotificationLearningEngine:
    """
    Singleton that ingests ALL notifications, learns patterns, detects anomalies,
    and feeds insights to other modules autonomously.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._profile: UserBehaviorProfile = self._load_profile()
        self._recent_notifications: deque = deque(maxlen=500)
        self._insights_queue: deque = deque(maxlen=100)
        self._learn_callbacks: List = []

    @classmethod
    def get_instance(cls) -> "NotificationLearningEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = NotificationLearningEngine()
            return cls._instance

    def _load_profile(self) -> UserBehaviorProfile:
        if not LEARNED_STATE_FILE.exists():
            return UserBehaviorProfile()
        try:
            data = json.loads(LEARNED_STATE_FILE.read_text(encoding="utf-8"))
            return UserBehaviorProfile(data)
        except Exception:
            return UserBehaviorProfile()

    # ─── Public API ──────────────────────────────────────────────────────────

    def ingest(self, notification: Dict):
        """
        Ingest a single notification and learn from it.
        Call this from notification_ingestion, device_bridge, or any source.
        """
        if not notification or not isinstance(notification, dict):
            return

        text = notification.get("text", "")
        if not text:
            return

        # Normalize
        entry = {
            "text": text,
            "app": notification.get("app", notification.get("source", "unknown")),
            "source": notification.get("source", "unknown"),
            "timestamp": notification.get("timestamp", datetime.now().isoformat()),
            "payload": notification.get("payload", {}),
        }

        self._recent_notifications.append(entry)
        self._persist_raw(entry)

        # Extract entities
        entities = EntityExtractor.extract(text, entry["app"])
        entry["entities"] = entities

        # Learn patterns
        PatternLearner.learn_financial(entry, self._profile)
        PatternLearner.learn_location(entry, self._profile)
        PatternLearner.learn_mood(entry, self._profile)
        PatternLearner.learn_social(entry, self._profile)

        # Detect anomalies
        anomaly = PatternLearner.detect_anomaly(entry, self._profile)
        if anomaly:
            entry["anomaly"] = anomaly
            self._push_anomaly(entry, anomaly)

        # Auto-save periodically
        if len(self._recent_notifications) % 10 == 0:
            self._profile.save()

        # Publish insight to neural bus
        self._publish_insight(entry)

    def ingest_batch(self, notifications: List[Dict]):
        """Ingest a batch of notifications."""
        for n in notifications:
            self.ingest(n)

    def get_profile(self) -> Dict[str, Any]:
        """Get the full learned user profile."""
        return self._profile.to_dict()

    def get_recent(self, limit: int = 50) -> List[Dict]:
        return list(self._recent_notifications)[-limit:]

    def get_insights(self, limit: int = 20) -> List[Dict]:
        return list(self._insights_queue)[-limit:]

    def get_merchants(self) -> List[Tuple[str, int]]:
        return self._profile.merchants.most_common(20)

    def get_recurring_charges(self) -> List[Dict]:
        return self._profile.recurring_charges

    def predict_location(self, hour: Optional[int] = None) -> Optional[str]:
        """Predict most likely location at given hour (default: now)."""
        if hour is None:
            hour = datetime.now().hour
        hour_str = str(hour)
        best_loc = None
        best_count = 0
        for loc, counter in self._profile.location_by_hour.items():
            count = counter.get(hour_str, 0)
            if count > best_count:
                best_count = count
                best_loc = loc
        return best_loc

    def estimate_mood(self) -> Dict[str, Any]:
        """Estimate current mood from recent signals."""
        recent_stress = self._profile.stress_signals
        recent_positive = self._profile.positive_signals
        total = recent_stress + recent_positive
        if total == 0:
            return {"mood": "neutral", "confidence": 0.0, "stress_ratio": 0.0}

        stress_ratio = recent_stress / total
        if stress_ratio > 0.7:
            mood = "stressed"
        elif stress_ratio > 0.4:
            mood = "tense"
        elif recent_positive > recent_stress * 2:
            mood = "positive"
        else:
            mood = "neutral"

        return {
            "mood": mood,
            "confidence": min(total / 50, 1.0),
            "stress_ratio": stress_ratio,
            "stress_signals": recent_stress,
            "positive_signals": recent_positive,
        }

    def detect_financial_anomalies(self) -> List[Dict]:
        """Scan recent notifications for financial anomalies."""
        anomalies = []
        for n in self._recent_notifications:
            if "anomaly" in n and any(k in n.get("text", "").lower() for k in
                                       ["debited", "credited", "spent", "purchase", "transaction"]):
                anomalies.append({
                    "text": n["text"][:200],
                    "anomaly": n["anomaly"],
                    "timestamp": n["timestamp"],
                    "app": n["app"],
                })
        return anomalies

    # ─── Internal ──────────────────────────────────────────────────────────

    def _persist_raw(self, entry: Dict):
        try:
            with open(NOTIFICATION_HISTORY, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    def _push_anomaly(self, entry: Dict, anomaly_desc: str):
        """Push anomaly alert to user."""
        self._insights_queue.append({
            "type": "anomaly",
            "description": anomaly_desc,
            "text": entry["text"][:150],
            "timestamp": entry["timestamp"],
        })

        if PUSH_AVAILABLE:
            try:
                engine = get_push_engine()
                engine.push(
                    category="anomaly_detected",
                    message=f"🚨 Anomaly: {anomaly_desc} — {entry['text'][:100]}",
                    priority="high",
                    metadata={"anomaly": anomaly_desc, "source": entry["source"]},
                )
            except Exception:
                pass

    def _publish_insight(self, entry: Dict):
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            bus.publish(
                domain="learning", event_type="notification_learned",
                payload={
                    "text_preview": entry["text"][:100],
                    "app": entry["app"],
                    "source": entry["source"],
                    "entities": entry.get("entities", {}),
                    "anomaly": entry.get("anomaly"),
                },
                source_module="notification_learning",
                priority=EventPriority.HIGH if entry.get("anomaly") else EventPriority.LOW,
            )
        except Exception:
            pass

    # ─── Lifecycle ───────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._save_loop, daemon=True, name="LOVE-NotifLearn")
        self._thread.start()
        print("[NotificationLearning] Started. Autonomous pattern learning active.")

    def stop(self):
        self._running = False
        self._profile.save()

    def _save_loop(self):
        """Periodic save of learned profile."""
        time.sleep(60)
        while self._running:
            try:
                self._profile.save()
                time.sleep(300)
            except Exception as e:
                print(f"[NotificationLearning] Save error: {e}")
                time.sleep(300)


# ═════════════════════════════════════════════════════════════════════════════
#  SUGGESTION ENGINE — What should LOVE do based on learned patterns?
# ═════════════════════════════════════════════════════════════════════════════

class SuggestionEngine:
    """
    Generates autonomous suggestions/actions based on learned patterns.
    E.g., "User usually orders food at 1 PM — pre-warm Swiggy data"
    """

    def __init__(self, profile: UserBehaviorProfile):
        self._profile = profile

    def get_suggestions(self) -> List[Dict]:
        """Return list of current autonomous suggestions."""
        suggestions = []
        now = datetime.now()

        # 1. Recurring charge reminder
        for rc in self._profile.recurring_charges:
            last = datetime.fromisoformat(rc.get("last_seen", "2000-01-01"))
            days_since = (now - last).days
            if days_since > 25:
                suggestions.append({
                    "type": "upcoming_bill",
                    "message": f"💳 {rc['merchant']} bill may be due soon (last: {days_since} days ago, ~₹{rc['amount']:.0f})",
                    "priority": "normal",
                    "action": None,
                })

        # 2. Location-based suggestions
        predicted = None
        try:
            predicted = self._predict_next_location()
        except Exception:
            pass
        if predicted:
            suggestions.append({
                "type": "location_prediction",
                "message": f"📍 Likely heading to {predicted['location']} around {predicted['time']}",
                "priority": "low",
                "action": None,
            })

        # 3. Mood-based suggestion
        mood = self._estimate_mood()
        if mood["mood"] == "stressed" and mood["confidence"] > 0.5:
            suggestions.append({
                "type": "mood_intervention",
                "message": "🧘 Stress signals elevated. Consider a break.",
                "priority": "normal",
                "action": None,
            })

        # 4. Spending alert
        today_spent = self._estimate_today_spending()
        if today_spent > 5000:  # INR threshold
            suggestions.append({
                "type": "spending_alert",
                "message": f"💰 High spending today: ~₹{today_spent:.0f}",
                "priority": "low",
                "action": None,
            })

        return suggestions

    def _predict_next_location(self) -> Optional[Dict]:
        """Predict where user will be next based on time-of-day patterns."""
        now = datetime.now()
        next_hour = (now.hour + 1) % 24
        best_loc = None
        best_count = 0
        for loc, counter in self._profile.location_by_hour.items():
            count = counter.get(str(next_hour), 0)
            if count > best_count:
                best_count = count
                best_loc = loc
        if best_loc and best_count > 2:
            return {"location": best_loc, "time": f"{next_hour}:00"}
        return None

    def _estimate_mood(self) -> Dict:
        total = self._profile.stress_signals + self._profile.positive_signals
        if total == 0:
            return {"mood": "neutral", "confidence": 0.0}
        stress_ratio = self._profile.stress_signals / total
        return {
            "mood": "stressed" if stress_ratio > 0.6 else "positive" if stress_ratio < 0.2 else "neutral",
            "confidence": min(total / 30, 1.0),
        }

    def _estimate_today_spending(self) -> float:
        today = datetime.now().strftime("%Y-%m-%d")
        total = 0.0
        # Very rough: sum of recent amounts from merchant_amounts
        for amounts in self._profile.merchant_amounts.values():
            total += sum(amounts[-5:])  # last 5 per merchant
        return total


# ═════════════════════════════════════════════════════════════════════════════
#  PUBLIC API — Module-level getters
# ═════════════════════════════════════════════════════════════════════════════

def get_notification_learning_engine() -> NotificationLearningEngine:
    return NotificationLearningEngine.get_instance()


def start_notification_learning():
    engine = get_notification_learning_engine()
    engine.start()
    return engine


def stop_notification_learning():
    engine = get_notification_learning_engine()
    engine.stop()
