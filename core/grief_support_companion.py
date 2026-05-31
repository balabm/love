"""
LOVE Grief Support Companion — Loss Intelligence (Modern AI Pattern)

Most people are unprepared for grief. This companion:

1. GRIEF TRACKING
   - Record grief experiences and their characteristics
   - Track grief types (anticipatory, acute, integrated, ambiguous)
   - Log waves, triggers, and moments of relief

2. PATTERN ANALYSIS
   - Identify the user's grief profile (suppressed, expressed, stuck, flowing)
   - Find patterns that indicate healthy processing vs complicated grief
   - Detect isolation and disconnection during grief

3. GRIEF SUPPORT
   - Suggest practices for honoring loss while maintaining life
   - Provide frameworks for dealing with grief waves
   - Recommend support structures and rituals

4. HEALING CULTIVATION
   - Track the correlation between expression and integration
   - Alert when grief is becoming the entire identity
   - Celebrate moments of meaning-making after loss

Architecture:
- record_grief(experience, type, intensity, expression, meaning): Log grief
- get_grief_stats(): Get grief pattern analysis
- get_support_suggestion(stage, capacity, context): Get suggestion
- get_grief_score(): Calculate overall grief health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "grief_support_companion"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GRIEF_LOG = DATA_DIR / "grief.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class GriefEntry:
    """A tracked grief entry."""
    entry_id: str = ""
    experience: str = ""  # what happened / what was felt
    grief_type: str = ""  # anticipatory, acute, integrated, ambiguous, anniversary
    intensity: float = 0.5  # 0-1
    expression: float = 0.0  # 0-1 how much was expressed
    support_received: float = 0.0  # 0-1
    meaning_making: float = 0.0  # 0-1
    self_compassion: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class GriefSupportCompanion:
    """
    Intelligent grief companion with wave detection and healing cultivation.
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
            "avg_expression": 0.0,
            "avg_meaning_making": 0.0,
            "complicated_grief_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_grief(self, experience: str = "", grief_type: str = "", intensity: float = 0.5, expression: float = 0.0, support_received: float = 0.0, meaning_making: float = 0.0, self_compassion: float = 0.0, notes: str = "") -> GriefEntry:
        """Record a grief entry."""
        entry_id = f"grf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = GriefEntry(
            entry_id=entry_id,
            experience=experience or "unspecified",
            grief_type=grief_type or "acute",
            intensity=intensity,
            expression=expression,
            support_received=support_received,
            meaning_making=meaning_making,
            self_compassion=self_compassion,
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

    def get_grief_stats(self) -> Dict[str, Any]:
        """Get grief pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "expression_sum": 0.0, "meaning_sum": 0.0})
        for e in self._entries:
            by_type[e.grief_type]["count"] += 1
            by_type[e.grief_type]["intensity_sum"] += e.intensity
            by_type[e.grief_type]["expression_sum"] += e.expression
            by_type[e.grief_type]["meaning_sum"] += e.meaning_making

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_expression": round(data["expression_sum"] / count, 2),
                "avg_meaning": round(data["meaning_sum"] / count, 2),
            }

        # Expression analysis
        high_expr = [e for e in self._entries if e.expression > 0.7]
        low_expr = [e for e in self._entries if e.expression < 0.4]
        if high_expr and low_expr:
            high_expr_meaning = sum(e.meaning_making for e in high_expr) / len(high_expr)
            low_expr_meaning = sum(e.meaning_making for e in low_expr) / len(low_expr)
            high_expr_support = sum(e.support_received for e in high_expr) / len(high_expr)
            low_expr_support = sum(e.support_received for e in low_expr) / len(low_expr)
        else:
            high_expr_meaning = 0
            low_expr_meaning = 0
            high_expr_support = 0
            low_expr_support = 0

        # Support analysis
        high_support = [e for e in self._entries if e.support_received > 0.7]
        low_support = [e for e in self._entries if e.support_received < 0.4]
        if high_support and low_support:
            high_sup_expr = sum(e.expression for e in high_support) / len(high_support)
            low_sup_expr = sum(e.expression for e in low_support) / len(low_support)
        else:
            high_sup_expr = 0
            low_sup_expr = 0

        # Self-compassion analysis
        high_sc = [e for e in self._entries if e.self_compassion > 0.7]
        low_sc = [e for e in self._entries if e.self_compassion < 0.4]
        if high_sc and low_sc:
            high_sc_meaning = sum(e.meaning_making for e in high_sc) / len(high_sc)
            low_sc_meaning = sum(e.meaning_making for e in low_sc) / len(low_sc)
        else:
            high_sc_meaning = 0
            low_sc_meaning = 0

        # Complicated grief detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if recent:
            recent_intensity = sum(e.intensity for e in recent) / len(recent)
            recent_expr = sum(e.expression for e in recent) / len(recent)
            recent_meaning = sum(e.meaning_making for e in recent) / len(recent)
            complicated_grief_risk = recent_intensity > 0.7 and recent_expr < 0.3 and recent_meaning < 0.3
        else:
            complicated_grief_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "expression_impact": {
                "high_expression_meaning": round(high_expr_meaning, 2),
                "low_expression_meaning": round(low_expr_meaning, 2),
                "high_expression_support": round(high_expr_support, 2),
                "low_expression_support": round(low_expr_support, 2),
            },
            "support_effect": {
                "high_support_expression": round(high_sup_expr, 2),
                "low_support_expression": round(low_sup_expr, 2),
            },
            "self_compassion_effect": {
                "high_compassion_meaning": round(high_sc_meaning, 2),
                "low_compassion_meaning": round(low_sc_meaning, 2),
            },
            "complicated_grief_risk": complicated_grief_risk,
            "avg_intensity": round(sum(e.intensity for e in self._entries) / len(self._entries), 2),
            "avg_expression": round(sum(e.expression for e in self._entries) / len(self._entries), 2),
        }

    def get_support_suggestion(self, stage: str = "", capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get grief support suggestion."""
        suggestions = [
            "Grief is not a problem to solve. It's an experience to have. Stop trying to fix it. Start trying to feel it. The only way out is through.",
            "Tell someone. Grief kept secret becomes poison. Grief shared becomes bearable. You don't need advice. You need witness. Find someone who can be present without fixing.",
            "Create a ritual of remembrance. Light a candle. Visit a place. Write a letter. Rituals say: this loss mattered. And I am still here, carrying it.",
            "Grief comes in waves. You can't stop the wave. But you can learn to surf. When it rises, breathe. Name it. 'This is grief.' It passes. It always passes.",
            "Don't rush yourself. Society gives you three days of bereavement leave and expects you to be fine. That's absurd. Grief takes as long as it takes. Respect your own timeline.",
            "Do one small thing for your future self. Eat something. Walk somewhere. Call someone. Grief makes the future feel irrelevant. Do one thing that says: I believe I will want to be here.",
            "The dead don't need your suffering. They need your living. The best tribute to someone you've lost is a life fully lived. Honor them by being alive. Really alive.",
            "Grief changes you. That's not failure. That's reality. You're not the person you were before the loss. And you're not yet the person you'll become after it. Be patient with the becoming.",
            "Some days will be harder than others. Anniversaries. Holidays. Random Tuesdays. Don't judge the bad days. They're part of the process. Let them come. Let them go.",
            "Self-compassion is not self-indulgence. Be gentle with yourself. Speak to yourself the way you'd speak to a dear friend in grief. You deserve that same kindness.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Just survive today. Nothing more is required. Survival is enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. One small expression. One conversation. One ritual. That's enough."
        else:
            capacity_note = "Good capacity. Meaning-making is possible now. Create. Share. Integrate. You have the strength to begin transforming grief into growth."

        return {
            "stage": stage or "general",
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Grief is the price of love. If you loved, you will grieve. There's no way around it. The attempt to avoid grief is the attempt to avoid love. And that's no life at all. Grief is not weakness. It's not something wrong with you. It's the natural, healthy response to loss. The problem is not that we grieve. The problem is that we grieve alone. That we grieve silently. That we grieve without support. Grief needs community. Grief needs expression. Grief needs time. And most of all, grief needs permission. Permission to be messy. Permission to take longer than expected. Permission to never fully get over it. Because some losses change you permanently. And that's okay. That's love.",
        }

    def get_grief_score(self) -> int:
        """Calculate overall grief health (0-100)."""
        if not self._entries:
            return 25

        avg_expression = sum(e.expression for e in self._entries) / len(self._entries)
        avg_support = sum(e.support_received for e in self._entries) / len(self._entries)
        avg_meaning = sum(e.meaning_making for e in self._entries) / len(self._entries)
        avg_self_compassion = sum(e.self_compassion for e in self._entries) / len(self._entries)
        avg_intensity = sum(e.intensity for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_expression = sum(e.expression for e in recent) / len(recent)
            recent_meaning = sum(e.meaning_making for e in recent) / len(recent)
        else:
            recent_expression = 0
            recent_meaning = 0

        # Complicated grief penalty
        cg_penalty = 0
        last_90 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
        if last_90:
            recent_intensity = sum(e.intensity for e in last_90) / len(last_90)
            recent_expr = sum(e.expression for e in last_90) / len(last_90)
            recent_meaning = sum(e.meaning_making for e in last_90) / len(last_90)
            if recent_intensity > 0.7 and recent_expr < 0.3 and recent_meaning < 0.3:
                cg_penalty = 20

        score = (avg_expression * 25) + (avg_support * 15) + (avg_meaning * 20) + (avg_self_compassion * 15) + (recent_expression * 10) + (recent_meaning * 10) - (avg_intensity * 5) - cg_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_expression"] = round(sum(e.expression for e in self._entries) / len(self._entries), 2)
            self._stats["avg_meaning_making"] = round(sum(e.meaning_making for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=90)).isoformat()]
            if recent:
                recent_intensity = sum(e.intensity for e in recent) / len(recent)
                recent_expr = sum(e.expression for e in recent) / len(recent)
                recent_meaning = sum(e.meaning_making for e in recent) / len(recent)
                self._stats["complicated_grief_risk"] = recent_intensity > 0.7 and recent_expr < 0.3 and recent_meaning < 0.3
            else:
                self._stats["complicated_grief_risk"] = False

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

    def _log_entry(self, entry: GriefEntry):
        try:
            with open(GRIEF_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "experience": entry.experience,
                    "grief_type": entry.grief_type,
                    "intensity": entry.intensity,
                    "expression": entry.expression,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gsc_instance: Optional[GriefSupportCompanion] = None
_gsc_lock = threading.Lock()


def get_grief_support_companion() -> GriefSupportCompanion:
    global _gsc_instance
    with _gsc_lock:
        if _gsc_instance is None:
            _gsc_instance = GriefSupportCompanion()
        return _gsc_instance
