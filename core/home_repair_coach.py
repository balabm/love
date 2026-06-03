"""
LOVE Home Repair Coach — Practical Home Intelligence (Modern AI Pattern)

Most people ignore home repairs until they break. This coach:

1. REPAIR TRACKING
   - Record home repair moments and their characteristics
   - Track repair types (maintenance, fix, upgrade, prevent, learn, teach)
   - Log confidence, skill, preparation, safety, and completion of repairs

2. PATTERN ANALYSIS
   - Identify the user's repair profile (avoidant, overwhelmed, developing, capable)
   - Find repair patterns that create confidence vs fear
   - Detect chronic home neglect and its costs

3. CAPABILITY BUILDING
   - Suggest practices for building repair confidence
   - Provide frameworks for safe, effective home maintenance
   - Recommend practices for learning practical skills

4. HOME MASTERY CULTIVATION
   - Track the correlation between repair practice and home quality
   - Alert when outsourcing is replacing capability
   - Celebrate moments of genuine home competence

Architecture:
- record_repair(task, type, confidence, skill, preparation, safety, completion): Log repair
- get_repair_stats(): Get repair pattern analysis
- get_repair_suggestion(capacity, context): Get suggestion
- get_repair_score(): Calculate overall repair health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "home_repair_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REPAIR_LOG = DATA_DIR / "repairs.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RepairEntry:
    """A tracked home repair moment."""
    entry_id: str = ""
    task: str = ""  # what was repaired
    repair_type: str = ""  # maintenance, fix, upgrade, prevent, learn, teach
    confidence: float = 0.0  # 0-1
    skill: float = 0.0  # 0-1
    preparation: float = 0.0  # 0-1
    safety: float = 0.0  # 0-1
    completion: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HomeRepairCoach:
    """
    Intelligent home repair coach with avoidance detection and home mastery cultivation.
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
            "avg_confidence": 0.0,
            "avg_completion": 0.0,
            "neglect_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_repair(self, task: str = "", repair_type: str = "", confidence: float = 0.0, skill: float = 0.0, preparation: float = 0.0, safety: float = 0.0, completion: float = 0.0, learning: float = 0.0, notes: str = "") -> RepairEntry:
        """Record a home repair moment."""
        entry_id = f"rep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RepairEntry(
            entry_id=entry_id,
            task=task or "unspecified",
            repair_type=repair_type or "fix",
            confidence=confidence,
            skill=skill,
            preparation=preparation,
            safety=safety,
            completion=completion,
            learning=learning,
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

    def get_repair_stats(self) -> Dict[str, Any]:
        """Get repair pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "confidence_sum": 0.0, "skill_sum": 0.0, "completion_sum": 0.0})
        for e in self._entries:
            by_type[e.repair_type]["count"] += 1
            by_type[e.repair_type]["confidence_sum"] += e.confidence
            by_type[e.repair_type]["skill_sum"] += e.skill
            by_type[e.repair_type]["completion_sum"] += e.completion

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_confidence": round(data["confidence_sum"] / count, 2),
                "avg_skill": round(data["skill_sum"] / count, 2),
                "avg_completion": round(data["completion_sum"] / count, 2),
            }

        # Confidence analysis
        high_conf = [e for e in self._entries if e.confidence > 0.7]
        low_conf = [e for e in self._entries if e.confidence < 0.4]
        if high_conf and low_conf:
            high_conf_comp = sum(e.completion for e in high_conf) / len(high_conf)
            low_conf_comp = sum(e.completion for e in low_conf) / len(low_conf)
            high_conf_saf = sum(e.safety for e in high_conf) / len(high_conf)
            low_conf_saf = sum(e.safety for e in low_conf) / len(low_conf)
        else:
            high_conf_comp = 0
            low_conf_comp = 0
            high_conf_saf = 0
            low_conf_saf = 0

        # Preparation analysis
        high_prep = [e for e in self._entries if e.preparation > 0.7]
        low_prep = [e for e in self._entries if e.preparation < 0.4]
        if high_prep and low_prep:
            high_prep_comp = sum(e.completion for e in high_prep) / len(high_prep)
            low_prep_comp = sum(e.completion for e in low_prep) / len(low_prep)
        else:
            high_prep_comp = 0
            low_prep_comp = 0

        # Neglect risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_conf = sum(e.confidence for e in recent) / len(recent)
            recent_comp = sum(e.completion for e in recent) / len(recent)
            neglect_risk = recent_conf < 0.3 and recent_comp < 0.3
        else:
            neglect_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "confidence_impact": {
                "high_confidence_completion": round(high_conf_comp, 2),
                "low_confidence_completion": round(low_conf_comp, 2),
                "high_confidence_safety": round(high_conf_saf, 2),
                "low_confidence_safety": round(low_conf_saf, 2),
            },
            "preparation_effect": {
                "high_preparation_completion": round(high_prep_comp, 2),
                "low_preparation_completion": round(low_prep_comp, 2),
            },
            "neglect_risk": neglect_risk,
            "avg_confidence": round(sum(e.confidence for e in self._entries) / len(self._entries), 2),
            "avg_completion": round(sum(e.completion for e in self._entries) / len(self._entries), 2),
        }

    def get_repair_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get repair suggestion."""
        suggestions = [
            "Most people are afraid of their own home. A dripping tap. A loose tile. A stuck window. They call someone. They wait. They pay. And they never learn. Your home is not a mystery. It's a machine. And machines can be understood.",
            "Start small. Not the roof. Not the wiring. A squeaky door. A loose handle. A clogged drain. Small repairs build confidence. Confidence builds skill. Skill builds capability. And capability builds freedom.",
            "Learn before you do. Watch a video. Read a manual. Ask someone who knows. Then do it. The person who repairs without learning is the person who creates bigger problems. Learn first. Do second.",
            "Tools matter. Buy good ones. Not many. A basic set. A hammer. A screwdriver set. A wrench. A tape measure. Pliers. A level. Good tools make good work. And good work makes good confidence.",
            "Safety first. Always. Turn off the water. Turn off the power. Wear glasses. Wear gloves. Use the right tool. The person who repairs unsafely is not brave. They're reckless. And recklessness has consequences.",
            "Keep a home journal. What you did. When. What worked. What didn't. What you learned. The journal is your teacher. Your memory. Your guide. The home that is journaled is the home that is understood.",
            "Prevent before you repair. The squeaky hinge before it breaks. The crack before it spreads. The filter before it clogs. Prevention is cheaper. Easier. And more satisfying. The proactive homeowner is the happy homeowner.",
            "Teach someone. Your child. Your partner. Your friend. Teaching is the best learning. It forces you to understand. To explain. To demonstrate. And it creates a legacy of capability.",
            "Celebrate the fix. Not just the big ones. The small ones too. The door that closes smoothly. The tap that doesn't drip. The light that works. These are victories. They matter. They build you.",
            "The person who repairs their own home is not saving money. They're building competence. They're creating independence. They're saying 'I can.' And that 'I can' extends beyond the home. Into everything."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One small fix. One tool learned. One video watched. One safety check made. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A planned repair. A proper preparation. A safe completion. A lesson learned. Medium competence."
        else:
            capacity_note = "Good capacity. Deep home mastery work. A systematic practice of repair, maintenance, prevention, and teaching. You have the strength to hold your home together."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Home repair is not about being handy. It's about being capable. Most people outsource their home. They call the plumber for a dripping tap. The electrician for a dead outlet. The carpenter for a loose shelf. And they pay. They wait. And they never learn. The work of home repair coaching is about understanding that your home is your responsibility. That the things you depend on are things you can understand. That the skills you need are skills you can learn. And that the person who repairs their own home is not just saving money. They're building competence. They're creating independence. They're saying 'I can figure this out.' And that belief is the foundation of all capability."
        }

    def get_repair_score(self) -> int:
        """Calculate overall repair health (0-100)."""
        if not self._entries:
            return 25

        avg_conf = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_skill = sum(e.skill for e in self._entries) / len(self._entries)
        avg_prep = sum(e.preparation for e in self._entries) / len(self._entries)
        avg_safe = sum(e.safety for e in self._entries) / len(self._entries)
        avg_comp = sum(e.completion for e in self._entries) / len(self._entries)
        avg_learn = sum(e.learning for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_conf = sum(e.confidence for e in recent) / len(recent)
            recent_comp = sum(e.completion for e in recent) / len(recent)
        else:
            recent_conf = 0
            recent_comp = 0

        # Neglect penalty
        neglect_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_conf_30 = sum(e.confidence for e in last_30) / len(last_30)
            recent_comp_30 = sum(e.completion for e in last_30) / len(last_30)
            if recent_conf_30 < 0.3 and recent_comp_30 < 0.3:
                neglect_penalty = 15

        # Type variety
        unique_types = len(set(e.repair_type for e in self._entries))

        score = (avg_conf * 25) + (avg_skill * 15) + (avg_prep * 10) + (avg_safe * 15) + (avg_comp * 15) + (avg_learn * 10) + (recent_conf * 5) + (recent_comp * 5) + (unique_types * 2) - neglect_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_confidence"] = round(sum(e.confidence for e in self._entries) / len(self._entries), 2)
            self._stats["avg_completion"] = round(sum(e.completion for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_conf = sum(e.confidence for e in recent) / len(recent)
                recent_comp = sum(e.completion for e in recent) / len(recent)
                self._stats["neglect_risk"] = recent_conf < 0.3 and recent_comp < 0.3
            else:
                self._stats["neglect_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.home_repair_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.home_repair_coach")

    def _log_entry(self, entry: RepairEntry):
        try:
            with open(REPAIR_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "task": entry.task,
                    "repair_type": entry.repair_type,
                    "confidence": entry.confidence,
                    "completion": entry.completion,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.home_repair_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hrc_instance: Optional[HomeRepairCoach] = None
_hrc_lock = threading.Lock()


def get_home_repair_coach() -> HomeRepairCoach:
    global _hrc_instance
    with _hrc_lock:
        if _hrc_instance is None:
            _hrc_instance = HomeRepairCoach()
        return _hrc_instance
