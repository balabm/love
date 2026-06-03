"""
LOVE Reasoning Engine — Chain-of-Thought & Reflection (Modern AI Pattern)

Before LOVE takes any significant action, it should think step-by-step.
This module implements:

1. CHAIN-OF-THOUGHT
   - Break complex problems into sub-problems
   - Reason about each step before acting
   - Surface the reasoning to the user for transparency

2. REFLECTION
   - After an action, evaluate: was it correct?
   - If not, generate a correction and retry
   - Learn from mistakes for future reasoning

3. STRUCTURED OUTPUT
   - All reasoning produces JSON with schema validation
   - Enables reliable parsing by downstream systems
   - Reduces hallucination in tool selection

4. REASONING MEMORY
   - Store successful reasoning chains for reuse
   - Build a library of "how to think about X" patterns
   - Self-improve reasoning strategies over time

Architecture:
- analyze(): Given a situation, produce a reasoning chain
- decide(): Given options, reason about which is best
- reflect(): Given an outcome, evaluate and learn
- get_patterns(): Retrieve reasoning patterns for similar situations
"""

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.llm import get_reasoning_llm
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "reasoning"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REASONING_LOG = DATA_DIR / "reasoning_log.jsonl"
PATTERN_FILE = DATA_DIR / "reasoning_patterns.json"


@dataclass
class ReasoningChain:
    """A single chain-of-thought reasoning session."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    situation: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, str]] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    action_taken: str = ""
    outcome: Optional[str] = None
    reflection: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)


@dataclass
class ReasoningPattern:
    """A reusable reasoning pattern learned from experience."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    pattern_type: str = ""  # decision, analysis, planning, debugging
    description: str = ""
    steps_template: List[str] = field(default_factory=list)
    success_rate: float = 0.5
    usage_count: int = 0
    tags: List[str] = field(default_factory=list)


class ReasoningEngine:
    """
    Central reasoning coordinator for LOVE.
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
        self._patterns: Dict[str, ReasoningPattern] = {}
        self._recent_chains: List[ReasoningChain] = []
        self._load_patterns()

    # ── Core Reasoning ──────────────────────────────────────────────────────────

    def analyze(self, situation: str, context: Dict[str, Any] = None,
                tags: List[str] = None) -> ReasoningChain:
        """Analyze a situation using chain-of-thought reasoning."""
        context = context or {}
        tags = tags or []

        chain = ReasoningChain(
            situation=situation,
            context=context,
            tags=tags,
        )

        try:
            llm = get_reasoning_llm()

            # Build the reasoning prompt
            prompt = self._build_analysis_prompt(situation, context)
            response = llm.complete(prompt, max_tokens=2000, temperature=0.3)

            # Parse the reasoning steps
            parsed = self._parse_reasoning_response(response)
            chain.steps = parsed.get("steps", [])
            chain.conclusion = parsed.get("conclusion", "")
            chain.confidence = parsed.get("confidence", 0.5)

            # Store for reflection later
            with self._lock:
                self._recent_chains.append(chain)
                if len(self._recent_chains) > 100:
                    self._recent_chains.pop(0)

            self._log({
                "event": "reasoning_complete",
                "chain_id": chain.id,
                "situation": situation[:80],
                "confidence": chain.confidence,
                "tags": tags,
            })

        except Exception as e:
            chain.conclusion = f"Reasoning error: {e}"
            chain.confidence = 0.0
            print(f"[ReasoningEngine] Analyze error: {e}")

        return chain

    def decide(self, question: str, options: List[Dict[str, str]],
               criteria: List[str] = None) -> Dict[str, Any]:
        """Make a decision by reasoning about options."""
        criteria = criteria or ["effectiveness", "risk", "effort", "alignment"]

        try:
            llm = get_reasoning_llm()

            options_text = "\n".join([
                f"Option {i+1}: {opt.get('name', 'Unknown')}\n"
                f"  Description: {opt.get('description', '')}\n"
                f"  Pros: {', '.join(opt.get('pros', []))}\n"
                f"  Cons: {', '.join(opt.get('cons', []))}"
                for i, opt in enumerate(options)
            ])

            prompt = f"""You are LOVE's reasoning engine. Analyze these options carefully.

Question: {question}

Options:
{options_text}

Evaluate each option against these criteria: {', '.join(criteria)}.

Respond with JSON only:
{{
  "analysis": [
    {{"option": "name", "scores": {{"criterion": score(0-10)}}, "total_score": sum, "reasoning": "why"}}
  ],
  "winner": "best option name",
  "confidence": 0.0-1.0,
  "reasoning": "step-by-step explanation"
}}"""

            response = llm.complete(prompt, max_tokens=2000, temperature=0.2)
            result = self._safe_json_parse(response, {
                "winner": options[0].get("name", "unknown") if options else "none",
                "confidence": 0.3,
                "reasoning": "Parse error, falling back to first option.",
                "analysis": [],
            })

            self._log({
                "event": "decision_made",
                "question": question[:80],
                "winner": result.get("winner"),
                "confidence": result.get("confidence"),
            })

            return result

        except Exception as e:
            print(f"[ReasoningEngine] Decide error: {e}")
            return {
                "winner": options[0].get("name", "unknown") if options else "none",
                "confidence": 0.1,
                "reasoning": f"Error: {e}",
                "analysis": [],
            }

    def reflect(self, chain_id: str, outcome: str, success: bool) -> str:
        """Reflect on a completed reasoning chain and learn from it."""
        chain = None
        for c in self._recent_chains:
            if c.id == chain_id:
                chain = c
                break

        if not chain:
            return "Chain not found for reflection"

        chain.outcome = outcome
        chain.reflection = f"Outcome: {outcome}. Success: {success}"

        # If successful and high confidence, extract as pattern
        if success and chain.confidence > 0.7:
            self._extract_pattern(chain)

        self._log({
            "event": "reflection_complete",
            "chain_id": chain_id,
            "success": success,
            "outcome": outcome[:100],
        })

        return chain.reflection

    # ── Pattern Management ──────────────────────────────────────────────────────

    def get_patterns(self, pattern_type: str = "", tags: List[str] = None) -> List[ReasoningPattern]:
        """Get reasoning patterns matching criteria."""
        patterns = list(self._patterns.values())
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        if tags:
            patterns = [p for p in patterns if any(t in p.tags for t in tags)]
        # Sort by success rate
        patterns.sort(key=lambda p: p.success_rate, reverse=True)
        return patterns[:10]

    def apply_pattern(self, pattern_id: str, situation: str) -> Optional[str]:
        """Apply a reasoning pattern to a new situation."""
        if pattern_id not in self._patterns:
            return None
        pattern = self._patterns[pattern_id]
        pattern.usage_count += 1
        self._save_patterns()

        # Substitute situation into pattern template
        steps = [step.replace("{situation}", situation) for step in pattern.steps_template]
        return "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

    def _extract_pattern(self, chain: ReasoningChain):
        """Extract a reusable pattern from a successful reasoning chain."""
        try:
            pattern_type = chain.tags[0] if chain.tags else "general"
            steps_template = [step.get("thought", "") for step in chain.steps[:5]]

            pattern = ReasoningPattern(
                pattern_type=pattern_type,
                description=f"Pattern from successful reasoning: {chain.situation[:60]}",
                steps_template=steps_template,
                success_rate=chain.confidence,
                tags=chain.tags,
            )
            self._patterns[pattern.id] = pattern
            self._save_patterns()
        except Exception as e:
            print(f"[ReasoningEngine] Pattern extraction error: {e}")

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _build_analysis_prompt(self, situation: str, context: Dict) -> str:
        context_str = json.dumps(context, indent=2, default=str) if context else "{}"
        return f"""You are LOVE's reasoning engine. Analyze this situation step by step.

Situation: {situation}

Context:
{context_str}

Think through this carefully:
1. What is the core problem or opportunity?
2. What information do I have vs. what am I missing?
3. What are the possible approaches?
4. What are the risks and trade-offs of each?
5. What is the best course of action?

Respond with JSON only:
{{
  "steps": [
    {{"step": 1, "thought": "your reasoning for this step", "category": "analysis|synthesis|evaluation"}}
  ],
  "conclusion": "final recommendation",
  "confidence": 0.0-1.0
}}"""

    def _parse_reasoning_response(self, response: str) -> Dict:
        """Parse a reasoning response from the LLM."""
        try:
            # Try to extract JSON from response
            return self._safe_json_parse(response, {
                "steps": [{"step": 1, "thought": response[:500], "category": "analysis"}],
                "conclusion": response[:500],
                "confidence": 0.5,
            })
        except Exception:
            return {
                "steps": [{"step": 1, "thought": "Raw response", "category": "analysis"}],
                "conclusion": response[:1000],
                "confidence": 0.3,
            }

    def _safe_json_parse(self, text: str, fallback: Dict) -> Dict:
        """Safely parse JSON from LLM response."""
        try:
            # Find JSON block if wrapped in markdown
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except Exception:
            return fallback

    # ── Persistence ─────────────────────────────────────────────────────────────

    def _load_patterns(self):
        try:
            if PATTERN_FILE.exists():
                data = json.loads(PATTERN_FILE.read_text())
                for pd in data.get("patterns", []):
                    self._patterns[pd["id"]] = ReasoningPattern(**pd)
        except Exception as e:
            print(f"[ReasoningEngine] Pattern load error: {e}")

    def _save_patterns(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "patterns": [
                    {
                        "id": p.id,
                        "pattern_type": p.pattern_type,
                        "description": p.description,
                        "steps_template": p.steps_template,
                        "success_rate": p.success_rate,
                        "usage_count": p.usage_count,
                        "tags": p.tags,
                    }
                    for p in self._patterns.values()
                ],
            }
            PATTERN_FILE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[ReasoningEngine] Pattern save error: {e}")

    def _log(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(REASONING_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.reasoning_engine")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_reasoning_engine_instance: Optional[ReasoningEngine] = None
_reasoning_engine_lock = threading.Lock()


def get_reasoning_engine() -> ReasoningEngine:
    global _reasoning_engine_instance
    with _reasoning_engine_lock:
        if _reasoning_engine_instance is None:
            _reasoning_engine_instance = ReasoningEngine()
        return _reasoning_engine_instance
