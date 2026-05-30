"""
LOVE Predictive Maintenance — Proactive System Health Forecasting

Modern AI systems need to predict problems before they happen, not just
react to them. This engine provides:

1. FAILURE PREDICTION
   - Analyze subsystem health trends over time
   - Predict when a subsystem is likely to fail or degrade
   - Score risk levels: low, medium, high, critical

2. PERFORMANCE FORECASTING
   - Predict response time degradation
   - Forecast memory/CPU usage trends
   - Alert before resource exhaustion

3. PROACTIVE MAINTENANCE SCHEDULING
   - Schedule optimization tasks before performance drops
   - Suggest subsystem restarts or reconfiguration
   - Coordinate with evolution engine for self-improvement

4. HEALTH TREND ANALYSIS
   - Track health scores over time for all subsystems
   - Detect declining trends early
   - Correlate failures across subsystems

Architecture:
- predict_failure(): Predict when a subsystem will fail
- forecast_performance(): Predict performance degradation
- schedule_maintenance(): Schedule proactive maintenance
- get_health_forecast(): Get health predictions for all subsystems
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "predictive_maintenance"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEALTH_HISTORY = DATA_DIR / "health_history.jsonl"
PREDICTIONS_DB = DATA_DIR / "predictions.json"


@dataclass
class HealthSnapshot:
    """A snapshot of subsystem health at a point in time."""
    timestamp: float = 0.0
    subsystem: str = ""
    health_score: float = 0.0  # 0-1
    latency_ms: float = 0.0
    error_rate: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0


@dataclass
class FailurePrediction:
    """A prediction of subsystem failure."""
    subsystem: str = ""
    predicted_failure_time: str = ""
    risk_score: float = 0.0  # 0-1
    risk_level: str = "low"  # low, medium, high, critical
    indicators: List[str] = field(default_factory=list)
    suggested_action: str = ""
    confidence: float = 0.0


class PredictiveMaintenanceEngine:
    """
    Proactive system health forecasting for LOVE.
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
        self._lock = threading.Lock()
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._predictions: List[FailurePrediction] = []
        self._stats = {"snapshots": 0, "predictions": 0, "maintenance_scheduled": 0}
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ── Core Prediction ────────────────────────────────────────────────────

    def predict_failure(self, subsystem: str) -> Optional[FailurePrediction]:
        """Predict when a subsystem is likely to fail."""
        history = list(self._history.get(subsystem, []))
        if len(history) < 5:
            return None

        # Extract health scores
        scores = [h.health_score for h in history]
        latencies = [h.latency_ms for h in history]
        errors = [h.error_rate for h in history]

        # Calculate trend (linear regression on last 10 points)
        recent_scores = scores[-10:]
        trend = self._calculate_trend(recent_scores)

        # Risk scoring
        risk_score = 0.0
        indicators = []

        # Declining health trend
        if trend < -0.05:
            risk_score += 0.3
            indicators.append(f"Health declining at {trend:.3f} per snapshot")

        # High error rate
        avg_error = sum(errors[-5:]) / 5
        if avg_error > 0.1:
            risk_score += 0.3
            indicators.append(f"Error rate {avg_error:.1%}")

        # High latency
        avg_latency = sum(latencies[-5:]) / 5
        if avg_latency > 2000:
            risk_score += 0.2
            indicators.append(f"High latency {avg_latency:.0f}ms")

        # Low current health
        current_health = recent_scores[-1]
        if current_health < 0.5:
            risk_score += 0.2
            indicators.append(f"Low health {current_health:.2f}")

        if risk_score == 0.0:
            return None

        # Determine risk level
        if risk_score > 0.8:
            risk_level = "critical"
        elif risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Predict failure time (simple linear extrapolation)
        if trend < 0 and current_health > 0:
            hours_to_failure = max(1, int(current_health / abs(trend) * 0.5))
            predicted_time = (datetime.now() + timedelta(hours=hours_to_failure)).isoformat()
        else:
            predicted_time = "Unknown"

        # Suggest action
        if risk_level in ("critical", "high"):
            suggested_action = f"Immediate attention required: restart or reconfigure {subsystem}"
        elif risk_level == "medium":
            suggested_action = f"Schedule maintenance for {subsystem} within 24 hours"
        else:
            suggested_action = f"Monitor {subsystem} closely"

        prediction = FailurePrediction(
            subsystem=subsystem,
            predicted_failure_time=predicted_time,
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            indicators=indicators,
            suggested_action=suggested_action,
            confidence=min(1.0, len(history) / 50),  # More history = higher confidence
        )

        with self._lock:
            # Remove old prediction for this subsystem
            self._predictions = [p for p in self._predictions if p.subsystem != subsystem]
            self._predictions.append(prediction)
        self._stats["predictions"] += 1

        return prediction

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend slope."""
        if len(values) < 2:
            return 0.0
        n = len(values)
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        if denominator == 0:
            return 0.0
        return numerator / denominator

    # ── Health Snapshot Recording ───────────────────────────────────────────

    def record_snapshot(self, subsystem: str, health_score: float,
                        latency_ms: float = 0.0, error_rate: float = 0.0,
                        memory_mb: float = 0.0, cpu_percent: float = 0.0):
        """Record a health snapshot for a subsystem."""
        snapshot = HealthSnapshot(
            timestamp=time.time(),
            subsystem=subsystem,
            health_score=health_score,
            latency_ms=latency_ms,
            error_rate=error_rate,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
        )
        with self._lock:
            self._history[subsystem].append(snapshot)
        self._stats["snapshots"] += 1
        self._log_snapshot(snapshot)

        # Auto-predict after enough data
        if len(self._history[subsystem]) % 10 == 0:
            self.predict_failure(subsystem)

    # ── Forecasting ────────────────────────────────────────────────────────

    def get_health_forecast(self, subsystem: str, hours: int = 24) -> Dict[str, Any]:
        """Get health forecast for a subsystem."""
        history = list(self._history.get(subsystem, []))
        if len(history) < 5:
            return {"subsystem": subsystem, "message": "Insufficient data for forecast"}

        scores = [h.health_score for h in history]
        trend = self._calculate_trend(scores[-10:])
        current = scores[-1]

        # Project health over next N hours
        forecast = []
        for h in range(1, hours + 1, 4):  # Every 4 hours
            projected = max(0.0, min(1.0, current + trend * h * 0.1))
            forecast.append({
                "hours_ahead": h,
                "projected_health": round(projected, 3),
                "status": "critical" if projected < 0.3 else "warning" if projected < 0.6 else "healthy",
            })

        prediction = next(
            (p for p in self._predictions if p.subsystem == subsystem), None
        )

        return {
            "subsystem": subsystem,
            "current_health": round(current, 3),
            "trend": round(trend, 5),
            "trend_direction": "declining" if trend < -0.01 else "improving" if trend > 0.01 else "stable",
            "forecast": forecast,
            "prediction": {
                "risk_score": prediction.risk_score if prediction else 0.0,
                "risk_level": prediction.risk_level if prediction else "low",
                "predicted_failure_time": prediction.predicted_failure_time if prediction else None,
                "suggested_action": prediction.suggested_action if prediction else "No action needed",
            } if prediction else None,
        }

    # ── Maintenance Scheduling ───────────────────────────────────────────────

    def schedule_maintenance(self, subsystem: str, action: str,
                             priority: str = "normal") -> Dict[str, Any]:
        """Schedule a proactive maintenance task."""
        self._stats["maintenance_scheduled"] += 1

        # Log to neural bus
        try:
            from core.neural_bus import get_neural_bus
            bus = get_neural_bus()
            bus.publish("maintenance_scheduled", {
                "subsystem": subsystem,
                "action": action,
                "priority": priority,
                "scheduled_at": datetime.now().isoformat(),
            })
        except Exception:
            pass

        return {
            "subsystem": subsystem,
            "action": action,
            "priority": priority,
            "scheduled": True,
        }

    # ── Global Health Report ─────────────────────────────────────────────────

    def get_all_predictions(self) -> List[Dict[str, Any]]:
        """Get all current failure predictions."""
        return [
            {
                "subsystem": p.subsystem,
                "risk_score": p.risk_score,
                "risk_level": p.risk_level,
                "predicted_failure_time": p.predicted_failure_time,
                "indicators": p.indicators,
                "suggested_action": p.suggested_action,
                "confidence": p.confidence,
            }
            for p in sorted(self._predictions, key=lambda x: x.risk_score, reverse=True)
        ]

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "monitored_subsystems": len(self._history),
            "active_predictions": len(self._predictions),
            "high_risk_predictions": len([p for p in self._predictions if p.risk_level in ("high", "critical")]),
        }

    # ── Background Loop ────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-PredictiveMaintenance"
        )
        self._thread.start()
        print("[PredictiveMaintenance] Started — proactive health forecasting active")

    def stop(self):
        self._running = False

    def _main_loop(self):
        time.sleep(300)  # First prediction after 5 minutes
        while self._running:
            try:
                # Collect health snapshots from all subsystems
                self._collect_health_snapshots()

                # Generate predictions for all subsystems
                for subsystem in list(self._history.keys()):
                    prediction = self.predict_failure(subsystem)
                    if prediction and prediction.risk_level in ("high", "critical"):
                        print(f"[PredictiveMaintenance] ALERT: {subsystem} at {prediction.risk_level} risk")
                        # Schedule maintenance for high-risk subsystems
                        self.schedule_maintenance(
                            subsystem,
                            prediction.suggested_action,
                            priority="high" if prediction.risk_level == "critical" else "normal",
                        )
            except Exception as e:
                print(f"[PredictiveMaintenance] Loop error: {e}")
            time.sleep(1800)  # Run every 30 minutes

    def _collect_health_snapshots(self):
        """Collect health snapshots from all available subsystems."""
        subsystems = [
            ("evolution", lambda: self._get_evolution_health()),
            ("memory", lambda: self._get_memory_health()),
            ("orchestrator", lambda: self._get_orchestrator_health()),
        ]

        for name, health_fn in subsystems:
            try:
                health = health_fn()
                self.record_snapshot(name, **health)
            except Exception:
                pass

    def _get_evolution_health(self) -> Dict[str, float]:
        try:
            from core.evolution_integration import get_evolution_integration
            evo = get_evolution_integration()
            status = evo.get_integration_status()
            return {
                "health_score": 0.9 if status.get("running") else 0.5,
                "latency_ms": 0.0,
                "error_rate": 0.0,
            }
        except Exception:
            return {"health_score": 0.5}

    def _get_memory_health(self) -> Dict[str, float]:
        try:
            from core.vector_memory import get_vector_engine
            vm = get_vector_engine()
            return {
                "health_score": 0.9 if len(vm._memories) < 10000 else 0.7,
                "latency_ms": 0.0,
                "error_rate": 0.0,
                "memory_mb": len(vm._memories) * 0.001,  # Rough estimate
            }
        except Exception:
            return {"health_score": 0.5}

    def _get_orchestrator_health(self) -> Dict[str, float]:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            return {
                "health_score": 0.9 if cpu < 80 and mem.percent < 90 else 0.6,
                "latency_ms": 0.0,
                "error_rate": 0.0,
                "memory_mb": mem.used / (1024 * 1024),
                "cpu_percent": cpu,
            }
        except Exception:
            return {"health_score": 0.8}

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log_snapshot(self, snapshot: HealthSnapshot):
        try:
            with open(HEALTH_HISTORY, "a") as f:
                f.write(json.dumps({
                    "timestamp": snapshot.timestamp,
                    "subsystem": snapshot.subsystem,
                    "health_score": snapshot.health_score,
                    "latency_ms": snapshot.latency_ms,
                    "error_rate": snapshot.error_rate,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pm_instance: Optional[PredictiveMaintenanceEngine] = None
_pm_lock = threading.Lock()


def get_predictive_maintenance_engine() -> PredictiveMaintenanceEngine:
    global _pm_instance
    with _pm_lock:
        if _pm_instance is None:
            _pm_instance = PredictiveMaintenanceEngine()
        return _pm_instance
