"""
LOVE Causal World Model — Counterfactual Reasoning Engine

The existing WorldModel stores facts and causal links.
This engine REASONS with them — answering:

  "What would happen IF...?"
  "WHY did X happen?"
  "What's the BEST action given the current state?"

Capabilities:
1. Causal Chain Tracing — Follow cause→effect→effect chains
2. Counterfactual Simulation — "If Karthi had slept 8 hours, would he be less stressed?"
3. Intervention Planning — "What should we CHANGE to get outcome Y?"
4. Causal Anomaly Detection — "This effect happened without its usual cause — investigate"
5. Root Cause Analysis — "Karthi is unproductive. Is it sleep? Stress? Boredom?"

This is what separates correlation-based systems (ML) from causal AGI.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import threading

from core.llm import get_reasoning_llm
from core.world_model import get_world_model, CausalLink
from core.consciousness import get_consciousness

DATA_DIR = Path(__file__).parent.parent / "data"
CAUSAL_LOG = DATA_DIR / "causal_reasoning.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CausalChain:
    """A traced chain of cause → effect → effect..."""
    trigger: str
    chain: List[Tuple[str, str, float]]  # (cause, effect, strength)
    terminal_effect: str
    cumulative_strength: float
    conditions: List[str] = field(default_factory=list)


@dataclass
class Counterfactual:
    """A 'what if' simulation result."""
    scenario: str           # "If Karthi slept 8 hours..."
    actual_state: str       # "He slept 5 hours"
    predicted_outcome: str  # "Stress would be 30% lower"
    causal_path: str        # The reasoning chain
    confidence: float
    actionable: bool        # Can we actually change this?


@dataclass
class Intervention:
    """A recommended action to change a causal outcome."""
    target_outcome: str       # What we want to achieve
    intervention_point: str   # Where in the causal chain to intervene
    action: str               # What to do
    expected_effect: str      # What should happen
    confidence: float
    side_effects: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard


class CausalReasoningEngine:
    """
    Reasons about cause and effect using the WorldModel's causal graph.
    """

    def __init__(self):
        self.world_model = get_world_model()
        self._lock = threading.Lock()

    # ── Causal Chain Tracing ─────────────────────────────────────────────────

    def trace_effects(self, cause: str, max_depth: int = 5) -> List[CausalChain]:
        """
        Follow a cause forward through chains of effects.
        "If X happens, what else happens as a consequence?"
        """
        chains = []
        self._trace_recursive(cause, [], 1.0, max_depth, chains)
        # Sort by cumulative strength
        chains.sort(key=lambda c: c.cumulative_strength, reverse=True)
        return chains

    def _trace_recursive(self, current_cause: str, chain_so_far: List,
                         cumulative_strength: float, depth_remaining: int,
                         results: List[CausalChain]):
        if depth_remaining <= 0:
            return

        for link in self.world_model.causal_links:
            if link.cause.lower() in current_cause.lower():
                new_chain = chain_so_far + [(link.cause, link.effect, link.strength)]
                new_strength = cumulative_strength * link.strength

                # Record this chain
                results.append(CausalChain(
                    trigger=chain_so_far[0][0] if chain_so_far else current_cause,
                    chain=new_chain,
                    terminal_effect=link.effect,
                    cumulative_strength=new_strength,
                    conditions=link.conditions,
                ))

                # Continue tracing
                self._trace_recursive(
                    link.effect, new_chain, new_strength,
                    depth_remaining - 1, results
                )

    def trace_causes(self, effect: str, max_depth: int = 5) -> List[CausalChain]:
        """
        Trace backward from an effect to its root causes.
        "WHY did X happen?"
        """
        chains = []
        self._trace_causes_recursive(effect, [], 1.0, max_depth, chains)
        chains.sort(key=lambda c: c.cumulative_strength, reverse=True)
        return chains

    def _trace_causes_recursive(self, current_effect: str, chain_so_far: List,
                                 cumulative_strength: float, depth_remaining: int,
                                 results: List[CausalChain]):
        if depth_remaining <= 0:
            return

        for link in self.world_model.causal_links:
            if link.effect.lower() in current_effect.lower():
                new_chain = [(link.cause, link.effect, link.strength)] + chain_so_far
                new_strength = cumulative_strength * link.strength

                results.append(CausalChain(
                    trigger=link.cause,
                    chain=new_chain,
                    terminal_effect=current_effect,
                    cumulative_strength=new_strength,
                    conditions=link.conditions,
                ))

                self._trace_causes_recursive(
                    link.cause, new_chain, new_strength,
                    depth_remaining - 1, results
                )

    # ── Counterfactual Simulation ────────────────────────────────────────────

    def counterfactual(self, scenario: str, actual_state: str,
                       context: Dict[str, Any] = None) -> Counterfactual:
        """
        "What would have happened if X instead of Y?"
        Uses LLM + causal graph for grounded counterfactual reasoning.
        """
        # First, gather relevant causal chains
        relevant_chains = self.trace_effects(scenario, max_depth=3)
        chain_text = ""
        if relevant_chains:
            chain_text = "KNOWN CAUSAL RELATIONSHIPS:\n"
            for chain in relevant_chains[:5]:
                path = " → ".join(f"{c} [→ {e}]" for c, e, s in chain.chain)
                chain_text += f"  {path} (strength: {chain.cumulative_strength:.2f})\n"

        llm = get_reasoning_llm(temperature=0.3)
        prompt = f"""You are performing counterfactual reasoning.

SCENARIO (what-if): {scenario}
ACTUAL STATE: {actual_state}
CONTEXT: {json.dumps(context or {}, indent=2, default=str)[:1000]}

{chain_text}

Based on the causal relationships and context:
1. What would the outcome have been under the counterfactual scenario?
2. Trace the causal reasoning step by step.
3. How confident are you?
4. Is this something the user can actually change?

Return JSON:
{{
  "predicted_outcome": "What would have happened",
  "causal_path": "Step-by-step reasoning",
  "confidence": 0.75,
  "actionable": true
}}"""

        try:
            response = str(llm.invoke(prompt))
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                result = Counterfactual(
                    scenario=scenario,
                    actual_state=actual_state,
                    predicted_outcome=data.get("predicted_outcome", "Unknown"),
                    causal_path=data.get("causal_path", ""),
                    confidence=data.get("confidence", 0.5),
                    actionable=data.get("actionable", False),
                )
                self._log("counterfactual", {
                    "scenario": scenario, "actual": actual_state,
                    "result": data, "chains_used": len(relevant_chains),
                })
                return result
        except Exception as e:
            print(f"[CausalReasoning] Counterfactual error: {e}")

        return Counterfactual(
            scenario=scenario, actual_state=actual_state,
            predicted_outcome="Unable to reason about this counterfactual",
            causal_path="", confidence=0.1, actionable=False,
        )

    # ── Intervention Planning ────────────────────────────────────────────────

    def plan_intervention(self, target_outcome: str,
                          current_state: Dict[str, Any] = None) -> List[Intervention]:
        """
        "How can we achieve outcome X? Where should we intervene?"
        Uses backward causal tracing + LLM synthesis.
        """
        # Trace causes of the target outcome
        cause_chains = self.trace_causes(target_outcome, max_depth=4)

        # Also get relevant forward chains for side effects
        interventions = []

        llm = get_reasoning_llm(temperature=0.3)

        cause_text = ""
        if cause_chains:
            cause_text = "CAUSES OF TARGET OUTCOME:\n"
            for chain in cause_chains[:5]:
                cause_text += f"  {chain.trigger} → ... → {target_outcome} (strength: {chain.cumulative_strength:.2f})\n"

        prompt = f"""You are planning interventions to achieve a desired outcome.

TARGET OUTCOME: {target_outcome}
CURRENT STATE: {json.dumps(current_state or {}, indent=2, default=str)[:1000]}

{cause_text}

Suggest 2-3 specific interventions. For each:
1. Where in the causal chain to intervene (the leverage point)
2. What specific action to take
3. What the expected effect would be
4. Any side effects to watch for
5. How difficult it would be

Return JSON array:
[
  {{
    "intervention_point": "Where to intervene",
    "action": "What to do",
    "expected_effect": "What should happen",
    "confidence": 0.7,
    "side_effects": ["..."],
    "difficulty": "easy|medium|hard"
  }}
]"""

        try:
            response = str(llm.invoke(prompt))
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                data = json.loads(json_match.group())
                for item in data[:3]:
                    interventions.append(Intervention(
                        target_outcome=target_outcome,
                        intervention_point=item.get("intervention_point", ""),
                        action=item.get("action", ""),
                        expected_effect=item.get("expected_effect", ""),
                        confidence=item.get("confidence", 0.5),
                        side_effects=item.get("side_effects", []),
                        difficulty=item.get("difficulty", "medium"),
                    ))
        except Exception as e:
            print(f"[CausalReasoning] Intervention planning error: {e}")

        return interventions

    # ── Root Cause Analysis ──────────────────────────────────────────────────

    def root_cause_analysis(self, problem: str,
                            observations: List[str] = None) -> Dict[str, Any]:
        """
        "Karthi is unproductive. Is it sleep? Stress? Boredom?"
        Deep root cause analysis using causal graph + LLM.
        """
        # Get all known causes of this problem
        cause_chains = self.trace_causes(problem, max_depth=4)

        # Build analysis
        llm = get_reasoning_llm(temperature=0.2)

        chains_text = ""
        if cause_chains:
            chains_text = "KNOWN CAUSAL CHAINS:\n"
            for chain in cause_chains[:8]:
                path = " → ".join(f"{c}" for c, e, s in chain.chain)
                chains_text += f"  {path} → {problem} (confidence: {chain.cumulative_strength:.2f})\n"

        prompt = f"""You are performing root cause analysis like a systems engineer.

PROBLEM: {problem}
OBSERVATIONS: {json.dumps(observations or [], default=str)}

{chains_text}

Perform thorough root cause analysis:
1. List all possible root causes (from causal chains and your knowledge)
2. Rank by likelihood given the observations
3. For the top cause, explain the full causal mechanism
4. Suggest what evidence would confirm or reject each cause

Return JSON:
{{
  "root_causes": [
    {{
      "cause": "...",
      "likelihood": 0.8,
      "mechanism": "How this cause leads to the problem",
      "confirming_evidence": "What would prove this is the cause",
      "disproving_evidence": "What would prove this is NOT the cause"
    }}
  ],
  "most_likely_cause": "...",
  "recommended_investigation": "Next steps to narrow down"
}}"""

        try:
            response = str(llm.invoke(prompt))
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                self._log("root_cause_analysis", {
                    "problem": problem, "result": result,
                })

                # Learn new causal links from analysis
                for rc in result.get("root_causes", []):
                    if rc.get("likelihood", 0) > 0.6:
                        self._learn_causal_link(
                            rc.get("cause", ""), problem,
                            strength=rc.get("likelihood", 0.5)
                        )

                return result
        except Exception as e:
            print(f"[CausalReasoning] Root cause analysis error: {e}")

        return {"root_causes": [], "most_likely_cause": "Unknown",
                "recommended_investigation": "Need more data"}

    # ── Learning & Integration ───────────────────────────────────────────────

    def _learn_causal_link(self, cause: str, effect: str, strength: float):
        """Learn a new causal relationship and add it to the world model."""
        # Check if link already exists
        for link in self.world_model.causal_links:
            if (link.cause.lower() == cause.lower() and
                    link.effect.lower() == effect.lower()):
                # Reinforce existing link
                link.strength = min(1.0, link.strength + 0.05)
                link.confidence = min(1.0, link.confidence + 0.05)
                return

        # Add new link
        new_link = CausalLink(
            cause=cause,
            effect=effect,
            strength=strength,
            confidence=strength * 0.8,
            examples=[f"Discovered via causal reasoning at {datetime.now().isoformat()}"],
        )
        self.world_model.causal_links.append(new_link)
        self.world_model._save_knowledge()

    def get_causal_context(self, topic: str) -> str:
        """Get causal reasoning context for prompt injection."""
        effects = self.trace_effects(topic, max_depth=2)
        causes = self.trace_causes(topic, max_depth=2)

        parts = []
        if causes:
            parts.append(f"CAUSES of {topic}:")
            for c in causes[:3]:
                parts.append(f"  ← {c.trigger} (strength: {c.cumulative_strength:.2f})")
        if effects:
            parts.append(f"EFFECTS of {topic}:")
            for e in effects[:3]:
                parts.append(f"  → {e.terminal_effect} (strength: {e.cumulative_strength:.2f})")

        return "\n".join(parts) if parts else ""

    def _log(self, event: str, data: Dict):
        try:
            with open(CAUSAL_LOG, "a") as f:
                f.write(json.dumps({
                    "event": event, "data": data,
                    "timestamp": datetime.now().isoformat(),
                }) + "\n")
        except Exception:
            pass


# Singleton
_engine: Optional[CausalReasoningEngine] = None
_lock = threading.Lock()

def get_causal_engine() -> CausalReasoningEngine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = CausalReasoningEngine()
    return _engine
