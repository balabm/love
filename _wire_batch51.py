# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.cognitive_bias_detector import get_cognitive_bias_detector
from core.mental_model_trainer import get_mental_model_trainer
from core.first_principles_thinker import get_first_principles_thinker
from core.systems_thinking_coach import get_systems_thinking_coach
"""

api_routes = '''

@router.post("/cognitive_bias_detector/record")
def cognitive_bias_detector_record(situation: str = "", bias_type: str = "", detection: float = 0.0, severity: float = 0.0, correction: float = 0.0, emotion_level: float = 0.0, outcome: float = 0.0, notes: str = ""):
    entry = get_cognitive_bias_detector().record_bias(situation=situation, bias_type=bias_type, detection=detection, severity=severity, correction=correction, emotion_level=emotion_level, outcome=outcome, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/cognitive_bias_detector/stats")
def cognitive_bias_detector_stats():
    return get_cognitive_bias_detector().get_bias_stats()

@router.get("/cognitive_bias_detector/score")
def cognitive_bias_detector_score():
    return {"bias_score": get_cognitive_bias_detector().get_bias_score()}

@router.post("/mental_model_trainer/record")
def mental_model_trainer_record(situation: str = "", model_type: str = "", application: float = 0.0, effectiveness: float = 0.0, integration: float = 0.0, cross_domain: float = 0.0, outcome: float = 0.0, notes: str = ""):
    entry = get_mental_model_trainer().record_model(situation=situation, model_type=model_type, application=application, effectiveness=effectiveness, integration=integration, cross_domain=cross_domain, outcome=outcome, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/mental_model_trainer/stats")
def mental_model_trainer_stats():
    return get_mental_model_trainer().get_model_stats()

@router.get("/mental_model_trainer/score")
def mental_model_trainer_score():
    return {"model_score": get_mental_model_trainer().get_model_score()}

@router.post("/first_principles_thinker/record")
def first_principles_thinker_record(problem: str = "", thinking_type: str = "", depth: float = 0.0, clarity: float = 0.0, application: float = 0.0, assumption_challenged: float = 0.0, novelty: float = 0.0, notes: str = ""):
    entry = get_first_principles_thinker().record_thinking(problem=problem, thinking_type=thinking_type, depth=depth, clarity=clarity, application=application, assumption_challenged=assumption_challenged, novelty=novelty, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/first_principles_thinker/stats")
def first_principles_thinker_stats():
    return get_first_principles_thinker().get_thinking_stats()

@router.get("/first_principles_thinker/score")
def first_principles_thinker_score():
    return {"thinking_score": get_first_principles_thinker().get_thinking_score()}

@router.post("/systems_thinking_coach/record")
def systems_thinking_coach_record(situation: str = "", systems_type: str = "", interconnection: float = 0.0, perspective: float = 0.0, intervention: float = 0.0, feedback_seen: float = 0.0, leverage_found: float = 0.0, notes: str = ""):
    entry = get_systems_thinking_coach().record_systems(situation=situation, systems_type=systems_type, interconnection=interconnection, perspective=perspective, intervention=intervention, feedback_seen=feedback_seen, leverage_found=leverage_found, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/systems_thinking_coach/stats")
def systems_thinking_coach_stats():
    return get_systems_thinking_coach().get_systems_stats()

@router.get("/systems_thinking_coach/score")
def systems_thinking_coach_score():
    return {"systems_score": get_systems_thinking_coach().get_systems_score()}
'''

# Insert imports before the last import block
last_import = api.rfind("from core.")
last_import_end = api.find("\n", api.find("\n", last_import) + 1)
if api_imports.strip() not in api:
    api = api[:last_import_end] + "\n" + api_imports + api[last_import_end:]

# Insert routes before the last line
if "cognitive_bias_detector/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch51 = """
        # Batch 51 — Cognitive Mastery
        from core.cognitive_bias_detector import get_cognitive_bias_detector
        from core.mental_model_trainer import get_mental_model_trainer
        from core.first_principles_thinker import get_first_principles_thinker
        from core.systems_thinking_coach import get_systems_thinking_coach
        self.cognitive_bias_detector = get_cognitive_bias_detector()
        self.mental_model_trainer = get_mental_model_trainer()
        self.first_principles_thinker = get_first_principles_thinker()
        self.systems_thinking_coach = get_systems_thinking_coach()
"""

if "cognitive_bias_detector" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch51 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch51_brief = """
        # Batch 51 — Cognitive Mastery
        try:
            from core.cognitive_bias_detector import get_cognitive_bias_detector
            report["cognitive_bias_detector"] = get_cognitive_bias_detector().get_bias_stats()
        except Exception as e:
            report["cognitive_bias_detector"] = {"error": str(e)}
        try:
            from core.mental_model_trainer import get_mental_model_trainer
            report["mental_model_trainer"] = get_mental_model_trainer().get_model_stats()
        except Exception as e:
            report["mental_model_trainer"] = {"error": str(e)}
        try:
            from core.first_principles_thinker import get_first_principles_thinker
            report["first_principles_thinker"] = get_first_principles_thinker().get_thinking_stats()
        except Exception as e:
            report["first_principles_thinker"] = {"error": str(e)}
        try:
            from core.systems_thinking_coach import get_systems_thinking_coach
            report["systems_thinking_coach"] = get_systems_thinking_coach().get_systems_stats()
        except Exception as e:
            report["systems_thinking_coach"] = {"error": str(e)}
"""

if "cognitive_bias_detector" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch51_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch51_pulse = """
        # Batch 51 — Cognitive Mastery
        try:
            from core.cognitive_bias_detector import get_cognitive_bias_detector
            report["cognitive_bias_detector_pulse"] = get_cognitive_bias_detector().get_bias_score()
        except Exception:
            pass
        try:
            from core.mental_model_trainer import get_mental_model_trainer
            report["mental_model_trainer_pulse"] = get_mental_model_trainer().get_model_score()
        except Exception:
            pass
        try:
            from core.first_principles_thinker import get_first_principles_thinker
            report["first_principles_thinker_pulse"] = get_first_principles_thinker().get_thinking_score()
        except Exception:
            pass
        try:
            from core.systems_thinking_coach import get_systems_thinking_coach
            report["systems_thinking_coach_pulse"] = get_systems_thinking_coach().get_systems_score()
        except Exception:
            pass
"""

if "cognitive_bias_detector_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch51_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 51 wiring complete.")
