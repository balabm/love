"""
LOVE Seasonal Garden Planner — Cyclical Intelligence (Modern AI Pattern)

Most people garden the same way year-round. This planner:

1. SEASON TRACKING
   - Record seasonal garden moments and their characteristics
   - Track season types (spring_prep, summer_tend, autumn_harvest, winter_rest)
   - Log planning, execution, adaptation, and learning of seasonal work

2. PATTERN ANALYSIS
   - Identify the user's seasonal profile (reactive, habitual, developing, cyclical)
   - Find seasonal patterns that create harmony vs struggle
   - Detect chronic season-ignorance and its costs

3. PLANNING BUILDING
   - Suggest practices for seasonally-aware gardening
   - Provide frameworks for cyclical garden management
   - Recommend practices for working with nature's rhythms

4. CYCLICAL HARMONY CULTIVATION
   - Track the correlation between seasonal alignment and garden success
   - Alert when fighting the season is becoming the default
   - Celebrate moments of genuine seasonal flow

Architecture:
- record_season(phase, type, planning, execution, adaptation, learning): Log season
- get_season_stats(): Get season pattern analysis
- get_season_suggestion(capacity, context): Get suggestion
- get_season_score(): Calculate overall season health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "seasonal_garden_planner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEASON_LOG = DATA_DIR / "seasons.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SeasonEntry:
    """A tracked seasonal garden moment."""
    entry_id: str = ""
    phase: str = ""  # what phase was worked on
    season_type: str = ""  # spring_prep, summer_tend, autumn_harvest, winter_rest
    planning: float = 0.0  # 0-1
    execution: float = 0.0  # 0-1
    adaptation: float = 0.0  # 0-1
    learning: float = 0.0  # 0-1
    harmony: float = 0.0  # 0-1 working with or against the season?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SeasonalGardenPlanner:
    """
    Intelligent seasonal garden planner with season-ignorance detection and cyclical harmony cultivation.
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
            "avg_planning": 0.0,
            "avg_harmony": 0.0,
            "season_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_season(self, phase: str = "", season_type: str = "", planning: float = 0.0, execution: float = 0.0, adaptation: float = 0.0, learning: float = 0.0, harmony: float = 0.0, notes: str = "") -> SeasonEntry:
        """Record a seasonal garden moment."""
        entry_id = f"sea_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = SeasonEntry(
            entry_id=entry_id,
            phase=phase or "unspecified",
            season_type=season_type or "spring_prep",
            planning=planning,
            execution=execution,
            adaptation=adaptation,
            learning=learning,
            harmony=harmony,
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

    def get_season_stats(self) -> Dict[str, Any]:
        """Get season pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "planning_sum": 0.0, "execution_sum": 0.0, "harmony_sum": 0.0})
        for e in self._entries:
            by_type[e.season_type]["count"] += 1
            by_type[e.season_type]["planning_sum"] += e.planning
            by_type[e.season_type]["execution_sum"] += e.execution
            by_type[e.season_type]["harmony_sum"] += e.harmony

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_planning": round(data["planning_sum"] / count, 2),
                "avg_execution": round(data["execution_sum"] / count, 2),
                "avg_harmony": round(data["harmony_sum"] / count, 2),
            }

        # Planning analysis
        high_plan = [e for e in self._entries if e.planning > 0.7]
        low_plan = [e for e in self._entries if e.planning < 0.4]
        if high_plan and low_plan:
            high_plan_exec = sum(e.execution for e in high_plan) / len(high_plan)
            low_plan_exec = sum(e.execution for e in low_plan) / len(low_plan)
            high_plan_har = sum(e.harmony for e in high_plan) / len(high_plan)
            low_plan_har = sum(e.harmony for e in low_plan) / len(low_plan)
        else:
            high_plan_exec = 0
            low_plan_exec = 0
            high_plan_har = 0
            low_plan_har = 0

        # Adaptation analysis
        high_adapt = [e for e in self._entries if e.adaptation > 0.7]
        low_adapt = [e for e in self._entries if e.adaptation < 0.4]
        if high_adapt and low_adapt:
            high_adapt_learn = sum(e.learning for e in high_adapt) / len(high_adapt)
            low_adapt_learn = sum(e.learning for e in low_adapt) / len(low_adapt)
        else:
            high_adapt_learn = 0
            low_adapt_learn = 0

        # Season risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_plan = sum(e.planning for e in recent) / len(recent)
            recent_har = sum(e.harmony for e in recent) / len(recent)
            season_risk = recent_plan < 0.3 and recent_har < 0.3
        else:
            season_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "planning_impact": {
                "high_planning_execution": round(high_plan_exec, 2),
                "low_planning_execution": round(low_plan_exec, 2),
                "high_planning_harmony": round(high_plan_har, 2),
                "low_planning_harmony": round(low_plan_har, 2),
            },
            "adaptation_effect": {
                "high_adaptation_learning": round(high_adapt_learn, 2),
                "low_adaptation_learning": round(low_adapt_learn, 2),
            },
            "season_risk": season_risk,
            "avg_planning": round(sum(e.planning for e in self._entries) / len(self._entries), 2),
            "avg_harmony": round(sum(e.harmony for e in self._entries) / len(self._entries), 2),
        }

    def get_season_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get season suggestion."""
        suggestions = [
            "The garden has seasons. And so does the gardener. Spring is for planting. Summer is for tending. Autumn is for harvesting. Winter is for resting. Fighting this is fighting nature. And nature always wins.",
            "Plan with the season. Not against it. Plant cool-weather crops in spring. Heat-loving ones in summer. Harvest before frost. Rest in winter. The garden knows what it needs. Listen.",
            "Spring: prepare the soil. Clear debris. Add compost. Plan layouts. Start seeds. This is foundation work. Rushed spring work leads to struggling summer gardens. Take your time.",
            "Summer: tend and observe. Water deeply. Weed regularly. Watch for pests. Harvest frequently. This is maintenance season. The work of keeping promises made in spring.",
            "Autumn: harvest and preserve. Collect seeds. Plant bulbs. Mulch beds. Clear spent plants. This is gratitude season. The reward for spring's hope and summer's work.",
            "Winter: rest and dream. Read garden books. Plan next year. Clean tools. Mend fences. This is not dormancy. It's preparation. The garden is resting. You should too.",
            "Notice microclimates. The sunny corner. The shady spot. The windy ridge. The protected nook. Each has its own season. Its own possibilities. Match plants to places. Not wishes to dreams.",
            "Track what works. What failed. What surprised you. Garden journals are data. Data becomes wisdom. Wisdom creates gardens that thrive. Write it down. You'll forget by next spring.",
            "Accept seasonal losses. The late frost. The drought. The pest invasion. These are not personal failures. They're nature's way. Adapt. Learn. Plant again. The garden always offers another season.",
            "The person who gardens in harmony with seasons is not old-fashioned. They're wise. They understand that growth and rest are both necessary. That every season has its purpose. And that the best gardens are those that flow with time, not against it."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One seasonal task done. One observation of what the garden needs now. One rest taken when needed. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A seasonal plan made. A crop rotated. A harvest preserved. A winter rest honored. Medium harmony."
        else:
            capacity_note = "Good capacity. Deep cyclical wisdom. A systematic practice of seasonal gardening that works with nature's rhythms. You have the strength to dance with the seasons."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Seasonal garden planning is about understanding that the garden is not a constant. It changes. It cycles. It has its own rhythm that is older than agriculture itself. Most people try to garden the same way year-round. They plant when they feel like it. They water when they remember. They ignore the season's signals. And they wonder why their garden struggles. The work of seasonal garden planning is about aligning your gardening practice with the natural cycles. About understanding what each season demands and offers. About preparing in spring, tending in summer, harvesting in autumn, and resting in winter. And about recognizing that the gardener who works with the seasons is not just more successful. They're more at peace. Because they're not fighting nature. They're flowing with it."
        }

    def get_season_score(self) -> int:
        """Calculate overall season health (0-100)."""
        if not self._entries:
            return 25

        avg_plan = sum(e.planning for e in self._entries) / len(self._entries)
        avg_exec = sum(e.execution for e in self._entries) / len(self._entries)
        avg_adapt = sum(e.adaptation for e in self._entries) / len(self._entries)
        avg_learn = sum(e.learning for e in self._entries) / len(self._entries)
        avg_har = sum(e.harmony for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_plan = sum(e.planning for e in recent) / len(recent)
            recent_har = sum(e.harmony for e in recent) / len(recent)
        else:
            recent_plan = 0
            recent_har = 0

        # Season risk penalty
        sea_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_plan_30 = sum(e.planning for e in last_30) / len(last_30)
            recent_har_30 = sum(e.harmony for e in last_30) / len(last_30)
            if recent_plan_30 < 0.3 and recent_har_30 < 0.3:
                sea_penalty = 15

        # Type variety
        unique_types = len(set(e.season_type for e in self._entries))

        score = (avg_plan * 20) + (avg_exec * 15) + (avg_adapt * 15) + (avg_learn * 10) + (avg_har * 20) + (recent_plan * 5) + (recent_har * 5) + (unique_types * 2) - sea_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_planning"] = round(sum(e.planning for e in self._entries) / len(self._entries), 2)
            self._stats["avg_harmony"] = round(sum(e.harmony for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_plan = sum(e.planning for e in recent) / len(recent)
                recent_har = sum(e.harmony for e in recent) / len(recent)
                self._stats["season_risk"] = recent_plan < 0.3 and recent_har < 0.3
            else:
                self._stats["season_risk"] = False

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

    def _log_entry(self, entry: SeasonEntry):
        try:
            with open(SEASON_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "phase": entry.phase,
                    "season_type": entry.season_type,
                    "planning": entry.planning,
                    "harmony": entry.harmony,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sgp_instance: Optional[SeasonalGardenPlanner] = None
_sgp_lock = threading.Lock()


def get_seasonal_garden_planner() -> SeasonalGardenPlanner:
    global _sgp_instance
    with _sgp_lock:
        if _sgp_instance is None:
            _sgp_instance = SeasonalGardenPlanner()
        return _sgp_instance
