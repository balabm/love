# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.mindful_eating_coach import get_mindful_eating_coach
from core.cooking_joy_cultivator import get_cooking_joy_cultivator
from core.meal_ritual_designer import get_meal_ritual_designer
from core.food_as_medicine_coach import get_food_as_medicine_coach
"""

api_routes = '''

@router.post("/mindful_eating_coach/record")
def mindful_eating_coach_record(food: str = "", eating_type: str = "", awareness: float = 0.0, satisfaction: float = 0.0, hunger_accuracy: float = 0.0, digestion_comfort: float = 0.0, savoring: float = 0.0, notes: str = ""):
    entry = get_mindful_eating_coach().record_eating(food=food, eating_type=eating_type, awareness=awareness, satisfaction=satisfaction, hunger_accuracy=hunger_accuracy, digestion_comfort=digestion_comfort, savoring=savoring, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/mindful_eating_coach/stats")
def mindful_eating_coach_stats():
    return get_mindful_eating_coach().get_eating_stats()

@router.get("/mindful_eating_coach/score")
def mindful_eating_coach_score():
    return {"eating_score": get_mindful_eating_coach().get_eating_score()}

@router.post("/cooking_joy_cultivator/record")
def cooking_joy_cultivator_record(dish: str = "", cooking_type: str = "", joy: float = 0.0, creativity: float = 0.0, skill: float = 0.0, nourishment: float = 0.0, sharing: float = 0.0, notes: str = ""):
    entry = get_cooking_joy_cultivator().record_cooking(dish=dish, cooking_type=cooking_type, joy=joy, creativity=creativity, skill=skill, nourishment=nourishment, sharing=sharing, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/cooking_joy_cultivator/stats")
def cooking_joy_cultivator_stats():
    return get_cooking_joy_cultivator().get_cooking_stats()

@router.get("/cooking_joy_cultivator/score")
def cooking_joy_cultivator_score():
    return {"cooking_score": get_cooking_joy_cultivator().get_cooking_score()}

@router.post("/meal_ritual_designer/record")
def meal_ritual_designer_record(meal: str = "", ritual_type: str = "", intention: float = 0.0, atmosphere: float = 0.0, meaning: float = 0.0, continuity: float = 0.0, presence: float = 0.0, notes: str = ""):
    entry = get_meal_ritual_designer().record_ritual(meal=meal, ritual_type=ritual_type, intention=intention, atmosphere=atmosphere, meaning=meaning, continuity=continuity, presence=presence, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/meal_ritual_designer/stats")
def meal_ritual_designer_stats():
    return get_meal_ritual_designer().get_ritual_stats()

@router.get("/meal_ritual_designer/score")
def meal_ritual_designer_score():
    return {"ritual_score": get_meal_ritual_designer().get_ritual_score()}

@router.post("/food_as_medicine_coach/record")
def food_as_medicine_coach_record(food: str = "", food_type: str = "", effect: float = 0.0, symptom: float = 0.0, intention: float = 0.0, healing: float = 0.0, prevention: float = 0.0, notes: str = ""):
    entry = get_food_as_medicine_coach().record_food(food=food, food_type=food_type, effect=effect, symptom=symptom, intention=intention, healing=healing, prevention=prevention, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/food_as_medicine_coach/stats")
def food_as_medicine_coach_stats():
    return get_food_as_medicine_coach().get_food_stats()

@router.get("/food_as_medicine_coach/score")
def food_as_medicine_coach_score():
    return {"food_score": get_food_as_medicine_coach().get_food_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "mindful_eating_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch56 = """
        # Batch 56 — Food & Cooking Intelligence
        from core.mindful_eating_coach import get_mindful_eating_coach
        from core.cooking_joy_cultivator import get_cooking_joy_cultivator
        from core.meal_ritual_designer import get_meal_ritual_designer
        from core.food_as_medicine_coach import get_food_as_medicine_coach
        self.mindful_eating_coach = get_mindful_eating_coach()
        self.cooking_joy_cultivator = get_cooking_joy_cultivator()
        self.meal_ritual_designer = get_meal_ritual_designer()
        self.food_as_medicine_coach = get_food_as_medicine_coach()
"""

if "mindful_eating_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch56 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch56_brief = """
        # Batch 56 — Food & Cooking Intelligence
        try:
            from core.mindful_eating_coach import get_mindful_eating_coach
            report["mindful_eating_coach"] = get_mindful_eating_coach().get_eating_stats()
        except Exception as e:
            report["mindful_eating_coach"] = {"error": str(e)}
        try:
            from core.cooking_joy_cultivator import get_cooking_joy_cultivator
            report["cooking_joy_cultivator"] = get_cooking_joy_cultivator().get_cooking_stats()
        except Exception as e:
            report["cooking_joy_cultivator"] = {"error": str(e)}
        try:
            from core.meal_ritual_designer import get_meal_ritual_designer
            report["meal_ritual_designer"] = get_meal_ritual_designer().get_ritual_stats()
        except Exception as e:
            report["meal_ritual_designer"] = {"error": str(e)}
        try:
            from core.food_as_medicine_coach import get_food_as_medicine_coach
            report["food_as_medicine_coach"] = get_food_as_medicine_coach().get_food_stats()
        except Exception as e:
            report["food_as_medicine_coach"] = {"error": str(e)}
"""

if "mindful_eating_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch56_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch56_pulse = """
        # Batch 56 — Food & Cooking Intelligence
        try:
            from core.mindful_eating_coach import get_mindful_eating_coach
            report["mindful_eating_coach_pulse"] = get_mindful_eating_coach().get_eating_score()
        except Exception:
            pass
        try:
            from core.cooking_joy_cultivator import get_cooking_joy_cultivator
            report["cooking_joy_cultivator_pulse"] = get_cooking_joy_cultivator().get_cooking_score()
        except Exception:
            pass
        try:
            from core.meal_ritual_designer import get_meal_ritual_designer
            report["meal_ritual_designer_pulse"] = get_meal_ritual_designer().get_ritual_score()
        except Exception:
            pass
        try:
            from core.food_as_medicine_coach import get_food_as_medicine_coach
            report["food_as_medicine_coach_pulse"] = get_food_as_medicine_coach().get_food_score()
        except Exception:
            pass
"""

if "mindful_eating_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch56_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 56 wiring complete.")
