"""
LOVE Retirement Meaning Architect — Post-Career Intelligence (Modern AI Pattern)

Most retirees drift without purpose. This architect:

1. RETIREMENT TRACKING
   - Record retirement moments and their characteristics
   - Track retirement types (structure, contribution, learning, connection, health, legacy)
   - Log structure, contribution, learning, connection, health, and legacy

2. PATTERN ANALYSIS
   - Identify the user's retirement profile (drifting, exploring, building, thriving)
   - Find retirement patterns that create meaning vs emptiness
   - Detect chronic drift and its costs

3. MEANING BUILDING
   - Suggest practices for designing a meaningful retirement
   - Provide frameworks for contribution and legacy
   - Recommend practices for connection and health

4. RETIREMENT THRIVING CULTIVATION
   - Track the correlation between contribution and retirement satisfaction
   - Alert when drift is replacing meaning
   - Celebrate moments of genuine retirement flourishing

Architecture:
- record_retirement(activity, type, structure, contribution, learning, connection, health, legacy): Log retirement
- get_retirement_stats(): Get retirement pattern analysis
- get_retirement_suggestion(capacity, context): Get suggestion
- get_retirement_score(): Calculate overall retirement health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "retirement_meaning_architect"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RETIREMENT_LOG = DATA_DIR / "retirements.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RetirementEntry:
    """A tracked retirement moment."""
    entry_id: str = ""
    activity: str = ""  # what was the activity
    retirement_type: str = ""  # structure, contribution, learning, connection, health, legacy
    structure: float = 0.0  # 0-1
    contribution: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    health: float = 0.0  # 0-1
    legacy: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RetirementMeaningArchitect:
    """
    Intelligent retirement meaning architect with drift detection and retirement thriving cultivation.
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
            "avg_contribution": 0.0,
            "avg_joy": 0.0,
            "drift_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_retirement(self, activity: str = "", retirement_type: str = "", structure: float = 0.0, contribution: float = 0.0, learning: float = 0.0, connection: float = 0.0, health: float = 0.0, legacy: float = 0.0, joy: float = 0.0, notes: str = "") -> RetirementEntry:
        """Record a retirement moment."""
        entry_id = f"rtm_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RetirementEntry(
            entry_id=entry_id,
            activity=activity or "unspecified",
            retirement_type=retirement_type or "structure",
            structure=structure,
            contribution=contribution,
            learning=learning,
            connection=connection,
            health=health,
            legacy=legacy,
            joy=joy,
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

    def get_retirement_stats(self) -> Dict[str, Any]:
        """Get retirement pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "contribution_sum": 0.0, "joy_sum": 0.0, "legacy_sum": 0.0})
        for e in self._entries:
            by_type[e.retirement_type]["count"] += 1
            by_type[e.retirement_type]["contribution_sum"] += e.contribution
            by_type[e.retirement_type]["joy_sum"] += e.joy
            by_type[e.retirement_type]["legacy_sum"] += e.legacy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_contribution": round(data["contribution_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
                "avg_legacy": round(data["legacy_sum"] / count, 2),
            }

        # Contribution analysis
        high_con = [e for e in self._entries if e.contribution > 0.7]
        low_con = [e for e in self._entries if e.contribution < 0.4]
        if high_con and low_con:
            high_con_joy = sum(e.joy for e in high_con) / len(high_con)
            low_con_joy = sum(e.joy for e in low_con) / len(low_con)
            high_con_health = sum(e.health for e in high_con) / len(high_con)
            low_con_health = sum(e.health for e in low_con) / len(low_con)
        else:
            high_con_joy = 0
            low_con_joy = 0
            high_con_health = 0
            low_con_health = 0

        # Structure analysis
        high_str = [e for e in self._entries if e.structure > 0.7]
        low_str = [e for e in self._entries if e.structure < 0.4]
        if high_str and low_str:
            high_str_joy = sum(e.joy for e in high_str) / len(high_str)
            low_str_joy = sum(e.joy for e in low_str) / len(low_str)
        else:
            high_str_joy = 0
            low_str_joy = 0

        # Drift risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_con = sum(e.contribution for e in recent) / len(recent)
            recent_str = sum(e.structure for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
            drift_risk = recent_con < 0.3 and recent_str < 0.3 and recent_joy < 0.3
        else:
            drift_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "contribution_impact": {
                "high_contribution_joy": round(high_con_joy, 2),
                "low_contribution_joy": round(low_con_joy, 2),
                "high_contribution_health": round(high_con_health, 2),
                "low_contribution_health": round(low_con_health, 2),
            },
            "structure_effect": {
                "high_structure_joy": round(high_str_joy, 2),
                "low_structure_joy": round(low_str_joy, 2),
            },
            "drift_risk": drift_risk,
            "avg_contribution": round(sum(e.contribution for e in self._entries) / len(self._entries), 2),
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
        }

    def get_retirement_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get retirement suggestion."""
        suggestions = [
            "Most retirees drift. They wake up without structure. Without demands. Without purpose. And they wonder why they feel empty. Why they feel lost. Why they feel like they're wasting the final third of their life. The answer is simple: they stopped building. And humans need to build.",
            "Structure is not prison. It's freedom. The person who has no schedule is not free. They're a victim of impulse. Of inertia. Of drift. Create a schedule. Not a prison. A rhythm. A pattern. Something that gives your days shape and your weeks meaning. The empty calendar is not liberation. It's a vacuum.",
            "Contribute. Not because you have to. Because you can. Your skills. Your experience. Your wisdom. Your time. The world still needs them. Mentor. Volunteer. Consult. Create. Teach. The person who contributes in retirement is the person who stays alive. Literally. Contribution correlates with longevity. And more importantly, with meaning.",
            "Keep learning. Not to get a job. To stay alive. New skills. New subjects. New domains. The brain that stops learning starts dying. Take a class. Learn a language. Study history. Understand science. The person who keeps learning keeps growing. At any age. Until the very end.",
            "Connect deeply. Not superficially. Not passively. Really connect. With your partner. With old friends. With new people. With younger generations. Connection is not a luxury in retirement. It's oxygen. The person who connects thrives. The person who isolates withers.",
            "Take care of your body. Not to look good. To feel good. To have energy. To have options. Retirement without health is not retirement. It's confinement. Move every day. Eat well. Sleep well. The body is the vehicle for everything you want to do. Maintain it.",
            "Build a legacy. Not for others. For yourself. What do you want to leave behind? A book? A garden? A relationship? A memory? A changed life? Legacy is not about fame. It's about mattering. About knowing your existence made a difference. Start building it now.",
            "Be patient with yourself. Retirement is a new identity. A new life. A new chapter. It takes time to figure out. You will try things that don't work. You will feel lost sometimes. That's normal. Keep exploring. Keep building. Keep moving forward.",
            "The person who thrives in retirement is not someone who stopped working. They're someone who started living differently. Who found new ways to contribute. To learn. To connect. To grow. Who understood that retirement is not the end of purpose. It's the beginning of choosing your own purpose. And that choice - made consciously, built daily, lived fully - is the most meaningful work of all."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One schedule created. One contribution made. One friend called. One walk taken. One page written. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A rhythm found. A skill building. A relationship deepening. A health habit formed. A legacy started. Medium thriving."
        else:
            capacity_note = "Good capacity. Deep retirement design. A systematic practice of structure, contribution, learning, connection, health, and legacy. You have the strength to make these years your best years."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Retirement meaning architecture is not about filling time. It's about building purpose. Most retirees drift. They lose structure. They lose contribution. They lose meaning. And they decline - physically, mentally, emotionally. The work of retirement meaning architecture coaching is about understanding that retirement is not the end of work. It's the beginning of chosen work. That structure is freedom. That contribution is longevity. That learning is life. That connection is oxygen. And that the person who designs their retirement with intention finds a chapter of life that can be the most meaningful of all."
        }

    def get_retirement_score(self) -> int:
        """Calculate overall retirement health (0-100)."""
        if not self._entries:
            return 25

        avg_str = sum(e.structure for e in self._entries) / len(self._entries)
        avg_con = sum(e.contribution for e in self._entries) / len(self._entries)
        avg_learn = sum(e.learning for e in self._entries) / len(self._entries)
        avg_conn = sum(e.connection for e in self._entries) / len(self._entries)
        avg_health = sum(e.health for e in self._entries) / len(self._entries)
        avg_legacy = sum(e.legacy for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_con = sum(e.contribution for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
        else:
            recent_con = 0
            recent_joy = 0

        # Drift penalty
        drift_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_con_30 = sum(e.contribution for e in last_30) / len(last_30)
            recent_str_30 = sum(e.structure for e in last_30) / len(last_30)
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            if recent_con_30 < 0.3 and recent_str_30 < 0.3 and recent_joy_30 < 0.3:
                drift_penalty = 15

        # Type variety
        unique_types = len(set(e.retirement_type for e in self._entries))

        score = (avg_str * 15) + (avg_con * 25) + (avg_learn * 10) + (avg_conn * 10) + (avg_health * 15) + (avg_legacy * 10) + (avg_joy * 10) + (recent_con * 5) + (recent_joy * 5) + (unique_types * 2) - drift_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_contribution"] = round(sum(e.contribution for e in self._entries) / len(self._entries), 2)
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_con = sum(e.contribution for e in recent) / len(recent)
                recent_str = sum(e.structure for e in recent) / len(recent)
                recent_joy = sum(e.joy for e in recent) / len(recent)
                self._stats["drift_risk"] = recent_con < 0.3 and recent_str < 0.3 and recent_joy < 0.3
            else:
                self._stats["drift_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.retirement_meaning_architect")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.retirement_meaning_architect")

    def _log_entry(self, entry: RetirementEntry):
        try:
            with open(RETIREMENT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "retirement_type": entry.retirement_type,
                    "contribution": entry.contribution,
                    "joy": entry.joy,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.retirement_meaning_architect")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rma_instance: Optional[RetirementMeaningArchitect] = None
_rma_lock = threading.Lock()


def get_retirement_meaning_architect() -> RetirementMeaningArchitect:
    global _rma_instance
    with _rma_lock:
        if _rma_instance is None:
            _rma_instance = RetirementMeaningArchitect()
        return _rma_instance
