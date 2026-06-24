"""
LOVE Reasoning Chain — Phase 5p of AGI Metamorphosis

LOVE doesn't just react. LOVE thinks in chains of consequences.

This module maintains structured reasoning:
- "I notice Karthi's CPU is at 90%"
- "This means he's compiling something heavy or running tests"
- "Which means he's been working hard for a while"
- "Which means I should suggest a break, not a new task"
- "But if he's in a deadline crunch, suggesting a break might frustrate him"
- "So I should check his calendar first"

Reasoning chains make LOVE's behavior transparent, auditable, and genuinely
intelligent. They also allow LOVE to revise its thinking when new evidence
arrives — just like a human would.
"""

import json
import time
import uuid
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

REASONING_LOG_PATH = DATA_DIR / "reasoning_chains.jsonl"


@dataclass
class ReasoningNode:
    """A single step in LOVE's reasoning chain."""
    id: str
    timestamp: str
    premise: str  # What LOVE observed or assumed
    inference: str  # What LOVE concluded from the premise
    confidence: float  # 0 to 1
    evidence: List[str]  # Supporting facts
    parent_id: Optional[str]  # Previous node in chain (None = root)
    branch: str  # "main", "alt_a", "alt_b", etc.
    status: str  # "active", "confirmed", "rejected", "pending"


class ReasoningChain:
    """
    LOVE's structured thinking. Maintains chains of connected inferences.
    """

    def __init__(self, max_chain_length: int = 10):
        self._max_length = max_chain_length
        self._nodes: Dict[str, ReasoningNode] = {}
        self._active_chains: Dict[str, List[str]] = {}  # branch -> ordered node IDs
        self._lock = threading.Lock()

    # ═══════════════════════════════════════════════════════════════════════
    # CORE: Build and manage reasoning chains
    # ═══════════════════════════════════════════════════════════════════════

    def observe(self, observation: str, confidence: float = 0.8,
                branch: str = "main") -> ReasoningNode:
        """
        Start a new reasoning chain from an observation.
        Or extend an existing chain.
        """
        with self._lock:
            node_id = uuid.uuid4().hex[:8]
            now = datetime.now().isoformat()

            # Find parent — last node in this branch
            parent_id = None
            if branch in self._active_chains and self._active_chains[branch]:
                parent_id = self._active_chains[branch][-1]

            node = ReasoningNode(
                id=node_id,
                timestamp=now,
                premise=observation,
                inference=f"From '{observation[:50]}...'",
                confidence=confidence,
                evidence=[observation],
                parent_id=parent_id,
                branch=branch,
                status="active",
            )

            self._nodes[node_id] = node
            self._active_chains.setdefault(branch, []).append(node_id)

            # Trim chain if too long
            if len(self._active_chains[branch]) > self._max_length:
                removed = self._active_chains[branch].pop(0)
                # Archive removed node instead of deleting
                if removed in self._nodes:
                    old = self._nodes[removed]
                    self._nodes[removed] = old.__class__(
                        **{**asdict(old), "status": "archived"}
                    )

            self._log_reasoning(node)
            return node

    def infer(self, from_node_id: str, conclusion: str,
              confidence: float = 0.7, evidence: List[str] = None) -> ReasoningNode:
        """
        Add an inference step to a reasoning chain.
        'Because [premise], therefore [conclusion]'
        """
        with self._lock:
            parent = self._nodes.get(from_node_id)
            if not parent:
                raise ValueError(f"Parent node {from_node_id} not found")

            node_id = uuid.uuid4().hex[:8]
            now = datetime.now().isoformat()

            node = ReasoningNode(
                id=node_id,
                timestamp=now,
                premise=parent.inference,
                inference=conclusion,
                confidence=confidence,
                evidence=evidence or [],
                parent_id=from_node_id,
                branch=parent.branch,
                status="active",
            )

            self._nodes[node_id] = node
            self._active_chains.setdefault(parent.branch, []).append(node_id)

            self._log_reasoning(node)
            return node

    def branch(self, from_node_id: str, alternative: str,
               confidence: float = 0.5) -> ReasoningNode:
        """
        Create a fork in reasoning: 'Two possibilities: A or B'
        """
        with self._lock:
            parent = self._nodes.get(from_node_id)
            if not parent:
                raise ValueError(f"Parent node {from_node_id} not found")

            branch_name = f"alt_{uuid.uuid4().hex[:4]}"
            node_id = uuid.uuid4().hex[:8]
            now = datetime.now().isoformat()

            node = ReasoningNode(
                id=node_id,
                timestamp=now,
                premise=parent.inference,
                inference=f"Alternative: {alternative}",
                confidence=confidence,
                evidence=[],
                parent_id=from_node_id,
                branch=branch_name,
                status="active",
            )

            self._nodes[node_id] = node
            self._active_chains[branch_name] = [node_id]

            self._log_reasoning(node)
            return node

    def confirm(self, node_id: str):
        """Mark a reasoning step as confirmed by evidence."""
        with self._lock:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                self._nodes[node_id] = node.__class__(
                    **{**asdict(node), "status": "confirmed", "confidence": min(1.0, node.confidence + 0.1)}
                )

    def reject(self, node_id: str, reason: str = ""):
        """Mark a reasoning step as rejected. Prune the chain."""
        with self._lock:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                self._nodes[node_id] = node.__class__(
                    **{**asdict(node), "status": "rejected"}
                )
                # Also reject all children
                self._reject_children(node_id)

    def _reject_children(self, parent_id: str):
        """Recursively reject all descendants of a node."""
        for node_id, node in list(self._nodes.items()):
            if node.parent_id == parent_id:
                self._nodes[node_id] = node.__class__(
                    **{**asdict(node), "status": "rejected"}
                )
                self._reject_children(node_id)

    # ═══════════════════════════════════════════════════════════════════════
    # INTELLIGENT: Auto-build chains from events
    # ═══════════════════════════════════════════════════════════════════════

    def build_chain_from_context(self) -> Optional[List[ReasoningNode]]:
        """
        Automatically build a reasoning chain from the current context.
        This is where LOVE's real intelligence lives.
        """
        try:
            from core.context_engine import get_live_context
            from core.emotional import get_emotional_summary
            from core.active_inference_engine import get_active_inference

            ctx = get_live_context()
            emotional = get_emotional_summary(days=1)
            ai = get_active_inference()
            ai_status = ai.get_status()

            chain: List[ReasoningNode] = []

            # Observation 1: System state
            if ctx and ctx.system_cpu and ctx.system_cpu > 70:
                n1 = self.observe(
                    f"Karthi's CPU is at {ctx.system_cpu}%",
                    confidence=0.9,
                )
                chain.append(n1)

                # Inference 1: What is he doing?
                n2 = self.infer(
                    n1.id,
                    "He's running something computationally intensive (compile, test, or build)",
                    confidence=0.7,
                )
                chain.append(n2)

                # Inference 2: How long has he been at it?
                n3 = self.infer(
                    n2.id,
                    "He's been working hard for a while. He might need a break soon.",
                    confidence=0.6,
                )
                chain.append(n3)

            # Observation 2: Emotional state
            mood = emotional.get("dominant_mood", "")
            if mood == "stressed":
                n = self.observe(
                    "Karthi's emotional state shows stress",
                    confidence=0.8,
                )
                if chain:
                    # Connect to existing chain
                    n = self.infer(
                        chain[-1].id,
                        f"And he's stressed. I should be very gentle. No new tasks.",
                        confidence=0.8,
                    )
                chain.append(n)

            # Observation 3: Prediction surprises
            recent_surprises = ai_status.get("recent_surprises", [])
            if recent_surprises and any(s.get("magnitude", 0) > 0.5 for s in recent_surprises[-3:]):
                n = self.observe(
                    "My recent predictions have been inaccurate (high surprise)",
                    confidence=0.8,
                )
                if chain:
                    n = self.infer(
                        chain[-1].id,
                        "My model needs updating. I should be less confident in my assumptions.",
                        confidence=0.7,
                    )
                chain.append(n)

            return chain if chain else None

        except Exception:
            return None

    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    def _log_reasoning(self, node: ReasoningNode):
        try:
            with open(REASONING_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(node)) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_active_chain(self, branch: str = "main") -> List[ReasoningNode]:
        """Get the current active reasoning chain for a branch."""
        with self._lock:
            node_ids = self._active_chains.get(branch, [])
            return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def get_chain_summary(self, branch: str = "main") -> str:
        """Generate a human-readable summary of the reasoning chain."""
        chain = self.get_active_chain(branch)
        if not chain:
            return ""

        lines = ["\n=== MY REASONING ==="]
        for i, node in enumerate(chain):
            marker = {"active": ">", "confirmed": "[OK]", "rejected": "[X]", "pending": "[?]"}.get(node.status, ">")
            indent = "  " * i
            lines.append(f"{indent}{marker} {node.inference} (confidence: {node.confidence:.0%})")
            if node.evidence:
                lines.append(f"{indent}   Evidence: {', '.join(node.evidence[:2])}")
        lines.append("=== END REASONING ===\n")
        return "\n".join(lines)

    def get_all_branches(self) -> List[str]:
        """Get all active reasoning branches."""
        with self._lock:
            return list(self._active_chains.keys())

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_nodes": len(self._nodes),
                "active_branches": len(self._active_chains),
                "branch_names": list(self._active_chains.keys()),
                "main_chain_length": len(self._active_chains.get("main", [])),
            }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_reasoning_chain: Optional[ReasoningChain] = None


def get_reasoning_chain() -> ReasoningChain:
    global _reasoning_chain
    if _reasoning_chain is None:
        _reasoning_chain = ReasoningChain()
    return _reasoning_chain
