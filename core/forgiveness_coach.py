"""
LOVE Forgiveness Coach — Release Intelligence (Modern AI Pattern)

Most grudges are held because release feels like weakness. This coach:

1. FORGIVENESS TRACKING
   - Record forgiveness attempts and their characteristics
   - Track forgiveness types (self, other, situation)
   - Log release outcomes and their effects on wellbeing

2. PATTERN ANALYSIS
   - Identify the user's forgiveness profile (reluctant, conditional, generous, rapid)
   - Find forgiveness accelerators (what helps them let go)
   - Detect grudge accumulation and its costs

3. FORGIVENESS BUILDING
   - Suggest release practices matched to current resentment
   - Provide perspective-taking exercises
   - Recommendation compassion practices

4. FREEDOM CULTIVATION
   - Track the correlation between forgiveness and energy
   - Alert when holding on is becoming habitual
   - Celebrate moments of genuine release

Architecture:
- record_forgiveness(target, type, method, release): Log forgiveness
- get_forgiveness_stats(): Get forgiveness pattern analysis
- get_forgiveness_practice(grudge, capacity): Get practice
- get_forgiveness_score(): Calculate overall forgiveness health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "forgiveness_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FORGIVENESS_LOG = DATA_DIR / "forgiveness.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ForgivenessEntry:
    """A tracked forgiveness entry."""
    entry_id: str = ""
    target: str = ""  # who or what was forgiven
    forgiveness_type: str = ""  # self, other, situation
    method: str = ""  # understanding, compassion, acceptance, time, ritual
    resentment_before: float = 0.5  # 0-1
    release_after: float = 0.5  # 0-1
    energy_change: float = 0.0  # -1 to 1
    genuine: bool = False  # was it genuine or forced
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ForgivenessCoach:
    """
    Intelligent forgiveness coach with grudge detection and release practices.
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
            "avg_release": 0.0,
            "avg_energy": 0.0,
            "grudge_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_forgiveness(self, target: str = "", forgiveness_type: str = "", method: str = "", resentment_before: float = 0.5, release_after: float = 0.5, energy_change: float = 0.0, genuine: bool = False, notes: str = "") -> ForgivenessEntry:
        """Record a forgiveness entry."""
        entry_id = f"forg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ForgivenessEntry(
            entry_id=entry_id,
            target=target or "unspecified",
            forgiveness_type=forgiveness_type or "other",
            method=method or "understanding",
            resentment_before=resentment_before,
            release_after=release_after,
            energy_change=energy_change,
            genuine=genuine,
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

    def get_forgiveness_stats(self) -> Dict[str, Any]:
        """Get forgiveness pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "resentment_sum": 0.0, "release_sum": 0.0, "energy_sum": 0.0, "genuine_count": 0})
        for e in self._entries:
            by_type[e.forgiveness_type]["count"] += 1
            by_type[e.forgiveness_type]["resentment_sum"] += e.resentment_before
            by_type[e.forgiveness_type]["release_sum"] += e.release_after
            by_type[e.forgiveness_type]["energy_sum"] += e.energy_change
            if e.genuine:
                by_type[e.forgiveness_type]["genuine_count"] += 1

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_resentment": round(data["resentment_sum"] / count, 2),
                "avg_release": round(data["release_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
                "genuine_rate": round(data["genuine_count"] / count, 2),
            }

        # Method analysis
        by_method = defaultdict(lambda: {"count": 0, "release_sum": 0.0, "energy_sum": 0.0})
        for e in self._entries:
            by_method[e.method]["count"] += 1
            by_method[e.method]["release_sum"] += e.release_after
            by_method[e.method]["energy_sum"] += e.energy_change

        method_stats = {}
        for m, data in by_method.items():
            count = data["count"]
            method_stats[m] = {
                "count": count,
                "avg_release": round(data["release_sum"] / count, 2),
                "avg_energy": round(data["energy_sum"] / count, 2),
            }

        best_method = max(method_stats.items(), key=lambda x: x[1]["avg_release"] + x[1]["avg_energy"]) if method_stats else ("", {})

        # Grudge detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if len(self._entries) > 14:
            high_resentment = sum(1 for e in self._entries if e.resentment_before > 0.7 and e.release_after < 0.4)
            grudge_rate = high_resentment / len(self._entries)
            grudge_risk = grudge_rate > 0.3
        else:
            grudge_risk = False

        # Release effectiveness
        release_effectiveness = sum(e.release_after - e.resentment_before for e in self._entries) / len(self._entries)

        # Genuine vs forced
        genuine = [e for e in self._entries if e.genuine]
        forced = [e for e in self._entries if not e.genuine]
        if genuine and forced:
            genuine_release = sum(e.release_after for e in genuine) / len(genuine)
            forced_release = sum(e.release_after for e in forced) / len(forced)
            genuine_energy = sum(e.energy_change for e in genuine) / len(genuine)
            forced_energy = sum(e.energy_change for e in forced) / len(forced)
        else:
            genuine_release = 0
            forced_release = 0
            genuine_energy = 0
            forced_energy = 0

        # Recent trend
        if recent:
            recent_release = sum(e.release_after for e in recent) / len(recent)
            recent_energy = sum(e.energy_change for e in recent) / len(recent)
            recent_genuine = sum(1 for e in recent if e.genuine) / len(recent)
        else:
            recent_release = 0
            recent_energy = 0
            recent_genuine = 0

        older = list(self._entries)[:-14] if len(self._entries) > 14 else []
        if older:
            older_release = sum(e.release_after for e in older) / len(older)
            older_energy = sum(e.energy_change for e in older) / len(older)
            release_trend = recent_release - older_release
            energy_trend = recent_energy - older_energy
        else:
            release_trend = 0
            energy_trend = 0

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "method_stats": method_stats,
            "best_method": best_method[0],
            "grudge_risk": grudge_risk,
            "release_effectiveness": round(release_effectiveness, 2),
            "genuine_vs_forced": {
                "genuine_release": round(genuine_release, 2),
                "forced_release": round(forced_release, 2),
                "genuine_energy": round(genuine_energy, 2),
                "forced_energy": round(forced_energy, 2),
            },
            "avg_release": round(sum(e.release_after for e in self._entries) / len(self._entries), 2),
            "avg_resentment": round(sum(e.resentment_before for e in self._entries) / len(self._entries), 2),
            "avg_energy": round(sum(e.energy_change for e in self._entries) / len(self._entries), 2),
            "release_trend": round(release_trend, 2),
            "energy_trend": round(energy_trend, 2),
            "recent_genuine_rate": round(recent_genuine, 2),
        }

    def get_forgiveness_practice(self, grudge: str = "", capacity: float = 0.5) -> Dict[str, Any]:
        """Get practice."""
        practices = {
            "self": [
                "You made a mistake. That makes you human, not irredeemable. What would you say to a friend who did the same?",
                "Write a letter to yourself from the perspective of someone who loves you unconditionally.",
                "Self-forgiveness is not self-indulgence. It's the prerequisite for genuine change. You can't grow from shame.",
            ],
            "other": [
                "They hurt you. That is true. Forgiveness doesn't change that truth. It changes your relationship to it.",
                "Write their story from their perspective. Not to excuse. To understand.",
                "Forgiveness is for you. It doesn't require their apology. It doesn't require their change. It requires your release.",
            ],
            "situation": [
                "Life is unfair. That is not negotiable. Your response to unfairness is.",
                "What would you tell someone else in this exact situation? Say that to yourself.",
                "Acceptance is not approval. It's the recognition that some things are outside your control.",
            ],
            "general": [
                "Forgiveness is a decision, not a feeling. Decide first. The feeling follows.",
                "Holding a grudge is like drinking poison and waiting for the other person to die. Put the cup down.",
                "Release is not forgetting. It's choosing not to let the past control your present.",
            ],
        }

        selected = practices.get(grudge, practices["general"])

        if capacity < 0.3:
            capacity_note = "Low capacity for forgiveness. That's okay. Start with tiny releases. One small grudge. One breath of relief."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. You can work with medium resentments. Choose one that costs you energy daily."
        else:
            capacity_note = "Good capacity. This is when you can tackle the big ones. The ones that shape your personality."

        return {
            "grudge": grudge or "general",
            "capacity": capacity,
            "practice": random.choice(selected),
            "capacity_note": capacity_note,
            "principle": "Forgiveness is not moral weakness. It's strategic intelligence. Grudges consume energy, attention, and joy. Forgiveness is the decision that your future is more important than your past. It's not about them. It's about you.",
        }

    def get_forgiveness_score(self) -> int:
        """Calculate overall forgiveness health (0-100)."""
        if not self._entries:
            return 30

        # Release and energy
        avg_release = sum(e.release_after for e in self._entries) / len(self._entries)
        avg_energy = sum(e.energy_change for e in self._entries) / len(self._entries)

        # Low resentment
        avg_resentment = sum(e.resentment_before for e in self._entries) / len(self._entries)

        # Genuine rate
        genuine = [e for e in self._entries if e.genuine]
        genuine_rate = len(genuine) / len(self._entries)

        # Release effectiveness
        release_effectiveness = sum(e.release_after - e.resentment_before for e in self._entries) / len(self._entries)

        # Type variety
        unique_types = len(set(e.forgiveness_type for e in self._entries))

        # Method variety
        unique_methods = len(set(e.method for e in self._entries))

        # Recent trend
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_release = sum(e.release_after for e in recent) / len(recent)
            recent_energy = sum(e.energy_change for e in recent) / len(recent)
            recent_genuine = sum(1 for e in recent if e.genuine) / len(recent)
        else:
            recent_release = 0
            recent_energy = 0
            recent_genuine = 0

        # Grudge penalty
        high_resentment = sum(1 for e in self._entries if e.resentment_before > 0.7 and e.release_after < 0.4)
        grudge_penalty = min(15, high_resentment / len(self._entries) * 15)

        score = (avg_release * 25) + (avg_energy * 15) + ((1 - avg_resentment) * 10) + (genuine_rate * 15) + (release_effectiveness * 10) + (unique_types * 2) + (unique_methods * 2) + (recent_release * 10) + (recent_energy * 10) + (recent_genuine * 5) - grudge_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_release"] = round(sum(e.release_after for e in self._entries) / len(self._entries), 2)
            self._stats["avg_energy"] = round(sum(e.energy_change for e in self._entries) / len(self._entries), 2)

            high_resentment = sum(1 for e in self._entries if e.resentment_before > 0.7 and e.release_after < 0.4)
            self._stats["grudge_risk"] = high_resentment / len(self._entries) > 0.3

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.forgiveness_coach")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.forgiveness_coach")

    def _log_entry(self, entry: ForgivenessEntry):
        try:
            with open(FORGIVENESS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "target": entry.target,
                    "forgiveness_type": entry.forgiveness_type,
                    "method": entry.method,
                    "resentment_before": entry.resentment_before,
                    "release_after": entry.release_after,
                    "energy_change": entry.energy_change,
                    "genuine": entry.genuine,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.forgiveness_coach")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_fc_instance: Optional[ForgivenessCoach] = None
_fc_lock = threading.Lock()


def get_forgiveness_coach() -> ForgivenessCoach:
    global _fc_instance
    with _fc_lock:
        if _fc_instance is None:
            _fc_instance = ForgivenessCoach()
        return _fc_instance
