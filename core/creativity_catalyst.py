"""
LOVE Creativity Catalyst — Creative Intelligence (Modern AI Pattern)

Most creativity is blocked by expectation, not lack of talent. This catalyst:

1. CREATIVE TRACKING
   - Record creative sessions and their characteristics
   - Track creative outputs (ideas, prototypes, drafts, experiments)
   - Log creative blocks and their sources

2. PATTERN ANALYSIS
   - Identify the user's creative profile (divergent, convergent, iterative, spontaneous)
   - Find creative triggers (environments, states, prompts)
   - Detect creative ruts and their causes

3. CATALYSIS
   - Suggest creative prompts matched to current block
   - Provide constraint-based creativity exercises
   - Recommend cross-pollination practices (borrow from other domains)

4. CREATIVE HABITS
   - Track daily creative practice adherence
   - Alert when creative muscles are atrophying
   - Celebrate creative breakthroughs

Architecture:
- record_session(activity, output, block, trigger): Log session
- get_creative_stats(): Get creative pattern analysis
- get_creative_prompt(block_type, domain): Get prompt
- get_creative_score(): Calculate overall creative health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "creativity_catalyst"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CREATIVE_LOG = DATA_DIR / "sessions.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CreativeSession:
    """A tracked creative session."""
    session_id: str = ""
    activity: str = ""  # what they did
    domain: str = ""  # writing, visual, music, design, problem_solving, code, culinary
    output_count: int = 0
    output_quality: float = 0.5  # 0-1
    block_type: str = ""  # fear, perfectionism, boredom, burnout, distraction, lack_of_inspiration
    trigger: str = ""  # what sparked the session
    energy_before: float = 0.5
    energy_after: float = 0.5
    flow_score: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CreativityCatalyst:
    """
    Intelligent creativity catalyst with block analysis and cross-domain stimulation.
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
        self._sessions: deque = deque(maxlen=300)
        self._stats = {
            "total_sessions": 0,
            "avg_output": 0.0,
            "avg_flow": 0.0,
            "best_domain": "",
            "common_block": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_session(self, activity: str = "", domain: str = "", output_count: int = 0, output_quality: float = 0.5, block_type: str = "", trigger: str = "", energy_before: float = 0.5, energy_after: float = 0.5, flow_score: float = 0.0, notes: str = "") -> CreativeSession:
        """Record a creative session."""
        session_id = f"creat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._sessions)}"
        session = CreativeSession(
            session_id=session_id,
            activity=activity or "unspecified",
            domain=domain or "general",
            output_count=output_count,
            output_quality=output_quality,
            block_type=block_type or "none",
            trigger=trigger,
            energy_before=energy_before,
            energy_after=energy_after,
            flow_score=flow_score,
            notes=notes,
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._update_stats()

        self._save_stats()
        self._log_session(session)

        return session

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_creative_stats(self) -> Dict[str, Any]:
        """Get creative pattern analysis."""
        if not self._sessions:
            return {"status": "insufficient_data"}

        # Domain analysis
        by_domain = defaultdict(lambda: {"count": 0, "output_sum": 0.0, "flow_sum": 0.0, "quality_sum": 0.0})
        for s in self._sessions:
            by_domain[s.domain]["count"] += 1
            by_domain[s.domain]["output_sum"] += s.output_count
            by_domain[s.domain]["flow_sum"] += s.flow_score
            by_domain[s.domain]["quality_sum"] += s.output_quality

        domain_stats = {}
        for d, data in by_domain.items():
            count = data["count"]
            domain_stats[d] = {
                "count": count,
                "avg_output": round(data["output_sum"] / count, 1),
                "avg_flow": round(data["flow_sum"] / count, 2),
                "avg_quality": round(data["quality_sum"] / count, 2),
            }

        best_domain = max(domain_stats.items(), key=lambda x: x[1]["avg_flow"] + x[1]["avg_quality"]) if domain_stats else ("", {})

        # Block analysis
        by_block = defaultdict(lambda: {"count": 0, "output_sum": 0.0, "flow_sum": 0.0})
        for s in self._sessions:
            if s.block_type:
                by_block[s.block_type]["count"] += 1
                by_block[s.block_type]["output_sum"] += s.output_count
                by_block[s.block_type]["flow_sum"] += s.flow_score

        block_stats = {}
        for b, data in by_block.items():
            count = data["count"]
            block_stats[b] = {
                "count": count,
                "avg_output": round(data["output_sum"] / count, 1),
                "avg_flow": round(data["flow_sum"] / count, 2),
            }

        common_block = max(block_stats.items(), key=lambda x: x[1]["count"]) if block_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "flow_sum": 0.0, "quality_sum": 0.0})
        for s in self._sessions:
            if s.trigger:
                by_trigger[s.trigger]["count"] += 1
                by_trigger[s.trigger]["flow_sum"] += s.flow_score
                by_trigger[s.trigger]["quality_sum"] += s.output_quality

        trigger_stats = {}
        for t, data in by_trigger.items():
            count = data["count"]
            if count >= 2:
                trigger_stats[t] = {
                    "count": count,
                    "avg_flow": round(data["flow_sum"] / count, 2),
                    "avg_quality": round(data["quality_sum"] / count, 2),
                }

        best_trigger = max(trigger_stats.items(), key=lambda x: x[1]["avg_flow"] + x[1]["avg_quality"]) if trigger_stats else ("", {})

        # Energy analysis
        avg_energy_change = sum(s.energy_after - s.energy_before for s in self._sessions) / len(self._sessions)

        # Recent trend
        recent = list(self._sessions)[-10:]
        if recent:
            recent_flow = sum(s.flow_score for s in recent) / len(recent)
            recent_quality = sum(s.output_quality for s in recent) / len(recent)
        else:
            recent_flow = 0
            recent_quality = 0

        older = list(self._sessions)[:-10] if len(self._sessions) > 10 else []
        if older:
            older_flow = sum(s.flow_score for s in older) / len(older)
            older_quality = sum(s.output_quality for s in older) / len(older)
            flow_trend = recent_flow - older_flow
            quality_trend = recent_quality - older_quality
        else:
            flow_trend = 0
            quality_trend = 0

        # Rut detection
        if len(self._sessions) >= 20:
            first_half = list(self._sessions)[:len(self._sessions)//2]
            second_half = list(self._sessions)[len(self._sessions)//2:]
            first_flow = sum(s.flow_score for s in first_half) / len(first_half)
            second_flow = sum(s.flow_score for s in second_half) / len(second_half)
            in_a_rut = second_flow < first_flow * 0.7
        else:
            in_a_rut = False

        return {
            "total_sessions": len(self._sessions),
            "domain_stats": domain_stats,
            "best_domain": best_domain[0],
            "block_stats": block_stats,
            "common_block": common_block[0],
            "trigger_stats": trigger_stats,
            "best_trigger": best_trigger[0],
            "avg_output": round(sum(s.output_count for s in self._sessions) / len(self._sessions), 1),
            "avg_quality": round(sum(s.output_quality for s in self._sessions) / len(self._sessions), 2),
            "avg_flow": round(sum(s.flow_score for s in self._sessions) / len(self._sessions), 2),
            "avg_energy_change": round(avg_energy_change, 2),
            "flow_trend": round(flow_trend, 2),
            "quality_trend": round(quality_trend, 2),
            "in_a_rut": in_a_rut,
        }

    def get_creative_prompt(self, block_type: str = "", domain: str = "") -> Dict[str, Any]:
        """Get prompt."""
        prompts = {
            "fear": [
                "Create the worst version intentionally. Make it terrible. Liberate yourself from perfection.",
                "Use a pseudonym. Create as someone else. The fear belongs to them, not you.",
                "Set a timer for 5 minutes. You only have to create for 5 minutes. Then you can stop.",
            ],
            "perfectionism": [
                "Add one deliberate flaw. Imperfection is human. Perfection is sterile.",
                "Use 'good enough' as your standard. What would you accept from a friend?",
                "Create two versions: one polished, one raw. Which has more life?",
            ],
            "boredom": [
                "Combine two unrelated things. A toaster + a galaxy. A spreadsheet + a symphony.",
                "Change one variable. Different color, different tool, different time of day.",
                "Imitate someone you admire. Then twist it. Imitation is the start of innovation.",
            ],
            "burnout": [
                "Create something tiny. A haiku. A doodle. One line of code. Small wins rebuild momentum.",
                "Switch domains. If you write, draw. If you code, cook. Cross-training for creativity.",
                "Copy something you love. Not to publish. To remember why you love creating.",
            ],
            "distraction": [
                "Create in a different environment. Cafe, park, library. New context, new focus.",
                "Use the pomodoro technique. 25 minutes of creation. 5 minutes of break. Repeat.",
                "Remove one distraction. Phone in another room. One browser tab. Start there.",
            ],
            "lack_of_inspiration": [
                "Take a walk. Movement generates ideas. Always.",
                "Consume something in a different domain. Architecture, biology, poetry. Cross-pollinate.",
                "Set an absurd constraint. Create using only circles. Write without the letter 'e'. Constraints breed creativity.",
            ],
            "none": [
                "Create something that doesn't exist yet. That's the job.",
                "Start with the question, not the answer. What's the most interesting question in your domain right now?",
                "Make something that delights you. If it delights you, it will delight someone else.",
            ],
        }

        selected = prompts.get(block_type, prompts["none"])

        if block_type:
            block_note = f"You're blocked by {block_type}. This is normal. Every creator faces this. The block is not the enemy. It's a signal."
        else:
            block_note = "No block detected. This is your time to push boundaries. Create something that scares you a little."

        return {
            "block_type": block_type or "none",
            "domain": domain or "general",
            "prompt": random.choice(selected),
            "block_note": block_note,
            "principle": "Creativity is not a talent. It's a practice. Show up, make things, learn, repeat. The muse visits those who are working.",
        }

    def get_creative_score(self) -> int:
        """Calculate overall creative health (0-100)."""
        if not self._sessions:
            return 30

        # Output quality and flow
        avg_quality = sum(s.output_quality for s in self._sessions) / len(self._sessions)
        avg_flow = sum(s.flow_score for s in self._sessions) / len(self._sessions)

        # Output volume
        avg_output = sum(s.output_count for s in self._sessions) / len(self._sessions)

        # Low block rate
        blocked = sum(1 for s in self._sessions if s.block_type and s.block_type != "none")
        block_rate = blocked / len(self._sessions)

        # Energy sustainability
        avg_energy_change = sum(s.energy_after - s.energy_before for s in self._sessions) / len(self._sessions)

        # Domain variety
        unique_domains = len(set(s.domain for s in self._sessions))

        # Recent trend
        recent = list(self._sessions)[-10:]
        if recent:
            recent_flow = sum(s.flow_score for s in recent) / len(recent)
            recent_quality = sum(s.output_quality for s in recent) / len(recent)
        else:
            recent_flow = 0
            recent_quality = 0

        # Rut penalty
        if len(self._sessions) >= 20:
            first_half = list(self._sessions)[:len(self._sessions)//2]
            second_half = list(self._sessions)[len(self._sessions)//2:]
            first_flow = sum(s.flow_score for s in first_half) / len(first_half)
            second_flow = sum(s.flow_score for s in second_half) / len(second_half)
            rut_penalty = 10 if second_flow < first_flow * 0.7 else 0
        else:
            rut_penalty = 0

        score = (avg_quality * 20) + (avg_flow * 20) + (avg_output * 10) + ((1 - block_rate) * 15) + (avg_energy_change * 10) + (unique_domains * 2) + (recent_flow * 10) + (recent_quality * 10) - rut_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._sessions:
            self._stats["avg_output"] = round(sum(s.output_count for s in self._sessions) / len(self._sessions), 1)
            self._stats["avg_flow"] = round(sum(s.flow_score for s in self._sessions) / len(self._sessions), 2)

            by_domain = defaultdict(lambda: {"flow": 0.0, "quality": 0.0, "count": 0})
            for s in self._sessions:
                by_domain[s.domain]["flow"] += s.flow_score
                by_domain[s.domain]["quality"] += s.output_quality
                by_domain[s.domain]["count"] += 1
            if by_domain:
                best = max(by_domain.items(), key=lambda x: (x[1]["flow"] + x[1]["quality"]) / max(1, x[1]["count"]))
                self._stats["best_domain"] = best[0]

            by_block = defaultdict(int)
            for s in self._sessions:
                if s.block_type and s.block_type != "none":
                    by_block[s.block_type] += 1
            if by_block:
                common = max(by_block.items(), key=lambda x: x[1])
                self._stats["common_block"] = common[0]

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

    def _log_session(self, session: CreativeSession):
        try:
            with open(CREATIVE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "activity": session.activity,
                    "domain": session.domain,
                    "output_count": session.output_count,
                    "output_quality": session.output_quality,
                    "block": session.block_type,
                    "flow": session.flow_score,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cc_instance: Optional[CreativityCatalyst] = None
_cc_lock = threading.Lock()


def get_creativity_catalyst() -> CreativityCatalyst:
    global _cc_instance
    with _cc_lock:
        if _cc_instance is None:
            _cc_instance = CreativityCatalyst()
        return _cc_instance
