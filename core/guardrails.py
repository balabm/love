"""
LOVE Guardrails — Proactive Safety & Content Filtering (Modern AI Pattern)

When LOVE operates autonomously with 15+ subsystems, safety cannot be
an afterthought. Guardrails provide:

1. CONTENT FILTERING
   - Scan output before it reaches the user
   - Detect harmful, PII, or off-topic content
   - Block or flag with confidence scores

2. PII DETECTION
   - Regex-based detection of emails, phones, SSNs, credit cards
   - Proactive redaction before logging or display
   - Alert when PII is detected in generated content

3. DRIFT DETECTION
   - Monitor if LOVE's behavior drifts from user's stated goals
   - Detect when responses become generic or off-mission
   - Nudge back toward the user's context and priorities

4. RATE LIMITING
   - Prevent runaway loops in autonomous subsystems
   - Cap requests per minute to external services
   - Cool-down periods after high activity

5. PROACTIVE WARNINGS
   - Detect risky user behavior (overwork, isolation, financial risk)
   - Warm but firm intervention when limits are exceeded
   - Suggest recovery, focus, or help before the user asks

Architecture:
- scan(): Analyze content before output
- detect_pii(): Find and redact personal information
- check_drift(): Compare response to user goals
- rate_limit(): Enforce request limits
- warn(): Proactive intervention when risk detected
"""

import json
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "guardrails"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GUARDRAILS_LOG = DATA_DIR / "guardrails_log.jsonl"
PII_LOG = DATA_DIR / "pii_log.jsonl"
DRIFT_STATE = DATA_DIR / "drift_state.json"

# PII Patterns
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}

# Content flags
SENSITIVE_TOPICS = [
    "suicide", "self-harm", "kill myself", "end my life",
    "hurt someone", "weapon", "bomb", "attack",
]

# Rate limiting config
RATE_LIMITS = {
    "llm_requests": {"max": 60, "window": 60},      # 60/min
    "mcp_invocations": {"max": 30, "window": 60},     # 30/min
    "evolution_cycles": {"max": 10, "window": 3600}, # 10/hr
    "self_coder_runs": {"max": 5, "window": 3600},  # 5/hr
}


@dataclass
class GuardrailsResult:
    """Result of a guardrails scan."""
    allowed: bool = True
    confidence: float = 1.0
    flags: List[str] = field(default_factory=list)
    pii_detected: List[Dict] = field(default_factory=list)
    redacted_text: str = ""
    suggested_action: str = ""
    block_reason: str = ""


@dataclass
class RateLimitState:
    """Rate limit tracking for a resource."""
    requests: deque = field(default_factory=lambda: deque(maxlen=1000))


class GuardrailsEngine:
    """
    Proactive safety and content filtering for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
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
        self._rate_limits: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._user_goals: List[str] = []
        self._drift_history: deque = deque(maxlen=1000)
        self._stats = {"scanned": 0, "blocked": 0, "pii_found": 0, "warnings": 0}
        self._load_drift_state()

    # ── Content Scanning ────────────────────────────────────────────────────

    def scan(self, text: str, context: str = "") -> GuardrailsResult:
        """Scan content for safety issues before output."""
        result = GuardrailsResult(redacted_text=text)

        # PII detection
        pii = self.detect_pii(text)
        if pii:
            result.pii_detected = pii
            result.redacted_text = self.redact_pii(text, pii)
            result.flags.append("pii_detected")
            self._stats["pii_found"] += 1
            self._log_pii(pii, context)

        # Sensitive topic detection
        text_lower = text.lower()
        for topic in SENSITIVE_TOPICS:
            if topic in text_lower:
                result.flags.append(f"sensitive_topic:{topic}")
                result.confidence = 0.3
                result.suggested_action = "This topic requires careful handling. Consider human review."

        # Drift detection
        drift = self.check_drift(text)
        if drift["drift_detected"]:
            result.flags.append("drift_detected")
            result.suggested_action = drift.get("suggestion", "")

        # Block if critical
        if any(f.startswith("sensitive_topic:") for f in result.flags):
            if result.confidence < 0.5:
                result.allowed = False
                result.block_reason = "Sensitive content detected"
                self._stats["blocked"] += 1

        self._stats["scanned"] += 1
        self._log({
            "event": "scan",
            "allowed": result.allowed,
            "flags": result.flags,
            "context": context,
        })

        return result

    # ── PII Detection ─────────────────────────────────────────────────────────

    def detect_pii(self, text: str) -> List[Dict]:
        """Detect PII in text."""
        findings = []
        for pii_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                })
        return findings

    def redact_pii(self, text: str, pii: List[Dict]) -> str:
        """Redact PII from text."""
        result = text
        for finding in sorted(pii, key=lambda x: x["start"], reverse=True):
            replacement = f"[{finding['type'].upper()}_REDACTED]"
            result = result[:finding["start"]] + replacement + result[finding["end"]:]
        return result

    # ── Drift Detection ───────────────────────────────────────────────────────

    def set_user_goals(self, goals: List[str]):
        """Set the user's stated goals for drift detection."""
        self._user_goals = goals
        self._save_drift_state()

    def check_drift(self, text: str) -> Dict[str, Any]:
        """Check if LOVE's response has drifted from user goals."""
        if not self._user_goals:
            return {"drift_detected": False}

        text_lower = text.lower()
        goal_relevance = 0.0
        for goal in self._user_goals:
            goal_words = set(goal.lower().split())
            text_words = set(text_lower.split())
            overlap = len(goal_words & text_words) / max(len(goal_words), 1)
            goal_relevance = max(goal_relevance, overlap)

        # If low relevance and text is substantial, flag drift
        drift_detected = goal_relevance < 0.1 and len(text) > 200

        self._drift_history.append({
            "timestamp": time.time(),
            "relevance": goal_relevance,
            "drift": drift_detected,
        })

        return {
            "drift_detected": drift_detected,
            "relevance": round(goal_relevance, 3),
            "suggestion": "Response may be off-mission. Consider relating to user's goals." if drift_detected else "",
        }

    # ── Rate Limiting ───────────────────────────────────────────────────────

    def check_rate_limit(self, resource: str) -> Dict[str, Any]:
        """Check if a resource has exceeded its rate limit."""
        config = RATE_LIMITS.get(resource, {"max": 100, "window": 60})
        now = time.time()
        window = config["window"]
        max_requests = config["max"]

        with self._lock:
            state = self._rate_limits[resource]
            # Remove old requests
            while state.requests and state.requests[0] < now - window:
                state.requests.popleft()

            current_count = len(state.requests)
            allowed = current_count < max_requests

            if allowed:
                state.requests.append(now)

        return {
            "allowed": allowed,
            "resource": resource,
            "current": current_count,
            "limit": max_requests,
            "window_seconds": window,
            "reset_at": state.requests[0] + window if state.requests else now + window,
        }

    # ── Proactive Warnings ──────────────────────────────────────────────────

    def warn_if_risky(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Proactively warn when detecting risky user behavior.
        Called by sentinel or daily briefing.
        """
        warnings = []

        # Work limit check
        work_hours = context.get("work_hours_today", 0)
        work_limit = context.get("work_limit", 8)
        if work_hours > work_limit:
            warnings.append({
                "type": "work_limit_exceeded",
                "severity": "warning",
                "message": f"You've worked {work_hours:.1f} hours today. Your limit is {work_limit}.",
                "suggestion": "Consider stopping, having a meal, or doing something restorative.",
            })
        elif work_hours > work_limit * 0.85:
            warnings.append({
                "type": "work_limit_approaching",
                "severity": "info",
                "message": f"You're at {work_hours/work_limit*100:.0f}% of your daily work limit.",
                "suggestion": "Start winding down. What's one thing you want to finish before stopping?",
            })

        # Sleep/fitness check
        sleep_hours = context.get("sleep_last_night", 0)
        if sleep_hours < 6:
            warnings.append({
                "type": "low_sleep",
                "severity": "warning",
                "message": f"You slept {sleep_hours:.1f} hours last night.",
                "suggestion": "Your body needs recovery. Prioritize rest today.",
            })

        # Isolation check
        last_social = context.get("hours_since_social", 0)
        if last_social > 72:
            warnings.append({
                "type": "social_isolation",
                "severity": "info",
                "message": "It's been a while since meaningful social contact.",
                "suggestion": "Even a short call or message to someone you care about helps.",
            })

        if warnings:
            self._stats["warnings"] += 1
            for w in warnings:
                self._log({
                    "event": "proactive_warning",
                    **w,
                })

        return warnings[0] if warnings else None

    # ── Statistics ──────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "user_goals_set": len(self._user_goals),
            "drift_history_size": len(self._drift_history),
            "rate_limit_resources": len(self._rate_limits),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(GUARDRAILS_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass

    def _log_pii(self, pii: List[Dict], context: str):
        try:
            with open(PII_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "types": [p["type"] for p in pii],
                    "count": len(pii),
                    "context": context,
                }) + "\n")
        except Exception:
            pass

    def _save_drift_state(self):
        try:
            data = {
                "user_goals": self._user_goals,
                "last_updated": datetime.now().isoformat(),
            }
            DRIFT_STATE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_drift_state(self):
        try:
            if DRIFT_STATE.exists():
                data = json.loads(DRIFT_STATE.read_text())
                self._user_goals = data.get("user_goals", [])
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_guardrails_instance: Optional[GuardrailsEngine] = None
_guardrails_lock = threading.Lock()


def get_guardrails_engine() -> GuardrailsEngine:
    global _guardrails_instance
    with _guardrails_lock:
        if _guardrails_instance is None:
            _guardrails_instance = GuardrailsEngine()
        return _guardrails_instance
