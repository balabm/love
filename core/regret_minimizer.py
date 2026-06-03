"""
LOVE Regret Minimizer — Life Optimization Intelligence (Modern AI Pattern)

Most people regret more than they need to. This minimizer:

1. REGRET TRACKING
   - Record regret moments and their characteristics
   - Track regret types (action, inaction, commission, omission, timing)
   - Log intensity, learning, and resolution of regrets

2. PATTERN ANALYSIS
   - Identify the user's regret profile (chronic, reflective, learning, resolved)
   - Find regret patterns that motivate vs paralyze
   - Detect chronic regret and its costs

3. REGRET MINIMIZATION
   - Suggest practices for reducing future regrets
   - Provide frameworks for pre-mortem and decision review
   - Recommend practices for learning from regret without dwelling

4. ANTICIPATED REGRET CULTIVATION
   - Track the correlation between anticipated regret and better decisions
   - Alert when regret is becoming chronic or paralyzing
   - Celebrate moments of genuine regret-free action

Architecture:
- record_regret(regret, type, intensity, learning, resolution): Log regret
- get_regret_stats(): Get regret pattern analysis
- get_regret_suggestion(capacity, context): Get suggestion
- get_regret_score(): Calculate overall regret health
"""

import json
import math
import random
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "regret_minimizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REGRET_LOG = DATA_DIR / "regrets.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RegretEntry:
    """A tracked regret moment."""
    entry_id: str = ""
    regret: str = ""  # what was regretted
    regret_type: str = ""  # action, inaction, commission, omission, timing
    intensity: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    resolution: float = 0.0  # 0-1
    anticipation: float = 0.0  # 0-1 did you anticipate this?
    action_taken: float = 0.0  # 0-1 did you act to fix it?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RegretMinimizer:
    """
    Intelligent regret minimizer with chronic regret detection and life optimization cultivation.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
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
        self._entries: deque = deque(maxlen=300)
        self._stats = {
            "total_entries": 0,
            "avg_intensity": 0.0,
            "avg_resolution": 0.0,
            "chronic_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_regret(self, regret: str = "", regret_type: str = "", intensity: float = 0.0, learning: float = 0.0, resolution: float = 0.0, anticipation: float = 0.0, action_taken: float = 0.0, notes: str = "") -> RegretEntry:
        """Record a regret moment."""
        entry_id = f"rgr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RegretEntry(
            entry_id=entry_id,
            regret=regret or "unspecified",
            regret_type=regret_type or "inaction",
            intensity=intensity,
            learning=learning,
            resolution=resolution,
            anticipation=anticipation,
            action_taken=action_taken,
            notes=notes,
        )

        with self._lock:
            self._entries.append(entry)
            self._stats["total_entries"] += 1
            self._update_stats()

        self._save_stats()
        self._log_entry(entry)

        return entry

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_regret_stats(self) -> Dict[str, Any]:
        """Get regret pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "learning_sum": 0.0, "resolution_sum": 0.0})
        for e in self._entries:
            by_type[e.regret_type]["count"] += 1
            by_type[e.regret_type]["intensity_sum"] += e.intensity
            by_type[e.regret_type]["learning_sum"] += e.learning
            by_type[e.regret_type]["resolution_sum"] += e.resolution

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_learning": round(data["learning_sum"] / count, 2),
                "avg_resolution": round(data["resolution_sum"] / count, 2),
            }

        # Intensity analysis
        high_int = [e for e in self._entries if e.intensity > 0.7]
        low_int = [e for e in self._entries if e.intensity < 0.4]
        if high_int and low_int:
            high_int_learn = sum(e.learning for e in high_int) / len(high_int)
            low_int_learn = sum(e.learning for e in low_int) / len(low_int)
            high_int_res = sum(e.resolution for e in high_int) / len(high_int)
            low_int_res = sum(e.resolution for e in low_int) / len(low_int)
        else:
            high_int_learn = 0
            low_int_learn = 0
            high_int_res = 0
            low_int_res = 0

        # Anticipation analysis
        high_ant = [e for e in self._entries if e.anticipation > 0.7]
        low_ant = [e for e in self._entries if e.anticipation < 0.4]
        if high_ant and low_ant:
            high_ant_act = sum(e.action_taken for e in high_ant) / len(high_ant)
            low_ant_act = sum(e.action_taken for e in low_ant) / len(low_ant)
        else:
            high_ant_act = 0
            low_ant_act = 0

        # Chronic risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_intensity = sum(e.intensity for e in recent) / len(recent)
            recent_res = sum(e.resolution for e in recent) / len(recent)
            chronic_risk = recent_intensity > 0.7 and recent_res < 0.3
        else:
            chronic_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "intensity_impact": {
                "high_intensity_learning": round(high_int_learn, 2),
                "low_intensity_learning": round(low_int_learn, 2),
                "high_intensity_resolution": round(high_int_res, 2),
                "low_intensity_resolution": round(low_int_res, 2),
            },
            "anticipation_effect": {
                "high_anticipation_action": round(high_ant_act, 2),
                "low_anticipation_action": round(low_ant_act, 2),
            },
            "chronic_risk": chronic_risk,
            "avg_intensity": round(sum(e.intensity for e in self._entries) / len(self._entries), 2),
            "avg_resolution": round(sum(e.resolution for e in self._entries) / len(self._entries), 2),
        }

    def get_regret_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get regret suggestion."""
        suggestions = [
            "Regret is a teacher. Not a jailer. Learn the lesson. Then release the regret. The person who carries every regret is too heavy to move forward.",
            "Most people regret what they didn't do more than what they did. The risk not taken. The word not spoken. The chance not seized. Inaction haunts more than action.",
            "Do a pre-mortem. Before you decide, imagine it's a year later and you regret it. What would you regret? Why? Now decide with that knowledge. It's not too late. You're just imagining it is.",
            "You can't change the past. But you can change what you do with it. The person who learns from regret grows. The person who dwells on it shrinks. Same regret. Different response.",
            "Anticipated regret is a decision tool. If you know you'll regret not doing something, that's information. Use it. The future you is giving you advice. Listen.",
            "The things you regret are usually the things that mattered. Not the safe choices. Not the comfortable paths. The scary ones. The uncertain ones. The ones where you risked something. That's where growth lives.",
            "Forgive yourself for not knowing what you didn't know. You made the best decision you could with the information you had. That's all anyone can do. Don't punish yourself for being human.",
            "Regret about the past is wasted energy. Action in the present is the only cure. If you regret not calling someone, call them now. If you regret not starting, start now. The present is the only time you can act.",
            "The person who lives without regret is not the person who never makes mistakes. It's the person who makes mistakes, learns from them, and moves on. Regret-free living is not about perfection. It's about resilience.",
            "Your deathbed self knows what matters. Ask them. What will they regret? Not the email you didn't send. Not the meeting you missed. The love you didn't express. The risk you didn't take. The life you didn't live. Live that life now."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small action to prevent one future regret. One forgiveness of one past regret. One breath of forward motion. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A pre-mortem for one decision. A regret review. A lesson extraction. Medium minimization."
        else:
            capacity_note = "Good capacity. Deep regret work. A systematic shift from dwelling to learning. You have the strength to live without unnecessary regret."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Regret is the most painful emotion because it's unchangeable. You can't go back. You can't undo it. And that finality makes it weigh more than any other feeling. But regret is also optional. Not because you can change the past. But because you can change your relationship with it. You can learn from it. You can forgive yourself for it. You can use it to make better future decisions. And you can minimize future regret by anticipating it. By asking yourself: what will I regret? And then doing the thing that avoids that regret. The work of regret minimization is not about never making mistakes. It's about making the mistakes that matter. The ones you learn from. The ones that move you forward. And it's about releasing the ones that don't. Because carrying every regret is too heavy. And you have too much living left to do."
        }

    def get_regret_score(self) -> int:
        """Calculate overall regret health (0-100)."""
        if not self._entries:
            return 25

        avg_int = sum(e.intensity for e in self._entries) / len(self._entries)
        avg_learn = sum(e.learning for e in self._entries) / len(self._entries)
        avg_res = sum(e.resolution for e in self._entries) / len(self._entries)
        avg_ant = sum(e.anticipation for e in self._entries) / len(self._entries)
        avg_act = sum(e.action_taken for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_int = sum(e.intensity for e in recent) / len(recent)
            recent_res = sum(e.resolution for e in recent) / len(recent)
        else:
            recent_int = 0
            recent_res = 0

        # Chronic penalty
        chronic_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_int_30 = sum(e.intensity for e in last_30) / len(last_30)
            recent_res_30 = sum(e.resolution for e in last_30) / len(last_30)
            if recent_int_30 > 0.7 and recent_res_30 < 0.3:
                chronic_penalty = 15

        # Type variety
        unique_types = len(set(e.regret_type for e in self._entries))

        score = (avg_learn * 25) + (avg_res * 25) + (avg_ant * 15) + (avg_act * 15) + (recent_res * 10) + (recent_res * 5) + (unique_types * 2) - (avg_int * 15) - chronic_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intensity"] = round(sum(e.intensity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_resolution"] = round(sum(e.resolution for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_intensity = sum(e.intensity for e in recent) / len(recent)
                recent_res = sum(e.resolution for e in recent) / len(recent)
                self._stats["chronic_risk"] = recent_intensity > 0.7 and recent_res < 0.3
            else:
                self._stats["chronic_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.regret_minimizer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.regret_minimizer")

    def _log_entry(self, entry: RegretEntry):
        try:
            with open(REGRET_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "regret": entry.regret,
                    "regret_type": entry.regret_type,
                    "intensity": entry.intensity,
                    "resolution": entry.resolution,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.regret_minimizer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rm_instance: Optional[RegretMinimizer] = None
_rm_lock = threading.Lock()


def get_regret_minimizer() -> RegretMinimizer:
    global _rm_instance
    with _rm_lock:
        if _rm_instance is None:
            _rm_instance = RegretMinimizer()
        return _rm_instance
