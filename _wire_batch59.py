# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.voice_presence_coach import get_voice_presence_coach
from core.stage_confidence_builder import get_stage_confidence_builder
from core.audience_connection_trainer import get_audience_connection_trainer
from core.speech_craft_coach import get_speech_craft_coach
"""

api_routes = '''

@router.post("/voice_presence_coach/record")
def voice_presence_coach_record(context: str = "", voice_type: str = "", presence: float = 0.0, power: float = 0.0, clarity: float = 0.0, warmth: float = 0.0, authenticity: float = 0.0, breath: float = 0.0, notes: str = ""):
    entry = get_voice_presence_coach().record_voice(context=context, voice_type=voice_type, presence=presence, power=power, clarity=clarity, warmth=warmth, authenticity=authenticity, breath=breath, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/voice_presence_coach/stats")
def voice_presence_coach_stats():
    return get_voice_presence_coach().get_voice_stats()

@router.get("/voice_presence_coach/score")
def voice_presence_coach_score():
    return {"voice_score": get_voice_presence_coach().get_voice_score()}

@router.post("/stage_confidence_builder/record")
def stage_confidence_builder_record(event: str = "", stage_type: str = "", confidence: float = 0.0, preparation: float = 0.0, delivery: float = 0.0, recovery: float = 0.0, impact: float = 0.0, fear: float = 0.0, notes: str = ""):
    entry = get_stage_confidence_builder().record_stage(event=event, stage_type=stage_type, confidence=confidence, preparation=preparation, delivery=delivery, recovery=recovery, impact=impact, fear=fear, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/stage_confidence_builder/stats")
def stage_confidence_builder_stats():
    return get_stage_confidence_builder().get_stage_stats()

@router.get("/stage_confidence_builder/score")
def stage_confidence_builder_score():
    return {"stage_score": get_stage_confidence_builder().get_stage_score()}

@router.post("/audience_connection_trainer/record")
def audience_connection_trainer_record(moment: str = "", connection_type: str = "", engagement: float = 0.0, empathy: float = 0.0, responsiveness: float = 0.0, reciprocity: float = 0.0, energy: float = 0.0, adaptation: float = 0.0, notes: str = ""):
    entry = get_audience_connection_trainer().record_connection(moment=moment, connection_type=connection_type, engagement=engagement, empathy=empathy, responsiveness=responsiveness, reciprocity=reciprocity, energy=energy, adaptation=adaptation, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/audience_connection_trainer/stats")
def audience_connection_trainer_stats():
    return get_audience_connection_trainer().get_connection_stats()

@router.get("/audience_connection_trainer/score")
def audience_connection_trainer_score():
    return {"connection_score": get_audience_connection_trainer().get_connection_score()}

@router.post("/speech_craft_coach/record")
def speech_craft_coach_record(section: str = "", speech_type: str = "", structure: float = 0.0, clarity: float = 0.0, persuasion: float = 0.0, memorability: float = 0.0, impact: float = 0.0, intention: float = 0.0, notes: str = ""):
    entry = get_speech_craft_coach().record_speech(section=section, speech_type=speech_type, structure=structure, clarity=clarity, persuasion=persuasion, memorability=memorability, impact=impact, intention=intention, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/speech_craft_coach/stats")
def speech_craft_coach_stats():
    return get_speech_craft_coach().get_speech_stats()

@router.get("/speech_craft_coach/score")
def speech_craft_coach_score():
    return {"speech_score": get_speech_craft_coach().get_speech_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "voice_presence_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch59 = """
        # Batch 59 — Public Speaking & Performance Intelligence
        from core.voice_presence_coach import get_voice_presence_coach
        from core.stage_confidence_builder import get_stage_confidence_builder
        from core.audience_connection_trainer import get_audience_connection_trainer
        from core.speech_craft_coach import get_speech_craft_coach
        self.voice_presence_coach = get_voice_presence_coach()
        self.stage_confidence_builder = get_stage_confidence_builder()
        self.audience_connection_trainer = get_audience_connection_trainer()
        self.speech_craft_coach = get_speech_craft_coach()
"""

if "voice_presence_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch59 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch59_brief = """
        # Batch 59 — Public Speaking & Performance Intelligence
        try:
            from core.voice_presence_coach import get_voice_presence_coach
            report["voice_presence_coach"] = get_voice_presence_coach().get_voice_stats()
        except Exception as e:
            report["voice_presence_coach"] = {"error": str(e)}
        try:
            from core.stage_confidence_builder import get_stage_confidence_builder
            report["stage_confidence_builder"] = get_stage_confidence_builder().get_stage_stats()
        except Exception as e:
            report["stage_confidence_builder"] = {"error": str(e)}
        try:
            from core.audience_connection_trainer import get_audience_connection_trainer
            report["audience_connection_trainer"] = get_audience_connection_trainer().get_connection_stats()
        except Exception as e:
            report["audience_connection_trainer"] = {"error": str(e)}
        try:
            from core.speech_craft_coach import get_speech_craft_coach
            report["speech_craft_coach"] = get_speech_craft_coach().get_speech_stats()
        except Exception as e:
            report["speech_craft_coach"] = {"error": str(e)}
"""

if "voice_presence_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch59_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch59_pulse = """
        # Batch 59 — Public Speaking & Performance Intelligence
        try:
            from core.voice_presence_coach import get_voice_presence_coach
            report["voice_presence_coach_pulse"] = get_voice_presence_coach().get_voice_score()
        except Exception:
            pass
        try:
            from core.stage_confidence_builder import get_stage_confidence_builder
            report["stage_confidence_builder_pulse"] = get_stage_confidence_builder().get_stage_score()
        except Exception:
            pass
        try:
            from core.audience_connection_trainer import get_audience_connection_trainer
            report["audience_connection_trainer_pulse"] = get_audience_connection_trainer().get_connection_score()
        except Exception:
            pass
        try:
            from core.speech_craft_coach import get_speech_craft_coach
            report["speech_craft_coach_pulse"] = get_speech_craft_coach().get_speech_score()
        except Exception:
            pass
"""

if "voice_presence_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch59_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 59 wiring complete.")
