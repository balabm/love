"""Minimal LOVE backend for UI testing."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/lifescore")
def lifescore():
    return {"score": 78}

@app.get("/orchestrator/interventions")
def interventions():
    return {"interventions": []}

@app.get("/context/summary")
def context():
    return {
        "local_time": "17:30",
        "time_of_day": "evening",
        "activity": "coding",
        "active_app": "VS Code",
        "active_window": "love",
        "battery": 85,
        "hours_worked": 6.5,
        "tasks_overdue": 0,
        "tasks_due_today": 2,
        "unread_important": 1,
        "is_in_meeting": False,
        "suggested_action": "take a break",
    }

@app.get("/evolution/status")
def evolution():
    return {"current_generation": 42, "active_mutations": 12, "prompt_size_bytes": 2048, "last_evolution_cycle": "2026-06-01T12:00:00Z"}

@app.get("/intelligence/predictions")
def predictions():
    return {"predictions": []}

@app.get("/agi/consciousness")
def consciousness():
    return {"emotional_state": {"primary_emotion": "focused"}, "thoughts": []}

@app.get("/agi/autonomy-policy")
def policy():
    return {"mode": "balanced"}

@app.post("/agi/autonomy-policy/mode")
def set_policy(req: dict):
    return {"mode": req.get("mode", "balanced")}

@app.post("/chat")
def chat(req: dict):
    return {"response": "Hey Karthi. I'm watching everything.", "thinking": ""}

@app.post("/orchestrator/dismiss/{id}")
def dismiss(id: str):
    return {"ok": True}

@app.websocket("/agi/companion/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass

@app.get("/evolution/experiments")
def experiments():
    return []

@app.get("/evolution/swarms")
def swarms():
    return []

@app.get("/evolution/history")
def history(limit: int = 10):
    return {"history": []}

@app.get("/intelligence/self-evolution")
def self_evolution():
    return {
        "modules": {
            "llm_manager": {"active": True, "status": "ready"},
            "graph_rag": {"active": True, "status": "ready"},
            "prompt_optimizer": {"active": True, "status": "ready"},
            "self_reflection": {"active": True, "status": "ready"},
            "conversation_quality": {"active": True, "status": "ready"},
            "predictive_maintenance": {"active": True, "status": "ready"},
            "multi_agent_orchestrator": {"active": True, "status": "ready"},
            "intent_predictor": {"active": True, "status": "ready"},
            "personality_adapter": {"active": True, "status": "ready"},
            "response_cache": {"active": True, "status": "ready"},
        }
    }

@app.get("/{path:path}")
def catch_all(path: str):
    return {}

@app.post("/{path:path}")
def catch_all_post(path: str):
    return {}
