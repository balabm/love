# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.money_mindset_coach import get_money_mindset_coach
from core.scarcity_healer import get_scarcity_healer
from core.generosity_cultivator import get_generosity_cultivator
from core.abundance_architect import get_abundance_architect
"""

api_routes = '''

@router.post("/money_mindset_coach/record")
def money_mindset_coach_record(situation: str = "", mindset_type: str = "", clarity: float = 0.0, confidence: float = 0.0, alignment: float = 0.0, generosity: float = 0.0, action_taken: float = 0.0, notes: str = ""):
    entry = get_money_mindset_coach().record_mindset(situation=situation, mindset_type=mindset_type, clarity=clarity, confidence=confidence, alignment=alignment, generosity=generosity, action_taken=action_taken, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/money_mindset_coach/stats")
def money_mindset_coach_stats():
    return get_money_mindset_coach().get_mindset_stats()

@router.get("/money_mindset_coach/score")
def money_mindset_coach_score():
    return {"mindset_score": get_money_mindset_coach().get_mindset_score()}

@router.post("/scarcity_healer/record")
def scarcity_healer_record(situation: str = "", scarcity_type: str = "", distress: float = 0.0, reality: float = 0.0, response: float = 0.0, gratitude: float = 0.0, perspective: float = 0.0, sufficiency: float = 0.0, notes: str = ""):
    entry = get_scarcity_healer().record_scarcity(situation=situation, scarcity_type=scarcity_type, distress=distress, reality=reality, response=response, gratitude=gratitude, perspective=perspective, sufficiency=sufficiency, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/scarcity_healer/stats")
def scarcity_healer_stats():
    return get_scarcity_healer().get_scarcity_stats()

@router.get("/scarcity_healer/score")
def scarcity_healer_score():
    return {"scarcity_score": get_scarcity_healer().get_scarcity_score()}

@router.post("/generosity_cultivator/record")
def generosity_cultivator_record(gift: str = "", generosity_type: str = "", joy: float = 0.0, reciprocity: float = 0.0, sustainability: float = 0.0, boundaries: float = 0.0, receiving: float = 0.0, notes: str = ""):
    entry = get_generosity_cultivator().record_generosity(gift=gift, generosity_type=generosity_type, joy=joy, reciprocity=reciprocity, sustainability=sustainability, boundaries=boundaries, receiving=receiving, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/generosity_cultivator/stats")
def generosity_cultivator_stats():
    return get_generosity_cultivator().get_generosity_stats()

@router.get("/generosity_cultivator/score")
def generosity_cultivator_score():
    return {"generosity_score": get_generosity_cultivator().get_generosity_score()}

@router.post("/abundance_architect/record")
def abundance_architect_record(manifestation: str = "", abundance_type: str = "", recognition: float = 0.0, gratitude: float = 0.0, expansion: float = 0.0, sharing: float = 0.0, blocking: float = 0.0, notes: str = ""):
    entry = get_abundance_architect().record_abundance(manifestation=manifestation, abundance_type=abundance_type, recognition=recognition, gratitude=gratitude, expansion=expansion, sharing=sharing, blocking=blocking, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/abundance_architect/stats")
def abundance_architect_stats():
    return get_abundance_architect().get_abundance_stats()

@router.get("/abundance_architect/score")
def abundance_architect_score():
    return {"abundance_score": get_abundance_architect().get_abundance_score()}
'''

# Insert imports before the last import block
last_import = api.rfind("from core.")
last_import_end = api.find("\n", api.find("\n", last_import) + 1)
if api_imports.strip() not in api:
    api = api[:last_import_end] + "\n" + api_imports + api[last_import_end:]

# Insert routes before the last line
if "money_mindset_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch49 = """
        # Batch 49 — Financial Psychology
        from core.money_mindset_coach import get_money_mindset_coach
        from core.scarcity_healer import get_scarcity_healer
        from core.generosity_cultivator import get_generosity_cultivator
        from core.abundance_architect import get_abundance_architect
        self.money_mindset_coach = get_money_mindset_coach()
        self.scarcity_healer = get_scarcity_healer()
        self.generosity_cultivator = get_generosity_cultivator()
        self.abundance_architect = get_abundance_architect()
"""

if "money_mindset_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch49 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch49_brief = """
        # Batch 49 — Financial Psychology
        try:
            from core.money_mindset_coach import get_money_mindset_coach
            report["money_mindset_coach"] = get_money_mindset_coach().get_mindset_stats()
        except Exception as e:
            report["money_mindset_coach"] = {"error": str(e)}
        try:
            from core.scarcity_healer import get_scarcity_healer
            report["scarcity_healer"] = get_scarcity_healer().get_scarcity_stats()
        except Exception as e:
            report["scarcity_healer"] = {"error": str(e)}
        try:
            from core.generosity_cultivator import get_generosity_cultivator
            report["generosity_cultivator"] = get_generosity_cultivator().get_generosity_stats()
        except Exception as e:
            report["generosity_cultivator"] = {"error": str(e)}
        try:
            from core.abundance_architect import get_abundance_architect
            report["abundance_architect"] = get_abundance_architect().get_abundance_stats()
        except Exception as e:
            report["abundance_architect"] = {"error": str(e)}
"""

if "money_mindset_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch49_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch49_pulse = """
        # Batch 49 — Financial Psychology
        try:
            from core.money_mindset_coach import get_money_mindset_coach
            report["money_mindset_coach_pulse"] = get_money_mindset_coach().get_mindset_score()
        except Exception:
            pass
        try:
            from core.scarcity_healer import get_scarcity_healer
            report["scarcity_healer_pulse"] = get_scarcity_healer().get_scarcity_score()
        except Exception:
            pass
        try:
            from core.generosity_cultivator import get_generosity_cultivator
            report["generosity_cultivator_pulse"] = get_generosity_cultivator().get_generosity_score()
        except Exception:
            pass
        try:
            from core.abundance_architect import get_abundance_architect
            report["abundance_architect_pulse"] = get_abundance_architect().get_abundance_score()
        except Exception:
            pass
"""

if "money_mindset_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch49_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 49 wiring complete.")
