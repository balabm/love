import re

# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r") as f:
    api = f.read()

api_imports = """from core.shadow_integrator import get_shadow_integrator
from core.inner_critic_tamer import get_inner_critic_tamer
from core.perfectionism_healer import get_perfectionism_healer
from core.comparison_detoxifier import get_comparison_detoxifier
"""

api_routes = '''

@router.post("/shadow_integrator/record")
def shadow_integrator_record(shadow: str = "", shadow_type: str = "", awareness: float = 0.0, acceptance: float = 0.0, integration: float = 0.0, trigger: str = "", projection: float = 0.0, notes: str = ""):
    entry = get_shadow_integrator().record_encounter(shadow=shadow, shadow_type=shadow_type, awareness=awareness, acceptance=acceptance, integration=integration, trigger=trigger, projection=projection, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/shadow_integrator/stats")
def shadow_integrator_stats():
    return get_shadow_integrator().get_shadow_stats()

@router.get("/shadow_integrator/score")
def shadow_integrator_score():
    return {"shadow_score": get_shadow_integrator().get_shadow_score()}

@router.post("/inner_critic_tamer/record")
def inner_critic_tamer_record(critic: str = "", critic_type: str = "", harshness: float = 0.5, accuracy: float = 0.0, response: float = 0.0, self_compassion: float = 0.0, challenge: float = 0.0, notes: str = ""):
    entry = get_inner_critic_tamer().record_critic(critic=critic, critic_type=critic_type, harshness=harshness, accuracy=accuracy, response=response, self_compassion=self_compassion, challenge=challenge, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/inner_critic_tamer/stats")
def inner_critic_tamer_stats():
    return get_inner_critic_tamer().get_critic_stats()

@router.get("/inner_critic_tamer/score")
def inner_critic_tamer_score():
    return {"critic_score": get_inner_critic_tamer().get_critic_score()}

@router.post("/perfectionism_healer/record")
def perfectionism_healer_record(situation: str = "", perfectionism_type: str = "", cost: float = 0.0, completion: float = 0.0, satisfaction: float = 0.0, self_acceptance: float = 0.0, good_enough: float = 0.0, notes: str = ""):
    entry = get_perfectionism_healer().record_perfectionism(situation=situation, perfectionism_type=perfectionism_type, cost=cost, completion=completion, satisfaction=satisfaction, self_acceptance=self_acceptance, good_enough=good_enough, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/perfectionism_healer/stats")
def perfectionism_healer_stats():
    return get_perfectionism_healer().get_perfectionism_stats()

@router.get("/perfectionism_healer/score")
def perfectionism_healer_score():
    return {"perfectionism_score": get_perfectionism_healer().get_perfectionism_score()}

@router.post("/comparison_detoxifier/record")
def comparison_detoxifier_record(comparison: str = "", comparison_type: str = "", distress: float = 0.0, accuracy: float = 0.0, response: float = 0.0, gratitude: float = 0.0, self_compassion: float = 0.0, self_reference: float = 0.0, notes: str = ""):
    entry = get_comparison_detoxifier().record_comparison(comparison=comparison, comparison_type=comparison_type, distress=distress, accuracy=accuracy, response=response, gratitude=gratitude, self_compassion=self_compassion, self_reference=self_reference, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/comparison_detoxifier/stats")
def comparison_detoxifier_stats():
    return get_comparison_detoxifier().get_comparison_stats()

@router.get("/comparison_detoxifier/score")
def comparison_detoxifier_score():
    return {"comparison_score": get_comparison_detoxifier().get_comparison_score()}
'''

# Insert imports before the last import block
last_import = api.rfind("from core.")
last_import_end = api.find("\n", api.find("\n", last_import) + 1)
if api_imports.strip() not in api:
    api = api[:last_import_end] + "\n" + api_imports + api[last_import_end:]

# Insert routes before the last line
if "shadow_integrator/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w") as f:
    f.write(api)

print("API wired.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r") as f:
    startup = f.read()

batch48 = """
        # Batch 48 — Shadow & Self-Acceptance
        from core.shadow_integrator import get_shadow_integrator
        from core.inner_critic_tamer import get_inner_critic_tamer
        from core.perfectionism_healer import get_perfectionism_healer
        from core.comparison_detoxifier import get_comparison_detoxifier
        self.shadow_integrator = get_shadow_integrator()
        self.inner_critic_tamer = get_inner_critic_tamer()
        self.perfectionism_healer = get_perfectionism_healer()
        self.comparison_detoxifier = get_comparison_detoxifier()
"""

if "shadow_integrator" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch48 + "        # === End Modern AI Systems ===")

with open(startup_path, "w") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r") as f:
    briefing = f.read()

batch48_brief = """
        # Batch 48 — Shadow & Self-Acceptance
        try:
            from core.shadow_integrator import get_shadow_integrator
            report["shadow_integrator"] = get_shadow_integrator().get_shadow_stats()
        except Exception as e:
            report["shadow_integrator"] = {"error": str(e)}
        try:
            from core.inner_critic_tamer import get_inner_critic_tamer
            report["inner_critic_tamer"] = get_inner_critic_tamer().get_critic_stats()
        except Exception as e:
            report["inner_critic_tamer"] = {"error": str(e)}
        try:
            from core.perfectionism_healer import get_perfectionism_healer
            report["perfectionism_healer"] = get_perfectionism_healer().get_perfectionism_stats()
        except Exception as e:
            report["perfectionism_healer"] = {"error": str(e)}
        try:
            from core.comparison_detoxifier import get_comparison_detoxifier
            report["comparison_detoxifier"] = get_comparison_detoxifier().get_comparison_stats()
        except Exception as e:
            report["comparison_detoxifier"] = {"error": str(e)}
"""

if "shadow_integrator" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch48_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r") as f:
    heartbeat = f.read()

batch48_pulse = """
        # Batch 48 — Shadow & Self-Acceptance
        try:
            from core.shadow_integrator import get_shadow_integrator
            report["shadow_integrator_pulse"] = get_shadow_integrator().get_shadow_score()
        except Exception:
            pass
        try:
            from core.inner_critic_tamer import get_inner_critic_tamer
            report["inner_critic_tamer_pulse"] = get_inner_critic_tamer().get_critic_score()
        except Exception:
            pass
        try:
            from core.perfectionism_healer import get_perfectionism_healer
            report["perfectionism_healer_pulse"] = get_perfectionism_healer().get_perfectionism_score()
        except Exception:
            pass
        try:
            from core.comparison_detoxifier import get_comparison_detoxifier
            report["comparison_detoxifier_pulse"] = get_comparison_detoxifier().get_comparison_score()
        except Exception:
            pass
"""

if "shadow_integrator_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch48_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 48 wiring complete.")
