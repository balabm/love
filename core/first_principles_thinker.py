"""
LOVE First Principles Thinker — Foundation Intelligence (Modern AI Pattern)

Most people reason by analogy. This thinker:

1. PRINCIPLES TRACKING
   - Record first principles thinking moments and their characteristics
   - Track principles types (deconstruction, reconstruction, assumption_challenging, fundamental_truths)
   - Log depth, clarity, and application of first principles thinking

2. PATTERN ANALYSIS
   - Identify the user's thinking profile (analogical, hybrid, principled, master)
   - Find thinking patterns that innovate vs imitate
   - Detect chronic analogy-dependent thinking and its costs

3. PRINCIPLES BUILDING
   - Suggest practices for breaking problems down to fundamentals
   - Provide frameworks for reconstructing solutions from basics
   - Recommend practices for challenging assumptions

4. FOUNDATIONAL THINKING CULTIVATION
   - Track the correlation between first principles thinking and innovation
   - Alert when thinking is becoming purely analogical
   - Celebrate moments of genuine foundational insight

Architecture:
- record_thinking(problem, type, depth, clarity, application): Log thinking
- get_thinking_stats(): Get thinking pattern analysis
- get_thinking_suggestion(capacity, context): Get suggestion
- get_thinking_score(): Calculate overall thinking health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "first_principles_thinker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

THINKING_LOG = DATA_DIR / "thinkings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ThinkingEntry:
    """A tracked first principles thinking moment."""
    entry_id: str = ""
    problem: str = ""  # what was analyzed
    thinking_type: str = ""  # deconstruction, reconstruction, assumption_challenging, fundamental_truths
    depth: float = 0.0  # 0-1 how deep did you go?
    clarity: float = 0.0  # 0-1
    application: float = 0.0  # 0-1 did you apply the insight?
    assumption_challenged: float = 0.0  # 0-1
    novelty: float = 0.0  # 0-1 how original was the insight?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class FirstPrinciplesThinker:
    """
    Intelligent first principles thinker with analogy detection and foundational thinking cultivation.
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
            "avg_clarity": 0.0,
            "analogy_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_thinking(self, problem: str = "", thinking_type: str = "", depth: float = 0.0, clarity: float = 0.0, application: float = 0.0, assumption_challenged: float = 0.0, novelty: float = 0.0, notes: str = "") -> ThinkingEntry:
        """Record a first principles thinking moment."""
        entry_id = f"fpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = ThinkingEntry(
            entry_id=entry_id,
            problem=problem or "unspecified",
            thinking_type=thinking_type or "deconstruction",
            depth=depth,
            clarity=clarity,
            application=application,
            assumption_challenged=assumption_challenged,
            novelty=novelty,
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

    def get_thinking_stats(self) -> Dict[str, Any]:
        """Get thinking pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "depth_sum": 0.0, "clarity_sum": 0.0, "novelty_sum": 0.0})
        for e in self._entries:
            by_type[e.thinking_type]["count"] += 1
            by_type[e.thinking_type]["depth_sum"] += e.depth
            by_type[e.thinking_type]["clarity_sum"] += e.clarity
            by_type[e.thinking_type]["novelty_sum"] += e.novelty

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_depth": round(data["depth_sum"] / count, 2),
                "avg_clarity": round(data["clarity_sum"] / count, 2),
                "avg_novelty": round(data["novelty_sum"] / count, 2),
            }

        # Depth analysis
        high_depth = [e for e in self._entries if e.depth > 0.7]
        low_depth = [e for e in self._entries if e.depth < 0.4]
        if high_depth and low_depth:
            high_depth_app = sum(e.application for e in high_depth) / len(high_depth)
            low_depth_app = sum(e.application for e in low_depth) / len(low_depth)
            high_depth_nov = sum(e.novelty for e in high_depth) / len(high_depth)
            low_depth_nov = sum(e.novelty for e in low_depth) / len(low_depth)
        else:
            high_depth_app = 0
            low_depth_app = 0
            high_depth_nov = 0
            low_depth_nov = 0

        # Assumption analysis
        high_ass = [e for e in self._entries if e.assumption_challenged > 0.7]
        low_ass = [e for e in self._entries if e.assumption_challenged < 0.4]
        if high_ass and low_ass:
            high_ass_nov = sum(e.novelty for e in high_ass) / len(high_ass)
            low_ass_nov = sum(e.novelty for e in low_ass) / len(low_ass)
        else:
            high_ass_nov = 0
            low_ass_nov = 0

        # Analogy risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_ass = sum(e.assumption_challenged for e in recent) / len(recent)
            analogy_risk = recent_depth < 0.3 and recent_ass < 0.3
        else:
            analogy_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "depth_impact": {
                "high_depth_application": round(high_depth_app, 2),
                "low_depth_application": round(low_depth_app, 2),
                "high_depth_novelty": round(high_depth_nov, 2),
                "low_depth_novelty": round(low_depth_nov, 2),
            },
            "assumption_effect": {
                "high_assumption_novelty": round(high_ass_nov, 2),
                "low_assumption_novelty": round(low_ass_nov, 2),
            },
            "analogy_risk": analogy_risk,
            "avg_depth": round(sum(e.depth for e in self._entries) / len(self._entries), 2),
            "avg_clarity": round(sum(e.clarity for e in self._entries) / len(self._entries), 2),
        }

    def get_thinking_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get thinking suggestion."""
        suggestions = [
            "Reasoning by analogy is fast. Reasoning from first principles is slow. But first principles gets you to places analogy can't. Most innovation comes from first principles. Most imitation comes from analogy.",
            "Ask why five times. Not as a technique. As a practice. Why do I believe this? Why is this done this way? Why is this the right approach? Keep asking until you hit bedrock. That's first principles.",
            "Every field has its fundamental truths. In physics, it's the laws of motion. In business, it's supply and demand. In relationships, it's reciprocity. Find the fundamentals of your field. Build from there.",
            "The person who copies what others do is limited by what others have done. The person who builds from first principles is limited only by physics and logic. That's the difference between incremental and transformative.",
            "Challenge your assumptions. Not just the ones you disagree with. Especially the ones you agree with. The assumptions you hold most deeply are the ones you never examine. And they're usually the ones holding you back.",
            "Deconstruction is not destruction. It's understanding. Take the problem apart. See what it's made of. Then reconstruct it better. Most people try to improve the whole without understanding the parts.",
            "Elon Musk didn't build electric cars by copying Toyota. He asked: what are batteries made of? What do they cost? What's the physics? That's first principles. The answer was surprising. And transformative.",
            "Your beliefs are not your own. Most of them were installed by parents, teachers, culture, media. Not examined. Not chosen. First principles thinking requires you to uninstall the borrowed beliefs. And install your own.",
            "The simplest explanation is usually correct. But the simplest explanation at the right level of analysis. Not the oversimplified one. Not the overcomplicated one. The one that captures the essence without the noise.",
            "First principles thinking feels uncomfortable. Because it removes the comfort of consensus. When everyone agrees, you don't have to think. When you think from first principles, you're often alone. That's the price of originality."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One why asked five times. One assumption challenged. One problem deconstructed. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A first principles analysis of one problem. A fundamental truth identified. A reconstruction attempted. Medium thinking."
        else:
            capacity_note = "Good capacity. Deep foundational work. A systematic practice of deconstruction and reconstruction. You have the strength to think from the ground up."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "First principles thinking is the most powerful thinking tool that most people never use. It's the practice of breaking down problems to their fundamental truths and building up from there. Most people don't do this. They reason by analogy. They look at what others do and copy it. They follow tradition. They accept assumptions. And they wonder why they can't innovate. Why they can't solve problems that others haven't solved. The answer is simple: they're not thinking. They're imitating. First principles thinking is hard. It requires you to question everything. To deconstruct what seems obvious. To rebuild from fundamentals. To be willing to be wrong. To be willing to be alone. But it's the only way to think originally. To solve problems that haven't been solved. To create what hasn't been created. The person who thinks from first principles is not limited by what has been done. They're limited only by what's possible."
        }

    def get_thinking_score(self) -> int:
        """Calculate overall thinking health (0-100)."""
        if not self._entries:
            return 25

        avg_depth = sum(e.depth for e in self._entries) / len(self._entries)
        avg_clarity = sum(e.clarity for e in self._entries) / len(self._entries)
        avg_app = sum(e.application for e in self._entries) / len(self._entries)
        avg_ass = sum(e.assumption_challenged for e in self._entries) / len(self._entries)
        avg_nov = sum(e.novelty for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_depth = sum(e.depth for e in recent) / len(recent)
            recent_clarity = sum(e.clarity for e in recent) / len(recent)
        else:
            recent_depth = 0
            recent_clarity = 0

        # Analogy penalty
        analogy_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_depth_30 = sum(e.depth for e in last_30) / len(last_30)
            recent_ass_30 = sum(e.assumption_challenged for e in last_30) / len(last_30)
            if recent_depth_30 < 0.3 and recent_ass_30 < 0.3:
                analogy_penalty = 15

        # Type variety
        unique_types = len(set(e.thinking_type for e in self._entries))

        score = (avg_depth * 25) + (avg_clarity * 20) + (avg_app * 15) + (avg_ass * 15) + (avg_nov * 10) + (recent_depth * 5) + (recent_clarity * 5) + (unique_types * 2) - analogy_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_depth"] = round(sum(e.depth for e in self._entries) / len(self._entries), 2)
            self._stats["avg_clarity"] = round(sum(e.clarity for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_depth = sum(e.depth for e in recent) / len(recent)
                recent_ass = sum(e.assumption_challenged for e in recent) / len(recent)
                self._stats["analogy_risk"] = recent_depth < 0.3 and recent_ass < 0.3
            else:
                self._stats["analogy_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.first_principles_thinker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.first_principles_thinker")

    def _log_entry(self, entry: ThinkingEntry):
        try:
            with open(THINKING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "problem": entry.problem,
                    "thinking_type": entry.thinking_type,
                    "depth": entry.depth,
                    "clarity": entry.clarity,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.first_principles_thinker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_fpt_instance: Optional[FirstPrinciplesThinker] = None
_fpt_lock = threading.Lock()


def get_first_principles_thinker() -> FirstPrinciplesThinker:
    global _fpt_instance
    with _fpt_lock:
        if _fpt_instance is None:
            _fpt_instance = FirstPrinciplesThinker()
        return _fpt_instance
