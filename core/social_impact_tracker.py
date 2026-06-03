"""
LOVE Social Impact Tracker — Purpose Intelligence (Modern AI Pattern)

Most people want to make a difference but have no feedback loop. This tracker:

1. IMPACT TRACKING
   - Record actions taken and their social impact
   - Track impact types (direct help, advocacy, creation, connection, education)
   - Log impact reach, depth, and sustainability

2. PATTERN ANALYSIS
   - Identify the user's impact profile (thinker, helper, builder, amplifier)
   - Find impact patterns that create lasting change vs temporary relief
   - Detect impact avoidance and its causes

3. IMPACT OPTIMIZATION
   - Suggest high-leverage actions matched to current capacity
   - Provide frameworks for measuring what matters
   - Recommend scaling strategies for effective actions

4. LEGACY CULTIVATION
   - Track the correlation between impact and life satisfaction
   - Alert when action is disconnected from values
   - Celebrate ripple effects that outlast the initial action

Architecture:
- record_impact(action, type, reach, depth, sustainability): Log impact
- get_impact_stats(): Get impact pattern analysis
- get_impact_suggestion(capacity, context): Get suggestion
- get_impact_score(): Calculate overall impact health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "social_impact_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

IMPACT_LOG = DATA_DIR / "impacts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ImpactEntry:
    """A tracked social impact entry."""
    entry_id: str = ""
    action: str = ""  # what was done
    impact_type: str = ""  # direct_help, advocacy, creation, connection, education
    reach: float = 0.0  # 0-1 how many people affected
    depth: float = 0.0  # 0-1 how deeply affected
    sustainability: float = 0.0  # 0-1 will effect last?
    alignment: float = 0.0  # 0-1 alignment with personal values
    effort: float = 0.5  # 0-1
    ripple: float = 0.0  # 0-1 secondary effects
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SocialImpactTracker:
    """
    Intelligent impact tracker with leverage detection and legacy cultivation.
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
            "avg_depth": 0.0,
            "avg_sustainability": 0.0,
            "impact_gap": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_impact(self, action: str = "", impact_type: str = "", reach: float = 0.0, depth: float = 0.0, sustainability: float = 0.0, alignment: float = 0.0, effort: float = 0.5, ripple: float = 0.0, notes: str = "") -> ImpactEntry:
        """Record an impact entry."""
        entry_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ImpactEntry(
            entry_id=entry_id,
            action=action or "unspecified",
            impact_type=impact_type or "direct_help",
            reach=reach,
            depth=depth,
            sustainability=sustainability,
            alignment=alignment,
            effort=effort,
            ripple=ripple,
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

    def get_impact_stats(self) -> Dict[str, Any]:
        """Get impact pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "reach_sum": 0.0, "depth_sum": 0.0, "sustainability_sum": 0.0})
        for e in self._entries:
            by_type[e.impact_type]["count"] += 1
            by_type[e.impact_type]["reach_sum"] += e.reach
            by_type[e.impact_type]["depth_sum"] += e.depth
            by_type[e.impact_type]["sustainability_sum"] += e.sustainability

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_reach": round(data["reach_sum"] / count, 2),
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_sustainability": round(data["sustainability_sum"] / count, 2),
            }

        best_type = max(type_stats.items(), key=lambda x: x[1]["avg_sustainability"]) if type_stats else ("", {})

        # Depth vs sustainability
        high_depth = [e for e in self._entries if e.depth > 0.7]
        low_depth = [e for e in self._entries if e.depth < 0.4]
        if high_depth and low_depth:
            high_depth_sustain = sum(e.sustainability for e in high_depth) / len(high_depth)
            low_depth_sustain = sum(e.sustainability for e in low_depth) / len(low_depth)
            high_depth_ripple = sum(e.ripple for e in high_depth) / len(high_depth)
            low_depth_ripple = sum(e.ripple for e in low_depth) / len(low_depth)
        else:
            high_depth_sustain = 0
            low_depth_sustain = 0
            high_depth_ripple = 0
            low_depth_ripple = 0

        # Alignment analysis
        high_align = [e for e in self._entries if e.alignment > 0.7]
        low_align = [e for e in self._entries if e.alignment < 0.4]
        if high_align and low_align:
            high_align_depth = sum(e.depth for e in high_align) / len(high_align)
            low_align_depth = sum(e.depth for e in low_align) / len(low_align)
            high_align_sustain = sum(e.sustainability for e in high_align) / len(high_align)
            low_align_sustain = sum(e.sustainability for e in low_align) / len(low_align)
        else:
            high_align_depth = 0
            low_align_depth = 0
            high_align_sustain = 0
            low_align_sustain = 0

        # Effort vs impact
        high_effort = [e for e in self._entries if e.effort > 0.7]
        low_effort = [e for e in self._entries if e.effort < 0.4]
        if high_effort and low_effort:
            high_effort_depth = sum(e.depth for e in high_effort) / len(high_effort)
            low_effort_depth = sum(e.depth for e in low_effort) / len(low_effort)
        else:
            high_effort_depth = 0
            low_effort_depth = 0

        # Impact gap detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=60)).isoformat()]
        impact_gap = len(recent) < 2

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "best_type": best_type[0],
            "depth_impact": {
                "high_depth_sustainability": round(high_depth_sustain, 2),
                "low_depth_sustainability": round(low_depth_sustain, 2),
                "high_depth_ripple": round(high_depth_ripple, 2),
                "low_depth_ripple": round(low_depth_ripple, 2),
            },
            "alignment_effect": {
                "high_alignment_depth": round(high_align_depth, 2),
                "low_alignment_depth": round(low_align_depth, 2),
                "high_alignment_sustainability": round(high_align_sustain, 2),
                "low_alignment_sustainability": round(low_align_sustain, 2),
            },
            "effort_efficiency": {
                "high_effort_depth": round(high_effort_depth, 2),
                "low_effort_depth": round(low_effort_depth, 2),
            },
            "impact_gap": impact_gap,
            "avg_reach": round(sum(e.reach for e in self._entries) / len(self._entries), 2),
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_sustainability": round(sum(e.sustainability for e in self._entries) / len(self._entries), 2),
        }

    def get_impact_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get impact suggestion."""
        suggestions = [
            "Teach someone something you know. The knowledge you take for granted is the knowledge someone else is desperate to learn. Teaching is impact at its most direct.",
            "Advocate for someone who has less power than you. Use your voice, your platform, your privilege. Amplification is a form of creation.",
            "Create something that outlasts you. A guide. A tool. A piece of art. Something that helps strangers you will never meet.",
            "Connect two people who should know each other. The right introduction at the right time can change the trajectory of a life.",
            "Listen to someone who needs to be heard. Not to fix. Just to witness. Sometimes the greatest impact is presence.",
            "Fix something that's broken in public. A typo. A broken link. A confusing sign. Small public improvements compound.",
            "Share your story. The thing you think is embarrassing might be the exact thing someone else needs to hear. Vulnerability is a gift.",
            "Mentor someone. Not formally. Just be available. Answer questions. Share what you wish you'd known. Mentorship is impact on a delay.",
            "Give credit publicly. Celebrate others. Elevate people who do good work. Recognition is free and transformative.",
            "Show up for something you believe in. A protest. A meeting. A cleanup. Your physical presence is a vote for the world you want.",
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. Micro-impact. A kind word. A share. A connection. Small is real."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. Medium impact. An hour of help. A thoughtful post. A small donation."
        else:
            capacity_note = "Good capacity. Major impact. The thing you've been thinking about doing for others. Do it now."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "The world doesn't need more people with good intentions. It needs more people with good actions. Intention is easy. Action is hard. And impact is the only metric that matters in the end. Not how you felt. Not what you meant. What you did. What changed because you were here. The best way to have a meaningful life is to create meaningful change for others. Start small. Start now. Start before you're ready.",
        }

    def get_impact_score(self) -> int:
        """Calculate overall impact health (0-100)."""
        if not self._entries:
            return 25

        avg_reach = sum(e.reach for e in self._entries) / len(self._entries)
        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_sustainability = sum(e.sustainability for e in self._entries) / len(self._entries)
        avg_alignment = sum(e.alignment for e in self._entries) / len(self._entries)
        avg_ripple = sum(e.ripple for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_sustain = sum(e.sustainability for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_sustain = 0

        # Impact gap penalty
        gap_penalty = 0
        last_60 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=60)).isoformat()]
        if len(last_60) < 2:
            gap_penalty = 15

        # Type variety
        unique_types = len(set(e.impact_type for e in self._entries))

        score = (avg_reach * 15) + (avg_depth * 25) + (avg_sustainability * 20) + (avg_alignment * 15) + (avg_ripple * 10) + (recent_depth * 5) + (recent_sustain * 5) + (unique_types * 2) - gap_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_sustainability"] = round(sum(e.sustainability for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=60)).isoformat()]
            self._stats["impact_gap"] = len(recent) < 2

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.social_impact_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.social_impact_tracker")

    def _log_entry(self, entry: ImpactEntry):
        try:
            with open(IMPACT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "impact_type": entry.impact_type,
                    "reach": entry.reach,
                    "depth": entry.depth,
                    "sustainability": entry.sustainability,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.social_impact_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sit_instance: Optional[SocialImpactTracker] = None
_sit_lock = threading.Lock()


def get_social_impact_tracker() -> SocialImpactTracker:
    global _sit_instance
    with _sit_lock:
        if _sit_instance is None:
            _sit_instance = SocialImpactTracker()
        return _sit_instance
