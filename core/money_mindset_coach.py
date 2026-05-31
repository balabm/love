"""
LOVE Money Mindset Coach — Financial Psychology Intelligence (Modern AI Pattern)

Most people's financial problems are psychological, not mathematical. This coach:

1. MINDSET TRACKING
   - Record money mindset moments and their characteristics
   - Track mindset types (scarcity, abundance, fear, guilt, shame, entitlement)
   - Log clarity, confidence, and alignment with money decisions

2. PATTERN ANALYSIS
   - Identify the user's money mindset profile (scarcity, anxious, balanced, abundant)
   - Find mindset patterns that create wealth vs anxiety
   - Detect chronic scarcity and its costs

3. MINDSET COACHING
   - Suggest practices for shifting from scarcity to abundance
   - Provide frameworks for understanding money psychology
   - Recommend practices for financial clarity and confidence

4. ABUNDANCE CULTIVATION
   - Track the correlation between mindset and financial behavior
   - Alert when scarcity mindset is dominating decisions
   - Celebrate moments of genuine financial confidence

Architecture:
- record_mindset(situation, type, clarity, confidence, alignment): Log mindset
- get_mindset_stats(): Get mindset pattern analysis
- get_mindset_suggestion(capacity, context): Get suggestion
- get_mindset_score(): Calculate overall mindset health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "money_mindset_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MINDSET_LOG = DATA_DIR / "mindsets.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MindsetEntry:
    """A tracked money mindset moment."""
    entry_id: str = ""
    situation: str = ""  # what happened
    mindset_type: str = ""  # scarcity, abundance, fear, guilt, shame, entitlement
    clarity: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    alignment: float = 0.0  # 0-1 with values
    generosity: float = 0.0  # 0-1
    action_taken: float = 0.0  # 0-1 did you act wisely?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class MoneyMindsetCoach:
    """
    Intelligent money mindset coach with scarcity detection and abundance cultivation.
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
            "avg_clarity": 0.0,
            "avg_confidence": 0.0,
            "scarcity_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_mindset(self, situation: str = "", mindset_type: str = "", clarity: float = 0.0, confidence: float = 0.0, alignment: float = 0.0, generosity: float = 0.0, action_taken: float = 0.0, notes: str = "") -> MindsetEntry:
        """Record a money mindset moment."""
        entry_id = f"mnd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = MindsetEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            mindset_type=mindset_type or "general",
            clarity=clarity,
            confidence=confidence,
            alignment=alignment,
            generosity=generosity,
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

    def get_mindset_stats(self) -> Dict[str, Any]:
        """Get mindset pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "confidence_sum": 0.0, "alignment_sum": 0.0})
        for e in self._entries:
            by_type[e.mindset_type]["count"] += 1
            by_type[e.mindset_type]["clarity_sum"] += e.clarity
            by_type[e.mindset_type]["confidence_sum"] += e.confidence
            by_type[e.mindset_type]["alignment_sum"] += e.alignment

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_confidence": round(data["confidence_sum"] / count, 2),
                "avg_alignment": round(data["alignment_sum"] / count, 2),
            }

        # Scarcity vs abundance analysis
        scarcity = [e for e in self._entries if e.mindset_type in ("scarcity", "fear", "guilt", "shame")]
        abundant = [e for e in self._entries if e.mindset_type in ("abundance", "generosity", "confidence")]
        if scarcity and abundant:
            sc_conf = sum(e.confidence for e in scarcity) / len(scarcity)
            ab_conf = sum(e.confidence for e in abundant) / len(abundant)
            sc_align = sum(e.alignment for e in scarcity) / len(scarcity)
            ab_align = sum(e.alignment for e in abundant) / len(abundant)
        else:
            sc_conf = 0
            ab_conf = 0
            sc_align = 0
            ab_align = 0

        # Action analysis
        high_conf = [e for e in self._entries if e.confidence > 0.7]
        low_conf = [e for e in self._entries if e.confidence < 0.4]
        if high_conf and low_conf:
            high_conf_act = sum(e.action_taken for e in high_conf) / len(high_conf)
            low_conf_act = sum(e.action_taken for e in low_conf) / len(low_conf)
        else:
            high_conf_act = 0
            low_conf_act = 0

        # Scarcity risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_scarcity = sum(1 for e in recent if e.mindset_type in ("scarcity", "fear", "guilt")) / len(recent)
            recent_conf = sum(e.confidence for e in recent) / len(recent)
            scarcity_risk = recent_scarcity > 0.6 and recent_conf < 0.4
        else:
            scarcity_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "scarcity_vs_abundance": {
                "scarcity_confidence": round(sc_conf, 2),
                "abundance_confidence": round(ab_conf, 2),
                "scarcity_alignment": round(sc_align, 2),
                "abundance_alignment": round(ab_align, 2),
            },
            "confidence_impact": {
                "high_confidence_action": round(high_conf_act, 2),
                "low_confidence_action": round(low_conf_act, 2),
            },
            "scarcity_risk": scarcity_risk,
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
            "avg_confidence": round(sum(e.confidence for e in self._entries) / len(self._entries), 2),
        }

    def get_mindset_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get mindset suggestion."""
        suggestions = [
            "Money is not the root of evil. The love of money is. And the fear of money is equally destructive. Neither obsession nor avoidance is healthy. Money is a tool. Use it well.",
            "Scarcity mindset says: I don't have enough. Abundance mindset says: I have enough, and more is coming. The truth is usually closer to abundance than scarcity. But fear distorts it.",
            "Track your money without judgment. Not to shame yourself. To understand yourself. Where does it go? What does it reflect? Your values? Your fears? Your hopes?",
            "The person who says 'I can't afford it' without thinking is living in scarcity. The person who says 'how can I afford it?' is living in possibility. Same situation. Different mind.",
            "Money anxiety is rarely about money. It's about security. About control. About worth. Address the root fear and the money follows. Or at least the anxiety about it fades.",
            "Your net worth is not your self-worth. The number in your bank account is information. Not a judgment. Not a verdict. Just information. Use it. Don't let it use you.",
            "Generosity is not about having excess. It's about trusting that you have enough. The most generous people are not always the richest. They're the most trusting.",
            "Every financial decision is a values decision. Where you spend is what you value. Look at your spending honestly. Is it aligned with who you want to be?",
            "Fear-based financial decisions are usually bad decisions. The stock you sell in panic. The opportunity you miss from caution. The investment you make from greed. Breathe. Then decide.",
            "Financial confidence comes from knowledge, not wealth. The person who understands their finances feels rich at any level. The person who doesn't feels poor at any level. Learn."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One honest look at your money. One moment without judgment. One small act of financial clarity. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A budget review. A spending analysis. A values alignment check. Medium coaching."
        else:
            capacity_note = "Good capacity. Deep financial psychology work. A systematic shift from scarcity to abundance. You have the strength to transform your relationship with money."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Most people's financial problems are not mathematical. They're psychological. The person who earns six figures and is stressed about money has the same problem as the person who earns minimum wage and is stressed about money: they believe they don't have enough. And that belief creates the stress, not the number. Scarcity mindset is a lens. It filters out abundance. It sees only what's missing. And it creates a self-fulfilling prophecy: the more you fear not having enough, the more you hoard, the more you miss opportunities, the less you have. Abundance mindset is also a lens. It sees possibility. It trusts that there is enough. And it creates a different prophecy: the more you trust, the more you invest in yourself and others, the more opportunities come. The work of money mindset coaching is not about getting rich. It's about getting free. Free from the anxiety. Free from the shame. Free from the belief that your worth is measured in dollars."
        }

    def get_mindset_score(self) -> int:
        """Calculate overall mindset health (0-100)."""
        if not self._entries:
            return 25

        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_conf = sum(e.confidence for e in self._entries) / len(self._entries)
        avg_align = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_gen = sum(e.generosity for e in self._entries) / len(self._entries)
        avg_act = sum(e.action_taken for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_conf = sum(e.confidence for e in recent) / len(recent)
            recent_align = sum(e.alignment for e in recent) / len(recent)
        else:
            recent_conf = 0
            recent_align = 0

        # Scarcity penalty
        scarcity_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_scarcity = sum(1 for e in last_30 if e.mindset_type in ("scarcity", "fear", "guilt")) / len(last_30)
            recent_conf_30 = sum(e.confidence for e in last_30) / len(last_30)
            if recent_scarcity > 0.6 and recent_conf_30 < 0.4:
                scarcity_penalty = 15

        # Type variety
        unique_types = len(set(e.mindset_type for e in self._entries))

        score = (avg_clarity * 20) + (avg_conf * 20) + (avg_align * 20) + (avg_gen * 15) + (avg_act * 10) + (recent_conf * 5) + (recent_align * 5) + (unique_types * 2) - scarcity_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_confidence"] = round(sum(e.confidence for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_scarcity = sum(1 for e in recent if e.mindset_type in ("scarcity", "fear", "guilt")) / len(recent)
                recent_conf = sum(e.confidence for e in recent) / len(recent)
                self._stats["scarcity_risk"] = recent_scarcity > 0.6 and recent_conf < 0.4
            else:
                self._stats["scarcity_risk"] = False

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

    def _log_entry(self, entry: MindsetEntry):
        try:
            with open(MINDSET_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "mindset_type": entry.mindset_type,
                    "clarity": entry.clarity,
                    "confidence": entry.confidence,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_mmc_instance: Optional[MoneyMindsetCoach] = None
_mmc_lock = threading.Lock()


def get_money_mindset_coach() -> MoneyMindsetCoach:
    global _mmc_instance
    with _mmc_lock:
        if _mmc_instance is None:
            _mmc_instance = MoneyMindsetCoach()
        return _mmc_instance
