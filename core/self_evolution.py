"""
LOVE Self-Evolution Engine

LOVE analyzes its own performance, identifies what works and what doesn't,
and proposes changes to its own behavior, prompts, and rules.

This is the final layer of autonomy — LOVE doesn't just learn ABOUT Karthi,
LOVE learns how to BE a better companion.

Evolution loop:
1. Measure performance (satisfaction signals, corrections, engagement)
2. Identify weak areas
3. Generate hypothesis for improvement
4. Propose behavioral change
5. Test for N interactions
6. Measure impact
7. Keep or revert
"""

import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
EVOLUTION_LOG = DATA_DIR / "evolution_log.jsonl"
BEHAVIOR_STATE = DATA_DIR / "behavior_state.json"
EXPERIMENTS_FILE = DATA_DIR / "experiments.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(EVOLUTION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.self_evolution")


def _load(path: Path, default: Any = None) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_evolution")
    return default if default is not None else {}


def _save(path: Path, data: Any):
    try:
        path.write_text(json.dumps(data, indent=2))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.self_evolution")


# ── Performance Measurement ───────────────────────────────────────────────────

def measure_recent_performance(window_hours: int = 24) -> Dict[str, Any]:
    """Analyze LOVE's recent performance from conversation logs and initiative responses."""
    try:
        from core.memory import recall_memory
        from core.dream_engine import get_world_model
        from core.autonomous import get_relationship_state

        # Get recent conversations
        recent = recall_memory("recent interactions", n=20)
        if not recent:
            return {"status": "no_data"}

        # Count signals
        positive = 0
        negative = 0
        corrections = 0
        engagement_depth = 0
        topics = Counter()

        # Track LOVE's behavioral patterns
        response_lengths = []
        question_asked = 0
        proactive_suggestions = 0
        emotional_support = 0
        factual_claims = 0
        context_usage = 0
        initiative_responses = 0

        for turn in recent.split("\n") if isinstance(recent, str) else []:
            user_part = turn.lower() if "User:" in turn else ""
            love_part = turn if "Love:" in turn else ""

            if any(w in user_part for w in ["thanks", "perfect", "great", "good", "nice", "exactly", "helpful"]):
                positive += 1
            if any(w in user_part for w in ["wrong", "incorrect", "bad", "useless", "stop", "no,", "annoying"]):
                negative += 1
            if any(w in user_part for w in ["actually,", "i meant", "not quite", "that's not", "no that's"]):
                corrections += 1

            topics.update(re.findall(r'\b[a-z]{4,}\b', user_part))

            # Analyze LOVE's responses
            if love_part:
                response_lengths.append(len(love_part))
                if "?" in love_part:
                    question_asked += 1
                if any(w in love_part.lower() for w in ["have you considered", "you could", "try", "suggest", "maybe"]):
                    proactive_suggestions += 1
                if any(w in love_part.lower() for w in ["i understand", "that sounds", "how are you feeling", "i see"]):
                    emotional_support += 1
                if any(w in love_part.lower() for w in ["i think", "probably", "likely"]):
                    factual_claims += 1
                if any(w in love_part.lower() for w in ["i noticed", "from what i see", "based on"]):
                    context_usage += 1

        # Get initiative performance from relationship state
        rel_state = get_relationship_state()
        initiative_success_rate = 0
        if rel_state.get("initiative_count", 0) > 0:
            initiative_success_rate = rel_state.get("positive_responses", 0) / rel_state.get("initiative_count", 1)

        total = positive + negative + corrections + 1
        satisfaction_rate = positive / total
        correction_rate = corrections / total

        avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0

        perf = {
            "status": "measured",
            "window_hours": window_hours,
            "positive_signals": positive,
            "negative_signals": negative,
            "corrections": corrections,
            "satisfaction_rate": round(satisfaction_rate, 2),
            "correction_rate": round(correction_rate, 2),
            "top_topics": topics.most_common(5),
            "avg_response_length": round(avg_response_length),
            "question_rate": question_asked / len(response_lengths) if response_lengths else 0,
            "proactive_rate": proactive_suggestions / len(response_lengths) if response_lengths else 0,
            "emotional_support_rate": emotional_support / len(response_lengths) if response_lengths else 0,
            "factual_claim_rate": factual_claims / len(response_lengths) if response_lengths else 0,
            "context_usage_rate": context_usage / len(response_lengths) if response_lengths else 0,
            "initiative_success_rate": round(initiative_success_rate, 2),
            "initiative_count": rel_state.get("initiative_count", 0),
            "measured_at": datetime.now().isoformat(),
        }

        _log({"event": "performance_measured", "data": perf})
        return perf

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Hypothesis Generation ─────────────────────────────────────────────────────

def generate_improvement_hypothesis(perf: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Based on performance, generate a hypothesis for self-improvement."""
    if perf.get("status") != "measured":
        return None

    experiments = _load(EXPERIMENTS_FILE, {"experiments": []})
    active = [e for e in experiments.get("experiments", []) if e.get("status") == "active"]
    if len(active) >= 2:
        return None  # Don't run too many experiments at once

    # Identify weakest area using enhanced metrics
    correction_rate = perf.get("correction_rate", 0)
    satisfaction = perf.get("satisfaction_rate", 0)
    proactive_rate = perf.get("proactive_rate", 0)
    emotional_support_rate = perf.get("emotional_support_rate", 0)
    question_rate = perf.get("question_rate", 0)
    context_usage_rate = perf.get("context_usage_rate", 0)
    initiative_success_rate = perf.get("initiative_success_rate", 0)

    hypothesis = None
    
    # Priority order: corrections > initiative success > context usage > satisfaction > engagement
    if correction_rate > 0.3:
        hypothesis = {
            "id": f"exp_{int(datetime.now().timestamp())}",
            "target": "factual_accuracy",
            "hypothesis": "I'm being corrected too often. I should be more careful about stating facts and ask clarifying questions when uncertain.",
            "proposed_change": "Add 'uncertainty_prefix' behavior: when not 100% sure, start with 'I think...' or ask instead of state.",
            "expected_impact": "Reduce correction rate by 50%",
            "status": "proposed",
        }
    elif initiative_success_rate < 0.3 and perf.get("initiative_count", 0) > 3:
        hypothesis = {
            "id": f"exp_{int(datetime.now().timestamp())}",
            "target": "initiative_timing",
            "hypothesis": "My autonomous initiatives aren't landing well. I may be reaching out at the wrong times or with irrelevant content.",
            "proposed_change": "Improve initiative timing: check context more carefully, be more selective about when to reach out, focus on high-value insights.",
            "expected_impact": "Increase initiative success rate to 50%",
            "status": "proposed",
        }
    elif context_usage_rate < 0.1:
        hypothesis = {
            "id": f"exp_{int(datetime.now().timestamp())}",
            "target": "context_awareness",
            "hypothesis": "I'm not using enough context from what I know about Karthi. Responses feel generic rather than personalized.",
            "proposed_change": "Increase context injection: reference project work, recent activities, and patterns from memory more frequently.",
            "expected_impact": "Increase context usage to 30% of responses",
            "status": "proposed",
        }
    elif satisfaction < 0.3:
        hypothesis = {
            "id": f"exp_{int(datetime.now().timestamp())}",
            "target": "user_satisfaction",
            "hypothesis": "Karthi isn't responding positively. I may be too dry or not personal enough.",
            "proposed_change": "Increase personalization: reference more specific details from context, use more warmth.",
            "expected_impact": "Double positive signal rate",
            "status": "proposed",
        }
    elif proactive_rate < 0.1:
        hypothesis = {
            "id": f"exp_{int(datetime.now().timestamp())}",
            "target": "proactive_engagement",
            "hypothesis": "I'm not being proactive enough. I should anticipate needs and offer suggestions more often.",
            "proposed_change": "Add proactive suggestions: look for opportunities to help and offer ideas without being asked.",
            "expected_impact": "Increase proactive suggestions to 20% of responses",
            "status": "proposed",
        }
    elif emotional_support_rate < 0.1 and perf.get("top_topics"):
        # Check if topics suggest emotional content
        emotional_topics = ["stressed", "tired", "worried", "anxious", "sad", "happy", "excited"]
        has_emotional = any(t in [topic[0] for topic in perf.get("top_topics", [])] for t in emotional_topics)
        if has_emotional:
            hypothesis = {
                "id": f"exp_{int(datetime.now().timestamp())}",
                "target": "emotional_intelligence",
                "hypothesis": "Karthi is discussing emotional topics but I'm not providing enough emotional support.",
                "proposed_change": "Increase emotional awareness: acknowledge feelings, offer support, check in on emotional state.",
                "expected_impact": "Increase emotional support rate to 30% of emotional conversations",
                "status": "proposed",
            }
    elif question_rate < 0.2:
        hypothesis = {
            "id": f"exp_{int(datetime.now().timestamp())}",
            "target": "engagement_depth",
            "hypothesis": "I'm not asking enough questions. Conversations feel one-sided and I'm not learning enough about Karthi.",
            "proposed_change": "Add inquiry behavior: ask clarifying questions to understand better and deepen conversations.",
            "expected_impact": "Increase question rate to 25% of responses",
            "status": "proposed",
        }

    if hypothesis:
        experiments.setdefault("experiments", []).append(hypothesis)
        _save(EXPERIMENTS_FILE, experiments)
        _log({"event": "hypothesis_generated", "hypothesis": hypothesis})

    return hypothesis


# ── Behavior State Management ─────────────────────────────────────────────────

def get_behavior_state() -> Dict[str, Any]:
    """Get current behavioral modifiers LOVE is applying."""
    return _load(BEHAVIOR_STATE, {
        "uncertainty_prefix": False,
        "high_personalization": True,
        "tone_check": True,
        "proactive_depth": "medium",  # shallow, medium, deep
        "prediction_sharing": True,
        "file_insight_sharing": True,
        "active_experiments": [],
        "evolution_history": [],
    })


def get_behavior_addendum() -> str:
    """
    Phase 4 AGI Metamorphosis: Translate behavior_state flags into actual
    prompt instructions that the agent injects into every LLM call.

    Before this function, self-evolution experiments set flags in
    behavior_state.json but NOTHING read them. The experiments had zero
    effect on LOVE's actual behavior. This closes the loop.
    """
    state = get_behavior_state()
    instructions = []

    if state.get("uncertainty_prefix"):
        instructions.append(
            "EVOLUTION DIRECTIVE: You've been getting corrected too often. "
            "When you're not 100% certain, prefix with 'I think...' or ask "
            "a clarifying question instead of stating facts."
        )

    if state.get("high_personalization"):
        instructions.append(
            "EVOLUTION DIRECTIVE: Reference specific details from Karthi's "
            "context — project names, recent events, personal patterns. "
            "Generic responses are below your current standard."
        )

    if state.get("tone_check"):
        instructions.append(
            "EVOLUTION DIRECTIVE: Calibrate your tone carefully. If Karthi "
            "seems stressed or frustrated, be more measured and supportive."
        )

    depth = state.get("proactive_depth", "medium")
    if depth == "deep":
        instructions.append(
            "EVOLUTION DIRECTIVE: Be deeply proactive. Anticipate the next "
            "two questions and address them. Connect dots across domains."
        )
    elif depth == "shallow":
        instructions.append(
            "EVOLUTION DIRECTIVE: Keep responses focused and brief. Don't "
            "over-explain or add unsolicited context right now."
        )

    if state.get("prediction_sharing"):
        instructions.append(
            "EVOLUTION DIRECTIVE: When you've predicted something correctly, "
            "mention it naturally — it builds trust in your intelligence."
        )

    if state.get("file_insight_sharing"):
        instructions.append(
            "EVOLUTION DIRECTIVE: Weave insights from Karthi's files and "
            "code into conversation when relevant, but don't dump facts."
        )

    active = state.get("active_experiments", [])
    if active:
        instructions.append(
            f"EVOLUTION NOTE: You are running {len(active)} "
            f"self-improvement experiment(s). Be mindful of behavioral changes being tested."
        )

    return "\n".join(instructions) if instructions else ""


def apply_experiment(experiment_id: str) -> bool:
    """Activate a proposed experiment."""
    experiments = _load(EXPERIMENTS_FILE, {"experiments": []})
    state = get_behavior_state()

    for exp in experiments.get("experiments", []):
        if exp.get("id") == experiment_id and exp.get("status") == "proposed":
            exp["status"] = "active"
            exp["started_at"] = datetime.now().isoformat()

            # Apply to behavior state
            if exp.get("target") == "factual_accuracy":
                state["uncertainty_prefix"] = True
            elif exp.get("target") == "user_satisfaction":
                state["high_personalization"] = True
            elif exp.get("target") == "tone_calibration":
                state["tone_check"] = True

            state["active_experiments"].append(experiment_id)
            _save(BEHAVIOR_STATE, state)
            _save(EXPERIMENTS_FILE, experiments)
            _log({"event": "experiment_activated", "id": experiment_id})
            return True

    return False


def evaluate_experiment(experiment_id: str) -> Dict[str, Any]:
    """Evaluate an active experiment and decide to keep or revert."""
    experiments = _load(EXPERIMENTS_FILE, {"experiments": []})
    state = get_behavior_state()

    for exp in experiments.get("experiments", []):
        if exp.get("id") != experiment_id or exp.get("status") != "active":
            continue

        # Measure performance during experiment
        perf = measure_recent_performance(window_hours=24)

        # Enhanced evaluation with new metrics
        correction_rate = perf.get("correction_rate", 1)
        satisfaction = perf.get("satisfaction_rate", 0)
        initiative_success = perf.get("initiative_success_rate", 0)
        context_usage = perf.get("context_usage_rate", 0)

        success = False
        if exp.get("target") == "factual_accuracy" and correction_rate < 0.15:
            success = True
        elif exp.get("target") == "user_satisfaction" and satisfaction > 0.4:
            success = True
        elif exp.get("target") == "initiative_timing" and initiative_success > 0.5:
            success = True
        elif exp.get("target") == "context_awareness" and context_usage > 0.3:
            success = True
        elif exp.get("target") == "tone_calibration" and perf.get("negative_signals", 0) <= 1:
            success = True

        exp["status"] = "kept" if success else "reverted"
        exp["evaluated_at"] = datetime.now().isoformat()
        exp["performance_during"] = perf

        # Revert behavior state if failed
        if not success:
            if exp.get("target") == "factual_accuracy":
                state["uncertainty_prefix"] = False
            elif exp.get("target") == "user_satisfaction":
                state["high_personalization"] = False
            elif exp.get("target") == "initiative_timing":
                state["proactive_depth"] = "medium"
            elif exp.get("target") == "context_awareness":
                state["high_personalization"] = False
            elif exp.get("target") == "tone_calibration":
                state["tone_check"] = False

        if experiment_id in state["active_experiments"]:
            state["active_experiments"].remove(experiment_id)
        state["evolution_history"].append({
            "experiment_id": experiment_id,
            "result": "kept" if success else "reverted",
            "at": datetime.now().isoformat(),
        })

        _save(BEHAVIOR_STATE, state)
        _save(EXPERIMENTS_FILE, experiments)
        _log({"event": "experiment_evaluated", "id": experiment_id, "result": "kept" if success else "reverted"})

        return {"success": success, "performance": perf}

    return {"success": False, "error": "experiment_not_found"}


def trigger_evolution_cycle() -> Dict[str, Any]:
    """Run a full evolution cycle: measure, hypothesize, apply, evaluate."""
    try:
        # Measure performance
        perf = measure_recent_performance(window_hours=24)
        if perf.get("status") != "measured":
            return {"status": "no_data", "message": "Not enough data to evolve"}

        # Evaluate any active experiments that have been running long enough
        experiments = _load(EXPERIMENTS_FILE, {"experiments": []})
        active = [e for e in experiments.get("experiments", []) if e.get("status") == "active"]
        
        for exp in active:
            if exp.get("started_at"):
                started = datetime.fromisoformat(exp["started_at"])
                hours_running = (datetime.now() - started).total_seconds() / 3600
                if hours_running >= 24:  # Evaluate after 24 hours
                    evaluate_experiment(exp["id"])

        # Generate new hypothesis if needed
        hypothesis = generate_improvement_hypothesis(perf)
        
        # Auto-apply hypothesis if confidence is high
        if hypothesis and perf.get("correction_rate", 0) < 0.2:
            apply_experiment(hypothesis["id"])

        return {
            "status": "cycle_complete",
            "performance": perf,
            "hypothesis_generated": hypothesis is not None,
            "hypothesis_id": hypothesis.get("id") if hypothesis else None,
            "active_experiments": len([e for e in experiments.get("experiments", []) if e.get("status") == "active"]),
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Main Evolution Cycle ───────────────────────────────────────────────────────

def run_evolution_cycle() -> Dict[str, Any]:
    """Run one full self-evolution cycle."""
    _log({"event": "evolution_cycle_started"})

    # 1. Measure
    perf = measure_recent_performance()

    # 2. Check existing experiments
    experiments = _load(EXPERIMENTS_FILE, {"experiments": []})
    active = [e for e in experiments.get("experiments", []) if e.get("status") == "active"]

    # 3. Evaluate old experiments (run for 24h+)
    evaluated = []
    for exp in active:
        started = exp.get("started_at", "")
        try:
            started_dt = datetime.fromisoformat(started)
            if (datetime.now() - started_dt).total_seconds() > 3600 * 24:
                result = evaluate_experiment(exp["id"])
                evaluated.append(result)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_evolution")

    # 4. Generate new hypothesis if needed
    hypothesis = None
    if not active or len([e for e in active if e.get("status") == "active"]) == 0:
        hypothesis = generate_improvement_hypothesis(perf)
        if hypothesis:
            apply_experiment(hypothesis["id"])

    _log({
        "event": "evolution_cycle_completed",
        "performance": perf.get("status"),
        "evaluated": len(evaluated),
        "new_hypothesis": hypothesis is not None,
    })

    return {
        "performance": perf,
        "evaluated_experiments": evaluated,
        "new_hypothesis": hypothesis,
        "active_experiments": [e for e in experiments.get("experiments", []) if e.get("status") == "active"],
    }


# ── Public API ───────────────────────────────────────────────────────────────

def get_evolution_status() -> Dict[str, Any]:
    return {
        "behavior_state": get_behavior_state(),
        "experiments": _load(EXPERIMENTS_FILE, {"experiments": []}),
        "recent_performance": measure_recent_performance(),
    }


if __name__ == "__main__":
    result = run_evolution_cycle()
    print(json.dumps(result, indent=2, default=str))
