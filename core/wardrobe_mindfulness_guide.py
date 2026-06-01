"""
LOVE Wardrobe Mindfulness Guide — Intentional Clothing Intelligence (Modern AI Pattern)

Most people dress on autopilot. This guide:

1. WARDROBE TRACKING
   - Record wardrobe moments and their characteristics
   - Track wardrobe types (acquire, edit, wear, care, retire, appreciate)
   - Log intention, quality, sustainability, joy, and care of wardrobe choices

2. PATTERN ANALYSIS
   - Identify the user's wardrobe profile (impulsive, hoarding, developing, intentional)
   - Find wardrobe patterns that create satisfaction vs clutter
   - Detect chronic unconscious consumption and its costs

3. INTENTIONALITY BUILDING
   - Suggest practices for mindful wardrobe curation
   - Provide frameworks for quality-over-quantity dressing
   - Recommend practices for sustainable, joyful clothing

4. WARDROBE WISDOM CULTIVATION
   - Track the correlation between intentionality and wardrobe satisfaction
   - Alert when accumulation is replacing curation
   - Celebrate moments of genuine wardrobe clarity

Architecture:
- record_wardrobe(action, type, intention, quality, sustainability, joy, care): Log wardrobe
- get_wardrobe_stats(): Get wardrobe pattern analysis
- get_wardrobe_suggestion(capacity, context): Get suggestion
- get_wardrobe_score(): Calculate overall wardrobe health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "wardrobe_mindfulness_guide"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WARDROBE_LOG = DATA_DIR / "wardrobes.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WardrobeEntry:
    """A tracked wardrobe moment."""
    entry_id: str = ""
    action: str = ""  # what was the action
    wardrobe_type: str = ""  # acquire, edit, wear, care, retire, appreciate
    intention: float = 0.0  # 0-1
    quality: float = 0.0  # 0-1
    sustainability: float = 0.0  # 0-1
    joy: float = 0.0  # 0-1
    care: float = 0.0  # 0-1
    curation: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class WardrobeMindfulnessGuide:
    """
    Intelligent wardrobe mindfulness guide with consumption detection and wardrobe wisdom cultivation.
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
            "avg_intention": 0.0,
            "avg_joy": 0.0,
            "consumption_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_wardrobe(self, action: str = "", wardrobe_type: str = "", intention: float = 0.0, quality: float = 0.0, sustainability: float = 0.0, joy: float = 0.0, care: float = 0.0, curation: float = 0.0, notes: str = "") -> WardrobeEntry:
        """Record a wardrobe moment."""
        entry_id = f"wrd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = WardrobeEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            wardrobe_type=wardrobe_type or "wear",
            intention=intention,
            quality=quality,
            sustainability=sustainability,
            joy=joy,
            care=care,
            curation=curation,
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

    def get_wardrobe_stats(self) -> Dict[str, Any]:
        """Get wardrobe pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "intention_sum": 0.0, "quality_sum": 0.0, "joy_sum": 0.0})
        for e in self._entries:
            by_type[e.wardrobe_type]["count"] += 1
            by_type[e.wardrobe_type]["intention_sum"] += e.intention
            by_type[e.wardrobe_type]["quality_sum"] += e.quality
            by_type[e.wardrobe_type]["joy_sum"] += e.joy

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_intention": round(data["intention_sum"] / count, 2),
                "avg_quality": round(data["quality_sum"] / count, 2),
                "avg_joy": round(data["joy_sum"] / count, 2),
            }

        # Intention analysis
        high_int = [e for e in self._entries if e.intention > 0.7]
        low_int = [e for e in self._entries if e.intention < 0.4]
        if high_int and low_int:
            high_int_joy = sum(e.joy for e in high_int) / len(high_int)
            low_int_joy = sum(e.joy for e in low_int) / len(low_int)
            high_int_qual = sum(e.quality for e in high_int) / len(high_int)
            low_int_qual = sum(e.quality for e in low_int) / len(low_int)
        else:
            high_int_joy = 0
            low_int_joy = 0
            high_int_qual = 0
            low_int_qual = 0

        # Curation analysis
        high_cur = [e for e in self._entries if e.curation > 0.7]
        low_cur = [e for e in self._entries if e.curation < 0.4]
        if high_cur and low_cur:
            high_cur_joy = sum(e.joy for e in high_cur) / len(high_cur)
            low_cur_joy = sum(e.joy for e in low_cur) / len(low_cur)
        else:
            high_cur_joy = 0
            low_cur_joy = 0

        # Consumption risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_int = sum(e.intention for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
            consumption_risk = recent_int < 0.3 and recent_joy < 0.3
        else:
            consumption_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "intention_impact": {
                "high_intention_joy": round(high_int_joy, 2),
                "low_intention_joy": round(low_int_joy, 2),
                "high_intention_quality": round(high_int_qual, 2),
                "low_intention_quality": round(low_int_qual, 2),
            },
            "curation_effect": {
                "high_curation_joy": round(high_cur_joy, 2),
                "low_curation_joy": round(low_cur_joy, 2),
            },
            "consumption_risk": consumption_risk,
            "avg_intention": round(sum(e.intention for e in self._entries) / len(self._entries), 2),
            "avg_joy": round(sum(e.joy for e in self._entries) / len(self._entries), 2),
        }

    def get_wardrobe_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get wardrobe suggestion."""
        suggestions = [
            "Most people have closets full of clothes and nothing to wear. They've accumulated without curating. Bought without intention. Kept without reason. And they stand in front of their closet every morning feeling defeated. This is not a clothing problem. It's an intention problem.",
            "Count what you have. Really count. How many shirts? How many pairs of shoes? How many things you've worn once or never? The number will shock you. And it should. Because every unworn item is a decision you didn't make. A choice you avoided. An intention you lacked.",
            "Edit ruthlessly. If you haven't worn it in a year, let it go. If it doesn't fit, let it go. If you don't love it, let it go. If it doesn't feel like you, let it go. The person who keeps everything wears nothing. The person who keeps only what they love wears everything.",
            "Buy less. Buy better. One quality piece that lasts five years is better than five cheap pieces that last one. Quality feels better. Looks better. Lasts longer. Costs less per wear. And respects the resources that made it.",
            "Know what you actually wear. Track it. For a month. Mark what you wear. At the end, you'll know your uniform. Your essentials. The things that actually serve you. And you'll know what you can let go of. Data defeats delusion.",
            "Care for what you keep. Wash properly. Store well. Repair promptly. Iron when needed. The person who cares for their clothes has fewer clothes. Because the ones they have last longer. And feel better. And look better. Care is curation.",
            "Define your palette. Your neutrals. Your accents. Your textures. Not someone else's. Yours. The colors that make you feel alive. The fabrics that feel good on your skin. The shapes that feel like you. A defined palette makes choosing easy.",
            "Dress for the life you have. Not the life you wish you had. Not the life you think you should have. The actual life. The actual activities. The actual weather. The actual you. The wardrobe that matches your life is the wardrobe that gets worn.",
            "Pause before acquiring. Not 'do I like it?' but 'do I need it?' Not 'is it on sale?' but 'will I wear it?' Not 'does it fit?' but 'does it fit my life?' The pause is the practice. The question is the tool. The answer is the clarity.",
            "The person who cultivates wardrobe mindfulness is not minimal. They're intentional. They understand that every piece of clothing is a choice. A resource. A responsibility. And they choose carefully. Because they understand that what they wear affects how they feel. How they move. How they show up. And that is worth paying attention to."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One item let go. One quality purchase questioned. One outfit appreciated. One care ritual practiced. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A wardrobe audit. A defined palette. A care routine. A curation session. Medium intentionality."
        else:
            capacity_note = "Good capacity. Deep wardrobe mindfulness work. A systematic practice of intention, quality, care, and curation. You have the strength to dress with clarity."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Wardrobe mindfulness is not about minimalism. It's about intentionality. Most people treat their wardrobe as an afterthought. They buy impulsively. They keep habitually. They wear unconsciously. And they wonder why they feel like they have nothing to wear. Why they feel frustrated every morning. Why they feel like their clothes don't represent who they are. The work of wardrobe mindfulness coaching is about understanding that your wardrobe is a mirror of your intentionality. That every piece of clothing is a choice. That accumulation without curation creates clutter. And that the person who curates their wardrobe with care is not just organized. They're expressing who they are. Every single day. Before they even speak."
        }

    def get_wardrobe_score(self) -> int:
        """Calculate overall wardrobe health (0-100)."""
        if not self._entries:
            return 25

        avg_int = sum(e.intention for e in self._entries) / len(self._entries)
        avg_qual = sum(e.quality for e in self._entries) / len(self._entries)
        avg_sus = sum(e.sustainability for e in self._entries) / len(self._entries)
        avg_joy = sum(e.joy for e in self._entries) / len(self._entries)
        avg_care = sum(e.care for e in self._entries) / len(self._entries)
        avg_cur = sum(e.curation for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_int = sum(e.intention for e in recent) / len(recent)
            recent_joy = sum(e.joy for e in recent) / len(recent)
        else:
            recent_int = 0
            recent_joy = 0

        # Consumption penalty
        cons_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_int_30 = sum(e.intention for e in last_30) / len(last_30)
            recent_joy_30 = sum(e.joy for e in last_30) / len(last_30)
            if recent_int_30 < 0.3 and recent_joy_30 < 0.3:
                cons_penalty = 15

        # Type variety
        unique_types = len(set(e.wardrobe_type for e in self._entries))

        score = (avg_int * 25) + (avg_qual * 10) + (avg_sus * 10) + (avg_joy * 20) + (avg_care * 15) + (avg_cur * 10) + (recent_int * 5) + (recent_joy * 5) + (unique_types * 2) - cons_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_intention"] = round(sum(e.intention for e in self._entries) / len(self._entries), 2)
            self._stats["avg_joy"] = round(sum(e.joy for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_int = sum(e.intention for e in recent) / len(recent)
                recent_joy = sum(e.joy for e in recent) / len(recent)
                self._stats["consumption_risk"] = recent_int < 0.3 and recent_joy < 0.3
            else:
                self._stats["consumption_risk"] = False

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

    def _log_entry(self, entry: WardrobeEntry):
        try:
            with open(WARDROBE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "wardrobe_type": entry.wardrobe_type,
                    "intention": entry.intention,
                    "joy": entry.joy,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wmg_instance: Optional[WardrobeMindfulnessGuide] = None
_wmg_lock = threading.Lock()


def get_wardrobe_mindfulness_guide() -> WardrobeMindfulnessGuide:
    global _wmg_instance
    with _wmg_lock:
        if _wmg_instance is None:
            _wmg_instance = WardrobeMindfulnessGuide()
        return _wmg_instance
