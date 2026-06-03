"""
LOVE Intelligence Hub — Unified Intelligence Dispatcher

Polls ALL connected sources every N seconds and:
1. Assembles a rich context block for every LLM prompt
2. Pushes critical signals to the proactive push engine
3. Publishes events to the neural bus
4. Detects cross-source patterns (e.g., stressed + meeting + market crash)

Sources managed:
  - System awareness (CPU, battery, active window) — always on
  - Google Calendar + Gmail — when credentials configured
  - Microsoft Outlook + Teams — when credentials configured
  - Phone (KDE Connect / iOS webhook) — when paired
  - GitHub — when token configured
  - Finance/Markets — always on (public APIs)
  - Browser (active tabs + history) — always on
  - Clipboard — always on

Cross-source intelligence patterns:
  - Upcoming meeting + browser is YouTube → gentle nudge to prepare
  - Work limit approaching + critical GitHub notification → push alert
  - Phone battery low + away from charger → warn
  - Market crash + large position → immediate alert
  - No sleep data + late hour + heavy cognitive load → suggest rest
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "love_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
HUB_STATE_FILE = DATA_DIR / "intelligence_hub_state.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

POLL_INTERVAL = 60  # seconds between full hub polls


@dataclass
class IntelligenceSnapshot:
    """Complete intelligence snapshot at one point in time."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    system: Dict = field(default_factory=dict)
    google: Dict = field(default_factory=dict)
    microsoft: Dict = field(default_factory=dict)
    phone: Dict = field(default_factory=dict)
    github: Dict = field(default_factory=dict)
    finance: Dict = field(default_factory=dict)
    browser: Dict = field(default_factory=dict)
    clipboard: Dict = field(default_factory=dict)
    cross_patterns: List[str] = field(default_factory=list)
    active_alerts: List[str] = field(default_factory=list)


class IntelligenceHub:
    """Central intelligence aggregator for LOVE."""

    _instance: Optional["IntelligenceHub"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._snapshot = IntelligenceSnapshot()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._sources: Dict[str, bool] = {}  # source_name → connected
        self._context_cache: str = ""
        self._cache_time: float = 0.0
        self._cache_ttl: float = 45.0  # seconds

    @classmethod
    def get_instance(cls) -> "IntelligenceHub":
        with cls._lock:
            if cls._instance is None:
                cls._instance = IntelligenceHub()
            return cls._instance

    # ── Source Collectors ─────────────────────────────────────────────────────

    def _collect_system(self) -> Dict:
        try:
            from core.awareness import get_awareness
            snap = get_awareness().get_snapshot() if hasattr(get_awareness(), 'get_snapshot') else {}
            # Fallback: get recent snapshot from file
            if not snap:
                snap_file = DATA_DIR / "awareness_snapshot.json"
                if snap_file.exists():
                    snap = json.loads(snap_file.read_text())
            self._sources["system"] = True
            return snap if isinstance(snap, dict) else {}
        except Exception as e:
            self._sources["system"] = False
            return {}

    def _collect_google(self) -> Dict:
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            if not gs.is_connected():
                self._sources["google"] = False
                return {"connected": False}
            events = gs.get_todays_events()
            next_ev = None
            for ev in events:
                mins = ev.get("minutes_away", 9999)
                if mins is not None and mins > 0:
                    next_ev = ev
                    break
            self._sources["google"] = True
            return {
                "connected": True,
                "events_today": len(events),
                "next_event": next_ev,
                "next_event_mins": next_ev.get("minutes_away") if next_ev else None,
            }
        except Exception as e:
            logger.error(f"Error in _collect_google: {e}", exc_info=True)
            self._sources["google"] = False
            return {"connected": False}

    def _collect_microsoft(self) -> Dict:
        try:
            try:
                from integrations.microsoft_bridge import MicrosoftBridge
            except ImportError:
                self._sources["microsoft"] = False
                return {"connected": False}
            ms = MicrosoftBridge.get_instance()
            if not ms.is_connected() if hasattr(ms, 'is_connected') else not ms._connected:
                self._sources["microsoft"] = False
                return {"connected": False}
            unread = ms.get_unread_count()
            next_event = ms.get_next_event()
            self._sources["microsoft"] = True
            return {
                "connected": True,
                "unread_emails": unread,
                "next_meeting": next_event,
            }
        except Exception as e:
            logger.error(f"Error in _collect_microsoft: {e}", exc_info=True)
            self._sources["microsoft"] = False
            return {"connected": False}

    def _collect_phone(self) -> Dict:
        try:
            from integrations.phone_bridge import PhoneBridge
            bridge = PhoneBridge.get_instance()
            state = bridge.get_state()
            self._sources["phone"] = bridge.is_connected()
            return state or {}
        except Exception as e:
            logger.error(f"Error in _collect_phone: {e}", exc_info=True)
            self._sources["phone"] = False
            return {}

    def _collect_github(self) -> Dict:
        try:
            from integrations.github_monitor import get_github_monitor
            gh = get_github_monitor()
            self._sources["github"] = gh.is_connected()
            if not gh.is_connected():
                return {"connected": False}
            return {
                "connected": True,
                "unread_notifications": len(gh.get_notifications(5)),
                "recent_event": (gh.get_recent_events(1) or [{}])[0].get("summary", ""),
            }
        except Exception as e:
            logger.error(f"Error in _collect_github: {e}", exc_info=True)
            self._sources["github"] = False
            return {"connected": False}

    def _collect_finance(self) -> Dict:
        try:
            from integrations.finance_intelligence import get_finance_intelligence
            fi = get_finance_intelligence()
            prices = fi.get_prices()
            self._sources["finance"] = bool(prices)
            return {
                "prices": {k: {"price": v.get("price"), "change_pct": v.get("change_pct")} for k, v in prices.items()},
                "alerts": fi.get_alerts(3),
                "summary": fi.get_price_summary(),
            }
        except Exception as e:
            logger.error(f"Error in _collect_finance: {e}", exc_info=True)
            self._sources["finance"] = False
            return {}

    def _collect_browser(self) -> Dict:
        try:
            from integrations.browser_monitor import get_browser_monitor
            bm = get_browser_monitor()
            tabs = bm.get_active_tabs()
            self._sources["browser"] = True
            return {
                "active_tab": tabs[0] if tabs else {},
                "tab_count": len(tabs),
                "current_context": bm.get_current_context(),
                "recent_topics": bm.get_recent_topics(3),
            }
        except Exception as e:
            logger.error(f"Error in _collect_browser: {e}", exc_info=True)
            self._sources["browser"] = False
            return {}

    def _collect_clipboard(self) -> Dict:
        try:
            from integrations.clipboard_monitor import get_clipboard_monitor
            cm = get_clipboard_monitor()
            signal = cm.get_current_signal()
            self._sources["clipboard"] = True
            return signal or {}
        except Exception as e:
            logger.error(f"Error in _collect_clipboard: {e}", exc_info=True)
            self._sources["clipboard"] = False
            return {}

    # ── Cross-source Pattern Detection ────────────────────────────────────────

    def _detect_patterns(self, snap: IntelligenceSnapshot) -> tuple:
        patterns = []
        alerts = []

        # Meeting imminent + browser is entertainment
        google_next_mins = snap.google.get("next_event_mins")
        browser_ctx = snap.browser.get("current_context", "")
        if google_next_mins is not None and 0 < google_next_mins <= 10:
            title = (snap.google.get("next_event") or {}).get("title", "meeting")
            alerts.append(f"Meeting in {google_next_mins}min: {title[:50]}")
            if any(ent in browser_ctx.lower() for ent in ["youtube", "netflix", "twitch", "reddit"]):
                alerts.append(f"You're on {browser_ctx[:40]} — meeting starts in {google_next_mins}min")

        # Finance alert
        for alert in snap.finance.get("alerts", []):
            if alert.get("severity") == "high":
                alerts.append(f"Market alert: {alert.get('message', '')[:80]}")

        # GitHub urgent
        if snap.github.get("unread_notifications", 0) > 5:
            alerts.append(f"GitHub: {snap.github['unread_notifications']} unread notifications")

        # Phone battery (only alert if phone is actually connected)
        if self._sources.get("phone"):
            battery = snap.phone.get("battery", snap.phone.get("battery_level", 100))
            if battery and int(battery) < 20:
                alerts.append(f"Phone battery low: {battery}%")

        # Work pattern: active window is IDE + late hour
        hour = datetime.now().hour
        sys_snap = snap.system
        active_app = sys_snap.get("active_context", {})
        if isinstance(active_app, dict):
            active_app = active_app.get("active_app", "")
        if any(ide in str(active_app).lower() for ide in ["code", "rider", "pycharm", "visual studio"]):
            if hour >= 22 or hour < 6:
                patterns.append(f"Coding late ({hour:02d}:00) — working in {active_app}")

        # Clipboard has error + coding
        if snap.clipboard.get("type") == "error":
            patterns.append(f"Debugging: {snap.clipboard.get('signal', '')[:80]}")

        return patterns, alerts

    # ── Context Assembly ──────────────────────────────────────────────────────

    def get_context_for_prompt(self, force_refresh: bool = False) -> str:
        """
        Get a formatted context string for injection into the LLM prompt.
        Cached for 45s to avoid hammering all APIs on every message.
        """
        now = time.time()
        if not force_refresh and self._context_cache and (now - self._cache_time) < self._cache_ttl:
            return self._context_cache

        parts = []

        # Google Calendar
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            if gs.is_connected():
                events = gs.get_todays_events()
                for ev in events[:3]:
                    mins = ev.get("minutes_away")
                    if mins is not None and 0 < mins <= 60:
                        parts.append(f"[CALENDAR] {ev['title']} in {mins}min" + (" (MEET)" if ev.get('meet_link') else ""))
                    elif mins is not None and mins <= 0 and mins > -30:
                        parts.append(f"[CALENDAR] {ev['title']} happening NOW")
        except Exception as e:
            logger.error(f"Error in get_context_for_prompt (Google): {e}", exc_info=True)

        # Microsoft
        try:
            from integrations.microsoft_bridge import MicrosoftBridge
            ms = MicrosoftBridge.get_instance()
            ctx = ms.get_context_summary()
            if ctx:
                parts.append(ctx)
        except (ImportError, Exception) as e:
            if not isinstance(e, ImportError):
                logger.error(f"Error in get_context_for_prompt (Microsoft): {e}", exc_info=True)

        # Phone
        try:
            from integrations.phone_bridge import PhoneBridge
            bridge = PhoneBridge.get_instance()
            if bridge.is_connected():
                state = bridge.get_state()
                battery = state.get("battery", state.get("battery_level"))
                location = state.get("location_label", state.get("location", ""))
                if battery:
                    parts.append(f"[PHONE] Battery: {battery}%" + (f" | At: {location}" if location else ""))
                missed = state.get("missed_calls", 0)
                if missed:
                    parts.append(f"[PHONE] {missed} missed call(s)")
        except Exception as e:
            logger.error(f"Error in get_context_for_prompt (Phone): {e}", exc_info=True)

        # GitHub
        try:
            from integrations.github_monitor import get_github_monitor
            gh = get_github_monitor()
            ctx = gh.get_context_summary()
            if ctx:
                parts.append(ctx)
        except Exception as e:
            logger.error(f"Error in get_context_for_prompt (GitHub): {e}", exc_info=True)

        # Finance
        try:
            from integrations.finance_intelligence import get_finance_intelligence
            fi = get_finance_intelligence()
            ctx = fi.get_context_summary()
            if ctx:
                parts.append(ctx)
        except Exception as e:
            logger.error(f"Error in get_context_for_prompt (Finance): {e}", exc_info=True)

        # Browser
        try:
            from integrations.browser_monitor import get_browser_monitor
            bm = get_browser_monitor()
            ctx = bm.get_context_summary()
            if ctx:
                parts.append(ctx)
        except Exception as e:
            logger.error(f"Error in get_context_for_prompt (Browser): {e}", exc_info=True)

        # Clipboard
        try:
            from integrations.clipboard_monitor import get_clipboard_monitor
            cm = get_clipboard_monitor()
            ctx = cm.get_context_summary()
            if ctx:
                parts.append(ctx)
        except Exception as e:
            logger.error(f"Error in get_context_for_prompt (Clipboard): {e}", exc_info=True)

        # Active alerts from cross-source patterns
        for alert in self._snapshot.active_alerts[:3]:
            parts.append(f"!! {alert}")

        # ── AGI Kernel Snapshot Injection (mandatory context) ───────────────────
        try:
            from core.agi_kernel import get_agi_kernel
            kernel = get_agi_kernel()
            kernel_prompt = kernel.get_snapshot_for_prompt()
            if kernel_prompt:
                parts.append(kernel_prompt)
        except Exception as e:
            logger.error(f"Error injecting AGIKernel snapshot: {e}", exc_info=True)

        context = "\n".join(parts)
        self._context_cache = context
        self._cache_time = now
        return context

    # ── Full Poll ─────────────────────────────────────────────────────────────

    def poll_all(self):
        """Run a full poll of all sources and update the snapshot."""
        snap = IntelligenceSnapshot()
        snap.system = self._collect_system()
        snap.google = self._collect_google()
        snap.microsoft = self._collect_microsoft()
        snap.phone = self._collect_phone()
        snap.github = self._collect_github()
        snap.finance = self._collect_finance()
        snap.browser = self._collect_browser()
        snap.clipboard = self._collect_clipboard()

        # Pattern detection
        patterns, alerts = self._detect_patterns(snap)
        snap.cross_patterns = patterns
        snap.active_alerts = alerts

        self._snapshot = snap
        self._context_cache = ""  # Invalidate cache

        # Push critical cross-source alerts
        for alert in alerts[:3]:
            try:
                from core.proactive_push import get_push_engine
                priority = "critical" if "meeting" in alert.lower() or "market" in alert.lower() else "high"
                get_push_engine().push("ALERT", alert, priority=priority, metadata={"source": "intelligence_hub"})
            except Exception as e:
                logger.error(f"Error in poll_all (push alerts): {e}", exc_info=True)

        # Emit neural bus event
        try:
            from core.neural_bus import get_neural_bus
            bus = get_neural_bus()
            bus.publish(
                domain="awareness",
                event_type="intelligence_poll_complete",
                payload={
                    "sources_active": [k for k, v in self._sources.items() if v],
                    "alerts": len(alerts),
                    "patterns": len(patterns),
                },
                source_module="intelligence_hub",
            )
        except Exception as e:
            logger.error(f"Error in poll_all (neural bus): {e}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        return {
            "sources": self._sources,
            "active_alerts": self._snapshot.active_alerts,
            "cross_patterns": self._snapshot.cross_patterns,
            "last_snapshot": self._snapshot.timestamp,
            "sources_connected": sum(1 for v in self._sources.values() if v),
        }

    # ── Daemon ────────────────────────────────────────────────────────────────

    def start(self, interval: int = POLL_INTERVAL):
        if self._running:
            return
        self._running = True
        # Start sub-monitors
        try:
            from integrations.finance_intelligence import get_finance_intelligence
            get_finance_intelligence().start_monitoring(300)
        except Exception as e:
            logger.error(f"Error in start (finance monitor): {e}", exc_info=True)
        try:
            from integrations.browser_monitor import get_browser_monitor
            get_browser_monitor().start_monitoring(30)
        except Exception as e:
            logger.error(f"Error in start (browser monitor): {e}", exc_info=True)
        try:
            from integrations.clipboard_monitor import get_clipboard_monitor
            get_clipboard_monitor().start_monitoring(2)
        except Exception as e:
            logger.error(f"Error in start (clipboard monitor): {e}", exc_info=True)
        try:
            from integrations.github_monitor import get_github_monitor
            get_github_monitor().start_polling(300)
        except Exception as e:
            logger.error(f"Error in start (github monitor): {e}", exc_info=True)

        def _loop():
            time.sleep(10)  # Brief init delay
            consecutive_errors = 0
            while self._running:
                try:
                    self.poll_all()
                    consecutive_errors = 0
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"[IntelligenceHub] Poll error: {e}", exc_info=True)
                    print(f"[IntelligenceHub] Poll error: {e}")
                    backoff = min(300, 10 * (2 ** (consecutive_errors - 1)))
                    time.sleep(backoff)
                    continue

                for _ in range(interval):
                    if not self._running:
                        break
                    time.sleep(1)

        self._thread = threading.Thread(target=_loop, daemon=True, name="LOVE-IntelligenceHub")
        self._thread.start()
        print(f"[IntelligenceHub] Started — monitoring all sources (interval={interval}s)")

    def get_snapshot(self) -> dict:
        """Returns a dictionary containing the current fused context and active patterns."""
        return {
            "fused_context": self.get_context_for_prompt(),
            "active_patterns": self._snapshot.cross_patterns
        }

    def get_intelligence_snapshot(self) -> IntelligenceSnapshot:
        """Public accessor for the current intelligence snapshot."""
        return self._snapshot

    def stop(self):
        self._running = False


def get_intelligence_hub() -> IntelligenceHub:
    return IntelligenceHub.get_instance()
