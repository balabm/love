# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.authentic_expression_coach import get_authentic_expression_coach
from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
from core.difficult_conversation_navigator import get_difficult_conversation_navigator
from core.active_listening_master import get_active_listening_master
"""

api_routes = '''

@router.post("/authentic_expression_coach/record")
def authentic_expression_coach_record(expression: str = "", expression_type: str = "", authenticity: float = 0.0, fear: float = 0.0, reception: float = 0.0, satisfaction: float = 0.0, kindness: float = 0.0, notes: str = ""):
    entry = get_authentic_expression_coach().record_expression(expression=expression, expression_type=expression_type, authenticity=authenticity, fear=fear, reception=reception, satisfaction=satisfaction, kindness=kindness, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/authentic_expression_coach/stats")
def authentic_expression_coach_stats():
    return get_authentic_expression_coach().get_expression_stats()

@router.get("/authentic_expression_coach/score")
def authentic_expression_coach_score():
    return {"expression_score": get_authentic_expression_coach().get_expression_score()}

@router.post("/vulnerable_communication_trainer/record")
def vulnerable_communication_trainer_record(vulnerability: str = "", vulnerability_type: str = "", courage: float = 0.0, reception: float = 0.0, connection: float = 0.0, safety: float = 0.0, reciprocity: float = 0.0, notes: str = ""):
    entry = get_vulnerable_communication_trainer().record_vulnerability(vulnerability=vulnerability, vulnerability_type=vulnerability_type, courage=courage, reception=reception, connection=connection, safety=safety, reciprocity=reciprocity, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/vulnerable_communication_trainer/stats")
def vulnerable_communication_trainer_stats():
    return get_vulnerable_communication_trainer().get_vulnerability_stats()

@router.get("/vulnerable_communication_trainer/score")
def vulnerable_communication_trainer_score():
    return {"vulnerability_score": get_vulnerable_communication_trainer().get_vulnerability_score()}

@router.post("/difficult_conversation_navigator/record")
def difficult_conversation_navigator_record(topic: str = "", conversation_type: str = "", preparation: float = 0.0, delivery: float = 0.0, reception: float = 0.0, outcome: float = 0.0, emotion_management: float = 0.0, follow_up: float = 0.0, notes: str = ""):
    entry = get_difficult_conversation_navigator().record_conversation(topic=topic, conversation_type=conversation_type, preparation=preparation, delivery=delivery, reception=reception, outcome=outcome, emotion_management=emotion_management, follow_up=follow_up, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/difficult_conversation_navigator/stats")
def difficult_conversation_navigator_stats():
    return get_difficult_conversation_navigator().get_conversation_stats()

@router.get("/difficult_conversation_navigator/score")
def difficult_conversation_navigator_score():
    return {"conversation_score": get_difficult_conversation_navigator().get_conversation_score()}

@router.post("/active_listening_master/record")
def active_listening_master_record(situation: str = "", listening_type: str = "", presence: float = 0.0, understanding: float = 0.0, impact: float = 0.0, no_fixing: float = 0.0, no_judging: float = 0.0, notes: str = ""):
    entry = get_active_listening_master().record_listening(situation=situation, listening_type=listening_type, presence=presence, understanding=understanding, impact=impact, no_fixing=no_fixing, no_judging=no_judging, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/active_listening_master/stats")
def active_listening_master_stats():
    return get_active_listening_master().get_listening_stats()

@router.get("/active_listening_master/score")
def active_listening_master_score():
    return {"listening_score": get_active_listening_master().get_listening_score()}
'''

# Insert imports before the last import block
last_import = api.rfind("from core.")
last_import_end = api.find("\n", api.find("\n", last_import) + 1)
if api_imports.strip() not in api:
    api = api[:last_import_end] + "\n" + api_imports + api[last_import_end:]

# Insert routes before the last line
if "authentic_expression_coach/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch52 = """
        # Batch 52 — Communication Mastery
        from core.authentic_expression_coach import get_authentic_expression_coach
        from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
        from core.difficult_conversation_navigator import get_difficult_conversation_navigator
        from core.active_listening_master import get_active_listening_master
        self.authentic_expression_coach = get_authentic_expression_coach()
        self.vulnerable_communication_trainer = get_vulnerable_communication_trainer()
        self.difficult_conversation_navigator = get_difficult_conversation_navigator()
        self.active_listening_master = get_active_listening_master()
"""

if "authentic_expression_coach" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch52 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch52_brief = """
        # Batch 52 — Communication Mastery
        try:
            from core.authentic_expression_coach import get_authentic_expression_coach
            report["authentic_expression_coach"] = get_authentic_expression_coach().get_expression_stats()
        except Exception as e:
            report["authentic_expression_coach"] = {"error": str(e)}
        try:
            from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
            report["vulnerable_communication_trainer"] = get_vulnerable_communication_trainer().get_vulnerability_stats()
        except Exception as e:
            report["vulnerable_communication_trainer"] = {"error": str(e)}
        try:
            from core.difficult_conversation_navigator import get_difficult_conversation_navigator
            report["difficult_conversation_navigator"] = get_difficult_conversation_navigator().get_conversation_stats()
        except Exception as e:
            report["difficult_conversation_navigator"] = {"error": str(e)}
        try:
            from core.active_listening_master import get_active_listening_master
            report["active_listening_master"] = get_active_listening_master().get_listening_stats()
        except Exception as e:
            report["active_listening_master"] = {"error": str(e)}
"""

if "authentic_expression_coach" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch52_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch52_pulse = """
        # Batch 52 — Communication Mastery
        try:
            from core.authentic_expression_coach import get_authentic_expression_coach
            report["authentic_expression_coach_pulse"] = get_authentic_expression_coach().get_expression_score()
        except Exception:
            pass
        try:
            from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
            report["vulnerable_communication_trainer_pulse"] = get_vulnerable_communication_trainer().get_vulnerability_score()
        except Exception:
            pass
        try:
            from core.difficult_conversation_navigator import get_difficult_conversation_navigator
            report["difficult_conversation_navigator_pulse"] = get_difficult_conversation_navigator().get_conversation_score()
        except Exception:
            pass
        try:
            from core.active_listening_master import get_active_listening_master
            report["active_listening_master_pulse"] = get_active_listening_master().get_listening_score()
        except Exception:
            pass
"""

if "authentic_expression_coach_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch52_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 52 wiring complete.")
