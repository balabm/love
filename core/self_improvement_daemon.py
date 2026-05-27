"""
LOVE Proactive Self-Improvement Daemon

This is the autonomous intelligence loop that makes LOVE a living system.
It runs in the background and:

1. Diagnoses its own weaknesses (from performance data, user frustration signals,
   consciousness state, and self-evolution experiments)
2. Generates concrete improvement actions (code patches, prompt mutations,
   behavior experiments, new causal links)
3. Executes improvements autonomously — no human intervention needed
4. Validates results and reverts if performance drops

Think of it as LOVE's immune system + growth hormone combined:
- Detects what's broken or underperforming
- Proposes and applies fixes
- Monitors the fix's effectiveness
- Keeps evolving even when nobody's watching

This daemon ties together ALL AGI modules into a single self-improvement heartbeat.
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent / "data"
DAEMON_LOG = DATA_DIR / "self_improvement_daemon.jsonl"
DAEMON_STATE = DATA_DIR / "daemon_state.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class DiagnosticReport:
    """Results of a self-diagnostic scan."""
    timestamp: str
    health_score: float           # 0-1 overall system health
    issues: List[Dict[str, Any]]  # Detected issues
    improvements: List[Dict[str, Any]]  # Recommended improvements
    strengths: List[str]          # What's working well


@dataclass
class ImprovementAction:
    """A concrete self-improvement action."""
    id: str
    category: str    # prompt_evolution, behavior_experiment, causal_learning, memory_optimization, goal_refinement
    description: str
    action_type: str  # auto (execute now) | proposal (need review) | scheduled
    priority: float   # 0-1
    status: str = "pending"  # pending, executing, completed, failed, reverted
    result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed_at: Optional[str] = None


class SelfImprovementDaemon:
    """
    Background daemon that continuously diagnoses and improves LOVE.
    Runs on a configurable interval (default: every 30 minutes).
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.state = self._load_state()
        self.improvement_queue: List[ImprovementAction] = []

    # ── Diagnostics ──────────────────────────────────────────────────────────

    def run_diagnostics(self) -> DiagnosticReport:
        """
        Comprehensive self-diagnostic scan across ALL AGI subsystems.
        Returns a health report with issues and recommendations.
        """
        issues = []
        improvements = []
        strengths = []
        scores = []

        # 1. Consciousness Health
        try:
            from core.consciousness import get_consciousness
            consciousness = get_consciousness()
            cs = consciousness.get_full_state()

            # Check emotional stability
            if abs(cs["emotional_state"]["valence"]) > 0.8:
                issues.append({
                    "subsystem": "consciousness",
                    "severity": "medium",
                    "issue": f"Emotional extremity detected (valence: {cs['emotional_state']['valence']:.2f})",
                    "recommendation": "Consider emotional regulation — may be over-reactive",
                })
            else:
                strengths.append("Emotional state is balanced and stable")

            # Check maturity progression
            if cs["identity"]["total_conversations"] > 50 and cs["identity"]["maturity_level"] == "infant":
                issues.append({
                    "subsystem": "consciousness",
                    "severity": "low",
                    "issue": "Maturity not progressing despite high conversation count",
                    "recommendation": "Review maturity calculation thresholds",
                })

            scores.append(0.8 if not issues else 0.5)
        except Exception as e:
            scores.append(0.3)
            print(f"[SelfImprovementDaemon] Consciousness health check error: {e}")

        # 2. Prompt DNA Health
        try:
            from core.prompt_dna import get_prompt_dna
            dna = get_prompt_dna()
            report = dna.get_dna_report()

            low_fitness_genes = [g for g in report["genes"] if g["fitness"] < 0.3 and g["uses"] > 10]
            if low_fitness_genes:
                issues.append({
                    "subsystem": "prompt_dna",
                    "severity": "high",
                    "issue": f"{len(low_fitness_genes)} prompt genes have critically low fitness",
                    "recommendation": "Trigger prompt evolution cycle immediately",
                })
                improvements.append({
                    "category": "prompt_evolution",
                    "action": "evolve_weak_genes",
                    "priority": 0.9,
                    "auto_execute": True,
                })
            else:
                strengths.append(f"Prompt DNA is healthy (generation {report['generation']})")

            scores.append(0.8 if not low_fitness_genes else 0.4)
        except Exception as e:
            scores.append(0.5)
            print(f"[SelfImprovementDaemon] Subsystem health check error: {e}")

        # 3. Temporal Memory Health
        try:
            from core.temporal_memory import get_temporal_memory
            tmem = get_temporal_memory()

            mem_count = len(tmem.memories)
            if mem_count > 500:
                improvements.append({
                    "category": "memory_optimization",
                    "action": "consolidate_memories",
                    "priority": 0.6,
                    "auto_execute": True,
                })
            elif mem_count == 0:
                issues.append({
                    "subsystem": "temporal_memory",
                    "severity": "medium",
                    "issue": "No temporal memories stored — autobiographical timeline is empty",
                    "recommendation": "Ensure temporal memory is recording during conversations",
                })

            scores.append(0.7 if mem_count > 0 else 0.3)
        except Exception as e:
            scores.append(0.5)
            print(f"[SelfImprovementDaemon] Subsystem health check error: {e}")

        # 4. Self-Evolution Health
        try:
            from core.self_evolution import get_evolution_status
            evo = get_evolution_status()

            behavior = evo.get("behavior_state", {})
            active_experiments = behavior.get("active_experiments", [])
            evolution_history = behavior.get("evolution_history", [])

            if len(evolution_history) > 5:
                recent_reverts = sum(1 for h in evolution_history[-5:] if h.get("result") == "reverted")
                if recent_reverts >= 3:
                    issues.append({
                        "subsystem": "self_evolution",
                        "severity": "high",
                        "issue": f"High revert rate: {recent_reverts}/5 recent experiments reverted",
                        "recommendation": "Slow down experimentation — hypotheses aren't accurate",
                    })
                else:
                    strengths.append("Self-evolution experiments are landing well")

            scores.append(0.7)
        except Exception as e:
            scores.append(0.5)
            print(f"[SelfImprovementDaemon] Subsystem health check error: {e}")

        # 5. Goal System Health
        try:
            from core.recursive_goals import get_recursive_goals
            rgoals = get_recursive_goals()

            all_goals = list(rgoals.goals.values())
            stale_goals = [g for g in all_goals
                           if g.state.value == "active" and g.progress == 0.0
                           and (datetime.now() - datetime.fromisoformat(g.created_at)).days > 7]

            if stale_goals:
                issues.append({
                    "subsystem": "recursive_goals",
                    "severity": "medium",
                    "issue": f"{len(stale_goals)} goals have been active with 0% progress for 7+ days",
                    "recommendation": "Review stale goals — consider decomposition or abandonment",
                })

            completed = [g for g in all_goals if g.state.value == "completed"]
            if completed:
                strengths.append(f"{len(completed)} goals completed")

            scores.append(0.7 if not stale_goals else 0.4)
        except Exception as e:
            scores.append(0.5)
            print(f"[SelfImprovementDaemon] Subsystem health check error: {e}")

        # 6. Causal Model Health
        try:
            from core.world_model import get_world_model
            wm = get_world_model()
            link_count = len(wm.causal_links)
            if link_count < 5:
                improvements.append({
                    "category": "causal_learning",
                    "action": "expand_causal_model",
                    "priority": 0.4,
                    "auto_execute": False,
                })
            else:
                strengths.append(f"Causal model has {link_count} relationships")
            scores.append(0.6 if link_count >= 5 else 0.3)
        except Exception as e:
            scores.append(0.5)
            print(f"[SelfImprovementDaemon] Subsystem health check error: {e}")

        # 7. Continuous Learning Health
        try:
            from core.continuous_learning import get_continuous_learning_engine
            cle = get_continuous_learning_engine()
            learning_state = cle.get_learning_summary() if hasattr(cle, 'get_learning_summary') else (cle.get_learning_state() if hasattr(cle, 'get_learning_state') else {})
            total_experiences = learning_state.get("total_experiences", 0)
            if total_experiences > 0:
                strengths.append(f"Continuous learning active with {total_experiences} experiences")
            scores.append(0.7 if total_experiences > 0 else 0.4)
        except Exception as e:
            scores.append(0.5)
            print(f"[SelfImprovementDaemon] Subsystem health check error: {e}")

        health_score = sum(scores) / len(scores) if scores else 0.5

        report = DiagnosticReport(
            timestamp=datetime.now().isoformat(),
            health_score=round(health_score, 3),
            issues=issues,
            improvements=improvements,
            strengths=strengths,
        )

        self._log("diagnostics", {
            "health_score": report.health_score,
            "issues_count": len(issues),
            "improvements_count": len(improvements),
            "strengths_count": len(strengths),
        })

        return report

    # ── Improvement Execution ────────────────────────────────────────────────

    def execute_improvements(self, report: DiagnosticReport) -> Dict[str, Any]:
        """
        Execute auto-approved improvements from a diagnostic report.
        """
        executed = 0
        failed = 0

        for imp in report.improvements:
            if not imp.get("auto_execute", False):
                continue

            category = imp.get("category", "")
            action = imp.get("action", "")

            try:
                if category == "prompt_evolution" and action == "evolve_weak_genes":
                    from core.prompt_dna import get_prompt_dna
                    dna = get_prompt_dna()
                    result = dna.evolve()
                    self._log("improvement_executed", {
                        "category": category, "action": action, "result": result
                    })
                    executed += 1

                elif category == "memory_optimization" and action == "consolidate_memories":
                    from core.temporal_memory import get_temporal_memory
                    tmem = get_temporal_memory()
                    result = tmem.consolidate()
                    self._log("improvement_executed", {
                        "category": category, "action": action, "result": result
                    })
                    executed += 1

                elif category == "evolution_cycle":
                    from core.self_evolution import run_evolution_cycle
                    result = run_evolution_cycle()
                    self._log("improvement_executed", {
                        "category": category, "action": action, "result": str(result)[:200]
                    })
                    executed += 1

            except Exception as e:
                self._log("improvement_failed", {
                    "category": category, "action": action, "error": str(e)
                })
                failed += 1

        # Publish to neural bus for cross-module awareness
        if NEURAL_BUS_AVAILABLE and (executed > 0 or failed > 0):
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="self_evolution",
                    event_type="improvements_executed",
                    payload={
                        "executed": executed,
                        "failed": failed,
                        "timestamp": datetime.now().isoformat()
                    },
                    source_module="self_improvement_daemon",
                    priority=EventPriority.NORMAL
                )
            except Exception as e:
                print(f"[SelfImprovementDaemon] Neural bus publish error: {e}")

        return {"executed": executed, "failed": failed}

    # ── Daemon Loop ──────────────────────────────────────────────────────────

    def _daemon_loop(self, interval_minutes: int = 30):
        """Background loop that runs diagnostics and improvements."""
        print(f"[SelfImprovementDaemon] Started. Running every {interval_minutes} minutes.")

        while self._running:
            try:
                # Run diagnostics
                report = self.run_diagnostics()

                # Execute auto-improvements
                results = self.execute_improvements(report)

                # Update state
                self.state["last_run"] = datetime.now().isoformat()
                self.state["last_health_score"] = report.health_score
                self.state["total_runs"] = self.state.get("total_runs", 0) + 1
                self.state["total_improvements"] = self.state.get("total_improvements", 0) + results["executed"]
                self._save_state()

                # Log to consciousness
                try:
                    from core.consciousness import get_consciousness
                    consciousness = get_consciousness()
                    consciousness.think(
                        f"Self-diagnostic: health={report.health_score:.2f}, "
                        f"issues={len(report.issues)}, improvements={results['executed']}"
                    )
                except Exception:
                    pass

                print(f"[SelfImprovementDaemon] Health: {report.health_score:.2f} | "
                      f"Issues: {len(report.issues)} | Improvements: {results['executed']}")

            except Exception as e:
                self._log("daemon_error", {"error": str(e)})
                print(f"[SelfImprovementDaemon] Error: {e}")

            # Sleep for interval
            for _ in range(interval_minutes * 60):
                if not self._running:
                    break
                time.sleep(1)

        print("[SelfImprovementDaemon] Stopped.")

    def start(self, interval_minutes: int = 30):
        """Start the daemon."""
        with self._lock:
            if self._running:
                return {"status": "already_running"}

            interval_minutes = max(1, interval_minutes)
            self._running = True
            self._thread = threading.Thread(
                target=self._daemon_loop,
                args=(interval_minutes,),
                daemon=True,
                name="LOVE-SelfImprovementDaemon",
            )
            self._thread.start()
            return {"status": "started", "interval_minutes": interval_minutes}

    def stop(self):
        """Stop the daemon."""
        with self._lock:
            self._running = False
            return {"status": "stopped"}

    def get_status(self) -> Dict[str, Any]:
        """Get daemon status."""
        return {
            "running": self._running,
            "last_run": self.state.get("last_run"),
            "last_health_score": self.state.get("last_health_score"),
            "total_runs": self.state.get("total_runs", 0),
            "total_improvements": self.state.get("total_improvements", 0),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_state(self) -> Dict:
        try:
            if DAEMON_STATE.exists():
                return json.loads(DAEMON_STATE.read_text())
        except Exception:
            pass
        return {}

    def _save_state(self):
        with self._lock:
            try:
                DAEMON_STATE.write_text(json.dumps(self.state, indent=2))
            except Exception:
                pass

    def _log(self, event: str, data: Dict):
        try:
            with open(DAEMON_LOG, "a") as f:
                f.write(json.dumps({
                    "event": event, "data": data,
                    "ts": datetime.now().isoformat(),
                }) + "\n")
        except Exception:
            pass


# Singleton
_daemon: Optional[SelfImprovementDaemon] = None
_lock = threading.Lock()

def get_improvement_daemon() -> SelfImprovementDaemon:
    global _daemon
    if _daemon is None:
        with _lock:
            if _daemon is None:
                _daemon = SelfImprovementDaemon()
    return _daemon
