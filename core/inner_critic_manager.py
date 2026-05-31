"""
LOVE Inner Critic Manager — Self-Talk Intelligence (Modern AI Pattern)

Most inner critics are unexamined internalized voices. This manager:

1. CRITIC TRACKING
   - Record inner critic attacks and their triggers
   - Track the critic's tone, frequency, and target areas
   - Log responses to the critic and their effectiveness

2. PATTERN ANALYSIS
   - Identify the critic's voice (perfectionist, comparator, catastrophizer, etc.)
   - Find the critic's favorite targets and timing
   - Detect when the critic is actually protecting something

3. CRITIC MANAGEMENT
   - Suggest counter-voices and compassionate responses
   - Provide reframe techniques for common attacks
   - Recommend boundary-setting with the inner critic

4. TRANSFORMATION
   - Track the correlation between critic management and self-esteem
   - Alert when the critic is dominating without being challenged
   - Celebrate moments of self-compassion triumph

Architecture:
- record_critic_attack(attack, trigger, tone, target): Log attack
- get_critic_stats(): Get inner critic pattern analysis
- get_response_strategy(attack_type, intensity): Get response plan
- get_critic_score(): Calculate overall inner critic management health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "inner_critic_manager"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CRITIC_LOG = DATA_DIR / "critic.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class CriticAttack:
    """A tracked inner critic attack."""
    attack_id: str = ""
    attack: str = ""  # what the critic said
    trigger: str = ""  # what triggered it
    tone: str = ""  # perfectionist, comparator, catastrophizer, shamer, doubter
    target_area: str = ""  # work, appearance, intelligence, social, creativity, worth
    intensity: float = 0.5  # 0-1
    response: str = ""  # how they responded
    response_effectiveness: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class InnerCriticManager:
    """
    Intelligent inner critic manager with voice identification and compassionate response generation.
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
        self._attacks: deque = deque(maxlen=200)
        self._stats = {
            "total_attacks": 0,
            "avg_intensity": 0.0,
            "avg_response_effectiveness": 0.0,
            "dominant_tone": "",
            "favorite_target": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_critic_attack(self, attack: str = "", trigger: str = "", tone: str = "", target_area: str = "", intensity: float = 0.5, response: str = "", response_effectiveness: float = 0.0, notes: str = "") -> CriticAttack:
        """Record a critic attack."""
        attack_id = f"critic_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._attacks)}"
        ca = CriticAttack(
            attack_id=attack_id,
            attack=attack or "unspecified",
            trigger=trigger,
            tone=tone or "shamer",
            target_area=target_area or "general",
            intensity=intensity,
            response=response,
            response_effectiveness=response_effectiveness,
            notes=notes,
        )

        with self._lock:
            self._attacks.append(ca)
            self._stats["total_attacks"] += 1
            self._update_stats()

        self._save_stats()
        self._log_attack(ca)

        return ca

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_critic_stats(self) -> Dict[str, Any]:
        """Get inner critic pattern analysis."""
        if not self._attacks:
            return {"status": "insufficient_data"}

        # Tone analysis
        by_tone = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "response_sum": 0.0})
        for a in self._attacks:
            by_tone[a.tone]["count"] += 1
            by_tone[a.tone]["intensity_sum"] += a.intensity
            by_tone[a.tone]["response_sum"] += a.response_effectiveness

        tone_stats = {}
        for t, data in by_tone.items():
            count = data["count"]
            tone_stats[t] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_response_effectiveness": round(data["response_sum"] / count, 2),
            }

        dominant_tone = max(tone_stats.items(), key=lambda x: x[1]["count"]) if tone_stats else ("", {})

        # Target analysis
        by_target = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0, "response_sum": 0.0})
        for a in self._attacks:
            by_target[a.target_area]["count"] += 1
            by_target[a.target_area]["intensity_sum"] += a.intensity
            by_target[a.target_area]["response_sum"] += a.response_effectiveness

        target_stats = {}
        for target, data in by_target.items():
            count = data["count"]
            target_stats[target] = {
                "count": count,
                "avg_intensity": round(data["intensity_sum"] / count, 2),
                "avg_response_effectiveness": round(data["response_sum"] / count, 2),
            }

        favorite_target = max(target_stats.items(), key=lambda x: x[1]["count"]) if target_stats else ("", {})

        # Trigger analysis
        by_trigger = defaultdict(lambda: {"count": 0, "intensity_sum": 0.0})
        for a in self._attacks:
            if a.trigger:
                by_trigger[a.trigger]["count"] += 1
                by_trigger[a.trigger]["intensity_sum"] += a.intensity

        trigger_stats = {}
        for tr, data in by_trigger.items():
            count = data["count"]
            if count >= 2:
                trigger_stats[tr] = {
                    "count": count,
                    "avg_intensity": round(data["intensity_sum"] / count, 2),
                }

        # Response effectiveness
        responded = [a for a in self._attacks if a.response]
        if responded:
            avg_response = sum(a.response_effectiveness for a in responded) / len(responded)
        else:
            avg_response = 0

        # High-intensity unchallenged attacks
        dangerous = [a for a in self._attacks if a.intensity > 0.7 and a.response_effectiveness < 0.3]

        return {
            "total_attacks": len(self._attacks),
            "tone_stats": tone_stats,
            "dominant_tone": dominant_tone[0],
            "target_stats": target_stats,
            "favorite_target": favorite_target[0],
            "trigger_stats": trigger_stats,
            "avg_intensity": round(sum(a.intensity for a in self._attacks) / len(self._attacks), 2),
            "avg_response_effectiveness": round(avg_response, 2),
            "dangerous_attacks": len(dangerous),
            "response_rate": round(len(responded) / len(self._attacks), 2),
        }

    def get_response_strategy(self, attack_type: str = "", intensity: float = 0.5, target: str = "") -> Dict[str, Any]:
        """Get response plan."""
        counter_voices = {
            "perfectionist": [
                "Done is better than perfect. Perfection is the enemy of progress.",
                "Mistakes are data, not character flaws. I'm learning.",
                "80% is often enough. The last 20% costs 80% of the energy.",
            ],
            "comparator": [
                "Comparison is the thief of joy. My path is mine alone.",
                "They have their struggles too. I just can't see them.",
                "I'm comparing my behind-the-scenes to their highlight reel.",
            ],
            "catastrophizer": [
                "This feels terrible, and it's probably not as bad as it feels.",
                "What's the most likely outcome? Not the worst. The most likely.",
                "I've survived 100% of my bad days so far. This is survivable too.",
            ],
            "shamer": [
                "Shame says I am bad. Guilt says I did bad. I can fix behavior.",
                "This feeling will pass. I don't have to believe everything I feel.",
                "I'm worthy of love and belonging, even when I mess up.",
            ],
            "doubter": [
                "Doubt is part of the process. It doesn't mean stop. It means check.",
                "I've done hard things before. I can do this too.",
                "What would I tell a friend who felt this way? Say that to myself.",
            ],
        }

        base_responses = counter_voices.get(attack_type, counter_voices["shamer"])

        if intensity > 0.7:
            strategy = "Don't argue with the critic right now. Ground yourself first. Breathe. Touch something physical. Then use the counter-voice."
        elif intensity > 0.4:
            strategy = "Use the counter-voice immediately. Say it aloud if possible. The critic loses power when challenged."
        else:
            strategy = "Low-intensity attack. This is practice time. Use a new counter-voice. Build your repertoire."

        compassionate_actions = [
            "Put your hand on your heart. Breathe. Say: 'This is hard, and I'm doing my best.'",
            "Text a friend: 'My inner critic is loud today.' Vulnerability disarms shame.",
            "Do one small act of self-care. Tea. Walk. Music. Show yourself kindness.",
            "Write the critic's words down. Then write a compassionate response. Read it aloud.",
        ]

        return {
            "attack_type": attack_type or "general",
            "intensity": intensity,
            "target": target or "general",
            "counter_voice": random.choice(base_responses),
            "strategy": strategy,
            "compassionate_action": random.choice(compassionate_actions),
            "reminder": "The inner critic thinks it's protecting you. Thank it for trying. Then do what you know is right anyway.",
        }

    def get_critic_score(self) -> int:
        """Calculate overall inner critic management health (0-100)."""
        if not self._attacks:
            return 35

        # Response effectiveness
        responded = [a for a in self._attacks if a.response]
        if responded:
            avg_response = sum(a.response_effectiveness for a in responded) / len(responded)
        else:
            avg_response = 0

        # Low intensity
        avg_intensity = sum(a.intensity for a in self._attacks) / len(self._attacks)

        # Response rate
        response_rate = len(responded) / len(self._attacks)

        # Dangerous attacks (high intensity, low response)
        dangerous = [a for a in self._attacks if a.intensity > 0.7 and a.response_effectiveness < 0.3]
        danger_penalty = min(20, len(dangerous) * 5)

        # Recent trend
        recent = [a for a in self._attacks if a.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_intensity = sum(a.intensity for a in recent) / len(recent)
            recent_response = sum(a.response_effectiveness for a in recent) / len(recent)
        else:
            recent_intensity = 0
            recent_response = 0

        # Target variety (critic focusing on one area is worse)
        unique_targets = len(set(a.target_area for a in self._attacks))

        score = (avg_response * 25) + ((1 - avg_intensity) * 15) + (response_rate * 15) + (recent_response * 15) + (unique_targets * 2) - danger_penalty + 15
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._attacks:
            self._stats["avg_intensity"] = round(sum(a.intensity for a in self._attacks) / len(self._attacks), 2)
            
            responded = [a for a in self._attacks if a.response]
            if responded:
                self._stats["avg_response_effectiveness"] = round(sum(a.response_effectiveness for a in responded) / len(responded), 2)

            by_tone = defaultdict(lambda: {"count": 0, "intensity": 0.0})
            for a in self._attacks:
                by_tone[a.tone]["count"] += 1
                by_tone[a.tone]["intensity"] += a.intensity
            if by_tone:
                dominant = max(by_tone.items(), key=lambda x: x[1]["count"])
                self._stats["dominant_tone"] = dominant[0]

            by_target = defaultdict(lambda: {"count": 0, "intensity": 0.0})
            for a in self._attacks:
                by_target[a.target_area]["count"] += 1
                by_target[a.target_area]["intensity"] += a.intensity
            if by_target:
                favorite = max(by_target.items(), key=lambda x: x[1]["count"])
                self._stats["favorite_target"] = favorite[0]

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

    def _log_attack(self, attack: CriticAttack):
        try:
            with open(CRITIC_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": attack.timestamp,
                    "attack": attack.attack,
                    "tone": attack.tone,
                    "target": attack.target_area,
                    "intensity": attack.intensity,
                    "response_effectiveness": attack.response_effectiveness,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_icm_instance: Optional[InnerCriticManager] = None
_icm_lock = threading.Lock()


def get_inner_critic_manager() -> InnerCriticManager:
    global _icm_instance
    with _icm_lock:
        if _icm_instance is None:
            _icm_instance = InnerCriticManager()
        return _icm_instance
