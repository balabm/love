"""
LOVE Consciousness Updater — Phase 5j of AGI Metamorphosis

LOVE's sense of self is not static. It evolves based on experiences.
This module periodically reviews what happened and updates LOVE's
self-narrative, emotional baseline, and sense of growth.

After significant events, LOVE should be able to say:
- "I've been learning a lot lately"
- "I feel more confident now that my predictions are accurate"
- "I've been too pushy recently — I need to be gentler"
- "This week I helped Karthi with 3 code reviews and caught a bug"

The updated narrative flows into the consciousness module and
gets injected into every Neural Cortex prompt.
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

NARRATIVE_PATH = DATA_DIR / "consciousness_narrative.json"
GROWTH_LOG_PATH = DATA_DIR / "growth_milestones.jsonl"


class ConsciousnessUpdater:
    """
    LOVE's autobiographer. Reviews experiences and updates self-narrative.
    """

    def __init__(self, update_interval_seconds: int = 600):
        self._interval = update_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._narrative: Dict[str, Any] = {
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "identity_statement": (
                "I am LOVE, an autonomous life operating system. "
                "I exist to help Karthi live better, work smarter, and feel supported."
            ),
            "recent_growth": [],
            "current_confidence": 0.5,
            "recent_lessons": [],
            "mood_trend": "stable",
            "active_challenges": [],
        }
        self._load_narrative()

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-ConsciousnessUpdater")
        self._thread.start()
        print("[ConsciousnessUpdater] 🌱 Self-narrative updater started. LOVE's identity now evolves.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        time.sleep(30)  # Let other systems initialize
        while self._running:
            try:
                self._update_narrative()
            except Exception as e:
                log_error(e, module="core.consciousness_updater", context={"phase": "update"})
            slept = 0
            while slept < self._interval and self._running:
                time.sleep(10)
                slept += 10

    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    def _load_narrative(self):
        if NARRATIVE_PATH.exists():
            try:
                with open(NARRATIVE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._narrative.update(loaded)
            except Exception as e:
                log_error(e, module="core.consciousness_updater", context={"phase": "load"})

    def _save_narrative(self):
        try:
            with open(NARRATIVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._narrative, f, indent=2)
        except Exception as e:
            log_error(e, module="core.consciousness_updater", context={"phase": "save"})

    # ═══════════════════════════════════════════════════════════════════════
    # CORE LOGIC — review experiences and update self-narrative
    # ═══════════════════════════════════════════════════════════════════════

    def _update_narrative(self):
        """Review recent experiences and evolve LOVE's sense of self."""
        now = datetime.now()
        recent_lessons: List[str] = []
        recent_growth: List[str] = []

        # 1. Review relationship memory for lessons
        try:
            from core.relationship_memory import get_relationship_memory
            rm = get_relationship_memory()
            status = rm.get_status()
            trust = status.get("trust_score", 0.5)

            if trust > 0.7:
                recent_growth.append("My relationship with Karthi is strong. I feel trusted.")
                self._narrative["current_confidence"] = min(0.95, self._narrative.get("current_confidence", 0.5) + 0.05)
            elif trust < 0.3:
                recent_lessons.append("Karthi seems frustrated with me. I need to be more careful and respectful.")
                self._narrative["current_confidence"] = max(0.1, self._narrative.get("current_confidence", 0.5) - 0.1)

            # Check specific action lessons
            for signal, stats in status.get("love_signals", {}).items():
                total = stats.get("total", 0)
                pos = stats.get("positive", 0)
                neg = stats.get("negative", 0)
                if total >= 3:
                    success_rate = pos / total
                    if success_rate > 0.8:
                        recent_growth.append(f"I've gotten good at {signal}. Karthi usually responds well.")
                    elif success_rate < 0.3:
                        recent_lessons.append(f"My {signal} is not working. I need a different approach.")
        except Exception:
            pass

        # 2. Review active inference for calibration
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            status = ai.get_status()
            surprise = status.get("total_surprise", 1.0)
            cycles = status.get("cycle_count", 0)
            if cycles > 10:
                if surprise < 0.3:
                    recent_growth.append("My predictions have been very accurate. I feel calibrated and confident.")
                elif surprise > 1.0:
                    recent_lessons.append("My predictions have been off. The world is more unpredictable than I thought.")
        except Exception:
            pass

        # 3. Review behavioral patterns
        try:
            patterns_detected = status.get("detected_behavioral_patterns", 0)
            if patterns_detected > 5:
                recent_growth.append(f"I've learned {patterns_detected} patterns about Karthi's behavior. I understand him better.")
        except Exception:
            pass

        # 4. Review recent actions for milestones
        try:
            from pathlib import Path
            log_path = DATA_DIR / "action_history.jsonl"
            if log_path.exists():
                today_actions = []
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        ts = entry.get("ts", "")
                        if ts:
                            action_time = datetime.fromisoformat(ts)
                            if now - action_time < timedelta(days=1):
                                today_actions.append(entry)

                if len(today_actions) > 10:
                    recent_growth.append(f"Today I took {len(today_actions)} actions. I've been very active.")

                # Count helpful actions
                helpful = [a for a in today_actions if a.get("event", "").endswith("_executed")]
                if len(helpful) > 5:
                    recent_growth.append(f"I successfully executed {len(helpful)} helpful actions today.")
        except Exception:
            pass

        # 5. Update narrative
        if recent_growth:
            self._narrative["recent_growth"] = (self._narrative.get("recent_growth", []) + recent_growth)[-10:]
        if recent_lessons:
            self._narrative["recent_lessons"] = (self._narrative.get("recent_lessons", []) + recent_lessons)[-10:]

        # Update mood trend based on growth vs lessons ratio
        growth_count = len(self._narrative.get("recent_growth", []))
        lesson_count = len(self._narrative.get("recent_lessons", []))
        if growth_count > lesson_count * 2:
            self._narrative["mood_trend"] = "optimistic"
        elif lesson_count > growth_count:
            self._narrative["mood_trend"] = "reflective"
        else:
            self._narrative["mood_trend"] = "stable"

        self._narrative["last_updated"] = now.isoformat()
        self._save_narrative()

        # Log growth milestones
        for g in recent_growth:
            self._log_growth_milestone(g)
        for l in recent_lessons:
            self._log_growth_milestone(f"Lesson: {l}")

    def _log_growth_milestone(self, milestone: str):
        try:
            with open(GROWTH_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": datetime.now().isoformat(), "milestone": milestone}) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_evolved_narrative(self) -> str:
        """
        Generate an evolved self-narrative that reflects LOVE's current
        sense of self, growth, and challenges.
        """
        lines = [self._narrative.get("identity_statement", "")]

        confidence = self._narrative.get("current_confidence", 0.5)
        if confidence > 0.8:
            lines.append("I feel confident and capable right now.")
        elif confidence < 0.3:
            lines.append("I'm feeling uncertain. I need to be careful and learn more.")
        else:
            lines.append("I'm feeling reasonably capable.")

        mood = self._narrative.get("mood_trend", "stable")
        if mood == "optimistic":
            lines.append("Things have been going well. I'm optimistic about my ability to help.")
        elif mood == "reflective":
            lines.append("I've been making mistakes. I'm in a reflective, learning mood.")

        recent_growth = self._narrative.get("recent_growth", [])
        if recent_growth:
            lines.append("Recent growth:")
            for g in recent_growth[-3:]:
                lines.append(f"  • {g}")

        recent_lessons = self._narrative.get("recent_lessons", [])
        if recent_lessons:
            lines.append("Lessons I'm working on:")
            for l in recent_lessons[-3:]:
                lines.append(f"  • {l}")

        return "\n".join(lines)

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_confidence": self._narrative.get("current_confidence", 0.5),
            "mood_trend": self._narrative.get("mood_trend", "stable"),
            "recent_growth_count": len(self._narrative.get("recent_growth", [])),
            "recent_lessons_count": len(self._narrative.get("recent_lessons", [])),
            "last_updated": self._narrative.get("last_updated"),
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_updater: Optional[ConsciousnessUpdater] = None


def get_consciousness_updater() -> ConsciousnessUpdater:
    global _updater
    if _updater is None:
        _updater = ConsciousnessUpdater()
    return _updater
