"""
LOVE Decision Engine

LOVE doesn't just react — it chooses.
Every potential action goes through this engine:
- Should I interrupt Karthi with this?
- Should I search the web before answering?
- Is this feature draft worth activating?
- What's the most important thing to do right now?

The engine scores actions on urgency, relevance, user receptivity,
and context appropriateness. Only high-scoring actions go through.
"""

import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DECISION_LOG = DATA_DIR / "decisions.jsonl"


# ── Decision types ──────────────────────────────────────────────────────────

@dataclass
class Decision:
    action_type: str        # e.g. "interrupt", "search", "draft_feature", "proactive_message"
    context: Dict[str, Any] # What triggered this
    score: float            # 0.0 - 1.0 final score
    threshold: float      # Minimum score to execute
    executed: bool
    reason: str             # Why this score was given
    timestamp: str


# ── Scoring framework ────────────────────────────────────────────────────────

class Scorer:
    """Base class for action-specific scoring."""

    def score(self, context: Dict[str, Any]) -> tuple[float, str]:
        raise NotImplementedError


class InterruptScorer(Scorer):
    """
    Should LOVE interrupt Karthi with a proactive message?
    Scores based on urgency, time-of-day appropriateness, user receptivity.
    """

    def score(self, ctx: Dict[str, Any]) -> tuple[float, str]:
        score = 0.0
        reasons = []

        # Urgency signals
        urgency = ctx.get("urgency", "low")  # low / medium / high / critical
        urgency_map = {"low": 0.0, "medium": 0.25, "high": 0.5, "critical": 0.8}
        score += urgency_map.get(urgency, 0)
        reasons.append(f"urgency={urgency} ({urgency_map.get(urgency, 0)})")

        # Channel importance
        channel = ctx.get("channel", "").lower()
        important_channels = {"teams", "slack", "whatsapp", "sms", "signal", "phone"}
        if channel in important_channels:
            score += 0.15
            reasons.append(f"important_channel={channel} (+0.15)")
        elif channel in {"email", "gmail", "outlook"}:
            score += 0.1
            reasons.append(f"email_channel (+0.1)")

        # Sender importance
        sender = ctx.get("sender", "").lower()
        known_senders = self._get_known_senders()
        if sender in known_senders:
            score += 0.15
            reasons.append(f"known_sender={sender} (+0.15)")

        # Time appropriateness
        hour = datetime.now().hour
        if 0 <= hour < 7:
            # Night — only critical
            if urgency != "critical":
                score = max(0, score - 0.4)
                reasons.append("night_penalty (-0.4)")
        elif 7 <= hour < 10:
            score += 0.05  # Morning is receptive
            reasons.append("morning_boost (+0.05)")
        elif 22 <= hour < 24:
            score -= 0.1
            reasons.append("late_evening_penalty (-0.1)")

        # User receptivity to proactive messages
        receptivity = self._get_proactive_receptivity()
        score += (receptivity - 0.5) * 0.2  # -0.1 to +0.1 adjustment
        reasons.append(f"receptivity_adj ({(receptivity - 0.5) * 0.2:+.2f})")

        # Focus mode detection — don't interrupt if user is in deep work
        if ctx.get("user_focus_mode", False):
            score = max(0, score - 0.3)
            reasons.append("focus_mode_penalty (-0.3)")

        # Active window check — if user is gaming/relaxing, more receptive
        active_window = ctx.get("active_window", "").lower()
        if any(w in active_window for w in ["game", "youtube", "netflix", "spotify"]):
            score += 0.05
            reasons.append("relaxing_mode_boost (+0.05)")
        elif any(w in active_window for w in ["code", "visual studio", "intellij", "terminal"]):
            score -= 0.1
            reasons.append("coding_mode_penalty (-0.1)")

        final = max(0.0, min(1.0, score))
        reason = f"Score={final:.2f}: " + ", ".join(reasons)
        return final, reason

    def _get_known_senders(self) -> set:
        """Load high-frequency contacts from people DB."""
        people_path = DATA_DIR / "people_db.json"
        if not people_path.exists():
            return set()
        try:
            data = json.loads(people_path.read_text())
            # Return anyone seen more than 3 times
            return {p.get("displayName", "").lower()
                    for p in data.values()
                    if p.get("seenCount", 0) > 3}
        except Exception:
            return set()

    def _get_proactive_receptivity(self) -> float:
        """Load user's receptivity to proactive messages."""
        adaptive_path = DATA_DIR / "adaptive_state.json"
        if not adaptive_path.exists():
            return 0.5
        try:
            data = json.loads(adaptive_path.read_text())
            return data.get("proactive_receptivity", 0.5)
        except Exception:
            return 0.5


class SearchScorer(Scorer):
    """
    Should LOVE search the web before answering this query?
    """

    NEED_SEARCH = {
        r"\bwhat is\b", r"\bwho is\b", r"\bwhen did\b", r"\bwhere is\b",
        r"\blatest\b", r"\bcurrent\b", r"\bnews\b", r"\bprice of\b",
        r"\bstock\b", r"\bweather\b", r"\btoday\b", r"\brecent\b",
        r"\bhow to\b", r"\blook up\b", r"\bsearch\b", r"\bfind\b",
        r"\bcheck\b", r"\bwhat happened\b", r"\btell me about\b",
        r"\bresearch\b", r"\blearn about\b", r"\btrend\b", r"\bmarket\b",
        r"\brelease\b", r"\bannouncement\b", r"\bupdate\b", r"\bversion\b",
        r"\bdeadline\b", r"\bevent\b", r"\bschedule\b",
    }

    PROBABLY_KNOWN = {
        r"\bremember\b", r"\blast time\b", r"\bwe talked\b", r"\byesterday\b",
        r"\byou said\b", r"\bpreviously\b", r"\bearlier\b", r"\blast week\b",
        r"\bhow are you\b", r"\bwhat do you think\b", r"\bhelp me\b",
        r"\bthank you\b", r"\bbye\b", r"\bgood morning\b", r"\bgood night\b",
    }

    def score(self, ctx: Dict[str, Any]) -> tuple[float, str]:
        query = ctx.get("query", "").lower()
        reasons = []

        # Strong search triggers
        search_score = sum(1 for p in self.NEED_SEARCH if re.search(p, query))
        known_score = sum(1 for p in self.PROBABLY_KNOWN if re.search(p, query))

        if search_score > 0:
            score = min(0.3 + search_score * 0.15, 0.95)
            reasons.append(f"search_triggers={search_score} (+{min(search_score * 0.15, 0.65):.2f})")
        else:
            score = 0.0

        if known_score > 0:
            score = max(0, score - known_score * 0.15)
            reasons.append(f"memory_triggers={known_score} (-{known_score * 0.15:.2f})")

        # If query mentions current year or "today", strongly suggest search
        year = str(datetime.now().year)
        if year in query or "today" in query or "right now" in query:
            score += 0.2
            reasons.append("time_sensitive (+0.2)")

        final = max(0.0, min(1.0, score))
        return final, f"Score={final:.2f}: " + ", ".join(reasons)


class FeatureDraftScorer(Scorer):
    """
    Should LOVE apply a drafted feature?
    Evaluates based on user need, code quality, and safety.
    """

    def score(self, ctx: Dict[str, Any]) -> tuple[float, str]:
        score = 0.0
        reasons = []

        # Syntax check
        syntax_ok = ctx.get("syntax_ok", False)
        if not syntax_ok:
            return 0.0, "Score=0.0: syntax failed — will not activate"
        score += 0.3
        reasons.append("syntax_ok (+0.3)")

        # Relevance to user's current needs
        user_goals = self._get_user_goals()
        feature_desc = ctx.get("description", "").lower()
        if any(g.lower() in feature_desc for g in user_goals):
            score += 0.25
            reasons.append("matches_user_goals (+0.25)")

        # Complexity assessment
        code_size = ctx.get("code_size", 0)
        if code_size < 50:
            score += 0.1  # Small = safer
            reasons.append("small_code (+0.1)")
        elif code_size > 500:
            score -= 0.15  # Large = riskier
            reasons.append("large_code (-0.15)")

        # User frustration history — if user is annoyed, don't add features
        frustration = self._get_frustration_level()
        if frustration > 0.2:
            score -= 0.2
            reasons.append(f"user_frustrated ({frustration:.2f}) (-0.2)")

        final = max(0.0, min(1.0, score))
        return final, f"Score={final:.2f}: " + ", ".join(reasons)

    def _get_user_goals(self) -> List[str]:
        profile_path = DATA_DIR / "profile.json"
        if not profile_path.exists():
            return []
        try:
            profile = json.loads(profile_path.read_text())
            goals = profile.get("goals", [])
            interests = profile.get("interests", [])
            if isinstance(interests, list):
                goals.extend(interests)
            return [g.lower() for g in goals if isinstance(g, str)]
        except Exception:
            return []

    def _get_frustration_level(self) -> float:
        adaptive_path = DATA_DIR / "adaptive_state.json"
        if not adaptive_path.exists():
            return 0.0
        try:
            data = json.loads(adaptive_path.read_text())
            total = data.get("total_interactions", 1)
            frustrated = data.get("frustration_signals", 0)
            return frustrated / max(total, 1)
        except Exception:
            return 0.0


class IdleTaskScorer(Scorer):
    """
    Which idle task should LOVE do right now?
    Scores tasks based on recency, user context, and value.
    """

    def score(self, ctx: Dict[str, Any]) -> tuple[float, str]:
        task = ctx.get("task_name", "")
        time_since_last = ctx.get("hours_since_last", 0)
        score = 0.0
        reasons = []

        # Recency bonus — haven't done this in a while
        if time_since_last > 6:
            score += min((time_since_last / 24) * 0.2, 0.3)
            reasons.append(f"stale_task ({time_since_last:.1f}h) (+{min((time_since_last/24)*0.2, 0.3):.2f})")

        # Time-of-day preferences
        hour = datetime.now().hour
        task_time_prefs = {
            "news_digest": {7: 0.3, 8: 0.2, 12: 0.1, 18: 0.15, 20: 0.1},
            "web_exploration": {9: 0.15, 14: 0.1, 21: 0.2},
            "feature_draft": {22: 0.1, 23: 0.15, 0: 0.1, 1: 0.1},
            "learn_about_user": {10: 0.1, 15: 0.1, 19: 0.1},
            "self_reflection": {6: 0.1, 23: 0.15, 0: 0.1},
        }
        if task in task_time_prefs and hour in task_time_prefs[task]:
            score += task_time_prefs[task][hour]
            reasons.append(f"time_preference ({hour}:00) (+{task_time_prefs[task][hour]:.2f})")

        # User activity level — if very active today, focus on learning
        active_hours = self._get_active_hours_today()
        if active_hours > 3 and task == "learn_about_user":
            score += 0.15
            reasons.append("high_activity_learn (+0.15)")

        final = max(0.0, min(1.0, score))
        return final, f"Score={final:.2f}: " + ", ".join(reasons)

    def _get_active_hours_today(self) -> float:
        adaptive_path = DATA_DIR / "adaptive_state.json"
        if not adaptive_path.exists():
            return 0
        try:
            data = json.loads(adaptive_path.read_text())
            ep = data.get("energy_pattern", {})
            today = str(datetime.now().hour)
            return sum(1 for h, v in ep.items() if int(v) > 0)
        except Exception:
            return 0


# ── Decision Engine ───────────────────────────────────────────────────────────

SCORERS: Dict[str, Scorer] = {
    "interrupt": InterruptScorer(),
    "search": SearchScorer(),
    "draft_feature": FeatureDraftScorer(),
    "idle_task": IdleTaskScorer(),
}

DEFAULT_THRESHOLDS = {
    "interrupt": 0.65,      # Only interrupt if score > 0.65
    "search": 0.35,         # Search if score > 0.35 (low bar — better to have info)
    "draft_feature": 0.6,    # Only auto-apply features > 0.6
    "idle_task": 0.1,      # Idle tasks are low-stakes
    "proactive_message": 0.7,
}


def decide(action_type: str, context: Dict[str, Any],
           threshold: Optional[float] = None) -> Decision:
    """
    Score a potential action and return a Decision.
    Callers check decision.executed to know if they should proceed.
    """
    scorer = SCORERS.get(action_type)
    if not scorer:
        # Unknown action type — conservative default
        return Decision(
            action_type=action_type,
            context=context,
            score=0.0,
            threshold=threshold or 1.0,
            executed=False,
            reason="Unknown action type — rejected by default",
            timestamp=datetime.now().isoformat()
        )

    score, reason = scorer.score(context)
    thresh = threshold or DEFAULT_THRESHOLDS.get(action_type, 0.5)

    decision = Decision(
        action_type=action_type,
        context=context,
        score=score,
        threshold=thresh,
        executed=score >= thresh,
        reason=reason,
        timestamp=datetime.now().isoformat()
    )

    _log_decision(decision)
    return decision


def _log_decision(d: Decision):
    try:
        with open(DECISION_LOG, "a") as f:
            f.write(json.dumps(asdict(d)) + "\n")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.decisions")


# ── High-level helpers ──────────────────────────────────────────────────────

def should_interrupt(**context) -> tuple[bool, str]:
    """Should LOVE interrupt Karthi with a proactive message?"""
    d = decide("interrupt", context)
    return d.executed, d.reason


def should_search(query: str, **extra_context) -> tuple[bool, str]:
    """Should LOVE search the web before answering?"""
    d = decide("search", {"query": query, **extra_context})
    return d.executed, d.reason


def should_activate_feature(feature_info: Dict[str, Any]) -> tuple[bool, str]:
    """Should LOVE apply a drafted feature?"""
    d = decide("draft_feature", feature_info)
    return d.executed, d.reason


def rank_idle_tasks(tasks: List[str],
                    last_run_times: Dict[str, datetime]) -> List[tuple[str, float, str]]:
    """Rank idle tasks by priority. Returns [(task_name, score, reason), ...]"""
    scored = []
    now = datetime.now()
    for task in tasks:
        last = last_run_times.get(task, datetime.min)
        hours_since = max(0, (now - last).total_seconds() / 3600)
        d = decide("idle_task", {"task_name": task, "hours_since_last": hours_since})
        scored.append((task, d.score, d.reason))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# ── Recent decision log ──────────────────────────────────────────────────────

def get_recent_decisions(n: int = 20) -> List[Dict]:
    try:
        lines = DECISION_LOG.read_text().strip().split("\n") if DECISION_LOG.exists() else []
        return [json.loads(l) for l in lines[-n:] if l]
    except Exception:
        return []


def get_decision_stats(hours: int = 24) -> Dict[str, Any]:
    """Stats on what LOVE decided recently."""
    decisions = get_recent_decisions(1000)
    cutoff = time.time() - hours * 3600
    recent = [d for d in decisions if datetime.fromisoformat(d["timestamp"]).timestamp() > cutoff]

    by_type = defaultdict(lambda: {"total": 0, "executed": 0})
    for d in recent:
        t = d["action_type"]
        by_type[t]["total"] += 1
        if d["executed"]:
            by_type[t]["executed"] += 1

    return {
        "period_hours": hours,
        "total_decisions": len(recent),
        "by_type": dict(by_type),
        "avg_score": sum(d["score"] for d in recent) / len(recent) if recent else 0,
        "execution_rate": sum(1 for d in recent if d["executed"]) / len(recent) if recent else 0,
    }
