# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.body_awareness_trainer import get_body_awareness_trainer
from core.breath_work_coach import get_breath_work_coach
from core.movement_intelligence import get_movement_intelligence
from core.posture_presence_coach import get_posture_presence_coach
"""

api_routes = '''

@router.post("/body_awareness_trainer/record")
def body_awareness_trainer_record(sensation: str = "", body_area: str = "", awareness: float = 0.0, response: float = 0.0, integration: float = 0.0, grounding: float = 0.0, notes: str = ""):
    entry = get_body_awareness_trainer().record_body(sensation=sensation, body_area=body_area, awareness=awareness, response=response, integration=integration, grounding=grounding, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/body_awareness_trainer/stats")
def body_awareness_trainer_stats():
    return get_body_awareness_trainer().get_body_stats()

@router.get("/body_awareness_trainer/score")
def body_awareness_trainer_score():
    return {"body_score": get_body_awareness_trainer().get_body_score()}

@router.post("/breath_work_coach/record")
def breath_work_coach_record(technique: str = "", breath_type: str = "", calm: float = 0.0, energy: float = 0.0, clarity: float = 0.0, practice: float = 0.0, duration: float = 0.0, notes: str = ""):
    entry = get_breath_work_coach().record_breath(technique=technique, breath_type=breath_type, calm=calm, energy=energy, clarity=clarity, practice=practice, duration=duration, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/breath_work_coach/stats")
def breath_work_coach_stats():
    return get_breath_work_coach().get_breath_stats()

@router.get("/breath_work_coach/score")
def breath_work_coach_score():
    return {"breath_score": get_breath_work_coach().get_breath_score()}

@router.post("/movement_intelligence/record")
def movement_intelligence_record(activity: str = "", movement_type: str = "", joy: float = 0.0, energy: float = 0.0, ease: float = 0.0, integration: float = 0.0, duration: float = 0.0, notes: str = ""):
    entry = get_movement_intelligence().record_movement(activity=activity, movement_type=movement_type, joy=joy, energy=energy, ease=ease, integration=integration, duration=duration, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/movement_intelligence/stats")
def movement_intelligence_stats():
    return get_movement_intelligence().get_movement_stats()

@router.get("/movement_intelligence/score")
def movement_intelligence_score():
    return {"movement_score": get_movement_intelligence().get_movement_score()}

@router.post("/posture_presence_coach/record")
def posture_presence_coach_record(situation: str = "", presence_type: str = "", posture: float = 0.0, presence: float = 0.0, confidence: float = 0.0, energy: float = 0.0, openness: float = 0.0, notes: str = ""):
    entry = get_posture_presence_coach().record_presence(situation=situation, presence_type=presence_type, posture=posture, presence=presence, confidence=confidence, energy=energy, openness=openness, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/posture_presence_coach/stats")
def posture_presence_coach_stats():
    return get_posture_presence_coach().get_presence_stats()

@router.get("/posture_presence_coach/score")
def posture_presence_coach_score():
    return {"presence_score": get_posture_presence_coach().get_presence_score()}
'''

# Insert imports before the last import block
last_import = api.rfind("from core.")
last_import_end = api.find("\n", api.find("\n", last_import) + 1)
if api_imports.strip() not in api:
    api = api[:last_import_end] + "\n" + api_imports + api[last_import_end:]

# Insert routes before the last line
if "body_awareness_trainer/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch53 = """
        # Batch 53 — Somatic Intelligence
        from core.body_awareness_trainer import get_body_awareness_trainer
        from core.breath_work_coach import get_breath_work_coach
        from core.movement_intelligence import get_movement_intelligence
        from core.posture_presence_coach import get_posture_presence_coach
        self.body_awareness_trainer = get_body_awareness_trainer()
        self.breath_work_coach = get_breath_work_coach()
        self.movement_intelligence = get_movement_intelligence()
        self.posture_presence_coach = get_posture_presence_coach()
"""

if "body_awareness_trainer" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch53 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch53_brief = """
        # Batch 53 — Somatic Intelligence
        try:
            from core.body_awareness_trainer import get_body_awareness_trainer
            report["body_awareness_trainer"] = get_body_awareness_trainer().get_body_stats()
        except Exception as e:
            report["body_awareness_trainer"] = {"error": str(e)}
        try:
            from core.breath_work_coach import get_breath_work_coach
            report["breath_work_coach"] = get_breath_work_coach().get_breath_stats()
        except Exception as e:
            report["breath_work_coach"] = {"error": str(e)}
        try:
            from core.movement_intelligence import get_movement_intelligence
            report["movement_intelligence"] = get_movement_intelligence().get_movement_stats()
        except Exception as e:
            report["movement_intelligence"] = {"error": str(e)}
        try:
            from core.posture_presence_coach import get_posture_presence_coach
            report["posture_presence_coach"] = get_posture_presence_coach().get_presence_stats()
        except Exception as e:
            report["posture_presence_coach"] = {"error": str(e)}
"""

if "body_awareness_trainer" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch53_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch53_pulse = """
        # Batch 53 — Somatic Intelligence
        try:
            from core.body_awareness_trainer import get_body_awareness_trainer
            report["body_awareness_trainer_pulse"] = get_body_awareness_trainer().get_body_score()
        except Exception:
            pass
        try:
            from core.breath_work_coach import get_breath_work_coach
            report["breath_work_coach_pulse"] = get_breath_work_coach().get_breath_score()
        except Exception:
            pass
        try:
            from core.movement_intelligence import get_movement_intelligence
            report["movement_intelligence_pulse"] = get_movement_intelligence().get_movement_score()
        except Exception:
            pass
        try:
            from core.posture_presence_coach import get_posture_presence_coach
            report["posture_presence_coach_pulse"] = get_posture_presence_coach().get_presence_score()
        except Exception:
            pass
"""

if "body_awareness_trainer_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch53_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 53 wiring complete.")
