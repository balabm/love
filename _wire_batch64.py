# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.daily_writing_coach import get_daily_writing_coach
from core.publishing_navigator import get_publishing_navigator
from core.blog_craft_coach import get_blog_craft_coach
from core.newsletter_creator import get_newsletter_creator
"""

api_routes = '''

@router.post("/daily_writing_coach/record")
def daily_writing_coach_record(piece: str = "", writing_type: str = "", flow: float = 0.0, clarity: float = 0.0, courage: float = 0.0, consistency: float = 0.0, joy: float = 0.0, voice: float = 0.0, notes: str = ""):
    entry = get_daily_writing_coach().record_writing(piece=piece, writing_type=writing_type, flow=flow, clarity=clarity, courage=courage, consistency=consistency, joy=joy, voice=voice, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/daily_writing_coach/stats")
def daily_writing_coach_stats():
    return get_daily_writing_coach().get_writing_stats()

@router.get("/daily_writing_coach/score")
def daily_writing_coach_score():
    return {"writing_score": get_daily_writing_coach().get_writing_score()}

@router.post("/publishing_navigator/record")
def publishing_navigator_record(work: str = "", publishing_type: str = "", readiness: float = 0.0, clarity: float = 0.0, courage: float = 0.0, strategy: float = 0.0, impact: float = 0.0, audience: float = 0.0, notes: str = ""):
    entry = get_publishing_navigator().record_publishing(work=work, publishing_type=publishing_type, readiness=readiness, clarity=clarity, courage=courage, strategy=strategy, impact=impact, audience=audience, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/publishing_navigator/stats")
def publishing_navigator_stats():
    return get_publishing_navigator().get_publishing_stats()

@router.get("/publishing_navigator/score")
def publishing_navigator_score():
    return {"publishing_score": get_publishing_navigator().get_publishing_score()}

@router.post("/blog_craft_coach/record")
def blog_craft_coach_record(post: str = "", blog_type: str = "", clarity: float = 0.0, voice: float = 0.0, structure: float = 0.0, value: float = 0.0, resonance: float = 0.0, consistency: float = 0.0, notes: str = ""):
    entry = get_blog_craft_coach().record_blog(post=post, blog_type=blog_type, clarity=clarity, voice=voice, structure=structure, value=value, resonance=resonance, consistency=consistency, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/blog_craft_coach/stats")
def blog_craft_coach_stats():
    return get_blog_craft_coach().get_blog_stats()

@router.get("/blog_craft_coach/score")
def blog_craft_coach_score():
    return {"blog_score": get_blog_craft_coach().get_blog_score()}

@router.post("/newsletter_creator/record")
def newsletter_creator_record(issue: str = "", newsletter_type: str = "", clarity: float = 0.0, value: float = 0.0, voice: float = 0.0, consistency: float = 0.0, engagement: float = 0.0, growth: float = 0.0, notes: str = ""):
    entry = get_newsletter_creator().record_newsletter(issue=issue, newsletter_type=newsletter_type, clarity=clarity, value=value, voice=voice, consistency=consistency, engagement=engagement, growth=growth, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/newsletter_creator/stats")
def newsletter_creator_stats():
    return get_newsletter_creator().get_newsletter_stats()

@router.get("/newsletter_creator/score")
def newsletter_creator_score():
    return {"newsletter_score": get_newsletter_creator().get_newsletter_score()}
'''

# Insert imports BEFORE router = APIRouter(...) to avoid corrupting try blocks inside functions
router_line = api.find("router = APIRouter")
if router_line != -1 and api_imports.strip() not in api:
    api = api[:router_line] + api_imports + "\n" + api[router_line:]

# Insert routes at end of file
if "daily_writing_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired safely.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch64 = """
        # Batch 64 — Writing & Expression Intelligence
        from core.daily_writing_coach import get_daily_writing_coach
        from core.publishing_navigator import get_publishing_navigator
        from core.blog_craft_coach import get_blog_craft_coach
        from core.newsletter_creator import get_newsletter_creator
        self.daily_writing_coach = get_daily_writing_coach()
        self.publishing_navigator = get_publishing_navigator()
        self.blog_craft_coach = get_blog_craft_coach()
        self.newsletter_creator = get_newsletter_creator()
"""

if "daily_writing_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch64 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch64_brief = """
        # Batch 64 — Writing & Expression Intelligence
        try:
            from core.daily_writing_coach import get_daily_writing_coach
            report["daily_writing_coach"] = get_daily_writing_coach().get_writing_stats()
        except Exception as e:
            report["daily_writing_coach"] = {"error": str(e)}
        try:
            from core.publishing_navigator import get_publishing_navigator
            report["publishing_navigator"] = get_publishing_navigator().get_publishing_stats()
        except Exception as e:
            report["publishing_navigator"] = {"error": str(e)}
        try:
            from core.blog_craft_coach import get_blog_craft_coach
            report["blog_craft_coach"] = get_blog_craft_coach().get_blog_stats()
        except Exception as e:
            report["blog_craft_coach"] = {"error": str(e)}
        try:
            from core.newsletter_creator import get_newsletter_creator
            report["newsletter_creator"] = get_newsletter_creator().get_newsletter_stats()
        except Exception as e:
            report["newsletter_creator"] = {"error": str(e)}
"""

if "daily_writing_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch64_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch64_pulse = """
        # Batch 64 — Writing & Expression Intelligence
        try:
            from core.daily_writing_coach import get_daily_writing_coach
            report["daily_writing_coach_pulse"] = get_daily_writing_coach().get_writing_score()
        except Exception:
            pass
        try:
            from core.publishing_navigator import get_publishing_navigator
            report["publishing_navigator_pulse"] = get_publishing_navigator().get_publishing_score()
        except Exception:
            pass
        try:
            from core.blog_craft_coach import get_blog_craft_coach
            report["blog_craft_coach_pulse"] = get_blog_craft_coach().get_blog_score()
        except Exception:
            pass
        try:
            from core.newsletter_creator import get_newsletter_creator
            report["newsletter_creator_pulse"] = get_newsletter_creator().get_newsletter_score()
        except Exception:
            pass
"""

if "daily_writing_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch64_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 64 wiring complete.")
