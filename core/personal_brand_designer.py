"""
LOVE Personal Brand Designer — Identity Communication Intelligence (Modern AI Pattern)

Most people have no idea how they're perceived. This designer:

1. BRAND TRACKING
   - Record personal brand moments and their characteristics
   - Track brand types (online, offline, professional, social, creative, leadership)
   - Log clarity, consistency, authenticity, impact, and alignment of brand expression

2. PATTERN ANALYSIS
   - Identify the user's brand profile (invisible, inconsistent, developing, magnetic)
   - Find brand patterns that create recognition vs confusion
   - Detect chronic invisibility and its costs

3. CLARITY BUILDING
   - Suggest practices for defining and expressing personal brand
   - Provide frameworks for consistent, authentic presence
   - Recommend practices for intentional impression management

4. MAGNETIC PRESENCE CULTIVATION
   - Track the correlation between brand clarity and opportunity
   - Alert when fragmentation is replacing focus
   - Celebrate moments of genuine brand power

Architecture:
- record_brand(moment, type, clarity, consistency, authenticity, impact, alignment): Log brand
- get_brand_stats(): Get brand pattern analysis
- get_brand_suggestion(capacity, context): Get suggestion
- get_brand_score(): Calculate overall brand health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "personal_brand_designer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BRAND_LOG = DATA_DIR / "brands.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BrandEntry:
    """A tracked personal brand moment."""
    entry_id: str = ""
    moment: str = ""  # what was the moment
    brand_type: str = ""  # online, offline, professional, social, creative, leadership
    clarity: float = 0.0  # 0-1
    consistency: float = 0.0  # 0-1
    authenticity: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    alignment: float = 0.0  # 0-1
    visibility: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class PersonalBrandDesigner:
    """
    Intelligent personal brand designer with invisibility detection and magnetic presence cultivation.
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
            "avg_impact": 0.0,
            "invisibility_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_brand(self, moment: str = "", brand_type: str = "", clarity: float = 0.0, consistency: float = 0.0, authenticity: float = 0.0, impact: float = 0.0, alignment: float = 0.0, visibility: float = 0.0, notes: str = "") -> BrandEntry:
        """Record a personal brand moment."""
        entry_id = f"brd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BrandEntry(
            entry_id=entry_id,
            moment=moment or "unspecified",
            brand_type=brand_type or "professional",
            clarity=clarity,
            consistency=consistency,
            authenticity=authenticity,
            impact=impact,
            alignment=alignment,
            visibility=visibility,
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

    def get_brand_stats(self) -> Dict[str, Any]:
        """Get brand pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "clarity_sum": 0.0, "consistency_sum": 0.0, "impact_sum": 0.0})
        for e in self._entries:
            by_type[e.brand_type]["count"] += 1
            by_type[e.brand_type]["clarity_sum"] += e.clarity
            by_type[e.brand_type]["consistency_sum"] += e.consistency
            by_type[e.brand_type]["impact_sum"] += e.impact

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_consistency": round(data["consistency_sum"] / count, 2),
                "avg_impact": round(data["impact_sum"] / count, 2),
            }

        # Clarity analysis
        high_clar = [e for e in self._entries if e.clarity > 0.7]
        low_clar = [e for e in self._entries if e.clarity < 0.4]
        if high_clar and low_clar:
            high_clar_imp = sum(e.impact for e in high_clar) / len(high_clar)
            low_clar_imp = sum(e.impact for e in low_clar) / len(low_clar)
            high_clar_align = sum(e.alignment for e in high_clar) / len(high_clar)
            low_clar_align = sum(e.alignment for e in low_clar) / len(low_clar)
        else:
            high_clar_imp = 0
            low_clar_imp = 0
            high_clar_align = 0
            low_clar_align = 0

        # Consistency analysis
        high_cons = [e for e in self._entries if e.consistency > 0.7]
        low_cons = [e for e in self._entries if e.consistency < 0.4]
        if high_cons and low_cons:
            high_cons_imp = sum(e.impact for e in high_cons) / len(high_cons)
            low_cons_imp = sum(e.impact for e in low_cons) / len(low_cons)
        else:
            high_cons_imp = 0
            low_cons_imp = 0

        # Invisibility risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_clar = sum(e.clarity for e in recent) / len(recent)
            recent_imp = sum(e.impact for e in recent) / len(recent)
            invisibility_risk = recent_clar < 0.3 and recent_imp < 0.3
        else:
            invisibility_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "clarity_impact": {
                "high_clarity_impact": round(high_clar_imp, 2),
                "low_clarity_impact": round(low_clar_imp, 2),
                "high_clarity_alignment": round(high_clar_align, 2),
                "low_clarity_alignment": round(low_clar_align, 2),
            },
            "consistency_effect": {
                "high_consistency_impact": round(high_cons_imp, 2),
                "low_consistency_impact": round(low_cons_imp, 2),
            },
            "invisibility_risk": invisibility_risk,
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
            "avg_impact": round(sum(e.impact for e in self._entries) / len(self._entries), 2),
        }

    def get_brand_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get brand suggestion."""
        suggestions = [
            "Most people are invisible. They do good work. They have good ideas. They have good character. And nobody knows. Because they've never made themselves known. They've never intentionally designed how they're perceived. And they wonder why opportunities pass them by.",
            "Your personal brand is not a lie. It's not marketing. It's not spin. It's the intentional expression of who you actually are. It's making sure that what people see matches what you are. It's clarity. Not deception.",
            "Define what you want to be known for. Not everything. One thing. Two at most. The thing you're genuinely good at. The thing you genuinely care about. The thing you want to be associated with. Clarity creates memory. Memory creates opportunity.",
            "Be consistent. Not identical. But recognizably you. The same values. The same tone. The same quality. Across platforms. Across contexts. Across time. The person who is consistent is the person who is remembered. And the person who is remembered is the person who is chosen.",
            "Show your work. Not just the results. The process. The thinking. The failures. The lessons. The behind-the-scenes. People don't just want to see what you did. They want to see how you think. And that is your real brand.",
            "Be specific. Not general. Not 'I help businesses grow.' But 'I help SaaS companies reduce churn by 20% using behavioral psychology.' Specificity creates credibility. Credibility creates trust. Trust creates opportunity.",
            "Own your story. Your failures. Your pivots. Your weirdness. Your unconventional path. These are not liabilities. They're differentiators. The person who owns their story is the person who stands out. Because most people hide theirs.",
            "Show up regularly. Not occasionally. Not when you feel like it. Regularly. Weekly. Daily. The person who shows up once is forgotten. The person who shows up consistently is expected. And expectation is the foundation of relationship.",
            "Engage genuinely. Not transactionally. Not strategically. Genuinely. Comment thoughtfully. Share generously. Help without expectation. The person who is genuinely engaged is the person who is genuinely liked. And liked is a form of branded.",
            "The person who designs their personal brand is not being fake. They're being intentional. They're saying 'this is who I am, and I'm going to make sure you can see it.' And that intentionality is what separates the invisible from the magnetic."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One definition written. One story shared. One appearance made. One genuine engagement. One consistency practiced. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A defined focus. A regular showing up. A story owned. A specific value offered. A genuine engagement made. Medium brand clarity."
        else:
            capacity_note = "Good capacity. Deep brand design work. A systematic practice of clarity, consistency, authenticity, and magnetic presence. You have the strength to be known for who you are."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Personal brand design is not about being famous. It's about being known. Most people do good work and remain invisible. They have skills, ideas, and character that could benefit others. But nobody knows because they've never intentionally expressed who they are. The work of personal brand design coaching is about understanding that you already have a brand. It's just probably accidental. And an accidental brand is usually inconsistent, unclear, and invisible. The work is about making it intentional. About defining what you want to be known for. About expressing it consistently. About showing your work. About being specific. And about understanding that the person who is known for something specific is the person who gets opportunities. Not because they're better. But because they're visible. And visibility is the prerequisite of opportunity."
        }

    def get_brand_score(self) -> int:
        """Calculate overall brand health (0-100)."""
        if not self._entries:
            return 25

        avg_clar = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_cons = sum(e.consistency for e in self._entries) / len(self._entries)
        avg_auth = sum(e.authenticity for e in self._entries) / len(self._entries)
        avg_imp = sum(e.impact for e in self._entries) / len(self._entries)
        avg_align = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_vis = sum(e.visibility for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_clar = sum(e.clarity for e in recent) / len(recent)
            recent_imp = sum(e.impact for e in recent) / len(recent)
        else:
            recent_clar = 0
            recent_imp = 0

        # Invisibility penalty
        invis_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_clar_30 = sum(e.clarity for e in last_30) / len(last_30)
            recent_imp_30 = sum(e.impact for e in last_30) / len(last_30)
            if recent_clar_30 < 0.3 and recent_imp_30 < 0.3:
                invis_penalty = 15

        # Type variety
        unique_types = len(set(e.brand_type for e in self._entries))

        score = (avg_clar * 25) + (avg_cons * 15) + (avg_auth * 10) + (avg_imp * 20) + (avg_align * 10) + (avg_vis * 10) + (recent_clar * 5) + (recent_imp * 5) + (unique_types * 2) - invis_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)
            self._stats["avg_impact"] = round(sum(e.impact for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_clar = sum(e.clarity for e in recent) / len(recent)
                recent_imp = sum(e.impact for e in recent) / len(recent)
                self._stats["invisibility_risk"] = recent_clar < 0.3 and recent_imp < 0.3
            else:
                self._stats["invisibility_risk"] = False

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

    def _log_entry(self, entry: BrandEntry):
        try:
            with open(BRAND_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "moment": entry.moment,
                    "brand_type": entry.brand_type,
                    "clarity": entry.clarity,
                    "impact": entry.impact,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pbd_instance: Optional[PersonalBrandDesigner] = None
_pbd_lock = threading.Lock()


def get_personal_brand_designer() -> PersonalBrandDesigner:
    global _pbd_instance
    with _pbd_lock:
        if _pbd_instance is None:
            _pbd_instance = PersonalBrandDesigner()
        return _pbd_instance
