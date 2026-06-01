# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.intimacy_coach import get_intimacy_coach
from core.sensory_awareness_trainer import get_sensory_awareness_trainer
from core.passion_cultivator import get_passion_cultivator
from core.deep_connection_coach import get_deep_connection_coach
"""

api_routes = '''

@router.post("/intimacy_coach/record")
def intimacy_coach_record(moment: str = "", intimacy_type: str = "", depth: float = 0.0, safety: float = 0.0, reciprocity: float = 0.0, satisfaction: float = 0.0, repair: float = 0.0, notes: str = ""):
    entry = get_intimacy_coach().record_intimacy(moment=moment, intimacy_type=intimacy_type, depth=depth, safety=safety, reciprocity=reciprocity, satisfaction=satisfaction, repair=repair, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/intimacy_coach/stats")
def intimacy_coach_stats():
    return get_intimacy_coach().get_intimacy_stats()

@router.get("/intimacy_coach/score")
def intimacy_coach_score():
    return {"intimacy_score": get_intimacy_coach().get_intimacy_score()}

@router.post("/sensory_awareness_trainer/record")
def sensory_awareness_trainer_record(experience: str = "", sensory_type: str = "", vividness: float = 0.0, presence: float = 0.0, pleasure: float = 0.0, curiosity: float = 0.0, notes: str = ""):
    entry = get_sensory_awareness_trainer().record_sensory(experience=experience, sensory_type=sensory_type, vividness=vividness, presence=presence, pleasure=pleasure, curiosity=curiosity, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/sensory_awareness_trainer/stats")
def sensory_awareness_trainer_stats():
    return get_sensory_awareness_trainer().get_sensory_stats()

@router.get("/sensory_awareness_trainer/score")
def sensory_awareness_trainer_score():
    return {"sensory_score": get_sensory_awareness_trainer().get_sensory_score()}

@router.post("/passion_cultivator/record")
def passion_cultivator_record(activity: str = "", passion_type: str = "", intensity: float = 0.0, duration: float = 0.0, satisfaction: float = 0.0, integration: float = 0.0, vitality: float = 0.0, notes: str = ""):
    entry = get_passion_cultivator().record_passion(activity=activity, passion_type=passion_type, intensity=intensity, duration=duration, satisfaction=satisfaction, integration=integration, vitality=vitality, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/passion_cultivator/stats")
def passion_cultivator_stats():
    return get_passion_cultivator().get_passion_stats()

@router.get("/passion_cultivator/score")
def passion_cultivator_score():
    return {"passion_score": get_passion_cultivator().get_passion_score()}

@router.post("/deep_connection_coach/record")
def deep_connection_coach_record(person: str = "", connection_type: str = "", depth: float = 0.0, authenticity: float = 0.0, reciprocity: float = 0.0, meaning: float = 0.0, maintenance: float = 0.0, notes: str = ""):
    entry = get_deep_connection_coach().record_connection(person=person, connection_type=connection_type, depth=depth, authenticity=authenticity, reciprocity=reciprocity, meaning=meaning, maintenance=maintenance, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/deep_connection_coach/stats")
def deep_connection_coach_stats():
    return get_deep_connection_coach().get_connection_stats()

@router.get("/deep_connection_coach/score")
def deep_connection_coach_score():
    return {"connection_score": get_deep_connection_coach().get_connection_score()}
'''

# Insert imports before the last import block
last_import = api.rfind("from core.")
last_import_end = api.find("\n", api.find("\n", last_import) + 1)
if api_imports.strip() not in api:
    api = api[:last_import_end] + "\n" + api_imports + api[last_import_end:]

# Insert routes before the last line
if "intimacy_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch54 = """
        # Batch 54 — Intimacy & Connection
        from core.intimacy_coach import get_intimacy_coach
        from core.sensory_awareness_trainer import get_sensory_awareness_trainer
        from core.passion_cultivator import get_passion_cultivator
        from core.deep_connection_coach import get_deep_connection_coach
        self.intimacy_coach = get_intimacy_coach()
        self.sensory_awareness_trainer = get_sensory_awareness_trainer()
        self.passion_cultivator = get_passion_cultivator()
        self.deep_connection_coach = get_deep_connection_coach()
"""

if "intimacy_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch54 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch54_brief = """
        # Batch 54 — Intimacy & Connection
        try:
            from core.intimacy_coach import get_intimacy_coach
            report["intimacy_coach"] = get_intimacy_coach().get_intimacy_stats()
        except Exception as e:
            report["intimacy_coach"] = {"error": str(e)}
        try:
            from core.sensory_awareness_trainer import get_sensory_awareness_trainer
            report["sensory_awareness_trainer"] = get_sensory_awareness_trainer().get_sensory_stats()
        except Exception as e:
            report["sensory_awareness_trainer"] = {"error": str(e)}
        try:
            from core.passion_cultivator import get_passion_cultivator
            report["passion_cultivator"] = get_passion_cultivator().get_passion_stats()
        except Exception as e:
            report["passion_cultivator"] = {"error": str(e)}
        try:
            from core.deep_connection_coach import get_deep_connection_coach
            report["deep_connection_coach"] = get_deep_connection_coach().get_connection_stats()
        except Exception as e:
            report["deep_connection_coach"] = {"error": str(e)}
"""

if "intimacy_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch54_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch54_pulse = """
        # Batch 54 — Intimacy & Connection
        try:
            from core.intimacy_coach import get_intimacy_coach
            report["intimacy_coach_pulse"] = get_intimacy_coach().get_intimacy_score()
        except Exception:
            pass
        try:
            from core.sensory_awareness_trainer import get_sensory_awareness_trainer
            report["sensory_awareness_trainer_pulse"] = get_sensory_awareness_trainer().get_sensory_score()
        except Exception:
            pass
        try:
            from core.passion_cultivator import get_passion_cultivator
            report["passion_cultivator_pulse"] = get_passion_cultivator().get_passion_score()
        except Exception:
            pass
        try:
            from core.deep_connection_coach import get_deep_connection_coach
            report["deep_connection_coach_pulse"] = get_deep_connection_coach().get_connection_score()
        except Exception:
            pass
"""

if "intimacy_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch54_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 54 wiring complete.")
