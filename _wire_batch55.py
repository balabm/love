# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.music_mood_regulator import get_music_mood_regulator
from core.sound_healing_guide import get_sound_healing_guide
from core.playlist_therapist import get_playlist_therapist
from core.rhythmic_living_coach import get_rhythmic_living_coach
"""

api_routes = '''

@router.post("/music_mood_regulator/record")
def music_mood_regulator_record(song: str = "", music_type: str = "", mood_before: float = 0.0, mood_after: float = 0.0, regulation: float = 0.0, intention: float = 0.0, duration: float = 0.0, notes: str = ""):
    entry = get_music_mood_regulator().record_music(song=song, music_type=music_type, mood_before=mood_before, mood_after=mood_after, regulation=regulation, intention=intention, duration=duration, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/music_mood_regulator/stats")
def music_mood_regulator_stats():
    return get_music_mood_regulator().get_music_stats()

@router.get("/music_mood_regulator/score")
def music_mood_regulator_score():
    return {"music_score": get_music_mood_regulator().get_music_score()}

@router.post("/sound_healing_guide/record")
def sound_healing_guide_record(sound: str = "", sound_type: str = "", relaxation: float = 0.0, clarity: float = 0.0, restoration: float = 0.0, healing: float = 0.0, intention: float = 0.0, notes: str = ""):
    entry = get_sound_healing_guide().record_sound(sound=sound, sound_type=sound_type, relaxation=relaxation, clarity=clarity, restoration=restoration, healing=healing, intention=intention, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/sound_healing_guide/stats")
def sound_healing_guide_stats():
    return get_sound_healing_guide().get_sound_stats()

@router.get("/sound_healing_guide/score")
def sound_healing_guide_score():
    return {"sound_score": get_sound_healing_guide().get_sound_score()}

@router.post("/playlist_therapist/record")
def playlist_therapist_record(song: str = "", playlist_type: str = "", match: float = 0.0, transition: float = 0.0, arc: float = 0.0, therapeutic: float = 0.0, notes: str = ""):
    entry = get_playlist_therapist().record_playlist(song=song, playlist_type=playlist_type, match=match, transition=transition, arc=arc, therapeutic=therapeutic, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/playlist_therapist/stats")
def playlist_therapist_stats():
    return get_playlist_therapist().get_playlist_stats()

@router.get("/playlist_therapist/score")
def playlist_therapist_score():
    return {"playlist_score": get_playlist_therapist().get_playlist_score()}

@router.post("/rhythmic_living_coach/record")
def rhythmic_living_coach_record(period: str = "", rhythm_type: str = "", alignment: float = 0.0, energy: float = 0.0, sustainability: float = 0.0, flow: float = 0.0, rest: float = 0.0, notes: str = ""):
    entry = get_rhythmic_living_coach().record_rhythm(period=period, rhythm_type=rhythm_type, alignment=alignment, energy=energy, sustainability=sustainability, flow=flow, rest=rest, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/rhythmic_living_coach/stats")
def rhythmic_living_coach_stats():
    return get_rhythmic_living_coach().get_rhythm_stats()

@router.get("/rhythmic_living_coach/score")
def rhythmic_living_coach_score():
    return {"rhythm_score": get_rhythmic_living_coach().get_rhythm_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "music_mood_regulator/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch55 = """
        # Batch 55 — Music & Sound Intelligence
        from core.music_mood_regulator import get_music_mood_regulator
        from core.sound_healing_guide import get_sound_healing_guide
        from core.playlist_therapist import get_playlist_therapist
        from core.rhythmic_living_coach import get_rhythmic_living_coach
        self.music_mood_regulator = get_music_mood_regulator()
        self.sound_healing_guide = get_sound_healing_guide()
        self.playlist_therapist = get_playlist_therapist()
        self.rhythmic_living_coach = get_rhythmic_living_coach()
"""

if "music_mood_regulator" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch55 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch55_brief = """
        # Batch 55 — Music & Sound Intelligence
        try:
            from core.music_mood_regulator import get_music_mood_regulator
            report["music_mood_regulator"] = get_music_mood_regulator().get_music_stats()
        except Exception as e:
            report["music_mood_regulator"] = {"error": str(e)}
        try:
            from core.sound_healing_guide import get_sound_healing_guide
            report["sound_healing_guide"] = get_sound_healing_guide().get_sound_stats()
        except Exception as e:
            report["sound_healing_guide"] = {"error": str(e)}
        try:
            from core.playlist_therapist import get_playlist_therapist
            report["playlist_therapist"] = get_playlist_therapist().get_playlist_stats()
        except Exception as e:
            report["playlist_therapist"] = {"error": str(e)}
        try:
            from core.rhythmic_living_coach import get_rhythmic_living_coach
            report["rhythmic_living_coach"] = get_rhythmic_living_coach().get_rhythm_stats()
        except Exception as e:
            report["rhythmic_living_coach"] = {"error": str(e)}
"""

if "music_mood_regulator" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch55_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch55_pulse = """
        # Batch 55 — Music & Sound Intelligence
        try:
            from core.music_mood_regulator import get_music_mood_regulator
            report["music_mood_regulator_pulse"] = get_music_mood_regulator().get_music_score()
        except Exception:
            pass
        try:
            from core.sound_healing_guide import get_sound_healing_guide
            report["sound_healing_guide_pulse"] = get_sound_healing_guide().get_sound_score()
        except Exception:
            pass
        try:
            from core.playlist_therapist import get_playlist_therapist
            report["playlist_therapist_pulse"] = get_playlist_therapist().get_playlist_score()
        except Exception:
            pass
        try:
            from core.rhythmic_living_coach import get_rhythmic_living_coach
            report["rhythmic_living_coach_pulse"] = get_rhythmic_living_coach().get_rhythm_score()
        except Exception:
            pass
"""

if "music_mood_regulator_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch55_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 55 wiring complete.")
