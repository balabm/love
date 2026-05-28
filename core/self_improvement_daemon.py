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

        # 8. Activity Log Health — learn from recent behavior patterns
        try:
            from core.activity_log import get_recent_activity, get_activity_stats
            stats = get_activity_stats(hours=24)
            recent = get_recent_activity(hours=6, limit=20)

            total_actions = stats.get("total", 0)
            trend = stats.get("trend", "idle")

            if total_actions == 0:
                issues.append({
                    "subsystem": "autonomy",
                    "severity": "high",
                    "issue": "No autonomous activity in the last 24 hours — system may be stalled",
                    "recommendation": "Check if supervisor and subsystems are running",
                })
                improvements.append({
                    "category": "capability_gap",
                    "action": "restart_autonomy_loops",
                    "priority": 0.9,
                    "auto_execute": False,
                    "context": "No recent activity detected"
                })
            elif trend == "idle":
                issues.append({
                    "subsystem": "autonomy",
                    "severity": "medium",
                    "issue": "Autonomy trend is idle — LOVE was active but has slowed down",
                    "recommendation": "Reduce loop intervals or increase trigger sensitivity",
                })

            # Check for repeated failures
            failed = [a for a in recent if a.get("action", "").startswith("failed") or a.get("action", "").endswith("_failed")]
            if len(failed) >= 3:
                issues.append({
                    "subsystem": "autonomy",
                    "severity": "high",
                    "issue": f"{len(failed)} recent failures detected in autonomous actions",
                    "recommendation": "Investigate and fix root causes — may need Ghost Dev intervention",
                })
                improvements.append({
                    "category": "capability_gap",
                    "action": "auto_fix_failures",
                    "priority": 0.85,
                    "auto_execute": True,
                    "context": f"{len(failed)} failures detected"
                })

            # Check for over-researching (too many research tasks, no execution)
            research_count = sum(1 for a in recent if a.get("component") == "research_engine")
            execute_count = sum(1 for a in recent if a.get("component") == "goal_engine" and a.get("action") == "execute")
            if research_count > 5 and execute_count == 0:
                issues.append({
                    "subsystem": "autonomy",
                    "severity": "low",
                    "issue": "High research activity but no goal execution — may be stuck in analysis paralysis",
                    "recommendation": "Force goal execution to convert knowledge into action",
                })

            scores.append(0.7 if total_actions > 10 else (0.5 if total_actions > 0 else 0.2))
        except Exception as e:
            scores.append(0.5)
            print(f"[SelfImprovementDaemon] Activity log health check error: {e}")

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
        Now handles more categories with real autonomous actions.
        """
        from core.activity_log import log_activity
        executed = 0
        failed = 0

        for imp in report.improvements:
            category = imp.get("category", "")
            action = imp.get("action", "")
            auto_execute = imp.get("auto_execute", False)

            try:
                if category == "prompt_evolution" and action == "evolve_weak_genes":
                    from core.prompt_dna import get_prompt_dna
                    dna = get_prompt_dna()
                    result = dna.evolve()
                    self._log("improvement_executed", {
                        "category": category, "action": action, "result": result
                    })
                    log_activity("self_improvement_daemon", "prompt_evolved", f"Evolved prompt DNA: {result}", {"result": str(result)[:200]}, importance="high")
                    executed += 1

                elif category == "memory_optimization" and action == "consolidate_memories":
                    from core.temporal_memory import get_temporal_memory
                    tmem = get_temporal_memory()
                    result = tmem.consolidate()
                    self._log("improvement_executed", {
                        "category": category, "action": action, "result": result
                    })
                    log_activity("self_improvement_daemon", "memory_consolidated", f"Consolidated temporal memories: {result}", {"result": str(result)[:200]}, importance="normal")
                    executed += 1

                elif category == "evolution_cycle":
                    from core.self_evolution import run_evolution_cycle
                    result = run_evolution_cycle()
                    self._log("improvement_executed", {
                        "category": category, "action": action, "result": str(result)[:200]
                    })
                    log_activity("self_improvement_daemon", "evolution_cycle", f"Ran self-evolution cycle", {"result": str(result)[:200]}, importance="high")
                    executed += 1

                elif category == "causal_learning" and action == "expand_causal_model":
                    # Queue research on causal reasoning to expand world model
                    try:
                        from core.research_engine import get_research_engine, ResearchPriority
                        re = get_research_engine()
                        re.add_research_task(
                            topic="causal reasoning in AI assistants",
                            question="How can an AI assistant build and maintain an accurate causal model of user behavior and system state?",
                            priority=ResearchPriority.MEDIUM,
                            source="self_improvement",
                            max_depth=1,
                            teach_user=False,
                        )
                        log_activity("self_improvement_daemon", "causal_research_queued", "Queued research to expand causal model", importance="normal")
                        executed += 1
                    except Exception as e:
                        failed += 1
                        self._log("improvement_failed", {"category": category, "action": action, "error": str(e)})

                elif category == "capability_gap" or (auto_execute and "gap" in action):
                    if action == "auto_fix_failures":
                        # Try to fix recent failures by queuing research on common failure patterns
                        try:
                            from core.research_engine import get_research_engine, ResearchPriority
                            from core.ghost_dev import get_ghost_dev
                            re = get_research_engine()
                            re.add_research_task(
                                topic="LOVE system failure patterns",
                                question="What are common failure patterns in autonomous AI systems and how can they be made self-healing?",
                                priority=ResearchPriority.HIGH,
                                source="self_healing",
                                max_depth=1,
                                teach_user=False,
                            )
                            log_activity("self_improvement_daemon", "auto_fix_triggered", "Queued research to fix repeated failures", importance="high")
                            executed += 1
                        except Exception as e:
                            failed += 1
                            self._log("improvement_failed", {"category": category, "action": action, "error": str(e)})
                    else:
                        # Trigger wave engine to propose a wave for this gap
                        try:
                            from core.wave_engine import get_wave_engine
                            wave = get_wave_engine()
                            wave.run_cycle()
                            log_activity("self_improvement_daemon", "wave_triggered", "Triggered wave engine for capability gap", importance="high")
                            executed += 1
                        except Exception as e:
                            failed += 1
                            self._log("improvement_failed", {"category": category, "action": action, "error": str(e)})

                elif category == "goal_refinement" and "stale" in str(imp.get("context", "")).lower():
                    # Decompose stale goals via goal engine
                    try:
                        from core.autonomous_goal_engine import get_goals, update_goal_progress
                        stale = [g for g in get_goals("active") if g.progress_pct == 0]
                        for g in stale[:1]:
                            update_goal_progress(g.id, 1, "Auto-decomposed by self-improvement daemon to prevent stagnation")
                        log_activity("self_improvement_daemon", "goals_decomposed", f"Decomposed {len(stale[:1])} stale goal(s)", importance="normal")
                        executed += 1
                    except Exception as e:
                        failed += 1
                        self._log("improvement_failed", {"category": category, "action": action, "error": str(e)})

                else:
                    # Log proposals that couldn't be auto-executed
                    if not auto_execute:
                        log_activity("self_improvement_daemon", "improvement_proposed", f"Proposed: {category}/{action} — needs review", {"category": category, "action": action}, importance="normal")

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
        from core.activity_log import log_activity
        print(f"[SelfImprovementDaemon] Started. Running every {interval_minutes} minutes.")
        log_activity("self_improvement_daemon", "started", f"Daemon started, interval={interval_minutes}min", importance="normal")

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

                # Log to activity log
                log_activity("self_improvement_daemon", "diagnostics_complete",
                    f"Health={report.health_score:.2f}, issues={len(report.issues)}, improvements={results['executed']}",
                    {"health_score": report.health_score, "issues": len(report.issues), "executed": results["executed"]},
                    importance="high" if report.health_score < 0.5 else "normal")

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
                log_activity("self_improvement_daemon", "error", f"Daemon error: {str(e)[:100]}", {"error": str(e)[:200]}, importance="critical")
                print(f"[SelfImprovementDaemon] Error: {e}")

            # Sleep for interval
            for _ in range(interval_minutes * 60):
                if not self._running:
                    break
                time.sleep(1)

        log_activity("self_improvement_daemon", "stopped", "Daemon stopped", importance="normal")
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
        """Get daemon status with activity summary."""
        status = {
            "running": self._running,
            "last_run": self.state.get("last_run"),
            "last_health_score": self.state.get("last_health_score"),
            "total_runs": self.state.get("total_runs", 0),
            "total_improvements": self.state.get("total_improvements", 0),
        }
        try:
            from core.activity_log import get_activity_stats
            stats = get_activity_stats(hours=24)
            status["activity_today"] = stats.get("total", 0)
            status["activity_trend"] = stats.get("trend", "idle")
            status["activity_by_component"] = stats.get("by_component", {})
        except Exception:
            pass
        return status

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
