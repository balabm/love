# --- API Routes ---
api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

api_imports = """from core.decision_quality_tracker import get_decision_quality_tracker
from core.optionality_maximizer import get_optionality_maximizer
from core.expected_value_coach import get_expected_value_coach
from core.regret_minimizer import get_regret_minimizer
"""

api_routes = '''

@router.post("/decision_quality_tracker/record")
def decision_quality_tracker_record(decision: str = "", decision_type: str = "", quality: float = 0.0, speed: float = 0.0, information: float = 0.0, outcome: float = 0.0, clarity: float = 0.0, values_alignment: float = 0.0, notes: str = ""):
    entry = get_decision_quality_tracker().record_decision(decision=decision, decision_type=decision_type, quality=quality, speed=speed, information=information, outcome=outcome, clarity=clarity, values_alignment=values_alignment, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/decision_quality_tracker/stats")
def decision_quality_tracker_stats():
    return get_decision_quality_tracker().get_decision_stats()

@router.get("/decision_quality_tracker/score")
def decision_quality_tracker_score():
    return {"decision_score": get_decision_quality_tracker().get_decision_score()}

@router.post("/optionality_maximizer/record")
def optionality_maximizer_record(decision: str = "", optionality_type: str = "", doors_opened: float = 0.0, doors_closed: float = 0.0, reversibility: float = 0.0, flexibility: float = 0.0, strategic_value: float = 0.0, notes: str = ""):
    entry = get_optionality_maximizer().record_optionality(decision=decision, optionality_type=optionality_type, doors_opened=doors_opened, doors_closed=doors_closed, reversibility=reversibility, flexibility=flexibility, strategic_value=strategic_value, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/optionality_maximizer/stats")
def optionality_maximizer_stats():
    return get_optionality_maximizer().get_optionality_stats()

@router.get("/optionality_maximizer/score")
def optionality_maximizer_score():
    return {"optionality_score": get_optionality_maximizer().get_optionality_score()}

@router.post("/expected_value_coach/record")
def expected_value_coach_record(decision: str = "", ev_type: str = "", probability: float = 0.0, payoff: float = 0.0, actual_outcome: float = 0.0, emotion_influence: float = 0.0, calibration: float = 0.0, notes: str = ""):
    entry = get_expected_value_coach().record_ev(decision=decision, ev_type=ev_type, probability=probability, payoff=payoff, actual_outcome=actual_outcome, emotion_influence=emotion_influence, calibration=calibration, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/expected_value_coach/stats")
def expected_value_coach_stats():
    return get_expected_value_coach().get_ev_stats()

@router.get("/expected_value_coach/score")
def expected_value_coach_score():
    return {"ev_score": get_expected_value_coach().get_ev_score()}

@router.post("/regret_minimizer/record")
def regret_minimizer_record(regret: str = "", regret_type: str = "", intensity: float = 0.0, learning: float = 0.0, resolution: float = 0.0, anticipation: float = 0.0, action_taken: float = 0.0, notes: str = ""):
    entry = get_regret_minimizer().record_regret(regret=regret, regret_type=regret_type, intensity=intensity, learning=learning, resolution=resolution, anticipation=anticipation, action_taken=action_taken, notes=notes)
    return {"status": "recorded", "entry_id": entry.entry_id}

@router.get("/regret_minimizer/stats")
def regret_minimizer_stats():
    return get_regret_minimizer().get_regret_stats()

@router.get("/regret_minimizer/score")
def regret_minimizer_score():
    return {"regret_score": get_regret_minimizer().get_regret_score()}
'''

# Insert imports before the last import block
last_import = api.rfind("from core.")
last_import_end = api.find("\n", api.find("\n", last_import) + 1)
if api_imports.strip() not in api:
    api = api[:last_import_end] + "\n" + api_imports + api[last_import_end:]

# Insert routes before the last line
if "decision_quality_tracker/record" not in api:
    api = api.rstrip() + "\n" + api_routes + "\n"

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)

print("API wired.")

# --- Startup Script ---
startup_path = "start_evolution.py"
with open(startup_path, "r", encoding="utf-8") as f:
    startup = f.read()

batch50 = """
        # Batch 50 — Decision Intelligence
        from core.decision_quality_tracker import get_decision_quality_tracker
        from core.optionality_maximizer import get_optionality_maximizer
        from core.expected_value_coach import get_expected_value_coach
        from core.regret_minimizer import get_regret_minimizer
        self.decision_quality_tracker = get_decision_quality_tracker()
        self.optionality_maximizer = get_optionality_maximizer()
        self.expected_value_coach = get_expected_value_coach()
        self.regret_minimizer = get_regret_minimizer()
"""

if "decision_quality_tracker" not in startup:
    startup = startup.replace("        # === End Modern AI Systems ===", batch50 + "        # === End Modern AI Systems ===")

with open(startup_path, "w", encoding="utf-8") as f:
    f.write(startup)

print("Startup wired.")

# --- Daily Briefing ---
briefing_path = "core/daily_briefing.py"
with open(briefing_path, "r", encoding="utf-8") as f:
    briefing = f.read()

batch50_brief = """
        # Batch 50 — Decision Intelligence
        try:
            from core.decision_quality_tracker import get_decision_quality_tracker
            report["decision_quality_tracker"] = get_decision_quality_tracker().get_decision_stats()
        except Exception as e:
            report["decision_quality_tracker"] = {"error": str(e)}
        try:
            from core.optionality_maximizer import get_optionality_maximizer
            report["optionality_maximizer"] = get_optionality_maximizer().get_optionality_stats()
        except Exception as e:
            report["optionality_maximizer"] = {"error": str(e)}
        try:
            from core.expected_value_coach import get_expected_value_coach
            report["expected_value_coach"] = get_expected_value_coach().get_ev_stats()
        except Exception as e:
            report["expected_value_coach"] = {"error": str(e)}
        try:
            from core.regret_minimizer import get_regret_minimizer
            report["regret_minimizer"] = get_regret_minimizer().get_regret_stats()
        except Exception as e:
            report["regret_minimizer"] = {"error": str(e)}
"""

if "decision_quality_tracker" not in briefing:
    briefing = briefing.replace("        # === End Modern AI Systems ===", batch50_brief + "        # === End Modern AI Systems ===")

with open(briefing_path, "w", encoding="utf-8") as f:
    f.write(briefing)

print("Daily briefing wired.")

# --- Heartbeat ---
heartbeat_path = "core/heartbeat.py"
with open(heartbeat_path, "r", encoding="utf-8") as f:
    heartbeat = f.read()

batch50_pulse = """
        # Batch 50 — Decision Intelligence
        try:
            from core.decision_quality_tracker import get_decision_quality_tracker
            report["decision_quality_tracker_pulse"] = get_decision_quality_tracker().get_decision_score()
        except Exception:
            pass
        try:
            from core.optionality_maximizer import get_optionality_maximizer
            report["optionality_maximizer_pulse"] = get_optionality_maximizer().get_optionality_score()
        except Exception:
            pass
        try:
            from core.expected_value_coach import get_expected_value_coach
            report["expected_value_coach_pulse"] = get_expected_value_coach().get_ev_score()
        except Exception:
            pass
        try:
            from core.regret_minimizer import get_regret_minimizer
            report["regret_minimizer_pulse"] = get_regret_minimizer().get_regret_score()
        except Exception:
            pass
"""

if "decision_quality_tracker_pulse" not in heartbeat:
    heartbeat = heartbeat.replace("        # === End Modern AI Systems ===", batch50_pulse + "        # === End Modern AI Systems ===")

with open(heartbeat_path, "w", encoding="utf-8") as f:
    f.write(heartbeat)

print("Heartbeat wired.")

print("Batch 50 wiring complete.")
