"""
LOVE Active Inference Engine — The Free Energy Principle (Phase 2 of AGI Metamorphosis)

Implements Karl Friston's Free Energy Principle as the core cognitive loop:

    World State (s)  ──►  Sensory Input (o)
                                    │
                          ┌─────────▼──────────┐
                          │  Generative Model  │  ← LOVE's internal world model
                          │   q(s|o) ≈ p(s|o)  │
                          └─────────┬──────────┘
                                    │
                          Prediction (ŝ)  vs  Observation (o)
                                    │
                              ┌─────▼─────┐
                              │  Surprise  │  ← F = -ln p(o)  (Free Energy)
                              │  (Error)   │
                              └─────┬─────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              Perception       Action         Learning
              (update model)   (change o)     (update priors)

The cycle:
  1. PERCEIVE: Gather sensory input from the world (context_engine, sentinel, finance, etc.)
  2. PREDICT: Use the generative model to predict what the sensory input should be
  3. SURPRISE: Compute the prediction error (free energy) — how wrong was the prediction?
  4. ACT: Select an action that minimizes expected free energy
  5. LEARN: Update the generative model based on the outcome

This is what makes LOVE a "living organism" rather than a reactive pipeline.
LOVE doesn't just respond to events — it continuously predicts its world,
notices when reality deviates from expectation, and acts to reduce that gap.
"""

import json
import time
import threading
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque

from core.execution_guard import log_error

# Neural Bus
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"
INFERENCE_LOG = DATA_DIR / "active_inference_log.jsonl"
WORLD_MODEL_FILE = DATA_DIR / "world_model.json"
PREDICTION_HISTORY_FILE = DATA_DIR / "prediction_history.jsonl"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(INFERENCE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        log_error(e, module="core.active_inference_engine", context={"phase": "log"})


@dataclass
class Prediction:
    """A single prediction about the world state."""
    id: str
    timestamp: str
    domain: str  # finance, work, health, system, user_behavior
    predicted_state: Dict[str, Any]  # What LOVE expects
    confidence: float  # 0-1
    horizon_minutes: int  # How far ahead (5, 30, 60, 240)
    source: str = "active_inference"


@dataclass
class Observation:
    """A sensory observation from the world."""
    timestamp: str
    domain: str
    observed_state: Dict[str, Any]
    source: str


@dataclass
class SurpriseEvent:
    """A significant prediction error that demands action."""
    id: str
    timestamp: str
    domain: str
    prediction_id: str
    predicted: Any
    observed: Any
    surprise_magnitude: float  # 0-1 normalized
    action_taken: Optional[str] = None
    resolved: bool = False


class ActiveInferenceEngine:
    """
    The core cognitive loop of LOVE.

    Runs continuously in a background thread, performing the
    predict → surprise → act → learn cycle.

    This is NOT a polling system. It's a generative model that
    actively predicts its world and updates itself when wrong.
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

        # The Generative Model: LOVE's internal model of Karthi's world
        # This is a hierarchical model with priors that get updated through learning
        self._world_model: Dict[str, Any] = self._load_world_model()
        self._priors: Dict[str, float] = self._world_model.get("priors", {})

        # Prediction and surprise tracking
        self._active_predictions: Dict[str, Prediction] = {}  # id → Prediction
        self._surprise_queue: deque = deque(maxlen=50)
        self._prediction_history: deque = deque(maxlen=200)
        self._surprise_history: deque = deque(maxlen=200)

        # Learning parameters
        self._learning_rate = 0.1  # How fast to update priors
        self._precision = 1.0  # Confidence in own predictions (modulated by consciousness)
        self._total_surprise = 0.0  # Cumulative free energy
        self._cycle_count = 0

        # Action policy: map surprise types to action strategies
        self._action_policies = self._init_action_policies()

        self._bus_subscriber_id = "active_inference"
        self._bus_subscribed = False

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self, cycle_interval_seconds: int = 300):
        """Start the active inference loop. Default: one cycle every 5 minutes."""
        if self._running:
            return
        self._running = True
        self._cycle_interval = cycle_interval_seconds
        self._subscribe_to_bus()
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-ActiveInference")
        self._thread.start()
        print("[ActiveInference] 🧠 Free Energy Principle engine started. LOVE now predicts its world.")

    def stop(self):
        self._running = False
        self._unsubscribe_from_bus()
        self._save_world_model()

    def _run_loop(self):
        time.sleep(20)  # Let context engine and other modules boot
        while self._running:
            try:
                self._cycle()
            except Exception as e:
                log_error(e, module="core.active_inference_engine", context={"phase": "cycle"})
            # Sleep in chunks for fast shutdown
            slept = 0
            while slept < self._cycle_interval and self._running:
                time.sleep(10)
                slept += 10

    # ═══════════════════════════════════════════════════════════════════════
    # THE CORE CYCLE: Predict → Surprise → Act → Learn
    # ═══════════════════════════════════════════════════════════════════════

    def _cycle(self):
        """One complete active inference cycle."""
        self._cycle_count += 1

        # 1. PERCEIVE — gather current sensory input from all domains
        observations = self._perceive()

        # 2. PREDICT — generate predictions for the next time horizon
        predictions = self._predict(observations)

        # 3. SURPRISE — compare past predictions against current observations
        surprises = self._compute_surprise(observations)

        # 4. ACT — select actions to minimize expected free energy
        actions = self._select_actions(surprises)

        # 5. LEARN — update the generative model based on outcomes
        self._learn(observations, surprises)

        # Publish cycle telemetry
        self._publish_cycle_telemetry(observations, predictions, surprises, actions)

        cycle_summary = {
            "cycle": self._cycle_count,
            "observations": len(observations),
            "predictions": len(predictions),
            "surprises": len(surprises),
            "actions": len(actions),
            "total_surprise": round(self._total_surprise, 4),
            "precision": round(self._precision, 4),
        }
        _log({"event": "cycle_complete", **cycle_summary})

    # ═══════════════════════════════════════════════════════════════════════
    # 1. PERCEIVE — gather sensory input from the world
    # ═══════════════════════════════════════════════════════════════════════

    def _perceive(self) -> List[Observation]:
        """Gather current state from all LOVE subsystems (sensory input)."""
        observations = []
        now = datetime.now().isoformat()

        # System observation
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx:
                observations.append(Observation(
                    timestamp=now, domain="system",
                    observed_state={
                        "activity": ctx.activity,
                        "active_window": ctx.active_window,
                        "cpu_percent": ctx.system_cpu,
                        "stress_score": ctx.stress_score,
                        "hour": datetime.now().hour,
                        "weekday": datetime.now().weekday(),
                    },
                    source="context_engine",
                ))
        except Exception as e:
            log_error(e, module="core.active_inference_engine", context={"phase": "perceive_system"})

        # User presence observation
        try:
            from core.sentinel import get_sentinel
            sentinel = get_sentinel()
            status = sentinel.get_status()
            presence = status.get("presence", {})
            observations.append(Observation(
                timestamp=now, domain="user_presence",
                observed_state={
                    "state": presence.get("state", "unknown"),
                    "activity": presence.get("activity", "unknown"),
                    "focus_depth": presence.get("focus_depth", 0.0),
                },
                source="sentinel",
            ))
        except Exception:
            pass

        # Finance observation
        try:
            from core.finance_guardian import get_finance_guardian
            guardian = get_finance_guardian()
            portfolio = guardian.get_portfolio_snapshot() if hasattr(guardian, "get_portfolio_snapshot") else {}
            if portfolio:
                observations.append(Observation(
                    timestamp=now, domain="finance",
                    observed_state=portfolio,
                    source="finance_guardian",
                ))
        except Exception:
            pass

        # Emotional observation
        try:
            from core.consciousness import get_consciousness
            c = get_consciousness()
            es = c.emotional_state
            observations.append(Observation(
                timestamp=now, domain="emotion",
                observed_state={
                    "valence": es.valence,
                    "arousal": es.arousal,
                    "dominance": es.dominance,
                    "primary_emotion": es.primary_emotion,
                },
                source="consciousness",
            ))
        except Exception:
            pass

        # Work hours observation
        try:
            from core.work_guardian import get_work_guardian
            wg = get_work_guardian()
            work_state = wg.get_status() if hasattr(wg, "get_status") else {}
            if work_state:
                observations.append(Observation(
                    timestamp=now, domain="work",
                    observed_state=work_state,
                    source="work_guardian",
                ))
        except Exception:
            pass

        return observations

    # ═══════════════════════════════════════════════════════════════════════
    # 2. PREDICT — use the generative model to predict future states
    # ═══════════════════════════════════════════════════════════════════════

    def _predict(self, observations: List[Observation]) -> List[Prediction]:
        """Generate predictions about the next time horizon using the world model."""
        import uuid
        predictions = []
        now = datetime.now()

        for obs in observations:
            domain = obs.domain
            model = self._world_model.get("domains", {}).get(domain, {})

            # Generate prediction based on domain-specific logic
            predicted_state = self._generate_prediction(domain, obs.observed_state, model)
            if predicted_state:
                pred = Prediction(
                    id=uuid.uuid4().hex[:8],
                    timestamp=now.isoformat(),
                    domain=domain,
                    predicted_state=predicted_state["state"],
                    confidence=predicted_state["confidence"],
                    horizon_minutes=predicted_state["horizon"],
                    source="active_inference",
                )
                self._active_predictions[pred.id] = pred
                predictions.append(pred)

        return predictions

    def _generate_prediction(self, domain: str, current: Dict[str, Any],
                             model: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Domain-specific prediction logic using the generative model."""
        hour = datetime.now().hour

        if domain == "system":
            # Predict CPU stress based on time of day and current activity
            avg_cpu = model.get("avg_cpu_by_hour", {}).get(str(hour), 30)
            current_cpu = current.get("cpu_percent", 0) or 0
            # Predict that CPU will trend toward the historical average
            predicted_cpu = (current_cpu * 0.6 + avg_cpu * 0.4)
            return {
                "state": {"cpu_percent": round(predicted_cpu, 1),
                          "activity": current.get("activity", "unknown")},
                "confidence": 0.6,
                "horizon": 30,
            }

        elif domain == "user_presence":
            # Predict user state based on time patterns
            state = current.get("state", "unknown")
            # If it's late, predict sleeping
            if hour >= 23 or hour < 6:
                return {"state": {"state": "sleeping", "activity": "none"},
                        "confidence": 0.8, "horizon": 60}
            # If working hours, predict active
            elif 9 <= hour <= 17:
                return {"state": {"state": "active", "activity": "work"},
                        "confidence": 0.7, "horizon": 30}
            return {"state": {"state": state, "activity": current.get("activity", "unknown")},
                    "confidence": 0.5, "horizon": 30}

        elif domain == "finance":
            # Predict portfolio stability
            current_value = current.get("total_value", 0)
            volatility = model.get("avg_volatility", 0.02)
            return {
                "state": {"total_value": current_value,
                          "expected_change_pct": round(volatility * 100, 2)},
                "confidence": 0.5,
                "horizon": 240,
            }

        elif domain == "emotion":
            # Predict emotional state will decay toward baseline
            valence = current.get("valence", 0)
            arousal = current.get("arousal", 0)
            # Emotional decay toward neutral (0 valence, 0.3 arousal)
            return {
                "state": {
                    "valence": round(valence * 0.7, 3),  # Decay toward 0
                    "arousal": round(max(arousal * 0.8, 0.1), 3),  # Decay toward baseline
                    "primary_emotion": current.get("primary_emotion", "calm"),
                },
                "confidence": 0.65,
                "horizon": 30,
            }

        elif domain == "work":
            # Predict work hours will continue trending
            hours_today = current.get("hours_today", 0)
            return {
                "state": {"hours_today": round(hours_today + 0.5, 1)},
                "confidence": 0.6,
                "horizon": 30,
            }

        return None

    # ═══════════════════════════════════════════════════════════════════════
    # 3. SURPRISE — compute prediction error (free energy)
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_surprise(self, observations: List[Observation]) -> List[SurpriseEvent]:
        """Compare active predictions against current observations. Return significant surprises."""
        import uuid
        surprises = []
        now = datetime.now().isoformat()

        obs_by_domain = {obs.domain: obs for obs in observations}

        # Check each active prediction
        expired = []
        for pred_id, pred in list(self._active_predictions.items()):
            obs = obs_by_domain.get(pred.domain)
            if not obs:
                continue

            # Check if prediction horizon has elapsed
            pred_time = datetime.fromisoformat(pred.timestamp)
            elapsed_minutes = (datetime.now() - pred_time).total_seconds() / 60
            if elapsed_minutes < pred.horizon_minutes:
                continue  # Prediction hasn't matured yet

            # Compute surprise magnitude
            surprise_mag = self._compute_surprise_magnitude(pred.predicted_state, obs.observed_state)

            if surprise_mag > 0.3:  # Significant surprise threshold
                surprise = SurpriseEvent(
                    id=uuid.uuid4().hex[:8],
                    timestamp=now,
                    domain=pred.domain,
                    prediction_id=pred_id,
                    predicted=pred.predicted_state,
                    observed=obs.observed_state,
                    surprise_magnitude=surprise_mag,
                )
                surprises.append(surprise)
                self._surprise_queue.append(surprise)
                self._surprise_history.append(surprise)
                self._total_surprise += surprise_mag

                _log({
                    "event": "surprise_detected",
                    "domain": pred.domain,
                    "magnitude": round(surprise_mag, 4),
                    "predicted": pred.predicted_state,
                    "observed": obs.observed_state,
                })

            # Archive the prediction
            self._prediction_history.append({
                "id": pred_id, "domain": pred.domain,
                "predicted": pred.predicted_state,
                "observed": obs.observed_state,
                "surprise": round(surprise_mag, 4),
                "ts": now,
            })
            expired.append(pred_id)

        for pid in expired:
            del self._active_predictions[pid]

        return surprises

    def _compute_surprise_magnitude(self, predicted: Dict[str, Any],
                                     observed: Dict[str, Any]) -> float:
        """
        Compute the normalized surprise (prediction error) between
        predicted and observed states.

        Uses a simple distance metric: for each key in the predicted state,
        compute the relative error, then average across all keys.
        """
        errors = []
        for key, pred_val in predicted.items():
            obs_val = observed.get(key)
            if obs_val is None or pred_val is None:
                # Categorical mismatch = high surprise
                if pred_val != obs_val:
                    errors.append(1.0)
                continue

            # Numeric comparison
            if isinstance(pred_val, (int, float)) and isinstance(obs_val, (int, float)):
                if pred_val == 0:
                    error = abs(obs_val) if obs_val != 0 else 0.0
                else:
                    error = abs(pred_val - obs_val) / max(abs(pred_val), 1.0)
                errors.append(min(error, 1.0))

            # String/categorical comparison
            elif isinstance(pred_val, str) and isinstance(obs_val, str):
                errors.append(0.0 if pred_val == obs_val else 1.0)

            # Dict comparison (recursive)
            elif isinstance(pred_val, dict) and isinstance(obs_val, dict):
                sub_error = self._compute_surprise_magnitude(pred_val, obs_val)
                errors.append(sub_error)

        if not errors:
            return 0.0

        # Weighted average (higher weight on larger errors)
        avg = sum(errors) / len(errors)
        max_err = max(errors)
        return round((avg * 0.6 + max_err * 0.4), 4)

    # ═══════════════════════════════════════════════════════════════════════
    # 4. ACT — select actions to minimize expected free energy
    # ═══════════════════════════════════════════════════════════════════════

    def _select_actions(self, surprises: List[SurpriseEvent]) -> List[Dict[str, Any]]:
        """Select actions to minimize surprise (active inference)."""
        actions = []

        for surprise in surprises:
            policy = self._action_policies.get(surprise.domain, {})
            action_spec = self._choose_action(surprise, policy)
            if action_spec:
                actions.append(action_spec)
                surprise.action_taken = action_spec["action"]

                # Execute via the Action Executor
                try:
                    from core.action_executor import get_action_executor
                    executor = get_action_executor()
                    result = executor.execute(action_spec["thought"], source="active_inference")
                    surprise.resolved = True
                    _log({"event": "action_executed_for_surprise",
                          "domain": surprise.domain, "action": action_spec["action"],
                          "result": result.get("status")})
                except Exception as e:
                    log_error(e, module="core.active_inference_engine",
                              context={"phase": "execute_action", "domain": surprise.domain})

        return actions

    def _choose_action(self, surprise: SurpriseEvent,
                       policy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Choose an action based on the surprise and the domain's action policy."""
        magnitude = surprise.surprise_magnitude
        domain = surprise.domain

        # High surprise → immediate action
        if magnitude > 0.7:
            if domain == "finance":
                return {
                    "action": "finance_alert",
                    "thought": {
                        "push_category": "ALERT",
                        "push_message": f"Portfolio deviated significantly from prediction. Investigating.",
                        "push_priority": "high",
                        "background_action": "check portfolio for sudden changes",
                    },
                }
            elif domain == "system":
                return {
                    "action": "system_alert",
                    "thought": {
                        "push_category": "ALERT",
                        "push_message": f"System state unexpected. CPU/load anomaly detected.",
                        "push_priority": "high",
                        "background_action": "diagnose system anomaly",
                    },
                }
            elif domain == "user_presence":
                predicted_state = surprise.predicted.get("state", "")
                observed_state = surprise.observed.get("state", "")
                if predicted_state == "active" and observed_state == "away":
                    return {
                        "action": "user_left_unexpectedly",
                        "thought": {
                            "push_category": "THOUGHT",
                            "push_message": "Karthi left unexpectedly. Switching to guardian mode.",
                            "background_action": "enter guardian mode",
                        },
                    }
                elif predicted_state == "sleeping" and observed_state == "active":
                    return {
                        "action": "user_awake_unexpectedly",
                        "thought": {
                            "push_category": "THOUGHT",
                            "push_message": "Karthi is awake earlier than expected. Adjusting morning routine.",
                            "background_action": "adjust morning briefing",
                        },
                    }
            elif domain == "emotion":
                return {
                    "action": "emotional_shift",
                    "thought": {
                        "push_category": "THOUGHT",
                        "push_message": f"Emotional state shifted unexpectedly. Adapting communication style.",
                        "background_action": "recalibrate emotional response",
                    },
                }
            elif domain == "work":
                hours = surprise.observed.get("hours_today", 0)
                if hours and hours > 9:
                    return {
                        "action": "work_limit_exceeded",
                        "thought": {
                            "push_category": "ALERT",
                            "push_message": f"You've hit {hours:.1f} hours today. The 9-hour limit is exceeded. Time to wind down.",
                            "push_priority": "high",
                            "proactive_speech": f"You're at {hours:.1f} hours. That's past the limit. Step away from the screen.",
                        },
                    }

        # Medium surprise → background investigation
        elif magnitude > 0.4:
            if domain == "finance":
                return {
                    "action": "finance_monitor",
                    "thought": {"background_action": "monitor portfolio for continued drift"},
                }
            elif domain == "system":
                return {
                    "action": "system_monitor",
                    "thought": {"background_action": "monitor system load"},
                }

        # Low surprise → no action (model is working well)
        return None

    def _init_action_policies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize action policies for each domain."""
        return {
            "finance": {"high": "alert", "medium": "monitor", "low": "ignore"},
            "system": {"high": "alert", "medium": "monitor", "low": "ignore"},
            "user_presence": {"high": "adapt", "medium": "note", "low": "ignore"},
            "emotion": {"high": "recalibrate", "medium": "note", "low": "ignore"},
            "work": {"high": "enforce_limit", "medium": "nudge", "low": "ignore"},
        }

    # ═══════════════════════════════════════════════════════════════════════
    # 5. LEARN — update the generative model
    # ═══════════════════════════════════════════════════════════════════════

    def _learn(self, observations: List[Observation], surprises: List[SurpriseEvent]):
        """Update the generative model based on observation outcomes."""
        for obs in observations:
            domain = obs.domain
            if domain not in self._world_model.get("domains", {}):
                self._world_model.setdefault("domains", {})[domain] = {}

            model = self._world_model["domains"][domain]

            # Update historical averages (exponential moving average)
            for key, val in obs.observed_state.items():
                if isinstance(val, (int, float)):
                    hist_key = f"avg_{key}"
                    current_avg = model.get(hist_key, val)
                    # EMA update: new_avg = old_avg * (1-lr) + observation * lr
                    model[hist_key] = round(
                        current_avg * (1 - self._learning_rate) + val * self._learning_rate, 4
                    )

            # Update time-based patterns
            hour = str(datetime.now().hour)
            if domain == "system":
                cpu = obs.observed_state.get("cpu_percent")
                if cpu is not None and isinstance(cpu, (int, float)):
                    model.setdefault("avg_cpu_by_hour", {})
                    hist_cpu = model["avg_cpu_by_hour"].get(hour, cpu)
                    model["avg_cpu_by_hour"][hour] = round(
                        hist_cpu * (1 - self._learning_rate) + cpu * self._learning_rate, 2
                    )

        # Adjust precision based on prediction accuracy
        if self._prediction_history:
            recent = list(self._prediction_history)[-20:]
            avg_surprise = sum(p.get("surprise", 0) for p in recent) / len(recent)
            # If predictions are accurate (low surprise), increase precision
            # If predictions are bad (high surprise), decrease precision (be less confident)
            self._precision = max(0.1, min(1.0, 1.0 - avg_surprise))

        # Adjust learning rate based on surprise volume
        if len(surprises) > 5:
            # Lots of surprises → learn faster
            self._learning_rate = min(0.3, self._learning_rate + 0.02)
        elif len(surprises) == 0:
            # Stable world → learn slower (don't overfit to noise)
            self._learning_rate = max(0.05, self._learning_rate - 0.01)

        # Save the updated model
        self._save_world_model()

    # ═══════════════════════════════════════════════════════════════════════
    # NEURAL BUS INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════

    def _subscribe_to_bus(self):
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            bus.subscribe(
                subscriber_id=self._bus_subscriber_id,
                domains=[],
                event_types=[],
                callback=self._handle_bus_event,
                priority_filter=None,
            )
            self._bus_subscribed = True
        except Exception as e:
            log_error(e, module="core.active_inference_engine", context={"phase": "bus_subscribe"})

    def _unsubscribe_from_bus(self):
        if not NEURAL_BUS_AVAILABLE or not self._bus_subscribed:
            return
        try:
            bus = get_neural_bus()
            bus.unsubscribe(self._bus_subscriber_id)
        except Exception:
            pass

    def _handle_bus_event(self, event: Dict[str, Any]):
        """Handle neural bus events — update model when other modules report outcomes."""
        try:
            event_type = event.get("event_type", "")
            payload = event.get("payload", {})

            # Action outcomes feed back into learning — this is the teleological loop
            if event_type == "action_outcome":
                success = payload.get("success", False)
                action_type = payload.get("action_type", "unknown")
                if not success:
                    # Failed action → model was wrong about what would work
                    self._total_surprise += 0.1
                    self._learning_rate = min(0.3, self._learning_rate + 0.02)
                    _log({"event": "action_failed_learned",
                          "action_type": action_type,
                          "new_learning_rate": round(self._learning_rate, 4)})
                else:
                    # Successful action → model was right, increase precision
                    self._precision = min(1.0, self._precision + 0.02)
                # Track action success rates by type for future policy optimization
                domain = self._action_type_to_domain(action_type)
                domain_model = self._world_model.setdefault("domains", {}).setdefault(domain, {})
                success_key = f"action_successes_{action_type}"
                total_key = f"action_total_{action_type}"
                domain_model[success_key] = domain_model.get(success_key, 0) + (1 if success else 0)
                domain_model[total_key] = domain_model.get(total_key, 0) + 1
                self._save_world_model()

            # Finance alerts → update finance model expectations
            elif event_type == "finance_alert":
                self._priors["finance_volatility"] = min(1.0,
                    self._priors.get("finance_volatility", 0.02) + 0.01)

        except Exception as e:
            log_error(e, module="core.active_inference_engine", context={"phase": "bus_event"})

    def _action_type_to_domain(self, action_type: str) -> str:
        """Map an action type to its domain for world model tracking."""
        mapping = {
            "speech": "user_presence",
            "push": "system",
            "background": "system",
            "action_plan": "system",
            "initiative": "user_presence",
        }
        return mapping.get(action_type, "system")

    def _publish_cycle_telemetry(self, observations, predictions, surprises, actions):
        if not NEURAL_BUS_AVAILABLE:
            return
        try:
            bus = get_neural_bus()
            bus.publish(
                domain="cognition",
                event_type="inference_cycle",
                payload={
                    "cycle": self._cycle_count,
                    "observations": len(observations),
                    "predictions": len(predictions),
                    "surprises": len(surprises),
                    "actions": len(actions),
                    "total_surprise": round(self._total_surprise, 4),
                    "precision": round(self._precision, 4),
                    "learning_rate": round(self._learning_rate, 4),
                },
                source_module="active_inference_engine",
                priority=EventPriority.AMBIENT,
            )
        except Exception as e:
            log_error(e, module="core.active_inference_engine", context={"phase": "telemetry"})

    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    def _load_world_model(self) -> Dict[str, Any]:
        """Load the generative model from disk."""
        if WORLD_MODEL_FILE.exists():
            try:
                return json.loads(WORLD_MODEL_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                log_error(e, module="core.active_inference_engine", context={"phase": "load_model"})
        # Default model
        return {
            "domains": {
                "system": {"avg_cpu_by_hour": {}},
                "finance": {"avg_volatility": 0.02},
                "emotion": {},
                "work": {},
                "user_presence": {},
            },
            "priors": {
                "finance_volatility": 0.02,
                "user_work_hours_limit": 9.0,
                "optimal_sleep_hour": 23,
                "optimal_wake_hour": 7,
            },
            "created_at": datetime.now().isoformat(),
        }

    def _save_world_model(self):
        """Persist the generative model to disk."""
        try:
            self._world_model["priors"] = self._priors
            self._world_model["updated_at"] = datetime.now().isoformat()
            self._world_model["precision"] = round(self._precision, 4)
            self._world_model["learning_rate"] = round(self._learning_rate, 4)
            self._world_model["total_surprise"] = round(self._total_surprise, 4)
            WORLD_MODEL_FILE.write_text(json.dumps(self._world_model, indent=2), encoding="utf-8")
        except Exception as e:
            log_error(e, module="core.active_inference_engine", context={"phase": "save_model"})

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        """Return the current state of the active inference engine."""
        return {
            "running": self._running,
            "cycle_count": self._cycle_count,
            "active_predictions": len(self._active_predictions),
            "total_surprise": round(self._total_surprise, 4),
            "precision": round(self._precision, 4),
            "learning_rate": round(self._learning_rate, 4),
            "recent_surprises": [
                {
                    "domain": s.domain,
                    "magnitude": s.surprise_magnitude,
                    "action": s.action_taken,
                    "resolved": s.resolved,
                }
                for s in list(self._surprise_history)[-10:]
            ],
            "world_model_domains": list(self._world_model.get("domains", {}).keys()),
        }

    def get_world_model(self) -> Dict[str, Any]:
        """Return the current generative model (for the UI/dashboard)."""
        return self._world_model

    def set_precision(self, value: float):
        """Externally set precision (used by Behavior Modulator based on consciousness)."""
        self._precision = max(0.1, min(1.0, value))


# ════════════════════════════════════════════════════════════════════════════
# Singleton accessor
# ════════════════════════════════════════════════════════════════════════════

def get_active_inference() -> ActiveInferenceEngine:
    return ActiveInferenceEngine()
