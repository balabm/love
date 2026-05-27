"""
LOVE Evolution Engine — Autonomous Self-Improvement Through Experimentation

Implements: measure -> hypothesize -> experiment -> validate -> integrate
The genome is LOVE's behavioral DNA — active prompt modifications that shape
how it thinks, speaks, and acts. Mutations that prove beneficial survive;
the rest get reverted. Natural selection for an AI companion.
"""
import json, math, time, uuid, threading, statistics, traceback
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GENOME_FILE = DATA_DIR / "genome.json"
HISTORY_FILE = DATA_DIR / "history.jsonl"
METRICS_FILE = DATA_DIR / "metrics.json"
EXPERIMENTS_FILE = DATA_DIR / "experiments.json"

# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class InteractionRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    interaction_type: str = "conversation"
    user_satisfaction: Optional[float] = None
    response_quality: float = 0.5
    latency_ms: float = 0.0
    tokens_used: int = 0
    was_proactive: bool = False
    context_relevance: float = 0.5
    error_occurred: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceReport:
    window_start: str = ""
    window_end: str = ""
    total_interactions: int = 0
    avg_quality: float = 0.0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    proactive_ratio: float = 0.0
    satisfaction_avg: Optional[float] = None
    quality_trend: float = 0.0
    strongest_area: str = ""
    weakest_area: str = ""
    breakdown_by_type: Dict[str, Dict] = field(default_factory=dict)

@dataclass
class Hypothesis:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    claim: str = ""
    rationale: str = ""
    predicted_effect: str = ""
    target_metric: str = "response_quality"
    predicted_delta: float = 0.0
    confidence: float = 0.5
    status: str = "proposed"  # proposed, testing, confirmed, rejected
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tested_at: Optional[str] = None
    evidence: List[str] = field(default_factory=list)

@dataclass
class Experiment:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    hypothesis_id: str = ""
    name: str = ""
    description: str = ""
    mutation_type: str = ""
    mutation_params: Dict[str, Any] = field(default_factory=dict)
    control_metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "designed"  # designed, running, completed, abandoned
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_hours: float = 24.0
    min_samples: int = 10

@dataclass
class ExperimentResult:
    experiment_id: str = ""
    hypothesis_id: str = ""
    control_mean: float = 0.0
    treatment_mean: float = 0.0
    delta: float = 0.0
    sample_size: int = 0
    p_value: float = 1.0
    is_significant: bool = False
    conclusion: str = ""
    should_integrate: bool = False
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Mutation:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    mutation_type: str = ""       # prompt_injection, tone_shift, strategy_change
    description: str = ""
    prompt_modification: str = "" # the actual text injected into prompts
    injection_point: str = "system_suffix"  # system_prefix, system_suffix, context_frame
    experiment_id: Optional[str] = None
    active: bool = True
    applied_at: str = field(default_factory=lambda: datetime.now().isoformat())
    reverted_at: Optional[str] = None
    fitness: float = 0.5
    interactions_since_applied: int = 0
    quality_before: float = 0.0
    quality_after: float = 0.0
    generation: int = 1

@dataclass
class EvolutionEvent:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    event_type: str = ""
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    generation: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class CapabilityGap:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    area: str = ""
    description: str = ""
    severity: float = 0.5
    evidence: List[str] = field(default_factory=list)
    suggested_fix: str = ""
    priority: float = 0.5
    identified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    addressed: bool = False

# ── Helper Functions ─────────────────────────────────────────────────────────

def _try_convert_scalar(s: Any):
    """Try to convert a scalar string to int/float/bool. Returns original on failure."""
    from fractions import Fraction
    if not isinstance(s, str):
        return s
    s_strip = s.strip()
    # boolean
    if s_strip.lower() in ('true', 'false', '1', '0', 'yes', 'no'):
        return s_strip.lower() in ('true', '1', 'yes')
    # fraction like '1/2'
    if '/' in s_strip:
        try:
            return float(Fraction(s_strip))
        except Exception:
            pass
    # try int then float
    try:
        if '.' in s_strip or 'e' in s_strip.lower():
            return float(s_strip)
        return int(s_strip)
    except Exception:
        try:
            return float(s_strip)
        except Exception:
            return s


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            return float(v.strip())
        return float(v)
    except Exception:
        return default


def _convert_numeric_fields(data: Dict[str, Any], numeric_fields: Dict[str, type]) -> Dict[str, Any]:
    """Recursively convert string numeric values to proper types before dataclass unpacking.

    This will coerce common string formats ("0.5", "1/2", "true") into native types.
    """
    def convert_item(item):
        if isinstance(item, dict):
            return {k: convert_item(v) for k, v in item.items()}
        if isinstance(item, list):
            return [convert_item(v) for v in item]
        return _try_convert_scalar(item)

    converted = convert_item(data)
    # Ensure the explicitly listed fields have expected types when possible
    for field_name, field_type in numeric_fields.items():
        if field_name in converted:
            v = converted[field_name]
            try:
                if field_type == float and not isinstance(v, float):
                    converted[field_name] = float(v)
                elif field_type == int and not isinstance(v, int):
                    converted[field_name] = int(float(v))
                elif field_type == bool and not isinstance(v, bool):
                    converted[field_name] = bool(v)
            except Exception:
                pass
    return converted

# ── Evolution Engine ─────────────────────────────────────────────────────────

class EvolutionEngine:
    """The Darwinian core. Every mutation is a prompt modification stored in genome.json."""
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._interactions: List[InteractionRecord] = []
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._experiments: Dict[str, Experiment] = {}
        self._mutations: Dict[str, Mutation] = {}
        self._history: List[EvolutionEvent] = []
        self._capability_gaps: Dict[str, CapabilityGap] = {}
        self._generation: int = 1
        self._loop_thread: Optional[threading.Thread] = None
        self._loop_running = False
        self._metrics_cache: Dict[str, List[float]] = defaultdict(list)
        self._load_genome()
        self._load_metrics()
        self._load_experiments()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_genome(self):
        try:
            if not GENOME_FILE.exists(): return
            data = json.loads(GENOME_FILE.read_text(encoding="utf-8"))
            self._generation = data.get("generation", 1)
            
            # Load mutations with type conversion for corrupted numeric fields
            for mid, md in data.get("mutations", {}).items():
                md_converted = _convert_numeric_fields(md, {
                    "fitness": float,
                    "interactions_since_applied": int,
                    "quality_before": float,
                    "quality_after": float,
                    "generation": int,
                    "active": bool,
                })
                self._mutations[mid] = Mutation(**md_converted)
            
            # Load hypotheses with type conversion
            for hid, hd in data.get("hypotheses", {}).items():
                hd_converted = _convert_numeric_fields(hd, {
                    "predicted_delta": float,
                    "confidence": float,
                })
                self._hypotheses[hid] = Hypothesis(**hd_converted)
        except Exception as e:
            print(f"[EvolutionEngine] Genome load error: {e}")

    def _save_genome(self):
        try:
            data = {
                "generation": self._generation, "last_updated": datetime.now().isoformat(),
                "active_mutation_count": sum(1 for m in self._mutations.values() if m.active),
                "mutations": {mid: asdict(m) for mid, m in self._mutations.items()},
                "hypotheses": {hid: asdict(h) for hid, h in self._hypotheses.items()},
            }
            GENOME_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            print(f"[EvolutionEngine] Genome save error: {e}")

    def _load_metrics(self):
        try:
            if not METRICS_FILE.exists(): return
            data = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            for rd in data.get("interactions", [])[-500:]:
                rd_converted = _convert_numeric_fields(rd, {
                    "user_satisfaction": float,
                    "response_quality": float,
                    "latency_ms": float,
                    "tokens_used": int,
                    "context_relevance": float,
                    "error_occurred": bool,
                    "was_proactive": bool,
                })
                self._interactions.append(InteractionRecord(**rd_converted))
            self._metrics_cache = defaultdict(list, data.get("cache", {}))
        except Exception as e:
            print(f"[EvolutionEngine] Metrics load error: {e}")

    def _save_metrics(self):
        try:
            data = {
                "interactions": [asdict(r) for r in self._interactions[-500:]],
                "cache": dict(self._metrics_cache), "saved_at": datetime.now().isoformat(),
            }
            METRICS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            print(f"[EvolutionEngine] Metrics save error: {e}")

    def _load_experiments(self):
        try:
            if not EXPERIMENTS_FILE.exists(): return
            data = json.loads(EXPERIMENTS_FILE.read_text(encoding="utf-8"))
            for eid, ed in data.get("experiments", {}).items():
                ed_converted = _convert_numeric_fields(ed, {
                    "duration_hours": float,
                    "min_samples": int,
                })
                self._experiments[eid] = Experiment(**ed_converted)
            for gid, gd in data.get("gaps", {}).items():
                gd_converted = _convert_numeric_fields(gd, {
                    "severity": float,
                    "priority": float,
                    "addressed": bool,
                })
                self._capability_gaps[gid] = CapabilityGap(**gd_converted)
        except Exception as e:
            print(f"[EvolutionEngine] Experiments load error: {e}")

    def _save_experiments(self):
        try:
            data = {
                "experiments": {eid: asdict(e) for eid, e in self._experiments.items()},
                "gaps": {gid: asdict(g) for gid, g in self._capability_gaps.items()},
                "saved_at": datetime.now().isoformat(),
            }
            EXPERIMENTS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            print(f"[EvolutionEngine] Experiments save error: {e}")

    def _log_event(self, event_type: str, description: str, details: Dict = None):
        event = EvolutionEvent(event_type=event_type, description=description,
                               details=details or {}, generation=self._generation)
        self._history.append(event)
        try:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event), default=str) + "\n")
        except Exception as e:
            print(f"[EvolutionEngine] Error: {e}")

    def _emit(self, event_type: str, payload: Dict, priority=EventPriority.NORMAL):
        try:
            get_neural_bus().publish(domain="self_evolution", event_type=event_type,
                payload=payload, source_module="evolution_engine", priority=priority)
        except Exception as e:
            print(f"[EvolutionEngine] Error: {e}")

    # ── 1. Performance Measurement ────────────────────────────────────────
    def record_interaction(self, interaction_type="conversation", response_quality=0.5,
                           user_satisfaction=None, latency_ms=0.0, tokens_used=0,
                           was_proactive=False, context_relevance=0.5, error_occurred=False,
                           tags=None, metadata=None) -> InteractionRecord:
        """Record a single interaction for performance tracking.

        Accepts either an InteractionRecord instance or individual fields.
        """
        if isinstance(interaction_type, InteractionRecord):
            rec = interaction_type
            with self._lock:
                self._interactions.append(rec)
                self._metrics_cache["quality"].append(_safe_float(rec.response_quality, 0.5))
                self._metrics_cache["latency"].append(_safe_float(rec.latency_ms, 0.0))
                if rec.user_satisfaction is not None:
                    self._metrics_cache["satisfaction"].append(_safe_float(rec.user_satisfaction, 0.0))
                self._metrics_cache["errors"].append(1.0 if rec.error_occurred else 0.0)
                for m in self._mutations.values():
                    if m.active: m.interactions_since_applied += 1
                self._save_metrics()
            return rec

        # Coerce common numeric/string inputs into proper types and normalize type fields
        try:
            rq = _safe_float(response_quality, 0.5)
        except Exception:
            rq = 0.5
        try:
            us = None if user_satisfaction is None else _safe_float(user_satisfaction, None)
        except Exception:
            us = None
        try:
            lat = _safe_float(latency_ms, 0.0)
        except Exception:
            lat = 0.0
        try:
            toks = int(tokens_used) if tokens_used is not None else 0
        except Exception:
            toks = 0

        # Ensure interaction_type is a stable str (some callers passed dicts)
        try:
            itype = interaction_type if isinstance(interaction_type, str) else str(interaction_type)
        except Exception:
            itype = "conversation"

        rec = InteractionRecord(
            interaction_type=itype, response_quality=rq,
            user_satisfaction=us, latency_ms=lat,
            tokens_used=toks, was_proactive=bool(was_proactive),
            context_relevance=_safe_float(context_relevance, 0.5), error_occurred=bool(error_occurred),
            tags=tags or [], metadata=metadata or {})
        with self._lock:
            self._interactions.append(rec)
            self._metrics_cache["quality"].append(rq)
            self._metrics_cache["latency"].append(lat)
            if us is not None:
                self._metrics_cache["satisfaction"].append(us)
            self._metrics_cache["errors"].append(1.0 if error_occurred else 0.0)
            for m in self._mutations.values():
                if m.active: m.interactions_since_applied += 1
            self._save_metrics()
        return rec

    def generate_performance_report(self, window_hours: float = 24.0) -> PerformanceReport:
        """Alias for get_performance_metrics used by tests and integration callers."""
        return self.get_performance_metrics(window_hours=window_hours)

    def create_hypothesis(self, claim: str, rationale: str, target_metric: str = "response_quality",
                          predicted_delta: float = 0.0, confidence: float = 0.5) -> Hypothesis:
        """Create a new hypothesis based on a claim and expected metric change."""
        hypothesis = Hypothesis(
            claim=claim,
            rationale=rationale,
            target_metric=target_metric,
            predicted_delta=predicted_delta,
            confidence=confidence,
        )
        with self._lock:
            self._hypotheses[hypothesis.id] = hypothesis
            self._save_genome()
        self._log_event("hypothesis_created", f"Hypothesis '{claim}' created",
                        {"hypothesis_id": hypothesis.id, "target_metric": target_metric})
        return hypothesis

    def create_mutation(self, mutation_type: str, description: str,
                        prompt_modification: str, injection_point: str = "system_suffix") -> Mutation:
        """Create and register a behavioral mutation."""
        mutation = Mutation(
            mutation_type=mutation_type,
            description=description,
            prompt_modification=prompt_modification,
            injection_point=injection_point,
            active=True,
            fitness=0.5,
        )
        with self._lock:
            self._mutations[mutation.id] = mutation
            self._save_genome()
        self._log_event("mutation_created", f"Mutation '{description}' created",
                        {"mutation_id": mutation.id, "type": mutation_type})
        return mutation

    def get_performance_metrics(self, window_hours: float = 24.0) -> PerformanceReport:
        """Compute aggregated performance over a time window."""
        cutoff = (datetime.now() - timedelta(hours=window_hours)).isoformat()
        with self._lock:
            # Normalize entries: support both InteractionRecord instances and plain dicts
            normalized = []
            for r in self._interactions:
                try:
                    if isinstance(r, dict):
                        # ensure timestamp exists
                        ts = r.get('timestamp', datetime.now().isoformat())
                        r_obj = InteractionRecord(**r)
                    else:
                        r_obj = r
                    normalized.append(r_obj)
                except Exception:
                    # fallback: skip malformed record
                    continue
            win = [r for r in normalized if r.timestamp >= cutoff]
        if not win:
            return PerformanceReport(window_start=cutoff, window_end=datetime.now().isoformat())
        quals = [_safe_float(r.response_quality, 0.0) for r in win]
        lats = [_safe_float(r.latency_ms, 0.0) for r in win]
        sats = [ _safe_float(r.user_satisfaction, 0.0) for r in win if r.user_satisfaction is not None]
        mid = len(quals) // 2
        trend = (statistics.mean(quals[mid:]) - statistics.mean(quals[:mid])) if mid > 0 else 0.0
        by_type: Dict[str, List[InteractionRecord]] = defaultdict(list)
        for r in win:
            key = r.interaction_type if isinstance(r.interaction_type, str) else str(r.interaction_type)
            by_type[key].append(r)
        bd = {}
        for t, recs in by_type.items():
            tq = [r.response_quality for r in recs]
            bd[t] = {"count": len(recs), "avg_quality": statistics.mean(tq),
                     "error_rate": sum(1 for r in recs if r.error_occurred)/len(recs)}
        return PerformanceReport(
            window_start=cutoff, window_end=datetime.now().isoformat(),
            total_interactions=len(win), avg_quality=statistics.mean(quals),
            avg_latency_ms=statistics.mean(lats) if lats else 0.0,
            error_rate=sum(1 for r in win if r.error_occurred)/len(win),
            proactive_ratio=sum(1 for r in win if r.was_proactive)/len(win),
            satisfaction_avg=statistics.mean(sats) if sats else None,
            quality_trend=trend,
            strongest_area=max(bd, key=lambda t: bd[t]["avg_quality"]) if bd else "unknown",
            weakest_area=min(bd, key=lambda t: bd[t]["avg_quality"]) if bd else "unknown",
            breakdown_by_type=bd)

    # ── 2. Hypothesis Generation ─────────────────────────────────────────
    def generate_hypotheses(self, max_hypotheses: int = 3) -> List[Hypothesis]:
        """Use LLM to analyze performance and generate improvement hypotheses with prompt mutations."""
        rpt = self.get_performance_metrics(window_hours=48.0)
        am = [m for m in self._mutations.values() if m.active]
        gps = list(self._capability_gaps.values())[:5]
        muts_str = chr(10).join(f'- [{m.id}] {m.description} (fit:{m.fitness:.2f})' for m in am) or '- None'
        gaps_str = chr(10).join(f'- [{g.area}] {g.description} (sev:{g.severity:.2f})' for g in gps) or '- None'
        prompt = (
            f"You are LOVE's evolution engine. Generate {max_hypotheses} testable hypotheses.\n\n"
            f"PERF (48h): {rpt.total_interactions} interactions | quality:{rpt.avg_quality:.3f} | "
            f"errors:{rpt.error_rate:.3f} | proactive:{rpt.proactive_ratio:.3f} | "
            f"trend:{rpt.quality_trend:+.3f}\nStrongest:{rpt.strongest_area} Weakest:{rpt.weakest_area}\n"
            f"Satisfaction: {rpt.satisfaction_avg if rpt.satisfaction_avg else 'n/a'}\n"
            f"Breakdown: {json.dumps(rpt.breakdown_by_type, default=str)}\n\n"
            f"ACTIVE MUTATIONS ({len(am)}):\n{muts_str}\nGAPS:\n{gaps_str}\n\n"
            f"Return JSON array. Each: claim, rationale, predicted_effect, "
            f"target_metric (response_quality|latency_ms|error_rate|proactive_ratio|satisfaction), "
            f"predicted_delta (float), confidence (0-1), "
            f"mutation_type (prompt_injection|tone_shift|strategy_change), "
            f"prompt_modification (exact text to inject). ONLY valid JSON array."
        )
        hypotheses = []
        try:
            raw = str(get_reasoning_llm(temperature=0.7).invoke(prompt)).strip()
            s, e = raw.find("["), raw.rfind("]") + 1
            for item in (json.loads(raw[s:e]) if s >= 0 and e > s else [])[:max_hypotheses]:
                try:
                    p_delta = float(item.get("predicted_delta", 0.05))
                except (ValueError, TypeError):
                    p_delta = 0.05
                try:
                    conf = min(1.0, max(0.0, float(item.get("confidence", 0.5))))
                except (ValueError, TypeError):
                    conf = 0.5
                h = Hypothesis(
                    claim=item.get("claim",""), rationale=item.get("rationale",""),
                    predicted_effect=item.get("predicted_effect",""),
                    target_metric=item.get("target_metric","response_quality"),
                    predicted_delta=p_delta,
                    confidence=conf,
                )
                h.evidence.append(json.dumps({
                    "mutation_type": item.get("mutation_type", "prompt_injection"),
                    "prompt_modification": item.get("prompt_modification", ""),
                }))
                self._hypotheses[h.id] = h
                hypotheses.append(h)
            if hypotheses:
                self._save_genome()
                self._log_event("hypothesis", f"Generated {len(hypotheses)} hypotheses",
                                {"ids": [h.id for h in hypotheses], "claims": [h.claim for h in hypotheses]})
                self._emit("evolution.hypothesis_generated",
                           {"count": len(hypotheses), "claims": [h.claim for h in hypotheses]})
        except Exception as e:
            print(f"[EvolutionEngine] Hypothesis generation error: {e}")
            self._log_event("error", f"Hypothesis generation failed: {e}")
        return hypotheses

    # ── 3. Experiment Framework ──────────────────────────────────────────
    def create_experiment(self, hypothesis_id: str, duration_hours: float = 24.0,
                          min_samples: int = 10) -> Optional[Experiment]:
        """Design an experiment to test a hypothesis."""
        h = self._hypotheses.get(hypothesis_id)
        if not h: return None
        md = {}  # extract mutation design from hypothesis evidence
        for ev in h.evidence:
            try:
                d = json.loads(ev)
                if "mutation_type" in d: md = d; break
            except (json.JSONDecodeError, TypeError): continue
        bl = self.get_performance_metrics(window_hours=max(24.0, duration_hours))
        ctrl = {"quality": bl.avg_quality, "latency": bl.avg_latency_ms,
                "error_rate": bl.error_rate, "proactive_ratio": bl.proactive_ratio}
        if bl.satisfaction_avg is not None: ctrl["satisfaction"] = bl.satisfaction_avg
        exp = Experiment(
            hypothesis_id=hypothesis_id, name=f"Test: {h.claim[:60]}", description=h.rationale,
            mutation_type=md.get("mutation_type", "prompt_injection"),
            mutation_params={"prompt_modification": md.get("prompt_modification", ""),
                             "target_metric": h.target_metric, "predicted_delta": h.predicted_delta},
            control_metrics=ctrl, duration_hours=duration_hours, min_samples=min_samples)
        with self._lock:
            self._experiments[exp.id] = exp; h.status = "testing"
            self._save_experiments(); self._save_genome()
        self._log_event("experiment_designed", f"'{exp.name}' designed",
                        {"experiment_id": exp.id, "hypothesis_id": hypothesis_id})
        return exp

    def run_experiment(self, experiment_id: str) -> bool:
        """Start an experiment by applying its mutation."""
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != "designed": return False
        pm = exp.mutation_params.get("prompt_modification", "")
        if not pm: return False
        mut = self.mutate_behavior(exp.mutation_type, {
            "description": exp.name, "prompt_modification": pm,
            "injection_point": "system_suffix", "experiment_id": exp.id})
        if not mut: return False
        with self._lock:
            exp.status = "running"; exp.started_at = datetime.now().isoformat()
            self._save_experiments()
        self._log_event("experiment_started", f"'{exp.name}' is live",
                        {"experiment_id": exp.id, "mutation_id": mut.id})
        self._emit("evolution.experiment_started", {
            "experiment_id": exp.id, "name": exp.name,
            "mutation_id": mut.id, "duration_hours": exp.duration_hours})
        return True

    def evaluate_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Evaluate a running experiment — compare treatment vs control metrics."""
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != "running" or not exp.started_at:
            return None
        elapsed_h = (datetime.now() - datetime.fromisoformat(exp.started_at)).total_seconds() / 3600.0
        if elapsed_h < exp.duration_hours * 0.5:
            return None  # not enough time elapsed
        treatment = self.get_performance_metrics(window_hours=max(1.0, elapsed_h))
        if treatment.total_interactions < exp.min_samples:
            return None
        # Map target metric to control/treatment values
        target = exp.mutation_params.get("target_metric", "response_quality")
        metric_map = {
            "response_quality": ("quality", treatment.avg_quality),
            "latency_ms": ("latency", treatment.avg_latency_ms),
            "error_rate": ("error_rate", treatment.error_rate),
            "proactive_ratio": ("proactive_ratio", treatment.proactive_ratio),
            "satisfaction": ("satisfaction", treatment.satisfaction_avg or 0.0),
        }
        ck, tv = metric_map.get(target, ("quality", treatment.avg_quality))
        cv = exp.control_metrics.get(ck, 0.5)
        delta = tv - cv
        if target in ("error_rate", "latency_ms"): delta = -delta  # lower = better
        # Significance test
        threshold = max(0.01, abs(cv) * 0.02)
        is_sig = abs(delta) > threshold and treatment.total_interactions >= exp.min_samples
        if treatment.total_interactions > 0 and cv > 0:
            p_value = max(0.001, 1.0 / (1.0 + (abs(delta)/max(0.01, cv)) * math.sqrt(treatment.total_interactions)))
        else:
            p_value = 1.0
        should_integrate = is_sig and delta > 0 and p_value < 0.15
        d = "improved" if delta > 0 else "degraded"
        conclusion = (f"Mutation {d} {target} by {abs(delta):.4f} (p={p_value:.3f}). "
                      f"{'Integrating.' if should_integrate else 'Reverting.'}") if is_sig else \
                     f"No significant effect on {target} (delta={delta:+.4f}, p={p_value:.3f}). Reverting."
        result = ExperimentResult(
            experiment_id=experiment_id, hypothesis_id=exp.hypothesis_id,
            control_mean=cv, treatment_mean=tv, delta=delta,
            sample_size=treatment.total_interactions, p_value=round(p_value, 4),
            is_significant=is_sig, conclusion=conclusion, should_integrate=should_integrate,
        )
        with self._lock:
            exp.status = "completed"; exp.completed_at = datetime.now().isoformat()
            h = self._hypotheses.get(exp.hypothesis_id)
            if h:
                h.status = "confirmed" if should_integrate else "rejected"
                h.tested_at = datetime.now().isoformat()
                h.evidence.append(json.dumps(asdict(result), default=str))
            if not should_integrate: self._revert_experiment_mutations(experiment_id)
            self._save_experiments(); self._save_genome()
        tag = "confirmed" if should_integrate else "rejected"
        self._log_event(f"experiment_{tag}", f"Experiment '{exp.name}' {tag}", asdict(result))
        return result

    def _revert_experiment_mutations(self, experiment_id: str):
        """Revert all mutations from a specific experiment."""
        for mut in self._mutations.values():
            if mut.experiment_id == experiment_id and mut.active:
                mut.active = False
                mut.reverted_at = datetime.now().isoformat()

    # ── 4. Behavioral Mutations ─────────────────────────────────────────
    def mutate_behavior(self, mutation_type: str, params: Dict[str, Any]) -> Optional[Mutation]:
        """Apply a behavioral mutation — injectable prompt modification."""
        pm = params.get("prompt_modification", "")
        if not pm: return None
        bl = self.get_performance_metrics(window_hours=24.0)
        m = Mutation(mutation_type=mutation_type, description=params.get("description", f"Mutation: {mutation_type}"),
                     prompt_modification=pm, injection_point=params.get("injection_point", "system_suffix"),
                     experiment_id=params.get("experiment_id"), active=True, fitness=0.5,
                     quality_before=bl.avg_quality, generation=self._generation)
        with self._lock:
            self._mutations[m.id] = m; self._save_genome()
        self._log_event("mutation_applied", f"'{m.description}' applied",
                        {"mutation_id": m.id, "type": mutation_type, "prompt": pm[:200]})
        self._emit("evolution.mutation_applied",
                   {"mutation_id": m.id, "description": m.description, "type": mutation_type},
                   priority=EventPriority.HIGH)
        return m

    def get_active_mutations(self) -> List[Mutation]:
        with self._lock: return [m for m in self._mutations.values() if m.active]

    def revert_mutation(self, mutation_id: str, reason: str = "manual") -> bool:
        with self._lock:
            mut = self._mutations.get(mutation_id)
            if not mut or not mut.active: return False
            mut.active = False; mut.reverted_at = datetime.now().isoformat()
            self._save_genome()
        self._log_event("mutation_reverted", f"'{mut.description}' reverted ({reason})",
                        {"mutation_id": mutation_id, "reason": reason})
        return True

    # ── 5. Validation ──────────────────────────────────────────────────────
    def validate_mutation(self, mutation_id: str) -> Dict[str, Any]:
        """Validate a mutation with Welch's t-test on pre/post quality distributions."""
        mut = self._mutations.get(mutation_id)
        if not mut: return {"valid": False, "error": "not found"}
        if not mut.active: return {"valid": False, "error": "not active"}
        if mut.interactions_since_applied < 5:
            return {"valid": None, "status": "insufficient_data",
                    "interactions": mut.interactions_since_applied, "needed": 5}
        cutoff = mut.applied_at
        with self._lock:
            post = [r.response_quality for r in self._interactions if r.timestamp >= cutoff]
            pre = [r.response_quality for r in self._interactions if r.timestamp < cutoff][-50:]
        if len(post) < 5 or len(pre) < 3:
            return {"valid": None, "status": "insufficient_data",
                    "post_count": len(post), "pre_count": len(pre)}
        pre_m, post_m = statistics.mean(pre), statistics.mean(post)
        delta = post_m - pre_m
        if len(post) >= 2 and len(pre) >= 2:
            se = math.sqrt((statistics.stdev(pre)**2/len(pre)) + (statistics.stdev(post)**2/len(post)))
            t_stat = delta / se if se > 0 else 0.0
            df = min(len(pre), len(post)) - 1
            p_val = 1.0/(1.0+math.exp(0.7*abs(t_stat)*math.sqrt(max(1,df)/5.0))) if se > 0 else 1.0
        else:
            t_stat, p_val = 0.0, 1.0
        beneficial = delta > 0 and p_val < 0.2
        harmful = delta < -0.02 and p_val < 0.2
        with self._lock:
            mut.fitness = min(1.0, mut.fitness+0.1) if beneficial else (
                max(0.0, mut.fitness-0.15) if harmful else mut.fitness)
            mut.quality_after = post_m
            self._save_genome()
        rec = "keep" if beneficial else ("revert" if harmful else "continue_monitoring")
        result = {
            "valid": beneficial, "mutation_id": mutation_id,
            "pre_mean": round(pre_m,4), "post_mean": round(post_m,4),
            "delta": round(delta,4), "t_stat": round(t_stat,3), "p_value": round(p_val,4),
            "is_significant": p_val < 0.2, "is_beneficial": beneficial, "is_harmful": harmful,
            "recommendation": rec, "sample_size": {"pre": len(pre), "post": len(post)},
            "fitness": round(mut.fitness, 3),
        }
        if harmful:
            self.revert_mutation(mutation_id, reason="validation_harmful")
            result["action_taken"] = "reverted"
        return result

    # ── 6. Evolution History ────────────────────────────────────────────
    def get_evolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent evolution history."""
        events = self._history[-limit:]
        if not events and HISTORY_FILE.exists():
            try:
                lines = HISTORY_FILE.read_text(encoding="utf-8").strip().split("\n")
                for line in lines[-limit:]:
                    if line.strip():
                        events.append(EvolutionEvent(**json.loads(line)))
            except Exception:
                pass
        return [asdict(e) for e in events[-limit:]]

    def explain_evolution(self) -> str:
        """Generate an LLM-narrated summary of LOVE's evolutionary journey."""
        active = self.get_active_mutations()
        r = self.get_performance_metrics(window_hours=72.0)
        n_exp = len(self._experiments)
        n_done = sum(1 for e in self._experiments.values() if e.status == "completed")
        n_mut = len(self._mutations)
        n_rev = sum(1 for m in self._mutations.values() if not m.active and m.reverted_at)
        muts_desc = chr(10).join(f'- {m.description} (fitness: {m.fitness:.2f})' for m in active) or '- None yet'
        prompt = (f"Narrate LOVE's evolutionary journey in 3-5 warm, honest sentences.\n"
                  f"Gen {self._generation} | {len(active)} active mutations | {n_exp} experiments ({n_done} done)\n"
                  f"{n_mut} mutations tried ({n_rev} reverted) | Quality: {r.avg_quality:.3f} | "
                  f"Trend: {r.quality_trend:+.3f}\nAdaptations:\n{muts_desc}\n"
                  f"Write from LOVE's perspective. Be specific. No generic AI talk.")
        try:
            return str(get_reasoning_llm(temperature=0.6).invoke(prompt)).strip()
        except Exception:
            return f"Gen {self._generation}. {len(active)} adaptations, {n_mut} tried. Quality: {r.avg_quality:.3f}."

    def get_generation(self) -> int:
        """Current evolutionary generation number."""
        return self._generation

    def get_current_genome(self) -> Dict[str, Any]:
        """Full behavioral genome — active prompt modifications organized by injection point."""
        active = self.get_active_mutations()
        genome: Dict[str, List[Dict]] = defaultdict(list)
        for m in active:
            genome[m.injection_point].append({
                "id": m.id, "type": m.mutation_type, "description": m.description,
                "prompt_modification": m.prompt_modification, "fitness": m.fitness,
                "generation": m.generation, "interactions_tested": m.interactions_since_applied,
            })
        return {
            "generation": self._generation, "total_active_mutations": len(active),
            "injection_points": dict(genome),
            "assembled_prompt_suffix": self._assemble_genome_prompt("system_suffix"),
            "assembled_prompt_prefix": self._assemble_genome_prompt("system_prefix"),
            "assembled_context_frame": self._assemble_genome_prompt("context_frame"),
        }

    def _assemble_genome_prompt(self, injection_point: str) -> str:
        """Assemble active mutations for a given injection point, highest fitness first."""
        muts = sorted([m for m in self._mutations.values()
                       if m.active and m.injection_point == injection_point],
                      key=lambda m: m.fitness, reverse=True)
        return "\n".join(m.prompt_modification for m in muts) if muts else ""

    # ── 7. Autonomous Loop ─────────────────────────────────────────────
    def start_evolution_loop(self, interval: int = 3600):
        """Start the autonomous evolution daemon."""
        if self._loop_running: return
        self._loop_running = True
        self._loop_thread = threading.Thread(
            target=self._evolution_loop, args=(interval,), daemon=True, name="evolution-loop")
        self._loop_thread.start()
        self._log_event("loop_started", f"Evolution loop started (interval={interval}s)")

    def stop_evolution_loop(self):
        self._loop_running = False
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5)
        self._log_event("loop_stopped", "Evolution loop stopped")

    def _evolution_loop(self, interval: int):
        time.sleep(30)  # let other systems init
        while self._loop_running:
            try:
                self._run_evolution_cycle()
            except Exception as e:
                tb = traceback.format_exc()
                print(f"[EvolutionEngine] Cycle error: {e}\n{tb}")
                self._log_event("cycle_error", f"Cycle failed: {e}\n{tb}")
            for _ in range(interval):  # interruptible sleep
                if not self._loop_running: break
                time.sleep(1)

    def _run_evolution_cycle(self):
        """One full measure-hypothesize-experiment-validate-integrate cycle."""
        t0 = time.time()
        self._log_event("cycle_start", f"Cycle beginning (gen {self._generation})")
        # 1. Validate active mutations
        validated = 0
        for mut in list(self._mutations.values()):
            if mut.active and mut.interactions_since_applied >= 5:
                r = self.validate_mutation(mut.id); validated += 1
                if r.get("action_taken") == "reverted":
                    print(f"[EvolutionEngine] Auto-reverted: {mut.description}")
        # 2. Evaluate running experiments
        evaluated = 0
        for exp in list(self._experiments.values()):
            if exp.status == "running":
                r = self.evaluate_experiment(exp.id)
                if r:
                    evaluated += 1
                    if r.should_integrate: self._integrate_mutation(exp, r)
        # 3. Generate hypotheses if few pending
        pending = [h for h in self._hypotheses.values() if h.status == "proposed"]
        new_h = self.generate_hypotheses(2) if len(pending) < 2 and len(self._interactions) >= 5 else []
        # 4. Launch best untested hypothesis (max 2 concurrent)
        if sum(1 for e in self._experiments.values() if e.status == "running") < 2:
            best = self._pick_best_hypothesis()
            if best:
                exp = self.create_experiment(best.id, 24.0, 10)
                if exp: self.run_experiment(exp.id)
        # 5. Discover gaps periodically
        if self._generation % 3 == 0: self.identify_gaps()
        self._log_event("cycle_complete", f"Done in {time.time()-t0:.1f}s",
                        {"validated": validated, "evaluated": evaluated, "new_hypotheses": len(new_h)})

    def _pick_best_hypothesis(self) -> Optional[Hypothesis]:
        cands = [h for h in self._hypotheses.values() if h.status == "proposed"]
        return max(cands, key=lambda h: h.confidence * abs(h.predicted_delta)) if cands else None

    def _integrate_mutation(self, experiment: Experiment, result: ExperimentResult):
        self._generation += 1
        for mut in self._mutations.values():
            if mut.experiment_id == experiment.id and mut.active:
                mut.fitness = min(1.0, mut.fitness + 0.2); mut.generation = self._generation
        self._save_genome()
        self._log_event("integrated",
            f"'{experiment.name}' integrated (gen {self._generation}, delta={result.delta:+.4f})",
            {"experiment_id": experiment.id, "result": asdict(result)})
        self._emit("evolution.integrated", {
            "experiment_name": experiment.name, "generation": self._generation,
            "delta": result.delta, "target_metric": experiment.mutation_params.get("target_metric"),
        }, priority=EventPriority.HIGH)

    # ── 8. Capability Discovery ─────────────────────────────────────────
    def discover_capabilities(self) -> Dict[str, Any]:
        """Analyze current capabilities from interaction history and active genome."""
        rpt = self.get_performance_metrics(window_hours=72.0)
        tag_stats: Dict[str, List[float]] = defaultdict(list)
        with self._lock:
            for rec in self._interactions[-200:]:
                for tag in rec.tags: tag_stats[tag].append(rec.response_quality)
                tag_stats[rec.interaction_type].append(rec.response_quality)
        caps = {}
        for tag, scores in tag_stats.items():
            if len(scores) >= 3:
                caps[tag] = {
                    "avg_quality": round(statistics.mean(scores), 3), "samples": len(scores),
                    "consistency": round(1.0-(statistics.stdev(scores) if len(scores)>=2 else 0.5), 3),
                    "trend": self._compute_trend(scores),
                }
        return {"overall_quality": round(rpt.avg_quality, 3), "generation": self._generation,
                "active_adaptations": len(self.get_active_mutations()), "capabilities": caps,
                "strongest": rpt.strongest_area, "weakest": rpt.weakest_area}

    def identify_gaps(self) -> List[CapabilityGap]:
        """Use LLM to identify capability gaps from performance data."""
        rpt = self.get_performance_metrics(window_hours=48.0)
        caps = self.discover_capabilities()
        prompt = (f"You are LOVE's self-analysis engine. Identify 2-3 capability gaps.\n"
                  f"Quality {rpt.avg_quality:.3f} | Errors {rpt.error_rate:.3f} | "
                  f"Proactive {rpt.proactive_ratio:.3f} | Trend {rpt.quality_trend:+.3f}\n"
                  f"Weakest: {rpt.weakest_area}\n"
                  f"Breakdown: {json.dumps(rpt.breakdown_by_type, default=str)}\n"
                  f"Capabilities: {json.dumps(caps.get('capabilities',{}), default=str)}\n\n"
                  f'Return JSON array: [{{"area":"...","description":"...","severity":0.5,"suggested_fix":"..."}}]\n'
                  f"Return ONLY valid JSON array.")
        gaps = []
        try:
            raw = str(get_reasoning_llm(temperature=0.5).invoke(prompt)).strip()
            s, e = raw.find("["), raw.rfind("]") + 1
            for item in (json.loads(raw[s:e]) if s >= 0 and e > s else [])[:3]:
                try:
                    sev = min(1.0, max(0.0, float(item.get("severity", 0.5))))
                except (ValueError, TypeError):
                    sev = 0.5
                gap = CapabilityGap(area=item.get("area","unknown"), description=item.get("description",""),
                                    severity=sev, suggested_fix=item.get("suggested_fix",""), priority=sev)
                with self._lock: self._capability_gaps[gap.id] = gap
                gaps.append(gap)
            if gaps:
                self._save_experiments()
                self._log_event("gaps_identified", f"{len(gaps)} gaps found",
                                {"gaps": [{"area": g.area, "severity": g.severity} for g in gaps]})
        except Exception as e:
            print(f"[EvolutionEngine] Gap identification error: {e}")
        return gaps

    def get_improvement_priorities(self) -> List[Dict[str, Any]]:
        """Ranked improvements: gaps + weak mutations + rejected high-confidence hypotheses."""
        priorities = []
        for g in self._capability_gaps.values():
            if not g.addressed:
                priorities.append({"source": "gap", "area": g.area, "description": g.description,
                                   "priority": g.priority, "action": g.suggested_fix})
        for m in self._mutations.values():
            if m.active and m.fitness < 0.3 and m.interactions_since_applied >= 10:
                priorities.append({"source": "weak_mutation", "area": m.mutation_type,
                    "description": f"'{m.description}' low fitness ({m.fitness:.2f})",
                    "priority": 1.0 - m.fitness, "action": "Revert or redesign", "mutation_id": m.id})
        for h in self._hypotheses.values():
            if h.status == "rejected" and h.confidence > 0.6:
                priorities.append({"source": "rejected_hypothesis", "area": h.target_metric,
                    "description": f"Rejected: {h.claim}", "priority": h.confidence*0.5,
                    "action": "Revisit with different approach"})
        priorities.sort(key=lambda p: p["priority"], reverse=True)
        return priorities[:10]

    # ── Utility ───────────────────────────────────────────────────────────
    def _compute_trend(self, values: List[float]) -> str:
        if len(values) < 4: return "insufficient_data"
        mid = len(values) // 2
        d = statistics.mean(values[mid:]) - statistics.mean(values[:mid])
        return "improving" if d > 0.03 else ("declining" if d < -0.03 else "stable")

    def get_status(self) -> Dict[str, Any]:
        return {
            "generation": self._generation, "active_mutations": len(self.get_active_mutations()),
            "running_experiments": sum(1 for e in self._experiments.values() if e.status == "running"),
            "total_interactions": len(self._interactions), "total_hypotheses": len(self._hypotheses),
            "total_experiments": len(self._experiments),
            "open_gaps": sum(1 for g in self._capability_gaps.values() if not g.addressed),
            "loop_running": self._loop_running, "genome_file": str(GENOME_FILE),
        }


# ── Singleton Access ─────────────────────────────────────────────────────────

_engine_instance: Optional[EvolutionEngine] = None
_engine_lock = threading.Lock()

def get_evolution_engine() -> EvolutionEngine:
    global _engine_instance
    if _engine_instance is None:
        with _engine_lock:
            if _engine_instance is None:
                _engine_instance = EvolutionEngine()
    return _engine_instance
