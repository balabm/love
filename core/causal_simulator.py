"""
LOVE Causal Simulator — Phase 5g of AGI Metamorphosis

Before executing high-stakes actions (Git commits, Binance trades, system changes),
LOVE simulates the consequences in a lightweight parallel thread.

This implements the Axiological Arbiter from the .cursorrules directive:
"Before executing any high-stakes action, LOVE spins a parallel thread
to simulate catastrophic failures. It only executes if the utility
outweighs the risk."

The simulator uses a fast, lightweight model (qwen2.5:0.5b) to evaluate:
- What could go wrong?
- What's the probability of failure?
- What's the worst-case outcome?
- Does the expected utility justify the risk?

Actions with risk_score > 0.7 require human approval.
Actions with risk_score > 0.9 are blocked regardless.
"""

import json
from typing import Dict, Any

from core.execution_guard import log_error


_LOW_STAKES_ACTIONS = frozenset({"speech", "push", "initiative", "notify", "log"})
_HIGH_RISK_KEYWORDS = frozenset({"trade", "buy", "sell", "delete", "format", "lock", "shutdown", "restart", "withdraw"})
_MEDIUM_RISK_KEYWORDS = frozenset({"commit", "push", "deploy", "install", "update", "migrate"})


def simulate_action_consequences(action: Dict[str, Any], context: str = "") -> Dict[str, Any]:
    """
    Run a lightweight causal simulation before executing a high-stakes action.

    Args:
        action: The action to simulate (with 'action' type and parameters)
        context: Additional context about the current system state

    Returns:
        Simulation result with risk_score, expected_outcome, and recommendation.
    """
    action_type = action.get("action", "unknown")
    action_desc = json.dumps(action, default=str)[:500]

    # Low-stakes actions skip simulation
    if action_type in _LOW_STAKES_ACTIONS:
        return {"risk_score": 0.1, "expected_outcome": "safe", "recommendation": "proceed", "simulated": True}

    # Build the simulation prompt
    sim_prompt = f"""You are LOVE's Causal Simulator. Your job is to quickly evaluate the risk of an action.

ACTION: {action_desc}
CONTEXT: {context[:300]}

Evaluate this action in 3 sentences:
1. What is the most likely outcome?
2. What is the worst-case scenario?
3. What is the risk level (0=safe, 1=catastrophic)?

Return ONLY valid JSON:
{{
    "likely_outcome": "brief description",
    "worst_case": "brief description",
    "risk_score": 0.0 to 1.0,
    "recommendation": "proceed" or "caution" or "block"
}}"""

    # Try to use a lightweight model for fast simulation
    try:
        from core.llm import route_llm
        llm = route_llm(sim_prompt, model_override="qwen2.5:0.5b")
        response = llm.invoke(sim_prompt) if hasattr(llm, "invoke") else llm(sim_prompt)

        # Parse JSON
        if isinstance(response, str):
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1:
                result = json.loads(response[start:end + 1])
                return {
                    "risk_score": float(result.get("risk_score", 0.5)),
                    "likely_outcome": result.get("likely_outcome", "unknown"),
                    "worst_case": result.get("worst_case", "unknown"),
                    "recommendation": result.get("recommendation", "caution"),
                    "simulated": True,
                }
    except Exception as e:
        log_error(e, module="core.causal_simulator", context={"phase": "causal_simulation"})

    # Fallback: rule-based risk assessment if LLM fails
    return _rule_based_risk_assessment(action)


def _rule_based_risk_assessment(action: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback risk assessment when LLM simulation is unavailable."""
    action_type = action.get("action", "unknown")
    action_str = str(action).lower()
    risk_score = 0.3
    recommendation = "proceed"

    # High-risk action types
    if action_type in _HIGH_RISK_KEYWORDS or any(w in action_str for w in _HIGH_RISK_KEYWORDS):
        risk_score = 0.8
        recommendation = "caution"
    # Medium-risk
    elif action_type in _MEDIUM_RISK_KEYWORDS or any(w in action_str for w in _MEDIUM_RISK_KEYWORDS):
        risk_score = 0.5
        recommendation = "caution"
    # Computer-use actions with many steps
    elif action_type == "action_plan":
        steps = action.get("steps", [])
        if len(steps) > 5:
            risk_score = 0.6
            recommendation = "caution"

    return {
        "risk_score": risk_score,
        "likely_outcome": "rule-based assessment",
        "worst_case": "unknown",
        "recommendation": recommendation,
        "simulated": False,
    }
