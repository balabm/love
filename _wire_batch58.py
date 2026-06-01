# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.garden_therapy_coach import get_garden_therapy_coach
from core.plant_parenting_guide import get_plant_parenting_guide
from core.seasonal_garden_planner import get_seasonal_garden_planner
from core.urban_gardening_coach import get_urban_gardening_coach
"""

api_routes = '''

@router.post("/garden_therapy_coach/record")
def garden_therapy_coach_record(activity: str = "", garden_type: str = "", presence: float = 0.0, growth: float = 0.0, patience: float = 0.0, healing: float = 0.0, sensory: float = 0.0, notes: str = ""):
    entry = get_garden_therapy_coach().record_garden(activity=activity, garden_type=garden_type, presence=presence, growth=growth, patience=patience, healing=healing, sensory=sensory, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/garden_therapy_coach/stats")
def garden_therapy_coach_stats():
    return get_garden_therapy_coach().get_garden_stats()

@router.get("/garden_therapy_coach/score")
def garden_therapy_coach_score():
    return {"garden_score": get_garden_therapy_coach().get_garden_score()}

@router.post("/plant_parenting_guide/record")
def plant_parenting_guide_record(plant: str = "", care_type: str = "", attentiveness: float = 0.0, health: float = 0.0, learning: float = 0.0, joy: float = 0.0, observation: float = 0.0, notes: str = ""):
    entry = get_plant_parenting_guide().record_care(plant=plant, care_type=care_type, attentiveness=attentiveness, health=health, learning=learning, joy=joy, observation=observation, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/plant_parenting_guide/stats")
def plant_parenting_guide_stats():
    return get_plant_parenting_guide().get_care_stats()

@router.get("/plant_parenting_guide/score")
def plant_parenting_guide_score():
    return {"care_score": get_plant_parenting_guide().get_care_score()}

@router.post("/seasonal_garden_planner/record")
def seasonal_garden_planner_record(phase: str = "", season_type: str = "", planning: float = 0.0, execution: float = 0.0, adaptation: float = 0.0, learning: float = 0.0, harmony: float = 0.0, notes: str = ""):
    entry = get_seasonal_garden_planner().record_season(phase=phase, season_type=season_type, planning=planning, execution=execution, adaptation=adaptation, learning=learning, harmony=harmony, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/seasonal_garden_planner/stats")
def seasonal_garden_planner_stats():
    return get_seasonal_garden_planner().get_season_stats()

@router.get("/seasonal_garden_planner/score")
def seasonal_garden_planner_score():
    return {"season_score": get_seasonal_garden_planner().get_season_score()}

@router.post("/urban_gardening_coach/record")
def urban_gardening_coach_record(garden: str = "", urban_type: str = "", creativity: float = 0.0, resourcefulness: float = 0.0, yield_val: float = 0.0, satisfaction: float = 0.0, community: float = 0.0, notes: str = ""):
    entry = get_urban_gardening_coach().record_urban(garden=garden, urban_type=urban_type, creativity=creativity, resourcefulness=resourcefulness, yield_val=yield_val, satisfaction=satisfaction, community=community, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/urban_gardening_coach/stats")
def urban_gardening_coach_stats():
    return get_urban_gardening_coach().get_urban_stats()

@router.get("/urban_gardening_coach/score")
def urban_gardening_coach_score():
    return {"urban_score": get_urban_gardening_coach().get_urban_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "garden_therapy_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch58 = """
        # Batch 58 — Gardening & Plants Intelligence
        from core.garden_therapy_coach import get_garden_therapy_coach
        from core.plant_parenting_guide import get_plant_parenting_guide
        from core.seasonal_garden_planner import get_seasonal_garden_planner
        from core.urban_gardening_coach import get_urban_gardening_coach
        self.garden_therapy_coach = get_garden_therapy_coach()
        self.plant_parenting_guide = get_plant_parenting_guide()
        self.seasonal_garden_planner = get_seasonal_garden_planner()
        self.urban_gardening_coach = get_urban_gardening_coach()
"""

if "garden_therapy_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch58 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch58_brief = """
        # Batch 58 — Gardening & Plants Intelligence
        try:
            from core.garden_therapy_coach import get_garden_therapy_coach
            report["garden_therapy_coach"] = get_garden_therapy_coach().get_garden_stats()
        except Exception as e:
            report["garden_therapy_coach"] = {"error": str(e)}
        try:
            from core.plant_parenting_guide import get_plant_parenting_guide
            report["plant_parenting_guide"] = get_plant_parenting_guide().get_care_stats()
        except Exception as e:
            report["plant_parenting_guide"] = {"error": str(e)}
        try:
            from core.seasonal_garden_planner import get_seasonal_garden_planner
            report["seasonal_garden_planner"] = get_seasonal_garden_planner().get_season_stats()
        except Exception as e:
            report["seasonal_garden_planner"] = {"error": str(e)}
        try:
            from core.urban_gardening_coach import get_urban_gardening_coach
            report["urban_gardening_coach"] = get_urban_gardening_coach().get_urban_stats()
        except Exception as e:
            report["urban_gardening_coach"] = {"error": str(e)}
"""

if "garden_therapy_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch58_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch58_pulse = """
        # Batch 58 — Gardening & Plants Intelligence
        try:
            from core.garden_therapy_coach import get_garden_therapy_coach
            report["garden_therapy_coach_pulse"] = get_garden_therapy_coach().get_garden_score()
        except Exception:
            pass
        try:
            from core.plant_parenting_guide import get_plant_parenting_guide
            report["plant_parenting_guide_pulse"] = get_plant_parenting_guide().get_care_score()
        except Exception:
            pass
        try:
            from core.seasonal_garden_planner import get_seasonal_garden_planner
            report["seasonal_garden_planner_pulse"] = get_seasonal_garden_planner().get_season_score()
        except Exception:
            pass
        try:
            from core.urban_gardening_coach import get_urban_gardening_coach
            report["urban_gardening_coach_pulse"] = get_urban_gardening_coach().get_urban_score()
        except Exception:
            pass
"""

if "garden_therapy_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch58_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 58 wiring complete.")
