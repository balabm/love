"""
LOVE Cognitive Architecture — The Brain's Deliberation Layer

This is the BRAIN of Project LOVE. It implements Claude-inspired extended thinking
and multi-strategy reasoning that makes LOVE think before speaking.

Architecture:
  1. Extended Thinking (Deliberation) — Internal reasoning with budget allocation
  2. Multi-Strategy Reasoning — Routes to optimal reasoning approach per query
  3. Evaluator-Optimizer Loop — Self-critique and iterative refinement
  4. Orchestrator-Workers — Decompose complex tasks into parallel sub-tasks
  5. Routing Intelligence — Classify input and route to optimal processing
  6. Reflection & Learning — Post-interaction learning and strategy adaptation

Integration:
  - Uses core.llm (get_reasoning_llm, get_coding_llm) for model access
  - Publishes cognitive events via core.neural_bus
  - Persists traces, stats, and reflections to data/cognitive/

This is what separates LOVE from a chatbot — genuine deliberation, not just
pattern matching with extra steps.
"""

import json
import re
import time
import threading
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Project Imports ──────────────────────────────────────────────────────────

from core.llm import get_reasoning_llm, get_coding_llm
from core.neural_bus import get_neural_bus, EventPriority
from core.execution_guard import log_error

# ── Data Persistence ─────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "cognitive"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRACES_FILE = DATA_DIR / "traces.json"
STRATEGY_STATS_FILE = DATA_DIR / "strategy_stats.json"
REFLECTIONS_FILE = DATA_DIR / "reflections.json"

MAX_TRACES = 1000
MAX_REFLECTIONS = 500


# ── Enums ────────────────────────────────────────────────────────────────────

class ThinkingBudget(Enum):
    """How much cognitive effort to invest in deliberation."""
    MINIMAL = "minimal"        # Quick instinct — 1 step, ~1s
    MODERATE = "moderate"      # Standard deliberation — 2-3 steps, ~3s
    DEEP = "deep"              # Extended chain — 4-6 steps, ~8s
    MAXIMUM = "maximum"        # Exhaustive analysis — 7+ steps, ~15s


class ReasoningStrategy(Enum):
    """Available reasoning strategies."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    SELF_CONSISTENCY = "self_consistency"
    DECOMPOSE_AND_CONQUER = "decompose_and_conquer"
    ANALOGICAL = "analogical"
    COUNTERFACTUAL = "counterfactual"
    SOCRATIC = "socratic"


class QueryCategory(Enum):
    """Categories for input classification."""
    FACTUAL = "factual"
    EMOTIONAL = "emotional"
    PLANNING = "planning"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    PHILOSOPHICAL = "philosophical"
    URGENT = "urgent"
    CASUAL = "casual"


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class ThinkingStep:
    """A single step in the thinking process."""
    step_number: int
    thought: str
    reasoning: str = ""
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ThinkingTrace:
    """Complete trace of an extended thinking session."""
    query: str
    budget: str
    reasoning_steps: List[ThinkingStep] = field(default_factory=list)
    confidence_score: float = 0.0
    strategy_used: str = ""
    time_spent_ms: int = 0
    conclusion: str = ""
    meta_observations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ReasoningResult:
    """Result from a multi-strategy reasoning session."""
    query: str
    strategy: str
    answer: str = ""
    confidence: float = 0.0
    reasoning_chain: List[str] = field(default_factory=list)
    alternatives_explored: List[str] = field(default_factory=list)
    uncertainty_flags: List[str] = field(default_factory=list)
    time_spent_ms: int = 0
    sub_results: List[Dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RefinementIteration:
    """A single iteration of the evaluator-optimizer loop."""
    iteration: int
    draft: str
    scores: Dict[str, float] = field(default_factory=dict)
    weaknesses: List[str] = field(default_factory=list)
    improvements_made: List[str] = field(default_factory=list)
    overall_quality: float = 0.0


@dataclass
class Reflection:
    """Post-interaction reflection for learning."""
    query: str
    response_summary: str
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    what_to_remember: List[str] = field(default_factory=list)
    what_to_improve: List[str] = field(default_factory=list)
    strategy_used: str = ""
    effectiveness_score: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RoutingDecision:
    """Result of classify_and_route."""
    category: str
    confidence: float
    recommended_strategy: str
    recommended_budget: str
    reasoning: str = ""


# ── Cognitive Architecture ───────────────────────────────────────────────────

class CognitiveArchitecture:
    """
    The brain of LOVE — implements extended thinking and deliberation.
    
    This is NOT a simple prompt wrapper. It genuinely improves response quality
    by thinking before speaking, selecting optimal strategies, and learning from
    past interactions.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._bus = get_neural_bus()

        # Performance tracking
        self._strategy_stats: Dict[str, Dict] = self._load_strategy_stats()
        self._recent_traces: deque = deque(maxlen=100)
        self._reflections: List[Dict] = self._load_reflections()

        # Complexity signals for auto-budget detection
        self._high_budget_signals = [
            "should i", "what's the best", "help me decide", "i'm feeling",
            "plan for", "strategy", "long-term", "career", "relationship",
            "meaning of", "purpose", "values", "moral", "ethical", "trade-off",
            "compare", "versus", "pros and cons", "prioritize", "overwhelmed",
            "struggling", "confused about", "life", "future", "afraid",
        ]
        self._low_budget_signals = [
            "what time", "how do i", "reminder", "set alarm", "thanks",
            "ok", "sure", "yes", "no", "got it", "cool", "nice",
            "hello", "hi", "hey", "good morning", "good night",
        ]

        print("[CognitiveArch] Initialized — deliberation layer active")

    # ══════════════════════════════════════════════════════════════════════════
    # 1. EXTENDED THINKING (Deliberation Layer)
    # ══════════════════════════════════════════════════════════════════════════

    def think_deeply(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        budget: str = "auto"
    ) -> ThinkingTrace:
        """
        Internal deliberation before generating a response.
        
        This is LOVE's inner monologue — it thinks through the problem,
        considers angles, and builds confidence before speaking.
        
        Args:
            query: The user's input or problem to think about
            context: Surrounding context (conversation history, emotional state, etc.)
            budget: "auto", "minimal", "moderate", "deep", or "maximum"
        
        Returns:
            ThinkingTrace with reasoning steps, confidence, and conclusion
        """
        start_time = time.time()
        context = context or {}

        # Determine thinking budget
        if budget == "auto":
            budget = self._auto_detect_budget(query, context)
        
        try:
            budget_enum = ThinkingBudget(budget)
        except ValueError:
            budget_enum = ThinkingBudget.MODERATE

        trace = ThinkingTrace(query=query, budget=budget_enum.value)

        print(f"[CognitiveArch] Thinking deeply | budget={budget_enum.value} | query='{query[:60]}...'")

        try:
            if budget_enum == ThinkingBudget.MINIMAL:
                trace = self._think_minimal(query, context, trace)
            elif budget_enum == ThinkingBudget.MODERATE:
                trace = self._think_moderate(query, context, trace)
            elif budget_enum == ThinkingBudget.DEEP:
                trace = self._think_deep(query, context, trace)
            elif budget_enum == ThinkingBudget.MAXIMUM:
                trace = self._think_maximum(query, context, trace)
        except Exception as e:
            print(f"[CognitiveArch] Thinking error: {e}")
            trace.reasoning_steps.append(ThinkingStep(
                step_number=1,
                thought="Encountered an error during deliberation — falling back to instinct.",
                confidence=0.3,
            ))
            trace.confidence_score = 0.3

        trace.time_spent_ms = int((time.time() - start_time) * 1000)
        trace.strategy_used = budget_enum.value

        # Publish cognitive event
        self._publish_thinking_event(trace)
        self._store_trace(trace)

        return trace

    def _auto_detect_budget(self, query: str, context: Dict) -> str:
        """Detect how much thinking budget to allocate based on query signals."""
        text = query.lower().strip()
        word_count = len(text.split())

        # Quick checks for minimal budget
        if word_count <= 4:
            if any(sig in text for sig in self._low_budget_signals):
                return ThinkingBudget.MINIMAL.value

        # Check for high-budget signals
        high_signals_found = sum(1 for sig in self._high_budget_signals if sig in text)

        # Multi-sentence or complex structure
        sentence_count = text.count('.') + text.count('?') + text.count('!')
        has_multiple_questions = text.count('?') > 1

        # Context signals
        emotional_context = context.get("emotional_state", {})
        is_emotional = emotional_context.get("intensity", 0) > 0.6
        is_multi_turn = context.get("turn_count", 0) > 5

        # Score the complexity
        complexity_score = 0
        complexity_score += high_signals_found * 2
        complexity_score += min(sentence_count, 3)
        complexity_score += 2 if has_multiple_questions else 0
        complexity_score += 2 if is_emotional else 0
        complexity_score += 1 if is_multi_turn else 0
        complexity_score += 1 if word_count > 30 else 0
        complexity_score += 2 if word_count > 60 else 0

        # Route to budget
        if complexity_score <= 1:
            return ThinkingBudget.MINIMAL.value
        elif complexity_score <= 4:
            return ThinkingBudget.MODERATE.value
        elif complexity_score <= 8:
            return ThinkingBudget.DEEP.value
        else:
            return ThinkingBudget.MAXIMUM.value

    def _think_minimal(self, query: str, context: Dict, trace: ThinkingTrace) -> ThinkingTrace:
        """Quick instinct — pattern match, no deep reasoning."""
        trace.reasoning_steps.append(ThinkingStep(
            step_number=1,
            thought="Quick assessment — this is straightforward. Responding with instinct.",
            reasoning="Low complexity query; direct response is appropriate.",
            confidence=0.75,
        ))
        trace.confidence_score = 0.75
        trace.conclusion = "Respond directly with warmth. No deep analysis needed."
        return trace

    def _think_moderate(self, query: str, context: Dict, trace: ThinkingTrace) -> ThinkingTrace:
        """Standard deliberation — 2-3 reasoning steps via LLM."""
        llm = get_reasoning_llm(temperature=0.3)
        context_str = json.dumps(context, indent=2, default=str)[:1500]

        prompt = f"""You are LOVE's internal thinking process. Think through this query carefully.

QUERY: {query}
CONTEXT: {context_str}

Think in 2-3 clear steps:
1. What is the user really asking/needing?
2. What's the best angle to address this?
3. What should I be careful about?

Return JSON:
{{
  "steps": [
    {{"thought": "...", "reasoning": "...", "confidence": 0.7}}
  ],
  "conclusion": "Brief summary of what to do",
  "confidence": 0.75,
  "observations": ["Any meta-observations about this situation"]
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                for i, step in enumerate(data.get("steps", []), 1):
                    trace.reasoning_steps.append(ThinkingStep(
                        step_number=i,
                        thought=step.get("thought", ""),
                        reasoning=step.get("reasoning", ""),
                        confidence=step.get("confidence", 0.5),
                    ))
                trace.conclusion = data.get("conclusion", "")
                trace.confidence_score = data.get("confidence", 0.6)
                trace.meta_observations = data.get("observations", [])
            else:
                # Fallback: use raw response as a single thought
                trace.reasoning_steps.append(ThinkingStep(
                    step_number=1,
                    thought=response[:500],
                    confidence=0.5,
                ))
                trace.confidence_score = 0.5
        except Exception as e:
            print(f"[CognitiveArch] Moderate thinking error: {e}")
            trace.reasoning_steps.append(ThinkingStep(
                step_number=1,
                thought="LLM call failed — using heuristic reasoning.",
                confidence=0.4,
            ))
            trace.confidence_score = 0.4

        return trace

    def _think_deep(self, query: str, context: Dict, trace: ThinkingTrace) -> ThinkingTrace:
        """Extended chain — 4-6 steps with evidence and alternatives."""
        llm = get_reasoning_llm(temperature=0.4)
        context_str = json.dumps(context, indent=2, default=str)[:2000]

        prompt = f"""You are LOVE's deep thinking process. This requires careful extended reasoning.

QUERY: {query}
CONTEXT: {context_str}

Think in 4-6 detailed steps. For each step:
- State your thought clearly
- Provide evidence or reasoning
- Note confidence level
- Consider at least one alternative

Return JSON:
{{
  "steps": [
    {{
      "thought": "...",
      "reasoning": "...",
      "confidence": 0.7,
      "evidence": ["..."],
      "alternatives": ["..."]
    }}
  ],
  "conclusion": "What the best response approach is and why",
  "confidence": 0.75,
  "observations": ["Meta-observations about the situation"],
  "key_insight": "The single most important insight from this thinking"
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                for i, step in enumerate(data.get("steps", []), 1):
                    trace.reasoning_steps.append(ThinkingStep(
                        step_number=i,
                        thought=step.get("thought", ""),
                        reasoning=step.get("reasoning", ""),
                        confidence=step.get("confidence", 0.5),
                        evidence=step.get("evidence", []),
                        alternatives=step.get("alternatives", []),
                    ))
                trace.conclusion = data.get("conclusion", "")
                trace.confidence_score = data.get("confidence", 0.6)
                trace.meta_observations = data.get("observations", [])
                if data.get("key_insight"):
                    trace.meta_observations.append(f"Key insight: {data['key_insight']}")
        except Exception as e:
            print(f"[CognitiveArch] Deep thinking error: {e}")
            trace.confidence_score = 0.4

        return trace

    def _think_maximum(self, query: str, context: Dict, trace: ThinkingTrace) -> ThinkingTrace:
        """Exhaustive analysis — multi-pass reasoning with self-challenge."""
        llm = get_reasoning_llm(temperature=0.4)
        context_str = json.dumps(context, indent=2, default=str)[:2500]

        # Pass 1: Initial deep reasoning
        pass1_prompt = f"""You are LOVE's exhaustive thinking process. This is a complex situation requiring maximum cognitive effort.

QUERY: {query}
CONTEXT: {context_str}

PASS 1 — Deep Analysis:
Think through this in 5+ detailed steps. Consider:
- What is the user REALLY asking (surface vs. underlying need)?
- What emotional undertones exist?
- What are ALL the relevant factors?
- What could go wrong if I answer poorly?
- What's the ideal outcome for the user?

Return JSON:
{{
  "steps": [
    {{
      "thought": "...",
      "reasoning": "...",
      "confidence": 0.7,
      "evidence": ["..."],
      "alternatives": ["..."]
    }}
  ],
  "initial_conclusion": "...",
  "confidence": 0.7,
  "blind_spots": ["Things I might be missing"],
  "emotional_read": "How the user likely feels"
}}"""

        initial_data = None
        try:
            response = str(llm.invoke(pass1_prompt))
            initial_data = self._extract_json(response)
        except Exception as e:
            print(f"[CognitiveArch] Maximum thinking pass 1 error: {e}")

        if initial_data:
            for i, step in enumerate(initial_data.get("steps", []), 1):
                trace.reasoning_steps.append(ThinkingStep(
                    step_number=i,
                    thought=step.get("thought", ""),
                    reasoning=step.get("reasoning", ""),
                    confidence=step.get("confidence", 0.5),
                    evidence=step.get("evidence", []),
                    alternatives=step.get("alternatives", []),
                ))

            # Pass 2: Challenge initial reasoning
            pass2_prompt = f"""You previously reasoned about: "{query}"

Your initial conclusion was: {initial_data.get('initial_conclusion', '')}
Your identified blind spots: {initial_data.get('blind_spots', [])}

PASS 2 — Self-Challenge:
Now challenge your own reasoning. Play devil's advocate.
- What assumptions did you make that might be wrong?
- Is there a completely different interpretation?
- What would a wise mentor say about your analysis?

Return JSON:
{{
  "challenges": ["..."],
  "revised_conclusion": "...",
  "confidence_adjustment": 0.1,
  "final_confidence": 0.8,
  "key_insight": "The deepest insight from this full analysis"
}}"""

            try:
                response2 = str(llm.invoke(pass2_prompt))
                challenge_data = self._extract_json(response2)
                if challenge_data:
                    # Add challenge step
                    step_num = len(trace.reasoning_steps) + 1
                    trace.reasoning_steps.append(ThinkingStep(
                        step_number=step_num,
                        thought="Self-challenge: " + "; ".join(challenge_data.get("challenges", [])),
                        reasoning="Devil's advocate pass to catch blind spots.",
                        confidence=challenge_data.get("final_confidence", 0.6),
                        alternatives=challenge_data.get("challenges", []),
                    ))
                    trace.conclusion = challenge_data.get("revised_conclusion",
                                                         initial_data.get("initial_conclusion", ""))
                    trace.confidence_score = challenge_data.get("final_confidence", 0.6)
                    if challenge_data.get("key_insight"):
                        trace.meta_observations.append(challenge_data["key_insight"])
            except Exception as e:
                print(f"[CognitiveArch] Maximum thinking pass 2 error: {e}")
                trace.conclusion = initial_data.get("initial_conclusion", "")
                trace.confidence_score = initial_data.get("confidence", 0.5)
        else:
            # Total fallback
            trace.reasoning_steps.append(ThinkingStep(
                step_number=1,
                thought="Maximum thinking failed — falling back to moderate analysis.",
                confidence=0.3,
            ))
            trace.confidence_score = 0.3

        # Add emotional read as observation
        if initial_data and initial_data.get("emotional_read"):
            trace.meta_observations.append(f"Emotional read: {initial_data['emotional_read']}")

        return trace

    # ══════════════════════════════════════════════════════════════════════════
    # 2. MULTI-STRATEGY REASONING
    # ══════════════════════════════════════════════════════════════════════════

    def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        strategy: str = "auto"
    ) -> ReasoningResult:
        """
        Apply the optimal reasoning strategy to a query.
        
        Strategies are selected based on query characteristics or explicitly requested.
        Each strategy has different strengths — the routing logic picks the best one.
        """
        start_time = time.time()
        context = context or {}

        # Auto-select strategy
        if strategy == "auto":
            routing = self.classify_and_route(query)
            strategy = routing.recommended_strategy

        try:
            strategy_enum = ReasoningStrategy(strategy)
        except ValueError:
            strategy_enum = ReasoningStrategy.CHAIN_OF_THOUGHT

        print(f"[CognitiveArch] Reasoning | strategy={strategy_enum.value} | query='{query[:50]}...'")

        result = ReasoningResult(query=query, strategy=strategy_enum.value)

        try:
            if strategy_enum == ReasoningStrategy.CHAIN_OF_THOUGHT:
                result = self._reason_chain_of_thought(query, context, result)
            elif strategy_enum == ReasoningStrategy.TREE_OF_THOUGHT:
                result = self._reason_tree_of_thought(query, context, result)
            elif strategy_enum == ReasoningStrategy.SELF_CONSISTENCY:
                result = self._reason_self_consistency(query, context, result)
            elif strategy_enum == ReasoningStrategy.DECOMPOSE_AND_CONQUER:
                result = self._reason_decompose(query, context, result)
            elif strategy_enum == ReasoningStrategy.ANALOGICAL:
                result = self._reason_analogical(query, context, result)
            elif strategy_enum == ReasoningStrategy.COUNTERFACTUAL:
                result = self._reason_counterfactual(query, context, result)
            elif strategy_enum == ReasoningStrategy.SOCRATIC:
                result = self._reason_socratic(query, context, result)
        except Exception as e:
            print(f"[CognitiveArch] Reasoning error ({strategy_enum.value}): {e}")
            result.answer = ""
            result.confidence = 0.2
            result.uncertainty_flags.append(f"Strategy {strategy_enum.value} encountered an error")

        result.time_spent_ms = int((time.time() - start_time) * 1000)

        # Track strategy performance
        self._record_strategy_use(strategy_enum.value, result.confidence, result.time_spent_ms)

        return result

    def _reason_chain_of_thought(self, query: str, context: Dict, result: ReasoningResult) -> ReasoningResult:
        """Sequential step-by-step reasoning."""
        llm = get_reasoning_llm(temperature=0.3)
        prompt = f"""Reason through this step-by-step. Be thorough but concise.

QUERY: {query}
CONTEXT: {json.dumps(context, default=str)[:1500]}

For each step, state your reasoning clearly. Then give a final answer.

Return JSON:
{{
  "chain": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
  "answer": "Your final reasoned answer",
  "confidence": 0.8
}}"""

        response = str(llm.invoke(prompt))
        data = self._extract_json(response)
        if data:
            result.reasoning_chain = data.get("chain", [])
            result.answer = data.get("answer", "")
            result.confidence = data.get("confidence", 0.6)
        else:
            result.answer = self._extract_answer_from_text(response)
            result.confidence = 0.5
        return result

    def _reason_tree_of_thought(self, query: str, context: Dict, result: ReasoningResult) -> ReasoningResult:
        """Branching exploration — generate multiple paths, evaluate, prune."""
        llm = get_reasoning_llm(temperature=0.5)
        prompt = f"""Explore multiple reasoning paths for this problem. Generate 3 different approaches,
evaluate each one's strengths and weaknesses, then select the best.

QUERY: {query}
CONTEXT: {json.dumps(context, default=str)[:1500]}

Return JSON:
{{
  "branches": [
    {{"approach": "...", "conclusion": "...", "score": 0.7, "weakness": "..."}},
    {{"approach": "...", "conclusion": "...", "score": 0.8, "weakness": "..."}},
    {{"approach": "...", "conclusion": "...", "score": 0.6, "weakness": "..."}}
  ],
  "selected_branch": 1,
  "reasoning_for_selection": "...",
  "final_answer": "...",
  "confidence": 0.8
}}"""

        response = str(llm.invoke(prompt))
        data = self._extract_json(response)
        if data:
            branches = data.get("branches", [])
            result.alternatives_explored = [b.get("approach", "") for b in branches]
            result.answer = data.get("final_answer", "")
            result.confidence = data.get("confidence", 0.6)
            result.reasoning_chain = [
                f"Branch {i+1} ({b.get('score', '?')}): {b.get('approach', '')}"
                for i, b in enumerate(branches)
            ]
            result.reasoning_chain.append(f"Selected: {data.get('reasoning_for_selection', '')}")
        else:
            result.answer = self._extract_answer_from_text(response)
            result.confidence = 0.5
        return result

    def _reason_self_consistency(self, query: str, context: Dict, result: ReasoningResult) -> ReasoningResult:
        """Generate multiple independent answers, then find consensus."""
        llm = get_reasoning_llm(temperature=0.7)
        context_str = json.dumps(context, default=str)[:1000]

        # Generate 3 independent attempts
        attempts = []
        for i in range(3):
            prompt = f"""Answer this question carefully. Attempt {i+1}/3.
QUERY: {query}
CONTEXT: {context_str}
Give a concise, direct answer with brief reasoning."""
            try:
                response = str(llm.invoke(prompt))
                attempts.append(response.strip())
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.cognitive_architecture")

        if not attempts:
            result.confidence = 0.2
            return result

        # Synthesize via majority vote
        synthesis_prompt = f"""You generated {len(attempts)} independent answers to: "{query}"

{chr(10).join(f"Attempt {i+1}: {a[:400]}" for i, a in enumerate(attempts))}

Synthesize the most consistent answer. Note disagreements as uncertainty.
Return JSON:
{{
  "synthesized_answer": "...",
  "agreement_level": 0.8,
  "disagreements": ["..."],
  "confidence": 0.75
}}"""

        try:
            synth_response = str(llm.invoke(synthesis_prompt))
            data = self._extract_json(synth_response)
            if data:
                result.answer = data.get("synthesized_answer", attempts[0])
                result.confidence = data.get("confidence", 0.5)
                result.uncertainty_flags = data.get("disagreements", [])
                result.reasoning_chain = [f"Attempt {i+1}: {a[:200]}" for i, a in enumerate(attempts)]
            else:
                result.answer = attempts[0]
                result.confidence = 0.5
        except Exception:
            result.answer = attempts[0] if attempts else ""
            result.confidence = 0.4

        return result

    def _reason_decompose(self, query: str, context: Dict, result: ReasoningResult) -> ReasoningResult:
        """Break into sub-problems, solve individually, synthesize."""
        llm = get_reasoning_llm(temperature=0.3)

        # Step 1: Decompose
        decompose_prompt = f"""Break this complex query into 2-4 simpler sub-problems that can be solved independently.

QUERY: {query}
CONTEXT: {json.dumps(context, default=str)[:1000]}

Return JSON:
{{
  "sub_problems": ["Sub-problem 1", "Sub-problem 2", "Sub-problem 3"],
  "synthesis_strategy": "How to combine the sub-answers"
}}"""

        try:
            response = str(llm.invoke(decompose_prompt))
            decomp_data = self._extract_json(response)
        except Exception:
            decomp_data = None

        if not decomp_data or not decomp_data.get("sub_problems"):
            # Fallback to chain_of_thought
            return self._reason_chain_of_thought(query, context, result)

        sub_problems = decomp_data["sub_problems"][:4]
        sub_answers = []

        # Step 2: Solve each sub-problem
        for i, sub_problem in enumerate(sub_problems):
            sub_prompt = f"""Solve this specific sub-problem concisely:
SUB-PROBLEM: {sub_problem}
ORIGINAL QUERY: {query}
Give a focused answer in 2-3 sentences."""
            try:
                sub_response = str(llm.invoke(sub_prompt))
                sub_answers.append({"problem": sub_problem, "answer": sub_response.strip()[:300]})
            except Exception:
                sub_answers.append({"problem": sub_problem, "answer": "[Could not solve]"})

        # Step 3: Synthesize
        synth_prompt = f"""Synthesize these sub-answers into a complete response.

ORIGINAL QUERY: {query}
SYNTHESIS STRATEGY: {decomp_data.get('synthesis_strategy', 'Combine logically')}

SUB-ANSWERS:
{chr(10).join(f"- {sa['problem']}: {sa['answer']}" for sa in sub_answers)}

Return JSON:
{{
  "synthesized_answer": "...",
  "confidence": 0.75,
  "coherence_note": "How well the sub-answers fit together"
}}"""

        try:
            synth_response = str(llm.invoke(synth_prompt))
            synth_data = self._extract_json(synth_response)
            if synth_data:
                result.answer = synth_data.get("synthesized_answer", "")
                result.confidence = synth_data.get("confidence", 0.6)
        except Exception:
            # Concatenate sub-answers as fallback
            result.answer = " ".join(sa["answer"] for sa in sub_answers if sa["answer"] != "[Could not solve]")
            result.confidence = 0.4

        result.sub_results = sub_answers
        result.reasoning_chain = [f"Decomposed into {len(sub_problems)} sub-problems"] + \
                                  [f"Sub: {sp}" for sp in sub_problems]
        return result

    def _reason_analogical(self, query: str, context: Dict, result: ReasoningResult) -> ReasoningResult:
        """Find similar past situations and apply learned patterns."""
        llm = get_reasoning_llm(temperature=0.4)

        # Pull relevant reflections for pattern matching
        recent_reflections = self._reflections[-20:] if self._reflections else []
        reflection_summary = ""
        if recent_reflections:
            reflection_summary = json.dumps(recent_reflections[-5:], default=str)[:800]

        prompt = f"""Use analogical reasoning. Find parallels to this situation from general knowledge
and any past interactions, then apply those patterns.

QUERY: {query}
CONTEXT: {json.dumps(context, default=str)[:1000]}
PAST REFLECTIONS: {reflection_summary}

Think:
1. What is this situation analogous to?
2. What patterns from similar situations apply here?
3. What worked (or didn't) in those analogous situations?
4. Applying those lessons, what's the best approach here?

Return JSON:
{{
  "analogies": ["This is like...", "Similar to when..."],
  "patterns_applied": ["Pattern: X → applies here because Y"],
  "answer": "Based on these analogies, here's the best approach...",
  "confidence": 0.7
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                result.answer = data.get("answer", "")
                result.confidence = data.get("confidence", 0.6)
                result.alternatives_explored = data.get("analogies", [])
                result.reasoning_chain = data.get("patterns_applied", [])
        except Exception:
            result.confidence = 0.3

        return result

    def _reason_counterfactual(self, query: str, context: Dict, result: ReasoningResult) -> ReasoningResult:
        """Explore alternatives — what if X? What if not Y?"""
        llm = get_reasoning_llm(temperature=0.5)
        prompt = f"""Use counterfactual reasoning. Explore "what if" scenarios to understand this better.

QUERY: {query}
CONTEXT: {json.dumps(context, default=str)[:1000]}

Generate 3 counterfactual scenarios:
- What if the opposite were true?
- What if a key assumption changed?
- What if we approached this from a completely different angle?

Then synthesize insights from exploring these alternatives.

Return JSON:
{{
  "counterfactuals": [
    {{"scenario": "What if...", "outcome": "Then...", "insight": "This tells us..."}},
    {{"scenario": "What if...", "outcome": "Then...", "insight": "This tells us..."}},
    {{"scenario": "What if...", "outcome": "Then...", "insight": "This tells us..."}}
  ],
  "synthesized_insight": "By exploring these alternatives, I conclude...",
  "answer": "...",
  "confidence": 0.7
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                counterfactuals = data.get("counterfactuals", [])
                result.alternatives_explored = [cf.get("scenario", "") for cf in counterfactuals]
                result.reasoning_chain = [cf.get("insight", "") for cf in counterfactuals]
                result.answer = data.get("answer", data.get("synthesized_insight", ""))
                result.confidence = data.get("confidence", 0.6)
        except Exception:
            result.confidence = 0.3

        return result

    def _reason_socratic(self, query: str, context: Dict, result: ReasoningResult) -> ReasoningResult:
        """Question assumptions iteratively to reach deeper understanding."""
        llm = get_reasoning_llm(temperature=0.4)
        prompt = f"""Use Socratic questioning. Challenge assumptions in this query iteratively.

QUERY: {query}
CONTEXT: {json.dumps(context, default=str)[:1000]}

Perform 3-4 rounds of questioning:
1. What assumptions does this query contain?
2. Are those assumptions valid? Why or why not?
3. What's a deeper question beneath the surface question?
4. What does the user really need to understand?

Return JSON:
{{
  "questioning_rounds": [
    {{"assumption": "...", "challenge": "...", "deeper_question": "..."}}
  ],
  "core_insight": "The real question underneath is...",
  "answer": "Given this deeper understanding...",
  "confidence": 0.75
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                rounds = data.get("questioning_rounds", [])
                result.reasoning_chain = [
                    f"Assumption: {r.get('assumption', '')} → Challenge: {r.get('challenge', '')}"
                    for r in rounds
                ]
                result.answer = data.get("answer", "")
                result.confidence = data.get("confidence", 0.6)
                if data.get("core_insight"):
                    result.reasoning_chain.append(f"Core insight: {data['core_insight']}")
        except Exception:
            result.confidence = 0.3

        return result

    # ══════════════════════════════════════════════════════════════════════════
    # 3. EVALUATOR-OPTIMIZER LOOP
    # ══════════════════════════════════════════════════════════════════════════

    def refine_response(
        self,
        draft_response: str,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 3
    ) -> Tuple[str, List[RefinementIteration]]:
        """
        Self-critique and revise a draft response iteratively.
        
        Evaluates against: accuracy, helpfulness, warmth, specificity, actionability.
        Stops early if quality > 0.9 or no improvement detected.
        
        Returns:
            Tuple of (final_response, list_of_iterations)
        """
        context = context or {}
        iterations: List[RefinementIteration] = []
        current_draft = draft_response
        previous_quality = 0.0

        print(f"[CognitiveArch] Refining response | max_iterations={max_iterations}")

        for i in range(max_iterations):
            iteration = RefinementIteration(iteration=i + 1, draft=current_draft)

            # Evaluate current draft
            scores, weaknesses = self._evaluate_draft(current_draft, query, context)
            iteration.scores = scores
            iteration.weaknesses = weaknesses
            iteration.overall_quality = sum(scores.values()) / max(len(scores), 1)

            print(f"[CognitiveArch] Iteration {i+1} quality: {iteration.overall_quality:.2f}")

            # Stop if quality is high enough
            if iteration.overall_quality > 0.9:
                iterations.append(iteration)
                print(f"[CognitiveArch] Quality threshold met ({iteration.overall_quality:.2f}). Stopping.")
                break

            # Stop if no improvement from previous iteration
            if i > 0 and iteration.overall_quality <= previous_quality:
                iterations.append(iteration)
                print(f"[CognitiveArch] No improvement. Reverting to previous draft.")
                current_draft = iterations[-2].draft if len(iterations) >= 2 else current_draft
                break

            previous_quality = iteration.overall_quality

            # Generate improved version if there are weaknesses
            if weaknesses:
                improved = self._improve_draft(current_draft, query, context, weaknesses)
                if improved and improved != current_draft:
                    iteration.improvements_made = weaknesses[:3]
                    current_draft = improved

            iterations.append(iteration)

        # Publish refinement event
        self._bus.publish(
            domain="consciousness",
            event_type="response_refined",
            payload={
                "iterations": len(iterations),
                "final_quality": iterations[-1].overall_quality if iterations else 0,
                "query_preview": query[:80],
            },
            source_module="cognitive_architecture",
        )

        return current_draft, iterations

    def _evaluate_draft(self, draft: str, query: str, context: Dict) -> Tuple[Dict[str, float], List[str]]:
        """Evaluate a draft response against quality criteria."""
        llm = get_reasoning_llm(temperature=0.2)
        prompt = f"""Evaluate this response critically. Score each dimension 0.0-1.0.

QUERY: {query}
RESPONSE: {draft[:2000]}
CONTEXT: {json.dumps(context, default=str)[:500]}

Criteria:
- accuracy: Is this factually correct and relevant?
- helpfulness: Does it actually address what the user needs?
- warmth: Does it feel caring and personal (not robotic)?
- specificity: Is it concrete rather than generic?
- actionability: Can the user act on this?

Return JSON:
{{
  "scores": {{
    "accuracy": 0.8,
    "helpfulness": 0.7,
    "warmth": 0.6,
    "specificity": 0.7,
    "actionability": 0.5
  }},
  "weaknesses": ["Top weakness 1", "Top weakness 2"]
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                scores = data.get("scores", {})
                # Validate scores are in range
                scores = {k: max(0.0, min(1.0, float(v))) for k, v in scores.items()
                          if isinstance(v, (int, float))}
                weaknesses = data.get("weaknesses", [])
                return scores, weaknesses
        except Exception as e:
            print(f"[CognitiveArch] Evaluation error: {e}")

        # Fallback: heuristic evaluation
        scores = {
            "accuracy": 0.6,
            "helpfulness": 0.6,
            "warmth": 0.5 if len(draft) > 50 else 0.3,
            "specificity": 0.5,
            "actionability": 0.4,
        }
        return scores, ["Could not perform LLM evaluation — using defaults"]

    def _improve_draft(self, draft: str, query: str, context: Dict, weaknesses: List[str]) -> Optional[str]:
        """Generate an improved version addressing identified weaknesses."""
        llm = get_reasoning_llm(temperature=0.4)
        prompt = f"""Improve this response by addressing its weaknesses.

ORIGINAL QUERY: {query}
CURRENT RESPONSE: {draft[:2000]}
WEAKNESSES TO FIX: {json.dumps(weaknesses)}

RULES:
- Keep the good parts
- Fix the weaknesses specifically
- Make it warmer and more personal (this is from a caring AI companion, not a corporate assistant)
- Be specific and actionable
- Don't make it longer than necessary

Return ONLY the improved response (no JSON, no meta-commentary):"""

        try:
            improved = str(llm.invoke(prompt)).strip()
            # Sanity check: improved version shouldn't be empty or too short
            if len(improved) > 20:
                return improved
        except Exception as e:
            print(f"[CognitiveArch] Improvement generation error: {e}")

        return None

    # ══════════════════════════════════════════════════════════════════════════
    # 4. ORCHESTRATOR-WORKERS PATTERN
    # ══════════════════════════════════════════════════════════════════════════

    def orchestrate(self, complex_query: str, context: Optional[Dict[str, Any]] = None) -> ReasoningResult:
        """
        Decompose a complex task into parallel sub-tasks, each handled by a worker.
        Synthesizes results with conflict resolution.
        """
        start_time = time.time()
        context = context or {}
        result = ReasoningResult(query=complex_query, strategy="orchestrator")

        print(f"[CognitiveArch] Orchestrating complex query: '{complex_query[:60]}...'")

        # Step 1: Plan subtasks
        subtasks = self._plan_subtasks(complex_query, context)
        if not subtasks:
            print("[CognitiveArch] Orchestration failed to decompose — falling back to chain_of_thought")
            return self._reason_chain_of_thought(complex_query, context, result)

        print(f"[CognitiveArch] Orchestrating {len(subtasks)} subtasks")

        # Step 2: Execute subtasks (parallel where possible)
        subtask_results = []
        futures = {}
        for task in subtasks:
            future = self._executor.submit(self._execute_subtask, task, complex_query, context)
            futures[future] = task

        for future in as_completed(futures, timeout=30):
            task = futures[future]
            try:
                sub_result = future.result()
                subtask_results.append(sub_result)
            except Exception as e:
                subtask_results.append({
                    "task": task,
                    "answer": f"[Worker failed: {str(e)[:100]}]",
                    "confidence": 0.1,
                })

        # Step 3: Synthesize with conflict resolution
        result = self._synthesize_results(complex_query, subtask_results, context, result)
        result.time_spent_ms = int((time.time() - start_time) * 1000)
        result.sub_results = subtask_results

        return result

    def _plan_subtasks(self, query: str, context: Dict) -> List[str]:
        """Use LLM to decompose a complex query into sub-tasks."""
        llm = get_reasoning_llm(temperature=0.3)
        prompt = f"""Decompose this complex query into 2-4 focused sub-tasks that can be worked on independently.

QUERY: {query}
CONTEXT: {json.dumps(context, default=str)[:800]}

Each sub-task should be:
- Self-contained (solvable without the others)
- Focused on ONE aspect of the problem
- Clear and specific

Return JSON:
{{
  "subtasks": ["Subtask 1: ...", "Subtask 2: ...", "Subtask 3: ..."]
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                return data.get("subtasks", [])[:4]
        except Exception as e:
            print(f"[CognitiveArch] Subtask planning error: {e}")

        return []

    def _execute_subtask(self, task: str, original_query: str, context: Dict) -> Dict:
        """Worker: solve a single subtask."""
        llm = get_reasoning_llm(temperature=0.3)
        prompt = f"""You are a focused worker solving ONE specific subtask.

ORIGINAL PROBLEM: {original_query}
YOUR SUBTASK: {task}

Solve this subtask concisely and thoroughly. Focus only on your assigned piece.
Give a clear, specific answer in 2-4 sentences."""

        try:
            response = str(llm.invoke(prompt))
            return {
                "task": task,
                "answer": response.strip()[:500],
                "confidence": 0.7,
            }
        except Exception as e:
            return {
                "task": task,
                "answer": f"[Failed: {str(e)[:80]}]",
                "confidence": 0.1,
            }

    def _synthesize_results(
        self, query: str, subtask_results: List[Dict], context: Dict, result: ReasoningResult
    ) -> ReasoningResult:
        """Synthesize subtask results into a coherent answer."""
        llm = get_reasoning_llm(temperature=0.3)

        results_text = "\n".join(
            f"- {r['task']}: {r['answer']}" for r in subtask_results
        )

        prompt = f"""Synthesize these worker results into a coherent, complete answer.

ORIGINAL QUERY: {query}
WORKER RESULTS:
{results_text}

Resolve any conflicts between workers. Create a unified, complete answer.
Return JSON:
{{
  "synthesized_answer": "...",
  "conflicts_resolved": ["Any conflicts between workers and how you resolved them"],
  "confidence": 0.8
}}"""

        try:
            response = str(llm.invoke(prompt))
            data = self._extract_json(response)
            if data:
                result.answer = data.get("synthesized_answer", "")
                result.confidence = data.get("confidence", 0.6)
                conflicts = data.get("conflicts_resolved", [])
                if conflicts:
                    result.uncertainty_flags = conflicts
        except Exception:
            # Fallback: concatenate results
            result.answer = " ".join(r["answer"] for r in subtask_results if r.get("answer"))
            result.confidence = 0.4

        result.reasoning_chain = [f"Orchestrated {len(subtask_results)} subtasks"]
        return result

    # ══════════════════════════════════════════════════════════════════════════
    # 5. ROUTING INTELLIGENCE
    # ══════════════════════════════════════════════════════════════════════════

    def classify_and_route(self, query: str) -> RoutingDecision:
        """
        Classify input type and route to appropriate processing.
        
        Fast heuristic classification — no LLM call needed for routing.
        Returns category, confidence, recommended strategy, and budget.
        """
        text = query.lower().strip()
        word_count = len(text.split())
        scores: Dict[str, float] = defaultdict(float)

        # ── Category scoring ──
        # Emotional signals
        emotional_words = ["feel", "feeling", "sad", "happy", "angry", "frustrated",
                          "anxious", "worried", "stressed", "overwhelmed", "lonely",
                          "scared", "excited", "hurt", "love", "hate", "afraid",
                          "depressed", "tired", "exhausted", "burned out"]
        scores["emotional"] = sum(0.3 for w in emotional_words if w in text)

        # Planning signals
        planning_words = ["plan", "schedule", "organize", "prepare", "goal", "deadline",
                         "next week", "tomorrow", "strategy", "steps", "how to", "roadmap"]
        scores["planning"] = sum(0.3 for w in planning_words if w in text)

        # Technical signals
        technical_words = ["code", "bug", "error", "python", "function", "api", "database",
                          "server", "deploy", "build", "install", "debug", "git", "docker"]
        scores["technical"] = sum(0.3 for w in technical_words if w in text)

        # Creative signals
        creative_words = ["write", "create", "design", "imagine", "story", "idea",
                         "brainstorm", "invent", "compose", "poem", "song", "creative"]
        scores["creative"] = sum(0.3 for w in creative_words if w in text)

        # Factual signals
        factual_words = ["what is", "who is", "when did", "how many", "define",
                        "explain", "tell me about", "what does", "meaning of"]
        scores["factual"] = sum(0.3 for w in factual_words if w in text)

        # Philosophical signals
        philosophical_words = ["meaning", "purpose", "why do we", "nature of", "consciousness",
                              "free will", "existence", "truth", "morality", "justice"]
        scores["philosophical"] = sum(0.3 for w in philosophical_words if w in text)

        # Urgent signals
        urgent_words = ["urgent", "emergency", "asap", "right now", "immediately",
                       "help me", "panic", "crisis", "can't", "broken"]
        scores["urgent"] = sum(0.4 for w in urgent_words if w in text)

        # Casual signals
        if word_count <= 5 and not any(scores[k] > 0.3 for k in scores):
            scores["casual"] = 0.8

        # Select highest scoring category
        if not any(scores.values()):
            category = QueryCategory.CASUAL
            confidence = 0.5
        else:
            best_category = max(scores, key=scores.get)
            category = QueryCategory(best_category)
            confidence = min(scores[best_category] / 1.5, 0.95)

        # ── Strategy routing ──
        strategy_map = {
            QueryCategory.FACTUAL: ReasoningStrategy.CHAIN_OF_THOUGHT,
            QueryCategory.EMOTIONAL: ReasoningStrategy.ANALOGICAL,
            QueryCategory.PLANNING: ReasoningStrategy.DECOMPOSE_AND_CONQUER,
            QueryCategory.CREATIVE: ReasoningStrategy.TREE_OF_THOUGHT,
            QueryCategory.TECHNICAL: ReasoningStrategy.CHAIN_OF_THOUGHT,
            QueryCategory.PHILOSOPHICAL: ReasoningStrategy.SOCRATIC,
            QueryCategory.URGENT: ReasoningStrategy.CHAIN_OF_THOUGHT,
            QueryCategory.CASUAL: ReasoningStrategy.CHAIN_OF_THOUGHT,
        }

        # ── Budget routing ──
        budget_map = {
            QueryCategory.FACTUAL: ThinkingBudget.MODERATE,
            QueryCategory.EMOTIONAL: ThinkingBudget.DEEP,
            QueryCategory.PLANNING: ThinkingBudget.DEEP,
            QueryCategory.CREATIVE: ThinkingBudget.MODERATE,
            QueryCategory.TECHNICAL: ThinkingBudget.MODERATE,
            QueryCategory.PHILOSOPHICAL: ThinkingBudget.MAXIMUM,
            QueryCategory.URGENT: ThinkingBudget.MINIMAL,
            QueryCategory.CASUAL: ThinkingBudget.MINIMAL,
        }

        # Adjust based on past strategy performance
        recommended_strategy = strategy_map.get(category, ReasoningStrategy.CHAIN_OF_THOUGHT)
        recommended_strategy = self._adjust_strategy_from_stats(recommended_strategy, category)

        return RoutingDecision(
            category=category.value,
            confidence=round(confidence, 2),
            recommended_strategy=recommended_strategy.value,
            recommended_budget=budget_map.get(category, ThinkingBudget.MODERATE).value,
            reasoning=f"Scored {category.value}={scores.get(category.value, 0):.1f} from {word_count} words",
        )

    def _adjust_strategy_from_stats(
        self, default_strategy: ReasoningStrategy, category: QueryCategory
    ) -> ReasoningStrategy:
        """Adjust strategy recommendation based on historical performance."""
        if not self._strategy_stats:
            return default_strategy

        # If default strategy has consistently low confidence, try alternatives
        default_stats = self._strategy_stats.get(default_strategy.value, {})
        if default_stats.get("avg_confidence", 1.0) < 0.4 and default_stats.get("uses", 0) > 5:
            # Find best performing alternative
            best_alt = default_strategy
            best_conf = 0.0
            for strat_name, stats in self._strategy_stats.items():
                if stats.get("avg_confidence", 0) > best_conf and stats.get("uses", 0) > 3:
                    best_conf = stats["avg_confidence"]
                    try:
                        best_alt = ReasoningStrategy(strat_name)
                    except ValueError:
                        continue
            if best_conf > 0.5:
                return best_alt

        return default_strategy

    # ══════════════════════════════════════════════════════════════════════════
    # 6. REFLECTION & LEARNING
    # ══════════════════════════════════════════════════════════════════════════

    def reflect_on_interaction(
        self,
        query: str,
        response: str,
        user_feedback: Optional[str] = None
    ) -> Reflection:
        """
        Post-interaction reflection — learn from what happened.
        
        Extracts: what worked, what didn't, what to remember, what to improve.
        Stores reflections for future strategy selection.
        """
        llm = get_reasoning_llm(temperature=0.3)

        feedback_str = f"\nUSER FEEDBACK: {user_feedback}" if user_feedback else ""
        prompt = f"""Reflect on this interaction. What can be learned for next time?

QUERY: {query}
RESPONSE GIVEN: {response[:1500]}
{feedback_str}

Analyze honestly:
- What worked well in this response?
- What could have been better?
- What should LOVE remember for future interactions?
- What specific improvements to make?

Return JSON:
{{
  "what_worked": ["..."],
  "what_failed": ["..."],
  "what_to_remember": ["Key pattern or preference to remember"],
  "what_to_improve": ["Specific actionable improvement"],
  "effectiveness_score": 0.7
}}"""

        reflection = Reflection(
            query=query[:200],
            response_summary=response[:200],
        )

        try:
            llm_response = str(llm.invoke(prompt))
            data = self._extract_json(llm_response)
            if data:
                reflection.what_worked = data.get("what_worked", [])
                reflection.what_failed = data.get("what_failed", [])
                reflection.what_to_remember = data.get("what_to_remember", [])
                reflection.what_to_improve = data.get("what_to_improve", [])
                reflection.effectiveness_score = data.get("effectiveness_score", 0.5)
        except Exception as e:
            print(f"[CognitiveArch] Reflection error: {e}")
            reflection.what_to_improve = ["Reflection system encountered an error"]

        # Store reflection
        with self._lock:
            self._reflections.append(reflection.to_dict())
            if len(self._reflections) > MAX_REFLECTIONS:
                self._reflections = self._reflections[-MAX_REFLECTIONS:]

        self._save_reflections()

        # Publish learning event
        self._bus.publish(
            domain="learning",
            event_type="interaction_reflected",
            payload={
                "effectiveness": reflection.effectiveness_score,
                "learnings_count": len(reflection.what_to_remember),
                "improvements_count": len(reflection.what_to_improve),
            },
            source_module="cognitive_architecture",
        )

        print(f"[CognitiveArch] Reflected | effectiveness={reflection.effectiveness_score:.2f} | "
              f"learned={len(reflection.what_to_remember)} items")

        return reflection

    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get performance metrics per strategy."""
        stats = {}
        for strategy_name, data in self._strategy_stats.items():
            stats[strategy_name] = {
                "uses": data.get("uses", 0),
                "avg_confidence": round(data.get("avg_confidence", 0), 3),
                "avg_time_ms": round(data.get("avg_time_ms", 0), 1),
                "total_time_ms": data.get("total_time_ms", 0),
            }

        # Add summary
        total_uses = sum(d.get("uses", 0) for d in self._strategy_stats.values())
        stats["_summary"] = {
            "total_reasoning_sessions": total_uses,
            "total_reflections": len(self._reflections),
            "strategies_used": len(self._strategy_stats),
            "best_performing": self._get_best_strategy(),
        }
        return stats

    def _get_best_strategy(self) -> str:
        """Find the best performing strategy by average confidence."""
        if not self._strategy_stats:
            return "none"
        best = max(
            self._strategy_stats.items(),
            key=lambda x: x[1].get("avg_confidence", 0) if x[1].get("uses", 0) >= 3 else 0
        )
        return best[0] if best[1].get("uses", 0) >= 3 else "insufficient_data"

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response text, handling common formatting issues."""
        if not text:
            return None

        # Try direct parse first
        try:
            return json.loads(text)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_architecture")

        # Try to find JSON block in text
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    candidate = match.group(1) if match.lastindex else match.group(0)
                    return json.loads(candidate)
                except (json.JSONDecodeError, IndexError):
                    continue

        # Last resort: find the largest {...} block
        brace_start = text.find('{')
        brace_end = text.rfind('}')
        if brace_start != -1 and brace_end > brace_start:
            try:
                return json.loads(text[brace_start:brace_end + 1])
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.cognitive_architecture")

        return None

    def _extract_answer_from_text(self, text: str) -> str:
        """Extract a usable answer from non-JSON LLM response."""
        # Remove common prefixes
        text = text.strip()
        for prefix in ["Answer:", "Response:", "Here's", "Sure,"]:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
        return text[:1000]

    def _record_strategy_use(self, strategy: str, confidence: float, time_ms: int):
        """Record strategy performance for learning."""
        with self._lock:
            if strategy not in self._strategy_stats:
                self._strategy_stats[strategy] = {
                    "uses": 0,
                    "total_confidence": 0.0,
                    "total_time_ms": 0,
                    "avg_confidence": 0.0,
                    "avg_time_ms": 0.0,
                    "last_used": "",
                }

            stats = self._strategy_stats[strategy]
            stats["uses"] += 1
            stats["total_confidence"] += confidence
            stats["total_time_ms"] += time_ms
            stats["avg_confidence"] = stats["total_confidence"] / stats["uses"]
            stats["avg_time_ms"] = stats["total_time_ms"] / stats["uses"]
            stats["last_used"] = datetime.now().isoformat()

        self._save_strategy_stats()

    def _publish_thinking_event(self, trace: ThinkingTrace):
        """Publish a thinking event to the neural bus."""
        try:
            self._bus.publish(
                domain="consciousness",
                event_type="deep_thinking",
                payload={
                    "budget": trace.budget,
                    "steps_count": len(trace.reasoning_steps),
                    "confidence": trace.confidence_score,
                    "time_ms": trace.time_spent_ms,
                    "query_preview": trace.query[:80],
                    "conclusion_preview": trace.conclusion[:200] if trace.conclusion else "",
                },
                source_module="cognitive_architecture",
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.cognitive_architecture")

    def _store_trace(self, trace: ThinkingTrace):
        """Persist thinking trace to disk."""
        with self._lock:
            self._recent_traces.append(trace.to_dict())

        # Periodic disk write (every 10 traces)
        if len(self._recent_traces) % 10 == 0:
            self._save_traces()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_strategy_stats(self) -> Dict[str, Dict]:
        """Load strategy performance stats from disk."""
        try:
            if STRATEGY_STATS_FILE.exists():
                data = json.loads(STRATEGY_STATS_FILE.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"[CognitiveArch] Failed to load strategy stats: {e}")
        return {}

    def _save_strategy_stats(self):
        """Save strategy stats to disk."""
        try:
            STRATEGY_STATS_FILE.write_text(
                json.dumps(self._strategy_stats, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"[CognitiveArch] Failed to save strategy stats: {e}")

    def _load_reflections(self) -> List[Dict]:
        """Load reflections from disk."""
        try:
            if REFLECTIONS_FILE.exists():
                data = json.loads(REFLECTIONS_FILE.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[CognitiveArch] Failed to load reflections: {e}")
        return []

    def _save_reflections(self):
        """Save reflections to disk."""
        try:
            REFLECTIONS_FILE.write_text(
                json.dumps(self._reflections[-MAX_REFLECTIONS:], indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"[CognitiveArch] Failed to save reflections: {e}")

    def _save_traces(self):
        """Save recent traces to disk."""
        try:
            traces = list(self._recent_traces)[-MAX_TRACES:]
            TRACES_FILE.write_text(
                json.dumps(traces, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"[CognitiveArch] Failed to save traces: {e}")

    # ── Proactive Capabilities ───────────────────────────────────────────────

    def get_cognitive_health(self) -> Dict[str, Any]:
        """
        Self-diagnostic: how well is the cognitive architecture performing?
        Useful for proactive self-monitoring.
        """
        stats = self.get_reasoning_stats()
        summary = stats.get("_summary", {})

        # Calculate health indicators
        total_sessions = summary.get("total_reasoning_sessions", 0)
        avg_confidence = 0.0
        if self._strategy_stats:
            confidences = [s.get("avg_confidence", 0) for s in self._strategy_stats.values()
                          if s.get("uses", 0) > 0]
            avg_confidence = statistics.mean(confidences) if confidences else 0.0

        # Recent reflection effectiveness
        recent_reflections = self._reflections[-10:]
        avg_effectiveness = 0.0
        if recent_reflections:
            scores = [r.get("effectiveness_score", 0.5) for r in recent_reflections]
            avg_effectiveness = statistics.mean(scores)

        health = {
            "status": "healthy" if avg_confidence > 0.5 else "needs_attention",
            "total_reasoning_sessions": total_sessions,
            "average_confidence": round(avg_confidence, 3),
            "average_reflection_effectiveness": round(avg_effectiveness, 3),
            "strategies_explored": len(self._strategy_stats),
            "reflections_stored": len(self._reflections),
            "best_strategy": self._get_best_strategy(),
            "recommendation": self._get_health_recommendation(avg_confidence, avg_effectiveness),
        }

        return health

    def _get_health_recommendation(self, avg_confidence: float, avg_effectiveness: float) -> str:
        """Generate a proactive recommendation based on cognitive health."""
        if avg_confidence < 0.4:
            return "Confidence is low. Consider using self_consistency strategy more often."
        if avg_effectiveness < 0.5:
            return "Reflection effectiveness is low. Focus on actionable improvements."
        if avg_confidence > 0.8:
            return "High confidence — but watch for overconfidence bias."
        return "Cognitive health is stable. Continue current strategy mix."

    def get_recent_learnings(self, limit: int = 5) -> List[str]:
        """Get the most recent learnings from reflections — useful for proactive suggestions."""
        learnings = []
        for reflection in reversed(self._reflections):
            for item in reflection.get("what_to_remember", []):
                learnings.append(item)
                if len(learnings) >= limit:
                    return learnings
        return learnings


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ══════════════════════════════════════════════════════════════════════════════

_instance: Optional[CognitiveArchitecture] = None
_instance_lock = threading.Lock()


def get_cognitive_architecture() -> CognitiveArchitecture:
    """Get the singleton CognitiveArchitecture instance."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = CognitiveArchitecture()
    return _instance
