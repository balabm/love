import os
from pathlib import Path

# Paths to files in workspace
workspace_dir = Path(r"C:\Users\balab\.gemini\antigravity\brain\4cc794b6-a5f4-4544-8e03-3660f8bf931b\.system_generated\worktrees\subagent-Core-Module-Auditor-module-auditor-718cf717")
agent_py = workspace_dir / "core" / "agent.py"
jarvis_py = workspace_dir / "core" / "jarvis_protocol.py"
evolution_py = workspace_dir / "core" / "evolution_engine.py"

def patch_agent():
    print("Patching core/agent.py...")
    content = agent_py.read_text(encoding="utf-8")
    
    # 1. Add datetime import
    old_imports = """from core.llm import route_llm
from core.memory import save_memory, recall_memory
from core.evolution import apply_fix, crash_monitor, format_crash_for_chat
from core.settings import get_settings
from dotenv import load_dotenv
import os
import re
import socket
import json"""

    new_imports = """from core.llm import route_llm
from core.memory import save_memory, recall_memory
from core.evolution import apply_fix, crash_monitor, format_crash_for_chat
from core.settings import get_settings
from dotenv import load_dotenv
import os
import re
import socket
import json
from datetime import datetime"""

    if old_imports in content:
        content = content.replace(old_imports, new_imports)
    else:
        # fallback if whitespace differs slightly
        content = content.replace("import json", "import json\nfrom datetime import datetime")
        
    # 2. Fix LTM import and stubs
    old_ltm = """# Long-term memory — companion for life
try:
    from core.long_term_memory import recall_memory, add_episodic, add_semantic, add_procedural
    LTM_AVAILABLE = True
except ImportError:
    LTM_AVAILABLE = False
    def recall_memory(q, mode="general", n=5): return []
    def add_episodic(**kwargs): pass
    def add_semantic(**kwargs): pass
    def add_procedural(**kwargs): pass"""

    new_ltm = """# Long-term memory — companion for life
try:
    from core.long_term_memory import remember, format_memory_for_chat, add_episodic, add_semantic, add_procedural
    LTM_AVAILABLE = True
except ImportError:
    LTM_AVAILABLE = False
    def remember(query, limit=10): return {}
    def format_memory_for_chat(memory_result): return ""
    def add_episodic(**kwargs): pass
    def add_semantic(**kwargs): pass
    def add_procedural(**kwargs): pass"""

    content = content.replace(old_ltm, new_ltm)
    
    # 3. Fix clean_response intros regexes to not consume rest of the lines
    old_intros = """    # 2. Strip generic intro phrases — match at start of ANY line
    intros = [
        r"^Here's (a breakdown|an overview|a summary|what I found|what's going on|the situation|a quick overview|what I know).*",
        r"^Based on (the data|the information|what I can see|the current data).*",
        r"^Looking at (your|the|Karthi's) (current |)situation.*",
        r"^Let me (break this down|give you an overview|summarize).*",
        r"^So (here's|this is|you have|it looks like).*",
        r"^I (can see|notice|see that|have access to).*",
        r"^According to (the data|your calendar|your email).*",
        r"^This (captures|gives|shows|is).*",
        r"^Here's a breakdown of .*",
        r"^This is (what I found|the current situation|a summary).*",
        r"^You have \\d+ (important )?unread emails?.*",
        r"^You have \\d+ (events?|tasks?|messages?).*",
        r"^Here (is|are) (a list of|your|the).*",
    ]"""

    new_intros = """    # 2. Strip generic intro phrases — match at start of ANY line
    intros = [
        r"^Here's (a breakdown|an overview|a summary|what I found|what's going on|the situation|a quick overview|what I know)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^Based on (the data|the information|what I can see|the current data)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^Looking at (your|the|Karthi's) (current |)situation(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^Let me (break this down|give you an overview|summarize)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^So (here's|this is|you have|it looks like)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^I (can see|notice|see that|have access to)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^According to (the data|your calendar|your email)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^This (captures|gives|shows|is)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^Here's a breakdown of(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^This is (what I found|the current situation|a summary)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^You have \\d+ (important )?unread emails?(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^You have \\d+ (events?|tasks?|messages?)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
        r"^Here (is|are) (a list of|your|the)(?:[^.!?]*?[:,-])?[\\.!?]?\\s*",
    ]"""

    content = content.replace(old_intros, new_intros)
    
    agent_py.write_text(content, encoding="utf-8")
    print("core/agent.py patched successfully.")

def patch_jarvis():
    print("Patching core/jarvis_protocol.py...")
    content = jarvis_py.read_text(encoding="utf-8")
    
    # Check if os is imported
    if "import os" not in content:
        content = "import os\n" + content
        
    # Replace the WS state sync check to guard against consciousness being None
    old_sync = """                    # Broadcast State Sync
                    try:
                        from core.consciousness import get_consciousness
                        c = get_consciousness()
                        state = {
                            "type": "state_sync",
                            "consciousness": c.get_full_state(),"""
                            
    new_sync = """                    # Broadcast State Sync
                    try:
                        from core.consciousness import get_consciousness
                        c = get_consciousness()
                        state = {
                            "type": "state_sync",
                            "consciousness": c.get_full_state() if c else None,"""
                            
    content = content.replace(old_sync, new_sync)
    
    # Separate LLM call from local code errors and prevent self-healing for LLM errors, and dynamicize the self-healing path
    old_think_try = """        try:
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
                
                self.last_thought = monologue"""
                
    new_think_try = """        # 1. LLM Invocation - Separate try/except block to avoid triggering self-healing on transient network/service errors
        try:
            llm = route_llm(prompt)
            response = llm.invoke(prompt) if hasattr(llm, 'invoke') else llm(prompt)
        except Exception as llm_e:
            print(f"[NeuralCortex] Monologue LLM invocation failed: {llm_e}")
            return

        # 2. Main processing - If this fails due to a local bug, self-healing is triggered
        try:
            # Parse JSON
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1:
                try:
                    data = json.loads(response[start:end+1])
                except json.JSONDecodeError as jde:
                    print(f"[NeuralCortex] Failed to parse JSON response: {jde}")
                    return
                
                monologue = data.get("internal_monologue", "")
                speech = data.get("proactive_speech")
                action = data.get("background_action")
                action_plan = data.get("action_plan")
                
                self.last_thought = monologue"""
                
    content = content.replace(old_think_try, new_think_try)
    
    # Replace self-healing target file from hardcoded path to os.path.abspath(__file__)
    old_self_heal = """dev.assign_task(fix_task, ["d:\\\\Balamurugan\\\\Love\\\\love\\\\core\\\\jarvis_protocol.py"])"""
    new_self_heal = """dev.assign_task(fix_task, [os.path.abspath(__file__)])"""
    content = content.replace(old_self_heal, new_self_heal)
    
    jarvis_py.write_text(content, encoding="utf-8")
    print("core/jarvis_protocol.py patched successfully.")

def patch_evolution():
    print("Patching core/evolution_engine.py...")
    content = evolution_py.read_text(encoding="utf-8")
    
    # Safe float conversion in generate_hypotheses
    old_hyp = """                h = Hypothesis(
                    claim=item.get("claim",""), rationale=item.get("rationale",""),
                    predicted_effect=item.get("predicted_effect",""),
                    target_metric=item.get("target_metric","response_quality"),
                    predicted_delta=float(item.get("predicted_delta", 0.05)),
                    confidence=min(1.0, max(0.0, float(item.get("confidence", 0.5)))),
                )"""
                
    new_hyp = """                try:
                    p_delta = float(item.get("predicted_delta", 0.05))
                except (ValueError, TypeError):
                    p_delta = 0.05
                try:
                    conf = min(1.0, max(0.0, float(item.get("confidence", 0.5))))
                except (ValueError, TypeError):
                    conf = 0.5
                h = Hypothesis(
                    claim=item.get("claim",""), rationale=item.get("rationale",""),
                    predicted_effect=item.get("predicted_effect",""),
                    target_metric=item.get("target_metric","response_quality"),
                    predicted_delta=p_delta,
                    confidence=conf,
                )"""
                
    content = content.replace(old_hyp, new_hyp)
    
    # Safe float conversion in identify_gaps
    old_gap = """            for item in (json.loads(raw[s:e]) if s >= 0 and e > s else [])[:3]:
                sev = min(1.0, max(0.0, float(item.get("severity", 0.5))))
                gap = CapabilityGap(area=item.get("area","unknown"), description=item.get("description",""),"""
                
    new_gap = """            for item in (json.loads(raw[s:e]) if s >= 0 and e > s else [])[:3]:
                try:
                    sev = min(1.0, max(0.0, float(item.get("severity", 0.5))))
                except (ValueError, TypeError):
                    sev = 0.5
                gap = CapabilityGap(area=item.get("area","unknown"), description=item.get("description",""),"""
                
    content = content.replace(old_gap, new_gap)
    
    evolution_py.write_text(content, encoding="utf-8")
    print("core/evolution_engine.py patched successfully.")

if __name__ == "__main__":
    patch_agent()
    patch_jarvis()
    patch_evolution()
