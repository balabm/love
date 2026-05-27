import sys
import os
import time

sys.path.insert(0, os.getcwd())

print("[Debug] Starting debug_chat.py", flush=True)

print("[Debug] 1. Importing ping_active...", flush=True)
from core.idle_mind import ping_active
print("[Debug] 1. Calling ping_active...", flush=True)
ping_active()

print("[Debug] 2. Importing get_hpc...", flush=True)
from core.hierarchical_predictive_coding import get_hpc
print("[Debug] 2. Calling get_hpc().feed...", flush=True)
get_hpc().feed("hello", source="user")

print("[Debug] 3. Importing latent/ssm...", flush=True)
from core.world_model_latent import get_world_model_latent
from core.state_space_memory import get_ssm_memory
print("[Debug] 3. Calling get_world_model_latent...", flush=True)
_wm = get_world_model_latent()
if _wm._recent_obs:
    print("[Debug] 3. Calling get_ssm_memory().step...", flush=True)
    get_ssm_memory().step(_wm._recent_obs[-1].state)

print("[Debug] 4. Importing handle_fix_command...", flush=True)
from core.agent import handle_fix_command
print("[Debug] 4. Calling handle_fix_command...", flush=True)
handle_fix_command("hello")

print("[Debug] 5. Importing handle_user_command...", flush=True)
from core.system_control import handle_user_command
print("[Debug] 5. Calling handle_user_command...", flush=True)
handle_user_command("hello")

print("[Debug] 6. Importing remember (LTM)...", flush=True)
from core.long_term_memory import remember
print("[Debug] 6. Calling remember...", flush=True)
remember("hello", limit=5)

print("[Debug] 7. Importing get_consciousness...", flush=True)
from core.consciousness import get_consciousness
print("[Debug] 7. Calling consciousness methods...", flush=True)
consciousness = get_consciousness()
if consciousness:
    consciousness.process_emotional_input("hello")
    consciousness.get_self_narrative()

print("[Debug] 8. Importing get_temporal_memory...", flush=True)
from core.temporal_memory import get_temporal_memory
print("[Debug] 8. Calling temporal_memory...", flush=True)
tmem = get_temporal_memory()
if tmem:
    tmem.get_temporal_context(query="hello", limit=5)

print("[Debug] 9. Importing get_recursive_goals...", flush=True)
from core.recursive_goals import get_recursive_goals
print("[Debug] 9. Calling recursive_goals...", flush=True)
rgoals = get_recursive_goals()
if rgoals:
    rgoals.get_prompt_context()

print("[Debug] 10. Importing get_prompt_dna...", flush=True)
from core.prompt_dna import get_prompt_dna
print("[Debug] 10. Calling prompt_dna...", flush=True)
dna = get_prompt_dna()
if dna:
    dna.assemble_prompt_addendum()

print("[Debug] 11. Importing get_cognitive_architecture...", flush=True)
from core.cognitive_architecture import get_cognitive_architecture
print("[Debug] 11. Calling cognitive_architecture...", flush=True)
cog = get_cognitive_architecture()
if cog:
    _cog_routing = cog.classify_and_route("hello")
    print("[Debug] 11. classified", flush=True)
    cog.think_deeply(query="hello", budget="moderate")

print("[Debug] All steps finished successfully!", flush=True)
