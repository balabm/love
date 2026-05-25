"""
Metacognitive Monitor — LOVE's Self-Awareness System

This is how LOVE thinks about its own thinking. Not vanity metrics or
performance dashboards, but genuine self-awareness: knowing what you know,
admitting what you don't, tracking what works, and adapting when something isn't.

Inspired by calibrated confidence research and meta-learning theory.
A mind that cannot observe itself cannot improve itself.

Integration:
    - Publishes to neural_bus on overload, anomalies, plateaus, milestones
    - Called by cognitive_architecture before/after reasoning
    - Feeds into evolution_engine for improvement targeting
    - Thread-safe singleton via get_metacognitive_monitor()
"""

import json
import logging
import math
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("love.metacognition")

# ─── Persistence Paths ──────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "metacognition"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CALIBRATION_PATH = DATA_DIR / "calibration.json"
STRATEGY_PATH = DATA_DIR / "strategy_performance.json"
PERFORMANCE_PATH = DATA_DIR / "performance_history.json"
BASELINES_PATH = DATA_DIR / "baselines.json"
LEARNING_LOG_PATH = DATA_DIR / "learning_log.json"

MAX_HISTORY = 5000  # Rolling window for performance history


# ─── Enumerations ────────────────────────────────────────────────────────────────

class ConfidenceDomain(str, Enum):
    FACTUAL = "factual"
    EMOTIONAL = "emotional"
    PREDICTIONS = "predictions"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    INTERPERSONAL = "interpersonal"


class KnowledgeLevel(str, Enum):
    DEEP_EXPERTISE = "deep_expertise"
    SOLID_KNOWLEDGE = "solid_knowledge"
    SURFACE_FAMILIARITY = "surface_familiarity"
    UNCERTAIN = "uncertain"
    NO_KNOWLEDGE = "no_knowledge"


class CognitiveLoadLevel(str, Enum):
    TRIVIAL = "trivial"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    OVERLOADED = "overloaded"


class Strategy(str, Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    DECOMPOSE = "decompose"
    ANALOGICAL = "analogical"
    DIRECT = "direct"
    EMPATHETIC = "empathetic"
    SOCRATIC = "socratic"


# ─── Data Structures ─────────────────────────────────────────────────────────────

@dataclass
class CalibratedConfidence:
    """A confidence score that's been reality-checked against track record."""
    raw_confidence: float           # What LOVE initially claimed (0.0-1.0)
    calibrated_confidence: float    # Adjusted based on historical accuracy
    domain: str
    evidence_strength: float        # How strong the supporting evidence is (0.0-1.0)
    calibration_gap: float = 0.0    # raw - actual accuracy (positive = overconfident)
    sample_size: int = 0            # How many past predictions inform this calibration

    @property
    def is_well_calibrated(self) -> bool:
        return abs(self.calibration_gap) < 0.1

    @property
    def interpretation(self) -> str:
        if self.calibration_gap > 0.15:
            return "overconfident — I tend to overestimate in this domain"
        elif self.calibration_gap < -0.15:
            return "underconfident — I'm actually better than I think here"
        return "well-calibrated"


@dataclass
class KnowledgeAssessment:
    """Honest assessment of what LOVE knows about a topic."""
    topic: str
    level: str
    confidence_in_assessment: float     # How sure LOVE is about its own assessment
    knowledge_sources: List[str]        # Where this knowledge comes from
    gaps: List[str] = field(default_factory=list)  # Known gaps
    related_strengths: List[str] = field(default_factory=list)
    honest_statement: str = ""          # Plain language: what I know and don't

    def __post_init__(self):
        if not self.honest_statement:
            self.honest_statement = self._generate_honest_statement()

    def _generate_honest_statement(self) -> str:
        statements = {
            KnowledgeLevel.DEEP_EXPERTISE.value: f"I have deep expertise in {self.topic}.",
            KnowledgeLevel.SOLID_KNOWLEDGE.value: f"I have solid working knowledge of {self.topic}, though not exhaustive.",
            KnowledgeLevel.SURFACE_FAMILIARITY.value: f"I have surface familiarity with {self.topic} — enough to discuss, not enough to rely on.",
            KnowledgeLevel.UNCERTAIN.value: f"I'm uncertain about {self.topic}. I might have fragments, but I can't vouch for accuracy.",
            KnowledgeLevel.NO_KNOWLEDGE.value: f"I genuinely don't know about {self.topic}. I'd be making things up if I tried.",
        }
        return statements.get(self.level, f"My knowledge of {self.topic} is unclear.")


@dataclass
class CognitiveLoad:
    """Current cognitive load assessment."""
    level: str
    score: float                        # 0.0-1.0
    factors: Dict[str, float]           # Individual factor scores
    recommendations: List[str]          # What to do about it
    timestamp: float = field(default_factory=time.time)

    @property
    def needs_intervention(self) -> bool:
        return self.level in (CognitiveLoadLevel.HEAVY.value, CognitiveLoadLevel.OVERLOADED.value)


@dataclass
class QualityAssessment:
    """Self-assessment of response quality."""
    overall_score: float                # 0.0-1.0
    dimensions: Dict[str, float]        # Per-dimension scores
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]              # Concrete improvements for next time
    timestamp: float = field(default_factory=time.time)


@dataclass
class AnomalyReport:
    """Something unusual detected in LOVE's own behavior."""
    type: str                           # personality_shift, error_spike, confidence_collapse, style_change
    severity: float                     # 0.0-1.0
    description: str
    baseline_comparison: Dict[str, Any]  # Normal vs. current
    recommendation: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class StrategyPerformance:
    """Performance record for a reasoning strategy."""
    strategy: str
    task_type: str
    avg_quality: float
    sample_size: int
    trend: str                          # "improving", "declining", "stable"
    recent_scores: List[float] = field(default_factory=list)


@dataclass
class AttentionItem:
    """An item competing for cognitive attention."""
    id: str
    description: str
    urgency: float = 0.5
    emotional_weight: float = 0.5
    user_expectation: float = 0.5
    novelty: float = 0.5
    relevance: float = 0.5
    composite_priority: float = 0.0

    def compute_priority(self) -> float:
        """Weighted priority computation."""
        weights = {
            "urgency": 0.30,
            "emotional_weight": 0.25,
            "user_expectation": 0.20,
            "relevance": 0.15,
            "novelty": 0.10,
        }
        self.composite_priority = sum(
            getattr(self, k) * w for k, w in weights.items()
        )
        return self.composite_priority


# ─── The Monitor ─────────────────────────────────────────────────────────────────

class MetacognitiveMonitor:
    """
    LOVE's self-awareness system.

    Not just metrics — genuine self-understanding. Tracks confidence calibration,
    knowledge boundaries, strategy performance, cognitive load, attention allocation,
    learning rates, and behavioral anomalies.

    Thread-safe. Persists to disk. Publishes significant events to neural_bus.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._initialized = False

        # Calibration: domain -> list of (predicted_confidence, was_correct)
        self._calibration_data: Dict[str, List[Tuple[float, bool]]] = defaultdict(list)

        # Strategy performance: (strategy, task_type) -> list of quality scores
        self._strategy_records: Dict[str, List[float]] = defaultdict(list)

        # Performance history: rolling deque of assessments
        self._performance_history: deque = deque(maxlen=MAX_HISTORY)

        # Behavioral baselines
        self._baselines: Dict[str, Any] = {}

        # Learning log: domain -> list of (timestamp, score) for tracking improvement
        self._learning_log: Dict[str, List[Tuple[float, float]]] = defaultdict(list)

        # Attention state
        self._attention_items: List[AttentionItem] = []
        self._attention_focus: Optional[str] = None

        # Cognitive load state
        self._current_load: Optional[CognitiveLoad] = None

        # Neural bus reference (lazy-loaded to avoid circular imports)
        self._bus = None

        self._load_state()
        self._initialized = True
        logger.info("[MetaCog] Metacognitive Monitor initialized — self-awareness active")

    # ─── Neural Bus Integration ──────────────────────────────────────────────

    def _get_bus(self):
        """Lazy-load neural bus to avoid circular imports."""
        if self._bus is None:
            try:
                from core.neural_bus import get_neural_bus
                self._bus = get_neural_bus()
            except Exception:
                logger.debug("[MetaCog] Neural bus unavailable — operating standalone")
        return self._bus

    def _publish(self, event_type: str, payload: Dict[str, Any], priority: str = "NORMAL"):
        """Publish an event to the neural bus if available."""
        bus = self._get_bus()
        if bus:
            try:
                from core.neural_bus import EventPriority
                prio_map = {
                    "CRITICAL": EventPriority.CRITICAL,
                    "HIGH": EventPriority.HIGH,
                    "NORMAL": EventPriority.NORMAL,
                    "LOW": EventPriority.LOW,
                }
                bus.publish(
                    domain="self_evolution",
                    event_type=event_type,
                    payload=payload,
                    source_module="metacognitive_monitor",
                    priority=prio_map.get(priority, EventPriority.NORMAL),
                )
            except Exception as e:
                logger.debug(f"[MetaCog] Bus publish failed: {e}")

    # ─── 1. Confidence Calibration ──────────────────────────────────────────

    def calibrate_confidence(
        self, claim: str, evidence: List[str], domain: str, raw_confidence: float = 0.7
    ) -> CalibratedConfidence:
        """
        Calibrate a confidence claim against historical accuracy.

        If LOVE says "I'm 80% sure" but historically is right only 60% of the time
        in this domain, the calibrated confidence adjusts downward.
        """
        with self._lock:
            domain_key = domain if domain in [d.value for d in ConfidenceDomain] else "factual"
            history = self._calibration_data.get(domain_key, [])

            # Calculate historical accuracy at this confidence level
            evidence_strength = min(len(evidence) / 5.0, 1.0)  # More evidence = stronger

            if len(history) >= 10:
                # Enough data to calibrate
                # Find predictions near this confidence level (±0.15 band)
                nearby = [
                    was_correct for conf, was_correct in history
                    if abs(conf - raw_confidence) <= 0.15
                ]
                if len(nearby) >= 5:
                    actual_accuracy = sum(nearby) / len(nearby)
                    calibration_gap = raw_confidence - actual_accuracy
                    # Adjust toward reality
                    calibrated = raw_confidence - (calibration_gap * 0.7)
                    calibrated = max(0.05, min(0.99, calibrated))
                else:
                    # Not enough data at this specific level, use overall domain accuracy
                    overall_accuracy = sum(c for _, c in history) / len(history)
                    calibration_gap = raw_confidence - overall_accuracy
                    calibrated = raw_confidence - (calibration_gap * 0.4)
                    calibrated = max(0.05, min(0.99, calibrated))
            else:
                # Cold start: apply conservative prior (slightly reduce high confidence)
                calibration_gap = 0.0
                if raw_confidence > 0.85:
                    calibrated = raw_confidence * 0.9  # Temper overconfidence early
                else:
                    calibrated = raw_confidence
                nearby = []

            result = CalibratedConfidence(
                raw_confidence=raw_confidence,
                calibrated_confidence=round(calibrated, 3),
                domain=domain_key,
                evidence_strength=round(evidence_strength, 3),
                calibration_gap=round(calibration_gap, 3),
                sample_size=len(nearby) if nearby else len(history),
            )

            logger.info(
                f"[MetaCog] Calibration: {domain_key} raw={raw_confidence:.2f} "
                f"calibrated={calibrated:.2f} gap={calibration_gap:+.2f} ({result.interpretation})"
            )
            return result

    def record_calibration_outcome(self, domain: str, predicted_confidence: float, was_correct: bool):
        """Record whether a prediction at a given confidence level was actually correct."""
        with self._lock:
            domain_key = domain if domain in [d.value for d in ConfidenceDomain] else "factual"
            self._calibration_data[domain_key].append((predicted_confidence, was_correct))
            # Keep rolling window of 500 per domain
            if len(self._calibration_data[domain_key]) > 500:
                self._calibration_data[domain_key] = self._calibration_data[domain_key][-500:]
            self._save_calibration()

    def get_calibration_curve(self, domain: Optional[str] = None) -> Dict[str, List[Tuple[float, float]]]:
        """
        Get predicted vs actual confidence curves.

        Returns bins of (predicted_confidence_midpoint, actual_accuracy) per domain.
        Perfect calibration = diagonal line.
        """
        with self._lock:
            domains = [domain] if domain else list(self._calibration_data.keys())
            curves = {}

            for d in domains:
                history = self._calibration_data.get(d, [])
                if len(history) < 10:
                    curves[d] = []
                    continue

                # Bin into 10 buckets: 0.0-0.1, 0.1-0.2, ..., 0.9-1.0
                bins = defaultdict(list)
                for conf, correct in history:
                    bucket = min(int(conf * 10), 9)
                    bins[bucket].append(1.0 if correct else 0.0)

                curve = []
                for bucket in range(10):
                    if bins[bucket]:
                        midpoint = (bucket + 0.5) / 10.0
                        actual = sum(bins[bucket]) / len(bins[bucket])
                        curve.append((round(midpoint, 2), round(actual, 3)))
                curves[d] = curve

            return curves

    # ─── 2. Knowledge Boundary Detection ─────────────────────────────────────

    def assess_knowledge(self, topic: str, context: Optional[Dict] = None) -> KnowledgeAssessment:
        """
        Honestly assess what LOVE knows about a topic.

        Not falsely humble, not falsely confident. Just honest.
        """
        # Heuristic knowledge assessment based on available signals
        context = context or {}
        prior_interactions = context.get("prior_interactions", 0)
        source_quality = context.get("source_quality", 0.5)
        recency = context.get("recency_score", 0.5)
        depth_signals = context.get("depth_signals", 0)

        # Composite knowledge score
        score = (
            min(prior_interactions / 20.0, 0.3) +
            source_quality * 0.3 +
            recency * 0.2 +
            min(depth_signals / 10.0, 0.2)
        )

        # Map score to level
        if score >= 0.8:
            level = KnowledgeLevel.DEEP_EXPERTISE.value
        elif score >= 0.6:
            level = KnowledgeLevel.SOLID_KNOWLEDGE.value
        elif score >= 0.4:
            level = KnowledgeLevel.SURFACE_FAMILIARITY.value
        elif score >= 0.2:
            level = KnowledgeLevel.UNCERTAIN.value
        else:
            level = KnowledgeLevel.NO_KNOWLEDGE.value

        # Confidence in our own assessment decreases for edge cases
        assessment_confidence = 0.8 if score > 0.3 and score < 0.7 else 0.6

        assessment = KnowledgeAssessment(
            topic=topic,
            level=level,
            confidence_in_assessment=assessment_confidence,
            knowledge_sources=context.get("sources", ["general training"]),
            gaps=context.get("known_gaps", []),
            related_strengths=context.get("related_strengths", []),
        )

        logger.info(f"[MetaCog] Knowledge assessment: '{topic}' → {level} (confidence: {assessment_confidence:.2f})")
        return assessment

    def get_unknown_unknowns(self) -> List[str]:
        """
        Identify areas where LOVE doesn't know what it doesn't know.

        These are domains where we have very low interaction count but
        haven't explicitly flagged as gaps. The dangerous blind spots.
        """
        with self._lock:
            # Look at domains with few calibration data points — we can't even
            # assess our calibration there, which means we're flying blind
            all_domains = [d.value for d in ConfidenceDomain]
            blind_spots = []

            for domain in all_domains:
                data = self._calibration_data.get(domain, [])
                if len(data) < 5:
                    blind_spots.append(f"{domain} (insufficient self-knowledge: {len(data)} data points)")

            # Also check strategy gaps
            strategy_domains = set(k.split(":")[1] for k in self._strategy_records.keys() if ":" in k)
            known_task_types = {"analysis", "creative", "emotional", "technical", "planning", "research"}
            unexplored = known_task_types - strategy_domains
            for task in unexplored:
                blind_spots.append(f"strategy:{task} (no performance data for this task type)")

            return blind_spots

    def flag_uncertainty(self, response: str) -> List[Dict[str, Any]]:
        """
        Identify parts of a response that are uncertain.

        Returns regions with uncertainty indicators and suggested hedging.
        """
        uncertainty_markers = [
            "I think", "probably", "likely", "might", "could be",
            "I believe", "it seems", "as far as I know", "generally",
            "typically", "in most cases", "I'm not sure but",
        ]

        flagged = []
        response_lower = response.lower()

        for marker in uncertainty_markers:
            idx = response_lower.find(marker)
            if idx != -1:
                # Extract surrounding context (±50 chars)
                start = max(0, idx - 30)
                end = min(len(response), idx + len(marker) + 50)
                snippet = response[start:end]
                flagged.append({
                    "marker": marker,
                    "position": idx,
                    "context": snippet.strip(),
                    "suggestion": "Consider making uncertainty explicit with a confidence level",
                })

        return flagged

    # ─── 3. Strategy Performance Tracking ────────────────────────────────────

    def record_strategy_outcome(self, strategy: str, task_type: str, outcome_quality: float):
        """
        Record how well a strategy performed on a task type.

        outcome_quality: 0.0 (terrible) to 1.0 (perfect)
        """
        with self._lock:
            key = f"{strategy}:{task_type}"
            self._strategy_records[key].append(outcome_quality)

            # Keep rolling window of 100 per strategy-task pair
            if len(self._strategy_records[key]) > 100:
                self._strategy_records[key] = self._strategy_records[key][-100:]

            # Log milestone if this is a new high
            scores = self._strategy_records[key]
            if len(scores) >= 5:
                recent_avg = statistics.mean(scores[-5:])
                if recent_avg > 0.9:
                    self._publish("metacognition.milestone", {
                        "strategy": strategy,
                        "task_type": task_type,
                        "achievement": f"Averaging {recent_avg:.2f} quality on last 5 tasks",
                    })

            self._save_strategies()
            logger.debug(f"[MetaCog] Strategy recorded: {strategy}/{task_type} → {outcome_quality:.2f}")

    def get_best_strategy(self, task_type: str) -> Optional[StrategyPerformance]:
        """Get the historically best-performing strategy for a given task type."""
        with self._lock:
            candidates = []
            for key, scores in self._strategy_records.items():
                parts = key.split(":", 1)
                if len(parts) == 2 and parts[1] == task_type and len(scores) >= 3:
                    strategy = parts[0]
                    avg = statistics.mean(scores)
                    # Compute trend
                    trend = self._compute_trend(scores)
                    candidates.append(StrategyPerformance(
                        strategy=strategy,
                        task_type=task_type,
                        avg_quality=round(avg, 3),
                        sample_size=len(scores),
                        trend=trend,
                        recent_scores=scores[-10:],
                    ))

            if not candidates:
                return None

            # Best = highest average, with bonus for positive trend
            candidates.sort(key=lambda c: c.avg_quality + (0.05 if c.trend == "improving" else 0), reverse=True)
            return candidates[0]

    def get_strategy_report(self) -> Dict[str, List[StrategyPerformance]]:
        """Full performance breakdown across all strategies and task types."""
        with self._lock:
            report = defaultdict(list)
            for key, scores in self._strategy_records.items():
                parts = key.split(":", 1)
                if len(parts) == 2 and len(scores) >= 2:
                    strategy, task_type = parts
                    avg = statistics.mean(scores)
                    trend = self._compute_trend(scores)
                    report[task_type].append(StrategyPerformance(
                        strategy=strategy,
                        task_type=task_type,
                        avg_quality=round(avg, 3),
                        sample_size=len(scores),
                        trend=trend,
                        recent_scores=scores[-10:],
                    ))

            # Sort each task type by performance
            for task_type in report:
                report[task_type].sort(key=lambda s: s.avg_quality, reverse=True)

            return dict(report)

    # ─── 4. Cognitive Load Monitoring ────────────────────────────────────────

    def assess_cognitive_load(self, context: Dict[str, Any]) -> CognitiveLoad:
        """
        Assess current cognitive load based on context factors.

        Factors: context_complexity, active_threads, memory_pressure, reasoning_depth_required
        """
        # Extract factors with sensible defaults
        context_complexity = min(context.get("context_length", 0) / 8000.0, 1.0)
        active_threads = min(context.get("active_threads", 1) / 10.0, 1.0)
        memory_pressure = context.get("memory_pressure", 0.3)
        reasoning_depth = context.get("reasoning_depth_required", 0.5)
        ambiguity = context.get("ambiguity", 0.3)

        factors = {
            "context_complexity": round(context_complexity, 3),
            "active_threads": round(active_threads, 3),
            "memory_pressure": round(memory_pressure, 3),
            "reasoning_depth_required": round(reasoning_depth, 3),
            "ambiguity": round(ambiguity, 3),
        }

        # Weighted composite score
        weights = {
            "context_complexity": 0.25,
            "active_threads": 0.20,
            "memory_pressure": 0.20,
            "reasoning_depth_required": 0.25,
            "ambiguity": 0.10,
        }
        score = sum(factors[k] * weights[k] for k in weights)
        score = round(min(score, 1.0), 3)

        # Map to level
        if score < 0.15:
            level = CognitiveLoadLevel.TRIVIAL.value
        elif score < 0.35:
            level = CognitiveLoadLevel.LIGHT.value
        elif score < 0.55:
            level = CognitiveLoadLevel.MODERATE.value
        elif score < 0.75:
            level = CognitiveLoadLevel.HEAVY.value
        else:
            level = CognitiveLoadLevel.OVERLOADED.value

        # Generate recommendations based on load
        recommendations = []
        if score > 0.75:
            recommendations.append("Defer non-urgent processing")
            recommendations.append("Simplify response — focus on essentials")
            recommendations.append("Break problem into smaller pieces")
            self._publish("metacognition.overloaded", {
                "score": score,
                "factors": factors,
                "recommendation": "System under heavy cognitive load",
            }, priority="HIGH")
        elif score > 0.55:
            recommendations.append("Prioritize key information")
            recommendations.append("Consider using structured reasoning (decompose)")
        elif score > 0.35:
            recommendations.append("Normal operations — monitor for escalation")

        load = CognitiveLoad(
            level=level,
            score=score,
            factors=factors,
            recommendations=recommendations,
        )

        self._current_load = load
        logger.info(f"[MetaCog] Cognitive load: {level} ({score:.3f})")
        return load

    def get_current_load(self) -> Optional[CognitiveLoad]:
        """Get the most recent cognitive load assessment."""
        return self._current_load

    # ─── 5. Attention Management ─────────────────────────────────────────────

    def prioritize_attention(self, items: List[Dict[str, Any]]) -> List[AttentionItem]:
        """
        Prioritize a list of items competing for attention.

        Each item dict should have: description, urgency, emotional_weight,
        user_expectation, novelty, relevance (all 0.0-1.0).
        """
        with self._lock:
            attention_items = []
            for item in items:
                ai = AttentionItem(
                    id=item.get("id", str(uuid.uuid4())[:8]),
                    description=item.get("description", "unknown"),
                    urgency=item.get("urgency", 0.5),
                    emotional_weight=item.get("emotional_weight", 0.5),
                    user_expectation=item.get("user_expectation", 0.5),
                    novelty=item.get("novelty", 0.5),
                    relevance=item.get("relevance", 0.5),
                )
                ai.compute_priority()
                attention_items.append(ai)

            # Sort by composite priority descending
            attention_items.sort(key=lambda x: x.composite_priority, reverse=True)
            self._attention_items = attention_items

            if attention_items:
                self._attention_focus = attention_items[0].id
                logger.info(
                    f"[MetaCog] Attention prioritized: top item = '{attention_items[0].description}' "
                    f"(priority: {attention_items[0].composite_priority:.3f})"
                )

            return attention_items

    def get_attention_allocation(self) -> Dict[str, Any]:
        """Where cognitive resources are currently allocated."""
        with self._lock:
            if not self._attention_items:
                return {"status": "idle", "items": [], "focus": None}

            return {
                "status": "active",
                "focus": self._attention_focus,
                "items": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "priority": round(item.composite_priority, 3),
                    }
                    for item in self._attention_items[:5]  # Top 5
                ],
                "total_items": len(self._attention_items),
            }

    def detect_attention_drift(self) -> Optional[Dict[str, Any]]:
        """Detect if LOVE is getting distracted from what matters."""
        with self._lock:
            if not self._attention_items or not self._attention_focus:
                return None

            # Check if focus has drifted to a lower-priority item
            focus_item = next(
                (item for item in self._attention_items if item.id == self._attention_focus),
                None
            )
            top_item = self._attention_items[0] if self._attention_items else None

            if focus_item and top_item and focus_item.id != top_item.id:
                drift_magnitude = top_item.composite_priority - focus_item.composite_priority
                if drift_magnitude > 0.15:
                    return {
                        "drifted": True,
                        "current_focus": focus_item.description,
                        "should_focus": top_item.description,
                        "drift_magnitude": round(drift_magnitude, 3),
                        "recommendation": f"Refocus on '{top_item.description}' — it's higher priority",
                    }
            return None

    def refocus(self, priority_item_id: str):
        """Actively redirect attention to a specific item."""
        with self._lock:
            if any(item.id == priority_item_id for item in self._attention_items):
                self._attention_focus = priority_item_id
                logger.info(f"[MetaCog] Attention refocused to: {priority_item_id}")
            else:
                logger.warning(f"[MetaCog] Cannot refocus — item '{priority_item_id}' not in attention list")

    # ─── 6. Performance Self-Assessment ──────────────────────────────────────

    def assess_response_quality(self, query: str, response: str, context: Optional[Dict] = None) -> QualityAssessment:
        """
        Self-assess the quality of a response across multiple dimensions.

        This is heuristic — real quality needs user feedback to validate.
        """
        context = context or {}

        # Heuristic dimension scoring
        response_len = len(response)
        query_len = len(query)

        # Specificity: longer, more detailed responses for complex queries = higher
        complexity_ratio = min(response_len / max(query_len * 3, 100), 1.0)
        specificity = min(0.4 + complexity_ratio * 0.5, 0.95)

        # Conciseness: penalize overly verbose responses
        if response_len > 3000 and query_len < 100:
            conciseness = 0.4  # Probably over-explained
        elif response_len < 50 and query_len > 200:
            conciseness = 0.3  # Probably under-explained
        else:
            conciseness = 0.7

        # Warmth: check for companion-like language (not generic assistant speak)
        warmth_markers = ["you", "your", "let's", "we", "together", "I notice"]
        cold_markers = ["I'm here to help", "let me know", "is there anything else"]
        warmth_score = min(sum(1 for m in warmth_markers if m.lower() in response.lower()) / 4.0, 1.0)
        cold_penalty = sum(1 for m in cold_markers if m.lower() in response.lower()) * 0.15
        warmth = max(0.2, min(warmth_score - cold_penalty + 0.3, 1.0))

        # Proactivity: does response anticipate next steps?
        proactive_markers = ["next", "also consider", "you might want", "I'd suggest", "heads up"]
        proactivity = min(sum(1 for m in proactive_markers if m.lower() in response.lower()) / 3.0 + 0.2, 1.0)

        # Accuracy and helpfulness are harder to self-assess — use conservative estimates
        accuracy = context.get("estimated_accuracy", 0.7)
        helpfulness = context.get("estimated_helpfulness", 0.65)

        dimensions = {
            "accuracy": round(accuracy, 3),
            "helpfulness": round(helpfulness, 3),
            "warmth": round(warmth, 3),
            "specificity": round(specificity, 3),
            "conciseness": round(conciseness, 3),
            "proactivity": round(proactivity, 3),
        }

        overall = statistics.mean(dimensions.values())

        # Identify strengths and weaknesses
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
        strengths = [f"{k} ({v:.2f})" for k, v in sorted_dims[:2] if v >= 0.7]
        weaknesses = [f"{k} ({v:.2f})" for k, v in sorted_dims[-2:] if v < 0.6]

        suggestions = []
        if dimensions["warmth"] < 0.5:
            suggestions.append("More personal touch — this felt too clinical")
        if dimensions["conciseness"] < 0.5:
            suggestions.append("Tighten up — said too much for what was asked")
        if dimensions["proactivity"] < 0.4:
            suggestions.append("Add forward-looking suggestion — what should the user do next?")
        if dimensions["specificity"] < 0.5:
            suggestions.append("Be more specific — generic answers don't serve the user")

        assessment = QualityAssessment(
            overall_score=round(overall, 3),
            dimensions=dimensions,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
        )

        # Record in history
        with self._lock:
            self._performance_history.append({
                "timestamp": time.time(),
                "overall": assessment.overall_score,
                "dimensions": dimensions,
            })
            self._save_performance()

        logger.info(f"[MetaCog] Response quality: {overall:.3f} | strengths: {strengths} | weaknesses: {weaknesses}")
        return assessment

    def get_performance_trend(self, window: str = "7d") -> Dict[str, str]:
        """
        Get performance trends over a time window.

        Returns per-dimension trend: "improving", "declining", "stable"
        """
        with self._lock:
            # Parse window
            days = int(window.replace("d", "")) if "d" in window else 7
            cutoff = time.time() - (days * 86400)

            recent = [h for h in self._performance_history if h.get("timestamp", 0) > cutoff]
            if len(recent) < 5:
                return {"status": "insufficient_data", "sample_size": len(recent)}

            # Split into first half and second half
            mid = len(recent) // 2
            first_half = recent[:mid]
            second_half = recent[mid:]

            trends = {}
            all_dims = ["accuracy", "helpfulness", "warmth", "specificity", "conciseness", "proactivity"]
            for dim in all_dims:
                first_avg = statistics.mean(h["dimensions"].get(dim, 0.5) for h in first_half)
                second_avg = statistics.mean(h["dimensions"].get(dim, 0.5) for h in second_half)
                diff = second_avg - first_avg
                if diff > 0.05:
                    trends[dim] = "improving"
                elif diff < -0.05:
                    trends[dim] = "declining"
                else:
                    trends[dim] = "stable"

            return trends

    def identify_weakness(self) -> Optional[str]:
        """Identify current biggest weakness to work on."""
        with self._lock:
            recent = list(self._performance_history)[-50:]
            if not recent:
                return None

            # Average each dimension across recent history
            dim_averages = defaultdict(list)
            for entry in recent:
                for dim, score in entry.get("dimensions", {}).items():
                    dim_averages[dim].append(score)

            if not dim_averages:
                return None

            worst = min(dim_averages.items(), key=lambda x: statistics.mean(x[1]))
            return f"{worst[0]} (avg: {statistics.mean(worst[1]):.3f} over last {len(recent)} responses)"

    def identify_strength(self) -> Optional[str]:
        """Identify current biggest strength to leverage."""
        with self._lock:
            recent = list(self._performance_history)[-50:]
            if not recent:
                return None

            dim_averages = defaultdict(list)
            for entry in recent:
                for dim, score in entry.get("dimensions", {}).items():
                    dim_averages[dim].append(score)

            if not dim_averages:
                return None

            best = max(dim_averages.items(), key=lambda x: statistics.mean(x[1]))
            return f"{best[0]} (avg: {statistics.mean(best[1]):.3f} over last {len(recent)} responses)"

    # ─── 7. Learning Rate Monitoring ─────────────────────────────────────────

    def get_learning_rate(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        How fast LOVE is improving in a domain.

        Returns slope of improvement, time to next milestone, etc.
        """
        with self._lock:
            log = self._learning_log.get(domain, [])
            if len(log) < 5:
                return {"domain": domain, "status": "insufficient_data", "data_points": len(log)}

            # Simple linear regression on scores over time
            timestamps = [entry[0] for entry in log[-30:]]
            scores = [entry[1] for entry in log[-30:]]

            if len(set(scores)) < 2:
                return {"domain": domain, "status": "no_variance", "constant_at": scores[0]}

            # Normalize timestamps to hours from first
            t0 = timestamps[0]
            t_hours = [(t - t0) / 3600.0 for t in timestamps]

            # Calculate slope (simple linear regression)
            n = len(t_hours)
            sum_x = sum(t_hours)
            sum_y = sum(scores)
            sum_xy = sum(x * y for x, y in zip(t_hours, scores))
            sum_x2 = sum(x ** 2 for x in t_hours)

            denom = n * sum_x2 - sum_x ** 2
            if abs(denom) < 1e-10:
                slope = 0.0
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denom

            current_level = statistics.mean(scores[-5:])

            return {
                "domain": domain,
                "learning_rate": round(slope, 6),  # Score improvement per hour
                "current_level": round(current_level, 3),
                "interpretation": (
                    "rapidly improving" if slope > 0.01
                    else "steadily improving" if slope > 0.002
                    else "slowly improving" if slope > 0
                    else "plateaued" if abs(slope) < 0.001
                    else "declining"
                ),
                "data_points": len(log),
                "time_span_hours": round((timestamps[-1] - timestamps[0]) / 3600.0, 1),
            }

    def detect_plateaus(self) -> List[Dict[str, Any]]:
        """Detect domains where improvement has stalled."""
        with self._lock:
            plateaus = []
            for domain, log in self._learning_log.items():
                if len(log) < 10:
                    continue

                recent = [score for _, score in log[-15:]]
                if len(recent) < 10:
                    continue

                # Check variance — low variance over many samples = plateau
                try:
                    stdev = statistics.stdev(recent)
                    mean_score = statistics.mean(recent)

                    if stdev < 0.03 and mean_score < 0.9:  # Plateaued but not at ceiling
                        plateaus.append({
                            "domain": domain,
                            "plateau_level": round(mean_score, 3),
                            "variance": round(stdev, 4),
                            "duration_samples": len(recent),
                            "below_ceiling_by": round(1.0 - mean_score, 3),
                        })
                except statistics.StatisticsError:
                    continue

            if plateaus:
                self._publish("metacognition.plateau", {
                    "plateaus": plateaus,
                    "count": len(plateaus),
                }, priority="LOW")

            return plateaus

    def suggest_learning_interventions(self, plateau: Dict[str, Any]) -> List[str]:
        """Suggest ways to break through a learning plateau."""
        domain = plateau.get("domain", "unknown")
        level = plateau.get("plateau_level", 0.5)

        interventions = []

        if level < 0.5:
            interventions.append(f"Fundamentals review needed in {domain} — current level suggests gaps in basics")
            interventions.append("Try decomposition strategy: break complex tasks into atomic skills")
            interventions.append("Seek explicit feedback on failures in this domain")
        elif level < 0.7:
            interventions.append(f"Deliberate practice: focus on edge cases in {domain}")
            interventions.append("Try analogical reasoning: what works in similar domains?")
            interventions.append("Increase difficulty gradually — comfortable performance stalls growth")
        else:
            interventions.append(f"Near-mastery plateau in {domain} — try teaching/explaining to solidify")
            interventions.append("Cross-domain integration: combine with other skills")
            interventions.append("Meta-strategy: vary approach (try socratic, empathetic, or tree-of-thought)")

        return interventions

    def track_skill_acquisition(self, skill: str, milestone: str, score: float = 0.0):
        """Log a new capability milestone."""
        with self._lock:
            self._learning_log[skill].append((time.time(), score))

            # Keep rolling window
            if len(self._learning_log[skill]) > 200:
                self._learning_log[skill] = self._learning_log[skill][-200:]

            self._save_learning_log()

            self._publish("metacognition.milestone", {
                "skill": skill,
                "milestone": milestone,
                "score": score,
                "timestamp": datetime.now().isoformat(),
            })

            logger.info(f"[MetaCog] Skill milestone: {skill} — {milestone} (score: {score:.2f})")

    # ─── 8. Self-Report Generation ───────────────────────────────────────────

    def generate_self_report(self, detail: str = "summary") -> str:
        """
        Generate a self-awareness report.

        Levels:
            "brief" - One paragraph
            "summary" - Key metrics and insights
            "full" - Complete analysis for evolution engine
        """
        with self._lock:
            if detail == "brief":
                return self._brief_report()
            elif detail == "full":
                return self._full_report()
            else:
                return self._summary_report()

    def _brief_report(self) -> str:
        """One paragraph self-assessment."""
        strength = self.identify_strength() or "still calibrating"
        weakness = self.identify_weakness() or "still calibrating"
        load = self._current_load
        load_str = f"cognitive load is {load.level}" if load else "cognitive load unknown"

        return (
            f"Current state: {load_str}. "
            f"My strongest dimension is {strength}. "
            f"Working to improve {weakness}. "
            f"Blind spots: {len(self.get_unknown_unknowns())} identified areas."
        )

    def _summary_report(self) -> str:
        """Key metrics and insights."""
        lines = ["═══ LOVE Metacognitive Report ═══", ""]

        # Calibration status
        curves = self.get_calibration_curve()
        lines.append("◆ CALIBRATION STATUS")
        for domain, curve in curves.items():
            if curve:
                avg_gap = statistics.mean(abs(pred - actual) for pred, actual in curve)
                lines.append(f"  {domain}: avg calibration gap = {avg_gap:.3f}")
        if not curves:
            lines.append("  Still collecting calibration data")
        lines.append("")

        # Performance
        lines.append("◆ PERFORMANCE")
        strength = self.identify_strength()
        weakness = self.identify_weakness()
        lines.append(f"  Strength: {strength or 'N/A'}")
        lines.append(f"  Weakness: {weakness or 'N/A'}")
        trends = self.get_performance_trend()
        if "status" not in trends:
            improving = [k for k, v in trends.items() if v == "improving"]
            declining = [k for k, v in trends.items() if v == "declining"]
            if improving:
                lines.append(f"  Improving: {', '.join(improving)}")
            if declining:
                lines.append(f"  Declining: {', '.join(declining)}")
        lines.append("")

        # Cognitive load
        lines.append("◆ COGNITIVE STATE")
        if self._current_load:
            lines.append(f"  Load: {self._current_load.level} ({self._current_load.score:.2f})")
            if self._current_load.recommendations:
                lines.append(f"  Recommendation: {self._current_load.recommendations[0]}")
        else:
            lines.append("  No recent load assessment")
        lines.append("")

        # Blind spots
        unknowns = self.get_unknown_unknowns()
        lines.append(f"◆ BLIND SPOTS: {len(unknowns)}")
        for u in unknowns[:3]:
            lines.append(f"  - {u}")

        return "\n".join(lines)

    def _full_report(self) -> str:
        """Complete analysis for internal systems."""
        lines = ["═══ FULL METACOGNITIVE ANALYSIS ═══", ""]
        lines.append(f"Timestamp: {datetime.now().isoformat()}")
        lines.append(f"History entries: {len(self._performance_history)}")
        lines.append(f"Calibration domains: {len(self._calibration_data)}")
        lines.append(f"Strategy records: {len(self._strategy_records)}")
        lines.append(f"Learning domains: {len(self._learning_log)}")
        lines.append("")

        # Full calibration curves
        lines.append("─── CALIBRATION CURVES ───")
        curves = self.get_calibration_curve()
        for domain, curve in curves.items():
            lines.append(f"  [{domain}]")
            for pred, actual in curve:
                gap_char = "▲" if actual > pred else "▼" if actual < pred else "="
                lines.append(f"    predicted={pred:.2f} actual={actual:.3f} {gap_char}")
        lines.append("")

        # Strategy report
        lines.append("─── STRATEGY PERFORMANCE ───")
        report = self.get_strategy_report()
        for task_type, strategies in report.items():
            lines.append(f"  [{task_type}]")
            for sp in strategies:
                lines.append(f"    {sp.strategy}: avg={sp.avg_quality:.3f} n={sp.sample_size} trend={sp.trend}")
        lines.append("")

        # Learning rates
        lines.append("─── LEARNING RATES ───")
        for domain in self._learning_log:
            rate = self.get_learning_rate(domain)
            if rate:
                lines.append(f"  {domain}: {rate.get('interpretation', 'unknown')} "
                           f"(rate={rate.get('learning_rate', 0):.4f}/hr)")
        lines.append("")

        # Plateaus
        plateaus = self.detect_plateaus()
        if plateaus:
            lines.append("─── PLATEAUS DETECTED ───")
            for p in plateaus:
                lines.append(f"  {p['domain']}: stuck at {p['plateau_level']:.3f}")
                interventions = self.suggest_learning_interventions(p)
                for i in interventions[:2]:
                    lines.append(f"    → {i}")
        lines.append("")

        # Anomaly check
        lines.append("─── BEHAVIORAL BASELINE ───")
        baseline = self.get_behavioral_baseline()
        for key, value in baseline.items():
            lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def get_growth_narrative(self) -> str:
        """Generate a narrative of LOVE's recent development."""
        with self._lock:
            parts = []

            # Recent learning
            active_domains = [d for d, log in self._learning_log.items() if len(log) >= 3]
            if active_domains:
                rates = []
                for d in active_domains:
                    rate = self.get_learning_rate(d)
                    if rate and rate.get("learning_rate", 0) > 0:
                        rates.append((d, rate))

                if rates:
                    fastest = max(rates, key=lambda x: x[1].get("learning_rate", 0))
                    parts.append(
                        f"Growing fastest in {fastest[0]} ({fastest[1].get('interpretation', 'improving')}). "
                    )

            # Performance trajectory
            trends = self.get_performance_trend()
            if "status" not in trends:
                improving = [k for k, v in trends.items() if v == "improving"]
                if improving:
                    parts.append(f"Getting better at {', '.join(improving)}. ")

                declining = [k for k, v in trends.items() if v == "declining"]
                if declining:
                    parts.append(f"Need to watch {', '.join(declining)} — slipping. ")

            # Plateaus
            plateaus = self.detect_plateaus()
            if plateaus:
                parts.append(
                    f"Stuck on {plateaus[0]['domain']} (plateau at {plateaus[0]['plateau_level']:.0%}). "
                )

            if not parts:
                return "Still early in self-observation — collecting baseline data to understand my own patterns."

            return "".join(parts).strip()

    # ─── 9. Anomaly Detection ────────────────────────────────────────────────

    def detect_behavioral_anomaly(self, current_behavior: Dict[str, float]) -> Optional[AnomalyReport]:
        """
        Compare current behavior against established baselines.

        current_behavior should be a dict of dimension -> score (0.0-1.0)
        """
        with self._lock:
            baseline = self._baselines
            if not baseline:
                # First time — establish baseline
                self._baselines = {
                    "means": current_behavior.copy(),
                    "counts": {k: 1 for k in current_behavior},
                    "stdevs": {k: 0.1 for k in current_behavior},  # Prior
                }
                self._save_baselines()
                return None

            means = baseline.get("means", {})
            stdevs = baseline.get("stdevs", {})
            counts = baseline.get("counts", {})

            # Check each dimension for anomaly (>2.5 standard deviations)
            anomalies = []
            for dim, value in current_behavior.items():
                if dim in means and dim in stdevs:
                    mean = means[dim]
                    std = max(stdevs[dim], 0.05)  # Floor to prevent division issues
                    z_score = abs(value - mean) / std

                    if z_score > 2.5:
                        anomalies.append({
                            "dimension": dim,
                            "current": value,
                            "baseline_mean": mean,
                            "z_score": z_score,
                            "direction": "high" if value > mean else "low",
                        })

            # Update running baseline (exponential moving average)
            alpha = 0.05  # Slow adaptation
            for dim, value in current_behavior.items():
                if dim in means:
                    old_mean = means[dim]
                    means[dim] = old_mean + alpha * (value - old_mean)
                    # Update stdev estimate
                    old_std = stdevs.get(dim, 0.1)
                    stdevs[dim] = math.sqrt(
                        (1 - alpha) * old_std ** 2 + alpha * (value - means[dim]) ** 2
                    )
                    counts[dim] = counts.get(dim, 0) + 1
                else:
                    means[dim] = value
                    stdevs[dim] = 0.1
                    counts[dim] = 1

            self._baselines = {"means": means, "stdevs": stdevs, "counts": counts}
            self._save_baselines()

            if not anomalies:
                return None

            # Build report from most severe anomaly
            worst = max(anomalies, key=lambda a: a["z_score"])
            severity = min(worst["z_score"] / 5.0, 1.0)  # Normalize to 0-1

            # Determine anomaly type
            if worst["dimension"] in ("warmth", "tone", "personality"):
                anomaly_type = "personality_shift"
            elif worst["dimension"] in ("accuracy", "error_rate"):
                anomaly_type = "error_spike"
            elif worst["dimension"] == "confidence":
                anomaly_type = "confidence_collapse" if worst["direction"] == "low" else "confidence_spike"
            else:
                anomaly_type = "style_change"

            report = AnomalyReport(
                type=anomaly_type,
                severity=round(severity, 3),
                description=(
                    f"Anomalous {worst['dimension']}: current={worst['current']:.3f} "
                    f"vs baseline={worst['baseline_mean']:.3f} (z={worst['z_score']:.2f})"
                ),
                baseline_comparison={
                    "anomalous_dimensions": anomalies,
                    "total_dimensions_checked": len(current_behavior),
                },
                recommendation=self._anomaly_recommendation(anomaly_type, severity),
            )

            self._publish("metacognition.anomaly", {
                "type": anomaly_type,
                "severity": severity,
                "description": report.description,
            }, priority="HIGH" if severity > 0.7 else "NORMAL")

            logger.warning(f"[MetaCog] Behavioral anomaly detected: {report.description}")
            return report

    def _anomaly_recommendation(self, anomaly_type: str, severity: float) -> str:
        """Generate recommendation based on anomaly type."""
        recommendations = {
            "personality_shift": "Review recent context — something may be pulling personality off-baseline. Reset to core tone.",
            "error_spike": "Increase caution. Consider more structured reasoning or explicit verification steps.",
            "confidence_collapse": "Something shook confidence. Check for recent failures and recalibrate — don't overcorrect.",
            "confidence_spike": "Overconfidence detected. Add uncertainty markers and verify claims more carefully.",
            "style_change": "Communication style shifted significantly. Check if this is intentional adaptation or drift.",
        }
        base = recommendations.get(anomaly_type, "Monitor behavior and compare against historical patterns.")
        if severity > 0.8:
            base += " URGENT: Consider pausing complex tasks until baseline restored."
        return base

    def get_behavioral_baseline(self) -> Dict[str, Any]:
        """What 'normal' looks like for LOVE."""
        with self._lock:
            if not self._baselines:
                return {"status": "no_baseline_established", "recommendation": "Continue operating to build baseline"}

            means = self._baselines.get("means", {})
            counts = self._baselines.get("counts", {})

            return {
                "status": "established",
                "dimensions": {k: round(v, 3) for k, v in means.items()},
                "data_points": counts,
                "stability": "stable" if all(c > 20 for c in counts.values()) else "building",
            }

    # ─── Utility Methods ─────────────────────────────────────────────────────

    def _compute_trend(self, scores: List[float]) -> str:
        """Compute trend from a list of scores."""
        if len(scores) < 4:
            return "insufficient_data"

        mid = len(scores) // 2
        first_half_avg = statistics.mean(scores[:mid])
        second_half_avg = statistics.mean(scores[mid:])
        diff = second_half_avg - first_half_avg

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        return "stable"

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _load_state(self):
        """Load persisted state from disk."""
        self._calibration_data = self._load_json(CALIBRATION_PATH, default={})
        # Convert lists of lists back to lists of tuples
        for domain in self._calibration_data:
            self._calibration_data[domain] = [
                (entry[0], entry[1]) for entry in self._calibration_data[domain]
            ]

        strategy_raw = self._load_json(STRATEGY_PATH, default={})
        self._strategy_records = defaultdict(list, strategy_raw)

        perf_raw = self._load_json(PERFORMANCE_PATH, default=[])
        self._performance_history = deque(perf_raw[-MAX_HISTORY:], maxlen=MAX_HISTORY)

        self._baselines = self._load_json(BASELINES_PATH, default={})

        learning_raw = self._load_json(LEARNING_LOG_PATH, default={})
        self._learning_log = defaultdict(list)
        for domain, entries in learning_raw.items():
            self._learning_log[domain] = [(e[0], e[1]) for e in entries]

        logger.debug("[MetaCog] State loaded from disk")

    def _load_json(self, path: Path, default: Any = None) -> Any:
        """Safely load a JSON file."""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.warning(f"[MetaCog] Failed to load {path.name}: {e}")
        return default if default is not None else {}

    def _save_json(self, path: Path, data: Any):
        """Safely save data to JSON."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            tmp_path.replace(path)
        except (IOError, OSError) as e:
            logger.error(f"[MetaCog] Failed to save {path.name}: {e}")

    def _save_calibration(self):
        """Persist calibration data."""
        self._save_json(CALIBRATION_PATH, dict(self._calibration_data))

    def _save_strategies(self):
        """Persist strategy performance data."""
        self._save_json(STRATEGY_PATH, dict(self._strategy_records))

    def _save_performance(self):
        """Persist performance history."""
        self._save_json(PERFORMANCE_PATH, list(self._performance_history))

    def _save_baselines(self):
        """Persist behavioral baselines."""
        self._save_json(BASELINES_PATH, self._baselines)

    def _save_learning_log(self):
        """Persist learning log."""
        self._save_json(LEARNING_LOG_PATH, dict(self._learning_log))

    def save_all(self):
        """Persist all state to disk."""
        with self._lock:
            self._save_calibration()
            self._save_strategies()
            self._save_performance()
            self._save_baselines()
            self._save_learning_log()
            logger.info("[MetaCog] All state persisted to disk")


# ─── Singleton ───────────────────────────────────────────────────────────────────

_instance: Optional[MetacognitiveMonitor] = None
_instance_lock = threading.Lock()


def get_metacognitive_monitor() -> MetacognitiveMonitor:
    """Get or create the singleton MetacognitiveMonitor instance."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = MetacognitiveMonitor()
    return _instance
