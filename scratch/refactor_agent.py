import os
import re
from core.execution_guard import log_error

agent_path = r'c:\Users\balab\OneDrive\Documents\Projects\LLove\love\core\agent.py'
context_path = r'c:\Users\balab\OneDrive\Documents\Projects\LLove\love\core\context_engine.py'

with open(agent_path, 'r', encoding='utf-8') as f:
    agent_code = f.read()

# Extract the block starting from `memory_context = recall_memory` to just before `prompt = f"""{system}`
start_marker = "    memory_context = recall_memory(user_input, mode=mode)"
end_marker = "    prompt = f\"\"\"{system}{crash_note}{device_context}"

start_idx = agent_code.find(start_marker)
end_idx = agent_code.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers in agent.py")
    exit(1)

extracted_block = agent_code[start_idx:end_idx]

# Replace the block in agent.py
new_agent_block = """    # Fetch unified context from context_engine
    try:
        from core.context_engine import get_unified_prompt_context
        unified_context = get_unified_prompt_context(
            user_input=user_input,
            mode=mode,
            injected_context=extra_context
        )
    except Exception as e:
        print(f"[Agent] Failed to get unified context: {e}")
        unified_context = ""
    
    system = SYSTEM_PROMPT.replace("{{memory}}", "First few messages. Still learning.")
    
    prompt = f\"\"\"{system}{crash_note}{device_context}

{unified_context}

FINAL INSTRUCTIONS — FOLLOW THESE EXACTLY:
1. Use the data in "WHAT I CURRENTLY KNOW" — name specific people, subjects, times
2. Flowing paragraphs only. No bullet points. No numbered lists. No markdown bold.
3. 2-4 sentences max unless depth is genuinely needed.
4. Be direct. No "Here's a breakdown" intros. No "Let me know if you need more" closings.
5. You are {LOVE_NAME}, {USER_NAME}'s companion. Talk like you're sitting next to them.

{USER_NAME}: {user_input}
{LOVE_NAME}:\"\"\"
"""

# Find the end of the prompt assignment in agent.py
prompt_end_marker = "{LOVE_NAME}:\"\"\""
prompt_end_idx = agent_code.find(prompt_end_marker, end_idx) + len(prompt_end_marker)

new_agent_code = agent_code[:start_idx] + new_agent_block + agent_code[prompt_end_idx:]

with open(agent_path, 'w', encoding='utf-8') as f:
    f.write(new_agent_code)

# Add get_unified_prompt_context to context_engine.py
with open(context_path, 'r', encoding='utf-8') as f:
    context_code = f.read()

context_function = """

def get_unified_prompt_context(user_input: str, mode: str = "general", injected_context: str = "") -> str:
    \"\"\"Gather context from all subsystems intelligently, with consolidation to avoid truncation.\"\"\"
    blocks = []
    
    # 1. Live Jarvis context
    live_context = get_prompt_context()
    if injected_context:
        live_context = f"{injected_context}\\n\\n{live_context}".strip()
    if live_context:
        blocks.append(f"=== WHAT I CURRENTLY KNOW ===\\n{live_context}")

    # 2. Long-term memory
    try:
        from core.long_term_memory import remember, format_memory_for_chat
        ltm_result = remember(user_input, limit=3)
        ltm_text = format_memory_for_chat(ltm_result)
        if ltm_text:
            blocks.append(ltm_text)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")

    # 3. User profile
    try:
        from agents.file_explorer import enrich_prompt_context
        profile_ctx = enrich_prompt_context()
        if profile_ctx:
            blocks.append(f"=== WHAT I KNOW ABOUT KARTHI ===\\n{profile_ctx}")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")

    # 4. AGI-Level Systems
    try:
        agi_context_parts = []
        from core.psychological_model import get_psychological_model
        pm = get_psychological_model()
        if pm:
            profile = pm.get_profile_summary()
            import json
            agi_context_parts.append(f"Psychological Profile: {json.dumps(profile, indent=2)[:200]}...")
        if agi_context_parts:
            blocks.append("=== AGI-LEVEL INSIGHTS ===\\n" + "\\n".join(agi_context_parts))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")

    # 5. Web Search
    try:
        from core.internet import auto_search_for_query
        web_results = auto_search_for_query(user_input)
        if web_results:
            blocks.append(f"REAL-TIME WEB DATA:\\n{web_results}")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")

    # 6. Temporal Memory
    try:
        from core.temporal_memory import get_temporal_memory
        tmem = get_temporal_memory()
        temporal_ctx = tmem.get_temporal_context(query=user_input, limit=3)
        if temporal_ctx:
            blocks.append(f"=== MY AUTOBIOGRAPHICAL MEMORY ===\\n{temporal_ctx}")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")
        
    # 7. Intelligence Hub
    try:
        from core.intelligence_hub import get_intelligence_hub
        hub = get_intelligence_hub()
        intel_ctx = hub.get_context_for_prompt()
        if intel_ctx:
            blocks.append("=== LIVE INTELLIGENCE ===\\n" + intel_ctx)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")
        
    # 8. Agent Registry
    try:
        from core.agent_registry import get_agent_registry
        registry = get_agent_registry()
        agent_ctx = registry.get_all_context(user_input)
        if agent_ctx:
            blocks.append("=== LIVE LIFE CONTEXT ===\\n" + agent_ctx)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")
        
    # 9. Active Goals
    try:
        from core.autonomous_goal_engine import get_goal_status
        goal_status = get_goal_status()
        active_goals = goal_status.get("goals", [])
        if active_goals:
            goal_lines = [f"  • {g['title']} [{g['priority']}] {g['progress']:.0f}% done" for g in active_goals[:3]]
            blocks.append("=== ACTIVE GOALS ===\\n" + "\\n".join(goal_lines))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="scratch.refactor_agent")
        
    # Join and enforce a hard limit to avoid prompt truncation upstream
    unified = "\\n\\n".join(blocks)
    if len(unified) > 8000:
        return unified[:8000] + "\\n...[context truncated]"
    return unified
"""

with open(context_path, 'a', encoding='utf-8') as f:
    f.write(context_function)

print("Refactor complete.")
