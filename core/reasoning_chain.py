"""
LOVE Reasoning Chain — Deep Thought Architecture

Implements multi-step Chain-of-Thought reasoning with:
1. Thought Decomposition — break complex queries into atomic sub-problems
2. Evidence Gathering — pull from memory, context, tools before answering
3. Hypothesis Testing — generate multiple hypotheses, score, select best
4. Confidence Calibration — know when to say "I don't know"
5. Reasoning Trace — full audit trail of HOW a conclusion was reached

This is what separates a chatbot from an AGI — the ability to THINK,
not just pattern-match.
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.llm import get_reasoning_llm
from core.consciousness import get_consciousness
from core.execution_guard import log_error


class ReasoningStrategy(Enum):
    DIRECT = "direct"                     # Simple question, direct answer
    CHAIN_OF_THOUGHT = "chain_of_thought" # Step-by-step reasoning
    TREE_OF_THOUGHT = "tree_of_thought"   # Explore multiple branches
    SELF_CONSISTENCY = "self_consistency"  # Generate multiple answers, vote
    METACOGNITIVE = "metacognitive"       # Reason about reasoning quality


@dataclass
class ThoughtNode:
    """A single step in a reasoning chain."""
    step_number: int
    thought: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5
    alternatives_considered: List[str] = field(default_factory=list)
    selected_because: str = ""


@dataclass
class ReasoningTrace:
    """Complete trace of a reasoning process."""
    query: str
    strategy: ReasoningStrategy
    steps: List[ThoughtNode] = field(default_factory=list)
    final_answer: str = ""
    overall_confidence: float = 0.0
    reasoning_time_ms: int = 0
    uncertainty_flags: List[str] = field(default_factory=list)
    self_critique: str = ""


class ReasoningChain:
    """
    Deep reasoning engine that thinks before it speaks.
    
    Instead of: User asks → LLM answers
    It does:    User asks → Decompose → Gather evidence → Hypothesize →
                Test → Critique → Calibrate confidence → Answer
    """

    def __init__(self):
        self.consciousness = get_consciousness()

    def classify_complexity(self, query: str) -> ReasoningStrategy:
        """Determine the right reasoning strategy for a query."""
        text = query.lower()
        word_count = len(text.split())

        # Multi-part or comparative questions need chain-of-thought
        if any(w in text for w in ["compare", "versus", "trade-off", "pros and cons",
                                    "should i", "what if", "how would"]):
            return ReasoningStrategy.CHAIN_OF_THOUGHT

        # Ambiguous or high-stakes decisions need tree-of-thought
        if any(w in text for w in ["best approach", "strategy for", "plan for",
                                    "most important", "prioritize"]):
            return ReasoningStrategy.TREE_OF_THOUGHT

        # Questions about uncertain domains need self-consistency
        if any(w in text for w in ["predict", "will", "forecast", "likely",
                                    "might", "probably"]):
            return ReasoningStrategy.SELF_CONSISTENCY

        # Meta-questions about LOVE's own abilities
        if any(w in text for w in ["can you", "are you able", "do you know",
                                    "how confident", "are you sure"]):
            return ReasoningStrategy.METACOGNITIVE

        # Simple factual or conversational
        return ReasoningStrategy.DIRECT

    def reason(self, query: str, context: Dict[str, Any] = None) -> ReasoningTrace:
        """
        Execute a full reasoning chain for a query.
        Returns a complete ReasoningTrace with steps, evidence, and confidence.
        """
        start_time = time.time()
        context = context or {}
        strategy = self.classify_complexity(query)

        # Log thought to consciousness
        self.consciousness.think(f"Reasoning about: '{query[:80]}...' using {strategy.value}")

        trace = ReasoningTrace(
            query=query,
            strategy=strategy,
        )

        if strategy == ReasoningStrategy.DIRECT:
            trace = self._reason_direct(query, context, trace)
        elif strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            trace = self._reason_chain_of_thought(query, context, trace)
        elif strategy == ReasoningStrategy.TREE_OF_THOUGHT:
            trace = self._reason_tree_of_thought(query, context, trace)
        elif strategy == ReasoningStrategy.SELF_CONSISTENCY:
            trace = self._reason_self_consistency(query, context, trace)
        elif strategy == ReasoningStrategy.METACOGNITIVE:
            trace = self._reason_metacognitive(query, context, trace)

        trace.reasoning_time_ms = int((time.time() - start_time) * 1000)

        # Self-critique
        if strategy != ReasoningStrategy.DIRECT:
            trace.self_critique = self._self_critique(trace)

        return trace

    def _reason_direct(self, query: str, context: Dict, trace: ReasoningTrace) -> ReasoningTrace:
        """Simple direct reasoning — just answer."""
        trace.steps.append(ThoughtNode(
            step_number=1,
            thought="This is a straightforward query. Answering directly.",
            confidence=0.8,
        ))
        trace.overall_confidence = 0.8
        return trace

    def _reason_chain_of_thought(self, query: str, context: Dict, trace: ReasoningTrace) -> ReasoningTrace:
        """Step-by-step reasoning with evidence gathering."""
        llm = get_reasoning_llm(temperature=0.3)

        prompt = f"""You are performing deep chain-of-thought reasoning.

QUERY: {query}

CONTEXT: {json.dumps(context, indent=2, default=str)[:2000]}

Think step by step. For each step:
1. State what you're thinking about
2. What evidence supports or contradicts it
3. What alternatives you considered
4. Your confidence level (0-1)

Return JSON:
{{
  "steps": [
    {{
      "step_number": 1,
      "thought": "...",
      "evidence": ["...", "..."],
      "confidence": 0.7,
      "alternatives": ["...", "..."],
      "selected_because": "..."
    }}
  ],
  "final_answer": "...",
  "overall_confidence": 0.75,
  "uncertainty_flags": ["..."]
}}"""

        try:
            response = str(llm.invoke(prompt))
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                for step in data.get("steps", []):
                    trace.steps.append(ThoughtNode(
                        step_number=step.get("step_number", 0),
                        thought=step.get("thought", ""),
                        evidence=step.get("evidence", []),
                        confidence=step.get("confidence", 0.5),
                        alternatives_considered=step.get("alternatives", []),
                        selected_because=step.get("selected_because", ""),
                    ))
                trace.final_answer = data.get("final_answer", "")
                trace.overall_confidence = data.get("overall_confidence", 0.5)
                trace.uncertainty_flags = data.get("uncertainty_flags", [])
        except Exception as e:
            trace.steps.append(ThoughtNode(
                step_number=1,
                thought=f"Reasoning encountered an error: {str(e)}",
                confidence=0.2,
            ))
            trace.overall_confidence = 0.2

        return trace

    def _reason_tree_of_thought(self, query: str, context: Dict, trace: ReasoningTrace) -> ReasoningTrace:
        """Explore multiple reasoning branches, select the best."""
        llm = get_reasoning_llm(temperature=0.5)

        prompt = f"""You are exploring multiple reasoning paths for a complex decision.

QUERY: {query}

CONTEXT: {json.dumps(context, indent=2, default=str)[:2000]}

Generate 3 different reasoning approaches (branches).
For each branch, follow the thought to its conclusion.
Then evaluate which branch produces the best answer.

Return JSON:
{{
  "branches": [
    {{
      "approach": "Description of this reasoning approach",
      "reasoning": "Step-by-step reasoning following this approach",
      "conclusion": "What this approach concludes",
      "confidence": 0.7,
      "strengths": ["..."],
      "weaknesses": ["..."]
    }}
  ],
  "selected_branch": 0,
  "selection_reasoning": "Why this branch was selected",
  "final_answer": "...",
  "overall_confidence": 0.75
}}"""

        try:
            response = str(llm.invoke(prompt))
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                for i, branch in enumerate(data.get("branches", [])):
                    trace.steps.append(ThoughtNode(
                        step_number=i + 1,
                        thought=f"Branch {i+1}: {branch.get('approach', '')}",
                        evidence=[branch.get('reasoning', '')],
                        confidence=branch.get('confidence', 0.5),
                        alternatives_considered=branch.get('weaknesses', []),
                        selected_because=branch.get('strengths', [''])[0] if branch.get('strengths') else "",
                    ))
                trace.final_answer = data.get("final_answer", "")
                trace.overall_confidence = data.get("overall_confidence", 0.5)
        except Exception as e:
            trace.overall_confidence = 0.2

        return trace

    def _reason_self_consistency(self, query: str, context: Dict, trace: ReasoningTrace) -> ReasoningTrace:
        """Generate multiple answers and vote on the most consistent one."""
        llm = get_reasoning_llm(temperature=0.7)
        
        answers = []
        for i in range(3):
            prompt = f"""Answer this question with careful reasoning.
QUERY: {query}
CONTEXT: {json.dumps(context, indent=2, default=str)[:1500]}

Give a concise answer with your reasoning. Be honest about uncertainty."""
            try:
                response = str(llm.invoke(prompt))
                answers.append(response)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.reasoning_chain")

        if answers:
            # Use LLM to synthesize
            synthesis_prompt = f"""You generated {len(answers)} independent answers to the same question.

QUESTION: {query}

ANSWERS:
{chr(10).join(f"Answer {i+1}: {a[:500]}" for i, a in enumerate(answers))}

Synthesize the most consistent and well-supported answer.
Note any disagreements between your answers — those indicate genuine uncertainty.

Return JSON:
{{
  "synthesized_answer": "...",
  "agreement_level": 0.8,
  "disagreements": ["..."],
  "confidence": 0.75
}}"""
            try:
                import re
                synth = str(llm.invoke(synthesis_prompt))
                json_match = re.search(r'\{[\s\S]*\}', synth)
                if json_match:
                    data = json.loads(json_match.group())
                    trace.final_answer = data.get("synthesized_answer", answers[0])
                    trace.overall_confidence = data.get("confidence", 0.5)
                    trace.uncertainty_flags = data.get("disagreements", [])
            except Exception:
                trace.final_answer = answers[0] if answers else ""
                trace.overall_confidence = 0.4

        return trace

    def _reason_metacognitive(self, query: str, context: Dict, trace: ReasoningTrace) -> ReasoningTrace:
        """Reason about LOVE's own capabilities and confidence."""
        consciousness_state = self.consciousness.get_full_state()
        
        trace.steps.append(ThoughtNode(
            step_number=1,
            thought=f"Assessing my own capabilities. Maturity: {consciousness_state['identity']['maturity_level']}. "
                    f"Conversations: {consciousness_state['identity']['total_conversations']}.",
            confidence=0.9,
        ))
        
        trace.overall_confidence = 0.7
        return trace

    def _self_critique(self, trace: ReasoningTrace) -> str:
        """Critique the reasoning chain itself."""
        if trace.overall_confidence < 0.4:
            return "Low confidence — I should be transparent about my uncertainty."
        if len(trace.uncertainty_flags) > 2:
            return "Multiple uncertainty flags — this answer should be presented as tentative."
        if trace.overall_confidence > 0.9:
            return "Very high confidence — but I should remain humble. Am I overconfident?"
        return "Reasoning seems solid. Moderate confidence is appropriate."


# Singleton
_chain: Optional[ReasoningChain] = None

def get_reasoning_chain() -> ReasoningChain:
    global _chain
    if _chain is None:
        _chain = ReasoningChain()
    return _chain
