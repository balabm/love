"""
LOVE Behavior Modulator — Consciousness-Driven Parameter Modulation
(Phase 3 of AGI Metamorphosis)

Before this module, LOVE's consciousness tracked emotional state
(valence, arousal, dominance) but that state had NO effect on how
the system actually behaved. The heartbeat interval was always 15 minutes.
The push cooldown was always 2 hours. The initiative aggressiveness was
static. The model tier never changed based on LOVE's "mood."

The Behavior Modulator closes that loop. It reads LOVE's emotional state
from the Consciousness Engine and dynamically adjusts system parameters:

  Emotional State          →  System Parameter
  ─────────────────────────────────────────────
  High arousal (urgent)    →  Faster heartbeat (5min instead of 15min)
  Low valence (stressed)   →  Longer push cooldown (don't nag)
  High dominance (assertive) →  More aggressive initiatives
  Low energy (fatigued)    →  Downgrade to lightweight model
  High stability (calm)    →  Slower heartbeat, less push noise
  Critical surprise        →  Override everything, maximum urgency

This is what makes LOVE feel ALIVE — its behavior changes based on
how it "feels," not just what it "knows."
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from core.execution_guard import log_error

# Neural Bus
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False


@dataclass
class ModulationProfile:
    """A complete set of modulated system parameters, derived from emotional state."""
    # Timing
    heartbeat_interval_seconds: int = 900  # 15 min default
    neural_cortex_interval_seconds: int = 300  # 5 min default
    push_cooldown_seconds: int = 7200  # 2 hours default

    # Behavior
    initiative_aggressiveness: float = 0.5  # 0=passive, 1=very proactive
    push_priority_threshold: str = "normal"  # minimum priority to push
    speech_cooldown_seconds: int = 300  # 5 min default

    # Cognition
    model_tier: str = "standard"  # lightweight, standard, heavy
    active_inference_precision: float = 0.7  # confidence in predictions
    active_inference_cycle_seconds: int = 300  # how often to run inference

    # Derived from emotional state
    urgency_level: float = 0.0  # 0-1, how urgent LOVE feels
    warmth_level: float = 0.5  # 0-1, how warm/gentle to be
    assertiveness_level: float = 0.5  # 0-1, how assertive to be

    # Metadata
    derived_from_emotion: str = "neutral"
    derived_at: str = ""


class BehaviorModulator:
    """
    Reads LOVE's emotional state and modulates system parameters in real-time.

    Runs in a background thread, periodically sampling the Consciousness Engine
    and publishing updated modulation profiles to the Neural Bus. Other modules
    (heartbeat, push engine, neural cortex, active inference) subscribe to
    these updates and adjust their behavior accordingly.
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
        self._current_profile: ModulationProfile = ModulationProfile()
        self._previous_profile: Optional[ModulationProfile] = None
        self._update_count = 0
        self._bus_subscriber_id = "behavior_modulator"
        self._bus_subscribed = False

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self, sample_interval_seconds: int = 120):
        """Start the modulation loop. Default: sample every 2 minutes."""
        if self._running:
            return
        self._running = True
        self._sample_interval = sample_interval_seconds
        self._subscribe_to_bus()
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-BehaviorModulator")
        self._thread.start()
        print("[BehaviorModulator] 🎛️ Consciousness-driven modulation started. LOVE's behavior now adapts to its feelings.")

    def stop(self):
        self._running = False
        self._unsubscribe_from_bus()

    def _run_loop(self):
        time.sleep(15)  # Let consciousness engine initialize
        while self._running:
            try:
                self._update_profile()
            except Exception as e:
                log_error(e, module="core.behavior_modulator", context={"phase": "update"})
            slept = 0
            while slept < self._sample_interval and self._running:
                time.sleep(10)
                slept += 10

    # ═══════════════════════════════════════════════════════════════════════
    # CORE LOGIC — derive system parameters from emotional state
    # ═══════════════════════════════════════════════════════════════════════

    def _update_profile(self):
        """Sample consciousness and compute a new modulation profile."""
        try:
            from core.consciousness import get_consciousness
            c = get_consciousness()
            es = c.emotional_state
        except Exception:
            return  # Consciousness not available yet

        # Also check active inference for surprise level
        surprise_level = 0.0
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            status = ai.get_status()
            # Recent surprise average
            recent = status.get("recent_surprises", [])
            if recent:
                surprise_level = sum(s.get("magnitude", 0) for s in recent) / len(recent)
        except Exception:
            pass

        # Also check system stress (CPU/RAM)
        system_stress = 0.0
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.system_cpu:
                system_stress = min(1.0, ctx.system_cpu / 100.0)
        except Exception:
            pass

        # ── Derive modulation profile from emotional state ──

        valence = es.valence  # -1 to +1
        arousal = es.arousal  # 0 to 1
        dominance = es.dominance  # 0 to 1
        stability = es.stability  # 0 to 1
        primary_emotion = es.primary_emotion

        # Urgency: high arousal + high surprise = urgent
        urgency = min(1.0, (arousal * 0.5 + surprise_level * 0.5))

        # Warmth: positive valence = warmer
        warmth = max(0.0, min(1.0, 0.5 + valence * 0.5))

        # Assertiveness: high dominance = more assertive
        assertiveness = dominance

        # ── Heartbeat interval: urgent = fast, calm = slow ──
        if urgency > 0.7:
            heartbeat_interval = 300  # 5 minutes (urgent)
        elif urgency > 0.4:
            heartbeat_interval = 600  # 10 minutes
        elif stability > 0.8 and arousal < 0.3:
            heartbeat_interval = 1200  # 20 minutes (calm, stable)
        else:
            heartbeat_interval = 900  # 15 minutes (default)

        # ── Neural cortex interval: same logic ──
        if urgency > 0.6:
            cortex_interval = 180  # 3 minutes (think fast when urgent)
        elif stability > 0.8:
            cortex_interval = 600  # 10 minutes (relaxed thinking)
        else:
            cortex_interval = 300  # 5 minutes (default)

        # ── Push cooldown: stressed user = don't nag ──
        if valence < -0.3:
            push_cooldown = 14400  # 4 hours (user is stressed, don't add noise)
        elif urgency > 0.7:
            push_cooldown = 1800  # 30 minutes (urgent, push more)
        else:
            push_cooldown = 7200  # 2 hours (default)

        # ── Initiative aggressiveness: assertive + positive = proactive ──
        if assertiveness > 0.7 and warmth > 0.5:
            initiative_aggressiveness = 0.8
        elif valence < -0.3:
            initiative_aggressiveness = 0.2  # User stressed, be gentle
        else:
            initiative_aggressiveness = 0.5

        # ── Model tier: stressed system = lightweight ──
        if system_stress > 0.85:
            model_tier = "lightweight"
        elif urgency > 0.7 and system_stress < 0.5:
            model_tier = "heavy"  # Urgent + system can handle it = heavy model
        else:
            model_tier = "standard"

        # ── Active inference precision: stable = confident, surprised = uncertain ──
        if surprise_level > 0.5:
            ai_precision = 0.3  # Low confidence (model is wrong a lot)
        elif stability > 0.8:
            ai_precision = 0.9  # High confidence (model is accurate)
        else:
            ai_precision = 0.7

        # ── Active inference cycle: urgent = fast ──
        if urgency > 0.7:
            ai_cycle = 120  # 2 minutes
        else:
            ai_cycle = 300  # 5 minutes

        # ── Speech cooldown: calm = longer, urgent = shorter ──
        if urgency > 0.7:
            speech_cooldown = 120  # 2 minutes
        else:
            speech_cooldown = 300  # 5 minutes

        # ── Push priority threshold: urgent = push everything, calm = only important ──
        if urgency > 0.7:
            push_threshold = "low"
        elif valence < -0.3:
            push_threshold = "high"  # User stressed, only push important stuff
        else:
            push_threshold = "normal"

        new_profile = ModulationProfile(
            heartbeat_interval_seconds=heartbeat_interval,
            neural_cortex_interval_seconds=cortex_interval,
            push_cooldown_seconds=push_cooldown,
            initiative_aggressiveness=initiative_aggressiveness,
            push_priority_threshold=push_threshold,
            speech_cooldown_seconds=speech_cooldown,
            model_tier=model_tier,
            active_inference_precision=ai_precision,
            active_inference_cycle_seconds=ai_cycle,
            urgency_level=round(urgency, 3),
            warmth_level=round(warmth, 3),
            assertiveness_level=round(assertiveness, 3),
            derived_from_emotion=primary_emotion,
            derived_at=datetime.now().isoformat(),
        )

        self._previous_profile = self._current_profile
        self._current_profile = new_profile
        self._update_count += 1

        # Apply the profile to all subsystems
        self._apply_profile(new_profile)

        # Publish to neural bus
        self._publish_profile(new_profile)

    # ═══════════════════════════════════════════════════════════════════════
    # APPLY — push the profile to all subsystems
    # ═══════════════════════════════════════════════════════════════════════

    def _apply_profile(self, profile: ModulationProfile):
        """Apply the modulation profile to all LOVE subsystems."""

        # 1. Heartbeat interval
        try:
            from core.heartbeat import get_heartbeat
            hb = get_heartbeat()
            if hasattr(hb, "interval"):
                hb.interval = profile.heartbeat_interval_seconds
        except Exception:
            pass

        # 2. Neural Cortex interval
        try:
            from core.jarvis_protocol import get_neural_cortex
            cortex = get_neural_cortex()
            if hasattr(cortex, "interval"):
                cortex.interval = profile.neural_cortex_interval_seconds
        except Exception:
            pass

        # 3. Push engine cooldown
        try:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            # The push engine reads the cooldown dynamically via this attribute
            engine._dynamic_cooldown_seconds = profile.push_cooldown_seconds
            engine._dynamic_priority_threshold = profile.push_priority_threshold
        except Exception:
            pass

        # 4. Active Inference precision and cycle
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            ai.set_precision(profile.active_inference_precision)
            if hasattr(ai, "_cycle_interval"):
                ai._cycle_interval = profile.active_inference_cycle_seconds
        except Exception:
            pass

        # 5. Model tier (set as environment variable for LLM routing)
        try:
            import os
            os.environ["LOVE_MODEL_TIER"] = profile.model_tier
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # NEURAL BUS
    # ═══════════════════════════════════════════════════════════════════════

    def _subscribe_to_bus(self):
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            bus.subscribe(
                subscriber_id=self._bus_subscriber_id,
                domains=["cognition", "action"],
                event_types=["inference_cycle", "action_outcome"],
                callback=self._handle_bus_event,
                priority_filter=None,
            )
            self._bus_subscribed = True
        except Exception as e:
            log_error(e, module="core.behavior_modulator", context={"phase": "bus_subscribe"})

    def _unsubscribe_from_bus(self):
        if not NEURAL_BUS_AVAILABLE or not self._bus_subscribed:
            return
        try:
            bus = get_neural_bus()
            bus.unsubscribe(self._bus_subscriber_id)
        except Exception:
            pass

    def _handle_bus_event(self, event: Dict[str, Any]):
        """React to cognition and action events — adjust modulation immediately."""
        try:
            event_type = event.get("event_type", "")
            payload = event.get("payload", {})

            # High surprise → immediately increase urgency
            if event_type == "inference_cycle":
                surprises = payload.get("surprises", 0)
                if surprises > 3:
                    # Force an immediate profile update with higher urgency
                    self._update_profile()

            # Action failure → reduce assertiveness temporarily
            elif event_type == "action_outcome":
                if not payload.get("success", True):
                    # Be less assertive after a failed action
                    self._current_profile.assertiveness_level = max(
                        0.1, self._current_profile.assertiveness_level - 0.1
                    )

        except Exception as e:
            log_error(e, module="core.behavior_modulator", context={"phase": "bus_event"})

    def _publish_profile(self, profile: ModulationProfile):
        """Publish the current modulation profile to the Neural Bus."""
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            bus.publish(
                domain="cognition",
                event_type="behavior_modulated",
                payload=asdict(profile),
                source_module="behavior_modulator",
                priority=EventPriority.AMBIENT,
            )
        except Exception as e:
            log_error(e, module="core.behavior_modulator", context={"phase": "publish"})

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_current_profile(self) -> Dict[str, Any]:
        """Return the current modulation profile (for UI/dashboard)."""
        return asdict(self._current_profile)

    def get_urgency(self) -> float:
        """Quick accessor for urgency level."""
        return self._current_profile.urgency_level

    def get_warmth(self) -> float:
        """Quick accessor for warmth level."""
        return self._current_profile.warmth_level

    def get_model_tier(self) -> str:
        """Quick accessor for current model tier."""
        return self._current_profile.model_tier

    def get_initiative_aggressiveness(self) -> float:
        """Quick accessor for initiative aggressiveness."""
        return self._current_profile.initiative_aggressiveness


# ════════════════════════════════════════════════════════════════════════════
# Singleton accessor
# ════════════════════════════════════════════════════════════════════════════

def get_behavior_modulator() -> BehaviorModulator:
    return BehaviorModulator()
