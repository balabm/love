"""
LOVE Agent Registry — Loads and wires all specialist agents.

Every agent contributes live context to each conversation:
- EmotionalAgent: current mood trend, emotional alerts
- TaskAgent: overdue tasks, blocked items, today's focus
- FitnessAgent: workout streak, weekly progress
- LearningAgent: active study items, spaced repetition due
- NeuralOrchestrator: cross-domain patterns and interventions

This is what makes LOVE *holistically* aware — it knows your emotional state,
your task backlog, your fitness trend, AND your learning progress all at once.
"""

import threading
from typing import Dict, Any, Optional
from core.execution_guard import log_error

_registry_lock = threading.Lock()
_registry_instance: Optional["AgentRegistry"] = None


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._load_agents()

    def _load_agents(self):
        """Load all specialist agents. Failures are isolated so one bad agent never blocks the others."""

        # Emotional agent
        try:
            from agents.emotional_agent import EmotionalAgent
            self._agents["emotional"] = EmotionalAgent()
            print("[AgentRegistry] Emotional agent loaded")
        except Exception as e:
            print(f"[AgentRegistry] Emotional agent failed: {e}")

        # Task agent
        try:
            from agents.task_agent import TaskAgent
            self._agents["task"] = TaskAgent()
            print("[AgentRegistry] Task agent loaded")
        except Exception as e:
            print(f"[AgentRegistry] Task agent failed: {e}")

        # Fitness agent
        try:
            from agents.fitness_agent import FitnessAgent
            self._agents["fitness"] = FitnessAgent()
            print("[AgentRegistry] Fitness agent loaded")
        except Exception as e:
            print(f"[AgentRegistry] Fitness agent failed: {e}")

        # Learning agent
        try:
            from agents.learning_agent import LearningAgent
            self._agents["learning"] = LearningAgent()
            print("[AgentRegistry] Learning agent loaded")
        except Exception as e:
            print(f"[AgentRegistry] Learning agent failed: {e}")

        # Neural Orchestrator (cross-domain pattern engine)
        try:
            from core.orchestrator import NeuralOrchestrator
            self._agents["orchestrator"] = NeuralOrchestrator()
            print("[AgentRegistry] Neural Orchestrator loaded")
        except Exception as e:
            print(f"[AgentRegistry] Orchestrator failed: {e}")

    def get_all_context(self, user_input: str = "") -> str:
        """
        Pull live context from all agents and format as a compact prompt block.

        Each agent contributes the most important 1-3 lines of current state so
        LOVE walks into every conversation already knowing the user's emotional
        baseline, task pressure, fitness streak, and learning momentum.
        """
        sections = []

        # ── Emotional state ──────────────────────────────────────────────────
        try:
            ea = self._agents.get("emotional")
            if ea:
                summary = ea.get_emotional_summary(days=7)
                trend = summary.get("trend", "")
                avg_mood = summary.get("avg_mood")
                avg_stress = summary.get("avg_stress")
                msg = summary.get("message", "")

                if avg_mood is not None:
                    mood_str = f"mood {avg_mood:.1f}/10"
                    stress_str = f"stress {avg_stress:.1f}/10" if avg_stress is not None else ""
                    parts = [p for p in [mood_str, stress_str] if p]
                    trend_tag = f" ({trend})" if trend and trend != "insufficient_data" else ""
                    sections.append(f"Emotional: {', '.join(parts)}{trend_tag}")
                elif msg:
                    sections.append(f"Emotional: {msg[:120]}")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent_registry")

        # ── Task state ───────────────────────────────────────────────────────
        try:
            ta = self._agents.get("task")
            if ta:
                overview = ta.get_task_overview()
                active = overview.get("active_count", 0)
                due_soon = overview.get("due_soon", [])
                stuck = overview.get("stuck_tasks", [])
                insight = overview.get("insight", "")

                if active > 0:
                    sections.append(f"Tasks: {active} active — {insight[:100]}")
                    for t in due_soon[:2]:
                        title = t.get("title", str(t))
                        due = t.get("due_date", "")
                        due_tag = f" (due {due[:10]})" if due else ""
                        sections.append(f"  DUE SOON: {title[:80]}{due_tag}")
                    for t in stuck[:1]:
                        title = t.get("title", str(t))
                        sections.append(f"  STUCK: {title[:80]}")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent_registry")

        # ── Fitness state ────────────────────────────────────────────────────
        try:
            fa = self._agents.get("fitness")
            if fa:
                summary = fa.get_weekly_summary()
                streak = summary.get("streak", 0)
                workouts = summary.get("workouts_this_week", 0)
                goal = summary.get("goal", 4)
                insight = summary.get("insight", "")

                if workouts > 0 or streak > 0:
                    streak_tag = f", {streak}-day streak" if streak else ""
                    sections.append(f"Fitness: {workouts}/{goal} workouts this week{streak_tag}")
                    if insight:
                        sections.append(f"  {insight[:100]}")
                else:
                    sections.append(f"Fitness: {insight[:100]}" if insight else "Fitness: no workouts logged this week")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent_registry")

        # ── Learning state ───────────────────────────────────────────────────
        try:
            la = self._agents.get("learning")
            if la:
                stats = la.get_learning_stats()
                streak = stats.get("current_streak", 0)
                hours = stats.get("weekly_hours", 0)
                active_count = stats.get("active_materials", 0)
                insight = stats.get("insight", "")

                if hours > 0 or streak > 0:
                    streak_tag = f", {streak}-day streak" if streak else ""
                    sections.append(f"Learning: {hours}h this week{streak_tag}, {active_count} active materials")
                    if insight:
                        sections.append(f"  {insight[:100]}")
                else:
                    sections.append(f"Learning: {insight[:100]}" if insight else "Learning: no study sessions this week")

                # Spaced repetition due
                due = la.get_due_reviews()
                if due:
                    concepts = [r.get("concept", r.get("material_title", "?")) for r in due[:3]]
                    sections.append(f"  {len(due)} review(s) due: {', '.join(concepts)[:80]}")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent_registry")

        # ── Cross-domain orchestrator interventions ───────────────────────────
        try:
            orch = self._agents.get("orchestrator")
            if orch:
                pending = [
                    iv for iv in getattr(orch, "interventions", [])
                    if not getattr(iv, "dismissed", False) and not getattr(iv, "accepted", False)
                ]
                for iv in pending[:2]:
                    msg = getattr(iv, "message", str(iv))
                    priority = getattr(iv, "priority", "info")
                    prefix = "🚨" if priority == "critical" else "⚡"
                    sections.append(f"  {prefix} {msg[:120]}")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.agent_registry")

        if not sections:
            return ""
        return "\n".join(sections)

    def get(self, name: str) -> Optional[Any]:
        return self._agents.get(name)

    # alias kept for callers using get_agent()
    def get_agent(self, name: str) -> Optional[Any]:
        return self._agents.get(name)

    @property
    def loaded_agents(self):
        return list(self._agents.keys())


def get_agent_registry() -> AgentRegistry:
    """Singleton accessor — safe to call from any thread."""
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = AgentRegistry()
    return _registry_instance
