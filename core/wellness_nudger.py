"""
LOVE Proactive Wellness Nudger — Pattern-Based Wellness Alerts (Modern AI Pattern)

Most wellness tracking is reactive (user logs, then gets feedback). This nudger:

1. PATTERN DETECTION
   - Detect declining wellness patterns from conversation + logs
   - Identify missing wellness activities (exercise, hydration, sleep)
   - Spot burnout precursors (overwork, stress accumulation)

2. PROACTIVE NUDGE GENERATION
   - Generate contextual nudges when patterns suggest need
   - Time nudges for maximum receptiveness (not during focus)
   - Adapt nudge tone to user's current emotional state

3. NUDGE TYPES
   - Hydration: "You've been coding for 2 hours — drink water"
   - Movement: "Stand up and stretch — your back will thank you"
   - Rest: "You've hit your work limit — time to wind down"
   - Social: "You've been isolated today — reach out to someone"
   - Nutrition: "It's been 4 hours since your last meal"

4. EFFECTIVENESS TRACKING
   - Track which nudges get acted on
   - Learn user's receptiveness by time of day
   - Adjust nudge frequency to avoid annoyance

Architecture:
- detect_patterns(context): Detect wellness patterns
- generate_nudge(pattern): Generate appropriate nudge
- record_nudge_response(nudge_id, acted): Track effectiveness
- get_nudge_stats(): Track nudge performance
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "wellness_nudger"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NUDGE_LOG = DATA_DIR / "nudge_log.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WellnessPattern:
    """A detected wellness pattern."""
    pattern_type: str = ""  # hydration, movement, rest, social, nutrition
    severity: str = "info"  # info, warning, critical
    description: str = ""
    confidence: float = 0.5
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Nudge:
    """A wellness nudge to deliver to the user."""
    id: str = ""
    pattern_type: str = ""
    message: str = ""
    tone: str = "gentle"  # gentle, firm, urgent
    suggested_action: str = ""
    deliver_at: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class WellnessNudger:
    """
    Proactively nudge user toward wellness based on detected patterns.
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
        self._stats = {
            "total_nudges_sent": 0,
            "nudges_acted_on": 0,
            "nudges_ignored": 0,
            "avg_effectiveness": 0.0,
        }
        self._nudge_history: deque = deque(maxlen=200)
        self._receptiveness_by_hour: Dict[int, float] = defaultdict(float)
        self._load_stats()

    # ── Core Nudge Generation ────────────────────────────────────────────

    def detect_and_nudge(self, context: Optional[Dict[str, Any]] = None) -> Optional[Nudge]:
        """Detect patterns and generate nudge if warranted."""
        patterns = self._detect_patterns(context)

        if not patterns:
            return None

        # Pick highest severity pattern
        severity_order = {"critical": 3, "warning": 2, "info": 1}
        patterns.sort(key=lambda p: severity_order.get(p.severity, 0), reverse=True)
        top_pattern = patterns[0]

        # Check cooldown (don't nudge same pattern type within 2 hours)
        if self._is_in_cooldown(top_pattern.pattern_type):
            return None

        nudge = self._generate_nudge(top_pattern)

        with self._lock:
            self._stats["total_nudges_sent"] += 1
            self._nudge_history.append({
                "nudge_id": nudge.id,
                "pattern_type": nudge.pattern_type,
                "timestamp": datetime.now().isoformat(),
                "acted": False,
            })

        self._save_stats()
        self._log_nudge(nudge)

        return nudge

    def _detect_patterns(self, context: Optional[Dict[str, Any]]) -> List[WellnessPattern]:
        """Detect wellness patterns from context."""
        patterns = []

        if context is None:
            context = {}

        # Hydration pattern
        hydration_pct = context.get("hydration_pct", 1.0)
        if hydration_pct < 0.3:
            patterns.append(WellnessPattern(
                pattern_type="hydration",
                severity="warning",
                description="Very low hydration today",
                confidence=0.8,
            ))
        elif hydration_pct < 0.5:
            patterns.append(WellnessPattern(
                pattern_type="hydration",
                severity="info",
                description="Below target hydration",
                confidence=0.7,
            ))

        # Work limit pattern
        work_hours = context.get("work_hours_today", 0)
        work_limit = context.get("work_limit", 8)
        if work_hours > work_limit:
            patterns.append(WellnessPattern(
                pattern_type="rest",
                severity="critical",
                description=f"Work limit exceeded ({work_hours:.1f}h / {work_limit}h)",
                confidence=0.9,
            ))
        elif work_hours > work_limit * 0.8:
            patterns.append(WellnessPattern(
                pattern_type="rest",
                severity="warning",
                description="Approaching work limit",
                confidence=0.8,
            ))

        # Movement pattern
        hours_since_movement = context.get("hours_since_movement", 0)
        if hours_since_movement > 4:
            patterns.append(WellnessPattern(
                pattern_type="movement",
                severity="warning",
                description=f"No movement for {hours_since_movement} hours",
                confidence=0.8,
            ))

        # Sleep pattern
        sleep_hours = context.get("sleep_hours_last_night", 0)
        if sleep_hours < 5:
            patterns.append(WellnessPattern(
                pattern_type="rest",
                severity="critical",
                description=f"Very low sleep ({sleep_hours}h)",
                confidence=0.9,
            ))
        elif sleep_hours < 6:
            patterns.append(WellnessPattern(
                pattern_type="rest",
                severity="warning",
                description=f"Below recommended sleep ({sleep_hours}h)",
                confidence=0.8,
            ))

        # Social pattern
        hours_since_social = context.get("hours_since_social", 0)
        if hours_since_social > 12:
            patterns.append(WellnessPattern(
                pattern_type="social",
                severity="info",
                description="No social interaction today",
                confidence=0.6,
            ))

        # Nutrition pattern
        hours_since_meal = context.get("hours_since_meal", 0)
        if hours_since_meal > 6:
            patterns.append(WellnessPattern(
                pattern_type="nutrition",
                severity="warning",
                description=f"No meal for {hours_since_meal} hours",
                confidence=0.8,
            ))

        return patterns

    def _generate_nudge(self, pattern: WellnessPattern) -> Nudge:
        """Generate a nudge for a detected pattern."""
        nudge_templates = {
            "hydration": {
                "gentle": "Feeling a bit dry? A glass of water would help.",
                "firm": "You've been going for a while — hydrate now.",
                "urgent": "Dehydration alert — drink water immediately.",
            },
            "movement": {
                "gentle": "Maybe stretch your legs for a minute?",
                "firm": "You've been sitting a while — stand up and move.",
                "urgent": "Sedentary alert — get up and walk around NOW.",
            },
            "rest": {
                "gentle": "Your body might need a break soon.",
                "firm": "You've hit your limit — time to wind down.",
                "urgent": "Burnout risk — STOP and rest immediately.",
            },
            "social": {
                "gentle": "Maybe reach out to someone today?",
                "firm": "You've been isolated — call a friend.",
                "urgent": "Social isolation detected — connect with someone.",
            },
            "nutrition": {
                "gentle": "Your stomach might appreciate some food.",
                "firm": "It's been a while — time to eat.",
                "urgent": "Low energy detected — eat something nutritious.",
            },
        }

        tone_map = {"info": "gentle", "warning": "firm", "critical": "urgent"}
        tone = tone_map.get(pattern.severity, "gentle")

        message = nudge_templates.get(pattern.pattern_type, {}).get(tone, "Take care of yourself.")

        action_map = {
            "hydration": "drink water",
            "movement": "stretch or walk",
            "rest": "take a break",
            "social": "message someone",
            "nutrition": "eat something",
        }

        return Nudge(
            id=f"nudge_{pattern.pattern_type}_{int(time.time())}",
            pattern_type=pattern.pattern_type,
            message=message,
            tone=tone,
            suggested_action=action_map.get(pattern.pattern_type, "self-care"),
            deliver_at=datetime.now().isoformat(),
        )

    def _is_in_cooldown(self, pattern_type: str) -> bool:
        """Check if pattern type is in cooldown."""
        now = datetime.now()
        for entry in self._nudge_history:
            if entry.get("pattern_type") == pattern_type:
                try:
                    nudge_time = datetime.fromisoformat(entry.get("timestamp", ""))
                    if (now - nudge_time).total_seconds() < 7200:  # 2 hours
                        return True
                except Exception:
                    pass
        return False

    # ── Feedback ──────────────────────────────────────────────────────────

    def record_nudge_response(self, nudge_id: str, acted: bool):
        """Record whether user acted on nudge."""
        for entry in self._nudge_history:
            if entry.get("nudge_id") == nudge_id:
                entry["acted"] = acted
                break

        if acted:
            self._stats["nudges_acted_on"] += 1
            # Update receptiveness by hour
            hour = datetime.now().hour
            self._receptiveness_by_hour[hour] = self._receptiveness_by_hour.get(hour, 0) + 1
        else:
            self._stats["nudges_ignored"] += 1

        total = self._stats["nudges_acted_on"] + self._stats["nudges_ignored"]
        self._stats["avg_effectiveness"] = round(self._stats["nudges_acted_on"] / max(1, total), 2)

        self._save_stats()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_nudge_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "receptiveness_by_hour": dict(self._receptiveness_by_hour),
            "recent_nudges": list(self._nudge_history)[-10:],
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "receptiveness_by_hour": dict(self._receptiveness_by_hour),
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                self._receptiveness_by_hour.update(data.get("receptiveness_by_hour", {}))
        except Exception:
            pass

    def _log_nudge(self, nudge: Nudge):
        try:
            with open(NUDGE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "nudge_id": nudge.id,
                    "pattern_type": nudge.pattern_type,
                    "message": nudge.message[:100],
                    "tone": nudge.tone,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_wn_instance: Optional[WellnessNudger] = None
_wn_lock = threading.Lock()


def get_wellness_nudger() -> WellnessNudger:
    global _wn_instance
    with _wn_lock:
        if _wn_instance is None:
            _wn_instance = WellnessNudger()
        return _wn_instance
