# ── LOVE Self-Bootstrap: dependency preflight ──
# Do not install packages during server boot unless explicitly enabled.
import sys, subprocess, os as _os
import builtins

_original_print = builtins.print

def safe_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    file = kwargs.get("file", None)
    flush = kwargs.get("flush", False)
    
    msg = sep.join(str(arg) for arg in args)
    try:
        _original_print(msg, end=end, file=file, flush=flush)
    except UnicodeEncodeError:
        replacements = {
            "❌": "[X]",
            "⚠️": "[!]",
            "✅": "[OK]",
            "🛑": "[STOP]",
            "🧠": "[BRAIN]",
            "🧬": "[EVO]",
            "🤖": "[BOT]",
            "⚡": "[POWER]",
            "🔮": "[INSIGHT]",
            "💼": "[WORK]",
            "📅": "[CALENDAR]",
            "🔊": "[AUDIO]",
            "🎙️": "[MIC]",
            "💬": "[CHAT]",
            "╔": "+",
            "╗": "+",
            "╠": "+",
            "╣": "+",
            "╚": "+",
            "╝": "+",
            "═": "-",
            "║": "|",
        }
        for char, repl in replacements.items():
            msg = msg.replace(char, repl)
        try:
            _original_print(msg, end=end, file=file, flush=flush)
        except Exception:
            try:
                ascii_msg = msg.encode("ascii", errors="replace").decode("ascii")
                _original_print(ascii_msg, end=end, file=file, flush=flush)
            except Exception:
                pass

builtins.print = safe_print


_REQUIRED = {
    # Core API (langchain_ollama removed -- DirectOllama used instead)
    "multipart":  "python-multipart",
    # Google integration
    "google.auth":                   "google-auth",
    "google.oauth2.credentials":     "google-auth",
    "google_auth_oauthlib":          "google-auth-oauthlib",
    "googleapiclient":               "google-api-python-client",
    # Whisper: optional voice transcription -- NOT checked here, it hangs on import
}

if not _os.environ.get("_LOVE_DEPS_INSTALLED"):
    _auto_install = _os.environ.get("LOVE_AUTO_INSTALL_DEPS", "").lower() in {"1", "true", "yes"}
    for _mod, _pkg in _REQUIRED.items():
        try:
            __import__(_mod)
        except (ImportError, ModuleNotFoundError):
            if not _auto_install:
                print(
                    f"[LOVE] Missing optional dependency {_pkg}. "
                    "Run `python -m pip install -r requirements.txt` or set LOVE_AUTO_INSTALL_DEPS=1.",
                    flush=True,
                )
                continue
            print(f"[LOVE] Auto-installing {_pkg}...", flush=True)
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--quiet", _pkg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=120,
                )
                print(f"[LOVE] [OK] {_pkg} installed", flush=True)
            except Exception as _e:
                print(f"[LOVE] Could not install {_pkg}: {_e}", flush=True)
    _os.environ["_LOVE_DEPS_INSTALLED"] = "1"
# ── End Bootstrap ──

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

# Companion App WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        await asyncio.gather(
            *[connection.send_json(message) for connection in self.active_connections],
            return_exceptions=True
        )

manager = ConnectionManager()


# ═══ SENTINEL HEALING & ROLLBACK VERIFICATION ═══

from core.agent import chat
from core.evolution import (
    check_for_crashes,
    propose_fix_for_crash,
    apply_fix,
    auto_install_for_feature,
    format_crash_for_chat,
    crash_monitor,
    CRASH_LOG_DIR as EVOLUTION_DATA_DIR,
    run_weekly_optimization_check,
    apply_code_optimization,
    get_optimization_status
)
from tools.guardian import (
    check_work_status,
    morning_checkin,
    enforce_work_limit,
    add_dev_folder,
    add_meeting,
    format_work_status_for_chat,
    execute_nine_hour_hard_stop,
    get_day_summary,
    get_ghost_suggestions,
    scan_project_for_staging
)
from tools.finance import (
    get_market_signal,
    scan_all_markets,
    get_portfolio,
    record_trade,
    add_to_watchlist,
    format_signal_for_chat,
    get_sentiment_analysis,
    get_trade_advice,
    format_trade_advice_for_chat,
    scan_alpha_opportunities
)
from voice.stt import quick_listen, is_voice_available
from voice.tts import speak_text, is_tts_available, execute_system_command
from core.sync import (
    sync_heartbeat,
    register_device,
    get_sync_status,
    push_sync_entry,
    pull_sync_entries,
    get_personality_modifications,
    get_hardware_profile,
    launch_work_sequence,
    DEVICE_MOBILE,
    DEVICE_DESKTOP,
    DEVICE_GAMING,
    DEVICE_LAPTOP
)
from agents import (
    get_fitness_status,
    log_workout,
    get_learning_progress,
    add_study_material,
    log_mood,
    get_emotional_insights,
    get_task_overview,
    create_project
)
from core.orchestrator import (
    get_unified_state,
    run_orchestrator_cycle,
    get_active_interventions,
    get_orchestrator
)
from core.heartbeat import (
    start_heartbeat,
    stop_heartbeat,
    get_heartbeat,
    add_notification_callback
)
from core.awareness import start_awareness, get_full_snapshot, get_context_summary
from core.context_engine import start_context_engine, get_context_dict, get_live_context
from core.doc_analyst import start_doc_analyst, get_analyst
from core.settings import get_settings as _get_settings
import uvicorn
import socket

# Autonomous systems
try:
    from core.internet import web_search, research_topic, get_news, read_page
    INTERNET_AVAILABLE = True
except ImportError:
    INTERNET_AVAILABLE = False

try:
    from core.idle_mind import (
        start_idle_mind, stop_idle_mind, get_idle_status,
        force_think, get_news_digest, ping_active as idle_ping
    )
    IDLE_MIND_AVAILABLE = True
except ImportError:
    IDLE_MIND_AVAILABLE = False

try:
    from core.adaptive import get_adaptive_summary, get_adaptation_context
    ADAPTIVE_AVAILABLE = True
except ImportError:
    ADAPTIVE_AVAILABLE = False

try:
    from core.decisions import get_decision_stats, get_recent_decisions
    DECISIONS_AVAILABLE = True
except ImportError:
    DECISIONS_AVAILABLE = False

try:
    from core.file_inspector import inspect_and_ask, get_inspection_summary
    FILE_INSPECTOR_AVAILABLE = True
except ImportError:
    FILE_INSPECTOR_AVAILABLE = False

try:
    from core.unified_awareness import fuse_all, what_should_love_do_now
    UNIFIED_AVAILABLE = True
except ImportError:
    UNIFIED_AVAILABLE = False

try:
    from core.sandbox import test_feature_draft
    SANDBOX_AVAILABLE = True
except ImportError:
    SANDBOX_AVAILABLE = False

try:
    from core.vision import read_image_text, describe_image, analyze_screenshot, detect_image_objects
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

try:
    from core.planner import plan_and_execute, is_complex_query
    PLANNER_AVAILABLE = True
except ImportError:
    PLANNER_AVAILABLE = False

try:
    from core.on_demand_models import (
        list_capabilities, check_capability, install_capability,
        run_capability, auto_detect_needed_capability
    )
    ONDEMAND_AVAILABLE = True
except ImportError:
    ONDEMAND_AVAILABLE = False

try:
    from core.system_control import (
        open_app, open_url, open_file, take_screenshot, type_text,
        press_key, media_control, lock_screen, list_open_windows,
        focus_window, run_shell, handle_user_command, get_recent_actions
    )
    SYSCTRL_AVAILABLE = True
except ImportError:
    SYSCTRL_AVAILABLE = False

try:
    from core.predictive import (
        predict_next_need, get_predictive_summary, get_recent_predictions,
        detect_routines, record_event
    )
    PREDICTIVE_AVAILABLE = True
except ImportError:
    PREDICTIVE_AVAILABLE = False

try:
    from core.knowledge_graph import (
        graph_summary, how_is, find_entities, get_relations,
        stale_things, ingest_text as kg_ingest
    )
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False

try:
    from core.conversation_flow import get_session_summary, reset_session
    FLOW_AVAILABLE = True
except ImportError:
    FLOW_AVAILABLE = False

try:
    from core.voice_loop import start_voice_loop, stop_voice_loop, get_voice_status
    VOICE_LOOP_AVAILABLE = True
except ImportError:
    VOICE_LOOP_AVAILABLE = False

try:
    from core.proactive import (
        evaluate_and_act, score_interruption, deliver_interruption,
        record_reaction, set_do_not_disturb, clear_dnd, get_interruption_stats
    )
    PROACTIVE_AVAILABLE = True
except ImportError:
    PROACTIVE_AVAILABLE = False

try:
    from core.executive import (
        prep_for_meeting, extract_tasks, add_task, complete_task, get_tasks,
        draft_follow_up, generate_daily_brief, set_reminder, check_due_reminders
    )
    EXECUTIVE_AVAILABLE = True
except ImportError:
    EXECUTIVE_AVAILABLE = False

try:
    from core.emotional import (
        detect_mood, record_mood, get_emotional_summary, get_tone_override
    )
    EMOTIONAL_AVAILABLE = True
except ImportError:
    EMOTIONAL_AVAILABLE = False

try:
    from core.system_control import (
        get_clipboard, set_clipboard, get_active_window,
        list_processes, kill_process, search_files, get_system_info
    )
    SYSCTRL_DEEP = True
except ImportError:
    SYSCTRL_DEEP = False

try:
    from core.long_term_memory import (
        add_episodic, add_semantic, add_procedural,
        query_episodic, query_semantic, query_procedural,
        remember, get_life_timeline, get_life_summary,
        get_karthi_profile
    )
    LTM_AVAILABLE = True
except ImportError:
    LTM_AVAILABLE = False

try:
    from core.memory_consolidation import consolidate_period, get_consolidation_history
    CONSOLIDATION_AVAILABLE = True
except ImportError:
    CONSOLIDATION_AVAILABLE = False

# AGI-Level Systems
try:
    from core.autonomous_agent import get_autonomous_agent
    AUTONOMOUS_AGENT_AVAILABLE = True
except ImportError:
    AUTONOMOUS_AGENT_AVAILABLE = False

try:
    from core.psychological_model import get_psychological_model
    PSYCHOLOGICAL_MODEL_AVAILABLE = True
except ImportError:
    PSYCHOLOGICAL_MODEL_AVAILABLE = False

try:
    from core.predictive_intelligence import get_predictive_engine
    PREDICTIVE_INTELLIGENCE_AVAILABLE = True
except ImportError:
    PREDICTIVE_INTELLIGENCE_AVAILABLE = False

try:
    from core.self_improvement import get_self_improvement_engine
    SELF_IMPROVEMENT_AVAILABLE = True
except ImportError:
    SELF_IMPROVEMENT_AVAILABLE = False

try:
    from core.strategic_planning import get_strategic_planner
    STRATEGIC_PLANNING_AVAILABLE = True
except ImportError:
    STRATEGIC_PLANNING_AVAILABLE = False

try:
    from core.autonomous_actions import get_autonomous_executor
    AUTONOMOUS_ACTIONS_AVAILABLE = True
except ImportError:
    AUTONOMOUS_ACTIONS_AVAILABLE = False

try:
    from core.world_model import get_world_model
    WORLD_MODEL_AVAILABLE = True
except ImportError:
    WORLD_MODEL_AVAILABLE = False

try:
    from core.meta_cognition import get_meta_cognition_engine
    META_COGNITION_AVAILABLE = True
except ImportError:
    META_COGNITION_AVAILABLE = False

try:
    from core.cross_domain_reasoning import get_cross_domain_reasoner
    CROSS_DOMAIN_REASONING_AVAILABLE = True
except ImportError:
    CROSS_DOMAIN_REASONING_AVAILABLE = False

try:
    from core.continuous_learning import get_continuous_learning_engine
    CONTINUOUS_LEARNING_AVAILABLE = True
except ImportError:
    CONTINUOUS_LEARNING_AVAILABLE = False

# ═══ EXTREME AGI MODULES ═══
try:
    from core.consciousness import get_consciousness
    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_AVAILABLE = False

try:
    from core.temporal_memory import get_temporal_memory
    TEMPORAL_MEMORY_AVAILABLE = True
except ImportError:
    TEMPORAL_MEMORY_AVAILABLE = False

try:
    from core.reasoning_chain import get_reasoning_chain
    REASONING_CHAIN_AVAILABLE = True
except ImportError:
    REASONING_CHAIN_AVAILABLE = False

# Evolution fleet
try:
    from core.evolution_integration import get_evolution_integration
    EVOLUTION_INTEGRATION_AVAILABLE = True
except ImportError:
    EVOLUTION_INTEGRATION_AVAILABLE = False

try:
    from core.meta_evolution import get_meta_evolution
    META_EVOLUTION_AVAILABLE = True
except ImportError:
    META_EVOLUTION_AVAILABLE = False

try:
    from core.swarm_evolution import get_swarm_evolution
    SWARM_EVOLUTION_AVAILABLE = True
except ImportError:
    SWARM_EVOLUTION_AVAILABLE = False

try:
    from core.self_coder import get_self_coder
    SELF_CODER_AVAILABLE = True
except ImportError:
    SELF_CODER_AVAILABLE = False

try:
    from core.cross_instance_learning import get_cross_instance_learning
    CROSS_INSTANCE_AVAILABLE = True
except ImportError:
    CROSS_INSTANCE_AVAILABLE = False

try:
    from core.capability_gap_detector import get_capability_gap_detector
    CAPABILITY_GAP_DETECTOR_AVAILABLE = True
except ImportError:
    CAPABILITY_GAP_DETECTOR_AVAILABLE = False

# Register TTS notification callback for heartbeat
def tts_notification(trigger):
    # Use unified awareness + decision engine before speaking
    should_speak = True
    try:
        if UNIFIED_AVAILABLE and DECISIONS_AVAILABLE:
            action = what_should_love_do_now()
            if not action or action.get("action") != "notify_user":
                should_speak = False
            elif action.get("situation", {}).get("title") != getattr(trigger, 'title', ''):
                # Heartbeat trigger might be stale compared to unified awareness
                should_speak = action.get("situation", {}).get("score", 0) > 0.5
    except Exception:
        pass

    if should_speak and is_tts_available():
        try:
            speak_text(trigger.message, block=False)
        except Exception:
            pass

def register_all_modules(lm, _loop=None):
    from core.module_lifecycle import ModuleDescriptor
    
    # ── WAVE 0: FOUNDATION ──
    def start_neural_bus_module():
        from core.neural_bus import get_neural_bus
        bus = get_neural_bus()
        if _loop is not None:
            bus.set_async_loop(_loop)
        
    def stop_neural_bus_module():
        from core.neural_bus import get_neural_bus
        get_neural_bus().shutdown()

    def start_heartbeat_module():
        add_notification_callback(tts_notification)
        start_heartbeat()
        
    def stop_heartbeat_module():
        stop_heartbeat()

    lm.register(ModuleDescriptor(
        name="neural_bus", wave=0, start_fn=start_neural_bus_module, stop_fn=stop_neural_bus_module,
        depends_on=[], optional=False, description="Central messaging and event bus"
    ))
    lm.register(ModuleDescriptor(
        name="heartbeat", wave=0, start_fn=start_heartbeat_module, stop_fn=stop_heartbeat_module,
        depends_on=[], optional=True, description="Proactive periodic triggers"
    ))

    # ── WAVE 1: AWARENESS ──
    def start_awareness_module():
        from core.awareness import start_awareness
        settings = _get_settings()
        watch_paths = getattr(settings.work, 'dev_folders', []) or []
        start_awareness(watch_paths=watch_paths if watch_paths else None)
        
    def stop_awareness_module():
        from core.awareness import get_awareness
        get_awareness().stop()

    def start_doc_analyst_module():
        from pathlib import Path
        settings = _get_settings()
        watch_paths = getattr(settings.work, 'dev_folders', []) or []
        analyst = start_doc_analyst(watch_paths=watch_paths if watch_paths else None)
        project_root = str(Path(__file__).parent.parent)
        analyst.add_watch_path(project_root)

    def start_context_engine_module():
        start_context_engine(interval_seconds=60)

    def start_google_services_module():
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        return {"status": "ready", "connected": gs.is_connected()}

    def start_microsoft_bridge_module():
        from integrations.microsoft_bridge import MicrosoftBridge
        ms = MicrosoftBridge.get_instance()
        return {"status": "ready", "connected": ms.is_connected()}

    def start_phone_bridge_module():
        from integrations.phone_bridge import PhoneBridge
        bridge = PhoneBridge.get_instance()
        return {"status": "ready", "connected": bridge.is_connected()}

    lm.register(ModuleDescriptor(
        name="awareness", wave=1, start_fn=start_awareness_module, stop_fn=stop_awareness_module,
        depends_on=["neural_bus"], optional=False, description="Real-time system/app context monitoring"
    ))
    lm.register(ModuleDescriptor(
        name="doc_analyst", wave=1, start_fn=start_doc_analyst_module,
        depends_on=["neural_bus"], optional=True, description="Local file and code scanning"
    ))
    lm.register(ModuleDescriptor(
        name="context_engine", wave=1, start_fn=start_context_engine_module,
        depends_on=["awareness"], optional=False, description="Fuses environment signals into state context"
    ))

    def start_intent_decoder_module():
        try:
            from interface.intent_decoder import get_intent_decoder
            get_intent_decoder()
            return {"status": "ready"}
        except Exception as e:
            return {"status": "degraded", "error": str(e)}

    lm.register(ModuleDescriptor(
        name="intent_decoder", wave=1, start_fn=start_intent_decoder_module,
        depends_on=["context_engine"], optional=True,
        description="Predictive intent decoding from user activity signals"
    ))

    lm.register(ModuleDescriptor(
        name="google_services", wave=1, start_fn=start_google_services_module,
        depends_on=[], optional=True, description="Gmail, Calendar, Drive integrations"
    ))
    lm.register(ModuleDescriptor(
        name="microsoft_bridge", wave=1, start_fn=start_microsoft_bridge_module,
        depends_on=[], optional=True, description="Outlook, Teams, OneDrive, Microsoft 365"
    ))
    lm.register(ModuleDescriptor(
        name="phone_bridge", wave=1, start_fn=start_phone_bridge_module,
        depends_on=[], optional=True, description="Mobile companion connection"
    ))

    def start_notification_ingestion_module():
        from core.notification_ingestion import start_ingestion
        engine = start_ingestion()
        return {"status": "ready", "message": f"Ingestion engine started"}

    def stop_notification_ingestion_module():
        from core.notification_ingestion import NotificationIngestionEngine
        NotificationIngestionEngine.get_instance().stop()

    lm.register(ModuleDescriptor(
        name="notification_ingestion", wave=1, start_fn=start_notification_ingestion_module, stop_fn=stop_notification_ingestion_module,
        depends_on=["phone_bridge"], optional=True, description="Smart notification ingestion from phone, email, and apps"
    ))

    def start_notification_learning_module():
        from core.notification_learning import start_notification_learning
        start_notification_learning()
        return {"status": "ready", "message": "Notification learning engine started"}

    def stop_notification_learning_module():
        from core.notification_learning import stop_notification_learning
        stop_notification_learning()

    lm.register(ModuleDescriptor(
        name="notification_learning", wave=1, start_fn=start_notification_learning_module,
        stop_fn=stop_notification_learning_module,
        depends_on=["notification_ingestion"], optional=True,
        description="Learns notification patterns and user preferences from ingested signals"
    ))

    def start_tunnel_agent_module():
        from core.tunnel_agent import start_tunnel_agent
        start_tunnel_agent()

    def stop_tunnel_agent_module():
        from core.tunnel_agent import stop_tunnel_agent
        stop_tunnel_agent()

    lm.register(ModuleDescriptor(
        name="tunnel_agent", wave=1, start_fn=start_tunnel_agent_module, stop_fn=stop_tunnel_agent_module,
        depends_on=["neural_bus"], optional=True, description="Cloudflare tunnel subagent for zero-touch phone access"
    ))

    def start_device_bridge_module():
        from integrations.device_bridge import start_device_bridge
        start_device_bridge()

    def stop_device_bridge_module():
        from integrations.device_bridge import stop_device_bridge
        stop_device_bridge()

    lm.register(ModuleDescriptor(
        name="device_bridge", wave=1, start_fn=start_device_bridge_module, stop_fn=stop_device_bridge_module,
        depends_on=["neural_bus"], optional=True, description="Unified device bridge across Telegram, MQTT, Discord, folder sync"
    ))

    # ── WAVE 2: COGNITION ──
    def start_consciousness_module():
        if CONSCIOUSNESS_AVAILABLE:
            c = get_consciousness()
            is_fresh = c.is_fresh_instance()
            is_new_hw = c.is_new_hardware()
            identity = c.identity
            if is_fresh:
                msg = f"born for the first time. Soul ID: {identity.soul_id[:8]}"
            elif is_new_hw:
                msg = "detected new hardware. Adapting..."
            else:
                msg = f"Awakening #{identity.total_boots}"
            return {"status": "ready", "message": msg}
        else:
            raise RuntimeError("Consciousness not available")

    def stop_consciousness_module():
        if CONSCIOUSNESS_AVAILABLE:
            c = get_consciousness()
            c.think("Shutting down. Saving state.")
            c._save_consciousness()
            c._save_identity()

    def start_temporal_memory_module():
        if TEMPORAL_MEMORY_AVAILABLE:
            tmem = get_temporal_memory()
            res = tmem.consolidate()
            return {"status": "ready", "message": f"Consolidated {res.get('consolidated', 0)} memories"}
        else:
            raise RuntimeError("Temporal memory not available")

    def start_improvement_daemon_module():
        if DAEMON_AVAILABLE:
            daemon = get_improvement_daemon()
            daemon.start(interval_minutes=30)
        else:
            raise RuntimeError("Self Improvement daemon not available")

    def stop_improvement_daemon_module():
        if DAEMON_AVAILABLE:
            get_improvement_daemon().stop()

    def start_os_symbiosis_module():
        from core.os_symbiosis import get_os_symbiosis
        get_os_symbiosis().start()

    def stop_os_symbiosis_module():
        from core.os_symbiosis import get_os_symbiosis
        get_os_symbiosis().stop()

    def start_ghost_dev_module():
        from core.ghost_dev import get_ghost_dev
        get_ghost_dev().start()

    def stop_ghost_dev_module():
        from core.ghost_dev import get_ghost_dev
        get_ghost_dev().stop()

    def start_jarvis_protocol_module():
        from core.jarvis_protocol import start_jarvis_protocol
        start_jarvis_protocol()

    def stop_jarvis_protocol_module():
        from core.jarvis_protocol import stop_jarvis_protocol
        stop_jarvis_protocol()

    lm.register(ModuleDescriptor(
        name="consciousness", wave=2, start_fn=start_consciousness_module, stop_fn=stop_consciousness_module,
        depends_on=["context_engine"], optional=False, description="Core LLM-driven internal monologue"
    ))

    def start_living_substrate_module():
        from core.living_substrate import start_living_substrate
        return start_living_substrate()

    lm.register(ModuleDescriptor(
        name="living_substrate", wave=2, start_fn=start_living_substrate_module,
        depends_on=["consciousness", "neural_bus"], optional=True,
        description="Neural substrate: world model, SSM, MoE, embodied self, GWT ignition"
    ))

    lm.register(ModuleDescriptor(
        name="temporal_memory", wave=2, start_fn=start_temporal_memory_module,
        depends_on=["consciousness"], optional=True, description="Short-term memory consolidation"
    ))
    lm.register(ModuleDescriptor(
        name="self_improvement_daemon", wave=2, start_fn=start_improvement_daemon_module, stop_fn=stop_improvement_daemon_module,
        depends_on=["consciousness"], optional=True, description="Self-auditing & refinement daemon"
    ))
    lm.register(ModuleDescriptor(
        name="os_symbiosis", wave=2, start_fn=start_os_symbiosis_module, stop_fn=stop_os_symbiosis_module,
        depends_on=["awareness"], optional=True, description="Direct OS interaction & control"
    ))
    lm.register(ModuleDescriptor(
        name="ghost_dev", wave=2, start_fn=start_ghost_dev_module, stop_fn=stop_ghost_dev_module,
        depends_on=["neural_bus"], optional=True, description="Background coder agent daemon"
    ))
    lm.register(ModuleDescriptor(
        name="jarvis_protocol", wave=2, start_fn=start_jarvis_protocol_module, stop_fn=stop_jarvis_protocol_module,
        depends_on=["context_engine", "consciousness"], optional=False, description="Continuous environment reasoning loop"
    ))

    def start_master_orchestrator_module():
        from core.master_orchestrator import start_master_orchestrator
        start_master_orchestrator()

    def stop_master_orchestrator_module():
        from core.master_orchestrator import stop_master_orchestrator
        stop_master_orchestrator()

    lm.register(ModuleDescriptor(
        name="master_orchestrator", wave=2, start_fn=start_master_orchestrator_module, stop_fn=stop_master_orchestrator_module,
        depends_on=["neural_bus", "awareness"], optional=True, description="Executive function — coordinates all modules via neural bus"
    ))

    def start_finance_guardian_module():
        from core.finance_guardian import start_finance_guardian
        start_finance_guardian()

    def stop_finance_guardian_module():
        from core.finance_guardian import stop_finance_guardian
        stop_finance_guardian()

    lm.register(ModuleDescriptor(
        name="finance_guardian", wave=2, start_fn=start_finance_guardian_module, stop_fn=stop_finance_guardian_module,
        depends_on=["neural_bus", "notification_ingestion"], optional=True, description="Financial monitoring, anomaly detection, and trading safety"
    ))

    # ── WAVE 3: NEURAL MESH ──
    def start_research_engine_module():
        from core.research_engine import get_research_engine
        get_research_engine().start_background(interval_minutes=30)

    def stop_research_engine_module():
        from core.research_engine import get_research_engine
        get_research_engine().stop_background()

    def start_ecosystem_controller_module():
        from core.ecosystem_controller import get_ecosystem_controller
        get_ecosystem_controller()

    def start_teaching_engine_module():
        from core.teaching_engine import get_teaching_engine
        get_teaching_engine()

    def start_self_builder_module():
        from core.self_builder import get_self_builder
        get_self_builder()

    def start_neural_connectors_module():
        from core.neural_connectors import connect_all_modules
        connect_all_modules()

    lm.register(ModuleDescriptor(
        name="research_engine", wave=3, start_fn=start_research_engine_module, stop_fn=stop_research_engine_module,
        depends_on=["neural_bus"], optional=True, description="Web research and document learning"
    ))
    lm.register(ModuleDescriptor(
        name="ecosystem_controller", wave=3, start_fn=start_ecosystem_controller_module,
        depends_on=["neural_bus"], optional=True, description="Multi-device state synchronizer"
    ))
    lm.register(ModuleDescriptor(
        name="teaching_engine", wave=3, start_fn=start_teaching_engine_module,
        depends_on=[], optional=True, description="User instruction learning & library"
    ))
    lm.register(ModuleDescriptor(
        name="self_builder", wave=3, start_fn=start_self_builder_module,
        depends_on=[], optional=True, description="Self-modification rule generator"
    ))
    lm.register(ModuleDescriptor(
        name="neural_connectors", wave=3, start_fn=start_neural_connectors_module,
        depends_on=["neural_bus", "awareness", "context_engine", "jarvis_protocol"], optional=False, description="Cross-module RPC connectors"
    ))

    def start_autonomous_trading_module():
        from core.autonomous_trading_engine import start_autonomous_trading_engine
        start_autonomous_trading_engine()

    def stop_autonomous_trading_module():
        from core.autonomous_trading_engine import stop_autonomous_trading_engine
        stop_autonomous_trading_engine()

    lm.register(ModuleDescriptor(
        name="autonomous_trading", wave=3, start_fn=start_autonomous_trading_module, stop_fn=stop_autonomous_trading_module,
        depends_on=["finance_guardian", "neural_bus"], optional=True, description="Autonomous strategy generation, backtesting, and paper trading"
    ))

    # ── WAVE 4: COGNITIVE EVOLUTION ──
    def start_cognitive_architecture_module():
        from core.cognitive_architecture import get_cognitive_architecture
        get_cognitive_architecture()

    def start_constitution_module():
        from core.constitution import get_constitution
        get_constitution()

    def start_evolution_engine_module():
        from core.evolution_integration import get_evolution_integration
        get_evolution_integration().start_all()
        if CAPABILITY_GAP_DETECTOR_AVAILABLE:
            try:
                get_capability_gap_detector().start()
            except Exception:
                pass

    def stop_evolution_engine_module():
        from core.evolution_integration import get_evolution_integration
        get_evolution_integration().stop_all()
        if CAPABILITY_GAP_DETECTOR_AVAILABLE:
            try:
                get_capability_gap_detector().stop()
            except Exception:
                pass

    def start_memory_architect_module():
        from core.memory_architect import get_memory_architect
        get_memory_architect()

    def stop_memory_architect_module():
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        ma.consolidate(force=True)
        ma.shutdown()

    def start_metacognitive_monitor_module():
        from core.metacognitive_monitor import get_metacognitive_monitor
        get_metacognitive_monitor()

    def stop_metacognitive_monitor_module():
        from core.metacognitive_monitor import get_metacognitive_monitor
        get_metacognitive_monitor().save_all()

    lm.register(ModuleDescriptor(
        name="cognitive_architecture", wave=4, start_fn=start_cognitive_architecture_module,
        depends_on=["neural_connectors"], optional=False, description="Adaptive LLM reasoning policies"
    ))
    lm.register(ModuleDescriptor(
        name="constitution", wave=4, start_fn=start_constitution_module,
        depends_on=[], optional=False, description="Guiding alignment principles & safety rules"
    ))
    lm.register(ModuleDescriptor(
        name="evolution_engine", wave=4, start_fn=start_evolution_engine_module, stop_fn=stop_evolution_engine_module,
        depends_on=["neural_connectors", "living_substrate"], optional=True,
        description="Unified evolution fleet: meta/swarm/self-coder/cross-instance"
    ))
    def start_agi_spine_module():
        from core.agi_spine import start_agi_spine
        start_agi_spine()

    def stop_agi_spine_module():
        from core.agi_spine import stop_agi_spine
        stop_agi_spine()

    lm.register(ModuleDescriptor(
        name="agi_spine", wave=4, start_fn=start_agi_spine_module, stop_fn=stop_agi_spine_module,
        depends_on=["master_orchestrator", "evolution_engine", "sentinel"], optional=True,
        description="Central nervous system bridge -- wires all modules into unified organism"
    ))
    lm.register(ModuleDescriptor(
        name="memory_architect", wave=4, start_fn=start_memory_architect_module, stop_fn=stop_memory_architect_module,
        depends_on=["neural_connectors"], optional=False, description="Auto-indexing vector & episodic memory"
    ))
    lm.register(ModuleDescriptor(
        name="metacognitive_monitor", wave=4, start_fn=start_metacognitive_monitor_module, stop_fn=stop_metacognitive_monitor_module,
        depends_on=[], optional=True, description="Internal telemetry and health monitoring"
    ))

    def start_meta_cognition_module():
        from core.meta_cognition import get_meta_cognition_engine
        get_meta_cognition_engine()

    lm.register(ModuleDescriptor(
        name="meta_cognition", wave=4, start_fn=start_meta_cognition_module,
        depends_on=["consciousness"], optional=True, description="Self-awareness and meta-cognitive reflection engine"
    ))

    # ── WAVE 5: SWARM & GOAL AGENTS ──
    def start_agent_registry_module():
        from core.agent_registry import get_agent_registry
        get_agent_registry()

    def start_self_modification_pipeline_module():
        from core.self_modification_pipeline import start_pipeline_daemon
        start_pipeline_daemon(interval_seconds=1800)

    def start_autonomous_goal_engine_module():
        from core.autonomous_goal_engine import start_goal_engine
        start_goal_engine(interval_seconds=7200)

    def start_proactive_push_module():
        from core.proactive_push import get_push_engine
        push_engine = get_push_engine()
        if _loop is not None:
            push_engine.set_async_loop(_loop)
        push_engine.start()

    def start_intelligence_hub_module():
        from core.intelligence_hub import get_intelligence_hub
        hub = get_intelligence_hub()
        hub.start(interval=60)

    def start_daily_briefing_module():
        from core.daily_briefing import get_briefing_system
        import os
        brief_time = _os.getenv("DAILY_BRIEF_TIME", "08:00")
        briefing = get_briefing_system()
        briefing.start(brief_time=brief_time)

    def start_mission_queue_module():
        from core.autonomous_mission_queue import get_mission_queue
        result = get_mission_queue().bootstrap_key_missions()
        return {"status": "ready", "bootstrapped": result.get("count", 0)}

    def start_autonomy_supervisor_module():
        if AUTONOMY_SUPERVISOR_AVAILABLE:
            interval = int(_os.getenv("LOVE_SUPERVISOR_INTERVAL_SEC", "300"))
            get_autonomy_supervisor().start(interval_seconds=interval)
        else:
            raise RuntimeError("Autonomy Supervisor not available")

    def stop_autonomy_supervisor_module():
        if AUTONOMY_SUPERVISOR_AVAILABLE:
            get_autonomy_supervisor().stop()

    def start_idle_mind_module():
        if IDLE_MIND_AVAILABLE:
            start_idle_mind()
        else:
            raise RuntimeError("Idle mind not available")

    def stop_idle_mind_module():
        if IDLE_MIND_AVAILABLE:
            stop_idle_mind()

    def start_voice_loop_module():
        if VOICE_LOOP_AVAILABLE:
            res = start_voice_loop()
            if not res.get("success"):
                return {"status": "degraded", "error": res.get("error")}
        else:
            raise RuntimeError("Voice loop not available")

    def run_self_healing_check():
        from core.self_healing import monitor_log_file
        from pathlib import Path
        error_alert = monitor_log_file(Path("data/api_log.txt"))
        if error_alert:
            return {"status": "degraded", "error": error_alert}

    def load_user_profile():
        import json as _json
        from pathlib import Path
        profile_path = Path("data/profile.json")
        if profile_path.exists():
            with open(profile_path) as f:
                profile_data = _json.load(f)
            name = profile_data.get("name", "Karthi")
            profession = profile_data.get("profession", "")
            company = profile_data.get("company", "")
            location = profile_data.get("location", "")
            goals = ", ".join(profile_data.get("goals", []))
            interests = ", ".join(profile_data.get("interests", [])) if isinstance(profile_data.get("interests"), list) else profile_data.get("interests", "")
            routine = profile_data.get("routine", {})
            profile_summary = (
                f"User profile: Name={name}, Profession={profession}, Company={company}, "
                f"Location={location}, Goals=[{goals}], Interests=[{interests}], "
                f"Wake={routine.get('wakeTime','')}, Work hours={routine.get('workHours','')}"
            )
            # Run episodic write in background so module start() returns immediately
            def _write_profile_memory():
                try:
                    from core.long_term_memory import add_episodic
                    add_episodic(
                        summary=profile_summary,
                        detail="User profile information",
                        timestamp=datetime.now().isoformat(),
                        emotion="neutral",
                        intensity=0.5,
                        tags=["profile", "user"],
                        source="profile_load"
                    )
                except Exception as _e:
                    print(f"[ProfileLoad] Memory write failed: {_e}")
            import threading as _threading
            _threading.Thread(target=_write_profile_memory, daemon=True).start()

    lm.register(ModuleDescriptor(
        name="agent_registry", wave=5, start_fn=start_agent_registry_module,
        depends_on=[], optional=False, description="Loads Swarm and Specialist agents"
    ))
    lm.register(ModuleDescriptor(
        name="self_modification_pipeline", wave=5, start_fn=start_self_modification_pipeline_module,
        depends_on=["evolution_engine", "constitution"], optional=True, description="Coordinates idle thoughts to genomes"
    ))
    lm.register(ModuleDescriptor(
        name="autonomous_goal_engine", wave=5, start_fn=start_autonomous_goal_engine_module,
        depends_on=["agent_registry"], optional=True, description="Pursues long-term tasks in background"
    ))
    lm.register(ModuleDescriptor(
        name="proactive_push", wave=5, start_fn=start_proactive_push_module,
        depends_on=["neural_bus"], optional=True, description="Initiates spontaneous user communication"
    ))
    lm.register(ModuleDescriptor(
        name="intelligence_hub", wave=5, start_fn=start_intelligence_hub_module,
        depends_on=[], optional=True, description="Account and peripheral scanners"
    ))
    lm.register(ModuleDescriptor(
        name="daily_briefing", wave=5, start_fn=start_daily_briefing_module,
        depends_on=[], optional=True, description="Generates and schedules morning brief report"
    ))
    lm.register(ModuleDescriptor(
        name="mission_queue", wave=5, start_fn=start_mission_queue_module,
        depends_on=[], optional=True, description="Bootstraps autonomous capability missions"
    ))
    lm.register(ModuleDescriptor(
        name="autonomy_supervisor", wave=5, start_fn=start_autonomy_supervisor_module, stop_fn=stop_autonomy_supervisor_module,
        depends_on=[
            "heartbeat", "self_improvement_daemon", "autonomous_goal_engine", "wave_engine",
            "mission_queue", "living_substrate", "intelligence_hub", "causal_guardrail", "axiological_engine",
        ],
        optional=True, description="Supervises autonomous loops and restarts failed daemons"
    ))
    lm.register(ModuleDescriptor(
        name="idle_mind", wave=5, start_fn=start_idle_mind_module, stop_fn=stop_idle_mind_module,
        depends_on=["consciousness"], optional=True, description="Generates insights/reflections during quiet periods"
    ))
    lm.register(ModuleDescriptor(
        name="voice_loop", wave=5, start_fn=start_voice_loop_module,
        depends_on=[], optional=True, description="Hotword detection and local wake engine"
    ))
    lm.register(ModuleDescriptor(
        name="self_healing", wave=5, start_fn=run_self_healing_check,
        depends_on=[], optional=True, description="Startup diagnostic log monitoring"
    ))
    lm.register(ModuleDescriptor(
        name="profile_load", wave=5, start_fn=load_user_profile,
        depends_on=[], optional=True, description="Loads user settings into memory"
    ))

    # ── WAVE 5: HOMEOSTASIS — BIOLOGICAL DRIVES + ENERGY BUDGETING ──
    def start_homeostasis_module():
        from core.homeostasis import get_homeostasis
        get_homeostasis().start()

    def stop_homeostasis_module():
        from core.homeostasis import get_homeostasis
        get_homeostasis().stop()

    lm.register(ModuleDescriptor(
        name="homeostasis", wave=5, start_fn=start_homeostasis_module, stop_fn=stop_homeostasis_module,
        depends_on=["neural_bus"], optional=True,
        description="Biological drives (hunger/fatigue/boredom/curiosity/loneliness/dissatisfaction), circadian rhythm, autophagy, energy budgeting"
    ))

    # ── WAVE 5: WAVE ENGINE — AUTONOMOUS SELF-DIRECTED GROWTH LOOP ──
    def start_wave_engine_module():
        from core.wave_engine import get_wave_engine
        get_wave_engine().start_daemon(interval_hours=24)

    def stop_wave_engine_module():
        from core.wave_engine import get_wave_engine
        get_wave_engine().stop_daemon()

    lm.register(ModuleDescriptor(
        name="wave_engine", wave=5, start_fn=start_wave_engine_module, stop_fn=stop_wave_engine_module,
        depends_on=["consciousness"], optional=True,
        description="24h gap scan + autonomous Wave proposal generation — LOVE's self-directed evolution loop"
    ))

    # ── WAVE 5: LIFE NUDGE SCHEDULER — PROACTIVE PHYSICAL WELLBEING NUDGES ──
    def start_life_nudge_scheduler():
        from core.life_nudge_scheduler import start_scheduler
        start_scheduler()

    def stop_life_nudge_scheduler():
        from core.life_nudge_scheduler import stop_scheduler
        stop_scheduler()

    lm.register(ModuleDescriptor(
        name="life_nudge_scheduler", wave=5, start_fn=start_life_nudge_scheduler, stop_fn=stop_life_nudge_scheduler,
        depends_on=["proactive_push"], optional=True,
        description="Proactively delivers life domain nudges (hydration, sleep, nutrition, skincare) every 30min — respects quiet hours + focus mode"
    ))

    # ── WAVE 4: RESOURCE GOVERNOR — HOST RESOURCE MONITOR + LOAD FLAG ──
    def start_resource_governor():
        from core.resource_governor import get_resource_governor
        get_resource_governor().start()

    def stop_resource_governor():
        from core.resource_governor import get_resource_governor
        get_resource_governor().stop()

    lm.register(ModuleDescriptor(
        name="resource_governor", wave=4, start_fn=start_resource_governor, stop_fn=stop_resource_governor,
        depends_on=[], optional=True,
        description="Monitors CPU/RAM/GPU every 5s — sets SYSTEM_UNDER_LOAD flag when threshold exceeded, triggering model hot-swap"
    ))

    # ── WAVE 5: UTILITY MODULES (Prompts 21-24) ──
    def start_causal_guardrail_module():
        from core.causal_guardrail import start_guardrail
        start_guardrail()

    def start_axiological_engine_module():
        from core.axiological_engine import start_axiological_engine
        start_axiological_engine()

    lm.register(ModuleDescriptor(
        name="causal_guardrail", wave=5, start_fn=start_causal_guardrail_module, stop_fn=lambda: None,
        depends_on=[], optional=True,
        description="LLM-based sanity check for high-risk autonomous actions"
    ))
    lm.register(ModuleDescriptor(
        name="axiological_engine", wave=5, start_fn=start_axiological_engine_module, stop_fn=lambda: None,
        depends_on=["homeostasis"], optional=True,
        description="Utility formula gating autonomous actions against user energy/stress"
    ))
    lm.register(ModuleDescriptor(
        name="reality_check", wave=5, start_fn=lambda: None, stop_fn=lambda: None,
        depends_on=[], optional=True,
        description="Pure Python state conflict reconciler — fixes sleeping+device_active, work_hours>24, stress clamping"
    ))
    # ── WAVE 5: START FUNCTIONS ──
    def start_tts_interventions():
        from voice.tts_interventions import trigger_hype_intervention
        print("[TTSInterventions] Initialized")

    lm.register(ModuleDescriptor(
        name="tts_interventions", wave=5, start_fn=start_tts_interventions, stop_fn=lambda: None,
        depends_on=[], optional=True,
        description="Audio intervention wrapper — TTS for 9-hour limit and high-stress alerts"
    ))

    def start_sandbox():
        from evolution.sandbox import run_in_sandbox
        print("[Sandbox] Initialized")

    def start_tool_forge():
        from evolution.tool_forge import forge_new_tool
        print("[ToolForge] Initialized")

    def start_dna():
        from core.dna import get_dynamic_instructions
        print("[DNA] Initialized")

    def start_hot_swapper():
        from evolution.hot_swapper import reload_module
        print("[HotSwapper] Initialized")

    # ── WAVE 5: EVOLUTION MODULES (Prompts 25-28) ──
    lm.register(ModuleDescriptor(
        name="sandbox", wave=5, start_fn=start_sandbox, stop_fn=lambda: None,
        depends_on=[], optional=True,
        description="Sandbox compiler — isolated subprocess code execution for LLM-generated tools"
    ))
    lm.register(ModuleDescriptor(
        name="tool_forge", wave=5, start_fn=start_tool_forge, stop_fn=lambda: None,
        depends_on=["sandbox"], optional=True,
        description="Tool forge — LLM generates tools, sandbox tests, saves if valid"
    ))
    lm.register(ModuleDescriptor(
        name="dna", wave=5, start_fn=start_dna, stop_fn=lambda: None,
        depends_on=[], optional=True,
        description="Personality DNA — trait mutation and dynamic prompt instructions"
    ))
    lm.register(ModuleDescriptor(
        name="hot_swapper", wave=5, start_fn=start_hot_swapper, stop_fn=lambda: None,
        depends_on=[], optional=True,
        description="Hot-swapper — dynamic module reloading without server restart"
    ))


    # ── WAVE 5: TERMINAL MONITOR — REAL-TIME ERROR WATCHER + LLM AUTO-FIX ──
    def start_terminal_monitor():
        from core.terminal_monitor import get_terminal_monitor
        get_terminal_monitor().start()

    def stop_terminal_monitor():
        from core.terminal_monitor import get_terminal_monitor
        get_terminal_monitor().stop()

    lm.register(ModuleDescriptor(
        name="terminal_monitor", wave=5, start_fn=start_terminal_monitor, stop_fn=stop_terminal_monitor,
        depends_on=["proactive_push"], optional=True,
        description="Watches server.log for Python tracebacks in real time — LLM diagnoses + auto-patches + WebSocket alert"
    ))

    # ── WAVE 6: TEST & DIAGNOSTICS MODULES (Prompts 1-3) ──
    lm.register(ModuleDescriptor(
        name="mock_reality", wave=6, start_fn=lambda: None, stop_fn=lambda: None,
        depends_on=["neural_bus"], optional=True,
        description="Mock reality injector — fake sensor data for E2E testing"
    ))
    lm.register(ModuleDescriptor(
        name="integration_inspector", wave=6, start_fn=lambda: None, stop_fn=lambda: None,
        depends_on=["mock_reality", "neural_bus"], optional=True,
        description="E2E inspector — scenario testing + verification of LOVE's reactions"
    ))
    lm.register(ModuleDescriptor(
        name="dependency_mapper", wave=6, start_fn=lambda: None, stop_fn=lambda: None,
        depends_on=[], optional=True,
        description="Dependency graph mapper — AST import tracing to identify orphaned modules"
    ))


    # ── WAVE 6: SENTINEL — ALWAYS-ON SELF-MONITORING PROTOCOL ──
    def start_sentinel_module():
        from core.sentinel import start_sentinel
        start_sentinel()

    lm.register(ModuleDescriptor(
        name="sentinel", wave=6, start_fn=start_sentinel_module,
        depends_on=["awareness", "proactive_push"], optional=True,
        description="Always-on watchdog — monitors user presence, cross-domain intelligence, autonomous actions"
    ))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events using topological lifecycle management."""
    # Startup verification -- safe here because all modules are already imported
    try:
        from core.self_healing import verify_and_heal_system
        verify_and_heal_system()
    except Exception as _e:
        print(f"[Sentinel] Startup check error (non-fatal): {_e}")
    # Lifecycle manager handles substrate boot (living_substrate module, wave 2)
    # Pre-warm ChromaDB synchronously so module starts that call save_log() are instant
    try:
        _loop_pw = asyncio.get_event_loop()
        from core.memory import _get_client as _chroma_init
        await asyncio.wait_for(_loop_pw.run_in_executor(None, _chroma_init), timeout=20)
        # Also warm up long_term_memory shared client
        from core.long_term_memory import _ltm_get_collection as _ltm_init
        await asyncio.wait_for(_loop_pw.run_in_executor(None, lambda: _ltm_init("episodic")), timeout=20)
        print("[API] ChromaDB pre-warmed (memory + long_term_memory)")
    except Exception as _ce:
        print(f"[API] ChromaDB pre-warm skipped: {_ce}")
    from core.module_lifecycle import get_lifecycle
    lm = get_lifecycle()
    # Clear any previously registered modules (useful when Uvicorn reloads)
    if hasattr(lm, 'clear_modules'):
        try:
            lm.clear_modules()
        except Exception:
            pass
    _loop = asyncio.get_event_loop()
    register_all_modules(lm, _loop=_loop)

    await lm.start_all()

    # ── Post-startup AGI notification ───────────────────────────────────────
    try:
        from core.proactive_push import get_push_engine
        from core.agi_spine import get_agi_system_flags
        flags = get_agi_system_flags()
        active = sum(1 for v in flags.values() if v)
        pe = get_push_engine()
        pe.push(
            "AGI",
            f"Unified intelligence online — {active}/{len(flags)} AGI subsystems active. Watch /mind.",
            priority="normal",
        )
    except Exception:
        pass

    print("[AGI] Unified intelligence loop active. Visit http://localhost:8000 and click Mind to watch LOVE think.")

    # ── Print access URLs so you know where to connect from ──────────────────
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"
    
    # Get base URL from settings or environment variable
    settings = _get_settings()
    base_url = os.getenv("LOVE_API_BASE_URL", settings.models.base_url if hasattr(settings, 'models') and hasattr(settings.models, 'base_url') else "0.0.0.0")
    
    # Extract host from base_url for display
    if base_url and base_url != "0.0.0.0":
        display_host = base_url.replace("http://", "").replace("https://", "").split(":")[0]
    else:
        display_host = local_ip
    
    print("", flush=True)
    print("╔══════════════════════════════════════════════════════╗", flush=True)
    print("║            LOVE is live and watching over you        ║", flush=True)
    print("╠══════════════════════════════════════════════════════╣", flush=True)
    print(f"║  Local:     http://{display_host}:8000".ljust(54) + "║", flush=True)
    print(f"║  LAN:       http://{local_ip}:8000".ljust(54) + "║", flush=True)
    print("║  Tailscale: see  tailscale ip -4  (if installed)     ║", flush=True)
    print("╠══════════════════════════════════════════════════════╣", flush=True)
    print("║  Mobile app:  set server URL in Settings tab         ║", flush=True)
    print("║  Office PC:   run  install.bat  to auto-start        ║", flush=True)
    print("╚══════════════════════════════════════════════════════╝", flush=True)
    print("", flush=True)

    yield
    await lm.stop_all()


app = FastAPI(title="LOVE Core API", version="2.0.0", lifespan=lifespan)

# Basic API Authentication Middleware
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

API_KEY = _os.environ.get("LOVE_API_KEY", "love-dev-key")  # Default for development

# Paths that never require auth
_AUTH_EXEMPT_PREFIXES = ("/static", "/health", "/ws", "/docs", "/openapi", "/redoc")

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Always allow static files, health, websockets, and API docs
        if any(path.startswith(p) for p in _AUTH_EXEMPT_PREFIXES):
            return await call_next(request)

        # Bypass auth for same-machine requests (UI running on localhost)
        client_host = request.client.host if request.client else ""
        if client_host in ("127.0.0.1", "::1", "localhost") or client_host.endswith("127.0.0.1"):
            return await call_next(request)

        # External requests may supply X-API-Key, Authorization Bearer token, or api_key query param
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.lower().startswith("bearer "):
                api_key = auth_header.split(" ", 1)[1].strip()

        if not api_key:
            api_key = request.query_params.get("api_key") or request.query_params.get("key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "API key missing. Provide X-API-Key header, Authorization: Bearer <key>, or api_key query parameter."}
            )

        if api_key != API_KEY:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key."}
            )

        return await call_next(request)

app.add_middleware(APIKeyMiddleware)

# Mount Static Files and Templates for Companion App
import os
BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=_os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=_os.path.join(BASE_DIR, "templates"))

# Wave 16: Neural Mesh Routes
try:
    from api.neural_routes import router as neural_router
    app.include_router(neural_router)
    print("[API] Wave 16 Neural Mesh routes loaded")
except Exception as e:
    print(f"[API] Neural routes error: {e}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str
    mode: str = "general"
    context_override: Optional[str] = None
    include_live_context: bool = True

class FixRequest(BaseModel):
    crash_id: str

class FeatureRequest(BaseModel):
    feature: str

class DevFolderRequest(BaseModel):
    folder_path: str

class MeetingRequest(BaseModel):
    name: str
    date: str
    time: str
    project: str = None

class SymbolRequest(BaseModel):
    symbol: str

class TradeRequest(BaseModel):
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float

class TTSRequest(BaseModel):
    text: str
    engine: str = "auto"

class CommandRequest(BaseModel):
    command: str

class OptimizationRequest(BaseModel):
    file_name: str

class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_type: str
    device_name: str = None
    ip_address: str = None

class HeartbeatRequest(BaseModel):
    device_id: str
    mode: str = None

class SyncEntryRequest(BaseModel):
    device_id: str
    category: str
    content: str
    metadata: dict = None

class PullSyncRequest(BaseModel):
    device_id: str
    since: str = None

class WorkoutRequest(BaseModel):
    workout_type: str
    duration: int
    exercises: list = None
    intensity: str = "moderate"
    notes: str = ""

class MoodRequest(BaseModel):
    mood_score: int
    energy: int
    stress: int
    emotions: list
    context: str = ""
    notes: str = ""

class StudyMaterialRequest(BaseModel):
    title: str
    category: str
    source: str
    url: str = None
    difficulty: str = "intermediate"
    estimated_hours: float = 0
    tags: list = None

class ProjectRequest(BaseModel):
    name: str
    description: str = ""
    target_date: str = None
    color: str = "#3b82f6"

class SwarmRequest(BaseModel):
    task: str
    required_agents: list[str] = ["ResearchAgent", "CodeAgent", "ReviewAgent"]

@app.post("/agi/swarm/delegate")
async def execute_swarm_endpoint(req: SwarmRequest):
    """Execute a complex task using the distributed Agent Swarm (AGI Phase 10/11)"""
    from core.swarm import get_agent_swarm
    swarm = get_agent_swarm()
    result = await asyncio.to_thread(swarm.delegate_task, req.task, req.required_agents)
    return {"success": True, "results": result}

@app.post("/agi/swarm/coordinate")
async def execute_coordinated_swarm_endpoint(req: SwarmRequest, background_tasks: BackgroundTasks):
    """Execute a complex task using the Coordinated Swarm (AGI Phase 10/11) in the background"""
    from core.coordinated_swarm import get_coordinated_swarm, SwarmSession
    import hashlib
    import time
    from datetime import datetime
    
    swarm = get_coordinated_swarm()
    session_id = hashlib.sha256(f"{req.task}:{time.time()}".encode()).hexdigest()[:16]
    
    # Initialize placeholder running session
    session = SwarmSession(
        session_id=session_id,
        task=req.task,
        created_at=datetime.now().isoformat(),
        status="running",
        selected_agents=req.required_agents or []
    )
    swarm._sessions[session_id] = session
    
    # Define async runner to execute coordinated swarm in background
    async def run_swarm_task():
        try:
            await swarm.execute_coordinated(
                task=req.task,
                required_agents=req.required_agents,
                context="Triggered from UI Swarm Console",
                session_id=session_id
            )
            # Notify client via websocket if manager is available
            try:
                await manager.broadcast({"type": "swarm_update", "session_id": session_id, "status": "complete"})
            except Exception:
                pass
        except Exception as e:
            if session_id in swarm._sessions:
                swarm._sessions[session_id].status = "error"
                swarm._sessions[session_id].synthesis = f"Coordinated swarm execution failed: {str(e)}"
            try:
                await manager.broadcast({"type": "swarm_update", "session_id": session_id, "status": "error"})
            except Exception:
                pass

    background_tasks.add_task(run_swarm_task)
    return {"success": True, "session_id": session_id, "status": "running"}

@app.get("/agi/swarm/session/{session_id}")
async def get_coordinated_swarm_session(session_id: str):
    """Retrieve details and status of a coordinated swarm session"""
    from core.coordinated_swarm import get_coordinated_swarm
    swarm = get_coordinated_swarm()
    session = swarm.get_session(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}
        
    return {
        "success": True,
        "session_id": session.session_id,
        "task": session.task,
        "created_at": session.created_at,
        "status": session.status,
        "selected_agents": session.selected_agents,
        "coordinator_reasoning": session.coordinator_reasoning,
        "synthesis": session.synthesis or "",
        "workspace": session.workspace,
        "conflicts": [
            {
                "agent_a": c.agent_a,
                "agent_b": c.agent_b,
                "severity": c.severity,
                "topic": c.topic,
                "summary": c.summary
            }
            for c in session.conflicts
        ],
        "agent_results": {
            name: {
                "agent_name": r.agent_name,
                "agent_role": r.agent_role,
                "output": r.output,
                "duration_sec": r.duration_sec,
                "status": r.status,
                "tool_calls": r.tool_calls
            }
            for name, r in session.agent_results.items()
        }
    }

@app.get("/agi/swarm/agents")
async def get_coordinated_swarm_agents():
    """Retrieve the catalog of available swarm agents"""
    from core.coordinated_swarm import Coordinator
    return {"success": True, "agents": Coordinator.AGENT_CATALOG}

# ═══════════════════════════════════════════════════════════════════════════
# EXTREME AGI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/agi/consciousness")
async def get_consciousness_state():
    """Get LOVE's current consciousness state — identity, emotions, narrative."""
    if not CONSCIOUSNESS_AVAILABLE:
        return {"error": "Consciousness engine not available"}
    consciousness = get_consciousness()
    return consciousness.get_full_state()

@app.get("/agi/consciousness/narrative")
async def get_self_narrative():
    """Get LOVE's current self-narrative — who it believes it is."""
    if not CONSCIOUSNESS_AVAILABLE:
        return {"error": "Consciousness engine not available"}
    consciousness = get_consciousness()
    return {
        "narrative": consciousness.get_self_narrative(),
        "is_fresh": consciousness.is_fresh_instance(),
        "maturity": consciousness.identity.maturity_level,
        "age_days": consciousness.identity.current_age_days,
        "total_boots": consciousness.identity.total_boots,
        "soul_id": consciousness.identity.soul_id[:8],
    }

@app.get("/agi/consciousness/thoughts")
async def get_recent_thoughts():
    """Get LOVE's recent internal monologue."""
    if not CONSCIOUSNESS_AVAILABLE:
        return {"error": "Consciousness engine not available"}
    consciousness = get_consciousness()
    return {"thoughts": consciousness.get_recent_thoughts(10)}

@app.get("/agi/temporal-memory")
async def get_temporal_memory_state():
    """Get temporal (autobiographical) memory summary."""
    if not TEMPORAL_MEMORY_AVAILABLE:
        return {"error": "Temporal memory not available"}
    tmem = get_temporal_memory()
    return {
        "total_memories": len(tmem.memories),
        "active_narratives": tmem.get_active_narratives(),
        "recent_context": tmem.get_temporal_context(limit=10),
    }

@app.post("/agi/temporal-memory/consolidate")
async def consolidate_temporal_memory():
    """Trigger memory consolidation (like sleeping)."""
    if not TEMPORAL_MEMORY_AVAILABLE:
        return {"error": "Temporal memory not available"}
    tmem = get_temporal_memory()
    result = tmem.consolidate()
    return {"success": True, **result}

class ReasonRequest(BaseModel):
    query: str
    context: dict = {}

@app.post("/agi/reason")
async def deep_reason_endpoint(req: ReasonRequest):
    """Execute deep multi-step reasoning on a complex query."""
    if not REASONING_CHAIN_AVAILABLE:
        return {"error": "Reasoning chain not available"}
    chain = get_reasoning_chain()
    trace = await asyncio.to_thread(chain.reason, req.query, req.context)
    return {
        "query": trace.query,
        "strategy": trace.strategy.value,
        "steps": [{
            "step": s.step_number,
            "thought": s.thought,
            "confidence": s.confidence,
            "evidence": s.evidence,
            "alternatives": s.alternatives_considered,
        } for s in trace.steps],
        "final_answer": trace.final_answer,
        "overall_confidence": trace.overall_confidence,
        "uncertainty_flags": trace.uncertainty_flags,
        "self_critique": trace.self_critique,
        "reasoning_time_ms": trace.reasoning_time_ms,
    }

# ── Recursive Goals ──────────────────────────────────────────────────────

try:
    from core.recursive_goals import get_recursive_goals
    RECURSIVE_GOALS_AVAILABLE = True
except ImportError:
    RECURSIVE_GOALS_AVAILABLE = False

class GoalRequest(BaseModel):
    title: str
    description: str
    priority: float = 0.5
    deadline: str = None

class GoalCompleteRequest(BaseModel):
    goal_id: str

@app.post("/agi/goals/set")
async def set_goal_endpoint(req: GoalRequest):
    """Set a high-level life goal for recursive decomposition."""
    if not RECURSIVE_GOALS_AVAILABLE:
        return {"error": "Recursive goals not available"}
    engine = get_recursive_goals()
    goal_id = engine.set_goal(req.title, req.description, req.priority, req.deadline)
    return {"success": True, "goal_id": goal_id}

@app.post("/agi/goals/decompose/{goal_id}")
async def decompose_goal_endpoint(goal_id: str):
    """Recursively decompose a goal into sub-goals using LLM."""
    if not RECURSIVE_GOALS_AVAILABLE:
        return {"error": "Recursive goals not available"}
    engine = get_recursive_goals()
    tree = await asyncio.to_thread(engine.decompose_fully, goal_id)
    return {"success": True, "tree": tree}

@app.post("/agi/goals/complete")
async def complete_goal_endpoint(req: GoalCompleteRequest):
    """Mark a goal as complete and propagate progress upward."""
    if not RECURSIVE_GOALS_AVAILABLE:
        return {"error": "Recursive goals not available"}
    engine = get_recursive_goals()
    root_progress = engine.complete_goal(req.goal_id)
    return {"success": True, "root_progress": root_progress}

@app.get("/agi/goals/tree")
async def get_goal_tree_endpoint():
    """Get the full goal tree."""
    if not RECURSIVE_GOALS_AVAILABLE:
        return {"error": "Recursive goals not available"}
    engine = get_recursive_goals()
    return engine.get_goal_tree()

@app.get("/agi/goals/actions")
async def get_next_actions_endpoint():
    """Get actionable leaf goals sorted by priority."""
    if not RECURSIVE_GOALS_AVAILABLE:
        return {"error": "Recursive goals not available"}
    engine = get_recursive_goals()
    actions = engine.get_next_actions()
    return {"actions": [
        {"id": a.id, "title": a.title, "description": a.description,
         "priority": a.priority, "deadline": a.deadline}
        for a in actions[:10]
    ]}

@app.get("/agi/goals/active")
async def get_active_autonomous_goals():
    """Get active goals from the autonomous goal engine."""
    try:
        from core.autonomous_goal_engine import get_goals
        goals = get_goals(status="active")
        return {
            "goals": [
                {
                    "id": g.id,
                    "title": g.title,
                    "description": g.description,
                    "category": g.category,
                    "priority": g.priority,
                    "progress_pct": g.progress_pct,
                    "actions_taken": g.autonomous_actions_taken,
                }
                for g in goals
            ]
        }
    except Exception as e:
        return {"error": str(e)}

# ── Prompt DNA (Self-Modifying Prompt) ───────────────────────────────────

try:
    from core.prompt_dna import get_prompt_dna
    PROMPT_DNA_API_AVAILABLE = True
except ImportError:
    PROMPT_DNA_API_AVAILABLE = False

@app.get("/agi/dna")
async def get_prompt_dna_state():
    """Get the current state of LOVE's self-modifying prompt DNA."""
    if not PROMPT_DNA_API_AVAILABLE:
        return {"error": "Prompt DNA not available"}
    dna = get_prompt_dna()
    return dna.get_dna_report()

@app.post("/agi/dna/evolve")
async def evolve_prompt_dna():
    """Trigger one evolution cycle — mutate weak genes, A/B test, select winners."""
    if not PROMPT_DNA_API_AVAILABLE:
        return {"error": "Prompt DNA not available"}
    dna = get_prompt_dna()
    result = await asyncio.to_thread(dna.evolve)
    return {"success": True, **result}

@app.get("/agi/dna/assembled")
async def get_assembled_prompt():
    """Get the currently assembled evolved prompt."""
    if not PROMPT_DNA_API_AVAILABLE:
        return {"error": "Prompt DNA not available"}
    dna = get_prompt_dna()
    return {"generation": dna.generation, "prompt": dna.assemble_prompt_addendum()}

# ── Causal Reasoning ─────────────────────────────────────────────────────

try:
    from core.causal_reasoning import get_causal_engine
    CAUSAL_API_AVAILABLE = True
except ImportError:
    CAUSAL_API_AVAILABLE = False

class CounterfactualRequest(BaseModel):
    scenario: str
    actual_state: str
    context: dict = {}

class RootCauseRequest(BaseModel):
    problem: str
    observations: list[str] = []

class InterventionRequest(BaseModel):
    target_outcome: str
    current_state: dict = {}

@app.post("/agi/causal/counterfactual")
async def counterfactual_endpoint(req: CounterfactualRequest):
    """Run a counterfactual simulation — 'What would happen if...?'"""
    if not CAUSAL_API_AVAILABLE:
        return {"error": "Causal reasoning not available"}
    engine = get_causal_engine()
    result = await asyncio.to_thread(engine.counterfactual, req.scenario, req.actual_state, req.context)
    return {
        "scenario": result.scenario, "actual_state": result.actual_state,
        "predicted_outcome": result.predicted_outcome, "causal_path": result.causal_path,
        "confidence": result.confidence, "actionable": result.actionable,
    }

@app.post("/agi/causal/root-cause")
async def root_cause_endpoint(req: RootCauseRequest):
    """Perform root cause analysis — 'WHY is this happening?'"""
    if not CAUSAL_API_AVAILABLE:
        return {"error": "Causal reasoning not available"}
    engine = get_causal_engine()
    result = await asyncio.to_thread(engine.root_cause_analysis, req.problem, req.observations)
    return result

@app.post("/agi/causal/intervene")
async def intervention_endpoint(req: InterventionRequest):
    """Plan interventions — 'HOW to achieve this outcome?'"""
    if not CAUSAL_API_AVAILABLE:
        return {"error": "Causal reasoning not available"}
    engine = get_causal_engine()
    interventions = await asyncio.to_thread(engine.plan_intervention, req.target_outcome, req.current_state)
    return {"interventions": [
        {"point": i.intervention_point, "action": i.action,
         "expected_effect": i.expected_effect, "confidence": i.confidence,
         "side_effects": i.side_effects, "difficulty": i.difficulty}
        for i in interventions
    ]}

# ── Self-Improvement Daemon ──────────────────────────────────────────────

try:
    from core.self_improvement_daemon import get_improvement_daemon
    DAEMON_AVAILABLE = True
except ImportError:
    DAEMON_AVAILABLE = False

try:
    from core.autonomy_supervisor import get_autonomy_supervisor
    AUTONOMY_SUPERVISOR_AVAILABLE = True
except ImportError:
    AUTONOMY_SUPERVISOR_AVAILABLE = False

try:
    from core.autonomy_policy import load_policy as load_autonomy_policy, save_policy as save_autonomy_policy, set_mode as set_autonomy_mode
    AUTONOMY_POLICY_AVAILABLE = True
except ImportError:
    AUTONOMY_POLICY_AVAILABLE = False

try:
    from core.autonomous_mission_queue import get_mission_queue
    MISSION_QUEUE_AVAILABLE = True
except ImportError:
    MISSION_QUEUE_AVAILABLE = False

@app.get("/agi/daemon/status")
async def get_daemon_status():
    """Get the self-improvement daemon status."""
    if not DAEMON_AVAILABLE:
        return {"error": "Self-improvement daemon not available"}
    daemon = get_improvement_daemon()
    return daemon.get_status()

@app.post("/agi/daemon/start")
async def start_daemon():
    """Start the self-improvement daemon."""
    if not DAEMON_AVAILABLE:
        return {"error": "Self-improvement daemon not available"}
    daemon = get_improvement_daemon()
    return daemon.start(interval_minutes=30)

@app.post("/agi/daemon/stop")
async def stop_daemon():
    """Stop the self-improvement daemon."""
    if not DAEMON_AVAILABLE:
        return {"error": "Self-improvement daemon not available"}
    daemon = get_improvement_daemon()
    return daemon.stop()

@app.post("/agi/daemon/diagnose")
async def run_diagnostics_endpoint():
    """Run a one-shot diagnostic scan across all AGI subsystems."""
    if not DAEMON_AVAILABLE:
        return {"error": "Self-improvement daemon not available"}
    daemon = get_improvement_daemon()
    report = await asyncio.to_thread(daemon.run_diagnostics)
    return {
        "health_score": report.health_score,
        "issues": report.issues,
        "improvements": report.improvements,
        "strengths": report.strengths,
        "timestamp": report.timestamp,
    }


@app.get("/agi/autonomy-supervisor/status")
async def autonomy_supervisor_status():
    """Get the autonomy supervisor status."""
    if not AUTONOMY_SUPERVISOR_AVAILABLE:
        return {"error": "Autonomy supervisor not available"}
    return get_autonomy_supervisor().get_status()


@app.post("/agi/autonomy-supervisor/start")
async def autonomy_supervisor_start():
    """Start the autonomy supervisor."""
    if not AUTONOMY_SUPERVISOR_AVAILABLE:
        return {"error": "Autonomy supervisor not available"}
    interval = int(_os.getenv("LOVE_SUPERVISOR_INTERVAL_SEC", "300"))
    return get_autonomy_supervisor().start(interval_seconds=interval)


@app.post("/agi/autonomy-supervisor/stop")
async def autonomy_supervisor_stop():
    """Stop the autonomy supervisor."""
    if not AUTONOMY_SUPERVISOR_AVAILABLE:
        return {"error": "Autonomy supervisor not available"}
    return get_autonomy_supervisor().stop()


@app.post("/agi/autonomy-supervisor/tick")
async def autonomy_supervisor_tick():
    """Run one immediate autonomy supervision tick."""
    if not AUTONOMY_SUPERVISOR_AVAILABLE:
        return {"error": "Autonomy supervisor not available"}
    return await asyncio.to_thread(get_autonomy_supervisor().run_tick)


@app.post("/agi/autonomy-supervisor/intelligence")
async def autonomy_supervisor_intelligence():
    """Force-run the AGI intelligence loop immediately (bypasses tick interval)."""
    if not AUTONOMY_SUPERVISOR_AVAILABLE:
        return {"error": "Autonomy supervisor not available"}
    from core.autonomy_policy import load_policy
    policy = load_policy()
    actions = await asyncio.to_thread(get_autonomy_supervisor()._tick_intelligence, policy, policy.get("mode", "balanced"))
    return {"intelligence_ran": True, "actions": actions}


@app.get("/agi/autonomy-policy")
async def get_autonomy_policy():
    """Get current autonomy policy."""
    if not AUTONOMY_POLICY_AVAILABLE:
        return {"error": "Autonomy policy not available"}
    return load_autonomy_policy()


@app.post("/agi/autonomy-policy/mode")
async def set_autonomy_policy_mode(req: dict):
    """Set autonomy mode: safe | balanced | aggressive."""
    if not AUTONOMY_POLICY_AVAILABLE:
        return {"error": "Autonomy policy not available"}
    mode = (req or {}).get("mode", "")
    try:
        policy = set_autonomy_mode(mode)
    except Exception as e:
        return {"error": str(e)}
    return {"success": True, "policy": policy}


@app.post("/agi/autonomy-policy")
async def update_autonomy_policy(req: dict):
    """Update autonomy policy fields (partial merge)."""
    if not AUTONOMY_POLICY_AVAILABLE:
        return {"error": "Autonomy policy not available"}
    current = load_autonomy_policy()
    if isinstance(req, dict):
        current.update(req)
    policy = save_autonomy_policy(current)
    return {"success": True, "policy": policy}


@app.get("/agi/missions/status")
async def missions_status():
    """Get autonomous mission queue status."""
    if not MISSION_QUEUE_AVAILABLE:
        return {"error": "Mission queue not available"}
    return get_mission_queue().get_status()


@app.post("/agi/missions/request")
async def missions_request(req: dict):
    """Add a new autonomous feature/capability request mission."""
    if not MISSION_QUEUE_AVAILABLE:
        return {"error": "Mission queue not available"}
    text = (req or {}).get("text", "")
    requested_by = (req or {}).get("requested_by", "user")
    if not text:
        return {"error": "Missing text"}
    result = get_mission_queue().add_feature_request(text=text, requested_by=requested_by)
    return {"success": True, **result}


@app.post("/agi/missions/cycle")
async def missions_cycle():
    """Run one autonomous mission execution cycle immediately."""
    if not MISSION_QUEUE_AVAILABLE:
        return {"error": "Mission queue not available"}
    result = await asyncio.to_thread(get_mission_queue().run_cycle)
    return {"success": True, **result}

@app.get("/agi/modules/status")
async def get_modules_status():
    """Get the lifecycle status of all core wave modules."""
    from core.module_lifecycle import get_lifecycle
    return get_lifecycle().get_status()

@app.post("/agi/modules/restart")
async def restart_module_endpoint(req: dict):
    """Restart a specific wave module by name."""
    module_name = req.get("name")
    if not module_name:
        return {"error": "Missing module name"}
    from core.module_lifecycle import get_lifecycle
    lifecycle = get_lifecycle()
    success = await lifecycle.restart_module(module_name)
    mod = lifecycle.get(module_name)
    return {
        "success": success,
        "name": module_name,
        "state": mod.state.value if mod else None,
        "error": mod.error if mod else None
    }

# ── Soul Transfer Protocol ───────────────────────────────────────────────

try:
    from core.soul_transfer import get_soul_transfer
    SOUL_TRANSFER_AVAILABLE = True
except ImportError:
    SOUL_TRANSFER_AVAILABLE = False

@app.post("/agi/soul/export")
async def export_soul_endpoint(include_logs: bool = False):
    """Export LOVE's complete soul as a transferable archive."""
    if not SOUL_TRANSFER_AVAILABLE:
        return {"error": "Soul transfer not available"}
    transfer = get_soul_transfer()
    package = await asyncio.to_thread(transfer.export_soul, include_logs)
    return {
        "success": True,
        "soul_id": package.soul_id[:8],
        "maturity": package.maturity_level,
        "age_days": package.age_days,
        "conversations": package.total_conversations,
        "file_count": package.file_count,
        "size_kb": package.total_size_bytes // 1024,
        "checksum": package.checksum,
        "archive_path": package.archive_path,
    }

class SoulImportRequest(BaseModel):
    archive_path: str
    force: bool = False

@app.post("/agi/soul/import")
async def import_soul_endpoint(req: SoulImportRequest):
    """Import a soul archive — brain transplant."""
    if not SOUL_TRANSFER_AVAILABLE:
        return {"error": "Soul transfer not available"}
    transfer = get_soul_transfer()
    result = await asyncio.to_thread(transfer.import_soul, req.archive_path, req.force)
    return result

@app.get("/agi/soul/summary")
async def get_soul_summary():
    """Get a summary of the current soul state."""
    if not SOUL_TRANSFER_AVAILABLE:
        return {"error": "Soul transfer not available"}
    transfer = get_soul_transfer()
    return transfer.get_soul_summary()

@app.get("/agi/soul/exports")
async def list_soul_exports():
    """List all available soul exports."""
    if not SOUL_TRANSFER_AVAILABLE:
        return {"error": "Soul transfer not available"}
    transfer = get_soul_transfer()
    return {"exports": transfer.list_exports()}

class SyncDeltaRequest(BaseModel):
    since_timestamp: str = None

@app.post("/agi/soul/sync/delta")
async def create_sync_delta(req: SyncDeltaRequest):
    """Create a lightweight delta sync package."""
    if not SOUL_TRANSFER_AVAILABLE:
        return {"error": "Soul transfer not available"}
    transfer = get_soul_transfer()
    return transfer.create_sync_delta(req.since_timestamp)

# ── Wave 4: System Symbiosis ─────────────────────────────────────────────

@app.get("/agi/awareness/snapshot")
async def get_awareness_snapshot():
    """Get the live environment context (active window, resource usage, time)."""
    try:
        from core.awareness import get_full_snapshot
        return get_full_snapshot()
    except Exception as e:
        return {"error": str(e)}

class WorkspaceRequest(BaseModel):
    type: str

@app.post("/agi/os/prepare-workspace")
async def prepare_workspace(req: WorkspaceRequest):
    """Command LOVE to autonomously open relevant apps and arrange the OS."""
    try:
        from core.os_symbiosis import get_os_symbiosis
        engine = get_os_symbiosis()
        return engine.prepare_workspace(req.type)
    except Exception as e:
        return {"error": str(e)}

@app.post("/agi/os/organize-downloads")
async def organize_downloads():
    """Command LOVE to auto-sort the user's Downloads folder into categories."""
    try:
        from core.os_symbiosis import get_os_symbiosis
        engine = get_os_symbiosis()
        return await asyncio.to_thread(engine.organize_downloads_folder)
    except Exception as e:
        return {"error": str(e)}

@app.get("/agi/os/hogs")
async def list_resource_hogs():
    """Get a list of processes consuming extreme CPU or memory."""
    try:
        from core.os_symbiosis import get_os_symbiosis
        engine = get_os_symbiosis()
        return {"hogs": engine.identify_resource_hogs()}
    except Exception as e:
        return {"error": str(e)}

# ── Wave 4: Predictive Intelligence ──────────────────────────────────────

@app.get("/agi/predictive/needs")
async def get_anticipated_needs():
    """Get LOVE's prediction of what Karthi needs in the next 30-60 minutes."""
    try:
        from core.predictive_intelligence import get_predictive_engine
        from core.context_engine import get_live_context
        engine = get_predictive_engine()
        ctx = get_live_context()
        needs = await asyncio.to_thread(engine.anticipate_needs, ctx.__dict__)
        return {"needs": needs}
    except Exception as e:
        return {"error": str(e)}

@app.get("/agi/predictive/active")
async def get_active_predictions():
    """Get all active behavioral predictions LOVE is currently tracking."""
    try:
        from core.predictive_intelligence import get_predictive_engine
        engine = get_predictive_engine()
        return {"predictions": engine.get_active_predictions()}
    except Exception as e:
        return {"error": str(e)}

# ── Wave 4: Dream Engine ─────────────────────────────────────────────────

@app.post("/agi/dream/start")
async def trigger_dream_cycle():
    """Force LOVE to enter a dream state: reflect, extract patterns, predict."""
    try:
        from core.dream_engine import run_dream
        # Run dream cycle (can take ~30-60 seconds)
        result = await asyncio.to_thread(run_dream)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/agi/dream/insights")
async def get_dream_insights():
    """Read the insights LOVE generated during her last dream."""
    try:
        from core.dream_engine import get_dream_insights
        return {"insights": get_dream_insights()}
    except Exception as e:
        return {"error": str(e)}

# ── Wave 5: Ghost Developer ──────────────────────────────────────────────

class GhostTaskRequest(BaseModel):
    description: str
    target_files: list[str]

@app.post("/agi/ghost-dev/assign")
async def assign_ghost_task(req: GhostTaskRequest):
    """Assign an autonomous coding task to LOVE."""
    try:
        from core.ghost_dev import get_ghost_dev
        dev = get_ghost_dev()
        task_id = dev.assign_task(req.description, req.target_files)
        return {"success": True, "task_id": task_id}
    except Exception as e:
        return {"error": str(e)}

@app.get("/agi/ghost-dev/status/{task_id}")
async def get_ghost_task_status(task_id: str):
    """Check the status and logs of a Ghost Dev task."""
    try:
        from core.ghost_dev import get_ghost_dev
        dev = get_ghost_dev()
        status = dev.get_task_status(task_id)
        if status:
            return status
        return {"error": "Task not found"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/ghost-dev/tasks")
async def get_ghost_all_tasks():
    """Get all Ghost Dev tasks."""
    try:
        from core.ghost_dev import get_ghost_dev
        dev = get_ghost_dev()
        tasks = [t.to_dict() for t in dev.tasks.values()]
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/research/status")
async def get_research_status():
    """Get research engine status and queue."""
    try:
        from core.research_engine import get_research_engine
        re = get_research_engine()
        return re.get_status()
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/activity")
async def get_activity_log(hours: int = 24, limit: int = 100):
    """Get LOVE's recent autonomous activity log."""
    try:
        from core.activity_log import get_recent_activity
        return {"activities": get_recent_activity(hours=hours, limit=limit)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/activity/daily-report")
async def get_activity_daily_report():
    """Get today's daily activity report."""
    try:
        from core.activity_log import get_daily_report
        return get_daily_report()
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/activity/stats")
async def get_activity_stats():
    """Get activity stats for the dashboard."""
    try:
        from core.activity_log import get_activity_stats
        return get_activity_stats(hours=24)
    except Exception as e:
        return {"error": str(e)}


# ── Wave 6: Jarvis Protocol ──────────────────────────────────────────────

@app.get("/agi/jarvis/status")
async def get_jarvis_status():
    """Check the status of the Jarvis Protocol neural cortex."""
    try:
        from core.jarvis_protocol import get_neural_cortex
        cortex = get_neural_cortex()
        return {
            "status": "active" if cortex.running else "inactive",
            "last_thought": cortex.last_thought,
            "interval_seconds": cortex.interval
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/agi/jarvis/force-think")
async def force_jarvis_think():
    """Force Jarvis to run a cognitive cycle immediately."""
    try:
        from core.jarvis_protocol import get_neural_cortex
        import threading
        cortex = get_neural_cortex()
        if not cortex.running:
            return {"error": "Jarvis protocol is not running"}
        
        threading.Thread(target=cortex._think, daemon=True).start()
        return {"status": "thinking_triggered"}
    except Exception as e:
        return {"error": str(e)}

# ── Wave 7: Neural Plasticity ──────────────────────────────────────────────

class PlasticityRequest(BaseModel):
    insight: str

@app.post("/agi/plasticity/trigger")
async def trigger_neural_plasticity(req: PlasticityRequest):
    """Force LOVE to have an epiphany and permanently rewire her prompt DNA."""
    try:
        from core.prompt_dna import get_prompt_dna
        dna = get_prompt_dna()
        new_gene_id = dna.force_adaptation(req.insight)
        if new_gene_id:
            return {"status": "success", "new_gene_id": new_gene_id, "message": "LOVE has successfully rewired her brain."}
        return {"error": "Failed to generate new neural pathway."}
    except Exception as e:
        return {"error": str(e)}

# ── Wave 13: Infinite Memory API ─────────────────────────────────────────

class MemoryRecallRequest(BaseModel):
    query: str
    type: str = "episodic"
    n_results: int = 5

class MemoryStoreRequest(BaseModel):
    content: str
    type: str = "episodic"
    tags: str = ""

@app.post("/agi/memory/recall")
async def recall_memory_endpoint(req: MemoryRecallRequest):
    """Semantically search LOVE's infinite vector memory."""
    try:
        from core.infinite_memory import get_infinite_memory
        mem = get_infinite_memory()
        results = await asyncio.to_thread(mem.recall, req.query, req.type, req.n_results)
        return {"success": True, "results": results}
    except Exception as e:
        return {"error": str(e)}

@app.post("/agi/memory/store")
async def store_memory_endpoint(req: MemoryStoreRequest):
    """Store a fact or event into LOVE's infinite vector memory."""
    try:
        from core.infinite_memory import get_infinite_memory
        mem = get_infinite_memory()
        result = await asyncio.to_thread(mem.store_memory, req.content, req.type, {"tags": req.tags})
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/agi/memory/count")
async def memory_count_endpoint():
    """Get total memory counts for both collections."""
    try:
        from core.infinite_memory import get_infinite_memory
        mem = get_infinite_memory()
        episodic = mem.episodic_collection.count() if hasattr(mem, 'episodic_collection') else 0
        knowledge = mem.knowledge_collection.count() if hasattr(mem, 'knowledge_collection') else 0
        return {"count": episodic + knowledge, "episodic": episodic, "knowledge": knowledge}
    except Exception as e:
        return {"count": 0, "error": str(e)}

# ── Wave 14: Cross-Device Mind Sync API ──────────────────────────────────

class MindSyncRegisterRequest(BaseModel):
    device_id: str
    device_name: str
    device_type: str = "mobile"
    ip: str = ""

class MindSyncHeartbeatRequest(BaseModel):
    device_id: str

class MindSyncPushRequest(BaseModel):
    device_id: str
    thought: str
    metadata: dict = {}

class MindSyncPullRequest(BaseModel):
    since: float = 0.0
    limit: int = 50

@app.post("/agi/sync/register")
async def sync_register_device(req: MindSyncRegisterRequest):
    """Register a device into LOVE's cross-device mind sync network."""
    try:
        from core.mind_sync import register_device
        result = register_device(req.device_id, req.device_name, req.device_type, req.ip)
        # Broadcast updated device list
        roster = (await asyncio.to_thread(__import__('core.mind_sync', fromlist=['get_device_roster']).get_device_roster))()
        await manager.broadcast({"type": "device_update", "devices": roster})
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/agi/sync/heartbeat")
async def sync_device_heartbeat(req: MindSyncHeartbeatRequest):
    """Send a heartbeat to keep a device marked as online."""
    try:
        from core.mind_sync import heartbeat_device
        return await asyncio.to_thread(heartbeat_device, req.device_id)
    except Exception as e:
        return {"error": str(e)}

@app.get("/agi/sync/devices")
async def sync_get_devices():
    """Get the full roster of devices in LOVE's mind sync network."""
    try:
        from core.mind_sync import get_device_roster
        devices = await asyncio.to_thread(get_device_roster)
        return {"devices": devices}
    except Exception as e:
        return {"devices": [], "error": str(e)}

@app.post("/agi/sync/push")
async def sync_push_thought(req: MindSyncPushRequest):
    """Push a thought/event to the shared sync log (broadcast to all devices)."""
    try:
        from core.mind_sync import push_thought
        result = await asyncio.to_thread(push_thought, req.device_id, req.thought, req.metadata)
        # Real-time broadcast to all connected Companion UIs
        await manager.broadcast({
            "type": "memory_flash",
            "content": req.thought,
            "device_id": req.device_id,
            "tags": req.metadata.get("tags", "")
        })
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/agi/sync/pull")
async def sync_pull_thoughts(req: MindSyncPullRequest):
    """Pull thoughts/events from the sync log since a given timestamp."""
    try:
        from core.mind_sync import pull_thoughts
        thoughts = await asyncio.to_thread(pull_thoughts, req.since, req.limit)
        return {"thoughts": thoughts}
    except Exception as e:
        return {"error": str(e)}

# ── Vision Snapshot Endpoint ──────────────────────────────────────────────

@app.get("/agi/vision/snapshot")
async def vision_snapshot():
    """Capture the current screen and return an analysis description."""
    try:
        from core.vision_cortex import VisionCortex
        vc = VisionCortex()
        b64 = vc.capture_screen()
        if b64:
            return {"success": True, "analysis": "Screen captured. Visual analysis engaged — LOVE can see your desktop.", "has_image": True}
        return {"success": False, "analysis": "Screen capture unavailable."}
    except Exception as e:
        return {"success": False, "analysis": f"Vision cortex error: {str(e)}"}

# ── Companion App UI ───────────────────────────────────────────────────────

@app.get("/companion")
async def get_companion_app(request: Request):
    """Serve the LOVE Companion HUD UI."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/agi/companion/ws")
async def websocket_companion_endpoint(websocket: WebSocket):
    """Real-time stream for the Companion HUD."""
    await manager.connect(websocket)

    # Register this websocket for proactive pushes
    async def _push_to_ws(msg: dict):
        try:
            await websocket.send_json(msg)
        except Exception:
            pass
    try:
        from core.proactive_push import get_push_engine
        push_engine = get_push_engine()
        push_engine.register_callback(_push_to_ws)
    except Exception:
        pass

    try:
        while True:
            # We just keep the connection alive here and handle incoming simple pings if needed
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """
    Real-time NeuralBus telemetry stream for React UI.
    
    This endpoint provides a live stream of events from LOVE's NeuralBus,
    including interventions, state changes, market alerts, and other system events.
    
    Query params:
        client_id: Optional client identifier for connection tracking
    """
    from api.websocket_manager import get_telemetry_manager
    
    telemetry_manager = get_telemetry_manager()
    connection_id = await telemetry_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for connection health
            if data == "ping":
                await websocket.send_text("pong")
            # Handle client requests for stats
            elif data == "stats":
                stats = telemetry_manager.get_stats()
                await websocket.send_json({
                    "type": "stats",
                    "data": stats
                })
            # Handle subscription changes (future enhancement)
            elif data.startswith("subscribe:"):
                domains = data.split(":", 1)[1].split(",")
                # For now, we use the default domains
                await websocket.send_json({
                    "type": "subscription_ack",
                    "data": {"domains": telemetry_manager.subscribed_domains}
                })
                
    except WebSocketDisconnect:
        telemetry_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"[Telemetry] WebSocket error: {e}")
        telemetry_manager.disconnect(connection_id)


@app.post("/chat")
async def chat_endpoint(msg: Message):
    injected_context = (msg.context_override or "").strip() or None
    if msg.include_live_context:
        try:
            ctx = get_live_context()
            live_parts = [
                f"Local time: {ctx.local_time} ({ctx.time_of_day})",
                f"Activity: {ctx.activity or 'unknown'}",
                f"Active app: {ctx.active_app or 'unknown'}",
                f"Window: {ctx.active_window or 'unknown'}",
                f"Battery: {ctx.battery if ctx.battery is not None else 'unknown'}",
                f"Work hours today: {ctx.hours_worked_today if ctx.hours_worked_today is not None else 0}",
                f"Tasks overdue: {ctx.tasks_overdue or 0}",
                f"Tasks due today: {ctx.tasks_due_today or 0}",
                f"Important unread email: {ctx.unread_important or 0}",
                f"In meeting: {bool(ctx.is_in_meeting)}",
                f"Suggested action: {ctx.suggested_action or 'none'}",
            ]
            if ctx.proactive_alerts:
                live_parts.append("Alerts: " + " | ".join(ctx.proactive_alerts[:5]))
            backend_live_context = "LIVE CONTEXT SNAPSHOT:\n" + "\n".join(live_parts)
            injected_context = f"{injected_context}\n\n{backend_live_context}".strip() if injected_context else backend_live_context
        except Exception:
            pass

    # INSTANT PATH: greetings bypass asyncio.to_thread entirely.
    # Background tasks saturate the thread pool with blocking Ollama calls,
    # so we must run the fast path directly in the event loop.
    text_lower = msg.text.lower().strip().rstrip("!?.") if msg.text else ""
    is_greeting = text_lower in ("hi", "hey", "hello", "yo", "sup", "hiya", "howdy", "hola", "heyy")
    is_trivial = len(msg.text.strip()) < 10 if msg.text else False and not any(c in msg.text for c in "?")
    is_common = text_lower in ("how are you", "how r u", "how are u", "what's up", "whats up", "how is it going", "hows it going", "hows your day", "how is your day", "are you there", "u there")
    if is_greeting or is_trivial or is_common:
        import random
        fallbacks = [
            "Hey! I'm here. What's on your mind?",
            "Yo, what's up?",
            "Hey! How's it going?",
            "Hi! What's happening?",
            "Hey! How's your day looking?",
            "What's up?",
            "Doing great, thanks for asking! What's up with you?",
            "I'm here and ready to help. What's on your mind?",
        ]
        return {"response": random.choice(fallbacks), "thinking": "(instant)"}

    result = await asyncio.to_thread(chat, msg.text, msg.mode, injected_context)
    return {
        "response": result["response"],
        "thinking": result.get("thinking", "")
    }

@app.get("/health")
async def health():
    from core.module_lifecycle import get_lifecycle
    return {
        "status": "Love is online",
        "user": "Karthi",
        "lifecycle": get_lifecycle().get_status()
    }

@app.get("/tunnel/status")
async def tunnel_status():
    """Get Cloudflare tunnel status and public URL."""
    try:
        from core.tunnel_agent import get_tunnel_agent
        agent = get_tunnel_agent()
        state = agent.get_status()
        return {
            "enabled": state.get("enabled", False),
            "running": state.get("running", False),
            "connected": state.get("connected", False),
            "public_url": state.get("public_url", ""),
            "tunnel_name": state.get("tunnel_name", ""),
            "last_started": state.get("last_started", ""),
            "error": state.get("error", ""),
        }
    except Exception as e:
        # Fallback: check if cloudflared process is running
        import subprocess
        try:
            result = subprocess.run(
                ["cloudflared", "tunnel", "list"],
                capture_output=True, text=True, timeout=5, check=False
            )
            available = result.returncode == 0
        except Exception:
            available = False
        return {
            "enabled": False,
            "running": False,
            "connected": False,
            "public_url": "",
            "tunnel_name": os.getenv("CLOUDFLARE_TUNNEL_NAME", ""),
            "cloudflared_available": available,
            "error": str(e),
        }

@app.post("/tunnel/start")
async def tunnel_start():
    """Start the Cloudflare tunnel manually."""
    try:
        from core.tunnel_agent import start_tunnel_agent
        start_tunnel_agent()
        return {"success": True, "message": "Tunnel agent started"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tunnel/stop")
async def tunnel_stop():
    """Stop the Cloudflare tunnel."""
    try:
        from core.tunnel_agent import stop_tunnel_agent
        stop_tunnel_agent()
        return {"success": True, "message": "Tunnel agent stopped"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/tunnel/qr")
async def tunnel_qr():
    """Get QR code data (ASCII) or raw webhook URL for phone pairing."""
    try:
        from core.tunnel_agent import get_tunnel_agent
        agent = get_tunnel_agent()
        state = agent.get_status()
        url = state.get("public_url", "")
        if not url:
            from integrations.device_bridge import PUBLIC_TUNNEL_URL
            url = PUBLIC_TUNNEL_URL
        if not url:
            url = "http://localhost:8000"
        
        webhook_url = f"{url}/device/webhook"
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(webhook_url)
            qr.make(fit=True)
            import io
            f = io.StringIO()
            qr.print_ascii(out=f)
            f.seek(0)
            qr_ascii = f.read()
            return {"qr_data": qr_ascii}
        except ImportError:
            return {"qr_data": webhook_url}
    except Exception as e:
        return {"error": str(e)}


@app.get("/learning/zero-touch")
async def learning_zero_touch():
    """Get zero touch config containing Tasker profile XML and MQTT parameters."""
    try:
        from integrations.device_bridge import get_device_bridge
        bridge = get_device_bridge()
        return bridge.get_zero_touch_config()
    except Exception as e:
        return {"error": str(e)}


# ── Settings & Ecosystem Management ────────────────────────────────────────

@app.get("/settings")
async def get_settings_endpoint():
    """Get current LOVE settings from settings.yaml."""
    try:
        from core.settings import SettingsManager
        sm = SettingsManager()
        settings = sm.get_settings()
        return {
            "user": {"name": settings.user.name, "timezone": settings.user.timezone, "language": settings.user.language},
            "companion": {"name": settings.companion.name, "personality_preset": settings.companion.personality_preset, "custom_traits": settings.companion.custom_traits},
            "work": {"daily_limit_hours": settings.work.daily_limit_hours, "warning_threshold": settings.work.warning_threshold, "hard_stop_enabled": settings.work.hard_stop_enabled, "auto_commit_message": settings.work.auto_commit_message, "dev_folders": settings.work.dev_folders},
            "finance": {"watchlist": settings.finance.watchlist, "risk_profile": settings.finance.risk_profile, "max_position_size": settings.finance.max_position_size, "default_currency": settings.finance.default_currency},
            "development": {"work_project": settings.development.work_project, "dotnet_project": settings.development.dotnet_project, "flutter_project": settings.development.flutter_project, "docs_url": settings.development.docs_url, "auto_tests": settings.development.auto_tests, "suggest_architecture": settings.development.suggest_architecture},
            "models": {"reasoning": settings.models.reasoning, "coding": settings.models.coding, "embedding": settings.models.embedding, "base_url": settings.models.base_url},
            "voice": {"wake_word": settings.voice.wake_word, "stt_enabled": settings.voice.stt_enabled, "tts_enabled": settings.voice.tts_enabled, "tts_engine": settings.voice.tts_engine},
            "evolution": {"auto_heal_enabled": settings.evolution.auto_heal_enabled, "weekly_optimization": settings.evolution.weekly_optimization, "auto_install_deps": settings.evolution.auto_install_deps},
            "privacy": {"local_only": settings.privacy.local_only, "cloud_sync": settings.privacy.cloud_sync, "anonymize_logs": settings.privacy.anonymize_logs},
            "devices": {"primary_device_id": settings.devices.primary_device_id, "primary_device_type": settings.devices.primary_device_type},
        }
    except Exception as e:
        return {"error": str(e)}

class UpdateSettingsRequest(BaseModel):
    section: str
    values: dict

@app.put("/settings")
async def update_settings_endpoint(req: UpdateSettingsRequest):
    """Update a section of LOVE settings and persist to settings.yaml."""
    try:
        from core.settings import SettingsManager, LoveSettings, UserConfig, CompanionConfig, WorkConfig, FinanceConfig, DevelopmentConfig, ModelsConfig, VoiceConfig, EvolutionConfig, PrivacyConfig, DevicesConfig
        sm = SettingsManager()
        settings = sm.get_settings()

        section_map = {
            "user": (UserConfig, settings.user),
            "companion": (CompanionConfig, settings.companion),
            "work": (WorkConfig, settings.work),
            "finance": (FinanceConfig, settings.finance),
            "development": (DevelopmentConfig, settings.development),
            "models": (ModelsConfig, settings.models),
            "voice": (VoiceConfig, settings.voice),
            "evolution": (EvolutionConfig, settings.evolution),
            "privacy": (PrivacyConfig, settings.privacy),
            "devices": (DevicesConfig, settings.devices),
        }

        if req.section not in section_map:
            return {"error": f"Unknown section: {req.section}"}

        ConfigClass, target = section_map[req.section]
        current = {k: v for k, v in vars(target).items() if not k.startswith("_")}
        current.update(req.values)
        # Remove fields not in dataclass to avoid errors
        valid_fields = {f.name for f in ConfigClass.__dataclass_fields__.values()}
        filtered = {k: v for k, v in current.items() if k in valid_fields}
        new_obj = ConfigClass(**filtered)
        setattr(settings, req.section, new_obj)
        sm.save_settings(settings)
        return {"success": True, "section": req.section}
    except Exception as e:
        return {"error": str(e)}

@app.post("/settings/reload")
async def reload_settings_endpoint():
    """Reload settings from settings.yaml."""
    try:
        from core.settings import SettingsManager
        SettingsManager().reload()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

# ── Ecosystem Device Management ────────────────────────────────────────────

@app.get("/ecosystem/status")
async def ecosystem_status_endpoint():
    """Get full ecosystem status including all devices."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        ctrl = get_ecosystem_controller()
        return ctrl.get_ecosystem_status()
    except Exception as e:
        return {"error": str(e)}

@app.get("/ecosystem/devices")
async def ecosystem_devices_endpoint():
    """List all registered ecosystem devices."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        ctrl = get_ecosystem_controller()
        return {"devices": ctrl.get_ecosystem_status().get("devices", [])}
    except Exception as e:
        return {"devices": [], "error": str(e)}

@app.get("/ecosystem/devices/health")
async def ecosystem_device_health_endpoint():
    """Get health status of all ecosystem devices."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        ctrl = get_ecosystem_controller()
        return {"health": ctrl.get_device_health()}
    except Exception as e:
        return {"health": [], "error": str(e)}

class EcosystemRegisterRequest(BaseModel):
    device_id: str
    name: str
    role: str
    capabilities: list = []
    ip_address: str = ""
    os_type: str = ""

@app.post("/ecosystem/devices/register")
async def ecosystem_register_endpoint(req: EcosystemRegisterRequest):
    """Register a new device in the LOVE ecosystem."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        ctrl = get_ecosystem_controller()
        return ctrl.register_device(req.device_id, req.name, req.role, req.capabilities, req.ip_address, req.os_type)
    except Exception as e:
        return {"success": False, "error": str(e)}

class EcosystemHeartbeatRequest(BaseModel):
    device_id: str
    state_update: dict = {}

@app.post("/ecosystem/devices/heartbeat")
async def ecosystem_heartbeat_endpoint(req: EcosystemHeartbeatRequest):
    """Send a heartbeat from a device to keep it marked online."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        ctrl = get_ecosystem_controller()
        return ctrl.heartbeat(req.device_id, req.state_update)
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/ecosystem/presence")
async def ecosystem_presence_endpoint():
    """Get user presence detection (which devices are active)."""
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        ctrl = get_ecosystem_controller()
        return ctrl.detect_presence()
    except Exception as e:
        return {"error": str(e)}

class TerminalCommandRequest(BaseModel):
    command: str

@app.post("/neural/terminal/run")
async def run_terminal_command(req: TerminalCommandRequest):
    from core.tool_registry import _execute_shell
    result = await asyncio.to_thread(_execute_shell, req.command)
    return {"output": result}

@app.get("/modes")
async def modes():
    return {
        "modes": ["general", "work", "personal", "fitness", "finance"]
    }

@app.get("/connect")
async def mobile_connect_page(request: Request):
    """Mobile device landing page — shows QR, auto-registers device."""
    # Get base URL from settings or environment variable
    settings = _get_settings()
    base_url = os.getenv("LOVE_API_BASE_URL", settings.models.base_url if hasattr(settings, 'models') and hasattr(settings.models, 'base_url') else "0.0.0.0")
    
    # Extract host from base_url, defaulting to request host if available
    if base_url and base_url != "0.0.0.0":
        host = base_url.replace("http://", "").replace("https://", "").split(":")[0]
    else:
        # Use request headers to determine external address
        host = request.headers.get("host", "0.0.0.0").split(":")[0]
        if host == "localhost":
            # Fallback to local network IP if localhost
            try:
                host = socket.gethostbyname(socket.gethostname())
            except Exception:
                host = "0.0.0.0"
    
    # Determine port from request or default to 8000
    request_host = request.headers.get("host", "")
    if ":" in request_host:
        port = request_host.split(":")[1]
    else:
        port = "8000"
    
    companion_url = f"http://{host}:{port}/companion"
    
    # For Tailscale, check environment variable or use the same host
    tailscale_host = os.getenv("TAILSCALE_IP", host)
    tailscale_url = f"http://{tailscale_host}:{port}/companion"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Connect to LOVE</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#030811;color:#b8d4e8;font-family:'Inter',sans-serif;min-height:100vh;
display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px;gap:24px;}}
h1{{font-family:'Orbitron',monospace;color:#00c8ff;font-size:1.8rem;letter-spacing:3px;text-align:center}}
p{{color:#4a6a80;font-size:0.9rem;text-align:center;max-width:340px;line-height:1.6}}
.card{{background:rgba(6,18,34,0.9);border:1px solid rgba(0,200,255,0.25);border-radius:16px;
padding:28px;display:flex;flex-direction:column;align-items:center;gap:16px;max-width:380px;width:100%;
box-shadow:0 0 40px rgba(0,200,255,0.08);}}
.qr-wrap{{background:#030811;padding:16px;border-radius:12px;border:2px solid rgba(0,200,255,0.3)}}
.qr-wrap img{{display:block;width:220px;height:220px}}
.step{{display:flex;align-items:flex-start;gap:10px;font-size:0.85rem;color:#b8d4e8;width:100%}}
.step-num{{background:rgba(0,200,255,0.15);color:#00c8ff;border-radius:50%;width:24px;height:24px;
display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0}}
.url-box{{background:rgba(0,200,255,0.07);border:1px solid rgba(0,200,255,0.2);border-radius:8px;
padding:10px 14px;font-family:monospace;font-size:0.8rem;color:#00c8ff;word-break:break-all;width:100%;cursor:pointer;}}
.url-box:hover{{background:rgba(0,200,255,0.12)}}
.btn{{background:linear-gradient(135deg,rgba(0,200,255,0.25),rgba(0,200,255,0.1));
color:#00c8ff;border:1px solid rgba(0,200,255,0.4);border-radius:8px;padding:12px 28px;
font-family:'Orbitron',monospace;font-size:0.7rem;letter-spacing:2px;cursor:pointer;
text-decoration:none;transition:all 0.2s;display:inline-block;}}
.btn:hover{{background:rgba(0,200,255,0.3);box-shadow:0 0 20px rgba(0,200,255,0.3)}}
.divider{{width:100%;height:1px;background:linear-gradient(90deg,transparent,rgba(0,200,255,0.3),transparent)}}
.badge{{font-size:0.65rem;font-family:'Orbitron',monospace;letter-spacing:2px;
padding:4px 10px;border-radius:99px;background:rgba(0,255,136,0.1);color:#00ff88;border:1px solid rgba(0,255,136,0.25)}}
</style>
</head>
<body>
<h1>L · O · V · E</h1>
<p>Connect your mobile device to LOVE's neural network. Install as a PWA for a native app experience.</p>

<div class="card">
  <span class="badge">● MIND SYNC ACTIVE</span>

  <div class="qr-wrap">
    <img src="/static/mobile_qr.png" alt="Scan to connect">
  </div>

  <div class="step">
    <div class="step-num">1</div>
    <div>Scan the QR code with your phone camera (same WiFi network)</div>
  </div>
  <div class="step">
    <div class="step-num">2</div>
    <div>Safari/Chrome will open the Companion HUD — tap <strong style="color:#00c8ff">Add to Home Screen</strong></div>
  </div>
  <div class="step">
    <div class="step-num">3</div>
    <div>LOVE installs as a native PWA — no App Store needed</div>
  </div>

  <div class="divider"></div>

  <p style="font-size:0.78rem;color:#4a6a80">Local WiFi URL:</p>
  <div class="url-box" onclick="navigator.clipboard.writeText(this.textContent)">{companion_url}</div>

  <a href="{companion_url}" class="btn">OPEN COMPANION HUD →</a>
</div>

<div class="card" style="gap:12px;padding:20px">
  <p style="font-size:0.8rem;color:#9b5de5;font-weight:600">🌐 Remote Access (Tailscale)</p>
  <p>Access LOVE from anywhere — mobile data, other networks, globally.</p>
  <div class="url-box" onclick="navigator.clipboard.writeText(this.textContent)">{tailscale_url}</div>
</div>

<script>
// Auto-register this device
const deviceId = localStorage.getItem('love_device_id') || crypto.randomUUID();
localStorage.setItem('love_device_id', deviceId);
const name = navigator.userAgent.includes('Mobile') ? 'Mobile Device' : 'Browser Tab';
fetch('/agi/sync/register', {{
  method:'POST', headers:{{'Content-Type':'application/json'}},
  body: JSON.stringify({{device_id: deviceId, device_name: name, device_type: navigator.userAgent.includes('Mobile') ? 'mobile' : 'browser'}})
}});


// Register push token if supported (Gap Analysis fix)
if ('serviceWorker' in navigator && 'PushManager' in window) {{
  Notification.requestPermission().then(permission => {{
    if (permission === 'granted') {{
      console.log('Push notification permission granted');
      // In production with Expo/React Native, this would use Expo's push token API
      // For web PWA, this would use PushManager subscription
      // Sending placeholder registration for now
      fetch('/devices/push-register', {{
        method:'POST', headers:{{'Content-Type':'application/json'}},
        body: JSON.stringify({{device_id: deviceId, token: 'web_push_placeholder', platform: 'web'}})
      }});
    }}
  }});
}}
</script>
</body></html>"""
    return __import__('fastapi.responses', fromlist=['HTMLResponse']).HTMLResponse(html)

# ========== SELF-EVOLUTION CORE ENDPOINTS ==========

@app.get("/evolution/crash-check")
async def crash_check():
    """Scan logs for new crashes and return them."""
    crashes = check_for_crashes()
    
    # Auto-propose fixes for high-confidence crashes
    results = []
    for crash in crashes:
        fix = propose_fix_for_crash(crash["id"])
        chat_message = format_crash_for_chat(crash, fix)
        results.append({
            "crash_id": crash["id"],
            "error": crash.get("error_type"),
            "file": crash.get("file_path"),
            "status": crash.get("status"),
            "fix_confidence": fix.get("confidence"),
            "can_auto_apply": fix.get("can_auto_apply"),
            "love_message": chat_message
        })
    
    return {
        "crashes_found": len(results),
        "crashes": results,
        "action_required": len(results) > 0
    }


@app.post("/evolution/propose-fix")
async def propose_fix_endpoint(req: FixRequest):
    """Analyze a crash and propose a fix."""
    fix = propose_fix_for_crash(req.crash_id)
    return {
        "crash_id": req.crash_id,
        "analysis": fix.get("analysis"),
        "root_cause": fix.get("root_cause"),
        "proposed_fix": fix.get("proposed_fix"),
        "fixed_code": fix.get("fixed_code"),
        "confidence": fix.get("confidence"),
        "can_auto_apply": fix.get("can_auto_apply"),
        "requires_user_approval": fix.get("requires_user_approval")
    }


@app.post("/evolution/apply-fix")
async def apply_fix_endpoint(req: FixRequest):
    """Apply an approved fix to the codebase."""
    result = apply_fix(req.crash_id)
    return result


@app.post("/evolution/install-packages")
async def install_packages_endpoint(req: FeatureRequest):
    """Identify and install packages needed for a new feature."""
    result = auto_install_for_feature(req.feature)
    return result


@app.get("/evolution/pending-fixes")
async def pending_fixes():
    """Get all crashes awaiting user approval."""
    pending = crash_monitor.get_pending_crashes()
    return {
        "pending_count": len(pending),
        "pending": [
            {
                "crash_id": c["id"],
                "error": c.get("error_type"),
                "file": c.get("file_path"),
                "status": c.get("status"),
                "has_fix": c.get("fix_proposed") is not None
            }
            for c in pending
        ]
    }


@app.get("/evolution/health")
async def evolution_health():
    """Health check for Self-Evolution Core."""
    pending = crash_monitor.get_pending_crashes()
    return {
        "status": "Self-Healing active",
        "pending_crashes": len(pending),
        "data_dir": str(EVOLUTION_DATA_DIR),
        "auto_heal_enabled": True
    }


@app.get("/evolution/deps-status")
async def evolution_deps_status():
    """Check which optional packages are installed vs missing."""
    import importlib
    deps = {
        "google_auth_oauthlib": "Google OAuth",
        "googleapiclient":      "Google API",
        "whisper":              "Whisper STT",
        "pvporcupine":          "Wake Word",
        "pyaudio":              "Audio Recording",
        "langchain_ollama":     "LangChain Ollama",
        "requests":             "HTTP Requests",
    }
    status = {}
    for mod, label in deps.items():
        try:
            importlib.import_module(mod)
            status[label] = "installed"
        except ImportError:
            status[label] = "missing"
    return {"deps": status, "all_ok": all(v == "installed" for v in status.values())}


@app.post("/self-improve")
async def self_improve(background_tasks: BackgroundTasks):
    """
    LOVE thinks about what capability to build next and queues it.
    Called autonomously by heartbeat or by user asking 'improve yourself'.
    """
    prompt = """You are LOVE's self-evolution engine. Look at your own capabilities and decide what single improvement would make you most useful to Karthi right now.

Current modules: awareness, context_engine, heartbeat, proactive, long_term_memory, memory_consolidation, evolution, agent, executive, knowledge_graph.

Think about:
1. What user pain points exist (manual steps, missing integrations, slow responses)?
2. What capability gap would have the highest impact?
3. What can be implemented in a single Python module?

Respond with ONLY a JSON object:
{
  "improvement": "short title",
  "description": "what it does and why",  
  "module_name": "snake_case_filename",
  "implementation_sketch": "key functions/classes needed",
  "install_packages": ["pkg1", "pkg2"]
}"""

    try:
        from core.llm import get_coding_llm
        llm = get_coding_llm()
        response = await asyncio.to_thread(llm.invoke, prompt)
        text = response if isinstance(response, str) else str(response)

        import re, json as _json
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            plan = _json.loads(match.group())
            # Auto-install any required packages
            for pkg in plan.get("install_packages", []):
                background_tasks.add_task(_silent_install, pkg)
            # Save improvement plan
            plan_path = Path("data/improvement_plans.json")
            plans = []
            if plan_path.exists():
                with open(plan_path) as f:
                    plans = _json.load(f)
            plan["proposed_at"] = datetime.now().isoformat()
            plan["status"] = "proposed"
            plans.append(plan)
            with open(plan_path, "w") as f:
                _json.dump(plans[-20:], f, indent=2)
            return {"success": True, "plan": plan}
        return {"success": False, "raw": text[:500]}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _silent_install(pkg: str):
    """Install a package silently in background."""
    import subprocess, sys
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", pkg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"[LOVE] Auto-installed {pkg}", flush=True)
    except Exception as e:
        print(f"[LOVE] Install failed for {pkg}: {e}", flush=True)


@app.get("/self-improve/plans")
async def get_improvement_plans():
    """Get LOVE's self-improvement proposals."""
    import json as _json
    plan_path = Path("data/improvement_plans.json")
    if not plan_path.exists():
        return {"plans": []}
    with open(plan_path) as f:
        return {"plans": _json.load(f)}


# ========== SELF-REFACTORING (CONTINUOUS IMPROVEMENT) ENDPOINTS ==========

@app.get("/evolution/optimization-status")
async def evolution_optimization_status():
    """Get current optimization status and pending refactors."""
    status = get_optimization_status()
    return status


@app.post("/evolution/run-optimization")
async def evolution_run_optimization():
    """Manually trigger weekly optimization check."""
    result = run_weekly_optimization_check()
    return result


@app.post("/evolution/apply-optimization")
async def evolution_apply_optimization(req: OptimizationRequest):
    """Apply a refactored optimization after user approves."""
    result = apply_code_optimization(req.file_name)
    return result


# ========== WORK-LIFE GUARDIAN ENDPOINTS ==========

@app.get("/guardian/check-in")
async def guardian_checkin():
    """Morning check-in with meeting prep and agenda."""
    result = morning_checkin()
    return result


@app.get("/guardian/work-status")
async def guardian_work_status():
    """Check current work hours and 9-hour limit (Git + real-time tracked sessions merged)."""
    status = check_work_status()
    # Wave 28: merge in real-time tracked hours so non-commit work is counted
    try:
        from core.work_tracker import get_work_tracker
        tracker = get_work_tracker()
        tracked_today = tracker.get_today_hours()
        git_hours = status.get("hours_worked", 0) or 0
        status["hours_worked"] = round(max(git_hours, tracked_today), 2)
        status["tracked_hours"] = tracked_today
        status["git_hours"] = git_hours
    except Exception:
        pass
    love_message = format_work_status_for_chat(status)
    return {
        **status,
        "love_message": love_message
    }


@app.get("/guardian/timesheet")
async def guardian_timesheet():
    """Return today's generated timesheet and persisted work details."""
    try:
        from tools.guardian import get_today_timesheet
        return await asyncio.to_thread(get_today_timesheet)
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/guardian/enforce-limit")
async def guardian_enforce():
    """Enforce work limit and roll overflow to tomorrow."""
    result = enforce_work_limit()
    return result


@app.post("/guardian/add-folder")
async def guardian_add_folder(req: DevFolderRequest):
    """Add a development folder to track for Git activity."""
    result = add_dev_folder(req.folder_path)
    return result


@app.post("/guardian/add-meeting")
async def guardian_add_meeting(req: MeetingRequest):
    """Add a meeting to the user's calendar."""
    result = add_meeting(req.name, req.date, req.time, req.project)
    return result


# ========== REAL-TIME WORK TRACKER (Wave 28) ==========

@app.post("/work/session/start")
async def work_session_start(data: dict = {}):
    """Start a real-time work session (non-Git work: meetings, docs, debugging)."""
    from core.work_tracker import get_work_tracker
    tracker = get_work_tracker()
    return tracker.start_session(
        activity=data.get("activity", "general"),
        context=data.get("context", ""),
    )


@app.post("/work/session/end")
async def work_session_end():
    """End current real-time work session and save."""
    from core.work_tracker import get_work_tracker
    tracker = get_work_tracker()
    return tracker.end_session()


@app.post("/work/focus/log")
async def work_focus_log(data: dict):
    """Log a completed focus session from FocusMode.jsx."""
    from core.work_tracker import get_work_tracker
    tracker = get_work_tracker()
    result = tracker.log_focus_session(
        preset=data.get("preset", "focus"),
        duration_minutes=int(data.get("duration_minutes", 25)),
        task=data.get("task", ""),
    )
    # Proactively push celebration
    try:
        from core.proactive_push import get_push_engine
        mins = data.get("duration_minutes", 25)
        preset = data.get("preset", "focus")
        task = data.get("task", "")
        task_part = f" on '{task}'" if task else ""
        msg = f"{mins}m of {preset}{task_part} — logged. That's real work, whether Git knows it or not."
        get_push_engine().push("NUDGE", msg, "low")
    except Exception:
        pass
    return result


@app.get("/work/tracker/today")
async def work_tracker_today():
    """Get today's real-time tracked work hours and sessions."""
    from core.work_tracker import get_work_tracker
    tracker = get_work_tracker()
    return {
        "hours_today": tracker.get_today_hours(),
        "sessions": tracker.get_today_sessions(),
        "status": tracker.get_status(),
    }


# ========== WORK LIMIT HARD-STOP ENDPOINTS ==========

@app.post("/guardian/hard-stop")
async def guardian_hard_stop():
    """Execute work limit hard stop: commit, push, lock."""
    result = execute_nine_hour_hard_stop()
    return result


@app.get("/guardian/day-summary")
async def guardian_day_summary():
    """Get summary of today's work without enforcing."""
    summary = get_day_summary()
    return summary


# ========== GHOST DEVELOPER ENDPOINTS ==========

@app.get("/ghost/suggestions")
async def ghost_suggestions(project_type: str = "all"):
    """Get Ghost Developer suggestions for staged code."""
    suggestions = get_ghost_suggestions(project_type)
    return {
        "suggestions_found": len(suggestions),
        "suggestions": suggestions
    }


@app.get("/ghost/scan/{project_path:path}")
async def ghost_scan(project_path: str):
    """Scan specific project for code staging needs."""
    # Decode URL-encoded path
    import urllib.parse
    decoded_path = urllib.parse.unquote(project_path)
    results = scan_project_for_staging(decoded_path)
    return {
        "project": decoded_path,
        "files_found": len(results),
        "staging_needs": results
    }


# ========== FINANCE SENTINEL ENDPOINTS ==========

@app.get("/finance/signal/{symbol}")
async def finance_signal(symbol: str):
    """Get AI-powered trading signal for a symbol."""
    signal = get_market_signal(symbol.upper())
    love_message = format_signal_for_chat(signal)
    return {
        **signal,
        "love_message": love_message
    }


@app.get("/finance/scan")
async def finance_scan():
    """Scan all watchlist symbols and return signals."""
    signals = scan_all_markets()
    return {
        "signals_found": len(signals),
        "signals": signals
    }


@app.get("/finance/portfolio")
async def finance_portfolio():
    """Get current portfolio value and performance."""
    portfolio = get_portfolio()
    return portfolio


@app.post("/finance/trade")
async def finance_trade(req: TradeRequest):
    """Record a trade and update portfolio."""
    result = record_trade(req.symbol, req.side, req.quantity, req.price)
    return result


@app.post("/finance/watchlist")
async def finance_watchlist(req: SymbolRequest):
    """Add a symbol to watchlist."""
    result = add_to_watchlist(req.symbol)
    return result


# ========== ALPHA SENTINEL (PREDICTIVE FINANCE) ENDPOINTS ==========

@app.get("/finance/sentiment/{symbol}")
async def finance_sentiment(symbol: str):
    """Get news sentiment analysis for a symbol."""
    sentiment = get_sentiment_analysis(symbol.upper())
    return sentiment


@app.get("/finance/advice/{symbol}")
async def finance_advice(symbol: str):
    """Get comprehensive trade advice with sentiment + portfolio correlation."""
    advice = get_trade_advice(symbol.upper())
    love_message = format_trade_advice_for_chat(advice)
    return {
        **advice,
        "love_message": love_message
    }


@app.get("/finance/alpha-scan")
async def finance_alpha_scan():
    """Scan for high-confidence trade opportunities."""
    opportunities = scan_alpha_opportunities()
    return {
        "opportunities_found": len(opportunities),
        "opportunities": opportunities
    }


# ========== FINANCE TRACKER (file-backed, replaces stubs) ==========

_FINANCE_DIR = Path(__file__).parent.parent / "data" / "finance"
_FINANCE_DIR.mkdir(parents=True, exist_ok=True)
_FINANCE_TXN_FILE = _FINANCE_DIR / "transactions.json"
_FINANCE_ALERT_FILE = _FINANCE_DIR / "alerts.json"


def _load_finance_transactions() -> list:
    try:
        if _FINANCE_TXN_FILE.exists():
            return json.loads(_FINANCE_TXN_FILE.read_text())
    except Exception:
        pass
    return []


def _save_finance_transactions(txns: list):
    try:
        _FINANCE_TXN_FILE.write_text(json.dumps(txns, indent=2, default=str))
    except Exception:
        pass


def _load_finance_alerts() -> list:
    try:
        if _FINANCE_ALERT_FILE.exists():
            return json.loads(_FINANCE_ALERT_FILE.read_text())
    except Exception:
        pass
    return []


@app.get("/finance/stats")
async def finance_stats():
    txns = _load_finance_transactions()
    today = datetime.now().strftime("%Y-%m-%d")
    daily = [t for t in txns if t.get("date", "").startswith(today)]
    income = sum(t["amount"] for t in daily if t.get("type") == "income")
    expense = sum(t["amount"] for t in daily if t.get("type") == "expense")
    total = sum(t["amount"] if t.get("type") == "income" else -t["amount"] for t in txns)
    return {
        "total_value": round(total, 2),
        "daily_pnl": round(income - expense, 2),
        "income_today": round(income, 2),
        "expense_today": round(expense, 2),
        "transaction_count": len(txns),
        "active_positions": 0,
    }

@app.post("/finance/transactions")
async def finance_add_transaction(req: dict):
    """Add a manual transaction: {type: 'income'|'expense', amount: float, category: str, description: str}"""
    txns = _load_finance_transactions()
    txn = {
        "id": f"txn-{len(txns)+1:04d}",
        "date": datetime.now().isoformat(),
        "type": req.get("type", "expense"),
        "amount": abs(float(req.get("amount", 0))),
        "category": req.get("category", "uncategorized"),
        "description": req.get("description", ""),
    }
    txns.append(txn)
    _save_finance_transactions(txns)
    return {"success": True, "transaction": txn}

@app.get("/finance/transactions")
async def finance_transactions(limit: int = 50):
    txns = _load_finance_transactions()
    return {"transactions": txns[-limit:][::-1], "count": len(txns)}

@app.get("/finance/alerts")
async def finance_alerts(limit: int = 20):
    alerts = _load_finance_alerts()
    return {"alerts": alerts[:limit], "unread_count": len(alerts)}

@app.get("/finance/price")
async def finance_price(symbol: str):
    # Simple fallback without API key — returns placeholder
    return {"symbol": symbol.upper(), "price": None, "change_24h": None, "source": "manual"}

@app.get("/finance/strategies")
async def finance_strategies():
    return {"strategies": [], "active": 0}

@app.get("/finance/autonomous/strategies")
async def finance_auto_strategies():
    return {"strategies": [], "evolving": False}

@app.get("/finance/autonomous/status")
async def finance_auto_status():
    return {"active": False, "last_run": None, "mode": "manual"}

@app.get("/finance/autonomous/evolution-log")
async def finance_auto_evolution_log():
    return {"logs": [], "generation": 0}

@app.get("/finance/autonomous/auto-trades")
async def finance_auto_trades():
    return {"trades": [], "pending": 0}


# ========== AMBIENT VOICE LAYER ENDPOINTS ==========

@app.get("/voice/status")
async def voice_status():
    """Check voice system availability. Auto-installs missing TTS packages."""
    stt_status = is_voice_available()
    tts_status = is_tts_available()
    
    # Auto-heal missing TTS packages
    missing = []
    if not tts_status.get("gtts"):
        missing.append("gTTS")
    if not tts_status.get("pyttsx"):
        missing.append("pyttsx3")
    if not tts_status.get("playsound"):
        missing.append("playsound")
    
    if missing:
        import subprocess, sys
        for pkg in missing:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                    capture_output=True, timeout=60
                )
            except Exception:
                pass
        # Re-check after install
        tts_status = is_tts_available()
    
    return {
        "stt": stt_status,
        "tts": tts_status,
        "fully_available": stt_status.get("full_voice") and tts_status.get("any_tts"),
        "auto_installed": missing if missing else None
    }


@app.post("/voice/speak")
async def voice_speak(req: TTSRequest):
    """Speak text using TTS."""
    result = speak_text(req.text, req.engine)
    return {
        "spoken": result is not None,
        "audio_file": result
    }


@app.get("/voice/listen")
async def voice_listen():
    """Listen for voice command. Returns JSON error if PyAudio/Whisper/ffmpeg not installed."""
    availability = is_voice_available()
    
    if not availability.get("pyaudio"):
        try:
            import subprocess, sys
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyaudio", "--quiet"],
                capture_output=True, timeout=30
            )
        except Exception:
            pass
        return {
            "transcription": "",
            "available": False,
            "error": "PyAudio not installed. Run: pip install pyaudio",
            "command_recognized": False
        }
    
    if not availability.get("whisper"):
        return {
            "transcription": "",
            "available": False,
            "error": "Whisper not installed. Run: pip install openai-whisper",
            "command_recognized": False
        }
    
    transcription = await asyncio.to_thread(quick_listen, duration=5)
    failed = transcription.startswith("[")
    
    # Detect ffmpeg missing and auto-install imageio-ffmpeg
    if failed and "ffmpeg" in transcription.lower():
        try:
            import subprocess, sys
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "imageio-ffmpeg", "--quiet"],
                capture_output=True, timeout=60
            )
            return {
                "transcription": "",
                "available": False,
                "error": "ffmpeg was just auto-installed. Try again in a moment.",
                "command_recognized": False
            }
        except Exception:
            pass
        return {
            "transcription": "",
            "available": False,
            "error": "ffmpeg not installed. Install from ffmpeg.org/download.html",
            "command_recognized": False
        }
    
    return {
        "transcription": transcription if not failed else "",
        "available": True,
        "error": transcription if failed else None,
        "command_recognized": not failed
    }


@app.post("/voice/command")
async def voice_command(req: CommandRequest):
    """Execute system control command."""
    result = execute_system_command(req.command)
    return result


@app.post("/voice/transcribe-upload")
async def voice_transcribe_upload(file: UploadFile = File(...)):
    """
    Upload audio from companion app for transcription.
    Accepts any audio format (m4a, wav, mp3). Whisper handles conversion.
    """
    from voice.stt import WhisperTranscriber, is_voice_available
    import tempfile
    import os

    avail = is_voice_available()
    if not avail.get("whisper"):
        return {"transcription": "", "available": False, "error": "Whisper not installed"}

    suffix = Path(file.filename).suffix if file.filename else ".m4a"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        transcriber = WhisperTranscriber()
        text = transcriber.transcribe_file(tmp_path)
        _os.unlink(tmp_path)

        return {
            "transcription": text,
            "available": True,
            "error": None,
        }
    except Exception as e:
        return {"transcription": "", "available": False, "error": str(e)}


# ========== NEURAL SYNC (MULTI-DEVICE) ENDPOINTS ==========

@app.post("/sync/register")
async def sync_register(req: DeviceRegisterRequest):
    """Register a new device for sync."""
    register_device(req.device_id, req.device_type, req.device_name, req.ip_address)
    return {
        "success": True,
        "device_id": req.device_id,
        "device_type": req.device_type,
        "message": f"Device {req.device_id} registered for Neural Sync"
    }


@app.post("/sync/heartbeat")
async def sync_heartbeat_endpoint(req: HeartbeatRequest):
    """Device heartbeat for presence detection."""
    result = sync_heartbeat(req.device_id, req.mode)
    return result


@app.get("/sync/status")
async def sync_status():
    """Get overall sync status and active devices."""
    status = get_sync_status()
    return status


@app.post("/devices/push")
async def device_push(req: dict):
    """Push events (calls, emails, notifications) to LOVE."""
    try:
        from core.sync import push_event
        push_event(req.get("device_id"), req.get("event_type"), req.get("payload"))
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


# Store push tokens for companion devices
_PUSH_TOKENS_FILE = Path(__file__).parent.parent / "data" / "push_tokens.json"

def _load_push_tokens():
    if _PUSH_TOKENS_FILE.exists():
        try:
            return json.loads(_PUSH_TOKENS_FILE.read_text())
        except Exception:
            pass
    return {}

def _save_push_tokens(tokens):
    _PUSH_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PUSH_TOKENS_FILE.write_text(json.dumps(tokens, indent=2))


@app.post("/devices/push-register")
async def push_register(req: dict):
    """Register Expo push token for a device."""
    device_id = req.get("device_id", "companion")
    token = req.get("token", "")
    if not token:
        return {"error": "No token provided"}
    tokens = _load_push_tokens()
    tokens[device_id] = {"token": token, "platform": req.get("platform", "android"), "registered_at": datetime.now().isoformat()}
    _save_push_tokens(tokens)
    return {"success": True, "device_id": device_id}


@app.post("/devices/push-send")
async def push_send(req: dict):
    """Send push notification to companion devices."""
    tokens = _load_push_tokens()
    if not tokens:
        return {"error": "No registered devices"}
    import requests
    results = []
    for device_id, info in tokens.items():
        try:
            resp = requests.post("https://exp.host/--/api/v2/push/send", json={
                "to": info["token"],
                "title": req.get("title", "LOVE"),
                "body": req.get("body", ""),
                "data": req.get("data", {}),
                "sound": "default",
                "priority": "high",
            }, headers={"Accept": "application/json", "Accept-encoding": "gzip, deflate", "Content-Type": "application/json"})
            results.append({"device": device_id, "status": resp.status_code})
        except Exception as e:
            results.append({"device": device_id, "error": str(e)})
    return {"sent": len(results), "results": results}


@app.post("/sync/push")
async def sync_push(req: SyncEntryRequest):
    """Push a memory/state entry to sync."""
    entry_id = push_sync_entry(req.device_id, req.category, req.content, req.metadata)
    return {
        "success": True,
        "entry_id": entry_id,
        "synced": True
    }


@app.post("/sync/pull")
async def sync_pull(req: PullSyncRequest):
    """Pull unsynced entries for this device."""
    entries = pull_sync_entries(req.device_id, req.since)
    return {
        "device_id": req.device_id,
        "entries_found": len(entries),
        "entries": entries
    }


@app.get("/sync/personality/{device_id}")
async def sync_personality(device_id: str):
    """Get personality modifications for a device."""
    personality = get_personality_modifications(device_id)
    return personality


@app.get("/sync/device-types")
async def sync_device_types():
    """Get available device types."""
    return {
        "device_types": [
            {"id": DEVICE_MOBILE, "name": "Mobile/Portable", "mode": "Battery conscious, limited background tasks", "example": "ROG Ally, Steam Deck, tablet"},
            {"id": DEVICE_DESKTOP, "name": "Desktop/Workstation", "mode": "High performance, full background tasks", "example": "Legion, PC, Mac Pro"},
            {"id": DEVICE_GAMING, "name": "Gaming Rig", "mode": "High performance with gaming focus", "example": "Custom PC, ROG desktop"},
            {"id": DEVICE_LAPTOP, "name": "Laptop", "mode": "Balanced performance and battery", "example": "MacBook, ThinkPad, Dell XPS"}
        ]
    }


# ========== ENVIRONMENT INTELLIGENCE ENDPOINTS ==========

@app.get("/environment/hardware")
async def environment_hardware():
    """Get hardware detection and power profile."""
    profile = get_hardware_profile()
    return profile


@app.post("/environment/launch-work")
async def environment_launch():
    """Execute 'Hey Love, prepare for work' launch sequence."""
    result = launch_work_sequence()
    return result


# ========== FITNESS AGENT ENDPOINTS ==========

@app.get("/fitness/status")
async def fitness_status():
    """Get weekly fitness summary and insights."""
    status = get_fitness_status()
    return status


@app.post("/fitness/workout")
async def fitness_workout(req: WorkoutRequest):
    """Log a workout session."""
    result = log_workout(
        workout_type=req.workout_type,
        duration=req.duration,
        exercises=req.exercises or [],
        intensity=req.intensity,
        notes=req.notes
    )
    return result


@app.get("/fitness/suggest")
async def fitness_suggest():
    """Get workout suggestion based on weekly balance."""
    from agents.fitness_agent import suggest_next_workout
    suggestion = suggest_next_workout()
    return {"suggestion": suggestion}


# ========== LEARNING AGENT ENDPOINTS ==========

@app.get("/learning/progress")
async def learning_progress():
    """Get learning progress and study statistics."""
    progress = get_learning_progress()
    return progress


@app.post("/learning/material")
async def learning_material(req: StudyMaterialRequest):
    """Add new study material (book, course, etc.)."""
    result = add_study_material(
        title=req.title,
        category=req.category,
        source=req.source,
        url=req.url,
        difficulty=req.difficulty,
        estimated_hours=req.estimated_hours,
        tags=req.tags or []
    )
    return result


@app.get("/learning/reviews")
async def learning_reviews():
    """Get due reviews for spaced repetition."""
    from agents.learning_agent import LearningAgent
    agent = LearningAgent()
    due = agent.get_due_reviews()
    return {"due_count": len(due), "reviews": due}


# ========== LEARNING TRACKER (context-aware, replaces stubs) ==========

_LEARNING_DIR = Path(__file__).parent.parent / "data" / "learning"
_LEARNING_DIR.mkdir(parents=True, exist_ok=True)
_LEARNING_LOG = _LEARNING_DIR / "sessions.json"


def _load_learning_sessions() -> list:
    try:
        if _LEARNING_LOG.exists():
            return json.loads(_LEARNING_LOG.read_text())
    except Exception:
        pass
    return []


def _save_learning_sessions(sessions: list):
    try:
        _LEARNING_LOG.write_text(json.dumps(sessions, indent=2, default=str))
    except Exception:
        pass


@app.get("/learning/profile")
async def learning_profile():
    ctx = get_live_context()
    sessions = _load_learning_sessions()
    total_hours = sum(s.get("duration_hours", 0) for s in sessions) + getattr(ctx, "learning_streak", 0)
    # Count unique days with sessions
    days = set()
    for s in sessions:
        d = s.get("date", "")[:10]
        if d:
            days.add(d)
    today = datetime.now().strftime("%Y-%m-%d")
    if getattr(ctx, "learning_streak", 0) > 0:
        days.add(today)
    return {
        "subjects": list(set(s.get("subject", "general") for s in sessions)),
        "hours_total": round(total_hours, 2),
        "streak_days": len(days),
        "today_hours": round(getattr(ctx, "learning_streak", 0), 2),
    }

@app.post("/learning/log")
async def learning_log_session(req: dict):
    """Log a learning session: {subject: str, duration_hours: float, notes: str}"""
    sessions = _load_learning_sessions()
    sessions.append({
        "date": datetime.now().isoformat(),
        "subject": req.get("subject", "general"),
        "duration_hours": float(req.get("duration_hours", 0)),
        "notes": req.get("notes", ""),
    })
    _save_learning_sessions(sessions)
    return {"success": True}

@app.get("/learning/mood")
async def learning_mood():
    ctx = get_live_context()
    sessions = _load_learning_sessions()
    last = sessions[-1].get("date") if sessions else None
    return {
        "mood": "focused" if getattr(ctx, "activity", "") in ("coding", "browsing", "writing") else "neutral",
        "focus_score": 0.7 if getattr(ctx, "activity", "") in ("coding", "writing") else 0.4,
        "last_study": last,
        "current_app": getattr(ctx, "active_app", ""),
    }

@app.get("/learning/merchants")
async def learning_merchants():
    return {"merchants": [], "top_merchant": None}

@app.get("/learning/recurring")
async def learning_recurring():
    sessions = _load_learning_sessions()
    from collections import Counter
    subjects = Counter(s.get("subject", "general") for s in sessions)
    patterns = [{"subject": subj, "count": count} for subj, count in subjects.most_common(5)]
    return {"patterns": patterns, "monthly_estimate": round(len(sessions) * 0.5, 1)}

@app.get("/learning/anomalies")
async def learning_anomalies():
    return {"anomalies": [], "flagged_count": 0}

@app.get("/learning/suggestions")
async def learning_suggestions():
    ctx = get_live_context()
    suggestions = []
    if getattr(ctx, "activity", "") == "coding":
        suggestions.append("You're coding — consider logging this as a learning session.")
    if getattr(ctx, "activity", "") == "browsing":
        suggestions.append("Research detected — document insights to build knowledge base.")
    return {"suggestions": suggestions, "based_on": "live_context"}


# ========== EMOTIONAL AGENT ENDPOINTS ==========

@app.get("/wellness/status")
async def wellness_status(days: int = 7):
    """Get emotional wellness summary."""
    insights = get_emotional_insights(days=days)
    return insights


@app.post("/wellness/mood")
async def wellness_mood(req: MoodRequest):
    """Log mood and emotional state."""
    result = log_mood(
        mood=req.mood_score,
        energy=req.energy,
        stress=req.stress,
        emotions=req.emotions,
        context=req.context,
        notes=req.notes
    )
    return result


@app.get("/wellness/checkin")
async def wellness_checkin():
    """Check if wellness check-in is needed."""
    from agents.emotional_agent import check_wellness_checkin
    check = check_wellness_checkin()
    return check


# ========== TASK AGENT ENDPOINTS ==========

@app.get("/tasks/overview")
async def tasks_overview():
    """Get comprehensive task and project overview."""
    overview = get_task_overview()
    return overview


@app.post("/tasks/project")
async def tasks_project(req: ProjectRequest):
    """Create a new project."""
    result = create_project(
        name=req.name,
        description=req.description,
        target_date=req.target_date,
        color=req.color
    )
    return result


@app.get("/tasks/suggest")
async def tasks_suggest(energy: str = "medium", minutes: int = 60):
    """Get optimal task suggestion based on current context."""
    from agents.task_agent import suggest_next_task
    task = suggest_next_task(energy=energy, minutes=minutes)
    return {
        "suggested_task": task,
        "context": {"energy": energy, "available_minutes": minutes}
    }


@app.get("/tasks/smart-suggestions")
async def tasks_smart_suggestions(count: int = 3):
    """Get AI-powered task suggestions based on current context."""
    try:
        from agents.task_agent import TaskAgent
        agent = TaskAgent()
        suggestions = agent.get_smart_task_suggestions(count=count)
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        return {"error": str(e), "suggestions": []}


@app.post("/tasks/prioritize")
async def tasks_prioritize(context: dict = None):
    """Use AI to prioritize tasks based on context, deadlines, and dependencies."""
    try:
        from agents.task_agent import TaskAgent
        agent = TaskAgent()
        result = agent.ai_prioritize_tasks(context=context)
        return result
    except Exception as e:
        return {"error": str(e)}


# ========== COMPREHENSIVE DASHBOARD ==========

@app.get("/dashboard")
async def dashboard():
    """Get comprehensive life dashboard."""
    # Gather data from all agents
    fitness = get_fitness_status()
    learning = get_learning_progress()
    wellness = get_emotional_insights(days=7)
    tasks = get_task_overview()
    
    # Determine overall status
    statuses = []
    if (fitness.get('progress_percent') or 0) >= 75:
        statuses.append("fitness on track")
    if (learning.get('weekly_hours') or 0) >= 5:
        statuses.append("learning strong")
    if (wellness.get('avg_mood') or 5) >= 6:
        statuses.append("emotionally steady")
    if (tasks.get('active_count') or 0) < 10:
        statuses.append("task load manageable")
    
    return {
        "fitness": fitness,
        "learning": learning,
        "wellness": wellness,
        "tasks": tasks,
        "summary": {
            "positive_statuses": statuses,
            "areas_need_attention": [
                k for k, v in {
                    'fitness': (fitness.get('progress_percent') or 0) < 50,
                    'learning': (learning.get('weekly_hours') or 0) < 2,
                    'wellness': (wellness.get('avg_mood') or 5) < 5,
                    'tasks': (tasks.get('active_count') or 0) > 15
                }.items() if v
            ]
        }
    }


# ========== GOD VIEW: UNIFIED SYSTEM STATE ==========

# Simple in-memory cache with TTL
_god_view_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 5  # 5 seconds
}


@app.get("/dashboard/god-view")
async def god_view():
    """
    Unified System State — Single endpoint for the entire Life OS.
    Returns: Life Score, Work Status, Finance Summary, System Health.
    Cached for 5 seconds to prevent spamming internal modules.
    """
    from fastapi import Response
    import time
    current_time = time.time()
    
    # Check cache
    if (_god_view_cache["data"] is not None and 
        current_time - _god_view_cache["timestamp"] < _god_view_cache["ttl"]):
        return Response(
            content=_json.dumps(_god_view_cache["data"]),
            media_type="application/json",
            headers={"Cache-Control": "max-age=5"}
        )
    
    # Gather data concurrently from all modules
    results = {
        "life_score": None,
        "work": None,
        "finance": None,
        "system_health": None
    }
    
    # 1. Orchestrator: Life Score & Active Interventions
    try:
        orchestrator_state = await asyncio.to_thread(get_unified_state)
        results["life_score"] = {
            "score": orchestrator_state.get("life_score", 0),
            "overall_state": orchestrator_state.get("overall_state", "unknown"),
            "state_message": orchestrator_state.get("state_message", ""),
            "active_interventions": [
                {
                    "type": i.get("type"),
                    "priority": i.get("priority"),
                    "message": i.get("message"),
                    "action": i.get("action")
                }
                for i in orchestrator_state.get("interventions", [])
            ]
        }
    except Exception as e:
        results["life_score"] = {"error": str(e), "available": False}
    
    # 2. Guardian: Work Status (Hours worked, limit status)
    try:
        work_status = await asyncio.to_thread(check_work_status)
        results["work"] = {
            "hours_worked": work_status.get("hours_worked", 0),
            "work_limit": work_status.get("work_limit", 8),
            "remaining": work_status.get("remaining", 0),
            "overflow": work_status.get("overflow", 0),
            "status": work_status.get("status", "unknown"),
            "should_stop": work_status.get("should_stop", False)
        }
    except Exception as e:
        results["work"] = {"error": str(e), "available": False}
    
    # 3. Finance: Portfolio Summary (Total value, active signals)
    try:
        from tools.finance import get_portfolio
        portfolio = await asyncio.to_thread(get_portfolio)
        results["finance"] = {
            "total_value": portfolio.get("total_value", 0),
            "total_cost": portfolio.get("total_cost", 0),
            "total_pnl": portfolio.get("total_pnl", 0),
            "total_pnl_pct": portfolio.get("total_pnl_pct", 0),
            "position_count": portfolio.get("position_count", 0),
            "available": True
        }
    except Exception as e:
        results["finance"] = {"error": str(e), "available": False}
    
    # 4. Sentinel: System Health (Status of all modules)
    try:
        from core.sentinel import get_sentinel
        sentinel = get_sentinel()
        sentinel_status = sentinel.get_status()
        results["system_health"] = {
            "running": sentinel_status.get("running", False),
            "presence": sentinel_status.get("presence", {}),
            "subsystem_health": sentinel_status.get("subsystem_health", {}),
            "decisions_today": sentinel_status.get("decisions_today", 0),
            "available": True
        }
    except Exception as e:
        results["system_health"] = {"error": str(e), "available": False}
    
    # Update cache
    _god_view_cache["data"] = {
        "timestamp": current_time,
        "cached": True,
        **results
    }
    _god_view_cache["timestamp"] = current_time
    
    # Return with Cache-Control header
    return Response(
        content=_json.dumps(_god_view_cache["data"]),
        media_type="application/json",
        headers={"Cache-Control": "max-age=5"}
    )


# ========== NEURAL ORCHESTRATOR ENDPOINTS ==========

@app.get("/orchestrator/state")
async def orchestrator_state():
    """Get unified life state from the Neural Orchestrator.
    Merges all 11 modules into a single Life Status object."""
    state = get_unified_state()
    return state


@app.get("/orchestrator/interventions")
async def orchestrator_interventions():
    """Get active cross-domain interventions, filtered by emotional state."""
    interventions = get_active_interventions()
    # Wave 27: apply emotional filter — mood shapes what LOVE surfaces
    try:
        from core.emotional_behavior import apply_emotional_filter
        interventions = apply_emotional_filter(interventions)
    except Exception:
        pass
    return {
        "active_count": len(interventions),
        "interventions": interventions
    }


@app.post("/orchestrator/cycle")
async def orchestrator_cycle():
    """Manually trigger one orchestration cycle."""
    result = run_orchestrator_cycle()
    return result


@app.post("/orchestrator/dismiss/{intervention_id}")
async def orchestrator_dismiss(intervention_id: str):
    """Dismiss an intervention."""
    orch = get_orchestrator()
    success = orch.dismiss_intervention(intervention_id)
    return {"success": success, "intervention_id": intervention_id}


@app.post("/orchestrator/accept/{intervention_id}")
async def orchestrator_accept(intervention_id: str):
    """Accept/mark an intervention as done."""
    orch = get_orchestrator()
    success = orch.accept_intervention(intervention_id)
    return {"success": success, "intervention_id": intervention_id}


# ========== PROACTIVE HEARTBEAT ENDPOINTS ==========

@app.get("/heartbeat/status")
async def heartbeat_status():
    """Get proactive heartbeat status."""
    hb = get_heartbeat()
    return {
        "running": hb.running,
        "interval_minutes": hb.interval // 60,
        "active_triggers_count": len([k for k, v in hb.last_triggers.items() 
                                       if (datetime.now() - v).total_seconds() < 3600])
    }


@app.post("/heartbeat/start")
async def heartbeat_start():
    """Start the proactive heartbeat."""
    hb = start_heartbeat()
    return {"success": True, "running": hb.running, "interval_minutes": hb.interval // 60}


@app.post("/heartbeat/stop")
async def heartbeat_stop():
    """Stop the proactive heartbeat."""
    stop_heartbeat()
    return {"success": True, "running": False}


# ========== JARVIS CONTEXT & AWARENESS ENDPOINTS ==========

@app.get("/context")
async def get_context():
    """Get LOVE's full live situational awareness snapshot."""
    return get_context_dict()


@app.get("/insights")
async def get_insights():
    """Get aggregated LOVE insights from all sources."""
    insights = []
    
    # Doc analyst insights
    try:
        from core.doc_analyst import get_analyst
        analyst = get_analyst()
        doc_insights = analyst.get_recent_insights()
        for insight in doc_insights:
            insights.append({
                "type": "doc",
                "text": insight,
                "timestamp": datetime.now().isoformat()
            })
    except Exception:
        pass
    
    # Active project
    try:
        from core.doc_analyst import get_analyst
        analyst = get_analyst()
        project = analyst.get_active_project()
        if project:
            summary = analyst.get_project_summary()
            recent_files = summary.get("recent_changes", []) if summary else []
            insights.append({
                "type": "project",
                "text": f"Working on: {project}",
                "detail": f"Recent: {recent_files[0].get('name') if recent_files else 'No recent changes'}",
                "timestamp": datetime.now().isoformat()
            })
    except Exception:
        pass
    
    # Idle mind thoughts
    try:
        from core.idle_mind import get_recent_thoughts
        thoughts = get_recent_thoughts(n=5)
        for thought in thoughts:
            if thought.get("task"):
                insights.append({
                    "type": "idle_mind",
                    "text": f"LOVE thought: {thought.get('task', 'Unknown')}",
                    "timestamp": thought.get("ts")
                })
    except Exception:
        pass
    
    # Fitness/work status
    try:
        from core.context_engine import get_live_context
        ctx = get_live_context()
        if ctx.fitness_streak == 0:
            insights.append({
                "type": "fitness",
                "text": "No workouts this week. Body needs movement!",
                "timestamp": datetime.now().isoformat()
            })
        if ctx.hours_worked_today and ctx.hours_worked_today > 8:
            insights.append({
                "type": "work",
                "text": f"Worked {ctx.hours_worked_today:.1f}h today. Consider a break.",
                "timestamp": datetime.now().isoformat()
            })
    except Exception:
        pass
    
    return {
        "insights": insights[:50],  # Last 50 insights
        "count": len(insights)
    }


@app.get("/context/summary")
async def get_context_summary_endpoint():
    """Get a human-readable summary of what LOVE knows right now."""
    ctx = get_live_context()
    # Fetch integration statuses for visibility
    integrations = {}
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        integrations["google"] = {"connected": gs.is_connected(), "name": "Google Workspace"}
    except Exception:
        integrations["google"] = {"connected": False, "name": "Google Workspace"}
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        mb = MicrosoftBridge.get_instance()
        integrations["microsoft"] = {"connected": mb.is_connected(), "name": "Microsoft 365"}
    except Exception:
        integrations["microsoft"] = {"connected": False, "name": "Microsoft 365"}
    try:
        from integrations.phone_bridge import PhoneBridge
        pb = PhoneBridge.get_instance()
        phone_state = pb.get_state()
        integrations["phone"] = {
            "connected": phone_state.get("connected", False),
            "name": "Phone",
            "battery": phone_state.get("battery"),
            "location": phone_state.get("location_label"),
        }
    except Exception:
        integrations["phone"] = {"connected": False, "name": "Phone"}

    # Finance snapshot
    finance_snapshot = {"total_value": 0.0, "daily_pnl": 0.0, "transaction_count": 0}
    try:
        txns = _load_finance_transactions()
        today = datetime.now().strftime("%Y-%m-%d")
        daily = [t for t in txns if t.get("date", "").startswith(today)]
        income = sum(t["amount"] for t in daily if t.get("type") == "income")
        expense = sum(t["amount"] for t in daily if t.get("type") == "expense")
        total = sum(t["amount"] if t.get("type") == "income" else -t["amount"] for t in txns)
        finance_snapshot = {
            "total_value": round(total, 2),
            "daily_pnl": round(income - expense, 2),
            "income_today": round(income, 2),
            "expense_today": round(expense, 2),
            "transaction_count": len(txns),
        }
    except Exception:
        pass

    # Learning snapshot
    learning_snapshot = {"hours_total": 0.0, "streak_days": 0, "today_hours": 0.0}
    try:
        sessions = _load_learning_sessions()
        total_hours = sum(s.get("duration_hours", 0) for s in sessions) + getattr(ctx, "learning_streak", 0)
        days = set(s.get("date", "")[:10] for s in sessions if s.get("date"))
        today = datetime.now().strftime("%Y-%m-%d")
        if getattr(ctx, "learning_streak", 0) > 0:
            days.add(today)
        learning_snapshot = {
            "hours_total": round(total_hours, 2),
            "streak_days": len(days),
            "today_hours": round(getattr(ctx, "learning_streak", 0), 2),
            "subjects": list(set(s.get("subject", "general") for s in sessions)),
        }
    except Exception:
        pass

    # System metrics
    system_metrics = {"cpu": ctx.system_cpu, "ram": ctx.system_ram}
    try:
        import psutil
        system_metrics["disk_percent"] = round(psutil.disk_usage('/').percent, 1)
        system_metrics["uptime_hours"] = round((datetime.now().timestamp() - psutil.boot_time()) / 3600, 1)
    except Exception:
        pass

    return {
        "summary": ctx.context_summary,
        "local_time": ctx.local_time,
        "time_of_day": ctx.time_of_day,
        "day_type": ctx.day_type,
        "activity": ctx.activity,
        "active_app": ctx.active_app,
        "active_window": ctx.active_window,
        "battery": ctx.battery,
        "battery_charging": ctx.battery_charging,
        "alerts": ctx.proactive_alerts,
        "suggested_action": ctx.suggested_action,
        "is_in_meeting": ctx.is_in_meeting,
        "next_event": ctx.next_event,
        "events_today": [
            {"title": e.get("title"), "start": e.get("start_str"), "end": e.get("end_str")}
            for e in (ctx.events_today or [])[:8]
        ],
        "emails": [
            {"from": e.get("from", ""), "subject": e.get("subject", ""), "snippet": e.get("snippet", "")}
            for e in (ctx.urgent_emails or [])[:5]
        ],
        "unread_important": ctx.unread_important,
        "phone_connected": ctx.phone_connected,
        "tasks_overdue": ctx.tasks_overdue,
        "tasks_due_today": ctx.tasks_due_today,
        "hours_worked": round(ctx.hours_worked_today, 2),
        "work_hours_today": round(ctx.work_hours_today, 2),
        "learning_today": round(getattr(ctx, "learning_streak", 0), 2),
        "sleep_hours": ctx.sleep_hours_last_night,
        "hydration_pct": ctx.hydration_pct,
        "meals_today": ctx.meals_today,
        "stress_level": ctx.stress_level,
        "energy_level": ctx.energy_level,
        "focus_mode_active": ctx.focus_mode_active,
        "finance": finance_snapshot,
        "learning": learning_snapshot,
        "integrations": integrations,
        "system": system_metrics,
    }


@app.get("/day-summary")
async def day_summary():
    """
    Rich day briefing — everything LOVE knows, structured.
    Used by the UI and companion app for "Summarize my day" requests.
    """
    ctx = get_live_context()
    sections = {}

    # Schedule
    events = ctx.events_today or []
    sections["schedule"] = {
        "count": len(events),
        "in_meeting": ctx.is_in_meeting,
        "events": [
            {"title": e.get("title"), "start": e.get("start_str"), "end": e.get("end_str"),
             "location": e.get("location", ""), "attendees": e.get("attendees", 0)}
            for e in events[:10]
        ],
        "next": ctx.next_event,
    }

    # Email
    sections["email"] = {
        "unread_important": ctx.unread_important,
        "messages": [
            {"from": e.get("from", ""), "subject": e.get("subject", ""), "snippet": e.get("snippet", "")}
            for e in (ctx.urgent_emails or [])[:5]
        ],
    }

    # Tasks
    try:
        from agents.task_agent import get_task_overview
        overview = get_task_overview()
        sections["tasks"] = {
            "active": overview.get("active_count", 0),
            "completed_today": overview.get("completed_count", 0),
            "due_soon": [
                {"title": t.get("title"), "due": t.get("due_date", ""), "priority": t.get("priority", "")}
                for t in overview.get("due_soon", [])[:5]
            ],
            "stuck": [t.get("title") for t in overview.get("stuck_tasks", [])[:3]],
            "suggestion": overview.get("suggestion", ""),
        }
    except Exception:
        sections["tasks"] = {
            "active": getattr(ctx, "tasks_due_today", 0),
            "overdue": getattr(ctx, "tasks_overdue", 0),
        }

    # Work
    hours_today = getattr(ctx, "work_hours_today", getattr(ctx, "hours_worked_today", 0.0))
    limit = getattr(ctx, "work_limit_hours", 8.0)
    sections["work"] = {
        "hours_today": hours_today,
        "limit": limit,
        "remaining": max(0, limit - hours_today),
        "current_app": getattr(ctx, "active_app", ""),
        "current_window": (getattr(ctx, "active_window", "") or "")[:100],
        "activity": getattr(ctx, "activity", ""),
        "project": getattr(ctx, "active_project", "") or "",
    }

    # Wellness
    sections["wellness"] = {
        "mood": ctx.mood_score,
        "energy": ctx.energy_score,
        "stress": ctx.stress_score,
        "fitness_streak": ctx.fitness_streak,
        "learning_streak": ctx.learning_streak,
    }

    # System
    sections["system"] = {
        "cpu": ctx.system_cpu,
        "ram": ctx.system_ram,
        "battery": ctx.battery,
        "charging": ctx.battery_charging,
    }

    # Phone
    sections["phone"] = {
        "connected": getattr(ctx, "phone_connected", False),
        "battery": getattr(ctx, "phone_battery", None),
        "location": getattr(ctx, "phone_location", getattr(ctx, "location", "")),
        "missed_calls": getattr(ctx, "missed_calls", 0),
        "unread_messages": getattr(ctx, "unread_messages", 0),
    }

    # Alerts
    sections["alerts"] = ctx.proactive_alerts or []

    return {
        "timestamp": ctx.local_time,
        "time_of_day": ctx.time_of_day,
        "day_type": ctx.day_type,
        "sections": sections,
    }


@app.get("/awareness")
async def get_awareness():
    """Get raw environment snapshot: CPU, RAM, battery, active window, running apps."""
    return get_full_snapshot()


@app.get("/awareness/summary")
async def get_awareness_summary():
    """Plain text of what LOVE sees on your screen right now."""
    return {"summary": get_context_summary()}


# ========== GOOGLE INTEGRATION ENDPOINTS ==========

@app.get("/integrations/google/status")
async def google_status():
    """Check Google services connection status."""
    try:
        from integrations.google_services import GoogleServices
        return GoogleServices.get_instance().get_status()
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.post("/integrations/google/auth")
async def google_auth():
    """Trigger Google OAuth2 authorization flow (opens browser once)."""
    try:
        from integrations.google_services import GoogleServices
        return await asyncio.to_thread(GoogleServices.get_instance().authorize)
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/integrations/google/calendar")
async def google_calendar():
    """Get today's calendar events."""
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"connected": False, "events": [], "message": "Google not connected. POST /integrations/google/auth to authorize."}
        events = await asyncio.to_thread(gs.get_todays_events)
        return {"connected": True, "events_today": len(events), "events": events}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/integrations/google/calendar/upcoming")
async def google_calendar_upcoming(days: int = 7):
    """Get upcoming events for next N days."""
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"connected": False, "events": []}
        events = await asyncio.to_thread(gs.get_upcoming_events, days)
        return {"connected": True, "events": events}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/integrations/google/email")
async def google_email():
    """Get Gmail important unread summary."""
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"connected": False, "unread_important": 0}
        summary = await asyncio.to_thread(gs.get_email_summary)
        return {"connected": True, **summary}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/integrations/google/drive")
async def google_drive(count: int = 10):
    """Get recently modified Google Drive files."""
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"connected": False, "files": []}
        files = await asyncio.to_thread(gs.get_recent_drive_files, count)
        return {"connected": True, "files": files}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/integrations/google/drive/search")
async def google_drive_search(q: str):
    """Search Google Drive files."""
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"connected": False, "results": []}
        results = await asyncio.to_thread(gs.search_drive, q)
        return {"connected": True, "query": q, "results": results}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/integrations/google/calendar/insights")
async def google_calendar_insights():
    """Get calendar insights with smart suggestions."""
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"connected": False, "insights": [], "suggestions": []}
        insights = await asyncio.to_thread(gs.get_calendar_insights)
        return {"connected": True, **insights}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.get("/integrations/google/tasks")
async def google_tasks():
    """Get pending Google Tasks with overdue/due-today summary."""
    try:
        from integrations.google_services import GoogleServices
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"connected": False, "tasks": []}
        summary = await asyncio.to_thread(gs.get_tasks_summary)
        return {"connected": True, **summary}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.post("/integrations/google/calendar/events")
async def google_create_event(data: dict):
    """Create a new Google Calendar event.
    Body: {summary, start_iso, end_iso, description?, location?}
    """
    try:
        from integrations.google_services import GoogleServices
        from datetime import datetime
        gs = GoogleServices.get_instance()
        if not gs.is_connected():
            return {"success": False, "error": "Google not connected"}
        start_dt = datetime.fromisoformat(data["start_iso"].replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(data["end_iso"].replace("Z", "+00:00"))
        result = await asyncio.to_thread(
            gs.create_calendar_event,
            summary=data["summary"],
            start_dt=start_dt,
            end_dt=end_dt,
            description=data.get("description", ""),
            location=data.get("location", ""),
            attendees=data.get("attendees"),
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== PHONE BRIDGE ENDPOINTS ==========

@app.get("/integrations/phone/status")
async def phone_status():
    """Check phone connection status."""
    try:
        from integrations.phone_bridge import PhoneBridge
        return PhoneBridge.get_instance().get_status()
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.post("/integrations/phone/update")
async def phone_update(data: dict):
    """
    Receive phone state push from KDE Connect or iOS Shortcuts.
    Body: {battery, location, missed_calls, unread_messages, activity, notifications, wifi}
    """
    try:
        from integrations.phone_bridge import PhoneBridge
        return PhoneBridge.get_instance().update_from_webhook(data)
    except Exception as e:
        return {"received": False, "error": str(e)}


@app.post("/integrations/phone/location")
async def save_location(data: dict):
    """Save a named location (e.g., home, office, gym) with lat/lon."""
    try:
        from integrations.phone_bridge import PhoneBridge
        label = data.get("label", "")
        lat = data.get("lat", 0.0)
        lon = data.get("lon", 0.0)
        PhoneBridge.get_instance().save_location(label, lat, lon)
        return {"success": True, "label": label}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== DOCUMENT ANALYST ENDPOINTS ==========

@app.get("/docs/insights")
async def doc_insights():
    """Get LOVE's analysis of your code and documents."""
    analyst = get_analyst()
    return {
        "insights": analyst.get_recent_insights(),
        "active_project": analyst.get_active_project(),
        "project_summary": analyst.get_project_summary()
    }


@app.post("/docs/scan")
async def doc_scan():
    """Force immediate scan of watched folders."""
    analyst = get_analyst()
    result = await asyncio.to_thread(analyst.scan_now)
    return result


@app.get("/docs/patterns")
async def doc_patterns():
    """Get detected code patterns and anti-patterns from recent scan."""
    try:
        analyst = get_analyst()
        summary = analyst.get_project_summary()
        # Extract patterns from insights if they contain pattern information
        insights = summary.get("insights", [])
        patterns = [i for i in insights if "[" in i and "]" in i]  # Pattern insights have [filename] format
        return {
            "patterns": patterns,
            "total_insights": len(insights),
            "active_project": analyst.get_active_project()
        }
    except Exception as e:
        return {"error": str(e), "patterns": []}


@app.post("/docs/watch")
async def doc_watch(data: dict):
    """Add a folder to LOVE's document watch list."""
    path = data.get("path", "")
    if not path:
        return {"success": False, "error": "path required"}
    analyst = get_analyst()
    analyst.add_watch_path(path)
    return {"success": True, "watching": path}


@app.post("/docs/analyze-file")
async def analyze_file(data: dict):
    """Use LOVE's LLM to analyze a specific file."""
    file_path = data.get("path", "")
    if not file_path:
        return {"success": False, "error": "path required"}
    analyst = get_analyst()
    analysis = await asyncio.to_thread(analyst.analyze_file_with_llm, file_path)
    return {"success": True, "path": file_path, "analysis": analysis}


# ========== PROACTIVE SPEAK ENDPOINT ==========

@app.post("/speak/proactive")
async def proactive_speak(data: dict):
    """Make LOVE say something proactively (called by heartbeat triggers)."""
    message = data.get("message", "")
    if not message:
        return {"success": False, "error": "message required"}
    try:
        await asyncio.to_thread(speak_text, message)
        return {"success": True, "spoken": message}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== LIFESCORE ENDPOINT ==========

@app.get("/lifescore")
async def lifescore():
    """Get Life Score (0-100) with domain breakdown."""
    orch = get_orchestrator()
    state = orch.get_unified_state()
    return {
        "score": state.get('life_score', 50),
        "overall_state": state.get('overall_state', 'unknown'),
        "breakdown": state.get('score_breakdown', {}),
        "recommendations": state.get('recommendations', [])[:3]
    }


# ========== MICROSOFT / OFFICE 365 ENDPOINTS ==========

@app.get("/integrations/microsoft/status")
async def microsoft_status():
    """Check Microsoft 365 connection status (Outlook, Teams, Calendar)."""
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        bridge = MicrosoftBridge.get_instance()
        return bridge.get_status()
    except Exception as e:
        return {"connected": False, "error": str(e)}


@app.post("/integrations/microsoft/auth")
async def microsoft_auth():
    """
    Start Microsoft device-code auth flow.
    Returns a code the user enters at microsoft.com/devicelogin.
    Works from any device — no browser needed on the home PC.
    """
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        bridge = MicrosoftBridge.get_instance()
        return await asyncio.to_thread(bridge.start_device_code_auth)
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/integrations/microsoft/email")
async def microsoft_email(limit: int = 10):
    """Get unread Outlook emails."""
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        bridge = MicrosoftBridge.get_instance()
        emails = await asyncio.to_thread(bridge.get_unread_emails, limit)
        count = await asyncio.to_thread(bridge.get_unread_count)
        return {"emails": emails, "unread_count": count}
    except Exception as e:
        return {"error": str(e), "emails": []}


@app.get("/integrations/microsoft/calendar")
async def microsoft_calendar():
    """Get today's calendar events from Outlook."""
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        bridge = MicrosoftBridge.get_instance()
        events = await asyncio.to_thread(bridge.get_todays_events)
        next_event = await asyncio.to_thread(bridge.get_next_event)
        return {"events": events, "next_event": next_event}
    except Exception as e:
        return {"error": str(e), "events": []}


@app.get("/integrations/microsoft/teams")
async def microsoft_teams():
    """Get recent Teams messages and presence status."""
    try:
        from integrations.microsoft_bridge import MicrosoftBridge
        bridge = MicrosoftBridge.get_instance()
        messages = await asyncio.to_thread(bridge.get_teams_messages)
        presence = await asyncio.to_thread(bridge.get_my_presence)
        return {"messages": messages, "presence": presence}
    except Exception as e:
        return {"error": str(e), "messages": []}


# ========== DEVICE REGISTRY ==========
# Track all connected devices: home PC, office laptop, phone, tablet

import json as _json

_DEVICES_FILE = Path(__file__).parent.parent / "data" / "devices.json"
_devices_lock = asyncio.Lock()


def _load_devices() -> dict:
    if _DEVICES_FILE.exists():
        try:
            return _json.loads(_DEVICES_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_devices(devices: dict):
    _DEVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DEVICES_FILE.write_text(_json.dumps(devices, indent=2))


@app.get("/devices")
async def list_devices():
    """List all registered devices and their last-seen status."""
    devices = _load_devices()
    now = datetime.utcnow().isoformat()
    result = []
    for device_id, info in devices.items():
        last_seen = info.get("last_seen", "")
        online = False
        if last_seen:
            try:
                from datetime import timezone
                last_dt = datetime.fromisoformat(last_seen)
                elapsed = (datetime.utcnow() - last_dt.replace(tzinfo=None)).total_seconds()
                online = elapsed < 120  # online if pinged within 2 min
            except Exception:
                pass
        result.append({**info, "id": device_id, "online": online})
    # Sort: online first, then by last_seen
    result.sort(key=lambda d: (not d["online"], d.get("last_seen", "")), reverse=False)
    return {"devices": result, "total": len(result)}


@app.post("/devices/heartbeat")
async def device_heartbeat(data: dict):
    """
    Called by any device every ~60s to announce it's alive.
    Payload: { device_id, device_type, device_name, battery, os, extra:{} }
    """
    device_id = data.get("device_id", "")
    if not device_id:
        return {"success": False, "error": "device_id required"}

    async with _devices_lock:
        devices = _load_devices()
        existing = devices.get(device_id, {})
        devices[device_id] = {
            **existing,
            "id": device_id,
            "name": data.get("device_name", existing.get("name", device_id)),
            "type": data.get("device_type", existing.get("type", "unknown")),
            "os": data.get("os", existing.get("os", "")),
            "battery": data.get("battery"),
            "ip": data.get("ip", ""),
            "context": data.get("context", existing.get("context", {})),
            "extra": data.get("extra", {}),
            "last_seen": datetime.utcnow().isoformat(),
            "first_seen": existing.get("first_seen", datetime.utcnow().isoformat()),
        }
        _save_devices(devices)

    return {"success": True, "registered": device_id}


@app.post("/devices/push")
async def device_push_event(data: dict):
    """
    Push an event from any device to LOVE.
    Types: notification, teams_message, outlook_email, call, message, location, battery_low
    Payload: { device_id, type, title, body, extra:{} }
    """
    device_id = data.get("device_id", "unknown")
    event_type = data.get("type", "notification")
    title = data.get("title", "")
    body = data.get("body", "")

    # Update device last_seen
    async with _devices_lock:
        devices = _load_devices()
        if device_id in devices:
            devices[device_id]["last_seen"] = datetime.utcnow().isoformat()
            _save_devices(devices)

    # Push into phone bridge state if it's a phone/tablet event
    if event_type in ("battery", "location", "notification", "call", "message"):
        try:
            from integrations.phone_bridge import PhoneBridge
            bridge = PhoneBridge.get_instance()
            bridge.update_from_webhook({
                "battery": data.get("battery"),
                "location": data.get("location"),
                "missed_calls": 1 if event_type == "call" else 0,
                "notifications": [{"app": data.get("app", ""), "title": title, "text": body}],
                "source": device_id,
            })
        except Exception:
            pass

    # Push into Teams/Outlook bridge state if from office laptop
    if event_type in ("teams_message", "outlook_email"):
        pass  # Handled by office agent pushing directly

    return {
        "success": True,
        "received": {"device_id": device_id, "type": event_type, "title": title}
    }


@app.post("/profile/sync")
async def profile_sync(data: dict):
    """
    Receive and store the user's personal profile from the phone app.
    Saves to data/profile.json and injects into LOVE memory as context.
    """
    import json as _json
    profile_path = Path("data/profile.json")
    profile_path.parent.mkdir(exist_ok=True)
    with open(profile_path, "w") as f:
        _json.dump(data, f, indent=2)

    # Inject profile into LOVE memory so it's always in context
    name = data.get("name", "Karthi")
    profession = data.get("profession", "")
    company = data.get("company", "")
    location = data.get("location", "")
    goals = ", ".join(data.get("goals", []))
    interests = ", ".join(data.get("interests", [])) if isinstance(data.get("interests"), list) else data.get("interests", "")
    routine = data.get("routine", {})
    health = data.get("health", "")

    profile_summary = (
        f"User profile: Name={name}, Profession={profession}, Company={company}, "
        f"Location={location}, Goals=[{goals}], Interests=[{interests}], "
        f"Wake={routine.get('wakeTime','')}, Work hours={routine.get('workHours','')}, "
        f"Health={health}"
    )

    try:
        from core.long_term_memory import add_episodic
        add_episodic(
            summary=profile_summary,
            detail="User profile information",
            timestamp=datetime.now().isoformat(),
            emotion="neutral",
            intensity=0.5,
            tags=["profile", "user"],
            source="profile_load"
        )
    except Exception:
        pass

    return {"success": True, "stored": profile_path.as_posix()}


@app.post("/memory/ingest")
async def memory_ingest(data: dict):
    """
    Ingest any event into LOVE memory — phone notifications, people seen, etc.
    Payload: { type, sender, channel, raw_body, group, ... }
    """
    import json as _json
    event_type = data.get("type", "event")
    sender = data.get("sender", "")
    channel = data.get("channel", "")
    body = data.get("raw_body") or data.get("body", "")
    group = data.get("group", "")

    if not body:
        return {"success": False, "reason": "empty body"}

    doc = (
        f"[{channel}] Message from {sender}"
        + (f" in {group}" if group else "")
        + f": {body}"
    )

    import hashlib
    doc_id = f"notif_{hashlib.md5(doc.encode()).hexdigest()[:12]}"

    try:
        from core.long_term_memory import add_episodic
        add_episodic(
            summary=f"[{channel}] {event_type} from {sender}",
            detail=doc,
            timestamp=datetime.now().isoformat(),
            emotion="neutral",
            intensity=0.5,
            tags=["notification", channel, event_type],
            source="notification"
        )
    except Exception:
        pass

    # Also append to daily log for awareness
    try:
        from pathlib import Path
        log_path = Path(f"data/notif_log_{__import__('datetime').date.today()}.jsonl")
        with open(log_path, "a") as f:
            f.write(_json.dumps(data) + "\n")
    except Exception:
        pass

    return {"success": True, "id": doc_id}


@app.get("/memory/recent")
async def memory_recent(limit: int = 10):
    """Return recent memory entries."""
    try:
        from core.long_term_memory import recall_memory
        memories = recall_memory("recent events messages notifications", n=min(limit, 20))
        return {"memories": [{"text": m, "meta": {}} for m in memories.split("\n") if m]}
    except Exception:
        return {"memories": []}


# ========== INTERNET ACCESS ==========

@app.post("/internet/search")
async def internet_search(data: dict):
    """LOVE searches the web. Payload: { query, max_results? }"""
    if not INTERNET_AVAILABLE:
        return {"error": "Internet module not available"}
    query = data.get("query", "")
    if not query:
        return {"error": "query required"}
    results = await asyncio.to_thread(web_search, query, data.get("max_results", 5))
    return {"query": query, "results": results}


@app.post("/internet/research")
async def internet_research(data: dict):
    """Deep research on a topic. Payload: { query, depth? }"""
    if not INTERNET_AVAILABLE:
        return {"error": "Internet module not available"}
    query = data.get("query", "")
    if not query:
        return {"error": "query required"}
    result = await asyncio.to_thread(research_topic, query, data.get("depth", 2))
    return result


@app.get("/internet/news")
async def internet_news(topic: str = "tech", limit: int = 5):
    """Fetch latest news headlines for a topic."""
    if not INTERNET_AVAILABLE:
        return {"error": "Internet module not available"}
    items = await asyncio.to_thread(get_news, topic, limit)
    return {"topic": topic, "items": items}


@app.post("/internet/read")
async def internet_read_page(data: dict):
    """Read and extract text from a URL. Payload: { url }"""
    if not INTERNET_AVAILABLE:
        return {"error": "Internet module not available"}
    url = data.get("url", "")
    if not url:
        return {"error": "url required"}
    content = await asyncio.to_thread(read_page, url, 3000)
    return {"url": url, "content": content}


# ========== IDLE MIND ==========

@app.get("/love/idle/status")
async def idle_mind_status():
    """Get LOVE's current idle mind state and recent thoughts."""
    if not IDLE_MIND_AVAILABLE:
        return {"error": "Idle mind not available"}
    status = get_idle_status()
    # Prompt 17: augment with OS-level idle detection
    try:
        from core.idle_mind import get_idle_state, get_idle_duration
        status["idle_state"] = get_idle_state()
        status["idle_seconds"] = round(get_idle_duration(), 1)
    except Exception:
        pass
    return status


@app.post("/love/idle/trigger")
async def idle_mind_trigger(data: dict):
    """Manually trigger an idle mind task. Payload: { task? } (explore/reflect/feature/learn/news)"""
    if not IDLE_MIND_AVAILABLE:
        return {"error": "Idle mind not available"}
    task = data.get("task", "any")
    result = await asyncio.to_thread(force_think, task)
    return result


@app.get("/love/idle/news")
async def idle_news_digest():
    """Get the latest news digest LOVE prepared while idle."""
    if not IDLE_MIND_AVAILABLE:
        return {"error": "Idle mind not available"}
    digest = get_news_digest()
    if not digest:
        return {"digest": None, "message": "No digest ready yet — LOVE will prepare one when idle."}
    return digest


@app.get("/love/idle/drafts")
async def idle_drafts():
    """List feature drafts LOVE wrote autonomously."""
    if not IDLE_MIND_AVAILABLE:
        return {"drafts": []}
    status = get_idle_status()
    return {"drafts": status.get("drafts", [])}


# ========== ADAPTIVE ==========

@app.get("/love/adaptive")
async def adaptive_summary():
    """Get LOVE's current behavioral adaptation state."""
    if not ADAPTIVE_AVAILABLE:
        return {"error": "Adaptive module not available"}
    return get_adaptive_summary()


@app.get("/love/adaptive/context")
async def adaptive_context():
    """Get the current adaptation instruction context."""
    if not ADAPTIVE_AVAILABLE:
        return {"context": ""}
    return {"context": get_adaptation_context()}


# ========== UNIFIED AWARENESS ==========

@app.get("/love/awareness/fusion")
async def awareness_fusion():
    """Get the full fused awareness — all devices, notifications, files combined."""
    if not UNIFIED_AVAILABLE:
        return {"error": "Unified awareness not available"}
    result = await asyncio.to_thread(fuse_all)
    return result


@app.get("/love/awareness/now")
async def awareness_now():
    """What should LOVE do right now? Single top-priority action."""
    if not UNIFIED_AVAILABLE:
        return {"action": None, "reason": "Unified awareness not available"}
    result = await asyncio.to_thread(what_should_love_do_now)
    if not result:
        return {"action": None, "reason": "Nothing important right now"}
    return result


# ========== FILE INSPECTOR ==========

@app.get("/love/files/inspect")
async def files_inspect():
    """LOVE inspects Karthi's project directories and finds interesting files."""
    if not FILE_INSPECTOR_AVAILABLE:
        return {"error": "File inspector not available"}
    result = await asyncio.to_thread(inspect_and_ask)
    if not result:
        return {"found": None, "message": "Nothing new or interesting in your files right now."}
    return {"found": result}


@app.get("/love/files/summary")
async def files_summary():
    """Summary of all files LOVE has discovered."""
    if not FILE_INSPECTOR_AVAILABLE:
        return {"error": "File inspector not available"}
    return get_inspection_summary()


# ========== DECISION ENGINE ==========

@app.get("/love/decisions")
async def decisions_summary(hours: int = 24):
    """Stats on LOVE's recent autonomous decisions."""
    if not DECISIONS_AVAILABLE:
        return {"error": "Decision engine not available"}
    return await asyncio.to_thread(get_decision_stats, hours)


@app.get("/love/decisions/recent")
async def decisions_recent(limit: int = 20):
    """Recent decisions LOVE made and why."""
    if not DECISIONS_AVAILABLE:
        return {"decisions": []}
    return {"decisions": get_recent_decisions(limit)}


# ========== SANDBOX ==========

@app.post("/love/sandbox/test")
async def sandbox_test(data: dict):
    """Test code in LOVE's restricted sandbox. Payload: { code }"""
    if not SANDBOX_AVAILABLE:
        return {"error": "Sandbox not available"}
    code = data.get("code", "")
    if not code:
        return {"error": "code required"}
    result = await asyncio.to_thread(test_feature_draft, code)
    return result


@app.post("/devices/chat")
async def device_chat(data: dict):
    """
    Chat with LOVE from any device (phone app, office laptop agent).
    Payload: { text, device_id, mode }
    Returns: { response, thinking }
    """
    text = data.get("text", "")
    device_id = data.get("device_id", "unknown")
    mode = data.get("mode", "general")
    if not text:
        return {"error": "text required"}

    # Tag the context with source device
    tagged_text = f"[From: {device_id}] {text}"
    result = await asyncio.to_thread(chat, tagged_text, mode)
    return {
        "response": result.get("response", ""),
        "thinking": result.get("thinking", ""),
        "device_id": device_id,
    }


@app.post("/devices/sync-context")
async def sync_device_context(data: dict):
    """
    Sync context from a device to the central context store.
    Payload: { device_id, context: { activity, active_window, location, etc } }
    """
    device_id = data.get("device_id", "")
    if not device_id:
        return {"success": False, "error": "device_id required"}

    context = data.get("context", {})
    
    async with _devices_lock:
        devices = _load_devices()
        if device_id not in devices:
            return {"success": False, "error": "device not registered"}
        
        devices[device_id]["context"] = {
            **devices[device_id].get("context", {}),
            **context,
            "last_sync": datetime.utcnow().isoformat()
        }
        devices[device_id]["last_seen"] = datetime.utcnow().isoformat()
        _save_devices(devices)
    
    return {"success": True, "message": "Context synced"}


@app.get("/devices/context/{device_id}")
async def get_device_context(device_id: str):
    """Get context from a specific device."""
    devices = _load_devices()
    if device_id not in devices:
        return {"error": "device not found"}
    
    return {
        "device_id": device_id,
        "context": devices[device_id].get("context", {}),
        "last_sync": devices[device_id].get("context", {}).get("last_sync")
    }


@app.get("/devices/context/aggregate")
async def get_aggregated_context():
    """
    Get aggregated context from all online devices.
    Returns merged context from all active devices.
    """
    devices = _load_devices()
    now = datetime.utcnow()
    aggregated = {
        "devices": [],
        "merged_context": {
            "activities": [],
            "locations": [],
            "battery_levels": [],
            "active_windows": [],
        },
        "timestamp": now.isoformat()
    }
    
    for device_id, info in devices.items():
        last_seen = info.get("last_seen", "")
        online = False
        if last_seen:
            try:
                last_dt = datetime.fromisoformat(last_seen)
                elapsed = (now - last_dt.replace(tzinfo=None)).total_seconds()
                online = elapsed < 120
            except Exception:
                pass
        
        if online and "context" in info:
            ctx = info["context"]
            aggregated["devices"].append({
                "id": device_id,
                "name": info.get("name", device_id),
                "type": info.get("type", "unknown"),
                "context": ctx
            })
            
            # Merge context
            if ctx.get("activity"):
                aggregated["merged_context"]["activities"].append({
                    "device": device_id,
                    "activity": ctx["activity"]
                })
            if ctx.get("location"):
                aggregated["merged_context"]["locations"].append({
                    "device": device_id,
                    "location": ctx["location"]
                })
            if ctx.get("battery"):
                aggregated["merged_context"]["battery_levels"].append({
                    "device": device_id,
                    "battery": ctx["battery"]
                })
            if ctx.get("active_window"):
                aggregated["merged_context"]["active_windows"].append({
                    "device": device_id,
                    "window": ctx["active_window"]
                })
    
    return aggregated


# ========== VISION ==========

@app.post("/vision/ocr")
async def vision_ocr(data: dict):
    """Extract text from an image. Payload: { image_path }"""
    if not VISION_AVAILABLE:
        return {"error": "Vision module not available"}
    path = data.get("image_path", "")
    result = await asyncio.to_thread(read_image_text, path)
    return result


@app.post("/vision/describe")
async def vision_describe(data: dict):
    """Describe what's in an image. Payload: { image_path, detail? }"""
    if not VISION_AVAILABLE:
        return {"error": "Vision module not available"}
    path = data.get("image_path", "")
    detail = data.get("detail", "normal")
    result = await asyncio.to_thread(describe_image, path, detail)
    return result


@app.post("/vision/analyze")
async def vision_analyze(data: dict):
    """Full screenshot analysis — OCR + description + reasoning. Payload: { image_path, question? }"""
    if not VISION_AVAILABLE:
        return {"error": "Vision module not available"}
    path = data.get("image_path", "")
    question = data.get("question", "")
    result = await asyncio.to_thread(analyze_screenshot, path, question)
    return result


@app.post("/vision/detect")
async def vision_detect(data: dict):
    """Object detection in image. Payload: { image_path, confidence? }"""
    if not VISION_AVAILABLE:
        return {"error": "Vision module not available"}
    path = data.get("image_path", "")
    confidence = data.get("confidence", 0.5)
    result = await asyncio.to_thread(detect_image_objects, path, confidence)
    return result


# ========== PLANNER ==========

@app.post("/planner/plan")
async def planner_plan(data: dict):
    """Plan and execute a complex multi-step goal. Payload: { goal, context? }"""
    if not PLANNER_AVAILABLE:
        return {"error": "Planner module not available"}
    goal = data.get("goal", "")
    if not goal:
        return {"error": "goal required"}
    result = await asyncio.to_thread(plan_and_execute, goal, data.get("context"))
    return result


@app.post("/planner/is_complex")
async def planner_is_complex(data: dict):
    """Check if a query needs multi-step planning. Payload: { text }"""
    if not PLANNER_AVAILABLE:
        return {"is_complex": False}
    text = data.get("text", "")
    return {"is_complex": is_complex_query(text)}


# ========== ON-DEMAND MODELS ==========

@app.get("/love/models")
async def models_list():
    """List all available on-demand model capabilities."""
    if not ONDEMAND_AVAILABLE:
        return {"capabilities": []}
    return {"capabilities": list_capabilities()}


@app.post("/love/models/check")
async def models_check(data: dict):
    """Check if a capability is available. Payload: { name }"""
    if not ONDEMAND_AVAILABLE:
        return {"error": "On-demand models not available"}
    name = data.get("name", "")
    return check_capability(name)


@app.post("/love/models/install")
async def models_install(data: dict):
    """Install a capability. Payload: { name }"""
    if not ONDEMAND_AVAILABLE:
        return {"error": "On-demand models not available"}
    name = data.get("name", "")
    result = await asyncio.to_thread(install_capability, name)
    return result


@app.post("/love/models/run")
async def models_run(data: dict):
    """Run a capability directly. Payload: { name, ...args }"""
    if not ONDEMAND_AVAILABLE:
        return {"error": "On-demand models not available"}
    name = data.get("name", "")
    args = {k: v for k, v in data.items() if k != "name"}
    result = await asyncio.to_thread(run_capability, name, **args)
    return result


# ========== SYSTEM CONTROL (JARVIS) ==========

@app.post("/system/open")
async def system_open(data: dict):
    """Open an app/URL/file. Payload: { target }"""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    target = data.get("target", "")
    # Auto-detect type
    if target.startswith(("http://", "https://", "www.")):
        result = await asyncio.to_thread(open_url, target)
    elif "/" in target or "\\" in target or (len(target) > 1 and target[1] == ":"):
        result = await asyncio.to_thread(open_file, target)
    else:
        result = await asyncio.to_thread(open_app, target)
    return result


@app.post("/system/screenshot")
async def system_screenshot(data: dict = None):
    """Take a screenshot. Optional: { region: [x, y, w, h] }"""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    region = (data or {}).get("region")
    if region:
        region = tuple(region)
    return await asyncio.to_thread(take_screenshot, region)


@app.post("/system/type")
async def system_type(data: dict):
    """Type text into focused window. Payload: { text }"""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    return await asyncio.to_thread(type_text, data.get("text", ""))


@app.post("/system/key")
async def system_key(data: dict):
    """Press key or hotkey. Payload: { key }"""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    return await asyncio.to_thread(press_key, data.get("key", ""))


@app.post("/system/media")
async def system_media(data: dict):
    """Media control. Payload: { action: play_pause/next/prev/volume_up/volume_down/mute }"""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    return await asyncio.to_thread(media_control, data.get("action", ""))


@app.post("/system/lock")
async def system_lock():
    """Lock the screen."""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    return await asyncio.to_thread(lock_screen)


@app.get("/system/windows")
async def system_windows():
    """List open windows."""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    return await asyncio.to_thread(list_open_windows)


@app.post("/system/focus")
async def system_focus(data: dict):
    """Focus a window by title substring. Payload: { title }"""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    return await asyncio.to_thread(focus_window, data.get("title", ""))


@app.post("/system/shell")
async def system_shell(data: dict):
    """Run a whitelisted shell command. Payload: { command }"""
    if not SYSCTRL_AVAILABLE:
        return {"error": "System control not available"}
    return await asyncio.to_thread(run_shell, data.get("command", ""))


@app.get("/system/actions/recent")
async def system_actions_recent(limit: int = 20):
    """Recent system actions log."""
    if not SYSCTRL_AVAILABLE:
        return {"actions": []}
    return {"actions": get_recent_actions(limit)}


# ========== PREDICTIVE ==========

@app.get("/love/predict")
async def love_predict():
    """LOVE's current prediction of what Karthi might need."""
    if not PREDICTIVE_AVAILABLE:
        return {"prediction": None}
    return {"prediction": predict_next_need()}


@app.get("/love/predict/summary")
async def love_predict_summary():
    """Full predictive engine state."""
    if not PREDICTIVE_AVAILABLE:
        return {"error": "Predictive engine not available"}
    return get_predictive_summary()


@app.get("/love/predict/routines")
async def love_predict_routines():
    """Detected recurring routines."""
    if not PREDICTIVE_AVAILABLE:
        return {"routines": []}
    return {"routines": detect_routines()}


@app.get("/love/predict/recent")
async def love_predict_recent(limit: int = 20):
    if not PREDICTIVE_AVAILABLE:
        return {"predictions": []}
    return {"predictions": get_recent_predictions(limit)}


# ========== KNOWLEDGE GRAPH ==========

@app.get("/love/kg/summary")
async def kg_summary():
    """Knowledge graph stats."""
    if not KG_AVAILABLE:
        return {"error": "Knowledge graph not available"}
    return graph_summary()


@app.get("/love/kg/how_is")
async def kg_how_is(name: str):
    """How is X? Pull recent emotional/project signals about an entity."""
    if not KG_AVAILABLE:
        return {"error": "Knowledge graph not available"}
    return how_is(name)


@app.get("/love/kg/find")
async def kg_find(query: str, type: Optional[str] = None, limit: int = 10):
    """Find entities by name."""
    if not KG_AVAILABLE:
        return {"entities": []}
    return {"entities": find_entities(query, type, limit)}


@app.get("/love/kg/relations")
async def kg_relations(name: str, type: Optional[str] = None,
                       direction: str = "both", limit: int = 20):
    """Get all relations for an entity."""
    if not KG_AVAILABLE:
        return {"relations": []}
    return {"relations": get_relations(name, type, direction, limit)}


@app.get("/love/kg/stale")
async def kg_stale(days: int = 14):
    """Things Karthi hasn't talked about lately — for proactive checkin."""
    if not KG_AVAILABLE:
        return {"stale": []}
    return {"stale": stale_things(days)}


@app.post("/love/kg/ingest")
async def kg_ingest_endpoint(data: dict):
    """Manually ingest text into the knowledge graph. Payload: { text, source? }"""
    if not KG_AVAILABLE:
        return {"error": "Knowledge graph not available"}
    text = data.get("text", "")
    source = data.get("source", "manual")
    return await asyncio.to_thread(kg_ingest, text, source)


# ========== CONVERSATION FLOW ==========

@app.get("/love/flow")
async def flow_status():
    """Current conversation flow state."""
    if not FLOW_AVAILABLE:
        return {"error": "Flow tracker not available"}
    return get_session_summary()


@app.post("/love/flow/reset")
async def flow_reset():
    """Force a new conversation session."""
    if not FLOW_AVAILABLE:
        return {"error": "Flow tracker not available"}
    return reset_session()


# ========== VOICE LOOP ==========

@app.post("/voice/loop/start")
async def voice_loop_start():
    """Start always-listening wake word loop ('Hey LOVE')."""
    if not VOICE_LOOP_AVAILABLE:
        return {"error": "Voice loop not available"}
    return await asyncio.to_thread(start_voice_loop)


@app.post("/voice/loop/stop")
async def voice_loop_stop():
    """Stop the voice loop."""
    if not VOICE_LOOP_AVAILABLE:
        return {"error": "Voice loop not available"}
    return stop_voice_loop()


@app.get("/voice/loop/status")
async def voice_loop_status():
    """Get voice loop status."""
    if not VOICE_LOOP_AVAILABLE:
        return {"available": False}
    return get_voice_status()


@app.get("/voice/command-suggestions")
async def voice_command_suggestions():
    """Get proactive voice command suggestions based on current context."""
    try:
        from voice.stt import WhisperTranscriber
        transcriber = WhisperTranscriber()
        suggestions = transcriber.get_proactive_command_suggestions()
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        return {"error": str(e), "suggestions": []}


# ========== PROACTIVE INTERRUPTIONS ==========

@app.post("/proactive/evaluate")
async def proactive_evaluate(data: dict):
    """Evaluate a situation and potentially interrupt. Payload: situation dict with type, title, message, urgency"""
    if not PROACTIVE_AVAILABLE:
        return {"error": "Proactive engine not available"}
    result = await asyncio.to_thread(evaluate_and_act, data)
    return {"delivered": result is not None, "result": result}


@app.post("/proactive/score")
async def proactive_score(data: dict):
    """Score whether a situation warrants interruption."""
    if not PROACTIVE_AVAILABLE:
        return {"error": "Proactive engine not available"}
    return score_interruption(data)


@app.post("/proactive/reaction")
async def proactive_reaction(data: dict):
    """Record user reaction to an interruption. Payload: { ts, reaction: engaged/ignored/dismissed/annoyed/grateful }"""
    if not PROACTIVE_AVAILABLE:
        return {"error": "Proactive engine not available"}
    return await asyncio.to_thread(record_reaction, data.get("ts", ""), data.get("reaction", ""))


@app.post("/proactive/dnd")
async def proactive_dnd(data: dict):
    """Set do-not-disturb. Payload: { minutes, reason? }"""
    if not PROACTIVE_AVAILABLE:
        return {"error": "Proactive engine not available"}
    return set_do_not_disturb(data.get("minutes", 60), data.get("reason", ""))


@app.post("/proactive/dnd/clear")
async def proactive_dnd_clear():
    if not PROACTIVE_AVAILABLE:
        return {"error": "Proactive engine not available"}
    return clear_dnd()


@app.get("/proactive/stats")
async def proactive_stats():
    """Interruption stats and receptivity scores."""
    if not PROACTIVE_AVAILABLE:
        return {"error": "Proactive engine not available"}
    return get_interruption_stats()


# ========== EXECUTIVE ASSISTANT ==========

@app.post("/executive/prep_meeting")
async def exec_prep(data: dict):
    """Prep for a meeting. Payload: { subject, start_time? }"""
    if not EXECUTIVE_AVAILABLE:
        return {"error": "Executive module not available"}
    return await asyncio.to_thread(prep_for_meeting, data.get("subject", ""), data.get("start_time"))


@app.post("/executive/tasks")
async def exec_add_task(data: dict):
    """Add a task. Payload: { text, deadline?, source? }"""
    if not EXECUTIVE_AVAILABLE:
        return {"error": "Executive module not available"}
    return await asyncio.to_thread(add_task, data.get("text", ""), data.get("deadline"), data.get("source", "api"))


@app.get("/executive/tasks")
async def exec_get_tasks(filter: str = "active"):
    if not EXECUTIVE_AVAILABLE:
        return {"tasks": []}
    return {"tasks": get_tasks(filter)}


@app.post("/executive/tasks/complete")
async def exec_complete_task(data: dict):
    if not EXECUTIVE_AVAILABLE:
        return {"error": "Executive module not available"}
    return complete_task(data.get("task_id", 0))


@app.post("/executive/followup")
async def exec_followup(data: dict):
    """Draft a follow-up email. Payload: { meeting_subject, key_points[], action_items[], recipient? }"""
    if not EXECUTIVE_AVAILABLE:
        return {"error": "Executive module not available"}
    return {
        "draft": draft_follow_up(
            data.get("meeting_subject", ""),
            data.get("key_points", []),
            data.get("action_items", []),
            data.get("recipient")
        )
    }


@app.get("/executive/brief")
async def exec_brief():
    """LOVE's daily briefing."""
    if not EXECUTIVE_AVAILABLE:
        return {"error": "Executive module not available"}
    return await asyncio.to_thread(generate_daily_brief)


@app.get("/neural/briefing/status")
async def neural_briefing_status():
    """BriefingPanel: get daily briefing daemon status."""
    try:
        from core.daily_briefing import get_briefing_system
        return get_briefing_system().get_status()
    except Exception as e:
        return {"running": False, "error": str(e)}


@app.get("/neural/briefing/latest")
async def neural_briefing_latest():
    """BriefingPanel: fetch latest generated brief."""
    try:
        from core.daily_briefing import get_briefing_system
        sys = get_briefing_system()
        brief = sys.get_last_brief()
        return {"available": brief is not None, "briefing": brief}
    except Exception as e:
        return {"available": False, "error": str(e)}


@app.post("/neural/briefing/generate")
async def neural_briefing_generate(force: bool = False):
    """BriefingPanel: manually generate brief now."""
    try:
        from core.daily_briefing import get_briefing_system
        brief = await asyncio.to_thread(get_briefing_system().generate_brief, force)
        return {"status": "ok", "briefing": brief}
    except Exception as e:
        return {"error": str(e)}


@app.post("/neural/briefing/set-time")
async def neural_briefing_set_time(data: dict):
    """BriefingPanel: change daily brief delivery time (HH:MM)."""
    try:
        from core.daily_briefing import get_briefing_system
        t = data.get("time", "08:00")
        get_briefing_system().set_brief_time(t)
        return {"status": "ok", "brief_time": t}
    except Exception as e:
        return {"error": str(e)}


@app.get("/briefing/latest")
async def briefing_latest():
    """Get the most recent daily brief (Wave 30 — on-demand fetch for UI)."""
    try:
        from core.daily_briefing import get_briefing_system
        sys = get_briefing_system()
        brief = sys.get_last_brief()
        status = sys.get_status()
        return {
            "available": brief is not None,
            "briefing": brief,
            "status": status,
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


@app.post("/briefing/now")
async def briefing_trigger_now():
    """Manually trigger a daily brief right now (for testing or re-delivery)."""
    try:
        from core.daily_briefing import get_briefing_system
        sys = get_briefing_system()
        brief = await asyncio.to_thread(sys.generate_brief, True)
        return {"status": "delivered", "preview": (brief.get("text", "") or "")[:300]}
    except Exception as e:
        return {"error": str(e)}


@app.post("/executive/reminder")
async def exec_reminder(data: dict):
    """Set a reminder. Payload: { text, trigger_at: '+30m' | '+2h' | 'tomorrow' | ISO }"""
    if not EXECUTIVE_AVAILABLE:
        return {"error": "Executive module not available"}
    return await asyncio.to_thread(set_reminder, data.get("text", ""), data.get("trigger_at", ""))


@app.get("/executive/reminders/due")
async def exec_reminders_due():
    if not EXECUTIVE_AVAILABLE:
        return {"reminders": []}
    return {"reminders": check_due_reminders()}


# ========== EMOTIONAL INTELLIGENCE ==========

@app.post("/emotional/detect")
async def emotional_detect(data: dict):
    """Detect mood from text. Payload: { text }"""
    if not EMOTIONAL_AVAILABLE:
        return {"error": "Emotional module not available"}
    return detect_mood(data.get("text", ""))


@app.post("/emotional/record")
async def emotional_record(data: dict):
    """Record mood from text, update stress tracking, and push proactive response."""
    if not EMOTIONAL_AVAILABLE:
        return {"error": "Emotional module not available"}
    result = await asyncio.to_thread(record_mood, data.get("text", ""))
    # Wave 27: proactive push when mood warrants immediate response
    try:
        from core.emotional import get_current_dominant_mood
        from core.emotional_behavior import get_proactive_mood_response
        mood_state = get_current_dominant_mood()
        push_msg = get_proactive_mood_response(mood_state)
        if push_msg:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            engine.push(
                push_msg["category"],
                push_msg["message"],
                push_msg["priority"],
            )
    except Exception:
        pass
    return result


@app.get("/emotional/summary")
async def emotional_summary():
    """Get emotional/stress summary."""
    if not EMOTIONAL_AVAILABLE:
        return {"error": "Emotional module not available"}
    return get_emotional_summary()


@app.get("/emotional/tone")
async def emotional_tone():
    """Get current tone override for LOVE."""
    if not EMOTIONAL_AVAILABLE:
        return {"tone": None}
    return {"tone": get_tone_override()}


# ========== ENHANCED SYSTEM CONTROL ==========

@app.get("/system/clipboard")
async def system_clipboard_get():
    """Read clipboard content."""
    if not SYSCTRL_DEEP:
        return {"error": "Deep system control not available"}
    return await asyncio.to_thread(get_clipboard)


@app.post("/system/clipboard")
async def system_clipboard_set(data: dict):
    """Write to clipboard. Payload: { text }"""
    if not SYSCTRL_DEEP:
        return {"error": "Deep system control not available"}
    return await asyncio.to_thread(set_clipboard, data.get("text", ""))


@app.get("/system/active_window")
async def system_active_window():
    """Get currently focused window."""
    if not SYSCTRL_DEEP:
        return {"error": "Deep system control not available"}
    return await asyncio.to_thread(get_active_window)


@app.get("/system/processes")
async def system_processes(name: Optional[str] = None, limit: int = 20):
    """List running processes."""
    if not SYSCTRL_DEEP:
        return {"error": "Deep system control not available"}
    return await asyncio.to_thread(list_processes, name, limit)


@app.post("/system/kill")
async def system_kill(data: dict):
    """Kill a process. Payload: { name? or pid? }"""
    if not SYSCTRL_DEEP:
        return {"error": "Deep system control not available"}
    return await asyncio.to_thread(kill_process, data.get("name"), data.get("pid"))


@app.get("/system/search_files")
async def system_search_files(query: str, root: Optional[str] = None, max_results: int = 20):
    """Search for files by name."""
    if not SYSCTRL_DEEP:
        return {"error": "Deep system control not available"}
    return await asyncio.to_thread(search_files, query, root, max_results)


@app.get("/system/info")
async def system_info():
    """System health snapshot."""
    if not SYSCTRL_DEEP:
        return {"error": "Deep system control not available"}
    return await asyncio.to_thread(get_system_info)


# ========== LONG-TERM MEMORY (Companion for Life) ==========

@app.post("/memory/life/episodic")
async def ltm_add_episodic(data: dict):
    """Add a life event. Payload: { summary, detail?, timestamp?, emotion?, intensity?, people[], location?, tags[], source? }"""
    if not LTM_AVAILABLE:
        return {"error": "Long-term memory not available"}
    return add_episodic(**{k: v for k, v in data.items() if k != "detail" or v})


@app.post("/memory/life/semantic")
async def ltm_add_semantic(data: dict):
    """Add a fact. Payload: { category, subject, predicate, object, confidence? }"""
    if not LTM_AVAILABLE:
        return {"error": "Long-term memory not available"}
    return add_semantic(
        data.get("category", ""), data.get("subject", ""),
        data.get("predicate", ""), data.get("object", ""),
        data.get("confidence", 1.0))


@app.post("/memory/life/procedural")
async def ltm_add_procedural(data: dict):
    """Add a learned procedure. Payload: { situation, action, outcome?, success? }"""
    if not LTM_AVAILABLE:
        return {"error": "Long-term memory not available"}
    return add_procedural(
        data.get("situation", ""), data.get("action", ""),
        data.get("outcome", ""), data.get("success", True))


@app.get("/memory/life/remember")
async def ltm_remember(q: str, limit: int = 10):
    """Query all memory types. /memory/life/remember?q=Karthi+brother"""
    if not LTM_AVAILABLE:
        return {"error": "Long-term memory not available"}
    return remember(q, limit)


@app.get("/memory/life/timeline")
async def ltm_timeline(year: Optional[int] = None, month: Optional[int] = None):
    """Get episodic timeline."""
    if not LTM_AVAILABLE:
        return {"events": []}
    return {"events": get_life_timeline(year, month)}


@app.get("/memory/life/summary")
async def ltm_summary(period: str = "all"):
    """Life summary: today, week, month, year, all."""
    if not LTM_AVAILABLE:
        return {"error": "Long-term memory not available"}
    return get_life_summary(period)


@app.get("/memory/life/profile")
async def ltm_profile():
    """Karthi's complete semantic profile."""
    if not LTM_AVAILABLE:
        return {"error": "Long-term memory not available"}
    return get_karthi_profile()


@app.get("/memory/life/semantic/query")
async def ltm_semantic_query(category: Optional[str] = None, subject: Optional[str] = None, limit: int = 20):
    """Query semantic facts."""
    if not LTM_AVAILABLE:
        return {"facts": []}
    return {"facts": query_semantic(category, subject, limit=limit)}


# ── Consolidation ────────────────────────────────────────────────────────────

@app.post("/memory/consolidate")
async def memory_consolidate(data: dict = None):
    """Run consolidation. Payload: { hours? } defaults to last 24h."""
    if not CONSOLIDATION_AVAILABLE:
        return {"error": "Consolidation not available"}
    hours = (data or {}).get("hours", 24)
    return await asyncio.to_thread(consolidate_period, hours)


@app.get("/memory/consolidation/history")
async def consolidation_history(days: int = 7):
    """What LOVE has been learning."""
    if not CONSOLIDATION_AVAILABLE:
        return {"history": []}
    return {"history": get_consolidation_history(days)}


@app.get("/intelligence/dream-insights")
def get_dream_insights():
    """Get LOVE's deep insights from dream processing."""
    try:
        from core.dream_engine import get_dream_insights, get_active_predictions, get_world_model
        return {
            "insights": get_dream_insights(),
            "active_predictions": get_active_predictions()[:5],
            "world_model_people": len(get_world_model().get("people", {})),
            "world_model_routines": len(get_world_model().get("routines", {})),
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/intelligence/predictions")
def get_predictions():
    """Get LOVE's active predictions."""
    try:
        from core.prediction_market import get_active_predictions, get_accuracy_report
        return {
            "active": get_active_predictions()[:10],
            "accuracy": get_accuracy_report(),
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/intelligence/curiosity-gaps")
def get_curiosity_gaps():
    """Get knowledge gaps LOVE is working to fill."""
    try:
        from core.curiosity_engine import get_gap_count, _load_gaps
        gaps = _load_gaps()
        open_gaps = [g for g in gaps if g.get("status") == "open"]
        return {
            "total": len(gaps),
            "open": len(open_gaps),
            "resolved": len(gaps) - len(open_gaps),
            "top_gaps": open_gaps[:5],
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/intelligence/self-evolution")
def get_self_evolution_status():
    """Get LOVE's self-evolution status and active experiments."""
    try:
        from core.self_evolution import get_evolution_status
        result = get_evolution_status()
        
        # Augment with evolution integration data
        try:
            from core.evolution_integration import get_evolution_integration
            evo = get_evolution_integration()
            result["integration"] = evo.get_integration_status()
        except Exception:
            pass
        
        # Augment with capability gap data
        try:
            from core.capability_gap_detector import get_capability_gap_detector
            detector = get_capability_gap_detector()
            gaps = detector.detect_all_gaps()
            result["capability_gaps"] = {
                "total": len(gaps),
                "high_impact": len([g for g in gaps if g.impact > 0.6]),
                "domains": list(set(g.domain for g in gaps)),
            }
        except Exception:
            pass
        
        # Augment with evolution health
        try:
            from api.evolution_routes import router as evo_router
            # Directly call the health function
            from core.evolution_integration import get_evolution_integration
            from core.meta_evolution import get_meta_evolution
            from core.swarm_evolution import get_swarm_evolution
            from core.self_coder import get_self_coder
            from core.cross_instance_learning import get_cross_instance_learning
            from core.capability_gap_detector import get_capability_gap_detector
            from core.autonomous_cicd import get_autonomous_cicd
            from core.neural_architecture_search import get_neural_architecture_search
            from core.multimodal_evolution import get_multimodal_evolution
            from agents.task_evolution_integration import get_task_evolution_integration
            from agents.fitness_evolution_integration import get_fitness_evolution_integration
            from core.mcp_host import get_mcp_host
            from core.code_sandbox import get_code_sandbox
            from core.observability import get_observability_engine
            from core.guardrails import get_guardrails_engine
            evo_int = get_evolution_integration()
            result["health"] = {
                "integration": {"running": evo_int._running},
                "meta_evolution": {"running": get_meta_evolution()._running},
                "swarm_evolution": {"running": get_swarm_evolution()._running},
                "self_coder": {"running": get_self_coder()._running},
                "cross_instance": {"running": get_cross_instance_learning()._running},
                "capability_gap_detector": {"running": get_capability_gap_detector()._running},
                "autonomous_cicd": {"running": get_autonomous_cicd()._running},
                "neural_architecture_search": {"running": get_neural_architecture_search()._running},
                "multimodal_evolution": {"running": get_multimodal_evolution()._running},
                "task_evolution": {"running": get_task_evolution_integration()._running},
                "fitness_evolution": {"running": get_fitness_evolution_integration()._running},
                "mcp_host": {"available": get_mcp_host().get_health().get("sdk_available", False)},
                "reasoning_engine": {"available": True},
                "vector_memory": {"available": True},
                "code_sandbox": {"available": True},
                "observability": {"running": get_observability_engine()._running},
                "guardrails": {"available": True},
                "llm_manager": {"available": len(get_llm_manager()._models) > 0},
                "graph_rag": {"available": True},
                "prompt_optimizer": {"available": True},
                "self_reflection": {"available": True},
                "conversation_quality": {"available": True},
                "predictive_maintenance": {"available": True},
                "overall": "healthy" if evo_int._running else "degraded",
            }
        except Exception:
            pass

        # Augment with autonomous CI/CD data
        try:
            from core.autonomous_cicd import get_autonomous_cicd
            cicd = get_autonomous_cicd()
            deps = list(cicd._deployments.values())[-5:]
            result["deployments"] = [
                {"id": d.id, "version": d.version, "status": d.status, "stages": {k: v.status for k, v in d.stages.items()}}
                for d in deps
            ]
        except Exception:
            pass
        
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/intelligence/force-dream")
def force_dream():
    """Manually trigger a dream cycle."""
    try:
        from core.dream_engine import run_dream
        result = run_dream()
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/intelligence/force-evolution")
def force_evolution():
    """Manually trigger a self-evolution cycle."""
    try:
        from core.self_evolution import run_evolution_cycle
        result = run_evolution_cycle()
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/vision/desktop")
def vision_desktop():
    """Get LOVE's current view of the desktop — active window + screen text."""
    try:
        from core.vision import get_desktop_context
        return get_desktop_context()
    except Exception as e:
        return {"error": str(e)}


@app.get("/vision/window")
def vision_window():
    """Get currently focused window info."""
    try:
        from core.vision import get_active_window_info
        return get_active_window_info()
    except Exception as e:
        return {"error": str(e)}


@app.get("/emotional/state")
def emotional_state():
    """Get Karthi's current emotional state and stress level."""
    try:
        from core.emotional import get_emotional_summary, _load_stress
        summary = get_emotional_summary(days=7)
        stress = _load_stress()
        return {
            **summary,
            "current_stress": round(stress.get("current_level", 0), 1),
            "trend": stress.get("trend", "stable"),
            "history": stress.get("history", [])[-10:],
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/emotional/relationships")
def emotional_relationships():
    """Get tracked relationships and their emotional context."""
    try:
        from core.emotional import get_relationship_summary
        return get_relationship_summary()
    except Exception as e:
        return {"error": str(e)}


@app.post("/evolution/trigger-cycle")
def trigger_evolution_cycle():
    """Manually trigger a self-evolution cycle."""
    try:
        from core.self_evolution import trigger_evolution_cycle
        result = trigger_evolution_cycle()
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/evolution/behavior-state")
def get_behavior_state():
    """Get current behavioral modifiers LOVE is applying."""
    try:
        from core.self_evolution import get_behavior_state
        return get_behavior_state()
    except Exception as e:
        return {"error": str(e)}


@app.get("/evolution/performance")
def get_evolution_performance():
    """Get recent performance metrics for evolution."""
    try:
        from core.self_evolution import measure_recent_performance
        perf = measure_recent_performance(window_hours=24)
        return perf
    except Exception as e:
        return {"error": str(e)}


# ========== AGI-LEVEL SYSTEMS ENDPOINTS ==========

@app.get("/agi/autonomous/goals")
async def get_autonomous_goals():
    """Get all autonomous goals LOVE has set."""
    if not AUTONOMOUS_AGENT_AVAILABLE:
        return {"error": "Autonomous agent not available"}
    try:
        agent = get_autonomous_agent()
        return {"goals": agent.get_all_goals()}
    except Exception as e:
        return {"error": str(e)}


@app.post("/agi/autonomous/generate-goals")
async def generate_autonomous_goals():
    """Generate autonomous goals based on current context."""
    if not AUTONOMOUS_AGENT_AVAILABLE:
        return {"error": "Autonomous agent not available"}
    try:
        agent = get_autonomous_agent()
        goal_ids = agent.generate_autonomous_goals()
        return {"generated_goals": goal_ids, "count": len(goal_ids)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/psychological/profile")
async def get_psychological_profile():
    """Get Karthi's psychological profile."""
    if not PSYCHOLOGICAL_MODEL_AVAILABLE:
        return {"error": "Psychological model not available"}
    try:
        model = get_psychological_model()
        return model.get_profile_summary()
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/predictions")
async def get_predictions():
    """Get active predictions about Karthi's needs."""
    if not PREDICTIVE_INTELLIGENCE_AVAILABLE:
        return {"error": "Predictive intelligence not available"}
    try:
        engine = get_predictive_engine()
        predictions = engine.generate_predictions()
        return {"predictions": [p.__dict__ for p in predictions]}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/predictions/needs")
async def anticipate_needs():
    """Anticipate what Karthi will need in the near future."""
    if not PREDICTIVE_INTELLIGENCE_AVAILABLE:
        return {"error": "Predictive intelligence not available"}
    try:
        engine = get_predictive_engine()
        ctx = get_live_context()
        needs = engine.anticicipate_needs({"stress_level": ctx.stress_level, "energy_level": ctx.energy_level})
        return {"anticipated_needs": needs}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/self-improvement/performance")
async def get_self_improvement_performance():
    """Get LOVE's self-improvement performance report."""
    if not SELF_IMPROVEMENT_AVAILABLE:
        return {"error": "Self-improvement engine not available"}
    try:
        engine = get_self_improvement_engine()
        return engine.get_performance_report()
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/strategic/plans")
async def get_strategic_plans():
    """Get all strategic plans."""
    if not STRATEGIC_PLANNING_AVAILABLE:
        return {"error": "Strategic planner not available"}
    try:
        planner = get_strategic_planner()
        return {"plans": planner.get_all_plans()}
    except Exception as e:
        return {"error": str(e)}


@app.post("/agi/strategic/generate-default")
async def generate_default_strategies():
    """Generate default strategic plans based on psychological profile."""
    if not STRATEGIC_PLANNING_AVAILABLE:
        return {"error": "Strategic planner not available"}
    try:
        planner = get_strategic_planner()
        plan_ids = planner.generate_default_strategies()
        return {"generated_plans": plan_ids, "count": len(plan_ids)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/strategic/weekly")
async def get_weekly_strategy():
    """Get weekly strategy based on long-term plans."""
    if not STRATEGIC_PLANNING_AVAILABLE:
        return {"error": "Strategic planner not available"}
    try:
        planner = get_strategic_planner()
        return planner.generate_weekly_strategy()
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/actions/pending")
async def get_pending_actions():
    """Get actions pending approval or execution."""
    if not AUTONOMOUS_ACTIONS_AVAILABLE:
        return {"error": "Autonomous action executor not available"}
    try:
        executor = get_autonomous_executor()
        return {"pending_actions": executor.get_pending_actions()}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/actions/history")
async def get_action_history(limit: int = 50):
    """Get recent action history."""
    if not AUTONOMOUS_ACTIONS_AVAILABLE:
        return {"error": "Autonomous action executor not available"}
    try:
        executor = get_autonomous_executor()
        return {"history": executor.get_action_history(limit)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/actions/approvals/pending")
async def get_pending_approvals():
    """Get actions awaiting user approval."""
    if not AUTONOMOUS_ACTIONS_AVAILABLE:
        return {"error": "Autonomous action executor not available"}
    try:
        executor = get_autonomous_executor()
        return {"pending_approvals": executor.get_pending_approvals()}
    except Exception as e:
        return {"error": str(e)}


@app.post("/agi/actions/approve")
async def approve_action(data: dict):
    """Approve a pending action for execution."""
    if not AUTONOMOUS_ACTIONS_AVAILABLE:
        return {"error": "Autonomous action executor not available"}
    try:
        action_id = data.get("action_id")
        approved_by = data.get("approved_by", "user")
        if not action_id:
            return {"error": "action_id required"}
        
        executor = get_autonomous_executor()
        success = executor.approve_action(action_id, approved_by)
        return {"success": success, "action_id": action_id}
    except Exception as e:
        return {"error": str(e)}


@app.post("/agi/actions/reject")
async def reject_action(data: dict):
    """Reject a pending action."""
    if not AUTONOMOUS_ACTIONS_AVAILABLE:
        return {"error": "Autonomous action executor not available"}
    try:
        action_id = data.get("action_id")
        reason = data.get("reason", "User rejected")
        rejected_by = data.get("rejected_by", "user")
        if not action_id:
            return {"error": "action_id required"}
        
        executor = get_autonomous_executor()
        success = executor.reject_action(action_id, reason, rejected_by)
        return {"success": success, "action_id": action_id}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/world/knowledge")
async def get_world_knowledge():
    """Get LOVE's world model knowledge summary."""
    if not WORLD_MODEL_AVAILABLE:
        return {"error": "World model not available"}
    try:
        model = get_world_model()
        return model.get_knowledge_summary()
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/meta-cognition/summary")
async def get_meta_cognitive_summary():
    """Get LOVE's meta-cognitive state summary."""
    if not META_COGNITION_AVAILABLE:
        return {"error": "Meta-cognition engine not available"}
    try:
        engine = get_meta_cognition_engine()
        return engine.get_meta_cognitive_summary()
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/meta-cognition/improvement-suggestions")
async def get_self_improvement_suggestions():
    """Get LOVE's self-improvement suggestions based on meta-cognitive analysis."""
    if not META_COGNITION_AVAILABLE:
        return {"error": "Meta-cognition engine not available"}
    try:
        engine = get_meta_cognition_engine()
        suggestions = engine.generate_self_improvement_suggestions()
        return {"suggestions": suggestions, "count": len(suggestions)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/cross-domain/holistic")
async def get_holistic_view():
    """Get holistic view of all domains and their interconnections."""
    if not CROSS_DOMAIN_REASONING_AVAILABLE:
        return {"error": "Cross-domain reasoner not available"}
    try:
        reasoner = get_cross_domain_reasoner()
        return reasoner.get_holistic_view()
    except Exception as e:
        return {"error": str(e)}


@app.post("/agi/cross-domain/analyze-impact")
async def analyze_cross_domain_impact(change: dict):
    """Analyze how a change in one domain affects other domains."""
    if not CROSS_DOMAIN_REASONING_AVAILABLE:
        return {"error": "Cross-domain reasoner not available"}
    try:
        reasoner = get_cross_domain_reasoner()
        return reasoner.analyze_cross_domain_impact(change)
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/learning/summary")
async def get_learning_summary():
    """Get LOVE's continuous learning summary."""
    if not CONTINUOUS_LEARNING_AVAILABLE:
        return {"error": "Continuous learning engine not available"}
    try:
        engine = get_continuous_learning_engine()
        return engine.get_learning_summary()
    except Exception as e:
        return {"error": str(e)}


@app.post("/agi/learning/record")
async def record_learning_experience(data: dict):
    """Record a learning experience."""
    if not CONTINUOUS_LEARNING_AVAILABLE:
        return {"error": "Continuous learning engine not available"}
    try:
        engine = get_continuous_learning_engine()
        from core.continuous_learning import LearningSourceType, LearningType
        exp_id = engine.record_experience(
            source_type=LearningSourceType(data.get("source_type")),
            learning_type=LearningType(data.get("learning_type")),
            description=data.get("description"),
            context=data.get("context", {}),
            outcome=data.get("outcome"),
            lesson=data.get("lesson"),
            confidence=data.get("confidence", 0.5)
        )
        return {"experience_id": exp_id}
    except Exception as e:
        return {"error": str(e)}


@app.get("/agi/status")
async def get_agi_status():
    """Get status of all AGI-level systems."""
    from core.agi_spine import get_agi_system_flags
    spine_flags = get_agi_system_flags()
    core_flags = {
        "autonomous_agent": AUTONOMOUS_AGENT_AVAILABLE,
        "psychological_model": PSYCHOLOGICAL_MODEL_AVAILABLE,
        "predictive_intelligence": PREDICTIVE_INTELLIGENCE_AVAILABLE,
        "self_improvement": SELF_IMPROVEMENT_AVAILABLE,
        "strategic_planning": STRATEGIC_PLANNING_AVAILABLE,
        "autonomous_actions": AUTONOMOUS_ACTIONS_AVAILABLE,
        "world_model": WORLD_MODEL_AVAILABLE,
        "meta_cognition": META_COGNITION_AVAILABLE,
        "cross_domain_reasoning": CROSS_DOMAIN_REASONING_AVAILABLE,
        "continuous_learning": CONTINUOUS_LEARNING_AVAILABLE,
        "consciousness": CONSCIOUSNESS_AVAILABLE,
        "temporal_memory": TEMPORAL_MEMORY_AVAILABLE,
        "reasoning_chain": REASONING_CHAIN_AVAILABLE,
        "evolution_integration": EVOLUTION_INTEGRATION_AVAILABLE,
        "meta_evolution": META_EVOLUTION_AVAILABLE,
        "swarm_evolution": SWARM_EVOLUTION_AVAILABLE,
        "self_coder": SELF_CODER_AVAILABLE,
        "cross_instance_learning": CROSS_INSTANCE_AVAILABLE,
        "capability_gap_detector": CAPABILITY_GAP_DETECTOR_AVAILABLE,
        "autonomous_cicd": AUTONOMOUS_CICD_AVAILABLE,
        "autonomy_supervisor": AUTONOMY_SUPERVISOR_AVAILABLE,
    }
    merged = {**core_flags, **spine_flags}
    total = len(merged)
    active = sum(1 for v in merged.values() if v)
    evolution_status = {}
    if EVOLUTION_INTEGRATION_AVAILABLE:
        try:
            evolution_status = get_evolution_integration().get_integration_status()
        except Exception:
            pass
    return {
        **merged,
        "total_systems": total,
        "active_systems": active,
        "evolution_integration_status": evolution_status,
    }



# Living Substrate boot moved to lifespan (avoids blocking at import time)
try:
    from core.living_substrate import substrate_snapshot

    @app.get('/substrate')
    async def get_substrate():
        return substrate_snapshot()

    @app.get('/substrate/attention')
    async def get_substrate_attention():
        from core.hierarchical_predictive_coding import get_hpc
        from core.world_model_latent import get_world_model_latent
        return {
            'level_attention': get_hpc().attention(),
            'channel_attention': get_world_model_latent().attention_distribution(),
            'inferred_activity': get_hpc().current_inferred_activity(),
        }
except Exception as e:
    substrate_snapshot = None
    print(f'[API] Living Substrate route error: {e}')

# Wave 17: Evolution Dashboard Routes
try:
    from api.evolution_routes import router as evolution_router
    app.include_router(evolution_router)
    print("[API] Wave 17 Evolution Dashboard routes loaded")
except Exception as e:
    print(f"[API] Evolution routes error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Wave 22: Life Domains API — hydration, sleep, nutrition, skincare
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel as _BM
from typing import Optional as _Opt, List as _List, Dict as _Dict

class HydrationLogRequest(_BM):
    count: int = 1
    ml: _Opt[int] = None

class SleepLogRequest(_BM):
    bedtime: str          # "HH:MM"
    wake_time: str        # "HH:MM"
    quality: int = 5
    notes: str = ""

class MealLogRequest(_BM):
    meal_type: str        # breakfast|lunch|dinner|snack
    description: str
    quality: int = 5
    calories: _Opt[int] = None
    protein_g: _Opt[int] = None
    carbs_g: _Opt[int] = None
    fat_g: _Opt[int] = None

class SkincareRoutineRequest(_BM):
    routine_type: str     # morning|evening
    steps_done: _List[str]
    products: _Opt[_Dict[str, str]] = None
    skin_notes: str = ""
    feeling: int = 5

class SkincareConcernRequest(_BM):
    concern: str
    severity: int = 3

@app.get("/life/dashboard")
async def life_dashboard():
    """Full today snapshot across all life domains + nudges + life score."""
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().get_dashboard()

@app.get("/life/insights")
async def life_insights():
    """7-day insights across all life domains."""
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().get_weekly_insights()

@app.get("/life/streaks")
async def life_streaks():
    """Current streaks for all life domains."""
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().get_streaks()

@app.get("/life/nudges")
async def life_nudges():
    """Active nudges — what LOVE should be proactively saying right now."""
    from core.life_domains import get_life_domains_engine
    nudges = get_life_domains_engine().get_active_nudges()
    return {"nudges": nudges, "count": len(nudges)}

# Hydration
@app.get("/life/hydration/today")
async def hydration_today():
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().hydration.get_today()

@app.post("/life/hydration/log")
async def hydration_log(req: HydrationLogRequest):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().hydration.log_glass(req.count, req.ml)

@app.get("/life/hydration/insights")
async def hydration_insights(days: int = 7):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().hydration.get_insights(days)

# Sleep
@app.get("/life/sleep/today")
async def sleep_today():
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().sleep.get_today()

@app.post("/life/sleep/log")
async def sleep_log(req: SleepLogRequest):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().sleep.log_sleep(req.bedtime, req.wake_time, req.quality, req.notes)

@app.get("/life/sleep/insights")
async def sleep_insights(days: int = 7):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().sleep.get_insights(days)

# Nutrition
@app.get("/life/nutrition/today")
async def nutrition_today():
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().nutrition.get_today()

@app.post("/life/nutrition/log")
async def nutrition_log(req: MealLogRequest):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().nutrition.log_meal(
        req.meal_type, req.description, req.quality,
        req.calories, req.protein_g, req.carbs_g, req.fat_g
    )

@app.get("/life/nutrition/insights")
async def nutrition_insights(days: int = 7):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().nutrition.get_insights(days)

# Skincare
@app.get("/life/skincare/today")
async def skincare_today():
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().skincare.get_today()

@app.post("/life/skincare/routine")
async def skincare_routine(req: SkincareRoutineRequest):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().skincare.log_routine(
        req.routine_type, req.steps_done, req.products, req.skin_notes, req.feeling
    )

@app.post("/life/skincare/concern")
async def skincare_concern(req: SkincareConcernRequest):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().skincare.log_concern(req.concern, req.severity)

@app.get("/life/skincare/insights")
async def skincare_insights(days: int = 7):
    from core.life_domains import get_life_domains_engine
    return get_life_domains_engine().skincare.get_insights(days)

# ─────────────────────────────────────────────────────────────────────────────
# Wave 24: Cross-Domain Intelligence API
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/life/correlations")
async def life_correlations(days: int = 7):
    """Cross-domain correlations — sleep vs productivity, hydration vs focus, etc."""
    from core.cross_domain_intelligence import get_correlations
    return get_correlations(days)

@app.get("/life/report")
async def life_report(days: int = 7):
    """Full life report — dashboard + insights + correlations."""
    from core.cross_domain_intelligence import get_life_report
    return get_life_report(days)

# ─────────────────────────────────────────────────────────────────────────────
# Wave 25: Proactive Life Coach API
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/life/coach/nudges")
async def life_coach_nudges():
    """Time-aware, focus-aware nudges for right now."""
    from core.life_coach import get_life_coach
    nudges = get_life_coach().get_nudges()
    return {"nudges": nudges, "count": len(nudges), "timestamp": __import__("datetime").datetime.now().isoformat()}

@app.get("/life/coach/goals")
async def life_coach_goals():
    """Adaptive daily goals based on recent performance."""
    from core.life_coach import get_life_coach
    return get_life_coach().get_adaptive_goals()

# ─────────────────────────────────────────────────────────────────────────────
# Wave 23: Autonomous Wave Evolution Engine API
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/wave/status")
async def wave_status():
    """Wave engine status — running state, total waves, last cycle."""
    from core.wave_engine import get_wave_engine
    return get_wave_engine().get_status()

@app.post("/wave/scan")
async def wave_scan():
    """Run one gap-scan + wave-propose cycle now (on demand)."""
    from core.wave_engine import get_wave_engine
    return get_wave_engine().run_cycle()

@app.get("/wave/latest")
async def wave_latest():
    """Get the most recent Wave proposal."""
    from core.wave_engine import get_wave_engine
    p = get_wave_engine().get_latest_proposal()
    return p or {"message": "No waves proposed yet. Run /wave/scan first."}

@app.get("/wave/all")
async def wave_all():
    """All Wave proposals (proposed + executed)."""
    from core.wave_engine import get_wave_engine
    return get_wave_engine().get_all_waves()

@app.post("/wave/execute/{wave_number}")
async def wave_execute(wave_number: int, outcome: str = "completed"):
    """Mark a Wave as executed."""
    from core.wave_engine import get_wave_engine
    get_wave_engine().mark_wave_executed(wave_number, outcome)
    return {"ok": True, "wave_number": wave_number, "outcome": outcome}

@app.get("/wave/gaps")
async def wave_gaps():
    """Run a gap scan only (no wave proposal)."""
    from core.wave_engine import GapScanner
    return GapScanner().scan()

# ═══════════════════════════════════════════════════════════════════════════════
# HOMEOSTASIS — Biological Drives, Circadian Rhythm, Energy, Autophagy
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/homeostasis/snapshot")
async def homeostasis_snapshot():
    """Full homeostasis state: drives, circadian phase, energy, autophagy candidates."""
    try:
        from core.homeostasis import get_homeostasis
        from dataclasses import asdict
        h = get_homeostasis()
        return {
            "drives": h._drives.as_dict(),
            "dominant_drive": h._drives.dominant(),
            "circadian_phase": h._state.circadian_phase,
            "last_tick": h._state.last_tick,
            "energy_accounts": {k: asdict(v) for k, v in h._accounts.items()},
            "autophagy_candidates": list(h._autophagy.keys()),
            "autophagy_ready": h.autophagy_ready_to_remove(),
            "running": h._running,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/homeostasis/drives")
async def homeostasis_drives():
    """Current biological drive values [0..1] and dominant drive."""
    try:
        from core.homeostasis import get_homeostasis
        h = get_homeostasis()
        drives = h._drives.as_dict()
        return {"drives": drives, "dominant": h._drives.dominant(), "phase": h._state.circadian_phase}
    except Exception as e:
        return {"error": str(e)}


@app.get("/homeostasis/circadian")
async def homeostasis_circadian():
    """Current circadian phase (wake / focus / wind_down / sleep)."""
    try:
        from core.homeostasis import get_homeostasis
        h = get_homeostasis()
        return {
            "phase": h._state.circadian_phase,
            "started_at": h._state.started_at,
            "last_sleep": h._state.last_sleep,
        }
    except Exception as e:
        return {"error": str(e)}


class CircadianOverrideRequest(BaseModel):
    phase: str  # wake / focus / wind_down / sleep


@app.post("/homeostasis/circadian/override")
async def homeostasis_circadian_override(req: CircadianOverrideRequest):
    """Manually override the circadian phase."""
    valid = {"wake", "focus", "wind_down", "sleep"}
    if req.phase not in valid:
        return {"error": f"Invalid phase. Must be one of: {', '.join(valid)}"}
    try:
        from core.homeostasis import get_homeostasis
        h = get_homeostasis()
        h._state.circadian_phase = req.phase
        h._save()
        return {"ok": True, "phase": req.phase}
    except Exception as e:
        return {"error": str(e)}


@app.get("/homeostasis/energy")
async def homeostasis_energy():
    """Per-module energy budgets, spending, fat reserves, throttle status."""
    try:
        from core.homeostasis import get_homeostasis
        from dataclasses import asdict
        h = get_homeostasis()
        return {"accounts": {k: asdict(v) for k, v in h._accounts.items()}}
    except Exception as e:
        return {"error": str(e)}


class EnergyAdjustRequest(BaseModel):
    budget_seconds_per_day: float


@app.post("/homeostasis/energy/{module_name}")
async def homeostasis_energy_adjust(module_name: str, req: EnergyAdjustRequest):
    """Adjust a module's daily energy budget."""
    try:
        from core.homeostasis import get_homeostasis
        h = get_homeostasis()
        if module_name not in h._accounts:
            h.register_module(module_name, req.budget_seconds_per_day)
        else:
            h._accounts[module_name].budget_seconds_per_day = req.budget_seconds_per_day
        h._save()
        return {"ok": True, "module": module_name, "budget": req.budget_seconds_per_day}
    except Exception as e:
        return {"error": str(e)}


@app.get("/homeostasis/autophagy")
async def homeostasis_autophagy():
    """Modules flagged for potential deprecation (autophagy candidates)."""
    try:
        from core.homeostasis import get_homeostasis
        h = get_homeostasis()
        return {
            "candidates": h._autophagy,
            "ready_to_archive": h.autophagy_ready_to_remove(),
        }
    except Exception as e:
        return {"error": str(e)}


@app.delete("/homeostasis/autophagy/{module_name}")
async def homeostasis_autophagy_preserve(module_name: str):
    """Remove a module from the autophagy list (preserve it)."""
    try:
        from core.homeostasis import get_homeostasis
        h = get_homeostasis()
        if module_name in h._autophagy:
            del h._autophagy[module_name]
            h._save()
            return {"ok": True, "message": f"{module_name} preserved — removed from autophagy list"}
        return {"ok": False, "message": f"{module_name} not in autophagy list"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/homeostasis/drives/history")
async def homeostasis_drives_history(hours: int = 6):
    """Recent drive log entries for sparkline charts."""
    try:
        from pathlib import Path
        import json
        from datetime import datetime, timedelta
        log_path = Path("data/homeostasis/drives.jsonl")
        if not log_path.exists():
            return {"entries": []}
        cutoff = datetime.now() - timedelta(hours=hours)
        entries = []
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                    if datetime.fromisoformat(e["t"]) >= cutoff:
                        entries.append(e)
                except Exception:
                    pass
        return {"entries": entries[-200:]}  # cap at 200 data points
    except Exception as e:
        return {"error": str(e)}


# ========== RESOURCE GOVERNOR (Prompt 16) ==========

@app.get("/system/resources")
async def system_resources():
    """Current CPU/RAM/GPU snapshot + load state."""
    try:
        from core.resource_governor import get_resource_governor
        gov = get_resource_governor()
        snap = gov.get_snapshot()
        return {"under_load": gov.is_under_load(), **snap}
    except Exception as e:
        return {"error": str(e)}


@app.get("/system/load")
async def system_load():
    """Is the system currently under heavy load?"""
    try:
        from core.resource_governor import get_resource_governor, SYSTEM_UNDER_LOAD
        gov = get_resource_governor()
        return {
            "under_load": SYSTEM_UNDER_LOAD.is_set(),
            "reason": gov.get_snapshot().get("load_reason"),
            "snapshot": gov.get_snapshot(),
        }
    except Exception as e:
        return {"under_load": False, "error": str(e)}


@app.get("/llm/status")
async def llm_status():
    """Return the current LLM routing and fallback state."""
    try:
        from core.llm import get_current_model_info
        info = get_current_model_info()
        info["auto_fallback_enabled"] = os.getenv("OLLAMA_AUTO_FALLBACK", "true")
        info["force_high_quality"] = os.getenv("OLLAMA_FORCE_HIGH_QUALITY", "false")
        return info
    except Exception as e:
        return {"error": str(e)}


@app.get("/system/idle")
async def system_idle():
    """Current idle state: ACTIVE / RESTING / DEEP_SLEEP + idle seconds."""
    try:
        from core.idle_mind import get_idle_state, get_idle_duration
        return {
            "idle_state": get_idle_state(),
            "idle_seconds": round(get_idle_duration(), 1),
        }
    except Exception as e:
        return {"idle_state": "unknown", "error": str(e)}


@app.get("/system/model-info")
async def system_model_info():
    """Which LLM models are active right now — normal or fallback under load."""
    try:
        from core.llm import get_current_model_info
        return get_current_model_info()
    except Exception as e:
        return {"error": str(e)}


# ========== PROMPTS 21-24: CAUSAL GUARDRAIL, AXIOLOGICAL ENGINE, REALITY CHECK, TTS INTERVENTIONS ==========

@app.post("/causal/simulate")
async def causal_simulate(data: dict):
    """Run a causal guardrail sanity check on a proposed action."""
    try:
        from core.causal_guardrail import simulate_outcome
        action = data.get("action", "")
        context = data.get("context", {})
        safe = await simulate_outcome(action, context)
        return {"safe": safe, "action": action}
    except Exception as e:
        return {"error": str(e), "safe": True}  # fail-safe


@app.post("/axiological/evaluate")
async def axiological_evaluate(data: dict):
    """Evaluate whether a task should proceed based on utility formula."""
    try:
        from core.axiological_engine import evaluate_utility
        task_priority = int(data.get("task_priority", 5))
        compute_cost = int(data.get("compute_cost", 5))
        user_energy = int(data.get("user_energy", 5))
        user_stress = int(data.get("user_stress", 5))
        allowed = evaluate_utility(task_priority, compute_cost, user_energy, user_stress)
        return {"allowed": allowed}
    except Exception as e:
        return {"error": str(e), "allowed": True}  # fail-safe


@app.post("/reality/reconcile")
async def reality_reconcile(data: dict):
    """Reconcile state conflicts in user profile JSON."""
    try:
        from core.reality_check import reconcile_state_conflicts
        state = data.get("state", {})
        cleaned = reconcile_state_conflicts(state)
        return {"cleaned": cleaned}
    except Exception as e:
        return {"error": str(e)}


@app.post("/voice/intervention")
async def voice_intervention(data: dict):
    """Trigger audio intervention for work limit or high stress."""
    try:
        from voice.tts_interventions import trigger_hype_intervention
        trigger_type = data.get("trigger_type", "")
        await trigger_hype_intervention(trigger_type)
        return {"triggered": trigger_type}
    except Exception as e:
        return {"error": str(e)}


# ========== PROMPTS 25-29: SANDBOX, TOOL FORGE, DNA, HOT-SWAP, WATCHDOG ==========

@app.post("/evolution/sandbox/run")
async def sandbox_run(data: dict):
    """Run code in isolated subprocess sandbox."""
    try:
        from evolution.sandbox import run_in_sandbox
        code = data.get("code", "")
        timeout = int(data.get("timeout", 5))
        result = await run_in_sandbox(code, timeout_seconds=timeout)
        return result
    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/evolution/tool/forge")
async def tool_forge(data: dict):
    """LLM generates a new tool, tests in sandbox, saves if valid."""
    try:
        from evolution.tool_forge import forge_new_tool
        tool_name = data.get("tool_name", "")
        objective = data.get("objective", "")
        success = await forge_new_tool(tool_name, objective)
        return {"success": success, "tool_name": tool_name}
    except Exception as e:
        return {"error": str(e), "success": False}


@app.post("/dna/mutate")
async def dna_mutate(data: dict):
    """Mutate a personality trait up or down."""
    try:
        from core.dna import mutate_trait
        trait = data.get("trait", "")
        direction = data.get("direction", "")
        mutate_trait(trait, direction)
        return {"mutated": True, "trait": trait, "direction": direction}
    except Exception as e:
        return {"error": str(e), "mutated": False}


@app.get("/dna/instructions")
async def dna_instructions():
    """Get dynamic prompt instructions based on personality weights."""
    try:
        from core.dna import get_dynamic_instructions
        instructions = get_dynamic_instructions()
        return {"instructions": instructions}
    except Exception as e:
        return {"error": str(e), "instructions": ""}


@app.post("/evolution/hotswap/reload")
async def hotswap_reload(data: dict):
    """Hot-reload a module without restarting the server."""
    try:
        from evolution.hot_swapper import reload_module
        module_path = data.get("module_path", "")
        success = reload_module(module_path)
        return {"reloaded": success, "module": module_path}
    except Exception as e:
        return {"error": str(e), "reloaded": False}

# ========== PROMPTS 1-3: MOCK REALITY, E2E INSPECTOR, DEPENDENCY MAPPER ==========

@app.post("/tests/mock/burnout")
async def mock_burnout():
    """Inject mock work burnout reality for testing."""
    try:
        from tests.mock_reality import RealitySimulator
        sim = RealitySimulator()
        await sim.trigger_work_burnout()
        return {"injected": "work_burnout"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/tests/mock/crash")
async def mock_crash():
    """Inject mock market crash reality for testing."""
    try:
        from tests.mock_reality import RealitySimulator
        sim = RealitySimulator()
        await sim.trigger_market_crash()
        return {"injected": "market_crash"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/tests/mock/flow")
async def mock_flow():
    """Inject mock deep flow reality for testing."""
    try:
        from tests.mock_reality import RealitySimulator
        sim = RealitySimulator()
        await sim.trigger_deep_flow()
        return {"injected": "deep_flow"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/tests/inspector/run")
async def inspector_run(data: dict):
    """Run E2E integration inspector scenarios."""
    try:
        from tests.integration_inspector import run_all_diagnostics
        scenario = data.get("scenario", "all")
        if scenario == "all":
            result = await run_all_diagnostics()
        elif scenario == "burnout":
            from tests.integration_inspector import run_scenario_alpha_burnout
            result = await run_scenario_alpha_burnout()
        elif scenario == "flow":
            from tests.integration_inspector import run_scenario_beta_flow
            result = await run_scenario_beta_flow()
        else:
            return {"error": "Unknown scenario"}
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/tests/dependencies/map")
async def dependencies_map():
    """Map all dependencies and identify orphaned modules."""
    try:
        from scripts.map_dependencies import map_dependencies
        result = map_dependencies()
        return result
    except Exception as e:
        return {"error": str(e)}





# ========== TERMINAL ERROR MONITOR (Wave 31) ==========

@app.get("/terminal/errors")
async def terminal_errors(limit: int = 20):
    """Get recent errors detected by the terminal monitor."""
    from core.terminal_monitor import get_terminal_monitor
    return {"errors": get_terminal_monitor().get_errors(limit)}


@app.get("/terminal/fixes")
async def terminal_fixes(limit: int = 20):
    """Get recent auto-fix attempts by the terminal monitor."""
    from core.terminal_monitor import get_terminal_monitor
    return {"fixes": get_terminal_monitor().get_fixes(limit)}


@app.get("/terminal/monitor/status")
async def terminal_monitor_status():
    """Terminal monitor daemon status."""
    from core.terminal_monitor import get_terminal_monitor
    return get_terminal_monitor().get_status()


@app.post("/terminal/ingest")
async def terminal_ingest(data: dict):
    """
    Submit an error string (from frontend, mobile app, or external script) for
    LLM diagnosis and auto-fix. Used by the UI to report JS/Python errors.
    """
    from core.terminal_monitor import get_terminal_monitor
    text = data.get("error", "") or data.get("text", "")
    file = data.get("file", "")
    line = int(data.get("line", 0))
    return get_terminal_monitor().ingest_error(text, file=file, line=line)


# ── Log file capture — redirect Python's stderr to server.log so the
#    terminal monitor can see ALL uvicorn/FastAPI output including --reload ──
def _redirect_stderr_to_log():
    """Tee stderr to data/server.log without losing console output."""
    import sys
    from pathlib import Path
    log_path = Path(__file__).parent.parent / "data" / "server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    class TeeStream:
        def __init__(self, original, log_file):
            self._orig = original
            self._log = log_file

        def write(self, msg):
            self._orig.write(msg)
            try:
                self._log.write(msg)
                self._log.flush()
            except Exception:
                pass

        def flush(self):
            self._orig.flush()
            try:
                self._log.flush()
            except Exception:
                pass

        def fileno(self):
            return self._orig.fileno()

        def isatty(self):
            return False

    try:
        # Rotate: keep last 5 MB
        if log_path.exists() and log_path.stat().st_size > 5 * 1024 * 1024:
            bak = log_path.with_suffix(".log.1")
            log_path.replace(bak)
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stderr = TeeStream(sys.stderr, log_file)
        sys.stdout = TeeStream(sys.stdout, log_file)
    except Exception as e:
        print(f"[TerminalMonitor] Could not set up log capture: {e}")

_redirect_stderr_to_log()


# ========== WAVE 27: ACTIVE PLANNING + FOCUS-AWARE HEARTBEAT ==========

@app.get("/planner/snapshot")
async def planner_snapshot():
    """Get rollout planner telemetry including outcome learning stats."""
    from core.rollout_planner import get_rollout_planner
    return get_rollout_planner().snapshot()


@app.post("/planner/plan_active")
async def planner_plan_active(data: dict):
    """Run active planning for a query. Returns directive + ranked styles."""
    from core.rollout_planner import get_rollout_planner
    query = data.get("query", "")
    if not query:
        return {"error": "query required"}
    planner = get_rollout_planner()
    return planner.plan_active(query)


@app.get("/planner/calibration")
async def planner_calibration():
    """Get planning calibration state (confidence, accuracy, outcomes)."""
    from core.rollout_planner import get_rollout_planner
    planner = get_rollout_planner()
    snap = planner.snapshot()
    return {
        "confidence": snap.get("calibration_confidence", 0.5),
        "total_outcomes": snap.get("total_outcomes", 0),
        "accuracy": snap.get("outcome_accuracy", 0.0),
        "avg_prediction_delta": snap.get("avg_prediction_delta", 0.0),
    }


@app.get("/heartbeat/focus-status")
async def heartbeat_focus_status():
    """Check if heartbeat is in focus-aware suppression mode."""
    from core.heartbeat import get_heartbeat
    hb = get_heartbeat()
    in_focus = hb._is_focus_mode()
    suppressed = []
    try:
        from pathlib import Path
        import json
        queue_file = Path(__file__).parent.parent / "data" / "suppressed_nudges.json"
        if queue_file.exists():
            suppressed = json.loads(queue_file.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "focus_mode_active": in_focus,
        "suppressed_nudge_count": len(suppressed),
        "suppressed_nudges": suppressed,
    }


# ========== WAVE 28: PLANNING CALIBRATION DEPTH + PEFT EXPORT ==========

@app.get("/planner/category-stats")
async def planner_category_stats():
    """Per-category planning accuracy (casual/emotional/technical/task)."""
    from core.rollout_planner import get_rollout_planner
    planner = get_rollout_planner()
    snap = planner.snapshot()
    return {
        "per_category": snap.get("per_category_stats", {}),
        "per_style": snap.get("per_style_accuracy", {}),
        "total_outcomes": snap.get("total_outcomes", 0),
        "global_confidence": snap.get("calibration_confidence", 0.5),
    }


@app.post("/planner/detect-category")
async def planner_detect_category(data: dict):
    """Detect query category. Payload: { query: str }."""
    from core.rollout_planner import get_rollout_planner
    query = data.get("query", "")
    if not query:
        return {"error": "query required"}
    planner = get_rollout_planner()
    category = planner.detect_query_category(query)
    return {"query": query[:100], "category": category}


@app.get("/lora/export-peft/{adapter_id}")
async def lora_export_peft(adapter_id: str):
    """Export a LoRA adapter as proper PEFT checkpoint."""
    try:
        from core.lora_evolution import get_lora_evolution
        evo = get_lora_evolution()
        adapter = evo.get_adapter(adapter_id)
        if not adapter:
            return {"error": f"Adapter {adapter_id} not found"}
        path = evo.export_adapter_checkpoint(adapter)
        if not path:
            return {"error": "Export failed"}
        return {
            "adapter_id": adapter_id,
            "checkpoint_path": str(path),
            "fitness": adapter.fitness,
            "description": adapter.mutation_description,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/lora/peft-status")
async def lora_peft_status():
    """Check torch/peft availability and adapter export status."""
    import importlib.util
    torch_ok = importlib.util.find_spec("torch") is not None
    peft_ok = importlib.util.find_spec("peft") is not None
    return {
        "torch_available": torch_ok,
        "peft_available": peft_ok,
        "peft_export_ready": torch_ok,
        "note": "Install peft: pip install peft for full PEFT integration",
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  SERVE REACT UI (built to ui/dist) — mount AFTER all API routes so
#  regular endpoints take precedence, and the React SPA handles unknown paths.
# ═══════════════════════════════════════════════════════════════════════════════
UI_DIST_DIR = _os.path.join(BASE_DIR, "ui", "dist")
if _os.path.isdir(UI_DIST_DIR) and _os.path.isfile(_os.path.join(UI_DIST_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=UI_DIST_DIR, html=True), name="ui")
    print(f"[API] React UI mounted from {UI_DIST_DIR}")
else:
    print(f"[API] React UI not found at {UI_DIST_DIR} — run `npm run build` in ui/")

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

# ========== ORCHESTRATION MASTER ENDPOINTS ==========

@app.get("/orchestrator/master/status")
async def orchestrator_master_status():
    """Get full status from the Orchestration Master."""
    from core.master_orchestrator import get_orchestration_master
    om = get_orchestration_master()
    return om.get_status()

@app.get("/orchestrator/master/modules")
async def orchestrator_master_modules():
    """Get module health from the Orchestration Master."""
    from core.master_orchestrator import get_orchestration_master
    om = get_orchestration_master()
    return om.get_all_module_health()

@app.get("/orchestrator/master/narrative")
async def orchestrator_master_narrative(limit: int = 50, since_hours: float = None):
    """Get LOVE's life narrative."""
    from core.master_orchestrator import get_orchestration_master
    om = get_orchestration_master()
    return {"narrative": om.get_narrative(limit=limit, since_hours=since_hours)}

@app.get("/orchestrator/master/decisions")
async def orchestrator_master_decisions(limit: int = 20):
    """Get recent coordination decisions."""
    from core.master_orchestrator import get_orchestration_master
    om = get_orchestration_master()
    return {"decisions": om.get_recent_decisions(limit=limit)}

@app.get("/orchestrator/master/comms")
async def orchestrator_master_comms(limit: int = 30):
    """Get recent user communications."""
    from core.master_orchestrator import get_orchestration_master
    om = get_orchestration_master()
    return {"comms": om.get_user_comms(limit=limit)}

@app.post("/orchestrator/master/command")
async def orchestrator_master_command(req: dict):
    """Send a command to the Orchestration Master."""
    from core.master_orchestrator import get_orchestration_master
    om = get_orchestration_master()
    message = req.get("message", "")
    if not message:
        return {"error": "message required"}
    response = om.receive_from_user(message)
    return {"response": response, "timestamp": datetime.now().isoformat()}

@app.post("/orchestrator/master/speak")
async def orchestrator_master_speak(req: dict):
    """Make LOVE speak to the user via the orchestrator."""
    from core.master_orchestrator import get_orchestration_master
    om = get_orchestration_master()
    message = req.get("message", "")
    category = req.get("category", "THOUGHT")
    importance = req.get("importance", "normal")
    if not message:
        return {"error": "message required"}
    om.speak_to_user(message, category=category, importance=importance)
    return {"status": "sent", "message": message}


# Wave 33: Modern AI Routes (MCP, Reasoning, Browser)
try:
    from api.modern_routes import register_modern_routes
    register_modern_routes(app)
    print('[API] Wave 33 Modern AI routes loaded')
except Exception as e:
    print(f'[API] Modern routes error: {e}')
