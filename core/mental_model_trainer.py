"""
LOVE Mental Model Trainer — Framework Intelligence (Modern AI Pattern)

Most people think without frameworks. This trainer:

1. MODEL TRACKING
   - Record mental model usage and their characteristics
   - Track model types (inversion, second_order, pareto, opportunity_cost, compounding, margin_of_safety)
   - Log application, effectiveness, and integration of models

2. PATTERN ANALYSIS
   - Identify the user's model profile (sparse, developing, integrated, masterful)
   - Find model patterns that clarify vs complicate thinking
   - Detect chronic model absence and its costs

3. MODEL TRAINING
   - Suggest practices for applying mental models to decisions
   - Provide frameworks for building a latticework of models
   - Recommend practices for cross-domain model transfer

4. COGNITIVE CLARITY CULTIVATION
   - Track the correlation between model usage and decision quality
   - Alert when thinking is becoming model-less and reactive
   - Celebrate moments of genuine multi-model thinking

Architecture:
- record_model(situation, type, application, effectiveness, integration): Log model
- get_model_stats(): Get model pattern analysis
- get_model_suggestion(capacity, context): Get suggestion
- get_model_score(): Calculate overall model health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "mental_model_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MODEL_LOG = DATA_DIR / "models.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ModelEntry:
    """A tracked mental model usage."""
    entry_id: str = ""
    situation: str = ""  # what happened
    model_type: str = ""  # inversion, second_order, pareto, opportunity_cost, compounding, margin_of_safety
    application: float = 0.0  # 0-1 how well applied
    effectiveness: float = 0.0  # 0-1
    integration: float = 0.0  # 0-1 with other models
    cross_domain: float = 0.0  # 0-1 transferred across domains
    outcome: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MentalModelTrainer:
    """
    Intelligent mental model trainer with usage detection and cognitive clarity cultivation.
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
            "avg_application": 0.0,
            "avg_effectiveness": 0.0,
            "model_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_model(self, situation: str = "", model_type: str = "", application: float = 0.0, effectiveness: float = 0.0, integration: float = 0.0, cross_domain: float = 0.0, outcome: float = 0.0, notes: str = "") -> ModelEntry:
        """Record a mental model usage."""
        entry_id = f"mdl_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ModelEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            model_type=model_type or "general",
            application=application,
            effectiveness=effectiveness,
            integration=integration,
            cross_domain=cross_domain,
            outcome=outcome,
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

    def get_model_stats(self) -> Dict[str, Any]:
        """Get model pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "app_sum": 0.0, "eff_sum": 0.0, "int_sum": 0.0})
        for e in self._entries:
            by_type[e.model_type]["count"] += 1
            by_type[e.model_type]["app_sum"] += e.application
            by_type[e.model_type]["eff_sum"] += e.effectiveness
            by_type[e.model_type]["int_sum"] += e.integration

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_application": round(data["app_sum"] / count, 2),
                "avg_effectiveness": round(data["eff_sum"] / count, 2),
                "avg_integration": round(data["int_sum"] / count, 2),
            }

        # Application analysis
        high_app = [e for e in self._entries if e.application > 0.7]
        low_app = [e for e in self._entries if e.application < 0.4]
        if high_app and low_app:
            high_app_eff = sum(e.effectiveness for e in high_app) / len(high_app)
            low_app_eff = sum(e.effectiveness for e in low_app) / len(low_app)
            high_app_out = sum(e.outcome for e in high_app) / len(high_app)
            low_app_out = sum(e.outcome for e in low_app) / len(low_app)
        else:
            high_app_eff = 0
            low_app_eff = 0
            high_app_out = 0
            low_app_out = 0

        # Integration analysis
        high_int = [e for e in self._entries if e.integration > 0.7]
        low_int = [e for e in self._entries if e.integration < 0.4]
        if high_int and low_int:
            high_int_eff = sum(e.effectiveness for e in high_int) / len(high_int)
            low_int_eff = sum(e.effectiveness for e in low_int) / len(low_int)
        else:
            high_int_eff = 0
            low_int_eff = 0

        # Model risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_app = sum(e.application for e in recent) / len(recent)
            recent_eff = sum(e.effectiveness for e in recent) / len(recent)
            model_risk = recent_app < 0.3 and recent_eff < 0.3
        else:
            model_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "application_impact": {
                "high_application_effectiveness": round(high_app_eff, 2),
                "low_application_effectiveness": round(low_app_eff, 2),
                "high_application_outcome": round(high_app_out, 2),
                "low_application_outcome": round(low_app_out, 2),
            },
            "integration_effect": {
                "high_integration_effectiveness": round(high_int_eff, 2),
                "low_integration_effectiveness": round(low_int_eff, 2),
            },
            "model_risk": model_risk,
            "avg_application": round(sum(e.application for e in self._entries) / len(self._entries), 2),
            "avg_effectiveness": round(sum(e.effectiveness for e in self._entries) / len(self._entries), 2),
        }

    def get_model_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get model suggestion."""
        suggestions = [
            "Inversion: instead of asking how to succeed, ask how to fail. Then avoid those things. It's easier to not be stupid than to be brilliant. Avoiding failure is often the best path to success.",
            "Second-order thinking: ask what happens next. And then what? Most people think one move ahead. The person who thinks three moves ahead wins. Because they see consequences that others miss.",
            "Pareto principle: 80% of outcomes come from 20% of inputs. Find the 20%. Do more of that. Do less of the 80%. It's not about doing more. It's about doing the right things.",
            "Opportunity cost: everything you choose costs you everything else you could have chosen. The person who says yes to everything says no to what matters. Choose consciously. The price is real.",
            "Compounding: small improvements accumulate into massive results. Not linearly. Exponentially. The person who improves 1% daily is 37x better in a year. The person who declines 1% daily is nearly zero.",
            "Margin of safety: don't build systems that work perfectly. Build systems that work even when things go wrong. Because things will go wrong. The question is not if. It's when. And will you survive?",
            "Occam's razor: the simplest explanation is usually correct. Not always. But usually. Don't add complexity to explain what simplicity can explain. Complexity is often a sign of confusion, not sophistication.",
            "Hanlon's razor: never attribute to malice what can be explained by incompetence. Most bad things are not intentional. They're just people doing their best with limited information and skill. Assume incompetence first.",
            "The map is not the territory: your model of reality is not reality. It's a simplification. And simplifications are wrong by definition. Use models. But hold them lightly. Update them when the territory changes.",
            "Multi-model thinking: no single model explains everything. The person who uses one model is a hammer looking for nails. The person who uses many models sees the world more clearly. Build a latticework."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One mental model applied to one situation. One framework. One new lens. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A model applied to a real decision. A cross-domain transfer. A latticework addition. Medium training."
        else:
            capacity_note = "Good capacity. Deep model integration. A systematic latticework of mental models applied to complex decisions. You have the strength to think in frameworks."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Mental models are thinking tools. They're frameworks that help you understand reality. And most people think without them. They react. They follow intuition. They use the same mental hammer for every nail. And they wonder why their thinking is so often wrong. The person who has a latticework of mental models sees the world differently. They see inversion. They see second-order effects. They see opportunity costs. They see compounding. They see margins of safety. And they apply these models across domains. Not just in finance. Not just in relationships. Everywhere. Because reality doesn't respect domain boundaries. And neither should your thinking. The work of mental model training is about building that latticework. About having multiple lenses. About knowing when to use which one. And about recognizing that no single model is sufficient. The world is too complex for that."
        }

    def get_model_score(self) -> int:
        """Calculate overall model health (0-100)."""
        if not self._entries:
            return 25

        avg_app = sum(e.application for e in self._entries) / len(self._entries)
        avg_eff = sum(e.effectiveness for e in self._entries) / len(self._entries)
        avg_int = sum(e.integration for e in self._entries) / len(self._entries)
        avg_cross = sum(e.cross_domain for e in self._entries) / len(self._entries)
        avg_out = sum(e.outcome for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_app = sum(e.application for e in recent) / len(recent)
            recent_eff = sum(e.effectiveness for e in recent) / len(recent)
        else:
            recent_app = 0
            recent_eff = 0

        # Model penalty
        model_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_app_30 = sum(e.application for e in last_30) / len(last_30)
            recent_eff_30 = sum(e.effectiveness for e in last_30) / len(last_30)
            if recent_app_30 < 0.3 and recent_eff_30 < 0.3:
                model_penalty = 15

        # Type variety
        unique_types = len(set(e.model_type for e in self._entries))

        score = (avg_app * 20) + (avg_eff * 20) + (avg_int * 20) + (avg_cross * 15) + (avg_out * 10) + (recent_app * 5) + (recent_eff * 5) + (unique_types * 2) - model_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_application"] = round(sum(e.application for e in self._entries) / len(self._entries), 2)
            self._stats["avg_effectiveness"] = round(sum(e.effectiveness for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_app = sum(e.application for e in recent) / len(recent)
                recent_eff = sum(e.effectiveness for e in recent) / len(recent)
                self._stats["model_risk"] = recent_app < 0.3 and recent_eff < 0.3
            else:
                self._stats["model_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception:
            pass

    def _log_entry(self, entry: ModelEntry):
        try:
            with open(MODEL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "model_type": entry.model_type,
                    "application": entry.application,
                    "effectiveness": entry.effectiveness,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mmt_instance: Optional[MentalModelTrainer] = None
_mmt_lock = threading.Lock()


def get_mental_model_trainer() -> MentalModelTrainer:
    global _mmt_instance
    with _mmt_lock:
        if _mmt_instance is None:
            _mmt_instance = MentalModelTrainer()
        return _mmt_instance
