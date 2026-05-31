"""
LOVE Communication Analyzer — Communication Intelligence (Modern AI Pattern)

Most communication tools are spell checkers. This analyzer:

1. COMMUNICATION TRACKING
   - Record communication sessions (emails, calls, meetings, messages)
   - Track clarity, tone, and effectiveness
   - Identify communication load and response time patterns

2. PATTERN DETECTION
   - Find your most/least effective communication channels
   - Detect communication overload (too many threads, too little depth)
   - Identify people you communicate with most and their patterns

3. TONE & CLARITY INSIGHTS
   - Track how often your messages are misunderstood
   - Identify when you're too terse or too verbose
   - Suggest communication style adjustments

4. PROACTIVE IMPROVEMENT
   - Suggest async vs sync communication for different contexts
   - Recommend response time windows to protect focus
   - Alert when communication load exceeds capacity

Architecture:
- record_communication(channel, recipient, purpose, effectiveness): Log interaction
- get_communication_stats(): Get communication pattern analysis
- get_channel_recommendation(): Suggest optimal channel for context
- get_communication_load_score(): Calculate current communication burden
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "communication_analyzer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMM_LOG = DATA_DIR / "communications.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Communication:
    """A communication interaction."""
    channel: str = ""  # email, call, meeting, chat, video, in_person
    recipient: str = ""
    purpose: str = ""  # request, update, discussion, decision, social
    duration_minutes: float = 0.0
    effectiveness: float = 0.5  # 0-1
    clarity: float = 0.5
    tone: str = ""  # formal, casual, assertive, deferential, neutral
    response_time_minutes: float = 0.0  # how long to respond
    misunderstanding: bool = False
    follow_up_required: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class CommunicationAnalyzer:
    """
    Analyze communication patterns and optimize communication strategy.
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
        self._communications: deque = deque(maxlen=500)
        self._stats = {
            "total_communications": 0,
            "avg_effectiveness": 0.5,
            "avg_clarity": 0.5,
            "misunderstanding_rate": 0.0,
            "avg_response_time": 0.0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_communication(self, channel: str = "", recipient: str = "", purpose: str = "", duration: float = 0, effectiveness: float = 0.5, clarity: float = 0.5, tone: str = "", response_time: float = 0, misunderstanding: bool = False, follow_up: bool = False, notes: str = "") -> Communication:
        """Record a communication interaction."""
        comm = Communication(
            channel=channel or "chat",
            recipient=recipient or "unspecified",
            purpose=purpose or "general",
            duration_minutes=duration,
            effectiveness=effectiveness,
            clarity=clarity,
            tone=tone or "neutral",
            response_time_minutes=response_time,
            misunderstanding=misunderstanding,
            follow_up_required=follow_up,
            notes=notes,
        )

        with self._lock:
            self._communications.append(comm)
            self._stats["total_communications"] += 1
            self._update_stats(comm)

        self._save_stats()
        self._log_communication(comm)

        return comm

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_communication_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get communication pattern analysis."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [c for c in self._communications if c.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Channel effectiveness
        by_channel = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0, "clarity_sum": 0.0, "misunderstandings": 0})
        for c in recent:
            ch = c.channel
            by_channel[ch]["count"] += 1
            by_channel[ch]["effectiveness_sum"] += c.effectiveness
            by_channel[ch]["clarity_sum"] += c.clarity
            if c.misunderstanding:
                by_channel[ch]["misunderstandings"] += 1

        channel_stats = {}
        for ch, stats in by_channel.items():
            channel_stats[ch] = {
                "count": stats["count"],
                "avg_effectiveness": round(stats["effectiveness_sum"] / stats["count"], 2),
                "avg_clarity": round(stats["clarity_sum"] / stats["count"], 2),
                "misunderstanding_rate": round(stats["misunderstandings"] / stats["count"] * 100, 1),
            }

        # Recipient patterns
        by_recipient = defaultdict(lambda: {"count": 0, "effectiveness_sum": 0.0})
        for c in recent:
            by_recipient[c.recipient]["count"] += 1
            by_recipient[c.recipient]["effectiveness_sum"] += c.effectiveness

        top_recipients = sorted(
            [(r, s["count"], round(s["effectiveness_sum"]/s["count"], 2)) for r, s in by_recipient.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Purpose breakdown
        by_purpose = defaultdict(int)
        for c in recent:
            by_purpose[c.purpose] += 1

        # Response time analysis
        response_times = [c.response_time_minutes for c in recent if c.response_time_minutes > 0]
        avg_response = sum(response_times) / len(response_times) if response_times else 0

        # Load analysis
        daily_comm = defaultdict(int)
        for c in recent:
            day = c.timestamp[:10]
            daily_comm[day] += 1

        avg_daily = sum(daily_comm.values()) / max(1, len(daily_comm))

        return {
            "days_analyzed": len(set(c.timestamp[:10] for c in recent)),
            "total_communications": len(recent),
            "avg_effectiveness": round(sum(c.effectiveness for c in recent) / len(recent), 2),
            "avg_clarity": round(sum(c.clarity for c in recent) / len(recent), 2),
            "misunderstanding_rate": round(sum(1 for c in recent if c.misunderstanding) / len(recent) * 100, 1),
            "avg_response_time_minutes": round(avg_response, 1),
            "channel_stats": channel_stats,
            "top_recipients": top_recipients,
            "purpose_breakdown": dict(by_purpose),
            "avg_daily_communications": round(avg_daily, 1),
            "communication_load": "high" if avg_daily > 20 else "medium" if avg_daily > 10 else "low",
        }

    def get_channel_recommendation(self, purpose: str = "", urgency: str = "normal", recipient: str = "") -> Dict[str, Any]:
        """Suggest optimal communication channel for context."""
        # Analyze past effectiveness by channel for similar contexts
        recent = list(self._communications)[-50:]
        purpose_matches = [c for c in recent if c.purpose == purpose] if purpose else recent

        if purpose_matches:
            by_channel = defaultdict(lambda: {"count": 0, "effectiveness": 0.0})
            for c in purpose_matches:
                by_channel[c.channel]["count"] += 1
                by_channel[c.channel]["effectiveness"] += c.effectiveness

            best_channel = max(by_channel.items(), key=lambda x: x[1]["effectiveness"]/x[1]["count"])[0]
            best_effectiveness = by_channel[best_channel]["effectiveness"] / by_channel[best_channel]["count"]
        else:
            # Default recommendations
            channel_map = {
                "request": "email",
                "update": "chat",
                "discussion": "call",
                "decision": "meeting",
                "social": "chat",
            }
            best_channel = channel_map.get(purpose, "email")
            best_effectiveness = 0.7

        # Override for urgency
        if urgency == "urgent" and best_channel not in ["call", "video", "in_person"]:
            best_channel = "call"

        channel_reasons = {
            "email": "Best for async, documented communication. Gives recipient time to respond thoughtfully.",
            "chat": "Good for quick questions and informal updates. Keep it brief.",
            "call": "Best for complex discussions or urgent matters. Allows real-time clarification.",
            "meeting": "Best for decisions requiring multiple stakeholders. Have an agenda.",
            "video": "Good for building rapport or showing complex visuals. More engaging than audio.",
            "in_person": "Best for sensitive topics or relationship building. Highest bandwidth.",
        }

        return {
            "recommended_channel": best_channel,
            "reason": channel_reasons.get(best_channel, "Default channel for this context."),
            "expected_effectiveness": round(best_effectiveness, 2),
            "alternative": "call" if best_channel == "email" else "email",
        }

    def get_communication_load_score(self) -> int:
        """Calculate current communication burden score (0-100)."""
        recent = [c for c in self._communications if c.timestamp > (datetime.now() - timedelta(hours=24)).isoformat()]
        
        if not recent:
            return 0

        # Volume load
        daily_count = len(recent)
        volume_score = min(100, daily_count * 5)  # 20+ communications = 100

        # Response pressure
        pending_responses = sum(1 for c in recent if c.follow_up_required)
        response_score = min(100, pending_responses * 20)

        # Time burden
        total_time = sum(c.duration_minutes for c in recent)
        time_score = min(100, total_time / 60 * 10)  # 10 hours = 100

        overall = round(volume_score * 0.4 + response_score * 0.3 + time_score * 0.3)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, comm: Communication):
        """Update running statistics."""
        n = self._stats["total_communications"]
        self._stats["avg_effectiveness"] = round((self._stats["avg_effectiveness"] * (n - 1) + comm.effectiveness) / n, 2)
        self._stats["avg_clarity"] = round((self._stats["avg_clarity"] * (n - 1) + comm.clarity) / n, 2)
        
        misunderstandings = sum(1 for c in self._communications if c.misunderstanding)
        self._stats["misunderstanding_rate"] = round(misunderstandings / n * 100, 1)

        response_times = [c.response_time_minutes for c in self._communications if c.response_time_minutes > 0]
        if response_times:
            self._stats["avg_response_time"] = round(sum(response_times) / len(response_times), 1)

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

    def _log_communication(self, comm: Communication):
        try:
            with open(COMM_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": comm.timestamp,
                    "channel": comm.channel,
                    "recipient": comm.recipient,
                    "purpose": comm.purpose,
                    "duration": comm.duration_minutes,
                    "effectiveness": comm.effectiveness,
                    "misunderstanding": comm.misunderstanding,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ca_instance: Optional[CommunicationAnalyzer] = None
_ca_lock = threading.Lock()


def get_communication_analyzer() -> CommunicationAnalyzer:
    global _ca_instance
    with _ca_lock:
        if _ca_instance is None:
            _ca_instance = CommunicationAnalyzer()
        return _ca_instance
