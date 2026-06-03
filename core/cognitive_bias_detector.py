"""
LOVE Cognitive Bias Detector — Thinking Intelligence (Modern AI Pattern)

Most people think they're rational. They're not. This detector:

1. BIAS TRACKING
   - Record bias encounters and their characteristics
   - Track bias types (confirmation, anchoring, availability, sunk cost, framing, halo, Dunning-Kruger)
   - Log detection, severity, and correction of biases

2. PATTERN ANALYSIS
   - Identify the user's bias profile (aware, occasional, chronic, unaware)
   - Find bias patterns that distort vs clarify thinking
   - Detect chronic bias vulnerability and its costs

3. BIAS DETECTION
   - Suggest practices for recognizing common biases
   - Provide frameworks for debiasing techniques
   - Recommend practices for clearer thinking

4. RATIONALITY CULTIVATION
   - Track the correlation between bias awareness and decision quality
   - Alert when biases are dominating thinking
   - Celebrate moments of genuine clear thinking

Architecture:
- record_bias(situation, type, detection, severity, correction): Log bias
- get_bias_stats(): Get bias pattern analysis
- get_bias_suggestion(capacity, context): Get suggestion
- get_bias_score(): Calculate overall bias health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "cognitive_bias_detector"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BIAS_LOG = DATA_DIR / "biases.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class BiasEntry:
    """A tracked bias encounter."""
    entry_id: str = ""
    situation: str = ""  # what happened
    bias_type: str = ""  # confirmation, anchoring, availability, sunk_cost, framing, halo, dunning_kruger
    detection: float = 0.0  # 0-1 did you notice it?
    severity: float = 0.0  # 0-1
    correction: float = 0.0  # 0-1 did you correct for it?
    emotion_level: float = 0.0  # 0-1
    outcome: float = 0.0  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CognitiveBiasDetector:
    """
    Intelligent cognitive bias detector with awareness detection and rationality cultivation.
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
            "avg_detection": 0.0,
            "avg_correction": 0.0,
            "bias_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_bias(self, situation: str = "", bias_type: str = "", detection: float = 0.0, severity: float = 0.0, correction: float = 0.0, emotion_level: float = 0.0, outcome: float = 0.0, notes: str = "") -> BiasEntry:
        """Record a bias encounter."""
        entry_id = f"bis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = BiasEntry(
            entry_id=entry_id,
            situation=situation or "unspecified",
            bias_type=bias_type or "general",
            detection=detection,
            severity=severity,
            correction=correction,
            emotion_level=emotion_level,
            outcome=outcome,
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

    def get_bias_stats(self) -> Dict[str, Any]:
        """Get bias pattern analysis."""
        if not self._entries:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "detection_sum": 0.0, "severity_sum": 0.0, "correction_sum": 0.0})
        for e in self._entries:
            by_type[e.bias_type]["count"] += 1
            by_type[e.bias_type]["detection_sum"] += e.detection
            by_type[e.bias_type]["severity_sum"] += e.severity
            by_type[e.bias_type]["correction_sum"] += e.correction

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_detection": round(data["detection_sum"] / count, 2),
                "avg_severity": round(data["severity_sum"] / count, 2),
                "avg_correction": round(data["correction_sum"] / count, 2),
            }

        # Detection analysis
        high_det = [e for e in self._entries if e.detection > 0.7]
        low_det = [e for e in self._entries if e.detection < 0.4]
        if high_det and low_det:
            high_det_corr = sum(e.correction for e in high_det) / len(high_det)
            low_det_corr = sum(e.correction for e in low_det) / len(low_det)
            high_det_out = sum(e.outcome for e in high_det) / len(high_det)
            low_det_out = sum(e.outcome for e in low_det) / len(low_det)
        else:
            high_det_corr = 0
            low_det_corr = 0
            high_det_out = 0
            low_det_out = 0

        # Emotion analysis
        high_emo = [e for e in self._entries if e.emotion_level > 0.7]
        low_emo = [e for e in self._entries if e.emotion_level < 0.4]
        if high_emo and low_emo:
            high_emo_det = sum(e.detection for e in high_emo) / len(high_emo)
            low_emo_det = sum(e.detection for e in low_emo) / len(low_emo)
        else:
            high_emo_det = 0
            low_emo_det = 0

        # Bias risk detection
        recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if recent:
            recent_det = sum(e.detection for e in recent) / len(recent)
            recent_corr = sum(e.correction for e in recent) / len(recent)
            bias_risk = recent_det < 0.3 and recent_corr < 0.3
        else:
            bias_risk = False

        return {
            "total_entries": len(self._entries),
            "type_stats": type_stats,
            "detection_impact": {
                "high_detection_correction": round(high_det_corr, 2),
                "low_detection_correction": round(low_det_corr, 2),
                "high_detection_outcome": round(high_det_out, 2),
                "low_detection_outcome": round(low_det_out, 2),
            },
            "emotion_effect": {
                "high_emotion_detection": round(high_emo_det, 2),
                "low_emotion_detection": round(low_emo_det, 2),
            },
            "bias_risk": bias_risk,
            "avg_detection": round(sum(e.detection for e in self._entries) / len(self._entries), 2),
            "avg_correction": round(sum(e.correction for e in self._entries) / len(self._entries), 2),
        }

    def get_bias_suggestion(self, capacity: float = 0.5, context: str = "") -> Dict[str, Any]:
        """Get bias suggestion."""
        suggestions = [
            "You are not rational. Neither am I. The difference between a good thinker and a bad thinker is not rationality. It's awareness. The good thinker knows they're biased. The bad thinker thinks they're objective.",
            "Confirmation bias is the most dangerous bias because it's invisible to the holder. You think you're looking for truth. You're looking for confirmation. Actively seek disconfirmation. Read what you disagree with. Talk to people who think differently.",
            "The sunk cost fallacy keeps people in bad jobs, bad relationships, and bad investments. The money is gone. The time is spent. The only question is: what now? Not: what did I invest?",
            "Anchoring bias means the first number you hear becomes the reference point. If someone says a salary is $100k, $80k seems low. Even if $80k is fair. Be aware of anchors. Create your own reference points.",
            "Availability bias makes you think plane crashes are common because you saw one on the news. And that heart disease is rare because you don't see it. The news is not reality. Statistics are reality.",
            "The Dunning-Kruger effect means the less you know, the more confident you are. And the more you know, the less confident you are. If you're very confident about something complex, be suspicious. Of yourself.",
            "Framing bias means the same information feels different depending on how it's presented. 90% survival sounds better than 10% mortality. Same fact. Different feeling. Notice the frame. Then look past it.",
            "The halo effect makes you think attractive people are smarter. Or that a good speaker is right. Or that a successful person is wise. These things are not correlated. Separate the signal from the packaging.",
            "Groupthink makes smart people agree with stupid conclusions. Because dissent is uncomfortable. Because conformity is rewarded. Be willing to be the person who says: this doesn't make sense.",
            "Your brain is a prediction machine, not a truth machine. It predicts what it wants to be true. Then finds evidence. Don't trust your brain's first take. It was built for survival, not accuracy."
        ]

        if capacity < 0.3:
            capacity_note = "Low capacity. One moment of self-doubt. One question: what if I'm wrong? One search for disconfirming evidence. That's enough."
        elif capacity < 0.6:
            capacity_note = "Moderate capacity. A bias audit for one decision. A perspective from someone who disagrees. A debiasing technique. Medium detection."
        else:
            capacity_note = "Good capacity. Deep cognitive work. A systematic examination of your thinking patterns. You have the strength to think truly clearly."

        return {
            "capacity": capacity,
            "context": context or "general",
            "suggestion": random.choice(suggestions),
            "capacity_note": capacity_note,
            "principle": "Cognitive biases are not bugs in human thinking. They're features. They're shortcuts that evolved because they were useful for survival. But they're terrible for truth. The confirmation bias helped our ancestors stick with their tribe. The availability bias helped them respond to immediate threats. The sunk cost fallacy helped them commit to long-term projects. But in the modern world, these shortcuts distort reality. They make us believe what we want to believe. They make us fear what's rare and ignore what's common. They make us stick with bad choices because we've already invested in them. The work of bias detection is not about eliminating biases. That's impossible. It's about noticing them. About compensating for them. About asking: what would I believe if I didn't want to believe this? That's the work of rationality. And it's the hardest work there is. Because it requires you to doubt your own mind."
        }

    def get_bias_score(self) -> int:
        """Calculate overall bias health (0-100)."""
        if not self._entries:
            return 25

        avg_det = sum(e.detection for e in self._entries) / len(self._entries)
        avg_corr = sum(e.correction for e in self._entries) / len(self._entries)
        avg_sev = sum(e.severity for e in self._entries) / len(self._entries)
        avg_out = sum(e.outcome for e in self._entries) / len(self._entries)
        avg_emo = sum(e.emotion_level for e in self._entries) / len(self._entries)

        # Recent trend
        recent = list(self._entries)[-14:]
        if recent:
            recent_det = sum(e.detection for e in recent) / len(recent)
            recent_corr = sum(e.correction for e in recent) / len(recent)
        else:
            recent_det = 0
            recent_corr = 0

        # Bias penalty
        bias_penalty = 0
        last_30 = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
        if last_30:
            recent_det_30 = sum(e.detection for e in last_30) / len(last_30)
            recent_corr_30 = sum(e.correction for e in last_30) / len(last_30)
            if recent_det_30 < 0.3 and recent_corr_30 < 0.3:
                bias_penalty = 15

        # Type variety
        unique_types = len(set(e.bias_type for e in self._entries))

        score = (avg_det * 25) + (avg_corr * 25) + (avg_out * 15) + (recent_det * 10) + (recent_corr * 10) + (unique_types * 2) - (avg_sev * 10) - (avg_emo * 10) - bias_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._entries:
            self._stats["avg_detection"] = round(sum(e.detection for e in self._entries) / len(self._entries), 2)
            self._stats["avg_correction"] = round(sum(e.correction for e in self._entries) / len(self._entries), 2)

            recent = [e for e in self._entries if e.timestamp > (datetime.now() - timedelta(days=30)).isoformat()]
            if recent:
                recent_det = sum(e.detection for e in recent) / len(recent)
                recent_corr = sum(e.correction for e in recent) / len(recent)
                self._stats["bias_risk"] = recent_det < 0.3 and recent_corr < 0.3
            else:
                self._stats["bias_risk"] = False

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_bias_detector")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_bias_detector")

    def _log_entry(self, entry: BiasEntry):
        try:
            with open(BIAS_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "situation": entry.situation,
                    "bias_type": entry.bias_type,
                    "detection": entry.detection,
                    "correction": entry.correction,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_bias_detector")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cbd_instance: Optional[CognitiveBiasDetector] = None
_cbd_lock = threading.Lock()


def get_cognitive_bias_detector() -> CognitiveBiasDetector:
    global _cbd_instance
    with _cbd_lock:
        if _cbd_instance is None:
            _cbd_instance = CognitiveBiasDetector()
        return _cbd_instance
