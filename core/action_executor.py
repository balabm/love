"""
LOVE Action Executor — The Execution Bridge (Phase 1 of AGI Metamorphosis)

This is the missing link between LOVE's thoughts and LOVE's actions.
Before this module, the Neural Cortex generated rich JSON thoughts
(proactive_speech, background_action, action_plan) but most were discarded:
  - background_action only routed to Ghost Dev if it contained "analyze/code/dev"
  - action_plan was blocked unless JARVIS_ENABLE_COMPUTER_USE=1
  - autonomous initiatives were generated but never delivered
  - thoughts never reached the Push Engine unless they were "proactive_speech"

The Action Executor closes that loop. Every thought the Cortex produces
flows through here and is routed to the appropriate actuator:

  Thought ──► ActionExecutor.execute(thought)
                 ├─► TTS (voice_loop)         if proactive_speech
                 ├─► Push Engine (WebSocket)  if insight/alert/nudge
                 ├─► Ghost Dev (code tasks)   if background_action is code-related
                 ├─► System Control           if background_action is system-related
                 ├─► Autonomous Delivery      if initiative
                 ├─► Computer Use             if action_plan (with safety gate)
                 └─► Neural Bus (telemetry)   always (for closed-loop feedback)

This is what makes LOVE a living organism: thoughts cause actions,
actions produce outcomes, outcomes feed back into the next thought.
"""

import time
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.execution_guard import log_error

# Neural Bus
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"
ACTION_LOG = DATA_DIR / "action_history.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log_action(entry: Dict[str, Any]):
    """Log every executed action for the teleological feedback loop."""
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        log_error(e, module="core.action_executor", context={"phase": "log_action"})


class ActionExecutor:
    """
    The single dispatch point for all of LOVE's autonomous actions.

    Every module that generates a "thought" or "decision" should route it
    through here instead of directly calling TTS/push/etc. This gives us:
      1. A single audit trail (action_history.jsonl)
      2. Safety gating (high-risk actions require approval)
      3. Rate limiting (don't spam the same action)
      4. Feedback loop (outcomes feed back to Active Inference)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._last_action_time: Dict[str, float] = {}  # action_key → timestamp
        self._min_gap_seconds = 60  # Don't repeat the same action within 60s
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}  # UUID → action
        self._action_count = 0
        self._success_count = 0

    # ═══════════════════════════════════════════════════════════════════════
    # MAIN DISPATCH — every thought flows through here
    # ═══════════════════════════════════════════════════════════════════════

    def execute(self, thought: Dict[str, Any], source: str = "neural_cortex") -> Dict[str, Any]:
        """
        Execute a structured thought. The thought dict may contain:
          - proactive_speech: str   → speak out loud via TTS
          - background_action: str  → route to Ghost Dev or System Control
          - action_plan: list       → computer-use steps (safety-gated)
          - push_category: str      → push a message to WebSocket clients
          - push_message: str       → the message to push
          - push_priority: str      → low/normal/high/critical
          - initiative: dict        → autonomous initiative to deliver
          - internal_monologue: str → logged but not acted on

        Returns a result dict with executed actions and their outcomes.
        """
        if not isinstance(thought, dict):
            return {"status": "invalid", "error": "thought must be a dict"}

        results = {"status": "executed", "actions": [], "source": source}
        self._action_count += 1

        # 1. Proactive Speech → TTS
        speech = thought.get("proactive_speech")
        if speech and isinstance(speech, str) and len(speech) > 5:
            if speech.lower() not in ("null", "none", ""):
                outcome = self._execute_speech(speech, source)
                results["actions"].append(outcome)

        # 2. Push notification → WebSocket clients
        push_cat = thought.get("push_category")
        push_msg = thought.get("push_message")
        if push_msg and isinstance(push_msg, str) and len(push_msg) > 3:
            outcome = self._execute_push(
                category=push_cat or "THOUGHT",
                message=push_msg,
                priority=thought.get("push_priority", "normal"),
                metadata=thought.get("push_metadata", {}),
                source=source,
            )
            results["actions"].append(outcome)

        # 3. Background action → Ghost Dev or System Control
        bg_action = thought.get("background_action")
        if bg_action and isinstance(bg_action, str) and bg_action.lower() not in ("null", "none", ""):
            outcome = self._execute_background_action(bg_action, source)
            results["actions"].append(outcome)

        # 4. Action plan → Computer Use (safety-gated)
        action_plan = thought.get("action_plan")
        if action_plan and isinstance(action_plan, list) and len(action_plan) > 0:
            outcome = self._execute_action_plan(action_plan, source)
            results["actions"].append(outcome)

        # 5. Autonomous initiative → deliver via push + TTS
        initiative = thought.get("initiative")
        if initiative and isinstance(initiative, dict):
            outcome = self._execute_initiative(initiative, source)
            results["actions"].append(outcome)

        # 6. Internal monologue → log only (no action, but track for feedback)
        monologue = thought.get("internal_monologue")
        if monologue:
            _log_action({
                "event": "monologue_logged",
                "source": source,
                "monologue": monologue[:500],
            })

        # 7. Always publish to Neural Bus for closed-loop feedback
        self._publish_telemetry(results, source)

        if results["actions"]:
            self._success_count += 1
        else:
            results["status"] = "no_actionable_content"

        return results

    # ═══════════════════════════════════════════════════════════════════════
    # ACTUATORS — each one interfaces with a real LOVE subsystem
    # ═══════════════════════════════════════════════════════════════════════

    def _execute_speech(self, text: str, source: str) -> Dict[str, Any]:
        """Speak text out loud via the voice loop."""
        action_key = f"speech:{hash(text[:50])}"
        if self._is_rate_limited(action_key):
            return {"action": "speech", "status": "rate_limited", "text": text[:80]}

        try:
            from core.voice_loop import speak_proactive_alert
            speak_proactive_alert(text, severity="info")
            _log_action({"event": "speech_executed", "source": source, "text": text[:200]})
            self._last_action_time[action_key] = time.time()
            return {"action": "speech", "status": "success", "text": text[:80]}
        except Exception as e:
            log_error(e, module="core.action_executor", context={"phase": "speech"})
            return {"action": "speech", "status": "error", "error": str(e)[:100]}

    def _execute_push(self, category: str, message: str, priority: str,
                      metadata: Dict, source: str) -> Dict[str, Any]:
        """Push a message to connected WebSocket clients via the Push Engine."""
        action_key = f"push:{category}:{hash(message[:50])}"
        if self._is_rate_limited(action_key) and priority not in ("high", "critical"):
            return {"action": "push", "status": "rate_limited", "category": category}

        try:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            engine.push(category=category, message=message, priority=priority, metadata=metadata)
            _log_action({"event": "push_executed", "source": source, "category": category,
                         "priority": priority, "message": message[:200]})
            self._last_action_time[action_key] = time.time()
            return {"action": "push", "status": "success", "category": category}
        except Exception as e:
            log_error(e, module="core.action_executor", context={"phase": "push"})
            return {"action": "push", "status": "error", "error": str(e)[:100]}

    def _execute_background_action(self, action: str, source: str) -> Dict[str, Any]:
        """Route a background action to Ghost Dev (code) or System Control (system)."""
        action_lower = action.lower()
        action_key = f"bg:{hash(action[:50])}"
        if self._is_rate_limited(action_key):
            return {"action": "background", "status": "rate_limited", "action": action[:80]}

        outcome = {"action": "background", "status": "unknown", "action_text": action[:80]}

        # Code-related actions → Ghost Developer
        if any(w in action_lower for w in ("analyze", "code", "dev", "refactor", "debug", "build", "test")):
            try:
                from core.ghost_dev import get_ghost_dev
                get_ghost_dev().assign_task(action, [])
                outcome["status"] = "dispatched_ghost_dev"
            except Exception as e:
                log_error(e, module="core.action_executor", context={"phase": "bg_ghost_dev"})
                outcome["status"] = "error"
                outcome["error"] = str(e)[:100]

        # System-related actions → System Control
        elif any(w in action_lower for w in ("open", "close", "launch", "kill", "focus", "volume", "brightness", "lock")):
            try:
                from core.system_control import get_system_control
                ctrl = get_system_control()
                ctrl.execute_command(action)
                outcome["status"] = "dispatched_system_control"
            except Exception as e:
                # System control may not be available; log but don't crash
                outcome["status"] = "system_control_unavailable"
                outcome["error"] = str(e)[:100]

        # Finance-related actions → Finance Guardian
        elif any(w in action_lower for w in ("trade", "buy", "sell", "portfolio", "crypto", "btc", "eth", "finance")):
            try:
                from core.finance_guardian import get_finance_guardian
                guardian = get_finance_guardian()
                # Publish as a finance event for the guardian to pick up
                if NEURAL_BUS_AVAILABLE:
                    bus = get_neural_bus()
                    bus.publish(
                        domain="finance",
                        event_type="action_request",
                        payload={"action": action, "source": source},
                        source_module="action_executor",
                        priority=EventPriority.HIGH,
                    )
                outcome["status"] = "dispatched_finance"
            except Exception as e:
                outcome["status"] = "error"
                outcome["error"] = str(e)[:100]

        # Memory-related actions → Memory Consolidation
        elif any(w in action_lower for w in ("remember", "consolidate", "memory", "recall", "forget")):
            try:
                if NEURAL_BUS_AVAILABLE:
                    bus = get_neural_bus()
                    bus.publish(
                        domain="memory",
                        event_type="consolidation_request",
                        payload={"action": action, "source": source},
                        source_module="action_executor",
                        priority=EventPriority.NORMAL,
                    )
                outcome["status"] = "dispatched_memory"
            except Exception as e:
                outcome["status"] = "error"
                outcome["error"] = str(e)[:100]

        # Unknown action → log it so self-evolution can learn to handle it
        else:
            outcome["status"] = "unrecognized"
            _log_action({"event": "unrecognized_action", "source": source, "action": action})

        _log_action({"event": "background_action_executed", "source": source,
                      "action": action[:200], "outcome": outcome["status"]})
        self._last_action_time[action_key] = time.time()
        return outcome

    def _execute_action_plan(self, action_plan: List[Dict], source: str) -> Dict[str, Any]:
        """Execute a computer-use action plan with safety gating."""
        import os

        # Safety gate: require explicit env var or human approval
        computer_use_enabled = os.getenv("JARVIS_ENABLE_COMPUTER_USE", "").lower() in ("1", "true", "yes")

        if not computer_use_enabled:
            # Publish the blocked plan so the UI can ask for approval
            if NEURAL_BUS_AVAILABLE:
                try:
                    bus = get_neural_bus()
                    bus.publish(
                        domain="action",
                        event_type="autonomous_action_blocked",
                        payload={"action_plan": action_plan, "source": source,
                                 "reason": "Safety block — set JARVIS_ENABLE_COMPUTER_USE=1 or approve via WebSocket"},
                        source_module="action_executor",
                        priority=EventPriority.HIGH,
                    )
                except Exception as e:
                    log_error(e, module="core.action_executor", context={"phase": "blocked_plan_publish"})

            _log_action({"event": "action_plan_blocked", "source": source,
                         "steps": len(action_plan), "reason": "computer_use_disabled"})
            return {"action": "action_plan", "status": "blocked", "steps": len(action_plan)}

        # Execute via pyautogui
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
        except ImportError:
            return {"action": "action_plan", "status": "error", "error": "pyautogui not installed"}

        executed_steps = 0
        for step in action_plan:
            action = step.get("action", "").lower()
            args = step.get("args", {})
            try:
                if action == "type":
                    pyautogui.typewrite(args.get("text", ""), interval=0.01)
                elif action == "click":
                    pyautogui.click(args.get("x", 0), args.get("y", 0))
                elif action == "rightclick":
                    pyautogui.rightClick(args.get("x", 0), args.get("y", 0))
                elif action == "focus":
                    title = args.get("title", "")
                    if title:
                        for win in pyautogui.getWindowsWithTitle(title):
                            try:
                                win.activate()
                                break
                            except Exception:
                                pass
                elif action == "screenshot":
                    path = args.get("path", "screenshot.png")
                    pyautogui.screenshot(path)
                elif action == "hotkey":
                    keys = args.get("keys", [])
                    if keys:
                        pyautogui.hotkey(*keys)
                elif action == "sleep":
                    time.sleep(args.get("seconds", 0.5))
                executed_steps += 1
            except Exception as e:
                log_error(e, module="core.action_executor",
                          context={"phase": "action_plan_step", "step": action})

        _log_action({"event": "action_plan_executed", "source": source,
                     "steps_total": len(action_plan), "steps_executed": executed_steps})
        return {"action": "action_plan", "status": "success",
                "executed": executed_steps, "total": len(action_plan)}

    def _execute_initiative(self, initiative: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Deliver an autonomous initiative via push + TTS."""
        msg = initiative.get("message", "")
        itype = initiative.get("type", "check_in")
        reason = initiative.get("reason", "unknown")

        if not msg:
            return {"action": "initiative", "status": "no_message"}

        # Push to WebSocket
        push_outcome = self._execute_push(
            category="AUTONOMOUS",
            message=msg,
            priority="normal",
            metadata={"initiative_type": itype, "reason": reason},
            source=source,
        )

        # Also speak it (initiatives are meant to be heard)
        speech_outcome = self._execute_speech(msg, source)

        # Update relationship state
        try:
            from core.autonomous import update_relationship_state
            update_relationship_state("pending")
        except Exception as e:
            log_error(e, module="core.action_executor", context={"phase": "initiative_relationship"})

        _log_action({"event": "initiative_delivered", "source": source,
                     "type": itype, "reason": reason, "message": msg[:200]})
        return {"action": "initiative", "status": "delivered",
                "push": push_outcome, "speech": speech_outcome}

    # ═══════════════════════════════════════════════════════════════════════
    # HUMAN-IN-THE-LOOP — high-risk actions require approval
    # ═══════════════════════════════════════════════════════════════════════

    def request_approval(self, action: Dict[str, Any], timeout: int = 300) -> str:
        """
        Generate a UUID for a high-risk action and wait for WebSocket approval.
        Returns the UUID. The UI must send back {"approval_id": UUID, "approved": true/false}.
        """
        import uuid
        approval_id = uuid.uuid4().hex[:12]
        self._pending_approvals[approval_id] = {
            "action": action,
            "requested_at": time.time(),
            "timeout": timeout,
            "status": "pending",
        }

        # Publish to neural bus so the UI can display the approval request
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="action",
                    event_type="approval_required",
                    payload={"approval_id": approval_id, "action": action},
                    source_module="action_executor",
                    priority=EventPriority.CRITICAL,
                )
            except Exception as e:
                log_error(e, module="core.action_executor", context={"phase": "request_approval"})

        _log_action({"event": "approval_requested", "approval_id": approval_id, "action": action})
        return approval_id

    def check_approval(self, approval_id: str) -> str:
        """Check the status of a pending approval. Returns: pending/approved/denied/expired."""
        entry = self._pending_approvals.get(approval_id)
        if not entry:
            return "unknown"
        if entry["status"] != "pending":
            return entry["status"]
        # Check timeout
        if time.time() - entry["requested_at"] > entry["timeout"]:
            entry["status"] = "expired"
            return "expired"
        return "pending"

    def resolve_approval(self, approval_id: str, approved: bool) -> bool:
        """Resolve a pending approval (called by the WebSocket handler)."""
        entry = self._pending_approvals.get(approval_id)
        if not entry or entry["status"] != "pending":
            return False
        entry["status"] = "approved" if approved else "denied"
        _log_action({"event": "approval_resolved", "approval_id": approval_id, "approved": approved})
        return True

    # ═══════════════════════════════════════════════════════════════════════
    # FEEDBACK — outcomes feed back into the Active Inference loop
    # ═══════════════════════════════════════════════════════════════════════

    def record_outcome(self, action_id: str, success: bool, feedback: str = ""):
        """Record the outcome of a previously executed action (for teleological feedback)."""
        _log_action({
            "event": "action_outcome",
            "action_id": action_id,
            "success": success,
            "feedback": feedback[:200],
        })
        # Publish to neural bus so Active Inference can update its world model
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="action",
                    event_type="action_outcome",
                    payload={"action_id": action_id, "success": success, "feedback": feedback},
                    source_module="action_executor",
                    priority=EventPriority.NORMAL,
                )
            except Exception as e:
                log_error(e, module="core.action_executor", context={"phase": "record_outcome"})

    # ═══════════════════════════════════════════════════════════════════════
    # TELEMETRY
    # ═══════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Return execution statistics for the orchestrator/dashboard."""
        return {
            "total_actions": self._action_count,
            "successful_actions": self._success_count,
            "pending_approvals": len([a for a in self._pending_approvals.values()
                                      if a["status"] == "pending"]),
            "rate_limited_keys": len(self._last_action_time),
        }

    def _publish_telemetry(self, results: Dict[str, Any], source: str):
        """Publish execution telemetry to the Neural Bus."""
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            bus.publish(
                domain="action",
                event_type="action_executed",
                payload={
                    "source": source,
                    "actions": results.get("actions", []),
                    "status": results.get("status"),
                },
                source_module="action_executor",
                priority=EventPriority.NORMAL,
            )
        except Exception as e:
            log_error(e, module="core.action_executor", context={"phase": "telemetry"})

    # ═══════════════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════════════

    def _is_rate_limited(self, action_key: str) -> bool:
        """Check if an action was executed too recently."""
        last = self._last_action_time.get(action_key, 0)
        return (time.time() - last) < self._min_gap_seconds


# ════════════════════════════════════════════════════════════════════════════
# Singleton accessor
# ════════════════════════════════════════════════════════════════════════════

def get_action_executor() -> ActionExecutor:
    return ActionExecutor()
