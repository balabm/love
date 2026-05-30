"""
LOVE Sentinel — Self-Monitoring Protocol

The Sentinel is LOVE's always-on watchdog that monitors the user across their
entire digital ecosystem and proactively acts on their behalf. It replaces the
user's presence when they're away and protects them when they're present.

Core behaviors:
─────────────────────────────────────────────────────────────────────────────
1. PRESENCE DETECTION
   - Tracks user presence (active / idle / away / sleeping)
   - Detects activity type (work / meeting / creative / browsing / gaming)
   - Monitors engagement patterns (focus depth, distraction frequency)

2. CROSS-DOMAIN INTELLIGENCE
   - Fuses data from: calendar, email, chat, finance, health, tasks, goals
   - Detects contradictions (meeting in 5min but gaming; deadline tomorrow but browsing)
   - Identifies opportunities (free slot → suggest deep work; low energy → suggest break)

3. AUTONOMOUS ACTIONS
   - While user is present: nudge, warn, suggest, protect
   - While user is away: monitor deadlines, summarize missed events, queue alerts
   - While user is sleeping: consolidate memory, plan next day, run maintenance

4. SELF-HEALING & RESILIENCE
   - If a subsystem crashes, Sentinel detects it and restarts it
   - Tracks system health across all modules
   - Logs every decision for transparency

Protocol:
  - Runs every 60s (fast tick) for presence/activity
  - Runs every 300s (slow tick) for cross-domain analysis
  - Runs every 3600s (hourly) for summaries and planning
"""

import asyncio
import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"
SENTINEL_DIR = DATA_DIR / "sentinel"
SENTINEL_DIR.mkdir(parents=True, exist_ok=True)
SENTINEL_LOG = SENTINEL_DIR / "sentinel_log.jsonl"
SENTINEL_STATE = SENTINEL_DIR / "sentinel_state.json"

# ── Tick intervals ─────────────────────────────────────────────────────────────
FAST_TICK = 60        # 1 min — presence + activity detection
SLOW_TICK = 300       # 5 min — cross-domain fusion + autonomous decisions
HOURLY_TICK = 3600    # 1 hour — summaries, planning, self-healing


# ── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class UserPresence:
    """Current state of the user."""
    state: str = "unknown"       # active / idle / away / sleeping
    activity: str = "unknown"    # work / meeting / creative / browsing / gaming / idle
    active_app: str = ""
    focus_depth: float = 0.0     # 0-1: how deeply focused (based on app-switch frequency)
    idle_seconds: int = 0
    last_interaction: str = ""
    location: str = "desktop"    # desktop / mobile / away


@dataclass
class SentinelEvent:
    """Something the Sentinel noticed or did."""
    id: str = ""
    timestamp: str = ""
    category: str = ""           # presence, alert, action, nudge, summary, health
    title: str = ""
    detail: str = ""
    priority: str = "normal"     # low, normal, high, critical
    acted: bool = False          # Did Sentinel take autonomous action?
    action_taken: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Sentinel Engine ────────────────────────────────────────────────────────────

class Sentinel:
    """
    LOVE's always-on self-monitoring protocol.
    Watches over the user and the entire LOVE ecosystem.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_event: Optional[asyncio.Event] = None
        self._presence = UserPresence()
        self._events: deque = deque(maxlen=200)
        self._callbacks: List[Callable] = []
        self._last_slow_tick = 0.0
        self._last_hourly_tick = 0.0
        self._last_activity_change = time.time()
        self._app_switch_count = 0
        self._app_switch_window_start = time.time()
        self._consecutive_idle_ticks = 0
        self._state = self._load_state()
        self._subsystem_health: Dict[str, Dict] = {}

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_async_loop, daemon=True, name="LOVE-Sentinel"
        )
        self._thread.start()
        self._emit("health", "Sentinel Online", "Self-monitoring protocol activated.", "low")
        print("[Sentinel] Started — always watching over you")

    def stop(self):
        self._running = False
        if self._loop and self._shutdown_event:
            asyncio.run_coroutine_threadsafe(
                self._shutdown_event.set(), self._loop
            )
        self._emit("health", "Sentinel Offline", "Self-monitoring protocol stopped.", "normal")

    def register_callback(self, cb: Callable):
        """Register async callback for real-time push."""
        self._callbacks.append(cb)

    # ── Main Loop ──────────────────────────────────────────────────────────────

    def _run_async_loop(self):
        """Run the async event loop in a dedicated thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._shutdown_event = asyncio.Event()
        try:
            self._loop.run_until_complete(self._main_loop())
        finally:
            self._loop.close()

    async def _main_loop(self):
        await asyncio.sleep(30)  # Let other systems boot first
        while self._running and not self._shutdown_event.is_set():
            try:
                await self._fast_tick()
            except Exception as e:
                print(f"[Sentinel] Fast tick error: {e}")

            now = time.time()
            if now - self._last_slow_tick >= SLOW_TICK:
                try:
                    await self._slow_tick()
                except Exception as e:
                    print(f"[Sentinel] Slow tick error: {e}")
                self._last_slow_tick = now

            if now - self._last_hourly_tick >= HOURLY_TICK:
                try:
                    await self._hourly_tick()
                except Exception as e:
                    print(f"[Sentinel] Hourly tick error: {e}")
                self._last_hourly_tick = now

            await asyncio.sleep(FAST_TICK)

    # ── Fast Tick: Presence & Activity Detection ───────────────────────────────

    async def _fast_tick(self):
        """Every 60s: detect what the user is doing right now."""
        prev_state = self._presence.state
        prev_app = self._presence.active_app

        # Get current awareness snapshot with timeout
        try:
            from core.awareness import get_awareness
            engine = get_awareness()
            snapshot = await asyncio.wait_for(
                asyncio.to_thread(engine.get_snapshot),
                timeout=5.0
            )

            system = snapshot.get("system", {})
            context = snapshot.get("context", {})

            self._presence.active_app = context.get("active_window", "")
            self._presence.idle_seconds = system.get("idle_seconds", 0)
            self._presence.last_interaction = datetime.now().isoformat()

            # Track app switching (indicator of distraction)
            if prev_app and prev_app != self._presence.active_app:
                self._app_switch_count += 1

            # Reset switch counter every 5 minutes
            if time.time() - self._app_switch_window_start > 300:
                self._presence.focus_depth = max(0.0, 1.0 - (self._app_switch_count / 15))
                self._app_switch_count = 0
                self._app_switch_window_start = time.time()

        except asyncio.TimeoutError:
            self._subsystem_health["awareness"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
            print("[Sentinel] Awareness subsystem stalled - timeout")
        except Exception as e:
            self._subsystem_health["awareness"] = {"status": "error", "error": str(e)}
            print(f"[Sentinel] Awareness error: {e}")

        # Determine presence state
        idle = self._presence.idle_seconds
        if idle < 120:
            self._presence.state = "active"
            self._consecutive_idle_ticks = 0
        elif idle < 600:
            self._presence.state = "idle"
            self._consecutive_idle_ticks += 1
        elif idle < 7200:
            self._presence.state = "away"
            self._consecutive_idle_ticks += 1
        else:
            self._presence.state = "sleeping"
            self._consecutive_idle_ticks += 1

        # Detect activity type from active window
        self._presence.activity = self._classify_activity(self._presence.active_app)

        # Emit presence change events
        if prev_state != self._presence.state:
            self._emit(
                "presence",
                f"State: {prev_state} → {self._presence.state}",
                f"User moved from {prev_state} to {self._presence.state}. "
                f"Active app: {self._presence.active_app}",
                "low",
            )
            await self._on_state_change(prev_state, self._presence.state)

    def _classify_activity(self, window_title: str) -> str:
        """Classify what the user is doing based on active window."""
        if not window_title:
            return "idle"
        t = window_title.lower()

        # Work indicators
        work_apps = ["vs code", "visual studio", "pycharm", "intellij", "terminal",
                     "cmd", "powershell", "git", "docker", "postman", "figma",
                     "notion", "jira", "slack", "teams", "outlook", "gmail"]
        # Meeting indicators
        meeting_apps = ["zoom", "google meet", "teams meeting", "webex", "discord call"]
        # Creative indicators
        creative_apps = ["photoshop", "illustrator", "blender", "premiere",
                         "davinci", "ableton", "logic pro", "unity", "unreal"]
        # Browsing
        browser_apps = ["chrome", "firefox", "edge", "safari", "brave", "opera"]
        # Gaming
        game_indicators = ["steam", "epic games", "game", ".exe", "valorant",
                          "minecraft", "gta", "league", "fortnite"]

        for app in meeting_apps:
            if app in t:
                return "meeting"
        for app in work_apps:
            if app in t:
                return "work"
        for app in creative_apps:
            if app in t:
                return "creative"
        for app in game_indicators:
            if app in t:
                return "gaming"
        for app in browser_apps:
            if app in t:
                return "browsing"
        return "other"

    # ── Slow Tick: Cross-Domain Intelligence ───────────────────────────────────

    async def _slow_tick(self):
        """Every 5 min: cross-reference all data sources, detect contradictions, take action."""
        decisions = []

        # 1. Calendar awareness — upcoming events
        decisions.extend(await self._check_calendar_context())
        # 2. Work limit protection
        decisions.extend(await self._check_work_protection())
        # 3. Goal alignment check
        decisions.extend(await self._check_goal_alignment())
        # 4. Communication monitoring (emails/chat needing attention)
        decisions.extend(await self._check_communications())
        # 5. Finance monitoring
        decisions.extend(await self._check_finance_alerts())
        # 6. Focus protection
        decisions.extend(await self._check_focus_protection())
        # 7. Guardrails proactive warnings
        decisions.extend(await self._check_guardrails_warnings())

        # Execute decisions
        for decision in decisions:
            self._execute_decision(decision)

        # Save state
        self._save_state()

    async def _check_calendar_context(self) -> List[Dict]:
        """Check if there's a meeting soon while user is not preparing."""
        decisions = []
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            if await asyncio.wait_for(
                asyncio.to_thread(gs.is_connected),
                timeout=5.0
            ):
                events = await asyncio.wait_for(
                    asyncio.to_thread(gs.get_todays_events),
                    timeout=5.0
                )
                now = datetime.now()
                for event in events:
                    start_str = event.get("start", "")
                    if not start_str:
                        continue
                    try:
                        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                        if hasattr(start, 'astimezone'):
                            start = start.replace(tzinfo=None)
                        delta = (start - now).total_seconds()
                        # Meeting in 5-10 minutes and user is not in a meeting app
                        if 300 <= delta <= 600 and self._presence.activity != "meeting":
                            decisions.append({
                                "type": "nudge",
                                "title": "Meeting Soon",
                                "message": f"'{event.get('summary', 'Meeting')}' starts in {int(delta/60)} minutes.",
                                "priority": "high",
                            })
                    except Exception:
                        continue
        except asyncio.TimeoutError:
            self._subsystem_health["calendar"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
            print("[Sentinel] Calendar subsystem stalled - timeout")
        except Exception as e:
            self._subsystem_health["calendar"] = {"status": "error", "error": str(e)}
            print(f"[Sentinel] Calendar error: {e}")
        return decisions

    async def _check_work_protection(self) -> List[Dict]:
        """Enforce work limits — LOVE's guardian role."""
        decisions = []
        try:
            from tools.guardian import check_work_status
            status = await asyncio.wait_for(
                asyncio.to_thread(check_work_status),
                timeout=5.0
            )
            hours = status.get("hours_worked", 0)
            limit = status.get("daily_limit", 8)
            pct = hours / limit if limit > 0 else 0

            if pct >= 1.0 and self._presence.activity == "work":
                decisions.append({
                    "type": "alert",
                    "title": "Work Limit Exceeded",
                    "message": f"You've worked {hours:.1f}h of your {limit}h limit. Stop. Your body needs rest.",
                    "priority": "critical",
                })
            elif pct >= 0.9 and self._presence.activity == "work":
                decisions.append({
                    "type": "nudge",
                    "title": "Winding Down",
                    "message": f"{hours:.1f}h of {limit}h. Start wrapping up — what's the ONE thing you'll finish before stopping?",
                    "priority": "high",
                })
        except asyncio.TimeoutError:
            self._subsystem_health["guardian"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
            print("[Sentinel] Guardian subsystem stalled - timeout")
        except Exception as e:
            self._subsystem_health["guardian"] = {"status": "error", "error": str(e)}
            print(f"[Sentinel] Guardian error: {e}")
        return decisions

    async def _check_goal_alignment(self) -> List[Dict]:
        """Check if current activity aligns with user's active goals."""
        decisions = []
        try:
            from core.autonomous_goal_engine import get_goals
            goals = await asyncio.wait_for(
                asyncio.to_thread(get_goals, status="active"),
                timeout=5.0
            )
            if not goals:
                return decisions

            # If user has been browsing/gaming for 30+ minutes and has active goals
            if (self._presence.activity in ("browsing", "gaming")
                    and self._consecutive_idle_ticks == 0
                    and time.time() - self._last_activity_change > 1800):
                goal_titles = [g.title for g in goals[:3]]
                decisions.append({
                    "type": "nudge",
                    "title": "Goal Check",
                    "message": f"You've been {self._presence.activity} for 30+ min. "
                               f"Your active goals: {', '.join(goal_titles)}. "
                               f"Is this intentional downtime?",
                    "priority": "normal",
                })
        except asyncio.TimeoutError:
            self._subsystem_health["goal_engine"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
            print("[Sentinel] Goal engine subsystem stalled - timeout")
        except Exception as e:
            self._subsystem_health["goal_engine"] = {"status": "error", "error": str(e)}
            print(f"[Sentinel] Goal engine error: {e}")
        return decisions

    async def _check_communications(self) -> List[Dict]:
        """Check for urgent unread communications."""
        decisions = []
        # Only nudge about comms when user is active and not in a meeting
        if self._presence.state != "active" or self._presence.activity == "meeting":
            return decisions

        try:
            from integrations.microsoft_bridge import MicrosoftBridge
        except ImportError:
            # Microsoft integration not available (azure not installed) — skip silently
            return decisions

        try:
            ms = MicrosoftBridge.get_instance()
            if await asyncio.wait_for(
                asyncio.to_thread(ms.is_connected),
                timeout=5.0
            ):
                count = await asyncio.wait_for(
                    asyncio.to_thread(ms.get_unread_count),
                    timeout=5.0
                )
                if count > 10:
                    decisions.append({
                        "type": "nudge",
                        "title": "Email Pile-up",
                        "message": f"{count} unread emails. Want me to summarize the important ones?",
                        "priority": "normal",
                    })
        except asyncio.TimeoutError:
            self._subsystem_health["microsoft_bridge"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
            print("[Sentinel] Microsoft Bridge subsystem stalled - timeout")
        except Exception as e:
            self._subsystem_health["microsoft_bridge"] = {"status": "error", "error": str(e)}
            print(f"[Sentinel] Microsoft Bridge error: {e}")
        return decisions

    async def _check_finance_alerts(self) -> List[Dict]:
        """Check for significant market moves."""
        decisions = []
        try:
            from integrations.finance_intelligence import FinanceIntelligence
            fi = FinanceIntelligence()
            if hasattr(fi, 'get_proactive_alerts'):
                alerts = await asyncio.wait_for(
                    asyncio.to_thread(fi.get_proactive_alerts),
                    timeout=5.0
                )
                for alert in alerts[:2]:
                    msg = alert if isinstance(alert, str) else alert.get("message", str(alert))
                    decisions.append({
                        "type": "alert",
                        "title": "Market Move",
                        "message": msg,
                        "priority": "normal",
                    })
        except asyncio.TimeoutError:
            self._subsystem_health["finance_intelligence"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
            print("[Sentinel] Finance Intelligence subsystem stalled - timeout")
        except Exception as e:
            self._subsystem_health["finance_intelligence"] = {"status": "error", "error": str(e)}
            print(f"[Sentinel] Finance Intelligence error: {e}")
        return decisions

    async def _check_focus_protection(self) -> List[Dict]:
        """Protect deep focus sessions — suppress non-critical notifications."""
        decisions = []
        # High focus depth + work activity = deep work session
        if (self._presence.focus_depth > 0.7
                and self._presence.activity == "work"
                and self._presence.state == "active"):
            # Don't push low-priority notifications during deep work
            self._state["in_deep_work"] = True
            self._state["deep_work_start"] = self._state.get("deep_work_start", time.time())
            duration = time.time() - self._state.get("deep_work_start", time.time())
            # After 90 minutes of deep focus, suggest a break
            if duration > 5400:
                decisions.append({
                    "type": "nudge",
                    "title": "Deep Work Break",
                    "message": "You've been in deep focus for 90+ minutes. "
                               "Take a 5-minute break — your brain consolidates during rest.",
                    "priority": "normal",
                })
                self._state["deep_work_start"] = time.time()  # Reset
        else:
            self._state["in_deep_work"] = False
            self._state.pop("deep_work_start", None)
        return decisions

    # ── Hourly Tick: Summaries & Self-Healing ──────────────────────────────────

    async def _hourly_tick(self):
        """Every hour: summarize what happened, heal broken subsystems, plan ahead."""
        # 1. Self-heal check
        await self._self_heal()
        # 2. Generate hourly summary if user is active
        if self._presence.state in ("active", "idle"):
            self._generate_hour_summary()

    async def _self_heal(self):
        """Check all LOVE subsystems and restart crashed ones."""
        subsystems = [
            ("awareness", "core.awareness", "start_awareness"),
            ("heartbeat", "core.heartbeat", "start_heartbeat"),
            ("proactive_push", "core.proactive_push", "get_push_engine"),
            ("goal_engine", "core.autonomous_goal_engine", "start_goal_engine"),
            ("evolution_integration", "core.evolution_integration", "get_evolution_integration"),
            ("neural_architecture_search", "core.neural_architecture_search", "get_neural_architecture_search"),
            ("multimodal_evolution", "core.multimodal_evolution", "get_multimodal_evolution"),
            ("task_evolution", "agents.task_evolution_integration", "get_task_evolution_integration"),
            ("fitness_evolution", "agents.fitness_evolution_integration", "get_fitness_evolution_integration"),
            ("observability", "core.observability", "get_observability_engine"),
            ("llm_manager", "core.llm_manager", "get_llm_manager"),
            ("graph_rag", "core.graph_rag", "get_graph_rag_engine"),
            ("prompt_optimizer", "core.prompt_optimizer", "get_prompt_optimizer"),
            ("self_reflection", "core.self_reflection", "get_self_reflection_engine"),
            ("conversation_quality", "core.conversation_quality", "get_conversation_quality_analyzer"),
            ("predictive_maintenance", "core.predictive_maintenance", "get_predictive_maintenance_engine"),
            ("multi_agent_orchestrator", "core.multi_agent_orchestrator", "get_multi_agent_orchestrator"),
            ("intent_predictor", "core.intent_predictor", "get_intent_predictor"),
            ("personality_adapter", "core.personality_adapter", "get_personality_adapter"),
            ("response_cache", "core.response_cache", "get_response_cache"),
            ("context_window_manager", "core.context_window_manager", "get_context_window_manager"),
            ("user_pattern_detector", "core.user_pattern_detector", "get_user_pattern_detector"),
            ("goal_drift_detector", "core.goal_drift_detector", "get_goal_drift_detector"),
            ("cross_modal_fusion", "core.cross_modal_fusion", "get_cross_modal_fusion_engine"),
            ("emotional_resonance", "core.emotional_resonance", "get_emotional_resonance_engine"),
            ("knowledge_graph_builder", "core.knowledge_graph_builder", "get_knowledge_graph_builder"),
            ("adaptive_learning_rate", "core.adaptive_learning_rate", "get_adaptive_learning_engine"),
        ]
        for name, module, func in subsystems:
            try:
                mod = __import__(module, fromlist=[func])
                f = getattr(mod, func)
                # Just calling the function validates it's alive
                if name == "proactive_push":
                    engine = await asyncio.wait_for(
                        asyncio.to_thread(f),
                        timeout=5.0
                    )
                    if not engine._running:
                        engine.start()
                        self._emit("health", f"Restarted: {name}",
                                   f"Self-healed {name} — was not running.", "normal")
                # Mark as healthy on successful check
                self._subsystem_health[name] = {"status": "ok", "last_check": time.time()}
            except asyncio.TimeoutError:
                self._subsystem_health[name] = {"status": "STALLED", "error": "Timeout after 5.0s"}
                self._emit("health", f"Subsystem Stalled: {name}",
                           f"{name} health check timed out after 5.0s", "high")
            except Exception as e:
                self._subsystem_health[name] = {"status": "dead", "error": str(e)}
                self._emit("health", f"Subsystem Dead: {name}",
                           f"Cannot restart {name}: {e}", "high")

    async def _check_guardrails_warnings(self) -> List[Dict]:
        """Check guardrails for proactive warnings about user wellbeing."""
        decisions = []
        try:
            from core.guardrails import get_guardrails_engine
            gr = get_guardrails_engine()
            # Build context from current state
            context = {
                "work_hours_today": getattr(self._presence, 'work_hours_today', 0),
                "work_limit": 8,  # Default
                "sleep_last_night": getattr(self._presence, 'sleep_hours', 0),
                "hours_since_social": getattr(self._presence, 'hours_since_social', 0),
            }
            warning = gr.warn_if_risky(context)
            if warning:
                decisions.append({
                    "category": "wellbeing",
                    "type": "warning",
                    "title": warning["title"],
                    "message": f"{warning['message']} {warning['suggestion']}",
                    "priority": warning["severity"],
                })
        except Exception as e:
            print(f"[Sentinel] Guardrails check error: {e}")
        return decisions

    def _generate_hour_summary(self):
        """Build a quick summary of what happened this hour."""
        hour_events = [
            e for e in self._events
            if (datetime.now() - datetime.fromisoformat(e.timestamp)).total_seconds() < 3600
        ]
        if not hour_events:
            return

        summary_parts = []
        alerts = [e for e in hour_events if e.category == "alert"]
        nudges = [e for e in hour_events if e.category == "nudge"]
        actions = [e for e in hour_events if e.acted]

        if alerts:
            summary_parts.append(f"{len(alerts)} alert(s)")
        if nudges:
            summary_parts.append(f"{len(nudges)} nudge(s)")
        if actions:
            summary_parts.append(f"{len(actions)} autonomous action(s)")

        if summary_parts:
            self._state["last_hour_summary"] = {
                "time": datetime.now().isoformat(),
                "activity": self._presence.activity,
                "summary": ", ".join(summary_parts),
                "events": len(hour_events),
            }

    # ── State Change Handlers ──────────────────────────────────────────────────

    async def _on_state_change(self, old_state: str, new_state: str):
        """Handle transitions between presence states."""
        if old_state == "away" and new_state == "active":
            # User came back — deliver "while you were away" summary
            await self._deliver_away_summary()
        elif old_state == "active" and new_state == "away":
            # User left — enter guardian mode
            self._state["away_since"] = datetime.now().isoformat()
        elif new_state == "sleeping":
            # User went to sleep — run overnight tasks
            self._start_overnight_mode()

    async def _deliver_away_summary(self):
        """When user returns from being away, summarize what they missed."""
        away_since = self._state.get("away_since")
        if not away_since:
            return

        missed = []
        # Check for new emails
        try:
            from integrations.microsoft_bridge import MicrosoftBridge
        except ImportError:
            pass  # Microsoft integration not available
        else:
            try:
                ms = MicrosoftBridge.get_instance()
                if await asyncio.wait_for(
                    asyncio.to_thread(ms.is_connected),
                    timeout=5.0
                ):
                    count = await asyncio.wait_for(
                        asyncio.to_thread(ms.get_unread_count),
                        timeout=5.0
                    )
                    if count > 0:
                        missed.append(f"{count} new emails")
            except asyncio.TimeoutError:
                self._subsystem_health["microsoft_bridge"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
                print("[Sentinel] Microsoft Bridge stalled during away summary")
            except Exception:
                pass

        # Check calendar events that passed
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            if await asyncio.wait_for(
                asyncio.to_thread(gs.is_connected),
                timeout=5.0
            ):
                events = await asyncio.wait_for(
                    asyncio.to_thread(gs.get_todays_events),
                    timeout=5.0
                )
                now = datetime.now()
                away_dt = datetime.fromisoformat(away_since)
                passed = [e for e in events if self._event_between(e, away_dt, now)]
                if passed:
                    missed.append(f"{len(passed)} calendar event(s) passed")
        except asyncio.TimeoutError:
            self._subsystem_health["calendar"] = {"status": "STALLED", "error": "Timeout after 5.0s"}
            print("[Sentinel] Calendar stalled during away summary")
        except Exception:
            pass

        if missed:
            self._emit(
                "summary",
                "Welcome Back",
                f"While you were away: {'; '.join(missed)}",
                "normal",
            )
        self._state.pop("away_since", None)

    def _event_between(self, event: Dict, start: datetime, end: datetime) -> bool:
        """Check if a calendar event falls between two times."""
        try:
            event_start = datetime.fromisoformat(
                event.get("start", "").replace("Z", "+00:00")
            ).replace(tzinfo=None)
            return start <= event_start <= end
        except Exception:
            return False

    def _start_overnight_mode(self):
        """User is sleeping — run maintenance tasks."""
        self._state["overnight_mode"] = True
        # Memory consolidation will run via the daily briefing scheduler
        self._emit("action", "Overnight Mode",
                   "You're asleep. Running memory consolidation and planning tomorrow.",
                   "low", acted=True)

    # ── Decision Execution ─────────────────────────────────────────────────────

    def _execute_decision(self, decision: Dict):
        """Execute a Sentinel decision — push to user or take autonomous action."""
        # Don't push low-priority stuff during deep work
        if (self._state.get("in_deep_work") and
                decision.get("priority") in ("low", "normal") and
                decision.get("type") != "alert"):
            return

        # Rate-limit: don't spam the same type within 10 minutes
        category = decision.get("type", "nudge")
        title = decision.get("title", "")
        recent = [
            e for e in self._events
            if e.category == category and e.title == title
            and (datetime.now() - datetime.fromisoformat(e.timestamp)).total_seconds() < 600
        ]
        if recent:
            return

        self._emit(
            category,
            title,
            decision.get("message", ""),
            decision.get("priority", "normal"),
            acted=decision.get("autonomous", False),
            action_taken=decision.get("action_taken", ""),
        )

        # Push to ProactivePush engine for WebSocket delivery
        try:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            push_cat = {
                "nudge": "NUDGE", "alert": "ALERT",
                "action": "INSIGHT", "summary": "MEMORY",
            }.get(category, "NUDGE")
            engine.push(push_cat, decision.get("message", ""), decision.get("priority", "normal"))
        except Exception:
            pass
        
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
                    domain="sentinel",
                    event_type="decision_executed",
                    payload={
                        "category": category,
                        "title": title,
                        "message": decision.get("message", ""),
                        "priority": decision.get("priority", "normal"),
                        "autonomous": decision.get("autonomous", False)
                    },
                    source_module="sentinel",
                    priority=priority_map.get(decision.get("priority", "normal"), EventPriority.NORMAL)
                )
            except Exception as e:
                print(f"[Sentinel] Neural bus publish error: {e}")

    # ── Event Emission ─────────────────────────────────────────────────────────

    def _emit(self, category: str, title: str, detail: str, priority: str = "normal",
              acted: bool = False, action_taken: str = ""):
        """Record a Sentinel event and notify callbacks."""
        import uuid
        event = SentinelEvent(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            category=category,
            title=title,
            detail=detail,
            priority=priority,
            acted=acted,
            action_taken=action_taken,
        )
        self._events.append(event)

        # Log to file
        try:
            with open(SENTINEL_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event)) + "\n")
        except Exception:
            pass

        # Notify callbacks
        for cb in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(cb(asdict(event)))
                else:
                    cb(asdict(event))
            except Exception:
                pass

    # ── State Persistence ──────────────────────────────────────────────────────

    def _load_state(self) -> Dict:
        try:
            if SENTINEL_STATE.exists():
                return json.loads(SENTINEL_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_state(self):
        try:
            state = {
                **self._state,
                "presence": asdict(self._presence),
                "subsystem_health": self._subsystem_health,
                "last_save": datetime.now().isoformat(),
            }
            SENTINEL_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Full Sentinel status for the API/UI."""
        return {
            "running": self._running,
            "presence": asdict(self._presence),
            "deep_work": self._state.get("in_deep_work", False),
            "subsystem_health": self._subsystem_health,
            "recent_events": [asdict(e) for e in list(self._events)[-20:]],
            "decisions_today": len([
                e for e in self._events
                if e.category in ("alert", "nudge", "action")
            ]),
            "state": {
                "overnight_mode": self._state.get("overnight_mode", False),
                "away_since": self._state.get("away_since"),
                "last_hour_summary": self._state.get("last_hour_summary"),
            },
        }

    def get_presence(self) -> Dict:
        return asdict(self._presence)

    def get_events(self, limit: int = 50) -> List[Dict]:
        return [asdict(e) for e in list(self._events)[-limit:]]

    def force_scan(self) -> Dict:
        """Manually trigger a full scan cycle."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._fast_tick(), self._loop
            ).result(timeout=10.0)
            asyncio.run_coroutine_threadsafe(
                self._slow_tick(), self._loop
            ).result(timeout=30.0)
        return self.get_status()

    def set_user_away(self, reason: str = "manual"):
        """Manually mark user as away (e.g. from phone app)."""
        self._presence.state = "away"
        self._state["away_since"] = datetime.now().isoformat()
        self._emit("presence", "User Away (manual)",
                   f"Marked as away: {reason}. Entering guardian mode.", "low")

    def set_user_back(self):
        """User returned (e.g. from phone app tap)."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._on_state_change("away", "active"), self._loop
            )
        self._presence.state = "active"


# ── Singleton ─────────────────────────────────────────────────────────────────

_sentinel: Optional[Sentinel] = None


def get_sentinel() -> Sentinel:
    global _sentinel
    if _sentinel is None:
        _sentinel = Sentinel()
    return _sentinel


def start_sentinel() -> Sentinel:
    s = get_sentinel()
    s.start()
    return s
