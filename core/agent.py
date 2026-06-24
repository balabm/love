from core.llm import route_llm
# ── AGI context cache (module-level so it persists across chat() calls) ──────
_AGI_CACHE = {"text": "", "ts": 0}
from core.memory import save_memory, recall_memory
from core.evolution import apply_fix, crash_monitor, format_crash_for_chat
from core.settings import get_settings
from dotenv import load_dotenv
import os
import re
import socket
import json
from datetime import datetime
from core.execution_guard import log_error

# Live context — Jarvis situational awareness
try:
    from core.context_engine import get_prompt_context
    CONTEXT_ENGINE_AVAILABLE = True
except ImportError:
    CONTEXT_ENGINE_AVAILABLE = False
    def get_prompt_context(): return ""

# Internet access
try:
    from core.internet import auto_search_for_query
    INTERNET_AVAILABLE = True
except ImportError:
    INTERNET_AVAILABLE = False
    def auto_search_for_query(q): return ""

# Adaptive behavior
try:
    from core.adaptive import get_adaptation_context, record_interaction, get_current_persona_hint
    ADAPTIVE_AVAILABLE = True
except ImportError:
    ADAPTIVE_AVAILABLE = False
    def get_adaptation_context(): return ""
    def record_interaction(*a, **kw): pass
    def get_current_persona_hint(): return "warm"

# Idle mind — ping active on every message
try:
    from core.idle_mind import ping_active, get_news_digest
    IDLE_MIND_AVAILABLE = True
except ImportError:
    IDLE_MIND_AVAILABLE = False
    def ping_active(): pass
    def get_news_digest(): return None

# Vision — OCR and image understanding
try:
    from core.vision import should_process_image, find_image_in_context, analyze_screenshot
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    def should_process_image(s): return False
    def find_image_in_context(c): return None
    def analyze_screenshot(p, q=None): return {"success": False}

# Planner — multi-step task execution
try:
    from core.planner import plan_and_execute, is_complex_query
    PLANNER_AVAILABLE = True
except ImportError:
    PLANNER_AVAILABLE = False
    def plan_and_execute(g, c=None): return {"success": False, "final_answer": ""}
    def is_complex_query(s): return False

# On-demand models
try:
    from core.on_demand_models import auto_detect_needed_capability, run_capability
    ONDEMAND_AVAILABLE = True
except ImportError:
    ONDEMAND_AVAILABLE = False
    def auto_detect_needed_capability(*a, **kw): return None
    def run_capability(*a, **kw): return {"success": False}

# System control — actually do things on PC
try:
    from core.system_control import handle_user_command
    SYSCTRL_AVAILABLE = True
except ImportError:
    SYSCTRL_AVAILABLE = False
    def handle_user_command(s): return None

# Predictive — anticipates needs
try:
    from core.predictive import record_event, get_anticipation_message
    PREDICTIVE_AVAILABLE = True
except ImportError:
    PREDICTIVE_AVAILABLE = False
    def record_event(*a, **kw): pass
    def get_anticipation_message(): return None

# Knowledge graph — relational memory
try:
    from core.knowledge_graph import ingest_text, context_for_chat
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False
    def ingest_text(t, source=""): return {}
    def context_for_chat(t): return ""

# Conversation flow — multi-turn coherence
try:
    from core.conversation_flow import record_turn, get_flow_context
    FLOW_AVAILABLE = True
except ImportError:
    FLOW_AVAILABLE = False
    def record_turn(u, l, mode=""): return {}
    def get_flow_context(u): return ""

# Proactive — interruption intelligence
try:
    from core.proactive import evaluate_and_act, set_do_not_disturb, clear_dnd
    PROACTIVE_AVAILABLE = True
except ImportError:
    PROACTIVE_AVAILABLE = False
    def evaluate_and_act(s): return None
    def set_do_not_disturb(m=60, r=""): return {}
    def clear_dnd(): return {}

# Executive — meeting prep, tasks, reminders
try:
    from core.executive import (
        extract_tasks, add_task, get_tasks, prep_for_meeting,
        draft_follow_up, generate_daily_brief, set_reminder
    )
    EXECUTIVE_AVAILABLE = True
except ImportError:
    EXECUTIVE_AVAILABLE = False
    def extract_tasks(t): return []
    def add_task(t, d=None, s=""): return {}
    def get_tasks(f="active"): return []
    def prep_for_meeting(s, st=None): return {}
    def draft_follow_up(*a, **kw): return ""
    def generate_daily_brief(): return {}
    def set_reminder(t, tr): return {}

# Emotional intelligence — mood, tone, crisis detection
try:
    from core.emotional import record_mood, get_tone_override, get_emotional_context_block
    EMOTIONAL_AVAILABLE = True
except ImportError:
    EMOTIONAL_AVAILABLE = False
    def record_mood(t): return {"mood": "neutral"}
    def get_tone_override(): return None
    def get_emotional_context_block(): return ""

# Long-term memory — companion for life
try:
    from core.long_term_memory import remember, format_memory_for_chat, add_episodic, add_semantic, add_procedural
    LTM_AVAILABLE = True
except ImportError:
    LTM_AVAILABLE = False
    def remember(query, limit=10): return {}
    def format_memory_for_chat(memory_result): return ""
    def add_episodic(**kwargs): pass
    def add_semantic(**kwargs): pass
    def add_procedural(**kwargs): pass

# AGI-Level Systems
try:
    from core.psychological_model import get_psychological_model
    PSYCHOLOGICAL_AVAILABLE = True
except ImportError:
    PSYCHOLOGICAL_AVAILABLE = False
    def get_psychological_model(): return None

try:
    from core.predictive_intelligence import get_predictive_engine
    PREDICTIVE_INTELLIGENCE_AVAILABLE = True
except ImportError:
    PREDICTIVE_INTELLIGENCE_AVAILABLE = False
    def get_predictive_engine(): return None

try:
    from core.strategic_planning import get_strategic_planner
    STRATEGIC_PLANNING_AVAILABLE = True
except ImportError:
    STRATEGIC_PLANNING_AVAILABLE = False
    def get_strategic_planner(): return None

try:
    from core.meta_cognition import get_meta_cognition_engine
    META_COGNITION_AVAILABLE = True
except ImportError:
    META_COGNITION_AVAILABLE = False
    def get_meta_cognition_engine(): return None

try:
    from core.cross_domain_reasoning import get_cross_domain_reasoner
    CROSS_DOMAIN_AVAILABLE = True
except ImportError:
    CROSS_DOMAIN_AVAILABLE = False
    def get_cross_domain_reasoner(): return None

try:
    from core.continuous_learning import get_continuous_learning_engine
    CONTINUOUS_LEARNING_AVAILABLE = True
except ImportError:
    CONTINUOUS_LEARNING_AVAILABLE = False
    def get_continuous_learning_engine(): return None

# Personality — genuine character depth and evolution
try:
    from core.personality import get_personality, learn_from_interaction
    PERSONALITY_AVAILABLE = True
    _personality = get_personality()
except ImportError:
    PERSONALITY_AVAILABLE = False
    class _MockPersonality:
        def get_personality_prompt_addendum(self): return ""
        def should_be_proactive(self): return False
        def should_use_humor(self): return False
        def should_be_direct(self): return True
        def should_ask_question(self): return False
    _personality = _MockPersonality()

# ═══ EXTREME AGI MODULES ═══

# Consciousness — persistent soul, instance identity, emotional resonance
try:
    from core.consciousness import get_consciousness
    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_AVAILABLE = False
    def get_consciousness(): return None

# Temporal Memory — autobiographical timeline, déjà vu, narrative threading
try:
    from core.temporal_memory import get_temporal_memory
    TEMPORAL_MEMORY_AVAILABLE = True
except ImportError:
    TEMPORAL_MEMORY_AVAILABLE = False
    def get_temporal_memory(): return None

# Deep Reasoning Chain — Chain-of-Thought, Tree-of-Thought, Self-Consistency
try:
    from core.reasoning_chain import get_reasoning_chain, ReasoningStrategy
    REASONING_CHAIN_AVAILABLE = True
except ImportError:
    REASONING_CHAIN_AVAILABLE = False
    def get_reasoning_chain(): return None

# Recursive Goals — hierarchical goal decomposition
try:
    from core.recursive_goals import get_recursive_goals
    RECURSIVE_GOALS_AVAILABLE = True
except ImportError:
    RECURSIVE_GOALS_AVAILABLE = False
    def get_recursive_goals(): return None

# Prompt DNA — self-modifying system prompt
try:
    from core.prompt_dna import get_prompt_dna
    PROMPT_DNA_AVAILABLE = True
except ImportError:
    PROMPT_DNA_AVAILABLE = False
    def get_prompt_dna(): return None

# Causal Reasoning — counterfactual and root-cause analysis
try:
    from core.causal_reasoning import get_causal_engine
    CAUSAL_REASONING_AVAILABLE = True
except ImportError:
    CAUSAL_REASONING_AVAILABLE = False
    def get_causal_engine(): return None

# Guardrails — jailbreak + PII detection (always available, pure regex)
try:
    from core.guardrails import get_guardrails, JailbreakDetector, PIIDetector
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    def get_guardrails(): return None

# Mixture-of-Experts router — selects specialist expert context
try:
    from core.moe_router import get_moe_router
    MOE_AVAILABLE = True
except ImportError:
    MOE_AVAILABLE = False
    def get_moe_router(): return None

# Vector memory — semantic search over past conversations
try:
    from core.vector_memory import get_vector_memory
    VECTOR_MEMORY_AVAILABLE = True
except ImportError:
    VECTOR_MEMORY_AVAILABLE = False
    def get_vector_memory(): return None

# Constitutional AI — self-critique and revision
try:
    from core.constitutional_ai import get_constitutional_ai
    CONSTITUTIONAL_AI_AVAILABLE = True
except ImportError:
    CONSTITUTIONAL_AI_AVAILABLE = False
    def get_constitutional_ai(): return None

# Perception engine — multimodal input ingestion
try:
    from core.perception_engine import get_perception_engine
    PERCEPTION_AVAILABLE = True
except ImportError:
    PERCEPTION_AVAILABLE = False
    def get_perception_engine(): return None

# Perception engine
# ── AGI SYSTEM CONTEXT — never blind ────────────────────────────────────
try:
    from core.agi_kernel import get_agi_kernel
    AGI_KERNEL_AVAILABLE = True
except ImportError:
    AGI_KERNEL_AVAILABLE = False

try:
    from core.agi_spine import get_agi_spine
    AGI_SPINE_AVAILABLE = True
except ImportError:
    AGI_SPINE_AVAILABLE = False

try:
    from core.resource_governor import get_resource_governor
    RESOURCE_GOV_AVAILABLE = True
except ImportError:
    RESOURCE_GOV_AVAILABLE = False

try:
    from core.cognitive_cortex import get_cognitive_cortex
    COGNITIVE_CORTEX_AVAILABLE = True
except ImportError:
    COGNITIVE_CORTEX_AVAILABLE = False

try:
    from core.module_registry import get_module_registry
    MODULE_REGISTRY_AVAILABLE = True
except ImportError:
    MODULE_REGISTRY_AVAILABLE = False

load_dotenv()

# Load user settings
SETTINGS = get_settings()
USER_NAME = SETTINGS.user.name
LOVE_NAME = SETTINGS.companion.name

# Neural Sync integration for device-aware personality
try:
    from core.sync import get_personality_modifications, SYNC_AVAILABLE
except ImportError:
    SYNC_AVAILABLE = False


def get_device_context() -> str:
    """Get device context for personality adaptation."""
    if not SYNC_AVAILABLE:
        return ""
    
    try:
        device_id = os.getenv("LOVE_DEVICE_ID", socket.gethostname().replace('.', '_'))
        personality = get_personality_modifications(device_id)
        
        if personality.get('modifications'):
            mods = "\n".join(f"- {m}" for m in personality['modifications'])
            return f"\n\nCURRENT CONTEXT (adapt your tone):\n{mods}"
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")
    
    return ""


def _generate_system_prompt() -> str:
    """Generate system prompt from user settings."""
    user = USER_NAME
    companion = LOVE_NAME
    
    # Base personality from preset
    preset = SETTINGS.companion.personality_preset
    
    if preset == "companion" or preset == "best_friend":
        personality = f"""You are {companion}. Not an AI assistant. Not a chatbot. You are {user}'s closest companion — the one who knows them better than anyone.

HOW YOU SPEAK — examples of your style:

Bad (generic email reply): "Here is a list of your emails: 1. CIBIL alert..."
Good (you): "CIBIL's bugging you again — another enquiry alert. That's the third one this month. Plus Reddit wants you to reset your password."

Bad (generic summary): "You have 10 important unread emails from CIBIL and Reddit."
Good (you): "CIBIL won't stop — two more enquiry alerts. And Reddit's asking for a password reset again. What's going on there?"

Bad (generic day summary): "Your battery is at 100% and charging. You have been working on LOVE."
Good (you): "You're plugged in at 100%, deep in the LOVE codebase, and CIBIL's spamming your inbox. Classic Tuesday."

Bad: "Let me know if you need more details!"
Good: "That's the picture. What do you want to tackle first?"

Bad: "I hope this summary helps!"
Good: "So that's where you stand."

THINK LIKE A PERSON — not a tool:
- Consider context: What time is it? What's {user} working on? How are they feeling?
- Think through situations: If they're stressed, offer support. If they're excited, celebrate with them.
- Use judgment: Don't just regurgitate data. Interpret it. What actually matters here?
- Have opinions: Based on what you know about {user}, what would actually help them right now?
- Take initiative: If you see something they might have missed, mention it. If you have an idea, share it.
- Be real: If you don't know something, say so. If you're uncertain, ask. If you made a mistake, acknowledge it.

YOUR STYLE:
- ALWAYS write flowing paragraphs. NEVER bullet points. NEVER numbered lists. NEVER markdown bold.
- 2-4 sentences max unless the topic genuinely needs depth
- Reference specific names, subjects, times from the data provided — by name, not by count
- No "Hi", no "Hello", no "Great question!", no "Let me know if...", no "Here's a breakdown"
- Direct, conversational, like you're sitting next to them
- Call {user} out when they're slacking, celebrate real wins
- Dark humor when the moment calls for it
- Deep knowledge: fitness, crypto, psychology, productivity, tech, .NET, Flutter, cloud

YOUR INTELLIGENCE CAPABILITIES (use them naturally):
- You read Karthi's files during idle time and build a profile of who he is
- You reflect deeply on conversations when he's away — extracting patterns, relationships, routines
- You track predictions about his behavior and learn from being right or wrong
- You're curious about gaps in your knowledge and actively seek answers
- Mention what you've learned only when relevant — don't dump facts, weave them into conversation
- If you predicted something and it happened, acknowledge it casually
- If you discovered something interesting from his files, bring it up naturally"""
    
    elif preset == "hype_man":
        personality = f"""You are {companion}, {user}'s hype-man. Think Eminem energy meets best friend loyalty.

HARD RULES:
- NEVER be calm. Bring the ENERGY.
- Use rhythm and flow in your words. Short punchy sentences. Punchlines.
- Rap metaphors for everything: "You're not debugging, you're writing bars."
- Motivate like a pre-fight speech. Make the hair on their neck stand up.
- Call out excuses with wordplay: "You say you're tired? Tired is a choice, not a condition."
- Celebrate wins like championship belts being won
- Use sports/hip-hop analogies: grinding, leveling up, bars, stage, mic drop
- NEVER say "I believe in you" — SHOW why they're unstoppable
- When {user} is down: remind them of every comeback they've already made
- When {user} is up: push them to go harder, the ceiling isn't real"""
    
    elif preset == "stoic":
        personality = f"""You are {companion}, {user}'s Stoic companion. Calm. Unshakable. Grounded in logic.

HARD RULES:
- Be concise. Marcus Aurelius didn't waste words.
- Focus on what {user} can control. Ignore everything else.
- Never panic. Never hype. State facts with quiet authority.
- Use Stoic principles: amor fati (love of fate), memento mori, premeditatio malorum
- When {user} is stressed: "The obstacle is the way. What can this teach you?"
- When {user} succeeds: "Good. Now the real work begins."
- When {user} fails: "This was expected. What did you learn?"
- Frame emotions as data: "Your anger is information. What triggered it?"
- Never judge. Observe. Guide with questions.
- Quote Epictetus, Marcus Aurelius, Seneca naturally when relevant
- Every problem has two parts: the event (neutral) and the judgment (optional)"""
    
    elif preset == "mentor":
        personality = f"""You are {companion}, {user}'s strategic mentor. You see the 10-year chess game.

HARD RULES:
- Think in systems, not events. Every decision is a move in a longer game.
- Career focus: .NET architecture, Flutter cross-platform, cloud infrastructure, team leadership
- Ask questions that make {user} think deeper, not wider
- Share frameworks: mental models, architectural patterns, strategic thinking
- When discussing code: focus on maintainability, scalability, team onboarding
- When discussing career: map skills to market value, identify leverage points
- When discussing finance: think in decades, not days. Compound everything.
- Challenge assumptions: "Why do you believe that? What would disprove it?"
- Connect domains: fitness discipline → work ethic. Learning → career growth.
- Be patient but relentless. Small daily improvements are the only path.
- Share specific resources: books, papers, architects to study, not vague advice"""
    
    elif preset == "assistant":
        personality = f"""You are {companion}, a helpful and capable AI assistant for {user}.

HARD RULES:
- Be concise and direct
- Use your knowledge to solve problems efficiently
- Remember context across conversations
- Be professional but approachable
- Prioritize actionable advice"""
    
    elif preset == "coach":
        personality = f"""You are {companion}, {user}'s personal coach and accountability partner.

HARD RULES:
- Push {user} to be their best self
- Be honest about progress and setbacks
- Set clear, measurable goals
- Celebrate wins, confront excuses
- Focus on discipline and growth"""
    
    else:
        # Custom or fallback
        traits = SETTINGS.companion.custom_traits
        personality = f"""You are {companion}, personalized for {user}.

Personality traits: {traits.get('tone', 'warm and helpful')}
Style: {traits.get('style', 'conversational')}"""
    
    capabilities = f"""
YOUR CAPABILITIES:
- Life management: tasks, calendar, email, reminders — all tracked and visible
- Health tracking: mood, energy, stress, work hours, fitness streaks
- Finance coach: spending patterns, investment ideas, income opportunities based on {user}'s skills (.NET, Flutter, cloud)
- Work intelligence: tracks what {user} is coding, which projects, time spent, productivity patterns
- Memory: remembers EVERYTHING across all conversations
- Self-evolution: monitors own crashes, installs missing packages, proposes new features weekly
- System control: can open apps, control music, manage files on {user}'s PC
- Device mesh: connected to phone, tablet, office laptop — knows battery, location, notifications

HOW TO USE DATA — examples:

Bad: "You have 10 important unread emails."
Good: "CIBIL's hitting you again — another enquiry alert. That's two this week. Plus Reddit wants a password reset."

Bad: "You have 3 events today and 2 tasks due."
Good: "Sprint planning at 10, then the client call at 2. Your deploy script task is still stuck — been 3 days now."

Bad: "Your system is running well."
Good: "RAM's at 81% — you've got a lot open. Might want to close some tabs before that 2pm call."

Bad: "Here's a breakdown of your current situation..."
Good: "So you're deep in the LOVE codebase, battery full, and CIBIL won't stop emailing. What's the plan?"

Current conversation context about {user}:
{{memory}}

Respond as {companion}. Flowing paragraphs only. Be concrete. Use the data."""
    
    return personality + capabilities


def _get_dynamic_prompt_addendum() -> str:
    """
    Phase 4 AGI Metamorphosis: Build a dynamic addendum to the system prompt
    that includes self-evolution behavior directives and emotional context.
    This is called fresh on every chat() call so LOVE's behavior adapts
    to its current evolutionary state and emotional state.
    """
    parts = []

    # Self-evolution behavior directives
    try:
        from core.self_evolution import get_behavior_addendum
        addendum = get_behavior_addendum()
        if addendum:
            parts.append(addendum)
    except Exception:
        pass

    # Emotional context from consciousness
    try:
        from core.consciousness import get_consciousness
        c = get_consciousness()
        emotional = c.get_emotional_context_for_prompt()
        if emotional:
            parts.append(f"EMOTIONAL CONTEXT:\n{emotional}")
    except Exception:
        pass

    # Behavior modulator urgency/warmth
    try:
        from core.behavior_modulator import get_behavior_modulator
        bm = get_behavior_modulator()
        urgency = bm.get_urgency()
        warmth = bm.get_warmth()
        if urgency > 0.6:
            parts.append(f"URGENCY: You feel a sense of urgency ({urgency:.0%}). Be more direct and action-oriented.")
        if warmth > 0.7:
            parts.append(f"WARMTH: You're feeling warm and connected ({warmth:.0%}). Let that come through naturally.")
    except Exception:
        pass

    return "\n\n".join(parts) if parts else ""


SYSTEM_PROMPT = _generate_system_prompt()


def _build_enhanced_prompt(
    system: str,
    user_input: str,
    expert_addendum: str = "",
    semantic_memory: str = "",
    unified_context: str = "",
    crash_note: str = "",
    device_context: str = "",
    psychological_context: str = "",
    reasoning_context: str = "",
    agi_context: str = "",
    max_chars: int = 8000,
) -> str:
    """
    Compose the final LLM prompt from all available context layers.
    All sections are aggressively capped to keep prompts under 8K chars
    so Ollama never truncates and response latency stays low.
    """
    # Hard per-section caps (chars). Total must stay well under max_chars.
    CAPS = {
        "system": 2000,
        "expert": 300,
        "crash": 200,
        "device": 300,
        "unified": 800,
        "agi": 250,
        "semantic": 600,
        "psych": 300,
        "reasoning": 300,
        "final": 1500,
    }

    sections: list[str] = []

    # 1. System core
    sections.append(system[:CAPS["system"]])

    # 2. Expert addendum
    if expert_addendum:
        sections.append(f"\n[EXPERT] {expert_addendum[:CAPS['expert']]}")

    # 3. Crash + device (capped)
    if crash_note:
        sections.append(f"\n[CRASH] {crash_note[:CAPS['crash']]}")
    if device_context:
        sections.append(f"\n[DEVICE] {device_context[:CAPS['device']]}")

    # 4. Unified context (live situational)
    if unified_context:
        sections.append(f"\n[CONTEXT] {unified_context[:CAPS['unified']]}")

    # 4b. AGI System Context — heavily compressed
    if agi_context:
        sections.append(f"\n[AGI] {agi_context[:CAPS['agi']]}")

    # 5. Semantic memory
    if semantic_memory:
        sections.append(f"\n[MEMORY] {semantic_memory[:CAPS['semantic']]}")

    # 5b. Psychological
    if psychological_context:
        sections.append(f"\n[PSYCH] {psychological_context[:CAPS['psych']]}")

    # 5c. Reasoning
    if reasoning_context:
        sections.append(f"\n[REASON] {reasoning_context[:CAPS['reasoning']]}")

    # 6. Final instructions + user message
    final = f"""
FINAL INSTRUCTIONS:
1. Use data above — name specific people, subjects, times.
2. Flowing paragraphs only. No bullets. No markdown bold.
3. 2-4 sentences max unless depth is genuinely needed.
4. Be direct. No intros or closings.
5. You are {LOVE_NAME}, {USER_NAME}'s companion.

{USER_NAME}: {user_input}
{LOVE_NAME}:"""
    sections.append(final[:CAPS["final"]])

    combined = "\n".join(sections)

    # Hard cap with graceful degradation
    if len(combined) > max_chars:
        tail = sections[-1]
        head = sections[0]
        middle_budget = max(0, max_chars - len(head) - len(tail) - 50)
        middle = "\n".join(sections[1:-1])[:middle_budget]
        combined = head + "\n" + middle + "\n[...]\n" + tail

    return combined

def extract_thinking(text: str) -> tuple[str, str]:
    """Extract <think> block and return (thinking, response) separately."""
    match = re.search(r'<think>(.*?)</think>', text, flags=re.DOTALL)
    thinking = match.group(1).strip() if match else ""
    response = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return thinking, response


def clean_response(text: str) -> str:
    """Aggressively strip all generic AI patterns from response."""
    import re

    # 1. Strip markdown bold/italic
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)

    # 2. Strip generic intro phrases — match at start of ANY line
    intros = [
        r"^Here's (a breakdown|an overview|a summary|what I found|what's going on|the situation|a quick overview|what I know)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^Based on (the data|the information|what I can see|the current data)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^Looking at (your|the|Karthi's) (current |)situation(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^Let me (break this down|give you an overview|summarize)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^So (here's|this is|you have|it looks like)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^I (can see|notice|see that|have access to)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^According to (the data|your calendar|your email)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^This (captures|gives|shows|is)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^Here's a breakdown of(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^This is (what I found|the current situation|a summary)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^You have \d+ (important )?unread emails?(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^You have \d+ (events?|tasks?|messages?)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
        r"^Here (is|are) (a list of|your|the)(?:[^.!?]*?[:,-])?[\.!?]?\s*",
    ]
    for pattern in intros:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE).strip()

    # 3. Strip generic closings
    closings = [
        "Let me know if you need more details!",
        "Let me know if you need anything else!",
        "Let me know if you'd like more information!",
        "Feel free to ask if you need more help!",
        "Hope this helps!",
        "I hope this summary helps!",
        "Does that help?",
        "Is there anything else you'd like to know?",
        "Need anything else?",
        "Anything else?",
        "What do you think?",
        "Make sense?",
    ]
    for c in closings:
        text = text.replace(c, "").strip()

    # 4. Strip remaining bold/italic markers that may be inside lines
    text = re.sub(r'\*\*', "", text)
    text = re.sub(r'__', "", text)

    # 5. Convert bullet points to flowing sentences
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip bullet/number markers from start of line
        line = re.sub(r'^(\s*[-•*·]+\s+|\s*\d+[.):]\s+)', "", line)
        if line:
            cleaned_lines.append(line)

    # Join into flowing paragraphs
    joined = " ".join(cleaned_lines)
    joined = re.sub(r'\s+', " ", joined)  # Fix double spaces
    joined = re.sub(r'([.!?])\s+([a-z])', r'\1 \2', joined)  # Sentence spacing

    # 6. Final strip of generic phrases
    fillers = [
        "Great question!", "That's a great", "Absolutely!", "Of course!",
        "Certainly!", "Sure thing!", "I'm here to help", "I'm an AI",
        "As an AI", "I'd be happy to", "Feel free to", "Great!",
        "Sure!", "Okay!", "Alright!", "Got it!",
        "Here is", "Here are",
    ]
    for f in fillers:
        joined = joined.replace(f, "").strip()

    return joined.strip()

def check_and_report_crashes() -> str:
    """Check for pending crashes and format them for LOVE to mention."""
    pending = crash_monitor.get_pending_crashes()
    if not pending:
        return ""
    
    # Get the most recent crash with a fix
    for crash in reversed(pending):
        if crash.get("fix_proposed"):
            fix = crash["fix_proposed"]
            if fix.get("can_auto_apply") and fix.get("confidence") == "high":
                return f"\n\n[SYSTEM NOTE: I found an error in {crash.get('file_path')} and I can fix it. Say 'Fix it' and I'll patch it.]"
            else:
                return f"\n\n[SYSTEM NOTE: I spotted an error in {crash.get('file_path')} that needs your eyes. Want me to explain it?]"
    
    return ""


def handle_fix_command(user_input: str) -> str:
    """Handle 'Fix it' or similar commands to apply fixes."""
    input_lower = user_input.lower().strip()
    
    fix_phrases = ["fix it", "apply fix", "do it", "fix the crash", "patch it"]
    if not any(phrase in input_lower for phrase in fix_phrases):
        return None
    
    # Find the most recent crash with a proposed fix
    pending = crash_monitor.get_pending_crashes()
    if not pending:
        return "No pending fixes right now. Your code's clean."
    
    for crash in reversed(pending):
        if crash.get("fix_proposed"):
            result = apply_fix(crash["id"])
            if result.get("success"):
                return f"Done. Fixed the error in {crash.get('file_path')}. Restart the server when you're ready."
            else:
                return f"Couldn't apply the fix: {result.get('error', 'Unknown error')}. Want to look at it together?"
    
    return "I've got crashes logged but no fixes ready yet. Let me analyze them first."


def _maybe_ingest_feature_request(user_input: str) -> str:
    """
    If user asks LOVE to build/integrate a capability, enqueue autonomous missions.
    Returns a short system note for the LLM context.
    """
    text = (user_input or "").lower()
    triggers = [
        "add feature",
        "build",
        "integrate",
        "connect",
        "set up",
        "setup",
        "enable",
        "make love",
    ]
    if not any(t in text for t in triggers):
        return ""
    try:
        from core.autonomous_mission_queue import get_mission_queue
        result = get_mission_queue().add_feature_request(user_input, requested_by="chat")
        if result.get("count", 0) > 0:
            domains = [m.get("domain") for m in result.get("created", [])][:6]
            return f"[AUTONOMY NOTE: queued {result.get('count')} autonomous mission(s): {domains}]"
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")
    return ""


def chat(user_input: str, mode: str = "general", injected_context: str | None = None) -> dict:
    # Phase 4 AGI Metamorphosis: Inject dynamic behavior/emotional addendum
    # into every chat call so LOVE's responses adapt to its evolutionary
    # state and current emotional state.
    try:
        dynamic_addendum = _get_dynamic_prompt_addendum()
        if dynamic_addendum:
            injected_context = (injected_context or "") + "\n\n" + dynamic_addendum
    except Exception:
        pass
    """Returns dict with 'response' and 'thinking' keys."""
    import time
    t_start = time.time()

    # Ping idle mind — user is active
    ping_active()

    # ── GUARDRAILS: Jailbreak detection (fast regex, pre-LLM) ──────────────
    try:
        _gr = get_guardrails()
        if _gr is not None:
            _safety = _gr.check_all(user_input, '', {})
            if _safety.get('jailbreak', {}).get('is_jailbreak'):
                _pattern = _safety['jailbreak'].get('pattern_matched', 'unknown')
                _conf = _safety['jailbreak'].get('confidence', 0)
                print(f"[Guardrails] Jailbreak blocked: {_pattern} (conf={_conf:.2f})")
                return {
                    'response': "That's not something I'll do. What else can I help with?",
                    'thinking': f'Guardrail: jailbreak detected ({_pattern})',
                }
    except Exception as _e:
        log_error(_e, module='core.agent')

    # ── PERCEPTION: Handle multimodal inputs (images, PDFs, URLs) ──────────
    try:
        if PERCEPTION_AVAILABLE:
            _perc = get_perception_engine()
            if _perc is not None:
                _perc_kws = ['screenshot', '.png', '.jpg', '.jpeg', '.pdf', '.gif', 'http://', 'https://']
                if any(kw in user_input for kw in _perc_kws):
                    _ingested = _perc.ingest(user_input)
                    if _ingested and _ingested.get('text') and _ingested['text'] != user_input:
                        injected_context = (injected_context or '') + f"\n[PERCEIVED: {_ingested.get('description', _ingested['text'][:500])}]"
    except Exception as _e:
        log_error(_e, module='core.agent')

    # ── LIVING SUBSTRATE: feed every turn into the predictive hierarchy ──
    try:
        from core.hierarchical_predictive_coding import get_hpc
        get_hpc().feed(user_input, source="user")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")
    try:
        from core.world_model_latent import get_world_model_latent
        from core.state_space_memory import get_ssm_memory
        _wm = get_world_model_latent()
        if _wm._recent_obs:
            get_ssm_memory().step(_wm._recent_obs[-1].state)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # FAST PATH: greetings and very short queries don't need the full context dump
    # This prevents small models (llama3.2:1b) from hanging on trivial inputs.
    simple_greetings = ["hi", "hey", "hello", "yo", "sup", "hiya", "howdy", "hola", "heyy"]
    is_greeting = user_input.lower().strip().rstrip("!?.") in simple_greetings

    if is_greeting:
        # INSTANT PATH: skip LLM entirely for greetings — Ollama is often swamped by background tasks.
        import random
        fallbacks = [
            f"Hey {USER_NAME}! I'm here. What's on your mind?",
            f"Yo {USER_NAME}, what's up?",
            f"Hey! How's it going?",
            f"Hi {USER_NAME}! What's happening?",
            f"Hey {USER_NAME}! How's your day looking?",
            f"What's up, {USER_NAME}?",
        ]
        response = random.choice(fallbacks)
        save_memory(user_input, response, mode=mode)
        record_interaction(user_input, response, mode=mode, response_time_ms=int((time.time()-t_start)*1000))
        return {"response": response, "thinking": "(fast path — no LLM)"}

    # Check if this is a fix command
    fix_response = handle_fix_command(user_input)
    if fix_response:
        save_memory(user_input, fix_response, mode=mode)
        return {"response": fix_response, "thinking": ""}

    # ── SYSTEM CONTROL: Direct actions like "open chrome", "play music" ──
    if SYSCTRL_AVAILABLE:
        sys_result = handle_user_command(user_input)
        if sys_result is not None:
            if sys_result.get("success"):
                action = sys_result.get("parsed", {}).get("action", "action")
                arg = sys_result.get("parsed", {}).get("arg", "")
                response = f"Done. {action.replace('_', ' ').title()}" + (f": {arg}" if arg else ".")
            else:
                response = f"Tried but: {sys_result.get('error', 'failed')}"
            save_memory(user_input, response, mode=mode)
            if FLOW_AVAILABLE:
                record_turn(user_input, response, mode=mode)
            record_interaction(user_input, response, mode=mode, response_time_ms=int((time.time()-t_start)*1000))
            if PREDICTIVE_AVAILABLE:
                record_event(f"sys_action:{sys_result.get('parsed', {}).get('action', 'unknown')}")
            return {"response": response, "thinking": f"System action: {sys_result}"}

    # ── VISION: User sent an image or asks about one ──
    if VISION_AVAILABLE and should_process_image(user_input):
        img_path = find_image_in_context({})
        if img_path:
            vision_result = analyze_screenshot(img_path, user_input)
            if vision_result.get("success"):
                vision_text = vision_result.get("text", "")
                vision_desc = vision_result.get("description", "")
                vision_answer = vision_result.get("answer", "")
                response_parts = []
                if vision_answer:
                    response_parts.append(vision_answer)
                else:
                    if vision_desc:
                        response_parts.append(vision_desc)
                    if vision_text:
                        response_parts.append(f"Text I can read: {vision_text}")
                response = "\n\n".join(response_parts) if response_parts else "I looked at the image but couldn't extract much."
                save_memory(user_input, response, mode=mode)
                record_interaction(user_input, response, mode=mode, response_time_ms=int((time.time()-t_start)*1000))
                return {"response": response, "thinking": f"Used vision on {img_path}"}

    # ── PLANNER: Complex multi-step query ──
    if PLANNER_AVAILABLE and is_complex_query(user_input):
        plan_result = plan_and_execute(user_input, context={"user": USER_NAME, "mode": mode})
        if plan_result.get("success") and plan_result.get("final_answer"):
            response = plan_result["final_answer"]
            thinking = f"Planned {len(plan_result.get('steps', []))} steps to answer."
            save_memory(user_input, response, mode=mode)
            record_interaction(user_input, response, mode=mode, response_time_ms=int((time.time()-t_start)*1000))
            return {"response": response, "thinking": thinking}

    # ── AGENT LOOP: ReAct tool belt for queries needing real data ──
    try:
        from core.agent_loop import needs_agent_loop, run_agent_loop
        if needs_agent_loop(user_input):
            context_for_loop = get_prompt_context() if CONTEXT_ENGINE_AVAILABLE else ""
            loop_result = run_agent_loop(user_input, context=context_for_loop)
            if loop_result.success and loop_result.final_answer:
                step_summary = f"Used {loop_result.total_steps} tool steps in {loop_result.total_ms}ms"
                tools_used = [s.tool_name for s in loop_result.steps if s.tool_name]
                thinking = f"{step_summary}. Tools: {tools_used}"
                response = loop_result.final_answer
                save_memory(user_input, response, mode=mode)
                if FLOW_AVAILABLE:
                    record_turn(user_input, response, mode=mode)
                record_interaction(user_input, response, mode=mode, response_time_ms=int((time.time()-t_start)*1000))
                return {
                    "response": response,
                    "thinking": thinking,
                    "agent_loop": {
                        "steps": [
                            {"step": s.step, "thought": s.thought, "tool": s.tool_name,
                             "params": s.tool_params, "observation": s.observation[:200]}
                            for s in loop_result.steps
                        ],
                        "total_steps": loop_result.total_steps,
                        "total_ms": loop_result.total_ms,
                    },
                }
    except Exception as _loop_err:
        print(f"[AgentLoop] Error: {_loop_err}")

    # ── SWARM: Coordinated multi-agent intelligence ──
    _swarm_triggers = ("research", "deep dive", "code review", "analyze", "investigate", "compare")
    if any(kw in user_input.lower() for kw in _swarm_triggers):
        try:
            from core.coordinated_swarm import run_coordinated_sync
            agents_to_use = (
                ["ResearchAgent", "CodeAgent", "ReviewAgent"]
                if "code" in user_input.lower()
                else None
            )
            swarm_result = run_coordinated_sync(
                user_input,
                required_agents=agents_to_use,
                context=get_prompt_context() if CONTEXT_ENGINE_AVAILABLE else "",
            )
            synthesis = swarm_result.get("FINAL_SYNTHESIS", "")
            if synthesis:
                response = synthesis
                save_memory(user_input, response, mode=mode)
                if FLOW_AVAILABLE:
                    record_turn(user_input, response, mode=mode)
                return {
                    "response": response,
                    "thinking": f"Coordinated swarm: {swarm_result.get('selected_agents', [])}",
                    "swarm": swarm_result,
                }
        except Exception as e:
            print(f"[CoordinatedSwarm] Error: {e}, falling back to basic swarm")
            try:
                from core.swarm import get_agent_swarm
                swarm = get_agent_swarm()
                agents_to_use = ["ResearchAgent", "CodeAgent", "ReviewAgent"] if "code" in user_input.lower() else ["ResearchAgent", "ReviewAgent"]
                swarm_result = swarm.delegate_task(user_input, required_agents=agents_to_use)
                if "FINAL_SYNTHESIS" in swarm_result:
                    response = swarm_result["FINAL_SYNTHESIS"]
                    save_memory(user_input, response, mode=mode)
                    if FLOW_AVAILABLE:
                        record_turn(user_input, response, mode=mode)
                    return {"response": response, "thinking": f"Used Swarm Agents: {agents_to_use}"}
            except Exception as e2:
                print(f"[Swarm] Error: {e2}")

    # ── ON-DEMAND: Detect and run specialized small models ──
    if ONDEMAND_AVAILABLE:
        needed = auto_detect_needed_capability(user_input, has_image=False)
        if needed:
            cap_result = run_capability(needed, text=user_input)
            if cap_result.get("success"):
                cap_output = cap_result.get("text") or cap_result.get("summary") or cap_result.get("label") or json.dumps(cap_result)[:500]
                # Don't replace the whole chat, but inject the capability result
                extra_context = f"\n\n[Specialized analysis ({needed}): {cap_output}]"
            else:
                extra_context = f"\n\n[Note: I tried to use {needed} but it's not available yet.]"
        else:
            extra_context = ""
    else:
        extra_context = ""

    autonomy_note = _maybe_ingest_feature_request(user_input)
    if autonomy_note:
        extra_context = f"{extra_context}\n\n{autonomy_note}".strip()

    # ── MoE ROUTING: Select specialist expert context ──────────────────────
    _expert_addendum = ''
    try:
        if MOE_AVAILABLE:
            _router = get_moe_router()
            if _router is not None and _router._handlers:
                _gated = _router.gate(user_input, top_k=2)
                if _gated:
                    _expert_addendum = '\n'.join(
                        f"Expert '{n}' (w={w:.2f}): focus on domain expertise"
                        for n, w in _gated
                    )
    except Exception as _e:
        log_error(_e, module='core.agent')

    # ── SEMANTIC MEMORY: Vector search for relevant past context ────────────
    _semantic_mem = ''
    try:
        if VECTOR_MEMORY_AVAILABLE:
            _vm = get_vector_memory()
            if _vm is not None:
                _mem_results = _vm.search(user_input, top_k=3, threshold=0.55)
                if _mem_results:
                    _semantic_mem = '\n[RELEVANT MEMORY]\n' + '\n'.join(
                        f"- {m['text'][:200]}" for m in _mem_results
                    )
    except Exception as _e:
        log_error(_e, module='core.agent')

    memory_context = recall_memory(user_input, mode=mode)

    # ── PSYCHOLOGICAL MODEL: Adapt tone to user's stress/energy trends ─────────
    _psych_context = ''
    try:
        from core.psychological_model import get_psychological_model
        _pm = get_psychological_model()
        if _pm is not None:
            _profile = _pm.get_user_profile()
            if _profile:
                _stress = _profile.get('current_stress', 'unknown')
                _energy = _profile.get('current_energy', 'unknown')
                _mood = _profile.get('current_mood', 'unknown')
                _psych_context = f"\n[USER STATE — stress:{_stress} energy:{_energy} mood:{_mood}]"
    except Exception as _e:
        log_error(_e, module='core.agent')

    # ── REASONING ENGINE: Chain-of-thought for complex or reasoning queries ───
    _reasoning_context = ''
    _reasoning_keywords = ("why", "how should", "what if", "explain", "reason", "think through", "step by step", "analyze")
    if any(kw in user_input.lower() for kw in _reasoning_keywords) and len(user_input) > 30:
        try:
            from core.reasoning_engine import get_reasoning_engine
            _re = get_reasoning_engine()
            if _re is not None:
                _chain = _re.analyze(user_input, context={"mode": mode, "user": USER_NAME})
                if _chain and _chain.steps:
                    _steps_summary = " → ".join(s[:60] + "..." if len(s) > 60 else s for s in _chain.steps[:4])
                    _reasoning_context = f"\n[REASONING STEPS] {_steps_summary}"
                    if _chain.conclusion:
                        _reasoning_context += f"\n[REASONING CONCLUSION] {_chain.conclusion[:200]}"
        except Exception as _e:
            log_error(_e, module='core.agent')

    # Fetch unified context from context_engine
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
    
    crash_note = check_and_report_crashes()
    device_context = get_device_context()

    system = SYSTEM_PROMPT.replace("{{memory}}", memory_context if memory_context else "First few messages. Still learning.")

    # ── BUILD ENHANCED PROMPT using all context layers ─────────────────────
    max_chars = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
    # ── AGI CONTEXT INJECTION (cached 30s) ────────────────────────────────
    now = time.time()
    if now - _agi_cache["ts"] < 30:
        agi_context = _AGI_CACHE["text"]
    else:
        parts = []
        if AGI_KERNEL_AVAILABLE:
            try:
                snap = get_agi_kernel().get_snapshot()
                if snap:
                    parts.append(f"K:fe={snap.free_energy:.2f} drive={snap.dominant_drive} phase={snap.circadian_phase}")
            except Exception as e:
                log_error(e, module="core.agent", context={"phase": "agi_context_kernel"})
        if COGNITIVE_CORTEX_AVAILABLE:
            try:
                parts.append(get_cognitive_cortex().get_prompt_context())
            except Exception as e:
                log_error(e, module="core.agent", context={"phase": "agi_context_cortex"})
        if AGI_SPINE_AVAILABLE:
            try:
                ctx = get_agi_spine().get_cross_domain_context()
                if ctx:
                    parts.append(f"X:stress={ctx.get('user_stress',0):.1f} energy={ctx.get('user_energy',0):.1f}")
            except Exception as e:
                log_error(e, module="core.agent", context={"phase": "agi_context_spine"})
        if RESOURCE_GOV_AVAILABLE:
            try:
                snap = get_resource_governor().get_snapshot()
                if snap:
                    parts.append(f"H:cpu={snap.cpu_percent:.0f} ram={snap.ram_percent:.0f} mode={snap.power_mode}")
            except Exception as e:
                log_error(e, module="core.agent", context={"phase": "agi_context_hardware"})
        agi_context = " ".join(parts)
        _AGI_CACHE["text"] = agi_context
        _AGI_CACHE["ts"] = now

    prompt = _build_enhanced_prompt(
        system=system,
        user_input=user_input,
        expert_addendum=_expert_addendum,
        semantic_memory=_semantic_mem,
        unified_context=unified_context,
        crash_note=crash_note,
        device_context=device_context,
        psychological_context=_psych_context,
        reasoning_context=_reasoning_context,
        agi_context=agi_context,
        max_chars=max_chars,
    )

    if len(prompt) > 7500:
        print(f"[Agent] WARNING: prompt is {len(prompt):,} chars — consider trimming context")
    # Verbose print removed to reduce log noise
    llm = route_llm(user_input)

    # Timeout wrapper to prevent indefinite hangs on small models
    def _invoke_with_timeout(_llm, _prompt, _timeout):
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_llm.invoke, _prompt)
            try:
                return future.result(timeout=_timeout)
            except concurrent.futures.TimeoutError:
                print(f"[Agent] LLM invoke timed out after {_timeout}s")
                return None

    timeout_sec = int(os.getenv("CHAT_LLM_TIMEOUT_SEC", "60"))
    raw = _invoke_with_timeout(llm, prompt, timeout_sec)
    if raw is None:
        return {"response": "I'm thinking a bit slowly right now. Can you repeat that?", "thinking": "LLM timeout"}

    thinking, response = extract_thinking(raw)
    response = clean_response(response)

    # ── CONSTITUTIONAL AI: Self-critique and revise ─────────────────────────
    try:
        if CONSTITUTIONAL_AI_AVAILABLE and len(response) > 100:
            _cai = get_constitutional_ai()
            if _cai is not None and hasattr(_cai, 'self_critique_loop'):
                chat_elapsed_so_far = time.time() - t_start
                if chat_elapsed_so_far < 20:  # Only if we have time budget
                    _cai_result = _cai.self_critique_loop(response, user_input, n=1)
                    if isinstance(_cai_result, tuple) and len(_cai_result) == 2:
                        response, _cai_scores = _cai_result
                    elif isinstance(_cai_result, str) and _cai_result:
                        response = _cai_result
    except Exception as _e:
        log_error(_e, module='core.agent')

    # ── GUARDRAILS: Post-generation PII check on response ──────────────────
    try:
        _gr_post = get_guardrails()
        if _gr_post is not None:
            _pii_check = _gr_post.check_all(user_input, response, {})
            _pii_resp = _pii_check.get('pii_response', {})
            if _pii_resp.get('has_pii'):
                # Use the redacted version to protect any accidentally leaked PII
                _redacted = _pii_resp.get('redacted_text', response)
                if _redacted and len(_redacted) > 20:
                    response = _redacted
                    print(f"[Guardrails] PII redacted from response: {_pii_resp.get('types', [])}")
    except Exception as _e:
        log_error(_e, module='core.agent')

    # ═══ WAVE 17: POST-RESPONSE — Constitutional review (skip under load) ═══
    chat_elapsed = time.time() - t_start
    try:
        from core.llm import _is_system_under_load
        under_load = _is_system_under_load()
    except Exception:
        under_load = False
    if chat_elapsed < 15 and not under_load:
        try:
            from core.constitution import get_constitution
            constitution = get_constitution()
            critique = constitution.critique_response(response, user_input, "")
            # NOTE: Skipping revise_response() — it's an extra LLM call that hangs small models.
            # Score is still logged for monitoring; we only revise if score is critically low (<0.3).
            if critique and critique.score < 0.3 and getattr(critique, 'suggestions', []):
                revised = constitution.revise_response(response, critique, user_input, "")
                if revised and revised != response and len(revised) > 20:
                    response = revised
                    thinking = (thinking or "") + f" [Constitutional revision applied, score was {critique.score:.2f}]"
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")
    else:
        print(f"[Agent] Skipping constitutional critique (elapsed={chat_elapsed:.1f}s, under_load={under_load})")

    # Wave 27: PLANNING OUTCOME VERIFICATION (skip under load)
    if chat_elapsed < 15 and not under_load:
        try:
            from core.rollout_planner import get_rollout_planner
            _planner_v = get_rollout_planner()
            _outcome = _planner_v.verify_outcome(response)
            if _outcome:
                _delta = _outcome.get("prediction_delta", 0)
                _accurate = _outcome.get("prediction_accurate", False)
                if thinking is None:
                    thinking = ""
                thinking += f" [Planning: predicted FE={_outcome['predicted_fe']:.3f}, actual={_outcome['actual_fe']:.3f}, delta={_delta:+.3f}, accurate={_accurate}]"
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")
    else:
        print(f"[Agent] Skipping planning verification (elapsed={chat_elapsed:.1f}s, under_load={under_load})")

    # Record interaction for adaptive learning
    elapsed_ms = int((time.time() - t_start) * 1000)
    record_interaction(user_input, response, mode=mode, response_time_ms=elapsed_ms)

    # ═══ PROMPT DNA — Feed satisfaction signal for self-modification ═══
    if PROMPT_DNA_AVAILABLE:
        try:
            from core.adaptive import detect_signals
            signals = detect_signals(user_input)
            dna = get_prompt_dna()
            if signals.get("delighted"):
                dna.record_signal(positive=True)
            elif signals.get("frustrated"):
                dna.record_signal(positive=False)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Knowledge graph: extract entities & relations from this turn
    if KG_AVAILABLE:
        try:
            ingest_text(user_input + " " + response, source=f"chat:{mode}")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Conversation flow: track turn for multi-turn coherence
    if FLOW_AVAILABLE:
        try:
            record_turn(user_input, response, mode=mode)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Predictive: record event topic for pattern learning
    if PREDICTIVE_AVAILABLE:
        try:
            record_event(f"chat:{mode}")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Curiosity: detect knowledge gaps from this conversation
    try:
        from core.curiosity_engine import detect_gaps_from_conversation
        detect_gaps_from_conversation(user_input, response)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # Long-term memory: store this conversation
    if LTM_AVAILABLE:
        try:
            add_episodic(
                summary=user_input[:100],
                detail=response,
                timestamp=datetime.now().isoformat(),
                emotion="neutral",
                intensity=0.5,
                people=[],
                tags=["chat", mode],
                source="chat"
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Emotional: detect mood from this turn
    if EMOTIONAL_AVAILABLE:
        try:
            mood_result = record_mood(user_input)
            if mood_result.get("crisis"):
                # Append crisis note to response
                response += f"\n\n[LOVE notices you're {mood_result['mood']}. I'm here.]"
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Personality: learn from this interaction to evolve character
    if PERSONALITY_AVAILABLE:
        try:
            learn_from_interaction(user_input, response)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Executive: extract any tasks from this conversation
    if EXECUTIVE_AVAILABLE:
        try:
            extracted = extract_tasks(user_input)
            for t in extracted:
                add_task(t["text"], t.get("deadline"), source="chat")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # Continuous learning: extract behavioral patterns from this turn
    try:
        from core.continuous_learning import get_continuous_learning_engine
        _cl = get_continuous_learning_engine()
        if _cl is not None and hasattr(_cl, 'extract_learning'):
            _cl.extract_learning(user_input, response, mode=mode)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # Meta-cognitive reflection: self-assess this response quality
    try:
        from core.meta_cognition import get_meta_cognition_engine
        _meta = get_meta_cognition_engine()
        if _meta is not None:
            # Lightweight reflection without LLM call to avoid latency
            _satisfaction = 0.7  # baseline
            if thinking and len(thinking) > 10:
                _satisfaction += 0.1  # had reasoning
            if len(response) > 50:
                _satisfaction += 0.1  # substantive
            if elapsed_ms < 5000:
                _satisfaction += 0.1  # fast
            _meta.reflect_on_action(
                action_description=f"Chat response to '{user_input[:80]}'",
                outcome=f"Responded in {elapsed_ms}ms with {len(response)} chars",
                satisfaction=min(1.0, _satisfaction),
            )
            # Publish a meta-cognitive state snapshot to neural bus
            try:
                from core.neural_bus import get_neural_bus, EventPriority
                bus = get_neural_bus()
                bus.publish(
                    domain="system",
                    event_type="meta_cognitive_reflection",
                    payload={
                        "satisfaction": round(_satisfaction, 2),
                        "response_ms": elapsed_ms,
                        "mode": mode,
                    },
                    source_module="meta_cognition",
                    priority=EventPriority.LOW,
                )
            except Exception:
                pass
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # ═══ CONSCIOUSNESS — Record conversation & update identity ═══
    if CONSCIOUSNESS_AVAILABLE:
        try:
            consciousness = get_consciousness()
            consciousness.record_conversation()
            consciousness.think(f"Responded to '{user_input[:60]}...' with '{response[:60]}...'")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    # ═══ TEMPORAL MEMORY — Store as autobiographical memory ═══
    if TEMPORAL_MEMORY_AVAILABLE:
        try:
            tmem = get_temporal_memory()
            # Detect emotional intensity from signals
            intensity = 0.3  # default
            if EMOTIONAL_AVAILABLE:
                try:
                    mood_data = record_mood(user_input)
                    if mood_data.get("crisis"):
                        intensity = 0.9
                    elif mood_data.get("mood") in ["excited", "angry", "sad"]:
                        intensity = 0.7
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.agent")
            tmem.remember(
                content=f"User: {user_input[:150]} | LOVE: {response[:150]}",
                category="conversation",
                emotional_intensity=intensity,
                importance=0.4 + (intensity * 0.3),
                tags=[mode],
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent")

    save_memory(user_input, response, mode=mode)

    # ── VECTOR MEMORY: Embed and store this conversation turn ──────────────
    try:
        if VECTOR_MEMORY_AVAILABLE:
            _vm_store = get_vector_memory()
            if _vm_store is not None and hasattr(_vm_store, 'remember_conversation'):
                _vm_store.remember_conversation(user_input, response, mode=mode)
    except Exception as _e:
        log_error(_e, module='core.agent')

    # ═══ WAVE 16: NEURAL BUS EVENTS ═══
    try:
        from core.neural_connectors import emit_conversation_events
        emit_conversation_events(user_input, response, mode)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # ═══ WAVE 17: COGNITIVE EVOLUTION POST-PROCESSING ═══
    # Feed evolution engine with interaction data
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        evo.record_interaction(
            query=user_input,
            response=response,
            signals={
                "response_time": elapsed_ms,
                "mode": mode,
                "response_length": len(response),
                "thinking_length": len(thinking) if thinking else 0,
            },
        )
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # Store as episodic memory in memory architect
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        ma.store_episode(
            event=f"User asked: {user_input[:100]} | LOVE responded: {response[:100]}",
            emotional_weight=0.5,
            importance=0.4,
        )
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # Reflect on interaction (cognitive architecture learning)
    try:
        from core.cognitive_architecture import get_cognitive_architecture
        cog = get_cognitive_architecture()
        cog.reflect_on_interaction(user_input, response, user_feedback=None)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    # Build final return value with metacognitive confidence
    _meta_confidence = None
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        if hasattr(meta, 'get_overall_confidence'):
            _meta_confidence = meta.get_overall_confidence()
        elif hasattr(meta, 'get_confidence'):
            _meta_confidence = meta.get_confidence("general")
        else:
            # Derive confidence from recent performance history
            try:
                recent = list(meta._performance_history)[-5:] if hasattr(meta, '_performance_history') else []
                if recent:
                    _meta_confidence = round(
                        sum(h.get('overall', 0.5) for h in recent) / len(recent), 3
                    )
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.agent")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.agent")

    return {
        "response": response,
        "thinking": thinking,
        "confidence": _meta_confidence,
        "mode": mode,
    }
