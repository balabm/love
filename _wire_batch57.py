# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.pet_bonding_coach import get_pet_bonding_coach
from core.animal_empathy_trainer import get_animal_empathy_trainer
from core.pet_loss_support import get_pet_loss_support
from core.human_animal_connection_guide import get_human_animal_connection_guide
"""

api_routes = '''

@router.post("/pet_bonding_coach/record")
def pet_bonding_coach_record(activity: str = "", bonding_type: str = "", quality: float = 0.0, reciprocity: float = 0.0, joy: float = 0.0, depth: float = 0.0, attention: float = 0.0, notes: str = ""):
    entry = get_pet_bonding_coach().record_bonding(activity=activity, bonding_type=bonding_type, quality=quality, reciprocity=reciprocity, joy=joy, depth=depth, attention=attention, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/pet_bonding_coach/stats")
def pet_bonding_coach_stats():
    return get_pet_bonding_coach().get_bonding_stats()

@router.get("/pet_bonding_coach/score")
def pet_bonding_coach_score():
    return {"bonding_score": get_pet_bonding_coach().get_bonding_score()}

@router.post("/animal_empathy_trainer/record")
def animal_empathy_trainer_record(animal: str = "", empathy_type: str = "", accuracy: float = 0.0, connection: float = 0.0, understanding: float = 0.0, growth: float = 0.0, patience: float = 0.0, notes: str = ""):
    entry = get_animal_empathy_trainer().record_empathy(animal=animal, empathy_type=empathy_type, accuracy=accuracy, connection=connection, understanding=understanding, growth=growth, patience=patience, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/animal_empathy_trainer/stats")
def animal_empathy_trainer_stats():
    return get_animal_empathy_trainer().get_empathy_stats()

@router.get("/animal_empathy_trainer/score")
def animal_empathy_trainer_score():
    return {"empathy_score": get_animal_empathy_trainer().get_empathy_score()}

@router.post("/pet_loss_support/record")
def pet_loss_support_record(moment: str = "", grief_type: str = "", intensity: float = 0.0, processing: float = 0.0, support: float = 0.0, integration: float = 0.0, memorial: float = 0.0, notes: str = ""):
    entry = get_pet_loss_support().record_grief(moment=moment, grief_type=grief_type, intensity=intensity, processing=processing, support=support, integration=integration, memorial=memorial, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/pet_loss_support/stats")
def pet_loss_support_stats():
    return get_pet_loss_support().get_grief_stats()

@router.get("/pet_loss_support/score")
def pet_loss_support_score():
    return {"grief_score": get_pet_loss_support().get_grief_score()}

@router.post("/human_animal_connection_guide/record")
def human_animal_connection_guide_record(animal: str = "", connection_type: str = "", wonder: float = 0.0, respect: float = 0.0, reciprocity: float = 0.0, expansion: float = 0.0, ethical: float = 0.0, notes: str = ""):
    entry = get_human_animal_connection_guide().record_connection(animal=animal, connection_type=connection_type, wonder=wonder, respect=respect, reciprocity=reciprocity, expansion=expansion, ethical=ethical, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/human_animal_connection_guide/stats")
def human_animal_connection_guide_stats():
    return get_human_animal_connection_guide().get_connection_stats()

@router.get("/human_animal_connection_guide/score")
def human_animal_connection_guide_score():
    return {"connection_score": get_human_animal_connection_guide().get_connection_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "pet_bonding_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch57 = """
        # Batch 57 — Pets & Animals Intelligence
        from core.pet_bonding_coach import get_pet_bonding_coach
        from core.animal_empathy_trainer import get_animal_empathy_trainer
        from core.pet_loss_support import get_pet_loss_support
        from core.human_animal_connection_guide import get_human_animal_connection_guide
        self.pet_bonding_coach = get_pet_bonding_coach()
        self.animal_empathy_trainer = get_animal_empathy_trainer()
        self.pet_loss_support = get_pet_loss_support()
        self.human_animal_connection_guide = get_human_animal_connection_guide()
"""

if "pet_bonding_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch57 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch57_brief = """
        # Batch 57 — Pets & Animals Intelligence
        try:
            from core.pet_bonding_coach import get_pet_bonding_coach
            report["pet_bonding_coach"] = get_pet_bonding_coach().get_bonding_stats()
        except Exception as e:
            report["pet_bonding_coach"] = {"error": str(e)}
        try:
            from core.animal_empathy_trainer import get_animal_empathy_trainer
            report["animal_empathy_trainer"] = get_animal_empathy_trainer().get_empathy_stats()
        except Exception as e:
            report["animal_empathy_trainer"] = {"error": str(e)}
        try:
            from core.pet_loss_support import get_pet_loss_support
            report["pet_loss_support"] = get_pet_loss_support().get_grief_stats()
        except Exception as e:
            report["pet_loss_support"] = {"error": str(e)}
        try:
            from core.human_animal_connection_guide import get_human_animal_connection_guide
            report["human_animal_connection_guide"] = get_human_animal_connection_guide().get_connection_stats()
        except Exception as e:
            report["human_animal_connection_guide"] = {"error": str(e)}
"""

if "pet_bonding_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch57_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch57_pulse = """
        # Batch 57 — Pets & Animals Intelligence
        try:
            from core.pet_bonding_coach import get_pet_bonding_coach
            report["pet_bonding_coach_pulse"] = get_pet_bonding_coach().get_bonding_score()
        except Exception:
            pass
        try:
            from core.animal_empathy_trainer import get_animal_empathy_trainer
            report["animal_empathy_trainer_pulse"] = get_animal_empathy_trainer().get_empathy_score()
        except Exception:
            pass
        try:
            from core.pet_loss_support import get_pet_loss_support
            report["pet_loss_support_pulse"] = get_pet_loss_support().get_grief_score()
        except Exception:
            pass
        try:
            from core.human_animal_connection_guide import get_human_animal_connection_guide
            report["human_animal_connection_guide_pulse"] = get_human_animal_connection_guide().get_connection_score()
        except Exception:
            pass
"""

if "pet_bonding_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch57_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 57 wiring complete.")
