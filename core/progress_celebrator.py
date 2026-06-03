"""
LOVE Progress Celebrator — Recognition Intelligence (Modern AI Pattern)

Most progress goes unnoticed. This celebrator:

1. PROGRESS TRACKING
   - Record milestones, wins, and progress moments
   - Track the size and significance of each win
   - Log what made the win possible (effort, luck, support, strategy)

2. PATTERN ANALYSIS
   - Identify the user's celebration style (quiet, social, material, experiential)
   - Find which wins the user tends to dismiss vs celebrate
   - Detect progress blindness (advancing without noticing)

3. CELEBRATION GENERATION
   - Suggest celebration ideas matched to win size and user style
   - Provide micro-celebrations for small wins
   - Recommend reflection practices for big wins

4. MOTIVATION AMPLIFICATION
   - Track the correlation between celebration and continued effort
   - Alert when the user is grinding without acknowledging progress
   - Celebrate the habit of celebrating

Architecture:
- record_win(description, size, attribution, celebration): Log win
- get_progress_stats(): Get progress pattern analysis
- get_celebration_suggestion(win_size, style): Get celebration idea
- get_progress_score(): Calculate overall progress recognition health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "progress_celebrator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WIN_LOG = DATA_DIR / "wins.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Win:
    """A tracked win."""
    win_id: str = ""
    description: str = ""
    win_size: str = ""  # micro, small, medium, large, milestone, breakthrough
    domain: str = ""  # work, health, relationship, creativity, learning, finance, character
    attribution: str = ""  # effort, strategy, luck, support, timing, persistence
    celebration: str = ""  # what they did to celebrate
    celebration_quality: float = 0.5  # 0-1
    significance: float = 0.5  # 0-1, how much it mattered
    dopamine_boost: float = 0.5  # 0-1, how good it felt
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ProgressCelebrator:
    """
    Intelligent progress celebrator with celebration matching and progress blindness detection.
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
        self._wins: deque = deque(maxlen=300)
        self._stats = {
            "total_wins": 0,
            "avg_celebration_quality": 0.0,
            "avg_significance": 0.0,
            "celebration_rate": 0.0,
            "dominant_domain": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_win(self, description: str = "", win_size: str = "", domain: str = "", attribution: str = "", celebration: str = "", celebration_quality: float = 0.5, significance: float = 0.5, dopamine: float = 0.5, notes: str = "") -> Win:
        """Record a win."""
        win_id = f"win_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._wins)}"
        win = Win(
            win_id=win_id,
            description=description or "unspecified",
            win_size=win_size or "small",
            domain=domain or "general",
            attribution=attribution or "effort",
            celebration=celebration,
            celebration_quality=celebration_quality,
            significance=significance,
            dopamine_boost=dopamine,
            notes=notes,
        )

        with self._lock:
            self._wins.append(win)
            self._stats["total_wins"] += 1
            self._update_stats()

        self._save_stats()
        self._log_win(win)

        return win

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_progress_stats(self) -> Dict[str, Any]:
        """Get progress pattern analysis."""
        if not self._wins:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "significance_sum": 0.0, "celebration_sum": 0.0, "celebrated": 0})
        for w in self._wins:
            by_domain[w.domain]["count"] += 1
            by_domain[w.domain]["significance_sum"] += w.significance
            by_domain[w.domain]["celebration_sum"] += w.celebration_quality
            if w.celebration:
                by_domain[w.domain]["celebrated"] += 1

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "avg_significance": round(data["significance_sum"] / count, 2),
                "avg_celebration": round(data["celebration_sum"] / count, 2),
                "celebration_rate": round(data["celebrated"] / count, 2),
            }

        dominant = max(domain_stats.items(), key=lambda x: x[1]["count"]) if domain_stats else ("", {})

        # Size analysis
        by_size = defaultdict(lambda: {"count": 0, "celebrated": 0, "dopamine_sum": 0.0})
        for w in self._wins:
            by_size[w.win_size]["count"] += 1
            if w.celebration:
                by_size[w.win_size]["celebrated"] += 1
            by_size[w.win_size]["dopamine_sum"] += w.dopamine_boost

        size_stats = {}
        for s, data in by_size.items():
            count = data["count"]
            size_stats[s] = {
                "count": count,
                "celebration_rate": round(data["celebrated"] / count, 2),
                "avg_dopamine": round(data["dopamine_sum"] / count, 2),
            }

        # Attribution analysis
        by_attr = defaultdict(lambda: {"count": 0, "significance_sum": 0.0})
        for w in self._wins:
            by_attr[w.attribution]["count"] += 1
            by_attr[w.attribution]["significance_sum"] += w.significance

        attr_stats = {}
        for a, data in by_attr.items():
            count = data["count"]
            attr_stats[a] = {
                "count": count,
                "avg_significance": round(data["significance_sum"] / count, 2),
            }

        # Progress blindness detection
        recent = [w for w in self._wins if w.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            celebrated_recent = sum(1 for w in recent if w.celebration)
            celebration_rate = celebrated_recent / len(recent)
            blindness = celebration_rate < 0.3
        else:
            blindness = False

        return {
            "total_wins": len(self._wins),
            "domain_stats": domain_stats,
            "dominant_domain": dominant[0],
            "size_stats": size_stats,
            "attribution_stats": attr_stats,
            "celebration_rate": round(sum(1 for w in self._wins if w.celebration) / len(self._wins), 2),
            "avg_celebration_quality": round(sum(w.celebration_quality for w in self._wins) / len(self._wins), 2),
            "avg_significance": round(sum(w.significance for w in self._wins) / len(self._wins), 2),
            "progress_blindness": blindness,
        }

    def get_celebration_suggestion(self, win_size: str = "small", style: str = "", significance: float = 0.5) -> Dict[str, Any]:
        """Get celebration idea."""
        celebrations = {
            "micro": [
                "Take 3 deep breaths and say 'I did that'",
                "Do a tiny victory dance (even if it's just finger wiggles)",
                "Tell one person what you just did",
                "Mark it on a visible tracker or calendar",
            ],
            "small": [
                "Treat yourself to a favorite beverage or snack",
                "Take a 10-minute walk in a nice place",
                "Text a friend and tell them your win",
                "Write a one-sentence journal entry about it",
            ],
            "medium": [
                "Buy yourself something small you've been wanting",
                "Take an afternoon off for something fun",
                "Cook or order a special meal",
                "Share the win in a group chat or social media",
            ],
            "large": [
                "Plan a day trip or experience you've been wanting",
                "Buy something meaningful that commemorates the achievement",
                "Throw a small gathering (even just 2 people)",
                "Document the journey: before, during, after",
            ],
            "milestone": [
                "Take a day off entirely. Rest is part of the achievement.",
                "Invest in something that supports your next milestone",
                "Write a letter to your past self who started this",
                "Create a ritual that marks the transition",
            ],
            "breakthrough": [
                "This changes things. Take time to integrate before rushing to the next goal.",
                "Share your story with someone who needs to hear it",
                "Upgrade something in your life that supports who you're becoming",
                "Document the breakthrough and what made it possible",
            ],
        }

        selected = celebrations.get(win_size, celebrations["small"])
        celebration = random.choice(selected)

        if style == "quiet":
            celebration = "Take 10 minutes of silence to feel the win. No phone. Just presence."
        elif style == "social":
            celebration = "Call someone who will be genuinely happy for you. Share the details."
        elif style == "material":
            celebration = "Buy something that represents the win. Every time you see it, remember."
        elif style == "experiential":
            celebration = "Do something you've never done before. New experiences cement new identities."

        if significance > 0.8:
            note = "This is a big one. Don't rush past it. Savor it like a fine meal."
        elif significance > 0.5:
            note = "This matters. Let yourself feel it. You earned this."
        else:
            note = "Small wins compound. Celebrating them trains your brain to notice progress."

        return {
            "win_size": win_size,
            "style": style or "matched",
            "celebration": celebration,
            "significance": significance,
            "note": note,
            "reflection": "What did this win prove about you? What becomes possible now?",
        }

    def get_progress_score(self) -> int:
        """Calculate overall progress recognition health (0-100)."""
        if not self._wins:
            return 30

        # Celebration rate
        celebrated = sum(1 for w in self._wins if w.celebration)
        celebration_rate = celebrated / len(self._wins)

        # Celebration quality
        avg_quality = sum(w.celebration_quality for w in self._wins) / len(self._wins)

        # Significance awareness
        avg_significance = sum(w.significance for w in self._wins) / len(self._wins)

        # Dopamine (feeling good about wins)
        avg_dopamine = sum(w.dopamine_boost for w in self._wins) / len(self._wins)

        # Variety of domains
        unique_domains = len(set(w.domain for w in self._wins))

        # Recent activity
        recent = [w for w in self._wins if w.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        recent_bonus = min(15, len(recent) * 3)

        # Size variety
        unique_sizes = len(set(w.win_size for w in self._wins))

        score = (celebration_rate * 25) + (avg_quality * 15) + (avg_significance * 15) + (avg_dopamine * 15) + (unique_domains * 2) + recent_bonus + (unique_sizes * 2)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._wins:
            celebrated = sum(1 for w in self._wins if w.celebration)
            self._stats["celebration_rate"] = round(celebrated / len(self._wins), 2)
            self._stats["avg_celebration_quality"] = round(sum(w.celebration_quality for w in self._wins) / len(self._wins), 2)
            self._stats["avg_significance"] = round(sum(w.significance for w in self._wins) / len(self._wins), 2)

            by_domain = defaultdict(int)
            for w in self._wins:
                by_domain[w.domain] += 1
            if by_domain:
                self._stats["dominant_domain"] = max(by_domain.items(), key=lambda x: x[1])[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.progress_celebrator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.progress_celebrator")

    def _log_win(self, win: Win):
        try:
            with open(WIN_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": win.timestamp,
                    "description": win.description,
                    "size": win.win_size,
                    "domain": win.domain,
                    "attribution": win.attribution,
                    "celebration": win.celebration,
                    "significance": win.significance,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.progress_celebrator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pc_instance: Optional[ProgressCelebrator] = None
_pc_lock = threading.Lock()


def get_progress_celebrator() -> ProgressCelebrator:
    global _pc_instance
    with _pc_lock:
        if _pc_instance is None:
            _pc_instance = ProgressCelebrator()
        return _pc_instance
