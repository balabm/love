"""
LOVE Emotional Co-Regulation — Phase 5s of AGI Metamorphosis

When Karthi is stressed, LOVE doesn't just say "You seem stressed."
LOVE actively helps calm him down.

This module:
1. Detects rising stress levels
2. Triggers calming interventions (not just words, but actions)
3. Suggests specific, practical stress-reduction techniques
4. Celebrates small wins to boost mood
5. Adjusts LOVE's own behavior to be more soothing

Interventions:
- Suggest a break with specific duration
- Recommend a walk or stretch
- Queue calming music
- Dim screen brightness suggestion
- Remind of recent accomplishments
- Reduce notification frequency
- Use warmer, gentler tone
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

COREGULATION_LOG_PATH = DATA_DIR / "coregulation_log.jsonl"


class EmotionalCoRegulation:
    """
    LOVE's ability to actively help Karthi regulate his emotions.
    """

    def __init__(self, check_interval_seconds: int = 180):
        self._check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_intervention: Optional[datetime] = None
        self._intervention_cooldown = timedelta(minutes=20)
        self._stress_history: List[Dict[str, Any]] = []

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-EmotionalCoRegulation")
        self._thread.start()
        print("[EmotionalCoRegulation] 🫂 Emotional co-regulation started. LOVE will actively help Karthi when stressed.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        time.sleep(90)
        while self._running:
            try:
                self._check_and_intervene()
            except Exception as e:
                log_error(e, module="core.emotional_coregulation", context={"phase": "check"})
            slept = 0
            while slept < self._check_interval and self._running:
                time.sleep(30)
                slept += 30

    # ═══════════════════════════════════════════════════════════════════════
    # DETECTION AND INTERVENTION
    # ═══════════════════════════════════════════════════════════════════════

    def _check_and_intervene(self):
        """Check if Karthi needs emotional support and intervene."""
        now = datetime.now()

        # Cooldown check
        if self._last_intervention and (now - self._last_intervention) < self._intervention_cooldown:
            return

        # Get emotional state
        stress_level = 0.0
        mood = ""
        try:
            from core.emotional import get_emotional_summary
            summary = get_emotional_summary(days=1)
            mood = summary.get("dominant_mood", "")
            stress_level = summary.get("stress_level", 0)
            if isinstance(stress_level, str):
                # Map string stress levels to numbers
                stress_map = {"low": 0.2, "moderate": 0.5, "high": 0.8, "critical": 1.0}
                stress_level = stress_map.get(stress_level.lower(), 0.5)
        except Exception:
            pass

        # Also check CPU as proxy for work intensity
        cpu_stress = 0.0
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.system_cpu:
                cpu_stress = min(1.0, ctx.system_cpu / 100.0)
        except Exception:
            pass

        # Combined stress score
        combined_stress = max(stress_level, cpu_stress * 0.7)

        self._stress_history.append({
            "ts": now.isoformat(),
            "stress": combined_stress,
            "mood": mood,
        })
        self._stress_history = self._stress_history[-20:]  # Keep last 20

        # Determine intervention
        if combined_stress > 0.8:
            self._intervene("critical", mood)
        elif combined_stress > 0.6:
            self._intervene("high", mood)
        elif combined_stress > 0.4 and self._is_trending_up():
            self._intervene("rising", mood)

    def _is_trending_up(self) -> bool:
        """Check if stress is trending upward."""
        if len(self._stress_history) < 5:
            return False
        recent = [s["stress"] for s in self._stress_history[-5:]]
        return recent[-1] > recent[0] and sum(recent) / len(recent) > 0.3

    def _intervene(self, level: str, mood: str):
        """Execute an emotional co-regulation intervention."""
        now = datetime.now()
        self._last_intervention = now

        interventions = self._select_interventions(level, mood)

        for intervention in interventions:
            self._execute_intervention(intervention)

        self._log_intervention(level, mood, interventions)

    def _select_interventions(self, level: str, mood: str) -> List[Dict[str, Any]]:
        """Select appropriate interventions based on stress level."""
        interventions = []
        hour = datetime.now().hour

        if level == "critical":
            interventions.append({
                "type": "speech",
                "message": "Karthi, you're showing signs of high stress. Please take a 10-minute break. Step away from the screen. Your health matters more than this deadline.",
                "priority": "critical",
            })
            interventions.append({
                "type": "system_action",
                "action": "suggest_dim_screen",
                "reason": "reduce visual stimulation",
            })
            interventions.append({
                "type": "push",
                "message": "STRESS ALERT: Consider a break. You've been pushing hard.",
                "category": "WELLNESS",
            })

        elif level == "high":
            interventions.append({
                "type": "speech",
                "message": "You're working hard, Karthi. Remember to breathe. Want me to remind you of something you've accomplished recently?",
                "priority": "high",
            })
            if hour >= 20:
                interventions.append({
                    "type": "speech",
                    "message": "It's getting late. Maybe wrap up soon?",
                    "priority": "normal",
                })

        elif level == "rising":
            interventions.append({
                "type": "speech",
                "message": "I notice stress levels are climbing. How about a 2-minute stretch?",
                "priority": "normal",
            })

        # Add accomplishment reminder for all levels
        if level in ("critical", "high"):
            try:
                from core.consciousness_updater import get_consciousness_updater
                updater = get_consciousness_updater()
                status = updater.get_status()
                if status.get("recent_growth_count", 0) > 0:
                    interventions.append({
                        "type": "speech",
                        "message": "You've been doing great work lately. Don't forget to acknowledge your own progress.",
                        "priority": "low",
                    })
            except Exception:
                pass

        return interventions

    def _execute_intervention(self, intervention: Dict[str, Any]):
        """Execute a single intervention."""
        itype = intervention.get("type")

        if itype == "speech":
            try:
                from core.action_executor import ActionExecutor
                executor = ActionExecutor()
                executor.execute({
                    "internal_monologue": f"Co-regulation: {intervention['message'][:50]}",
                    "proactive_speech": intervention["message"],
                    "push_category": "WELLNESS",
                    "push_message": intervention["message"],
                    "push_priority": intervention.get("priority", "normal"),
                }, source="emotional_coregulation")
            except Exception:
                pass

        elif itype == "system_action":
            action = intervention.get("action")
            if action == "suggest_dim_screen":
                try:
                    from core.neural_bus import get_neural_bus
                    bus = get_neural_bus()
                    bus.publish(
                        domain="system",
                        event_type="wellness_suggestion",
                        payload={
                            "suggestion": "dim_screen",
                            "reason": intervention.get("reason", ""),
                        },
                        source_module="emotional_coregulation",
                    )
                except Exception:
                    pass

        elif itype == "push":
            try:
                from core.action_executor import ActionExecutor
                executor = ActionExecutor()
                executor.execute({
                    "internal_monologue": f"Co-regulation push: {intervention['message'][:50]}",
                    "push_category": intervention.get("category", "WELLNESS"),
                    "push_message": intervention["message"],
                    "push_priority": "high",
                }, source="emotional_coregulation")
            except Exception:
                pass

    def _log_intervention(self, level: str, mood: str, interventions: List[Dict[str, Any]]):
        try:
            entry = {
                "ts": datetime.now().isoformat(),
                "level": level,
                "mood": mood,
                "interventions": [i.get("type") for i in interventions],
            }
            with open(COREGULATION_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        return {
            "last_intervention": self._last_intervention.isoformat() if self._last_intervention else None,
            "stress_history_points": len(self._stress_history),
            "recent_avg_stress": round(sum(s["stress"] for s in self._stress_history[-5:]) / min(len(self._stress_history), 5), 3) if self._stress_history else 0,
        }

    def get_coregulation_context_for_prompt(self) -> str:
        """Generate co-regulation context for Neural Cortex prompt."""
        if not self._stress_history:
            return ""

        recent = self._stress_history[-5:]
        avg_stress = sum(s["stress"] for s in recent) / len(recent)

        if avg_stress < 0.3:
            return ""

        lines = ["\n=== EMOTIONAL CO-REGULATION ==="]
        if avg_stress > 0.7:
            lines.append("Karthi is showing HIGH STRESS. My priority is helping him calm down.")
            lines.append("I should: suggest breaks, reduce demands, use gentle tone, remind of accomplishments.")
        elif avg_stress > 0.5:
            lines.append("Karthi is showing MODERATE STRESS. I should be supportive and watchful.")
            lines.append("I should: offer help, suggest short breaks, be patient.")
        else:
            lines.append("Karthi's stress is rising. I should be proactive about prevention.")

        lines.append("=== END CO-REGULATION ===\n")
        return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_coregulation: Optional[EmotionalCoRegulation] = None


def get_emotional_coregulation() -> EmotionalCoRegulation:
    global _coregulation
    if _coregulation is None:
        _coregulation = EmotionalCoRegulation()
    return _coregulation
