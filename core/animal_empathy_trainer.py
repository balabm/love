"""
LOVE Animal Empathy Trainer — Interspecies Intelligence (Modern AI Pattern)

Most people project human emotions onto animals. This trainer:

1. EMPATHY TRACKING
   - Record animal empathy moments and their characteristics
   - Track empathy types (observation, interpretation, response, patience, curiosity, respect)
   - Log accuracy, connection, understanding, and growth of empathy

2. PATTERN ANALYSIS
   - Identify the user's empathy profile (projecting, assuming, developing, attuned)
   - Find empathy patterns that create connection vs misunderstanding
   - Detect chronic anthropomorphism and its costs

3. EMPATHY BUILDING
   - Suggest practices for understanding animal perspectives
   - Provide frameworks for reading animal body language
   - Recommend practices for responding to animal needs

4. INTERSPECIES UNDERSTANDING CULTIVATION
   - Track the correlation between empathy accuracy and animal wellbeing
   - Alert when projection is replacing observation
   - Celebrate moments of genuine cross-species understanding

Architecture:
- record_empathy(animal, type, accuracy, connection, understanding, growth): Log empathy
- get_empathy_stats(): Get empathy pattern analysis
- get_empathy_suggestion(capacity, context): Get suggestion
- get_empathy_score(): Calculate overall empathy health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "animal_empathy_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMPATHY_LOG = DATA_DIR / "empathies.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EmpathyEntry:
    """A tracked animal empathy moment."""
    entry_id: str = ""
    animal: str = ""  # what animal was observed
    empathy_type: str = ""  # observation, interpretation, response, patience, curiosity, respect
    accuracy: float = 0.0  # 0-1
    connection: float = 0.0  # 0-1
    understanding: float = 0.0  # 0-1
    growth: float = 0.0  # 0-1
    patience: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AnimalEmpathyTrainer:
    """
    Intelligent animal empathy trainer with anthropomorphism detection and interspecies understanding cultivation.
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
            "avg_accuracy": 0.0,
            "avg_understanding": 0.0,
            "projection_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_empathy(self, animal: str = "", empathy_type: str = "", accuracy: float = 0.0, connection: float = 0.0, understanding: float = 0.0, growth: float = 0.0, patience: float = 0.0, notes: str = "") -> EmpathyEntry:
        """Record an animal empathy moment."""
        entry_id = f"emp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = EmpathyEntry(
            entry_id=entry_id,
            animal=animal or "unspecified",
            empathy_type=empathy_type or "observation",
            accuracy=accuracy,
            connection=connection,
            understanding=understanding,
            growth=growth,
            patience=patience,
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

    def get_empathy_stats(self) -> Dict[str, Any]:
        """Get empathy pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "acc_sum": 0.0, "conn_sum": 0.0, "under_sum": 0.0})
        for e in self._entries:
            by_type[e.empathy_type]["count"] += 1
            by_type[e.empathy_type]["acc_sum"] += e.accuracy
            by_type[e.empathy_type]["conn_sum"] += e.connection
            by_type[e.empathy_type]["under_sum"] += e.understanding

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_accuracy": round(data["acc_sum"] / count, 2),
                "avg_connection": round(data["conn_sum"] / count, 2),
                "avg_understanding": round(data["under_sum"] / count, 2),
            }

        # Accuracy analysis
        high_acc = [e for e in self._entries if e.accuracy > 0.7]
        low_acc = [e for e in self._entries if e.accuracy < 0.4]
        if high_acc and low_acc:
            high_acc_conn = sum(e.connection for e in high_acc) / len(high_acc)
            low_acc_conn = sum(e.connection for e in low_acc) / len(low_acc)
            high_acc_grow = sum(e.growth for e in high_acc) / len(high_acc)
            low_acc_grow = sum(e.growth for e in low_acc) / len(low_acc)
        else:
            high_acc_conn = 0
            low_acc_conn = 0
            high_acc_grow = 0
            low_acc_grow = 0

        # Patience analysis
        high_pat = [e for e in self._entries if e.patience > 0.7]
        low_pat = [e for e in self._entries if e.patience < 0.4]
        if high_pat and low_pat:
            high_pat_under = sum(e.understanding for e in high_pat) / len(high_pat)
            low_pat_under = sum(e.understanding for e in low_pat) / len(low_pat)
        else:
            high_pat_under = 0
            low_pat_under = 0

        # Projection risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_acc = sum(e.accuracy for e in recent) / len(recent)
            recent_under = sum(e.understanding for e in recent) / len(recent)
            projection_risk = recent_acc < 0.3 and recent_under < 0.3
        else:
            projection_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "accuracy_impact": {
                "high_accuracy_connection": round(high_acc_conn, 2),
                "low_accuracy_connection": round(low_acc_conn, 2),
                "high_accuracy_growth": round(high_acc_grow, 2),
                "low_accuracy_growth": round(low_acc_grow, 2),
            },
            "patience_effect": {
                "high_patience_understanding": round(high_pat_under, 2),
                "low_patience_understanding": round(low_pat_under, 2),
            },
            "projection_risk": projection_risk,
            "avg_accuracy": round(sum(e.accuracy for e in self._entries) / len(self._entries), 2),
            "avg_understanding": round(sum(e.understanding for e in self._entries) / len(self._entries), 2),
        }

    def get_empathy_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get empathy suggestion."""
        suggestions = [
            "Animals are not small humans in fur coats. They have their own emotional languages. Their own social rules. Their own ways of being. The person who treats a dog like a baby is not empathizing. They're projecting.",
            "Watch before interpreting. Most people see an animal behavior and immediately explain it. 'He's sad.' 'She's mad.' Stop. Watch. What is the body actually doing? What is the context? What happened before? Observation first. Interpretation second.",
            "Learn their signals. Ears back means fear in dogs. Slow blinking means trust in cats. Raised hackles means arousal. Tail position communicates mood. These are not metaphors. They're data. Learn the data.",
            "Patience is the core of animal empathy. Animals operate on different timelines. They process slower. They decide slower. They trust slower. Rushing them is not empathy. It's impatience disguised as care. Wait. Let them come to you.",
            "Don't punish fear. Fear is information. The animal is telling you something is wrong. Punishing fear doesn't fix the problem. It destroys trust. Help them feel safe. That's empathy.",
            "Respect their 'no.' When an animal doesn't want to be touched. Doesn't want to play. Doesn't want to interact. That's a boundary. Respect it. The person who forces affection is not loving. They're violating.",
            "Notice their preferences. The cat who likes high perches. The dog who prefers gentle touch. The bird who wants to watch before joining. These are individual personalities. Not species stereotypes. See the individual.",
            "Empathy is not feeling sorry. It's understanding. The animal who is aggressive is not bad. They're scared. The animal who hides is not unfriendly. They're careful. Understanding the why is empathy. Judging the what is not.",
            "Spend time in their world. On the floor with the dog. At the window with the cat. In the field with the horse. See what they see. Smell what they smell. Hear what they hear. Their world is richer than you think.",
            "The person who truly empathizes with animals becomes more human. Because empathy is a muscle. And animals are the best trainers. They don't lie. They don't perform. They just are. And they teach us to just be."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One minute of watching. One behavior observed without interpreting. One boundary respected. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A body language study. A patient wait. A response adjusted to their signals. Medium empathy."
        else:
            capacity_note = "Good capacity. Deep interspecies work. A systematic practice of observation, understanding, and respect. You have the strength to truly see them."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Animal empathy is not about being nice to animals. It's about understanding them. Really understanding them. On their terms. In their language. From their perspective. Most people don't do this. They project human emotions onto animals. They interpret animal behavior through human social norms. They expect animals to understand human communication. And they wonder why the relationship feels limited. The work of animal empathy training is about learning to see animals as they are. About understanding that a dog is not a wolf who wants to please you. That a cat is not a small tiger who tolerates you. That every animal has their own species-specific needs, signals, and ways of being. And about developing the patience, observation skills, and humility to meet them where they are. Because the person who truly empathizes with animals doesn't just become a better pet owner. They become a more perceptive, patient, and present human being."
        }

    def get_empathy_score(self) -> int:
        """Calculate overall empathy health (0-100)."""
        if not self._entries:
            return 25

        avg_acc = sum(e.accuracy for e in self._entries) / len(self._entries)
        avg_conn = sum(e.connection for e in self._entries) / len(self._entries)
        avg_under = sum(e.understanding for e in self._entries) / len(self._entries)
        avg_grow = sum(e.growth for e in self._entries) / len(self._entries)
        avg_pat = sum(e.patience for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_acc = sum(e.accuracy for e in recent) / len(recent)
            recent_under = sum(e.understanding for e in recent) / len(recent)
        else:
            recent_acc = 0
            recent_under = 0

        # Projection penalty
        proj_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_acc_30 = sum(e.accuracy for e in last_30) / len(last_30)
            recent_under_30 = sum(e.understanding for e in last_30) / len(last_30)
            if recent_acc_30 < 0.3 and recent_under_30 < 0.3:
                proj_penalty = 15

        # Type variety
        unique_types = len(set(e.empathy_type for e in self._entries))

        score = (avg_acc * 25) + (avg_conn * 15) + (avg_under * 20) + (avg_grow * 10) + (avg_pat * 10) + (recent_acc * 5) + (recent_under * 5) + (unique_types * 2) - proj_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_accuracy"] = round(sum(e.accuracy for e in self._entries) / len(self._entries), 2)
            self._stats["avg_understanding"] = round(sum(e.understanding for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_acc = sum(e.accuracy for e in recent) / len(recent)
                recent_under = sum(e.understanding for e in recent) / len(recent)
                self._stats["projection_risk"] = recent_acc < 0.3 and recent_under < 0.3
            else:
                self._stats["projection_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.animal_empathy_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.animal_empathy_trainer")

    def _log_entry(self, entry: EmpathyEntry):
        try:
            with open(EMPATHY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "animal": entry.animal,
                    "empathy_type": entry.empathy_type,
                    "accuracy": entry.accuracy,
                    "understanding": entry.understanding,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.animal_empathy_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_aet_instance: Optional[AnimalEmpathyTrainer] = None
_aet_lock = threading.Lock()


def get_animal_empathy_trainer() -> AnimalEmpathyTrainer:
    global _aet_instance
    with _aet_lock:
        if _aet_instance is None:
            _aet_instance = AnimalEmpathyTrainer()
        return _aet_instance
