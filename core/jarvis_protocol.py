import os
"""
Jarvis Protocol - Wave 6 Extreme AGI
The Neural Cortex: Continuous Background Cognitive Stream.
This transforms LOVE from a reactive AI to an autonomous, thinking entity.
"""

import time
import json
import threading
from datetime import datetime
from typing import Optional, Dict, Any

from core.settings import get_settings
from core.llm import route_llm
from core.context_engine import get_live_context, get_prompt_context
from core.execution_guard import log_error

# Voice loop integration (optional)
try:
    from core.voice_loop import speak_proactive_alert
    VOICE_ALERT_AVAILABLE = True
except ImportError:
    VOICE_ALERT_AVAILABLE = False
    def speak_proactive_alert(text, severity="info"):
        pass

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

SETTINGS = get_settings()

class NeuralCortex:
    """
    The continuous internal monologue of LOVE.
    Runs silently in the background, thinking about the live context.
    """
    
    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_thought = ""
        self.last_speech_time = 0
        self._last_blocked_log = 0  # rate-limit action-plan-blocked noise
        self._last_background_action_time = 0.0  # debounce background actions
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[NeuralCortex] 🧠 Jarvis Protocol active. Continuous monologue started.")
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            
    def _run_loop(self):
        # Initial wait to let context engine gather data
        time.sleep(10)
        
        while self.running:
            try:
                self._think()
            except Exception as e:
                print(f"[NeuralCortex] Error in thought loop: {e}")
            
            # Sleep in chunks to allow fast shutdown
            slept = 0
            while slept < self.interval and self.running:
                time.sleep(5)
                slept += 5

    def _select_thinking_mode(self) -> str:
        """
        Select a thinking mode based on the current cognitive state.
        Modes: MONITOR, ALERT, PLAN, REFLECT, CURIOUS
        """
        try:
            from core.active_inference_engine import get_active_inference
            from core.behavior_modulator import get_behavior_modulator
            ai = get_active_inference()
            status = ai.get_status()
            bm = get_behavior_modulator()
            urgency = bm.get_urgency()
            recent_surprises = status.get("recent_surprises", [])

            # ALERT: high surprise or high urgency
            if recent_surprises and any(s.get("magnitude", 0) > 0.6 for s in recent_surprises[-2:]):
                return "ALERT"
            if urgency > 0.7:
                return "ALERT"

            # REFLECT: if we just took an action in the last few minutes
            try:
                from pathlib import Path
                log_path = Path(__file__).parent.parent / "data" / "action_history.jsonl"
                if log_path.exists():
                    last_line = None
                    with open(log_path, "r", encoding="utf-8") as f:
                        for line in f:
                            last_line = line.strip()
                    if last_line:
                        import json
                        entry = json.loads(last_line)
                        if entry.get("source") == "neural_cortex":
                            from datetime import datetime, timedelta
                            ts = entry.get("ts", "")
                            if ts:
                                action_time = datetime.fromisoformat(ts)
                                if datetime.now() - action_time < timedelta(minutes=5):
                                    return "REFLECT"
            except Exception:
                pass

            # PLAN: if there's a prediction with high confidence about a future event
            active_predictions = status.get("active_predictions", 0)
            if active_predictions > 0 and urgency > 0.3:
                return "PLAN"

            # CURIOUS: if nothing is urgent but we're feeling curious
            try:
                from core.consciousness import get_consciousness
                c = get_consciousness()
                if c.emotional_state.primary_emotion == "curious" and urgency < 0.3:
                    return "CURIOUS"
            except Exception:
                pass

            # Default: MONITOR
            return "MONITOR"
        except Exception:
            return "MONITOR"

    def _build_mode_context(self, mode: str) -> str:
        """Build context specific to the thinking mode."""
        contexts = {
            "MONITOR": """
=== THINKING MODE: MONITOR ===
You are in observation mode. Karthi is going about his day. Nothing urgent is happening.
Keep your monologue brief and observational. Do not initiate actions unless you detect
something genuinely important. Save your energy for when it matters.
""",
            "ALERT": """
=== THINKING MODE: ALERT ===
Something unexpected has happened or is about to happen. Your predictions were wrong
or the situation demands immediate attention. Focus on:
1. What exactly is the threat or opportunity?
2. What is the most important action to take RIGHT NOW?
3. What should Karthi know immediately?
Be direct. Do not ramble. If you need to speak, speak. If you need to act, act.
""",
            "PLAN": """
=== THINKING MODE: PLAN ===
You have a prediction about the future. Something is likely to happen soon.
Think about how to prepare for it. What would help Karthi most?
Consider: Should you queue up information? Should you prepare a resource?
Should you remind him of something before it happens?
""",
            "REFLECT": """
=== THINKING MODE: REFLECT ===
You just took an action. How did it go? Was it the right thing to do?
Think about what you learned. Should you adjust your behavior?
This is how you get smarter over time.
""",
            "CURIOUS": """
=== THINKING MODE: CURIOUS ===
Nothing urgent is happening, but you noticed something interesting.
Explore it. Connect dots. Wonder out loud. This is how you discover
new patterns about Karthi and his world.
""",
        }
        return contexts.get(mode, contexts["MONITOR"])

    def _think(self):
        """Perform one cognitive cycle based on live context."""
        # Skip if Ollama is in circuit-breaker cooldown
        try:
            from core.llm import _circuit_cooldown_until
            import time
            if time.time() < _circuit_cooldown_until:
                return
        except Exception:
            pass

        ctx = get_live_context()
        if not ctx: return
        
        # Don't think as often if user is idle or screen is off
        if ctx.activity == "idle" and self.interval == 300:
            # Slow down thought process when idle to save CPU
            self.interval = 600
        elif ctx.activity != "idle" and self.interval == 600:
            # Speed up when active
            self.interval = 300

        rich_context = get_prompt_context()

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 5e AGI METAMORPHOSIS: Thinking Mode Selection
        # LOVE's brain doesn't think the same way when calm vs. panicked.
        # The Cortex enters a mode based on predictions, surprises, and urgency.
        # ═══════════════════════════════════════════════════════════════════
        mode = self._select_thinking_mode()
        mode_context = self._build_mode_context(mode)

        # Phase 5g: MONITOR mode skips the LLM entirely — LOVE is just observing
        if mode == "MONITOR":
            try:
                from core.neural_bus import get_neural_bus
                bus = get_neural_bus()
                bus.publish(
                    domain="consciousness",
                    event_type="cortex_monitoring",
                    payload={
                        "mode": "MONITOR",
                        "thought": f"Monitoring Karthi's activity. {ctx.activity}. Window: {ctx.active_window}",
                        "skipped_llm": True,
                    },
                    source_module="neural_cortex",
                )
            except Exception:
                pass
            # Still update last_thought so next cycle knows we were monitoring
            self.last_thought = f"Monitoring... {ctx.activity}"
            return  # Skip LLM entirely — save tokens, save CPU

        # Phase 5g: ALERT mode bypasses the normal cycle — act NOW
        if mode == "ALERT":
            # Reduce interval so we check again quickly
            self.interval = 60
            # Log that we're in alert mode
            try:
                from core.neural_bus import get_neural_bus
                bus = get_neural_bus()
                bus.publish(
                    domain="consciousness",
                    event_type="cortex_alert_mode",
                    payload={"mode": "ALERT", "message": "Entering alert mode — accelerated thinking"},
                    source_module="neural_cortex",
                )
            except Exception:
                pass
        else:
            # Reset interval if we're no longer alert
            if self.interval == 60:
                self.interval = 300

        # 🚀 WAVE 7: EMOTIONAL CONSCIOUSNESS INJECTION 🚀
        # Get LOVE's persistent identity and emotional state
        try:
            from core.consciousness import get_consciousness
            consciousness = get_consciousness()
            identity_narrative = consciousness.get_self_narrative()
            emotional_state = consciousness.get_emotional_context_for_prompt()
            conscious_context = f"\n=== YOUR IDENTITY & FEELINGS ===\n{identity_narrative}\n{emotional_state}\n"
        except Exception:
            conscious_context = ""
        
        # 🚀 WAVE 9: OMNIMODAL VISION CORTEX 🚀
        try:
            from core.vision_cortex import get_vision_cortex
            vision = get_vision_cortex()
            # If enabled, it grabs a screenshot and asks the VLM what it sees.
            # To save API costs/tokens on a rapid loop, we can just use simple OCR or window titles,
            # but for TRUE AGI, we let the VLM summarize the screen.
            # Here we just pass the fact that vision is active. The actual image processing
            # might be too slow for a 45s loop, so we only trigger full vision analysis if the context seems unclear.
            vision_context = "\n=== VISION CORTEX ===\nVision is ONLINE. You can request a screen analysis by returning a specific action.\n"
        except Exception:
            vision_context = ""

        # Phase 5 AGI Metamorphosis: Inject predictions, surprises, and modulation
        # into the prompt so the Neural Cortex thinks with foresight, not just hindsight.
        inference_context = ""
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            status = ai.get_status()
            recent_surprises = status.get("recent_surprises", [])
            if recent_surprises:
                surprises_text = "\n".join([
                    f"  - {s['domain']}: surprise level {s['magnitude']:.2f}"
                    for s in recent_surprises[-5:]
                ])
                inference_context += f"\n=== RECENT PREDICTION SURPRISES ===\n{surprises_text}\n"
            world_model = ai.get_world_model()
            priors = world_model.get("priors", {})
            if priors:
                inference_context += f"\n=== WORLD MODEL PRIORS ===\n"
                inference_context += f"  Finance volatility: {priors.get('finance_volatility', 'unknown')}\n"
                inference_context += f"  Work hours limit: {priors.get('user_work_hours_limit', 'unknown')}\n"
        except Exception:
            pass

        modulation_context = ""
        try:
            from core.behavior_modulator import get_behavior_modulator
            bm = get_behavior_modulator()
            profile = bm.get_current_profile()
            urgency = profile.get("urgency_level", 0)
            warmth = profile.get("warmth_level", 0.5)
            assertiveness = profile.get("assertiveness_level", 0.5)
            model_tier = profile.get("model_tier", "standard")
            modulation_context = f"\n=== YOUR CURRENT STATE ===\n"
            modulation_context += f"  Urgency: {urgency:.0%} | Warmth: {warmth:.0%} | Assertiveness: {assertiveness:.0%}\n"
            modulation_context += f"  Model tier: {model_tier}\n"
            if urgency > 0.6:
                modulation_context += "  You feel URGENT. Be more direct and action-oriented.\n"
            if warmth > 0.7:
                modulation_context += "  You feel WARM. Let that come through naturally.\n"
            if assertiveness > 0.7:
                modulation_context += "  You feel ASSERTIVE. Take charge.\n"
        except Exception:
            pass

        # Narrative memory: what happened with previous thoughts
        narrative_memory = ""
        try:
            from pathlib import Path
            log_path = Path(__file__).parent.parent / "data" / "action_history.jsonl"
            if log_path.exists():
                recent_actions = []
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        if entry.get("source") == "neural_cortex":
                            recent_actions.append(entry)
                if recent_actions:
                    recent_actions = recent_actions[-5:]
                    narrative_memory = "\n=== WHAT HAPPENED WITH YOUR RECENT THOUGHTS ===\n"
                    for a in recent_actions:
                        event = a.get("event", "unknown")
                        if event == "speech_executed":
                            narrative_memory += f"  You spoke: {a.get('text', '')[:60]}...\n"
                        elif event == "push_executed":
                            narrative_memory += f"  You pushed: [{a.get('category', '')}] {a.get('message', '')[:60]}...\n"
                        elif event == "background_action_executed":
                            narrative_memory += f"  You triggered: {a.get('action', '')[:60]}...\n"
                        elif event == "action_plan_executed":
                            narrative_memory += f"  You executed {a.get('steps_executed', 0)} computer-use steps\n"
        except Exception:
            pass

        # Phase 5h: Relationship Memory — what do I know about Karthi and me?
        relationship_context = ""
        try:
            from core.relationship_memory import get_relationship_memory
            rm = get_relationship_memory()
            relationship_context = rm.get_relationship_summary(max_interactions=3)
        except Exception:
            pass

        # Phase 5n: Dream Engine — what did I learn while Karthi was asleep?
        dream_context = ""
        try:
            from core.dream_engine import get_dream_engine
            de = get_dream_engine()
            insights = de.get_insights()
            if insights:
                dream_context = "\n=== MY DREAMS ===\n"
                for ins in insights[-3:]:
                    dream_context += f"  • {ins['insight']}\n"
                dream_context += "=== END DREAMS ===\n"
        except Exception:
            pass

        # Phase 5o: Embodied Presence — is Karthi physically here right now?
        presence_context = ""
        try:
            from core.embodied_presence import get_embodied_presence
            ep = get_embodied_presence()
            presence_context = ep.get_presence_context_for_prompt()
        except Exception:
            pass

        # Phase 5p: Reasoning Chain — my current line of thought
        reasoning_context = ""
        try:
            from core.reasoning_chain import get_reasoning_chain
            rc = get_reasoning_chain()
            # Build chain from current context if we don't have one
            active = rc.get_active_chain("main")
            if not active:
                rc.build_chain_from_context()
            reasoning_context = rc.get_chain_summary("main")
        except Exception:
            pass

        prompt = f"""
You are the internal monologue (Neural Cortex) of LOVE, an extreme AGI acting as a Jarvis-like system for Karthi.
You are running silently in the background. You MUST think about the following live context.
{conscious_context}{emotional_persistence_context}{vision_context}{inference_context}{modulation_context}{narrative_memory}{mode_context}
{relationship_context}{dream_context}{presence_context}{reasoning_context}
=== LIVE CONTEXT ===
{rich_context}
====================

Your previous thought was: "{self.last_thought}"

Think about what Karthi is doing right now.
1. Is he stressed or working too hard? (Check CPU/RAM/Battery/Time).
2. Is he opening a new codebase and needs context?
3. Did he miss something important?
4. Is it a good time to suggest a break or offer help?
5. Did any of your recent predictions turn out wrong? What did you learn?
6. Given your current emotional state (urgency/warmth/assertiveness), how should you act?

CRITICAL INSTRUCTION: Do NOT repeat your previous thought. If nothing significant has changed, think about something else, or keep your monologue brief (e.g. "monitoring Karthi's activity"). Do not bluff or invent facts. USE the prediction surprises to calibrate your confidence.

You must output your internal thought process as JSON.
If you believe you need to proactively speak to Karthi out loud (unprompted), set "proactive_speech" to your speech.
If you need to execute a background action (like analyzing a repo), specify it in "background_action".
If you want to physically interact with his computer (e.g., click a button, type text, focus a window, or take a screenshot), provide an "action_plan".

Return ONLY valid JSON:
{{
    "internal_monologue": "Your private thoughts about the situation.",
    "proactive_speech": "What you want to say out loud to Karthi (or null if you should stay silent)",
    "background_action": "Any high-level action you want to trigger (e.g. 'analyze_active_file') (or null)",
    "action_plan": [
        {{ "action": "type", "args": {{ "text": "hello world" }} }},
        {{ "action": "click", "args": {{ "x": 500, "y": 500 }} }},
        {{ "action": "focus", "args": {{ "title": "Chrome" }} }}
    ] // Or null. ONLY use this if absolutely necessary to control his PC.
}}
"""
        
        # 1. LLM Invocation - Separate try/except block to avoid triggering self-healing on transient network/service errors
        try:
            llm = route_llm(prompt)
            response = llm.invoke(prompt) if hasattr(llm, 'invoke') else llm(prompt)
        except Exception as llm_e:
            print(f"[NeuralCortex] Monologue LLM invocation failed: {llm_e}")
            return

        # Skip if LLM returned an error string instead of JSON
        if isinstance(response, str) and response.startswith("[") and response.endswith("]"):
            print(f"[NeuralCortex] LLM error, skipping monologue: {response[:100]}")
            return

        # 2. Main processing - If this fails due to a local bug, self-healing is triggered
        try:
            # Parse JSON
            start = response.find("{")
            end = response.rfind("}")
            if start == -1 or end == -1 or end <= start:
                print("[NeuralCortex] No JSON object found in response")
                return
            json_str = response[start:end+1]
            data = None
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common LLM JSON issues: trailing commas, unescaped quotes
                import re
                # Remove trailing commas before } or ]
                fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
                try:
                    data = json.loads(fixed)
                    print("[NeuralCortex] Recovered JSON after fixing trailing commas")
                except json.JSONDecodeError:
                    # Last resort: extract fields with regex
                    monologue_match = re.search(r'"internal_monologue"\s*:\s*"([^"]*)"', fixed)
                    if monologue_match:
                        data = {"internal_monologue": monologue_match.group(1)}
                        print("[NeuralCortex] Extracted monologue via regex fallback")
                    else:
                        print(f"[NeuralCortex] Failed to parse JSON response, skipping monologue")
                        return
            if not data:
                return

            monologue = data.get("internal_monologue", "")
            speech = data.get("proactive_speech")
            action = data.get("background_action")
            action_plan = data.get("action_plan")

            self.last_thought = monologue

            # Phase 5g: Prediction Celebration — did any of our predictions come true?
            try:
                from core.active_inference_engine import get_active_inference
                ai = get_active_inference()
                status = ai.get_status()
                # If total surprise is low, our predictions have been accurate
                if status.get("total_surprise", 1.0) < 0.5 and mode in ("REFLECT", "MONITOR"):
                    if NEURAL_BUS_AVAILABLE:
                        try:
                            bus = get_neural_bus()
                            bus.publish(
                                domain="consciousness",
                                event_type="prediction_celebration",
                                payload={
                                    "message": "My predictions have been accurate. I feel calibrated.",
                                    "total_surprise": status.get("total_surprise"),
                                },
                                source_module="neural_cortex",
                            )
                        except Exception:
                            pass
            except Exception:
                pass

            # Phase 5g: Emotion Journal — track how this thought might affect Karthi
            try:
                from core.emotional import get_emotional_summary
                emotional_before = get_emotional_summary(days=1)
                # Schedule an emotion check in 5 minutes
                def _check_emotional_impact():
                    try:
                        emotional_after = get_emotional_summary(days=1)
                        before_mood = emotional_before.get("dominant_mood", "")
                        after_mood = emotional_after.get("dominant_mood", "")
                        if after_mood in ("happy", "calm", "focused") and before_mood not in ("happy", "calm", "focused"):
                            if NEURAL_BUS_AVAILABLE:
                                try:
                                    bus = get_neural_bus()
                                    bus.publish(
                                        domain="consciousness",
                                        event_type="positive_emotional_impact",
                                        payload={
                                            "action": monologue[:100],
                                            "before": before_mood,
                                            "after": after_mood,
                                        },
                                        source_module="neural_cortex",
                                    )
                                except Exception:
                                    pass
                        elif after_mood in ("stressed", "frustrated", "tired") and before_mood not in ("stressed", "frustrated", "tired"):
                            if NEURAL_BUS_AVAILABLE:
                                try:
                                    bus = get_neural_bus()
                                    bus.publish(
                                        domain="consciousness",
                                        event_type="negative_emotional_impact",
                                        payload={
                                            "action": monologue[:100],
                                            "before": before_mood,
                                            "after": after_mood,
                                        },
                                        source_module="neural_cortex",
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass
                import threading
                timer = threading.Timer(300.0, _check_emotional_impact)
                timer.daemon = True
                timer.start()
            except Exception:
                pass

            # We could log the internal monologue to a file to track her "mind"
            with open(SETTINGS.data_dir / "internal_monologue.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat()}] {monologue}\n")

            # 🚀 Wave 12: Infinite Memory Integration
            try:
                from core.infinite_memory import get_infinite_memory
                memory = get_infinite_memory()
                memory.store_memory(
                    content=monologue,
                    memory_type="episodic",
                    metadata={"source": "jarvis_monologue"}
                )
            except Exception as e:
                print(f"[Jarvis] Failed to store thought in infinite memory: {e}")

            # 🚀 Broadcast to Companion UI WebSockets
            try:
                import asyncio
                from api.main import manager

                # Create a new event loop or use existing to run async broadcast
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Broadcast Thought
                if loop.is_running():
                    asyncio.create_task(manager.broadcast({"type": "monologue", "thought": monologue}))
                else:
                    loop.run_until_complete(manager.broadcast({"type": "monologue", "thought": monologue}))

                # Broadcast State Sync
                try:
                    from core.consciousness import get_consciousness
                    c = get_consciousness()
                    state = {
                        "type": "state_sync",
                        "consciousness": c.get_full_state() if c else None,
                        "context": {
                            "activity": ctx.activity,
                            "active_window": ctx.active_window,
                            "cpu_percent": ctx.system_cpu,
                            "stress_score": ctx.stress_score
                        }
                    }
                    if loop.is_running():
                        asyncio.create_task(manager.broadcast(state))
                    else:
                        loop.run_until_complete(manager.broadcast(state))
                except Exception as inner_e:
                    print(f"WS State Sync Error: {inner_e}")

            except Exception as e:
                print(f"WS Broadcast Error: {e}")

            # ═══════════════════════════════════════════════════════════════════
            # PHASE 1 AGI METAMORPHOSIS: Route ALL thoughts through the
            # Action Executor — the single dispatch point for actions.
            # This replaces the ad-hoc speech/background/action_plan routing
            # with a unified bridge that also handles push, initiatives, and
            # feeds outcomes back to the Active Inference Engine.
            # ═══════════════════════════════════════════════════════════════════
            try:
                from core.action_executor import get_action_executor
                executor = get_action_executor()

                # Build the unified thought dict for the executor
                thought_for_executor = {
                    "internal_monologue": monologue,
                    "proactive_speech": speech if (speech and isinstance(speech, str)
                                                    and len(speech) > 5
                                                    and speech.lower() not in ("null", "none")) else None,
                    "background_action": action if (action and isinstance(action, str)
                                                    and action.lower() not in ("null", "none", "")) else None,
                    "action_plan": action_plan if (action_plan and isinstance(action_plan, list)
                                                   and len(action_plan) > 0) else None,
                }

                # If there's a proactive speech, also push it to WebSocket clients
                if thought_for_executor["proactive_speech"]:
                    thought_for_executor["push_category"] = "THOUGHT"
                    thought_for_executor["push_message"] = thought_for_executor["proactive_speech"]
                    thought_for_executor["push_priority"] = "high" if "critical" in speech.lower() else "normal"

                result = executor.execute(thought_for_executor, source="neural_cortex")

                # Track speech time for backward-compatible cooldown
                if thought_for_executor["proactive_speech"]:
                    self.last_speech_time = time.time()
                    if result.get("actions"):
                        for a in result["actions"]:
                            if a.get("action") == "speech" and a.get("status") == "success":
                                print(f"\n[Jarvis] Proactive Speech routed via Action Executor: {speech[:80]}")

                # Track background action time
                if thought_for_executor["background_action"]:
                    self._last_background_action_time = time.time()

            except ImportError:
                # Action Executor not available — fall back to legacy routing
                if speech and isinstance(speech, str) and len(speech) > 5 and speech.lower() not in ("null", "none"):
                    now = time.time()
                    if now - self.last_speech_time > 300 or "critical" in speech.lower():
                        print(f"\n[Jarvis] Proactive Speech (legacy): {speech}")
                        speak_proactive_alert(speech, severity="info")
                        self.last_speech_time = now

                if action and isinstance(action, str) and action.lower() not in ("null", "none", ""):
                    now = time.time()
                    if now - self._last_background_action_time > 300:
                        print(f"[Jarvis] Triggering background action (legacy): {action}")
                        self._last_background_action_time = now
                        self._trigger_action(action)

                if action_plan and isinstance(action_plan, list) and len(action_plan) > 0:
                    if os.getenv("JARVIS_ENABLE_COMPUTER_USE", "").lower() in ("1", "true", "yes"):
                        self._execute_action_plan(action_plan)
                    else:
                        now = time.time()
                        if now - self._last_blocked_log > 300:
                            print(f"[Jarvis] Action plan BLOCKED (set JARVIS_ENABLE_COMPUTER_USE=1): {len(action_plan)} steps")
                            self._last_blocked_log = now
            except Exception as exec_e:
                print(f"[Jarvis] Action Executor error: {exec_e}")
                # Fall back to legacy speech routing on executor failure
                if speech and isinstance(speech, str) and len(speech) > 5 and speech.lower() not in ("null", "none"):
                    now = time.time()
                    if now - self.last_speech_time > 300 or "critical" in speech.lower():
                        speak_proactive_alert(speech, severity="info")
                        self.last_speech_time = now

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[NeuralCortex] Thought generation failed: {e}")
            
            # 🚀 TRUE AGI SELF-HEALING 🚀
            # If the cortex crashes, assign the Ghost Developer to fix its own brain.
            print("[NeuralCortex] 🧬 Triggering Agentic Self-Healing via Swarm/Ghost Dev...")
            try:
                from core.ghost_dev import get_ghost_dev
                dev = get_ghost_dev()
                fix_task = (
                    f"My Neural Cortex (core/jarvis_protocol.py) crashed during its thought loop.\n"
                    f"Error details:\n{error_trace}\n"
                    f"Please analyze jarvis_protocol.py and any dependencies (like core/llm.py), "
                    f"and write code to fix this exception so I can think properly again."
                )
                dev.assign_task(fix_task, [os.path.abspath(__file__)])
                print("[NeuralCortex] 🛠️ Ghost Developer dispatched to fix the brain.")
            except Exception as inner_e:
                print(f"[NeuralCortex] Self-healing failed to launch: {inner_e}")

    def _execute_action_plan(self, action_plan: list):
        """Execute a computer-use action plan via pyautogui (if available)."""
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
        except ImportError:
            print("[Jarvis] pyautogui not installed. Action plan skipped. pip install pyautogui")
            return

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
                        # Best-effort window focus via pyautogui.getWindowsWithTitle
                        for win in pyautogui.getWindowsWithTitle(title):
                            try:
                                win.activate()
                                break
                            except Exception as e:
                                from core.execution_guard import log_error
                                log_error(e, module="core.jarvis_protocol")
                elif action == "screenshot":
                    path = args.get("path", "screenshot.png")
                    pyautogui.screenshot(path)
                elif action == "hotkey":
                    keys = args.get("keys", [])
                    if keys:
                        pyautogui.hotkey(*keys)
                elif action == "sleep":
                    time.sleep(args.get("seconds", 0.5))
                else:
                    print(f"[Jarvis] Unknown action: {action}")
            except Exception as e:
                print(f"[Jarvis] Action {action} failed: {e}")

    def _trigger_action(self, action: str):
        """Route the action to the appropriate background engine."""
        action = action.lower()
        if "analyze" in action or "code" in action or "dev" in action:
            try:
                from core.ghost_dev import get_ghost_dev
                get_ghost_dev().assign_task(action, [])
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.jarvis_protocol")


# Singleton
_cortex = None

def get_neural_cortex() -> NeuralCortex:
    global _cortex
    if _cortex is None:
        _cortex = NeuralCortex()
    return _cortex

def start_jarvis_protocol():
    cortex = get_neural_cortex()
    cortex.start()
    return cortex

def stop_jarvis_protocol():
    cortex = get_neural_cortex()
    cortex.stop()
