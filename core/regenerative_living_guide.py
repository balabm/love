"""
LOVE Regenerative Living Guide — Restoration Intelligence (Modern AI Pattern)

Most sustainability is about doing less harm. Regeneration is about doing more good. This guide:

1. REGENERATIVE TRACKING
   - Record regenerative actions and their characteristics
   - Track regenerative types (soil, water, biodiversity, community, climate)
   - Log restoration outcomes and their effects on ecosystems

2. PATTERN ANALYSIS
   - Identify the user's regenerative profile (consumer, neutral, restorative, regenerative)
   - Find actions that create net positive impact
   - Detect extractive patterns disguised as green

3. REGENERATIVE BUILDING
   - Suggest regenerative actions matched to current capacity and context
   - Provide restoration and rewilding frameworks
   - Recommendation net-positive practices

4. RESTORATION CULTIVATION
   - Track the correlation between regenerative action and ecosystem health
   - Alert when lifestyle is still extractive
   - Celebrate moments of genuine regeneration

Architecture:
- record_action(action, type, impact, net_positive): Log action
- get_regenerative_stats(): Get regenerative pattern analysis
- get_regenerative_action(capacity, context): Get action
- get_regenerative_score(): Calculate overall regenerative health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "regenerative_living_guide"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REGENERATIVE_LOG = DATA_DIR / "actions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class RegenerativeEntry:
    """A tracked regenerative entry."""
    entry_id: str = ""
    action: str = ""  # what was done
    regen_type: str = ""  # soil, water, biodiversity, community, climate
    impact: float = 0.0  # positive impact score
    net_positive: bool = True  # does it restore more than it takes
    consistency: float = 0.5  # 0-1
    scalability: float = 0.5  # 0-1, can others replicate
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class RegenerativeLivingGuide:
    """
    Intelligent regenerative living guide with net-positive tracking and restoration optimization.
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
            "total_impact": 0.0,
            "net_positive_rate": 0.0,
            "extractive_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_action(self, action: str = "", regen_type: str = "", impact: float = 0.0, net_positive: bool = True, consistency: float = 0.5, scalability: float = 0.5, notes: str = "") -> RegenerativeEntry:
        """Record a regenerative entry."""
        entry_id = f"reg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = RegenerativeEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            regen_type=regen_type or "soil",
            impact=impact,
            net_positive=net_positive,
            consistency=consistency,
            scalability=scalability,
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

    def get_regenerative_stats(self) -> Dict[str, Any]:
        """Get regenerative pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "impact_sum": 0.0, "consistency_sum": 0.0, "scalability_sum": 0.0, "net_positive_count": 0})
        for e in self._entries:
            by_type[e.regen_type]["count"] += 1
            by_type[e.regen_type]["impact_sum"] += e.impact
            by_type[e.regen_type]["consistency_sum"] += e.consistency
            by_type[e.regen_type]["scalability_sum"] += e.scalability
            if e.net_positive:
                by_type[e.regen_type]["net_positive_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "total_impact": round(data["impact_sum"], 1),
                "avg_impact": round(data["impact_sum"] / count, 1),
                "avg_consistency": round(data["consistency_sum"] / count, 2),
                "avg_scalability": round(data["scalability_sum"] / count, 2),
                "net_positive_rate": round(data["net_positive_count"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["total_impact"]) if type_stats else ("", {})

        # Net positive analysis
        net_positive = [e for e in self._entries if e.net_positive]
        net_negative = [e for e in self._entries if not e.net_positive]
        if net_positive and net_negative:
            np_impact = sum(e.impact for e in net_positive) / len(net_positive)
            nn_impact = sum(e.impact for e in net_negative) / len(net_negative)
            np_consistency = sum(e.consistency for e in net_positive) / len(net_positive)
            nn_consistency = sum(e.consistency for e in net_negative) / len(net_negative)
        else:
            np_impact = 0
            nn_impact = 0
            np_consistency = 0
            nn_consistency = 0

        # Scalability analysis
        high_scale = [e for e in self._entries if e.scalability > 0.7]
        low_scale = [e for e in self._entries if e.scalability < 0.4]
        if high_scale and low_scale:
            high_scale_impact = sum(e.impact for e in high_scale) / len(high_scale)
            low_scale_impact = sum(e.impact for e in low_scale) / len(low_scale)
        else:
            high_scale_impact = 0
            low_scale_impact = 0

        # Extractive detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_net_positive = sum(1 for e in recent if e.net_positive) / len(recent)
            recent_impact = sum(e.impact for e in recent) / len(recent)
            extractive_risk = recent_net_positive < 0.5 or recent_impact < 0
        else:
            extractive_risk = False

        # Recent trend
        if recent:
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            recent_scale = sum(e.scalability for e in recent) / len(recent)
        else:
            recent_cons = 0
            recent_scale = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_impact = sum(e.impact for e in older) / len(older)
            older_cons = sum(e.consistency for e in older) / len(older)
            impact_trend = (sum(e.impact for e in recent) / len(recent)) - older_impact if recent else 0
            cons_trend = (sum(e.consistency for e in recent) / len(recent)) - older_cons if recent else 0
        else:
            impact_trend = 0
            cons_trend = 0

        return {
            "total_entries": len(self._entries),
            "total_impact": round(sum(e.impact for e in self._entries), 1),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "net_positive_analysis": {
                "net_positive_avg_impact": round(np_impact, 1),
                "net_negative_avg_impact": round(nn_impact, 1),
                "net_positive_consistency": round(np_consistency, 2),
                "net_negative_consistency": round(nn_consistency, 2),
            },
            "scalability_impact": {
                "high_scalability_impact": round(high_scale_impact, 1),
                "low_scalability_impact": round(low_scale_impact, 1),
            },
            "extractive_risk": extractive_risk,
            "net_positive_rate": round(len(net_positive) / len(self._entries), 2),
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 1),
            "impact_trend": round(impact_trend, 1),
            "consistency_trend": round(cons_trend, 2),
            "recent_scalability": round(recent_scale, 2),
        }

    def get_regenerative_action(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get action."""
        actions = {
            "soil": [
                "Compost. Food scraps become soil. Soil grows food. You've closed a loop.",
                "Plant natives. They support local insects. Insects feed birds. Birds spread seeds. You've started a cascade.",
                "No-till garden. Disturb soil as little as possible. The fungi network stays intact. Carbon stays buried.",
            ],
            "water": [
                "Rain garden. Capture runoff. Let it sink in. Recharge groundwater. Reduce flooding.",
                "Fix leaks. A dripping faucet wastes 3,000 gallons a year. That's not trivial.",
                "Greywater system. Shower water waters plants. You've used water twice. That's regeneration.",
            ],
            "biodiversity": [
                "Plant pollinator strips. Even a small patch of wildflowers supports bees. Bees support everything.",
                "Leave the leaves. Leaf litter is habitat. For insects. For small mammals. For decomposition.",
                "Remove invasive species. They crowd out natives. One weekend of pulling can change an ecosystem.",
            ],
            "community": [
                "Start a tool library. One drill. Many users. Less production. More connection.",
                "Organize a repair cafe. Fix instead of replace. Teach others. Build skills. Reduce waste.",
                "Share surplus. Garden overflow. Book collection. Time. What you have too much of, someone needs.",
            ],
            "climate": [
                "Plant trees. The simplest carbon capture. One mature tree = 48 lbs CO2 per year. Plant ten.",
                "Support regenerative agriculture. Buy from farmers who build soil. Soil stores carbon. Food tastes better.",
                "Advocate. Vote. Speak. System change amplifies individual action. Be loud.",
            ],
            "general": [
                "Regeneration is not about being less bad. It's about being more good. Net positive. That's the goal.",
                "Start where you are. Your yard. Your street. Your community. Small actions ripple outward.",
                "The most regenerative thing you can do is inspire others. Multiply your impact by teaching.",
            ],
        }

        selected = actions.get(context, actions["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity. Pick one tiny regenerative act. Compost one banana peel. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Choose one domain. Go deep. Soil. Water. Biodiversity. Master one."
        else:
            capacity_note = "Good capacity. This is when you lead. Organize. Teach. Scale your impact through others."

        return {
            "context": context or "general",
            "capacity": capacity,
            "action": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Most environmentalism is defensive. Stop this. Reduce that. Protect this. Regeneration is offensive. Build soil. Plant trees. Clean water. Restore wetlands. The difference is profound. Sustainability asks: 'How do we maintain?' Regeneration asks: 'How do we heal?' The world doesn't need more people doing less harm. It needs more people doing more good. Be a net positive. That's the only goal that matters.",
        }

    def get_regenerative_score(self) -> int:
        """Calculate overall regenerative health (0-100)."""
        if not self._entries:
            return 25

        # Impact and net positivity
        total_impact = sum(e.impact for e in self._entries)
        net_positive = sum(1 for e in self._entries if e.net_positive)
        net_positive_rate = net_positive / len(self._entries)

        # Consistency and scalability
        avg_cons = sum(e.consistency for e in self._entries) / len(self._entries)
        avg_scale = sum(e.scalability for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.regen_type for e in self._entries))

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_impact = sum(e.impact for e in recent) / len(recent)
            recent_cons = sum(e.consistency for e in recent) / len(recent)
            recent_scale = sum(e.scalability for e in recent) / len(recent)
            recent_np = sum(1 for e in recent if e.net_positive) / len(recent)
        else:
            recent_impact = 0
            recent_cons = 0
            recent_scale = 0
            recent_np = 0

        # Extractive penalty
        extractive_penalty = 0
        if recent:
            recent_np_rate = sum(1 for e in recent if e.net_positive) / len(recent)
            recent_impact_val = sum(e.impact for e in recent) / len(recent)
            if recent_np_rate < 0.5 or recent_impact_val < 0:
                extractive_penalty = 15

        score = (total_impact * 0.5) + (net_positive_rate * 25) + (avg_cons * 15) + (avg_scale * 10) + (unique_types * 3) + (recent_impact * 0.3) + (recent_cons * 10) + (recent_scale * 5) + (recent_np * 10) - extractive_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["total_impact"] = round(sum(e.impact for e in self._entries), 1)
            self._stats["net_positive_rate"] = round(sum(1 for e in self._entries if e.net_positive) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_np = sum(1 for e in recent if e.net_positive) / len(recent)
                recent_impact = sum(e.impact for e in recent) / len(recent)
                self._stats["extractive_risk"] = recent_np < 0.5 or recent_impact < 0

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

    def _log_entry(self, entry: RegenerativeEntry):
        try:
            with open(REGENERATIVE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "regen_type": entry.regen_type,
                    "impact": entry.impact,
                    "net_positive": entry.net_positive,
                    "consistency": entry.consistency,
                    "scalability": entry.scalability,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rlg_instance: Optional[RegenerativeLivingGuide] = None
_rlg_lock = threading.Lock()


def get_regenerative_living_guide() -> RegenerativeLivingGuide:
    global _rlg_instance
    with _rlg_lock:
        if _rlg_instance is None:
            _rlg_instance = RegenerativeLivingGuide()
        return _rlg_instance
