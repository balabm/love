"""
LOVE Proactive Push Engine

LOVE is not a chatbot. It notices things. It reaches out. It protects you.

This engine runs in a background thread and pushes messages to connected
WebSocket clients when LOVE has something to say — no prompt needed.

Push categories:
- INSIGHT: LOVE noticed a pattern across your life domains
- ALERT: Something needs your attention (overdue task, work limit, health)
- NUDGE: Gentle encouragement or habit reminder
- THOUGHT: LOVE had an interesting thought during idle time
- EVOLUTION: LOVE improved itself and wants to tell you
- MEMORY: LOVE remembered something relevant to what you're doing now
"""

import asyncio
import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from core.execution_guard import log_error
from core.base_module import BaseLOVEModule, ModuleCapabilities


# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"
PUSH_LOG = DATA_DIR / "push_history.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PUSH_INTERVAL_SECONDS = 300  # Check every 5 minutes for things to push
MIN_PUSH_GAP_SECONDS = 120   # Don't push more than once every 2 minutes


@dataclass
class PushMessage:
    id: str
    category: str  # INSIGHT, ALERT, NUDGE, THOUGHT, EVOLUTION, MEMORY
    message: str
    priority: str = "normal"  # low, normal, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    delivered: bool = False


class ProactivePushEngine(BaseLOVEModule):
    """
    Scans all LOVE systems periodically and pushes relevant messages
    to connected WebSocket clients.
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name or "ProactivePushEngine")
        self._queue: deque = deque(maxlen=100)
        self._callbacks: List[Callable] = []  # async callbacks for WS push
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_push_time: float = 0.0
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._push_counts: Dict[str, int] = {}  # category → count today
        self._recent_messages: Dict[str, float] = {}  # message_hash → timestamp for dedup
        self._pushed_mutation_ids: set = set()  # already-pushed evolution mutations
        self._last_category_push_time: Dict[str, float] = {}  # category → timestamp
        self._printed_suppressions: set = set()  # suppress duplicate log noise


    # -- BaseLOVEModule contract --

    def get_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            domain="proactivepush",
            actions=[],
            events_produced=[],
            resource_heavy=False,
            user_facing=False,
        )

    def stress_score(self) -> float:
        return 0.3

    def dependencies(self) -> list:
        return []

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_bus_event(self, event: dict):
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})
        if event_type == "finance_alert":
            alert = payload.get("alert", "")
            symbol = payload.get("symbol", "")
            if alert:
                try:
                    self.push(
                        category="finance",
                        message=f"Finance Alert ({symbol or 'General'}): {alert[:200]}",
                        priority="high",
                    )
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.proactive_push", context={"phase": "on_bus_event"})
        elif event_type == "guardrails_intervention":
            action = payload.get("action", "")
            if action:
                try:
                    self.push(
                        category="system",
                        message=f"LOVE Intervention: Blocked risky action: {action[:100]}",
                        priority="high",
                    )
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.proactive_push", context={"phase": "on_bus_event"})
    def set_async_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async callbacks."""
        self._async_loop = loop

    def register_callback(self, callback: Callable):
        """Register an async callback to receive push messages."""
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable):
        """Remove a previously registered callback."""
        try:
            self._callbacks.remove(callback)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")

    def push(self, category: str, message: str, priority: str = "normal", metadata: Dict = None):
        """Add a message to the push queue. Skip if identical message was pushed recently."""
        import uuid
        import hashlib
        now = time.time()

        # Phase 3 AGI Metamorphosis: Dynamic cooldown from Behavior Modulator
        # The modulator sets _dynamic_cooldown_seconds based on LOVE's emotional state.
        # Default is 7200 (2 hours) if modulator hasn't set a value.
        cooldown = getattr(self, "_dynamic_cooldown_seconds", 7200)

        # Category cooldown: max 1 push per category per cooldown period (except high/critical)
        if priority not in ("high", "critical"):
            last_cat = self._last_category_push_time.get(category, 0)
            if now - last_cat < cooldown:
                return  # silently skip

        # Deduplication: same message within cooldown period = suppressed
        msg_hash = hashlib.sha256(f"{category}:{message}".encode()).hexdigest()[:16]
        if msg_hash in self._recent_messages:
            last_time = self._recent_messages[msg_hash]
            if now - last_time < cooldown:
                # Only print suppression once per hash to reduce log noise
                if msg_hash not in self._printed_suppressions:
                    self._printed_suppressions.add(msg_hash)
                    print(f"[ProactivePush] Duplicate suppressed: {message[:60]}")
                return
        self._recent_messages[msg_hash] = now
        self._last_category_push_time[category] = now
        # Prune old entries to prevent memory growth
        self._recent_messages = {k: v for k, v in self._recent_messages.items() if now - v < cooldown}
        self._printed_suppressions.discard(msg_hash)

        msg = PushMessage(
            id=uuid.uuid4().hex[:8],
            category=category,
            message=message,
            priority=priority,
            metadata=metadata or {},
        )
        self._queue.append(msg)
        # Log to centralized activity log
        try:
            from core.activity_log import log_activity
            log_activity("proactive_push", "message_queued", f"[{category}] {message}", {"category": category, "priority": priority}, importance=priority if priority in ("high", "critical") else "normal")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        # Log it locally
        try:
            with open(PUSH_LOG, "a") as f:
                f.write(json.dumps(asdict(msg)) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")

        # Publish to neural bus for cross-module awareness
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                priority_map = {
                    "critical": EventPriority.CRITICAL,
                    "high": EventPriority.HIGH,
                    "normal": EventPriority.NORMAL,
                    "low": EventPriority.LOW
                }
                bus.publish(
                    domain="proactive",
                    event_type="push_queued",
                    payload=asdict(msg),
                    source_module="proactive_push",
                    priority=priority_map.get(priority, EventPriority.NORMAL)
                )
            except Exception as e:
                print(f"[ProactivePush] Neural bus publish error: {e}")
        # Deliver immediately if high priority
        if priority in ("high", "critical"):
            self._deliver(msg)

    def _deliver(self, msg: PushMessage):
        """Deliver a message to all registered WebSocket callbacks + Telegram."""
        # Telegram delivery for high/critical
        if msg.priority in ("high", "critical"):
            try:
                import os, urllib.request, urllib.parse, json as _json
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
                chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
                if bot_token and chat_id:
                    text = f"[LOVE {msg.category}]\n{msg.message}"
                    data = _json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
                    req = urllib.request.Request(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        data=data,
                        headers={"Content-Type": "application/json"},
                    )
                    urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.proactive_push")
        if not self._callbacks:
            return
        payload = {
            "type": "proactive_push",
            "category": msg.category,
            "message": msg.message,
            "priority": msg.priority,
            "timestamp": msg.timestamp,
            "metadata": msg.metadata,
        }
        if self._async_loop and self._async_loop.is_running():
            for cb in self._callbacks:
                asyncio.run_coroutine_threadsafe(cb(payload), self._async_loop)
        msg.delivered = True

    def start(self):
        """Start the proactive push background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._scan_loop, daemon=True, name="LOVE-ProactivePush"
        )
        self._thread.start()
        print("[ProactivePush] Started — LOVE will now reach out proactively")
        super().start()
        return True



    def stop(self):
        self._running = False
        super().stop()
        return True



    def _scan_loop(self):
        """Background loop: scan all systems, push insights."""
        from core.activity_log import log_activity
        time.sleep(60)  # Let systems initialize first
        log_activity("proactive_push", "daemon_started", "Proactive push daemon started", importance="normal")
        while self._running:
            try:
                self._run_scan()
            except Exception as e:
                print(f"[ProactivePush] Scan error: {e}")
                log_activity("proactive_push", "scan_error", f"Scan error: {str(e)[:100]}", {"error": str(e)[:200]}, importance="high")
            time.sleep(PUSH_INTERVAL_SECONDS)

    def _run_scan(self):
        """Scan all systems for push-worthy events."""
        now = time.time()
        if now - self._last_push_time < MIN_PUSH_GAP_SECONDS:
            return

        pushed = False

        # 1. Check for overdue tasks
        pushed |= self._check_tasks()
        # 2. Check work limit
        pushed |= self._check_work_limit()
        # 3. Check idle mind drafts (LOVE's own thoughts)
        pushed |= self._check_idle_thoughts()
        # 4. Check evolution milestone
        pushed |= self._check_evolution()
        # 5. Check emotional patterns
        pushed |= self._check_emotional_patterns()
        # 6. Check research findings
        pushed |= self._check_research()
        # 7. Check predictive intelligence for high-confidence forecasts
        pushed |= self._check_predictions()

        if pushed:
            self._last_push_time = now

    def _check_tasks(self) -> bool:
        try:
            from agents.task_agent import TaskAgent
            ta = TaskAgent()
            overdue = ta.get_overdue_tasks() if hasattr(ta, 'get_overdue_tasks') else []
            if overdue:
                titles = ", ".join(getattr(t, 'title', str(t)) for t in overdue[:3])
                self.push(
                    "ALERT",
                    f"You have {len(overdue)} overdue task(s): {titles}",
                    priority="high" if len(overdue) > 2 else "normal",
                    metadata={"overdue_count": len(overdue)},
                )
                return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        return False

    def _check_work_limit(self) -> bool:
        try:
            from tools.guardian import check_work_status, format_work_status_for_chat
            status = check_work_status()
            hours_worked = status.get("hours_worked", 0)
            limit = status.get("daily_limit", 8)
            pct = hours_worked / limit if limit > 0 else 0
            if pct >= 1.0:
                self.push(
                    "ALERT",
                    f"Work limit reached: {hours_worked:.1f}h of {limit}h. Time to stop.",
                    priority="critical",
                    metadata={"hours_worked": hours_worked, "limit": limit},
                )
                return True
            elif pct >= 0.8:
                self.push(
                    "NUDGE",
                    f"Approaching work limit: {hours_worked:.1f}h of {limit}h. Start winding down.",
                    priority="normal",
                    metadata={"hours_worked": hours_worked, "limit": limit},
                )
                return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        return False

    def _check_idle_thoughts(self) -> bool:
        try:
            from core.idle_mind import get_recent_thoughts
            thoughts = get_recent_thoughts(3)
            for t in thoughts:
                if not t.get("pushed_to_ui"):
                    thought_text = t.get("summary", t.get("result", ""))
                    if thought_text and len(thought_text) > 30:
                        self.push(
                            "THOUGHT",
                            f"While you were away, I was thinking: {thought_text[:200]}",
                            priority="low",
                            metadata={"thought_id": t.get("id", "")},
                        )
                        # Mark as pushed (best effort)
                        try:
                            t["pushed_to_ui"] = True
                        except Exception as e:
                            from core.execution_guard import log_error
                            log_error(e, module="core.proactive_push")
                        return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        return False

    def _check_evolution(self) -> bool:
        try:
            from core.evolution_engine import get_evolution_engine
            evo = get_evolution_engine()
            mutations = evo.get_active_mutations()
            if mutations:
                latest = mutations[-1]
                mutation_id = getattr(latest, 'id', '')
                # Skip if we already pushed this exact mutation
                if mutation_id and mutation_id in self._pushed_mutation_ids:
                    return False
                desc = getattr(latest, 'description', str(latest))
                gen = evo.get_generation()
                self.push(
                    "EVOLUTION",
                    f"I just evolved (gen {gen}): {desc[:150]}",
                    priority="low",
                    metadata={"generation": gen, "mutation": desc[:100], "mutation_id": mutation_id},
                )
                if mutation_id:
                    self._pushed_mutation_ids.add(mutation_id)
                return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        return False

    def _check_emotional_patterns(self) -> bool:
        try:
            from agents.emotional_agent import EmotionalAgent
            ea = EmotionalAgent()
            insights = ea.get_current_insights() if hasattr(ea, 'get_current_insights') else []
            for ins in (insights or []):
                insight_type = getattr(ins, 'insight_type', '')
                if insight_type in ('alert', 'pattern'):
                    msg = getattr(ins, 'message', str(ins))
                    self.push(
                        "INSIGHT",
                        msg,
                        priority="high" if insight_type == 'alert' else "normal",
                        metadata={"insight_type": insight_type},
                    )
                    return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        return False

    def _check_research(self) -> bool:
        try:
            from core.research_engine import get_research_engine
            research = get_research_engine()
            status = research.get_status() if hasattr(research, 'get_status') else {}
            recent = status.get("recent_findings", [])
            if recent:
                finding = recent[0]
                topic = finding.get("topic", "")
                synthesis = finding.get("synthesis", "")[:150]
                if topic and synthesis:
                    self.push(
                        "INSIGHT",
                        f"I researched '{topic}' and found: {synthesis}",
                        priority="low",
                        metadata={"topic": topic},
                    )
                    return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        return False

    def _check_predictions(self) -> bool:
        """Check predictive intelligence for high-confidence actionable forecasts."""
        try:
            from core.predictive_intelligence import get_predictive_engine
            engine = get_predictive_engine()
            predictions = engine.get_active_predictions()
            if not predictions:
                return False
            for p in predictions:
                conf = p.get("confidence", 0)
                ptype = p.get("type", "")
                if conf >= 0.75 and ptype in ("NEED", "BEHAVIOR", "EMOTIONAL_STATE"):
                    what = p.get("what", "")
                    actions = p.get("suggested_actions", [])
                    action_text = actions[0] if actions else ""
                    if not hasattr(self, "_pushed_predictions"):
                        self._pushed_predictions = set()
                    pred_id = p.get("id", what)
                    if pred_id in self._pushed_predictions:
                        continue
                    self._pushed_predictions.add(pred_id)
                    msg = f"I anticipate: {what}"
                    if action_text:
                        msg += f" ({action_text})"
                    self.push(
                        "PREDICTION",
                        msg,
                        priority="normal",
                        metadata={"confidence": conf, "prediction_type": ptype},
                    )
                    return True
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.proactive_push")
        return False

    def get_pending(self, limit: int = 10) -> List[Dict]:
        """Get pending (undelivered) push messages."""
        return [asdict(m) for m in list(self._queue)[-limit:] if not m.delivered]

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get push history from log."""
        try:
            lines = PUSH_LOG.read_text().strip().split("\n") if PUSH_LOG.exists() else []
            entries = []
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line))
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.proactive_push")
            return list(reversed(entries))
        except Exception:
            return []


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[ProactivePushEngine] = None
_lock = threading.Lock()


def get_push_engine() -> ProactivePushEngine:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = ProactivePushEngine()
    return _instance
