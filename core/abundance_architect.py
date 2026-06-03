"""
LOVE Abundance Architect — Wealth Consciousness Intelligence (Modern AI Pattern)

Most people repel abundance unconsciously. This architect:

1. ABUNDANCE TRACKING
   - Record abundance moments and their characteristics
   - Track abundance types (financial, relational, creative, time, opportunity, health)
   - Log recognition, gratitude, and expansion of abundance

2. PATTERN ANALYSIS
   - Identify the user's abundance profile (blocking, receiving, creating, expanding)
   - Find abundance patterns that attract vs repel wealth
   - Detect chronic abundance-blocking and its costs

3. ABUNDANCE ARCHITECTURE
   - Suggest practices for expanding capacity to receive
   - Provide frameworks for wealth consciousness
   - Recommend practices for creating and recognizing abundance

4. WEALTH CONSCIOUSNESS CULTIVATION
   - Track the correlation between abundance mindset and opportunities
   - Alert when abundance-blocking is dominating
   - Celebrate moments of genuine abundance creation

Architecture:
- record_abundance(manifestation, type, recognition, gratitude, expansion): Log abundance
- get_abundance_stats(): Get abundance pattern analysis
- get_abundance_suggestion(capacity, context): Get suggestion
- get_abundance_score(): Calculate overall abundance health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "abundance_architect"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ABUNDANCE_LOG = DATA_DIR / "abundances.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class AbundanceEntry:
    """A tracked abundance moment."""
    entry_id: str = ""
    manifestation: str = ""  # what manifested
    abundance_type: str = ""  # financial, relational, creative, time, opportunity, health
    recognition: float = 0.0  # 0-1 did you notice it?
    gratitude: float = 0.0  # 0-1
    expansion: float = 0.0  # 0-1 did you expand it?
    sharing: float = 0.0  # 0-1 did you share it?
    blocking: float = 0.0  # 0-1 did you block it?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AbundanceArchitect:
    """
    Intelligent abundance architect with blocking detection and wealth consciousness cultivation.
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
            "avg_recognition": 0.0,
            "avg_expansion": 0.0,
            "blocking_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_abundance(self, manifestation: str = "", abundance_type: str = "", recognition: float = 0.0, gratitude: float = 0.0, expansion: float = 0.0, sharing: float = 0.0, blocking: float = 0.0, notes: str = "") -> AbundanceEntry:
        """Record an abundance moment."""
        entry_id = f"abn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = AbundanceEntry(
            entry_id=entry_id,
            manifestation=manifestation or "unspecified",
            abundance_type=abundance_type or "opportunity",
            recognition=recognition,
            gratitude=gratitude,
            expansion=expansion,
            sharing=sharing,
            blocking=blocking,
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

    def get_abundance_stats(self) -> Dict[str, Any]:
        """Get abundance pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "recognition_sum": 0.0, "expansion_sum": 0.0, "gratitude_sum": 0.0})
        for e in self._entries:
            by_type[e.abundance_type]["count"] += 1
            by_type[e.abundance_type]["recognition_sum"] += e.recognition
            by_type[e.abundance_type]["expansion_sum"] += e.expansion
            by_type[e.abundance_type]["gratitude_sum"] += e.gratitude

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_recognition": round(data["recognition_sum"] / count, 2),
                "avg_expansion": round(data["expansion_sum"] / count, 2),
                "avg_gratitude": round(data["gratitude_sum"] / count, 2),
            }

        # Recognition analysis
        high_rec = [e for e in self._entries if e.recognition > 0.7]
        low_rec = [e for e in self._entries if e.recognition < 0.4]
        if high_rec and low_rec:
            high_rec_exp = sum(e.expansion for e in high_rec) / len(high_rec)
            low_rec_exp = sum(e.expansion for e in low_rec) / len(low_rec)
            high_rec_gr = sum(e.gratitude for e in high_rec) / len(high_rec)
            low_rec_gr = sum(e.gratitude for e in low_rec) / len(low_rec)
        else:
            high_rec_exp = 0
            low_rec_exp = 0
            high_rec_gr = 0
            low_rec_gr = 0

        # Blocking analysis
        high_block = [e for e in self._entries if e.blocking > 0.7]
        low_block = [e for e in self._entries if e.blocking < 0.4]
        if high_block and low_block:
            high_block_rec = sum(e.recognition for e in high_block) / len(high_block)
            low_block_rec = sum(e.recognition for e in low_block) / len(low_block)
        else:
            high_block_rec = 0
            low_block_rec = 0

        # Blocking risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_block = sum(e.blocking for e in recent) / len(recent)
            recent_rec = sum(e.recognition for e in recent) / len(recent)
            blocking_risk = recent_block > 0.6 and recent_rec < 0.4
        else:
            blocking_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "recognition_impact": {
                "high_recognition_expansion": round(high_rec_exp, 2),
                "low_recognition_expansion": round(low_rec_exp, 2),
                "high_recognition_gratitude": round(high_rec_gr, 2),
                "low_recognition_gratitude": round(low_rec_gr, 2),
            },
            "blocking_effect": {
                "high_blocking_recognition": round(high_block_rec, 2),
                "low_blocking_recognition": round(low_block_rec, 2),
            },
            "blocking_risk": blocking_risk,
            "avg_recognition": round(sum(e.recognition for e in self._entries) / len(self._entries), 2),
            "avg_expansion": round(sum(e.expansion for e in self._entries) / len(self._entries), 2),
        }

    def get_abundance_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get abundance suggestion."""
        suggestions = [
            "Abundance is not about having more. It's about noticing what you already have. Most people are standing in a river of abundance and complaining about being thirsty. Look around.",
            "You block abundance by believing you don't deserve it. By pushing away compliments. By refusing help. By saying 'I can't afford it' before you've even checked. Stop blocking. Start receiving.",
            "Wealth consciousness is a practice. Not a state. You practice it by noticing opportunities. By saying yes to good things. By trusting that more will come. Practice daily.",
            "The universe is not scarce. It creates galaxies from nothing. Your scarcity is not the universe's fault. It's your filter. Change the filter. See the abundance.",
            "Expand your capacity to receive. Most people can give but cannot receive. They feel guilty. Unworthy. Awkward. Practice receiving. A compliment. A gift. An opportunity. Just say thank you.",
            "Abundance creates abundance. The more you share, the more you have. Not because of some cosmic law. Because generosity creates connection. And connection creates opportunity.",
            "Track your wins. Not just money. Everything. A good conversation. A beautiful sunset. A moment of peace. A kind word. You have more abundance than you think. You just don't count it.",
            "Stop saying 'I can't.' Start saying 'how can I?' The first is a closed door. The second is an open one. Same situation. Different mind. Different outcome.",
            "Your environment reflects your consciousness. If you live in clutter, you live in scarcity. Clean your space. Organize your life. Make room for abundance. Literally.",
            "Abundance is not the opposite of scarcity. It's the transcendence of it. The person who has transcended scarcity doesn't think about scarcity or abundance. They just live. Fully."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of noticing abundance. One acceptance of a gift. One breath of enough-ness. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. An abundance audit. A receiving practice. An expansion exercise. Medium architecture."
        else:
            capacity_note = "Good capacity. Deep wealth consciousness work. A systematic shift from blocking to receiving. You have the strength to be truly abundant."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Abundance is not something you get. It's something you recognize. The person who feels abundant is not necessarily the person who has the most. They're the person who notices what they have. And expands it. And shares it. And trusts that more will come. Most people repel abundance unconsciously. They push away opportunities. They say no to good things. They believe they don't deserve success. And that belief becomes self-fulfilling. The work of abundance architecture is about removing the blocks. About expanding capacity. About recognizing that abundance is not a zero-sum game. When you succeed, you don't take from others. You create more possibility for everyone. That's abundance consciousness. And it's available to anyone who stops blocking it."
        }

    def get_abundance_score(self) -> int:
        """Calculate overall abundance health (0-100)."""
        if not self._entries:
            return 25

        avg_rec = sum(e.recognition for e in self._entries) / len(self._entries)
        avg_grat = sum(e.gratitude for e in self._entries) / len(self._entries)
        avg_exp = sum(e.expansion for e in self._entries) / len(self._entries)
        avg_share = sum(e.sharing for e in self._entries) / len(self._entries)
        avg_block = sum(e.blocking for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_rec = sum(e.recognition for e in recent) / len(recent)
            recent_exp = sum(e.expansion for e in recent) / len(recent)
        else:
            recent_rec = 0
            recent_exp = 0

        # Blocking penalty
        block_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_block = sum(e.blocking for e in last_30) / len(last_30)
            recent_rec_30 = sum(e.recognition for e in last_30) / len(last_30)
            if recent_block > 0.6 and recent_rec_30 < 0.4:
                block_penalty = 15

        # Type variety
        unique_types = len(set(e.abundance_type for e in self._entries))

        score = (avg_rec * 25) + (avg_grat * 20) + (avg_exp * 20) + (avg_share * 15) + (recent_rec * 5) + (recent_exp * 5) + (unique_types * 2) - (avg_block * 15) - block_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_recognition"] = round(sum(e.recognition for e in self._entries) / len(self._entries), 2)
            self._stats["avg_expansion"] = round(sum(e.expansion for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_block = sum(e.blocking for e in recent) / len(recent)
                recent_rec = sum(e.recognition for e in recent) / len(recent)
                self._stats["blocking_risk"] = recent_block > 0.6 and recent_rec < 0.4
            else:
                self._stats["blocking_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.abundance_architect")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.abundance_architect")

    def _log_entry(self, entry: AbundanceEntry):
        try:
            with open(ABUNDANCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "manifestation": entry.manifestation,
                    "abundance_type": entry.abundance_type,
                    "recognition": entry.recognition,
                    "expansion": entry.expansion,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.abundance_architect")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_aa_instance: Optional[AbundanceArchitect] = None
_aa_lock = threading.Lock()


def get_abundance_architect() -> AbundanceArchitect:
    global _aa_instance
    with _aa_lock:
        if _aa_instance is None:
            _aa_instance = AbundanceArchitect()
        return _aa_instance
