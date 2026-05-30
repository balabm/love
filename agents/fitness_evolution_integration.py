"""
Evolution Integration for Fitness Agent

This module adds evolution capabilities to the fitness agent:
1. EVOLUTION-AWARE FITNESS TRACKING
   - Fitness patterns inform evolution
   - Workout effectiveness guides hypotheses
   - Health metrics set evolutionary pressures

2. ADAPTIVE WORKOUT RECOMMENDATIONS
   - Learns from user workout patterns
   - Evolves recommendation strategies
   - Adapts to fitness progress

3. PERFORMANCE TRACKING
   - Tracks workout consistency
   - Measures goal achievement
   - Identifies fitness bottlenecks

4. EVOLUTIONARY FEEDBACK
   - Provides feedback to evolution system
   - Reports health capability gaps
   - Suggests fitness improvements
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

DATA_DIR = Path(__file__).parent.parent / "data" / "fitness_evolution"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FITNESS_EVOLUTION_STATE = DATA_DIR / "fitness_evolution_state.json"
FITNESS_METRICS = DATA_DIR / "fitness_metrics.jsonl"
EVOLUTION_FEEDBACK = DATA_DIR / "fitness_evolution_feedback.jsonl"


@dataclass
class FitnessPattern:
    """A pattern in fitness activities."""
    id: str = ""
    pattern_type: str = ""  # workout_consistency, intensity, timing
    description: str = ""
    frequency: int = 0
    effectiveness: float = 0.5
    last_observed: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FitnessMetric:
    """Fitness metric for evolution feedback."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat)
    workouts_completed: int = 0
    workout_consistency: float = 0.0
    goal_achievement_rate: float = 0.0
    energy_level: float = 0.5
    recovery_quality: float = 0.5
    overall_fitness_score: float = 0.5


class FitnessEvolutionIntegration:
    """
    Integration between fitness agent and evolution system.
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
        self._patterns: Dict[str, FitnessPattern] = {}
        self._fitness_history: List[FitnessMetric] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_state()
    
    # ── Fitness Pattern Detection ───────────────────────────────────────────────
    
    def analyze_fitness_patterns(self, workouts: List[Any]) -> List[FitnessPattern]:
        """Analyze workouts to detect patterns."""
        new_patterns = []
        
        if not workouts:
            return new_patterns
        
        # Pattern: Consistent workout timing
        if len(workouts) >= 3:
            new_patterns.append(FitnessPattern(
                id="workout_consistency",
                pattern_type="consistency",
                description="Regular workout pattern detected",
                frequency=len(workouts),
                effectiveness=0.8,
            ))
        
        if new_patterns:
            self._save_state()
        
        return new_patterns
    
    # ── Fitness Tracking ───────────────────────────────────────────────────────
    
    def track_fitness(self, workouts: List[Any]) -> FitnessMetric:
        """Track fitness metrics for evolution feedback."""
        try:
            metric = FitnessMetric(
                workouts_completed=len(workouts),
                workout_consistency=min(1.0, len(workouts) / 7.0),  # Weekly consistency
            )
            
            self._fitness_history.append(metric)
            self._log_fitness(metric)
            self._save_state()
            
            return metric
            
        except Exception as e:
            print(f"[FitnessEvolution] Fitness tracking error: {e}")
            return FitnessMetric()
    
    # ── Evolution Feedback ─────────────────────────────────────────────────────
    
    def provide_evolution_feedback(self) -> Dict[str, Any]:
        """Provide feedback to the evolution system."""
        try:
            feedback = {
                "capability_gaps": [],
                "evolutionary_pressures": {},
                "suggested_improvements": [],
            }
            
            # Analyze recent fitness
            if self._fitness_history:
                recent = self._fitness_history[-10:]
                avg_consistency = sum(m.workout_consistency for m in recent) / len(recent)
                
                # Identify capability gaps
                if avg_consistency < 0.3:
                    feedback["capability_gaps"].append({
                        "area": "fitness_consistency",
                        "severity": "high",
                        "description": "Low workout consistency",
                    })
                
                # Set evolutionary pressures
                feedback["evolutionary_pressures"] = {
                    "health": 1.0 - avg_consistency,  # Higher pressure when consistency is low
                }
                
                # Suggest improvements
                if avg_consistency < 0.3:
                    feedback["suggested_improvements"].append(
                        "Implement workout reminder system"
                    )
            
            self._log_evolution_feedback(feedback)
            
            return feedback
            
        except Exception as e:
            print(f"[FitnessEvolution] Feedback generation error: {e}")
            return {}
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        try:
            if FITNESS_EVOLUTION_STATE.exists():
                data = json.loads(FITNESS_EVOLUTION_STATE.read_text())
                for pid, pd in data.get("patterns", {}).items():
                    self._patterns[pid] = FitnessPattern(**pd)
        except Exception as e:
            print(f"[FitnessEvolution] State load error: {e}")
    
    def _save_state(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "patterns": {pid: asdict(p) for pid, p in self._patterns.items()},
            }
            FITNESS_EVOLUTION_STATE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[FitnessEvolution] State save error: {e}")
    
    def _log_fitness(self, metric: FitnessMetric):
        try:
            with open(FITNESS_METRICS, "a") as f:
                f.write(json.dumps(asdict(metric)) + "\n")
        except Exception:
            pass
    
    def _log_evolution_feedback(self, feedback: Dict):
        try:
            with open(EVOLUTION_FEEDBACK, "a") as f:
                f.write(json.dumps(feedback) + "\n")
        except Exception:
            pass


    # ── Background Loop ───────────────────────────────────────────────────────
    
    def start(self):
        """Start the fitness evolution background loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-FitnessEvolution"
        )
        self._thread.start()
        print("[FitnessEvolution] Started — fitness evolution active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(180)
        while self._running:
            try:
                # Periodic fitness pattern analysis
                self.analyze_fitness_patterns()
                self.track_fitness_metrics()
            except Exception as e:
                print(f"[FitnessEvolution] Loop error: {e}")
            time.sleep(3600)
    
# ── Singleton Access ─────────────────────────────────────────────────────────────

_fitness_evolution_instance: Optional[FitnessEvolutionIntegration] = None
_fitness_evolution_lock = threading.Lock()


def get_fitness_evolution_integration() -> FitnessEvolutionIntegration:
    global _fitness_evolution_instance
    with _fitness_evolution_lock:
        if _fitness_evolution_instance is None:
            _fitness_evolution_instance = FitnessEvolutionIntegration()
        return _fitness_evolution_instance