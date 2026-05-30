"""
LOVE Meta-Evolution Engine — Learning How to Learn Better

This is LOVE's meta-learning layer. It doesn't just improve behaviors —
it improves the improvement process itself.

Meta-evolution capabilities:
1. LEARNING EFFICIENCY OPTIMIZATION
   - Tracks which hypothesis generation strategies work best
   - Adapts experiment duration based on effect size detection
   - Optimizes sample size calculations for faster learning

2. PREDICTIVE EVOLUTION
   - Anticipates user needs before they arise
   - Pre-generates hypotheses for likely future scenarios
   - Maintains a "ready queue" of improvements

3. EVOLUTIONARY PRESSURE SYSTEM
   - Aligns evolution with user's life goals and values
   - Prioritizes capabilities that matter most to the user
   - Dynamically adjusts based on changing life circumstances

4. CROSS-DOMAIN SYNTHESIS
   - Detects patterns across different life domains
   - Transfers successful mutations from one domain to another
   - Creates unified hypotheses from multi-domain signals
"""

import json
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "meta_evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

META_STATE_FILE = DATA_DIR / "meta_state.json"
LEARNING_LOG = DATA_DIR / "learning_log.jsonl"
PREDICTION_CACHE = DATA_DIR / "prediction_cache.json"
GOAL_ALIGNMENT_FILE = DATA_DIR / "goal_alignment.json"


@dataclass
class LearningStrategy:
    """A meta-learning strategy for generating hypotheses."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    description: str = ""
    success_rate: float = 0.5
    avg_effect_size: float = 0.0
    usage_count: int = 0
    last_used: str = ""
    domain_effectiveness: Dict[str, float] = field(default_factory=dict)  # domain -> effectiveness


@dataclass
class EvolutionaryPressure:
    """Pressure from user goals that guides evolution priorities."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    goal_area: str = ""  # health, career, relationships, finance, creativity
    pressure_level: float = 0.5  # 0-1: how much this area needs attention
    priority: float = 0.5  # 0-1: relative importance to user
    trend: str = "stable"  # increasing, stable, decreasing
    evidence: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PredictiveHypothesis:
    """A pre-generated hypothesis for a likely future scenario."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    trigger_scenario: str = ""  # when this should be activated
    hypothesis: str = ""
    proposed_change: str = ""
    expected_impact: str = ""
    confidence: float = 0.5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    activated: bool = False
    activation_time: Optional[str] = None


@dataclass
class CrossDomainPattern:
    """A pattern detected across multiple life domains."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    domains: List[str] = field(default_factory=list)
    pattern_description: str = ""
    strength: float = 0.5
    first_detected: str = field(default_factory=lambda: datetime.now().isoformat())
    confirmed_count: int = 0
    transfer_hypotheses: List[str] = field(default_factory=list)  # hypothesis IDs


class MetaEvolutionEngine:
    """
    LOVE's meta-learning layer — improves the improvement process.
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
        self._strategies: Dict[str, LearningStrategy] = {}
        self._pressures: Dict[str, EvolutionaryPressure] = {}
        self._predictions: List[PredictiveHypothesis] = []
        self._cross_domain_patterns: Dict[str, CrossDomainPattern] = {}
        self._learning_history: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_state()
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        try:
            if META_STATE_FILE.exists():
                data = json.loads(META_STATE_FILE.read_text())
                for sid, sd in data.get("strategies", {}).items():
                    self._strategies[sid] = LearningStrategy(**sd)
                for pid, pd in data.get("pressures", {}).items():
                    self._pressures[pid] = EvolutionaryPressure(**pd)
                for cd in data.get("predictions", []):
                    self._predictions.append(PredictiveHypothesis(**cd))
                for cid, cpd in data.get("cross_domain_patterns", {}).items():
                    self._cross_domain_patterns[cid] = CrossDomainPattern(**cpd)
        except Exception as e:
            print(f"[MetaEvolution] Load error: {e}")
    
    def _save_state(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "strategies": {sid: asdict(s) for sid, s in self._strategies.items()},
                "pressures": {pid: asdict(p) for pid, p in self._pressures.items()},
                "predictions": [asdict(p) for p in self._predictions],
                "cross_domain_patterns": {cid: asdict(c) for cid, c in self._cross_domain_patterns.items()},
            }
            META_STATE_FILE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[MetaEvolution] Save error: {e}")
    
    def _log_learning(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        self._learning_history.append(event)
        try:
            with open(LEARNING_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
    
    # ── Meta-Learning: Strategy Optimization ───────────────────────────────────────
    
    def initialize_strategies(self):
        """Initialize the default set of learning strategies."""
        if self._strategies:
            return
        
        default_strategies = [
            LearningStrategy(
                name="correction_based",
                description="Generate hypotheses from user correction patterns",
                success_rate=0.6,
                domain_effectiveness={"factual_accuracy": 0.7, "context_usage": 0.5}
            ),
            LearningStrategy(
                name="initiative_feedback",
                description="Learn from proactive initiative response rates",
                success_rate=0.5,
                domain_effectiveness={"initiative_timing": 0.8, "proactive_rate": 0.6}
            ),
            LearningStrategy(
                name="satisfaction_decay",
                description="Detect and address satisfaction drop patterns",
                success_rate=0.55,
                domain_effectiveness={"emotional_support": 0.6, "engagement": 0.5}
            ),
            LearningStrategy(
                name="cross_domain_synthesis",
                description="Combine insights from multiple life domains",
                success_rate=0.65,
                domain_effectiveness={"holistic_intelligence": 0.8, "pattern_recognition": 0.7}
            ),
            LearningStrategy(
                name="goal_pressure_alignment",
                description="Align improvements with user's life goals",
                success_rate=0.7,
                domain_effectiveness={"goal_achievement": 0.9, "prioritization": 0.7}
            ),
            LearningStrategy(
                name="modern_module_optimization",
                description="Optimize modern AI module parameters from usage feedback",
                success_rate=0.65,
                domain_effectiveness={
                    "llm_routing": 0.8, "memory_search": 0.7, "prompt_tuning": 0.9,
                    "context_optimization": 0.8, "cache_efficiency": 0.7,
                    "pattern_detection": 0.8, "emotion_analysis": 0.6,
                }
            ),
            LearningStrategy(
                name="cross_modal_learning",
                description="Transfer insights between text, visual, and voice modalities",
                success_rate=0.6,
                domain_effectiveness={
                    "multimodal_fusion": 0.9, "conversation_quality": 0.7,
                    "personality_adaptation": 0.8,
                }
            ),
        ]
        
        for strategy in default_strategies:
            self._strategies[strategy.id] = strategy
        
        self._save_state()
        print(f"[MetaEvolution] Initialized {len(default_strategies)} learning strategies")
    
    def record_strategy_outcome(self, strategy_id: str, success: bool, effect_size: float, domain: str = ""):
        """Record the outcome of using a learning strategy."""
        if strategy_id not in self._strategies:
            return
        
        strategy = self._strategies[strategy_id]
        strategy.usage_count += 1
        strategy.last_used = datetime.now().isoformat()
        
        # Update success rate with exponential smoothing
        alpha = 0.1
        strategy.success_rate = (alpha * (1.0 if success else 0.0) + 
                                (1 - alpha) * strategy.success_rate)
        
        # Update average effect size
        strategy.avg_effect_size = (alpha * effect_size + 
                                   (1 - alpha) * strategy.avg_effect_size)
        
        # Update domain-specific effectiveness
        if domain:
            if domain not in strategy.domain_effectiveness:
                strategy.domain_effectiveness[domain] = 0.5
            strategy.domain_effectiveness[domain] = (
                alpha * (1.0 if success else 0.0) + 
                (1 - alpha) * strategy.domain_effectiveness[domain]
            )
        
        self._log_learning({
            "event": "strategy_outcome",
            "strategy_id": strategy_id,
            "success": success,
            "effect_size": effect_size,
            "domain": domain,
            "updated_success_rate": strategy.success_rate,
        })
        
        self._save_state()
    
    def get_best_strategy(self, domain: str = "") -> Optional[LearningStrategy]:
        """Get the best learning strategy for a given domain."""
        if not self._strategies:
            self.initialize_strategies()
        
        if domain:
            # Find strategy with highest domain-specific effectiveness
            domain_strategies = [
                (s, s.domain_effectiveness.get(domain, 0.5))
                for s in self._strategies.values()
            ]
            if domain_strategies:
                best = max(domain_strategies, key=lambda x: x[1])
                if best[1] > 0.5:  # Only return if above baseline
                    return best[0]
        
        # Fallback to overall best strategy
        return max(self._strategies.values(), key=lambda s: s.success_rate)
    
    # ── Evolutionary Pressure System ───────────────────────────────────────────────
    
    def update_evolutionary_pressures(self):
        """Analyze user's life state and update evolutionary pressures."""
        pressures = {}
        has_any_data = False
        try:
            try:
                from agents.task_agent import get_task_overview
                if get_task_overview is not None:
                    tasks = get_task_overview()
                    overdue = tasks.get("overdue_count", 0)
                    due_soon = len(tasks.get("due_soon", []))
                    if overdue > 0 or due_soon > 0:
                        pressures["career"] = min(1.0, (overdue * 0.3 + due_soon * 0.1))
                        has_any_data = True
            except Exception:
                pass

            try:
                from agents.fitness_agent import get_fitness_overview
                if get_fitness_overview is not None:
                    fitness = get_fitness_overview()
                    activity_level = fitness.get("recent_activity_level")
                    if activity_level is not None:
                        pressures["health"] = 1.0 - activity_level
                        has_any_data = True
            except Exception:
                pass

            try:
                from integrations.finance_intelligence import get_finance_intelligence
                if get_finance_intelligence is not None:
                    fi = get_finance_intelligence()
                    alerts = fi.get_alerts(5)
                    if alerts:
                        pressures["finance"] = min(1.0, len(alerts) * 0.2)
                        has_any_data = True
            except Exception:
                pass

            try:
                from core.autonomous import get_relationship_state
                if get_relationship_state is not None:
                    rel_state = get_relationship_state()
                    freq = rel_state.get("interaction_frequency")
                    if freq is not None:
                        try:
                            pressures["relationships"] = 1.0 - float(freq)
                            has_any_data = True
                        except (ValueError, TypeError):
                            pass
            except Exception:
                pass

            if not has_any_data:
                return pressures

            # Update or create pressure objects only from real data
            for area, level in pressures.items():
                pressure_id = f"pressure_{area}"
                if pressure_id not in self._pressures:
                    self._pressures[pressure_id] = EvolutionaryPressure(
                        goal_area=area,
                        pressure_level=level,
                        priority=0.5,
                    )
                else:
                    old_level = self._pressures[pressure_id].pressure_level
                    if level > old_level + 0.1:
                        self._pressures[pressure_id].trend = "increasing"
                    elif level < old_level - 0.1:
                        self._pressures[pressure_id].trend = "decreasing"
                    else:
                        self._pressures[pressure_id].trend = "stable"
                    self._pressures[pressure_id].pressure_level = level
                    self._pressures[pressure_id].last_updated = datetime.now().isoformat()

            self._save_state()
            return pressures
        except Exception:
            return pressures

    def get_evolutionary_priorities(self) -> List[Tuple[str, float]]:
        """Get ordered list of evolution priorities based on pressures."""
        if not self._pressures:
            self.update_evolutionary_pressures()

        # Calculate priority score = pressure_level * priority_weight
        scored = [
            (p.goal_area, p.pressure_level * p.priority)
            for p in self._pressures.values()
        ]
        return sorted(scored, key=lambda x: x[1], reverse=True)
    
    # ── Predictive Evolution ─────────────────────────────────────────────────────
    
    def generate_predictive_hypotheses(self):
        """Pre-generate hypotheses for likely future scenarios."""
        try:
            llm = get_reasoning_llm()
            
            # Get current context
            priorities = self.get_evolutionary_priorities()
            priority_areas = [area for area, _ in priorities[:3]]
            
            prompt = f"""You are LOVE's predictive evolution engine. 
Generate 3-5 hypotheses for likely future scenarios based on current state.

Current high-priority areas: {', '.join(priority_areas)}

For each hypothesis, provide:
1. trigger_scenario: When this should be activated (e.g., "user has 3+ overdue tasks", "market drops 10%")
2. hypothesis: What LOVE should try to improve
3. proposed_change: Specific behavioral change
4. expected_impact: What improvement is expected
5. confidence: 0.0-1.0 how confident you are

Return as JSON array with these exact fields."""
            
            response = llm.invoke(prompt)
            
            # Parse response
            try:
                hypotheses_data = json.loads(response)
                for hd in hypotheses_data:
                    pred = PredictiveHypothesis(
                        trigger_scenario=hd.get("trigger_scenario", ""),
                        hypothesis=hd.get("hypothesis", ""),
                        proposed_change=hd.get("proposed_change", ""),
                        expected_impact=hd.get("expected_impact", ""),
                        confidence=hd.get("confidence", 0.5),
                    )
                    self._predictions.append(pred)
                
                self._save_state()
                self._log_learning({
                    "event": "predictive_hypotheses_generated",
                    "count": len(hypotheses_data),
                })
                
                print(f"[MetaEvolution] Generated {len(hypotheses_data)} predictive hypotheses")
                
            except json.JSONDecodeError:
                print("[MetaEvolution] Failed to parse predictive hypotheses")
                
        except Exception as e:
            print(f"[MetaEvolution] Predictive generation error: {e}")
    
    def check_predictive_triggers(self, current_state: Dict) -> List[PredictiveHypothesis]:
        """Check if any predictive hypotheses should be activated."""
        activated = []
        
        for pred in self._predictions:
            if pred.activated:
                continue
            
            # Simple trigger matching (can be enhanced with NLP)
            trigger = pred.trigger_scenario.lower()
            
            # Check against current state
            should_activate = False
            
            if "overdue" in trigger and current_state.get("overdue_count", 0) >= 3:
                should_activate = True
            elif "market" in trigger and current_state.get("market_change", 0) < -0.1:
                should_activate = True
            elif "deadline" in trigger and current_state.get("upcoming_deadline_hours", 999) < 24:
                should_activate = True
            
            if should_activate:
                pred.activated = True
                pred.activation_time = datetime.now().isoformat()
                activated.append(pred)
        
        if activated:
            self._save_state()
        
        return activated
    
    # ── Cross-Domain Synthesis ─────────────────────────────────────────────────────
    
    def detect_cross_domain_patterns(self):
        """Detect patterns that span multiple life domains."""
        try:
            from core.intelligence_hub import IntelligenceHub
            from core.memory import recall_memory
            
            hub = IntelligenceHub.get_instance()
            snapshot = hub.get_snapshot()
            
            patterns = []
            
            # Pattern: Work stress + poor sleep + low activity
            work_stress = snapshot.get("career", {}).get("stress_level", 0) > 0.7
            poor_sleep = snapshot.get("health", {}).get("sleep_quality", 0.5) < 0.5
            low_activity = snapshot.get("health", {}).get("activity_level", 0.5) < 0.4
            
            if work_stress and poor_sleep and low_activity:
                pattern_id = "stress_sleep_activity_cycle"
                if pattern_id not in self._cross_domain_patterns:
                    self._cross_domain_patterns[pattern_id] = CrossDomainPattern(
                        domains=["career", "health", "fitness"],
                        pattern_description="High work stress correlates with poor sleep and low activity",
                        strength=0.8,
                    )
                    patterns.append(self._cross_domain_patterns[pattern_id])
            
            # Pattern: Financial stress + work distraction + task delays
            financial_stress = len(snapshot.get("finance", {}).get("alerts", [])) > 2
            work_distraction = snapshot.get("system", {}).get("focus_depth", 1.0) < 0.5
            task_delays = snapshot.get("career", {}).get("overdue_count", 0) > 2
            
            if financial_stress and work_distraction and task_delays:
                pattern_id = "finance_work_delay_cycle"
                if pattern_id not in self._cross_domain_patterns:
                    self._cross_domain_patterns[pattern_id] = CrossDomainPattern(
                        domains=["finance", "career", "productivity"],
                        pattern_description="Financial stress correlates with work distraction and task delays",
                        strength=0.7,
                    )
                    patterns.append(self._cross_domain_patterns[pattern_id])
            
            if patterns:
                self._save_state()
                self._log_learning({
                    "event": "cross_domain_patterns_detected",
                    "count": len(patterns),
                })
                
                # Generate transfer hypotheses
                self._generate_transfer_hypotheses(patterns)
            
        except Exception as e:
            print(f"[MetaEvolution] Cross-domain pattern detection error: {e}")
    
    def _generate_transfer_hypotheses(self, patterns: List[CrossDomainPattern]):
        """Generate hypotheses based on cross-domain patterns."""
        try:
            llm = get_reasoning_llm()
            
            for pattern in patterns:
                prompt = f"""Based on this cross-domain pattern:
Domains: {', '.join(pattern.domains)}
Pattern: {pattern.pattern_description}
Strength: {pattern.strength}

Generate 2-3 transfer hypotheses — improvements that worked in one domain
that should be applied to another domain in this pattern.

Return as JSON array with: source_domain, target_domain, hypothesis, proposed_change"""
                
                response = llm.invoke(prompt)
                
                try:
                    hypotheses = json.loads(response)
                    for h in hypotheses:
                        # This would integrate with the main evolution engine
                        self._log_learning({
                            "event": "transfer_hypothesis_generated",
                            "pattern_id": pattern.id,
                            "hypothesis": h,
                        })
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"[MetaEvolution] Transfer hypothesis generation error: {e}")
    
    # ── Main Loop ─────────────────────────────────────────────────────────────────
    
    def start(self):
        """Start the meta-evolution background loop."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-MetaEvolution"
        )
        self._thread.start()
        print("[MetaEvolution] Started — meta-learning active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(120)  # Let other systems initialize
        
        while self._running:
            try:
                # Update evolutionary pressures
                self.update_evolutionary_pressures()
                
                # Generate predictive hypotheses (less frequently)
                if len(self._predictions) < 10:
                    self.generate_predictive_hypotheses()
                
                # Detect cross-domain patterns
                self.detect_cross_domain_patterns()
                
                # ── APPLY BEST STRATEGIES ──
                try:
                    priorities = self.get_evolutionary_priorities()
                    for domain, _ in priorities[:2]:
                        best = self.get_best_strategy(domain=domain)
                        if best and best.success_rate > 0.5:
                            from core.evolution_engine import EvolutionEngine
                            engine = EvolutionEngine()
                            hypothesis = engine.create_hypothesis(
                                claim=f"Apply {best.name} strategy to improve {domain}",
                                rationale=f"Meta-evolution detected {domain} as high-pressure. Strategy {best.name} has {best.success_rate:.0%} success rate.",
                                target_metric=domain,
                                predicted_delta=0.1,
                            )
                            print(f"[MetaEvolution] Applied strategy '{best.name}' to '{domain}' -> hypothesis {hypothesis.id}")
                            try:
                                from core.master_orchestrator import get_orchestration_master
                                om = get_orchestration_master()
                                om._narrate("meta_evolution", f"Applied strategy '{best.name}' to {domain} (success: {best.success_rate:.0%})", "action")
                            except Exception:
                                pass
                except Exception as e:
                    print(f"[MetaEvolution] Strategy application error: {e}")
                
            except Exception as e:
                print(f"[MetaEvolution] Loop error: {e}")
            
            time.sleep(600)  # Run every 10 minutes


# ── Singleton Access ─────────────────────────────────────────────────────────────

_meta_evolution_instance: Optional[MetaEvolutionEngine] = None
_meta_lock = threading.Lock()


def get_meta_evolution() -> MetaEvolutionEngine:
    global _meta_evolution_instance
    with _meta_lock:
        if _meta_evolution_instance is None:
            _meta_evolution_instance = MetaEvolutionEngine()
        return _meta_evolution_instance