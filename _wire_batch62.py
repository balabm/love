# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.style_expression_coach import get_style_expression_coach
from core.wardrobe_mindfulness_guide import get_wardrobe_mindfulness_guide
from core.personal_brand_designer import get_personal_brand_designer
from core.dress_for_joy_coach import get_dress_for_joy_coach
"""

api_routes = '''

@router.post("/style_expression_coach/record")
def style_expression_coach_record(choice: str = "", style_type: str = "", authenticity: float = 0.0, confidence: float = 0.0, comfort: float = 0.0, appropriateness: float = 0.0, expression: float = 0.0, experimentation: float = 0.0, notes: str = ""):
    entry = get_style_expression_coach().record_style(choice=choice, style_type=style_type, authenticity=authenticity, confidence=confidence, comfort=comfort, appropriateness=appropriateness, expression=expression, experimentation=experimentation, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/style_expression_coach/stats")
def style_expression_coach_stats():
    return get_style_expression_coach().get_style_stats()

@router.get("/style_expression_coach/score")
def style_expression_coach_score():
    return {"style_score": get_style_expression_coach().get_style_score()}

@router.post("/wardrobe_mindfulness_guide/record")
def wardrobe_mindfulness_guide_record(action: str = "", wardrobe_type: str = "", intention: float = 0.0, quality: float = 0.0, sustainability: float = 0.0, joy: float = 0.0, care: float = 0.0, curation: float = 0.0, notes: str = ""):
    entry = get_wardrobe_mindfulness_guide().record_wardrobe(action=action, wardrobe_type=wardrobe_type, intention=intention, quality=quality, sustainability=sustainability, joy=joy, care=care, curation=curation, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/wardrobe_mindfulness_guide/stats")
def wardrobe_mindfulness_guide_stats():
    return get_wardrobe_mindfulness_guide().get_wardrobe_stats()

@router.get("/wardrobe_mindfulness_guide/score")
def wardrobe_mindfulness_guide_score():
    return {"wardrobe_score": get_wardrobe_mindfulness_guide().get_wardrobe_score()}

@router.post("/personal_brand_designer/record")
def personal_brand_designer_record(moment: str = "", brand_type: str = "", clarity: float = 0.0, consistency: float = 0.0, authenticity: float = 0.0, impact: float = 0.0, alignment: float = 0.0, visibility: float = 0.0, notes: str = ""):
    entry = get_personal_brand_designer().record_brand(moment=moment, brand_type=brand_type, clarity=clarity, consistency=consistency, authenticity=authenticity, impact=impact, alignment=alignment, visibility=visibility, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/personal_brand_designer/stats")
def personal_brand_designer_stats():
    return get_personal_brand_designer().get_brand_stats()

@router.get("/personal_brand_designer/score")
def personal_brand_designer_score():
    return {"brand_score": get_personal_brand_designer().get_brand_score()}

@router.post("/dress_for_joy_coach/record")
def dress_for_joy_coach_record(choice: str = "", dress_type: str = "", joy: float = 0.0, confidence: float = 0.0, energy: float = 0.0, playfulness: float = 0.0, self_love: float = 0.0, intention: float = 0.0, notes: str = ""):
    entry = get_dress_for_joy_coach().record_dress(choice=choice, dress_type=dress_type, joy=joy, confidence=confidence, energy=energy, playfulness=playfulness, self_love=self_love, intention=intention, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/dress_for_joy_coach/stats")
def dress_for_joy_coach_stats():
    return get_dress_for_joy_coach().get_dress_stats()

@router.get("/dress_for_joy_coach/score")
def dress_for_joy_coach_score():
    return {"dress_score": get_dress_for_joy_coach().get_dress_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "style_expression_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch62 = """
        # Batch 62 — Fashion & Personal Style Intelligence
        from core.style_expression_coach import get_style_expression_coach
        from core.wardrobe_mindfulness_guide import get_wardrobe_mindfulness_guide
        from core.personal_brand_designer import get_personal_brand_designer
        from core.dress_for_joy_coach import get_dress_for_joy_coach
        self.style_expression_coach = get_style_expression_coach()
        self.wardrobe_mindfulness_guide = get_wardrobe_mindfulness_guide()
        self.personal_brand_designer = get_personal_brand_designer()
        self.dress_for_joy_coach = get_dress_for_joy_coach()
"""

if "style_expression_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch62 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch62_brief = """
        # Batch 62 — Fashion & Personal Style Intelligence
        try:
            from core.style_expression_coach import get_style_expression_coach
            report["style_expression_coach"] = get_style_expression_coach().get_style_stats()
        except Exception as e:
            report["style_expression_coach"] = {"error": str(e)}
        try:
            from core.wardrobe_mindfulness_guide import get_wardrobe_mindfulness_guide
            report["wardrobe_mindfulness_guide"] = get_wardrobe_mindfulness_guide().get_wardrobe_stats()
        except Exception as e:
            report["wardrobe_mindfulness_guide"] = {"error": str(e)}
        try:
            from core.personal_brand_designer import get_personal_brand_designer
            report["personal_brand_designer"] = get_personal_brand_designer().get_brand_stats()
        except Exception as e:
            report["personal_brand_designer"] = {"error": str(e)}
        try:
            from core.dress_for_joy_coach import get_dress_for_joy_coach
            report["dress_for_joy_coach"] = get_dress_for_joy_coach().get_dress_stats()
        except Exception as e:
            report["dress_for_joy_coach"] = {"error": str(e)}
"""

if "style_expression_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch62_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch62_pulse = """
        # Batch 62 — Fashion & Personal Style Intelligence
        try:
            from core.style_expression_coach import get_style_expression_coach
            report["style_expression_coach_pulse"] = get_style_expression_coach().get_style_score()
        except Exception:
            pass
        try:
            from core.wardrobe_mindfulness_guide import get_wardrobe_mindfulness_guide
            report["wardrobe_mindfulness_guide_pulse"] = get_wardrobe_mindfulness_guide().get_wardrobe_score()
        except Exception:
            pass
        try:
            from core.personal_brand_designer import get_personal_brand_designer
            report["personal_brand_designer_pulse"] = get_personal_brand_designer().get_brand_score()
        except Exception:
            pass
        try:
            from core.dress_for_joy_coach import get_dress_for_joy_coach
            report["dress_for_joy_coach_pulse"] = get_dress_for_joy_coach().get_dress_score()
        except Exception:
            pass
"""

if "style_expression_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch62_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 62 wiring complete.")
