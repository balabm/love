# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.home_repair_coach import get_home_repair_coach
from core.diy_project_planner import get_diy_project_planner
from core.maker_mindset_trainer import get_maker_mindset_trainer
from core.handcraft_joy_cultivator import get_handcraft_joy_cultivator
"""

api_routes = '''

@router.post("/home_repair_coach/record")
def home_repair_coach_record(task: str = "", repair_type: str = "", confidence: float = 0.0, skill: float = 0.0, preparation: float = 0.0, safety: float = 0.0, completion: float = 0.0, learning: float = 0.0, notes: str = ""):
    entry = get_home_repair_coach().record_repair(task=task, repair_type=repair_type, confidence=confidence, skill=skill, preparation=preparation, safety=safety, completion=completion, learning=learning, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/home_repair_coach/stats")
def home_repair_coach_stats():
    return get_home_repair_coach().get_repair_stats()

@router.get("/home_repair_coach/score")
def home_repair_coach_score():
    return {"repair_score": get_home_repair_coach().get_repair_score()}

@router.post("/diy_project_planner/record")
def diy_project_planner_record(project: str = "", project_type: str = "", planning: float = 0.0, execution: float = 0.0, patience: float = 0.0, creativity: float = 0.0, satisfaction: float = 0.0, completion: float = 0.0, notes: str = ""):
    entry = get_diy_project_planner().record_project(project=project, project_type=project_type, planning=planning, execution=execution, patience=patience, creativity=creativity, satisfaction=satisfaction, completion=completion, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/diy_project_planner/stats")
def diy_project_planner_stats():
    return get_diy_project_planner().get_project_stats()

@router.get("/diy_project_planner/score")
def diy_project_planner_score():
    return {"project_score": get_diy_project_planner().get_project_score()}

@router.post("/maker_mindset_trainer/record")
def maker_mindset_trainer_record(creation: str = "", make_type: str = "", curiosity: float = 0.0, resourcefulness: float = 0.0, persistence: float = 0.0, learning: float = 0.0, joy: float = 0.0, flow: float = 0.0, notes: str = ""):
    entry = get_maker_mindset_trainer().record_make(creation=creation, make_type=make_type, curiosity=curiosity, resourcefulness=resourcefulness, persistence=persistence, learning=learning, joy=joy, flow=flow, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/maker_mindset_trainer/stats")
def maker_mindset_trainer_stats():
    return get_maker_mindset_trainer().get_make_stats()

@router.get("/maker_mindset_trainer/score")
def maker_mindset_trainer_score():
    return {"make_score": get_maker_mindset_trainer().get_make_score()}

@router.post("/handcraft_joy_cultivator/record")
def handcraft_joy_cultivator_record(item: str = "", craft_type: str = "", skill: float = 0.0, patience: float = 0.0, creativity: float = 0.0, beauty: float = 0.0, satisfaction: float = 0.0, flow: float = 0.0, notes: str = ""):
    entry = get_handcraft_joy_cultivator().record_handcraft(item=item, craft_type=craft_type, skill=skill, patience=patience, creativity=creativity, beauty=beauty, satisfaction=satisfaction, flow=flow, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/handcraft_joy_cultivator/stats")
def handcraft_joy_cultivator_stats():
    return get_handcraft_joy_cultivator().get_handcraft_stats()

@router.get("/handcraft_joy_cultivator/score")
def handcraft_joy_cultivator_score():
    return {"handcraft_score": get_handcraft_joy_cultivator().get_handcraft_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "home_repair_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch61 = """
        # Batch 61 — DIY & Home Craft Intelligence
        from core.home_repair_coach import get_home_repair_coach
        from core.diy_project_planner import get_diy_project_planner
        from core.maker_mindset_trainer import get_maker_mindset_trainer
        from core.handcraft_joy_cultivator import get_handcraft_joy_cultivator
        self.home_repair_coach = get_home_repair_coach()
        self.diy_project_planner = get_diy_project_planner()
        self.maker_mindset_trainer = get_maker_mindset_trainer()
        self.handcraft_joy_cultivator = get_handcraft_joy_cultivator()
"""

if "home_repair_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch61 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch61_brief = """
        # Batch 61 — DIY & Home Craft Intelligence
        try:
            from core.home_repair_coach import get_home_repair_coach
            report["home_repair_coach"] = get_home_repair_coach().get_repair_stats()
        except Exception as e:
            report["home_repair_coach"] = {"error": str(e)}
        try:
            from core.diy_project_planner import get_diy_project_planner
            report["diy_project_planner"] = get_diy_project_planner().get_project_stats()
        except Exception as e:
            report["diy_project_planner"] = {"error": str(e)}
        try:
            from core.maker_mindset_trainer import get_maker_mindset_trainer
            report["maker_mindset_trainer"] = get_maker_mindset_trainer().get_make_stats()
        except Exception as e:
            report["maker_mindset_trainer"] = {"error": str(e)}
        try:
            from core.handcraft_joy_cultivator import get_handcraft_joy_cultivator
            report["handcraft_joy_cultivator"] = get_handcraft_joy_cultivator().get_handcraft_stats()
        except Exception as e:
            report["handcraft_joy_cultivator"] = {"error": str(e)}
"""

if "home_repair_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch61_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch61_pulse = """
        # Batch 61 — DIY & Home Craft Intelligence
        try:
            from core.home_repair_coach import get_home_repair_coach
            report["home_repair_coach_pulse"] = get_home_repair_coach().get_repair_score()
        except Exception:
            pass
        try:
            from core.diy_project_planner import get_diy_project_planner
            report["diy_project_planner_pulse"] = get_diy_project_planner().get_project_score()
        except Exception:
            pass
        try:
            from core.maker_mindset_trainer import get_maker_mindset_trainer
            report["maker_mindset_trainer_pulse"] = get_maker_mindset_trainer().get_make_score()
        except Exception:
            pass
        try:
            from core.handcraft_joy_cultivator import get_handcraft_joy_cultivator
            report["handcraft_joy_cultivator_pulse"] = get_handcraft_joy_cultivator().get_handcraft_score()
        except Exception:
            pass
"""

if "home_repair_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch61_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 61 wiring complete.")
