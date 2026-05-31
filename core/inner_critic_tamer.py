"""
LOVE Inner Critic Tamer — Self-Judgment Intelligence (Modern AI Pattern)

Most people have a cruel inner voice they never question. This tamer:

1. CRITIC TRACKING
   - Record inner critic encounters and their characteristics
   - Track critic types (perfectionist, comparison, shame, catastrophizing, blame)
   - Log harshness, accuracy, and response to inner criticism

2. PATTERN ANALYSIS
   - Identify the user's critic profile (harsh, moderate, aware, tamed)
   - Find inner critic patterns that motivate vs paralyze
   - Detect chronic self-attack and its consequences

3. CRITIC TAMING
   - Suggest practices for recognizing and softening inner criticism
   - Provide frameworks for turning critic into coach
   - Recommend self-compassion as antidote

4. SELF-KINDNESS CULTIVATION
   - Track the correlation between inner critic tone and wellbeing
   - Alert when self-attack is becoming the default
   - Celebrate moments of genuine self-compassion

Architecture:
- record_critic(critic, type, harshness, accuracy, response): Log critic
- get_critic_stats(): Get critic pattern analysis
- get_critic_suggestion(capacity, context): Get suggestion
- get_critic_score(): Calculate overall critic health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "inner_critic_tamer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CRITIC_LOG = DATA_DIR / "critics.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CriticEntry:
    """A tracked inner critic encounter."""
    entry_id: str = ""
    critic: str = ""  # what the critic said
    critic_type: str = ""  # perfectionist, comparison, shame, catastrophizing, blame
    harshness: float = 0.5  # 0-1
    accuracy: float = 0.0  # 0-1
    response: float = 0.0  # 0-1 how well you responded
    self_compassion: float = 0.0  # 0-1
    challenge: float = 0.0  # 0-1 did you challenge the critic?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class InnerCriticTamer:
    """
    Intelligent inner critic tamer with harshness detection and self-kindness cultivation.
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
            "avg_harshness": 0.0,
            "avg_self_compassion": 0.0,
            "attack_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_critic(self, critic: str = "", critic_type: str = "", harshness: float = 0.5, accuracy: float = 0.0, response: float = 0.0, self_compassion: float = 0.0, challenge: float = 0.0, notes: str = "") -> CriticEntry:
        """Record an inner critic encounter."""
        entry_id = f"cric_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = CriticEntry(
            entry_id=entry_id,
            critic=critic or "unspecified",
            critic_type=critic_type or "general",
            harshness=harshness,
            accuracy=accuracy,
            response=response,
            self_compassion=self_compassion,
            challenge=challenge,
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

    def get_critic_stats(self) -> Dict[str, Any]:
        """Get critic pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "harshness_sum": 0.0, "accuracy_sum": 0.0, "self_compassion_sum": 0.0})
        for e in self._entries:
            by_type[e.critic_type]["count"] += 1
            by_type[e.critic_type]["harshness_sum"] += e.harshness
            by_type[e.critic_type]["accuracy_sum"] += e.accuracy
            by_type[e.critic_type]["self_compassion_sum"] += e.self_compassion

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_harshness": round(data["harshness_sum"] / count, 2),
                "avg_accuracy": round(data["accuracy_sum"] / count, 2),
                "avg_self_compassion": round(data["self_compassion_sum"] / count, 2),
            }

        # Harshness analysis
        high_harsh = [e for e in self._entries if e.harshness > 0.7]
        low_harsh = [e for e in self._entries if e.harshness < 0.4]
        if high_harsh and low_harsh:
            high_harsh_resp = sum(e.response for e in high_harsh) / len(high_harsh)
            low_harsh_resp = sum(e.response for e in low_harsh) / len(low_harsh)
            high_harsh_sc = sum(e.self_compassion for e in high_harsh) / len(high_harsh)
            low_harsh_sc = sum(e.self_compassion for e in low_harsh) / len(low_harsh)
        else:
            high_harsh_resp = 0
            low_harsh_resp = 0
            high_harsh_sc = 0
            low_harsh_sc = 0

        # Challenge analysis
        high_chal = [e for e in self._entries if e.challenge > 0.7]
        low_chal = [e for e in self._entries if e.challenge < 0.4]
        if high_chal and low_chal:
            high_chal_sc = sum(e.self_compassion for e in high_chal) / len(high_chal)
            low_chal_sc = sum(e.self_compassion for e in low_chal) / len(low_chal)
        else:
            high_chal_sc = 0
            low_chal_sc = 0

        # Attack risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_harsh = sum(e.harshness for e in recent) / len(recent)
            recent_sc = sum(e.self_compassion for e in recent) / len(recent)
            attack_risk = recent_harsh > 0.7 and recent_sc < 0.3
        else:
            attack_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "harshness_impact": {
                "high_harshness_response": round(high_harsh_resp, 2),
                "low_harshness_response": round(low_harsh_resp, 2),
                "high_harshness_compassion": round(high_harsh_sc, 2),
                "low_harshness_compassion": round(low_harsh_sc, 2),
            },
            "challenge_effect": {
                "high_challenge_compassion": round(high_chal_sc, 2),
                "low_challenge_compassion": round(low_chal_sc, 2),
            },
            "attack_risk": attack_risk,
            "avg_harshness": round(sum(e.harshness for e in self._entries) / len(self._entries), 2),
            "avg_self_compassion": round(sum(e.self_compassion for e in self._entries) / len(self._entries), 2),
        }

    def get_critic_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get critic suggestion."""
        suggestions = [
            "Notice the critic's voice. It's not you. It's a pattern. A habit. A recording from childhood. Name it. 'Oh, there's the perfectionist critic.' Distance creates choice.",
            "Ask: would I say this to a friend? If not, why am I saying it to myself? The standard you apply to yourself should be at least as kind as the standard you apply to others.",
            "Your inner critic is trying to protect you. From failure. From shame. From rejection. It's just doing it badly. Thank it for the intention. Then tell it: I've got this.",
            "Turn the critic into a coach. Same observations. Different tone. 'You made a mistake' becomes 'How can we do better next time?' The message stays. The cruelty goes.",
            "Compassion is not indulgence. It's not letting yourself off the hook. It's acknowledging that you're human. That humans make mistakes. And that you deserve kindness.",
            "Challenge the critic's evidence. 'I'm terrible at this.' Really? Always? In every context? The critic speaks in absolutes. Reality is more nuanced.",
            "When the critic attacks, place your hand on your heart. Physically. It's a somatic anchor for self-compassion. The body needs the signal too.",
            "The critic thrives in isolation. Share your struggle. The thing you're most ashamed of is the thing that connects you most deeply when you share it.",
            "Your worth is not conditional. Not on performance. Not on approval. Not on perfection. You are worthy because you exist. The critic doesn't get to vote on that.",
            "The inner critic is the voice of your harshest teacher, your most insecure parent, your cruelest bully. Combined. And amplified. But it's not the truth. It's a fear. And fears can be faced."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One gentle word to yourself. One challenge to the critic. One moment of self-kindness. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A self-compassion practice. A critic challenge. A kind inner dialogue. Medium taming."
        else:
            capacity_note = "Good capacity. Deep inner work. A systematic transformation of the critic into a coach. You have the strength to be truly kind to yourself."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "The inner critic is the most abusive relationship most people have. And they can't escape it. Because it lives in their head. It's there when they wake up. When they make a mistake. When they try to rest. When they succeed and immediately think about what could have been better. The critic is relentless. And it's a liar. It doesn't tell you the truth. It tells you what you're afraid of. What you fear others think. What you internalized from people who didn't know how to love you properly. And the only way to tame it is to become aware of it. To name it. To challenge it. And ultimately, to replace it with a voice that has the same observations but speaks with compassion instead of cruelty. The inner coach. The voice that says: I see the problem. And I believe in your ability to fix it. That voice changes everything."
        }

    def get_critic_score(self) -> int:
        """Calculate overall critic health (0-100)."""
        if not self._entries:
            return 25

        avg_harsh = sum(e.harshness for e in self._entries) / len(self._entries)
        avg_sc = sum(e.self_compassion for e in self._entries) / len(self._entries)
        avg_resp = sum(e.response for e in self._entries) / len(self._entries)
        avg_chal = sum(e.challenge for e in self._entries) / len(self._entries)
        avg_acc = sum(e.accuracy for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_harsh = sum(e.harshness for e in recent) / len(recent)
            recent_sc = sum(e.self_compassion for e in recent) / len(recent)
        else:
            recent_harsh = 0
            recent_sc = 0

        # Attack penalty
        attack_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_harsh_30 = sum(e.harshness for e in last_30) / len(last_30)
            recent_sc_30 = sum(e.self_compassion for e in last_30) / len(last_30)
            if recent_harsh_30 > 0.7 and recent_sc_30 < 0.3:
                attack_penalty = 15

        # Type variety
        unique_types = len(set(e.critic_type for e in self._entries))

        score = (avg_sc * 30) + (avg_resp * 20) + (avg_chal * 15) + (avg_acc * 10) + (recent_sc * 15) + (recent_sc * 5) + (unique_types * 2) - (avg_harsh * 15) - attack_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_harshness"] = round(sum(e.harshness for e in self._entries) / len(self._entries), 2)
            self._stats["avg_self_compassion"] = round(sum(e.self_compassion for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_harsh = sum(e.harshness for e in recent) / len(recent)
                recent_sc = sum(e.self_compassion for e in recent) / len(recent)
                self._stats["attack_risk"] = recent_harsh > 0.7 and recent_sc < 0.3
            else:
                self._stats["attack_risk"] = False

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

    def _log_entry(self, entry: CriticEntry):
        try:
            with open(CRITIC_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "critic": entry.critic,
                    "critic_type": entry.critic_type,
                    "harshness": entry.harshness,
                    "self_compassion": entry.self_compassion,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ict_instance: Optional[InnerCriticTamer] = None
_ict_lock = threading.Lock()


def get_inner_critic_tamer() -> InnerCriticTamer:
    global _ict_instance
    with _ict_lock:
        if _ict_instance is None:
            _ict_instance = InnerCriticTamer()
        return _ict_instance
