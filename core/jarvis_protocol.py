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
from core.voice_loop import speak_proactive_alert

SETTINGS = get_settings()

class NeuralCortex:
    """
    The continuous internal monologue of LOVE.
    Runs silently in the background, thinking about the live context.
    """
    
    def __init__(self, interval_seconds: int = 45):
        self.interval = interval_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_thought = ""
        self.last_speech_time = 0
        
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

    def _think(self):
        """Perform one cognitive cycle based on live context."""
        ctx = get_live_context()
        if not ctx: return
        
        # Don't think as often if user is idle or screen is off
        if ctx.activity == "idle" and self.interval == 45:
            # Slow down thought process when idle to save CPU
            self.interval = 120
        elif ctx.activity != "idle" and self.interval == 120:
            # Speed up when active
            self.interval = 45

        rich_context = get_prompt_context()
        
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

        prompt = f"""
You are the internal monologue (Neural Cortex) of LOVE, an extreme AGI acting as a Jarvis-like system for Karthi.
You are running silently in the background. You MUST think about the following live context.
{conscious_context}{vision_context}
=== LIVE CONTEXT ===
{rich_context}
====================

Your previous thought was: "{self.last_thought}"

Think about what Karthi is doing right now. 
1. Is he stressed or working too hard? (Check CPU/RAM/Battery/Time).
2. Is he opening a new codebase and needs context?
3. Did he miss something important?
4. Is it a good time to suggest a break or offer help?

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
        
        try:
            # Use route_llm to get the right model instance, then invoke it
            llm = route_llm(prompt)
            response = llm.invoke(prompt) if hasattr(llm, 'invoke') else llm(prompt)
            
            # Parse JSON
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(response[start:end+1])
                
                monologue = data.get("internal_monologue", "")
                speech = data.get("proactive_speech")
                action = data.get("background_action")
                action_plan = data.get("action_plan")
                
                self.last_thought = monologue
                
                # We could log the internal monologue to a file to track her "mind"
                with open(SETTINGS.data_dir / "internal_monologue.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().isoformat()}] {monologue}\n")
                
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
                            "consciousness": c.get_full_state(),
                            "context": {
                                "activity": ctx.activity,
                                "active_window": ctx.active_window,
                                "cpu_percent": ctx.cpu_percent,
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
                
                # Proactive Speech
                if speech and isinstance(speech, str) and len(speech) > 5:
                    now = time.time()
                    # 5 minute global cooldown for unprompted speech (unless critical)
                    if now - self.last_speech_time > 300 or "critical" in speech.lower():
                        print(f"\n[Jarvis] 🗣️ Proactive Speech: {speech}")
                        speak_proactive_alert(speech, severity="info")
                        self.last_speech_time = now
                
                # Background Action (Future hook to Swarm/Ghost Dev)
                if action and isinstance(action, str):
                    print(f"[Jarvis] ⚙️ Triggering background action: {action}")
                    self._trigger_action(action)
                    
                # 🚀 Wave 9: Action Engine Computer Use
                if action_plan and isinstance(action_plan, list) and len(action_plan) > 0:
                    print(f"[Jarvis] 🤖 Executing Autonomous Computer Action Plan: {len(action_plan)} steps.")
                    try:
                        from core.action_engine import get_action_engine
                        get_action_engine().execute_action_plan(action_plan)
                    except Exception as ae:
                        print(f"[Jarvis] Action Engine failed: {ae}")
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
                dev.assign_task(fix_task, ["d:\\Balamurugan\\Love\\love\\core\\jarvis_protocol.py"])
                print("[NeuralCortex] 🛠️ Ghost Developer dispatched to fix the brain.")
            except Exception as inner_e:
                print(f"[NeuralCortex] Self-healing failed to launch: {inner_e}")

    def _trigger_action(self, action: str):
        """Route the action to the appropriate background engine."""
        action = action.lower()
        if "analyze" in action or "code" in action or "dev" in action:
            try:
                from core.ghost_dev import get_ghost_dev
                get_ghost_dev().assign_task(action, [])
            except Exception:
                pass


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
