"""
LOVE Observability — Proactive Tracing & Anomaly Detection (Modern AI Pattern)

When LOVE operates 15+ subsystems autonomously, things can go wrong silently.
Observability fixes this by:

1. DISTRIBUTED TRACING
   - Every operation gets a trace ID that flows through all subsystems
   - Spans measure latency of each component
   - Parent-child relationships show the full call chain

2. ANOMALY DETECTION
   - Baseline metrics established over time
   - Statistical outliers flagged automatically
   - Proactive alerts when a subsystem deviates from normal

3. HEALTH SCORING
   - Each subsystem gets a composite health score (0-100)
   - Trends show degradation before failure
   - Correlation between subsystems reveals root causes

4. PROACTIVE ALERTS
   - Not just passive metrics — LOVE notices and acts
   - High latency? Suggest a mutation to optimize
   - Memory leak? Trigger a health check
   - Error spike? Alert the user with context

Architecture:
- trace(): Decorator / context manager for tracing operations
- record_metric(): Store a metric point with tags
- detect_anomalies(): Scan for statistical outliers
- get_health_score(): Composite health for any subsystem
- alert(): Proactive notification with suggested action
"""

import json
import math
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "observability"
DATA_DIR.mkdir(parents=True, exist_ok=True)

METRICS_DB = DATA_DIR / "metrics.jsonl"
TRACES_DB = DATA_DIR / "traces.jsonl"
ALERTS_DB = DATA_DIR / "alerts.jsonl"
HEALTH_STATE = DATA_DIR / "health_state.json"


@dataclass
class TraceSpan:
    """A single span in a distributed trace."""
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    name: str = ""
    subsystem: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)
    status: str = "ok"  # ok, error, timeout

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000 if self.end_time else 0.0


@dataclass
class MetricPoint:
    """A single metric observation."""
    timestamp: float
    name: str
    value: float
    subsystem: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """A proactive alert with suggested action."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    severity: str = "info"  # info, warning, critical
    subsystem: str = ""
    title: str = ""
    description: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    suggested_action: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False


class ObservabilityEngine:
    """
    Proactive observability and tracing for LOVE.
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
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._traces: Dict[str, List[TraceSpan]] = {}
        self._active_spans: Dict[str, TraceSpan] = {}
        self._alerts: List[Alert] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_health_state()

    # ── Tracing ──────────────────────────────────────────────────────────────

    def start_trace(self, name: str, subsystem: str = "",
                    tags: Dict[str, str] = None) -> str:
        """Start a new distributed trace. Returns trace_id."""
        trace_id = uuid.uuid4().hex[:12]
        span = TraceSpan(
            trace_id=trace_id,
            span_id=trace_id,  # Root span uses trace_id as span_id
            name=name,
            subsystem=subsystem,
            start_time=time.time(),
            tags=tags or {},
        )
        with self._lock:
            self._active_spans[trace_id] = span
            self._traces[trace_id] = [span]
        return trace_id

    def start_span(self, trace_id: str, name: str, subsystem: str = "",
                   tags: Dict[str, str] = None) -> str:
        """Start a child span within a trace."""
        span_id = uuid.uuid4().hex[:8]
        parent_id = None
        with self._lock:
            if trace_id in self._active_spans:
                parent_id = self._active_spans[trace_id].span_id

        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            name=name,
            subsystem=subsystem,
            start_time=time.time(),
            tags=tags or {},
        )
        with self._lock:
            self._active_spans[span_id] = span
            if trace_id in self._traces:
                self._traces[trace_id].append(span)
        return span_id

    def end_span(self, span_id: str, status: str = "ok"):
        """End a span and record its duration."""
        with self._lock:
            if span_id in self._active_spans:
                span = self._active_spans[span_id]
                span.end_time = time.time()
                span.status = status
                del self._active_spans[span_id]
                self._log_trace(span)

    def end_trace(self, trace_id: str, status: str = "ok"):
        """End the root trace."""
        self.end_span(trace_id, status)
        with self._lock:
            if trace_id in self._traces:
                spans = self._traces[trace_id]
                total_ms = sum(s.duration_ms for s in spans if s.end_time)
                self.record_metric("trace_duration_ms", total_ms,
                                   subsystem=spans[0].subsystem if spans else "",
                                   tags={"trace_id": trace_id, "status": status})

    # ── Metrics ──────────────────────────────────────────────────────────────

    def record_metric(self, name: str, value: float, subsystem: str = "",
                      tags: Dict[str, str] = None):
        """Record a metric point."""
        point = MetricPoint(
            timestamp=time.time(),
            name=name,
            value=value,
            subsystem=subsystem,
            tags=tags or {},
        )
        key = f"{subsystem}:{name}"
        with self._lock:
            self._metrics[key].append(point)
        self._log_metric(point)

    def get_metric_stats(self, name: str, subsystem: str = "",
                         window_minutes: int = 60) -> Dict[str, Any]:
        """Get statistics for a metric over a time window."""
        key = f"{subsystem}:{name}"
        cutoff = time.time() - (window_minutes * 60)

        with self._lock:
            points = [p for p in self._metrics[key] if p.timestamp > cutoff]

        if not points:
            return {"count": 0}

        values = [p.value for p in points]
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std = math.sqrt(variance)

        return {
            "count": n,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "latest": round(values[-1], 4),
            "p95": round(sorted(values)[int(n * 0.95)] if n > 1 else values[0], 4),
            "p99": round(sorted(values)[int(n * 0.99)] if n > 1 else values[0], 4),
        }

    # ── Anomaly Detection ─────────────────────────────────────────────────────

    def detect_anomalies(self, subsystem: str = "",
                         window_minutes: int = 60) -> List[Alert]:
        """Scan metrics for statistical anomalies."""
        alerts = []
        cutoff = time.time() - (window_minutes * 60)

        with self._lock:
            keys = list(self._metrics.keys())

        for key in keys:
            if subsystem and not key.startswith(f"{subsystem}:"):
                continue

            stats = self.get_metric_stats(key.split(":")[1] if ":" in key else key,
                                          subsystem=key.split(":")[0] if ":" in key else "",
                                          window_minutes=window_minutes * 2)
            if stats["count"] < 10:
                continue

            current_stats = self.get_metric_stats(key.split(":")[1] if ":" in key else key,
                                                  subsystem=key.split(":")[0] if ":" in key else "",
                                                  window_minutes=window_minutes)
            if current_stats["count"] < 3:
                continue

            mean = stats["mean"]
            std = stats["std"]
            if std == 0:
                continue

            latest = current_stats["latest"]
            z_score = abs(latest - mean) / std

            if z_score > 3.0:
                severity = "critical" if z_score > 5 else "warning"
                alerts.append(Alert(
                    severity=severity,
                    subsystem=key.split(":")[0] if ":" in key else "",
                    title=f"Anomaly in {key}",
                    description=f"Value {latest} is {z_score:.1f} std from mean {mean:.2f}",
                    metric_name=key,
                    metric_value=latest,
                    threshold=mean + 3 * std,
                    suggested_action=self._suggest_action(key, latest, mean),
                ))

        with self._lock:
            self._alerts.extend(alerts)

        for alert in alerts:
            self._log_alert(alert)

        return alerts

    def _suggest_action(self, metric_key: str, value: float, mean: float) -> str:
        """Suggest an action based on the anomaly."""
        if "latency" in metric_key.lower() or "duration" in metric_key.lower():
            return "Consider triggering a performance optimization mutation"
        if "memory" in metric_key.lower():
            return "Check for memory leaks, consider restart"
        if "error" in metric_key.lower():
            return "Investigate error source, check logs"
        if "cpu" in metric_key.lower():
            return "Consider load balancing or model quantization"
        return "Monitor and investigate"

    # ── Health Scoring ────────────────────────────────────────────────────────

    def get_health_score(self, subsystem: str) -> Dict[str, Any]:
        """Get a composite health score for a subsystem."""
        latency_stats = self.get_metric_stats("trace_duration_ms", subsystem, 60)
        error_rate = self.get_metric_stats("error_rate", subsystem, 60)

        score = 100.0
        factors = []

        if latency_stats["count"] > 0:
            p95 = latency_stats.get("p95", 0)
            if p95 > 1000:  # > 1s
                deduction = min(30, (p95 - 1000) / 100)
                score -= deduction
                factors.append(f"High latency (p95={p95:.0f}ms): -{deduction:.0f}")

        if error_rate["count"] > 0:
            err = error_rate.get("latest", 0)
            if err > 0.01:
                deduction = min(40, err * 1000)
                score -= deduction
                factors.append(f"Error rate {err:.2%}: -{deduction:.0f}")

        return {
            "subsystem": subsystem,
            "score": round(max(0, score), 1),
            "factors": factors,
            "latency": latency_stats,
            "errors": error_rate,
        }

    def get_all_health_scores(self) -> List[Dict[str, Any]]:
        """Get health scores for all subsystems."""
        subsystems = set()
        with self._lock:
            for key in self._metrics:
                if ":" in key:
                    subsystems.add(key.split(":")[0])
        return [self.get_health_score(s) for s in subsystems]

    # ── Background Loop ───────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-Observability"
        )
        self._thread.start()
        print("[Observability] Started — proactive anomaly detection active")

    def stop(self):
        self._running = False

    def _main_loop(self):
        time.sleep(120)
        while self._running:
            try:
                alerts = self.detect_anomalies(window_minutes=30)
                if alerts:
                    for alert in alerts:
                        print(f"[Observability] {alert.severity.upper()}: {alert.title} — {alert.suggested_action}")
                        # Publish to neural bus for orchestrator to act on
                        try:
                            from core.neural_bus import get_neural_bus
                            bus = get_neural_bus()
                            bus.publish("observability_alert", {
                                "severity": alert.severity,
                                "subsystem": alert.subsystem,
                                "title": alert.title,
                                "suggested_action": alert.suggested_action,
                            })
                        except Exception:
                            pass
            except Exception as e:
                print(f"[Observability] Loop error: {e}")
            time.sleep(300)

    # ── Persistence ─────────────────────────────────────────────────────────

    def _log_metric(self, point: MetricPoint):
        try:
            with open(METRICS_DB, "a") as f:
                f.write(json.dumps({
                    "ts": point.timestamp,
                    "name": point.name,
                    "value": point.value,
                    "subsystem": point.subsystem,
                    "tags": point.tags,
                }) + "\n")
        except Exception:
            pass

    def _log_trace(self, span: TraceSpan):
        try:
            with open(TRACES_DB, "a") as f:
                f.write(json.dumps({
                    "trace_id": span.trace_id,
                    "span_id": span.span_id,
                    "parent_id": span.parent_id,
                    "name": span.name,
                    "subsystem": span.subsystem,
                    "duration_ms": span.duration_ms,
                    "status": span.status,
                    "tags": span.tags,
                }) + "\n")
        except Exception:
            pass

    def _log_alert(self, alert: Alert):
        try:
            with open(ALERTS_DB, "a") as f:
                f.write(json.dumps({
                    "id": alert.id,
                    "severity": alert.severity,
                    "subsystem": alert.subsystem,
                    "title": alert.title,
                    "description": alert.description,
                    "suggested_action": alert.suggested_action,
                    "created_at": alert.created_at,
                }) + "\n")
        except Exception:
            pass

    def _load_health_state(self):
        try:
            if HEALTH_STATE.exists():
                data = json.loads(HEALTH_STATE.read_text())
                # Could restore baselines here
        except Exception:
            pass


# ── Decorator ──────────────────────────────────────────────────────────────

_observability_instance: Optional[ObservabilityEngine] = None
_observability_lock = threading.Lock()


def get_observability_engine() -> ObservabilityEngine:
    global _observability_instance
    with _observability_lock:
        if _observability_instance is None:
            _observability_instance = ObservabilityEngine()
        return _observability_instance


def traced(subsystem: str = "", name: str = ""):
    """Decorator to trace a function."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            engine = get_observability_engine()
            trace_id = engine.start_trace(name or func.__name__, subsystem)
            try:
                result = func(*args, **kwargs)
                engine.end_trace(trace_id, "ok")
                return result
            except Exception as e:
                engine.end_trace(trace_id, "error")
                engine.record_metric("error_rate", 1.0, subsystem, {"error": str(e)})
                raise
        return wrapper
    return decorator
