# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.photo_memory_keeper import get_photo_memory_keeper
from core.visual_storytelling_coach import get_visual_storytelling_coach
from core.mindful_photography_guide import get_mindful_photography_guide
from core.memory_curation_coach import get_memory_curation_coach
"""

api_routes = '''

@router.post("/photo_memory_keeper/record")
def photo_memory_keeper_record(photo: str = "", photo_type: str = "", intention: float = 0.0, quality: float = 0.0, emotion: float = 0.0, story: float = 0.0, preservation: float = 0.0, curation: float = 0.0, notes: str = ""):
    entry = get_photo_memory_keeper().record_photo(photo=photo, photo_type=photo_type, intention=intention, quality=quality, emotion=emotion, story=story, preservation=preservation, curation=curation, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/photo_memory_keeper/stats")
def photo_memory_keeper_stats():
    return get_photo_memory_keeper().get_photo_stats()

@router.get("/photo_memory_keeper/score")
def photo_memory_keeper_score():
    return {"photo_score": get_photo_memory_keeper().get_photo_score()}

@router.post("/visual_storytelling_coach/record")
def visual_storytelling_coach_record(series: str = "", story_type: str = "", narrative: float = 0.0, composition: float = 0.0, emotion: float = 0.0, continuity: float = 0.0, impact: float = 0.0, intention: float = 0.0, notes: str = ""):
    entry = get_visual_storytelling_coach().record_story(series=series, story_type=story_type, narrative=narrative, composition=composition, emotion=emotion, continuity=continuity, impact=impact, intention=intention, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/visual_storytelling_coach/stats")
def visual_storytelling_coach_stats():
    return get_visual_storytelling_coach().get_story_stats()

@router.get("/visual_storytelling_coach/score")
def visual_storytelling_coach_score():
    return {"story_score": get_visual_storytelling_coach().get_story_score()}

@router.post("/mindful_photography_guide/record")
def mindful_photography_guide_record(session: str = "", practice_type: str = "", attention: float = 0.0, patience: float = 0.0, stillness: float = 0.0, seeing: float = 0.0, presence: float = 0.0, surrender: float = 0.0, notes: str = ""):
    entry = get_mindful_photography_guide().record_practice(session=session, practice_type=practice_type, attention=attention, patience=patience, stillness=stillness, seeing=seeing, presence=presence, surrender=surrender, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/mindful_photography_guide/stats")
def mindful_photography_guide_stats():
    return get_mindful_photography_guide().get_practice_stats()

@router.get("/mindful_photography_guide/score")
def mindful_photography_guide_score():
    return {"practice_score": get_mindful_photography_guide().get_practice_score()}

@router.post("/memory_curation_coach/record")
def memory_curation_coach_record(moment: str = "", curation_type: str = "", intention: float = 0.0, selectivity: float = 0.0, care: float = 0.0, meaning: float = 0.0, preservation: float = 0.0, ritual: float = 0.0, notes: str = ""):
    entry = get_memory_curation_coach().record_curation(moment=moment, curation_type=curation_type, intention=intention, selectivity=selectivity, care=care, meaning=meaning, preservation=preservation, ritual=ritual, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/memory_curation_coach/stats")
def memory_curation_coach_stats():
    return get_memory_curation_coach().get_curation_stats()

@router.get("/memory_curation_coach/score")
def memory_curation_coach_score():
    return {"curation_score": get_memory_curation_coach().get_curation_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "photo_memory_keeper/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch60 = """
        # Batch 60 — Photography & Visual Memory Intelligence
        from core.photo_memory_keeper import get_photo_memory_keeper
        from core.visual_storytelling_coach import get_visual_storytelling_coach
        from core.mindful_photography_guide import get_mindful_photography_guide
        from core.memory_curation_coach import get_memory_curation_coach
        self.photo_memory_keeper = get_photo_memory_keeper()
        self.visual_storytelling_coach = get_visual_storytelling_coach()
        self.mindful_photography_guide = get_mindful_photography_guide()
        self.memory_curation_coach = get_memory_curation_coach()
"""

if "photo_memory_keeper" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch60 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch60_brief = """
        # Batch 60 — Photography & Visual Memory Intelligence
        try:
            from core.photo_memory_keeper import get_photo_memory_keeper
            report["photo_memory_keeper"] = get_photo_memory_keeper().get_photo_stats()
        except Exception as e:
            report["photo_memory_keeper"] = {"error": str(e)}
        try:
            from core.visual_storytelling_coach import get_visual_storytelling_coach
            report["visual_storytelling_coach"] = get_visual_storytelling_coach().get_story_stats()
        except Exception as e:
            report["visual_storytelling_coach"] = {"error": str(e)}
        try:
            from core.mindful_photography_guide import get_mindful_photography_guide
            report["mindful_photography_guide"] = get_mindful_photography_guide().get_practice_stats()
        except Exception as e:
            report["mindful_photography_guide"] = {"error": str(e)}
        try:
            from core.memory_curation_coach import get_memory_curation_coach
            report["memory_curation_coach"] = get_memory_curation_coach().get_curation_stats()
        except Exception as e:
            report["memory_curation_coach"] = {"error": str(e)}
"""

if "photo_memory_keeper" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch60_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch60_pulse = """
        # Batch 60 — Photography & Visual Memory Intelligence
        try:
            from core.photo_memory_keeper import get_photo_memory_keeper
            report["photo_memory_keeper_pulse"] = get_photo_memory_keeper().get_photo_score()
        except Exception:
            pass
        try:
            from core.visual_storytelling_coach import get_visual_storytelling_coach
            report["visual_storytelling_coach_pulse"] = get_visual_storytelling_coach().get_story_score()
        except Exception:
            pass
        try:
            from core.mindful_photography_guide import get_mindful_photography_guide
            report["mindful_photography_guide_pulse"] = get_mindful_photography_guide().get_practice_score()
        except Exception:
            pass
        try:
            from core.memory_curation_coach import get_memory_curation_coach
            report["memory_curation_coach_pulse"] = get_memory_curation_coach().get_curation_score()
        except Exception:
            pass
"""

if "photo_memory_keeper_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch60_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 60 wiring complete.")
