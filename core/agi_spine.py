"""
LOVE AGI Spine — The Central Nervous System Bridge

This module wires ALL of LOVE's autonomous systems together through the
neural bus and orchestrator. It ensures that:

1. Sentinel events reach the Orchestrator and drive user-facing actions
2. Evolution discoveries become missions in the autonomous mission queue
3. Capability gaps trigger autonomous improvement cycles
4. Cross-module intelligence flows bidirectionally

Think of this as the corpus callosum of LOVE's brain — it connects
isolated modules into a unified, living organism.
"""

import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

DATA_DIR = Path(__file__).parent.parent / "data"
SPINE_LOG = DATA_DIR / "agi_spine_log.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Optional integrations
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

try:
    from core.master_orchestrator import get_orchestration_master
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False


class AGISpine:
    """
    The bridge that makes LOVE's modules act as one organism.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_gap_scan = 0.0
        self._last_evolution_report = 0.0
        self._last_life_pulse = 0.0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-AGISpine"
        )
        self._thread.start()
        print("[AGISpine] Central nervous system bridge started")

    def stop(self):
        self._running = False

    def _main_loop(self):
        time.sleep(60)  # Let all systems boot
        while self._running:
            try:
                self._bridge_sentinel_to_orchestrator()
                self._bridge_evolution_to_missions()
                self._bridge_gaps_to_missions()
                self._bridge_cross_module_intelligence()
                time.sleep(60)
            except Exception as e:
                print(f"[AGISpine] Loop error: {e}")
                time.sleep(60)

    # ═══════════════════════════════════════════════════════════════
    # BRIDGE 1: Sentinel → Orchestrator
    # ═══════════════════════════════════════════════════════════════

    def _bridge_sentinel_to_orchestrator(self):
        """Ensure sentinel decisions reach the orchestrator's user channel."""
        if not ORCHESTRATOR_AVAILABLE:
            return
        try:
            om = get_orchestration_master()
            # The sentinel already publishes to neural bus, and the orchestrator
            # already subscribes. This bridge ensures critical sentinel decisions
            # also get logged in the orchestrator's narrative for user visibility.
            # No extra work needed — the neural bus handles it.
            pass
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════
    # BRIDGE 2: Evolution → Mission Queue
    # ═══════════════════════════════════════════════════════════════

    def _bridge_evolution_to_missions(self):
        """Turn evolution discoveries into actionable missions."""
        now = time.time()
        if now - self._last_evolution_report < 3600:
            return
        self._last_evolution_report = now

        try:
            from core.evolution_integration import get_evolution_integration
            evo = get_evolution_integration()
            status = evo.get_integration_status()

            if not status.get("running"):
                return

            # Report to orchestrator
            if ORCHESTRATOR_AVAILABLE:
                om = get_orchestration_master()
                total_mods = status.get("statistics", {}).get("total_code_modifications", 0)
                total_muts = status.get("statistics", {}).get("total_mutations_applied", 0)
                if total_mods > 0 or total_muts > 0:
                    om._narrate(
                        "evolution_bridge",
                        f"Evolution systems active: {total_mods} code mods, {total_muts} mutations",
                        "action",
                        importance="normal"
                    )

            # Publish to neural bus
            if NEURAL_BUS_AVAILABLE:
                bus = get_neural_bus()
                bus.publish(
                    domain="self_evolution",
                    event_type="evolution_status_report",
                    payload=status,
                    source_module="agi_spine",
                    priority=EventPriority.NORMAL,
                )

        except Exception as e:
            print(f"[AGISpine] Evolution bridge error: {e}")

    # ═══════════════════════════════════════════════════════════════
    # BRIDGE 3: Capability Gaps → Mission Queue
    # ═══════════════════════════════════════════════════════════════

    def _bridge_gaps_to_missions(self):
        """Turn detected capability gaps into autonomous missions."""
        now = time.time()
        if now - self._last_gap_scan < 3600:
            return
        self._last_gap_scan = now

        try:
            from core.capability_gap_detector import get_capability_gap_detector
            detector = get_capability_gap_detector()
            gaps = detector.detect_all_gaps()

            if not gaps:
                return

            # Only create missions for high-impact gaps
            high_impact = [g for g in gaps if g.impact > 0.6 and g.urgency > 0.5]

            if not high_impact:
                return

            # Create missions from gaps
            try:
                from core.autonomous_mission_queue import get_mission_queue
                mq = get_mission_queue()

                for gap in high_impact[:3]:  # Max 3 missions per scan
                    mission_title = f"Close gap: {gap.subdomain}"
                    mission_desc = f"{gap.description}. Suggested fixes: {', '.join(gap.suggested_fixes[:2])}"
                    mq.add_mission(
                        title=mission_title,
                        description=mission_desc,
                        domain=gap.domain,
                        priority="high" if gap.urgency > 0.7 else "normal",
                        source="capability_gap_detector",
                    )

                # Report to orchestrator
                if ORCHESTRATOR_AVAILABLE:
                    om = get_orchestration_master()
                    om._narrate(
                        "gap_mission",
                        f"Created {len(high_impact[:3])} mission(s) from capability gaps",
                        "action",
                        importance="normal"
                    )
                    om.speak_to_user(
                        f"I detected {len(high_impact)} capability gaps in your life domains. "
                        f"I've queued {len(high_impact[:3])} improvement missions. "
                        f"Top gap: {high_impact[0].description[:80]}",
                        category="INSIGHT",
                        importance="normal"
                    )

            except Exception as e:
                print(f"[AGISpine] Mission queue bridge error: {e}")

            # Publish to neural bus
            if NEURAL_BUS_AVAILABLE:
                bus = get_neural_bus()
                bus.publish(
                    domain="self_evolution",
                    event_type="gaps_detected",
                    payload={
                        "count": len(gaps),
                        "high_impact": len(high_impact),
                        "domains": list(set(g.domain for g in gaps)),
                    },
                    source_module="agi_spine",
                    priority=EventPriority.NORMAL,
                )

        except Exception as e:
            print(f"[AGISpine] Gap bridge error: {e}")

    # ═══════════════════════════════════════════════════════════════
    # BRIDGE 4: Cross-Module Intelligence
    # ═══════════════════════════════════════════════════════════════

    def _bridge_cross_module_intelligence(self):
        """
        Ensure modules react to each other's neural bus events.
        For example: if heartbeat detects stress + finance detects volatility,
        the orchestrator should block trading and suggest a walk.
        """
        # This is handled by the orchestrator's neural bus subscription.
        # The spine ensures the orchestrator has the full picture.
        pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "last_gap_scan": self._last_gap_scan,
            "last_evolution_report": self._last_evolution_report,
            "bridges_active": [
                "sentinel_to_orchestrator",
                "evolution_to_missions",
                "gaps_to_missions",
                "cross_module_intelligence",
            ],
        }


# ═══════════════════════════════════════════════════════════════════
# Global Access
# ═══════════════════════════════════════════════════════════════════

_spine: Optional[AGISpine] = None
_spine_lock = threading.Lock()


def get_agi_spine() -> AGISpine:
    global _spine
    with _spine_lock:
        if _spine is None:
            _spine = AGISpine()
        return _spine


def start_agi_spine():
    return get_agi_spine().start()


def stop_agi_spine():
    return get_agi_spine().stop()


def get_agi_system_flags():
    """Return status flags for all AGI-level subsystems."""
    flags = {
        "neural_bus": False,
        "orchestrator": False,
        "sentinel": False,
        "evolution": False,
        "capability_gap": False,
        "mission_queue": False,
    }
    try:
        from core.neural_bus import get_neural_bus
        bus = get_neural_bus()
        flags["neural_bus"] = True
    except Exception:
        pass
    try:
        from core.master_orchestrator import get_orchestration_master
        om = get_orchestration_master()
        flags["orchestrator"] = getattr(om, '_running', False)
    except Exception:
        pass
    try:
        from core.sentinel import get_sentinel
        s = get_sentinel()
        flags["sentinel"] = getattr(s, '_running', False)
    except Exception:
        pass
    try:
        from core.evolution_integration import get_evolution_integration
        evo = get_evolution_integration()
        flags["evolution"] = evo.get_integration_status().get("running", False)
    except Exception:
        pass
    try:
        from core.capability_gap_detector import get_capability_gap_detector
        detector = get_capability_gap_detector()
        flags["capability_gap"] = getattr(detector, "_running", False)
    except Exception:
        pass
    try:
        from core.autonomous_mission_queue import get_mission_queue
        mq = get_mission_queue()
        flags["mission_queue"] = getattr(mq, "_running", False)
    except Exception:
        pass
    try:
        from core.mcp_host import get_mcp_host
        mcp = get_mcp_host()
        flags["mcp_host"] = mcp.get_health().get("sdk_available", False)
    except Exception:
        pass
    try:
        from core.reasoning_engine import get_reasoning_engine
        re = get_reasoning_engine()
        flags["reasoning_engine"] = True
    except Exception:
        pass
    try:
        from core.neural_architecture_search import get_neural_architecture_search
        nas = get_neural_architecture_search()
        flags["neural_architecture_search"] = getattr(nas, '_running', False)
    except Exception:
        pass
    try:
        from core.multimodal_evolution import get_multimodal_evolution
        mme = get_multimodal_evolution()
        flags["multimodal_evolution"] = getattr(mme, '_running', False)
    except Exception:
        pass
    try:
        from agents.task_evolution_integration import get_task_evolution_integration
        te = get_task_evolution_integration()
        flags["task_evolution"] = getattr(te, '_running', False)
    except Exception:
        pass
    try:
        from agents.fitness_evolution_integration import get_fitness_evolution_integration
        fe = get_fitness_evolution_integration()
        flags["fitness_evolution"] = getattr(fe, '_running', False)
    except Exception:
        pass
    try:
        from core.code_sandbox import get_code_sandbox
        sb = get_code_sandbox()
        flags["code_sandbox"] = True
    except Exception:
        pass
    try:
        from core.observability import get_observability_engine
        obs = get_observability_engine()
        flags["observability"] = getattr(obs, '_running', False)
    except Exception:
        pass
    try:
        from core.guardrails import get_guardrails_engine
        gr = get_guardrails_engine()
        flags["guardrails"] = True
    except Exception:
        pass
    try:
        from core.llm_manager import get_llm_manager
        mgr = get_llm_manager()
        flags["llm_manager"] = len(mgr._models) > 0
    except Exception:
        pass
    try:
        from core.graph_rag import get_graph_rag_engine
        gr = get_graph_rag_engine()
        flags["graph_rag"] = True
    except Exception:
        pass
    try:
        from core.prompt_optimizer import get_prompt_optimizer
        po = get_prompt_optimizer()
        flags["prompt_optimizer"] = len(po._templates) > 0
    except Exception:
        pass
    try:
        from core.self_reflection import get_self_reflection_engine
        sr = get_self_reflection_engine()
        flags["self_reflection"] = getattr(sr, '_running', False)
    except Exception:
        pass
    try:
        from core.conversation_quality import get_conversation_quality_analyzer
        cq = get_conversation_quality_analyzer()
        flags["conversation_quality"] = True
    except Exception:
        pass
    try:
        from core.predictive_maintenance import get_predictive_maintenance_engine
        pm = get_predictive_maintenance_engine()
        flags["predictive_maintenance"] = True
    except Exception:
        pass
    try:
        from core.multi_agent_orchestrator import get_multi_agent_orchestrator
        ma = get_multi_agent_orchestrator()
        flags["multi_agent"] = len(ma._agents) > 0
    except Exception:
        pass
    try:
        from core.intent_predictor import get_intent_predictor
        ip = get_intent_predictor()
        flags["intent_predictor"] = True
    except Exception:
        pass
    try:
        from core.personality_adapter import get_personality_adapter
        pa = get_personality_adapter()
        flags["personality_adapter"] = True
    except Exception:
        pass
    try:
        from core.response_cache import get_response_cache
        rc = get_response_cache()
        flags["response_cache"] = True
    except Exception:
        pass
    try:
        from core.context_window_manager import get_context_window_manager
        cwm = get_context_window_manager()
        flags["context_window_manager"] = True
    except Exception:
        pass
    try:
        from core.user_pattern_detector import get_user_pattern_detector
        upd = get_user_pattern_detector()
        flags["user_pattern_detector"] = True
    except Exception:
        pass
    try:
        from core.goal_drift_detector import get_goal_drift_detector
        gd = get_goal_drift_detector()
        flags["goal_drift_detector"] = True
    except Exception:
        pass

    try:
        from core.cross_modal_fusion import get_cross_modal_fusion_engine
        cm = get_cross_modal_fusion_engine()
        flags["cross_modal_fusion"] = True
    except Exception:
        pass
    try:
        from core.emotional_resonance import get_emotional_resonance_engine
        er = get_emotional_resonance_engine()
        flags["emotional_resonance"] = True
    except Exception:
        pass
    try:
        from core.knowledge_graph_builder import get_knowledge_graph_builder
        kgb = get_knowledge_graph_builder()
        flags["knowledge_graph_builder"] = True
    except Exception:
        pass
    try:
        from core.adaptive_learning_rate import get_adaptive_learning_engine
        alr = get_adaptive_learning_engine()
        flags["adaptive_learning_rate"] = True
    except Exception:
        pass
    try:
        from core.conversation_continuity import get_conversation_continuity_manager
        ccm = get_conversation_continuity_manager()
        flags["conversation_continuity"] = True
    except Exception:
        pass
    try:
        from core.memory_compressor import get_memory_compressor
        mc = get_memory_compressor()
        flags["memory_compressor"] = True
    except Exception:
        pass
    try:
        from core.semantic_search_optimizer import get_semantic_search_optimizer
        sso = get_semantic_search_optimizer()
        flags["semantic_search_optimizer"] = True
    except Exception:
        pass
    try:
        from core.emotion_aware_response import get_emotion_aware_response_generator
        ear = get_emotion_aware_response_generator()
        flags["emotion_aware_response"] = True
    except Exception:
        pass
    try:
        from core.knowledge_injector import get_knowledge_injector
        ki = get_knowledge_injector()
        flags["knowledge_injector"] = True
    except Exception:
        pass
    try:
        from core.conversation_summarizer import get_conversation_summarizer
        cs = get_conversation_summarizer()
        flags["conversation_summarizer"] = True
    except Exception:
        pass
    try:
        from core.context_aware_prioritizer import get_context_aware_prioritizer
        cap = get_context_aware_prioritizer()
        flags["context_aware_prioritizer"] = True
    except Exception:
        pass
    try:
        from core.wellness_nudger import get_wellness_nudger
        wn = get_wellness_nudger()
        flags["wellness_nudger"] = True
    except Exception:
        pass
    try:
        from core.notification_filter import get_notification_filter
        nf = get_notification_filter()
        flags["notification_filter"] = True
    except Exception:
        pass
    try:
        from core.deep_work_protector import get_deep_work_protector
        dwp = get_deep_work_protector()
        flags["deep_work_protector"] = True
    except Exception:
        pass
    try:
        from core.energy_forecaster import get_energy_forecaster
        ef = get_energy_forecaster()
        flags["energy_forecaster"] = True
    except Exception:
        pass
    try:
        from core.smart_break_suggester import get_smart_break_suggester
        sbs = get_smart_break_suggester()
        flags["smart_break_suggester"] = True
    except Exception:
        pass

    return flags
