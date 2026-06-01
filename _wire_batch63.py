# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.language_immersion_coach import get_language_immersion_coach
from core.cross_cultural_bridge_builder import get_cross_cultural_bridge_builder
from core.conversation_fluency_trainer import get_conversation_fluency_trainer
from core.vocabulary_growth_coach import get_vocabulary_growth_coach
"""

api_routes = '''

@router.post("/language_immersion_coach/record")
def language_immersion_coach_record(activity: str = "", immersion_type: str = "", exposure: float = 0.0, comprehension: float = 0.0, courage: float = 0.0, consistency: float = 0.0, joy: float = 0.0, authenticity: float = 0.0, notes: str = ""):
    entry = get_language_immersion_coach().record_immersion(activity=activity, immersion_type=immersion_type, exposure=exposure, comprehension=comprehension, courage=courage, consistency=consistency, joy=joy, authenticity=authenticity, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/language_immersion_coach/stats")
def language_immersion_coach_stats():
    return get_language_immersion_coach().get_immersion_stats()

@router.get("/language_immersion_coach/score")
def language_immersion_coach_score():
    return {"immersion_score": get_language_immersion_coach().get_immersion_score()}

@router.post("/cross_cultural_bridge_builder/record")
def cross_cultural_bridge_builder_record(situation: str = "", interaction_type: str = "", curiosity: float = 0.0, respect: float = 0.0, empathy: float = 0.0, adaptability: float = 0.0, openness: float = 0.0, humility: float = 0.0, notes: str = ""):
    entry = get_cross_cultural_bridge_builder().record_interaction(situation=situation, interaction_type=interaction_type, curiosity=curiosity, respect=respect, empathy=empathy, adaptability=adaptability, openness=openness, humility=humility, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/cross_cultural_bridge_builder/stats")
def cross_cultural_bridge_builder_stats():
    return get_cross_cultural_bridge_builder().get_interaction_stats()

@router.get("/cross_cultural_bridge_builder/score")
def cross_cultural_bridge_builder_score():
    return {"interaction_score": get_cross_cultural_bridge_builder().get_interaction_score()}

@router.post("/conversation_fluency_trainer/record")
def conversation_fluency_trainer_record(topic: str = "", conversation_type: str = "", fluency: float = 0.0, vocabulary: float = 0.0, grammar: float = 0.0, listening: float = 0.0, confidence: float = 0.0, connection: float = 0.0, notes: str = ""):
    entry = get_conversation_fluency_trainer().record_conversation(topic=topic, conversation_type=conversation_type, fluency=fluency, vocabulary=vocabulary, grammar=grammar, listening=listening, confidence=confidence, connection=connection, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/conversation_fluency_trainer/stats")
def conversation_fluency_trainer_stats():
    return get_conversation_fluency_trainer().get_conversation_stats()

@router.get("/conversation_fluency_trainer/score")
def conversation_fluency_trainer_score():
    return {"conversation_score": get_conversation_fluency_trainer().get_conversation_score()}

@router.post("/vocabulary_growth_coach/record")
def vocabulary_growth_coach_record(word: str = "", vocabulary_type: str = "", retention: float = 0.0, usage: float = 0.0, context: float = 0.0, depth: float = 0.0, joy: float = 0.0, connection: float = 0.0, notes: str = ""):
    entry = get_vocabulary_growth_coach().record_vocabulary(word=word, vocabulary_type=vocabulary_type, retention=retention, usage=usage, context=context, depth=depth, joy=joy, connection=connection, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/vocabulary_growth_coach/stats")
def vocabulary_growth_coach_stats():
    return get_vocabulary_growth_coach().get_vocabulary_stats()

@router.get("/vocabulary_growth_coach/score")
def vocabulary_growth_coach_score():
    return {"vocabulary_score": get_vocabulary_growth_coach().get_vocabulary_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "language_immersion_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch63 = """
        # Batch 63 — Language & Cultural Intelligence
        from core.language_immersion_coach import get_language_immersion_coach
        from core.cross_cultural_bridge_builder import get_cross_cultural_bridge_builder
        from core.conversation_fluency_trainer import get_conversation_fluency_trainer
        from core.vocabulary_growth_coach import get_vocabulary_growth_coach
        self.language_immersion_coach = get_language_immersion_coach()
        self.cross_cultural_bridge_builder = get_cross_cultural_bridge_builder()
        self.conversation_fluency_trainer = get_conversation_fluency_trainer()
        self.vocabulary_growth_coach = get_vocabulary_growth_coach()
"""

if "language_immersion_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch63 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch63_brief = """
        # Batch 63 — Language & Cultural Intelligence
        try:
            from core.language_immersion_coach import get_language_immersion_coach
            report["language_immersion_coach"] = get_language_immersion_coach().get_immersion_stats()
        except Exception as e:
            report["language_immersion_coach"] = {"error": str(e)}
        try:
            from core.cross_cultural_bridge_builder import get_cross_cultural_bridge_builder
            report["cross_cultural_bridge_builder"] = get_cross_cultural_bridge_builder().get_interaction_stats()
        except Exception as e:
            report["cross_cultural_bridge_builder"] = {"error": str(e)}
        try:
            from core.conversation_fluency_trainer import get_conversation_fluency_trainer
            report["conversation_fluency_trainer"] = get_conversation_fluency_trainer().get_conversation_stats()
        except Exception as e:
            report["conversation_fluency_trainer"] = {"error": str(e)}
        try:
            from core.vocabulary_growth_coach import get_vocabulary_growth_coach
            report["vocabulary_growth_coach"] = get_vocabulary_growth_coach().get_vocabulary_stats()
        except Exception as e:
            report["vocabulary_growth_coach"] = {"error": str(e)}
"""

if "language_immersion_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch63_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch63_pulse = """
        # Batch 63 — Language & Cultural Intelligence
        try:
            from core.language_immersion_coach import get_language_immersion_coach
            report["language_immersion_coach_pulse"] = get_language_immersion_coach().get_immersion_score()
        except Exception:
            pass
        try:
            from core.cross_cultural_bridge_builder import get_cross_cultural_bridge_builder
            report["cross_cultural_bridge_builder_pulse"] = get_cross_cultural_bridge_builder().get_interaction_score()
        except Exception:
            pass
        try:
            from core.conversation_fluency_trainer import get_conversation_fluency_trainer
            report["conversation_fluency_trainer_pulse"] = get_conversation_fluency_trainer().get_conversation_score()
        except Exception:
            pass
        try:
            from core.vocabulary_growth_coach import get_vocabulary_growth_coach
            report["vocabulary_growth_coach_pulse"] = get_vocabulary_growth_coach().get_vocabulary_score()
        except Exception:
            pass
"""

if "language_immersion_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch63_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 63 wiring complete.")
