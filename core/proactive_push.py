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


class ProactivePushEngine:
    """
    Scans all LOVE systems periodically and pushes relevant messages
    to connected WebSocket clients.
    """

    def __init__(self):
        self._queue: deque = deque(maxlen=100)
        self._callbacks: List[Callable] = []  # async callbacks for WS push
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_push_time: float = 0.0
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._push_counts: Dict[str, int] = {}  # category → count today

    def set_async_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async callbacks."""
        self._async_loop = loop

    def register_callback(self, callback: Callable):
        """Register an async callback to receive push messages."""
        self._callbacks.append(callback)

    def push(self, category: str, message: str, priority: str = "normal", metadata: Dict = None):
        """Add a message to the push queue."""
        import uuid
        msg = PushMessage(
            id=uuid.uuid4().hex[:8],
            category=category,
            message=message,
            priority=priority,
            metadata=metadata or {},
        )
        self._queue.append(msg)
        # Log it
        try:
            with open(PUSH_LOG, "a") as f:
                f.write(json.dumps(asdict(msg)) + "\n")
        except Exception:
            pass
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
            except Exception:
                pass
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

    def stop(self):
        self._running = False

    def _scan_loop(self):
        """Background loop: scan all systems, push insights."""
        time.sleep(60)  # Let systems initialize first
        while self._running:
            try:
                self._run_scan()
            except Exception as e:
                print(f"[ProactivePush] Scan error: {e}")
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
        except Exception:
            pass
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
        except Exception:
            pass
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
                        except Exception:
                            pass
                        return True
        except Exception:
            pass
        return False

    def _check_evolution(self) -> bool:
        try:
            from core.evolution_engine import get_evolution_engine
            evo = get_evolution_engine()
            mutations = evo.get_active_mutations()
            if mutations:
                latest = mutations[-1]
                desc = getattr(latest, 'description', str(latest))
                gen = evo.get_generation()
                self.push(
                    "EVOLUTION",
                    f"I just evolved (gen {gen}): {desc[:150]}",
                    priority="low",
                    metadata={"generation": gen, "mutation": desc[:100]},
                )
                return True
        except Exception:
            pass
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
        except Exception:
            pass
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
        except Exception:
            pass
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
                except Exception:
                    pass
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
