"""
LOVE Self-Compassion Coach — Inner Kindness Intelligence (Modern AI Pattern)

Most self-improvement is self-criticism in disguise. This coach:

1. SELF-TALK TRACKING
   - Record self-critical vs self-compassionate thoughts
   - Track the intensity and frequency of inner criticism
   - Log situations that trigger harsh self-judgment

2. PATTERN ANALYSIS
   - Identify themes in self-criticism (perfectionism, comparison, shame)
   - Find which life areas get the most negative self-talk
   - Detect the gap between how the user treats others vs themselves

3. COMPASSION TRAINING
   - Generate self-compassion reframes for specific criticisms
   - Suggest Kristin Neff's three components: mindfulness, common humanity, self-kindness
   - Provide guided self-compassion exercises

4. PROGRESS TRACKING
   - Calculate self-compassion score over time
   - Identify triggers and proactive interventions
   - Celebrate shifts from criticism to kindness

Architecture:
- record_thought(thought, type, trigger, intensity): Log self-talk
- get_self_compassion_stats(): Get inner dialogue analysis
- get_reframe(criticism): Get compassionate reframe
- get_self_compassion_score(): Calculate overall self-kindness level
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "self_compassion_coach"
DATA_DIR.mkdir(parents=True, exist_ok=True)

THOUGHT_LOG = DATA_DIR / "thoughts.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class SelfTalk:
    """A tracked self-talk moment."""
    thought_id: str = ""
    thought: str = ""  # the actual thought
    talk_type: str = ""  # critical, compassionate, neutral
    trigger: str = ""  # what triggered it
    life_area: str = ""  # work, appearance, relationships, performance, parenting, etc.
    intensity: float = 0.5  # 0-1
    would_say_to_friend: bool = False  # would you say this to a friend?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SelfCompassionCoach:
    """
    Intelligent self-compassion coach with thought tracking and reframe generation.
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
        self._thoughts: deque = deque(maxlen=300)
        self._stats = {
            "total_thoughts": 0,
            "critical_rate": 0.0,
            "avg_intensity": 0.0,
            "self_friend_gap": 0.0,
            "most_critical_area": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_thought(self, thought: str = "", talk_type: str = "", trigger: str = "", life_area: str = "", intensity: float = 0.5, would_say_to_friend: bool = False, notes: str = "") -> SelfTalk:
        """Record a self-talk moment."""
        thought_id = f"thought_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._thoughts)}"
        st = SelfTalk(
            thought_id=thought_id,
            thought=thought or "unspecified",
            talk_type=talk_type or "neutral",
            trigger=trigger,
            life_area=life_area or "general",
            intensity=intensity,
            would_say_to_friend=would_say_to_friend,
            notes=notes,
        )

        with self._lock:
            self._thoughts.append(st)
            self._stats["total_thoughts"] += 1
            self._update_stats()

        self._save_stats()
        self._log_thought(st)

        return st

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_self_compassion_stats(self) -> Dict[str, Any]:
        """Get inner dialogue analysis."""
        if not self._thoughts:
            return {"status": "insufficient_data"}

        # Type distribution
        by_type = defaultdict(int)
        for t in self._thoughts:
            by_type[t.talk_type] += 1

        total = len(self._thoughts)
        type_dist = {k: round(v / total, 2) for k, v in by_type.items()}

        # Area analysis
        by_area = defaultdict(lambda: {"count": 0, "critical": 0, "intensity_sum": 0.0})
        for t in self._thoughts:
            by_area[t.life_area]["count"] += 1
            if t.talk_type == "critical":
                by_area[t.life_area]["critical"] += 1
            by_area[t.life_area]["intensity_sum"] += t.intensity

        area_stats = {}
        for area, data in by_area.items():
            count = data["count"]
            area_stats[area] = {
                "count": count,
                "critical_rate": round(data["critical"] / count, 2),
                "avg_intensity": round(data["intensity_sum"] / count, 2),
            }

        # Most critical area
        most_critical = max(area_stats.items(), key=lambda x: x[1]["critical_rate"]) if area_stats else ("", {})

        # Self-friend gap
        critical_thoughts = [t for t in self._thoughts if t.talk_type == "critical"]
        if critical_thoughts:
            would_say = sum(1 for t in critical_thoughts if t.would_say_to_friend)
            gap = 1 - (would_say / len(critical_thoughts))
        else:
            gap = 0

        # Trend
        recent = [t for t in self._thoughts if t.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_critical = sum(1 for t in recent if t.talk_type == "critical")
            recent_rate = recent_critical / len(recent)
            older = [t for t in self._thoughts if t.timestamp <= (datetime.now() - timedelta(days=14)).isoformat()]
            if older:
                older_critical = sum(1 for t in older if t.talk_type == "critical")
                older_rate = older_critical / len(older)
                trend = "improving" if recent_rate < older_rate - 0.05 else "declining" if recent_rate > older_rate + 0.05 else "stable"
            else:
                trend = "new"
        else:
            trend = "stable"

        return {
            "total_thoughts": total,
            "type_distribution": type_dist,
            "area_stats": area_stats,
            "most_critical_area": most_critical[0],
            "critical_rate": type_dist.get("critical", 0),
            "compassionate_rate": type_dist.get("compassionate", 0),
            "avg_intensity": round(sum(t.intensity for t in self._thoughts) / total, 2),
            "self_friend_gap": round(gap, 2),
            "trend": trend,
        }

    def get_reframe(self, criticism: str = "", area: str = "") -> Dict[str, Any]:
        """Get compassionate reframe."""
        reframes = {
            "perfectionism": {
                "criticism": "I messed up. I'm a failure.",
                "mindfulness": "I'm having a hard time right now. This feeling is temporary.",
                "common_humanity": "Everyone makes mistakes. This is part of being human.",
                "self_kindness": "I did my best with what I had. I can learn from this.",
            },
            "comparison": {
                "criticism": "Everyone else is doing better than me.",
                "mindfulness": "I'm feeling inadequate. That's a feeling, not a fact.",
                "common_humanity": "Everyone struggles. Social media shows highlight reels.",
                "self_kindness": "I'm on my own path. My journey is valid.",
            },
            "appearance": {
                "criticism": "I look terrible today.",
                "mindfulness": "I'm noticing critical thoughts about my body. They're just thoughts.",
                "common_humanity": "Everyone has days they don't feel great about how they look.",
                "self_kindness": "My body does amazing things for me. I'm grateful for it.",
            },
            "work": {
                "criticism": "I'm not good enough for this job.",
                "mindfulness": "I'm feeling imposter syndrome. Many people feel this.",
                "common_humanity": "Even the most successful people doubt themselves sometimes.",
                "self_kindness": "I was hired for a reason. I bring unique value.",
            },
            "relationships": {
                "criticism": "I'm too much for people. I'll end up alone.",
                "mindfulness": "I'm feeling fear of abandonment. This is an old wound.",
                "common_humanity": "Everyone fears rejection. It's a universal human experience.",
                "self_kindness": "I'm worthy of love exactly as I am. The right people will stay.",
            },
            "parenting": {
                "criticism": "I'm a bad parent. I lost my temper.",
                "mindfulness": "I'm feeling guilty. Guilt means I care.",
                "common_humanity": "All parents struggle. There is no perfect parent.",
                "self_kindness": "I can repair this. Apologizing to my child models accountability.",
            },
        }

        base = reframes.get(area, reframes["perfectionism"])

        return {
            "area": area,
            "original_criticism": criticism or base["criticism"],
            "mindfulness": base["mindfulness"],
            "common_humanity": base["common_humanity"],
            "self_kindness": base["self_kindness"],
            "exercise": "Place hand on heart. Say the self-kindness phrase three times. Breathe.",
        }

    def get_self_compassion_score(self) -> int:
        """Calculate overall self-kindness level (0-100)."""
        if not self._thoughts:
            return 50

        # Critical rate (lower is better)
        critical = sum(1 for t in self._thoughts if t.talk_type == "critical")
        critical_rate = critical / len(self._thoughts)

        # Compassionate rate (higher is better)
        compassionate = sum(1 for t in self._thoughts if t.talk_type == "compassionate")
        compassionate_rate = compassionate / len(self._thoughts)

        # Intensity of critical thoughts
        critical_intensity = [t.intensity for t in self._thoughts if t.talk_type == "critical"]
        avg_critical_intensity = sum(critical_intensity) / max(1, len(critical_intensity))

        # Self-friend gap (lower is better)
        critical_thoughts = [t for t in self._thoughts if t.talk_type == "critical"]
        if critical_thoughts:
            would_say = sum(1 for t in critical_thoughts if t.would_say_to_friend)
            gap = 1 - (would_say / len(critical_thoughts))
        else:
            gap = 0

        # Recent trend bonus
        recent = [t for t in self._thoughts if t.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        if recent:
            recent_compassionate = sum(1 for t in recent if t.talk_type == "compassionate")
            recent_rate = recent_compassionate / len(recent)
        else:
            recent_rate = compassionate_rate

        score = (compassionate_rate * 35) + ((1 - critical_rate) * 25) + ((1 - avg_critical_intensity) * 15) + ((1 - gap) * 10) + (recent_rate * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._thoughts:
            critical = sum(1 for t in self._thoughts if t.talk_type == "critical")
            self._stats["critical_rate"] = round(critical / len(self._thoughts), 2)
            self._stats["avg_intensity"] = round(sum(t.intensity for t in self._thoughts) / len(self._thoughts), 2)

            critical_thoughts = [t for t in self._thoughts if t.talk_type == "critical"]
            if critical_thoughts:
                would_say = sum(1 for t in critical_thoughts if t.would_say_to_friend)
                self._stats["self_friend_gap"] = round(1 - (would_say / len(critical_thoughts)), 2)

            by_area = defaultdict(lambda: {"critical": 0, "total": 0})
            for t in self._thoughts:
                by_area[t.life_area]["total"] += 1
                if t.talk_type == "critical":
                    by_area[t.life_area]["critical"] += 1
            
            if by_area:
                most = max(by_area.items(), key=lambda x: x[1]["critical"] / max(1, x[1]["total"]))
                self._stats["most_critical_area"] = most[0]

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

    def _log_thought(self, thought: SelfTalk):
        try:
            with open(THOUGHT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": thought.timestamp,
                    "type": thought.talk_type,
                    "trigger": thought.trigger,
                    "area": thought.life_area,
                    "intensity": thought.intensity,
                    "would_say_to_friend": thought.would_say_to_friend,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_scc_instance: Optional[SelfCompassionCoach] = None
_scc_lock = threading.Lock()


def get_self_compassion_coach() -> SelfCompassionCoach:
    global _scc_instance
    with _scc_lock:
        if _scc_instance is None:
            _scc_instance = SelfCompassionCoach()
        return _scc_instance
